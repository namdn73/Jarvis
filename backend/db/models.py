from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DbSession(Base):
    __tablename__ = "sessions"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at:   Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    queries: Mapped[list["DbQuery"]] = relationship("DbQuery", back_populates="session")


class DbQuery(Base):
    __tablename__ = "queries"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True)
    session_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    text:        Mapped[str]      = mapped_column(Text, nullable=False)
    timestamp:   Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    search_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "news"|"general"|"knowledge"

    session: Mapped[DbSession]       = relationship("DbSession", back_populates="queries")
    results: Mapped[list["DbResult"]] = relationship("DbResult", back_populates="query")


class DbResult(Base):
    __tablename__ = "results"

    id:       Mapped[int] = mapped_column(Integer, primary_key=True)
    query_id: Mapped[int] = mapped_column(Integer, ForeignKey("queries.id"), nullable=False)
    title:    Mapped[str] = mapped_column(Text, nullable=False)
    url:      Mapped[str] = mapped_column(Text, nullable=False)
    snippet:  Mapped[str] = mapped_column(Text, nullable=False)
    source:   Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # 0–4, card order

    query: Mapped[DbQuery] = relationship("DbQuery", back_populates="results")
