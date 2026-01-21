from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .core.config import settings
from .core.database import Base, engine, SessionLocal
from .routers import auth, session_mode, norms, documents, library
from .deps import require_auth
from .seed import seed_doc_templates  # 👈 seed inicial de modelos

# ============================
# Criação das tabelas
# ============================
Base.metadata.create_all(bind=engine)

# ============================
# App
# ============================
app = FastAPI(title=settings.app_name)

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

# ============================
# STARTUP: seed automático
# ============================
@app.on_event("startup")
def startup_seed():
    db = SessionLocal()
    try:
        seed_doc_templates(db)
    finally:
        db.close()

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
