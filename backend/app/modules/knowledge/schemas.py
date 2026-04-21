from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class KnowledgeBase(BaseModel):
    article_no: str = Field(..., description="条文编号")
    law_name: str = Field(..., description="法律名称")
    title: str | None = Field(default=None, description="条文标题")
    content: str = Field(..., description="条文内容")
    keywords: list[str] = Field(default_factory=list, description="关键词标签")
    scenario_tags: list[str] = Field(default_factory=list, description="适用场景标签")
    source_type: str = Field(default="law", description="来源类型")
    effective_date: date | None = Field(default=None, description="生效日期")
    status: str = Field(default="active", description="状态")
    extra_meta: dict = Field(default_factory=dict, description="附加信息")


class KnowledgeUpsertItem(KnowledgeBase):
    id: str | None = None


class KnowledgeRead(KnowledgeBase):
    id: str

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., description="搜索文本，可为案件描述、风险摘要、法条关键词")
    law_name: str | None = Field(default=None, description="限定某部法律")
    scenario_tag: str | None = Field(default=None, description="限定某个适用场景标签")
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchHit(BaseModel):
    id: str
    article_no: str
    law_name: str
    title: str | None = None
    content: str
    keywords: list[str] = Field(default_factory=list)
    scenario_tags: list[str] = Field(default_factory=list)
    score: float = 0.0
    reason: str = ""
    matched_terms: list[str] = Field(default_factory=list)


class KnowledgeBatchUpsertRequest(BaseModel):
    items: list[KnowledgeUpsertItem]


class KnowledgeSearchResponse(BaseModel):
    hits: list[KnowledgeSearchHit]
