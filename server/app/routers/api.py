"""JSON API consumed by the student mobile app and admin clients."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..config import settings
from ..database import get_db
from ..deps import get_current_admin
from ..security import create_access_token, verify_password

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/info")
def info():
    """Public app info used by the mobile client for branding."""
    return {
        "school_name": settings.SCHOOL_NAME,
        "school_name_he": settings.SCHOOL_NAME_HE,
        "version": "1.0.0",
    }


# ---------- Student sign in / sign out (public, by student ID) ----------
@router.post("/check", response_model=schemas.CheckResponse)
def check(req: schemas.CheckRequest, db: Session = Depends(get_db)):
    """Toggle attendance: signs the student in if out, or out if in."""
    student = crud.get_student_by_student_id(db, req.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student ID not found")
    if not student.is_active:
        raise HTTPException(status_code=403, detail="This student account is inactive")
    rec = crud.toggle_check(db, student, source="mobile", note=req.note)
    verb = "signed in" if rec.action == "in" else "signed out"
    return schemas.CheckResponse(
        ok=True,
        action=rec.action,
        student_name=student.full_name,
        student_id=student.student_id,
        is_present=student.is_present,
        timestamp=rec.timestamp,
        message=f"{student.full_name} {verb}.",
    )


@router.post("/check/in", response_model=schemas.CheckResponse)
def check_in(req: schemas.CheckRequest, db: Session = Depends(get_db)):
    return _explicit_check(req, "in", db)


@router.post("/check/out", response_model=schemas.CheckResponse)
def check_out(req: schemas.CheckRequest, db: Session = Depends(get_db)):
    return _explicit_check(req, "out", db)


def _explicit_check(req: schemas.CheckRequest, action: str, db: Session):
    student = crud.get_student_by_student_id(db, req.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student ID not found")
    if not student.is_active:
        raise HTTPException(status_code=403, detail="This student account is inactive")
    rec = crud.record_check(db, student, action, source="mobile", note=req.note)
    verb = "signed in" if action == "in" else "signed out"
    return schemas.CheckResponse(
        ok=True,
        action=rec.action,
        student_name=student.full_name,
        student_id=student.student_id,
        is_present=student.is_present,
        timestamp=rec.timestamp,
        message=f"{student.full_name} {verb}.",
    )


@router.get("/student/{student_id}/status", response_model=schemas.StudentStatus)
def student_status(student_id: str, db: Session = Depends(get_db)):
    student = crud.get_student_by_student_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student ID not found")
    last = crud.last_action(db, student)
    return schemas.StudentStatus(
        student_id=student.student_id,
        full_name=student.full_name,
        grade=student.grade,
        is_present=student.is_present,
        last_action=last.action if last else None,
        last_timestamp=last.timestamp if last else None,
    )


# ---------- Admin auth (JSON) ----------
@router.post("/admin/login", response_model=schemas.Token)
def admin_login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = crud.get_admin_by_username(db, form.username)
    if not admin or not verify_password(form.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": admin.username})
    return schemas.Token(access_token=token)


# ---------- Admin data (JSON, token-protected) ----------
@router.get("/admin/stats")
def admin_stats(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return crud.dashboard_stats(db)


@router.get("/admin/students", response_model=list[schemas.StudentOut])
def admin_students(
    search: str = "",
    class_id: int | None = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return crud.list_students(db, search=search, class_id=class_id)


@router.get("/admin/attendance", response_model=list[schemas.AttendanceOut])
def admin_attendance(
    limit: int = Query(200, le=2000),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return crud.list_attendance(db, limit=limit)
