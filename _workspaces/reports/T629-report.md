# T629 Report — Register allocation, instruction selection & post-RA machine optimization conformance suite

## Summary

Implemented E15.8 (`T629`): the end-to-end conformance suite under `tests/conformance/p15/e15_8_regalloc_isel/` certifying `REQ-OPT-371` (*Late machine optimization does not define semantics*), `REQ-OPT-372` (*Post-RA Machine IR remains an inspectable IR prior to byte encoding*), and `SPEC-77` invariants (`AXS-RA-020..027`, `AXS-MCOPT-010..016`, `AXS-MCOPT-020..026`) across linear-scan register allocation, x86-64 instruction selection, branchless diamond if-conversion, and post-RA machine peephole optimization.

1. **White-Box Compiler Probe & Multi-Stage CLI Inspect Oracle (`e15_8_conformance.test`, `e15_8_conformance_oracle.py`, `e15_8_conformance_probe.ax.in`)**:
   - Compiles and executes `e15_8_conformance_probe.ax.in` directly against the live `compiler/backend/regalloc`, `compiler/target/x64/{isel,frame,verify,print,encode}`, and `compiler/backend/peephole` modules under both `-O0` and `-O2 --verify-each` (`E15_8_PROBE_OK stages=4`).
   - **Stage 1 (`AXS-RA-020..027`)**: Exercises live-range splitting across high-pressure multi-block loops (>20 live GPR values across all 13 allocatable GPRs), spill-slot reuse for disjoint intervals, coalescing of move-related vregs without fixed-register conflict, callee-saved preservation (`rbx`, `rsi`, `rdi`, `r12..r15`), `call` caller-saved clobber barriers (`rax`, `rcx`, `rdx`, `r8..r11`), fixed-register `idiv` (`rax`/`rdx`) and variable shift (`rcx`/`cl`) constraints, and non-0-byte / 16-byte-aligned Win64 frame sizing.
   - **Stage 2 (`AXS-MCOPT-010..016`)**: Certifies `lea` scaled-index + displacement folding (`base + idx * 8 + 16`), 32-bit signed immediate folding vs 64-bit `movimm64`, constant multiply (`*3`, `*5`, `*9`, power-of-two `shl`) and unsigned/signed magic-number division/remainder lowering without `idiv`, branchless diamond `cmovcc`/`setcc` selection on pure arms (`cost <= 6`), and strict rejection of diamond if-conversion when an arm contains trapping `idiv`, `call`, or store side effects (`AXS-MCOPT-014`).
   - **Stage 3 (`AXS-MCOPT-020..026`, `REQ-OPT-372`)**: Certifies post-RA redundant self-move removal (`mov r, r`), identity-arithmetic elimination (`add/sub/or/xor/shl/shr/sar r, 0`), dead overwrite elimination, store-reload forwarding across identical stack slots with aliasing/call barriers, `cmp r, 0` -> `test r, r` and `mov r, 0` -> `xor r, r` gated by sound `EFLAGS` liveness (`x64_flags_are_dead_after` across fallthrough blocks and variable `cl` shifts), jump-to-jump threading, post-peephole `x64_verify_checked` physical-register cleanliness (`0` surviving virtual registers), and deterministic textual Machine IR printing (`x64_print_func`) prior to `x64_encode` byte emission (`REQ-OPT-372`).
   - **Stage 4 & CLI Driver Oracle (`REQ-OPT-371`, `REQ-OPT-372`)**: Invokes `axiomc inspect --emit=lir`, `--emit=mi`, and `--emit=mc` across `-O0`, `-O1`, and `-O2` to verify: (a) deterministic inspectability of post-RA physical-register Machine IR (`--emit=mi`) as a distinct representation prior to encoded machine bytes (`--emit=mc`) with zero virtual `%vN` operands and byte-identical repeat runs; (b) `-O0` unoptimized baseline policy vs `-O1`/`-O2` optimized lowering (`lea`, magic multiply, `cmovcc`/`setcc`, peephole cleanup); (c) `lea` exclusion on checked `i64` `+` (`AXS-MCOPT-016` — `add` + `jo` overflow check preserved); and (d) exact byte-for-byte stdout, stderr, and exit-code parity across MIR interpreter (`run`), `-O0`, `-O1`, `-O2`, and `-O2 --verify-each` native executables on both positive workloads and runtime trap workloads.

2. **Differential (`-O0` vs MIR Interpreter) & `-O2 --verify-each` Native Parity Suite (`REQ-OPT-371`)**:
   - **Positive Conformance Workloads (5 `diff` + 5 `-O2 --verify-each` `run` fixtures = 15 `axtest` entries)**:
     - `{,o2_}regalloc_extreme_pressure_spills.ax`: 24 simultaneous live `i64` values across nested loops, conditional merges, and helper calls (`RA_PRESSURE_TOTAL=277924`).
     - `{,o2_}fixed_reg_clobbers_div_shift_abi.ax`: Simultaneous variable shifts (`rcx`), runtime signed/unsigned division/remainder (`rax`/`rdx`), and 8-argument Win64 calls (`FIXED_CLOBBER_TOTAL=1901505804`).
     - `{,o2_}isel_lea_const_divmul_casts.ax`: Complex `base + index * scale + disp` `lea` addressing, boundary immediates, constant multiply/divide/remainder (`INT64_MIN` / `UINT64_MAX` edges), and cascading integer width casts (`i8`/`u8`/`i16`/`u16`/`i32`/`u32`/`i64`/`u64`) (`ISEL_TOTAL=73938`).
     - `{,o2_}if_conv_cmov_setcc_nospeculate.ax`: Branchless `cmovcc`/`setcc` diamonds alongside guarded division, null-pointer load, and out-of-bounds slice indexing arms that must never be speculated (`IFCONV_TOTAL=4182`).
     - `{,o2_}peephole_eflags_barriers_utf8_io.ax`: Post-RA peephole `EFLAGS` liveness across fallthrough jumps and `cl` shifts, store-reload forwarding with pointer-alias barriers, and UTF-8 string output (`PEEPHOLE_UTF8=Xin chào E15.8 αβγ 42`, `PEEPHOLE_TOTAL=5259`).
   - **Negative / Trap Preservation Conformance Workloads (5 `diff` + 5 `-O2 --verify-each` `run` fixtures = 15 `axtest` entries, `exit: 101`)**:
     - `{,o2_}trap_checked_add_lea_exclusion_i64.ax`: Checked `i64` addition overflow (`9223372036854775800 + idx * 4 + 16`) must trap rather than silently wrapping via `lea` (`AXS-MCOPT-016`).
     - `{,o2_}trap_checked_sub_underflow_u64.ax`: Checked `u64` subtraction underflow (`3u64 - 4u64`) preserved under `-O2` constant/immediate folding.
     - `{,o2_}trap_checked_mul_overflow_i64.ax`: Checked `i64` multiplication overflow (`* 9`) must trap rather than silently wrapping via `lea r, [r + r*8]`.
     - `{,o2_}trap_div_by_zero_guarded_arm_taken.ax`:Taken runtime division-by-zero arm traps identically across interpreter, `-O0`, and `-O2 --verify-each`.
     - `{,o2_}trap_signed_min_div_neg1_i64.ax`: `i64::MIN / -1` signed division overflow traps identically across interpreter, `-O0`, and `-O2 --verify-each`.

## Files changed

- `tests/conformance/p15/e15_8_regalloc_isel/e15_8_conformance.test`
- `tests/conformance/p15/e15_8_regalloc_isel/e15_8_conformance_oracle.py`
- `tests/conformance/p15/e15_8_regalloc_isel/e15_8_conformance_probe.ax.in`
- `tests/conformance/p15/e15_8_regalloc_isel/fixed_reg_clobbers_div_shift_abi.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/if_conv_cmov_setcc_nospeculate.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/isel_lea_const_divmul_casts.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_fixed_reg_clobbers_div_shift_abi.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_if_conv_cmov_setcc_nospeculate.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_isel_lea_const_divmul_casts.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_peephole_eflags_barriers_utf8_io.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_regalloc_extreme_pressure_spills.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_trap_checked_add_lea_exclusion_i64.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_trap_checked_mul_overflow_i64.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_trap_checked_sub_underflow_u64.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_trap_div_by_zero_guarded_arm_taken.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/o2_trap_signed_min_div_neg1_i64.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/peephole_eflags_barriers_utf8_io.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/regalloc_extreme_pressure_spills.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/trap_checked_add_lea_exclusion_i64.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/trap_checked_mul_overflow_i64.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/trap_checked_sub_underflow_u64.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/trap_div_by_zero_guarded_arm_taken.ax`
- `tests/conformance/p15/e15_8_regalloc_isel/trap_signed_min_div_neg1_i64.ax`

## Verification

- **Stage-2 Bootstrap Build (`build-snap-T629`)**:
  - `python build-snap-T629/tools/build_axiomc.py --root build-snap-T629 --out build-snap-T629/build --axiom0 build-snap-T629/build/axiom0.exe --stage 2`
  - `BUILD-AXIOMC OK`: `build-snap-T629/build/axiomc2.exe` (`size=5,833,216` bytes, `sha256=e6427fba4cb802a25fdd21185c4f57b9daeba14554f503ed0e99522dcda86912`)
- **E15.8 Conformance Suite (`build-snap-T629`, `-j 1`)**:
  - `cd build-snap-T629 && python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 1 -v conformance/p15/e15_8_regalloc_isel`
  - **TOTAL 31 PASS 31 FAIL 0 SKIP 0 XFAIL 0 (`WEAK-NATIVE 0`)** — covers `e15_8_conformance.test` (4-stage live backend probe + `--emit={lir,mi,mc}` `-O0`/`-O1`/`-O2` inspect oracle + multi-opt runtime parity matrix), 5 positive `diff` tests, 5 positive `-O2 --verify-each` (`[interp]` + `[native]`) tests, 5 trap `diff` tests, and 5 trap `-O2 --verify-each` (`[interp]` + `[native]`) tests.
- **P15 Conformance, Machine Code, Optimizer & Sentinel Regressions (`build-snap-T629`, `-j 1`)**:
  - `cd build-snap-T629 && python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 1 conformance/p15/ mc/frame mc/isel mc/isel_peephole mc/regalloc opt/const_fold_run.ax opt/qa_dce_run.ax opt/qa_edge_cases_run.ax run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax`
  - **TOTAL 123 PASS 118 FAIL 0 SKIP 5 XFAIL 0** (`0` failures across all P15 conformance suites, `mc/*`, `opt/*`, and intrinsic sentinels).
- **Empirical Mutation Proof (`build-snap-T629` snapshot only, cleanly restored)**:
  - Temporarily mutated `build-snap-T629/compiler/target/x64/isel.ax:2467` (`addr.disp` -> `addr.disp + 1` in `isel_emit_addr_mem_op`) and `build-snap-T629/tests/conformance/p15/e15_8_regalloc_isel/o2_isel_lea_const_divmul_casts.ax` (`ISEL_TOTAL=73938` -> `73939`):
    - `FAIL conformance/p15/e15_8_regalloc_isel/e15_8_conformance.test`: `e15_8_probe -O0 failed with exit code 202` (caught live `isel.ax` `lea` displacement defect).
    - `FAIL conformance/p15/e15_8_regalloc_isel/o2_isel_lea_const_divmul_casts.ax [native]`: `stdout differs at byte 70` (caught native `-O2 --verify-each` output mismatch).
  - Immediately restored `build-snap-T629` via `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T629` (`HEAD 1d10259 + 23 changed, 0 deleted file(s) of T629`) and re-ran `conformance/p15/e15_8_regalloc_isel`: **TOTAL 31 PASS 31 FAIL 0 (`WEAK-NATIVE 0`)**.
- **Architecture, Requirement Coverage, Line Endings & Staging Gates**:
  - `python build-snap-T629/tools/archcheck.py`: `archcheck: 193 files scanned, 0 violations` (exit `0`).
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK`, `gaps: 0` (exit `0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit `0`).
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T629`: `0 REFUSED`, all 23 suite files + `_workspaces/reports/T629-report.md` LF-only (`0` `\r` bytes).

STATUS: COMPLETE round=0
