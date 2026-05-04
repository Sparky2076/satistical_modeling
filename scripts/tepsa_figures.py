
"""
Generate competition-style figures from obs_macro_preview.csv (or enriched).

  pip install -r requirements-viz.txt
  python scripts/tepsa_figures.py
  python scripts/tepsa_figures.py --run-id ds_batch
  python scripts/tepsa_figures.py --extended
  python scripts/tepsa_figures.py --extended --run-id ds_batch

Outputs PNG under output/figures/ (300 dpi).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "data" / "tessa_psa" / "obs_macro_preview.csv"
OUT_DIR = REPO_ROOT / "output" / "figures"


def _set_cn_font() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "figure.facecolor": "white",
            "axes.facecolor": "#fafafa",
            "axes.grid": True,
            "grid.alpha": 0.35,
        }
    )


def load_obs(path: Path, run_id: str | None) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    if run_id:
        df = df[df["run_id"].astype(str).str.strip() == run_id.strip()]
    return df


def fig_schematic_shrinkage(out: Path) -> None:
    """图1 风格：国家战略 → TESSA-PSA → 可估计子问题。"""
    fig, ax = plt.subplots(figsize=(8, 2.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1)
    ax.axis("off")
    boxes = [
        (0.2, 0.2, 2.6, 0.6, "「人工智能+」\n国家战略叙事"),
        (3.6, 0.2, 2.8, 0.6, "TESSA-PSA\n测度—估计—配置"),
        (7.0, 0.2, 2.6, 0.6, "任务级 Token\n与预算配置"),
    ]
    for x, y, w, h, t in boxes:
        ax.add_patch(
            plt.Rectangle(
                (x, y),
                w,
                h,
                fill=True,
                facecolor="#e3f2fd",
                edgecolor="#1565c0",
                linewidth=1.5,
            )
        )
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=10)
    for x in [2.9, 6.5]:
        ax.annotate("", xy=(x + 0.35, 0.5), xytext=(x, 0.5), arrowprops=dict(arrowstyle="->", color="#424242", lw=1.5))
    ax.set_title("图1  从国家战略到统计建模的收缩路径（示意）", fontsize=12, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_schematic_data_pipeline(out: Path) -> None:
    """图3 风格：数据 → 估计 → 看板。"""
    fig, ax = plt.subplots(figsize=(8, 2.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1)
    ax.axis("off")
    steps = [
        (0.3, 0.25, 2.4, 0.55, "任务库\n价目·基准"),
        (3.5, 0.25, 2.4, 0.55, "API 观测\n与合并表"),
        (6.7, 0.25, 2.6, 0.55, "统计估计\n与可视化"),
    ]
    for x, y, w, h, t in steps:
        ax.add_patch(
            plt.Rectangle(
                (x, y),
                w,
                h,
                fill=True,
                facecolor="#fff3e0",
                edgecolor="#ef6c00",
                linewidth=1.5,
            )
        )
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=10)
    for x in [2.8, 6.0]:
        ax.annotate("", xy=(x + 0.45, 0.52), xytext=(x, 0.52), arrowprops=dict(arrowstyle="->", color="#424242", lw=1.5))
    ax.set_title("图3  数据到政策看板的建模流程（示意）", fontsize=12, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_run_id_counts(df: pd.DataFrame, out: Path) -> None:
    s = df.groupby("run_id").size().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    s.plot(kind="barh", ax=ax, color="#5c6bc0")
    ax.set_xlabel("观测行数")
    ax.set_title("各 run_id 样本量", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_cost_by_policy(
    df: pd.DataFrame,
    out: Path,
    min_n_box: int = 5,
) -> None:
    """箱线仅用于 n≥min_n_box；低于阈值只画观测点，避免 n=1 退化成「假箱线」。"""
    min_n_box = max(2, int(min_n_box))
    df = df.copy()
    df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce")
    pol_col = "policy_id"
    policies = sorted(df[pol_col].dropna().astype(str).unique())
    pos = np.arange(1, len(policies) + 1, dtype=int)
    counts = {p: int(df.loc[df[pol_col] == p, "cost_usd"].notna().sum()) for p in policies}

    box_data: list[np.ndarray] = []
    box_positions: list[int] = []
    low_x: list[int] = []
    low_y: list[float] = []

    for i, p in zip(pos, policies):
        sub = df.loc[df[pol_col] == p, "cost_usd"].dropna().to_numpy(dtype=float)
        n = len(sub)
        if n >= min_n_box:
            box_data.append(sub)
            box_positions.append(int(i))
        elif n > 0:
            low_x.extend([int(i)] * n)
            low_y.extend(sub.tolist())

    fig, ax = plt.subplots(figsize=(9, 4.5))
    if box_data:
        bp = ax.boxplot(
            box_data,
            positions=box_positions,
            widths=0.55,
            showfliers=True,
            patch_artist=True,
        )
        for b in bp.get("boxes", ()) or []:
            b.set_facecolor("#c8e6c9")
            b.set_alpha(0.88)
    if low_x:
        ax.scatter(
            low_x,
            low_y,
            s=95,
            c="#c62828",
            marker="D",
            zorder=5,
            edgecolors="white",
            linewidths=1.0,
            label=f"n<{min_n_box}（仅观测点，不作分布比较）",
        )
    ax.set_xticks(list(pos))
    ax.set_xticklabels([f"{p}\n(n={counts[p]})" for p in policies], rotation=32, ha="right")
    ax.set_ylabel("cost_usd")
    ax.set_xlabel("policy_id")
    ax.set_title(
        f"单次调用成本（USD）按 policy_id（箱线需 n≥{min_n_box}；否则为单次/少量点）",
        fontweight="bold",
    )
    if low_x:
        ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, axis="y", alpha=0.35)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_tokens_total_hist(df: pd.DataFrame, out: Path) -> None:
    tin = pd.to_numeric(df["input_tokens"], errors="coerce").fillna(0)
    tout = pd.to_numeric(df["output_tokens"], errors="coerce").fillna(0)
    tot = tin + tout
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(tot, bins=40, color="#00897b", edgecolor="white", alpha=0.85)
    ax.set_xlabel("input + output tokens")
    ax.set_ylabel("频数")
    ax.set_title("Token 用量分布（全样本）", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_cost_vs_tokens(df: pd.DataFrame, out: Path) -> None:
    df = df.copy()
    df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce")
    df["tok"] = pd.to_numeric(df["input_tokens"], errors="coerce").fillna(0) + pd.to_numeric(
        df["output_tokens"], errors="coerce"
    ).fillna(0)
    fig, ax = plt.subplots(figsize=(7, 5))
    for prov, sub in df.groupby(df["provider"].fillna("unknown")):
        ax.scatter(sub["tok"], sub["cost_usd"], s=12, alpha=0.55, label=str(prov))
    ax.set_xlabel("input + output tokens")
    ax.set_ylabel("cost_usd")
    ax.set_title("成本—Token 散点（按 provider 着色）", fontweight="bold")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_latency_by_provider(df: pd.DataFrame, out: Path) -> None:
    df = df.copy()
    df["latency_sec"] = pd.to_numeric(df["latency_sec"], errors="coerce")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    df.boxplot(column="latency_sec", by="provider", ax=ax, rot=25)
    ax.set_title("延迟（秒）按 provider", fontweight="bold")
    ax.set_ylabel("latency_sec")
    plt.suptitle("")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_sector_median_cost(df: pd.DataFrame, out: Path) -> None:
    df = df.copy()
    df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce")
    g = df.groupby("tepsa_sector", dropna=False)["cost_usd"].median().sort_values()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    g.plot(kind="barh", ax=axes[0], color="#6a1b9a")
    axes[0].set_title("tepsa_sector 单次成本中位数")
    axes[0].set_xlabel("median cost_usd")
    c = df.groupby("tepsa_sector").size().sort_values()
    c.plot(kind="barh", ax=axes[1], color="#00695c")
    axes[1].set_title("tepsa_sector 观测条数")
    axes[1].set_xlabel("行数")
    fig.suptitle("扇区结构（与宏观 join 一致）", fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_quality_vs_tokens(df: pd.DataFrame, out: Path) -> None:
    """图2 占位：质量分 vs Token；含占位标注时在脚注说明。"""
    df = df.copy()
    df["quality_score"] = pd.to_numeric(df["quality_score"], errors="coerce")
    df["tok"] = pd.to_numeric(df["input_tokens"], errors="coerce").fillna(0) + pd.to_numeric(
        df["output_tokens"], errors="coerce"
    ).fillna(0)
    sub = df[df["quality_score"].notna() & (df["quality_score"] > 0)]
    fig, ax = plt.subplots(figsize=(7, 5))
    if len(sub) > 0:
        sc = ax.scatter(
            sub["tok"],
            sub["quality_score"],
            c=pd.to_numeric(sub["cost_usd"], errors="coerce"),
            cmap="viridis",
            s=35,
            alpha=0.75,
        )
        fig.colorbar(sc, ax=ax).set_label("cost_usd")
    else:
        ax.text(0.5, 0.5, "无有效 quality_score\n（请先完成人工标注）", ha="center", va="center", transform=ax.transAxes)
    ax.set_xlabel("input + output tokens")
    ax.set_ylabel("quality_score（合并标注列）")
    nq = len(sub)
    if nq >= 50:
        ax.set_title(f"图2  Token—质量散点（n={nq}；DS / GLM / Spark 合并标注列，含自动评测）", fontweight="bold")
    else:
        ax.set_title("图2  Token—质量散点（示意；扩充标注后更新）", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_risk_welfare_frontier(df: pd.DataFrame, out: Path) -> None:
    """图4 占位：成本 vs 质量，颜色为任务 risk_class。"""
    df = df.copy()
    df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce")
    df["quality_score"] = pd.to_numeric(df["quality_score"], errors="coerce")
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    plot_df = df[df["quality_score"].notna() & df["cost_usd"].notna()]
    for risk, sub in plot_df.groupby(plot_df["risk_class"].fillna("unknown")):
        ax.scatter(
            sub["cost_usd"],
            sub["quality_score"],
            s=22,
            alpha=0.65,
            label=str(risk),
        )
    ax.set_xlabel("cost_usd（代理「成本」轴）")
    ax.set_ylabel("quality_score（合并标注列）")
    n4 = len(plot_df)
    if n4 >= 50:
        ax.set_title(f"图4  风险分层下的成本—质量散点（n={n4}）", fontweight="bold")
    else:
        ax.set_title("图4  风险分层下的成本—质量散点（示意）", fontweight="bold")
    ax.legend(title="risk_class", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def _ensure_src_on_path() -> None:
    src = REPO_ROOT / "src"
    p = str(src)
    if p not in sys.path:
        sys.path.insert(0, p)


def _prep_like_baseline(df: pd.DataFrame) -> pd.DataFrame:
    _ensure_src_on_path()
    from tepsa_regression_baseline import _prep_base, _value_score_from_row

    d = _prep_base(df)
    d["value_score_calc"] = d.apply(_value_score_from_row, axis=1)
    _vs_file = pd.to_numeric(d["value_score"], errors="coerce")
    d["value_score_reg"] = _vs_file.where(_vs_file.notna(), d["value_score_calc"])
    return d


def fig_propensity_overlap(
    input_csv: Path,
    run_id: str,
    out: Path,
    treat_policy: str,
    clip: float,
    outcome: str,
) -> bool:
    _ensure_src_on_path()
    from tepsa_regression_ipw import IPWFrameBuildError, build_ipw_frame

    try:
        dz, _, _, _ = build_ipw_frame(input_csv, run_id, treat_policy, outcome, clip)
    except IPWFrameBuildError as e:
        print(f"[extended] Skip propensity overlap: {e}")
        return False
    p = np.asarray(dz["pscore"], dtype=float)
    t = np.asarray(dz["T"], dtype=int)
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bins = 28
    ax.hist(p[t == 0], bins=bins, alpha=0.55, color="#3949ab", label=f"对照 T=0 (n={(t == 0).sum()})", density=True)
    ax.hist(p[t == 1], bins=bins, alpha=0.55, color="#c62828", label=f"处理 T=1 (n={(t == 1).sum()})", density=True)
    ax.set_xlabel(r"$\hat p$ = P(T=1|Z)（裁剪后）")
    ax.set_ylabel("密度")
    rid = run_id.strip() or "全 run"
    ax.set_title(
        f"倾向得分重叠（policy={treat_policy}；{rid}；outcome={outcome}）",
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_m1_logcost_fitted_vs_actual(df: pd.DataFrame, out: Path, min_cell: int) -> bool:
    _ensure_src_on_path()
    from tepsa_regression_baseline import _drop_sparse_categories

    d = _prep_like_baseline(df)
    d1 = d[np.isfinite(d["log_cost"]) & np.isfinite(d["log_tokens"])].copy()
    d1 = _drop_sparse_categories(d1, "policy_id", min_cell)
    if len(d1) < 20 or d1["policy_id"].nunique() < 2:
        print("[extended] Skip M1 fitted vs actual: insufficient rows or policy levels.")
        return False
    res = smf.ols("log_cost ~ log_tokens + C(policy_id)", data=d1).fit(cov_type="HC1")
    y = np.asarray(res.model.endog, dtype=float)
    fh = np.asarray(res.fittedvalues, dtype=float)
    r = np.asarray(res.resid, dtype=float)
    lt = np.asarray(d1["log_tokens"], dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5))
    n = len(y)
    if n > 5000:
        idx = np.random.default_rng(0).choice(n, size=5000, replace=False)
        yp, fhp, rp, ltp = y[idx], fh[idx], r[idx], lt[idx]
    else:
        yp, fhp, rp, ltp = y, fh, r, lt
    axes[0].scatter(fhp, yp, s=8, alpha=0.35, c="#1565c0")
    lo = float(min(yp.min(), fhp.min()))
    hi = float(max(yp.max(), fhp.max()))
    axes[0].plot([lo, hi], [lo, hi], color="#c62828", lw=1.2, label="y=x")
    axes[0].set_xlabel("拟合 log(cost+ε)")
    axes[0].set_ylabel("实际 log(cost+ε)")
    axes[0].set_title("M1 价目核对：拟合 vs 实际（对数成本）", fontweight="bold")
    axes[0].legend(loc="upper left", fontsize=8)
    axes[1].scatter(ltp, rp, s=8, alpha=0.35, c="#00695c")
    axes[1].axhline(0.0, color="#c62828", lw=1.0)
    axes[1].set_xlabel("log_tokens")
    axes[1].set_ylabel("残差（log 成本）")
    axes[1].set_title("残差 — log_tokens", fontweight="bold")
    fig.suptitle(f"M1 OLS + C(policy_id)，HC1；N={int(res.nobs)}", fontsize=10, y=1.02)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_coef_log_tokens_forest(
    df: pd.DataFrame,
    out: Path,
    min_cell: int,
    min_policies_per_task: int,
) -> bool:
    _ensure_src_on_path()
    from tepsa_regression_baseline import _drop_sparse_categories, _fit_ols_robust
    from tepsa_regression_within_task import _filter_multi_policy

    d = _prep_like_baseline(df)
    rows: list[tuple[str, float, float, float]] = []

    d2 = d[d["quality_score"].notna() & np.isfinite(d["log_tokens"])].copy()
    d2 = d2[pd.to_numeric(d2["quality_score"], errors="coerce") > 0]
    d2 = _drop_sparse_categories(d2, "tepsa_sector", min_cell)
    if len(d2) >= 15 and d2["tepsa_sector"].nunique() >= 2:
        res2, _ = _fit_ols_robust("quality_score ~ log_tokens + C(tepsa_sector)", d2, "M2")
        se = float(res2.bse["log_tokens"])
        c = float(res2.params["log_tokens"])
        rows.append(("M2 基线（扇区 FE）", c, c - 1.96 * se, c + 1.96 * se))

    d3 = d[np.isfinite(d["log_tokens"]) & d["value_score_reg"].notna()].copy()
    d3 = _drop_sparse_categories(d3, "policy_id", min_cell)
    if len(d3) >= 15 and d3["policy_id"].nunique() >= 2:
        res3, _ = _fit_ols_robust("value_score_reg ~ log_tokens + C(policy_id)", d3, "M3")
        se = float(res3.bse["log_tokens"])
        c = float(res3.params["log_tokens"])
        rows.append(("M3 基线（策略 FE）", c, c - 1.96 * se, c + 1.96 * se))

    if "task_id" not in d.columns:
        print("[extended] Skip within-task forest: no task_id.")
    else:
        df_w, _ = _filter_multi_policy(d, min_policies_per_task)
        d2w = df_w[df_w["quality_score"].notna() & np.isfinite(df_w["log_tokens"])].copy()
        d2w = d2w[pd.to_numeric(d2w["quality_score"], errors="coerce") > 0]
        if len(d2w) >= 20 and d2w["task_id"].nunique() >= 2:
            res2w, _ = _fit_ols_robust("quality_score ~ log_tokens + C(task_id)", d2w, "M2w")
            se = float(res2w.bse["log_tokens"])
            c = float(res2w.params["log_tokens"])
            rows.append(("M2w Within-task（任务 FE）", c, c - 1.96 * se, c + 1.96 * se))

        d3w = df_w[np.isfinite(df_w["log_tokens"]) & df_w["value_score_reg"].notna()].copy()
        d3w = _drop_sparse_categories(d3w, "policy_id", min_cell)
        if len(d3w) >= 20 and d3w["policy_id"].nunique() >= 2 and d3w["task_id"].nunique() >= 2:
            res3w, _ = _fit_ols_robust(
                "value_score_reg ~ log_tokens + C(task_id) + C(policy_id)",
                d3w,
                "M3w",
            )
            se = float(res3w.bse["log_tokens"])
            c = float(res3w.params["log_tokens"])
            rows.append(("M3w Within-task（任务+策略 FE）", c, c - 1.96 * se, c + 1.96 * se))

    if not rows:
        print("[extended] Skip log_tokens forest: no models fitted.")
        return False

    fig, ax = plt.subplots(figsize=(8, max(3.0, 0.9 * len(rows))))
    y_pos = np.arange(len(rows))
    for i, (_lab, coef, lo, hi) in enumerate(rows):
        ax.plot([lo, hi], [i, i], color="#424242", lw=2, solid_capstyle="round")
        ax.scatter([coef], [i], zorder=3, s=55, c="#1565c0", edgecolors="white", linewidths=1)
    ax.axvline(0.0, color="#bdbdbd", linestyle="--", lw=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("log_tokens 系数（OLS，HC1；95% 区间）")
    ax.set_title("基线 vs Within-task：log_tokens 系数森林图", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_policy_sector_quality_heatmap(df: pd.DataFrame, out: Path, min_n_cell: int = 3) -> bool:
    d = df.copy()
    d["quality_score"] = pd.to_numeric(d["quality_score"], errors="coerce")
    d["policy_id"] = d["policy_id"].astype(str).str.strip()
    d["tepsa_sector"] = d["tepsa_sector"].astype(str).str.strip()
    sub = d[d["quality_score"].notna() & (d["quality_score"] > 0)]
    if sub.empty:
        print("[extended] Skip policy×sector heatmap: no quality rows.")
        return False
    g = sub.groupby(["policy_id", "tepsa_sector"], observed=True)
    mean_q = g["quality_score"].mean().unstack(fill_value=np.nan)
    cnt = g.size().unstack(fill_value=0)
    pols = sorted(mean_q.index.tolist())
    secs = sorted(mean_q.columns.tolist())
    mean_q = mean_q.reindex(index=pols, columns=secs)
    cnt = cnt.reindex(index=pols, columns=secs)
    Z = mean_q.to_numpy(dtype=float)
    Cn = cnt.to_numpy(dtype=float)
    Z = np.where(Cn >= min_n_cell, Z, np.nan)
    if np.all(np.isnan(Z)):
        print("[extended] Skip heatmap: all cells below min_n_cell.")
        return False
    fig, ax = plt.subplots(figsize=(max(8.0, 0.45 * len(secs) + 4), max(5.0, 0.35 * len(pols) + 2)))
    im = ax.imshow(Z, aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax.set_xticks(np.arange(len(secs)))
    ax.set_yticks(np.arange(len(pols)))
    ax.set_xticklabels(secs, rotation=35, ha="right", fontsize=8)
    ax.set_yticklabels(pols, fontsize=8)
    for i in range(len(pols)):
        for j in range(len(secs)):
            if np.isfinite(Z[i, j]):
                ax.text(
                    j,
                    i,
                    f"{Z[i, j]:.2f}\n(n={int(Cn[i, j])})",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="black",
                )
    fig.colorbar(im, ax=ax, label="mean quality_score")
    ax.set_title(
        f"policy × tepsa_sector 平均质量（quality>0；格内 n≥{min_n_cell}）",
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_within_task_policy_count_hist(
    df: pd.DataFrame,
    out: Path,
    min_policies_per_task: int,
) -> bool:
    if "task_id" not in df.columns or "policy_id" not in df.columns:
        print("[extended] Skip within-task policy count hist: missing task_id or policy_id.")
        return False
    tid = df["task_id"].astype(str).str.strip()
    pid = df["policy_id"].astype(str).str.strip()
    g = pd.DataFrame({"task_id": tid, "policy_id": pid}).groupby("task_id")["policy_id"].nunique()
    n_tasks = int(len(g))
    if n_tasks == 0:
        print("[extended] Skip within-task hist: no tasks.")
        return False
    kept = int((g >= min_policies_per_task).sum())
    ret_rows = 0
    keep_set = set(g[g >= min_policies_per_task].index)
    for t in keep_set:
        ret_rows += int((tid == t).sum())
    n_rows = int(len(df))
    pct_tasks = 100.0 * kept / n_tasks
    pct_rows = 100.0 * ret_rows / max(n_rows, 1)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    vals = g.to_numpy()
    max_k = int(vals.max())
    bins = np.arange(0.5, max_k + 1.5, 1.0)
    ax.hist(vals, bins=bins, color="#5c6bc0", edgecolor="white", alpha=0.88)
    ax.axvline(min_policies_per_task, color="#c62828", lw=2, label=f"阈值 ≥{min_policies_per_task} 策略/任务")
    ax.set_xlabel("每任务不同 policy_id 个数")
    ax.set_ylabel("任务数")
    ax.set_title(
        f"Within-task 样本构造：每任务策略数分布（任务 {n_tasks}；≥阈值 {kept}，{pct_tasks:.1f}%）",
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=8)
    fig.text(
        0.5,
        0.01,
        f"行保留（粗略）：{ret_rows}/{n_rows} ≈ {pct_rows:.1f}%（与 within-task 回归筛选一致时需同 run_id）",
        ha="center",
        fontsize=8,
        color="#424242",
    )
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.14)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def run_extended_figures(
    input_csv: Path,
    out_dir: Path,
    run_id: str,
    suffix: str,
    *,
    treat_policy: str,
    ipw_clip: float,
    ipw_outcome: str,
    min_cell: int,
    min_policies_per_task: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = load_obs(input_csv, run_id or None)
    if df.empty:
        raise SystemExit("No rows after filter; check --run-id or --input.")

    fig_propensity_overlap(
        input_csv,
        run_id,
        out_dir / f"fig_propensity_overlap{suffix}.png",
        treat_policy,
        ipw_clip,
        ipw_outcome,
    )
    fig_m1_logcost_fitted_vs_actual(df, out_dir / f"fig_m1_logcost_fitted_vs_actual{suffix}.png", min_cell)
    fig_coef_log_tokens_forest(
        df,
        out_dir / f"fig_coef_log_tokens_forest{suffix}.png",
        min_cell,
        min_policies_per_task,
    )
    fig_policy_sector_quality_heatmap(df, out_dir / f"fig_policy_sector_quality_heatmap{suffix}.png")
    fig_within_task_policy_count_hist(
        df,
        out_dir / f"fig_within_task_policy_count_hist{suffix}.png",
        min_policies_per_task,
    )
    print(f"[extended] Wrote extended figures to {out_dir} (suffix={suffix!r})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--run-id", default="", help="Filter e.g. ds_batch for cleaner main analysis.")
    ap.add_argument(
        "--policy-min-n-box",
        type=int,
        default=5,
        help="fig_cost_by_policy: draw boxplot only when policy has at least this many non-null cost rows.",
    )
    ap.add_argument(
        "--extended",
        action="store_true",
        help="Also write IPW overlap, M1 diagnostic, coef forest, heatmap, within-task hist (needs statsmodels).",
    )
    ap.add_argument("--treat-policy", default="pl_deepseek_pro", help="IPW / overlap figure: T=1 policy_id.")
    ap.add_argument("--ipw-clip", type=float, default=0.05, help="Propensity clipping for overlap figure.")
    ap.add_argument(
        "--ipw-outcome",
        choices=("quality", "value"),
        default="quality",
        help="Outcome used for IPW sample construction in overlap figure (same as tepsa_regression_ipw).",
    )
    ap.add_argument(
        "--min-cell",
        type=int,
        default=5,
        help="Min rows per FE category for extended M1/forest (align with regression scripts).",
    )
    ap.add_argument(
        "--min-policies-per-task",
        type=int,
        default=2,
        help="Within-task threshold for forest + policy-count histogram.",
    )
    args = ap.parse_args()

    _set_cn_font()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = load_obs(args.input, args.run_id or None)
    if df.empty:
        raise SystemExit("No rows after filter; check --run-id or --input.")

    suffix = f"_{args.run_id.strip()}" if args.run_id.strip() else "_allruns"

    fig_schematic_shrinkage(args.out_dir / "fig01_schematic_national_to_mvp.png")
    fig_schematic_data_pipeline(args.out_dir / "fig03_schematic_data_to_dashboard.png")
    fig_run_id_counts(df, args.out_dir / f"fig_run_id_counts{suffix}.png")
    fig_cost_by_policy(
        df,
        args.out_dir / f"fig_cost_by_policy{suffix}.png",
        min_n_box=args.policy_min_n_box,
    )
    fig_tokens_total_hist(df, args.out_dir / f"fig_tokens_hist{suffix}.png")
    fig_cost_vs_tokens(df, args.out_dir / f"fig_cost_vs_tokens{suffix}.png")
    fig_latency_by_provider(df, args.out_dir / f"fig_latency_by_provider{suffix}.png")
    fig_sector_median_cost(df, args.out_dir / f"fig_sector_structure{suffix}.png")
    fig_quality_vs_tokens(df, args.out_dir / f"fig02_token_quality_scatter{suffix}.png")
    fig_risk_welfare_frontier(df, args.out_dir / f"fig04_risk_welfare_scatter{suffix}.png")

    print(f"Wrote figures to {args.out_dir} (n={len(df)} rows, suffix={suffix!r})")

    if args.extended:
        run_extended_figures(
            args.input,
            args.out_dir,
            args.run_id,
            suffix,
            treat_policy=args.treat_policy,
            ipw_clip=args.ipw_clip,
            ipw_outcome=args.ipw_outcome,
            min_cell=args.min_cell,
            min_policies_per_task=args.min_policies_per_task,
        )


if __name__ == "__main__":
    main()
