from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .core.database import Base

class SessionNote(Base):
    __tablename__ = "session_notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    patient_alias: Mapped[str] = mapped_column(String(120), default="")
    stage: Mapped[str] = mapped_column(String(30))  # pre, during, post
    content: Mapped[str] = mapped_column(Text, default="")

class NormCard(Base):
    __tablename__ = "norm_cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    title: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(300), default="")
    practical_summary: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(String(300), default="")

class DocTemplate(Base):
    __tablename__ = "doc_templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    name: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")

class LibraryItem(Base):
    __tablename__ = "library_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    title: Mapped[str] = mapped_column(String(220))
    filename: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str] = mapped_column(Text, default="")
