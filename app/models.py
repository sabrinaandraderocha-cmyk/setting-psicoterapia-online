from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import secrets
import string

from .core.database import Base


# =========================
# Helpers
# =========================
def generate_invite_code(length: int = 10) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# =========================
# Organização / Clínica
# =========================
class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    users = relationship("User", back_populates="organization")
    invites = relationship("InviteCode", back_populates="organization")


# =========================
# Usuário (profissional)
# =========================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # 👇 MULTIUSUÁRIO
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=True,
        index=True
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="member"  # admin | member
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    organization = relationship("Organization", back_populates="users")


# =========================
# Convites por código
# =========================
class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="member"
    )

    max_uses: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    uses: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    organization = relationship("Organization", back_populates="invites")

    def is_valid(self) -> bool:
        if self.revoked:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        if self.max_uses is not None and self.uses >= self.max_uses:
            return False
        return True


# =========================
# Sessões
# =========================
class SessionNote(Base):
    __tablename__ = "session_notes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    patient_alias: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    stage: Mapped[str] = mapped_column(
        String(30)  # pre, during, post
    )

    content: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    owner = relationship("User")
    organization = relationship("Organization")


# =========================
# Normas / Resumos práticos
# =========================
class NormCard(Base):
    __tablename__ = "norm_cards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    title: Mapped[str] = mapped_column(
        String(200)
    )

    source: Mapped[str] = mapped_column(
        String(300),
        default=""
    )

    practical_summary: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    tags: Mapped[str] = mapped_column(
        String(300),
        default=""
    )

    owner = relationship("User")
    organization = relationship("Organization")


# =========================
# Modelos de documentos
# =========================
class DocTemplate(Base):
    __tablename__ = "doc_templates"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    name: Mapped[str] = mapped_column(
        String(200)
    )

    body: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    owner = relationship("User")
    organization = relationship("Organization")


# =========================
# Biblioteca
# =========================
class LibraryItem(Base):
    __tablename__ = "library_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    title: Mapped[str] = mapped_column(
        String(220)
    )

    filename: Mapped[str] = mapped_column(
        String(300)
    )

    notes: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    owner = relationship("User")
    organization = relationship("Organization")
from sqlalchemy import Boolean

class InviteRequest(Base):
    __tablename__ = "invite_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    name: Mapped[str] = mapped_column(String(120), default="")
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # texto livre (motivo / vínculo / clínica)
    message: Mapped[str] = mapped_column(Text, default="")

    # status
    handled: Mapped[bool] = mapped_column(Boolean, default=False)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # opcional: qual convite foi gerado
    invite_code: Mapped[str] = mapped_column(String(32), default="")
