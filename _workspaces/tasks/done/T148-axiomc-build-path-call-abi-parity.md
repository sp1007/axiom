---
id: T148
title: axiomc build path equals axiom0 build.c - call ABI of destructor calls, inspect reflects build
phase: P10-selfhost
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T147]
priority: 116
status: done
attempts: 1
paths: [bootstrap/axiom0/src/driver, compiler/driver/pipeline.ax, compiler/backend, compiler/lir, compiler/abi, tests/run/parity/build_abi, tests/selfhost]
spec: [spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md, spec/decisions/ADR-0032-unblock-t131-drop-destructors.md]
covers: [REQ-BLD-030, REQ-CORE-3181]
started: 2026-10-26 09:13:55
finished: 2026-10-26 17:39:17
---
# T148 — axiomc `build` path parity: call ABI, `inspect` == `build`

## Goal
`axiomc build` lowers every function exactly like `axiom0 build` (`driver/build_native/build.c`, the
reference path of ADR-0035 §5), so the code of every `tests/run/drop/*` program is byte-identical;
and axiom0's own `inspect --emit=lir|mi|mc|obj` shows what `build` produces.

Confirmed defect (architect probe 2026-10-20): `tests/run/drop/003.ax` — `axiom0 build` loads the
destructor's `self` into RCX before `call Droppable1_drop`, `axiomc build` loads it into RAX (the
Win64 first-argument register is RCX). `inspect --emit=mir|lir|mi` of both compilers are identical,
so the difference is introduced only in the port's `build` path (function
`driver_emit_build_mi_body_obj` of `compiler/driver/pipeline.ax` and its callers): axiom0's `build.c` passes the function type to
`ax_lir_lower` (~line 483) while the `inspect` emitters (`emit_lir.c`, `emit_mi.c`, `emit_mc.c`,
`emit_obj.c`) pass `NULL` for most bodies. 24 registry entries (all `.text`-differing
`tests/run/drop/*`) show this pattern; destructors that read a field of `self` would crash or
misbehave.

## Scope
- Find every difference between the port's `build` lowering and `build.c` (function type for LIR
  lowering, ABI lowering of calls inserted by drop elaboration, drop-glue calls, any other per-body
  step) and make the port follow `build.c`.
- axiom0 lockstep (ADR-0035 §5, ADR-0034 §2): make the `inspect` emitters use the same lowering
  inputs as `build` (shared helper or the same function type), so `inspect --emit=mi` shows RCX for
  the destructor call; mirror the same change in the port's `inspect` path. Goldens that change are
  reviewed and explained, not blindly re-blessed.

## Acceptance
- [ ] `tests/run/parity/build_abi/drop_reads_self.ax` (`modes: interp native`): destructors that read
      and print scalar fields of `self` (one field, two fields of different widths, a destructor called
      for a parameter, a temporary and a block-scope value); `// stdout:` derived by hand. Passes with
      axiom0 in both modes and is identical under the e2e oracle (not in the registry).
- [ ] `axiom0 inspect --emit=mi tests/run/drop/003.ax` shows the destructor argument in RCX, and
      equals `axiomc inspect --emit=mi` of the same file.
- [ ] `known_divergent.txt` shrinks by every entry that becomes identical — after T147 and this task
      no `tests/run/drop/*` entry remains (24 entries in the plan table); no entry is added.
- [ ] Full suite passes in `build-snap-T148` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T148-report.md` with exact `## Files changed` and the list of
      removed registry paths.

## Out of scope
- String-symbol naming (T147); Drop semantics changes (T141 owns them).

## Notes
- ADR-0035 §4: remove registry lines explicitly; XPASS/IMPROVED lines from the oracle tell which.
- axiomc for probes: `python tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py <axiom0> <tmp> <root>`
  leaves `<tmp>/axiomc.exe`.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-26 09:13:55 started (attempt 1) T148-impl
- 2026-10-26 17:39:17 accepted by QA -> done
