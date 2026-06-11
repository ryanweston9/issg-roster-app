# FF-002 — Flight data fix (`flight-data-fix`)

> Standalone Future-Feature spec. Created/maintained by `/ff`. One feature per file.
> Keep the matching one-line entry in this project's `FUTURE_FEATURES.md` registry in sync
> (same change, every change). **This feature is not built until Status reaches `Ready for Build`.**

**Status:** Shipped <!-- Draft → Validated → Speccing → Ready for Build → In Build → Shipped -->
**Added:** 2026-06-11
**Updated:** 2026-06-11
**Owner:** Ryan Weston
**Related:** `roster-tool-ROADMAP.md` Phase 2 (Flight pre-load fix); [[ff-spec-workflow]]

---

## 1. Problem / Need  *(GATE — Need validation)*

- **Problem.** The swing detail modal shows **"Times unavailable"** and the Add-Swing flight
  picker shows **"No flights on this day"** — for *every* flight. **Root cause (reproduced):** the
  flights SQLite stores `site = "Christmas Creek"`, but the app queries `?site=CC`, which the
  router uppercases to `"CC"` and matches exactly against the stored value → **zero rows**. So
  `flightCache` is *always empty* and the day-of-week picker *always* returns nothing. The
  roadmap's framing ("cache hasn't populated yet" / "fetch missing numbers") is a misdiagnosis —
  there is no fetch-by-number endpoint and the cache never populates at all.
- **Who's affected.** Britt (Coordinator) on every swing she views and every swing she adds; the
  flight picker — a Phase-1 "done" feature — is in fact non-functional in prod.
- **Cost of inaction.** Flight times never display; the picker can't suggest flights, forcing
  free-text entry from memory (error-prone). Undermines the swing/flight half of the tool.
- **Alternatives considered** (incl. *do nothing*):
  - *Do nothing* — rejected: a core feature is silently broken in prod.
  - *Pre-load missing numbers (roadmap's suggestion)* — rejected: infeasible (no by-number
    endpoint) and treats a symptom; the cache is empty for *all* numbers, not some.
  - *Fix it in the frontend by querying the full site name* — viable (see §8), but a backend
    site-code alias is the cleaner contract fix (decided 2026-06-11).
- **Success metric.** After login, scheduled flights show real depart/arrive times in the swing
  detail modal and the Add-Swing picker lists flights for the chosen day; zero spurious
  "Times unavailable" for scheduled flights.

## 2. Goals & non-goals

- **Goals:**
  - Flight queries by site **code** (`CC`) return the matching site's flights.
  - `flightCache` populates on login; swing detail shows real times for scheduled flights.
  - Add-Swing day-of-week picker lists flights again.
  - A flight number genuinely **not** in the schedule degrades gracefully (show the number +
    "No scheduled time", not "Times unavailable").
- **Non-goals:**
  - No change to the flights data or `build_flights_db.py`.
  - No new by-flight-number endpoint; no fetching arbitrary numbers.
  - No validation/locking of the free-text flight inputs.

> **Scope expanded 2026-06-11** (Ryan follow-up: "live across all sites, inline, no page
> refresh"). The original CC-only non-goals below in §2 are **superseded** — see §11. The cache now
> covers every hub and resolves times by the swing's actual day, and the picker follows the staff's
> site. Still no data/build/endpoint changes.

## 3. Codebase stress-test — Repo audit (2026-06-11)  *(GATE)*

> Findings from reading the repo + an empirical DB query. Root cause confirmed against real data.

- **Reproduced root cause:** built `data/fmg_flights.db` from `data/fmg_flights.json` and ran the
  app's exact query `SELECT * FROM flights WHERE site = 'CC' AND direction = 'inbound'` → **0 rows**.
  Stored `site` values are full names: `Christmas Creek, Cloudbreak, Eliwana, Port Hedland,
  Solomon, Iron Bridge`. CC actually has 13 inbound / 12 outbound flights, all under
  `site = "Christmas Creek"`.
- **Backend — the bug + fix site:** `routers/flights.py:43-46` — `if site: query += " AND site = ?";
  params.append(site.upper())`. Two problems: (a) `"CC".upper()` never matches `"Christmas Creek"`;
  (b) even passing the full name fails because `.upper()` turns it into `"CHRISTMAS CREEK"` ≠ stored
  title-case. Fix: resolve a site **code→name alias** then match **case-insensitively**.
  `day_of_week` filter (`:47-49`, `.capitalize()`) already matches stored `"Friday"` — leave it.
- **Frontend — cache + display:**
  - `static/index.html:563-568` `preloadFlights()` queries `?site=CC` inbound + outbound and keys
    `flightCache` by `flight_number`. **No frontend change needed** — it starts working once the
    backend alias lands. (No error guard, CC-only — acceptable, out of scope.)
  - `static/index.html:541-550` `showApp()` awaits `preloadFlights()` before render — ordering fine.
  - `static/index.html:884,890` swing detail: `fiData ? times : (fiF ? 'Times unavailable' :
    'No flight set')` — the **only** scary fallback; change "Times unavailable" → graceful text.
  - `static/index.html:931-944` Swings tab already degrades silently (shows number, omits time) —
    no change required.
  - `static/index.html:367,371` flight-number fields are **free-text** `<input type="text">`, so
    unknown numbers are possible and must degrade gracefully (goal above).
  - `static/index.html:1011-1026` `loadFlyOpts()` queries `?site=CC&day_of_week=…&direction=…` —
    starts working once the alias lands; no change needed.
- **Conflicts / risks:**
  - Changing the site filter is a behaviour change to a shared endpoint — but every current caller
    passes `site=CC`, and the change only *adds* matches (was returning nothing). Unknown sites
    still return empty (no crash). Low regression risk.
  - Flights live in **bundled SQLite** (`data/fmg_flights.db`, rebuilt from JSON on startup), not
    Postgres — the pg8000/DB-driver landmine does **not** apply here.
  - `/api/flights/sites` returns full names — unaffected (no alias on that path).
- **New dependencies:** none.
- **Data model / migration:** none. SQLite rebuilds from JSON on boot via `build_flights_db.py`.
- **Integration points:** `routers/flights.py` `list_flights`; `static/index.html` swing-detail
  fallback text. Two files.
- **Effort:** small — one backend filter fix + one frontend string fallback.

## 4. Design / approach

Two surgical changes; additive and reversible.

**A. Backend site-code alias + case-insensitive match (`routers/flights.py`).**
```python
SITE_ALIASES = {"CC": "Christmas Creek"}  # extend per hub as they onboard (CB, etc.)
...
if site:
    name = SITE_ALIASES.get(site.strip().upper(), site)
    query += " AND UPPER(site) = UPPER(?)"
    params.append(name)
```
- `CC` → `Christmas Creek` → matches. Passing the full name also works (case-insensitive).
- Unknown code/site falls through to a literal that simply matches nothing (same as today; no
  crash, no regression). `day_of_week`/`direction` filters unchanged.

**B. Graceful unknown-flight display (`static/index.html:884,890`).** Replace the
`'Times unavailable'` fallback with `'No scheduled time'` (the flight number is already shown in
`sd-fb-num` just above). `'No flight set'` (when no number at all) stays. Swings tab unchanged.

No change to `preloadFlights`, the data, or `build_flights_db.py`.

## 5. Acceptance criteria

- [ ] `GET /api/flights/?site=CC&direction=inbound` returns CC inbound flights (13), not 0.
- [ ] `GET /api/flights/?site=CC&direction=outbound` returns CC outbound flights (12).
- [ ] Passing the full name `?site=Christmas Creek` also returns the same flights (case-insensitive).
- [ ] An unknown `?site=ZZ` returns `[]` (no error) — no regression.
- [ ] After login, `flightCache` is populated (CC flights present).
- [ ] Swing detail for a **scheduled** flight number shows real `depart - arrive` times (no "Times unavailable").
- [ ] Swing detail for an **unknown** flight number shows the number + "No scheduled time".
- [ ] Add-Swing picker (`loadFlyOpts`) lists flights for the selected day (not "No flights on this day").
- [ ] No JS console errors; `node --check` passes on the page script.

## 6. Test plan

- **Backend (decisive):** build the SQLite from JSON, run the aliased query for `CC` inbound/
  outbound and assert counts 13/12; assert full-name and case variants match; assert unknown site →
  empty. (Mirrors the repro that found the bug.)
- **Live API:** start the server (SQLite DB locally), login as `britt`, `GET /api/flights/?site=CC&
  direction=inbound` → non-empty; `?site=ZZ` → `[]`.
- **Frontend:** `node --check` the page script; static-trace that `flightCache` keys cover a known
  CC `flight_number`; confirm the swing-detail fallback now reads "No scheduled time" for an unknown
  number and real times for a scheduled one. Manual eyeball post-deploy: open a swing with a
  scheduled flight → times show; open Add Swing → picker lists flights.

## 7. Rollout

Two files (`routers/flights.py`, `static/index.html`). Push to `main` → Railway auto-deploys; the
SQLite rebuilds from JSON on boot. No migration, no flag. Reversible by revert. Smoke after deploy:
`GET /api/flights/?site=CC&direction=inbound` on the live URL returns flights (read-only, safe).

## 8. Open decisions

- [x] Fix location — **backend site-code alias** in `routers/flights.py` (vs frontend code→name
  map, vs data-build mapping). *Resolved 2026-06-11.*
- [x] Unknown free-text flight numbers — **show number + "No scheduled time"** (vs keep "Times
  unavailable"). *Resolved 2026-06-11.*
- No blocking decisions remain.

## 9. Completeness checklist  *(GATE — must be all ✅ before build)*

- [x] Need validated (§1) — root cause reproduced against real data; do-nothing rejected.
- [x] Goals & non-goals defined (§2).
- [x] Repo audit done with real `file:line` citations (§3).
- [x] Design chosen (§4) — small, two surgical changes.
- [x] Acceptance criteria are testable (§5).
- [x] Test plan covers each criterion (§6).
- [x] Rollout / migration understood (§7) — additive, no migration.
- [x] No **blocking** open decisions remain (§8).

> All ✅ → Status **Ready for Build**; registry synced; build prompt below.

## 10. Build prompt — ultracode handoff

```
ultracode: Implement FF-002 Flight data fix per docs/future-features/FF-002-flight-data-fix.md.

Root cause (reproduced): the flights SQLite stores site="Christmas Creek" but the app queries
site=CC, which routers/flights.py uppercases and matches exactly → zero rows, so flightCache is
always empty and the Add-Swing picker always shows "No flights". Two surgical changes only.

Honour this project's CLAUDE.md guardrails:
- Surgical, simplest fix; match existing style (FastAPI router; single-file vanilla JS, var/concat).
- This intentionally DOES touch the backend (the bug is a backend/data contract mismatch) — but
  ONLY routers/flights.py for the site filter. Do not touch database.py, build_flights_db.py, the
  data, or preloadFlights.
- After changes: syntax-check (node --check the page script; python import-check the router).
- Do NOT push to production without Ryan's explicit cutover.

Phases (each independently verifiable):
  1. Backend alias (routers/flights.py): add SITE_ALIASES = {"CC": "Christmas Creek"}; resolve the
     site param through it and match case-insensitively (UPPER(site)=UPPER(?)). Leave day_of_week
     and direction filters as-is.
     → verify: build the SQLite from JSON and assert site=CC returns 13 inbound / 12 outbound;
       full-name + case variants match; unknown site → []. Live: login as britt, GET
       /api/flights/?site=CC&direction=inbound is non-empty, ?site=ZZ is [].
  2. Graceful display (static/index.html:884,890): change the "Times unavailable" fallback to
     "No scheduled time" (number already shown above; keep "No flight set" when no number).
     → verify: node --check passes; swing detail shows real times for a scheduled flight and
       "No scheduled time" for an unknown number; Add-Swing picker lists flights for the day.

Acceptance: all §5 criteria. Test per §6. Keep the FUTURE_FEATURES.md FF-002 Status line in sync in
the same change as code. Smoke the live API after deploy (read-only).
```

## 11. Follow-up — all-hubs + inline (2026-06-11)

Ryan's follow-up after the base fix: "make it live across all sites, inline, no full page refresh."
Frontend-only (`static/index.html`); the backend alias from §4A is unchanged.

- **All hubs.** `preloadFlights()` now fetches `/api/flights/` with **no site filter** (one request,
  all 6 sites, both directions) instead of CC-only. Every swing's flight resolves from cache, whatever
  the site.
- **Day-accurate cache.** Cache is keyed by `flight_number|day_of_week|direction` (was number only).
  The same number flies different times on different days (37 ambiguous numbers across hubs; **6 even
  within CC** — pre-existing latent bug: the modal showed whichever day's row loaded last). New
  `lookupFlight(num, dateStr, dir)` computes the swing date's weekday and returns the exact flight, or
  `null` → "No scheduled time". Used by the swing-detail modal and the Swings tab.
- **Site-aware picker.** `loadFlyOpts()` derives the site from the selected staff member's `site_code`
  (returned by `/api/staff/`, currently all `CC`) instead of hardcoding `CC` — so the Add-Swing picker
  lists the right hub's flights for future non-CC staff.
- **Inline, no page refresh.** The all-hubs cache populates once at login and every render path
  (detail modal, Swings tab, calendar) reads it synchronously; save already re-renders in place. No
  manual browser refresh is needed during a session.
- **Verified** (Node simulation against the real 149-flight DB): day-accurate times for multi-day
  numbers (QF2918 Mon/Wed/Thu/Fri), correct site for cross-site numbers (QF2916 Cloudbreak-Wed vs
  Solomon-Thu), direction separation, and graceful `null` for unknown numbers / non-operating days.
- **Cache key trivia:** `(number, day, direction)` has exactly one same-site collision (QF2911
  Tue outbound, 2 times) — last-wins, negligible.
- **Behaviour change to note:** times are now *correct-or-blank*. A swing whose date's weekday doesn't
  match any flight row for that number now reads "No scheduled time" rather than an arbitrary
  (possibly wrong-day) time.

### 11a. The actual prod blocker — SQLite cross-thread 500 (found via live smoke)

The live smoke after deploy revealed every `/api/flights/*` call (incl. unchanged `/sites`) was
**500ing** in prod — the real reason flight times never showed. The §1/§3 root-cause analysis was done
with a *direct, single-threaded* SQLite query, so it never hit this:

```
File "/app/routers/flights.py", in list_flights
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
```

`get_flights_db()` is a **sync** generator dependency (FastAPI runs it in a threadpool worker, where
the connection is created), but the endpoints are **`async def`** (run in the event-loop thread, where
`conn.execute` is called) → connection created in one thread, used in another → SQLite refuses. The
frontend's `api()` swallowed the 500, so `flightCache` stayed empty and everything read
"Times unavailable" — the same symptom the site-filter bug would produce, masking it.

**Fix:** open the per-request connection with `check_same_thread=False` (`routers/flights.py`). Each
request gets its own short-lived connection, never used concurrently, so it's safe.

**Verified:** local FastAPI harness (async endpoint + sync `get_db`, real flights DB) — default connect
→ HTTP 500 (reproduces prod), `check_same_thread=False` → HTTP 200. **Live prod smoke after deploy:**
`?site=CC&direction=inbound` → 13, `outbound` → 12, `?site=ZZ` → [], `/api/flights/` → 149 (all 6 hubs),
`/sites` → all six sites. Endpoint healthy.

> **Lesson:** smoke the running server, not just a direct DB query — the threading defect only appears
> under the ASGI threadpool, never in a single-threaded repro.

### 11b. Remaining

API + data path are live-verified. The only open item is a **visual eyeball** in the browser (Britt /
Ryan): open a swing → real `depart - arrive` times; open Add Swing → picker lists flights for the day.
