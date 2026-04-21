from __future__ import annotations

from typing import Any


def _as_set(values: list[str] | None) -> set[str]:
    return {str(x).strip() for x in (values or []) if str(x).strip()}


def _norm_hot(value: float | int | None) -> float:
    try:
        score = float(value or 0.0)
    except Exception:
        score = 0.0
    score = max(0.0, min(score, 100.0))
    return score / 100.0


def expand_context_tags(risk_type: str | None, context_tags: list[str] | None, alert_code: str | None = None) -> list[str]:
    tags = []
    for item in (context_tags or []):
        item = str(item).strip()
        if item and item not in tags:
            tags.append(item)

    aliases = {
        'labor_service_dispute': ['欠薪', '劳务合同纠纷', '工地欠薪', '农民工工资'],
        'labor_dispute': ['劳动争议', '劳动报酬', '维权'],
        'support_prosecution': ['支持起诉', '依法维权'],
        'other': ['普法', '法治治理'],
        'group_wage_arrears': ['群体性欠薪', '多人维权', '工地欠薪'],
        'high_frequency_defendant': ['高频欠薪主体', '重复主体', '发包方拖欠'],
        'risk_level_upgrade': ['风险升级', '重点治理'],
    }
    for source in [risk_type, alert_code]:
        if source and source in aliases:
            for tag in aliases[source]:
                if tag not in tags:
                    tags.append(tag)
    if risk_type and risk_type not in tags:
        tags.append(risk_type)
    if alert_code and alert_code not in tags:
        tags.append(alert_code)
    return tags


def score_article_match(article: Any, *, risk_type: str, context_tags: list[str], related_law_names: list[str], scope_type: str) -> dict:
    article_risk_types = _as_set(getattr(article, 'risk_types', None))
    article_tags = _as_set(getattr(article, 'scenario_tags', None))
    article_laws = _as_set(getattr(article, 'related_law_names', None))
    article_scopes = _as_set(getattr(article, 'applicable_scope_types', None))

    context_tag_set = _as_set(context_tags)
    law_set = _as_set(related_law_names)

    score = 0.0
    reasons: list[str] = []
    matched_risk_types: list[str] = []
    matched_scenario_tags: list[str] = []

    if article_risk_types:
        if risk_type in article_risk_types:
            score += 0.45
            matched_risk_types.append(risk_type)
            reasons.append(f'风险类型命中：{risk_type}')
        elif 'other' in article_risk_types or 'general' in article_risk_types:
            score += 0.08
            matched_risk_types.extend(sorted(article_risk_types & {'other', 'general'}))
            reasons.append('通用普法内容兜底')
    else:
        score += 0.10
        reasons.append('未设置风险类型，按通用内容处理')

    if article_tags and context_tag_set:
        overlap = article_tags & context_tag_set
        if overlap:
            matched_scenario_tags = sorted(overlap)
            ratio = len(overlap) / max(1, len(article_tags))
            score += min(0.30, 0.18 + ratio * 0.12)
            reasons.append('场景标签匹配：' + '、'.join(matched_scenario_tags[:3]))
    elif not article_tags:
        score += 0.04

    if article_laws and law_set:
        law_overlap = sorted(article_laws & law_set)
        if law_overlap:
            score += min(0.10, 0.05 * len(law_overlap))
            reasons.append('相关法条匹配：' + '、'.join(law_overlap[:2]))

    if article_scopes:
        if scope_type in article_scopes:
            score += 0.05
            reasons.append(f'适用范围匹配：{scope_type}')
    else:
        score += 0.03

    score += _norm_hot(getattr(article, 'hot_score', 0.0)) * 0.10
    score += max(0.0, min(float(getattr(article, 'priority', 50)), 100.0)) / 100.0 * 0.05

    return {
        'score': round(score * 100, 4),
        'matched_risk_types': matched_risk_types,
        'matched_scenario_tags': matched_scenario_tags,
        'match_reason': '；'.join(reasons) if reasons else '热度排序补位',
    }
