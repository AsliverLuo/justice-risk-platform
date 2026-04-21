import { Button, Card, Collapse, Descriptions, Empty, Space, Spin, Statistic, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import CaseClosureTimeline from "../../components/CaseClosureTimeline";
import {
  getDefendantCases,
  type DefendantCasesResponse,
  type WorkflowCaseItem,
} from "../../services/dashboard";
import "./DefendantCasesPage.css";

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
      <Card size="small" title="案件标签">{renderTags(item.tags)}</Card>
      <Card size="small" title="证据材料">{renderTags(item.evidence, "blue")}</Card>
      <Card size="small" title="预警特征">{renderTags(item.warningFeatures, "orange")}</Card>
      <Card size="small" title="处置建议">{renderTags(item.recommendedActions, "green")}</Card>
      <Card size="small" title="精准普法主题">{renderTags(item.propagandaTopics, "purple")}</Card>
    </Space>
  );
}

function DefendantCasesPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const defendant = searchParams.get("name") || "";
  const [data, setData] = useState<DefendantCasesResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadCases() {
      setLoading(true);
      try {
        const nextData = await getDefendantCases(defendant);
        if (!cancelled) setData(nextData);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (defendant) loadCases();
    return () => {
      cancelled = true;
    };
  }, [defendant]);

  return (
    <main className="defendant-cases-page" style={{ minHeight: "100vh", background: "#101916", padding: 24 }}>
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
                高风险主体涉案列表
              </Title>
              <Text style={{ color: "#95b8b0" }}>{defendant || "未选择主体"} · 点击案件展开查看具体信息。</Text>
            </div>
            <Button type="primary" onClick={() => navigate("/dashboard")}>返回驾驶舱</Button>
          </header>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            <Card size="small">
              <Statistic title="涉案数量" value={data?.totalCases ?? 0} suffix="件" />
            </Card>
            <Card size="small">
              <Statistic title="涉案金额" value={data?.totalAmount ?? 0} suffix="万元" />
            </Card>
            <Card size="small">
              <Space wrap>
                {Object.entries(data?.riskSummary ?? {}).map(([level, count]) => (
                  <Tag key={level} color={riskColorMap[level]}>{riskTextMap[level]} {count}</Tag>
                ))}
              </Space>
            </Card>
          </div>

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
              <Empty description={loading ? "正在加载案件" : "该主体暂无关联案件"} />
            )}
          </Spin>
        </Space>
      </Card>
    </main>
  );
}

export default DefendantCasesPage;
