"""
Identification placebos / permutation checks on obs_macro_preview.

  pip install -r requirements-regression.txt
  python src/tepsa_identification_placebos.py
  python src/tepsa_identification_placebos.py --run-id ds_batch --n-reps 499

1) Task-level random permutation of policy_id (multiset fixed per task) on the
   within-multi-policy sample; null for row-level mean(quality|T=1) - mean(quality|T=0).

2) On the IPW analysis frame (build_ipw_frame): stratified permutation of T within
   (difficulty_label, risk_class, tepsa_sector), holding pscore fixed; null for Hajek ATE.

Outputs under output/identification_placebo/ (see docs/tepsa_empirical_chapter_outline.md).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from tepsa_regression_baseline import (  # noqa: E402
    DEFAULT_INPUT,
    REPO_ROOT,
    _prep_base,
    _value_score_from_row,
)
from tepsa_regression_ipw import (  # noqa: E402
    IPWFrameBuildError,
    _hajek_ate,
    build_ipw_frame,
)
from tepsa_regression_within_task import _filter_multi_policy  # noqa: E402

STRATA = ("difficulty_label", "risk_class", "tepsa_sector")


def _prep_with_value(df: pd.DataFrame) -> pd.DataFrame:
    d = _prep_base(df)
    d["value_score_calc"] = d.apply(_value_score_from_row, axis=1)
    _vs_file = pd.to_numeric(d["value_score"], errors="coerce")
    d["value_score_reg"] = _vs_file.where(_vs_file.notna(), d["value_score_calc"])
    return d


def _mean_quality_treat_diff(df: pd.DataFrame, treat_policy: str) -> float:
    pol = df["policy_id"].astype(str).str.strip()
    t = (pol == treat_policy.strip()).astype(int)
    y = pd.to_numeric(df["quality_score"], errors="coerce")
    if not (t == 1).any() or not (t == 0).any():
        return float("nan")
    m1 = float(y[t == 1].mean())
    m0 = float(y[t == 0].mean())
    return m1 - m0


def _permute_policy_within_task(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    out = df.copy()
    out["policy_id"] = out["policy_id"].astype(str).str.strip()
    for _tid, g in out.groupby("task_id", sort=False):
        idx = g.index.to_numpy()
        vals = out.loc[idx, "policy_id"].to_numpy()
        out.loc[idx, "policy_id"] = rng.permutation(vals)
    return out


def run_task_policy_permutation(
    df_in: pd.DataFrame,
    treat_policy: str,
    n_reps: int,
    min_policies_per_task: int,
    rng: np.random.Generator,
) -> tuple[float, np.ndarray, str | None]:
    d = _prep_with_value(df_in)
    if "task_id" not in d.columns:
        return float("nan"), np.array([]), "no task_id"
    df_w, meta = _filter_multi_policy(d, min_policies_per_task)
    if meta["n_rows_after"] == 0:
        return float("nan"), np.array([]), "no multi-policy tasks"
    sub = df_w.copy()
    sub["quality_score"] = pd.to_numeric(sub["quality_score"], errors="coerce")
    sub = sub[sub["quality_score"].notna() & (sub["quality_score"] > 0)]
    if len(sub) < 10:
        return float("nan"), np.array([]), "insufficient quality rows"
    obs = _mean_quality_treat_diff(sub, treat_policy)
    if not np.isfinite(obs):
        return float("nan"), np.array([]), "degenerate T on subsample"
    nulls = np.empty(n_reps, dtype=float)
    for r in range(n_reps):
        perm = _permute_policy_within_task(sub, rng)
        nulls[r] = _mean_quality_treat_diff(perm, treat_policy)
    return float(obs), nulls, None


def _permute_T_stratified(dz: pd.DataFrame, rng: np.random.Generator) -> tuple[np.ndarray, bool]:
    """Returns (T_perm, used_global_fallback)."""
    out = dz.copy()
    t = out["T"].to_numpy(dtype=int)
    out["_Tperm"] = t.astype(float)
    any_strata = False
    for _, g in out.groupby(list(STRATA), sort=False):
        idx = g.index.to_numpy()
        ts = out.loc[idx, "T"].to_numpy(dtype=int)
        if np.unique(ts).size < 2:
            continue
        any_strata = True
        out.loc[idx, "_Tperm"] = rng.permutation(ts).astype(float)
    if not any_strata:
        return rng.permutation(t).astype(float), True
    return out["_Tperm"].to_numpy(dtype=float), False


def run_hajek_T_permutation(
    dz: pd.DataFrame,
    n_reps: int,
    rng: np.random.Generator,
) -> tuple[float, np.ndarray, bool]:
    p = np.asarray(dz["pscore"], dtype=float)
    T = np.asarray(dz["T"], dtype=float)
    Y = np.asarray(dz["Y"], dtype=float)
    _, _, obs_ate = _hajek_ate(T, Y, p)
    nulls = np.empty(n_reps, dtype=float)
    global_warn = False
    for r in range(n_reps):
        Tp, fb = _permute_T_stratified(dz, rng)
        if fb:
            global_warn = True
        _, _, ate = _hajek_ate(Tp, Y, p)
        nulls[r] = ate
    return float(obs_ate), nulls, global_warn


def _two_sided_p(obs: float, nulls: np.ndarray) -> float:
    if nulls.size == 0 or not np.isfinite(obs):
        return float("nan")
    c = int(np.sum(np.abs(nulls) >= abs(obs)))
    return (1.0 + c) / (1.0 + len(nulls))


def _set_plot_font() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "figure.facecolor": "white",
            "axes.facecolor": "#fafafa",
        }
    )


def _write_figure(
    out_png: Path,
    null_task: np.ndarray,
    obs_task: float,
    null_haj: np.ndarray,
    obs_haj: float,
    task_skip: str | None,
    haj_skip: str | None,
) -> None:
    _set_plot_font()
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5))
    if task_skip is None and null_task.size > 0:
        nb0 = min(40, max(10, len(null_task) // 5))
        axes[0].hist(null_task, bins=nb0, color="#1565c0", alpha=0.85, edgecolor="white")
        axes[0].axvline(obs_task, color="#c62828", lw=2, label=f"观测 = {obs_task:.4f}")
        axes[0].set_title("实验1：任务内 policy 置换\nmean(quality|T=1)−mean(T=0)", fontweight="bold")
        axes[0].set_xlabel("零分布")
        axes[0].legend(fontsize=8)
    else:
        axes[0].text(0.5, 0.5, f"未绘图：{task_skip or '无数据'}", ha="center", va="center", transform=axes[0].transAxes)

    if haj_skip is None and null_haj.size > 0:
        axes[1].hist(null_haj, bins=min(40, max(10, len(null_haj) // 5)), color="#3949ab", alpha=0.85, edgecolor="white")
        axes[1].axvline(obs_haj, color="#c62828", lw=2, label=f"观测 = {obs_haj:.4f}")
        axes[1].set_title("实验2：分层内 T 置换（固定 pscore）\nHajek ATE 零分布", fontweight="bold")
        axes[1].set_xlabel("ATE")
        axes[1].legend(fontsize=8)
    else:
        axes[1].text(0.5, 0.5, f"未绘图：{haj_skip or '无数据'}", ha="center", va="center", transform=axes[1].transAxes)
    fig.suptitle("识别安慰剂：置换检验（非 RCT）", fontsize=11, y=1.02)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def run_all(
    input_path: Path,
    out_dir: Path,
    run_id: str,
    treat_policy: str,
    n_reps: int,
    min_policies_per_task: int,
    ipw_clip: float,
    ipw_outcome: str,
    seed: int,
) -> None:
    rng = np.random.default_rng(seed)
    df = pd.read_csv(input_path, encoding="utf-8")
    df = _prep_base(df)
    if run_id.strip():
        df = df[df["run_id"] == run_id.strip()]
    if df.empty:
        raise SystemExit("No rows after run_id filter.")

    try:
        in_rel = input_path.relative_to(REPO_ROOT)
    except ValueError:
        in_rel = input_path

    out_dir.mkdir(parents=True, exist_ok=True)

    obs_task, null_task, task_err = run_task_policy_permutation(
        df, treat_policy, n_reps, min_policies_per_task, rng
    )
    p_task = _two_sided_p(obs_task, null_task) if task_err is None else float("nan")

    haj_err: str | None = None
    obs_haj = float("nan")
    null_haj = np.array([])
    global_fallback = False
    try:
        dz, _, _, _ = build_ipw_frame(input_path, run_id, treat_policy, ipw_outcome, ipw_clip)
        obs_haj, null_haj, global_fallback = run_hajek_T_permutation(dz, n_reps, rng)
    except IPWFrameBuildError as e:
        haj_err = str(e)

    p_haj = _two_sided_p(obs_haj, null_haj) if haj_err is None and null_haj.size else float("nan")

    if null_task.size:
        pd.DataFrame({"rep": np.arange(1, n_reps + 1), "stat_mean_diff": null_task}).to_csv(
            out_dir / "tepsa_placebo_null_task_perm.csv", index=False, encoding="utf-8"
        )
    if null_haj.size:
        pd.DataFrame({"rep": np.arange(1, n_reps + 1), "ate_hajek": null_haj}).to_csv(
            out_dir / "tepsa_placebo_null_hajek_perm.csv", index=False, encoding="utf-8"
        )

    md = [
        "# 识别安慰剂 / 置换检验（仓库内「实验」）",
        "",
        f"- **Input**: `{in_rel}`",
        f"- **run_id**: `{run_id or '(none)'}`",
        f"- **treat_policy (T=1)**: `{treat_policy}`",
        f"- **n_reps**: {n_reps}",
        f"- **RNG seed**: {seed}",
        "",
        "## 实验1：任务内 `policy_id` 置换（质量）",
        "",
        "- **样本**：within-task 多策略任务子集；`quality_score > 0`。",
        "- **观测统计量**：行级 `mean(Y|T=1) - mean(Y|T=0)`。",
        "- **零假设参照**：组内打乱 `policy_id`（每任务 multiset 不变），重算均值差。",
        "",
    ]
    if task_err:
        md.append(f"**跳过**：{task_err}\n")
    else:
        md.extend(
            [
                f"- **观测统计量** ≈ `{obs_task:.6f}`",
                f"- **零分布**：均值 `{float(np.mean(null_task)):.6f}`，SD `{float(np.std(null_task, ddof=1)):.6f}`",
                f"- **双侧 p（|null|≥|obs|）** ≈ `{p_task:.6f}`",
                "",
            ]
        )

    md.extend(
        [
            "## 实验2：分层内 `T` 置换 + Hajek（固定倾向 `pscore`）",
            "",
            "- **样本**：与 `build_ipw_frame` / IPW 一致。",
            "- **观测统计量**：Hajek ATE（与 `tepsa_regression_ipw` 相同公式）。",
            "- **零假设参照**：在 `(difficulty_label, risk_class, tepsa_sector)` 层内置换 `T`，**不重估 logit**，`pscore` 不变；",
            "  含义是「在同一拟合倾向下，若处理与结果独立」的参照，**非**同时重估倾向得分。",
            "",
        ]
    )
    if haj_err:
        md.append(f"**跳过**：{haj_err}\n")
    else:
        if global_fallback:
            md.append("- **注意**：无可用分层（层内 T 全 0 或全 1），已 **全局置换 T**（边际 P(T=1) 不变但破坏分层结构）。\n")
        md.extend(
            [
                f"- **观测 Hajek ATE** ≈ `{obs_haj:.6f}`",
                f"- **零分布**：均值 `{float(np.mean(null_haj)):.6f}`，SD `{float(np.std(null_haj, ddof=1)):.6f}`",
                f"- **双侧 p** ≈ `{p_haj:.6f}`",
                "",
            ]
        )

    md.extend(
        [
            "## 局限",
            "",
            "- 置换 **不** 替代随机实验；p 值在依赖模型/样本构造时需谨慎叙述。",
            "- 与正文「谨慎条件相关 / 敏感性」一致；强因果主张需外生设计。",
            "",
        ]
    )
    (out_dir / "tepsa_placebo_summary.md").write_text("\n".join(md), encoding="utf-8")

    _write_figure(
        out_dir / "fig_placebo_null_distributions.png",
        null_task,
        obs_task,
        null_haj,
        obs_haj,
        task_err,
        haj_err,
    )

    print(f"Wrote {out_dir / 'tepsa_placebo_summary.md'}")
    if null_task.size:
        print(f"Wrote {out_dir / 'tepsa_placebo_null_task_perm.csv'}")
    if null_haj.size:
        print(f"Wrote {out_dir / 'tepsa_placebo_null_hajek_perm.csv'}")
    print(f"Wrote {out_dir / 'fig_placebo_null_distributions.png'}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Permutation placebo checks for identification")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out-dir", type=Path, default=_REPO / "output" / "identification_placebo")
    ap.add_argument("--run-id", default="", help="Filter run_id (optional).")
    ap.add_argument("--treat-policy", default="pl_deepseek_pro")
    ap.add_argument("--n-reps", type=int, default=499)
    ap.add_argument("--min-policies-per-task", type=int, default=2)
    ap.add_argument("--ipw-clip", type=float, default=0.05)
    ap.add_argument("--ipw-outcome", choices=("quality", "value"), default="quality")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    run_all(
        args.input,
        args.out_dir,
        args.run_id,
        args.treat_policy,
        args.n_reps,
        args.min_policies_per_task,
        args.ipw_clip,
        args.ipw_outcome,
        args.seed,
    )


if __name__ == "__main__":
    main()
