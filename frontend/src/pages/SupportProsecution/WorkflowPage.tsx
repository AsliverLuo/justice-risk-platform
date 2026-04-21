import { useEffect, useState } from "react";
import { Card, Steps, Tag } from "antd";
import { getWorkflowStatus } from "../../services/support_case";
import type { WorkflowStep } from "../../modules/supportProsecution/types";

function WorkflowPage() {
  const [steps, setSteps] = useState<WorkflowStep[]>([]);

  useEffect(() => {
    async function fetchWorkflow() {
      const res = await getWorkflowStatus("SC20260414001");
      setSteps(res);
    }

    fetchWorkflow();
  }, []);

  const currentStepIndex = steps.findIndex((step) => step.status === "process");

  const currentStep =
    currentStepIndex !== -1 ? steps[currentStepIndex] : steps[steps.length - 1];

  return (
    <div style={{ padding: 24 }}>
      <h2>支持起诉 - 流程状态页</h2>

      <Card title="一、案件流程状态" style={{ marginBottom: 24 }}>
        <Steps
          direction="vertical"
          current={currentStepIndex === -1 ? steps.length - 1 : currentStepIndex}
          items={steps.map((step) => ({
            title: step.title,
            description: step.time ? `更新时间：${step.time}` : "暂无时间记录",
            status: step.status,
          }))}
        />
      </Card>

      <Card title="二、当前状态说明" style={{ marginBottom: 24 }}>
        <p>
          当前状态：
          <Tag color="processing">{currentStep?.title || "暂无状态"}</Tag>
        </p>
        <p>
          更新时间：
          {currentStep?.time || "暂无更新时间"}
        </p>
        <p>
          办理说明：
          当前案件已进入“{currentStep?.title || "暂无"}”阶段，后续将根据办理情况继续推进。
        </p>
      </Card>

      <Card title="三、备注说明">
        <p>1. 当前流程数据为 mock 模拟数据。</p>
        <p>2. 后续可接入真实案件办理状态接口。</p>
        <p>3. 后续可根据不同状态补充颜色、图标和办理意见。</p>
      </Card>
    </div>
  );
}

export default WorkflowPage;