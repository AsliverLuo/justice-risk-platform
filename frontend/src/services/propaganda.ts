import http from "./http";

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface PropagandaArticle {
  id: string;
  article_code: string;
  title: string;
  summary?: string | null;
  content: string;
  risk_types: string[];
  scenario_tags: string[];
  related_law_names: string[];
  hot_score: number;
}

export interface PropagandaPush {
  id: string;
  title: string;
  summary?: string | null;
  recommendation_score: number;
  matched_risk_types: string[];
  matched_scenario_tags: string[];
  related_law_names: string[];
  match_reason: string;
}

export interface PropagandaRecommendResponse {
  items: PropagandaPush[];
  articles: PropagandaArticle[];
  resolved_scope_type: string;
  resolved_scope_id: string;
  resolved_scope_name: string;
  resolved_risk_type: string;
  used_context_tags: string[];
  used_related_law_names: string[];
  source_mode: string;
}

export interface PropagandaRecommendRequest {
  scope_type: string;
  scope_id: string;
  risk_type: string;
  context_tags: string[];
  related_law_names: string[];
  limit: number;
  persist: boolean;
  dashboard_visible: boolean;
}

export async function recommendPropaganda(payload: PropagandaRecommendRequest) {
  const response = await http.post<ApiResponse<PropagandaRecommendResponse>>(
    "/propaganda/recommend",
    payload
  );
  return response.data.data;
}
