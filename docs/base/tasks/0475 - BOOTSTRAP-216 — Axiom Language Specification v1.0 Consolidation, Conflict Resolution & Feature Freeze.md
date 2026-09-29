# BOOTSTRAP-216 — Axiom Language Specification v1.0: Consolidation, Conflict Resolution & Feature Freeze

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là bước **không thêm tính năng mới một cách tùy tiện**. Mục tiêu là biến toàn bộ kiến trúc đã thiết kế thành một specification có thứ bậc rõ ràng, để khi implementation bắt đầu, agent/compiler không tự diễn giải khác nhau.

---

# 216.1. Specification hierarchy

Axiom v1.0 được chia thành 5 tầng:

```text
Axiom Specification
│
├── 1. Language Core
│      ├── Syntax
│      ├── Types
│      ├── Values
│      ├── Ownership
│      ├── Capabilities
│      ├── Control Flow
│      ├── Effects
│      ├── Concurrency
│      ├── Async
│      ├── Comptime
│      └── Unsafe
│
├── 2. Compiler Contract
│      ├── MIR
│      ├── Verification
│      ├── Optimization
│      ├── ABI lowering
│      └── Diagnostics
│
├── 3. Platform/System
│      ├── FFI
│      ├── OS
│      ├── GPU
│      ├── Freestanding
│      └── Native targets
│
├── 4. Standard Library
│      ├── Collections
│      ├── IO
│      ├── Networking
│      ├── Math
│      ├── Tensor
│      └── GUI/Graphics...
│
└── 5. Tooling
       ├── Package manager
       ├── IDE
       ├── AI interface
       ├── Debugger
       └── Build/distribution
```

Điểm quan trọng:

> **Không được để Standard Library hoặc Compiler Implementation ngược lại định nghĩa Core Language.**

---

# 216.2. Core phải nhỏ hơn toàn bộ Axiom

Axiom có thể rất lớn về ecosystem nhưng Core vẫn chỉ chứa những semantic primitive thực sự cần thiết.

Ví dụ:

```text
view<T>
mut_view<T>
```

là Core semantic primitives.

Nhưng:

```text
Vec<T>
HashMap<K,V>
TcpStream
Tensor<T>
Window
```

không phải Core.

---

# 216.3. Compiler complexity không phải language complexity

Một tính năng có thể khiến compiler rất phức tạp nhưng programmer vẫn không cần biết.

Ví dụ:

```text
ownership inference
escape analysis
alias analysis
lifetime inference
allocation elimination
vectorization
specialization
```

được compiler xử lý.

Không biến chúng thành annotation bắt buộc.

---

# 216.4. Explicit semantic boundaries

Ngược lại, những thứ có thể thay đổi observable behavior phải explicit.

Ví dụ:

```text
unsafe
async
spawn
atomic
FFI
GPU transfer
fast-math
stable ABI
serialization
```

---

# 216.5. Precedence rules

Nếu hai rule xung đột, thứ tự ưu tiên:

```text
1. Memory / type / ownership safety
2. Observable semantics
3. Explicit programmer contract
4. ABI/platform contract
5. Optimization freedom
6. Compiler implementation heuristic
```

Không được dùng optimization để phá semantic rule.

---

# 216.6. Safety vs optimization

Nếu compiler không chứng minh được optimization an toàn:

```text
DO NOT OPTIMIZE
```

Không được:

```text
ASSUME SAFE
```

---

# 216.7. Explicit contract vs inference

Nếu programmer cung cấp contract:

```text
@repr(C)
@abi(stable)
@target_feature(...)
@constant_time
```

compiler phải tuân thủ contract.

Nếu không có contract, compiler được tự tối ưu trong semantic freedom.

---

# 216.8. Core language freeze

Axiom v1.0 Core không bao gồm:

```text
GC
class
inheritance
exceptions
runtime reflection
mandatory runtime
mandatory heap
mandatory pointer syntax
borrow annotations
lifetime annotations
macro language
```

---

# 216.9. Core ownership model

Chính thức:

```text
Value
Ownership
Move
Copy
Clone
Drop
```

là sáu khái niệm nền tảng.

---

# 216.10. Core access model

Chính thức:

```text
value
view<T>
mut_view<T>
raw pointer (unsafe)
```

Không có general:

```text
&T
&mut T
T&
T&&
```

ở safe Core.

---

# 216.11. Pointer model

Safe programmer thường không cần biết pointer.

System programmer có:

```text
*const T
*mut T
```

trong `unsafe`.

---

# 216.12. Memory model

Axiom v1.0 chính thức sử dụng:

```text
value semantics
+
ownership
+
capability
+
deterministic lifetime
+
explicit unsafe
```

Không sử dụng:

```text
GC
implicit reference counting
borrow checker syntax
```

---

# 216.13. Flat memory model — clarification

Axiom **không định nghĩa "flat memory" như allocator strategy**.

Semantic model là:

```text
logical storage
```

Backend có thể sử dụng:

```text
stack
register
heap
arena
pool
static
mapped
device
```

---

# 216.14. Allocation semantics

Allocation là effect/storage operation.

Compiler có quyền eliminate allocation nếu:

```text
address does not escape
identity not observable
resource semantics preserved
```

---

# 216.15. No hidden allocation guarantee

Axiom không cho phép API high-level âm thầm hứa:

```text
zero allocation
```

trừ khi contract/API chỉ rõ.

Tooling có thể inspect allocation behavior.

---

# 216.16. Collection boundary

Core:

```text
Array
view
mut_view
```

Library:

```text
Vec
Deque
HashMap
BTreeMap
SmallVec
Arena
```

---

# 216.17. String boundary

Core semantic primitives:

```text
UTF-8 validity
char
view
bytes
```

Library types:

```text
String
Str
Bytes
Path
CStr
```

---

# 216.18. Error model

Axiom v1.0 chính thức:

```text
Option
Result
panic
never
```

Không có mandatory exception system.

---

# 216.19. Panic policy

Panic implementation là profile:

```text
abort
unwind
custom
```

nhưng semantic distinction vẫn giữ nguyên.

---

# 216.20. Concurrency model

Core concepts:

```text
Execution Domain
Ownership
Send
Share
Capability
Atomic
Synchronization
```

Không có universal actor/thread abstraction trong Core.

---

# 216.21. Thread

Thread API thuộc standard/system library.

Core chỉ cần semantics để compiler hiểu:

```text
execution domain
Send
Share
synchronization
```

---

# 216.22. Async

Core syntax:

```text
async
await
```

nhưng:

```text
executor
scheduler
reactor
runtime
```

thuộc library/runtime.

---

# 216.23. Structured concurrency

Library mặc định nên khuyến khích structured concurrency.

Detached execution phải explicit.

---

# 216.24. GPU

Core compiler semantics hiểu:

```text
ExecutionDomain
StorageDomain
GpuLegal
```

Nhưng:

```text
Device
Queue
Texture
RenderGraph
```

thuộc graphics/GPU libraries.

---

# 216.25. Comptime

Core:

```text
const
comptime
```

Compiler cung cấp execution environment.

External capabilities là explicit.

---

# 216.26. Reflection

Compile-time reflection thuộc compiler language capability.

Runtime reflection:

```text
optional metadata
```

không phải Core runtime requirement.

---

# 216.27. Macro decision

Axiom v1.0 **không đóng gói một general-purpose macro language vào Core**.

Thay vào đó:

```text
comptime
derive
typed generation
```

là hướng chính.

---

# 216.28. Why no unrestricted macros

Tránh tạo hai compiler:

```text
Axiom compiler
+
Macro compiler
```

và tránh semantic bypass.

---

# 216.29. Traits

Trait là Core type-system mechanism.

Trait không mặc định có:

```text
object header
vtable
runtime dispatch
```

---

# 216.30. Dynamic dispatch

Explicit:

```text
dyn Trait
```

Static dispatch mặc định.

---

# 216.31. Classes

Không có class trong Core.

Thay bằng:

```text
struct
fn
impl
trait
```

---

# 216.32. Method model

```axiom
fn length(self: Vec2) -> f32
```

gọi:

```text
v.length()
```

chỉ là syntax sugar.

---

# 216.33. Inheritance

Không có class inheritance.

Behavior reuse:

```text
trait
composition
generic
extension
```

---

# 216.34. Override

Default trait method có thể được concrete implementation thay thế.

Không bắt buộc `override` keyword.

Compiler/IDE có thể cung cấp warning nếu muốn biểu thị intent.

---

# 216.35. Generics

Generic là compile-time abstraction.

Mặc định:

```text
static dispatch
monomorphization
specialization
```

theo compiler policy.

---

# 216.36. Dynamic generic abstraction

Khi cần runtime polymorphism:

```text
dyn Trait
```

explicit.

---

# 216.37. Type conversion

Bốn tầng chính thức:

```text
Coercion
Cast
Bitcast
Unsafe reinterpretation
```

Không trộn lẫn.

---

# 216.38. Numeric conversion

Không có implicit narrowing nguy hiểm.

Ví dụ:

```text
i64 → i32
```

phải explicit.

---

# 216.39. Memory representation

Default:

```text
compiler controlled
```

Explicit:

```text
@repr(C)
@repr(transparent)
@repr(packed)
@repr(align)
```

---

# 216.40. `@repr(packed)`

Là system/unsafe-oriented feature.

Không làm packed layout trở thành mặc định.

---

# 216.41. ABI

Ba tầng:

```text
Internal ABI
Package ABI
Stable/Public ABI
```

---

# 216.42. Stable ABI

Chỉ khi explicit:

```text
@abi(stable)
```

---

# 216.43. Public ≠ Stable ABI

```text
pub fn
```

không tự động freeze binary layout.

---

# 216.44. FFI

Primary stable foreign boundary:

```text
extern "C"
```

Các ABI khác là platform-specific extensions.

---

# 216.45. Serialization

Serialization không được dựa trực tiếp vào:

```text
raw struct memory layout
```

trừ khi explicit representation contract.

---

# 216.46. Security

Core security primitive chỉ gồm những semantic obligations cần compiler hiểu:

```text
unsafe boundary
constant-time contract
secret/zeroization contracts
```

Crypto algorithms vẫn library-level.

---

# 216.47. AI

AI không phải semantic feature.

AI integration thuộc:

```text
CompilerDB
AXCP
Tooling
```

AI không có quyền bypass compiler.

---

# 216.48. Compiler interface

Compiler API chính thức:

```text
Source
Syntax
Semantic
MIR
Verification
Diagnostics
Optimization
ABI
Target
Build
```

---

# 216.49. AI interface

AXCP cung cấp:

```text
query
inspect
explain
diagnose
suggest
context
```

nhưng không:

```text
approve unsafe semantic state
```

---

# 216.50. Standard Library classification

Standard Library chia:

```text
Core-compatible
Platform
Runtime
High-level
Optional
```

---

# 216.51. Minimal standard library

Một chương trình freestanding có thể chỉ cần:

```text
Core
startup
minimal system layer
```

---

# 216.52. Full standard library

Hosted application có thể sử dụng:

```text
IO
filesystem
network
threads
async
Unicode
collections
crypto
GUI
graphics
tensor
```

---

# 216.53. Runtime composition

Runtime được link theo capability graph.

Không có:

```text
libaxiom_runtime_everything
```

bắt buộc cho mọi binary.

---

# 216.54. Binary-size principle

Nếu chương trình không dùng:

```text
async
network
GUI
reflection
Unicode
GPU
```

các subsystem tương ứng không nên xuất hiện trong binary.

---

# 216.55. Compiler-generated machinery

Compiler có thể generate:

```text
drop glue
async state machines
pattern dispatch
generic specializations
```

nhưng generated machinery không phải runtime dependency mặc định.

---

# 216.56. Zero-cost abstraction

Định nghĩa chính thức:

> Abstraction không được áp đặt runtime cost khi compiler có đủ thông tin để loại bỏ nó và observable semantics không yêu cầu cost đó.

Không có nghĩa mọi abstraction luôn miễn phí.

---

# 216.57. Performance principle

Axiom không cam kết:

```text
mọi chương trình Axiom > C
```

Cam kết kiến trúc:

> **Không đặt ra semantic overhead bắt buộc nếu overhead đó không cần thiết cho semantics.**

Đây là cách diễn đạt chính xác hơn mục tiêu “nhanh bằng hoặc hơn C/C++”.

---

# 216.58. C compatibility philosophy

Axiom không phải:

```text
C with better syntax
```

nhưng phải có khả năng:

```text
interoperate with C
```

mà không phá Core type system.

---

# 216.59. C++ compatibility

Không cố mô phỏng toàn bộ C++ object model trong Core.

C++ interop thông qua:

```text
C ABI
opaque types
explicit C++ ABI integration
```

---

# 216.60. Rust compatibility

Không nhập borrow checker/lifetime syntax của Rust.

Có thể interop qua:

```text
C ABI
FFI contract
future Axiom ABI
```

---

# 216.61. WASM

WASM là target, không phải language subset riêng.

---

# 216.62. Embedded

Embedded là target/profile:

```text
freestanding
no allocator
no OS
no threads
```

nếu cần.

---

# 216.63. Kernel development

Có thể dùng:

```text
unsafe
volatile
MMIO
interrupt ABI
custom allocator
freestanding
```

---

# 216.64. Real-time profile

Có thể có profile:

```text
@profile(realtime)
```

với các compiler/runtime restrictions phù hợp.

Không thay đổi Core semantics.

---

# 216.65. Deterministic profile

Có thể có:

```text
@profile(deterministic)
```

kiểm soát:

```text
scheduling
floating point
randomness
time
external effects
```

theo library/runtime contract.

---

# 216.66. Safety profiles

Compiler profile có thể tăng kiểm tra:

```text
strict unsafe
constant-time
freestanding
kernel
hardening
```

nhưng không được làm safe semantics yếu đi.

---

# 216.67. Experimental features

Không đưa experimental feature vào Core v1 nếu chưa có:

```text
formal semantics
implementation
conformance tests
ABI decision
diagnostics
```

---

# 216.68. Future features

Có thể reserve:

```text
future syntax
future traits
future SIMD
future accelerators
```

nhưng **không được làm chúng trở thành semantic ambiguity**.

---

# 216.69. Specification conflict resolution

Nếu hai document mâu thuẫn:

```text
1. Formal Semantic Kernel
2. Core Specification
3. Compiler Contract
4. ABI/Platform Contract
5. Library Contract
6. Implementation Notes
```

theo thứ tự này.

---

# 216.70. Implementation note không thể thay đổi semantics

Một comment kiểu:

```text
"compiler hiện tại làm X"
```

không trở thành language rule.

---

# 216.71. Compiler behavior matrix

Mỗi feature phải phân loại:

| Feature | Semantic | Compiler | Runtime | Library |
|---|---:|---:|---:|---:|
| Ownership | ✓ | ✓ | | |
| `view` | ✓ | ✓ | | |
| Drop | ✓ | ✓ | | |
| Async | ✓ | ✓ | ✓ | ✓ |
| Executor | | | ✓ | ✓ |
| Vec | | | | ✓ |
| GPU domain | ✓ | ✓ | | ✓ |
| Tensor | | ✓ | | ✓ |
| FFI | ✓ | ✓ | | ✓ |
| GUI | | | | ✓ |

---

# 216.72. Feature admission rule

Một feature mới chỉ vào Core nếu ít nhất một trong các điều kiện:

```text
1. Không thể biểu diễn chính xác bằng existing primitives
2. Compiler cần hiểu để guarantee safety/correctness
3. Feature là observable semantic contract
4. Feature là fundamental syntax/control-flow primitive
```

---

# 216.73. Library-first rule

Nếu một tính năng có thể xây bằng:

```text
struct
trait
generic
comptime
function
```

mà không cần compiler semantic primitive mới:

> **Để ở library.**

---

# 216.74. Compiler-known library

Một library API có thể được compiler tối ưu đặc biệt mà không biến nó thành Core semantic primitive.

Ví dụ:

```text
Vec
Tensor
Iterator
```

có thể có compiler intrinsics/optimization metadata.

---

# 216.75. Compiler intrinsic boundary

Intrinsic phải có:

```text
semantic definition
fallback
target constraints
verification
```

Không được là "magic function" không specification.

---

# 216.76. Language syntax principle

Syntax ưu tiên:

```text
readable
predictable
machine-parsable
AI-friendly
```

Không tối ưu cho viết code cực ngắn bằng mọi giá.

---

# 216.77. AI-friendly syntax

Compiler phải có AST/lossless syntax nên AI không cần dựa vào parsing heuristics.

---

# 216.78. Error messages

Mỗi diagnostic có:

```text
code
severity
primary span
secondary spans
cause
explanation
suggested fix
semantic facts
```

---

# 216.79. AI diagnostic output

Machine-readable:

```text
{
  error_code,
  semantic_rule,
  location,
  facts,
  dependencies,
  possible_fixes
}
```

không phải chỉ text.

---

# 216.80. Human diagnostic

Human-facing vẫn phải tự nhiên:

```text
error AOWN-...
value `x` was moved here
...
```

---

# 216.81. Compiler certainty

Compiler không được nói:

```text
probably unsafe
```

ở production verification.

Phải phân biệt:

```text
Proven
Not Proven
Invalid
Unknown
```

---

# 216.82. AI explanation

AI có thể diễn giải:

```text
"Compiler không chứng minh A và B disjoint."
```

thay vì tự bịa:

```text
"hai vùng chắc chắn overlap"
```

---

# 216.83. Core v1.0 feature matrix

### Core language

```text
✓ static typing
✓ structs
✓ enums
✓ traits
✓ generics
✓ functions
✓ closures
✓ pattern matching
✓ ownership
✓ Copy/Move/Clone/Drop
✓ view/mut_view
✓ async/await
✓ comptime
✓ unsafe
✓ modules
✓ Result/Option
✓ deterministic evaluation
✓ atomics
```

---

# 216.84. Core exclusions

```text
✗ class
✗ inheritance
✗ GC
✗ mandatory runtime
✗ mandatory heap
✗ implicit RC
✗ borrow syntax
✗ lifetime syntax
✗ exceptions
✗ general macro language
✗ runtime reflection
✗ universal Object
✗ null
```

---

# 216.85. System layer

```text
✓ raw pointers
✓ volatile
✓ MMIO
✓ OS resources
✓ process/thread
✓ FFI
✓ stable ABI
✓ dynamic loading
✓ allocator
✓ TLS
✓ interrupt/system ABI
```

---

# 216.86. Compute layer

```text
✓ SIMD
✓ CPU feature dispatch
✓ GPU
✓ Tensor
✓ AD
✓ parallel computing
✓ NUMA
✓ distributed compute
✓ accelerator backends
```

nhưng chủ yếu là compiler/library/platform layer.

---

# 216.87. Application layer

```text
✓ GUI
✓ graphics
✓ networking
✓ database
✓ filesystem
✓ serialization
✓ crypto
✓ scientific computing
```

---

# 216.88. Compiler layer

```text
✓ CompilerDB
✓ HIR
✓ MIR
✓ Verified MIR
✓ OptIR
✓ Axiom LIR
✓ Machine IR
✓ object writer
✓ linker
✓ reference interpreter
✓ MIR interpreter
```

---

# 216.89. Tooling layer

```text
✓ LSP
✓ debugger
✓ profiler
✓ formatter
✓ documentation
✓ package manager
✓ AI protocol
✓ semantic query
```

---

# 216.90. Specification maturity levels

Một feature được coi là:

```text
Draft
        ↓
Designed
        ↓
Specified
        ↓
Implemented
        ↓
Conformance Tested
        ↓
Frozen
```

Chỉ `Frozen` mới thuộc Axiom v1.0 normative specification.

---

# 216.91. Normative vs informative

Specification chia:

```text
NORMATIVE
```

và:

```text
INFORMATIVE
```

Ví dụ:

> "Compiler thường dùng SSA."

là informative.

> "Verified MIR phải bảo toàn ownership state."

là normative.

---

# 216.92. Compiler implementation freedom

Axiom specification không ép:

```text
SSA
specific register allocator
specific parser algorithm
specific database implementation
```

trừ khi cần cho observable semantics/tooling contract.

---

# 216.93. ABI implementation freedom

Internal ABI hoàn toàn compiler-controlled.

Stable ABI mới bị ràng buộc.

---

# 216.94. Backend implementation freedom

Compiler có thể sử dụng:

```text
pattern matching
DAG selection
machine learning cost model
table-driven selector
```

miễn output đúng semantics.

---

# 216.95. AI implementation freedom

AI agent có thể hỗ trợ compiler development nhưng không trở thành dependency của compiler correctness.

---

# 216.96. No AI dependency in compilation

Production compiler phải compile code:

```text
offline
without model
```

nếu source/build dependencies đầy đủ.

---

# 216.97. Reproducibility

AI-generated suggestions không được làm artifact nondeterministic.

---

# 216.98. Final Axiom v1.0 invariants — `ASPEC`

### `ASPEC-20`
Axiom shall maintain one authoritative semantic hierarchy.

### `ASPEC-21`
Formal Semantic Kernel has precedence over implementation notes.

### `ASPEC-22`
Core semantics shall remain independent of standard-library implementation.

### `ASPEC-23`
Compiler implementation shall not silently define language semantics.

### `ASPEC-24`
Library functionality shall remain library-level whenever existing Core primitives suffice.

### `ASPEC-25`
Compiler-known library optimizations shall preserve ordinary semantic contracts.

### `ASPEC-26`
Explicit semantic boundaries shall remain explicit.

### `ASPEC-27`
Unsafe shall never imply unrestricted semantic bypass.

### `ASPEC-28`
No mandatory garbage collector shall exist in Core.

### `ASPEC-29`
No mandatory runtime shall exist in Core.

### `ASPEC-30`
No mandatory heap allocation shall exist in Core.

### `ASPEC-31`
No programmer-written lifetime annotations shall be required by Core.

### `ASPEC-32`
No programmer-written borrow-checking annotations shall be required by Core.

### `ASPEC-33`
No general class/inheritance hierarchy shall exist in Core.

### `ASPEC-34`
No mandatory exception mechanism shall exist in Core.

### `ASPEC-35`
No implicit null reference shall exist in safe Core.

### `ASPEC-36`
Ownership and capability semantics shall remain distinct.

### `ASPEC-37`
Logical identity shall remain distinct from storage address.

### `ASPEC-38`
Memory representation shall remain distinct from semantic value.

### `ASPEC-39`
Wire representation shall remain distinct from memory representation.

### `ASPEC-40`
Stable ABI shall remain explicit.

### `ASPEC-41`
FFI shall remain an explicit semantic boundary.

### `ASPEC-42`
GPU and accelerator semantics shall not contaminate ordinary CPU Core semantics.

### `ASPEC-43`
AI tooling shall not become part of semantic correctness.

### `ASPEC-44`
All normative Core features shall have semantic definitions.

### `ASPEC-45`
All normative features shall have conformance tests.

### `ASPEC-46`
Experimental features shall not silently enter the v1.0 semantic contract.

### `ASPEC-47`
Implementation freedom shall be preserved wherever observable semantics permit.

### `ASPEC-48`
Optimization freedom shall be preserved wherever observable semantics permit.

### `ASPEC-49`
Compiler inability to prove an optimization shall result in omission of that optimization, not semantic weakening.

### `ASPEC-50`
Unknown shall never be promoted to Proven.

### `ASPEC-51`
The language shall remain implementable by an independent compiler.

### `ASPEC-52`
The language specification shall not require the reference compiler implementation to define semantics.

### `ASPEC-53`
Axiom v1.0 shall be internally consistent across Core, compiler, ABI, system and library contracts.

### `ASPEC-54`
Any future semantic change shall require an explicit language-version decision.

### `ASPEC-55`
Existing frozen semantics shall not be silently reinterpreted by later features.

---

# 216.99. Kết quả của 216

Axiom giờ có thể được xem như:

```text
                    AXIOM v1.0
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
       CORE           COMPILER          PLATFORM
        │                │                 │
   Semantics         MIR/OptIR          FFI/GPU/OS
        │                │                 │
        └────────────────┼─────────────────┘
                         │
                    STANDARD LIB
                         │
                  APPLICATION STACK
```

Quan trọng hơn, ta đã có nguyên tắc:

> **Không thêm feature chỉ vì nó "hay". Feature mới phải chứng minh nó cần thiết ở đúng tầng.**

Điều này giúp Axiom tránh trở thành một ngôn ngữ có hàng trăm tính năng nhưng semantic model rối.

---

# BOOTSTRAP-217 — Axiom v1.0 Syntax, Grammar & Canonical Surface Language

**TRẠNG THÁI: NEXT**

Bước kế tiếp nên chuyển từ **semantic architecture** sang **ngôn ngữ mà lập trình viên thực sự nhìn thấy**.

217 sẽ khóa:

```text
lexical rules
keywords
identifiers
literals
operators
precedence
expressions
statements
blocks
struct
enum
trait
impl
generic syntax
function syntax
method syntax
pattern syntax
match
async/await
comptime
unsafe
modules
attributes
visibility
type syntax
view/mut_view syntax
error propagation
closures
iterators
```

Đặc biệt sẽ giải quyết một vấn đề rất quan trọng của Axiom:

> **Làm thế nào để syntax đủ đơn giản cho con người và AI, nhưng vẫn biểu đạt được ownership, capability, generics, async, comptime, FFI và system programming mà không quay lại kiểu cú pháp con trỏ/lifetime phức tạp của C++/Rust?**