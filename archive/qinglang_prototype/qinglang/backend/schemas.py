from pydantic import BaseModel
from typing import List, Optional


class ApplicantInfo(BaseModel):
    name: str
    gender: str
    birth_date: str
    ethnicity: str
    id_number: str
    phone: str
    hukou_address: str
    current_address: str
    id_card_front: str
    id_card_back: str
    signature_file: str
    has_agent: bool
    agent_info: Optional[str] = None


class WorkInfo(BaseModel):
    work_start_date: str
    work_end_date: str
    actual_work_days: int
    project_name: str
    work_address: str
    job_type: str
    agreed_wage_standard: str
    total_wage_due: float
    paid_amount: float
    unpaid_amount: float
    wage_calc_desc: str
    employer_name: str
    employer_phone: str
    has_repeated_demand: bool
    demand_desc: str


class DefendantInfo(BaseModel):
    defendant_type: str
    name: str
    credit_code_or_id_number: str
    phone: str
    address: str
    legal_representative: str
    legal_representative_title: str
    role_type: str
    is_actual_controller: bool
    has_payment_promise: bool
    project_relation_desc: str


class EvidenceInfo(BaseModel):
    evidence_type: str
    file_path: str
    description: str


class DocumentOptions(BaseModel):
    court_name: str
    case_cause: str
    apply_support_prosecution: bool
    claim_litigation_cost: bool
    document_types: List[str]


class CaseCreate(BaseModel):
    applicant: ApplicantInfo
    work_info: WorkInfo
    defendants: List[DefendantInfo]
    evidences: List[EvidenceInfo]
    document_options: DocumentOptions
