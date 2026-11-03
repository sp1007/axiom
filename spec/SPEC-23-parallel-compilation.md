# SPEC-23 — Parallel Compilation, Thread-Safe Snapshots & Deterministic DAG Scheduling

- **Status**: draft (T760, 2026-11-03)
- **Owner**: `axiom-architect`
- **Consolidates**: `0153` (`specs/0153`, §19 & §37 `APAR-20..24`), `0473` (`tasks/0473`, BOOTSTRAP-214 §214.24–§214.33 `ACOMPILER-30..33`), `0528` (`tasks/0528`, BOOTSTRAP-269 §115, §131 & §134 `ACOMPARCH-20..60`), `0530` (`tasks/0530`, BOOTSTRAP-271 §127–§148 & §163 `AQUERY-50..80`), `0593` (`tasks/0593`, BOOTSTRAP-334 §1–§57), `0789` (`tasks/0789`, BOOTSTRAP-567 §567.101–§567.200), `0790` (`tasks/0790`, BOOTSTRAP-568 §568.1–§568.200)
- **Covers**: `REQ-DRV-018`, `REQ-CORE-2669..2711`, `REQ-CORE-3125`, `REQ-CORE-3126`, `REQ-TOOL-224..254`, `REQ-LNK-934..1233`
- **Related**: `spec/SPEC-20-selfhost.md`, `spec/SPEC-21-query-engine-semantic-db.md`, `spec/SPEC-22-incremental-compilation.md`, `spec/diagnostics.md`, `spec/invariants.md`

## Tóm tắt

SPEC-23 định nghĩa kiến trúc biên dịch song song (parallel compilation), ảnh chụp cơ sở dữ liệu ngữ nghĩa an toàn luồng (thread-safe `DatabaseSnapshot`), cấp phát định danh độc lập với thứ tự lập lịch, và bộ lập lịch DAG đánh cắp việc (work-stealing scheduler) cho `compiler/` (E18.3):
1. **Bất biến tương đương tuyệt đối giữa tuần tự và song song (`--jobs 1` == `--jobs N`)**: Song song hóa chỉ thay đổi thứ tự thực thi vật lý giữa các luồng worker, tuyệt đối không làm thay đổi ngữ nghĩa chương trình, định danh ngữ nghĩa (`DefId`, `HirId`, `TypeId`, `SymbolId`), danh sách và thứ tự chẩn đoán (`AXD-060`), hay từng byte của tệp đầu ra `.obj`/`.lib`/`.dll`/`.exe` (`APAR-20..24`, `ACOMPILER-30`, `ACOMPARCH-36`, `AQUERY-77`).
2. **Ảnh chụp bất biến, định danh theo phạm vi module & bảng intern phân mảnh (sharded interner)**: Worker chỉ đọc từ `DatabaseSnapshot` bất biến, dùng vùng nhớ arena cục bộ theo luồng/truy vấn, cấp phát định danh dạng `(ModuleId, LocalIndex)` hoặc định danh theo nội dung (`SemanticKey`), và intern chuỗi/kiểu qua bảng băm phân mảnh mà không đua tranh trên bộ đếm toàn cục.
3. **Khử trùng lặp truy vấn đang chạy (`SingleFlightLatch`), phát hiện chu trình xuyên luồng & lập lịch DAG**: Khi nhiều worker cùng yêu cầu một `QueryKey` hoặc `ActionId`, chỉ một worker thực thi còn các worker khác đợi trên chốt đơn luồng; đồ thị chờ (`WaitForGraph`) phát hiện tức thời mọi chu trình xuyên worker (`AQUERY-51`) và xoay chuẩn hóa theo `SemanticKey`. Bộ lập lịch DAG điều phối theo đường găng (critical path) và ngân sách tài nguyên (`cpu_cost`, `memory_cost`).
4. **Sinh mã song song theo đơn vị biên dịch (`CGU`) & hợp nhất tất định sau khi gom luồng**: Các `CodegenUnit` bẩn được hạ bậc LIR, phân bổ thanh ghi và sinh COFF `.obj` song song (kết hợp nạp `.obj` sạch từ `.axiom-cache`), sau đó hợp nhất bộ đệm chẩn đoán và truyền `.obj` vào trình liên kết theo đúng thứ tự chỉ mục chuẩn.

---

## 1. Fundamental Parallel Determinism Invariant, Layer Boundaries & Thread-Count-Independent Identity

### `AXS-PAR-001` — Fundamental Parallel Determinism Invariant (`--jobs 1` == `--jobs N`)

1. **Physical order vs semantic order**: Parallelism changes physical execution order across worker threads only; it SHALL NEVER alter semantic evaluation results, inferred types, trait selection, ownership/capability decisions, MIR/LIR/machine-IR dumps, diagnostic sets/ordering, or output artifact bytes (`REQ-DRV-018`, `REQ-CORE-2669`, `REQ-TOOL-250`, `0153 APAR-20`, `0473 ACOMPILER-30`, `0528 §115, ACOMPARCH-36`, `0530 AQUERY-50, AQUERY-77`).
2. **Thread-count and policy invariance**: Compiling any workspace with `--jobs 1`, `--jobs 2`, `--jobs 4`, `--jobs 8`, or `--jobs N` under any valid scheduling policy (`Interactive`, `Balanced`, `Throughput`, `MemoryBound`, `LowPower`, `DeterministicDebug`) MUST converge to byte-for-byte identical `.obj`, `.lib`, `.dll`, and `.exe` outputs and identical `AXD-060` diagnostic streams (`REQ-TOOL-251..252`, `REQ-LNK-972..973`, `REQ-LNK-1057`, `REQ-LNK-1230..1233`, `0530 AQUERY-78..79`, `0789 §567.139–140`, `0790 §568.197–200`).

### `AXS-PAR-002` — Acyclic Compiler Architecture & Semantic vs Representation Authority

The self-hosted compiler (`compiler/`) enforces the frozen architectural contracts of `0528 §131–134` (`ACOMPARCH-20..60`, `REQ-CORE-2670..2711`) and `0530 §163–164` (`AQUERY-51..80`, `REQ-TOOL-224..254`):
1. **Acyclic module graph & layer separation (`ACOMPARCH-20..30`, `ACOMPARCH-51..56`)**: Compiler subsystems form a strict DAG (`INV-LAYER-001`, CI-enforced via `archcheck` per `ACOMPARCH-45`) with explicit input/output/invariant contracts and no miscellaneous dependency sink (`ACOMPARCH-55..56`). Semantic layers (`resolve`, `hir`, `ty`, `traits`, `own`) own language meaning; representation/codegen layers (`lir`, `abi`, `target`, `obj`, `link`) own physical realization. Frontend and type semantics never depend on target ISA or register allocation (`ACOMPARCH-23..24`), `MIR` remains target-independent (`ACOMPARCH-25`), `LIR` remains ISA-independent (`ACOMPARCH-26`), `TargetBackend` is the ISA boundary (`ACOMPARCH-27`), `ABI` classification is target-dependent (`ACOMPARCH-28`), and object emission/linking remain independent of frontend type checking (`ACOMPARCH-29..30`). Replacing a backend, object writer, or linker, or adding a target ISA, never requires changing core frontend semantics (`ACOMPARCH-51..54`).
2. **Single semantic authority (`ACOMPARCH-31..32`, `ACOMPARCH-42..43`, `ACOMPARCH-48`, `AQUERY-60..66`, `AQUERY-73..74`)**: `CompilerDB` provides shared query infrastructure (`SPEC-21`) and is the sole semantic database for compiler and tooling queries (`REQ-TOOL-246..247`, `REQ-TOOL-254`), while remaining infrastructure rather than a semantic layer itself (`ACOMPARCH-32`). Caches (`ACOMPARCH-48`), schedulers, optimizers, backends, and AI agents never create competing semantic truth or directly mutate semantic compiler state (`ACOMPARCH-42`, `AQUERY-64`); AI-generated or `@derive`-generated code retained with source provenance (`AQUERY-62`) passes through the full verification pipeline (`ACOMPARCH-43`, `AQUERY-63`). Explanations and invalidation traces derive strictly from recorded semantic facts and dependency edges (`AQUERY-65..66`, `ACOMPARCH-57`).
3. **Verification & fail-closed pipeline boundaries (`ACOMPARCH-37..41`, `ACOMPARCH-44`, `AQUERY-60..61`)**: Partial or unverified semantic results never cross the verification/codegen boundary (`AQUERY-60`), unknown information is never treated as proof (`AQUERY-61`), verification precedes optimization and codegen (`ACOMPARCH-37`), only `Verified MIR` enters production codegen (`ACOMPARCH-38`), optimization failures fail closed without invalidating semantics (`ACOMPARCH-39`), and backend or object-writer failures emit structured diagnostics (`ACOMPARCH-44`) rather than invalid machine code or corrupt artifacts (`ACOMPARCH-40..41`).
4. **Implementation independence & cache separation (`ACOMPARCH-46..47`, `ACOMPARCH-49..50`, `ACOMPARCH-58..60`, `AQUERY-67..72`, `AQUERY-75..76`, `AQUERY-80`)**: The self-hosted compiler uses the same module contracts as the bootstrap compiler without letting the bootstrap host language define module semantics (`ACOMPARCH-49..50, 60`). Compiler memory management uses arenas and structural sharing without tracing GC (`ACOMPARCH-46..47`, `AQUERY-80`). Semantic fingerprints and codegen fingerprints remain distinct (`ACOMPARCH-58`, `SPEC-22`): compiler semantic version changes invalidate incompatible semantic caches (`AQUERY-69`), whereas codegen-only or tooling-only changes and performance instrumentation do not invalidate semantic caches or alter semantics (`AQUERY-67, 70..71`). Local and remote caches validate complete semantic/codegen identities (`REQ-DRV-018`, `AQUERY-53, 68, 72`), and incremental/cached execution is indistinguishable from clean evaluation (`ACOMPARCH-59`, `AQUERY-54, 75..76`).

### `AXS-PAR-003` — Immutable `DatabaseSnapshot` Sharing & Per-Worker Arena Isolation

1. **Read-only snapshot execution**: Worker threads execute queries and build actions exclusively against an immutable `DatabaseSnapshot` bound to `(BuildSnapshotId, RevisionId)` (`SPEC-21 AXS-QRY-001`, `REQ-CORE-2685`, `REQ-LNK-1132..1133`, `0153 APAR-21`, `0528 ACOMPARCH-34`). Input tables and previously published semantic objects are immutable after publication and shared across revisions and workers via structural sharing (`REQ-TOOL-228..229`, `0530 AQUERY-55..56`).
2. **Thread-local / query-local arenas**: Each worker thread allocates temporary CST, AST, HIR, constraint-solving, MIR, and LIR data inside an isolated per-query or per-worker `Arena` (`0153 APAR-21..22`, `0528 ACOMPARCH-47`). Once a query seals its result into a `MemoEntry`, its arena is frozen as read-only for the lifetime of the snapshot. No worker ever mutates another worker's live arena.

### `AXS-PAR-004` — Module-Scoped `(ModuleId, LocalIndex)` IDs & Content-Addressed Semantic Identity

To eliminate non-deterministic ID assignment when modules or functions are processed in parallel (`0153 ACKERNEL-21`, `0473 §214.24–25`, `0528 ACOMPARCH-33`, `0530 §127–130`, `0593 §17`, `T761`):
1. **Forbidden global sequential counters**: Concurrent lexing, parsing, HIR lowering, typechecking, and MIR construction SHALL NEVER allocate `DefId`, `HirId`, `LocalId`, `BlockId`, or `RegionId` from an unsynchronized or lock-contended global atomic counter whose values depend on thread arrival order.
2. **Two-level module-scoped IDs**: Every item and AST/HIR node ID is encoded deterministically as `(ModuleId, LocalIndex)` (or `(DefId, BodyLocalIndex)` for body-local `HirId` / `MirLocalId` / `BasicBlockId`), where:
   - `ModuleId` is assigned in canonical topological / lexicographical module-path order during workspace discovery before parallel fan-out.
   - `LocalIndex` is assigned deterministically by sequential preorder traversal within the single worker that parses or lowers that module/body.
3. **Deterministic trait & constraint ordering**: Hash-map iteration (`INV-KERN-007`), trait candidate assembly, and parallel type constraint solving sort and merge candidates by canonical `SemanticKey` order, never by worker completion order or pointer address (`REQ-CORE-2684`, `REQ-TOOL-225`, `0530 §128–130`).

### `AXS-PAR-005` — Sharded Deterministic String & Type Interner

1. **Content-addressed sharding**: `compiler/parallel/scheduler` partitions the string interner and structural type interner into $2^k$ fixed shards (e.g. 64 shards) indexed by the high bits of the 64-bit canonical content hash (`BLAKE3` / `SipHash-2-4` over UTF-8 bytes or canonical `TypeKey` structure) (`0153 AINTERN-20..23`, `T761`).
2. **Order-independent canonical ID**: A `StrId` or `TypeId` encodes `(shard_id, canonical_key_hash)` or resolves through a frozen post-phase canonical table sorted by content/structure so that all comparisons, serializations, and emitted symbols use canonical structural identity rather than thread insertion timing (`REQ-TOOL-241`, `0530 §127, AQUERY-68`).

```axiom
// Canonical Axiom model of module-scoped IDs and sharded interner keys
struct ScopedDefId {
    module_id: u32,
    local_index: u32
}

struct ShardedInternId {
    shard: u16,
    slot: u32,
    content_hash64: u64
}
```

---

## 2. Single-Flight Query Deduplication, Cross-Worker Cycle Detection & Work-Stealing DAG Scheduler

### `AXS-PAR-010` — In-Flight Query Deduplication & `SingleFlightLatch` State Machine

When multiple worker threads concurrently invoke `db.query(Q)` (or execute a shared `ActionId`) on the same `DatabaseSnapshot` (`REQ-LNK-1121..1124`, `REQ-LNK-1166..1168`, `REQ-LNK-1194`, `0530 §139–141`, `0790 §568.88–91, §568.133–135, §568.161`, `T761`):
1. **Atomic claim (`Vacant -> Computing(OwnerWorkerId, LatchId)`)**: The first worker to claim slot `Q` transitions the slot atomically to `Computing` and becomes the sole owner executing `Q`'s provider.
2. **Single-flight wait or work-steal**: Any second worker `W_2` requesting `Q` while `Q` is `Computing(W_1, LatchId)` does NOT duplicate execution:
   - First, `W_2` runs the cross-worker wait-for cycle check (`AXS-PAR-011`).
   - If no cycle exists, `W_2` registers on `LatchId` and cooperatively executes ready tasks from its work-stealing queue (or parks on `LatchId`) until `W_1` transitions `Q` to `Ready(MemoEntry)` or `Poisoned(MemoEntry)`.
3. **Deduplicated duplicate/speculative results**: If speculative or retry execution produces a duplicate completion for the same `ActionId`, the first verified result commits and any later duplicate is verified for byte/fingerprint equivalence (raising `AX_ICE_INTERNAL` / `BUILD_INCONSISTENCY` on mismatch) and discarded (`REQ-LNK-1008..1009`, `REQ-LNK-1121..1124`).

### `AXS-PAR-011` — Cross-Worker Wait-For Graph & Deadlock-Free Cycle Detection

To guarantee that no query or build action ever waits indefinitely on itself across threads (`REQ-TOOL-224`, `REQ-LNK-1041..1043`, `REQ-LNK-1114..1115`, `0530 §163 AQUERY-51`, `0593 §15`, `0790 §568.8–10, §568.81–82`, `T761`):
1. **Global `WaitForGraph`**: The scheduler maintains an atomic wait-for table mapping each blocked query/worker `Q_waiter` (owned by `W_2`) to the in-flight query `Q_target` (owned by `W_1`) it is waiting on.
2. **Cross-worker cycle detection**: Before `W_2` waits on `Q_target`, the scheduler walks the active `QueryStack`s and `WaitForGraph` chain starting from `W_1`. If `Q_target` transitively waits on any query currently active on `W_2`'s `QueryStack`, a cross-worker cycle `C` is detected immediately without deadlocking.
3. **Canonical rotation & deterministic recovery**: The detected cross-worker cycle `C` is rotated to its lexicographically minimum `(QueryKind, SemanticKey)` head (`SPEC-21 AXS-QRY-022`), emits the exact same `AX_QUERY_CYCLE` / `AX_TYPE_CYCLE` / `AX_CTM_CYCLE` / `AX_TRAIT_CYCLE` diagnostic as single-threaded `--jobs 1` execution, and seals the cycle head with its deterministic recovery value (`SPEC-21 AXS-QRY-023`).
4. **SCC scheduling & resource deadlock prevention**: Legal Strongly Connected Components (`SCC`s, e.g. mutually recursive functions within a module) are collapsed into a single atomic DAG scheduling unit (`REQ-LNK-1041..1043`), and resource reservations are acquired in canonical sorted order so two actions never form a resource wait cycle (`REQ-LNK-1114..1115`).

```axiom
enum ActionState {
    Pending,
    Blocked,
    CacheCheck,
    Verified,
    Ready,
    Dispatched,
    Running,
    Success,
    Failed,
    Cancelled,
    Lost,
    BlockedByFailure
}

struct ResourceCostEstimate {
    cpu_tokens: u16,
    memory_bytes: u64,
    critical_cost: u64
}
```

### `AXS-PAR-012` — Action & Query DAG State Machine, Critical-Path Priority & Work-Stealing Queue Hierarchy

1. **Action state machine (`REQ-LNK-1034..1040`, `0790 §568.1–7`)**: Every scheduled node transitions through `Pending -> Blocked (remaining_dependencies > 0) -> CacheCheck (Hit -> Verified | Miss -> Ready) -> Dispatched -> Running -> {Success, Failed, Cancelled, Lost}`. If a required dependency fails, downstream dependents transition to `BlockedByFailure` (`REQ-LNK-1040`).
2. **Critical-path & cost-model prioritization (`REQ-CORE-3126`, `REQ-LNK-1044..1051`, `REQ-LNK-1178..1180`, `0593 §3, §6–7`, `0790 §568.11–18`)**: Each node carries an estimated `ResourceCostEstimate { cpu_tokens, memory_bytes, critical_cost }`. The scheduler prioritizes ready nodes with higher `critical_cost` (longest estimated path to completion). Cost estimates and historical/AI scheduling predictions are strictly performance hints (`REQ-CORE-3126`, `REQ-LNK-1048`, `REQ-LNK-1180`, `REQ-LNK-1197..1203`): they never affect artifact identity or semantics, and corrupt/unavailable models fall back to static deterministic heuristics (`REQ-LNK-1199..1203`).
3. **Queue hierarchy & work stealing (`REQ-LNK-1052..1057`, `REQ-LNK-1076..1087`, `REQ-LNK-1109..1113`, `0593 §41–45`, `0790 §568.19–24, §568.43–54, §568.76–80`)**:
   - The orchestrator maintains a priority-tiered `GlobalReadyQueue` (`Critical`, `Interactive`, `Normal`, `Background`) feeding per-worker local deques.
   - Idle workers steal ready tasks matching their resource capability (`REQ-LNK-1076..1077`).
   - Priority inheritance boosts prerequisites of `Critical`/`Interactive` nodes (`REQ-LNK-1080..1081`), while priority aging guarantees bounded starvation for `Background` work (`REQ-LNK-1079`, `REQ-LNK-1113`).
   - Small lexical/parse/query/codegen tasks may be batched for efficiency without altering observable semantics (`REQ-LNK-1082..1087`).

### `AXS-PAR-013` — Resource-Token Admission Control, Memory Pressure Governance & Bounded Nested Parallelism

1. **Automatic optimal parallelism & token budgets (`REQ-CORE-3125`, `REQ-LNK-1058..1069`, `REQ-LNK-1116..1117`, `0593 §8–14, §334`, `0790 §568.25–36, §568.83–84`)**: The scheduler governs concurrency via explicit `CPU`, `Memory`, `GPU`, and `IO` token pools (`max_parallel_actions` defaults to logical CPU count, overridden by `--jobs <N>`). An action is admitted to `Dispatched` only when both its `cpu_tokens` and `memory_bytes` reservations are available, and releases all tokens immediately upon completion.
2. **Memory pressure throttling & OOM recovery (`REQ-LNK-970..971`, `REQ-LNK-1181..1183`, `REQ-LNK-1188..1192`, `0593 §9–12, §46–47`, `0789 §567.137–138`, `0790 §568.148–159`)**:
   - Only actions in the reachable dependency closure of the requested build goals are materialized (`REQ-LNK-1188..1192`).
   - Under `Pressure` or `Critical` memory thresholds, the scheduler throttles admission of high-memory actions (e.g. large `CGU` optimization or `LTO` partitions) before OOM occurs, and retries any OOM-interrupted action at lower concurrency (`REQ-LNK-1182..1183`). Low worker memory may delay or fail an action with `AX_ICE_OUT_OF_MEMORY`, never produce altered output bytes (`REQ-LNK-971`).
3. **Forbidden uncontrolled nested parallelism (`REQ-LNK-1063..1064`, `0593 §14, §56`)**: Subsystem passes (lexing, parsing, typechecking, `OptIR`, codegen, linking) SHALL NOT spawn unmanaged OS thread pools; all parallel sub-tasks submit into the shared cooperative work-stealing pool so total active threads never exceed the `--jobs <N>` budget.

### `AXS-PAR-014` — Speculative Execution, Cancellation, Preemption & Interactive Responsiveness

1. **Validated speculation (`REQ-LNK-1088..1108`, `0530 §142`, `0790 §568.55–75`)**: When module `A` is being compiled, the scheduler may speculatively evaluate downstream module `B` or prefetch artifacts (`REQ-LNK-1104..1108`) under the assumption that `InterfaceFingerprint(A)` remains unchanged (`SPEC-22`). Speculative outputs remain isolated and uncommitted until `A` finishes: if the assumption holds (`assumption == actual`), the speculative result is promoted; otherwise it is cancelled and discarded (`REQ-LNK-1092..1098`).
2. **Interactive / LSP priority & cancellation (`REQ-LNK-1151..1172`, `0593 §21–22, §44`, `0790 §568.118–139`)**: Foreground IDE/LSP diagnostic requests run in the `Interactive`/`Foreground` class, can preempt cancellable background work, emit independent diagnostics as soon as required semantic facts are ready (`time-to-first-diagnostic`, `REQ-LNK-1160..1162`), and cleanly cancel superseded queries without corrupting committed cache entries or leaving temporary files (`REQ-LNK-1151..1155`, `REQ-LNK-1165`).

### `AXS-PAR-015` — Hermetic Action Identity, Local/Remote Worker Equivalence & Fault Recovery

1. **Hermetic execution & environment isolation (`REQ-LNK-934..969`, `REQ-LNK-974..982`, `REQ-LNK-1004..1033`, `0593 §25–35`, `0789 §567.101–200`)**: Every build/codegen action declares explicit content-addressed inputs (sources, `TargetTriple`, CPU/SIMD features, ABI, optimization/PGO/debug/security/safety profile, lockfile, sysroot/SDK/runtime digests) and explicit declared outputs (`ActionResult { action_id, outputs, diagnostics, execution_metadata }`). Host architecture, hostname, PID, timestamps, inode/mtime, undeclared env vars, shell aliases, locale, timezone, NUMA node (`REQ-LNK-1073..1075`), and worker IDs (`REQ-LNK-935..937`) are excluded from canonical artifact identity. Offline and air-gapped modes (`distributed = disabled`, `remote_cache = disabled`, `network = false`) remain 100% functional from local inputs (`REQ-LNK-1002..1005`).
2. **Fault classification, leases & quarantine (`REQ-LNK-983..1001`, `REQ-LNK-1006..1025`, `REQ-LNK-1118..1131`, `REQ-LNK-1144..1150`, `REQ-LNK-1173..1177`, `0593 §36–39`, `0790 §568.85–98, §568.111–117, §568.140–144`)**: Failures are classified into `SourceFailure` (deterministic user error — never retried, `REQ-LNK-1126`), `WorkerFailure` / `NetworkFailure` / `InfrastructureFailure` (retried with bounded exponential backoff on expired leases, `REQ-LNK-1118..1120`, `REQ-LNK-1127`, `REQ-LNK-1129`, `REQ-LNK-1148..1150`), `ResourceFailure` (rescheduled with adjusted token profile, `REQ-LNK-1128`), and `ArtifactFailure` (hash/schema mismatch — rejected and quarantined from entering trusted caches, `REQ-LNK-940..945`, `REQ-LNK-1010..1017`, `REQ-LNK-1130..1131`, `REQ-LNK-1176`).

---

## 3. Parallel Per-CGU Codegen, Incremental Cache Integration & Deterministic Post-Join Merging

### `AXS-PAR-020` — Deterministic Codegen Unit (`CGU`) Partitioning & Canonical Indexing

1. **Canonical `CguId` assignment**: After frontend/middle-end semantic verification (`Verified MIR`, `INV-PIPE-002`), `compiler/parallel/codegen` partitions reachable monomorphized functions and static data items into deterministic Codegen Units (`CGU_0, CGU_1, ..., CGU_{M-1}`) (`0153 APAR-24`, `0473 §214.25–26`, `0593 §40`, `T762`).
2. **Sorting rule**: `CGU`s are ordered lexicographically by their primary `ModuleId` (`SemanticKey`) and partition ordinal, and functions/statics inside each `CGU` are sorted by canonical `SemanticKey`. Partition boundaries depend exclusively on `(DatabaseSnapshot, TargetConfig, OptProfile)`, never on `--jobs <N>` or worker count.

### `AXS-PAR-021` — Isolated Per-Worker LIR Lowering, Register Allocation, Encoding & COFF `.obj` Emission

Each ready `CGU_i` is dispatched as an independent parallel action to a worker thread (`T762`):
1. The worker runs `OptIR` passes (`SPEC-70..73`), LIR lowering, ABI lowering, instruction selection, linear-scan register allocation, post-RA peephole optimization, `x64_verify_checked` verification (`SPEC-77`), and COFF `.obj` byte encoding inside an isolated per-CGU arena.
2. Local symbol tables, section indices, and relocation tables inside `CGU_i.obj` are emitted in canonical `SemanticKey` order with `TimeDateStamp = 0` (`INV-DET-002`).
3. Any backend or object-writer limit failure emits a structured diagnostic (`AX_LINK_*` / `AX_ICE_*`) and aborts artifact publication (`REQ-CORE-2691..2692`, `ACOMPARCH-40..41`).

### `AXS-PAR-022` — Hybrid Incremental Cache + Parallel Codegen Execution

In incremental workspace builds (`SPEC-22` + `SPEC-23`, `REQ-DRV-018`, `REQ-LNK-1134..1143`, `REQ-LNK-1193..1196`, `0790 §568.4–5, §568.101–110`, `T762`):
1. For each `CGU_i`, the scheduler computes `CodegenFingerprint(CGU_i)` (`SPEC-22 AXS-INC-002`).
2. **Clean CGU (`CacheCheck -> Hit -> Verified`)**: If `.axiom-cache/objects/<fp128>.obj` exists and passes BLAKE3 checksum validation, `CGU_i` loads its cached `.obj` buffer without scheduling codegen work.
3. **Dirty CGUs (`CacheCheck -> Miss -> Ready`)**: All dirty `CGU`s are scheduled in parallel across the worker pool, and their validated `.obj` buffers are atomically published to `.axiom-cache` upon completion (`REQ-LNK-1021..1025`).

### `AXS-PAR-023` — Deterministic Post-Join Diagnostic Buffer Merging

1. **Per-worker / per-query diagnostic buffers**: Worker threads never write directly to `stderr` or lock a shared unsorted output stream (`0153 APAR-22..23`, `0593 §18–19`, `AXD-001`). Each query/action accumulates diagnostics in its private buffer bound to `MemoEntry` / `ActionResult`.
2. **Canonical post-join merge (`AXD-060`)**: At phase barriers (or upon interactive query completion), the coordinator collects diagnostics from all reachable nodes in the dependency graph, deduplicates by `(code, primary_span, message)`, and stably sorts them by `(has_primary_span, FileId, primary.start, code_registry_ordinal, canonical_semantic_key)` (`AXD-060`, `T762`, `T763`). Worker scheduling delays never alter diagnostic order.

### `AXS-PAR-024` — Canonical Linker Input Ordering, Finalization Barriers & Byte-Identical Artifact Promotion

1. **Canonical `.obj` join order**: Regardless of which worker finishes `CGU_i` first, the coordinator joins all `CGU` results and passes `[CGU_0.obj, CGU_1.obj, ..., CGU_{M-1}.obj]` (followed by external archives in CLI argument order) to `compiler/link/` in strict index order `0 .. M-1` (`0153 APAR-24`, `T762`).
2. **Finalization barriers & promotion (`REQ-LNK-1026..1029`, `REQ-LNK-1223..1229`, `0790 §568.190–196`)**: The final link barrier (`LinkBarrier`), package barrier, and signing barrier execute only after all required `CGU` actions succeed with zero error diagnostics. Artifacts transition strictly through `Produced -> Verified -> Trusted -> Published` (`REQ-LNK-1227`).

---

## 4. CLI Flags, Telemetry, Canonical Examples & E18.3 Verification Matrix

### `AXS-PAR-050` — Parallel CLI Flags, Deterministic Debug Mode & Telemetry

1. **CLI flags**:
   - `--jobs <N>` / `-j <N>`: Sets the worker thread pool size (`N >= 1`; defaults to host logical CPU count; `--jobs 1` runs single-threaded deterministic execution without spawning background worker threads). An invalid `<N>` (`0` or non-integer) emits `AX_DRIVER_USAGE` (exit code 2).
   - `--schedule-mode <mode>`: Selects `interactive | balanced | throughput | memory-bound | low-power | deterministic-debug` (`REQ-LNK-1052`, `REQ-LNK-1204..1206`). In `deterministic-debug` mode, ready queues break all ties strictly by canonical `ActionId` / `SemanticKey` order for forensic trace reproducibility (`REQ-LNK-1204..1205`).
   - `inspect --emit=parallel-trace` / `build --emit=parallel-stats`: Emits deterministic build orchestration statistics (`total_actions`, `executed`, `cached`, `speculative`, `cancelled`, `failed`, `critical_path_cost`, bottleneck classification) without leaking source secrets or altering artifact bytes (`REQ-LNK-1207..1222`, `0790 §568.174–189`).
2. **Diagnostic invariance**: Parallel execution introduces no new user-facing semantic error codes; cross-worker cycles emit the canonical `SPEC-21` cycle codes (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`), and internal duplicate-execution mismatches fail closed with `AX_ICE_INTERNAL` (`data.stage = "parallel_verify"`).

### `AXS-PAR-051` — Positive Canonical Examples

```axiom
// === File: geom.ax (ModuleId = 1) ===
module geom

pub struct Vec2 {
    pub x: i32,
    pub y: i32
}

pub fn dot(a: view<Vec2>, b: view<Vec2>) -> i32 {
    a.x * b.x + a.y * b.y
}
```

```axiom
// === File: physics.ax (ModuleId = 2) ===
module physics

use geom

pub fn kinetic_scale(v: view<geom.Vec2>, mass: i32) -> i32 {
    // Worker W_1 (checking `physics.kinetic_scale`) and Worker W_2 (checking `app.main`)
    // may concurrently request `item_signature(geom.dot)`.
    // SingleFlightLatch (AXS-PAR-010) ensures `item_signature(geom.dot)` executes once,
    // assigns ScopedDefId { module_id: 1, local_index: 1 } (AXS-PAR-004), and produces
    // byte-identical CGU_1.obj and CGU_2.obj under `--jobs 1`, `--jobs 2`, and `--jobs 8`.
    geom.dot(v, v) * mass
}
```

```axiom
// === File: app.ax (ModuleId = 3) ===
module app

use geom
use physics

pub fn main() -> i32 {
    let u = geom.Vec2 { x: 3, y: 4 }
    let e = physics.kinetic_scale(view(u), 2)
    if e == 50 {
        0
    } else {
        1
    }
}
```

### `AXS-PAR-052` — Negative Canonical Examples (Cross-Worker Cycle Detection & Deterministic Diagnostic Merge)

```axiom
// === File: mod_a.ax (FileId = 1, ModuleId = 1) ===
module mod_a

use mod_b

// Worker W_1 evaluates `const_eval(mod_a.FIRST)` -> waits on `const_eval(mod_b.SECOND)` (owned by W_2).
// Worker W_2 evaluates `const_eval(mod_b.SECOND)` -> requests `const_eval(mod_a.FIRST)` (owned by W_1).
// WaitForGraph (AXS-PAR-011) immediately detects the cross-worker cycle without deadlocking,
// rotates to canonical minimum SemanticKey `mod_a.FIRST`, and emits:
pub const FIRST: i32 = mod_b.SECOND + 1 // ERROR [AX_CTM_CYCLE]: cyclic constant evaluation: `mod_a.FIRST -> mod_b.SECOND -> mod_a.FIRST`

pub fn err_in_a() -> i32 {
    let bad_a: i32 = true // ERROR [AX_TYPE_MISMATCH]: expected `i32`, found `bool`
    bad_a
}
```

```axiom
// === File: mod_b.ax (FileId = 2, ModuleId = 2) ===
module mod_b

use mod_a

pub const SECOND: i32 = mod_a.FIRST + 1

pub fn err_in_b() -> i32 {
    // Even if Worker W_2 finishes `typeck_body(mod_b.err_in_b)` 50 ms before Worker W_1
    // finishes `typeck_body(mod_a.err_in_a)`, Post-Join Diagnostic Merging (AXS-PAR-023)
    // stably sorts diagnostics by (FileId, primary.start, code_ordinal) so `mod_a.ax`
    // errors ALWAYS appear before `mod_b.ax` errors under any `--jobs N`.
    let bad_b: bool = 42 // ERROR [AX_TYPE_MISMATCH]: expected `bool`, found `i32`
    if bad_b { 1 } else { 0 }
}
```

### `AXS-PAR-053` — E18.3 Implementation & Verification Matrix

| Task | Scope | Required Verification Target | Invariant ID |
|---|---|---|---|
| `T761` | Thread-safe immutable `CompilerDB` snapshots, `(ModuleId, LocalIndex)` IDs, sharded interner, `SingleFlightLatch` + `WaitForGraph` cycle detection, `--jobs N` work-stealing scheduler | `tests/run/parallel_scheduler` | `INV-PAR-001` |
| `T762` | Parallel per-module / per-`CGU` LIR lowering, RA, encoding & `.obj` emission, incremental cache integration, deterministic post-join diagnostic & `.obj` merging | `tests/run/parallel_codegen` | `INV-PAR-002` |
| `T763` | End-to-end E18.3 conformance: `--jobs 1` vs `2` vs `4` vs `8` byte-identical `.obj`/`.exe` & HIR/MIR/LIR dumps, randomized worker delay diagnostic ordering, parallel + incremental equivalence | `tests/conformance/p18/e18_3_parallel` | `INV-PAR-003` |

---

## Sources

- `docs/base/specs/0153 - AXIOM COMPILER KERNEL SPEC.md` (§19 Parallelism Rules, §37 `APAR-20..24`, `ACKERNEL-21`, `AINTERN-20..23`, `ADET-20..24`)
- `docs/base/tasks/0473 - BOOTSTRAP-214 — Self-Hosting, Bootstrap Trust, Reproducible Compiler & Compiler-as-Program.md` (§214.24–§214.33, `ACOMPILER-30..33`)
- `docs/base/tasks/0528 - BOOTSTRAP-269 — AXIOM COMPILER REPOSITORY ARCHITECTURE, MODULE BOUNDARIES & IMPLEMENTATION CONTRACTS.md` (§115 Parallel Determinism, §131 Semantic vs Representation, §134 `ACOMPARCH-20..60`)
- `docs/base/tasks/0530 - BOOTSTRAP-271 — AXIOM COMPILER QUERY ENGINE, INCREMENTAL COMPILATION & PARALLEL SEMANTIC DATABASE.md` (§127–§148 Parallel Query Execution & Snapshot Isolation, §163 `AQUERY-50..80`, §164)
- `docs/base/tasks/0593 - BOOTSTRAP-334 — AXIOM BUILD GRAPH EXECUTION, PARALLELISM & DISTRIBUTED COMPILATION ENGINE.md` (§1–§57, §334 Resource-Aware Parallelism & Deterministic Result Ordering)
- `docs/base/tasks/0789 - BOOTSTRAP-567 — COMPILER DISTRIBUTED BUILD 2.0 — REMOTE EXECUTION, CONTENT-ADDRESSED WORKERS, HERMETIC ACTIONS, REMOTE ARTIFACT TRANSFER, SCHEDULING & VERIFICATION.md` (§567.101–§567.200)
- `docs/base/tasks/0790 - BOOTSTRAP-568 — COMPILER BUILD ORCHESTRATOR 3.0 — DAG EXECUTION ENGINE, SPECULATIVE COMPILATION, CRITICAL-PATH SCHEDULING, RESOURCE-AWARE PARALLELISM.md` (§568.1–§568.200)
