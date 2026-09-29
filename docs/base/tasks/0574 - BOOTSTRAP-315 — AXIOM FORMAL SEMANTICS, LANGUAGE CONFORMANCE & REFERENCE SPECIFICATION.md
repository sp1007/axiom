# BOOTSTRAP-315 — AXIOM FORMAL SEMANTICS, LANGUAGE CONFORMANCE & REFERENCE SPECIFICATION

## 1. Mục tiêu

Sau khi đã có:

- Core language semantics
- Memory/ownership/capability model
- Concurrency/async/GPU
- Type system
- Compiler IR
- Verification
- Optimization
- ABI/FFI
- Runtime
- Toolchain
- Testing
- Self-hosting
- IDE/debugger
- Security

Axiom cần một **nguồn sự thật chuẩn tắc (normative source of truth)** để xác định chính xác:

> Một chương trình Axiom **có nghĩa gì**, compiler **được phép làm gì**, và implementation nào được coi là **đúng chuẩn Axiom**.

BOOTSTRAP-315 không thiết kế thêm feature ngôn ngữ. Nó đóng vai trò **hợp nhất và chuẩn hóa toàn bộ semantics đã đóng băng** thành một specification có thể dùng để:

- implement compiler;
- viết reference interpreter;
- viết test suite;
- kiểm chứng optimizer;
- kiểm chứng compiler self-hosted;
- kiểm chứng compiler độc lập của bên thứ ba;
- xác định compatibility giữa các phiên bản Axiom.

---

# 2. Nguyên tắc tối cao

Axiom có ba tầng specification:

```text
Axiom Language Specification
        │
        ├── Normative Semantics
        │
        ├── Implementation Requirements
        │
        └── Implementation Extensions
```

### Normative Semantics

Quy định chương trình **phải có nghĩa gì**.

### Implementation Requirements

Quy định compiler conforming phải làm được gì.

### Extensions

Tính năng implementation-specific không được làm thay đổi semantics Core.

---

# 3. Không dùng compiler làm định nghĩa semantics

Một nguyên tắc rất quan trọng:

> Compiler hiện tại không phải là specification.

Không được định nghĩa:

```text
“Axiom làm X vì compiler hiện tại làm X.”
```

Thay vào đó:

```text
Specification
      ↓
Reference semantics
      ↓
Compiler implementation
```

Nếu compiler sai specification thì:

> compiler sai.

Không được sửa specification chỉ để hợp thức hóa compiler bug.

---

# 4. Semantic Layers

Specification chính thức chia thành:

```text
L0 Lexical
L1 Syntax
L2 Names & Modules
L3 Types
L4 Values
L5 Evaluation
L6 Ownership
L7 Capability
L8 Effects
L9 Concurrency
L10 Async
L11 GPU
L12 Comptime
L13 FFI / ABI
L14 Memory Model
L15 Observable Behavior
L16 Diagnostics
L17 Compilation
```

Mỗi tầng chỉ được phụ thuộc vào các tầng thấp hơn hoặc các dependency được khai báo rõ.

---

# 5. Semantic Objects

Specification định nghĩa các semantic object chuẩn:

```text
Program
Package
Module
Declaration
Type
Value
Place
Region
Capability
Effect
ExecutionDomain
StorageDomain
Thread
Task
Future
ComptimeValue
ForeignValue
ABIValue
```

Các object này phải có định nghĩa độc lập với implementation.

Ví dụ:

```text
Place
```

không đồng nghĩa với:

```text
register
stack address
heap address
machine pointer
```

Đây là semantic location, không phải physical location.

---

# 6. Evaluation Semantics

Axiom cần quy định chính xác evaluation order.

Ví dụ:

```axiom
f(a(), b())
```

Specification phải xác định:

- `f` được resolve khi nào;
- `a()` và `b()` được evaluate theo thứ tự nào;
- side effect nào xảy ra trước;
- panic/trap xảy ra ở đâu;
- Move/Copy xảy ra lúc nào;
- Drop xảy ra khi nào.

Không để compiler tự chọn thứ tự nếu observable behavior có thể thay đổi.

---

# 7. Observable Behavior

Specification định nghĩa:

```text
ObservableBehavior
```

bao gồm những thứ chương trình được phép quan sát:

- giá trị trả về;
- output;
- I/O;
- atomic synchronization;
- synchronization ordering;
- panic/trap;
- allocation failure khi được expose;
- FFI effects;
- volatile access;
- timing/security contracts trong phạm vi đã khai báo;
- process/environment interaction.

Ngược lại:

```text
register allocation
stack vs heap
instruction ordering
temporary objects
SSA form
MIR representation
```

không phải observable behavior nếu language không expose chúng.

---

# 8. As-if Rule

Compiler được phép biến đổi chương trình tùy ý nếu:

```text
ObservableBehavior(original)
==
ObservableBehavior(transformed)
```

và mọi semantic invariant vẫn được bảo toàn.

Do đó:

```text
source
 ↓
MIR
 ↓
optimized MIR
 ↓
machine code
```

không cần giữ nguyên cấu trúc.

Nhưng không được biến:

```text
defined behavior
```

thành:

```text
undefined behavior
```

chỉ vì optimization.

---

# 9. Undefined Behavior Policy

Axiom Core **hạn chế tối đa undefined behavior**.

Phân loại:

```text
WellDefined
CompileError
RuntimeFailure
Panic
Trap
UnsafeContractViolation
ForeignContractViolation
ImplementationDefined
TargetDefined
Unspecified
```

Không dùng một nhãn `undefined behavior` chung cho mọi trường hợp.

Đặc biệt:

> Safe Axiom program không được phụ thuộc vào UB để đạt hiệu năng.

---

# 10. Compile-time vs Runtime Semantics

Mỗi operation được đánh dấu:

```text
CompileTime
Runtime
Either
```

Ví dụ:

```text
size_of<T>()
```

là compile-time semantic operation.

Optimizer có thể constant-fold runtime expression nhưng điều đó **không biến expression thành compile-time semantic operation**.

Điểm này bảo đảm phân biệt:

```text
language guarantee
```

với:

```text
optimization accident
```

---

# 11. Ownership Semantics chuẩn

Specification phải định nghĩa ownership bằng semantic transition.

Ví dụ:

```text
Owned(x)
   │
   ├── Copy ──→ Owned(x) + Owned(y)
   │
   ├── Move ──→ Moved(x) + Owned(y)
   │
   ├── Drop ──→ Dropped(x)
   │
   └── Borrow/view ──→ Owned(x) + Capability(y)
```

Không định nghĩa Move bằng physical memcpy.

Move có thể compile thành:

```text
register transfer
pointer transfer
no machine instruction
```

nếu semantics vẫn đúng.

---

# 12. Capability Semantics

Specification chính thức hóa:

```text
Capability {
    provenance
    region
    access
    validity
    lifetime
    storage_domain
}
```

Các capability cơ bản:

```text
READ
WRITE
MOVE
DROP
```

và semantic views:

```text
view<T>
mut_view<T>
```

Quy tắc conflict phải được định nghĩa normative:

```text
READ + READ       = allowed
READ + WRITE      = conflict
WRITE + WRITE     = conflict
MOVE + anything   = conflict
DROP + live use   = conflict
```

trừ khi region relation chứng minh chúng không overlap.

---

# 13. Memory Model

Memory model chính thức phải định nghĩa:

```text
sequenced-before
synchronizes-with
happens-before
atomic modification order
```

và:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không để backend CPU quyết định semantics.

Ví dụ:

```text
x.store(1, Release)
```

phải có cùng semantic meaning trên:

- x86-64
- ARM64
- RISC-V
- WASM

dù machine instruction hoàn toàn khác nhau.

---

# 14. Data Race Definition

Specification định nghĩa chính xác:

> Data race là gì?

Ví dụ hai execution:

```text
Thread A: WRITE x
Thread B: READ x
```

nếu không có synchronization phù hợp và cùng access region thì:

```text
safe program = rejected
```

Compiler không được dựa vào:

```text
“CPU này thường chạy đúng.”
```

để chấp nhận chương trình.

---

# 15. Concurrency Semantics

Các khái niệm phải được chuẩn hóa:

```text
Send
Share
Atomic
Mutex
RwLock
Channel
Thread
Task
Executor
```

Đặc biệt:

```text
Send != Share
Share != mutable sharing
```

và:

```text
channel send → receive
mutex unlock → lock
thread completion → join
```

phải tạo ra synchronization relationship chuẩn.

---

# 16. Async Semantics

Specification định nghĩa:

```text
async fn
Future
Poll
Ready
Pending
await
Waker
cancellation
```

Một `async fn`:

```text
async fn foo() -> T
```

không có nghĩa:

```text
spawn thread
```

hay:

```text
execute immediately
```

Nó tạo Future semantic object.

Executor là implementation/runtime concern.

---

# 17. Suspension Semantics

Tại mỗi:

```text
await
```

specification xác định:

```text
SuspensionPoint
```

Các giá trị live across suspension phải tuân thủ:

- ownership;
- capability;
- storage;
- Send nếu task migration yêu cầu;
- guard restrictions.

Compiler có thể tối ưu state machine nhưng không được thay đổi semantics.

---

# 18. GPU Semantics

GPU được specification coi là execution/storage domain riêng.

```text
CPU
GPU
Device
Shared
Local
Private
External
```

Phải định nghĩa:

```text
kernel launch
completion
memory transfer
device ownership
GPU synchronization
atomic scope
```

Kernel không được tự động kế thừa mọi khả năng của host.

---

# 19. Comptime Semantics

Specification định nghĩa `comptime` như một execution environment có semantics riêng:

```text
comptime value
comptime execution
comptime capability
comptime external input
```

Compiler implementation có thể dùng:

- interpreter;
- bytecode VM;
- native execution;
- JIT;

nhưng kết quả semantic phải tương đương.

---

# 20. Determinism

Specification phải chia:

### Deterministic

```text
integer arithmetic
type checking
ownership
layout queries
compile-time pure computation
```

### Potentially nondeterministic

```text
thread scheduling
network
filesystem
random
time
external process
```

Comptime reproducible mode phải giới hạn nondeterminism.

---

# 21. ABI Semantics

ABI phải được định nghĩa ở tầng:

```text
Semantic ABI
      ↓
Representation ABI
      ↓
Target ABI
```

Ví dụ:

```text
Result<T,E>
```

không bị specification ép phải có một machine representation duy nhất.

ABI lowering quyết định:

- registers;
- stack;
- return registers;
- aggregate passing;
- alignment;
- calling convention.

---

# 22. Representation Independence

Specification phải phân biệt:

```text
Type identity
Value semantics
Representation
Layout
ABI
```

Ví dụ:

```text
struct Vec2 {
    x: f32
    y: f32
}
```

không mặc định có layout C-compatible.

Chỉ:

```text
@repr(C)
```

mới tạo representation contract tương ứng.

---

# 23. Optimization Legality

Mỗi optimization trong compiler phải có:

```text
Preconditions
Proof obligations
Transformation
Preserved properties
```

Ví dụ:

```text
BoundsCheckElimination
```

chỉ được áp dụng nếu compiler chứng minh:

```text
index < length
```

Không được áp dụng chỉ vì optimizer “nghĩ rằng” điều đó đúng.

---

# 24. Reference Semantics

Axiom cần có một **Reference Semantic Engine** độc lập với optimizer.

Pipeline:

```text
Axiom Source
    ↓
Parser
    ↓
Reference HIR
    ↓
Reference Semantic Evaluator
    ↓
Observable Result
```

Nó không cần nhanh.

Mục tiêu là:

> correctness oracle.

Compiler optimized:

```text
Axiom Compiler
    ↓
Machine Code
    ↓
Result
```

phải tương đương reference semantics.

---

# 25. Semantic Equivalence

Định nghĩa:

```text
P ≡ Q
```

nếu hai chương trình có cùng observable behavior trong cùng execution environment.

Đây là cơ sở cho:

- optimizer testing;
- MIR interpreter;
- compiler differential testing;
- self-host verification;
- independent compiler implementations.

---

# 26. Conformance Levels

Axiom định nghĩa:

### Level 0 — Parser Conformance

Đúng lexical/syntax.

### Level 1 — Semantic Conformance

Đúng:

- types
- ownership
- capability
- evaluation
- effects
- memory semantics

### Level 2 — Core Compiler Conformance

Có native compilation đúng semantic.

### Level 3 — Platform Conformance

Đúng ABI/target/platform.

### Level 4 — Toolchain Conformance

Đúng:

- package
- build
- diagnostics
- incremental
- debugger/IDE interfaces

### Level 5 — Full Axiom Conformance

Toàn bộ normative specification.

---

# 27. Feature Matrix

Compiler phải công bố:

```text
Axiom Implementation
      │
      ├── Core
      ├── Async
      ├── GPU
      ├── Comptime
      ├── FFI
      ├── ABI
      └── Target
```

Mỗi feature có trạng thái:

```text
Required
Optional
Experimental
Extension
Unsupported
```

Không được gọi compiler là “Axiom compliant” nếu thiếu một feature bắt buộc.

---

# 28. Versioning

Specification sử dụng semantic language version:

```text
Axiom 1.0
Axiom 1.1
Axiom 2.0
```

Phải phân biệt:

```text
Language semantic version
Compiler implementation version
Standard library version
ABI version
Package ecosystem version
```

Compiler patch version không được tự ý thay đổi language semantics.

---

# 29. Compatibility

Ba loại compatibility:

```text
Source Compatibility
Semantic Compatibility
ABI Compatibility
```

Ví dụ compiler mới có thể:

```text
source compatible = yes
ABI compatible = no
```

hoặc:

```text
source compatible = no
ABI compatible = yes
```

Không gộp tất cả thành một khái niệm “compatible”.

---

# 30. Conformance Test Suite

Specification tạo một test corpus chuẩn:

```text
conformance/
├── lexical/
├── parser/
├── types/
├── evaluation/
├── ownership/
├── capability/
├── effects/
├── memory/
├── concurrency/
├── async/
├── gpu/
├── comptime/
├── ffi/
├── abi/
├── optimization/
├── security/
└── diagnostics/
```

Mỗi test có:

```text
TestId
RequiredFeature
Source
ExpectedSemanticResult
ExpectedDiagnostic
TargetConstraints
```

---

# 31. Negative Conformance Tests

Không chỉ test chương trình hợp lệ.

Ví dụ:

```text
use-after-move
double-drop
invalid-view
overlapping-mut-view
data-race
invalid-await-guard
invalid-FFI-layout
invalid-comptime-capability
```

phải được kiểm tra compiler **reject**.

Điều này rất quan trọng:

> Compiler conforming không chỉ phải chấp nhận chương trình đúng; nó còn phải từ chối chương trình sai theo normative semantics.

---

# 32. Diagnostic Conformance

Diagnostic text không bắt buộc giống nhau.

Normative requirement là:

```text
DiagnosticCode
PrimarySpan
SemanticCategory
RequiredFacts
```

Compiler có thể render:

```text
Vietnamese
English
IDE UI
JSON
AI protocol
```

mà semantics không thay đổi.

---

# 33. Implementation-defined Behavior

Một số thứ không thể portable tuyệt đối:

```text
pointer width
endianness
ABI
alignment limits
available SIMD
GPU features
OS behavior
```

Specification phải yêu cầu implementation khai báo chúng.

Ví dụ:

```text
TargetSpec {
    architecture
    pointer_width
    endian
    abi
    object_format
    executable_format
    features
}
```

Không được âm thầm phụ thuộc.

---

# 34. Target-defined Behavior

Ví dụ:

```text
f32 hardware behavior
volatile semantics
trap behavior
FP environment
atomic width
```

phải được target specification mô tả.

Compiler không được giả định target nào cũng giống nhau.

---

# 35. Security Semantics

BOOTSTRAP-314 phải được đưa vào normative specification:

```text
unsafe
FFI
comptime capabilities
security contracts
constant-time
trust boundaries
```

Security policy implementation có thể khác nhau, nhưng các invariant Core không được phá vỡ.

---

# 36. Specification Machine-Readable

Đây là điểm đặc biệt quan trọng đối với Axiom.

Không chỉ có:

```text
axiom-language-spec.md
```

mà cần:

```text
spec/
├── lexical.axs
├── syntax.axs
├── types.axs
├── ownership.axs
├── capability.axs
├── memory.axs
├── concurrency.axs
├── async.axs
├── gpu.axs
├── comptime.axs
├── abi.axs
├── ffi.axs
├── security.axs
└── conformance.axs
```

`*.axs` là **machine-readable semantic specification format** của Axiom.

AI/compiler tooling có thể đọc trực tiếp.

---

# 37. Semantic Rule Format

Ví dụ concept:

```text
rule OWN-MOVE-001 {
    when:
        source.state == Owned
        destination.type == source.type

    transition:
        source.state := Moved
        destination.state := Owned

    invalid:
        source.read
        source.move
        source.drop

    unless:
        source.reinitialized
}
```

Mục tiêu là specification có thể trở thành input cho:

- test generator;
- verifier;
- documentation generator;
- AI reasoning tools.

---

# 38. Single Source of Truth

Từ semantic rule có thể sinh:

```text
Specification
     ↓
Reference interpreter rules
     ↓
Conformance tests
     ↓
Compiler verifier tests
     ↓
Documentation
     ↓
AI semantic database
```

Tránh tình trạng:

```text
spec nói A
compiler làm B
docs nói C
tests kiểm tra D
```

---

# 39. Semantic Fingerprint

Mỗi compiler build phải chứa:

```text
AxiomSemanticVersion
CoreSpecHash
ABIRevision
TargetSpecHash
FeatureSet
```

Ví dụ:

```text
AXIOM-SEMANTIC:
    version = 1.0
    core_hash = ...
    abi = ...
```

Build cache của compiler sử dụng semantic fingerprint này.

---

# 40. Compiler Conformance Mode

Compiler phải hỗ trợ:

```text
axiom conformance
```

và:

```text
axiom conformance --core
axiom conformance --target x86_64-linux
axiom conformance --abi c
axiom conformance --security
```

Output machine-readable:

```text
PASS
FAIL
UNSUPPORTED
IMPLEMENTATION_ERROR
SPEC_AMBIGUITY
```

---

# 41. Specification Ambiguity Detection

Một compiler không được tự ý chọn semantics khi specification chưa đủ rõ.

Nếu gặp:

```text
SPEC_AMBIGUITY
```

thì:

1. ghi nhận rule conflict;
2. tạo diagnostic cho compiler developer;
3. tạo test reproducer;
4. specification phải được sửa trước khi behavior trở thành normative.

Điều này đặc biệt quan trọng trong quá trình Axiom tiến tới self-hosting.

---

# 42. Formalization Roadmap

Không cần biến toàn bộ Axiom thành theorem prover ngay lập tức.

Phân tầng:

```text
Phase 1
Executable semantic rules

Phase 2
Reference interpreter

Phase 3
Property-based semantic validation

Phase 4
Machine-checkable invariants

Phase 5
Formal proofs cho critical components
```

Critical components ưu tiên:

1. ownership
2. capability
3. memory model
4. concurrency
5. ABI
6. unsafe boundary
7. optimizer legality

---

# 43. Compiler Bug Classification

Mỗi failure phải phân loại:

```text
SPEC_ERROR
PARSER_ERROR
RESOLVER_ERROR
TYPE_ERROR
VERIFIER_ERROR
OPTIMIZER_ERROR
CODEGEN_ERROR
ABI_ERROR
LINKER_ERROR
RUNTIME_ERROR
TOOLCHAIN_ERROR
TARGET_ERROR
USER_ERROR
FOREIGN_CONTRACT_VIOLATION
```

Điều này cho phép agent tự động tìm đúng subsystem thay vì sửa ngẫu nhiên compiler.

---

# 44. Implementation Tree

Thêm:

```text
spec/
├── normative/
├── semantic/
├── rules/
├── conformance/
├── targets/
├── abi/
├── security/
├── examples/
└── generated/

compiler/
└── semantics/
    ├── reference/
    ├── rules/
    ├── conformance/
    ├── equivalence/
    └── validation/
```

CompilerDB thêm:

```text
SpecDB
SemanticRuleDB
ConformanceDB
ReferenceSemanticsDB
```

---

# 45. Definition of Done

BOOTSTRAP-315 hoàn thành khi Axiom có:

1. Normative language specification.
2. Layered semantic model.
3. Formal observable-behavior definition.
4. Explicit evaluation semantics.
5. Ownership semantic transitions.
6. Capability semantic rules.
7. Memory model specification.
8. Concurrency memory-order semantics.
9. Async semantics.
10. GPU execution/storage semantics.
11. Comptime semantics.
12. ABI/representation separation.
13. Unsafe/FFI semantics.
14. Security semantics.
15. Optimization legality model.
16. Reference semantic engine.
17. Semantic equivalence framework.
18. Conformance levels.
19. Positive/negative conformance suites.
20. Diagnostic conformance model.
21. Target-defined behavior model.
22. Machine-readable semantic specification.
23. Semantic fingerprint/versioning.
24. Compiler conformance mode.
25. Specification ambiguity detection.
26. Compiler bug classification.
27. Foundation for machine-checkable formal proofs.

---

## Nguyên tắc đóng băng

> **Specification định nghĩa Axiom. Compiler thực thi specification. Reference semantics kiểm chứng compiler. Conformance suite kiểm chứng implementation. Optimizer không bao giờ được trở thành nguồn định nghĩa semantics.**

Đây sẽ là lớp đặc biệt quan trọng cho mục tiêu **self-hosting + nhiều compiler/AI agent cùng phát triển Axiom**: mọi agent có thể dựa vào cùng một semantic source of truth thay vì tự diễn giải ngôn ngữ theo cách riêng.