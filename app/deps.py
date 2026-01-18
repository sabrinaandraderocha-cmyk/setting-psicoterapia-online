from fastapi import Request
from .core.database import SessionLocal
from .core.security import unsign_session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_auth(request: Request) -> bool:
    token = request.cookies.get("setting_session")
    if not token:
        return False
    data = unsign_session(token)
    return bool(data and data.get("u") == "admin")
