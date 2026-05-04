# 统计建模大赛：仓库内「参赛就绪」清单

> **不能替代**赛方当年正式通知与导师审阅；用于交稿前自检与队友分工。  
> **无法靠仓库保证获奖**：赛题契合、评审尺度、答辩现场等仍取决于赛会与队伍表现。

---

## 1. 格式与匿名

- 以 Word 母版为准时，对照抽取的格式要点：[`docs/paper/_source/format_outline.md`](paper/_source/format_outline.md)（封面字段、边距、章节要素等）。
- **匿名规则**（与格式说明一致）：除**封面页**、**致谢**外，正文等处**不得**出现学校、队号、指导教师等可识别信息；LaTeX 预览见 [`docs/paper/README_overleaf.md`](paper/README_overleaf.md)，终稿在 Word 中再核对一遍。
- PDF 预览：[`docs/paper/main.tex`](paper/main.tex)；终稿转 Word 见 [`docs/paper/README_overleaf.md`](paper/README_overleaf.md) 末节（Pandoc / 手工对齐）。

---

## 2. 可复现命令链（建议固定写入论文附录）

在仓库根目录、已配置好 API 密钥（仅续跑时需要）与 Python 依赖的前提下，**分析向**推荐顺序：

1. `python src/tepsa_main.py` — 生成/更新 `task_policy_observations_enriched.csv`（价目与 `cost_usd`）。
2. （若用标注）按 [`TODO_list.md`](../TODO_list.md) P2：`python src/tepsa_build_human_labels.py` → `python src/tepsa_merge_labels.py`。
3. `python src/tepsa_macro_join_preview.py` — `obs_macro_preview.csv`。
4. 回归（建议用本机实际有 `numpy`/`statsmodels` 的解释器，Windows 上常为 **`py -3`** 而非首位的 `python`）：  
   - `py -3 src/tepsa_regression_baseline.py`  
   - `py -3 src/tepsa_regression_within_task.py`（可选 `--run-id ds_batch`）  
   - `py -3 src/tepsa_regression_ipw.py`（可选）
5. 出图：`pip install -r requirements-viz.txt` → `python scripts/tepsa_figures.py`。

详细变量与表号映射：[`docs/tepsa_empirical_chapter_outline.md`](tepsa_empirical_chapter_outline.md)。  
Git、`run_id`、主表版本：[`data/tessa_psa/appendix/reproducibility_baseline.md`](../data/tessa_psa/appendix/reproducibility_baseline.md)。

---

## 3. 数据、伦理与标注口径

- **高风险任务**：[`docs/tessa_psa_data_sources.md`](tessa_psa_data_sources.md) §2；跑批策略与 [`TODO_list.md`](../TODO_list.md) P1（`risk_class`、`--skip-high-risk` 等）。
- **自动评测 vs 真人**：主表/标注中 `annotator_id` 含 `claude_auto_evaluation` 等与真人 ID 混用时，正文与附录须**分开表述**；自动评测汇总示例：[`human_label _res/glm_scores/evaluation_report.md`](../human_label%20_res/glm_scores/evaluation_report.md)。评分细则：[`data/tessa_psa/appendix/annotation_rubric.md`](../data/tessa_psa/appendix/annotation_rubric.md)。
- **双评与 ICC**：当前 `human_labels.csv` 在 `(task_id, policy_id, run_id)` 上**无双行双评分人**（见 `python src/tepsa_annotation_icc.py` 报告）。若赛方或导师要求信度，建议**小样本双评**后再跑该脚本或手工计算 ICC。

---

## 4. 创新点：建议「可主张 / 勿夸大」

**可主张（与仓库实现一致）**

- TESSA-PSA：**任务级** Token 观测 + 价目 + 质量/价值 proxy 的**可复现**分析协议（非全国卫星账）。
- **价目—日志核对**（M1 + `output/regression/tepsa_m1_accounting_metrics.csv`）：记账一致性指标，回应高 R²。
- **同一任务多策略 + 任务固定效应**（`tepsa_regression_within_task.py`）：控制题目载体后的 within 关联，**非 RCT**。
- **IPW 敏感性**（`tepsa_regression_ipw.py`）：在显式假设下对照，**不作唯一主因果结论**。
- 图表与宏观扇区 join、附录数据字典与可复现说明。

**勿夸大**

- 勿将 M1 或 OLS/IPW **单独包装**为「已识别因果效应」或「政策净效应」。
- 勿声称已完成**全国代表性**智能服务账户或**强外生** IV/DML（除非另做附录并满足假设）；见 [`docs/tepsa_empirical_chapter_outline.md`](tepsa_empirical_chapter_outline.md) §6。

---

## 5. 图表、回归与 Git

- **建议纳入版本库、便于队友拉取**：`output/figures/`、`output/regression/`、`output/regression_within_task/`、`output/regression_ipw/`（交稿前执行脚本后 `git add` / `commit` / `push` 由队里约定）。
- **勿提交**：`.env`、任何 API 密钥、本机绝对路径私货；大体积 `runs/` 是否跟踪以团队约定为准（见根目录 [`.gitignore`](../.gitignore)）。
- 交稿前在本机执行 `git status`，确认无意外敏感文件。

---

## 6. 外链与价目快照

- 定价页可能变更：在 [`data/tessa_psa/appendix/B2_official_pricing_urls.md`](../data/tessa_psa/appendix/B2_official_pricing_urls.md) 更新**末次核对日期**；论文中写清 `price_collected_date` 与附录引用。

---

## 7. 答辩话术速查

见 [`docs/competition_QA_defense.md`](competition_QA_defense.md)。
