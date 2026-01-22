from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from ..core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/termos")
def termos(request: Request):
    return templates.TemplateResponse(
        "termos.html",
        {"request": request, "app_name": settings.app_name},
    )
