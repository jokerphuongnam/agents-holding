# {{COMPANY_TITLE}}

Company OS (`{{COMPANY_SLUG}}`). Staffs, skills, harness, and hop live under `system/`.

## Usage — CEO / BA in one worktree

**User talks only to `ceo` and `ba-user`.** Everyone else is a **sub-agent**.

**Default launch = NEW git worktree as `ceo`.**

```bash
./.agents/{{COMPANY_SLUG}}/launch.sh grok "your ask"

# Same worktree → BA
./.agents/{{COMPANY_SLUG}}/launch.sh grok --worktree-name <name> --agent ba-user "clarify with user"

# Same worktree → back to CEO
./.agents/{{COMPANY_SLUG}}/launch.sh grok --worktree-name <name> --agent ceo "continue"

./.agents/{{COMPANY_SLUG}}/launch.sh merge "…"
./.agents/{{COMPANY_SLUG}}/launch.sh grok --no-worktree "…"
./.agents/{{COMPANY_SLUG}}/launch.sh grok --continue "…"
```

| Arg | Meaning |
| --- | --- |
| `--agent ceo\|ba-user` | User-facing agent (default `ceo`) |
| `--worktree-name NAME` | Create/join named worktree (required for `ba-user`) |
| (default) | **New** worktree as ceo |

### Parent → child

```bash
./.agents/{{COMPANY_SLUG}}/launch.sh grok <child-ish> "short goal"
```

## Regenerate

```bash
./.agents/{{COMPANY_SLUG}}/system/install/company_os.sh all
```

Holding: [docs/ceo-launch-and-children.md](https://github.com/jokerphuongnam/agents-holding/blob/main/docs/ceo-launch-and-children.md)

## User-facing choices

`ceo` / `ba-user` (and domain BA): when more than one viable path, present **Title / short description / code before / code after** — not bare option grids. See `system/staffs/ba/ba-user.md`.
