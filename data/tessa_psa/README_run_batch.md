# 多厂商 API 跑批（`tepsa_api_batch.py`）

从仓库根目录运行。脚本只读环境变量中的密钥，**不要**把密钥写进命令行或提交到 git；日志中只打印 `task_id` / `policy_id` / token 计数与错误摘要，不打印完整 API 响应正文。

## 环境变量


| 厂商            | 变量                                  | 说明                                                        |
| ------------- | ----------------------------------- | --------------------------------------------------------- |
| OpenAI        | `OPENAI_API_KEY`                    | [Platform API keys](https://platform.openai.com/api-keys) |
| DeepSeek      | `DEEPSEEK_API_KEY`                  | 官方控制台密钥                                                   |
| DeepSeek（可选）  | `DEEPSEEK_BASE_URL`                 | 默认 `https://api.deepseek.com`（OpenAI 兼容路径）                |
| Anthropic     | `ANTHROPIC_API_KEY`                 | Messages API                                              |
| Google Gemini | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` | Generative Language API                                   |


未设置对应密钥时，该厂商的调用会失败；可用 `--providers` 只跑已配置密钥的厂商。

## 输入与输出

- **任务库**：默认 `data/tessa_psa/task_bank.csv`（`--task-bank` 可改）。
- **策略表**：默认 `data/tessa_psa/policies.csv`（`--policies`）；`provider` / `model_id` 需与 `api_price_schedule.csv` 一致。
- **主表输出**：默认追加/重写 `data/tessa_psa/task_policy_observations.csv`（`--out`）。每行含 `tepsa_sector`（与宏观表 `tepsa_sector` 对齐）、`run_id`、`response_path`。**仅当 API 返回无 `error` 时写入主表行**（缺密钥、HTTP 错误等会跳过主表行）；每次调用仍会在 `runs/<run_id>/` 下写入 JSON 便于排查。
- **原始响应**：每个 `(task_id, policy_id)` 一条 JSON：`data/tessa_psa/runs/<run_id>/<task_id>__<policy_id>.json`。该目录已在 `.gitignore` 中忽略，避免误提交大文件。

## 建议流程

1. **校验任务库**（应无致命错误、退出码 0）。`task_source` 一般为 `http(s)` URL；`ceval-` / `cmmlu-` 开头的锚点任务允许数据集出处字符串（见 `appendix/data_dictionary.md`）。
  ```text
   python src/tepsa_validate_inputs.py
  ```
2. **干跑**（不发起 HTTP，只统计将发起的调用数）：
  ```text
   python src/tepsa_api_batch.py --dry-run
  ```
3. **一键烟测（PowerShell）**：仓库根目录执行 `.\scripts\smoke_tepsa_batch.ps1` — 校验 + 干跑；若已设置 `OPENAI_API_KEY`、`DEEPSEEK_API_KEY`、`ANTHROPIC_API_KEY`，则按 `run_id=smoke20260201` 各跑 1 任务 × 1 策略；缺密钥时只提示待执行命令。
4. **烟测**（默认最多 20 条任务 × 全部策略；可先缩小策略或任务数）：
  ```text
   python src/tepsa_api_batch.py --max-tasks 3 --policy-ids pl_openai_mini_std --providers OpenAI
   python src/tepsa_api_batch.py --max-tasks 1 --policy-ids pl_deepseek_flash --providers DeepSeek
   python src/tepsa_api_batch.py --max-tasks 1 --policy-ids pl_claude_haiku --providers Anthropic
   python src/tepsa_api_batch.py --max-tasks 1 --policy-ids pl_gemini_flash_lite --providers Google
  ```
5. **高风险任务**：可加 `--skip-high-risk`，使 `risk_class=high` 的任务不参与跑批。
6. **断点续跑**：固定同一 `--run-id`，再加 `--resume`，已写入 `--out` 的 `(task_id, policy_id)` 会跳过。

## 与 `tepsa_main.py` 的衔接

跑批脚本已按价目写入 `cost_usd`；若需把价目表字段合并进观测表并统一回填 `value_score`（在有人工质量分等字段时才有意义），可执行（**观测表仅表头时也会写出带价目列的空 enriched 表头**，便于后续追加行后再跑）：

```text
python src/tepsa_main.py --obs data/tessa_psa/task_policy_observations.csv --out data/tessa_psa/task_policy_observations_enriched.csv
```

默认 `--obs` 即为上述路径；输出默认 `task_policy_observations_enriched.csv`。

## P2：人工标注与主表合并

1. 量表与试标流程：[`appendix/annotation_rubric.md`](appendix/annotation_rubric.md)。  
2. 填写 `human_labels.csv` 后，在仓库根目录执行：

```text
python src/tepsa_merge_labels.py
```

默认读取 `task_policy_observations_enriched.csv` 与 `human_labels.csv`，写出 `task_policy_observations_with_labels.csv`（左连接，无标注行标签列为空）。  
3. 导出待标队列（去重后的 `task_id,policy_id,run_id,response_path`），便于 Excel 分配：

```text
python src/tepsa_merge_labels.py --export-queue data/tessa_psa/label_queue.csv --filter-run-id ds_batch
```

## 相关文档

- 数据源与字段提醒：`docs/tessa_psa_data_sources.md`
- 字段与 `tepsa_sector` 口径：`appendix/data_dictionary.md`

