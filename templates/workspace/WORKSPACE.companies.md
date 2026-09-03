# Workspace registry

| Field | Value |
| --- | --- |
| Topology | `{{TOPOLOGY}}` |
| Parent | `{{PARENT}}` |

## Subsidiaries

| Package path | Company slug | Project root |
| --- | --- | --- |
{{SUBSIDIARIES_TABLE}}

Each package has its **own** `.agents/<slug>/` and runtime adapters
(`.grok/`, `.claude/`) under that package root — do **not** co-locate
two companies on the same `--project-root` (adapters collide).

Each subsidiary has a **full** formula (`ceo`, `cto`, BA/PO/QC, `git`, …).
Cross-company asks: requesting `ceo` → `holding-ceo` → sibling `ceo`
(see holding `ORG.md`).

## Next

{{NEXT_STEPS}}
