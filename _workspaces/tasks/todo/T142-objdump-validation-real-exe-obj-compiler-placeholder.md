---
id: T142
title: External COFF/PE oracle - objdump validation of real exe/obj; manifests use {compiler}
phase: P10-selfhost
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: []
priority: 110
status: todo
attempts: 0
paths: [tests/link, tests/obj, tests/driver, tests/verify]
spec: [spec/decisions/ADR-0034-oracle-independence.md, spec/decisions/ADR-0003-backend-pipeline-robustness.md, 0185, tasks/0361]
covers: [REQ-TST-109, REQ-CORE-345, REQ-CORE-346]
---
# T142 — External COFF/PE oracle: objdump validation of real exe/obj

## Goal
The COFF objects and PE executables that the compiler under test writes for real programs are
checked by a tool outside the project (GNU `objdump`) in every per-task gate and at T086 with
axiomc, and every exec manifest tests the compiler under test, not a hard-wired axiom0
(ADR-0034 §1, §4).

Audit OI-07: T026's objdump criterion and T028's "cross-link every native run test" have no test;
`tests/obj/dummy.test` is `python -c "exit(0)"`; the gcc cross-link of hand-built objects
(`tests/obj/cdriver_coff.c`) runs only in ctest and prints SKIP without gcc;
`tests/driver/build_emit_obj.test` links only `fn main() {}`. Extra finding (architect, 2026-10-20):
37 exec manifests (36 in `tests/driver`, `tests/verify`; `tests/hir/more.test` is T139's) call `{build}/axiom0` instead of
`{compiler}`, so with `--compiler axiomc` at T086 they would test axiom0 or fail.

## Scope
- `tests/link/objdump_validate.py` + `tests/link/objdump_validate.test` (Python 3 stdlib, no
  `requires: axiom0-internal`): builds a fixed list of ≥ 20 existing native run tests (numeric, drop,
  str/UTF-8, ffi, std fs/io/process, a multi-function program with `.rdata` tables) with
  `{compiler} build` and `{compiler} build --emit=obj`, runs `objdump -x -d` (and `-p` for the exe) and
  checks: objdump exit 0 and no "file format not recognized"; zero `(bad)` lines; entry point inside
  `.text`; section characteristics (`.text` CODE|EXECUTE|READ not WRITE, `.rdata` READ only, `.data`
  READ|WRITE not EXECUTE); every kernel32 function the program imports (expected list written by the
  script from the program's known host calls, not read from compiler output) appears in the import
  table; relocation targets in the `.obj` are defined or listed as externals; the exe runs and its
  exit code equals the test's pinned value. objdump missing → FAIL (ADR-0034 §7), never SKIP.
- Replace `tests/obj/dummy.test` with a manifest that runs the C driver
  `{build}/tests/ct_obj_cdriver_coff` (`requires: axiom0-internal`, expects `PASS`), and make the
  driver FAIL instead of printing SKIP when gcc is missing.
- Every exec manifest under `tests/driver` and `tests/verify` that names `{build}/axiom0` as the
  compiler uses `{compiler}`; helper scripts take the compiler path as an argument (already the case
  for `cross_link_oracle.py`, `build_stack_reserve.py`). Manifests that genuinely test an axiom0-only
  binary keep it and gain `requires: axiom0-internal`.
- `tests/driver/build_emit_obj.test` additionally gcc-links one non-trivial self-contained program
  (no std, no host calls, arithmetic + calls + `.rdata` table) if that links with the existing
  `ax_main` entry; if it cannot link because of the runtime naming, record that in the report (real
  program cross-linking is deferred to E18.7, ADR-0034 §4).

## Acceptance
- [ ] `python tools/axtest.py --compiler build/axiom0.exe link/objdump_validate obj/ driver/ verify/`
      passes inside `build-snap-T142`; the report shows one negative check (a deliberately corrupted
      copy of an .exe/.obj makes the script FAIL).
- [ ] `grep -rlE "\{build\}/axiom0([ .]|$)" tests --include=*.test` lists only manifests carrying
      `requires: axiom0-internal` (report lists the count before/after).
- [ ] `tests/obj/dummy.test` is gone; the cdriver_coff manifest passes; without gcc on PATH it fails.
- [ ] Full suite passes in `build-snap-T142`.
- [ ] Report `_workspaces/reports/T142-report.md` with exact `## Files changed`; any defect objdump
      reveals is listed under `## Follow-ups` (the architect files AX0-FIX tasks), not patched here.

## Out of scope
- Changing the object model so gcc/ld can link real programs (`__imp_` + runtime object) — deferred
  to E18.7 (T750/T751), ADR-0034 §4.
- Compiler code under `bootstrap/` or `compiler/`.

## Notes
- Independent of the running T085 (no shared paths); can run now. T086 depends on it.
- Use the snapshot build (`build-snap-T142/build/axiom0.exe`); `build/axiom0.exe` in the main tree is
  stale.

## Log
