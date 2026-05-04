"""
Left-join human_labels onto task_policy_observations_enriched.csv (stdlib).

Run from repo root:
  python src/tepsa_merge_labels.py
  python src/tepsa_merge_labels.py --obs data/tessa_psa/task_policy_observations_enriched.csv
  python src/tepsa_merge_labels.py --export-queue data/tessa_psa/label_queue_ds_batch.csv --filter-run-id ds_batch

Smoke-test merge with a few label rows (local only, do not commit secrets):
  append rows to human_labels.csv, re-run this script, check non-empty label columns.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "tessa_psa"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = list(r)
        return list(r.fieldnames or []), rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def raw_key(row: dict[str, str]) -> tuple[str, str, str]:
    """观测表 join 键：与 CSV 中 run_id 一致（不做别名改写）。"""
    return (
        (row.get("task_id") or "").strip(),
        (row.get("policy_id") or "").strip(),
        (row.get("run_id") or "").strip(),
    )


# GLM 评测导出曾使用 glm_batch_v3 / v4 / final，与主表 run_id=glm_batch 不一致；合并前对齐。
_GLM_RUN_ALIASES = frozenset({"glm_batch_v3", "glm_batch_v4", "glm_batch_final"})


def normalize_label_run_id(run_id: str) -> str:
    r = (run_id or "").strip()
    if r in _GLM_RUN_ALIASES:
        return "glm_batch"
    return r


def label_join_key(row: dict[str, str], *, normalize_glm_run: bool) -> tuple[str, str, str]:
    t, p, rid = raw_key(row)
    if normalize_glm_run:
        rid = normalize_label_run_id(rid)
    return (t, p, rid)


def main() -> None:
    ap = argparse.ArgumentParser(description="Merge human_labels into enriched observations (left join).")
    ap.add_argument(
        "--obs",
        type=Path,
        default=DATA_DIR / "task_policy_observations_enriched.csv",
        help="Left table (default: enriched observations).",
    )
    ap.add_argument(
        "--labels",
        type=Path,
        default=DATA_DIR / "human_labels.csv",
        help="Human labels CSV (may be header-only).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=DATA_DIR / "task_policy_observations_with_labels.csv",
        help="Output merged CSV.",
    )
    ap.add_argument(
        "--export-queue",
        type=Path,
        default=None,
        help="If set, write task_id,policy_id,run_id,response_path for labeling (no merge).",
    )
    ap.add_argument(
        "--filter-run-id",
        default="",
        help="With --export-queue: keep only rows with this run_id.",
    )
    ap.add_argument(
        "--no-normalize-glm-run-id",
        action="store_true",
        help="Do not map glm_batch_v3/v4/final -> glm_batch on label keys (default: normalize).",
    )
    args = ap.parse_args()

    obs_fields, obs_rows = read_csv(args.obs)
    obs_rows = [r for r in obs_rows if any((v or "").strip() for v in r.values())]
    if not obs_fields:
        raise SystemExit(f"Missing or empty header: {args.obs}")

    if args.export_queue is not None:
        run_filter = (args.filter_run_id or "").strip()
        seen: set[tuple[str, str, str]] = set()
        queue_rows: list[dict[str, str]] = []
        for r in obs_rows:
            if run_filter and (r.get("run_id") or "").strip() != run_filter:
                continue
            k = raw_key(r)
            if not all(k) or k in seen:
                continue
            seen.add(k)
            queue_rows.append(
                {
                    "task_id": k[0],
                    "policy_id": k[1],
                    "run_id": k[2],
                    "response_path": (r.get("response_path") or "").strip(),
                }
            )
        qfields = ["task_id", "policy_id", "run_id", "response_path"]
        write_csv(args.export_queue, qfields, queue_rows)
        print(f"Wrote label queue {args.export_queue} ({len(queue_rows)} unique keys).")
        return

    lbl_fields, lbl_rows = read_csv(args.labels)
    lbl_rows = [r for r in lbl_rows if any((v or "").strip() for v in r.values())]

    join_keys = ("task_id", "policy_id", "run_id")
    norm_glm = not args.no_normalize_glm_run_id
    label_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for r in lbl_rows:
        lr = dict(r)
        k = label_join_key(lr, normalize_glm_run=norm_glm)
        if not all(k):
            continue
        label_by_key[k] = {a: (lr.get(a) or "").strip() for a in lbl_fields}

    label_only = [c for c in lbl_fields if c not in join_keys]
    out_fields = list(obs_fields)
    for c in label_only:
        if c not in out_fields:
            out_fields.append(c)

    merged: list[dict[str, object]] = []
    for r in obs_rows:
        out = dict(r)
        k = raw_key(r)
        lab = label_by_key.get(k)
        if lab:
            for c in label_only:
                out[c] = lab.get(c, "")
        merged.append(out)

    write_csv(args.out, out_fields, merged)
    n_matched = sum(1 for r in merged if raw_key(r) in label_by_key)
    print(f"Wrote {args.out} rows={len(merged)} label_keys_in_file={len(label_by_key)} matched_rows={n_matched}")


if __name__ == "__main__":
    main()
