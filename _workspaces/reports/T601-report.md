STATUS: COMPLETE round=0

# T601 Report — E15.1 Verified MIR to OptIR Lowering, Dominance Frontier & SSA/MemorySSA Construction

## Summary
Implemented the `OptIR` unified dataflow optimization intermediate representation (`compiler/opt/optir/mod.ax`), Cooper-Harvey-Kennedy dominator tree and dominance frontier computation, minimal SSA construction (with `Copy`/`Move` value sharing and SROA aggregate field projection), `MemorySSA` (`LiveOnEntry`, `MemoryDef`, `MemoryUse`, `MemoryPhi`, `MemoryRegion`, `AliasResult`, and clobber walking), the three-valued certainty lattice (`Proven`, `Possible`, `Unknown`) with `ProofProvenance` and bounded step budgets (`OPT_MAX_CERTAINTY_STEPS`), `OptIR` contract verification (`optir_verify_contract`) and `MirBody` reconstruction (`optir_reconstruct_mir`), and `inspect --emit=optir` / `--emit=memssa` in `compiler/driver`, per `spec/SPEC-70-optir-ssa-memoryssa.md`.

### Requirements Covered
- `REQ-OPT-337`, `REQ-OPT-338`: SSA value sharing across `Copy` and `Move` assignments (`OPT_INST_COPY` shares `OptValueId` with its source operand while preserving `OPT_FLAG_MOVE`), plus SROA scalarization for non-address-taken aggregate locals without `Drop` (`OPT_LOCAL_SROA`).
- `REQ-OPT-340`, `REQ-OPT-341`: Origin provenance tracking (`OptOrigin` with `Span`, `MirBbId`, `mir_stmt_idx`, `pass_id`) on `OptValue`, `OptPhi`, `OptInst`, and `OptTerminator`, plus observable semantic preservation through `optir_verify_contract` and `optir_reconstruct_mir`.
- `REQ-OPT-390`, `REQ-OPT-391`, `REQ-OPT-392`: Internal non-intrusive static analysis and `MemorySSA` (`LiveOnEntry`, `MemoryPhi`, `MemoryDef`, `MemoryUse`, `MemoryRegion`, `optir_alias_query`, `memssa_does_clobber`, `memssa_find_clobbering_def`) constructed exclusively from `Verified MIR` (`verify_mir` entry gate).
- `REQ-OPT-397`, `REQ-OPT-398`, `REQ-OPT-399`, `REQ-OPT-400`, `REQ-OPT-401`, `REQ-OPT-402`, `REQ-OPT-403`: Three-valued certainty lattice (`CERTAINTY_PROVEN`, `CERTAINTY_POSSIBLE`, `CERTAINTY_UNKNOWN`), lattice operations (`certainty_meet`/`certainty_and`, `certainty_join_paths`, `certainty_negate_hazard`, `opt_can_rewrite_proven`/`certainty_can_rewrite`, `certainty_should_emit_remark`), bounded step budget (`OPT_MAX_CERTAINTY_STEPS`), and structured `ProofProvenance` recording.

## Files changed
- `compiler/opt/optir/mod.ax`
- `compiler/driver/opts.ax`
- `compiler/driver/mod.ax`
- `compiler/driver/pipeline.ax`
- `tests/run/optir_ssa/diamond_loop_sroa.ax`
- `tests/run/optir_ssa/fixtures/verified_sample.mir`
- `tests/run/optir_ssa/fixtures/unverified_bad.mir`
- `tests/run/optir_ssa/optir_inspect.test`
- `tests/run/optir_ssa/optir_inspect_oracle.py`
- `tests/selfhost/opt/gen_opt_tests.py`
- `tests/selfhost/opt/harness_opt_unit.ax.in`
- `tests/selfhost/opt/harness_opt_pipeline.ax.in`
- `tests/selfhost/opt/qa_opt_unit.ax`
- `tests/selfhost/opt/qa_opt_pipeline.ax`
- `tests/selfhost/driver/gen_driver_tests.py`
- `tests/selfhost/driver/qa_driver_cli_and_project.ax`
- `tests/selfhost/driver/qa_driver_boundary_edges.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_a.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_b.ax`
- `tests/selfhost/driver/qa_driver_commands_a.ax`
- `tests/selfhost/driver/qa_driver_commands_b.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`

## Verification
- Built self-hosted Stage 1 (`axiomc1.exe`) and Stage 2 (`axiomc2.exe` at `-O1`) cleanly in `build-snap-T601/build` via `python tools/build_axiomc.py --out build`.
- `python tools/axtest.py --compiler build/axiom0.exe -j 1 run/optir_ssa selfhost/opt/bundles_current.test selfhost/driver/bundles_current.test selfhost/obj_link_driver/bundles_current.test selfhost/bundles_current.test`: **7/7 PASS**.
- `python tools/axtest.py --compiler build/axiomc2.exe -j 1 run/optir_ssa`: **4/4 PASS** (`diamond_loop_sroa.ax` in `interp`, `native`, `native-O1`, and `optir_inspect.test`).
- `python tools/axtest.py --compiler build/axiom0.exe -j 1 selfhost/opt`: **7/7 PASS** (`qa_opt_unit.ax` and `qa_opt_pipeline.ax` across `interp`, `native`, `native-O1`, plus `bundles_current.test`).
- `python tools/axtest.py --compiler build/axiom0.exe -j 1 selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax selfhost/driver/qa_driver_cli_and_project.ax selfhost/driver/qa_driver_boundary_edges.ax selfhost/driver/qa_driver_inspect_diff_a.ax selfhost/driver/qa_driver_inspect_diff_b.ax`: **14/14 PASS**.
