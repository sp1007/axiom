# T063 Report — E15.8: Linear-scan register allocation, spill/reload & callee-saved frame integration

STATUS: COMPLETE

## Summary

Implemented `SPEC-77` (`AXS-RA-010..027`) linear-scan register allocation, spill/reload & rematerialization, lifetime-colored stack spill-slot allocation, and dynamic callee-saved register prologue/epilogue integration in `compiler/target/x64` (`REQ-OPT-203`, `REQ-OPT-204`, `REQ-OPT-212`, `REQ-OPT-218`):

1. **Target Register Description & SSE/Vector Encodings (`compiler/target/x64/encode.ax`, `compiler/target/x64/isel.ax`, `compiler/target/x64/frame.ax`)**:
   - Defined `REG_CLASS_GPR`, `REG_CLASS_XMM`, `REG_CLASS_VEC128`, `REG_CLASS_VEC256` and `REG_XMM0`..`REG_XMM15` (`16`..`31`).
   - Implemented `X64TargetDesc` and `x64_target_desc_win64` (`AXS-RA-011`) describing Windows x64 ABI caller-saved (`RAX, RCX, RDX, R8..R11, XMM0..XMM5`) and callee-saved (`RBX, RSI, RDI, R12..R15, XMM6..XMM15`) bitmasks.
   - Added SSE/vector move emitters (`x64_movups_rr`, `x64_movups_rm_disp`, `x64_movups_mr_disp`) and masked prologue/epilogue emitters (`x64_emit_prologue_masked`, `x64_emit_epilogue_masked`).
   - Fixed a critical `REX` prefix bug in `x64_lea_sym` and `x64_lea_sym_disp` (`compiler/target/x64/encode.ax`) where `dst` was passed in the `rm` position (`REX.B` = `0x49`) instead of the `reg` position (`REX.R` = `0x4C`), which previously corrupted `RSP`/`RBP` when `lea r12/r13, [rip + sym]` was emitted for extended registers `R8`..`R15`.

2. **Backward CFG Liveness, Natural Loop Nesting Depth & Live Intervals (`compiler/target/x64/frame.ax`)**:
   - Implemented `X64LivenessInfo` (`AXS-RA-012..014`) with bitset `def`/`use`/`live_in`/`live_out` per basic block, iterative backward fixed-point dataflow convergence, and back-edge natural loop body discovery computing `loop_depth[bb]`.
   - Implemented `X64LiveRange`, `X64UsePos`, and `X64LiveInterval` (`AXS-RA-015..017`) with sorted half-open `[start, end)` live ranges, use positions, fixed-register constraints, call-crossing flags, rematerialization descriptors (`X64_REMAT_CONST`, `X64_REMAT_STACK_ADDR`), and loop-depth-weighted spill weights ($10^d$, with PGO `block_exec_counts` override via `x64_regalloc_with_pgo_in_arena` per `AXS-RA-026`).

3. **Linear-Scan Register Allocation, Copy Coalescing, Parallel-Copy Cycle Breaking & Colored Spill Slots (`compiler/target/x64/frame.ax`)**:
   - Implemented `x64_regalloc_with_pgo_in_arena`, `x64_regalloc_in_arena`, and `x64_regalloc` (`AXS-RA-018..023`):
     - Honors fixed-register constraints (`RCX` for variable shifts, `RAX`/`RDX` for `DIV`/`REM`/`IDIV`, Win64 ABI argument/return registers) and call clobber masks.
     - Coalesces move/2-address hints (`copy_hint_vreg`, `fixed_reg_hint`) and folds redundant scratch `RAX` moves when `RAX` is dead.
     - Breaks cycles in `X64ParallelCopy` via `x64_emit_parallel_copies_in_arena` using `REG_R11` scratch (`AXS-RA-021`).
     - Rematerializes spilled constants (`X64_REMAT_CONST`) and stack addresses (`X64_REMAT_STACK_ADDR`) in place instead of allocating stack spill traffic (`AXS-RA-022`).
     - Colors non-overlapping spilled vreg intervals onto shared 8-byte-aligned stack slots via `X64StackSlotAllocator` (`AXS-RA-023`).

4. **Dynamic Callee-Saved Frame Lowering & Machine IR Verifier Integration (`compiler/target/x64/frame.ax`, `compiler/driver/opts.ax`)**:
   - Implemented `x64_frame_lower_baseline_in_arena` (`-O0` fast stack-slot-per-vreg baseline) and `x64_frame_lower_opt_in_arena` (`-O1`/`-O2` optimizing frame lowering).
   - Embedded validated metadata (`X64_FRAME_META_MAGIC`) in `X64FrameLayout.slot_offsets` so `x64_frame_callee_saved_mask`, `x64_frame_callee_saved_bytes`, `x64_frame_emit_prologue`, `x64_frame_emit_epilogue`, and `x64_verify_checked` dynamically push/pop only the callee-saved GPRs and save/restore only the callee-saved XMM registers (`XMM6`..`XMM15`) actually touched by the function while preserving 16-byte `RSP` alignment and `__chkstk` stack probing (`AXS-RA-024..025`).
   - Added `-O2` CLI flag recognition in `compiler/driver/opts.ax`.

## Files changed

- `compiler/driver/opts.ax`
- `compiler/target/x64/encode.ax`
- `compiler/target/x64/frame.ax`
- `compiler/target/x64/isel.ax`
- `compiler/target/x64/mod.ax`
- `tests/mc/regalloc/call_clobbers_diff.ax`
- `tests/mc/regalloc/call_clobbers_o2.ax`
- `tests/mc/regalloc/callee_saved_diff.ax`
- `tests/mc/regalloc/callee_saved_o2.ax`
- `tests/mc/regalloc/fixed_regs_diff.ax`
- `tests/mc/regalloc/fixed_regs_o2.ax`
- `tests/mc/regalloc/high_pressure_diff.ax`
- `tests/mc/regalloc/high_pressure_o2.ax`
- `tests/mc/regalloc/ra_pressure_mi.ax`
- `tests/mc/regalloc/ra_pressure_mi.mi`
- `tests/perf/baseline.csv`
- `tests/selfhost/backend/qa_backend_diff_lir_a.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_b.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax`
- `tests/selfhost/backend/qa_backend_edge.ax`
- `tests/selfhost/backend/qa_backend_unit.ax`
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
- `tests/selfhost/isel/qa_isel_diff_golden.ax.in`
- `tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax`
- `tests/selfhost/isel/qa_isel_instructions_and_abi.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`

## Performance & Code-Size Metrics

| Metric | Baseline (`-O0` / Pre-T063) | Optimizing (`-O1` / `-O2` Post-T063) | Improvement |
|---|---:|---:|---:|
| Stage 1 (`axiomc1.exe` `-O0`) vs Stage 2 (`axiomc2.exe` `-O1`) PE size | `16,180,736` bytes (`15.43 MB`) | `9,890,816` bytes (`9.43 MB`) | **-38.87%** (`-6,289,920` bytes) |
| Stage 2 (`axiomc2.exe` `-O1`) Pre-T063 vs Post-T063 PE size | `13,561,856` bytes (`12.93 MB`) | `9,890,816` bytes (`9.43 MB`) | **-27.07%** (`-3,671,040` bytes) |
| `tests/perf/bench/loop.ax` `build` pass latency (`baseline.csv`) | `38 ms` | `1.6 ms` | **23.75x faster** |
| Leaf function frame size (`test_linear_scan_ra_and_opt_frame`) | `88` bytes + `56` bytes callee pushes (`144` bytes) | `48` bytes + `0` bytes callee pushes (`48` bytes) | **-66.67% stack frame** |

## Verification

- `python tools/build_axiomc.py --out build-snap-T063/build --force`: `STAGE1 OK`, `STAGE2 (O1) OK`, `BUILD-AXIOMC OK` (`build-snap-T063/build/axiomc2.exe`, `9,890,816` bytes).
- `python tools/axtest.py mc/regalloc -j 1 --compiler build-snap-T063/build/axiomc2.exe`: `TOTAL 9 PASS 9 FAIL 0` (verifying `high_pressure`, `call_clobbers`, `fixed_regs`, `callee_saved`, and `ra_pressure_mi` across `[interp]`, `[native]` `-O0`, `[native-O1]` `-O1`, and `-O2`).
- `python tools/axtest.py selfhost/encode selfhost/isel selfhost/backend selfhost/driver selfhost/obj_link_driver -j 1 --compiler build-snap-T063/build/axiomc2.exe`: `PASS` across all regenerated selfhost suites (`WEAK-NATIVE 0` on `selfhost/isel`).
- `python tools/axtest.py mc/ diff/ run/ conformance/ -j 1 --compiler build-snap-T063/build/axiomc2.exe`: all 1,849 test cases pass (including `run/mono/qa_generic_enum_drop.ax` and `run/mono/qa_test_result_drop.ax`).
- Static gates:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T063`: `0` unlisted files, exit code `0`.
  - `python tools/gatecheck.py --no-run`: `MS-P1`..`MS-P10b PASS`.
  - `python tools/archcheck.py`: `192 files scanned, 0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0, COVERAGE OK`.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
