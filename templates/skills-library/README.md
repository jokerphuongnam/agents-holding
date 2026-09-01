# skills-library

Ready-made **custom** skills for new subsidiaries. English, Company bar
(ownership / not-you / done-when). Adapted from public guides — see
`SOURCES.md` for provenance. Not raw copyrighted dumps.

## Layout

`tech/…`, `product/…`, `design/…`, `qc/…` — each skill is `<id>/SKILL.md`.

## Wire-up

`create-company.sh --tech "react,nestjs,kotlin"` copies matching skills (by
`--tech` tags in `MANIFEST.json`) into
`.agents/<slug>-company/system/skills/customs/<team>/<role>/` and updates
`TASK_SKILLS.json` when entries are empty. Product / design / QC baselines
seed by role regardless of stack when the installer includes them.
