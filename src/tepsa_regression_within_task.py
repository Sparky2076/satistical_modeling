"""
Within-task regressions: keep rows where the same task_id has multiple policy_id
(same run_id window). Absorbs task difficulty/wording via C(task_id).

  pip install -r requirements-regression.txt
  python src/tepsa_regression_within_task.py
  python src/tepsa_regression_within_task.py --run-id ds_batch --out-dir output/regression_within_task

Not RCT: interpret as association conditional on task FE; see docs/tepsa_empirical_chapter_outline.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from tepsa_regression_baseline import (
    DEFAULT_INPUT,
    REPO_ROOT,
    _drop_sparse_categories,
    _fit_ols_robust,
    _prep_base,
    _value_score_from_row,
)


def _filter_multi_policy(df: pd.DataFrame, min_policies: int) -> tuple[pd.DataFrame, dict]:
    g = df.groupby("task_id", observed=True)["policy_id"].nunique()
    keep = set(g[g >= min_policies].index)
    out = df[df["task_id"].isin(keep)].copy()
    qv = g[g >= min_policies].quantile([0.25, 0.5, 0.75])
    meta = {
        "n_rows_before": int(len(df)),
        "n_rows_after": int(len(out)),
        "n_tasks_ge_min": int((g >= min_policies).sum()),
        "min_policies_per_task": min_policies,
        "policies_per_task_q25": float(qv.loc[0.25]) if len(qv) else np.nan,
        "policies_per_task_q50": float(qv.loc[0.50]) if len(qv) else np.nan,
        "policies_per_task_q75": float(qv.loc[0.75]) if len(qv) else np.nan,
    }
    return out, meta


def run_within_task(
    input_path: Path,
    out_dir: Path,
    run_id: str,
    min_cell: int,
    min_policies_per_task: int,
) -> None:
    df = pd.read_csv(input_path, encoding="utf-8")
    df = _prep_base(df)
    if "task_id" not in df.columns:
        raise SystemExit("Input CSV must contain task_id.")
    if run_id.strip():
        df = df[df["run_id"] == run_id.strip()]
    if df.empty:
        raise SystemExit("No rows after run_id filter.")

    df["value_score_calc"] = df.apply(_value_score_from_row, axis=1)
    _vs_file = pd.to_numeric(df["value_score"], errors="coerce")
    df["value_score_reg"] = _vs_file.where(_vs_file.notna(), df["value_score_calc"])

    df_w, meta = _filter_multi_policy(df, min_policies_per_task)
    out_dir.mkdir(parents=True, exist_ok=True)
    if meta["n_rows_after"] == 0:
        (out_dir / "tepsa_within_task_summary.md").write_text(
            "# Within-task regressions\n\n**Skipped**: no tasks with enough distinct `policy_id`.\n",
            encoding="utf-8",
        )
        pd.DataFrame([meta]).to_csv(out_dir / "tepsa_within_task_sample_meta.csv", index=False, encoding="utf-8")
        print(f"Wrote {out_dir / 'tepsa_within_task_summary.md'} (empty sample)")
        return
    try:
        in_rel = input_path.relative_to(REPO_ROOT)
    except ValueError:
        in_rel = input_path

    md_lines: list[str] = [
        "# TESSA-PSA within-task regressions (task fixed effects)",
        "",
        f"- **Input**: `{in_rel}`",
        f"- **run_id filter**: `{run_id or '(none)'}`",
        f"- **min_policies_per_task**: {min_policies_per_task}",
        f"- **Retention**: rows {meta['n_rows_after']} / {meta['n_rows_before']} "
        f"({100.0 * meta['n_rows_after'] / max(meta['n_rows_before'], 1):.1f}%)",
        f"- **Tasks with ≥{min_policies_per_task} policies**: {meta['n_tasks_ge_min']}",
        f"- **Policies per task (q25/median/q75, among kept tasks)**: "
        f"{meta['policies_per_task_q25']:.2f} / {meta['policies_per_task_q50']:.2f} / {meta['policies_per_task_q75']:.2f}",
        "- **SE**: HC1 robust",
        "- **解释**：控制 `task_id` 后，利用**同一任务多策略**的 within 变异；**不等于**随机实验，需与正文局限一致。",
        "",
    ]

    coef_parts: list[pd.DataFrame] = []

    # M1w: pricing within task + policy
    d1 = df_w[np.isfinite(df_w["log_cost"]) & np.isfinite(df_w["log_tokens"])].copy()
    d1 = _drop_sparse_categories(d1, "policy_id", min_cell)
    if len(d1) < 20 or d1["policy_id"].nunique() < 2 or d1["task_id"].nunique() < 2:
        md_lines.append("## M1w `log_cost ~ log_tokens + C(task_id) + C(policy_id)`\n\nSkipped: insufficient rows or FE levels.\n")
    else:
        res, c = _fit_ols_robust(
            "log_cost ~ log_tokens + C(task_id) + C(policy_id)", d1, "M1w_cost_task_policy_fe"
        )
        coef_parts.append(c)
        md_lines.append("## M1w `log_cost ~ log_tokens + C(task_id) + C(policy_id)`\n")
        md_lines.append(
            f"- N = {int(res.nobs)}, R² = {res.rsquared:.4f}（仍可能极高：成本仍由价目×token 决定；本式强调**任务内**截距与策略差，而非因果 AT）\n"
        )
        md_lines.append("```\n" + res.summary().as_text() + "\n```\n")

    # M2w: quality ~ tokens + task FE
    d2 = df_w[df_w["quality_score"].notna() & np.isfinite(df_w["log_tokens"])].copy()
    d2 = d2[d2["quality_score"] > 0]
    if len(d2) < 20 or d2["task_id"].nunique() < 2:
        md_lines.append("## M2w `quality_score ~ log_tokens + C(task_id)`\n\nSkipped: insufficient labeled rows or tasks.\n")
    else:
        res, c = _fit_ols_robust("quality_score ~ log_tokens + C(task_id)", d2, "M2w_quality_task_fe")
        coef_parts.append(c)
        md_lines.append("## M2w `quality_score ~ log_tokens + C(task_id)`\n")
        md_lines.append(f"- N = {int(res.nobs)}, R² = {res.rsquared:.4f}\n")
        md_lines.append("```\n" + res.summary().as_text() + "\n```\n")

    # M3w: value ~ tokens + task + policy
    d3 = df_w[np.isfinite(df_w["log_tokens"]) & df_w["value_score_reg"].notna()].copy()
    d3 = _drop_sparse_categories(d3, "policy_id", min_cell)
    if len(d3) < 20 or d3["policy_id"].nunique() < 2 or d3["task_id"].nunique() < 2:
        md_lines.append("## M3w `value_score_reg ~ log_tokens + C(task_id) + C(policy_id)`\n\nSkipped.\n")
    else:
        res, c = _fit_ols_robust(
            "value_score_reg ~ log_tokens + C(task_id) + C(policy_id)",
            d3,
            "M3w_value_task_policy_fe",
        )
        coef_parts.append(c)
        md_lines.append("## M3w `value_score_reg ~ log_tokens + C(task_id) + C(policy_id)`\n")
        md_lines.append(f"- N = {int(res.nobs)}, R² = {res.rsquared:.4f}\n")
        md_lines.append("```\n" + res.summary().as_text() + "\n```\n")

    if coef_parts:
        pd.concat(coef_parts, ignore_index=True).to_csv(
            out_dir / "tepsa_within_task_coefficients.csv", index=False, encoding="utf-8"
        )
    else:
        pd.DataFrame(
            columns=["model", "param", "coef", "std_err", "t", "pvalue", "n_obs", "r2"]
        ).to_csv(out_dir / "tepsa_within_task_coefficients.csv", index=False, encoding="utf-8")

    pd.DataFrame([meta]).to_csv(out_dir / "tepsa_within_task_sample_meta.csv", index=False, encoding="utf-8")
    (out_dir / "tepsa_within_task_summary.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_dir / 'tepsa_within_task_summary.md'}")
    print(f"Wrote {out_dir / 'tepsa_within_task_coefficients.csv'}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Within-task OLS with C(task_id) on multi-policy tasks")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out-dir", type=Path, default=_REPO / "output" / "regression_within_task")
    ap.add_argument("--run-id", default="", help="Keep only this run_id (optional).")
    ap.add_argument("--min-cell", type=int, default=5, help="Min rows per policy FE level (M1w/M3w).")
    ap.add_argument(
        "--min-policies-per-task",
        type=int,
        default=2,
        help="Keep tasks with at least this many distinct policy_id values.",
    )
    args = ap.parse_args()
    run_within_task(args.input, args.out_dir, args.run_id, args.min_cell, args.min_policies_per_task)


if __name__ == "__main__":
    main()
