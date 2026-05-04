# 后续待办清单（TESSA-PSA + 仓库维护）

> 说明：下列条目按依赖顺序排列，**写明后面要做的事**。完成一项勾一项（`[ ]` → `[x]`）；需要分工时可在条目前自行标注负责人。

---

## P0 — 跑通真实数据（阻塞后续实证）

> **同步更新**：仓库已含队友提交的 `task_policy_observations.csv`（约 **1268** 行）与 `runs/` 下多批次 JSON（含 `spark_batch`、`glm_batch`、`ds_batch` 等）；下列「主表非空 / 路径 / enriched」可视为已达成。**若你本机还要跑新批次**，仍须完成密钥与环境变量（第 1～2 项）。

- 在 Anthropic / OpenAI / DeepSeek 等**官方或团队认可渠道**申请 API Key；勿将密钥写入仓库或聊天。（**仅续跑新批次时需要**）
- 在本机 PowerShell 设置环境变量：`OPENAI_API_KEY`、`DEEPSEEK_API_KEY`、`ANTHROPIC_API_KEY` 等。（**仅续跑新批次时需要**）
- 主表 `task_policy_observations.csv` 已出现多行成功观测（`input_tokens` / `output_tokens` / `latency_sec` 非空）；含 `ds_batch`、`spark_batch`、`glm_batch`、`batch_20260503`、`test_each`、`smoke_test` 等 `run_id`。
- `runs/<run_id>/` 下 JSON 与 CSV 中 `response_path` 已抽样核对（前 50 条路径均存在）。
- 已执行 `python src/tepsa_main.py`，`task_policy_observations_enriched.csv` 与观测行数一致并含 `cost_usd`、价目相关列。

## P1 — 小批量与全量跑批策略

- 与导师确认：是否对 `risk_class=high` 全程使用 `--skip-high-risk` 或仅分配强模型 policy。
- 固定 `run_id`（如 `batch_YYYYMMDD`），用 `--max-tasks 10~20` 做费用可控小批量；确认无误后再扩大或全库（300×策略数，费用显著）。
- 需要断点续跑时：同一 `--run-id` + `--resume`，避免重复扣费。

## P2 — 标注与主表合并

- 定稿 `[data/tessa_psa/appendix/annotation_rubric.md](data/tessa_psa/appendix/annotation_rubric.md)`（已补合并键、试标/ICC、`runs` 材料；若导师另有口径可再修订）。
- 评测导出：`human_label _res/` 下 `ds_results_final.csv`、`glm_results_final.csv`、`spark_results_final.csv` → 运行 `python src/tepsa_build_human_labels.py` 写入 `human_labels.csv`。真人 ICC 与 `claude_auto_evaluation` 等自动分在论文中分开表述。
- 将标注左连接到 enriched 主表：运行 `python src/tepsa_merge_labels.py`（默认将 GLM 导出中的 `glm_batch_v3`/`v4`/`final` 对齐为 `glm_batch`），产出 `[task_policy_observations_with_labels.csv](data/tessa_psa/task_policy_observations_with_labels.csv)`；可选 `--export-queue --filter-run-id <run_id>` 导出待补队列。

## P3 — 论文与可复现性

- 附录/脚注素材：已新增 `[appendix/reproducibility_baseline.md](data/tessa_psa/appendix/reproducibility_baseline.md)`（`run_id`、价目日、主表选用；Git HEAD 按文内说明用 `git rev-parse` 填入）。  
- 宏观 join 预览：运行 `python src/tepsa_macro_join_preview.py` 生成 `[obs_macro_preview.csv](data/tessa_psa/obs_macro_preview.csv)`（`tepsa_sector` 对齐 `macro_calibration_totals` `year=2024` 五扇区）；正式回归可在 Stata/R 中再写权重与稳健性。  
- **Python 基线回归**：`pip install -r requirements-regression.txt` → `python src/tepsa_regression_baseline.py`（可选 `--run-id ds_batch`），将 `output/regression/tepsa_baseline_summary.md` 链入论文附录或转录为表；章节约稿见 `[docs/tepsa_empirical_chapter_outline.md](docs/tepsa_empirical_chapter_outline.md)`。  
- 外链巡检：按需打开定价页；已在本仓库 `[appendix/B2_official_pricing_urls.md](data/tessa_psa/appendix/B2_official_pricing_urls.md)` 与 `[docs/tessa_psa_data_sources.md](docs/tessa_psa_data_sources.md)` §6 留「末次核对」占位，复查后改日期。

## P4 — 仓库与协作（可选）

- `git add` / `commit` / `push` 前确认未包含 `.env`、任何密钥文件。（`runs/` 大 JSON 已由队友纳入版本库时，以团队约定为准。）
- 在 GitHub 上开 **Issues** 将 P0–P2 拆给不同成员，与本 `TODO_list.md` 同步。

---

## 非阻塞 / 历史课题

- 若继续做 `micro_impact_pipeline.py`：按脚本注释准备 `data/raw/cfps_micro.csv` 等输入。
- 若需重建任务库：联网运行 `python src/tepsa_task_bank_build.py`（会覆盖/重写 `task_bank.csv`，先备份）。

---

**最后更新**：与根目录 `[README.md](README.md)` 中「当前进度」表一并维护。