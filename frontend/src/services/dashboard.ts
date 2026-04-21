import http from "./http";

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface CaseCorpusDetail {
  id: string;
  source_type: string;
  source_ref?: string | null;
  title: string;
  case_no?: string | null;
  full_text: string;
  case_type?: string | null;
  plaintiff_summary?: string | null;
  defendant_summary?: string | null;
  claim_summary?: string | null;
  focus_summary?: string | null;
  fact_summary?: string | null;
  judgment_summary?: string | null;
  province?: string | null;
  city?: string | null;
  occurred_at?: string | null;
  entities: {
    persons?: string[];
    companies?: string[];
    amounts?: string[];
    amount_total_estimate?: number;
    dates?: string[];
    addresses?: string[];
    projects?: string[];
    [key: string]: unknown;
  };
  cited_laws: string[];
  extra_meta: {
    street?: string;
    street_name?: string;
    risk_level?: "red" | "orange" | "yellow" | "blue";
    risk_score?: number;
    amount?: number;
    total_amount?: number;
    people_count?: number;
    status?: string;
    tags?: string[];
    evidence?: string[];
    warning_features?: string[];
    recommended_actions?: string[];
    propaganda_topics?: string[];
    [key: string]: unknown;
  };
}

export interface WorkflowCaseItem {
  id: string;
  title: string;
  caseType: string;
  street: string;
  riskLevel: "red" | "orange" | "yellow" | "blue";
  riskScore: number;
  status: string;
  amount: number;
  peopleCount: number;
  occurredAt?: string | null;
  claimants: string[];
  defendants: string[];
  summary: string;
  tags: string[];
  evidence: string[];
  warningFeatures: string[];
  recommendedActions: string[];
  propagandaTopics: string[];
  stage: string;
}

export interface WorkflowStageOption {
  key: string;
  label: string;
  count: number;
}

export interface WorkflowCasesResponse {
  stage: string;
  stageLabel: string;
  stageOptions: WorkflowStageOption[];
  items: WorkflowCaseItem[];
}

export interface DefendantCasesResponse {
  defendant: string;
  totalCases: number;
  totalAmount: number;
  riskSummary: Record<string, number>;
  items: WorkflowCaseItem[];
}

export interface CommunityStreetItem {
  key: string;
  name: string;
  region: string;
  caseCount: number;
  peopleCount: number;
  totalAmount: number;
  riskLevel: "red" | "orange" | "yellow" | "blue";
  highRiskCount: number;
  topCaseType: string;
  tags: string[];
}

export interface CommunityStreetsResponse {
  region: string;
  totalStreets: number;
  items: CommunityStreetItem[];
}

export interface StreetCasesResponse {
  street: string;
  totalCases: number;
  totalAmount: number;
  riskSummary: Record<string, number>;
  items: WorkflowCaseItem[];
}

export interface StreetRiskDimension {
  name: string;
  level: "red" | "orange" | "yellow" | "blue";
  description: string;
}

export interface StreetHighFrequencyType {
  caseType: string;
  count: number;
  ratio: number;
}

export interface StreetProfileResponse {
  street: string;
  sourceMode: "llm" | "rule";
  profile: {
    summary: string;
    riskLevel: "red" | "orange" | "yellow" | "blue";
    totalCases: number;
    peopleCount: number;
    totalAmount: number;
    highFrequencyTypes: StreetHighFrequencyType[];
    riskDistribution: Record<string, number>;
    topDefendants: Array<{ name: string; count: number }>;
    dimensions: StreetRiskDimension[];
  };
  governanceSuggestions: Array<{
    title: string;
    summary: string;
    actions: string[];
    relatedPolicies: string[];
  }>;
  propagandaPlans: Array<{
    title: string;
    targetAudience: string;
    content: string;
    channels: string[];
    relatedLaws: string[];
  }>;
}

export async function getWorkflowCases(stage: string) {
  const response = await http.get<ApiResponse<WorkflowCasesResponse>>(
    "/dashboard/workflow-cases",
    { params: { stage } }
  );
  return response.data.data;
}

export async function getDefendantCases(defendant: string) {
  const response = await http.get<ApiResponse<DefendantCasesResponse>>(
    "/dashboard/defendant-cases",
    { params: { defendant } }
  );
  return response.data.data;
}

export async function getCommunityStreets() {
  const response = await http.get<ApiResponse<CommunityStreetsResponse>>(
    "/dashboard/community-streets"
  );
  return response.data.data;
}

export async function getStreetCases(street: string) {
  const response = await http.get<ApiResponse<StreetCasesResponse>>(
    "/dashboard/street-cases",
    { params: { street } }
  );
  return response.data.data;
}

export async function getStreetProfile(street: string, preferLlm = true) {
  const response = await http.get<ApiResponse<StreetProfileResponse>>(
    "/dashboard/street-profile",
    { params: { street, prefer_llm: preferLlm } }
  );
  return response.data.data;
}

export async function getCaseCorpusDetail(caseId: string) {
  const response = await http.get<ApiResponse<CaseCorpusDetail>>(
    `/analysis/corpus/${caseId}`
  );
  return response.data.data;
}
