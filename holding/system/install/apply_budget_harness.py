#!/usr/bin/env python3
"""Apply holding budget to a subsidiary's harness/*.toml and hop agents.tsv.

Used by create-company and by holding-hr on re-budget (poor→low, rich→high).
Plan writers (po-*) always get always_max_tier from policy. Leads stay dispatch.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def normalize_budget(raw: str, policy: dict) -> str:
    s = (raw or "").strip().lower()
    aliases = (policy or {}).get("nl_aliases") or {}
    for level, words in aliases.items():
        if s == level or s in {w.lower() for w in words}:
            return level
    # substring match for phrases like "too poor" / "we are rich"
    for level, words in aliases.items():
        for w in words:
            if w.lower() in s:
                return level
    if s in ("low", "medium", "high"):
        return s
    raise SystemExit(f"error: unknown budget {raw!r} (want low|medium|high )")


def patch_tier_to_effort(text: str, eff: dict[str, str]) -> str:
    for k, v in eff.items():
        text = text.replace(f"{{{{EFFORT_{k.upper()}}}}}", v)

    m = re.search(r"(\[tier_to_effort\]\s*\n)(.*?)(?=\n\[|\Z)", text, re.S)
    if not m:
        return text
    head, block = m.group(1), m.group(2)
    for k, v in eff.items():
        block_new, n = re.subn(
            rf'(?m)^(\s*{re.escape(k)}\s*=\s*")[^"]*(")',
            rf"\1{v}\2",
            block,
        )
        if n:
            block = block_new
        else:
            block = block.rstrip() + f'\n{k} = "{v}"\n'
    return text[: m.start()] + head + block + text[m.end() :]


def apply_agents_tsv(path: Path, overrides: dict[str, str]) -> int:
    if not path.is_file():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return 0
    header = lines[0].split("\t")
    if "name" not in header or "tier" not in header:
        return 0
    i_name, i_tier = header.index("name"), header.index("tier")
    out = [lines[0]]
    changed = 0
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = line.split("\t")
        while len(cells) < len(header):
            cells.append("")
        name = cells[i_name]
        if name in overrides and cells[i_tier] != overrides[name]:
            cells[i_tier] = overrides[name]
            changed += 1
        out.append("\t".join(cells))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def merge_overrides(budget_cfg: dict, policy: dict) -> dict[str, str]:
    overrides = dict(budget_cfg.get("agents_tsv_tier_overrides") or {})
    max_roles = policy.get("always_max_roles") or ["po-modify", "po-new"]
    max_tier = policy.get("always_max_tier") or "xhigh"
    for role in max_roles:
        overrides[role] = max_tier
    return overrides


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default="", help="subsidiary company root")
    ap.add_argument("--budget", required=True, help="low|medium|high or NL alias")
    ap.add_argument("--budget-json", required=True)
    ap.add_argument("--normalize-only", action="store_true", help="print normalized budget and exit")
    args = ap.parse_args()

    cfg = json.loads(Path(args.budget_json).read_text(encoding="utf-8"))
    policy = cfg.get("policy") or {}
    budget = normalize_budget(args.budget, policy)
    if args.normalize_only:
        print(budget)
        return 0

    if not args.dest:
        print("error: --dest required unless --normalize-only", file=sys.stderr)
        return 2
    if budget not in cfg or budget == "policy":
        print(f"error: missing budget key {budget}", file=sys.stderr)
        return 1

    dest = Path(args.dest)
    budget_cfg = cfg[budget]
    eff = budget_cfg["tier_to_effort"]
    overrides = merge_overrides(budget_cfg, policy)

    harness = dest / "system" / "harness"
    n_toml = 0
    if harness.is_dir():
        for toml in sorted(harness.glob("*.toml")):
            text = toml.read_text(encoding="utf-8")
            new = patch_tier_to_effort(text, eff)
            if new != text:
                toml.write_text(new, encoding="utf-8")
            n_toml += 1

    agents = (
        dest
        / "system"
        / "skills"
        / "defaults"
        / "marlin-hop"
        / "data"
        / "agents.tsv"
    )
    n_agents = apply_agents_tsv(agents, overrides)

    # Record last applied budget for HR/ceo
    meta = dest / "system" / "install" / "BUDGET_APPLIED.json"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(
        json.dumps(
            {
                "budget": budget,
                "tier_to_effort": eff,
                "agents_tsv_tier_overrides": overrides,
                "note": budget_cfg.get("note"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"[apply_budget_harness] budget={budget} harness={n_toml} agents_tier_updates={n_agents}")
    print(f"[apply_budget_harness] always_max={policy.get('always_max_roles')} → {policy.get('always_max_tier')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
