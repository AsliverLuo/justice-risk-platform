from __future__ import annotations

import re
from collections import OrderedDict

from sqlalchemy.orm import Session

from app.common.enums import CaseType
from app.core.config import settings
from app.infra.embedding import BaseEmbeddingClient, build_embedding_client
from app.infra.llm_client import BaseLLMClient, build_llm_client
from app.modules.analysis.parsers import (
    extract_case_no,
    extract_court_name,
    extract_judgment_date,
    fallback_parse_structured_case,
)
from app.modules.analysis.prompts import (
    CASE_STRUCTURE_SYSTEM_PROMPT,
    NLP_SYSTEM_PROMPT,
    build_case_structure_prompt,
    build_classification_prompt,
    build_entity_extraction_prompt,
    build_law_link_prompt,
)
from app.modules.analysis.repository import CaseCorpusRepository
from app.modules.analysis.rules import (
    build_case_risk_hints,
    build_case_summary,
    calculate_aggregate_risk,
    classify_case_type,
    extract_entities,
)
from app.modules.analysis.schemas import (
    CaseCorpusBatchUpsertRequest,
    CaseCorpusRead,
    CaseCorpusUpsertItem,
    CaseStructureRequest,
    CaseStructureResponse,
    CaseTextAnalyzeRequest,
    CaseTextAnalyzeResponse,
    CorpusSearchRequest,
    CorpusSearchResponse,
    EntityExtractRequest,
    EntityExtractResponse,
    EntityGroup,
    LawLinkRequest,
    LawLinkResponse,
    NLPClassifyRequest,
    NLPClassifyResponse,
    RelatedLawHit,
    RiskScoreRequest,
    RiskScoreResponse,
    StructuredCaseFields,
)
from app.modules.knowledge.schemas import KnowledgeSearchHit, KnowledgeSearchRequest
from app.modules.knowledge.service import LegalKnowledgeService


VALID_CASE_TYPES = {
    CaseType.labor_service_dispute.value,
    CaseType.labor_dispute.value,
    CaseType.other.value,
}

ARTICLE_REF_PATTERN = re.compile(r'第([一二三四五六七八九十百零〇0-9]+)条')
CHINESE_NUMERAL_MAP = {'零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
CHINESE_UNIT_MAP = {'十': 10, '百': 100, '千': 1000}


def normalize_article_ordinal(value: str) -> str:
    value = (value or '').strip()
    if value.isdigit():
        return value
    if not value:
        return value
    if not all(ch in CHINESE_NUMERAL_MAP or ch in CHINESE_UNIT_MAP for ch in value):
        return value

    section = 0
    number = 0
    for ch in value:
        if ch in CHINESE_NUMERAL_MAP:
            number = CHINESE_NUMERAL_MAP[ch]
        else:
            unit = CHINESE_UNIT_MAP[ch]
            if number == 0:
                number = 1
            section += number * unit
            number = 0
    total = section + number
    return str(total) if total > 0 else value


class AnalysisService:
    def __init__(
        self,
        db: Session,
        embedding_client: BaseEmbeddingClient | None = None,
        llm_client: BaseLLMClient | None = None,
    ) -> None:
        self.db = db
        self.repo = CaseCorpusRepository(db)
        self.embedding_client = embedding_client or build_embedding_client()
        self.llm_client = llm_client or build_llm_client()
        self.knowledge_service = LegalKnowledgeService(db=db, embedding_client=self.embedding_client)

    def batch_upsert_corpus(self, payload: CaseCorpusBatchUpsertRequest) -> list[CaseCorpusRead]:
        texts = []
        normalized_items: list[CaseCorpusUpsertItem] = []
        for item in payload.items:
            case_type = item.case_type or classify_case_type(item.full_text, item.title)
            entities = item.entities or extract_entities(item.full_text).model_dump()
            normalized = item.model_copy(update={'case_type': case_type, 'entities': entities})
            normalized_items.append(normalized)
            texts.append(' '.join([normalized.title, normalized.case_no or '', normalized.full_text]))

        embeddings = self.embedding_client.embed_texts(texts)
        output: list[CaseCorpusRead] = []
        for item, embedding in zip(normalized_items, embeddings):
            obj = self.repo.upsert(item=item, embedding=embedding)
            output.append(CaseCorpusRead.model_validate(obj))
        self.db.commit()
        return output

    def get_case(self, case_id: str) -> CaseCorpusRead | None:
        obj = self.repo.get(case_id)
        if not obj:
            obj = self.repo.get_by_source_ref(case_id)
        if not obj:
            obj = self.repo.get_by_case_no(case_id)
        if not obj:
            return None
        return CaseCorpusRead.model_validate(obj)

    def search_corpus(self, payload: CorpusSearchRequest) -> CorpusSearchResponse:
        query_embedding = self.embedding_client.embed_text(payload.query)
        hits = self.repo.hybrid_search(
            query=payload.query,
            query_embedding=query_embedding,
            top_k=payload.top_k or settings.case_corpus_top_k,
            case_type=payload.case_type,
        )
        return CorpusSearchResponse(hits=hits)

    def classify_text(self, payload: NLPClassifyRequest) -> NLPClassifyResponse:
        fallback_type = classify_case_type(payload.text, payload.title)
        if not self._use_llm(payload.prefer_llm):
            return NLPClassifyResponse(
                case_type=fallback_type,
                confidence=0.72,
                reason='rule_based_keyword_match',
                mode='rule',
            )

        raw = self.llm_client.complete_json(
            prompt=build_classification_prompt(payload.title, payload.text),
            system_prompt=NLP_SYSTEM_PROMPT,
        )
        case_type = raw.get('case_type')
        if case_type not in VALID_CASE_TYPES:
            case_type = fallback_type
        confidence = raw.get('confidence', 0.82)
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.82
        return NLPClassifyResponse(
            case_type=case_type,
            confidence=max(0.0, min(confidence, 1.0)),
            reason=str(raw.get('reason', 'llm_classification')),
            mode=self.llm_client.provider,
        )

    def extract_entities_capability(self, payload: EntityExtractRequest) -> EntityExtractResponse:
        fallback_entities = extract_entities('\n'.join([payload.title or '', payload.text]))
        if not self._use_llm(payload.prefer_llm):
            return EntityExtractResponse(entities=fallback_entities, mode='rule')

        raw = self.llm_client.complete_json(
            prompt=build_entity_extraction_prompt(payload.title, payload.text),
            system_prompt=NLP_SYSTEM_PROMPT,
        )
        try:
            entities = EntityGroup.model_validate(raw)
        except Exception:
            entities = fallback_entities
        return EntityExtractResponse(entities=entities, mode=self.llm_client.provider)

    def link_laws(self, payload: LawLinkRequest) -> LawLinkResponse:
        query_text = self._build_law_query_text(payload.title, payload.text)
        quick_case_type = classify_case_type(payload.text, payload.title)
        quick_entities = extract_entities(query_text)
        retrieval_queries = self._build_law_retrieval_queries(
            title=payload.title,
            text=payload.text,
            case_type=quick_case_type,
            entities=quick_entities,
        )
        candidate_pool_size = payload.candidate_pool_size or settings.analysis_law_candidate_pool_size
        candidate_hits = self._retrieve_law_candidates(
            queries=retrieval_queries,
            case_type=quick_case_type,
            entities=quick_entities,
            top_k=candidate_pool_size,
            law_name=payload.law_name,
            scenario_tag=payload.scenario_tag,
        )
        if not candidate_hits:
            return LawLinkResponse(
                matched_laws=[],
                query_text=query_text,
                mode='retrieval_only',
                candidate_count=0,
                retrieval_queries=retrieval_queries,
            )
        if not self._use_llm(payload.prefer_llm):
            return LawLinkResponse(
                matched_laws=candidate_hits[: payload.top_k],
                query_text=query_text,
                mode='retrieval_only',
                candidate_count=len(candidate_hits),
                retrieval_queries=retrieval_queries,
            )

        knowledge_context = self._render_knowledge_candidates(candidate_hits)
        case_profile = build_case_summary(
            case_type=quick_case_type,
            entities=quick_entities,
            title=payload.title,
        )
        raw = self.llm_client.complete_json(
            prompt=build_law_link_prompt(payload.title, payload.text, knowledge_context, payload.top_k, case_profile=case_profile),
            system_prompt=NLP_SYSTEM_PROMPT,
        )
        recommended = raw.get('recommended_refs', [])
        selected = self._select_recommended_laws(candidate_hits, recommended)
        if not selected:
            selected = candidate_hits[: payload.top_k]
            mode = 'retrieval_only'
        else:
            mode = self.llm_client.provider
        return LawLinkResponse(
            matched_laws=selected[: payload.top_k],
            query_text=query_text,
            mode=mode,
            candidate_count=len(candidate_hits),
            retrieval_queries=retrieval_queries,
        )

    def structure_case(self, payload: CaseStructureRequest) -> CaseStructureResponse:
        structured_case = self._parse_structured_case(payload.title, payload.text, payload.prefer_llm)
        classify_resp = self.classify_text(
            NLPClassifyRequest(title=payload.title, text=payload.text, prefer_llm=payload.prefer_llm)
        )
        entity_resp = self.extract_entities_capability(
            EntityExtractRequest(title=payload.title, text=payload.text, prefer_llm=payload.prefer_llm)
        )
        law_resp = self.link_laws(
            LawLinkRequest(title=payload.title, text=payload.text, top_k=payload.top_k_laws, prefer_llm=payload.prefer_llm)
        )

        persisted_case_id: str | None = None
        if payload.persist_to_corpus:
            case_no = payload.case_no or extract_case_no(payload.text)
            court_name = payload.court_name or extract_court_name(payload.text)
            judgment_date = payload.judgment_date or extract_judgment_date(payload.text)
            plaintiff_summary = '；'.join(item.summary or item.name for item in structured_case.plaintiffs) or None
            defendant_summary = '；'.join(item.summary or item.name for item in structured_case.defendants) or None
            claim_summary = '；'.join(structured_case.claims) or None
            focus_summary = '；'.join(structured_case.disputed_issues) or None
            fact_summary = structured_case.facts_found_by_court
            judgment_summary = structured_case.judgment_result
            cited_laws = self._merge_law_refs(structured_case.applied_laws, law_resp.matched_laws)
            item = CaseCorpusUpsertItem(
                source_type=payload.source_type,
                source_ref=payload.source_ref,
                title=payload.title,
                case_no=case_no,
                full_text=payload.text,
                case_type=classify_resp.case_type,
                plaintiff_summary=plaintiff_summary,
                defendant_summary=defendant_summary,
                claim_summary=claim_summary,
                focus_summary=focus_summary,
                fact_summary=fact_summary,
                judgment_summary=judgment_summary,
                court_name=court_name,
                judgment_date=judgment_date,
                entities=entity_resp.entities.model_dump(),
                cited_laws=cited_laws,
                extra_meta={
                    **payload.extra_meta,
                    'structured_case': structured_case.model_dump(),
                    'llm_mode': self._pick_mode(payload.prefer_llm, fallback='rule'),
                },
            )
            embedding = self.embedding_client.embed_text(f"{item.title}\n{item.full_text}")
            obj = self.repo.upsert(item=item, embedding=embedding)
            self.db.commit()
            persisted_case_id = obj.id

        mode = self.llm_client.provider if self._use_llm(payload.prefer_llm) else 'rule'
        return CaseStructureResponse(
            title=payload.title,
            case_type=classify_resp.case_type,
            structured_case=structured_case,
            entities=entity_resp.entities,
            matched_laws=law_resp.matched_laws,
            mode=mode,
            persisted_case_id=persisted_case_id,
        )

    def analyze_text(self, payload: CaseTextAnalyzeRequest) -> CaseTextAnalyzeResponse:
        classify_resp = self.classify_text(
            NLPClassifyRequest(title=payload.title, text=payload.text, prefer_llm=payload.prefer_llm)
        )
        entity_resp = self.extract_entities_capability(
            EntityExtractRequest(title=payload.title, text=payload.text, prefer_llm=payload.prefer_llm)
        )
        law_resp = self.link_laws(
            LawLinkRequest(title=payload.title, text=payload.text, top_k=payload.top_k_laws, prefer_llm=payload.prefer_llm)
        )
        summary = build_case_summary(case_type=classify_resp.case_type, entities=entity_resp.entities, title=payload.title)
        risk_hints = build_case_risk_hints(
            amount_total_estimate=entity_resp.entities.amount_total_estimate,
            people_count=payload.people_count,
            repeat_defendant_count=payload.repeat_defendant_count,
        )

        persisted_case_id: str | None = None
        if payload.persist_to_corpus:
            item = CaseCorpusUpsertItem(
                source_type='parsed_text',
                source_ref=payload.source_ref,
                title=payload.title or '未命名案件文本',
                full_text=payload.text,
                case_type=classify_resp.case_type,
                fact_summary=summary,
                entities=entity_resp.entities.model_dump(),
                cited_laws=self._merge_law_refs([], law_resp.matched_laws),
                extra_meta={'risk_hints': [item.model_dump() for item in risk_hints]},
            )
            embedding = self.embedding_client.embed_text(f"{item.title}\n{item.full_text}")
            obj = self.repo.upsert(item=item, embedding=embedding)
            self.db.commit()
            persisted_case_id = obj.id

        return CaseTextAnalyzeResponse(
            case_type=classify_resp.case_type,
            summary=summary,
            entities=entity_resp.entities,
            matched_laws=law_resp.matched_laws,
            risk_hints=risk_hints,
            persisted_case_id=persisted_case_id,
            classify_mode=classify_resp.mode,
            entity_mode=entity_resp.mode,
            law_link_mode=law_resp.mode,
        )

    def score_risk(self, payload: RiskScoreRequest) -> RiskScoreResponse:
        return calculate_aggregate_risk(
            case_count=payload.case_count,
            total_amount=payload.total_amount,
            people_count=payload.people_count,
            growth_rate=payload.growth_rate,
            repeat_defendant_rate=payload.repeat_defendant_rate,
        )

    def _parse_structured_case(self, title: str, text: str, prefer_llm: bool) -> StructuredCaseFields:
        fallback = fallback_parse_structured_case(title=title, text=text)
        if not self._use_llm(prefer_llm):
            return fallback
        raw = self.llm_client.complete_json(
            prompt=build_case_structure_prompt(title, text),
            system_prompt=CASE_STRUCTURE_SYSTEM_PROMPT,
        )
        try:
            parsed = StructuredCaseFields.model_validate(raw)
        except Exception:
            return fallback

        if not parsed.plaintiffs:
            parsed = parsed.model_copy(update={'plaintiffs': fallback.plaintiffs})
        if not parsed.defendants:
            parsed = parsed.model_copy(update={'defendants': fallback.defendants})
        if not parsed.cause_of_action:
            parsed = parsed.model_copy(update={'cause_of_action': fallback.cause_of_action})
        if not parsed.applied_laws:
            parsed = parsed.model_copy(update={'applied_laws': fallback.applied_laws})
        return parsed

    @staticmethod
    def _merge_law_refs(raw_refs: list[str], matched_laws: list[RelatedLawHit]) -> list[str]:
        merged = list(raw_refs)
        for hit in matched_laws:
            merged.append(f'{hit.law_name}{hit.article_no}')
        dedup: list[str] = []
        for item in merged:
            if item and item not in dedup:
                dedup.append(item)
        return dedup

    def _use_llm(self, prefer_llm: bool) -> bool:
        return bool(prefer_llm and not self.llm_client.is_echo)

    def _pick_mode(self, prefer_llm: bool, fallback: str = 'rule') -> str:
        return self.llm_client.provider if self._use_llm(prefer_llm) else fallback

    @staticmethod
    def _build_law_query_text(title: str | None, text: str) -> str:
        return ((title or '').strip() + '\n' + text[: settings.analysis_law_query_text_limit].strip()).strip()

    @staticmethod
    def _render_knowledge_candidates(hits: list[RelatedLawHit]) -> str:
        blocks: list[str] = []
        for hit in hits:
            blocks.append(
                f'[{hit.law_name}|{hit.article_no}] 标题：{hit.title or ""} 适用场景：{", ".join(hit.scenario_tags)} 内容：{hit.content}'
            )
        return '\n'.join(blocks)

    def _build_law_retrieval_queries(
        self,
        title: str | None,
        text: str,
        case_type: str,
        entities: EntityGroup,
    ) -> list[str]:
        queries: list[str] = []
        base_query = self._build_law_query_text(title, text)
        queries.append(base_query)
        queries.append(build_case_summary(case_type=case_type, entities=entities, title=title))

        compact_tokens: list[str] = []
        compact_tokens.extend(entities.law_refs[:3])
        compact_tokens.extend(entities.companies[:2])
        compact_tokens.extend(entities.projects[:2])
        compact_tokens.extend(entities.amounts[:2])
        compact_tokens.extend(entities.addresses[:2])
        if case_type == CaseType.labor_service_dispute.value:
            compact_tokens.extend(['农民工工资', '劳务报酬', '拖欠工资', '清偿责任'])
        elif case_type == CaseType.labor_dispute.value:
            compact_tokens.extend(['劳动关系', '劳动争议'])
        else:
            compact_tokens.extend(['支持起诉', '程序依据'])
        queries.append(' '.join(token for token in compact_tokens if token))

        ordered = OrderedDict()
        for query in queries:
            query = (query or '').strip()
            if query:
                ordered[query] = None
        return list(ordered.keys())

    def _retrieve_law_candidates(
        self,
        queries: list[str],
        case_type: str,
        entities: EntityGroup,
        top_k: int,
        law_name: str | None = None,
        scenario_tag: str | None = None,
    ) -> list[RelatedLawHit]:
        preferred_laws = [law_name] if law_name else self._infer_preferred_law_names(case_type=case_type, entities=entities)
        scenario_tags = [scenario_tag] if scenario_tag else self._infer_scenario_tags(case_type=case_type, entities=entities)
        explicit_ref_keys = {self._law_ref_key(*self._split_law_ref(ref)) for ref in entities.law_refs if ref}
        if None not in scenario_tags:
            scenario_tags.append(None)

        merged: dict[str, RelatedLawHit] = {}
        for query in queries:
            law_buckets = preferred_laws or [None]
            if None not in law_buckets:
                law_buckets.append(None)
            for target_law in law_buckets:
                for target_tag in scenario_tags:
                    resp = self.knowledge_service.search(
                        KnowledgeSearchRequest(
                            query=query,
                            top_k=min(top_k, 20),
                            law_name=target_law,
                            scenario_tag=target_tag,
                        )
                    )
                    for hit in resp.hits:
                        boosted_score = hit.score
                        if target_law and hit.law_name == target_law:
                            boosted_score += 0.03
                        if target_tag and target_tag in (hit.scenario_tags or []):
                            boosted_score += 0.02
                        if self._law_ref_key(hit.law_name, hit.article_no) in explicit_ref_keys:
                            boosted_score += 0.15
                        candidate = RelatedLawHit(
                            id=hit.id,
                            article_no=hit.article_no,
                            law_name=hit.law_name,
                            title=hit.title,
                            content=hit.content,
                            score=round(min(boosted_score, 1.0), 6),
                            reason=hit.reason,
                            scenario_tags=hit.scenario_tags,
                            matched_terms=hit.matched_terms,
                        )
                        existing = merged.get(candidate.id)
                        if not existing or candidate.score > existing.score:
                            merged[candidate.id] = candidate
                        else:
                            existing.matched_terms = list(set(existing.matched_terms + candidate.matched_terms))

        ranked = list(merged.values())
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    @staticmethod
    def _infer_preferred_law_names(case_type: str, entities: EntityGroup) -> list[str | None]:
        explicit_names: list[str] = []
        for ref in entities.law_refs:
            if '《' in ref and '》' in ref:
                explicit_names.append(ref.split('》')[0].replace('《', '').strip())

        defaults: list[str] = []
        if case_type == CaseType.labor_service_dispute.value:
            defaults = ['保障农民工工资支付条例', '中华人民共和国民法典', '中华人民共和国民事诉讼法']
        elif case_type == CaseType.labor_dispute.value:
            defaults = ['中华人民共和国民法典', '中华人民共和国民事诉讼法']
        else:
            defaults = ['关于办理民事支持起诉案件若干问题的指导意见', '中华人民共和国民事诉讼法', '中华人民共和国民法典']

        ordered = OrderedDict()
        for item in explicit_names + defaults:
            if item:
                ordered[item] = None
        return list(ordered.keys())

    @staticmethod
    def _infer_scenario_tags(case_type: str, entities: EntityGroup) -> list[str | None]:
        text_blob = ' '.join(entities.law_refs + entities.projects + entities.amounts + entities.addresses + entities.companies + entities.persons)
        tags: list[str | None] = []
        if case_type == CaseType.labor_service_dispute.value:
            tags.extend(['工资支付', '清偿责任', '支持起诉'])
        elif case_type == CaseType.labor_dispute.value:
            tags.extend(['程序依据'])
        else:
            tags.extend(['支持起诉', '程序依据'])
        if '家庭暴力' in text_blob or '离婚' in text_blob:
            tags.append('支持起诉')
        ordered = OrderedDict()
        for item in tags:
            if item:
                ordered[item] = None
        return list(ordered.keys())

    def _select_recommended_laws(self, candidate_hits: list[RelatedLawHit], recommended: list[dict]) -> list[RelatedLawHit]:
        candidate_map = {
            self._law_ref_key(hit.law_name, hit.article_no): hit
            for hit in candidate_hits
        }
        selected: list[RelatedLawHit] = []
        for item in recommended:
            law_name = str(item.get('law_name', '')).strip()
            article_no = str(item.get('article_no', '')).strip()
            reason = str(item.get('reason', '')).strip()
            matched = candidate_map.get(self._law_ref_key(law_name, article_no))
            if matched:
                selected.append(matched.model_copy(update={'reason': reason or matched.reason}))
        # 去重
        dedup: list[RelatedLawHit] = []
        seen: set[str] = set()
        for hit in selected:
            if hit.id not in seen:
                dedup.append(hit)
                seen.add(hit.id)
        return dedup

    @staticmethod
    def _split_law_ref(ref: str) -> tuple[str, str]:
        ref = (ref or '').strip()
        if '》' in ref:
            law_name = ref.split('》')[0].replace('《', '').strip()
            article = ref.split('》', 1)[1].strip()
            return law_name, article
        if '|' in ref:
            law_name, article = ref.split('|', 1)
            return law_name.strip(), article.strip()
        return '', ref

    @staticmethod
    def _law_ref_key(law_name: str, article_no: str) -> str:
        def _norm_law(value: str) -> str:
            return re.sub(r'\s+', '', (value or '').replace('《', '').replace('》', ''))

        def _norm_article(value: str) -> str:
            value = (value or '').replace(' ', '')
            match = ARTICLE_REF_PATTERN.search(value)
            if match:
                return normalize_article_ordinal(match.group(1))
            return normalize_article_ordinal(value)

        return f'{_norm_law(law_name)}|{_norm_article(article_no)}'
