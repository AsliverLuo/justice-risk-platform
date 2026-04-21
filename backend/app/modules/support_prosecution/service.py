from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.support_prosecution.context_builders import build_complaint_context
from app.modules.support_prosecution.repository import SupportProsecutionRepository
from app.modules.support_prosecution.schemas import CaseCreate


class SupportProsecutionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SupportProsecutionRepository(db)

    def create_case(self, data: CaseCreate) -> dict:
        applicant, case_record = self.repo.create_case(data)
        self.db.commit()
        return {
            "message": "案件提交成功，并已保存到数据库",
            "applicant_id": applicant.id,
            "case_id": case_record.id,
            "received_data": data.model_dump(),
        }

    def get_case_detail(self, case_id: int) -> dict:
        case_record = self.repo.get_case(case_id)
        if not case_record:
            raise HTTPException(status_code=404, detail="案件不存在")

        applicant = self.repo.get_applicant(case_record.applicant_id)
        if not applicant:
            raise HTTPException(status_code=404, detail="申请人信息不存在")

        document_option = self.repo.get_document_option(case_id)
        document_types = []
        if document_option and document_option.document_types:
            document_types = [
                item.strip()
                for item in document_option.document_types.split(",")
                if item.strip()
            ]

        return {
            "case_id": case_record.id,
            "applicant_id": applicant.id,
            "applicant": {
                "name": applicant.name,
                "gender": applicant.gender,
                "birth_date": applicant.birth_date,
                "ethnicity": applicant.ethnicity,
                "id_number": applicant.id_number,
                "phone": applicant.phone,
                "hukou_address": applicant.hukou_address,
                "current_address": applicant.current_address,
                "id_card_front": applicant.id_card_front,
                "id_card_back": applicant.id_card_back,
                "signature_file": applicant.signature_file,
                "has_agent": applicant.has_agent,
                "agent_info": applicant.agent_info,
            },
            "work_info": {
                "work_start_date": case_record.work_start_date,
                "work_end_date": case_record.work_end_date,
                "actual_work_days": case_record.actual_work_days,
                "project_name": case_record.project_name,
                "work_address": case_record.work_address,
                "job_type": case_record.job_type,
                "agreed_wage_standard": case_record.agreed_wage_standard,
                "total_wage_due": case_record.total_wage_due,
                "paid_amount": case_record.paid_amount,
                "unpaid_amount": case_record.unpaid_amount,
                "wage_calc_desc": case_record.wage_calc_desc,
                "employer_name": case_record.employer_name,
                "employer_phone": case_record.employer_phone,
                "has_repeated_demand": case_record.has_repeated_demand,
                "demand_desc": case_record.demand_desc,
            },
            "defendants": [
                {
                    "id": item.id,
                    "defendant_type": item.defendant_type,
                    "name": item.name,
                    "credit_code_or_id_number": item.credit_code_or_id_number,
                    "phone": item.phone,
                    "address": item.address,
                    "legal_representative": item.legal_representative,
                    "legal_representative_title": item.legal_representative_title,
                    "role_type": item.role_type,
                    "is_actual_controller": item.is_actual_controller,
                    "has_payment_promise": item.has_payment_promise,
                    "project_relation_desc": item.project_relation_desc,
                }
                for item in self.repo.list_defendants(case_id)
            ],
            "evidences": [
                {
                    "id": item.id,
                    "evidence_type": item.evidence_type,
                    "file_path": item.file_path,
                    "description": item.description,
                }
                for item in self.repo.list_evidences(case_id)
            ],
            "document_options": {
                "court_name": document_option.court_name if document_option else "",
                "case_cause": document_option.case_cause if document_option else "",
                "apply_support_prosecution": (
                    document_option.apply_support_prosecution if document_option else False
                ),
                "claim_litigation_cost": (
                    document_option.claim_litigation_cost if document_option else False
                ),
                "document_types": document_types,
            },
        }

    def get_complaint_context(self, case_id: int) -> dict:
        return build_complaint_context(self.db, case_id)
