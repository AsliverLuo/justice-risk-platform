import type {
  DocumentResult,
  SupportCaseDetail,
  SupportCaseFormData,
  WorkflowStep,
} from "./types";

export const mockSupportCaseFormData: SupportCaseFormData = {
  applicantName: "张三",
  birthDate: "1990-05-12",
  age: 34,
  householdAddress: "广东省广州市天河区某街道某小区12号",
  idCard: "440106199005120011",
  phone: "13800138000",
  workStartDate: "2024-01-10",
  workEndDate: "2024-06-30",
  projectName: "某建设工程项目",
  streetName: "某街道",
  workAddress: "广州市天河区某施工工地",
  defendantName: "某建筑劳务公司",
  defendantPhone: "13900139000",
  wageAmount: 26800,
  wageCalculation: "按月工资和加班费用合计计算",
  entrustmentInfo: "委托检察机关依法支持起诉",
};

export const mockSupportCaseDetail: SupportCaseDetail = {
  caseId: "SC20260414001",
  formData: mockSupportCaseFormData,
  evidenceFiles: [
    {
      uid: "1",
      name: "身份证正反面.pdf",
      type: "identity",
      url: "/mock-files/id-card.pdf",
    },
    {
      uid: "2",
      name: "工资流水.pdf",
      type: "salary",
      url: "/mock-files/salary-record.pdf",
    },
    {
      uid: "3",
      name: "聊天记录截图.zip",
      type: "chat",
      url: "/mock-files/chat-record.zip",
    },
  ],
  status: "材料已提交",
  createdAt: "2026-04-14 10:30:00",
};

export const mockDocumentResult: DocumentResult = {
  caseId: "SC20260414001",
  complaintGenerated: true,
  supportLetterGenerated: true,
  complaintUrl: "/mock-files/complaint.docx",
  supportLetterUrl: "/mock-files/support-letter.docx",
};

export const mockWorkflowSteps: WorkflowStep[] = [
  {
    key: "accept",
    title: "申请接收",
    status: "finish",
    time: "2026-04-14 10:30:00",
  },
  {
    key: "review",
    title: "初步审查",
    status: "finish",
    time: "2026-04-14 14:00:00",
  },
  {
    key: "material",
    title: "材料补充",
    status: "process",
    time: "2026-04-15 09:20:00",
  },
  {
    key: "document",
    title: "文书生成",
    status: "wait",
  },
  {
    key: "approval",
    title: "检察审批",
    status: "wait",
  },
  {
    key: "court",
    title: "法院移送",
    status: "wait",
  },
  {
    key: "feedback",
    title: "跟踪反馈",
    status: "wait",
  },
];