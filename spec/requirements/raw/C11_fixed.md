| id | area | tier | statement | sources | status |
|---|---|---|---|---|---|
| RQ-C11-001 | linker | v1-core | Linker must not change language semantics. | tasks/0786 | GAP |
| RQ-C11-002 | linker | v1-core | Linker must not change type semantics. | tasks/0786 | GAP |
| RQ-C11-003 | linker | v1-core | Linker must not change ownership semantics. | tasks/0786 | GAP |
| RQ-C11-004 | linker | v1-core | Linker must not change memory model. | tasks/0786 | GAP |
| RQ-C11-005 | linker | v1-core | Linker must not change ABI. | tasks/0786 | GAP |
| RQ-C11-006 | linker | v1-core | Linker must resolve symbols deterministic. | tasks/0786 | GAP |
| RQ-C11-007 | linker | v1-core | Duplicate strong symbols must diagnostic. | tasks/0786 | GAP |
| RQ-C11-008 | linker | v1-core | Undefined symbols must diagnostic trừ explicit dynamic imports. | tasks/0786 | GAP |
| RQ-C11-009 | linker | v1-core | Weak resolution must deterministic. | tasks/0786 | GAP |
| RQ-C11-010 | linker | v1-core | Common symbol handling must target-correct. | tasks/0786 | GAP |
| RQ-C11-011 | artifact | v1-core | Artifact must not trở thành nguồn sự thật thứ hai của compiler. | tasks/0787 | GAP |
| RQ-C11-012 | artifact | v1-core | Source semantics luôn là authoritative input. | tasks/0787 | GAP |
| RQ-C11-013 | artifact | v1-core | Artifact identity must deterministic. | tasks/0787 | GAP |
| RQ-C11-014 | artifact | v1-core | Canonical serialization must deterministic. | tasks/0787 | GAP |
| RQ-C11-015 | artifact | v1-core | Artifact hash must ổn định. | tasks/0787 | GAP |
| RQ-C11-016 | artifact | v1-core | Process pointer must not serialize. | tasks/0787 | GAP |
| RQ-C11-017 | artifact | v1-core | Host virtual address must not serialize. | tasks/0787 | GAP |
| RQ-C11-018 | artifact | v1-core | Absolute host filesystem state must not implicit dependency. | tasks/0787 | GAP |
| RQ-C11-019 | artifact | v1-core | Mọi offset must bounds-check. | tasks/0787 | GAP |
| RQ-C11-020 | artifact | v1-core | Mọi size must overflow-check. | tasks/0787 | GAP |
| RQ-C11-021 | compiler | v1-core | Security suppression must explicit và audit được. | tasks/0794 §572.183 | GAP |
| RQ-C11-022 | diagnostics | v1-core | Dead-code warning must not suppress unrelated diagnostics. | tasks/0794 §572.185 | GAP |
| RQ-C11-023 | testing | v1-core | Critical analyses must được test bằng reference semantics. | tasks/0794 §572.186 | GAP |
| RQ-C11-024 | compiler | v1-core | Known violation must luôn được phát hiện trong các analyses được cam kết sound. | tasks/0794 §572.191 | GAP |
| RQ-C11-025 | compiler | v1-core | Unknown state must not biến thành safe state. | tasks/0794 §572.192 | GAP |
| RQ-C11-026 | optimizer | v1-core | Mọi fixed bug must trở thành permanent analysis test. | tasks/0794 §572.193 | GAP |
| RQ-C11-027 | compiler | v1-core | Standard profile must phù hợp incremental IDE usage. | tasks/0794 §572.194 | GAP |
| RQ-C11-028 | optimizer | v1-core | Static analysis must not biến thành mandatory Rust-style borrow/lifetime checker. | tasks/0794 §572.196 | GAP |
| RQ-C11-029 | optimizer | v1-core | Axiom Static Analysis 3.0 must phân biệt tuyệt đối giữa “đã chứng minh”, “có khả năng”, và “chưa biết”. Mọi analysis safety-critical must conservative; timeout, thiếu metadata, dynamic dispatch, FFI hoặc open-world assumptions chỉ có thể làm giảm mức độ chắc chắn chứ must not biến thành proof giả. Static analysis must not biến Axiom thành một borrow-checker nặng; nó là một tầng phân tích độc lập, có thể incremental, parallel, cached và whole-program, nhưng semantic correctness vẫn thuộc compiler language rules và canonical semantic engine. | tasks/0794 §572.200 | GAP |
| RQ-C11-030 | compiler | v1-core | Không must mọi effect category đều dùng cùng một total ordering; mỗi category có lattice riêng. | tasks/0795 §573.14 | GAP |
| RQ-C11-031 | compiler | v1-core | Unknown` must not tự động hạ xuống thành một effect cụ thể. | tasks/0795 §573.14 | GAP |
| RQ-C11-032 | compiler | v1-core | Nếu callee effect change, caller summaries phụ thuộc vào callee must invalidate. | tasks/0795 §573.24 | GAP |
| RQ-C11-033 | compiler | v1-core | Hardware/system entropy must được phân loại external/nondeterministic. | tasks/0795 §573.36 | GAP |
| RQ-C11-034 | compiler | v1-core | Debug-only logging must được modeled theo compilation profile. | tasks/0795 §573.39 | GAP |
| RQ-C11-035 | compiler | v1-core | Cleanup paths must contribute effects vào summary. | tasks/0795 §573.45 | GAP |
| RQ-C11-036 | compiler | v1-core | Blocking operation must được đánh dấu `Block`. | tasks/0795 §573.57 | GAP |
| RQ-C11-037 | compiler | v1-core | Nếu borrow escape function boundary, summary must reflect lifetime/resource consequence. | tasks/0795 §573.69 | GAP |
| RQ-C11-038 | ffi | v1-core | Compiler không tự tin vào FFI contract nếu function must not đánh dấu trusted/verified theo FFI rules. | tasks/0795 §573.71 | GAP |
| RQ-C11-039 | compiler | v1-core | Function passed as callback must satisfy required effect bound. | tasks/0795 §573.82 | GAP |
| RQ-C11-040 | compiler | v1-core | Function accepting callbacks must include callback effects trong summary nếu callback được invoke. | tasks/0795 §573.85 | GAP |
| RQ-C11-041 | runtime | v1-core | Runtime không mandatory must carry effect metadata nếu compiler đã resolve statically. | tasks/0795 §573.88 | GAP |
| RQ-C11-042 | optimizer | v1-core | Effect analysis must hướng tới zero runtime overhead trong native optimized builds. | tasks/0795 §573.89 | GAP |
| RQ-C11-043 | compiler | v1-core | Impure call must not eliminate chỉ vì return value không dùng. | tasks/0795 §573.92 | GAP |
| RQ-C11-044 | compiler | v1-core | Caller must not assume callee purity chỉ vì caller itself được declared pure. | tasks/0795 §573.108 | GAP |
| RQ-C11-045 | compiler | v1-core | Explicit effect declarations có thể được compiler trust theo policy nhưng must giữ provenance. | tasks/0795 §573.109 | GAP |
| RQ-C11-046 | compiler | v1-core | Unsafe/trusted assertion must được đánh dấu rõ. | tasks/0795 §573.111 | GAP |
| RQ-C11-047 | compiler | v1-core | Syntax effect annotation must optional trong common code. | tasks/0795 §573.114 | GAP |
| RQ-C11-048 | compiler | v1-core | AI explanation must lấy canonical effect summary. | tasks/0795 §573.122 | GAP |
| RQ-C11-049 | runtime | v1-core | Comptime functions must thỏa effect policy nghiêm ngặt hơn runtime functions. | tasks/0795 §573.128 | GAP |
| RQ-C11-050 | runtime | v1-core | Const evaluator must not thực thi arbitrary runtime IO effects. | tasks/0795 §573.129 | GAP |
| RQ-C11-051 | compiler | v1-core | Nếu Axiom cho phép compile-time file access, nó must là explicit build input/effect. | tasks/0795 §573.130 | GAP |
| RQ-C11-052 | compiler | v1-core | Nondeterministic effects trong comptime must bị cấm hoặc explicit external build input. | tasks/0795 §573.131 | GAP |
| RQ-C11-053 | compiler | v1-core | Effect system must not dùng để cache một function nếu effect summary cho thấy observable state dependency. | tasks/0795 §573.132 | GAP |
| RQ-C11-054 | compiler | v1-core | Unknown hidden state → must not classify Pure. | tasks/0795 §573.135 | GAP |
| RQ-C11-055 | compiler | v1-core | Memory-mapped device IO must được mark volatile/device effect. | tasks/0795 §573.137 | GAP |
| RQ-C11-056 | compiler | v1-core | Device synchronization must được represented trong effect graph. | tasks/0795 §573.144 | GAP |
| RQ-C11-057 | compiler | v1-core | Inference must monotonic: | tasks/0795 §573.156 | GAP |
| RQ-C11-058 | compiler | v1-core | must not oscillate. | tasks/0795 §573.156 | GAP |
| RQ-C11-059 | compiler | v1-core | Traversal order must not change canonical summary. | tasks/0795 §573.157 | GAP |
| RQ-C11-060 | compiler | v1-core | Parallel và serial inference must cho cùng summary. | tasks/0795 §573.159 | GAP |
| RQ-C11-061 | compiler | v1-core | Older `.axsem` effect summaries must được migrate hoặc reject rõ ràng. | tasks/0795 §573.162 | GAP |
| RQ-C11-062 | compiler | v1-core | Target-specific effect summaries must not nhầm với target-independent summaries. | tasks/0795 §573.163 | GAP |
| RQ-C11-063 | compiler | v1-core | Partial summary must có `Incomplete` marker. | tasks/0795 §573.172 | GAP |
| RQ-C11-064 | compiler | v1-core | Effect cache key must bao gồm analyzer/schema version. | tasks/0795 §573.173 | GAP |
| RQ-C11-065 | compiler | v1-core | Corrupted/stale summary must reject. | tasks/0795 §573.174 | GAP |
| RQ-C11-066 | diagnostics | v1-core | Diagnostic must chỉ rõ: | tasks/0795 §573.112 | GAP |
| RQ-C11-067 | testing | v1-core | Mỗi primitive MIR operation must có expected effect test. | tasks/0795 §573.184 | GAP |
| RQ-C11-068 | compiler | v1-core | Known side effect must không thể bị classify thành `Pure`. | tasks/0795 §573.190 | GAP |
| RQ-C11-069 | compiler | v1-core | Missing metadata must produce conservative `Unknown`. | tasks/0795 §573.191 | GAP |
| RQ-C11-070 | compiler | v1-core | Cùng MIR snapshot must produce byte-identical canonical effect summary. | tasks/0795 §573.192 | GAP |
| RQ-C11-071 | compiler | v1-core | Local effect inference must O(number of relevant MIR operations + dependency edges) ở mức cơ bản. | tasks/0795 §573.193 | GAP |
| RQ-C11-072 | optimizer | v1-core | Small source change must not trigger whole-program analysis khi dependency graph chứng minh không cần. | tasks/0795 §573.194 | GAP |
| RQ-C11-073 | compiler | v1-core | Effect summaries must compact và có thể intern/shared. | tasks/0795 §573.195 | GAP |
| RQ-C11-074 | optimizer | v1-core | Effect analysis must not trở thành một semantic type system thứ hai cạnh type checker. | tasks/0795 §573.199 | GAP |
| RQ-C11-075 | optimizer | v1-core | Axiom Effect System must là một hệ thống suy luận effect canonical, deterministic và conservative. Function effects được suy ra từ MIR và transitive call summaries; `Unknown` không bao giờ được coi là `Pure` hay `Safe`; declared effects must not tự tạo proof nếu chưa được xác minh theo policy. Effect metadata must có thể được compiler, optimizer, static analyzer, concurrency engine, FFI, async runtime, IDE và AI dùng chung. Effect analysis không tạo runtime overhead mandatory và không làm Axiom thành một ngôn ngữ must viết effect annotation ở mọi nơi. | tasks/0795 §573.200 | GAP |
| RQ-C11-076 | compiler | v1-core | Trọng tâm sẽ là **proof engine có giới hạn tài nguyên**, không biến Axiom compiler thành một theorem prover nặng. Nó must tận dụng tối đa facts từ `571–573`, chỉ đi sâu symbolic execution khi việc đó thực sự giúp chứng minh một property hoặc tìm bug. | tasks/0795 §573.200 | GAP |
| RQ-C11-077 | compiler | v1-core | The goal is not biến Axiom thành theorem-proving language. The goal là dùng symbolic reasoning **có giới hạn** để chứng minh những property thực dụng của compiler: | tasks/0796 §574.200 | GAP |
| RQ-C11-078 | compiler | v1-core | Symbolic engine chỉ must chứng minh các property nằm trong supported abstract domains. | tasks/0796 §574.2 | GAP |
| RQ-C11-079 | compiler | v1-core | Equivalent expressions must canonicalize khi có thể. | tasks/0796 §574.6 | GAP |
| RQ-C11-080 | compiler | v1-core | Range must respect bit width và signedness. | tasks/0796 §574.9 | GAP |
| RQ-C11-081 | compiler | v1-core | Symbolic engine must tuân thủ chính xác semantics của từng arithmetic operation. | tasks/0796 §574.10 | GAP |
| RQ-C11-082 | compiler | v1-core | Không được tự giả định mọi integer operation là mathematical integer. | tasks/0796 §574.10 | GAP |
| RQ-C11-083 | compiler | v1-core | Nếu operation wrapping, proof engine must model modulo arithmetic. | tasks/0796 §574.11 | GAP |
| RQ-C11-084 | compiler | v1-core | Saturating operation must preserve saturation semantics. | tasks/0796 §574.13 | GAP |
| RQ-C11-085 | compiler | v1-core | Float symbolic reasoning must conservative hơn integer reasoning. | tasks/0796 §574.14 | GAP |
| RQ-C11-086 | compiler | v1-core | Floating-point domain must có trạng thái NaN khi cần. | tasks/0796 §574.15 | GAP |
| RQ-C11-087 | optimizer | v1-core | +∞/-∞` must được model khi analysis hỗ trợ. | tasks/0796 §574.1 | GAP |
| RQ-C11-088 | compiler | v1-core | IEEE semantics must được preserve khi relevant. | tasks/0796 §574.17 | GAP |
| RQ-C11-089 | compiler | v1-core | Engine must giới hạn số path/disjunct. | tasks/0796 §574.31 | GAP |
| RQ-C11-090 | compiler | v1-core | Không được enumerate vô hạn paths. | tasks/0796 §574.32 | GAP |
| RQ-C11-091 | compiler | v1-core | Loops must đạt fixed point hoặc conservative approximation. | tasks/0796 §574.36 | GAP |
| RQ-C11-092 | optimizer | v1-core | Mọi optimization proof must lưu provenance nội bộ: | tasks/0796 §574.43 | GAP |
| RQ-C11-093 | compiler | v1-core | Proof object không nhất thiết must lưu trong release binary. | tasks/0796 §574.44 | GAP |
| RQ-C11-094 | compiler | v1-core | MIR/semantic/dataflow change must invalidate proof liên quan. | tasks/0796 §574.47 | GAP |
| RQ-C11-095 | compiler | v1-core | Engine must detect: | tasks/0796 §574.48 | GAP |
| RQ-C11-096 | compiler | v1-core | Nếu denominator unknown → must not claim safe. | tasks/0796 §574.50 | GAP |
| RQ-C11-097 | compiler | v1-core | Shift amount must nằm trong legal range. | tasks/0796 §574.51 | GAP |
| RQ-C11-098 | compiler | v1-core | Raw pointer reasoning must conservative. | tasks/0796 §574.55 | GAP |
| RQ-C11-099 | compiler | v1-core | Symbolic engine must not phá vỡ pointer provenance semantics. | tasks/0796 §574.56 | GAP |
| RQ-C11-100 | compiler | v1-core | Volatile access must not symbolic-fold như ordinary memory. | tasks/0796 §574.65 | GAP |
| RQ-C11-101 | compiler | v1-core | Atomic access must giữ synchronization semantics. | tasks/0796 §574.66 | GAP |
| RQ-C11-102 | compiler | v1-core | Unknown call must conservative. | tasks/0796 §574.71 | GAP |
| RQ-C11-103 | compiler | v1-core | Contract must phân biệt: | tasks/0796 §574.73 | GAP |
| RQ-C11-104 | optimizer | v1-core | Không được dùng cho hard optimizer proof nếu policy không cho phép. | tasks/0796 §574.76 | GAP |
| RQ-C11-105 | optimizer | v1-core | Incomplete path analysis → finding must được đánh dấu potential/unknown. | tasks/0796 §574.88 | GAP |
| RQ-C11-106 | compiler | v1-core | Engine must detect ít nhất contradiction của supported domains. | tasks/0796 §574.92 | GAP |
| RQ-C11-107 | compiler | v1-core | Core native compiler must not phụ thuộc mandatory vào external SMT solver. | tasks/0796 §574.95 | GAP |
| RQ-C11-108 | compiler | v1-core | Solver result must bind với exact query/input snapshot. | tasks/0796 §574.97 | GAP |
| RQ-C11-109 | compiler | v1-core | Abstract counterexample must được ghi rõ nếu chưa concretized. | tasks/0796 §574.102 | GAP |
| RQ-C11-110 | compiler | v1-core | Engine must có bounded exploration. | tasks/0796 §574.108 | GAP |
| RQ-C11-111 | optimizer | v1-core | Cùng budget + snapshot must cho deterministic analysis outcome. | tasks/0796 §574.110 | GAP |
| RQ-C11-112 | compiler | v1-core | Transformation yêu cầu proof must fail-closed. | tasks/0796 §574.123 | GAP |
| RQ-C11-113 | compiler | v1-core | Một input fact invalidated must invalidate dependent proofs. | tasks/0796 §574.128 | GAP |
| RQ-C11-114 | compiler | v1-core | Equivalent proof facts must canonicalize để cache hiệu quả. | tasks/0796 §574.130 | GAP |
| RQ-C11-115 | compiler | v1-core | Abstract states must compact. | tasks/0796 §574.134 | GAP |
| RQ-C11-116 | compiler | v1-core | Integer identities must xét overflow semantics. | tasks/0796 §574.141 | GAP |
| RQ-C11-117 | compiler | v1-core | Signed/unsigned comparisons must preserve exact semantics. | tasks/0796 §574.142 | GAP |
| RQ-C11-118 | compiler | v1-core | Symbolic engine must not nhầm byte length với character count. | tasks/0796 §574.151 | GAP |
| RQ-C11-119 | compiler | v1-core | Await/suspend boundaries must preserve resource facts. | tasks/0796 §574.157 | GAP |
| RQ-C11-120 | compiler | v1-core | Cancellation paths must được symbolic modeled. | tasks/0796 §574.158 | GAP |
| RQ-C11-121 | runtime | v1-core | Panic path must đi qua cleanup graph theo runtime semantics. | tasks/0796 §574.159 | GAP |
| RQ-C11-122 | compiler | v1-core | Atomic semantics must not simplify thành ordinary memory operations. | tasks/0796 §574.163 | GAP |
| RQ-C11-123 | compiler | v1-core | Không được constant-fold dựa trên unknown external state. | tasks/0796 §574.166 | GAP |
| RQ-C11-124 | compiler | v1-core | Time/random/system state must giữ symbolic unknown. | tasks/0796 §574.167 | GAP |
| RQ-C11-125 | compiler | v1-core | Environment-dependent values must not coi constant trừ khi build explicitly captures them. | tasks/0796 §574.168 | GAP |
| RQ-C11-126 | compiler | v1-core | Unknown must not biến thành false-positive hard error. | tasks/0796 §574.177 | GAP |
| RQ-C11-127 | compiler | v1-core | AI must not tự tạo proof. | tasks/0796 §574.1 | GAP |
| RQ-C11-128 | compiler | v1-core | Cache hit/miss must not change semantic result. | tasks/0796 §574.184 | GAP |
| RQ-C11-129 | compiler | v1-core | Optional solver execution must được sandbox/trust-boundary kiểm soát. | tasks/0796 §574.186 | GAP |
| RQ-C11-130 | optimizer | v1-core | Nếu proof verifier reject proof → optimization must not áp dụng. | tasks/0796 §574.190 | GAP |
| RQ-C11-131 | compiler | v1-core | Corpus must chứa: | tasks/0796 §574.194 | GAP |
| RQ-C11-132 | compiler | v1-core | Common proofs must chạy trong compiler hot path với low overhead. | tasks/0796 §574.195 | GAP |
| RQ-C11-133 | compiler | v1-core | Expensive symbolic execution must not làm compilation baseline chậm đáng kể. | tasks/0796 §574.196 | GAP |
| RQ-C11-134 | optimizer | v1-core | Axiom Symbolic Execution 2.0 must là một proof engine có giới hạn, deterministic, incremental và fail-closed. Nó được phép dùng abstract interpretation, symbolic values, path constraints và optional solver để chứng minh các property thực dụng, nhưng must not biến compiler thành theorem prover mandatory. `Unknown` luôn khác `Proven`; timeout, thiếu metadata, external effects, floating-point uncertainty hoặc path explosion must dẫn đến approximation/conservative result. Mọi optimization dựa trên proof must có provenance và chỉ được áp dụng khi proof đủ mạnh cho transformation đó. | tasks/0796 §574.200 | GAP |
| RQ-C11-135 | optimizer | v1-core | Trọng tâm `575` sẽ là tạo **hàng rào cuối cùng giữa optimizer và miscompilation**: mỗi optimization quan trọng must khai báo transformation contract, preconditions, preserved properties và postconditions; verifier kiểm tra chúng trước khi native codegen tiếp tục. | tasks/0796 §574.200 | GAP |
| RQ-C11-136 | optimizer | v1-core | Optimizer được phép rất mạnh, nhưng **must not biến một giả định chưa chứng minh thành machine code**. | tasks/0797 §575.200 | GAP |
| RQ-C11-137 | optimizer | v1-core | Mỗi optimization pass must khai báo contract: | tasks/0797 §575.2 | GAP |
| RQ-C11-138 | compiler | v1-core | Pass must khai báo IR level yêu cầu: | tasks/0797 §575.4 | GAP |
| RQ-C11-139 | compiler | v1-core | Postcondition mô tả property must đúng sau transformation. | tasks/0797 §575.6 | GAP |
| RQ-C11-140 | compiler | v1-core | Pass must khai báo properties must not change: | tasks/0797 §575.2 | GAP |

## Conflicts
None found.

## Files skimmed
48 files skimmed.
- docs/base/tasks/0786 - BOOTSTRAP-564 — COMPILER LINKER 3.0 — WHOLE-PROGRAM LINKING, SYMBOL RESOLUTION, SECTION GC, ICF, RELAXATION, TLS, IMPORTEXPORT & FINAL IMAGE OPTIMIZAT.md
- docs/base/tasks/0787 - BOOTSTRAP-565 — COMPILER ARTIFACT FORMAT 2.0 — AXIOM OBJECTLTOSEMANTICDEBUG PACKAGE, SECTION SCHEMA, VERSIONING, COMPATIBILITY & ZERO-COPY COMPILATION.md
- docs/base/tasks/0788 - BOOTSTRAP-566 — COMPILER CACHE 3.0 — SEMANTIC INVALIDATION, CROSS-PHASE REUSE, REMOTE CACHE, CACHE TRUST, CACHE GC & ZERO-REBUILD INCREMENTAL COMPILAT.md
- docs/base/tasks/0789 - BOOTSTRAP-567 — COMPILER DISTRIBUTED BUILD 2.0 — REMOTE EXECUTION, CONTENT-ADDRESSED WORKERS, HERMETIC ACTIONS, REMOTE ARTIFACT TRANSFER, SCHEDULING &.md
- docs/base/tasks/0790 - BOOTSTRAP-568 — COMPILER BUILD ORCHESTRATOR 3.0 — DAG EXECUTION ENGINE, SPECULATIVE COMPILATION, CRITICAL-PATH SCHEDULING, RESOURCE-AWARE PARALLELISM.md
- docs/base/tasks/0791 - BOOTSTRAP-569 — COMPILER DIAGNOSTIC ENGINE 3.0.md
- docs/base/tasks/0792 - BOOTSTRAP-570 — COMPILER IDELSP ENGINE 4.0.md
- docs/base/tasks/0793 - BOOTSTRAP-571 — COMPILER SOURCE ANALYSIS 2.0.md
- docs/base/tasks/0794 - BOOTSTRAP-572 — COMPILER STATIC ANALYSIS 3.0.md
- docs/base/tasks/0795 - BOOTSTRAP-573 — COMPILER EFFECT SYSTEM 2.0.md
- docs/base/tasks/0796 - BOOTSTRAP-574 — COMPILER SYMBOLIC EXECUTION 2.0.md
- docs/base/tasks/0797 - BOOTSTRAP-575 — COMPILER OPTIMIZATION SAFETY & TRANSFORMATION VERIFIER 2.0.md
- docs/base/tasks/0798 - BOOTSTRAP-576 — COMPILER OPTIMIZATION PASS LIBRARY 3.0.md
- docs/base/tasks/0799 - BOOTSTRAP-577 — COMPILER REGISTER ALLOCATION 3.0.md
- docs/base/tasks/0800 - BOOTSTRAP-578 — COMPILER INSTRUCTION SCHEDULING 3.0.md
- docs/base/tasks/0801 - BOOTSTRAP-579 — COMPILER MACHINE CODE FINALIZATION 3.0.md
- docs/base/tasks/0802 - BOOTSTRAP-580 — MACHINE CODE ENCODING 4.0.md
- docs/base/tasks/0803 - BOOTSTRAP-581 — OBJECT FILE WRITER 3.0.md
- docs/base/tasks/0804 - BOOTSTRAP-582 — NATIVE LINKER 4.0.md
- docs/base/tasks/0805 - BOOTSTRAP-583 — NATIVE IMAGE LOADER CONTRACT 2.0.md
- docs/base/tasks/0806 - BOOTSTRAP-584 — NATIVE EXECUTABLE IMAGE FORMAT 3.0.md
- docs/base/tasks/0807 - BOOTSTRAP-585 — NATIVE STARTUP & CRT REPLACEMENT 3.0.md
- docs/base/tasks/0808 - BOOTSTRAP-586 — COMPILER BOOTSTRAP & RUNTIME SELF-HOSTING 4.0.md
- docs/base/tasks/0809 - BOOTSTRAP-587 — COMPILER BOOTSTRAP TRUST & DIVERGENT COMPILATION 3.0.md
- docs/base/tasks/0810 - BOOTSTRAP-588 — COMPILER DISTRIBUTION & TOOLCHAIN SDK 4.0.md
- docs/base/tasks/0811 - BOOTSTRAP-589 — NATIVE DEBUGGER & DEBUGGING TOOLCHAIN 4.0.md
- docs/base/tasks/0812 - BOOTSTRAP-590 — IDE PLATFORM & SEMANTIC DEVELOPMENT ENVIRONMENT 5.0.md
- docs/base/tasks/0813 - BOOTSTRAP-591 — PACKAGE REGISTRY, DEPENDENCY RESOLUTION & SUPPLY-CHAIN PLATFORM 5.0.md
- docs/base/tasks/0814 - BOOTSTRAP-592 — DISTRIBUTED PACKAGE BUILD & BINARY CACHE PLATFORM 5.0.md
- docs/base/tasks/0815 - BOOTSTRAP-593 — NATIVE APPLICATION PACKAGING, BUNDLE FORMAT & DEPLOYMENT GRAPH 5.0.md
- docs/base/tasks/0816 - BOOTSTRAP-594 — NATIVE APPLICATION RUNTIME & PROCESS SUPERVISION 5.0.md
- docs/base/tasks/0817 - BOOTSTRAP-595 — NATIVE APPLICATION CONFIGURATION & ENVIRONMENT 5.0.md
- docs/base/tasks/0818 - BOOTSTRAP-596 — NATIVE APPLICATION RESOURCE & ASSET RUNTIME 5.0.md
- docs/base/tasks/0819 - BOOTSTRAP-597 — NATIVE APPLICATION LOCAL STORAGE & USER DATA 5.0.md
- docs/base/tasks/0820 - BOOTSTRAP-598 — NATIVE APPLICATION IPC & INTER-PROCESS DATA MODEL 6.0.md
- docs/base/tasks/0821 - BOOTSTRAP-599 — NATIVE APPLICATION SERVICE MODEL & LOCAL SERVICE HOSTING 6.0.md
- docs/base/tasks/0822 - BOOTSTRAP-597 — NATIVE APPLICATION LOCAL STORAGE & USER DATA 5.0.md
- docs/base/tasks/0823 - BOOTSTRAP-598 — NATIVE APPLICATION UPDATE, DATA MIGRATION & VERSION COMPATIBILITY RUNTIME 5.0.md
- docs/base/tasks/0824 - BOOTSTRAP-599 — NATIVE APPLICATION CONFIGURATION, PREFERENCES, SECRETS & POLICY RUNTIME 5.0.md
- docs/base/tasks/0825 - BOOTSTRAP-600 — NATIVE APPLICATION STATE, SESSION, CHECKPOINT & CRASH-RESILIENT STATE RUNTIME 5.0.md
- docs/base/tasks/0826 - BOOTSTRAP-601 — NATIVE APPLICATION CONFIGURATION, SECRETS, ENVIRONMENT & DEPLOYMENT RUNTIME 5.0.md
- docs/base/tasks/0827 - BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0.md
- docs/base/tasks/0828 - BOOTSTRAP-603 — NATIVE APPLICATION SECURITY, IDENTITY, CAPABILITY & TRUST RUNTIME 5.0.md
- docs/base/tasks/0829 - BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0.md
- docs/base/tasks/0830 - BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0.md
- docs/base/tasks/0831 - BOOTSTRAP-603 — NATIVE APPLICATION SECURITY BOUNDARY, CAPABILITY SYSTEM, PERMISSIONS & TRUSTED RUNTIME 5.0.md
- docs/base/tasks/0832 - BOOTSTRAP-604.md
- docs/base/tasks/0833 - BOOTSTRAP-605.md
