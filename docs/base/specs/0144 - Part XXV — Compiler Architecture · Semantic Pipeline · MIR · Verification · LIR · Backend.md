# Part XXV — Compiler Architecture · Semantic Pipeline · MIR · Verification · LIR · Backend

Đây là phần nối trực tiếp từ Runtime. Nếu Part XXIV xác định **chương trình cần runtime gì**, thì Part XXV xác định **compiler biến semantics Axiom thành machine code như thế nào**.

Mục tiêu không phải xây một compiler “nhiều tầng cho đẹp”, mà là:

> **Mỗi tầng có một trách nhiệm duy nhất, và sau khi một semantic property đã được chứng minh thì các tầng thấp hơn không phải gánh lại complexity đó.**

---

# XXV.1. Pipeline chính thức

Axiom v0.1 chốt pipeline:

```text
Source
  ↓
Lexer
  ↓
Parser
  ↓
AST
  ↓
Resolver
  ↓
HIR
  ↓
Typed HIR
  ↓
Trait / Generic Resolution
  ↓
Closure / Async Lowering
  ↓
MIR
  ↓
Ownership + Capability + Effect Verification
  ↓
Drop Elaboration
  ↓
Verified MIR
  ↓
Semantic Optimization
  ↓
ABI Lowering
  ↓
LIR
  ↓
Target Lowering
  ↓
Machine IR
  ↓
Machine Optimization
  ↓
Register Allocation
  ↓
Spill / Reload
  ↓
Final Machine IR
  ↓
Machine Encoder
  ↓
Object Writer
  ↓
Linker
  ↓
Executable / Library
```

Điểm quan trọng:

```text
Verification
```

xảy ra **trước khi ownership/capability semantics bị erase**.

---

# XXV.2. Compiler Không Phải Runtime

Compiler có thể thực hiện:

- ownership analysis;
- borrow/view analysis;
- trait solving;
- escape analysis;
- lifetime analysis;
- alias analysis;
- effect analysis;
- compile-time execution.

Nhưng tất cả những thứ đó:

> **không trở thành runtime machinery nếu semantics không yêu cầu.**

Ví dụ:

```axiom
fn sum(a: view<i32>) -> i32 {
    ...
}
```

Compiler kiểm tra view.

Machine code cuối cùng có thể chỉ còn:

```text
pointer + length
```

Không có runtime borrow checker.

---

# XXV.3. AST — Syntax Representation

AST giữ syntax gần source:

```text
FunctionDecl
StructDecl
EnumDecl
TraitDecl
ImplDecl
Expr
Pattern
TypeSyntax
Attribute
```

AST **không phải semantic representation cuối cùng**.

Ví dụ:

```axiom
v.length()
```

AST vẫn có thể là:

```text
MethodCall(
    receiver = v,
    name = length
)
```

---

# XXV.4. Resolver

Resolver biến tên thành identity.

Ví dụ:

```axiom
import math.vector { Vec2 }

fn f(v: Vec2) -> f32 {
    v.length()
}
```

Resolver xác định:

```text
Vec2 → Package:math.vector::Vec2
length → FunctionId:...
```

Không resolve bằng string ở các tầng sau.

---

# XXV.5. Typed HIR

HIR là semantic representation cấp cao hơn AST.

Ví dụ:

```text
Call {
    function: FunctionId(42),
    receiver: ValueId(7),
    arguments: [...]
}
```

Method sugar đã được resolve.

---

# XXV.6. Type Identity

Compiler không dùng tên text để nhận dạng type.

Ví dụ:

```axiom
type UserId = u64
```

và:

```axiom
struct UserId(u64)
```

khác nhau.

Compiler dùng:

```text
TypeId
```

và type interning.

---

# XXV.7. Type Interning

Ví dụ:

```text
i32
Vec<i32>
Option<Vec<i32>>
```

được canonicalize:

```text
TypeId(1)
TypeId(37)
TypeId(92)
```

Điều này rất quan trọng cho:

- trait solver;
- incremental compilation;
- cache;
- diagnostics;
- ABI;
- monomorphization.

---

# XXV.8. Typed HIR Không Chứa Ambiguity

Sau Typed HIR:

```text
x + y
```

không còn là:

```text
"maybe integer addition"
"maybe trait call"
```

mà phải resolve thành semantic operation.

Ví dụ:

```text
Add::add<T>
```

hoặc intrinsic numeric addition.

---

# XXV.9. Trait Solver

Trait solver nhận:

```text
T: Trait
```

và trả trạng thái:

```text
PROVEN
DISPROVEN
AMBIGUOUS
OVERFLOW
```

Không được để backend tự giải trait.

---

# XXV.10. Trait Solver Có Giới Hạn

Ví dụ recursive constraints:

```axiom
trait A<T: A<T>> {}
```

hoặc chuỗi impl pathological.

Compiler phải có:

```text
depth limit
step limit
cycle detection
cache
```

Nếu vượt:

```text
AX_TRAIT_...
trait resolution overflow
```

Không compiler hang vô hạn.

---

# XXV.11. Generic Resolution

Axiom mặc định:

```text
monomorphization
```

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

có thể tạo:

```text
max<i32>
max<f64>
max<User>
```

khi cần.

---

# XXV.12. Nhưng Monomorphization Không Phải Semantics

Compiler có thể sau này chọn:

```text
code sharing
specialized version
devirtualized version
```

miễn observable behavior không đổi.

Đã chốt:

> Specialization là compiler strategy, không phải language semantics.

---

# XXV.13. Closure Lowering

Source:

```axiom
let factor = 10

let f = |x: i32| x * factor
```

Compiler biến thành conceptual:

```text
Closure {
    environment: {
        factor: i32
    }

    function: closure_body
}
```

Nhưng nếu closure không escape:

```text
environment
```

có thể bị scalarize/eliminate hoàn toàn.

---

# XXV.14. Capture Analysis

Compiler xác định capture:

```text
READ
MUTATE
MOVE
```

Ví dụ:

```axiom
var count = 0

let f = || {
    count += 1
}
```

Compiler biết closure cần mutable access.

Programmer không cần viết lifetime/capture metadata.

---

# XXV.15. Async Lowering

Source:

```axiom
async fn fetch() -> Result<Data, Error> {
    let a = await_a().await?
    let b = await_b(a).await?
    Ok(b)
}
```

được chuyển thành state machine conceptual:

```text
State0
 ↓
await_a
 ↓
State1 { a }
 ↓
await_b
 ↓
State2 { a, b }
 ↓
Return
```

---

# XXV.16. Async State Không Có Nghĩa Heap

State machine có thể:

```text
stack
register
inline
arena
heap
```

Compiler quyết định.

---

# XXV.17. MIR — Trung Tâm Của Axiom Compiler

MIR là semantic execution representation.

Nó phải đủ thấp để:

- ownership verification;
- Drop;
- alias analysis;
- async;
- concurrency;
- optimization

nhưng vẫn đủ target-neutral.

---

# XXV.18. MIR Không Phải SSA Thuần

Axiom MIR nên là:

> **SSA-oriented, ownership-aware CFG IR**

Không ép tất cả mọi thứ thành pure SSA.

Lý do:

```text
Drop
MOVE
PARTIAL MOVE
PLACE
VIEW
CAPABILITY
```

cần semantics rõ ràng hơn SSA value thuần.

---

# XXV.19. MIR Place

Một khái niệm quan trọng:

```text
Place
```

Ví dụ:

```axiom
user.name
```

có thể trở thành:

```text
Place(
    base = user,
    projection = Field(name)
)
```

Array:

```axiom
a[i]
```

thành:

```text
Place(
    base = a,
    projection = Index(i)
)
```

---

# XXV.20. Vì Sao Place Quan Trọng?

Nhờ Place, compiler có thể hiểu:

```axiom
struct S {
    a: i32
    b: i32
}

var s = ...
```

và:

```text
view_mut(s.a)
view_mut(s.b)
```

là DISJOINT.

Không cần coi toàn bộ `s` là một mutable region.

---

# XXV.21. MIR Ownership State

MIR verifier theo dõi:

```text
UNINIT
OWNED
PARTIAL
MOVED
DROPPED
```

Ví dụ:

```axiom
let x = Foo()
consume(x)
use(x)
```

sau `consume(x)`:

```text
x → MOVED
```

`use(x)`:

```text
AX_MOVE_0003
use of moved value
```

---

# XXV.22. Partial Move

Ví dụ:

```axiom
struct Pair {
    a: String
    b: String
}

let p = Pair(...)
let x = p.a
```

MIR:

```text
p.a → MOVED
p.b → OWNED
p → PARTIAL
```

Nếu compiler-derived Drop:

```text
drop(p.b)
```

được emit.

---

# XXV.23. User Drop

Nếu:

```axiom
impl Drop for Pair {
    fn drop(self) { ... }
}
```

partial move bị cấm.

Vì compiler không thể tùy tiện gọi custom destructor trên partially-valid object.

---

# XXV.24. Drop Elaboration

Source:

```axiom
fn f() {
    let a = A()
    let b = B()

    if condition {
        return
    }
}
```

Compiler tạo semantic cleanup:

```text
if condition:
    drop(b)
    drop(a)
    return
```

Không cần programmer viết.

---

# XXV.25. Drop CFG

Mỗi exit path phải được phân tích:

```text
normal return
early return
break
continue
panic/unwind
```

và xác định object nào còn ownership.

---

# XXV.26. Verified MIR

Sau verifier:

```text
Verified MIR
```

phải đảm bảo các invariant chính:

```text
no invalid move
no double drop
no dangling view
no conflicting mut_view
no safe use-after-free
no invalid ownership transfer
no safe data race
```

Từ đây trở xuống, compiler không cần “suy đoán” những property này nữa.

---

# XXV.27. Đây Là Một Boundary Rất Quan Trọng

Trước:

```text
semantic verification
```

Sau:

```text
verified semantics
```

Do đó:

```text
Optimizer
```

không phải borrow checker.

Đây là cách tránh compiler architecture bị rối.

---

# XXV.28. Unsafe Trong MIR

`unsafe` không tạo một MIR riêng.

Nó tạo:

```text
unsafe operation
```

với proof obligation khác.

Ví dụ:

```axiom
unsafe {
    *ptr
}
```

MIR:

```text
DEREF_RAW_PTR
```

Verifier biết đây là operation yêu cầu unsafe context.

Nhưng các property khác vẫn kiểm tra.

---

# XXV.29. Unsafe Không Tắt Type Checking

Ví dụ:

```axiom
unsafe {
    let x: i32 = "hello"
}
```

vẫn compile error.

Unsafe chỉ mở:

```text
specific machine-level proof obligations
```

---

# XXV.30. Capability Verification

Ví dụ:

```axiom
let v = mut_view(x)
```

Verifier ghi:

```text
Capability {
    provenance: x
    region: whole(x)
    access: WRITE
}
```

Khi:

```axiom
let r = view(x)
```

đồng thời tồn tại:

```text
WRITE(x)
READ(x)
```

→ conflict.

---

# XXV.31. Disjoint Capability

Nhưng:

```axiom
let a = mut_view(x.left)
let b = mut_view(x.right)
```

nếu:

```text
left ∩ right = ∅
```

thì hợp lệ.

Đây là một trong những lý do MIR phải có Place/Region.

---

# XXV.32. View Erasure

Sau verification:

```text
view<T>
mut_view<T>
```

không còn là runtime ownership machinery.

Representation có thể chỉ là:

```text
ptr
ptr + len
```

hoặc:

```text
ptr
```

tùy type.

---

# XXV.33. Ownership Erasure

Ownership state:

```text
OWNED
MOVED
DROPPED
```

là compiler metadata.

Machine code chỉ còn những operations thực sự observable:

```text
load
store
call destructor
```

---

# XXV.34. Semantic Optimization

Optimization bắt đầu trên Verified MIR.

Ví dụ:

```text
constant folding
dead code elimination
copy propagation
move elimination
scalar replacement
escape analysis
allocation elimination
inline
devirtualization
loop optimization
vectorization
```

---

# XXV.35. Optimization Không Được Thay Đổi Semantics

Ví dụ:

```axiom
let x = side_effect()
if false {
    use(x)
}
```

Compiler chỉ được bỏ `use`, không được bỏ `side_effect()` nếu observable.

---

# XXV.36. Observable Behavior

Axiom cần định nghĩa observable behavior gồm ít nhất:

```text
return values
memory-visible effects
volatile operations
atomic operations
IO
FFI calls
synchronization
panic/trap
program termination
observable addresses
```

---

# XXV.37. Pure Computation

Nếu compiler chứng minh:

```text
x = calculate()
```

không có observable effect và result không được dùng:

→ có thể eliminate toàn bộ.

---

# XXV.38. Allocation Elimination

```axiom
fn f() -> i32 {
    let b = Box.new(42)
    *b
}
```

có thể thành:

```text
return 42
```

nếu address không escape và allocation failure semantics không observable theo API contract.

Đây là điểm phải rất cẩn thận:

> Optimization không được loại allocation nếu allocation failure là observable semantic behavior của API.

---

# XXV.39. ABI Lowering

Sau semantic optimization:

```text
Axiom types
```

được chuyển thành:

```text
ABI representation
```

Ví dụ:

```text
struct
→ registers / stack / memory
```

hoặc:

```text
view<T>
→ ptr + len
```

---

# XXV.40. ABI Không Được Chạy Ngược Lên Type System

Type system không được thiết kế dựa trên:

```text
x86-64 register count
```

Thay vào đó:

```text
Type semantics
 ↓
ABI classification
 ↓
target ABI
```

---

# XXV.41. LIR

LIR là target-neutral machine-oriented IR.

Ví dụ:

```text
v1 = ADD v2, v3
LOAD v4, [v5]
STORE [v6], v7
CALL fn, args
BR label
CMP
SELECT
ATOMIC_CAS
```

Không còn:

```text
view lifetime
trait solving
ownership states
```

---

# XXV.42. Không Có `ALLOCA` Trong LIR

Stack storage nên được biểu diễn qua:

```text
stack object / frame requirement
```

hoặc target lowering.

Không nên đưa một C-like:

```text
alloca
```

vào LIR rồi bắt backend tự hiểu semantic ownership.

---

# XXV.43. Target Lowering

Ví dụ:

```text
LIR
 ↓
x86_64 lowering
 ↓
Machine IR
```

hoặc:

```text
LIR
 ↓
AArch64 lowering
 ↓
Machine IR
```

---

# XXV.44. Machine IR

Machine IR biết:

```text
physical registers
register classes
instruction constraints
addressing modes
calling convention
stack frame
ABI
```

Ví dụ:

```text
RAX
RBX
XMM0
SP
FP
```

---

# XXV.45. Register Allocation

Flow:

```text
Virtual Register
        ↓
liveness
        ↓
interference
        ↓
allocation
        ↓
physical register
```

Nếu thiếu register:

```text
spill
```

---

# XXV.46. Register Allocation Không Được Biết Ownership

Ví dụ:

```text
String moved
```

đã được giải quyết ở MIR.

Register allocator chỉ biết:

```text
v1 live
v2 dead
```

Không cần hiểu `String`.

---

# XXV.47. Machine Optimization

Ở tầng Machine IR có thể làm:

```text
peephole
instruction combining
target-specific scheduling
addressing-mode folding
register coalescing
```

---

# XXV.48. Encoder

Encoder biến:

```text
Machine IR
```

thành:

```text
machine bytes
```

Ví dụ x86-64:

```text
opcode
ModRM
SIB
displacement
immediate
```

Không còn semantics Axiom.

---

# XXV.49. Object Writer

Object writer tạo:

```text
ELF
PE/COFF
Mach-O
WASM
```

với:

```text
sections
symbols
relocations
debug info
unwind info
```

---

# XXV.50. Linker

Linker xử lý:

```text
objects
libraries
symbols
relocations
sections
imports
exports
```

Không xử lý:

```text
ownership
traits
views
Drop
```

---

# XXV.51. Đây Là Boundary Rất Quan Trọng

Compiler:

```text
Source semantics
→ Machine representation
```

Linker:

```text
Machine artifacts
→ Final binary
```

Không để linker trở thành “compiler backend lần hai”.

---

# XXV.52. Debug Information

Axiom cần giữ mapping:

```text
Source
 ↕
AST/HIR
 ↕
MIR
 ↕
LIR
 ↕
Machine instruction
```

để debugger có thể nói:

```text
line 42
variable x
field user.name
```

ngay cả khi optimization mạnh.

---

# XXV.53. Ownership Debugging

Debug build có thể expose:

```text
x: OWNED
v: view(x)
```

nhưng đây là debugger metadata.

Không tạo runtime ownership tracking trong release.

---

# XXV.54. Compiler Architecture

Repository hiện tại trở thành hợp lý:

```text
compiler/
├── lexer/
├── parser/
├── ast/
├── resolver/
├── hir/
├── typeck/
├── mir/
├── verifier/
├── oracle/
├── optimizer/
├── abi/
├── lir/
├── backend/
├── object/
└── driver/
```

Target-specific:

```text
targets/
└── x86_64/
    ├── target/
    ├── abi/
    ├── legalize/
    ├── isel/
    ├── machine/
    ├── regalloc/
    ├── encoder/
    └── elf/
```

---

# XXV.55. Dependency Direction

Bắt buộc:

```text
lexer
  ↓
parser
  ↓
AST
  ↓
HIR
  ↓
MIR
  ↓
LIR
  ↓
backend
```

Không được:

```text
parser → x86_64
typeck → ELF
ownership verifier → register allocator
```

---

# XXV.56. Backend Plugin Boundary

Một target mới:

```text
AArch64
RISC-V
x86-64
ARM32
WASM
```

không được yêu cầu sửa language semantics.

Chỉ cần implement:

```text
TargetDescription
ABI
Legalizer
InstructionSelector
MachineIR
RegisterAllocator
Encoder
ObjectWriter
```

theo mức cần thiết.

---

# XXV.57. Target Description

Compiler phải có target description:

```text
Target {
    architecture
    pointer_width
    endianness
    alignment
    calling_conventions
    atomic_capabilities
    features
    object_format
    executable_format
}
```

---

# XXV.58. Compiler Determinism

Cùng:

```text
source
compiler version
target
profile
dependencies
configuration
```

phải tạo cùng semantic result.

Không:

```text
random trait resolution
random ABI
random diagnostics
```

---

# XXV.59. Parallel Compiler

Compiler có thể parallelize:

```text
module compilation
generic instantiation
optimization units
code generation
```

nhưng kết quả semantic phải deterministic.

---

# XXV.60. Incremental Compilation

Part XXIII đã chốt SIF.

Pipeline:

```text
Source
 ↓
HIR
 ↓
SIF
 ↓
API fingerprint
```

Nếu implementation private thay đổi nhưng API không đổi:

```text
consumer semantic checking
```

không cần chạy lại.

---

# XXV.61. Codegen Cache

Generic:

```text
Vec<i32>
```

có thể cache:

```text
CodegenKey {
    generic_definition
    type_arguments
    target
    cpu_features
    optimization
    ABI
}
```

---

# XXV.62. Verified MIR Cache

Một optimization quan trọng:

```text
Typed HIR
 ↓
Verified MIR
```

có thể cache nếu semantic fingerprint không đổi.

Điều này giúp compiler nhanh mà không ảnh hưởng semantics.

---

# XXV.63. Oracle Integration

Mỗi compiler stage có thể test:

```text
Source
→ MIR
→ Oracle
```

và:

```text
Source
→ Native
```

so sánh observable behavior.

---

# XXV.64. Differential Compiler Testing

Một test:

```axiom
fn main() -> i32 {
    let x = 10
    x * 2 + 3
}
```

Oracle:

```text
return = 23
```

Native:

```text
return = 23
```

Nếu khác:

```text
compiler bug
```

---

# XXV.65. Optimization Equivalence

Cùng source:

```text
-O0
-O1
-O2
-O3
-Os
```

phải có:

```text
same observable semantics
```

ngoại trừ những hành vi explicitly target/profile-defined như timing, resource exhaustion nếu spec cho phép.

---

# XXV.66. Compiler Internal Rule

Một nguyên tắc rất mạnh nên freeze:

> **Không một optimization pass nào được phép tạo ra semantic assumption mà verifier trước đó chưa chứng minh.**

Ví dụ optimizer không được tự giả định:

```text
two pointers do not alias
```

nếu safe semantics không bảo đảm.

Nhưng nếu capability verifier chứng minh:

```text
DISJOINT
```

thì optimizer có thể dùng fact đó.

---

# XXV.67. Optimization Facts

Verified MIR có thể mang:

```text
Fact {
    NoAlias
    NonNull
    Aligned
    InBounds
    Immutable
    NoEscape
    ReadOnly
    Disjoint
}
```

Các fact này là compiler-internal.

Không nhất thiết tồn tại runtime.

---

# XXV.68. Fact Lifetime

Một fact chỉ được sử dụng trong phạm vi mà proof còn hợp lệ.

Ví dụ:

```text
NoAlias(v)
```

không được giữ sau một operation có thể invalidate capability.

Đây là điểm rất quan trọng để tránh optimizer bug.

---

# XXV.69. Compiler Contract

Ta có thể đóng pipeline thành:

```text
Syntax correctness
        ↓
Name correctness
        ↓
Type correctness
        ↓
Trait correctness
        ↓
Ownership correctness
        ↓
Capability correctness
        ↓
Concurrency correctness
        ↓
Drop correctness
        ↓
Verified semantic program
        ↓
Optimization
        ↓
ABI correctness
        ↓
Machine correctness
```

---

# XXV.70. Bộ Invariant Part XXV

### Frontend

**ACOMPILER-20 — AST Preserves Source Structure**

**ACOMPILER-21 — Resolver Produces Stable Semantic Identities**

**ACOMPILER-22 — Typed HIR Contains No Unresolved Type Ambiguity**

**ACOMPILER-23 — Trait Resolution Terminates Or Reports Overflow**

**ACOMPILER-24 — Generic Specialization Is Not Observable**

### MIR

**ACOMPILER-25 — MIR Is Target-Neutral**

**ACOMPILER-26 — MIR Represents Ownership-Relevant Operations Explicitly**

**ACOMPILER-27 — MIR Represents Places Explicitly**

**ACOMPILER-28 — MIR Represents Capability-Relevant Access Explicitly**

**ACOMPILER-29 — MIR Represents Drop-Relevant Control Flow Explicitly**

### Verification

**ACOMPILER-30 — Safe Ownership Rules Are Verified Before Semantic Erasure**

**ACOMPILER-31 — Capability Conflicts Are Rejected**

**ACOMPILER-32 — Live Capabilities Cannot Depend On Dead Owners**

**ACOMPILER-33 — Double Drop Is Rejected**

**ACOMPILER-34 — Use After Move Is Rejected**

**ACOMPILER-35 — Safe Data Races Are Rejected**

**ACOMPILER-36 — Unsafe Does Not Disable Type Correctness**

**ACOMPILER-37 — Unsafe Does Not Disable Atomic Semantics**

### Optimization

**ACOMPILER-38 — Optimization Preserves Observable Semantics**

**ACOMPILER-39 — Optimization May Erase Verified Language Machinery**

**ACOMPILER-40 — Optimization May Use Proven Semantic Facts**

**ACOMPILER-41 — Optimization Cannot Invent Unproven Alias Guarantees**

**ACOMPILER-42 — Allocation Elimination Must Preserve Allocation Failure Semantics**

**ACOMPILER-43 — Observable Address Identity Constrains Optimization**

**ACOMPILER-44 — Optimization Level Does Not Change Language Semantics**

### ABI / Backend

**ACOMPILER-45 — ABI Lowering Occurs After Language Semantic Verification**

**ACOMPILER-46 — LIR Does Not Depend On High-Level Ownership Semantics**

**ACOMPILER-47 — Machine IR Is Target-Specific**

**ACOMPILER-48 — Register Allocation Is Independent Of Language Ownership**

**ACOMPILER-49 — Object Writers Operate On Machine-Level Artifacts**

**ACOMPILER-50 — Linkers Do Not Resolve Axiom Language Semantics**

### Determinism

**ACOMPILER-51 — Compilation Is Deterministic For Equal Semantic Inputs**

**ACOMPILER-52 — Parallel Compilation Preserves Deterministic Semantics**

**ACOMPILER-53 — Incremental Compilation Preserves Full Compilation Semantics**

**ACOMPILER-54 — Cached Verified Artifacts Must Be Semantically Equivalent To Recomputed Artifacts**

### Debugging

**ACOMPILER-55 — Debug Mapping May Survive Semantic Optimization**

**ACOMPILER-56 — Debug Ownership Information Is Not A Release Runtime Requirement**

---

# XXV.71. Một thay đổi kiến trúc rất đáng giá

Sau Part XXV, tôi đề xuất **không gọi `verifier` đơn thuần là “borrow checker”**.

Nó thực chất là:

```text
Semantic Verifier
```

và bên trong gồm:

```text
Ownership verifier
Capability verifier
Drop verifier
Concurrency verifier
Effect verifier
Pattern verifier
Execution-domain verifier
```

Như vậy Axiom không bị mắc vào mô hình:

```text
language = borrow checker
```

mà chính xác hơn:

```text
Language
   ↓
Semantic Verifier
   ├── Ownership
   ├── Capability
   ├── Drop
   ├── Concurrency
   ├── Effect
   ├── Pattern
   └── Execution Domain
```

Đây cũng khớp với triết lý cốt lõi:

> **Compiler Complexity Is Not Language Complexity.**

---

# XXV.72. Kiến trúc compiler Axiom sau khi khóa

```text
                         SOURCE
                            │
                     ┌──────▼──────┐
                     │ Lexer/Parser│
                     └──────┬──────┘
                            AST
                             │
                     ┌───────▼───────┐
                     │ Resolver/HIR  │
                     └───────┬───────┘
                             │
                     ┌───────▼────────┐
                     │ Type/Traitck    │
                     └───────┬────────┘
                             │
                     ┌───────▼────────┐
                     │ Closure/Async   │
                     └───────┬────────┘
                             │
                            MIR
                             │
              ┌──────────────▼──────────────┐
              │      SEMANTIC VERIFIER      │
              │ Ownership / Capability      │
              │ Drop / Concurrency / Effect│
              └──────────────┬──────────────┘
                             │
                       VERIFIED MIR
                             │
                     ┌───────▼───────┐
                     │   Optimizer   │
                     └───────┬───────┘
                             │
                       ABI Lowering
                             │
                            LIR
                             │
                     Target Lowering
                             │
                       Machine IR
                             │
                  ┌──────────▼──────────┐
                  │ RegAlloc / Machine  │
                  │ Optimization        │
                  └──────────┬──────────┘
                             │
                         Encoder
                             │
                         Object
                             │
                         Linker
                             │
                         BINARY
```

Đây là pipeline đủ mạnh để Axiom hướng tới C/C++-class performance mà vẫn giữ phần lớn complexity ở compiler thay vì đẩy lên programmer.

**Tiếp theo: Part XXVI — Semantic Oracle · Reference Interpreter · Conformance Engine · Differential Testing.** Đây là phần sẽ quyết định Axiom có thực sự có một “nguồn sự thật” độc lập để phát hiện compiler miscompilation hay không.