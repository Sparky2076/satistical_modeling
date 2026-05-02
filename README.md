# satistical_modeling（统计建模 / TESSA-PSA 与相关数据）

本仓库包含两条可区分的主线：**（A）TESSA-PSA v2** — 中文公共服务相关任务库、多厂商 API 跑批、价目与观测表；**（B）历史/并行课题** — 部分省级 processed 数据与微观影响流水线脚本（输入数据需自备）。当前文档与开发重心在 **（A）**。

---

## 当前进度（截至 README 更新）

| 模块 | 状态 | 说明 |
|------|------|------|
| 任务库 `task_bank.csv` | **已完成** | 约 300 条；含政务门户类 + C-Eval / CMMLU 锚点；`task_source` 校验规则见数据字典。 |
| 价目与基准表 | **已完成** | `api_price_schedule.csv`、`model_benchmark_table.csv` 等与 proposal 对齐。 |
| 策略表 `policies.csv` | **已完成** | 8 条 policy（OpenAI / DeepSeek / Anthropic / Google），`model_id` 与价目表一致。 |
| 输入校验 `tepsa_validate_inputs.py` | **已完成** | 对 `task_bank.csv` 做枚举与唯一性等校验；`sector` → `tepsa_sector` 映射与宏观表对齐。 |
| 批量 API `tepsa_api_batch.py` | **已完成** | 分厂商 stdlib HTTP 调用；CLI 含 `--dry-run`、`--max-tasks`、`--resume`、`--skip-high-risk` 等；**仅成功响应写入主表**。 |
| 成本/价值回填 `tepsa_main.py` | **已完成** | 合并价目、计算 `cost_usd`；观测表仅表头时仍写出 **带扩展列的 enriched 表头**。 |
| 烟测脚本 `scripts/smoke_tepsa_batch.ps1` | **已完成** | 校验 + 干跑；三把密钥齐全则跑 OpenAI + DeepSeek + Anthropic 各 1 次。 |
| **真实 API 跑批数据行** | **待你本机完成** | 需在环境变量中配置各厂商 **API Key** 后执行跑批；详见 [`data/tessa_psa/README_run_batch.md`](data/tessa_psa/README_run_batch.md)。当前 `task_policy_observations.csv` 可为 **仅表头**（无密钥时不会产生成功观测行）。 |
| 人工标注 `human_labels.csv` | **未开始** | 仅表头；定稿 rubric 后填写。 |
| GitHub 同步 | **以你本地 `git push` 为准** | 本 README 与 `TODO_list.md` 用于说明进度与后续分工。 |

---

## 仓库结构与各文件功能

### 根目录

| 路径 | 功能 |
|------|------|
| [`README.md`](README.md) | 本文件：项目说明、进度、结构索引。 |
| [`TODO_list.md`](TODO_list.md) | **后续待办清单**（含配置密钥、跑批、标注、论文步骤）；便于分工（如指定负责人跟进）。 |
| [`.gitignore`](.gitignore) | 忽略 `__pycache__`、虚拟环境、`.env`、`data/tessa_psa/runs/`（大批量 JSON 跑批产物）等。 |

### `src/` Python 脚本

| 路径 | 功能 |
|------|------|
| [`src/tepsa_validate_inputs.py`](src/tepsa_validate_inputs.py) | 校验 `data/tessa_psa/task_bank.csv`；致命错误时非零退出。 |
| [`src/tepsa_api_batch.py`](src/tepsa_api_batch.py) | `task_bank` × `policies` 多厂商批量调用；写 `task_policy_observations.csv` 与 `data/tessa_psa/runs/<run_id>/*.json`。 |
| [`src/tepsa_main.py`](src/tepsa_main.py) | 读取观测表，合并 `api_price_schedule` 字段，计算 `cost_usd` / `value_score`（后者依赖质量分等）；输出 `task_policy_observations_enriched.csv`。 |
| [`src/tepsa_task_bank_build.py`](src/tepsa_task_bank_build.py) | **重建**任务库：门户数据 + C-Eval + CMMLU（需网络）；一般维护直接编辑 CSV 即可，不必每次全量重跑。 |
| [`src/tepsa_task_bank_portal_data.py`](src/tepsa_task_bank_portal_data.py) | 门户类任务 curated 数据，供 `tepsa_task_bank_build.py` 引用。 |
| [`src/tepsa_task_bank_benchmark_gen.py`](src/tepsa_task_bank_benchmark_gen.py) | 基准题生成相关辅助逻辑（与任务库构建配合）。 |
| [`src/micro_impact_pipeline.py`](src/micro_impact_pipeline.py) | 微观 AI 影响合并与基线回归（**需自备** `data/raw/` 下 CFPS、Bartik、暴露度等 CSV）；与 TESSA 跑批独立。 |
| [`src/nbs_download_checklist.py`](src/nbs_download_checklist.py) | 统计局/NBS 类下载核对清单辅助脚本。 |

### `scripts/`

| 路径 | 功能 |
|------|------|
| [`scripts/smoke_tepsa_batch.ps1`](scripts/smoke_tepsa_batch.ps1) | Windows PowerShell：校验 → 干跑 →（若已设三密钥）固定 `run_id` 三厂商烟测。 |

### `data/tessa_psa/`（TESSA-PSA 主数据）

| 路径 | 功能 |
|------|------|
| [`task_bank.csv`](data/tessa_psa/task_bank.csv) | 任务母本：`task_id`、`task_text`、`sector`、`risk_class`、`difficulty_label`、`task_source` 等。 |
| [`policies.csv`](data/tessa_psa/policies.csv) | 跑批策略：`policy_id`、`provider`、`model_id`、`temperature`、`max_output_tokens` 等。 |
| [`api_price_schedule.csv`](data/tessa_psa/api_price_schedule.csv) | 各模型公开价目快照，供 `cost_usd` 计算。 |
| [`model_benchmark_table.csv`](data/tessa_psa/model_benchmark_table.csv) | 模型能力/延迟等辅助表。 |
| [`task_policy_observations.csv`](data/tessa_psa/task_policy_observations.csv) | **主表**：每次「任务 × 策略」API 调用一行（成功写入）；列含 `tepsa_sector`、`run_id`、`response_path`。 |
| [`task_policy_observations_enriched.csv`](data/tessa_psa/task_policy_observations_enriched.csv) | `tepsa_main.py` 输出：在原观测上附加价目列与回填后的 `cost_usd` 等（可无数据行，仅表头）。 |
| [`human_labels.csv`](data/tessa_psa/human_labels.csv) | 人工标注（与主表按 `task_id`+`policy_id`+`run_id` 合并）。 |
| [`macro_calibration_totals.csv`](data/tessa_psa/macro_calibration_totals.csv) | 宏观校准：`tepsa_sector`（下划线）与工资等。 |
| [`compute_service_wedge_optional.csv`](data/tessa_psa/compute_service_wedge_optional.csv) | 可选算力楔指数。 |
| [`policy_background_notes.md`](data/tessa_psa/policy_background_notes.md) | 政策背景摘录笔记。 |
| [`README_run_batch.md`](data/tessa_psa/README_run_batch.md) | **跑批必读**：环境变量、命令示例、与 `tepsa_main.py` 衔接。 |
| [`appendix/`](data/tessa_psa/appendix/) | 数据字典、定价 URL 索引、标注 rubric、B6/B7 方法论等 Markdown。 |

### `data/` 其他

| 路径 | 功能 |
|------|------|
| [`data/README_data.md`](data/README_data.md) | 数据目录总览；说明课题重心已切至 TESSA-PSA。 |
| [`data/README_nbs_download_checklist.md`](data/README_nbs_download_checklist.md) | NBS 下载核对说明。 |
| [`data todo list.md`](data%20todo%20list.md) | 课题级数据待办（与 proposal 对齐的长清单）。 |
| [`data/raw/`](data/raw/) / [`data/processed/`](data/processed/) | 原始与加工表（含历史课题占位文件）；**微观流水线**依赖的 raw 文件需自行放入。 |

### `docs/`

| 路径 | 功能 |
|------|------|
| [`docs/tessa_psa_data_sources.md`](docs/tessa_psa_data_sources.md) | 数据源速查、风险建议、与 `README_run_batch` 的交叉引用。 |

---

## 快速开始（TESSA 跑批）

```powershell
cd D:\GitHub_Code\satistical_modeling   # 改为你的克隆路径
python src/tepsa_validate_inputs.py
python src/tepsa_api_batch.py --dry-run
# 配置 OPENAI_API_KEY 等后：
.\scripts\smoke_tepsa_batch.ps1
python src/tepsa_main.py
```

详细参数与多厂商说明：[`data/tessa_psa/README_run_batch.md`](data/tessa_psa/README_run_batch.md)。

---

## 后续分工

执行层待办见 **[`TODO_list.md`](TODO_list.md)**（**后面要做的事项**清单）；需要分工时在清单里标注负责人或拆 GitHub Issue 跟踪即可。
