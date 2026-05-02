# TESSA-PSA v2 Data Search TODO List

Purpose: build an easy-to-collect dataset for the statistical modeling paper **From Token Consumption to Public Intelligent-Service Allocation**. The minimum viable empirical target is **MTP estimation and token-budget allocation for Chinese public-service / enterprise-support tasks**. Do not try to build a full national token satellite account in the first version.

---

## A. Minimum viable data table structure

Create one master table named `task_policy_observations.csv`. Each row should be one task-policy evaluation.


| Field                 | Meaning                                                                | How to collect                                 |
| --------------------- | ---------------------------------------------------------------------- | ---------------------------------------------- |
| `task_id`             | unique task ID                                                         | hash or manual ID                              |
| `sector`              | public service / enterprise support / manufacturing / education / code | manual classification                          |
| `task_source`         | URL or document source                                                 | save source URL                                |
| `task_text`           | question or instruction                                                | copied from FAQ, policy document, or benchmark |
| `risk_class`          | low / medium / high                                                    | manual rubric                                  |
| `difficulty_label`    | easy / medium / hard                                                   | human label or benchmark difficulty            |
| `model`               | model/API endpoint                                                     | provider docs or API call                      |
| `policy_id`           | model + prompt + context + output cap                                  | manually coded                                 |
| `prompt_type`         | weak / standard / expert                                               | experiment design                              |
| `context_type`        | short / long / retrieval                                               | experiment design                              |
| `input_tokens`        | input token count                                                      | provider tokenizer/API log                     |
| `output_tokens`       | output token count                                                     | provider tokenizer/API log                     |
| `cache_tokens`        | cached tokens if any                                                   | provider API log if supported                  |
| `cost_usd`            | monetary API cost                                                      | token count × current price                    |
| `latency_sec`         | response time                                                          | API timing                                     |
| `quality_score`       | correctness/completeness score, 0-10                                   | student/expert annotation                      |
| `hallucination_flag`  | 0/1 factual error                                                      | manual check                                   |
| `risk_score`          | 0-10 risk severity                                                     | manual rubric                                  |
| `human_time_base_min` | human-only baseline time                                               | small annotation experiment                    |
| `human_time_ai_min`   | AI-assisted time                                                       | small annotation experiment                    |
| `value_score`         | computed value using paper formula                                     | formula field                                  |


---

## B. Data modules and source priorities

### 1. National strategy and policy background

**Goal:** support the introduction, not the main model.

**Primary source:**

- State Council / China government pages for the 2025 AI+ policy guideline.
- Search query: `国务院 深入实施 人工智能+ 行动 意见 国发 2025 11号`

**Variables to extract:** policy fields emphasized by AI+ strategy: science and technology, industry, consumption, people's livelihood, governance, and global cooperation.

**Output table:** `policy_background_notes.md`.

**Priority:** Medium. Use this for narrative only.

---

### 2. API price schedule

**Goal:** construct `cost_usd` and compare token policies.

**Primary sources:**

- OpenAI API pricing page.
- DeepSeek API pricing documentation.
- Alibaba Cloud Model Studio / Qwen pricing.
- Baidu Qianfan pricing.
- Zhipu AI pricing.
- Google Gemini API pricing.
- Anthropic Claude API pricing.

**Variables to extract:**

- model name
- input price per 1M tokens
- output price per 1M tokens
- cached input price per 1M tokens
- batch discount if available
- context window
- date of price collection

**Output table:** `api_price_schedule.csv`.

**Priority:** Very high. This is the easiest and most important dataset.

**Recommended first action:** collect 6-10 representative models: cheap Chinese model, medium model, frontier model, and one reasoning model.

---

### 3. Model capability and speed benchmark

**Goal:** build baseline policies such as benchmark ranking and quality-per-dollar ranking.

**Primary sources:**

- Artificial Analysis model/provider pages and free API if available.
- C-Eval leaderboard or benchmark data.
- CMMLU benchmark data.
- Optional: HELM or other public leaderboards.

**Variables to extract:**

- model name
- benchmark score
- Chinese benchmark score if available
- output speed
- latency / TTFT if available
- price per 1M tokens
- context window

**Output table:** `model_benchmark_table.csv`.

**Priority:** High. Needed for baseline comparison.

---

### 4. Chinese task bank

**Goal:** create 300-800 tasks for the pilot; 1,000+ tasks for a stronger final version.

**Easy task sources:**

1. Government-service FAQ pages: tax, social insurance, medical reimbursement, business registration, household registration, public procedures.
2. Policy interpretation documents: enterprise subsidy policies, tax deduction rules, social-security contribution rules.
3. Listed-company annual reports: annual-report summarization tasks.
4. Public manufacturing manuals: troubleshooting and safety operation tasks.
5. C-Eval / CMMLU questions: benchmark-style task difficulty anchors.

**Search queries:**

- `site:gov.cn 税务 问答 企业 补贴 政策 解读`
- `site:gov.cn 社保 医保 报销 问答`
- `site:gov.cn 政务服务 常见问题 办理 流程`
- `上市公司 年报 PDF 管理层讨论 分析`
- `制造业 设备 操作 手册 PDF 故障 排查`

**Variables to extract:**

- task text
- source URL
- sector
- expected answer or reference document
- risk class
- difficulty label

**Output table:** `task_bank.csv`.

**Priority:** Very high. This is the core empirical dataset.

**Practical rule:** start with 50 tasks per sector across 5 sectors. Do not over-expand before the labeling rubric is stable.

---

### 5. Human label and value data

**Goal:** define the welfare value `V_i(a)`.

**Low-cost annotation plan:**

- 2-3 annotators per task-policy response.
- Use a 0-10 rubric for correctness, completeness, usefulness, risk, and hallucination severity.
- Record baseline human time and AI-assisted verification time on a small subset.
- Use sector wage data to convert time saving into value.

**Variables to collect:**

- `quality_score`
- `correctness_score`
- `completeness_score`
- `risk_score`
- `hallucination_flag`
- `human_time_base_min`
- `human_time_ai_min`
- `review_effort_min`

**Output table:** `human_labels.csv`.

**Priority:** Very high. Without this, the paper degenerates into benchmark accounting.

---

### 6. Macro calibration data

**Goal:** keep the national-strategy flavor without requiring a full national survey.

**Primary sources:**

- National Bureau of Statistics of China: average wages by sector and employment-related data.
- China Statistical Yearbook.
- Local statistical yearbooks if regional calibration is needed.

**Variables to extract:**

- average annual wage by sector
- employment by sector
- number of enterprises by sector
- public-service volume if available
- regional population or employment weights

**Output table:** `macro_calibration_totals.csv`.

**Priority:** High. Use only simple calibration variables at first: sector and wage group.

---

### 7. Optional compute-service wedge data

**Goal:** support discussion/extension, not the main model.

**Sources:**

- API price pages over time, using archived pages if possible.
- Cloud GPU rental prices.
- data-center investment statistics.
- electricity price and energy-use reports.
- industry reports on chips and compute scarcity.

**Variables:**

- downstream API service price index
- upstream GPU/cloud-compute price proxy
- date
- provider

**Output table:** `compute_service_wedge_optional.csv`.

**Priority:** Medium-low. Do not let this delay the main paper.

---

## C. Modeling tasks after data collection

1. Build `api_price_schedule.csv` and compute API cost per observation.
2. Build `task_bank.csv` and assign sector, difficulty, and risk labels.
3. Run 4-8 token policies per task.
4. Label response quality, risk, and human time saving.
5. Estimate the value score:
  `value_score = wage_value * time_saved + gamma * quality_gain - lambda * risk_score - kappa * review_effort`
6. Fit difficulty-calibrated production model.
7. Estimate MTP by sector and policy.
8. Solve budget allocation.
9. Compare against baselines:
  - invoice minimization
  - cheapest model
  - strongest model
  - benchmark ranking
  - naive logged outcome
  - IPW/DR if logs are non-random
10. Generate final figures:
  - token cost vs. value scatter
    - token-response curves
    - MTP boxplot by sector
    - value decomposition bars
    - allocation frontier
    - robustness heatmap

---

## D. Suggested 7-day execution plan

### Day 1

Collect API prices and model benchmark data. Build `api_price_schedule.csv` and `model_benchmark_table.csv`.

### Day 2

Collect 300-500 tasks from government FAQ/policy pages and benchmark datasets. Build `task_bank.csv`.

### Day 3

Run selected models/policies on the task bank. Record token counts, cost, response, and latency.

### Day 4

Annotate quality, hallucination, risk, and time saving. Build `human_labels.csv`.

### Day 5

Fit value model and difficulty-calibrated token production curves. Produce first figures.

### Day 6

Run allocation optimization and baseline comparison. Produce allocation frontier and MTP plots.

### Day 7

Write empirical results, limitations, and policy implications. Finalize figures and appendices.

---

## E. Minimum deliverables for the competition paper

1. `api_price_schedule.csv`
2. `model_benchmark_table.csv`
3. `task_bank.csv`
4. `human_labels.csv`
5. `macro_calibration_totals.csv`
6. `analysis_code.ipynb` or `main.py`
7. final paper PDF
8. appendix with data dictionary and annotation rubric

---

## F. Keep / drop rule

Keep:

- MTP estimation
- public-service token budget allocation
- difficulty calibration
- risk-aware allocation
- simple macro calibration

Drop or move to appendix:

- full national token satellite account
- full compute-service wedge decomposition
- dynamic equilibrium macro model
- complicated causal theory beyond what the data can support

