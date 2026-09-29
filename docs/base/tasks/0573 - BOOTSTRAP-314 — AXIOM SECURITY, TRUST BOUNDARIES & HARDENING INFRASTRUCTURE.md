# BOOTSTRAP-314 — AXIOM SECURITY, TRUST BOUNDARIES & HARDENING INFRASTRUCTURE

## 1. Mục tiêu

Thiết kế **mô hình bảo mật thống nhất của Axiom**, bao phủ:

- Safe code
- `unsafe`
- FFI
- Comptime
- Package/dependency
- Build system
- Compiler
- Runtime
- Generated code
- Native executable
- Debugger/profiler
- GPU/device code
- Supply-chain và reproducible build

Mục tiêu quan trọng:

> **Axiom không coi “memory safe” là toàn bộ security.**  
> Compiler phải duy trì các trust boundary rõ ràng giữa phần được chứng minh, phần do programmer cam kết, và phần đến từ bên ngoài.

Security không được biến thành một runtime bắt buộc hoặc làm chậm safe code.

---

# 2. Security Model tổng thể

Axiom chia hệ thống thành 5 mức trust:

```text
┌──────────────────────────────┐
│ Verified Safe Semantic Code  │
│ compiler proves invariants   │
└──────────────┬───────────────┘
               │ explicit contract
┌──────────────▼───────────────┐
│ Trusted Unsafe Boundary      │
│ programmer establishes facts │
└──────────────┬───────────────┘
               │ ABI / external contract
┌──────────────▼───────────────┐
│ Foreign / External Boundary  │
│ C ABI / OS / device / input  │
└──────────────┬───────────────┘
               │ capability
┌──────────────▼───────────────┐
│ Build / Comptime / Package   │
│ external execution/input     │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│ Host / OS / Hardware         │
└──────────────────────────────┘
```

Mỗi boundary phải có:

- explicit contract
- provenance
- capability
- validation
- diagnostic
- audit trail nếu cần

Không có khái niệm:

> “đã vào unsafe thì compiler bỏ kiểm tra.”

---

# 3. Security invariants

Các invariant mới:

### `ASEC-20`
Safe code cannot directly perform an operation classified as unsafe.

### `ASEC-21`
Unsafe code cannot silently weaken already-established safe invariants.

### `ASEC-22`
Every unsafe boundary has a statically identifiable source location.

### `ASEC-23`
Foreign values enter Axiom only through an explicit ABI boundary.

### `ASEC-24`
External data is never implicitly trusted as a valid Axiom value.

### `ASEC-25`
Comptime external capabilities are explicit and tracked.

### `ASEC-26`
Generated code must pass the same semantic verification pipeline as handwritten code.

### `ASEC-27`
Package dependencies cannot silently introduce compiler/runtime capabilities.

### `ASEC-28`
Build scripts cannot obtain arbitrary host capabilities unless explicitly granted.

### `ASEC-29`
Security configuration must not alter Core language semantics.

### `ASEC-30`
Debug/profiling instrumentation cannot silently weaken memory or concurrency guarantees.

### `ASEC-31`
Security-hardening transformations must preserve observable program semantics.

### `ASEC-32`
Security-sensitive compiler assumptions must be represented explicitly in IR metadata.

### `ASEC-33`
Unknown security state must never be interpreted as trusted.

### `ASEC-34`
Unsafe contracts must be auditable independently of optimization level.

### `ASEC-35`
Reproducible builds must produce identical semantic artifacts for identical declared inputs.

---

# 4. Unsafe model

Axiom `unsafe` is a **trust boundary**, not a second language.

Ví dụ:

```axiom
unsafe {
    let p: *mut u32 = address_of(buffer)
    *p = 42
}
```

Compiler vẫn kiểm tra:

- type correctness
- control flow
- instruction validity
- ABI
- initialization
- layout
- target constraints

Nhưng programmer chịu trách nhiệm cho các invariant mà compiler không thể chứng minh:

- pointer validity
- alignment
- lifetime
- provenance
- aliasing
- hardware constraints
- external API contracts

---

# 5. Unsafe contract

Axiom bổ sung metadata nội bộ:

```text
UnsafeContract {
    required_facts
    established_facts
    affected_regions
    affected_types
    affected_execution_domains
    affected_storage_domains
}
```

Ví dụ:

```text
required:
    ptr != null
    ptr aligned(4)
    region contains 4 bytes
    region writable

establishes:
    writable<T>
```

Sau đó compiler tiếp tục verification bình thường.

Điểm rất quan trọng:

> `unsafe` chỉ được phép **thiết lập các fact được khai báo**, không được phép biến mọi thứ phía sau thành “trusted”.

---

# 6. Unsafe audit system

Compiler phải có khả năng:

```text
axiom audit unsafe
```

và trả về:

```text
Unsafe Boundary #17

file: memory.axm
line: 84

operation:
    raw pointer dereference

required:
    alignment
    valid provenance
    initialized memory
    writable region

established by:
    unsafe contract #17

callers:
    Buffer<T>.write
    Image::set_pixel
```

Có thể tạo:

```text
unsafe-report.json
```

để AI/CI/security tooling phân tích.

---

# 7. FFI security boundary

FFI là một trust boundary độc lập với `unsafe`.

Ví dụ:

```axiom
extern "C" fn memcpy(
    dst: *mut u8,
    src: *const u8,
    size: usize
)
```

Compiler không tự giả định:

- pointer hợp lệ
- size hợp lệ
- function không panic
- function không giữ pointer
- function không mutate global state

FFI contract phải mô tả những gì biết được:

```text
ABI
calling convention
ownership
aliasing
effects
thread safety
panic behavior
return validity
```

---

# 8. FFI contract

Mô hình:

```text
FfiContract {
    abi
    inputs
    outputs
    ownership
    borrowing
    effects
    panic_behavior
    thread_behavior
    async_behavior
    layout
}
```

Ví dụ:

```text
@ffi_safe
@noescape(dst)
@noescape(src)
@readonly(src)
@writes(dst)
extern "C" fn ...
```

Các annotation này là **contract compiler-level**, không phải runtime checks.

---

# 9. Foreign data validation

Không được phép:

```text
C bytes → cast → arbitrary Axiom struct
```

một cách an toàn.

Thay vào đó:

```text
foreign bytes
      ↓
validation
      ↓
validated representation
      ↓
Axiom value
```

Đặc biệt với:

- network packet
- file format
- serialized data
- IPC
- device memory
- OS structures

Memory representation và wire representation vẫn là hai khái niệm riêng.

---

# 10. Comptime security

Comptime có quyền mạnh hơn runtime code vì nó chạy trong compiler.

Do đó mọi external capability phải được tracking:

```text
ReadSource
ReadMetadata
ReadFilesystem
WriteGenerated
ExecuteTool
Environment
Network
Time
Random
```

Compiler tạo:

```text
ComptimeCapabilityGraph
```

Ví dụ:

```text
package A
 └─ comptime fn generate()
      ├─ ReadFilesystem
      └─ Environment
```

Build system có thể từ chối:

```text
--deny-comptime-network
--deny-comptime-exec
```

---

# 11. Comptime sandbox

Mặc định:

```text
Comptime = sandboxed
```

Không tự động có:

- filesystem write
- process execution
- network
- environment secrets
- arbitrary OS access

Một project muốn dùng phải khai báo capability.

Ví dụ:

```text
comptime-capabilities:
    read-filesystem
    write-generated
```

Build graph đưa capability vào semantic/build fingerprint.

Do đó thay đổi capability cũng có thể invalidate cache.

---

# 12. Package security

Package metadata bổ sung:

```text
PackageSecurity {
    source
    version
    checksum
    publisher
    signature
    dependencies
    capabilities
    comptime_capabilities
    build_capabilities
}
```

Package không được âm thầm yêu cầu:

```text
execute-process
network
filesystem-write
```

mà build system không biết.

---

# 13. Dependency capability propagation

Ví dụ:

```text
App
 └── LibraryA
      └── LibraryB
           └── comptime network
```

Build system phải hiển thị:

```text
App
 └─ LibraryA
     └─ LibraryB
         └─ requires: Network
```

Không được che capability qua dependency chain.

---

# 14. Build security

Build action được mô hình hóa:

```text
BuildAction {
    inputs
    outputs
    capabilities
    environment
    tools
    target
    reproducibility
}
```

Không cho phép build script tùy ý chạy:

```text
cmd.exe
powershell
bash
python
```

mà không qua capability boundary.

Trong bootstrap có thể cho phép rộng hơn, nhưng production/self-hosted toolchain phải có policy rõ ràng.

---

# 15. Compiler security

Compiler itself là trusted computing base.

Compiler phải có:

```text
CompilerIntegrity
CompilerProvenance
SemanticVersion
TargetSpecHash
SourceHash
BuildEnvironmentHash
```

Compiler binary có thể phát hành kèm:

```text
compiler-manifest
compiler-source-revision
semantic-version
target
build-id
```

Mục tiêu:

> Có thể xác định executable được tạo bởi compiler nào và từ input nào.

---

# 16. Reproducible build security

Hai build:

```text
Build A
Build B
```

với cùng:

```text
source
dependencies
compiler semantic version
target
features
comptime inputs
build configuration
```

phải có cùng semantic result.

Artifact byte-identical là mục tiêu mạnh khi target/build policy cho phép.

Nếu khác:

```text
axiom explain-reproducibility
```

phải chỉ ra nguyên nhân.

---

# 17. Supply-chain security

Build graph phải có provenance:

```text
Executable
 ├── source files
 ├── generated source
 ├── packages
 ├── object files
 ├── runtime components
 ├── compiler
 └── linker
```

Có thể xuất:

```text
axiom provenance
```

thành machine-readable format.

Mục tiêu là trả lời:

> “Executable này được tạo từ những gì?”

---

# 18. Generated code security

Comptime/generated code:

```text
Generated HIR
      ↓
Resolver
      ↓
Type checker
      ↓
Ownership
      ↓
Capability
      ↓
Effect
      ↓
Concurrency
      ↓
ABI
      ↓
Verified MIR
```

Không có đường tắt:

```text
generated code → machine code
```

Điều này đặc biệt quan trọng với AI-generated Axiom code.

---

# 19. AI-generated code

Axiom compiler có thể gắn provenance:

```text
SourceOrigin {
    Human
    Generated
    Comptime
    MacroLike
    External
    Imported
}
```

AI-generated code **không được trust hơn code thường**.

Compiler có thể cung cấp:

```text
axiom explain-security file.axm
```

với:

```text
unsafe boundaries
FFI boundaries
external capabilities
comptime capabilities
external dependencies
generated regions
security-sensitive operations
```

---

# 20. Secret handling

Compiler/build system không được vô tình đưa secrets vào:

- diagnostics
- generated source
- cache key
- build logs
- package metadata
- reproducibility manifest
- debug information

Environment capability phải phân biệt:

```text
EnvironmentMetadata
EnvironmentSecret
```

Secret không được trở thành dependency fingerprint raw.

Thay vào đó sử dụng:

```text
SecretPresenceHash
```

hoặc capability-specific redacted identity.

---

# 21. Debugger security

Debugger có quyền quan sát rất mạnh nhưng không được biến debug build thành semantic khác.

Debug mode có thể bật:

- bounds instrumentation
- ownership tracking
- race detection
- allocation tracing
- memory poisoning

nhưng các instrumentation này phải:

```text
observable only through debugging/tooling
```

và không được làm thay đổi language semantics.

---

# 22. Sanitizer architecture

Axiom sanitizer framework:

```text
Sanitizer
├── Address
├── Bounds
├── Initialization
├── Ownership
├── DataRace
├── Thread
├── Integer
├── Float
├── ControlFlow
└── FFI
```

Sanitizer là tooling/runtime instrumentation.

Không được dùng sanitizer để “thay thế” compiler verifier.

Ví dụ:

```text
safe use-after-free
```

phải bị compiler reject trước khi sanitizer có cơ hội chạy.

---

# 23. Constant-time security

Crypto-sensitive code cần security contract:

```text
@constant_time
fn ...
```

Compiler phải hạn chế các transformation có thể tạo timing dependency từ secret.

Metadata:

```text
Secret
Public
```

được theo dõi trong security-sensitive optimization.

Không cho phép optimizer tự biến:

```text
secret-dependent branch
```

thành một dạng không đáp ứng contract.

Đây là security contract riêng, không phải memory safety.

---

# 24. Control-flow hardening

Target backend có thể hỗ trợ:

- stack canary
- CFI
- shadow stack
- CET
- PAC
- BTI
- branch hardening
- return-address protection

nhưng phải được biểu diễn qua:

```text
SecurityTargetFeatures
```

chứ không nhúng vào Core language semantics.

---

# 25. Memory hardening

Có thể hỗ trợ theo profile:

```text
ASLR
NX/W^X
RELRO
stack protection
heap hardening
guard pages
pointer authentication
memory tagging
```

Axiom compiler/linker/image writer phối hợp nhưng không yêu cầu tất cả target phải có.

---

# 26. GPU security

GPU thêm security domains:

```text
Host
Device
Shared
External
```

Không được:

```text
Host pointer
    ↓ implicit
Device pointer
```

hoặc ngược lại.

External/device resources phải có contract về:

- ownership
- lifetime
- synchronization
- address space
- access
- device identity

---

# 27. Security metadata trong IR

MIR/LIR cần metadata:

```text
SecurityFact {
    Provenance
    TrustLevel
    Secretness
    FfiBoundary
    UnsafeBoundary
    ExternalOrigin
    CapabilityOrigin
    ConstantTime
}
```

Tuy nhiên:

> Security metadata không được biến thành semantic escape hatch.

Optimization chỉ được sử dụng fact nếu fact đã được verifier chứng minh.

---

# 28. Security-aware optimization

Optimizer có thể sử dụng:

```text
proven-safe
no-secret-dependency
no-ffi-side-effect
no-alias
constant-time
trusted-input
```

nhưng:

```text
UNKNOWN ≠ SAFE
UNKNOWN ≠ PUBLIC
UNKNOWN ≠ NOALIAS
UNKNOWN ≠ CONSTANT_TIME
```

Đây là nguyên tắc cực kỳ quan trọng.

---

# 29. Security levels

Axiom không tạo nhiều ngôn ngữ.

Thay vào đó build profile:

```text
security = normal
security = hardened
security = paranoid
```

Ví dụ:

### normal

- standard checks
- ordinary optimization

### hardened

- extra stack protection
- CFI
- sanitizer options
- stricter FFI checks
- dependency verification

### paranoid

- reproducibility requirements
- stricter unsafe policy
- restricted comptime capabilities
- restricted external build actions
- stronger hardening

Core semantics vẫn giống nhau.

---

# 30. Security policy

Project có thể khai báo:

```text
security-policy.axm
```

Ví dụ policy concept:

```text
deny unsafe
deny ffi
deny comptime-network
deny build-exec
require signed-packages
require reproducible
require constant-time-crypto
```

Compiler biến policy violation thành structured diagnostic.

---

# 31. Security CI

CI có thể chạy:

```text
axiom check
axiom audit unsafe
axiom audit ffi
axiom audit dependencies
axiom audit comptime
axiom verify reproducibility
axiom test --sanitizers
axiom build --hardened
```

Kết quả machine-readable để CI/AI xử lý.

---

# 32. Threat model

Axiom security specification phải phân biệt:

### Compiler bugs

Ví dụ:

```text
compiler incorrectly accepts invalid ownership
```

Đây là compiler correctness failure.

### Unsafe programmer error

```text
unsafe pointer contract sai
```

Không phải compiler bug nếu compiler đã thực hiện đúng contract.

### FFI contract violation

```text
foreign library phá contract
```

là external trust failure.

### Malicious package

```text
package cố tình chạy build command
```

phải bị capability/package policy kiểm soát.

### Compromised compiler

Đây là TCB compromise và cần bootstrap/reproducibility/provenance để phát hiện hoặc giảm rủi ro.

---

# 33. Trust Boundary Graph

Compiler tạo graph:

```text
Program
 │
 ├── Safe
 │
 ├── Unsafe
 │
 ├── FFI
 │
 ├── Comptime
 │    └── Filesystem
 │    └── Network
 │
 ├── Dependency
 │
 ├── Generated
 │
 ├── Runtime
 │
 └── Device/GPU
```

API:

```text
get_security_graph()
explain_security_boundary()
get_unsafe_contracts()
get_external_capabilities()
get_security_dependencies()
```

Các API này dùng chung cho:

- IDE
- LSP
- AI agent
- CI
- security audit tools

---

# 34. Compiler implementation

Thêm:

```text
compiler/security/
├── policy/
├── trust/
├── unsafe/
├── ffi/
├── comptime/
├── dependency/
├── provenance/
├── secret/
├── constant_time/
├── hardening/
├── sanitizer/
├── audit/
└── diagnostics/
```

CompilerDB thêm:

```text
SecurityDB
TrustDB
SecurityPolicyDB
ProvenanceDB
```

---

# 35. Security query API

Compiler native API:

```text
get_security_graph()
get_security_boundaries()
get_unsafe_operations()
get_unsafe_contract()
get_ffi_contract()
get_external_capabilities()
get_dependency_capabilities()
get_provenance()
get_secret_flows()
get_constant_time_constraints()
explain_security()
```

AI agent có thể hỏi compiler:

> “Đoạn code này cần trust assumption nào?”

thay vì tự phân tích source một cách không đáng tin cậy.

---

# 36. Definition of Done

BOOTSTRAP-314 hoàn thành khi Axiom có:

1. Unified security/trust model.
2. Explicit unsafe boundaries.
3. Unsafe contracts.
4. FFI security contracts.
5. Comptime capability security.
6. Package capability propagation.
7. Build capability sandbox.
8. Compiler provenance.
9. Reproducible-build security model.
10. Generated-code trust model.
11. Secret-handling rules.
12. Constant-time contract.
13. Security-aware optimizer constraints.
14. Target hardening framework.
15. GPU security domains.
16. Sanitizer architecture.
17. Security policy system.
18. Security CI/audit commands.
19. Security graph.
20. AI/compiler security query API.
21. Security metadata in IR.
22. Structured security diagnostics.
23. No mandatory runtime overhead for ordinary safe code.
24. No semantic difference between normal and hardened builds.

### Nguyên tắc đóng băng

> **Axiom compiler phải chứng minh được cái gì nó biết; programmer phải khai báo cái gì compiler không thể chứng minh; external world phải được coi là không đáng tin cho đến khi có contract/validation tương ứng.**

Đây là ranh giới để Axiom vừa giữ được **hiệu năng native**, vừa không biến `unsafe`, FFI, comptime và AI-generated code thành những “lỗ hổng ngầm” trong mô hình ngôn ngữ.