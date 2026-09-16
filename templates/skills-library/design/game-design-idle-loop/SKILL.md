---
name: game-design-idle-loop
description: >
  Specialize idle / garden care loops — plant, grow, water — for one-screen
  desktop companions. Keep calm pacing; no combat.
---

# game-design-idle-loop

For **Desk Garden** MVP: idle plant/water on **one** Unity screen inside a
native shell.

## How

1. **Minimal verbs.** Plant, water (optional harvest/remove later — not MVP
   unless AC says so).
2. **Growth tick.** Visible idle progress while the view is up; define tick
   rate and stages (seed → sprout → grown) with few stages.
3. **Feedback.** Unity animation/VFX for plant/water; short EN/VI lines via
   Marlin L10n for confirmations — not walls of tutorial text.
4. **Desktop companion tone.** Calm, glanceable; works beside other apps;
   avoid loud fail states that need a second screen.
5. **Balance.** Early success in &lt;2 minutes for a stranger; longer idle
   optional, not required to “win”.
6. **Anti-patterns:** combat, quests, multi-plot maps, shop meta, forcing
   account before first plant (login may exist but first plant should be
   reachable).

## Done-when

- [ ] Verb list ≤ MVP AC
- [ ] Growth stages + timings written
- [ ] Stranger can complete one plant/water cycle quickly
- [ ] Tone matches desktop companion
