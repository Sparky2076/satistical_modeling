# runs/ 目录说明

本目录存放每次 API 跑批的**原始 JSON 响应**，供人工标注时查阅模型回答内容。

## 目录结构

```
runs/
├── <run_id>/                        # 每次跑批一个文件夹
│   ├── <task_id>__<policy_id>.json  # 每条"任务×策略"一个文件
│   ├── ...
```

当前已有的 run_id：

| run_id | 说明 | 文件数 |
|--------|------|--------|
| smoke_test | 初始烟测 | 2 |
| batch_20260503 | 早期小批量（仅 DeepSeek，10 任务） | 40 |
| test_each | 逐厂商烟测（DeepSeek / GLM / Spark） | 4 |
| ds_batch | DeepSeek 正式跑批（50 任务 × 2 策略） | 600 |

## JSON 文件格式

每个文件包含一次 API 调用的完整记录：

```json
{
  "task_id": "ps-001",
  "policy_id": "pl_deepseek_pro",
  "run_id": "ds_batch",
  "provider": "DeepSeek",
  "model_id": "deepseek-v4-pro",
  "latency_sec": 49.64,
  "usage": {
    "input_tokens": 99,
    "output_tokens": 1803,
    "cache_tokens": 0
  },
  "error": null,
  "response_text": "模型的中文回答内容..."
}
```

| 字段 | 说明 |
|------|------|
| `task_id` | 任务编号，对应 `task_bank.csv` |
| `policy_id` | 策略编号，对应 `policies.csv` |
| `run_id` | 批次编号，对应 `observations.csv` 中的 `run_id` |
| `provider` | 厂商（DeepSeek / GLM / Spark 等） |
| `model_id` | 具体模型名 |
| `latency_sec` | 响应耗时（秒） |
| `usage` | token 用量 |
| `error` | 失败时为错误信息，成功时为 `null` |
| `response_text` | **模型的完整回答** — 标注时重点看这个字段 |

## 与主表的关系

`task_policy_observations.csv` 中的 `response_path` 列指向对应的 JSON 文件路径，例如：

```
response_path = data/tessa_psa/runs/ds_batch/ps-001__pl_deepseek_pro.json
```

**observations CSV 里不含回答文本**，回答只存在 JSON 文件中。

## 人工标注流程

1. 从 `task_policy_observations.csv` 或 `task_policy_observations_enriched.csv` 中选取待标注行
2. 根据 `response_path` 找到对应 JSON，阅读 `response_text`
3. 按 `appendix/annotation_rubric.md` 的标准打分
4. 将分数填入 `human_labels.csv`，用 `task_id` + `policy_id` + `run_id` 关联

### 标注字段速查

| 字段 | 范围 | 说明 |
|------|------|------|
| `quality_score` | 0-10 | 回答总体质量 |
| `correctness_score` | 0-10 | 与权威事实的一致性 |
| `completeness_score` | 0-10 | 要点覆盖程度 |
| `risk_score` | 0-10 | 错误答案可能造成的损害严重程度 |
| `hallucination_flag` | 0/1 | 是否存在可证伪的事实性错误 |
| `human_time_base_min` | 分钟 | 无 AI 辅助完成该任务的预估时间 |
| `human_time_ai_min` | 分钟 | 在 AI 输出基础上复核至可交付的时间 |
| `review_effort_min` | 分钟 | 阅读与检索核对的总投入时间 |

## 注意事项

- `output_tokens` 达到 `max_output_tokens` 上限（如 2048）的 JSON，回答可能被截断，标注时需留意
- `error` 非 `null` 的 JSON 表示调用失败，不存在有效回答，无需标注
- 同一任务可能被多个 `run_id` 重复调用（不同批次），标注时注意区分
