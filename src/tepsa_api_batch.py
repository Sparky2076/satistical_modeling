"""
Multi-vendor batch API runner for TESSA-PSA: task_bank x policies -> task_policy_observations.

Uses stdlib only (urllib + ssl). Run from repo root with API keys in env:

  set OPENAI_API_KEY=...
  set DEEPSEEK_API_KEY=...
  set ANTHROPIC_API_KEY=...
  set GEMINI_API_KEY=...   (or GOOGLE_API_KEY)
  set ZAI_API_KEY=...      (or GLM_API_KEY)
  set MOONSHOT_API_KEY=... (or KIMI_API_KEY)
  set SPARK_API_KEY=...    (or XFYUN_API_PASSWORD)
  set QIANFAN_API_KEY=...  (or BAIDU_API_KEY / WENXIN_API_KEY)

Examples:
  python src/tepsa_api_batch.py --dry-run
  python src/tepsa_api_batch.py --max-tasks 5 --policy-ids pl_openai_mini_std,pl_deepseek_flash
  python src/tepsa_api_batch.py --max-tasks 20 --skip-high-risk

Then enrich costs (optional):
  python src/tepsa_main.py --obs data/tessa_psa/task_policy_observations.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import ssl
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "tessa_psa"

if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import tepsa_main  # noqa: E402

SECTOR_TO_TEPSA: dict[str, str] = {
    "public service": "public_service",
    "enterprise support": "enterprise_support",
    "manufacturing": "manufacturing",
    "education": "education",
    "code": "code",
}

DEFAULT_SYSTEM = (
    "You are a helpful assistant for Chinese public service, enterprise, and policy Q&A. "
    "Answer concisely in Chinese unless the user asks otherwise. "
    "Do not fabricate citations. If the question requires case-specific legal or medical "
    "judgment, state limits and suggest checking the latest official guidance."
)

IMPLEMENTED_PROVIDERS = frozenset({
    "OpenAI",
    "DeepSeek",
    "Anthropic",
    "Google",
    "GLM",
    "Kimi",
    "Spark",
    "Baidu",
})

OBS_EXTRA = ("tepsa_sector", "run_id", "response_path")

BASE_OBS_FIELDS = [
    "task_id",
    "sector",
    "task_source",
    "task_text",
    "risk_class",
    "difficulty_label",
    "model",
    "policy_id",
    "prompt_type",
    "context_type",
    "input_tokens",
    "output_tokens",
    "cache_tokens",
    "cost_usd",
    "latency_sec",
    "quality_score",
    "hallucination_flag",
    "risk_score",
    "human_time_base_min",
    "human_time_ai_min",
    "value_score",
]


def _json_request(
    url: str,
    headers: dict[str, str],
    body: dict[str, Any] | None,
    method: str = "POST",
    timeout: int = 120,
) -> tuple[dict[str, Any] | None, str | None]:
    ctx = ssl.create_default_context()
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, context=ctx, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = str(e)
        return None, f"HTTP {e.code}: {err_body[:2000]}"
    except URLError as e:
        return None, f"URL error: {e.reason!s}"
    except Exception as e:
        return None, str(e)
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"


def call_openai_chat(
    model_id: str,
    user_text: str,
    system: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str | None, dict[str, int], str | None]:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None, {}, "OPENAI_API_KEY not set"
    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data, err = _json_request(url, headers, body)
    if err:
        return None, {}, err
    try:
        text = data["choices"][0]["message"]["content"]  # type: ignore[index]
        u = data.get("usage") or {}
        toks = {
            "input_tokens": int(u.get("prompt_tokens", 0)),
            "output_tokens": int(u.get("completion_tokens", 0)),
            "cache_tokens": int(u.get("prompt_tokens_details", {}).get("cached_tokens", 0))
            if isinstance(u.get("prompt_tokens_details"), dict)
            else 0,
        }
        return text, toks, None
    except (KeyError, IndexError, TypeError) as e:
        return None, {}, f"parse OpenAI response: {e}"


def call_deepseek_chat(
    model_id: str,
    user_text: str,
    system: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str | None, dict[str, int], str | None]:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        return None, {}, "DEEPSEEK_API_KEY not set"
    base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    url = f"{base}/v1/chat/completions"
    body = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data, err = _json_request(url, headers, body)
    if err:
        return None, {}, err
    try:
        text = data["choices"][0]["message"]["content"]  # type: ignore[index]
        u = data.get("usage") or {}
        return (
            text,
            {
                "input_tokens": int(u.get("prompt_tokens", 0)),
                "output_tokens": int(u.get("completion_tokens", 0)),
                "cache_tokens": 0,
            },
            None,
        )
    except (KeyError, IndexError, TypeError) as e:
        return None, {}, f"parse DeepSeek response: {e}"


def call_anthropic_messages(
    model_id: str,
    user_text: str,
    system: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str | None, dict[str, int], str | None]:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None, {}, "ANTHROPIC_API_KEY not set"
    url = "https://api.anthropic.com/v1/messages"
    body: dict[str, Any] = {
        "model": model_id,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": user_text}],
    }
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    data, err = _json_request(url, headers, body)
    if err:
        return None, {}, err
    try:
        parts = data["content"][0]  # type: ignore[index]
        text = parts.get("text", "") if isinstance(parts, dict) else ""
        u = data.get("usage") or {}
        return (
            text,
            {
                "input_tokens": int(u.get("input_tokens", 0)),
                "output_tokens": int(u.get("output_tokens", 0)),
                "cache_tokens": int(u.get("cache_creation_input_tokens", 0) or 0)
                + int(u.get("cache_read_input_tokens", 0) or 0),
            },
            None,
        )
    except (KeyError, IndexError, TypeError) as e:
        return None, {}, f"parse Anthropic response: {e}"


def call_google_gemini(
    model_id: str,
    user_text: str,
    system: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str | None, dict[str, int], str | None]:
    key = (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )
    if not key:
        return None, {}, "GEMINI_API_KEY or GOOGLE_API_KEY not set"
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_id}:generateContent?key={key}"
    )
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        },
    }
    headers = {"Content-Type": "application/json"}
    data, err = _json_request(url, headers, body)
    if err:
        return None, {}, err
    try:
        cand = data["candidates"][0]  # type: ignore[index]
        parts = cand["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        um = data.get("usageMetadata") or {}
        return (
            text,
            {
                "input_tokens": int(um.get("promptTokenCount", 0)),
                "output_tokens": int(um.get("candidatesTokenCount", 0)),
                "cache_tokens": int(um.get("cachedContentTokenCount", 0) or 0),
            },
            None,
        )
    except (KeyError, IndexError, TypeError) as e:
        return None, {}, f"parse Gemini response: {e}"


def _call_openai_compatible_chat(
    *,
    provider_name: str,
    api_key: str,
    base_url: str,
    model_id: str,
    user_text: str,
    system: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str | None, dict[str, int], str | None]:
    """Call an OpenAI-compatible /chat/completions endpoint."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    body = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data, err = _json_request(url, headers, body)
    if err:
        return None, {}, err
    try:
        text = data["choices"][0]["message"]["content"]  # type: ignore[index]
        u = data.get("usage") or {}
        toks = {
            "input_tokens": int(u.get("prompt_tokens", 0) or u.get("input_tokens", 0) or 0),
            "output_tokens": int(u.get("completion_tokens", 0) or u.get("output_tokens", 0) or 0),
            "cache_tokens": int(u.get("prompt_tokens_details", {}).get("cached_tokens", 0))
            if isinstance(u.get("prompt_tokens_details"), dict)
            else int(u.get("cached_tokens", 0) or 0),
        }
        return text, toks, None
    except (KeyError, IndexError, TypeError) as e:
        return None, {}, f"parse {provider_name} response: {e}"


def call_glm_chat(
    model_id: str,
    user_text: str,
    system: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str | None, dict[str, int], str | None]:
    key = os.environ.get("ZAI_API_KEY", "").strip() or os.environ.get("GLM_API_KEY", "").strip()
    if not key:
        return None, {}, "ZAI_API_KEY or GLM_API_KEY not set"
    base = os.environ.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").rstrip("/")
    return _call_openai_compatible_chat(
        provider_name="GLM",
        api_key=key,
        base_url=base,
        model_id=model_id,
        user_text=user_text,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )




def call_kimi_chat(
    model_id: str,
    user_text: str,
    system: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str | None, dict[str, int], str | None]:
    key = os.environ.get("MOONSHOT_API_KEY", "").strip() or os.environ.get("KIMI_API_KEY", "").strip()
    if not key:
        return None, {}, "MOONSHOT_API_KEY or KIMI_API_KEY not set"
    base = os.environ.get("KIMI_BASE_URL", "https://api.moonshot.ai/v1").rstrip("/")
    return _call_openai_compatible_chat(
        provider_name="Kimi",
        api_key=key,
        base_url=base,
        model_id=model_id,
        user_text=user_text,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def call_spark_chat(
    model_id: str,
    user_text: str,
    system: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str | None, dict[str, int], str | None]:
    key = os.environ.get("SPARK_API_KEY", "").strip() or os.environ.get("XFYUN_API_PASSWORD", "").strip()
    if not key:
        return None, {}, "SPARK_API_KEY or XFYUN_API_PASSWORD not set"
    base = os.environ.get("SPARK_BASE_URL", "https://spark-api-open.xf-yun.com/v1").rstrip("/")
    return _call_openai_compatible_chat(
        provider_name="Spark",
        api_key=key,
        base_url=base,
        model_id=model_id,
        user_text=user_text,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def call_baidu_chat(
    model_id: str,
    user_text: str,
    system: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str | None, dict[str, int], str | None]:
    key = (
        os.environ.get("QIANFAN_API_KEY", "").strip()
        or os.environ.get("BAIDU_API_KEY", "").strip()
        or os.environ.get("WENXIN_API_KEY", "").strip()
    )
    if not key:
        return None, {}, "QIANFAN_API_KEY or BAIDU_API_KEY or WENXIN_API_KEY not set"
    base = os.environ.get("BAIDU_BASE_URL", "https://qianfan.baidubce.com/v2").rstrip("/")
    return _call_openai_compatible_chat(
        provider_name="Baidu",
        api_key=key,
        base_url=base,
        model_id=model_id,
        user_text=user_text,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def dispatcher(provider: str) -> Callable[..., tuple[str | None, dict[str, int], str | None]]:
    if provider == "OpenAI":
        return call_openai_chat
    if provider == "DeepSeek":
        return call_deepseek_chat
    if provider == "Anthropic":
        return call_anthropic_messages
    if provider == "Google":
        return call_google_gemini
    if provider == "GLM":
        return call_glm_chat
    if provider == "Kimi":
        return call_kimi_chat
    if provider == "Spark":
        return call_spark_chat
    if provider == "Baidu":
        return call_baidu_chat
    raise ValueError(f"Unsupported provider: {provider}")


def load_policies(path: Path, allowed: frozenset[str] | None) -> list[dict[str, str]]:
    _, rows = tepsa_main.read_csv(path)
    out: list[dict[str, str]] = []
    for row in rows:
        if not any((v or "").strip() for v in row.values()):
            continue
        prov = (row.get("provider") or "").strip()
        if prov not in IMPLEMENTED_PROVIDERS:
            raise SystemExit(
                f"Policy {row.get('policy_id')!r} uses provider {prov!r} which is not "
                f"implemented in tepsa_api_batch.py (implemented: {sorted(IMPLEMENTED_PROVIDERS)})."
            )
        if allowed is not None and prov not in allowed:
            continue
        out.append(row)
    return out


def existing_keys_for_run(path: Path, run_id: str) -> set[tuple[str, str]]:
    """Pairs (task_id, policy_id) already present for this run_id (resume)."""
    if not path.is_file():
        return set()
    _, rows = tepsa_main.read_csv(path)
    keys: set[tuple[str, str]] = set()
    for r in rows:
        if not any((v or "").strip() for v in r.values()):
            continue
        tid = (r.get("task_id") or "").strip()
        pid = (r.get("policy_id") or "").strip()
        rid = (r.get("run_id") or "").strip()
        if tid and pid and rid == run_id:
            keys.add((tid, pid))
    return keys


def build_obs_row(
    task: dict[str, str],
    pol: dict[str, str],
    run_id: str,
    model_id: str,
    toks: dict[str, int],
    latency: float,
    cost_usd: str,
    rel_response_path: str,
) -> dict[str, str]:
    sec = (task.get("sector") or "").strip()
    tepsa = SECTOR_TO_TEPSA.get(sec, "")
    row: dict[str, str] = {
        "task_id": task.get("task_id", "").strip(),
        "sector": sec,
        "task_source": (task.get("task_source") or "").strip(),
        "task_text": (task.get("task_text") or "").strip(),
        "risk_class": (task.get("risk_class") or "").strip(),
        "difficulty_label": (task.get("difficulty_label") or "").strip(),
        "model": model_id,
        "policy_id": (pol.get("policy_id") or "").strip(),
        "prompt_type": (pol.get("prompt_type") or "").strip(),
        "context_type": (pol.get("context_type") or "").strip(),
        "input_tokens": str(toks.get("input_tokens", 0)),
        "output_tokens": str(toks.get("output_tokens", 0)),
        "cache_tokens": str(toks.get("cache_tokens", 0)),
        "cost_usd": cost_usd,
        "latency_sec": f"{latency:.4f}",
        "quality_score": "",
        "hallucination_flag": "",
        "risk_score": "",
        "human_time_base_min": "",
        "human_time_ai_min": "",
        "value_score": "",
        "tepsa_sector": tepsa,
        "run_id": run_id,
        "response_path": rel_response_path.replace("\\", "/"),
    }
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-bank", type=Path, default=DATA_DIR / "task_bank.csv")
    ap.add_argument("--policies", type=Path, default=DATA_DIR / "policies.csv")
    ap.add_argument("--out", type=Path, default=DATA_DIR / "task_policy_observations.csv")
    ap.add_argument("--run-id", default="", help="Defaults to short random id.")
    ap.add_argument("--max-tasks", type=int, default=20, help="Safety cap (default 20).")
    ap.add_argument(
        "--policy-ids",
        default="",
        help="Comma-separated policy_id subset; empty means all policies in CSV.",
    )
    ap.add_argument(
        "--providers",
        default="",
        help=(
            "Comma subset of OpenAI,DeepSeek,Anthropic,Google,"
            "GLM,Kimi,Spark,Baidu; empty = all."
        ),
    )
    ap.add_argument("--skip-high-risk", action="store_true")
    ap.add_argument(
        "--resume",
        action="store_true",
        help="Skip (task_id, policy_id) pairs already present for the same --run-id in --out.",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    run_id = (args.run_id or "").strip() or uuid.uuid4().hex[:10]
    _, tasks = tepsa_main.read_csv(args.task_bank)
    tasks = [t for t in tasks if any((v or "").strip() for v in t.values())]

    prov_filter: frozenset[str] | None = None
    if args.providers.strip():
        prov_filter = frozenset(p.strip() for p in args.providers.split(",") if p.strip())

    policies = load_policies(args.policies, prov_filter)
    if args.policy_ids.strip():
        wanted = frozenset(x.strip() for x in args.policy_ids.split(",") if x.strip())
        policies = [p for p in policies if (p.get("policy_id") or "").strip() in wanted]
    if not policies:
        print("No policies after filter.", file=sys.stderr)
        sys.exit(2)

    if args.skip_high_risk:
        tasks = [t for t in tasks if (t.get("risk_class") or "").strip().lower() != "high"]

    tasks = tasks[: max(0, args.max_tasks)]
    n_calls = len(tasks) * len(policies)
    print(f"run_id={run_id}")
    print(f"tasks={len(tasks)} policies={len(policies)} total_calls={n_calls}")
    if args.dry_run:
        print("dry-run: no API calls made.")
        return

    done = existing_keys_for_run(args.out, run_id) if args.resume else set()
    runs_dir = DATA_DIR / "runs" / run_id
    runs_dir.mkdir(parents=True, exist_ok=True)

    prices = tepsa_main.price_rows_by_model()
    fieldnames = list(BASE_OBS_FIELDS) + list(OBS_EXTRA)
    existing_rows: list[dict[str, str]] = []
    if args.out.is_file():
        _, old_rows = tepsa_main.read_csv(args.out)
        for r in old_rows:
            if any((v or "").strip() for v in r.values()):
                existing_rows.append(r)

    new_rows: list[dict[str, str]] = []
    for task in tasks:
        tid = (task.get("task_id") or "").strip()
        user_text = (task.get("task_text") or "").strip()
        for pol in policies:
            pid = (pol.get("policy_id") or "").strip()
            if args.resume and (tid, pid) in done:
                print(f"skip (resume) {tid} {pid}")
                continue
            prov = (pol.get("provider") or "").strip()
            model_id = (pol.get("model_id") or "").strip()
            max_out = int((pol.get("max_output_tokens") or "1024").strip() or "1024")
            temp = float((pol.get("temperature") or "0.2").strip() or "0.2")
            fn = dispatcher(prov)
            t0 = time.perf_counter()
            text, toks, err = fn(
                model_id,
                user_text,
                DEFAULT_SYSTEM,
                max_out,
                temp,
            )
            latency = time.perf_counter() - t0

            rel_path = f"data/tessa_psa/runs/{run_id}/{tid}__{pid}.json"
            abs_path = REPO_ROOT / rel_path.replace("/", os.sep)
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            payload: dict[str, Any] = {
                "task_id": tid,
                "policy_id": pid,
                "run_id": run_id,
                "provider": prov,
                "model_id": model_id,
                "latency_sec": latency,
                "usage": toks,
                "error": err,
                "response_text": text,
            }
            abs_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            if err:
                print(
                    f"FAIL {tid} {pid}: {err}",
                    file=sys.stderr,
                )
                continue

            obs_stub = {
                "input_tokens": str(toks.get("input_tokens", 0)),
                "output_tokens": str(toks.get("output_tokens", 0)),
                "cache_tokens": str(toks.get("cache_tokens", 0)),
            }
            pr = prices.get(model_id)
            cost = tepsa_main.compute_cost_usd_row({**obs_stub, "model": model_id}, pr) if pr else ""

            row = build_obs_row(
                task,
                pol,
                run_id,
                model_id,
                toks,
                latency,
                cost,
                rel_path,
            )
            new_rows.append(row)
            print(f"ok {tid} {pid} in={toks.get('input_tokens',0)} out={toks.get('output_tokens',0)}")

    merged = existing_rows + new_rows
    tepsa_main.write_csv(args.out, fieldnames, merged)
    print(f"Wrote {args.out} total_rows={len(merged)} new_rows={len(new_rows)}")


if __name__ == "__main__":
    main()
