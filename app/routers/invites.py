from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..deps import get_db, require_auth, require_admin
from ..models import InviteCode, generate_invite_code

router = APIRouter(prefix="/invites", tags=["Convites"])
templates = Jinja2Templates(directory="app/templates")


# =========================
# Helpers de sessão
# =========================
def _org_id(request: Request) -> int | None:
    return request.session.get("org_id")


def _user_id(request: Request) -> int | None:
    return request.session.get("user_id")


# =========================
# Página de convites (ADMIN)
# =========================
@router.get("")
def invites_home(request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    if not require_admin(request):
        return RedirectResponse(url="/", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    invites = (
        db.query(InviteCode)
        .filter(InviteCode.organization_id == org_id)
        .order_by(InviteCode.created_at.desc())
        .limit(50)
        .all()
    )

    return templates.TemplateResponse(
        "invites.html",
        {
            "request": request,
            "invites": invites,
        },
    )


# =========================
# Criar convite
# =========================
@router.post("/create")
def create_invite(
    request: Request,
    role: str = Form("member"),
    max_uses: int = Form(1),
    expires_days: int = Form(7),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    if not require_admin(request):
        return RedirectResponse(url="/", status_code=303)

    org_id = _org_id(request)
    user_id = _user_id(request)

    if not org_id or not user_id:
        return RedirectResponse(url="/logout", status_code=303)

    code = generate_invite_code(10)
    expires_at = datetime.utcnow() + timedelta(days=expires_days)

    invite = InviteCode(
        code=code,
        organization_id=org_id,
        role=role,
        max_uses=max_uses,
        uses=0,
        expires_at=expires_at,
        revoked=False,
        created_by_user_id=user_id,
    )

    db.add(invite)
    db.commit()

    return RedirectResponse(url="/invites", status_code=303)


# =========================
# Visualizar convite individual
# =========================
@router.get("/{code}")
def show_invite(code: str, request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    if not require_admin(request):
        return RedirectResponse(url="/", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    invite = (
        db.query(InviteCode)
        .filter(
            InviteCode.code == code,
            InviteCode.organization_id == org_id,
        )
        .first()
    )

    if not invite:
        return RedirectResponse(url="/invites", status_code=303)

    return templates.TemplateResponse(
        "invite_show.html",
        {
            "request": request,
            "code": invite.code,
            "signup_url": f"/signup?code={invite.code}",
            "expires_at": invite.expires_at,
            "max_uses": invite.max_uses,
            "uses": invite.uses,
            "revoked": invite.revoked,
        },
    )
