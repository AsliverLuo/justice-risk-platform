from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from app.db.session import SessionLocal, init_db
from app.modules.analysis.schemas import EntityExtractRequest, LawLinkRequest, NLPClassifyRequest
from app.modules.analysis.service import AnalysisService


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / 'mock_data' / 'nlp_eval_cases.json'
DEFAULT_REPORT_JSON = ROOT / 'docs' / 'nlp_verification_report.json'
DEFAULT_REPORT_MD = ROOT / 'docs' / 'nlp_verification_report.md'
ARTICLE_REF_PATTERN = re.compile(r'第([一二三四五六七八九十百零〇0-9]+)条')
CHINESE_NUMERAL_MAP = {'零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
CHINESE_UNIT_MAP = {'十': 10, '百': 100, '千': 1000}


def normalize_article_ordinal(value: str) -> str:
    value = (value or '').strip()
    if value.isdigit():
        return value
    if not value or not all(ch in CHINESE_NUMERAL_MAP or ch in CHINESE_UNIT_MAP for ch in value):
        return value
    section = 0
    number = 0
    for ch in value:
        if ch in CHINESE_NUMERAL_MAP:
            number = CHINESE_NUMERAL_MAP[ch]
        else:
            unit = CHINESE_UNIT_MAP[ch]
            if number == 0:
                number = 1
            section += number * unit
            number = 0
    total = section + number
    return str(total) if total > 0 else value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='验证 analysis 三个 NLP 能力：分类、实体抽取、法条关联')
    parser.add_argument('--input', default=str(DEFAULT_INPUT), help='评测样本 JSON 路径')
    parser.add_argument('--report-json', default=str(DEFAULT_REPORT_JSON), help='输出 JSON 报告路径')
    parser.add_argument('--report-md', default=str(DEFAULT_REPORT_MD), help='输出 Markdown 报告路径')
    parser.add_argument('--top-k-laws', type=int, default=5, help='法条关联返回数量')
    parser.add_argument('--prefer-llm', action='store_true', help='优先调用真实大模型')
    parser.add_argument('--write-report', action='store_true', help='写出报告文件')
    return parser.parse_args()


def text_match(expected: str, predicted: list[str]) -> bool:
    expected = (expected or '').strip()
    return any(expected in item or item in expected for item in predicted)


def law_ref_key(law_name: str, article_no: str) -> str:
    law_name = re.sub(r'\s+', '', (law_name or '').replace('《', '').replace('》', ''))
    match = ARTICLE_REF_PATTERN.search(article_no or '')
    if match:
        article_no = normalize_article_ordinal(match.group(1))
    else:
        article_no = normalize_article_ordinal((article_no or '').replace(' ', ''))
    return f'{law_name}|{article_no}'


def expected_law_key(ref: str) -> str:
    law_name, _, article = ref.partition('|')
    return law_ref_key(law_name, article)


def eval_case(service: AnalysisService, case: dict[str, Any], prefer_llm: bool, top_k_laws: int) -> dict[str, Any]:
    title = case['title']
    text = case['text']
    expected = case['expected']

    classify = service.classify_text(NLPClassifyRequest(title=title, text=text, prefer_llm=prefer_llm))
    entities = service.extract_entities_capability(EntityExtractRequest(title=title, text=text, prefer_llm=prefer_llm))
    laws = service.link_laws(LawLinkRequest(title=title, text=text, top_k=top_k_laws, prefer_llm=prefer_llm))

    entity_pred = entities.entities.model_dump()
    entity_scores: dict[str, dict[str, Any]] = {}
    for field in ['persons', 'companies', 'amounts', 'dates', 'addresses']:
        expected_items = expected.get(field, [])
        predicted_items = entity_pred.get(field, []) or []
        matched_items = [item for item in expected_items if text_match(item, predicted_items)]
        score = 1.0 if not expected_items else round(len(matched_items) / len(expected_items), 4)
        entity_scores[field] = {
            'expected': expected_items,
            'predicted': predicted_items,
            'matched': matched_items,
            'score': score,
        }

    predicted_law_keys = [law_ref_key(item.law_name, item.article_no) for item in laws.matched_laws]
    expected_laws = expected.get('law_refs', [])
    matched_laws = [ref for ref in expected_laws if expected_law_key(ref) in predicted_law_keys]
    law_score = 1.0 if not expected_laws else round(len(matched_laws) / len(expected_laws), 4)

    return {
        'case_id': case['case_id'],
        'title': title,
        'classify': {
            'expected': expected.get('case_type'),
            'predicted': classify.case_type,
            'passed': classify.case_type == expected.get('case_type'),
            'mode': classify.mode,
            'confidence': classify.confidence,
            'reason': classify.reason,
        },
        'entities': {
            'mode': entities.mode,
            'scores': entity_scores,
            'overall_score': round(sum(v['score'] for v in entity_scores.values()) / max(1, len(entity_scores)), 4),
        },
        'law_link': {
            'mode': laws.mode,
            'candidate_count': laws.candidate_count,
            'retrieval_queries': laws.retrieval_queries,
            'expected': expected_laws,
            'predicted': [
                {
                    'law_name': item.law_name,
                    'article_no': item.article_no,
                    'title': item.title,
                    'reason': item.reason,
                    'score': item.score,
                }
                for item in laws.matched_laws
            ],
            'matched': matched_laws,
            'score': law_score,
        },
    }


def build_markdown_report(results: list[dict[str, Any]]) -> str:
    lines = ['# NLP 能力验证报告', '']
    if not results:
        return '\n'.join(lines + ['无结果'])

    class_pass = sum(1 for item in results if item['classify']['passed'])
    entity_avg = round(sum(item['entities']['overall_score'] for item in results) / len(results), 4)
    law_avg = round(sum(item['law_link']['score'] for item in results) / len(results), 4)

    lines.extend([
        f'- 分类准确率（当前样本）：{class_pass}/{len(results)} = {round(class_pass/len(results), 4)}',
        f'- 实体抽取平均覆盖率：{entity_avg}',
        f'- 法条关联平均命中率：{law_avg}',
        '',
    ])

    for item in results:
        lines.append(f"## {item['title']}")
        lines.append(f"- 分类：{item['classify']['predicted']}（期望：{item['classify']['expected']}，mode={item['classify']['mode']}）")
        lines.append(f"- 实体抽取 mode：{item['entities']['mode']}，overall={item['entities']['overall_score']}")
        for field, detail in item['entities']['scores'].items():
            lines.append(
                f"  - {field}: score={detail['score']}，expected={detail['expected']}，predicted={detail['predicted']}"
            )
        lines.append(
            f"- 法条关联 mode：{item['law_link']['mode']}，score={item['law_link']['score']}，matched={item['law_link']['matched']}"
        )
        lines.append(f"- 法条候选数：{item['law_link']['candidate_count']}")
        lines.append('')
    return '\n'.join(lines)


def main() -> None:
    args = parse_args()
    init_db()
    data = json.loads(Path(args.input).read_text(encoding='utf-8'))
    cases = data.get('cases', [])
    with SessionLocal() as db:
        service = AnalysisService(db)
        results = [
            eval_case(service=service, case=case, prefer_llm=args.prefer_llm, top_k_laws=args.top_k_laws)
            for case in cases
        ]

    report = {
        'prefer_llm': args.prefer_llm,
        'case_count': len(results),
        'results': results,
    }
    md = build_markdown_report(results)
    print(md)

    if args.write_report:
        Path(args.report_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        Path(args.report_md).write_text(md, encoding='utf-8')
        print(f'\nwritten report json -> {args.report_json}')
        print(f'written report md   -> {args.report_md}')


if __name__ == '__main__':
    main()
