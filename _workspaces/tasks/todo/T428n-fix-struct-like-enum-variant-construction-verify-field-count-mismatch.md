---
id: T428n
title: Fix — constructing any struct-like enum variant (`E.S { x: 5i64, y: 6i64 }`) fails with AX_VERIFY_TYPE_MISMATCH "enum aggregate variant field count mismatch"
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T428j]
priority: 30
status: todo
attempts: 0
paths: [tests/run/enum_struct_variant]
locks: [compiler/mir/builder.ax, compiler/verify/verifier.ax, compiler/types/typeck.ax, compiler/hir/lower.ax]
spec: [spec/SPEC-02-grammar.md, spec/SPEC-03-core-semantics.md]
covers: [REQ-GRM-041, REQ-TYP-083, REQ-TYP-269]
---
# T428n — Struct-like enum variants can be constructed and matched

## Why
Found by T428j (`_workspaces/reports/T428j-report.md`, "Pre-existing defects" 1) and reproduced by the architect
(`_workspaces/reports/triage-2026-11-26-T502-regression.md`) with the HEAD e085e8e6 compiler:

```axiom
enum E {
    A,
    S { x: i64, y: i64 },
}

fn main() -> i32 {
    let s = E.S { x: 5i64, y: 6i64 };
    match s {
        E.S { x, y } => (x + y) as i32,
        E.A => 0,
    }
}
```

`run --interp` and `build` both stop with `error[AX_VERIFY_TYPE_MISMATCH]: enum aggregate variant field count mismatch`
at the literal. SPEC-02 AXS-GRM-030 allows struct variants (`Rect { w: f32, h: f32 }`) and AXS-GRM-095 their
patterns; so the MIR built for the literal (or the variant field list the verifier compares against) is wrong. Tuple
variants (`E.V(a, b)`) work. This is an implementation bug (TYPE A).

## Scope
1. Find where the field counts diverge (HIR lowering of a struct literal whose path names a variant, typeck of the
   variant's field list, the `Aggregate(Enum, variant, operands)` built by `compiler/mir/builder.ax`, or the verifier
   check) and fix it at the source. Operands are ordered by the variant's **declaration** order, evaluated in
   **written** order (AXS-SEM-040), and shorthand `E.S { x, y }` / `..` base forms follow the struct-literal rules.
   Change only the files in `locks:` that the fix needs; say in the report which ones changed.
2. Tests `tests/run/enum_struct_variant/` (interp, native, native-O1, exact `// stdout:`): construction with fields in
   declaration and in reversed order, field shorthand, a struct variant beside unit and tuple variants, a variant whose
   fields have mixed sizes and padding (`{ a: u8, b: i64, c: u16 }`), nested in a struct and in an array, matched
   with full, partial (`..`) and nested patterns, passed by value to and returned from a function, and one with a
   drop-needing field (drop runs exactly once). A compile-fail test: a missing or unknown field gives the struct-literal
   diagnostic, not a verifier error.
3. Restore the struct-variant case T428j removed from `tests/run/agg_self_assign/enum_payload.ax` as a new file in this
   task's directory (`e = E.S { x: match e {..}, y: .. }` reading the destination).

## Acceptance
- [ ] The tests above pass in all three modes; WEAK-NATIVE 0.
- [ ] Stage-2 build succeeds; stage-2 == stage-3 fixed point at `-O0` and `-O1`.
- [ ] Gate: task tests + affected set (grep of the changed functions) + the selfhost groups of every changed module +
      smoke; failing ids ⊆ `_workspaces/baseline-failures.txt`.
- [ ] Report `_workspaces/reports/T428n-report.md`: root cause (file:function), the fix, an exact `## Files changed`.

## Out of scope
- The general operand-timing defect (T428o).

## Log
- 2026-11-26 created by architect (`_workspaces/reports/triage-2026-11-26-T502-regression.md`)
