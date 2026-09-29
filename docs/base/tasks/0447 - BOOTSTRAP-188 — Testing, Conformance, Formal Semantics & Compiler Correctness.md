# BOOTSTRAP-188 — Testing, Conformance, Formal Semantics & Compiler Correctness
## FROZEN / COMPLETED

Đây là một tầng **cực kỳ quan trọng** của Axiom. Với kiến trúc hiện tại, compiler có thể có hàng trăm optimization pass, nhiều backend, GPU, async, ownership/capability… nên chỉ unit test thông thường là không đủ.

Nguyên tắc trung tâm:

> **Compiler được phép tối ưu bất kỳ thứ gì, nhưng không được phép thay đổi observable semantics của chương trình Axiom.**

---

## 1. Semantic Oracle

Axiom cần một **Semantic Oracle** làm chuẩn tham chiếu.

```text
Axiom Source
     │
     ├── Reference Semantics
     │       ↓
     │   Expected behavior
     │
     └── Production Compiler
             ↓
        Native / WASM / GPU
             ↓
        Observed behavior
```

Oracle không cần nhanh. Nó cần **đúng và đơn giản**.

Nó định nghĩa:

- evaluation order
- value semantics
- Move/Copy/Clone
- Drop
- capability validity
- aliasing
- panic/Result
- concurrency semantics
- async suspension
- atomic ordering
- FFI boundary semantics
- numeric semantics
- layout khi `repr` được chỉ định

### Quyết định

**Reference semantics là authority cao hơn optimizer.**

Nếu optimizer tạo kết quả khác Oracle → compiler bug.

---

# 2. Reference Interpreter

Axiom sẽ có một interpreter tham chiếu:

```text
ax-ref
```

Nó thực thi semantic model trực tiếp, không tối ưu mạnh.

Ví dụ:

```axiom
fn sum(a: i32, b: i32) -> i32 {
    a + b
}

fn main() {
    print(sum(2, 3))
}
```

Reference interpreter phải cho kết quả:

```text
5
```

Nhưng quan trọng hơn, nó phải có khả năng kiểm tra những thứ như:

```text
Move
Drop
Capability
Result
Match
Async
Atomic
```

---

# 3. MIR Interpreter

Ngoài source interpreter, Axiom cần:

```text
ax-mir
```

để chạy **Verified MIR**.

Pipeline kiểm thử:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Verifier
  ↓
Verified MIR
  ↓
MIR Interpreter
```

Sau đó so sánh:

```text
Reference Semantics
        ≡
MIR Interpreter
```

Nếu khác:

> lỗi compiler frontend / MIR lowering / verifier.

Điều này cực kỳ hữu ích vì không cần đợi backend native.

---

# 4. Compiler Correctness Boundary

Ta chia compiler thành các boundary có thể kiểm chứng:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Verified MIR
  ↓
OptIR
  ↓
ABI MIR
  ↓
Axiom LIR
  ↓
Machine IR
  ↓
Machine Code
```

Mỗi bước phải có invariant.

Ví dụ:

```text
Typed HIR
   ↓
must preserve typing semantics

HIR
   ↓
MIR
must preserve evaluation semantics

Verified MIR
   ↓
OptIR
must preserve observable behavior

ABI MIR
   ↓
LIR
must preserve calling convention

Machine IR
   ↓
Machine Code
must preserve machine semantics
```

---

# 5. Translation Validation

Không nhất thiết phải chứng minh toàn bộ optimizer bằng formal proof.

Axiom dùng:

> **Translation Validation**

Mỗi lần compiler biến đổi chương trình:

```text
Before
   ↓
Optimization Pass
   ↓
After
```

compiler có thể kiểm tra:

```text
Does After preserve required semantics of Before?
```

Ví dụ:

```text
x * 2
```

được biến thành:

```text
x << 1
```

chỉ hợp lệ nếu semantic conditions phù hợp.

Không đủ điều kiện:

```text
optimization rejected
```

Không được:

```text
"compiler nghĩ rằng chắc đúng"
```

---

# 6. Optimization Proof Contracts

Mỗi optimization pass phải khai báo:

```text
Pass
├── Preconditions
├── Transformation
├── Preserved Invariants
├── New Facts
└── Validation Strategy
```

Ví dụ:

```text
BoundsCheckElimination

Preconditions:
    RangeInfo proves i < len

Transformation:
    remove bounds check

Preserves:
    memory safety
    observable behavior

Validation:
    MIR verifier
```

Điều này phù hợp trực tiếp với kiến trúc `Verified MIR → OptIR`.

---

# 7. Differential Compiler Testing

Axiom sẽ thường xuyên chạy:

```text
Source
 ├── Reference Interpreter
 ├── MIR Interpreter
 ├── Debug Compiler
 ├── Optimized Compiler
 └── Different Backend
```

và so sánh kết quả.

Ví dụ:

```text
              ┌── Interpreter ── 42
Program ──────┼── Debug ──────── 42
              ├── Release ────── 42
              ├── Size ───────── 42
              └── WASM ───────── 42
```

Nếu:

```text
42
42
17
42
```

→ optimization bug.

---

# 8. Metamorphic Testing

Đây là một cơ chế rất mạnh.

Không cần biết trước output chính xác.

Ta tạo chương trình:

```text
P
```

và một chương trình tương đương:

```text
P'
```

Sau đó yêu cầu:

```text
execute(P) == execute(P')
```

Ví dụ:

```axiom
x + 0
```

vs:

```axiom
x
```

hoặc:

```axiom
let a = f()
let b = g()
a + b
```

so với các transformation **chỉ khi evaluation-order semantics cho phép**.

Điểm cuối rất quan trọng:

> Metamorphic testing không được tự ý giả định hai chương trình tương đương.

Transformation phải được compiler/test framework đánh dấu là **semantic-preserving**.

---

# 9. Property-Based Testing

Axiom test generator sẽ sinh hàng triệu chương trình nhỏ:

```text
integers
floats
arrays
structs
enums
generics
traits
match
closures
move
copy
drop
views
mut_views
async
atomics
```

Ví dụ generator tạo:

```axiom
struct S {
    a: i32,
    b: i64
}
```

rồi tự động tạo:

- copy
- move
- partial move
- drop
- view
- mutation
- nested ownership

Mục tiêu là tìm các tổ hợp compiler developer không nghĩ tới.

---

# 10. Fuzzing

Các thành phần sau phải fuzz:

```text
Lexer
Parser
Resolver
Type checker
Trait solver
Const evaluator
Comptime
MIR lowering
Ownership verifier
Capability verifier
Pattern exhaustiveness
ABI lowering
Object writer
Linker
```

Đặc biệt:

### Parser fuzzing

Input bất kỳ:

```text
random bytes
random Unicode
deep nesting
huge identifiers
malformed syntax
```

Compiler phải:

```text
diagnostic
```

hoặc:

```text
successful compilation
```

nhưng **không crash/ICE** vì input hợp lệ về mặt process safety.

---

# 11. Compiler Fuzzing bằng chương trình hợp lệ

Không chỉ fuzz input lỗi.

Cần:

```text
Generate Valid Axiom Program
        ↓
Compile
        ↓
Execute
        ↓
Compare Oracle
```

Đây là nơi có thể bắt:

- optimizer bug
- register allocator bug
- ABI bug
- incorrect Drop
- incorrect alias analysis
- wrong vectorization
- wrong constant folding

---

# 12. Ownership Adversarial Suite

Đây phải là một test suite riêng.

Ví dụ các nhóm:

```text
double move
use after move
partial move
partial initialization
conditional move
conditional drop
nested drop
early return
panic during cleanup
loop ownership
closure capture
async capture
view escape
mut_view alias
relocation while view exists
returning view
FFI capability
unsafe → safe boundary
```

Mỗi case phải có expected result:

```text
ACCEPT
```

hoặc:

```text
REJECT + stable diagnostic code
```

---

# 13. Concurrency Litmus Tests

Memory model cần có test dạng:

```text
Thread A                 Thread B

store(x, 1, Release)     load(x, Acquire)
```

và kiểm tra những execution nào:

```text
allowed
forbidden
```

Các nhóm:

- Relaxed
- Acquire
- Release
- AcqRel
- SeqCst
- mutex
- channel
- thread start
- join
- task migration
- atomics
- shared memory

Mục tiêu là compiler không được vô tình biến:

```text
allowed
```

thành:

```text
forbidden
```

hoặc ngược lại.

---

# 14. Async State-Machine Testing

Một `async fn`:

```text
async fn foo() -> T
```

sẽ được test cả:

```text
source Future
      ↓
lowered state machine
      ↓
MIR
```

Test:

- suspension
- resume
- multiple await
- cancellation
- drop future
- values live across await
- Send
- non-Send
- guard across await
- recursion
- executor migration

Đặc biệt:

```text
Future before lowering
        ≡
Future after lowering
```

về observable behavior.

---

# 15. GPU Conformance

GPU compiler cũng không được trở thành "vùng riêng".

Test:

```text
Axiom GPU source
       ↓
GPU legality verifier
       ↓
GPU IR
       ↓
GPU machine code
```

kiểm tra:

- address space
- capability
- alias
- synchronization
- atomics
- barriers
- host/device ownership
- launch arguments
- event completion
- layout
- bounds
- race prevention

Có thể dùng CPU reference implementation làm oracle cho nhiều kernel thuần dữ liệu:

```text
CPU implementation
       ≡
GPU implementation
```

---

# 16. FFI ABI Conformance

Axiom phải test ABI với:

```text
C
C++
Rust
Swift
Objective-C
system ABI
```

khi cần.

Đặc biệt:

```text
struct layout
alignment
calling convention
integer widths
float passing
return values
variadic ABI
strings
pointers
callbacks
dynamic libraries
```

Không được chỉ test trên một CPU.

Matrix:

```text
x86-64
ARM64
WASM
Windows
Linux
macOS
Android
iOS
```

tùy target được hỗ trợ.

---

# 17. Numeric Conformance

Test đặc biệt cho:

```text
overflow
underflow
division
shift
casts
NaN
Infinity
signed zero
floating comparison
fast-math
SIMD
```

Ví dụ:

```text
strict FP
```

phải giữ semantics nghiêm ngặt.

Còn:

```text
fast-math
```

là profile/opt-in với semantics riêng đã được định nghĩa.

---

# 18. Deterministic Compiler

Compiler phải deterministic ở semantic level.

Cùng:

```text
source
compiler version
target
features
dependencies
comptime inputs
profile
```

phải cho cùng:

```text
semantic result
```

và trong reproducible mode:

```text
identical artifact
```

nếu môi trường build đáp ứng yêu cầu hermetic.

Parallel compiler không được làm thay đổi semantics.

---

# 19. Stable Diagnostic Conformance

Diagnostic không chỉ là text.

Mỗi lỗi có:

```text
DiagnosticCode
Severity
PrimarySpan
SecondarySpans
Explanation
MachineAction
RelatedDeclarations
```

Ví dụ:

```text
AOWN-204
use of moved value
```

Text có thể thay đổi.

**Diagnostic code và semantic category phải ổn định.**

Điều này đặc biệt quan trọng cho AI tooling.

---

# 20. Axiom Language Conformance Suite v0.1

Đây là bộ test chuẩn chính thức:

```text
tests/conformance/
```

cấu trúc:

```text
language/
types/
expressions/
control/
patterns/
generics/
traits/
ownership/
drop/
capability/
memory/
concurrency/
async/
comptime/
reflection/
gpu/
ffi/
abi/
numeric/
strings/
collections/
errors/
os/
packages/
```

Mỗi test có metadata:

```text
test_id
language_version
expected = pass | fail
diagnostic_code
targets
features
profile
```

---

# 21. Compiler Self-Check

Compiler production build có thể tự kiểm tra:

```text
axc self-test
```

gồm:

```text
frontend tests
semantic tests
MIR tests
verifier tests
optimizer tests
backend tests
ABI tests
linker tests
conformance tests
```

Ngoài ra:

```text
axc --verify-compiler
```

có thể chạy các invariant quan trọng.

---

# 22. Bootstrap Compiler Comparison

Khi Axiom có compiler mới:

```text
Compiler A
    ↓
compile Axiom compiler
    ↓
Compiler B
```

sau đó:

```text
Compiler A → compile test suite
Compiler B → compile test suite
```

và so sánh.

Khi self-hosting:

```text
Bootstrap compiler
       ↓
Stage 1 compiler
       ↓
Stage 2 compiler
       ↓
Stage 3 compiler
```

Kết quả semantic phải hội tụ.

---

# 23. Formal Semantics

Không cần formalize toàn bộ Axiom ngay từ đầu bằng theorem prover.

Nhưng Core phải có **small-step semantic model** cho các thành phần quan trọng:

```text
Expression evaluation
Value
Move
Copy
Drop
Capability
Memory access
Control flow
Result
Panic
Concurrency events
Atomic events
Async suspension
```

Ví dụ khái niệm:

```text
⟨Program, State⟩ → ⟨Program', State'⟩
```

và:

```text
Move(x)
```

làm thay đổi ownership state:

```text
Owned → Moved
```

chứ không phụ thuộc implementation cụ thể.

---

# 24. Observable Behavior

Compiler correctness không có nghĩa:

```text
machine code giống nhau
```

Mà là:

```text
observable behavior giống nhau
```

Observable events gồm:

```text
returned value
Result
panic
external IO
volatile access
atomic behavior
synchronization
FFI calls
program termination
specified timing-independent ordering
```

Compiler được tự do thay đổi:

```text
register allocation
stack layout
instruction order
temporary objects
allocation strategy
inlining
vectorization
```

miễn semantics không đổi.

---

# 25. Unsafe Testing

`unsafe` không được tạo thành vùng:

> "compiler không kiểm tra gì nữa."

Test phải đảm bảo:

```text
unsafe establishes contract
        ↓
safe verifier resumes
```

Có test cho:

```text
valid unsafe contract
invalid unsafe contract
invalid pointer provenance
misaligned access
invalid bitcast
invalid lifetime reconstruction
FFI contract mismatch
```

Compiler không nhất thiết chứng minh được mọi lỗi bên trong unsafe, nhưng **boundary semantics phải chính xác**.

---

# 26. Test Levels

Axiom sẽ có nhiều tầng:

```text
L0 — Unit
L1 — Semantic
L2 — MIR
L3 — Verification
L4 — Optimization
L5 — Backend
L6 — ABI
L7 — Integration
L8 — Differential
L9 — Fuzz
L10 — Conformance
L11 — Bootstrap
```

Một thay đổi compiler lớn không được chỉ chạy L0.

---

# 27. Golden Tests

Một số representation ổn định sẽ có:

```text
source.ax
expected.hir
expected.mir
expected.diagnostic
expected.asm
```

Nhưng cần phân biệt:

### Semantic golden

Ổn định mạnh:

```text
HIR semantics
MIR semantics
diagnostics
ABI contract
```

### Codegen golden

Ổn định yếu hơn:

```text
assembly
register allocation
instruction selection
```

Không nên khiến thay đổi optimization vô hại phá toàn bộ test suite.

---

# 28. Compiler Bug Classification

Compiler phải phân loại bug:

```text
FRONTEND
TYPE
TRAIT
OWNERSHIP
CAPABILITY
MIR
OPTIMIZER
ABI
BACKEND
LINKER
RUNTIME
CONCURRENCY
ASYNC
GPU
FFI
COMPTIME
DEBUG
BUILD
```

Mỗi bug regression trở thành một test.

Nguyên tắc:

> **Every miscompilation becomes a permanent regression test.**

---

# 29. Correctness Architecture cuối cùng

Kiến trúc testing của Axiom:

```text
                    ┌────────────────────┐
                    │ Semantic Oracle    │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             ↓                ↓                ↓
       Reference VM       MIR Interpreter   Test Generator
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                       Production Compiler
                              │
          ┌───────────────────┼───────────────────┐
          ↓                   ↓                   ↓
       Debug                Release              Size
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ↓
                       Native / WASM / GPU
                              ↓
                       Differential Test
```

Đây là nền tảng để Axiom có thể thực sự theo đuổi:

> **Aggressive optimization without sacrificing semantic reliability.**

---

# Invariants mới — FROZEN

### `ATEST-20`
Mọi compiler transformation phải bảo toàn observable semantics.

### `ATEST-21`
Reference semantics là semantic authority.

### `ATEST-22`
Verified MIR là correctness boundary trước optimization.

### `ATEST-23`
MIR interpreter phải phản ánh semantics của Verified MIR.

### `ATEST-24`
Optimization pass phải có explicit preconditions và preserved invariants.

### `ATEST-25`
Failed optimization proof → transformation không được áp dụng.

### `ATEST-26`
Optimization không được dựa trên assumption chưa được chứng minh.

### `ATEST-27`
UNKNOWN alias không được coi là NO_ALIAS.

### `ATEST-28`
Differential execution phải được hỗ trợ giữa reference, MIR và production compiler.

### `ATEST-29`
Metamorphic transformations phải được chứng minh là semantic-preserving trước khi dùng làm oracle.

### `ATEST-30`
Ownership/capability/concurrency semantics phải có adversarial conformance tests.

### `ATEST-31`
Compiler crash trên valid input là compiler defect.

### `ATEST-32`
Compiler phải deterministic về semantic result.

### `ATEST-33`
Diagnostic semantic identity phải có stable diagnostic code.

### `ATEST-34`
FFI ABI phải được kiểm thử theo target/ABI contract.

### `ATEST-35`
Async lowering phải bảo toàn observable semantics.

### `ATEST-36`
GPU lowering phải giữ nguyên các semantic safety/synchronization contracts.

### `ATEST-37`
Unsafe boundary không được làm mất verifier state.

### `ATEST-38`
Mỗi compiler miscompilation phải trở thành regression test.

### `ATEST-39`
Self-hosted compiler phải vượt qua cùng conformance suite với bootstrap compiler.

### `ATEST-40`
Formal semantics không phụ thuộc implementation strategy.

### `ATEST-41`
Code generation khác nhau được chấp nhận nếu observable semantics tương đương.

### `ATEST-42`
Reproducible build mode phải tạo artifact deterministic khi mọi build inputs được cố định.

---

# Trạng thái Axiom hiện tại

Sau **BOOTSTRAP-188**, chuỗi kiến trúc đã có đủ một vòng rất quan trọng:

```text
Language
   ↓
Type System
   ↓
Ownership / Memory
   ↓
Capability
   ↓
Concurrency / Async
   ↓
Comptime / Reflection
   ↓
IR
   ↓
Verification
   ↓
Optimization
   ↓
ABI
   ↓
Backend
   ↓
Runtime
   ↓
OS / Process / IPC
   ↓
Package / Build / Distribution
   ↓
Testing / Formal Semantics
   ↓
Compiler Correctness
```

**BOOTSTRAP-188 — FROZEN / COMPLETED.**

---

# BOOTSTRAP-189 — Developer Experience, IDE, Tooling & AI-Native Compiler Interface

Đây là bước tiếp theo hợp lý.

Không phải làm IDE trước, mà thiết kế **compiler interface** đủ mạnh để cả:

- IDE
- debugger
- language server
- formatter
- refactoring
- documentation generator
- profiler
- static analyzer
- AI coding agent

đều sử dụng **cùng CompilerDB và semantic model**, thay vì mỗi tool tự parse/analyze Axiom theo cách riêng.

Trọng tâm sẽ là:

```text
axc
├── check
├── build
├── run
├── test
├── fmt
├── doc
├── inspect
├── explain
├── query
├── ast
├── hir
├── mir
├── diagnostics
├── symbols
├── dependencies
└── ai
```

và đặc biệt thiết kế **AI-native compiler protocol** để agent có thể hỏi compiler những câu như:

```text
"Why does this fail?"
"Which capability conflicts?"
"Who owns this value?"
"Why can't this view escape?"
"Which trait implementation was selected?"
"Why wasn't this allocation eliminated?"
"Why wasn't this function inlined?"
"Which dependency caused this artifact?"
```

thay vì AI phải tự đoán từ text/error message.

**BOOTSTRAP-189** sẽ là tầng biến Axiom từ một language/compiler thành một **development platform có semantic API thống nhất**.