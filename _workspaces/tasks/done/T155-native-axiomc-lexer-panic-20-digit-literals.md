---
id: T155
title: Natively built axiomc lexer panics (arithmetic overflow) on 20-digit integer literals
phase: P10-selfhost
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T146]
priority: 116
status: done
attempts: 1
paths: [compiler/lex, compiler/lexer, tests/run/parity/lexer, tests/selfhost]
spec: [spec/SPEC-01-lexical.md, spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md]
covers: [REQ-BLD-030]
started: 2026-10-28 13:18:23
finished: 2026-10-28 20:56:29
---
# T155 — axiomc lexer panic on 20-digit literals

## Goal
The natively built axiomc lexes every integer literal axiom0 lexes, including `u64::MAX`, without a
runtime panic, so the 8 `tokens`-stage registry programs build under axiomc.

Confirmed defect (architect probe 2026-10-20, axiomc built by axiom0 with 64 MB stack):
`fn main() -> i32 { let x: u64 = 18446744073709551615u64; ... }` — every `axiomc` command
(`inspect --emit=tokens` … `build`) exits 101 `panic: arithmetic overflow`; `9223372036854775808u64`
and `4294967295` are fine. The accumulation in `compiler/lex/scanner.ax` ~873-880
(`val * base + d` guarded by `max_q`/`max_r`) is correct in the interpreter; the same `u64`
operations compiled alone by axiom0 natively do not trap (`1844674407370955161u64 * 10u64 + 5u64`
exits 0), so the panic comes from another operation on the path (token value storage, the digit
loop, suffix handling, hashing/interning) compiled natively — possibly one of the native defects of
T134 (placeholder intrinsic bodies) or T140 (unsigned 64-bit div/rem).

## Scope
- After T134/T140 have landed, rebuild axiomc and re-check. If the panic is gone, only the regression
  test and the registry update remain. Otherwise reduce to the failing operation (a native repro built
  by axiom0 from a few lines), fix it where it lives: in `compiler/lex` if the port is wrong; if it is
  an axiom0 native-codegen defect, stop and report `STATUS: BLOCKED` with the repro (the architect
  files an AX0-FIX task — this task's paths do not include axiom0).

## Acceptance
- [ ] `tests/run/parity/lexer/u64_max_literal.ax` (`modes: interp native`): prints
      `18446744073709551615`, `0xFFFF_FFFF_FFFF_FFFFu64 == 18446744073709551615u64` result and
      `9223372036854775808u64 / 2u64` = `4611686018427387904` (values by hand). Passes with axiom0
      and is identical under the e2e oracle.
- [ ] A selfhost test built from the real `compiler/lex` sources, natively, lexes
      `18446744073709551615u64` into one `TOK_INT` with value `0xFFFFFFFFFFFFFFFF` and reports
      `AX_LEX_INT_OVERFLOW` (or axiom0's code for it) for `18446744073709551616`, like axiom0.
- [ ] `known_divergent.txt`: `tests/run/numeric/{boundary,qa_boundary_missing,qa_overflow_u64,
      qa_overflow_usize}.ax` are removed (or updated in place with the residual cause named);
      `host/fs/{dir,file_io,metadata}.ax` and `numeric/intrinsic_ops.ax` move past the `tokens` stage
      (their lines updated; removed by whichever of T150/T155 lands last); no entry is added.
- [ ] Full suite passes in `build-snap-T155` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T155-report.md` with exact `## Files changed`, the root cause and
      the registry changes.

## Out of scope
- Integer semantics in axiom0 (T140); intrinsics (T134, T150).

## Notes
- T140's acceptance already requires the natively built port to print `u64::MAX` correctly; if T140
  removes these entries itself (ADR-0035 §4), this task reduces to the tests above.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-28 13:18:23 started (attempt 1) T155-impl
- 2026-10-28 20:56:29 accepted by QA -> done
