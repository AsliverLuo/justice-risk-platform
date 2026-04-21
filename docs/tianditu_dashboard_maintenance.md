# 天地图驾驶舱使用、维护与扩展文档

## 1. 模块定位

本模块用于驾驶舱中央区域的欠薪风险地图展示。当前实现采用“天地图在线底图 + 西城区风险点叠加 + 本地 JSON 兜底”的方案。

核心目标：

- 在评审现场展示北京市西城区真实地图底图。
- 以街道、片区工地为单位展示欠薪风险等级。
- 支持点击风险点查看案件数量、涉及人数、涉案金额、处置状态等详情。
- 当天地图 Key 未配置、网络不可用或天地图服务加载失败时，自动切换到本地 JSON 地图，避免中央区域空白。

当前主要文件：

| 文件 | 作用 |
|---|---|
| `frontend/src/pages/Dashboard/index.tsx` | 驾驶舱页面、天地图加载、风险点渲染、详情抽屉 |
| `frontend/public/data/xicheng-risk-map.json` | 北京市西城区本地地图兜底数据 |
| `frontend/.env.example` | 前端环境变量示例，包含天地图 Key 配置项 |
| `frontend/package.json` | 前端依赖，包含 AntV L7、less、Vite 等 |

## 2. 首次使用步骤

### 2.1 申请天地图 Key

进入天地图开放平台申请 Web 服务 Key。当前代码通过 WMTS 服务访问天地图底图，请确保 Key 具备 Web 端调用权限。

### 2.2 写入前端环境变量

进入前端目录：

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/frontend
```

复制环境变量示例：

```bash
cp .env.example .env.local
```

编辑 `.env.local`：

```env
VITE_TIANDITU_TOKEN=你的天地图Key
```

注意事项：

- 变量名必须是 `VITE_TIANDITU_TOKEN`，因为 Vite 只会向前端暴露以 `VITE_` 开头的变量。
- `.env.local` 不应提交到代码仓库，避免 Key 泄露。
- 修改 `.env.local` 后必须重启前端服务。

### 2.3 启动前端

```bash
cd /home/jovyan/data/bugui_v2/web/justice-risk-platform/frontend
npm install
npm run dev
```

浏览器访问 Vite 输出的地址，一般是：

```text
http://localhost:5173
```

进入驾驶舱页面后，中央地图左上角应显示：

```text
天地图 API · 北京市西城区风险热力图
```

如果显示：

```text
未配置 VITE_TIANDITU_TOKEN，已切换为北京市西城区本地 JSON 地图
```

说明当前没有读到天地图 Key，需要检查 `.env.local` 和前端服务是否重启。

## 3. 运行环境要求

建议使用：

| 项目 | 建议版本 |
|---|---|
| Node.js | 20.x 或 22.x |
| npm | 随 Node.js 安装即可 |
| 浏览器 | Chrome、Edge 最新稳定版 |

已知问题：

- Node.js 14 会触发 Vite 依赖中的 `Unexpected token '??='` 错误。
- Windows 环境如果出现 `rolldown native binding` 错误，通常是 `node_modules` 和当前 Node/系统架构不匹配，需要删除 `node_modules` 和 `package-lock.json` 后重新安装。

推荐处理：

```bash
node -v
```

如果低于 Node 20，请切换 Node 版本后重新安装依赖：

```bash
rm -rf node_modules package-lock.json
npm install
npm run dev
```

Windows 下不要直接复制 Linux 机器上的 `node_modules`，必须在本机重新执行 `npm install`。

## 4. 当前地图加载逻辑

驾驶舱地图加载顺序如下：

1. 前端读取 `import.meta.env.VITE_TIANDITU_TOKEN`。
2. 如果 Key 存在，加载天地图 WMTS 在线底图。
3. 使用 AntV L7 在地图上绘制风险点。
4. 点击风险点后打开右侧详情抽屉。
5. 如果 Key 不存在或天地图加载失败，切换到 `xicheng-risk-map.json` 本地 SVG 风格地图。

天地图当前使用两类 WMTS 图层：

| 图层 | 说明 |
|---|---|
| `vec_w` | 天地图矢量底图 |
| `cva_w` | 天地图矢量注记 |

代码中的 URL 结构：

```text
https://t0.tianditu.gov.cn/vec_w/wmts?...&tk=你的Key
https://t0.tianditu.gov.cn/cva_w/wmts?...&tk=你的Key
```

实际运行时会自动使用 `t0` 到 `t7` 多个子域名，提高瓦片加载稳定性。

## 5. 风险点数据维护

当前风险点仍写在 `Dashboard/index.tsx` 的 `riskPoints` 数组中，字段结构如下：

```ts
interface RiskPoint {
  id: string;
  name: string;
  type: "街道" | "工地";
  lng: number;
  lat: number;
  level: "red" | "orange" | "yellow" | "blue";
  caseCount: number;
  workers: number;
  amount: number;
  owner: string;
  status: string;
}
```

字段说明：

| 字段 | 含义 |
|---|---|
| `id` | 唯一标识，建议使用区域或项目拼音 |
| `name` | 地图展示名称 |
| `type` | 街道或工地 |
| `lng` | 经度 |
| `lat` | 纬度 |
| `level` | 风险等级，红橙黄蓝 |
| `caseCount` | 欠薪案件数量 |
| `workers` | 涉及农民工人数 |
| `amount` | 涉案金额，单位万元 |
| `owner` | 高风险主体或主要被告 |
| `status` | 当前处置状态 |

风险等级颜色：

| 等级 | 颜色 | 含义 |
|---|---|---|
| `red` | 红色 | 高风险，建议重点预警 |
| `orange` | 橙色 | 较高风险，建议跟踪处置 |
| `yellow` | 黄色 | 中风险，建议调解或补证 |
| `blue` | 蓝色 | 低风险，建议观察 |

维护建议：

- 经度、纬度使用 WGS84 坐标。
- 同一街道多个工地可以分开建点，也可以聚合为街道点。
- 评审演示数据建议保持 5 到 12 个风险点，避免地图过密。
- `amount` 建议保留一位小数，单位统一为万元。

## 6. 本地 JSON 地图维护

本地兜底文件：

```text
frontend/public/data/xicheng-risk-map.json
```

该文件用于无 Key、无网络或天地图加载失败时展示西城区本地地图。结构包含：

| 字段 | 说明 |
|---|---|
| `name` | 地图名称 |
| `bbox` | 地图经纬度范围 |
| `features` | 街道区域多边形 |
| `roads` | 道路折线 |
| `labels` | 地名标注 |

示例结构：

```json
{
  "name": "北京市西城区风险地图",
  "bbox": [116.33, 39.86, 116.42, 39.96],
  "features": [],
  "roads": [],
  "labels": []
}
```

维护要求：

- `bbox` 顺序为 `[最小经度, 最小纬度, 最大经度, 最大纬度]`。
- `features.coordinates` 必须是闭合区域的坐标点数组。
- `labels` 用于展示街道或片区名称。
- JSON 修改后建议执行格式检查：

```bash
python -m json.tool frontend/public/data/xicheng-risk-map.json
```

## 7. 常见问题排查

### 7.1 地图仍然显示本地 JSON，不显示天地图

检查项：

- `.env.local` 是否位于 `frontend/` 目录下。
- Key 是否写成 `VITE_TIANDITU_TOKEN=xxx`。
- 写入 Key 后是否重启了 `npm run dev`。
- 浏览器控制台是否有天地图请求 403、401 或网络错误。
- 当前网络是否能访问 `tianditu.gov.cn`。

### 7.2 中央地图空白

优先检查浏览器控制台：

- 如果报 `VITE_TIANDITU_TOKEN` 未配置，说明 Key 没读到。
- 如果报瓦片请求失败，说明 Key、网络或服务权限有问题。
- 如果报 AntV L7 依赖错误，执行 `npm install`。
- 如果报 Less 错误，确认已安装：

```bash
npm install -D less
```

### 7.3 Vite 启动时报 `Unexpected token '??='`

这是 Node 版本过低导致。切换到 Node 20 或 22。

### 7.4 Windows 报 native binding 不是有效 Win32 应用

一般是依赖安装环境和运行环境不一致。处理方式：

```powershell
cd D:\智能检察平台\justice-risk-platform\justice-risk-platform\frontend
rmdir /s /q node_modules
del package-lock.json
npm install
npm run dev
```

## 8. 后续扩展方案

### 8.1 将风险点从静态数组改为后端接口

当前 `riskPoints` 是前端静态数据。后续应迁移到后端驾驶舱聚合接口：

```text
GET /api/v1/dashboard/risk-map
```

建议返回：

```json
{
  "region": "北京市西城区",
  "center": [116.365, 39.91],
  "zoom": 12.1,
  "points": [
    {
      "id": "xicheng-zhanlanlu",
      "name": "展览路街道",
      "type": "街道",
      "lng": 116.345,
      "lat": 39.923,
      "level": "red",
      "caseCount": 46,
      "workers": 182,
      "amount": 386.4,
      "owner": "北京某建筑劳务公司",
      "status": "联合核查中"
    }
  ]
}
```

前端改造方向：

- 新增 `frontend/src/modules/dashboard/api.ts`。
- 在页面加载时调用后端接口。
- 接口失败时继续使用内置演示数据。
- 风险点类型定义迁移到 `frontend/src/modules/dashboard/types.ts`。

### 8.2 增加街道边界真实 GeoJSON

当前本地 JSON 是演示用简化边界。后续可以换成真实街道边界 GeoJSON：

```text
frontend/public/data/xicheng-streets.geojson
```

建议做法：

- 使用标准 GeoJSON `FeatureCollection`。
- 每个 Feature 带上 `name`、`riskLevel`、`caseCount`。
- 用 L7 `PolygonLayer` 绘制面图层。
- 风险点继续用 `PointLayer` 绘制。

### 8.3 支持热力图效果

当前是风险点气泡图。后续可以增加真正的热力图：

- 点位较少时使用气泡图更清晰。
- 点位超过 30 个后可启用 L7 `HeatmapLayer`。
- 热力权重建议使用 `caseCount`、`workers` 或综合风险分。

建议权重：

```text
riskWeight = caseCount * 0.4 + workers * 0.3 + amount * 0.3
```

### 8.4 支持行政区切换

后续如果不只展示西城区，可以增加区域选择：

| 区域 | center | zoom | 本地兜底 JSON |
|---|---|---|---|
| 北京市西城区 | `[116.365, 39.91]` | `12.1` | `xicheng-risk-map.json` |
| 北京市东城区 | 待补充 | 待补充 | `dongcheng-risk-map.json` |
| 北京市朝阳区 | 待补充 | 待补充 | `chaoyang-risk-map.json` |

前端可以新增配置：

```ts
const regionMapConfig = {
  xicheng: {
    name: "北京市西城区",
    center: [116.365, 39.91],
    zoom: 12.1,
    fallbackJson: "/data/xicheng-risk-map.json",
  },
};
```

### 8.5 天地图 Key 的生产部署

开发环境：

```text
frontend/.env.local
```

生产环境：

- Docker Compose 或 CI/CD 注入 `VITE_TIANDITU_TOKEN`。
- 重新执行前端构建。
- 不要把真实 Key 写入 `.env.example`。

示例：

```bash
VITE_TIANDITU_TOKEN=真实Key npm run build
```

注意：Vite 的环境变量会在构建时打入前端产物。生产 Key 仍可能被浏览器看到，因此必须在天地图控制台配置域名白名单和调用额度限制。

## 9. 建议的演进优先级

1. 保持当前天地图在线底图和本地 JSON 兜底稳定。
2. 把 `riskPoints` 从前端静态数组迁移到后端 `dashboard` 聚合接口。
3. 增加真实街道 GeoJSON 面图层，形成街道级红橙黄蓝风险区。
4. 增加工地、企业、被告主体三类图层开关。
5. 增加时间维度筛选，例如本月、本季度、近一年。
6. 增加点击街道下钻，展示案件列表、被告 TOP、治理建议和普法推送效果。
7. 对接真实预警引擎，把实时预警列表和地图点位联动。

## 10. 交接检查清单

上线或演示前建议逐项确认：

- [ ] Node.js 版本为 20 或 22。
- [ ] `npm install` 已执行成功。
- [ ] `frontend/.env.local` 已配置 `VITE_TIANDITU_TOKEN`。
- [ ] 修改 Key 后已重启 `npm run dev`。
- [ ] 驾驶舱中央地图显示天地图底图。
- [ ] 风险点能正常显示红橙黄蓝等级。
- [ ] 点击风险点能打开详情抽屉。
- [ ] 断网或删除 Key 后，本地 JSON 兜底地图能正常显示。
- [ ] `xicheng-risk-map.json` 能通过 JSON 格式检查。
- [ ] 评审机器浏览器能访问 `tianditu.gov.cn`。

