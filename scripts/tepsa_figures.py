
"""
Generate competition-style figures from obs_macro_preview.csv (or enriched).

  pip install -r requirements-viz.txt
  python scripts/tepsa_figures.py
  python scripts/tepsa_figures.py --run-id ds_batch

Outputs PNG under output/figures/ (300 dpi).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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


if __name__ == "__main__":
    main()
