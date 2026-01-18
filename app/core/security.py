from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer, BadSignature
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeSerializer(settings.secret_key, salt="setting-session")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def sign_session(data: dict) -> str:
    return serializer.dumps(data)

def unsign_session(token: str) -> dict | None:
    try:
        return serializer.loads(token)
    except BadSignature:
        return None
