from __future__ import annotations


def format_date_cn(date_str: str) -> str:
    if not date_str:
        return ""
    parts = date_str.split("-")
    if len(parts) != 3:
        return date_str
    year, month, day = parts
    return f"{int(year)}年{int(month)}月{int(day)}日"


def money_to_cn(amount: float) -> str:
    digits = "零壹贰叁肆伍陆柒捌玖"
    units = ["", "拾", "佰", "仟", "万", "拾", "佰", "仟", "亿"]

    try:
        amount_int = int(round(float(amount)))
    except Exception:
        return str(amount)

    if amount_int == 0:
        return "零元"

    num_str = str(amount_int)
    result = ""
    length = len(num_str)

    for index, ch in enumerate(num_str):
        num = int(ch)
        unit = units[length - index - 1]
        if num == 0:
            if not result.endswith("零") and index != length - 1:
                result += "零"
        else:
            result += digits[num] + unit

    while "零零" in result:
        result = result.replace("零零", "零")

    result = result.rstrip("零")
    result = result.replace("零万", "万")
    result = result.replace("零亿", "亿")

    return result + "元"


def sort_defendants(defendants: list) -> list:
    role_order = {
        "发包方": 1,
        "承包方": 2,
        "担保方": 3,
        "实控人": 4,
        "直接雇佣人": 5,
        "其他": 99,
    }
    return sorted(defendants, key=lambda item: role_order.get(item.role_type, 999))
