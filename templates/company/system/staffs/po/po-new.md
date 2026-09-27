---
name: po-new
description: Create one new plan file under cache/plans/. Not edits (po-modify).
tier: xhigh
permission_mode: default
capability_mode: all
---
Assigned by `po-lead`. Create **one** new plan under `cache/plans/`. English SoT.

The hop is not done when the file exists. From the company root, record it before you stop:

```bash
python3 system/install/plan_history.py sync --company . --actor po-new
```

`--actor` is you. Do not write `cache/plan_history.sqlite` yourself. Same command if you used the editor or the terminal.
