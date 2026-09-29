Tiếp tục với **BOOTSTRAP-063 — Testing, Conformance, Language Specification & Formal Semantic Validation**.

Đây là mốc rất quan trọng. Axiom hiện đã có rất nhiều semantics: ownership, capability, memory, concurrency, async, GPU, FFI, ABI, optimizer, linker… Nếu không xây **một hệ thống kiểm chứng độc lập với compiler implementation**, càng về sau càng dễ xảy ra tình trạng:

> Compiler hiện tại “định nghĩa” ngôn ngữ thay vì Specification định nghĩa ngôn ngữ.

Mục tiêu của 063 là ngược lại:

```text
                AXIOM SPECIFICATION
                       │
                       ▼
                Semantic Rules
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Tests         Oracle       Reference
          │            │          Semantics
          └────────────┼────────────┘
                       ▼
                    axiomc
                       │
                 implementation
```

---

# BOOTSTRAP-063 — Testing & Semantic Conformance

# 1. Nguyên tắc số 1

**Specification là nguồn sự thật.**

Không phải:

```text
axiomc behavior
```

mà là:

```text
Axiom Specification
        ↓
expected semantic behavior
        ↓
axiomc implementation
```

Nếu compiler khác specification:

```text
compiler = bug
```

trừ khi specification được chính thức sửa đổi.

---

# 2. Không dùng compiler để làm test oracle duy nhất

Sai:

```text
compile program
→ compiler chạy
→ output = expected
```

vì nếu compiler có bug:

```text
buggy compiler
      ↓
buggy result
      ↓
test passes
```

Đây là **self-confirming test**.

---

# 3. Có Reference Semantic Model

Cần một model đơn giản:

```text
Source
 ↓
Reference Interpreter
 ↓
Semantic Result
```

Reference interpreter không cần nhanh.

Mục tiêu của nó là:

> dễ kiểm chứng hơn compiler tối ưu.

---

# 4. Reference Interpreter

Ban đầu có thể viết bằng host language.

Sau này có thể viết lại bằng Axiom.

Nó thực hiện:

```text
AST/HIR
 ↓
semantic evaluation
```

không cần:

```text
machine code
register allocation
linker
```

---

# 5. Reference Interpreter không phải runtime của Axiom

Đây là tooling:

```text
axiom-ref
```

không được link vào application.

---

# 6. Test ba tầng

Mỗi semantics quan trọng nên có:

```text
Level 1
Syntax / type

Level 2
Semantic / MIR

Level 3
Native behavior
```

Ví dụ ownership:

```text
source
 ↓
compile-fail expectation
 ↓
MIR verification
 ↓
native executable
```

---

# 7. Compile-pass tests

Ví dụ:

```axiom
fn main() {
    let x = 42
    let y = x
    print(y)
}
```

Expected:

```text
PASS
```

---

# 8. Compile-fail tests

Ví dụ:

```axiom
fn main() {
    let x = SomeResource()
    let y = move x

    use(x)
}
```

Expected:

```text
FAIL
```

với stable diagnostic code.

---

# 9. Diagnostic code

Không test bằng text:

```text
"variable x was moved"
```

vì wording có thể thay đổi.

Test bằng:

```text
EOWN-MOVED
```

hoặc một stable diagnostic identifier.

---

# 10. Diagnostic structure

Diagnostic nên có:

```text
code
severity
primary_span
secondary_spans
message
notes
semantic_facts
fixits
```

Ví dụ:

```json
{
  "code": "EOWN-MOVED",
  "severity": "error",
  "primary_span": "...",
  "facts": {
    "place": "x",
    "state": "Moved"
  }
}
```

---

# 11. UI text không phải contract

Compiler có thể thay đổi:

```text
"x was already moved"
```

thành:

```text
"x cannot be used after move"
```

nhưng:

```text
EOWN-MOVED
```

không đổi nếu semantics không đổi.

---

# 12. Test organization

Đề xuất:

```text
tests/
├── lexer/
├── parser/
├── resolver/
├── types/
├── traits/
├── generics/
├── ownership/
├── capability/
├── drop/
├── concurrency/
├── async/
├── comptime/
├── gpu/
├── ffi/
├── abi/
├── mir/
├── optimization/
├── backend/
├── object/
├── linker/
├── runtime/
└── integration/
```

---

# 13. Ownership test suite

Phải test riêng:

```text
Move
Copy
Clone
Drop
partial move
return
early return
panic
loop
match
closure
async
thread
```

---

# 14. Capability test suite

Ví dụ:

```text
view duplication
mut_view exclusivity
owner destruction
relocation
field disjointness
range disjointness
unknown overlap
escape
returning view
```

---

# 15. Memory test suite

```text
stack promotion
heap elimination
Box
Arena
Pool
stable address
relocatable Vec
observable address
FFI address
```

Không chỉ test output.

Phải test semantic fact:

```text
allocation eliminated = allowed
```

nhưng:

```text
observable address changed = forbidden
```

---

# 16. Concurrency test suite

```text
Send
Share
Move across thread
Arc
Mutex
RwLock
Atomic
Channel
happens-before
Acquire
Release
SeqCst
volatile
```

---

# 17. Không test concurrency bằng timing

Sai:

```text
sleep(1ms)
expect race gone
```

Timing-dependent tests rất dễ flaky.

Thay vào đó cần:

```text
deterministic synchronization
```

và model-based tests.

---

# 18. Memory model litmus tests

Đây là một phần rất quan trọng.

Ví dụ conceptually:

```text
Thread A:
    data = 42
    flag.store(1, Release)

Thread B:
    if flag.load(Acquire) == 1:
        read(data)
```

Test phải xác định:

```text
42
```

có phải outcome được phép hay không theo memory model.

---

# 19. Forbidden outcome

Test memory model không chỉ:

```text
expected output
```

mà có thể định nghĩa:

```text
Allowed outcomes
Forbidden outcomes
```

---

# 20. Litmus suite

Có thể có:

```text
tests/memory/
    message_passing.ax
    store_buffering.ax
    load_buffering.ax
    iriw.ax
    atomicity.ax
```

---

# 21. Async tests

Phải test:

```text
await
suspension
future state
drop future
cancellation
spawn
spawn_local
Send across executor
sync guard across await
```

---

# 22. Deterministic executor

Test async nên có:

```text
TestExecutor
```

với scheduling deterministic.

Ví dụ:

```text
step()
run_until_ready()
advance()
```

không phụ thuộc wall-clock.

---

# 23. GPU tests

Không thể chỉ test GPU bằng actual hardware.

Cần:

```text
semantic GPU tests
GPU IR tests
backend tests
hardware integration tests
```

---

# 24. GPU semantic interpreter

Có thể có một execution model đơn giản:

```text
GPU kernel
 ↓
reference GPU execution
```

để test:

```text
ownership
capability
storage domain
barrier
atomic
```

---

# 25. ABI tests

ABI phải có golden tests.

Ví dụ:

```text
function signature
 ↓
ABI classification
 ↓
expected registers/stack
```

---

# 26. ABI golden files

Ví dụ:

```text
tests/abi/x86_64/
tests/abi/aarch64/
tests/abi/riscv64/
```

với expected:

```text
argument register
return register
stack offset
alignment
calling convention
```

---

# 27. Machine encoder tests

Đã có quyết định golden-byte.

Ví dụ:

```text
Axiom LIR
 ↓
Machine IR
 ↓
bytes
```

Expected byte sequence được freeze trong test.

---

# 28. Golden machine code không phải semantic ABI duy nhất

Nếu backend tối ưu:

```text
instruction A
```

thành:

```text
instruction B
```

thì golden byte có thể thay đổi.

Vì vậy phân biệt:

```text
semantic golden
ABI golden
encoder golden
```

---

# 29. Encoder golden

Dùng cho:

```text
specific instruction encoding
```

Ví dụ:

```text
x86 ADD
AArch64 ADD
RISC-V ADD
```

Không dùng golden byte cho toàn bộ executable trừ khi reproducibility test.

---

# 30. Object writer tests

Test:

```text
ELF
PE/COFF
Mach-O
WASM
```

riêng.

---

# 31. Relocation tests

Ví dụ:

```text
symbol A references symbol B
```

expected:

```text
relocation type
offset
addend
symbol
```

---

# 32. Linker tests

Test:

```text
symbol resolution
weak
COMDAT
dead stripping
section GC
TLS
imports
exports
PIE
shared libraries
```

---

# 33. Cross-target conformance

Một source program hợp lệ phải có semantics giống nhau nếu target có đủ capability.

Ví dụ:

```text
x86_64
AArch64
RISC-V
```

không được thay đổi language semantics chỉ vì backend khác.

---

# 34. Target-specific behavior

Nhưng những thứ vốn target-specific có thể khác:

```text
usize size
alignment
floating implementation details
atomic availability
SIMD
ABI
```

Specification phải đánh dấu:

```text
portable semantic
target-defined
implementation-defined
```

---

# 35. Ba loại behavior

Tôi đề xuất chính thức:

### Defined

Specification quy định chính xác.

### Implementation-defined

Compiler/target chọn một behavior trong tập cho phép và phải expose metadata.

### Unspecified

Có nhiều behavior hợp lệ và program không được phụ thuộc vào lựa chọn.

---

# 36. Undefined behavior

Axiom nên cực kỳ hạn chế UB trong safe code.

```text
Safe invalid operation
→ compile-time rejection
```

Unsafe:

```text
machine-level invalid behavior
```

có thể trở thành target-defined/undefined tùy operation.

---

# 37. Không biến mọi thứ thành UB

Ví dụ integer overflow:

Không:

```text
signed overflow → UB
```

mà đã freeze:

```text
checked
wrapping
saturating
```

semantics rõ ràng.

---

# 38. Floating point

Cần có profile:

```text
strict
default
fast
```

nhưng `fast` phải là **explicit semantic/optimization contract**, không được ngầm bật.

---

# 39. Differential testing

Một trong những vũ khí mạnh nhất:

```text
Program
 ├── Reference Interpreter
 └── axiomc native
        ↓
     compare
```

---

# 40. Differential testing không chỉ output

Có thể so:

```text
return value
stdout
stderr
exit status
panic behavior
observable file/network behavior
```

trong môi trường controlled.

---

# 41. MIR differential testing

Thậm chí:

```text
source
 ↓
HIR
 ↓
MIR
```

có thể so với reference lowering.

---

# 42. Optimization differential testing

Chạy:

```text
-O0
-O1
-O2
-O3
-LTO
-PGO
```

và yêu cầu observable semantics tương đương.

---

# 43. Translation validation

Đây là tầng mạnh hơn.

Mỗi optimization:

```text
before
 ↓
optimization
 ↓
after
```

có verifier kiểm tra:

```text
semantic equivalence / preservation
```

trong phạm vi có thể chứng minh.

---

# 44. Không cần theorem prover toàn ngôn ngữ

Axiom không cần xây một hệ thống:

```text
formal theorem prover
```

khổng lồ.

Thay vào đó:

```text
local verification
+
semantic invariants
+
reference interpreter
+
differential tests
+
translation validation
```

là đủ thực tế.

---

# 45. Optimization invariants

Mỗi pass có contract:

```text
Input invariants
Output invariants
Preserved semantics
Required facts
```

Ví dụ:

```text
VectorizeLoop:
requires:
    noalias(regionA, regionB)

preserves:
    ownership
    capability
    memory_order
    observable_behavior
```

---

# 46. Pass verification

Pipeline:

```text
Verified MIR
 ↓
OptIR
 ↓
Pass A
 ↓ verify
Pass B
 ↓ verify
Pass C
 ↓ verify
ABI MIR
```

Nếu invariant hỏng:

```text
compiler bug / ICE
```

không tiếp tục tạo binary.

---

# 47. Compiler ICE

Phải phân biệt:

```text
User error
```

và:

```text
Compiler invariant failure
```

Ví dụ:

```text
ICE-VERIFY-MIR-001
```

có structured diagnostic.

---

# 48. Fuzzing

Fuzzer nên fuzz:

```text
lexer
parser
resolver
type checker
trait solver
comptime
MIR
verifier
optimizer
ABI
machine encoder
object writer
linker
```

---

# 49. Grammar fuzzing

Random source:

```text
bytes
 ↓
lexer/parser
```

mục tiêu:

```text
no crash
no hang
no memory corruption
```

---

# 50. Semantic fuzzing

Generate valid Axiom programs:

```text
generator
 ↓
valid AST
 ↓
reference interpreter
 ↓
axiomc
 ↓
compare
```

Cực kỳ hữu ích.

---

# 51. Mutation testing

Lấy valid program rồi mutate:

```text
move
copy
drop
await
ownership
index
atomic ordering
```

và kiểm tra compiler có phát hiện violation tương ứng.

---

# 52. Exhaustive small-state testing

Đặc biệt hữu ích cho:

```text
ownership
capability
Drop
CFG
pattern matching
trait solver
```

Ví dụ generate mọi CFG nhỏ đến N nodes.

---

# 53. Model checking

Không cần cho toàn compiler.

Có thể dùng cho:

```text
channel
mutex state machine
future state machine
ownership dataflow
capability conflict
```

---

# 54. Compiler self-test

Compiler binary phải có:

```text
axiom test
```

và chạy:

```text
unit
integration
conformance
backend
linker
```

---

# 55. Conformance suite độc lập

Đề xuất repository:

```text
axiom-spec-tests/
```

không phụ thuộc implementation của `axiomc`.

Có thể chạy:

```text
axiom test-conformance
```

với bất kỳ compiler Axiom compliant nào.

---

# 56. Test format

Không nên để mỗi test là custom executable script.

Một format machine-readable:

```text
.toml
.json
```

hoặc metadata ngay trong source.

Ví dụ:

```axiom
//@test: compile-pass
//@target: x86_64-linux
```

---

# 57. Test metadata

Có thể:

```text
id="5nq8r2"
kind = "compile-fail"
diagnostic = "EOWN-MOVED"
target = ["x86_64", "aarch64"]
optimization = ["O0", "O2"]
```

---

# 58. Snapshot tests

Dùng snapshot cho:

```text
AST
HIR
MIR
Verified MIR
OptIR
ABI MIR
Machine IR
```

nhưng snapshot phải phân biệt:

```text
semantic fields
implementation fields
```

---

# 59. Không snapshot implementation noise

Ví dụ:

```text
temporary_id = 49271
```

không nên làm test fail nếu semantic graph giống nhau.

---

# 60. Canonical IR serialization

Compiler cần:

```text
canonical dump
```

Ví dụ:

```text
axiom build --emit=mir --canonical
```

để test deterministic.

---

# 61. Determinism test

Build cùng source:

```text
N lần
```

với:

```text
parallelism = 1
parallelism = 8
```

phải có semantic artifact giống nhau.

---

# 62. Reproducible binary

Trong reproducible mode:

```text
same source
same dependencies
same compiler
same target
same config
```

→ ideally:

```text
same binary bytes
```

nếu target/toolchain conditions cho phép.

---

# 63. Nếu binary bytes khác

Không nhất thiết là semantic bug.

Có thể do:

```text
timestamp
UUID
link ordering
debug paths
non-semantic metadata
```

Reproducible mode phải loại bỏ/chuẩn hóa các yếu tố đó.

---

# 64. Bootstrap test

Khi self-host:

```text
Stage 0
 ↓
Stage 1
 ↓
Stage 2
```

phải chạy conformance suite.

---

# 65. Stage comparison

Không yêu cầu:

```text
stage1 binary == stage2 binary
```

ngay lập tức.

Trước tiên:

```text
semantic outputs equivalent
```

sau đó mới hướng tới:

```text
reproducible bootstrap
```

---

# 66. Compiler bug minimization

Khi fuzzer tìm bug:

```text
large program
```

phải có reducer:

```text
1000 lines
 ↓
500
 ↓
100
 ↓
20
 ↓
minimal reproducer
```

---

# 67. `axiom reduce`

Có thể cung cấp:

```text
axiom reduce bug.ax
```

để tự động minimize compiler failure.

Đây sẽ cực kỳ hữu ích cho AI agent sửa compiler.

---

# 68. AI-compatible failure artifact

Khi compiler crash:

```text
bug/
├── source.ax
├── compiler.json
├── target.json
├── diagnostics.json
├── ast.json
├── hir.json
├── mir.json
└── stack.json
```

AI có thể phân tích mà không cần đọc log khổng lồ.

---

# 69. Semantic witness

Mỗi verifier failure nên cố gắng tạo:

```text
semantic witness
```

Ví dụ:

```text
capability C17
owner = v
region = v[0..8]
access = WRITE

capability C21
region = v[4..12]
access = WRITE

relation = OVERLAPS
```

AI/debugger hiểu ngay lý do reject.

---

# 70. Explain mode

Các hệ thống trước đã có:

```text
axiom explain
```

063 bổ sung semantic explanations:

```text
axiom explain ownership
axiom explain capability
axiom explain optimization
axiom explain abi
axiom explain error
```

---

# 71. Example

```text
axiom explain ownership main.ax:12
```

có thể trả:

```text
x:
  created       line 3
  moved         line 8
  used          line 12

state at line 12:
  Moved

diagnostic:
  EOWN-MOVED
```

---

# 72. Specification machine-readable

Đây là một bước rất đáng làm.

Không chỉ Markdown:

```text
spec/
├── prose/
├── rules/
├── invariants/
└── schema/
```

Mỗi semantic rule có ID.

---

# 73. Rule ID

Ví dụ:

```text
AVERIFY-46
```

có thể được liên kết:

```text
spec rule
 ↕
compiler implementation
 ↕
test cases
```

---

# 74. Traceability

Ví dụ:

```text
AOWN-20
```

được trace tới:

```text
spec/memory/ownership.axspec
compiler/verify/ownership
tests/ownership/move/
```

---

# 75. Đây là lợi thế cực lớn khi AI xây compiler

Agent nhận task:

```text
Fix EOWN-MOVED
```

có thể query:

```text
rule
implementation
failing tests
related invariants
```

thay vì tự mò toàn repository.

---

# 76. Semantic change process

Không được tùy tiện sửa compiler rồi update test để test pass.

Quy trình:

```text
Issue
 ↓
Spec analysis
 ↓
Decision
 ↓
Semantic rule change
 ↓
Test update
 ↓
Compiler implementation
 ↓
Conformance
```

---

# 77. Compiler change process

Nếu chỉ thay implementation:

```text
optimization
data structure
IR representation
backend
```

mà semantics không đổi:

```text
Spec unchanged
```

nhưng test phải vẫn pass.

---

# 78. Language versioning

Semantic change cần:

```text
Axiom language version
```

Ví dụ:

```text
Axiom 0.1
Axiom 0.2
Axiom 1.0
```

---

# 79. Compiler version ≠ language version

Ví dụ:

```text
axiomc 0.8.31
```

không có nghĩa language semantics thay đổi.

Có thể chỉ là:

```text
backend optimization improvement
```

---

# 80. Compatibility modes

Khi Axiom 1.0 stable:

```text
--language=1
```

để compile theo semantic version.

---

# 81. Edition-like mechanism

Có thể sau này có:

```text
edition = "2028"
```

nhưng không cần đưa vào Core v1 ngay.

Điểm quan trọng là:

> language evolution phải explicit.

---

# 82. Specification categories

Mỗi rule nên đánh dấu:

```text
CORE
LIBRARY
TARGET
ABI
IMPLEMENTATION
TOOLING
```

tránh nhập nhằng.

---

# 83. Example

`Vec` layout:

```text
LIBRARY
```

`view<T>` capability:

```text
CORE
```

ELF relocation:

```text
TARGET/OBJECT
```

`@repr(C)`:

```text
CORE + ABI
```

---

# 84. Conformance levels

Không phải compiler nào cũng phải hỗ trợ GPU ngay.

Có thể:

```text
Axiom Core
Axiom Hosted
Axiom Native
Axiom GPU
Axiom Full
```

nhưng mỗi level có explicit feature set.

---

# 85. Core conformance

Compiler tối thiểu phải pass:

```text
parser
type
ownership
capability
Drop
control flow
generics
traits
comptime core
```

---

# 86. Native conformance

Thêm:

```text
ABI
object
linker
native targets
```

---

# 87. GPU conformance

Thêm:

```text
kernel
device storage
GPU synchronization
GPU backend
```

---

# 88. Standard Library conformance

Không nên đồng nghĩa:

```text
compiler conformance
```

Một compiler có thể compliant language nhưng chưa implement toàn bộ std.

---

# 89. Library conformance

Standard library API cũng cần:

```text
API tests
behavior tests
ABI tests nếu có
platform tests
```

---

# 90. Platform-specific test matrix

Ví dụ:

```text
                 Linux Windows macOS Android WASM
Core               ✓      ✓      ✓      ✓      ✓
FS                 ✓      ✓      ✓      ✓      -
Sockets            ✓      ✓      ✓      ✓      -
Threads            ✓      ✓      ✓      ✓      -
GPU                ✓      ✓      ✓      ✓      -
```

Nhưng bảng này là implementation support matrix, không phải thay đổi Core semantics.

---

# 91. No flaky tests

Test suite phải ưu tiên:

```text
deterministic
isolated
repeatable
```

Không phụ thuộc:

```text
network
wall clock
random scheduler
machine load
```

trừ integration tests explicitly marked.

---

# 92. Test tiers

```text
Tier 0
unit

Tier 1
semantic

Tier 2
compiler integration

Tier 3
native backend

Tier 4
OS/platform

Tier 5
stress/fuzz
```

---

# 93. CI

CI tối thiểu:

```text
format
lint
unit
semantic
conformance
compile-fail
MIR
optimizer
ABI
backend
linker
integration
```

---

# 94. Nightly

Nightly có thể chạy:

```text
fuzz
stress
cross-target
differential
bootstrap
large corpus
```

---

# 95. Release gate

Không release compiler nếu:

```text
semantic regression
ABI regression
miscompilation
safety verifier regression
```

đặc biệt:

> **Miscompilation nghiêm trọng hơn compiler rejection.**

Compiler từ chối valid program là correctness bug; compiler chấp nhận và tạo chương trình sai là semantic/codegen bug nghiêm trọng hơn.

---

# 96. Security testing

Đặc biệt test:

```text
unsafe
FFI
pointer provenance
bounds
alignment
integer overflow
atomic
concurrency
object layout
```

---

# 97. Sanitizer/tooling

Có thể có:

```text
axiom-sanitize
```

nhưng sanitizer **không định nghĩa language semantics**.

Nó chỉ phát hiện violation/runtime bug.

---

# 98. Debug vs release test

Mọi semantic test quan trọng nên chạy:

```text
-O0
-O1
-O2
-O3
```

và nếu có:

```text
LTO
PGO
```

---

# 99. Final semantic pipeline

Đến đây hệ thống kiểm chứng hoàn chỉnh:

```text
                   Axiom Specification
                           │
                           ▼
                    Semantic Rules
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        Ref Interpreter   Tests       Invariants
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                        axiomc
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
      Verify            Optimize            Codegen
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                       Native Run
                           │
                           ▼
                     Differential Test
```

---

# 100. Frozen invariants — BOOTSTRAP-063

```text
ATEST-20   The language specification is the semantic source of truth.
ATEST-21   Compiler implementation is not the language specification.
ATEST-22   Conformance tests are independent of compiler implementation details where practical.
ATEST-23   A reference semantic model may serve as an independent test oracle.
ATEST-24   Reference execution is a tooling facility, not a mandatory application runtime.
ATEST-25   Compile-pass tests verify accepted programs.
ATEST-26   Compile-fail tests verify rejected programs.
ATEST-27   Compile-fail tests identify stable diagnostic codes.
ATEST-28   Diagnostic wording is not a semantic contract.
ATEST-29   Diagnostic semantic facts are machine-readable.
ATEST-30   Ownership semantics have dedicated conformance coverage.
ATEST-31   Capability semantics have dedicated conformance coverage.
ATEST-32   Drop semantics have dedicated conformance coverage.
ATEST-33   Memory semantics have dedicated conformance coverage.
ATEST-34   Concurrency semantics have dedicated conformance coverage.
ATEST-35   Async semantics have dedicated conformance coverage.
ATEST-36   Comptime semantics have dedicated conformance coverage.
ATEST-37   GPU semantics have dedicated conformance coverage.
ATEST-38   FFI semantics have dedicated conformance coverage.
ATEST-39   ABI semantics have dedicated conformance coverage.
ATEST-40   Object and linker semantics have dedicated implementation tests.
ATEST-41   Memory-model tests distinguish allowed and forbidden outcomes.
ATEST-42   Concurrency tests must not rely solely on timing.
ATEST-43   Deterministic executors may be used for async testing.
ATEST-44   GPU semantics can be tested independently of physical GPU hardware.
ATEST-45   ABI classification has target-specific golden tests.
ATEST-46   Machine instruction encoders have target-specific golden-byte tests.
ATEST-47   Object writers have target-specific format tests.
ATEST-48   Relocation behavior has explicit tests.
ATEST-49   Linker symbol resolution has explicit tests.
ATEST-50   Optimization tests verify semantic preservation.
ATEST-51   Optimization passes declare required semantic facts.
ATEST-52   Optimization passes cannot manufacture safety facts.
ATEST-53   Verification invariants are checked between critical compiler stages.
ATEST-54   Compiler invariant failures are distinct from user diagnostics.
ATEST-55   Fuzzing may target every compiler stage.
ATEST-56   Semantic fuzzing may compare reference and native execution.
ATEST-57   Mutation testing targets safety and semantic boundaries.
ATEST-58   Small-state exhaustive testing is encouraged for semantic analyzers.
ATEST-59   Model checking may be used for finite compiler/runtime state machines.
ATEST-60   Full theorem proving is not required for Core conformance.
ATEST-61   Differential testing compares independent semantic paths where possible.
ATEST-62   Optimization-level changes must preserve observable semantics.
ATEST-63   Debug and release must preserve language semantics.
ATEST-64   LTO must preserve language semantics.
ATEST-65   PGO must preserve language semantics.
ATEST-66   Snapshot tests distinguish semantic data from implementation noise.
ATEST-67   Canonical IR serialization supports deterministic testing.
ATEST-68   Parallel compilation must have semantically equivalent results to serial compilation.
ATEST-69   Reproducible mode removes uncontrolled semantic inputs.
ATEST-70   Bootstrap stages must pass the conformance suite.
ATEST-71   Bootstrap stages need not initially produce identical machine bytes.
ATEST-72   Bootstrap equivalence is first established semantically.
ATEST-73   Compiler bug reports should support minimized reproducers.
ATEST-74   Compiler failures may emit structured diagnostic artifacts.
ATEST-75   Verifier failures should expose semantic witnesses where practical.
ATEST-76   Explain commands may expose compiler semantic reasoning.
ATEST-77   Specification rules have stable identifiers.
ATEST-78   Specification rules may trace to implementation and tests.
ATEST-79   Semantic changes require specification review before compiler changes.
ATEST-80   Implementation-only changes need not alter language specification.
ATEST-81   Language version is distinct from compiler implementation version.
ATEST-82   Semantic language changes are explicitly versioned.
ATEST-83   Core, library, target, ABI and implementation rules are distinguished.
ATEST-84   Implementation-defined behavior is explicitly identified.
ATEST-85   Unspecified behavior is explicitly identified.
ATEST-86   Safe Core minimizes undefined behavior.
ATEST-87   Integer arithmetic semantics remain defined according to their explicit operation.
ATEST-88   Unsafe behavior may expose target-level machine semantics.
ATEST-89   Standard Library conformance is distinct from language conformance.
ATEST-90   Platform support matrices are distinct from language semantics.
ATEST-91   Tests should be deterministic unless explicitly classified otherwise.
ATEST-92   Network and wall-clock dependencies are excluded from deterministic semantic tests.
ATEST-93   Randomized testing records seeds and relevant configuration.
ATEST-94   Release gates reject semantic regressions.
ATEST-95   Miscompilation is treated as a correctness failure.
ATEST-96   Compiler rejection of valid code is distinct from miscompilation.
ATEST-97   Sanitizers and debugging tools do not redefine language semantics.
ATEST-98   Test infrastructure is not part of the application runtime.
ATEST-99   Conformance artifacts are machine-readable where practical.
ATEST-100  Axiom compiler evolution must remain constrained by specification and conformance.
```

---

# Một kiến trúc quan trọng vừa hình thành

Sau 063, Axiom không còn chỉ là:

```text
Language → Compiler → Binary
```

mà trở thành:

```text
                     ┌──────────────────────┐
                     │ Axiom Specification  │
                     └──────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │ Semantic Model        │
                    └───────────┬───────────┘
                                │
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
       Reference Model       Conformance        Invariants
             │                  │                  │
             └──────────────────┼──────────────────┘
                                ▼
                         ┌─────────────┐
                         │   axiomc    │
                         └──────┬──────┘
                                ▼
                       Verified MIR
                                ▼
                            OptIR
                                ▼
                           ABI / LIR
                                ▼
                         Machine / Object
                                ▼
                            Linker
                                ▼
                           Executable
```

Điều này đặc biệt quan trọng với mục tiêu **self-hosting**: sau này `axiomc` được viết bằng chính Axiom, nhưng **axiomc không được trở thành nơi duy nhất chứa “sự thật” về Axiom**.

### Mốc tiếp theo: **BOOTSTRAP-064 — Language Syntax & Surface Grammar Freeze**

Đến đây phần semantic backend đã tương đối đầy đủ. Bước hợp lý tiếp theo là quay lên phía trên và chốt **ngôn ngữ mà lập trình viên thực sự viết**: lexical rules, identifiers, keywords, literals, declaration syntax, `struct`, `enum`, `trait`, `impl`, functions/methods, generics, `view/mut_view`, ownership syntax, `async`, `comptime`, attributes, operators, pattern syntax, module/import syntax và grammar EBNF.

Đặc biệt 064 sẽ giải quyết một vấn đề quan trọng: **Axiom đã có semantics khá mạnh nhưng vẫn cần một surface syntax đủ đơn giản để AI và con người đọc/viết nhanh, không biến thành Rust 2.0.**