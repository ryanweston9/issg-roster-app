# FF-001 — Leave Recording (`leave-recording`)

> Standalone Future-Feature spec. Created/maintained by `/ff`. One feature per file.
> Keep the matching one-line entry in this project's `FUTURE_FEATURES.md` registry in sync
> (same change, every change). **This feature is not built until Status reaches `Ready for Build`.**

**Status:** In Build <!-- Draft → Validated → Speccing → Ready for Build → In Build → Shipped -->
**Added:** 2026-06-11
**Updated:** 2026-06-11
**Owner:** Ryan Weston
**Related:** `roster-tool-ROADMAP.md` Phase 1 (Leave Recording); `roster-tool-SPEC.md`

---

## 1. Problem / Need  *(GATE — Need validation)*

- **Problem.** The roster calendar can *display* AL/LWOP (annual leave / leave without pay) from
  the `roster_overrides` table, but there is **no UI to create or remove an override**. Britt has
  no in-app way to record leave at all.
- **Who's affected.** Brittany Crawford (Coordinator, the primary daily user). Every time a staff
  member takes leave — a recurring, routine event in a FIFO operation.
- **Cost of inaction.** Leave stays tracked outside the app (Excel / memory), so the calendar is
  knowingly incomplete: an on-site day that is actually AL still shows as `CC`. That undermines the
  app's core promise — a single trustworthy roster — and is the #1 gap blocking V1 sign-off.
- **Alternatives considered** (incl. *do nothing*):
  - *Do nothing / keep leave in Excel* — rejected: defeats the purpose of the tool and is the
    explicit Phase 1 blocker in the roadmap.
  - *Model leave as a swing record* — rejected: leave isn't a swing; the data model already has a
    dedicated `RosterOverride` and `getStatusForDate` already prioritises it.
  - *Build a separate "Leave" admin tab* — rejected: slower for Britt than acting on the calendar
    cell she's already looking at; adds a surface for no benefit.
- **Success metric.** Britt can set and remove AL/LWOP entirely from the calendar; the change
  persists across refresh; zero remaining cases where she must record leave outside the app.

> Need is genuine and already validated by the roadmap. Status moved past this gate.

## 2. Goals & non-goals

- **Goals:**
  - Set AL or LWOP for a staff member over a **date range** (single day = range of one) from the
    calendar, persisted as one `RosterOverride` per day.
  - Remove an existing leave override from the calendar.
  - Consistent **click-to-act** interaction on every cell type (no hover, mobile-friendly).
  - No duplicate overrides for the same `(staff_emp, date)`.
- **Non-goals:**
  - No backend changes — the `/api/overrides/` endpoints and `RosterOverride` model are reused as-is.
  - No leave *approval* workflow, balances, accruals, or leave types beyond AL/LWOP.
  - No automated notifications (Phase 3).
  - No change-request linkage — leave is a direct calendar override, not a `ChangeRequest`.
  - Not fixing the pre-existing UTC date-string offset (see §3 risks) — only staying consistent with it.

## 3. Codebase stress-test — Repo audit (2026-06-11)  *(GATE)*

> Findings from reading the repo. This is a **frontend-only** feature; the backend already supports it.

- **Related / existing code (reuse, do not rebuild):**
  - `routers/overrides.py:44` — `POST /api/overrides/` (`staff_emp, date, status, notes`); sets
    `created_by` from the JWT user. Reuse directly.
  - `routers/overrides.py:57` — `DELETE /api/overrides/{override_id}`. Reuse for removal.
  - `routers/overrides.py:32` — `GET /api/overrides/` (optional `staff_emp` filter).
  - `database.py:64-72` — `RosterOverride(id, staff_emp, date, status, notes, created_by, created_at)`.
    Already has `notes`. **No unique constraint on `(staff_emp, date)`** → frontend must prevent dupes.
  - `static/index.html:517` — `allOverrides` is already fetched on login alongside swings/staff/changes.
  - `static/index.html:549-553` — `getStatusForDate()` already checks overrides **first**, so a new
    override renders immediately on re-render. No rendering logic change needed for display.
  - `static/index.html:632-633` — AL/LWOP already render as a `.rr-label`; CSS `.pill-AL`/`.pill-LWOP`
    exist at `:62-63` (used in the staff strip / labels).
  - `static/index.html:460` — `DT_LABEL` maps `AL`/`LWOP` to display text.
  - `static/index.html:786-815` (approx) — `openSwingModal()` is the existing pattern for a
    pre-filled, staff/date-locked modal; mirror its structure for the leave modal.
- **What must change (all in `static/index.html`):**
  - The three cell-click branches at `index.html:646-655`:
    - `cell-empty` (`:648`) currently calls `promptAddSwing` directly → route through a new chooser.
    - `cell-click` (swing, `:651`) currently calls `openSwingDetail` directly → route through chooser.
    - `cell-rr` (override-only, `:653-654`) is currently **not clickable** → make it open a remove path.
  - Add: an **action chooser** (small modal), a **leave modal** (staff locked, AL/LWOP, start/end
    date, optional notes), a **save loop**, and a **remove** handler. Plus a couple of helper fns
    (find override by emp+date; iterate a local date range with the same `toDateStr`).
- **Conflicts / risks:**
  - **Timezone / date-string landmine.** `toDateStr()` (`index.html:547`) uses
    `d.toISOString().slice(0,10)` — UTC. For Perth (UTC+8) a local-midnight `Date` serialises to the
    *previous* calendar day. This is a **pre-existing** pattern used by swings and override display
    alike, so it round-trips consistently *within the app*. **Constraint:** the range loop MUST build
    each day by incrementing a local `Date` and calling the same `toDateStr()`, so stored override
    dates line up exactly with the cells Britt clicked. Do **not** "fix" the offset here (out of scope;
    would desync existing swing data). Perth has no DST, so no DST drift.
  - **Duplicate overrides.** No DB uniqueness → saving onto a day that already has an override would
    create a second row; `getStatusForDate` returns the first match (stale). Mitigation: before
    POSTing a day, delete any existing override for that `(emp, date)` first (replace semantics).
  - **Live surface.** `static/index.html` is the deployed prod frontend. Single-file, vanilla JS,
    `var`/string-concat style — match it exactly (CLAUDE.md: surgical, match existing style).
  - **No bulk endpoint.** A range write = N sequential `POST`s client-side. Ranges are small
    (a swing is ~8 days; UI shows 14), so this is acceptable; no backend change.
- **New dependencies:** none.
- **Data model / migration:** none. `roster_overrides` table and columns already exist in prod.
- **Integration points:** `POST`/`DELETE /api/overrides/`, the existing `api()` helper, `allOverrides`
  in-memory array, `renderCalendar()` / `renderStaffStrip()` re-render after mutation.
- **Effort:** small — frontend-only, reuses existing endpoints, modal patterns, and render path.
  Independently shippable (additive; no backend or schema change).

## 4. Design / approach

Additive, frontend-only, reversible. All edits in `static/index.html`.

**A. Unified cell-click → action chooser.** Every calendar cell becomes clickable and opens a small
centered chooser modal (an "action sheet", not a hover popover) whose options depend on the cell's
current status (`getStatusForDate`):

| Cell state | Chooser options |
|---|---|
| Empty (`null`) | **Add Swing** · **Set Leave** |
| Swing day (`FIAM`/`CC`/`FOAM`/`RR`) | **View Swing** · **Set Leave** |
| Leave day (`AL`/`LWOP`) | **Remove Leave** |

- **Add Swing** → existing `openSwingModal(null, emp, ds)`.
- **View Swing** → existing `openSwingDetail(sw.id, ds)`.
- This satisfies the decisions: click-only trigger, leave allowed on **any** cell type, and it keeps
  the existing Add-Swing / swing-detail actions reachable (now one tap behind the chooser).

**B. Leave modal** (mirror `openSwingModal` structure):
- Staff member — pre-filled, locked.
- Leave type — `AL` | `LWOP` (radio or select).
- Start date — pre-filled to the clicked day. End date — pre-filled to the clicked day too
  (so a single-day entry needs no extra input).
- Notes — optional, maps to `RosterOverride.notes`.
- **[Save Leave]** / **[Cancel]**.

**C. Save loop (replace semantics, dup-safe):**
1. Build the inclusive list of dates from start→end by incrementing a **local** `Date` and applying
   `toDateStr()` (same fn the calendar uses).
2. Validate end ≥ start.
3. For each date: if an override already exists for `(emp, date)` in `allOverrides`, `DELETE` it
   first, then `POST` the new `{staff_emp, date, status, notes}`.
4. Re-fetch overrides (or splice the in-memory `allOverrides`), close modal, `renderCalendar()`.

**D. Remove leave:** chooser on a leave cell → **Remove Leave** → confirm → `DELETE /api/overrides/{id}`
(id looked up from `allOverrides` by emp+date) → update `allOverrides`, re-render. V1 removes the
single clicked day (block removal is not a goal; clicking each day is acceptable and matches reversibility).

**Safety profile:** additive UI, no backend/schema change, fully reversible per day, no destructive
bulk operations.

## 5. Acceptance criteria

- [ ] Clicking an **empty** cell opens the chooser with **Add Swing** + **Set Leave**.
- [ ] Clicking a **swing** cell (FIAM/CC/FOAM/RR) opens the chooser with **View Swing** + **Set Leave**; View Swing opens the existing detail modal.
- [ ] Clicking a **leave** (AL/LWOP) cell opens the chooser with **Remove Leave**.
- [ ] **Set Leave** with start = end writes exactly one override and the cell immediately shows AL/LWOP.
- [ ] **Set Leave** over a multi-day range writes one override per day inclusive; every day in the range shows AL/LWOP.
- [ ] Setting leave on a day that already had an override **replaces** it (no duplicate rows).
- [ ] Stored override dates match the clicked cells exactly (date-string consistency with the calendar).
- [ ] **Remove Leave** clears the override and the cell returns to its underlying state (empty or the swing day-type).
- [ ] All changes persist after a page refresh (data in Postgres, not memory).
- [ ] Works on mobile browser (Safari iOS / Chrome Android) — chooser and modal are tap-friendly, no hover dependency.
- [ ] No JS console errors across set/remove/range flows.

## 6. Test plan

Manual, against the running app (Railway dev/prod or local), logged in as `britt`:
1. **Single-day AL:** empty cell → Set Leave → AL, start=end → save → cell shows AL → refresh → still AL.
2. **Range AL:** pick a Mon→Fri range → save → all five cells show AL → refresh → persists.
3. **Replace:** set AL on a day, then set LWOP on the same day → cell shows LWOP, only one row exists
   (verify via `GET /api/overrides/?staff_emp=...`).
4. **Leave over a swing day:** on a `CC` cell → Set Leave → AL → cell shows AL (swing record still
   present underneath; removing the leave restores `CC`).
5. **Remove:** click an AL cell → Remove Leave → confirm → reverts to underlying state → refresh persists.
6. **Date consistency:** confirm the cell clicked == the cell that shows leave (no off-by-one).
7. **Mobile:** repeat 1 and 5 on a phone browser; chooser + modal usable by tap.
8. **Console:** no errors during any of the above.
> Per CLAUDE.md: syntax-check `index.html`, verify no broken references before declaring done.

## 7. Rollout

Additive, no migration, no flag. Standard project deploy: commit `static/index.html` →
`git push origin main` → Railway auto-deploys. Reversible by reverting the commit. Smoke-check the
single-day set/remove flow on the deployed URL after deploy (CLAUDE.md §5: verify ops, don't assume).

## 8. Open decisions

- [x] Leave span — **date range** (start/end, one override per day). *Resolved 2026-06-11.*
- [x] Trigger UI — **action chooser on cell click**. *Resolved 2026-06-11.*
- [x] Eligible cells — **any cell type**. *Resolved 2026-06-11.*
- No blocking decisions remain. (Minor, decided in §4: remove is single-day in V1; range write uses
  client-side replace-then-post; no bulk endpoint.)

## 9. Completeness checklist  *(GATE — must be all ✅ before build)*

- [x] Need validated (§1) — problem real, alternatives weighed, do-nothing rejected.
- [x] Goals & non-goals defined (§2).
- [x] Repo audit done with real `file:line` citations (§3).
- [x] Design chosen and phased if large (§4) — small, single increment.
- [x] Acceptance criteria are testable (§5).
- [x] Test plan covers each criterion (§6).
- [x] Rollout / migration understood (§7) — additive, no migration.
- [x] No **blocking** open decisions remain (§8).

> All ✅ → Status set to **Ready for Build**; registry synced; build prompt below.

## 10. Build prompt — ultracode handoff  *(filled only when Ready for Build)*

> Paste into a fresh turn to launch the build. References this spec, embeds CLAUDE.md guardrails,
> phases with verify gates.

```
ultracode: Implement FF-001 Leave Recording per docs/future-features/FF-001-leave-recording.md.

This is FRONTEND-ONLY (static/index.html). Do NOT touch the backend, database.py, or routers/ —
the /api/overrides/ POST+DELETE endpoints and RosterOverride model already exist and are reused as-is.

Honour this project's CLAUDE.md guardrails:
- Surgical changes only — match the existing single-file vanilla-JS style (var, string concat, no
  framework). Touch only the cell-click logic and add the new chooser/leave modal + handlers.
- Confirmed-data-only calendar; no auto-calc. Overrides already render via getStatusForDate.
- Click-only interaction, no hover popovers, mobile-aware (chooser + modal must be tap-friendly).
- After changes: syntax-check index.html, verify no broken references.
- Do NOT push to production without Ryan's explicit cutover.

Phases (each independently verifiable):
  1. Action chooser: route all three cell branches (index.html:646-655) through a small centered
     chooser modal; options vary by cell status (empty: Add Swing/Set Leave; swing: View Swing/Set
     Leave; leave: Remove Leave). Keep existing openSwingModal/openSwingDetail reachable.
     → verify: clicking each cell type opens the correct chooser; existing add/detail flows still work.
  2. Leave modal + save loop: staff locked, AL|LWOP, start+end date (default both = clicked day),
     optional notes. Build the date range by incrementing a LOCAL Date and using the existing
     toDateStr() (do NOT change toDateStr or its UTC behaviour). For each day: delete any existing
     override for (emp,date) then POST — replace semantics, no duplicates.
     → verify: single-day and multi-day ranges write correctly; re-setting a day replaces, never
       duplicates (check GET /api/overrides/?staff_emp=...); clicked cells == leave cells (no off-by-one).
  3. Remove leave: chooser on an AL/LWOP cell → confirm → DELETE /api/overrides/{id} (id from
     allOverrides by emp+date) → update allOverrides, re-render.
     → verify: cell reverts to underlying state (empty or swing day-type); persists after refresh.

Acceptance: all §5 criteria in the spec. Test per §6 (manual, logged in as britt, incl. mobile +
no console errors). Keep the FUTURE_FEATURES.md FF-001 Status line in sync in the same change as code.
```

## 11. Build notes (2026-06-11)

Built via multi-agent workflow (build → 4-lens adversarial review → fix → verify). All changes in
`static/index.html` only; backend untouched; `node --check` passes. Two deliberate deviations from
the design above, both improvements found during review:

- **Save ordering — create-then-delete (not delete-then-post, §3/§4-C).** The original delete-first
  loop would silently wipe an existing override if the replacement POST then failed (401/500/network).
  `saveLeave()` now POSTs the new override first, only deletes the old one on success, and `alert()`s +
  stops the loop on failure. Idempotent no-op when the same status already exists. End state is
  identical (one row, replaced); a failed DELETE-after-POST leaves a transient duplicate (no data loss;
  no DB uniqueness constraint anyway), surfaced on next login re-fetch.
- **Timezone display fix (decision 2026-06-11).** The `toDateStr` UTC offset means a cell's storage
  key sits one day behind its column header in AWST. Per §2/§3 we do **not** touch `toDateStr` or
  stored data — but to stop the new chooser/modal from *showing* dates a day behind (a foot-gun for
  range entry), `keyToDisplay(ds)`/`localYMD(d)` helpers map the stored key to the local date the
  header shows, for **display only**. The save loop iterates **local** dates and re-derives keys via
  `toDateStr` (the calendar's own transform), so stored leave lands on exactly the cells the picker
  displays. Verified in `TZ=Australia/Perth`: click "Thu 11 Jun" → chooser + modal show "11 Jun";
  range 11→15 Jun renders on cells 11–15 Jun; storage keys stay offset (consistent with swings).

**Smoke test (2026-06-11, 15/15 passed).** Ran the real FastAPI server locally (SQLite DB, prod
seed) and replayed the exact frontend algorithm against the live API in `TZ=Australia/Perth`, logged
in as `britt`: login; single-day set (one row, on the clicked cell key, renders AL); replace AL→LWOP
(no duplicate row); remove (cleared); multi-day range 11→15 Jun (5 rows, render on exactly cells
11–15 Jun = picker selection); persistence across re-fetch; leave-over-swing (override wins, remove
reverts to CC with swing intact); modal date display matches the clicked cell header. Served page
confirmed to contain all new elements/handlers.

**Still required before Shipped:** visual/manual eyeball of the chooser + modal in a real browser
incl. mobile (iOS Safari / Android Chrome) and a console-error sweep (the algorithm/data/persistence
are proven; only on-screen rendering + tap ergonomics remain), then Ryan's cutover. Note: tested
against SQLite locally, not Postgres — schema is identical via SQLAlchemy, but prod is pg8000.
