import { Button, Card, Collapse, Descriptions, Empty, Space, Spin, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import CaseClosureTimeline from "../../components/CaseClosureTimeline";
import {
  getWorkflowCases,
  type WorkflowCaseItem,
  type WorkflowCasesResponse,
} from "../../services/dashboard";
import "./ProgressCasesPage.css";

const { Text, Title } = Typography;

const riskColorMap: Record<string, string> = {
  red: "#e5484d",
  orange: "#f97316",
  yellow: "#facc15",
  blue: "#3b82f6",
};

const riskTextMap: Record<string, string> = {
  red: "红色风险",
  orange: "橙色风险",
  yellow: "黄色风险",
  blue: "蓝色风险",
};

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
        <Descriptions.Item label="申请人">{item.claimants.join("、") || "暂无"}</Descriptions.Item>
        <Descriptions.Item label="责任主体" span={2}>
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

      <Card size="small" title="案件标签">
        {renderTags(item.tags)}
      </Card>

      <Card size="small" title="证据材料">
        {renderTags(item.evidence, "blue")}
      </Card>

      <Card size="small" title="预警特征">
        {renderTags(item.warningFeatures, "orange")}
      </Card>

      <Card size="small" title="处置建议">
        {renderTags(item.recommendedActions, "green")}
      </Card>

      <Card size="small" title="精准普法主题">
        {renderTags(item.propagandaTopics, "purple")}
      </Card>
    </Space>
  );
}

function ProgressCasesPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const stage = searchParams.get("stage") || "discovered";
  const [data, setData] = useState<WorkflowCasesResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadCases() {
      setLoading(true);
      try {
        const nextData = await getWorkflowCases(stage);
        if (!cancelled) setData(nextData);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadCases();
    return () => {
      cancelled = true;
    };
  }, [stage]);

  return (
    <main className="progress-cases-page" style={{ minHeight: "100vh", background: "#101916", padding: 24 }}>
      <Card
        bordered={false}
        style={{
          borderRadius: 8,
          background: "rgba(8, 20, 20, 0.92)",
          border: "1px solid rgba(72, 214, 193, 0.22)",
        }}
      >
        <Space direction="vertical" size={18} style={{ width: "100%" }}>
          <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <Title level={2} style={{ color: "#ecfffb", margin: 0 }}>
                平台级风险闭环任务列表
              </Title>
              <Text style={{ color: "#95b8b0" }}>按风险发现、预警、分派、处置、反馈、评估阶段查看案件与任务。</Text>
            </div>
            <Space>
              <Button onClick={() => navigate("/dashboard")}>返回驾驶舱</Button>
              <Button type="primary" onClick={() => navigate("/community-risk")}>社区风险治理</Button>
            </Space>
          </header>

          <Space wrap>
            {(data?.stageOptions ?? [
              { key: "discovered", label: "风险发现", count: 0 },
              { key: "alerted", label: "已预警", count: 0 },
              { key: "assigned", label: "已分派", count: 0 },
              { key: "handling", label: "处置中", count: 0 },
              { key: "feedback", label: "已反馈", count: 0 },
              { key: "evaluated", label: "已评估", count: 0 },
            ]).map((item) => (
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
            {data?.items.length ? (
              <Collapse
                accordion
                items={data.items.map((item) => ({
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
            ) : (
              <Empty description={loading ? "正在加载案件" : "当前阶段暂无案件"} />
            )}
          </Spin>
        </Space>
      </Card>
    </main>
  );
}

export default ProgressCasesPage;
