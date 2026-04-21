from __future__ import annotations

from textwrap import dedent


def _trim_text(text: str, limit: int = 12000) -> str:
    text = (text or '').strip()
    if len(text) <= limit:
        return text
    return text[:limit] + '\n\n[文本已截断用于大模型调用]'


JSON_OUTPUT_RULE = '仅输出合法 JSON，不要输出 markdown 代码块，不要补充解释。'


CASE_STRUCTURE_SYSTEM_PROMPT = dedent(
    """
    你是民事案件结构化解析助手。请将判例文书或指导性案例解析为结构化字段，便于后续做文书分类、实体抽取和法条关联。
    输出必须严格遵循 JSON 结构，并尽量使用原文措辞。
    """
).strip()


NLP_SYSTEM_PROMPT = dedent(
    """
    你是法律 NLP 助手。请在保证可审查性的前提下，将案件文本分类、抽取实体或匹配法条。
    输出必须为 JSON，且不要编造原文中没有的关键事实。
    如信息不足，请返回空数组、空字符串或低置信度，而不是猜测。
    """
).strip()


STRUCTURE_SCHEMA_HINT = dedent(
    """
    JSON schema:
    {
      "cause_of_action": "",
      "plaintiffs": [{"name": "", "role": "", "party_type": "individual|company", "original_label": "", "summary": ""}],
      "defendants": [{"name": "", "role": "", "party_type": "individual|company", "original_label": "", "summary": ""}],
      "claims": [""],
      "disputed_issues": [""],
      "facts_found_by_court": "",
      "judgment_result": "",
      "applied_laws": ["《某法》第X条"],
      "source_sections": {
        "claims_source": "",
        "facts_source": "",
        "judgment_source": ""
      }
    }
    """
).strip()


def build_case_structure_prompt(title: str, text: str) -> str:
    return dedent(
        f"""
        任务：解析下面这份案件文本，提取案由、原告信息、被告信息、诉请、争议焦点、法院认定事实、裁判结果、适用法条。
        {JSON_OUTPUT_RULE}

        {STRUCTURE_SCHEMA_HINT}

        规则：
        1. 原告/被告信息尽量按案件程序角色填写，summary 保留最关键身份描述。
        2. claims 只保留诉讼请求或核心请求，不要展开成大段描述。
        3. disputed_issues 尽量抽取法院明确讨论的争议焦点；若原文未显式写明，可概括 1-3 条。
        4. applied_laws 只写文中明确出现或裁判明显直接适用的法条。

        标题：{title}
        正文：
        {_trim_text(text)}
        """
    ).strip()


CLASSIFY_SCHEMA_HINT = '{"case_type": "labor_service_dispute|labor_dispute|other", "confidence": 0.0, "reason": ""}'


def build_classification_prompt(title: str | None, text: str) -> str:
    return dedent(
        f"""
        任务：将下面案件文本分类到以下三类之一：
        1. labor_service_dispute：劳务合同纠纷、追索劳动报酬、农民工工资拖欠、承包/分包导致的欠薪清偿责任等。
        2. labor_dispute：劳动关系、劳动合同、劳动仲裁、工伤、违法解除、社保、公积金等。
        3. other：以上两类之外的其他案件。

        判别优先规则：
        - 如果文本核心围绕“拖欠劳务费、农民工工资、劳务报酬、施工项目上的工人欠薪”，优先判为 labor_service_dispute。
        - 如果核心围绕“劳动关系是否成立、劳动仲裁、工伤、解除劳动关系”，优先判为 labor_dispute。
        - 支持起诉、离婚纠纷、家庭暴力等不属于上述两类时，判为 other。

        {JSON_OUTPUT_RULE}
        JSON schema: {CLASSIFY_SCHEMA_HINT}

        标题：{title or ''}
        正文：
        {_trim_text(text, 8000)}
        """
    ).strip()


ENTITY_SCHEMA_HINT = dedent(
    """
    {
      "persons": [""],
      "companies": [""],
      "amounts": [""],
      "amount_total_estimate": 0.0,
      "dates": [""],
      "addresses": [""],
      "projects": [""],
      "phones": [""],
      "id_cards": [""],
      "law_refs": ["《某法》第X条"]
    }
    """
).strip()


def build_entity_extraction_prompt(title: str | None, text: str) -> str:
    return dedent(
        f"""
        任务：从案件文本中抽取关键实体，重点抽取：人名、公司名、金额、日期、地址；若文本中出现项目名称、手机号、身份证号、法条引用，也一并抽取。
        仅保留原文可直接支持的实体，不要臆造。

        输出要求：
        - persons：只放自然人姓名，如崔某、张某云。
        - companies：只放单位或公司名称。
        - amounts：保留原文表达，例如 23127元、8万元。
        - amount_total_estimate：如果存在多个金额，给出一个尽量合理的金额总估计；没有就填 0。
        - dates / addresses / projects / law_refs：尽量保留原文表达。

        {JSON_OUTPUT_RULE}
        JSON schema: {ENTITY_SCHEMA_HINT}

        标题：{title or ''}
        正文：
        {_trim_text(text, 8000)}
        """
    ).strip()


LAW_LINK_SCHEMA_HINT = dedent(
    """
    {
      "recommended_refs": [
        {"law_name": "", "article_no": "", "reason": ""}
      ]
    }
    """
).strip()


def build_law_link_prompt(
    title: str | None,
    text: str,
    knowledge_context: str,
    top_k: int,
    case_profile: str = '',
) -> str:
    return dedent(
        f"""
        任务：根据案件描述，从候选法律条文中选出最相关的 {top_k} 条，并为每条说明匹配理由。
        只能从候选条文中选择，不得编造不存在的法条。

        选择规则：
        1. 优先选择能直接支持案件请求、抗辩判断或责任分配的条文。
        2. 对农民工欠薪/劳务报酬案件，优先关注《保障农民工工资支付条例》《民法典》《民事诉讼法》中的直接依据。
        3. 如果文本本身已明确引用某法条，应优先考虑该法条。
        4. 如果候选条文很多，宁可少选也不要错选。

        {JSON_OUTPUT_RULE}
        JSON schema: {LAW_LINK_SCHEMA_HINT}

        标题：{title or ''}
        案件画像：{case_profile}
        案件描述：
        {_trim_text(text, 8000)}

        候选条文：
        {knowledge_context}
        """
    ).strip()
