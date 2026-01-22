from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..deps import get_db, require_auth, require_admin
from ..models import InviteRequest, InviteCode, generate_invite_code

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _org_id(request: Request) -> int | None:
    return request.session.get("org_id")


def _user_id(request: Request) -> int | None:
    return request.session.get("user_id")


# -------------------------
# Público: solicitar convite
# -------------------------
@router.get("/solicitar-convite")
def request_invite_page(request: Request):
    return templates.TemplateResponse(
        "request_invite.html",
        {"request": request, "error": None},
    )


@router.post("/solicitar-convite")
def request_invite_submit(
    request: Request,
    name: str = Form(""),
    email: str = Form(...),
    message: str = Form(""),
    db: Session = Depends(get_db),
):
    email = (email or "").strip().lower()
    name = (name or "").strip()
    message = (message or "").strip()

    if "@" not in email or "." not in email:
        return templates.TemplateResponse(
            "request_invite.html",
            {"request": request, "error": "Informe um e-mail válido."},
        )

    db.add(InviteRequest(name=name, email=email, message=message))
    db.commit()

    return templates.TemplateResponse(
        "request_invite_done.html",
        {"request": request, "email": email},
    )


# -------------------------
# Admin: ver solicitações
# -------------------------
@router.get("/admin/solicitacoes")
def admin_requests(request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse("/login", status_code=303)
    if not require_admin(request):
        return RedirectResponse("/", status_code=303)

    reqs = (
        db.query(InviteRequest)
        .order_by(InviteRequest.created_at.desc())
        .limit(100)
        .all()
    )

    return templates.TemplateResponse(
        "admin_requests.html",
        {"request": request, "reqs": reqs},
    )


# -------------------------
# Admin: aprovar (gera convite)
# -------------------------
@router.post("/admin/solicitacoes/aprovar")
def approve_request(
    request: Request,
    request_id: int = Form(...),
    expires_days: int = Form(7),
    max_uses: int = Form(1),
    role: str = Form("member"),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse("/login", status_code=303)
    if not require_admin(request):
        return RedirectResponse("/", status_code=303)

    org_id = _org_id(request)
    user_id = _user_id(request)
    if not org_id or not user_id:
        return RedirectResponse("/logout", status_code=303)

    req = db.query(InviteRequest).filter(InviteRequest.id == request_id).first()
    if not req:
        return RedirectResponse("/admin/solicitacoes", status_code=303)

    # cria convite
    code = generate_invite_code(10)
    expires_at = datetime.utcnow() + timedelta(days=expires_days)

    inv = InviteCode(
        code=code,
        organization_id=org_id,
        role=role,
        max_uses=max_uses,
        uses=0,
        expires_at=expires_at,
        revoked=False,
        created_by_user_id=user_id,
    )
    db.add(inv)

    # marca solicitação como atendida
    req.handled = True
    req.handled_at = datetime.utcnow()
    req.invite_code = code

    db.commit()

    return RedirectResponse("/admin/solicitacoes", status_code=303)
