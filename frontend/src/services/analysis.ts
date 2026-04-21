import http from "./http";

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface EntityGroup {
  persons: string[];
  companies: string[];
  amounts: string[];
  amount_total_estimate: number;
  dates: string[];
  addresses: string[];
  projects: string[];
  phones: string[];
  id_cards: string[];
  law_refs: string[];
}

export interface RelatedLawHit {
  id: string;
  article_no: string;
  law_name: string;
  title?: string | null;
  content: string;
  score: number;
  reason: string;
  scenario_tags: string[];
  matched_terms: string[];
}

export interface CaseRiskHint {
  label: string;
  triggered: boolean;
  detail: string;
}

export interface CaseTextAnalyzeRequest {
  title?: string;
  text: string;
  people_count: number;
  repeat_defendant_count: number;
  top_k_laws: number;
  persist_to_corpus: boolean;
  source_ref?: string;
  prefer_llm: boolean;
}

export interface CaseTextAnalyzeResponse {
  case_type: string;
  summary: string;
  entities: EntityGroup;
  matched_laws: RelatedLawHit[];
  risk_hints: CaseRiskHint[];
  persisted_case_id?: string | null;
  classify_mode: string;
  entity_mode: string;
  law_link_mode: string;
}

export async function analyzeCaseText(payload: CaseTextAnalyzeRequest) {
  const response = await http.post<ApiResponse<CaseTextAnalyzeResponse>>(
    "/analysis/text",
    payload
  );
  return response.data.data;
}
