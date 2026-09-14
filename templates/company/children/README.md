# Children (scoped Company OS)

**Same relationship as holding → company**, nested and recursive:

```text
holding
  └── company          ← may own children only if it has hr
        └── child      ← product via child ceo; org via parent hr
              └── …    ← child needs hr before it owns further children
```

## Who owns what

| Role | Child **product** work | Child **org** (create / read / approve / staff / grants) |
| --- | --- | --- |
| Parent **ceo** | Hop handoff → child ceo (short goal) | Assign **hr** |
| Parent **hr** | No | **Yes** — portfolio owner (`manage-children`) |
| Child **ceo** | Hop own staffs in child folder | Escalate people/org upward |

**No `hr` on a company ⇒ no child-org flows** (cannot create/list/approve children).

## No hr yet → escalate up

```text
company wants children but has no hr
  → nested: parent hr hires hr into this company
  → top subsidiary: holding-hr hires hr here
  → then child-org flows unlock
```

Dev bootstrap: `seed_parent_hr.py --parent …`

## Layout

```text
.agents/<parent>-company/
├── system/staffs/cross-cut/hr.md          # required for child org
├── system/skills/customs/cross-cut/hr/manage-children/
├── cache/children.sqlite
└── children/<stem>/
    ├── GRANTS.toml
    ├── META.toml
    └── <stem>-company/
```

## Runtime — product path (token-cheap) — **still the main coding flow**

This was never removed from hop: parent path match → `handoff: child`.

```text
parent ceo  --hop(path)-->  handoff: child ceo only (short goal)
                                │
                                ▼
                          child ceo hops own staffs
                          (scope = child company folder + package)
                                │
                                ▼ (need more parent info)
                          escalate → parent ceo (ask grants/info)
```

Parent does **not** deep-spawn child ICs. Child does **not** crawl the parent tree.

## Runtime — org / people (only if parent has `hr`)

```text
new child / grants policy / restaff child / enable hr on descendant
  → parent ceo Assigns **hr** (manage-children)
  → deal + lock → hr executes
```

Product hop (diagram above) and org hop (hr) are **both** active; hr does not replace the child-ceo handoff.

## Create (after hr exists)

```bash
python3 ~/.agents/holding/system/install/seed_parent_hr.py \
  --parent /path/to/.agents/<parent>-company

~/.agents/holding/system/install/create-child-company.sh \
  --parent /path/to/.agents/<parent>-company \
  --name sdk-ios --budget low \
  --project-root /path/to/package \
  --grant-path documents/api/
```

Prefer: parent **hr** runs create after user lock (ceo does not bypass hr for org).
