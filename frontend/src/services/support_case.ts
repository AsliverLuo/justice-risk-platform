import { mockWorkflowSteps } from "../modules/supportProsecution/mock";
import http from "./http";
import type {
  DocumentResult,
  SupportCaseDetail,
  SupportCaseFormData,
  SupportProsecutionCaseCreatePayload,
  WorkflowStep,
} from "../modules/supportProsecution/types";

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

const LATEST_CASE_ID_KEY = "support_prosecution_latest_case_id";

function resolveCaseId(caseId: string): string {
  if (/^\d+$/.test(caseId)) {
    return caseId;
  }
  return localStorage.getItem(LATEST_CASE_ID_KEY) || caseId;
}

function toBackendPayload(formData: SupportCaseFormData): SupportProsecutionCaseCreatePayload {
  return {
    applicant: {
      name: formData.applicantName,
      gender: "",
      birth_date: formData.birthDate,
      ethnicity: "",
      id_number: formData.idCard,
      phone: formData.phone,
      hukou_address: formData.householdAddress,
      current_address: formData.householdAddress,
      id_card_front: "",
      id_card_back: "",
      signature_file: "",
      has_agent: Boolean(formData.entrustmentInfo),
      agent_info: formData.entrustmentInfo || null,
    },
    work_info: {
      work_start_date: formData.workStartDate,
      work_end_date: formData.workEndDate,
      actual_work_days: 0,
      project_name: formData.projectName,
      work_address: formData.workAddress,
      job_type: "",
      agreed_wage_standard: formData.wageCalculation || "",
      total_wage_due: formData.wageAmount,
      paid_amount: 0,
      unpaid_amount: formData.wageAmount,
      wage_calc_desc: formData.wageCalculation || "",
      employer_name: formData.defendantName,
      employer_phone: formData.defendantPhone || "",
      has_repeated_demand: false,
      demand_desc: "",
    },
    defendants: [
      {
        defendant_type: "company",
        name: formData.defendantName,
        credit_code_or_id_number: "",
        phone: formData.defendantPhone || "",
        address: formData.workAddress,
        legal_representative: "",
        legal_representative_title: "",
        role_type: "直接雇佣人",
        is_actual_controller: false,
        has_payment_promise: false,
        project_relation_desc: `与${formData.projectName}欠薪事项相关`,
      },
    ],
    evidences: [],
    document_options: {
      court_name: "",
      case_cause: "劳务合同纠纷",
      apply_support_prosecution: true,
      claim_litigation_cost: true,
      document_types: ["complaint", "support_prosecution"],
    },
  };
}

function fromBackendDetail(data: any): SupportCaseDetail {
  return {
    caseId: String(data.case_id),
    formData: {
      applicantName: data.applicant?.name || "",
      birthDate: data.applicant?.birth_date || "",
      age: 0,
      householdAddress: data.applicant?.hukou_address || "",
      idCard: data.applicant?.id_number || "",
      phone: data.applicant?.phone || "",
      workStartDate: data.work_info?.work_start_date || "",
      workEndDate: data.work_info?.work_end_date || "",
      projectName: data.work_info?.project_name || "",
      streetName: "",
      workAddress: data.work_info?.work_address || "",
      defendantName: data.defendants?.[0]?.name || data.work_info?.employer_name || "",
      defendantPhone: data.defendants?.[0]?.phone || data.work_info?.employer_phone || "",
      wageAmount: data.work_info?.unpaid_amount || 0,
      wageCalculation: data.work_info?.wage_calc_desc || "",
      entrustmentInfo: data.applicant?.agent_info || "",
    },
    evidenceFiles: (data.evidences || []).map((item: any) => ({
      uid: String(item.id),
      name: item.description || item.file_path || "证据材料",
      type: item.evidence_type,
      url: item.file_path,
    })),
    status: "submitted",
    createdAt: "",
  };
}

export async function createSupportCase(
  formData: SupportCaseFormData
): Promise<SupportCaseDetail> {
  const response = await http.post<ApiResponse<{ case_id: number }>>(
    "/support-prosecution/cases",
    toBackendPayload(formData)
  );
  const caseId = String(response.data.data.case_id);
  localStorage.setItem(LATEST_CASE_ID_KEY, caseId);
  return {
    caseId,
    formData,
    evidenceFiles: [],
    status: "submitted",
    createdAt: "",
  };
}

export async function getSupportCaseDetail(
  caseId: string
): Promise<SupportCaseDetail> {
  const resolvedCaseId = resolveCaseId(caseId);
  const response = await http.get<ApiResponse<any>>(
    `/support-prosecution/cases/${resolvedCaseId}`
  );
  return fromBackendDetail(response.data.data);
}

export async function generateDocuments(
  caseId: string
): Promise<DocumentResult> {
  const resolvedCaseId = resolveCaseId(caseId);
  await http.post<ApiResponse<any>>(
    `/document-gen/support-prosecution/cases/${resolvedCaseId}`,
    {
      document_types: ["complaint", "support_prosecution"],
    }
  );
  return {
    caseId: resolvedCaseId,
    complaintGenerated: true,
    supportLetterGenerated: true,
  };
}

export async function getWorkflowStatus(
  caseId: string
): Promise<WorkflowStep[]> {
  console.log("当前查询案件流程状态，caseId:", caseId);

  return Promise.resolve(mockWorkflowSteps);
}
