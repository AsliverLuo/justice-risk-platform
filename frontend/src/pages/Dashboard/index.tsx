import {
  Alert,
  Button,
  Card,
  Drawer,
  List,
  Progress,
  Space,
  Statistic,
  Tag,
  Typography,
} from "antd";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import http from "../../services/http";

const { Text, Title } = Typography;

type RiskLevel = "red" | "orange" | "yellow" | "blue";

interface RiskPoint {
  id: string;
  name: string;
  type: "街道" | "工地";
  lng: number;
  lat: number;
  level: RiskLevel;
  caseCount: number;
  workers: number;
  amount: number;
  owner: string;
  status: string;
}

interface RealtimeAlert {
  id: string;
  time: string;
  title: string;
  level: RiskLevel;
  scope: string;
  caseType?: string;
  suggestedUnit?: string;
  suggestedActions?: string[];
}

interface DefendantTopItem {
  name: string;
  count: number;
  amount: number;
}

interface CaseDistributionItem {
  label: string;
  value: number;
  count?: number;
  color: string;
}

interface SupportProgressItem {
  label: string;
  value: number;
  color: string;
  stage?: string;
}

interface DashboardRiskMapData {
  points: RiskPoint[];
  totals: {
    totalCases: number;
    totalWorkers: number;
    totalAmount: number;
    monthlyNew: number;
  };
  caseDistribution: CaseDistributionItem[];
  monthlyTrend: number[];
  monthlyLabels?: string[];
  alertRows: RealtimeAlert[];
  defendantTop: DefendantTopItem[];
  supportProgress: SupportProgressItem[];
}

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

interface LocalMapFeature {
  id: string;
  name: string;
  riskLevel: RiskLevel;
  coordinates: [number, number][];
}

interface LocalMapLabel {
  name: string;
  lng: number;
  lat: number;
}

interface LocalRiskMapData {
  name: string;
  bbox: [number, number, number, number];
  features: LocalMapFeature[];
  roads: [number, number][][];
  labels: LocalMapLabel[];
}

const riskColors: Record<RiskLevel, string> = {
  red: "#e5484d",
  orange: "#f97316",
  yellow: "#facc15",
  blue: "#3b82f6",
};

const riskText: Record<RiskLevel, string> = {
  red: "红色",
  orange: "橙色",
  yellow: "黄色",
  blue: "蓝色",
};

const riskLevelWeight: Record<RiskLevel, number> = {
  red: 1,
  orange: 0.76,
  yellow: 0.48,
  blue: 0.26,
};

const tiandituToken = String(import.meta.env.VITE_TIANDITU_TOKEN ?? "").trim();

function buildTiandituTiles(layer: "vec" | "cva", token: string) {
  return Array.from(
    { length: 8 },
    (_, index) =>
      `https://t${index}.tianditu.gov.cn/${layer}_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${layer}&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${token}`
  );
}

const fallbackRiskPoints: RiskPoint[] = [
  {
    id: "xicheng-zhanlanlu",
    name: "展览路街道",
    type: "街道",
    lng: 116.345,
    lat: 39.923,
    level: "red",
    caseCount: 46,
    workers: 182,
    amount: 386.4,
    owner: "北京某建筑劳务公司",
    status: "联合核查中",
  },
  {
    id: "xicheng-dashilan-site",
    name: "大栅栏片区工地",
    type: "工地",
    lng: 116.383,
    lat: 39.887,
    level: "orange",
    caseCount: 31,
    workers: 119,
    amount: 248.6,
    owner: "北京某建设集团分包项目部",
    status: "限期支付计划",
  },
  {
    id: "xicheng-jinrongjie",
    name: "金融街街道",
    type: "街道",
    lng: 116.365,
    lat: 39.908,
    level: "yellow",
    caseCount: 18,
    workers: 62,
    amount: 96.2,
    owner: "北京某装饰工程公司",
    status: "调解前置",
  },
  {
    id: "xicheng-xinjiekou",
    name: "新街口街道",
    type: "工地",
    lng: 116.360,
    lat: 39.941,
    level: "orange",
    caseCount: 27,
    workers: 88,
    amount: 174.5,
    owner: "北京某劳务分包队",
    status: "证据补充",
  },
  {
    id: "xicheng-guanganmenwai",
    name: "广安门外街道",
    type: "街道",
    lng: 116.342,
    lat: 39.880,
    level: "blue",
    caseCount: 9,
    workers: 24,
    amount: 31.8,
    owner: "北京某安装公司",
    status: "持续观察",
  },
];

const fallbackAlertRows: RealtimeAlert[] = [
  { id: "A-001", time: "10:32", title: "展览路街道触发群体性法治风险红色预警", level: "red", scope: "展览路街道", caseType: "劳动争议", suggestedUnit: "街道综治中心、人社所、司法所", suggestedActions: ["排查重点用工单位", "建立欠薪线索快转机制", "评估支持起诉条件"] },
  { id: "A-002", time: "10:18", title: "大栅栏片区重复被告主体次数升高", level: "orange", scope: "大栅栏片区工地", caseType: "合同诈骗", suggestedUnit: "街道综治中心、市场监管所、公安派出所", suggestedActions: ["建立异常主体名单", "核验经营资质", "发布合同签订风险提示"] },
  { id: "A-003", time: "09:54", title: "新街口街道新增 12 条劳动争议和社区纠纷线索", level: "orange", scope: "新街口街道", caseType: "邻里纠纷", suggestedUnit: "社区居委会、司法所、人民调解委员会", suggestedActions: ["梳理重复投诉点位", "组织入户释法", "建立议事台账"] },
  { id: "A-004", time: "09:27", title: "金融街街道劳务纠纷进入调解期限", level: "yellow", scope: "金融街街道", caseType: "劳动争议", suggestedUnit: "街道综治中心、人社所、司法所", suggestedActions: ["联系双方当事人", "组织调解", "推送劳动权益普法"] },
  { id: "A-005", time: "08:46", title: "广安门外街道完成普法推送回访", level: "blue", scope: "广安门外街道", caseType: "物业纠纷", suggestedUnit: "街道城管办、社区居委会、物业主管部门", suggestedActions: ["建立物业纠纷清单", "推动公共收益公开", "指导业委会依法履职"] },
];

const fallbackDefendantTop: DefendantTopItem[] = [
  { name: "北京某建筑劳务公司", count: 18, amount: 186.2 },
  { name: "北京某建设集团分包项目部", count: 14, amount: 143.7 },
  { name: "北京某装饰工程公司", count: 11, amount: 92.8 },
  { name: "北京某劳务分包队", count: 9, amount: 81.4 },
  { name: "北京某安装公司", count: 7, amount: 48.6 },
];

const fallbackMonthlyTrend = [26, 28, 31, 15];
const fallbackMonthlyLabels = ["1月", "2月", "3月", "4月"];
const fallbackCaseDistribution: CaseDistributionItem[] = [
  { label: "劳动争议", value: 25, color: "#2dd4bf" },
  { label: "邻里纠纷", value: 15, color: "#a78bfa" },
  { label: "合同诈骗", value: 15, color: "#34d399" },
  { label: "婚姻家庭", value: 10, color: "#f472b6" },
  { label: "物业纠纷", value: 10, color: "#94a3b8" },
  { label: "其他类型", value: 25, color: "#67e8f9" },
];

const fallbackSupportProgress: SupportProgressItem[] = [
  { label: "风险发现", value: 29, color: "#38bdf8", stage: "discovered" },
  { label: "已预警", value: 24, color: "#15b8a6", stage: "alerted" },
  { label: "已分派", value: 14, color: "#a78bfa", stage: "assigned" },
  { label: "处置中", value: 14, color: "#3b82f6", stage: "handling" },
  { label: "已反馈", value: 14, color: "#f97316", stage: "feedback" },
  { label: "已评估", value: 14, color: "#22c55e", stage: "evaluated" },
];

function DashboardPanel({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <Card
      bordered={false}
      title={<span style={{ color: "#d9fff7", fontWeight: 700 }}>{title}</span>}
      style={{
        borderRadius: 8,
        background: "rgba(8, 20, 20, 0.82)",
        border: "1px solid rgba(72, 214, 193, 0.24)",
        boxShadow: "0 14px 34px rgba(0,0,0,0.25)",
      }}
      styles={{
        header: { borderBottom: "1px solid rgba(72,214,193,0.18)", minHeight: 36, padding: "0 14px" },
        body: { padding: 14 },
      }}
    >
      {children}
    </Card>
  );
}

function LocalRiskMap({
  points,
  onSelect,
  message,
}: {
  points: RiskPoint[];
  onSelect: (point: RiskPoint) => void;
  message?: string;
}) {
  const [mapData, setMapData] = useState<LocalRiskMapData | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadLocalMap() {
      try {
        const response = await fetch("/data/xicheng-risk-map.json");
        const data = (await response.json()) as LocalRiskMapData;
        if (!cancelled) setMapData(data);
      } catch (error) {
        console.error("本地风险地图 JSON 加载失败。", error);
      }
    }

    loadLocalMap();

    return () => {
      cancelled = true;
    };
  }, []);

  if (!mapData) return <FallbackRiskMap points={points} onSelect={onSelect} message={message ?? "正在加载本地风险地图 JSON"} />;

  return <FallbackRiskMap points={points} onSelect={onSelect} mapData={mapData} message={message} />;
}

function TiandituRiskMap({
  points,
  onSelect,
}: {
  points: RiskPoint[];
  onSelect: (point: RiskPoint) => void;
}) {
  const containerIdRef = useRef(`tianditu-risk-map-${Math.random().toString(36).slice(2)}`);
  const sceneRef = useRef<null | { destroy?: () => void }>(null);
  const [fallbackMessage, setFallbackMessage] = useState<string | null>(
    tiandituToken ? null : "未配置 VITE_TIANDITU_TOKEN，已切换为北京市西城区本地 JSON 地图"
  );
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!tiandituToken) {
      setFallbackMessage("未配置 VITE_TIANDITU_TOKEN，已切换为北京市西城区本地 JSON 地图");
      return;
    }

    let cancelled = false;
    setLoaded(false);
    setFallbackMessage(null);

    async function mountMap() {
      try {
        const [{ Scene, HeatmapLayer, PointLayer, Popup }, { Mapbox }] = await Promise.all([
          import("@antv/l7"),
          import("@antv/l7-maps"),
        ]);

        if (cancelled) return;

        const scene = new Scene({
          id: containerIdRef.current,
          map: new Mapbox({
            style: {
              version: 8,
              sources: {
                tiandituVec: {
                  type: "raster",
                  tiles: buildTiandituTiles("vec", tiandituToken),
                  tileSize: 256,
                  minzoom: 1,
                  maxzoom: 18,
                },
                tiandituCva: {
                  type: "raster",
                  tiles: buildTiandituTiles("cva", tiandituToken),
                  tileSize: 256,
                  minzoom: 1,
                  maxzoom: 18,
                },
              },
              layers: [
                { id: "tianditu-vec", type: "raster", source: "tiandituVec", paint: { "raster-opacity": 0.86 } },
                { id: "tianditu-cva", type: "raster", source: "tiandituCva", paint: { "raster-opacity": 0.95 } },
              ],
            },
            center: [116.365, 39.91],
            zoom: 12.1,
            pitch: 0,
            rotation: 0,
            token: "",
          }),
        });

        sceneRef.current = scene as { destroy?: () => void };

        scene.on("loaded", () => {
          if (cancelled) return;

          const maxCases = Math.max(...points.map((item) => item.caseCount), 1);
          const heatData = points.map((item) => ({
            ...item,
            heatWeight: Math.max(0.18, (item.caseCount / maxCases) * riskLevelWeight[item.level]),
          }));

          const heatLayer = new HeatmapLayer({ name: "xicheng-risk-heatmap", zIndex: 18 })
            .source(heatData, {
              parser: {
                type: "json",
                x: "lng",
                y: "lat",
              },
            })
            .shape("heatmap")
            .size("heatWeight")
            .style({
              intensity: 2.25,
              radius: 58,
              opacity: 0.86,
              rampColors: {
                type: "linear",
                colors: ["rgba(59,130,246,0)", "#3b82f6", "#facc15", "#f97316", "#e5484d"],
                positions: [0, 0.22, 0.48, 0.72, 1],
              },
            });

          const hitLayer = new PointLayer({ name: "xicheng-risk-heatmap-hit-area", zIndex: 24 })
            .source(heatData, {
              parser: {
                type: "json",
                x: "lng",
                y: "lat",
              },
            })
            .shape("circle")
            .size("level", (level: RiskLevel) => {
              if (level === "red") return 42;
              if (level === "orange") return 36;
              if (level === "yellow") return 30;
              return 26;
            })
            .color("level", (level: RiskLevel) => riskColors[level])
            .style({
              opacity: 0.08,
              stroke: "#ffffff",
              strokeWidth: 1,
            });

          hitLayer.on("click", (event: { feature?: RiskPoint }) => {
            const point = points.find((item) => item.id === event.feature?.id);
            if (!point) return;

            onSelect(point);
            const popup = new Popup({
              offsets: [0, 12],
              closeButton: false,
            })
              .setLnglat([point.lng, point.lat])
              .setHTML(
                `<div style="color:#10211d;font-size:12px;line-height:1.7"><strong>${point.name}</strong><br/>${riskText[point.level]}风险 · ${point.caseCount}件<br/>${point.status}</div>`
            );
            scene.addPopup(popup);
          });

          scene.addLayer(heatLayer);
          scene.addLayer(hitLayer);
          setLoaded(true);
        });
      } catch (error) {
        console.error("天地图 API 加载失败。", error);
        if (!cancelled) {
          setFallbackMessage("天地图 API 加载失败，已切换为北京市西城区本地 JSON 地图");
        }
      }
    }

    mountMap();

    return () => {
      cancelled = true;
      try {
        sceneRef.current?.destroy?.();
      } catch (error) {
        console.warn("天地图场景销毁失败。", error);
      }
      sceneRef.current = null;
    };
  }, [onSelect, points]);

  if (fallbackMessage) {
    return <LocalRiskMap points={points} onSelect={onSelect} message={fallbackMessage} />;
  }

  return (
    <div
      style={{
        position: "relative",
        height: "100%",
        minHeight: 430,
        overflow: "hidden",
        borderRadius: 8,
        background: "#07100f",
      }}
    >
      <div id={containerIdRef.current} style={{ position: "absolute", inset: 0 }} />
      <div
        style={{
          position: "absolute",
          left: 12,
          top: 12,
          zIndex: 5,
          padding: "6px 10px",
          borderRadius: 8,
          color: "#d9fff7",
          background: "rgba(8,20,20,0.78)",
          border: "1px solid rgba(94,234,212,0.32)",
          fontSize: 12,
        }}
      >
        {loaded ? "天地图 API · 北京市西城区法治风险热力图" : "正在加载天地图 API"}
      </div>
      <HeatLegend />
    </div>
  );
}

function HeatLegend() {
  return (
    <div
      style={{
        position: "absolute",
        right: 12,
        bottom: 12,
        zIndex: 5,
        width: 168,
        padding: 10,
        borderRadius: 8,
        color: "#d9fff7",
        background: "rgba(8,20,20,0.78)",
        border: "1px solid rgba(94,234,212,0.32)",
        fontSize: 12,
      }}
    >
      <div style={{ marginBottom: 6 }}>风险热力强度</div>
      <div
        style={{
          height: 10,
          borderRadius: 8,
          background: "linear-gradient(90deg, #3b82f6 0%, #facc15 42%, #f97316 70%, #e5484d 100%)",
        }}
      />
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 5, color: "#95b8b0" }}>
        <span>低</span>
        <span>高</span>
      </div>
    </div>
  );
}

function FallbackRiskMap({
  points,
  onSelect,
  message,
  mapData,
}: {
  points: RiskPoint[];
  onSelect: (point: RiskPoint) => void;
  message?: string;
  mapData?: LocalRiskMapData;
}) {
  const bbox = mapData?.bbox ?? [116.33, 39.86, 116.42, 39.96];
  const [minLng, minLat, maxLng, maxLat] = bbox;
  const project = (lng: number, lat: number) => {
    const x = ((lng - minLng) / (maxLng - minLng)) * 660 + 50;
    const y = 470 - ((lat - minLat) / (maxLat - minLat)) * 400;
    return [x, y] as const;
  };
  const polygonPath = (coordinates: [number, number][]) =>
    coordinates
      .map(([lng, lat], index) => {
        const [x, y] = project(lng, lat);
        return `${index === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(" ") + " Z";
  const maxCases = Math.max(...points.map((item) => item.caseCount), 1);

  return (
    <div
      style={{
        position: "relative",
        height: "100%",
        minHeight: 430,
        overflow: "hidden",
        borderRadius: 8,
        background:
          "radial-gradient(circle at 40% 38%, rgba(20,184,166,0.22), transparent 24%), linear-gradient(145deg, #111b18, #07100f)",
      }}
    >
      {message ? (
        <Alert
          type="warning"
          showIcon
          message={message}
          style={{ position: "absolute", top: 12, left: 12, right: 12, zIndex: 2, borderRadius: 8 }}
        />
      ) : null}
      <svg viewBox="0 0 760 520" style={{ width: "100%", height: "100%" }}>
        <defs>
          <filter id="riskGlow">
            <feGaussianBlur stdDeviation="5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="heatBlur">
            <feGaussianBlur stdDeviation="18" />
          </filter>
          {points.map((point) => (
            <radialGradient key={point.id} id={`heat-${point.id}`} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={riskColors[point.level]} stopOpacity={point.level === "red" ? 0.86 : 0.72} />
              <stop offset="42%" stopColor={riskColors[point.level]} stopOpacity="0.34" />
              <stop offset="100%" stopColor={riskColors[point.level]} stopOpacity="0" />
            </radialGradient>
          ))}
        </defs>
        <rect width="760" height="520" fill="rgba(4,14,13,0.28)" />
        {[0, 1, 2, 3, 4, 5].map((line) => (
          <path
            key={line}
            d={`M${80 + line * 95} 80 C${110 + line * 95} 180 ${90 + line * 95} 320 ${130 + line * 95} 460`}
            fill="none"
            stroke="rgba(94,234,212,0.08)"
            strokeWidth="1"
          />
        ))}
        {(mapData?.features ?? []).map((feature) => (
          <path
            key={feature.id}
            d={polygonPath(feature.coordinates)}
            fill={riskColors[feature.riskLevel]}
            fillOpacity="0.16"
            stroke={riskColors[feature.riskLevel]}
            strokeWidth="2"
            opacity="0.96"
          />
        ))}
        {points.map((point) => {
          const [x, y] = project(point.lng, point.lat);
          const weight = Math.max(0.28, (point.caseCount / maxCases) * riskLevelWeight[point.level]);
          const radius = 52 + weight * 78;
          return (
            <circle
              key={`heat-${point.id}`}
              cx={x}
              cy={y}
              r={radius}
              fill={`url(#heat-${point.id})`}
              filter="url(#heatBlur)"
              opacity="0.82"
            />
          );
        })}
        {(mapData?.roads ?? []).map((road, index) => (
          <polyline
            key={index}
            points={road.map(([lng, lat]) => project(lng, lat).join(",")).join(" ")}
            fill="none"
            stroke={index % 2 === 0 ? "rgba(250,204,21,0.34)" : "rgba(59,130,246,0.26)"}
            strokeWidth={index % 2 === 0 ? 5 : 4}
            strokeLinecap="round"
          />
        ))}
        {(mapData?.labels ?? []).map((label) => {
          const [x, y] = project(label.lng, label.lat);
          return (
            <text key={label.name} x={x} y={y} fill="#a9fff2" fontSize="13" textAnchor="middle">
              {label.name}
            </text>
          );
        })}
        {points.map((point) => {
          const [x, y] = project(point.lng, point.lat);
          return (
            <g key={point.id} onClick={() => onSelect(point)} style={{ cursor: "pointer" }}>
              <circle cx={x} cy={y} r={point.level === "red" ? 42 : point.level === "orange" ? 36 : 30} fill="transparent" />
              <circle cx={x} cy={y} r={6} fill={riskColors[point.level]} stroke="#fff" strokeWidth="1.5" filter="url(#riskGlow)" />
              <text x={x + 14} y={y + 4} fill="#eafffa" fontSize="13">{point.name}</text>
            </g>
          );
        })}
        <text x="62" y="488" fill="#95b8b0" fontSize="12">
          北京市西城区本地 JSON 地图 / 热力值按案件量与风险等级加权
        </text>
      </svg>
      <HeatLegend />
    </div>
  );
}

function PieChart({ data }: { data: CaseDistributionItem[] }) {
  const safeData = data.length ? data : fallbackCaseDistribution;
  const total = safeData.reduce((sum, item) => sum + item.value, 0) || 1;
  const gradient = safeData
    .reduce(
      (acc, item) => {
        const start = (acc.offset / total) * 100;
        const nextOffset = acc.offset + item.value;
        const end = (nextOffset / total) * 100;
        acc.parts.push(`${item.color} ${start.toFixed(2)}% ${end.toFixed(2)}%`);
        acc.offset = nextOffset;
        return acc;
      },
      { offset: 0, parts: [] as string[] }
    )
    .parts.join(", ");

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
      <div
        style={{
          width: 116,
          height: 116,
          borderRadius: "50%",
          background: `conic-gradient(${gradient})`,
          boxShadow: "inset 0 0 0 1px rgba(217,255,247,0.12)",
        }}
      />
      <div style={{ display: "grid", gap: 8 }}>
        {safeData.map((item) => (
          <Space key={item.label}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: item.color }} />
            <Text style={{ color: "#d9fff7" }}>{item.label}</Text>
            <Text style={{ color: "#95b8b0" }}>{item.value}%</Text>
          </Space>
        ))}
      </div>
    </div>
  );
}

function buildRecentMonthLabels(count: number) {
  const now = new Date();
  return Array.from({ length: count }, (_, index) => {
    const date = new Date(now.getFullYear(), now.getMonth() - (count - 1 - index), 1);
    return `${date.getMonth() + 1}月`;
  });
}

function TrendLine({ data, labels }: { data: number[]; labels?: string[] }) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const sourceData = data.length ? data : fallbackMonthlyTrend;
  const safeData = sourceData.slice(-9);
  const sourceLabels = labels?.length === sourceData.length ? labels : buildRecentMonthLabels(sourceData.length);
  const monthLabels = sourceLabels.slice(-safeData.length);
  const max = Math.max(...safeData, 1);
  const points = safeData
    .map((value, index) => `${(index / Math.max(1, safeData.length - 1)) * 300 + 10},${100 - (value / max) * 76 + 8}`)
    .join(" ");
  const activePoint = activeIndex === null ? null : {
    label: monthLabels[activeIndex],
    value: safeData[activeIndex],
    x: (activeIndex / Math.max(1, safeData.length - 1)) * 300 + 10,
    y: 100 - (safeData[activeIndex] / max) * 76 + 8,
  };

  return (
    <svg viewBox="0 0 340 150" style={{ width: "100%", height: 150 }}>
      {[24, 52, 80, 108].map((y) => (
        <line key={y} x1="10" x2="318" y1={y} y2={y} stroke="rgba(217,255,247,0.12)" />
      ))}
      <polyline points={points} fill="none" stroke="#5eead4" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      {safeData.map((value, index) => {
        const x = (index / Math.max(1, safeData.length - 1)) * 300 + 10;
        const y = 100 - (value / max) * 76 + 8;
        const isActive = activeIndex === index;
        return (
          <g
            key={monthLabels[index]}
            onMouseEnter={() => setActiveIndex(index)}
            onMouseLeave={() => setActiveIndex(null)}
            onClick={() => setActiveIndex(index)}
            style={{ cursor: "pointer" }}
          >
            <circle cx={x} cy={y} r={isActive ? 8 : 5} fill={isActive ? "#ffffff" : "#facc15"} stroke="#5eead4" strokeWidth="2" />
            <text x={x} y="130" fill="#95b8b0" fontSize="11" textAnchor="middle">
              {monthLabels[index]}
            </text>
          </g>
        );
      })}
      {activePoint ? (
        <g>
          <line x1={activePoint.x} x2={activePoint.x} y1="14" y2="120" stroke="rgba(250,204,21,0.42)" strokeDasharray="4 4" />
          <rect x={Math.min(246, Math.max(8, activePoint.x - 46))} y={Math.max(8, activePoint.y - 40)} width="92" height="31" rx="6" fill="rgba(8,20,20,0.92)" stroke="rgba(94,234,212,0.36)" />
          <text x={Math.min(292, Math.max(54, activePoint.x))} y={Math.max(27, activePoint.y - 20)} fill="#ecfffb" fontSize="12" textAnchor="middle">
            {activePoint.label}：{activePoint.value}件
          </text>
        </g>
      ) : null}
    </svg>
  );
}

function DashboardPage() {
  const navigate = useNavigate();
  const [selectedPoint, setSelectedPoint] = useState<RiskPoint | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardRiskMapData | null>(null);
  const [dataSourceMessage, setDataSourceMessage] = useState("正在读取后端案件数据");
  const riskPoints = dashboardData?.points?.length ? dashboardData.points : fallbackRiskPoints;
  const alertRows = dashboardData?.alertRows?.length ? dashboardData.alertRows : fallbackAlertRows;
  const defendantTop = dashboardData?.defendantTop?.length ? dashboardData.defendantTop : fallbackDefendantTop;
  const caseDistribution = dashboardData?.caseDistribution?.length ? dashboardData.caseDistribution : fallbackCaseDistribution;
  const monthlyTrend = dashboardData?.monthlyTrend?.length ? dashboardData.monthlyTrend : fallbackMonthlyTrend;
  const monthlyLabels = dashboardData?.monthlyLabels?.length ? dashboardData.monthlyLabels : fallbackMonthlyLabels;
  const supportProgress = dashboardData?.supportProgress?.length ? dashboardData.supportProgress : fallbackSupportProgress;
  const totalCases = dashboardData?.totals.totalCases ?? riskPoints.reduce((sum, item) => sum + item.caseCount, 0);
  const totalWorkers = dashboardData?.totals.totalWorkers ?? riskPoints.reduce((sum, item) => sum + item.workers, 0);
  const totalAmount = dashboardData?.totals.totalAmount ?? riskPoints.reduce((sum, item) => sum + item.amount, 0);
  const monthlyNew = dashboardData?.totals.monthlyNew ?? 42;

  const navigateToTaskCreate = (item: RealtimeAlert) => {
    const params = new URLSearchParams({
      alertId: item.id,
      title: item.title,
      street: item.scope,
      riskLevel: item.level,
      caseType: item.caseType || "其他",
      suggestedUnit: item.suggestedUnit || "街道综治中心、司法所、社区居委会",
      suggestedActions: (item.suggestedActions || []).join("；"),
    });
    navigate(`/workflow/tasks/create?${params.toString()}`);
  };

  useEffect(() => {
    let cancelled = false;
    async function loadDashboardRiskMap() {
      try {
        const response = await http.get<ApiResponse<DashboardRiskMapData>>("/dashboard/risk-map");
        if (cancelled) return;
        const nextData = response.data.data;
        if (nextData?.points?.length) {
          setDashboardData(nextData);
          setDataSourceMessage(`已接入后端案件数据：${nextData.totals.totalCases} 件`);
        } else {
          setDataSourceMessage("后端暂无案件聚合数据，当前显示本地演示数据");
        }
      } catch (error) {
        console.error("驾驶舱风险地图数据加载失败。", error);
        if (!cancelled) setDataSourceMessage("后端数据读取失败，当前显示本地演示数据");
      }
    }

    loadDashboardRiskMap();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #151515 0%, #10211d 52%, #1f1c16 100%)",
        padding: "14px 42px 14px 14px",
        color: "#ecfffb",
        overflow: "hidden",
      }}
    >
      <section style={{ display: "grid", gap: 12, height: "calc(100vh - 28px)" }}>
        <header
          style={{
            height: 58,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 22px",
            borderRadius: 8,
            border: "1px solid rgba(94,234,212,0.28)",
            background: "rgba(8,20,20,0.74)",
          }}
        >
          <div>
            <Title level={2} style={{ color: "#ecfffb", margin: 0 }}>
              社区法治风险智能预警与精准普法平台
            </Title>
            <Text style={{ color: "#95b8b0" }}>多源数据接入 · 法治风险识别 · 预警推送 · 治理建议 · 精准普法 · 闭环处置</Text>
          </div>
          <Space>
            <Button onClick={() => navigate("/community-risk")}>社区风险治理</Button>
          </Space>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "330px minmax(520px, 1fr) 360px",
            gridTemplateRows: "minmax(438px, calc(100vh - 198px)) 92px",
            gap: 12,
            minHeight: 0,
          }}
        >
          <aside style={{ display: "grid", gap: 16 }}>
            <DashboardPanel title="核心数据概览">
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <Statistic title={<span style={{ color: "#9fbdb6" }}>风险线索</span>} value={totalCases} suffix="件" valueStyle={{ color: "#ecfffb" }} />
                <Statistic title={<span style={{ color: "#9fbdb6" }}>涉及群众</span>} value={totalWorkers} suffix="人" valueStyle={{ color: "#ecfffb" }} />
                <Statistic title={<span style={{ color: "#9fbdb6" }}>涉案金额</span>} value={totalAmount.toFixed(1)} suffix="万元" valueStyle={{ color: "#facc15" }} />
                <Statistic title={<span style={{ color: "#9fbdb6" }}>本月新增</span>} value={monthlyNew} suffix="件" valueStyle={{ color: "#5eead4" }} />
              </div>
            </DashboardPanel>

            <DashboardPanel title="案件类型分布">
              <PieChart data={caseDistribution} />
            </DashboardPanel>

            <DashboardPanel title="月度趋势">
              <TrendLine data={monthlyTrend} labels={monthlyLabels} />
            </DashboardPanel>
          </aside>

          <section style={{ minHeight: 0 }}>
            <DashboardPanel title="社区法治风险地图热力图">
              <div style={{ height: "calc(100vh - 282px)", minHeight: 408 }}>
                <TiandituRiskMap points={riskPoints} onSelect={setSelectedPoint} />
              </div>
              <Text style={{ color: "#95b8b0", fontSize: 12 }}>{dataSourceMessage}</Text>
            </DashboardPanel>
          </section>

          <aside style={{ display: "grid", gap: 12, minHeight: 0 }}>
            <DashboardPanel title="实时预警列表">
              <div
                style={{
                  maxHeight: 178,
                  overflowY: "auto",
                  paddingRight: 6,
                  scrollbarColor: "rgba(94,234,212,0.42) rgba(255,255,255,0.06)",
                }}
              >
                <List
                  dataSource={alertRows}
                  renderItem={(item) => (
                    <List.Item
                      onClick={() => navigate(`/dashboard/cases/${encodeURIComponent(item.id)}`)}
                      style={{
                        borderColor: "rgba(255,255,255,0.08)",
                        padding: "9px 0",
                        cursor: "pointer",
                        transition: "background 0.2s ease",
                      }}
                    >
                      <List.Item.Meta
                        title={<Text style={{ color: "#ecfffb" }}>{item.title}</Text>}
                        description={
                          <Text style={{ color: "#95b8b0" }}>
                            {item.time} · {item.scope} · {item.caseType || "其他"}
                          </Text>
                        }
                      />
                      <Space>
                        <Tag color={riskColors[item.level]}>{riskText[item.level]}</Tag>
                        <Button
                          size="small"
                          type="primary"
                          onClick={(event) => {
                            event.stopPropagation();
                            navigateToTaskCreate(item);
                          }}
                        >
                          去分派
                        </Button>
                      </Space>
                    </List.Item>
                  )}
                />
              </div>
              <Text style={{ color: "#95b8b0", fontSize: 12 }}>
                鼠标滚轮查看更多预警 · 点击预警查看案件 · 去分派生成任务
              </Text>
            </DashboardPanel>

            <DashboardPanel title="高风险被告 TOP5">
              <div style={{ display: "grid", gap: 10 }}>
                {defendantTop.map((item, index) => (
                  <div key={item.name}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <Text
                        onClick={() => navigate(`/dashboard/defendants?name=${encodeURIComponent(item.name)}`)}
                        style={{ color: "#ecfffb", cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 3 }}
                      >
                        {index + 1}. {item.name}
                      </Text>
                      <Text style={{ color: "#facc15" }}>{item.count} 件</Text>
                    </div>
                    <Progress percent={Math.min(100, item.amount / 2)} showInfo={false} strokeColor={index < 2 ? "#e5484d" : "#f97316"} trailColor="rgba(255,255,255,0.1)" />
                  </div>
                ))}
              </div>
            </DashboardPanel>

            <DashboardPanel title="普法推送效果">
              <div style={{ display: "grid", gap: 8 }}>
                <Statistic title={<span style={{ color: "#9fbdb6" }}>推送覆盖</span>} value={12840} suffix="人次" valueStyle={{ color: "#ecfffb" }} />
                <Progress percent={76} strokeColor="#15b8a6" trailColor="rgba(255,255,255,0.1)" />
                <Space wrap>
                  <Tag color="green">阅读率 76%</Tag>
                  <Tag color="cyan">咨询转化 18%</Tag>
                  <Tag color="gold">回访完成 64%</Tag>
                </Space>
              </div>
            </DashboardPanel>
          </aside>

          <footer style={{ gridColumn: "1 / 4" }}>
            <DashboardPanel title="平台级风险闭环管理链路">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 14 }}>
                {supportProgress.map(({ label, value, color, stage }) => (
                  <div
                    key={label}
                    onClick={() => navigate(`/workflow/tasks?stage=${stage || "assigned"}`)}
                    style={{ cursor: "pointer" }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                      <Text style={{ color: "#ecfffb" }}>{label}</Text>
                      <Text style={{ color }}>{value} 件</Text>
                    </div>
                    <Progress percent={Math.min(100, value * 2)} showInfo={false} strokeColor={color} trailColor="rgba(255,255,255,0.1)" />
                  </div>
                ))}
              </div>
            </DashboardPanel>
          </footer>
        </div>
      </section>

      <Drawer
        title={selectedPoint ? `${selectedPoint.name}风险详情` : "风险详情"}
        open={Boolean(selectedPoint)}
        onClose={() => setSelectedPoint(null)}
        width={420}
      >
        {selectedPoint && (
          <Space direction="vertical" size={14} style={{ width: "100%" }}>
            <Tag color={riskColors[selectedPoint.level]}>{riskText[selectedPoint.level]}风险</Tag>
            <Statistic title="风险线索" value={selectedPoint.caseCount} suffix="件" />
            <Statistic title="涉及群众" value={selectedPoint.workers} suffix="人" />
            <Statistic title="涉案金额" value={selectedPoint.amount} suffix="万元" />
            <Card title="高风险主体" size="small">{selectedPoint.owner}</Card>
            <Card title="当前处置状态" size="small">{selectedPoint.status}</Card>
            <Button type="primary" block onClick={() => navigate(`/community-risk/${encodeURIComponent(selectedPoint.name)}/cases`)}>进入社区风险治理</Button>
          </Space>
        )}
      </Drawer>
    </main>
  );
}

export default DashboardPage;
