# Future Features — backlog (Rostering Tool)

Ideas and partially-scaffolded features that are not yet built — forward-looking, not bugs.
Existing direction also lives in `../roster-tool-ROADMAP.md`; this file is the live registry.

> **Keep this live.** One `FF-NNN` line per idea (Tier-1 stub). When an idea is fleshed out,
> promote it to a full spec at `future-features/FF-NNN-slug.md` and keep the **Status** line
> here in sync. **Nothing is built until its Status is `Ready for Build`.**
> Launch with `/ff <name>`. Standard: `~/.claude/DOCUMENTATION_STANDARDS.md`.

---

## FF-001 — Leave Recording (`leave-recording`)
**Status:** In Build  ·  **Added:** 2026-06-11  ·  **Updated:** 2026-06-11
Roadmap Phase 1. Let the Coordinator click any calendar cell to set/remove AL or LWOP over a date range, persisted as RosterOverrides. Closes the biggest current gap: Britt has no in-app way to record leave. Frontend-only; backend endpoints already exist. Spec: `future-features/FF-001-leave-recording.md`.

---

## How to use this list

Add an item with a unique `FF-NNN` ID, short title + slug, Status, dates, and one line on what
it is. Flesh it out into `future-features/FF-NNN-slug.md` before building.
Status lifecycle: `Draft → Validated → Speccing → Ready for Build → In Build → Shipped`.
