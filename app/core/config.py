import os
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Setting")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-please")
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin")

settings = Settings()
