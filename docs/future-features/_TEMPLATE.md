# FF-NNN — <Feature title> (`<short-slug>`)

> Standalone Future-Feature spec. Created/maintained by `/ff`. One feature per file.
> Keep the matching one-line entry in this project's `FUTURE_FEATURES.md` registry in sync
> (same change, every change). **This feature is not built until Status reaches `Ready for Build`.**

**Status:** Draft <!-- Draft → Validated → Speccing → Ready for Build → In Build → Shipped -->
**Added:** YYYY-MM-DD
**Updated:** YYYY-MM-DD
**Owner:** Ryan Weston
**Related:** <links to specs / build plans / prior FFs / tickets, or "none">

---

## 1. Problem / Need  *(GATE — Need validation)*

- **Problem.** <The pain, in 1–3 sentences. Concrete, not aspirational.>
- **Who's affected.** <Which users/roles, how often.>
- **Cost of inaction.** <What happens if we never build this? Who keeps hurting?>
- **Alternatives considered** (incl. *do nothing*):
  - <Alternative A — why rejected.>
  - <Do nothing — why that's not acceptable, or why it might be.>
- **Success metric.** <How we'll know it worked. Observable, ideally measurable.>

> Do not proceed past this section until the feature is genuinely justified.
> If it isn't, set Status and registry note to `Parked` and stop.

## 2. Goals & non-goals

- **Goals:** <bulleted, testable outcomes.>
- **Non-goals:** <explicitly out of scope — prevents creep.>

## 3. Codebase stress-test — Repo audit (YYYY-MM-DD)  *(GATE)*

> Findings from actually reading this repo. Cite real `path:line`. This is what makes the
> spec trustworthy — claims are verified against the code, not assumed.

- **Related / existing code:** <what already exists that this touches or can reuse, with `file:line`.>
- **What must change:** <files/modules to add or edit, and why.>
- **Conflicts / risks:** <anything this could break; live surfaces to avoid; concurrency/timezone/etc. landmines for this project.>
- **New dependencies:** <libs/services, or "none".>
- **Data model / migration:** <schema changes + whether a live-DB migration is needed, or "none".>
- **Integration points:** <APIs, blueprints, jobs, env vars touched.>
- **Effort:** <small | medium | large> — <one line; note if phaseable/independently shippable.>

## 4. Design / approach

<The chosen approach. Phase it if large — each phase independently shippable + verifiable.
Note the safety profile (additive? reversible? touches live surfaces?).>

## 5. Acceptance criteria

- [ ] <Testable criterion 1.>
- [ ] <Testable criterion 2.>

## 6. Test plan

<How each criterion is verified — unit/integration tests, manual steps, staging checks.
Follow this project's "test as you go" / dev→staging→prod discipline where it applies.>

## 7. Rollout

<Flags, migration order, dev→staging→prod path, cutover, rollback. Or "additive, no special rollout".>

## 8. Open decisions

- [ ] <Unresolved question needing Ryan / a stakeholder — flag blockers explicitly.>

## 9. Completeness checklist  *(GATE — must be all ✅ before build)*

- [ ] Need validated (§1) — problem real, alternatives weighed, do-nothing rejected.
- [ ] Goals & non-goals defined (§2).
- [ ] Repo audit done with real `file:line` citations (§3).
- [ ] Design chosen and phased if large (§4).
- [ ] Acceptance criteria are testable (§5).
- [ ] Test plan covers each criterion (§6).
- [ ] Rollout / migration understood (§7).
- [ ] No **blocking** open decisions remain (§8).

> When every box is ✅: set **Status → Ready for Build**, bump **Updated**, sync the registry
> line, then fill §10. Until then, building does not start.

## 10. Build prompt — ultracode handoff  *(filled only when Ready for Build)*

> The deliverable. Paste this into a fresh turn to launch the multi-agent build Workflow.
> It must reference this file, embed this project's `CLAUDE.md` guardrails, and list phases
> with verify gates.

```
ultracode: Implement FF-NNN <title> per docs/future-features/FF-NNN-<slug>.md.
Honour this project's CLAUDE.md guardrails: <key guardrails, copied explicitly>.
Phases (each independently shippable + verified):
  1. <phase> → verify: <check>
  2. <phase> → verify: <check>
Acceptance: <the §5 criteria>. Spec/register only updates the FUTURE_FEATURES.md Status line
in the same change as code. Do not push to production without Ryan's explicit cutover.
```
