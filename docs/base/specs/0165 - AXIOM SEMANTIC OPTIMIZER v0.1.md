Tiếp theo là **Semantic Optimizer v0.1**. Đây là bước rất quan trọng vì mục tiêu của Axiom không chỉ là “biên dịch được native”, mà là **abstraction cao nhưng machine code vẫn gần với cách một lập trình viên C/C++ tối ưu thủ công sẽ viết**.

# AXIOM SEMANTIC OPTIMIZER v0.1

## 1. Vị trí trong pipeline

Chốt pipeline hiện tại:

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
Type Checker
 ↓
Typed HIR
 ↓
Ownership / Capability / Drop / Concurrency
 ↓
MIR
 ↓
Verifier
 ↓
Verified MIR
 ↓
┌─────────────────────────┐
│ Semantic Optimizer      │
└─────────────────────────┘
 ↓
LIR
 ↓
Target Lowering
 ↓
Machine IR
 ↓
Register Allocation
 ↓
Encoder
 ↓
Object
 ↓
Linker
 ↓
Native Binary
```

Điểm quan trọng:

> **Optimizer chỉ được phép tối ưu sau Verified MIR.**

Nó không được tự suy luận lại ownership hoặc type semantics.

---

# 2. Nguyên tắc lớn

Axiom có một lợi thế mà C/C++ không có:

Compiler biết chắc:

```text
ownership
capability
lifetime
Drop
Send
Share
types
bounds
effects
```

Do đó optimizer có thể nhận những facts rất mạnh từ verifier.

Ví dụ:

```axiom
fn sum(a: view<[i32]>) -> i32 {
    var s = 0
    for x in a {
        s = s + x
    }
    s
}
```

Compiler biết:

- `a` không sở hữu data
- `a` hợp lệ trong toàn bộ loop
- đọc-only
- không có mutable capability xung đột
- index hợp lệ nếu iterator abstraction chứng minh
- `s` không escape

→ có thể tạo machine code rất gần vòng lặp C tối ưu.

---

# 3. Optimizer không được phá semantics

Invariant nền:

```text
OPT(program) ≡ program
```

về observable behavior.

Cho phép thay đổi:

```text
instruction count
register usage
memory allocation
storage placement
control flow
branch structure
```

nhưng không được thay đổi:

```text
result
panic behavior
observable I/O
atomic semantics
volatile semantics
FFI-visible behavior
required Drop behavior
```

---

# 4. Đừng bắt đầu bằng LLVM-style optimizer khổng lồ

MVP chỉ cần:

```text
MIR
 ↓
Canonicalization
 ↓
Constant Folding
 ↓
Constant Propagation
 ↓
Copy Propagation
 ↓
Dead Code Elimination
 ↓
CFG Simplification
 ↓
Local Simplification
 ↓
Inlining
 ↓
Bounds Check Elimination
 ↓
Escape Analysis
 ↓
Allocation Elimination
 ↓
LIR
```

Sau đó mới mở rộng.

---

# 5. Optimization Levels

Chốt ban đầu:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

### `-O0`

Mục tiêu:

- compile nhanh
- debug tốt
- gần MIR
- ít biến đổi

Không có nghĩa là “không optimization”.

Một số transformation correctness-required vẫn được thực hiện.

---

### `-O1`

```text
constant folding
constant propagation
DCE
CFG simplification
copy propagation
basic inlining
```

---

### `-O2`

Thêm:

```text
aggressive inlining
bounds elimination
escape analysis
allocation elimination
loop optimization
basic vectorization
```

---

### `-O3`

Thêm các transformation có thể tăng code size:

```text
loop unrolling
aggressive vectorization
more specialization
PGO hooks
```

---

### `-Os`

Ưu tiên:

```text
binary size
I-cache
```

---

### `-Oz`

Cực đại giảm size.

---

# 6. Optimization Pipeline

Không nên chạy pass tùy tiện.

Dùng pass manager:

```text
PassManager
 ├── input invariant
 ├── transformation
 ├── output invariant
 └── analysis dependencies
```

Ví dụ:

```text
ConstantFold
Input:
    Typed MIR

Output:
    Valid MIR

Preserves:
    ownership
    control flow semantics
```

---

# 7. MIR Canonicalization

Trước optimization:

```text
canonicalize(MIR)
```

Mục tiêu:

```text
x + 0
x * 1
copy(copy(x))
redundant blocks
empty blocks
trivial branches
```

được đưa về canonical form.

Ví dụ:

```text
x = COPY(y)
z = COPY(x)
```

→

```text
z = COPY(y)
```

---

# 8. Constant Folding

```axiom
let x = 10 * 20
x + 2
```

MIR:

```text
t1 = MUL 10, 20
t2 = ADD t1, 2
```

→

```text
t1 = 200
t2 = 202
```

→

```text
202
```

Nhưng phải đặc biệt chú ý checked arithmetic.

```axiom
let x = MAX_I32 + 1
```

không được biến thành wrapping result.

Nó phải giữ:

```text
panic/trap
```

nếu semantics yêu cầu checked arithmetic.

---

# 9. Wrapping và Saturating phải khác nhau

```axiom
a + b
a +% b
a +| b
```

là ba semantics khác nhau.

Optimizer không được:

```text
ADD_CHECKED → ADD_WRAP
```

chỉ vì CPU instruction thuận tiện.

Ngược lại, có thể biến:

```text
ADD_CHECKED
```

thành machine `ADD` nếu compiler chứng minh overflow không xảy ra.

---

# 10. Constant Propagation

```axiom
let x = 10

if true {
    x
} else {
    100
}
```

→

```text
10
```

CFG:

```text
       if true
       /     \
      A       B
       \     /
        JOIN
```

→ chỉ giữ A.

---

# 11. Dead Code Elimination

```axiom
fn f() {
    let x = expensive()
    42
}
```

Nếu `x` không được sử dụng và:

```text
expensive()
```

không có observable side effect:

→ loại bỏ.

Nhưng:

```axiom
log()
```

không được loại bỏ nếu có I/O.

---

# 12. Memory Effects

Đây là lúc MIR facts rất hữu ích.

Mỗi call có:

```text
MemoryEffect:
    None
    Read
    Write
    ReadWrite
    Unknown
```

Ví dụ:

```text
pure_add → None
read_file → Write/Unknown
atomic → Atomic effect
volatile → Volatile
```

DCE không được xóa:

```text
CALL effectful()
```

chỉ vì return value không dùng.

---

# 13. Copy Propagation

```text
a = b
c = a
```

→

```text
c = b
```

Nhưng cần ownership facts.

Nếu:

```text
a = MOVE(b)
```

thì không được biến đổi thành ordinary copy.

---

# 14. Move Elimination

Đây là optimization đặc biệt quan trọng cho Axiom.

```axiom
fn make() -> BigStruct {
    var x = ...
    x
}
```

Semantically:

```text
MOVE x → return
```

nhưng không nhất thiết:

```text
memcpy
```

Compiler có thể:

```text
caller allocates result
callee writes directly
```

tức:

```text
NRVO / caller-allocated return
```

mà không thay đổi semantics.

---

# 15. SROA

Scalar Replacement of Aggregates.

Ví dụ:

```axiom
struct Point {
    x: i32
    y: i32
}

fn f() -> i32 {
    let p = Point { x: 10, y: 20 }
    p.x + p.y
}
```

Không cần tạo object:

```text
p
```

Thay bằng:

```text
p.x → register
p.y → register
```

→

```text
30
```

Đây chính là:

> **Abstraction Erasure**

---

# 16. Struct không đồng nghĩa memory object

Điều này cần được giữ rất rõ.

Source:

```axiom
Vec2 { x: 1, y: 2 }
```

không có nghĩa machine phải tạo:

```text
memory:
[x][y]
```

Có thể là:

```text
xmm0 = ...
```

hoặc:

```text
rax = ...
```

hoặc hoàn toàn constant-fold.

---

# 17. Escape Analysis

Đây sẽ là một trong những optimization quan trọng nhất của Axiom.

Ví dụ:

```axiom
fn f() -> i32 {
    let x = Box { value: 42 }
    x.value
}
```

Nếu `x`:

- không escape
- address không observable
- không truyền FFI
- không trả storage identity
- không tạo stable-address requirement

thì:

```text
dynamic storage
```

có thể bị loại bỏ.

Kết quả:

```text
register/local
```

---

# 18. Đây là lý do `Box` không nên định nghĩa là “heap”

Semantic:

```text
Box<T>
```

= owned dynamic storage semantics.

Không phải:

```text
always malloc()
```

Optimizer có quyền:

```text
Box
 ↓
stack
 ↓
register
 ↓
eliminate
```

nếu storage identity không observable.

---

# 19. Khi address observable

Ví dụ:

```axiom
unsafe {
    addr_of(x)
}
```

hoặc FFI yêu cầu stable pointer.

Lúc đó:

```text
address becomes observable
```

→ optimizer không thể tùy tiện scalarize/eliminate storage.

Đây khớp trực tiếp:

```text
AMEM-55
AMEM-70
AMEM-72
```

---

# 20. Allocation Elimination

Ví dụ:

```text
ALLOC x
STORE x, 10
LOAD x
DEALLOC x
```

Nếu không escape:

```text
10
```

Toàn bộ allocation biến mất.

Đây là optimization mà người dùng không cần viết:

```text
stackalloc
placement new
manual free
```

---

# 21. Bounds Check Elimination

Axiom có:

```axiom
a[i]
```

và semantics yêu cầu bounds check.

Nhưng:

```axiom
for i in 0..a.len {
    sum += a[i]
}
```

compiler có thể chứng minh:

```text
0 <= i < len
```

→ bỏ check bên trong loop.

Đây là nơi verifier + optimizer phối hợp.

---

# 22. Không cho optimizer “đoán” safety

Optimizer không được nói:

> “chắc là index hợp lệ”.

Nó chỉ được dùng:

```text
BoundsFact
CapabilityFact
RangeFact
LoopInvariant
```

đã được chứng minh.

Ví dụ:

```text
BoundsFact:
    i ∈ [0, len)
```

→ legal elimination.

---

# 23. Alias Analysis

Axiom capability system cho compiler một nguồn thông tin rất mạnh.

Ví dụ:

```axiom
fn add(
    a: view<[f32]>,
    b: view<[f32]>,
    out: mut_view<[f32]>
)
```

Nếu verifier chứng minh:

```text
a ∩ out = ∅
b ∩ out = ∅
```

optimizer có thể sử dụng:

```text
NoAlias(a, out)
NoAlias(b, out)
```

để vectorize.

Nếu:

```text
UNKNOWN
```

thì không được tự giả định no-alias.

---

# 24. Đây là điểm khác biệt lớn với C

Axiom không cần bắt programmer viết:

```c
float * restrict a
```

chỉ để compiler biết alias.

Compiler đã có:

```text
capability provenance
region relation
ownership facts
```

để chứng minh.

---

# 25. Nhưng không được biến capability thành runtime overhead

Sau:

```text
Verified MIR
```

các capability như:

```text
view
mut_view
provenance
region
ownership
```

có thể bị erase.

LIR chỉ còn:

```text
pointer
length
load
store
```

nếu runtime representation cần chúng.

Nếu không cần thì thậm chí:

```text
length
```

cũng có thể biến mất.

---

# 26. Inlining

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() -> i32 {
    add(10, 20)
}
```

Inlining:

```text
main:
    return 30
```

MVP nên có cost model đơn giản:

```text
tiny function → inline
cold huge function → không inline
```

---

# 27. Generic specialization

Axiom:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

Khi:

```text
max<i32>
```

compiler có thể tạo specialization:

```text
max_i32
```

Optimizer sau đó thấy concrete type:

```text
i32 comparison
```

và tiếp tục tối ưu.

---

# 28. Trait dispatch

Static:

```axiom
fn print<T: Display>(x: T)
```

→ monomorphization.

Dynamic:

```axiom
fn print(x: dyn Display)
```

→ dynamic call.

Optimizer có thể devirtualize dynamic dispatch nếu chứng minh concrete type duy nhất.

Nhưng:

> Không được thay đổi observable dispatch semantics nếu trait object có behavior động thực sự.

---

# 29. Loop optimization

MVP:

```text
loop invariant code motion
induction variable simplification
strength reduction
bounds check elimination
loop unswitching
```

Ví dụ:

```axiom
for i in 0..n {
    x = a * 10
    ...
}
```

Nếu `a` invariant:

```text
x = a * 10

for i in ...
```

---

# 30. Strength Reduction

Ví dụ:

```text
i * 4
```

có thể thành:

```text
i << 2
```

nếu semantics tương đương.

Nhưng optimizer không nên biến mọi multiplication thành shift một cách máy móc. Backend có thể biết:

```text
LEA
```

tốt hơn.

Do đó:

```text
Semantic optimizer
```

không nên chứa quá nhiều x86-specific optimization.

---

# 31. Vectorization

Tách:

```text
High-level vectorization
```

và:

```text
Target vector legalization
```

Ví dụ:

```axiom
for i in 0..n {
    c[i] = a[i] + b[i]
}
```

Optimizer có thể tạo:

```text
VECTOR_ADD
```

LIR.

x86 backend quyết định:

```text
SSE
AVX
AVX2
AVX-512
```

dựa trên target features.

---

# 32. PGO không thuộc v0.1

Nhưng architecture phải chừa:

```text
ProfileData
```

Sau này:

```text
build --profile generate
run
build --profile use
```

Profile có thể cung cấp:

```text
hot/cold
branch probability
call frequency
inline candidates
code layout
```

Không nên đưa vào MVP.

---

# 33. `black_box`

Đã freeze semantic rule cho `black_box`.

Optimizer phải coi:

```text
black_box(x)
```

là optimization barrier phù hợp với contract.

Nhưng:

```text
value semantics
```

không thay đổi.

Nó không phải:

```text
volatile
```

và không phải:

```text
atomic
```

---

# 34. Volatile phải chặn optimizer mạnh hơn

```text
volatile load
volatile store
```

là observable machine memory access.

Optimizer không được:

```text
merge
remove
reorder
```

trái với volatile semantics.

Volatile cũng không tạo synchronization/happens-before.

---

# 35. Atomics

Optimizer phải tôn trọng:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Ví dụ không được biến:

```text
Acquire
```

thành ordinary load chỉ vì value type giống nhau.

Atomic semantics đi xuống LIR:

```text
ATOMIC_LOAD
ordering = Acquire
```

sau đó backend mới map xuống instruction sequence.

---

# 36. Drop và optimization

Đây là vùng rất dễ sai.

Ví dụ:

```axiom
let x = Resource(...)
x
```

Compiler không được xóa:

```text
DROP(x)
```

nếu Drop có observable effect.

Nhưng:

```text
Drop(Resource)
```

nếu compiler biết resource abstraction không có observable behavior trong context cụ thể thì có thể tối ưu theo rules tương ứng.

Không được giả định:

> Drop = free.

---

# 37. Dead allocation vs dead resource

Hai thứ khác nhau:

```text
memory dead
```

không đồng nghĩa:

```text
resource dead
```

Ví dụ:

```text
FileHandle
```

có thể cần:

```text
close
```

dù memory object đã scalarized.

Optimizer phải giữ **resource semantics**, nhưng có thể thay đổi storage.

---

# 38. Optimization facts

Nên có một hệ thống facts:

```text id="0n5p7d"
OptimizationFacts
├── Constant
├── Range
├── NonNull
├── NoAlias
├── ReadOnly
├── NoEscape
├── StableAddress
├── KnownLength
├── Alignment
├── Cold
├── Hot
├── Pure
├── NoPanic
└── Dominates
```

Nhưng:

> Fact phải có provenance.

Ví dụ:

```text
NoAlias
source = CapabilityVerifier
confidence = Proven
```

Không phải optimizer tự gắn:

```text
NoAlias = true
```

---

# 39. Fact provenance

Ví dụ:

```text
Fact {
    kind: NoAlias
    values: [a, b]
    source: CapabilityAnalysis
    proof_id: CAP_182
}
```

Điều này cực kỳ hữu ích cho debug:

```text
why did compiler vectorize this?
```

→

```text
NoAlias proved by capability analysis
```

---

# 40. Debug optimization explanation

Nên có:

```text
axiom explain-opt foo
```

Ví dụ:

```text
Inlining:
    add(i32,i32)
    cost = 3
    threshold = 12
    reason = inline

Bounds Check:
    index i
    range [0,n)
    length n
    result = eliminated

Allocation:
    Box<Point>
    escape = false
    address_observable = false
    result = scalarized
```

Đây sẽ là một tính năng rất mạnh khi dùng AI agent phát triển/compiler-debug.

---

# 41. Pass dependency

Ví dụ:

```text
EscapeAnalysis
```

phải chạy trước:

```text
AllocationElimination
```

Còn:

```text
Capability facts
```

đã có trước optimizer.

Pass manager:

```text
require:
    VerifiedMIR
    CapabilityFacts
    OwnershipFacts
```

---

# 42. Optimization correctness

Đừng chỉ test output.

Mỗi pass:

```text
Input MIR
 ↓
Pass
 ↓
Output MIR
 ↓
Verifier
```

Nếu output không còn hợp lệ:

```text
AXC_INTERNAL_OPT_0001
optimizer produced invalid MIR
```

Optimizer **không được bypass verifier**.

---

# 43. Oracle differential testing

Với mỗi chương trình:

```text
source
```

chạy:

```text
Oracle(source)
```

và:

```text
Native(source, -O0)
Native(source, -O1)
Native(source, -O2)
Native(source, -O3)
```

So sánh observable behavior:

```text
exit code
stdout
stderr
panic
trap
observable I/O
```

Đây là nền tảng cực mạnh để phát hiện optimizer bug.

---

# 44. Optimization equivalence

Test:

```text
-O0 == -O1 == -O2 == -O3
```

về semantic result.

Không yêu cầu machine code giống nhau.

Ví dụ:

```text
-O0
    12 instructions

-O3
    2 instructions
```

vẫn đúng nếu observable behavior giống nhau.

---

# 45. Fuzzing

Sau khi MIR ổn định:

```text
random valid source
        ↓
      MIR
        ↓
  random optimizer
        ↓
   Oracle vs native
```

Các vùng fuzz quan trọng:

```text
integer overflow
branches
loops
match
Option
Result
Drop
partial move
views
alias
atomic
panic
async
```

---

# 46. Optimizer architecture

Chốt:

```text id="6ylxdp"
compiler/optimizer/
├── analysis/
│   ├── cfg.ax
│   ├── dominator.ax
│   ├── liveness.ax
│   ├── range.ax
│   ├── alias.ax
│   ├── escape.ax
│   ├── purity.ax
│   └── loop.ax
│
├── scalar/
│   ├── constant_fold.ax
│   ├── constant_prop.ax
│   ├── copy_prop.ax
│   ├── sroa.ax
│   └── dce.ax
│
├── control/
│   ├── cfg_simplify.ax
│   ├── jump_thread.ax
│   └── branch.ax
│
├── memory/
│   ├── bounds.ax
│   ├── allocation.ax
│   └── load_store.ax
│
├── inline/
│   ├── cost.ax
│   └── inline.ax
│
├── loop/
│   ├── canonicalize.ax
│   ├── licm.ax
│   ├── induction.ax
│   └── unroll.ax
│
├── vector/
│   └── vectorize.ax
│
├── pass.ax
├── pipeline.ax
├── facts.ax
├── explain.ax
└── tests/
```

---

# 47. Invariants

Đề nghị freeze:

```text
AOPT-20
Optimizer input must be Verified MIR.

AOPT-21
Optimizer must preserve observable semantics.

AOPT-22
Optimizer may not weaken ownership guarantees.

AOPT-23
Optimizer may not invalidate capability validity.

AOPT-24
Optimizer may not invent alias facts without proof.

AOPT-25
Optimizer may use verifier-established alias facts.

AOPT-26
Optimizer may erase ownership metadata after semantic verification.

AOPT-27
Optimizer may eliminate unobservable allocations.

AOPT-28
Optimizer may change storage placement when address identity is not observable.

AOPT-29
Observable address identity constrains optimization.

AOPT-30
Resource Drop semantics must be preserved.

AOPT-31
Atomic ordering semantics must be preserved.

AOPT-32
Volatile semantics must be preserved.

AOPT-33
Checked arithmetic semantics must be preserved.

AOPT-34
Optimization level cannot change language semantics.

AOPT-35
Optimization passes must be deterministic.

AOPT-36
Optimization passes must declare required facts/invariants.

AOPT-37
Optimizer output must pass MIR verification.

AOPT-38
Optimization diagnostics must be reproducible.

AOPT-39
Oracle and native optimized execution must be differentially testable.

AOPT-40
Target-specific optimization must not leak into target-neutral semantic MIR.
```

---

# 48. Milestone OPT-001

Không nên bắt đầu với vectorization.

Làm vertical slice nhỏ:

```text
OPT-001
Constant folding
```

Test:

```axiom
fn main() -> i32 {
    10 + 20 * 3
}
```

Expected MIR after optimization:

```text
RETURN 70
```

---

# 49. OPT-002 → OPT-010

```text
OPT-001  Constant folding
OPT-002  Constant propagation
OPT-003  Copy propagation
OPT-004  DCE
OPT-005  CFG simplification
OPT-006  Local simplification
OPT-007  Inlining
OPT-008  Bounds-check elimination
OPT-009  Escape analysis
OPT-010  Allocation elimination
```

Sau đó:

```text
OPT-011  SROA
OPT-012  LICM
OPT-013  induction-variable optimization
OPT-014  load/store optimization
OPT-015  basic vectorization
OPT-016  loop unrolling
OPT-017  code-size optimization
```

---

# 50. Điều quan trọng nhất sau OPT-010

Khi tới đây, Axiom sẽ có một chuỗi thực sự đáng kể:

```text
Axiom source
 ↓
type-safe
 ↓
ownership-safe
 ↓
capability-safe
 ↓
resource-safe
 ↓
optimized
 ↓
x86 machine code
 ↓
own ELF object
 ↓
own linker
 ↓
native executable
```

Và lúc này ta **không nên tiếp tục mở rộng feature ngôn ngữ ngay**.

Bước kế tiếp hợp lý là xây **Benchmark + Conformance Harness** để đo Axiom so với C/C++/Rust ở các microbenchmark thực tế, đồng thời kiểm tra:

```text
binary size
startup cost
allocation count
instruction count
branch count
memory usage
compile time
-O0/-O2/-O3
```

Quan trọng hơn, harness phải trở thành **cổng kiểm soát**: một optimization mới chỉ được chấp nhận khi vừa giữ được Oracle equivalence, vừa không âm thầm làm xấu các workload đã được xác lập.