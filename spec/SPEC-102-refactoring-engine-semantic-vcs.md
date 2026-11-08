# SPEC-102 — Canonical Semantic Refactoring Engine, LSP Code Actions & AST-Aware `AXDIFF` / `AXMERGE` / `AXPATCH` / `AXHISTORY` / `AXVCS` Specification

- **Spec ID**: `SPEC-102`
- **Status**: `draft` (`T808`, 2026-11-08)
- **Owner**: `axiom-architect` (`T808`, `E19.3`)
- **Consumers**: `T809` (`CompilerDB` semantic refactorings & LSP `codeAction` in `compiler/refactor/transforms`, `compiler/refactor/code_actions`, `compiler/lsp/handlers/mod.ax`, `tests/run/refactor_engine`), `T810` (`AXDIFF`, `AXMERGE`, `AXPATCH`, `AXHISTORY`, and `AXVCS` in `compiler/refactor/vcs`, `std/vcs`, `compiler/driver/refactor_cmd`, `tests/run/semantic_vcs`), `T811` (`E19.3` conformance suite in `tests/conformance/p19/e19_3_refactoring_vcs`), `T319` (`P19` certification gate)
- **Consolidates**: `0101` (`specs/0101`, §12–§17, §25–§29, §45–§48 `AIDE-01..03, 05..10, 15, 20..21, 24`), `0448` (`tasks/0448`, BOOTSTRAP-189 §14, §16–§17, §31, §36 `ATOOL-20..22, 27..30`), `1059` (`tasks/1059`, BOOTSTRAP-794 `AXDIFF` §1–§59, §117–§127, §138–§140, §241 `DIFF-INV-01..40`), `1060` (`tasks/1060`, BOOTSTRAP-795 `AXMERGE` §1–§62, §85–§106, §120 `MERGE-INV-01..40`), `1061` (`tasks/1061`, BOOTSTRAP-796 `AXPATCH` §1–§55, §113–§114 `PATCH-INV-01..40`), `1062` (`tasks/1062`, BOOTSTRAP-797 `AXHISTORY` §1–§45, §130–§132 `HISTORY-INV-01..40`), `1063` (`tasks/1063`, BOOTSTRAP-798 `AXVCS` §1–§60, §199 `VCS-INV-01..40`), `1064` (`tasks/1064`, BOOTSTRAP-799 `AXPATCH` §1–§75, §112–§115, §145–§149, §199 `PATCH-INV-01..40`)
- **Covers**: `REQ-TOOL-183`, `REQ-TOOL-186`, `REQ-TOOL-301`, `REQ-TOOL-302`, `REQ-TOOL-303`, `REQ-TOOL-304`, `REQ-TOOL-305`
- **Depends on**: `SPEC-01` (Lexical Structure), `SPEC-02` (Surface Grammar), `SPEC-10` (Ownership & Move Semantics), `SPEC-11` (View & Capability Model), `SPEC-12` (Deterministic Drop), `SPEC-21` (Query Engine & `CompilerDB`), `SPEC-22` (Incremental Compilation), `SPEC-100` (LSP Server, `AXEDITOR` & `AXCODEEDITOR`), `SPEC-101` (Canonical Formatter & Lossless CST)
- **Diagnostics**: `AX_LEX_*`, `AX_PARSE_*`, `AX_NAME_*`, `AX_TYPE_*`, `AX_TRAIT_*`, `AX_PAT_*`, `AX_MOVE_*`, `AX_INIT_*`, `AX_CAP_*`, `AX_DROP_*`, `AX_UNSAFE_*`, `AX_IO_*`, `AX_DRIVER_*`, `AX_ICE_INTERNAL`
- **Invariants**: `INV-REF-001`, `INV-REF-002`, `INV-REF-003`

## Tóm tắt

Đặc tả `SPEC-102` định nghĩa bộ máy tái cấu trúc mã nguồn ngữ nghĩa (*semantic refactoring engine*) dựa trên `CompilerDB`, giao thức `textDocument/codeAction` & `codeAction/resolve` cho `axiomc lsp`, và chuỗi hạ tầng quản lý thay đổi nhận biết AST/ngữ nghĩa (`AXDIFF`, `AXMERGE`, `AXPATCH`, `AXHISTORY`, `AXVCS`) cho giai đoạn E19.3:
1. **`CompilerDB` là nguồn sự thật duy nhất và là cổng kiểm chứng bắt buộc (`REQ-TOOL-183`, `REQ-TOOL-186`)**: Mọi phép biến đổi tái cấu trúc tự động của IDE hoặc đề xuất chỉnh sửa từ tác tử AI (`ATOOL-27..29`) đều tính toán trên đồ thị định danh ngữ nghĩa (`SymbolId`, `LocalId`, `PlaceId`, `TypeId`, trạng thái sở hữu, năng lực `view<T>`/`mut_view<T>`, hiệu ứng) của `CompilerDB` và bắt buộc phải vượt qua cổng tái kiểm chứng ngữ nghĩa đầy đủ trước khi phát hành `WorkspaceEdit` hoặc ghi nhận thay đổi. Không một công cụ tái cấu trúc hay tác tử AI nào được phép vượt qua bộ kiểm tra kiểu, quyền sở hữu, năng lực bộ nhớ hoặc tự ý chèn `unsafe`.
2. **Các phép tái cấu trúc bảo toàn ngữ nghĩa và tích hợp LSP `codeAction` (`0101 §14–§17`)**: Định nghĩa chính xác `extract_function` (tự động tổng hợp tham số sở hữu, `view<T>`, `mut_view<T>`, kiểu trả về và hiệu ứng `! ErrorType` từ luồng sở hữu/năng lực qua biên vùng chọn), `extract_variable` / `inline_variable` (bảo toàn thứ tự định giá, hiệu ứng phụ và vòng đời năng lực), `populate_match_arms` (sinh các nhánh `match` còn thiếu từ bộ kiểm tra vét cạn của trình biên dịch), `organize_imports` (chuẩn hóa, khử trùng lặp và sắp xếp `use` theo đường dẫn dấu chấm `.`), cùng `change_signature`, `move_item` và `convert_capability_view`.
3. **So sánh, hợp nhất và vá mã nguồn nhận biết AST/ngữ nghĩa (`AXDIFF` `REQ-TOOL-301`, `AXMERGE` `REQ-TOOL-302`, `AXPATCH` `REQ-TOOL-303`)**: `AXDIFF` (`compiler/refactor/vcs/diff.ax`) đối sánh cây CST/AST và bảng ký hiệu `CompilerDB` để phân biệt thay đổi định dạng/chú thích với di chuyển (`MOVED`), đổi tên (`RENAMED`), thay đổi chữ ký (`SIGNATURE_CHANGED`) và tương thích API/ABI. `AXMERGE` (`merge.ax`) thực hiện hợp nhất 3 chiều (`BASE`, `LEFT`, `RIGHT`) theo thứ tự ưu tiên `SymbolId` → cấu trúc ngữ nghĩa → AST → văn bản và phát hiện xung đột tường minh (`ConflictId` tất định). `AXPATCH` (`patch.ax`) áp dụng, đảo ngược (`reverse`), hợp성 (`compose`) và `rebase` các bản vá AST/ngữ nghĩa/văn bản theo giao dịch nguyên tử kèm kiểm tra tiền điều kiện băm trạng thái (`Precondition`) và hậu điều kiện (`Postcondition`).
4. **Lịch sử dòng dõi ký hiệu `AXHISTORY` (`REQ-TOOL-304`) và kho lưu trữ tất định `AXVCS` (`REQ-TOOL-305`)**: `AXHISTORY` (`std/vcs`, `compiler/driver/refactor_cmd`) theo dõi đồ thị DAG phiên bản và dòng dõi từng `SymbolId` qua các phép đổi tên, di chuyển giữa các mô-đun, trích xuất/nội tuyến hàm và tách/gộp ký hiệu. `AXVCS` cung cấp kho đối tượng định địa chỉ theo nội dung (*content-addressed store*: `BLOB`, `TREE`, `SEMANTIC`, `PATCH`, `REVISION`) với thứ tự cây tất định, giao dịch cập nhật tham chiếu (`Ref`) nguyên tử và khả năng tương thích qua bộ chuyển đổi Git.

---

## 1. Unified Semantic Authority (`CompilerDB`), Verification Gate & AI Proposal Boundary (`compiler/refactor/*`)

### `AXS-REF-001` — `CompilerDB` as Single Semantic Refactoring Authority (`REQ-TOOL-183`)

1. **Unified semantic kernel (`0101 §1, §14, §48 AIDE-01, AIDE-09`, `tasks/0448 §1, §16, §36 ATOOL-20..21`)**: The refactoring engine (`compiler/refactor/transforms`, `compiler/refactor/code_actions`) and semantic version-control suite (`compiler/refactor/vcs`, `std/vcs`) SHALL query `CompilerDB` (`SPEC-21`, `SPEC-22`, `SPEC-100`) as their sole source of syntactic and semantic truth. Separate regex-based refactorers, shadow parsers, or heuristic text-search symbol rewriters are strictly forbidden.
2. **Identity-driven transformations (`tasks/0448 §5, §16 ATOOL-22`)**: Every refactoring target is resolved first to a typed generational entity handle (`SymbolId`, `FunctionId`, `TypeId`, `LocalId`, `PlaceId`, `ExprId`; `SPEC-100 AXS-LSP-002`) within a pinned `DatabaseSnapshot(RevisionId)`. No transformation may match or rewrite identifiers by raw string equality without verifying `SymbolId` / `LocalId` binding identity in `CompilerDB`.
3. **Canonical surface emission (`SPEC-101 AXS-FMT-001..029`)**: All source fragments synthesized by refactoring operations, quick-fixes, `AXMERGE`, or `AXPATCH` MUST use canonical Axiom surface syntax (`=` for bindings and assignments, `.` for module/type/member paths, 4-space indentation, `LF` line endings, and lossless CST trivia preservation per `SPEC-101`) — never legacy `:=`, `var`, or `::`.

### `AXS-REF-002` — Mandatory Post-Transformation Semantic Re-Verification & AI Proposal Gate (`REQ-TOOL-186`)

1. **Compiler as sole verification judge (`0101 §14, §26, §48 AIDE-20..21`, `tasks/0448 §14, §17, §36 ATOOL-27..29`)**: Automated refactoring rules, IDE code actions, and AI developer interfaces may propose source or AST modifications, but `CompilerDB` remains the sole authority to verify and accept them:
   $$\text{Candidate Edit / Patch } \Delta \xrightarrow{\text{apply to scratch overlay}} S_{\text{cand}} \xrightarrow{\text{CompilerDB verify}} \text{Accept} \lor \text{Reject}(\text{Diagnostics})$$
2. **Inviolable safety boundaries (`REQ-TOOL-186`, `ATOOL-28`)**: Neither an automated refactoring transform nor an AI-proposed patch may:
   - bypass or silence type checking (`SPEC-03`), trait coherence, or pattern exhaustiveness;
   - bypass ownership transfer rules (`SPEC-10`, e.g. duplicating a `!Copy` value or causing a use-after-move `AX_MOVE_USED_AFTER_MOVE`);
   - bypass memory capability rules (`SPEC-11`, e.g. creating overlapping `mut_view<T>` and `view<T>` capabilities `AX_CAP_CONFLICT_MUT` / `AX_CAP_CONFLICT_READ` or returning an escaping capability `AX_CAP_OUTLIVES_OWNER`);
   - bypass deterministic drop (`SPEC-12`), concurrency `Send`/`Share` verification (`SPEC-30`), or safety profile policies (`SPEC-53`);
   - automatically synthesize `unsafe` blocks, `unsafe fn` qualifiers, raw pointer casts, or `@allow_unsafe` attributes unless explicitly invoked by an audited user command with explicit provenance (`tasks/0448 §14`, `tasks/1064 §130`).
3. **Transactional verification rollback (`ATOOL-29`, `tasks/1064 §47–§50 PATCH-INV-05..07, 17`)**: Before any refactoring or semantic patch commits a `WorkspaceEdit` to `AXEDITOR` / disk, the engine evaluates the candidate overlay in `CompilerDB` (`parse_module`, `resolve_module`, `item_signature`, `typeck_body`, `ownership_check`, `mir_verify`). If the transformation introduces any new semantic error or violates a transformation precondition, the transaction MUST abort cleanly and leave the original buffer and `CompilerDB` revision untouched.

### `AXS-REF-003` — Refactoring Applicability Classes & Lossless CST Edit Generation (`REQ-TOOL-183`, `REQ-TOOL-186`)

1. **Applicability classification (`0101 §14–§15`, `spec/diagnostics.md §7`)**: Every refactoring action and diagnostic fix-it carries an explicit `RefactorApplicability` tag:
   - `MachineApplicable`: Proven semantics-preserving by `CompilerDB` (`certainty == Proven`); safe for unattended batch execution, `axiomc refactor`, and IDE auto-apply.
   - `HasPlaceholders`: Syntactically and type-theoretically valid scaffolding containing explicit user placeholders (such as `todo()` bodies in generated `match` arms or default parameter values in `change_signature`).
   - `MaybeIncorrect`: Suggested semantic transformation whose behavioral equivalence depends on external user intent not fully decidable from static types alone; never auto-applied without explicit user or policy confirmation (`tasks/1061 PATCH-INV-30`).
2. **Non-overlapping atomic `WorkspaceEdit` (`SPEC-100 AXS-LSP-022`, `SPEC-101 AXS-FMT-003..004`)**: Every accepted refactoring produces a deterministic `WorkspaceEdit` consisting of per-document `EditTransaction` batches whose byte spans are sorted, non-overlapping (`e_i.end <= e_{i+1}.start`), aligned to UTF-8 scalar boundaries, and preserve all surrounding CST comments (`//`, `///`, `//!`, `/* ... */`, `#region`).

```axiom
module compiler.refactor.transforms

pub enum RefactorApplicability {
    MachineApplicable,
    HasPlaceholders,
    MaybeIncorrect,
}

pub enum RefactorKind {
    ExtractFunction,
    ExtractVariable,
    InlineVariable,
    PopulateMatchArms,
    OrganizeImports,
    ChangeSignature,
    MoveItem,
    ConvertCapabilityView,
}

pub enum RefactorStatus {
    Ok,
    InvalidSelection,
    PreconditionFailed,
    OwnershipConflict,
    CapabilityConflict,
    ControlFlowConflict,
    NameCollision,
    VerificationFailed,
}
```

---

## 2. `CompilerDB`-Driven Semantic Refactoring Transformations (`compiler/refactor/transforms`)

### `AXS-REF-010` — `extract_function`: Ownership, Capability (`view<T>` / `mut_view<T>`), Effect & Control-Flow Boundary Synthesis (`REQ-TOOL-183`, `REQ-TOOL-186`)

When `extract_function(snapshot, file_id, selection_range, new_fn_name)` is invoked on a contiguous statement or expression selection $R$ inside enclosing function $F$ (`0101 §14`, `tasks/0448 §17`, `tasks/1064 §30`):

1. **Syntactic & control-flow precondition check**:
   - $R$ MUST correspond to a well-formed expression $E$ or a contiguous slice of statements $S_1 \dots S_k$ within a single lexical block of $F$, containing zero `MissingToken` / `IncompleteExpr` error nodes (`AXS-LSP-030`).
   - **Unstructured exit rejection**: If $R$ contains a `break` or `continue` targeting a loop outside $R$, or an early `return` from $F$ mixed with fallthrough live variable definitions (unless $R$ is in tail position or returns a uniform `Result`/`Option` carrier), `extract_function` MUST reject the transformation with `RefactorStatus.ControlFlowConflict`.
   - **Suspension boundary check**: If $R$ contains `.await` (`SPEC-33`) while $F$ is `async fn`, the extracted helper is synthesized as `async fn` and call site as `new_fn(...).await`; if $R$ contains `yield` (`SPEC-62`), extraction across the generator suspension boundary is rejected with `RefactorStatus.ControlFlowConflict`.
2. **Dataflow & ownership/capability capture classification (`REQ-TOOL-183`, `REQ-TOOL-186`)**: For every local binding $v$ (`LocalId`) declared in $F$ outside $R$ and referenced inside $R$, `CompilerDB` queries the ownership and capability dataflow across the entry and exit boundaries of $R$:
   - **Case 1 — Copy-by-value (`ParamMode.ByCopy`)**: If `type_of(v): Copy` and $v$ is only read inside $R$ (not mutated on a path live after $R$), synthesize parameter `v: T` and pass `v` at the call site.
   - **Case 2 — Shared read capability (`ParamMode.ReadView`)**: If `type_of(v): !Copy` (or `v` is already `view<T>`), $v$ is only read inside $R$, and $v$ is **live after $R$** (or cannot be moved), synthesize parameter `v: view<T>` and pass `view(v)` (or `v` if already `view<T>`) at the call site.
   - **Case 3 — Exclusive write capability (`ParamMode.MutView`)**: If $v$ is mutated in place inside $R$ (or passed to a callee requiring `mut_view<T>`) and $v$ is **live after $R$** (or is an incoming `mut_view<T>`), verify that $v$ is declared `let mut` (or `mut_view<T>`) and that no conflicting `view` of $v$ overlaps $R$; synthesize parameter `v: mut_view<T>` and pass `mut_view(v)` (or `v`) at the call site.
   - **Case 4 — Ownership transfer (`ParamMode.ByMove`)**: If `type_of(v): !Copy`, $v$ is consumed by move inside $R$, and $v$ has **zero uses after $R$** in $F$, synthesize owned parameter `v: T` and pass `v` by move at the call site.
   - **Rejection of illegal ownership/capability flow**:
     - If $v$ (`!Copy`) is consumed by move inside $R$ **and** is also used in $F$ after $R$, reject with `RefactorStatus.OwnershipConflict` (`AX_MOVE_USED_AFTER_MOVE`).
     - If $R$ constructs a `view<U>` or `mut_view<U>` rooted in a local variable allocated *inside* $R$ and that view is live after $R$ (escaped in the return value), reject with `RefactorStatus.CapabilityConflict` (`AX_CAP_OUTLIVES_OWNER`).
3. **Return type & error-effect synthesis**:
   - Let $O = \{u_1, \dots, u_m\}$ be the set of bindings declared inside $R$ (or mutated `Copy` locals when not passed by `mut_view`) that are live after $R$:
     - If $R$ is an expression $E$ of type $T_E$, the return type is $T_E$.
     - If $m = 0$, the return type is omitted (`()`).
     - If $m = 1$, the return type is `type_of(u_1)` and the extracted function ends with `return u_1` (and the call site binds `let u_1 = new_fn(...)` or `let mut u_1 = new_fn(...)` if mutated later).
     - If $m > 1$, the return type is the tuple `(T_1, ..., T_m)` and the call site destructures `let (u_1, ..., u_m) = new_fn(...)`.
   - If $R$ contains error propagation `expr?` (`SPEC-03`) with error type $E_{\text{err}}$, the extracted signature carries `-> RetType ! E_err` and the call site emits `new_fn(...)?`.
   - Generic type parameters `[T: Bound]` and `unsafe` / `comptime` modifiers of $F$ actually referenced within $R$ are projected onto `new_fn`.

#### Positive Example — `extract_function` Synthesizing `view<T>`, `mut_view<T>`, and Owned Parameters
```axiom
module app.billing

// Before extracting the loop body inside `process_batch`:
pub fn process_batch(
    header: PacketHeader,
    mut ledger: Ledger,
    audit_log: AuditLog,
) -> usize {
    let prefix = header.prefix()
    // --- selection start ---
    let mut processed: usize = 0
    if prefix.len() > 0 {
        ledger.record_prefix(prefix)
        processed = ledger.entry_count()
    }
    consume_audit(audit_log)
    // --- selection end ---
    return processed + header.version()
}

// After `extract_function` ("apply_batch_step"):
// - `prefix` (`view<u8>` / read-only) -> `prefix: view<u8>`
// - `ledger` (mutated in selection AND live/owned) -> `ledger: mut_view<Ledger>`
// - `audit_log` (`!Copy`, consumed in selection, dead after selection) -> `audit_log: AuditLog` (owned move)
// - `processed` (defined in selection, live after selection) -> returned `usize`
fn apply_batch_step(
    prefix: view<u8>,
    ledger: mut_view<Ledger>,
    audit_log: AuditLog,
) -> usize {
    let mut processed: usize = 0
    if prefix.len() > 0 {
        ledger.record_prefix(prefix)
        processed = ledger.entry_count()
    }
    consume_audit(audit_log)
    return processed
}

pub fn process_batch(
    header: PacketHeader,
    mut ledger: Ledger,
    audit_log: AuditLog,
) -> usize {
    let prefix = header.prefix()
    let processed = apply_batch_step(prefix, mut_view(ledger), audit_log)
    return processed + header.version()
}
```

### `AXS-REF-011` — `extract_variable` (`introduce_variable`) & `inline_variable`: Evaluation Order, Side-Effect, Move & Capability Preservation (`REQ-TOOL-183`, `REQ-TOOL-186`)

1. **`extract_variable(snapshot, file_id, expr_range, var_name)` (`0101 §14`, `tasks/0448 §17`, `tasks/1064 §31`)**:
   - **Preconditions**:
     - `expr_range` resolves to a complete value-producing expression $E$ (`type_of(E) != ()` and `type_of(E) != never`) that is not a bare assignment left-hand place.
     - `var_name` is a valid Axiom identifier not colliding with or shadowing any binding visible at the insertion statement (`AX_NAME_DUPLICATE`).
   - **Single vs multi-occurrence hoisting**:
     - Extracting the single selected occurrence hoists `let <var_name> = <E>` immediately before the innermost enclosing statement $S$ in the same basic block, provided no side-effecting expression or mutable borrow evaluated in $S$ *prior* to $E$ aliases any place read by $E$ (`EffectSummary` check, `SPEC-25`).
     - Replacing multiple syntactically & semantically identical occurrences $E_1, \dots, E_k$ (`k >= 2`) within the same block is permitted **if and only if** `CompilerDB` proves that $E$ is pure (`EffectSummary.is_pure() == true`), `type_of(E): Copy`, and no variable read by $E$ is mutated between $E_1$ and $E_k$. If `type_of(E): !Copy` or $E$ has side effects, multi-occurrence extraction is rejected (`RefactorStatus.OwnershipConflict` / `PreconditionFailed`).
2. **`inline_variable(snapshot, file_id, binding_pos)` (`0101 §14`, `tasks/0448 §17`, `tasks/1064 §31`)**:
   - Resolves `binding_pos` (at declaration `let x = init` or at a reference to local `x`) to its `LocalId`.
   - **Mandatory safety & semantics preconditions**:
     - `x` MUST be an immutable local binding (`let x = init`, not `let mut x`) with a single definite initializer `init`.
     - If `x` is referenced $k = 0$ times: inlining is permitted **only if** `init` is pure and `type_of(x)` has no observable `Drop` side effect; otherwise removing `let x = init` would silently elide side effects or change drop order (`SPEC-12`).
     - If `x` is referenced $k = 1$ time: inlining is permitted if no statement between `let x = init` and the sole use site $u_1$ mutates any place read by `init`, interferes with capabilities held by `init`, or shifts deterministic `Drop` destruction across an observable side effect.
     - If `x` is referenced $k \ge 2$ times: inlining is permitted **if and only if** `init` is pure (`EffectSummary.is_pure() == true`), `type_of(init): Copy`, and no place read by `init` is mutated between the declaration of `x` and its last use $u_k$. Inlining a `!Copy` value or an impure call (`alloc()`, `read_line()`) across $\ge 2$ uses is strictly rejected (`RefactorStatus.OwnershipConflict` / `PreconditionFailed`).
   - **Parenthesization**: When `init` replaces a use site $u_i$, `compiler/refactor/transforms` wraps `init` in parentheses `(...)` if and only if the operator precedence of `init` is lower than (or non-associative with) the enclosing expression context at $u_i$ (`SPEC-02`).

### `AXS-REF-012` — `populate_match_arms` (`add_missing_match_arms`): Exhaustive Pattern Matrix Expansion (`REQ-TOOL-183`)

When `populate_match_arms(snapshot, file_id, match_span)` is invoked on a `match scrutinee { ... }` expression (`0101 §15–§16`, `tasks/0448 §17`):

1. **Compiler pattern-matrix authority (`0101 §16 AIDE-09`)**: The refactoring engine queries `CompilerDB`'s exhaustiveness checker (`compiler/own` / `compiler/types` pattern matrix) for the scrutinee's resolved `TypeId` (`enum`, `bool`, integer range, tuple, or struct). It never scrapes enum declarations by text.
2. **Canonical arm generation**:
   - For an `enum` scrutinee `E`, missing variants are emitted in their exact declaration order in `E`, using canonical dot-qualified variant patterns (`E.Variant` for unit variants, `E.Variant(v0, ...)` or field names `E.Variant { field_a, ... }` for payload variants, or unqualified `Variant` when already imported via `use`).
   - For `bool`, missing arms are emitted in canonical order `true => todo(),` then `false => todo(),`.
   - For open scalar types (`i32`, `u64`, `Slice<T>`, `Str`) where finite constructor enumeration does not close the matrix, a final wildcard arm `_ => todo(),` is appended.
   - Each synthesized arm uses `todo()` as its placeholder body and carries `RefactorApplicability.HasPlaceholders`. If the `match` is already exhaustive (`0` missing patterns), the transformation is not offered.

```axiom
module app.protocol

pub enum FrameState {
    Idle,
    Payload(usize),
    Completed { bytes: u64, ok: bool },
}

// Before `populate_match_arms`:
pub fn describe_state(state: FrameState) -> u64 {
    return match state {
        FrameState.Idle => 0,
    }
}

// After `populate_match_arms`:
pub fn describe_state(state: FrameState) -> u64 {
    return match state {
        FrameState.Idle => 0,
        FrameState.Payload(v0) => todo(),
        FrameState.Completed { bytes, ok } => todo(),
    }
}
```

### `AXS-REF-013` — `organize_imports`: Semantic `use` Resolution, Deduplication, Unused Pruning & Canonical Dot-Path Sorting (`REQ-TOOL-183`)

When `organize_imports(snapshot, file_id)` is invoked (`0101 §14, §17`, `SPEC-101 AXS-FMT-021`):

1. **Unused import removal**: Queries `resolve_module(file_id)` in `CompilerDB` to identify every `use` binding (`SymbolId`) that has zero semantic references in the module (excluding `pub use` re-exports, which form part of the module's public interface, and `use` items gated by inactive `@cfg` predicates, which are preserved intact per `SPEC-88`). Unused private `use` bindings are pruned.
2. **Deduplication & brace-group merging**: Duplicate imports of the same `SymbolId` within an import group are collapsed into a single import. Sibling imports sharing a module prefix (`use std.collections.Vec` and `use std.collections.HashMap`) within the same contiguous import group (not separated by `#region` directives, attached comments, or `@cfg` attributes) are merged into a canonical braced import `use std.collections.{HashMap, Vec}`, while single-item braces `use std.io.{Read}` are unwrapped to `use std.io.Read` (`SPEC-101 AXS-FMT-021`).
3. **Ambiguity preservation (`0101 §17`)**: If two candidate imports in scope would introduce a conflicting binding name (`AX_NAME_DUPLICATE`), `organize_imports` preserves explicit aliasing (`use pkg.mod.Item as ModItem`) and never silently drops or overwrites a colliding import.

### `AXS-REF-014` — `change_signature`, `move_item` & `convert_capability_view` (`REQ-TOOL-183`, `REQ-TOOL-186`)

1. **`change_signature` (`0101 §14`, `tasks/0448 §17`, `tasks/1064 §26`)**:
   - Supports parameter reordering (via permutation map $\pi$), parameter addition (with a typed default expression `default_expr` inserted at existing call sites), parameter removal (permitted only when the parameter has zero uses inside the function body and all call-site arguments for that parameter are pure), parameter rename, and return/capability type updates.
   - Rewrites the target declaration (`FunctionId`), any matching `trait` / `impl` method declarations in the same trait family, and all workspace call sites returned by `CompilerDB.references_of(SymbolId)`.
2. **`move_item` (`0101 §14`, `tasks/0448 §17`, `tasks/1064 §25, §32`)**:
   - Moves a top-level item (`fn`, `struct`, `enum`, `trait`, `const`, `type`) from source module $M_{\text{src}}$ to target module $M_{\text{dst}}$.
   - Verifies that moving the item does not violate trait orphan coherence rules or private-field visibility boundaries; updates or inserts `use` declarations in $M_{\text{src}}$, $M_{\text{dst}}$, and all referencing modules in the workspace while preserving the item's logical lineage for `AXHISTORY`.
3. **`convert_capability_view` (capability qualification & upgrade, `0101 §15`, `tasks/0448 §13, §17`)**:
   - When a function parameter or local binding `x: T` (`!Copy`) is only read within its scope, offers a semantics-preserving conversion to `x: view<T>` and rewrites call sites `f(buf)` $\rightarrow$ `f(view(buf))`.
   - When a diagnostic `AX_CAP_MUT_REQUIRED` / `AX_TYPE_MISMATCH` occurs because a `view<T>` parameter or `let` binding is mutated, offers a targeted capability upgrade (`view<T>` $\rightarrow$ `mut_view<T>` or `let x` $\rightarrow$ `let mut x`) **if and only if** `CompilerDB` verifies that all callers can legally provide an exclusive `mut_view<T>` without violating `AX_CAP_CONFLICT_MUT`.

---

## 3. LSP `textDocument/codeAction` & `codeAction/resolve` Integration (`compiler/refactor/code_actions`, `compiler/lsp/handlers/mod.ax`)

### `AXS-REF-020` — `textDocument/codeAction` Request Handling, `CodeActionKind` Taxonomy & Diagnostic Quick-Fixes (`REQ-TOOL-183`, `REQ-TOOL-186`)

1. **Supported `CodeActionKind` hierarchy (`0101 §2, §15`, `SPEC-100 AXS-LSP-010`)**: `axiomc lsp` advertises `codeActionProvider = { codeActionKinds: ["quickfix", "refactor", "refactor.extract", "refactor.inline", "refactor.rewrite", "source.organizeImports"], resolveProvider: true }`:

| `CodeActionKind` | Action ID | Trigger Condition | Applicability |
|---|---|---|---|
| `"quickfix"` | `quickfix.populate_match_arms` | Cursor overlaps non-exhaustive `match` (`AX_PAT_NON_EXHAUSTIVE`) | `HasPlaceholders` |
| `"quickfix"` | `quickfix.qualify_ambiguous_method` | Call site triggers `AX_TRAIT_AMBIGUOUS_METHOD` (`0101 §8, §15`) | `MachineApplicable` (one action per candidate `Trait.method`) |
| `"quickfix"` | `quickfix.import_unresolved_symbol` | Unresolved identifier (`AX_NAME_UNRESOLVED`) matches accessible workspace/std `pub` item (`0101 §15, §17`) | `MachineApplicable` |
| `"quickfix"` | `quickfix.remove_unused_import` | Unused `use` item warning | `MachineApplicable` |
| `"quickfix"` | `quickfix.upgrade_to_mut_binding` | Mutating immutable local `let x` (`AX_MOVE_ASSIGN_IMMUTABLE` / `AX_CAP_*`) where `let mut x` is verified legal | `MachineApplicable` |
| `"quickfix"` | `quickfix.pass_view_instead_of_move` | Use-after-move (`AX_MOVE_USED_AFTER_MOVE`) where callee accepts `view<T>` or `.clone()` is available (`tasks/0448 §13`) | `MachineApplicable` |
| `"refactor.extract"` | `refactor.extract_function` | Non-empty statement/expression selection $R$ passing `AXS-REF-010` preconditions | `MachineApplicable` |
| `"refactor.extract"` | `refactor.extract_variable` | Non-empty expression selection $E$ passing `AXS-REF-011` preconditions | `MachineApplicable` |
| `"refactor.inline"` | `refactor.inline_variable` | Cursor on local binding or reference passing `AXS-REF-011` preconditions | `MachineApplicable` |
| `"refactor.rewrite"` | `refactor.populate_match_arms` | Cursor on any non-exhaustive `match` header/body | `HasPlaceholders` |
| `"refactor.rewrite"` | `refactor.convert_capability_view` | Parameter/binding eligible for `T -> view<T>` or `view<T> -> mut_view<T>` (`AXS-REF-014`) | `MachineApplicable` |
| `"refactor.rewrite"` | `refactor.change_signature` / `move_item` | Cursor on function/item declaration passing `AXS-REF-014` preconditions | `MachineApplicable` |
| `"source.organizeImports"` | `source.organize_imports` | Any module containing `use` items (`AXS-REF-013`) | `MachineApplicable` |

2. **Deterministic action ordering**: Returned `CodeAction` items are sorted deterministically by: (1) `isPreferred: true` (`MachineApplicable` diagnostic quick-fixes matching the primary cursor span first), (2) `CodeActionKind` tier (`quickfix` < `refactor.extract` < `refactor.inline` < `refactor.rewrite` < `source.organizeImports`), and (3) lexicographical `action_id` and target `SemanticKey`.

### `AXS-REF-021` — Lazy `codeAction/resolve`, Precondition Filtering & Zero-Codegen Firewall (`REQ-TOOL-183`, `REQ-TOOL-185`, `REQ-TOOL-186`)

1. **Precondition-gated action surfacing**: `textDocument/codeAction` MUST evaluate lightweight semantic preconditions on the pinned `DatabaseSnapshot(RevisionId)` before listing an action. An illegal refactoring (such as `inline_variable` on a `let mut` variable or `extract_function` on a selection with an escaping local view) SHALL NOT be offered as a valid action.
2. **Snapshot-pinned `codeAction/resolve`**:
   - Each unresolved `CodeAction` carries a structured `data` token `{ schema_version: 1, revision: RevisionId, doc_id: u32, range: LspRange, action_id: Str, target_symbol: SymbolId }`.
   - When `codeAction/resolve` is invoked, `compiler/refactor/code_actions` verifies that `data.revision == workspace.current_revision()` (or re-validates preconditions against the current snapshot), computes the full `WorkspaceEdit`, runs the mandatory post-transformation `CompilerDB` verification gate (`AXS-REF-002`), and returns the populated `edit` field. If the document changed incompatibility since `textDocument/codeAction`, `codeAction/resolve` returns a structured stale-revision error without mutating any buffer.
3. **Zero-codegen firewall (`SPEC-100 AXS-LSP-004`, `REQ-TOOL-185`)**: Neither `textDocument/codeAction` nor `codeAction/resolve` may invoke `OptIR`, `LIR`, register allocation, object emission, or linking.

---

## 4. `AXDIFF` — Structural CST/AST & Semantic Symbol Difference Engine (`compiler/refactor/vcs/diff.ax`; `REQ-TOOL-301`)

### `AXS-REF-030` — `AXDIFF` Architecture, Comparison Layers & Nine-State Change Status (`REQ-TOOL-301`)

1. **Multi-layer difference separation (`0101 §45–§47`, `tasks/1059 §1–§5, §10–§13, §241 DIFF-INV-01..08`)**: `AXDIFF` (`AXDIFF_ABI_1 = 1`, `AXDIFF_SCHEMA_1 = 1`, artifact `.axdiff`) enforces the fundamental invariant that **byte difference $\ne$ CST trivia/formatting difference $\ne$ AST structural difference $\ne$ semantic difference $\ne$ ABI difference**. `AXDIFF` operates across four explicit source/compiler comparison tiers:
   - `DiffMode.Byte`: Raw byte-slice and BLAKE3 `content_hash` comparison (`tasks/1059 §10`).
   - `DiffMode.Trivia` (`CST`): Compares lossless CST token and comment streams (`SPEC-101 AXS-FMT-001..004`), isolating whitespace/formatting-only edits and comment-only edits from syntax tree changes.
   - `DiffMode.Ast`: Structural comparison of parsed `AstModule` / `AstItem` / `AstStmt` / `AstExpr` trees (`tasks/1059 §23–§26`).
   - `DiffMode.Semantic` (default for `axiomc diff`): Compares `CompilerDB` declaration tables, `SymbolId` / `SemanticKey` identities, function signatures, type definitions, `view`/`mut_view` receiver/parameter capabilities, declared effects, trait implementations, `unsafe` surface, and `@repr` / `layout_of` ABI contracts (`0101 §45–§47`, `tasks/1059 §27–§59`).
2. **Nine-state status & evidence lattice (`tasks/1059 §3, §17–§18, §30–§31, DIFF-INV-06..10`)**:
   - Every compared entity is assigned an explicit `DiffStatus`: `Identical`, `Changed`, `Added`, `Removed`, `Moved`, `Renamed`, `Unknown`, `Unavailable`, or `Incomparable`. `AXDIFF` MUST NEVER silently collapse `Unknown` or `Incomparable` into `Identical` (`DIFF-INV-06..07`).
   - Every non-trivial match carries an explicit `DiffEvidenceLevel`: `Exact` (proven by identical `SymbolId` / `SemanticKey` or identical canonical AST hash), `Strong` (identical qualified path + signature or identical body AST under rename), `Inferred` (structural subtree similarity across both rename and body edit), `Heuristic`, or `Unknown`. A heuristic or inferred match is NEVER reported as `Exact` (`DIFF-INV-10`).

```axiom
module compiler.refactor.vcs.diff

pub const AXDIFF_ABI_1: u32 = 1
pub const AXDIFF_SCHEMA_1: u32 = 1

pub enum DiffMode {
    Byte,
    Trivia,
    Ast,
    Semantic,
    Api,
    Abi,
}

pub enum DiffStatus {
    Identical,
    Changed,
    Added,
    Removed,
    Moved,
    Renamed,
    Unknown,
    Unavailable,
    Incomparable,
}

pub enum DiffChangeKind {
    TriviaOnly,
    FormattingOnly,
    Added,
    Removed,
    Modified,
    Moved,
    Renamed,
    RenamedAndModified,
    MovedAndModified,
    TypeChanged,
    SignatureChanged,
    CapabilityChanged,
    EffectChanged,
    VisibilityChanged,
    LayoutChanged,
    TraitImplChanged,
    UnsafeSurfaceChanged,
}

pub enum DiffSeverity {
    Info,
    Notice,
    Compatible,
    Breaking,
    SecurityRelevant,
    Unknown,
}

pub enum DiffEvidenceLevel {
    Exact,
    Strong,
    Inferred,
    Heuristic,
    Unknown,
}
```

### `AXS-REF-031` — CST/AST Structural Matching, `SymbolId` Continuity & Rename/Move Classification (`REQ-TOOL-301`)

Given left source snapshot $A$ and right source snapshot $B$, `AXDIFF` computes a deterministic matching $M \subseteq \text{Nodes}(A) \times \text{Nodes}(B)$ in four ordered passes (`tasks/1059 §10–§12, §23–§29, DIFF-INV-05, 08..12`):

1. **Pass 1 — Fast exact & formatting-equivalence check (`DIFF-INV-05`)**:
   - If `content_hash(A) == content_hash(B)`, return `DiffStatus.Identical` immediately ($O(1)$).
   - If `content_hash(A) != content_hash(B)` but the canonical AST structural hashes of $A$ and $B$ are equal (`ast_hash(A) == ast_hash(B)` per `SPEC-101 AXS-FMT-031`), classify the file change as `DiffChangeKind.FormattingOnly` (when comments are identical) or `DiffChangeKind.TriviaOnly` (when only comments changed) with `DiffSeverity.Info` and `0` semantic changes.
2. **Pass 2 — Exact `SymbolId` / `SemanticKey` anchoring (`DIFF-INV-09`)**:
   - Top-level and member declarations in $A$ and $B$ with identical `(ModulePath, ItemNamespace, ItemKind, CanonicalName, Disambiguator)` (`SemanticKey`) are paired with `DiffEvidenceLevel.Exact`.
   - If a paired item's declaration order within the file changed while its `SemanticKey` and normalized AST body hash are unchanged, it is classified as an intra-module `Moved` (reordered) item rather than `Removed` + `Added` (`DIFF-INV-12`).
3. **Pass 3 — Cross-name (`RENAMED`) and cross-module (`MOVED`) structural matching (`tasks/1059 §25–§26, DIFF-INV-11..12`)**:
   - Unpaired removed items $a \in U_A$ and unpaired added items $b \in U_B$ of the same `ItemKind` are compared by their canonical normalized signature and body AST digest (`body_ast_hash`, alpha-normalized over local variable slots):
     - **Same module, different name, identical normalized body or identical parameter/field layout**: paired as `DiffChangeKind.Renamed` (`DiffEvidenceLevel.Strong` when body hashes match exactly; `Inferred` when AST Dice similarity $\ge 0.75$ and signature matches), recording `RenamedAndModified` if the body or signature also changed.
     - **Different module, same name (or proven rename), identical signature + normalized body**: paired as `DiffChangeKind.Moved` (or `MovedAndModified` if the body also changed).
4. **Pass 4 — Top-down / bottom-up statement & expression AST tree diff (`tasks/1059 §23–§24`)**:
   - Within each paired function or initializer body $(f_A, f_B)$, `AXDIFF` matches child statements and expressions by `(AstNodeKind, LocalId / SymbolId reference, SubtreeHash)` to emit minimal structural edit scripts (`InsertNode`, `DeleteNode`, `ReplaceNode`, `MoveNode`) tied to exact `Span` and `NodeId` anchors rather than raw line numbers.

### `AXS-REF-032` — Semantic Declaration, Signature, Capability, Effect & API/ABI Compatibility Diff (`REQ-TOOL-301`)

For every paired declaration $(d_A, d_B)$, `AXDIFF` queries `CompilerDB` to classify semantic, API, and ABI impact (`0101 §45–§47 AIDE-24`, `tasks/1059 §32–§59, §162, DIFF-INV-13..18, 34..35`):

1. **Function & method diff (`tasks/1059 §32, §39–§41`)**:
   - Detects changes to visibility (`pub` $\rightarrow$ private = `Breaking`; private $\rightarrow$ `pub` = `Compatible`), generic type parameters and trait bounds (`T: Clone`), parameter count/types, receiver capability (`view<Self>` $\leftrightarrow$ `mut_view<Self>` $\leftrightarrow$ owned `Self`, classified as `CapabilityChanged`), return type, error effect (`! ErrorType`, `EffectChanged`), `async`/`comptime`/`unsafe` modifiers (`UnsafeSurfaceChanged`), and calling convention (`extern "C"`).
2. **Nominal type & layout diff (`tasks/1059 §33–§36, DIFF-INV-13..15`)**:
   - For `struct`, `enum`, and `union` items, compares field names, field types, field visibility, enum variants and explicit discriminants, `@repr(Axiom | C | packed | transparent)` attributes, and `CompilerDB.layout_of(TypeId)` (`size`, `align`, field byte offsets).
   - Any change to `size`, `align`, field offset, discriminant value, or `@repr(C)` layout on an exported or FFI-visible type is flagged with `DiffChangeKind.LayoutChanged` and `AbiImpact.Breaking` (`0101 §46–§47`, `DIFF-INV-13..18`).
3. **Deterministic ordering & `.axdiff` serialization (`tasks/1059 §122–§125, §162, DIFF-INV-34..35`)**:
   - All `DiffChange` records are sorted deterministically by `(module_path, ChangeKind ordinal, left_semantic_key, right_semantic_key, left_span.lo, right_span.lo)`.
   - `diff_hash` is the 256-bit BLAKE3 digest of the canonical `.axdiff` payload (`AXDIFF_SCHEMA_1`), independent of thread scheduling, filesystem timestamps, or memory addresses.

---

## 5. `AXMERGE` — AST-Aware Three-Way Semantic Merge & Conflict Engine (`compiler/refactor/vcs/merge.ax`; `REQ-TOOL-302`)

### `AXS-REF-040` — `AXMERGE` Three-Way (`BASE`, `LEFT`, `RIGHT`) Semantic Merge Model & Identity Hierarchy (`REQ-TOOL-302`)

1. **Normative three-way model (`tasks/1060 §1–§7, MERGE-PRINCIPLE-01..07, §120 MERGE-INV-01..09`)**: `AXMERGE` (`AXMERGE_ABI_1 = 1`, `AXMERGE_SCHEMA_1 = 1`, artifact `.axmerge`) combines two divergent states `LEFT` ($L$) and `RIGHT` ($R$) relative to their common ancestor `BASE` ($B$) by computing structural/semantic deltas $\Delta_L = \text{AXDIFF}(B, L)$ and $\Delta_R = \text{AXDIFF}(B, R)$:
   - **Idempotent convergence (`MERGE-PRINCIPLE-05`, `MERGE-INV-02`)**: If $\Delta_L(e)$ and $\Delta_R(e)$ perform the **exact same semantic change** on entity $e$ (e.g. both sides add `use std.io.Read`, both sides change `const MAX: usize = 64` to `const MAX: usize = 128`, or both sides apply the same formatting change), `AXMERGE` applies the change **once** with zero conflict.
   - **Disjoint preservation (`MERGE-PRINCIPLE-06`, `MERGE-INV-03`)**: If $\Delta_L(e_1)$ modifies entity $e_1$ while $e_1$ is unchanged in $\Delta_R$, and $\Delta_R(e_2)$ modifies a distinct entity $e_2$ ($e_1 \ne e_2$) while $e_2$ is unchanged in $\Delta_L$, both changes are preserved automatically.
   - **Zero silent guessing (`MERGE-PRINCIPLE-02, 07`, `MERGE-INV-04..05, 40`)**: Whenever $\Delta_L$ and $\Delta_R$ make incompatible changes to the same semantic target or introduce a cross-declaration semantic conflict, `AXMERGE` MUST emit an explicit `MergeConflict` record and SHALL NEVER silently pick `LEFT` or `RIGHT` unless an explicit caller-supplied `MergeResolutionPolicy` authorizes it.
2. **Six-level identity matching priority (`tasks/1060 §2 MERGE-PRINCIPLE-03..04, §9, MERGE-INV-06..07`)**: `AXMERGE` aligns declarations, members, and statements across $B$, $L$, and $R$ strictly from strongest to weakest identity:
   1. **Level 0 — `SymbolId` / `SemanticKey`** (`CompilerDB` canonical identity);
   2. **Level 1 — `DeclarationId` / `MemberId`** (field, variant, or trait item identity within matched parent);
   3. **Level 2 — Structural & signature fingerprint** (proven `RENAMED` or `MOVED` symbol continuity from `AXDIFF`);
   4. **Level 3 — AST node kind & parent-child structural path** (`AstStmt` / `AstExpr` tree alignment);
   5. **Level 4 — Lexical token stream**;
   6. **Level 5 — UTF-8 line/text fallback** (used only for non-Axiom plain-text files or unparseable syntax regions, and explicitly tagged `MergeFallback.Text`).

### `AXS-REF-041` — Structural & Declaration-Level Auto-Merge Rules (`REQ-TOOL-302`)

When merging valid Axiom modules $(B, L, R)$, `AXMERGE` resolves the following structural combinations without false line-based conflicts (`tasks/1060 §10–§29, §102–§104, MERGE-INV-02..03, 08..09, 32..33`):

1. **Formatting & trivia immunity (`tasks/1060 §59, §102–§104, MERGE-INV-32..33`)**:
   - If `LEFT` reformats a file or declaration (changing line breaks/indentation) while `RIGHT` modifies an expression or statement inside that declaration, `AXMERGE` merges at the AST level and formats the merged output through `SPEC-101` (`compiler/fmt/printer`), eliminating false whitespace conflicts.
   - Doc-comment (`///`) modified on one side while the item's body is modified on the other side merges cleanly into the combined item.
2. **`use` import set union & canonical sorting (`tasks/1060 §29`)**:
   - Independent `use` additions and removals in `LEFT` and `RIGHT` are merged by set algebra:
     $$\text{Imports}_{\text{merged}} = (\text{Imports}_B \setminus (\text{Removed}_L \cup \text{Removed}_R)) \cup \text{Added}_L \cup \text{Added}_R$$
     and formatted in canonical dot-sorted order (`SPEC-101 AXS-FMT-021`), unless `LEFT` and `RIGHT` bind the same imported local alias to two different target `SymbolId`s (which raises `MergeConflictKind.ImportAliasCollision`).
3. **Independent top-level declaration additions, reorderings, renames & moves (`tasks/1060 §10–§14, MERGE-INV-08..09`)**:
   - Adding `fn alpha()` in `LEFT` and `fn beta()` in `RIGHT` at the same file offset merges both declarations cleanly in deterministic order (`LEFT` additions in source order followed by `RIGHT` additions, unless sorted by policy) as long as their `SemanticKey`s are distinct.
   - **Rename + body modification (`tasks/1060 §10, §86`)**: If `LEFT` renames `fn calc_total` $\rightarrow$ `fn compute_total` (preserving `SymbolId` continuity) while `RIGHT` modifies the body of `fn calc_total` (and/or adds new call sites to `calc_total`), `AXMERGE` produces `fn compute_total` with `RIGHT`'s updated body and rewrites `RIGHT`'s new call sites to `compute_total`!
   - **Move + body modification (`tasks/1060 §11, §87`)**: If `LEFT` moves `fn helper` from `module a` to `module b` while `RIGHT` modifies the body of `fn helper` in `module a`, `AXMERGE` places the modified `fn helper` in `module b` and preserves the cross-module `use` import in `module a`.
4. **Composite item member merges (`struct`, `enum`, `union`, `trait`, `impl`; `tasks/1060 §16–§24, §88–§90`)**:
   - `struct` / `union`: Independent field additions on `LEFT` (`name: String`) and `RIGHT` (`age: u32`) merge into a single struct containing both fields (with `AbiImpact.LayoutChanged` recorded in the merge summary per `tasks/1060 §18`).
   - `enum`: Independent variant additions (`Green` on `LEFT`, `Blue` on `RIGHT`) merge cleanly provided their names and explicit discriminants do not collide (`tasks/1060 §19–§20`).
   - `trait` / `impl`: Independent method or associated-type additions in the same `trait` or `impl` block merge cleanly when method names do not collide.
5. **Function body statement blocks (`tasks/1060 §14`)**:
   - Inside a matched function body, non-overlapping statement insertions, deletions, or modifications in distinct sub-blocks or non-interfering statement spans merge structurally, subject to the mandatory post-merge `CompilerDB` verification gate (`AXS-REF-042`).

### `AXS-REF-042` — Explicit Semantic Conflict Taxonomy, Deterministic `ConflictId` & Post-Merge Verification (`REQ-TOOL-186`, `REQ-TOOL-302`)

1. **Mandatory conflict taxonomy (`tasks/1060 §15, §17, §20, §23, §25, §40–§41, MERGE-INV-04..05, 10..15`)**: `AXMERGE` MUST report an explicit `MergeConflict` (and refuse to mark the merge `Clean`) whenever any of the following occurs:

| `MergeConflictKind` | Trigger Condition (`tasks/1060`) |
|---|---|
| `DuplicateSymbolAdd` | Both `LEFT` and `RIGHT` independently add a declaration with the same `SemanticKey` (`fn foo`, `struct Item`) but non-identical AST/type definitions. |
| `ModifyDeleteConflict` | One side modifies a declaration, field, variant, or statement while the other side deletes it. |
| `RenameIdentityConflict` | `LEFT` renames symbol $S \rightarrow S_L$ while `RIGHT` renames $S \rightarrow S_R$ ($S_L \ne S_R$), or rename provenance is ambiguous (`CONFLICT_RENAME_IDENTITY`, `tasks/1060 §10`). |
| `MoveDestinationConflict` | `LEFT` moves symbol $S$ to module $M_L$ while `RIGHT` moves $S$ to module $M_R$ ($M_L \ne M_R$). |
| `SignatureConflict` | Both `LEFT` and `RIGHT` modify the signature of the same function (`CONFLICT_SIGNATURE`, `tasks/1060 §15`, e.g. `LEFT` changes parameter type `i32 -> i64` while `RIGHT` changes return type `i32 -> f32` or capability `view<T> -> mut_view<T>`). `AXMERGE` never synthesizes an unverified hybrid signature automatically. |
| `StructFieldConflict` | Both sides modify the same `struct` or `union` field to different types/visibilities/attributes (`STRUCT_FIELD_TYPE_CONFLICT`, `tasks/1060 §17`), or add fields with the same name and different types. |
| `EnumDiscriminantConflict` | Both sides add `enum` variants assigned the same explicit discriminant value (`C = 3` vs `D = 3`) or assign different discriminants to the same variant (`C = 3` vs `C = 4`, `tasks/1060 §20`). |
| `TraitImplCoherenceConflict` | `LEFT` and `RIGHT` introduce overlapping or conflicting `impl Trait for Type` blocks (`tasks/1060 §23`). |
| `StatementBodyConflict` | Overlapping or order-conflicting edits to the same statement or expression node inside a function body (`FUNCTION_BODY_CONFLICT`, `tasks/1060 §14`). |
| `ImportAliasCollision` | `LEFT` and `RIGHT` import different symbols under the same local identifier. |
| `SemanticVerificationConflict` | Syntactically disjoint edits in `LEFT` and `RIGHT` (e.g. `LEFT` changes a callee signature or moves a local variable `buf`, while `RIGHT` adds a new call site or reads `buf` on a subsequent line) fail `CompilerDB` type, ownership (`AX_MOVE_*`), or capability (`AX_CAP_*`) verification when combined (`MERGE-INV-38`). |

2. **Deterministic `ConflictId` & conflict rendering (`tasks/1060 §42, §60, MERGE-INV-25`)**:
   - Every conflict receives a deterministic `ConflictId = BLAKE3("axiom-merge-conflict-v1" || target_semantic_key || conflict_kind || base_hash || left_hash || right_hash)`.
   - In structured mode (`--json` or `.axmerge`), conflicts are emitted as typed `MergeConflict` records with `base_span`, `left_span`, `right_span`, `symbol_id`, and `explanation`.
   - When materializing a partially merged source file with unresolved conflicts (`MergeStatus.Conflicted`), `AXMERGE` emits canonical 3-way conflict blocks showing `<<<<<<< LEFT`, `||||||| BASE`, `=======`, and `>>>>>>> RIGHT` around the minimal conflicting AST declaration or statement node (`tasks/1060 §60`).
3. **Post-merge `CompilerDB` verification gate (`tasks/1060 §7 step 11, §106, MERGE-INV-31, 38`, `REQ-TOOL-186`)**:
   - A merge with zero structural conflicts is loaded into `CompilerDB` and checked through `typeck_body` and `ownership_check`.
   - If combining `LEFT` and `RIGHT` introduces a type mismatch, unresolved symbol, ownership use-after-move (`AX_MOVE_USED_AFTER_MOVE`), or capability overlap (`AX_CAP_CONFLICT_MUT`), `AXMERGE` converts the compiler diagnostic into a `SemanticVerificationConflict` with provenance pointing to the interacting `LEFT` and `RIGHT` changes, and downgrades the merge status from `Clean` to `SemanticConflict`.

---

## 6. `AXPATCH` — Symbol-Centric Semantic & Text Patch Engine (`compiler/refactor/vcs/patch.ax`; `REQ-TOOL-303`)

### `AXS-REF-050` — `AXPATCH` Typed Patch IR, Content-Addressed `PatchId` & Target Resolution Priority (`REQ-TOOL-303`)

1. **Dual AST/semantic & text patch representation (`tasks/1061 §1–§6, PATCH-INV-01..03`, `tasks/1064 §1–§7, §41–§45, PATCH-INV-01..03, 08..12`, `REQ-TOOL-303`)**: `AXPATCH` (`AXPATCH_ABI_1 = 1`, `AXPATCH_SCHEMA_1 = 1`, artifact `.axpatch`) represents changes as a typed sequence of `PatchOperation` records supporting both semantic/AST-targeted mutations (`PatchKind.Semantic`, `PatchKind.Ast`) and range/context-anchored text mutations (`PatchKind.Text`).
2. **Deterministic content-addressed `PatchId` (`tasks/1061 §6, PATCH-INV-01`, `tasks/1064 §5, PATCH-INV-01..02`)**:
   - `PatchId = BLAKE3("axiom-patch-v1" || AXPATCH_SCHEMA_1 || canonical_serialized_patch)`.
   - `PatchId` is independent of wall-clock timestamps, local file paths, or host OS environment.
3. **Six-level target relocation priority (`tasks/1061 PATCH-PRINCIPLE-01..02`, `tasks/1064 §41–§45, PATCH-INV-08..12`)**: When applying a semantic or AST patch to a workspace snapshot where lines or comments have shifted above the target, `AXPATCH` resolves each operation's target strictly in the following order:
   1. `SymbolId` / `SemanticKey` in `CompilerDB` (`Exact` match);
   2. Qualified semantic path `(ModulePath, ItemKind, Name)` + structural signature digest (`High` confidence);
   3. Normalized AST subtree hash within the enclosing declaration (`High` confidence);
   4. Source `ContextAnchor { before_lines, target_span, after_lines }` (`Medium` confidence, `fallback = Text`);
   5. Exact byte span `TextRange` when file `content_hash` matches `base_content_hash` (`Exact` match).
   - If target resolution yields zero matches (`PATCH_TARGET_NOT_FOUND`) or multiple ambiguous matches (`PATCH_TARGET_AMBIGUOUS`), `AXPATCH` aborts without applying the patch (`PATCH-INV-11`).

```axiom
module compiler.refactor.vcs.patch

pub const AXPATCH_ABI_1: u32 = 1
pub const AXPATCH_SCHEMA_1: u32 = 1

pub enum PatchKind {
    Text,
    Ast,
    Semantic,
    Combined,
}

pub enum PatchOpKind {
    TextReplace,
    InsertItem,
    DeleteItem,
    ModifyItemBody,
    RenameSymbol,
    MoveSymbol,
    ExtractFunctionOp,
    InlineBindingOp,
    ChangeSignatureOp,
    UpdateImportsOp,
}

pub enum PreconditionKind {
    FileContentHashIs,
    SymbolExists,
    SymbolAbsent,
    SymbolSignatureHashIs,
    SymbolBodyAstHashIs,
    RangeTextHashIs,
}

pub enum PatchApplyStatus {
    AppliedClean,
    AppliedRelocated,
    PreconditionFailed,
    TargetNotFound,
    TargetAmbiguous,
    DependencyCycle,
    PostconditionFailed,
    SemanticVerificationFailed,
}
```

### `AXS-REF-051` — Mandatory Preconditions, Postconditions & Atomic Transactional Application (`REQ-TOOL-186`, `REQ-TOOL-303`)

1. **Mandatory precondition verification (`tasks/1061 §2 PATCH-PRINCIPLE-03, PATCH-INV-04..05, 11..13`, `tasks/1064 §35–§39, PATCH-INV-04..05`)**:
   - Every mutating `PatchOperation` MUST carry explicit `Precondition` guards verifying the expected state of its target before mutation:
     - `ModifyItemBody` / `ChangeSignatureOp` / `DeleteItem`: verifies `SymbolExists(target_key)` and `SymbolBodyAstHashIs(expected_ast_hash)` (or `SymbolSignatureHashIs(expected_sig_hash)`).
     - `InsertItem` / `RenameSymbol` / `MoveSymbol`: verifies `SymbolAbsent(new_target_key)` so an `Add` or `Rename` never silently overwrites an existing declaration (`PATCH-INV-11`).
     - `TextReplace`: verifies `RangeTextHashIs(range, expected_slice_hash)` (or `ContextAnchor` match in `PATCH_ADAPTIVE` mode).
   - If any precondition fails, `AXPATCH` returns `PatchApplyStatus.PreconditionFailed` immediately with zero state mutation.
2. **Dependency DAG ordering & atomic copy-on-write transaction (`tasks/1061 PATCH-INV-06`, `tasks/1064 §46–§54, §145–§149, PATCH-INV-06..07, 13..19`)**:
   - Composite patches (e.g. `ExtractFunctionOp` or cross-module `MoveSymbol` + `UpdateImportsOp`) topologically sort operations by their semantic dependency edges (rejecting unsupported cycles with `PatchApplyStatus.DependencyCycle`, `PATCH-INV-14`).
   - All operations execute inside an atomic `PatchTransaction` over copy-on-write `AXEDITOR` / `CompilerDB` buffers (`PATCH-INV-06..07`).
   - Before committing, `AXPATCH` checks all declared `Postcondition` predicates **and** runs the `CompilerDB` semantic verification gate (`AXS-REF-002`, `PATCH-INV-17, 19`, `REQ-TOOL-186`). If operation $k$ of $N$ fails or post-patch `CompilerDB` verification fails, the entire transaction rolls back so the workspace remains byte-for-byte identical to its pre-patch state.
   - Preview / `--dry-run` mode executes the full precondition, relocation, and `CompilerDB` verification pipeline and reports the resulting diff without writing to disk (`PATCH-INV-37`).

### `AXS-REF-052` — Patch Inversion (`reverse`), Composition (`compose`) & Three-Way Rebasing (`rebase`) (`REQ-TOOL-303`)

1. **Exact patch inversion (`tasks/1061 PATCH-INV-18..19`, `tasks/1064 §61–§63, PATCH-INV-27`)**:
   - Every reversible `Patch` $P$ stores both the `before` state snapshot/digest and `after` state payload of each operation so `reverse(P)` constructs the inverse patch $P^{-1}$ swapping preconditions and postconditions (`InsertItem` $\leftrightarrow$ `DeleteItem`, `RenameSymbol(A -> B)` $\leftrightarrow$ `RenameSymbol(B -> A)`, `TextReplace(old -> new)` $\leftrightarrow$ `TextReplace(new -> old)`).
   - Applying $P$ then $P^{-1}$ satisfies `ast_hash(apply(P^{-1}, apply(P, S))) == ast_hash(S)` (and exact byte identity for `PatchKind.Text`).
2. **Sequential composition (`tasks/1061 PATCH-INV-20`, `tasks/1064 §64–§69`)**:
   - `compose(P_1, P_2)` verifies that the postconditions of $P_1$ satisfy the preconditions of $P_2$, normalizes chained renames/edits (`Rename(A -> B)` followed by `Rename(B -> C)` $\rightarrow$ `Rename(A -> C)` when $B$ has no intermediate external anchor), and preserves combined provenance. Conflicting writes between $P_1$ and $P_2$ report an explicit composition conflict (`PATCH-INV-20`).
3. **Three-way semantic patch rebasing (`tasks/1061 PATCH-INV-21..22`, `tasks/1064 §70–§74, PATCH-INV-28`)**:
   - `rebase_patch(patch, old_base, new_base)` computes $\Delta_{\text{upstream}} = \text{AXDIFF}(\text{old\_base}, \text{new\_base})$ and adapts `patch` across upstream formatting edits, item relocations (`Moved`), and symbol renames (`Renamed`). If upstream deleted or incompatibly modified a target of `patch`, `rebase_patch` returns an explicit `PatchConflict` rather than guessing (`PATCH-INV-28`).

---

## 7. `AXHISTORY` & `AXVCS` — Semantic Revision Lineage, Deterministic Repository Model & CLI Entrypoints (`std/vcs`, `compiler/driver/refactor_cmd`; `REQ-TOOL-304`, `REQ-TOOL-305`)

### `AXS-REF-060` — `AXHISTORY` Content-Addressed `RevisionId`, Revision DAG & Timestamp Independence (`REQ-TOOL-304`)

1. **Deterministic semantic `RevisionId` (`tasks/1062 §1–§8, §130 HISTORY-INV-01..06, §132`, `REQ-TOOL-304`)**: `AXHISTORY` (`AXHISTORY_ABI_1 = 1`, `AXHISTORY_SCHEMA_1 = 1`, artifact `.axhistory`) models project history as a directed acyclic graph (DAG) of immutable `VcsRevision` nodes whose identity is defined strictly by canonical content and ancestry:
   $$\text{RevisionId} = \text{BLAKE3}(\text{"axiom-revision-v1"} \parallel \text{AXHISTORY\_SCHEMA\_1} \parallel \text{parent\_ids} \parallel \text{root\_tree\_hash} \parallel \text{semantic\_root\_hash} \parallel \text{patch\_set\_id})$$
   - **Timestamp and host independence (`HISTORY-INV-02`, `tasks/1062 §6, §132`)**: Wall-clock commit timestamps, local filesystem paths, hostname, and branch names are non-semantic administrative metadata and SHALL NEVER alter `RevisionId`.
   - **Parent sensitivity & cycle rejection (`HISTORY-INV-03, 38`, `tasks/1062 §8, §132`)**: An initial root revision has `parents = []`; a linear revision has `parents = [P_0]`; a merge revision has `parents = [P_left, P_right, ...]` preserving the ordered lineage of all merged branches (`HISTORY-INV-05`). Any cycle in the parent graph is rejected as a corrupt history DAG (`HISTORY-INV-38`).

### `AXS-REF-061` — Symbol-Centric Lineage Graph & Refactoring Provenance Across Revisions (`REQ-TOOL-304`)

1. **First-class symbol lineage (`tasks/1062 §16–§45, §130 HISTORY-INV-07..22, 33..40`, `REQ-TOOL-304`)**: Unlike line-based `git log`, `AXHISTORY` maintains a symbol-centric lineage graph tracking each declaration (`SymbolId` / `SemanticKey`) across revisions via typed `LineageEdge` transitions:
   - `LineageKind.Created`: Symbol introduced in revision $R$.
   - `LineageKind.Modified`: Symbol body, signature, or attributes modified in $R$ (distinguishing `BodyModified`, `SignatureModified`, `CapabilityModified`, and `FormattingOnly`).
   - `LineageKind.Renamed`: Symbol renamed from `old_key` in $R_{\text{prev}}$ to `new_key` in $R$ (`1 -> 1` continuity, `HISTORY-INV-09`).
   - `LineageKind.Moved`: Symbol moved from module $M_{\text{old}}$ to $M_{\text{new}}$ (`1 -> 1` continuity, `HISTORY-INV-10`).
   - `LineageKind.ExtractedFrom`: Helper function `f_new` extracted from source function `f_orig` via `extract_function` (`1 -> 2` one-to-many lineage edge recording both `f_orig -> f_orig'` and `f_orig -> f_new`, `HISTORY-INV-11`).
   - `LineageKind.InlinedInto`: Symbol `x` or helper `f_helper` inlined into `f_target` (`2 -> 1` many-to-one lineage edge, `HISTORY-INV-12`).
   - `LineageKind.SplitInto` / `LineageKind.MergedFrom`: Explicit `1 -> N` symbol split and `N -> 1` symbol consolidation (`HISTORY-INV-11..12`).
   - `LineageKind.Removed`: Symbol deleted in $R$; historical lineage in prior revisions remains intact and queryable (`HISTORY-INV-13`), and a later symbol added with the same name does NOT automatically inherit the deleted symbol's lineage without explicit resurrection provenance (`HISTORY-INV-14`).
2. **Semantic blame & $O(\log N + K)$ indexed queries (`tasks/1062 §35–§42, §133, HISTORY-INV-15..17, 26..27, 33`)**:
   - `history_of_symbol(repo, symbol_key)` traces the symbol backward across renames, module moves, and function extractions in deterministic topological revision order, returning all $K$ semantic events in $O(\log N + K)$ time via the rebuildable semantic history index (`HISTORY-INV-26..27`).
   - Property-level blame (`blame_symbol_property`) identifies the exact `RevisionId` and `PatchId` that last modified a symbol's signature, receiver capability (`view` / `mut_view`), visibility, or `@repr` ABI layout, ignoring intervening formatting-only commits (`HISTORY-INV-15..17`).

```axiom
module std.vcs

pub const AXHISTORY_ABI_1: u32 = 1
pub const AXHISTORY_SCHEMA_1: u32 = 1
pub const AXVCS_ABI_1: u32 = 1
pub const AXVCS_SCHEMA_1: u32 = 1

pub enum LineageKind {
    Created,
    Modified,
    Renamed,
    Moved,
    ExtractedFrom,
    InlinedInto,
    SplitInto,
    MergedFrom,
    Removed,
}

pub struct LineageEdge {
    pub revision_id: u64,
    pub parent_revision_id: u64,
    pub kind: LineageKind,
    pub prior_symbol_key: u64,
    pub current_symbol_key: u64,
    pub patch_id: u64,
    pub evidence: u8,
}
```

### `AXS-REF-062` — `AXVCS` Content-Addressed Object Store, Deterministic Tree Ordering & Atomic Ref Transactions (`REQ-TOOL-305`)

1. **Content-addressed object store (`tasks/1063 §1–§15, §199 VCS-INV-01..10`, `REQ-TOOL-305`)**: `AXVCS` (`AXVCS_ABI_1 = 1`, `AXVCS_SCHEMA_1 = 1`, container `.axrepo`) stores all repository state as immutable, integrity-verified content-addressed objects keyed by `ObjectId = BLAKE3("axiom-vcs-obj-v1" || AXVCS_SCHEMA_1 || object_kind || canonical_payload)`:
   - `ObjectKind.Blob`: Raw UTF-8 source or asset bytes.
   - `ObjectKind.Tree`: Directory/module tree mapping entry names to `(EntryMode, ObjectKind, ObjectId, SemanticFileHash)`.
   - `ObjectKind.Semantic`: Serialized `CompilerDB` module interface & symbol table digest (`SemanticRoot`) for the snapshot.
   - `ObjectKind.Patch`: Canonical `AXPATCH` payload (`PatchId`).
   - `ObjectKind.Revision`: Canonical `AXHISTORY` revision record (`RevisionId`).
2. **Deterministic canonical ordering (`tasks/1063 §9–§12, VCS-INV-06..09, 37`, `REQ-TOOL-305`)**:
   - Every `Tree` object sorts its entries strictly by **canonical UTF-8 ASCII byte order of the entry name** (with forward-slash `/` normalized paths and zero host-OS directory-iteration order dependence).
   - Every `Semantic` snapshot sorts modules and symbols by canonical `SemanticKey` order.
   - Every repository export or log query sorts refs by canonical ref path (`refs/heads/*`, `refs/tags/*`) and revisions by topological parent order with lexicographical `RevisionId` tie-breaking (`VCS-INV-09, 37`).
3. **Atomic ref transactions, integrity verification & Git adapter boundary (`tasks/1063 §16–§35, VCS-INV-03, 11..16, 30..34`)**:
   - Reading any object from `ObjectStore` recomputes its BLAKE3 `ObjectId` and rejects corrupted or missing objects with `VcsStatus.IntegrityError` / `MissingObject` — never substituting empty bytes (`VCS-INV-03, 24`).
   - Branch and tag updates (`refs/heads/<branch>`, `refs/tags/<tag>`) execute as compare-and-swap atomic transactions (`expected_old_rev -> new_rev`). A failed commit or interrupted write leaves all refs at their prior revision (`VCS-INV-11..13, 30`).
   - `fetch` updates only remote-tracking refs (`refs/remotes/<remote>/*`) and never mutates local branch heads (`VCS-INV-14`); `push` rejects non-fast-forward overwrites unless explicitly authorized by policy (`VCS-INV-15`).
   - External Git repositories interoperate through a bidirectional `GitAdapter` mapping `GitCommitOid <-> ExternalRevisionRef` without coupling `CompilerDB` or `AXHISTORY` to Git line-diff internals (`tasks/1062 §7`, `tasks/1063 VCS-INV-34`).

### `AXS-REF-063` — CLI Driver Entrypoints (`axiomc refactor`, `axiomc diff`, `axiomc merge`, `axiomc patch`), Diagnostic Mapping & Conformance (`REQ-TOOL-183`, `REQ-TOOL-186`, `REQ-TOOL-301`..`REQ-TOOL-305`)

1. **CLI subcommands (`compiler/driver/refactor_cmd`, `0101 §45–§46`, `tasks/0448 §31`)**:
   - `axiomc refactor <op> <file>:<span_or_pos> [--name <ident>] [--check | --dry-run] [--json]`: Executes a `CompilerDB`-verified refactoring (`extract-fn`, `extract-var`, `inline-var`, `populate-match`, `organize-imports`, `change-sig`, `move-item`, `convert-view`), printing the canonical edit/patch or applying it atomically after `CompilerDB` re-verification.
   - `axiomc diff <left> <right> [--mode byte|trivia|ast|semantic|api|abi] [--json]`: Runs `AXDIFF` and emits a human-readable or `--json` (`AXDIFF_SCHEMA_1`) structural/semantic diff report. Exit code `0` when no breaking/semantic differences (or identical), `1` when differences are detected under `--check` or when breaking API/ABI changes are flagged, `2` on invalid CLI usage.
   - `axiomc merge <base> <left> <right> [-o <out>] [--json]`: Runs 3-way `AXMERGE` (`AXMERGE_SCHEMA_1`). Exit code `0` on `Clean` compiler-verified merge, `1` when explicit `MergeConflict` records remain unresolved, `2` on invalid CLI usage.
   - `axiomc patch apply|reverse|check|rebase <patch_file> [--dry-run] [--json]`: Runs transactional `AXPATCH` (`AXPATCH_SCHEMA_1`) with precondition and post-patch `CompilerDB` verification.
2. **Diagnostic area mapping (`spec/diagnostics.md AXD-010, AXD-020..021`)**:
   - E19.3 introduces no separate diagnostic area outside the 18 canonical areas of `spec/diagnostics.md §3`:
     - Refactoring and post-patch/post-merge semantic verification gates (`REQ-TOOL-186`) emit the exact canonical `CompilerDB` codes (`AX_PARSE_*`, `AX_NAME_UNRESOLVED`, `AX_NAME_DUPLICATE`, `AX_TYPE_MISMATCH`, `AX_TRAIT_AMBIGUOUS_METHOD`, `AX_PAT_NON_EXHAUSTIVE`, `AX_MOVE_USED_AFTER_MOVE`, `AX_MOVE_ASSIGN_IMMUTABLE`, `AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, `AX_CAP_OUTLIVES_OWNER`, `AX_UNSAFE_REQUIRED`).
     - CLI argument and option errors emit `AX_DRIVER_USAGE` or `AX_DRIVER_UNKNOWN_OPTION` (exit code `2`).
     - File and repository I/O errors emit `AX_IO_READ_FAILED` or `AX_IO_WRITE_FAILED` (exit code `1`).
     - Any internal invariant failure inside the refactoring or VCS engine emits `AX_ICE_INTERNAL` (`data.stage = "refactor_verify"` or `"vcs_verify"`, exit code `3`).
3. **Differential & conformance verification (`T809`, `T810`, `T811`)**:
   - Every refactoring transformation in `tests/run/refactor_engine` and `tests/conformance/p19/e19_3_refactoring_vcs` MUST preserve observable program semantics (`--interp` and native x86-64 outputs before and after refactoring are byte-for-byte identical, with `0 WEAK-NATIVE`).

---

## 8. Sources & References

- `0101` (`docs/base/specs/0101 - Axiom — IDE, LSP, Refactoring & AI-native Tooling v0.1.md`, §§1–17, §§25–29, §§45–48 `AIDE-01..25`)
- `tasks/0448` (`docs/base/tasks/0448 - BOOTSTRAP-189 — Developer Experience, IDE, Tooling & AI-Native Compiler Interface.md`, §§1–8, §§14–18, §31, §36 `ATOOL-20..40`)
- `tasks/1059` (`docs/base/tasks/1059 - BOOTSTRAP-794 — AXDIFF.md`, §§1–59, §§117–127, §§138–140, §241 `DIFF-INV-01..40`)
- `tasks/1060` (`docs/base/tasks/1060 - BOOTSTRAP-795 — AXMERGE.md`, §§1–62, §§85–106, §120 `MERGE-INV-01..40`)
- `tasks/1061` (`docs/base/tasks/1061 - BOOTSTRAP-796 — AXPATCH.md`, §§1–55, §§113–114 `PATCH-INV-01..40`)
- `tasks/1062` (`docs/base/tasks/1062 - BOOTSTRAP-797 — AXHISTORY.md`, §§1–45, §§130–133 `HISTORY-INV-01..40`)
- `tasks/1063` (`docs/base/tasks/1063 - BOOTSTRAP-798 — AXVCS.md`, §§1–60, §199 `VCS-INV-01..40`)
- `tasks/1064` (`docs/base/tasks/1064 - BOOTSTRAP-799 — AXPATCH.md`, §§1–75, §§112–115, §§145–149, §199 `PATCH-INV-01..40`)
- `spec/SPEC-01-lexical.md`, `spec/SPEC-02-grammar.md`, `spec/SPEC-10-ownership.md`, `spec/SPEC-11-capability.md`, `spec/SPEC-12-drop.md`, `spec/SPEC-21-query-engine-semantic-db.md`, `spec/SPEC-22-incremental-compilation.md`, `spec/SPEC-100-lsp-server-ide-engine.md`, `spec/SPEC-101-canonical-formatter.md`, `spec/diagnostics.md`, `spec/invariants.md`
