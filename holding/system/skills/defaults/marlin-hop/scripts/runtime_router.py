#!/usr/bin/env python3
"""Cross-runtime Assign router (harness policy).

Portable SoT (staffs/**, agents.tsv) is NEVER modified here.
This module:
  - matches role → runtime from system/harness/runtime_router.toml
  - filters which roles belong in a generated harness export
  - preflight CLI bins; cross-runtime assign via CLI + cache/handoff

Usage:
  python3 runtime_router.py match --role ba-lead
  python3 runtime_router.py roles --runtime codex
  python3 runtime_router.py check
  python3 runtime_router.py assign --from ceo --to ba-lead --goal '…'
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import agents_home, repo_root_from_company  # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:  # py<3.11
    import tomli as tomllib  # type: ignore


ROUTER_NAME = "runtime_router.toml"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def router_path(home: Optional[Path] = None) -> Path:
    home = home or agents_home()
    return home / "system" / "harness" / ROUTER_NAME


def load_router(home: Optional[Path] = None) -> dict[str, Any]:
    path = router_path(home)
    if not path.is_file():
        return {
            "id": "runtime_router",
            "enabled": False,
            "default": {"runtime": "grok"},
            "cli": {},
            "preflight": {"require_path": True, "require_login": True, "on_fail": "error"},
            "assign": {
                "same_runtime": "native",
                "cross_runtime": "cli",
                "return": "brief+handoff",
                "handoff_dir": "cache/handoff",
            },
            "roles": [{"match": "*", "runtime": "grok"}],
        }
    cfg = tomllib.loads(path.read_text(encoding="utf-8"))
    # Missing key = classic single-vendor (backward compatible)
    if "enabled" not in cfg:
        cfg["enabled"] = False
    return cfg


def router_enabled(cfg: Optional[dict[str, Any]] = None) -> bool:
    cfg = cfg or load_router()
    return bool(cfg.get("enabled"))


def default_runtime(cfg: dict[str, Any]) -> str:
    return str((cfg.get("default") or {}).get("runtime") or "grok")


def match_runtime(role: str, cfg: Optional[dict[str, Any]] = None) -> str:
    """First-match glob in [[roles]]; fallback default."""
    cfg = cfg or load_router()
    role = (role or "").strip()
    for row in cfg.get("roles") or []:
        pat = str(row.get("match") or "").strip()
        if not pat:
            continue
        if fnmatch.fnmatchcase(role, pat) or fnmatch.fnmatch(role, pat):
            rt = str(row.get("runtime") or "").strip()
            if rt:
                return rt
    return default_runtime(cfg)


def roles_for_runtime(
    runtime: str, all_roles: list[str], cfg: Optional[dict[str, Any]] = None
) -> list[str]:
    """Which SoT role names belong in a generated export for `runtime`."""
    cfg = cfg or load_router()
    runtime = (runtime or "").strip()
    out: list[str] = []
    for name in all_roles:
        if match_runtime(name, cfg) == runtime:
            out.append(name)
    return out


def filter_agent_rows(
    rows: list[dict[str, str]], runtime: str, cfg: Optional[dict[str, Any]] = None
) -> list[dict[str, str]]:
    """Filter agents.tsv rows for harness export. SoT file itself unchanged.

    When router disabled / missing: return all rows (classic all-on-one-vendor).
    When enabled: only roles mapped to this runtime appear in the generated export.
    """
    cfg = cfg or load_router()
    if not router_enabled(cfg):
        return rows
    return [r for r in rows if match_runtime(r.get("name") or "", cfg) == runtime]


def _cli_bin(cfg: dict[str, Any], runtime: str) -> str:
    cli = (cfg.get("cli") or {}).get(runtime) or {}
    if isinstance(cli, dict) and cli.get("bin"):
        return str(cli["bin"])
    return runtime


def _which(bin_name: str) -> Optional[str]:
    return shutil.which(bin_name)


def cmd_match(args: argparse.Namespace) -> int:
    cfg = load_router()
    enabled = router_enabled(cfg)
    rt = match_runtime(args.role, cfg) if enabled else default_runtime(cfg)
    print(f"enabled\t{1 if enabled else 0}")
    print(f"role\t{args.role}")
    print(f"runtime\t{rt}")
    print(f"same_as_session\t{1 if args.session and args.session == rt else 0}")
    print("sot\tunchanged")
    if not enabled:
        print("mode\tsingle_vendor — enable runtime_router.toml to split")
    return 0


def cmd_roles(args: argparse.Namespace) -> int:
    from common import load_tsv

    cfg = load_router()
    names = [r.get("name") or "" for r in load_tsv("agents.tsv") if r.get("name")]
    runtime = args.runtime or default_runtime(cfg)
    enabled = router_enabled(cfg)
    print(f"enabled\t{1 if enabled else 0}")
    if not enabled:
        print(f"runtime\t{runtime}")
        print(f"count\t{len(names)}")
        for n in names:
            print(f"role\t{n}")
        print("mode\tsingle_vendor — full roster on every company_os.sh harness")
        print("sot\tunchanged")
        return 0
    picked = roles_for_runtime(runtime, names, cfg)
    print(f"runtime\t{runtime}")
    print(f"count\t{len(picked)}")
    for n in picked:
        print(f"role\t{n}")
    print("sot\tunchanged — filter applies to generated export only")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    home = agents_home()
    cfg = load_router(home)
    path = router_path(home)
    enabled = router_enabled(cfg)
    print(f"router\t{path}")
    print(f"exists\t{1 if path.is_file() else 0}")
    print(f"enabled\t{1 if enabled else 0}")
    print(f"default\t{default_runtime(cfg)}")
    if not enabled:
        print("mode\tsingle_vendor")
        print("status\tok")
        print("hint\tset enabled=true in runtime_router.toml to split vendors by role")
        print("sot\tunchanged")
        return 0
    pre = cfg.get("preflight") or {}
    on_fail = str(pre.get("on_fail") or "error")
    issues = 0
    runtimes = set()
    for row in cfg.get("roles") or []:
        rt = str(row.get("runtime") or "").strip()
        if rt:
            runtimes.add(rt)
    runtimes.add(default_runtime(cfg))
    for rt in sorted(runtimes):
        bin_name = _cli_bin(cfg, rt)
        found = _which(bin_name)
        ok = 1 if found else 0
        print(f"cli\t{rt}\t{bin_name}\t{ok}\t{found or '—'}")
        if not found:
            issues += 1
            print(f"warn\tmissing_bin\t{bin_name}")
    if issues and on_fail == "error":
        print(f"status\terror\tmissing={issues}")
        print("rule\tno silent fallback — install/login CLIs or change on_fail")
        return 1
    print("status\tok" if not issues else f"status\twarn\tmissing={issues}")
    print("sot\tunchanged")
    return 0


def cmd_assign(args: argparse.Namespace) -> int:
    """Emit assign plan; cross-runtime may invoke CLI when --execute."""
    home = agents_home()
    cfg = load_router(home)
    root = repo_root_from_company(home)
    session = (args.session or os.environ.get("MARLIN_HARNESS") or default_runtime(cfg)).strip()
    target = args.to.strip()
    enabled = router_enabled(cfg)
    target_rt = match_runtime(target, cfg) if enabled else session
    same = (not enabled) or (session == target_rt)
    print(f"enabled\t{1 if enabled else 0}")
    print(f"from\t{args.from_role or '—'}")
    print(f"to\t{target}")
    print(f"session\t{session}")
    print(f"target_runtime\t{target_rt}")
    print(f"mode\t{'native' if same else 'cli'}")
    print("sot\tunchanged")
    if not enabled:
        print("hint\tsingle_vendor — native spawn only; set enabled=true to cross CLI")

    assign = cfg.get("assign") or {}
    handoff_rel = str(assign.get("handoff_dir") or "cache/handoff")
    handoff_dir = home / handoff_rel
    goal = (args.goal or "").strip()
    stamp = utc_stamp()
    handoff_path = handoff_dir / f"{stamp}-{target}-{target_rt}.md"

    brief_lines = [
        f"# Handoff → `{target}` ({target_rt})",
        "",
        f"- from: `{args.from_role or 'ceo'}`",
        f"- session_runtime: `{session}`",
        f"- target_runtime: `{target_rt}`",
        f"- mode: `{'native' if same else 'cli'}`",
        f"- project_root: `{root}`",
        f"- company: `{home}`",
        f"- goal: {goal or '—'}",
        "",
        "SoT staffs/agents.tsv unchanged. Generated adapters filtered by runtime_router.toml.",
        "",
    ]
    brief = "\n".join(brief_lines)

    if same:
        print("action\tspawn_native")
        print(f"hint\tAssign subagent_type={target} in current session")
        if assign.get("return", "").startswith("brief") or True:
            handoff_dir.mkdir(parents=True, exist_ok=True)
            handoff_path.write_text(brief + "\n## Note\n\nSame-runtime — use native spawn.\n", encoding="utf-8")
            print(f"handoff\t{handoff_path}")
        print(brief.replace("\n", "\n# "))
        return 0

    # Cross-runtime
    bin_name = _cli_bin(cfg, target_rt)
    found = _which(bin_name)
    pre = cfg.get("preflight") or {}
    on_fail = str(pre.get("on_fail") or "error")
    if not found:
        print(f"error\tmissing_bin\t{bin_name}", file=sys.stderr)
        if on_fail == "error":
            print("status\terror")
            return 1
        print("status\twarn\tno_execute")
        return 1

    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(
        brief
        + "\n## CLI\n\n"
        + f"```bash\n{bin_name} -p '…' --cwd '{root}'\n```\n",
        encoding="utf-8",
    )
    print(f"handoff\t{handoff_path}")
    print(f"cli_bin\t{found}")

    if not args.execute:
        print("action\tplan_only")
        print(f"next\trun with --execute to invoke {bin_name}")
        print(f"brief_path\t{handoff_path}")
        return 0

    # Minimal headless invoke — vendor flags differ; keep conservative.
    prompt = (
        f"You are company staff `{target}` (runtime {target_rt}).\n"
        f"Read handoff: {handoff_path}\n"
        f"Goal: {goal or '(see handoff)'}\n"
        f"Do not invent unpaid roles. Return a short English done-when summary.\n"
    )
    timeout = int(((cfg.get("cli") or {}).get(target_rt) or {}).get("timeout_sec") or 600)
    cmd: list[str]
    if target_rt == "grok":
        cmd = [found, "-p", prompt, "--cwd", str(root), "--yolo", "--no-auto-update"]
    elif target_rt == "codex":
        cmd = [found, "exec", "--cwd", str(root), prompt]
    elif target_rt == "claude":
        cmd = [found, "-p", prompt, "--print"]
    else:
        cmd = [found, prompt]

    print(f"action\texec\t{' '.join(cmd[:3])}…")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        print("error\ttimeout", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"error\tmissing_bin\t{bin_name}", file=sys.stderr)
        return 1

    out_log = handoff_dir / f"{stamp}-{target}-{target_rt}.stdout.txt"
    out_log.write_text(proc.stdout or "", encoding="utf-8")
    err_log = handoff_dir / f"{stamp}-{target}-{target_rt}.stderr.txt"
    err_log.write_text(proc.stderr or "", encoding="utf-8")
    print(f"exit\t{proc.returncode}")
    print(f"stdout_log\t{out_log}")
    print(f"stderr_log\t{err_log}")
    # Short stdout brief for parent
    snippet = (proc.stdout or "").strip().splitlines()
    for line in snippet[:20]:
        print(f"out\t{line}")
    return 0 if proc.returncode == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Runtime router: SoT unchanged; filters generated harness exports "
            "and plans CEO Assign native vs CLI."
        )
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("match", help="Role → runtime")
    m.add_argument("--role", required=True)
    m.add_argument("--session", default="", help="Current session harness id")

    r = sub.add_parser("roles", help="List SoT roles for one generated runtime")
    r.add_argument("--runtime", default="")

    sub.add_parser("check", help="Preflight CLI bins for mapped runtimes")

    a = sub.add_parser("assign", help="Plan/execute Assign with router")
    a.add_argument("--from", dest="from_role", default="ceo")
    a.add_argument("--to", required=True)
    a.add_argument("--goal", default="")
    a.add_argument("--session", default="", help="Current session runtime (default MARLIN_HARNESS)")
    a.add_argument(
        "--execute",
        action="store_true",
        help="Actually invoke cross-runtime CLI (default: plan + handoff file only)",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "match":
        return cmd_match(args)
    if args.cmd == "roles":
        return cmd_roles(args)
    if args.cmd == "check":
        return cmd_check(args)
    if args.cmd == "assign":
        return cmd_assign(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
