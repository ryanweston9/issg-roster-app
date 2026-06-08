# ISSG Roster App — Product Specification
**Version:** 1.0  
**Date:** March 2026  
**Author:** Ryan Weston, Operations Manager — ISSG  
**Status:** Active development — Eastern Hub trial

---

## 1. Purpose

This document is the authoritative product specification for the ISSG FIFO Roster Management System. It defines what the system does, how it works, all data models, all UI behaviour, all API contracts, role permissions, and the rules Claude Code must follow when building or modifying any part of this application.

**Read this before touching any file.**

---

## 2. Problem Statement

ISSG manages FIFO vending technicians across remote Pilbara mining sites. Prior to this system:

- Swing data (flights, dates, villages) was tracked across uncontrolled Excel spreadsheets — error-prone, not auditable, version conflicts frequent
- Change requests (flight changes, leave, relief mobilisation) were handled ad hoc via email and phone with no tracking or audit trail
- The Coordinator spent significant time on manual follow-up and communication that should be systematised
- Mobilisation coordinators had no structured queue — no visibility of what needed actioning or what was done
- Management had no real-time view of who was on site, in transit, or on R&R at any time

---

## 3. Solution Overview

A login-protected web application accessible from any browser. Single source of truth for:

- Confirmed swing records (fly-in/fly-out dates, flights, village, room)
- A rolling 14-day roster calendar per staff member
- Structured change request workflow (submit → action → confirm → notify → complete)
- Automated communications to staff and requestors on confirmation
- Role-based access across Coordinator, Ops Manager, Supervisor, Mobe Coordinator, HR, GM

**Design principle — confirmed data only.** The calendar never displays assumed, calculated, or fabricated data. If a swing is not entered by an authorised user, the cell is blank and grey. No exceptions.

---

## 4. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Backend | FastAPI (Python 3.11) | |
| Database | PostgreSQL | Railway-hosted |
| DB driver | **pg8000 only** | psycopg2 fails on Railway — never change this |
| ORM | SQLAlchemy 2.x | |
| Auth | JWT + bcrypt | 8hr token expiry |
| Frontend | Vanilla JS, single `static/index.html` | No framework, no build step |
| Flight data | SQLite (fmg_flights.db) | Built from fmg_flights.json on startup |
| Hosting | Railway.app | Auto-deploy from GitHub main |
| Source control | GitHub | SSH deploy |

---

## 5. Repository Structure

```
issg-roster-app/
├── CLAUDE.md                  # Project brief — Claude Code reads this first
├── SPEC.md                    # This document
├── ROADMAP.md                 # V1 roadmap
├── main.py                    # App entry point, startup seeding
├── auth.py                    # JWT + bcrypt
├── database.py                # Models + pg8000 connection rewrite
├── build_flights_db.py        # Builds fmg_flights.db from JSON
├── requirements.txt
├── railway.toml
├── .env.example
├── .gitignore
├── routers/
│   ├── auth_router.py         # /api/auth/token, /api/auth/me
│   ├── staff.py               # /api/staff/
│   ├── swings.py              # /api/swings/ CRUD
│   ├── overrides.py           # /api/overrides/ CRUD
│   ├── changes.py             # /api/changes/ CRUD + status update
│   ├── flights.py             # /api/flights/
│   └── agent.py               # /api/agent/chat
├── static/
│   └── index.html             # Entire frontend
└── data/
    └── fmg_flights.json
```

---

## 6. Data Models

### 6.1 User
```
id              INT PK
username        VARCHAR UNIQUE
full_name       VARCHAR
hashed_password VARCHAR
role            VARCHAR  -- coordinator, ops_manager, supervisor, mobe, hr, gm, admin
hub             VARCHAR  -- EAST, WEST, NORTH, PERTH (null = all hubs)
created_at      TIMESTAMP
```

### 6.2 Staff
```
id              INT PK
emp_number      VARCHAR UNIQUE   -- e.g. "764148", "PETE-CASUAL"
full_name       VARCHAR
role            VARCHAR          -- Technician, Relief
hub             VARCHAR          -- EAST
roster_type     VARCHAR          -- "8/6", "casual"
roster_expiry   DATE             -- null for casual
village         VARCHAR          -- JV, KV, CB (default)
site_code       VARCHAR          -- CC, SOL, ELI etc
is_active       BOOLEAN
```

### 6.3 Swing
```
id              INT PK
staff_emp       VARCHAR FK→Staff.emp_number
fly_in_date     DATE
fly_out_date    DATE
fly_in_flight   VARCHAR          -- e.g. QF2924
fly_out_flight  VARCHAR
village         VARCHAR          -- JV, KV, CB
room_ref        VARCHAR          -- optional
notes           TEXT             -- optional
confirmed       BOOLEAN DEFAULT true
created_by      VARCHAR          -- username of creator
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### 6.4 RosterOverride
```
id              INT PK
staff_emp       VARCHAR FK→Staff.emp_number
date            DATE
status          VARCHAR          -- AL, LWOP
created_by      VARCHAR
created_at      TIMESTAMP
```

### 6.5 ChangeRequest
```
id              INT PK
staff_emp       VARCHAR FK→Staff.emp_number
swing_id        INT FK→Swing.id  -- optional link to swing
change_type     VARCHAR          -- see §8.3
effective_date  DATE
new_date        DATE             -- optional
new_flight      VARCHAR          -- optional, for flight change types
reason          TEXT
status          VARCHAR          -- requested, in_progress, confirmed, complete
workflow_ref    VARCHAR          -- FMG Workflow reference, logged when booked
submitted_by    VARCHAR          -- username
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### 6.6 Notification (Phase 3)
```
id              INT PK
change_request_id INT FK
recipient_type  VARCHAR          -- staff, requestor
recipient_email VARCHAR
sent_at         TIMESTAMP
status          VARCHAR          -- sent, failed
```

---

## 7. API Contracts

### Auth
```
POST /api/auth/token
  Body: form-data { username, password }
  Returns: { access_token, token_type, full_name }

GET /api/auth/me
  Header: Authorization: Bearer <token>
  Returns: { username, full_name, role, hub }
```

### Staff
```
GET /api/staff/
  Returns: [ Staff ]
  Auth: required
```

### Swings
```
GET    /api/swings/               Returns all swings (filterable by ?staff_emp=)
POST   /api/swings/               Create swing
GET    /api/swings/{id}           Get single swing
PUT    /api/swings/{id}           Update swing
DELETE /api/swings/{id}           Delete swing
```

All require auth. Body for POST/PUT:
```json
{
  "staff_emp": "764148",
  "fly_in_date": "2026-03-19",
  "fly_out_date": "2026-03-27",
  "fly_in_flight": "QF2924",
  "fly_out_flight": "QF2925",
  "village": "JV",
  "room_ref": "A14",
  "notes": ""
}
```

### Overrides
```
GET    /api/overrides/            Returns all overrides
POST   /api/overrides/            Create override { staff_emp, date, status }
DELETE /api/overrides/{id}        Remove override
```

### Change Requests
```
GET    /api/changes/              Returns all change requests
POST   /api/changes/              Create request
GET    /api/changes/{id}          Get single request
PUT    /api/changes/{id}/status   Update status
  Body: { status, workflow_ref? }
DELETE /api/changes/{id}          Delete request
```

### Flights
```
GET /api/flights/
  Params: ?site=CC &direction=inbound|outbound &day_of_week=Wednesday
  Returns: [ Flight ]
  Source: fmg_flights.db (SQLite, built on startup)
```

### Agent
```
POST /api/agent/chat
  Body: { messages: [ { role, content } ] }
  Returns: { reply: string }
  Proxies to Anthropic claude-sonnet API
```

---

## 8. Business Rules

### 8.1 Calendar Status Logic

Priority order (first match wins):
1. **RosterOverride** — AL or LWOP for that staff member on that date
2. **Swing record** — if fly_in_date matches → FIAM; fly_out_date matches → FOAM; date falls between → CC
3. **No record** → `null` (blank grey cell)

`null` is never displayed as a status — it renders as an empty grey cell.

### 8.2 Day Type Labels (displayed in cells)

| Code | Label |
|---|---|
| FIAM | Fly In (AM) |
| FIPM | Fly In (PM) |
| FOAM | Fly Out (AM) |
| FOPM | Fly Out (PM) |
| CC | On Site |
| RR | R&R |
| AL | Annual Leave |
| LWOP | LWOP |

Flight numbers are **never displayed in cells**. They appear only in the swing detail modal.

### 8.3 Change Request Types

| Type | Description |
|---|---|
| flight_change_in | Change the fly-in flight |
| flight_change_out | Change the fly-out flight |
| swing_extension | Extend fly-out date |
| swing_cut_short | Early fly-out |
| sick_leave | Staff member sick on site or travelling |
| annual_leave | Planned leave |
| relief_mobilisation | Deploy Pete or another casual to cover |

### 8.4 Change Request Status Flow

```
requested → in_progress → confirmed → complete
```

- `requested` — submitted by Coordinator, Ops Manager, or Supervisor
- `in_progress` — Mobe Coordinator has picked it up, actioning in FMG Workflow
- `confirmed` — FMG Workflow confirmation received (Phase 3: auto via email parse; Phase 1-2: manual)
- `complete` — all done, Mobe marks complete, requestor notified

### 8.5 Village Codes

| Code | Name | Colour |
|---|---|---|
| JV | Java Village | Orange (#F7951E) |
| KV | Kariyarra Village | Red (#B21C24) |
| CB | Cloudbreak Village | Purple (#7C3AED) |

Village pill always displays on its own line below the day type pill in calendar cells.

### 8.6 Swing Seeding Rules

**No auto-seeding.** On startup, `main.py` wipes the swings table. All swing data must be entered manually by an authorised user. This was a deliberate decision to prevent ghost/phantom data from polluting the calendar.

---

## 9. Frontend Specification

### 9.1 Architecture

Single file: `static/index.html`  
Vanilla JS — no framework, no build step, no npm.  
All CSS in `<style>` block inside `<head>`. No external stylesheets except Google Fonts (Inter).  
All JS at bottom of `<body>` in a single `<script>` block.

### 9.2 Colour Palette (CSS variables)

```css
--red:        #B21C24   /* primary brand */
--orange:     #F7951E   /* secondary / JV village */
--dark:       #1A1A2E   /* topbar, dark backgrounds */
--bg:         #F7F8FA   /* page background */
--card:       #FFFFFF
--border:     #E4E6EA
--muted:      #6B7280
--rr-bg:      #F3F4F6   /* R&R and empty cell background */
--green-light:#DCFCE7
--jv:         #F7951E
--kv:         #B21C24
--cb:         #7C3AED
```

### 9.3 Tab Structure

| Tab | ID | Description |
|---|---|---|
| Roster | tab-roster | 14-day calendar + staff strip |
| Swings | tab-swings | List of confirmed swing records |
| Changes | tab-changes | Change request queue |
| AI Agent | tab-agent | Chat interface, proxies to Claude |

### 9.4 Calendar Behaviour

**Staff strip** — row of cards above calendar showing today's status for each staff member.

**Calendar table** — 14-day window. Staff as rows, dates as columns. Today's column highlighted.

**Cell types and behaviour:**

| State | Background | Click action |
|---|---|---|
| Has confirmed swing | White | Open swing detail modal |
| Empty (null) | Grey (#F3F4F6) | Open "Add Swing" modal pre-filled with staff + date |
| R&R | Grey (#F3F4F6) | None (not yet interactive) |
| AL / LWOP | White | None |

**No hover interactions.** Click is the only interaction model. Hover popover was removed and must not be reinstated.

**Cell content layout:**
```
[ Day Type Pill ]   ← line 1
[ Village Pill  ]   ← line 2 (only if on-site day)
```

**R&R cells:** No pill. Dimmed grey text label only. Grey cell background.

**Empty cells:** Completely blank. Grey background. Cursor pointer to indicate clickable.

### 9.5 Swing Detail Modal

Opens on click of any cell that has a confirmed swing record (FIAM, CC, FOAM).

Contains:
- Staff name + swing date range + village
- Fly-in card (flight number, date, depart→arrive times)
- Fly-out card (same)
- Info strip: Village | Room | Days on site | Notes
- Change request buttons: Change Fly-In | Change Fly-Out | Other / General

Flight cards highlight on hover (red border + light red background).

### 9.6 Add Swing Modal

Pre-fills staff member and fly-in date when opened from a grey calendar cell.

Fields:
- Staff member (dropdown)
- Fly-in date + Fly-out date
- Fly-in flight + Fly-out flight (text input + flight suggestions loaded from API by day of week)
- Village (JV / KV / CB)
- Room ref (optional)
- Notes (optional)

### 9.7 Change Request Modal

Fields:
- Staff member
- Change type (dropdown)
- Effective date
- New date (optional)
- New flight number (shown only for flight_change_in / flight_change_out)
- Reason / notes

### 9.8 Changes Tab

Each change request card shows:
- Staff member + change type + effective date
- Status badge (colour coded)
- FMG Workflow reference (if logged)
- Reason text
- Actions: View Draft Email | Mark In Progress | Mark Confirmed | Mark Complete | Delete

Status badge colours:
- `requested` — grey
- `in_progress` — amber
- `confirmed` — green
- `complete` — red (closed)

### 9.9 Mobilisation Draft Email

Auto-generated from change request data. Format:
```
To: mobilisation@issg.net.au
Subject: Roster Change Request - [Staff Name] / [Site]

Hi Team,

Please action the following roster change in FMG Workflow:

Technician: [name]
Change Type: [type]
Effective Date: [date]
New Date: [if applicable]
Site: Christmas Creek (CCK)

Reason: [reason]

Please confirm once actioned in Workflow and provide the booking reference.

Regards,
[current user name]
ISSG - Eastern Hub
```

---

## 10. Role Permissions

| Permission | Ops Manager | Coordinator | Site Supervisor | Mobe Coordinator | HR Manager | GM / MD |
|---|---|---|---|---|---|---|
| View roster | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| View team's submitted requests | ✓ | — | — | — | — | — |
| Submit change requests | ✓ | ✓ | ✓ | — | — | — |
| Add / edit confirmed swings | ✓ | ✓ | — | ✓ | — | — |
| Action / progress change requests | ✓ | ✓ | — | ✓ | — | — |
| View own KPI data | — | — | — | ✓ | — | — |
| View all coordinator KPI data | — | — | — | — | ✓ | — |
| Manage users and permissions | — | — | — | — | ✓ | — |

**Phase 1–2:** All roles see the same tabs. Role-based tab separation is Phase 3.

---

## 11. Staff — Eastern Hub

| emp_number | Name | Role | Default Village | Site |
|---|---|---|---|---|
| 764148 | Amanda Inglis-Baillie | Technician | JV | CC |
| 807406 | Clive Ettia | Technician | KV | CC |
| PETE-CASUAL | Pete Scully | Relief | JV | CC |

---

## 12. Users — Seeded on Startup

| Username | Full Name | Role | Password |
|---|---|---|---|
| britt | Brittany Crawford | coordinator | changeme123 |
| ryan | Ryan Weston | ops_manager | changeme123 |

---

## 13. Environment Variables

```bash
# Required
DATABASE_URL        # Set automatically by Railway Postgres plugin
SECRET_KEY          # JWT signing key — set in Railway dashboard

# Required for AI agent tab
ANTHROPIC_API_KEY

# Phase 3 — not yet required
SMTP_EMAIL
SMTP_PASSWORD
ROSTER_CONFIRM_INBOX  # roster-confirm@issg.net.au
```

---

## 14. Non-Negotiable Technical Rules

These are locked decisions. Do not propose alternatives without flagging first.

1. **pg8000 only** — never use psycopg2 or psycopg3. Railway lacks libpq.
2. **No auto-calc fallback** — calendar never generates a status from a date pattern. null = no data.
3. **No hover popover** — removed permanently. Click-only interaction model.
4. **Single index.html** — no split files, no framework, no build step.
5. **CSS inside `<head>`** — style block must be inside `<head>`. Never in body.
6. **Swings wiped on startup** — `main.py` runs `db.query(Swing).delete()` on every boot. Intentional.
7. **Flight numbers never in cells** — only in swing detail modal.
8. **Village always on own line** — second line below day type, every time.
9. **Railway + GitHub deploy** — no other hosting approach.
10. **No localStorage** — all state in JS variables. No browser storage.

---

## 15. Known Issues / Technical Debt

- No role-based tab visibility yet (all roles see all tabs)
- No leave overlay UI (Britt cannot set AL/LWOP via calendar click — must use overrides API directly)
- Flight time pre-load on login is partial — times may show as "unavailable" if flight not in cache
- No automated email notifications
- No FMG email auto-parse
- AI agent tab is functional but context-free (no roster data injected into system prompt)

---

## 16. Claude Code Behaviour Rules

When working on this codebase:

1. **Ask clarifying questions before building any new feature or UI change.** Understand exactly what is needed before writing code.
2. **Apply UI/UX best practices at all times.** Clear visual hierarchy, sufficient contrast, consistent spacing, accessible labels, mobile-aware layouts.
3. **Never start building until Ryan confirms the approach.**
4. **Run pre-flight checks before delivery:** syntax check (`python3 -m py_compile`), verify cross-file references, check for unclosed DB connections, None guards, division by zero guards.
5. **State exactly where each file goes** (full path relative to repo root), whether it replaces an existing file or is new, and include commit/push steps.
6. **Comment all code clearly.**
7. **Explain what code does before writing it** for any non-trivial change.
