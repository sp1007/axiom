# Part XXVI — Semantic Oracle · Reference Interpreter · Conformance · Differential Testing

Nếu Part XXV định nghĩa **compiler phải biến Axiom thành machine code như thế nào**, thì Part XXVI định nghĩa thứ còn quan trọng hơn:

> **Làm sao biết compiler đang biên dịch đúng?**

Với một ngôn ngữ systems language có ownership, capability, async, concurrency, atomics, GPU, FFI và optimizer mạnh, chỉ unit test compiler là chưa đủ.

Axiom cần một **Semantic Oracle** độc lập với production compiler.

---

# XXVI.1. Semantic Oracle là gì?

Oracle là một implementation tham chiếu của semantics Axiom.

```text id="7v9d0h"
Axiom Source
      │
      ├───────────────┐
      ▼               ▼
 Semantic Oracle   Production Compiler
      │               │
      ▼               ▼
 Expected         Native Binary
 Behavior             │
      │               ▼
      └──────────→ Compare
```

Oracle không nhằm chạy nhanh.

Mục tiêu của Oracle là:

- đúng;
- đơn giản;
- dễ kiểm tra;
- deterministic;
- dễ instrument;
- độc lập với optimizer/backend.

---

# XXVI.2. Oracle Không Phải Runtime

Đây là distinction quan trọng:

```text
Oracle
≠
Axiom Runtime
```

Oracle có thể dùng:

```text
heap simulator
virtual scheduler
virtual filesystem
virtual atomics
virtual GPU
```

mà production program không có.

---

# XXVI.3. Oracle Không Được Dùng Để Chạy Production

Không:

```text
axiom build
→ Oracle
→ native
```

mà:

```text
axiom run
→ native
```

Oracle chỉ dành cho:

```text
axiom interpret
axiom test --oracle
compiler test
conformance
differential testing
```

---

# XXVI.4. Oracle Input

Oracle không nên parse source theo một grammar hoàn toàn khác.

Có thể:

```text
Source
 ↓
Frontend
 ↓
Typed HIR
 ↓
MIR
 ↓
Oracle
```

Nhưng có một nguy cơ:

> Nếu frontend sai, Oracle và compiler cùng sai.

Do đó Oracle cần **nhiều tầng validation**.

---

# XXVI.5. Oracle Không Nên Phụ Thuộc Backend

Kiến trúc:

```text id="zazb7n"
Source
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ├────────→ Oracle Interpreter
 │
 └────────→ Production Backend
```

Oracle dừng ở MIR.

Nó không biết:

```text
x86
ARM
register allocation
ELF
```

---

# XXVI.6. MIR Là Semantic Execution Contract

Ta đã định nghĩa MIR là semantic representation.

Do đó:

> **MIR phải có semantics đủ rõ để Oracle có thể execute từng instruction.**

Ví dụ:

```text id="s2o4fc"
ADD
MOVE
LOAD
STORE
CALL
DROP
VIEW
VIEW_MUT
BRANCH
PANIC
ATOMIC_CAS
```

đều có semantic definition.

---

# XXVI.7. Oracle RuntimeValue

Oracle cần value model:

```text id="d7qv9b"
RuntimeValue =
    Bool
    Integer
    Float
    Tuple
    Struct
    Enum
    Array
    Function
    Closure
    View
    MutView
    RawPointer
```

---

# XXVI.8. Integer Representation

Oracle không dùng host language integer một cách mù quáng.

Ví dụ:

```text id="r6wq3v"
i8
u8
i16
u16
...
```

phải có width/sign semantics riêng.

Điều này đặc biệt quan trọng với:

```text
overflow
wrapping
shifts
casts
```

---

# XXVI.9. Overflow

Axiom đã chốt:

```text id="g0j4x6"
+
-
*
```

checked semantics mặc định.

Wrapping:

```text id="s4l0u5"
+%
-%
*%
```

Saturating:

```text id="g9p3aa"
+|
-|
*|
```

Oracle phải thực hiện chính xác.

---

# XXVI.10. Floating Point

Oracle phải định nghĩa mức độ chính xác.

Không được giả định:

```text
host float == Axiom f32
```

một cách tuyệt đối.

Production backend có thể dùng:

```text
IEEE-754 hardware
```

nhưng Oracle cần xác định semantic contract.

---

# XXVI.11. Memory Model

Oracle có simulated memory:

```text id="o8w7l3"
Allocation {
    id
    type
    size
    alignment
    state
    bytes
}
```

Mỗi allocation có:

```text id="r1gqvt"
AllocationId
```

không phải host address.

---

# XXVI.12. Vì Sao Không Dùng Host Pointer?

Nếu Oracle dùng pointer thật:

```text id="n7h9ec"
void*
```

thì:

- UB của host language có thể ảnh hưởng Oracle;
- dangling pointer khó phát hiện;
- provenance khó kiểm tra;
- allocator behavior khó deterministic.

Thay vào đó:

```text id="l7hrj0"
Pointer {
    allocation_id
    offset
    provenance
}
```

---

# XXVI.13. Oracle Có Thể Bắt Use-After-Free

Ví dụ:

```axiom id="aqc9m1"
let b = Box.new(42)
let p = raw_ptr(b)

drop(b)

unsafe {
    load(p)
}
```

Oracle có thể phát hiện:

```text id="o5u0c9"
invalid access:
allocation already released
```

production behavior trong unsafe có thể target-defined/machine-level, nhưng Oracle vẫn hữu ích để test semantic contracts mà Axiom đã định nghĩa.

---

# XXVI.14. View Capability

Oracle view:

```text id="r0e6x9"
View {
    owner: AllocationId
    region
    access: READ
}
```

Mutable:

```text id="kq9c2v"
MutView {
    owner: AllocationId
    region
    access: WRITE
}
```

---

# XXVI.15. Oracle Không Chỉ Execute

Oracle còn phải verify runtime invariants:

```text id="9uhw0e"
owner alive?
region valid?
read/write conflict?
drop valid?
move valid?
```

Nó trở thành một semantic debugger rất mạnh.

---

# XXVI.16. Ownership State

Oracle tracking:

```text id="7c2zq1"
UNINIT
OWNED
PARTIAL
MOVED
DROPPED
```

phải tương thích với MIR verifier.

Nhưng nên có một nguyên tắc:

> Production verifier và Oracle không dùng chung implementation logic ở mức có thể che giấu cùng một bug.

Có thể dùng chung **specification**, nhưng không nên dùng chung toàn bộ algorithm.

---

# XXVI.17. Event Log

Oracle có event stream:

```text id="m0f1se"
CALL
RETURN
ALLOC
DEALLOC
DROP
MOVE
PANIC
TRAP
IO
ATOMIC
LOCK
UNLOCK
SPAWN
JOIN
SEND
RECEIVE
SUSPEND
RESUME
```

Ví dụ:

```text id="x1y0gc"
ALLOC #1
CALL f
MOVE #1
DROP #1
RETURN
```

---

# XXVI.18. Event Log Không Phải Observable Output

Event log là test instrumentation.

Production semantics chỉ expose events được spec coi là observable.

Điều này tránh việc optimizer bị ép phải giữ mọi internal event.

---

# XXVI.19. Observable Result

Oracle execution result nên chuẩn hóa:

```text id="7r5yda"
ExecutionResult {
    status
    return_value
    stdout
    stderr
    panic
    trap
    exit_code
    observable_events
}
```

---

# XXVI.20. Deterministic Execution

Mặc định:

```text id="5lqg0g"
deterministic_scheduler = true
```

cho concurrency test.

Ví dụ:

```text id="3m9jdb"
Thread A
Thread B
```

Oracle có scheduler controlled:

```text id="u0d6yl"
A → B → A → A → B
```

---

# XXVI.21. Vì Sao Cần Deterministic Scheduler?

Nếu test concurrency bằng OS scheduler:

```text id="p7xk3w"
sometimes pass
sometimes fail
```

rất khó debug.

Oracle có thể replay:

```text id="j4y1tc"
schedule #18273
```

để tái hiện chính xác.

---

# XXVI.22. Concurrency State

Oracle giữ:

```text id="8drz7w"
ThreadState
TaskState
FutureState
MutexState
ChannelState
AtomicMemory
```

---

# XXVI.23. Atomics

Oracle phải mô phỏng:

```text id="11z2oo"
Relaxed
Acquire
Release
AcqRel
SeqCst
```

không đơn giản biến tất cả thành sequential consistency.

Nếu Oracle làm sai memory model thì differential testing vô dụng.

---

# XXVI.24. Atomic Litmus Tests

Axiom nên có test suite:

```text id="y5f1h0"
Store Buffering
Load Buffering
Message Passing
IRIW
CAS
```

để kiểm tra:

```text
Acquire
Release
SeqCst
```

và optimizer/backend.

---

# XXVI.25. Race Detection

Oracle có thể theo dõi:

```text id="2hx4ca"
READ(region)
WRITE(region)
ATOMIC(region)
LOCK(region)
```

và phát hiện safe program nào tạo conflicting concurrent access.

---

# XXVI.26. Nhưng Oracle Không Thay Verifier

Có hai lớp:

```text id="2qf2w8"
Compile-time:
Semantic Verifier

Runtime test:
Oracle
```

Verifier phải reject invalid safe programs.

Oracle kiểm tra compiler implementation.

---

# XXVI.27. Async Oracle

Oracle có virtual executor:

```text id="qcv5pu"
Future
 ↓
poll
 ↓
Pending
 ↓
Wake
 ↓
poll
 ↓
Ready
```

Không cần OS threads.

---

# XXVI.28. Await Semantics

Oracle phải kiểm tra:

```text id="7z7g4c"
view/mut_view
```

không sống qua `.await`.

Nếu compiler accidentally tạo state field chứa capability:

```text id="xk0e2e"
Oracle/Verifier test
→ fail
```

---

# XXVI.29. Cancellation

Oracle phân biệt:

```text id="5k8f1m"
Future dropped
```

với:

```text id="0t3y2d"
external operation cancelled
```

Đã chốt:

> Drop Future không tự động có nghĩa external operation bị cancellation.

---

# XXVI.30. Panic

Oracle có:

```text id="x3p9ar"
panic_mode = abort
panic_mode = unwind
```

Trong unwind mode:

```text
panic
 ↓
cleanup
 ↓
catch boundary
```

phải được kiểm chứng.

---

# XXVI.31. Drop Verification Test

Một test rất quan trọng:

```axiom id="r0h74g"
fn f() -> Result<(), Error> {
    let a = ResourceA()
    let b = ResourceB()

    operation()?
}
```

Nếu `operation()` fail:

```text id="l5x1fy"
Drop(b)
Drop(a)
return Err
```

Oracle event log phải xác nhận cleanup đúng thứ tự.

---

# XXVI.32. `?` Testing

Source:

```axiom id="1k0q1e"
let x = foo()?
let y = bar(x)?
Ok(y)
```

Oracle phải tương đương với semantic expansion:

```text id="h7v5qv"
match foo() {
    Ok(x) => ...
    Err(e) => return Err(e)
}
```

và cleanup phải giống nhau.

---

# XXVI.33. Property: `?` Không Là Magic

Compiler lowering:

```text id="0kz5g0"
?
 ↓
MIR branches
 ↓
cleanup
 ↓
return
```

Oracle chạy MIR.

Do đó không cần một “special runtime for ?”.

---

# XXVI.34. FFI Oracle

FFI là một boundary khó.

Oracle có thể hỗ trợ modes:

```text id="5kt2g7"
intrinsic
mock
host_callback
unsupported
```

Ví dụ:

```text id="a8xv8d"
extern "C" fn foo(...)
```

test có thể inject mock:

```text id="7f2l0s"
foo → deterministic mock result
```

---

# XXVI.35. Không Giả Lập Toàn Bộ OS

Oracle không cần implement:

```text
Linux
Windows
macOS
```

Nó chỉ cần abstract capability:

```text id="02q0xu"
File
Socket
Clock
Random
Process
```

test có thể inject deterministic provider.

---

# XXVI.36. Time

Không cho Oracle gọi wall clock thật mặc định.

Thay vào đó:

```text id="v8qz7v"
VirtualClock
```

Ví dụ:

```text id="r3f4bq"
now() = 1000
sleep(10)
now() = 1010
```

---

# XXVI.37. Randomness

Oracle:

```text id="a4w7x9"
Seeded RNG
```

Production:

```text id="6jv4mt"
OS entropy
```

Nhưng test có thể inject seed.

---

# XXVI.38. Filesystem

Virtual filesystem:

```text id="7m7l2d"
/
├── input.txt
└── data/
```

Không phụ thuộc host filesystem.

---

# XXVI.39. Network

Mock network:

```text id="q8z4e1"
connect
send
receive
timeout
```

deterministic.

---

# XXVI.40. GPU Oracle

GPU là phần khó nhất.

Không cần mô phỏng GPU hardware đầy đủ.

Thay vào đó:

```text id="9c0b5f"
@kernel
 ↓
Kernel semantic execution
```

có thể chạy kernel như deterministic scalar/SIMD simulation.

Mục tiêu:

```text
kernel semantics
```

không phải:

```text
GPU performance
```

---

# XXVI.41. GPU Differential Test

Ví dụ:

```axiom id="xj4u3r"
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    ...
}
```

Oracle:

```text id="4c9f31"
scalar execution
```

Native:

```text id="k2d9a0"
GPU execution
```

so sánh buffer output.

---

# XXVI.42. Property Testing

Ngoài test viết tay:

```text id="7c3u5f"
input → expected output
```

Axiom cần property-based generation:

```text id="w8v1zs"
random valid AST
→ compile
→ Oracle
→ native
→ compare
```

---

# XXVI.43. Fuzzing

Các fuzz target:

```text id="7j7j5h"
lexer
parser
resolver
type checker
trait solver
MIR builder
verifier
optimizer
ABI lowering
object writer
linker
```

---

# XXVI.44. Compiler Fuzzer

Ví dụ generate:

```text id="6v4f6e"
struct
enum
generic
trait
closure
async
match
views
moves
drops
```

với depth giới hạn.

Sau đó:

```text id="3t4k0j"
parse
→ compile
→ Oracle
→ native
```

---

# XXVI.45. Metamorphic Testing

Rất mạnh cho optimizer.

Ví dụ source:

```axiom id="v5a0qk"
x + 0
```

và transformed:

```text id="n2c5m7"
x
```

phải có cùng semantics trong context phù hợp.

Một số transformation:

```text
constant folding
dead branch elimination
inline
copy propagation
loop unrolling
```

---

# XXVI.46. Optimization Differential

Test:

```text id="2k4c2u"
-O0
-O1
-O2
-O3
-Os
```

đối chiếu:

```text
Oracle
```

Không chỉ:

```text
-O0 vs -O3
```

vì cả hai compiler output đều có thể cùng sai.

---

# XXVI.47. Triple Differential

Mạnh hơn:

```text id="7r6b4e"
                ┌→ Oracle
Source ─────────┼→ Native -O0
                ├→ Native -O2
                └→ Native alternate backend
```

Ví dụ:

```text
Oracle = 42
O0     = 42
O2     = 42
ARM64  = 42
x86    = 42
```

---

# XXVI.48. Cross-Target Differential

Cùng source:

```text id="3kj5fp"
Axiom
 ├── x86-64
 ├── AArch64
 └── RISC-V
```

Nếu semantics target-independent:

```text id="9m0u1f"
same result
```

trừ những target-defined differences.

---

# XXVI.49. Undefined/Unspecified Behavior

Oracle không được cố tạo “kết quả” cho mọi unsafe operation.

Phải có trạng thái:

```text id="6o1r2v"
DEFINED
PANIC
TRAP
UNSAFE_CONTRACT
TARGET_DEFINED
UNSUPPORTED
```

Nếu program vượt semantic contract:

```text
Oracle
→ không giả tạo expected value
```

---

# XXVI.50. Safe vs Unsafe Test

Safe program:

```text id="3xw1yk"
must have defined semantic behavior
```

Unsafe:

```text id="v1s0f8"
may require explicit contract
```

Test harness phải phân biệt hai loại.

---

# XXVI.51. Conformance Suite

Axiom cần một suite chính thức:

```text id="o1z1kc"
tests/
├── lexical/
├── parser/
├── types/
├── ownership/
├── capability/
├── drop/
├── traits/
├── generics/
├── async/
├── concurrency/
├── atomics/
├── panic/
├── ffi/
├── gpu/
├── comptime/
├── modules/
├── abi/
├── runtime/
└── optimization/
```

---

# XXVI.52. Test Mỗi Rule

Mỗi normative rule:

```text id="3bq9q7"
SPEC rule
 ↓
positive test
 ↓
negative test
 ↓
Oracle test
 ↓
optimization test
```

Ví dụ:

```text id="f3b7s1"
AOWN-30 Drop-bearing type not Copy
```

phải có:

```text
valid Drop
invalid Copy
partial move test
drop ordering test
optimizer test
```

---

# XXVI.53. Test ID

Không dùng test name tùy tiện.

Ví dụ:

```text id="f0h1l7"
AOWN-30-001
AOWN-30-002
AOWN-30-003
```

Khi compiler regression:

```text
AX-REG-...
```

có thể truy ngược tới spec rule.

---

# XXVI.54. Golden MIR

Compiler có thể có:

```text id="9h4r0d"
test.mir.expected
```

Ví dụ:

```text id="f8s7j5"
fn f(x: i32) -> i32
```

expected MIR:

```text id="l0x1a8"
bb0:
    v1 = CONST 1
    v2 = ADD x, v1
    RETURN v2
```

---

# XXVI.55. Nhưng Không Chỉ Golden MIR

Golden test dễ trở thành:

```text
implementation-specific
```

Do đó cần phân biệt:

```text
semantic MIR assertions
```

và:

```text
exact MIR snapshot
```

Exact snapshot chỉ dùng khi thật sự cần.

---

# XXVI.56. Semantic MIR Assertions

Ví dụ test:

```text id="5k0r3c"
assert:
    no DROP for Copy type
    one DROP for owner
    no capability survives await
```

thay vì bắt MIR có đúng từng register ID.

---

# XXVI.57. ABI Conformance

Ví dụ:

```text id="y7h4w3"
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

test:

```text id="h3q8c1"
sizeof
alignof
offset(x)
offset(y)
calling convention
```

so với C ABI expectation.

---

# XXVI.58. ABI Probe

Compiler có thể sinh:

```text id="5n7j2f"
ABI probe program
```

để kiểm tra target.

Ví dụ:

```text
pass Point
return Point
```

và verify actual machine ABI.

---

# XXVI.59. Object/Linker Tests

Object writer cần test:

```text id="g0y6t3"
ELF header
section
symbol
relocation
TLS
debug
```

Linker:

```text id="4z6j0e"
symbol resolution
weak/strong
visibility
relocation
dead stripping
```

---

# XXVI.60. Self-Hosting Bootstrap Test

Khi compiler Axiom được viết bằng Axiom:

```text id="j3s6w4"
Stage N compiler
        ↓
compile Axiom compiler
        ↓
Stage N+1
```

phải so sánh:

```text id="q8r5o1"
semantic output
```

và eventually:

```text
compiler builds itself
```

---

# XXVI.61. Bootstrap Fixed Point

Mục tiêu:

```text id="6w9q3e"
Axiom compiler vN
   compiles
Axiom compiler source
   produces
Axiom compiler vN+1
```

Sau đó:

```text id="g7p2v5"
vN compiler builds vN+1
vN+1 builds vN+1
```

---

# XXVI.62. Oracle Không Được Tự Phụ Thuộc Production Compiler

Một nguy hiểm:

```text id="1x9d8j"
compiler generates MIR
 ↓
Oracle
```

Nếu MIR builder bug, Oracle không thấy source-level error.

Do đó cần:

```text id="6z3k2n"
AST-level semantic tests
HIR-level tests
MIR-level tests
```

và một số independent reference algorithms.

---

# XXVI.63. Reference Type Checker

Có thể có một simplified checker trong Oracle/conformance harness.

Không cần nhanh.

Mục tiêu:

```text id="z5p7h0"
production type checker
vs
reference semantic model
```

---

# XXVI.64. Reference Trait Solver

Tương tự trait solver.

Production:

```text id="4j8k1n"
optimized solver
```

Reference:

```text id="k2c4v7"
simple bounded search
```

Nếu khác:

```text
semantic discrepancy
```

---

# XXVI.65. Oracle Specification Boundary

Có thể định nghĩa:

```text id="w9g4c2"
Axiom Semantic Model
```

gồm:

```text
values
types
ownership
capabilities
evaluation
effects
memory
concurrency
async
panic
ABI-visible behavior
```

Compiler phải implement model này.

---

# XXVI.66. Đây Là “Executable Specification”

Thay vì spec chỉ là text:

```text
SPEC
```

ta có:

```text
SPEC
 ↓
Semantic Model
 ↓
Oracle
 ↓
Tests
```

Do đó:

> **Axiom specification becomes partially executable.**

Đây là lợi thế cực lớn khi AI agents tham gia phát triển compiler.

---

# XXVI.67. AI Agent Integration

AI agent có thể được yêu cầu:

```text id="5v7x3b"
implement feature
```

Harness tự động:

```text
read SPEC
 ↓
find invariants
 ↓
find tests
 ↓
modify compiler
 ↓
run conformance
 ↓
run Oracle differential
 ↓
run optimizer differential
 ↓
run ABI tests
```

Nếu fail:

```text
AI agent receives
structured diagnostic
```

thay vì tự đoán.

---

# XXVI.68. Compiler Bug Classification

Harness nên phân loại:

```text id="g8x2w1"
FRONTEND_BUG
TYPE_SYSTEM_BUG
TRAIT_BUG
OWNERSHIP_BUG
VERIFIER_BUG
MIR_BUG
OPTIMIZER_BUG
ABI_BUG
BACKEND_BUG
ENCODER_BUG
OBJECT_BUG
LINKER_BUG
RUNTIME_BUG
ORACLE_BUG
TEST_BUG
```

Điều này rất hữu ích cho project Axiom lớn.

---

# XXVI.69. Oracle Trace

CLI:

```text id="j0q8p4"
axiom interpret test.ax --trace
```

có thể:

```text
CALL main
ALLOC #1
MOVE x -> y
VIEW #1 [0..4]
STORE #1
DROP #1
RETURN 0
```

---

# XXVI.70. Ownership Trace

Có thể:

```text id="7y2w5s"
axiom interpret test.ax --trace=ownership
```

output conceptual:

```text
x = OWNED
v = READ(x)
x = OWNED
v = DEAD
x = DROPPED
```

Đây là debugger cực mạnh cho compiler developer.

---

# XXVI.71. Capability Trace

```text id="p8j4r6"
Capability #4
owner = x
region = x.field.a
access = WRITE
live = true
```

Nếu conflict:

```text id="h4m2c8"
Capability #5
region overlaps Capability #4
```

---

# XXVI.72. Scheduler Replay

Concurrency failure:

```text id="k7m3r9"
axiom test --replay 18273
```

Oracle chạy lại chính xác schedule.

Đây sẽ là một feature rất giá trị khi Axiom bắt đầu có lock-free structures.

---

# XXVI.73. Fuzz Failure Artifact

Mỗi failure phải lưu:

```text id="q6j1v5"
source.ax
seed
compiler version
target
profile
optimization
oracle trace
scheduler trace
MIR
native output
expected output
```

để regression test có thể tái hiện.

---

# XXVI.74. Conformance Levels

Có thể chia:

```text id="7g1z0m"
Level 0 — Lexer
Level 1 — Parser
Level 2 — Type
Level 3 — Semantic
Level 4 — MIR
Level 5 — Runtime
Level 6 — ABI
Level 7 — Target
Level 8 — Optimization
```

Compiler chưa cần backend vẫn có thể đạt semantic conformance.

---

# XXVI.75. Formal Definition

Ta có thể đóng:

> **Axiom-conforming implementation** là implementation mà mọi chương trình nằm trong semantic domain được định nghĩa phải có observable behavior tương đương Semantic Model, ngoại trừ các behavior được spec khai báo target-defined, implementation-defined hoặc explicitly unsafe/undefined.

---

# XXVI.76. Invariants Part XXVI

### Oracle

**AORACLE-20 — Oracle Is A Semantic Reference Implementation**

**AORACLE-21 — Oracle Is Not A Production Runtime**

**AORACLE-22 — Oracle Executes Target-Neutral Semantics**

**AORACLE-23 — Oracle Does Not Depend On Target Machine Representation**

**AORACLE-24 — Oracle Uses Deterministic Virtual State Where Practical**

**AORACLE-25 — Oracle Memory Uses Logical Allocation Identity**

**AORACLE-26 — Oracle Tracks Ownership-Relevant State**

**AORACLE-27 — Oracle Tracks Capability-Relevant State**

**AORACLE-28 — Oracle Tracks Resource Lifetime**

### Determinism

**AORACLE-29 — Oracle Execution Is Deterministic By Default**

**AORACLE-30 — Virtual Time Is Deterministic**

**AORACLE-31 — Virtual Randomness Is Seedable**

**AORACLE-32 — Virtual External Resources Are Injectable**

**AORACLE-33 — Concurrency Schedules Can Be Replayed**

### Concurrency

**AORACLE-34 — Oracle Models Defined Atomic Ordering Semantics**

**AORACLE-35 — Oracle Distinguishes Atomic And Ordinary Memory**

**AORACLE-36 — Oracle Does Not Treat All Atomics As Sequentially Consistent**

**AORACLE-37 — Oracle Models Synchronization According To Its Contract**

### Async

**AORACLE-38 — Future Suspension Is Explicitly Modelled**

**AORACLE-39 — Future Drop Does Not Imply External Cancellation**

**AORACLE-40 — Capabilities Cannot Survive Forbidden Suspension Boundaries**

### Error

**AORACLE-41 — Oracle Distinguishes Return, Panic, Trap, And Termination**

**AORACLE-42 — Oracle Models Configured Panic Strategy**

**AORACLE-43 — Oracle Does Not Invent Semantics For Undefined Unsafe Behavior**

### Differential Testing

**AORACLE-44 — Production Compiler Can Be Differentially Tested Against Oracle**

**AORACLE-45 — Optimization Levels Can Be Differentially Tested**

**AORACLE-46 — Multiple Targets Can Be Differentially Tested**

**AORACLE-47 — Fuzzed Programs Can Be Differentially Tested**

**AORACLE-48 — Metamorphic Transformations Can Be Differentially Tested**

### Conformance

**AORACLE-49 — Every Normative Rule Should Have Conformance Tests**

**AORACLE-50 — Negative Semantic Cases Are First-Class Tests**

**AORACLE-51 — Compiler Diagnostics Are Testable Outputs**

**AORACLE-52 — ABI Rules Have Independent Conformance Tests**

**AORACLE-53 — Object Format Rules Have Independent Conformance Tests**

### Reproducibility

**AORACLE-54 — Failing Tests Preserve Reproduction Inputs**

**AORACLE-55 — Concurrency Failures Preserve Replay Schedules**

**AORACLE-56 — Fuzz Failures Become Regression Tests**

### Architecture

**AORACLE-57 — Oracle Does Not Become A Mandatory Production Dependency**

**AORACLE-58 — Oracle And Production Compiler May Share The Specification But Should Avoid Shared Bug-Critical Algorithms**

**AORACLE-59 — Semantic Model Is More Fundamental Than Any Particular Compiler Implementation**

**AORACLE-60 — Conformance Is Defined Against Semantics, Not Against Compiler Internals**

---

# XXVI.77. Kiến trúc test hoàn chỉnh

Axiom cuối cùng sẽ có:

```text id="0o2g1v"
                    Axiom Specification
                            │
                            ▼
                    Semantic Model
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
             Oracle              Conformance
                 │                     │
                 └──────────┬──────────┘
                            ▼
                         Compiler
                            │
                ┌───────────┼────────────┐
                ▼           ▼            ▼
              -O0          -O2        -O3/Os
                │           │            │
                └───────────┼────────────┘
                            ▼
                     Native Executions
                            │
                            ▼
                       Differential
                         Testing
```

Và đối với concurrency:

```text
Program
  ↓
Oracle
  ↓
Schedule #1234
  ↓
Expected behavior
  ↓
Native
  ↓
Compare
```

---

# XXVI.78. Một điểm rất quan trọng cho Axiom

Ta vừa tạo ra một cấu trúc mà nhiều language project thiếu:

```text
Language Specification
        ↓
Executable Semantic Model
        ↓
Reference Oracle
        ↓
Compiler
        ↓
Backend
```

Điều này có nghĩa **Axiom không cần tin compiler chỉ vì compiler tự nói rằng nó đúng**.

Compiler phải chứng minh thông qua:

```text
SPEC
→ Oracle
→ Tests
→ Differential execution
```

Đặc biệt phù hợp với cách bạn đang xây Axiom bằng AI agents: agent có thể sửa hàng nghìn dòng compiler, nhưng harness vẫn có một “trọng tài” độc lập.

---

## Part XXVII tiếp theo

Tiếp tục sẽ là:

**Part XXVII — Diagnostics · Error Model · Compiler UX · Machine-Readable Errors · IDE/LSP · AI-Agent Interface**

Phần này sẽ khóa cách Axiom báo lỗi sao cho **con người dễ hiểu nhưng AI agent cũng có thể tự sửa code một cách đáng tin cậy**, bao gồm:

```text
AX_TYPE_...
AX_MOVE_...
AX_VIEW_...
AX_DROP_...
AX_TRAIT_...
AX_ASYNC_...
AX_CONC_...
AX_ABI_...
AX_RUNTIME_...
```

và quan trọng nhất là thiết kế **Diagnostic Object** có cấu trúc thay vì chỉ in text ra terminal.