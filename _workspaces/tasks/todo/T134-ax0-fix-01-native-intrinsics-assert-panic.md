---
id: T134
title: AX0-FIX-01 native lowering of wrapping/bit intrinsics, assert and panic
phase: P10-selfhost
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: []
priority: 0
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/mir/mir.h, bootstrap/axiom0/src/mir/print.c, bootstrap/axiom0/src/mir/parse.c, bootstrap/axiom0/src/interp, bootstrap/axiom0/src/verify, bootstrap/axiom0/src/opt, bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, bootstrap/axiom0/src/driver/pipeline.c, tests/run/numeric, tests/run/intrinsics, tests/ui/intrinsics, tests/mir, tests/lir, tests/mc, tests/selfhost, tests/std/core/qa_hash_vectors.ax]
locks: [bootstrap/axiom0/src/types/typeck.c, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [spec/decisions/ADR-0004-self-host-subset-additions.md, spec/SPEC-03-core-semantics.md, tasks/0327, tasks/0334]
covers: [REQ-EXP-022, REQ-DRP-022]
timeout_min: 300
---
# T134 — AX0-FIX-01: native lowering of wrapping/bit intrinsics, assert and panic

## Goal
Every `@intrinsic` function that axiom0 accepts has exact, identical semantics in the MIR
interpreter and in native code, and an `@intrinsic` that no backend implements is a compile error.
Today the wrapping/bit intrinsics, `assert` and `panic` are implemented only by name in
`interp/interp.c` (~lines 511-620); the native backend compiles their placeholder bodies
(`{ 0 }`, `{}`), so native `assert` is vacuous, `panic` falls through a `-> !` function, and the
native kernel hash (`compiler/kernel/hash.ax`, `std/core/hash.ax`) degenerates to a constant. This
breaks the natively built axiomc of T085/T086/T087 (HashMap/interner, mangling, hash-dependent output).
T034 / ADR-0004 §1 required MIR operations with exact semantics in both backends; this task delivers
the native half that never landed.

Verified defect (orchestrator, 2026-10-19, `build/axiom0.exe`):
`let x = wrapping_add_u64(3,4); let y = rotate_left_u32(1,3); let z = count_ones_u32(7); x*100+y*10+z`
gives interp 783, native 0; `assert(false); 42` gives interp exit 101, native exit 0; `panic();`
native exits 0.

## Scope
- **One intrinsic table** (e.g. `bootstrap/axiom0/src/mir/build/intrinsics.def` or a table in
  `mir.h`) listing every recognised intrinsic name, its signature class and its lowering class
  (builtin-retyped in typeck, host call `__ax_host_*`, MIR operation, MIR terminator). All
  special-casing (typeck retyping, `build_mir_for_item` host skip, lir/lower `__ax_host_` rename,
  interp dispatch) consults this table instead of ad-hoc name matching where it touches these paths.
- **MIR builder lowering** (spec'd route, ADR-0004 §1, SPEC-03): a call to
  `wrapping_add/sub/mul/neg_<w>`, `rotate_left/right_<w>`, `leading_zeros_<w>`,
  `trailing_zeros_<w>`, `count_ones_<w>` (every integer width i8..i64, u8..u64, isize, usize) becomes
  MIR operation(s) without an overflow assert, with results truncated/sign-extended to the width;
  `assert(c)` becomes an `AX_MIR_TERM_ASSERT` terminator on the panic path; `panic(...)` becomes
  the same abort path as checked-arithmetic failures (exit code 101, SPEC-03), never a call to the
  placeholder body. Whether bit ops are new MIR/LIR ops (x64: `rol`/`ror`, `bsr`/`bsf` with the
  zero case, `popcnt` or a SWAR sequence — no CPU feature beyond baseline x86-64 unless guarded) or
  expansions into existing MIR ops is the engineer's choice (TYPE A); record it in the report. New
  ops must be handled by the MIR verifier, printer/parser, interpreter, optimizer (constant folding
  must use the same semantics) and LIR/x64 isel/encoder.
- The interpreter executes the lowered MIR (the by-name shortcut in `interp.c` for these names is
  removed or reduced to the same table), so both executors run the same MIR.
- **Guard:** a function marked `@intrinsic` whose name is not in the table, or whose signature does
  not match the table entry, is a compile error `AX_TYPE_UNKNOWN_INTRINSIC` (new code in TYPE.def)
  at the declaration span. No placeholder intrinsic body is ever compiled or executed again.
- **Vacuous-test sweep:** run the full suite with the native leg (`modes: interp native` tests and
  every `tests/run` / `tests/selfhost` run test that can build natively). Every test that now fails
  natively is either fixed (wrong expectation in the test) or, when the failure is a real bug in
  ported Axiom code under `compiler/` or `std/`, listed in the report's `## Follow-ups` with the
  failing test and diagnosis and its native leg marked `// native-after: T086` (the architect files
  the fix task, retargets the marker to it, and makes T086 depend on it). Do not edit `compiler/`
  or `std/` in this task.
- Known defects that are **not** this task's: unsigned 64-bit div/rem, u64/usize multiply overflow
  and isize/usize shift width (T140, AX0-FIX-02); implicit Drop of scalar-field structs (T141,
  AX0-FIX-03). Tests that hit them are not "fixed" here.

## Acceptance
- [ ] `tests/run/intrinsics/native_repro.ax` (`modes: interp native`) runs the repro above and
      exits/prints 783 in both modes.
- [ ] `tests/run/numeric/intrinsic_ops.ax` runs in `modes: interp native` with identical results for
      every width at MIN/MAX/edge values; no `native-after` marker remains on it.
- [ ] `tests/run/intrinsics/assert_false.ax` and `panic_abort.ax`: native and interp both exit 101
      (SPEC-03); a statement after `panic()` is never executed natively (observable output check).
- [ ] `tests/ui/intrinsics/unknown_intrinsic.ax`: `@intrinsic fn frobnicate(a: u32) -> u32 { 0 }`
      gets `AX_TYPE_UNKNOWN_INTRINSIC` at the right span; a known name with a wrong signature also
      errors.
- [ ] Hash against the independent Python reference (ADR-0034 §1, audit OI-03): the expected values
      are the vectors of `tests/unit/kernel/hash_vectors.txt` (written by
      `tests/unit/kernel/gen_hash_vectors.py`, an implementation independent of both compilers) —
      never a constant produced by axiom0's C `kernel/hash.c`. (a) A test built from the **real**
      `compiler/kernel/hash.ax` (a generated bundle that embeds the file verbatim with a
      regenerate-and-compare manifest, or a direct module build — engineer's choice), e.g.
      `tests/selfhost/kernel/hash_native.ax`, `modes: interp native`, checks every vector of
      `hash_vectors.txt` (embedded as a generated byte table) plus the `"Xin chào thế giới"` UTF-8
      bytes. (b) `tests/std/core/qa_hash_vectors.ax` loses its `modes: interp` restriction and passes
      natively against the same vectors for `std/core/hash.ax`. (c)
      `tests/selfhost/kernel/qa_kernel_hash.ax` no longer carries a hand copy whose bodies differ
      from `compiler/kernel/hash.ax` (its `wrapping_mul_u64 { a * b }` checked-multiply body is
      wrong); it tests the real module or is deleted in favour of (a). All three pass in both modes
      with `--compiler build/axiom0.exe` run inside `build-snap-T134`.
- [ ] MIR/LIR/MC golden files touched by the lowering are updated and reviewed (not blindly
      re-blessed): the report lists each regenerated golden and why it changed.
- [ ] Full suite passes in the snapshot `build-snap-T134` with the native legs enabled; the report
      lists every test that was passing vacuously before this fix (name, what it now checks, fixed
      here or follow-up).
- [ ] Build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T134-report.md` with exact `## Files changed`.

## Out of scope
- Saturating ops, i128/u128 (E12.1); panic message printing beyond what SPEC-03 already defines.
- Fixing bugs in ported Axiom modules under `compiler/` or `std/` (report them as follow-ups).
- Any change to T085's files beyond test expectations under `tests/selfhost` that were vacuous.

## Notes
- Why sonnet/opus gate: the semantics are fully specified (SPEC-03, ADR-0004 §1) and verifiable by
  interp-vs-native differential tests; the gate is opus because the fix touches every executor and
  silently-vacuous tests are what let the defect through.
- `paths` overlap `tests/selfhost` with running T085, so the scheduler starts this task right after
  T085 is accepted; priority 0 makes it run alone. T086 depends on this task.
- Existing correct special cases to keep working: size_of/align_of/ptr_*/null_mut/needs_drop/
  drop_in_place/forget/address_of*/is_null (typeck ~line 2150) and host intrinsics heap_alloc …
  monotonic_ns (pipeline.c `build_mir_for_item`, lir/lower.c `__ax_host_*`). Move them into the
  table without behaviour change.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
- axiom0 is not frozen yet (freeze after T087); the `AX0-FIX-NN` title keeps the freeze-rule naming.
- Amended 2026-10-20 by the oracle-independence plan (ADR-0034): hash acceptance uses the Python
  vectors, the real `compiler/kernel/hash.ax` and a native leg for `qa_hash_vectors.ax`.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale (2026-10-14) and is
  not evidence.

## Log
