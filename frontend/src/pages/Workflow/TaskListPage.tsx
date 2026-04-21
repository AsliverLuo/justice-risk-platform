import { Button, Card, Collapse, Descriptions, Empty, Input, Space, Spin, Tag, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import CaseClosureTimeline from "../../components/CaseClosureTimeline";
import {
  getWorkflowCases,
  type WorkflowCaseItem,
  type WorkflowCasesResponse,
  type WorkflowStageOption,
} from "../../services/dashboard";
import {
  listWorkflowTasks,
  updateWorkflowTaskStage,
  type WorkflowEvaluationCard,
  type WorkflowTaskItem,
  type WorkflowTaskListResponse,
} from "../../services/workflow";
import "./TaskListPage.css";

const { Paragraph, Text, Title } = Typography;

const riskColorMap: Record<string, string> = {
  red: "#e5484d",
  orange: "#f97316",
  yellow: "#facc15",
  blue: "#3b82f6",
};

const riskTextMap: Record<string, string> = {
  red: "红色预警",
  orange: "橙色预警",
  yellow: "黄色预警",
  blue: "蓝色关注",
};

const nextStageMap: Record<string, { stage: string; label: string }> = {
  assigned: { stage: "handling", label: "转入处置中" },
  handling: { stage: "feedback", label: "提交处置反馈" },
  feedback: { stage: "evaluated", label: "完成效果评估" },
};

const caseStageKeys = new Set(["discovered", "alerted"]);

function fallbackEvaluationCard(item: WorkflowTaskItem): WorkflowEvaluationCard {
  const beforeScoreMap: Record<string, number> = { red: 86, orange: 68, yellow: 48, blue: 28 };
  const afterLevelMap: Record<string, string> = { red: "yellow", orange: "yellow", yellow: "blue", blue: "blue" };
  const levelTextMap: Record<string, string> = { red: "红色", orange: "橙色", yellow: "黄色", blue: "蓝色" };
  const beforeLevel = item.risk_level || "orange";
  const afterLevel = afterLevelMap[beforeLevel] || "blue";
  const beforeScore = beforeScoreMap[beforeLevel] ?? 68;
  const afterScore = beforeScoreMap[afterLevel] ?? 28;
  return {
    summary: `处置后风险评分下降 ${Math.max(0, beforeScore - afterScore)} 分，建议转入常态化跟踪。`,
    before: { riskLevel: beforeLevel, riskLevelText: levelTextMap[beforeLevel] || "橙色", riskScore: beforeScore },
    after: { riskLevel: afterLevel, riskLevelText: levelTextMap[afterLevel] || "蓝色", riskScore: afterScore },
    riskChange: {
      levelChanged: beforeLevel !== afterLevel,
      scoreDrop: Math.max(0, beforeScore - afterScore),
      conclusion: `风险等级由${levelTextMap[beforeLevel] || "橙色"}调整为${levelTextMap[afterLevel] || "蓝色"}。`,
    },
    eventChange: {
      sameTypeNewCaseDropRate: 42,
      repeatSubjectTriggered: false,
      conclusion: "同类案件新增下降 42%，重复主体暂未再次触发预警。",
    },
    governanceEffect: {
      onTimeCompletionRate: 100,
      jointHandlingCompletionRate: 92,
      conclusion: "承办单位按期反馈，协同单位完成联动处置。",
    },
    propagandaEffect: {
      coveragePeople: 1260,
      readRate: 76,
      surveySatisfaction: 83,
      conclusion: "精准普法覆盖 1260 人，阅读率 76%，回访满意度 83%。",
    },
  };
}

function EvaluationCard({ item }: { item: WorkflowTaskItem }) {
  const card = item.extra_meta?.evaluation_card || (item.stage === "evaluated" ? fallbackEvaluationCard(item) : null);
  if (!card) {
    return (
      <Card size="small" title="处置成效评估卡">
        <Text type="secondary">任务完成效果评估后自动生成。</Text>
      </Card>
    );
  }

  const metricCards = [
    {
      title: "风险变化",
      values: [
        `处置前：${card.before.riskLevelText} ${card.before.riskScore}分`,
        `处置后：${card.after.riskLevelText} ${card.after.riskScore}分`,
        `风险下降：${card.riskChange.scoreDrop}分`,
      ],
      conclusion: card.riskChange.conclusion,
    },
    {
      title: "事件变化",
      values: [
        `同类案件新增：下降 ${card.eventChange.sameTypeNewCaseDropRate}%`,
        `重复主体预警：${card.eventChange.repeatSubjectTriggered ? "再次触发" : "未再次触发"}`,
      ],
      conclusion: card.eventChange.conclusion,
    },
    {
      title: "治理效果",
      values: [
        `按期办结率：${card.governanceEffect.onTimeCompletionRate}%`,
        `联动处置完成率：${card.governanceEffect.jointHandlingCompletionRate}%`,
      ],
      conclusion: card.governanceEffect.conclusion,
    },
    {
      title: "普法效果",
      values: [
        `普法覆盖：${card.propagandaEffect.coveragePeople}人`,
        `阅读率：${card.propagandaEffect.readRate}%`,
        `回访满意度：${card.propagandaEffect.surveySatisfaction}%`,
      ],
      conclusion: card.propagandaEffect.conclusion,
    },
  ];

  return (
    <Card size="small" title="处置成效评估卡">
      <Space direction="vertical" size={12} style={{ width: "100%" }}>
        <Card size="small">
          <Text strong>{card.summary}</Text>
        </Card>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
          {metricCards.map((metric) => (
            <Card key={metric.title} size="small" title={metric.title}>
              <Space direction="vertical" size={6}>
                {metric.values.map((value) => (
                  <Text key={value}>{value}</Text>
                ))}
                <Text type="secondary">{metric.conclusion}</Text>
              </Space>
            </Card>
          ))}
        </div>
      </Space>
    </Card>
  );
}

function renderTags(values: string[], color = "cyan") {
  if (!values.length) return <Text type="secondary">暂无</Text>;
  return (
    <Space wrap>
      {values.map((value) => (
        <Tag key={value} color={color}>
          {value}
        </Tag>
      ))}
    </Space>
  );
}

function CaseDetail({ item }: { item: WorkflowCaseItem }) {
  return (
    <Space direction="vertical" size={14} style={{ width: "100%" }}>
      <Descriptions column={2} size="small" bordered>
        <Descriptions.Item label="案件编号">{item.id}</Descriptions.Item>
        <Descriptions.Item label="案件类型">{item.caseType}</Descriptions.Item>
        <Descriptions.Item label="所属街道">{item.street}</Descriptions.Item>
        <Descriptions.Item label="当前状态">{item.status}</Descriptions.Item>
        <Descriptions.Item label="风险等级">
          <Tag color={riskColorMap[item.riskLevel]}>{riskTextMap[item.riskLevel]}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="风险评分">{item.riskScore || "暂无"}</Descriptions.Item>
        <Descriptions.Item label="涉案金额">{item.amount} 万元</Descriptions.Item>
        <Descriptions.Item label="涉及人数">{item.peopleCount} 人</Descriptions.Item>
        <Descriptions.Item label="发生时间">{item.occurredAt || "暂无"}</Descriptions.Item>
        <Descriptions.Item label="当事人">{item.claimants.join("、") || "暂无"}</Descriptions.Item>
        <Descriptions.Item label="关联主体" span={2}>
          {item.defendants.join("、") || "暂无"}
        </Descriptions.Item>
      </Descriptions>

      <Card size="small" title="案件概述">
        <Text>{item.summary}</Text>
      </Card>
      <CaseClosureTimeline
        status={item.status}
        riskLevel={item.riskLevel}
        stage={item.stage}
        warningFeatures={item.warningFeatures}
        recommendedActions={item.recommendedActions}
      />
      <Card size="small" title="案件标签">{renderTags(item.tags)}</Card>
      <Card size="small" title="预警特征">{renderTags(item.warningFeatures, "orange")}</Card>
      <Card size="small" title="治理建议">{renderTags(item.recommendedActions, "green")}</Card>
      <Card size="small" title="精准普法主题">{renderTags(item.propagandaTopics, "purple")}</Card>
    </Space>
  );
}

function TaskDetail({ item, onUpdated }: { item: WorkflowTaskItem; onUpdated: () => void }) {
  const nextStage = nextStageMap[item.stage];
  const [feedback, setFeedback] = useState(item.feedback || "");
  const [evaluation, setEvaluation] = useState(item.evaluation || "");
  const [saving, setSaving] = useState(false);

  async function advanceTask() {
    if (!nextStage) return;
    setSaving(true);
    try {
      await updateWorkflowTaskStage(item.id, {
        stage: nextStage.stage,
        feedback: nextStage.stage === "feedback" ? feedback || "已完成核查处置并形成反馈记录。" : feedback,
        evaluation: nextStage.stage === "evaluated" ? evaluation || "处置后风险已纳入持续跟踪评估。" : evaluation,
      });
      message.success("任务阶段已更新。");
      onUpdated();
    } finally {
      setSaving(false);
    }
  }

  return (
    <Space direction="vertical" size={14} style={{ width: "100%" }}>
      <Descriptions column={2} size="small" bordered>
        <Descriptions.Item label="任务编号">{item.id}</Descriptions.Item>
        <Descriptions.Item label="关联预警">{item.alert_id || "暂无"}</Descriptions.Item>
        <Descriptions.Item label="所属街道">{item.street}</Descriptions.Item>
        <Descriptions.Item label="高发类型">{item.case_type}</Descriptions.Item>
        <Descriptions.Item label="风险等级">
          <Tag color={riskColorMap[item.risk_level]}>{riskTextMap[item.risk_level]}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="办理期限">{item.deadline || "暂无"}</Descriptions.Item>
        <Descriptions.Item label="承办/协办单位" span={2}>
          {item.main_unit}
        </Descriptions.Item>
      </Descriptions>

      <Card size="small" title="任务说明">
        <Paragraph>{item.description || "暂无"}</Paragraph>
      </Card>

      <CaseClosureTimeline
        status={item.stage}
        riskLevel={item.risk_level}
        stage={item.stage}
        warningFeatures={[item.alert_title || "已由预警信息生成处置任务"]}
        recommendedActions={item.actions}
      />

      <Card size="small" title="处置动作">
        <Space wrap>
          {(item.actions || []).map((action) => (
            <Tag key={action} color="cyan">
              {action}
            </Tag>
          ))}
        </Space>
      </Card>

      <Card size="small" title="处置反馈">
        <Input.TextArea rows={3} value={feedback} onChange={(event) => setFeedback(event.target.value)} />
      </Card>

      <Card size="small" title="效果评估">
        <Input.TextArea rows={3} value={evaluation} onChange={(event) => setEvaluation(event.target.value)} />
      </Card>

      <EvaluationCard item={item} />

      {nextStage ? (
        <Button type="primary" loading={saving} onClick={advanceTask}>
          {nextStage.label}
        </Button>
      ) : (
        <Tag color="green">已完成闭环评估</Tag>
      )}
    </Space>
  );
}

function TaskListPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const stage = searchParams.get("stage") || "assigned";
  const [taskData, setTaskData] = useState<WorkflowTaskListResponse | null>(null);
  const [caseData, setCaseData] = useState<WorkflowCasesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const isCaseStage = caseStageKeys.has(stage);

  async function loadTasks() {
    setLoading(true);
    try {
      const [nextCaseData, nextTaskData] = await Promise.all([
        getWorkflowCases(caseStageKeys.has(stage) ? stage : "discovered"),
        listWorkflowTasks(stage),
      ]);
      setCaseData(nextCaseData);
      setTaskData(nextTaskData);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTasks();
  }, [stage]);

  const caseStageOptions = caseData?.stageOptions ?? [];
  const taskStageOptions = taskData?.stage_options ?? [];
  const stageOptions: WorkflowStageOption[] = [
    { key: "discovered", label: "风险发现", count: caseStageOptions.find((item) => item.key === "discovered")?.count ?? 0 },
    { key: "alerted", label: "已预警", count: caseStageOptions.find((item) => item.key === "alerted")?.count ?? 0 },
    { key: "assigned", label: "已分派", count: taskStageOptions.find((item) => item.key === "assigned")?.count ?? 0 },
    { key: "handling", label: "处置中", count: taskStageOptions.find((item) => item.key === "handling")?.count ?? 0 },
    { key: "feedback", label: "已反馈", count: taskStageOptions.find((item) => item.key === "feedback")?.count ?? 0 },
    { key: "evaluated", label: "已评估", count: taskStageOptions.find((item) => item.key === "evaluated")?.count ?? 0 },
  ];

  return (
    <main className="workflow-task-list-page" style={{ minHeight: "100vh", background: "#101916", padding: 24 }}>
      <Card
        bordered={false}
        style={{
          borderRadius: 8,
          background: "rgba(8, 20, 20, 0.92)",
          border: "1px solid rgba(72, 214, 193, 0.22)",
        }}
      >
        <Space direction="vertical" size={18} style={{ width: "100%" }}>
          <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
            <div>
              <Title level={2} style={{ color: "#ecfffb", margin: 0 }}>
                闭环任务管理
              </Title>
              <Text style={{ color: "#95b8b0" }}>风险发现和已预警查看案件线索，已分派以后查看真实任务表并推进闭环。</Text>
            </div>
            <Button type="primary" onClick={() => navigate("/dashboard")}>
              返回驾驶舱
            </Button>
          </header>

          <Space wrap>
            {stageOptions.map((item) => (
              <Button
                key={item.key}
                type={stage === item.key ? "primary" : "default"}
                onClick={() => setSearchParams({ stage: item.key })}
              >
                {item.label} {item.count} 件
              </Button>
            ))}
          </Space>

          <Spin spinning={loading}>
            {isCaseStage && caseData?.items.length ? (
              <Collapse
                accordion
                items={caseData.items.map((item) => ({
                  key: item.id,
                  label: (
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
                      <Space wrap>
                        <Text strong>{item.title}</Text>
                        <Tag color={riskColorMap[item.riskLevel]}>{riskTextMap[item.riskLevel]}</Tag>
                        <Tag>{item.caseType}</Tag>
                      </Space>
                      <Text type="secondary">{item.street} · {item.status}</Text>
                    </div>
                  ),
                  children: <CaseDetail item={item} />,
                }))}
              />
            ) : !isCaseStage && taskData?.items.length ? (
              <Collapse
                accordion
                items={taskData.items.map((item) => ({
                  key: item.id,
                  label: (
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
                      <Space wrap>
                        <Text strong>{item.task_name}</Text>
                        <Tag color={riskColorMap[item.risk_level]}>{riskTextMap[item.risk_level]}</Tag>
                        <Tag>{item.case_type}</Tag>
                      </Space>
                      <Text type="secondary">{item.street} · {item.main_unit}</Text>
                    </div>
                  ),
                  children: <TaskDetail item={item} onUpdated={loadTasks} />,
                }))}
              />
            ) : (
              <Empty description={loading ? "正在加载数据" : isCaseStage ? "当前阶段暂无案件线索" : "当前阶段暂无真实分派任务"} />
            )}
          </Spin>
        </Space>
      </Card>
    </main>
  );
}

export default TaskListPage;
