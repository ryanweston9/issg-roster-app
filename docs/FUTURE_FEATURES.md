# Future Features — backlog (Rostering Tool)

Ideas and partially-scaffolded features that are not yet built — forward-looking, not bugs.
Existing direction also lives in `../roster-tool-ROADMAP.md`; this file is the live registry.

> **Keep this live.** One `FF-NNN` line per idea (Tier-1 stub). When an idea is fleshed out,
> promote it to a full spec at `future-features/FF-NNN-slug.md` and keep the **Status** line
> here in sync. **Nothing is built until its Status is `Ready for Build`.**
> Launch with `/ff <name>`. Standard: `~/.claude/DOCUMENTATION_STANDARDS.md`.

---

## FF-001 — Leave Recording (`leave-recording`)
**Status:** Shipped  ·  **Added:** 2026-06-11  ·  **Updated:** 2026-06-11
Roadmap Phase 1. Let the Coordinator click any calendar cell to set/remove AL or LWOP over a date range, persisted as RosterOverrides. Closes the biggest current gap: Britt has no in-app way to record leave. Frontend-only; backend endpoints already exist. Shipped to prod (commit 8bf3d28). Spec: `future-features/FF-001-leave-recording.md`.

## FF-002 — Flight data fix (`flight-data-fix`)
**Status:** Shipped  ·  **Added:** 2026-06-11  ·  **Updated:** 2026-06-11
Roadmap Phase 2. Swing detail shows "Times unavailable" and the Add-Swing flight picker shows "No flights". Root cause: app queries `site=CC` but the flights DB stores `site="Christmas Creek"` → zero matches, so the flight cache is always empty. Fix = backend site-code alias in `routers/flights.py` + graceful "No scheduled time" for unknown numbers. Follow-up (§11): cache all hubs, key by number+day+direction for day-accurate times, site-aware Add-Swing picker — live inline, no page refresh. Live smoke (§11a) found the real prod blocker — a SQLite cross-thread 500 on every flights call — fixed with `check_same_thread=False`. Live-verified in prod. Spec: `future-features/FF-002-flight-data-fix.md`.

---

## How to use this list

Add an item with a unique `FF-NNN` ID, short title + slug, Status, dates, and one line on what
it is. Flesh it out into `future-features/FF-NNN-slug.md` before building.
Status lifecycle: `Draft → Validated → Speccing → Ready for Build → In Build → Shipped`.
