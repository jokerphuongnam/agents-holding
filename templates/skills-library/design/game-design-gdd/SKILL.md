---
name: game-design-gdd
description: >
  Write and maintain a clear GDD — the compass for eng and art. Technical
  writing; keep diffs small and versioned with the plan.
---

# game-design-gdd

Game Designer owns the **Game Design Document** as living SoT for play.
Industry expectation: a description clear in both artistic and technical
angles so the whole team builds the same game
(https://topdev.vn/blog/game-designer-la-gi-mo-ta-cong-viec-cua-nha-thiet-ke-game/).

## Who / paths

- **You:** `game-designer`. GDD under the child package / plans the ceo names
  (e.g. `projects/desk-garden/docs/GDD.md` or company plan slice).
- **Not you:** Implementation PRs; Unity scene authorship as eng SoT.

## How

1. **Structure.** Overview → audience → loop → rules → entities (plant types
   MVP-minimal) → UI/feedback map → L10n keys (EN/VI) → open questions.
2. **Clarity.** Prefer tables and numbered steps over prose walls. Every rule
   must be testable by QA.
3. **Change log.** Date + what changed + why (balance or cut).
4. **Scope fence.** One screen idle only — mark cut ideas as “later”.
5. **Handoff.** Each eng hop cites GDD section paths (`read: GDD.md:…`).
6. **Anti-patterns:** GDD that eng cannot implement; silent rule changes;
   mixing Service API design without eng.

## Done-when

- [ ] GDD readable by stranger eng in one sitting
- [ ] Rules testable; change log present
- [ ] EN/VI player strings inventoried
- [ ] Out-of-scope ideas parked, not mixed into MVP
