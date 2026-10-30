"""Application configuration for the Ohr Temimim attendance server."""
import os


class Settings:
    """Central configuration. Values can be overridden with environment variables."""

    SCHOOL_NAME: str = os.getenv("SCHOOL_NAME", "Ohr Temimim School")
    SCHOOL_NAME_HE: str = os.getenv("SCHOOL_NAME_HE", "אור תמימים")

    # The server is required to run on port 8000 only.
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database (SQLite file next to the server package by default).
    DB_PATH: str = os.getenv(
        "DB_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ohr_temimim.db"),
    )
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

    # Auth / sessions. CHANGE THIS in production via the SECRET_KEY env var.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-ohr-temimim-dev-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
    ALGORITHM: str = "HS256"

    # Default admin account created on first run if no admins exist.
    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")


settings = Settings()
