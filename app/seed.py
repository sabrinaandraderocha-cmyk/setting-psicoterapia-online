from sqlalchemy.orm import Session

from .models import DocTemplate, Organization, User

DEFAULT_DOC_TEMPLATES = [
    {
        "name": "Declaração de comparecimento",
        "body": """DECLARAÇÃO DE COMPARECIMENTO

Declaro, para os devidos fins, que {{PACIENTE_NOME}} compareceu a atendimento psicológico com {{PROFISSIONAL_NOME}}, CRP {{CRP}}, na data de {{DATA}}, em modalidade on-line.

Esta declaração tem por finalidade exclusiva comprovar o comparecimento ao atendimento, não contendo informações sobre conteúdo clínico, hipótese diagnóstica ou evolução do processo.

Local e data: {{DATA}}

____________________________________
{{PROFISSIONAL_NOME}} — CRP {{CRP}}
""",
    },
    {
        "name": "Atestado psicológico",
        "body": """ATESTADO

Atesto, para os devidos fins, que {{PACIENTE_NOME}} esteve em atendimento psicológico com {{PROFISSIONAL_NOME}}, CRP {{CRP}}, na data de {{DATA}}, em modalidade on-line.

Quando aplicável, recomenda-se o afastamento de suas atividades por ______ (______) dia(s), a contar de {{DATA}}, para preservação de condições necessárias ao cuidado.

Este documento limita-se à finalidade declarada, resguardando o sigilo profissional e não contendo informações clínicas detalhadas.

Local e data: {{DATA}}

____________________________________
{{PROFISSIONAL_NOME}} — CRP {{CRP}}
""",
    },
    {
        "name": "Termo de Consentimento (Psicoterapia on-line)",
        "body": """TERMO DE CONSENTIMENTO INFORMADO PARA PSICOTERAPIA ON-LINE

Este Termo tem por finalidade informar, de forma clara, sobre o funcionamento da psicoterapia on-line, seus limites e cuidados éticos.

1. SOBRE A PSICOTERAPIA ON-LINE
A psicoterapia on-line é uma modalidade de atendimento psicológico mediada por tecnologias digitais, regulamentada pelo Conselho Federal de Psicologia.

2. LIMITES DO ATENDIMENTO
A psicoterapia on-line não se caracteriza como atendimento de urgência ou emergência. Em situações de crise grave, o(a) paciente deverá buscar serviços da rede de saúde.

3. USO DE TECNOLOGIAS
As sessões ocorrerão por meio de plataforma previamente acordada. Apesar dos cuidados adotados, podem ocorrer falhas técnicas relacionadas à conexão e dispositivos.

4. SIGILO E PRIVACIDADE
O sigilo profissional é assegurado conforme o Código de Ética Profissional do Psicólogo. Recomenda-se que o(a) paciente participe das sessões em ambiente que preserve sua privacidade.

5. REGISTROS E DADOS
O(a) psicólogo(a) poderá realizar registros técnicos mínimos, com finalidade clínica e ética, respeitando o princípio da minimização de dados.

6. COMUNICAÇÃO ENTRE SESSÕES
A comunicação fora das sessões seguirá combinados previamente definidos e não substitui o espaço terapêutico.

Declaro que li, compreendi e tive oportunidade de esclarecer dúvidas.

Local e data: {{DATA}}

Nome do(a) paciente: {{PACIENTE_NOME}}
Assinatura do(a) paciente: ___________________________

{{PROFISSIONAL_NOME}} — CRP {{CRP}}
Assinatura do(a) psicólogo(a): _______________________
""",
    },
    {
        "name": "Combinados do setting on-line",
        "body": """COMBINADOS DO SETTING TERAPÊUTICO ON-LINE

Este documento estabelece combinados básicos para o funcionamento do atendimento psicoterapêutico on-line, favorecendo clareza, continuidade do processo e cuidado com o setting digital.

1. HORÁRIO E DURAÇÃO
As sessões ocorrem em dia e horário combinados, com duração aproximada de ______ minutos.

2. FALTAS E REMARCAÇÕES
Cancelamentos/remarcações devem ser comunicados com antecedência mínima de {{REAGENDAMENTO_REGRAS}}.

3. COMUNICAÇÃO ENTRE SESSÕES
A comunicação fora da sessão destina-se a avisos objetivos (ex.: remarcações). Demandas urgentes devem seguir orientações acordadas.

4. URGÊNCIAS
O atendimento on-line não substitui serviços de urgência/emergência. Em crise, buscar rede de saúde/CAPS/hospital ou CVV (188).

5. SIGILO E PRIVACIDADE
Ambas as partes comprometem-se a zelar pela privacidade do ambiente e das informações compartilhadas.

6. PAGAMENTO
Regras de pagamento: {{PAGAMENTO_REGRAS}}.

7. REGISTROS
Registros técnicos seguirão o princípio do mínimo necessário, sem dados identificáveis e sem detalhamento excessivo.

Local e data: {{DATA}}

Assinatura do(a) paciente: ___________________________

{{PROFISSIONAL_NOME}} — CRP {{CRP}}
Assinatura do(a) psicólogo(a): _______________________
""",
    },
]


def seed_doc_templates(db: Session) -> int:
    """
    Cria modelos padrão PARA CADA ORGANIZAÇÃO, apenas se ainda não existirem
    (por organization_id + name). Preenche owner_id com o admin da org.
    Retorna quantos foram criados no total.
    """
    created = 0

    orgs = db.query(Organization).all()
    for org in orgs:
        admin = (
            db.query(User)
            .filter(User.organization_id == org.id, User.role == "admin")
            .first()
        )
        if not admin:
            # sem admin, não dá pra setar owner_id com segurança
            continue

        for tpl in DEFAULT_DOC_TEMPLATES:
            exists = (
                db.query(DocTemplate)
                .filter(
                    DocTemplate.organization_id == org.id,
                    DocTemplate.name == tpl["name"],
                )
                .first()
            )
            if exists:
                continue

            db.add(
                DocTemplate(
                    owner_id=admin.id,
                    organization_id=org.id,
                    name=tpl["name"],
                    body=tpl["body"],
                )
            )
            created += 1

    if created:
        db.commit()

    return created
