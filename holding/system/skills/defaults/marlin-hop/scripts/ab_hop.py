#!/usr/bin/env python3
"""A/B/C hop cost: no LLM vs agent-reads-ORG vs agent+hop.py.

A  no agent     — hop.py only (0 model tokens)
B  agent        — grok classifies; may read ORG.md; hop.py not mentioned
C  agent+script — grok must run hop.py; no reading ORG.md

Usage:
  python3 ab_hop.py              # A only (free)
  python3 ab_hop.py --lanes A,C  # skip expensive B
  python3 ab_hop.py --lanes A,B,C --limit 3
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import agents_home, load_tsv

HOP = Path(__file__).resolve().parent / "hop.py"
SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {"agent": {"type": "string"}},
        "required": ["agent"],
    }
)


def repo_root() -> Path:
    return agents_home().parent


def load_cases(limit: int | None) -> list[dict]:
    rows = []
    for r in load_tsv("cases.tsv"):
        row = {"id": r["id"], "expect": r["expect"]}
        if r.get("path"):
            row["path"] = r["path"]
        if r.get("section"):
            row["section"] = r["section"]
        rows.append(row)
    return rows[:limit] if limit else rows


def parse_agent(text: str) -> str | None:
    if not text:
        return None
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and isinstance(obj.get("agent"), str):
            return obj["agent"].strip().strip("`")
    except json.JSONDecodeError:
        pass
    m = re.search(r"(?im)^agent:\s*([a-z0-9-]+)", text)
    if m:
        return m.group(1)
    m = re.search(r'"agent"\s*:\s*"([a-z0-9-]+)"', text)
    if m:
        return m.group(1)
    return None


def run_a(case: dict) -> dict:
    cmd = [sys.executable, str(HOP)]
    if case.get("path"):
        cmd += ["--path", case["path"]]
    elif case.get("section"):
        cmd += ["--section", case["section"]]
    elif case.get("lesson"):
        cmd += ["--lesson", case["lesson"]]
    else:
        return {"lane": "A", "ok": False, "error": "no path/section"}
    t0 = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True)
    ms = int((time.perf_counter() - t0) * 1000)
    got = parse_agent(p.stdout)
    expect = case["expect"]
    return {
        "lane": "A",
        "id": case["id"],
        "ok": p.returncode == 0 and got == expect,
        "got": got,
        "expect": expect,
        "duration_ms": ms,
        "num_turns": 0,
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
            "total_tokens": 0,
        },
        "total_cost_usd": 0.0,
        "error": None if p.returncode == 0 else (p.stderr or "")[:400],
    }


def grok_prompt(case: dict, lane: str) -> str:
    target = case.get("path") or f"section {case.get('section')}"
    if lane == "C":
        if case.get("path"):
            invoke = f"python3 .agents/marlin-language-company/system/skills/defaults/marlin-hop/scripts/hop.py --path {case['path']}"
        else:
            invoke = f"python3 .agents/marlin-language-company/system/skills/defaults/marlin-hop/scripts/hop.py --section {case['section']!r}"
        return (
            "Run this command and copy its agent field. Do not read ORG.md.\n"
            f"{invoke}\n"
            'Reply JSON only: {"agent": "<name>"}'
        )
    return (
        "Which Marlin org agent owns this work? You may read "
        ".agents/marlin-language-company/system/staffs/ORG.md Path table. Do not spawn subagents.\n"
        f"Target: {target}\n"
        'Reply JSON only: {"agent": "<name>"}'
    )


def run_llm(case: dict, lane: str, model: str, effort: str, timeout: int) -> dict:
    grok = shutil.which("grok")
    if not grok:
        return {"lane": lane, "id": case["id"], "ok": False, "error": "grok not on PATH"}
    cmd = [
        grok,
        "-p",
        grok_prompt(case, lane),
        "-m",
        model,
        "--agent",
        "ceo",
        "--effort",
        effort,
        "--output-format",
        "json",
        "--json-schema",
        SCHEMA,
        "--always-approve",
        "--no-subagents",
        "--cwd",
        str(repo_root()),
        "--max-turns",
        "6" if lane == "B" else "4",
    ]
    if lane == "C":
        cmd += ["--tools", "run_terminal_cmd"]
    else:
        cmd += ["--tools", "read_file,grep,list_dir"]
    t0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {
            "lane": lane,
            "id": case["id"],
            "ok": False,
            "error": f"timeout {timeout}s",
            "duration_ms": timeout * 1000,
        }
    ms = int((time.perf_counter() - t0) * 1000)
    raw = (p.stdout or "").strip()
    payload = {}
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {"text": raw[:2000]}
    text = payload.get("text") or payload.get("result") or raw
    got = parse_agent(text if isinstance(text, str) else json.dumps(text))
    usage = payload.get("usage") or {}
    expect = case["expect"]
    return {
        "lane": lane,
        "id": case["id"],
        "ok": got == expect,
        "got": got,
        "expect": expect,
        "duration_ms": payload.get("duration_ms") or ms,
        "num_turns": payload.get("num_turns"),
        "usage": {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "reasoning_tokens": usage.get("reasoning_tokens", 0),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
        "total_cost_usd": payload.get("total_cost_usd"),
        "error": None if p.returncode == 0 else ((p.stderr or raw)[:400]),
    }


def summarize(rows: list[dict]) -> list[dict]:
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["lane"], []).append(r)
    out = []
    for lane, items in by.items():
        n = len(items)
        toks = sum((i.get("usage") or {}).get("total_tokens") or 0 for i in items)
        ms = sum(i.get("duration_ms") or 0 for i in items)
        ok = sum(1 for i in items if i.get("ok"))
        cost = [i.get("total_cost_usd") for i in items if i.get("total_cost_usd") is not None]
        out.append(
            {
                "lane": lane,
                "n": n,
                "correct": ok,
                "total_tokens": toks,
                "avg_tokens": round(toks / n, 1) if n else 0,
                "duration_ms": ms,
                "cost_usd": round(sum(cost), 6) if cost else None,
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="A/B hop token test")
    ap.add_argument("--lanes", default="A", help="comma: A,B,C")
    ap.add_argument("--limit", type=int, default=0, help="max cases (0=all)")
    ap.add_argument("--model", default="grok-4.5")
    ap.add_argument("--effort", default="low")
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()
    lanes = [x.strip().upper() for x in args.lanes.split(",") if x.strip()]
    cases = load_cases(args.limit or None)
    rows: list[dict] = []
    for case in cases:
        for lane in lanes:
            if lane == "A":
                rows.append(run_a(case))
            elif lane in {"B", "C"}:
                rows.append(run_llm(case, lane, args.model, args.effort, args.timeout))
            else:
                print(f"unknown lane {lane}", file=sys.stderr)
                return 2
            r = rows[-1]
            flag = "ok" if r.get("ok") else "miss"
            toks = (r.get("usage") or {}).get("total_tokens", 0)
            print(
                f"{r['lane']} {r.get('id')} {flag} got={r.get('got')} "
                f"tokens={toks} {r.get('duration_ms')}ms",
                file=sys.stderr,
            )
    report = {"lanes": lanes, "summary": summarize(rows), "runs": rows}
    json.dump(report, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
