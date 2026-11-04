# T628 Report — Better instruction selection, branchless if-conversion & post-RA machine peephole optimization

## Summary

Implemented E15.8 (`T628`): upgraded x86-64 LIR-to-Machine-IR instruction selection (`compiler/target/x64/isel.ax`, `compiler/lir/`), branchless diamond if-conversion (`cmovcc` / `setcc`), and the post-register-allocation machine peephole optimizer (`compiler/backend/peephole/`, `compiler/target/x64/frame.ax`), together with differential, run, and Machine IR golden tests in `tests/mc/isel_peephole/` and self-host test coverage in `tests/selfhost/isel/` and `tests/selfhost/backend/`.

1. **Address-Mode Folding & Immediate Selection (`compiler/target/x64/isel.ax`, `REQ-OPT-205`, `AXS-MCOPT-010`, `AXS-MCOPT-011`)**:
   - Implemented `isel_match_addr` and `isel_match_scaled_index` to recognize `base + index * scale + disp` (`scale in {1, 2, 4, 8}`, signed 32-bit `disp`) across `LIR_INST_ADD`, `LIR_INST_OFFSET`, `LIR_INST_SUB`, `LIR_INST_MUL`, and `LIR_INST_SHL`, emitting single-instruction `lea` for arithmetic and folding complex addressing modes directly into `LIR_INST_LOAD` and `LIR_INST_STORE` memory operands.
   - Folded 32-bit signed immediates (`isel_fits_i32`) directly into arithmetic (`add`, `sub`, `and`, `or`, `xor`), shift (`shl`, `shr`, `sar`), and comparison (`cmp`) instructions without materializing scratch registers, while keeping 64-bit immediates outside `[-2^31, 2^31 - 1]` in `mov reg, imm64`.

2. **Strength Reduction for Constant Multiplication, Division & Remainder (`compiler/target/x64/isel.ax`, `REQ-OPT-205`, `AXS-MCOPT-012`)**:
   - Lowered constant multiplications by `{0, 1, -1}`, `{3, 5, 9}` (single-cycle `lea r, [r + r*{2,4,8}]`), and powers of two (`shl`).
   - Implemented 64-bit unsigned magic-number reciprocal multiplication (`isel_umagic64` / `isel_emit_umagic_div`) and power-of-two shift/mask lowering for `LIR_INST_UDIV` and `LIR_INST_UREM`, and signed constant division/remainder lowering (`isel_opt_lower_sdiv_srem_inst`) for `LIR_INST_DIV` and `LIR_INST_REM` using sign-correction + magic multiply without `idiv`.

3. **Branchless Diamond If-Conversion (`compiler/target/x64/isel.ax`, `REQ-OPT-207`, `REQ-OPT-208`, `REQ-OPT-369`, `REQ-OPT-370`, `AXS-MCOPT-013`, `AXS-MCOPT-014`)**:
   - Implemented `isel_check_diamond_arm` and `isel_try_if_convert_diamond` to convert short, pure diamond basic-block patterns (`cost_then + cost_else + 1 <= 6` with no trapping instructions, calls, or arbitrary memory writes) into branchless `setcc` (for `{0, 1}` boolean selects) or `cmovcc` sequences.
   - Fused comparison flags directly into branches (`isel_emit_cond_flags_for_branch`) using `test reg, reg` for boolean conditions and direct `cmp` condition codes (`x64_cc_invert` through `LIR_INST_NOT` / `xor 1`).

4. **Post-RA Machine Peephole Optimizer (`compiler/backend/peephole/peephole.ax`, `compiler/target/x64/frame.ax`, `REQ-OPT-034..036`, `AXS-MCOPT-020..026`)**:
   - Created `compiler.backend.peephole` (`x64_peephole_opt_in_arena`, `x64_peephole_opt`) and wired it into `x64_frame_lower_opt_in_arena` / `x64_frame_lower_in_arena` after register allocation and spill resolution and before `x64_verify_checked`.
   - Eliminates redundant self-moves (`mov r, r`), identity arithmetic (`add/sub/or/xor/shl/shr/sar r, 0`), dead register overwrites, store-followed-by-identical-load pairs (guarded by call/atomic/volatile/aliasing barriers), `cmp r, 0` -> `test r, r` (via `peep_cmp_zero_can_use_test`), and `mov r, 0` -> `xor r, r` (only when `EFLAGS` are proven dead via `x64_flags_are_dead_after`).
   - Threads jump-to-jump chains, inverts branch conditions over fallthroughs, and removes fallthrough jumps to the next basic block (`peep_opt_cfg`).

5. **Round 1 QA Fixes (`T628-qa.md` Findings 1–4 & Non-Blocking Notes)**:
   - **Finding 1 (Cast Constant Propagation & `INT_MIN` Width Semantics)**: Normalized propagated and materialized constants across narrowing, widening, and sign-changing integer/bool/char/pointer casts (`isel_type_can_prop_const`, `isel_norm_const_to_ty`, `isel_const_inst_val`, `isel_vreg_const`, `isel_opt_pass3_aliases`) while preserving raw uncast `LIR_INST_CONST` magnitudes (`inst_ty == dst_ty`, e.g., `const 128` feeding `0 - 128` for `-128i8`, `-32768i16`, `-2147483648i32`), fixed sub-word signed load selection (`isel_type_is_signed_int`), restricted same-block store-to-load vreg aliasing to matching slot/load/vreg types, and computed `isel_urem64` bit-by-bit without 64-bit unsigned `*` for Stage-0 `axiom0` compatibility.
   - **Finding 2 (`-O0` vs `-O1`/`-O2` Policy & Driver Wiring)**: Deleted `lir_is_unopt_golden` completely from `compiler/lir/builder.ax`, added `lir_lower_opt`, `lir_lower_ext_opt`, `backend_lower_fn_to_lir_opt`, `backend_lower_fn_to_mi_opt`, and `backend_lower_fn_to_mc_checked_opt` so `LirBody.is_opt` defaults to `false` at `-O0`, and wired `run_opt` (`-O1`/`-O2`) through `compiler/driver/pipeline.ax` (`driver_emit_objmodel_filtered` and `inspect --emit={lir,mi,mc}` via `session_emit_{lir,mi,mc}_mir_text_opt`).
   - **Finding 3 (`TY_BOOL` Guard on `^ 1` / `!` Condition Inversion)**: Guarded `LIR_INST_BIT_XOR(..., 1)` and `LIR_INST_NOT` inversion in `isel_emit_cond_flags_for_branch` to require `isel_vreg_is_bool` on both result and operand, and guarded scalar GPR conditions (`isel_vreg_is_scalar_gpr`) in `isel_try_if_convert_diamond` and `isel_opt_lower_terminator` (plus `REG_CLASS_GPR` guards in `isel_check_diamond_arm`).
   - **Finding 4 (Sound `EFLAGS` Liveness & Variable `cl` Shifts)**: Fixed `x64_mi_flags_effect` (`X64_MI_ASSERT` -> `FLAGS_USE`, `X64_MI_CALL`/`X64_MI_IDIV`/`X64_MI_RET` -> `FLAGS_KILL`), `x64_flags_are_dead_after`, and `peep_cmp_zero_can_use_test` to return `false` at `X64_MI_JMP` and end-of-block `(curr as usize) == 0` (preserving `EFLAGS` across fallthrough blocks after `peep_opt_cfg` removes fallthrough jumps) and to never treat variable-count shifts (`cl`) as killing prior `EFLAGS`.
   - **Self-Host Bundles**: Regenerated and verified `--check` across all 28 selfhost bundles in `tests/selfhost/{lir,isel,encode,backend,driver,obj_link_driver}` (updating `sym_pad_count=256` in `tests/selfhost/driver/gen_driver_tests.py` to avoid `axiomc1` symbol-table padding collision).

## Files changed

- `compiler/backend/mod.ax`
- `compiler/backend/peephole/mod.ax`
- `compiler/backend/peephole/peephole.ax`
- `compiler/backend/session.ax`
- `compiler/driver/pipeline.ax`
- `compiler/lir/builder.ax`
- `compiler/lir/lir.ax`
- `compiler/lir/mod.ax`
- `compiler/target/x64/encode.ax`
- `compiler/target/x64/frame.ax`
- `compiler/target/x64/isel.ax`
- `compiler/target/x64/mod.ax`
- `tests/mc/isel_peephole/branchless_cmov_diff.ax`
- `tests/mc/isel_peephole/branchless_cmov_o2.ax`
- `tests/mc/isel_peephole/cast_const_prop.ax`
- `tests/mc/isel_peephole/cast_const_prop_o2.ax`
- `tests/mc/isel_peephole/checked_add_overflow_o1.ax`
- `tests/mc/isel_peephole/checked_add_overflow_o2.ax`
- `tests/mc/isel_peephole/checked_unsigned_sub_underflow_o1.ax`
- `tests/mc/isel_peephole/checked_unsigned_sub_underflow_o2.ax`
- `tests/mc/isel_peephole/const_div_rem_diff.ax`
- `tests/mc/isel_peephole/const_div_rem_o2.ax`
- `tests/mc/isel_peephole/isel_peephole_mi.ax`
- `tests/mc/isel_peephole/isel_peephole_mi.mi`
- `tests/mc/isel_peephole/lea_addressing_diff.ax`
- `tests/mc/isel_peephole/lea_addressing_o2.ax`
- `tests/mc/isel_peephole/peephole_flags_and_barriers_diff.ax`
- `tests/mc/isel_peephole/peephole_flags_and_barriers_o2.ax`
- `tests/mc/isel_peephole/peephole_flags_fallthrough_cl_diff.ax`
- `tests/mc/isel_peephole/peephole_flags_fallthrough_cl_o2.ax`
- `tests/mc/isel_peephole/xor1_nonbool_switch_diff.ax`
- `tests/mc/isel_peephole/xor1_nonbool_switch_o2.ax`
- `tests/selfhost/backend/gen_backend_tests.py`
- `tests/selfhost/backend/harness_backend_unit.ax.in`
- `tests/selfhost/backend/qa_backend_diff_lir_a.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_b.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax`
- `tests/selfhost/backend/qa_backend_edge.ax`
- `tests/selfhost/backend/qa_backend_unit.ax`
- `tests/selfhost/driver/gen_driver_tests.py`
- `tests/selfhost/driver/qa_driver_boundary_edges.ax`
- `tests/selfhost/driver/qa_driver_cli_and_project.ax`
- `tests/selfhost/driver/qa_driver_commands_a.ax`
- `tests/selfhost/driver/qa_driver_commands_b.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_a.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_b.ax`
- `tests/selfhost/encode/qa_encode_edge_cases.ax`
- `tests/selfhost/encode/qa_encode_instructions.ax`
- `tests/selfhost/encode/qa_encode_relocs_and_frames.ax`
- `tests/selfhost/isel/qa_frame_layout_and_verify.ax`
- `tests/selfhost/isel/qa_frame_layout_and_verify.ax.in`
- `tests/selfhost/isel/qa_isel_diff_golden.ax`
- `tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax`
- `tests/selfhost/isel/qa_isel_instructions_and_abi.ax`
- `tests/selfhost/lir/qa_lir_from_ax_a.ax`
- `tests/selfhost/lir/qa_lir_from_ax_b.ax`
- `tests/selfhost/lir/qa_lir_from_ax_c.ax`
- `tests/selfhost/lir/qa_lir_from_ax_d.ax`
- `tests/selfhost/lir/qa_lir_from_ax_e.ax`
- `tests/selfhost/lir/qa_lir_from_mir.ax`
- `tests/selfhost/lir/qa_lir_seam_edge.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`

## Verification

- **3-Stage Bootstrap & Fixed-Point (`build-snap-T628`)**:
  - `python build-snap-T628/tools/build_axiomc.py --root build-snap-T628 --out build-snap-T628/build --stage 3 --force`
  - `STAGE1 OK`: `build-snap-T628/build/axiomc1.exe` (`18,957,312` bytes, `sha256=c8944b79c572abcf`, `wall=52.10s`)
  - `STAGE2 (O1) OK`: `build-snap-T628/build/dir_stage2_O1/axiomc2.exe` (`5,833,216` bytes, `sha256=e6427fba4cb802a2`, `wall=723.23s`)
  - `STAGE3 (O1) OK`: `build-snap-T628/build/dir_stage3_O1/axiomc3.exe` (`5,833,216` bytes, `sha256=e6427fba4cb802a2`, `wall=197.01s`)
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == e6427fba4cb802a25fdd21185c4f57b9daeba14554f503ed0e99522dcda86912`
- **Targeted Suites (`build-snap-T628`, `-j 1`)**:
  - `cd build-snap-T628 && python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 1 -v mc/isel_peephole mc/isel mc/regalloc lir run/intrinsics run/parity/intrinsics ui/intrinsics`: **TOTAL 150 PASS 150 FAIL 0 SKIP 0 XFAIL 0 (`WEAK-NATIVE 0`)** — includes `ops_table.ax`, `qa_intrinsics_ptr_edges.ax`, `cast_const_prop.ax`, `cast_const_prop_o2.ax`, `xor1_nonbool_switch_diff.ax`, `peephole_flags_fallthrough_cl_diff.ax`, `isel_peephole_mi.ax` (`-O2`), and unoptimized `vs1_*` / `ra_pressure_mi.ax` without `lir_is_unopt_golden`.
- **Self-Host Bundle Freshness (`--check`) & Suites (`build-snap-T628`, `-j 1`)**:
  - `gen_{lir,isel,encode}_tests.py --check` & `gen_{backend,driver,obj_link_driver}_tests.py --axiom0 build-snap-T628/build/axiomc2.exe --check`: all `28` selfhost bundles `up to date` (exit `0`).
  - `cd build-snap-T628 && python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 1 -v selfhost/lir selfhost/isel selfhost/encode selfhost/backend selfhost/driver selfhost/obj_link_driver`: **TOTAL 88 PASS 88 FAIL 0 SKIP 0 XFAIL 0** (including `bundles_current.test` on all 6 suites and `selfhost/obj_link_driver/axiomc_e2e.test`).
- **Architecture, Coverage & Staging Gates**:
  - `python build-snap-T628/tools/archcheck.py`: `193 files scanned, 0 violations` (exit `0`).
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK`, `gaps: 0` (exit `0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit `0`).
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T628`: `0 REFUSED`, LF-only line endings (exit `0`).

STATUS: COMPLETE round=1
