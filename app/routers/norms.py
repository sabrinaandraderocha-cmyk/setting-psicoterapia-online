from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..deps import get_db, require_auth
from ..models import NormCard

router = APIRouter(prefix="/normas", tags=["Normas"])
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def norms_home(request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)
    cards = db.query(NormCard).order_by(NormCard.created_at.desc()).limit(100).all()
    return templates.TemplateResponse("norms.html", {"request": request, "cards": cards})

@router.post("/add")
def add_card(request: Request,
             title: str = Form(...),
             source: str = Form(""),
             practical_summary: str = Form(""),
             tags: str = Form(""),
             db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)
    card = NormCard(title=title.strip(), source=source.strip(), practical_summary=practical_summary.strip(), tags=tags.strip())
    db.add(card); db.commit()
    return RedirectResponse(url="/normas", status_code=303)

@router.post("/delete")
def delete_card(request: Request, card_id: int = Form(...), db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)
    obj = db.get(NormCard, card_id)
    if obj:
        db.delete(obj); db.commit()
    return RedirectResponse(url="/normas", status_code=303)
