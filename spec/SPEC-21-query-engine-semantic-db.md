# SPEC-21 — Compiler Query Engine & Demand-Driven Semantic Database

- **Status**: draft (T752, 2026-11-03)
- **Owner**: `axiom-architect`
- **Consolidates**: `0153` (`specs/0153`, kernel architecture §3 & §6–§9), `0171` (`specs/0171`, kernel v0.1 §3.4 & §8), `0384` (`tasks/0384`, BOOTSTRAP-125 frontend incremental DB), `0530` (`tasks/0530`, BOOTSTRAP-271 query engine & semantic DB), `0532` (`tasks/0532`, BOOTSTRAP-273 `axiom_query` subsystem), `0533` (`tasks/0533`, BOOTSTRAP-274 query engine infrastructure), `0781` (`tasks/0781`, BOOTSTRAP-559 Query Engine 3.0), `0791` (`tasks/0791`, BOOTSTRAP-569 Diagnostic Engine 3.0)
- **Covers**: `specs/0153`, `specs/0171`, `tasks/0384`, `tasks/0530`, `tasks/0532`, `tasks/0533`, `tasks/0781`, `tasks/0791`
- **Related**: `spec/SPEC-01-lexical-source.md`, `spec/SPEC-02-ast-hir-lowering.md`, `spec/SPEC-05-type-system-core.md`, `spec/SPEC-10-mir-ownership-ir.md`, `spec/SPEC-20-selfhost.md`, `spec/diagnostics.md`, `spec/invariants.md`

## Tóm tắt

SPEC-21 định nghĩa kiến trúc cơ sở dữ liệu ngữ nghĩa hướng cầu (demand-driven semantic database — `CompilerDB`) và bộ máy truy vấn biên dịch (query engine) cho trình biên dịch tự thân `compiler/` (E18.1). Tài liệu quy định:
1. Tách biệt bất biến giữa **bảng đầu vào** (input tables: `SourceFileId`, `ModuleId`, `TargetConfig`, `PackageGraph`) gắn với `RevisionId` và **bảng suy dẫn** (derived query tables: `parse_module`, `resolve_module`, `item_signature`, `typeck_body`, `mir_body`, ...) được tính toán thuần túy, không có trạng thái toàn cục khả biến.
2. Thực thi truy vấn theo nhu cầu (demand-driven evaluation) với ngăn xếp truy vấn đang hoạt động (`QueryStack`), tự động ghi nhận đồ thị phụ thuộc có hướng (dependency DAG) từ truy vấn gọi sang truy vấn được gọi, bộ nhớ đệm theo `RevisionId`, và lệnh `inspect --emit=query-graph`.
3. Phát hiện chu trình truy vấn tất định (Tarjan / active-stack cycle detection), xoay chuẩn hóa chu trình theo khóa ngữ nghĩa nhỏ nhất (`SemanticKey`) để chẩn đoán độc lập với thứ tự gọi, cùng giá trị phục hồi (`ErrorType`, hằng/trait bị đánh dấu lỗi) nhằm ngăn lỗi dây chuyền.
4. Gắn kết chẩn đoán với ảnh chụp cơ sở dữ liệu (`SnapshotId` / `RevisionId`) để phát lại tất định khi trúng bộ nhớ đệm (warm hit), và cơ chế vô hiệu hóa lan truyền (transitive dirty marking) khi bảng đầu vào thay đổi.

---

## 1. `CompilerDB` Architecture, Input vs Derived Tables & Session Isolation

### `AXS-QRY-001` — `CompilerDB` Snapshot & Revision Model

The self-hosted Axiom compiler (`compiler/`) organizes all frontend and middle-end state inside an explicit, session-scoped semantic database (`CompilerDB`).

1. **Monotonic revision counter**: Every `CompilerDB` instance maintains a monotonically increasing 64-bit `RevisionId` (`R_0, R_1, ...`). `R_0` is the initial empty revision; each batch of mutations to an input table increments `RevisionId` before any derived query executes.
2. **Immutable query snapshots**: Derived queries never read or mutate live OS/filesystem state directly (`0153 §3.1`, `tasks/0781 §5`). Instead, query evaluation operates against an immutable `DatabaseSnapshot` identified by `(SnapshotId, RevisionId)`.
3. **No mutable global state**: Compiler phases (`lexer`, `parser`, `resolve`, `hir`, `ty`, `mir`, `diag`) SHALL NOT store semantic facts, intern tables, or diagnostic buffers in process-global mutable variables (`0153 §3.4`, `tasks/0533 §1`). Two `CompilerDB` instances in the same process are completely isolated.

```axiom
// Canonical Axiom model of the revision-stamped CompilerDB header
struct RevisionId {
    raw: u64
}

struct SnapshotId {
    session_id: u64,
    revision: RevisionId
}
```

### `AXS-QRY-002` — Explicit Input Tables vs Derived Query Tables

`CompilerDB` strictly partitions storage into **Input Tables** (set only by the driver/workspace loader between revisions) and **Derived Query Tables** (computed lazily by pure query functions).

| Table Kind | Canonical Table / Query Name | Key Type | Value / Result Summary | Durability |
|---|---|---|---|---|
| **Input** | `source_file_input` | `SourceFileId` | Normalized UTF-8 text, `ContentHash` (BLAKE3-256), line index (`SPEC-01`) | Low (High for stdlib) |
| **Input** | `module_tree_input` | `ModuleId` | Module path, parent/child `ModuleId` links, `SourceFileId` list | Medium |
| **Input** | `target_config_input` | `UnitKey` | `TargetTriple`, ABI profile, feature flags, edition, opt level | High |
| **Input** | `package_graph_input` | `PackageId` | Direct dependencies, edition, capability ceiling | High |
| **Derived** | `parse_module` | `ModuleId` | Green/Red CST + arena-allocated surface AST + parse diagnostics | Per-module |
| **Derived** | `module_def_map` | `ModuleId` | Exported & module-scope symbol table (`SymbolId -> DefId`) | Per-module |
| **Derived** | `resolve_module` | `ModuleId` | Lowered HIR items + name resolution bindings (`HirId -> DefId`) | Per-module |
| **Derived** | `item_signature` | `DefId` | Canonical item header: generics, parameter/return `TypeId`, `where` clauses, effect/cap contract | Interface-level |
| **Derived** | `typeck_body` | `DefId` | Expression types (`HirId -> TypeId`), method/coercion tables, body diagnostics | Body-level |
| **Derived** | `trait_solve` | `TraitGoalKey` | Canonical coherence/obligation result (`Implemented`, `Ambiguous`, `NoSolution`, `Error`) | Goal-level |
| **Derived** | `const_eval` | `ConstEvalKey` | Evaluated compile-time value (`ConstValue` or `ConstValue.Poisoned`) | Item/expr-level |
| **Derived** | `mir_body` | `DefId` | Lowered and ownership/region-verified `MirBody` (`SPEC-10`) | Body-level |
| **Derived** | `layout_of` | `TypeId` | Target-dependent size, alignment, field offsets, niche layout | Type-level |

### `AXS-QRY-003` — Session-Local Typed IDs vs Stable Semantic Keys

1. **Typed compact IDs (`u32`)**: Within a `DatabaseSnapshot`, tables are indexed by strongly typed 32-bit indices (`SourceFileId`, `ModuleId`, `DefId`, `HirId`, `TypeId`, `SymbolId`, `RegionId`, `MirBodyId`) (`0153 §6`, `0171 §5.2`). Raw integer conversions across ID domains are forbidden.
2. **Canonical `SemanticKey`**: Every `DefId` and `QueryKey` has a deterministic, allocation-order-independent `SemanticKey` composed of `(PackageName, ModulePath, ItemNamespace, DisambiguatorIndex, CanonicalName, CanonicalTypeArgs)` (`tasks/0781 §7`).
3. **Allocation-order independence**: Hashing, cycle canonicalization, and `inspect --emit=query-graph` output MUST order and compare keys by `SemanticKey`, never by raw pointer address or thread scheduling order.

### `AXS-QRY-004` — Interface Queries vs Body Queries Separation

1. **Header/body firewall**: Checking a caller function `f` that invokes callee `g` SHALL query `item_signature(g)` and NEVER `typeck_body(g)` or `mir_body(g)` unless `g` has an inferred return/const contract or is explicitly requested for CTFE/inlining (`tasks/0384 §3.2`, `tasks/0530 §4`, `tasks/0781 §8`).
2. **Unreferenced body isolation**: During signature-level or single-entry query execution, unreferenced function bodies (`typeck_body`, `mir_body`) are not evaluated on demand unless required by a full-module check (`check`/`build`) or transitive CTFE dependency.

### `AXS-QRY-005` — Query Purity Contract

Every derived query provider `Q(db: view<CompilerDB>, key: K) -> V` MUST be a pure deterministic function of `(db, key)`:
- It MAY read inputs or invoke other queries exclusivamente through `db`.
- It SHALL NOT mutate syntax/HIR/MIR arenas owned by previously completed queries.
- It SHALL NOT read wall-clock time, OS environment variables, random number generators, or filesystem paths directly (`0153 §3.1`, `tasks/0533 §4.2`).

---

## 2. Demand-Driven Evaluation, Memoization & Dependency DAG Recording

### `AXS-QRY-010` — Canonical `QueryKey` & `QueryState` Machine

Every derived query invocation is uniquely addressed by a canonical `QueryKey = (QueryKind, KeyPayload)` whose `KeyPayload` is interned and paired with its `SemanticKey`. Each memo table slot transitions strictly through the following states within a revision (`tasks/0530 §5`, `tasks/0781 §6`):

1. `Vacant`: Never evaluated in any revision.
2. `Computing(FrameIndex, OwnerWorkerId)`: Currently on the active `QueryStack` at `FrameIndex`.
3. `Ready(MemoEntry)`: Evaluated and memoized with `{ value, verified_at: RevisionId, changed_at: RevisionId, value_fingerprint: Fingerprint128, deps: Slice<QueryKey>, diagnostics: Slice<Diagnostic> }`.
4. `Poisoned(MemoEntry)`: Completed via cycle recovery or fatal dependency poison; stores the deterministic fallback value (`AXS-QRY-023`) and attached cycle/root diagnostics.

### `AXS-QRY-011` — Active `QueryStack` & Automatic Dependency Edge Recording

1. **Stack discipline**: Each evaluation context maintains an explicit `QueryStack` of active `QueryKey` frames `[Q_0, Q_1, ..., Q_k]`.
2. **Automatic edge capture**: Whenever `Q_k` is at the top of `QueryStack` and invokes `db.query(Q_next)`:
   - Before evaluating or returning `Q_next`, the engine appends `Q_next` to `Q_k`'s ordered dependency list `deps(Q_k)` (deduplicating repeated edges while preserving first-seen deterministic order).
   - Once `Q_next` finishes (`Ready` or `Poisoned`), the engine records the reverse edge `Q_next -> Q_k` in the reverse dependency index (`dependents`).
3. **Root queries**: Top-level driver queries pushed when `QueryStack` is empty record no caller edge, serving as roots of the query execution DAG.

```axiom
enum QuerySlotState {
    Vacant,
    Computing(u32),
    Ready(RevisionId),
    Poisoned(RevisionId)
}

struct DependencyEdge {
    caller: QueryKey,
    callee: QueryKey
}
```

### `AXS-QRY-012` — Revision-Stamped Memoization & Warm Hit Replay

When `db.query(Q)` is invoked at current revision `R_curr`:
1. **Same-revision hit (`verified_at == R_curr`)**: If the slot for `Q` is `Ready` or `Poisoned` with `verified_at == R_curr`, the engine increments the query's `memo_hits` counter, records the dependency edge `Q_caller -> Q`, replays any diagnostics bound to `Q` into the active query diagnostic sink (deduplicated per snapshot), and returns the cached `value` without re-executing the provider (`tasks/0781 §10`, `tasks/0791 §11`).
2. **Cold miss (`Vacant`)**: The engine increments `memo_misses`, pushes `Q` onto `QueryStack`, transitions the slot to `Computing`, executes the pure provider, seals `MemoEntry` with `verified_at = R_curr` and `changed_at = R_curr`, pops `Q`, and returns `value`.
3. **Stale revision verification (`verified_at < R_curr`)**: Handled by the shallow-verify / green-node reuse algorithm in `AXS-QRY-033`.

### `AXS-QRY-013` — Deterministic Query Graph Inspection (`inspect --emit=query-graph`)

The compiler CLI and test harness expose `axiom inspect <file> --emit=query-graph` (`T753`):
1. The output lists all executed `QueryKey` nodes sorted lexicographically by `(QueryKind, SemanticKey)`.
2. For each node, it emits its terminal state (`Ready` or `Poisoned`), `verified_at` and `changed_at` revisions, `memo_hits` / `memo_misses` counts, and outgoing ` caller -> callee ` dependency edges in canonical order.
3. Identical source inputs and query entry points MUST produce byte-for-byte identical `--emit=query-graph` output across runs.

---

## 3. Deterministic Query Cycle Detection & Recovery

### `AXS-QRY-020` — Legal Semantic Recursion vs Illegal Query Cycles

Not every recursive construct in Axiom is a query cycle (`tasks/0530 §8`, `tasks/0781 §11`):
1. **Legal recursion (not a query cycle)**:
   - Direct or mutual runtime function recursion `fn f(n: i32) -> i32 { f(n - 1) }`: resolved via `item_signature(f)` while `typeck_body(f)` is on the stack (`AXS-QRY-004`). Because `typeck_body(f)` queries `item_signature(f)` rather than `typeck_body(f)`, no query cycle arises.
   - Recursive nominal types via indirection (`struct Node { next: Option<Box<Node>> }`): nominal declaration headers are registered before field layouts are queried (`layout_of`).
2. **Illegal cyclic query dependencies**:
   - Cyclic type aliases (`type A = B` and `type B = A`).
   - Value-sized infinite struct/enum layout recursion without indirection (`struct Bad { inner: Bad }`).
   - Cyclic compile-time constant definitions (`const A: i32 = B + 1` and `const B: i32 = A + 1`).
   - Cyclic module re-exports / import aliases (`use a.X` -> `use b.X` -> `use a.X`).
   - Non-contractive trait/obligation cycles that exceed coinductive/depth policies.

### `AXS-QRY-021` — Active-Stack Cycle Detection & Cycle Policies

When `Q_k` invokes `db.query(Q_target)` and `Q_target` is already in state `Computing(idx)` on the active `QueryStack`:
1. The engine extracts the cycle slice `C = QueryStack[idx ..= k]` with closing edge `Q_k -> Q_target`.
2. It dispatches on `QueryKind.cycle_policy(Q_target)` (`tasks/0781 §11`):
   - `CyclePolicy.Reject`: Default for `item_signature`, `type_alias_expand`, `layout_of`, `const_eval`, `module_def_map`. Immediately triggers canonical cycle rotation (`AXS-QRY-022`), emits the cycle diagnostic once, and returns the query kind's deterministic recovery value (`AXS-QRY-023`).
   - `CyclePolicy.DepthLimited(max_depth)`: Used for trait solver goals (`trait_solve`) and CTFE recursion limits; if stack depth exceeds `max_depth`, emits `AX_QUERY_DEPTH_LIMIT` (or domain-specific limit code) and returns poisoned recovery.

### `AXS-QRY-022` — Canonical Cycle Rotation (Order-Independent Diagnostics)

To guarantee that cycle diagnostics are identical regardless of which item or module was queried first (`tasks/0530 §8.3`, `tasks/0781 §11.3`, `T754`):
1. Given raw cycle sequence `C = [Q_0, Q_1, ..., Q_{m-1}]`, the engine computes the index `p` that minimizes `(QueryKind.order_rank(Q_i), SemanticKey(Q_i))` under canonical lexicographical order.
2. The cycle is rotated to `C_canon = [Q_p, Q_{p+1}, ..., Q_{m-1}, Q_0, ..., Q_{p-1}, Q_p]`.
3. Primary span, diagnostic header, and cycle trace notes (`note: cycle step 1 -> ...`) are emitted strictly from `C_canon[0]`, and deduplicated by `CycleFingerprint = BLAKE3(C_canon)` within the snapshot so entering a 2-node cycle `(A, B)` from `A` or from `B` emits the exact same diagnostic.

### `AXS-QRY-023` — Deterministic Cycle Recovery Values

Every `QueryKind` under `CyclePolicy.Reject` or `DepthLimited` defines a total fallback constructor `cycle_recovery_value(db, key, C_canon)` (`tasks/0781 §11.4`, `tasks/0791 §10`):
- Type / signature / layout queries return `TypeId.ERROR` (`ErrorType`, `has_error = true`) or `LayoutResult.Poisoned`.
- Constant evaluation queries (`const_eval`) return `ConstValue.Poisoned`.
- Trait goal queries (`trait_solve`) return `TraitResult.Error`.
- Name/import resolution queries return `DefId.ERROR`.
The slot for the cycle head is marked `Poisoned(R_curr)` with this recovery value so callers unwind cleanly without panicking or diverging.

---

## 4. Snapshot-Bound Diagnostics, Causality Suppression & Revision Invalidation

### `AXS-QRY-030` — Snapshot-Bound Diagnostic Accumulation & Replay

1. **Per-query diagnostic sink**: During evaluation of `Q`, any diagnostic emitted by `Q` is appended to `Q`'s local diagnostic vector and tagged with `(SnapshotId, RevisionId, origin_query = Q)` (`tasks/0791 §11`, `T754`).
2. **MemoEntry persistence**: When `Q` completes (`Ready` or `Poisoned`), its local diagnostics are frozen inside `MemoEntry.diagnostics`.
3. **Cold vs warm equivalence**: When a warm query hit or green-verified node is reused in revision `R_curr`, the engine replays `MemoEntry.diagnostics` (plus transitive dependency diagnostics in canonical DFS dependency order) into the session diagnostic collector, deduplicating by `DiagnosticFingerprint`. Cold evaluation and warm memoized evaluation MUST produce identical diagnostic sets and ordering (`T754`, `T755`).

### `AXS-QRY-031` — Cascading Error Suppression on Poisoned / Recovery Values

To prevent a single cycle or syntax/type error from triggering secondary diagnostic avalanches (`tasks/0791 §10`, `T754`):
1. Every semantic carrier (`TypeId`, `ConstValue`, `DefId`, `TraitResult`, `MirOperand`) carries a poison bit (`is_error() == true` when constructed from `ErrorType`, `ConstValue.Poisoned`, or `DefId.ERROR`).
2. Downstream queries (`typeck_body`, `trait_solve`, `layout_of`, `mir_body`) that observe an input with `is_error() == true` MUST propagate a poisoned result silently without emitting secondary type-mismatch, missing-field, or unresolved-method diagnostics.
3. Unrelated items, functions, and modules in the same `CompilerDB` whose dependency subgraphs do not touch the poisoned node MUST continue normal checking and emit all of their own genuine diagnostics.

### `AXS-QRY-032` — Input-Revision Invalidation & Transitive Dirty Marking

When one or more input table entries (`source_file_input`, `module_tree_input`, `target_config_input`) are mutated (`tasks/0530 §6`, `tasks/0781 §10`, `T754`):
1. `CompilerDB` increments `RevisionId` to `R_next = R_curr + 1`.
2. If the mutated input's content hash (`ContentHash`) is unchanged from `R_curr`, no derived slots are dirtied.
3. If `ContentHash` changed, the engine marks the input key modified at `R_next` and traverses the reverse dependency DAG (`dependents`) from that input to mark all transitive dependent query slots `MaybeDirty(R_next)`.

### `AXS-QRY-033` — Shallow Verification & Firewall Green-Node Reuse

When `db.query(Q)` encounters a `MaybeDirty(R_next)` slot with stored `MemoEntry` from `R_prev`:
1. The engine iterates `deps(Q)` in recorded order and verifies each dependency `D_i` at `R_next`.
2. If every `D_i` verifies with `changed_at(D_i) <= verified_at(Q)`, `Q`'s inputs have not semantically changed: the engine updates `verified_at(Q) = R_next` (green-node reuse) without running `Q`'s provider.
3. If any `D_i` has `changed_at(D_i) > verified_at(Q)`, the engine re-executes `Q`'s provider at `R_next` and computes `new_fingerprint = fingerprint128(new_value)`.
4. **Backdating (firewall stop)**: If `new_fingerprint == old_fingerprint` and `new_diagnostics == old_diagnostics`, the engine sets `verified_at(Q) = R_next` while preserving the older `changed_at(Q)`, halting invalidation propagation to callers of `Q` (e.g. editing a function body does not invalidate `item_signature(f)` or downstream callers).

---

## 5. Diagnostics, Canonical Examples & Verification Matrix

### `AXS-QRY-050` — Query Engine & Cycle Diagnostic Codes

| Code | Severity | Category | Trigger Summary |
|---|---|---|---|
| `AX_QUERY_CYCLE` | Error | `QRY` | Generic illegal cyclic query dependency detected on `QueryStack` (`AXS-QRY-021`) when no narrower domain code applies |
| `AX_TYPE_CYCLE` | Error | `QRY` / `TYP` | Cyclic type alias expansion (`type A = B; type B = A`) or infinite value-sized struct/enum layout recursion without indirection |
| `AX_CTM_CYCLE` | Error | `CTM` / `QRY` | Cyclic compile-time `const` / `comptime` dependency (`AX_CONST_CYCLE` alias, `SPEC-08`) |
| `AX_TRAIT_CYCLE` | Error | `TRT` / `QRY` | Cyclic trait/obligation resolution goal under `CyclePolicy.Reject` or `DepthLimited` |
| `AX_QUERY_DEPTH_LIMIT` | Error | `QRY` | Query evaluation stack depth exceeded configured recursion limit (`CyclePolicy.DepthLimited`) |

### `AXS-QRY-051` — Positive Canonical Examples

```axiom
// Example 1: Demand-driven isolation & header/body firewall (AXS-QRY-004, AXS-QRY-033)
module math

pub fn square(x: i32) -> i32 {
    x * x
}

pub fn compute(a: i32) -> i32 {
    // Checking `typeck_body(math.compute)` queries `item_signature(math.square)`
    // and does NOT depend on `typeck_body(math.square)`.
    // Editing the body of `square` (e.g., to `(x + 0) * x`) leaves
    // `item_signature(math.square)` fingerprint unchanged, so `typeck_body(math.compute)`
    // is reused green without re-running its provider.
    square(a) + 1
}

// Legal runtime recursion: `typeck_body(math.fact)` queries `item_signature(math.fact)`,
// NOT `typeck_body(math.fact)` -> no query cycle (AXS-QRY-020).
pub fn fact(n: i32) -> i32 {
    if n <= 1 {
        1
    } else {
        n * fact(n - 1)
    }
}
```

### `AXS-QRY-052` — Negative Canonical Examples (Cycle Detection, Canonical Rotation & Recovery)

```axiom
// Example 2: Order-independent cycle diagnostics & cascade suppression (AXS-QRY-022, AXS-QRY-031)
module cycles

// Cycle 1: Mutual compile-time constants (`const_eval(cycles.ALPHA)` <-> `const_eval(cycles.BETA)`).
// Canonical SemanticKey order rotates the cycle to start at `cycles.ALPHA`
// regardless of whether `ALPHA` or `BETA` is queried first.
const BETA: i32 = ALPHA + 1
const ALPHA: i32 = BETA + 1 // ERROR [AX_CTM_CYCLE]: cyclic constant evaluation: `cycles.ALPHA -> cycles.BETA -> cycles.ALPHA`

// Cycle 2: Recursive type aliases (`item_signature(cycles.Left)` <-> `item_signature(cycles.Right)`).
type Right = Left
type Left = Right // ERROR [AX_TYPE_CYCLE]: cyclic type alias definition: `cycles.Left -> cycles.Right -> cycles.Left`

pub fn downstream_uses_poisoned() -> i32 {
    // `ALPHA` evaluates to `ConstValue.Poisoned` (AXS-QRY-023).
    // No secondary cascading type-mismatch error is emitted here (AXS-QRY-031).
    let x: i32 = ALPHA
    x
}

pub fn unrelated_function_still_checked() -> i32 {
    // Independent subgraph in the same module continues normal checking and reports genuine errors:
    let bad: i32 = "not_an_int" // ERROR [AX_TYP_MISMATCH]
    bad
}
```

### `AXS-QRY-053` — E18.1 Implementation & Verification Matrix

| Task | Scope | Required Verification Target | Invariant ID |
|---|---|---|---|
| `T753` | `CompilerDB` input/derived tables, demand-driven `QueryStack`, dependency DAG recording, `inspect --emit=query-graph` | `tests/run/query_db` | `INV-QRY-001` |
| `T754` | Active-stack cycle detection, canonical rotation, fallback recovery values, snapshot-bound diagnostics, revision invalidation | `tests/run/query_cycles` | `INV-QRY-002` |
| `T755` | Multi-module demand-driven isolation, order-independent cycle diagnostics, cold vs warm equivalence, `--interp` vs native equivalence | `tests/conformance/p18/e18_1_query_engine` | `INV-QRY-003` |

---

## Sources

- `docs/base/specs/0153 - AXIOM COMPILER KERNEL SPEC.md` (§3 Architectural Principles, §6 Identity & Interning, §7 Source DB, §8 Memory & Arenas, §9 Diagnostics)
- `docs/base/specs/0171 - XXXIV — Axiom Compiler Kernel v0.1.md` (§3.4 No Global Mutable Compiler State, §5.2 Typed IDs, §8 Incremental Hook)
- `docs/base/tasks/0384 - BOOTSTRAP-125 — Compiler Frontend Architecture & Incremental Compiler Database.md`
- `docs/base/tasks/0530 - BOOTSTRAP-271 — AXIOM COMPILER QUERY ENGINE, INCREMENTAL COMPILATION & PARALLEL SEMANTIC DATABASE.md`
- `docs/base/tasks/0532 - BOOTSTRAP-273 — AXIOM COMPILER REPOSITORY & IMPLEMENTATION SPECIFICATION.md` (`axiom_query` subsystem)
- `docs/base/tasks/0533 - BOOTSTRAP-274 — AXIOM COMPILER COMMON INFRASTRUCTURE & QUERY ENGINE.md`
- `docs/base/tasks/0781 - BOOTSTRAP-559 — COMPILER QUERY ENGINE 3.0, DEMAND-DRIVEN SEMANTIC DATABASE, CYCLE HANDLING, QUERY INVALIDATION, SNAPSHOT REUSE & CROSS-PHASE DEPENDENC.md`
- `docs/base/tasks/0791 - BOOTSTRAP-569 — COMPILER DIAGNOSTIC ENGINE 3.0.md` (§10 Error Recovery & Poisoning, §11 Query Engine & Incremental Diagnostic Caching)
