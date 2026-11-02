# T215 Report — Plan phase P15: Optimizer 2.0

## Tóm tắt
Đã mở rộng toàn bộ giai đoạn P15 (`P15-optimizer-2-0`) từ 8 epic (`E15.1`–`E15.8`) trong `spec/ROADMAP.md` thành 32 task cụ thể (`T063` và `T064` được tinh chỉnh tại chỗ và 30 task mới `T600`–`T629` trong dải `T600`–`T649` của P15, từ 3 đến 5 task mỗi epic), bao gồm sắp lịch `E15.8` (`T627`, `T063`, `T628`, `T629`) chạy đầu tiên trong P15 để tăng tốc bản thân `axiomc` (ROADMAP R7), thiết lập phụ thuộc của tất cả task `E15.5` (`T616`–`T619`) vào gate `T312` của P12, chuyển toàn bộ 405 dòng `EPIC(E15.*)` trong `spec/requirements/CATALOG.md` sang ID task cụ thể (`T063`, `T064`, `T600`–`T629`), cập nhật `T315` phụ thuộc vào tất cả task P15, và ghi nhận vào `spec/ROADMAP.md`.

## Summary
Expanded Phase P15 (`P15-optimizer-2-0`) across all eight roadmap epics (`E15.1`–`E15.8`) into 32 concrete, single-sitting tasks (30 new tasks `T600`–`T629` in the `T600`–`T649` P15 block plus refined existing tasks `T063` and `T064`), converted all 405 `EPIC(E15.*)` rows in `spec/requirements/CATALOG.md` to concrete `T063`, `T064`, and `T600`–`T629` task IDs with matching `covers:` lists, wired `T315` (`depends: [T215, T063, T064, T600..T629]`), and updated `spec/ROADMAP.md`.

### Epic breakdown
1. **E15.1 OptIR: SSA / MemorySSA** (5 tasks: `T600`–`T604`):
   - `T600` (`axiom-architect`): Canonical `spec/SPEC-70-optir-ssa-memoryssa.md` (`OptIR` SSA/MemorySSA model, pass-manager legality contracts, and observable semantics preservation; 42 reqs).
   - `T601` (`axiom-semantics`): Verified MIR → `OptIR` lowering, dominance frontier, SSA phi placement, `MemorySSA` construction, and `Proven`/`Possible`/`Unknown` certainty tracking (14 reqs).
   - `T602` (`axiom-semantics`): `OptIR` Pass Manager, canonical `EffectInfo` inference, and transformation contract/proof verifier (22 reqs).
   - `T603` (`axiom-semantics`): Unified scalar optimization engine (SCCP, GVN, CSE, DCE, and overflow-faithful algebraic simplification; 11 reqs).
   - `T604` (`axiom-qa`): `OptIR` SSA/MemorySSA, pass-contract verifier & scalar optimization conformance suite (6 reqs).
2. **E15.2 Alias & escape analysis, allocation promotion** (4 tasks: `T605`–`T608`):
   - `T605` (`axiom-architect`): Canonical `spec/SPEC-71-alias-escape-promotion.md` (capability/provenance `AliasInfo`, `EscapeInfo` lattice, and storage promotion rules; 12 reqs).
   - `T606` (`axiom-semantics`): Capability-aware `AliasInfo`, provenance disjointness, and `MemorySSA` store-to-load forwarding & dead store elimination (7 reqs).
   - `T607` (`axiom-semantics`): Escape analysis (`NoEscape`/`ArgumentEscape`/`ReturnEscape`/`GlobalEscape`) and heap-to-stack/register allocation promotion (10 reqs).
   - `T608` (`axiom-qa`): Alias analysis, escape analysis & allocation promotion conformance suite (6 reqs).
3. **E15.3 Loops & bounds-check elimination** (4 tasks: `T609`–`T612`):
   - `T609` (`axiom-architect`): Canonical `spec/SPEC-72-loops-scev-bce.md` (natural loops, `SCEV`, `RangeInfo`, `BCE`, `LICM`, and loop transformations; 23 reqs).
   - `T610` (`axiom-semantics`): Natural loop discovery, canonicalization (`LoopSimplify` + `LCSSA`), `SCEV`, and range/bounds-check elimination (`BCE`; 16 reqs).
   - `T611` (`axiom-semantics`): `LICM`, induction strength reduction, loop unrolling/peeling/unswitching, and lazy iterator pipeline fusion (15 reqs).
   - `T612` (`axiom-qa`): Loop optimizations, `SCEV` & bounds-check elimination conformance suite (18 reqs).
4. **E15.4 Inlining, specialization, devirtualization (+ copy propagation, SROA)** (4 tasks: `T613`, `T064`, `T614`, `T615`):
   - `T613` (`axiom-architect`): Canonical `spec/SPEC-73-inlining-specialization-devirt.md` (call-graph inlining, `SROA`, `RVO`/`NRVO`, specialization, devirtualization, and tail-call optimization; 28 reqs).
   - `T064` (`axiom-semantics`): Copy/move propagation, `SROA`, return-slot construction, and bottom-up SCC call-graph inlining (21 reqs: 6 `REQ-TYP-*` + 15 `REQ-OPT-*`).
   - `T614` (`axiom-semantics`): Interprocedural constant/closure call-site specialization, `dyn Trait` devirtualization, and tail-call optimization (21 reqs).
   - `T615` (`axiom-qa`): Inlining, specialization, devirtualization & `SROA` conformance suite (6 reqs).
5. **E15.5 Auto-vectorization** (4 tasks: `T616`–`T619`, all depending on P12 gate `T312`):
   - `T616` (`axiom-architect`): Canonical `spec/SPEC-74-auto-vectorization.md` (loop & `SLP` auto-vectorization, capability-disjoint dependence proofs, reduction legality, and scalar epilogues; 9 reqs).
   - `T617` (`axiom-semantics`): Loop auto-vectorization legality, capability-disjoint dependence proving, reduction recognition, and scalar remainder epilogue generation (4 reqs).
   - `T618` (`axiom-backend`): Straight-line `SLP` vectorization, target SIMD width/cost model, and LIR vector lowering (5 reqs).
   - `T619` (`axiom-qa`): Loop & `SLP` auto-vectorization conformance suite (4 reqs).
6. **E15.6 LTO / whole-program / section GC / PGO** (4 tasks: `T620`–`T623`):
   - `T620` (`axiom-architect`): Canonical `spec/SPEC-75-lto-wpo-section-gc-pgo.md` (`LTO`, whole-program closed-world reachability, section GC/`ICF`, and `PGO`; 29 reqs).
   - `T621` (`axiom-semantics`): Whole-program closed-world reachability, cross-module `LTO` inlining/specialization, and generic deduplication (16 reqs).
   - `T622` (`axiom-backend`): Linker section GC (`COMDAT`/dead stripping), safe `ICF`, and deterministic `--pgo-gen`/`--pgo-use` pipeline (19 reqs).
   - `T623` (`axiom-qa`): `LTO`, whole-program optimization, section GC & `PGO` conformance suite (5 reqs).
7. **E15.7 Performance contract** (3 tasks: `T624`–`T626`):
   - `T624` (`axiom-architect`): Canonical `spec/SPEC-76-performance-contract.md` (benchmark suite, compile-time & binary size/working-set budgets, optimization profiles, and CI regression gates; 7 reqs).
   - `T625` (`axiom-backend`): Compiler `--time-passes` / `--size-report` telemetry and `tools/perf.py` + `tools/bench` benchmark harness enforcement (4 reqs).
   - `T626` (`axiom-qa`): Performance contract, `-O2` differential equivalence & CI regression budget conformance suite (6 reqs).
8. **E15.8 Register allocation (linear scan) & better instruction selection** (4 tasks: `T627`, `T063`, `T628`, `T629`, scheduled first in P15 at `priority: 89`–`92`):
   - `T627` (`axiom-architect`): Canonical `spec/SPEC-77-regalloc-machine-opt.md` (linear-scan register allocation, spill/reload, `FrameLayout`, instruction selection, branchless if-conversion, and post-RA peephole optimization; 11 reqs).
   - `T063` (`axiom-backend`): Linear-scan register allocation, move coalescing, spill/reload insertion, and callee-saved frame integration (4 reqs).
   - `T628` (`axiom-backend`): Better instruction selection (`lea` addressing, constant division/modulo), branchless `cmov` if-conversion, and post-RA machine peephole optimization (8 reqs).
   - `T629` (`axiom-qa`): Register allocation, instruction selection & post-RA machine optimization conformance suite (2 reqs).

## Files changed
- ./_workspaces/tasks/todo/T063-linear-scan-register-allocation.md
- ./_workspaces/tasks/todo/T064-optimizer-ladder-2-copy-propagation-inlining-sroa.md
- ./_workspaces/tasks/todo/T215-plan-phase-p15-optimizer-2-0.md
- ./_workspaces/tasks/todo/T315-phase-p15-gate-optimizer-2-0.md
- ./_workspaces/tasks/todo/T600-e15-1-optir-ssa-memoryssa-legality-spec.md
- ./_workspaces/tasks/todo/T601-e15-1-mir-to-optir-dominance-ssa-memoryssa.md
- ./_workspaces/tasks/todo/T602-e15-1-pass-manager-effect-summaries-contract-verifier.md
- ./_workspaces/tasks/todo/T603-e15-1-scalar-opt-sccp-gvn-cse-dce.md
- ./_workspaces/tasks/todo/T604-e15-1-optir-ssa-scalar-opt-conformance-suite.md
- ./_workspaces/tasks/todo/T605-e15-2-alias-escape-allocation-promotion-spec.md
- ./_workspaces/tasks/todo/T606-e15-2-capability-alias-info-memoryssa-dse.md
- ./_workspaces/tasks/todo/T607-e15-2-escape-analysis-allocation-promotion.md
- ./_workspaces/tasks/todo/T608-e15-2-alias-escape-promotion-conformance-suite.md
- ./_workspaces/tasks/todo/T609-e15-3-loops-scev-licm-bce-spec.md
- ./_workspaces/tasks/todo/T610-e15-3-loop-canonicalization-scev-bce.md
- ./_workspaces/tasks/todo/T611-e15-3-licm-strength-reduction-unrolling-iterator-fusion.md
- ./_workspaces/tasks/todo/T612-e15-3-loops-scev-bce-conformance-suite.md
- ./_workspaces/tasks/todo/T613-e15-4-inlining-specialization-devirt-sroa-spec.md
- ./_workspaces/tasks/todo/T614-e15-4-call-site-specialization-devirt-tailcall.md
- ./_workspaces/tasks/todo/T615-e15-4-inline-specialize-devirt-conformance-suite.md
- ./_workspaces/tasks/todo/T616-e15-5-loop-slp-auto-vectorization-spec.md
- ./_workspaces/tasks/todo/T617-e15-5-loop-auto-vectorization-dependence-epilogue.md
- ./_workspaces/tasks/todo/T618-e15-5-slp-vectorization-simd-cost-model-lir.md
- ./_workspaces/tasks/todo/T619-e15-5-auto-vectorization-conformance-suite.md
- ./_workspaces/tasks/todo/T620-e15-6-lto-wpo-section-gc-pgo-spec.md
- ./_workspaces/tasks/todo/T621-e15-6-whole-program-lto-cross-module-generic-dedup.md
- ./_workspaces/tasks/todo/T622-e15-6-linker-section-gc-icf-pgo-pipeline.md
- ./_workspaces/tasks/todo/T623-e15-6-lto-wpo-section-gc-pgo-conformance-suite.md
- ./_workspaces/tasks/todo/T624-e15-7-performance-contract-benchmarks-budgets-spec.md
- ./_workspaces/tasks/todo/T625-e15-7-pass-timing-size-telemetry-benchmark-harness.md
- ./_workspaces/tasks/todo/T626-e15-7-perf-contract-o2-differential-conformance-suite.md
- ./_workspaces/tasks/todo/T627-e15-8-regalloc-instruction-selection-machine-opt-spec.md
- ./_workspaces/tasks/todo/T628-e15-8-isel-branchless-cmov-post-ra-peephole.md
- ./_workspaces/tasks/todo/T629-e15-8-regalloc-isel-peephole-conformance-suite.md
- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T063`, `T064`, `T315`, and `T600`–`T629`: `OK` (33 files).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate`: `OK (388 tasks)`.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK` (all 405 `EPIC(E15.*)` rows converted to concrete `T063`, `T064`, and `T600`–`T629` tasks; `v1-full planned=2144`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T215`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE
