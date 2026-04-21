from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.infra.vector_store import HAS_PGVECTOR, clamp_score, cosine_similarity
from app.modules.knowledge.models import LegalKnowledge
from app.modules.knowledge.schemas import KnowledgeSearchHit, KnowledgeUpsertItem


class LegalKnowledgeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, knowledge_id: str) -> LegalKnowledge | None:
        return self.db.get(LegalKnowledge, knowledge_id)

    def get_by_article_and_law(self, article_no: str, law_name: str) -> LegalKnowledge | None:
        stmt = select(LegalKnowledge).where(
            LegalKnowledge.article_no == article_no,
            LegalKnowledge.law_name == law_name,
        )
        return self.db.scalar(stmt)

    def upsert(self, item: KnowledgeUpsertItem, embedding: list[float] | None) -> LegalKnowledge:
        existing = None
        if item.id:
            existing = self.get(item.id)
        if not existing:
            existing = self.get_by_article_and_law(item.article_no, item.law_name)

        if existing:
            existing.title = item.title
            existing.content = item.content
            existing.keywords = item.keywords
            existing.scenario_tags = item.scenario_tags
            existing.source_type = item.source_type
            existing.effective_date = item.effective_date
            existing.status = item.status
            existing.extra_meta = item.extra_meta
            existing.embedding = embedding
            obj = existing
        else:
            obj = LegalKnowledge(
                article_no=item.article_no,
                law_name=item.law_name,
                title=item.title,
                content=item.content,
                keywords=item.keywords,
                scenario_tags=item.scenario_tags,
                source_type=item.source_type,
                effective_date=item.effective_date,
                status=item.status,
                extra_meta=item.extra_meta,
                embedding=embedding,
            )
            self.db.add(obj)

        self.db.flush()
        return obj

    def _base_stmt(self, law_name: str | None = None, scenario_tag: str | None = None) -> Select[tuple[LegalKnowledge]]:
        stmt = select(LegalKnowledge).where(LegalKnowledge.status == "active")
        if settings.knowledge_exclude_demo_articles:
            stmt = stmt.where(~LegalKnowledge.article_no.like("示例-%"))
        if law_name:
            stmt = stmt.where(LegalKnowledge.law_name == law_name)
        if scenario_tag:
            # JSON contains 在不同数据库行为不同，这里使用朴素兼容逻辑：
            # 先缩小 law_name / status，实际标签过滤放到 Python 侧二次判断。
            pass
        return stmt

    def _normalize_embedding(self, value: Any) -> list[float]:
        """
        将数据库里取出的 embedding 统一转成 list[float]，兼容：
        - None
        - Python list / tuple
        - numpy.ndarray
        - pgvector / 其他可迭代对象
        """
        if value is None:
            return []

        # numpy.ndarray / pandas / 某些向量对象
        if hasattr(value, "tolist"):
            try:
                value = value.tolist()
            except Exception:
                pass

        if isinstance(value, list):
            try:
                return [float(x) for x in value]
            except Exception:
                return []

        if isinstance(value, tuple):
            try:
                return [float(x) for x in value]
            except Exception:
                return []

        # 某些数据库返回的特殊数组对象，可迭代但不是 list/tuple
        try:
            return [float(x) for x in value]
        except Exception:
            return []

    def keyword_search(
        self,
        query: str,
        top_k: int,
        law_name: str | None = None,
        scenario_tag: str | None = None,
    ) -> list[KnowledgeSearchHit]:
        stmt = self._base_stmt(law_name=law_name, scenario_tag=scenario_tag)
        tokens = [token for token in query.replace("，", " ").replace("。", " ").split() if token.strip()]
        like_clauses = []
        for token in tokens[:12]:
            pattern = f"%{token}%"
            like_clauses.extend(
                [
                    LegalKnowledge.law_name.ilike(pattern),
                    LegalKnowledge.article_no.ilike(pattern),
                    LegalKnowledge.title.ilike(pattern),
                    LegalKnowledge.content.ilike(pattern),
                ]
            )
        if like_clauses:
            stmt = stmt.where(or_(*like_clauses))

        records = list(self.db.scalars(stmt.limit(max(top_k * 5, 20))).all())

        hits: list[KnowledgeSearchHit] = []
        for record in records:
            if scenario_tag and scenario_tag not in (record.scenario_tags or []):
                continue

            matched_terms: list[str] = []
            haystack = " ".join(
                [record.law_name, record.article_no, record.title or "", record.content]
            ).lower()
            for token in tokens:
                if token.lower() in haystack:
                    matched_terms.append(token)

            if not matched_terms and tokens:
                continue

            raw_score = len(set(matched_terms)) / max(1, len(set(tokens)))
            score = clamp_score(raw_score)
            hits.append(
                KnowledgeSearchHit(
                    id=record.id,
                    article_no=record.article_no,
                    law_name=record.law_name,
                    title=record.title,
                    content=record.content,
                    keywords=record.keywords or [],
                    scenario_tags=record.scenario_tags or [],
                    score=score,
                    reason="keyword_match",
                    matched_terms=matched_terms,
                )
            )

        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]

    def semantic_search(
        self,
        query_embedding: list[float],
        top_k: int,
        law_name: str | None = None,
        scenario_tag: str | None = None,
    ) -> list[KnowledgeSearchHit]:
        stmt = self._base_stmt(law_name=law_name, scenario_tag=scenario_tag)

        # PostgreSQL + pgvector 时优先用数据库内排序
        if HAS_PGVECTOR and self.db.bind and self.db.bind.dialect.name == "postgresql":
            distance = LegalKnowledge.embedding.cosine_distance(query_embedding)  # type: ignore[attr-defined]
            stmt = stmt.order_by(distance).limit(top_k)
            records = list(self.db.scalars(stmt).all())
            hits: list[KnowledgeSearchHit] = []
            for record in records:
                if scenario_tag and scenario_tag not in (record.scenario_tags or []):
                    continue

                record_embedding = self._normalize_embedding(record.embedding)
                if not record_embedding:
                    continue

                similarity = cosine_similarity(query_embedding, record_embedding)
                if similarity <= 0:
                    continue

                hits.append(
                    KnowledgeSearchHit(
                        id=record.id,
                        article_no=record.article_no,
                        law_name=record.law_name,
                        title=record.title,
                        content=record.content,
                        keywords=record.keywords or [],
                        scenario_tags=record.scenario_tags or [],
                        score=clamp_score(similarity),
                        reason="semantic_match",
                        matched_terms=[],
                    )
                )
            hits.sort(key=lambda item: item.score, reverse=True)
            return hits[:top_k]

        # 其他数据库 / 本地联调环境，走 Python 余弦重排
        records = list(self.db.scalars(stmt.limit(500)).all())
        hits: list[KnowledgeSearchHit] = []
        for record in records:
            if scenario_tag and scenario_tag not in (record.scenario_tags or []):
                continue

            record_embedding = self._normalize_embedding(record.embedding)
            if not record_embedding:
                continue

            similarity = cosine_similarity(query_embedding, record_embedding)
            if similarity <= 0:
                continue

            hits.append(
                KnowledgeSearchHit(
                    id=record.id,
                    article_no=record.article_no,
                    law_name=record.law_name,
                    title=record.title,
                    content=record.content,
                    keywords=record.keywords or [],
                    scenario_tags=record.scenario_tags or [],
                    score=clamp_score(similarity),
                    reason="semantic_match",
                    matched_terms=[],
                )
            )
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]

    def hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int,
        law_name: str | None = None,
        scenario_tag: str | None = None,
    ) -> list[KnowledgeSearchHit]:
        semantic_hits = self.semantic_search(
            query_embedding=query_embedding,
            top_k=max(top_k * 2, 10),
            law_name=law_name,
            scenario_tag=scenario_tag,
        )
        keyword_hits = self.keyword_search(
            query=query,
            top_k=max(top_k * 2, 10),
            law_name=law_name,
            scenario_tag=scenario_tag,
        )

        merged: dict[str, KnowledgeSearchHit] = {}
        score_pool: dict[str, dict[str, Any]] = defaultdict(lambda: {"semantic": 0.0, "keyword": 0.0})

        for hit in semantic_hits:
            merged[hit.id] = hit
            score_pool[hit.id]["semantic"] = hit.score

        for hit in keyword_hits:
            merged[hit.id] = hit if hit.id not in merged else merged[hit.id]
            score_pool[hit.id]["keyword"] = hit.score
            merged[hit.id].matched_terms = list(set(merged[hit.id].matched_terms + hit.matched_terms))

        results: list[KnowledgeSearchHit] = []
        for knowledge_id, hit in merged.items():
            semantic_score = score_pool[knowledge_id]["semantic"]
            keyword_score = score_pool[knowledge_id]["keyword"]
            final_score = (
                semantic_score * settings.knowledge_semantic_weight
                + keyword_score * settings.knowledge_keyword_weight
            )
            hit.score = round(clamp_score(final_score), 6)
            if semantic_score and keyword_score:
                hit.reason = "hybrid_match"
            elif semantic_score:
                hit.reason = "semantic_match"
            else:
                hit.reason = "keyword_match"
            results.append(hit)

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]