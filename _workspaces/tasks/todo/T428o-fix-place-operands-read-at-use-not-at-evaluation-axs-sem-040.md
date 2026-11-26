---
id: T428o
title: Fix — a place operand is read when the consuming rvalue/call executes, not when it is evaluated, so a later sibling operand's side effect leaks into it (`add(z, { z = 9; 1 })`, `w + { w = 9; 1 }`, `[y[0], f(mut_view(y))]`) — AXS-SEM-040
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T428j]
priority: 25
status: todo
attempts: 0
timeout_min: 240
paths: [tests/run/eval_order_operand_snapshot]
locks: [compiler/mir/builder.ax]
spec: [spec/SPEC-03-core-semantics.md]
covers: [REQ-EXP-007, REQ-MIR-006, REQ-CORE-025, REQ-CORE-026]
---
# T428o — Operands keep the value they had when they were evaluated

## Why
T428j recorded it as a limitation (`_workspaces/reports/T428j-report.md`, "Known limitation"); the architect checked it
is a real AXS-SEM-040 violation and much wider than aggregates
(`_workspaces/reports/triage-2026-11-26-T502-regression.md`). With the HEAD e085e8e6 compiler, identically in
`--interp`, native `-O0` and `-O1`:

```axiom
fn add(a: i64, b: i64) -> i64 { a + b }
fn bump(v: mut_view<[2]i64>) -> i64 { (*v)[0] = 100i64; 7i64 }

let mut z = 5i64;
let s = add(z, { z = 9i64; 1i64 });        // expected 6, gets 10
let mut w = 5i64;
let u = w + { w = 9i64; 1i64 };            // expected 6, gets 10
let mut y = [1i64, 2i64];
let x = [y[0], bump(mut_view(y))];         // expected x[0] == 1, gets 100
let mut t5 = 5i64;
let t = (t5, { t5 = 9i64; 1i64 });         // expected t.0 == 5, gets 9
```

SPEC-03 AXS-SEM-040: operands, call arguments, array/tuple elements and struct literal fields are evaluated left to
right, "each completely ... before the next starts"; a binary operator evaluates its left operand, then its right. The
MIR builder emits a `copy _z` place operand for an earlier operand and the read happens only when the call / binary
op / aggregate executes, after the later operand's side effect. This is an implementation bug (TYPE A): the spec is
clear, all three execution modes agree on the wrong value (so no differential test catches it).

## Scope
1. In `compiler/mir/builder.ax`, when lowering an operand list (call arguments, method receiver + arguments, binary
   and comparison operands, array / repeat / tuple / struct / enum / closure-capture aggregates, index expressions of
   a place, compound assignment) materialise an earlier place operand into a fresh temporary **only if** a later
   sibling operand may write memory the place can observe: the later operand contains an assignment, a call, a
   `mut_view(..)` / `address_of(..)`, an `.await`, or any raw-pointer store. Otherwise keep the direct place operand
   (no extra copies in the common case: `f(a, b)`, `a + b`, `[x, y]`).
   Reuse T428j's conservative place-overlap helpers where they fit. A `move` operand is already a value transfer;
   make sure a later operand cannot observe the moved-from place either.
2. Keep AXS-SEM-043 (drop-needing assignment through a temporary) and the T428j destination-overlap spill intact.
3. Tests `tests/run/eval_order_operand_snapshot/` (interp, native, native-O1, exact `// stdout:`): the four cases above;
   the same for struct literal fields written out of declaration order, a method call `p.m(p.a, p.bump())`, an index
   `a[i] + { i = 1; 0 }`, a compound assignment, an operand in an `async fn` with a later `.await` that mutates it, and a
   later operand that panics (earlier side effects visible, no later ones). Golden MIR test showing `f(a, b)` and `a + b`
   get **no** new temporaries and `add(z, { z = 9; 1 })` gets exactly one.

## Acceptance
- [ ] The tests above pass in all three modes; WEAK-NATIVE 0; the golden MIR shows no needless temporaries.
- [ ] Stage-2 build succeeds; stage-2 == stage-3 fixed point at `-O0` and `-O1`; `tests/opt*` codegen goldens unchanged
      or each change explained (only programs with a side-effecting later operand may change).
- [ ] Gate: task tests + the selfhost groups of `compiler/mir` + a **Tier-1 non-selfhost sweep** (every program goes
      through this code); failing ids ⊆ `_workspaces/baseline-failures.txt`.
- [ ] Report `_workspaces/reports/T428o-report.md`: the rule implemented, the "may write" test, the call sites, and an
      exact `## Files changed`.

## Out of scope
- axiom0 (frozen after T087).
- Struct-like enum variant construction (T428n).

## Log
- 2026-11-26 created by architect (`_workspaces/reports/triage-2026-11-26-T502-regression.md`)
