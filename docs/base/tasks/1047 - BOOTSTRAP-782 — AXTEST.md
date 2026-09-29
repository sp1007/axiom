# BOOTSTRAP-782 — AXTEST

**Native Axiom Testing, Unit/Integration/System/Compiler/ABI/Runtime Testing, Property Testing, Fuzzing, Golden Tests, Differential Testing, Deterministic Replay, Cross-Target Conformance, Performance Regression & Self-Hosting Verification Runtime 5.0**

**Namespace:** `AXTEST`  
**Status:** **FROZEN — Target 5.0**  
**ABI:** `AXTEST_ABI_1`

---

# 1. Mục tiêu

`AXTEST` là **verification layer của toàn bộ Axiom**, không chỉ là thư viện unit-test.

```text
                         AXTEST
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
      SOURCE            COMPILER           RUNTIME
        │                  │                  │
     parser             AST/HIR/MIR       AXRUNTIME
        │                  │                  │
     semantic             IR/SSA          AXTASK
        │                  │                  │
     diagnostics        codegen           AXASYNC
        │                  │                  │
        └──────────────┬───┴───────┬──────────┘
                       │           │
                    AXOBJECT     AXABI
                       │           │
                    AXLINKER───────┘
                       │
                    AXBINARY
                       │
                    AXLOADER
                       │
                   AXSTARTUP
                       │
                  APPLICATION
```

AXTEST phải có khả năng trả lời:

> "Một chương trình Axiom có đúng không?"

nhưng cũng phải trả lời được:

> "Compiler có biên dịch đúng không?"

> "IR có đúng không?"

> "Machine code có đúng không?"

> "Object/linker/binary có đúng không?"

> "ABI có tương thích không?"

> "Runtime có đúng không?"

> "Stage2 compiler có tạo ra chính compiler tương đương Stage1 không?"

---

# 2. Boundary

## 2.1 AXTEST sở hữu

AXTEST sở hữu:

- test definition
- test discovery
- test execution
- fixtures
- test isolation
- assertions
- expected results
- golden/snapshot comparison
- property testing
- fuzzing
- deterministic replay
- differential testing
- cross-target conformance
- compiler conformance
- ABI conformance
- binary conformance
- runtime conformance
- benchmark/regression measurement
- test sharding
- parallel scheduling
- result serialization
- failure minimization
- test artifact generation
- test metadata
- self-hosting verification

## 2.2 Không sở hữu

AXTEST **không sở hữu**:

```text
AXCOMPILER  → compiler implementation
AXOBJECT    → object format
AXLINKER    → linking
AXBINARY    → final binary representation
AXLOADER    → loading
AXSTARTUP   → process bootstrap
AXRUNTIME   → runtime implementation
AXSTANDARD  → standard library implementation
AXTIME      → time implementation
AXRANDOM    → RNG implementation
AXSECURITY  → security enforcement
AXBUILD     → build graph
AXTOOLCHAIN → target/toolchain description
```

AXTEST chỉ **kiểm chứng** các subsystem này.

---

# 3. Nguyên tắc thiết kế

### TEST-PRINCIPLE-01 — deterministic by default

Test thông thường phải deterministic.

### TEST-PRINCIPLE-02 — isolation by default

Một test không được phụ thuộc trạng thái test khác.

### TEST-PRINCIPLE-03 — explicit nondeterminism

Stress/concurrency/random tests có thể nondeterministic nhưng phải ghi rõ mode.

### TEST-PRINCIPLE-04 — no hidden network

Test bình thường không được tự động truy cập Internet.

### TEST-PRINCIPLE-05 — no hidden downloads

Test phải chạy được từ local test corpus.

### TEST-PRINCIPLE-06 — test compiler itself

Không được chỉ kiểm tra application output.

### TEST-PRINCIPLE-07 — test every abstraction boundary

Mỗi ABI/format/runtime boundary phải có conformance suite.

### TEST-PRINCIPLE-08 — reproducible failure

Một failure phải có khả năng tái tạo bằng seed + input + configuration.

### TEST-PRINCIPLE-09 — machine-readable result

Kết quả phải có format máy đọc được.

### TEST-PRINCIPLE-10 — test infrastructure itself is tested

AXTEST phải tự kiểm chứng runner, scheduler, result serializer, replay system.

---

# 4. Testing pyramid

```text
                    SYSTEM
                   /       \
             END-TO-END    PLATFORM
                /            \
          INTEGRATION      ABI/BINARY
             /                 \
        COMPONENT             COMPILER
             \                 /
              UNIT + PROPERTY
                     │
                   FUZZ
```

Các lớp:

1. unit
2. component
3. property
4. compiler
5. IR
6. code generation
7. ABI
8. object
9. linker
10. binary
11. loader
12. startup
13. runtime
14. standard library
15. integration
16. system
17. cross-target
18. differential
19. fuzz
20. performance
21. bootstrap

Không lớp nào được coi là thay thế hoàn toàn lớp khác.

---

# 5. Test Model

Canonical:

```text
TestCase {
    id
    name
    suite
    kind
    source
    entry
    target
    profile
    requirements
    fixtures[]
    dependencies[]
    timeout
    seed
    isolation
    expected
    metadata
}
```

`kind`:

```text
UNIT
COMPONENT
INTEGRATION
SYSTEM
COMPILER
SEMANTIC
IR
CODEGEN
ABI
OBJECT
LINKER
BINARY
LOADER
STARTUP
RUNTIME
STANDARD
PROPERTY
FUZZ
GOLDEN
DIFFERENTIAL
CONFORMANCE
PERFORMANCE
BOOTSTRAP
SECURITY
```

---

# 6. Test Suite

```text
TestSuite {
    id
    name
    version
    tests[]
    fixtures[]
    target_matrix
    environment
    policy
    metadata
}
```

Suite có thể chứa:

```text
ax.test.compiler
ax.test.runtime
ax.test.abi
ax.test.binary
ax.test.standard
ax.test.platform
ax.test.bootstrap
```

---

# 7. Test Manifest

File canonical:

```text
test.axmanifest
```

Ví dụ:

```text
test {
    name = "integer-overflow"
    kind = semantic

    source = "overflow.ax"

    target = "x86_64-windows"
    profile = "debug"

    timeout = 2s

    expected {
        exit = 0
        stdout = "overflow detected\n"
    }
}
```

Compiler test:

```text
test {
    name = "generic-inference"
    kind = compiler

    source = "generic.ax"

    expect {
        compile = success
    }
}
```

Negative test:

```text
test {
    name = "invalid-type"
    kind = semantic

    source = "invalid.ax"

    expect {
        compile = failure
        diagnostic = "TYPE-MISMATCH"
    }
}
```

---

# 8. Test Lifecycle

```text
DISCOVER
   ↓
LOAD
   ↓
VALIDATE
   ↓
PREPARE
   ↓
FIXTURE
   ↓
EXECUTE
   ↓
COLLECT
   ↓
COMPARE
   ↓
CLASSIFY
   ↓
STORE
   ↓
REPORT
```

Các trạng thái:

```text
DISCOVERED
QUEUED
PREPARING
RUNNING
PASSED
FAILED
SKIPPED
BLOCKED
TIMEOUT
CRASHED
CANCELLED
UNSUPPORTED
INVALID
```

---

# 9. Test Isolation

Mặc định:

```text
Test
 ├── private environment
 ├── private temporary directory
 ├── private process
 ├── controlled environment variables
 ├── controlled clock
 ├── controlled RNG
 ├── controlled scheduler
 └── resource limits
```

Không được để:

```text
test A → modifies global state
       ↓
test B accidentally observes it
```

---

# 10. Isolation Levels

```text
NONE
IN_PROCESS
THREAD
TASK
PROCESS
SANDBOX
VM
```

Mặc định:

- unit → `IN_PROCESS`
- runtime crash → `PROCESS`
- security → `SANDBOX`
- kernel/platform → external harness
- destructive tests → isolated environment

---

# 11. Assertion Model

Canonical:

```text
assert(condition)

assert_equal(a, b)
assert_not_equal(a, b)

assert_true(x)
assert_false(x)

assert_null(x)
assert_not_null(x)

assert_same(a, b)
assert_not_same(a, b)

assert_near(a, b, tolerance)

assert_contains(container, value)

assert_panics(fn)
assert_traps(fn)
assert_returns_error(fn)

assert_compile_success(source)
assert_compile_failure(source)

assert_binary_equal(a, b)
assert_object_equal(a, b)
```

Assertions phải tạo diagnostic:

```text
expected
actual
location
expression
type
formatted value
test id
seed
trace
```

---

# 12. Source Location

Mọi failure có source location nếu khả dụng:

```text
SourceLocation {
    file
    line
    column
    byte_offset
    symbol
}
```

Compiler diagnostics phải preserve:

```text
source → token → AST → HIR → MIR → IR → machine code
```

để AXTEST có thể kiểm chứng source mapping.

---

# 13. Unit Testing

Unit test kiểm tra:

- function
- method
- trait implementation
- parser component
- lexer
- data structure
- allocator component
- runtime primitive

Ví dụ:

```text
@test
fn add_test() {
    assert_equal(add(2, 3), 5)
}
```

Compiler có thể compile test function trực tiếp.

Không yêu cầu reflection.

---

# 14. Integration Testing

Kiểm tra nhiều subsystem:

```text
source
 ↓
AXCOMPILER
 ↓
AXOBJECT
 ↓
AXLINKER
 ↓
AXBINARY
 ↓
AXLOADER
 ↓
AXSTARTUP
 ↓
AXRUNTIME
 ↓
program
```

Đây là lớp cực kỳ quan trọng của Axiom.

---

# 15. System Testing

System test chạy artifact như một application thật.

Ví dụ:

```text
compile
→ link
→ produce exe
→ launch process
→ provide argv/env
→ capture stdout/stderr
→ inspect exit code
→ inspect files
→ inspect resources
```

Không được coi output compiler là bằng chứng đủ.

---

# 16. Compiler Testing

Compiler test chia thành:

```text
LEXER
PARSER
AST
NAME_RESOLUTION
TYPE_CHECK
TRAITS
GENERICS
INFERENCE
CONST_EVAL
LOWERING
HIR
MIR
SSA
OPTIMIZATION
CODEGEN
DEBUG
DIAGNOSTICS
```

Mỗi tầng có thể test độc lập.

---

# 17. Golden Compiler Tests

Input:

```text
example.ax
```

Expected:

```text
example.ast.gold
example.hir.gold
example.mir.gold
example.ir.gold
example.asm.gold
example.diag.gold
```

Không nhất thiết golden toàn bộ pipeline.

Có thể chọn:

```text
--golden=ast
--golden=mir
--golden=ir
--golden=asm
```

---

# 18. Canonicalization

Golden output phải canonical.

Ví dụ IR:

```text
%tmp17
```

có thể normalize thành:

```text
%tmp0
```

Canonicalization loại bỏ:

- memory addresses
- timestamps
- random IDs
- absolute paths
- machine-specific temporary names
- nondeterministic ordering

trừ khi chính chúng là đối tượng kiểm thử.

---

# 19. Snapshot Testing

Snapshot:

```text
snapshot {
    input
    canonical_output
    version
    target
    compiler
}
```

Khi snapshot thay đổi:

```text
OLD
NEW
DIFF
REASON
```

Không tự động overwrite golden trong CI.

---

# 20. Property-Based Testing

Thay vì:

```text
test x = 17
```

kiểm tra property:

```text
for all x:
    decode(encode(x)) == x
```

Generator:

```text
Generator<T> {
    generate(seed, size) -> T
}
```

Các generator cơ bản:

```text
bool
integer
float
bytes
string
unicode
array
tuple
struct
enum
AST
IR
binary
```

---

# 21. Property Shrinking

Khi failure:

```text
large failing input
       ↓
shrink
       ↓
smaller input
       ↓
minimal reproducer
```

Ví dụ:

```text
10000-token program
        ↓
remove irrelevant statements
        ↓
17-token program
```

Shrinker phải deterministic.

---

# 22. Fuzzing

AXTEST có native fuzz engine:

```text
Corpus
   ↓
Mutator
   ↓
Input
   ↓
Target
   ↓
Observation
   ↓
Crash / Failure?
   ↓
Minimize
   ↓
Corpus
```

Targets:

```text
lexer
parser
type checker
IR parser
object reader
binary reader
linker
loader
UTF-8
serialization
standard collections
runtime APIs
```

---

# 23. Fuzz Input Model

```text
FuzzCase {
    target
    seed
    iteration
    input
    timeout
    memory_limit
    result
    crash_signature
}
```

Mỗi failure phải lưu:

```text
seed
input
target
compiler version
AXTEST version
target ABI
toolchain fingerprint
```

---

# 24. Fuzz Corpus

```text
corpus/
    seed/
    generated/
    interesting/
    crash/
    minimized/
```

Corpus phải có hash.

Không được đưa duplicate vào corpus.

---

# 25. Deterministic Replay

Command:

```text
axtest replay <failure>
```

phải tái tạo:

```text
input
seed
target
environment
virtual clock
scheduler schedule
compiler flags
toolchain
```

Mục tiêu:

```text
same input
+
same seed
+
same configuration
=
same observable result
```

---

# 26. Randomness

Mỗi test có:

```text
seed
```

Nếu không chỉ định:

```text
seed = deterministic(hash(test_id, suite_version))
```

Stress mode:

```text
--random-seed=auto
```

nhưng seed thực tế phải được ghi vào result.

Không sử dụng global implicit RNG.

---

# 27. Virtual Time

Concurrency/async test phải có:

```text
VirtualClock
```

Ví dụ:

```text
sleep(10s)
```

không nhất thiết phải chờ 10 giây thực.

Test scheduler:

```text
advance_time(10s)
```

cho phép kiểm tra:

- timeout
- timer
- deadline
- retry
- cancellation
- async scheduling

mà không phụ thuộc wall-clock.

---

# 28. Controlled Scheduler

AXTEST cung cấp:

```text
TestScheduler {
    spawn(task)
    run_next()
    run_until_idle()
    advance_time(duration)
    choose(task)
    checkpoint()
}
```

Cho phép tái tạo:

```text
Task A
Task B
Task A
Task C
Task B
```

đúng thứ tự.

Đây là cơ sở cho deterministic concurrency testing.

---

# 29. Concurrency Testing

Kiểm tra:

- race
- deadlock
- starvation
- livelock
- cancellation
- task ordering
- channel semantics
- mutex semantics
- atomic operations
- memory visibility

Test scheduler cố định trước khi chuyển sang stress mode.

---

# 30. Race/Deadlock Detection

AXTEST có thể chạy backend:

```text
SCHEDULE_EXPLORATION
LOCK_GRAPH
ATOMIC_TRACE
MEMORY_SANITIZER
```

AXTEST không thay thế AXRUNTIME hoặc AXSECURITY.

Nó chỉ instrument chúng.

---

# 31. Filesystem Fixture

```text
FixtureFS {
    root
    files[]
    permissions
    timestamps
}
```

Test có thể khai báo:

```text
fixture {
    file "/config/a.txt" = "hello"
    file "/data/x.bin" = bytes(...)
}
```

Không phụ thuộc filesystem thật nếu không cần.

---

# 32. Network Fixture

Mặc định:

```text
NETWORK = DENY
```

Mock:

```text
MockNetwork {
    endpoint
    request
    response
    delay
    failure
}
```

Integration test thực sự dùng network phải khai báo:

```text
network = external
```

và thuộc test profile riêng.

---

# 33. Process Fixture

Có thể mock:

```text
spawn
exit
stdout
stderr
signal
environment
argv
```

System test vẫn có thể chạy process thật.

---

# 34. Golden Binary Tests

AXBINARY/AXLINKER phải có golden fixtures:

```text
minimal.exe
minimal.o
minimal.lib
minimal.so
minimal.elf
minimal.macho
minimal.wasm
```

Không compare raw bytes nếu field chứa:

- timestamp
- UUID
- address
- signing data

trừ khi canonicalized.

---

# 35. Structural Binary Comparison

AXTEST có binary comparator:

```text
compare_binary(a, b,
    mode = STRUCTURAL
)
```

So sánh:

```text
headers
segments
sections
imports
exports
relocations
entry
TLS
metadata
```

Thay vì chỉ byte-for-byte.

---

# 36. ABI Conformance

AXABI phải có suite:

```text
scalar
integer
float
vector
struct
enum
union
tuple
array
slice
string
function pointer
generic monomorphized
method receiver
return values
stack alignment
register allocation
variadic boundary
TLS
unwind
```

Mỗi target:

```text
x86_64-windows
x86_64-linux
x86_64-macos
aarch64-linux
aarch64-macos
aarch64-ios
aarch64-android
wasm32
```

---

# 37. ABI Probe

Compiler có thể generate probe:

```text
abi_probe {
    function
    parameters
    returns
    expected_registers
    expected_stack
}
```

Sau đó AXTEST kiểm tra machine-level behavior.

---

# 38. C ABI

Phải có explicit:

```text
extern "C"
```

test suite:

```text
Axiom → C
C → Axiom
Axiom struct → C
C struct → Axiom
Axiom callback → C
C callback → Axiom
```

Không được suy luận C ABI từ AXABI.

---

# 39. Object Tests

AXOBJECT tests:

```text
sections
symbols
relocations
archives
COMDAT
weak
TLS
debug
unwind
visibility
imports
exports
alignment
hashing
canonicalization
```

Test malformed object:

```text
truncated
overflow
invalid relocation
invalid symbol
duplicate table
invalid offset
invalid alignment
```

---

# 40. Linker Tests

AXLINKER test:

```text
one object
multiple objects
static archive
shared library
weak symbols
duplicate symbols
cyclic archive
TLS
PIE
relocations
dead stripping
ICF
debug
unwind
imports
exports
```

Negative tests phải xác nhận linker **từ chối đúng**.

---

# 41. Loader Tests

AXLOADER:

```text
minimal executable
shared library
dependency chain
TLS
ASLR
PIE
imports
relocations
permissions
W^X
unload
dependency cycle
missing dependency
invalid binary
```

Loader tests không được execute binary untrusted ngoài sandbox.

---

# 42. Startup Tests

AXSTARTUP test:

```text
argc
argv
env
auxv
stack
TLS
Unicode command line
raw bytes
platform data
entry ABI
freestanding
WASM startup
```

Có synthetic raw startup fixture.

---

# 43. Runtime Tests

AXRUNTIME:

```text
allocation
deallocation
panic/trap
thread/task
TLS
startup
shutdown
error propagation
resource cleanup
signals
stack
atomic
scheduler
```

Runtime crash tests phải chạy process-isolated.

---

# 44. Standard Library Tests

AXSTANDARD:

```text
String
Str
Bytes
Vec
HashMap
Option
Result
Iterator
format
parse
numeric
Path
environment
time facade
random facade
```

Đặc biệt:

```text
UTF-8 validity
UTF-8 boundary
invalid UTF-8
zero-length
maximum lengths
overflow
capacity growth
allocation failure
```

---

# 45. Platform Matrix

Canonical:

| Target | Required | Tests |
|---|---|---|
| x86_64 Windows PE64 | Yes | Full |
| x86_64 Linux ELF64 | Yes | Full |
| AArch64 Linux ELF64 | Yes | Full |
| x86_64 macOS Mach-O | Yes | Full |
| AArch64 macOS | Yes | Full |
| AArch64 iOS | Yes | Platform |
| AArch64 Android | Yes | Platform |
| WASM32 | Yes | Hosted |

Target state:

```text
SUPPORTED
PARTIAL
OPTIONAL
UNSUPPORTED
```

Không được coi `UNSUPPORTED` là test failure.

---

# 46. Cross-Target Conformance

Một semantic test có thể chạy:

```text
source
 ↓
compile(target A)
 ↓
compile(target B)
 ↓
execute
 ↓
normalize result
 ↓
compare
```

Ví dụ:

```text
2 + 3 = 5
```

phải cho semantic result giống nhau trên mọi target hỗ trợ feature.

---

# 47. Differential Testing

AXTEST hỗ trợ:

```text
Axiom compiler
       vs
reference evaluator
```

hoặc:

```text
Axiom compiler v1
       vs
Axiom compiler v2
```

hoặc:

```text
AXLINKER
       vs
independent structural validator
```

Không được coi implementation thứ hai là oracle tuyệt đối.

Differential result phải ghi rõ:

```text
oracle
version
scope
limitations
```

---

# 48. Reference Evaluator

Nếu Axiom có interpreter/reference evaluator:

```text
source
 ├── reference evaluator
 └── native compiler
          ↓
      observable result
```

So sánh:

```text
stdout
stderr
exit
return value
structured result
```

Reference evaluator ưu tiên:

- đơn giản
- đúng
- dễ audit

không tối ưu tốc độ.

---

# 49. Compiler Self-Testing

Compiler phải tự compile test suite:

```text
AXCOMPILER
    ↓
compile AXTEST suite
    ↓
execute
    ↓
results
```

Compiler không được tự xác nhận duy nhất bằng implementation nội bộ của chính nó.

---

# 50. Stage Bootstrap

Axiom bootstrap:

```text
Stage0
   ↓ compile
Stage1
   ↓ compile
Stage2
   ↓ compile
Stage3/self-hosted
```

AXTEST kiểm tra:

```text
Stage1 == expected
Stage2 == Stage1-equivalent
Stage3 == Stage2-equivalent
```

---

# 51. Bootstrap Equivalence

Không nhất thiết binary phải giống byte-for-byte.

So sánh theo cấp:

```text
LEVEL 1
artifact valid

LEVEL 2
ABI equivalent

LEVEL 3
symbol equivalent

LEVEL 4
IR canonical equivalent

LEVEL 5
behavior equivalent
```

Có thể bật reproducible byte comparison khi toolchain deterministic.

---

# 52. Reproducibility Test

Compile:

```text
same source
same compiler
same toolchain
same SDK
same environment
```

hai lần:

```text
artifact A
artifact B
```

Expected:

```text
A == B
```

Nếu target cho phép deterministic output.

Nếu không:

```text
canonical(A) == canonical(B)
```

---

# 53. Build Environment Capture

Mỗi failure ghi:

```text
compiler_version
axtest_version
toolchain_fingerprint
target
abi
sdk
sysroot
optimization
debug_mode
environment_hash
source_hash
test_seed
```

Không lưu secrets.

---

# 54. Crash Tests

Test có thể expect:

```text
PANIC
TRAP
ABORT
SIGNAL
PROCESS_CRASH
TIMEOUT
```

Ví dụ:

```text
expect {
    result = trap
    code = BOUNDS_CHECK
}
```

Không được coi mọi crash là tương đương.

---

# 55. Diagnostic Testing

Compiler diagnostic được kiểm tra:

```text
error code
severity
source location
message class
notes
spans
suggestions
```

Không nên golden toàn bộ text nếu text không phải API ổn định.

Ưu tiên:

```text
diagnostic code
span
structured fields
```

---

# 56. AI-Readable Metadata

AXTEST cung cấp:

```text
TestMetadata {
    purpose
    subsystem
    preconditions
    inputs
    expected_behavior
    failure_class
    target_constraints
    determinism
    isolation
    dependencies
    safety_level
}
```

Compiler/AI agent có thể query:

```text
find tests for AXABI aggregate return
```

hoặc:

```text
find regression tests for PE64 TLS
```

---

# 57. Test Artifact

Canonical result:

```text
TestResult {
    test_id
    suite_id
    status
    duration
    target
    seed
    exit_code
    stdout
    stderr
    diagnostics[]
    artifacts[]
    metrics[]
    failure
    trace
    environment
}
```

---

# 58. Machine-Readable Result

Format chính:

```text
.axtest-result
```

Có thể serialize:

```text
binary
JSON
text
```

Binary dùng cho CI/performance.

JSON dùng cho tools/AI.

Text dùng cho developer.

---

# 59. Failure Object

```text
TestFailure {
    class
    message
    expected
    actual
    location
    seed
    input
    command
    environment
    trace
    artifacts[]
    reproduction
}
```

Failure phải sinh reproduction command.

Ví dụ:

```text
axtest replay test/compiler/generic-17 --seed 4839201
```

---

# 60. Failure Minimization

Các failure:

```text
compiler crash
fuzz failure
wrong codegen
wrong diagnostic
deadlock
timeout
```

phải có minimizer phù hợp.

Pipeline:

```text
failure
 ↓
classify
 ↓
minimize
 ↓
validate minimized case
 ↓
store reproducer
```

---

# 61. Flaky Test Detection

AXTEST không tự động coi test flaky là pass.

Có trạng thái:

```text
PASS
FAIL
FLAKY
```

Flaky detection:

```text
run N times
compare outcomes
```

Metadata:

```text
flaky_reason
observed_runs
failure_rate
last_failure
```

Policy:

```text
CI may fail on known flaky tests
```

hoặc explicit quarantine.

Quarantine không được che giấu failure.

---

# 62. Parallel Test Execution

Scheduler:

```text
Test Graph
    ↓
ready queue
    ↓
worker 1
worker 2
worker 3
...
```

Test có dependency thì:

```text
A → B → C
```

Không chạy song song sai thứ tự.

---

# 63. Test Resource Model

Mỗi test khai báo:

```text
cpu
memory
disk
processes
threads
network
gpu
time
```

Ví dụ:

```text
resources {
    cpu = 2
    memory = 256MiB
    processes = 4
    network = false
}
```

Scheduler dùng để tránh overcommit.

---

# 64. Sharding

Suite lớn chia:

```text
shard 0/16
shard 1/16
...
shard 15/16
```

Stable hash:

```text
hash(test_id) % shard_count
```

Không được phụ thuộc execution order.

---

# 65. Test Cache

AXTEST có thể cache:

```text
test input hash
compiler fingerprint
target
flags
fixtures
dependencies
```

Nếu tất cả giống nhau:

```text
CACHE HIT
```

Nhưng:

```text
nondeterministic test
stress test
external-state test
```

không cache mặc định.

---

# 66. Incremental Testing

Thay đổi:

```text
lexer
```

không nhất thiết chạy:

```text
entire platform suite
```

AXTEST có dependency metadata:

```text
test → subsystem → source/component
```

AXBUILD có thể yêu cầu AXTEST chạy affected tests.

---

# 67. Performance Testing

Benchmark result không chỉ là một số.

```text
BenchmarkResult {
    iterations
    warmup
    min
    max
    mean
    median
    p50
    p90
    p95
    p99
    stddev
    allocations
    bytes_allocated
    cpu_time
    wall_time
}
```

---

# 68. Performance Regression

Baseline:

```text
baseline
current
delta
threshold
```

Ví dụ:

```text
compile_time +8%
binary_size +3%
runtime +1%
allocations +0%
```

Threshold configurable theo benchmark.

Không hard-code một ngưỡng toàn hệ thống.

---

# 69. Memory Testing

AXTEST kiểm tra:

```text
leak
double free
use-after-free
invalid free
buffer overflow
stack overflow
allocator corruption
fragmentation
```

Các backend sanitizer là optional instrumentation.

AXTEST không biến sanitizer thành runtime requirement.

---

# 70. Debug/Unwind Tests

Test:

```text
panic
crash
stack trace
source mapping
symbolization
unwind
debug info
```

Kiểm tra:

```text
machine address
 ↓
symbol
 ↓
source file
 ↓
line
```

---

# 71. Security Testing

AXTEST security suite:

```text
malformed object
malformed binary
malformed package
resource exhaustion
integer overflow
path traversal
invalid UTF-8
oversized input
deep recursion
huge symbol table
cyclic dependency
malicious metadata
```

Mọi parser nhận binary bên ngoài phải có fuzz suite.

---

# 72. Resource Exhaustion

Test giới hạn:

```text
max input
max nesting
max symbols
max sections
max relocations
max dependencies
max memory
max execution time
```

Expected:

```text
controlled failure
```

không phải:

```text
host crash
unbounded allocation
hang forever
```

---

# 73. Test Security Boundary

AXTEST runner phải coi:

```text
test source
fixture
fuzz input
golden file
binary
external output
```

là untrusted data.

Không được:

```text
execute fixture
trust metadata
follow arbitrary paths
download arbitrary files
```

nếu chưa được policy cho phép.

---

# 74. Test Runner Architecture

```text
                axtest
                  │
             Test Registry
                  │
             Test Scheduler
          ┌───────┼────────┐
          │       │        │
       Worker   Worker   Worker
          │       │        │
      Sandbox  Process   InProcess
          │       │        │
          └───────┼────────┘
                  │
             Result Collector
                  │
             Result Database
                  │
          Report / CI / AI
```

---

# 75. Worker

```text
TestWorker {
    id
    capabilities
    resource_budget
    execute(test)
    cancel(test)
    collect()
}
```

Worker phải có cancellation.

---

# 76. Runner Modes

```text
axtest run
axtest list
axtest filter
axtest replay
axtest fuzz
axtest bench
axtest compare
axtest golden
axtest update-golden
axtest bootstrap
axtest conformance
```

---

# 77. Filter

Ví dụ concept:

```text
axtest run --suite compiler
axtest run --kind abi
axtest run --target x86_64-windows
axtest run --tag parser
axtest run --changed
```

---

# 78. Test Tags

```text
fast
slow
compiler
runtime
platform
network
filesystem
unsafe
fuzz
stress
benchmark
bootstrap
security
```

---

# 79. Test Profiles

```text
MINIMAL
FAST
DEFAULT
FULL
CI
NIGHTLY
STRESS
FUZZ
BOOTSTRAP
RELEASE
```

Ví dụ:

```text
FAST
→ unit + compiler smoke

CI
→ unit + integration + conformance

NIGHTLY
→ fuzz + stress + cross-target + bootstrap
```

---

# 80. External Tool Integration

AXTEST có adapter:

```text
TestBackend {
    discover()
    execute()
    collect()
    normalize()
}
```

Có thể tích hợp:

- external debugger
- platform simulator
- OS process launcher
- hardware target

Nhưng Axiom test semantics vẫn thuộc AXTEST.

---

# 81. Reference Test API

Native API:

```text
test_suite_create()
test_suite_destroy()

test_register()
test_unregister()
test_find()
test_list()

test_run()
test_run_suite()
test_run_filter()

test_assert()
test_assert_equal()
test_assert_near()

test_fixture_create()
test_fixture_destroy()

test_seed()
test_clock()
test_scheduler()

test_snapshot()
test_golden_compare()

test_property()
test_fuzz()

test_replay()
test_minimize()

test_result()
test_results()
test_report()

test_benchmark()
test_compare()

test_bootstrap()
test_conformance()
```

---

# 82. Test Context

```text
TestContext {
    test_id
    seed
    clock
    scheduler
    filesystem
    network
    environment
    resources
    artifacts
    logger
}
```

Test function:

```text
fn test_x(ctx: TestContext)
```

Compiler có thể optimize context access nếu fields không được sử dụng.

---

# 83. Artifact Management

Mỗi failure có thư mục:

```text
.artifacts/
    test-id/
        input/
        stdout
        stderr
        binary
        object
        trace
        diagnostics
        environment
        result
```

Không giữ artifact thành công lâu dài trừ khi profile yêu cầu.

---

# 84. Trace

```text
TestTrace {
    events[]
}
```

Event:

```text
TEST_START
PROCESS_START
COMPILE_START
COMPILE_END
LINK_START
LINK_END
LOAD
TASK_SWITCH
ASSERT
FAILURE
TEST_END
```

Trace có sequence number deterministic.

---

# 85. Replay Trace

Concurrency test có thể lưu:

```text
task schedule
atomic ordering
virtual time
random seed
```

Replay:

```text
trace
 ↓
scheduler
 ↓
same execution ordering
```

---

# 86. Compiler Differential Matrix

Axiom compiler có thể được test:

```text
Stage0
Stage1
Stage2
Current
```

với:

```text
same source corpus
```

So sánh:

```text
diagnostics
IR
ABI
binary
runtime behavior
```

---

# 87. Optimization Correctness

Mỗi optimization có before/after:

```text
IR_before
   ↓
optimization
   ↓
IR_after
```

AXTEST kiểm tra semantic equivalence.

Ví dụ:

```text
constant folding
DCE
inlining
devirtualization
bounds-check elimination
loop optimization
SIMD
```

---

# 88. Undefined/Unsafe Behavior

AXTEST phải phân biệt:

```text
DEFINED
IMPLEMENTATION_DEFINED
TARGET_DEFINED
UNDEFINED
UNSAFE
INVALID_PROGRAM
```

Không được biến undefined behavior thành language guarantee chỉ vì test hiện tại cho một kết quả.

---

# 89. Negative Corpus

Mỗi subsystem phải có negative tests.

```text
invalid source
invalid AST
invalid IR
invalid object
invalid relocation
invalid binary
invalid loader state
invalid ABI
```

Mục tiêu:

```text
reject safely
```

không chỉ:

```text
accept correctly
```

---

# 90. Conformance Specification

AXTEST định nghĩa:

```text
ConformanceSuite {
    version
    language_version
    abi_version
    required_tests[]
    optional_tests[]
    target_requirements
}
```

Kết quả:

```text
CONFORMANT
PARTIAL
NON_CONFORMANT
UNSUPPORTED_TARGET
```

---

# 91. Language Conformance

Test:

```text
syntax
semantics
types
generics
traits
pattern matching
error model
memory model
concurrency
modules
attributes
unsafe
```

Không phụ thuộc implementation details.

---

# 92. Runtime Conformance

Test:

```text
allocation
task
async
TLS
panic
trap
process
IPC
time
random
```

Theo runtime contract.

---

# 93. Standard Library Conformance

Mỗi API public phải có:

```text
normal case
boundary case
invalid input
resource failure
cross-platform behavior
thread behavior
allocation behavior
```

---

# 94. ABI Compatibility

AXTEST phải kiểm tra:

```text
old object
+
new linker
```

và:

```text
new object
+
old-compatible ABI
```

theo compatibility matrix.

Không được tuyên bố binary compatibility chỉ vì source vẫn compile.

---

# 95. ABI Fingerprint Test

```text
AXABI fingerprint
=
target
+ calling convention
+ representation
+ alignment
+ unwind
+ TLS
+ ABI version
```

Mismatch phải được phát hiện trước link/load.

---

# 96. Binary Compatibility

Test:

```text
old shared library
new executable
```

và ngược lại trong phạm vi ABI được hỗ trợ.

Kiểm tra:

```text
symbol
calling convention
layout
version
TLS
unwind
```

---

# 97. Test Metadata for AI

Canonical AI query interface:

```text
test_search(
    subsystem = "AXLINKER",
    feature = "TLS",
    target = "PE64"
)
```

trả:

```text
test id
purpose
source
expected
related invariants
related implementation
```

Điều này giúp agent sửa compiler có thể tìm regression suite trước khi thay đổi code.

---

# 98. Test-to-Code Traceability

Mỗi test có thể tham chiếu:

```text
requirement
invariant
spec section
implementation component
regression issue
```

Ví dụ:

```text
test = LINK-TLS-004
spec = AXLINKER-SEC-17
implementation = linker/tls.ax
invariant = LINK-INV-28
```

---

# 99. Mutation Testing

AXTEST có mutation backend:

```text
correct compiler
      ↓
mutation
      ↓
broken compiler
      ↓
test suite
```

Mutation operators:

```text
replace + with -
remove bounds check
invert branch
change comparison
drop error handling
alter alignment
modify relocation
```

Mục tiêu:

> Test suite phải phát hiện lỗi có chủ ý.

---

# 100. Test Quality Metrics

Không dùng một score tổng hợp để quyết định correctness.

Có các metric riêng:

```text
test_count
coverage
mutation_detection
fuzz_cases
conformance_rate
reproducibility_rate
flaky_rate
benchmark_regressions
bootstrap_equivalence
```

Coverage:

```text
line
branch
function
IR
instruction
ABI
semantic feature
```

Coverage chỉ là metric, không phải proof of correctness.

---

# 101. Instruction Coverage

Codegen có bảng:

```text
instruction
target
test_count
```

Ví dụ:

```text
ADD
SUB
MUL
DIV
SIMD
LOAD
STORE
BRANCH
CALL
RET
ATOMIC
```

Mỗi instruction encoding phải có positive + boundary tests.

---

# 102. Relocation Coverage

Tương tự:

```text
relocation type
target
test count
overflow test
negative test
```

Đặc biệt:

```text
PE64
ELF64
Mach-O
WASM
```

---

# 103. Parser Fuzzing

Parser fuzz input:

```text
UTF-8
invalid UTF-8
very long identifiers
deep nesting
huge literals
unicode identifiers
malformed comments
unterminated strings
```

Expected:

```text
diagnostic or successful parse
```

Không crash.

---

# 104. Compiler Resource Limits

Test compiler với:

```text
huge source
huge generic depth
deep recursion
large AST
many symbols
many modules
large IR
```

Expected:

```text
bounded resource use
controlled diagnostic
```

---

# 105. No Test-Induced Semantic Changes

AXTEST instrumentation không được làm thay đổi semantics.

Ví dụ instrumentation:

```text
ASSERT
TRACE
COVERAGE
SANITIZER
```

phải có explicit mode.

---

# 106. Test Build Modes

```text
DEBUG
RELEASE
OPTIMIZED
SANITIZED
PROFILED
FREESTANDING
NO_HEAP
NO_LIBC
```

Các test core phải chạy được trong profile phù hợp.

---

# 107. Freestanding Testing

Axiom phải có suite:

```text
no libc
no OS runtime
no heap
minimal runtime
```

để chứng minh core compiler/runtime không phụ thuộc môi trường desktop.

---

# 108. WASM Testing

Pipeline:

```text
Axiom
 ↓
WASM32
 ↓
WASM validator
 ↓
WASM runtime/host
 ↓
result
```

Test:

```text
imports
exports
memory
table
globals
start
custom metadata
trap
```

---

# 109. Platform Simulator Boundary

iOS/Android test có thể cần simulator/device.

AXTEST interface:

```text
TargetExecutor {
    prepare()
    deploy()
    launch()
    collect()
    cleanup()
}
```

AXTEST không hard-code simulator implementation.

---

# 110. Test Database

Không bắt buộc database server.

Mặc định:

```text
filesystem + append-only result files
```

Có thể có indexed cache:

```text
test index
result index
artifact index
```

Phải hoạt động offline.

---

# 111. Result Retention

Profiles:

```text
LOCAL
CI
NIGHTLY
FORENSIC
```

Ví dụ:

- LOCAL → failures only
- CI → full machine-readable result
- NIGHTLY → traces/corpora
- FORENSIC → all artifacts

---

# 112. Cancellation

Runner phải hỗ trợ:

```text
cancel test
cancel suite
cancel shard
cancel entire run
```

Cancellation phải cleanup fixture/process/resource.

Không để child process mồ côi.

---

# 113. Timeout

Timeout levels:

```text
test timeout
process timeout
compile timeout
fuzz iteration timeout
suite timeout
global timeout
```

Timeout result phải ghi:

```text
which timeout
elapsed
last event
child process
resource state
```

---

# 114. Test Environment

```text
TestEnvironment {
    target
    toolchain
    sdk
    sysroot
    cwd
    env
    locale
    timezone
    clock
    rng
    scheduler
}
```

Environment có fingerprint.

---

# 115. Locale

Core compiler tests không phụ thuộc locale.

AXSTANDARD locale-sensitive tests phải explicit:

```text
locale = "vi-VN"
```

hoặc:

```text
locale = "C"
```

---

# 116. Timezone

Time tests phải explicit timezone database/version.

Không dùng timezone hệ thống ngầm định.

---

# 117. Random Test Reproducibility

Ví dụ:

```text
seed = 0xA7C10293
```

phải đủ để tái tạo.

Fuzz corpus luôn lưu seed.

---

# 118. Test Runner CLI Contract

Canonical:

```text
axtest
axtest list
axtest run
axtest replay
axtest fuzz
axtest bench
axtest compare
axtest bootstrap
axtest conformance
axtest doctor
```

`doctor` kiểm tra:

```text
toolchain
targets
SDK
runtime
sandbox
permissions
resources
```

---

# 119. Exit Codes

```text
0 = all selected tests passed
1 = test failure
2 = configuration error
3 = infrastructure failure
4 = unsupported target/profile
5 = interrupted
6 = flaky detected under strict policy
7 = internal AXTEST error
```

Exit code phải ổn định.

---

# 120. Native Test Framework API

Minimal developer-facing API:

```text
@test
fn test_add() {
    assert_equal(add(1, 2), 3)
}
```

Property:

```text
@property
fn prop_roundtrip(x: Value) {
    assert_equal(decode(encode(x)), x)
}
```

Benchmark:

```text
@benchmark
fn bench_parser() {
    parse(input)
}
```

Fuzz:

```text
@fuzz
fn fuzz_parser(data: Bytes) {
    parse(data)
}
```

Compiler có thể lower các annotations này thành AXTEST metadata.

---

# 121. Compile-Time Test Registration

Không cần reflection runtime.

Compiler sinh:

```text
TestDescriptor[]
```

vào special metadata section:

```text
.ax.test
```

AXTEST loader đọc section này.

Có thể strip khỏi production binary.

---

# 122. Test Descriptor

```text
TestDescriptor {
    id
    name
    kind
    function
    source
    line
    flags
    requirements
    metadata
}
```

Function pointer hoặc symbol reference tùy target.

---

# 123. Production Binary

Mặc định:

```text
tests stripped
```

Debug/test build:

```text
tests retained
```

Không kéo AXTEST runtime vào production nếu không cần.

---

# 124. Zero-Cost Test Framework

Test API không được ép production runtime phụ thuộc AXTEST.

Compiler có thể:

```text
@test → metadata + test harness
```

riêng trong test build.

---

# 125. Test ABI

`AXTEST_ABI_1` phải định nghĩa:

```text
TestDescriptor
TestContext
TestResult
TestFailure
TestArtifact
TestMetadata
```

Versioned.

Reserved fields zero.

Size/version ở đầu ABI-stable structs.

---

# 126. C ABI

AXTEST runner có thể expose:

```text
extern "C"
```

cho external CI integration.

Nhưng native AXTEST ABI vẫn là AXABI.

---

# 127. AXTEST ABI Stability

Stable:

```text
runner ↔ test binary
result ↔ CI
artifact ↔ tooling
```

Không stable mặc định:

```text
internal scheduler structures
internal fixture representation
internal property generator implementation
```

---

# 128. Performance Architecture

Mục tiêu:

```text
thousands of unit tests
```

không được tạo:

```text
thousands of processes
```

mặc định.

In-process tests nhanh.

Process isolation chỉ dùng khi cần.

Parallelism theo:

```text
CPU
memory
IO
target
```

---

# 129. Hot Path

Test execution hot path không được:

- format string lớn nếu không failure
- ghi disk từng assertion
- allocate unbounded trace
- lock global result database

Assertions thành công phải rất rẻ.

---

# 130. Failure-Only Diagnostics

Mặc định:

```text
PASS → minimal event
FAIL → full diagnostic
```

Trace sâu chỉ bật khi:

```text
failure
--trace
--debug
```

---

# 131. Fuzz Performance

Fuzz runner phải tái sử dụng:

```text
compiler context
allocator
parser state
process
```

khi an toàn.

Không spawn process cho mỗi fuzz iteration nếu không cần.

---

# 132. Fuzz Crash Isolation

Parser fuzz:

```text
in-process
```

Compiler crash:

```text
worker process
```

Loader/binary fuzz:

```text
sandboxed process
```

Security-sensitive fuzz:

```text
strong isolation
```

---

# 133. Test Scheduler Fairness

Scheduler phải tránh:

```text
one huge suite
```

chiếm toàn bộ workers.

Có priority:

```text
FAST
NORMAL
SLOW
RESOURCE_HEAVY
```

---

# 134. Dependency Scheduling

```text
test A
   ↓
artifact X
   ↓
test B
```

AXTEST có thể express artifact dependency nhưng phải tránh hidden mutable state.

---

# 135. Test Resource Lock

Ví dụ:

```text
GPU0
device:android-1
simulator:iOS
exclusive:file-system
```

Test manifest:

```text
requires {
    resource = "GPU0"
    mode = exclusive
}
```

Scheduler lock resource.

---

# 136. CI Integration

AXTEST output:

```text
machine result
JUnit-like adapter
CI-native adapter
human console
```

Không bắt buộc CI provider cụ thể.

---

# 137. Local Developer Workflow

```text
edit
 ↓
axtest run --changed
 ↓
fix
 ↓
axtest run --suite compiler
 ↓
axtest run --full
 ↓
commit
```

---

# 138. Regression Test Workflow

Mỗi bug:

```text
bug
 ↓
minimal reproducer
 ↓
regression test
 ↓
fix
 ↓
test passes
 ↓
permanent corpus
```

Không sửa bug mà không thêm regression test nếu test có thể được tạo hợp lý.

---

# 139. Golden Update Policy

Chỉ explicit:

```text
axtest golden update
```

Không:

```text
test failure → automatically update
```

CI tuyệt đối không tự update golden.

---

# 140. Fuzz Corpus Promotion

Interesting input:

```text
generated
 ↓
reproduces unique path/behavior
 ↓
promote
 ↓
permanent corpus
```

Corpus phải reviewable.

---

# 141. Differential Oracle Policy

Mỗi oracle phải khai báo:

```text
oracle_type
version
scope
known_differences
```

Không coi khác biệt là compiler bug trước khi normalize semantics.

---

# 142. Semantic Normalization

Ví dụ:

```text
OS error code
```

có thể khác giữa Windows/Linux.

AXTEST compare:

```text
semantic category
```

thay vì raw code khi test cross-platform.

---

# 143. Cross-Platform Expected Result

```text
Expected {
    common
    target_overrides[]
}
```

Ví dụ:

```text
common:
    exit = 0

windows:
    path_separator = "\\"

unix:
    path_separator = "/"
```

---

# 144. Unsupported Features

Nếu feature không hỗ trợ target:

```text
UNSUPPORTED
```

không phải:

```text
FAIL
```

Nhưng test phải khai báo target requirement rõ ràng.

---

# 145. Test Capability

```text
TestRequirement {
    target
    cpu_features
    os_features
    runtime_features
    sdk_version
    abi_version
}
```

Runner resolve trước khi schedule.

---

# 146. CPU Feature Testing

Codegen tests:

```text
baseline
SSE
AVX
AVX2
NEON
```

Không chạy instruction không hỗ trợ CPU host.

Có remote/hardware target abstraction nếu cần.

---

# 147. Deterministic Build Test

AXBUILD + AXTEST:

```text
clean build
incremental build
clean build
```

So sánh:

```text
artifacts
dependencies
cache behavior
```

Expected semantic equivalence và reproducibility theo profile.

---

# 148. Cache Correctness

Test:

```text
build A
modify unrelated file
build B
```

Expected:

```text
affected nodes rebuild
unaffected nodes cache-hit
```

Sau đó compare clean build.

---

# 149. Compiler Cache Poisoning Test

Thay đổi:

```text
compiler version
ABI
target
optimization
source
dependency
SDK
```

phải invalidate cache khi cần.

Đây là security/correctness test quan trọng.

---

# 150. Toolchain Fingerprint Test

AXTEST xác nhận:

```text
compiler
assembler
linker
SDK
sysroot
runtime
ABI
target
```

thay đổi → fingerprint thay đổi.

---

# 151. Self-Hosting Test

Canonical pipeline:

```text
Stage0 compiler
       ↓
Stage1 compiler
       ↓
Stage1 compiles itself
       ↓
Stage2
       ↓
Stage2 compiles itself
       ↓
Stage3
```

AXTEST tự động compare.

---

# 152. Bootstrap Trust

Không tuyên bố bootstrap thành công chỉ vì executable chạy.

Phải kiểm tra:

```text
compiler functionality
ABI
artifacts
tests
reproducibility
semantic equivalence
```

---

# 153. Stage0 External Tool

Stage0 có thể sử dụng:

```text
external host compiler/linker
```

nhưng chỉ trong bootstrap.

AXTEST phải xác định:

```text
BOOTSTRAP_EXTERNAL
```

để không nhầm với final architecture.

---

# 154. Final Self-Hosted Requirement

Final Axiom toolchain:

```text
AXCOMPILER
AXASSEMBLER
AXOBJECT
AXLINKER
AXBINARY
AXLOADER
AXSTARTUP
AXRUNTIME
AXTEST
```

phải có thể build bằng Axiom itself trong supported host environment.

---

# 155. Test Infrastructure Bootstrap

AXTEST itself:

```text
Stage0 AXTEST
 ↓
Stage1 AXTEST
 ↓
Stage2 AXTEST
```

phải verify test runner output tương đương.

---

# 156. AXTEST Internal Self-Test

AXTEST phải test chính:

```text
assertion engine
scheduler
fixture engine
result serializer
golden comparator
property engine
shrinker
fuzzer
replay engine
sharding
cache
```

---

# 157. Test Runner Fault Injection

AXTEST có fault injection:

```text
allocation failure
IO failure
timeout
process failure
thread failure
disk full
permission denied
invalid input
```

Chỉ test harness/controlled environment.

---

# 158. Allocation Failure Tests

Core runtime/standard tests:

```text
allocate
→ fail at Nth allocation
```

Expected:

```text
controlled Result/error/panic
```

không memory corruption.

---

# 159. IO Failure Tests

Fixture:

```text
read → short read
write → partial
open → denied
flush → failure
close → failure
```

Kiểm tra error propagation.

---

# 160. Fault Injection Determinism

```text
fault_seed
fault_point
fault_index
```

phải replay được.

---

# 161. Test Manifest Versioning

```text
AXTEST_MANIFEST_1
```

Manifest version độc lập với:

```text
AXTEST_ABI_1
language version
compiler version
```

---

# 162. Artifact Versioning

Artifact header:

```text
magic
version
schema
target
ABI
flags
payload
checksum
```

Reader phải reject unsupported version an toàn.

---

# 163. Result Integrity

Result file có:

```text
checksum
```

Optional:

```text
signature
```

Signing không thuộc AXTEST; dùng AXTRUST/AXCRYPTO nếu cần.

---

# 164. Test Data Integrity

Golden/corpus có:

```text
content hash
schema version
origin
```

Nếu hash mismatch:

```text
CORRUPT_FIXTURE
```

không chạy âm thầm.

---

# 165. Test Dependency Graph

```text
Test
 ↓
Fixture
 ↓
Source
 ↓
Compiler
 ↓
Toolchain
 ↓
SDK
```

Hash toàn bộ dependency.

---

# 166. Test Selection

Selection có thể dựa trên:

```text
changed source
dependency graph
subsystem
target
tag
failure history
coverage
```

Không dùng failure history để bỏ qua test bắt buộc.

---

# 167. Failed-Test Priority

Sau failure:

```text
reproduce failed tests first
```

nhưng vẫn chạy full selected suite nếu policy yêu cầu.

---

# 168. Test Result Aggregation

Parallel workers gửi:

```text
ResultEvent
```

collector sort theo:

```text
test_id
```

để output deterministic dù execution parallel.

---

# 169. Deterministic Console Output

Không in theo completion order.

Có thể:

```text
live mode
```

nhưng final report phải stable.

---

# 170. Test Ordering

Default order:

```text
lexicographic test ID
```

không dùng order để tạo dependency.

Stress mode có thể randomize order nhưng phải ghi seed.

---

# 171. Order Dependency Detection

Runner có mode:

```text
--shuffle
```

Nếu test chỉ pass theo một thứ tự:

```text
ORDER_DEPENDENCY
```

---

# 172. Global State Detection

In-process test framework có thể snapshot một số state:

```text
allocator counters
registered handlers
global registry
TLS
```

và phát hiện leak state sau test.

---

# 173. Resource Leak Detection

Sau test:

```text
open handles
threads
tasks
file descriptors
temporary files
memory allocations
```

phải về expected baseline.

Không nhất thiết bằng zero nếu fixture giữ resource theo scope.

---

# 174. Process Leak Detection

Sau process-isolated test:

```text
no child process remains
```

trừ process được khai báo persistent.

---

# 175. Test Cleanup Guarantee

Nếu test:

```text
PASS
FAIL
PANIC
TIMEOUT
CRASH
CANCEL
```

cleanup vẫn phải chạy ở mức có thể.

---

# 176. Security Cleanup

Sensitive artifacts:

```text
tokens
keys
credentials
```

không được tự động lưu vào failure artifact.

Redaction metadata:

```text
secret
sensitive
private
```

---

# 177. No Network Default

Runner phải fail closed:

```text
network unavailable
```

nếu test không khai báo network.

---

# 178. No Implicit Host State

Tests không được phụ thuộc:

```text
current username
current directory
host timezone
host locale
host random state
host PATH
```

trừ platform tests explicit.

---

# 179. Environment Normalization

Runner set explicit:

```text
AXTEST=1
LANG=C
TZ=UTC
```

hoặc equivalent Axiom-controlled environment.

Platform tests có override.

---

# 180. Test Invariant Set

AXTEST frozen invariants:

### TEST-INV-01
Every registered test has a unique stable ID.

### TEST-INV-02
Test execution is isolated according to declared isolation.

### TEST-INV-03
Default tests are deterministic.

### TEST-INV-04
Every nondeterministic run records its seed.

### TEST-INV-05
Every replayable failure records sufficient reproduction state.

### TEST-INV-06
A test cannot silently depend on another test's mutable state.

### TEST-INV-07
Test results are machine-readable.

### TEST-INV-08
Result status is explicit.

### TEST-INV-09
Unsupported target is distinct from failure.

### TEST-INV-10
Timeout is distinct from ordinary failure.

### TEST-INV-11
Crash is distinct from assertion failure.

### TEST-INV-12
Test cancellation performs cleanup.

### TEST-INV-13
Golden files are never automatically modified during ordinary test execution.

### TEST-INV-14
Golden comparison uses canonicalization where nondeterministic fields exist.

### TEST-INV-15
Fuzz failures retain their original seed and input.

### TEST-INV-16
Fuzz corpus entries are content-addressed.

### TEST-INV-17
Property failures are minimized when a deterministic shrinker exists.

### TEST-INV-18
Property generators are seedable.

### TEST-INV-19
Virtual time is explicit.

### TEST-INV-20
Deterministic scheduler decisions are replayable.

### TEST-INV-21
Test fixtures are isolated from unrelated host state.

### TEST-INV-22
Ordinary tests have no implicit network dependency.

### TEST-INV-23
Test inputs are treated as untrusted data.

### TEST-INV-24
Malformed compiler/object/binary inputs must not crash the test infrastructure.

### TEST-INV-25
AXTEST does not silently redefine language semantics.

### TEST-INV-26
Cross-target tests normalize only explicitly target-dependent behavior.

### TEST-INV-27
ABI tests validate actual ABI behavior, not only source compilation.

### TEST-INV-28
Binary tests validate structural correctness.

### TEST-INV-29
Loader tests execute untrusted images only under declared isolation.

### TEST-INV-30
Performance results preserve enough distribution data for regression analysis.

### TEST-INV-31
Performance thresholds are configurable.

### TEST-INV-32
Parallel execution does not alter logical test results.

### TEST-INV-33
Final result ordering is deterministic.

### TEST-INV-34
Test cache keys include all correctness-relevant inputs.

### TEST-INV-35
Cache invalidation occurs when ABI/toolchain/target semantics change.

### TEST-INV-36
Flaky tests cannot silently become permanent passes.

### TEST-INV-37
Bootstrap validation checks more than executable startup.

### TEST-INV-38
Stage convergence is verified through defined equivalence levels.

### TEST-INV-39
Production binaries do not require AXTEST unless explicitly requested.

### TEST-INV-40
AXTEST itself has a self-test and bootstrap verification suite.

---

# 181. Required Conformance Suites

Axiom distribution must contain at minimum:

```text
tests/
├── language/
├── lexer/
├── parser/
├── semantic/
├── types/
├── generics/
├── traits/
├── consteval/
├── hir/
├── mir/
├── ir/
├── optimizer/
├── codegen/
├── abi/
├── object/
├── linker/
├── binary/
├── loader/
├── startup/
├── runtime/
├── standard/
├── concurrency/
├── async/
├── diagnostics/
├── debug/
├── security/
├── fuzz/
├── differential/
├── performance/
├── bootstrap/
└── platform/
```

---

# 182. Minimal Implementation Order

Để implementation khả thi, AXTEST không xây toàn bộ cùng lúc.

## Phase A — Core

```text
TestDescriptor
TestContext
assertions
runner
result
CLI
```

## Phase B — Isolation

```text
process
filesystem fixture
environment
timeout
cleanup
```

## Phase C — Compiler

```text
compiler tests
golden
diagnostics
IR
codegen
```

## Phase D — Native Artifact

```text
object
linker
binary
loader
startup
```

## Phase E — Advanced

```text
property
fuzz
shrinking
replay
scheduler
virtual time
```

## Phase F — Verification

```text
cross-target
differential
bootstrap
reproducibility
performance
```

---

# 183. Canonical End-to-End Test

Một test tối quan trọng:

```text
hello.ax
   ↓
AXCOMPILER
   ↓
AXOBJECT
   ↓
AXLINKER
   ↓
AXBINARY
   ↓
AXLOADER
   ↓
AXSTARTUP
   ↓
AXRUNTIME
   ↓
stdout
```

AXTEST phải kiểm tra toàn bộ chuỗi.

Expected:

```text
exit = 0
stdout = "Hello, Axiom!\n"
stderr = ""
```

Test này trở thành **smoke test cấp hệ thống**.

---

# 184. Compiler Correctness Test

```text
source
 ↓
reference evaluator
 ↓
expected semantics

source
 ↓
native compiler
 ↓
binary
 ↓
execute
 ↓
actual semantics
```

So sánh:

```text
expected == actual
```

Đây là một trong những test quan trọng nhất để tránh compiler tạo machine code "chạy được nhưng sai".

---

# 185. Full Verification Pipeline

Final CI:

```text
AXBUILD
  ↓
AXTEST DISCOVER
  ↓
UNIT
  ↓
COMPILER
  ↓
IR
  ↓
CODEGEN
  ↓
ABI
  ↓
OBJECT
  ↓
LINKER
  ↓
BINARY
  ↓
LOADER
  ↓
STARTUP
  ↓
RUNTIME
  ↓
STANDARD
  ↓
INTEGRATION
  ↓
SYSTEM
  ↓
CROSS-TARGET
  ↓
REPRODUCIBILITY
  ↓
BOOTSTRAP
  ↓
PERFORMANCE
  ↓
CONFORMANCE
```

---

# 186. AXTEST ↔ AXBUILD

`AXBUILD` quyết định:

```text
what needs rebuilding
```

`AXTEST` quyết định:

```text
what needs testing
```

Hai subsystem không được hợp nhất.

```text
AXBUILD
   ↓
artifact graph
   ↓
AXTEST
   ↓
test graph
```

---

# 187. AXTEST ↔ AXDIAGNOSTICS

AXTEST tạo diagnostic artifacts.

AXDIAGNOSTICS cung cấp:

```text
crash dump
stack unwind
symbolization
source mapping
```

AXTEST không thay thế crash infrastructure.

---

# 188. AXTEST ↔ AXOBSERVABILITY

AXTEST có thể consume:

```text
metrics
traces
health
```

nhưng test result vẫn là source of truth cho test status.

---

# 189. AXTEST ↔ AXSECURITY

AXTEST có thể yêu cầu:

```text
sandbox
capability restrictions
resource limits
```

nhưng không bypass AXSECURITY.

---

# 190. AXTEST ↔ AXTRUST

Test artifact signing nếu cần:

```text
AXTEST
 ↓
artifact
 ↓
AXTRUST/AXCRYPTO
```

Không tự định nghĩa cryptography mới.

---

# 191. AXTEST ↔ AXSTANDARD

AXTEST core nên phụ thuộc cực ít vào AXSTANDARD để tránh circular bootstrap.

Bootstrap:

```text
minimal AXTEST
 ↓
AXSTANDARD subset
 ↓
full AXTEST
```

---

# 192. AXTEST ↔ AXRUNTIME

AXTEST runtime test harness có thể dùng AXRUNTIME.

Nhưng phải có:

```text
minimal test mode
```

để test chính AXRUNTIME.

Nếu AXRUNTIME hỏng, AXTEST vẫn phải có khả năng report failure.

---

# 193. Failure Independence

Một nguyên tắc quan trọng:

> Test framework không được phụ thuộc hoàn toàn vào subsystem mà nó đang kiểm thử.

Ví dụ:

```text
AXRUNTIME allocator broken
```

AXTEST phải vẫn có emergency allocator/host-side runner đủ để báo lỗi.

---

# 194. Stage0 Runner

Stage0 AXTEST có thể chạy bằng host implementation.

Nó tạo:

```text
machine-readable results
```

cho Stage1.

Sau đó Stage1 chạy chính suite.

---

# 195. AXTEST Versioning

```text
AXTEST_VERSION
AXTEST_ABI
MANIFEST_VERSION
RESULT_SCHEMA
CORPUS_SCHEMA
```

độc lập.

Không được gộp thành một version number duy nhất.

---

# 196. Definition of Done

`AXTEST 5.0` chỉ được coi là hoàn thành khi:

### Core

- [x] test model
- [x] runner
- [x] assertions
- [x] isolation
- [x] fixtures
- [x] deterministic execution
- [x] result model

### Compiler

- [x] frontend tests
- [x] semantic tests
- [x] HIR/MIR/IR tests
- [x] optimization tests
- [x] codegen tests
- [x] diagnostics

### Native Toolchain

- [x] AXABI
- [x] AXOBJECT
- [x] AXLINKER
- [x] AXBINARY
- [x] AXLOADER
- [x] AXSTARTUP

### Runtime

- [x] AXRUNTIME
- [x] AXTASK
- [x] AXASYNC
- [x] AXSTANDARD

### Advanced Verification

- [x] golden tests
- [x] property tests
- [x] fuzzing
- [x] shrinking
- [x] replay
- [x] differential testing
- [x] cross-target tests
- [x] performance regression
- [x] sanitizer/debug/unwind
- [x] security/resource tests

### Bootstrap

- [x] Stage0
- [x] Stage1
- [x] Stage2
- [x] self-hosting verification
- [x] reproducibility
- [x] convergence

### Infrastructure

- [x] parallel execution
- [x] sharding
- [x] caching
- [x] machine-readable output
- [x] AI metadata
- [x] stable `AXTEST_ABI_1`
- [x] 40 frozen invariants

**AXTEST 5.0 = FROZEN.**

---

# 197. Architectural Result

Sau AXTEST, Axiom có một verification chain hoàn chỉnh:

```text
                    AXTEST
                       │
 ┌─────────────────────┼──────────────────────┐
 │                     │                      │
SOURCE              TOOLCHAIN              RUNTIME
 │                     │                      │
 ▼                     ▼                      ▼
AXCOMPILER          AXOBJECT               AXRUNTIME
 │                     │                      │
 ▼                     ▼                   AXTASK
IR                    AXLINKER             AXASYNC
 │                     │
 ▼                     ▼
MACHINE CODE         AXBINARY
 │                     │
 ▼                     ▼
 ABI                 AXLOADER
 │                     │
 └──────────────┬──────┘
                ▼
            AXSTARTUP
                │
                ▼
           APPLICATION
                │
                ▼
             RESULT
                │
                ▼
             AXTEST
```

Điểm quan trọng nhất của thiết kế này là **AXTEST trở thành vòng phản hồi khép kín của compiler/toolchain/runtime**, chứ không phải một package assertion đơn giản.

---

# 198. Task tiếp theo

## BOOTSTRAP-783 — AXDOC

**Native Axiom Documentation, Language Reference, API Documentation, Specification Extraction, Source/ABI/IR Documentation, Cross-Linking, Generated Documentation, AI-Readable Semantic Index & Documentation Build Runtime 5.0**

Sau khi đã có:

```text
AXCOMPILER
AXTOOLCHAIN
AXLINKER
AXOBJECT
AXBINARY
AXLOADER
AXSTARTUP
AXABI
AXRUNTIME
AXSTANDARD
AXTEST
```

thì subsystem tiếp theo hợp lý là **AXDOC**: biến specification + source metadata + compiler semantic information + API metadata thành một hệ documentation có cấu trúc, đồng thời phục vụ compiler, IDE, AI agent và người lập trình.

**BOOTSTRAP-782 — AXTEST: FROZEN 5.0.**