from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..deps import get_db, require_auth, require_admin
from ..models import User

router = APIRouter(tags=["Usuários"])
templates = Jinja2Templates(directory="app/templates")


def _org_id(request: Request) -> int | None:
    return request.session.get("org_id")


def _user_id(request: Request) -> int | None:
    return request.session.get("user_id")


@router.get("/admin/usuarios")
def list_users(request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse("/login", status_code=303)
    if not require_admin(request):
        return RedirectResponse("/", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse("/logout", status_code=303)

    users = (
        db.query(User)
        .filter(User.organization_id == org_id)
        .order_by(User.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "users": users},
    )


@router.post("/admin/usuarios/tornar-admin")
def make_admin(
    request: Request,
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse("/login", status_code=303)
    if not require_admin(request):
        return RedirectResponse("/", status_code=303)

    org_id = _org_id(request)
    current_id = _user_id(request)
    if not org_id or not current_id:
        return RedirectResponse("/logout", status_code=303)

    target = (
        db.query(User)
        .filter(User.id == user_id, User.organization_id == org_id)
        .first()
    )
    if target:
        target.role = "admin"
        db.commit()

    return RedirectResponse("/admin/usuarios", status_code=303)


@router.post("/admin/usuarios/remover-admin")
def remove_admin(
    request: Request,
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse("/login", status_code=303)
    if not require_admin(request):
        return RedirectResponse("/", status_code=303)

    org_id = _org_id(request)
    current_id = _user_id(request)
    if not org_id or not current_id:
        return RedirectResponse("/logout", status_code=303)

    # 1) Nunca permitir tirar o próprio admin
    if user_id == current_id:
        return RedirectResponse("/admin/usuarios", status_code=303)

    # 2) Nunca permitir deixar a organização sem admin
    admins_count = (
        db.query(User)
        .filter(User.organization_id == org_id, User.role == "admin")
        .count()
    )
    if admins_count <= 1:
        return RedirectResponse("/admin/usuarios", status_code=303)

    target = (
        db.query(User)
        .filter(User.id == user_id, User.organization_id == org_id)
        .first()
    )
    if target and target.role == "admin":
        target.role = "member"
        db.commit()

    return RedirectResponse("/admin/usuarios", status_code=303)
