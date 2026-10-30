"""SQLAlchemy ORM models for the Ohr Temimim attendance system."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class AdminUser(Base):
    """A staff/admin account that can log into the admin panel."""

    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(128), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_superadmin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SchoolClass(Base):
    """A class / grade group that students belong to."""

    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    grade = Column(String(64), nullable=True)
    teacher = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    students = relationship("Student", back_populates="school_class")


class Student(Base):
    """A student. The student_id is the human-facing ID used to sign in/out."""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(64), unique=True, nullable=False, index=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    grade = Column(String(64), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    guardian_name = Column(String(255), nullable=True)
    guardian_phone = Column(String(64), nullable=True)
    photo_url = Column(String(512), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    # Current presence status, kept in sync with attendance records.
    is_present = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    school_class = relationship("SchoolClass", back_populates="students")
    attendance = relationship(
        "AttendanceRecord", back_populates="student", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class AttendanceRecord(Base):
    """A single sign-in or sign-out event for a student."""

    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    # "in" = signed in (arrived), "out" = signed out (left)
    action = Column(String(8), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String(32), default="mobile")  # mobile | admin | kiosk
    note = Column(String(255), nullable=True)

    student = relationship("Student", back_populates="attendance")


class AuditLog(Base):
    """Tracks admin actions for accountability."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    admin_username = Column(String(64), nullable=True)
    action = Column(String(255), nullable=False)
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
