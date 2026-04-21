import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Form,
  Input,
  InputNumber,
  List,
  Row,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from "antd";
import { useMemo, useState } from "react";

import {
  analyzeCaseText,
  type CaseTextAnalyzeResponse,
} from "../../services/analysis";
import {
  generateRecommendation,
  type RecommendationGenerateResponse,
} from "../../services/recommendation";
import {
  recommendPropaganda,
  type PropagandaRecommendResponse,
} from "../../services/propaganda";

const { Paragraph, Text, Title } = Typography;

interface NlpFormValues {
  title: string;
  text: string;
  scopeName: string;
  scopeId: string;
  peopleCount: number;
  repeatDefendantCount: number;
  preferLlm: boolean;
}

const defaultText =
  "张三、李四等6名工人在某建筑工地从事木工和钢筋工工作，约定工资300元每天。工程结束后，某建筑劳务公司仍拖欠工资合计26800元，多次催要未果。工人反映同一公司近期还涉及其他项目欠薪。";

function mapRiskType(caseType: string, text: string) {
  if (caseType === "labor_service_dispute") {
    return "wage_arrears";
  }
  if (caseType === "labor_dispute") {
    return "labor_dispute";
  }
  if (text.includes("欠薪") || text.includes("工资") || text.includes("劳务费")) {
    return "wage_arrears";
  }
  return "other";
}

function buildContextTags(analysis: CaseTextAnalyzeResponse, riskType: string) {
  const tags = new Set<string>([riskType, analysis.case_type]);
  analysis.risk_hints
    .filter((item) => item.triggered)
    .forEach((item) => tags.add(item.label));
  analysis.matched_laws.forEach((law) => {
    law.scenario_tags.forEach((tag) => tags.add(tag));
  });
  if (analysis.entities.amounts.length > 0) tags.add("amount_related");
  if (analysis.entities.companies.length > 0) tags.add("enterprise_related");
  return Array.from(tags).filter(Boolean);
}

function renderStringList(items: string[], emptyText: string) {
  if (!items.length) {
    return <Text type="secondary">{emptyText}</Text>;
  }
  return (
    <Space wrap>
      {items.map((item) => (
        <Tag key={item}>{item}</Tag>
      ))}
    </Space>
  );
}

function NlpDemoPage() {
  const [form] = Form.useForm<NlpFormValues>();
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<CaseTextAnalyzeResponse | null>(null);
  const [recommendation, setRecommendation] =
    useState<RecommendationGenerateResponse | null>(null);
  const [propaganda, setPropaganda] = useState<PropagandaRecommendResponse | null>(
    null
  );

  const riskType = useMemo(() => {
    if (!analysis) return "";
    return mapRiskType(analysis.case_type, form.getFieldValue("text") || "");
  }, [analysis, form]);

  const handleAnalyze = async (values: NlpFormValues) => {
    setLoading(true);
    setAnalysis(null);
    setRecommendation(null);
    setPropaganda(null);

    try {
      const analysisResult = await analyzeCaseText({
        title: values.title,
        text: values.text,
        people_count: values.peopleCount,
        repeat_defendant_count: values.repeatDefendantCount,
        top_k_laws: 5,
        persist_to_corpus: false,
        prefer_llm: Boolean(values.preferLlm),
      });

      const resolvedRiskType = mapRiskType(analysisResult.case_type, values.text);
      const resolvedScopeId = values.scopeName || values.scopeId;
      const contextTags = buildContextTags(analysisResult, resolvedRiskType);
      const relatedLawNames = Array.from(
        new Set(analysisResult.matched_laws.map((item) => item.law_name))
      );

      const [recommendationResult, propagandaResult] = await Promise.all([
        generateRecommendation({
          scope_type: "community",
          scope_id: resolvedScopeId,
          risk_type: resolvedRiskType,
          context_summary: `${values.scopeName}：${analysisResult.summary}`,
          case_summaries: [values.text],
          template_limit: 3,
          case_limit: 5,
          law_top_k: 5,
          prefer_llm: Boolean(values.preferLlm),
          persist: false,
          dashboard_visible: true,
        }),
        recommendPropaganda({
          scope_type: "community",
          scope_id: resolvedScopeId,
          risk_type: resolvedRiskType,
          context_tags: contextTags,
          related_law_names: relatedLawNames,
          limit: 5,
          persist: false,
          dashboard_visible: true,
        }),
      ]);

      setAnalysis(analysisResult);
      setRecommendation(recommendationResult);
      setPropaganda(propagandaResult);
      message.success("案件 NLP 分析、治理建议和普法内容已生成");
    } catch (error) {
      console.error(error);
      message.error("生成失败，请确认后端服务已启动并完成数据库初始化");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: "100vh", background: "#f3f6f8", padding: 32 }}>
      <section style={{ maxWidth: 1240, margin: "0 auto", display: "grid", gap: 24 }}>
        <Card bordered={false} style={{ borderRadius: 8 }}>
          <Title level={2} style={{ marginBottom: 8 }}>
            案件 NLP 研判与治理生成
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            按检察平台处理案件逻辑，将文本受理、案件分类、实体抽取、法条关联、治理建议和普法推送串成一条可演示链路。
          </Paragraph>
        </Card>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={10}>
            <Card title="案件文本受理" bordered={false} style={{ borderRadius: 8 }}>
              <Form<NlpFormValues>
                form={form}
                layout="vertical"
                initialValues={{
                  title: "欠薪纠纷风险线索",
                  text: defaultText,
                  scopeName: "天河区某街道",
                  scopeId: "demo-community-001",
                  peopleCount: 6,
                  repeatDefendantCount: 2,
                  preferLlm: false,
                }}
                onFinish={handleAnalyze}
              >
                <Form.Item
                  label="案件标题"
                  name="title"
                  rules={[{ required: true, message: "请输入案件标题" }]}
                >
                  <Input placeholder="请输入案件标题" />
                </Form.Item>

                <Row gutter={12}>
                  <Col span={12}>
                    <Form.Item
                      label="治理对象"
                      name="scopeName"
                      rules={[{ required: true, message: "请输入治理对象" }]}
                    >
                      <Input placeholder="例如：某街道" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      label="对象编号"
                      name="scopeId"
                      rules={[{ required: true, message: "请输入对象编号" }]}
                    >
                      <Input placeholder="community id" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={12}>
                  <Col span={12}>
                    <Form.Item label="涉及人数" name="peopleCount">
                      <InputNumber min={1} style={{ width: "100%" }} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="重复主体次数" name="repeatDefendantCount">
                      <InputNumber min={1} style={{ width: "100%" }} />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item
                  label="案件文本"
                  name="text"
                  rules={[{ required: true, message: "请输入案件文本" }]}
                >
                  <Input.TextArea rows={10} placeholder="输入投诉、线索、判例或案件描述" />
                </Form.Item>

                <Alert
                  type="info"
                  showIcon
                  style={{ marginBottom: 16, borderRadius: 8 }}
                  message="默认使用规则模式。配置 LLM key 后，可在接口层切换为大模型增强。"
                />

                <Button type="primary" htmlType="submit" loading={loading} block>
                  一键分析并生成
                </Button>
              </Form>
            </Card>
          </Col>

          <Col xs={24} lg={14}>
            <Spin spinning={loading}>
              <div style={{ display: "grid", gap: 16 }}>
                <Card title="NLP 识别结果" bordered={false} style={{ borderRadius: 8 }}>
                  {!analysis ? (
                    <Text type="secondary">提交案件文本后显示分类、实体和法条关联。</Text>
                  ) : (
                    <Space direction="vertical" size={16} style={{ width: "100%" }}>
                      <Descriptions column={2} bordered size="small">
                        <Descriptions.Item label="案件类型">
                          <Tag color="blue">{analysis.case_type}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="风险类型">
                          <Tag color="orange">{riskType}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="分类模式">
                          {analysis.classify_mode}
                        </Descriptions.Item>
                        <Descriptions.Item label="实体模式">
                          {analysis.entity_mode}
                        </Descriptions.Item>
                      </Descriptions>
                      <Paragraph>{analysis.summary}</Paragraph>
                      <div>
                        <Text strong>人员：</Text>{" "}
                        {renderStringList(analysis.entities.persons, "未识别")}
                      </div>
                      <div>
                        <Text strong>企业：</Text>{" "}
                        {renderStringList(analysis.entities.companies, "未识别")}
                      </div>
                      <div>
                        <Text strong>金额：</Text>{" "}
                        {renderStringList(analysis.entities.amounts, "未识别")}
                      </div>
                      <div>
                        <Text strong>项目/地址：</Text>{" "}
                        {renderStringList(
                          [...analysis.entities.projects, ...analysis.entities.addresses],
                          "未识别"
                        )}
                      </div>
                    </Space>
                  )}
                </Card>

                <Card title="法条关联" bordered={false} style={{ borderRadius: 8 }}>
                  {!analysis?.matched_laws.length ? (
                    <Text type="secondary">暂无匹配法条。可先运行法律知识库种子脚本。</Text>
                  ) : (
                    <List
                      dataSource={analysis.matched_laws}
                      renderItem={(item) => (
                        <List.Item>
                          <List.Item.Meta
                            title={`${item.law_name} ${item.article_no}`}
                            description={item.content}
                          />
                          <Tag>{Math.round(item.score * 100)}分</Tag>
                        </List.Item>
                      )}
                    />
                  )}
                </Card>
              </div>
            </Spin>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="治理建议生成" bordered={false} style={{ borderRadius: 8 }}>
              {!recommendation ? (
                <Text type="secondary">完成 NLP 分析后自动生成治理建议。</Text>
              ) : (
                <Space direction="vertical" size={16} style={{ width: "100%" }}>
                  <div>
                    <Title level={4} style={{ marginBottom: 8 }}>
                      {recommendation.recommendation.title}
                    </Title>
                    <Tag color="processing">{recommendation.recommendation.source_mode}</Tag>
                    <Tag>{recommendation.recommendation.recommendation_level}</Tag>
                  </div>
                  <Paragraph>{recommendation.recommendation.summary}</Paragraph>
                  <List
                    header={<Text strong>处置动作</Text>}
                    dataSource={recommendation.recommendation.action_items}
                    renderItem={(item) => <List.Item>{item}</List.Item>}
                  />
                  <div>
                    <Text strong>协同部门：</Text>{" "}
                    {renderStringList(
                      recommendation.recommendation.departments,
                      "暂无部门建议"
                    )}
                  </div>
                </Space>
              )}
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="普法内容引擎" bordered={false} style={{ borderRadius: 8 }}>
              {!propaganda ? (
                <Text type="secondary">完成 NLP 分析后自动推荐普法内容。</Text>
              ) : propaganda.items.length === 0 ? (
                <Alert
                  type="warning"
                  showIcon
                  style={{ borderRadius: 8 }}
                  message="未命中普法内容"
                  description="请先在后端运行 python -m scripts.seed_propaganda_articles，导入普法文章后再试。"
                />
              ) : (
                <List
                  dataSource={propaganda.items}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        title={item.title}
                        description={
                          <Space direction="vertical" size={4}>
                            <Text>{item.summary || item.match_reason}</Text>
                            <Space wrap>
                              {item.matched_scenario_tags.map((tag) => (
                                <Tag key={tag}>{tag}</Tag>
                              ))}
                            </Space>
                          </Space>
                        }
                      />
                      <Tag color="green">{Math.round(item.recommendation_score)}分</Tag>
                    </List.Item>
                  )}
                />
              )}
            </Card>
          </Col>
        </Row>
      </section>
    </main>
  );
}

export default NlpDemoPage;
