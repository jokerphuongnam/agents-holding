#!/usr/bin/env python3
"""Generate runtime agent views from Company OS + a harness profile.

Company SoT: `.agents/marlin-language-company/system/staffs/**`, `agents.tsv` (portable — no vendor model).
Harness: `.agents/marlin-language-company/system/harness/<id>.toml` declares `layout` + paths + tier maps.
Setup one harness → generate **that** harness's agents/boot only.

Layouts (declared in toml, not hardcoded per vendor name):
  flat          — vendor cards under export_dir + flat symlinks
  agents_md     — single AGENTS.md boot + roster
  tree_symlink  — dir/file symlinks into a runtime folder (+ optional readme)

Usage:
  python3 export_harness.py --list
  python3 export_harness.py --to grok
  python3 export_harness.py --to codex
  python3 export_harness.py --to all    # every harness/*.toml
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import agents_home, company_relposix, load_agents, load_tsv

try:
    import tomllib
except ModuleNotFoundError:  # py<3.11
    import tomli as tomllib  # type: ignore


def repo_root(home: Path) -> Path:
    # home = <repo>/.agents/marlin-language-company
    if home.parent.name == ".agents":
        return home.parent.parent
    return home.parent


def load_harness(home: Path, harness_id: str) -> dict:
    path = home / "system" / "harness" / f"{harness_id}.toml"
    if not path.is_file():
        raise SystemExit(f"missing harness profile: {path}")
    cfg = tomllib.loads(path.read_text(encoding="utf-8"))
    cfg.setdefault("id", harness_id)
    return cfg


def discovered_harnesses(home: Path) -> list[str]:
    harness_dir = home / "system" / "harness"
    if not harness_dir.is_dir():
        return []
    return sorted(p.stem for p in harness_dir.glob("*.toml"))


def agent_bodies(home: Path) -> dict[str, Path]:
    by_name: dict[str, Path] = {}
    for p in (home / "system" / "staffs").rglob("*.md"):
        if p.name == "ORG.md":
            continue
        # Per-agent custom skills/scripts are not role cards (ORG layout).
        if "skills" in p.parts or "scripts" in p.parts:
            continue
        text = p.read_text(encoding="utf-8")
        name = None
        for line in text.splitlines():
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
                break
        if name:
            by_name[name] = p
    return by_name


def split_md(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end < 0:
        return "", text
    return text[4:end], text[end + 5 :]


def resolve_tier_maps(cfg: dict, tier: str) -> tuple[str, str]:
    models = cfg.get("tier_to_model") or {}
    efforts = cfg.get("tier_to_effort") or {}
    model = models.get(tier) or models.get("medium") or "default"
    effort = efforts.get(tier) or efforts.get("medium") or "medium"
    return str(model), str(effort)


def normalize_sot_portable(home: Path) -> int:
    """Ensure Company SoT frontmatter has no vendor model/effort."""
    rows = load_tsv("agents.tsv")
    bodies = agent_bodies(home)
    n = 0
    for r in rows:
        name = r.get("name")
        if not name or name not in bodies:
            continue
        p = bodies[name]
        _, body = split_md(p.read_text(encoding="utf-8"))
        tier = r.get("tier") or "low"
        lines = [
            "---",
            f"name: {name}",
            f"description: {r.get('blurb', '')}",
            f"tier: {tier}",
            f"permission_mode: {r.get('permission_mode', 'default')}",
        ]
        cap = r.get("capability_mode") or ""
        if cap:
            lines.append(f"capability_mode: {cap}")
        lines += ["---", ""]
        p.write_text("\n".join(lines) + body.lstrip("\n"))
        n += 1
    return n


def _resolve_path(root: Path, raw: str) -> Path:
    p = Path(os.path.expanduser(str(raw)))
    return p if p.is_absolute() else root / p


def _symlink(link: Path, target: Path | str, *, allow_replace_file: bool = True) -> None:
    target_s = str(target)
    if link.is_symlink() or link.exists():
        if link.is_symlink():
            link.unlink()
        elif link.is_dir() and not any(link.iterdir()):
            link.rmdir()
        elif link.is_dir():
            print(f"skip {link}: real non-empty directory", file=sys.stderr)
            return
        elif allow_replace_file:
            link.unlink()
        else:
            print(f"skip {link}: exists", file=sys.stderr)
            return
    link.symlink_to(target_s)


def layout_flat(home: Path, cfg: dict) -> int:
    """Generate per-role vendor cards + flat symlinks (e.g. Grok)."""
    hid = cfg.get("id", "harness")
    rows = load_tsv("agents.tsv")
    bodies = agent_bodies(home)
    fm_extra = cfg.get("frontmatter") or {}
    root = repo_root(home)
    paths = cfg.get("paths") or {}
    export_rel = paths.get("export_dir") or f".agents/marlin-language-company/cache/export/{hid}"
    export_dir = _resolve_path(root, export_rel)
    export_dir.mkdir(parents=True, exist_ok=True)

    n = 0
    for r in rows:
        name = r.get("name")
        if not name or name not in bodies:
            if name:
                print(f"{hid}: missing SoT .md for {name}", file=sys.stderr)
            continue
        _, body = split_md(bodies[name].read_text(encoding="utf-8"))
        tier = r.get("tier") or "low"
        model, effort = resolve_tier_maps(cfg, tier)
        cap = r.get("capability_mode") or ""
        lines = [
            "---",
            f"name: {name}",
            f"description: {r.get('blurb', '')}",
            f"prompt_mode: {fm_extra.get('prompt_mode', 'full')}",
            f"model: {model}",
            f"permission_mode: {r.get('permission_mode', 'default')}",
            f"effort: {effort}",
        ]
        if cap:
            lines.append(f"capability_mode: {cap}")
        lines.append(f"tier: {tier}")
        for key in ("discoverSkills", "inheritSkills", "agents_md"):
            if key in fm_extra:
                val = fm_extra[key]
                if isinstance(val, bool):
                    val = "true" if val else "false"
                lines.append(f"{key}: {val}")
        lines += ["---", ""]
        (export_dir / f"{name}.md").write_text("\n".join(lines) + body.lstrip("\n"))
        n += 1

    (export_dir / "README.md").write_text(
        f"# Generated `{hid}` agent cards\n\n"
        f"Do not edit by hand. Regenerated by:\n\n"
        f"```bash\n"
        f"python3 .agents/marlin-language-company/system/skills/defaults/marlin-hop/scripts/export_harness.py --to {hid}\n"
        f"# or: .agents/marlin-language-company/system/install/company_os.sh {hid}\n"
        f"```\n\n"
        f"Company SoT (portable): `.agents/marlin-language-company/system/staffs/**`\n",
        encoding="utf-8",
    )

    export_names = {p.name for p in export_dir.glob("*.md") if p.name != "README.md"}
    for key in ("repo_flat_agents", "user_flat_agents"):
        raw = paths.get(key)
        if not raw:
            continue
        dest = _resolve_path(root, str(raw))
        dest.mkdir(parents=True, exist_ok=True)
        # Drop stale role links (renames, old SoT links, broken symlinks)
        for existing in list(dest.glob("*.md")):
            if existing.name not in export_names:
                if existing.is_symlink() or existing.is_file():
                    existing.unlink(missing_ok=True)
                continue
            if existing.is_symlink() or existing.is_file():
                existing.unlink(missing_ok=True)
        for p in sorted(export_dir.glob("*.md")):
            if p.name == "README.md":
                continue
            link = dest / p.name
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to(p.resolve())

    print(f"{hid}: layout=flat — {n} agent cards → {export_rel}")
    return 0


def _ensure_codex_project_doc_fallback(root: Path, agents_md_rel: str) -> None:
    """Codex only auto-reads AGENTS.md on the root→cwd walk. Point fallback at
    `.codex/AGENTS.md` (or whatever agents_md path) so repo root stays clean."""
    codex_dir = root / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = codex_dir / "config.toml"
    key = "project_doc_fallback_filenames"
    rel = agents_md_rel.replace("\\", "/")
    if cfg_path.is_file():
        text = cfg_path.read_text(encoding="utf-8")
        if rel in text and key in text:
            return
        # Replace existing array or append
        import re

        if re.search(rf"(?m)^{re.escape(key)}\s*=", text):
            text = re.sub(
                rf"(?m)^{re.escape(key)}\s*=\s*\[[^\]]*\]",
                f'{key} = ["{rel}"]',
                text,
                count=1,
            )
        else:
            text = text.rstrip() + f"\n\n# Company OS — Codex project doc (no repo-root AGENTS.md)\n{key} = [\"{rel}\"]\n"
        cfg_path.write_text(text, encoding="utf-8")
    else:
        cfg_path.write_text(
            "\n".join(
                [
                    "# Generated/updated by company_os.sh codex — Company OS boot pointer.",
                    "# Codex discovers this via project_doc_fallback_filenames (no root AGENTS.md).",
                    f'{key} = ["{rel}"]',
                    "",
                ]
            ),
            encoding="utf-8",
        )


def layout_agents_md(home: Path, cfg: dict) -> int:
    """Codex boot: short pointer under .codex/ (not repo-root AGENTS.md).

    Boot SoT = COMPANY_BOOT.md; roster = hop agents.tsv. Optional full mirror
    under export_dir.
    """
    hid = cfg.get("id", "harness")
    root = repo_root(home)
    company = home.relative_to(root).as_posix()
    paths = cfg.get("paths") or {}
    agents_rel = str(paths.get("agents_md") or ".codex/AGENTS.md")
    out = _resolve_path(root, agents_rel)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(load_tsv("agents.tsv"), key=lambda r: r.get("name", ""))
    source_roles = load_agents(home)
    guidance = cfg.get("tier_guidance") or {}
    boot = cfg.get("boot") or {}
    hop = f"python3 {company}/system/skills/defaults/marlin-hop/scripts/hop.py"

    pointer = "\n".join(
        [
            f"# Codex boot pointer — Company OS ({hid})",
            "",
            f"Generated adapter (not SoT). Lives under `.codex/` so the repo root stays free of AGENTS.md.",
            f"Boot: [`{company}/COMPANY_BOOT.md`]({company}/COMPANY_BOOT.md).",
            f"Org: [`{company}/README.md`]({company}/README.md). Hiring: `.agents/holding/` (`holding-hr`).",
            "",
            "```bash",
            f"{hop} --path <file>",
            f"{hop} --roster ceo",
            f"{hop} --list --harness {hid}",
            f"{company}/system/install/company_os.sh {hid}",
            "```",
            "",
            "## Codex execution contract",
            "",
            "When the user addresses the CEO, run the Company OS flow automatically. Use the "
            "actual `multi_agent_v1__spawn_agent` tool for delegated stages; do not merely "
            "role-play the chain:",
            "",
            "```text",
            "Product: CEO → product-lead → ba-user → product-lead → (po-new|po-modify)? → ## Result → CEO → eng",
            "Eng:     CEO → [team-lead] → IC → *-qc  (QC only after IC done)",
            "Cross-team: always ## Result/Escalate UP to CEO, then CEO hops down.",
            "Slim brief: goal + paths + optional plan_dir + read loci — never paste full plans.",
            "```",
            "",
            "Resolve the exact role with `hop.py --path <file> --harness codex`. Start every "
            "spawn prompt with `COMPANY_OS_ROLE: <exact hop role>` and "
            "`COMPANY_OS_PARENT: <parent role>`. The UI nickname is not the role identity. "
            "Use the generated role card under `.codex/agents/` as the brief. A dispatch "
            "role must spawn its next role; a leaf IC must not spawn. Product-lead must not "
            "spawn eng — report up to CEO with `plan_dir`/`read` only.",
            "",
        ]
    )
    out.write_text(pointer, encoding="utf-8")
    _ensure_codex_project_doc_fallback(root, agents_rel)

    # Remove stale repo-root AGENTS.md if we no longer own that path
    root_agents = root / "AGENTS.md"
    if agents_rel.replace("\\", "/") != "AGENTS.md" and root_agents.is_file():
        # Only remove if it looks like our generated Company OS boot
        head = root_agents.read_text(encoding="utf-8", errors="ignore")[:200]
        if "Company OS" in head or "Marlin Company OS" in head:
            root_agents.unlink()
            print(f"{hid}: removed stale repo-root AGENTS.md")

    export_rel = paths.get("export_dir")
    if export_rel:
        lines: list[str] = [
            f"# AGENTS.md — Company OS ({hid} export mirror)",
            "",
            f"Mirror only. Codex boot pointer: `{agents_rel}` → `{company}/COMPANY_BOOT.md`.",
            f"**{hid}** is a runtime — not a second org.",
            "",
            "## Portable tiers",
            "",
        ]
        for tier in ("dispatch", "low", "medium", "high", "xhigh"):
            tip = guidance.get(tier, "")
            model, _ = resolve_tier_maps(cfg, tier)
            extra = f" (harness model hint: `{model}`)" if model and model != "default" else ""
            lines.append(f"- **`{tier}`** — {tip}{extra}".rstrip(" —"))
        lines += [
            "",
            "## Roster (`agents.tsv`)",
            "",
            "| Role | Tier | Write policy | Skill | Blurb |",
            "| --- | --- | --- | --- | --- |",
        ]
        for r in rows:
            blurb = (r.get("blurb") or "").replace("|", "\\|")
            lines.append(
                f"| `{r.get('name','')}` | `{r.get('tier','')}` | "
                f"`{r.get('permission_mode','')}` / `{r.get('capability_mode','')}` | "
                f"`{r.get('skill') or '—'}` | {blurb} |"
            )
        lines += [
            "",
            "## Re-generate",
            "",
            "```bash",
            f"{company}/system/install/company_os.sh {hid}",
            "```",
            "",
        ]
        if boot.get("skills_note"):
            lines += ["## Skills note", "", str(boot["skills_note"]), ""]
        mirror = _resolve_path(root, str(export_rel))
        mirror.mkdir(parents=True, exist_ok=True)
        (mirror / "AGENTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        role_names = {f"{r.get('name')}.md" for r in rows if r.get("name")}
        for existing in mirror.glob("*.md"):
            if existing.name not in role_names and existing.name not in {"AGENTS.md", "README.md"}:
                existing.unlink(missing_ok=True)
        for row in rows:
            name = row.get("name")
            source = (source_roles.get(name) or {}).get("file")
            if name and source and Path(source).is_file():
                (mirror / f"{name}.md").write_text(
                    Path(source).read_text(encoding="utf-8"), encoding="utf-8"
                )
        (mirror / "README.md").write_text(
            f"Generated `{hid}` roster mirror. Boot pointer: `{agents_rel}`.\n",
            encoding="utf-8",
        )

    print(
        f"{hid}: layout=agents_md — pointer {out.relative_to(root)} "
        f"({len(rows)} roles mirrored under export_dir)"
    )
    return 0


def layout_tree_symlink(home: Path, cfg: dict) -> int:
    """Symlink mounts into a runtime dir (e.g. Claude .claude/)."""
    hid = cfg.get("id", "harness")
    root = repo_root(home)
    paths = cfg.get("paths") or {}
    boot = cfg.get("boot") or {}
    runtime_rel = paths.get("runtime_dir") or paths.get("claude_dir") or f".{hid}"
    runtime = _resolve_path(root, str(runtime_rel))
    runtime.mkdir(parents=True, exist_ok=True)

    mounts: list[tuple[str, str]] = []
    if "mounts" in cfg:
        for m in cfg["mounts"]:
            mounts.append((str(m["link"]), str(m["target"])))
    else:
        # Convenience keys used by existing claude.toml
        for link_key, target_key, default_link, default_target in (
            ("link_agents", "agents_target", "agents", "../.agents/marlin-language-company/system/staffs"),
            ("link_skills", "skills_target", "skills", "../.agents/marlin-language-company/system/skills"),
            ("link_plans", "plans_target", "plans", "../.agents/marlin-language-company/cache/plans"),
        ):
            mounts.append(
                (
                    str(paths.get(link_key) or default_link),
                    str(paths.get(target_key) or default_target),
                )
            )

    for link_name, target_rel in mounts:
        _symlink(runtime / link_name, target_rel)

    link_boot = boot.get("link_boot")
    company_boot = boot.get("company_boot")
    if link_boot and company_boot:
        _symlink(runtime / str(link_boot), str(company_boot))

    harness_readme = boot.get("harness_readme")
    if harness_readme:
        tiers = cfg.get("tier_to_model") or {}
        tier_lines = "\n".join(f"| `{k}` | `{v}` |" for k, v in tiers.items())
        _resolve_path(root, str(harness_readme)).write_text(
            "\n".join(
                [
                    f"# `{hid}` runtime mount (not Company SoT)",
                    "",
                    "Company: [`.agents/marlin-language-company/README.md`](../.agents/marlin-language-company/README.md) · "
                    "[`.agents/marlin-language-company/COMPANY_BOOT.md`](../.agents/marlin-language-company/COMPANY_BOOT.md)",
                    "",
                    "Do not add org skills/cache/plans/agents here — mount Company OS only.",
                    "",
                    "## Tier → UI model (guidance only)",
                    "",
                    "| Portable `tier` | Suggested model |",
                    "| --- | --- |",
                    tier_lines,
                    "",
                    f"Re-generate: `.agents/marlin-language-company/system/install/company_os.sh {hid}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    print(f"{hid}: layout=tree_symlink — mounts under {runtime_rel}/")
    return 0


LAYOUTS = {
    "flat": layout_flat,
    "agents_md": layout_agents_md,
    "tree_symlink": layout_tree_symlink,
}


def export_one(home: Path, harness_id: str) -> int:
    cfg = load_harness(home, harness_id)
    layout = str(cfg.get("layout") or "").strip()
    if not layout:
        print(f"{harness_id}: harness.toml missing layout=", file=sys.stderr)
        return 1
    fn = LAYOUTS.get(layout)
    if not fn:
        print(
            f"{harness_id}: unknown layout={layout!r}. "
            f"Known: {sorted(LAYOUTS)}",
            file=sys.stderr,
        )
        return 1
    return fn(home, cfg)


def list_harnesses(home: Path) -> int:
    """Discovery: harness id + layout (no generate)."""
    ids = discovered_harnesses(home)
    company = company_relposix(home)
    if not ids:
        print(f"no harness/*.toml under {company}/system/harness/")
        return 1
    print("id\tlayout\tpath")
    for hid in ids:
        cfg = load_harness(home, hid)
        layout = str(cfg.get("layout") or "?")
        print(f"{hid}\t{layout}\t{company}/system/harness/{hid}.toml")
    print(f"count: {len(ids)}")
    print(f"generate: {company}/system/install/company_os.sh <id|all>")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--to",
        default=None,
        help="harness id (must have harness/<id>.toml) | all",
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="list harness id + layout (no generate)",
    )
    ap.add_argument(
        "--skip-sot-normalize",
        action="store_true",
        help="do not rewrite SoT frontmatter to portable-only",
    )
    args = ap.parse_args()
    home = agents_home()
    if args.list:
        return list_harnesses(home)
    if not args.to:
        ap.error("one of --to or --list is required")
    target = args.to.strip().lower()
    if target == "all":
        targets = discovered_harnesses(home)
        if not targets:
            print("no harness/*.toml found", file=sys.stderr)
            return 1
    else:
        targets = [target]

    skip_normalize_for_codex = target == "codex"
    if not args.skip_sot_normalize and not skip_normalize_for_codex:
        n = normalize_sot_portable(home)
        print(f"sot: normalized {n} portable role cards")

    rc = 0
    for t in targets:
        rc |= export_one(home, t)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
