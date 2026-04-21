from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal, init_db
from app.modules.alert.schemas import CommunityRiskEngineRequest
from app.modules.alert.service import AlertService


def main() -> None:
    parser = argparse.ArgumentParser(description='Run community risk alert engine')
    parser.add_argument('--scope-type', default='community', choices=['community', 'street', 'project'])
    parser.add_argument('--window-days', type=int, default=30)
    parser.add_argument('--compare-window-days', type=int, default=30)
    parser.add_argument('--no-persist', action='store_true')
    parser.add_argument('--no-alerts', action='store_true')
    parser.add_argument('--out', default='../docs/alert_engine_run_result.json')
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        service = AlertService(db)
        response = service.run_engine(
            CommunityRiskEngineRequest(
                scope_type=args.scope_type,
                window_days=args.window_days,
                compare_window_days=args.compare_window_days,
                persist_profiles=not args.no_persist,
                generate_alerts=not args.no_alerts,
            )
        )
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(response.model_dump_json(indent=2), encoding='utf-8')
        print(json.dumps({'profile_count': response.profile_count, 'alert_count': response.alert_count, 'out': str(out_path)}, ensure_ascii=False))
    finally:
        db.close()


if __name__ == '__main__':
    main()
