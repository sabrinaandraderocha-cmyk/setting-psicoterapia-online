from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from werkzeug.security import check_password_hash

from ..core.config import settings
from ..core.database import SessionLocal
from ..models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def login_page(request: Request):
    # Se já estiver logada(o), manda pra home
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "app_name": settings.app_name, "error": None},
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    email = (email or "").strip().lower()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user or not check_password_hash(user.password_hash, password):
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "app_name": settings.app_name,
                    "error": "E-mail ou senha inválidos.",
                },
            )

        # Segurança: não deixar entrar sem organização
        if not user.organization_id:
            request.session.clear()
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "app_name": settings.app_name,
                    "error": "Conta sem organização vinculada. Solicite um convite válido.",
                },
            )

        # Sessão (BASE DO MULTIUSUÁRIO)
        request.session["user_id"] = user.id
        request.session["user_email"] = user.email
        request.session["org_id"] = user.organization_id
        request.session["role"] = user.role or "member"

        return RedirectResponse(url="/", status_code=303)

    finally:
        db.close()


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
