from types import SimpleNamespace

from app.modules.propaganda.rules import expand_context_tags, score_article_match


def make_article(**kwargs):
    defaults = {
        'risk_types': ['labor_service_dispute'],
        'scenario_tags': ['工地欠薪'],
        'related_law_names': ['保障农民工工资支付条例'],
        'applicable_scope_types': ['project'],
        'hot_score': 50,
        'priority': 50,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_expand_context_tags_adds_aliases():
    tags = expand_context_tags('labor_service_dispute', ['发包方拖欠'], 'group_wage_arrears')
    assert '工地欠薪' in tags
    assert '发包方拖欠' in tags
    assert 'group_wage_arrears' in tags


def test_score_article_prefers_specific_scenario_match():
    specific = make_article(scenario_tags=['发包方拖欠', '工程欠薪'], hot_score=80, priority=90)
    generic = make_article(risk_types=['other'], scenario_tags=['普法'], hot_score=95, priority=95)

    specific_score = score_article_match(
        specific,
        risk_type='labor_service_dispute',
        context_tags=['发包方拖欠', '工地欠薪'],
        related_law_names=['保障农民工工资支付条例'],
        scope_type='project',
    )
    generic_score = score_article_match(
        generic,
        risk_type='labor_service_dispute',
        context_tags=['发包方拖欠', '工地欠薪'],
        related_law_names=['保障农民工工资支付条例'],
        scope_type='project',
    )
    assert specific_score['score'] > generic_score['score']
