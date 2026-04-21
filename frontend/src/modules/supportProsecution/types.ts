export interface SupportCaseFormData {
  applicantName: string;
  birthDate: string;
  age: number;
  householdAddress: string;
  idCard: string;
  phone: string;
  workStartDate: string;
  workEndDate: string;
  projectName: string;
  streetName: string;
  workAddress: string;
  defendantName: string;
  defendantPhone?: string;
  wageAmount: number;
  wageCalculation?: string;
  entrustmentInfo?: string;
}

export interface EvidenceFile {
  uid: string;
  name: string;
  type: string;
  url?: string;
}

export interface SupportCaseDetail {
  caseId: string;
  formData: SupportCaseFormData;
  evidenceFiles: EvidenceFile[];
  status: string;
  createdAt: string;
}

export interface DocumentResult {
  caseId: string;
  complaintGenerated: boolean;
  supportLetterGenerated: boolean;
  complaintUrl?: string;
  supportLetterUrl?: string;
}

export interface WorkflowStep {
  key: string;
  title: string;
  status: "wait" | "process" | "finish" | "error";
  time?: string;
}

export interface SupportProsecutionCaseCreatePayload {
  applicant: {
    name: string;
    gender: string;
    birth_date: string;
    ethnicity: string;
    id_number: string;
    phone: string;
    hukou_address: string;
    current_address: string;
    id_card_front: string;
    id_card_back: string;
    signature_file: string;
    has_agent: boolean;
    agent_info?: string | null;
  };
  work_info: {
    work_start_date: string;
    work_end_date: string;
    actual_work_days: number;
    project_name: string;
    work_address: string;
    job_type: string;
    agreed_wage_standard: string;
    total_wage_due: number;
    paid_amount: number;
    unpaid_amount: number;
    wage_calc_desc: string;
    employer_name: string;
    employer_phone: string;
    has_repeated_demand: boolean;
    demand_desc: string;
  };
  defendants: Array<{
    defendant_type: string;
    name: string;
    credit_code_or_id_number: string;
    phone: string;
    address: string;
    legal_representative: string;
    legal_representative_title: string;
    role_type: string;
    is_actual_controller: boolean;
    has_payment_promise: boolean;
    project_relation_desc: string;
  }>;
  evidences: Array<{
    evidence_type: string;
    file_path: string;
    description: string;
  }>;
  document_options: {
    court_name: string;
    case_cause: string;
    apply_support_prosecution: boolean;
    claim_litigation_cost: boolean;
    document_types: string[];
  };
}
