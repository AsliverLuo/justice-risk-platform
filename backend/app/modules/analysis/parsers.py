from __future__ import annotations

import re
from typing import Any

from app.modules.analysis.schemas import StructuredCaseFields


def _clean_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def extract_case_no(text: str) -> str | None:
    """
    提取案号，例如：
    (2025)京01民终12262号
    （2025）京01民终12262号
    """
    if not text:
        return None

    patterns = [
        r"[（(]\d{4}[)）][^\n，。；：:]*?号",
        r"案号[：:]\s*([（(]\d{4}[)）][^\n，。；：:]*?号)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if match.lastindex:
                return match.group(1).strip()
            return match.group(0).strip()
    return None


def extract_court_name(text: str) -> str | None:
    """
    提取法院名称，例如：
    北京市第一中级人民法院
    河北省武邑县人民法院
    """
    if not text:
        return None

    patterns = [
        r"审理法院[：:]\s*([^\n]+?人民法院)",
        r"([^\n，。；：:（）()]{2,40}?人民法院)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if match.lastindex:
                return match.group(1).strip()
            return match.group(0).strip()
    return None


def extract_judgment_date(text: str) -> str | None:
    """
    提取裁判日期，例如：
    2025.11.26
    2025年11月26日
    二Ｏ二五年十一月二十六日（这种先不强转，原样返回）
    """
    if not text:
        return None

    patterns = [
        r"裁判日期[：:]\s*(\d{4}\.\d{1,2}\.\d{1,2})",
        r"裁判日期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)",
        r"(\d{4}\.\d{1,2}\.\d{1,2})",
        r"(\d{4}年\d{1,2}月\d{1,2}日)",
        r"([二三四五六七八九〇Ｏ○零一二两\d]{4}年[一二三四五六七八九十〇Ｏ○零\d]{1,3}月[一二三四五六七八九十〇Ｏ○零\d]{1,3}日)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def _extract_cause_of_action(text: str) -> str | None:
    if not text:
        return None

    patterns = [
        r"案由[：:]\s*([^\n]+)",
        r"因与[^\n，。]*?([^\n，。]*纠纷)一案",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def _extract_party_lines(text: str, prefix: str) -> list[str]:
    if not text:
        return []

    results: list[str] = []
    pattern = rf"{prefix}[^\n：:]*[：:]\s*([^\n]+)"
    for match in re.finditer(pattern, text):
        value = match.group(1).strip()
        if value and value not in results:
            results.append(value)
    return results


def _extract_claims(text: str) -> list[str]:
    if not text:
        return []

    claims: list[str] = []

    patterns = [
        r"(?:提出以下诉讼请求|诉讼请求)[：:]\s*([^\n]+)",
        r"[一二三四五六七八九十\d]+[\.、]\s*([^。\n]+)",
    ]

    first = re.search(patterns[0], text)
    if first:
        claims.append(first.group(1).strip())

    for match in re.finditer(patterns[1], text):
        line = match.group(1).strip()
        if "请求" in line or "支付" in line or "判令" in line or "离婚" in line:
            if line not in claims:
                claims.append(line)

    return claims


def _extract_focus(text: str) -> list[str]:
    if not text:
        return []

    results: list[str] = []
    patterns = [
        r"争议焦点[为是：:]\s*([^\n。]+)",
        r"本案争议焦点[为是：:]\s*([^\n。]+)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            item = match.group(1).strip()
            if item and item not in results:
                results.append(item)
    return results


def _extract_fact_summary(text: str) -> str | None:
    if not text:
        return None

    patterns = [
        r"一审法院认定事实[：:](.*?)(?:一审法院认为|本院认为|综上)",
        r"【基本案情】(.*?)(?:【检察机关履职过程】|【指导意义】|【相关规定】)",
        r"【基本案情】(.*?)(?:【要旨】|【指导意义】|【裁判结果】)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.S)
        if match:
            value = _clean_text(match.group(1))
            if value:
                return value[:3000]
    return None


def _extract_judgment_result(text: str) -> str | None:
    if not text:
        return None

    patterns = [
        r"判决如下[：:](.*?)(?:本判决为终审判决|二审案件受理费|审 判 长|审判长)",
        r"裁判结果[：:](.*?)(?:【指导意义】|【相关规定】)",
        r"法庭经审理.*?当庭作出一审判决，(.*?)(?:一审宣判后|【支持提起变更抚养权诉讼】|【指导意义】)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.S)
        if match:
            value = _clean_text(match.group(1))
            if value:
                return value[:2000]
    return None


def _extract_applied_laws(text: str) -> list[str]:
    if not text:
        return []

    laws: list[str] = []

    patterns = [
        r"依照(.*?)(?:判决如下|之规定，判决如下)",
        r"【相关规定】(.*)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.S)
        if not match:
            continue
        block = match.group(1)
        for line in re.split(r"[\n；;]", block):
            line = _clean_text(line)
            if (
                "法" in line
                or "条例" in line
                or "解释" in line
                or "规定" in line
                or "意见" in line
            ):
                if line and line not in laws:
                    laws.append(line[:200])

    return laws[:20]


def fallback_parse_structured_case(text: str, title: str | None = None) -> StructuredCaseFields:
    """
    当 LLM 不可用或 JSON 解析失败时，使用规则版兜底解析。
    """
    merged_text = _clean_text(text)
    merged_title = _clean_text(title)

    plaintiffs = _extract_party_lines(merged_text, "原告") + _extract_party_lines(merged_text, "被上诉人（原审原告）")
    defendants = (
        _extract_party_lines(merged_text, "被告")
        + _extract_party_lines(merged_text, "上诉人（原审被告）")
        + _extract_party_lines(merged_text, "被上诉人（原审被告）")
    )

    # 去重但保序
    plaintiffs = list(dict.fromkeys(plaintiffs))
    defendants = list(dict.fromkeys(defendants))

    case_type = "guiding_case" if "指导性案例" in merged_text or "检例第" in merged_text else "judgment"

    return StructuredCaseFields(
        case_title=merged_title or None,
        case_no=extract_case_no(merged_text),
        court_name=extract_court_name(merged_text),
        judgment_date=extract_judgment_date(merged_text),
        case_type=case_type,
        cause_of_action=_extract_cause_of_action(merged_text),
        plaintiffs=plaintiffs,
        defendants=defendants,
        claims=_extract_claims(merged_text),
        disputed_issues=_extract_focus(merged_text),
        facts_found_by_court=_extract_fact_summary(merged_text),
        judgment_result=_extract_judgment_result(merged_text),
        applied_laws=_extract_applied_laws(merged_text),
        extra_meta={},
    )