import { useEffect, useState } from "react";
import { Card, Button } from "antd";
import { useNavigate } from "react-router-dom";
import { getSupportCaseDetail } from "../../services/support_case";
import type { SupportCaseDetail } from "../../modules/supportProsecution/types";

function DetailPage() {
  const [data, setData] = useState<SupportCaseDetail | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchData() {
      const res = await getSupportCaseDetail("SC20260414001");
      setData(res);
    }

    fetchData();
  }, []);

  if (!data) {
    return <div>加载中...</div>;
  }

  return (
    <div style={{ padding: 24 }}>
      <h2>支持起诉 - 案件详情页</h2>

      <Card title="一、申请人信息" style={{ marginBottom: 24 }}>
        <p>姓名：{data.formData.applicantName}</p>
        <p>身份证号：{data.formData.idCard}</p>
        <p>联系方式：{data.formData.phone}</p>
        <p>户籍地址：{data.formData.householdAddress}</p>
      </Card>

      <Card title="二、工作及欠薪信息" style={{ marginBottom: 24 }}>
        <p>项目名称：{data.formData.projectName}</p>
        <p>工作地址：{data.formData.workAddress}</p>
        <p>
          工作时间：
          {data.formData.workStartDate} - {data.formData.workEndDate}
        </p>
        <p>欠薪方：{data.formData.defendantName}</p>
        <p>欠薪金额：{data.formData.wageAmount}</p>
      </Card>

      <Card title="三、附件列表" style={{ marginBottom: 24 }}>
        {data.evidenceFiles.map((file) => (
          <p key={file.uid}>{file.name}</p>
        ))}
      </Card>

      <Card title="四、操作区域">
        <Button onClick={() => navigate(-1)} style={{ marginRight: 16 }}>
          返回修改
        </Button>

        <Button
          type="primary"
          onClick={() => navigate("/support-prosecution/document")}
          style={{ marginRight: 16 }}
        >
          生成文书
        </Button>

        <Button onClick={() => navigate("/support-prosecution/workflow")}>
          查看流程
        </Button>
      </Card>
    </div>
  );
}

export default DetailPage;