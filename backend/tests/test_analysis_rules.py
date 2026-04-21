from app.common.enums import CaseType
from app.modules.analysis.rules import build_case_summary, classify_case_type, extract_entities


def test_classify_case_type() -> None:
    text = '原告请求被告支付拖欠劳务报酬18000元，案由为劳务合同纠纷。'
    assert classify_case_type(text) == CaseType.labor_service_dispute.value


def test_extract_entities() -> None:
    text = '原告崔某于2023年3月1日在西城区某工地工作，被告北京某建设有限公司拖欠18000元，联系电话13800138000。'
    entities = extract_entities(text)
    assert any('北京某建设有限公司' in item for item in entities.companies)
    assert '2023年3月1日' in entities.dates
    assert '13800138000' in entities.phones
    assert entities.amount_total_estimate >= 18000


def test_build_case_summary() -> None:
    text = '原告崔某与北京某建设有限公司存在劳务合同纠纷，拖欠18000元。'
    entities = extract_entities(text)
    summary = build_case_summary(case_type=CaseType.labor_service_dispute.value, entities=entities, title='示例案件')
    assert '案件类型' in summary
    assert '示例案件' in summary
