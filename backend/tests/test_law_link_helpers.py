from app.modules.analysis.rules import extract_entities
from app.modules.analysis.service import AnalysisService


SAMPLE_TEXT = '崔某请求北京某公司支付23127元劳务费，北京市昌平区人民检察院支持起诉，依据《保障农民工工资支付条例》第三十六条。'


def test_law_ref_key_equivalence() -> None:
    assert AnalysisService._law_ref_key('中华人民共和国民事诉讼法', '民诉第15条') == AnalysisService._law_ref_key(
        '《中华人民共和国民事诉讼法》', '第十五条'
    )


def test_build_law_retrieval_queries_contains_compact_hints() -> None:
    entities = extract_entities(SAMPLE_TEXT)
    service = AnalysisService.__new__(AnalysisService)
    queries = service._build_law_retrieval_queries(
        title='崔某劳务合同纠纷二审民事判决书',
        text=SAMPLE_TEXT,
        case_type='labor_service_dispute',
        entities=entities,
    )
    assert queries
    assert any('农民工工资' in item or '劳务报酬' in item for item in queries)
    assert any('北京某公司' in item for item in queries)
