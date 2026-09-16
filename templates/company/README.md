# {{COMPANY_TITLE}}

Clone of `.agents/templates/company/`. Reference instance with full Marlin shape:
`.agents/marlin-language-company/`.

```bash
system/install/company_os.sh all

# Always CEO (preferred):
./launch.sh grok|claude|codex|merge "first prompt"
# Parent → child: ./launch.sh grok <child-ish> "prompt"
# Docs: agents-holding docs/ceo-launch-and-children.md
```
