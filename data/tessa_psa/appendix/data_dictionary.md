# 数据字典（最小版）

路径根目录：`data/tessa_psa/`。

| 文件 | 一行含义 | 主键 / 合并键 |
|------|----------|----------------|
| task_policy_observations.csv | 任务 × token 策略的一次 API 调用与（后续）标注 | 建议 `task_id` + `policy_id` + `run_id` |
| task_bank.csv | 任务库母本 | `task_id` |
| api_price_schedule.csv | 厂商公开价目快照 | `provider` + `model_id` + `pricing_tier` |
| model_benchmark_table.csv | 能力与价格辅助表 | `model_id` |
| human_labels.csv | 人工对某次响应的评分 | `task_id` + `policy_id` + `run_id` |
| macro_calibration_totals.csv | 宏观工资锚（与部门映射） | `tepsa_sector` + `year` |
| compute_service_wedge_optional.csv | 可选算力楔：下游 API 与上游云 GPU 价格指数（季度） | `date` + `provider` |

**Sector 口径**：`task_bank.sector` 使用空格风格（如 `public service`），与 `macro_calibration_totals.csv` 的 `tepsa_sector`（下划线，如 `public_service`）不同。跑批写入 `task_policy_observations.csv` 时增加列 `tepsa_sector`，由 `src/tepsa_validate_inputs.py` 与 `src/tepsa_api_batch.py` 中的同一映射表从 `sector` 派生，便于与宏观表 join。

**task_source**：政务/网页类任务应为 `http` 或 `https` URL；`task_id` 以 `ceval-` / `cmmlu-` 开头的基准锚点允许非 URL 的数据集出处字符串（校验脚本 `tepsa_validate_inputs.py` 与之一致）。

**b4_benchmark_snapshot.json**：附录中 C-Eval/CMMLU 子集的 JSON 快照（90 条），字段与 `task_bank.csv` 同源；以 **CSV 母本为准** 时，快照用于可复现与论文附录引用；已核对与 `task_bank` 中对应 `task_id` 的 `task_text`、`expected_answer_hint` 一致。

`cost_usd` 推荐由程序按价目表计算：`input/1e6 * pin + output/1e6 * pout + cache/1e6 * pcache`。

`value_score` 见 `data todo list.md` §C 与 `proposal.pdf` 式 (1)，默认系数在 `src/tepsa_main.py` 中可配置。
