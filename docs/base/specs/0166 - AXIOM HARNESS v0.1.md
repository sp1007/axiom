Tiếp theo là **Axiom Benchmark + Conformance Harness v0.1**. Đây là bước chuyển từ “thiết kế compiler” sang **đo lường và chứng minh compiler hoạt động đúng**.

Điểm tôi muốn chốt ngay: **benchmark không được dùng để định nghĩa semantics**. Semantics đã đóng băng; benchmark chỉ đo hiệu năng, kích thước và regression.

# AXIOM HARNESS v0.1

## 1. Ba hệ thống phải tách biệt

```text id="harness01"
                 ┌── Oracle
                 │
Axiom Source ────┼── Native Compiler
                 │
                 └── Reference/Foreign Compiler
```

Ba mục tiêu:

### Conformance

```text
Axiom source
→ Oracle
→ expected semantics
```

### Compiler correctness

```text
Axiom source
→ Oracle
→ Native executable
→ compare
```

### Performance

```text
Axiom
C
C++
Rust
...
→ same workload
→ measure
```

Không trộn ba loại test này.

---

# 2. Repository

Tạo:

```text id="harness02"
tests/
├── conformance/
│   ├── lexical/
│   ├── parser/
│   ├── resolver/
│   ├── types/
│   ├── ownership/
│   ├── capability/
│   ├── drop/
│   ├── traits/
│   ├── async/
│   ├── concurrency/
│   ├── atomics/
│   ├── ffi/
│   ├── unsafe/
│   └── modules/
│
├── oracle/
│
├── compiler/
│
├── backend/
│
├── linker/
│
├── negative/
│
├── optimization/
│
├── abi/
│
└── benchmarks/
    ├── micro/
    ├── memory/
    ├── compute/
    ├── allocation/
    ├── io/
    ├── concurrency/
    └── realworld/
```

Và:

```text id="harness03"
tools/harness/
├── runner
├── manifest
├── oracle
├── compiler
├── executor
├── comparator
├── benchmark
├── profiler
└── report
```

---

# 3. Test không chỉ là source file

Mỗi test nên có metadata.

Ví dụ:

```text id="harness04"
test:
    name: ownership/use_after_move
    category: negative
    source: use_after_move.ax
    expect:
        diagnostic: AX_OWN_0001
```

Positive:

```text id="harness05"
test:
    name: arithmetic/basic
    category: conformance

    run:
        exit_code: 42
```

Optimization:

```text id="harness06"
test:
    name: allocation/elimination
    category: optimization

    required:
        - no_dynamic_allocation
```

---

# 4. Không hard-code expected machine code

Đừng làm:

```text id="harness07"
expect:
    x86:
        bytes: ...
```

cho mọi test.

Machine code thay đổi theo optimizer là bình thường.

Thay vào đó:

```text id="harness08"
semantic result
```

và một số **optimization invariant** riêng.

Ví dụ:

```text
allocation_count == 0
```

hoặc:

```text
bounds_check_count == 0
```

---

# 5. Test lifecycle

Mỗi test:

```text id="harness09"
Source
 ↓
Lex
 ↓
Parse
 ↓
Resolve
 ↓
Type
 ↓
Ownership
 ↓
MIR
 ↓
Verify
 ↓
Oracle
 ↓
Optimize
 ↓
LIR
 ↓
Backend
 ↓
Object
 ↓
Link
 ↓
Run
```

Không phải test nào cũng cần toàn pipeline.

Ví dụ parser test chỉ:

```text id="harness10"
Source
 ↓
Lexer
 ↓
Parser
 ↓
AST
```

---

# 6. Golden tests

Đây sẽ là loại test chính cho compiler.

Ví dụ:

```text id="harness11"
tests/parser/arithmetic.ax
tests/parser/arithmetic.expect
```

`expect` có thể chứa canonical AST:

```text id="harness12"
Binary(Add)
  Literal(1)
  Binary(Mul)
    Literal(2)
    Literal(3)
```

Nhưng không nên phụ thuộc ID nội bộ.

---

# 7. Canonical serialization

AST/HIR/MIR cần serializer deterministic.

Ví dụ:

```text id="harness13"
axiom dump-mir test.ax
```

luôn cho:

```text id="harness14"
fn main() -> i32
bb0:
    %0 = const.i32 40
    %1 = const.i32 2
    %2 = add.checked %0, %1
    return %2
```

Không đưa:

```text
InstrId=827364
```

vào golden output.

---

# 8. Diagnostic tests

Ví dụ:

```axiom id="harness15"
fn main() {
    let x = String(...)
    consume(x)
    print(x)
}
```

Expected:

```text id="harness16"
AX_OWN_0001
```

Harness phải kiểm tra:

- error code
- primary span
- severity
- số lượng diagnostic
- secondary spans nếu có
- message template nếu cần

Không nên bắt buộc exact wording trong mọi test vì wording có thể cải thiện.

---

# 9. Diagnostic schema

Đề nghị:

```text id="harness17"
{
    "code": "AX_OWN_0001",
    "severity": "error",
    "primary_span": {
        "file": "main.ax",
        "start": 42,
        "end": 43
    },
    "related": [],
    "notes": []
}
```

AI agent có thể đọc trực tiếp.

---

# 10. Negative test là first-class

Không chỉ test chương trình hợp lệ.

Axiom cần hàng nghìn test:

```text id="harness18"
use-after-move
double-move
use-before-init
dangling-view
mutable-view-conflict
view-cross-await
view-after-reallocation
not-Send
not-Share
invalid-cast
invalid-layout
trait-ambiguity
duplicate-symbol
...
```

Một compiler systems-language mạnh phải chứng minh rằng **code sai bị từ chối đúng cách**.

---

# 11. Oracle là trọng tài semantic

Ví dụ:

```axiom id="harness19"
fn main() -> i32 {
    let x = 20
    x + 22
}
```

Oracle:

```text id="harness20"
exit = 42
stdout = ""
stderr = ""
panic = false
```

Native:

```text id="harness21"
exit = 42
stdout = ""
stderr = ""
panic = false
```

→ PASS.

---

# 12. So sánh tất cả optimization levels

Một test executable mặc định chạy:

```text id="harness22"
-O0
-O1
-O2
-O3
-Os
-Oz
```

và:

```text id="harness23"
Oracle == O0
Oracle == O1
Oracle == O2
Oracle == O3
Oracle == Os
Oracle == Oz
```

Điều này cực kỳ quan trọng.

Một optimizer bug thường chỉ xuất hiện:

```text
-O2
```

hoặc:

```text
-O3
```

---

# 13. Random differential testing

Sau khi pipeline ổn định:

```text id="harness24"
Random Source
     ↓
Oracle
     ↓
Native -O0
     ↓
Native -O3
```

Nếu:

```text id="harness25"
Oracle != Native
```

→ compiler bug.

Nếu:

```text id="harness26"
-O0 != -O3
```

→ optimizer bug.

---

# 14. Fuzzing theo grammar

Không random byte thuần túy.

Dùng:

```text id="harness27"
Grammar-aware generator
```

sinh:

```text id="harness28"
expressions
types
structs
enums
match
generics
ownership
views
loops
closures
```

Ví dụ:

```text id="harness29"
depth <= 8
expression_count <= 100
```

để compiler không bị test generator tạo chương trình vô hạn.

---

# 15. MIR fuzzing

Đây còn mạnh hơn source fuzzing.

```text id="harness30"
Random valid MIR
 ↓
Verifier
 ↓
Optimizer
 ↓
Verifier
 ↓
Oracle
```

Mục tiêu:

> Optimizer không bao giờ tạo MIR invalid.

---

# 16. Backend fuzzing

```text id="harness31"
Random valid LIR
 ↓
x86 lowering
 ↓
Machine IR verifier
 ↓
encoder
```

Sau đó:

```text id="harness32"
decode / execute
```

Các lỗi cần bắt:

```text
invalid register
invalid operand
bad ModRM
bad SIB
bad displacement
bad relocation
wrong calling convention
```

---

# 17. Encoder byte tests

Đây là nơi test exact bytes hợp lý.

Ví dụ:

```text id="harness33"
LIR:
    ADD rax, 1
```

Expected machine encoding:

```text id="harness34"
[...]
```

Test này dành riêng cho encoder.

Không dùng exact bytes cho whole compiler.

---

# 18. Linker tests

Input:

```text id="harness35"
a.o
b.o
```

Expected:

```text id="harness36"
symbols
sections
relocations
entry
```

Sau đó executable test:

```text id="harness37"
run
expect exit=42
```

---

# 19. ABI tests

Đây là nhóm rất quan trọng.

Test:

```text id="harness38"
i32
i64
f32
f64
pointer
small struct
large struct
mixed integer/float
many arguments
return struct
```

Ví dụ:

```axiom id="harness39"
extern "C" fn c_function(
    a: i32,
    b: f64
) -> i32
```

So sánh Axiom với C ABI reference.

---

# 20. C interoperability test

Mục tiêu:

```text id="harness40"
Axiom → C
C → Axiom
```

Ví dụ:

```text id="harness41"
Axiom:
    add(10, 32)
```

C wrapper:

```text id="harness42"
return add(10, 32);
```

Expected:

```text id="harness43"
42
```

Đây sẽ chứng minh native ABI thật sự hoạt động.

---

# 21. Benchmark methodology

Benchmark không được chỉ:

```text
time ./program
```

vì noise lớn.

Mỗi benchmark:

```text id="harness44"
warmup
N iterations
median
p95
min
max
```

và ghi:

```text id="harness45"
CPU
OS
architecture
compiler version
commit
optimization
features
```

---

# 22. Benchmark categories

### Compute

```text id="harness46"
integer arithmetic
floating point
matrix
hash
sorting
parsing
```

### Memory

```text id="harness47"
copy
scan
allocation
deallocation
cache locality
```

### Control flow

```text id="harness48"
branch
loop
switch/match
function call
indirect call
```

### Abstraction

Đây là nhóm **đặc biệt quan trọng với Axiom**:

```text id="harness49"
struct method
generic function
trait static dispatch
closure
iterator
view
Option
Result
```

Mục tiêu:

> Đo xem abstraction có thực sự bị erase hay không.

---

# 23. Ví dụ abstraction benchmark

So sánh:

```text id="harness50"
raw loop
```

với:

```text id="harness51"
iterator abstraction
```

và:

```text id="harness52"
generic abstraction
```

Nếu cả ba tạo machine code tương đương về performance trong workload phù hợp, ta có bằng chứng cho:

> **Zero-cost abstraction.**

---

# 24. Allocation benchmark

Ví dụ:

```text id="harness53"
create 1,000,000 small objects
```

đo:

```text id="harness54"
allocations
frees
peak memory
time
```

Sau đó:

```text id="harness55"
-O0
-O2
```

có thể thấy allocation elimination hoạt động đến đâu.

---

# 25. Binary-size benchmark

Đo:

```text id="harness56"
.text
.rodata
.data
.bss
total file
loadable memory
```

Không chỉ:

```text
ls -l
```

vì file size không phản ánh chính xác memory footprint.

---

# 26. Startup benchmark

Vì Axiom có optional runtime, phải đo:

```text id="harness57"
_start
→ main
```

cho:

```text id="harness58"
freestanding
hosted-minimal
hosted-full
```

Mục tiêu:

```text
freestanding
≈ minimal OS interaction
```

không bị kéo theo runtime khổng lồ.

---

# 27. Dependency-size test

Một chương trình:

```axiom id="harness59"
fn main() -> i32 {
    42
}
```

phải không tự động link:

```text id="harness60"
async runtime
thread runtime
GC
reflection
network
unicode database
```

nếu không sử dụng.

Đây là regression test cực tốt cho kiến trúc runtime modular.

---

# 28. Reproducible build

Hai lần:

```text id="harness61"
axiom build
```

phải tạo:

```text id="harness62"
SHA256(binary_A)
==
SHA256(binary_B)
```

nếu environment inputs giống nhau.

Nếu timestamp embedded:

```text id="harness63"
SOURCE_DATE_EPOCH
```

được dùng để deterministic.

---

# 29. Compiler determinism

Không chỉ executable.

Kiểm tra:

```text id="harness64"
AST
HIR
MIR
LIR
object
binary
diagnostics
```

đều deterministic.

Đặc biệt:

```text id="harness65"
parallel compilation
```

phải cho cùng kết quả với:

```text id="harness66"
single-thread compilation
```

---

# 30. Performance regression gate

Không nên đặt:

> Axiom phải nhanh hơn C.

Điều này không thực tế và không phải semantics.

Thay vào đó benchmark lưu baseline:

```text id="harness67"
benchmark
baseline
current
delta
```

Ví dụ:

```text id="harness68"
array_sum
baseline: 10.2 ms
current: 10.4 ms
delta: +1.96%
```

CI có thể cảnh báo nếu vượt threshold.

---

# 31. Compiler performance cũng phải benchmark

Đừng chỉ benchmark executable.

Đo:

```text id="harness69"
lexing time
parsing time
resolution time
type checking
trait solving
ownership analysis
MIR construction
optimization
codegen
link
total compile time
```

Đặc biệt:

```text id="harness70"
trait solver
ownership analysis
```

vì đây là hai nơi dễ trở thành compile-time bottleneck.

---

# 32. Compile-time complexity guard

Trait solver phải có:

```text id="harness71"
max depth
max candidates
max normalization steps
max total steps
```

Ownership analysis:

```text id="harness72"
CFG iterations
region constraints
capability count
```

Nếu một chương trình khiến compiler mất quá lâu:

```text id="harness73"
AXC_LIMIT_...
```

thay vì treo.

---

# 33. AI-friendly test report

Đây là nơi Axiom có thể khác biệt.

`axiom test --json`:

```text id="harness74"
{
  "test": "ownership/use_after_move",
  "status": "fail",
  "phase": "ownership",
  "diagnostics": [
    {
      "code": "AX_OWN_0001",
      "span": {...}
    }
  ]
}
```

AI agent có thể đọc trực tiếp.

Không cần parse:

```text id="harness75"
human prose
```

---

# 34. Failure artifact

Khi test fail, tự động giữ:

```text id="harness76"
source.ax
ast.json
hir.json
typed-hir.json
mir.txt
verified-mir.txt
optimized-mir.txt
lir.txt
machine.txt
object.o
link-map.txt
stdout
stderr
trace.json
```

Đây sẽ là **dream setup cho Claude/Gemini/Codex agent debug compiler**.

Agent có thể tự tìm:

```text
phase = optimizer
```

thay vì chạy lại toàn bộ từ đầu.

---

# 35. Link map

Axiom linker nên hỗ trợ:

```text id="harness77"
--map
```

output:

```text id="harness78"
.text
    _start      0x401000   32
    main        0x401020   12
    foo         0x40102c   24

.rodata
    string_0    0x402000   16
```

Rất hữu ích cho binary-size optimization.

---

# 36. `axiom test`

CLI:

```text id="harness79"
axiom test
```

Các mode:

```text
axiom test --unit
axiom test --conformance
axiom test --negative
axiom test --oracle
axiom test --backend
axiom test --linker
axiom test --optimization
axiom test --fuzz
axiom test --benchmark
```

---

# 37. `axiom test --changed`

Về sau query graph của compiler có thể xác định test bị ảnh hưởng.

Ví dụ sửa:

```text
compiler/typeck/
```

chỉ chạy:

```text
type tests
trait tests
HIR tests
dependent conformance
```

thay vì toàn bộ hàng trăm nghìn test.

---

# 38. Conformance matrix

Tạo:

```text id="harness80"
Conformance Matrix
```

```text
                    Oracle  O0  O1  O2  O3  ELF  ABI
ownership            ✓      ✓   ✓   ✓   ✓
traits               ✓      ✓   ✓   ✓   ✓
views                ✓      ✓   ✓   ✓   ✓
drop                 ✓      ✓   ✓   ✓   ✓
async                ✓      ✓   ✓   ✓   ✓
atomics              ✓      ✓   ✓   ✓   ✓
FFI                  ✓      ✓   ✓   ✓   ✓   ✓
```

Không cần đạt hết ngay; đây là dashboard tiến độ.

---

# 39. Harness invariant

Chốt:

```text id="harness81"
AHARNESS-20
Tests must be deterministic.

AHARNESS-21
Positive tests must have explicit expected semantics.

AHARNESS-22
Negative tests must assert diagnostic codes.

AHARNESS-23
Compiler diagnostics must be machine-readable.

AHARNESS-24
Oracle semantics are independent of native code generation.

AHARNESS-25
Optimization tests must preserve Oracle-observable behavior.

AHARNESS-26
Backend tests may assert target-specific representation.

AHARNESS-27
Encoder tests may assert exact bytes.

AHARNESS-28
Linker tests may assert ELF structure.

AHARNESS-29
Benchmark results must record environment metadata.

AHARNESS-30
Benchmark data must not define language semantics.

AHARNESS-31
Compiler output must be reproducible.

AHARNESS-32
Parallel and serial compilation must be semantically equivalent.

AHARNESS-33
Failed tests preserve diagnostic artifacts.

AHARNESS-34
Fuzz-generated programs must be reproducible from a seed.

AHARNESS-35
Optimizer output must pass verification.

AHARNESS-36
Native execution must be differentially testable against Oracle.

AHARNESS-37
ABI tests must use independently compiled foreign references where applicable.

AHARNESS-38
Performance regression thresholds must not change language semantics.
```

---

# 40. Milestone

Chốt thành:

```text
HARNESS-001
test runner

HARNESS-002
golden AST/HIR/MIR

HARNESS-003
diagnostic tests

HARNESS-004
Oracle differential tests

HARNESS-005
optimization equivalence

HARNESS-006
backend tests

HARNESS-007
encoder tests

HARNESS-008
ELF/linker tests

HARNESS-009
ABI/FFI tests

HARNESS-010
fuzzer

HARNESS-011
benchmark runner

HARNESS-012
reproducible build

HARNESS-013
AI-readable failure artifacts
```

---

# 41. Sau bước này, Axiom đã có “hệ thần kinh” để tự kiểm tra

Kiến trúc lúc này thực sự bắt đầu hoàn chỉnh:

```text
                  ┌──────────── Oracle
                  │
Source → Compiler ├──────────── Conformance
                  │
                  └──────────── Optimizer
                                  ↓
                              Native
                                  ↓
                               Runner
                                  ↓
                              Compare
```

Và một điều rất quan trọng:

**Từ đây, mỗi feature mới không còn được phép “viết code rồi hy vọng chạy”.**

Quy trình bắt buộc sẽ là:

```text
Semantic rule
    ↓
Invariant
    ↓
Positive test
    ↓
Negative test
    ↓
Oracle test
    ↓
Optimization equivalence
    ↓
ABI/backend test nếu cần
    ↓
Benchmark nếu ảnh hưởng performance
```

Đây chính là nền móng để sau này giao cho AI agent kiểu Claude/Gemini/Antigravity tự phát triển Axiom mà vẫn giữ được kiến trúc.

## Bước kế tiếp

Bây giờ tôi sẽ không quay lại thêm feature ngôn ngữ. Bước hợp lý tiếp theo là **Bootstrap Compiler v0.1**:

```text
C/C++ bootstrap compiler
        ↓
Axiom compiler core
        ↓
Axiom → x86-64
        ↓
Axiom compiler viết bằng Axiom
        ↓
self-hosting
```

Trong bước đó cần giải quyết một vấn đề rất quan trọng mà trước đây ta chưa chốt đủ sâu: **compiler bootstrap tối thiểu phải dùng ngôn ngữ nào, giai đoạn nào chuyển từng subsystem sang Axiom, và làm thế nào để cuối cùng Axiom compiler không còn phụ thuộc compiler C/C++ bên ngoài**.