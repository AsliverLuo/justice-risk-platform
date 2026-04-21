import { Button, Card, Col, Row, Steps, Typography } from "antd";
import { useNavigate } from "react-router-dom";

const { Paragraph, Title } = Typography;

function SupportProsecutionPage() {
  const navigate = useNavigate();

  return (
    <main style={{ minHeight: "100vh", background: "#f3f6f8", padding: 32 }}>
      <section style={{ maxWidth: 1120, margin: "0 auto", display: "grid", gap: 24 }}>
        <Card bordered={false} style={{ borderRadius: 8 }}>
          <Title level={2} style={{ marginBottom: 8 }}>
            民事支持起诉专题
          </Title>
          <Paragraph type="secondary">
            面向欠薪纠纷场景，完成案件采集、责任链梳理、证据登记、起诉状上下文生成和文书生成。
          </Paragraph>
          <Button
            type="primary"
            size="large"
            onClick={() => navigate("/support-prosecution/form")}
          >
            开始录入案件
          </Button>
        </Card>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={14}>
            <Card title="办理流程" bordered={false} style={{ borderRadius: 8 }}>
              <Steps
                direction="vertical"
                current={1}
                items={[
                  { title: "案件信息采集", description: "录入申请人、欠薪事实、被告和证据。" },
                  { title: "风险与责任链分析", description: "识别欠薪主体、责任角色和重点风险。" },
                  { title: "文书生成", description: "生成民事起诉状和支持起诉申请书。" },
                  { title: "流程跟踪", description: "跟踪办理状态和后续处置结果。" },
                ]}
              />
            </Card>
          </Col>
          <Col xs={24} lg={10}>
            <Card title="专题能力" bordered={false} style={{ borderRadius: 8 }}>
              <div style={{ display: "grid", gap: 12 }}>
                <Button onClick={() => navigate("/support-prosecution/form")}>
                  案件录入
                </Button>
                <Button onClick={() => navigate("/support-prosecution/detail")}>
                  案件详情
                </Button>
                <Button onClick={() => navigate("/support-prosecution/document")}>
                  文书生成
                </Button>
                <Button onClick={() => navigate("/support-prosecution/workflow")}>
                  流程状态
                </Button>
              </div>
            </Card>
          </Col>
        </Row>
      </section>
    </main>
  );
}

export default SupportProsecutionPage;
