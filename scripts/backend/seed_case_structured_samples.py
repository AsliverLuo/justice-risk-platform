from __future__ import annotations

import json
from pathlib import Path

from app.db.session import SessionLocal, init_db
from app.modules.analysis.schemas import CaseCorpusBatchUpsertRequest, CaseCorpusUpsertItem
from app.modules.analysis.service import AnalysisService


ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = ROOT / 'mock_data' / 'case_corpus_structured_seed.json'


def main() -> None:
    init_db()
    payload = json.loads(SAMPLE_PATH.read_text(encoding='utf-8'))
    items = [CaseCorpusUpsertItem.model_validate(item) for item in payload.get('items', [])]
    with SessionLocal() as db:
        service = AnalysisService(db)
        service.batch_upsert_corpus(CaseCorpusBatchUpsertRequest(items=items))
    print(f'seeded {len(items)} structured case corpus items')


if __name__ == '__main__':
    main()
