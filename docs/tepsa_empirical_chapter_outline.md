# TESSA-PSA 实证章节提纲（与仓库脚本、数据对齐）

> 用途：把「论文章节—表号—图号—变量—命令」对齐到本仓库，便于粘贴进 Word；**不替代**导师对统稿结构的修改。

---

## 1. 数据与可复现窗口


| 用途               | 文件                                                        | 生成命令                                     |
| ---------------- | --------------------------------------------------------- | ---------------------------------------- |
| 任务 × 策略观测 + 价目   | `data/tessa_psa/task_policy_observations_enriched.csv`    | `python src/tepsa_main.py`               |
| 左连标注列            | `data/tessa_psa/task_policy_observations_with_labels.csv` | `python src/tepsa_merge_labels.py`       |
| 宏观五扇区 join（分析主表） | `data/tessa_psa/obs_macro_preview.csv`                    | `python src/tepsa_macro_join_preview.py` |


- **`run_id`**：正文应写清所用子样本（如仅 `ds_batch` 做多厂商可比，或全样本描述统计）。见 [`data/tessa_psa/appendix/reproducibility_baseline.md`](../data/tessa_psa/appendix/reproducibility_baseline.md)。
- **Git 快照**：投稿前在仓库根目录执行 `git rev-parse HEAD` 写入附录。

---

## 2. 变量与数据字典映射


| 论文叙述           | CSV 列名                           | 备注                                                                                             |
| -------------- | -------------------------------- | ---------------------------------------------------------------------------------------------- |
| 单次调用美元成本       | `cost_usd`                       | 由价目与 token 计算，见 `[appendix/data_dictionary.md](../data/tessa_psa/appendix/data_dictionary.md)` |
| 总 token        | `input_tokens` + `output_tokens` | 回归脚本内构造 `log_tokens = log(·+1)`                                                                |
| 任务键            | `task_id`                        | **Within-task** 规格需同一 `task_id` 下多 `policy_id`                                                 |
| 策略 / 厂商档位      | `policy_id`，`provider`           | FE 常用 `C(policy_id)`                                                                           |
| 任务扇区（宏观对齐）     | `tepsa_sector`                   | FE 可用 `C(tepsa_sector)`                                                                        |
| 难度 / 风险（倾向得分用） | `difficulty_label`，`risk_class`  | 仅作前定协变量 Z，勿把结果变量喂进倾向模型                                                                         |
| 质量 proxy       | `quality_score`                  | 含自动评测等，方法段需声明，见 `[docs/tessa_psa_data_sources.md](tessa_psa_data_sources.md)` §2               |
| 综合价值 proxy     | `value_score`（CSV 常空）            | 回归脚本用 `tepsa_main.compute_value_score_row` 重算后列 `value_score_reg`                              |
| 宏观工资锚等         | `macro_avg_annual_wage_cny` 等    | 前缀 `macro_`，与扇区 join                                                                           |


---

## 3. 图表与正文交叉引用（建议）


| 类型            | 仓库产物                                                                                                                                                                                                                                                                                                                     | 论文章节建议                                            |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------- |
| 概念图           | `output/figures/fig01_*.png`、`fig03_*.png`                                                                                                                                                                                                                                                                               | 引言 / 方法：框架与数据流                                    |
| 描述统计          | `fig_run_id_counts_*`、`fig_cost_by_policy_*`、`fig_tokens_hist_*`、`fig_cost_vs_tokens_*`、`fig_latency_by_provider_*`、`fig_sector_structure_*`                                                                                                                                                                             | 数据节：样本结构、成本与延迟                                    |
| Token—质量      | `fig02_token_quality_scatter_*.png`                                                                                                                                                                                                                                                                                      | 结果：质量与规模（注意自动分口径）                                 |
| 风险—成本—质量      | `fig04_risk_welfare_scatter_*.png`                                                                                                                                                                                                                                                                                       | 结果或稳健性讨论                                          |
| 扩展（IPW/回归可视化） | `fig_propensity_overlap_*`、`fig_m1_logcost_fitted_vs_actual_*`、`fig_coef_log_tokens_forest_*`、`fig_policy_sector_quality_heatmap_*`、`fig_within_task_policy_count_hist_*`                                                                                                                                                | 识别敏感性、M1 价目核对、系数对照、异质性、within 样本构造                |
| 扩展诊断（附录/答辩备选） | `fig_m1_residual_diagnostics_*`、`fig_m1_cost_rel_error_hist_*`、`fig_cost_per_token_by_policy_*`、`fig_latency_cost_and_tokens_*`、`fig_quality_difficulty_risk_box_*`、`fig_value_score_policy_and_tokens_*`、`fig_within_retention_sector_share_*`、`fig_ipw_weight_distribution_*`、`fig_macro_wage_vs_sector_median_cost_*` | 残差与相对误差、单位成本、延迟、质量分层、价值 proxy、扇区保留、IPW 权重、宏观—成本描述 |


出图命令：`pip install -r requirements-viz.txt` → `python scripts/tepsa_figures.py`（可加 `--run-id`）；扩展图加 `--extended`（依赖 `statsmodels`，与 `tepsa_regression_ipw.build_ipw_frame` 共用 IPW 样本定义）。

---

## 4. 回归与识别叙事（答辩对齐）

### 4.1 表 A：价目—日志核对（非因果主结果）


| 表号（自拟） | 规格                                         | 脚本                                        | 输出                                            |
| ------ | ------------------------------------------ | ----------------------------------------- | --------------------------------------------- |
| 表 A    | `log_cost ~ log_tokens + C(policy_id)`，HC1 | `python src/tepsa_regression_baseline.py` | `output/regression/tepsa_baseline_summary.md` |


**写作**：表 A 为 **accounting check（价目与日志一致性）**；**禁止**写「政策因果解释力」。除 R² 外，报告 `**tepsa_m1_accounting_metrics.csv`** 中的 log 残差 RMSE/MAE 与美元 **相对误差中位数**，用于回应「R² 高是否过拟合」——结构上应接近恒等式，残差反映数值噪声与价目近似误差。

### 4.2 表 B / C：混合截面关联（扇区或策略 FE）


| 表号  | 规格                                             | 脚本          | 输出                                |
| --- | ---------------------------------------------- | ----------- | --------------------------------- |
| 表 B | `quality_score ~ log_tokens + C(tepsa_sector)` | 同上 baseline | `tepsa_baseline_coefficients.csv` |
| 表 C | `value_score_reg ~ log_tokens + C(policy_id)`  | 同上          | 同上                                |


**写作**：表述为 **条件相关 / 预测关系**；因果句仅在与 **within-task 或 IPW** 对照时使用。

### 4.3 表 D–F：Within-task（任务固定效应）


| 表号  | 规格                                                         | 脚本                                           | 输出                               |
| --- | ---------------------------------------------------------- | -------------------------------------------- | -------------------------------- |
| 表 D | `log_cost ~ log_tokens + C(task_id) + C(policy_id)`        | `python src/tepsa_regression_within_task.py` | `output/regression_within_task/` |
| 表 E | `quality_score ~ log_tokens + C(task_id)`                  | 同上                                           | 同上                               |
| 表 F | `value_score_reg ~ log_tokens + C(task_id) + C(policy_id)` | 同上                                           | 同上                               |


**样本**：同一 `run_id` 内，保留「**至少 2 个不同 `policy_id`**」的 `task_id`；表中报告 **保留率**（见 `tepsa_within_task_sample_meta.csv`）。

**写作**：控制任务文本载体后的 **within 关联**，**仍非 RCT**；若跑批非完全随机，需在局限段写清选择机制。

**命令示例**：`python src/tepsa_regression_within_task.py --run-id ds_batch`

### 4.4 表 G（可选）：二值策略 IPW + overlap


| 表号  | 内容                                                                       | 脚本                                   | 输出                                                               |
| --- | ------------------------------------------------------------------------ | ------------------------------------ | ---------------------------------------------------------------- |
| 表 G | 以 `policy_id == pl_deepseek_pro` 为 T=1；logit `T ~ Z`；Hajek ATE；p 的分位数与裁剪 | `python src/tepsa_regression_ipw.py` | `output/regression_ipw/tepsa_ipw_summary.md`、`tepsa_ipw_ate.csv` |


**Z**（前定）：`difficulty_label`、`risk_class`、`tepsa_sector`。可用 `--outcome quality|value`。

**写作**：**敏感性 / 对照估计**；依赖可交换性与无未测混杂等假设，**不作唯一主因果结论**。

### 4.5 表 H（可选）：识别安慰剂 / 置换检验


| 表号  | 内容                                                                                                                                                                                                               | 脚本                                                                                  | 输出                                                                                                                                                                   |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 表 H | **实验1**：within-task 组内打乱 `policy_id`（multiset 不变），零分布为行级「处理组与对照组 `quality_score` 样本均值之差」；**实验2**：在 `difficulty_label`×`risk_class`×`tepsa_sector` 层内置换 `T`，**固定** `pscore`、不重估 logit，零分布为 **Hajek ATE**；双侧 p 见摘要 | `python src/tepsa_identification_placebos.py`（可加 `--run-id`、`--n-reps`、`--out-dir`） | `output/identification_placebo/tepsa_placebo_summary.md`、`tepsa_placebo_null_task_perm.csv`、`tepsa_placebo_null_hajek_perm.csv`、`fig_placebo_null_distributions.png` |


**写作**：**随机化推断式参照**，用于「若处理与结果（近似）独立」时的对照；**不**替代 RCT。若与 `ds_batch` 等不同子样本复跑，建议用 `--out-dir` 分目录保存，避免覆盖全样本结果。

**LaTeX（公式与表述边界）**：与上表同一套定义与符号见 [`docs/paper/sections/identification_placebo_writeup.tex`](../docs/paper/sections/identification_placebo_writeup.tex)（已 `\input` 进 `docs/paper/sections/body_backmatter.tex` 附录；亦可单独 `xelatex docs/paper/identification_placebo_standalone.tex`）。

---

依赖（MVP）：`pip install -r requirements-regression.txt`。

可选 **DML / econml**（未默认安装）：见 `[requirements-causal.txt](../requirements-causal.txt)` 注释。

---

## 5. 局限与答辩（与数据源文档一致）

1. **自动评测 vs 真人**：`annotator_id` 含 `claude_auto_evaluation` 等，ICC 与「人类金标准」需分写。
2. **跨 `run_id` 混用**：可比性、费用与任务分配策略需在方法段说明。
3. **高风险任务**：见 `[docs/tessa_psa_data_sources.md](tessa_psa_data_sources.md)` §2 随机化与 overlap。
4. **正式加权回归**：年鉴权重、熵平衡等可在 Stata/R 中扩展；本仓库 Python 线为 **MVP 基线 + within-task + 可选 IPW**。

---

## 6. 工具变量（IV）与 DML：如何在正文定位（回应评委）

**工具变量（IV）**  

- 本仓库 **未** 将 IV 作为主结果：公开 API **价目、token 与策略路由**通常与任务难度、质量需求**同时决定**，缺少外生且仅通过单一渠道影响结果的 instrument 时，IV **易偏、难辩护**。  
- 若未来有 **价目外生跳变窗口**（如官方调价日 + 事件研究）或可辩护的 **成本冲击**，可另做附录；否则建议在正文 **明确不写 IV 主规格**，避免伪工具。

**Double / debiased ML（DML）**  

- Chernozhukov 等提出的 DML 适合 **高维控制 + 部分线性** 的 nuisance 估计；实现需 **交叉拟合** 与较多样本，依赖如 `doubleml` / `econml`（见 `requirements-causal.txt`）。  
- **当前主线**：以 **OLS + task FE + IPW 对照** 为主，成本可控、可复现。DML 可作为 **加分附录** 或 **方法局限 + 文献引用**，不必阻塞交稿。

---

## 7. 可选：微观 Bartik 线（与 TESSA 独立）

若另有 CFPS 与 Bartik 输入：`[src/micro_impact_pipeline.py](../src/micro_impact_pipeline.py)`，见脚本头注释与 `[README.md](../README.md)` 中 `micro_impact_pipeline` 一行。

---

*与 `TODO_list.md` P3「跑通回归并链到论文附录」一并维护。*