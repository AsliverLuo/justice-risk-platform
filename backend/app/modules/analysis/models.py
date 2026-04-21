from __future__ import annotations

from datetime import date

from sqlalchemy import Date, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import CaseType
from app.core.config import settings
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.infra.vector_store import get_vector_column_type


class CaseCorpus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'case_corpus'

    source_type: Mapped[str] = mapped_column(String(64), default='judgment', index=True)
    source_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    case_no: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    full_text: Mapped[str] = mapped_column(Text)
    case_type: Mapped[str] = mapped_column(String(64), default=CaseType.other.value, index=True)

    plaintiff_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    defendant_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    claim_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    focus_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    fact_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    judgment_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    court_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    province: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occurred_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    judgment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    entities: Mapped[dict] = mapped_column(JSON, default=dict)
    cited_laws: Mapped[list[str]] = mapped_column(JSON, default=list)
    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(
        get_vector_column_type(settings.embedding_dimension),
        nullable=True,
    )

    def to_search_text(self) -> str:
        cited_laws = ' '.join(self.cited_laws or [])
        people = ' '.join((self.entities or {}).get('persons', []))
        companies = ' '.join((self.entities or {}).get('companies', []))
        amounts = ' '.join((self.entities or {}).get('amounts', []))
        return ' '.join(
            part
            for part in [
                self.title,
                self.case_no or '',
                self.case_type,
                self.plaintiff_summary or '',
                self.defendant_summary or '',
                self.claim_summary or '',
                self.focus_summary or '',
                self.fact_summary or '',
                self.judgment_summary or '',
                cited_laws,
                people,
                companies,
                amounts,
                self.full_text,
            ]
            if part
        )
