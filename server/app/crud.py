"""Database operations (create/read/update/delete) shared by the API and admin UI."""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .security import hash_password


# ---------- Audit ----------
def log_action(db: Session, admin_username: Optional[str], action: str, detail: str = "") -> None:
    db.add(models.AuditLog(admin_username=admin_username, action=action, detail=detail))
    db.commit()


# ---------- Students ----------
def get_student_by_student_id(db: Session, student_id: str) -> Optional[models.Student]:
    return (
        db.query(models.Student)
        .filter(func.lower(models.Student.student_id) == student_id.strip().lower())
        .first()
    )


def get_student(db: Session, pk: int) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.id == pk).first()


def list_students(
    db: Session,
    search: str = "",
    class_id: Optional[int] = None,
    only_present: Optional[bool] = None,
):
    q = db.query(models.Student)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            (models.Student.first_name.ilike(like))
            | (models.Student.last_name.ilike(like))
            | (models.Student.student_id.ilike(like))
        )
    if class_id is not None:
        q = q.filter(models.Student.class_id == class_id)
    if only_present is not None:
        q = q.filter(models.Student.is_present == only_present)
    return q.order_by(models.Student.last_name, models.Student.first_name).all()


def create_student(db: Session, data: schemas.StudentCreate) -> models.Student:
    student = models.Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update_student(db: Session, student: models.Student, data: dict) -> models.Student:
    for field, value in data.items():
        if value is not None:
            setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student: models.Student) -> None:
    db.delete(student)
    db.commit()


# ---------- Attendance ----------
def record_check(
    db: Session, student: models.Student, action: str, source: str = "mobile", note: str = None
) -> models.AttendanceRecord:
    rec = models.AttendanceRecord(
        student_id=student.id, action=action, source=source, note=note
    )
    student.is_present = action == "in"
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def toggle_check(
    db: Session, student: models.Student, source: str = "mobile", note: str = None
) -> models.AttendanceRecord:
    """Sign out if currently present, otherwise sign in."""
    action = "out" if student.is_present else "in"
    return record_check(db, student, action, source=source, note=note)


def last_action(db: Session, student: models.Student) -> Optional[models.AttendanceRecord]:
    return (
        db.query(models.AttendanceRecord)
        .filter(models.AttendanceRecord.student_id == student.id)
        .order_by(models.AttendanceRecord.timestamp.desc())
        .first()
    )


def list_attendance(
    db: Session,
    student_pk: Optional[int] = None,
    on_date: Optional[date] = None,
    action: Optional[str] = None,
    limit: int = 500,
):
    q = db.query(models.AttendanceRecord)
    if student_pk is not None:
        q = q.filter(models.AttendanceRecord.student_id == student_pk)
    if action:
        q = q.filter(models.AttendanceRecord.action == action)
    if on_date is not None:
        start = datetime.combine(on_date, datetime.min.time())
        end = datetime.combine(on_date, datetime.max.time())
        q = q.filter(models.AttendanceRecord.timestamp.between(start, end))
    return q.order_by(models.AttendanceRecord.timestamp.desc()).limit(limit).all()


# ---------- Classes ----------
def list_classes(db: Session):
    return db.query(models.SchoolClass).order_by(models.SchoolClass.name).all()


def get_class(db: Session, pk: int) -> Optional[models.SchoolClass]:
    return db.query(models.SchoolClass).filter(models.SchoolClass.id == pk).first()


def create_class(db: Session, data: schemas.ClassCreate) -> models.SchoolClass:
    c = models.SchoolClass(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def delete_class(db: Session, c: models.SchoolClass) -> None:
    # Detach students from the class before deleting.
    for s in c.students:
        s.class_id = None
    db.delete(c)
    db.commit()


# ---------- Admin users ----------
def get_admin_by_username(db: Session, username: str) -> Optional[models.AdminUser]:
    return db.query(models.AdminUser).filter(models.AdminUser.username == username).first()


def list_admins(db: Session):
    return db.query(models.AdminUser).order_by(models.AdminUser.username).all()


def create_admin(db: Session, data: schemas.AdminCreate) -> models.AdminUser:
    admin = models.AdminUser(
        username=data.username,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        is_superadmin=data.is_superadmin,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def delete_admin(db: Session, admin: models.AdminUser) -> None:
    db.delete(admin)
    db.commit()


# ---------- Stats ----------
def dashboard_stats(db: Session) -> dict:
    total = db.query(func.count(models.Student.id)).scalar() or 0
    present = (
        db.query(func.count(models.Student.id))
        .filter(models.Student.is_present == True)  # noqa: E712
        .scalar()
        or 0
    )
    classes = db.query(func.count(models.SchoolClass.id)).scalar() or 0
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    today_events = (
        db.query(func.count(models.AttendanceRecord.id))
        .filter(models.AttendanceRecord.timestamp.between(start, end))
        .scalar()
        or 0
    )
    return {
        "total_students": total,
        "present": present,
        "absent": total - present,
        "classes": classes,
        "today_events": today_events,
    }
