from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from ..deps import require_auth

router = APIRouter(prefix="/biblioteca", tags=["Biblioteca"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def biblioteca_home(request: Request):
    """
    Biblioteca formativa do Setting.

    - Conteúdo base fixo (textos autorais)
    - Links externos para pesquisa acadêmica
    - Nenhum upload
    - Nenhum armazenamento de documentos do usuário
    """

    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "biblioteca.html",
        {
            "request": request
        }
    )
