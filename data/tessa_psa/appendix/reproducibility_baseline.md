# 可复现性基线（TESSA-PSA）

定稿实证或投稿前，将本节复制到论文附录或脚注，并更新 **Git commit** 与 **价目抓取日**。

## Git 快照

- 记录分析冻结时的仓库 HEAD：在仓库根目录执行 `git rev-parse HEAD`，将输出粘贴到本节（或论文脚注）。  
- 本附录检入时的示例提交仅用于占位；**每次**投稿/复现前更新一次。

## API 跑批 `run_id`

与 [`../runs/README_runs.md`](../runs/README_runs.md) 一致，当前仓库已纳入版本库的批次包括（示例）：

| run_id | 说明 |
|--------|------|
| smoke_test | 烟测 |
| batch_20260503 | 小批量（示例日期批次） |
| test_each | 逐厂商烟测 |
| ds_batch | DeepSeek 较大批量 |

分析时应用 **单一或明确列出的** `run_id` 子集，避免跨批次混用导致不可比。

## 价目表快照

- 数据文件：[`../api_price_schedule.csv`](../api_price_schedule.csv)。  
- 当前表内 `price_collected_date` 均为 **2026-05-02**（以各行 `source_url` 官方页为准；调价后须整表更新并改日期）。  
- 成本列 `cost_usd` 由 [`../../../src/tepsa_main.py`](../../../src/tepsa_main.py) 按该表计算。

## 主表与合并表选用

| 用途 | 文件 |
|------|------|
| 仅机器观测 + 价目 | [`../task_policy_observations_enriched.csv`](../task_policy_observations_enriched.csv) |
| 含人工（或占位）标注列 | [`../task_policy_observations_with_labels.csv`](../task_policy_observations_with_labels.csv)（[`../../../src/tepsa_merge_labels.py`](../../../src/tepsa_merge_labels.py) 产出） |
| 宏观 join 预览 | [`../obs_macro_preview.csv`](../obs_macro_preview.csv)（[`../../../src/tepsa_macro_join_preview.py`](../../../src/tepsa_macro_join_preview.py) 产出） |

**脚注**：`human_labels.csv` 中 `annotator_id=assistant_demo_v1` 为 **AI 占位**，正式结果表不得直接当作人类标注 ICC 依据；真人重标后更新本节说明。
