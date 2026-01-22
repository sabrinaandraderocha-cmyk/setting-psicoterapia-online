import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .core.config import settings
from .core.database import Base, engine, SessionLocal
from .deps import require_auth

# Routers principais
from .routers import auth, session_mode, norms, documents, library

# Convites e cadastro
from .routers import invites, signup
from .routers import invite_requests

# Gestão de usuários da organização
from .routers import org_users

# 🔹 NOVO: páginas institucionais (termos, política etc.)
from .routers import pages

from .seed import seed_doc_templates
from .seed_multi import seed_org_and_admin

# ============================
# App
# ============================
app = FastAPI(title=settings.app_name)

# ============================
# SESSION MIDDLEWARE
# ============================
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-me-now"),
    same_site="lax",
    https_only=True,
)

# ============================
# STARTUP
# ============================
@app.on_event("startup")
def on_startup():
    """
    - Cria tabelas automaticamente
    - Reset do banco SOMENTE se RESET_DB=1
    - Seed inicial controlado
    """
    if os.getenv("RESET_DB") == "1":
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_doc_templates(db)
        seed_org_and_admin(db)
    finally:
        db.close()

# ============================
# Arquivos estáticos e templates
# ============================
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

templates = Jinja2Templates(directory="app/templates")

# ============================
# Rotas
# ============================
app.include_router(auth.router)
app.include_router(session_mode.router)
app.include_router(norms.router)
app.include_router(documents.router)
app.include_router(library.router)

app.include_router(invites.router)
app.include_router(signup.router)
app.include_router(invite_requests.router)
app.include_router(org_users.router)

# 🔹 PÁGINAS INSTITUCIONAIS
app.include_router(pages.router)

# ============================
# HOME
# ============================
@app.get("/")
def home(request: Request):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "app_name": settings.app_name,
        }
    )
