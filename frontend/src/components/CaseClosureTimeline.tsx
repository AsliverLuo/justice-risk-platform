import { Card, Typography } from "antd";

const { Text } = Typography;

type RiskLevel = "red" | "orange" | "yellow" | "blue" | string;

interface CaseClosureTimelineProps {
  status?: string | null;
  riskLevel?: RiskLevel | null;
  stage?: string | null;
  warningFeatures?: string[];
  recommendedActions?: string[];
}

const stageRank: Record<string, number> = {
  discovered: 1,
  alerted: 2,
  assigned: 3,
  handling: 4,
  feedback: 4,
  evaluated: 5,
};

function inferStage(status?: string | null, riskLevel?: RiskLevel | null, warningFeatures: string[] = [], stage?: string | null) {
  if (stage && stageRank[stage]) return stage;
  if (status === "拟制发检察建议") return "evaluated";
  if (status === "联合核查中") return "feedback";
  if (status === "调解中") return "handling";
  if (status === "已转入支持起诉评估") return "assigned";
  if (status === "补充材料" || warningFeatures.length || riskLevel === "red" || riskLevel === "orange") return "alerted";
  return "discovered";
}

function nodeColor(index: number, currentRank: number) {
  if (index < currentRank) return "#22c55e";
  if (index === currentRank) return "#5eead4";
  return "#64748b";
}

function itemSuffix(index: number, currentRank: number) {
  if (index < currentRank) return "已完成";
  if (index === currentRank) return "当前环节";
  return "待推进";
}

function CaseClosureTimeline({
  status,
  riskLevel = "blue",
  stage,
  warningFeatures = [],
  recommendedActions = [],
}: CaseClosureTimelineProps) {
  const currentStage = inferStage(status, riskLevel, warningFeatures, stage);
  const currentRank = stageRank[currentStage] ?? 1;
  const warningText = warningFeatures.length ? warningFeatures.join("；") : "尚未命中明确预警特征";
  const actionText = recommendedActions.length ? recommendedActions.join("；") : "待生成或确认治理建议";

  const items = [
    {
      title: "风险发现",
      description: `线索已接入案件库，当前状态：${status || "已接入"}。`,
    },
    {
      title: "智能预警",
      description: `系统完成案件类型、街道归属和风险等级识别，当前等级：${riskLevel || "blue"}；预警依据：${warningText}。`,
    },
    {
      title: "任务分派",
      description: "预警确认后生成处置任务，明确承办单位、办理期限和协同动作。",
    },
    {
      title: "处置反馈",
      description: actionText,
    },
    {
      title: "效果评估",
      description: "根据风险变化、同类线索变化、回访结果和普法触达情况形成评估结论。",
    },
  ];
  const visibleItems = items.slice(0, currentRank);
  const size = 390;
  const center = size / 2;
  const radius = 132;
  const nodeRadius = 32;
  const progressPercent = Math.max(0, Math.min(100, ((currentRank - 1) / (items.length - 1)) * 100));

  return (
    <Card size="small" title="闭环轨迹">
      <div style={{ display: "grid", gridTemplateColumns: "minmax(320px, 420px) 1fr", gap: 18, alignItems: "center" }}>
        <div style={{ position: "relative", width: "100%", maxWidth: 420, margin: "0 auto" }}>
          <svg viewBox={`0 0 ${size} ${size}`} style={{ width: "100%", display: "block" }}>
            <defs>
              <marker id="closureArrow" markerWidth="8" markerHeight="8" refX="5" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L6,3 z" fill="#5eead4" />
              </marker>
              <filter id="closureGlow">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <circle cx={center} cy={center} r={radius} fill="none" stroke="rgba(15,23,42,0.12)" strokeWidth="18" />
            <circle
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke="#5eead4"
              strokeWidth="18"
              strokeDasharray={`${2 * Math.PI * radius * (progressPercent / 100)} ${2 * Math.PI * radius}`}
              strokeLinecap="round"
              transform={`rotate(-90 ${center} ${center})`}
              opacity="0.72"
              markerEnd="url(#closureArrow)"
            />
            <text x={center} y={center - 8} textAnchor="middle" fill="#10211d" fontSize="20" fontWeight="700">
              {items[currentRank - 1]?.title}
            </text>
            <text x={center} y={center + 18} textAnchor="middle" fill="#475569" fontSize="13">
              {itemSuffix(currentRank, currentRank)}
            </text>
            {items.map((item, index) => {
              const rank = index + 1;
              const angle = -90 + index * (360 / items.length);
              const radian = (angle * Math.PI) / 180;
              const x = center + radius * Math.cos(radian);
              const y = center + radius * Math.sin(radian);
              const color = nodeColor(rank, currentRank);
              return (
                <g key={item.title}>
                  <circle cx={x} cy={y} r={nodeRadius} fill={color} opacity={rank > currentRank ? 0.78 : 0.95} filter="url(#closureGlow)" />
                  <circle cx={x} cy={y} r={nodeRadius - 6} fill="rgba(255,255,255,0.92)" />
                  <text x={x} y={y - 3} textAnchor="middle" fill="#0f172a" fontSize="14" fontWeight="700">
                    {rank}
                  </text>
                  <text x={x} y={y + 14} textAnchor="middle" fill="#0f172a" fontSize="10">
                    {item.title.slice(0, 4)}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10 }}>
          {visibleItems.map((item, index) => {
            const rank = index + 1;
            const color = nodeColor(rank, currentRank);
            return (
              <div
                key={item.title}
                style={{
                  border: `1px solid ${rank === currentRank ? color : "rgba(15,23,42,0.12)"}`,
                  borderRadius: 8,
                  padding: 10,
                  background: rank === currentRank ? "rgba(94,234,212,0.08)" : "rgba(255,255,255,0.72)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <span style={{ width: 9, height: 9, borderRadius: 9, background: color }} />
                  <Text strong>{item.title}</Text>
                  <Text type="secondary">{itemSuffix(rank, currentRank)}</Text>
                </div>
                <div style={{ color: "#475569", fontSize: 13, lineHeight: 1.6 }}>{item.description}</div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

export default CaseClosureTimeline;
