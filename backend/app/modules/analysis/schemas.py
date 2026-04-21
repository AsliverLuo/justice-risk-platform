from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.common.enums import CaseType, RiskLevel


class CaseCorpusBase(BaseModel):
    source_type: str = 'judgment'
    source_ref: str | None = None
    title: str
    case_no: str | None = None
    full_text: str
    case_type: str | None = None
    plaintiff_summary: str | None = None
    defendant_summary: str | None = None
    claim_summary: str | None = None
    focus_summary: str | None = None
    fact_summary: str | None = None
    judgment_summary: str | None = None
    court_name: str | None = None
    province: str | None = None
    city: str | None = None
    occurred_at: date | None = None
    judgment_date: date | None = None
    entities: dict = Field(default_factory=dict)
    cited_laws: list[str] = Field(default_factory=list)
    extra_meta: dict = Field(default_factory=dict)


class CaseCorpusUpsertItem(CaseCorpusBase):
    id: str | None = None


class CaseCorpusBatchUpsertRequest(BaseModel):
    items: list[CaseCorpusUpsertItem]


class CaseCorpusRead(CaseCorpusBase):
    id: str

    model_config = {'from_attributes': True}


class CorpusSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    case_type: str | None = None


class CorpusSearchHit(BaseModel):
    id: str
    title: str
    case_no: str | None = None
    case_type: str
    judgment_summary: str | None = None
    cited_laws: list[str] = Field(default_factory=list)
    score: float = 0.0
    reason: str = ''
    matched_terms: list[str] = Field(default_factory=list)


class CorpusSearchResponse(BaseModel):
    hits: list[CorpusSearchHit]


class EntityGroup(BaseModel):
    persons: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    amount_total_estimate: float = 0.0
    dates: list[str] = Field(default_factory=list)
    addresses: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    id_cards: list[str] = Field(default_factory=list)
    law_refs: list[str] = Field(default_factory=list)


class RelatedLawHit(BaseModel):
    id: str
    article_no: str
    law_name: str
    title: str | None = None
    content: str
    score: float = 0.0
    reason: str = ''
    scenario_tags: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)


class CaseRiskHint(BaseModel):
    label: str
    triggered: bool
    detail: str


class PartyInfo(BaseModel):
    name: str
    role: str
    party_type: str = 'individual'
    original_label: str | None = None
    summary: str | None = None


class StructuredCaseFields(BaseModel):
    cause_of_action: str | None = None
    plaintiffs: list[PartyInfo] = Field(default_factory=list)
    defendants: list[PartyInfo] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    disputed_issues: list[str] = Field(default_factory=list)
    facts_found_by_court: str | None = None
    judgment_result: str | None = None
    applied_laws: list[str] = Field(default_factory=list)
    source_sections: dict[str, str] = Field(default_factory=dict)


class NLPClassifyRequest(BaseModel):
    title: str | None = Field(default=None, description='案件标题，可选')
    text: str = Field(..., description='案件文本')
    prefer_llm: bool = Field(default=True, description='是否优先调用大模型')


class NLPClassifyResponse(BaseModel):
    case_type: str = CaseType.other.value
    confidence: float = 0.0
    reason: str = ''
    mode: str = 'rule'


class EntityExtractRequest(BaseModel):
    title: str | None = Field(default=None, description='案件标题，可选')
    text: str = Field(..., description='案件文本')
    prefer_llm: bool = Field(default=True, description='是否优先调用大模型')


class EntityExtractResponse(BaseModel):
    entities: EntityGroup
    mode: str = 'rule'


class LawLinkRequest(BaseModel):
    title: str | None = Field(default=None, description='案件标题，可选')
    text: str = Field(..., description='案件文本')
    top_k: int = Field(default=5, ge=1, le=10)
    prefer_llm: bool = Field(default=True, description='是否优先调用大模型')
    law_name: str | None = Field(default=None, description='可选：仅在某部法律内检索')
    scenario_tag: str | None = Field(default=None, description='可选：仅在某个场景标签下检索')
    candidate_pool_size: int | None = Field(default=None, ge=3, le=30, description='候选法条池大小，默认走配置')


class LawLinkResponse(BaseModel):
    matched_laws: list[RelatedLawHit] = Field(default_factory=list)
    query_text: str = ''
    mode: str = 'retrieval_only'
    candidate_count: int = 0
    retrieval_queries: list[str] = Field(default_factory=list)


class CaseStructureRequest(BaseModel):
    title: str
    text: str = Field(..., description='判例全文或指导性案例全文')
    source_type: str = Field(default='judgment')
    source_ref: str | None = None
    case_no: str | None = None
    court_name: str | None = None
    judgment_date: date | None = None
    top_k_laws: int = Field(default=5, ge=1, le=10)
    prefer_llm: bool = Field(default=True, description='是否优先调用大模型')
    persist_to_corpus: bool = Field(default=False, description='是否保存到案例语料表')
    extra_meta: dict = Field(default_factory=dict)


class CaseStructureResponse(BaseModel):
    title: str
    case_type: str = CaseType.other.value
    structured_case: StructuredCaseFields
    entities: EntityGroup
    matched_laws: list[RelatedLawHit] = Field(default_factory=list)
    mode: str = 'rule'
    persisted_case_id: str | None = None


class CaseTextAnalyzeRequest(BaseModel):
    title: str | None = Field(default=None, description='案件标题，可选')
    text: str = Field(..., description='案件描述、判例全文或投诉文本')
    people_count: int = Field(default=1, ge=1, description='涉及人数，用于群体性风险提示')
    repeat_defendant_count: int = Field(default=1, ge=1, description='同一主体近期重复出现次数')
    top_k_laws: int = Field(default=5, ge=1, le=10)
    persist_to_corpus: bool = Field(default=False, description='是否把解析结果落库到案例语料表')
    source_ref: str | None = None
    prefer_llm: bool = Field(default=True, description='是否优先调用大模型')


class CaseTextAnalyzeResponse(BaseModel):
    case_type: str = CaseType.other.value
    summary: str
    entities: EntityGroup
    matched_laws: list[RelatedLawHit] = Field(default_factory=list)
    risk_hints: list[CaseRiskHint] = Field(default_factory=list)
    persisted_case_id: str | None = None
    classify_mode: str = 'rule'
    entity_mode: str = 'rule'
    law_link_mode: str = 'retrieval_only'


class RiskScoreRequest(BaseModel):
    case_count: int = Field(..., ge=0)
    total_amount: float = Field(..., ge=0)
    people_count: int = Field(..., ge=0)
    growth_rate: float = Field(default=0.0, ge=0.0, description='近期增长率，0.25 表示增长 25%')
    repeat_defendant_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class RiskScoreDetail(BaseModel):
    metric: str
    raw_value: float
    normalized_value: float
    weight: float
    contribution: float


class RiskScoreResponse(BaseModel):
    score: float
    level: str = RiskLevel.blue.value
    details: list[RiskScoreDetail] = Field(default_factory=list)
    triggered_rules: list[str] = Field(default_factory=list)
