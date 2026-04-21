from __future__ import annotations

from datetime import date

from app.common.enums import RiskLevel, ScopeType
from app.modules.alert.rules import AggregatedRiskStats, build_trigger_rules, calculate_risk_score
from app.modules.alert.schemas import RiskWeightProfile


def make_stats(**overrides):
    payload = {
        'scope_type': ScopeType.community.value,
        'scope_id': 'c-a',
        'scope_name': '新街口社区',
        'community_id': 'c-a',
        'community_name': '新街口社区',
        'street_id': 's-a',
        'street_name': '新街口街道',
        'risk_type': 'wage_arrears',
        'window_start': date(2026, 4, 1),
        'window_end': date(2026, 4, 30),
        'case_count': 8,
        'total_amount': 120000.0,
        'people_count': 12,
        'growth_rate': 0.6,
        'repeat_defendant_rate': 0.75,
        'repeat_defendant_max_count': 33,
        'top_defendants': ['某建设公司'],
        'top_projects': ['新街口排水改造项目'],
    }
    payload.update(overrides)
    return AggregatedRiskStats(**payload)


def test_calculate_risk_score_reaches_orange_or_red():
    score, level, details = calculate_risk_score(make_stats(), weights=RiskWeightProfile())
    assert score >= 60
    assert level in {RiskLevel.orange.value, RiskLevel.red.value}
    assert len(details) == 5


def test_high_frequency_trigger_is_built():
    alerts = build_trigger_rules(
        make_stats(),
        previous_level=RiskLevel.yellow.value,
        current_level=RiskLevel.orange.value,
        repeat_defendant_threshold=32,
        group_people_threshold=10,
        only_level_upgrade_alert=True,
    )
    codes = {item['alert_code'] for item in alerts}
    assert 'risk_level_upgrade' in codes
    assert 'high_frequency_defendant' in codes


def test_project_group_alert_is_built():
    alerts = build_trigger_rules(
        make_stats(scope_type=ScopeType.project.value, scope_name='新街口排水改造项目'),
        previous_level=RiskLevel.blue.value,
        current_level=RiskLevel.orange.value,
        repeat_defendant_threshold=32,
        group_people_threshold=10,
        only_level_upgrade_alert=True,
    )
    codes = {item['alert_code'] for item in alerts}
    assert 'group_wage_arrears' in codes
