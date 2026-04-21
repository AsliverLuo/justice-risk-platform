from __future__ import annotations

from app.db.session import SessionLocal, init_db
from app.modules.recommendation.schemas import RecommendationTemplateBatchUpsertRequest, RecommendationTemplateUpsertItem
from app.modules.recommendation.service import RecommendationService


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        service = RecommendationService(db)
        payload = RecommendationTemplateBatchUpsertRequest(
            items=[
                RecommendationTemplateUpsertItem(
                    template_code='wage-group-special-inspection',
                    title='群体性欠薪专项核查模板',
                    risk_type='wage_arrears',
                    alert_code='group_wage_arrears',
                    applicable_levels=['orange', 'red'],
                    departments=['劳动监察', '住房城乡建设部门', '属地街道'],
                    suggested_actions=[
                        '建议联合劳动监察、住建部门和属地街道对涉事工地开展专项检查。',
                        '建议核查实名制考勤、分包链条、工资专户及工资支付台账。',
                        '建议督促总承包及分包单位限期提出清欠计划并向工人公开说明。',
                    ],
                    narrative_hint='重点突出群体性、工程项目、账册核查和限期清欠。',
                    priority=95,
                ),
                RecommendationTemplateUpsertItem(
                    template_code='high-frequency-defendant-governance',
                    title='高频风险主体治理模板',
                    risk_type='wage_arrears',
                    alert_code='high_frequency_defendant',
                    applicable_levels=['orange', 'red'],
                    departments=['市场监管部门', '劳动监察', '属地街道'],
                    suggested_actions=[
                        '建议将高频风险主体纳入重点巡查和约谈名单。',
                        '建议梳理其历史涉诉、用工合规、关联项目和投诉分布，形成专门台账。',
                        '建议对其关联工地同步排查是否存在新增受害人并提前介入化解。',
                    ],
                    narrative_hint='重点突出重复主体、台账化管理、联合会商与源头压降。',
                    priority=92,
                ),
                RecommendationTemplateUpsertItem(
                    template_code='labor-dispute-compliance',
                    title='劳动争议合规治理模板',
                    risk_type='labor_dispute',
                    applicable_levels=['yellow', 'orange', 'red'],
                    departments=['人力资源和社会保障部门', '工会组织', '属地街道'],
                    suggested_actions=[
                        '建议围绕高发企业开展劳动合同、考勤管理、加班工资、解除程序等专项合规排查。',
                        '建议联合工会、人社开展调解前置和定向普法，减少批量争议进入诉讼阶段。',
                        '建议对争议增长明显的企业建立月度复盘与回访机制。',
                    ],
                    narrative_hint='重点突出企业合规、调解前置、普法与复盘。',
                    priority=85,
                ),
                RecommendationTemplateUpsertItem(
                    template_code='risk-level-upgrade-general',
                    title='风险等级升级通用模板',
                    alert_code='risk_level_upgrade',
                    applicable_levels=['yellow', 'orange', 'red'],
                    departments=['属地街道', '相关行业主管部门'],
                    suggested_actions=[
                        '建议围绕高风险社区/项目建立“发现—会商—整改—回访”闭环处置机制。',
                        '建议对重点主体、重点项目和重点时间段进行持续监测和数据复盘。',
                        '建议同步推送针对性普法内容，提前疏导潜在矛盾。',
                    ],
                    narrative_hint='适用于其他未细分风险场景的兜底模板。',
                    priority=70,
                ),
            ]
        )
        result = service.batch_upsert_templates(payload)
        print({'seeded_templates': len(result.items)})
    finally:
        db.close()


if __name__ == '__main__':
    main()
