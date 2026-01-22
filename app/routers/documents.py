import os
from datetime import datetime

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fpdf import FPDF

from ..deps import get_db, require_auth
from ..models import DocTemplate

router = APIRouter(prefix="/documentos", tags=["Documentos"])
templates = Jinja2Templates(directory="app/templates")

# Pasta para PDFs/TXTs gerados
GENERATED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "generated"
)
os.makedirs(GENERATED_DIR, exist_ok=True)


def _org_id(request: Request) -> int | None:
    return request.session.get("org_id")


def _user_id(request: Request) -> int | None:
    return request.session.get("user_id")


@router.get("")
def docs_home(request: Request, db: Session = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    docs = (
        db.query(DocTemplate)
        .filter(DocTemplate.organization_id == org_id)
        .order_by(DocTemplate.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "documents.html",
        {"request": request, "docs": docs},
    )


@router.post("/add")
def add_doc(
    request: Request,
    name: str = Form(...),
    body: str = Form(""),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    user_id = _user_id(request)
    if not org_id or not user_id:
        return RedirectResponse(url="/logout", status_code=303)

    db.add(
        DocTemplate(
            name=name.strip(),
            body=body,
            owner_id=user_id,
            organization_id=org_id,
        )
    )
    db.commit()
    return RedirectResponse(url="/documentos", status_code=303)


@router.post("/update")
def update_doc(
    request: Request,
    doc_id: int = Form(...),
    name: str = Form(...),
    body: str = Form(""),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    obj = (
        db.query(DocTemplate)
        .filter(DocTemplate.id == doc_id, DocTemplate.organization_id == org_id)
        .first()
    )
    if obj:
        obj.name = name.strip()
        obj.body = body
        db.commit()

    return RedirectResponse(url="/documentos", status_code=303)


@router.post("/delete")
def delete_doc(
    request: Request,
    doc_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    obj = (
        db.query(DocTemplate)
        .filter(DocTemplate.id == doc_id, DocTemplate.organization_id == org_id)
        .first()
    )
    if obj:
        db.delete(obj)
        db.commit()

    return RedirectResponse(url="/documentos", status_code=303)


@router.post("/render")
def render_doc(
    request: Request,
    doc_id: int = Form(...),
    profissional_nome: str = Form(""),
    crp: str = Form(""),
    paciente_nome: str = Form(""),
    data: str = Form(""),
    tolerancia_min: str = Form("10"),
    pagamento_regras: str = Form(""),
    reagendamento_regras: str = Form(""),
    janela_contato: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Renderiza uma página HTML com o texto preenchido (para copiar).
    """
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    obj = (
        db.query(DocTemplate)
        .filter(DocTemplate.id == doc_id, DocTemplate.organization_id == org_id)
        .first()
    )
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

    return templates.TemplateResponse(
        "document_render.html",
        {"request": request, "title": obj.name, "text": out},
    )


@router.post("/render-txt")
def render_doc_txt(
    request: Request,
    doc_id: int = Form(...),
    profissional_nome: str = Form(""),
    crp: str = Form(""),
    paciente_nome: str = Form(""),
    data: str = Form(""),
    tolerancia_min: str = Form("10"),
    pagamento_regras: str = Form(""),
    reagendamento_regras: str = Form(""),
    janela_contato: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Baixa um .txt preenchido a partir de um DocTemplate (modelo criado pelo usuário).
    """
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    org_id = _org_id(request)
    if not org_id:
        return RedirectResponse(url="/logout", status_code=303)

    obj = (
        db.query(DocTemplate)
        .filter(DocTemplate.id == doc_id, DocTemplate.organization_id == org_id)
        .first()
    )
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

    safe_name = "".join([c if c.isalnum() or c in " _-" else "_" for c in (obj.name or "documento")]).strip()
    safe_name = safe_name.replace(" ", "_")[:40] or "documento"
    download_name = f"{safe_name}.txt"

    filename = f"doc_{doc_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(GENERATED_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(out + "\n")

    return FileResponse(path, filename=download_name, media_type="text/plain; charset=utf-8")


# ==========================
# TXT (documentos prontos)
# ==========================
@router.post("/gerar-documento-txt")
def gerar_documento_txt(
    request: Request,
    tipo: str = Form("declaracao"),
    paciente: str = Form(""),
    profissional: str = Form(""),
    crp: str = Form(""),
    cidade_uf: str = Form(""),
    data_emissao: str = Form(""),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    paciente = paciente.strip() or "__________"
    profissional = profissional.strip() or "__________"
    crp = crp.strip() or "__________"
    cidade_uf = cidade_uf.strip() or "__________"
    data_emissao = data_emissao.strip() or datetime.now().strftime("%d/%m/%Y")
    tipo = (tipo or "declaracao").strip().lower()

    if tipo == "atestado":
        titulo = "ATESTADO"
        corpo = (
            f"Atesto, para os devidos fins, que {paciente} esteve em atendimento psicológico na data de {data_emissao}.\n\n"
            "Este documento limita-se à finalidade declarada, resguardando o sigilo profissional e não contém informações clínicas detalhadas."
        )
        download_name = "Atestado_Setting.txt"

    elif tipo == "consentimento":
        titulo = "TERMO DE CONSENTIMENTO (PSICOTERAPIA ON-LINE)"
        corpo = (
            "Declaro estar ciente e de acordo com a realização de atendimento psicológico mediado por tecnologias digitais.\n\n"
            "1. Privacidade: comprometo-me a participar em ambiente que preserve minha privacidade.\n"
            "2. Limites: o atendimento on-line não se caracteriza como urgência/emergência.\n"
            "3. Tecnologia: podem ocorrer falhas técnicas de conexão e dispositivos.\n"
            "4. Sigilo: o sigilo profissional é assegurado, respeitando as normativas éticas aplicáveis.\n\n"
            f"Paciente: {paciente}\n"
            "Assinatura do(a) paciente: ___________________________\n\n"
            f"Profissional: {profissional} — CRP {crp}\n"
            "Assinatura do(a) profissional: _______________________"
        )
        download_name = "Termo_Consentimento_Setting.txt"

    elif tipo == "contrato":
        titulo = "CONTRATO TERAPÊUTICO (COMBINADOS)"
        corpo = (
            "Este documento estabelece combinados básicos para o funcionamento do atendimento psicoterapêutico.\n\n"
            "1. Horário e duração: sessões em dia/horário combinados, com duração aproximada de ______ minutos.\n"
            "2. Faltas e remarcações: comunicar com antecedência mínima de ______.\n"
            "3. Pagamento: ______ (forma e prazo).\n"
            "4. Comunicação entre sessões: destinada a avisos objetivos (ex.: remarcações), não substitui a sessão.\n"
            "5. Privacidade e sigilo: ambas as partes se comprometem a zelar pela privacidade do ambiente.\n\n"
            f"Paciente: {paciente}\n"
            "Assinatura do(a) paciente: ___________________________\n\n"
            f"Profissional: {profissional} — CRP {crp}\n"
            "Assinatura do(a) profissional: _______________________"
        )
        download_name = "Contrato_Terapeutico_Setting.txt"

    elif tipo == "recibo":
        titulo = "RECIBO"
        corpo = (
            f"Recebi de {paciente} a quantia de R$ ______ (__________), referente a atendimento psicológico.\n\n"
            "Forma de pagamento: ________________________________\n"
            "Referência (opcional): ______________________________\n\n"
            "Assinatura: ________________________________________"
        )
        download_name = "Recibo_Setting.txt"

    else:
        titulo = "DECLARAÇÃO DE COMPARECIMENTO"
        corpo = (
            f"Declaro, para os devidos fins, que {paciente} compareceu a atendimento psicológico na data de {data_emissao}.\n\n"
            "Esta declaração tem por finalidade exclusiva comprovar o comparecimento, não contendo informações sobre conteúdo clínico, hipótese diagnóstica ou evolução do processo."
        )
        download_name = "Declaracao_Comparecimento_Setting.txt"

    texto = (
        f"{titulo}\n\n"
        f"{corpo}\n\n"
        f"{cidade_uf}, {data_emissao}\n\n"
        f"{profissional}\n"
        f"CRP: {crp}\n\n"
    )

    filename = f"documento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(GENERATED_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(texto)

    return FileResponse(path, filename=download_name, media_type="text/plain; charset=utf-8")


# ---------- PDF (emissão) ----------

def criar_pdf_documento(
    titulo: str,
    corpo: str,
    profissional: str,
    crp: str,
    cidade_uf: str,
    data_emissao: str,
) -> str:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, titulo, ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 7, corpo)
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"{cidade_uf}, {data_emissao}", ln=True, align="R")
    pdf.ln(14)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, profissional, ln=True, align="R")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"CRP: {crp}", ln=True, align="R")

    filename = f"documento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join(GENERATED_DIR, filename)
    pdf.output(path)
    return path


@router.post("/gerar-documento-pdf")
def gerar_documento_pdf(
    request: Request,
    tipo: str = Form("declaracao"),
    paciente: str = Form(""),
    profissional: str = Form(""),
    crp: str = Form(""),
    cidade_uf: str = Form(""),
    data_emissao: str = Form(""),
    db: Session = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    paciente = paciente.strip() or "__________"
    profissional = profissional.strip() or "__________"
    crp = crp.strip() or "__________"
    cidade_uf = cidade_uf.strip() or "__________"
    data_emissao = data_emissao.strip() or datetime.now().strftime("%d/%m/%Y")
    tipo = (tipo or "declaracao").strip().lower()

    if tipo == "atestado":
        titulo = "ATESTADO"
        corpo = (
            f"Atesto, para os devidos fins, que {paciente} esteve em atendimento psicológico na data de {data_emissao}.\n\n"
            "Este documento limita-se à finalidade declarada, resguardando o sigilo profissional e não contendo informações clínicas detalhadas."
        )
        download_name = "Atestado_Setting.pdf"

    elif tipo == "consentimento":
        titulo = "TERMO DE CONSENTIMENTO (PSICOTERAPIA ON-LINE)"
        corpo = (
            "Declaro estar ciente e de acordo com a realização de atendimento psicológico mediado por tecnologias digitais.\n\n"
            "1. Privacidade: comprometo-me a participar em ambiente que preserve minha privacidade.\n"
            "2. Limites: o atendimento on-line não se caracteriza como urgência/emergência.\n"
            "3. Tecnologia: podem ocorrer falhas técnicas de conexão e dispositivos.\n"
            "4. Sigilo: o sigilo profissional é assegurado, respeitando as normativas éticas aplicáveis.\n\n"
            f"Paciente: {paciente}\n"
            "Assinatura do(a) paciente: ___________________________\n\n"
            f"Profissional: {profissional} — CRP {crp}\n"
            "Assinatura do(a) profissional: _______________________"
        )
        download_name = "Termo_Consentimento_Setting.pdf"

    elif tipo == "contrato":
        titulo = "CONTRATO TERAPÊUTICO (COMBINADOS)"
        corpo = (
            "Este documento estabelece combinados básicos para o funcionamento do atendimento psicoterapêutico.\n\n"
            "1. Horário e duração: sessões em dia/horário combinados, com duração aproximada de ______ minutos.\n"
            "2. Faltas e remarcações: comunicar com antecedência mínima de ______.\n"
            "3. Pagamento: ______ (forma e prazo).\n"
            "4. Comunicação entre sessões: destinada a avisos objetivos (ex.: remarcações), não substitui a sessão.\n"
            "5. Privacidade e sigilo: ambas as partes se comprometem a zelar pela privacidade do ambiente.\n\n"
            f"Paciente: {paciente}\n"
            "Assinatura do(a) paciente: ___________________________\n\n"
            f"Profissional: {profissional} — CRP {crp}\n"
            "Assinatura do(a) profissional: _______________________"
        )
        download_name = "Contrato_Terapeutico_Setting.pdf"

    elif tipo == "recibo":
        titulo = "RECIBO"
        corpo = (
            f"Recebi de {paciente} a quantia de R$ ______ (__________), referente a atendimento psicológico.\n\n"
            "Forma de pagamento: ________________________________\n"
            "Referência (opcional): ______________________________\n\n"
            "Assinatura: ________________________________________"
        )
        download_name = "Recibo_Setting.pdf"

    else:
        titulo = "DECLARAÇÃO DE COMPARECIMENTO"
        corpo = (
            f"Declaro, para os devidos fins, que {paciente} compareceu a atendimento psicológico na data de {data_emissao}.\n\n"
            "Esta declaração tem por finalidade exclusiva comprovar o comparecimento, não contendo informações sobre conteúdo clínico, hipótese diagnóstica ou evolução do processo."
        )
        download_name = "Declaracao_Comparecimento_Setting.pdf"

    path = criar_pdf_documento(
        titulo=titulo,
        corpo=corpo,
        profissional=profissional,
        crp=crp,
        cidade_uf=cidade_uf,
        data_emissao=data_emissao,
    )

    return FileResponse(path, filename=download_name, media_type="application/pdf")
