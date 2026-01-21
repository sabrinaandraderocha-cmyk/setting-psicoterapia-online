from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from .core.database import Base


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

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


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
