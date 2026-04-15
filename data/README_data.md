# 数据文件说明

更新时间：2026-04-15

## 已产出数据

### 1) `data/processed/occupation_exposure.csv`

- 含义：职业层面的 AI/任务暴露表
- 核心字段：
  - `occupation_code`
  - `routine_task_score`
  - `cognitive_task_score`
  - `social_task_score`
  - `ai_exposure_score`
  - `llm_exposure_score`
  - `source`
- 生成脚本：`src/build_occupation_exposure.py`
- 上游原始文件：
  - `job_exposure.csv`
  - `onet_task_statements.csv`

### 2) `data/processed/occupation_code_mapping.csv`

- 含义：SOC 基础职业码映射表（预留 ISCO/国标/CFPS 补齐字段）
- 核心字段：
  - `soc_code`
  - `soc_title`
  - `isco08_code`
  - `gbt_occ_code`
  - `cfps_occ_code`
  - `mapping_method`
  - `confidence`
- 生成脚本：`src/build_occupation_code_mapping.py`
- 上游原始文件：
  - `SOC_Structure.csv`

### 3) `data/raw/jobs/jobs_micro_raw.csv`

- 含义：招聘岗位原始快照（最近一年窗口）
- 主要来源：
  - The Muse API
  - RemoteOK API
- 关键字段：
  - `job_id`
  - `platform`
  - `crawl_date`
  - `city`
  - `industry`
  - `company_name`
  - `job_title`
  - `salary_min`
  - `salary_max`
  - `salary_unit`
  - `job_description_raw`
  - `job_url`
  - `post_date`
- 生成脚本：`src/fetch_jobs_micro_raw.py`

## 仍待获取数据

- **CFPS（消息中也写作 CPFS）个体面板数据**：仍在申请流程中，当前仓库未包含该数据文件。
