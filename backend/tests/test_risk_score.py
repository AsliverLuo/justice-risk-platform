from app.common.enums import RiskLevel
from app.modules.analysis.rules import calculate_aggregate_risk


def test_calculate_aggregate_risk() -> None:
    result = calculate_aggregate_risk(
        case_count=8,
        total_amount=320000,
        people_count=12,
        growth_rate=0.4,
        repeat_defendant_rate=0.7,
    )
    assert result.score > 0
    assert result.level in {RiskLevel.yellow.value, RiskLevel.orange.value, RiskLevel.red.value}
    assert result.details
    assert result.triggered_rules
