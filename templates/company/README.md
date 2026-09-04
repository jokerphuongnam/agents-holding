# {{COMPANY_TITLE}}

Clone of `.agents/templates/company/`. Reference instance with full Marlin shape:
`.agents/marlin-language-company/`.

```bash
.agents/{{COMPANY_SLUG}}/system/install/company_os.sh all
```

Install one runtime from the project root:

```bash
.agents/{{COMPANY_SLUG}}/system/install/company_os.sh codex
.agents/{{COMPANY_SLUG}}/system/install/company_os.sh grok
```

The installer generates the selected runtime view from this Company OS source. Codex reads
`.codex/AGENTS.md` and `.codex/agents/`; Grok uses its own generated runtime paths. Do not
edit generated runtime files directly.
