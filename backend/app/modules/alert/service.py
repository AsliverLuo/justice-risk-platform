from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.common.enums import AlertStatus, RiskLevel, ScopeType
from app.core.config import settings
from app.modules.alert.repository import AlertRepository
from app.modules.alert.rules import (
    CaseRiskSignal,
    aggregate_stats,
    build_trigger_rules,
    calculate_risk_score,
    default_weight_profile,
)
from app.modules.alert.schemas import (
    AlertListRequest,
    AlertListResponse,
    AlertRead,
    CommunityRiskEngineRequest,
    CommunityRiskEngineResponse,
    CommunityRiskProfileRead,
    DashboardOverviewResponse,
    RiskWeightProfile,
)
from app.modules.analysis.models import CaseCorpus


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AlertRepository(db)

    def run_engine(self, payload: CommunityRiskEngineRequest) -> CommunityRiskEngineResponse:
        as_of_date = payload.as_of_date or date.today()
        current_start = as_of_date - timedelta(days=payload.window_days - 1)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=payload.compare_window_days - 1)
        weights = (payload.weights or default_weight_profile()).normalized()
        repeat_threshold = payload.repeat_defendant_threshold or settings.alert_repeat_defendant_threshold_30d
        group_people_threshold = payload.group_people_threshold or settings.alert_group_people_threshold

        all_cases = self.repo.list_all_cases()
        filtered_cases = [
            case for case in all_cases
            if self._case_in_scope(case=case, community_ids=payload.community_ids, risk_types=payload.risk_types)
        ]

        current_cases = [
            case for case in filtered_cases
            if self._event_date(case) is not None and current_start <= self._event_date(case) <= as_of_date
        ]
        previous_cases = [
            case for case in filtered_cases
            if self._event_date(case) is not None and previous_start <= self._event_date(case) <= previous_end
        ]

        current_signals = [self._to_signal(case) for case in current_cases]
        previous_signals = [self._to_signal(case) for case in previous_cases]

        current_groups = self._group_signals(current_signals, scope_type=payload.scope_type)
        previous_groups = self._group_signals(previous_signals, scope_type=payload.scope_type)

        profile_reads: list[CommunityRiskProfileRead] = []
        alert_reads: list[AlertRead] = []

        for group_key, signals in current_groups.items():
            scope_type, scope_id, risk_type = group_key
            if not signals:
                continue
            sample = signals[0]
            prev_signals = previous_groups.get(group_key, [])
            stats = aggregate_stats(
                signals,
                prev_signals,
                scope_type=scope_type,
                scope_id=scope_id,
                scope_name=self._resolve_scope_name(scope_type, sample),
                community_id=sample.community_id,
                community_name=sample.community_name,
                street_id=sample.street_id,
                street_name=sample.street_name,
                risk_type=risk_type,
                window_start=current_start,
                window_end=as_of_date,
            )
            score, level, metric_scores = calculate_risk_score(stats, weights=weights)
            previous_profile = self.repo.get_latest_profile(
                scope_type=scope_type,
                scope_id=scope_id,
                risk_type=risk_type,
                before_date=current_start,
            )
            previous_level = previous_profile.risk_level if previous_profile else None
            triggered_rules = self._build_profile_trigger_reasons(stats=stats, previous_level=previous_level, current_level=level)

            profile_payload = {
                'community_id': stats.community_id,
                'community_name': stats.community_name,
                'street_id': stats.street_id,
                'street_name': stats.street_name,
                'scope_type': stats.scope_type,
                'scope_id': stats.scope_id,
                'scope_name': stats.scope_name,
                'risk_type': stats.risk_type,
                'stat_window_start': current_start,
                'stat_window_end': as_of_date,
                'case_count': stats.case_count,
                'total_amount': stats.total_amount,
                'people_count': stats.people_count,
                'growth_rate': stats.growth_rate,
                'repeat_defendant_rate': stats.repeat_defendant_rate,
                'repeat_defendant_max_count': stats.repeat_defendant_max_count,
                'top_defendants': stats.top_defendants,
                'top_projects': stats.top_projects,
                'metric_scores': [item.model_dump() for item in metric_scores],
                'triggered_rules': triggered_rules,
                'risk_score': score,
                'risk_level': level,
                'previous_risk_level': previous_level,
                'extra_meta': {
                    'used_weights': weights.model_dump(),
                    'window_days': payload.window_days,
                    'compare_window_days': payload.compare_window_days,
                },
            }
            if payload.persist_profiles:
                profile_obj = self.repo.upsert_profile(
                    scope_type=scope_type,
                    scope_id=scope_id,
                    risk_type=risk_type,
                    stat_window_start=current_start,
                    stat_window_end=as_of_date,
                    payload=profile_payload,
                )
                profile_read = CommunityRiskProfileRead.model_validate(profile_obj)
            else:
                profile_read = CommunityRiskProfileRead(
                    id=f'temp:{scope_type}:{scope_id}:{risk_type}',
                    **profile_payload,
                )
            profile_reads.append(profile_read)

            if payload.generate_alerts:
                raw_alerts = build_trigger_rules(
                    stats,
                    previous_level=previous_level,
                    current_level=level,
                    repeat_defendant_threshold=repeat_threshold,
                    group_people_threshold=group_people_threshold,
                    only_level_upgrade_alert=payload.only_level_upgrade_alert,
                )
                for raw_alert in raw_alerts:
                    alert_payload = {
                        'community_id': stats.community_id,
                        'community_name': stats.community_name,
                        'street_id': stats.street_id,
                        'street_name': stats.street_name,
                        'scope_type': stats.scope_type,
                        'scope_id': stats.scope_id,
                        'scope_name': stats.scope_name,
                        'risk_type': stats.risk_type,
                        'alert_code': raw_alert['alert_code'],
                        'alert_level': raw_alert['alert_level'],
                        'title': raw_alert['title'],
                        'trigger_reason': raw_alert['trigger_reason'],
                        'status': AlertStatus.active.value,
                        'profile_id': None if not payload.persist_profiles else profile_read.id,
                        'previous_level': previous_level,
                        'current_level': level,
                        'case_count': stats.case_count,
                        'people_count': stats.people_count,
                        'total_amount': stats.total_amount,
                        'growth_rate': stats.growth_rate,
                        'repeat_defendant_rate': stats.repeat_defendant_rate,
                        'repeat_defendant_max_count': stats.repeat_defendant_max_count,
                        'top_defendants': stats.top_defendants,
                        'dashboard_visible': True,
                        'pushed_at': datetime.utcnow(),
                        'extra_meta': {
                            'top_projects': stats.top_projects,
                            'used_weights': weights.model_dump(),
                        },
                    }
                    if payload.persist_profiles:
                        alert_obj = self.repo.create_alert(alert_payload)
                        alert_reads.append(AlertRead.model_validate(alert_obj))
                    else:
                        alert_reads.append(
                            AlertRead(
                                id=f'temp:{stats.scope_type}:{stats.scope_id}:{raw_alert["alert_code"]}',
                                **alert_payload,
                            )
                        )

        # 项目级群体性欠薪预警：即使主 scope_type 为 community，也额外做一层 project 扫描
        if payload.generate_alerts:
            project_alerts = self._build_project_group_alerts(
                signals=current_signals,
                current_start=current_start,
                as_of_date=as_of_date,
                group_people_threshold=group_people_threshold,
                persist=payload.persist_profiles,
            )
            alert_reads.extend(project_alerts)

        if payload.persist_profiles:
            self.db.commit()
        else:
            self.db.rollback()

        profile_reads.sort(key=lambda item: item.risk_score, reverse=True)
        alert_reads.sort(key=lambda item: (self._level_rank(item.alert_level), item.created_at if hasattr(item, 'created_at') else datetime.utcnow()), reverse=True)
        return CommunityRiskEngineResponse(
            as_of_date=as_of_date,
            scope_type=payload.scope_type,
            profile_count=len(profile_reads),
            alert_count=len(alert_reads),
            profiles=profile_reads,
            alerts=alert_reads,
            used_weights=weights,
        )

    def list_alerts(self, payload: AlertListRequest) -> AlertListResponse:
        records = self.repo.list_alerts(
            limit=payload.limit,
            status=payload.status,
            scope_type=payload.scope_type,
            community_id=payload.community_id,
            risk_type=payload.risk_type,
            dashboard_visible_only=payload.dashboard_visible_only,
        )
        return AlertListResponse(items=[AlertRead.model_validate(item) for item in records])

    def list_profiles(self, *, limit: int = 100, scope_type: str | None = None, community_id: str | None = None) -> list[CommunityRiskProfileRead]:
        records = self.repo.list_profiles(limit=limit, scope_type=scope_type, community_id=community_id)
        return [CommunityRiskProfileRead.model_validate(item) for item in records]

    def get_dashboard_overview(self, *, scope_type: str = ScopeType.community.value, limit: int = 10) -> DashboardOverviewResponse:
        profiles = self.repo.list_latest_profiles_by_scope(scope_type=scope_type, limit=200)
        deduped: dict[tuple[str, str], CommunityRiskProfileRead] = {}
        for item in profiles:
            key = (item.scope_id, item.risk_type)
            if key not in deduped:
                deduped[key] = CommunityRiskProfileRead.model_validate(item)
        latest_profiles = list(deduped.values())
        latest_profiles.sort(key=lambda item: item.risk_score, reverse=True)
        alerts = self.repo.list_alerts(limit=limit, dashboard_visible_only=True)
        return DashboardOverviewResponse(
            as_of_date=date.today(),
            total_profiles=len(latest_profiles),
            total_alerts=len(alerts),
            red_count=sum(1 for item in latest_profiles if item.risk_level == RiskLevel.red.value),
            orange_count=sum(1 for item in latest_profiles if item.risk_level == RiskLevel.orange.value),
            yellow_count=sum(1 for item in latest_profiles if item.risk_level == RiskLevel.yellow.value),
            blue_count=sum(1 for item in latest_profiles if item.risk_level == RiskLevel.blue.value),
            top_risk_communities=latest_profiles[:limit],
            latest_alerts=[AlertRead.model_validate(item) for item in alerts],
        )

    def _case_in_scope(self, *, case: CaseCorpus, community_ids: list[str] | None, risk_types: list[str] | None) -> bool:
        extra = case.extra_meta or {}
        case_community_id = str(extra.get('community_id') or extra.get('community_name') or '').strip()
        case_risk_type = str(extra.get('risk_type') or case.case_type or 'other').strip()
        if community_ids and case_community_id and case_community_id not in set(community_ids):
            return False
        if risk_types and case_risk_type not in set(risk_types):
            return False
        return True

    def _event_date(self, case: CaseCorpus) -> date | None:
        if case.occurred_at:
            return case.occurred_at
        if case.judgment_date:
            return case.judgment_date
        created = getattr(case, 'created_at', None)
        if created:
            return created.date()
        return None

    def _to_signal(self, case: CaseCorpus) -> CaseRiskSignal:
        extra = case.extra_meta or {}
        entities = case.entities or {}
        community_id = self._safe_str(extra.get('community_id')) or self._safe_str(extra.get('community_name'))
        community_name = self._safe_str(extra.get('community_name')) or community_id or '未命名社区'
        street_id = self._safe_str(extra.get('street_id')) or self._safe_str(extra.get('street_name'))
        street_name = self._safe_str(extra.get('street_name')) or street_id or community_name
        project_name = self._safe_str(extra.get('project_name')) or self._safe_str(extra.get('worksite_name'))
        if not project_name:
            projects = entities.get('projects') or []
            project_name = projects[0] if projects else None
        project_id = self._safe_str(extra.get('project_id')) or project_name
        risk_type = self._safe_str(extra.get('risk_type')) or case.case_type or 'other'
        people_count = self._safe_int(extra.get('people_count'), default=1)
        amount = self._safe_float(extra.get('total_amount'), default=0.0)
        if amount <= 0:
            amount = self._safe_float(entities.get('amount_total_estimate'), default=0.0)
        defendant_names = self._extract_defendant_names(case)
        return CaseRiskSignal(
            case_id=case.id,
            title=case.title,
            risk_type=risk_type,
            case_type=case.case_type,
            event_date=self._event_date(case) or date.today(),
            community_id=community_id,
            community_name=community_name,
            street_id=street_id,
            street_name=street_name,
            project_id=project_id,
            project_name=project_name,
            people_count=max(1, people_count),
            total_amount=max(0.0, amount),
            defendant_names=defendant_names,
        )

    def _extract_defendant_names(self, case: CaseCorpus) -> list[str]:
        extra = case.extra_meta or {}
        if isinstance(extra.get('defendant_names'), list):
            return [self._safe_str(item) for item in extra.get('defendant_names', []) if self._safe_str(item)]
        entities = case.entities or {}
        companies = [self._safe_str(item) for item in entities.get('companies', []) if self._safe_str(item)]
        if companies:
            return companies
        raw = case.defendant_summary or ''
        chunks = [part.strip() for part in raw.replace('；', ',').replace('、', ',').split(',')]
        return [part for part in chunks if part][:5]

    def _group_signals(self, signals: list[CaseRiskSignal], *, scope_type: str) -> dict[tuple[str, str, str], list[CaseRiskSignal]]:
        grouped: dict[tuple[str, str, str], list[CaseRiskSignal]] = defaultdict(list)
        normalized_scope = scope_type or ScopeType.community.value
        for signal in signals:
            if normalized_scope == ScopeType.project.value:
                scope_id = signal.project_id or f'project:{signal.community_id or "unknown"}:{signal.project_name or signal.title}'
                scope_name = signal.project_name or '未命名项目'
            elif normalized_scope == ScopeType.street.value:
                scope_id = signal.street_id or signal.street_name or signal.community_id or 'street:unknown'
                scope_name = signal.street_name or signal.community_name or '未命名街道'
            else:
                scope_id = signal.community_id or signal.community_name or 'community:unknown'
                scope_name = signal.community_name or signal.street_name or '未命名社区'
            signal._resolved_scope_name = scope_name  # type: ignore[attr-defined]
            grouped[(normalized_scope, scope_id, signal.risk_type)].append(signal)
        return grouped

    def _resolve_scope_name(self, scope_type: str, sample: CaseRiskSignal) -> str:
        if scope_type == ScopeType.project.value:
            return sample.project_name or '未命名项目'
        if scope_type == ScopeType.street.value:
            return sample.street_name or sample.community_name or '未命名街道'
        return sample.community_name or sample.street_name or '未命名社区'

    def _build_profile_trigger_reasons(self, *, stats, previous_level: str | None, current_level: str) -> list[str]:
        reasons = [
            f'案件数量={stats.case_count}',
            f'涉及人数={stats.people_count}',
            f'近期增长率={stats.growth_rate:.2f}',
            f'重复主体复现率={stats.repeat_defendant_rate:.2f}',
            f'涉案金额={stats.total_amount:.2f}元',
        ]
        if previous_level and current_level != previous_level:
            reasons.append(f'风险等级由 {previous_level} 升级为 {current_level}')
        return reasons

    def _build_project_group_alerts(
        self,
        *,
        signals: list[CaseRiskSignal],
        current_start: date,
        as_of_date: date,
        group_people_threshold: int,
        persist: bool,
    ) -> list[AlertRead]:
        project_groups = self._group_signals(signals, scope_type=ScopeType.project.value)
        outputs: list[AlertRead] = []
        for (scope_type, scope_id, risk_type), group_signals in project_groups.items():
            if not group_signals:
                continue
            sample = group_signals[0]
            stats = aggregate_stats(
                group_signals,
                [],
                scope_type=scope_type,
                scope_id=scope_id,
                scope_name=self._resolve_scope_name(scope_type, sample),
                community_id=sample.community_id,
                community_name=sample.community_name,
                street_id=sample.street_id,
                street_name=sample.street_name,
                risk_type=risk_type,
                window_start=current_start,
                window_end=as_of_date,
            )
            if stats.people_count < group_people_threshold:
                continue
            payload = {
                'community_id': stats.community_id,
                'community_name': stats.community_name,
                'street_id': stats.street_id,
                'street_name': stats.street_name,
                'scope_type': stats.scope_type,
                'scope_id': stats.scope_id,
                'scope_name': stats.scope_name,
                'risk_type': stats.risk_type,
                'alert_code': 'group_wage_arrears',
                'alert_level': RiskLevel.red.value if stats.people_count >= max(group_people_threshold * 2, 20) else RiskLevel.orange.value,
                'title': f'{stats.scope_name} 群体性欠薪预警',
                'trigger_reason': f'该工地/项目近30天涉及人数 {stats.people_count} 人，达到群体性欠薪阈值 {group_people_threshold} 人',
                'status': AlertStatus.active.value,
                'profile_id': None,
                'previous_level': None,
                'current_level': None,
                'case_count': stats.case_count,
                'people_count': stats.people_count,
                'total_amount': stats.total_amount,
                'growth_rate': stats.growth_rate,
                'repeat_defendant_rate': stats.repeat_defendant_rate,
                'repeat_defendant_max_count': stats.repeat_defendant_max_count,
                'top_defendants': stats.top_defendants,
                'dashboard_visible': True,
                'pushed_at': datetime.utcnow(),
                'extra_meta': {'top_projects': stats.top_projects},
            }
            if persist:
                obj = self.repo.create_alert(payload)
                outputs.append(AlertRead.model_validate(obj))
            else:
                outputs.append(AlertRead(id=f'temp:{scope_type}:{scope_id}:group', **payload))
        return outputs

    def _level_rank(self, level: str) -> int:
        return {
            RiskLevel.blue.value: 0,
            RiskLevel.yellow.value: 1,
            RiskLevel.orange.value: 2,
            RiskLevel.red.value: 3,
        }.get(level, 0)

    @staticmethod
    def _safe_str(value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _safe_int(value, default: int = 0) -> int:
        try:
            if value is None or value == '':
                return default
            return int(float(value))
        except Exception:
            return default

    @staticmethod
    def _safe_float(value, default: float = 0.0) -> float:
        try:
            if value is None or value == '':
                return default
            return float(value)
        except Exception:
            return default
