---
id: T444c
title: Tooling — build_axiomc/bootstrap reuse stage binaries by content hash of their inputs, not mtime; rebuild axiom0 when its sources change
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: []
priority: 11
status: done
attempts: 1
paths: [tools/build_axiomc.py, tools/bootstrap.py, tools/tests/build_axiomc]
spec: [spec/decisions/ADR-0043-cyclic-type-graphs-and-symbol-id-space.md, spec/SPEC-20-selfhost.md]
covers: [REQ-BLD-028, REQ-TST-072]
started: 2026-11-19 06:56:12
finished: 2026-11-19 08:04:57
---
# T444c — build_axiomc reuse by content hash

## Goal
A gate never tests a stale compiler. `tools/bootstrap.py --reuse-existing` (used by `tools/build_axiomc.py` unless
`--force`) reuses `axiomc2`/`axiomc3` when the binary's mtime is newer than every `compiler/**/*.ax` /
`std/**/*.ax`; `taskctl snapshot` copies sources with their main-tree mtimes, so after an edit in a snapshot the old
`axiomc2.exe` was reused (T444 report F3: wall 0.00 s, old sha256). `ensure_stage0` reuses any existing `axiom0.exe`
even after `bootstrap/axiom0` changed (relevant for AX0-FIX tasks such as T164).

## Scope
- Replace the mtime test by a manifest written next to each produced binary (`<bin>.inputs.json`): sha256 over the
  sorted list of (relative path, sha256) of every input — `compiler/**/*.ax`, `std/**/*.ax`, the bundle text actually
  compiled, the producing compiler's sha256, the stage flags (opt level, stack reserve, std root). Reuse only on an
  exact manifest match; print `REUSED <bin> (inputs <hash16>)` or `REBUILT <bin> (reason)`.
- `ensure_stage0`: same rule for `axiom0.exe` over `bootstrap/axiom0/**` (C sources, headers, CMake files) plus cc and
  build type; on mismatch re-run the CMake build in the out dir.
- Hashing cost must stay small (report the time on the full tree; target under 2 s).
- Self-tests `tools/tests/build_axiomc/` (in the style of `tools/tests/taskgate`): edit a source with an older mtime
  than the binary → rebuild; no change → reuse; flag change → rebuild; axiom0 source change → stage 0 rebuilt. Use a
  fake stage driver so the test runs in seconds.

## Acceptance
- [ ] Self-tests pass; a real `python tools/build_axiomc.py --out <dir>` twice prints REUSED the second time and
      REBUILT after the content of one `.ax` file changes while its mtime is set back to an older value.
- [ ] `--force` behaviour unchanged; output binaries byte-identical to a forced build.
- [ ] Report `_workspaces/reports/T444c-report.md` with exact `## Files changed`.

## Out of scope
- `taskctl.py` snapshot logic, `tools/axtest.py` result cache (already content-keyed), `bootstrap/axiom0`.

## Log
- 2026-11-17 created by axiom-architect (T444 report F3; ADR-0043 §4)
- 2026-11-19 03:36:57 started (attempt 1) T444c-impl
- 2026-11-19 04:29:25 requeue: restart (not charged: attempt refunded)
- 2026-11-19 06:56:12 started (attempt 1) T444c-impl
- 2026-11-19 08:04:57 accepted by QA -> done
