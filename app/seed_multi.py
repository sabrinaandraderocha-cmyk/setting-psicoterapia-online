import os
from sqlalchemy.orm import Session

from .models import Organization, User


def seed_org_and_admin(db: Session):
    """
    Cria a primeira organização (clínica) e garante que o admin
    esteja ligado nela como role='admin'.
    """
    org_name = os.getenv("DEFAULT_ORG_NAME", "Setting")
    admin_username = os.getenv("ADMIN_USER", "admin")

    org = db.query(Organization).filter(Organization.name == org_name).first()
    if not org:
        org = Organization(name=org_name)
        db.add(org)
        db.commit()
        db.refresh(org)

    admin = db.query(User).filter(User.username == admin_username).first()
    if admin and admin.organization_id is None:
        admin.organization_id = org.id
        admin.role = "admin"
        db.commit()
