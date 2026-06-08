# ISSG Roster App — V1 Roadmap
**Version:** 1.0  
**Date:** March 2026  
**Scope:** Eastern Hub (Christmas Creek) — usable V1  
**Read SPEC.md first.** This document defines what to build and in what order.

---

## Definition of V1

V1 is complete when Brittany Crawford (Coordinator) can:

1. Log in and see a live roster calendar for Eastern Hub
2. Add, edit, and delete confirmed swing records
3. Record leave (AL/LWOP) directly on the calendar
4. Submit change requests and track them through to completion
5. Copy a mobilisation draft email for any request
6. Hand off confirmed requests to the mobe team with full visibility on both sides

V1 does **not** include: automated email notifications, FMG email parsing, role-based tab separation, multi-hub, or rolling roster automation. Those are Phase 3+.

---

## Current State (as of v6)

### ✅ Done and working
- Login (JWT, bcrypt, 8hr token)
- 14-day calendar with confirmed-data-only logic
- Staff strip (today's status per staff member)
- Swing CRUD (add, edit, delete via Swings tab and calendar)
- Click-to-open swing detail modal (FIAM, CC, FOAM cells)
- Click-empty-cell to open Add Swing modal pre-filled
- Change request submission (all types)
- Change request status progression (Requested → In Progress → Confirmed → Complete)
- Mobilisation draft email generation
- FMG Workflow reference logging (on mark-as-booked)
- AI agent tab (functional, context-free)
- Flight data loaded from fmg_flights.json on startup
- Flight suggestions in swing add modal (by day of week)
- Village pill on own line below day type
- R&R cells greyed with dimmed text
- Empty cells grey and clickable
- CSS inside `<head>` (fixed)
- No hover popover (removed)
- No auto-calc fallback (removed)

### ❌ Not yet built (V1 blockers)
- Leave overlay UI (AL/LWOP via calendar click)
- Flight times pre-loaded on login (times currently may show unavailable)
- Changes tab badge count (open requests)

### ⚠️ Partial / needs improvement
- Changes tab visibility — all roles see all tabs (role separation is Phase 3, acceptable for now)
- AI agent has no roster context injected
- Swing detail modal flight times rely on flight cache — cache not guaranteed on first load

---

## V1 Build Sequence

Work through these in order. Do not skip ahead. Each phase must be confirmed working before starting the next.

---

### Phase 1 — Leave Recording (Priority 1)
**Why:** Britt has no way to record AL or LWOP through the UI. This is the biggest functional gap.

**What to build:**

A. **Leave modal** — opens when user clicks any calendar cell that currently has:
   - A confirmed swing record with status CC (on site)
   - An empty/null cell

   Modal fields:
   ```
   Staff member (pre-filled, locked)
   Date (pre-filled, locked)
   Leave type: AL | LWOP
   Notes (optional)
   [Save Leave] [Cancel]
   ```

B. **Remove leave** — cells showing AL or LWOP need an X or remove option in the same modal.

C. **Calendar rendering** — already handles overrides correctly. No calendar changes needed, just the UI to create/delete them.

**API endpoints to use:**
```
POST   /api/overrides/   { staff_emp, date, status }
DELETE /api/overrides/{id}
```

**Trigger:** Right-click on any calendar cell → "Set Leave" OR add a small leave button in the swing detail modal for on-site days.

**Acceptance criteria:**
- Britt can click a CC cell → set it to AL → calendar immediately shows AL
- Britt can click an AL cell → remove the override → calendar returns to CC
- Leave persists after page refresh

---

### Phase 2 — Flight Pre-load Fix
**Why:** Swing detail modal currently shows "Times unavailable" if the flight cache hasn't been populated. Unreliable UX.

**What to build:**

On login (`showApp()`), pre-load ALL flights for CC (inbound + outbound) into `flightCache` before rendering the calendar.

Current code calls:
```javascript
await api('/api/flights/?site=CC&direction=inbound');
await api('/api/flights/?site=CC&direction=outbound');
```

Problem: This runs but `flightCache` is keyed by flight number. If a swing uses a flight number not in cache, it shows unavailable.

Fix: After pre-load, also pre-load any flight numbers referenced in `allSwings` that aren't already in cache. On swing load, extract all unique flight numbers and fetch any missing ones.

**Acceptance criteria:**
- Open any swing detail modal → flight times always display correctly
- No "Times unavailable" text after login

---

### Phase 3 — Changes Tab Badge
**Why:** Minor UX fix. The badge on the Changes tab should show the count of open (non-complete) requests.

**What to build:**
`updateChangesBadge()` already exists. Confirm it runs correctly:
- On login
- After any change request is created
- After any status update

If the badge isn't updating, trace the call chain and fix.

**Acceptance criteria:**
- Changes tab badge shows correct count of open requests
- Updates immediately when a request is created or completed

---

### Phase 4 — Swing Edit from Detail Modal
**Why:** Currently, Britt must go to the Swings tab to edit a swing. Should be doable from the calendar.

**What to build:**

Add an "Edit Swing" button to the swing detail modal (top right, alongside Close).

Clicking it:
1. Closes the swing detail modal
2. Opens the swing add/edit modal pre-filled with the swing's existing data
3. On save, updates the swing record and re-renders the calendar

**Acceptance criteria:**
- Click any CC / FIAM / FOAM cell → swing detail opens → click Edit → edit modal opens pre-filled
- Save → calendar updates immediately

---

### Phase 5 — AI Agent Context Injection
**Why:** The AI agent tab is live but useless — it has no knowledge of the current roster state.

**What to build:**

When the user sends a message via the agent tab, inject a system prompt into the API call that includes:

```
Current roster context (as of [today's date]):
- Hub: Eastern Hub / Christmas Creek
- Staff:
  [for each staff member: name, today's status, current swing dates if any]
- Open change requests: [count] open, [list of summaries]
- Upcoming fly-ins this week: [list]
```

Build a `buildRosterContext()` function that generates this string from `allSwings`, `allStaff`, `allChanges`.

Pass it as the system message in the `/api/agent/chat` call.

**Acceptance criteria:**
- Ask the agent "Who is on site today?" → correct answer
- Ask "What change requests are open?" → correct answer
- Ask "When is Clive's next fly-in?" → correct answer

---

### Phase 6 — Mobe Queue View
**Why:** Phase 3 of the product spec. Mobe coordinators need a dedicated view of pending requests.

**What to build:**

New tab: **Mobe Queue** (hidden until role-based access is built — add the tab but hide it with `display:none` for now, controlled by a `SHOW_MOBE_TAB = true/false` JS constant at the top of the script).

The Mobe Queue tab shows only requests with status `requested` or `in_progress`, sorted by submission date ascending (oldest first).

Each card shows:
- Staff member + change type + effective date
- Days since submitted (highlight red if >2 days)
- Reason
- Actions: Mark In Progress | Log FMG Reference + Mark Confirmed | Mark Complete

No delete option in this view — mobe team cannot delete requests.

**Acceptance criteria:**
- Cards show only open/in-progress requests
- Status updates from this tab persist correctly
- Empty state message when no open requests

---

### Phase 7 — Manual Email Notification (Bridge until Phase 3 auto-notify)
**Why:** Until FMG email parsing is built, the Coordinator needs a way to notify staff of confirmed changes without manually drafting emails.

**What to build:**

When a request reaches `confirmed` status, show a "Copy Staff Notification" button alongside "Copy Draft Email".

Staff notification template:
```
Hi [Staff Name],

Your roster has been updated:

Change: [change type in plain language]
Effective: [effective date]
[New flight: QF2924 | Perth → Christmas Creek | Departs 06:00 Arrives 08:20]
[New fly-out: 27 March 2026]

If you have any questions, contact the office.

ISSG Operations
```

This is a copy-to-clipboard button, not an auto-send. Britt copies and pastes into email manually until Phase 3 auto-send is built.

**Acceptance criteria:**
- Button appears on confirmed requests only
- Template populates correctly from request + swing data
- Copies to clipboard in one click

---

## V1 Complete Checklist

Before calling V1 done, verify all of these:

- [ ] Britt can log in
- [ ] Calendar renders correctly — confirmed swings only, no ghost data
- [ ] Empty cells are grey and open Add Swing on click
- [ ] All swing CRUD works (add, edit from calendar, delete)
- [ ] Leave (AL/LWOP) can be set and removed via calendar UI
- [ ] Flight times display correctly in swing detail modal
- [ ] Change requests can be submitted for all 7 types
- [ ] Status can be progressed through all stages
- [ ] FMG reference number can be logged
- [ ] Mobilisation draft email generates correctly
- [ ] Staff notification copy works for confirmed requests
- [ ] Changes tab badge shows correct open count
- [ ] AI agent gives correct answers about current roster state
- [ ] All data persists after page refresh (stored in Postgres, not localStorage)
- [ ] App works on mobile browser (Safari iOS, Chrome Android)
- [ ] No JS console errors on normal usage flows

---

## What Comes After V1

These are explicitly out of scope for V1. Do not build them early.

| Feature | Phase | Trigger |
|---|---|---|
| Role-based tab separation | Phase 3 | Mobe team onboarded |
| FMG email auto-parse | Phase 3 | FMG email template obtained |
| Automated staff notifications | Phase 3 | SMTP inbox provisioned |
| Rolling roster auto-generation | Phase 4 | FMG email template + mobe confirmed |
| Multi-hub expansion | Phase 5 | Eastern Hub V1 signed off by Ryan |
| Casual pool / shutdown management | Phase 5 | Separate scoping required |
| HR KPI dashboard | Phase 3 | HR Manager user created |
| Asset tracking | Separate project | Scoped with Emma/Jenae |

---

## Pending Inputs (Blocking Phase 3+)

These must be collected before Phase 3 work can begin. Not blocking V1.

| Input | Owner | Status |
|---|---|---|
| FMG Workflow confirmation email template | Ryan | ⏳ Pending |
| roster-confirm@issg.net.au inbox provisioning | Avantegarde (IT) | ⏳ Pending |
| Staff email addresses for notifications | HR | ⏳ Pending |
| Mobe coordinator names + email addresses | HR | ⏳ Pending |
| Supervisor list + assigned hub | Ryan | ⏳ Pending |

---

## How to Use This Document in Claude Code

Start a Claude Code session with:

```
Read SPEC.md and ROADMAP.md. Confirm you understand the current state and what Phase 1 of the roadmap requires. Then ask me one clarifying question before starting.
```

After each phase is complete:

```
Phase [N] is done and tested. Update ROADMAP.md to mark it complete, then confirm what Phase [N+1] requires before starting.
```

Keep ROADMAP.md updated as phases complete — it's the live state of the build.
