
"""
Generate competition-style figures from obs_macro_preview.csv (or enriched).

  pip install -r requirements-viz.txt
  python scripts/tepsa_figures.py
  python scripts/tepsa_figures.py --run-id ds_batch
  python scripts/tepsa_figures.py --extended
  python scripts/tepsa_figures.py --extended --run-id ds_batch

Outputs PNG under output/figures/ (300 dpi).
`--extended` 另含 IPW/回归诊断及一批「全量诊断图」（附录/答辩可选用）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.graphics.gofplots import qqplot

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "data" / "tessa_psa" / "obs_macro_preview.csv"
OUT_DIR = REPO_ROOT / "output" / "figures"

# 扩展诊断图统一色板（与现有图协调）
EXT_BLUE = "#1565c0"
EXT_RED = "#c62828"
EXT_TEAL = "#00897b"
EXT_INDIGO = "#3949ab"
EXT_PURPLE = "#6a1b9a"
EXT_BOX_FACE = "#e3f2fd"
EXT_BOX_EDGE = "#1565c0"
TAB10 = plt.cm.tab10(np.linspace(0, 0.9, 10))


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


def _apply_extended_style() -> None:
    """略增大字号与线宽，供 `--extended` 整批图统一观感。"""
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "lines.linewidth": 1.4,
            "axes.linewidth": 1.0,
        }
    )


def _provider_color_map(labels: pd.Series) -> dict[str, tuple]:
    u = sorted(labels.fillna("unknown").astype(str).unique())
    return {p: tuple(TAB10[i % len(TAB10)]) for i, p in enumerate(u)}


def _subsample_mask(n: int, max_n: int = 5000, seed: int = 0) -> np.ndarray:
    if n <= max_n:
        return np.ones(n, dtype=bool)
    rng = np.random.default_rng(seed)
    idx = rng.choice(n, size=max_n, replace=False)
    m = np.zeros(n, dtype=bool)
    m[idx] = True
    return m


def _m1_sample_and_result(
    df: pd.DataFrame, min_cell: int
) -> tuple[pd.DataFrame, object] | tuple[None, None]:
    _ensure_src_on_path()
    from tepsa_regression_baseline import _drop_sparse_categories

    d = _prep_like_baseline(df)
    d1 = d[np.isfinite(d["log_cost"]) & np.isfinite(d["log_tokens"])].copy()
    d1 = _drop_sparse_categories(d1, "policy_id", min_cell)
    if len(d1) < 20 or d1["policy_id"].nunique() < 2:
        return None, None
    res = smf.ols("log_cost ~ log_tokens + C(policy_id)", data=d1).fit(cov_type="HC1")
    return d1, res


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
    d1, res = _m1_sample_and_result(df, min_cell)
    if d1 is None or res is None:
        print("[extended] Skip M1 fitted vs actual: insufficient rows or policy levels.")
        return False
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


def fig_m1_residual_diagnostics(df: pd.DataFrame, out: Path, min_cell: int) -> bool:
    d1, res = _m1_sample_and_result(df, min_cell)
    if d1 is None or res is None:
        print("[extended] Skip M1 residual diagnostics: insufficient M1 sample.")
        return False
    r = np.asarray(res.resid, dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6))
    axes[0].hist(r, bins=36, color=EXT_BLUE, edgecolor="white", alpha=0.88)
    axes[0].set_xlabel("残差（log 成本）")
    axes[0].set_ylabel("频数")
    axes[0].set_title("M1 log 残差分布", fontweight="bold")
    qqplot(
        pd.Series(r),
        line="45",
        ax=axes[1],
        fit=False,
        markerfacecolor=EXT_TEAL,
        markeredgecolor="white",
        alpha=0.75,
    )
    axes[1].set_title("正态 QQ（对照残差形态）", fontweight="bold")
    fig.suptitle(f"M1：`log_cost ~ log_tokens + C(policy_id)`，N={int(res.nobs)}", fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_m1_cost_rel_error_hist(df: pd.DataFrame, out: Path, min_cell: int) -> bool:
    d1, res = _m1_sample_and_result(df, min_cell)
    if d1 is None or res is None:
        print("[extended] Skip M1 cost rel error hist: insufficient M1 sample.")
        return False
    y = np.asarray(res.model.endog, dtype=float)
    fh = np.asarray(res.fittedvalues, dtype=float)
    eps = 1e-12
    c_act = np.exp(y) - eps
    c_hat = np.exp(fh) - eps
    rel = np.abs(c_hat - c_act) / np.maximum(c_act, eps)
    rel = rel[np.isfinite(rel)]
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    upper = float(np.clip(np.nanpercentile(rel, 99), 0.05, 1.0))
    ax.hist(np.minimum(rel, upper), bins=40, color=EXT_PURPLE, edgecolor="white", alpha=0.88)
    ax.set_xlabel(f"美元成本相对误差 |ĉ−c|/c（截断至 99% 分位 ≈{upper:.4f} 以抑制极端尾）")
    ax.set_ylabel("频数")
    ax.set_title("M1 价目核对：相对误差分布", fontweight="bold")
    fig.text(0.5, 0.02, f"中位数相对误差={float(np.median(rel)):.4f}；N={int(res.nobs)}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.14)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_cost_per_token_by_policy(df: pd.DataFrame, out: Path, min_n_box: int = 3) -> bool:
    d = df.copy()
    d["cost_usd"] = pd.to_numeric(d["cost_usd"], errors="coerce")
    tin = pd.to_numeric(d["input_tokens"], errors="coerce").fillna(0)
    tout = pd.to_numeric(d["output_tokens"], errors="coerce").fillna(0)
    d["tokens_total"] = tin + tout
    d["cpt"] = d["cost_usd"] / (d["tokens_total"] + 1.0)
    d = d[d["cost_usd"].notna() & np.isfinite(d["cpt"]) & (d["cpt"] >= 0)]
    pol_col = "policy_id"
    policies = sorted(d[pol_col].dropna().astype(str).unique())
    if not policies:
        print("[extended] Skip cost/token by policy: no rows.")
        return False
    min_n_box = max(2, int(min_n_box))
    pos = np.arange(1, len(policies) + 1, dtype=int)
    box_data: list[np.ndarray] = []
    box_positions: list[int] = []
    low_x: list[int] = []
    low_y: list[float] = []
    counts: dict[str, int] = {}
    for i, p in zip(pos, policies):
        sub = d.loc[d[pol_col] == p, "cpt"].dropna().to_numpy(dtype=float)
        counts[p] = len(sub)
        if len(sub) >= min_n_box:
            box_data.append(sub)
            box_positions.append(int(i))
        elif len(sub) > 0:
            low_x.extend([int(i)] * len(sub))
            low_y.extend(sub.tolist())

    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    if box_data:
        bp = ax.boxplot(
            box_data,
            positions=box_positions,
            widths=0.55,
            showfliers=True,
            patch_artist=True,
        )
        for b in bp.get("boxes", ()) or []:
            b.set_facecolor(EXT_BOX_FACE)
            b.set_edgecolor(EXT_BOX_EDGE)
            b.set_alpha(0.92)
    if low_x:
        ax.scatter(
            low_x,
            low_y,
            s=85,
            c=EXT_RED,
            marker="D",
            zorder=5,
            edgecolors="white",
            linewidths=1.0,
            label=f"n<{min_n_box}（仅点）",
        )
    ax.set_xticks(list(pos))
    ax.set_xticklabels([f"{p}\n(n={counts[p]})" for p in policies], rotation=32, ha="right", fontsize=8)
    ax.set_ylabel("cost_usd / (tokens_total+1)")
    ax.set_title("单位 Token 成本（近似）按 policy_id", fontweight="bold")
    if low_x:
        ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, axis="y", alpha=0.35)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_latency_cost_and_tokens(df: pd.DataFrame, out: Path) -> bool:
    if "latency_sec" not in df.columns:
        print("[extended] Skip latency scatter: no latency_sec.")
        return False
    d = df.copy()
    d["latency_sec"] = pd.to_numeric(d["latency_sec"], errors="coerce")
    d["cost_usd"] = pd.to_numeric(d["cost_usd"], errors="coerce")
    d["tokens_total"] = pd.to_numeric(d["input_tokens"], errors="coerce").fillna(0) + pd.to_numeric(
        d["output_tokens"], errors="coerce"
    ).fillna(0)
    d = d[d["latency_sec"].notna() & np.isfinite(d["latency_sec"])]
    if d.empty:
        print("[extended] Skip latency scatter: no valid latency.")
        return False
    prov = d["provider"].fillna("unknown").astype(str) if "provider" in d.columns else pd.Series(["unknown"] * len(d))
    cmap = _provider_color_map(prov)
    colors = prov.map(lambda x: cmap.get(x, (0.5, 0.5, 0.5, 1.0)))
    m = _subsample_mask(len(d), 5000)
    d = d.loc[m].reset_index(drop=True)
    prov = prov.loc[m].reset_index(drop=True)
    colors = prov.map(lambda x: cmap.get(x, (0.5, 0.5, 0.5, 1.0)))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].scatter(d["cost_usd"], d["latency_sec"], s=14, alpha=0.55, c=colors.tolist())
    axes[0].set_xlabel("cost_usd")
    axes[0].set_ylabel("latency_sec")
    axes[0].set_title("延迟 — 成本", fontweight="bold")
    axes[1].scatter(d["tokens_total"], d["latency_sec"], s=14, alpha=0.55, c=colors.tolist())
    axes[1].set_xlabel("tokens_total")
    axes[1].set_ylabel("latency_sec")
    axes[1].set_title("延迟 — Token", fontweight="bold")
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=cmap[p], markersize=8, label=p)
        for p in sorted(cmap.keys())[:12]
    ]
    if len(cmap) > 12:
        handles.append(plt.Line2D([0], [0], linestyle="none", label="…"))
    fig.legend(handles=handles, loc="upper center", ncol=min(6, len(handles)), bbox_to_anchor=(0.5, 1.12), fontsize=7)
    fig.suptitle("延迟与成本/规模（按 provider 着色）", fontsize=11, y=1.08)
    fig.tight_layout()
    fig.subplots_adjust(top=0.86)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_quality_difficulty_risk_box(df: pd.DataFrame, out: Path, min_per_cat: int = 5) -> bool:
    d = df.copy()
    d["quality_score"] = pd.to_numeric(d["quality_score"], errors="coerce")
    d = d[d["quality_score"].notna() & (d["quality_score"] > 0)]
    if len(d) < 20:
        print("[extended] Skip quality×difficulty/risk: insufficient quality rows.")
        return False
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8))

    def _one_box(ax, col: str, title: str) -> bool:
        if col not in d.columns:
            ax.set_visible(False)
            return False
        sub = d.copy()
        sub[col] = sub[col].astype(str).str.strip()
        vc = sub[col].value_counts()
        keep = vc[vc >= min_per_cat].index
        sub = sub[sub[col].isin(keep)]
        cats = sorted(sub[col].unique())
        if len(cats) < 2:
            ax.text(0.5, 0.5, f"{title}\n类别不足", ha="center", va="center", transform=ax.transAxes)
            return False
        data = [sub.loc[sub[col] == c, "quality_score"].to_numpy(dtype=float) for c in cats]
        try:
            bp = ax.boxplot(data, tick_labels=cats, patch_artist=True, showfliers=True)
        except TypeError:
            bp = ax.boxplot(data, labels=cats, patch_artist=True, showfliers=True)
        for b in bp.get("boxes", ()) or []:
            b.set_facecolor(EXT_BOX_FACE)
            b.set_edgecolor(EXT_BOX_EDGE)
        ax.set_ylabel("quality_score")
        ax.set_title(title, fontweight="bold")
        plt.setp(ax.get_xticklabels(), rotation=22, ha="right")
        return True

    ok1 = _one_box(axes[0], "difficulty_label", "质量 — difficulty_label")
    ok2 = _one_box(axes[1], "risk_class", "质量 — risk_class")
    if not ok1 and not ok2:
        plt.close(fig)
        print("[extended] Skip quality×difficulty/risk: categories too sparse.")
        return False
    fig.suptitle(f"质量分层（quality>0；每类≥{min_per_cat}）", fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_value_score_policy_and_tokens(df: pd.DataFrame, out: Path, min_n_box: int = 3) -> bool:
    d = _prep_like_baseline(df)
    d = d[d["value_score_reg"].notna() & np.isfinite(d["value_score_reg"])]
    tin = pd.to_numeric(d["input_tokens"], errors="coerce").fillna(0)
    tout = pd.to_numeric(d["output_tokens"], errors="coerce").fillna(0)
    d["tokens_total"] = tin + tout
    if len(d) < 15:
        print("[extended] Skip value_score figures: N<15 non-missing.")
        return False
    min_n_box = max(2, int(min_n_box))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    pol_col = "policy_id"
    policies = sorted(d[pol_col].astype(str).str.strip().unique())
    pos = np.arange(1, len(policies) + 1)
    box_data: list[np.ndarray] = []
    box_pos: list[int] = []
    for i, p in zip(pos, policies):
        sub = d.loc[d[pol_col].astype(str).str.strip() == p, "value_score_reg"].dropna().to_numpy(dtype=float)
        if len(sub) >= min_n_box:
            box_data.append(sub)
            box_pos.append(int(i))
    if box_data:
        bp = axes[0].boxplot(box_data, positions=box_pos, widths=0.55, patch_artist=True)
        for b in bp.get("boxes", ()) or []:
            b.set_facecolor("#fff3e0")
            b.set_edgecolor("#ef6c00")
        axes[0].set_xticks(list(pos))
        axes[0].set_xticklabels(policies, rotation=30, ha="right", fontsize=8)
    else:
        axes[0].text(0.5, 0.5, "各 policy n 不足，未画箱线", ha="center", va="center", transform=axes[0].transAxes)
    axes[0].set_ylabel("value_score_reg")
    axes[0].set_title("价值 proxy 按 policy", fontweight="bold")

    prov = d["provider"].fillna("unknown").astype(str) if "provider" in d.columns else pd.Series(["unknown"] * len(d))
    cmap = _provider_color_map(prov)
    colors = prov.map(lambda x: cmap.get(x, (0.5, 0.5, 0.5, 1.0)))
    m = _subsample_mask(len(d), 5000)
    axes[1].scatter(
        d["tokens_total"].to_numpy()[m],
        d["value_score_reg"].to_numpy()[m],
        s=16,
        alpha=0.55,
        c=colors[m].tolist(),
    )
    axes[1].set_xlabel("tokens_total")
    axes[1].set_ylabel("value_score_reg")
    axes[1].set_title("价值 proxy — Token（provider 色）", fontweight="bold")
    fig.suptitle(f"综合价值 proxy（N={len(d)}）", fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_within_retention_sector_share(
    df: pd.DataFrame,
    out: Path,
    min_policies_per_task: int,
) -> bool:
    if "task_id" not in df.columns:
        print("[extended] Skip within retention sector: no task_id.")
        return False
    _ensure_src_on_path()
    from tepsa_regression_within_task import _filter_multi_policy

    d = _prep_like_baseline(df)
    df_w, meta = _filter_multi_policy(d, min_policies_per_task)
    if meta["n_rows_after"] == 0:
        print("[extended] Skip within retention sector: no multi-policy tasks.")
        return False
    sec = "tepsa_sector"
    if sec not in d.columns:
        print("[extended] Skip within retention sector: no tepsa_sector.")
        return False
    full_c = d.groupby(sec, dropna=False).size()
    kept_c = df_w.groupby(sec, dropna=False).size()
    sectors = sorted(set(full_c.index.astype(str)) | set(kept_c.index.astype(str)))
    p_full = np.array([full_c.get(s, 0) / max(len(d), 1) for s in sectors], dtype=float)
    p_kept = np.array([kept_c.get(s, 0) / max(len(df_w), 1) for s in sectors], dtype=float)
    x = np.arange(len(sectors))
    w = 0.36
    fig, ax = plt.subplots(figsize=(max(9, 0.35 * len(sectors) + 5), 5))
    ax.bar(x - w / 2, p_full, width=w, label="全样本（行占比）", color=EXT_INDIGO, alpha=0.85, edgecolor="white")
    ax.bar(x + w / 2, p_kept, width=w, label="Within 保留（行占比）", color=EXT_TEAL, alpha=0.85, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(sectors, rotation=28, ha="right", fontsize=8)
    ax.set_ylabel("占各自总行数比例")
    ax.set_title("Within-task 筛选前后：扇区行占比对照", fontweight="bold")
    ax.legend(loc="upper right")
    fig.text(
        0.5,
        0.02,
        f"保留行 {meta['n_rows_after']}/{meta['n_rows_before']}；≥{min_policies_per_task} 策略/任务",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.18)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_ipw_weight_distribution(
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
        print(f"[extended] Skip IPW weight distribution: {e}")
        return False
    p = np.asarray(dz["pscore"], dtype=float)
    t = np.asarray(dz["T"], dtype=int)
    w1 = 1.0 / p[t == 1]
    w0 = 1.0 / (1.0 - p[t == 0])
    lw1 = np.log10(np.clip(w1, 1e-12, None))
    lw0 = np.log10(np.clip(w0, 1e-12, None))
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    bins = 32
    ax.hist(lw1, bins=bins, alpha=0.6, color=EXT_RED, label=f"T=1：log10(1/p)，n={len(w1)}", density=True)
    ax.hist(lw0, bins=bins, alpha=0.55, color=EXT_INDIGO, label=f"T=0：log10(1/(1−p))，n={len(w0)}", density=True)
    ax.set_xlabel("log10(IPW 权重)")
    ax.set_ylabel("密度")
    ax.set_title("IPW 权重分布（Hajek 形式；敏感性对照）", fontweight="bold")
    ax.legend(loc="upper right", fontsize=9)
    fig.text(0.5, 0.02, f"p 裁剪 [{clip}, {1 - clip}]；policy(T=1)={treat_policy}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.14)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return True


def fig_macro_wage_vs_sector_median_cost(df: pd.DataFrame, out: Path) -> bool:
    if "macro_avg_annual_wage_cny" not in df.columns or "tepsa_sector" not in df.columns:
        print("[extended] Skip macro wage vs cost: missing columns.")
        return False
    d = df.copy()
    d["cost_usd"] = pd.to_numeric(d["cost_usd"], errors="coerce")
    d["wage"] = pd.to_numeric(d["macro_avg_annual_wage_cny"], errors="coerce")
    d["tepsa_sector"] = d["tepsa_sector"].astype(str).str.strip()
    rows = []
    for s, g in d.groupby("tepsa_sector"):
        wvals = g["wage"].dropna()
        cvals = g["cost_usd"].dropna()
        if wvals.empty or cvals.empty:
            continue
        rows.append((str(s), float(wvals.iloc[0]), float(cvals.median())))
    if len(rows) < 2:
        print("[extended] Skip macro scatter: insufficient sector points.")
        return False
    sectors, wages, med_cost = zip(*rows)
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.scatter(wages, med_cost, s=120, c=EXT_BLUE, edgecolors="white", linewidths=1.2, alpha=0.88, zorder=3)
    for w, c, s in zip(wages, med_cost, sectors):
        short = s.replace("enterprise_support", "ent_sup")[:16]
        ax.annotate(short, (w, c), textcoords="offset points", xytext=(4, 4), fontsize=8, alpha=0.9)
    ax.set_xlabel("macro_avg_annual_wage_cny（扇区首行非空）")
    ax.set_ylabel("cost_usd 中位数（观测）")
    ax.set_title("宏观工资锚 vs 扇区观测成本中位数（描述性）", fontweight="bold")
    fig.text(0.5, 0.02, "非因果：扇区层面聚合；注意生态学谬误", ha="center", fontsize=8, color="#616161")
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.12)
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
    _apply_extended_style()
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
    fig_m1_residual_diagnostics(df, out_dir / f"fig_m1_residual_diagnostics{suffix}.png", min_cell)
    fig_m1_cost_rel_error_hist(df, out_dir / f"fig_m1_cost_rel_error_hist{suffix}.png", min_cell)
    fig_cost_per_token_by_policy(df, out_dir / f"fig_cost_per_token_by_policy{suffix}.png")
    fig_latency_cost_and_tokens(df, out_dir / f"fig_latency_cost_and_tokens{suffix}.png")
    fig_quality_difficulty_risk_box(df, out_dir / f"fig_quality_difficulty_risk_box{suffix}.png")
    fig_value_score_policy_and_tokens(df, out_dir / f"fig_value_score_policy_and_tokens{suffix}.png")
    fig_within_retention_sector_share(
        df,
        out_dir / f"fig_within_retention_sector_share{suffix}.png",
        min_policies_per_task,
    )
    fig_ipw_weight_distribution(
        input_csv,
        run_id,
        out_dir / f"fig_ipw_weight_distribution{suffix}.png",
        treat_policy,
        ipw_clip,
        ipw_outcome,
    )
    fig_macro_wage_vs_sector_median_cost(df, out_dir / f"fig_macro_wage_vs_sector_median_cost{suffix}.png")
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
        help=(
            "Also write extended diagnostics: IPW overlap, M1, forest, heatmap, within hist, "
            "M1 residual/rel-error, cost/token, latency scatters, quality boxes, value proxy, "
            "within sector retention, IPW weights, macro wage vs cost (needs statsmodels)."
        ),
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
