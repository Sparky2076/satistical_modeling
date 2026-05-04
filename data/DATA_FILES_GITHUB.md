# GitHub 仓库内数据与派生产物索引

本文档描述**当前已纳入 Git 版本库**的数据相关路径：是什么、给谁用、与哪条流水线对齐。  
未跟踪的大文件（如本机 `.env`、部分队友本地的 `runs/` 新批次）不在此列；以你执行 `git ls-files` 为准。

更细的列级说明见 [`tessa_psa/appendix/data_dictionary.md`](tessa_psa/appendix/data_dictionary.md)；数据源与外链见 [`docs/tessa_psa_data_sources.md`](../docs/tessa_psa_data_sources.md)。

---

## 1. TESSA-PSA 核心表（`data/tessa_psa/*.csv`）

| 文件 | 一行代表什么 | 典型用途 |
|------|----------------|----------|
| [`task_bank.csv`](tessa_psa/task_bank.csv) | 一条评测/办事类**任务**（题干、出处、扇区、难度等） | 跑批输入母本；主键 `task_id` |
| [`policies.csv`](tessa_psa/policies.csv) | 一条可调用的 **Token 策略**（模型、提示、上下文档位等） | `tepsa_api_batch.py` 与 `policy_id` 对齐价目 |
| [`api_price_schedule.csv`](tessa_psa/api_price_schedule.csv) | 厂商公开 **价目快照**（$/1M tokens 等） | `tepsa_main.py` 算 `cost_usd`；论文需写 `price_collected_date` |
| [`model_benchmark_table.csv`](tessa_psa/model_benchmark_table.csv) | 模型 **能力/延迟** 等辅助指标 | 基线排序、附录表 |
| [`task_policy_observations.csv`](tessa_psa/task_policy_observations.csv) | **任务 × 策略 × run** 的一次成功 API 调用日志（token、延迟、`response_path` 等） | 跑批直接产出；分析前建议走 enriched |
| [`task_policy_observations_enriched.csv`](tessa_psa/task_policy_observations_enriched.csv) | 观测表 + 价目合并 + **`cost_usd`** 等 | **回归/作图主输入之一**（`tepsa_main.py`） |
| [`human_labels.csv`](tessa_psa/human_labels.csv) | 对某次 `(task_id, policy_id, run_id)` 的 **评分/工时** 等 | `tepsa_build_human_labels.py` 合并导出；论文区分真人 vs 自动评测 |
| [`task_policy_observations_with_labels.csv`](tessa_psa/task_policy_observations_with_labels.csv) | enriched **左连** `human_labels` | 需要 `quality_score` 等列时的宽表（`tepsa_merge_labels.py`） |
| [`obs_macro_preview.csv`](tessa_psa/obs_macro_preview.csv) | with_labels（或 enriched）**左连宏观五扇区**（`macro_*`，`year=2024`） | **Python 回归默认读入表**（`tepsa_macro_join_preview.py`） |
| [`macro_calibration_totals.csv`](tessa_psa/macro_calibration_totals.csv) | 分扇区 **工资/就业** 等宏观锚 | 与 `tepsa_sector` join；年鉴来源见附录 |
| [`compute_service_wedge_optional.csv`](tessa_psa/compute_service_wedge_optional.csv) | **可选**算力楔（下游 API vs 上游 GPU 价格指数） | 扩展讨论，不阻塞主线 |

---

## 2. 说明性 Markdown（`data/tessa_psa/`）

| 文件 | 用途 |
|------|------|
| [`README_run_batch.md`](tessa_psa/README_run_batch.md) | 跑批环境变量、输入输出、`runs/` 目录约定 |
| [`policy_background_notes.md`](tessa_psa/policy_background_notes.md) | 政策背景笔记（与论文引言引用衔接） |

---

## 3. 附录与可复现（`data/tessa_psa/appendix/`）

| 文件 | 用途 |
|------|------|
| [`data_dictionary.md`](tessa_psa/appendix/data_dictionary.md) | 主表关系与主键（最小数据字典） |
| [`reproducibility_baseline.md`](tessa_psa/appendix/reproducibility_baseline.md) | Git、`run_id`、用哪张主表、价目日等 |
| [`annotation_rubric.md`](tessa_psa/appendix/annotation_rubric.md) | 标注量表与合并键 |
| [`B2_official_pricing_urls.md`](tessa_psa/appendix/B2_official_pricing_urls.md) | 官方定价页链接与核对占位 |
| [`B4_source_url_index.md`](tessa_psa/appendix/B4_source_url_index.md) | 来源 URL 索引 |
| [`B6_nbs_table_citations.md`](tessa_psa/appendix/B6_nbs_table_citations.md) | 统计局表引用 |
| [`B7_compute_wedge_methodology.md`](tessa_psa/appendix/B7_compute_wedge_methodology.md) | 算力楔方法论 |
| [`b4_benchmark_snapshot.json`](tessa_psa/appendix/b4_benchmark_snapshot.json) | C-Eval/CMMLU 子集 JSON 快照（与 `task_bank` 对照） |

---

## 4. 原始 API 响应（`data/tessa_psa/runs/<run_id>/`）

每个 JSON 对应一次 **`{task_id}__{policy_id}.json`**，含模型原始返回与元数据，供审计与排错；**主表行**由跑批脚本从成功响应汇总写入 `task_policy_observations.csv`。

当前仓库 **已跟踪**的 `run_id` 目录包括（示例，便于论文写「批次」）：

| `run_id` | 说明（概要） |
|----------|----------------|
| `batch_20260503` | 较早一批多策略政务类跑批 |
| `ds_batch` | DeepSeek 等可比子样本（论文常作 `--run-id` 稳健性） |
| `glm_all` | 智谱相关批次导出对齐用 |
| `smoke_test` / `test_each` | 烟测、单测 |
| `spark_batch` | 讯飞 Spark 双模型策略等 |

> 注：部分文档曾写「`runs/` 默认 gitignore」；**本仓库已选择跟踪上述批次**。若本地新建大批 JSON，是否提交由队里约定。

---

## 5. 标注导出（`human_label _res/`）

| 文件 | 用途 |
|------|------|
| [`ds_results_final.csv`](../human_label%20_res/ds_results_final.csv) | DeepSeek 侧标注导出（合并进 `human_labels.csv` 的源之一） |
| [`glm_results_final.csv`](../human_label%20_res/glm_results_final.csv) | 智谱侧标注导出 |
| [`spark_results_final.csv`](../human_label%20_res/spark_results_final.csv) | 讯飞侧标注导出 |
| [`glm_scores/evaluation_report.md`](../human_label%20_res/glm_scores/evaluation_report.md) | 自动评测汇总（与真人分开展示） |
| [`annotate_json_files.py`](../human_label%20_res/annotate_json_files.py) | 辅助脚本（非数据表） |

生成合并表：`python src/tepsa_build_human_labels.py`。

---

## 6. 历史 / 并行课题（`data/processed/`, `data/raw/`）

| 文件 | 用途 |
|------|------|
| [`processed/bartik_prov_year.csv`](processed/bartik_prov_year.csv) | 旧 Bartik 相关省×年表（占位/历史） |
| [`processed/occupation_code_mapping.csv`](processed/occupation_code_mapping.csv) | 职业码映射 |
| [`processed/occupation_exposure.csv`](processed/occupation_exposure.csv) | 职业暴露度 |
| [`processed/province_controls.csv`](processed/province_controls.csv) | 省级控制变量 |
| [`raw/jobs/jobs_micro_raw.csv`](raw/jobs/jobs_micro_raw.csv) | 招聘微观原始样本（若继续 `micro_impact_pipeline`） |

新主线以 **`data/tessa_psa/`** 为准；见 [`README_data.md`](README_data.md)。

---

## 7. 仓库根目录其他数据说明

| 文件 | 用途 |
|------|------|
| [`README_nbs_download_checklist.md`](README_nbs_download_checklist.md) | 国统计局等下载核对清单 |

---

## 8. 派生产物（`output/`，若已跟踪）

由脚本再生，**论文插图与回归表**常引用此目录； teammate `git pull` 可直接用。

| 路径 | 用途 |
|------|------|
| [`output/figures/*.png`](../output/figures/) | `scripts/tepsa_figures.py` 出图 |
| [`output/regression/`](../output/regression/) | `tepsa_regression_baseline.py` 基线 + M1 核对指标 |
| [`output/regression_ds_batch/`](../output/regression_ds_batch/) | 同上，`--run-id ds_batch` |
| [`output/regression_within_task/`](../output/regression_within_task/) | `tepsa_regression_within_task.py` |
| [`output/regression_ipw/`](../output/regression_ipw/) | `tepsa_regression_ipw.py` |
| [`output/annotation/icc_report.md`](../output/annotation/icc_report.md) | `tepsa_annotation_icc.py` 双评可行性说明 |

---

## 9. 推荐阅读顺序（新人）

1. [`README_data.md`](README_data.md)（本目录总览）  
2. 本文 **`DATA_FILES_GITHUB.md`**（Git 上有什么）  
3. [`tessa_psa/appendix/data_dictionary.md`](tessa_psa/appendix/data_dictionary.md)（列与键）  
4. [`docs/tepsa_empirical_chapter_outline.md`](../docs/tepsa_empirical_chapter_outline.md)（论文—表—图—命令）  
5. [`docs/competition_readiness.md`](../docs/competition_readiness.md)（交稿前自检）
