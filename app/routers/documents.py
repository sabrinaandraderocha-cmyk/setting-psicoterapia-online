from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..deps import get_db, require_auth
from ..models import DocTemplate

router = APIRouter(prefix="/documentos", tags=["Documentos"])
templates = Jinja2Templates(directory="app/templates")

DEFAULT_TEMPLATES = [
    ("Termo de consentimento para psicoterapia on-line (rascunho)",
"""TERMO DE CONSENTIMENTO PARA PSICOTERAPIA ON-LINE

Profissional: {{PROFISSIONAL_NOME}} (CRP: {{CRP}})
Paciente: {{PACIENTE_NOME}}
Data: {{DATA}}

1. Objetivo
Este termo registra o consentimento informado para a realização de psicoterapia por meios digitais.

2. Confidencialidade e privacidade
As sessões dependem de condições mínimas de privacidade (ambiente reservado, uso de fones quando necessário, ausência de terceiros).

3. Registros e armazenamento
O profissional realizará registros clínicos mínimos necessários, mantendo sigilo e segurança conforme legislação aplicável.

4. Limites e emergências
Este atendimento não substitui serviços de urgência/emergência. Em risco imediato, procure o serviço local e/ou acione contatos de emergência.

Assinaturas:
Profissional: ______________________
Paciente: _________________________
"""),
    ("Contrato terapêutico e combinados do setting on-line (rascunho)",
"""COMBINADOS DO SETTING ON-LINE

Profissional: {{PROFISSIONAL_NOME}} (CRP: {{CRP}})
Paciente: {{PACIENTE_NOME}}

- Pontualidade: tolerância de {{TOLERANCIA_MIN}} minutos.
- Pagamento: {{PAGAMENTO_REGRAS}}
- Reagendamento/cancelamento: {{REAGENDAMENTO_REGRAS}}
- Ambiente: paciente se compromete a buscar local privado e estável.
- Comunicação entre sessões: {{JANELA_CONTATO}}

Assinaturas:
Profissional: ______________________
Paciente: _________________________
"""),
]

@router.get("")
def docs_home(request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)
    # seed only once
    if db.query(DocTemplate).count() == 0:
        for name, body in DEFAULT_TEMPLATES:
            db.add(DocTemplate(name=name, body=body))
        db.commit()

    docs = db.query(DocTemplate).order_by(DocTemplate.created_at.desc()).all()
    return templates.TemplateResponse("documents.html", {"request": request, "docs": docs})

@router.post("/add")
def add_doc(request: Request, name: str = Form(...), body: str = Form(...), db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)
    db.add(DocTemplate(name=name.strip(), body=body))
    db.commit()
    return RedirectResponse(url="/documentos", status_code=303)

@router.post("/update")
def update_doc(request: Request, doc_id: int = Form(...), name: str = Form(...), body: str = Form(...), db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)
    obj = db.get(DocTemplate, doc_id)
    if obj:
        obj.name = name.strip()
        obj.body = body
        db.commit()
    return RedirectResponse(url="/documentos", status_code=303)

@router.post("/render")
def render_doc(request: Request,
               doc_id: int = Form(...),
               profissional_nome: str = Form(""),
               crp: str = Form(""),
               paciente_nome: str = Form(""),
               data: str = Form(""),
               tolerancia_min: str = Form("10"),
               pagamento_regras: str = Form(""),
               reagendamento_regras: str = Form(""),
               janela_contato: str = Form(""),
               db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)
    obj = db.get(DocTemplate, doc_id)
    if not obj:
        return RedirectResponse(url="/documentos", status_code=303)

    out = obj.body
    repl = {
        "{{PROFISSIONAL_NOME}}": profissional_nome or "__________",
        "{{CRP}}": crp or "__________",
        "{{PACIENTE_NOME}}": paciente_nome or "__________",
        "{{DATA}}": data or "__________",
        "{{TOLERANCIA_MIN}}": tolerancia_min or "10",
        "{{PAGAMENTO_REGRAS}}": pagamento_regras or "__________",
        "{{REAGENDAMENTO_REGRAS}}": reagendamento_regras or "__________",
        "{{JANELA_CONTATO}}": janela_contato or "__________",
    }
    for k, v in repl.items():
        out = out.replace(k, v)

    return PlainTextResponse(out, media_type="text/plain; charset=utf-8")
