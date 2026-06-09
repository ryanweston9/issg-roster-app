# ISSG Roster App — Claude Code Project Brief

## What This Is

A purpose-built FIFO roster management web app for ISSG (Palyku Resources). Replaces manual Excel tracking of staff swings, flight bookings, and change requests across Pilbara mining sites.

Currently deployed and live at: **issg-roster-app-production.up.railway.app**

This is the Eastern Hub trial (Christmas Creek). If successful, rolls out to all vending hubs.

---

## Tech Stack

| Layer | Detail |
|---|---|
| Backend | FastAPI (Python) |
| Database | PostgreSQL on Railway (prod) |
| DB driver | pg8000 (pure Python — no native libs, required for Railway) |
| Auth | JWT, 8hr expiry, bcrypt password hashing |
| Frontend | Single-file `static/index.html` — vanilla JS, no framework |
| Hosting | Railway.app |
| Source control | GitHub (push via Claude Code SSH) |

---

## Repo Structure

```
issg-roster-app/
├── main.py                    # FastAPI app, startup seeding, auto-wipes swings on boot
├── auth.py                    # JWT creation and verification, bcrypt
├── database.py                # SQLAlchemy models + pg8000 connection rewrite
├── build_flights_db.py        # Builds fmg_flights.db SQLite from JSON on startup
├── seed.py                    # (legacy — seeding now in main.py)
├── requirements.txt
├── railway.toml
├── .env.example
├── .gitignore
├── routers/
│   ├── auth_router.py         # POST /api/auth/token, GET /api/auth/me
│   ├── staff.py               # GET /api/staff/
│   ├── swings.py              # CRUD /api/swings/
│   ├── overrides.py           # CRUD /api/overrides/  (AL/LWOP calendar overrides)
│   ├── changes.py             # CRUD /api/changes/ + PUT /api/changes/{id}/status
│   ├── flights.py             # GET /api/flights/ — reads bundled SQLite
│   └── agent.py               # POST /api/agent/chat — proxies Anthropic API
├── static/
│   └── index.html             # Entire frontend — 1100 lines, vanilla JS
└── data/
    └── fmg_flights.json       # Source flight data for all FMG sites
```

---

## Database Models (database.py)

```
User          — username, full_name, hashed_password
Staff         — emp_number, full_name, role, hub, roster_type, village, site_code
Swing         — staff_emp, fly_in_date, fly_out_date, fly_in_flight, fly_out_flight,
                village, room_ref, notes
RosterOverride — staff_emp, date, status (AL/LWOP)
ChangeRequest  — staff_emp, change_type, effective_date, new_date, reason,
                 status, workflow_ref, created_at
```

**Critical:** `database.py` rewrites the `DATABASE_URL` env var to use `postgresql+pg8000://` driver. Do not change this — psycopg2-binary fails on Railway due to missing libpq.so.5.

---

## Staff (Eastern Hub)

| emp_number | Name | Role | Village |
|---|---|---|---|
| 764148 | Amanda Inglis-Baillie | Technician | JV |
| 807406 | Clive Ettia | Technician | KV |
| PETE-CASUAL | Pete Scully | Relief | JV |

Site: Christmas Creek (CC). Pattern: 8/6 FIFO, fly Wed.

---

## Auth / Users

Auto-seeded on startup:
- `britt` / `changeme123` — Brittany Crawford (Coordinator, primary user)
- `ryan` / `changeme123` — Ryan Weston (Ops Manager)

JWT token in `Authorization: Bearer <token>` header. 8hr expiry.

---

## Calendar Logic (index.html)

**Key rule:** Calendar shows CONFIRMED DATA ONLY. No auto-calculation fallback.

- `getStatusForDate(emp, ds)` — checks overrides first, then DB swings, returns `null` if no record
- `null` status = grey/blank cell, clickable to add swing
- Cells with a confirmed swing (any day type: FIAM, CC, FOAM) open swing detail modal on click
- No hover popover — removed. Click is the only interaction model.

Day type labels (cells only show these, never flight numbers):
- `FIAM` = Fly In (AM)
- `FOAM` = Fly Out (AM)
- `CC` = On Site
- `RR` = R&R (dimmed, grey cell)
- `AL` / `LWOP` = from overrides table

Villages: `JV` (orange), `KV` (red), `CB` (purple) — always shown on own line below day type pill.

---

## Change Request Workflow

Status flow: `Requested` → `In Progress` → `Confirmed` → `Complete`

- All requests submitted by Coordinator, Ops Manager, or Site Supervisor
- Mobe Coordinator actions in FMG Workflow (external system)
- FMG sends confirmation email to `roster-confirm@issg.net.au` (not yet built — Phase 3)
- On confirmation, status updates to `Confirmed`, staff member notified automatically (Phase 3)

Change types: `flight_change_in`, `flight_change_out`, `swing_extension`, `swing_cut_short`, `sick_leave`, `annual_leave`, `relief_mobilisation`

---

## Phase Status

| Phase | Status | What it is |
|---|---|---|
| 1 | ✅ Complete | Calendar, confirmed swings, change requests, mobilisation email drafts |
| 2 | 🔄 In Progress | Leave overlay (AL/LWOP UI), override controls |
| 3 | Planned | Role-based tabs, mobe queue, FMG email auto-parse, automated notifications |
| 4 | Planned | Rolling roster automation, multi-hub expansion |

---

## Known Decisions (Do Not Re-Litigate)

- **pg8000 only** — psycopg2 fails on Railway
- **No auto-calc pattern** — seeded swings wiped on startup; all data must be confirmed manually
- **No hover popover** — removed due to UX issues on touch devices
- **Single index.html** — all frontend in one file for simplicity
- **Confirmed-only calendar** — null status = empty grey cell, never a guessed state

---

## Environment Variables (Railway)

```
DATABASE_URL     — set by Railway Postgres plugin automatically
SECRET_KEY       — JWT signing key (set in Railway dashboard)
ANTHROPIC_API_KEY — for AI agent tab
```

Optional (Phase 3):
```
SMTP_EMAIL
SMTP_PASSWORD
```

---

## Deploy Process

1. Make changes locally
2. `git add . && git commit -m "description"`
3. `git push origin main`
4. Railway auto-deploys from main branch

OR: Upload zip via Railway dashboard → Deploy from zip.

---

## Dev Notes for Claude Code

- **Always ask clarifying questions before building any new feature or UI change**
- **Apply UI/UX best practices at all times**: clear visual hierarchy, contrast, consistent spacing, accessible labels, mobile-aware
- **Never start building until Ryan confirms the approach**
- Frontend changes = edit `static/index.html` only (backend is stable)
- Backend changes = likely `routers/` files or `database.py`
- After any change: run a syntax check, verify no broken references
- Commit message format: plain English, what changed and why

## Current Backlog (Priority Order)

1. Leave overlay UI — click cell to set AL/LWOP (Britt has no way to record leave currently)
2. Role-based tab visibility (Coordinator, Supervisor, Mobe views)
3. Mobe queue view — pending requests with action workflow
4. Email notifications — auto-trigger on status change
5. FMG email auto-parse — roster-confirm@issg.net.au inbox monitoring
6. Rolling roster feature — auto-generate swings from pattern + FMG email confirmation
7. Multi-hub expansion

## Pending Inputs Required

- FMG Workflow confirmation email template (critical for Phase 3 parser)
- Mobe team user names and email addresses
- Supervisor list with assigned hub per person
- Confirm roster-confirm@issg.net.au inbox can be provisioned (Avantegarde)
- Staff email addresses for automated notifications

## Future Features (FF) workflow
New features are specced before they're built. Run `/ff <name>` to start (`/ff quick "<idea>"` to just stash an idea, `/ff list` to see the backlog). It drives need-validation → codebase stress-test → full spec, and only emits a build prompt once the spec is **complete**.
- Registry/backlog: `docs/FUTURE_FEATURES.md` (existing direction also in `roster-tool-ROADMAP.md`) · full specs: `docs/future-features/FF-NNN-slug.md` · template: `docs/future-features/_TEMPLATE.md`
- **Do not start building an FF until its Status is `Ready for Build`.**
- Standard across all projects: `~/.claude/DOCUMENTATION_STANDARDS.md`.
