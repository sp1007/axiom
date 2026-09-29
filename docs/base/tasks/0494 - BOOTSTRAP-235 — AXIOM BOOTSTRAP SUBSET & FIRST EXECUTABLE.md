# BOOTSTRAP-235 — AXIOM BOOTSTRAP SUBSET & FIRST EXECUTABLE

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là bước biến kiến trúc compiler thành **một kế hoạch bootstrap có thể thực sự chạy được**.

Mục tiêu của 235 không phải tạo một “ngôn ngữ Axiom mini” rồi sau đó bỏ đi. Mục tiêu là tạo **Bootstrap Subset** là một tập con có tính chất:

> **Đủ nhỏ để compiler đầu tiên triển khai nhanh, nhưng đủ mạnh để compiler đó có thể mở rộng chính nó và tiến dần đến full Axiom mà không phải thiết kế lại compiler.**

---

# 1. Bootstrap strategy

Axiom sử dụng mô hình:

```text
Stage 0
External implementation language
        │
        ▼
Bootstrap Compiler
        │
        ▼
Axiom Bootstrap Subset
        │
        ▼
Native executable
        │
        ▼
Stage 1 Axiom Compiler
        │
        ▼
Stage 2
        │
        ▼
Self-hosted Axiom Compiler
```

Điểm quan trọng:

**Bootstrap compiler không phải là một compiler khác về semantics.**

Nó là implementation đầu tiên của cùng Axiom Semantic Kernel.

---

# 2. Không xây "toy language"

Không nên làm:

```text
MiniAxiom
 ├── int
 ├── fn
 └── print
```

rồi sau đó:

```text
MiniAxiom → Full Axiom
```

vì sẽ tạo hai semantics.

Thay vào đó:

```text
Full Axiom Specification
        │
        ├── Bootstrap subset
        │
        └── Remaining features
```

Bootstrap subset chỉ là:

```text
Axiom language
with features not yet implemented
```

---

# 3. Bootstrap subset

Stage 0 hỗ trợ:

```text id="6d6x0g"
module
import/use

fn
return

let
let mut

primitive types
struct
enum

arrays

if
else
loop
while
break
continue

match

operators

function calls

basic generics

const

Option
Result

basic ownership
Move
Copy
Drop

view
mut_view
```

Có thể chưa hỗ trợ:

```text id="m0h8m2"
async
GPU
runtime reflection
dynamic loading
advanced comptime
full macro system
advanced SIMD
distributed networking
```

---

# 4. Bootstrap language grammar subset

Canonical:

```axiom id="4bq4cj"
fn main() {
    let x = 10
    let y = 20
    print(x + y)
}
```

Function:

```axiom id="v3xj1c"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Struct:

```axiom id="3m6i3g"
struct Point {
    x: i32
    y: i32
}
```

Enum:

```axiom id="j0pxev"
enum Option<T> {
    Some(T)
    None
}
```

---

# 5. Bootstrap types

Stage 0:

```text id="o5yn99"
bool

i8
i16
i32
i64

u8
u16
u32
u64

isize
usize

f32
f64

unit
never
```

Không cần ngay:

```text id="bh0mve"
i128
u128
f16
bf16
fp8
```

nhưng TypeDB phải được thiết kế để thêm chúng mà không thay đổi architecture.

---

# 6. Literals

Bootstrap hỗ trợ:

```axiom id="5rq5n7"
0
42
-42

0u32
42i64

3.14
3.14f32

true
false

"hello"
```

Integer literal typing phải deterministic.

Không dùng heuristic:

```text
"compiler đoán type"
```

---

# 7. Variable model

```axiom id="h3v6xi"
let x = 10
```

semantic:

```text id="4j1f9b"
x : i32
ownership = Owned
```

Mutable:

```axiom id="5jv07b"
let mut x = 10
x = 20
```

---

# 8. Assignment

Assignment không phải implicit clone.

```axiom id="2b6y5h"
let a = String(...)
let b = a
```

→ Move.

Trong khi:

```axiom id="0i3kca"
let a = 10
let b = a
```

→ Copy nếu `i32: Copy`.

---

# 9. Bootstrap ownership

Stage 0 phải có ownership ngay từ đầu.

Không được:

```text id="c2yqg3"
Stage 0
    ↓
GC
    ↓
Stage 1
    ↓
remove GC
```

vì compiler architecture sẽ bị thiết kế sai.

---

# 10. Bootstrap Drop

Một resource type:

```axiom id="g0c3pr"
struct File {
    ...
}
```

có Drop semantics.

Compiler phải có:

```text id="y4fj9p"
StorageLive
StorageDead
Drop
```

ngay từ MIR đầu tiên.

---

# 11. Nhưng chưa cần allocator phức tạp

Bootstrap compiler không cần implement ngay:

```text id="i2d2sn"
Arc
Vec
Arena
Pool
TLS
custom allocator
```

Chỉ cần semantic infrastructure:

```text id="nhx6y1"
owned value
Drop
storage
```

---

# 12. Bootstrap views

Phải hỗ trợ:

```axiom id="ng1j3x"
fn sum(x: view<[4]i32>) -> i32
```

và:

```axiom id="03r4hl"
fn fill(x: mut_view<[4]i32>) {
    ...
}
```

Compiler verifier ban đầu có thể giới hạn region analysis nhưng **semantic representation phải đầy đủ**.

---

# 13. Arrays

Bootstrap:

```axiom id="gnx9na"
let a: [4]i32 = [1, 2, 3, 4]
```

Index:

```axiom id="khph8k"
a[i]
```

Bounds safety:

```text id="5qg4d4"
0 <= i < 4
```

Nếu compiler không chứng minh được:

```text id="9m82ka"
runtime bounds check
```

được sinh ra.

---

# 14. Bounds-check elimination

Ngay Stage 0 architecture phải có hook:

```text id="j99f0m"
RangeInfo
```

để sau này optimizer có thể biến:

```text id="6b6j83"
for i in 0..4 {
    a[i]
}
```

thành code không bounds-check nếu proof tồn tại.

---

# 15. `if`

```axiom id="h4l1b6"
if x > 0 {
    foo()
} else {
    bar()
}
```

HIR:

```text id="4gjm9q"
If
```

MIR:

```text id="m9ptt8"
Branch
```

---

# 16. `loop`

```axiom id="9qbyy6"
loop {
    ...
}
```

MIR:

```text id="2z2yjm"
BB0 → BB1 → BB0
```

Ownership analysis phải xử lý loop fixed point.

---

# 17. `match`

Stage 0 hỗ trợ exhaustive match.

```axiom id="v6o7q1"
match value {
    Some(x) => use(x)
    None => fallback()
}
```

Pattern checker chạy trước MIR lowering.

---

# 18. `Option`

`Option<T>` phải là ordinary enum:

```axiom id="v6c5k3"
enum Option<T> {
    Some(T)
    None
}
```

Không có compiler magic ngoại trừ syntax/optimization nếu được định nghĩa.

---

# 19. `Result`

Tương tự:

```axiom id="l44p2q"
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

`?` có thể ban đầu lower trực tiếp thành `match`.

---

# 20. `?` bootstrap lowering

```axiom id="i9f5tq"
let value = operation()?
```

→

```text id="oz2xqa"
tmp = operation()

switch tmp:
    Ok(v) → value = v
    Err(e) → return Err(e)
```

Không cần exception runtime.

---

# 21. Functions

Function declaration:

```text id="j0d5pf"
FunctionId
Signature
Body
GenericParams
Effects
ABI
```

Function call:

```text id="w5gq0q"
Call(FunctionId, Arguments)
```

---

# 22. Methods

Stage 0 vẫn hỗ trợ method syntax:

```axiom id="z8ip6n"
point.length()
```

nhưng parser/resolver canonicalizes:

```text id="e9p1cb"
length(point)
```

Do đó compiler không cần xây OOP runtime.

---

# 23. Traits

Bootstrap trait subset:

```axiom id="1c1j3s"
trait Add {
    fn add(self: Self, other: Self) -> Self
}
```

Implementation:

```axiom id="c0v1t3"
impl Add for Vec2 {
    fn add(self: Vec2, other: Vec2) -> Vec2 {
        ...
    }
}
```

---

# 24. Generic static dispatch

```axiom id="lqg0a9"
fn add<T: Add>(a: T, b: T) -> T {
    a.add(b)
}
```

Stage 0 ưu tiên:

```text id="4vlzv8"
monomorphization
```

chưa cần `dyn Trait`.

---

# 25. Why static dispatch first?

Vì compiler có thể kiểm tra:

```text id="q2m0iz"
trait resolution
→ concrete function
→ direct call
```

đơn giản hơn rất nhiều so với dynamic dispatch.

Sau này thêm:

```text id="ez9pkr"
dyn Trait
```

không cần thay semantic model.

---

# 26. Generic compiler implementation

Compiler generic representation:

```text id="y6q4st"
GenericFunction
GenericParams
Constraints
Instantiation
```

không hard-code:

```text id="qj7f4h"
max_i32
max_i64
max_f32
```

---

# 27. Monomorphization

Ví dụ:

```axiom id="r6rj4e"
max<i32>
```

compiler tạo:

```text id="1s72ng"
GenericInstanceId
```

sau đó:

```text id="s5q6pr"
HIR
 ↓
MIR
 ↓
specialized MIR
```

---

# 28. Bootstrap comptime

Stage 0 chỉ cần:

```text id="cr5t80"
const
```

và subset nhỏ của:

```text id="q3asw4"
comptime
```

đủ để compiler tự xây metadata/code tables.

Không cần ngay:

```text id="v8m5h0"
filesystem
network
execute tool
dynamic declaration generation
```

---

# 29. Compiler bootstrap data structures

Đây là điểm quan trọng.

Compiler đầu tiên cần dùng chính các abstraction mà Axiom sau này sẽ cung cấp:

```text id="m7rjpf"
Vec<T>
Map<K,V>
String
Option<T>
Result<T,E>
Arena<T>
```

Trong Stage 0, các abstraction này có thể được implement bằng bootstrap implementation language.

Nhưng API semantic phải là Axiom-compatible.

---

# 30. CompilerDB Stage 0

Không bỏ CompilerDB vì “bootstrap cho nhanh”.

Ngay từ đầu:

```text id="v9okgq"
CompilerDB
├── SourceDB
├── SyntaxDB
├── DeclarationDB
├── TypeDB
├── TraitDB
├── HIRDB
├── MIRDB
├── DiagnosticDB
├── SourceMapDB
└── BuildDB
```

Một số DB chưa hoàn chỉnh nhưng interface tồn tại.

---

# 31. Why this matters for self-hosting

Nếu bootstrap compiler viết kiểu:

```text id="n0s0ak"
global mutable maps
hard-coded parser
hard-coded types
```

thì Stage 1 sẽ phải rewrite.

Thay vào đó:

```text id="vqlw4h"
Stage 0
   ↓
same CompilerDB architecture
   ↓
Stage 1
   ↓
replace implementations progressively
```

---

# 32. Bootstrap MIR subset

MIR Stage 0:

```text id="8w0y7r"
StorageLive
StorageDead

Assign
Copy
Move

Load
Store

BinaryOp
UnaryOp

Aggregate

MakeView
MakeMutView

Cast

Call

Drop

Branch
Jump
Switch

Return
Panic

Unreachable
```

---

# 33. No target instructions in MIR

Không:

```text id="9a1hfj"
MIR::MOV_EAX
MIR::ADD_RAX
```

MIR vẫn semantic.

---

# 34. Minimal verifier

Stage 0 verifier bắt buộc:

```text id="6f3q2p"
definite initialization
move checking
double-drop checking
basic capability validity
view lifetime
mutable exclusivity
return validity
basic Send/Share boundary
```

Không cần toàn bộ sophisticated alias analysis ngay.

---

# 35. Layered verification

Verifier API:

```text id="x7x7c4"
verify_basic()
verify_ownership()
verify_capabilities()
verify_effects()
verify_concurrency()
verify_async()
verify_gpu()
verify_ffi()
```

Stage 0 gọi subset:

```text id="jbrl4g"
basic
ownership
capability
effects
```

---

# 36. First backend: LLVM adapter

Bootstrap backend:

```text id="7a5q5v"
Verified MIR
      ↓
Axiom LLVM Lowering
      ↓
LLVM IR
      ↓
LLVM
      ↓
Object
      ↓
LLD
```

---

# 37. LLVM boundary

LLVM adapter phải nhận:

```text id="g2r1x0"
Verified MIR
+
Layout
+
ABI
+
TargetSpec
```

Không nhận AST.

Không nhận unresolved HIR.

Không nhận unchecked MIR.

---

# 38. LLVM type mapping

Ví dụ:

```text id="4t5xoc"
Axiom i32 → LLVM i32
Axiom u64 → LLVM i64
Axiom f32 → LLVM float
Axiom f64 → LLVM double
```

Struct mapping phụ thuộc:

```text id="5u1p8y"
ABI
repr
layout
```

---

# 39. Ownership disappears at backend

Ví dụ:

```axiom id="2o3pr0"
let b = a
```

ownership verifier xử lý:

```text id="q1f3la"
a → Moved
b → Owned
```

LLVM backend thường không cần emit instruction cho Move.

Đây chính là:

> **Semantic overhead ≠ machine overhead.**

---

# 40. Drop lowering

Nếu:

```text id="x2w0h5"
T: Drop
```

MIR:

```text id="u8y6l0"
Drop(x)
```

LLVM backend emit call/inline code tương ứng.

Nếu compiler chứng minh Drop không có observable effect:

```text id="v9df7g"
Drop(x)
```

có thể eliminate theo optimization rules.

---

# 41. First executable

Canonical test:

```axiom id="k5x7i1"
fn main() {
    let a: i32 = 10
    let b: i32 = 20
    let c = a + b

    print(c)
}
```

Expected:

```text
30
```

Pipeline:

```text id="f3rj0s"
source
 ↓
lexer
 ↓
parser
 ↓
AST
 ↓
resolver
 ↓
type checker
 ↓
HIR
 ↓
MIR
 ↓
verifier
 ↓
LLVM
 ↓
object
 ↓
link
 ↓
native executable
```

---

# 42. First compiler test

Ngay sau Hello World phải có:

```text id="c4z8c0"
compile_test.ax
```

với:

```axiom id="3w9q2m"
fn square(x: i32) -> i32 {
    x * x
}

fn main() {
    let x = square(5)
    print(x)
}
```

Expected:

```text
25
```

---

# 43. First negative test

```axiom id="g8x5x9"
fn main() {
    let x: String = ...
    let y = x
    print(x)
}
```

Expected diagnostic:

```text id="v4q5x3"
AOWN-001
use of moved value
```

Đây là test cực kỳ quan trọng.

---

# 44. First capability test

```axiom id="n8d7j2"
fn read(x: view<[4]i32>) {
    ...
}
```

Compiler phải tạo:

```text id="7p6v0k"
READ capability
```

và bảo đảm owner sống đủ lâu.

---

# 45. First mutable capability test

```axiom id="6r1v6y"
fn write(x: mut_view<[4]i32>) {
    ...
}
```

Concurrent/read conflict phải được verifier nhận diện.

---

# 46. First Drop test

Resource:

```axiom id="k1z8d9"
struct Resource { ... }
```

với Drop.

Test:

```text id="9h2u3c"
scope exit
→ exactly one Drop
```

Test thêm:

```text id="c6u4n1"
early return
→ exactly one Drop
```

và:

```text id="3m4p6k"
panic
→ correct cleanup according to panic profile
```

---

# 47. First optimization test

Source:

```axiom id="w3s9j7"
let x = 10
let y = x
print(y)
```

Semantic Move/Copy operations có thể không xuất hiện trong machine code.

Test không kiểm tra exact assembly.

Kiểm tra:

```text id="2d7m3f"
observable output == 10
```

---

# 48. First optimizer

Không cần viết optimizer khổng lồ.

Stage 0:

```text id="q3a7b2"
Constant folding
Dead code elimination
Basic CFG simplification
Copy propagation
Simple inlining
```

Nhưng OptIR architecture phải tồn tại.

---

# 49. First target

Ưu tiên:

```text id="x1c8w4"
x86_64 Windows
```

sau đó:

```text id="k6s1a2"
x86_64 Linux
AArch64
WASM
```

TargetSpec đã được thiết kế độc lập nên không cần thay frontend.

---

# 50. Bootstrap runtime

First executable có thể dùng runtime tối thiểu:

```text id="j5h9x3"
Startup
Print
Exit
```

Không link:

```text id="h2g6j1"
GC
async
GUI
network
reflection
```

---

# 51. `print`

`print` không cần là Core primitive.

Nó là:

```text id="7f2j3x"
std::io::print
```

Compiler bootstrap có thể hard-code một **temporary platform intrinsic**, nhưng phải đặt dưới std/platform boundary.

Không đưa:

```text id="5f8j2k"
print
```

vào Semantic Kernel.

---

# 52. Bootstrap temporary intrinsic rule

Nếu bootstrap cần intrinsic:

```text id="5j4x0v"
@bootstrap_intrinsic("...")
```

thì phải có:

```text id="m5x7d1"
semantic definition
fallback or target constraint
```

và có kế hoạch loại bỏ khi std/platform layer hoàn thiện.

---

# 53. Stage 0 artifact

Build:

```text id="6h8s3q"
ax-bootstrap
```

có thể là:

```text id="k5r8y0"
ax-bootstrap.exe
```

nó compile:

```text id="b6v1c4"
hello.ax
```

thành:

```text id="f4z6s2"
hello.exe
```

---

# 54. Stage 1

Sau khi Stage 0 ổn định:

```text id="9x2r7p"
Axiom compiler source
```

bắt đầu viết bằng Axiom subset.

Ban đầu có thể:

```text id="c3m8w1"
20% Axiom
```

sau đó:

```text id="a6q2s4"
50%
70%
90%
100%
```

---

# 55. Self-extension loop

Một feature mới:

```text id="m7v4k8"
Trait associated type
```

được thêm:

```text id="p8q3n1"
Spec
 ↓
Compiler implementation
 ↓
Test
 ↓
Axiom compiler source
 ↓
Self-hosted compiler rebuild
```

Compiler tự trở thành test của chính language.

---

# 56. Stage N/N+1 test

Self-host validation:

```text id="z8x5q2"
Compiler(N)
    compile
Compiler(N source)
    ↓
Compiler(N+1)
```

sau đó:

```text id="j4c9s1"
Compiler(N+1)
    compile same source
```

So sánh:

```text id="e7v3n5"
semantic behavior
compiler test suite
bootstrap identity
```

Không yêu cầu machine binary byte-for-byte giống nhau.

---

# 57. Trust chain

Final trust chain:

```text id="v2h6s0"
Formal Semantic Kernel
        ↓
Reference Interpreter
        ↓
Bootstrap Compiler
        ↓
Axiom Compiler
        ↓
Self-hosted Compiler
```

Mỗi stage phải được kiểm tra bằng stage trước.

---

# 58. Compiler reproducibility

Build compiler với:

```text id="c1s7k3"
same source
same compiler
same target
same dependencies
same comptime inputs
```

phải tạo artifact reproducibly theo profile.

---

# 59. Bootstrap dependency rule

Cho phép:

```text id="n3k8x5"
LLVM
LLD
system SDK
C runtime/platform libraries
```

ở bootstrap.

Không cho phép:

```text id="x4m9q1"
LLVM-specific semantics
LLVM-specific source syntax
LLVM runtime requirement
```

lọt vào Axiom language.

---

# 60. Bootstrap compiler code organization

```text id="y5p2s7"
bootstrap/
├── driver/
├── lexer/
├── parser/
├── ast/
├── resolver/
├── types/
├── traits/
├── hir/
├── mir/
├── verify/
├── comptime/
├── llvm/
├── object/
├── linker/
└── tests/
```

Điều này phải mirror:

```text id="c9r4x2"
compiler/
```

của final compiler.

---

# 61. Điều đặc biệt quan trọng: không fork semantics

Không được có:

```text id="m2f8x7"
Bootstrap semantics
Full Axiom semantics
```

Mà:

```text id="k7c3v1"
Axiom semantics
├── implemented
└── not-yet-implemented
```

Đây là invariant bootstrap quan trọng nhất.

---

# 62. Bootstrap feature gates

Compiler dùng:

```text id="p1x9v4"
FeatureStatus
```

Ví dụ:

```text id="n4k8q2"
async = implemented=false
gpu = implemented=false
dyn_trait = implemented=false
```

Nếu gặp:

```axiom id="j6p3w0"
async fn foo()
```

compiler báo:

```text id="v8r2s5"
feature not implemented in bootstrap compiler
```

chứ không thay đổi semantics.

---

# 63. Bootstrap feature progression

```text id="u5s9x3"
Phase A
Lexer/parser

Phase B
Resolver/types

Phase C
HIR/MIR

Phase D
Ownership/Drop

Phase E
First executable

Phase F
Traits/generics

Phase G
Views/capabilities

Phase H
Comptime

Phase I
Optimizer

Phase J
Axiom-written compiler

Phase K
Self-hosted backend

Phase L
Self-hosted linker
```

---

# 64. First executable gate

Không chuyển sang Stage 1 chỉ vì:

```text id="5q7r2z"
"Hello World chạy"
```

Phải pass:

```text id="g4n6s1"
basic syntax tests
type tests
ownership tests
drop tests
capability tests
match tests
Result/Option tests
MIR interpreter tests
negative tests
native integration tests
```

---

# 65. Bootstrap Gate Matrix

```text
                 Required
Lexer               ✓
Parser              ✓
Resolver            ✓
Types               ✓
HIR                 ✓
MIR                 ✓
Ownership           ✓
Drop                ✓
Capabilities        ✓
Reference interp.   ✓
MIR interp.         ✓
LLVM backend        ✓
Object              ✓
Link                ✓
Native executable   ✓
```

Không cần:

```text
Async               -
GPU                 -
GUI                 -
Network             -
Tensor              -
Reflection runtime  -
```

---

# 66. Frozen invariants

```text id="b8n4q2"
ABOOT-20
Bootstrap is an implementation stage of Axiom, not a separate language.

ABOOT-21
Bootstrap semantics must derive from the same Formal Semantic Kernel as full Axiom.

ABOOT-22
Bootstrap feature omission must never redefine implemented semantics.

ABOOT-23
Unimplemented features must be rejected explicitly rather than silently reinterpreted.

ABOOT-24
Bootstrap compiler architecture must mirror the final compiler architecture where practical.

ABOOT-25
Bootstrap must contain a semantic HIR/MIR boundary.

ABOOT-26
Bootstrap MIR must remain target-independent.

ABOOT-27
Only Verified MIR may enter the bootstrap backend.

ABOOT-28
Bootstrap ownership verification must exist before native code generation.

ABOOT-29
Bootstrap Drop semantics must be deterministic.

ABOOT-30
Bootstrap capability semantics must preserve provenance and lifetime.

ABOOT-31
Bootstrap generic dispatch is static by default.

ABOOT-32
Bootstrap generic implementation must not hard-code individual concrete types.

ABOOT-33
Bootstrap method syntax must lower to ordinary function semantics.

ABOOT-34
Bootstrap Option and Result are ordinary algebraic types.

ABOOT-35
Bootstrap error propagation must not require exception machinery.

ABOOT-36
Bootstrap backend dependencies must remain behind backend boundaries.

ABOOT-37
LLVM must not become Axiom's semantic IR.

ABOOT-38
Bootstrap runtime must contain only components required by the compiled program.

ABOOT-39
Bootstrap must support a minimal native executable vertical slice.

ABOOT-40
Bootstrap compiler correctness must be tested against the reference semantic model.

ABOOT-41
Bootstrap and self-hosted compiler implementations must share the same language semantics.

ABOOT-42
Self-hosting must be an incremental replacement of implementation components rather than a semantic rewrite.

ABOOT-43
The compiler source must eventually be compilable by Axiom itself.

ABOOT-44
Self-hosting validation compares semantic/compiler behavior rather than requiring identical machine binaries.

ABOOT-45
Bootstrap compiler output must be reproducible under equivalent build inputs.

ABOOT-46
Bootstrap temporary intrinsics must have explicit semantic definitions and removal plans.

ABOOT-47
Core semantics must never depend on bootstrap-only intrinsics.

ABOOT-48
Axiom compiler development must preserve the Formal Semantic Kernel as the authority.

ABOOT-49
A compiler feature is complete only when implementation, tests and semantic verification are integrated.

ABOOT-50
The bootstrap path must remain capable of reaching a third-party-toolchain-independent self-hosted compiler.
```

---

# 67. Kết quả của 235

Axiom hiện đã có:

```text
                Axiom Specification
                         │
                         ▼
              Formal Semantic Kernel
                         │
                         ▼
                Compiler Architecture
                         │
                         ▼
              Bootstrap Subset
                         │
                         ▼
               First Executable
                         │
                         ▼
                 Self-hosting
```

Và đặc biệt, chúng ta đã tránh được một cái bẫy rất lớn:

> **Không xây một compiler prototype rồi sau đó vứt bỏ để xây compiler thật.**

Thay vào đó, compiler đầu tiên được thiết kế như **hạt giống của chính compiler cuối cùng**.

---

# TASK TIẾP THEO

## **BOOTSTRAP-236 — AXIOM LEXER, LOSSLESS SYNTAX & TOKEN MODEL**

Bước tiếp theo sẽ đi xuống **tầng code/compiler đầu tiên thực sự**.

Ta sẽ đóng băng cực kỳ chi tiết:

```text
UTF-8 source
    ↓
Character model
    ↓
Unicode handling
    ↓
Lexer
    ↓
TokenKind
    ↓
Token flags
    ↓
SourceSpan
    ↓
Trivia/comments
    ↓
Indentation/newline semantics
    ↓
String/byte literals
    ↓
Numeric literals
    ↓
Operators
    ↓
Keywords
    ↓
Lossless Syntax Tree
```

và quan trọng nhất là thiết kế **token representation đủ tốt cho incremental compilation, formatter, IDE, diagnostics và AI tooling**, thay vì một lexer đơn giản chỉ trả về danh sách token.