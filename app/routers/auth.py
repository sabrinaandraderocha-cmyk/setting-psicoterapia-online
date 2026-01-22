from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from werkzeug.security import check_password_hash

from ..core.config import settings
from ..core.database import SessionLocal
from ..models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# =========================
# Login
# =========================
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "error": None
        }
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user or not check_password_hash(user.password_hash, password):
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "app_name": settings.app_name,
                    "error": "Usuário ou senha inválidos."
                }
            )

        # =========================
        # Sessão (BASE DO MULTIUSUÁRIO)
        # =========================
        request.session["user_id"] = user.id
        request.session["user_email"] = user.email
        request.session["org_id"] = user.organization_id
        request.session["role"] = user.role

        return RedirectResponse(url="/", status_code=303)

    finally:
        db.close()


# =========================
# Logout
# =========================
@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
