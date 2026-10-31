---
id: T156
title: Dump and diagnostic parity (resolved PathSegment, type interning order, message texts), oracle compares dumps, divergence registry empty
phase: P10-selfhost
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T147, T148, T149, T150, T151, T152, T153, T154, T155]
priority: 118
status: doing
attempts: 1
paths: [compiler/resolve, compiler/resolve_hir, compiler/types, compiler/typeck, compiler/typeck_traits, compiler/diag, compiler/hir, compiler/mir, compiler/driver, bootstrap/axiom0/src/driver, tests/run/parity/diag, tests/selfhost]
spec: [spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md]
covers: [REQ-BOOT-085, REQ-TST-089, REQ-BLD-030]
started: 2026-10-31 14:56:04
unblocks: 1
agent: T156-impl
---
# T156 — Dump and diagnostic parity; registry empty

## Goal
`axiomc inspect --emit=<stage>` prints exactly what axiom0 prints for every stage and corpus
program, and axiomc's diagnostics are byte-identical (code, severity, span, message text;
ADR-0035 §3). The e2e oracle enforces it, and `known_divergent.txt` is empty when T086 starts.

Confirmed differences (architect probe 2026-10-20):
1. `resolved` dump: `(PathSegment @Sym(2) "i32")` vs axiom0 `(PathSegment "i32")` for builtin type
   segments (14 registry entries have `resolved` as first stage).
2. Type interning order: `type#29` vs `type#26` in `mir`/`lir` dumps (`tests/run/array/*`,
   `trait2/*`, …) — the port interns slice/array/fn types in a different order.
3. Diagnostic texts: axiomc prints generic texts (`type error`) where axiom0 prints specific ones
   (`unreachable statement`, `cannot index into a value of this type`); registry entry
   `tests/run/native_enum/01-simple.ax` differs only in that warning's text.

## Scope
- Port dump printing, interning order and the diagnostic message table so that the outputs equal
  axiom0's.
- Extend `tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py`: a program is `equal` only if, in
  addition to today's checks, every `inspect --emit=<stage>` output of `INSPECT_STAGES` is identical
  (exit code, stdout, stderr).
- Align driver `inspect` stage handling and object emission across `compiler/driver/pipeline.ax` and
  `bootstrap/axiom0/src/driver/emit_{mir,lir,mi,mc,obj}.c` for the 20 residual `inspect`-only
  divergences:
  1. **Error-case `inspect` parity (4 programs: `tests/driver/error.ax`,
     `tests/run/parity/traits/qa_self_missing_member.ax`,
     `tests/run/parity/diag/cannot_index.ax`, `tests/run/parity/diag/not_callable.ax`)**:
     - In `compiler/driver/pipeline.ax` (`driver_execute_inspect_ctx`, `EMIT_HIR`), when `!ok` after
       `pipeline_run_stages(..., STAGE_HIR, ...)` because `STAGE_RESOLVE` reported errors (while
       `(ctx.ast.items as usize) != 0` and `(ctx.hir.items as usize) == 0`), still run
       `pipeline_stage_hir(mut_view(*ctx))` before `session_render_hir_into(...)` so `inspect --emit=hir`
       lowers and dumps HIR alongside the resolve diagnostics and exits `AX_EXIT_DIAG` (`1`), matching
       `bootstrap/axiom0/src/driver/pipeline.c` (`ax_pipeline_run(&st, AX_STAGE_HIR)`).
     - In `bootstrap/axiom0/src/driver/emit_{mir,lir,mi,mc,obj}.c`, capture
       `int rc = ax_pipeline_run(&st, AX_STAGE_TYPECK);` on the `.ax` path and return `rc` immediately
       (after `ax_pipeline_free(&st); free(pos_argv);`) when `rc != AX_EXIT_OK` (matching
       `emit_thir.c:385-386` and `compiler/driver/pipeline.ax`), instead of only checking `st.failed`.
  2. **Closure & indirect-call `inspect --emit=obj` parity (16 programs: 15 closure programs +
     `tests/run/native_p7/qa_fn_ptr.ax`)**:
     - In `bootstrap/axiom0/src/driver/emit_obj.c` (`run_emit_obj`), guard `item->fn.name.v != 0`
       before calling `ax_interner_get(&st.interner, item->fn.name)` and fall back to
       `snprintf(name_buf, 256, "__ax_fn_%u", (uint32_t)item->fn.symbol.v);` for anonymous closure
       functions (matching `build.c:505-510` and `lir/lower.c:127`).
     - In `compiler/driver/pipeline.ax` (`driver_emit_objmodel`), use `if fname_id_v == 0u32` (instead
       of `if is_build_mode && fname_id_v == 0u32`) to call
       `backend_alloc_anon_fn_sym(mut_view(ctx.backend_arena), (*fn_item).symbol.v)` so anonymous
       closure functions receive `"__ax_fn_%u"` in both `build` and `inspect --emit=obj`.
     - In `bootstrap/axiom0/src/driver/emit_obj.c` (`encode_mi_to_sec`, `case AX_X64_MI_CALL:`), add
       the indirect register call branch
       `else if (inst->op_count > 0 && inst->ops[0].kind == AX_X64_OP_REG) { ax_x64_call_r(sec, inst->ops[0].reg); }`
       (matching `build.c:169-171` and `compiler/target/x64/frame.ax:693-695`).
  3. Regenerate affected selfhost bundles (`tests/selfhost/driver/gen_driver_tests.py` and
     `tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py`) after updating
     `compiler/driver/pipeline.ax` and `bootstrap/axiom0`.
- Residuals: re-run the oracle; any entry still listed whose cause belongs to T147–T155 is fixed
  here if it lies in this task's paths, otherwise reported `STATUS: BLOCKED` with the entry list
  (the architect files the fix; the gate never passes with a non-empty registry).

## Acceptance
- [ ] `tests/run/parity/diag/`: ui tests for three diagnostics whose message text differed
      (unreachable statement warning, cannot-index error, one more from the probe) with expected
      stderr written from axiom0's message table; and the oracle's dump comparison covers them.
- [ ] `known_divergent.txt` contains only its comment header (0 entries) and
      `axiomc_e2e.test` prints `AXIOMC-E2E programs=<n> equal=<n> known_divergent=0` with the extended
      dump comparison.
- [ ] Full suite passes in `build-snap-T156` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T156-report.md` with exact `## Files changed`, the final
      `AXIOMC-E2E` line and the removed registry paths.

## Out of scope
- New diagnostics or message rewording (both compilers keep axiom0's texts until after T087).

## Notes
- ADR-0035 §3 Revisit: if porting message texts proves out of proportion, the owner may relax the
  rule to code + severity + span; until then texts must match.
- ADR-0035 §4: remove registry lines explicitly; adding is forbidden.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-30 17:42:41 started (attempt 1) T156-impl
- 2026-10-31 14:39:00 block: 20 residual inspect-only divergences rooted in compiler/driver/pipeline.ax and bootstrap/axiom0/src/driver/emit_*.c outside T156 paths
- 2026-10-31 14:54:21 unblocked (cycle 1) 
- 2026-10-31 14:56:04 started (attempt 1) T156-impl
