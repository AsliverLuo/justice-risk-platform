import { Button, Card, DatePicker, Form, Input, InputNumber, message } from "antd";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import { createSupportCase } from "../../services/support_case";
import type { SupportCaseFormData } from "../../modules/supportProsecution/types";

function FormPage() {
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const handleSubmit = async (values: any) => {
    try {
      const formData: SupportCaseFormData = {
        applicantName: values.applicantName,
        birthDate: values.birthDate ? values.birthDate.format("YYYY-MM-DD") : "",
        age: values.age,
        householdAddress: values.householdAddress,
        idCard: values.idCard,
        phone: values.phone,
        workStartDate: values.workStartDate
          ? values.workStartDate.format("YYYY-MM-DD")
          : "",
        workEndDate: values.workEndDate
          ? values.workEndDate.format("YYYY-MM-DD")
          : "",
        projectName: values.projectName,
        streetName: values.streetName,
        workAddress: values.workAddress,
        defendantName: values.defendantName,
        defendantPhone: values.defendantPhone,
        wageAmount: values.wageAmount,
        wageCalculation: values.wageCalculation,
        entrustmentInfo: values.entrustmentInfo,
      };

      const res = await createSupportCase(formData);
      console.log("提交结果：", res);

      message.success("案件信息提交成功");
      navigate("/support-prosecution/detail");
    } catch (error) {
      console.error("提交失败：", error);
      message.error("案件信息提交失败");
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>支持起诉 - 信息录入页</h2>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          applicantName: "张三",
          birthDate: dayjs("1990-05-12"),
          age: 34,
          householdAddress: "广东省广州市天河区某街道某小区12号",
          idCard: "440106199005120011",
          phone: "13800138000",
          workStartDate: dayjs("2024-01-10"),
          workEndDate: dayjs("2024-06-30"),
          projectName: "某建设工程项目",
          streetName: "某街道",
          workAddress: "广州市天河区某施工工地",
          defendantName: "某建筑劳务公司",
          defendantPhone: "13900139000",
          wageAmount: 26800,
          wageCalculation: "按月工资和加班费用合计计算",
          entrustmentInfo: "委托检察机关依法支持起诉",
        }}
      >
        <Card title="一、申请人基本信息" style={{ marginBottom: 24 }}>
          <Form.Item
            label="姓名"
            name="applicantName"
            rules={[{ required: true, message: "请输入姓名" }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>

          <Form.Item
            label="出生日期"
            name="birthDate"
            rules={[{ required: true, message: "请选择出生日期" }]}
          >
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item
            label="年龄"
            name="age"
            rules={[{ required: true, message: "请输入年龄" }]}
          >
            <InputNumber style={{ width: "100%" }} min={0} max={120} />
          </Form.Item>

          <Form.Item
            label="户籍地地址"
            name="householdAddress"
            rules={[{ required: true, message: "请输入户籍地地址" }]}
          >
            <Input placeholder="请输入户籍地地址" />
          </Form.Item>

          <Form.Item
            label="身份证号"
            name="idCard"
            rules={[
              { required: true, message: "请输入身份证号" },
              {
                pattern: /^[0-9]{17}[0-9Xx]$/,
                message: "请输入正确的身份证号",
              },
            ]}
          >
            <Input placeholder="请输入身份证号" />
          </Form.Item>

          <Form.Item
            label="联系方式"
            name="phone"
            rules={[
              { required: true, message: "请输入联系方式" },
              {
                pattern: /^1\d{10}$/,
                message: "请输入正确的手机号",
              },
            ]}
          >
            <Input placeholder="请输入手机号" />
          </Form.Item>
        </Card>

        <Card title="二、工作信息" style={{ marginBottom: 24 }}>
          <Form.Item
            label="工作开始时间"
            name="workStartDate"
            rules={[{ required: true, message: "请选择工作开始时间" }]}
          >
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item
            label="工作结束时间"
            name="workEndDate"
            rules={[{ required: true, message: "请选择工作结束时间" }]}
          >
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item
            label="工地/项目名称"
            name="projectName"
            rules={[{ required: true, message: "请输入项目名称" }]}
          >
            <Input placeholder="请输入工地或项目名称" />
          </Form.Item>

          <Form.Item
            label="街道"
            name="streetName"
            rules={[{ required: true, message: "请输入街道" }]}
          >
            <Input placeholder="请输入街道" />
          </Form.Item>

          <Form.Item
            label="具体地址"
            name="workAddress"
            rules={[{ required: true, message: "请输入具体地址" }]}
          >
            <Input placeholder="请输入具体地址" />
          </Form.Item>
        </Card>

        <Card title="三、欠薪信息" style={{ marginBottom: 24 }}>
          <Form.Item
            label="欠薪公司/个人姓名"
            name="defendantName"
            rules={[{ required: true, message: "请输入欠薪方名称" }]}
          >
            <Input placeholder="请输入欠薪公司或个人姓名" />
          </Form.Item>

          <Form.Item
            label="联系方式"
            name="defendantPhone"
            rules={[
              {
                pattern: /^1\d{10}$/,
                message: "请输入正确的手机号",
              },
            ]}
          >
            <Input placeholder="请输入联系方式" />
          </Form.Item>

          <Form.Item
            label="欠薪金额"
            name="wageAmount"
            rules={[{ required: true, message: "请输入欠薪金额" }]}
          >
            <InputNumber
              style={{ width: "100%" }}
              min={0}
              placeholder="请输入欠薪金额"
            />
          </Form.Item>

          <Form.Item label="欠薪计算方式" name="wageCalculation">
            <Input.TextArea rows={3} placeholder="请输入欠薪计算方式" />
          </Form.Item>
        </Card>

        <Card title="四、选填信息" style={{ marginBottom: 24 }}>
          <Form.Item label="授权委托情况" name="entrustmentInfo">
            <Input.TextArea rows={3} placeholder="请输入授权委托情况" />
          </Form.Item>
        </Card>

        <Card title="五、附件上传区域" style={{ marginBottom: 24 }}>
          <p>附件上传功能后续补充，当前先占位。</p>
        </Card>

        <Card title="六、电子签名区域" style={{ marginBottom: 24 }}>
          <p>电子签名功能后续补充，当前先占位。</p>
        </Card>

        <Form.Item>
          <Button type="primary" htmlType="submit">
            提交案件信息
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
}

export default FormPage;