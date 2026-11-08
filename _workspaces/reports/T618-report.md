# T618 Report — E15.5 Straight-Line Basic-Block SLP Vectorization, Target SIMD Cost Model & LIR Vector Instruction Lowering

## Summary
- Implemented straight-line basic-block Superword-Level Parallelism (`opt_slp_vec`, `PASS_SLP_VEC = 29`) in `compiler/opt/slp/mod.ax` per `SPEC-74` (`§5.1..§5.7`, `§6`, `§10`, `AXS-VEC-036..046`, `AXS-VEC-051`, `REQ-OPT-213..215`, `REQ-OPT-218..222`):
  - Adjacent store and struct field-write chain seeding (`SLP_SEED_ADJACENT_STORES`) and associative horizontal reduction seeding (`SLP_SEED_HORIZ_REDUCTION`) for power-of-two bundle widths `L in {2, 4, 8}`, including out-of-order offset sorting, commutative operand canonicalization, and post-unroll relative index offset resolution (`base_iv + k`).
  - Bottom-up isomorphic `SlpTree` / `SlpNode` DAG construction with broadcast (`SLP_NODE_BROADCAST` -> `OPT_INST_VSPLAT`), contiguous vector load/store/arithmetic (`SLP_NODE_VECTORIZABLE` -> `OPT_INST_VLOAD` / `OPT_INST_VSTORE` / `OPT_INST_VBINOP` / `OPT_INST_VCAST`), horizontal reduction roots (`SLP_NODE_REDUCTION_ROOT` -> `OPT_INST_VREDUCE`), and fallback gather packs (`SLP_NODE_GATHER_PACK` -> `OPT_INST_VINSERT`).
  - SSA DAG acyclicity & intra-bundle independence verification, `MemorySSA` / `AliasInfo` memory hazard & capability-disjoint verification (never treating `Unknown` or `MayAlias` as `NoAlias`), strict floating-point reduction rejection (`REASON_STRICT_FP_REDUCTION`), unproven checked integer overflow rejection (`REASON_CHECKED_OVERFLOW_TRAP`), and atomic/volatile/call/drop barrier enforcement.
  - External scalar use extraction (`OPT_INST_VEXTRACT`) and target-aware `VectorCostModel` profitability estimation (`slp_estimate_tree_cost`) accounting for scalar baseline cost, vector instruction cost, gather/splat pack tax, external lane-extract boundary tax, register pressure spill penalty, and `-O0` / `-Os` profile gates.
  - Deterministic `--emit=vectorize` (`slp_vec_print`) and `--emit=vector-cost` (`slp_vec_cost_print`) formatters, plus PassManager rollback and MIR roundtrip reconstruction (`slp_vec_optimize_mir_body`).
- Implemented `OptIR` vector operation to LIR `Vec128`/`Vec256` lowering and target SIMD legalization in `compiler/lir/vec_lower/mod.ax` per `SPEC-74` (`§7`, `AXS-VEC-047..050`, `REQ-OPT-216..217`) and `SPEC-43` (`AXS-SBE-001..022`):
  - Target SIMD type legalization (`vec_lower_legalize_type`): 64-bit sub-vector packs (`2x32`, `4x16`, `8x8`) lowered to `REG_CLASS_VEC128` via exact 64-bit `LIR_INST_VMOVQ_64` transfers without out-of-bounds 128-bit memory over-reads; 128-bit packs lowered to `REG_CLASS_VEC128` (`XMM0..XMM15`); 256-bit packs lowered to `REG_CLASS_VEC256` (`YMM0..YMM15`) on AVX2 (`ISA_X86_64_V3_AVX2`) or split into `2 x Vec128` lo/hi pairs on 128-bit targets (`ISA_X86_64_V1_SSE2`).
  - Alignment-aware memory flag selection (`vec_lower_select_mem_flags`), horizontal reduction tree sequences (`PSHUFD`/`VEXTRACTI128` + lane add/mul/and/or/xor), unsupported lane op scalarization (`LIR_INST_SCALAR_LANE_OP` for integer `DIV`/`REM`), 32-byte YMM spill slot frame alignment (`LirVecFrame`), and `LIR_INST_VZEROUPPER` emission before returns when 256-bit `YMM` registers are touched.
- Added live compiler oracle, 6-case probe, and positive/negative differential fixtures under `tests/run/opt_slp_vec/`.

## Files changed
- compiler/opt/slp/mod.ax
- compiler/lir/vec_lower/mod.ax
- tests/run/opt_slp_vec/opt_slp_vec_engine.test
- tests/run/opt_slp_vec/opt_slp_vec_oracle.py
- tests/run/opt_slp_vec/opt_slp_vec_probe.ax.in
- tests/run/opt_slp_vec/adjacent_struct_and_array_slp.ax
- tests/run/opt_slp_vec/unrolled_and_reduction_slp.ax
- tests/run/opt_slp_vec/rejected_gather_alias_and_barriers_slp.ax
- tests/run/opt_slp_vec/slp_checked_overflow_panic.ax
- tests/run/opt_slp_vec/slp_bounds_oob_panic.ax

## Verification
- `python build-snap-T618/tools/axtest.py -j 1 --root build-snap-T618 --build-dir build-snap-T618/build --compiler build-snap-T618/build/axiomc2.exe run/opt_slp_vec run/opt_loop_vec run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 39 PASS 39 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `196 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T618` -> verified clean scope compliance

STATUS: COMPLETE round=0
