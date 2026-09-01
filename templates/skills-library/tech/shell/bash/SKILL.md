---
name: bash
description: >
  Safe bash/sh scripting — strict mode, quoting, idempotency, traps, and
  secret hygiene. Use for install/CI/helper scripts. Not for rewriting
  product backends in bash.
---

# bash

## Who / paths

- **You:** Shell scripts used in CI, developer tooling, installers, and ops helpers.
- **Not you:** Implementing core product business logic in bash when a real language service exists; storing long-lived secrets in scripts.
- **Paths:** `**/*.{sh,bash}`, `**/scripts/**`, `**/bin/**`, inline shell in `.github/workflows/*`
- **Load when:** Brief adds/fixes shell scripts or CI shell steps.

## How

1. **Strict mode.** New scripts: set -euo pipefail (or document why not). Use env bash shebang when bash features are required.

2. **Quote everything.** Quote variables and $@. Unquoted expansions break on spaces/globs.

3. **Tests.** Prefer [[ ... ]] in bash. Check command presence with command -v.

4. **Arrays and paths.** Arrays for arg lists; cd safely or exit; prefer absolute paths when cwd is uncertain.

5. **Pipes.** Enable pipefail or check PIPESTATUS — last command alone is not enough.

6. **Secrets.** Never embed tokens/passwords. Pass via env or mode-600 files; redact logs.

7. **Idempotency.** Install/setup scripts re-runnable (mkdir -p, skip-if-exists) for CI/bootstrap.

8. **Privileges.** Least privilege; do not sudo entire scripts when one command needs it.

9. **Portability.** sh-targeted scripts avoid bashisms; bash-targeted scripts do not claim POSIX purity.

10. **Structure.** Functions + local; main entry; useful usage on bad args.

11. **Temps.** mktemp + trap cleanup for temp dirs/files.

12. **Anti-pattern — curl|bash to prod:** downloading and executing remote scripts without pin/review.

13. **CI.** Fail non-zero on errors; do not mask failures with || true unless intentional and commented.

## Done-when

- [ ] Strict mode (or documented exception); variables quoted.
- [ ] No embedded secrets.
- [ ] Idempotent when used for install/CI bootstrap.
- [ ] Temp files cleaned; errors exit non-zero.
- [ ] Shell dialect matches shebang (bash vs sh).
- [ ] No unjustified || true masking failures.

## References (external)

- https://google.github.io/styleguide/shellguide.html
- https://www.gnu.org/software/bash/manual/bash.html
- https://shellcheck.net/
- https://github.com/HoangNguyen0403/agent-skills-standard
- https://github.com/HK-hub/AgentSkills
- https://www.agentskills.io/
