# 评委追问与答辩要点（TESSA-PSA）

> 与 [`docs/tepsa_empirical_chapter_outline.md`](tepsa_empirical_chapter_outline.md)、[`docs/competition_readiness.md`](competition_readiness.md) 一致；**短答可背**，细节以论文与附录为准。

---

## 1. 「回归 R² 接近 1，是不是过拟合 / 造假？」

- **答**：主结果里的 **M1**（`log_cost ~ log_tokens + C(policy_id)`）是 **价目与调用日志的记账核对**，因变量由公开单价 × token **机械决定**，高 R² **符合数据生成过程**，不是「解释社会现象」的模型。
- **证据**：报告 **`output/regression/tepsa_m1_accounting_metrics.csv`**：log 残差 RMSE/MAE 与 **美元相对误差中位数**（约 1%～2% 量级，以你本机最新跑表为准），说明拟合误差在**数值噪声**范围，而非虚构拟合。

---

## 2. 「你们有没有因果识别？凭什么说政策好？」

- **答**：全文**不**把 OLS 系数当作**已识别因果**。识别强度分层表述：  
  - **M1**：非因果，仅核对成本核算。  
  - **M2/M3（混合截面 + 扇区/策略 FE）**：**关联与异质性**，控制部分混淆，仍有内生性。  
  - **Within-task**（`tepsa_regression_within_task.py`）：同一 `task_id` 多 `policy_id`，加 **任务固定效应**，比较「同一题换策略」——**强于**纯混合截面，但**仍非随机实验**（路由、费用约束等仍可混淆）。  
  - **IPW**（`tepsa_regression_ipw.py`）：在 **可交换性、无未测混杂、倾向模型正确** 等假设下的**加权对照**；若 Z 对处理几乎无预测力，应诚实写「**调整空间有限，仅作敏感性**」，避免夸大。
- **答**：与 [`docs/tessa_psa_data_sources.md`](tessa_psa_data_sources.md) 一致——理想情况是**随机分配任务到策略**或 **双重稳健/熵平衡**；当前仓库为 **MVP + 可答辩扩展**，更强识别可作为**未来工作**或 Stata/R 附录。

---

## 3. 「质量分是自动评测，能代表真实质量吗？」

- **答**：自动分（如 `claude_auto_evaluation`）与**真人**在数据字典与正文**分开披露**；自动分用于**可比、可复现**的 MVP，**不替代**高风险场景的人类金标准。
- **建议**：引用 [`data/tessa_psa/appendix/annotation_rubric.md`](../data/tessa_psa/appendix/annotation_rubric.md) 与 [`human_label _res/glm_scores/evaluation_report.md`](../human_label%20_res/glm_scores/evaluation_report.md)；若已有真人双评，报告 **ICC**；当前主表无双评重复键时，见 `python src/tepsa_annotation_icc.py` 生成的说明。

---

## 4. 「跨 run_id 混用，结论还成立吗？」

- **答**：正文**写清**主分析所用的 `run_id` 子样本（如全样本 vs `ds_batch`），并说明不同批次在**费用、任务集、厂商组合**上的差异；稳健性可在**单一 run_id** 上复现回归/图（脚本均支持 `--run-id`）。

---

## 5. 「创新点到底是什么？」

- **答**：不在「又训了一个模型」，而在 **把国家战略叙事压成可估计、可复现、可审计的任务级指标与流程**（测度—核对—within 比较—敏感性），并**诚实写局限**。可对照 [`docs/competition_readiness.md`](competition_readiness.md) §4。

---

## 6. 为何正文不写 IV / 全量 DML？

- 与 [`docs/tepsa_empirical_chapter_outline.md`](tepsa_empirical_chapter_outline.md) **§6** 一致：缺**外生且可辩护**的工具时不上 IV；DML 可作为**文献与附录扩展**（可选依赖见 [`requirements-annotation.txt`](../requirements-annotation.txt) 注释），不阻塞主线。
