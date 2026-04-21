from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.support_prosecution.service import SupportProsecutionService


class DocumentGenerationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate(self, case_id: int, document_types: list[str]) -> dict:
        context = SupportProsecutionService(self.db).get_complaint_context(case_id)
        documents = []
        for document_type in document_types:
            if document_type == "support_prosecution":
                documents.append(self._support_prosecution_letter(context))
            else:
                documents.append(self._complaint(context))
        return {"case_id": case_id, "documents": documents}

    def _complaint(self, context: dict) -> dict:
        defendant_block = "\n".join(context["defendant_texts"])
        evidence_block = "\n".join(
            f"{index}. {item['type']}：{item['description']}（{item['file_path']}）"
            for index, item in enumerate(context["evidence_summary"], start=1)
        )
        content = f"""民事起诉状

原告：{context['plaintiff_name']}，{context['plaintiff_gender']}，{context['plaintiff_birth_date_cn']}出生，{context['plaintiff_ethnicity']}，身份证号码：{context['plaintiff_id_number']}，住{context['plaintiff_address']}，联系电话：{context['plaintiff_phone']}。
{defendant_block}

诉讼请求：
1. 请求判令被告支付拖欠劳务报酬{context['unpaid_amount']}元（{context['unpaid_amount_cn']}）；
2. 请求判令被告承担本案诉讼费用。

事实与理由：
{context['facts_reason_text']}

证据目录：
{evidence_block or '暂无证据材料。'}

此致
{context['court_name']}
"""
        return {"document_type": "complaint", "title": "民事起诉状", "content": content}

    def _support_prosecution_letter(self, context: dict) -> dict:
        content = f"""支持起诉申请书

申请人：{context['plaintiff_name']}
案由：{context['case_cause']}

申请事项：
请求依法对申请人追索劳务报酬纠纷案件予以支持起诉。

事实概述：
{context['facts_reason_text']}

欠付金额：{context['unpaid_amount']}元（{context['unpaid_amount_cn']}）。
"""
        return {
            "document_type": "support_prosecution",
            "title": "支持起诉申请书",
            "content": content,
        }
