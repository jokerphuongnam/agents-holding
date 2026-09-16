# {{COMPANY_TITLE}}

Company OS (`{{COMPANY_SLUG}}`). Staffs, skills, harness, and hop live under `system/`.

## Usage — always talk to the CEO

Do **not** open a bare CLI and then hop for `ceo`. Use this company’s `launch.sh`:

```bash
# From the project / package root (owns .grok/ adapters):
./.agents/{{COMPANY_SLUG}}/launch.sh grok "your ask"
./.agents/{{COMPANY_SLUG}}/launch.sh claude "your ask"
./.agents/{{COMPANY_SLUG}}/launch.sh codex "your ask"
./.agents/{{COMPANY_SLUG}}/launch.sh merge "your ask"    # multi-vendor Assign

# From this company directory:
./launch.sh grok "your ask"

# New session (default continues the prior session for this company cwd):
./.agents/{{COMPANY_SLUG}}/launch.sh grok --fresh "new topic"
```

| Arg | Meaning |
| --- | --- |
| `grok` / `claude` / `codex` | Start **CEO** on that vendor CLI |
| `merge` | `company_os all` + CEO on `runtime_router` default runtime |
| `"ask…"` | **First user message** in the CEO session |
| `--fresh` | Do not continue the prior session |

### Parent → child CEO (if this company has children)

```bash
./.agents/{{COMPANY_SLUG}}/launch.sh grok <child-ish> "short goal"
./.agents/{{COMPANY_SLUG}}/launch.sh --list-children
```

Do **not** open the child ORG/staffs from here. Child CEO hops its own ICs.

## Regenerate adapters

```bash
./.agents/{{COMPANY_SLUG}}/system/install/company_os.sh all
```

Generated how-to also appears in `.grok/README.md` after `company_os.sh grok` (points here).

Holding templates: [docs/ceo-launch-and-children.md](https://github.com/jokerphuongnam/agents-holding/blob/main/docs/ceo-launch-and-children.md)
