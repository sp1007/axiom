# SPEC-25 — Canonical Pass Contracts, Proof-Carrying Transformations & Translation Validation Specification

- **Status**: draft (T768, 2026-11-03)
- **Owner**: `axiom-architect`
- **Consolidates**: `spec/SPEC-20-selfhost.md`, `spec/SPEC-70-optir-ssa-memoryssa.md` (`AXS-OPT-001..006`, `AXS-OPT-030..034`), `spec/SPEC-77-regalloc-machine-opt.md` (`AXS-RA-010..027`, `AXS-MCOPT-001..026`), `0545` (`tasks/0545`, BOOTSTRAP-286 Analysis Orchestrator & Proof Dependency Engine), `0577` (`tasks/0577`, BOOTSTRAP-318 Compiler Correctness, Translation Validation & Semantic Equivalence Engine), `0578` (`tasks/0578`, BOOTSTRAP-319 Compiler Pass Contract System & Proof-Carrying Transformations), `0793` (`tasks/0793`, BOOTSTRAP-571 Compiler Source Analysis 2.0), `0794` (`tasks/0794`, BOOTSTRAP-572 Compiler Static Analysis 3.0), `0795` (`tasks/0795`, BOOTSTRAP-573 Compiler Effect System 2.0), `0796` (`tasks/0796`, BOOTSTRAP-574 Compiler Symbolic Execution 2.0), `0797` (`tasks/0797`, BOOTSTRAP-575 Compiler Optimization Safety & Transformation Verifier 2.0), `0798` (`tasks/0798`, BOOTSTRAP-576 Compiler Optimization Pass Library 3.0), `0799` (`tasks/0799`, BOOTSTRAP-577 Compiler Register Allocation 3.0), `0800` (`tasks/0800`, BOOTSTRAP-578 Compiler Instruction Scheduling 3.0), `0801` (`tasks/0801`, BOOTSTRAP-579 Compiler Machine Code Finalization 3.0)
- **Covers**: `REQ-CORE-3105..3108`, `REQ-CORE-3192..3285`, `REQ-LNK-1634..3433`
- **Related**: `spec/SPEC-21-query-engine-semantic-db.md`, `spec/SPEC-22-incremental-compilation.md`, `spec/SPEC-23-parallel-compilation.md`, `spec/SPEC-24-artifact-format-module-interfaces.md`, `spec/SPEC-70-optir-ssa-memoryssa.md`, `spec/SPEC-77-regalloc-machine-opt.md`, `spec/diagnostics.md`, `spec/invariants.md`

## Tóm tắt

SPEC-25 định nghĩa kiến trúc hợp đồng pha biên dịch (`PassContract`), chứng chỉ biến đổi mang bằng chứng (`ProofCertificate` / `ProofProvenance`), cơ chế đóng an toàn (fail-closed) khi nghĩa vụ chứng minh là `Unknown`, và kiểm chứng dịch thuật hữu hạn (`Translation Validation`) xuyên suốt `MIR`, `OptIR`, `LIR`, cấp phát thanh ghi (`RegAlloc`) và lập lịch lệnh (`Scheduling`) cho trình biên dịch tự thân `compiler/` (E18.5):
1. **Lược đồ hợp đồng pha biên dịch & giao dịch nguyên tử (`AXS-PCT-001`..`005`)**: Mọi pha phân tích, tối ưu hóa và hạ bậc mã máy bắt buộc khai báo `PassContract` gồm mức IR (`HIR`/`MIR`/`OptIR`/`LIR`/`MachineIR`), phân tích/tiền điều kiện bắt buộc, thuộc tính ngữ nghĩa bảo toàn (`Ownership`, `Capability`, `Effects`, `PanicBehavior`, `ABI`), tập phân tích bị làm cũ (`invalidated_analyses`) và hậu điều kiện. Pha chạy theo giao dịch có khả năng hoàn tác (rollback) nguyên tử và tách biệt tuyệt đối bằng chứng ngữ nghĩa với mô hình chi phí (`CostModel`).
2. **Chứng chỉ biến đổi mang bằng chứng & vô hiệu hóa bắc cầu (`AXS-PCT-010`..`015`)**: Mọi quyết định tối ưu hóa nhạy cảm ngữ nghĩa dựa trên dàn độ chắc chắn 3 giá trị (`Proven`, `Possible`, `Unknown`) từ `Source Analysis 2.0` (`tasks/0793`), `Static Analysis 3.0` (`tasks/0794`), `Effect System 2.0` (`tasks/0795`) và `Symbolic Execution 2.0` hữu hạn không phụ thuộc SMT ngoài (`tasks/0796`). Mỗi `ProofCertificate` lưu `ProofProvenance` gắn với `RevisionId`/phiên bản IR và tự động bị vô hiệu hóa bắc cầu khi định nghĩa IR hoặc CFG cơ sở thay đổi; mọi nghĩa vụ chứng minh trả về `Possible` hoặc `Unknown` bắt buộc đóng an toàn (giữ nguyên IR đã kiểm định).
3. **Kiểm chứng dịch thuật hữu hạn (`Translation Validation`) từ MIR đến mã máy (`AXS-PCT-020`..`024`, `AXS-PCT-050`..`053`)**: Kiểm tra chứng nhân tương đương ngữ nghĩa (`TranslationWitness`) cho từng hàm qua các phép biến đổi đại số/CFG/bộ nhớ/vòng lặp (`tasks/0798`), hợp thức hóa đích & khoảng sống/khe tràn thanh ghi (`tasks/0799`), bảo toàn phụ thuộc `RAW`/`WAR`/`WAW` và rào cản `volatile`/`atomic`/`trap` khi lập lịch lệnh (`tasks/0800`), và cổng hoàn tất mã máy cuối cùng (`tasks/0801`), cùng cờ `--verify-pass-contracts`, `--validate-translations` và `inspect --emit=pass-witness`.

---

## 1. Formal Pass Contract Schema, Analysis Dependency DAG & Transactional Execution

### `AXS-PCT-001` — Mandatory Pass Contracts & Semantic Authority Hierarchy

1. **Verifiable contract per pass (`REQ-CORE-3105..3108`, `tasks/0577 §318.1–2`, `tasks/0578 §319.1–2`, `tasks/0797 §575.1–2`)**: Axiom does not rely on an external theorem prover to certify the compiler monolithically (`REQ-CORE-3105`). Instead, no compiler transformation is permitted to run as an unconstrained IR mutation (`REQ-CORE-3108`): every semantic lowering, optimization, and backend machine pass MUST register a machine-readable `PassContract` and adhere to semantic equivalence verification (`REQ-CORE-3106`, `REQ-CORE-3107`).
2. **Authority hierarchy (`tasks/0577 §318.2 CORR-PRINCIPLE-01..03`, `tasks/0578 APASS-40`)**: Language semantics flow strictly top-down: `Canonical Spec` -> `Verified MIR Reference Semantics` -> `PassContract` -> `Pass & Translation Verifier` -> `Optimization / Lowering`. An optimization or backend pass SHALL NEVER define or alter observable program semantics (`ObservableBehavior(before) == ObservableBehavior(after)`).

### `AXS-PCT-002` — Canonical `PassContract` Descriptor Schema

Every registered pass in `compiler/` declares a static `PassContract` descriptor (`REQ-CORE-3283..3285`, `REQ-LNK-2434..2460`, `tasks/0545 §18`, `tasks/0577 §318.5`, `tasks/0578 §319.2`, `tasks/0797 §575.2–10`):

```axiom
enum IrLevel {
    Hir,
    Mir,
    OptIr,
    AbiMir,
    Lir,
    MachineIr,
    FinalMachineIr
}

enum AnalysisKind {
    Cfg,
    Dominators,
    PostDominators,
    DefUse,
    Liveness,
    Reachability,
    SsaForm,
    MemorySsa,
    OwnershipSummary,
    CapabilityDisjointness,
    AliasAnalysis,
    EscapeAnalysis,
    EffectSummary,
    RangeSymbolic,
    LoopStructure,
    CallGraphScc,
    LiveIntervals,
    ScheduleDepGraph,
    FrameLayout
}

enum SemanticProperty {
    WellTyped,
    OwnershipAndMove,
    CapabilityExclusivity,
    DeterministicDrop,
    ObservableMemory,
    ObservableEffects,
    CheckedOverflowAndTraps,
    SignedUnsignedSemantics,
    Ieee754FloatSemantics,
    VolatileOrdering,
    AtomicOrderingAndSync,
    AsyncSuspensionState,
    AbiCallingConvention,
    StackFrameAndUnwind,
    ConstantTimeAndSecret
}

enum ValidationStrategy {
    StructuralVerifier,
    LocalEquivalenceWitness,
    SymbolicDomainCheck,
    LiveRangeSpillWitness,
    ScheduleDagWitness,
    DifferentialOracle
}

enum PassFailurePolicy {
    RollbackAndSkip,
    AbortCompilationIce
}

struct PassContract {
    pass_id: u32,
    pass_name: Str,
    pass_version: u16,
    input_ir: IrLevel,
    output_ir: IrLevel,
    required_analyses: u32,         // Bitmask of AnalysisKind preconditions
    required_propositions: u32,     // Bitmask of PropositionKind proof obligations
    produced_analyses: u32,         // Bitmask of AnalysisKind established by pass
    preserved_analyses: u32,        // Bitmask of AnalysisKind guaranteed unchanged
    invalidated_analyses: u32,      // Bitmask of AnalysisKind dirtied on mutation
    preserved_properties: u32,      // Bitmask of SemanticProperty invariants (REQ-CORE-3285)
    postconditions: u32,            // Bitmask of post-pass structural/semantic predicates (REQ-CORE-3284)
    validation_strategy: ValidationStrategy,
    failure_policy: PassFailurePolicy
}
```

1. **Required IR level (`REQ-CORE-3283`, `tasks/0797 §575.4`)**: A pass executes only on the exact `input_ir` and produces `output_ir` declared in its `PassContract`.
2. **Preserved semantic properties & postconditions (`REQ-CORE-3284..3285`, `tasks/0797 §575.6–7`)**: Every intra-level optimization pass MUST preserve `WellTyped`, `OwnershipAndMove`, `CapabilityExclusivity`, `DeterministicDrop`, `ObservableMemory`, `ObservableEffects`, `CheckedOverflowAndTraps`, `VolatileOrdering`, `AtomicOrderingAndSync`, and `AbiCallingConvention`, and must satisfy all declared `postconditions` upon completion.

### `AXS-PCT-003` — Analysis Orchestrator DAG, Preserved Analyses & Automatic Invalidation

1. **Demand-driven Analysis Orchestrator (`tasks/0545 §7–12`, `tasks/0578 §319.14–16`, `SPEC-70 AXS-OPT-005`)**: Analyses are never invoked through ad-hoc cyclic calls inside individual passes. Before running pass `P`, the pass manager inspects `P.required_analyses` and computes any missing or `Stale` analyses in topological dependency order over `CompilerDB` (`SPEC-21`).
2. **No hidden invalidation (`tasks/0578 §319.6–7, APASS-26, APASS-31, APASS-34`, `tasks/0797 §575.8–10`)**:
   - When a pass mutates at least one instruction, block, or operand (`PassModified == true`), every analysis not explicitly bit-masked in `preserved_analyses` (and every analysis in `invalidated_analyses`) is immediately marked `Stale`.
   - Under `--verify-pass-contracts` (or `--verify-each`), the verifier recomputes every analysis claimed in `preserved_analyses` from scratch after the pass finishes and checks exact structural equality against the cached analysis state (`APASS-31`). Any discrepancy is a pass contract violation.

### `AXS-PCT-004` — Transactional Pass Execution, Atomic Commit & Clean Rollback

1. **Snapshot-and-commit transaction (`REQ-LNK-2456..2485`, `REQ-LNK-2633`, `tasks/0545 AOPTGATE-36..38`, `tasks/0578 §319.8–9, APASS-27..28`, `tasks/0797 §575.25–40, §575.200`)**:
   - Before a pass mutates a function body (`MirBody`, `OptBody`, `LirBody`, or `X64MIBody`), the pass framework records a lightweight structural checkpoint `(ir_revision, snapshot_handle)`.
   - A candidate transformation commits atomically if and only if: (a) all `required_propositions` hold with `Certainty.Proven`, (b) postcondition predicates (`postconditions`) succeed, and (c) the required local/global verifier and translation witness check succeed.
   - If a candidate rewrite lacks a required proof (`Certainty.Possible` or `Certainty.Unknown`) or exceeds its cost/step budget, the transaction rolls back cleanly to the pre-transform snapshot (`APASS-28`), leaving zero half-mutated instructions, orphaned SSA values, or stale dominance/liveness records.

### `AXS-PCT-005` — Semantic Firewall: Separation of Semantic Proofs from Profitability Facts

1. **Disjoint domains (`tasks/0578 §319.13, §319.20, APASS-29..32`, `tasks/0798 §576.199`, `tasks/0800 §578.199`)**: Compiler facts are partitioned into **Semantic Facts** (ownership, capability disjointness, alias proofs, effect summaries, range bounds, dominance, liveness) and **Performance / Profitability Facts** (`CostModel` latency/throughput/code-size estimates, loop trip weights, PGO execution counts, register-pressure heuristics).
2. **Firewall rule**: Performance facts (`Observed` PGO profiles, branch probability hints, cost estimates) govern only whether a *already-proven-legal* transformation is profitable (`SPEC-75 AXS-PGO-002`). A profitability heuristic or AI suggestion (`REQ-CORE-3277`, `tasks/0578 §319.29, APASS-39`) SHALL NEVER fabricate a `Proven` semantic certificate or override a failed precondition.

---

## 2. Proof-Carrying Transformation Certificates, Certainty Lattice & Provenance Invalidation

### `AXS-PCT-010` — Three-Valued Static Certainty Lattice (`Proven` / `Possible` / `Unknown`) & Fail-Closed Gate

1. **Three-valued certainty lattice (`REQ-CORE-3193..3194`, `REQ-CORE-3263`, `REQ-CORE-3276`, `REQ-LNK-1834..2033`, `tasks/0545 §2–3`, `tasks/0578 §319.3`, `tasks/0794 §572.1–200`, `tasks/0796 §574.1, §574.200`)**: Every semantic, dataflow, effect, or symbolic query consumed by a pass evaluates to one of three distinct certainty grades:

```axiom
enum Certainty {
    Proven,     // Holds on all reachable execution paths under canonical semantics
    Possible,   // Holds on some path, or negation is feasible (`Disproven` for opposite)
    Unknown     // Budget exhausted, opaque FFI/indirect call, volatile, or open-world boundary
}
```

2. **Mandatory fail-closed fallback (`REQ-CORE-3194`, `REQ-CORE-3263`, `REQ-CORE-3276`, `REQ-LNK-2033`, `REQ-LNK-2633`, `tasks/0545 AOPTGATE-22..23`, `tasks/0794 §572.192, §572.200`, `tasks/0797 §575.1, §575.200`)**:
   - `Unknown` and `Possible` are strictly distinct from `Proven`. Analysis step-budget exhaustion, missing cross-module metadata, dynamic trait/function-pointer dispatch, external FFI, floating-point `NaN`/`-0.0` uncertainty, or open-world boundaries MUST degrade certainty to `Possible` or `Unknown` (`REQ-CORE-3194`), never to a fabricated `Proven`.
   - **Fail-closed optimization rule (`REQ-CORE-3263`)**: Any transformation whose required proof obligation evaluates to `Certainty.Possible` or `Certainty.Unknown` MUST be rejected (rolled back cleanly to the unoptimized IR) without emitting a spurious user compile error (`REQ-CORE-3276`).
   - **Sound static analysis & IDE ergonomics (`REQ-CORE-3193`, `REQ-CORE-3195`, `tasks/0794 §572.191–197`)**: Known violations in sound language-mandated checks (definite initialization, move/ownership, capability exclusivity) are always caught (`REQ-CORE-3193`), whereas the standard static-analysis profile remains lightweight for incremental IDE responsiveness (`REQ-CORE-3195`) and never imposes a Rust-style surface borrow/lifetime annotation burden (`tasks/0794 §572.196`).

### `AXS-PCT-011` — Proof Certificates (`ProofCertificate`), `ProofProvenance` & Transitive Invalidation

Every semantic fact that authorizes an IR transformation is packaged as a versioned `ProofCertificate` (`REQ-CORE-3248`, `REQ-CORE-3264..3265`, `REQ-CORE-3278`, `tasks/0545 §3–6, §14–16, APROOF-59..65`, `tasks/0578 §319.3–5, §319.17–19, APASS-24..26, APASS-33..34`):

```axiom
enum PropositionKind {
    NoAlias,            // Two memory places/regions do not overlap
    MustAlias,          // Two memory places refer to the exact same byte range
    InBounds,           // Index `idx < len` proven for slice/array access
    NonZero,            // Divisor or pointer proven `!= 0`
    NoOverflow,         // Checked integer operation proven within `[MIN, MAX]`
    ShiftInRange,       // Shift amount proven `< bit_width`
    NonNull,            // Pointer or capability proven non-null
    Initialized,        // Place proven definitely initialized on all reaching paths
    UniqueOwner,        // Value has a single unaliased owner
    DoesNotEscape,      // Allocation does not escape current frame/scope
    PureCall,           // Callee has `EffectMask.PURE` and terminates deterministically
    NoPanic,            // Operation/callee proven never to panic or trap
    DeadStore,          // Store overwritten or dead before any observable read/drop
    ReachableEdge,      // CFG edge/block reachability or unreachability
    ValidLiveRange,     // Physical register assignment free of live interference
    ValidScheduleOrder  // Instruction schedule preserves RAW/WAR/WAW & memory barriers
}

enum FactOrigin {
    SemanticVerifier,   // Ownership / Capability / Type / Drop verifier
    DataflowEngine,     // Source Analysis 2.0 (CFG, Dominance, DefUse, Liveness)
    EffectEngine,       // Effect System 2.0 (interprocedural SCC summary)
    SymbolicEngine,     // Bounded Symbolic Execution 2.0 (Range, Bitmask, Congruence)
    TrustedBoundary     // Explicit `unsafe` / FFI / intrinsic contract with audit trail
}

struct ProofProvenance {
    proof_id: u32,
    origin: FactOrigin,
    analysis_id: AnalysisKind,
    rule_id: u32,
    subject_fn: u32,
    subject_inst: u32,
    ir_revision: u32,               // Function IR mutation counter when proven
    snapshot_revision: u64,         // CompilerDB RevisionId (SPEC-21)
    parent_proof_mask: u64          // Bitmask/list of upstream ProofId dependencies
}

struct ProofCertificate {
    proposition: PropositionKind,
    certainty: Certainty,
    provenance: ProofProvenance,
    fingerprint: Fingerprint128,    // Canonical content digest for proof caching (REQ-CORE-3265)
    valid: bool
}
```

1. **Automatic invalidation on IR mutation (`REQ-CORE-3248`, `REQ-CORE-3264`, `tasks/0545 §15 APROOF-59`, `tasks/0578 §319.5, §319.19, APASS-26, APASS-34`)**:
   - Every `MirBody`, `OptBody`, `LirBody`, and `X64MIBody` maintains a monotonic `ir_revision: u32` incremented on any instruction, operand, memory def, or CFG edge mutation.
   - A `ProofCertificate` is valid for consumption only if `cert.valid == true`, `cert.certainty == Certainty.Proven`, and `cert.provenance.ir_revision == body.ir_revision` (or the mutating pass explicitly re-validated and advanced `cert.provenance.ir_revision`).
   - Invalidating any root fact or mutating its underlying SSA/IR definition transitively marks all dependent `ProofCertificate` nodes in the proof dependency DAG as `valid = false` (`REQ-CORE-3264`). Stale certificates are never silently reused (`APASS-34`).
2. **Canonical proof caching (`REQ-CORE-3265`, `REQ-CORE-3278`, `tasks/0578 APASS-33`)**: Equivalent proof obligations are canonicalized before hashing (`REQ-CORE-3265`), and proof cache hits vs misses never alter semantic or codegen outcomes (`REQ-CORE-3278`).

### `AXS-PCT-012` — Shared Source Dataflow Authority (`Source Analysis 2.0`)

`compiler/` maintains a single canonical CFG and dataflow infrastructure (`REQ-LNK-1634..1833`, `tasks/0793 §571.1–200`) shared across semantic checking, diagnostics, optimization, register allocation, and IDE queries (`tasks/0793 §571.199–200`):
1. **Deterministic graph & lattice convergence**: Forward and backward dataflow analyses (reachability, dominators, postdominators, def-use chains, constant propagation, definite initialization, and liveness) iterate in canonical Reverse Post-Order (`RPO` / post-order) over finite-height monotone lattices, converging to the exact same fixed point regardless of worker thread count (`tasks/0793 §571.200`).
2. **Bounded scaling on deep CFGs (`tasks/0793 §571.195–197`)**: Dataflow evaluation scales near-linearly from 10 to `10,000+` basic blocks without path explosion.

### `AXS-PCT-013` — Canonical Effect System 2.0 (`EffectSummary` & Multi-Category Lattices)

`compiler/` computes a canonical `EffectSummary` for every function, closure, and instruction (`REQ-CORE-3196..3235`, `REQ-LNK-2034..2233`, `tasks/0795 §573.1–200`):
1. **Per-category effect lattices & `Unknown` preservation (`REQ-CORE-3196..3197`, `REQ-CORE-3215`, `tasks/0795 §573.14, §573.135`)**: Effects are factored into independent category lattices (`Memory: None | Read | Write | ReadWrite | Unknown`, `Resource: None | Alloc | Free | Move | Drop`, `Control: Total | MayPanic | Diverges`, `Concurrency: Local | Atomic | Lock | Block | Spawn`, `External: None | Io | VolatileMmio | Entropy | Ffi | Unknown`). Categories do not share a single linear total order (`REQ-CORE-3196`), and `Unknown` (or unknown hidden state) NEVER silently downgrades to `Pure` or a weaker concrete effect (`REQ-CORE-3197`, `REQ-CORE-3215`).
2. **Entropy, profile logging, cleanup, blocking, borrows & callbacks (`REQ-CORE-3199..3206`, `tasks/0795 §573.36–92`)**:
   - Hardware/OS entropy (`RDRAND`, OS RNG, wall clock) is classified as external/nondeterministic (`REQ-CORE-3199`); debug-only logging is modeled per active compilation profile (`REQ-CORE-3200`).
   - Normal and unwind `Drop` cleanup paths contribute their effects to the enclosing function's `EffectSummary` (`REQ-CORE-3201`); blocking operations carry the `Block` effect (`REQ-CORE-3202`); escaping borrows record their lifetime/resource effect in the summary (`REQ-CORE-3203`).
   - Callbacks passed as arguments must satisfy the parameter's effect bound (`REQ-CORE-3204`), higher-order functions union the effects of invoked callbacks into their own summary (`REQ-CORE-3205`), and dead-code elimination NEVER removes an impure call solely because its return value is unused (`REQ-CORE-3206`).
3. **Optional annotations, comptime/device rules & monotonic SCC inference (`REQ-CORE-3198`, `REQ-CORE-3207..3225`, `tasks/0795 §573.24, §573.108–172`)**:
   - Surface effect annotations are optional in ordinary Axiom code (`REQ-CORE-3210`). A caller never assumes a callee is pure merely because the caller is marked pure (`REQ-CORE-3207`).
   - Compile-time file reads (`REQ-CORE-3212`) and nondeterministic comptime inputs (`REQ-CORE-3213`) must be declared build inputs or rejected (`SPEC-60`), and functions with observable state effects are never memoized across calls (`REQ-CORE-3214`). MMIO accesses and device barriers carry explicit `VolatileMmio` and device-sync effects (`REQ-CORE-3216..3217`).
   - Interprocedural effect inference over `CallGraph` SCCs is strictly monotonic without oscillation (`REQ-CORE-3218..3219`), invariant to traversal order and `--jobs N` parallelism (`REQ-CORE-3220..3221`), invalidates callers when a callee's `EffectSummary` changes (`REQ-CORE-3198`), tags partial summaries as `Incomplete` (`REQ-CORE-3224`), separates target-specific from target-neutral summaries (`REQ-CORE-3223`), and binds cache keys to schema/analyzer versions while rejecting or migrating older `.axmi`/`.axsem` summaries (`REQ-CORE-3222`, `REQ-CORE-3225`). AI explanations read only the canonical `EffectSummary` (`REQ-CORE-3211`).

### `AXS-PCT-014` — Bounded Symbolic Execution 2.0 (Abstract Domains & Zero External SMT Dependency)

The symbolic proof engine (`REQ-CORE-3236..3282`, `REQ-LNK-2234..2433`, `tasks/0796 §574.1–200`) refines dataflow and effect facts using compact abstract states (`Constant`, `Range [lo, hi]`, `Nullability`, `Bitmask known_zeros/known_ones`, `Congruence stride/offset`) and path constraints (`==`, `!=`, `<`, `<=`, boolean guards):
1. **No external SMT solver dependency & bounded hot-path cost (`REQ-CORE-3258..3262`, `REQ-CORE-3266`, `REQ-CORE-3279..3282`, `tasks/0796 §574.92–108, §574.134, §574.186–196`)**:
   - The core native compiler SHALL NOT depend on any external SMT solver binary or library (`REQ-CORE-3259`); all domain propagation and contradiction detection (`REQ-CORE-3258`) run deterministically in-process with compact abstract states (`REQ-CORE-3266`) under a strict step/branch exploration budget (`REQ-CORE-3262`) bound to the exact input snapshot (`REQ-CORE-3260`, `REQ-CORE-3279`).
   - Common range/non-zero/bounds proofs execute in the compiler hot path with low overhead (`REQ-CORE-3281`) and never slow down baseline compilation (`REQ-CORE-3282`). Unconcretized abstract counterexamples are explicitly tagged as abstract (`REQ-CORE-3261`).
2. **Semantic fidelity across arithmetic, pointers, strings, async & external state (`REQ-CORE-3249..3257`, `REQ-CORE-3267..3275`, `tasks/0796 §574.48–73, §574.141–168`)**:
   - Division/remainder requires `NonZero` (`REQ-CORE-3249..3250`: an `Unknown` denominator is never claimed safe); bit shifts require `ShiftInRange` (`0 <= sh < width`, `REQ-CORE-3251`); integer algebraic identities respect checked vs wrapping overflow semantics (`REQ-CORE-3267`); signed vs unsigned comparisons preserve exact bit-width and sign rules (`REQ-CORE-3268`).
   - Raw pointer reasoning is conservative (`REQ-CORE-3252`) and preserves strict pointer provenance (`REQ-CORE-3253`); `volatile` loads/stores are never symbolically folded (`REQ-CORE-3254`); `atomic` operations preserve synchronization orderings and are never simplified to ordinary memory accesses (`REQ-CORE-3255`, `REQ-CORE-3272`); unknown calls are treated conservatively (`REQ-CORE-3256`) while distinguishing preconditions from postconditions (`REQ-CORE-3257`).
   - UTF-8 byte length (`len_bytes`) is never conflated with Unicode scalar count (`REQ-CORE-3269`); `.await` / generator `yield` suspension boundaries and cancellation paths preserve live resource/drop facts (`REQ-CORE-3270..3271`); time, RNG, OS state, and uncaptured environment variables remain symbolic `Unknown` and are never constant-folded (`REQ-CORE-3273..3275`).

### `AXS-PCT-015` — Trusted Boundary Assumptions & Auditability

Explicit effect or aliasing contracts on `unsafe` blocks, FFI declarations, or target intrinsics may be accepted by policy as `FactOrigin.TrustedBoundary` (`REQ-CORE-3208..3209`, `tasks/0545 §3, §30`, `tasks/0795 §573.109–111`), but MUST retain explicit `TrustedBoundary` provenance in `ProofProvenance` and in `.axmi` / witness dumps. Any security or static-analysis suppression attribute MUST be explicit in source and auditable in compilation reports (`REQ-CORE-3192`, `tasks/0794 §572.183`).

---

## 3. Bounded Translation Validation Across MIR, `OptIR`, LIR, Register Allocation & Scheduling

### `AXS-PCT-020` — Observable Semantic Equivalence Hierarchy & Per-Function `TranslationWitness`

1. **Five-tier semantic equivalence hierarchy (`REQ-CORE-3105..3106`, `tasks/0577 §318.3, §318.6–9, ACORR-33..40`, `tasks/0797 §575.11–12`)**:
   - `Level 0 (Structural)`: Isomorphic IR graph structure (debug/canonicalization check).
   - `Level 1 (Value)`: Identical return values and SSA expression outcomes for all valid inputs.
   - `Level 2 (Memory & Resource)`: Identical observable memory stores, ownership state, initialization, and deterministic `Drop` sequence.
   - `Level 3 (Effect & Trap)`: Identical ordered sequence of I/O, checked-arithmetic/bounds traps (`panic`), `volatile` accesses, `atomic` synchronization operations, and FFI calls.
   - `Level 4 (Observable Semantic Equivalence)`: Conjunction of Levels 1–3; the mandatory correctness criterion across all Axiom passes.
2. **Per-function `TranslationWitness` (`tasks/0577 §318.6–12`, `T770`)**: Under `--validate-translations` (and `inspect --emit=pass-witness`), `compiler/verify/translation_val` emits and checks a bounded `TranslationWitness` for each transformed function:

```axiom
struct TranslationWitness {
    pass_id: u32,
    fn_id: u32,
    input_ir: IrLevel,
    output_ir: IrLevel,
    pre_fingerprint: Fingerprint128,
    post_fingerprint: Fingerprint128,
    consumed_proofs: u32,           // Count of verified ProofCertificates consumed
    preserved_props: u32,           // Verified SemanticProperty bitmask
    equivalence_verified: bool,
    failure_reason: Str             // Empty when equivalence_verified == true
}
```

### `AXS-PCT-021` — Middle-End Translation Validation (`MIR` ↔ `OptIR`, Scalar, Memory, CFG & Loop Passes)

For middle-end passes in `Optimization Pass Library 3.0` (`REQ-CORE-3280`, `REQ-LNK-2434..2833`, `tasks/0577 §318.10–12`, `tasks/0797 §575.17–120`, `tasks/0798 §576.1–200`, `T770`):
1. **Scalar & algebraic rewrites**: The validator checks that constant folding, algebraic simplification, strength reduction, SCCP, and GVN preserve exact bit-width, signed/unsigned comparison polarity (`REQ-CORE-3268`), IEEE-754 `NaN`/`-0.0` rules, and checked-arithmetic trap conditions (`NoOverflow`, `NonZero`, `ShiftInRange`). Dropping a checked-overflow or bounds trap without a `Certainty.Proven` certificate is rejected immediately.
2. **CFG canonicalization & unreachable block removal**: Removing a branch edge or basic block requires a verified `ReachableEdge` / constant-condition proof; dominance and `phi` / `MemoryPhi` inputs at remaining join blocks must remain complete and well-typed.
3. **Memory & loop transformations**: Dead-store elimination (`DeadStore`), load forwarding (`MustAlias` / `NoAlias`), SROA, LICM, and Bounds-Check Elimination (`InBounds`) require valid `ProofCertificate` entries and preserve all `volatile`, `atomic`, `Drop`, and capability barriers (`SPEC-70`..`SPEC-73`).

### `AXS-PCT-022` — Target Legalization & Register Allocation Witness Validation (`Register Allocation 3.0`)

Across `OptIR`/`MIR` → `LIR` → `MachineIR` target legalization and register allocation (`REQ-LNK-2834..3033`, `tasks/0577 §318.15–17`, `tasks/0799 §577.1–200`, `SPEC-77 AXS-RA-010..027`, `T770`):
1. **Target legalization equivalence (`tasks/0799 §577.1–25`)**: Narrow/wide integer promotion, 128-bit register-pair splitting (`SPEC-40`), and vector legalization (`SPEC-43`) must preserve exact value and trap semantics.
2. **Register allocation & spill/reload witness (`tasks/0577 §318.16`, `tasks/0799 §577.30–199`)**: Regardless of allocator policy (`Fast`, `Balanced`, `Aggressive`, `Size`), the post-RA witness checker verifies that:
   - Zero virtual registers remain (`AXS-PCT-024`);
   - No two simultaneously live virtual intervals share an overlapping physical register unit (`RAX`/`EAX`/`AX`/`AL`, `XMMi`/`YMMi`) unless coalesced from a move with identical value provenance;
   - Every spilled definition is paired with a dominating spill store to its dedicated stack frame slot before any reload, and spill slots never alias user-addressable stack locals or `volatile`/`MMIO` memory (`tasks/0799 §577.195–197`);
   - Fixed-register ISA constraints (`RCX` for variable shifts, `RAX:RDX` for `div`/`idiv`/`mul`), caller-saved `call` clobbers, and callee-saved register save/restore contracts match `TargetDesc`.

### `AXS-PCT-023` — Instruction Scheduling Dependency & Barrier Witness Validation (`Instruction Scheduling 3.0`)

For pre-RA and post-RA instruction scheduling (`REQ-LNK-3034..3233`, `tasks/0800 §578.1–200`, `SPEC-77 AXS-MCOPT-005`, `T770`):
1. **Dependency DAG preservation**: Every scheduled basic block or trace (`Fast`, `Balanced`, `Aggressive`, `Size`, `Debug` policies; `tasks/0800 §578.198`) is validated against its pre-schedule `ScheduleDepGraph` to confirm that all true data (`RAW`), anti (`WAR`), and output (`WAW`) dependencies on GPR/XMM/vector registers, stack slots, and `EFLAGS` condition codes are topological sub-orders of the emitted schedule.
2. **Memory, volatile, atomic & trap barriers (`tasks/0800 §578.40–95, §578.199`)**: Loads and stores that are not proven `NoAlias`, `volatile` / `MMIO` accesses, `atomic` instructions, fences, `call` instructions, and potentially trapping instructions (`Assert`, `idiv`, `div`) act as strict ordering barriers; reordering across a barrier fails translation validation. Unknown hardware latency/port behavior falls back to the conservative original order (`tasks/0800 §578.197`).

### `AXS-PCT-024` — Machine Code Finalization Gate (`Final Machine IR 3.0`)

Before `Machine Encoder` emits bytes (`REQ-LNK-3234..3433`, `tasks/0801 §579.1–200`, `SPEC-77`), the finalization gate verifies the cross-pass pipeline `allocated -> scheduled -> framed -> unwindable -> security-valid -> encodable` (`tasks/0801 §579.196–199`):
1. **Complete physical resolution (`tasks/0801 §579.133–142`)**: Zero virtual registers, zero unresolved abstract stack slots, 16-byte Win64 call-site `RSP` alignment, deterministic slot & callee-save ordering (`tasks/0801 §579.173–176`), stack probes (`__chkstk`) on frames `>= 4096` bytes (`ADR-0003`), and preserved `Secret<T>` zeroization barriers (`tasks/0801 §579.98–101`).
2. **Unwind/CFI & security profile reproducibility (`REQ-LNK-3383..3384`, `tasks/0801 §579.69–75, §579.148–151`)**: Canonical `.pdata`/`.xdata` unwind records match the exact prologue/epilogue instructions, and identical inputs + security profile produce byte-identical `FinalMachineIr`.

---

## 4. CLI Flags, Fail-Closed vs Verification Diagnostics, Canonical Examples & Conformance Matrix

### `AXS-PCT-050` — CLI Verification Flags & Diagnostic Contract

1. **CLI interface (`T769`, `T770`, `T771`)**:
   - `axiom build --verify-pass-contracts` (or `axiom check/run --verify-pass-contracts`): enables strict pre/postcondition, preserved-analysis recomputation, and `ProofCertificate` revision verification before and after every compiler pass.
   - `axiom build --validate-translations`: runs the bounded `TranslationWitness` equivalence checker across MIR, `OptIR`, LIR, register allocation, instruction scheduling, and machine finalization passes.
   - `axiom inspect --emit=pass-witness <file>`: outputs deterministic machine-readable `PassContract`, `ProofCertificate` provenance, and `TranslationWitness` verification records in canonical pass execution order.
2. **Diagnostic vs fail-closed behavior (`spec/diagnostics.md` `AXD-042`)**:
   - An unproven optimization precondition (`Certainty.Possible` or `Certainty.Unknown`) is **not** a user error or compiler bug: the pass rolls back its candidate transform cleanly (`AXS-PCT-004`, `AXS-PCT-010`) and emits zero diagnostics.
   - If a pass commits a transformation that violates its `PassContract` postconditions, mutates an undeclared property, consumes an invalidated `ProofCertificate`, or fails `TranslationWitness` validation (e.g., dropped overflow trap, clobbered live register, or reordered `volatile` load), the verifier aborts compilation before object emission with `AX_ICE_MIR_VERIFY` or `AX_ICE_INTERNAL` (`data.stage = "pass_contract"` or `"translation_val"`, `data.pass_id`, `data.detail`; exit code 3).

### `AXS-PCT-051` — Positive Canonical Examples (Proof-Authorized Transform vs Fail-Closed `Unknown` Rollback)

```axiom
// Command: axiom run --verify-pass-contracts --validate-translations -O2 slice_sum.ax
module slice_sum

// 1. Proven in-bounds & non-aliasing via `view<[i32]>` capability + loop guard:
//    `SymbolicEngine` issues `ProofCertificate { proposition: PropositionKind.InBounds, certainty: Certainty.Proven }`
//    and `CapabilityDisjointness` issues `PropositionKind.NoAlias` (`Certainty.Proven`).
//    `opt.bce` and `opt.licm` consume these certificates; `TranslationWitness` verifies equivalence.
pub fn sum_prefix(xs: view<[i32]>, limit: usize) -> i32 {
    let mut acc: i32 = 0
    let n = if limit < xs.len() { limit } else { xs.len() }
    let mut i: usize = 0
    while i < n {
        acc = acc.wrapping_add(xs[i])
        i = i + 1
    }
    acc
}

// 2. Unproven divisor (`Certainty.Unknown` for `d != 0`):
//    `opt.licm` / `opt.dce` requests `PropositionKind.NonZero` and `PropositionKind.NoPanic`.
//    Because `d` is an unconstrained runtime parameter (`Certainty.Unknown`), the pass fails closed,
//    rolls back speculative hoisting, and preserves the exact division-by-zero trap in place.
pub fn safe_ratio(a: i32, d: i32, run_div: bool) -> i32 {
    if run_div {
        a / d
    } else {
        0
    }
}

pub fn main() -> i32 {
    let data: [4]i32 = [10, 20, 30, 40]
    let total = sum_prefix(view(data), 3)
    let fallback = safe_ratio(100, 0, false)
    if total == 60 && fallback == 0 { 0 } else { 1 }
}
```

### `AXS-PCT-052` — Negative Canonical Examples (Synthetic Pass Bugs Caught by Contract & Witness Verifier)

```axiom
// === Negative Case 1: Consuming a stale `ProofCertificate` after IR mutation (`T769`) ===
// Pass A proves `InBounds(idx < 4)` at `ir_revision = 1`.
// Pass B mutates `idx = idx + 1` (`ir_revision` advances to `2`), automatically invalidating
// dependent certificates (`cert.valid = false`).
// If a faulty pass attempts to consume the stale `ir_revision = 1` certificate under `--verify-pass-contracts`:
// ERROR [AX_ICE_INTERNAL]: pass `opt.bce` consumed invalidated ProofCertificate (cert_rev=1, ir_rev=2)

// === Negative Case 2: Dropped checked-overflow trap in scalar rewrite (`T770`) ===
// Pre-pass MIR has checked `a + b` (`SemanticProperty.CheckedOverflowAndTraps`).
// If a faulty rewrite lowers `a + b` to unchecked wrapping addition without `PropositionKind.NoOverflow == Proven`:
// ERROR [AX_ICE_MIR_VERIFY]: translation validation failed in pass `opt.instcombine`: dropped overflow trap

// === Negative Case 3: Clobbered live register or reordered `volatile` load in backend (`T770`) ===
// If register allocation assigns overlapping live intervals `v1` and `v2` both to `RAX`, or instruction
// scheduling reorders `volatile_load(reg_a)` across `volatile_store(reg_b)`:
// ERROR [AX_ICE_INTERNAL]: translation validation failed in pass `x64.schedule`: volatile barrier order violated
```

### `AXS-PCT-053` — E18.5 Implementation & Verification Matrix

| Task | Scope | Required Verification Target | Invariant ID |
|---|---|---|---|
| `T769` | `PassContract` registry, `ProofCertificate` / `ProofProvenance` attachment & automatic invalidation on IR mutation, three-valued `Certainty` (`Proven`/`Possible`/`Unknown`), canonical effect & symbolic domain proofs, and fail-closed rollback gate in `compiler/verify/pass_contracts` (`--verify-pass-contracts`) | `tests/run/pass_contracts` | `INV-PCT-001` |
| `T770` | Per-function bounded `TranslationWitness` checker in `compiler/verify/translation_val` across MIR, `OptIR`, LIR, register allocation live-range/spill equivalence, and instruction scheduling dependency/barrier preservation (`--validate-translations`, `inspect --emit=pass-witness`) | `tests/run/translation_val` | `INV-PCT-002` |
| `T771` | End-to-end E18.5 conformance: `--verify-pass-contracts` and `--validate-translations` at `-O0`, `-O1`, and `-O2`, preservation of overflow, signed/unsigned comparison, `Drop`, atomic, `volatile`, and capability invariants, and differential `--interp` vs native parity (`0 WEAK-NATIVE`) | `tests/conformance/p18/e18_5_pass_contracts` | `INV-PCT-003` |

---

## Sources

- `spec/SPEC-20-selfhost.md`, `spec/SPEC-70-optir-ssa-memoryssa.md` (`AXS-OPT-001..006`, `AXS-OPT-030..034`), `spec/SPEC-77-regalloc-machine-opt.md` (`AXS-RA-010..027`, `AXS-MCOPT-001..026`)
- `docs/base/tasks/0545 - BOOTSTRAP-286 — AXIOM ANALYSIS ORCHESTRATOR & PROOF DEPENDENCY ENGINE.md` (§1–§42, `APROOF-20..65`, `AOPTGATE-20..40`)
- `docs/base/tasks/0577 - BOOTSTRAP-318 — AXIOM COMPILER CORRECTNESS, TRANSLATION VALIDATION & SEMANTIC EQUIVALENCE ENGINE.md` (§318.1–§318.33, `ACORR-01..40`, `REQ-CORE-3105..3106`)
- `docs/base/tasks/0578 - BOOTSTRAP-319 — AXIOM COMPILER PASS CONTRACT SYSTEM & PROOF-CARRYING TRANSFORMATIONS.md` (§319.1–§319.34, `APASS-01..40`, `REQ-CORE-3107..3108`)
- `docs/base/tasks/0793 - BOOTSTRAP-571 — COMPILER SOURCE ANALYSIS 2.0.md` (§571.1–§571.200, `REQ-LNK-1634..1833`)
- `docs/base/tasks/0794 - BOOTSTRAP-572 — COMPILER STATIC ANALYSIS 3.0.md` (§572.1–§572.200, `REQ-CORE-3192..3195`, `REQ-LNK-1834..2033`)
- `docs/base/tasks/0795 - BOOTSTRAP-573 — COMPILER EFFECT SYSTEM 2.0.md` (§573.1–§573.200, `REQ-CORE-3196..3235`, `REQ-LNK-2034..2233`)
- `docs/base/tasks/0796 - BOOTSTRAP-574 — COMPILER SYMBOLIC EXECUTION 2.0.md` (§574.1–§574.200, `REQ-CORE-3236..3282`, `REQ-LNK-2234..2433`)
- `docs/base/tasks/0797 - BOOTSTRAP-575 — COMPILER OPTIMIZATION SAFETY & TRANSFORMATION VERIFIER 2.0.md` (§575.1–§575.200, `REQ-CORE-3283..3285`, `REQ-LNK-2434..2633`)
- `docs/base/tasks/0798 - BOOTSTRAP-576 — COMPILER OPTIMIZATION PASS LIBRARY 3.0.md` (§576.1–§576.200, `REQ-LNK-2634..2833`)
- `docs/base/tasks/0799 - BOOTSTRAP-577 — COMPILER REGISTER ALLOCATION 3.0.md` (§577.1–§577.200, `REQ-LNK-2834..3033`)
- `docs/base/tasks/0800 - BOOTSTRAP-578 — COMPILER INSTRUCTION SCHEDULING 3.0.md` (§578.1–§578.200, `REQ-LNK-3034..3233`)
- `docs/base/tasks/0801 - BOOTSTRAP-579 — COMPILER MACHINE CODE FINALIZATION 3.0.md` (§579.1–§579.200, `REQ-LNK-3234..3433`)
