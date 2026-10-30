"""Ohr Temimim School — attendance server & admin panel (FastAPI).

Runs on port 8000. Serves:
  - JSON API under /api (used by the student mobile APK)
  - HTML admin panel at / (login, dashboard, students, attendance, etc.)
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import crud, models, schemas
from .config import settings
from .database import Base, SessionLocal, engine
from .routers import admin_ui, api

app = FastAPI(title=f"{settings.SCHOOL_NAME} Attendance API", version="1.0.0")

# Allow the mobile app (any origin) to call the JSON API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Session cookie for the HTML admin panel.
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(api.router)
app.include_router(admin_ui.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed a default admin if none exist.
        if not crud.list_admins(db):
            crud.create_admin(
                db,
                schemas.AdminCreate(
                    username=settings.DEFAULT_ADMIN_USERNAME,
                    password=settings.DEFAULT_ADMIN_PASSWORD,
                    full_name="Default Administrator",
                    is_superadmin=True,
                ),
            )
            print(
                f"[seed] Created default admin '{settings.DEFAULT_ADMIN_USERNAME}' "
                f"(password: '{settings.DEFAULT_ADMIN_PASSWORD}'). Change this in production!"
            )
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "school": settings.SCHOOL_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
