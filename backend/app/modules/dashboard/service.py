from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.common.enums import ScopeType
from app.infra.llm_client import build_llm_client
from app.modules.alert.service import AlertService
from app.modules.alert.schemas import DashboardOverviewResponse
from app.modules.analysis.models import CaseCorpus
from app.modules.propaganda.schemas import PropagandaPushListRequest, PropagandaPushRead
from app.modules.propaganda.service import PropagandaService
from app.modules.recommendation.schemas import GovernanceRecommendationRead, RecommendationListRequest
from app.modules.recommendation.service import RecommendationService
from app.modules.workflow.models import WorkflowTask


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.alert_service = AlertService(db)
        self.recommendation_service = RecommendationService(db)
        self.propaganda_service = PropagandaService(db)

    def overview(self, *, scope_type: str = ScopeType.community.value, limit: int = 10) -> DashboardOverviewResponse:
        return self.alert_service.get_dashboard_overview(scope_type=scope_type, limit=limit)

    def risk_map(self, *, limit: int = 500) -> dict:
        records = list(
            self.db.scalars(
                select(CaseCorpus)
                .where(CaseCorpus.source_type == 'demo_case')
                .order_by(CaseCorpus.occurred_at.desc().nullslast(), CaseCorpus.created_at.desc())
                .limit(limit)
            ).all()
        )
        if not records:
            return {
                'points': [],
                'totals': {'totalCases': 0, 'totalWorkers': 0, 'totalAmount': 0.0, 'monthlyNew': 0},
                'caseDistribution': [],
                'monthlyTrend': [],
                'monthlyLabels': [],
                'alertRows': [],
                'defendantTop': [],
                'supportProgress': [
                    {'label': '风险发现', 'value': 0, 'color': '#38bdf8', 'stage': 'discovered'},
                    {'label': '已预警', 'value': 0, 'color': '#15b8a6', 'stage': 'alerted'},
                    {'label': '已分派', 'value': 0, 'color': '#a78bfa', 'stage': 'assigned'},
                    {'label': '处置中', 'value': 0, 'color': '#3b82f6', 'stage': 'handling'},
                    {'label': '已反馈', 'value': 0, 'color': '#f97316', 'stage': 'feedback'},
                    {'label': '已评估', 'value': 0, 'color': '#22c55e', 'stage': 'evaluated'},
                ],
            }

        grouped: dict[str, dict] = {}
        case_type_counter: Counter[str] = Counter()
        defendant_counter: Counter[str] = Counter()
        defendant_amount: defaultdict[str, float] = defaultdict(float)
        month_keys = self._case_month_keys(records)
        monthly_counter = {key: 0 for key in month_keys}
        alert_rows = []
        support_count = 0
        total_cases = 0
        total_workers = 0
        total_amount_yuan = 0.0
        current_month = date.today().month
        current_year = date.today().year
        monthly_new = 0
        workflow_stage_counts: Counter[str] = Counter()

        for record in records:
            extra = record.extra_meta or {}
            entities = record.entities or {}
            street = self._safe_str(extra.get('street_name')) or self._safe_str(extra.get('street')) or '未标注街道'
            lng = self._safe_float(extra.get('longitude'), default=116.365)
            lat = self._safe_float(extra.get('latitude'), default=39.91)
            amount_yuan = self._safe_float(extra.get('total_amount'), default=0.0)
            if amount_yuan <= 0:
                amount_yuan = self._safe_float(extra.get('amount'), default=0.0)
            if amount_yuan <= 0:
                amount_yuan = self._safe_float(entities.get('amount_total_estimate'), default=0.0)
            people_count = self._safe_int(extra.get('people_count'), default=1)
            risk_level = self._normalize_level(extra.get('risk_level'))
            status = self._safe_str(extra.get('status')) or '已接入'
            case_date = record.occurred_at

            total_cases += 1
            total_workers += people_count
            total_amount_yuan += amount_yuan
            case_type_counter[record.case_type or '其他'] += 1
            if case_date:
                month_key = f'{case_date.year}-{case_date.month:02d}'
                if month_key in monthly_counter:
                    monthly_counter[month_key] += 1
                if case_date.year == current_year and case_date.month == current_month:
                    monthly_new += 1

            defendants = self._extract_companies(record)
            for defendant in defendants:
                defendant_counter[defendant] += 1
                defendant_amount[defendant] += amount_yuan

            workflow_stage_counts[self._resolve_workflow_stage(record)] += 1
            if extra.get('support_prosecution_candidate'):
                support_count += 1

            bucket = grouped.setdefault(
                street,
                {
                    'id': f'xicheng-{street}',
                    'name': street,
                    'type': '街道',
                    'lng_sum': 0.0,
                    'lat_sum': 0.0,
                    'location_count': 0,
                    'level': 'blue',
                    'caseCount': 0,
                    'workers': 0,
                    'amount_yuan': 0.0,
                    'owners': Counter(),
                    'status_counter': Counter(),
                },
            )
            bucket['lng_sum'] += lng
            bucket['lat_sum'] += lat
            bucket['location_count'] += 1
            bucket['level'] = self._max_level(bucket['level'], risk_level)
            bucket['caseCount'] += 1
            bucket['workers'] += people_count
            bucket['amount_yuan'] += amount_yuan
            for defendant in defendants:
                bucket['owners'][defendant] += 1
            bucket['status_counter'][status] += 1

            warning_features = extra.get('warning_features') or []
            if warning_features or risk_level in {'red', 'orange'}:
                case_type = record.case_type or '其他'
                assignment = self._suggested_assignment_for_case_type(case_type)
                alert_rows.append(
                    {
                        'id': record.case_no or record.source_ref or record.id,
                        'time': self._format_time(record.created_at),
                        'title': record.title,
                        'level': risk_level,
                        'scope': street,
                        'caseType': case_type,
                        'suggestedUnit': assignment['unit'],
                        'suggestedActions': assignment['actions'],
                    }
                )

        points = []
        for bucket in grouped.values():
            location_count = max(1, bucket.pop('location_count'))
            owners: Counter = bucket.pop('owners')
            status_counter: Counter = bucket.pop('status_counter')
            amount_wan = round(bucket.pop('amount_yuan') / 10000, 1)
            lng = round(bucket.pop('lng_sum') / location_count, 6)
            lat = round(bucket.pop('lat_sum') / location_count, 6)
            points.append(
                {
                    **bucket,
                    'lng': lng,
                    'lat': lat,
                    'amount': amount_wan,
                    'owner': owners.most_common(1)[0][0] if owners else '暂无高频主体',
                    'status': status_counter.most_common(1)[0][0] if status_counter else '已接入',
                }
            )
        points.sort(key=lambda item: (self._level_rank(item['level']), item['caseCount']), reverse=True)

        distribution_colors = ['#2dd4bf', '#a78bfa', '#34d399', '#f472b6', '#94a3b8', '#c084fc', '#67e8f9', '#bef264', '#fb7185']
        case_distribution = []
        for index, (label, value) in enumerate(case_type_counter.most_common()):
            case_distribution.append(
                {
                    'label': label,
                    'value': round(value / max(1, total_cases) * 100, 1),
                    'count': value,
                    'color': distribution_colors[index % len(distribution_colors)],
                }
            )

        defendant_top = [
            {'name': name, 'count': count, 'amount': round(defendant_amount[name] / 10000, 1)}
            for name, count in defendant_counter.most_common(5)
        ]

        task_stage_counts = self._workflow_task_stage_counts()
        support_progress = [
            {'label': '风险发现', 'value': workflow_stage_counts['discovered'], 'color': '#38bdf8', 'stage': 'discovered'},
            {'label': '已预警', 'value': workflow_stage_counts['alerted'], 'color': '#15b8a6', 'stage': 'alerted'},
            {'label': '已分派', 'value': task_stage_counts['assigned'], 'color': '#a78bfa', 'stage': 'assigned'},
            {'label': '处置中', 'value': task_stage_counts['handling'], 'color': '#3b82f6', 'stage': 'handling'},
            {'label': '已反馈', 'value': task_stage_counts['feedback'], 'color': '#f97316', 'stage': 'feedback'},
            {'label': '已评估', 'value': task_stage_counts['evaluated'], 'color': '#22c55e', 'stage': 'evaluated'},
        ]

        return {
            'points': points,
            'totals': {
                'totalCases': total_cases,
                'totalWorkers': total_workers,
                'totalAmount': round(total_amount_yuan / 10000, 1),
                'monthlyNew': monthly_new,
            },
            'caseDistribution': case_distribution,
            'monthlyTrend': [monthly_counter[key] for key in month_keys],
            'monthlyLabels': [self._format_month_label(key) for key in month_keys],
            'alertRows': alert_rows[:20],
            'defendantTop': defendant_top,
            'supportProgress': support_progress,
        }

    def workflow_cases(self, *, stage: str | None = None, limit: int = 200) -> dict:
        records = list(
            self.db.scalars(
                select(CaseCorpus)
                .where(CaseCorpus.source_type == 'demo_case')
                .order_by(CaseCorpus.occurred_at.desc().nullslast(), CaseCorpus.created_at.desc())
                .limit(limit)
            ).all()
        )
        stage_options = [
            {'key': 'discovered', 'label': '风险发现'},
            {'key': 'alerted', 'label': '已预警'},
            {'key': 'assigned', 'label': '已分派'},
            {'key': 'handling', 'label': '处置中'},
            {'key': 'feedback', 'label': '已反馈'},
            {'key': 'evaluated', 'label': '已评估'},
        ]
        stage_key = stage if stage in {item['key'] for item in stage_options} else 'discovered'
        items = []
        stage_counts: Counter[str] = Counter()

        for record in records:
            item_stage = self._resolve_workflow_stage(record)
            stage_counts[item_stage] += 1
            if item_stage != stage_key:
                continue
            items.append(self._build_case_list_item(record))

        return {
            'stage': stage_key,
            'stageLabel': next(item['label'] for item in stage_options if item['key'] == stage_key),
            'stageOptions': [
                {**item, 'count': stage_counts[item['key']]} for item in stage_options
            ],
            'items': items,
        }

    def defendant_cases(self, *, defendant: str, limit: int = 200) -> dict:
        defendant_name = self._safe_str(defendant)
        records = list(
            self.db.scalars(
                select(CaseCorpus)
                .where(CaseCorpus.source_type == 'demo_case')
                .order_by(CaseCorpus.occurred_at.desc().nullslast(), CaseCorpus.created_at.desc())
                .limit(limit)
            ).all()
        )
        items = []
        total_amount = 0.0
        risk_counter: Counter[str] = Counter()

        for record in records:
            defendants = self._extract_companies(record)
            if defendant_name and defendant_name not in defendants:
                continue
            item = self._build_case_list_item(record)
            items.append(item)
            total_amount += item['amount']
            risk_counter[item['riskLevel']] += 1

        return {
            'defendant': defendant_name,
            'totalCases': len(items),
            'totalAmount': round(total_amount, 1),
            'riskSummary': dict(risk_counter),
            'items': items,
        }

    def community_streets(self, *, limit: int = 500) -> dict:
        records = self._load_demo_records(limit=limit)
        grouped: dict[str, dict] = {}

        for record in records:
            extra = record.extra_meta or {}
            street = self._street_name(record)
            amount_yuan = self._amount_yuan(record)
            risk_level = self._normalize_level(extra.get('risk_level'))
            people_count = self._safe_int(extra.get('people_count'), default=1)
            case_type = record.case_type or '其他'

            bucket = grouped.setdefault(
                street,
                {
                    'key': street,
                    'name': street,
                    'region': '北京市西城区',
                    'caseCount': 0,
                    'peopleCount': 0,
                    'totalAmountYuan': 0.0,
                    'riskLevel': 'blue',
                    'highRiskCount': 0,
                    'caseTypes': Counter(),
                },
            )
            bucket['caseCount'] += 1
            bucket['peopleCount'] += people_count
            bucket['totalAmountYuan'] += amount_yuan
            bucket['riskLevel'] = self._max_level(bucket['riskLevel'], risk_level)
            bucket['caseTypes'][case_type] += 1
            if risk_level in {'red', 'orange'}:
                bucket['highRiskCount'] += 1

        streets = []
        for bucket in grouped.values():
            case_types: Counter = bucket.pop('caseTypes')
            top_case_type = case_types.most_common(1)[0][0] if case_types else '暂无'
            streets.append(
                {
                    **bucket,
                    'topCaseType': top_case_type,
                    'totalAmount': round(bucket.pop('totalAmountYuan') / 10000, 1),
                    'tags': [item[0] for item in case_types.most_common(3)],
                }
            )

        streets.sort(key=lambda item: (self._level_rank(item['riskLevel']), item['caseCount']), reverse=True)
        return {
            'region': '北京市西城区',
            'totalStreets': len(streets),
            'items': streets,
        }

    def street_cases(self, *, street: str, limit: int = 500) -> dict:
        street_name = self._safe_str(street)
        records = [
            record
            for record in self._load_demo_records(limit=limit)
            if not street_name or self._street_name(record) == street_name
        ]
        items = [self._build_case_list_item(record) for record in records]
        risk_counter: Counter[str] = Counter(item['riskLevel'] for item in items)
        total_amount = round(sum(item['amount'] for item in items), 1)

        return {
            'street': street_name,
            'totalCases': len(items),
            'totalAmount': total_amount,
            'riskSummary': dict(risk_counter),
            'items': items,
        }

    def street_profile(self, *, street: str, prefer_llm: bool = True, limit: int = 500) -> dict:
        street_name = self._safe_str(street)
        records = [
            record
            for record in self._load_demo_records(limit=limit)
            if not street_name or self._street_name(record) == street_name
        ]
        base_profile = self._build_street_profile_payload(street_name, records)
        llm_result = self._generate_street_profile_with_llm(base_profile) if prefer_llm else {}
        if llm_result:
            base_profile.update(llm_result)
            base_profile['sourceMode'] = 'llm'
        return base_profile

    def latest_recommendations(self, *, limit: int = 10) -> list[GovernanceRecommendationRead]:
        items = self.recommendation_service.list_recommendations(RecommendationListRequest(limit=limit))
        return items.items

    def latest_propaganda(self, *, limit: int = 10) -> list[PropagandaPushRead]:
        items = self.propaganda_service.list_pushes(PropagandaPushListRequest(limit=limit))
        return items.items

    def _safe_str(self, value) -> str:
        return str(value).strip() if value is not None else ''

    def _safe_int(self, value, *, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _safe_float(self, value, *, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _normalize_level(self, value) -> str:
        level = self._safe_str(value)
        return level if level in {'red', 'orange', 'yellow', 'blue'} else 'blue'

    def _level_rank(self, value: str) -> int:
        return {'blue': 1, 'yellow': 2, 'orange': 3, 'red': 4}.get(value, 0)

    def _max_level(self, left: str, right: str) -> str:
        return left if self._level_rank(left) >= self._level_rank(right) else right

    def _extract_companies(self, record: CaseCorpus) -> list[str]:
        extra = record.extra_meta or {}
        if isinstance(extra.get('defendant_names'), list):
            return [str(item) for item in extra['defendant_names'] if item]
        entities = record.entities or {}
        companies = entities.get('companies') or []
        return [str(item) for item in companies if item]

    def _format_time(self, value: datetime | None) -> str:
        if not value:
            return '--:--'
        return value.strftime('%H:%M')

    def _resolve_workflow_stage(self, record: CaseCorpus) -> str:
        extra = record.extra_meta or {}
        status = self._safe_str(extra.get('status'))
        if status in {'待审查', '已受理'}:
            return 'discovered'
        if status == '补充材料':
            return 'alerted'
        if status == '已转入支持起诉评估':
            return 'assigned'
        if status == '调解中':
            return 'handling'
        if status == '联合核查中':
            return 'feedback'
        if status == '拟制发检察建议':
            return 'evaluated'
        if extra.get('warning_features') or self._normalize_level(extra.get('risk_level')) in {'red', 'orange'}:
            return 'alerted'
        return 'discovered'

    def _extract_list_from_meta(self, extra: dict, key: str) -> list[str]:
        value = extra.get(key)
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return []

    def _workflow_task_stage_counts(self) -> Counter[str]:
        counter: Counter[str] = Counter()
        try:
            tasks = self.db.scalars(select(WorkflowTask)).all()
        except SQLAlchemyError:
            return counter
        for task in tasks:
            counter[task.stage] += 1
        return counter

    def _load_demo_records(self, *, limit: int = 500) -> list[CaseCorpus]:
        return list(
            self.db.scalars(
                select(CaseCorpus)
                .where(CaseCorpus.source_type == 'demo_case')
                .order_by(CaseCorpus.occurred_at.desc().nullslast(), CaseCorpus.created_at.desc())
                .limit(limit)
            ).all()
        )

    def _street_name(self, record: CaseCorpus) -> str:
        extra = record.extra_meta or {}
        return self._safe_str(extra.get('street_name')) or self._safe_str(extra.get('street')) or '未标注街道'

    def _amount_yuan(self, record: CaseCorpus) -> float:
        extra = record.extra_meta or {}
        entities = record.entities or {}
        amount = self._safe_float(extra.get('total_amount'), default=0.0)
        if amount <= 0:
            amount = self._safe_float(extra.get('amount'), default=0.0)
        if amount <= 0:
            amount = self._safe_float(entities.get('amount_total_estimate'), default=0.0)
        return amount

    def _build_street_profile_payload(self, street: str, records: list[CaseCorpus]) -> dict:
        case_type_counter: Counter[str] = Counter()
        risk_counter: Counter[str] = Counter()
        defendant_counter: Counter[str] = Counter()
        total_people = 0
        total_amount_yuan = 0.0
        max_level = 'blue'

        for record in records:
            extra = record.extra_meta or {}
            case_type = record.case_type or '其他'
            risk_level = self._normalize_level(extra.get('risk_level'))
            case_type_counter[case_type] += 1
            risk_counter[risk_level] += 1
            max_level = self._max_level(max_level, risk_level)
            total_people += self._safe_int(extra.get('people_count'), default=1)
            total_amount_yuan += self._amount_yuan(record)
            for defendant in self._extract_companies(record):
                defendant_counter[defendant] += 1

        total_cases = len(records)
        high_frequency_types = [
            {
                'caseType': case_type,
                'count': count,
                'ratio': round(count / max(1, total_cases) * 100, 1),
            }
            for case_type, count in case_type_counter.most_common(5)
        ]
        dimensions = self._build_risk_dimensions(high_frequency_types)
        suggestions = self._build_governance_suggestions(high_frequency_types)
        propaganda_plans = self._build_propaganda_plans(high_frequency_types)
        top_types_text = '、'.join(item['caseType'] for item in high_frequency_types[:3]) or '暂无高发类型'

        return {
            'street': street,
            'sourceMode': 'rule',
            'profile': {
                'summary': f'{street}当前共接入{total_cases}件社区法治风险线索，高发类型集中在{top_types_text}，综合风险等级为{self._risk_level_text(max_level)}。',
                'riskLevel': max_level,
                'totalCases': total_cases,
                'peopleCount': total_people,
                'totalAmount': round(total_amount_yuan / 10000, 1),
                'highFrequencyTypes': high_frequency_types,
                'riskDistribution': dict(risk_counter),
                'topDefendants': [
                    {'name': name, 'count': count}
                    for name, count in defendant_counter.most_common(5)
                ],
                'dimensions': dimensions,
            },
            'governanceSuggestions': suggestions,
            'propagandaPlans': propaganda_plans,
        }

    def _generate_street_profile_with_llm(self, profile_payload: dict) -> dict:
        client = build_llm_client()
        if client.is_echo:
            return {}

        prompt = json.dumps(
            {
                'task': '基于街道案件聚合结果生成社区法治风险画像、治理建议和精准普法方案。',
                'requirements': [
                    '识别高发案件类型和主要风险成因。',
                    '输出可执行的街道治理建议，兼顾检察监督、街道治理、行业主管部门联动。',
                    '输出面向重点人群的普法方案，包含主题、对象、内容和投放渠道。',
                    '只返回 JSON，不要返回 Markdown。',
                ],
                'input': profile_payload,
                'output_schema': {
                    'profile': {
                        'summary': 'string',
                        'dimensions': [{'name': 'string', 'level': 'red|orange|yellow|blue', 'description': 'string'}],
                    },
                    'governanceSuggestions': [
                        {'title': 'string', 'summary': 'string', 'actions': ['string'], 'relatedPolicies': ['string']}
                    ],
                    'propagandaPlans': [
                        {'title': 'string', 'targetAudience': 'string', 'content': 'string', 'channels': ['string'], 'relatedLaws': ['string']}
                    ],
                },
            },
            ensure_ascii=False,
        )
        raw = client.complete_json(
            prompt=prompt,
            system_prompt='你是社区法治风险治理助手，熟悉检察监督、基层治理、精准普法和法律知识图谱应用。',
        )
        if not isinstance(raw, dict):
            return {}
        result: dict = {}
        if isinstance(raw.get('profile'), dict):
            merged_profile = {**profile_payload.get('profile', {}), **raw['profile']}
            result['profile'] = merged_profile
        if isinstance(raw.get('governanceSuggestions'), list):
            result['governanceSuggestions'] = raw['governanceSuggestions']
        if isinstance(raw.get('propagandaPlans'), list):
            result['propagandaPlans'] = raw['propagandaPlans']
        return result

    def _build_risk_dimensions(self, high_frequency_types: list[dict]) -> list[dict]:
        dimensions = []
        for item in high_frequency_types[:4]:
            case_type = item['caseType']
            level = 'orange' if item['ratio'] >= 20 else 'yellow'
            dimensions.append(
                {
                    'name': case_type,
                    'level': level,
                    'description': self._case_type_description(case_type),
                }
            )
        return dimensions

    def _build_governance_suggestions(self, high_frequency_types: list[dict]) -> list[dict]:
        suggestions = []
        for item in high_frequency_types[:4]:
            case_type = item['caseType']
            template = self._case_type_template(case_type)
            suggestions.append(
                {
                    'title': f'{case_type}专项治理建议',
                    'summary': template['governance'],
                    'actions': template['actions'],
                    'relatedPolicies': template['policies'],
                }
            )
        return suggestions

    def _build_propaganda_plans(self, high_frequency_types: list[dict]) -> list[dict]:
        plans = []
        for item in high_frequency_types[:4]:
            case_type = item['caseType']
            template = self._case_type_template(case_type)
            plans.append(
                {
                    'title': f'{case_type}精准普法方案',
                    'targetAudience': template['audience'],
                    'content': template['propaganda'],
                    'channels': template['channels'],
                    'relatedLaws': template['laws'],
                }
            )
        return plans

    def _case_type_template(self, case_type: str) -> dict:
        templates = {
            '邻里纠纷': {
                'governance': '建立社区调解、网格走访、司法所释法联动机制，对反复投诉楼栋和重点小区提前介入。',
                'actions': ['梳理重复投诉点位', '组织人民调解员入户释法', '推动物业和居委会建立议事台账'],
                'policies': ['矛盾纠纷多元化解机制', '基层社会治理网格化工作规范'],
                'audience': '社区居民、物业服务人员、网格员',
                'propaganda': '围绕相邻关系、噪声扰民、公共空间占用、证据留存开展案例式普法。',
                'channels': ['社区公告栏', '业主微信群', '网格员入户', '社区法治讲堂'],
                'laws': ['民法典物权编', '民法典侵权责任编', '人民调解法'],
            },
            '合同诈骗': {
                'governance': '聚焦预付费、加盟、装修、培训等高风险交易场景，开展线索核查和市场主体风险提示。',
                'actions': ['建立异常主体名单', '联动市场监管核验经营资质', '发布合同签订风险提示'],
                'policies': ['打击治理电信网络诈骗和涉众型经济风险工作要求', '市场主体信用监管制度'],
                'audience': '老年人、个体商户、求职人员、预付费消费者',
                'propaganda': '提示虚假承诺、格式合同、预付费跑路、证据保存和报案路径。',
                'channels': ['短视频号', '社区电子屏', '商圈巡回宣讲', '反诈宣传群'],
                'laws': ['刑法诈骗罪相关规定', '民法典合同编', '消费者权益保护法'],
            },
            '劳动争议': {
                'governance': '针对欠薪、未签劳动合同、社保缴纳争议，推动人社、街道、工会和检察机关信息联动。',
                'actions': ['排查重点用工单位', '建立欠薪线索快转机制', '对困难劳动者评估支持起诉条件'],
                'policies': ['保障农民工工资支付条例', '根治欠薪冬季专项行动要求'],
                'audience': '劳动者、灵活就业人员、用工单位负责人',
                'propaganda': '讲清劳动合同、工资支付、社保缴纳、工伤认定和维权证据清单。',
                'channels': ['工地宣讲', '企业合规提示函', '劳动者服务站', '公众号推文'],
                'laws': ['劳动合同法', '劳动争议调解仲裁法', '保障农民工工资支付条例'],
            },
            '物业纠纷': {
                'governance': '围绕物业收费、公共收益、维修基金和服务质量，推动小区议事协商和信息公开。',
                'actions': ['建立物业纠纷清单', '推动公共收益公开', '指导业委会依法履职'],
                'policies': ['物业管理条例', '北京市物业管理相关规定'],
                'audience': '业主、业委会成员、物业服务企业',
                'propaganda': '解释物业服务合同、公共收益、维修基金使用、业主大会程序。',
                'channels': ['小区议事会', '楼门微信群', '物业服务大厅', '社区公开栏'],
                'laws': ['民法典合同编', '物业管理条例', '北京市物业管理条例'],
            },
            '婚姻家庭纠纷': {
                'governance': '联合妇联、民政、司法所和社区网格，对家事矛盾、赡养抚养、特殊群体保护开展分级干预。',
                'actions': ['识别困难家庭和弱势群体', '开展家事调解和心理疏导', '对侵害线索依法移送监督'],
                'policies': ['家事纠纷多元化解机制', '妇女儿童权益保障工作要求'],
                'audience': '家庭成员、老年人、妇女儿童、社区工作人员',
                'propaganda': '围绕赡养、抚养、监护、反家庭暴力和救助渠道进行精准提示。',
                'channels': ['妇女之家', '社区课堂', '民政服务窗口', '网格员走访'],
                'laws': ['民法典婚姻家庭编', '反家庭暴力法', '妇女权益保障法'],
            },
            '未成年人保护线索': {
                'governance': '联动教育、市场监管、民政和公安，对托管培训、安全管理、监护缺失风险开展闭环核查。',
                'actions': ['核查机构资质', '评估未成年人权益受损情况', '建立强制报告和回访台账'],
                'policies': ['未成年人保护工作协调机制', '校外培训机构治理要求'],
                'audience': '家长、校外培训机构、学校、社区儿童工作者',
                'propaganda': '提示监护责任、机构选择、安全保护、强制报告和救济渠道。',
                'channels': ['家长群', '学校班会', '社区儿童之家', '机构现场提示'],
                'laws': ['未成年人保护法', '家庭教育促进法', '预防未成年人犯罪法'],
            },
        }
        return templates.get(
            case_type,
            {
                'governance': '对高发线索开展清单化管理，形成街道、行业主管部门、检察监督协同处置机制。',
                'actions': ['建立风险线索台账', '明确责任单位和办理期限', '定期复盘高发问题'],
                'policies': ['基层社会治理工作规范', '检察建议跟踪落实机制'],
                'audience': '社区居民、重点行业主体、网格员',
                'propaganda': '围绕常见法律风险、证据留存、依法维权路径开展案例式普法。',
                'channels': ['社区公告栏', '公众号', '网格群', '线下宣讲'],
                'laws': ['民法典', '行政处罚法', '人民调解法'],
            },
        )

    def _suggested_assignment_for_case_type(self, case_type: str) -> dict:
        unit_map = {
            '劳动争议': '街道综治中心、人社所、司法所',
            '工伤赔偿': '街道综治中心、人社所、工会',
            '邻里纠纷': '社区居委会、司法所、人民调解委员会',
            '合同诈骗': '街道综治中心、市场监管所、公安派出所',
            '物业纠纷': '街道城管办、社区居委会、物业主管部门',
            '婚姻家庭纠纷': '妇联、司法所、社区居委会',
            '未成年人保护线索': '街道未保站、教育部门、市场监管所',
            '消费维权': '市场监管所、消费者协会、社区居委会',
            '民间借贷': '司法所、人民调解委员会、社区居委会',
        }
        template = self._case_type_template(case_type)
        return {
            'unit': unit_map.get(case_type, '街道综治中心、司法所、社区居委会'),
            'actions': template.get('actions') or ['建立风险线索台账', '明确责任单位和办理期限', '定期复盘高发问题'],
        }

    def _case_type_description(self, case_type: str) -> str:
        return self._case_type_template(case_type)['governance']

    def _risk_level_text(self, level: str) -> str:
        return {'red': '红色', 'orange': '橙色', 'yellow': '黄色', 'blue': '蓝色'}.get(level, '蓝色')

    def _build_case_list_item(self, record: CaseCorpus) -> dict:
        extra = record.extra_meta or {}
        entities = record.entities or {}
        amount = self._safe_float(extra.get('total_amount'), default=0.0)
        if amount <= 0:
            amount = self._safe_float(extra.get('amount'), default=0.0)
        if amount <= 0:
            amount = self._safe_float(entities.get('amount_total_estimate'), default=0.0)
        return {
            'id': record.case_no or record.source_ref or record.id,
            'title': record.title,
            'caseType': record.case_type or '其他',
            'street': self._safe_str(extra.get('street_name')) or self._safe_str(extra.get('street')) or '未标注街道',
            'riskLevel': self._normalize_level(extra.get('risk_level')),
            'riskScore': self._safe_float(extra.get('risk_score'), default=0.0),
            'status': self._safe_str(extra.get('status')) or '已接入',
            'amount': round(amount / 10000, 1),
            'peopleCount': self._safe_int(extra.get('people_count'), default=1),
            'occurredAt': record.occurred_at.isoformat() if record.occurred_at else None,
            'claimants': (entities.get('persons') or [])[:5],
            'defendants': self._extract_companies(record)[:5],
            'summary': record.fact_summary or record.claim_summary or record.full_text[:180],
            'tags': extra.get('tags') or [],
            'evidence': self._extract_list_from_meta(extra, 'evidence'),
            'warningFeatures': extra.get('warning_features') or [],
            'recommendedActions': extra.get('recommended_actions') or [],
            'propagandaTopics': extra.get('propaganda_topics') or [],
            'stage': self._resolve_workflow_stage(record),
        }

    def _case_month_keys(self, records: list[CaseCorpus]) -> list[str]:
        month_dates = sorted(
            {date(record.occurred_at.year, record.occurred_at.month, 1) for record in records if record.occurred_at}
        )
        if month_dates:
            start = month_dates[0]
            end = month_dates[-1]
            keys = []
            cursor = start
            while cursor <= end:
                keys.append(f'{cursor.year}-{cursor.month:02d}')
                year = cursor.year + (1 if cursor.month == 12 else 0)
                month = 1 if cursor.month == 12 else cursor.month + 1
                cursor = date(year, month, 1)
            return keys

        today = date.today()
        count = 9
        keys = []
        for offset in range(count - 1, -1, -1):
            month_index = today.month - offset
            year = today.year
            while month_index <= 0:
                month_index += 12
                year -= 1
            keys.append(f'{year}-{month_index:02d}')
        return keys

    def _format_month_label(self, key: str) -> str:
        try:
            _, month = key.split('-', 1)
            return f'{int(month)}月'
        except (ValueError, TypeError):
            return key
