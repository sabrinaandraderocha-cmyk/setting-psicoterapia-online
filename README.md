# Setting (MVP) — app para psicólogos focado em psicoterapia on-line

Este é um **MVP local** (rodando no seu computador) feito em **Python + FastAPI**.
Ele foi pensado como um "cockpit" de prática clínica on-line, com:

- **Modo Sessão**: checklist pré/durante/pós sessão e notas rápidas
- **Normas**: área para você registrar *cards* de normas/resoluções (ex.: CFP) e suas sínteses práticas
- **Documentos**: modelos editáveis (termos/contratos) com variáveis simples
- **Biblioteca**: upload de artigos (PDF) e criação de *cards* de conhecimento

> Observação: este projeto é **um ponto de partida** (MVP). Não é aconselhamento jurídico nem substitui revisão profissional.
> Para uso real com pacientes, será necessário reforçar segurança, LGPD, auditoria, criptografia, backups e hardening.

---

## 1) Requisitos
- Python 3.10+ (recomendado 3.11/3.12)
- Windows, macOS ou Linux

## 2) Rodar localmente (Windows PowerShell / Terminal)
Dentro da pasta do projeto:

### a) Criar e ativar ambiente virtual
**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### b) Instalar dependências
```bash
pip install -r requirements.txt
```

### c) Iniciar o servidor
```bash
uvicorn app.main:app --reload
```

Acesse no navegador:
- App: http://127.0.0.1:8000
- Docs (API): http://127.0.0.1:8000/docs

---

## 3) Login do MVP
Este MVP usa login simples só para proteger o acesso local:

- Usuário: `admin`
- Senha: `admin`

Você pode mudar em `app/core/config.py`.

---

## 4) Estrutura do projeto
```
setting_app/
  app/
    main.py
    core/
      config.py
      security.py
      database.py
    routers/
      auth.py
      session_mode.py
      norms.py
      documents.py
      library.py
    templates/
      *.html
    static/
      styles.css
    data/
      setting.db
      uploads/
  requirements.txt
  README.md
  LICENSE
```

---

## 5) Próximos passos (sugestões)
- Trocar login simples por OAuth/2FA e hashing com salt/pepper (já tem hashing básico)
- Criptografar dados sensíveis no SQLite
- Trilhas de auditoria (quem alterou o quê e quando)
- Exportação segura (PDF) dos modelos
- Pesquisa: módulo de instrumentos + exportação anonimizável

