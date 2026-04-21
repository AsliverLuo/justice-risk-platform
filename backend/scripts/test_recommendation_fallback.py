from datetime import date
from app.db.session import SessionLocal, init_db
from app.modules.alert.models import AlertEvent, CommunityRiskProfile
from app.modules.recommendation.schemas import RecommendationGenerateRequest, RecommendationTemplateBatchUpsertRequest, RecommendationTemplateUpsertItem
from app.modules.recommendation.service import RecommendationService


def test_recommendation_generate_fallback_template():
    init_db()
    db = SessionLocal()
    try:
        profile = CommunityRiskProfile(
            scope_type='project',
            scope_id='p-1',
            scope_name='新街口排水改造项目',
            risk_type='wage_arrears',
            stat_window_start=date(2026, 4, 1),
            stat_window_end=date(2026, 4, 16),
            case_count=5,
            total_amount=80000,
            people_count=12,
            growth_rate=0.5,
            repeat_defendant_rate=0.8,
            repeat_defendant_max_count=5,
            top_defendants=['某建设公司'],
            top_projects=['新街口排水改造项目'],
            metric_scores=[],
            triggered_rules=['group_wage_arrears'],
            risk_score=86,
            risk_level='red',
            extra_meta={},
        )
        db.add(profile)
        db.flush()
        alert = AlertEvent(
            scope_type='project',
            scope_id='p-1',
            scope_name='新街口排水改造项目',
            risk_type='wage_arrears',
            alert_code='group_wage_arrears',
            alert_level='red',
            title='群体性欠薪预警',
            trigger_reason='近30天涉及12人，超过阈值10人',
            profile_id=profile.id,
            current_level='red',
            people_count=12,
            total_amount=80000,
            top_defendants=['某建设公司'],
            extra_meta={},
        )
        db.add(alert)
        db.commit()

        service = RecommendationService(db)
        service.batch_upsert_templates(
            RecommendationTemplateBatchUpsertRequest(
                items=[
                    RecommendationTemplateUpsertItem(
                        template_code='group-test',
                        title='群体性欠薪模板',
                        risk_type='wage_arrears',
                        alert_code='group_wage_arrears',
                        applicable_levels=['orange', 'red'],
                        departments=['劳动监察'],
                        suggested_actions=['建议联合劳动监察开展专项检查。'],
                    )
                ]
            )
        )
        resp = service.generate(RecommendationGenerateRequest(alert_id=alert.id, prefer_llm=False, persist=False))
        assert resp.recommendation.title
        assert resp.recommendation.source_mode == 'template'
        assert resp.recommendation.action_items
        assert '劳动监察' in resp.recommendation.departments
    finally:
        db.close()
