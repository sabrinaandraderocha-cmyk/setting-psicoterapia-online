from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..deps import get_db, require_auth
from ..models import NormCard

router = APIRouter(prefix="/normas", tags=["Normas"])
templates = Jinja2Templates(directory="app/templates")


def _org_id(request: Request) -> int | None:
    return request.session.get("org_id")


def _user_id(request: Request) -> int | None:
    return request.session.get("user_id")


@router.get("")
def norms_home(request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    cards = (
        db.query(NormCard)
        .filter(NormCard.organization_id == org_id)
        .order_by(NormCard.created_at.desc())
        .limit(100)
        .all()
    )

    return templates.TemplateResponse(
        "norms.html",
        {"request": request, "cards": cards}
    )


@router.post("/add")
def add_card(
    request: Request,
    title: str = Form(...),
    source: str = Form(""),
    practical_summary: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    user_id = _user_id(request)
    if not org_id or not user_id:
        return RedirectResponse(url="/logout", status_code=303)

    card = NormCard(
        owner_id=user_id,
        organization_id=org_id,
        title=title.strip(),
        source=source.strip(),
        practical_summary=practical_summary.strip(),
        tags=tags.strip(),
    )
    db.add(card)
    db.commit()

    return RedirectResponse(url="/normas", status_code=303)


@router.post("/delete")
def delete_card(
    request: Request,
    card_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    obj = (
        db.query(NormCard)
        .filter(NormCard.id == card_id, NormCard.organization_id == org_id)
        .first()
    )
    if obj:
        db.delete(obj)
        db.commit()

    return RedirectResponse(url="/normas", status_code=303)
