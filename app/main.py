import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .core.config import settings
from .core.database import Base, engine, SessionLocal
from .routers import auth, session_mode, norms, documents, library

# 👇 NOVO: routers de convite + cadastro por código
from .routers import invites, signup

from .deps import require_auth
from .seed import seed_doc_templates

# 👇 NOVO: seed multi (cria Organization e liga admin)
from .seed_multi import seed_org_and_admin

# ============================
# App
# ============================
app = FastAPI(title=settings.app_name)

# ============================
# STARTUP (seguro no Render)
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
        seed_org_and_admin(db)  # 👈 NOVO
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

# 👇 NOVO
app.include_router(invites.router)
app.include_router(signup.router)

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
