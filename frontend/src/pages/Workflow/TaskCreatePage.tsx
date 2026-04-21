import { Button, Card, Descriptions, Form, Input, Select, Space, Tag, Typography, message } from "antd";
import { useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { createWorkflowTask } from "../../services/workflow";

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

function getParam(searchParams: URLSearchParams, key: string, fallback = "") {
  return searchParams.get(key) || fallback;
}

function TaskCreatePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialValues = useMemo(() => {
    const street = getParam(searchParams, "street", "未标注街道");
    const riskLevel = getParam(searchParams, "riskLevel", "blue");
    const caseType = getParam(searchParams, "caseType", "其他");
    const suggestedActions = getParam(searchParams, "suggestedActions", "建立风险线索台账；明确责任单位和办理期限；定期复盘高发问题");

    return {
      alertId: getParam(searchParams, "alertId", "未关联预警"),
      alertTitle: getParam(searchParams, "title", "社区法治风险预警"),
      street,
      riskLevel,
      caseType,
      taskName: `${street}${caseType}风险处置任务`,
      mainUnit: getParam(searchParams, "suggestedUnit", "街道综治中心、司法所、社区居委会"),
      deadline: riskLevel === "red" ? "3个工作日" : riskLevel === "orange" ? "5个工作日" : "7个工作日",
      actions: suggestedActions,
      description: `针对${street}${caseType}风险线索，开展核查、分派、处置反馈和效果评估，形成闭环治理台账。`,
    };
  }, [searchParams]);

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
          <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
            <div>
              <Title level={2} style={{ color: "#ecfffb", margin: 0 }}>
                创建风险处置任务
              </Title>
              <Text style={{ color: "#95b8b0" }}>由实时预警自动带入街道、风险等级、高发类型和建议处置动作。</Text>
            </div>
            <Space>
              <Button onClick={() => navigate("/dashboard")}>返回驾驶舱</Button>
              <Button onClick={() => navigate(`/dashboard/cases/${encodeURIComponent(initialValues.alertId)}`)}>
                查看关联案件
              </Button>
            </Space>
          </header>

          <Card size="small" title="预警来源">
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="预警编号">{initialValues.alertId}</Descriptions.Item>
              <Descriptions.Item label="所属街道">{initialValues.street}</Descriptions.Item>
              <Descriptions.Item label="风险等级">
                <Tag color={riskColorMap[initialValues.riskLevel]}>{riskTextMap[initialValues.riskLevel]}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="高发类型">{initialValues.caseType}</Descriptions.Item>
              <Descriptions.Item label="预警标题" span={2}>
                {initialValues.alertTitle}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card size="small" title="任务分派信息">
            <Form
              layout="vertical"
              initialValues={initialValues}
              onFinish={async (values) => {
                await createWorkflowTask({
                  task_name: values.taskName,
                  alert_id: initialValues.alertId,
                  alert_title: initialValues.alertTitle,
                  street: initialValues.street,
                  risk_level: initialValues.riskLevel,
                  case_type: initialValues.caseType,
                  main_unit: values.mainUnit,
                  deadline: values.deadline,
                  actions: String(values.actions || "")
                    .split(/[；;\n]/)
                    .map((item) => item.trim())
                    .filter(Boolean),
                  description: values.description || "",
                  stage: "assigned",
                  extra_meta: {
                    source: "realtime_alert",
                  },
                });
                message.success("任务已保存到闭环任务表。");
                navigate("/workflow/tasks?stage=assigned");
              }}
            >
              <Form.Item label="任务名称" name="taskName" rules={[{ required: true, message: "请输入任务名称" }]}>
                <Input />
              </Form.Item>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <Form.Item label="承办/协办单位" name="mainUnit" rules={[{ required: true, message: "请输入承办单位" }]}>
                  <Input />
                </Form.Item>
                <Form.Item label="办理期限" name="deadline" rules={[{ required: true, message: "请输入办理期限" }]}>
                  <Select
                    options={[
                      { value: "3个工作日", label: "3个工作日" },
                      { value: "5个工作日", label: "5个工作日" },
                      { value: "7个工作日", label: "7个工作日" },
                      { value: "10个工作日", label: "10个工作日" },
                    ]}
                  />
                </Form.Item>
              </div>

              <Form.Item label="建议处置动作" name="actions">
                <Input.TextArea rows={4} />
              </Form.Item>

              <Form.Item label="任务说明" name="description">
                <Input.TextArea rows={4} />
              </Form.Item>

              <Card size="small" title="闭环要求">
                <Paragraph>
                  <Text strong>办理单位需反馈：</Text>
                  核查结论、处置措施、普法触达情况、回访结果和风险变化。办结后进入“已反馈”，系统再生成“已评估”记录。
                </Paragraph>
              </Card>

              <Form.Item style={{ marginTop: 18, marginBottom: 0 }}>
                <Space>
                  <Button type="primary" htmlType="submit">
                    生成处置任务
                  </Button>
                  <Button onClick={() => navigate("/dashboard")}>取消</Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Space>
      </Card>
    </main>
  );
}

export default TaskCreatePage;
