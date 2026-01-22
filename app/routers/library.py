import os
from fastapi import APIRouter, Request, Form, UploadFile, File, Depends
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..deps import get_db, require_auth
from ..models import LibraryItem

router = APIRouter(prefix="/biblioteca", tags=["Biblioteca"])
templates = Jinja2Templates(directory="app/templates")

# Diretório base do app
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Pasta onde os arquivos serão salvos
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _org_id(request: Request) -> int | None:
    return request.session.get("org_id")


def _user_id(request: Request) -> int | None:
    return request.session.get("user_id")


@router.get("")
def lib_home(request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    items = (
        db.query(LibraryItem)
        .filter(LibraryItem.organization_id == org_id)
        .order_by(LibraryItem.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "biblioteca.html",
        {"request": request, "items": items}
    )


@router.post("/upload")
async def upload(
    request: Request,
    title: str = Form(...),
    notes: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    user_id = _user_id(request)
    if not org_id or not user_id:
        return RedirectResponse(url="/logout", status_code=303)

    safe_name = (
        (file.filename or "arquivo")
        .replace("..", "")
        .replace("/", "_")
        .replace("\\", "_")
    )

    # (Opcional, mas recomendado) evitar colisão de nome:
    # prefixa com org_id e timestamp pra não sobrescrever
    ts = int(__import__("time").time())
    safe_name = f"org{org_id}_{ts}_{safe_name}"

    dest = os.path.join(UPLOAD_DIR, safe_name)

    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    db.add(
        LibraryItem(
            owner_id=user_id,
            organization_id=org_id,
            title=title.strip(),
            filename=safe_name,
            notes=notes.strip(),
        )
    )
    db.commit()

    return RedirectResponse(url="/biblioteca", status_code=303)


@router.get("/file/{item_id}")
def download_file(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    item = (
        db.query(LibraryItem)
        .filter(LibraryItem.id == item_id, LibraryItem.organization_id == org_id)
        .first()
    )
    if not item:
        return RedirectResponse(url="/biblioteca", status_code=303)

    path = os.path.join(UPLOAD_DIR, item.filename)
    if not os.path.exists(path):
        return RedirectResponse(url="/biblioteca", status_code=303)

    return FileResponse(path, filename=item.filename)


@router.post("/delete")
def delete_item(
    request: Request,
    item_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    item = (
        db.query(LibraryItem)
        .filter(LibraryItem.id == item_id, LibraryItem.organization_id == org_id)
        .first()
    )
    if item:
        path = os.path.join(UPLOAD_DIR, item.filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

        db.delete(item)
        db.commit()

    return RedirectResponse(url="/biblioteca", status_code=303)
