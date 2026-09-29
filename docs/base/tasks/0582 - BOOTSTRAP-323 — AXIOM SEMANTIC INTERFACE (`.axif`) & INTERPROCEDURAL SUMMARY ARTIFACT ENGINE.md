# BOOTSTRAP-323 — AXIOM SEMANTIC INTERFACE (`.axif`) & INTERPROCEDURAL SUMMARY ARTIFACT ENGINE

Sau 321, Axiom đã có khả năng phân tích toàn chương trình. Sau 322, compiler còn có profile/feedback để tối ưu theo workload thực tế.

Nhưng một vấn đề rất quan trọng vẫn cần giải quyết:

> **Compiler phải có thể truyền các sự kiện semantic đã được chứng minh giữa các lần biên dịch mà không cần đọc lại source implementation của dependency.**

Đây chính là vai trò của `.axif`.

---

## 323.1. Vấn đề cần giải quyết

Giả sử:

```text
app.axm
   ↓
package math
```

`app` cần biết về `math`:

- function nào public;
- type nào public;
- ABI thế nào;
- function có panic không;
- function có allocation không;
- ownership transfer ra sao;
- argument có thể alias không;
- function có suspend không;
- có Send/Share requirement không;
- trait implementation nào tồn tại;
- generic constraint;
- FFI contract;
- semantic summary;
- optimization summary.

Nhưng app **không cần và không nên** đọc toàn bộ implementation của `math`.

Do đó:

```text
math source
    ↓
compiler
    ↓
math.axif
```

và:

```text
app compiler
    ↓
read math.axif
```

---

# 323.2. `.axif` không phải object file

Phải phân biệt rõ:

```text
.axm
    source

.axif
    semantic interface

.axo
    relocatable object

.axlib
    static library

.axso/.dll/.dylib
    shared image

.debug
    debug information
```

`.axif` trả lời:

> **"Dependency này có ý nghĩa semantic và ABI như thế nào?"**

`.axo` trả lời:

> **"Dependency này đã được codegen thành machine code như thế nào?"**

---

# 323.3. `.axif` không chỉ là header

C/C++ header chủ yếu mô tả declaration:

```text
int foo(int);
```

`.axif` phải mô tả nhiều hơn:

```text
foo:
    input: i32
    output: i32

    ownership:
        consumes: none
        returns: value

    capabilities:
        reads: none
        writes: none

    effects:
        pure

    panic:
        impossible

    allocation:
        none

    concurrency:
        Send

    ABI:
        axiom-native-vX
```

Nó là:

> **Semantic contract artifact.**

---

# 323.4. Kiến trúc artifact

`.axif` gồm các layer:

```text
AXIF
├── Identity
├── Package
├── Module
├── Public Declarations
├── Types
├── Traits
├── Generics
├── ABI
├── Ownership
├── Capability
├── Effects
├── Concurrency
├── Async
├── GPU
├── FFI
├── Reachability
├── Semantic Summaries
├── Optimization Summaries
├── Security / Provenance
└── Fingerprints
```

Không phải mọi package đều phải emit tất cả layer.

---

# 323.5. Identity Header

Header tối thiểu:

```text
AxifHeader {
    magic
    format_version
    semantic_spec_version

    compiler_semantic_version
    target_family

    package_id
    package_version

    source_fingerprint
    public_api_fingerprint
    semantic_fingerprint
    abi_fingerprint
}
```

Ví dụ:

```text
AXIF
format = 1
spec = 0.1
package = std.math
version = 1.4.0
```

---

# 323.6. Public API Fingerprint

Fingerprint của:

```text
public declarations
public types
public traits
public constants
public ABI
```

Nếu implementation private thay đổi:

```text
public_api_fingerprint
```

có thể không đổi.

Khi đó dependent package có thể tránh recompilation.

---

# 323.7. Semantic Fingerprint

Khác với API fingerprint.

Ví dụ implementation thay đổi từ:

```text
fn foo(x: i32) -> i32
```

thành implementation khác nhưng vẫn cùng API.

Nếu semantic contract vẫn giữ:

```text
semantic_fingerprint
```

có thể giữ nguyên.

Nhưng nếu function trước đây:

```text
no_alloc
```

nay có allocation:

```text
semantic_fingerprint != old
```

---

# 323.8. ABI Fingerprint

ABI phải độc lập:

```text
abi_fingerprint
```

Bao gồm:

- calling convention;
- parameter lowering;
- return lowering;
- struct layout;
- alignment;
- enum representation;
- symbol ABI;
- target ABI;
- exception/panic convention;
- async ABI;
- FFI ABI.

Thay đổi ABI có thể yêu cầu relink hoặc rebuild.

---

# 323.9. Declaration Record

Ví dụ:

```text
FunctionDecl {
    id
    name
    visibility

    generic_parameters
    parameters
    return_type

    effects
    ownership_contract
    capability_contract

    async_info
    gpu_info

    abi
}
```

---

# 323.10. Type Record

`.axif` cần serialize semantic type identity:

```text
TypeRecord {
    TypeId
    kind
    generic_parameters
    fields
    variants

    traits
    repr
    layout_contract
}
```

Không serialize implementation-specific compiler pointer/ID.

Ví dụ:

```text
TypeId = hash(package_id, declaration_id)
```

---

# 323.11. Trait Record

Ví dụ:

```text
TraitRecord {
    trait_id
    name

    methods
    associated_types
    associated_constants

    supertraits
    generic_constraints

    object_safety
}
```

Compiler consumer có thể giải quyết:

```text
T: Iterator
```

mà không cần source của package.

---

# 323.12. Trait Implementation Summary

`.axif` phải mô tả:

```text
impl Iterator for MyVec
```

nhưng không nhất thiết expose private implementation.

Record:

```text
TraitImplRecord {
    trait_id
    type_pattern
    constraints
    associated_items
    coherence_identity
}
```

---

# 323.13. Generic Contract

Ví dụ:

```text
fn sort<T: Ord + Send>(x: mut_view<T>)
```

`.axif` phải lưu:

```text
GenericContract {
    parameters
    trait_bounds
    type_constraints
    const_constraints
    ownership_constraints
    capability_constraints
    Send/Share constraints
}
```

---

# 323.14. Ownership Summary

Ví dụ:

```text
fn consume(x: Buffer) -> Buffer
```

summary:

```text
OwnershipSummary {
    parameter[0]:
        Consume

    return:
        CreatesOwner
}
```

Hoặc:

```text
fn inspect(x: view<T>)
```

```text
parameter[0]:
    ReadCapability
    DoesNotConsumeOwner
```

---

# 323.15. Capability Summary

Ví dụ:

```text
fn process(x: view<Data>)
```

có thể ghi:

```text
CapabilitySummary {
    reads: parameter[0]
    writes: none
    escapes: false
}
```

Compiler consumer có thể dùng thông tin này cho interprocedural analysis.

---

# 323.16. Effect Summary

Ví dụ:

```text
fn hash(x: &[u8]) -> u64
```

có thể:

```text
Effects {
    ReadMemory
}
```

Trong khi:

```text
fn save(x: Data) -> Result<()>
```

có:

```text
Effects {
    FileIO
    Allocation
}
```

Effect summary phải được xem là **semantic contract đã được verifier xác nhận**, không phải heuristic.

---

# 323.17. Panic Contract

Function có thể có:

```text
PanicBehavior {
    Never
    MayPanic
    AlwaysPanic
    TargetDefined
}
```

Ví dụ compiler có thể biết:

```text
checked_div()
```

có thể panic/trap.

Thông tin này hỗ trợ:

- DCE;
- CFG;
- optimization;
- exception/unwind planning;
- diagnostics.

---

# 323.18. Allocation Summary

```text
AllocationSummary {
    may_allocate
    allocation_sites
    may_deallocate
    allocation_escape
}
```

Có thể chi tiết:

```text
allocation:
    count = unknown
    escapes = false
```

hoặc:

```text
allocation:
    returned_to_caller = true
```

---

# 323.19. Escape Summary

Ví dụ:

```text
fn foo(x: view<T>)
```

summary:

```text
EscapeSummary {
    parameter[0]:
        NoEscape
}
```

Nếu function lưu view vào global:

```text
EscapeSummary {
    parameter[0]:
        GlobalEscape
}
```

Điều này rất quan trọng vì caller có thể dùng summary thay vì re-analyze callee source.

---

# 323.20. Alias Summary

Ví dụ:

```text
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

summary có thể chứa:

```text
AliasSummary {
    a ↔ b: allowed
    a ↔ out: forbidden
    b ↔ out: forbidden
}
```

Nhưng:

> `.axif` chỉ được ghi **NoAlias** khi fact đã được chứng minh.

Không được ghi dựa trên heuristic.

---

# 323.21. Concurrency Summary

```text
ConcurrencySummary {
    spawns
    sends
    receives
    locks
    atomics
    synchronization
    thread_migration
}
```

Ví dụ:

```text
fn worker(x: Buffer) -> Buffer
```

có:

```text
Send:
    yes

Share:
    no
```

---

# 323.22. Async Summary

```text
AsyncSummary {
    is_async
    may_suspend
    suspension_count
    state_size
    may_block
    Send
    Share
}
```

Compiler caller có thể quyết định:

```text
await foo()
```

có thể ảnh hưởng state machine thế nào.

---

# 323.23. GPU Summary

```text
GpuSummary {
    kernel
    execution_domain
    storage_domains
    synchronization
    resource_requirements
}
```

Ví dụ:

```text
@kernel
fn add(...)
```

consumer có thể kiểm tra legality mà không cần implementation source.

---

# 323.24. FFI Contract

`.axif` phải lưu:

```text
FfiContract {
    abi
    calling_convention

    ownership
    aliasing
    effects

    panic_behavior
    thread_behavior
    async_behavior

    layout
}
```

Foreign declarations không được mặc định coi là safe.

---

# 323.25. Dynamic Boundary

Đây là phần rất quan trọng cho whole-program optimization.

`.axif` phải đánh dấu:

```text
DynamicBoundary {
    Plugin
    FFI
    Reflection
    DynamicLoading
    ExternalRuntime
    Unknown
}
```

Nếu có:

```text
dynamic_loading
```

compiler không được kết luận:

```text
"function này không bao giờ được gọi"
```

chỉ vì static call graph không thấy caller.

---

# 323.26. Reachability Roots

Interface có thể khai báo:

```text
ExportedSymbol
FfiSymbol
ReflectionRoot
PluginEntry
GpuEntry
RuntimeRoot
```

321 sử dụng chúng để xây ProgramGraph.

---

# 323.27. Optimization Summary

Đây là phần **không bắt buộc**.

Ví dụ:

```text
OptimizationSummary {
    likely_inline
    hot
    pure
    readonly
    allocation_free
    small
}
```

Nhưng phải phân biệt:

```text
SemanticSummary
```

với:

```text
OptimizationHint
```

Ví dụ:

```text
pure
```

nếu là semantic fact thì được verifier chứng minh.

Trong khi:

```text
likely_inline
```

chỉ là hint.

---

# 323.28. Không được nhầm Hint với Proof

Ví dụ `.axif`:

```text
foo:
    no_alias = proven
    hot = profile_hint
```

Compiler consumer được phép:

```text
dùng no_alias để chứng minh optimization
```

nhưng:

```text
hot
```

chỉ dùng để ưu tiên.

---

# 323.29. Certificate

Mỗi semantic summary quan trọng có thể đi kèm:

```text
SemanticCertificate {
    rule_version
    verifier_version
    input_fingerprint
    summary_fingerprint

    required_facts
    proven_facts

    certificate_kind
}
```

Consumer kiểm tra:

```text
certificate valid?
spec compatible?
compiler semantic version compatible?
fingerprint match?
```

---

# 323.30. Trust Model

Không được:

```text
read .axif
    ↓
blindly trust
```

Mà:

```text
.axif
 ↓
parse
 ↓
validate format
 ↓
validate identity
 ↓
validate fingerprint
 ↓
validate certificate
 ↓
validate semantic version
 ↓
accept facts
```

Nếu validation thất bại:

```text
reject
```

hoặc:

```text
treat as opaque dependency
```

không được nâng cấp UNKNOWN thành PROVEN.

---

# 323.31. Private Information

`.axif` không được leak implementation mặc định.

Ví dụ source:

```text
fn secret_algorithm(...)
```

private.

Public interface chỉ cần expose những gì consumer cần.

Không expose:

- private variable names;
- internal CFG;
- internal source;
- proprietary algorithm;
- debug information;
- profile workload;
- secrets.

---

# 323.32. Privacy Levels

Có thể có:

```text
InterfaceVisibility {
    Public
    Package
    Build
    Private
}
```

Một `.axif` phát hành ra registry chỉ chứa:

```text
Public
```

Trong LTO nội bộ có thể dùng:

```text
Package
Build
```

summary phong phú hơn.

---

# 323.33. Thin `.axif` và Full `.axif`

### Thin

Chỉ:

```text
API
Type
Trait
ABI
minimal semantic contract
```

dùng cho package distribution.

### Full

Thêm:

```text
interprocedural summaries
optimization metadata
inline candidates
profile feedback
LTO information
```

dùng trong build nội bộ.

---

# 323.34. Deterministic Serialization

Cùng semantic input:

```text
same source
same compiler semantic version
same target
```

phải tạo:

```text
identical .axif bytes
```

trừ metadata explicitly nondeterministic.

Canonicalization:

- stable ordering;
- stable IDs;
- canonical integer encoding;
- canonical string encoding;
- canonical type ordering;
- deterministic hash.

---

# 323.35. Compact Representation

Không nên biến `.axif` thành file khổng lồ.

Dùng:

```text
interned strings
type tables
symbol tables
shared constraints
deduplicated summaries
compact bitsets
```

Các declaration tham chiếu bằng ID thay vì lặp dữ liệu.

---

# 323.36. Cross-Target Interface

Một package có thể có:

```text
foo.axif
```

với nhiều target:

```text
targets/
    x86_64-windows.axif
    x86_64-linux.axif
    aarch64-linux.axif
    aarch64-macos.axif
```

hoặc một artifact chứa nhiều target sections.

Semantic core có thể giống nhau trong khi:

```text
ABI
layout
calling convention
target features
```

khác nhau.

---

# 323.37. Incremental Invalidation

Ví dụ implementation thay đổi:

```text
private function changed
```

nhưng:

```text
public_api_fingerprint unchanged
semantic_fingerprint unchanged
abi_fingerprint unchanged
```

→ consumer không cần rebuild.

Nếu:

```text
semantic_fingerprint changed
```

→ semantic-dependent units invalidated.

Nếu:

```text
abi_fingerprint changed
```

→ relink/recompile ABI-dependent units.

---

# 323.38. Fingerprint Dependency Graph

```text
Source
 ↓
ImplementationFingerprint
 ↓
SemanticSummaryFingerprint
 ↓
PublicAPIFingerprint
 ↓
ABIFingerprint
```

Không phải thay đổi nào cũng propagate toàn bộ graph.

Ví dụ:

```text
private optimization changed
```

có thể chỉ thay:

```text
implementation fingerprint
```

mà không thay:

```text
API / ABI
```

---

# 323.39. LTO

Trong LTO:

```text
.axif
   +
.axo
   +
profile
   ↓
WholeProgramDB
```

Compiler có thể sử dụng:

- semantic summaries;
- call graph;
- optimization summaries;
- profile;
- machine-level metadata.

Nếu source không còn:

```text
.axif + .axo
```

vẫn đủ cho một số dạng LTO.

---

# 323.40. Package Registry

Package manager có thể cache:

```text
package.axif
```

riêng với:

```text
package.axo
```

Ví dụ:

```text
registry/
    math/
        1.4.0/
            math.axif
            x86_64-linux/
                math.axo
            aarch64-linux/
                math.axo
```

Compiler frontend không cần tải source nếu package binary interface phù hợp.

---

# 323.41. AI Interface

`.axif` đặc biệt phù hợp cho AI.

Compiler có thể cung cấp:

```text
get_public_api(package)
get_type(package, type)
get_function_contract(function)
get_trait_impls(type)
get_effect_summary(function)
get_ownership_summary(function)
get_capability_summary(function)
get_async_summary(function)
get_gpu_summary(function)
get_ffi_contract(function)
get_abi(function)
```

AI không cần đọc hàng nghìn dòng source chỉ để biết:

> Function này nhận gì, trả gì, có ownership như thế nào và có thể gây effect gì?

---

# 323.42. AI Không Được Tự Suy Diễn Fact

AI có thể đọc:

```text
OwnershipSummary:
    consumes parameter 0
```

nhưng không được tự tạo:

```text
NoAlias = true
```

nếu `.axif` không có proof.

AI chỉ là consumer của semantic database.

---

# 323.43. CompilerDB Integration

Thêm:

```text
AxifDB
```

vào:

```text
CompilerDB
```

```text
CompilerDB
 ├── PackageDB
 ├── ModuleDB
 ├── TypeDB
 ├── TraitDB
 ├── ProgramDB
 ├── SummaryDB
 ├── ProfileDB
 ├── AxifDB
 └── CorrectnessDB
```

---

# 323.44. API

```text
load_axif()
```

```text
validate_axif()
```

```text
query_axif()
```

```text
get_public_api()
```

```text
get_semantic_summary()
```

```text
get_ownership_summary()
```

```text
get_capability_summary()
```

```text
get_effect_summary()
```

```text
get_concurrency_summary()
```

```text
get_async_summary()
```

```text
get_gpu_summary()
```

```text
get_ffi_contract()
```

```text
get_abi_contract()
```

```text
check_axif_compatibility()
```

```text
compute_axif_fingerprint()
```

```text
export_axif()
```

```text
explain_axif_change()
```

---

# 323.45. Implementation Tree

```text
compiler/interface/
├── axif/
│   ├── format.ax
│   ├── header.ax
│   ├── reader.ax
│   ├── writer.ax
│   ├── canonical.ax
│   └── verifier.ax
│
├── declarations/
│   ├── function.ax
│   ├── type.ax
│   ├── trait.ax
│   ├── generic.ax
│   └── impl.ax
│
├── summaries/
│   ├── semantic.ax
│   ├── ownership.ax
│   ├── capability.ax
│   ├── effect.ax
│   ├── escape.ax
│   ├── alias.ax
│   ├── concurrency.ax
│   ├── async.ax
│   ├── gpu.ax
│   └── ffi.ax
│
├── optimization/
│   ├── hints.ax
│   ├── lto.ax
│   └── profile.ax
│
├── fingerprint/
│   ├── api.ax
│   ├── semantic.ax
│   ├── abi.ax
│   └── compatibility.ax
│
├── certificate/
│   ├── certificate.ax
│   ├── verifier.ax
│   └── trust.ax
│
└── database/
    └── axif_db.ax
```

---

# 323.46. Invariants

```text
AIFACE-20  .axif is a semantic interface artifact, not an object file.

AIFACE-21  Public API identity is independent from implementation identity.

AIFACE-22  ABI compatibility is tracked independently from API compatibility.

AIFACE-23  Semantic summaries must originate from verified facts.

AIFACE-24  Optimization hints are never semantic proofs.

AIFACE-25  Unknown facts must never be upgraded to Proven by absence of information.

AIFACE-26  .axif consumers must validate format and semantic compatibility.

AIFACE-27  Invalid certificates cannot establish semantic facts.

AIFACE-28  Private implementation details are not exported by default.

AIFACE-29  Dynamic boundaries must be represented explicitly.

AIFACE-30  FFI contracts are explicit and conservative.

AIFACE-31  Ownership summaries must preserve ownership semantics across package boundaries.

AIFACE-32  Capability summaries must preserve provenance and access restrictions.

AIFACE-33  Effect summaries must preserve observable effects.

AIFACE-34  Async summaries must preserve suspension semantics.

AIFACE-35  GPU summaries must preserve execution/storage-domain contracts.

AIFACE-36  Cross-target ABI differences must not be hidden.

AIFACE-37  .axif serialization is deterministic.

AIFACE-38  Semantic fingerprints participate in incremental invalidation.

AIFACE-39  ABI fingerprint changes invalidate ABI-dependent artifacts.

AIFACE-40  Public API changes invalidate dependent interface consumers.

AIFACE-41  Profile data is not part of semantic proof unless explicitly classified as optimization evidence.

AIFACE-42  .axif may be consumed without source code.

AIFACE-43  .axif must be independently verifiable.

AIFACE-44  LTO may use .axif summaries but cannot bypass compiler correctness validation.

AIFACE-45  AI consumers cannot inject facts into AxifDB.

AIFACE-46  Equivalent semantic interfaces should produce canonical equivalent representations.

AIFACE-47  Stale .axif artifacts must be detected rather than silently trusted.

AIFACE-48  Interface artifacts must not contain secrets.

AIFACE-49  Summary precision may be reduced across trust boundaries, but never strengthened without proof.

AIFACE-50  Separate compilation must remain semantically equivalent to whole-program compilation.
```

---

# 323.47. Definition of Done

BOOTSTRAP-323 hoàn thành khi:

1. Có binary `.axif` format.
2. Có canonical serialization.
3. Có deterministic encoding.
4. Có public declaration table.
5. Có type table.
6. Có trait table.
7. Có generic constraints.
8. Có ownership summaries.
9. Có capability summaries.
10. Có effect summaries.
11. Có escape summaries.
12. Có alias summaries.
13. Có concurrency summaries.
14. Có async summaries.
15. Có GPU summaries.
16. Có FFI contracts.
17. Có ABI contracts.
18. Có dynamic-boundary metadata.
19. Có semantic certificates.
20. Có fingerprint hierarchy.
21. Có compatibility checker.
22. Có incremental invalidation.
23. Có thin/full interface modes.
24. Có cross-target interface support.
25. Có LTO integration.
26. Có package-manager integration.
27. Có ProfileDB integration nhưng giữ profile là optimization evidence.
28. Có AxifDB trong CompilerDB.
29. Có AI query interface.
30. Có verifier độc lập cho `.axif`.
31. Có test source-build vs `.axif`-only build.
32. Có test stale `.axif`.
33. Có test ABI mismatch.
34. Có test semantic-summary mismatch.
35. Có test malicious/corrupted `.axif`.
36. Có test private-information leakage.
37. Có test incremental rebuild.
38. Có test separate compilation vs whole-program compilation.
39. Có test LTO sử dụng `.axif`.
40. Không cần source dependency để compiler có thể type-check và optimize các API đã được đóng gói trong `.axif`.

---

## Nguyên tắc đóng băng của 323

> **`.axif` là "bộ nhớ semantic" của compiler giữa các lần biên dịch.**

Axiom từ đây có thể hình thành một kiến trúc rất mạnh:

```text
                 AXIOM SOURCE
                      │
                      ▼
               Semantic Analysis
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     .axif semantic          .axo machine
     knowledge               implementation
          │                       │
          └───────────┬───────────┘
                      ▼
                Whole Program
                   Analysis
                      │
             + ProfileDB
                      │
                      ▼
              Adaptive Optimizer
                      │
                      ▼
              Verified Native Code
```

Điểm đặc biệt là **compiler không còn phải lựa chọn giữa “recompile toàn bộ” và “không biết gì về dependency”**. Nó có thể giữ lại tri thức semantic đã được chứng minh dưới dạng `.axif`, đúng với mục tiêu ban đầu của Axiom: compiler đủ thông minh để xử lý phần phức tạp, trong khi lập trình viên không phải gánh complexity đó.