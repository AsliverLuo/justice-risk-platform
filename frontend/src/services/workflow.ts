import http from "./http";

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface WorkflowTaskCreatePayload {
  task_name: string;
  alert_id?: string | null;
  alert_title?: string | null;
  street: string;
  risk_level: string;
  case_type: string;
  main_unit: string;
  deadline: string;
  actions: string[];
  description: string;
  stage: string;
  extra_meta?: WorkflowTaskExtraMeta;
}

export interface WorkflowEvaluationCard {
  summary: string;
  before: {
    riskLevel: string;
    riskLevelText: string;
    riskScore: number;
  };
  after: {
    riskLevel: string;
    riskLevelText: string;
    riskScore: number;
  };
  riskChange: {
    levelChanged: boolean;
    scoreDrop: number;
    conclusion: string;
  };
  eventChange: {
    sameTypeNewCaseDropRate: number;
    repeatSubjectTriggered: boolean;
    conclusion: string;
  };
  governanceEffect: {
    onTimeCompletionRate: number;
    jointHandlingCompletionRate: number;
    conclusion: string;
  };
  propagandaEffect: {
    coveragePeople: number;
    readRate: number;
    surveySatisfaction: number;
    conclusion: string;
  };
}

export interface WorkflowTaskExtraMeta {
  source?: string;
  evaluation_card?: WorkflowEvaluationCard;
  [key: string]: unknown;
}

export interface WorkflowTaskItem extends WorkflowTaskCreatePayload {
  id: string;
  feedback?: string | null;
  evaluation?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowTaskListResponse {
  stage: string;
  stage_label: string;
  stage_options: Array<{ key: string; label: string; count: number }>;
  total: number;
  items: WorkflowTaskItem[];
}

export async function createWorkflowTask(payload: WorkflowTaskCreatePayload) {
  const response = await http.post<ApiResponse<WorkflowTaskItem>>("/workflow/tasks", payload);
  return response.data.data;
}

export async function listWorkflowTasks(stage: string) {
  const response = await http.get<ApiResponse<WorkflowTaskListResponse>>("/workflow/tasks", {
    params: { stage },
  });
  return response.data.data;
}

export async function updateWorkflowTaskStage(
  taskId: string,
  payload: { stage: string; feedback?: string; evaluation?: string }
) {
  const response = await http.patch<ApiResponse<WorkflowTaskItem>>(`/workflow/tasks/${taskId}/stage`, payload);
  return response.data.data;
}
