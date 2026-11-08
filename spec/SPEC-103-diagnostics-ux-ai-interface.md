# SPEC-103 — Canonical Diagnostics UX 2.0, Explain Registry, Machine-Applicable Fixes & AI-Agent Semantic Fact Protocol

- **Status**: draft (T812, 2026-11-08)
- **Owner**: `axiom-architect`
- **Consolidates**: `spec/SPEC-21-query-engine-semantic-db.md` (`AXS-QRY-030..031`), `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-012`, `AXS-ART-014`, `AXS-ART-021..022`), `spec/SPEC-100-lsp-server-ide-engine.md` (`AXS-LSP-001..004`, `AXS-LSP-052`), `spec/SPEC-101-canonical-formatter.md`, `spec/SPEC-102-refactoring-engine-semantic-vcs.md` (`AXS-REF-002`), `spec/diagnostics.md` (`AXD-001..063`), `0101` (`specs/0101` §23–§36, §44–§48 `AIDE-01..25`), `0129` (`specs/0129` §61–§62), `0146` (`specs/0146` Part XXVII §1–§68 `ADIAG-20..48`), `0360` (`tasks/0360`, BOOTSTRAP-101 §1–§51 `ADIAG-20..90`), `0374` (`tasks/0374`, BOOTSTRAP-115 §1–§25), `0421` (`tasks/0421`, BOOTSTRAP-162 §1–§70 `ADIAG-20..70`), `0425` (`tasks/0425`, BOOTSTRAP-166 §76–§80 `ACONT-76`), `0444` (`tasks/0444`, BOOTSTRAP-185 §185.138–§185.152 `AMETA-20..25`), `0448` (`tasks/0448`, BOOTSTRAP-189 §20–§36 `ATOOL-20..40`), `0456` (`tasks/0456`, BOOTSTRAP-197 §197.35–§197.51 `ASTDL-34..37`), `0693` (`tasks/0693`, BOOTSTRAP-434 §434.127–§434.200)
- **Covers**: `REQ-TOOL-004`, `REQ-TOOL-180`, `REQ-TOOL-181`, `REQ-TOOL-182`, `REQ-TOOL-185`, `REQ-TOOL-186`, `REQ-TOOL-187`, `REQ-TOOL-190`, `REQ-TOOL-298`
- **Related**: `spec/SPEC-01-lexical.md`, `spec/SPEC-02-grammar.md`, `spec/SPEC-03-core-semantics.md`, `spec/SPEC-10-ownership.md`, `spec/SPEC-11-capability.md`, `spec/SPEC-12-drop.md`, `spec/SPEC-21-query-engine-semantic-db.md`, `spec/SPEC-24-artifact-format-module-interfaces.md`, `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`, `spec/SPEC-61-reflection-derive.md`, `spec/SPEC-100-lsp-server-ide-engine.md`, `spec/SPEC-102-refactoring-engine-semantic-vcs.md`, `spec/diagnostics.md`, `spec/invariants.md`

## Tóm tắt

SPEC-103 định nghĩa chuẩn **Diagnostics UX 2.0**, từ điển bách khoa mã chẩn đoán `axiomc explain`, bộ máy sửa lỗi tự động có kiểm chứng (`axiomc fix`), thanh tra bố cục kiểu (`axiomc inspect layout`), siêu dữ liệu hợp đồng container/hiệu ứng `std`, và giao thức sự kiện ngữ nghĩa cho tác tử AI (`axiomc query`) trong giai đoạn E19.4:
1. **Diagnostics UX 2.0 với chuỗi nhân-quả đa vị trí & triệt tiêu lỗi dây chuyền (`AXS-DIAG-001..005` / `AXS-DUX-001..005`, `REQ-TOOL-298`)**: Mọi chẩn đoán được sinh từ `CompilerDB` kèm đồ thị nguyên nhân có hướng (`CausalProvenanceChain`: điểm khởi tạo `Origin` → điểm chuyển giao/mượn/bí danh `Transfer`/`Borrow`/`Alias` → điểm vi phạm `Violation`), dấu vân tay tất định 128-bit (`DiagnosticFingerprint`) độc lập câu chữ hiển thị, và cơ chế lan truyền độc tố (`PoisonTaint`) chặn hoàn toàn các lỗi giả tạo phát sinh sau lỗi gốc.
2. **Sửa lỗi tự động phân cấp độ tin cậy & `axiomc fix` giao dịch (`AXS-DIAG-010..014` / `AXS-DUX-010..014`, `REQ-TOOL-185`, `REQ-TOOL-186`)**: Phân loại rõ 4 mức độ áp dụng (`MachineApplicable`, `HasPlaceholders`, `MaybeIncorrect`, `Unspecified`). Lệnh `axiomc fix` chỉ tự động áp dụng các bản sửa `MachineApplicable` không chồng lấp và bắt buộc chạy lại cổng kiểm chứng `CompilerDB` để đảm bảo mã sau khi sửa biên dịch sạch hoặc giảm chặt số lỗi gốc mà không phát sinh lỗi mới.
3. **Từ điển chuẩn `axiomc explain <AX_CODE>` (`AXS-DIAG-020..023` / `AXS-DUX-020..023`)**: Cung cấp tài liệu tra cứu ngoại tuyến cho toàn bộ 18+ vùng mã chẩn đoán, liên kết trực tiếp từng mã `AX_<AREA>_<NAME>` tới quy tắc đặc tả (`AXS-*`), bất biến (`INV-*`), nguyên nhân gốc, ví dụ Axiom chuẩn chạy được (dương tính/âm tính dùng `=` và `.`), và hướng khắc phục.
4. **Giao thức truy vấn sự kiện ngữ nghĩa AI (`axiomc query`), thanh tra bố cục (`axiomc inspect layout`) & siêu dữ liệu `.axmeta` / `std.meta_effects` (`AXS-AI-001..023` / `AXS-DUX-030..053`, `REQ-TOOL-004`, `REQ-TOOL-180..182`, `REQ-TOOL-185..187`, `REQ-TOOL-190`)**: Xuất luồng JSON/NDJSON có phiên bản (`schema_version = 1`) cho đồ thị ký hiệu, vòng đời sở hữu/capability, giải quyết trait (`why`/`why-not`), ranh giới `unsafe`, bố cục kiểu/ABI, hợp đồng container (`Vec`, `HashMap`, `Slice`, `String`), và hiệu ứng hàm `std` mà không cần chạy sinh mã máy. Mọi mã/bản vá do AI đề xuất phải đi qua toàn bộ trình kiểm chứng của compiler, và các thành phẩm `.axmeta`, `.axdb`, thông tin gỡ lỗi tuyệt đối không trở thành phụ thuộc thời gian chạy của tệp thực thi sản xuất.

---

## 1. Diagnostics UX 2.0: Multi-Span Causal Provenance, Fingerprints & Cascade Suppression

### `AXS-DIAG-001` (`AXS-DUX-001`) — Unified `CompilerDB` Diagnostic Authority & Multi-View Rendering (`REQ-TOOL-298`)

1. **Single semantic source (`0146 §1–2, §67 ADIAG-48`, `tasks/0360 §1 ADIAG-20`, `tasks/0421 §1`, `tasks/0693 §434.162–163`)**: Every diagnostic in `axiomc` (`check`, `build`, `run`, `test`, `fix`, `lsp`, and `query`) is constructed once inside `CompilerDB` (`SPEC-21 AXS-QRY-030`) as a structured `Diagnostic2` value. Terminal human rendering (`AXD-062`), `--json` / `--format=json` (`AXD-063`), `--format=jsonl` (NDJSON streaming), LSP `publishDiagnostics` (`SPEC-100 AXS-LSP-060`), and AI fact bundles are pure projections of the same `Diagnostic2` object.
2. **Strict separation of semantic facts from prose (`AXD-002`, `0146 §19, §56 ADIAG-22, 27`, `tasks/0421 §70 ADIAG-54..56`)**: Diagnostic identity is determined exclusively by `(code, primary_span, causal_chain, data, fingerprint)`. Human English prose and future localized message tables (`--locale`) never affect diagnostic identity, sorting, deduplication, or AI consumption.
3. **No internal ID leakage in user prose (`0146 §14`)**: Default human and JSON diagnostic messages format user-level canonical paths and types (`Vec<i32>`, `view<Buffer>`) and SHALL NOT expose raw arena or table indices (`TypeId(1847)`, `HirId(9912)`, `RegionId(17)`) unless `--debug-diagnostics` is explicitly passed.

### `AXS-DIAG-002` (`AXS-DUX-002`) — Multi-Span Causal Provenance Chains (`CausalProvenanceChain`) (`REQ-TOOL-298`)

1. **Causal step graph (`0101 §20–23`, `0146 §7–9, §24–26`, `tasks/0360 §13–18`, `tasks/0374 §14`, `tasks/0421 §5–12, §70 ADIAG-29..38`)**: Diagnostics UX 2.0 extends secondary labels (`AXD-050`) with an ordered, directed causal provenance chain `causal_chain: Slice<CausalStep>` explaining *why* a semantic invariant was violated in terms of Axiom's ownership and capability model (never using Rust borrow-checker lifetime syntax `'a`):

   | `CausalRole` | Canonical Label Tag | Semantic Meaning |
   |---|---|---|
   | `Origin` | `"created here"` / `"declared here"` | Binding declaration, allocation site, or owner scope entry |
   | `Transfer` | `"moved here"` / `"ownership transferred here"` | Value moved into a callee, channel, closure, or new binding |
   | `BorrowShared` | `"shared view created here"` | Read-only `view<T>` capability derived from owner or parent view |
   | `BorrowMut` | `"exclusive mut_view created here"` | Mutable `mut_view<T>` capability derived from owner |
   | `AliasOverlap` | `"conflicting access here"` | Overlapping `READ`/`WRITE` or `WRITE`/`WRITE` place or slice range |
   | `ContainerMutation` | `"container mutated/relocated here"` | `Vec`/`String`/`HashMap` growth or mutation invalidating element views |
   | `SuspensionPoint` | `"suspended across .await / yield here"` | Async `.await` or generator `yield` crossed by a non-live capability/guard |
   | `ScopeExit` | `"owner dropped here"` | Lexical scope exit where backing owner is deterministically dropped |
   | `ObligationOrigin` | `"required by bound here"` | Generic `where` clause, `@derive`, or call site introducing a trait obligation |
   | `Violation` | `"used here"` / `"cannot escape here"` | Primary site where the illegal use, conflict, or escape occurs |

2. **Mandatory provenance completeness (`tasks/0421 §70 ADIAG-34..38`)**:
   - Every `MOVE` diagnostic (`AX_MOVE_USE_AFTER_MOVE`, `AX_CTM_STATIC_MOVE_FORBIDDEN`) MUST carry at least `[Origin, Transfer, Violation]`.
   - Every `CAP` conflict or escape diagnostic (`AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, `AX_CAP_OUTLIVES_OWNER`, `AX_CAP_CONTAINER_RELOC`, `AX_TYPE_STORED_VIEW_ESCAPE`) MUST carry `[Origin, BorrowShared/BorrowMut, ContainerMutation/ScopeExit/AliasOverlap, Violation]` plus the symbolic region description (`data.region`, `data.owner`).
   - Every `TRAIT` or `CONC` obligation failure (`AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`, `AX_DERIVE_FIELD_BOUND`, `AX_DYN_NOT_OBJECT_SAFE`) MUST carry the structural derivation path (`OuterType -> field_name: InnerType -> NonCompliantLeafType`).

```axiom
module compiler.diag.ux2

pub enum CausalRole {
    Origin,
    Transfer,
    BorrowShared,
    BorrowMut,
    AliasOverlap,
    ContainerMutation,
    SuspensionPoint,
    ScopeExit,
    ObligationOrigin,
    Violation
}

pub struct CausalStep {
    pub step_index: u32,
    pub role: CausalRole,
    pub span: Span,
    pub symbol: SymbolId,
    pub fact_summary: Str
}
```

### `AXS-DIAG-003` (`AXS-DUX-003`) — Deterministic 128-Bit `DiagnosticFingerprint` (`0146 §40`)

1. **Message-independent identity (`0146 §6, §40`, `tasks/0421 §70 ADIAG-61`, `SPEC-21 AXS-QRY-030`)**: Every emitted diagnostic computes a deterministic 128-bit `fingerprint: Fingerprint128` via domain-separated BLAKE3 (`"AXIOM-DIAG-FP-v1"`):
   $$\text{DiagnosticFingerprint} = \text{BLAKE3}_{128}(\text{"AXIOM-DIAG-FP-v1"} \parallel \text{code} \parallel \text{SemanticKey}(\text{enclosing\_item}) \parallel \text{relative\_span\_anchor} \parallel \text{canonical\_data\_keys})$$
   where `relative_span_anchor` is the byte offset of `primary` relative to the start of the enclosing item declaration (or file start for top-level lexical/parse errors).
2. **Stability across unrelated edits & message wording**: Editing lines above an item shifts file-global line numbers and byte offsets, but preserves `SemanticKey(enclosing_item)` and `relative_span_anchor`, leaving `DiagnosticFingerprint` unchanged so IDE sessions, CI trackers, and AI repair loops recognize the exact same diagnostic across iterations (`0146 §40–41`).
3. **Deduplication**: Within any `DatabaseSnapshot`, diagnostics sharing an identical `(code, primary)` or identical `DiagnosticFingerprint` are deduplicated before `AXD-060` sorting (`AXD-044`).

### `AXS-DIAG-004` (`AXS-DUX-004`) — Root-Cause Poison-Taint Tracking & Cascading Suppression (`REQ-TOOL-298`)

1. **Fine-grained poison propagation (`tasks/0360 §39–40 ADIAG-39..41, 82..83`, `tasks/0421 §18–23, §70 ADIAG-28`, `tasks/0791 §10`, `SPEC-21 AXS-QRY-031`, `AXD-044`)**: Every AST recovery node, unresolved `SymbolId.ERROR`, `TypeId.ERROR`, `ConstValue.Poisoned`, `TraitResult.Error`, and poisoned `PlaceId` / `LocalId` carries a `PoisonTaint { root_diag_fingerprint: Fingerprint128 }`.
2. **Zero cascading artificial errors (`REQ-TOOL-298`)**:
   - **Type/name taint**: If an expression or binding `x` fails name resolution or type inference (`x: TypeId.ERROR`), subsequent field accesses `x.f`, method calls `x.m()`, indexing `x[i]`, binary operations `x + 1`, and return/argument checks involving `x` propagate `TypeId.ERROR` silently and emit **zero** secondary `AX_TYPE_*` or `AX_NAME_*` diagnostics.
   - **Ownership/capability taint**: Once a local binding `x` is diagnosed with `AX_MOVE_USE_AFTER_MOVE` or `AX_INIT_UNINITIALIZED`, `x` transitions to `OwnershipState.Poisoned` for the remainder of the basic block/dominator subtree so further uses of `x` in the same straight-line path do not emit repetitive duplicate move errors; alternatively, if `x` is re-initialized (`x = new_val`), its taint is cleared and checking resumes normally.
   - **Parser delimiter & statement recovery**: A missing `;` or unclosed delimiter emits one primary `AX_PARSE_*` diagnostic at the exact recovery point and resynchronizes at the next statement/item boundary (`SPEC-02 §9`, `SPEC-100 AXS-LSP-030`) without cascading into bogus top-level item errors.
3. **Sibling & cross-item independence (`SPEC-21 AXS-QRY-031`)**: Poison taint is strictly scoped to the dataflow/type dependency cone of the failing node. Unpoisoned statements in the same function and independent functions/modules in `CompilerDB` MUST still be checked and report all genuine errors in the same compilation run.

### `AXS-DIAG-005` (`AXS-DUX-005`) — Terminal UX 2.0 & JSON Schema v1 Backward-Compatible Extensions

1. **Unicode-aware multi-span terminal rendering (`compiler/diag/ux2`, `0146 §9, §21–23, §65 ADIAG-28..30`, `tasks/0693 §434.167–168`, `AXD-062`)**:
   - Preserves the exact `AXD-062` header `<severity>[<code>]: <message>` and ` --> <path>:<line>:<col>` layout for single-span diagnostics so all existing `axiom0` and P1–P18 golden tests remain 100% compatible.
   - When `causal_chain` contains multi-step provenance across lines in the same file, renders numbered causal connectors (`[1] created here`, `[2] moved here`, `[3] used here after move`) in ascending line order within the unified snippet gutter, computing display columns over Unicode extended grapheme clusters (correctly aligning multi-byte UTF-8 Vietnamese text such as `"Xin chào"`).
2. **JSON Schema v1 compatible extension (`0146 §57`, `AXD-063`)**: In `--json` (and `--format=json` / `--format=jsonl`), each diagnostic object preserves all mandatory Schema 1 keys (`id`, `code`, `severity`, `message`, `primary`, `labels`, `notes`, `helps`, `fixes`, `data`) in `AXD-063` order and attaches structured UX 2.0 fields (`fingerprint`, `causal_chain`, `spec_rules`) inside `data` (or as top-level fields when `--json-schema=2` / `axiomc query --diagnostics` is requested), ensuring 100% backward compatibility with `tools/axtest.py` (`AXD-063`).

---

## 2. Confidence-Graded Machine-Applicable Fix-Its & Transactional `axiomc fix`

### `AXS-DIAG-010` (`AXS-DUX-010`) — Four-Tier Fix Applicability Taxonomy (`0146 §10–12, §42`, `tasks/0360 §9`)

Every structured `Fix` attached to a diagnostic carries an explicit `Applicability` grade (`compiler/diag/ux2`, bridging `AXD-056` wire strings and canonical enum variants):

| Variant (`Applicability`) | JSON Wire String (`AXD-056`) | Semantic Guarantee & Tooling Rule |
|---|---|---|
| `MachineApplicable` | `"machine-applicable"` | Proven by `CompilerDB` to preserve program intent and resolve the diagnostic (`0146 §12 ADIAG-41`). Safe for unattended `axiomc fix`, IDE auto-fix on save, and autonomous AI agent loops. |
| `HasPlaceholders` | `"has-placeholders"` | Structural edit is valid (`match` arm skeleton, missing type annotation `: /* Type */`), but contains a `<placeholder>` token requiring user or AI completion before compilation succeeds. Never auto-applied by default `axiomc fix`. |
| `MaybeIncorrect` | `"maybe-applicable"` | Plausible repair (e.g., passing `view(x)` instead of `x`, or `.clone()`), but multiple valid semantic choices exist or program behavior may change (`tasks/0421 §8`). Requires explicit confirmation (`axiomc fix --allow-maybe-incorrect` or interactive IDE selection). |
| `Unspecified` | `"manual-review"` | Illustrative code edit shown for human comprehension only. Never applied automatically by `axiomc fix`. |

### `AXS-DIAG-011` (`AXS-DUX-011`) — Well-Formedness & Safety Invariants of Structured `TextEdit` Sets

1. **Span & UTF-8 validity (`AXD-055`, `tasks/0360 ADIAG-30..32, 84..85`)**: Every `Fix` consists of `{ message: Str, applicability: Applicability, edits: Slice<TextEdit> }` where each `TextEdit` is `{ span: Span, replacement: Str }`.
2. **Non-overlapping sorted edits**: Within a single `Fix`, all `edits` MUST be sorted by `(span.file, span.start, span.end)` and MUST be strictly non-overlapping (`edit[i].span.end <= edit[i+1].span.start` when in the same file). Every `span.start` and `span.end` MUST lie on a valid UTF-8 codepoint boundary (`SPEC-01 §1`).
3. **Canonical syntax & safety law (`tasks/0360 ADIAG-84..85`, `0146 §65 ADIAG-26`)**:
   - A `Fix` SHALL NEVER emit non-canonical or forbidden Axiom syntax (`::`, `:=`, `var`, `import`, `mod`, prefix `&x`, or lifetime annotations `'a`).
   - A `Fix` SHALL NEVER be graded `MachineApplicable` if it wraps safe code in `unsafe { ... }`, adds `@allow_unsafe`, weakens a `--safety-profile`, or introduces `std.mem.bitcast` / raw pointer casts (`0146 §65 ADIAG-26`: *"Unsafe Suggestions Must Not Be Presented As Safe Fixes"*). Any suggestion that crosses an `unsafe` boundary MUST be at most `MaybeIncorrect` or placed in `helps`.

### `AXS-DIAG-012` (`AXS-DUX-012`) — Required `MachineApplicable` Fix-It Catalog (`T813`)

In addition to the lexical and parser fix-its of `SPEC-01 AXS-LEX-100` (`AX_LEX_COLON_COLON -> "."`, `AX_LEX_COLON_EQ -> "="`, `AX_LEX_BAD_BASE_PREFIX -> "0x"/"0b"/"0o"`, `AX_LEX_BAD_DIGIT_SEPARATOR`) and `SPEC-02 AXS-GRM-101` (`AX_PARSE_VAR -> "let mut"`, `AX_PARSE_IMPORT -> "use"`, `AX_PARSE_REFERENCE_OPERATOR -> remove "&"`, `AX_PARSE_ARRAY_TYPE_ORDER -> "[N]T"`), `compiler/diag/ux2` (`T813`) provides verified `MachineApplicable` (and graded `MaybeIncorrect` / `HasPlaceholders`) fixes for semantic diagnostics when `CompilerDB` proves uniqueness:
1. **`AX_TYPE_ASSIGN_IMMUTABLE` (local binding)**: When a local binding `let x = init` is mutated inside the same function and is not captured across a shared boundary, emit a `MachineApplicable` edit inserting `mut ` after `let ` at `Origin` (`let mut x = init`).
2. **`AX_UNSAFE_UNNECESSARY_IMPL`**: When `unsafe impl Trait for T` is written for a safe `Trait`, emit a `MachineApplicable` edit removing the redundant `unsafe ` keyword.
3. **`AX_NAME_UNRESOLVED_IMPORT` / missing `use` for unambiguous workspace symbol**: When an unresolved identifier matches exactly one visible `pub` item in an already-loaded dependency/std module, emit a `MaybeIncorrect` fix inserting `use <module>.<Item>` in the file's import block.
4. **`AX_MOVE_USE_AFTER_MOVE` when callee expects `view<T>` or type implements `Copy`/`Clone`**:
   - If a call argument was explicitly wrapped or if a binding is passed to a parameter whose signature accepts `view<T>`, emit a `MachineApplicable` edit `view(x)`.
   - If the callee takes ownership `T` and `x` is used later only by read views, emit `MaybeIncorrect` edits (`reorder read before move` or explicit `.clone()`).
5. **`AX_PAT_NONEXHAUSTIVE`**: Emit a `HasPlaceholders` fix inserting the missing constructor patterns (`Variant => todo()`) synthesized from `CompilerDB` `PAT` exhaustiveness matrix (`SPEC-102 AXS-REF-012`).

### `AXS-DIAG-013` (`AXS-DUX-013`) — Transactional `axiomc fix` Applicator & `CompilerDB` Re-Verification Gate (`REQ-TOOL-186`)

1. **Read-only default compilation (`AXD-057`, `tasks/0360 §10 ADIAG-31`)**: `axiomc check`, `axiomc build`, and `axiomc run` NEVER modify source files on disk.
2. **CLI entrypoint (`T813`)**: `axiomc fix [<path>...]` (with flags `--dry-run`, `--json`, `--allow-maybe-incorrect`, `--code <AX_CODE>`, `--max-iterations <N>` default `4`) runs the transactional fix engine:
   - **Step 1 (Collect & Filter)**: Evaluates `CompilerDB` on the target workspace/files, collects all diagnostics, and selects candidate fixes matching the allowed applicability (`MachineApplicable` only by default) and optional `--code` filter.
   - **Step 2 (Conflict Resolution)**: Partitions candidate edits by `SourceFileId`. If two candidate fixes in the same file have overlapping byte spans (`a.end > b.start`), the engine keeps the earlier diagnostic in `AXD-060` order and defers the overlapping fix to the next iteration.
   - **Step 3 (In-Memory Application & Mandatory `CompilerDB` Re-Verification, `REQ-TOOL-186`)**: Applies the non-overlapping edits in memory to a candidate `VfsOverlay` snapshot (`R_next`) and re-runs `CompilerDB` semantic verification (`parse_module`, `resolve_module`, `typeck_body`, `ownership_check`, `mir_verify`).
   - **Step 4 (Monotonic Convergence & Rollback Guarantee)**: A batch of edits on file `F` is accepted if and only if:
     a. None of the original `DiagnosticFingerprint`s targeted by the applied fixes remain in `F`;
     b. No new `error` diagnostics (fingerprints not present in `R_curr`) were introduced in `F` or its dependents; and
     c. Total error count strictly decreases (`errors(R_next) < errors(R_curr)`) or warning count decreases with zero errors.
     If any condition fails, the offending fix is rolled back in memory and rejected (`status = "rolled_back"`).
   - **Step 5 (Atomic Commit)**: In normal mode, accepted buffers are written to disk via crash-safe atomic temp-file rename (`<file>.tmp.<pid>`). In `--dry-run` mode, disk files are untouched and the unified diff / JSON fix report is written to `stdout`.

### `AXS-DIAG-014` (`AXS-DUX-014`) — Multi-Iteration Fix-Point Loop & Idempotence

`axiomc fix` repeats Steps 1–4 up to `--max-iterations` (default `4`) until no `MachineApplicable` fixes remain or a fixed point is reached. Running `axiomc fix` a second time immediately after a converged `axiomc fix` run MUST apply `0` edits and exit with code `0` (if zero errors remain) or `1` (if unfixable user errors remain).

---

## 3. Canonical `axiomc explain` Encyclopedia Registry

### `AXS-DIAG-020` (`AXS-DUX-020`) — `axiomc explain <AX_CODE>` CLI & Registry Architecture (`0101 §24`, `0146 §15–18`)

1. **CLI interface (`T813`)**:
   - `axiomc explain <AX_CODE>` (and driver alias `axiom explain <AX_CODE>`) looks up `<AX_CODE>` in the compiled-in canonical explain registry (`compiler/diag/explain`, `compiler/driver/explain_cmd`) and writes the structured explanation to `stdout` with exit code `0`.
   - `axiomc explain <AX_CODE> --json` writes the machine-readable JSON explanation object (`schema_version = 1`) to `stdout` with exit code `0`.
   - `axiomc explain --list [--area <AREA>] [--json]` lists all registered diagnostic codes in deterministic `AXD-031` registry order with their area, severity, spec rule IDs, and one-line summary.
   - Passing an unknown or unregistered code to `axiomc explain <UNKNOWN>` emits `AX_DRIVER_UNKNOWN_DIAG_CODE` (or `AX_DRIVER_USAGE` with `data.code = "<UNKNOWN>"`) on `stderr` and exits with code `2`.
2. **Offline & zero-IO execution (`tasks/0693 §434.154–155`)**: `axiomc explain` is 100% self-contained inside the compiler binary and requires no network access, no external documentation files, and no project workspace on disk.

### `AXS-DIAG-021` (`AXS-DUX-021`) — Required Schema of an `ExplainEntry`

Every entry in `compiler/diag/explain` (`ExplainEntry`) MUST contain the following structured fields (`0101 §24`, `0146 §16–18`, `tasks/0360 §12`):

```axiom
module compiler.diag.explain

pub struct ExplainEntry {
    pub code: Str,                    // e.g. "AX_MOVE_USE_AFTER_MOVE"
    pub area: Str,                    // One of the canonical areas (LEX, PARSE, NAME, TYPE, ..., LINK, DRIVER, ICE)
    pub severity: Str,                // "error" or "warning"
    pub title: Str,                   // Concise human title, e.g. "Use of Value After Ownership Transfer"
    pub summary: Str,                 // One-paragraph semantic definition
    pub why_it_happens: Str,          // Causal explanation in Axiom's ownership/capability/type model
    pub spec_rules: Slice<Str>,       // Normative rule IDs, e.g. ["SPEC-10 AXS-OWN-002", "AXD-020"]
    pub invariants: Slice<Str>,       // Enforced invariants, e.g. ["INV-SEM-001", "INV-DIAG-001"]
    pub bad_example: Str,             // Minimal canonical Axiom snippet triggering the diagnostic
    pub good_example: Str,            // Minimal canonical Axiom snippet fixing the diagnostic
    pub common_fixes: Slice<Str>,     // Ordered actionable remediation steps
    pub related_codes: Slice<Str>     // Related AX_* codes
}
```

### `AXS-DIAG-022` (`AXS-DUX-022`) — Complete Area Coverage & Spec Traceability (`0146 §17–18 ADIAG-31..32`)

1. **100% area coverage**: The explain registry MUST cover all 18 core areas of `spec/diagnostics.md §3` (`LEX`, `PARSE`, `NAME`, `TYPE`, `TRAIT`, `PAT`, `MOVE`, `INIT`, `CAP`, `DROP`, `UNSAFE`, `CONST`, `VERIFY`, `FFI`, `LINK`, `IO`, `DRIVER`, `ICE`) plus the self-hosted `axiomc` domain prefixes established in `spec/diagnostics.md §3 AXD-021` (`CONC`, `ASYNC`, `SIMD`, `TARGET`, `SEC`, `PANIC`, `CTM`, `REFLECT`, `DERIVE`, `GEN`, `DYN`, `QUERY`).
2. **Bidirectional spec linkage (`ADIAG-31`)**: Every `ExplainEntry` cites at least one normative `SPEC-*` rule (`AXS-*` or `AXD-*`) and one `INV-*` invariant from `spec/invariants.md`.
3. **Canonical example hygiene (`ADR-0007`, `ADIAG-32`)**: Every `good_example` in `ExplainEntry` MUST use strictly canonical Axiom syntax (`=` for binding/assignment, `.` for paths, `use` for imports) and pass `axiomc check` with zero errors (except for `LEX`/`PARSE` entries deliberately illustrating rejected foreign tokens in `bad_example`).

---

## 4. AI-Agent Semantic Fact & Query Protocol (`axiomc query`)

### `AXS-AI-001` (`AXS-DUX-030`) — Versioned Machine-Readable Fact Protocol (`AXCP v1`) & Zero-Codegen Firewall (`REQ-TOOL-180`, `REQ-TOOL-185`)

1. **Structured semantic reasoning export (`0101 §25–32 AIDE-20`, `0146 §38–39, §57–62 ADIAG-38..43`, `tasks/0421 §70 ADIAG-42..44, 69`, `tasks/0448 §26–28, §33–34, §36 ATOOL-24, 26, 34, 35, 38`, `tasks/0693 §434.127–134, 164–166`, `REQ-TOOL-180`, `REQ-TOOL-185`)**:
   - `axiomc query <subcommand> [options]` (implemented in `compiler/ai_query` and `compiler/driver/query_cmd`, `T814`) exposes `CompilerDB`'s internal semantic reasoning as deterministic, machine-readable JSON (`--format=json`, default) or newline-delimited JSON fact streams (`--format=jsonl` / NDJSON) on `stdout`.
   - Every response envelope carries the canonical protocol header:
     ```json
     {
       "protocol": "AXCP",
       "schema_version": 1,
       "compiler_semantic_version": "0.1.0",
       "revision": 1,
       "target": "x86_64-windows",
       "profile": "hosted",
       "safety_profile": "system",
       "codegen_invoked": false,
       "facts": []
     }
     ```
2. **Zero-codegen semantic query firewall (`REQ-TOOL-185`, `ATOOL-24`, `SPEC-100 AXS-LSP-004`)**:
   - All semantic `axiomc query` subcommands (`symbol`, `type`, `ownership`, `capabilities`, `trait`, `effects`, `container`, `unsafe-map`, `deps`, `context`, `facts`) evaluate only demand-driven `CompilerDB` frontend and semantic verification tables (`parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `typeck_body`, `trait_solve`, `const_eval`, `mir_body`, `layout_of`).
   - They SHALL NEVER invoke `OptIR` optimization passes, LIR lowering, register allocation, machine code encoding, `ObjectWriter`, or `LinkerCore`, and MUST report `"codegen_invoked": false` in the response envelope.
   - Only explicit optimization remark queries (`axiomc query opt-remarks` / `axiomc inspect optimize`) invoke the read-only `OptIR` analysis pipeline, and even those never write object or executable files.
3. **Fact domain & certainty tagging (`0101 §28 AIDE-16..17`, `tasks/0421 §70 ADIAG-39..40, 64..67`, `tasks/0448 §36 ATOOL-36`)**: Every exported fact record carries:
   - `fact_domain`: `"semantic"` (language-level truth: types, `Copy`/`Drop`/`Send`/`Share`, ownership, capabilities, effects), `"layout_abi"` (target-parameterized size, alignment, offsets, calling convention), or `"optimization"` (profile-dependent remarks: inlining, BCE, escape promotion, vectorization);
   - `certainty`: `"Proven"` (`Certainty.Proven`), `"Inferred"`, `"Observed"` (PGO/profile weight), `"Possible"` (`Certainty.Possible`), or `"Unknown"` (`Certainty.Unknown`). Optimization remarks and heuristic observations never masquerade as `"semantic"` `"Proven"` facts.

### `AXS-AI-002` (`AXS-DUX-031`) — Canonical `axiomc query` Subcommands & Fact Schemas (`T814`)

`compiler/ai_query` and `compiler/driver/query_cmd` (`T814`) implement the following subcommands over `CompilerDB`:

| Subcommand | CLI Invocation | Exported Fact Payload (`facts`) |
|---|---|---|
| `symbol` | `axiomc query symbol <path_or_span> <file>` | `SemanticKey`, `kind` (`fn`, `struct`, `enum`, `trait`, `const`, `static`, `type`), visibility (`pub` / private), generic params, signature, `TypeId` properties, `FnContractSummary` effects, callers, callees, and source span (`0101 §27`, `0146 §59`, `tasks/0693 §434.128`). |
| `type` | `axiomc query type <TypePath_or_span> <file>` | Canonical type name, `copy`, `drop`, `send`, `share`, `sized`, `@repr`, `@align`, `size`, `align`, field layouts, implemented traits, and `ContainerContract` if applicable (`0101 §27`, `0146 §60`). |
| `ownership` | `axiomc query ownership <fn_or_local> <file>` | Per-local and per-place ownership lifeline graph: declaration span, `Copy` vs `!Copy` move semantics, state transitions (`Uninit -> Owned -> BorrowedShared -> BorrowedMut -> Moved -> Dropped`), drop scope, and active capabilities (`0101 §19–20`, `0146 §61`, `tasks/0374 §19`). |
| `capabilities` | `axiomc query capabilities <fn_name> <file>` | Capability lifeline table for all `view<T>` and `mut_view<T>` bindings: `cap_id`, `access` (`READ` vs `WRITE`), `owner_place`, symbolic region (`buf[0..n]`, `self.field`), live span range, disjointness proof status (`Disjoint`, `Overlap`, `Unknown`), and return provenance (`0101 §21`, `tasks/0374 §20`, `tasks/0448 §23`). |
| `trait` | `axiomc query trait <Trait> <Type> <file>` | Structured `why` / `why-not` obligation derivation tree: root goal `Trait(Type)`, matched `impl` header or auto-trait structural recursion (`Send`/`Share`), per-field/per-bound child obligation status (`Proven` vs `NoSolution` vs `Ambiguous`), and failing leaf witness (`tasks/0374 §18, §21`, `tasks/0421 §70 ADIAG-37`). |
| `effects` | `axiomc query effects <fn_path> <file>` | Interprocedural `ApiEffectSummary` (`allocates`, `blocks`, `synchronizes`, `panics`, `os_io`, `ffi`, `unsafe_required`, `required_caps`, `invalidates`, `complexity`) (`tasks/0456 §197.36–38`, `REQ-TOOL-190`). |
| `container` | `axiomc query container <TypePath> [<file>]` | `ContainerContract` semantic properties (`storage_kind`, `contiguous`, `relocatable`, `address_stable`, `random_access`, `preserves_order`, `concurrency_model`, `invalidation_rules`) (`tasks/0425 §78–80`, `REQ-TOOL-181`). |
| `unsafe-map` | `axiomc query unsafe-map <file_or_dir>` | Inventory of all `unsafe` blocks, `unsafe fn` declarations, `unsafe trait`/`unsafe impl` items, raw-pointer dereferences, `MakeView`/`MakeMutView` bridges, `extern` FFI blocks, `@at`/`@addr` bindings, and `bitcast` sites (`0101 §31 AIDE-14`). |
| `deps` | `axiomc query deps <file_or_dir>` | Module and package dependency DAG with edge kinds (`SemanticInput`, `ABI`, `NativeLink`, `Comptime`, `RuntimeCap`) and reachability chains (`axiomc query why-runtime <cap>`) (`0101 §32`, `tasks/0448 §24`). |
| `context` | `axiomc query context <symbol> <file>` | Self-contained AI context bundle (`tasks/0448 §28, §36 ATOOL-35`) combining target symbol definition, referenced type definitions, direct callers/callees, trait impls, ownership/capability summary, effect contract, and active diagnostics in that symbol's cone. |
| `facts` | `axiomc query facts <file> [--format=jsonl]` | Full NDJSON stream of symbol, type, ownership, capability, trait, effect, and diagnostic facts for the module without AST/MIR internal noise (`0146 §58`). |

### `AXS-AI-003` (`AXS-DUX-032`) — Ownership & Capability Lifeline Fact Graph Schema (`REQ-TOOL-180`)

For `axiomc query ownership` and `axiomc query capabilities`, `compiler/ai_query` exports the exact MIR/THIR-proven ownership and capability state transitions (`0101 §19–21`, `0146 §61`, `tasks/0374 §19–20`, `tasks/0421 §6–12`):

```axiom
module compiler.ai_query

pub enum OwnershipFactState {
    Uninitialized,
    Owned,
    PartiallyMoved,
    Moved,
    BorrowedShared(u32), // count of active view<T>
    BorrowedMut,         // active exclusive mut_view<T>
    Dropped,
    Poisoned
}

pub struct OwnershipLifelineFact {
    pub symbol: Str,
    pub ty: Str,
    pub is_copy: bool,
    pub has_drop: bool,
    pub decl_span: Span,
    pub events: Slice<OwnershipEventFact>
}

pub struct CapabilityLifelineFact {
    pub cap_binding: Str,
    pub kind: Str,             // "view" or "mut_view"
    pub target_type: Str,
    pub owner_symbol: Str,
    pub region_expr: Str,      // e.g. "buf[0..mid]" or "record.header"
    pub created_at: Span,
    pub last_used_at: Span,
    pub escapes_via_return: bool,
    pub disjoint_from: Slice<Str>
}
```

### `AXS-AI-004` (`AXS-DUX-033`) — Trait & Auto-Trait `Why` / `Why-Not` Proof Tree Schema (`tasks/0374 §18, §21`)

When querying `axiomc query trait <Trait> <Type> <file>` (e.g., `axiomc query trait Send WorkerState app.ax`), the solver exports a deterministic proof/refutation tree (`TraitResolutionTrace`):
1. If `Trait(Type)` holds (`status = "Implemented"`), the trace lists the matched `impl` declaration or structural derivation over all fields/variants.
2. If `Trait(Type)` fails (`status = "NotImplemented"` or `"Ambiguous"`), the trace identifies the exact structural field path (`WorkerState.handle -> Rc<Socket>`) or unsatisfied `where` bound (`T: Copy`) responsible for the rejection, eliminating any need for an AI agent to guess why a bound failed.

### `AXS-AI-005` (`AXS-DUX-034`) — Structured Optimization & Legality/Profitability Remark Queries (`tasks/0374 §23–25`, `tasks/0421 §70 ADIAG-39..41, 64`)

When `axiomc query opt-remarks <fn_name> <file>` (or `axiomc inspect optimize <fn_name> <file>`) is invoked, the compiler runs the read-only `OptIR` analysis passes (`SPEC-25`, `SPEC-70..74`) and emits structured `OptimizationRemarkFact` records separating:
- `pass`: `"inline"`, `"sroa"`, `"escape_promote"`, `"bce"`, `"licm"`, `"loop_vec"`, `"slp_vec"`, `"devirt"`;
- `outcome`: `"Applied"` vs `"Missed"`;
- `legality`: `"Proven"` vs `"Possible"` vs `"Unknown"` with explicit blocker reason (`"address_observable"`, `"may_alias_mut_view"`, `"loop_carried_dep"`, `"bounds_range_unknown"`, `"open_world_dyn"`);
- `profitability`: `"Profitable"` vs `"RejectedByCostModel"`.
These remarks are tagged `fact_domain = "optimization"` and NEVER alter language semantics or emit compile errors (`SPEC-25 AXS-PCT-010`, `AXD-042`).

---

## 5. Type Layout Inspector (`axiomc inspect layout`), `.axmeta` Container Contracts & `std.meta_effects`

### `AXS-AI-010` (`AXS-DUX-040`) — Command-Line Type Layout & ABI Inspection (`axiomc inspect layout`) (`0129 §61–62`, `REQ-TOOL-004`)

1. **CLI command (`0129 §61`, `tasks/0448 §32`, `REQ-TOOL-004`, `T814`)**:
   - `axiomc inspect layout <TypeName> <file> [--target <triple>] [--json]` (and alias `axiomc query layout <TypeName> <file>`) evaluates `CompilerDB.layout_of(TypeId)` and `CallConvDesc.classify_type(TypeId)` for the requested nominal or composite type on the active (or `--target`-specified) `TargetDesc` (`SPEC-81 AXS-TGTD-004`) without running codegen.
2. **Required layout & ABI fields (`0129 §61–62`, `SPEC-50`, `SPEC-51`)**:
   - `type_name`: canonical qualified name (e.g., `app.User` or `std.collections.Vec<i32>`);
   - `target`: canonical target triple (e.g., `"x86_64-windows"`, `"aarch64-linux"`, `"wasm32-wasi"`);
   - `repr`: `"axiom"`, `"C"`, `"transparent"`, `"packed(N)"`, or `"int(u8..u64)"`;
   - `size`: total byte size (`u64`);
   - `align`: required byte alignment (`u64`);
   - `stride`: array element stride (`align_up(size, align)`);
   - `padding_bytes`: total internal and tail padding bytes (`u64`);
   - `niche`: optional niche range `(offset, bit_width, valid_range)` used for `Option<T>` layout compression (`0129 §102`);
   - `fields`: ordered list of `{ name, ty, offset, size, align, padding_before }` in physical memory offset order (along with declaration-order index);
   - `variants`: for `enum` / `union`, discriminant tag size/offset and per-variant payload offsets;
   - `abi_passing`: physical ABI classification (`0129 §62`: `Register(reg_class)`, `RegisterPair(r0, r1)`, `IndirectCallerCopy`, `IndirectSret`, `Hfa(elem_ty, count)`) distinguishing logical memory layout (`size`, `align`) from calling-convention ABI lowering.
3. **Human & JSON output**: Default terminal output prints the human table of `0129 §61` (`Type: <Name>`, `size: <N>`, `align: <A>`, per-field `offset: <O>`) to `stdout`; `--json` prints the `schema_version = 1` JSON object to `stdout`.

```axiom
module compiler.ai_query.layout

pub struct FieldLayoutFact {
    pub name: Str,
    pub ty: Str,
    pub decl_index: u32,
    pub offset: u64,
    pub size: u64,
    pub align: u64,
    pub padding_before: u64
}

pub struct TypeLayoutFact {
    pub type_name: Str,
    pub target: Str,
    pub repr: Str,
    pub size: u64,
    pub align: u64,
    pub stride: u64,
    pub padding_bytes: u64,
    pub copy: bool,
    pub drop: bool,
    pub send: bool,
    pub share: bool,
    pub abi_passing: Str,
    pub fields: Slice<FieldLayoutFact>
}
```

### `AXS-AI-011` (`AXS-DUX-041`) — Container Semantic Properties in `.axmeta` & `CompilerDB` (`tasks/0425 §76–80`, `REQ-TOOL-181`)

1. **Contract-driven container model (`tasks/0425 §76–80 ACONT-76`, `REQ-TOOL-181`, `T814`)**: Rather than hard-coding ad-hoc container optimizers throughout the backend, Axiom exports a structured `ContainerContract` for standard and user-defined collection types into `.axmi` / `.axmeta` (`SPEC-24 AXS-ART-004` `SectionType.EffectsCapabilities = 9` / `AIIndex = 13`) and exposes it via `axiomc query container <Type>` and `axiomc inspect --axmeta <file>`:

```axiom
module std.meta_effects

pub enum StorageKind {
    InlineFixed,        // [N]T, ArrayVec<T, N>
    HeapContiguous,     // Vec<T>, String, Box<T>
    HeapTable,          // HashMap<K, V>, HashSet<T>
    HeapNodeGraph,      // BTreeMap<K, V>, LinkedSlab<T>
    BorrowedContiguous, // Slice [T], Str, view<T>, mut_view<T>
    SharedRefCounted    // Rc<T>, Arc<T>
}

pub struct ContainerContract {
    pub type_name: Str,
    pub ownership_kind: Str,        // "owning", "borrowed_view", "shared_rc"
    pub storage_kind: StorageKind,
    pub contiguous: bool,
    pub relocatable: bool,          // true if elements may move in memory on growth/rehash
    pub address_stable: bool,       // true if element addresses stay valid across insertions
    pub random_access: bool,        // O(1) index access
    pub preserves_order: bool,      // insertion/sequence order preserved
    pub concurrency_model: Str,     // "single_owner_send_if_t", "thread_local_rc", "atomic_arc", "lock_free"
    pub invalidation_rules: Slice<Str> // e.g. ["push/reserve/insert/remove invalidates active view<T>/mut_view<T> (AX_CAP_CONTAINER_RELOC)"]
}
```

2. **Canonical built-in & `std` container table (`tasks/0425 §78–79`, `REQ-TOOL-181`)**:

   | Container Type | `storage_kind` | `contiguous` | `relocatable` | `address_stable` | `random_access` | `preserves_order` | `invalidation_rules` |
   |---|---|---|---|---|---|---|---|
   | `[N]T` (Array) | `InlineFixed` | `true` | `false` (in-place) | `true` (while owner unmoved) | `true` | `true` | `"moving array invalidates element views (AX_CAP_OUTLIVES_OWNER)"` |
   | `Slice<T>` / `view<[T]>` | `BorrowedContiguous` | `true` | `false` | `true` (for borrow duration) | `true` | `true` | `"owner mutation or drop forbidden while slice view is live (AX_CAP_CONFLICT_MUT)"` |
   | `Str` | `BorrowedContiguous` | `true` | `false` | `true` (for borrow duration) | `true` (byte) | `true` | `"backing String mutation or reallocation forbidden while Str is live (AX_CAP_CONTAINER_RELOC)"` |
   | `Vec<T>` | `HeapContiguous` | `true` | `true` | `false` | `true` | `true` | `"push, reserve, insert, remove, truncate, clear invalidate element views (AX_CAP_CONTAINER_RELOC)"` |
   | `String` | `HeapContiguous` | `true` | `true` | `false` | `true` (byte) | `true` | `"push_str, reserve, clear invalidate Str/byte views (AX_CAP_CONTAINER_RELOC)"` |
   | `HashMap<K, V>` | `HeapTable` | `false` | `true` | `false` | `false` (`O(1)` key lookup) | `true` (insertion order, `INV-KERN-007`) | `"insert, remove, reserve, rehash invalidate entry/value views (AX_CAP_CONTAINER_RELOC)"` |
   | `Box<T>` | `HeapContiguous` | `true` | `false` | `true` (heap pointee) | `true` | `true` | `"moving Box transfers ownership and invalidates derived views"` |
   | `Arc<T>` | `SharedRefCounted` | `true` | `false` | `true` | `true` | `true` | `"shared read-only view<T>; interior mutation requires Mutex/RwLock/Atomic"` |

### `AXS-AI-012` (`AXS-DUX-042`) — `std.meta_effects`: Standard Library Allocation, Blocking, Synchronization & Effect Metadata (`tasks/0456 §197.35–51`, `REQ-TOOL-190`)

1. **Standard library effect contract registry (`std/meta_effects`, `tasks/0456 §197.35–38, §197.45–47, §197.51 ASTDL-34..38`, `REQ-TOOL-190`, `T814`)**:
   - Module `std.meta_effects` defines the canonical `ApiEffectSummary` data structures and registers the verified cost, allocation, blocking, synchronization, invalidation, panic, and authority capability metadata for `std` public APIs (`std.core`, `std.alloc`, `std.collections`, `std.io`, `std.fs`, `std.net`, `std.thread`, `std.sync`, `std.future`, `std.mem`).
   - `CompilerDB` combines static interprocedural effect inference (`SPEC-25 AXS-PCT-021`, `SPEC-24 AXS-ART-012`) with `std.meta_effects` contracts and exports them in `.axmi` / `.axmeta` and `axiomc query effects <api_path>`.

```axiom
module std.meta_effects

pub enum AllocBehavior {
    NeverAllocates,     // Str.len, Slice.get, Atomic.load, Mutex.lock
    MayAllocate,        // Vec.push, String.push_str, HashMap.insert (on growth)
    AlwaysAllocates     // Box.new, Vec.with_capacity(n > 0), Arc.new
}

pub enum BlockingBehavior {
    NonBlocking,        // pure compute, Atomic.*, Slice.*, Vec.*
    MayBlock,           // File.read,File.write, TcpStream.read, Mutex.lock, Condvar.wait, Thread.join
    AsyncSuspends       // AsyncFile.read, AsyncTcpStream.read, AsyncMutex.lock, sleep
}

pub enum SyncBehavior {
    None,               // single-threaded / unsynchronized
    AcquireReleaseLock, // Mutex.lock/unlock, RwLock.read/write
    AtomicOrdering,     // Atomic.load/store/cas/fetch_add, fence
    ThreadLifecycle,    // Thread.spawn, JoinHandle.join, Channel.send/recv
    AsyncTaskWake       // Waker.wake, TaskGroup.spawn, AsyncSemaphore.acquire
}

pub struct ApiEffectSummary {
    pub api_path: Str,                  // e.g. "std.collections.Vec.push"
    pub receiver_mode: Str,             // "none", "view", "mut_view", "move", "copy"
    pub allocates: AllocBehavior,
    pub blocks: BlockingBehavior,
    pub synchronizes: SyncBehavior,
    pub panics: Str,                    // "never", "on_oob", "on_oom", "on_overflow", "on_poison", "explicit"
    pub invalidates_views: bool,        // true if call can relocate/invalidate existing element views
    pub invalidation_detail: Str,       // e.g. "views:on_reallocation"
    pub required_authority_caps: Slice<Str>, // e.g. ["FsCap"] or ["NetCap"] in sandbox/comptime
    pub unsafe_preconditions: Slice<Str>,    // non-empty for unsafe fn APIs
    pub complexity: Str                 // e.g. "O(1)", "amortized O(1)", "O(n)"
}
```

2. **Representative normative `std` effect table (`tasks/0456 §197.35–47`, `REQ-TOOL-190`)**:

   | `api_path` | `allocates` | `blocks` | `synchronizes` | `panics` | `invalidates_views` | `complexity` |
   |---|---|---|---|---|---|---|
   | `std.core.Str.len` | `NeverAllocates` | `NonBlocking` | `None` | `"never"` | `false` | `"O(1)"` |
   | `std.collections.Vec.len` | `NeverAllocates` | `NonBlocking` | `None` | `"never"` | `false` | `"O(1)"` |
   | `std.collections.Vec.push` | `MayAllocate` | `NonBlocking` | `None` | `"on_oom"` | `true` (`"views:on_reallocation"`) | `"amortized O(1)"` |
   | `std.collections.Vec.get` | `NeverAllocates` | `NonBlocking` | `None` | `"never"` (returns `Option`) | `false` | `"O(1)"` |
   | `std.collections.HashMap.insert` | `MayAllocate` | `NonBlocking` | `None` | `"on_oom"` | `true` (`"views:on_rehash"`) | `"amortized O(1)"` |
   | `std.sync.Mutex.lock` | `NeverAllocates` | `MayBlock` | `AcquireReleaseLock` | `"on_poison"` | `false` | `"O(1) uncontended"` |
   | `std.sync.Atomic.load` | `NeverAllocates` | `NonBlocking` | `AtomicOrdering` | `"on_invalid_ordering"` | `false` | `"O(1)"` |
   | `std.fs.File.read` | `NeverAllocates` | `MayBlock` | `None` (`os_io`) | `"never"` (returns `Result`) | `false` | `"O(bytes_read)"` |
   | `std.io.AsyncFile.read` | `NeverAllocates` | `AsyncSuspends` | `AsyncTaskWake` | `"never"` | `false` | `"O(bytes_read) async"` |
   | `std.mem.volatile_load` | `NeverAllocates` | `NonBlocking` | `None` (`volatile`) | `"never"` (`unsafe` aligned valid addr) | `false` | `"O(1)"` |

---

## 6. AI Verification Gate & Zero-Runtime-Overhead Invariants

### `AXS-AI-020` (`AXS-DUX-050`) — Sole Compiler Verification Authority over AI-Generated & AI-Patched Code (`REQ-TOOL-180`, `REQ-TOOL-186`)

1. **No AI safety bypass (`0101 §26, §48 AIDE-21`, `0146 §63, §65 ADIAG-44`, `tasks/0421 §70 ADIAG-44..46`, `tasks/0448 §27, §35, §36 ATOOL-27..29`, `tasks/0693 §434.129–130`, `REQ-TOOL-180`, `REQ-TOOL-186`)**:
   - AI agents, automated fixers (`axiomc fix`), refactoring pipelines (`SPEC-102 AXS-REF-002`), and external synthesis tools are untrusted source producers.
   - There exists **no** compiler flag, pragma, attribute, environment variable, or JSON-RPC/CLI mode that trusts AI-generated code or skips lexing, parsing, name/visibility resolution, type checking, trait coherence, ownership/move checking (`SPEC-10`), `view`/`mut_view` capability exclusivity (`SPEC-11`), deterministic `Drop` elaboration (`SPEC-12`), concurrency/async `Send`/`Share` verification (`SPEC-30..33`), safety profile checks (`SPEC-53`), or the `Verified MIR` / `verify_mc` barriers (`INV-PIPE-001..005`).
2. **Transactional AI patch verification (`axiomc query verify-patch`, `T814`)**:
   - `axiomc query verify-patch <patch_or_candidate.ax> [--target-file <src.ax>]` evaluates a proposed AI source edit or `AXPATCH` bundle (`SPEC-102`) inside an ephemeral `CompilerDB` overlay snapshot without touching disk files.
   - If the candidate introduces any `error` diagnostic (e.g., `AX_MOVE_USE_AFTER_MOVE`, `AX_CAP_CONFLICT_MUT`, `AX_CAP_OUTLIVES_OWNER`, `AX_UNSAFE_REQUIRED`, `AX_SEC_UNSAFE_FORBIDDEN`, `AX_TYPE_MISMATCH`), `verify-patch` rejects the candidate (`"accepted": false`), returns the structured diagnostics and causal chains (`AXS-DIAG-002`), and leaves the workspace unchanged.

### `AXS-AI-021` (`AXS-DUX-051`) — Strict Separation of `.axmeta`, `.axdb` & Debug Artifacts from Production Executables (`REQ-TOOL-182`, `REQ-TOOL-187`)

1. **Distinct artifact domains (`tasks/0444 §185.138–140, §185.151–152 AMETA-20..25`, `tasks/0448 §29–30, §36 ATOOL-33, 39`, `tasks/0693 §434.196–197`, `SPEC-24 AXS-ART-001, 021..022, 024`, `SPEC-61 AXS-RFL-002`, `REQ-TOOL-182`, `REQ-TOOL-187`)**:
   - **Compile-time & AI metadata (`.axmi` / `.axmeta`)**: Contains exported symbols, types, traits, `ContainerContract`, `ApiEffectSummary`, and AI query indexes (`magic = "AXMI0001"` / `"AXMETA01"`). Used only by `CompilerDB`, `LinkerCore`, IDE/LSP, and `axiomc query`/`inspect`.
   - **Incremental query database snapshot (`.axdb` / `.axiom-cache`)**: Persistent on-disk `CompilerDB` memo/fingerprint cache (`SPEC-22`). Used only by toolchain invocations to accelerate warm rebuilds and IDE startup; deleting `.axdb` never alters program behavior.
   - **Detached debug metadata (`.axdbg` / `.pdb` / DWARF debug sections)**: Maps machine addresses to source lines, scopes, and variable locations (`SPEC-24 AXS-ART-024`).
   - **Opt-in runtime reflection descriptors (`@reflect(runtime)`)**: Emitted into `.rdata` only for types explicitly annotated with `@reflect(runtime)` (`SPEC-61 AXS-RFL-002`); never emitted universally.
2. **Zero runtime dependency & mandatory final-image stripping (`REQ-TOOL-182`, `REQ-TOOL-187`, `T814`)**:
   - Production executables (`--kind exe` / `bin`) and dynamic libraries (`--kind dll` / `cdylib`) SHALL NEVER require `.axmeta`, `.axmi`, `.axdb`, or `.axdbg` files to be present at runtime.
   - When linking relocatable `.obj`/`.o` or `.lib`/`.a` inputs that carry embedded `.axmeta`, `.axmir`, or `.axlto` sections (`IMAGE_SCN_LNK_INFO | IMAGE_SCN_MEM_DISCARDABLE`), the linker strips 100% of those sections from the final `.exe`, `.dll`, `.so`, `.dylib`, or `.wasm` image (`SPEC-24 AXS-ART-022`, `SPEC-89 AXS-ARTM-029`).
   - `axiomc inspect binary <exe>` (and `axiomc query verify-production-binary <exe>`) verifies that the linked image contains zero `.axmeta`, `.axmir`, `.axlto`, or `.axdb` sections and zero imports from compiler/IDE tooling libraries.

---

## 7. CLI Surface, Diagnostics, Canonical Examples & Verification Matrix

### `AXS-DIAG-050` (`AXS-AI-050` / `AXS-DUX-060`) — CLI Commands & Diagnostic Mapping (`spec/diagnostics.md` §3)

1. **Canonical CLI commands (`T813`, `T814`)**:
   - `axiomc explain <AX_CODE> [--json]` / `axiomc explain --list [--area <AREA>] [--json]`
   - `axiomc fix [<path>...] [--dry-run] [--json] [--allow-maybe-incorrect] [--code <AX_CODE>] [--max-iterations <N>]`
   - `axiomc inspect layout <TypeName> <file> [--target <triple>] [--json]`
   - `axiomc query <symbol|type|ownership|capabilities|trait|effects|container|unsafe-map|deps|context|facts|opt-remarks|verify-patch|verify-production-binary> ... [--format=json|jsonl]`
2. **Diagnostic area & code mapping (`spec/diagnostics.md` §3 AXD-020..021)**:
   - E19.4 introduces **no** new diagnostic area: `compiler/diag/ux2`, `compiler/diag/explain`, and `compiler/ai_query` emit and explain the existing 18 canonical areas (`LEX`, `PARSE`, `NAME`, `TYPE`, `TRAIT`, `PAT`, `MOVE`, `INIT`, `CAP`, `DROP`, `UNSAFE`, `CONST`, `VERIFY`, `FFI`, `LINK`, `IO`, `DRIVER`, `ICE`) and `axiomc` domain prefixes (`CONC`, `ASYNC`, `SIMD`, `TARGET`, `SEC`, `PANIC`, `CTM`, `REFLECT`, `DERIVE`, `GEN`, `DYN`, `QUERY`).
   - Corpus shorthand codes in `0101 §23–24`, `0146 §4, §37–41`, `tasks/0374 §14–16`, and `tasks/0421 §2–12` map per `AXD-010` to canonical codes:
     - `E_USE_AFTER_MOVE` / `EOWN_MOVED` / `AX_MOVE_0003` $\rightarrow$ `AX_MOVE_USE_AFTER_MOVE`;
     - `E_UNINITIALIZED_READ` $\rightarrow$ `AX_INIT_UNINITIALIZED`;
     - `E_CAPABILITY_CONFLICT` / `ECAP_CONFLICT` / `AX_VIEW_0002` $\rightarrow$ `AX_CAP_CONFLICT_MUT` / `AX_CAP_CONFLICT_READ`;
     - `E_CAPABILITY_LIFETIME` / `AX_VIEW_0001` $\rightarrow$ `AX_CAP_OUTLIVES_OWNER` / `AX_TYPE_STORED_VIEW_ESCAPE`;
     - `E_TRAIT_AMBIGUOUS` / `AX_METHOD_0001` $\rightarrow$ `AX_TRAIT_AMBIGUOUS_METHOD`;
     - `AX_TRAIT_0012` $\rightarrow$ `AX_DYN_NOT_OBJECT_SAFE`;
     - `E_NONEXHAUSTIVE_MATCH` $\rightarrow$ `AX_PAT_NONEXHAUSTIVE`;
     - `E_CONSTANT_TIME_VIOLATION` $\rightarrow$ `AX_SEC_TIMING_LEAK`.
   - CLI usage errors in `axiomc explain`, `axiomc fix`, `axiomc inspect layout`, or `axiomc query` (such as an unknown diagnostic code passed to `axiomc explain`, an unknown query subcommand, or a missing target type/symbol) emit `AX_DRIVER_USAGE` or `AX_DRIVER_UNKNOWN_OPTION` (exit code `2`); file I/O errors emit `AX_IO_FILE_NOT_FOUND` / `AX_IO_READ_FAILED` / `AX_IO_WRITE_FAILED` (exit code `1`); internal invariant failures in the fix-it re-verification gate emit `AX_ICE_INTERNAL` (`data.stage = "fix_verify"`, exit code `3`).

### `AXS-DIAG-051` (`AXS-AI-051` / `AXS-DUX-061`) — Positive Canonical Examples

```axiom
// Example 1: Clean ownership, disjoint capability views, layout inspection & std effect queries
// Commands:
//   axiomc check packet_proc.ax
//   axiomc inspect layout PacketHeader packet_proc.ax --json
//   axiomc query capabilities split_payload packet_proc.ax --format=json
//   axiomc query effects packet_proc.append_tag packet_proc.ax --format=json
module packet_proc

use std.collections.Vec

@repr(C)
pub struct PacketHeader {
    pub magic: u32,
    pub flags: u16,
    pub length: u16,
    pub seq_no: u64
}

pub fn split_payload(mut buf: [8]u8) -> u8 {
    // Disjoint mutable slice views [0..4] and [4..8] are proven non-overlapping by CompilerDB:
    let left = mut_view(buf[0..4])
    let right = mut_view(buf[4..8])
    left[0] = 10
    right[0] = 20
    left[0] + right[0]
}

pub fn append_tag(items: mut_view<Vec<i32>>, tag: i32) -> usize {
    // `axiomc query effects` reports:
    //   allocates = MayAllocate, blocks = NonBlocking, invalidates_views = true ("views:on_reallocation")
    items.push(tag)
    items.len()
}

pub fn main() -> i32 {
    let hdr = PacketHeader {
        magic: 0x4158_4D31,
        flags: 1,
        length: 64,
        seq_no: 7
    }
    let arr: [8]u8 = [0, 0, 0, 0, 0, 0, 0, 0]
    let sum = split_payload(arr)
    if sum == 30 && hdr.length == 64 {
        0
    } else {
        1
    }
}
```

### `AXS-DIAG-052` (`AXS-AI-052` / `AXS-DUX-062`) — Negative Canonical Examples (Causal Provenance, Cascade Suppression, Fix-It & AI Gate Rejection)

```axiom
// Example 2: Multi-span causal provenance (`Origin -> Transfer -> Violation`) & zero cascading errors
// Command: axiomc check --json bad_move.ax
module bad_move

pub struct Buffer {
    pub data: i32
}

pub fn consume(b: Buffer) -> i32 {
    b.data
}

pub fn read_view(b: view<Buffer>) -> i32 {
    b.data
}

pub fn trigger_use_after_move() -> i32 {
    let buf = Buffer { data: 42 }        // [1] CausalRole.Origin: `buf` created here (owning `Buffer`)
    let first = consume(buf)             // [2] CausalRole.Transfer: ownership of `buf` moved into `consume` here
    let second = read_view(view(buf))    // [3] CausalRole.Violation: ERROR [AX_MOVE_USE_AFTER_MOVE] `buf` used here after move
    // PoisonTaint on `buf` suppresses any duplicate secondary move error on the next line (AXS-DIAG-004):
    let third = buf.data
    first + second + third
}
```

```axiom
// Example 3: Container relocation invalidating an active element view (`AX_CAP_CONTAINER_RELOC`)
// and AI patch rejection (`axiomc query verify-patch`)
module bad_container_borrow

use std.collections.Vec

pub fn invalidate_elem_view(mut v: Vec<i32>) -> i32 {
    v.push(10)
    let elem = view(v[0])                // [1] CausalRole.BorrowShared: shared `view<i32>` borrows from `v` here
    v.push(20)                           // [2] CausalRole.ContainerMutation: `Vec.push` may reallocate `v` (ContainerContract.relocatable == true)
    *elem                                // [3] CausalRole.Violation: ERROR [AX_CAP_CONTAINER_RELOC] `elem` used after container mutation
}
```

```axiom
// Example 4: `MachineApplicable` fix-it convergence via `axiomc fix`
// Before `axiomc fix`:
//   `let count = 0` followed by `count = count + 1` emits `AX_TYPE_ASSIGN_IMMUTABLE`
//   with MachineApplicable fix inserting `mut ` -> `let mut count = 0`.
// After `axiomc fix`, `CompilerDB` re-verifies that the module compiles with 0 errors:
module fixable_mut

pub fn increment_three_times() -> i32 {
    let mut count = 0
    count = count + 1
    count = count + 2
    count
}
```

### `AXS-DIAG-053` (`AXS-AI-053` / `AXS-DUX-063`) — E19.4 Implementation & Verification Matrix

| Task | Scope | Required Verification Target | Invariant ID |
|---|---|---|---|
| `T813` | `compiler/diag/ux2` multi-span causal provenance chains, `DiagnosticFingerprint`, `PoisonTaint` cascade suppression, confidence-graded fix-its & transactional `axiomc fix` applicator, and `compiler/diag/explain` + `compiler/driver/explain_cmd` (`axiomc explain <CODE>`) | `tests/run/diag_ux2` | `INV-DIAG-009` |
| `T814` | `compiler/ai_query` & `compiler/driver/query_cmd` (`axiomc query`, `axiomc inspect layout`), `std/meta_effects` container & `std` API effect metadata in `.axmeta` / `CompilerDB`, AI patch verification gate, and production binary `.axmeta`/`.axdb` non-embedding check | `tests/run/ai_query` | `INV-DIAG-010` |
| `T815` | End-to-end E19.4 conformance suite certifying causal provenance, cascade suppression, `axiomc explain`, `axiomc fix` convergence, `axiomc inspect layout`, `.axmeta` container/`std` effect queries, AI verification gate, production binary separation, and `--interp` vs native equivalence (`0 WEAK-NATIVE`) | `tests/conformance/p19/e19_4_diagnostics_ai` | `INV-DIAG-011` |

---

## Sources

- `spec/SPEC-21-query-engine-semantic-db.md` (`AXS-QRY-030..031`: snapshot-bound diagnostics, poison taint, cascade suppression)
- `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-012`, `AXS-ART-014`, `AXS-ART-021..022`: `.axmi` effect summaries, `AIIndex`, `.axmeta` stripping)
- `spec/SPEC-100-lsp-server-ide-engine.md` (`AXS-LSP-001..004`, `AXS-LSP-052`, `AXS-LSP-060`: single `CompilerDB` authority, zero-codegen query firewall, LSP diagnostics & code actions)
- `spec/SPEC-102-refactoring-engine-semantic-vcs.md` (`AXS-REF-002`: mandatory post-transformation `CompilerDB` verification gate)
- `spec/diagnostics.md` (`AXD-001..063`: diagnostic taxonomy, 18 areas, severities, JSON schema v1, fix-it model)
- `docs/base/specs/0101 - Axiom — IDE, LSP, Refactoring & AI-native Tooling v0.1.md` (§23–§36, §44–§48 `AIDE-01..25`)
- `docs/base/specs/0129 - AXIOM LANGUAGE SPECIFICATION v0.1 — Part VIII.md` (§61–§62 `axiom inspect layout`, layout vs ABI)
- `docs/base/specs/0146 - Part XXVII — Diagnostics · Error Model · IDELSP · AI-Agent Interface.md` (§1–§68 `ADIAG-20..48`)
- `docs/base/tasks/0360 - BOOTSTRAP-101 — Axiom Diagnostics, Error Model & Compiler UX.md` (§1–§51 `ADIAG-20..90`)
- `docs/base/tasks/0374 - BOOTSTRAP-115 — Compiler Tooling, Diagnostics & DeveloperAI Interface.md` (§1–§25)
- `docs/base/tasks/0421 - BOOTSTRAP-162 — Diagnostics, Error Recovery, Compiler UX & AI-Native Compiler Interface.md` (§1–§70 `ADIAG-20..70`)
- `docs/base/tasks/0425 - BOOTSTRAP-166 — Standard Library Collections, Containers & Data Structures.md` (§76–§80 `ACONT-76`)
- `docs/base/tasks/0444 - BOOTSTRAP-185 — Reflection, Metadata, Runtime Type Information & Dynamic Loading.md` (§185.138–§185.152 `AMETA-20..25`)
- `docs/base/tasks/0448 - BOOTSTRAP-189 — Developer Experience, IDE, Tooling & AI-Native Compiler Interface.md` (§20–§36 `ATOOL-20..40`)
- `docs/base/tasks/0456 - BOOTSTRAP-197 — Standard Library Architecture, std Layering & Core Abstractions.md` (§197.35–§197.51 `ASTDL-34..37`)
- `docs/base/tasks/0693 - BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE & DEVELOPER EXPERIENCE.md` (§434.127–§434.200)
