---
id: T610
title: E15.3 — Natural loop discovery, loop canonicalization, Scalar Evolution (SCEV) & range/bounds-check elimination (BCE)
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T606, T609]
priority: 103
status: todo
attempts: 0
paths: [compiler/opt/loops, compiler/opt/bce, tests/run/opt_bce]
spec: [spec/SPEC-72-loops-scev-bce.md, spec/decisions/ADR-0037-loops-discriminant-and-aggregate-memdef-clobber.md, 0113, 0165, tasks/0366, tasks/0402, tasks/0416, tasks/0549]
covers: [REQ-OPT-143, REQ-OPT-144, REQ-OPT-145, REQ-OPT-146, REQ-OPT-147, REQ-OPT-155, REQ-OPT-156, REQ-OPT-157, REQ-OPT-158, REQ-OPT-159, REQ-OPT-160, REQ-OPT-161, REQ-OPT-162, REQ-OPT-189, REQ-OPT-190, REQ-OPT-342]
started: 2026-11-05 18:05:07
unblocks: 1
---
# T610 — E15.3 — Natural loop discovery, loop canonicalization, Scalar Evolution (SCEV) & range/bounds-check elimination (BCE)

## Goal
Implement CFG natural loop discovery, preheader/latch/LCSSA canonicalization, overflow-faithful Scalar Evolution (`SCEV`), dominating range analysis (`RangeInfo`), and Bounds-Check Elimination (`BCE`) in `compiler/opt/loops` and `compiler/opt/bce`.

## Scope
- Implement natural loop detection, loop nesting forest, preheader/latch insertion, and LCSSA form in `compiler/opt/loops`, preserving `Drop`, ownership, capability, synchronization, async suspension, and FFI boundaries (`REQ-OPT-155..162`).
- Implement `SCEV` affine add-recurrence analysis (`{start, +, step}`) respecting checked vs wrapping integer semantics and computing proven trip counts.
- Implement `RangeInfo` and `BCE` in `compiler/opt/bce` (`REQ-OPT-189`, `REQ-OPT-190`, `REQ-OPT-342`) to eliminate proven in-bounds array, `view<[T]>`, `mut_view<[T]>`, and `Vec<T>` index checks while retaining checks for any `Unknown` or potentially out-of-bounds index.
- Validate `MemorySSA` and `EffectInfo` loop dependencies (`REQ-OPT-143..147`).

## Acceptance
- [ ] Differential run and `OptIR` dump tests in `tests/run/opt_bce` verify elimination of proven bounds checks in `for i in 0..len(a)` and guarded slices, and verify that out-of-bounds accesses still panic identically at `-O0`, `-O1`, and `-O2`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T610-report.md` with exact `## Files changed`.

## Out of scope
- Loop-invariant code motion, unrolling/peeling, and iterator fusion (`T611`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T610/build` and `python tools/axtest.py --compiler build-snap-T610/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).
- **Unblock instructions (`ADR-0037`, `_workspaces/reports/T610-qa.md` Round 2 Findings 1 & 2 — continue from the existing implementation in `compiler/opt/loops/mod.ax`, `compiler/opt/bce/mod.ax`, and `tests/run/opt_bce/*`; do not rewrite from scratch)**:
  1. **Round 2 Finding 1 — `OPT_INST_DISCRIMINANT` in `loops_can_hoist_inst` (`compiler/opt/loops/mod.ax:2994`)**:
     - Import `OPT_INST_DISCRIMINANT` (and `OPT_INST_AGGREGATE`) from `compiler.opt.optir` in `compiler/opt/loops/mod.ax`.
     - At `compiler/opt/loops/mod.ax:2994`, update `if opc == OPT_INST_LOAD || opc == OPT_INST_LEN` to `if opc == OPT_INST_LOAD || opc == OPT_INST_LEN || opc == OPT_INST_DISCRIMINANT` so `_d = discriminant(place)` checks `loops_local_written_in_loop` on `inst.rhs_place.local` and any dynamic `MIR_PROJ_INDEX` / `MIR_PROJ_SUB_SLICE` operand locals, enforces the `rreg.cap_mode == CAP_MODE_RAW_PTR` zero-trip trap guard (`proven_nonzero_trip && lp_dominates_all_exits`), and runs `loops_region_clobbered_in_loop`.
  2. **Round 2 Finding 2 — Whole-aggregate `MemoryDef` (`OPT_INST_AGGREGATE` with `place.proj_count == 0`) clobber checks in `compiler/opt/bce/mod.ax` and `compiler/opt/loops/mod.ax`**:
     - In `bce_inst_clobbers_len_state` (`compiler/opt/bce/mod.ax:1198-1208`), import `OPT_INST_AGGREGATE` from `compiler.opt.optir` and treat any `MIR_STMT_ASSIGN` instruction with `inst.mem_def.v != MEM_SSA_NONE`, `opc == OPT_INST_AGGREGATE`, or `inst.place.proj_count > 0` (`opc != OPT_INST_NOP`) as a memory write that must run `alias_query_places(unsafe { view(*info) }, body, mut_view(*arena), view(inst.place), region_place, pt)` (also check `view(inst.orig_stmt.place)` if `inst.place.local.v == 0`). Also in `bce_term_clobbers_len_state` (`compiler/opt/bce/mod.ax:1228-1269`), when `can_mutate_root` holds on `OPT_TERM_DROP` or `OPT_TERM_CALL` with `bb.term.has_call_dest`, run `alias_query_places` on `view(bb.term.drop_place)` / `view(bb.term.call_dest)` against `region_place` as well.
     - In `loops_region_clobbered_in_loop` (`compiler/opt/loops/mod.ax:2833-2843`), inside `else if opc != OPT_INST_NOP && sk == MIR_STMT_ASSIGN`, run `alias_extract_region` + `alias_query_regions` whenever `dpl.proj_count > 0`, `(unsafe { (*inst).mem_def.v }) != MEM_SSA_NONE`, `opc == OPT_INST_AGGREGATE`, `loops_local_has_indirect_mutation(body, info, dpl.local.v)`, `dpl.local.v == reg.base_local.v`, or `(reg.has_resolved_place && dpl.local.v == reg.resolved_place.local.v)`. Also in `lp_base_container_stable_in_loop` (`compiler/opt/loops/mod.ax:3746-3750`), include `opc == OPT_INST_AGGREGATE` alongside `OPT_INST_STORE` / `OPT_INST_VOLATILE_STORE` when checking `inst.place.local.v == base_loc`.
     - Add regression tests in `tests/run/opt_bce/opt_bce_probe.ax.in` and `tests/run/opt_bce/opt_bce_oracle.py` covering `OPT_INST_DISCRIMINANT` hoisting (positive invariant `view<State>` -> `true`; negative local enum mutation `st = State.Done`, `mut_view<State>` mutation `*mv = State.Done`, and zero-trip raw pointer `*raw_p` -> `false`) and whole-aggregate `MemoryDef` clobbers (`bug_bce_agg_vec` `a = Vec<i32> { ptr: p, len: 0, cap: 4 }` -> `vec_checks_eliminated == 0`; `bug_loops_agg_clobber` `a = Pair { x: 99, y: 99 }` -> `loops_can_hoist_inst == false`).

## Log
- 2026-11-03 02:40:00 created by T215 (P15 phase planning)
- 2026-11-05 18:05:07 started (attempt 1) T610-impl
- 2026-11-06 07:59:02 block: QA failed 3 times: (1) OPT_INST_DISCRIMINANT missing in loops_can_hoist_inst; (2) whole-aggregate MemoryDef (OPT_INST_AGGREGATE proj_count==0) bypasses AliasInfo clobber check in bce/loops
- 2026-11-07 06:15:52 unblocked (cycle 1) --note ADR-0037: fix OPT_INST_DISCRIMINANT in loops_can_hoist_inst and whole-aggregate MemoryDef clobber checks in bce/loops
