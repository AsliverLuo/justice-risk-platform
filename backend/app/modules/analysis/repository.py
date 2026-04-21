from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.infra.vector_store import HAS_PGVECTOR, clamp_score, cosine_similarity
from app.modules.analysis.models import CaseCorpus
from app.modules.analysis.schemas import CaseCorpusUpsertItem, CorpusSearchHit


class CaseCorpusRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, case_id: str) -> CaseCorpus | None:
        return self.db.get(CaseCorpus, case_id)

    def get_by_source_ref(self, source_ref: str) -> CaseCorpus | None:
        stmt = select(CaseCorpus).where(CaseCorpus.source_ref == source_ref)
        return self.db.scalar(stmt)

    def get_by_case_no(self, case_no: str) -> CaseCorpus | None:
        stmt = select(CaseCorpus).where(CaseCorpus.case_no == case_no)
        return self.db.scalar(stmt)

    def upsert(self, item: CaseCorpusUpsertItem, embedding: list[float] | None) -> CaseCorpus:
        existing = None
        if item.id:
            existing = self.get(item.id)
        if not existing and item.source_ref:
            existing = self.get_by_source_ref(item.source_ref)

        payload = item.model_dump(exclude={'id'})
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            existing.embedding = embedding
            obj = existing
        else:
            obj = CaseCorpus(**payload, embedding=embedding)
            self.db.add(obj)
        self.db.flush()
        return obj

    def keyword_search(self, query: str, top_k: int, case_type: str | None = None) -> list[CorpusSearchHit]:
        stmt = select(CaseCorpus)
        if case_type:
            stmt = stmt.where(CaseCorpus.case_type == case_type)

        tokens = [token for token in query.replace('，', ' ').replace('。', ' ').split() if token.strip()]
        like_clauses = []
        for token in tokens[:12]:
            pattern = f'%{token}%'
            like_clauses.extend([
                CaseCorpus.title.ilike(pattern),
                CaseCorpus.case_no.ilike(pattern),
                CaseCorpus.full_text.ilike(pattern),
                CaseCorpus.fact_summary.ilike(pattern),
                CaseCorpus.judgment_summary.ilike(pattern),
            ])
        if like_clauses:
            stmt = stmt.where(or_(*like_clauses))

        records = list(self.db.scalars(stmt.limit(max(top_k * 5, 20))).all())
        hits: list[CorpusSearchHit] = []
        for record in records:
            matched_terms: list[str] = []
            haystack = record.to_search_text().lower()
            for token in tokens:
                if token.lower() in haystack:
                    matched_terms.append(token)
            if tokens and not matched_terms:
                continue
            score = clamp_score(len(set(matched_terms)) / max(1, len(set(tokens))))
            hits.append(
                CorpusSearchHit(
                    id=record.id,
                    title=record.title,
                    case_no=record.case_no,
                    case_type=record.case_type,
                    judgment_summary=record.judgment_summary,
                    cited_laws=record.cited_laws or [],
                    score=score,
                    reason='keyword_match',
                    matched_terms=matched_terms,
                )
            )
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]

    def semantic_search(self, query_embedding: list[float], top_k: int, case_type: str | None = None) -> list[CorpusSearchHit]:
        stmt = select(CaseCorpus)
        if case_type:
            stmt = stmt.where(CaseCorpus.case_type == case_type)

        if HAS_PGVECTOR and self.db.bind and self.db.bind.dialect.name == 'postgresql':
            distance = CaseCorpus.embedding.cosine_distance(query_embedding)  # type: ignore[attr-defined]
            stmt = stmt.order_by(distance).limit(top_k)
            records = list(self.db.scalars(stmt).all())
            hits: list[CorpusSearchHit] = []
            for record in records:
                similarity = cosine_similarity(query_embedding, record.embedding or [])
                hits.append(
                    CorpusSearchHit(
                        id=record.id,
                        title=record.title,
                        case_no=record.case_no,
                        case_type=record.case_type,
                        judgment_summary=record.judgment_summary,
                        cited_laws=record.cited_laws or [],
                        score=clamp_score(similarity),
                        reason='semantic_match',
                        matched_terms=[],
                    )
                )
            hits.sort(key=lambda item: item.score, reverse=True)
            return hits[:top_k]

        records = list(self.db.scalars(stmt.limit(500)).all())
        hits: list[CorpusSearchHit] = []
        for record in records:
            similarity = cosine_similarity(query_embedding, record.embedding or [])
            if similarity <= 0:
                continue
            hits.append(
                CorpusSearchHit(
                    id=record.id,
                    title=record.title,
                    case_no=record.case_no,
                    case_type=record.case_type,
                    judgment_summary=record.judgment_summary,
                    cited_laws=record.cited_laws or [],
                    score=clamp_score(similarity),
                    reason='semantic_match',
                    matched_terms=[],
                )
            )
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]

    def hybrid_search(self, query: str, query_embedding: list[float], top_k: int, case_type: str | None = None) -> list[CorpusSearchHit]:
        semantic_hits = self.semantic_search(query_embedding=query_embedding, top_k=max(top_k * 2, 10), case_type=case_type)
        keyword_hits = self.keyword_search(query=query, top_k=max(top_k * 2, 10), case_type=case_type)

        merged: dict[str, CorpusSearchHit] = {}
        score_pool: dict[str, dict[str, Any]] = defaultdict(lambda: {'semantic': 0.0, 'keyword': 0.0})

        for hit in semantic_hits:
            merged[hit.id] = hit
            score_pool[hit.id]['semantic'] = hit.score
        for hit in keyword_hits:
            merged[hit.id] = hit if hit.id not in merged else merged[hit.id]
            score_pool[hit.id]['keyword'] = hit.score
            merged[hit.id].matched_terms = list(set(merged[hit.id].matched_terms + hit.matched_terms))

        results: list[CorpusSearchHit] = []
        for case_id, hit in merged.items():
            semantic_score = score_pool[case_id]['semantic']
            keyword_score = score_pool[case_id]['keyword']
            final_score = semantic_score * settings.analysis_semantic_weight + keyword_score * settings.analysis_keyword_weight
            hit.score = round(clamp_score(final_score), 6)
            if semantic_score and keyword_score:
                hit.reason = 'hybrid_match'
            elif semantic_score:
                hit.reason = 'semantic_match'
            else:
                hit.reason = 'keyword_match'
            results.append(hit)

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]
