# Phase 18 (`P18-compiler-architecture-2-0`) Conformance Suite Index

This directory (`tests/conformance/p18/`) contains the end-to-end Phase 18 (**Compiler Architecture 2.0**) conformance suite certifying all seven roadmap epics (`E18.1`–`E18.7`) in `spec/ROADMAP.md` §3, canonical specifications `spec/SPEC-21-query-engine-semantic-db.md` through `spec/SPEC-27-separate-compilation-linker-v2.md`, architecture invariants `INV-QRY-001..003` (`INV-DB-*`), `INV-INC-001..003`, `INV-PAR-001..003`, `INV-ART-001..003`, `INV-PCT-001..003` (`INV-DRV-*`), `INV-WLIB-001..003`, and `INV-LNK-001..003` in `spec/invariants.md`, and all 28 Phase 18 implementation/spec/QA tasks (`T067`, `T750`–`T776`) gated by `T318`.

---

## 1. Epic & Canonical Specification Overview (`E18.1`–`E18.7`, `SPEC-21`–`SPEC-27`)

| Epic | Conformance Directory | Canonical Spec | Rule Range | Invariant IDs (`spec/invariants.md`) | Tasks (`28` total) | Core Exit Criteria |
|---|---|---|---|---|---|---|
| **`E18.1`** Query engine / semantic database | `tests/conformance/p18/e18_1_query_engine/` | `spec/SPEC-21-query-engine-semantic-db.md` | `AXS-QRY-001..053` | `INV-QRY-001..003` (`INV-DB-*`) | `T752`, `T753`, `T754`, `T755` | Demand-driven `CompilerDB` input/derived separation, active `QueryStack` DAG recording, `inspect --emit=query-graph`, Tarjan cycle detection with canonical `SemanticKey` rotation (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`), poisoned fallback cascade suppression, and cold-vs-warm snapshot-bound diagnostic replay |
| **`E18.2`** Incremental compilation | `tests/conformance/p18/e18_2_incremental/` | `spec/SPEC-22-incremental-compilation.md` | `AXS-INC-001..053` | `INV-INC-001..003` | `T756`, `T757`, `T758`, `T759` | Four-tier 128-bit BLAKE3 fingerprints (`Source`, `Ast`, `Interface`/`Abi`, `Body`, `Codegen`), Red-Green `try_mark_green` backdating, Private-Body Firewall (`edit-one-private-fn` re-typechecks only that module; `0` downstream `typeck` queries), persistent checksummed `.axiom-cache` (`AXCACHE1`), `< 100 ms` no-op rebuild on the compiler itself, and clean-vs-incremental byte identity |
| **`E18.3`** Parallel compilation | `tests/conformance/p18/e18_3_parallel/` | `spec/SPEC-23-parallel-compilation.md` | `AXS-PAR-001..053` | `INV-PAR-001..003` | `T760`, `T761`, `T762`, `T763` | Thread-safe immutable `DatabaseSnapshot`s, `(ModuleId, LocalIndex)` scoped IDs, 64-shard content-addressed interner, `SingleFlightLatch` + cross-worker `WaitForGraph` cycle detection, work-stealing DAG scheduler, parallel per-`CGU` codegen, and byte-identical `.obj`/`.exe`, HIR/MIR/LIR dumps, and `AXD-060` diagnostics across `--jobs 1`, `2`, `4`, `8` |
| **`E18.4`** Artifact format & module interface files | `tests/conformance/p18/e18_4_artifacts/` | `spec/SPEC-24-artifact-format-module-interfaces.md` | `AXS-ART-001..053` | `INV-ART-001..003` | `T764`, `T765`, `T766`, `T767` | Pointer-free 64-byte `ArtifactHeader` & `SectionDescriptor` containers, `.axmi` binary module interfaces (signatures, `TypeId` DAG, traits, capabilities, `const` values, verified generic MIR templates) for source-free downstream compilation, and embedded non-alloc `.axmeta`/`.axmir`/`.axlto` COFF sections stripped from final `.exe`/`.dll` |
| **`E18.5`** Pass contracts & proof-carrying transformations (+ driver CLI verification flags) | `tests/conformance/p18/e18_5_pass_contracts/` (`e18_5_driver_cli`) | `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` | `AXS-PCT-001..053` | `INV-PCT-001..003` (`INV-DRV-*`) | `T768`, `T769`, `T770`, `T771` | Static `PassContract` registry, `ProofCertificate` / `ProofProvenance` invalidation on `ir_revision` mutation, 3-valued `Certainty` (`Proven`/`Possible`/`Unknown`) fail-closed transactional rollback, in-process `Source Analysis 2.0` / `Effect System 2.0` / `Symbolic Execution 2.0`, per-function `TranslationWitness` across MIR/`OptIR`/LIR/RegAlloc/Scheduling, and `--verify-pass-contracts` / `--validate-translations` / `inspect --emit=pass-witness` |
| **`E18.6`** Separate compilation, multiple objects, archives, section GC | `tests/conformance/p18/e18_6_separate_compilation/` | `spec/SPEC-27-separate-compilation-linker-v2.md` | `AXS-LNK-001..053` | `INV-LNK-001..003` | `T774`, `T067`, `T775`, `T776` | Per-module `.obj` + `.axmi` separate compilation, format-neutral `LinkIR`, multi-object & `.lib` fixed-point linking, `_AX1_` lossless demangling in `AX_LINK_*` diagnostics, per-item section subdivision (`.text$<sym>`, `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>`, associative `.pdata`/`.xdata`), `IMAGE_SCN_LNK_COMDAT` generic/vtable deduplication, and root-set `--gc-sections` |
| **`E18.7`** Windows x64 artifact kinds: static `.lib`, `.dll` + import `.lib` | `tests/conformance/p18/e18_7_windows_artifacts/` | `spec/SPEC-26-windows-artifact-kinds.md` | `AXS-WLIB-001..053` | `INV-WLIB-001..003` | `T772`, `T750`, `T751`, `T773` | `REQ-OWNER-006`: `--kind exe\|obj\|lib\|dll`, deterministic COFF `.lib` writer/reader (`!<arch>\n`, 1st/2nd linker members, `//`, zero timestamps), PE32+ `.dll` writer (`.edata`, synthesized `_DllMainCRTStartup` calling `__ax_resolve_module_bindings()`, `.reloc` with `DYNAMIC_BASE`), companion COFF short-import `.lib` (`Sig1=0x0000, Sig2=0xFFFF`), and `ADR-0034` §4 OI-07b GNU `ld` cross-linking of `--emit=obj` via `__imp_<name>` and `axiom_rt.obj` |

---

## 2. All 28 Phase 18 Tasks (`T067`, `T750`–`T776`) + Planning (`T218`) & Gate (`T318`)

| Task ID | Epic | Owner | Title & Scope Summary | Primary Verification Target |
|---|---|---|---|---|
| `T218` | Plan | `axiom-architect` | Plan phase P18 — Compiler architecture 2.0 (expand `E18.1`–`E18.7` into 28 tasks and map 5,523 `CATALOG.md` requirements) | `spec/ROADMAP.md`, `spec/requirements/CATALOG.md` |
| `T772` | `E18.7` | `axiom-architect` | Canonical `spec/SPEC-26-windows-artifact-kinds.md` (`--kind exe\|obj\|lib\|dll`, COFF `.lib`, PE32+ `.dll`, short-import `.lib`) | `spec/SPEC-26-windows-artifact-kinds.md` |
| `T750` | `E18.7` | `axiom-backend` | Static libraries: COFF archive (`.lib`) writer and reader, `--kind lib`, `-l`/`-L` search, fixed-point extraction (`INV-WLIB-001`) | `tests/link/lib` |
| `T751` | `E18.7` | `axiom-backend` | PE DLL output: `.edata` exports, `_DllMainCRTStartup` initialiser, `.reloc` base relocations, short-import `.lib`, and `ADR-0034` §4 OI-07b `__imp_<name>` + `--rt-obj` (`INV-WLIB-002`) | `tests/link/dll` |
| `T773` | `E18.7` | `axiom-qa` | Windows x64 static `.lib`, PE DLL, import library & GNU `ld` cross-link conformance suite (`INV-WLIB-003`) | `tests/conformance/p18/e18_7_windows_artifacts` |
| `T752` | `E18.1` | `axiom-architect` | Canonical `spec/SPEC-21-query-engine-semantic-db.md` (`CompilerDB`, demand-driven queries, cycle handling, snapshot diagnostics, invalidation) | `spec/SPEC-21-query-engine-semantic-db.md` |
| `T753` | `E18.1` | `axiom-frontend` | `CompilerDB` input/derived tables, demand-driven `QueryStack`, memoization, and `inspect --emit=query-graph` (`INV-QRY-001`) | `tests/run/query_db` |
| `T754` | `E18.1` | `axiom-semantics` | Deterministic active-stack query cycle detection, canonical `SemanticKey` rotation, fallback recovery values, snapshot-bound diagnostics, and revision invalidation (`INV-QRY-002`) | `tests/run/query_cycles` |
| `T755` | `E18.1` | `axiom-qa` | Query engine, cycle recovery & semantic database conformance suite (`INV-QRY-003`) | `tests/conformance/p18/e18_1_query_engine` |
| `T756` | `E18.2` | `axiom-architect` | Canonical `spec/SPEC-22-incremental-compilation.md` (multi-tier fingerprints `0152 §78`, red-green `try_mark_green`, persistent `.axiom-cache`) | `spec/SPEC-22-incremental-compilation.md` |
| `T757` | `E18.2` | `axiom-semantics` | 128-bit `Source`/`Ast`/`Interface`/`Abi`/`Body`/`Codegen` fingerprints, red-green `try_mark_green` propagation, `inspect --emit=fingerprints` & `--emit=incremental-stats` (`INV-INC-001`) | `tests/run/incremental_fingerprint` |
| `T758` | `E18.2` | `axiom-backend` | Persistent `.axiom-cache` on-disk dependency graph & `.obj` cache, hermetic `EnvironmentDigest`, corruption recovery, `< 100 ms` no-op rebuild fast path (`INV-INC-002`) | `tests/run/incremental_cache` |
| `T759` | `E18.2` | `axiom-qa` | Incremental compilation, `edit-one-private-fn` firewall & `< 100 ms` no-op rebuild conformance suite (`INV-INC-003`) | `tests/conformance/p18/e18_2_incremental` |
| `T760` | `E18.3` | `axiom-architect` | Canonical `spec/SPEC-23-parallel-compilation.md` (`--jobs N` determinism, immutable snapshots, `(ModuleId, LocalIndex)` IDs, work-stealing DAG) | `spec/SPEC-23-parallel-compilation.md` |
| `T761` | `E18.3` | `axiom-frontend` | Thread-safe immutable `CompilerDB` snapshots, `(ModuleId, LocalIndex)` IDs, sharded interner, `SingleFlightLatch` + `WaitForGraph` cycle detection, `--jobs N` scheduler (`INV-PAR-001`) | `tests/run/parallel_scheduler` |
| `T762` | `E18.3` | `axiom-backend` | Parallel per-module / per-`CGU` LIR lowering, RA, encoding & `.obj` emission, incremental cache integration, deterministic post-join diagnostic & `.obj` merging (`INV-PAR-002`) | `tests/run/parallel_codegen` |
| `T763` | `E18.3` | `axiom-qa` | Parallel compilation thread-count invariance (`--jobs 1/2/4/8`) & byte-identical determinism conformance suite (`INV-PAR-003`) | `tests/conformance/p18/e18_3_parallel` |
| `T764` | `E18.4` | `axiom-architect` | Canonical `spec/SPEC-24-artifact-format-module-interfaces.md` (`ArtifactHeader`, `.axmi` module interfaces, `.axmeta`/`.axmir`/`.axlto` sections) | `spec/SPEC-24-artifact-format-module-interfaces.md` |
| `T765` | `E18.4` | `axiom-semantics` | `.axmi` binary serializer & loader in `compiler/artifact/axmi`, exported signatures/types/traits/capabilities/`const`/generic MIR templates, `CompilerDB` ingestion (`INV-ART-001`) | `tests/run/artifact_axmi` |
| `T766` | `E18.4` | `axiom-backend` | Embedded `.axmeta`/`.axlto` non-alloc COFF sections & container reader/writer in `compiler/artifact/container`, schema/target/checksum validation, final `.exe`/`.dll` stripping (`INV-ART-002`) | `tests/run/artifact_container` |
| `T767` | `E18.4` | `axiom-qa` | Artifact format, module interface (`.axmi`) & LTO section round-trip conformance suite (`INV-ART-003`) | `tests/conformance/p18/e18_4_artifacts` |
| `T768` | `E18.5` | `axiom-architect` | Canonical `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` (`PassContract`, `ProofCertificate`, 3-valued `Certainty`, `TranslationWitness`) | `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` |
| `T769` | `E18.5` | `axiom-semantics` | `PassContract` registry, `ProofCertificate` / `ProofProvenance` invalidation on IR mutation, 3-valued `Certainty` (`Proven`/`Possible`/`Unknown`), fail-closed rollback gate (`INV-PCT-001`) | `tests/run/pass_contracts` |
| `T770` | `E18.5` | `axiom-backend` | Per-function bounded `TranslationWitness` checker in `compiler/verify/translation_val` across MIR, `OptIR`, LIR, RegAlloc, and Scheduling (`INV-PCT-002`) | `tests/run/translation_val` |
| `T771` | `E18.5` | `axiom-qa` | Pass contracts, proof-carrying transformations & translation validation conformance suite (`INV-PCT-003`) | `tests/conformance/p18/e18_5_pass_contracts` |
| `T774` | `E18.6` | `axiom-architect` | Canonical `spec/SPEC-27-separate-compilation-linker-v2.md` (`LinkIR` separate compilation, multi-object/archive linking, `COMDAT`, section GC) | `spec/SPEC-27-separate-compilation-linker-v2.md` |
| `T067` | `E18.6` | `axiom-backend` | Linker v2: per-module `.obj` + `.axmi` separate compilation, `LinkIR` multi-object & `.lib` archive linking, cross-object relocation patching, demangled `AX_LINK_*` diagnostics (`INV-LNK-001`) | `tests/link2` |
| `T775` | `E18.6` | `axiom-backend` | Linker v2 per-item section subdivision, `IMAGE_SCN_LNK_COMDAT` generic/vtable deduplication, root-set mark-sweep `--gc-sections`, `inspect --emit=link-map` / `--emit=gc-sections` (`INV-LNK-002`) | `tests/run/link_section_gc` |
| `T776` | `E18.6` | `axiom-qa` | Separate compilation, multi-object archives, `COMDAT` deduplication, section GC & P18 exit conformance suite (`INV-LNK-003`) | `tests/conformance/p18/e18_6_separate_compilation` |
| `T318` | Gate | `axiom-qa` | Phase P18 gate — Compiler architecture 2.0 (certify all `E18.1`–`E18.7` exit criteria, 5,551 phase requirements, and full conformance index) | `tests/conformance/p18/README.md`, `_workspaces/reports/phase-P18-review.md` |

---

## 3. Directory-by-Directory Conformance Test Inventory

### 3.1 `e18_1_query_engine/` — E18.1 Query Engine & Demand-Driven Semantic Database (`SPEC-21`, `INV-QRY-001..003`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e18_1_query_engine_oracle.test` / `e18_1_query_engine_oracle.py` / `e18_1_query_engine_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler/query/db/mod.ax` and `compiler/query/engine/mod.ax` and executes across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`; verifies demand-driven isolation, `inspect --emit=query-graph`, Tarjan SCC cycle rotation, and snapshot-bound diagnostic replay |
| `demand_driven_isolation_and_memo.ax` | `run` (`interp`, `native`) | 3-module workspace (`core.math`, `core.app`, `core.unused`) across revisions `R1..R4`: unreferenced body skipping (`AXS-QRY-004`), warm memo hits (`AXS-QRY-012`), header/body firewall backdating (`AXS-QRY-033`), and multi-session `CompilerDB` isolation (`AXS-QRY-001`) |
| `cycle_recovery_and_cascade_suppression.ax` | `run` (`interp`, `native`) | All 5 cycle/depth diagnostic codes (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`), canonical `SemanticKey` rotation across all entry permutations (`AXS-QRY-022`), and cascade suppression on `Poisoned` recovery values (`AXS-QRY-023`, `AXS-QRY-031`) |
| `snapshot_diag_replay_and_invalidation.ax` | `run` (`interp`, `native`) | `RevisionSnapshot` immutability, cold (`R1`) vs warm (`R2`, `R3`) byte-for-byte diagnostic replay (`AXS-QRY-030`), and cycle-breaking edit (`R4`) clearing `Poisoned` slots back to `Ready` (`AXS-QRY-032`) |
| `lollipop_cycle_and_multihop_backdate.ax` | `run` (`interp`, `native`) | QA boundary check: lollipop stem-into-cycle (`Entry -> Stem -> A -> B -> A`) isolating cycle diagnostic strictly to `[A, B, A]` while poisoning `Stem`/`Entry` without secondary cascades, plus 4-hop diamond early-cutoff backdating |

### 3.2 `e18_2_incremental/` — E18.2 Incremental Compilation & Multi-Tier Fingerprinting (`SPEC-22`, `INV-INC-001..003`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e18_2_incremental_oracle.test` / `e18_2_incremental_oracle.py` / `e18_2_incremental_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler/query/db/mod.ax`, `compiler/incremental/fingerprint/mod.ax`, and `compiler/incremental/cache/mod.ax` across 11 incremental revisions in `--interp` and `-O0`/`-O1`/`-O2 --verify-each`; verifies `.axiom-cache/dep-graph.axcache` (`AXCACHE1`), atomic publication, corruption fallback, `< 100 ms` no-op rebuild, Private-Body Firewall, and byte-for-byte clean equivalence |
| `noop_rebuild_under_100ms.ax` | `run` (`interp`, `native`) | 5-tier domain-separated BLAKE3-128 fingerprints (`AXS-INC-001..002`), `EnvironmentDigest` flag/target binding (`AXS-INC-021`), `< 100 ms` warm no-op fast path (`queries_recomputed=0`, `modules_typechecked=0`, `cgu_rebuilt=0`), `touch` `mtime` invariance, comment/whitespace `AstFingerprint` backdating, and `AXCACHE1` corruption recovery (`AXS-INC-022..023`) |
| `edit_one_private_fn_firewall.ax` | `run` (`interp`, `native`) | 4-module workspace across private body edit, non-`@inline` `pub fn` body edit, and private helper addition: proves `modules_typechecked == 1` (`0` downstream modules re-typechecked), `cgu_rebuilt == 1`, `cgu_reused == 3`, and byte-identical output to `--no-incremental` (`AXS-INC-012`) |
| `sig_const_generic_invalidation_and_clean_equiv.ax` | `run` (`interp`, `native`) | Selective invalidation for unchanged vs changed `pub const` values, `@inline` and generic `pub fn<T>` body edits (`0` downstream `typeck`, targeted `cgu_rebuilt`), public signature / `@repr(C)` layout changes (`AXS-INC-003..004`), and error non-pollution (`AXS-INC-024`) |

### 3.3 `e18_3_parallel/` — E18.3 Parallel Compilation & Deterministic DAG Scheduling (`SPEC-23`, `INV-PAR-001..003`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e18_3_parallel_oracle.test` / `e18_3_parallel_oracle.py` / `e18_3_parallel_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler/parallel/scheduler/mod.ax`, `compiler/parallel/codegen/mod.ax`, and `compiler/incremental/*`; verifies identical stdout, exit code `0`, `AXCACHE1` headers, COFF `.obj` headers (`TimeDateStamp = 0`), and byte-identical PE32+ executables across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each` |
| `jobs_1_2_4_8_byte_identical_artifacts_and_ir.ax` | `run` (`interp`, `native`) | `(ModuleId, LocalIndex)` `ScopedDefId`/`ScopedHirId` invariance (`AXS-PAR-004`), 64-shard `ShardedInterner` (`AXS-PAR-005`), and byte-identical HIR/MIR/LIR dumps, per-`CGU` `.obj` files, and linked `.exe` artifacts across `--jobs 1`, `2`, `4`, `8` and all 6 schedule modes (`AXS-PAR-001`, `AXS-PAR-020..024`) |
| `randomized_delay_multifile_diag_and_cycles.ax` | `run` (`interp`, `native`) | `AXD-060` post-join diagnostic sorting across 5 randomized worker completion schedules (`forward`, `reverse`, `interleaved`, `burst-delayed`, `starvation-skewed`), `SingleFlightLatch` deduplication (`AXS-PAR-010`), and cross-worker `WaitForGraph` cycle detection & canonical rotation (`AXS-PAR-011`) |
| `parallel_incremental_hybrid_determinism.ax` | `run` (`interp`, `native`) | Combined `--jobs 2/4/8` + incremental cache reuse (`AXS-PAR-022`), worker/resource fault retry, corrupt artifact checksum quarantine (`AXS-PAR-015`), and `LinkBarrier`/`PackageBarrier`/`SigningBarrier` gating (`AXS-PAR-024`) |

### 3.4 `e18_4_artifacts/` — E18.4 Canonical Artifact Format & `.axmi` Module Interfaces (`SPEC-24`, `INV-ART-001..003`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e18_4_artifacts_oracle.test` / `e18_4_artifacts_oracle.py` / `e18_4_artifacts_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler/artifact/axmi` and `compiler/artifact/container` AND executes real `axiomc2` multi-module CLI builds (`--emit=obj --emit=axmi`) with upstream `.ax` source files deleted before linking downstream consumer modules |
| `multimodule_axmi_axmeta_generics_traits_caps_consts.ax` | `run` (`interp`, `native`) | 3-module chain (`core_math -> algo_lib -> app_main`) compiled source-free via `.axmi` across `pub const`, `@repr(C)` layouts, traits/impls, ownership/capability/effect summaries (`FnContractSummary`), and verified generic MIR templates (`AXS-ART-010..013`) |
| `byte_identical_axmi_obj_and_lto_roundtrip.ax` | `run` (`interp`, `native`) | Byte-identical `.axmi`, `.obj` (`.axmeta`, `.axmir`, `.axlto`), and `.axpkg` emission across repeated runs and permuted declaration orders, LTO cross-module generic instantiation/inlining, and mandatory stripping of `.axmeta`/`.axmir`/`.axlto` from final `.exe`/`.dll` (`AXS-ART-002..004`, `AXS-ART-021..022`) |
| `negative_diag_version_target_and_corrupt_payloads.ax` | `run` (`interp`, `native`) | Fail-closed diagnostics (`AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`) on corrupt magic/checksum, unsupported `schema_version`, unknown required vs optional sections (`AXS-ART-005`), target/ABI/panic mismatch, and unverified generic MIR |
| `cross_module_freshness_invalidation_and_archive_seam.ax` | `run` (`interp`, `native`) | `.axmi` freshness preservation on private body edits vs targeted invalidation on API/ABI/layout/`const`/capability/generic template changes (`AXS-ART-014`), plus mixed COFF `.lib` archives combining Axiom `.obj` (with `.axmeta`) and foreign C `.obj` members (`AXS-ART-022`) |

### 3.5 `e18_5_pass_contracts/` — E18.5 Pass Contracts, Proof-Carrying IR & Translation Validation (`SPEC-25`, `INV-PCT-001..003`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e18_5_conformance.test` / `e18_5_conformance_oracle.py` / `e18_5_conformance_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler.mir.mir`, `compiler.verify.pass_contracts`, and `compiler.verify.translation_val` across `-O0`, `-O1`, and `-O2 --verify-each`; verifies `--verify-pass-contracts`, `--validate-translations`, `inspect --emit=pass-witness`, fail-closed rollback on `Possible`/`Unknown` obligations, and deterministic rejection of synthetic pass bugs |
| `overflow_and_signed_unsigned_polarity.ax` (+ `o2_*`) | `run` (`interp`, `native`, `-O2`) | Checked vs wrapping arithmetic, `ShiftInRange`, congruence-proven `NonZero` division, signed vs unsigned comparison/division/shift polarity (`REQ-CORE-3268`), 128-bit carry chains, and fail-closed rollback on `Certainty.Unknown` divisors (`AXS-PCT-010`, `AXS-PCT-014`, `AXS-PCT-021`) |
| `drop_capability_and_effect_barriers.ax` (+ `o2_*`) | `run` (`interp`, `native`, `-O2`) | LIFO `Drop` ordering across scopes/early returns, `view`/`mut_view` capability exclusivity across SROA/DSE/load-forwarding, and multi-category `EffectSummary` preservation of impure calls with unused return values (`AXS-PCT-013`, `AXS-PCT-021`) |
| `volatile_atomic_and_schedule_invariants.ax` (+ `o2_*`) | `run` (`interp`, `native`, `-O2`) | `volatile`/MMIO load-store ordering barriers, `atomic` synchronization barriers, raw-pointer conservative aliasing, high-pressure register allocation (`RCX` shifts, `RAX:RDX` `idiv`) witness validation (`AXS-PCT-022`), and `RAW`/`WAR`/`WAW`/`EFLAGS` instruction scheduling validation (`AXS-PCT-023`) |
| `final_machine_ir_and_frame_reproducibility.ax` (+ `o2_*`) | `run` (`interp`, `native`, `-O2`) | Final Machine IR 3.0 gate (`AXS-PCT-024`): Win64 8-arg calls, 16-byte `RSP` alignment, dynamic frame indexing, shrink-wrap + unwind `Drop` guards, and `Secret<T>` zeroization barrier preservation |
| `boundary_cfg_diamond_and_loop_drop_guards.ax` (+ `o2_*`) | `run` (`interp`, `native`, `-O2`) | QA boundary check: nested diamond CFG join `phi` invariants, zero-trip vs multi-trip loop `Drop` guard ordering, and range/bitmask symbolic proof boundaries |

### 3.6 `e18_6_separate_compilation/` — E18.6 Separate Compilation, `LinkIR`, `COMDAT` & Section GC (`SPEC-27`, `INV-LNK-001..003`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e18_6_separate_compilation_oracle.test` / `e18_6_separate_compilation_oracle.py` / `e18_6_separate_compilation_probe.ax.in` | `cmd` + live compiler probe | Bundles `compiler.link.gc` AND runs real `axiomc2` multi-module `.obj` + `.axmi` + `.lib` + `.dll` separate builds vs whole-workspace builds, verifying byte-identical `.exe` output, single-module incremental `.obj` rebuilds, `< 100 ms` warm no-op budget, and `--json` linker diagnostics |
| `separate_vs_whole_workspace_equivalence.ax` | `run` (`interp`, `native`) | Canonical topological `.obj`/`.lib`/`.dll` input ordering (`AXS-LNK-003`), `Strong`/`Weak`/`Local`/`Import` resolution (`AXS-LNK-012`), cross-object `REL32`/`ADDR64`/`ADDR32NB`/`SECREL`/`SECTION` relocation patching (`AXS-LNK-024`), and separate vs whole-workspace equivalence (`AXS-LNK-002`) |
| `comdat_generic_vtable_archive_and_section_gc.ax` | `run` (`interp`, `native`) | Per-item section subdivision (`.text$<sym>`, `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>`, `.pdata$<sym>`, `.xdata$<sym>`), `IMAGE_SCN_LNK_COMDAT` generic/vtable deduplication (`AXS-LNK-013`), fixed-point `.lib` extraction, root-set `--gc-sections` (`@entry`, `@export`, `@used`, `@at`, `ModuleInit`, `Reflection`), forward `.pdata`/`.xdata` unwind sweeping (`AXS-LNK-020..023`), and `inspect --emit=link-map` / `--emit=gc-sections` |
| `incremental_single_obj_rebuild_and_noop_budget.ax` | `run` (`interp`, `native`) | Private-Function Body Firewall for separate `.obj` + `.axmi` builds (`modules_typechecked=1`, `cgu_rebuilt=1`, `cgu_reused=3`, downstream `.axmi` backdated to `Green`) and `< 100 ms` no-op rebuild on the compiler workspace (`AXS-LNK-002`, `INV-LNK-003`) |
| `negative_linker_diags_abi_comdat_and_wx.ax` | `run` (`interp`, `native`) | Structured diagnostics and verifier gates: `AX_LINK_UNDEFINED_SYMBOL` (with `_AX1_` demangling to dotted Axiom path), `AX_LINK_DUPLICATE_SYMBOL` (strong collision + COMDAT mismatch), `AX_LINK_ABI_MISMATCH`, `AX_LINK_WX_VIOLATION`, `AX_LINK_DANGLING_RELOC`, and `AX_LINK_RELOC_OUT_OF_RANGE` (`AXS-LNK-005`, `AXS-LNK-014`, `AXS-LNK-024..025`) |
| `README.md` | Doc | Detailed E18.6 rule-by-rule traceability matrix for `SPEC-27` (`AXS-LNK-001..053`) |

### 3.7 `e18_7_windows_artifacts/` — E18.7 Windows x64 `.lib`, `.dll`, Import `.lib` & GNU `ld` Cross-Linking (`SPEC-26`, `INV-WLIB-001..003`)

| File | Kind | Coverage Summary |
|---|---|---|
| `e18_7_static_lib_conformance.test` / `e18_7_static_lib_oracle.py` | `cmd` + binary oracle | Validates `axiomc build --kind lib` COFF archives (`!<arch>\n`, big-endian 1st & little-endian 2nd `/` linker members, `//` longnames, `Date="0"`, `TimeDateStamp=0`), bidirectional Axiom/GCC `.lib` consumption, fixed-point dead-member exclusion, post-layout `.pdata` RVA patching (`REQ-LNK-120`), and `AX_DRIVER_INVALID_ARTIFACT_KIND` / `AX_LINK_BAD_ARCHIVE` / `AX_LINK_DUPLICATE_SYMBOL` / `AX_LINK_UNDEFINED_SYMBOL` |
| `e18_7_pe_dll_import_conformance.test` / `e18_7_pe_dll_import_oracle.py` | `cmd` + binary oracle | Validates `axiomc build --kind dll` PE32+ DLLs (`IMAGE_FILE_DLL=0x2000`, `ImageBase=0x180000000`, `DYNAMIC_BASE`, sorted `.edata`, multi-page `.reloc` `IMAGE_REL_BASED_DIR64`, `W^X`), companion COFF short-import `.lib` (`Sig1=0x0000, Sig2=0xFFFF`), `REQ-LNK-113..119` IAT/ILT/RIP-relative `FF 25` verification, forced base relocation via `VirtualAlloc` + `LoadLibraryA`/`GetProcAddress`, and `_DllMainCRTStartup` (`__ax_resolve_module_bindings()` + `@entry`) |
| `e18_7_gnu_ld_crosslink_conformance.test` / `e18_7_gnu_ld_crosslink_oracle.py` | `cmd` + cross-link oracle | Certifies `ADR-0034` §4 OI-07b & `SPEC-26` `AXS-WLIB-032`: `--rt-obj` (`axiom_rt.obj`), `--kind obj` / `--emit=obj` standard `__imp_<sym>` symbols (zero internal `__IAT_*` leaks), and multi-artifact cross-linking (`--kind obj` + `--kind lib` + `--kind dll` + C `.obj`) via standalone GNU `ld` and `gcc -nostdlib` at `-O0` and `-O2` |
| `fn_ptr_calling_conv_abi.ax` (+ `o2_*`) | `run` (`interp`, `native`, `-O2`) | Calling convention (`""`, `"C"`, `"system"`) and `unsafe` identity in function-pointer types (`REQ-LNK-121`), >4-arg Win64 stack-slot calls (`[RSP+0x20]`, `[RSP+0x28]`), and non-capturing closure-to-`fn` coercion |
| `export_visibility_and_abi_layout.ax` (+ `o2_*`) | `run` (`interp`, `native`, `-O2`) | `@export` and `@export("custom_name")` vs unexported `pub`/private items, UTF-8 `Str` fat pointers (`"Xin chào thế giới\n"`), and LIFO `Drop` ordering |
| `qa_e18_7_export_fn_ptr_boundary.ax` (+ `o2_*`) | `run` (`interp`, `native`, `-O2`) | QA boundary check: exported functions returning and accepting `extern "C"` / `extern "system"` function pointers across 6-argument Win64 stack boundaries |
| `ui_duplicate_export.ax`, `ui_generic_export.ax`, `ui_fn_ptr_unsafe_mismatch.ax` | `ui` | Negative compile-time diagnostics: duplicate `@export` symbol name, `@export` on uninstantiated generic function, and `unsafe fn` to safe `fn` pointer mismatch |

---

## 4. Running the Phase 18 Conformance Suite

From an isolated task snapshot (e.g., `build-snap-T318`) with `-j 1`:

```bash
python build-snap-T318/tools/axtest.py -j 1 \
  --root build-snap-T318 \
  --build-dir build-snap-T318/build \
  --compiler build-snap-T318/build/axiomc2.exe \
  conformance/p18 link2 \
  run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax
```

Expected result: `WEAK-NATIVE 0`, `0 FAIL`, `0 SKIP`, `0 XFAIL`.
