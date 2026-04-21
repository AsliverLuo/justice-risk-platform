import { Button, Card, Empty, Progress, Space, Spin, Statistic, Tag, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  getStreetProfile,
  type StreetProfileResponse,
} from "../../services/dashboard";
import "./CommunityRisk.css";

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

function decodeStreet(value?: string) {
  if (!value) return "";
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function StreetProfilePage() {
  const navigate = useNavigate();
  const params = useParams();
  const street = useMemo(() => decodeStreet(params.street), [params.street]);
  const [data, setData] = useState<StreetProfileResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      setLoading(true);
      try {
        const nextData = await getStreetProfile(street, true);
        if (!cancelled) setData(nextData);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (street) loadProfile();
    return () => {
      cancelled = true;
    };
  }, [street]);

  return (
    <main className="community-risk-page">
      <Card className="community-risk-shell" bordered={false}>
        <Space direction="vertical" size={18} style={{ width: "100%" }}>
          <header className="community-risk-header">
            <div>
              <Title level={2} className="community-risk-title">
                {street || "街道"}社区法治风险画像
              </Title>
              <Text className="community-risk-subtitle">
                自动识别高发案件类型，生成治理建议与个性化普法内容。
              </Text>
            </div>
            <Space>
              <Button onClick={() => navigate(`/community-risk/${encodeURIComponent(street)}/cases`)}>
                返回案件列表
              </Button>
              <Button type="primary" onClick={() => navigate("/dashboard")}>
                返回驾驶舱
              </Button>
            </Space>
          </header>

          <Spin spinning={loading}>
            {data ? (
              <Space direction="vertical" size={16} style={{ width: "100%" }}>
                <section className="community-profile-grid">
                  <Card title="社区法治风险画像" bordered={false}>
                    <Space direction="vertical" size={12} style={{ width: "100%" }}>
                      <Space wrap>
                        <Tag color={riskColorMap[data.profile.riskLevel]}>
                          {riskTextMap[data.profile.riskLevel]}
                        </Tag>
                        <Tag color={data.sourceMode === "llm" ? "green" : "blue"}>
                          {data.sourceMode === "llm" ? "大模型生成" : "规则兜底生成"}
                        </Tag>
                      </Space>
                      <Paragraph>{data.profile.summary}</Paragraph>
                      <div className="community-risk-summary compact">
                        <Statistic title="线索总量" value={data.profile.totalCases} suffix="件" />
                        <Statistic title="涉及群众" value={data.profile.peopleCount} suffix="人" />
                        <Statistic title="涉案金额" value={data.profile.totalAmount} suffix="万元" />
                      </div>
                    </Space>
                  </Card>

                  <Card title="高发案件类型识别" bordered={false}>
                    <Space direction="vertical" size={12} style={{ width: "100%" }}>
                      {(data.profile.highFrequencyTypes ?? []).map((item) => (
                        <div key={item.caseType}>
                          <div className="community-profile-row">
                            <Text strong>{item.caseType}</Text>
                            <Text>{item.count} 件 · {item.ratio}%</Text>
                          </div>
                          <Progress
                            percent={item.ratio}
                            showInfo={false}
                            strokeColor="#5eead4"
                            trailColor="rgba(255,255,255,0.1)"
                          />
                        </div>
                      ))}
                    </Space>
                  </Card>
                </section>

                <Card title="风险维度研判" bordered={false}>
                  <div className="community-dimension-grid">
                    {(data.profile.dimensions ?? []).map((item) => (
                      <Card key={item.name} size="small" bordered={false}>
                        <Space direction="vertical" size={8}>
                          <Space>
                            <Tag color={riskColorMap[item.level]}>{riskTextMap[item.level]}</Tag>
                            <Text strong>{item.name}</Text>
                          </Space>
                          <Text>{item.description}</Text>
                        </Space>
                      </Card>
                    ))}
                  </div>
                </Card>

                <section className="community-profile-grid">
                  <Card title="智能治理建议" bordered={false}>
                    <Space direction="vertical" size={14} style={{ width: "100%" }}>
                      {(data.governanceSuggestions ?? []).map((item) => (
                        <Card key={item.title} size="small" title={item.title}>
                          <Paragraph>{item.summary}</Paragraph>
                          <Text strong>处置动作</Text>
                          <ul>
                            {(item.actions ?? []).map((action) => (
                              <li key={action}>{action}</li>
                            ))}
                          </ul>
                          <Space wrap>
                            {(item.relatedPolicies ?? []).map((policy) => (
                              <Tag key={policy} color="cyan">
                                {policy}
                              </Tag>
                            ))}
                          </Space>
                        </Card>
                      ))}
                    </Space>
                  </Card>

                  <Card title="精准普法方案" bordered={false}>
                    <Space direction="vertical" size={14} style={{ width: "100%" }}>
                      {(data.propagandaPlans ?? []).map((item) => (
                        <Card key={item.title} size="small" title={item.title}>
                          <Paragraph>
                            <Text strong>对象：</Text>
                            {item.targetAudience}
                          </Paragraph>
                          <Paragraph>{item.content}</Paragraph>
                          <Space wrap>
                            {(item.channels ?? []).map((channel) => (
                              <Tag key={channel} color="green">
                                {channel}
                              </Tag>
                            ))}
                          </Space>
                          <div className="community-law-tags">
                            {(item.relatedLaws ?? []).map((law) => (
                              <Tag key={law} color="purple">
                                {law}
                              </Tag>
                            ))}
                          </div>
                        </Card>
                      ))}
                    </Space>
                  </Card>
                </section>
              </Space>
            ) : (
              <Empty description={loading ? "正在生成风险画像" : "暂无风险画像数据"} />
            )}
          </Spin>
        </Space>
      </Card>
    </main>
  );
}

export default StreetProfilePage;
