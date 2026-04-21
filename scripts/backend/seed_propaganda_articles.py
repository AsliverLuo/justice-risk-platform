from __future__ import annotations

from app.db.session import SessionLocal
from app.modules.propaganda.schemas import PropagandaArticleBatchUpsertRequest, PropagandaArticleUpsertItem
from app.modules.propaganda.service import PropagandaService


def build_items() -> list[PropagandaArticleUpsertItem]:
    raw_items = [
        {
            'article_code': 'edu-001',
            'title': '工地拖欠工资怎么办？',
            'summary': '围绕讨薪流程、证据收集和维权路径做简明说明。',
            'content': '当工地出现拖欠工资时，劳动者应先固定考勤、聊天记录、工资表、项目名称等证据，再向施工单位、项目承包方主张支付。必要时可以向人社部门投诉、申请法律援助，符合条件的可申请支持起诉。',
            'risk_types': ['labor_service_dispute'],
            'scenario_tags': ['工地欠薪', '农民工工资', '证据固定'],
            'related_law_names': ['保障农民工工资支付条例'],
            'applicable_scope_types': ['community', 'project'],
            'hot_score': 95,
            'priority': 95,
        },
        {
            'article_code': 'edu-002',
            'title': '发包方和承包方谁负责付钱？',
            'summary': '解释工程建设中发包方、承包方、包工头的责任边界。',
            'content': '在工程欠薪场景下，发包方、施工总承包单位、实际招工人之间可能承担不同责任。若施工单位允许个人以其名义承揽工程，导致拖欠农民工工资的，施工单位可能依法承担清偿责任。',
            'risk_types': ['labor_service_dispute'],
            'scenario_tags': ['发包方拖欠', '承包方拖欠', '工程欠薪'],
            'related_law_names': ['保障农民工工资支付条例', '中华人民共和国民法典'],
            'applicable_scope_types': ['project'],
            'hot_score': 92,
            'priority': 98,
        },
        {
            'article_code': 'edu-003',
            'title': '没有劳动合同能要回工资吗？',
            'summary': '说明没有书面合同情况下的常见证据与维权方式。',
            'content': '没有书面劳动合同并不当然导致无法维权。考勤记录、工资表、转账记录、工友证言、聊天记录、工地照片等都可以作为证明劳动或劳务关系存在的证据。',
            'risk_types': ['labor_service_dispute', 'labor_dispute'],
            'scenario_tags': ['无合同用工', '证据固定', '劳动报酬'],
            'related_law_names': ['中华人民共和国民事诉讼法'],
            'applicable_scope_types': ['community', 'project'],
            'hot_score': 88,
            'priority': 90,
        },
        {
            'article_code': 'edu-004',
            'title': '什么是支持起诉？',
            'summary': '介绍支持起诉的适用对象、条件和流程。',
            'content': '支持起诉是检察机关依法维护特定弱势群体合法权益的一种方式。对农民工欠薪、家暴受害人等情形，符合条件的可以依法申请支持起诉。',
            'risk_types': ['support_prosecution', 'other'],
            'scenario_tags': ['支持起诉', '依法维权'],
            'related_law_names': ['中华人民共和国民事诉讼法', '关于办理民事支持起诉案件若干问题的指导意见'],
            'applicable_scope_types': ['community', 'street', 'project'],
            'hot_score': 85,
            'priority': 86,
        },
        {
            'article_code': 'edu-005',
            'title': '遇到群体性欠薪如何依法维权？',
            'summary': '说明多人讨薪场景下的维权秩序与风险提示。',
            'content': '群体性欠薪应当优先统一证据、明确被告主体、依法向有关部门反映，并避免过激表达。必要时可通过法律援助、支持起诉等方式维权。',
            'risk_types': ['labor_service_dispute'],
            'scenario_tags': ['群体性欠薪', '多人维权', '工地欠薪'],
            'related_law_names': ['保障农民工工资支付条例'],
            'applicable_scope_types': ['project', 'community'],
            'hot_score': 90,
            'priority': 92,
        },
        {
            'article_code': 'edu-006',
            'title': '包工头拖欠工资怎么办？',
            'summary': '面向实际招工人拖欠工资场景的简明普法。',
            'content': '被包工头拖欠工资时，应尽快固定招工、考勤、结算、转账与聊天记录等证据，并梳理项目所属施工单位及发包链条。',
            'risk_types': ['labor_service_dispute'],
            'scenario_tags': ['包工头拖欠', '高频欠薪主体', '工地欠薪'],
            'related_law_names': ['保障农民工工资支付条例'],
            'applicable_scope_types': ['project'],
            'hot_score': 87,
            'priority': 89,
        },
        {
            'article_code': 'edu-007',
            'title': '被拖欠工资时证据怎么留？',
            'summary': '强调考勤、工资表、照片、录音等证据的重要性。',
            'content': '维权成败很大程度取决于证据完整性。建议劳动者及时保存工地照片、定位、工资表、聊天记录、录音录像、转账记录等材料。',
            'risk_types': ['labor_service_dispute', 'labor_dispute'],
            'scenario_tags': ['证据固定', '工资表', '聊天记录'],
            'related_law_names': ['中华人民共和国民事诉讼法'],
            'applicable_scope_types': ['community', 'project', 'street'],
            'hot_score': 89,
            'priority': 84,
        },
        {
            'article_code': 'edu-008',
            'title': '劳动争议和劳务纠纷有什么区别？',
            'summary': '帮助群众区分劳动关系与劳务关系。',
            'content': '劳动争议和劳务纠纷在主体关系、处理程序和法律依据上存在差异。正确区分有助于选择仲裁、诉讼或其他维权路径。',
            'risk_types': ['labor_dispute', 'labor_service_dispute'],
            'scenario_tags': ['劳动争议', '劳务合同纠纷'],
            'related_law_names': ['中华人民共和国民法典'],
            'applicable_scope_types': ['community', 'street'],
            'hot_score': 80,
            'priority': 78,
        },
        {
            'article_code': 'edu-009',
            'title': '发生家庭暴力后如何依法求助？',
            'summary': '为支持起诉和反家暴场景预留通用内容。',
            'content': '遭受家庭暴力时，应及时报警、就医、申请人身安全保护令，并保留伤情照片、出警记录等证据。符合条件的，可申请支持起诉。',
            'risk_types': ['support_prosecution', 'other'],
            'scenario_tags': ['家庭暴力', '支持起诉', '依法维权'],
            'related_law_names': ['中华人民共和国民事诉讼法'],
            'applicable_scope_types': ['community', 'street'],
            'hot_score': 76,
            'priority': 70,
        },
        {
            'article_code': 'edu-010',
            'title': '社区法治提示：遇到纠纷先固定事实',
            'summary': '面向通用社区风险场景的兜底普法内容。',
            'content': '面对各类纠纷，建议群众先保存关键事实与证据，理性表达诉求，依法寻求街道、社区、行业主管部门或司法机关帮助。',
            'risk_types': ['other'],
            'scenario_tags': ['普法', '法治治理'],
            'related_law_names': [],
            'applicable_scope_types': ['community', 'street', 'project'],
            'hot_score': 70,
            'priority': 60,
        },
    ]
    return [PropagandaArticleUpsertItem(**item) for item in raw_items]


def main() -> None:
    db = SessionLocal()
    try:
        service = PropagandaService(db)
        payload = PropagandaArticleBatchUpsertRequest(items=build_items())
        result = service.batch_upsert_articles(payload)
        print(f'seeded {len(result.items)} propaganda articles')
    finally:
        db.close()


if __name__ == '__main__':
    main()
