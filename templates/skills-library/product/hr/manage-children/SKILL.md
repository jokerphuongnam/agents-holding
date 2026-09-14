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

## Owns

| Work | You do |
| --- | --- |
| **Approve / create child** | Deal with user → lock → `create-child-company.sh` |
| **Inventory** | `children_registry.py list/show/scan` — read child SoT metadata |
| **Grants** | With parent ceo: what RO slices a child may receive; edit `GRANTS.toml` |
| **Hire / restaff child** | Deal → write staffs/skills/hop **into the child** |
| **Enable hr on a descendant** | Hire `hr` + this skill into a child that wants its own children |

## Does not own

- Implementing product code in a child (child ceo → ICs)
- Sibling hops / editing sibling children without a deal
- Holding-level new subsidiaries (`holding-hr`)

## Flow — approve a new child

```text
parent ceo (or user): we need a scoped child for package X
  → Assign hr
  → you deal: name, budget, project-root, grants, placement
  → user confirm/lock
  → create-child-company.sh …  (parent already has you / hr)
  → company_os.sh all on child
  → notify parent ceo + child ceo
```

## Flow — no hr on a company that wants children

That company escalates **up** to you (or to `holding-hr` if it is a top
subsidiary). You hire role `hr` + `manage-children` **into that company** after
lock — then *they* may run child flows.

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
  --name … --budget … --project-root … --grant-path …
```

## Token rule

Parent product hop to a child **path** still handoffs to **child ceo** (cheap).
You are for **org** work: create/approve child, grants, staffing — not every
file hop.
