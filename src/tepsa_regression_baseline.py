"""
Baseline regressions on obs_macro_preview.csv (TESSA-PSA + macro join).

  pip install -r requirements-regression.txt
  python src/tepsa_regression_baseline.py
  python src/tepsa_regression_baseline.py --run-id ds_batch --out-dir output/regression

Writes:
  - output/regression/tepsa_baseline_summary.md
  - output/regression/tepsa_baseline_coefficients.csv
  - output/regression/tepsa_m1_accounting_metrics.csv (M1 价目核对指标)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO_ROOT / "src"))
import tepsa_main  # noqa: E402
DEFAULT_INPUT = REPO_ROOT / "data" / "tessa_psa" / "obs_macro_preview.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "output" / "regression"


def _prep_base(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["cost_usd"] = pd.to_numeric(d["cost_usd"], errors="coerce")
    d["input_tokens"] = pd.to_numeric(d["input_tokens"], errors="coerce").fillna(0)
    d["output_tokens"] = pd.to_numeric(d["output_tokens"], errors="coerce").fillna(0)
    d["tokens_total"] = d["input_tokens"] + d["output_tokens"]
    d["log_tokens"] = np.log(d["tokens_total"].clip(lower=0) + 1.0)
    d["log_cost"] = np.log(d["cost_usd"].clip(lower=0) + 1e-12)
    d["quality_score"] = pd.to_numeric(d["quality_score"], errors="coerce")
    d["value_score"] = pd.to_numeric(d["value_score"], errors="coerce")
    d["policy_id"] = d["policy_id"].astype(str).str.strip()
    d["tepsa_sector"] = d["tepsa_sector"].astype(str).str.strip()
    d["run_id"] = d["run_id"].astype(str).str.strip()
    if "task_id" in d.columns:
        d["task_id"] = d["task_id"].astype(str).str.strip()
    return d


def _value_score_from_row(r: pd.Series) -> float:
    """Align with tepsa_main.compute_value_score_row (CSV string dict)."""
    rd = {k: ("" if pd.isna(v) else str(v)) for k, v in r.items()}
    s = tepsa_main.compute_value_score_row(rd)
    return float(s) if s not in ("", None) else np.nan


def _drop_sparse_categories(
    d: pd.DataFrame, col: str, min_cell: int
) -> pd.DataFrame:
    if min_cell <= 1:
        return d
    vc = d[col].value_counts()
    keep = set(vc[vc >= min_cell].index)
    return d[d[col].isin(keep)].copy()


def _m1_accounting_metrics(res) -> dict[str, float]:
    """Non-R² diagnostics for M1: pricing–log identity should leave small residuals."""
    y = np.asarray(res.model.endog, dtype=float)
    fh = np.asarray(res.fittedvalues, dtype=float)
    r = np.asarray(res.resid, dtype=float)
    eps = 1e-12
    c_act = np.exp(y) - eps
    c_hat = np.exp(fh) - eps
    rel = np.abs(c_hat - c_act) / np.maximum(c_act, eps)
    return {
        "rmse_log_cost": float(np.sqrt(np.mean(r**2))),
        "mae_log_cost": float(np.mean(np.abs(r))),
        "median_ae_log_cost": float(np.median(np.abs(r))),
        "mean_rel_abs_error_cost": float(np.mean(rel)),
        "median_rel_abs_error_cost": float(np.median(rel)),
    }


def _fit_ols_robust(formula: str, data: pd.DataFrame, model_name: str) -> tuple[object, pd.DataFrame]:
    if len(data) < 10:
        raise ValueError(f"{model_name}: insufficient rows ({len(data)})")
    res = smf.ols(formula, data=data).fit(cov_type="HC1")
    summ = pd.DataFrame(
        {
            "model": model_name,
            "param": res.params.index.astype(str),
            "coef": res.params.values,
            "std_err": res.bse.values,
            "t": res.tvalues.values,
            "pvalue": res.pvalues.values,
        }
    )
    summ["n_obs"] = int(res.nobs)
    summ["r2"] = float(res.rsquared)
    return res, summ


def run_all(
    input_path: Path,
    out_dir: Path,
    run_id: str,
    min_cell: int,
) -> None:
    df = pd.read_csv(input_path, encoding="utf-8")
    df = _prep_base(df)
    if run_id.strip():
        df = df[df["run_id"] == run_id.strip()]
    if df.empty:
        raise SystemExit("No rows after run_id filter.")

    df["value_score_calc"] = df.apply(_value_score_from_row, axis=1)
    _vs_file = pd.to_numeric(df["value_score"], errors="coerce")
    df["value_score_reg"] = _vs_file.where(_vs_file.notna(), df["value_score_calc"])

    out_dir.mkdir(parents=True, exist_ok=True)
    coef_parts: list[pd.DataFrame] = []
    try:
        in_rel = input_path.relative_to(REPO_ROOT)
    except ValueError:
        in_rel = input_path
    md_lines: list[str] = [
        "# TESSA-PSA baseline regressions",
        "",
        f"- **Input**: `{in_rel}`",
        f"- **Rows used (after filter)**: {len(df)}",
        f"- **run_id filter**: `{run_id or '(none)'}`",
        f"- **min_cell** (drop sparse FE levels): {min_cell}",
        "- **SE**: HC1 robust",
        "- **M3** `value_score`: 若 CSV 中 `value_score` 为空，则按 `tepsa_main.compute_value_score_row` 与主表相同默认参数重算为 `value_score_calc`。",
        "",
    ]

    # M1: log cost ~ log tokens + policy FE
    d1 = df[np.isfinite(df["log_cost"]) & np.isfinite(df["log_tokens"])].copy()
    d1 = _drop_sparse_categories(d1, "policy_id", min_cell)
    if d1["policy_id"].nunique() < 2:
        md_lines.append("## M1 log_cost ~ log_tokens + C(policy_id)\n\nSkipped: fewer than 2 policy levels after min_cell filter.\n")
    else:
        res1, c1 = _fit_ols_robust("log_cost ~ log_tokens + C(policy_id)", d1, "M1_log_cost_policy")
        coef_parts.append(c1)
        m1m = _m1_accounting_metrics(res1)
        md_lines.append("## M1 `log_cost ~ log_tokens + C(policy_id)`\n")
        md_lines.append(f"- N = {int(res1.nobs)}, R² = {res1.rsquared:.4f}\n")
        md_lines.append(
            "- **定位（价目—日志核对 / accounting check）**：不把本式当作因果识别或「政策解释力」；高 R² 反映 `cost_usd` 与公开价目×token 的**记账一致性**。\n"
        )
        md_lines.append("- **核对指标**（补充 R²，便于答辩「过拟合了吗」）：\n")
        md_lines.append(
            f"  - log 残差 RMSE = `{m1m['rmse_log_cost']:.6f}`；MAE = `{m1m['mae_log_cost']:.6f}`；|残差|中位数 = `{m1m['median_ae_log_cost']:.6f}`\n"
        )
        md_lines.append(
            f"  - 美元成本相对误差：均值 `{m1m['mean_rel_abs_error_cost']:.4f}`，中位数 `{m1m['median_rel_abs_error_cost']:.4f}`（由 log 空间拟合反推 `cost`）\n"
        )
        pd.DataFrame([{"model": "M1_accounting", **m1m, "n_obs": int(res1.nobs), "r2": float(res1.rsquared)}]).to_csv(
            out_dir / "tepsa_m1_accounting_metrics.csv", index=False, encoding="utf-8"
        )
        md_lines.append("```\n" + res1.summary().as_text() + "\n```\n")

    # M2: quality ~ log tokens + sector FE (labeled subset)
    d2 = df[df["quality_score"].notna() & np.isfinite(df["log_tokens"])].copy()
    d2 = d2[d2["quality_score"] > 0]
    d2 = _drop_sparse_categories(d2, "tepsa_sector", min_cell)
    if len(d2) < 15 or d2["tepsa_sector"].nunique() < 2:
        md_lines.append("## M2 quality_score ~ log_tokens + C(tepsa_sector)\n\nSkipped: insufficient labeled rows or fewer than 2 sectors after filter.\n")
    else:
        res2, c2 = _fit_ols_robust("quality_score ~ log_tokens + C(tepsa_sector)", d2, "M2_quality_sector")
        coef_parts.append(c2)
        md_lines.append("## M2 `quality_score ~ log_tokens + C(tepsa_sector)`\n")
        md_lines.append(f"- N = {int(res2.nobs)}, R² = {res2.rsquared:.4f}\n")
        md_lines.append("```\n" + res2.summary().as_text() + "\n```\n")

    # M3: value_score ~ log tokens + policy FE (CSV column or recomputed)
    d3 = df[np.isfinite(df["log_tokens"]) & df["value_score_reg"].notna()].copy()
    d3 = _drop_sparse_categories(d3, "policy_id", min_cell)
    if len(d3) < 15 or d3["policy_id"].nunique() < 2:
        md_lines.append("## M3 value_score ~ log_tokens + C(policy_id)\n\nSkipped: insufficient non-missing value_score or fewer than 2 policies.\n")
    else:
        res3, c3 = _fit_ols_robust("value_score_reg ~ log_tokens + C(policy_id)", d3, "M3_value_policy")
        coef_parts.append(c3)
        md_lines.append("## M3 `value_score ~ log_tokens + C(policy_id)`\n")
        md_lines.append(f"- N = {int(res3.nobs)}, R² = {res3.rsquared:.4f}\n")
        md_lines.append("```\n" + res3.summary().as_text() + "\n```\n")

    if coef_parts:
        pd.concat(coef_parts, ignore_index=True).to_csv(
            out_dir / "tepsa_baseline_coefficients.csv", index=False, encoding="utf-8"
        )
    else:
        pd.DataFrame(
            columns=["model", "param", "coef", "std_err", "t", "pvalue", "n_obs", "r2"]
        ).to_csv(out_dir / "tepsa_baseline_coefficients.csv", index=False, encoding="utf-8")

    (out_dir / "tepsa_baseline_summary.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_dir / 'tepsa_baseline_summary.md'}")
    print(f"Wrote {out_dir / 'tepsa_baseline_coefficients.csv'}")
    if (out_dir / "tepsa_m1_accounting_metrics.csv").exists():
        print(f"Wrote {out_dir / 'tepsa_m1_accounting_metrics.csv'}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Baseline OLS on obs_macro_preview.csv")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--run-id", default="", help="Keep only this run_id (optional).")
    ap.add_argument(
        "--min-cell",
        type=int,
        default=5,
        help="Drop FE category levels with fewer than this many rows before OLS.",
    )
    args = ap.parse_args()
    run_all(args.input, args.out_dir, args.run_id, args.min_cell)


if __name__ == "__main__":
    main()
