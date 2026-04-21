from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from app.common.enums import RiskLevel, ScopeType
from app.core.config import settings
from app.modules.alert.schemas import RiskMetricScore, RiskWeightProfile


@dataclass
class CaseRiskSignal:
    case_id: str
    title: str
    risk_type: str
    case_type: str
    event_date: date
    community_id: str | None
    community_name: str | None
    street_id: str | None
    street_name: str | None
    project_id: str | None
    project_name: str | None
    people_count: int = 1
    total_amount: float = 0.0
    defendant_names: list[str] = field(default_factory=list)


@dataclass
class AggregatedRiskStats:
    scope_type: str
    scope_id: str
    scope_name: str
    community_id: str | None
    community_name: str | None
    street_id: str | None
    street_name: str | None
    risk_type: str
    window_start: date
    window_end: date
    case_count: int
    total_amount: float
    people_count: int
    growth_rate: float
    repeat_defendant_rate: float
    repeat_defendant_max_count: int
    top_defendants: list[str] = field(default_factory=list)
    top_projects: list[str] = field(default_factory=list)


def default_weight_profile() -> RiskWeightProfile:
    return RiskWeightProfile(
        case_count=settings.risk_weight_case_count,
        people_count=settings.risk_weight_people_count,
        growth_rate=settings.risk_weight_trend,
        repeat_defendant_rate=settings.risk_weight_repeat_defendant,
        total_amount=settings.risk_weight_total_amount,
    ).normalized()


def level_rank(level: str) -> int:
    order = {
        RiskLevel.blue.value: 0,
        RiskLevel.yellow.value: 1,
        RiskLevel.orange.value: 2,
        RiskLevel.red.value: 3,
    }
    return order.get(level, 0)


def max_level(level_a: str, level_b: str) -> str:
    return level_a if level_rank(level_a) >= level_rank(level_b) else level_b


def score_case_count(case_count: int) -> tuple[float, str]:
    if case_count <= 0:
        return 0.0, '近30天无案件'
    if case_count <= 2:
        return 20.0, '案件量较低（1-2件）'
    if case_count <= 5:
        return 40.0, '案件量开始聚集（3-5件）'
    if case_count <= 10:
        return 70.0, '案件量较高（6-10件）'
    return 100.0, '案件量高发（>10件）'


def score_people_count(people_count: int) -> tuple[float, str]:
    if people_count <= 0:
        return 0.0, '未记录涉及人数'
    if people_count == 1:
        return 10.0, '单人事件'
    if people_count <= 4:
        return 30.0, '少量多人事件（2-4人）'
    if people_count <= 9:
        return 60.0, '多人事件（5-9人）'
    if people_count <= 19:
        return 80.0, '群体性倾向明显（10-19人）'
    return 100.0, '群体性风险高（>=20人）'


def score_growth_rate(growth_rate: float) -> tuple[float, str]:
    if growth_rate <= 0:
        return 10.0, '较上一周期未增长或下降'
    if growth_rate <= 0.2:
        return 30.0, '轻度增长（0-20%）'
    if growth_rate <= 0.5:
        return 60.0, '中度增长（20%-50%）'
    if growth_rate <= 1.0:
        return 80.0, '显著增长（50%-100%）'
    return 100.0, '爆发式增长（>100%）'


def score_repeat_defendant_rate(repeat_defendant_rate: float) -> tuple[float, str]:
    if repeat_defendant_rate <= 0:
        return 0.0, '未出现重复被告'
    if repeat_defendant_rate <= 0.2:
        return 20.0, '重复主体占比较低（<=20%）'
    if repeat_defendant_rate <= 0.4:
        return 40.0, '重复主体占比上升（20%-40%）'
    if repeat_defendant_rate <= 0.6:
        return 70.0, '重复主体集中（40%-60%）'
    return 100.0, '高频主体显著集中（>60%）'


def score_total_amount(total_amount: float) -> tuple[float, str]:
    if total_amount <= 0:
        return 0.0, '未记录金额'
    if total_amount <= 10_000:
        return 20.0, '涉案金额较低（<=1万元）'
    if total_amount <= 50_000:
        return 40.0, '涉案金额中等（1-5万元）'
    if total_amount <= 200_000:
        return 70.0, '涉案金额较高（5-20万元）'
    return 100.0, '涉案金额高（>20万元）'


def aggregate_stats(
    signals: list[CaseRiskSignal],
    previous_signals: list[CaseRiskSignal],
    *,
    scope_type: str,
    scope_id: str,
    scope_name: str,
    community_id: str | None,
    community_name: str | None,
    street_id: str | None,
    street_name: str | None,
    risk_type: str,
    window_start: date,
    window_end: date,
) -> AggregatedRiskStats:
    case_count = len(signals)
    total_amount = round(sum(max(0.0, signal.total_amount) for signal in signals), 2)
    people_count = int(sum(max(0, signal.people_count) for signal in signals))
    prev_count = len(previous_signals)
    growth_rate = 0.0
    if case_count > 0:
        growth_rate = (case_count - prev_count) / max(prev_count, 1)
    defendant_counter: Counter[str] = Counter()
    project_counter: Counter[str] = Counter()
    for signal in signals:
        for name in signal.defendant_names:
            if name:
                defendant_counter[name] += 1
        if signal.project_name:
            project_counter[signal.project_name] += 1
    repeat_defendant_max_count = max(defendant_counter.values()) if defendant_counter else 0
    repeat_defendant_rate = round(repeat_defendant_max_count / max(case_count, 1), 6) if case_count else 0.0
    return AggregatedRiskStats(
        scope_type=scope_type,
        scope_id=scope_id,
        scope_name=scope_name,
        community_id=community_id,
        community_name=community_name,
        street_id=street_id,
        street_name=street_name,
        risk_type=risk_type,
        window_start=window_start,
        window_end=window_end,
        case_count=case_count,
        total_amount=total_amount,
        people_count=people_count,
        growth_rate=round(growth_rate, 6),
        repeat_defendant_rate=repeat_defendant_rate,
        repeat_defendant_max_count=repeat_defendant_max_count,
        top_defendants=[name for name, _ in defendant_counter.most_common(5)],
        top_projects=[name for name, _ in project_counter.most_common(5)],
    )


def calculate_risk_score(stats: AggregatedRiskStats, weights: RiskWeightProfile | None = None) -> tuple[float, str, list[RiskMetricScore]]:
    weights = (weights or default_weight_profile()).normalized()
    case_bucket, case_desc = score_case_count(stats.case_count)
    people_bucket, people_desc = score_people_count(stats.people_count)
    growth_bucket, growth_desc = score_growth_rate(stats.growth_rate)
    repeat_bucket, repeat_desc = score_repeat_defendant_rate(stats.repeat_defendant_rate)
    amount_bucket, amount_desc = score_total_amount(stats.total_amount)

    metrics = [
        RiskMetricScore(
            metric='case_count',
            raw_value=float(stats.case_count),
            bucket_score=case_bucket,
            weight=weights.case_count,
            weighted_contribution=round(case_bucket * weights.case_count, 6),
            description=case_desc,
        ),
        RiskMetricScore(
            metric='people_count',
            raw_value=float(stats.people_count),
            bucket_score=people_bucket,
            weight=weights.people_count,
            weighted_contribution=round(people_bucket * weights.people_count, 6),
            description=people_desc,
        ),
        RiskMetricScore(
            metric='growth_rate',
            raw_value=float(stats.growth_rate),
            bucket_score=growth_bucket,
            weight=weights.growth_rate,
            weighted_contribution=round(growth_bucket * weights.growth_rate, 6),
            description=growth_desc,
        ),
        RiskMetricScore(
            metric='repeat_defendant_rate',
            raw_value=float(stats.repeat_defendant_rate),
            bucket_score=repeat_bucket,
            weight=weights.repeat_defendant_rate,
            weighted_contribution=round(repeat_bucket * weights.repeat_defendant_rate, 6),
            description=repeat_desc,
        ),
        RiskMetricScore(
            metric='total_amount',
            raw_value=float(stats.total_amount),
            bucket_score=amount_bucket,
            weight=weights.total_amount,
            weighted_contribution=round(amount_bucket * weights.total_amount, 6),
            description=amount_desc,
        ),
    ]
    score = round(sum(item.weighted_contribution for item in metrics), 4)
    level = score_to_level(score)
    return score, level, metrics


def score_to_level(score: float) -> str:
    if score >= settings.risk_red_threshold:
        return RiskLevel.red.value
    if score >= settings.risk_orange_threshold:
        return RiskLevel.orange.value
    if score >= settings.risk_yellow_threshold:
        return RiskLevel.yellow.value
    return RiskLevel.blue.value


def build_trigger_rules(
    stats: AggregatedRiskStats,
    *,
    previous_level: str | None,
    current_level: str,
    repeat_defendant_threshold: int,
    group_people_threshold: int,
    only_level_upgrade_alert: bool,
) -> list[dict]:
    """
    返回 alert 触发明细，每一项包含 code / level / title / reason / scope_*.
    """
    alerts: list[dict] = []

    if current_level != RiskLevel.blue.value:
        is_upgrade = previous_level is None or level_rank(current_level) > level_rank(previous_level)
        if is_upgrade or not only_level_upgrade_alert:
            alerts.append(
                {
                    'alert_code': 'risk_level_upgrade',
                    'alert_level': current_level,
                    'title': f'{stats.scope_name} {stats.risk_type} 风险等级预警',
                    'trigger_reason': (
                        f'{stats.scope_name} 在统计窗口内 {stats.risk_type} 风险评分为 {stats.case_count}件/{stats.people_count}人/'
                        f'{stats.total_amount:.2f}元，综合评分升级为 {current_level}'
                    ),
                }
            )

    if stats.repeat_defendant_max_count >= repeat_defendant_threshold:
        high_freq_level = RiskLevel.red.value if stats.repeat_defendant_max_count >= max(repeat_defendant_threshold * 2, repeat_defendant_threshold + 3) else RiskLevel.orange.value
        alerts.append(
            {
                'alert_code': 'high_frequency_defendant',
                'alert_level': high_freq_level,
                'title': f'{stats.scope_name} 高频风险主体预警',
                'trigger_reason': (
                    f'同一被告/主体近30天重复出现 {stats.repeat_defendant_max_count} 次，超过阈值 {repeat_defendant_threshold} 次；'
                    f'高频主体：{", ".join(stats.top_defendants[:3]) or "未命名主体"}'
                ),
            }
        )

    if stats.scope_type == ScopeType.project.value and stats.people_count >= group_people_threshold:
        group_level = RiskLevel.red.value if stats.people_count >= max(group_people_threshold * 2, 20) else RiskLevel.orange.value
        alerts.append(
            {
                'alert_code': 'group_wage_arrears',
                'alert_level': group_level,
                'title': f'{stats.scope_name} 群体性欠薪预警',
                'trigger_reason': f'该工地/项目近30天涉及人数 {stats.people_count} 人，超过群体性欠薪阈值 {group_people_threshold} 人',
            }
        )

    return alerts
