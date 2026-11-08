# SPEC-104 — Canonical Documentation Generator (`axiomc doc`) & Integrated Test, Differential MIR-Oracle, Pass-Bisection & Debug/Trace Verification Framework (`axiomc test`)

- **Status**: draft (T816, 2026-11-08)
- **Owner**: `axiom-architect`
- **Consolidates**: `spec/SPEC-21-query-engine-semantic-db.md` (`AXS-QRY-001..034`), `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-012`, `AXS-ART-021..024`), `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` (`AXS-PCT-001..044`), `spec/SPEC-101-canonical-formatter.md` (`AXS-FMT-002..004`), `spec/SPEC-103-diagnostics-ux-ai-interface.md` (`AXS-DIAG-001..005`, `AXS-AI-001..021`), `0120` (`specs/0120` §293 `APKG-36`), `0121` (`specs/0121` §309 `AORACLE-20`), `0147` (`specs/0147` Part XXVIII §1–§69 `ATOOL-20..28`), `0161` (`specs/0161` §43–§45 `MIR-001..004`), `0163` (`specs/0163` §38), `0361` (`tasks/0361`, BOOTSTRAP-102 §1–§64 `ATEST-20..100`), `0374` (`tasks/0374`, BOOTSTRAP-115 §30–§32, §36–§41, §56 `ATOOL-20..55`), `0418` (`tasks/0418`, BOOTSTRAP-159 §1–§70 `ATEST2-20..70`), `0423` (`tasks/0423`, BOOTSTRAP-164 §1–§80 `ATEST2-20..80`), `0662` (`tasks/0662`, BOOTSTRAP-403 §1–§51 `ATEST-01..30`), `0693` (`tasks/0693`, BOOTSTRAP-434 §434.6–§434.9, §434.14–§434.17, §434.113–§434.119, §434.146–§434.150, §434.193–§434.200), `0695` (`tasks/0695`, BOOTSTRAP-434 §434.7–§434.8, §434.11, §434.68–§434.69, §434.81–§434.86, §434.95–§434.98, §434.146–§434.147 & BOOTSTRAP-435 §435.1–§435.200), `0696` (`tasks/0696`, BOOTSTRAP-434 §434.8–§434.9, §434.14–§434.15, §434.84–§434.85, §434.94–§434.95)
- **Covers**: `REQ-TOOL-002`, `REQ-TOOL-003`, `REQ-TOOL-005`, `REQ-TOOL-006`, `REQ-TOOL-007`, `REQ-TOOL-008`, `REQ-TOOL-009`, `REQ-TOOL-010`, `REQ-TOOL-011`, `REQ-TOOL-179`, `REQ-TOOL-187`, `REQ-TOOL-298`, `REQ-TST-112`
- **Related**: `spec/SPEC-01-lexical.md`, `spec/SPEC-02-grammar.md`, `spec/SPEC-03-core-semantics.md`, `spec/SPEC-10-ownership.md`, `spec/SPEC-11-capability.md`, `spec/SPEC-12-drop.md`, `spec/SPEC-21-query-engine-semantic-db.md`, `spec/SPEC-22-incremental-compilation.md`, `spec/SPEC-24-artifact-format-module-interfaces.md`, `spec/SPEC-25-pass-contracts-proof-carrying-ir.md`, `spec/SPEC-70-optir-ssa-memoryssa.md`, `spec/SPEC-76-performance-contract.md`, `spec/SPEC-100-lsp-server-ide-engine.md`, `spec/SPEC-101-canonical-formatter.md`, `spec/SPEC-103-diagnostics-ux-ai-interface.md`, `spec/diagnostics.md`, `spec/invariants.md`

## Tóm tắt

SPEC-104 định nghĩa kiến trúc chuẩn cho **trình sinh tài liệu chuẩn tắc (`axiomc doc`)** và **khung kiểm thử tích hợp, đối chiếu trình thông dịch MIR (`--interp`), tái hiện/chia đôi tìm lỗi pha tối ưu (`--opt-replay`, `--opt-bisect`) cùng thanh tra siêu dữ liệu gỡ lỗi/truy vết (`axiomc test`)** trong giai đoạn E19.5:
1. **Trình sinh tài liệu dựa trên `CompilerDB` (`axiomc doc`, `AXS-DOC-001..005`, `REQ-TOOL-298`, `REQ-TOOL-002`, `REQ-TOOL-187`)**: Trích xuất chú thích tài liệu `///` và `//!` cùng chữ ký ngữ nghĩa chuẩn tắc trực tiếp từ `CompilerDB` mà không phân tích lại văn bản hay gọi sinh mã máy (`codegen_invoked == false`). Hiển thị đầy đủ chế độ sở hữu/capability (`T`, `view<T>`, `mut_view<T>`), ràng buộc trait, thuộc tính an toàn (`unsafe`, `@repr`), huy hiệu hiệu ứng `std.meta_effects` (`AllocBehavior`, `BlockingBehavior`, `invalidates_views`), và kiểm chứng liên kết nội bộ `[module.Item]` / `[Type.method]`. Chú thích tài liệu và cờ cấu hình tuyệt đối không làm thay đổi ngữ nghĩa ngôn ngữ cốt lõi hoặc tệp nhị phân sản xuất (`REQ-TOOL-002`, `REQ-TOOL-187`).
2. **Trang HTML tĩnh tất định, đồ thị API JSON & kiểm thử ví dụ tài liệu (`axiomc doc --test`, `AXS-DOC-010..014`, `tasks/0418`, `tasks/0695`)**: Xuất bộ tài liệu HTML ngoại tuyến (`target/doc/`), chỉ mục tìm kiếm `search-index.json`, và đồ thị API máy đọc được `doc-graph.json` (`schema_version = 1`) hoàn toàn tất định theo byte. Chế độ `axiomc doc --test` (và `axiomc test --doc`) tự động biên dịch và thực thi các khối mã ```` ```axiom ```` trong chú thích `///` / `//!` (hỗ trợ `run`, `no_run`, `compile_fail(AX_CODE)`, `should_panic`, `ignore`) với ánh xạ vị trí lỗi ngược về đúng dòng chú thích gốc.
3. **Khung kiểm thử UX 2.0 (`axiomc test`), tách biệt nhị phân kiểm thử & bất biến ngữ nghĩa (`AXS-TST-001..004`, `REQ-TOOL-002`, `REQ-TST-112`)**: Phát hiện khối `test "name" { ... }` và hàm `@test fn` qua `CompilerDB` không cần phản chiếu thời gian chạy; tạo tệp thực thi kiểm thử riêng biệt để `axiomc build` không bao giờ kéo khung kiểm thử vào nhị phân sản xuất; chạy song song có cô lập thư mục tạm và hạt giống tất định (`--seed`); đảm bảo mọi cờ tính năng biên dịch (`--feature`, `--cfg test`) không bao giờ làm thay đổi ngữ nghĩa cốt lõi của ngôn ngữ (`REQ-TOOL-002`).
4. **Trình thông dịch tham chiếu MIR (`--interp`) & kiểm thử đối chiếu tự động (`AXS-TST-010..012`, `REQ-TOOL-003`, `REQ-TOOL-009`)**: Trình thông dịch `Verified MIR` (`compiler/interp`) thực thi trực tiếp các chỉ thị MIR đã kiểm chứng để làm chuẩn đối chiếu ngữ nghĩa với bản dịch mã máy (`-O0`, `-O1`, `-O2`, `-Os`, `-Oz`, `--lto`) trên giá trị trả về, mã thoát, `stdout`/`stderr`, sự kiện `panic`, và thứ tự `Drop`. Toàn bộ siêu dữ liệu đối chiếu/oracle không có bất kỳ phụ thuộc thời gian chạy nào trong tệp thực thi sản xuất (`REQ-TOOL-003`, `REQ-TOOL-187`).
5. **Tái hiện pha tối ưu (`--opt-replay`), chia đôi tự động tìm pha gây lỗi (`--opt-bisect`) & kiểm định gỡ lỗi/truy vết (`AXS-TST-020..035`, `REQ-TOOL-005..008`, `REQ-TOOL-010..011`, `REQ-TOOL-179`, `REQ-TST-112`)**: Khi phát hiện sai lệch giữa `--interp` và mã tối ưu hóa, `compiler/opt/bisect` thực hiện tìm kiếm nhị phân $O(\log_2 M)$ qua `--opt-bisect-limit=<N>` để cô lập chính xác pha tối ưu $k^*$ và hàm gây sai lệch, đồng thời xuất gói `--opt-replay` độc lập. Kiểm định gốc trong `axiomc test` xác nhận mô hình gỡ lỗi ngữ nghĩa độc lập đích (`REQ-TOOL-007`), bắt buộc phát `.debug_line` ở `-O0` (`REQ-TOOL-010`) tách biệt với các phân đoạn DWARF đầy đủ theo tầng (`REQ-TOOL-011`), tái tạo khung hàm logic khi nội tuyến hóa mạnh (`REQ-TOOL-006`), biểu diễn trung thực biến `OptimizedOut` mà không tạo trạng thái vật lý giả tạo (`REQ-TOOL-005`), và đảm bảo chi phí thời gian chạy bằng 0 khi tắt truy vết (`REQ-TOOL-008`).

---

## 1. `CompilerDB`-Backed Documentation Extraction, Semantic Signatures & Intra-Doc Link Resolution (`axiomc doc`)

### `AXS-DOC-001` — Single `CompilerDB` Semantic Authority & Zero-Codegen Documentation Pipeline (`REQ-TOOL-298`)

1. **Shared semantic authority (`tasks/0374 §1, §30–31 ATOOL-20`, `tasks/0693 §434.14–16, §434.162–163`, `tasks/0695 §434.11, §434.171`, `tasks/0696 §434.14`, `SPEC-21 AXS-QRY-001`, `REQ-TOOL-298`)**:
   - `axiomc doc` (implemented in `compiler/docgen` and `compiler/driver/doc_cmd`, `T817`) queries the exact same `CompilerDB` frontend and semantic tables (`parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `trait_solve`, `const_eval`, `layout_of`, `std.meta_effects`) used by `axiomc check`, `axiomc lsp`, and `axiomc query`.
   - `compiler/docgen` SHALL NEVER implement a standalone regex/text scraper or duplicate type/trait/ownership inference outside `CompilerDB` (`tasks/0693 §434.16`: *"Không parse source lần nữa"*; `tasks/0696 §434.14`: *"Documentation generator không được tự suy diễn semantic information"*).
2. **Zero-codegen documentation generation (`SPEC-100 AXS-LSP-004`, `SPEC-103 AXS-AI-001`)**:
   - Generating HTML and JSON documentation (`axiomc doc` without `--test`) evaluates only semantic and layout queries in `CompilerDB` and SHALL NEVER invoke `OptIR` optimization passes, `LIR` lowering, register allocation, machine encoding, or linking (`codegen_invoked == false`).

### `AXS-DOC-002` — Outer (`///`) & Inner (`//!`) Doc-Comment Attachment and Documentation Attributes

1. **Lexical & CST trivia attachment (`SPEC-01 §3`, `SPEC-101 AXS-FMT-002..003`, `tasks/0695 §434.81`, `tasks/0696 §434.84–85`)**:
   - **Inner module doc comments (`//! ...`, `TriviaInnerDoc`)**: Consecutive `//!` lines in `CstFile.header_trivia` (or immediately inside a `module` header) attach to the enclosing `ModuleId` (`DocModule.doc_markdown`).
   - **Outer item doc comments (`/// ...`, `TriviaOuterDoc`)**: Consecutive `///` lines in a declaration's `leading_trivia` slot (placed above any `@attribute` list per `SPEC-101 AXS-FMT-003` Slot 4) attach to that declaration (`fn`, `struct`, `enum`, `union`, `trait`, `impl`, `const`, `static`, `type`, `struct` field, `enum` variant, or `trait` method).
   - Ordinary line comments (`// ...`, `//// ...`) and block comments (`/* ... */`) are non-documentation trivia and are never exported into generated documentation.
2. **Markdown payload normalization (`SPEC-101 AXS-FMT-002`)**:
   - Each `///` or `//!` line strips its `///` or `//!` prefix plus at most one common leading ASCII space (`0x20`), normalizes `CRLF` to `LF`, and joins consecutive lines with `\n`.
   - The first paragraph (up to the first blank line or heading) forms the item's `summary_markdown`; the full text forms `body_markdown`.
3. **Structured documentation attributes (`tasks/0696 §434.84–85`)**:
   - `@doc(hidden)`: Excludes the item from default public HTML/search rendering while retaining it in `CompilerDB` and `--include-private` / `--include-hidden` JSON dumps.
   - `@deprecated("message", since = "version")`: Marks the item with a structured deprecation notice (`DocDeprecation { since: Option<Str>, message: Str }`) in both HTML and `doc-graph.json`.
   - `@since("version")` and `@must_use("reason")`: Exported as structured stability and usage contract badges on the item.

### `AXS-DOC-003` — Canonical Semantic Signatures, Ownership/Capability Contracts & Effect Badges

Every documented declaration in `compiler/docgen` renders its canonical Axiom signature (`=` and `.` syntax formatted via `compiler/fmt/printer` `SPEC-101`) enriched with `CompilerDB`-verified semantic facts (`tasks/0374 §30–31`, `tasks/0693 §434.16–17`, `SPEC-103 AXS-AI-011..012`):

1. **Functions & methods (`DocFunctionSig`)**:
   - Displays canonical qualifiers (`pub`, `unsafe`, `async`, `comptime`, `gen`, `extern "<abi>"`), generic parameters with trait bounds, receiver mode (`self`, `view<Self>`, `mut_view<Self>`), parameter list with explicit ownership/capability classification (`ByValueMove`, `ByValueCopy`, `SharedView` `view<T>`, `ExclusiveMutView` `mut_view<T>`), return type, and `where` clauses.
   - Attaches verified `ApiEffectSummary` badges (`SPEC-103 AXS-AI-012`, `REQ-TOOL-190`): allocation behavior (`NeverAllocates` / `MayAllocate` / `AlwaysAllocates`), blocking/suspension behavior (`NonBlocking` / `MayBlock` / `AsyncSuspends`), synchronization (`AcquireReleaseLock`, `AtomicOrdering`, etc.), panic conditions, view/container invalidation rules (`invalidates_views`), required authority capabilities (`FsCap`, `NetCap`, etc.), and asymptotic complexity.
2. **Nominal & composite types (`struct`, `enum`, `union`, `type`)**:
   - Displays representation attributes (`@repr(C)`, `@repr(transparent)`, `@repr(packed)`, `@align(N)`), auto-trait & lifecycle implementation badges (`Copy`, `Drop`, `Send`, `Share`, `Sized`), and `ContainerContract` invalidation rules when the type is a container (`Vec<T>`, `String`, `HashMap<K, V>`, `Slice<T>`, `Box<T>`, `Arc<T>`; `SPEC-103 AXS-AI-011`).
   - Lists all visible fields (or variants with discriminant tags/payloads), inherent `impl` methods, and trait implementations (`impl Trait for Type`) grouped deterministically.
3. **Traits (`DocTraitSig`)**:
   - Displays supertraits, associated types/constants, required vs default methods, `dyn Trait` object-safety status (`ObjectSafe` vs `NotObjectSafe` with reason from `SPEC-63`), and all known implementors across the documented package graph.

```axiom
module compiler.docgen

pub struct DocDeprecation {
    pub is_deprecated: bool,
    pub since: Str,
    pub message: Str
}

pub struct DocParamContract {
    pub name: Str,
    pub ty: Str,
    pub passing_mode: Str, // "move", "copy", "view", "mut_view"
    pub target_symbol: Str
}

pub struct DocItem {
    pub semantic_key: Str,
    pub module_path: Str,
    pub name: Str,
    pub kind: Str,                  // "module", "fn", "struct", "enum", "union", "trait", "const", "type"
    pub visibility: Str,            // "pub", "private"
    pub canonical_signature: Str,   // Formatted via compiler/fmt/printer (SPEC-101)
    pub summary_markdown: Str,
    pub body_markdown: Str,
    pub source_span: Span,
    pub deprecation: DocDeprecation,
    pub since_version: Str,
    pub must_use_reason: Str,
    pub copy_trait: bool,
    pub drop_trait: bool,
    pub send_trait: bool,
    pub share_trait: bool,
    pub params: Slice<DocParamContract>,
    pub effects: ApiEffectSummary,
    pub resolved_links: Slice<DocLink>,
    pub doctests: Slice<DocTestBlock>
}
```

### `AXS-DOC-004` — Verified Intra-Doc Cross-Reference Resolution (`[module.Item]`, `[Type.method]`)

1. **Intra-doc link syntax (`tasks/0374 §31`, `tasks/0695 §434.146–147`)**:
   - Markdown link references of the form `[path.to.Item]`, `` [`path.to.Item`] ``, `[Type.method]`, `[Enum.Variant]`, or `[ local_item ]` (without an explicit `http://`, `https://`, or file URL target) are treated as semantic intra-doc symbol links.
   - All path separators in intra-doc links MUST use Axiom's canonical dot `.` syntax (`ADR-0007`). An intra-doc link using foreign `::` syntax (`[std::vec::Vec]`) is flagged as a broken/non-canonical link with a `MachineApplicable` fix replacing `::` with `.`.
2. **Resolution via `CompilerDB`**:
   - `compiler/docgen` resolves each intra-doc path in the lexical and `use`-import scope of the enclosing `ModuleId` (falling back to workspace/standard-library root paths such as `std.collections.Vec`).
   - When resolved to a `SymbolId` / `SemanticKey`, the HTML renderer rewrites the link to the target item's deterministic relative URL (e.g., `../collections/struct.Vec.html#method.push`) and the JSON exporter records `DocLink { raw_text: Str, target_semantic_key: Str, target_url: Str, span: Span }`.
3. **Broken intra-doc link diagnostics**:
   - If an intra-doc link `[unknown.Symbol]` fails resolution in `CompilerDB`, `axiomc doc` emits `AX_NAME_UNRESOLVED` (`data.context = "doc_link"`, `data.doc_link = "unknown.Symbol"`) at the exact byte span inside the `///` or `//!` comment (warning by default; hard error with exit code `1` when `--deny-broken-links` is passed).

### `AXS-DOC-005` — Zero Semantic or Production Runtime Impact of Documentation & Build Features (`REQ-TOOL-002`, `REQ-TOOL-187`)

1. **Comment & docgen invariance (`0120 §293 APKG-36`, `tasks/0448 §36 ATOOL-33, 39`, `tasks/0693 §434.197`, `SPEC-22 AXS-INC-002`, `SPEC-103 AXS-AI-021`, `REQ-TOOL-002`, `REQ-TOOL-187`)**:
   - `///` and `//!` comments are stored in the separate `DocCommentTable` of `CompilerDB` (`SPEC-22` `DocFingerprint`), completely excluded from `AstFingerprint`, `InterfaceFingerprint`, `AbiFingerprint`, `BodyFingerprint`, and `CodegenFingerprint`.
   - Adding, editing, or stripping all `///` and `//!` comments in a workspace MUST produce **byte-for-byte identical** `.obj`, `.lib`, `.a`, `.dll`, `.so`, `.dylib`, `.wasm`, and `.exe` production binaries (`INV-DET-001`, `REQ-TOOL-187`).
   - Generated documentation artifacts (`target/doc/**`, `doc-graph.json`, `search-index.json`) and `.axmeta` doc sections are never linked into or required at runtime by production binaries (`REQ-TOOL-187`).

---

## 2. Deterministic Static HTML Site, Machine-Readable JSON API Graph & Executable Doc-Tests

### `AXS-DOC-010` — Deterministic Static HTML Site & Offline Search Index (`target/doc/`)

1. **Directory layout (`tasks/0693 §434.14–15, §434.154`, `tasks/0695 §434.146–147`, `tasks/0696 §434.15`)**:
   - `axiomc doc [<path>...]` (default output directory `target/doc`, overridable via `--out-dir <dir>`) writes a self-contained static documentation site:
     - `target/doc/index.html` — package/workspace overview and top-level module index;
     - `target/doc/<module_slash_path>/index.html` — module page (`//!` module docs, re-exports, structs, enums, traits, functions, constants, type aliases);
     - `target/doc/<module_slash_path>/<kind>.<Name>.html` — dedicated item page (`struct.Vec.html`, `trait.Iterator.html`, `fn.split_payload.html`);
     - `target/doc/search-index.json` — client-side offline symbol/signature/summary search index;
     - `target/doc/doc-graph.json` — machine-readable semantic API & documentation graph (`AXS-DOC-011`);
     - `target/doc/assets/{axiom-doc.css, axiom-doc.js}` — built-in static stylesheet and offline search script.
2. **Offline-first & byte-for-byte determinism (`tasks/0693 §434.56–57, §434.154–155`, `tasks/0695 §434.132–133`, `INV-DET-001`)**:
   - Generated HTML/CSS/JS/JSON files contain **zero** external network URLs (no CDN fonts, scripts, or telemetry), **zero** wall-clock timestamps, and **zero** host-specific absolute paths.
   - All modules, items, fields, methods, trait implementations, and search index entries are sorted deterministically by canonical `(module_path, kind_ordinal, item_name, semantic_key)` so two `axiomc doc` runs on the same source produce byte-identical outputs.

### `AXS-DOC-011` — Machine-Readable JSON Documentation & API Graph (`doc-graph.json`, `schema_version = 1`)

When `axiomc doc --json` (or default `target/doc/doc-graph.json`) is emitted, the output conforms to the versioned `AXDOC` schema (`tasks/0374 §31`, `tasks/0693 §434.17, §434.164`, `tasks/0696 §434.15`):

```json
{
  "protocol": "AXDOC",
  "schema_version": 1,
  "compiler_semantic_version": "0.1.0",
  "package_name": "packet_proc",
  "codegen_invoked": false,
  "modules": [
    {
      "module_path": "packet_proc",
      "doc_markdown": "Module header documentation.",
      "items": []
    }
  ],
  "search_index": []
}
```

### `AXS-DOC-012` — Executable Documentation Examples (`axiomc doc --test` / `axiomc test --doc`)

1. **Doc-test extraction (`tasks/0418 §1–8`, `tasks/0695 §434.82, §435.137`, `T817`)**:
   - `axiomc doc --test [<path>...]` (and `axiomc test --doc [<path>...]`) extracts every fenced code block with info string `axiom` or `ax` (optionally followed by comma-separated modifiers) from `///` and `//!` comments across all documented modules.
2. **Doc-test fence modifiers (`tasks/0695 §434.82, §435.137`)**:

   | Fence Info String | Execution Contract |
   |---|---|
   | ```` ```axiom ```` or ```` ```axiom,run ```` | Default mode: compiles and executes the snippet in `--interp` (and native when `--native-doctests` is enabled). Must compile with `0` errors and exit with `0` without panicking. |
   | ```` ```axiom,no_run ```` | Compiles the snippet through full `CompilerDB` type/ownership/capability checking and `Verified MIR` (`axiomc check`) without executing it. |
   | ```` ```axiom,compile_fail ```` or ```` ```axiom,compile_fail(AX_MOVE_USE_AFTER_MOVE) ```` | Must fail compilation; when an `AX_<AREA>_<NAME>` code is specified, the emitted diagnostics MUST include that exact code (`AXD-003`, `ATEST-26..27`). |
   | ```` ```axiom,should_panic ```` or ```` ```axiom,should_panic(expected = "msg") ```` | Must compile cleanly and panic during execution (matching substring `"msg"` if specified). |
   | ```` ```axiom,ignore ```` | Checked for lexical/canonical syntax hygiene (`=` and `.`), skipped for execution unless `--include-ignored` is passed. |

3. **Wrapper synthesis, hidden setup lines & source-span remapping**:
   - Lines inside a fenced block starting with `# ` (hash followed by space, e.g. `# use std.collections.Vec`) are included when compiling and running the doc-test but stripped from rendered HTML/Markdown display.
   - If the extracted snippet does not declare `fn main`, `compiler/docgen` wraps the body in a synthetic harness module importing the documented module (`use <module_path>.*`) and placing the snippet inside `pub fn main() -> i32 { ...; 0 }`.
   - Every token span inside the synthesized doc-test maps back to the exact `(FileId, line, col)` of the originating `///` or `//!` comment so any diagnostic points directly to the doc comment in the user's `.ax` file (`tasks/0695 §434.152`).

---

## 3. Integrated Test Framework UX 2.0 (`axiomc test`), Isolated Test Executables & Semantic Invariance

### `AXS-TST-001` — Unified Three-Tier Verification Architecture (`REQ-TST-112`)

1. **Natively integrated toolchain verification (`0361 §1–3, §63–64 ATEST-20..22, 95..100`, `0418 §1–2 ATEST2-20`, `0662 §1–2, §50–51 ATEST-01..30`, `REQ-TST-112`)**:
   - `axiomc test` (`compiler/test_runner`, `compiler/driver/test_cmd`, `T818`) is not a bolt-on shell wrapper around external unit-test libraries; it is a first-class compiler subsystem over `CompilerDB` integrating three verification layers in one unified pipeline:
     - **Layer 1 — Static & Compile-Time Verification**: Compile-pass (`check`), compile-fail diagnostic identity verification (`AX_<AREA>_<NAME>`, `CausalProvenanceChain`, `DiagnosticFingerprint`), `const`/`comptime` static assertions, layout/ABI contract checks, and `Verified MIR` / `verify_mc` invariants;
     - **Layer 2 — Reference Oracle & Differential Execution**: Unit/integration tests, property tests, executable doc-tests (`--doc`), and automatic `Verified MIR` interpreter (`--interp`) vs native (`-O0`..`-Oz`, `--lto`) differential execution (`REQ-TOOL-009`);
     - **Layer 3 — Optimization Pass Bisection & Debug/Trace Auditing**: Automated pass replay (`--opt-replay`) and binary-search pass bisection (`--opt-bisect`, `REQ-TOOL-179`), `.debug_line` and logical inline frame auditing (`REQ-TOOL-005..007`, `REQ-TOOL-010..011`), and zero-cost disabled-trace verification (`REQ-TOOL-008`).

### `AXS-TST-002` — First-Class `test "name" { ... }` & `@test fn` Discovery and Assertion Semantics

1. **Compile-time test discovery without runtime reflection (`0374 §32`, `0418 §3–7`, `0662 §3–4, §51 ATEST-01`, `0693 §434.6–7`, `0695 §434.83–84`)**:
   - `CompilerDB` discovers test cases directly from the parsed/resolved HIR module tree (`discover_module_tests(ModuleId)`), supporting both canonical surface forms:
     - Named test blocks: `test "addition preserves checked overflow" { ... }` (`0418 §3`);
     - Annotated test functions: `@test fn test_addition() { ... }` (or `@test fn test_addition() -> Result<(), Error>`).
   - Every discovered test is assigned a deterministic 128-bit `test_id: Fingerprint128`:
     $$\text{test\_id} = \text{BLAKE3}_{128}(\text{"AXIOM-TEST-ID-v1"} \parallel \text{module\_path} \parallel \text{canonical\_test\_name})$$
   - Supported test attributes (`0695 §434.84`, `0662 §3–10`):
     - `@should_panic` / `@should_panic(expected = "substring")` — test passes if and only if execution panics (with message containing `"substring"` when specified);
     - `@ignore` / `@ignore("reason")` — test is type-checked and MIR-verified (`ATEST2-65`), but skipped at runtime unless `--include-ignored` is passed;
     - `@timeout(ms = <u64>)` — per-test execution deadline (default `30000` ms);
     - `@serial` — runs exclusively without concurrent worker tests;
     - `@seed(<u64>)` — pins the deterministic PRNG seed for property/randomized test generators (`ATEST-06`, `ATEST-69`).
2. **Assertions are never unsafe optimizer hints (`0418 §5–7 ATEST2-23..24`)**:
   - `assert(cond)`, `assert_eq(left, right)`, and `assert_ne(left, right)` evaluate their operands once and deterministically panic on failure in **all** profiles (`debug` and `release`).
   - A failed or disabled `debug_assert(cond)` SHALL NEVER be treated by the optimizer as an unchecked `unreachable` assumption capable of causing Undefined Behavior (`0418 §6`: *"Assertion không phải optimizer hint"*).

### `AXS-TST-003` — Isolated Test Executables & Build-Feature Core Semantic Invariance (`REQ-TOOL-002`, `REQ-TOOL-187`)

1. **Dedicated test binary isolation (`0374 §32`, `0418 §4 ATEST2-21..22`, `0662 §5`, `0693 §434.8`, `REQ-TOOL-187`)**:
   - `axiomc test` synthesizes a standalone test runner entry point in an isolated test artifact (`target/<triple>/test/<pkg>-test`), linking only the test harness and the modules reachable from the selected tests.
   - `axiomc build` (and `axiomc run`) strips 100% of `test "..." { ... }` blocks and `@test` functions during HIR pruning (`SPEC-88` `@cfg(test)` boundary), ensuring zero test-harness code, zero test descriptors, and zero test strings ever enter production executables or libraries (`0418 §4`: *"Production build không kéo test harness vào binary"*; `REQ-TOOL-187`).
2. **Build features must not change core language semantics (`REQ-TOOL-002`, `0120 §293 APKG-36`, `0361 §64 ATEST-100`, `0418 §70 ATEST2-65`, `0423 §80 ATEST2-73..74`)**:
   - Package and build features (`--feature <name>`, `--cfg <pred>`, `--test`, `--interp`, `--opt-bisect`, `-g`, `--trace`) only select conditional library modules, target bindings, or tooling observers (`0120 §293`).
   - Build features and test modes SHALL NEVER alter core Axiom language semantics:
     - Lexical and grammatical rules (`=` and `.` canonical syntax, `SPEC-01`, `SPEC-02`);
     - Scalar integer overflow and IEEE-754 floating-point semantics (`SPEC-40`, `SPEC-41`);
     - Ownership transfer, move checking, and `Copy` vs `!Copy` rules (`SPEC-10`);
     - `view<T>` / `mut_view<T>` capability exclusivity and lifetime containment (`SPEC-11`);
     - Deterministic reverse-order `Drop` semantics (`SPEC-12`);
     - `Send` / `Share` concurrency verification and safety-profile boundaries (`SPEC-30`, `SPEC-53`).

### `AXS-TST-004` — Deterministic Parallel Execution, Tempdir Isolation & Machine-Readable Test Events

1. **Per-test isolation & deterministic seeds (`0361 §59–60 ATEST-69..70, 75..76`, `0418 §68–69 ATEST2-60..61`, `0662 §6–10, §42, §51 ATEST-03..08`, `0695 §434.85–86, §435.113–116, §435.196–197`)**:
   - Each test case executes with its own isolated temporary directory (`TMPDIR` set to `target/test-tmp/<test_id_hex>/`), cleaned up on pass and retained on failure with a reproducible rerun command (`0695 §435.114–115, §435.177`).
   - Every randomized/property test receives a deterministic PRNG stream seeded from `hash("--seed", global_seed, test_id)` (`ATEST-06`, `0695 §435.116`).
2. **Deterministic parallel reporting (`ATEST-76`, `ATEST2-61, 71`)**:
   - When running across `--jobs <N>` workers, test execution interleaving never affects the final report: `compiler/test_runner` buffers per-test results and emits the final human summary and `--format=json` (`schema_version = 1`) report sorted by `(module_path, span.start, test_id)`.

```axiom
module compiler.test_runner

pub enum TestOutcomeKind {
    Passed,
    Failed,
    PanickedUnexpectedly,
    ExpectedPanicMissing,
    DifferentialMismatch,
    TimedOut,
    Ignored
}

pub struct TestCaseResult {
    pub test_id: Fingerprint128,
    pub module_path: Str,
    pub name: Str,
    pub outcome: TestOutcomeKind,
    pub duration_us: u64,
    pub seed: u64,
    pub interp_exit_code: i32,
    pub native_exit_code: i32,
    pub stdout_text: Str,
    pub stderr_text: Str,
    pub failure_reason: Str,
    pub repro_command: Str
}
```

---

## 4. MIR Reference Interpreter & Differential Execution Oracle

### `AXS-TST-010` — Minimal Verified-MIR Reference Interpreter (`--interp`) (`REQ-TOOL-009`)

1. **Direct execution of `Verified MIR` (`0161 §43–45 MIR-001..004`, `0361 §20–21, §64 ATEST-46..48`, `0418 §14–15`, `0423 §8–9, §19–21`, `0695 §435.84–86, §435.106–108`, `REQ-TOOL-009`, `INV-PIPE-002`, `INV-ORACLE-001..003`)**:
   - `compiler/interp` provides a self-contained, target-independent MIR reference interpreter that executes `Verified MIR` immediately after `compiler/verify` passes (`0161 §43 MIR-001`, `REQ-TOOL-009`).
   - The MIR interpreter executes basic and composite MIR instructions directly (`Assign`, `Move`, `Copy`, `Drop`, `MakeView`, `MakeMutView`, `CheckedBinOp`, `UnaryOp`, `Cast`, `Aggregate`, `Discriminant`, `SwitchInt`, `Call`, `Return`, `Assert`), tracking exact place initialization, move states, `view`/`mut_view` capability provenance, deterministic reverse-order `Drop` execution, and step budgets (`--max-steps`).
2. **Trust boundary (`0418 §15`, `0423 §9`, `0361 ATEST-95`)**:
   - The Axiom specification (`SPEC-*`) and `CompilerDB` semantic/MIR verifiers are the normative authority; `compiler/interp` is the reference execution oracle (`MIR-003`) whose simplicity and independence from `OptIR`, `LIR`, `RegAlloc`, and machine encoding (`INV-LAYER-003`) make it the ground-truth baseline for differential validation.

### `AXS-TST-011` — Zero Production Runtime Requirement for Semantic Oracle Metadata (`REQ-TOOL-003`, `REQ-TOOL-187`)

1. **Compile/test-only oracle boundary (`0121 §309 AORACLE-20`, `0147 §52–53, §67 ATOOL-21..23`, `0693 §434.197`, `0695 §435.86`, `REQ-TOOL-003`, `REQ-TOOL-187`)**:
   - Semantic oracle metadata — including MIR interpreter state, allocation epoch tags, capability borrow ledgers, `Drop` trace recorders, `.axmir` verification templates, and differential test manifests — is strictly a compile-time and test-time verification facility (`0121 §309 AORACLE-20`: *"Semantic Oracle metadata has no production runtime requirement"*).
   - Production native executables and libraries (`axiomc build`) SHALL NEVER embed the MIR interpreter, link oracle support tables, or require `.axmeta`, `.axmir`, `.axdb`, or oracle sidecar files at runtime (`REQ-TOOL-003`, `REQ-TOOL-187`).

### `AXS-TST-012` — Multi-Mode Differential Execution Harness (`axiomc test --diff`) (`REQ-TOOL-009`)

1. **Observable equivalence vector (`0161 §45 MIR-003..004`, `0361 §18–22 ATEST-44..48`, `0418 §16–17, §26 ATEST2-27`, `0423 §10, §16–21`, `INV-ORACLE-002`)**:
   - For any deterministic test case $T$, `axiomc test --diff` executes $T$ under the MIR interpreter (`--interp`) and under one or more native backend configurations (`-O0`, `-O1`, `-O2`, `-Os`, `-Oz`, `--lto`) and compares the observable outcome tuple:
     $$\mathcal{O}(T) = (\text{exit\_code}, \text{return\_value}, \text{stdout\_bytes}, \text{stderr\_bytes}, \text{panic\_kind}, \text{drop\_sequence})$$
   - Machine instruction selection, register assignment, stack frame size, and physical memory addresses are allowed to differ across optimization levels (`0418 §17`), but $\mathcal{O}_{\text{native}}(T)$ MUST equal $\mathcal{O}_{\text{interp}}(T)$ bit-for-bit (`ATEST-44..48`, `REQ-TOOL-009`).
2. **Automatic handoff to pass bisection**:
   - If $\mathcal{O}_{\text{interp}}(T) == \mathcal{O}_{\text{native}, \text{-O0}}(T)$ but $\mathcal{O}_{\text{native}, \text{-O2}}(T) \neq \mathcal{O}_{\text{interp}}(T)$, the runner classifies the failure as an optimizer miscompilation (`DifferentialMismatch`) and invokes (or emits the exact command for) `compiler/opt/bisect` (`AXS-TST-020..022`).

---

## 5. Optimization Pass Replay (`--opt-replay`) & Automated Pass Bisection (`--opt-bisect`)

### `AXS-TST-020` — Deterministic Pass Provenance Indexing & `--opt-bisect-limit=<N>` (`REQ-TOOL-179`)

1. **Monotonic pass invocation numbering (`0418 §64–65, §70 ATEST2-58..59`, `0423 §22–24, §78–80 ATEST2-68`, `SPEC-25 AXS-PCT-002`, `SPEC-70 AXS-OPT-030`, `REQ-TOOL-179`, `T818`)**:
   - Inside `compiler/opt/bisect`, every optimization transformation step across the compilation unit is assigned a deterministic 1-based index `step_id: u32` in canonical `(cgu_index, fn_semantic_key, pass_ordinal, iteration_index)` order.
   - Each step records a `PassStepRecord`:
     ```axiom
     module compiler.opt.bisect

     pub struct PassStepRecord {
         pub step_id: u32,
         pub pass_name: Str,          // e.g. "sccp", "gvn", "cse", "sroa", "dce", "bce", "licm", "inline"
         pub fn_symbol: Str,          // canonical function path, e.g. "math.fast_sum"
         pub input_ir_hash: Fingerprint128,
         pub output_ir_hash: Fingerprint128,
         pub mutated: bool,
         pub verified_after: bool
     }
     ```
2. **Fuel-gated pass execution (`--opt-bisect-limit=<N>`, `--stop-after=<pass>`, `--disable-pass=<pass>`)**:
   - When `--opt-bisect-limit=<N>` is supplied:
     - For every pass invocation with `step_id <= N`, `PassManager` executes the pass normally and runs the post-pass `OptIR` verifier (`SPEC-70 AXS-OPT-034`).
     - For every pass invocation with `step_id > N`, `PassManager` bypasses the transformation and leaves the function's `OptIR` unchanged (`mutated = false`), proceeding directly to LIR/machine lowering with the valid post-step-`N` IR.
   - `limit = 0` disables all optional `OptIR` passes (equivalent to baseline unoptimized lowering).

### `AXS-TST-021` — Automated Binary-Search Pass Bisection (`axiomc test --opt-bisect`) (`REQ-TOOL-179`)

1. **Binary search algorithm (`0418 §64, §70 ATEST2-59`, `0423 §78, §80 ATEST2-68`, `REQ-TOOL-179`, `T818`)**:
   - When `axiomc test --opt-bisect [<test_filter>]` is invoked on a test where baseline `limit = 0` (and `--interp`) produces the expected oracle result $\mathcal{O}_{\text{ref}}$ while full optimization `limit = M` (where $M$ is the total count of mutating pass invocations) diverges ($\mathcal{O}(M) \neq \mathcal{O}_{\text{ref}}$):
     - **Step 1**: Initialize search bounds $lo = 1$, $hi = M$.
     - **Step 2**: While $lo < hi$:
       - Compute $mid = lo + \lfloor(hi - lo) / 2\rfloor$.
       - Compile and execute the test (or evaluate the intermediate `OptIR` interpreter/evaluator) with `--opt-bisect-limit=mid`.
       - If $\mathcal{O}(mid) == \mathcal{O}_{\text{ref}}$, the miscompilation occurred after `mid`: set $lo = mid + 1$.
       - Otherwise ($\mathcal{O}(mid) \neq \mathcal{O}_{\text{ref}}$), the miscompilation occurred at or before `mid`: set $hi = mid$.
     - **Step 3**: At termination ($lo == hi == k^*$), step $k^*$ is proven to be the **exact first pass invocation** where the program semantics diverged:
       $$\mathcal{O}(k^* - 1) == \mathcal{O}_{\text{ref}} \quad \wedge \quad \mathcal{O}(k^*) \neq \mathcal{O}_{\text{ref}}$$
2. **Structured bisection report (`PassBisectReport`)**:
   - Outputs both human summary and machine-readable JSON (`--format=json`) containing:
     - `total_steps: M`, `evaluations_run` ($\le \lceil \log_2 M \rceil + 2$), `culprit_step_id: k*`;
     - `culprit_pass_name` (e.g. `"bce"` or `"gvn"`) and `culprit_function` (`SemanticKey` + `Span`);
     - Canonical `OptIR` snapshot immediately **before** step $k^*$ (`ir_before`) and immediately **after** step $k^*$ (`ir_after`), plus their minimal unified IR diff;
     - Path to the automatically generated replay bundle (`target/opt-bisect/<test_name>.replay.json`).

### `AXS-TST-022` — Self-Contained Optimization Pass Replay (`--opt-replay=<manifest>`) (`REQ-TOOL-179`)

1. **Deterministic pass replay (`0418 §63, §70 ATEST2-58`, `0423 §79, §80 ATEST2-68`, `REQ-TOOL-179`, `T818`)**:
   - An `OptReplayManifest` (`schema_version = 1`) serializes the self-contained reproduction state:
     - `target_triple`, `opt_profile`, `safety_profile`, `panic_profile`;
     - `fn_symbol`, `input_ir_snapshot` (the verified MIR/`OptIR` entering the pass pipeline or immediately preceding `culprit_step_id`);
     - `pass_sequence: Slice<Str>`, `bisect_limit: u32`, and `expected_oracle_output`.
   - Running `axiomc test --opt-replay=<manifest>` (or `axiomc inspect --opt-replay=<manifest>`) reloads `input_ir_snapshot`, runs the exact specified `pass_sequence` up to `bisect_limit`, verifies post-pass contracts (`SPEC-25`), and compares the resulting execution against `expected_oracle_output` without requiring the original multi-file workspace (`0423 §79`).

---

## 6. Native Debug Metadata, Logical Inlined Frames, `OptimizedOut` Honesty & Zero-Cost Disabled Tracing

### `AXS-TST-030` — Target-Independent Semantic Debug Model (`SemanticDebugModel`) (`REQ-TOOL-007`)

1. **Format-neutral semantic debug representation (`0147 §1–3, §9, §11–13, §59, §67 ATOOL-21..23, 28`, `0662 §20–24`, `0693 §434.114–119`, `0695 §434.95–97`, `REQ-TOOL-007`, `T818`)**:
   - The compiler constructs a target-independent `SemanticDebugModel` from `CompilerDB` (`SourceOrigin`, lexical scopes, `TypeId` layouts, ownership/capability states, and `OptIR`/`LIR` provenance) before target-specific object emission (`0147 §9`: *"Axiom semantic debug model phải độc lập target"*; `REQ-TOOL-007`).
   - Target object writers project `SemanticDebugModel` into the target's native container format without altering any frontend, MIR, `OptIR`, or ABI rule (`0147 §59 ATOOL-28`: *"Debug metadata không được ảnh hưởng ABI"*):
     - ELF (`x86_64-linux`, `aarch64-linux`, `riscv64-linux`, `aarch64-android`) & WASM (`wasm32-*`): DWARF sections (`.debug_line`, `.debug_info`, `.debug_abbrev`, `.debug_str`);
     - Mach-O (`aarch64-macos`, `x86_64-macos`): `__DWARF` segment (`__debug_line`, `__debug_info`, `__debug_abbrev`, `__debug_str`);
     - Windows PE/COFF (`x86_64-windows`, `aarch64-windows`): `.debug_line` / CodeView `.debug$S` & `.debug$T` / detached `.pdb` / `.axdbg` (`SPEC-24 AXS-ART-024`).

```axiom
module compiler.test_runner.debug_audit

pub enum DebugVarStorage {
    Register(Str),              // Live in physical register e.g. "rax", "xmm0"
    StackFrameOffset(i64),      // Live at [rbp + offset] / [sp + offset]
    ConstantValue(Str),         // Constant-folded value known without runtime storage
    ScalarizedPieces(u32),      // Split across N SROA scalar pieces
    OptimizedOut(Str)           // Eliminated/clobbered; carries reason e.g. "dce", "last_use_passed"
}

pub struct LogicalFrameEntry {
    pub depth: u32,             // 0 = innermost inlined callee, k = outer physical caller
    pub fn_symbol: Str,
    pub def_span: Span,
    pub call_site_span: Span,   // Span in outer caller where this frame was inlined
    pub is_inlined: bool
}
```

### `AXS-TST-031` — Tiered Debug Emission: Mandatory `-O0` `.debug_line` vs Post-MVP Rich DWARF Sections (`REQ-TOOL-010`, `REQ-TOOL-011`)

1. **Mandatory `-O0` `.debug_line` source mapping (`0163 §38`, `0147 §3–4`, `0693 §434.115`, `REQ-TOOL-010`)**:
   - Debug builds at `-O0` (and `-gline-tables-only`) MUST emit accurate source-line mapping metadata via `.debug_line` (mapping every emitted machine instruction address range `[pc_start, pc_end)` to `(FileId, line, column, is_stmt, prologue_end, epilogue_begin)`), alongside frame unwind tables (`.pdata`/`.xdata` on PE, `.eh_frame` on ELF, `__unwind_info` on Mach-O) and symbol tables (`0163 §38`, `REQ-TOOL-010`).
   - This guarantees 100% accurate source file/line attribution for panics, stack traces, profiler samples, and line-level debugger breakpoints in `-O0` builds without requiring external compilers.
2. **Tiered rich DWARF sections (`0163 §38`, `0147 §4, §52, §67 ATOOL-23`, `REQ-TOOL-011`, `REQ-TOOL-187`)**:
   - Emission of full type/DIE/location DWARF sections (`.debug_info`, `.debug_abbrev`, `.debug_str`, `.debug_loclists`, `.debug_ranges`) is stratified into the full-debug tier (`-g` / `--debug-info=full`) and MAY be deferred or omitted in minimal line-table builds (`0163 §38`, `REQ-TOOL-011`) and completely stripped from production release binaries (`0147 §52 ATOOL-23`, `REQ-TOOL-187`).

### `AXS-TST-032` — Accurate Logical Function Frames Under Aggressive Inlining (`REQ-TOOL-006`)

1. **Inlined call-site provenance chain (`0147 §8, §67 ATOOL-25`, `0662 §20`, `0693 §434.116`, `REQ-TOOL-006`)**:
   - When `compiler/opt` inlines a function $g$ into $f$ (including multi-level nested inlining $f \to g \to h$, `SPEC-73`), the inliner attaches a structured `InlineSiteChain` to every cloned instruction in $f$:
     $$\text{InlineSiteChain}(I) = [(\text{fn}: h, \text{span}: S_h), (\text{fn}: g, \text{call\_site}: S_{g \to h}), (\text{fn}: f, \text{call\_site}: S_{f \to g})]$$
   - The debug metadata emitter lowers `InlineSiteChain` into logical frame records (`LogicalFrameEntry` / DWARF `DW_TAG_inlined_subroutine` + inline line-table entries) so that at any single physical instruction pointer `PC` inside $f$, debuggers, crash/panic unwinders, and `axiomc test --audit-debug` reconstruct the complete ordered stack of **logical function frames** (`h` inside `g` inside `f`) even though only one physical stack frame exists at runtime (`0147 §8`, `ATOOL-25`, `REQ-TOOL-006`).

### `AXS-TST-033` — Honest `OptimizedOut` Variable Representation Without Artificial Physical State (`REQ-TOOL-005`)

1. **Zero artificial physical state for optimized-out variables (`0147 §5–7, §61, §67 ATOOL-24`, `0662 §23, §51 ATEST-16`, `REQ-TOOL-005`)**:
   - Enabling debug metadata (`-g`) at `-O1`, `-O2`, `-O3`, `-Os`, or `-Oz` SHALL NEVER alter code generation, disable optimizations (`SROA`, `DCE`, `SCCP`, `GVN`, `LICM`, register allocation), spill dead values to the stack, extend register live ranges past their last semantic use, or materialize dummy memory locations just to satisfy debugger variable inspection (`0147 §6`, `REQ-TOOL-005`).
   - When a variable has been eliminated by dead-code elimination, overwritten after its last read, or merged by optimization, the debug location table MUST explicitly record `DebugVarStorage.OptimizedOut(reason)` (DWARF empty location description / `<optimized out>`) rather than fabricating an artificial physical state or reporting a stale register/stack slot (`ATEST-16`, `ATOOL-24`, `REQ-TOOL-005`).
   - When a variable is constant-folded (`let x = 10; let y = x + 20`), the compiler may record `DebugVarStorage.ConstantValue("10")` (`DW_OP_lit10` / `DW_OP_implicit_value`) in metadata because doing so requires zero physical registers, zero stack bytes, and zero instructions (`0147 §6`).

### `AXS-TST-034` — Zero Runtime Cost of Trace & Profiling Machinery When Disabled (`REQ-TOOL-008`, `REQ-TOOL-187`)

1. **Complete compile-time erasure when disabled (`0147 §19–24, §48–53, §67`, `0662 §32–36`, `REQ-TOOL-008`, `REQ-TOOL-187`)**:
   - When tracing and instrumentation profiling are disabled (the default in `axiomc build`, `axiomc run`, and non-traced `axiomc test`), the compiler completely elides all trace points (`std.trace.*`, `@trace`) during MIR/`OptIR` lowering (`0147 §20`: *"Trace phải có zero-cost khi disabled"*; `REQ-TOOL-008`):
     - **Zero instructions emitted**: No branch checks (`if trace_enabled`), no NOP sleds, no timestamp reads (`RDTSC`), and no function calls at trace sites;
     - **Zero runtime state**: No global tracer singleton, no event ring buffer, no heap allocations, no background threads, and no profiler/trace symbols linked into the final binary (`0147 §20, §52–53`, `REQ-TOOL-008`, `REQ-TOOL-187`).
2. **Structured deterministic trace when enabled (`0147 §21–23, §48–49`, `0662 §10, §51 ATEST-23`)**:
   - When explicitly enabled via `axiomc test --trace` (or `axiomc build --trace`), the compiler lowers trace points to structured `TraceEvent` emissions with deterministic logical sequence numbers (replayable via `axiomc test --replay-trace=<file>`) without altering observable program semantics (`0147 §49`).

### `AXS-TST-035` — Integrated Verification, Debug & Profiling Diagnostics in `axiomc test` (`REQ-TST-112`)

`compiler/test_runner` (`T818`) natively integrates testing, verification, debugging, and profiling diagnostics (`0662 Goal`, `REQ-TST-112`) via `axiomc test --audit-debug`:
1. Verifies that every compiled test function has a valid target-independent `SemanticDebugModel` (`REQ-TOOL-007`);
2. Verifies that `-O0` builds emit complete, monotonic `.debug_line` mappings covering all source statements (`REQ-TOOL-010`) while tiered `.debug_info`/`.debug_abbrev`/`.debug_str` sections obey the requested debug level (`REQ-TOOL-011`);
3. Verifies that inlined call chains at `-O2` preserve exact `LogicalFrameEntry` stacks (`REQ-TOOL-006`) and mark eliminated variables as `OptimizedOut` with zero instruction changes between `-O2` and `-O2 -g` (`REQ-TOOL-005`);
4. Verifies that builds with tracing disabled contain zero trace symbols, zero trace branches, and zero runtime overhead (`REQ-TOOL-008`).

---

## 7. CLI Surface, Diagnostics, Canonical Examples & Verification Matrix

### `AXS-DOC-050` (`AXS-TST-050`) — CLI Commands & Diagnostic Mapping (`spec/diagnostics.md` §3)

1. **Canonical CLI commands (`T817`, `T818`)**:
   - `axiomc doc [<path>...] [--out-dir <dir>] [--json] [--include-private] [--deny-broken-links] [--test]`
   - `axiomc test [<path_or_filter>...] [--doc] [--diff] [--interp] [--opt-bisect] [--opt-bisect-limit=<N>] [--opt-replay=<manifest>] [--audit-debug] [--trace] [--seed=<u64>] [--jobs=<N>] [--include-ignored] [--format=json|jsonl]`
2. **Diagnostic area & code mapping (`spec/diagnostics.md` §3 AXD-020..021)**:
   - E19.5 introduces **no** new diagnostic area:
     - Broken intra-doc links `[unknown.Item]` emit `AX_NAME_UNRESOLVED` (`data.context = "doc_link"`, `data.doc_link = "<target>"`) at the exact byte span inside the `///` or `//!` comment; non-canonical `::` inside intra-doc links or doc-tests emits `AX_LEX_COLON_COLON` with a `MachineApplicable` fix to `.`.
     - Invalid CLI flags or missing arguments in `axiomc doc` or `axiomc test` emit `AX_DRIVER_USAGE` or `AX_DRIVER_UNKNOWN_OPTION` (exit code `2`).
     - File/directory I/O failures emit `AX_IO_FILE_NOT_FOUND` / `AX_IO_READ_FAILED` / `AX_IO_WRITE_FAILED` (exit code `1`).
     - Unverified MIR or machine IR discovered during `--opt-bisect` or `--opt-replay` under `--verify-each` emits `AX_ICE_MIR_VERIFY` or `AX_ICE_INTERNAL` (`data.stage = "opt_bisect"` or `"opt_replay"`, exit code `3`).

### `AXS-DOC-051` (`AXS-TST-051`) — Positive Canonical Examples

```axiom
//! High-assurance ring buffer metrics module.
//!
//! Provides bounded accumulation with [`RingCounter.push_sample`] and
//! [`RingCounter.average`].

module metrics.ring

/// Fixed-window accumulator for telemetry samples.
///
/// See [`RingCounter.push_sample`] for mutating updates and [`RingCounter.average`]
/// for read-only inspection.
///
/// ```axiom
/// use metrics.ring.RingCounter
/// use metrics.ring.push_sample
/// use metrics.ring.average
///
/// let mut c = RingCounter { sum: 0, count: 0, max_samples: 4 }
/// push_sample(mut_view(c), 12)
/// push_sample(mut_view(c), 28)
/// assert_eq(average(view(c)), 20)
/// ```
@repr(C)
pub struct RingCounter {
    pub sum: i64,
    pub count: i64,
    pub max_samples: i64
}

/// Adds a sample `val` into `counter` if capacity remains.
///
/// Requires an exclusive `mut_view<RingCounter>` capability.
pub fn push_sample(counter: mut_view<RingCounter>, val: i64) -> bool {
    if counter.count >= counter.max_samples {
        return false
    }
    counter.sum = counter.sum + val
    counter.count = counter.count + 1
    true
}

/// Computes the integer average of accumulated samples via a shared `view<RingCounter>`.
@inline
pub fn average(counter: view<RingCounter>) -> i64 {
    if counter.count == 0 {
        0
    } else {
        counter.sum / counter.count
    }
}

test "ring counter differential & inline debug audit" {
    let mut c = RingCounter { sum: 0, count: 0, max_samples: 3 }
    let ok1 = push_sample(mut_view(c), 10)
    let ok2 = push_sample(mut_view(c), 20)
    let ok3 = push_sample(mut_view(c), 30)
    let ok4 = push_sample(mut_view(c), 40)
    assert(ok1 && ok2 && ok3 && !ok4)
    assert_eq(average(view(c)), 20)
}
```

### `AXS-DOC-052` (`AXS-TST-052`) — Negative Canonical Examples (Broken Intra-Doc Link, Compile-Fail Doc-Test & Seeded Pass Bisection)

```axiom
// Example 1: Broken intra-doc link rejected under `axiomc doc --deny-broken-links`
module bad_doc_link

/// Calls [`nonexistent.Module.missing_fn`] to process data.
///        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ERROR [AX_NAME_UNRESOLVED] unresolved intra-doc link `nonexistent.Module.missing_fn`
pub fn run_job(x: i32) -> i32 {
    x + 1
}
```

```axiom
// Example 2: Negative `compile_fail(AX_MOVE_USE_AFTER_MOVE)` doc-test verifying ownership rules
module doc_compile_fail_demo

pub struct Token {
    pub id: i32
}

pub fn consume_token(t: Token) -> i32 {
    t.id
}

/// Consumes a [`Token`] by move. Using the token again after calling
/// [`consume_token`] is a compile-time error:
///
/// ```axiom,compile_fail(AX_MOVE_USE_AFTER_MOVE)
/// use doc_compile_fail_demo.Token
/// use doc_compile_fail_demo.consume_token
///
/// let tok = Token { id: 7 }
/// let first = consume_token(tok)
/// let second = consume_token(tok) // Expected AX_MOVE_USE_AFTER_MOVE
/// ```
pub fn verify_doc_contract() -> i32 {
    0
}
```

```text
// Example 3: `axiomc test --opt-bisect` isolating a seeded pass divergence in O(log2 M) steps
$ axiomc test --opt-bisect tests/run/test_ux/bisect_demo.ax
[opt-bisect] Oracle (--interp) exit=0, Native (-O2, 16 pass steps) exit=42 -> DIVERGENCE
[opt-bisect] step 1/4: testing limit=8  -> exit=42 (diverges; hi=8)
[opt-bisect] step 2/4: testing limit=4  -> exit=0  (matches oracle; lo=5)
[opt-bisect] step 3/4: testing limit=6  -> exit=42 (diverges; hi=6)
[opt-bisect] step 4/4: testing limit=5  -> exit=0  (matches oracle; lo=6)
[opt-bisect] ISOLATED CULPRIT STEP: step_id=6, pass="gvn", fn="bisect_demo.compute_window"
[opt-bisect] wrote replay bundle: target/opt-bisect/bisect_demo.replay.json
```

### `AXS-DOC-053` (`AXS-TST-053`) — E19.5 Implementation & Verification Matrix

| Task | Scope | Required Verification Target | Invariant ID |
|---|---|---|---|
| `T817` | `compiler/docgen` & `compiler/driver/doc_cmd` (`axiomc doc`): `CompilerDB` `///`/`//!` extraction, canonical signatures & effect/container badges, intra-doc `[module.Item]` link resolution, deterministic HTML + JSON index, `axiomc doc --test` executable doc-test runner, and zero production binary impact (`REQ-TOOL-002`, `REQ-TOOL-187`, `REQ-TOOL-298`) | `tests/run/docgen` | `INV-DOC-001` |
| `T818` | `compiler/test_runner`, `compiler/opt/bisect`, & `compiler/driver/test_cmd` (`axiomc test`): `test "..."` discovery, isolated test binary, MIR interpreter differential harness (`REQ-TOOL-009`), `--opt-replay` & `--opt-bisect` pass bisection (`REQ-TOOL-179`), zero production oracle/trace overhead (`REQ-TOOL-003`, `REQ-TOOL-008`), and debug metadata audit (`REQ-TOOL-005..007`, `REQ-TOOL-010..011`, `REQ-TST-112`) | `tests/run/test_ux` | `INV-TST-001` |
| `T819` | End-to-end E19.5 conformance suite certifying `axiomc doc`, `axiomc doc --test`, `axiomc test` MIR differential oracle, `--opt-replay`/`--opt-bisect`, semantic invariance of build features, zero production runtime overhead for oracle/trace/doc/debug metadata, `.debug_line`/logical-inline/`OptimizedOut` debug invariants, and `--interp` vs native equivalence (`0 WEAK-NATIVE`) | `tests/conformance/p19/e19_5_docgen_test_ux` | `INV-TST-002` |

---

## Sources

- `spec/SPEC-21-query-engine-semantic-db.md` (`AXS-QRY-001..034`: demand-driven `CompilerDB` tables, dependency tracking, snapshot diagnostics)
- `spec/SPEC-22-incremental-compilation.md` (`AXS-INC-002`: `DocFingerprint` separation from `AstFingerprint`/`BodyFingerprint`/`AbiFingerprint`)
- `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-012`, `AXS-ART-021..024`: `.axmi` effect metadata, `.axmeta` stripping, detached `.axdbg`)
- `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` (`AXS-PCT-001..044`: `PassContract`, `ProofCertificate`, `TranslationWitness`)
- `spec/SPEC-101-canonical-formatter.md` (`AXS-FMT-002..004`: `TriviaOuterDoc` `///` and `TriviaInnerDoc` `//!` attachment, canonical signature printing)
- `spec/SPEC-103-diagnostics-ux-ai-interface.md` (`AXS-DIAG-001..005`, `AXS-AI-001..021`: `ContainerContract`, `std.meta_effects` `ApiEffectSummary`, `.axmeta`/`.axdb` production binary separation)
- `docs/base/specs/0120 - 265. GPU phải dùng cùng ownership model.md` (§293 `APKG-36`: build features must not change core language semantics)
- `docs/base/specs/0121 - Global Semantic Freeze — Pass #7.md` (§309 `AORACLE-20`: semantic oracle metadata has no production runtime requirement)
- `docs/base/specs/0147 - PART XXVIII — DEBUGGING · TOOLING · PROFILER · SANITIZER · TRACE · PERFORMANCE INTROSPECTION.md` (§1–§69 `ATOOL-20..28`: optimized debugging `OptimizedOut`, logical inlined frames, target-independent semantic debug model, zero-cost disabled trace)
- `docs/base/specs/0161 - AXIOM MIR v0.1.md` (§43–§45 `MIR-001..004`: minimal MIR interpreter & differential execution)
- `docs/base/specs/0163 - 1. Target Description phải là dữ liệu, không phải hàng đống if.md` (§38: `-O0` `.debug_line` emission vs tiered DWARF sections)
- `docs/base/tasks/0361 - BOOTSTRAP-102 — Axiom Testing Architecture & Language Conformance Suite.md` (§1–§64 `ATEST-20..100`)
- `docs/base/tasks/0374 - BOOTSTRAP-115 — Compiler Tooling, Diagnostics & Developer/AI Interface.md` (§30–§32, §36–§41, §56 `ATOOL-20..55`)
- `docs/base/tasks/0418 - BOOTSTRAP-159 — Testing, Assertions, Contracts & Verification-Aware Debugging.md` (§1–§70 `ATEST2-20..70`: `test "..."`, separate test binary, `--opt-bisect`, `ATEST2-58..59`)
- `docs/base/tasks/0423 - BOOTSTRAP-164 — Testing at Scale, Fuzzing, Differential Testing & Compiler Bug Defense.md` (§1–§80 `ATEST2-20..80`: optimization pass bisection & pass replay `ATEST2-68`)
- `docs/base/tasks/0662 - BOOTSTRAP-403 — Testing, Verification, Debugging, Profiling & Diagnostics.md` (§1–§51 `ATEST-01..30`)
- `docs/base/tasks/0693 - BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE.md` (§434.6–§434.9, §434.14–§434.17, §434.113–§434.119, §434.193–§434.200)
- `docs/base/tasks/0695 - BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE.md` (§434.7–§434.11, §434.81–§434.86, §434.146–§434.147 & BOOTSTRAP-435 §435.1–§435.200)
- `docs/base/tasks/0696 - BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE.md` (§434.8–§434.9, §434.14–§434.15, §434.84–§434.85, §434.94–§434.95)
