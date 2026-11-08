# Phase 15 (`P15-optimizer-2-0`) Conformance Suite Index

This directory (`tests/conformance/p15/`) contains the end-to-end Phase 15 (**Optimizer 2.0**) conformance suite certifying all eight roadmap epics (`E15.1`–`E15.8`) in `spec/ROADMAP.md` §3 (`differential green at -O2; benchmark targets met and tracked in CI`), canonical specifications `spec/SPEC-70-optir-ssa-memoryssa.md` through `spec/SPEC-77-regalloc-machine-opt.md`, architecture invariants `INV-PIPE-006` through `INV-PIPE-013` and `INV-VEC-001` through `INV-VEC-003` in `spec/invariants.md`, and all 32 Phase 15 implementation/spec/QA tasks (`T063`, `T064`, `T600`–`T629`) gated by `T315`.

---

## 1. Epic & Canonical Specification Overview (`E15.1`–`E15.8`, `SPEC-70`–`SPEC-77`)

| Epic | Conformance Directory | Canonical Spec | Rule Range | Invariant IDs (`spec/invariants.md`) | Tasks (`32` total) | Core Exit Criteria |
|---|---|---|---|---|---|---|
| **`E15.1`** `OptIR`: SSA / `MemorySSA` | `tests/conformance/p15/e15_1_optir_ssa/` | `spec/SPEC-70-optir-ssa-memoryssa.md` | `AXS-OPT-001..047` | `INV-PIPE-008` | `T600`, `T601`, `T602`, `T603`, `T604` | Verified MIR → `OptIR` lowering (`optimizer.inference = None`), Cooper-Harvey-Kennedy `DominatorTree` & minimal `OptPhi` placement, `MemorySSA` (`LiveOnEntry`, `MemoryDef`, `MemoryUse`, `MemoryPhi`), 3-valued `Certainty` (`Proven`/`Possible`/`Unknown`) fail-closed `PassManager` contracts & transactional rollback, canonical `EffectInfo`, and overflow/barrier-faithful `SCCP`, `GVN`, `CSE`, `SROA`, and `DCE` |
| **`E15.2`** Alias & escape analysis, allocation promotion | `tests/conformance/p15/e15_2_alias_escape/` | `spec/SPEC-71-alias-escape-promotion.md` | `AXS-ALIAS-001..006`, `AXS-ESC-001..017` | `INV-PIPE-009` | `T605`, `T606`, `T607`, `T608` | 5-valued `AliasResult` (`NoAlias`, `MustAlias`, `PartialAlias`, `MayAlias`, `UnknownAlias`) derived from verified `view`/`mut_view` capabilities & allocation roots, `MemorySSA` store-to-load forwarding / `RLE` / `DSE`, 4-point `EscapeInfo` lattice (`NoEscape < ArgumentEscape < ReturnEscape < GlobalEscape`), `Box<T>`/closure/bounded-buffer stack & register promotion, `NRVO`, and address-observability barriers (`address_of`, `@at`, `volatile`) |
| **`E15.3`** Loops & bounds-check elimination | `tests/conformance/p15/e15_3_loops_bce/` | `spec/SPEC-72-loops-scev-bce.md` | `AXS-LOOP-001..018`, `AXS-BCE-001..006` | `INV-PIPE-010` | `T609`, `T610`, `T611`, `T612` | CFG natural loop discovery, `LoopSimplify` (`preheader`, single `latch`, dedicated exits) & `LCSSA`, overflow-faithful `SCEV` (`Checked`, `Wrapping`, `Saturating`, `ProvenNswNuw`), `RangeInfo` & proven `BCE` (`0 <= idx < len`) vs retained runtime bounds traps, `LICM` with zero-trip trap safety, IV strength reduction, peeling, unswitching, unrolling, versioning, and lazy iterator pipeline fusion |
| **`E15.4`** Inlining, specialization, devirtualization (+ copy propagation, `SROA`) | `tests/conformance/p15/e15_4_inline_specialize_devirt/` | `spec/SPEC-73-inlining-specialization-devirt.md` | `AXS-INL-001..035` | `INV-PIPE-011` | `T613`, `T064`, `T614`, `T615` | Tarjan `SCC` call-graph summary propagation, ownership-preserving copy/move propagation, deep `SROA` & caller `RVO`/`NRVO`, 2-stage `InlineLegality` vs `CostModel` (`@inline`, `@inline(always)`, `@inline(never)`), bounded `SpecializationKey` constant/closure specialization, 3-tier `dyn Trait` / fn-ptr devirtualization (`Exact`, `Guarded`, `RetainedDynamic`), and $O(1)$-stack tail-call optimization (`@tailcall`) |
| **`E15.5`** Auto-vectorization | `tests/conformance/p15/e15_5_autovec/` | `spec/SPEC-74-auto-vectorization.md` | `AXS-VEC-001..053` | `INV-VEC-001..003` | `T616`, `T617`, `T618`, `T619` | Annotation-free pre-LIR loop (`opt_loop_vec`) and straight-line `SLP` (`opt_slp_vec`) auto-vectorization, capability-disjoint (`mut_view` vs `view`) + `SCEV` dependence proving, associative reduction legality vs strict IEEE-754 FP order, scalar remainder epilogue (`N % VF`) across all trip counts, `TargetDesc` `SSE2` (`128`-bit) / `AVX2` (`256`-bit) `VectorCostModel` & `LIR` `Vec128`/`Vec256` lowering, and `Source → MIR → OptIR → LIR → Machine` remarks |
| **`E15.6`** `LTO` / whole-program / section GC / `PGO` | `tests/conformance/p15/e15_6_lto_pgo_gc/` | `spec/SPEC-75-lto-wpo-section-gc-pgo.md` | `AXS-LTO-001..030`, `AXS-PGO-001..016` | `INV-PIPE-012` | `T620`, `T621`, `T622`, `T623` | `--lto=off\|thin\|full` with `.axmeta` summaries, closed-world reachability (`@entry`, `@export`, FFI, reflection, `@at` roots), cross-module inlining/specialization/RTA devirtualization, generic monomorphization deduplication, linker `COMDAT` section GC & `Safe ICF` (`0xE9 jmp rel32` identity thunks), and deterministic `--pgo-gen` / `--pgo-use` where `Observed` profiles never override semantic legality |
| **`E15.7`** Performance contract | `tests/conformance/p15/e15_7_perf_contract/` | `spec/SPEC-76-performance-contract.md` | `AXS-PERF-001..044` | `INV-PIPE-013` | `T624`, `T625`, `T626` | Cross-profile semantic equivalence (`--interp`, `-O0`, `-O1`, `-O2`, `-Os`, `-Oz`, `--lto`, `--pgo-use`) with zero safe UB, 3D binary footprint (`FileSize`, `MappedSize`, `WorkingSet`), noise-free `--time-passes` & `--size-report` JSON telemetry orthogonal to binary determinism, 7 canonical `tools/bench` suites, and 9 hard CI budgets enforced by `tools/perf.py --check-budgets` |
| **`E15.8`** Register allocation (linear scan) & better instruction selection | `tests/conformance/p15/e15_8_regalloc_isel/` | `spec/SPEC-77-regalloc-machine-opt.md` | `AXS-RA-010..027`, `AXS-MCOPT-001..026` | `INV-PIPE-006`, `INV-PIPE-007` | `T627`, `T063`, `T628`, `T629` | RPO liveness & loop-weighted `LiveInterval`s, linear-scan register allocation with pre-colored fixed-reg constraints (`rcx` shifts, `rax`/`rdx` div/mul), copy coalescing, spill-slot coloring & callee-saved `FrameLayout` preservation, scaled `lea` & magic-multiply div/rem ISel, non-speculating branchless `cmovcc`/`setcc` if-conversion, `EFLAGS`-safe post-RA peepholes, and inspectable post-RA Machine IR (`--emit=mi`) |

---

## 2. All 32 Phase 15 Tasks (`T063`, `T064`, `T600`–`T629`) + Planning (`T215`) & Gate (`T315`)

| Task ID | Epic | Owner | Title & Scope Summary | Primary Verification Target |
|---|---|---|---|---|
| `T215` | Plan | `axiom-architect` | Plan phase P15 — Optimizer 2.0 (expand `E15.1`–`E15.8` into 32 tasks and map 411 `CATALOG.md` requirements) | `spec/ROADMAP.md`, `spec/requirements/CATALOG.md` |
| `T627` | `E15.8` | `axiom-architect` | Canonical `spec/SPEC-77-regalloc-machine-opt.md` (linear-scan RA, spill/reload, `FrameLayout`, ISel, `cmovcc`, post-RA peephole) | `spec/SPEC-77-regalloc-machine-opt.md` |
| `T063` | `E15.8` | `axiom-backend` | Linear-scan register allocation, move coalescing, spill/reload insertion, and callee-saved frame integration (`INV-PIPE-006`) | `tests/mc/regalloc` |
| `T628` | `E15.8` | `axiom-backend` | Better instruction selection (`lea` addressing, constant div/rem), branchless `cmovcc` if-conversion, and post-RA machine peepholes (`INV-PIPE-007`) | `tests/mc/isel_peephole` |
| `T629` | `E15.8` | `axiom-qa` | Register allocation, instruction selection & post-RA machine optimization conformance suite (`INV-PIPE-007`) | `tests/conformance/p15/e15_8_regalloc_isel` |
| `T600` | `E15.1` | `axiom-architect` | Canonical `spec/SPEC-70-optir-ssa-memoryssa.md` (`OptIR` SSA/`MemorySSA`, pass-manager legality contracts, observable semantics preservation) | `spec/SPEC-70-optir-ssa-memoryssa.md` |
| `T601` | `E15.1` | `axiom-semantics` | Verified MIR → `OptIR` lowering, dominance frontier, SSA `OptPhi` placement, `MemorySSA` construction, and 3-valued `Certainty` tracking (`INV-PIPE-008`) | `tests/run/optir_ssa` |
| `T602` | `E15.1` | `axiom-semantics` | `OptIR` Pass Manager, canonical `EffectInfo` inference, and transformation contract/proof verifier (`INV-PIPE-008`) | `tests/run/opt_passmgr` |
| `T603` | `E15.1` | `axiom-semantics` | Unified scalar optimization engine (`SCCP`, `GVN`, `CSE`, `DCE`, and overflow-faithful algebraic simplification; `INV-PIPE-008`) | `tests/run/opt_scalar` |
| `T604` | `E15.1` | `axiom-qa` | `OptIR` SSA/`MemorySSA`, pass-contract verifier & scalar optimization conformance suite (`INV-PIPE-008`) | `tests/conformance/p15/e15_1_optir_ssa` |
| `T605` | `E15.2` | `axiom-architect` | Canonical `spec/SPEC-71-alias-escape-promotion.md` (capability/provenance `AliasInfo`, `EscapeInfo` lattice, storage promotion rules) | `spec/SPEC-71-alias-escape-promotion.md` |
| `T606` | `E15.2` | `axiom-semantics` | Capability-aware `AliasInfo`, provenance disjointness, and `MemorySSA` store-to-load forwarding, `RLE` & `DSE` (`INV-PIPE-009`) | `tests/run/opt_alias` |
| `T607` | `E15.2` | `axiom-semantics` | Escape analysis (`NoEscape`/`ArgumentEscape`/`ReturnEscape`/`GlobalEscape`), heap-to-stack/register promotion, and `NRVO` (`INV-PIPE-009`) | `tests/run/opt_escape` |
| `T608` | `E15.2` | `axiom-qa` | Alias analysis, escape analysis & allocation promotion conformance suite (`INV-PIPE-009`) | `tests/conformance/p15/e15_2_alias_escape` |
| `T609` | `E15.3` | `axiom-architect` | Canonical `spec/SPEC-72-loops-scev-bce.md` (natural loops, `SCEV`, `RangeInfo`, `BCE`, `LICM`, and loop transformations) | `spec/SPEC-72-loops-scev-bce.md` |
| `T610` | `E15.3` | `axiom-semantics` | Natural loop discovery, canonicalization (`LoopSimplify` + `LCSSA`), overflow-faithful `SCEV`, and `RangeInfo` bounds-check elimination (`BCE`; `INV-PIPE-010`) | `tests/run/opt_bce` |
| `T611` | `E15.3` | `axiom-semantics` | `LICM`, induction strength reduction, loop unrolling/peeling/unswitching/versioning/fusion, and lazy iterator pipeline fusion (`INV-PIPE-010`) | `tests/run/opt_loops` |
| `T612` | `E15.3` | `axiom-qa` | Loop optimizations, `SCEV` & bounds-check elimination conformance suite (`INV-PIPE-010`) | `tests/conformance/p15/e15_3_loops_bce` |
| `T613` | `E15.4` | `axiom-architect` | Canonical `spec/SPEC-73-inlining-specialization-devirt.md` (call-graph inlining, `SROA`, `RVO`/`NRVO`, specialization, devirtualization, `TCO`) | `spec/SPEC-73-inlining-specialization-devirt.md` |
| `T064` | `E15.4` | `axiom-semantics` | Copy/move propagation, `SROA`, return-slot construction, and bottom-up `SCC` call-graph inlining (`INV-PIPE-011`) | `tests/opt2` |
| `T614` | `E15.4` | `axiom-semantics` | Interprocedural constant/closure call-site specialization, 3-tier `dyn Trait` devirtualization, and tail-call optimization (`INV-PIPE-011`) | `tests/run/opt_ipa_devirt` |
| `T615` | `E15.4` | `axiom-qa` | Inlining, specialization, devirtualization & `SROA` conformance suite (`INV-PIPE-011`) | `tests/conformance/p15/e15_4_inline_specialize_devirt` |
| `T616` | `E15.5` | `axiom-architect` | Canonical `spec/SPEC-74-auto-vectorization.md` (loop & `SLP` auto-vectorization, capability-disjoint dependence proofs, reduction legality, scalar epilogues) | `spec/SPEC-74-auto-vectorization.md` |
| `T617` | `E15.5` | `axiom-semantics` | Loop auto-vectorization legality, capability-disjoint dependence proving, reduction recognition, and scalar remainder epilogue generation (`INV-VEC-001`) | `tests/run/opt_loop_vec` |
| `T618` | `E15.5` | `axiom-backend` | Straight-line `SLP` vectorization, target SIMD width/cost model, and `OptIR` → `LIR` `Vec128`/`Vec256` vector lowering (`INV-VEC-002`) | `tests/run/opt_slp_vec` |
| `T619` | `E15.5` | `axiom-qa` | Loop & `SLP` auto-vectorization conformance suite (`INV-VEC-003`) | `tests/conformance/p15/e15_5_autovec` |
| `T620` | `E15.6` | `axiom-architect` | Canonical `spec/SPEC-75-lto-wpo-section-gc-pgo.md` (`LTO`, whole-program closed-world reachability, section GC/`ICF`, and `PGO`) | `spec/SPEC-75-lto-wpo-section-gc-pgo.md` |
| `T621` | `E15.6` | `axiom-semantics` | Whole-program closed-world reachability, cross-module `LTO` inlining/specialization/devirtualization, and generic deduplication (`INV-PIPE-012`) | `tests/run/opt_lto` |
| `T622` | `E15.6` | `axiom-backend` | Linker section GC (`COMDAT`/dead stripping), safe `ICF`, and deterministic `--pgo-gen`/`--pgo-use` pipeline (`INV-PIPE-012`) | `tests/run/opt_pgo_gc` |
| `T623` | `E15.6` | `axiom-qa` | `LTO`, whole-program optimization, section GC & `PGO` conformance suite (`INV-PIPE-012`) | `tests/conformance/p15/e15_6_lto_pgo_gc` |
| `T624` | `E15.7` | `axiom-architect` | Canonical `spec/SPEC-76-performance-contract.md` (benchmark suite, 3D binary size & compile-time budgets, optimization profiles, CI regression gates) | `spec/SPEC-76-performance-contract.md` |
| `T625` | `E15.7` | `axiom-backend` | Compiler `--time-passes` / `--size-report` telemetry and `tools/perf.py` + `tools/bench` benchmark harness enforcement (`INV-PIPE-013`) | `tests/run/perf_contract`, `tools/perf.py` |
| `T626` | `E15.7` | `axiom-qa` | Performance contract, `-O2` differential equivalence & CI regression budget conformance suite (`INV-PIPE-013`) | `tests/conformance/p15/e15_7_perf_contract` |
| `T315` | Gate | `axiom-qa` | Phase P15 gate — Optimizer 2.0 (certify all `E15.1`–`E15.8` exit criteria, `-O2` differential parity, CI performance budgets, and 411 phase requirements) | `tests/conformance/p15/README.md`, `_workspaces/reports/phase-P15-review.md` |

---

## 3. Directory-by-Directory Conformance Test Inventory

### 3.1 `e15_1_optir_ssa/` — E15.1 `OptIR`: SSA, `MemorySSA`, Pass-Contract Verifier & Scalar Optimization (`SPEC-70`, `INV-PIPE-008`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e15_1_conformance.test` / `e15_1_conformance_oracle.py` / `e15_1_conformance_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler.opt.optir`, `compiler.opt.effects`, `compiler.opt.passmgr`, and `compiler.opt.scalar` and executes across `-O0`, `-O1`, and `-O2 --verify-each`; verifies Cooper-Harvey-Kennedy `DominatorTree`, `OptPhi` & `MemorySSA` construction, `PassManager` fail-closed `Certainty` gate & transactional rollback, `EffectInfo` SCC propagation, `--emit=optir`/`--emit=memssa` determinism, and `unverified_read.mir` rejection |
| `memssa_phi_sroa_diamond_loop.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Nested-diamond + loop CFG exercising `OptPhi` placement, `MemorySSA` `LiveOnEntry`/`MemoryDef`/`MemoryUse`/`MemoryPhi` joins, and non-escaping aggregate scalarization (`MEMSSA_SROA_CFG=368`) |
| `cfg_ssa_memssa_sccp_gvn.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Wegman-Zadeck `SCCP` dead-branch pruning, dominator-scoped `GVN` & commutative `CSE`, and `NoAlias` `view`/`mut_view` store-to-load forwarding vs `UnknownAlias` raw-pointer reload retention (`CFG_TOTAL=1892`) |
| `abstraction_erasure_sroa_generics.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Zero-cost abstraction erasure across nested affine structs, generic wrapper monomorphization, and enum discriminant state-machine loops (`ABSTRACTION_TOTAL=345`) |
| `arith_wrapping_vs_checked_identities.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Modular `wrapping_add`/`wrapping_sub`/`wrapping_mul` group cancellation (`i8`, `i32`, `u8`, `u32`, `i64`, `u64` at `MIN`/`MAX` boundaries) vs guard-proven checked arithmetic (`ARITH_TOTAL=260`) |
| `effects_drop_clone_io_barriers_zeroize.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | UTF-8 I/O (`GREETING=Xin chào thế giới`), explicit `Clone` side effects, LIFO `Drop` ordering, `black_box`, `volatile_load`/`volatile_store`, atomic operations, and unread secret buffer `zeroize` preservation (`EFFECTS_DONE=69`) |
| `qa_loop_break_drop_unread_zeroize_alias.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | QA boundary check: move-flag single-drop elision, composite field `Drop`, loop `continue`/nested `break` LIFO `Drop` cleanup, loop-backedge pure-call destination clobbers, raw-pointer alias barriers, and unread `ptr_write_bytes` zeroization (`QA_ADVERSARIAL_DONE=202`) |
| `trap_checked_add_overflow_cancel_i32.ax`, `trap_checked_dead_overflow_dce_i64.ax`, `trap_checked_sub_underflow_u64.ax`, `trap_checked_mul_overflow_i16.ax`, `trap_div_by_zero_self_div_i32.ax`, `trap_signed_min_div_neg1_i8.ax`, `trap_signed_min_rem_neg1_i64.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`, `exit: 101`) | 7 checked-arithmetic and division/remainder trap fixtures proving `(i32.MAX + 1) - 1`, unused `i64.MAX + 1`, `0u64 - 1u64`, `300i16 * 300i16`, `0 / 0` (`x / x`), `(-128i8) / (-1i8)`, and `i64.MIN % (-1i64)` trap with exit code `101` across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each` |

### 3.2 `e15_2_alias_escape/` — E15.2 Capability-Driven Alias Analysis, Escape Analysis & Allocation Promotion (`SPEC-71`, `INV-PIPE-009`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e15_2_conformance.test` / `e15_2_conformance_oracle.py` / `e15_2_conformance_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler.own.cap`, `compiler.opt.alias`, `compiler.opt.memopt`, and `compiler.opt.escape` across `-O0`, `-O1`, and `-O2 --verify-each`; verifies 41 MIR blobs covering `AliasResult`, store-to-load forwarding, `RLE`, `DSE`, `TY_CLOSURE` capture typing (`REQ-OPT-385..386`), 4-point `EscapeClass` SCC fixed-point propagation, all 6 allocation promotions (`Box<T>` SROA/stack, closure env, inline buffer, `NRVO`, stack slot coloring), and fail-closed rollback |
| `alias_cap_forwarding_rle_dse.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Capability-driven `NoAlias` (`mut_view` vs `mut_view`/`view`), store-to-load forwarding, `RLE`, `DSE`, disjoint struct fields vs dynamic array index clobbers, sequential reborrows, and raw-pointer `MayAlias` barriers |
| `escape_box_buffer_slot_promotion.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | `NoEscape` `Box<T>` scalar/aggregate `SROA`, `ArgumentEscape` stack promotion across mutually recursive SCCs, bounded inline buffer & `Vec<i64>` promotion, and disjoint-lifetime stack slot reuse |
| `closure_signature_capture_promotion.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Explicit closure parameter/return signatures (`REQ-OPT-385`), all 4 capture modes (`CAP_COPY`, `CAP_VIEW`, `CAP_MUT_VIEW`, `CAP_MOVE`), generic `Fn`/`FnMut` dispatch, and `NoEscape` closure environment promotion |
| `nrvo_return_slot_and_drop_parity.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Single-local struct `NRVO`, multi-branch array `NRVO`, conflicting two-local `NRVO` rejection, and LIFO `Drop` ordering across nested scopes and `BoxGuard` payloads |
| `stable_address_and_escape_barriers.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Distinct `Box<i64>` pointer identity inequality, `address_of`/`address_of_mut` stable-address barriers, `GlobalEscape` via `mut_view<PtrSink>`, loop-carried heap allocations, oversized (`5120 B > 4096 B`) frame-budget retention, and `ptr_copy` overlap safety |
| `cross_seam_closure_box_nrvo_alias.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | QA cross-seam check combining closure capture promotion, `Box<T>` promotion, `NRVO`, `NoAlias` forwarding, address-taken pin barriers, and LIFO `Drop` ordering (`checksum=2067`) |
| `closure_cap_conflict_mut_ui.ax`, `closure_cap_conflict_read_ui.ax`, `closure_cap_move_conflict_ui.ax` | `ui` | Negative compile-time capability diagnostics (`REQ-OPT-386`): `AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, and `AX_MOVE_USE_AFTER_MOVE` on conflicting closure captures |

### 3.3 `e15_3_loops_bce/` — E15.3 Canonical Loop Analysis, Overflow-Faithful `SCEV`, `BCE` & Loop Transformations (`SPEC-72`, `INV-PIPE-010`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e15_3_loops_bce_oracle.test` / `e15_3_loops_bce_oracle.py` / `e15_3_loops_bce_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler.opt.loops`, `compiler.opt.bce`, and `compiler.opt.loop_xform`; verifies natural loop discovery, irreducible cycle classification, `LoopSimplify` + `LCSSA`, `SCEV` `{start, +, step}<mode>` & `TripCount`, positive vs negative `opt_bce` (`BCE_PROVEN_SAFE` vs `BCE_POSSIBLE_VIOLATION`), `opt_licm`, `opt_iv_strength_reduce`, `opt_loop_peel`, `opt_loop_unswitch`, `opt_loop_unroll`, `opt_loop_version`, and `opt_loop_fuse` |
| `scev_bce_and_range_elimination.ax` (+ `.stdout`, `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Canonical CFG loops (`continue`/`break`/LCSSA), nested loop `Drop` elaboration, fixed-array & bitmask `BCE`, multi-slice zip & `Vec<i32>` `BCE`, descending & signed guarded loops, disjoint subslices `[0..mid)` / `[mid..len)`, and soundness barriers |
| `licm_sr_peel_unroll_version_fusion.ax` (+ `.stdout`, `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | `LICM` invariant arithmetic/load hoisting, affine IV strength reduction, `i == 0` peeling with `arr[i - 1]`, loop unswitching, constant-trip full/partial unrolling & zero-trip elimination, symbolic loop versioning, and adjacent producer-consumer loop fusion |
| `oob_and_overflow_trap_preservation.ax` (+ `.stdout`, `o2_*`) | `diff` + `run` (`-O2 --verify-each`, `exit: 101`) | Exact stdout prefix preservation before panicking on out-of-bounds dynamic indexing |
| `trap_oob_vec_shrink_in_loop.ax`, `trap_licm_non_dominating_div.ax`, `trap_iv_sr_checked_overflow.ax`, `trap_versioned_loop_fallback_oob.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`, `exit: 101`) | 4 loop trap fixtures proving in-loop `Vec.len` shrink OOB, non-dominating guarded `100 / 0` inside zero-trip/conditional loops, checked IV `i * 1000000000` `i32` overflow, and versioned fallback OOB trap at the exact scalar iteration |

### 3.4 `e15_4_inline_specialize_devirt/` — E15.4 Inlining, `SROA`, Call-Site Specialization, Devirtualization & Tail Calls (`SPEC-73`, `INV-PIPE-011`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e15_4_inline_specialize_devirt_oracle.test` / `e15_4_inline_specialize_devirt_oracle.py` / `e15_4_inline_specialize_devirt_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler.opt.sroa`, `compiler.opt.inline`, `compiler.opt.ipa`, and `compiler.opt.devirt`; verifies all 5 E15.4 `PassManager` contracts (`PASS_COPY_MOVE_SROA`..`PASS_TAILCALL`), deep `SROA` & `RVO`/`NRVO`, Tarjan `SCC` summaries (`Result<T, E>` != `MayPanic`), 2-stage `InlineLegality` vs `CostModel`, `SpecializationKey` cloning & `address_taken_fn` identity preservation, 3-tier devirtualization, and `TCO_LEGAL` self-tail-recursion loop lowering |
| `abstraction_erasure_sroa_rvo_inline.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Nested generic/closure pipelines, deep `SROA`, caller-allocated `RVO`/`NRVO` with LIFO `Drop` ordering, `Result<T, E>` purity, and `@inline(never)` / recursive `SCC` termination boundaries |
| `devirt_and_open_world_boundaries.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Tier 1 exact devirtualization, Tier 2 guarded polymorphic switch devirtualization, Tier 3 retained dynamic dispatch (>4 targets & opaque boundaries), and function-pointer identity preservation |
| `tailcall_constant_stack_and_drop_guards.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Deep self-tail-recursion lowered to $O(1)$-stack loop (`25,000` iterations without stack overflow), sibling tail calls, post-call `Drop` guard preservation (`TCO_REASON_LIVE_DROP_AFTER_CALL`), and stack-view escape guards (`TCO_REASON_STACK_VIEW_ESCAPE`) |
| `trap_inlined_panic_and_drop_order.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`, `exit: 101`) | Strict left-to-right call-site argument evaluation order and inner LIFO `Drop` execution before a deterministic panic inside an inlined callee |

### 3.5 `e15_5_autovec/` — E15.5 Loop & `SLP` Auto-Vectorization (`SPEC-74`, `INV-VEC-001..003`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e15_5_conformance.test` / `e15_5_conformance_oracle.py` / `e15_5_conformance_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler.opt.vectorize`, `compiler.opt.slp`, and `compiler.lir.vec_lower`; verifies `opt_loop_vec` & `opt_slp_vec` legality, capability-disjoint (`mut_view` vs `view`) + `SCEV` dependence proofs, `VectorCostModel` (`SSE2` 128-bit / `AVX2` 256-bit), `LirType.V128`/`V256` lowering with `VZEROUPPER`, and `Source → MIR → OptIR → LIR → Machine` remarks (`--emit=vectorize`, `--emit=vector-cost`) |
| `loop_vec_all_widths_and_epilogues.ax` (+ `.stdout`, `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Loop auto-vectorization across `i8..i64`, `u8..u64`, `f32`, and `f64` with scalar remainder epilogue execution across `0`, `1`, prime (`7`, `13`, `19`), aligned (`16`), and unaligned (`23`) trip counts |
| `loop_vec_reductions_and_barriers.ax` (+ `.stdout`, `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Associative `wrapping_*` / bitwise / `min` / `max` reductions vs strict IEEE-754 ordered FP reductions, raw-pointer `MayAlias` fallback, and `atomic`/`volatile` barriers |
| `slp_pack_trees_and_fallbacks.ax` (+ `.stdout`, `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Straight-line `SLP` 2-, 4-, and 8-lane isomorphic struct-field and array-element pack trees, cost-model rejection of non-contiguous scatter/gather trees, and aliasing store barriers |
| `trap_loop_checked_add_overflow.ax`, `trap_loop_epilogue_tail_oob.ax`, `trap_slp_lane_bounds_oob.ax`, `trap_slp_lane_checked_overflow.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`, `exit: 101`) | 4 vectorization trap fixtures proving checked-overflow and out-of-bounds traps inside loop main bodies, scalar remainder epilogues, and individual `SLP` lanes trap identically to scalar `--interp` |

### 3.6 `e15_6_lto_pgo_gc/` — E15.6 Whole-Program `LTO`, Section GC / `ICF` & `PGO` (`SPEC-75`, `INV-PIPE-012`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e15_6_lto_pgo_gc_oracle.test` / `e15_6_lto_pgo_gc_oracle.py` / `e15_6_lto_pgo_gc_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler.opt.lto`, `compiler.link.gc_icf`, and `compiler.opt.pgo`; verifies `.axmeta` summaries, `ThinLTO` partition rebuild detection, closed-world reachability roots, cross-module inlining/specialization/RTA devirt, generic monomorphization deduplication, `COMDAT` GC + `Safe ICF` (`0xE9 jmp rel32` thunks), 3D binary size metrics, `--pgo-gen` → `pgo_merge_profiles` → `--pgo-use`, stale-profile fallback, and multi-module CLI build equivalence |
| `lto_multimod_inline_spec_devirt_dedup.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Cross-boundary inlining, constant specialization, closed-world RTA trait dispatch, generic monomorphization deduplication, function-pointer identity preservation, and LIFO `Drop` order |
| `section_gc_roots_and_safe_icf_identity.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Dead function/table stripping vs `@export`/live table roots, `Safe ICF` indirect call address distinctness, and distinct mutable capability barriers |
| `pgo_roundtrip_stale_and_safety_contracts.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Speculative devirtualization guard fallback, zero-count cold branch preservation, constant-time secret `zeroize` barrier, and ordered MMIO sequence preservation (`REQ-OPT-246..250`) |
| `trap_pgo_lto_bounds_and_drop_order.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`, `exit: 101`) | Proves 100%-observed in-bounds hot execution never elides cold panic/bounds traps and preserves pre-trap stdout and LIFO `Drop` order |

### 3.7 `e15_7_perf_contract/` — E15.7 Performance Contract, 3D Footprint, Telemetry & CI Budgets (`SPEC-76`, `INV-PIPE-013`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e15_7_conformance.test` / `e15_7_conformance_oracle.py` / `e15_7_conformance_probe.ax.in` | `cmd` + live compiler probe + `perf.py` | Bundles `compiler.driver.perf_telemetry`, `compiler.link.gc_icf`, and `compiler.obj.coff`; verifies differential equivalence across `--interp`, `-O0`, `-O1`, `-O2 --verify-each`, and `-Oz`, byte-identical `-O2` reproducibility, `--time-passes`/`--size-report` telemetry orthogonality, and runs `tools/perf.py --check-budgets` across all 7 `tools/bench` suites and all 9 quantitative `SPEC-76` budgets |
| `multipass_stress_all_tiers.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Full-pipeline multi-pass stress kernel exercising `OptIR` SSA/`MemorySSA`, `SCCP`, `GVN`/`CSE`, `SROA`, escape promotion, `SCEV`/`BCE`, `LICM`, `SCC` inlining, specialization, devirtualization, 4-lane loop & `SLP` auto-vectorization, and high-pressure linear-scan RA + `lea`/`cmovcc` ISel |
| `perf_profiles_zero_cost_vs_size_sharing.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Zero-cost abstraction erasure (`WeightKernel` devirt, `Accumulator` SROA, proven `BCE`), `-O2` specialization vs `-Oz` shared code folding, generic representation sharing, zero monolithic runtime (`REQ-OPT-334`), and LIFO `Drop` order |
| `provenance_determinism_and_pgo_optionality.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | PGO optionality (`REQ-OPT-251..252`), legality-first auto-tuning filtering (`!legality_proven` rejected, `REQ-OPT-242`), hard candidate/time budgets (`REQ-OPT-243`), telemetry orthogonality (`REQ-OPT-244..245`), and `OptOrigin` provenance chain preservation (`REQ-OPT-254..256`) |
| `binary_footprint_3d_and_layout_contract.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | 3D binary footprint contract (`FileSize`, `MappedSize`, `StartupWorkingSet`, `PeakWorkingSet`), `.bss` zero-file-bytes invariant, thermal `.text` section clustering (`StartupEntrySet -> HotCluster -> WarmNormal -> ColdSplit`), and alignment padding budget (`<= 2%` at `-O2`, `0` at `-Oz`) |
| `trap_multipass_unproven_bounds_and_drop_order.ax`, `trap_checked_overflow_preserved_under_o2_oz.ax`, `trap_pgo_autotune_never_weakens_verified_mir.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`, `exit: 101`) | 3 multi-pass trap fixtures proving unproven dynamic bounds checks, checked `(i32.MAX + 1) - 1` overflow, and cold division-by-zero after 100%-taken fast paths trap with exit code `101` across `--interp`, `-O0`, `-O1`, `-O2`, and `-Oz` |

### 3.8 `e15_8_regalloc_isel/` — E15.8 Linear-Scan Register Allocation, ISel, Branchless `cmovcc` & Post-RA Peepholes (`SPEC-77`, `INV-PIPE-006`, `INV-PIPE-007`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e15_8_conformance.test` / `e15_8_conformance_oracle.py` / `e15_8_conformance_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler.backend.regalloc`, `compiler.target.x64.{isel,frame,verify,print,encode}`, and `compiler.backend.peephole`; verifies 4 stages covering high-pressure live-range splitting, spill-slot coloring, copy coalescing, callee-saved `FrameLayout` preservation, fixed-reg `rcx`/`rax`/`rdx` constraints, `lea` & magic-multiply ISel, non-speculating `cmovcc`/`setcc` if-conversion, `EFLAGS`-safe post-RA peepholes, and `axiomc inspect --emit={lir,mi,mc}` determinism (`REQ-OPT-371..372`) |
| `regalloc_extreme_pressure_spills.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | 24 simultaneous live `i64` values across nested loops, conditional merges, and helper calls (`RA_PRESSURE_TOTAL=277924`) |
| `fixed_reg_clobbers_div_shift_abi.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Simultaneous variable shifts (`rcx`), runtime signed/unsigned division/remainder (`rax`/`rdx`), and 8-argument Win64 ABI calls (`FIXED_CLOBBER_TOTAL=1901505804`) |
| `isel_lea_const_divmul_casts.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Scaled-index `base + index * scale + disp` `lea` addressing, boundary immediates, constant multiply/divide/remainder (`INT64_MIN`/`UINT64_MAX` edges), and cascading integer width casts (`ISEL_TOTAL=73938`) |
| `if_conv_cmov_setcc_nospeculate.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Branchless `cmovcc`/`setcc` diamonds alongside guarded division, null-pointer load, and OOB slice indexing arms that must never be speculated (`IFCONV_TOTAL=4182`) |
| `peephole_eflags_barriers_utf8_io.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | Post-RA peephole `EFLAGS` liveness across fallthrough jumps and `cl` shifts, store-reload forwarding with pointer-alias barriers, and UTF-8 string output (`PEEPHOLE_UTF8=Xin chào E15.8 αβγ 42`) |
| `qa_cross_seam_40live_div_shift_cmov_peephole.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`) | QA cross-seam check: 40 simultaneous live `i64` locals across 2-level nested loops, 9-arg Win64 stack call, `RDX:RAX` div/rem, `RCX` shifts, `cmovcc`/`setcc`, `lea`, LIFO `Drop`, and UTF-8 output (`QA_TOTAL=8697`) |
| `trap_checked_add_lea_exclusion_i64.ax`, `trap_checked_sub_underflow_u64.ax`, `trap_checked_mul_overflow_i64.ax`, `trap_div_by_zero_guarded_arm_taken.ax`, `trap_signed_min_div_neg1_i64.ax`, `qa_trap_subword_overflow_under_pressure.ax` (+ `o2_*`) | `diff` + `run` (`-O2 --verify-each`, `exit: 101`) | 6 machine-level trap fixtures proving checked `i64` `+` and `* 9` never silently wrap via `lea` (`AXS-MCOPT-016`), `3u64 - 4u64` underflow traps, taken guarded `/ 0` and `i64.MIN / -1` trap, and subword `i16` overflow under 20-live-value spill pressure + `cmovcc` preserves `OF` (`exit: 101`) |

---

## 4. Running the Phase 15 Conformance Suite & CI Performance Budget Gate

From the workspace root with `-j 1`:

```bash
python tools/axtest.py --compiler build/axiomc2.exe -j 1 \
  --exclude-requires axiom0-internal \
  conformance/p15

python tools/perf.py --compiler build/axiomc2.exe --check-budgets
```

Expected results:
- `axtest.py`: `WEAK-NATIVE 0`, `FAIL 0`, `SKIP 0`, `XFAIL 0`.
- `perf.py --check-budgets`: All 7 benchmarks (`BENCH-STARTUP-001`..`BENCH-COMPILE-001`) and all 9 budgets (`BUDGET-CTIME-001`..`BUDGET-SELF-002`) `PASS` (exit `0`).
