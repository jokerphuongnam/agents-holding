#!/usr/bin/env python3
"""Cross-runtime Assign / hop router (harness policy).

Portable SoT (staffs/**, agents.tsv) is NEVER modified here.
Staff identity stays the same under every launch mode:
  - grok|codex|claude → run that vendor's full harness setup
  - merge → overlay only (which vendor CLI + that vendor's model/effort)
    via runtime_router.toml; staff card/skills/tier SoT unchanged

This module:
  - matches role → runtime from system/harness/runtime_router.toml
  - resolves merge profile: runtime + tier + model + effort
  - filters which roles belong in a generated harness export
  - preflight CLI bins; cross-runtime hop/assign via CLI + cache/handoff

Usage:
  python3 runtime_router.py match --role ba-user --session grok
  python3 runtime_router.py resolve --role ba-user
  python3 runtime_router.py resolve --role ba-user --session grok
  python3 runtime_router.py roles --runtime claude
  python3 runtime_router.py check
  python3 runtime_router.py hop --from ceo --to ba-user --session grok --goal '…'
  python3 runtime_router.py assign --from ceo --to ba-user --goal '…'
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    agents_home,
    load_harness_toml,
    load_tsv,
    repo_root_from_company,
    resolve_vendor,
)

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


def _budget_tier_overrides(home: Path) -> dict[str, str]:
    path = home / "system" / "install" / "BUDGET_APPLIED.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    raw = data.get("agents_tsv_tier_overrides") or {}
    return {str(k): str(v) for k, v in raw.items() if k and v}


def _role_tier(role: str, home: Path) -> str:
    """Effective portable tier: agents.tsv, then BUDGET_APPLIED overrides."""
    role = (role or "").strip()
    tier = "medium"
    for row in load_tsv("agents.tsv"):
        if (row.get("name") or "").strip() == role:
            tier = (row.get("tier") or tier).strip() or tier
            break
    overrides = _budget_tier_overrides(home)
    if role in overrides:
        tier = overrides[role]
    return tier


def resolve_profile(
    role: str,
    *,
    session: str = "",
    cfg: Optional[dict[str, Any]] = None,
    home: Optional[Path] = None,
) -> dict[str, Any]:
    """Merge profile for one staff: runtime + tier + model + effort + hop mode.

    When router enabled: runtime comes from [[roles]].
    When disabled: runtime is session (or company default) — single-vendor story.
    Model/effort always come from that runtime's harness toml + effective tier.
    """
    home = home or agents_home()
    cfg = cfg or load_router(home)
    enabled = router_enabled(cfg)
    session_rt = (
        session or os.environ.get("MARLIN_HARNESS") or default_runtime(cfg)
    ).strip()
    if enabled:
        runtime = match_runtime(role, cfg)
    else:
        runtime = session_rt or default_runtime(cfg)
    tier = _role_tier(role, home)
    model, effort = resolve_vendor(tier, runtime)
    # If harness missing maps, still surface empty model clearly.
    if not model:
        ht = load_harness_toml(runtime)
        model = str((ht.get("tier_to_model") or {}).get(tier) or "")
    same = (not enabled) or (session_rt == runtime)
    return {
        "role": role,
        "enabled": enabled,
        "session": session_rt,
        "runtime": runtime,
        "tier": tier,
        "model": model,
        "effort": effort,
        "mode": "native" if same else "cli",
        "same_as_session": same,
    }


def _print_profile(prefix: str, profile: dict[str, Any]) -> None:
    p = prefix
    print(f"{p}role\t{profile['role']}")
    print(f"{p}runtime\t{profile['runtime']}")
    print(f"{p}tier\t{profile['tier']}")
    print(f"{p}model\t{profile['model'] or '—'}")
    print(f"{p}effort\t{profile['effort']}")
    print(f"{p}mode\t{profile['mode']}")
    print(f"{p}same_as_session\t{1 if profile['same_as_session'] else 0}")


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


def cmd_resolve(args: argparse.Namespace) -> int:
    """Show merge profile: runtime + model + effort for a staff (and hop mode vs session)."""
    home = agents_home()
    cfg = load_router(home)
    profile = resolve_profile(args.role, session=args.session or "", cfg=cfg, home=home)
    print(f"enabled\t{1 if profile['enabled'] else 0}")
    print(f"session\t{profile['session'] or '—'}")
    _print_profile("", profile)
    print("sot\tunchanged")
    if not profile["enabled"]:
        print("hint\tsingle_vendor — set enabled=true in runtime_router.toml for merge split")
        print("hint\tmodel/effort still resolve against session/default runtime harness")
    elif not profile["same_as_session"]:
        print(
            f"hint\thop from session `{profile['session']}` → CLI `{profile['runtime']}` "
            f"({profile['model'] or '—'} / {profile['effort']})"
        )
    else:
        print("hint\tsame runtime as session — native spawn")
    return 0


def cmd_roles(args: argparse.Namespace) -> int:
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


def _assign_or_hop(args: argparse.Namespace, *, command: str) -> int:
    """Shared plan/execute path for assign and hop.

    hop always prints from/to merge profiles first. When router enabled and
    target runtime ≠ session, mode=cli (CEO on grok hops BA on claude via CLI),
    not a same-session grok spawn.
    """
    home = agents_home()
    cfg = load_router(home)
    root = repo_root_from_company(home)
    session = (args.session or os.environ.get("MARLIN_HARNESS") or default_runtime(cfg)).strip()
    target = args.to.strip()
    from_role = (args.from_role or "ceo").strip()
    enabled = router_enabled(cfg)

    from_profile = resolve_profile(from_role, session=session, cfg=cfg, home=home)
    to_profile = resolve_profile(target, session=session, cfg=cfg, home=home)
    target_rt = to_profile["runtime"]
    same = to_profile["same_as_session"]

    print(f"command\t{command}")
    print(f"enabled\t{1 if enabled else 0}")
    print(f"from\t{from_role}")
    print(f"to\t{target}")
    print(f"session\t{session}")
    print(f"target_runtime\t{target_rt}")
    print(f"mode\t{'native' if same else 'cli'}")
    print("sot\tunchanged")
    print("from_profile")
    _print_profile("from.", from_profile)
    print("to_profile")
    _print_profile("to.", to_profile)

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
        f"- command: `{command}`",
        f"- from: `{from_role}` ({from_profile['runtime']} · {from_profile['model'] or '—'} · {from_profile['effort']})",
        f"- to: `{target}` ({to_profile['runtime']} · {to_profile['model'] or '—'} · {to_profile['effort']})",
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
    if not same:
        brief_lines += [
            "## Cross-runtime hop",
            "",
            f"Do **not** spawn `{target}` inside session `{session}`.",
            f"Invoke CLI `{target_rt}` with this staff's model/effort "
            f"(`{to_profile['model'] or '—'}` / `{to_profile['effort']}`).",
            "",
        ]
    brief = "\n".join(brief_lines)

    if same:
        print("action\tspawn_native")
        print(f"hint\tAssign subagent_type={target} in current session")
        handoff_dir.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text(
            brief + "\n## Note\n\nSame-runtime — use native spawn.\n",
            encoding="utf-8",
        )
        print(f"handoff\t{handoff_path}")
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
    print(
        f"hint\tCEO session `{session}` hops `{target}` on `{target_rt}` "
        f"— not native spawn in `{session}`"
    )

    if not args.execute:
        print("action\tplan_only")
        print(f"next\trun with --execute to invoke {bin_name}")
        print(f"brief_path\t{handoff_path}")
        return 0

    prompt = (
        f"You are company staff `{target}` (runtime {target_rt}, "
        f"model {to_profile['model'] or 'default'}, effort {to_profile['effort']}).\n"
        f"Read handoff: {handoff_path}\n"
        f"Goal: {goal or '(see handoff)'}\n"
        f"Do not invent unpaid roles. Return a short English done-when summary.\n"
    )
    timeout = int(((cfg.get("cli") or {}).get(target_rt) or {}).get("timeout_sec") or 600)
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
    snippet = (proc.stdout or "").strip().splitlines()
    for line in snippet[:20]:
        print(f"out\t{line}")
    return 0 if proc.returncode == 0 else 1


def cmd_assign(args: argparse.Namespace) -> int:
    return _assign_or_hop(args, command="assign")


def cmd_hop(args: argparse.Namespace) -> int:
    """CEO/lead hop: resolve profiles then native spawn or cross-runtime CLI."""
    return _assign_or_hop(args, command="hop")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Runtime router: SoT unchanged; resolve merge profiles "
            "(runtime+model+effort); filter exports; hop native vs CLI."
        )
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("match", help="Role → runtime")
    m.add_argument("--role", required=True)
    m.add_argument("--session", default="", help="Current session harness id")

    s = sub.add_parser(
        "resolve",
        help="Merge profile for a staff: runtime + tier + model + effort (+ hop mode vs session)",
    )
    s.add_argument("--role", required=True)
    s.add_argument(
        "--session",
        default="",
        help="Current session harness (default MARLIN_HARNESS / router default)",
    )

    r = sub.add_parser("roles", help="List SoT roles for one generated runtime")
    r.add_argument("--runtime", default="")

    sub.add_parser("check", help="Preflight CLI bins for mapped runtimes")

    def add_hop_flags(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--from", dest="from_role", default="ceo")
        sp.add_argument("--to", required=True)
        sp.add_argument("--goal", default="")
        sp.add_argument(
            "--session",
            default="",
            help="Current session runtime (default MARLIN_HARNESS)",
        )
        sp.add_argument(
            "--execute",
            action="store_true",
            help="Actually invoke cross-runtime CLI (default: plan + handoff file only)",
        )

    a = sub.add_parser("assign", help="Plan/execute Assign with router (alias of hop semantics)")
    add_hop_flags(a)

    h = sub.add_parser(
        "hop",
        help="Hop to staff: print profiles; native if same runtime, else CLI bridge",
    )
    add_hop_flags(h)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "match":
        return cmd_match(args)
    if args.cmd == "resolve":
        return cmd_resolve(args)
    if args.cmd == "roles":
        return cmd_roles(args)
    if args.cmd == "check":
        return cmd_check(args)
    if args.cmd == "assign":
        return cmd_assign(args)
    if args.cmd == "hop":
        return cmd_hop(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
