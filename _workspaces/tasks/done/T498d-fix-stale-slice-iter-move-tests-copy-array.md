---
id: T498d
title: Fix — stale `ui/slice/iter_move*.ax` expectations after T498 (a `[N]u8` array is Copy, so `consume(arr)` no longer moves the owner)
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: []
priority: 0
status: done
attempts: 1
timeout_min: 180
paths: [tests/ui/slice/iter_move.ax, tests/ui/slice/qa_slice_iter_move.ax, tests/run/slice/copy_array_owner_view.ax]
locks: []
spec: [spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, spec/decisions/ADR-0044-t455-integer-model-gaps.md]
covers: [REQ-OWNER-007]
started: 2026-11-22 02:29:44
finished: 2026-11-22 02:54:19
---
# T498d — make the slice iterator move tests move a non-Copy owner again

## Goal
`tests/ui/slice/iter_move.ax` and `tests/ui/slice/qa_slice_iter_move.ax` pass at 37a299d8 and fail from T498 (9f31ed56)
onwards with `missing diagnostics: ERROR AX_CAP_OUTLIVES_OWNER` (evidence: `_workspaces/reports/T499a-qa.md`,
"Regression check"). Both build `Iter { s: view(arr), .. }` over `let arr: [3]u8` / `[4]u8` and then call `consume(arr)`.
Since T498 (ADR-0044 §3, SPEC-10 AXS-OWN-003) `[N]T` is Copy when `T` is Copy, so `consume(arr)` copies, `arr` stays
`OWNED`, the view does not outlive its owner and **no diagnostic is the correct result**. The compiler is right; the tests'
expectation is stale. The tests must again exercise what they were written for: moving the owner while a view into it is
live is `AX_CAP_OUTLIVES_OWNER` (SPEC-11 AXS-CAP-004).

## Scope
- Rewrite both ui tests so the owner really moves while the view lives: use an array whose element type is not Copy
  (e.g. `struct Tok { v: u8 }` without `Copy`, `[3]Tok` / `[4]Tok`, `consume(arr: [3]Tok)`), or another non-Copy owner that a
  `view<[T]>` can point into. Keep the `//~ ERROR AX_CAP_OUTLIVES_OWNER` on the `consume(arr)` line and keep the view used
  after the move (`len(it.s)` in the loop; read only Copy data through the view, e.g. `it.s[i].v`, so no other diagnostic
  such as a move out of a view appears). The diagnostic set must be exactly that one error (no extra diagnostics).
- Add a positive test `tests/run/slice/copy_array_owner_view.ax` (interp/native/native-O1, exact `// stdout:`): the original
  Copy-array shape — `[3]u8` owner, a struct holding `view(arr)`, `consume(arr)` by value, then the view iterated and its
  sum printed, then `arr` read again — is accepted and prints the expected values (proves the copy kept the owner alive and
  the view reads the original bytes). Cite SPEC-10 AXS-OWN-003 / ADR-0044 §3 in a header comment.
- Do NOT weaken the capability check, do not change compiler sources, do not mark either ui test xfail and do not add them to
  `_workspaces/baseline-failures.txt`.

## Acceptance
- [ ] `axtest` on `ui/slice/iter_move`, `ui/slice/qa_slice_iter_move` passes on HEAD; each reports exactly one
      `AX_CAP_OUTLIVES_OWNER` at the `consume(arr)` line. QA mutation: changing the array element type back to `u8` makes the
      test fail (missing diagnostic), proving the move is what triggers it.
- [ ] `tests/run/slice/copy_array_owner_view.ax` passes in all three modes with WEAK-NATIVE 0; QA mutates one expected value to
      prove the native leg compares output.
- [ ] Gate per axiom-qa.md "Per-task gate scope" (the whole `tests/ui/slice` and `tests/run/slice` groups, smoke set, archcheck).
- [ ] Report `_workspaces/reports/T498d-report.md` with exact `## Files changed`.

## Out of scope
- `compiler/`, `bootstrap/axiom0` (frozen), `spec/`, `docs/`.

## Log
- 2026-11-22 created by axiom-architect (p0-slice-iter-move; regression check in T499a-qa.md, culprit T498 9f31ed56)
- 2026-11-22 02:29:44 started (attempt 1) T498d-impl
- 2026-11-22 02:54:19 accepted by QA -> done
