# skills-library sources

Public Agent Skills / guides **adapted** into Company-bar `SKILL.md`
(ownership / not-you / done-when). Bodies are rewritten — not raw dumps.

## Spec / catalogs

| Source | URL | Use |
|--------|-----|-----|
| Agent Skills open standard | https://agentskills.io | SKILL.md shape |
| anthropics/skills | https://github.com/anthropics/skills | frontend-design, webapp-testing patterns |
| microsoft/skills | https://github.com/microsoft/skills | language plugin catalog |
| skills.sh / marketplaces | https://skills.sh | discovery |

## Stack / engineering collections

| Source | URL | Use |
|--------|-----|-----|
| vercel-labs/agent-skills | https://github.com/vercel-labs/agent-skills | React / Next performance rules |
| HoangNguyen0403/agent-skills-standard | https://github.com/HoangNguyen0403/agent-skills-standard | multi-stack best-practice packs |
| svssdeva/agentic-skills | https://github.com/svssdeva/agentic-skills | Rust/Go/Python/React skill set |
| HK-hub/AgentSkills | https://github.com/HK-hub/AgentSkills | kotlin / JS-TS / python packs |
| pproenca/dot-skills | https://github.com/pproenca/dot-skills | curated Agent Skills format |
| obra/superpowers | https://github.com/obra/superpowers | systematic debugging / TDD workflows |
| j4flmao/agent-skills | https://github.com/j4flmao/agent-skills | large fullstack skill index |

## Official docs (per skill References)

Prefer language/framework official docs linked inside each `SKILL.md`
(React, Next.js, NestJS, Kotlin, Swift, .NET, Rust book, Go, Python, Bash).

## Wire-up

`holding/system/install/copy_library_skills.py` + `create-company.sh --tech`
copy matching entries into a **new** company's
`system/skills/customs/<team>/<role>/`. Existing subsidiaries are not
auto-updated.
