import { useState } from 'react'

const initialFormData = {
  applicant: {
    name: '',
    gender: '',
    birth_date: '',
    ethnicity: '',
    id_number: '',
    phone: '',
    hukou_address: '',
    current_address: '',
    id_card_front: '',
    id_card_back: '',
    signature_file: '',
    has_agent: false,
    agent_info: '',
  },
  work_info: {
    work_start_date: '',
    work_end_date: '',
    actual_work_days: 0,
    project_name: '',
    work_address: '',
    job_type: '',
    agreed_wage_standard: '',
    total_wage_due: 0,
    paid_amount: 0,
    unpaid_amount: 0,
    wage_calc_desc: '',
    employer_name: '',
    employer_phone: '',
    has_repeated_demand: false,
    demand_desc: '',
  },
  defendants: [
    {
      defendant_type: '',
      name: '',
      credit_code_or_id_number: '',
      phone: '',
      address: '',
      legal_representative: '',
      legal_representative_title: '',
      role_type: '',
      is_actual_controller: false,
      has_payment_promise: false,
      project_relation_desc: '',
    },
  ],
  evidences: [
    {
      evidence_type: '',
      file_path: '',
      description: '',
    },
  ],
  document_options: {
    court_name: '',
    case_cause: '劳务合同纠纷',
    apply_support_prosecution: true,
    claim_litigation_cost: true,
    document_types: [],
  },
}

function App() {
  const [formData, setFormData] = useState(initialFormData)
  const [result, setResult] = useState('还没有提交案件')
  const [submitting, setSubmitting] = useState(false)

  const handleNestedChange = (section, field, value) => {
    setFormData((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }))
  }

  const handleDefendantChange = (index, field, value) => {
    const updated = [...formData.defendants]
    updated[index][field] = value
    setFormData((prev) => ({
      ...prev,
      defendants: updated,
    }))
  }

  const addDefendant = () => {
    setFormData((prev) => ({
      ...prev,
      defendants: [
        ...prev.defendants,
        {
          defendant_type: '',
          name: '',
          credit_code_or_id_number: '',
          phone: '',
          address: '',
          legal_representative: '',
          legal_representative_title: '',
          role_type: '',
          is_actual_controller: false,
          has_payment_promise: false,
          project_relation_desc: '',
        },
      ],
    }))
  }

  const removeDefendant = (index) => {
    if (formData.defendants.length === 1) return
    const updated = formData.defendants.filter((_, i) => i !== index)
    setFormData((prev) => ({
      ...prev,
      defendants: updated,
    }))
  }

  const handleEvidenceChange = (index, field, value) => {
    const updated = [...formData.evidences]
    updated[index][field] = value
    setFormData((prev) => ({
      ...prev,
      evidences: updated,
    }))
  }

  const addEvidence = () => {
    setFormData((prev) => ({
      ...prev,
      evidences: [
        ...prev.evidences,
        {
          evidence_type: '',
          file_path: '',
          description: '',
        },
      ],
    }))
  }

  const removeEvidence = (index) => {
    if (formData.evidences.length === 1) return
    const updated = formData.evidences.filter((_, i) => i !== index)
    setFormData((prev) => ({
      ...prev,
      evidences: updated,
    }))
  }

  const handleDocumentTypeChange = (type, checked) => {
    let updatedTypes = [...formData.document_options.document_types]

    if (checked) {
      if (!updatedTypes.includes(type)) {
        updatedTypes.push(type)
      }
    } else {
      updatedTypes = updatedTypes.filter((item) => item !== type)
    }

    setFormData((prev) => ({
      ...prev,
      document_options: {
        ...prev.document_options,
        document_types: updatedTypes,
      },
    }))
  }

  const buildPayload = () => {
    return {
      applicant: {
        ...formData.applicant,
        has_agent: Boolean(formData.applicant.has_agent),
      },
      work_info: {
        ...formData.work_info,
        actual_work_days: Number(formData.work_info.actual_work_days) || 0,
        total_wage_due: Number(formData.work_info.total_wage_due) || 0,
        paid_amount: Number(formData.work_info.paid_amount) || 0,
        unpaid_amount: Number(formData.work_info.unpaid_amount) || 0,
        has_repeated_demand: Boolean(formData.work_info.has_repeated_demand),
      },
      defendants: formData.defendants.map((item) => ({
        ...item,
        is_actual_controller: Boolean(item.is_actual_controller),
        has_payment_promise: Boolean(item.has_payment_promise),
      })),
      evidences: formData.evidences,
      document_options: {
        ...formData.document_options,
        apply_support_prosecution: Boolean(
          formData.document_options.apply_support_prosecution
        ),
        claim_litigation_cost: Boolean(
          formData.document_options.claim_litigation_cost
        ),
      },
    }
  }

  const handleSubmit = async () => {
    try {
      setSubmitting(true)
      const payload = buildPayload()

      const response = await fetch('http://127.0.0.1:8000/cases', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      const data = await response.json()
      setResult(JSON.stringify(data, null, 2))
    } catch (error) {
      setResult('提交失败：' + error.message)
    } finally {
      setSubmitting(false)
    }
  }

  const sectionStyle = {
    background: '#ffffff',
    padding: '24px',
    borderRadius: '12px',
    marginBottom: '24px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  }

  const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    fontSize: '15px',
    borderRadius: '8px',
    border: '1px solid #ccc',
    boxSizing: 'border-box',
  }

  const labelStyle = {
    display: 'block',
    marginBottom: '6px',
    fontWeight: 600,
  }

  const grid2 = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
  }

  const cardStyle = {
    border: '1px solid #ddd',
    borderRadius: '10px',
    padding: '16px',
    marginBottom: '16px',
    background: '#fafafa',
  }

  return (
    <div
      style={{
        padding: '32px',
        fontFamily: 'Arial, sans-serif',
        maxWidth: '1100px',
        margin: '0 auto',
        background: '#f5f7fb',
      }}
    >
      <h1 style={{ marginBottom: '8px' }}>清朗法治 · 支持起诉案件录入系统</h1>
      <p style={{ color: '#666', marginBottom: '24px' }}>
        按 5 个模块录入案件信息，并提交给后端接口。
      </p>

      <div style={sectionStyle}>
        <h2>第 1 步：申请人信息</h2>
        <div style={grid2}>
          <div>
            <label style={labelStyle}>姓名</label>
            <input
              style={inputStyle}
              value={formData.applicant.name}
              onChange={(e) =>
                handleNestedChange('applicant', 'name', e.target.value)
              }
            />
          </div>
          <div>
            <label style={labelStyle}>性别</label>
            <select
              style={inputStyle}
              value={formData.applicant.gender}
              onChange={(e) =>
                handleNestedChange('applicant', 'gender', e.target.value)
              }
            >
              <option value="">请选择</option>
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>出生日期</label>
            <input
              type="date"
              style={inputStyle}
              value={formData.applicant.birth_date}
              onChange={(e) =>
                handleNestedChange('applicant', 'birth_date', e.target.value)
              }
            />
          </div>
          <div>
            <label style={labelStyle}>民族</label>
            <input
              style={inputStyle}
              value={formData.applicant.ethnicity}
              onChange={(e) =>
                handleNestedChange('applicant', 'ethnicity', e.target.value)
              }
            />
          </div>

          <div>
            <label style={labelStyle}>身份证号</label>
            <input
              style={inputStyle}
              value={formData.applicant.id_number}
              onChange={(e) =>
                handleNestedChange('applicant', 'id_number', e.target.value)
              }
            />
          </div>
          <div>
            <label style={labelStyle}>联系电话</label>
            <input
              style={inputStyle}
              value={formData.applicant.phone}
              onChange={(e) =>
                handleNestedChange('applicant', 'phone', e.target.value)
              }
            />
          </div>
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={labelStyle}>户籍地址</label>
          <input
            style={inputStyle}
            value={formData.applicant.hukou_address}
            onChange={(e) =>
              handleNestedChange('applicant', 'hukou_address', e.target.value)
            }
          />
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={labelStyle}>经常居住地</label>
          <input
            style={inputStyle}
            value={formData.applicant.current_address}
            onChange={(e) =>
              handleNestedChange('applicant', 'current_address', e.target.value)
            }
          />
        </div>

        <div style={{ ...grid2, marginTop: '16px' }}>
          <div>
            <label style={labelStyle}>身份证正面（先填文件路径占位）</label>
            <input
              style={inputStyle}
              value={formData.applicant.id_card_front}
              onChange={(e) =>
                handleNestedChange('applicant', 'id_card_front', e.target.value)
              }
            />
          </div>
          <div>
            <label style={labelStyle}>身份证反面（先填文件路径占位）</label>
            <input
              style={inputStyle}
              value={formData.applicant.id_card_back}
              onChange={(e) =>
                handleNestedChange('applicant', 'id_card_back', e.target.value)
              }
            />
          </div>
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={labelStyle}>电子签名（先填文件路径占位）</label>
          <input
            style={inputStyle}
            value={formData.applicant.signature_file}
            onChange={(e) =>
              handleNestedChange('applicant', 'signature_file', e.target.value)
            }
          />
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={{ ...labelStyle, display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={formData.applicant.has_agent}
              onChange={(e) =>
                handleNestedChange('applicant', 'has_agent', e.target.checked)
              }
            />
            是否有代理人
          </label>
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={labelStyle}>代理人信息</label>
          <textarea
            style={{ ...inputStyle, minHeight: '80px' }}
            value={formData.applicant.agent_info}
            onChange={(e) =>
              handleNestedChange('applicant', 'agent_info', e.target.value)
            }
          />
        </div>
      </div>

      <div style={sectionStyle}>
        <h2>第 2 步：工作与欠薪事实</h2>
        <div style={grid2}>
          <div>
            <label style={labelStyle}>工作开始日期</label>
            <input
              type="date"
              style={inputStyle}
              value={formData.work_info.work_start_date}
              onChange={(e) =>
                handleNestedChange('work_info', 'work_start_date', e.target.value)
              }
            />
          </div>
          <div>
            <label style={labelStyle}>工作结束日期</label>
            <input
              type="date"
              style={inputStyle}
              value={formData.work_info.work_end_date}
              onChange={(e) =>
                handleNestedChange('work_info', 'work_end_date', e.target.value)
              }
            />
          </div>

          <div>
            <label style={labelStyle}>实际工作天数</label>
            <input
              type="number"
              style={inputStyle}
              value={formData.work_info.actual_work_days}
              onChange={(e) =>
                handleNestedChange('work_info', 'actual_work_days', e.target.value)
              }
            />
          </div>
          <div>
            <label style={labelStyle}>工种 / 岗位</label>
            <input
              style={inputStyle}
              value={formData.work_info.job_type}
              onChange={(e) =>
                handleNestedChange('work_info', 'job_type', e.target.value)
              }
            />
          </div>

          <div>
            <label style={labelStyle}>项目 / 工地名称</label>
            <input
              style={inputStyle}
              value={formData.work_info.project_name}
              onChange={(e) =>
                handleNestedChange('work_info', 'project_name', e.target.value)
              }
            />
          </div>
          <div>
            <label style={labelStyle}>欠薪方名称</label>
            <input
              style={inputStyle}
              value={formData.work_info.employer_name}
              onChange={(e) =>
                handleNestedChange('work_info', 'employer_name', e.target.value)
              }
            />
          </div>

          <div>
            <label style={labelStyle}>约定工资标准</label>
            <input
              style={inputStyle}
              placeholder="如：300元/天"
              value={formData.work_info.agreed_wage_standard}
              onChange={(e) =>
                handleNestedChange(
                  'work_info',
                  'agreed_wage_standard',
                  e.target.value
                )
              }
            />
          </div>
          <div>
            <label style={labelStyle}>欠薪方联系方式</label>
            <input
              style={inputStyle}
              value={formData.work_info.employer_phone}
              onChange={(e) =>
                handleNestedChange('work_info', 'employer_phone', e.target.value)
              }
            />
          </div>

          <div>
            <label style={labelStyle}>应得总劳务费</label>
            <input
              type="number"
              style={inputStyle}
              value={formData.work_info.total_wage_due}
              onChange={(e) =>
                handleNestedChange('work_info', 'total_wage_due', e.target.value)
              }
            />
          </div>
          <div>
            <label style={labelStyle}>已支付金额</label>
            <input
              type="number"
              style={inputStyle}
              value={formData.work_info.paid_amount}
              onChange={(e) =>
                handleNestedChange('work_info', 'paid_amount', e.target.value)
              }
            />
          </div>

          <div>
            <label style={labelStyle}>尚欠金额</label>
            <input
              type="number"
              style={inputStyle}
              value={formData.work_info.unpaid_amount}
              onChange={(e) =>
                handleNestedChange('work_info', 'unpaid_amount', e.target.value)
              }
            />
          </div>
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={labelStyle}>具体地址</label>
          <input
            style={inputStyle}
            value={formData.work_info.work_address}
            onChange={(e) =>
              handleNestedChange('work_info', 'work_address', e.target.value)
            }
          />
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={labelStyle}>欠薪计算方式说明</label>
          <textarea
            style={{ ...inputStyle, minHeight: '80px' }}
            value={formData.work_info.wage_calc_desc}
            onChange={(e) =>
              handleNestedChange('work_info', 'wage_calc_desc', e.target.value)
            }
          />
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={{ ...labelStyle, display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={formData.work_info.has_repeated_demand}
              onChange={(e) =>
                handleNestedChange(
                  'work_info',
                  'has_repeated_demand',
                  e.target.checked
                )
              }
            />
            是否多次催要未果
          </label>
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={labelStyle}>催要经过</label>
          <textarea
            style={{ ...inputStyle, minHeight: '80px' }}
            value={formData.work_info.demand_desc}
            onChange={(e) =>
              handleNestedChange('work_info', 'demand_desc', e.target.value)
            }
          />
        </div>
      </div>

      <div style={sectionStyle}>
        <h2>第 3 步：被告与责任链</h2>
        {formData.defendants.map((defendant, index) => (
          <div key={index} style={cardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <h3 style={{ margin: 0 }}>被告 {index + 1}</h3>
              <button
                type="button"
                onClick={() => removeDefendant(index)}
                style={{
                  padding: '6px 12px',
                  border: 'none',
                  borderRadius: '6px',
                  background: '#d9534f',
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                删除
              </button>
            </div>

            <div style={grid2}>
              <div>
                <label style={labelStyle}>被告类型</label>
                <select
                  style={inputStyle}
                  value={defendant.defendant_type}
                  onChange={(e) =>
                    handleDefendantChange(index, 'defendant_type', e.target.value)
                  }
                >
                  <option value="">请选择</option>
                  <option value="company">公司</option>
                  <option value="person">个人</option>
                </select>
              </div>
              <div>
                <label style={labelStyle}>名称</label>
                <input
                  style={inputStyle}
                  value={defendant.name}
                  onChange={(e) =>
                    handleDefendantChange(index, 'name', e.target.value)
                  }
                />
              </div>

              <div>
                <label style={labelStyle}>统一社会信用代码 / 身份证号</label>
                <input
                  style={inputStyle}
                  value={defendant.credit_code_or_id_number}
                  onChange={(e) =>
                    handleDefendantChange(
                      index,
                      'credit_code_or_id_number',
                      e.target.value
                    )
                  }
                />
              </div>
              <div>
                <label style={labelStyle}>联系电话</label>
                <input
                  style={inputStyle}
                  value={defendant.phone}
                  onChange={(e) =>
                    handleDefendantChange(index, 'phone', e.target.value)
                  }
                />
              </div>

              <div>
                <label style={labelStyle}>法定代表人</label>
                <input
                  style={inputStyle}
                  value={defendant.legal_representative}
                  onChange={(e) =>
                    handleDefendantChange(
                      index,
                      'legal_representative',
                      e.target.value
                    )
                  }
                />
              </div>
              <div>
                <label style={labelStyle}>法定代表人职务</label>
                <input
                  style={inputStyle}
                  value={defendant.legal_representative_title}
                  onChange={(e) =>
                    handleDefendantChange(
                      index,
                      'legal_representative_title',
                      e.target.value
                    )
                  }
                />
              </div>

              <div>
                <label style={labelStyle}>角色类型</label>
                <select
                  style={inputStyle}
                  value={defendant.role_type}
                  onChange={(e) =>
                    handleDefendantChange(index, 'role_type', e.target.value)
                  }
                >
                  <option value="">请选择</option>
                  <option value="发包方">发包方</option>
                  <option value="承包方">承包方</option>
                  <option value="担保方">担保方</option>
                  <option value="实控人">实控人</option>
                  <option value="直接雇佣人">直接雇佣人</option>
                  <option value="其他">其他</option>
                </select>
              </div>
            </div>

            <div style={{ marginTop: '16px' }}>
              <label style={labelStyle}>地址</label>
              <input
                style={inputStyle}
                value={defendant.address}
                onChange={(e) =>
                  handleDefendantChange(index, 'address', e.target.value)
                }
              />
            </div>

            <div style={{ ...grid2, marginTop: '16px' }}>
              <label style={{ ...labelStyle, display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="checkbox"
                  checked={defendant.is_actual_controller}
                  onChange={(e) =>
                    handleDefendantChange(
                      index,
                      'is_actual_controller',
                      e.target.checked
                    )
                  }
                />
                是否为实控人
              </label>

              <label style={{ ...labelStyle, display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="checkbox"
                  checked={defendant.has_payment_promise}
                  onChange={(e) =>
                    handleDefendantChange(
                      index,
                      'has_payment_promise',
                      e.target.checked
                    )
                  }
                />
                是否曾承诺支付工资
              </label>
            </div>

            <div style={{ marginTop: '16px' }}>
              <label style={labelStyle}>工程关系说明</label>
              <textarea
                style={{ ...inputStyle, minHeight: '80px' }}
                value={defendant.project_relation_desc}
                onChange={(e) =>
                  handleDefendantChange(
                    index,
                    'project_relation_desc',
                    e.target.value
                  )
                }
              />
            </div>
          </div>
        ))}

        <button
          type="button"
          onClick={addDefendant}
          style={{
            padding: '10px 16px',
            border: 'none',
            borderRadius: '8px',
            background: '#1677ff',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          + 新增被告
        </button>
      </div>

      <div style={sectionStyle}>
        <h2>第 4 步：证据与附件</h2>
        {formData.evidences.map((evidence, index) => (
          <div key={index} style={cardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <h3 style={{ margin: 0 }}>证据 {index + 1}</h3>
              <button
                type="button"
                onClick={() => removeEvidence(index)}
                style={{
                  padding: '6px 12px',
                  border: 'none',
                  borderRadius: '6px',
                  background: '#d9534f',
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                删除
              </button>
            </div>

            <div style={grid2}>
              <div>
                <label style={labelStyle}>证据类型</label>
                <select
                  style={inputStyle}
                  value={evidence.evidence_type}
                  onChange={(e) =>
                    handleEvidenceChange(index, 'evidence_type', e.target.value)
                  }
                >
                  <option value="">请选择</option>
                  <option value="payroll_list">花名册 / 工资册</option>
                  <option value="labor_contract">劳务合同</option>
                  <option value="construction_contract">施工合同</option>
                  <option value="chat_record">聊天记录</option>
                  <option value="call_record">通话记录</option>
                  <option value="payment_promise">欠薪承诺材料</option>
                  <option value="other">其他凭证</option>
                </select>
              </div>
              <div>
                <label style={labelStyle}>文件路径（先填占位）</label>
                <input
                  style={inputStyle}
                  value={evidence.file_path}
                  onChange={(e) =>
                    handleEvidenceChange(index, 'file_path', e.target.value)
                  }
                />
              </div>
            </div>

            <div style={{ marginTop: '16px' }}>
              <label style={labelStyle}>证据说明</label>
              <textarea
                style={{ ...inputStyle, minHeight: '80px' }}
                value={evidence.description}
                onChange={(e) =>
                  handleEvidenceChange(index, 'description', e.target.value)
                }
              />
            </div>
          </div>
        ))}

        <button
          type="button"
          onClick={addEvidence}
          style={{
            padding: '10px 16px',
            border: 'none',
            borderRadius: '8px',
            background: '#1677ff',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          + 新增证据
        </button>
      </div>

      <div style={sectionStyle}>
        <h2>第 5 步：文书确认</h2>
        <div style={grid2}>
          <div>
            <label style={labelStyle}>受诉法院</label>
            <input
              style={inputStyle}
              value={formData.document_options.court_name}
              onChange={(e) =>
                handleNestedChange(
                  'document_options',
                  'court_name',
                  e.target.value
                )
              }
            />
          </div>
          <div>
            <label style={labelStyle}>案由</label>
            <input
              style={inputStyle}
              value={formData.document_options.case_cause}
              onChange={(e) =>
                handleNestedChange(
                  'document_options',
                  'case_cause',
                  e.target.value
                )
              }
            />
          </div>
        </div>

        <div style={{ ...grid2, marginTop: '16px' }}>
          <label style={{ ...labelStyle, display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={formData.document_options.apply_support_prosecution}
              onChange={(e) =>
                handleNestedChange(
                  'document_options',
                  'apply_support_prosecution',
                  e.target.checked
                )
              }
            />
            是否申请支持起诉
          </label>

          <label style={{ ...labelStyle, display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={formData.document_options.claim_litigation_cost}
              onChange={(e) =>
                handleNestedChange(
                  'document_options',
                  'claim_litigation_cost',
                  e.target.checked
                )
              }
            />
            是否主张诉讼费用
          </label>
        </div>

        <div style={{ marginTop: '16px' }}>
          <label style={labelStyle}>生成哪类文书</label>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input
                type="checkbox"
                checked={formData.document_options.document_types.includes('complaint')}
                onChange={(e) =>
                  handleDocumentTypeChange('complaint', e.target.checked)
                }
              />
              民事起诉状
            </label>

            <label style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input
                type="checkbox"
                checked={formData.document_options.document_types.includes(
                  'support_prosecution'
                )}
                onChange={(e) =>
                  handleDocumentTypeChange(
                    'support_prosecution',
                    e.target.checked
                  )
                }
              />
              支持起诉书
            </label>
          </div>
        </div>
      </div>

      <div style={sectionStyle}>
        <h2>信息预览</h2>
        <pre
          style={{
            background: '#f5f5f5',
            padding: '16px',
            borderRadius: '8px',
            whiteSpace: 'pre-wrap',
            overflowX: 'auto',
          }}
        >
          {JSON.stringify(buildPayload(), null, 2)}
        </pre>
      </div>

      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <button
          onClick={handleSubmit}
          disabled={submitting}
          style={{
            padding: '14px 28px',
            fontSize: '16px',
            border: 'none',
            borderRadius: '10px',
            background: submitting ? '#999' : '#1677ff',
            color: '#fff',
            cursor: submitting ? 'not-allowed' : 'pointer',
          }}
        >
          {submitting ? '提交中...' : '提交案件'}
        </button>
      </div>

      <div style={sectionStyle}>
        <h2>后端返回结果</h2>
        <pre
          style={{
            background: '#f5f5f5',
            padding: '16px',
            borderRadius: '8px',
            whiteSpace: 'pre-wrap',
            overflowX: 'auto',
          }}
        >
          {result}
        </pre>
      </div>
    </div>
  )
}

export default App
