"""HTML admin panel routes (cookie-session auth)."""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..config import settings
from ..database import get_db
from ..deps import get_session_admin
from ..security import verify_password

import os

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter(tags=["admin-ui"])


def ctx(request: Request, admin, **extra):
    base = {
        "request": request,
        "admin": admin,
        "school_name": settings.SCHOOL_NAME,
        "school_name_he": settings.SCHOOL_NAME_HE,
    }
    base.update(extra)
    return base


def redirect(url: str):
    return RedirectResponse(url, status_code=303)


# ---------- Auth ----------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if get_session_admin(request, db):
        return redirect("/")
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "school_name": settings.SCHOOL_NAME, "school_name_he": settings.SCHOOL_NAME_HE, "error": None},
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    admin = crud.get_admin_by_username(db, username)
    if not admin or not admin.is_active or not verify_password(password, admin.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "school_name": settings.SCHOOL_NAME, "school_name_he": settings.SCHOOL_NAME_HE, "error": "Incorrect username or password"},
            status_code=401,
        )
    request.session["admin"] = admin.username
    crud.log_action(db, admin.username, "login", "Logged into admin panel")
    return redirect("/")


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return redirect("/login")


# ---------- Dashboard ----------
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    stats = crud.dashboard_stats(db)
    recent = crud.list_attendance(db, limit=15)
    return templates.TemplateResponse(
        "dashboard.html", ctx(request, admin, active="dashboard", stats=stats, recent=recent)
    )


# ---------- Students ----------
@router.get("/students", response_class=HTMLResponse)
def students_page(request: Request, search: str = "", class_id: str = "", db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    cid = int(class_id) if class_id.strip().isdigit() else None
    students = crud.list_students(db, search=search, class_id=cid)
    return templates.TemplateResponse(
        "students.html",
        ctx(request, admin, active="students", students=students, classes=crud.list_classes(db),
            search=search, class_id=cid),
    )


@router.get("/students/new", response_class=HTMLResponse)
def student_new(request: Request, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    return templates.TemplateResponse(
        "student_form.html",
        ctx(request, admin, active="students", student=None, classes=crud.list_classes(db), action="/students/new"),
    )


def _parse_student_form(form) -> dict:
    cid = form.get("class_id")
    return {
        "student_id": form.get("student_id", "").strip(),
        "first_name": form.get("first_name", "").strip(),
        "last_name": form.get("last_name", "").strip(),
        "grade": form.get("grade", "").strip() or None,
        "class_id": int(cid) if cid and cid.isdigit() else None,
        "email": form.get("email", "").strip() or None,
        "phone": form.get("phone", "").strip() or None,
        "guardian_name": form.get("guardian_name", "").strip() or None,
        "guardian_phone": form.get("guardian_phone", "").strip() or None,
        "notes": form.get("notes", "").strip() or None,
        "is_active": form.get("is_active", "1") == "1",
    }


@router.post("/students/new")
async def student_create(request: Request, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    form = await request.form()
    data = _parse_student_form(form)
    if crud.get_student_by_student_id(db, data["student_id"]):
        return templates.TemplateResponse(
            "student_form.html",
            ctx(request, admin, active="students", student=None, classes=crud.list_classes(db),
                action="/students/new", flash="That Student ID already exists.", flash_type="err"),
        )
    student = crud.create_student(db, schemas.StudentCreate(**data))
    crud.log_action(db, admin.username, "create_student", f"{student.student_id} {student.full_name}")
    return redirect("/students")


@router.get("/students/{pk}/edit", response_class=HTMLResponse)
def student_edit(request: Request, pk: int, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    student = crud.get_student(db, pk)
    if not student:
        return redirect("/students")
    return templates.TemplateResponse(
        "student_form.html",
        ctx(request, admin, active="students", student=student, classes=crud.list_classes(db),
            action=f"/students/{pk}/edit"),
    )


@router.post("/students/{pk}/edit")
async def student_update(request: Request, pk: int, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    student = crud.get_student(db, pk)
    if not student:
        return redirect("/students")
    form = await request.form()
    crud.update_student(db, student, _parse_student_form(form))
    crud.log_action(db, admin.username, "update_student", f"{student.student_id} {student.full_name}")
    return redirect("/students")


@router.get("/students/{pk}/toggle")
def student_toggle(request: Request, pk: int, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    student = crud.get_student(db, pk)
    if student:
        rec = crud.toggle_check(db, student, source="admin")
        crud.log_action(db, admin.username, "toggle_attendance", f"{student.student_id} -> {rec.action}")
    return redirect("/students")


@router.post("/students/{pk}/delete")
def student_delete(request: Request, pk: int, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    student = crud.get_student(db, pk)
    if student:
        label = f"{student.student_id} {student.full_name}"
        crud.delete_student(db, student)
        crud.log_action(db, admin.username, "delete_student", label)
    return redirect("/students")


# ---------- Attendance ----------
@router.get("/attendance", response_class=HTMLResponse)
def attendance_page(request: Request, date: str = "", action: str = "", db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    on_date = None
    if date:
        try:
            on_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            on_date = None
    records = crud.list_attendance(db, on_date=on_date, action=action or None, limit=1000)
    return templates.TemplateResponse(
        "attendance.html",
        ctx(request, admin, active="attendance", records=records, date_filter=date, action_filter=action),
    )


# ---------- Classes ----------
@router.get("/classes", response_class=HTMLResponse)
def classes_page(request: Request, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    return templates.TemplateResponse(
        "classes.html", ctx(request, admin, active="classes", classes=crud.list_classes(db))
    )


@router.post("/classes/new")
def class_create(
    request: Request, name: str = Form(...), grade: str = Form(""), teacher: str = Form(""),
    db: Session = Depends(get_db),
):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    crud.create_class(db, schemas.ClassCreate(name=name.strip(), grade=grade or None, teacher=teacher or None))
    crud.log_action(db, admin.username, "create_class", name)
    return redirect("/classes")


@router.post("/classes/{pk}/delete")
def class_delete(request: Request, pk: int, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    c = crud.get_class(db, pk)
    if c:
        crud.delete_class(db, c)
        crud.log_action(db, admin.username, "delete_class", c.name)
    return redirect("/classes")


# ---------- Admin users ----------
@router.get("/admins", response_class=HTMLResponse)
def admins_page(request: Request, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    return templates.TemplateResponse(
        "admins.html", ctx(request, admin, active="admins", admins=crud.list_admins(db))
    )


@router.post("/admins/new")
def admin_create(
    request: Request, username: str = Form(...), password: str = Form(...),
    full_name: str = Form(""), is_superadmin: str = Form("0"), db: Session = Depends(get_db),
):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    if not crud.get_admin_by_username(db, username.strip()):
        crud.create_admin(db, schemas.AdminCreate(
            username=username.strip(), password=password,
            full_name=full_name or None, is_superadmin=is_superadmin == "1",
        ))
        crud.log_action(db, admin.username, "create_admin", username)
    return redirect("/admins")


@router.post("/admins/{pk}/delete")
def admin_delete(request: Request, pk: int, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    target = db.query(models.AdminUser).filter(models.AdminUser.id == pk).first()
    if target and target.username != admin.username:
        crud.delete_admin(db, target)
        crud.log_action(db, admin.username, "delete_admin", target.username)
    return redirect("/admins")


# ---------- Audit ----------
@router.get("/audit", response_class=HTMLResponse)
def audit_page(request: Request, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    entries = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).limit(500).all()
    return templates.TemplateResponse("audit.html", ctx(request, admin, active="audit", entries=entries))


# ---------- CSV export ----------
@router.get("/export/students.csv")
def export_students(request: Request, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["student_id", "first_name", "last_name", "grade", "class", "email", "phone",
                "guardian_name", "guardian_phone", "is_present", "is_active"])
    for s in crud.list_students(db):
        w.writerow([s.student_id, s.first_name, s.last_name, s.grade or "",
                    s.school_class.name if s.school_class else "", s.email or "", s.phone or "",
                    s.guardian_name or "", s.guardian_phone or "", s.is_present, s.is_active])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ohr_temimim_students.csv"},
    )


@router.get("/export/attendance.csv")
def export_attendance(request: Request, db: Session = Depends(get_db)):
    admin = get_session_admin(request, db)
    if not admin:
        return redirect("/login")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["timestamp", "student_id", "student_name", "action", "source"])
    for r in crud.list_attendance(db, limit=100000):
        w.writerow([r.timestamp.strftime("%Y-%m-%d %H:%M:%S"), r.student.student_id,
                    r.student.full_name, r.action, r.source])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ohr_temimim_attendance.csv"},
    )
