"""Optional: populate the database with demo classes and students for testing."""
from app import crud, schemas
from app.database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)
db = SessionLocal()

demo_classes = [
    {"name": "Grade 1 - Aleph", "grade": "1", "teacher": "Rabbi Cohen"},
    {"name": "Grade 2 - Bet", "grade": "2", "teacher": "Mrs. Levi"},
    {"name": "Grade 3 - Gimel", "grade": "3", "teacher": "Mr. Friedman"},
]
class_objs = []
for c in demo_classes:
    existing = [x for x in crud.list_classes(db) if x.name == c["name"]]
    class_objs.append(existing[0] if existing else crud.create_class(db, schemas.ClassCreate(**c)))

demo_students = [
    ("1001", "Moshe", "Goldberg", "1", 0),
    ("1002", "Chaya", "Rosen", "1", 0),
    ("1003", "Dovid", "Katz", "2", 1),
    ("1004", "Rivka", "Stern", "2", 1),
    ("1005", "Yaakov", "Weiss", "3", 2),
    ("1006", "Sara", "Klein", "3", 2),
]
for sid, first, last, grade, cidx in demo_students:
    if not crud.get_student_by_student_id(db, sid):
        crud.create_student(db, schemas.StudentCreate(
            student_id=sid, first_name=first, last_name=last, grade=grade,
            class_id=class_objs[cidx].id,
        ))

db.close()
print("Demo data seeded. Student IDs: 1001-1006")
