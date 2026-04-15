"""
Fetch raw job-posting data and export jobs_micro_raw.csv.

Current sources:
- The Muse public API (supports pagination, large history)
- RemoteOK public JSON feed

Output columns:
- job_id, platform, crawl_date, city, industry, company_name,
  job_title, salary_min, salary_max, salary_unit,
  exp_req, edu_req, job_type, job_description_raw, job_url, post_date
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests


REMOTEOK_API = "https://remoteok.com/api"
THEMUSE_API = "https://www.themuse.com/api/public/jobs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch raw job postings and save jobs_micro_raw.csv")
    parser.add_argument("--out", default="data/raw/jobs/jobs_micro_raw.csv", help="Output CSV path")
    parser.add_argument(
        "--min-date",
        default=None,
        help="Optional ISO date filter (YYYY-MM-DD), keep jobs with date >= min-date",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=365,
        help="If --min-date not set, use today - lookback_days (default: 365).",
    )
    parser.add_argument(
        "--max-pages-themuse",
        type=int,
        default=200,
        help="Max pages to request from The Muse API (default: 200).",
    )
    parser.add_argument(
        "--sources",
        default="themuse,remoteok",
        help="Comma-separated sources: themuse,remoteok (default both).",
    )
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout (seconds)")
    return parser.parse_args()


def _parse_salary_range(text: str) -> Tuple[float | None, float | None, str]:
    """
    Parse coarse salary from free text.
    RemoteOK salary formats vary (e.g. "$60k - $120k", "€80,000").
    We keep a best-effort numeric range and unit label.
    """
    if not text:
        return None, None, ""

    s = str(text).lower().replace(",", "")
    unit = "year"
    if "month" in s or "/mo" in s:
        unit = "month"
    elif "hour" in s or "/hr" in s:
        unit = "hour"

    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if not nums:
        return None, None, unit

    vals = [float(x) for x in nums]
    if "k" in s:
        vals = [v * 1000 for v in vals]

    if len(vals) == 1:
        return vals[0], vals[0], unit
    return min(vals), max(vals), unit


def _pick_city(loc: str) -> str:
    if not loc:
        return ""
    # Best-effort split for values like "Worldwide", "Berlin, Germany", etc.
    return str(loc).split(",")[0].strip()


def fetch_remoteok_jobs(timeout: int = 30) -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0; +https://github.com/Sparky2076/satistical_modeling)"
    }
    resp = requests.get(REMOTEOK_API, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # First item is usually metadata, remaining items are jobs.
    jobs = [x for x in data if isinstance(x, dict) and x.get("id")]
    return jobs


def fetch_themuse_jobs(timeout: int = 30, max_pages: int = 200) -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0; +https://github.com/Sparky2076/satistical_modeling)"
    }
    all_jobs: List[Dict[str, Any]] = []
    page = 1
    while page <= max_pages:
        resp = requests.get(THEMUSE_API, headers=headers, params={"page": page}, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
        results = payload.get("results", [])
        if not results:
            break
        all_jobs.extend(results)

        page_count = int(payload.get("page_count", page))
        if page >= page_count:
            break
        page += 1
    return all_jobs


def remoteok_to_rows(jobs: List[Dict[str, Any]], crawl_date: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for j in jobs:
        salary_min, salary_max, salary_unit = _parse_salary_range(j.get("salary") or "")
        tags = j.get("tags") or []
        if isinstance(tags, list):
            industry = "|".join([str(t) for t in tags[:5]])
        else:
            industry = str(tags)

        rows.append(
            {
                "job_id": str(j.get("id", "")),
                "platform": "remoteok",
                "crawl_date": crawl_date,
                "city": _pick_city(j.get("location") or ""),
                "industry": industry,
                "company_name": str(j.get("company") or ""),
                "job_title": str(j.get("position") or ""),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_unit": salary_unit,
                "exp_req": "",
                "edu_req": "",
                "job_type": str(j.get("employment_type") or ""),
                "job_description_raw": str(j.get("description") or ""),
                "job_url": str(j.get("url") or ""),
                "post_date": str(j.get("date") or ""),
            }
        )
    return rows


def themuse_to_rows(jobs: List[Dict[str, Any]], crawl_date: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for j in jobs:
        locations = j.get("locations") or []
        cats = j.get("categories") or []
        levels = j.get("levels") or []

        city = ""
        if isinstance(locations, list) and locations:
            city = str(locations[0].get("name", ""))
        industry = "|".join([str(c.get("name", "")) for c in cats[:5]]) if isinstance(cats, list) else ""
        job_type = "|".join([str(l.get("name", "")) for l in levels[:3]]) if isinstance(levels, list) else ""

        refs = j.get("refs") or {}
        landing = refs.get("landing_page") if isinstance(refs, dict) else ""

        rows.append(
            {
                "job_id": str(j.get("id", "")),
                "platform": "themuse",
                "crawl_date": crawl_date,
                "city": city,
                "industry": industry,
                "company_name": str((j.get("company") or {}).get("name", "")),
                "job_title": str(j.get("name", "")),
                "salary_min": None,
                "salary_max": None,
                "salary_unit": "",
                "exp_req": "",
                "edu_req": "",
                "job_type": job_type,
                "job_description_raw": str(j.get("contents", "")),
                "job_url": str(landing or ""),
                "post_date": str(j.get("publication_date", "")),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    crawl_date = dt.datetime.now().strftime("%Y-%m-%d")
    source_set = {s.strip().lower() for s in args.sources.split(",") if s.strip()}

    if args.min_date:
        min_dt = pd.to_datetime(args.min_date, errors="coerce")
        if pd.isna(min_dt):
            raise ValueError("--min-date must be YYYY-MM-DD")
    else:
        min_dt = pd.Timestamp.now().normalize() - pd.Timedelta(days=args.lookback_days)

    rows: List[Dict[str, Any]] = []

    if "themuse" in source_set:
        muse_jobs = fetch_themuse_jobs(timeout=args.timeout, max_pages=args.max_pages_themuse)
        rows.extend(themuse_to_rows(muse_jobs, crawl_date=crawl_date))

    if "remoteok" in source_set:
        ok_jobs = fetch_remoteok_jobs(timeout=args.timeout)
        rows.extend(remoteok_to_rows(ok_jobs, crawl_date=crawl_date))

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No jobs fetched. Check sources and network.")

    post_dt = pd.to_datetime(df["post_date"], errors="coerce", utc=True)
    min_dt_utc = pd.Timestamp(min_dt).tz_localize("UTC") if pd.Timestamp(min_dt).tzinfo is None else pd.Timestamp(min_dt)
    df = df[post_dt >= min_dt_utc].copy()

    # De-dup within run
    df = df.drop_duplicates(subset=["platform", "job_id"]).reset_index(drop=True)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8-sig")

    print(f"[OK] Saved: {args.out}")
    print(f"[INFO] Rows: {len(df)}")
    print(f"[INFO] Sources: {sorted(source_set)}")
    print(f"[INFO] Min date filter: {min_dt.date().isoformat()}")
    if len(df) > 0:
        print("[INFO] Sample columns:", list(df.columns))


if __name__ == "__main__":
    main()

