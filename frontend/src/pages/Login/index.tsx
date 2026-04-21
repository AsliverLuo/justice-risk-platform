import {
  Alert,
  Button,
  Card,
  Checkbox,
  Form,
  Input,
  Space,
  Typography,
  message,
} from "antd";
import {
  LockOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const { Paragraph, Text, Title } = Typography;

interface LoginFormValues {
  username: string;
  password: string;
  remember?: boolean;
}

function LoginPage() {
  const navigate = useNavigate();

  const handleSubmit = (values: LoginFormValues) => {
    localStorage.setItem("justice_platform_token", "demo-token");
    localStorage.setItem("justice_platform_user", values.username);
    message.success("登录成功");
    navigate("/dashboard", { replace: true });
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "minmax(420px, 1fr) minmax(380px, 520px)",
        background: "#eef3f7",
      }}
    >
      <section
        style={{
          padding: "72px 72px 48px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background:
            "linear-gradient(135deg, rgba(10,92,105,0.96), rgba(33,121,87,0.94))",
          color: "#fff",
        }}
      >
        <div>
          <Space align="center" size={12}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 8,
                display: "grid",
                placeItems: "center",
                background: "rgba(255,255,255,0.16)",
                border: "1px solid rgba(255,255,255,0.28)",
              }}
            >
              <SafetyCertificateOutlined style={{ fontSize: 24 }} />
            </div>
            <Text style={{ color: "#fff", fontSize: 18, fontWeight: 700 }}>
              清朗法治平台
            </Text>
          </Space>

          <Title
            level={1}
            style={{
              color: "#fff",
              marginTop: 72,
              marginBottom: 20,
              fontSize: 42,
              lineHeight: 1.18,
            }}
          >
            智能检察治理工作台
          </Title>
          <Paragraph style={{ color: "rgba(255,255,255,0.84)", fontSize: 17 }}>
            面向数据接入、风险识别、预警处置、支持起诉、文书生成和治理评估的统一入口。
          </Paragraph>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 16,
          }}
        >
          {[
            ["风险识别", "社区矛盾与重点案件"],
            ["支持起诉", "欠薪案件采集和文书"],
            ["治理闭环", "预警、建议、评估"],
          ].map(([title, desc]) => (
            <div
              key={title}
              style={{
                border: "1px solid rgba(255,255,255,0.24)",
                borderRadius: 8,
                padding: 16,
                background: "rgba(255,255,255,0.1)",
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: 8 }}>{title}</div>
              <div style={{ color: "rgba(255,255,255,0.78)", fontSize: 13 }}>
                {desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section
        style={{
          padding: "72px 56px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Card
          bordered={false}
          style={{
            width: "100%",
            maxWidth: 420,
            borderRadius: 8,
            boxShadow: "0 16px 40px rgba(33, 53, 71, 0.14)",
          }}
        >
          <Title level={2} style={{ marginBottom: 8 }}>
            登录系统
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 24 }}>
            使用演示账号进入平台管理台。
          </Paragraph>

          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 24, borderRadius: 8 }}
            message="演示账号：admin / 123456"
          />

          <Form<LoginFormValues>
            layout="vertical"
            initialValues={{
              username: "admin",
              password: "123456",
              remember: true,
            }}
            onFinish={handleSubmit}
          >
            <Form.Item
              label="账号"
              name="username"
              rules={[{ required: true, message: "请输入账号" }]}
            >
              <Input
                size="large"
                prefix={<UserOutlined />}
                placeholder="请输入账号"
              />
            </Form.Item>

            <Form.Item
              label="密码"
              name="password"
              rules={[{ required: true, message: "请输入密码" }]}
            >
              <Input.Password
                size="large"
                prefix={<LockOutlined />}
                placeholder="请输入密码"
              />
            </Form.Item>

            <Form.Item name="remember" valuePropName="checked">
              <Checkbox>记住登录状态</Checkbox>
            </Form.Item>

            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              style={{ borderRadius: 8 }}
            >
              进入平台
            </Button>
          </Form>
        </Card>
      </section>
    </main>
  );
}

export default LoginPage;
