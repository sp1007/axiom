STATUS: COMPLETE round=1

# T603 Report — E15.1 Unified Scalar Optimization Engine (SCCP, GVN, CSE, DCE & Algebraic Simplification)

## Summary of Changes

1. **Semantic Intrinsic Classification & Statistics (`compiler/opt/scalar/mod.ax`)**:
   - Implemented deterministic intrinsic semantic contract classifiers (`scalar_classify_inst_intrinsic`, `scalar_classify_call_intrinsic`) distinguishing `INTRINSIC_SEM_WRAPPING_ARITH`, `INTRINSIC_SEM_CHECKED_ARITH`, `INTRINSIC_SEM_BLACK_BOX`, `INTRINSIC_SEM_ZEROIZE`, `INTRINSIC_SEM_VOLATILE_LOAD`, `INTRINSIC_SEM_VOLATILE_STORE`, `INTRINSIC_SEM_ATOMIC`, `INTRINSIC_SEM_PURE_CALL`, and `INTRINSIC_SEM_EXPLICIT_CLONE_OR_IMPURE` (`REQ-OPT-011`, `REQ-OPT-306`, `REQ-OPT-351`, `REQ-OPT-352`, `REQ-OPT-353`).
   - Added `ScalarOptStats` (`scalar_stats_zero`) tracking constant folds, folded branches, pruned blocks, algebraic rewrites, GVN/CSE eliminations, forwarded loads, eliminated pure calls, DCE instruction/dead-store/move-copy eliminations, simplified CFG edges, and fail-closed rejected candidates.

2. **Wegman-Zadeck Sparse Conditional Constant Propagation & CFG Pruning (`scalar_run_sccp`)**:
   - Implemented joint CFG reachability and SSA lattice propagation (`Top` / `Const(c)` / `Overdefined`) over `OptBody`, evaluating `OptPhi` nodes strictly across executable incoming CFG edges (`AXS-OPT-040`).
   - Pinned barrier instructions (`OPT_FLAG_BARRIER`, `OPT_INST_BLACK_BOX`, `OPT_INST_ZEROIZE`, `OPT_INST_VOLATILE_LOAD`, `OPT_INST_VOLATILE_STORE`, `OPT_INST_ATOMIC`, `OPT_INST_DROP_FLAG`) and values carrying `OptRange.has_fp_hazard` (`REQ-OPT-397`) to `Overdefined`.
   - Enforced trap-faithful checked arithmetic and division/modulo-by-zero non-folding so checked overflow or zero-divisor operations never fold away observable panic traps (`REQ-OPT-014`, `REQ-OPT-363`, `REQ-OPT-364`).
   - Folded constant `OPT_TERM_BRANCH`, `OPT_TERM_SWITCH_INT`, and satisfied `OPT_TERM_ASSERT` terminators to `OPT_TERM_GOTO`, pruned unreachable blocks, and incrementally rebuilt `CFG`, `DominatorTree`, `OptPhi` incoming edges, and `MemorySSA` (`sc_prune_unreachable_and_rebuild_cfg_ssa`, `AXS-OPT-013`, `AXS-OPT-045`).

3. **Overflow-Faithful & Float-Hazard-Safe Algebraic Simplification (`scalar_run_inst_combine`)**:
   - Implemented commutative constant-to-RHS canonicalization, `OPT_INST_CHECKED_BINOP` (`Overflows`) constant/identity folding, discrete identities (`x + 0`, `x - 0`, `x * 1`, `x * 0`, `x & 0`, `x & ~0`, `x | 0`, `x ^ 0`, `x == x`, `x != x`, `!!b`, `~~x`, identity casts), and dominator-safe MIR scalar copy propagation (`AXS-OPT-041`).
   - Distinguished modular `OPT_INST_WRAPPING_BINOP` cancellation/reassociation (`(x +w y) -w y -> x`, `(x -w y) +w y -> x`, `(x +w c1) +w c2 -> x +w (c1 +w c2)`) from checked `OPT_INST_BINOP` (`(x + y) - y`), gating checked cancellation strictly on `CERTAINTY_PROVEN` `PROP_NO_OVERFLOW` and `x / x -> 1` / `x % x -> 0` strictly on `CERTAINTY_PROVEN` `PROP_NON_ZERO` via `passmgr_evaluate_candidate` (`0165 §8-9`, `REQ-OPT-014`, `REQ-OPT-363`, `REQ-OPT-364`).
   - Degraded `OptRange.has_fp_hazard` (`NaN` / `-0.0`) rewrites to `CERTAINTY_POSSIBLE` so `passmgr_evaluate_candidate` fails closed (`REQ-OPT-397`), while preserving unique SSA `result` definitions across `sc_rewrite_inst_to_copy_local`.

4. **Dominator-Scoped GVN, Commutative CSE, `MemorySSA` Store-to-Load Forwarding & Pure-Call CSE (`scalar_run_gvn_cse`)**:
   - Implemented recursive `DominatorTree`-scoped value numbering with deterministic ascending `OptBbId` traversal, propagating dominating `assert(!Overflows(op, a, b))` `NoOverflow` facts (`AXS-OPT-013`, `AXS-OPT-042`).
   - Eliminated redundant direct and commutative scalar expressions only when the dominating MIR scalar destination local is unclobbered along all paths (`sc_mir_local_clobbered_on_path`).
   - Implemented `MemorySSA`-walked store-to-load forwarding and redundant load CSE across `NoAlias` `mut_view<T>` and stack stores while failing closed on `UnknownAlias` raw pointers, calls, and barriers (`AXS-OPT-022`, `AXS-OPT-043`, `REQ-OPT-339`).
   - Eliminated redundant `INTRINSIC_SEM_PURE_CALL` terminators proven pure via `EffectCallTable` while preserving explicit `Clone` and impure calls (`REQ-OPT-306`, `REQ-OPT-351`).

5. **Effect-Aware Dead Code, Dead Store & Move/Copy Elision (`scalar_run_dce`, `scalar_run_cfg_simplify`, `scalar_run_pipeline`)**:
   - Implemented fixed-point dead `OptPhi` pruning, backward dead pure instruction elimination, `MemorySSA` `PROP_DEAD_STORE` overwrite/unread-local store elimination, `Drop`-safe `Copy`/`Move` temporary elision (`REQ-OPT-304`, `REQ-OPT-305`), and orphaned `StorageLive`/`StorageDead` cleanup (`AXS-OPT-044`).
   - Strictly preserved `OPT_INST_BLACK_BOX`, `OPT_INST_ZEROIZE`, `OPT_INST_VOLATILE_LOAD`, `OPT_INST_VOLATILE_STORE`, `OPT_INST_ATOMIC`, `OPT_INST_DROP_FLAG`, and `OPT_TERM_DROP` (`REQ-OPT-011`, `REQ-OPT-351`, `REQ-OPT-352`, `REQ-OPT-353`).
   - Added `scalar_run_pass` (with `PassManager` pre-pass snapshotting, postcondition verification, and automatic rollback), `scalar_run_pipeline`, and `scalar_optimize_mir_body` (`AXS-OPT-030..034`, `AXS-OPT-046..047`).

6. **Differential & Direct Engine Test Suite (`tests/run/opt_scalar/`)**:
   - Added differential `.ax` fixtures, trap exit `101` preservation fixtures, and `opt_scalar_engine.test` (`opt_scalar_oracle.py` + `opt_scalar_probe.ax.in`) directly compiling and executing `compiler.opt.scalar` under `-O0`, `-O1`, and `-O2 --verify-each`, verifying differential outputs across `--interp`, `-O0`, `-O1`, and `-O2`, trap exit `101` preservation, UTF-8 Vietnamese + `Clone` + `Drop` + secure zeroization retention, and deterministic `--emit=optir` / `--emit=memssa` output.

## Round 1 Fixes

1. **Finding 1 — Subword signed (`i8`, `i16`, `i32`) `MIN / -1` and `MIN % -1` overflow & trap preservation (`compiler/opt/scalar/mod.ax`)**:
   - Added width-aware `sc_max_signed_pos_for_bits` (`0x7F`, `0x7FFF`, `0x7FFFFFFF`, `0x7FFFFFFFFFFFFFFF`), `sc_query_no_overflow_certainty_safe`, `sc_effect_infer_inst_safe`, and `sc_can_dce_inst_safe`.
   - For signed `MIR_BINOP_DIV` and `MIR_BINOP_REM` (`<= 64`-bit), `sc_query_no_overflow_certainty_safe` refuses to report `CERTAINTY_PROVEN` unless both operands are known constants that do not overflow (`sc_eval_checked_binop`), or the divisor is a known non-zero constant `!= opt_bit_mask(bits)` (`-1`), or the divisor carries a valid `OptRange` with `non_zero_certainty == CERTAINTY_PROVEN` and `hi <= sc_max_signed_pos_for_bits(bits)` (strictly non-negative, excluding all masked two's-complement negative encodings such as `0xFF`/`0xFFFF`/`0xFFFFFFFF`), or the dividend carries a valid `OptRange` strictly excluding signed `MIN`.
   - Wired `sc_query_no_overflow_certainty_safe` and `sc_can_dce_inst_safe` into `scalar_run_inst_combine` (`OPT_INST_CHECKED_BINOP` `overflows(...)`), `scalar_run_gvn_cse`, `sc_prove_dead_store`, `sc_mir_local_overwritten_before_read_in_block`, and `scalar_run_dce` so neither `overflows(x / -1)` nor dead signed subword `x / -1` / `x % -1` traps are folded or DCE-erased.

2. **Finding 2 — Loop-backedge clobber safety for `PureCall` CSE and `sc_resolve_copy_source_for_val` (`compiler/opt/scalar/mod.ax`)**:
   - Added `sc_local_any_clobber_in_body` and `sc_call_dest_clobbered_on_path(body, arena, call_b, cont_b, cur_b, cur_i, loc_v)`.
   - `sc_call_dest_clobbered_on_path` enforces `call_b != cont_b`, `opt_dominates(call_b, cur_b)`, and `opt_dominates(cont_b, cur_b)`, rejects reaching `call_b`'s `unwind_bb`, and traverses backward from `(cur_b, cur_i)` stopping only at `call_b` (rather than stopping early at `cont_b`), so any loop backedge `back_b -> cont_b` that mutates `call_dest` is visited and blocks forwarding/CSE.
   - Updated `scalar_run_gvn_cse` (`GVN_KIND_PURE_CALL` records `def_inst_idx = b_idx as u32` as `call_bb_v`) and `sc_resolve_copy_source_for_val` (`OPT_VAL_INST` call result, `OPT_VAL_PARAM` when `bb0.pred_count > 0` or clobbered in body, and `OPT_VAL_PHI`).

3. **Finding 3 — Memory-backed (`OPT_LOCAL_MEMORY`) / dereferenced non-`OPT_INST_STORE` writes & `MemorySSA` coherence (`compiler/opt/scalar/mod.ax`)**:
   - Added `sc_place_is_ssa_slot` (requiring unprojected `OPT_LOCAL_SCALAR` without address-taken uses anywhere in `OptBody`) and updated `sc_rewrite_inst_to_const` and `sc_rewrite_inst_to_copy_local` so folding or copy-rewriting an instruction whose destination `MirPlace` is memory-backed emits `OPT_INST_STORE` with `result = OPT_VALUE_NONE`.
   - Added `sc_region_clobbered_on_path` and wired it into both Store-to-Load Forwarding and Redundant Load Elimination in `scalar_run_gvn_cse`, rejecting forwarding whenever any intervening instruction, `orig_stmt` (`MIR_STMT_ASSIGN`, `MIR_STMT_DROP`, `StorageLive`, `StorageDead`), call destination/clobber, or barrier on any CFG path may alias the loaded `MemoryRegion`.
   - Refreshed `optir_compute_dom_frontier` + `optir_construct_memssa` at the end of `scalar_run_sccp`, `scalar_run_inst_combine`, `scalar_run_gvn_cse`, and `scalar_run_dce` whenever memory-affecting instructions change.

4. **Finding 4 — Independent `PROP_DEAD_STORE` validation across `&_x` / aliasing reads & scalar-only non-store DCE (`compiler/opt/scalar/mod.ax`)**:
   - Removed the unvalidated `passmgr_find_proven_property(..., PROP_DEAD_STORE, ...)` early bypass in `sc_prove_dead_store` (and unused `passmgr_find_proven_property` import) so every dead-store candidate is independently validated by `sc_prove_dead_store`.
   - Added `sc_mir_stmt_reads_aliasing_region` (`sc_mir_place_reads_aliasing_region`, `sc_mir_op_reads_aliasing_region`) and blocked dead-store elimination whenever any intervening instruction/statement takes `&_x` (`OPT_INST_ADDR_OF` / `MIR_RVALUE_REF`), reads an aliasing `MirPlace` (such as `copy (*_2)` inside any rvalue), or writes to an aliasing non-`OPT_INST_STORE` place; also required `!sc_local_addr_taken_anywhere` for unread-local store elimination.
   - Restricted non-`OPT_INST_STORE` scalar DCE in `scalar_run_dce` and intra-block overwrite DCE in `sc_mir_local_overwritten_before_read_in_block` to `sc_local_is_unprojected_scalar` and `!sc_local_addr_taken_anywhere`.

5. **Round 1 Regression Tests (`tests/run/opt_scalar/`)**:
   - Added MIR-level regression Blobs `7..11` (`ROUND1_REGRESSION_BLOBS`) in `opt_scalar_oracle.py` and `verify_round1_qa_regressions` in `opt_scalar_probe.ax.in` testing all 4 QA findings directly against `scalar_run_pass`, `scalar_run_pipeline`, and `scalar_optimize_mir_body` under `-O0`, `-O1`, and `-O2 --verify-each`.
   - Added positive differential fixture `round1_clobber_and_alias_regressions.ax` and runtime trap fixtures `subword_div_min_neg1_trap.ax` (`i8::MIN / -1`), `subword_div_i16_min_neg1_trap.ax` (`i16::MIN / -1`), and `subword_rem_min_neg1_trap.ax` (`i32::MIN % -1`), and wired all of them into `opt_scalar_oracle.py` (`POSITIVE_FIXTURES` and `TRAP_FIXTURES`) as well as `axtest.py`. Verified QA's `qa_boundary_scalar_clobbers.ax` passes across `[interp]`, `[native]`, and `[native-O1]`.

## Files changed

- `compiler/opt/scalar/mod.ax`
- `tests/run/opt_scalar/algebraic_checked_vs_wrapping.ax`
- `tests/run/opt_scalar/barriers_clone_drop_zeroize.ax`
- `tests/run/opt_scalar/checked_overflow_trap_preserved.ax`
- `tests/run/opt_scalar/gvn_cse_and_alias_forwarding.ax`
- `tests/run/opt_scalar/opt_scalar_engine.test`
- `tests/run/opt_scalar/opt_scalar_oracle.py`
- `tests/run/opt_scalar/opt_scalar_probe.ax.in`
- `tests/run/opt_scalar/round1_clobber_and_alias_regressions.ax`
- `tests/run/opt_scalar/sccp_dead_branch_and_phi.ax`
- `tests/run/opt_scalar/subword_div_i16_min_neg1_trap.ax`
- `tests/run/opt_scalar/subword_div_min_neg1_trap.ax`
- `tests/run/opt_scalar/subword_rem_min_neg1_trap.ax`

## Requirement Coverage

| Requirement | Implementation & Verification |
| --- | --- |
| `REQ-OPT-011` | `OPT_INST_BLACK_BOX` classified as `INTRINSIC_SEM_BLACK_BOX`, pinned `Overdefined` in SCCP, excluded from GVN/CSE & DCE (`barriers_clone_drop_zeroize.ax`, `opt_scalar_probe.ax.in`). |
| `REQ-OPT-014` | Checked integer and subword signed `MIN / -1` / `MIN % -1` overflow semantics preserved across SCCP, InstCombine, GVN/CSE, and DCE (`checked_overflow_trap_preserved.ax`, `subword_div_min_neg1_trap.ax`, `subword_div_i16_min_neg1_trap.ax`, `subword_rem_min_neg1_trap.ax`, `algebraic_checked_vs_wrapping.ax`). |
| `REQ-OPT-304` | Dead `Move` temporaries of `Copy`-safe non-`Drop` locals elided by `scalar_run_dce` while preserving `Drop` and memory-backed/address-taken locals (`opt_scalar_probe.ax.in`, `barriers_clone_drop_zeroize.ax`, `round1_clobber_and_alias_regressions.ax`). |
| `REQ-OPT-305` | Redundant `Copy` temporaries propagated and elided across `scalar_run_inst_combine` and `scalar_run_dce` with loop-backedge clobber protection (`opt_scalar_probe.ax.in`, `round1_clobber_and_alias_regressions.ax`). |
| `REQ-OPT-306` | Explicit `Clone` calls classified `INTRINSIC_SEM_EXPLICIT_CLONE_OR_IMPURE` and never CSE/DCE-eliminated; proven `INTRINSIC_SEM_PURE_CALL` CSE-eliminated only when destination local is unclobbered across all paths including loop backedges (`barriers_clone_drop_zeroize.ax`, `opt_scalar_probe.ax.in`, `qa_boundary_scalar_clobbers.ax`). |
| `REQ-OPT-339` | `NoAlias` `view`/`mut_view` and stack store-to-load forwarding in `scalar_run_gvn_cse`, failing closed on `UnknownAlias` raw pointers and intervening non-`OPT_INST_STORE` aliasing writes (`gvn_cse_and_alias_forwarding.ax`, `round1_clobber_and_alias_regressions.ax`, `opt_scalar_probe.ax.in`). |
| `REQ-OPT-351` | Intrinsic semantic contracts enforced uniformly across `scalar_classify_inst_intrinsic` and `scalar_classify_call_intrinsic` (`opt_scalar_probe.ax.in`). |
| `REQ-OPT-352` | `OPT_INST_ZEROIZE` (`INTRINSIC_SEM_ZEROIZE`) treated as non-removable memory barrier in `MemorySSA`, GVN, and DCE (`opt_scalar_probe.ax.in`). |
| `REQ-OPT-353` | Volatile/barrier secret buffer wiping retained even when buffer goes out of scope unread (`barriers_clone_drop_zeroize.ax`, `opt_scalar_probe.ax.in`). |
| `REQ-OPT-363` | Checked arithmetic identities (`(x + y) - y`) and subword signed `DIV`/`REM` overflow queries rejected unless `PROP_NO_OVERFLOW` is `CERTAINTY_PROVEN`; `x / x` gated on `CERTAINTY_PROVEN` `PROP_NON_ZERO` (`opt_scalar_probe.ax.in`, `checked_overflow_trap_preserved.ax`, `subword_div_min_neg1_trap.ax`). |
| `REQ-OPT-364` | `wrapping_add` / `wrapping_sub` / `wrapping_mul` (`OPT_INST_WRAPPING_BINOP`) simplified via modular group identities and constant reassociation (`algebraic_checked_vs_wrapping.ax`, `opt_scalar_probe.ax.in`). |

## Verification

- Stage-1 & Stage-2 self-host compiler build inside `build-snap-T603`:
  - `python build-snap-T603/tools/build_axiomc.py --root build-snap-T603 --out build-snap-T603/build`: `STAGE1 OK` (`17303552` bytes, `sha256=3a0011394e04002f`), `STAGE2 (O1) OK` (`10572800` bytes, `sha256=d4fd9b56148d874460905cfe94be7550d11802be676fea9b9605cbf8045af419`), `BUILD-AXIOMC OK`.
- Differential, trap, QA boundary & engine test suite in `tests/run/opt_scalar` (`-j 1`):
  - `python build-snap-T603/tools/axtest.py --compiler build-snap-T603/build/axiomc2.exe --root build-snap-T603 --build-dir build-snap-T603/build --exclude-requires axiom0-internal -j 1 --verbose run/opt_scalar`: `WEAK-NATIVE 0`, `TOTAL 31 PASS 31 FAIL 0 SKIP 0 XFAIL 0` (including `opt_scalar_engine.test`, `qa_boundary_scalar_clobbers.ax`, `round1_clobber_and_alias_regressions.ax`, `subword_div_min_neg1_trap.ax`, `subword_div_i16_min_neg1_trap.ax`, and `subword_rem_min_neg1_trap.ax`).
- Broader optimizer, `OptIR`, `PassManager`, intrinsics, MIR, verifier, and self-host optimizer suites (`-j 1`):
  - `python build-snap-T603/tools/axtest.py --compiler build-snap-T603/build/axiomc2.exe --root build-snap-T603 --build-dir build-snap-T603/build --exclude-requires axiom0-internal -j 1 --verbose run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax run/opt_passmgr run/optir_ssa selfhost/opt/ selfhost/bundles_current.test opt/const_fold_run.ax opt/qa_dce_run.ax opt/qa_edge_cases_run.ax`: `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0` (`0` weak in `run/opt_passmgr`, `run/optir_ssa`, `selfhost/opt`, and `run/intrinsics`).
  - `python build-snap-T603/tools/axtest.py --compiler build-snap-T603/build/axiomc2.exe --root build-snap-T603 --build-dir build-snap-T603/build --exclude-requires axiom0-internal -j 1 mir/ verify/`: `WEAK-NATIVE 0`, `TOTAL 96 PASS 95 FAIL 0 SKIP 1 XFAIL 0`.
- Repository gates:
  - `python build-snap-T603/tools/archcheck.py`: `archcheck: 193 files scanned, 0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `requirements: 32308`, `gaps: 0`, `COVERAGE OK`.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T603`: exit `0` (`0 REFUSED`).

STATUS: COMPLETE round=1
