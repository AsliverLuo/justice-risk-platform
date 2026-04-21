from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from app.core.config import settings
from app.core.logger import get_logger
from app.infra.vector_store import normalize_vector


logger = get_logger(__name__)


class BaseEmbeddingClient(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


class HashEmbeddingClient(BaseEmbeddingClient):
    """离线可跑的回退方案。

    作用：
    1. 没有 GPU / 没有模型 / 没有 API Key 时也能联调
    2. 让知识库流程先跑通
    3. 后续切换到真实 embedding 时不改上层 service/repository
    """

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def embed_text(self, text: str) -> list[float]:
        buckets = [0.0] * self.dim
        for token in self._tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i in range(self.dim):
                buckets[i] += digest[i % len(digest)] / 255.0
        return normalize_vector(buckets)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = (text or "").strip().lower()
        if not text:
            return [""]
        # 简单兼容中英文
        chars = [ch for ch in text if not ch.isspace()]
        tokens = []
        for idx, ch in enumerate(chars):
            tokens.append(ch)
            if idx < len(chars) - 1:
                tokens.append(ch + chars[idx + 1])
        return tokens or [text]


class SentenceTransformerEmbeddingClient(BaseEmbeddingClient):
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> list[float]:
        vector = self.model.encode(text or "", normalize_embeddings=True)
        return [float(v) for v in vector.tolist()]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [[float(v) for v in row.tolist()] for row in vectors]


def build_embedding_client() -> BaseEmbeddingClient:
    provider = settings.embedding_provider

    if provider == "local":
        try:
            logger.info("loading local embedding model: %s", settings.embedding_model)
            return SentenceTransformerEmbeddingClient(settings.embedding_model)
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning("local embedding unavailable, fallback to hash embedding: %s", exc)

    logger.info("using hash embedding fallback, dim=%s", settings.embedding_dimension)
    return HashEmbeddingClient(dim=settings.embedding_dimension)
