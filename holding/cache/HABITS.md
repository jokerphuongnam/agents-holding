# User habit cache (local only)

SQLite file `user_habits.sqlite` in this directory is **single-user hobby
prefs** — how you usually structure new companies and restaff old ones.

- **Gitignored.** Never commit the DB.
- **API:** `../system/install/habit_cache.py` (`propose` / `get` / `record-bundle`).
- Agents/staffs read **CLI stdout (TSV) only** — never open the DB or paste `dump`.
- `dump` requires `--i-am-human` (debug for people, not agents).
- Habits are **prior** for `holding-hr`; user lock still required before factory
  writes.
