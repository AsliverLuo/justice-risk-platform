import http from "./http";

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface RecommendationLawReference {
  id?: string | null;
  article_no?: string | null;
  law_name: string;
  title?: string | null;
  content: string;
  score: number;
}

export interface GovernanceRecommendation {
  id: string;
  scope_type: string;
  scope_id: string;
  scope_name: string;
  risk_type: string;
  recommendation_level: string;
  title: string;
  summary: string;
  action_items: string[];
  departments: string[];
  follow_up_metrics: string[];
  related_laws: RecommendationLawReference[];
  matched_template_codes: string[];
  source_mode: string;
}

export interface RecommendationGenerateResponse {
  recommendation: GovernanceRecommendation;
  related_laws: RecommendationLawReference[];
  mode: string;
}

export interface RecommendationGenerateRequest {
  scope_type: string;
  scope_id: string;
  risk_type: string;
  context_summary: string;
  case_summaries: string[];
  template_limit: number;
  case_limit: number;
  law_top_k: number;
  prefer_llm: boolean;
  persist: boolean;
  dashboard_visible: boolean;
}

export async function generateRecommendation(payload: RecommendationGenerateRequest) {
  const response = await http.post<ApiResponse<RecommendationGenerateResponse>>(
    "/recommendations/generate",
    payload
  );
  return response.data.data;
}
