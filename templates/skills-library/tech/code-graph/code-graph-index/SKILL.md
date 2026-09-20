---
name: code-graph-index
description: >
  Build and refresh a lightweight code graph (graph.json / graph.jsonl / GRAPH.md)
  so agents can index from an artifact instead of walking the whole project.
  Use when asked to index, map the repo, or speed up hop briefs.
---

# code-graph-index

## Who / paths

- **You:** `code-graph` staff (cross-cut). Own the graph artifact only.
- **Not you:** Implementing product features; rewriting app code; inventing architecture.
- **Paths (read):** project `--root` (source tree). **Paths (write):** `cache/code-graph/` or `.agents/code-graph/`.
- **Load when:** Brief asks to index / refresh code graph / map imports for faster hops.

## How

1. **Prefer artifact first.** If `GRAPH.md` / `graph.json` already exists and the ask is “where is X?”, read the graph **before** a full-repo walk.

2. **Refresh command** (from company or holding templates copy):

```bash
python3 system/skills/customs/cross-cut/code-graph/code-graph-index/scripts/build_code_graph.py \
  --root "$PROJECT_ROOT" \
  --out "$COMPANY_ROOT/cache/code-graph"
```

If the skill still lives only in the holding library (not yet copied into company customs):

```bash
python3 "$HOLDING/templates/skills-library/tech/code-graph/code-graph-index/scripts/build_code_graph.py" \
  --root "$PROJECT_ROOT" \
  --out "$COMPANY_ROOT/cache/code-graph"
```

3. **Outputs**
   - `graph.json` — full snapshot (`files[]`, `edges[]`, lang counts)
   - `graph.jsonl` — one file record per line (stream-friendly)
   - `GRAPH.md` — short summary for humans / hop briefs

4. **Ignore noise.** The script skips `.git`, `node_modules`, `.build`, `DerivedData`, lockfiles, binaries. Do not hand-edit those lists unless asked.

5. **Scope.** Default root = project root registered for this company. Do not scan sibling companies unless the brief says so.

6. **After large refactors** (many files moved/renamed): refresh once; tell CEO/CTO the new `file_count` / `edge_count`.

## Done-when

- [ ] `graph.json`, `graph.jsonl`, and `GRAPH.md` exist under the out dir.
- [ ] Script exited 0; stdout printed the three paths.
- [ ] Brief reply includes file_count, edge_count, and out dir — no product code changes.

## Anti-patterns

- Re-walking the entire monorepo on every hop when a fresh graph already answers the ask.
- Committing huge generated graphs without ask (ask `git` / user if unsure).
- Treating this as a full SCIP/LSP semantic index — it is a **lightweight** path/import map.
