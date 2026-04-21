from __future__ import annotations

from datetime import date

from sqlalchemy import Date, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import KnowledgeSourceType
from app.core.config import settings
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.infra.vector_store import get_vector_column_type


class LegalKnowledge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "legal_knowledge"

    article_no: Mapped[str] = mapped_column(String(64), index=True)
    law_name: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    scenario_tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    source_type: Mapped[str] = mapped_column(
        String(64),
        default=KnowledgeSourceType.law.value,
        index=True,
    )
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)

    extra_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(
        get_vector_column_type(settings.embedding_dimension),
        nullable=True,
    )

    def to_search_text(self) -> str:
        return " ".join(
            part
            for part in [
                self.law_name,
                self.article_no,
                self.title or "",
                " ".join(self.keywords or []),
                " ".join(self.scenario_tags or []),
                self.content,
            ]
            if part
        )
