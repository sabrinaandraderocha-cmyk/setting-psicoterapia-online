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

# Pasta onde os arquivos PDF serão salvos
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("")
def lib_home(request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    items = (
        db.query(LibraryItem)
        .order_by(LibraryItem.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "biblioteca.html",
        {
            "request": request,
            "items": items
        }
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

    safe_name = (
        file.filename
        .replace("..", "")
        .replace("/", "_")
        .replace("\\", "_")
    )

    dest = os.path.join(UPLOAD_DIR, safe_name)

    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    db.add(
        LibraryItem(
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

    item = db.get(LibraryItem, item_id)
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

    item = db.get(LibraryItem, item_id)
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
