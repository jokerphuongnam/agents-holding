#!/usr/bin/env python3
"""Promote safe defaults FROM one subsidiary company INTO holding templates.

Inverse of update_company_defaults.py:

  company (reference)  →  templates/  →  (later) update-company --all

Promotes the same managed set:
  - system/skills/defaults/marlin-hop/scripts/** + SKILL.md  → templates/hop-reference/
  - system/install/company_os.sh                            → templates/install/
  - FORMULA.md                                              → templates/company/
  - system/harness/*                                        → templates/company/system/harness/
    (re-generalize {{COMPANY_SLUG}} and {{EFFORT_*}})

Never copies: staffs/, customs/, hop data/, COMPANY*.md, cache/, CTO_TECH_SEED.md
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HOP_SRC_PREFIX = Path("system/skills/defaults/marlin-hop")
HARNESS_SRC_PREFIX = Path("system/harness")
COMPANY_OS_REL = Path("system/install/company_os.sh")
FORMULA_REL = Path("FORMULA.md")

HARNESS_NAMES = (
    "grok.toml",
    "codex.toml",
    "claude.toml",
    "runtime_router.toml",
    "README.md",
)

SKIP_DIR_NAMES = frozenset({"data", "agents", "__pycache__"})
EFFORT_KEYS = ("dispatch", "low", "medium", "high", "xhigh")


@dataclass
class PromotePlan:
    rel_template: str  # path under templates/
    desired: bytes
    status: str = "ok"  # ok | update | add | skip
    detail: str = ""


@dataclass
class PromoteStats:
    updated: int = 0
    added: int = 0
    ok: int = 0


@dataclass
class PromoteResult:
    source: Path
    agents_home: Path
    rows: list[PromotePlan] = field(default_factory=list)
    stats: PromoteStats = field(default_factory=PromoteStats)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path: Path) -> Optional[bytes]:
    if not path.is_file():
        return None
    return path.read_bytes()


def holding_install_dir() -> Path:
    return Path(__file__).resolve().parent


def default_agents_home() -> Path:
    return holding_install_dir().parents[3]


def generalize_harness(text: str, company_slug: str) -> str:
    """Turn instance harness back into template placeholders."""
    slug = company_slug.strip()
    if slug:
        text = text.replace(f".agents/{slug}/", ".agents/{{COMPANY_SLUG}}/")
        # claude-style relative paths
        text = text.replace(
            f"../.agents/{slug}/", "../.agents/{{COMPANY_SLUG}}/"
        )

    # Re-placeholder [tier_to_effort] values
    def repl_block(m: re.Match[str]) -> str:
        head, block = m.group(1), m.group(2)
        for key in EFFORT_KEYS:
            block, n = re.subn(
                rf'(?m)^(\s*{re.escape(key)}\s*=\s*")[^"]*(")',
                rf"\1{{{{EFFORT_{key.upper()}}}}}\2",
                block,
            )
            if not n:
                # ensure key exists with placeholder
                block = block.rstrip() + f'\n{key} = "{{{{EFFORT_{key.upper()}}}}}"\n'
        return head + block

    text = re.sub(
        r"(\[tier_to_effort\]\s*\n)(.*?)(?=\n\[|\Z)",
        repl_block,
        text,
        count=1,
        flags=re.S,
    )
    return text


def iter_company_hop_files(company: Path) -> list[tuple[str, Path]]:
    """Yield (rel under marlin-hop, abs path) from company."""
    root = company / HOP_SRC_PREFIX
    out: list[tuple[str, Path]] = []
    if not root.is_dir():
        return out
    skill = root / "SKILL.md"
    if skill.is_file():
        out.append(("SKILL.md", skill))
    scripts = root / "scripts"
    if scripts.is_dir():
        for path in sorted(scripts.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            parts = Path(rel).parts
            if any(p in SKIP_DIR_NAMES for p in parts):
                continue
            if path.suffix == ".pyc" or path.name == ".DS_Store":
                continue
            out.append((rel, path))
    return out


def classify_write(existing: Optional[bytes], desired: bytes) -> tuple[str, str]:
    if existing is None:
        return "add", "missing-in-templates"
    if existing == desired:
        return "ok", "unchanged"
    return "update", "differs"


def build_plans(source: Path, agents_home: Path) -> list[PromotePlan]:
    source = source.resolve()
    slug = source.name
    templates = agents_home / "templates"
    plans: list[PromotePlan] = []

    # 1) hop → templates/hop-reference
    for rel_under_hop, src in iter_company_hop_files(source):
        desired = src.read_bytes()
        dest_rel = f"hop-reference/{rel_under_hop}"
        existing = read_bytes(templates / dest_rel)
        status, detail = classify_write(existing, desired)
        plans.append(
            PromotePlan(
                rel_template=dest_rel,
                desired=desired,
                status=status,
                detail=detail,
            )
        )

    # 2) company_os.sh
    os_src = source / COMPANY_OS_REL
    if os_src.is_file():
        desired = os_src.read_bytes()
        dest_rel = "install/company_os.sh"
        existing = read_bytes(templates / dest_rel)
        status, detail = classify_write(existing, desired)
        plans.append(
            PromotePlan(
                rel_template=dest_rel,
                desired=desired,
                status=status,
                detail=detail,
            )
        )

    # 3) FORMULA.md
    formula = source / FORMULA_REL
    if formula.is_file():
        desired = formula.read_bytes()
        dest_rel = "company/FORMULA.md"
        existing = read_bytes(templates / dest_rel)
        status, detail = classify_write(existing, desired)
        plans.append(
            PromotePlan(
                rel_template=dest_rel,
                desired=desired,
                status=status,
                detail=detail,
            )
        )

    # 4) harness → generalize placeholders
    for name in HARNESS_NAMES:
        src = source / HARNESS_SRC_PREFIX / name
        if not src.is_file():
            continue
        raw = src.read_bytes()
        if name.endswith(".toml"):
            desired = generalize_harness(raw.decode("utf-8"), slug).encode("utf-8")
        else:
            desired = raw
        dest_rel = f"company/system/harness/{name}"
        existing = read_bytes(templates / dest_rel)
        status, detail = classify_write(existing, desired)
        plans.append(
            PromotePlan(
                rel_template=dest_rel,
                desired=desired,
                status=status,
                detail=detail,
            )
        )

    return plans


def apply_plans(
    agents_home: Path,
    plans: list[PromotePlan],
    *,
    dry_run: bool,
) -> PromoteStats:
    stats = PromoteStats()
    templates = agents_home / "templates"
    for plan in plans:
        if plan.status == "ok":
            stats.ok += 1
            continue
        if plan.status == "add":
            stats.added += 1
        elif plan.status == "update":
            stats.updated += 1
        else:
            continue
        if dry_run:
            continue
        target = templates / plan.rel_template
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(plan.desired)
        if plan.rel_template.endswith("company_os.sh"):
            target.chmod(target.stat().st_mode | 0o111)
    return stats


def print_report(result: PromoteResult) -> None:
    print("status\trel_template\tdetail")
    for plan in result.rows:
        print(f"{plan.status}\t{plan.rel_template}\t{plan.detail}")
    s = result.stats
    print(
        "summary\t"
        f"updated={s.updated}\tadded={s.added}\tok={s.ok}\t"
        f"from={result.source}\tagents_home={result.agents_home}"
    )


def promote(
    source: Path,
    agents_home: Path,
    *,
    dry_run: bool,
) -> PromoteResult:
    source = source.resolve()
    agents_home = agents_home.resolve()
    if not source.is_dir() or not (source / "system").is_dir():
        raise SystemExit(f"error: not a Company OS tree: {source}")
    if not (agents_home / "templates").is_dir():
        raise SystemExit(f"error: templates/ missing under {agents_home}")

    plans = build_plans(source, agents_home)
    stats = apply_plans(agents_home, plans, dry_run=dry_run)
    return PromoteResult(
        source=source, agents_home=agents_home, rows=plans, stats=stats
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="promote_company_defaults.py",
        description=(
            "Mirror safe defaults from one company into templates/ "
            "(then distribute with update-company.sh)."
        ),
    )
    p.add_argument(
        "--from",
        dest="source",
        required=True,
        help="Reference company path (…/<slug>-company)",
    )
    p.add_argument(
        "--agents-home",
        default="",
        help="Agents home with templates/ (default: parent of holding)",
    )
    p.add_argument("--dry-run", action="store_true", help="Report only")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    agents_home = (
        Path(args.agents_home).expanduser().resolve()
        if args.agents_home
        else default_agents_home()
    )
    source = Path(args.source).expanduser().resolve()
    result = promote(source, agents_home, dry_run=args.dry_run)
    print_report(result)
    if not args.dry_run and (result.stats.updated or result.stats.added):
        print("next\tcommit templates if using author checkout")
        print("next\tinstall_holding_system.sh --dest ~/.agents   # if promoted to author repo")
        print("next\tupdate-company.sh --all --dry-run")
        print("next\tupdate-company.sh --all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
