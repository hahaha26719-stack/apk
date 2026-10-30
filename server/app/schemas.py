"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ---------- Students ----------
class StudentBase(BaseModel):
    student_id: str
    first_name: str
    last_name: str
    grade: Optional[str] = None
    class_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    student_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    grade: Optional[str] = None
    class_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class StudentOut(StudentBase):
    id: int
    is_present: bool
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Attendance ----------
class CheckRequest(BaseModel):
    student_id: str
    note: Optional[str] = None


class AttendanceOut(BaseModel):
    id: int
    student_id: int
    action: str
    timestamp: datetime
    source: str
    note: Optional[str] = None

    class Config:
        from_attributes = True


class CheckResponse(BaseModel):
    ok: bool
    action: str
    student_name: str
    student_id: str
    is_present: bool
    timestamp: datetime
    message: str


class StudentStatus(BaseModel):
    student_id: str
    full_name: str
    grade: Optional[str] = None
    is_present: bool
    last_action: Optional[str] = None
    last_timestamp: Optional[datetime] = None


# ---------- Classes ----------
class ClassBase(BaseModel):
    name: str
    grade: Optional[str] = None
    teacher: Optional[str] = None


class ClassCreate(ClassBase):
    pass


class ClassOut(ClassBase):
    id: int
    student_count: int = 0

    class Config:
        from_attributes = True


# ---------- Admin users ----------
class AdminCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    is_superadmin: bool = False


class AdminOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    is_superadmin: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
