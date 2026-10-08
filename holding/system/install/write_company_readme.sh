#!/usr/bin/env bash
# Write Company OS README.md (usage how-to). Product package README must stay AI-free.
set -euo pipefail
COMPANY_DIR=""; PKG_ROOT=""; TITLE=""
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

## Usage — CEO / BA in one room

**User talks only to \`ceo\` and \`ba-user\`.** Everyone else is a **sub-agent**
(Assigned by ceo/ba-user; not a direct user chat).

**Default launch = the project that contains this company as \`ceo\`**
(room folder → \`../.company-rooms/<name>\` —
**never** a harness/system clone).

\`\`\`bash
# Start (new company room as CEO) — note the room name
./$REL_COMP/launch.sh grok "ship empty-state"

# Call BA in the SAME room (handoff conversation surface to ba-user)
./$REL_COMP/launch.sh grok --room-name <name> --agent ba-user "clarify acceptance with user"

# Return to CEO in that room
./$REL_COMP/launch.sh grok --room-name <name> --agent ceo "BA done — continue eng"

# Other harnesses
./$REL_COMP/launch.sh claude "…"
./$REL_COMP/launch.sh merge "…"

# Opt out of a new room / resume
./$REL_COMP/launch.sh grok --no-room "…"
./$REL_COMP/launch.sh grok --continue "…"
\`\`\`

| Arg | Meaning |
| --- | --- |
| \`grok\` / \`claude\` / \`codex\` | Vendor CLI |
| \`merge\` | \`company_os all\` + default runtime_router vendor |
| \`--agent ceo\|ba-user\` | User-facing agent (default \`ceo\`) |
| \`--room-name NAME\` | Name/join \`../.company-rooms/NAME\` (required for \`--agent ba-user\`) |
| (default) | **New** company room as ceo |
| \`--no-room\` / \`--continue\` | Stay in current folder / resume session |

### Parent → child product CEO

\`\`\`bash
./$REL_COMP/launch.sh grok <child-ish> "short goal"
./$REL_COMP/launch.sh --list-children
\`\`\`

## Regenerate adapters

\`\`\`bash
./$REL_COMP/system/install/company_os.sh all
\`\`\`

Holding: https://github.com/jokerphuongnam/agents-holding/blob/main/docs/ceo-launch-and-children.md
EOF
echo "[write_company_readme] $COMPANY_DIR/README.md"
