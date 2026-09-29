# BOOTSTRAP-310 — AXIOM TESTING, VERIFICATION & COMPILER VALIDATION INFRASTRUCTURE

## 310.1. Mục tiêu

Xây dựng hệ thống kiểm thử và xác minh toàn bộ Axiom Compiler, từ parser đến machine code và executable.

Mục tiêu quan trọng nhất:

> **Không chỉ kiểm tra compiler có chạy hay không; phải kiểm tra compiler có biên dịch đúng ngữ nghĩa Axiom ở mọi tầng hay không.**

Hệ thống này phải phát hiện được:

- compiler sinh code sai;
- verifier cho phép chương trình không hợp lệ;
- optimizer làm thay đổi semantics;
- ownership/capability analysis sai;
- ABI sai;
- relocation/linking sai;
- machine encoder sinh byte sai;
- incremental compilation dùng artifact cũ sai;
- cross-target khác semantics;
- compiler bootstrap/self-host tạo regression;
- diagnostic thay đổi ngoài ý muốn;
- compiler crash/ICE.

---

# 310.2. Nguyên tắc thiết kế

### VTEST-01 — Semantic correctness là oracle tối cao

Test không được chỉ kiểm tra:

```text
compiler exits 0
```

mà phải kiểm tra:

```text
Source
  ↓
accepted/rejected
  ↓
semantic result
  ↓
IR
  ↓
machine code
  ↓
runtime behavior
```

Một chương trình chỉ được coi là pass khi toàn bộ tầng phù hợp đều đúng.

---

### VTEST-02 — Compiler test không phụ thuộc vào compiler implementation

Không viết test kiểu:

```text
expect AST node #17
```

nếu điều đó không phải semantic contract.

Có thể test implementation detail ở các test chuyên biệt, nhưng semantic test phải kiểm tra **observable contract**.

---

### VTEST-03 — Optimization không được thay đổi semantics

Cùng một chương trình:

```text
-O0
-O1
-O2
-O3
-Os
-Ofast
```

nếu cùng semantic profile thì phải có observable behavior tương đương.

Ngoại lệ chỉ khi source **explicitly** chọn semantics khác, ví dụ:

```text
fast_float
unchecked
target_intrinsic
unsafe
```

---

### VTEST-04 — Optimization phải có oracle

Mọi transformation quan trọng phải có:

```text
Precondition
Transformation
Proof/Analysis dependency
Postcondition
Test oracle
```

Không cho phép optimizer chỉ được test bằng benchmark.

---

# 310.3. Test Pyramid

Axiom sử dụng nhiều tầng:

```text
                  ┌─────────────────────┐
                  │ Self-host / Bootstrap│
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │ End-to-End Compiler │
                  └──────────┬──────────┘
                             │
             ┌───────────────┴───────────────┐
             │                               │
      ┌──────▼──────┐                 ┌──────▼──────┐
      │ Codegen/ABI │                 │ Runtime/FFI │
      └──────┬──────┘                 └──────┬──────┘
             │                               │
      ┌──────▼───────────────────────────────▼──────┐
      │          MIR / Verification Tests           │
      └────────────────────┬────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │ Semantic/Type/Trait     │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │ Parser/Resolver/AST     │
              └─────────────────────────┘
```

Không tầng nào được thay thế hoàn toàn bởi tầng khác.

---

# 310.4. Test Artifact Model

Mỗi test là một `TestCase`.

```text
TestCase {
    id
    category
    source
    auxiliary_files
    target
    profile
    expected
    oracle
    dependencies
    capabilities
    timeout
}
```

Test result:

```text
TestResult {
    test_id
    status
    diagnostics
    artifacts
    stdout
    stderr
    exit_code
    duration
    hashes
    environment
}
```

Status:

```text
PASS
FAIL
XFAIL
SKIP
TIMEOUT
CRASH
ICE
UNSUPPORTED
```

`XFAIL` phải có lý do và issue/spec reference.

Không cho phép biến test fail thành XFAIL mà không có metadata hợp lệ.

---

# 310.5. Test Categories

## 310.5.1. Parser tests

Kiểm tra:

- lexical grammar;
- UTF-8;
- identifiers;
- literals;
- operators;
- precedence;
- expressions;
- statements;
- declarations;
- generics;
- traits;
- pattern;
- attributes;
- `comptime`;
- `async`;
- `@kernel`;
- FFI declarations.

Bao gồm cả:

```text
valid syntax
invalid syntax
error recovery
ambiguous syntax
nested malformed syntax
Unicode edge cases
```

Parser test phải đảm bảo malformed input không làm compiler crash.

---

# 310.6. Compile-Fail Test Suite

Đây là một thành phần **bắt buộc**.

Ví dụ:

```text
fn test() {
    let x = 10
    drop(x)
    print(x)
}
```

Expected:

```text
AOWN...
use of moved value
```

Test không chỉ kiểm tra compile thất bại.

Nó phải kiểm tra:

- diagnostic code;
- primary span;
- relevant secondary spans;
- semantic explanation;
- expected suggestion nếu contract yêu cầu.

Ví dụ metadata:

```text
// expect-error: AOWN-USE-AFTER-MOVE
// span: x
```

Không nên hard-code toàn bộ human-readable message.

Message có thể cải thiện mà test vẫn hợp lệ.

---

# 310.7. Ownership Test Matrix

Phải có test tự động cho toàn bộ state transition:

```text
UNINIT
  ↓
INIT
  ↓
MOVED
  ↓
INVALID
```

và:

```text
Owned
PartiallyMoved
Dropped
```

Test các trường hợp:

- move;
- copy;
- clone;
- partial move;
- reinitialization;
- conditional initialization;
- loop;
- match;
- early return;
- panic;
- nested scopes;
- closure capture;
- async suspension;
- thread spawn;
- channel transfer;
- Drop;
- custom Drop;
- stable address.

Đặc biệt:

```text
if condition {
    move x
}

use x
```

phải được kiểm tra trên cả hai nhánh.

---

# 310.8. Capability / Alias Test Matrix

Phải kiểm tra:

```text
view
mut_view
```

với:

- overlapping regions;
- disjoint fields;
- nested fields;
- arrays;
- slices;
- dynamic indexing;
- unknown overlap;
- returned views;
- stored views;
- escaping views;
- relocation;
- reallocation;
- Drop;
- async;
- threads.

Ví dụ:

```text
let a = mut_view(x.a)
let b = mut_view(x.b)
```

được phép nếu compiler chứng minh:

```text
DISJOINT(a, b)
```

nhưng:

```text
let a = mut_view(x[i])
let b = mut_view(x[j])
```

không được giả định disjoint nếu không có proof.

---

# 310.9. Differential Verification

Các tầng IR phải có khả năng kiểm tra chéo.

Ví dụ:

```text
Typed MIR
    ↓
Verified MIR
    ↓
Optimized MIR
```

Có thể chạy:

```text
reference interpreter
```

trên MIR trước và sau optimization.

Nếu:

```text
run(reference MIR)
    !=
run(optimized MIR)
```

→ compiler bug.

Đây là một trong những cơ chế quan trọng nhất để bắt optimizer miscompile.

---

# 310.10. Axiom MIR Interpreter

Xây dựng:

```text
MIR Interpreter
```

không phải runtime production.

Mục đích:

- semantic oracle;
- constant/comptime testing;
- optimizer testing;
- debugging;
- differential testing;
- compiler bootstrap.

Interpreter phải hiểu các semantic operation quan trọng:

```text
load
store
move
copy
drop
view
mut_view
branch
switch
call
return
panic
atomic
allocation
deallocation
```

Không nhất thiết phải mô phỏng machine-level timing.

Nó phải mô phỏng **Axiom semantics**.

---

# 310.11. Property-Based Testing

Các thành phần như:

- parser;
- type checker;
- trait solver;
- ownership verifier;
- capability verifier;
- optimizer;
- encoder;
- object writer;
- linker

phải hỗ trợ property testing.

Ví dụ parser:

```text
parse(print(parse(source)))
```

phải giữ semantic structure tương đương.

Encoder:

```text
decode(encode(machine_instruction))
```

phải khôi phục instruction semantics.

Object:

```text
parse(write(object))
```

phải tương đương object IR.

Linker:

```text
link(objects)
```

phải deterministic.

---

# 310.12. Fuzzing Infrastructure

Compiler phải chịu được input tùy ý.

Các fuzz target chính:

```text
lexer
parser
parser-recovery
resolver
type-checker
trait-solver
comptime
MIR-lowering
ownership-verifier
capability-verifier
optimizer
machine-selector
encoder
object-parser
linker
executable-parser
AI-protocol
```

Invariant:

> **Arbitrary input may produce a diagnostic, but must not cause undefined compiler behavior or silent miscompile.**

Các kết quả đặc biệt:

```text
Crash
ICE
Timeout
OOM
Nontermination
Miscompile
```

được phân loại riêng.

---

# 310.13. Compiler Crash ≠ User Error

Compiler phải phân biệt:

```text
UserError
CompilerBug
UnsupportedFeature
InternalFailure
```

Ví dụ source sai:

```text
let x: UnknownType = ...
```

→ `UserError`.

Compiler gặp assertion nội bộ:

→ `CompilerBug / ICE`.

Không được biến ICE thành diagnostic thông thường để che lỗi compiler.

---

# 310.14. Golden Tests

Dùng cho các output cần ổn định:

```text
diagnostic JSON
HIR snapshots
MIR snapshots
optimized MIR
machine IR
assembly
object metadata
ABI metadata
```

Nhưng golden test phải có cơ chế:

```text
update expected
```

có kiểm soát.

Không tự động overwrite golden files khi test chạy.

---

# 310.15. Semantic Snapshot

Ngoài textual snapshot, cần:

```text
SemanticSnapshot
```

chứa:

```text
public API
types
traits
generic constraints
effects
ownership facts
ABI
layout
comptime dependencies
exports
```

Điều này đặc biệt quan trọng cho incremental compilation.

Nếu semantic snapshot không thay đổi, compiler phải có khả năng reuse artifact tương ứng.

---

# 310.16. Optimization Differential Testing

Mỗi optimization pass có thể chạy:

```text
source
 ↓
-O0 reference
 ↓
-OX candidate
```

sau đó so sánh:

```text
exit status
stdout
stderr
observable memory
result
```

với deterministic program.

Đối với nondeterministic/concurrent code, oracle phải sử dụng semantic equivalence phù hợp thay vì byte-for-byte output.

---

# 310.17. Compiler Metamorphic Testing

Một chương trình có thể được biến đổi theo semantics-preserving transformation:

```text
x + 0
```

thành:

```text
x
```

hoặc:

```text
let t = expr
use(t)
```

thành equivalent inline form.

Nếu hai chương trình có cùng semantics nhưng compiler tạo behavior khác:

```text
Compiler bug
```

Đây là cách rất hiệu quả để phát hiện optimizer bugs mà không cần biết trước output chính xác.

---

# 310.18. Codegen Testing

Mỗi target phải có:

```text
semantic test
ABI test
instruction-selection test
encoding test
relocation test
link test
executable test
```

Target matrix:

```text
x86_64-windows
x86_64-linux
x86_64-macos
aarch64-linux
aarch64-macos
aarch64-ios
aarch64-android
riscv64-linux
wasm32
```

Target nào chưa implementation hoàn chỉnh có thể `UNSUPPORTED`, nhưng không được silently skip.

---

# 310.19. ABI Test Suite

ABI tests phải kiểm tra:

- argument passing;
- return values;
- integer widths;
- float;
- structs;
- enums;
- aggregates;
- alignment;
- padding;
- variadic functions;
- calling convention;
- register classes;
- stack arguments;
- return-by-memory;
- TLS;
- dynamic imports;
- symbol visibility.

Đặc biệt phải có:

```text
Axiom ↔ Axiom
Axiom ↔ C
Axiom ↔ system ABI
Axiom ↔ foreign library
```

---

# 310.20. FFI Conformance Tests

Mỗi FFI boundary phải test:

```text
layout
calling convention
ownership
allocator
string encoding
error convention
threading
callback
opaque handles
async ABI
```

Không cho phép compiler tự đoán ownership của foreign API.

---

# 310.21. Runtime Test Matrix

Runtime component phải được test độc lập:

```text
allocator
panic
threads
TLS
async executor
I/O
Unicode
GPU runtime
reflection
```

Và các profile:

```text
freestanding
hosted
server
async
GPU
embedded
WASM
```

Phải có test chứng minh:

```text
runtime-free program
```

thực sự không kéo theo runtime component không cần thiết.

---

# 310.22. Concurrency Testing

Concurrency test cần:

- deterministic scheduler;
- randomized scheduler;
- race stress;
- atomic ordering tests;
- channel tests;
- mutex tests;
- cancellation;
- task migration;
- thread join;
- Send/Share verification.

Không dựa vào:

```text
"chạy 1000 lần không lỗi"
```

như một proof.

Phải có:

```text
controlled scheduler
```

để tái tạo interleaving.

Mỗi concurrency failure phải lưu:

```text
seed
schedule
thread/task events
memory events
```

để replay.

---

# 310.23. Async Testing

Kiểm tra:

```text
await
suspension
resume
cancellation
drop future
Send future
non-Send future
view across await
lock across await
recursive future
executor migration
```

Test state machine trước và sau optimization.

---

# 310.24. GPU Testing

GPU tests chia thành:

```text
compile legality
kernel IR
address-space legality
layout
host/device ABI
transfer
launch
synchronization
atomic
runtime
```

Có thể có:

```text
GPU emulator/reference interpreter
```

để differential test kernel.

CPU reference implementation:

```text
kernel CPU semantics
```

so với GPU execution.

---

# 310.25. Reproducible Build Testing

Cùng:

```text
source
compiler
target
profile
dependencies
comptime inputs
```

phải tạo:

```text
identical artifact
```

nếu build environment nằm trong reproducibility contract.

Test:

```text
build A
build B
binary_hash(A) == binary_hash(B)
```

Đối với metadata không deterministic, phải định nghĩa rõ field nào được phép khác.

---

# 310.26. Incremental Compilation Testing

Đây là phần cực kỳ quan trọng vì Axiom đã có incremental build.

Test pattern:

```text
Build 1
Modify source
Build 2
```

sau đó so sánh với:

```text
Clean Build
```

Kết quả phải semantic-equivalent:

```text
Incremental Build ≡ Clean Build
```

Test các thay đổi:

- private implementation;
- public function;
- public type;
- trait;
- generic;
- comptime;
- dependency;
- ABI;
- layout;
- generated declaration;
- target feature.

Nếu invalidation thiếu → **serious compiler bug**.

---

# 310.27. Cache Poisoning Tests

Cache phải không được reuse artifact sai.

Test:

```text
same source
different target
different ABI
different feature
different comptime input
different dependency
different compiler semantic version
different profile
```

phải tạo cache identity khác khi semantics yêu cầu.

---

# 310.28. Package/Dependency Tests

Kiểm tra:

- version resolution;
- lockfile;
- dependency DAG;
- cyclic package errors;
- feature unification;
- target-specific dependency;
- optional dependency;
- checksum;
- offline mode;
- vendoring;
- package interface;
- public API fingerprint;
- ABI compatibility.

---

# 310.29. AI Compiler Protocol Tests

Vì compiler có AI interface, protocol cũng phải được test như compiler API.

Test:

```text
get_diagnostics
get_symbol
get_type
get_signature
get_public_api
get_ownership
get_capabilities
get_effects
get_trait_candidates
get_dependency_graph
get_build_graph
explain
explain_optimization
explain_codegen
```

Phải đảm bảo:

- schema ổn định;
- ID ổn định trong snapshot;
- source span chính xác;
- không expose thông tin trái contract;
- không thể dùng AI protocol để bypass compiler verifier.

---

# 310.30. Bootstrap Testing

Khi Axiom compiler bắt đầu được viết bằng Axiom:

```text
Stage 0
External bootstrap compiler

Stage 1
Axiom compiler compiled by Stage 0

Stage 2
Stage 1 compiles itself

Stage 3
Stage 2 compiles Stage 2
```

Kiểm tra:

```text
Stage N output
    ==
Stage N+1 output
```

hoặc semantic-equivalent nếu bootstrap binary không deterministic hoàn toàn.

Mục tiêu cuối:

> **Axiom compiler có thể tự xây dựng chính nó mà không cần compiler bên ngoài.**

---

# 310.31. Translation Validation

Đối với optimizer/codegen, có thể áp dụng:

```text
Source/MIR semantics
        ↓
Transformation
        ↓
Validate transformed program
```

Thay vì tin tuyệt đối vào từng optimizer pass.

Đặc biệt hữu ích cho:

- aggressive optimization;
- vectorization;
- instruction selection;
- lowering;
- peephole optimization.

---

# 310.32. Formal Invariant Registry

Tất cả invariant của compiler phải có ID.

Ví dụ:

```text
AOWN-20  moved value cannot be read
ACAP-31  unknown overlap is not disjoint
ADROP-24 exactly-once cleanup
AASYNC-27 view cannot cross suspension without contract
AGPU-30 host capability cannot implicitly enter device domain
AOPT-41 transformation requires valid alias proof
AENC-33 encoded instruction must satisfy target encoding constraints
AOBJ-40 relocation must resolve against compatible symbol
ALINK-44 relocation overflow must be diagnosed
```

Mỗi invariant phải map tới:

```text
spec
implementation
unit tests
integration tests
fuzz target
```

Không để invariant chỉ tồn tại trong tài liệu.

---

# 310.33. Test Registry

Compiler có một:

```text
TestDB
```

chứa:

```text
TestId
TestCategory
SourceFiles
Target
Profile
ExpectedDiagnostics
ExpectedSemanticResult
ExpectedArtifact
Oracle
Dependencies
```

Test runner query-based:

```text
run_tests(category)
run_tests(target)
run_tests(changed_components)
run_tests(failed)
run_tests(invariant)
```

---

# 310.34. Test Selection

Incremental test execution:

```text
changed compiler component
        ↓
dependency graph
        ↓
affected tests
        ↓
run minimal relevant subset
```

Nhưng CI đầy đủ vẫn có:

```text
full suite
```

định kỳ.

Ví dụ:

```text
changed trait solver
→ trait tests
→ type tests
→ generic tests
→ ownership tests affected by type facts
→ optimizer tests depending on type specialization
```

---

# 310.35. Failure Artifact

Mỗi failure phải tự động lưu:

```text
source
compiler version
target
profile
command
diagnostics
IR snapshots
machine IR
assembly
object
link map
runtime output
seed
environment
cache state
```

để bug có thể replay.

Đặc biệt:

```text
fuzz failure
```

phải được biến thành regression test tự động.

---

# 310.36. Compiler Determinism Test

Compiler phải được chạy nhiều lần:

```text
same input
same environment
```

và kiểm tra:

```text
diagnostics
IR
object
binary
metadata
```

Không được có nondeterminism vô tình do:

- HashMap iteration;
- parallel scheduling;
- thread race;
- random IDs;
- filesystem order;
- dependency traversal order.

Nếu cần randomization để fuzz/test thì seed phải explicit.

---

# 310.37. Performance Regression Tests

Không chỉ correctness.

Theo dõi:

```text
compile time
peak memory
binary size
runtime performance
allocation count
IR size
code size
```

Nhưng performance test **không được trở thành semantic oracle**.

Benchmark regression có threshold và tolerance.

---

# 310.38. Compiler Resource Limits

Test:

```text
huge source
deep recursion
generic explosion
trait recursion
comptime recursion
large enum
large struct
huge match
many modules
many dependencies
```

Compiler phải:

- terminate;
- emit controlled diagnostic;
- không stack overflow ngoài kiểm soát;
- không vô hạn trait solving;
- không infinite compile-time execution.

---

# 310.39. Security-Oriented Compiler Tests

Kiểm tra:

- malformed object;
- malformed dependency;
- malformed package metadata;
- malicious comptime input;
- unsafe FFI declarations;
- invalid relocations;
- integer overflow;
- path traversal;
- cache poisoning;
- corrupted lockfile;
- corrupted compiler cache.

Compiler phải fail closed khi không chứng minh được tính hợp lệ.

---

# 310.40. CI Pipeline

Pipeline chuẩn:

```text
Lint
 ↓
Unit Tests
 ↓
Parser/Semantic Tests
 ↓
Compile-Fail Tests
 ↓
MIR Verification
 ↓
Optimization Differential Tests
 ↓
Codegen Tests
 ↓
Object/Link Tests
 ↓
Runtime Tests
 ↓
Cross Target
 ↓
Fuzz Smoke
 ↓
Reproducibility
 ↓
Incremental Build
 ↓
Bootstrap
```

Các tầng nặng như fuzz/full cross-target có thể chạy nightly, nhưng semantic core phải chạy mỗi commit.

---

# 310.41. Compiler Validation Modes

Axiom compiler cung cấp:

```text
axiom test
axiom test --compile-fail
axiom test --fuzz
axiom test --property
axiom test --differential
axiom test --target
axiom test --incremental
axiom test --reproducible
axiom test --bootstrap
axiom test --invariant AOWN-20
```

Và:

```text
axiom test --changed
```

để chạy test bị ảnh hưởng bởi thay đổi.

---

# 310.42. Verification Levels

Có thể bật các mức:

```text
Fast
Standard
Strict
Exhaustive
```

### Fast

- unit;
- semantic;
- compile-fail;
- basic codegen.

### Standard

+ differential;
+ ABI;
+ incremental;
+ runtime.

### Strict

+ sanitizer;
+ deterministic;
+ cross-target;
+ extensive verification.

### Exhaustive

+ fuzz;
+ property;
+ randomized scheduler;
+ bootstrap;
+ translation validation.

Semantics không thay đổi giữa các mode.

---

# 310.43. Test Oracle Hierarchy

Ưu tiên:

```text
1. Formal semantic invariant
2. Reference interpreter
3. Differential execution
4. ABI specification
5. Target architecture specification
6. Golden artifact
7. Expected textual output
```

Không lấy output của chính compiler hiện tại làm oracle duy nhất.

---

# 310.44. Definition of Done

BOOTSTRAP-310 chỉ hoàn thành khi:

- parser có unit + fuzz tests;
- semantic compiler có compile-pass/compile-fail tests;
- ownership/capability verifier có invariant tests;
- MIR có reference interpreter;
- optimizer có differential validation;
- machine encoder có encode/decode tests;
- object writer có roundtrip tests;
- linker có deterministic/conformance tests;
- executable writer có parser roundtrip tests;
- ABI/FFI có conformance tests;
- runtime components có independent tests;
- async/concurrency có deterministic replay;
- GPU có reference validation;
- comptime có sandbox/reproducibility tests;
- incremental build có clean-vs-incremental equivalence tests;
- cache có poisoning tests;
- package manager có resolution tests;
- AI compiler protocol có schema tests;
- fuzz failures tự động trở thành regression tests;
- compiler có deterministic build tests;
- bootstrap compiler có self-build tests;
- invariant registry liên kết được với automated tests;
- mọi compiler crash đều có phân loại và reproduction artifact;
- CI có fast/standard/nightly validation tiers.

---

# 310.45. Kiến trúc thư mục

```text
tests/
├── unit/
│   ├── lexer/
│   ├── parser/
│   ├── resolver/
│   ├── types/
│   ├── traits/
│   ├── ownership/
│   ├── capability/
│   ├── effects/
│   ├── async/
│   ├── concurrency/
│   ├── comptime/
│   └── gpu/
│
├── compile_pass/
├── compile_fail/
├── semantic/
├── mir/
├── optimizer/
├── codegen/
├── abi/
├── ffi/
├── object/
├── linker/
├── runtime/
├── async/
├── concurrency/
├── gpu/
├── incremental/
├── packages/
├── ai_protocol/
├── bootstrap/
│
├── differential/
├── property/
├── fuzz/
├── regression/
├── golden/
└── fixtures/
```

Compiler infrastructure:

```text
compiler/testing/
├── test_db/
├── test_runner/
├── oracle/
├── mir_interpreter/
├── differential/
├── property/
├── fuzz/
├── replay/
├── snapshots/
├── bootstrap/
├── reproducibility/
└── reporting/
```

---

# 310.46. Invariants chính

### `ATEST-20`
Every accepted semantic program must pass all required semantic verification stages.

### `ATEST-21`
Every rejected program must produce a structured diagnostic or classified compiler failure.

### `ATEST-22`
Compiler crash must never be classified as a normal user error.

### `ATEST-23`
Optimization must preserve observable semantics.

### `ATEST-24`
Unknown aliasing must never be treated as proven independence.

### `ATEST-25`
Incremental compilation must be semantically equivalent to clean compilation.

### `ATEST-26`
Cache reuse requires a valid complete cache identity.

### `ATEST-27`
Same deterministic build inputs must produce deterministic artifacts.

### `ATEST-28`
Every fuzz-discovered compiler failure must be reproducible from stored input and seed.

### `ATEST-29`
Every machine encoding must satisfy the target instruction encoding contract.

### `ATEST-30`
Every object relocation must satisfy its relocation contract.

### `ATEST-31`
Every linked image must pass image verification before publication.

### `ATEST-32`
Reference interpreter semantics must follow Axiom language semantics, not optimized implementation behavior.

### `ATEST-33`
Test infrastructure must not silently weaken compiler verification.

### `ATEST-34`
Bootstrap compiler output must remain semantically equivalent across bootstrap stages.

### `ATEST-35`
Test results must be reproducible from recorded inputs.

### `ATEST-36`
Concurrency failures must record enough scheduling information for deterministic replay.

### `ATEST-37`
Compile-fail tests must validate diagnostic identity and semantic location, not fragile human wording.

### `ATEST-38`
Performance regressions must not be used as semantic correctness proof.

### `ATEST-39`
External tools may act as test oracles during bootstrap, but cannot become mandatory compiler dependencies.

### `ATEST-40`
The final self-hosted compiler must be capable of validating itself using the same testing architecture.

---

## Kết quả kiến trúc

Sau BOOTSTRAP-310, Axiom không còn chỉ có một **compiler pipeline**, mà đã có một **compiler validation pipeline** song song:

```text
                 AXIOM COMPILER
                       │
                       ▼
                  Verified MIR
                       │
                       ▼
                    Codegen
                       │
                       ▼
                  Native Image
                       │
                       ▼
                 ┌─────────────┐
                 │   TESTING   │
                 │ VALIDATION  │
                 └──────┬──────┘
                        │
       ┌────────────────┼─────────────────┐
       ▼                ▼                 ▼
 Semantic Oracle   Differential       Target Oracle
       │                │                 │
       ▼                ▼                 ▼
  MIR Interpreter   Optimizer        ABI/Encoder
       │             Validation         Validation
       └────────────────┼─────────────────┘
                        ▼
                  Regression DB
                        │
                        ▼
                 Bootstrap / CI
```

**Điểm quan trọng:** từ đây trở đi, các subsystem mới của Axiom không nên chỉ có `implementation + spec`, mà phải có **semantic contract + verifier + oracle + automated validation** ngay từ đầu.