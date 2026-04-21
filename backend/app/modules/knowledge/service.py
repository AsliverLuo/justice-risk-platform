from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.infra.embedding import BaseEmbeddingClient, build_embedding_client
from app.modules.knowledge.repository import LegalKnowledgeRepository
from app.modules.knowledge.schemas import (
    KnowledgeBatchUpsertRequest,
    KnowledgeRead,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)


class LegalKnowledgeService:
    def __init__(
        self,
        db: Session,
        embedding_client: BaseEmbeddingClient | None = None,
    ) -> None:
        self.db = db
        self.embedding_client = embedding_client or build_embedding_client()
        self.repo = LegalKnowledgeRepository(db)

    def batch_upsert(self, payload: KnowledgeBatchUpsertRequest) -> list[KnowledgeRead]:
        items = payload.items
        texts = [
            " ".join(
                [
                    item.law_name,
                    item.article_no,
                    item.title or "",
                    " ".join(item.keywords),
                    " ".join(item.scenario_tags),
                    item.content,
                ]
            )
            for item in items
        ]
        embeddings = self.embedding_client.embed_texts(texts)

        output: list[KnowledgeRead] = []
        for item, embedding in zip(items, embeddings):
            obj = self.repo.upsert(item=item, embedding=embedding)
            output.append(KnowledgeRead.model_validate(obj))

        self.db.commit()
        return output

    def get(self, knowledge_id: str) -> KnowledgeRead | None:
        obj = self.repo.get(knowledge_id)
        if not obj:
            return None
        return KnowledgeRead.model_validate(obj)

    def search(self, payload: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
        query_embedding = self.embedding_client.embed_text(payload.query)
        hits = self.repo.hybrid_search(
            query=payload.query,
            query_embedding=query_embedding,
            top_k=payload.top_k or settings.knowledge_top_k,
            law_name=payload.law_name,
            scenario_tag=payload.scenario_tag,
        )
        return KnowledgeSearchResponse(hits=hits)

    def retrieve_context_blocks(self, query: str, top_k: int = 5) -> list[str]:
        response = self.search(KnowledgeSearchRequest(query=query, top_k=top_k))
        blocks: list[str] = []
        for hit in response.hits:
            blocks.append(
                f"【{hit.law_name} {hit.article_no}】"
                f"{hit.title or ''} "
                f"适用场景：{', '.join(hit.scenario_tags)} "
                f"内容：{hit.content}"
            )
        return blocks

    def build_context_for_llm(self, query: str, top_k: int = 5) -> str:
        return "\n".join(self.retrieve_context_blocks(query=query, top_k=top_k))
