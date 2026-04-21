from __future__ import annotations

import re
from collections import OrderedDict

from app.common.enums import CaseType, RiskLevel
from app.core.config import settings
from app.modules.analysis.schemas import CaseRiskHint, EntityGroup, RiskScoreDetail, RiskScoreResponse


COMPANY_PATTERN = re.compile(r'[一-龥A-Za-z0-9（）()\-]{2,40}(?:有限责任公司|有限公司|集团|公司|建设公司|劳务公司|工程局|工程公司|人民检察院|人民法院)')
PERSON_PATTERN = re.compile(r'(?:原告|被告|申请人|被申请人|法定代表人|负责人|实控人|项目经理|上诉人|被上诉人)[:：]?[（(]?(?:原审[^）)]*)?[）)]?\s*([一-龥]{2,4})')
PERSON_FALLBACK_PATTERN = re.compile(r'([一-龥]{1,3}某[一-龥]{0,2})')
AMOUNT_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*(万元|元)')
DATE_PATTERN = re.compile(r'\d{4}年\d{1,2}月\d{1,2}日')
PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')
ID_CARD_PATTERN = re.compile(r'\d{17}[\dXx]')
ADDRESS_PATTERN = re.compile(r'(?:北京市|天津市|上海市|重庆市|[一-龥]{2,8}省)?[一-龥]{1,12}(?:区|县|市)(?:[一-龥A-Za-z0-9]{0,20}(?:人民检察院|人民法院|街道|社区|工地|项目|路|号))?')
PROJECT_PATTERN = re.compile(r'[一-龥A-Za-z0-9（）()\-]{2,50}(?:工地|项目|工程)')
LAW_REF_PATTERN = re.compile(r'《[^》]{2,40}》第?[一二三四五六七八九十百零0-9]+条')
RANGE_DAY_PATTERN = re.compile(r'工作\s*(\d+)\s*天')


def unique_keep_order(values: list[str]) -> list[str]:
    return list(OrderedDict((v, None) for v in values if v))


def classify_case_type(text: str, title: str | None = None) -> str:
    haystack = f"{title or ''}\n{text or ''}".lower()
    if any(token in haystack for token in ['劳动仲裁', '劳动争议', '解除劳动关系', '工伤认定', '劳动合同', '违法解除']):
        return CaseType.labor_dispute.value
    if any(token in haystack for token in ['劳务合同', '劳务费', '劳务报酬', '追索劳动报酬', '欠薪', '农民工工资']):
        return CaseType.labor_service_dispute.value
    return CaseType.other.value


def extract_entities(text: str) -> EntityGroup:
    text = text or ''
    persons = PERSON_PATTERN.findall(text)
    persons.extend(PERSON_FALLBACK_PATTERN.findall(text))
    companies = COMPANY_PATTERN.findall(text)
    amounts_raw = AMOUNT_PATTERN.findall(text)
    dates = DATE_PATTERN.findall(text)
    phones = PHONE_PATTERN.findall(text)
    id_cards = ID_CARD_PATTERN.findall(text)
    addresses = ADDRESS_PATTERN.findall(text)
    projects = PROJECT_PATTERN.findall(text)
    law_refs = LAW_REF_PATTERN.findall(text)

    amounts: list[str] = []
    amount_total_estimate = 0.0
    for num, unit in amounts_raw:
        value = float(num)
        if unit == '万元':
            amount_total_estimate += value * 10000
            amounts.append(f'{value:g}万元')
        else:
            amount_total_estimate += value
            amounts.append(f'{value:g}元')

    # 补一个简单的工作天数实体，便于后面做 AI 叙事和风险解释
    days = RANGE_DAY_PATTERN.findall(text)
    for day in days:
        amounts.append(f'工作{day}天')

    return EntityGroup(
        persons=unique_keep_order(persons),
        companies=unique_keep_order(companies),
        amounts=unique_keep_order(amounts),
        amount_total_estimate=round(amount_total_estimate, 2),
        dates=unique_keep_order(dates),
        addresses=unique_keep_order(addresses),
        projects=unique_keep_order(projects),
        phones=unique_keep_order(phones),
        id_cards=unique_keep_order(id_cards),
        law_refs=unique_keep_order(law_refs),
    )


def build_case_summary(case_type: str, entities: EntityGroup, title: str | None = None) -> str:
    parts: list[str] = []
    if title:
        parts.append(f'标题：{title}')
    parts.append(f'案件类型：{case_type}')
    if entities.persons:
        parts.append(f'涉及自然人：{"、".join(entities.persons[:4])}')
    if entities.companies:
        parts.append(f'涉及企业：{"、".join(entities.companies[:4])}')
    if entities.projects:
        parts.append(f'工程/项目：{"、".join(entities.projects[:3])}')
    if entities.addresses:
        parts.append(f'地点线索：{"、".join(entities.addresses[:3])}')
    if entities.amount_total_estimate:
        parts.append(f'金额估算：约 {entities.amount_total_estimate:.2f} 元')
    if entities.dates:
        parts.append(f'时间线索：{"、".join(entities.dates[:4])}')
    if entities.law_refs:
        parts.append(f'文本中已出现法条：{"、".join(entities.law_refs[:3])}')
    return '；'.join(parts)


def build_case_risk_hints(amount_total_estimate: float, people_count: int, repeat_defendant_count: int) -> list[CaseRiskHint]:
    return [
        CaseRiskHint(
            label='群体性欠薪风险',
            triggered=people_count >= settings.alert_group_people_threshold,
            detail=f'当前涉及人数={people_count}，阈值={settings.alert_group_people_threshold}',
        ),
        CaseRiskHint(
            label='高频欠薪主体风险',
            triggered=repeat_defendant_count >= settings.alert_repeat_defendant_threshold_30d,
            detail=f'同一主体重复出现次数={repeat_defendant_count}，阈值={settings.alert_repeat_defendant_threshold_30d}',
        ),
        CaseRiskHint(
            label='大额欠薪风险',
            triggered=amount_total_estimate >= 50000,
            detail=f'金额估算={amount_total_estimate:.2f} 元，演示阈值=50000 元',
        ),
    ]


def _normalize(value: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return max(0.0, min(value / cap, 1.0))


def _level_from_score(score: float) -> str:
    if score >= settings.risk_red_threshold:
        return RiskLevel.red.value
    if score >= settings.risk_orange_threshold:
        return RiskLevel.orange.value
    if score >= settings.risk_yellow_threshold:
        return RiskLevel.yellow.value
    return RiskLevel.blue.value


def calculate_aggregate_risk(
    case_count: int,
    total_amount: float,
    people_count: int,
    growth_rate: float,
    repeat_defendant_rate: float,
) -> RiskScoreResponse:
    case_count_norm = _normalize(float(case_count), float(settings.risk_case_count_cap))
    total_amount_norm = _normalize(float(total_amount), float(settings.risk_total_amount_cap))
    people_count_norm = _normalize(float(people_count), float(settings.risk_people_count_cap))
    growth_rate_norm = _normalize(float(growth_rate), float(settings.risk_growth_rate_cap))
    repeat_rate_norm = _normalize(float(repeat_defendant_rate), float(settings.risk_repeat_defendant_rate_cap))

    details = [
        RiskScoreDetail(
            metric='case_count',
            raw_value=float(case_count),
            normalized_value=round(case_count_norm, 6),
            weight=settings.risk_weight_case_count,
            contribution=round(case_count_norm * settings.risk_weight_case_count * 100, 6),
        ),
        RiskScoreDetail(
            metric='total_amount',
            raw_value=float(total_amount),
            normalized_value=round(total_amount_norm, 6),
            weight=settings.risk_weight_total_amount,
            contribution=round(total_amount_norm * settings.risk_weight_total_amount * 100, 6),
        ),
        RiskScoreDetail(
            metric='people_count',
            raw_value=float(people_count),
            normalized_value=round(people_count_norm, 6),
            weight=settings.risk_weight_people_count,
            contribution=round(people_count_norm * settings.risk_weight_people_count * 100, 6),
        ),
        RiskScoreDetail(
            metric='growth_rate',
            raw_value=float(growth_rate),
            normalized_value=round(growth_rate_norm, 6),
            weight=settings.risk_weight_trend,
            contribution=round(growth_rate_norm * settings.risk_weight_trend * 100, 6),
        ),
        RiskScoreDetail(
            metric='repeat_defendant_rate',
            raw_value=float(repeat_defendant_rate),
            normalized_value=round(repeat_rate_norm, 6),
            weight=settings.risk_weight_repeat_defendant,
            contribution=round(repeat_rate_norm * settings.risk_weight_repeat_defendant * 100, 6),
        ),
    ]

    score = round(sum(item.contribution for item in details), 4)
    triggered_rules: list[str] = []
    level = _level_from_score(score)
    if level in {RiskLevel.red.value, RiskLevel.orange.value, RiskLevel.yellow.value}:
        triggered_rules.append(f'风险等级达到 {level}')
    if people_count >= settings.alert_group_people_threshold:
        triggered_rules.append('触发群体性欠薪预警条件')
    if repeat_defendant_rate >= 0.6:
        triggered_rules.append('触发高频欠薪主体预警条件')
    if growth_rate >= 0.3:
        triggered_rules.append('近期增长趋势显著')

    return RiskScoreResponse(score=score, level=level, details=details, triggered_rules=triggered_rules)
