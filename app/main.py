import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# --- Configurações e Banco de Dados ---
from .core.config import settings
from .core.database import Base, engine, SessionLocal
from .deps import require_auth

# --- Seeds ---
from .seed import seed_doc_templates
from .seed_multi import seed_org_and_admin

# --- Routers ---
from .routers import (
    auth,
    session_mode,
    norms,
    documents,
    library,
    invites,
    signup,
    invite_requests,
    org_users,
    pages,
)

# ==============================================================================
# MIDDLEWARE: AUTO-LOGOUT (SEGURANÇA DE 30 MINUTOS)
# ==============================================================================
class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout_minutes: int = 30, public_prefixes: tuple = ()):
        super().__init__(app)
        self.timeout = timedelta(minutes=timeout_minutes)
        self.public_prefixes = public_prefixes

    async def dispatch(self, request: Request, call_next):
        # 1. Ignorar rotas públicas (estáticos, login, etc.)
        if request.url.path.startswith(self.public_prefixes):
            return await call_next(request)

        # 2. Tentar recuperar a sessão
        # (SessionMiddleware deve ter rodado antes para isso existir)
        session = request.scope.get("session")

        if session is None:
            return await call_next(request)

        try:
            # 3. Verificar se usuário está logado
            if session.get("user_id"):
                now = datetime.utcnow()
                last_activity = session.get("last_activity")

                if isinstance(last_activity, str) and last_activity:
                    try:
                        last_dt = datetime.fromisoformat(last_activity)
                        # 4. Checar se expirou o tempo
                        if now - last_dt > self.timeout:
                            session.clear()
                            return RedirectResponse(url="/login?expired=1", status_code=303)
                    except Exception:
                        # Se data estiver corrompida, limpa por segurança
                        session.clear()
                        return RedirectResponse(url="/login", status_code=303)

                # 5. Se não expirou, atualiza o relógio
                session["last_activity"] = now.isoformat()

            return await call_next(request)

        except Exception:
            # Fallback de segurança: erro na validação derruba a sessão
            if session:
                session.clear()
            return RedirectResponse(url="/login", status_code=303)


# ==============================================================================
# INICIALIZAÇÃO DO APP
# ==============================================================================
app = FastAPI(title=settings.app_name)

# ==============================================================================
# MIDDLEWARES (A ORDEM IMPORTA!)
# O último adicionado é o primeiro a rodar na requisição.
# ==============================================================================

# 1. Timeout (Roda DEPOIS que a sessão é decodificada, mas ANTES da rota)
PUBLIC_PREFIXES = (
    "/login",
    "/logout",
    "/signup",
    "/solicitar-convite",
    "/static",
    "/terms",
    "/politica",
    "/health",
    "/docs",    # Opcional: liberar docs sem timeout
    "/openapi", # Opcional
)

app.add_middleware(
    SessionTimeoutMiddleware,
    timeout_minutes=30,  # Configuração de 30 minutos
    public_prefixes=PUBLIC_PREFIXES,
)

# 2. Session (Roda PRIMEIRO na requisição para criar o request.session)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-me-now"),
    same_site="lax",
    https_only=True,   # Mude para False se estiver testando em localhost sem HTTPS
    max_age=60 * 30,   # Cookie também expira em 30 min para sincronizar
)


# ==============================================================================
# CONFIGURAÇÃO DE ARQUIVOS E TEMPLATES
# ==============================================================================
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

templates = Jinja2Templates(directory="app/templates")


# ==============================================================================
# EVENTOS DE STARTUP
# ==============================================================================
@app.on_event("startup")
def on_startup():
    """
    Inicializa o banco de dados e executa seeds se necessário.
    """
    # Reset do DB apenas se variável de ambiente permitir
    if os.getenv("RESET_DB") == "1":
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    # Seeds iniciais
    db = SessionLocal()
    try:
        seed_doc_templates(db)
        seed_org_and_admin(db)
    finally:
        db.close()


# ==============================================================================
# ROTAS E ENDPOINTS
# ==============================================================================

# Logout Manual
@app.get("/logout")
def logout(request: Request):
    session = request.scope.get("session")
    if session is not None:
        session.clear()
    return RedirectResponse(url="/login", status_code=303)

# Home
@app.get("/")
def home(request: Request):
    # Verifica autenticação manual (redundância de segurança)
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "app_name": settings.app_name,
        },
    )

# Inclusão dos Routers
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
