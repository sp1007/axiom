---
id: T140
title: AX0-FIX-02 unsigned 64-bit div/rem, u64/usize mul overflow, isize/usize shift width (axiom0 + port, Python integer table)
phase: P10-selfhost
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T134]
priority: 0
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/opt, bootstrap/axiom0/src/interp, compiler/lir, compiler/target/x64, compiler/mir/builder.ax, compiler/opt, compiler/interp, std/text/fmt/int.ax, tests/run/numeric, tests/lir, tests/mc, tests/mir, tests/selfhost, tests/encode]
spec: [spec/SPEC-03-core-semantics.md, spec/decisions/ADR-0034-oracle-independence.md, tasks/0327, tasks/0334]
covers: [REQ-CORE-028, REQ-TYP-035, REQ-EXP-219]
timeout_min: 300
---
# T140 — AX0-FIX-02: unsigned 64-bit div/rem, u64/usize multiply overflow, isize/usize shift width

## Goal
Integer arithmetic gives the SPEC-03 result for every operator, every integer type and every edge
operand, identically in the MIR interpreter, native -O0 and native -O1, in axiom0 **and** in the
ported compiler under `compiler/` (ADR-0034 §2, lockstep rule). The expected results come from an
independent Python table, not from either compiler (ADR-0034 §1).

Confirmed defects (audit `_workspaces/audit/2026-10-19/oracle-independence.md` OI-01, OI-02, OI-05):
1. Native `/` and `%` on `u64`/`usize` use `sar rdx,63` + `idiv` for every type
   (`bootstrap/axiom0/src/target/x64/isel/isel.c` ~338-351; LIR `div`/`rem` carry no signedness;
   ported as-is in `compiler/target/x64/frame.ax` ~572 and `compiler/target/x64/isel.ax`). Wrong when
   the dividend is ≥ 2^63 (`0x8000000000000000 / 2^56`: interp 128, native 127). A natively built
   axiomc panics when printing the maximum u64 `0xFFFF_FFFF_FFFF_FFFFu64` (`compiler/lir/lir.ax:502`, `compiler/mir/mir.ax:1071`).
2. Native `u64`/`usize` `*` overflow is not trapped (`isel.c` ~210-262, 64-bit `UMUL_OVERFLOW`):
   `2^32 * 2^32` interp exit 101, native continues.
3. `isize`/`usize` shifts by 32..63 panic `shift amount out of range` in both executors
   (`bootstrap/axiom0/src/mir/build/builder.c` ~1650: `bits` defaults to 32, ISIZE/USIZE missing).

## Scope
- **Python integer-semantics generator** `tests/run/numeric/gen_int_semantics.py` (Python 3 stdlib
  only). It computes expected results from SPEC-03 rules alone (AXS-SEM-030 checked `+ - *` unary
  `-`, AXS-SEM-031 wrapping/bit intrinsics, AXS-SEM-032 `/ %` truncation and traps, AXS-SEM-033
  bitwise, AXS-SEM-034 shifts incl. out-of-range amounts, AXS-SEM-035 comparisons) for all ten
  integer types i8..i64, u8..u64, isize, usize (64-bit target) and edge operands
  {0, 1, 2, MAX, MIN, MAX-1, MIN+1, 2^(w-1), 2^(w-1)±1, -1 for signed}; shift amounts
  {0, 1, 31, 32, 33, w-1, w, w+1, negative for signed amount types}. Non-trapping results are
  printed and pinned with `stdout:`; each trapping case is pinned to exit 101 plus the SPEC-03 panic
  line. Grouping (one file per type × op family, one file per trap case, or a selector argument) is
  the engineer's choice (TYPE A); the generated tests run in `modes: interp native` and at -O1 when
  the runner offers it. A `check` mode plus `tests/run/numeric/int_semantics_current.test`
  regenerates into `{tmp}` and byte-compares, so the committed table cannot drift.
- **axiom0 fixes:** signedness reaches LIR for `div`/`rem` (new `udiv`/`urem` ops or a signedness
  flag — TYPE A; printer, parser, verifier, optimizer constant folding and isel all handled); x64
  unsigned path `xor edx,edx` + `div`; 64-bit unsigned multiply overflow detected (`mul` + CF/OF, or
  equivalent) and routed to the overflow panic; MIR builder shift-width table covers ISIZE/USIZE
  (64 on x64; taken from the target layout, not a literal).
- **Port fixes in lockstep** (ADR-0034 §2): the same three fixes in `compiler/lir`,
  `compiler/target/x64` (`isel.ax`, `frame.ax`), `compiler/mir/builder.ax`, `compiler/opt`
  (constant folding) and `compiler/interp` if it shares the defect. Selfhost bundles/goldens under
  `tests/selfhost` that change because axiom0's output changed are regenerated with their generators
  and each change is explained in the report.
- **Remove the std workaround** `u64_div_u32` in `std/text/fmt/int.ax` (~404) once native `u64 /` is
  correct; std formatting tests must still pass in both modes.
- MIR/LIR/MC goldens touched (`tests/lir/div*.lir`, `tests/mc`, `tests/mir`) are updated and
  reviewed, not blindly re-blessed.

## Acceptance
- [ ] `python tests/run/numeric/gen_int_semantics.py check` exits 0 and
      `tests/run/numeric/int_semantics_current.test` passes; the generated table covers every
      operator family above × all ten types × the edge list (the report states the case count).
- [ ] Every generated test passes with `--compiler build/axiom0.exe` inside `build-snap-T140` in
      interp and native (and -O1 if available); before the fix the report shows the failing cases
      (at least the three defects above reproduce).
- [ ] Repro tests (hand-written, values from the audit): `u64` `0x8000000000000000 / (1u64 << 56)`
      prints 128; `0xFFFF_FFFF_FFFF_FFFFu64 % 10u64` prints 5; `0xFFFF_FFFF_FFFF_FFFFusize / (1usize << 56)` prints 255;
      `(1u64 << 32) * (1u64 << 32)` exits 101; `0xFFFF_FFFF_FFFF_FFFFusize * 2usize` exits 101; `x >> 40` and
      `x << 40` on `usize`/`isize` give the shifted value; `usize` shift by 64 exits 101 — all in both
      modes.
- [ ] Port: a selfhost test built from the real `compiler/target/x64` / `compiler/lir` sources
      (regenerated bundle or direct module build) shows the port selects unsigned division for
      `u64`/`usize` and traps `u64` multiply overflow; a test from `compiler/mir/builder.ax` shows a
      `usize` shift by 40 does not panic. Printing the maximum u64 `0xFFFF_FFFF_FFFF_FFFFu64` through the ported
      `compiler/lir/lir.ax` / `compiler/mir/mir.ax` formatting path, built natively, prints
      `18446744073709551615`.
- [ ] `std/text/fmt/int.ax` no longer contains the `u64_div_u32` workaround; `tests/std` formatting
      tests pass in both modes.
- [ ] Full suite passes in `build-snap-T140` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T140-report.md` with exact `## Files changed`, the list of
      regenerated goldens/bundles with the reason for each change.

## Out of scope
- i128/u128, saturating/`checked_*` families (E12.1), floats (E12.2).
- Casts (`as`) beyond what the table needs to build operands; Drop (T141); encoder table (T143).

## Notes
- ADR-0034 §2: until the T087 freeze an axiom0 semantic fix and its port twin land in the same task,
  because the selfhost bundles compare the port with axiom0's output; fixing one side alone would
  leave the suite red between two tasks.
- Runs after T134 (shared `lir`, `target/x64`, `mir/build`, `tests/selfhost`); priority 0 runs alone.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale (2026-10-14) and is not
  evidence.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
