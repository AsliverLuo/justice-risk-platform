from __future__ import annotations

import json
from pathlib import Path

from app.db.session import SessionLocal
from app.modules.analysis.schemas import CaseCorpusBatchUpsertRequest
from app.modules.analysis.service import AnalysisService


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FILE = ROOT / 'mock_data' / 'case_corpus_sample.json'


def main() -> None:
    data = json.loads(DEFAULT_FILE.read_text(encoding='utf-8'))
    payload = CaseCorpusBatchUpsertRequest(**data)
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        result = service.batch_upsert_corpus(payload)
        print(f'seeded {len(result)} case corpus items')
    finally:
        db.close()


if __name__ == '__main__':
    main()
