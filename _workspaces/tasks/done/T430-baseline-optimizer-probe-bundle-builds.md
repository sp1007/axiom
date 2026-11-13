---
id: T430
title: Baseline fix — optimizer engine/oracle probe bundles build clean against compiler/ at HEAD
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 13
status: done
attempts: 1
timeout_min: 600
paths: [tests/run/opt_alias, tests/run/opt_bce, tests/run/opt_escape, tests/run/opt_ipa_devirt, tests/run/opt_loop_vec, tests/run/opt_loops, tests/run/opt_lto, tests/run/opt_pgo_gc, tests/run/opt_slp_vec, tests/opt2, tests/conformance/p15]
locks: [_workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-70-optir-ssa-memoryssa.md, spec/SPEC-71-alias-escape-promotion.md, spec/SPEC-72-loops-scev-bce.md, spec/SPEC-73-inlining-specialization-devirt.md, spec/SPEC-74-auto-vectorization.md, spec/SPEC-75-lto-wpo-section-gc-pgo.md]
covers: [REQ-OPT-176, REQ-OPT-037, REQ-OPT-307, REQ-OPT-108, REQ-OPT-219, REQ-OPT-246]
started: 2026-11-13 11:41:33
finished: 2026-11-13 16:19:56
---
# T430 — Baseline fix: optimizer probe bundles build clean

## Goal
The 15 optimizer engine/oracle tests listed for T430 in `_workspaces/baseline-failures.txt` pass again under
`axiomc2`, so the P15 optimizer conformance evidence is live again.

## Scope
- Observed at HEAD (T421-qa §C): the oracle scripts assemble probe bundles from `*_probe.ax.in` templates plus
  `compiler/` modules at HEAD and build them; the builds now report `warning[AX_NAME_SHADOW_MODULE]` and an
  `AX_NAME_UNRE…` error where the oracle expects a clean build. For each test find the exact message (run it with `-v`),
  identify the drift (a renamed/moved `compiler/` symbol, a new module name shadowed by a probe local, a new import
  needed) and fix the probe template or oracle script so it builds clean (ADR-0041 §2 D3). Prefer one shared fix if the
  15 share a cause (e.g. a helper in `tests/selfhost/bundle_common.py` is NOT editable here: report it instead).
- Do not weaken checks: an oracle that tolerated warnings before must not start ignoring errors; keep every expected
  output string.
- If the root cause is inside `compiler/` or `std/` (a real compiler regression), do not fix it here: report the
  ids and the cause in "Follow-ups" for an architect split; remove only the ids you fixed.
- Remove the fixed T430 lines from `_workspaces/baseline-failures.txt`.

## Acceptance
- [ ] Every T430 id passes under `axiomc2.exe` built in `build-snap-T430`: the 9 `run/opt_*/opt_*_engine.test`,
  `opt2/opt2_sroa_inline_engine.test`, and the 5 `conformance/p15/*` oracle/conformance tests (or, for ids whose cause
  is in `compiler/`/`std/`, a report entry with the evidence and the line kept in the baseline).
- [ ] Mutation proof: one expected string changed in one oracle makes that test FAIL.
- [ ] Complete suite: failing ids are a subset of the baseline after this task's removals; WEAK-NATIVE 0;
  `archcheck.py` clean.
- [ ] The fixed lines are removed from `_workspaces/baseline-failures.txt` in this task's change set.
- [ ] Report `_workspaces/reports/T430-report.md` with exact `## Files changed`.

## Out of scope
- `compiler/`, `std/`, `tests/selfhost`, `tests/opt/int128`, `tests/run/int128_interp` (running task T452). `docs/`.

## Notes
- Runs alongside T452: this task edits test harness files only.
- Build/test in `build-snap-T430` (`tools/build_axiomc.py --out build-snap-T430/build`; `tools/axtest.py -j 2`).

## Log
- 2026-11-13 07:40:00 created by axiom-architect (ADR-0041, complete-suite baseline)
- 2026-11-13 11:41:33 started (attempt 1) T430-impl
- 2026-11-13 16:19:56 accepted by QA -> done
