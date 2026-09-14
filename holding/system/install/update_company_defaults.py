#!/usr/bin/env python3
"""Sync safe template defaults into an existing subsidiary Company OS.

Updates hop scripts, company_os.sh, FORMULA.md, and (optionally) budget-rendered
harness files. Never touches staffs/, customs/, hop data/, COMPANY*.md, or cache
(except cache/template_sync.json).

Fingerprint rules (per managed file):
  missing locally                         → add
  local == template                       → ok (refresh manifest)
  local == origin and template != origin  → update (safe)
  local != origin and local != template   → diverge (skip)
  no origin and local != template         → review (skip)

--force / --force-file overwrite diverge|review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

# Reuse budget rendering helpers + hop self_test soften (same as create-company)
from apply_budget_harness import (  # type: ignore
    normalize_budget,
    patch_tier_to_effort,
)
from seed_company_hop_data import soften_hop_self_test  # type: ignore

MANIFEST_NAME = "template_sync.json"
MANIFEST_VERSION = 1

HOP_DEST_PREFIX = Path("system/skills/defaults/marlin-hop")
HARNESS_DEST_PREFIX = Path("system/harness")
COMPANY_OS_REL = Path("system/install/company_os.sh")
FORMULA_REL = Path("FORMULA.md")

HARNESS_NAMES = (
    "grok.toml",
    "codex.toml",
    "claude.toml",
    "runtime_router.toml",
    "README.md",
)

SKIP_HOP_DIR_NAMES = frozenset({"data", "agents", "__pycache__"})


@dataclass
class FilePlan:
    rel: str
    source_label: str
    desired: bytes
    status: str = "ok"
    detail: str = ""


@dataclass
class SyncStats:
    updated: int = 0
    added: int = 0
    ok: int = 0
    diverge: int = 0
    review: int = 0
    forced: int = 0
    skipped_missing_dest: int = 0


@dataclass
class SyncResult:
    dest: Path
    rows: list[FilePlan] = field(default_factory=list)
    stats: SyncStats = field(default_factory=SyncStats)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path: Path) -> Optional[bytes]:
    if not path.is_file():
        return None
    return path.read_bytes()


def load_manifest(dest: Path) -> dict:
    path = dest / "cache" / MANIFEST_NAME
    if not path.is_file():
        return {"version": MANIFEST_VERSION, "synced_at": "", "files": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": MANIFEST_VERSION, "synced_at": "", "files": {}}
    if not isinstance(data, dict):
        return {"version": MANIFEST_VERSION, "synced_at": "", "files": {}}
    files = data.get("files") or {}
    if not isinstance(files, dict):
        files = {}
    return {
        "version": int(data.get("version") or MANIFEST_VERSION),
        "synced_at": str(data.get("synced_at") or ""),
        "files": files,
    }


def save_manifest(dest: Path, manifest: dict) -> None:
    cache = dest / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / MANIFEST_NAME
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def origin_sha(manifest: dict, rel: str) -> Optional[str]:
    entry = (manifest.get("files") or {}).get(rel)
    if not isinstance(entry, dict):
        return None
    sha = entry.get("sha256")
    return str(sha) if sha else None


def set_origin(manifest: dict, rel: str, sha: str, source: str) -> None:
    files = manifest.setdefault("files", {})
    files[rel] = {"sha256": sha, "source": source}


def holding_install_dir() -> Path:
    return Path(__file__).resolve().parent


def default_agents_home() -> Path:
    # …/holding/system/install → system → holding → agents-home (~/.agents or repo root)
    return holding_install_dir().parents[3]


def resolve_budget(dest: Path, budget_json: Path, explicit: str = "") -> str:
    policy: dict = {}
    if budget_json.is_file():
        try:
            cfg = json.loads(budget_json.read_text(encoding="utf-8"))
            policy = cfg.get("policy") or {}
        except (json.JSONDecodeError, OSError):
            cfg = {}
    else:
        cfg = {}

    if explicit.strip():
        return normalize_budget(explicit, policy)

    meta = dest / "system" / "install" / "BUDGET_APPLIED.json"
    if meta.is_file():
        try:
            applied = json.loads(meta.read_text(encoding="utf-8"))
            b = str(applied.get("budget") or "").strip()
            if b:
                return normalize_budget(b, policy)
        except (json.JSONDecodeError, OSError, SystemExit):
            pass

    # Fallback medium
    return "medium"


def render_harness_bytes(
    template_harness: Path,
    budget: str,
    budget_json: Path,
    company_slug: str,
) -> dict[str, bytes]:
    """Return rel-name → rendered bytes for managed harness files."""
    out: dict[str, bytes] = {}
    if not template_harness.is_dir():
        return out
    cfg = json.loads(budget_json.read_text(encoding="utf-8"))
    if budget not in cfg or budget == "policy":
        raise SystemExit(f"error: missing budget key {budget} in {budget_json}")
    budget_cfg = cfg[budget]
    eff = budget_cfg["tier_to_effort"]
    slug = company_slug.strip() or "{{COMPANY_SLUG}}"

    for name in HARNESS_NAMES:
        src = template_harness / name
        if not src.is_file():
            continue
        raw = src.read_bytes()
        if name.endswith(".toml"):
            text = raw.decode("utf-8")
            text = text.replace("{{COMPANY_SLUG}}", slug)
            text = patch_tier_to_effort(text, eff)
            out[name] = text.encode("utf-8")
        else:
            out[name] = raw
    return out


def iter_hop_files(hop_ref: Path) -> Iterable[tuple[str, Path]]:
    """Yield (rel_under_marlin_hop, absolute source path)."""
    if not hop_ref.is_dir():
        return
    # SKILL.md at hop root
    skill = hop_ref / "SKILL.md"
    if skill.is_file():
        yield ("SKILL.md", skill)
    scripts = hop_ref / "scripts"
    if not scripts.is_dir():
        return
    for path in sorted(scripts.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(hop_ref).as_posix()
        # skip junk
        parts = Path(rel).parts
        if any(p in SKIP_HOP_DIR_NAMES for p in parts):
            continue
        if path.suffix in {".pyc"} or path.name == ".DS_Store":
            continue
        yield (rel, path)


def classify(
    local: Optional[bytes],
    desired: bytes,
    origin: Optional[str],
    force: bool,
) -> tuple[str, str]:
    desired_sha = sha256_bytes(desired)
    if local is None:
        return "add", "missing"
    local_sha = sha256_bytes(local)
    if local_sha == desired_sha:
        return "ok", "matches-template"
    if force:
        return "update", "forced"
    if origin and local_sha == origin:
        return "update", "origin-matches-safe"
    if origin and local_sha != origin:
        return "diverge", "local!=origin"
    return "review", "no-manifest"


def build_plans(
    dest: Path,
    agents_home: Path,
    *,
    skip_harness: bool,
    budget: str,
    budget_json: Path,
    force_all: bool,
    force_files: set[str],
    manifest: dict,
) -> list[FilePlan]:
    plans: list[FilePlan] = []
    templates = agents_home / "templates"

    # 1) hop-reference → marlin-hop (exclude data/agents)
    # hop.py desired matches create-company: template + soften_hop_self_test
    hop_ref = templates / "hop-reference"
    for rel_under_hop, src in iter_hop_files(hop_ref):
        rel = (HOP_DEST_PREFIX / rel_under_hop).as_posix()
        desired = src.read_bytes()
        if rel_under_hop == "scripts/hop.py" or rel_under_hop.endswith("/hop.py"):
            desired = soften_hop_self_test(desired.decode("utf-8")).encode("utf-8")
        force = force_all or rel in force_files
        local = read_bytes(dest / rel)
        status, detail = classify(local, desired, origin_sha(manifest, rel), force)
        plans.append(
            FilePlan(
                rel=rel,
                source_label=f"templates/hop-reference/{rel_under_hop}",
                desired=desired,
                status=status,
                detail=detail,
            )
        )

    # 2) company_os.sh
    os_src = templates / "install" / "company_os.sh"
    if os_src.is_file():
        rel = COMPANY_OS_REL.as_posix()
        desired = os_src.read_bytes()
        force = force_all or rel in force_files
        local = read_bytes(dest / rel)
        status, detail = classify(local, desired, origin_sha(manifest, rel), force)
        plans.append(
            FilePlan(
                rel=rel,
                source_label="templates/install/company_os.sh",
                desired=desired,
                status=status,
                detail=detail,
            )
        )

    # 3) FORMULA.md
    formula_src = templates / "company" / "FORMULA.md"
    if formula_src.is_file():
        rel = FORMULA_REL.as_posix()
        desired = formula_src.read_bytes()
        force = force_all or rel in force_files
        local = read_bytes(dest / rel)
        status, detail = classify(local, desired, origin_sha(manifest, rel), force)
        plans.append(
            FilePlan(
                rel=rel,
                source_label="templates/company/FORMULA.md",
                desired=desired,
                status=status,
                detail=detail,
            )
        )

    # 4) harness (budget-rendered + COMPANY_SLUG)
    if not skip_harness:
        rendered = render_harness_bytes(
            templates / "company" / "system" / "harness",
            budget=budget,
            budget_json=budget_json,
            company_slug=dest.name,
        )
        for name, desired in rendered.items():
            rel = (HARNESS_DEST_PREFIX / name).as_posix()
            force = force_all or rel in force_files
            local = read_bytes(dest / rel)
            status, detail = classify(local, desired, origin_sha(manifest, rel), force)
            plans.append(
                FilePlan(
                    rel=rel,
                    source_label=f"templates/company/system/harness/{name} (budget={budget})",
                    desired=desired,
                    status=status,
                    detail=detail,
                )
            )

    return plans


def apply_plans(
    dest: Path,
    plans: list[FilePlan],
    manifest: dict,
    *,
    dry_run: bool,
) -> SyncStats:
    stats = SyncStats()
    for plan in plans:
        if plan.status == "ok":
            stats.ok += 1
            set_origin(manifest, plan.rel, sha256_bytes(plan.desired), plan.source_label)
            continue
        if plan.status == "diverge":
            stats.diverge += 1
            continue
        if plan.status == "review":
            stats.review += 1
            continue
        if plan.status == "add":
            stats.added += 1
        elif plan.status == "update":
            if plan.detail == "forced":
                stats.forced += 1
            stats.updated += 1
        else:
            continue

        if dry_run:
            continue

        target = dest / plan.rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(plan.desired)
        if plan.rel.endswith("company_os.sh"):
            target.chmod(target.stat().st_mode | 0o111)
        set_origin(manifest, plan.rel, sha256_bytes(plan.desired), plan.source_label)

    if not dry_run:
        manifest["version"] = MANIFEST_VERSION
        manifest["synced_at"] = utc_now()
        save_manifest(dest, manifest)
    return stats


def print_report(result: SyncResult) -> None:
    print("status\trel_path\tdetail")
    for plan in result.rows:
        print(f"{plan.status}\t{plan.rel}\t{plan.detail}")
    s = result.stats
    print(
        "summary\t"
        f"updated={s.updated}\tadded={s.added}\tok={s.ok}\t"
        f"diverge={s.diverge}\treview={s.review}\tforced={s.forced}\t"
        f"dest={result.dest}"
    )


def sync_one(
    dest: Path,
    agents_home: Path,
    *,
    dry_run: bool,
    skip_harness: bool,
    budget_arg: str,
    force_all: bool,
    force_files: set[str],
) -> SyncResult:
    dest = dest.resolve()
    if not dest.is_dir():
        raise SystemExit(f"error: company dest not found: {dest}")
    if not (dest / "system").is_dir():
        raise SystemExit(f"error: not a Company OS tree (missing system/): {dest}")

    budget_json = agents_home / "holding" / "system" / "install" / "budget_tiers.json"
    if not budget_json.is_file():
        # author-repo layout: holding next to templates under agents-home
        alt = holding_install_dir() / "budget_tiers.json"
        budget_json = alt if alt.is_file() else budget_json
    if not budget_json.is_file():
        raise SystemExit(f"error: budget_tiers.json not found under {agents_home}")

    budget = resolve_budget(dest, budget_json, budget_arg)
    manifest = load_manifest(dest)
    plans = build_plans(
        dest,
        agents_home,
        skip_harness=skip_harness,
        budget=budget,
        budget_json=budget_json,
        force_all=force_all,
        force_files=force_files,
        manifest=manifest,
    )
    # Work on a copy of manifest so dry-run does not mutate disk; apply_plans
    # still updates the in-memory copy for ok/update/add bookkeeping.
    stats = apply_plans(dest, plans, manifest, dry_run=dry_run)
    return SyncResult(dest=dest, rows=plans, stats=stats)


def write_manifest_snapshot(
    dest: Path,
    agents_home: Path,
    *,
    skip_harness: bool = False,
    budget_arg: str = "",
) -> Path:
    """Record origin only when local == desired (create-company / safe bootstrap).

    Files that already differ from the template are left without an origin entry
    so a later update reports ``review`` instead of silently overwriting them.
    """
    dest = dest.resolve()
    budget_json = holding_install_dir() / "budget_tiers.json"
    if not budget_json.is_file():
        budget_json = agents_home / "holding" / "system" / "install" / "budget_tiers.json"
    budget = resolve_budget(dest, budget_json, budget_arg)
    manifest = load_manifest(dest)
    plans = build_plans(
        dest,
        agents_home,
        skip_harness=skip_harness,
        budget=budget,
        budget_json=budget_json,
        force_all=False,
        force_files=set(),
        manifest=manifest,
    )
    matched = skipped = 0
    for plan in plans:
        local = read_bytes(dest / plan.rel)
        if local is None:
            skipped += 1
            continue
        if sha256_bytes(local) == sha256_bytes(plan.desired):
            set_origin(manifest, plan.rel, sha256_bytes(plan.desired), plan.source_label)
            matched += 1
        else:
            # Keep any prior origin only if it still equals local; else drop so
            # status stays review (do not treat divergent local as "stock").
            prev = origin_sha(manifest, plan.rel)
            if prev and prev == sha256_bytes(local):
                skipped += 1
            else:
                files = manifest.setdefault("files", {})
                files.pop(plan.rel, None)
                skipped += 1
    manifest["version"] = MANIFEST_VERSION
    manifest["synced_at"] = utc_now()
    save_manifest(dest, manifest)
    print(
        f"[update_company_defaults] manifest matched={matched} unmatched={skipped}"
    )
    return dest / "cache" / MANIFEST_NAME


def registry_active_paths(db: Optional[Path] = None) -> list[Path]:
    """Return company_path for active registry rows that exist on disk."""
    # Import lazily to avoid circular import issues when shipped side-by-side
    try:
        from company_registry import (  # type: ignore
            STATUS_ACTIVE,
            connect,
            default_db_path,
            refresh_missing,
        )
    except ImportError:
        return []

    path = db or default_db_path()
    if not path.is_file():
        return []
    conn = connect(path)
    try:
        rows = conn.execute(
            "SELECT * FROM companies WHERE status = ? ORDER BY slug, project_root",
            (STATUS_ACTIVE,),
        ).fetchall()
        out: list[Path] = []
        for r in rows:
            st = refresh_missing(conn, r)
            if st != STATUS_ACTIVE:
                continue
            cp = Path(r["company_path"])
            if cp.is_dir():
                out.append(cp.resolve())
        return out
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="update_company_defaults.py",
        description=(
            "Sync safe template defaults into existing Company OS trees. "
            "Keeps staffs/, customs/, hop data/, and company docs."
        ),
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dest", default="", help="Path to one …/<slug>-company/")
    g.add_argument(
        "--all",
        action="store_true",
        help="Update every active company in the local registry",
    )
    g.add_argument(
        "--write-manifest-only",
        metavar="DEST",
        default="",
        help="Record fingerprint from current files (create-company hook)",
    )
    p.add_argument(
        "--agents-home",
        default="",
        help="Agents home containing templates/ + holding/ (default: parent of holding)",
    )
    p.add_argument("--dry-run", action="store_true", help="Report only; do not write")
    p.add_argument("--force", action="store_true", help="Overwrite diverge/review")
    p.add_argument(
        "--force-file",
        action="append",
        default=[],
        metavar="REL",
        help="Force one relative path (repeatable)",
    )
    p.add_argument("--skip-harness", action="store_true", help="Do not sync harness/")
    p.add_argument(
        "--budget",
        default="",
        help="Override budget for harness render (default: BUDGET_APPLIED.json)",
    )
    p.add_argument(
        "--db",
        default="",
        help="Override company registry sqlite (for --all)",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    agents_home = (
        Path(args.agents_home).expanduser().resolve()
        if args.agents_home
        else default_agents_home()
    )
    if not (agents_home / "templates").is_dir():
        # When running from author checkout: agents-home is repo root
        # (templates/ + holding/ live there). default_agents_home() from
        # holding/system/install → parents[2] == repo root. Good.
        print(f"error: templates/ not found under {agents_home}", file=sys.stderr)
        return 1

    force_files = {f.strip().lstrip("./") for f in args.force_file if f.strip()}

    if args.write_manifest_only:
        dest = Path(args.write_manifest_only).expanduser().resolve()
        path = write_manifest_snapshot(
            dest,
            agents_home,
            skip_harness=args.skip_harness,
            budget_arg=args.budget,
        )
        print(f"[update_company_defaults] wrote manifest {path}")
        return 0

    dests: list[Path] = []
    if args.all:
        db = Path(args.db).expanduser().resolve() if args.db else None
        dests = registry_active_paths(db)
        if not dests:
            print(
                "error: no active companies in registry (run company_registry.py scan --register)",
                file=sys.stderr,
            )
            return 1
    else:
        dests = [Path(args.dest).expanduser().resolve()]

    any_blockers = False
    for dest in dests:
        print(f"company\t{dest}")
        try:
            result = sync_one(
                dest,
                agents_home,
                dry_run=args.dry_run,
                skip_harness=args.skip_harness,
                budget_arg=args.budget,
                force_all=bool(args.force),
                force_files=force_files,
            )
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            print(f"error\t{dest}\t{e}", file=sys.stderr)
            if code:
                any_blockers = True
            continue
        print_report(result)
        if result.stats.diverge or result.stats.review:
            any_blockers = True
        if not args.dry_run and (result.stats.updated or result.stats.added):
            print(
                f"next\t{dest}/system/install/company_os.sh all"
            )

    return 2 if any_blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
