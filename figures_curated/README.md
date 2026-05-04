# 精选实证图（约 10 张）

本目录为从 [`output/figures/`](../output/figures/) 复制的**答辩/附件优先展示**子集，与正文「数据—成本—质量—识别」主线一致。完整出图见仓库根目录命令：

`py -3 scripts/tepsa_figures.py` 与 `py -3 scripts/tepsa_figures.py --extended`（详见 [`docs/统模画图任务清单.md`](../docs/统模画图任务清单.md)）。

| 文件 | 用途简述 |
|------|----------|
| `fig01_schematic_national_to_mvp.png` | 国家战略 → 可估计子问题的叙事收缩 |
| `fig03_schematic_data_to_dashboard.png` | 数据—估计—看板流程 |
| `fig_run_id_counts_allruns.png` | 各 `run_id` 样本量，说明可复现窗口 |
| `fig_cost_by_policy_allruns.png` | 单次调用成本按策略/档位分布 |
| `fig_cost_vs_tokens_allruns.png` | 成本—规模关系（按 provider 着色） |
| `fig02_token_quality_scatter_allruns.png` | Token 与质量 proxy（注意标注口径） |
| `fig04_risk_welfare_scatter_allruns.png` | 风险分层下的成本—质量 |
| `fig_propensity_overlap_allruns.png` | IPW 倾向得分重叠（识别敏感性） |
| `fig_m1_logcost_fitted_vs_actual_allruns.png` | M1 价目—日志核对（拟合 vs 实际） |
| `fig_coef_log_tokens_forest_allruns.png` | 基线 vs within-task 的 `log_tokens` 系数对照 |

*后缀 `_allruns` 为全量 run 汇总；若论文主分析仅用 `ds_batch`，可在本地用同脚本 `--run-id ds_batch` 重出后替换本目录对应文件。*
