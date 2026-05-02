# 后续待办清单（TESSA-PSA + 仓库维护）

> 说明：下列条目按依赖顺序排列，**写明后面要做的事**。完成一项勾一项（`[ ]` → `[x]`）；需要分工时可在条目前自行标注负责人。

---

## P0 — 跑通真实数据（阻塞后续实证）

- [ ] 在 Anthropic / OpenAI / DeepSeek 等**官方或团队认可渠道**申请 API Key；勿将密钥写入仓库或聊天。
- [ ] 在本机 PowerShell 设置环境变量（至少完成计划中的三厂商之一即可先试）：`OPENAI_API_KEY`、`DEEPSEEK_API_KEY`、`ANTHROPIC_API_KEY`（可选 `GEMINI_API_KEY` / `GOOGLE_API_KEY`）。
- [ ] 仓库根目录执行 `.\scripts\smoke_tepsa_batch.ps1`，确认 `data/tessa_psa/task_policy_observations.csv` 出现 **≥1 行**成功观测，且 `input_tokens`、`output_tokens`、`latency_sec` 非空。
- [ ] 检查 `data/tessa_psa/runs/<run_id>/` 下 JSON 是否与 CSV 中 `response_path` 一致，抽查一条回答质量。
- [ ] 执行 `python src/tepsa_main.py`，确认 `task_policy_observations_enriched.csv` 中 `cost_usd`、价目相关列被正确填充。

## P1 — 小批量与全量跑批策略

- [ ] 与导师确认：是否对 `risk_class=high` 全程使用 `--skip-high-risk` 或仅分配强模型 policy。
- [ ] 固定 `run_id`（如 `batch_YYYYMMDD`），用 `--max-tasks 10~20` 做费用可控小批量；确认无误后再扩大或全库（300×策略数，费用显著）。
- [ ] 需要断点续跑时：同一 `--run-id` + `--resume`，避免重复扣费。

## P2 — 标注与主表合并

- [ ] 定稿 [`data/tessa_psa/appendix/annotation_rubric.md`](data/tessa_psa/appendix/annotation_rubric.md)（若需修订）。
- [ ] 小样本试标 → 计算一致性（ICC 等）→ 扩面填写 [`data/tessa_psa/human_labels.csv`](data/tessa_psa/human_labels.csv)。
- [ ] 用 `task_id` + `policy_id` + `run_id` 将标注与 `task_policy_observations.csv` 合并，用于论文表格与 MTP。

## P3 — 论文与可复现性

- [ ] 在附录或脚注中记录：`api_price_schedule.csv` 抓取日期、各 `run_id`、关键脚本版本（Git commit）。
- [ ] 宏观 join：使用观测表中的 `tepsa_sector` 与 [`macro_calibration_totals.csv`](data/tessa_psa/macro_calibration_totals.csv) 对齐（见 `appendix/data_dictionary.md`）。
- [ ] 更新 `docs/tessa_psa_data_sources.md` 中若有的失效链接（定价页常变）。

## P4 — 仓库与协作（可选）

- [ ] `git add` / `commit` / `push` 前确认未包含 `.env`、`runs/` 下大 JSON、任何密钥文件。
- [ ] 在 GitHub 上开 **Issues** 将 P0–P2 拆给不同成员，与本 `TODO_list.md` 同步。

---

## 非阻塞 / 历史课题

- [ ] 若继续做 `micro_impact_pipeline.py`：按脚本注释准备 `data/raw/cfps_micro.csv` 等输入。
- [ ] 若需重建任务库：联网运行 `python src/tepsa_task_bank_build.py`（会覆盖/重写 `task_bank.csv`，先备份）。

---

**最后更新**：与根目录 [`README.md`](README.md) 中「当前进度」表一并维护。
