from __future__ import annotations

import math
from typing import Iterable

from sqlalchemy import JSON

try:
    from pgvector.sqlalchemy import Vector  # type: ignore
    HAS_PGVECTOR = True
except Exception:  # pragma: no cover - fallback
    Vector = None  # type: ignore
    HAS_PGVECTOR = False


def get_vector_column_type(dim: int):
    if HAS_PGVECTOR:
        return Vector(dim)
    return JSON


def l2_norm(values: Iterable[float]) -> float:
    return math.sqrt(sum(v * v for v in values))


def normalize_vector(values: Iterable[float]) -> list[float]:
    vals = [float(v) for v in values]
    norm = l2_norm(vals)
    if norm == 0:
        return vals
    return [v / norm for v in vals]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = l2_norm(vec_a)
    norm_b = l2_norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))
