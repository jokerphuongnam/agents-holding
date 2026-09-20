---
name: code-graph-index
description: >
  Install/refresh Code Prism SoT for a project and query it via MCP tools
  (ask_graph, resolve_symbol, …) so agents index from a real symbol graph
  instead of walking the whole tree or a homemade path graph.
---

# code-graph-index

## Who / paths

- **You:** `code-graph` staff (cross-cut). Own Prism index + MCP query for this company.
- **Not you:** Product features; architecture (`cto`); git commits (`git`).
- **SoT (system):** `~/Library/Caches/code-prism/<projectName>-<hash>/{lang}-prism/`
- **Optional company pointer (write):** `$COMPANY_ROOT/cache/code-graph/GRAPH.md`
- **Load when:** index / refresh graph / “where is X” / “who calls Y” / hop needs neighbors.

## Setup (once per machine)

```bash
curl -fsSL https://raw.githubusercontent.com/jokerphuongnam/code-prism-cli/main/install.sh | bash
# needs Node ≥ 20, git, npm — puts prism + prism-mcp on ~/bin
```

Verify: `prism plugins` and `prism-mcp which`.

## How

### 1. Prefer Prism cache first

If the ask is “where is X?” / “who calls Y?”, **query MCP** before re-analyzing:

| Tool | Use |
|------|-----|
| `get_project_summary` | Entry overview / node counts |
| `search_symbols` | Relative name → ranked ids |
| `resolve_symbol` | Best hit + `full_info` |
| `ask_graph` | Natural-language relative ask (any language) |
| `get_node_info` | One or many node ids |
| `get_smart_context` | Target ids + neighborhood |
| `get_logical_cluster` / `trace_dependency` / `find_impact_range` | Structure / blast radius |

MCP client (after analyze):

```json
{
  "mcpServers": {
    "code-prism": {
      "command": "prism-mcp",
      "args": ["."]
    }
  }
}
```

Or short cache name: `"args": ["LiteTrace"]` / `["game"]`.

### 2. Refresh SoT

```bash
prism detect  --root "$PROJECT_ROOT"
prism analyze --root "$PROJECT_ROOT"
```

Optional company pointer (human + hop brief):

```bash
python3 system/skills/customs/cross-cut/code-graph/code-graph-index/scripts/sync_prism_pointer.py \
  --root "$PROJECT_ROOT" \
  --out "$COMPANY_ROOT/cache/code-graph"
```

If the skill is only in the holding library:

```bash
python3 "$HOLDING/templates/skills-library/tech/code-graph/code-graph-index/scripts/sync_prism_pointer.py" \
  --root "$PROJECT_ROOT" \
  --out "$COMPANY_ROOT/cache/code-graph"
```

### 3. What Prism owns vs company cache

| Location | Role |
|----------|------|
| `~/Library/Caches/code-prism/…` | **Source of truth** (JSON + SQLite per language) |
| `$COMPANY_ROOT/cache/code-graph/GRAPH.md` | Thin pointer + how to query — **not** a second indexer |

Do **not** run or extend deprecated `build_code_graph.py` (homemade path/import walk).

### 4. Scope

Default root = project root registered for this company. Do not scan sibling companies unless the brief says so.

### 5. After large refactors

`prism analyze` once; reply with languages, cache slug/dir, and a sample `ask_graph` / `resolve_symbol` hit if the brief asked a question.

## Done-when

- [ ] `prism` available (or install one-liner reported if blocked)
- [ ] `prism analyze --root …` succeeded (or cache already fresh and query-only)
- [ ] Query asks answered via MCP tools — not a full-tree walk
- [ ] Optional `GRAPH.md` pointer updated if `--out` was requested
- [ ] No product code changes

## Anti-patterns

- Re-walking the monorepo when `ask_graph` / `resolve_symbol` already answers
- Treating company `cache/code-graph/*.json` from the old script as SoT
- Writing Prism SoT into the user project tree
- Inventing absolute node ids when a relative ask works
