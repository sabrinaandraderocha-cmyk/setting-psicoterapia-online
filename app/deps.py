from fastapi import Request
from sqlalchemy.orm import Session

from .core.database import SessionLocal
from .models import User


# =========================
# DB helper (se você usa em routers)
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# Auth helpers (novo padrão)
# =========================
def require_auth(request: Request) -> bool:
    """
    Autenticação baseada em SessionMiddleware.
    """
    return bool(request.session.get("user_id"))


def require_admin(request: Request) -> bool:
    return require_auth(request) and request.session.get("role") == "admin"


def get_context(request: Request) -> dict:
    return {
        "user_id": request.session.get("user_id"),
        "user_email": request.session.get("user_email"),
        "org_id": request.session.get("org_id"),
        "role": request.session.get("role"),
    }


def get_current_user(db: Session, request: Request) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()
