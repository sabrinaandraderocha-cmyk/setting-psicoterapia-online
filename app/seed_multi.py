import os
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from .models import Organization, User


def seed_org_and_admin(db: Session):
    """
    - Cria a organização padrão (DEFAULT_ORG_NAME ou 'Setting')
    - Cria o usuário admin do ENV (ADMIN_USER/ADMIN_PASSWORD) se não existir
    - Garante que o admin esteja ligado à organização como role='admin'
    """

    org_name = os.getenv("DEFAULT_ORG_NAME", "Setting")

    # Seu User é por EMAIL:
    admin_email = os.getenv("ADMIN_USER", "admin@setting.app")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")

    # 1) Organization
    org = db.query(Organization).filter(Organization.name == org_name).first()
    if not org:
        org = Organization(name=org_name)
        db.add(org)
        db.commit()
        db.refresh(org)

    # 2) Admin user
    admin = db.query(User).filter(User.email == admin_email).first()
    if not admin:
        admin = User(
            email=admin_email,
            password_hash=generate_password_hash(admin_password),
            organization_id=org.id,
            role="admin",
        )
        db.add(admin)
        db.commit()
        return

    # 3) Garantir vínculo e role
    changed = False
    if admin.organization_id is None:
        admin.organization_id = org.id
        changed = True
    if admin.role != "admin":
        admin.role = "admin"
        changed = True

    if changed:
        db.commit()
