from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..deps import get_db, require_auth
from ..models import SessionNote

router = APIRouter(prefix="/modo-sessao", tags=["Modo Sessão"])
templates = Jinja2Templates(directory="app/templates")


def _org_id(request: Request) -> int | None:
    return request.session.get("org_id")


def _user_id(request: Request) -> int | None:
    return request.session.get("user_id")


@router.get("")
def session_home(request: Request, patient: str = "", db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    # lista de pacientes/apelidos (para filtro) - SOMENTE da clínica
    patients = (
        db.query(SessionNote.patient_alias)
        .filter(
            SessionNote.organization_id == org_id,
            SessionNote.patient_alias != ""
        )
        .distinct()
        .order_by(SessionNote.patient_alias.asc())
        .all()
    )
    patients = [p[0] for p in patients]

    q = db.query(SessionNote).filter(SessionNote.organization_id == org_id)

    # filtro opcional
    if patient:
        q = q.filter(SessionNote.patient_alias == patient)

    notes = (
        q.order_by(SessionNote.patient_alias.asc(), SessionNote.created_at.desc())
        .limit(200)
        .all()
    )

    return templates.TemplateResponse(
        "session_mode.html",
        {
            "request": request,
            "notes": notes,
            "patients": patients,
            "selected_patient": patient
        },
    )


@router.post("/add")
def add_note(
    request: Request,
    stage: str = Form(...),
    patient_alias: str = Form(""),
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    user_id = _user_id(request)
    if not org_id or not user_id:
        return RedirectResponse(url="/logout", status_code=303)

    note = SessionNote(
        owner_id=user_id,
        organization_id=org_id,
        stage=stage,
        patient_alias=patient_alias.strip(),
        content=content.strip(),
    )
    db.add(note)
    db.commit()
    return RedirectResponse(url="/modo-sessao", status_code=303)


@router.post("/update")
def update_note(
    request: Request,
    note_id: int = Form(...),
    stage: str = Form(...),
    patient_alias: str = Form(""),
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    obj = (
        db.query(SessionNote)
        .filter(SessionNote.id == note_id, SessionNote.organization_id == org_id)
        .first()
    )
    if obj:
        obj.stage = stage
        obj.patient_alias = patient_alias.strip()
        obj.content = content.strip()
        db.commit()

    ref = request.headers.get("referer") or "/modo-sessao"
    return RedirectResponse(url=ref, status_code=303)


@router.post("/delete")
def delete_note(
    request: Request,
    note_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    obj = (
        db.query(SessionNote)
        .filter(SessionNote.id == note_id, SessionNote.organization_id == org_id)
        .first()
    )
    if obj:
        db.delete(obj)
        db.commit()

    ref = request.headers.get("referer") or "/modo-sessao"
    return RedirectResponse(url=ref, status_code=303)
