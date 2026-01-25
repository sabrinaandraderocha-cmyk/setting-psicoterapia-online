import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

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

# Páginas institucionais
from .routers import pages

from .seed import seed_doc_templates
from .seed_multi import seed_org_and_admin


# ============================
# MIDDLEWARE: AUTO-LOGOUT
# (roda DEPOIS do SessionMiddleware)
# ============================
class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout_minutes: int = 30, public_prefixes=()):
        super().__init__(app)
        self.timeout = timedelta(minutes=timeout_minutes)
        self.public_prefixes = public_prefixes

    async def dispatch(self, request: Request, call_next):
        # rotas públicas não controlam sessão
        if request.url.path.startswith(self.public_prefixes):
            return await call_next(request)

        # ✅ aqui já deve existir, porque SessionMiddleware roda antes
        session = request.scope.get("session")

        # se por algum motivo não existir, não derruba o app
        if session is None:
            return await call_next(request)

        try:
            if session.get("user_id"):
                now = datetime.utcnow()
                last_activity = session.get("last_activity")

                if isinstance(last_activity, str) and last_activity:
                    try:
                        last_dt = datetime.fromisoformat(last_activity)
                        if now - last_dt > self.timeout:
                            session.clear()
                            return RedirectResponse(url="/login", status_code=303)
                    except Exception:
                        session.clear()
                        return RedirectResponse(url="/login", status_code=303)

                # atualiza atividade
                session["last_activity"] = now.isoformat()

            return await call_next(request)

        except Exception:
            # fallback total: nunca deixar virar 500 por causa de sessão
            session.clear()
            return RedirectResponse(url="/login", status_code=303)


# ============================
# App
# ============================
app = FastAPI(title=settings.app_name)

# ============================
# SESSION MIDDLEWARE (PRECISA VIR ANTES)
# ============================
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-me-now"),
    same_site="lax",
    https_only=True,
    max_age=60 * 30,  # cookie expira em 30 min
)

# ============================
# AUTO-LOGOUT POR INATIVIDADE
# ============================
PUBLIC_PREFIXES = (
    "/login",
    "/logout",
    "/signup",
    "/solicitar-convite",
    "/static",
    "/terms",
    "/politica",
    "/health",
)

app.add_middleware(
    SessionTimeoutMiddleware,
    timeout_minutes=30,
    public_prefixes=PUBLIC_PREFIXES,
)

# ============================
# LOGOUT MANUAL
# ============================
@app.get("/logout")
def logout(request: Request):
    session = request.scope.get("session")
    if session is not None:
        session.clear()
    return RedirectResponse(url="/login", status_code=303)

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
    name="static",
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
        },
    )
