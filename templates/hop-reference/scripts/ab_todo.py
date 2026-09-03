#!/usr/bin/env python3
"""Realistic A/B/C: build an MPM Marlin todo Service backend.

Same first user line for every lane:
  build a backend with an mpm marlin service that implements a todo list

A  chat      — no CEO, no hop.py (ordinary grok session + follow-ups)
B  ceo_plain — CEO first, no hop.py (may read ORG), then one IC
C  ceo_hop   — CEO first, hop.py/roster, then one IC

Done when todo_gate.py passes. Writes under:
  qa/integrations/mpm/applications/applications/server/TodoListAB/<lane>/
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import agents_home
from todo_gate import scan

USER0 = "build a backend with an mpm marlin service that implements a todo list"

REL_ROOT = Path(".agents/marlin-language-company/example/eval/todo-ab")


def repo() -> Path:
    return agents_home().parent


def grok_bin() -> str:
    g = shutil.which("grok")
    if not g:
        raise SystemExit("grok not on PATH")
    return g


def parse_assign(text: str) -> str | None:
    if not text:
        return None
    for pat in (
        r"(?im)^-?\s*agent:\s*`?([a-z0-9-]+)`?",
        r"(?im)^-?\s*spawn:\s*`?([a-z0-9-]+)`?",
        r'"agent"\s*:\s*"([a-z0-9-]+)"',
    ):
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return None


def grok_call(
    *,
    prompt: str,
    cwd: Path,
    session: str,
    resume: bool,
    model: str,
    effort: str,
    agent: str | None,
    extra: list[str],
    timeout: int,
) -> dict:
    cmd = [
        grok_bin(),
        "-p",
        prompt,
        "-m",
        model,
        "--effort",
        effort,
        "--output-format",
        "json",
        "--always-approve",
        "--no-subagents",
        "--cwd",
        str(cwd),
        "--max-turns",
        "40",
    ]
    if resume:
        cmd += ["-r", session]
    else:
        cmd += ["-s", session]
    if agent:
        cmd += ["--agent", agent]
    cmd += extra
    t0 = time.perf_counter()
    log_dir = repo() / REL_ROOT / ".grok_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    out_log = log_dir / f"{session}.stdout.json"
    err_log = log_dir / f"{session}.stderr.txt"
    raw = ""
    err = ""
    code = 1
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        raw = p.stdout or ""
        err = p.stderr or ""
        code = p.returncode
    except subprocess.TimeoutExpired as e:
        raw = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        code = 124
        err = (err + f"\ntimeout {timeout}s").strip()
    out_log.write_text(raw)
    err_log.write_text(err)
    ms = int((time.perf_counter() - t0) * 1000)
    raw_s = raw.strip()
    payload: dict = {}
    if raw_s:
        try:
            payload = json.loads(raw_s)
        except json.JSONDecodeError:
            brace = raw_s.rfind("\n{")
            chunk = raw_s[brace + 1 :] if brace >= 0 else raw_s[raw_s.find("{") :] if "{" in raw_s else ""
            try:
                payload = json.loads(chunk) if chunk else {"text": raw_s[:4000]}
            except json.JSONDecodeError:
                payload = {"text": raw_s[:4000], "stderr": err[:800]}
    usage = payload.get("usage") or {}
    text = payload.get("text") or payload.get("result") or raw
    if isinstance(text, dict):
        text = json.dumps(text)
    sid = payload.get("sessionId") or session
    return {
        "ok": code == 0,
        "error": None if code == 0 else (err or raw_s)[:600],
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
        "text": text if isinstance(text, str) else str(text),
        "session": sid,
    }


def add_usage(a: dict, b: dict) -> dict:
    keys = (
        "input_tokens",
        "output_tokens",
        "reasoning_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
        "total_tokens",
    )
    out = {k: int(a.get(k) or 0) + int(b.get(k) or 0) for k in keys}
    return out


def constraint(out_rel: Path) -> str:
    return (
        f"Write the new MPM Application only under `{out_rel.as_posix()}/`. "
        "Do not edit other qa fixtures, src/, or libraries/. "
        "Need: ConfigKit Application.marlin, .application(.service), "
        "import Service, import ServiceDatabase, todo CRUD routes, "
        "isTestTarget unit tests (UnitTest/TestCase) and a Service test "
        "(ServiceTestApplication or import Service in Tests). "
        "Follow existing qa/.../RestApplication and MySQLApplication patterns."
    )


def run_lane_chat(out: Path, out_rel: Path, args: argparse.Namespace) -> dict:
    session = str(uuid.uuid4())
    usage = {}
    cost = 0.0
    ms = 0
    turns = []
    prompt = USER0 + "\n\n" + constraint(out_rel)
    resume = False
    for i in range(args.max_user_turns):
        r = grok_call(
            prompt=prompt,
            cwd=repo(),
            session=session,
            resume=resume,
            model=args.model,
            effort="medium",
            agent=None,
            extra=[],
            timeout=args.timeout,
        )
        resume = True
        session = r["session"]
        usage = add_usage(usage, r.get("usage") or {})
        if r.get("total_cost_usd"):
            cost += float(r["total_cost_usd"])
        ms += int(r.get("duration_ms") or 0)
        gate = scan(out)
        turns.append(
            {
                "user_turn": i + 1,
                "agent": None,
                "ok_model": r["ok"],
                "gate_pass": gate["pass"],
                "missing": gate["missing"],
                "tokens": (r.get("usage") or {}).get("total_tokens"),
                "error": r.get("error"),
            }
        )
        if gate["pass"]:
            break
        prompt = gate["follow_up"]
    return _finish("chat", out, usage, cost, ms, turns)


def run_lane_ceo(out: Path, out_rel: Path, args: argparse.Namespace, hop: bool) -> dict:
    usage = {}
    cost = 0.0
    ms = 0
    turns = []
    ceo_session = str(uuid.uuid4())
    if hop:
        ceo_prompt = (
            USER0
            + "\n\nYou are CEO. Dispatch only. Run hop.py, do not read ORG.md or child .md.\n"
            "python3 .agents/marlin-language-company/system/skills/defaults/marlin-hop/scripts/hop.py --path "
            "qa/integrations/mpm/applications/applications/server\n"
            "python3 .agents/marlin-language-company/system/skills/defaults/marlin-hop/scripts/hop.py --roster ceo\n"
            "Implementer is almost certainly mpm-engineer. Return ## Assign with agent/model/"
            "capability_mode/skill. Do not implement.\n"
            + constraint(out_rel)
        )
        extra = ["--tools", "run_terminal_cmd"]
    else:
        ceo_prompt = (
            USER0
            + "\n\nYou are CEO. Dispatch only. Do NOT use hop.py. "
            "You may read .agents/marlin-language-company/system/staffs/ORG.md. Return ## Assign with the IC to implement. "
            "Do not implement yourself.\n"
            + constraint(out_rel)
        )
        extra = ["--tools", "read_file,grep,list_dir"]
    r = grok_call(
        prompt=ceo_prompt,
        cwd=repo(),
        session=ceo_session,
        resume=False,
        model=args.model,
        effort="low",
        agent="ceo",
        extra=extra,
        timeout=min(args.timeout, 180),
    )
    usage = add_usage(usage, r.get("usage") or {})
    if r.get("total_cost_usd"):
        cost += float(r["total_cost_usd"])
    ms += int(r.get("duration_ms") or 0)
    ic = parse_assign(r.get("text") or "") or "mpm-engineer"
    if ic in {"ceo", "po-modify", "po-new", "ba-user", "ba-lead", "cto"}:
        ic = "mpm-engineer"
    turns.append(
        {
            "user_turn": 0,
            "agent": "ceo",
            "assign": ic,
            "ok_model": r["ok"],
            "tokens": (r.get("usage") or {}).get("total_tokens"),
            "error": r.get("error"),
        }
    )

    ic_session = str(uuid.uuid4())
    if hop:
        ic_prompt = (
            USER0
            + "\nYou are "
            + ic
            + ". Implement now. Load only the skill in hop.py stdout if you run it.\n"
            "python3 .agents/marlin-language-company/system/skills/defaults/marlin-hop/scripts/hop.py --agent "
            + ic
            + "\n"
            + constraint(out_rel)
        )
    else:
        ic_prompt = USER0 + "\nYou are " + ic + ". Implement now.\n" + constraint(out_rel)
    resume = False
    session = ic_session
    for i in range(args.max_user_turns):
        r = grok_call(
            prompt=ic_prompt,
            cwd=repo(),
            session=session,
            resume=resume,
            model=args.model,
            effort="medium",
            agent=ic,
            extra=[],
            timeout=args.timeout,
        )
        resume = True
        session = r["session"]
        usage = add_usage(usage, r.get("usage") or {})
        if r.get("total_cost_usd"):
            cost += float(r["total_cost_usd"])
        ms += int(r.get("duration_ms") or 0)
        gate = scan(out)
        turns.append(
            {
                "user_turn": i + 1,
                "agent": ic,
                "ok_model": r["ok"],
                "gate_pass": gate["pass"],
                "missing": gate["missing"],
                "tokens": (r.get("usage") or {}).get("total_tokens"),
                "error": r.get("error"),
            }
        )
        if gate["pass"]:
            break
        ic_prompt = gate["follow_up"]
    name = "ceo_hop" if hop else "ceo_plain"
    return _finish(name, out, usage, cost, ms, turns)


def _finish(lane: str, out: Path, usage: dict, cost: float, ms: int, turns: list) -> dict:
    gate = scan(out) if out.exists() else {"pass": False, "missing": ["no-dir"], "score_0_10": 0, "files": [], "quality": {}}
    return {
        "lane": lane,
        "pass": gate.get("pass"),
        "score_0_10": gate.get("score_0_10"),
        "missing": gate.get("missing"),
        "files": gate.get("files"),
        "quality": gate.get("quality"),
        "usage": usage,
        "total_cost_usd": round(cost, 6) if cost else None,
        "duration_ms": ms,
        "user_turns": len([t for t in turns if t.get("user_turn", 0) > 0]),
        "turns": turns,
    }


def state_path() -> Path:
    return repo() / REL_ROOT / "ab_todo_state.json"


def load_state() -> dict:
    p = state_path()
    if not p.is_file():
        return {"input": USER0, "lanes": {}}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return {"input": USER0, "lanes": {}}


def save_state(state: dict) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lanes", default="A,B,C", help="A=chat B=ceo_plain C=ceo_hop")
    ap.add_argument("--model", default="grok-4.5")
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument("--max-user-turns", type=int, default=4)
    ap.add_argument("--resume", action="store_true",
                    help="continue after pause/reboot; skip lanes whose gate already passes")
    args = ap.parse_args()

    import signal

    state = load_state() if args.resume else {"input": USER0, "lanes": {}}
    paused = {"v": False}

    def _pause(_signum, _frame):
        paused["v"] = True
        print("pause requested — finishing current grok call then saving", file=sys.stderr)

    signal.signal(signal.SIGINT, _pause)
    signal.signal(signal.SIGTERM, _pause)

    base = repo() / REL_ROOT
    mapping = {
        "A": ("chat", False, "chat"),
        "B": ("ceo_plain", False, "ceo"),
        "C": ("ceo_hop", True, "ceo"),
    }
    results = []
    for key in [x.strip().upper() for x in args.lanes.split(",") if x.strip()]:
        if paused["v"]:
            break
        if key not in mapping:
            print("unknown lane", key, file=sys.stderr)
            return 2
        folder, hop, kind = mapping[key]
        out = base / folder
        out.mkdir(parents=True, exist_ok=True)
        (out / ".eval").write_text(f"lane={folder}\ninput={USER0}\n")
        prev = (state.get("lanes") or {}).get(folder) or {}
        if args.resume and prev.get("pass") and scan(out).get("pass"):
            print(f"== skip {key} {folder} (gate already pass) ==", file=sys.stderr)
            results.append(prev)
            continue
        if args.resume and scan(out).get("pass"):
            row = _finish(folder, out, prev.get("usage") or {}, float(prev.get("total_cost_usd") or 0), int(prev.get("duration_ms") or 0), prev.get("turns") or [])
            print(f"== skip {key} {folder} (files already pass gate) ==", file=sys.stderr)
            state.setdefault("lanes", {})[folder] = row
            save_state(state)
            results.append(row)
            continue
        out_rel = REL_ROOT / folder
        print(f"== lane {key} {folder} ==", file=sys.stderr)
        if kind == "chat":
            row = run_lane_chat(out, out_rel, args)
        else:
            row = run_lane_ceo(out, out_rel, args, hop=hop)
        state.setdefault("lanes", {})[folder] = row
        save_state(state)
        results.append(row)
        print(
            f"{row['lane']} pass={row['pass']} score={row['score_0_10']} "
            f"tokens={row['usage'].get('total_tokens')} {row['duration_ms']}ms "
            f"missing={row['missing']}",
            file=sys.stderr,
        )
        if paused["v"]:
            print("paused. Resume: python3 .../ab_todo.py --resume --lanes A,B,C", file=sys.stderr)
            break
    report = {"input": USER0, "lanes": results, "paused": paused["v"]}
    tsv = base / "ab_todo_report.tsv"
    cols = ["lane", "pass", "tokens", "ms", "usd", "quality", "naming", "isolation"]
    lines = ["\t".join(cols)]
    for row in results:
        q = (row.get("quality_score") or {}).get("overall", "")
        d = row.get("distinction") or {}
        u = row.get("usage") or {}
        lines.append("\t".join([
            str(row.get("lane", "")),
            str(row.get("pass", "")),
            str((u.get("total_tokens") if isinstance(u, dict) else "") or ""),
            str(row.get("duration_ms") or ""),
            str(row.get("total_cost_usd") or ""),
            str(q),
            str(d.get("naming_specificity") or ""),
            str(d.get("db_isolation") or ""),
        ]))
    tsv.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("wrote", tsv, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
