#!/usr/bin/env bash
# Write Company OS README.md (usage how-to). Product package README must stay AI-free.
# Usage: write_company_readme.sh --company-dir DEST --package-root PKG [--title TITLE]
set -euo pipefail

COMPANY_DIR=""
PKG_ROOT=""
TITLE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --company-dir) COMPANY_DIR="${2:-}"; shift 2 ;;
    --package-root) PKG_ROOT="${2:-}"; shift 2 ;;
    --title) TITLE="${2:-}"; shift 2 ;;
    *) echo "unknown: $1" >&2; exit 2 ;;
  esac
done

[[ -n "$COMPANY_DIR" && -n "$PKG_ROOT" ]] || { echo "need --company-dir and --package-root" >&2; exit 2; }
COMPANY_DIR="$(cd "$COMPANY_DIR" && pwd)"
PKG_ROOT="$(cd "$PKG_ROOT" && pwd)"
SLUG="$(basename "$COMPANY_DIR")"
TITLE="${TITLE:-$SLUG}"
REL_COMP="$(python3 -c "import os; print(os.path.relpath('$COMPANY_DIR', '$PKG_ROOT'))")"

cat > "$COMPANY_DIR/README.md" <<EOF
# $TITLE

Company OS (\`$SLUG\`). Staffs, skills, harness, and hop live under \`system/\`.

Package / adapters root: \`$PKG_ROOT\`

## Usage — always talk to the CEO

Do **not** open a bare CLI and then hop for \`ceo\`. Use this company's \`launch.sh\`:

\`\`\`bash
# From the project / package root:
./$REL_COMP/launch.sh grok "your ask"
./$REL_COMP/launch.sh claude "your ask"
./$REL_COMP/launch.sh codex "your ask"
./$REL_COMP/launch.sh merge "your ask"    # multi-vendor Assign

# From this company directory:
./launch.sh grok "your ask"

# New session (default continues prior session for this company cwd):
./$REL_COMP/launch.sh grok --fresh "new topic"
\`\`\`

| Arg | Meaning |
| --- | --- |
| \`grok\` / \`claude\` / \`codex\` | Start **CEO** on that vendor CLI |
| \`merge\` | \`company_os all\` + CEO on \`runtime_router\` default runtime |
| \`"ask…"\` | **First user message** in the CEO session |
| \`--fresh\` | Do not continue the prior session |

### Parent → child CEO (if this company has children)

\`\`\`bash
./$REL_COMP/launch.sh grok <child-ish> "short goal"
./$REL_COMP/launch.sh --list-children
\`\`\`

Do **not** open the child ORG/staffs from here. Child CEO hops its own ICs.

## Regenerate adapters

\`\`\`bash
./$REL_COMP/system/install/company_os.sh all
\`\`\`

Generated pointer also appears in \`.grok/README.md\` after \`company_os.sh grok\`.

Holding: https://github.com/jokerphuongnam/agents-holding/blob/main/docs/ceo-launch-and-children.md
EOF

echo "[write_company_readme] $COMPANY_DIR/README.md"
