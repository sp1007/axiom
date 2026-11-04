# T604 Report — E15.1 OptIR SSA/MemorySSA, Pass-Contract Verifier & Scalar Optimization Conformance Suite

## Summary of Deliverables

1. **Differential Conformance Fixtures (`--interp` vs AOT `-O0` vs AOT `-O1` + Direct AOT `-O2 --verify-each` Companions)**:
   - Added 5 positive differential conformance programs (`// test: diff`, `// flags: --verify-each`, byte-exact `// stdout:`) paired with 5 direct `-O2 --verify-each` native run wrappers (`o2_*.ax`, `// test: run`, `// input: ...`, `// flags: -O2 --verify-each`):
     - `memssa_phi_sroa_diamond_loop.ax` / `o2_memssa_phi_sroa_diamond_loop.ax`: Monomorphic nested-diamond + loop CFG exercising `OptPhi` construction, `MemorySSA` `LiveOnEntry` / `MemoryDef` / `MemoryUse` / `MemoryPhi` joins, stack aggregate scalarization, and `--emit=optir` / `--emit=memssa` determinism (`MEMSSA_SROA_CFG=368\n`).
     - `cfg_ssa_memssa_sccp_gvn.ax` / `o2_cfg_ssa_memssa_sccp_gvn.ax`: Complex diamond/loop CFG joins, Wegman-Zadeck SCCP dead-branch pruning, dominator-scoped GVN & commutative CSE, and `NoAlias` `view`/`mut_view` store-to-load forwarding vs `UnknownAlias` raw-pointer reload preservation (`CFG_TOTAL=1892\n`).
     - `abstraction_erasure_sroa_generics.ax` / `o2_abstraction_erasure_sroa_generics.ax`: Zero-cost abstraction erasure across nested affine structs, generic wrapper monomorphization, and enum discriminant state-machine loops (`ABSTRACTION_TOTAL=345\n`).
     - `arith_wrapping_vs_checked_identities.ax` / `o2_arith_wrapping_vs_checked_identities.ax`: Modular `wrapping_add` / `wrapping_sub` / `wrapping_mul` group cancellation (`i8`, `i32`, `u8`, `u32`, `i64`, `u64` at `MIN`/`MAX` boundaries) vs guard-proven checked arithmetic (`ARITH_TOTAL=260\n`).
     - `effects_drop_clone_io_barriers_zeroize.ax` / `o2_effects_drop_clone_io_barriers_zeroize.ax`: Canonical UTF-8 Vietnamese stdout (`GREETING=Xin chào thế giới`), ordered I/O barriers, explicit observable `Clone` side effects, deterministic reverse-LIFO scope & nested-field `Drop` ordering, `black_box`, `volatile_load`/`volatile_store`, atomic load/store/RMW/fence preservation, and unread stack secret buffer zeroization (`EFFECTS_DONE=69\n`).

2. **Panic & Checked-Overflow Trap Conformance Fixtures (`exit: 101` Across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`)**:
   - Added 7 runtime panic/trap differential fixtures (`// test: diff`, `// flags: --verify-each`, `// exit: 101`) paired with 7 direct `-O2 --verify-each` native run wrappers (`o2_trap_*.ax`):
     - `trap_checked_add_overflow_cancel_i32.ax` / `o2_trap_checked_add_overflow_cancel_i32.ax`: Proves `(i32.MAX + 1) - 1` traps (`exit: 101`) rather than cancelling to `i32.MAX`.
     - `trap_checked_dead_overflow_dce_i64.ax` / `o2_trap_checked_dead_overflow_dce_i64.ax`: Proves unused checked `i64.MAX + 1` traps (`exit: 101`) rather than being eliminated by DCE.
     - `trap_checked_sub_underflow_u64.ax` / `o2_trap_checked_sub_underflow_u64.ax`: Proves unsigned `0u64 - 1u64` checked underflow traps (`exit: 101`).
     - `trap_checked_mul_overflow_i16.ax` / `o2_trap_checked_mul_overflow_i16.ax`: Proves subword signed `300i16 * 300i16` checked multiplication overflow traps (`exit: 101`).
     - `trap_div_by_zero_self_div_i32.ax` / `o2_trap_div_by_zero_self_div_i32.ax`: Proves `x / x` with runtime `x == 0` traps (`exit: 101`) rather than simplifying to `1`.
     - `trap_signed_min_div_neg1_i8.ax` / `o2_trap_signed_min_div_neg1_i8.ax`: Proves subword `(-128i8) / (-1i8)` traps (`exit: 101`).
     - `trap_signed_min_rem_neg1_i64.ax` / `o2_trap_signed_min_rem_neg1_i64.ax`: Proves `i64.MIN % (-1i64)` traps (`exit: 101`).

3. **Live 4-Module E15.1 Optimizer Integration Oracle (`e15_1_conformance.test` + `e15_1_conformance_oracle.py` + `e15_1_conformance_probe.ax.in`)**:
   - Compiles and executes the live `compiler.opt.optir`, `compiler.opt.effects`, `compiler.opt.passmgr`, and `compiler.opt.scalar` modules together as standalone AOT native executables under `-O0`, `-O1`, and `-O2 --verify-each`, verifying:
     - **Stage 1 (`OptIR` & `MemorySSA`)**: Cooper-Harvey-Kennedy `DominatorTree` (`idom`) & dominance frontiers (`df`), `PASS_MEM2REG_SROA` scalarization of non-escaping aggregates to `OptPhi` nodes while retaining address-taken locals as `OPT_LOCAL_MEMORY`, `MemorySSA` `LiveOnEntry` / `MemoryDef` / `MemoryUse` / `MemoryPhi` integrity, `optir_alias_query` (`NoAlias` vs `UnknownAlias`), `optir_verify_body`, and round-trip `optir_lower_to_mir` + `verify_mir`.
     - **Stage 2 (`EffectInfo` & `CallGraph`)**: Interprocedural Tarjan SCC fixed-point propagation (`Pure`, `ReadsMem`, `MayPanic`, recursive cycle termination, indirect-call fail-closed conservativeness) and instruction-level `effect_can_dce_inst` / `effect_can_cse_inst` contracts.
     - **Stage 3 (`PassManager` & Verifier Rollback)**: `CERTAINTY_POSSIBLE` candidate rejection (`passmgr_evaluate_candidate`), injected postcondition corruption triggering `AX_OPT_POSTCOND_FAILED` + deterministic pre-pass snapshot rollback (`PASS_EXEC_ROLLED_BACK`), invalid-analysis consumption rejection (`AX_OPT_INVALID_ANALYSIS`), `PassRunReport` JSON trace emission, and byte-identical deterministic execution across repeated runs.
     - **Stage 4 (`Scalar` Pipeline & Barrier Contracts)**: SCCP dead-branch pruning & non-folding of trapping `div-by-zero`/`overflow`, `InstCombine` modular wrapping cancellation vs fail-closed checked `(x + y) - y` and `x / x` rejection, `NaN`/`-0.0` `has_fp_hazard` non-rewrite, `NoAlias` store-to-load forwarding vs `UnknownAlias` retention, pure-call CSE vs explicit `Clone` retention, and non-elimination of `black_box`, `volatile_load`, `volatile_store`, `atomic`, and `zeroize` barriers across `PASS_MEM2REG_SROA` and `scalar_run_pipeline`.
   - Also independently compiles and runs every positive and trap `.ax` fixture across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`, verifies deterministic `inspect --emit=optir` and `inspect --emit=memssa` dumps across `-O0`/`-O1`/`-O2 --verify-each`, and checks fail-closed `build` rejection on `tests/verify/unverified_read.mir`.

## Requirement Coverage

| Requirement | Verification Coverage |
| --- | --- |
| `REQ-OPT-037` | Standalone AOT native `.exe` compilation by default verified across `-O0`, `-O1`, and `-O2 --verify-each` in `e15_1_conformance_oracle.py`, 12 `o2_*.ax` native tests, and 12 `diff` tests (`0 WEAK-NATIVE`). |
| `REQ-OPT-038` | Native AOT executables run directly on the Windows x64 host OS without any VM or interpreter runtime across all 24 `.ax` conformance tests and the 3 `-O0`/`-O1`/`-O2` `e15_1_probe` binaries. |
| `REQ-OPT-039` | Unobservable language abstractions (wrapper structs, affine tuple/struct temporaries, generic monomorphized functions, enum state-machine tags) scalarized and erased (`abstraction_erasure_sroa_generics.ax`, `memssa_phi_sroa_diamond_loop.ax`, `e15_1_conformance_probe.ax.in` Stages 1 & 4). |
| `REQ-OPT-040` | Zero-cost abstraction verified via `PASS_MEM2REG_SROA` SSA promotion and `ScalarOptStats` confirming concrete constant folds, dead-branch pruning, GVN/CSE eliminations, `NoAlias` store-to-load forwarding, pure-call CSE, and dead-store/copy elision (`e15_1_conformance_probe.ax.in`, `cfg_ssa_memssa_sccp_gvn.ax`). |
| `REQ-OPT-041` | Observable semantics strictly preserved under optimization: UTF-8 I/O (`"Xin chào thế giới"`), explicit `Clone`, reverse-LIFO `Drop` ordering, `black_box`, `volatile`, atomics, unread secret `zeroize` (`effects_drop_clone_io_barriers_zeroize.ax`), modular vs checked integer semantics (`arith_wrapping_vs_checked_identities.ax`), `NaN`/`-0.0` FP hazard rejection, and all 7 exit-`101` overflow/div-by-zero panic traps (`trap_*.ax`). |
| `REQ-OPT-343` | Byte-exact stdout and exit-code equivalence verified across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each` for all 5 positive fixtures, all 7 panic/trap fixtures, and the 3 `-O0`/`-O1`/`-O2` builds of `e15_1_conformance_probe` (`e15_1_conformance.test` + `axtest.py`). |

## Verification Evidence

- **Snapshot Stage-1 & Stage-2 Compiler Build (`build-snap-T604`)**:
  - `cmake -S build-snap-T604/bootstrap/axiom0 -B build-snap-T604/build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build-snap-T604/build --target axiom0`
  - `python build-snap-T604/tools/build_axiomc.py --out build-snap-T604/build`: `BUILD-AXIOMC OK` (`build-snap-T604/build/axiomc2.exe`, `size=10997760`, `sha256=62e71e52554ac920059d8e946eddecee532e4be09179bf2ab6452024397f2d9f`).
- **E15.1 Conformance Suite (`-j 1`)**:
  - `python build-snap-T604/tools/axtest.py --root build-snap-T604 --compiler build-snap-T604/build/axiomc2.exe --exclude-requires axiom0-internal -j 1 conformance/p15/e15_1_optir_ssa` -> `WEAK-NATIVE 0`, `TOTAL 37 PASS 37 FAIL 0 SKIP 0 XFAIL 0`.
- **Empirical Native Liveness & Mutation Check (`build-snap-T604` ONLY, Restored Cleanly)**:
  - Mutated `build-snap-T604/compiler/opt/scalar/mod.ax:393` (`INTRINSIC_SEM_ZEROIZE` -> `INTRINSIC_SEM_NONE`) and `build-snap-T604/tests/conformance/p15/e15_1_optir_ssa/effects_drop_clone_io_barriers_zeroize.ax:61` (`ScopeGuard { id: 10 }` -> `ScopeGuard { id: 99 }`), then ran:
    `python build-snap-T604/tools/axtest.py --root build-snap-T604 --compiler build-snap-T604/build/axiomc2.exe --exclude-requires axiom0-internal -j 1 -v conformance/p15/e15_1_optir_ssa/e15_1_conformance.test conformance/p15/e15_1_optir_ssa/effects_drop_clone_io_barriers_zeroize.ax conformance/p15/e15_1_optir_ssa/o2_effects_drop_clone_io_barriers_zeroize.ax`
    -> `TOTAL 4 PASS 0 FAIL 4 SKIP 0 XFAIL 0` (`e15_1_conformance.test` failed natively at `e15_1_probe -O0` exit code `171` on zeroize DCE assertion; `effects_drop_clone_io_barriers_zeroize.ax [diff]` and `o2_effects_drop_clone_io_barriers_zeroize.ax [native]` failed on stdout `DROP=10` vs `DROP=99`).
  - Restored `build-snap-T604` via `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T604` and re-verified `conformance/p15/e15_1_optir_ssa` -> `WEAK-NATIVE 0`, `TOTAL 37 PASS 37 FAIL 0 SKIP 0 XFAIL 0`.
- **Optimizer, Intrinsics, MIR, Verifier, Differential & Conformance Regression Suites (`-j 1`)**:
  - `python build-snap-T604/tools/axtest.py --root build-snap-T604 --compiler build-snap-T604/build/axiomc2.exe --build-dir build-snap-T604/build --exclude-requires axiom0-internal -j 1 run/opt_scalar run/opt_passmgr run/optir_ssa selfhost/opt selfhost/bundles_current.test run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax opt/const_fold_run.ax opt/qa_dce_run.ax opt/qa_edge_cases_run.ax` -> `TOTAL 65 PASS 65 FAIL 0 SKIP 0 XFAIL 0`.
  - `python build-snap-T604/tools/axtest.py --root build-snap-T604 --compiler build-snap-T604/build/axiomc2.exe --build-dir build-snap-T604/build --exclude-requires axiom0-internal -j 1 mir/ verify/ diff/ conformance/` -> `TOTAL 424 PASS 423 FAIL 0 SKIP 1 XFAIL 0`.
- **Architecture, Traceability, Line-Ending & Scope Gates**:
  - `python build-snap-T604/tools/archcheck.py` -> `archcheck: 193 files scanned, 0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `requirements: 32308`, `gaps: 0`, `COVERAGE OK`.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T604` -> exit `0`, `0 REFUSED`, LF-only (`0` `\r` bytes) across all 27 test files and `_workspaces/reports/T604-report.md`.

## Files changed
- tests/conformance/p15/e15_1_optir_ssa/abstraction_erasure_sroa_generics.ax
- tests/conformance/p15/e15_1_optir_ssa/arith_wrapping_vs_checked_identities.ax
- tests/conformance/p15/e15_1_optir_ssa/cfg_ssa_memssa_sccp_gvn.ax
- tests/conformance/p15/e15_1_optir_ssa/e15_1_conformance.test
- tests/conformance/p15/e15_1_optir_ssa/e15_1_conformance_oracle.py
- tests/conformance/p15/e15_1_optir_ssa/e15_1_conformance_probe.ax.in
- tests/conformance/p15/e15_1_optir_ssa/effects_drop_clone_io_barriers_zeroize.ax
- tests/conformance/p15/e15_1_optir_ssa/memssa_phi_sroa_diamond_loop.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_abstraction_erasure_sroa_generics.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_arith_wrapping_vs_checked_identities.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_cfg_ssa_memssa_sccp_gvn.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_effects_drop_clone_io_barriers_zeroize.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_memssa_phi_sroa_diamond_loop.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_trap_checked_add_overflow_cancel_i32.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_trap_checked_dead_overflow_dce_i64.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_trap_checked_mul_overflow_i16.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_trap_checked_sub_underflow_u64.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_trap_div_by_zero_self_div_i32.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_trap_signed_min_div_neg1_i8.ax
- tests/conformance/p15/e15_1_optir_ssa/o2_trap_signed_min_rem_neg1_i64.ax
- tests/conformance/p15/e15_1_optir_ssa/trap_checked_add_overflow_cancel_i32.ax
- tests/conformance/p15/e15_1_optir_ssa/trap_checked_dead_overflow_dce_i64.ax
- tests/conformance/p15/e15_1_optir_ssa/trap_checked_mul_overflow_i16.ax
- tests/conformance/p15/e15_1_optir_ssa/trap_checked_sub_underflow_u64.ax
- tests/conformance/p15/e15_1_optir_ssa/trap_div_by_zero_self_div_i32.ax
- tests/conformance/p15/e15_1_optir_ssa/trap_signed_min_div_neg1_i8.ax
- tests/conformance/p15/e15_1_optir_ssa/trap_signed_min_rem_neg1_i64.ax

## Status
STATUS: COMPLETE round=0
