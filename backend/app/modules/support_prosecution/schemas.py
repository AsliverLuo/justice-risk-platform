from __future__ import annotations

from pydantic import BaseModel, Field


class ApplicantInfo(BaseModel):
    name: str
    gender: str
    birth_date: str
    ethnicity: str
    id_number: str
    phone: str
    hukou_address: str
    current_address: str
    id_card_front: str = ""
    id_card_back: str = ""
    signature_file: str = ""
    has_agent: bool = False
    agent_info: str | None = None


class WorkInfo(BaseModel):
    work_start_date: str
    work_end_date: str
    actual_work_days: int = Field(ge=0)
    project_name: str
    work_address: str
    job_type: str
    agreed_wage_standard: str
    total_wage_due: float = Field(ge=0)
    paid_amount: float = Field(ge=0)
    unpaid_amount: float = Field(ge=0)
    wage_calc_desc: str
    employer_name: str
    employer_phone: str
    has_repeated_demand: bool = False
    demand_desc: str = ""


class DefendantInfo(BaseModel):
    defendant_type: str
    name: str
    credit_code_or_id_number: str
    phone: str = ""
    address: str = ""
    legal_representative: str = ""
    legal_representative_title: str = ""
    role_type: str = ""
    is_actual_controller: bool = False
    has_payment_promise: bool = False
    project_relation_desc: str = ""


class EvidenceInfo(BaseModel):
    evidence_type: str
    file_path: str = ""
    description: str = ""


class DocumentOptions(BaseModel):
    court_name: str
    case_cause: str = "劳务合同纠纷"
    apply_support_prosecution: bool = True
    claim_litigation_cost: bool = True
    document_types: list[str] = Field(default_factory=list)


class CaseCreate(BaseModel):
    applicant: ApplicantInfo
    work_info: WorkInfo
    defendants: list[DefendantInfo] = Field(default_factory=list)
    evidences: list[EvidenceInfo] = Field(default_factory=list)
    document_options: DocumentOptions


class CaseCreateResponse(BaseModel):
    message: str
    applicant_id: int
    case_id: int
    received_data: dict


class CaseDetail(BaseModel):
    case_id: int
    applicant_id: int
    applicant: dict
    work_info: dict
    defendants: list[dict]
    evidences: list[dict]
    document_options: dict


class ComplaintContext(BaseModel):
    case_id: int
    plaintiff_name: str
    plaintiff_gender: str
    plaintiff_birth_date: str
    plaintiff_birth_date_cn: str
    plaintiff_ethnicity: str
    plaintiff_id_number: str
    plaintiff_address: str
    plaintiff_phone: str
    court_name: str
    case_cause: str
    unpaid_amount: float
    unpaid_amount_cn: str
    total_wage_due: float
    agreed_wage_standard: str
    actual_work_days: int
    project_name: str
    job_type: str
    work_start_date_cn: str
    work_end_date_cn: str
    defendant_count: int
    defendant_texts: list[str]
    facts_reason_text: str
    evidence_summary: list[dict]
