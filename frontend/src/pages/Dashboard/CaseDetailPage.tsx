import { Button, Card, Descriptions, Space, Spin, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import CaseClosureTimeline from "../../components/CaseClosureTimeline";
import { getCaseCorpusDetail, type CaseCorpusDetail } from "../../services/dashboard";

const { Paragraph, Text, Title } = Typography;

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

function renderTags(values?: string[], color = "cyan") {
  if (!values?.length) return <Text type="secondary">暂无</Text>;
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

function CaseDetailPage() {
  const navigate = useNavigate();
  const { caseId = "" } = useParams();
  const [data, setData] = useState<CaseCorpusDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadCase() {
      setLoading(true);
      try {
        const nextData = await getCaseCorpusDetail(caseId);
        if (!cancelled) setData(nextData);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (caseId) loadCase();
    return () => {
      cancelled = true;
    };
  }, [caseId]);

  const extra = data?.extra_meta ?? {};
  const entities = data?.entities ?? {};
  const riskLevel = extra.risk_level || "blue";

  return (
    <main style={{ minHeight: "100vh", background: "#101916", padding: 24 }}>
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
                预警案件详情
              </Title>
              <Text style={{ color: "#95b8b0" }}>查看实时预警关联案件的结构化信息与处置建议。</Text>
            </div>
            <Button type="primary" onClick={() => navigate("/dashboard")}>
              返回主界面
            </Button>
          </header>

          <Spin spinning={loading}>
            {data ? (
              <Space direction="vertical" size={14} style={{ width: "100%" }}>
                <Card size="small" title={data.title}>
                  <Descriptions column={2} size="small" bordered>
                    <Descriptions.Item label="案件编号">{data.case_no || data.source_ref || data.id}</Descriptions.Item>
                    <Descriptions.Item label="案件类型">{data.case_type || "其他"}</Descriptions.Item>
                    <Descriptions.Item label="所属街道">{String(extra.street_name || extra.street || "暂无")}</Descriptions.Item>
                    <Descriptions.Item label="当前状态">{String(extra.status || "暂无")}</Descriptions.Item>
                    <Descriptions.Item label="风险等级">
                      <Tag color={riskColorMap[riskLevel]}>{riskTextMap[riskLevel]}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="风险评分">{String(extra.risk_score || "暂无")}</Descriptions.Item>
                    <Descriptions.Item label="涉案金额">
                      {Number(extra.total_amount || extra.amount || entities.amount_total_estimate || 0).toLocaleString()} 元
                    </Descriptions.Item>
                    <Descriptions.Item label="涉及人数">{String(extra.people_count || "暂无")} 人</Descriptions.Item>
                    <Descriptions.Item label="发生时间">{data.occurred_at || "暂无"}</Descriptions.Item>
                    <Descriptions.Item label="申请人">{entities.persons?.join("、") || data.plaintiff_summary || "暂无"}</Descriptions.Item>
                    <Descriptions.Item label="责任主体" span={2}>
                      {entities.companies?.join("、") || data.defendant_summary || "暂无"}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>

                <Card size="small" title="案件概述">
                  <Paragraph>{data.fact_summary || data.claim_summary || data.full_text}</Paragraph>
                </Card>

                <CaseClosureTimeline
                  status={String(extra.status || "已接入")}
                  riskLevel={riskLevel}
                  warningFeatures={extra.warning_features}
                  recommendedActions={extra.recommended_actions}
                />

                <Card size="small" title="案件标签">
                  {renderTags(extra.tags)}
                </Card>

                <Card size="small" title="证据材料">
                  {renderTags(extra.evidence, "blue")}
                </Card>

                <Card size="small" title="预警特征">
                  {renderTags(extra.warning_features, "orange")}
                </Card>

                <Card size="small" title="处置建议">
                  {renderTags(extra.recommended_actions, "green")}
                </Card>

                <Card size="small" title="精准普法主题">
                  {renderTags(extra.propaganda_topics, "purple")}
                </Card>
              </Space>
            ) : (
              <Card size="small">未找到案件信息。</Card>
            )}
          </Spin>
        </Space>
      </Card>
    </main>
  );
}

export default CaseDetailPage;
