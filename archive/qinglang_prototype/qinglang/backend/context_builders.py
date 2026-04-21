from fastapi import HTTPException

from database import SessionLocal
from models import Applicant, CaseRecord, Defendant, Evidence, DocumentOption
from utils import format_date_cn, money_to_cn, sort_defendants


def build_complaint_context(case_id: int) -> dict:
    db = SessionLocal()
    try:
        case_record = db.query(CaseRecord).filter(CaseRecord.id == case_id).first()
        if not case_record:
            raise HTTPException(status_code=404, detail="案件不存在")

        applicant = db.query(Applicant).filter(Applicant.id == case_record.applicant_id).first()
        if not applicant:
            raise HTTPException(status_code=404, detail="申请人不存在")

        defendants = db.query(Defendant).filter(Defendant.case_id == case_id).all()
        evidences = db.query(Evidence).filter(Evidence.case_id == case_id).all()
        document_option = db.query(DocumentOption).filter(DocumentOption.case_id == case_id).first()

        defendants = sort_defendants(defendants)

        court_name = document_option.court_name if document_option else ""
        case_cause = document_option.case_cause if document_option else "劳务合同纠纷"

        # 生成被告文本
        defendant_texts = []
        order_map = ["一", "二", "三", "四", "五", "六"]

        for i, d in enumerate(defendants):
            order_text = order_map[i] if i < len(order_map) else str(i + 1)

            if d.defendant_type == "company":
                line1 = f"被告{order_text}：{d.name}，统一社会信用代码：{d.credit_code_or_id_number}，住所地{d.address}。"
                line2 = f"法定代表人：{d.legal_representative}，联系电话：{d.phone}。"
            else:
                line1 = f"被告{order_text}：{d.name}，身份证号码：{d.credit_code_or_id_number}，住{d.address}，联系电话：{d.phone}。"
                line2 = ""

            defendant_texts.append(line1)
            if line2:
                defendant_texts.append(line2)

        # 按角色提取责任链
        role_map = {d.role_type: d.name for d in defendants}
        employer_name = case_record.employer_name or role_map.get("直接雇佣人", "")

        # 事实与理由（第一版：规则拼接）
        facts_reason_parts = []

        facts_reason_parts.append(
            f"{format_date_cn(case_record.work_start_date)}至{format_date_cn(case_record.work_end_date)}，"
            f"{applicant.name}受雇于{employer_name}，在{case_record.project_name}从事{case_record.job_type}工作。"
        )

        project_roles = []
        if "发包方" in role_map:
            project_roles.append(f"案涉工程项目的发包方系{role_map['发包方']}")
        if "承包方" in role_map:
            project_roles.append(f"承包方系{role_map['承包方']}")
        if "担保方" in role_map:
            project_roles.append(f"担保方系{role_map['担保方']}")

        if project_roles:
            facts_reason_parts.append("，".join(project_roles) + "。")

        facts_reason_parts.append(
            f"施工期间，{applicant.name}完成了相关劳务工作，共计工作{case_record.actual_work_days}天。"
            f"双方约定劳务费标准为{case_record.agreed_wage_standard}，"
            f"应得劳务报酬合计{case_record.total_wage_due}元。"
        )

        facts_reason_parts.append(
            f"然而，截至目前仍有{case_record.unpaid_amount}元未予支付。"
        )

        if case_record.has_repeated_demand and case_record.demand_desc:
            facts_reason_parts.append(
                f"{applicant.name}曾多次催要未果，具体情况如下：{case_record.demand_desc}。"
            )

        facts_reason_parts.append("为维护合法权益，现依法提起诉讼，望判如所请。")

        facts_reason_text = "\n".join(facts_reason_parts)

        evidence_summary = [
            {
                "type": item.evidence_type,
                "file_path": item.file_path,
                "description": item.description,
            }
            for item in evidences
        ]

        return {
            "case_id": case_record.id,
            "plaintiff_name": applicant.name,
            "plaintiff_gender": applicant.gender,
            "plaintiff_birth_date": applicant.birth_date,
            "plaintiff_birth_date_cn": format_date_cn(applicant.birth_date),
            "plaintiff_ethnicity": applicant.ethnicity,
            "plaintiff_id_number": applicant.id_number,
            "plaintiff_address": applicant.current_address or applicant.hukou_address,
            "plaintiff_phone": applicant.phone,
            "court_name": court_name,
            "case_cause": case_cause,
            "unpaid_amount": case_record.unpaid_amount,
            "unpaid_amount_cn": money_to_cn(case_record.unpaid_amount),
            "total_wage_due": case_record.total_wage_due,
            "agreed_wage_standard": case_record.agreed_wage_standard,
            "actual_work_days": case_record.actual_work_days,
            "project_name": case_record.project_name,
            "job_type": case_record.job_type,
            "work_start_date_cn": format_date_cn(case_record.work_start_date),
            "work_end_date_cn": format_date_cn(case_record.work_end_date),
            "defendant_count": len(defendants),
            "defendant_texts": defendant_texts,
            "facts_reason_text": facts_reason_text,
            "evidence_summary": evidence_summary,
        }
    finally:
        db.close()
