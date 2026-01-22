from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from werkzeug.security import generate_password_hash

from ..core.database import SessionLocal
from ..models import InviteCode, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _invite_status(inv: InviteCode) -> dict:
    """Retorna info amigável para a UI."""
    now = datetime.utcnow()
    expires_at = inv.expires_at
    expired = bool(expires_at and now > expires_at)
    remaining = None
    if inv.max_uses is not None:
        remaining = max(inv.max_uses - (inv.uses or 0), 0)

    return {
        "exists": True,
        "code": inv.code,
        "revoked": bool(inv.revoked),
        "expired": expired,
        "expires_at": expires_at,
        "uses": inv.uses or 0,
        "max_uses": inv.max_uses,
        "remaining": remaining,
        "is_valid": inv.is_valid(),
    }


@router.get("/signup")
def signup_page(request: Request, code: str = ""):
    code = (code or "").strip()

    db = SessionLocal()
    try:
        inv = db.query(InviteCode).filter(InviteCode.code == code).first() if code else None

        invite = None
        error = None

        if code and not inv:
            error = "Convite não encontrado. Verifique o código."
        elif inv:
            invite = _invite_status(inv)
            if invite["revoked"]:
                error = "Este convite foi revogado."
            elif invite["expired"]:
                error = "Este convite expirou."
            elif invite["remaining"] == 0:
                error = "Este convite já foi utilizado."
            # se válido, não mostra erro

        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "code": code,
                "invite": invite,   # pode ser None
                "error": error,     # pode ser None
            },
        )
    finally:
        db.close()


@router.post("/signup")
def signup_with_code(
    request: Request,
    code: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    code = (code or "").strip()
    email = (email or "").strip().lower()

    db = SessionLocal()
    try:
        inv = db.query(InviteCode).filter(InviteCode.code == code).first()
        if not inv:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "code": code, "invite": None, "error": "Convite não encontrado."},
            )

        invite = _invite_status(inv)

        if not inv.is_valid():
            # mensagem mais clara
            if invite["revoked"]:
                msg = "Este convite foi revogado."
            elif invite["expired"]:
                msg = "Este convite expirou."
            elif invite["remaining"] == 0:
                msg = "Este convite já foi utilizado."
            else:
                msg = "Convite inválido."
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "code": code, "invite": invite, "error": msg},
            )

        exists = db.query(User).filter(User.email == email).first()
        if exists:
            return templates.TemplateResponse(
                "signup.html",
                {
                    "request": request,
                    "code": code,
                    "invite": invite,
                    "error": "Este e-mail já está cadastrado. Faça login.",
                },
            )

        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            organization_id=inv.organization_id,
            role=inv.role or "member",
        )
        db.add(user)

        inv.uses = (inv.uses or 0) + 1
        db.commit()

        return RedirectResponse(url="/login", status_code=303)

    finally:
        db.close()
