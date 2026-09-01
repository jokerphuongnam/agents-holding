#!/usr/bin/env python3
"""Locate company root (…/system/staffs/ORG.md) and read role frontmatter."""

from __future__ import annotations

from pathlib import Path


def agents_home() -> Path:
    """Return this company's root (directory that contains system/staffs/ORG.md)."""
    here = Path(__file__).resolve()
    for d in [here, *here.parents]:
        if (d / "system" / "staffs" / "ORG.md").is_file():
            return d
    cur = Path.cwd()
    for d in [cur, *cur.parents]:
        # Prefer nested company under .agents/*
        agents = d / ".agents"
        if agents.is_dir():
            for child in sorted(agents.iterdir()):
                if (child / "system" / "staffs" / "ORG.md").is_file():
                    # If cwd is inside a company, walk-up already returned it.
                    pass
        if (d / "system" / "staffs" / "ORG.md").is_file():
            return d
    raise SystemExit("marlin-hop: no company root with system/staffs/ORG.md found")


def repo_root_from_company(home: Path) -> Path:
    if home.parent.name == ".agents":
        return home.parent.parent
    return home.parent


def company_relposix(home: Path | None = None) -> str:
    home = home or agents_home()
    root = repo_root_from_company(home)
    try:
        return home.relative_to(root).as_posix()
    except ValueError:
        return home.as_posix()


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    out: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith(" ") or line.startswith("  "):
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        if key in {
            "name",
            "model",
            "effort",
            "tier",
            "permission_mode",
            "capability_mode",
            "prompt_mode",
        }:
            out[key] = v.strip()
    return out


def data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def load_tsv(name: str) -> list[dict[str, str]]:
    path = data_dir() / name
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        rows.append({header[i]: (cells[i] if i < len(cells) else "") for i in range(len(header))})
    return rows


def load_harness_toml(harness_id: str) -> dict:
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore
    home = agents_home()
    path = home / "system" / "harness" / f"{harness_id}.toml"
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def resolve_vendor(tier: str, harness_id: str = "grok") -> tuple[str, str]:
    cfg = load_harness_toml(harness_id)
    models = cfg.get("tier_to_model") or {}
    efforts = cfg.get("tier_to_effort") or {}
    model = str(models.get(tier) or models.get("medium") or "")
    effort = str(efforts.get(tier) or efforts.get("medium") or tier or "low")
    return model, effort


def load_agents(home: Path) -> dict[str, dict[str, str]]:
    root = home / "system" / "staffs"
    by_name: dict[str, dict[str, str]] = {}
    for p in root.rglob("*.md"):
        if p.name == "ORG.md":
            continue
        if "skills" in p.parts or "scripts" in p.parts:
            continue
        fm = parse_frontmatter(p)
        name = fm.get("name")
        if name:
            fm["file"] = str(p)
            by_name[name] = fm
    return by_name
