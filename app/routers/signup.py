from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from werkzeug.security import generate_password_hash

from ..core.database import SessionLocal
from ..models import InviteCode, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/signup")
def signup_page(request: Request, code: str = ""):
    # Página de cadastro via convite
    return templates.TemplateResponse(
        "signup.html",
        {
            "request": request,
            "code": code,
            "error": None,
        },
    )


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
        if not inv or not inv.is_valid():
            return templates.TemplateResponse(
                "signup.html",
                {
                    "request": request,
                    "code": code,
                    "error": "Convite inválido, expirado ou revogado.",
                },
            )

        exists = db.query(User).filter(User.email == email).first()
        if exists:
            return templates.TemplateResponse(
                "signup.html",
                {
                    "request": request,
                    "code": code,
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

        inv.uses += 1
        db.commit()

        return RedirectResponse(url="/login", status_code=303)

    finally:
        db.close()
