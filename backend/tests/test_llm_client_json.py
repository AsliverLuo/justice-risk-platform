from app.infra.llm_client import BaseLLMClient


def test_extract_json_block_from_markdown_fence() -> None:
    raw = '```json\n{"case_type":"labor_service_dispute"}\n```'
    assert BaseLLMClient._extract_json_block(raw) == '{"case_type":"labor_service_dispute"}'
