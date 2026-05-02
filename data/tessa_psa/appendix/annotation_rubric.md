# 人工标注量表（附录草案）

与 `human_labels.csv` 配套。正式研究前应用小样本试标并报告一致性（如 ICC）。

## 分数（0–10）

| 字段 | 定义锚点 |
|------|----------|
| correctness_score | 与可核查事实/权威条文的一致性；不确定处是否明确声明限制。 |
| completeness_score | 是否覆盖问题要点；是否给出可执行步骤或清单。 |
| quality_score | 总评：可取 correctness 与 completeness 的加权或独立 holistic。 |
| risk_score | 错误答案可能造成的经济/合规/健康安全损害严重程度（非模型“自信度”）。 |

## 二值与努力

| 字段 | 规则 |
|------|------|
| hallucination_flag | 1 = 存在可证伪的事实性错误；0 = 未发现或未核查。 |
| human_time_base_min | 无模型辅助下，合格完成该任务预估分钟数。 |
| human_time_ai_min | 在模型输出基础上复核/修订至可交付的分钟数。 |
| review_effort_min | 阅读提示、检索核对、多轮追问等总投入。 |

## 高风险任务

税务、医保、法律、特种设备等领域：**禁止**为对比随意分配弱策略到可致损场景；见 `proposal.pdf` 伦理说明。
