from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILE = ROOT / "mock_data" / "cases" / "demo_cases_100.json"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.modules.analysis.schemas import CaseCorpusBatchUpsertRequest, CaseCorpusUpsertItem
from app.modules.analysis.service import AnalysisService


def parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def join_values(values: list[str] | None) -> str | None:
    if not values:
        return None
    return "；".join(str(item) for item in values if item)


def build_full_text(case: dict[str, Any]) -> str:
    sections = [
        f"案件标题：{case.get('title', '')}",
        f"案件类型：{case.get('case_type', '')} / {case.get('sub_type', '')}",
        f"区域位置：{case.get('region', '')}{case.get('street', '')}",
        f"案情描述：{case.get('description', '')}",
        f"申请人：{join_values(case.get('parties', {}).get('claimants')) or ''}",
        f"责任主体：{join_values(case.get('parties', {}).get('defendants')) or ''}",
        f"涉案金额：{case.get('amount', 0)}元",
        f"涉及人数：{case.get('people_count', 0)}人",
        f"证据材料：{join_values(case.get('evidence')) or ''}",
        f"预警特征：{join_values(case.get('warning_features')) or ''}",
        f"治理建议：{join_values(case.get('recommended_actions')) or ''}",
        f"普法主题：{join_values(case.get('propaganda_topics')) or ''}",
    ]
    return "\n".join(sections)


def convert_case(case: dict[str, Any]) -> CaseCorpusUpsertItem:
    claimants = case.get("parties", {}).get("claimants", [])
    defendants = case.get("parties", {}).get("defendants", [])
    amount = case.get("amount", 0)
    street = case.get("street")
    street_id = f"xicheng-{street}" if street else None

    return CaseCorpusUpsertItem(
        id=case["case_id"],
        source_type="demo_case",
        source_ref=case["case_id"],
        title=case["title"],
        case_no=case["case_id"],
        full_text=build_full_text(case),
        case_type=case.get("case_type"),
        plaintiff_summary=join_values(claimants),
        defendant_summary=join_values(defendants),
        claim_summary=case.get("description"),
        focus_summary=join_values(case.get("tags")),
        fact_summary=case.get("description"),
        judgment_summary=None,
        court_name=None,
        province="北京市",
        city="北京市",
        occurred_at=parse_date(case.get("report_time")),
        judgment_date=None,
        entities={
            "persons": claimants,
            "companies": defendants,
            "amounts": [f"{amount}元"] if amount else [],
            "amount_total_estimate": float(amount or 0),
            "dates": [case.get("report_time")] if case.get("report_time") else [],
            "addresses": [f"{case.get('region', '')}{street or ''}"] if street else [],
            "projects": [case.get("title", "")],
            "phones": [],
            "id_cards": [],
            "law_refs": [],
        },
        cited_laws=[],
        extra_meta={
            "region": case.get("region"),
            "street": street,
            "community_id": street_id,
            "community_name": street,
            "street_id": street_id,
            "street_name": street,
            "longitude": case.get("longitude"),
            "latitude": case.get("latitude"),
            "source": case.get("source"),
            "report_time": case.get("report_time"),
            "sub_type": case.get("sub_type"),
            "amount": amount,
            "total_amount": amount,
            "people_count": case.get("people_count"),
            "risk_type": case.get("case_type"),
            "risk_level": case.get("risk_level"),
            "risk_score": case.get("risk_score"),
            "defendant_names": defendants,
            "tags": case.get("tags", []),
            "evidence": case.get("evidence", []),
            "warning_features": case.get("warning_features", []),
            "expected_modules": case.get("expected_modules", []),
            "recommended_actions": case.get("recommended_actions", []),
            "propaganda_topics": case.get("propaganda_topics", []),
            "status": case.get("status"),
            "support_prosecution_candidate": case.get("support_prosecution_candidate"),
            "is_fictional": case.get("is_fictional", True),
        },
    )


def load_cases(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("demo case file must be a JSON array")
    if limit:
        return data[:limit]
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Import generated demo cases into analysis case corpus.")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="demo case JSON file")
    parser.add_argument("--limit", type=int, default=None, help="only import first N cases")
    parser.add_argument("--dry-run", action="store_true", help="convert and validate only, do not write database")
    args = parser.parse_args()

    cases = load_cases(args.file, limit=args.limit)
    items = [convert_case(case) for case in cases]
    payload = CaseCorpusBatchUpsertRequest(items=items)

    if args.dry_run:
        type_counts: dict[str, int] = {}
        for item in payload.items:
            type_counts[item.case_type or "未分类"] = type_counts.get(item.case_type or "未分类", 0) + 1
        print(f"validated {len(payload.items)} demo cases")
        print(type_counts)
        print(f"first case: {payload.items[0].id} {payload.items[0].title}" if payload.items else "no cases")
        return

    db = SessionLocal()
    try:
        service = AnalysisService(db)
        result = service.batch_upsert_corpus(payload)
        print(f"imported {len(result)} demo cases into case corpus")
    finally:
        db.close()


if __name__ == "__main__":
    main()
