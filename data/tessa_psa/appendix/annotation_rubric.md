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

---

## 与主表对齐（合并键）

填写 [`human_labels.csv`](../human_labels.csv) 时，**必须**与 [`task_policy_observations.csv`](../task_policy_observations.csv)（或 enriched 版）中同一行完全一致：

- `task_id`、`policy_id`、`run_id`（建议复制粘贴，避免空格或大小写误差）。
- 同一任务若存在多个 `run_id`（如烟测、正式批），**勿混用**：每条标注只对应唯一一次 API 调用。

合并到分析表：仓库根目录执行 `python src/tepsa_merge_labels.py`（左连接，见根目录 `README.md` 或 `README_run_batch.md`）。

---

## 试标与一致性（建议流程）

1. **先固定一个 `run_id`**（例如 `ds_batch`），避免跨批次口径漂移。  
2. **每位标注员先试标 20–30 条**，用同一批 JSON（`response_path` 指向 `data/tessa_psa/runs/<run_id>/…json`）阅读模型全文再打分。  
3. **一致性**：可在 R 或独立 Python notebook 中计算 ICC / Fleiss’ Kappa / 加权 Kappa；本仓库不捆绑统计包。  
4. **定稿 rubric** 后再扩面；扩面时仍保留 `annotator_id` 便于审计。

## 标注材料从哪来

- 主表列 **`response_path`**：打开对应 JSON，字段 `response_text`（或脚本约定字段）即为模型回答。  
- 目录说明见 [`../runs/README_runs.md`](../runs/README_runs.md)。
