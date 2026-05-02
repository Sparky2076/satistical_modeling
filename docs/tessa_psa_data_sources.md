# TESSA-PSA v2：数据源速查（配合 proposal + data todo list）

本文档根据你们微信目录下的 **proposal.pdf** 与 **data todo list.md** 整理：**文件对齐分析、执行建议、可直接打开的数据链接**。不替代论文中的正式引用格式。

---

## 1. 两份材料如何对齐

| Todo 模块 | Proposal 中对应 | 一句话 |
|-----------|-----------------|--------|
| A 主表 `task_policy_observations.csv` | §3.1、附录 Table 3 | 一行 = 任务 × 策略的一次 API 调用 + 标注 |
| B API 价格 | §2.1 `Ci(a)`、Table 1 | 用公开价目表算 `cost_usd` |
| C 模型基准 | §6 baselines、gap | 能力/速度/单价用于 baseline 排序 |
| D 中文任务库 | §3.2 task bank | 政务 FAQ + 基准题 + 政策文本片段 |
| E 人工标注 | §2.2 `Vi(a)` | 无标注则论文退化为「发票会计」 |
| F 宏观校准 | §4.3 entropy balancing | 年鉴工资/就业做权重，不写全国卫星账 |
| G 算力楔（可选） | 扩展讨论 | `compute_service_wedge_optional.csv` 见 §3.6 |

**核心一致点**：先 MVP（任务库 + 价目 + 多策略跑批 + 标注），**不要做**第一版全国 token 卫星账（todo F 已写清）。

---

## 2. 建议（风险与答辩）

1. **随机化**：proposal 强调困难任务易与贵模型策略混淆；任务到策略的分配应 **随机** 或事后 **DR/IPW**，并在文中写清 overlap 与缺失机制。  
2. **高风险任务**：税务/医保/法律等 **不要** 为追求对比把弱模型随机到「可致损答案」；可 `risk_class=high` 只做强模型 + 人工审核路径，或从任务库剔除敏感子集。  
3. **价目快照**：`api_price_schedule.csv` 必须带 **抓取日期**；API 常调价，附录保留 PDF/HTML 存档或 Wayback 链接。  
4. **标注协议**：todo 写的 rubric 在 **第 1 天定稿** 小样本试标后再扩面；报告 **ICC 或一致性** 增强可信度。  
5. **与统计建模大赛主题**：引言用国发〔2025〕11 号扣「人工智能+」与公共服务；**实证主体**仍是可复现的表格 + 估计量 + 图（与 proposal 的 C 节 deliverables 一致）。

---

## 3. 按模块：去哪里找数据

### 3.1 国家战略背景（todo §B.1 → `policy_background_notes.md`）

- **国务院公报（推荐引用）**：[国务院关于深入实施「人工智能+」行动的意见（国发〔2025〕11号）](https://www.gov.cn/gongbao/2025/issue_12266/202509/content_7039598.html)  
- 可摘录维度：科技、产业、消费、民生、治理、全球合作（与 proposal §1.1 一致）。

### 3.2 API 价目表（todo §B.2 → `api_price_schedule.csv`）

从各厂商 **官方定价页** 手抄或截图存档（字段见 todo）。常用入口（若 404 请从各站「Pricing」导航进入）：

- OpenAI：`https://openai.com/api/pricing/`  
- DeepSeek：`https://api-docs.deepseek.com/zh-cn/quick_start/pricing`（以文档站当前路径为准）  
- 阿里云百炼 / 通义：`https://help.aliyun.com/` 内搜索「模型调用计费」  
- 百度千帆：`https://cloud.baidu.com/doc/WENXINWORKSHOP/s/` 定价相关文档  
- 智谱：`https://open.bigmodel.cn/dev/pricing`  
- Google AI / Gemini：Developers 站点 **Gemini API pricing**  
- Anthropic Claude：`https://www.anthropic.com/pricing`（API 分项以控制台文档为准）

**建议模型组合（与 todo 一致）**：低价国产 1、中端 1、前沿 1、推理型 1，共 4～6 个即可开题。

### 3.3 能力与速度基准（todo §B.3 → `model_benchmark_table.csv`）

- **Artificial Analysis**（聚合延迟、价格、上下文等）：`https://artificialanalysis.ai/`  
- **C-Eval**（论文与数据，proposal 参考文献）：站点 `https://cevalbenchmark.com/`；数据 [Hugging Face `ceval/ceval-exam`](https://huggingface.co/datasets/ceval/ceval-exam)；官方仓库指引见 [hkust-nlp/ceval](https://github.com/hkust-nlp/ceval)（含 `wget` zip 说明）。  
- **CMMLU**：[GitHub haonan-li/CMMLU](https://github.com/haonan-li/CMMLU)；[Hugging Face `haonan-li/cmmlu`](https://huggingface.co/datasets/haonan-li/cmmlu) 按 subject 加载。

### 3.4 中文任务库（todo §B.4 → `task_bank.csv`）

- **跑批与校验**：先 `python src/tepsa_validate_inputs.py`，再按 [`data/tessa_psa/README_run_batch.md`](../data/tessa_psa/README_run_batch.md) 设置环境变量并调用 `src/tepsa_api_batch.py`；成本与 `value_score` 回填见同文件中的 `tepsa_main.py` 说明。  
- **政府 FAQ / 办事指南**：用 todo 中的检索式，例如  
  `site:gov.cn 社保 医保 报销 问答`  
  `site:gov.cn 政务服务 常见问题 办理 流程`  
  每条记录：**原文问题 + 来源 URL + sector + 风险分级**；优先复制「问答对」页面，避免整站爬取。  
- **基准锚点**：从 C-Eval / CMMLU 抽取子集作 **easy/medium/hard** 锚点（注意许可证与引用要求）。  
- **上市公司年报**：上交所/深交所信息披露 `cninfo.com.cn` 下载 **MD&A 段落**作「摘要类」任务源（遵守网站使用条款，控制频率）。

### 3.5 宏观校准（todo §B.6 → `macro_calibration_totals.csv`）

- **城镇单位分行业年平均工资等**：[国家统计局 — 2024年城镇单位就业人员年平均工资情况](https://www.stats.gov.cn/sj/zxfb/202505/t20250516_1959826.html)  
- 更长面板：购买或图书馆 **《中国统计年鉴》** 电子版，或 EPS / Wind 导出「按行业门类」工资与就业表。

### 3.6 可选：算力楔（todo §B.7 → `compute_service_wedge_optional.csv`）

- **产出与方法论**：[../data/tessa_psa/compute_service_wedge_optional.csv](../data/tessa_psa/compute_service_wedge_optional.csv)；指数定义与引用见 [../data/tessa_psa/appendix/B7_compute_wedge_methodology.md](../data/tessa_psa/appendix/B7_compute_wedge_methodology.md)。  
- **下游 API 锚（GPT-4o 输出 $/1M）**：[OpenAI Platform — Pricing](https://platform.openai.com/docs/pricing)；[API Changelog](https://developers.openai.com/api/docs/changelog)；[Hello GPT-4o（2024-05-13）](https://openai.com/index/hello-gpt-4o/)。  
- **上游 GPU 清单价代理（p4d.24xlarge / us-east-1）**：[AWS What’s New — EC2 NVIDIA GPU pricing（2025-06）](https://aws.amazon.com/about-aws/whats-new/2025/06/pricing-usage-model-ec2-instances-nvidia-gpus/)；[AWS News Blog — GPU instance price reduction](https://aws.amazon.com/blogs/aws/announcing-up-to-45-price-reduction-for-amazon-ec2-nvidia-gpu-accelerated-instances/)；现价便查 [instances.vantage.sh — p4d.24xlarge](https://instances.vantage.sh/aws/ec2/p4d.24xlarge?region=us-east-1)（非 AWS 官方，仅二次核对）。  
- **历史价目存档**：若需逐日核对，建议对 `platform.openai.com/docs/pricing` 与 AWS EC2 On-Demand 价目页使用 [Internet Archive](https://web.archive.org/) 做 Wayback 快照（本仓库首版未逐条爬档）。  
- 云 GPU 小时价、数据中心投资等仍为 **加分讨论**，**勿阻塞主线**。

---

## 4. 与 `task_policy_observations.csv` 的字段映射提醒

跑 API 时向日志写入：`input_tokens`、`output_tokens`、`cache_tokens`（若支持）、`latency_sec`、`model`、`policy_id`；与 `human_labels.csv` 用 **`task_id` + `policy_id` + run_id** 合并，避免一行多义。

---

## 5. 执行顺序（与 todo 7 日计划一致，再压缩版）

| 顺序 | 产出 |
|------|------|
| 1 | `api_price_schedule.csv` + `model_benchmark_table.csv` |
| 2 | `task_bank.csv`（先 200～300 条高质量） |
| 3 | 固定 4～8 个 `policy_id`，跑全库存原始 JSON |
| 4 | `human_labels.csv`（冻结 rubric） |
| 5 | 合并主表 → MTP → 图与分配前沿 |

本仓库路径：`D:\GitHub_Code\satistical_modeling\docs\tessa_psa_data_sources.md`。
