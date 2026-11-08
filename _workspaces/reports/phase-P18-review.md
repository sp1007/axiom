# Phase Review — `P18-compiler-architecture-2-0` (Compiler Architecture 2.0)

## Tóm tắt

Báo cáo thẩm định kiến trúc khi hoàn tất trọn vẹn **Phase 18 (`P18-compiler-architecture-2-0` — Compiler Architecture 2.0)** tại cổng kiểm định `T318`:
1. **Hoàn thành 28/28 task thực thi và đặc tả của `P18-compiler-architecture-2-0` (`T067`, `T750`–`T776`, cùng task lập kế hoạch `T218`)**: Toàn bộ 7 epic (`E18.1`–`E18.7`) trong `spec/ROADMAP.md` §3 và 7 đặc tả chuẩn (`SPEC-21` đến `SPEC-27`) đã được hiện thực hóa hoàn toàn bằng Axiom trong `compiler/` và chứng nhận qua bộ kiểm thử hợp chuẩn `tests/conformance/p18/`:
   - **`E18.1` (`SPEC-21`, `T752`–`T755`, `INV-QRY-001..003`)**: Cơ sở dữ liệu ngữ nghĩa hướng cầu (`CompilerDB`), tách biệt bảng đầu vào bất biến theo `RevisionId` và bảng suy dẫn thuần túy, tự động ghi nhận đồ thị phụ thuộc (`QueryStack` / `--emit=query-graph`), phát hiện chu trình Tarjan kèm xoay chuẩn hóa theo `SemanticKey` độc lập thứ tự gọi (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`), giá trị phục hồi chống lỗi dây chuyền và phát lại chẩn đoán gắn với ảnh chụp (`SnapshotId`).
   - **`E18.2` (`SPEC-22`, `T756`–`T759`, `INV-INC-001..003`)**: Biên dịch tăng dần với hệ thống dấu vân tay 128-bit BLAKE3 đa tầng (`Source`, `Ast`, `Interface`/`Abi`, `Body`, `Codegen`), thuật toán lan truyền đỏ-xanh `try_mark_green`, tường lửa thân hàm riêng tư (`edit-one-private-fn` chỉ kiểm tra kiểu lại đúng module đó, `0` truy vấn `typeck` hạ lưu chạy lại), bộ nhớ đệm bền vững `.axiom-cache` (`AXCACHE1`) xuất bản nguyên tử và đường nhanh biên dịch lại không thay đổi (no-op rebuild) **dưới `< 100 ms`** trên chính trình biên dịch.
   - **`E18.3` (`SPEC-23`, `T760`–`T763`, `INV-PAR-001..003`)**: Biên dịch song song tất định (`--jobs 1` == `--jobs 2` == `--jobs 4` == `--jobs 8`), chia sẻ ảnh chụp `DatabaseSnapshot` bất biến, định danh `(ModuleId, LocalIndex)` độc lập thứ tự luồng, bảng intern phân mảnh 64-shard, khử trùng lặp `SingleFlightLatch` + phát hiện chu trình xuyên worker trên `WaitForGraph`, lập lịch DAG đánh cắp việc và sinh mã song song theo từng `CodegenUnit` (`CGU`) tạo ra tệp `.obj`/`.exe`, bản in HIR/MIR/LIR và luồng chẩn đoán `AXD-060` đồng nhất từng byte.
   - **`E18.4` (`SPEC-24`, `T764`–`T767`, `INV-ART-001..003`)**: Chuẩn định dạng thành phẩm nhị phân không con trỏ (`ArtifactHeader` 64-byte, `SectionDescriptor`), tệp giao diện mô-đun `.axmi` (chứa chữ ký `pub`, DAG `TypeId`, trait/impl, tóm tắt quyền sở hữu/capability/hiệu ứng, giá trị `const` và mẫu `Verified MIR` cho hàm tổng quát) cho phép biên dịch riêng rẽ không cần tệp nguồn `.ax` thượng nguồn, cùng các phân đoạn nhúng `.axmeta`/`.axmir`/`.axlto` tự động được lược bỏ khỏi `.exe`/`.dll` cuối cùng.
   - **`E18.5` (`SPEC-25`, `T768`–`T771`, `INV-PCT-001..003`)**: Hợp đồng pha biên dịch (`PassContract`), chứng chỉ biến đổi mang bằng chứng (`ProofCertificate` / `ProofProvenance`) tự động vô hiệu hóa khi `ir_revision` thay đổi, cổng đóng an toàn (fail-closed rollback) trên dàn độ chắc chắn 3 giá trị (`Proven` / `Possible` / `Unknown`), phân tích luồng dữ liệu/hiệu ứng/biểu tượng nội bộ không phụ thuộc SMT ngoài, và bộ kiểm chứng dịch thuật hữu hạn (`TranslationWitness`) từ MIR → `OptIR` → LIR → cấp phát thanh ghi → lập lịch lệnh → mã máy cuối (`--verify-pass-contracts`, `--validate-translations`, `inspect --emit=pass-witness`).
   - **`E18.6` (`SPEC-27`, `T774`, `T067`, `T775`, `T776`, `INV-LNK-001..003`)**: Biên dịch riêng rẽ từng mô-đun (`.obj` + `.axmi`), trình liên kết `LinkIR` đa đối tượng và kho lưu trữ `.lib`, giải mã tên `_AX1_` không mất thông tin trong chẩn đoán `AX_LINK_*`, chia nhỏ phân đoạn theo từng hàm/dữ liệu (`.text$<sym>`, `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>`), khử trùng lặp thực thể tổng quát và vtable qua `IMAGE_SCN_LNK_COMDAT`, và thu gom rác phân đoạn (`--gc-sections`) theo tập gốc khả đạt kèm liên kết nhân quả `.pdata`/`.xdata`.
   - **`E18.7` (`SPEC-26`, `T772`, `T750`, `T751`, `T773`, `INV-WLIB-001..003`, `REQ-OWNER-006`)**: Đầy đủ các loại thành phẩm Windows x64 (`--kind exe|obj|lib|dll`), trình đọc/ghi thư viện tĩnh COFF `.lib` tất định (`!<arch>\n`, trích xuất điểm bất động), xuất PE32+ `.dll` (`.edata`, `_DllMainCRTStartup` gọi `__ax_resolve_module_bindings()`, `.reloc` hỗ trợ ASLR), thư viện nhập khẩu ngắn COFF `.lib` (`Sig1=0x0000, Sig2=0xFFFF`), và liên kết chéo trực tiếp đầu ra `--emit=obj` bằng GNU `ld`/`gcc` qua quy ước `__imp_<name>` và `axiom_rt.obj` (`ADR-0034` §4 OI-07b).
2. **Độ phủ yêu cầu và kiểm chứng toàn cục**: Toàn bộ **5.551 yêu cầu** ánh xạ vào `P18-compiler-architecture-2-0` đều đạt trạng thái `done`; `reqcov.py --strict` báo cáo `gaps: 0` (`COVERAGE OK`); `archcheck.py` quét 196 tệp nguồn với `0 violations`; `harness_check.py` đạt `HARNESS OK`; toàn bộ 21 bất biến của P18 (`INV-QRY-001..003`, `INV-INC-001..003`, `INV-PAR-001..003`, `INV-ART-001..003`, `INV-PCT-001..003`, `INV-WLIB-001..003`, `INV-LNK-001..003`) và bộ kiểm thử `conformance/p18` + `link2` + canary vượt qua 100% với `WEAK-NATIVE 0`, `0 FAIL`.

---

## 1. Phase 18 (`P18-compiler-architecture-2-0`) Completion Summary

- **Phase Tasks**: All `28 / 28` implementation, specification, and epic conformance tasks (`T067`, `T750`–`T776`) plus planning task `T218` are `done` and verified via QA gates.
- **Canonical Specifications Delivered (`SPEC-21`–`SPEC-27`)**:
  - `spec/SPEC-21-query-engine-semantic-db.md` (`T752`): `AXS-QRY-001..053` (`INV-QRY-001..003`).
  - `spec/SPEC-22-incremental-compilation.md` (`T756`): `AXS-INC-001..053` (`INV-INC-001..003`).
  - `spec/SPEC-23-parallel-compilation.md` (`T760`): `AXS-PAR-001..053` (`INV-PAR-001..003`).
  - `spec/SPEC-24-artifact-format-module-interfaces.md` (`T764`): `AXS-ART-001..053` (`INV-ART-001..003`).
  - `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` (`T768`): `AXS-PCT-001..053` (`INV-PCT-001..003`).
  - `spec/SPEC-26-windows-artifact-kinds.md` (`T772`): `AXS-WLIB-001..053` (`INV-WLIB-001..003`).
  - `spec/SPEC-27-separate-compilation-linker-v2.md` (`T774`): `AXS-LNK-001..053` (`INV-LNK-001..003`).

---

## 2. Epic Exit-Criterion Verification (`E18.1`–`E18.7`)

### 2.1 `E18.1` — Query Engine & Demand-Driven Semantic Database (`SPEC-21`, `T752`–`T755`)
- **Subsystems**: `compiler/query/db/mod.ax`, `compiler/query/engine/mod.ax`.
- **Exit Criteria Certified**:
  - Strict separation between revision-stamped input tables (`source_file_input`, `module_tree_input`, `target_config_input`, `package_graph_input`) and pure derived queries (`parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `typeck_body`, `trait_solve`, `const_eval`, `mir_body`, `layout_of`) with zero process-global mutable state (`INV-QRY-001`).
  - Demand-driven evaluation with header/body firewall (`typeck_body(caller)` queries `item_signature(callee)` and skips unreferenced function bodies) and deterministic `inspect --emit=query-graph` sorted by `(QueryKind, SemanticKey)`.
  - Active-stack Tarjan cycle detection with canonical `SemanticKey` rotation so cycle diagnostics (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`) are order-independent, paired with poisoned recovery values (`ErrorType`, `ConstValue.Poisoned`, `TraitResult.Error`) that suppress secondary cascading errors and snapshot-bound diagnostic replay on warm hits (`INV-QRY-002`, `INV-QRY-003`).
- **Verification Suite**: `tests/run/query_db`, `tests/run/query_cycles`, `tests/conformance/p18/e18_1_query_engine` (`PASS`, `0 WEAK-NATIVE`).

### 2.2 `E18.2` — Incremental Compilation, Multi-Tier Fingerprints & `< 100 ms` No-Op Rebuild (`SPEC-22`, `T756`–`T759`)
- **Subsystems**: `compiler/incremental/fingerprint/mod.ax`, `compiler/incremental/cache/mod.ax`.
- **Exit Criteria Certified**:
  - Domain-separated 128-bit BLAKE3 fingerprints across `SourceFingerprint`, whitespace/comment-insensitive `AstFingerprint`, `InterfaceFingerprint` + `AbiFingerprint`, `Verified MIR` `BodyFingerprint`, and monomorphized `CodegenFingerprint` (`INV-INC-001`).
  - Red-Green `try_mark_green` dependency verification and backdating enforcing the **Private-Body Firewall**: editing a private function (or non-`@inline` `pub fn` body) re-typechecks only that module (`modules_typechecked = 1`, `0` downstream `typeck` queries re-run, `cgu_rebuilt = 1`).
  - Versioned, BLAKE3-checksummed persistent cache (`.axiom-cache/dep-graph.axcache`, magic `"AXCACHE1"`) with atomic temp-file + rename publication, transparent fallback on corruption/schema mismatch, hermetic `EnvironmentDigest` binding, **`< 100 ms` warm no-op rebuild** on the compiler workspace (`queries_recomputed = 0`, `modules_typechecked = 0`, `cgu_rebuilt = 0`), and byte-for-byte identity against clean `--no-incremental` builds (`INV-INC-002`, `INV-INC-003`).
- **Verification Suite**: `tests/run/incremental_fingerprint`, `tests/run/incremental_cache`, `tests/conformance/p18/e18_2_incremental` (`PASS`, `0 WEAK-NATIVE`).

### 2.3 `E18.3` — Parallel Compilation & Thread-Count-Independent Determinism (`SPEC-23`, `T760`–`T763`)
- **Subsystems**: `compiler/parallel/scheduler/mod.ax`, `compiler/parallel/codegen/mod.ax`.
- **Exit Criteria Certified**:
  - Immutable `DatabaseSnapshot` sharing across worker threads with per-worker arenas, module-scoped `(ModuleId, LocalIndex)` semantic IDs (`ScopedDefId`, `ScopedHirId`), and 64-shard content-addressed string/type interning (`INV-PAR-001`).
  - In-flight query deduplication via `SingleFlightLatch`, deadlock-free cross-worker `WaitForGraph` cycle detection with canonical `SemanticKey` rotation, and critical-path / resource-token (`cpu_tokens`, `memory_bytes`) work-stealing DAG scheduling across all 6 schedule modes (`Interactive`, `Balanced`, `Throughput`, `MemoryBound`, `LowPower`, `DeterministicDebug`).
  - Parallel per-`CGU` LIR lowering, register allocation, machine encoding, and COFF `.obj` emission integrated with `.axiom-cache`, post-join `AXD-060` diagnostic sorting under arbitrary worker delays, and byte-for-byte identical `.obj`, `.exe`, and HIR/MIR/LIR dumps across `--jobs 1`, `--jobs 2`, `--jobs 4`, and `--jobs 8` (`INV-PAR-002`, `INV-PAR-003`).
- **Verification Suite**: `tests/run/parallel_scheduler`, `tests/run/parallel_codegen`, `tests/conformance/p18/e18_3_parallel` (`PASS`, `0 WEAK-NATIVE`).

### 2.4 `E18.4` — Canonical Artifact Format & `.axmi` Module Interfaces (`SPEC-24`, `T764`–`T767`)
- **Subsystems**: `compiler/artifact/axmi/mod.ax`, `compiler/artifact/container/mod.ax`.
- **Exit Criteria Certified**:
  - Pointer-free, timestamp-free 64-byte `ArtifactHeader` (`"AXMI0001"`, `"AXMETA01"`, `"AXLTO001"`, `"AXMIR001"`, `"AXPKG001"`) and 48-byte `SectionDescriptor` table with BLAKE3-128 `content_hash` and checked 64-bit bounds (`INV-ART-001`).
  - Source-free downstream compilation via `<module>.axmi` (`--emit=axmi`, `inspect --axmi`): populates `CompilerDB` with exported signatures, self-contained `TypeId` DAG, trait/impl tables, `FnContractSummary` ownership/capability/effect/panic contracts, evaluated `const` values, and pre-verified generic/`@inline`/`comptime` MIR templates without reading upstream `.ax` source files.
  - Non-alloc discardable `.axmeta`, `.axmir`, and `.axlto` (`IMAGE_SCN_LNK_INFO | IMAGE_SCN_MEM_DISCARDABLE`) sections embedded in `.obj`/`.lib`, validated at link time (`AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`), and stripped from final `.exe` and `.dll` images (`INV-ART-002`, `INV-ART-003`).
- **Verification Suite**: `tests/run/artifact_axmi`, `tests/run/artifact_container`, `tests/conformance/p18/e18_4_artifacts` (`PASS`, `0 WEAK-NATIVE`).

### 2.5 `E18.5` — Pass Contracts, Proof-Carrying Transformations & Translation Validation (`SPEC-25`, `T768`–`T771`)
- **Subsystems**: `compiler/verify/pass_contracts/mod.ax`, `compiler/verify/translation_val/mod.ax`.
- **Exit Criteria Certified**:
  - Static `PassContract` descriptors for compiler passes, `ProofCertificate` / `ProofProvenance` tracking bound to `ir_revision` with automatic transitive invalidation on IR mutation, and a strict semantic firewall separating profitability (`CostModel` / PGO) from legality proofs (`INV-PCT-001`).
  - Three-valued static certainty lattice (`Proven` / `Possible` / `Unknown`) across `Source Analysis 2.0`, multi-category `EffectSummary` (`Effect System 2.0`), and in-process `Symbolic Execution 2.0` (zero external SMT dependency), rolling back any candidate transformation whose proof obligation is `Possible` or `Unknown`.
  - Per-function bounded `TranslationWitness` validation (`--verify-pass-contracts`, `--validate-translations`, `inspect --emit=pass-witness`) across MIR/`OptIR` scalar/CFG/memory/loop passes, register allocation live-range/spill witnesses, instruction scheduling `RAW`/`WAR`/`WAW` + `volatile`/`atomic`/`trap` barriers, and `FinalMachineIr` frame/unwind invariants across `-O0`, `-O1`, and `-O2` (`INV-PCT-002`, `INV-PCT-003`).
- **Verification Suite**: `tests/run/pass_contracts`, `tests/run/translation_val`, `tests/conformance/p18/e18_5_pass_contracts` (`PASS`, `0 WEAK-NATIVE`).

### 2.6 `E18.6` — Separate Compilation, Multi-Object Archives, `COMDAT` & Section GC (`SPEC-27`, `T774`, `T067`, `T775`, `T776`)
- **Subsystems**: `compiler/link/`, `compiler/link/gc/mod.ax`, `compiler/obj/`.
- **Exit Criteria Certified**:
  - Per-module separate compilation (`<module>.obj` + `<module>.axmi`), format-neutral `LinkIR`, deterministic topological object/archive input ordering, `Strong` / `Weak` / `Local` / `Import` symbol resolution, range-checked `REL32` / `ADDR64` / `ADDR32NB` / `SECREL` / `SECTION` relocation patching, and structured linker diagnostics (`AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_ABI_MISMATCH`) carrying lossless demangled dotted Axiom paths (`data.demangled`) and `.axmeta` source spans (`INV-LNK-001`).
  - Per-item section subdivision (`.text$<sym>`, `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>`, associative `.pdata$<sym>` / `.xdata$<sym>`), `IMAGE_SCN_LNK_COMDAT` deduplication (`Any`, `SameSize`, `ExactMatch`, `Largest`, `Associative`) for generic instantiations and vtables, root-set mark-sweep section GC (`--gc-sections` from `@entry`, `@export`, `@used`, `@at`, `ModuleInit`, `Reflection`) with forward unwind sweeping, and deterministic `inspect --emit=link-map` / `--emit=gc-sections` (`INV-LNK-002`, `INV-LNK-003`).
- **Verification Suite**: `tests/link2`, `tests/run/link_section_gc`, `tests/conformance/p18/e18_6_separate_compilation` (`PASS`, `0 WEAK-NATIVE`).

### 2.7 `E18.7` — Windows x64 Artifact Kinds: Static `.lib`, PE32+ `.dll` & Import `.lib` (`SPEC-26`, `T772`, `T750`, `T751`, `T773`)
- **Subsystems**: `compiler/obj/`, `compiler/link/`, `compiler/driver/`.
- **Exit Criteria Certified**:
  - Owner requirement `REQ-OWNER-006`: `--kind exe|obj|lib|dll` (`--emit=obj` alias, `--implib <path>`), deterministic COFF `.lib` archive writer/reader (`!<arch>\n`, big-endian 1st and little-endian 2nd linker members, `//` longnames, `Date = 0`, `TimeDateStamp = 0`), and demand-driven fixed-point archive extraction (`-l<name>`, `-L<dir>`, `@link("<name>")`) excluding unreferenced members (`INV-WLIB-001`).
  - PE32+ `.dll` emission (`IMAGE_FILE_DLL = 0x2000`, `ImageBase = 0x180000000`, `DYNAMIC_BASE`), lexicographically sorted `.edata` Export Directory for `@export` / `@export("custom_name")` items, synthesized `_DllMainCRTStartup` invoking `__ax_resolve_module_bindings()` (`SPEC-56`) and module initializers, multi-page `.reloc` (`IMAGE_REL_BASED_DIR64`) verified under forced non-preferred base relocation, and companion COFF short-import `.lib` (`IMPORT_OBJECT_HEADER`, `Sig1 = 0x0000`, `Sig2 = 0xFFFF`) (`INV-WLIB-002`).
  - `ADR-0034` §4 OI-07b independent GNU `ld` / `gcc` cross-linking of `--kind obj` (`--emit=obj`) output using standard `__imp_<name>` IAT symbols and linkable runtime object `axiom_rt.obj` (`--rt-obj`) (`INV-WLIB-003`).
- **Verification Suite**: `tests/link/lib`, `tests/link/dll`, `tests/conformance/p18/e18_7_windows_artifacts` (`PASS`, `0 WEAK-NATIVE`).

---

## 3. Governance, Traceability & Quality Gate Evidence

1. **Phase 18 Conformance & Linker Suite (`axtest.py -j 1`)**:
   - Command:
     ```bash
     python build-snap-T318/tools/axtest.py -j 1 --root build-snap-T318 --build-dir build-snap-T318/build --compiler build-snap-T318/build/axiomc2.exe conformance/p18 link2 run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax
     ```
   - Result: `WEAK-NATIVE 0`, `TOTAL 111 PASS 111 FAIL 0 SKIP 0 XFAIL 0` (exit `0`).
2. **Requirements Coverage (`reqcov.py`)**:
   - Command: `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P18-compiler-architecture-2-0`
   - Result: All `5,551` requirement mappings in `P18-compiler-architecture-2-0` across `T067` and `T750`–`T776` are `done` (`0` planned/todo remaining in P18).
   - Command: `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`
   - Result:
     - `requirements: 32308`
     - `v1-core: implemented=5864`
     - `v1-full: implemented=6565 planned=2266`
     - `post-v1: epic=17535 planned=78`
     - `gaps: 0` — **`COVERAGE OK`** (exit `0`).
3. **Architecture Layer Check (`archcheck.py`)**:
   - Command: `python tools/archcheck.py`
   - Result: `archcheck: 196 files scanned, 0 violations` (exit `0`).
4. **Harness & Freeze Integrity Check (`harness_check.py`)**:
   - Command: `python .claude/skills/axiom-tasks/scripts/harness_check.py`
   - Result: `HARNESS OK` (exit `0`; `bootstrap/axiom0` remains untouched since `axiom0-frozen`).

---

## 4. Spec Drift, Shortcuts to Retire & Follow-Ups for `axiom-architect`

- **Phase 18 Spec Drift**: None. All seven canonical specifications (`SPEC-21` through `SPEC-27`) and all 21 Phase 18 invariants (`INV-QRY-001..003`, `INV-INC-001..003`, `INV-PAR-001..003`, `INV-ART-001..003`, `INV-PCT-001..003`, `INV-WLIB-001..003`, `INV-LNK-001..003`) match their implemented subsystems and conformance oracles with `0` xfail entries and `0` shortcuts remaining in P18.
- **Shortcuts Retired in P18**:
  - Retired the Stage-0 single-object/monolithic compilation limitation (`T067`, `T765`, `T766`, `T775`): `compiler/` now supports per-module `.obj` + `.axmi` separate compilation, `LinkIR` multi-object/archive linking, `IMAGE_SCN_LNK_COMDAT` generic/vtable folding, and root-set `--gc-sections`.
  - Retired the Stage-0 `.obj`/`.exe`-only artifact restriction (`SPEC-04 AXS-EXT-070`, `REQ-OWNER-006`, `T750`, `T751`): `compiler/` natively emits and consumes Windows x64 COFF static libraries (`--kind lib`), PE32+ dynamic libraries (`--kind dll`) with `.edata`/`DllMain`/`.reloc`, and COFF short-import `.lib` files, and cross-links `--emit=obj` output with GNU `ld` (`ADR-0034` §4 OI-07b).
- **Non-P18 Follow-Up Observations for `axiom-architect`**:
  1. `tools/gatecheck.py` task ID regex currently matches 3-digit task IDs (`^T[0-9]{3}[a-z]?$`), whereas Phase 23 planning (`T223`) introduced 4-digit task IDs (`T1000`–`T1010`), and `spec/invariants.md` `INV-CONC-002..004` (`P11`) list legacy `verify:` paths (`tests/unit/sema/conc_capture`, etc.) instead of the delivered `tests/ui/concurrency` / `tests/run/concurrency` / `tests/conformance/p11/e11_1_concurrency` paths. Updating `tools/gatecheck.py` / `spec/invariants.md` in the respective P11/P23 gate or maintenance task will restore `gatecheck.py --no-run` across all post-P10 phases.

## Files changed
- tests/conformance/p18/README.md
- ./_workspaces/reports/phase-P18-review.md
