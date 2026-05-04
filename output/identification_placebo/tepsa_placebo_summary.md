# 识别安慰剂 / 置换检验（仓库内「实验」）

- **Input**: `data\tessa_psa\obs_macro_preview.csv`
- **run_id**: `(none)`
- **treat_policy (T=1)**: `pl_deepseek_pro`
- **n_reps**: 199
- **RNG seed**: 42

## 实验1：任务内 `policy_id` 置换（质量）

- **样本**：within-task 多策略任务子集；`quality_score > 0`。
- **观测统计量**：行级 `mean(Y|T=1) - mean(Y|T=0)`。
- **零假设参照**：组内打乱 `policy_id`（每任务 multiset 不变），重算均值差。

- **观测统计量** ≈ `1.029049`
- **零分布**：均值 `-0.140384`，SD `0.096380`
- **双侧 p（|null|≥|obs|）** ≈ `0.005000`

## 实验2：分层内 `T` 置换 + Hajek（固定倾向 `pscore`）

- **样本**：与 `build_ipw_frame` / IPW 一致。
- **观测统计量**：Hajek ATE（与 `tepsa_regression_ipw` 相同公式）。
- **零假设参照**：在 `(difficulty_label, risk_class, tepsa_sector)` 层内置换 `T`，**不重估 logit**，`pscore` 不变；
  含义是「在同一拟合倾向下，若处理与结果独立」的参照，**非**同时重估倾向得分。

- **观测 Hajek ATE** ≈ `1.180370`
- **零分布**：均值 `-0.000561`，SD `0.100188`
- **双侧 p** ≈ `0.005000`

## 局限

- 置换 **不** 替代随机实验；p 值在依赖模型/样本构造时需谨慎叙述。
- 与正文「谨慎条件相关 / 敏感性」一致；强因果主张需外生设计。
