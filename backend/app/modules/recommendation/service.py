from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.infra.llm_client import build_llm_client
from app.modules.knowledge.schemas import KnowledgeSearchRequest
from app.modules.knowledge.service import LegalKnowledgeService
from app.modules.recommendation.repository import RecommendationRepository
from app.modules.recommendation.prompts import RECOMMENDATION_SYSTEM_PROMPT, build_recommendation_prompt
from app.modules.recommendation.schemas import (
    GovernanceRecommendationRead,
    RecommendationCaseSnapshot,
    RecommendationGenerateRequest,
    RecommendationGenerateResponse,
    RecommendationLawReference,
    RecommendationListRequest,
    RecommendationListResponse,
    RecommendationTemplateBatchUpsertRequest,
    RecommendationTemplateListResponse,
    RecommendationTemplateRead,
)

logger = get_logger(__name__)


class RecommendationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RecommendationRepository(db)
        self.knowledge_service = LegalKnowledgeService(db)
        self.llm_client = build_llm_client()

    def batch_upsert_templates(self, payload: RecommendationTemplateBatchUpsertRequest) -> RecommendationTemplateListResponse:
        items = [RecommendationTemplateRead.model_validate(self.repo.upsert_template(item.model_dump())) for item in payload.items]
        self.db.commit()
        return RecommendationTemplateListResponse(items=items)

    def list_templates(self, *, risk_type: str | None = None, alert_code: str | None = None, scope_type: str | None = None, current_level: str | None = None, limit: int = 20) -> RecommendationTemplateListResponse:
        records = self.repo.list_templates(risk_type=risk_type, alert_code=alert_code, scope_type=scope_type, current_level=current_level, limit=limit)
        return RecommendationTemplateListResponse(items=[RecommendationTemplateRead.model_validate(item) for item in records])

    def list_recommendations(self, payload: RecommendationListRequest) -> RecommendationListResponse:
        records = self.repo.list_recommendations(
            limit=payload.limit,
            alert_id=payload.alert_id,
            profile_id=payload.profile_id,
            scope_type=payload.scope_type,
            scope_id=payload.scope_id,
            risk_type=payload.risk_type,
            dashboard_visible_only=payload.dashboard_visible_only,
        )
        return RecommendationListResponse(items=[self._to_recommendation_read(item) for item in records])

    def generate(self, payload: RecommendationGenerateRequest) -> RecommendationGenerateResponse:
        alert = self.repo.get_alert(payload.alert_id) if payload.alert_id else None
        profile = self.repo.get_profile(payload.profile_id) if payload.profile_id else None
        if profile is None and alert and alert.profile_id:
            profile = self.repo.get_profile(alert.profile_id)
        if profile is None and payload.scope_type and payload.scope_id:
            profile = self.repo.get_latest_profile_by_scope(scope_type=payload.scope_type, scope_id=payload.scope_id, risk_type=payload.risk_type)

        resolved_scope_type = (profile.scope_type if profile else None) or (alert.scope_type if alert else None) or payload.scope_type or 'community'
        resolved_scope_id = (profile.scope_id if profile else None) or (alert.scope_id if alert else None) or payload.scope_id or 'unknown-scope'
        resolved_scope_name = (profile.scope_name if profile else None) or (alert.scope_name if alert else None) or resolved_scope_id
        resolved_risk_type = (profile.risk_type if profile else None) or (alert.risk_type if alert else None) or payload.risk_type or 'other'
        current_level = (alert.alert_level if alert else None) or (profile.risk_level if profile else None) or 'yellow'
        alert_code = alert.alert_code if alert else None

        case_snapshots = self._collect_case_snapshots(
            scope_type=resolved_scope_type,
            scope_id=resolved_scope_id,
            risk_type=resolved_risk_type,
            limit=payload.case_limit,
        )
        related_laws = self._retrieve_related_laws(
            resolved_scope_name=resolved_scope_name,
            risk_type=resolved_risk_type,
            alert=alert,
            profile=profile,
            case_snapshots=case_snapshots,
            top_k=payload.law_top_k,
        )
        used_templates = self.repo.list_templates(
            risk_type=resolved_risk_type,
            alert_code=alert_code,
            scope_type=resolved_scope_type,
            current_level=current_level,
            limit=payload.template_limit,
        )

        context = self._build_context(
            payload=payload,
            profile=profile,
            alert=alert,
            scope_type=resolved_scope_type,
            scope_id=resolved_scope_id,
            scope_name=resolved_scope_name,
            risk_type=resolved_risk_type,
            current_level=current_level,
            case_snapshots=case_snapshots,
            related_laws=related_laws,
            used_templates=used_templates,
        )

        result_data: dict[str, Any]
        mode = 'template'
        if payload.prefer_llm and not self.llm_client.is_echo:
            result_data = self._generate_with_llm(context)
            mode = 'llm_hybrid'
        else:
            result_data = self._generate_with_templates(context)

        recommendation_payload = {
            'profile_id': profile.id if profile else payload.profile_id,
            'alert_id': alert.id if alert else payload.alert_id,
            'community_id': getattr(profile, 'community_id', None) or getattr(alert, 'community_id', None),
            'community_name': getattr(profile, 'community_name', None) or getattr(alert, 'community_name', None),
            'street_id': getattr(profile, 'street_id', None) or getattr(alert, 'street_id', None),
            'street_name': getattr(profile, 'street_name', None) or getattr(alert, 'street_name', None),
            'scope_type': resolved_scope_type,
            'scope_id': resolved_scope_id,
            'scope_name': resolved_scope_name,
            'risk_type': resolved_risk_type,
            'recommendation_level': result_data.get('recommendation_level') or self._map_level(current_level),
            'title': result_data.get('title') or self._default_title(resolved_scope_name, resolved_risk_type),
            'summary': result_data.get('summary') or context['profile_summary'],
            'action_items': self._ensure_string_list(result_data.get('action_items')) or self._fallback_actions(context),
            'departments': self._ensure_string_list(result_data.get('departments')) or self._fallback_departments(context),
            'follow_up_metrics': self._ensure_string_list(result_data.get('follow_up_metrics')) or self._fallback_followup_metrics(context),
            'related_laws': [item.model_dump() for item in related_laws],
            'case_snapshots': [item.model_dump() for item in case_snapshots],
            'matched_template_codes': [item.template_code for item in used_templates],
            'source_mode': mode,
            'dashboard_visible': payload.dashboard_visible,
            'status': 'active',
            'extra_meta': {
                'law_reasons': self._ensure_string_list(result_data.get('law_reasons')),
                'used_context_summary': payload.context_summary,
                'alert_code': alert_code,
                'current_level': current_level,
            },
        }

        if payload.persist:
            recommendation = self.repo.upsert_recommendation(recommendation_payload)
            self.db.commit()
            recommendation_read = self._to_recommendation_read(recommendation)
        else:
            recommendation_read = GovernanceRecommendationRead(
                id='temp-recommendation',
                **recommendation_payload,
            )

        return RecommendationGenerateResponse(
            recommendation=recommendation_read,
            used_templates=[RecommendationTemplateRead.model_validate(item) for item in used_templates],
            related_laws=related_laws,
            case_snapshots=case_snapshots,
            mode=mode,
        )

    def _default_title(self, scope_name: str, risk_type: str) -> str:
        return f'{scope_name}{risk_type}治理建议'

    def _map_level(self, risk_level: str) -> str:
        if risk_level == 'red':
            return 'high'
        if risk_level == 'orange':
            return 'high'
        if risk_level == 'yellow':
            return 'medium'
        return 'low'

    def _ensure_string_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str):
            value = value.strip()
            return [value] if value else []
        return []

    def _to_recommendation_read(self, item) -> GovernanceRecommendationRead:
        data = GovernanceRecommendationRead.model_validate(item)
        if data.related_laws:
            data.related_laws = [RecommendationLawReference.model_validate(x) for x in item.related_laws or []]
        if data.case_snapshots:
            data.case_snapshots = [RecommendationCaseSnapshot.model_validate(x) for x in item.case_snapshots or []]
        return data

    def _collect_case_snapshots(self, *, scope_type: str, scope_id: str, risk_type: str, limit: int) -> list[RecommendationCaseSnapshot]:
        records = self.repo.list_recent_cases(scope_type=scope_type, scope_id=scope_id, risk_type=risk_type, limit=limit)
        snapshots: list[RecommendationCaseSnapshot] = []
        for record in records:
            meta = record.extra_meta or {}
            snapshots.append(
                RecommendationCaseSnapshot(
                    case_id=record.id,
                    title=record.title,
                    case_type=record.case_type,
                    judgment_date=record.judgment_date.isoformat() if record.judgment_date else None,
                    defendant_summary=record.defendant_summary,
                    claim_summary=record.claim_summary,
                    summary=record.judgment_summary or record.fact_summary or record.focus_summary,
                    people_count=int(meta.get('people_count') or 0),
                    total_amount=float(meta.get('total_amount') or 0.0),
                )
            )
        return snapshots

    def _retrieve_related_laws(self, *, resolved_scope_name: str, risk_type: str, alert, profile, case_snapshots: list[RecommendationCaseSnapshot], top_k: int) -> list[RecommendationLawReference]:
        query_parts = [resolved_scope_name, risk_type]
        if alert is not None:
            query_parts.extend([alert.title, alert.trigger_reason])
        if profile is not None:
            query_parts.extend(profile.top_defendants or [])
            query_parts.extend(profile.top_projects or [])
        query_parts.extend([item.title for item in case_snapshots[:3]])
        query = ' '.join(part for part in query_parts if part)
        hits = self.knowledge_service.search(KnowledgeSearchRequest(query=query, top_k=top_k)).hits
        return [
            RecommendationLawReference(
                id=item.id,
                article_no=item.article_no,
                law_name=item.law_name,
                title=item.title,
                content=item.content,
                score=item.score,
            )
            for item in hits
        ]

    def _build_context(self, *, payload: RecommendationGenerateRequest, profile, alert, scope_type: str, scope_id: str, scope_name: str, risk_type: str, current_level: str, case_snapshots: list[RecommendationCaseSnapshot], related_laws: list[RecommendationLawReference], used_templates: list) -> dict:
        profile_summary = self._summarize_profile(profile=profile, alert=alert, scope_name=scope_name, risk_type=risk_type)
        template_summary = [
            {
                'template_code': item.template_code,
                'title': item.title,
                'departments': item.departments,
                'suggested_actions': item.suggested_actions,
                'narrative_hint': item.narrative_hint,
            }
            for item in used_templates
        ]
        return {
            'scope_type': scope_type,
            'scope_id': scope_id,
            'scope_name': scope_name,
            'risk_type': risk_type,
            'current_level': current_level,
            'profile_summary': profile_summary,
            'context_summary': payload.context_summary,
            'alert': {
                'alert_code': getattr(alert, 'alert_code', None),
                'alert_level': getattr(alert, 'alert_level', None),
                'title': getattr(alert, 'title', None),
                'trigger_reason': getattr(alert, 'trigger_reason', None),
                'top_defendants': getattr(alert, 'top_defendants', []) if alert else [],
            },
            'profile': {
                'case_count': getattr(profile, 'case_count', None),
                'people_count': getattr(profile, 'people_count', None),
                'total_amount': getattr(profile, 'total_amount', None),
                'growth_rate': getattr(profile, 'growth_rate', None),
                'repeat_defendant_rate': getattr(profile, 'repeat_defendant_rate', None),
                'repeat_defendant_max_count': getattr(profile, 'repeat_defendant_max_count', None),
                'top_defendants': getattr(profile, 'top_defendants', []) if profile else [],
                'top_projects': getattr(profile, 'top_projects', []) if profile else [],
                'triggered_rules': getattr(profile, 'triggered_rules', []) if profile else [],
            },
            'case_snapshots': [item.model_dump() for item in case_snapshots],
            'related_laws': [item.model_dump() for item in related_laws],
            'template_summary': template_summary,
            'manual_case_summaries': payload.case_summaries,
        }

    def _summarize_profile(self, *, profile, alert, scope_name: str, risk_type: str) -> str:
        if profile is not None:
            return (
                f'{scope_name}近一周期{risk_type}相关案件{profile.case_count}起，涉及{profile.people_count}人，'
                f'总金额约{profile.total_amount:.2f}元，增长率{profile.growth_rate:.2f}，'
                f'重复主体占比{profile.repeat_defendant_rate:.2f}。'
            )
        if alert is not None:
            return alert.trigger_reason
        return f'{scope_name}存在{risk_type}相关风险，需要形成针对性治理建议。'

    def _generate_with_llm(self, context: dict) -> dict[str, Any]:
        prompt = build_recommendation_prompt(context)
        raw = self.llm_client.complete_json(prompt=prompt, system_prompt=RECOMMENDATION_SYSTEM_PROMPT)
        if not isinstance(raw, dict):
            return self._generate_with_templates(context)
        if 'raw_text' in raw:
            return self._generate_with_templates(context)
        return raw

    def _generate_with_templates(self, context: dict) -> dict[str, Any]:
        scope_name = context['scope_name']
        risk_type = context['risk_type']
        current_level = context['current_level']
        alert_code = context.get('alert', {}).get('alert_code')
        top_defendants = context.get('profile', {}).get('top_defendants') or context.get('alert', {}).get('top_defendants') or []
        top_projects = context.get('profile', {}).get('top_projects') or []
        case_count = context.get('profile', {}).get('case_count') or 0
        people_count = context.get('profile', {}).get('people_count') or 0
        total_amount = context.get('profile', {}).get('total_amount') or 0.0
        repeat_max = context.get('profile', {}).get('repeat_defendant_max_count') or 0

        title = f'{scope_name}{risk_type}治理建议'
        summary = f'{scope_name}近期出现{case_count}起{risk_type}相关风险，涉及{people_count}人，总金额约{total_amount:.2f}元。'
        if top_defendants:
            summary += f'主要风险主体为{top_defendants[0]}。'
        if top_projects:
            summary += f'重点关注项目为{top_projects[0]}。'

        actions = []
        departments = []
        if alert_code == 'group_wage_arrears' or risk_type == 'wage_arrears':
            actions.extend([
                '建议联合劳动监察、住建及属地街道对涉事工地开展专项核查，重点核实实名制考勤、工资专户、分包链条及工资台账。',
                '建议督促总承包单位、分包单位及实际控制人限期提交工资支付计划，对拖欠部分明确支付时点并形成书面承诺。',
                '建议同步开展面向工人的释法说明与维权指引，及时回应群体性诉求，防止风险进一步外溢。',
            ])
            departments.extend(['劳动监察', '住房城乡建设部门', '属地街道'])
        elif alert_code == 'high_frequency_defendant':
            actions.extend([
                '建议将高频风险主体纳入重点巡查名单，联合市场监管、劳动监察、街道综治等部门开展交叉核查。',
                '建议围绕同一主体历史涉诉、欠薪、用工合规、关联项目情况建立专门台账，必要时开展集中约谈。',
                '建议对该主体涉及项目同步排查是否存在新增受害人，提前介入疏导，压降重复起诉与集中投诉风险。',
            ])
            departments.extend(['市场监管部门', '劳动监察', '属地街道'])
        elif risk_type == 'labor_dispute':
            actions.extend([
                '建议围绕高发争议企业开展劳动合同、考勤管理、加班工资、解除程序等合规排查。',
                '建议联合工会、人社等部门开展定向普法和调解前置，优先化解批量劳动争议。',
                '建议对近期增长明显的主体建立月度复盘机制，持续跟踪争议类型和化解效果。',
            ])
            departments.extend(['人力资源和社会保障部门', '工会组织', '属地街道'])
        else:
            actions.extend([
                '建议围绕该类风险的主要场景开展专题排查，优先锁定高频主体、重点项目和高发时间段。',
                '建议建立“风险发现—联合会商—限期整改—回访复盘”的闭环治理机制，提高处置效率。',
                '建议结合社区群众关注焦点开展靶向普法与回访，减少同类纠纷重复发生。',
            ])
            departments.extend(['属地街道', '相关行业主管部门'])

        # 吸收模板方向
        for item in context.get('template_summary', []):
            for action in item.get('suggested_actions') or []:
                if action not in actions:
                    actions.append(action)
            for dep in item.get('departments') or []:
                if dep not in departments:
                    departments.append(dep)

        actions = actions[:5]
        departments = departments[:4]

        follow_metrics = [
            '未来30天同类案件数变化',
            '重点主体新增投诉/起诉数量',
            '整改承诺兑现率',
        ]
        if people_count >= 10:
            follow_metrics.insert(0, '涉案人员稳定情况与回访覆盖率')
        if repeat_max:
            follow_metrics.insert(0, '高频主体重复出现次数')

        law_reasons = []
        for law in context.get('related_laws', [])[:3]:
            law_name = law.get('law_name') or ''
            article_no = law.get('article_no') or ''
            title_piece = law.get('title') or ''
            reason = ' '.join(part for part in [law_name, article_no, title_piece] if part)
            if reason:
                law_reasons.append(f'建议可参考{reason}中的相关要求。')

        return {
            'title': title,
            'summary': summary,
            'recommendation_level': self._map_level(current_level),
            'action_items': actions,
            'departments': departments,
            'follow_up_metrics': follow_metrics[:4],
            'law_reasons': law_reasons,
        }

    def _fallback_actions(self, context: dict) -> list[str]:
        return self._generate_with_templates(context).get('action_items', [])

    def _fallback_departments(self, context: dict) -> list[str]:
        return self._generate_with_templates(context).get('departments', [])

    def _fallback_followup_metrics(self, context: dict) -> list[str]:
        return self._generate_with_templates(context).get('follow_up_metrics', [])
