import { useState } from "react";
import { Card, Button, Tag, message } from "antd";
import { generateDocuments } from "../../services/support_case";

function DocumentPage() {
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);

  const handleGenerate = async () => {
    try {
      setLoading(true);

      const res = await generateDocuments("SC20260414001");
      console.log("文书生成结果：", res);

      setGenerated(true);
      message.success("文书生成成功");
    } catch (error) {
      console.error(error);
      message.error("文书生成失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>支持起诉 - 文书生成页</h2>

      {/* 顶部案件信息 */}
      <Card title="一、案件基础信息" style={{ marginBottom: 24 }}>
        <p>申请人：张三</p>
        <p>欠薪金额：26800 元</p>
        <p>被告：某建筑劳务公司</p>
        <p>案由：劳务合同纠纷</p>
      </Card>

      {/* 中间状态 */}
      <Card title="二、文书生成状态" style={{ marginBottom: 24 }}>
        {!generated && !loading && <Tag>未生成</Tag>}
        {loading && <Tag color="processing">生成中...</Tag>}
        {generated && <Tag color="success">已生成</Tag>}
      </Card>

      {/* 底部操作 */}
      <Card title="三、操作区域">
        <Button
          type="primary"
          loading={loading}
          onClick={handleGenerate}
          style={{ marginRight: 16 }}
        >
          生成文书
        </Button>

        <Button disabled={!generated} style={{ marginRight: 16 }}>
          预览
        </Button>

        <Button disabled={!generated}>下载</Button>
      </Card>
    </div>
  );
}

export default DocumentPage;