# Chat compare

**Easy read (bubbles):** open [`CHAT_VIEW.html`](CHAT_VIEW.html) — user **right**, agent **left**. Per-arm: [`case-a-plain/CHAT.html`](case-a-plain/CHAT.html), [`case-b-company-os/CHAT.html`](case-b-company-os/CHAT.html).
 — Case A (plain) vs Case B (Company OS)

Evidence: `case-a-plain/chat_history.jsonl` + `case-b-company-os/chat_history.jsonl`  
(and human-readable `CHAT_TRANSCRIPT.md`). Same user vibe line; different process.

## Numbers (session)

| Metric | A plain | B company-os |
| --- | ---: | ---: |
| Wall | 244s | **159s** |
| Total tokens | 657,966 | **478,849** |
| Model turns | 30 | **18** |
| Reasoning events | 30 | **18** |
| Tool results | 42 | 47 |
| Score /40 | 39 | 39 |

## How the chats differ

### A — plain vibe (“scaffold everything”)

Opening assistant move:

> I'll build a local Todo app… Checking the workspace first.  
> Scaffolding the backend and frontend now.

Chat pattern:

1. Empty tree → **from scratch**
2. Long scaffold loop (Express + SQLite + Vite + Vitest)
3. Fix import/test issues as they appear
4. Smoke API + write docs

Keyword hits in transcript: `scaffold` **10**, `sqlite` **18**, `vitest` **20**;  
**0** hits for `product-lead` / `hop.py` / `task_cache` / `po-new`.

**Read as:** one mega-worker owns the whole job. No org routing in the chat — just implement.

### B — Company OS plugin (“route, then fill gaps”)

Opening assistant move:

> I'll act as CEO and kick off Company OS: inspect the workspace, then route the product ask to product-lead.

Chat pattern:

1. Inspect starter + company tree
2. `hop.py --roster ceo` / `product-lead`
3. `task_cache` / `task_memory` touches
4. Slim PO plan (`cache/plans/todo-mvp.md`, `plan_dir` cited)
5. Act as backend/frontend engineers on gaps
6. QC tests + smoke + `BENCH_DONE` with cascade notes

Keyword hits: `product-lead` **21**, `task_cache` **30**, `task_memory` **14**,  
`hop.py` **13**, `backend-engineer` **16**, `frontend-engineer` **15**, `qc-lead` **10**,  
`plan_dir` **5**, `## Result` **3**.

**Read as:** chat shows **org vocabulary and tools** (ceo → product-lead → po-new → eng → qc), even though one session still executes the tools. Not a silent “just code” path.

## Why this is not “ăn gian”

1. **Raw JSONL** checked in — every user/assistant/tool step is auditable.
2. **usage.json** totals match `TOKENS.md` (`turn_completed.usage`).
3. A never mentions Company OS roles; B repeatedly runs hop/task_cache and writes a plan under `.agents/…/cache/plans/`.
4. Both still had to make tests pass (`npm test`) — score tied; **efficiency** is where B wins.

## Caveat (honest)

B started with **create-company starter** (Express+React scaffold already present). A started **empty**. That is part of the plugin path (factory seeds stack), not hidden — see case-b setup log / COMPANY tree. The chat still shows B spending turns on **process + gap-fill + QC**, not re-scaffolding the universe.

## Bottom line from the two chats

| | A | B |
| --- | --- | --- |
| Strategy in chat | Build monolith from zero | Route via Company OS, extend starter |
| Org signals in transcript | None | Dense (hop, product-lead, po, eng, qc, memory) |
| Outcome quality | Pass bar | Pass bar |
| Cost in this run | Higher tokens & wall | Lower tokens & wall |
