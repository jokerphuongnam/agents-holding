---
name: manage-children
description: >
  Parent HR: own child-company portfolio — approve/create children, inventory,
  grants coordination with ceo, hire/restaff into children. /manage-children
---

# Manage child companies (parent HR)

`hr` is the **portfolio owner** for children under this company — not only a
recruiter. Parent `ceo` routes child-org work here; product code stays with
child ceos/ICs.

## Hard rule — create via holding scripts only

**Never** invent / scaffold / copy a child Company OS by hand or by “hop AI
writing files.” Creating a child **must** run:

```bash
~/.agents/holding/system/install/create-child-company.sh \
  --parent .agents/<parent>-company \
  --name <stem> \
  --budget low|medium|high \
  --project-root <package-root> \
  [--placement nested|external] \
  [--grant-path …] [--grant-artifact …]
```

Then:

```bash
<child-company>/system/install/company_os.sh all
```

`create-child-company.sh` writes META/GRANTS, registry, hop fences, `launch.sh`,
and **company `README.md` (usage)**. Hand-made trees skip those and drift.

| Allowed | Forbidden |
| --- | --- |
| Deal → lock → **run the script** | AI/ceo mkdir + paste staffs without the script |
| Edit GRANTS/META after create (with lock) | “Just clone another company folder” |
| Hire into an **existing** child SoT | Re-implement create-child logic in prose |

Inventory / show still use `children_registry.py` — also scripts, not ORG browsing.

## Owns

| Work | You do |
| --- | --- |
| **Approve / create child** | Deal with user → lock → **`create-child-company.sh`** |
| **Inventory** | `children_registry.py list/show/scan` |
| **Grants** | With parent ceo: RO slices; edit `GRANTS.toml` |
| **Hire / restaff child** | Deal → write staffs/skills/hop **into the existing child** |
| **Enable hr on a descendant** | Hire `hr` + this skill into that company |

## Does not own

- Implementing product code in a child (child ceo → ICs)
- Sibling hops / editing sibling children without a deal
- Holding-level new subsidiaries (`holding-hr`)
- Scaffolding child OS without `create-child-company.sh`

## Flow — approve a new child

```text
parent ceo (or user): we need a scoped child for package X
  → Assign hr
  → you deal: name, budget, project-root, grants, placement
  → user confirm/lock
  → YOU RUN create-child-company.sh …   ← mandatory
  → child: company_os.sh all
  → notify parent ceo + child ceo
```

## Flow — no hr on a company that wants children

That company escalates **up** to you (or to `holding-hr` if it is a top
subsidiary). You hire role `hr` + `manage-children` **into that company** after
lock — then *they* may run child flows (still via the script).

## Flow — child needs people

```text
child ceo → parent ceo → you (hr)
  → deal + lock → write into child SoT only
```

## Scripts

```bash
CR=~/.agents/holding/system/install/children_registry.py
python3 "$CR" --parent .agents/<parent>-company list
python3 "$CR" --parent .agents/<parent>-company show --slug <child>-company

~/.agents/holding/system/install/create-child-company.sh \
  --parent .agents/<parent>-company \
  --name … --budget … --project-root … \
  --placement external \
  --grant-path …
```

## Token rule

Parent product hop to a child **path** still handoffs to **child ceo** (cheap)
via `launch.sh` / `handoff_child.py` — not by re-creating the company.
You are for **org** work: create/approve child, grants, staffing — not every
file hop.
