# User habit cache (local only)

SQLite `user_habits.sqlite` here is single-user prefs (gitignore).

## Agent I/O (2-step)

1. `habit_cache.py index|propose` → `key` + `short_descript` only  
2. `habit_cache.py get --key …` → load `work` for that key  

Staffs read CLI stdout only — never open the DB. `dump` needs `--i-am-human`.
