from app.modules.analysis.parsers import fallback_parse_structured_case


BJ_CASE_TEXT = '''
案由：民事/合同、准合同纠纷/合同纠纷/劳务合同纠纷
上诉人（原审被告）：北京某公司。
被上诉人（原审原告）：崔某。
被上诉人（原审被告）：张某。
崔某向一审法院提出以下诉讼请求：北京某公司、张某支付崔某劳务费23127元。
一审法院认定事实：崔某受张某雇佣从事案涉项目的劳务工作，并提交工资表、工资发放表及微信聊天记录予以证明。
本院认为，通观双方诉辩意见，本案争议焦点为北京某公司是否应就本案农民工主张的工资承担清偿责任。
依照《保障农民工工资支付条例》第三十六条规定，判决如下：驳回上诉，维持原判。
本判决为终审判决。
'''


GUIDE_CASE_TEXT = '''
【基本案情】
2006年3月9日，张某云与张某森登记结婚。2020年4月，张某云向武邑县检察院申请支持起诉。
【检察机关履职过程】
武邑县检察院查阅报案材料、出警记录、伤情照片、微信聊天记录等，认为根据《中华人民共和国民事诉讼法》第十五条可以支持其起诉离婚。
【裁判结果】
2020年5月28日，武邑县法院作出一审民事判决，准予张某云与张某森离婚。2020年7月15日，衡水市中级人民法院出具民事调解书，双方同意离婚。
'''


def test_fallback_parse_beijing_case() -> None:
    result = fallback_parse_structured_case('崔某劳务合同纠纷二审民事判决书', BJ_CASE_TEXT)
    assert result.cause_of_action and '劳务合同纠纷' in result.cause_of_action
    assert result.plaintiffs and result.plaintiffs[0].name == '崔某'
    assert any(item.name == '北京某公司' for item in result.defendants)
    assert result.claims and '23127元' in result.claims[0]
    assert result.disputed_issues
    assert result.judgment_result and '维持原判' in result.judgment_result


def test_fallback_parse_guiding_case() -> None:
    result = fallback_parse_structured_case('张某云与张某森离婚纠纷支持起诉案', GUIDE_CASE_TEXT)
    assert result.cause_of_action == '离婚纠纷'
    assert result.claims and '请求离婚' in result.claims[0]
    assert result.judgment_result and '离婚' in result.judgment_result
    assert any('民事诉讼法' in item for item in result.applied_laws)
