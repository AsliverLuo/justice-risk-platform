from __future__ import annotations

import json
from pathlib import Path

from app.db.session import SessionLocal, init_db
from app.modules.knowledge.schemas import KnowledgeBatchUpsertRequest, KnowledgeUpsertItem
from app.modules.knowledge.service import LegalKnowledgeService


def main() -> None:
    init_db()
    seed_path = Path(__file__).resolve().parents[2] / "mock_data" / "legal_knowledge_seed.user.json"
    rows = json.loads(seed_path.read_text(encoding="utf-8"))
    payload = KnowledgeBatchUpsertRequest(
        items=[KnowledgeUpsertItem(**row) for row in rows]
    )
    with SessionLocal() as db:
        service = LegalKnowledgeService(db)
        result = service.batch_upsert(payload)
        print(f"seeded {len(result)} legal knowledge items")


if __name__ == "__main__":
    main()
