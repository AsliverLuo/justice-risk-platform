import { Button, Card, Empty, Space, Spin, Statistic, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getCommunityStreets,
  type CommunityStreetsResponse,
} from "../../services/dashboard";
import "./CommunityRisk.css";

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

function CommunityRiskPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<CommunityStreetsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadStreets() {
      setLoading(true);
      try {
        const nextData = await getCommunityStreets();
        if (!cancelled) setData(nextData);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadStreets();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="community-risk-page">
      <Card className="community-risk-shell" bordered={false}>
        <Space direction="vertical" size={18} style={{ width: "100%" }}>
          <header className="community-risk-header">
            <div>
              <Title level={2} className="community-risk-title">
                社区风险治理
              </Title>
              <Text className="community-risk-subtitle">
                {data?.region || "北京市西城区"} · 按街道查看社区法治风险线索、案件清单和风险画像。
              </Text>
            </div>
            <Button type="primary" onClick={() => navigate("/dashboard")}>
              返回驾驶舱
            </Button>
          </header>

          <div className="community-risk-summary">
            <Card size="small">
              <Statistic title="街道数量" value={data?.totalStreets ?? 0} suffix="个" />
            </Card>
            <Card size="small">
              <Statistic
                title="风险线索"
                value={(data?.items ?? []).reduce((sum, item) => sum + item.caseCount, 0)}
                suffix="件"
              />
            </Card>
            <Card size="small">
              <Statistic
                title="高风险线索"
                value={(data?.items ?? []).reduce((sum, item) => sum + item.highRiskCount, 0)}
                suffix="件"
              />
            </Card>
            <Card size="small">
              <Statistic
                title="涉案金额"
                value={(data?.items ?? []).reduce((sum, item) => sum + item.totalAmount, 0).toFixed(1)}
                suffix="万元"
              />
            </Card>
          </div>

          <Spin spinning={loading}>
            {data?.items.length ? (
              <div className="community-street-grid">
                {data.items.map((item) => (
                  <Card
                    key={item.key}
                    className="community-street-card"
                    bordered={false}
                    onClick={() => navigate(`/community-risk/${encodeURIComponent(item.name)}/cases`)}
                  >
                    <Space direction="vertical" size={12} style={{ width: "100%" }}>
                      <div className="community-street-card-head">
                        <Title level={4}>{item.name}</Title>
                        <Tag color={riskColorMap[item.riskLevel]}>{riskTextMap[item.riskLevel]}</Tag>
                      </div>
                      <Text className="community-street-subline">
                        高频类型：{item.topCaseType} · 高风险 {item.highRiskCount} 件
                      </Text>
                      <div className="community-street-metrics">
                        <span>{item.caseCount} 件线索</span>
                        <span>{item.peopleCount} 人涉及</span>
                        <span>{item.totalAmount.toFixed(1)} 万元</span>
                      </div>
                      <Space wrap>
                        {item.tags.map((tag) => (
                          <Tag key={tag} color="cyan">
                            {tag}
                          </Tag>
                        ))}
                      </Space>
                    </Space>
                  </Card>
                ))}
              </div>
            ) : (
              <Empty description={loading ? "正在加载街道数据" : "暂无街道风险数据"} />
            )}
          </Spin>
        </Space>
      </Card>
    </main>
  );
}

export default CommunityRiskPage;
