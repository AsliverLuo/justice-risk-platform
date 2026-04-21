from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "mock_data" / "cases"
JSON_PATH = OUT_DIR / "demo_cases_100.json"
CSV_PATH = OUT_DIR / "demo_cases_100.csv"


STREETS = [
    {"name": "展览路街道", "lng": 116.345, "lat": 39.923},
    {"name": "金融街街道", "lng": 116.365, "lat": 39.908},
    {"name": "新街口街道", "lng": 116.360, "lat": 39.941},
    {"name": "大栅栏街道", "lng": 116.383, "lat": 39.887},
    {"name": "广安门外街道", "lng": 116.342, "lat": 39.880},
    {"name": "西长安街街道", "lng": 116.378, "lat": 39.905},
    {"name": "陶然亭街道", "lng": 116.375, "lat": 39.872},
    {"name": "德胜街道", "lng": 116.380, "lat": 39.953},
    {"name": "月坛街道", "lng": 116.356, "lat": 39.915},
    {"name": "牛街街道", "lng": 116.363, "lat": 39.888},
]

SOURCES = [
    "12309检察服务热线",
    "街道综治中心转办",
    "劳动监察协同平台",
    "社区网格员上报",
    "群众来信来访",
    "司法所调解平台",
    "检察官走访排查",
]

STATUSES = ["待审查", "已受理", "补充材料", "调解中", "联合核查中", "拟制发检察建议", "已转入支持起诉评估"]

CLAIMANT_NAMES = [
    "林北辰", "许清禾", "周景澄", "陈晚柠", "沈云舟", "顾念安", "宋知遥", "韩亦川", "陆星野", "叶舒然",
    "程砚秋", "唐予白", "乔安澜", "梁嘉木", "苏明岚", "马书远", "魏南栀", "罗景行", "蒋沐辰", "袁诗宁",
    "杜若溪", "任嘉树", "方以默", "白知夏", "钟亦棠", "江临川", "夏南乔", "秦屿森", "孟嘉禾", "贺云深",
    "黎书瑶", "邵庭远", "温若言", "易星河", "傅清越", "宁初夏", "纪南风", "段怀瑾", "邱沐白", "姚知微",
    "莫云栖", "安澄澈", "石闻舟", "范景然", "龙以宁", "田嘉言", "薛北望", "康若竹", "颜司南", "辛明澈",
    "高星眠", "赵予安", "钱景和", "孙若汐", "李望舒", "吴清欢", "郑明序", "王云帆", "冯砚宁", "陈知许",
]

DEFENDANTS = {
    "labor": [
        "北京星澜建筑劳务有限公司",
        "北京嘉禾盛景建设工程有限公司",
        "北京恒筑安泰劳务服务有限公司",
        "北京瑞坤城市更新工程有限公司",
        "北京明诚装饰工程有限公司",
    ],
    "neighbor": [
        "朗庭花园三号楼二单元业主群",
        "清榆里社区物业协调小组",
        "槐安胡同沿街商户自治队",
        "西河湾小区地下一层使用人联组",
    ],
    "contract": [
        "北京启程优选科技有限公司",
        "北京辰光智联商务咨询有限公司",
        "北京蓝桥供应链管理有限公司",
        "北京合创云服信息技术有限公司",
        "北京久誉商贸有限公司",
    ],
    "family": [
        "明安养老护理服务站",
        "和宁家庭服务协调中心",
        "西城春晖社区照护站",
    ],
    "property": [
        "北京润庭物业服务有限公司",
        "北京宜居方舟物业管理有限公司",
        "北京金槐里社区服务有限公司",
        "北京澄园城市服务有限公司",
    ],
    "injury": [
        "北京筑宁安装工程有限公司",
        "北京同辉设备维护有限公司",
        "北京青石机电工程有限公司",
    ],
    "consumer": [
        "北京明眸视界健康管理有限公司",
        "北京悠享健身服务有限公司",
        "北京童趣星球教育咨询有限公司",
        "北京锦礼生活商贸有限公司",
    ],
    "loan": [
        "北京融信达信息咨询有限公司",
        "北京久诺资产管理咨询有限公司",
        "北京诚桥商务服务有限公司",
    ],
    "minor": [
        "青芽课后托管中心",
        "西城晨星体育培训中心",
        "明德启航文化培训工作室",
    ],
}

CASE_PLAN = [
    ("劳动争议", "拖欠工资", 25),
    ("邻里纠纷", "噪声扰民", 15),
    ("合同诈骗", "虚假履约", 15),
    ("婚姻家庭纠纷", "赡养抚养", 10),
    ("物业纠纷", "物业服务争议", 10),
    ("工伤赔偿", "劳务损害赔偿", 8),
    ("消费维权", "预付费退费", 7),
    ("民间借贷", "高息借贷", 5),
    ("未成年人保护线索", "监护和培训机构风险", 5),
]

RISK_LEVELS = ["red"] * 15 + ["orange"] * 25 + ["yellow"] * 35 + ["blue"] * 25
RISK_SCORE_RANGE = {
    "red": (84, 98),
    "orange": (64, 79),
    "yellow": (43, 59),
    "blue": (18, 39),
}


def pick_name(index: int, step: int = 1) -> str:
    return CLAIMANT_NAMES[(index * step) % len(CLAIMANT_NAMES)]


def risk_score(level: str, index: int) -> int:
    low, high = RISK_SCORE_RANGE[level]
    return low + ((index * 7) % (high - low + 1))


def amount_for(case_type: str, level: str, index: int) -> int:
    base = {
        "劳动争议": 18000,
        "邻里纠纷": 3000,
        "合同诈骗": 52000,
        "婚姻家庭纠纷": 12000,
        "物业纠纷": 4500,
        "工伤赔偿": 35000,
        "消费维权": 2800,
        "民间借贷": 42000,
        "未成年人保护线索": 0,
    }[case_type]
    multiplier = {"red": 7, "orange": 4, "yellow": 2, "blue": 1}[level]
    return base * multiplier + (index % 9) * 3600


def people_count_for(case_type: str, level: str, index: int) -> int:
    if case_type == "劳动争议":
        return {"red": 18, "orange": 9, "yellow": 4, "blue": 1}[level] + index % 6
    if case_type in {"物业纠纷", "邻里纠纷"}:
        return {"red": 22, "orange": 12, "yellow": 6, "blue": 2}[level] + index % 5
    if case_type == "合同诈骗":
        return {"red": 16, "orange": 8, "yellow": 3, "blue": 1}[level] + index % 4
    if case_type == "未成年人保护线索":
        return 1 + index % 3
    return {"red": 5, "orange": 3, "yellow": 2, "blue": 1}[level]


def modules_for(case_type: str, level: str) -> list[str]:
    modules = ["ingest", "analysis", "recommendation", "propaganda", "dashboard"]
    if level in {"red", "orange"}:
        modules.append("alert")
    if case_type in {"劳动争议", "工伤赔偿", "婚姻家庭纠纷", "未成年人保护线索"}:
        modules.append("support_prosecution")
    if case_type in {"劳动争议", "工伤赔偿", "合同诈骗"}:
        modules.append("document_gen")
    return modules


def category_key(case_type: str) -> str:
    return {
        "劳动争议": "labor",
        "邻里纠纷": "neighbor",
        "合同诈骗": "contract",
        "婚姻家庭纠纷": "family",
        "物业纠纷": "property",
        "工伤赔偿": "injury",
        "消费维权": "consumer",
        "民间借贷": "loan",
        "未成年人保护线索": "minor",
    }[case_type]


def build_case(index: int, case_type: str, sub_type: str, type_index: int) -> dict:
    level = RISK_LEVELS[index - 1]
    street = STREETS[(index + type_index) % len(STREETS)]
    claimant_count = 2 if people_count_for(case_type, level, index) > 2 else 1
    claimants = [pick_name(index, 1), pick_name(index + 3, 5)][:claimant_count]
    defendants = [DEFENDANTS[category_key(case_type)][(index + type_index) % len(DEFENDANTS[category_key(case_type)])]]
    amount = amount_for(case_type, level, index)
    people_count = people_count_for(case_type, level, index)
    score = risk_score(level, index)
    report_time = datetime(2026, 1, 5, 9, 15) + timedelta(days=index, hours=index % 8, minutes=(index * 11) % 45)

    common = {
        "case_id": f"CASE-2026-{index:04d}",
        "case_type": case_type,
        "sub_type": sub_type,
        "region": "北京市西城区",
        "street": street["name"],
        "longitude": round(street["lng"] + ((index % 5) - 2) * 0.0021, 6),
        "latitude": round(street["lat"] + ((index % 7) - 3) * 0.0016, 6),
        "source": SOURCES[index % len(SOURCES)],
        "report_time": report_time.strftime("%Y-%m-%d %H:%M:%S"),
        "parties": {"claimants": claimants, "defendants": defendants},
        "amount": amount,
        "people_count": people_count,
        "risk_level": level,
        "risk_score": score,
        "expected_modules": modules_for(case_type, level),
        "status": STATUSES[index % len(STATUSES)],
        "is_fictional": True,
    }

    claimant_text = "、".join(claimants)
    defendant = defendants[0]

    if case_type == "劳动争议":
        title = f"{street['name']}某工程项目拖欠{people_count}名劳动者工资线索"
        description = f"{claimant_text}等人在{defendant}承包的西城区更新改造项目中从事木工、钢筋和保洁作业，约定按月结算工资。项目结束后仍有工资未支付，劳动者多次催要未果，部分人员反映存在考勤表被收走、工资结算单未盖章等情况。"
        evidence = ["劳动合同或用工协议", "考勤记录", "工资结算单", "微信催款记录", "施工现场照片"]
        tags = ["欠薪", "农民工", "劳动争议", "支持起诉", "群体性" if level in {"red", "orange"} else "工资支付"]
        actions = ["联动人社部门核查工资台账", "约谈施工总包和劳务分包主体", "评估支持起诉条件", "提示保全考勤和结算证据"]
        propaganda = ["保障农民工工资支付条例", "劳动合同签订提示", "欠薪维权证据清单"]
    elif case_type == "邻里纠纷":
        title = f"{street['name']}居民因噪声和公共空间占用发生邻里纠纷"
        description = f"{claimant_text}反映其居住楼栋长期受到夜间装修、公共楼道堆物和电动车违规停放影响，已与{defendant}多次沟通但未形成稳定整改方案，社区调解后仍有反复。"
        evidence = ["社区调解记录", "现场照片", "噪声时间记录", "物业通知", "居民联名材料"]
        tags = ["邻里纠纷", "社区治理", "调解", "公共安全", "重复投诉" if level in {"red", "orange"} else "普法宣传"]
        actions = ["推动社区、物业、司法所联合调解", "明确公共区域整改期限", "开展相邻关系普法宣传", "建立重复投诉回访台账"]
        propaganda = ["民法典相邻关系", "社区公共空间使用规则", "矛盾纠纷调解指引"]
    elif case_type == "合同诈骗":
        title = f"{defendant}涉嫌以虚假履约承诺引发合同诈骗风险"
        description = f"{claimant_text}称其与{defendant}签订服务或供货合同后，已按约支付款项，但对方长期拖延交付，并以升级服务、追加保证金等理由继续收款。经初步核查，已有多名群众反映类似情况。"
        evidence = ["合同文本", "付款凭证", "聊天记录", "宣传材料截图", "退款承诺书"]
        tags = ["合同诈骗", "涉众风险", "虚假承诺", "资金损失", "重复主体" if level in {"red", "orange"} else "合同纠纷"]
        actions = ["核查同类投诉数量", "研判是否涉嫌刑民交叉", "提示群众固定付款和沟通证据", "必要时移送相关线索"]
        propaganda = ["合同签订风险提示", "预付款消费防范", "识别虚假履约承诺"]
    elif case_type == "婚姻家庭纠纷":
        title = f"{street['name']}赡养抚养义务履行纠纷线索"
        description = f"{claimant_text}反映家庭成员长期未按约履行赡养或抚养义务，相关生活费、医疗费承担存在争议。社区多次协调后，争议双方仍未达成稳定履行安排。"
        evidence = ["亲属关系材料", "医疗票据", "社区调解记录", "转账记录", "生活困难证明"]
        tags = ["赡养抚养", "弱势群体保护", "民事支持起诉", "家庭纠纷"]
        actions = ["核实困难程度和法定权利基础", "联动民政和社区开展帮扶", "评估支持起诉必要性", "推动形成书面履行方案"]
        propaganda = ["民法典婚姻家庭编", "赡养义务说明", "未成年人权益保护"]
    elif case_type == "物业纠纷":
        title = f"{street['name']}小区物业服务和费用争议集中反映"
        description = f"{claimant_text}等业主反映{defendant}在公共维修、停车管理、费用公示等方面存在争议，部分业主拒缴物业费后矛盾升级，社区网格员提示存在群体性投诉风险。"
        evidence = ["物业服务合同", "费用公示照片", "业主沟通记录", "维修报修单", "社区会议纪要"]
        tags = ["物业纠纷", "社区治理", "群体性", "费用公示" if level in {"red", "orange"} else "服务争议"]
        actions = ["推动物业公开费用和维修进度", "组织业委会和居民代表协商", "开展物业服务合同普法", "跟踪群体性风险"]
        propaganda = ["物业服务合同权利义务", "业主大会规则", "公共维修资金说明"]
    elif case_type == "工伤赔偿":
        title = f"{claimant_text}在施工或设备维护过程中受伤后赔偿争议"
        description = f"{claimant_text}在{defendant}安排的设备维护或现场施工中受伤，双方对劳动关系、工伤认定、误工费和后续治疗费用承担存在争议，申请人希望获得法律帮助。"
        evidence = ["就医记录", "现场施工记录", "证人证言", "费用票据", "用工沟通记录"]
        tags = ["工伤赔偿", "劳务损害", "劳动关系", "支持起诉"]
        actions = ["协助梳理劳动关系证据", "引导申请工伤认定", "核算医疗和误工损失", "评估支持起诉条件"]
        propaganda = ["工伤认定流程", "劳务损害赔偿证据", "安全生产责任提示"]
    elif case_type == "消费维权":
        title = f"{street['name']}预付式消费退费争议线索"
        description = f"{claimant_text}在{defendant}办理预付费服务后，商家出现停业、缩短服务期限或拒绝退款等情况。消费者多次沟通未果，要求平台协助研判维权路径。"
        evidence = ["会员协议", "付款凭证", "门店停业照片", "客服聊天记录", "退款申请记录"]
        tags = ["消费维权", "预付费", "退费", "普法推送"]
        actions = ["提示消费者保存合同和付款证据", "联动市场监管核查经营状态", "研判是否存在涉众风险", "推送预付费消费风险提示"]
        propaganda = ["消费者权益保护法", "预付式消费风险提示", "退款证据准备"]
    elif case_type == "民间借贷":
        title = f"{street['name']}民间借贷本金利息争议"
        description = f"{claimant_text}反映其与{defendant}发生借款或居间服务纠纷，双方对本金、利息、服务费和还款记录存在明显分歧，部分材料显示存在高额费用约定。"
        evidence = ["借款协议", "转账流水", "还款记录", "聊天记录", "费用明细"]
        tags = ["民间借贷", "高息风险", "合同审查", "重复主体" if level in {"red", "orange"} else "债务纠纷"]
        actions = ["核查本金和实际到账金额", "识别高息和变相服务费", "提示诉讼时效风险", "排查是否涉及套路贷线索"]
        propaganda = ["民间借贷利率规则", "借款证据清单", "防范套路贷"]
    else:
        title = f"{street['name']}未成年人保护相关风险线索"
        description = f"{claimant_text}反映未成年人在{defendant}接受托管或培训期间出现安全管理、退费或不当管教争议，家长对机构资质、监护责任和后续处置提出检察监督诉求。"
        evidence = ["监护人陈述", "机构协议", "缴费凭证", "现场照片", "沟通记录"]
        tags = ["未成年人保护", "监护责任", "培训机构", "特殊群体保护"]
        actions = ["核查机构资质和安全管理制度", "联动教育、市场监管部门", "评估未成年人权益受损情况", "开展家庭和机构普法"]
        propaganda = ["未成年人保护法", "校外培训风险提示", "监护责任说明"]

    warning_features = []
    if level in {"red", "orange"}:
        warning_features.extend(["高风险等级", "需进入预警列表"])
    if people_count >= 10:
        warning_features.append("群体性风险")
    if index % 6 == 0:
        warning_features.append("重复投诉")
    if index % 8 == 0:
        warning_features.append("重点主体重复出现")

    common.update(
        {
            "title": title,
            "description": description,
            "evidence": evidence,
            "tags": sorted(set(tags)),
            "warning_features": warning_features,
            "recommended_actions": actions,
            "propaganda_topics": propaganda,
            "support_prosecution_candidate": "support_prosecution" in common["expected_modules"],
        }
    )
    return common


def flatten_for_csv(case: dict) -> dict:
    return {
        "case_id": case["case_id"],
        "case_type": case["case_type"],
        "sub_type": case["sub_type"],
        "region": case["region"],
        "street": case["street"],
        "longitude": case["longitude"],
        "latitude": case["latitude"],
        "source": case["source"],
        "report_time": case["report_time"],
        "title": case["title"],
        "description": case["description"],
        "claimants": "|".join(case["parties"]["claimants"]),
        "defendants": "|".join(case["parties"]["defendants"]),
        "amount": case["amount"],
        "people_count": case["people_count"],
        "evidence": "|".join(case["evidence"]),
        "risk_level": case["risk_level"],
        "risk_score": case["risk_score"],
        "tags": "|".join(case["tags"]),
        "warning_features": "|".join(case["warning_features"]),
        "expected_modules": "|".join(case["expected_modules"]),
        "recommended_actions": "|".join(case["recommended_actions"]),
        "propaganda_topics": "|".join(case["propaganda_topics"]),
        "status": case["status"],
        "support_prosecution_candidate": case["support_prosecution_candidate"],
        "is_fictional": case["is_fictional"],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = []
    case_no = 1
    for type_index, (case_type, sub_type, count) in enumerate(CASE_PLAN):
        for _ in range(count):
            cases.append(build_case(case_no, case_type, sub_type, type_index))
            case_no += 1

    JSON_PATH.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csv_rows = [flatten_for_csv(case) for case in cases]
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"generated {len(cases)} cases")
    print(JSON_PATH)
    print(CSV_PATH)


if __name__ == "__main__":
    main()
