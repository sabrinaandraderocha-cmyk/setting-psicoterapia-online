from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from ..core.config import settings
from ..core.security import sign_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "app_name": settings.app_name, "error": None})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == settings.admin_username and password == settings.admin_password:
        token = sign_session({"u": "admin"})
        resp = RedirectResponse(url="/", status_code=303)
        resp.set_cookie("setting_session", token, httponly=True, samesite="lax")
        return resp
    return templates.TemplateResponse("login.html", {"request": request, "app_name": settings.app_name, "error": "Usuário ou senha inválidos."})

@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("setting_session")
    return resp
