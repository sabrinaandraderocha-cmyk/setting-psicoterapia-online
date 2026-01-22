from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..deps import require_auth
from ..models import InviteCode, User, generate_invite_code

router = APIRouter()


def _get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def get_current_username(request: Request) -> str | None:
    """
    Tenta achar o username salvo na sessão.
    (mantém compatível com implementações diferentes)
    """
    # comuns: "user", "username"
    return request.session.get("user") or request.session.get("username")


def get_current_user(db: Session, request: Request) -> User | None:
    username = get_current_username(request)
    if not username:
        return None
    return db.query(User).filter(User.username == username).first()


@router.post("/invites/create")
def create_invite(
    request: Request,
    role: str = Form("member"),
    max_uses: int = Form(1),
    expires_days: int = Form(7),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    db = _get_db()
    try:
        user = get_current_user(db, request)
        if not user or user.role != "admin":
            return RedirectResponse(url="/", status_code=303)

        code = generate_invite_code(10)
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

        inv = InviteCode(
            code=code,
            organization_id=user.organization_id,
            role=role,
            max_uses=max_uses,
            uses=0,
            expires_at=expires_at,
            revoked=False,
            created_by_user_id=user.id,
        )
        db.add(inv)
        db.commit()

        return RedirectResponse(url=f"/invites/{code}", status_code=303)
    finally:
        db.close()


@router.get("/invites/{code}")
def show_invite(code: str):
    # Por enquanto simples (depois fazemos uma tela bonita em template)
    return {"invite_code": code, "signup_url": f"/signup?code={code}"}
