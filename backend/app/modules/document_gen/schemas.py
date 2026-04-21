from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentGenerateRequest(BaseModel):
    document_types: list[str] = Field(default_factory=lambda: ["complaint"])


class GeneratedDocument(BaseModel):
    document_type: str
    title: str
    content: str


class DocumentGenerateResponse(BaseModel):
    case_id: int
    documents: list[GeneratedDocument]
