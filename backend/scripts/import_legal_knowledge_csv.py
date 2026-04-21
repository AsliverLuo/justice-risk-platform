from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Iterable

from sqlalchemy import text

from app.db.session import SessionLocal, init_db
from app.modules.knowledge.schemas import KnowledgeBatchUpsertRequest, KnowledgeUpsertItem
from app.modules.knowledge.service import LegalKnowledgeService

STANDARD_HEADER = [
    "序号",
    "条文编号",
    "法律全称",
    "标题",
    "条文原文",
    "keywords",
    "scenario_tags",
    "用途分类",
    "完成状态",
]

TAG_SPLIT_RE = re.compile(r"[;,，；、\n\t]+")


def split_tags(value: str | None) -> list[str]:
    if value is None:
        return []
    raw = str(value).strip().strip('"').strip("'")
    if not raw:
        return []
    parts = [part.strip() for part in TAG_SPLIT_RE.split(raw) if part and part.strip()]
    seen: set[str] = set()
    output: list[str] = []
    for part in parts:
        if part not in seen:
            seen.add(part)
            output.append(part)
    return output


def read_csv_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0] if text.splitlines() else ""
    has_header = ("条文编号" in first_line) and ("法律全称" in first_line)

    if has_header:
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    # 兼容“指导意见”这类没有表头、第一行就是数据的 CSV
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(zip(STANDARD_HEADER, row)) for row in csv.reader(f)]


def normalize_rows(rows: Iterable[dict], source_file: str, merge_purpose_tags: bool = False) -> list[dict]:
    items: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    for raw in rows:
        law_name = str(raw.get("法律全称", "")).strip()
        article_no = str(raw.get("条文编号", "")).strip()
        title = str(raw.get("标题", "")).strip() or None
        content = str(raw.get("条文原文", "")).strip()
        if law_name == "法律全称" or article_no == "条文编号" or content == "条文原文":
            continue
        if not (law_name and article_no and content):
            continue

        keywords = split_tags(raw.get("keywords"))
        scenario_tags = split_tags(raw.get("scenario_tags"))
        purpose_categories = split_tags(raw.get("用途分类"))
        if merge_purpose_tags:
            scenario_tags = list(dict.fromkeys(scenario_tags + purpose_categories))

        key = (law_name, article_no)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        items.append(
            {
                "article_no": article_no,
                "law_name": law_name,
                "title": title,
                "content": content,
                "keywords": keywords,
                "scenario_tags": scenario_tags,
                "source_type": "law",
                "status": "active",
                "extra_meta": {
                    "serial_no": str(raw.get("序号", "")).strip(),
                    "purpose_category": purpose_categories,
                    "annotation_status": str(raw.get("完成状态", "")).strip(),
                    "source_file": source_file,
                },
            }
        )
    return items


def build_items_from_csv_dir(input_dir: Path, merge_purpose_tags: bool = False) -> list[dict]:
    all_items: list[dict] = []
    global_seen: set[tuple[str, str]] = set()
    for path in sorted(input_dir.glob("*.csv")):
        rows = read_csv_rows(path)
        items = normalize_rows(rows, source_file=path.name, merge_purpose_tags=merge_purpose_tags)
        for item in items:
            key = (item["law_name"], item["article_no"])
            if key not in global_seen:
                all_items.append(item)
                global_seen.add(key)
    return all_items


def main() -> None:
    parser = argparse.ArgumentParser(description="将法律知识库 CSV 转为 pkg2 可导入的 JSON，并可直接写入数据库")
    parser.add_argument("--input-dir", type=str, required=True, help="CSV 所在目录")
    parser.add_argument("--output-json", type=str, default="", help="输出 JSON 文件路径")
    parser.add_argument("--merge-purpose-tags", action="store_true", help="将‘用途分类’合并进 scenario_tags")
    parser.add_argument("--do-import", action="store_true", help="转换后直接入库")
    parser.add_argument("--drop-example", action="store_true", help="入库前删除 source_type=example 或 article_no 以 示例- 开头的联调数据")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists():
        raise FileNotFoundError(f"input dir not found: {input_dir}")

    items = build_items_from_csv_dir(input_dir=input_dir, merge_purpose_tags=args.merge_purpose_tags)
    print(f"normalized {len(items)} knowledge items from {input_dir}")

    if args.output_json:
        output_path = Path(args.output_json).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote json -> {output_path}")

    if args.do_import:
        init_db()
        payload = KnowledgeBatchUpsertRequest(items=[KnowledgeUpsertItem(**item) for item in items])
        with SessionLocal() as db:
            if args.drop_example:
                db.execute(text("DELETE FROM legal_knowledge WHERE source_type = 'example' OR article_no LIKE '示例-%'"))
                db.commit()
                print("deleted example knowledge rows")
            service = LegalKnowledgeService(db)
            result = service.batch_upsert(payload)
            print(f"imported {len(result)} knowledge items into database")


if __name__ == "__main__":
    main()
