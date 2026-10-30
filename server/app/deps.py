"""Authentication dependencies for API (bearer token) and admin UI (session cookie)."""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import crud, models
from .database import get_db
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login", auto_error=False)


def get_current_admin(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.AdminUser:
    """Bearer-token auth for JSON API admin endpoints."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exc
    admin = crud.get_admin_by_username(db, payload["sub"])
    if not admin or not admin.is_active:
        raise credentials_exc
    return admin


def get_session_admin(request: Request, db: Session = Depends(get_db)):
    """Cookie-session auth for the HTML admin panel. Returns None if not logged in."""
    username = request.session.get("admin")
    if not username:
        return None
    admin = crud.get_admin_by_username(db, username)
    if not admin or not admin.is_active:
        return None
    return admin


def require_session_admin(request: Request, db: Session = Depends(get_db)) -> models.AdminUser:
    admin = get_session_admin(request, db)
    if not admin:
        raise HTTPException(status_code=status.HTTP_302_FOUND, headers={"Location": "/login"})
    return admin
