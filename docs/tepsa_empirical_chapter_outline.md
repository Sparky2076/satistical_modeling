# TESSA-PSA 实证章节提纲（与仓库脚本、数据对齐）

> 用途：把「论文章节—表号—图号—变量—命令」对齐到本仓库，便于粘贴进 Word；**不替代**导师对统稿结构的修改。

---

## 1. 数据与可复现窗口


| 用途               | 文件                                                        | 生成命令                                     |
| ---------------- | --------------------------------------------------------- | ---------------------------------------- |
| 任务 × 策略观测 + 价目   | `data/tessa_psa/task_policy_observations_enriched.csv`    | `python src/tepsa_main.py`               |
| 左连标注列            | `data/tessa_psa/task_policy_observations_with_labels.csv` | `python src/tepsa_merge_labels.py`       |
| 宏观五扇区 join（分析主表） | `data/tessa_psa/obs_macro_preview.csv`                    | `python src/tepsa_macro_join_preview.py` |


- `**run_id`**：正文应写清所用子样本（如仅 `ds_batch` 做多厂商可比，或全样本描述统计）。见 `[data/tessa_psa/appendix/reproducibility_baseline.md](../data/tessa_psa/appendix/reproducibility_baseline.md)`。
- **Git 快照**：投稿前在仓库根目录执行 `git rev-parse HEAD` 写入附录。

---

## 2. 变量与数据字典映射


| 论文叙述       | CSV 列名                           | 备注                                                                                             |
| ---------- | -------------------------------- | ---------------------------------------------------------------------------------------------- |
| 单次调用美元成本   | `cost_usd`                       | 由价目与 token 计算，见 `[appendix/data_dictionary.md](../data/tessa_psa/appendix/data_dictionary.md)` |
| 总 token    | `input_tokens` + `output_tokens` | 回归脚本内构造 `log_tokens = log(·+1)`                                                                |
| 策略 / 厂商档位  | `policy_id`，`provider`           | FE 常用 `C(policy_id)`                                                                           |
| 任务扇区（宏观对齐） | `tepsa_sector`                   | FE 可用 `C(tepsa_sector)`                                                                        |
| 质量 proxy   | `quality_score`                  | 含自动评测等，方法段需声明，见 `[docs/tessa_psa_data_sources.md](tessa_psa_data_sources.md)` §2               |
| 综合价值 proxy | `value_score`（CSV 常空）            | 回归脚本用 `tepsa_main.compute_value_score_row` 对齐默认参数重算后回归，列名为 `value_score_reg`                   |
| 宏观工资锚等     | `macro_avg_annual_wage_cny` 等    | 前缀 `macro_`，与扇区 join                                                                           |


---

## 3. 图表与正文交叉引用（建议）


| 类型       | 仓库产物                                                                                                                                         | 论文章节建议            |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| 概念图      | `output/figures/fig01_*.png`、`fig03_*.png`                                                                                                   | 引言 / 方法：框架与数据流    |
| 描述统计     | `fig_run_id_counts_`*、`fig_cost_by_policy_`*、`fig_tokens_hist_*`、`fig_cost_vs_tokens_*`、`fig_latency_by_provider_*`、`fig_sector_structure_*` | 数据节：样本结构、成本与延迟    |
| Token—质量 | `fig02_token_quality_scatter_*.png`                                                                                                          | 结果：质量与规模（注意自动分口径） |
| 风险—成本—质量 | `fig04_risk_welfare_scatter_*.png`                                                                                                           | 结果或稳健性讨论          |


出图命令：`pip install -r requirements-viz.txt` → `python scripts/tepsa_figures.py`（可加 `--run-id`）。

---

## 4. 基线回归（主结果 / 技术基线）


| 表号（自拟）    | 规格                                                    | 脚本                                        | 输出                                            |
| --------- | ----------------------------------------------------- | ----------------------------------------- | --------------------------------------------- |
| 表 A（技术基线） | `log(cost) ~ log(tokens) + C(policy_id)`，HC1          | `python src/tepsa_regression_baseline.py` | `output/regression/tepsa_baseline_summary.md` |
| 表 B       | `quality_score ~ log(tokens) + C(tepsa_sector)`（有分样本） | 同上                                        | 系数表见同目录 `tepsa_baseline_coefficients.csv`     |
| 表 C       | `value_score_reg ~ log(tokens) + C(policy_id)`        | 同上                                        | 同上                                            |


依赖：`pip install -r requirements-regression.txt`。

**写作提示**：表 A 的 R² 常接近 1 反映**价目线性计费**与策略截距，适合作为「发票会计」技术基线，不宜单独包装为因果识别主结论。

---

## 5. 局限与答辩（与数据源文档一致）

1. **自动评测 vs 真人**：`annotator_id` 含 `claude_auto_evaluation` 等，ICC 与「人类金标准」需分写。
2. **跨 `run_id` 混用**：可比性、费用与任务分配策略需在方法段说明。
3. **高风险任务**：见 `[docs/tessa_psa_data_sources.md](tessa_psa_data_sources.md)` §2 随机化与 overlap。
4. **正式加权回归**：年鉴权重、熵平衡等可在 Stata/R 中扩展；本仓库 Python 线为 **MVP 基线**。

---

## 6. 可选：微观 Bartik 线（与 TESSA 独立）

若另有 CFPS 与 Bartik 输入：`[src/micro_impact_pipeline.py](../src/micro_impact_pipeline.py)`，见脚本头注释与 `[README.md](../README.md)` 中 `micro_impact_pipeline` 一行。

---

*与 `TODO_list.md` P3「跑通回归并链到论文附录」一并维护。*