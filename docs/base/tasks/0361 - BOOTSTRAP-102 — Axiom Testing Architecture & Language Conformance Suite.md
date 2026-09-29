# BOOTSTRAP-102 — Axiom Testing Architecture & Language Conformance Suite

**Trạng thái: FROZEN**

Đây là một mốc quan trọng. Với Axiom, **test không chỉ để bắt bug compiler** mà phải trở thành cơ chế chứng minh compiler đang thực hiện đúng specification.

Nguyên tắc:

> **Specification → Conformance Test → Compiler → Artifact → Verification**

Compiler nào vượt qua cùng một conformance suite thì phải có cùng **observable semantics**, bất kể compiler được viết bằng C++, Rust hay chính Axiom.

---

# 1. Tách 3 loại "đúng"

Axiom cần phân biệt:

### Semantic correctness

```text
Source
→
được hiểu đúng theo language specification
```

### Compiler correctness

```text
Semantic IR
→
machine code
```

phải giữ nguyên observable behavior.

### Toolchain correctness

```text
Compiler
→
Object
→
Linker
→
Executable
```

phải tạo artifact hợp lệ cho target.

Vì vậy:

```text
Language correctness
≠
Compiler correctness
≠
Linker correctness
```

---

# 2. Conformance là tầng cao nhất

Ta định nghĩa:

```text
Axiom Conformance
```

là:

> Một implementation conformant nếu mọi behavior thuộc specification mà implementation tuyên bố hỗ trợ đều thỏa các semantic invariants tương ứng.

Không yêu cầu:

- cùng IR
- cùng optimizer
- cùng register allocator
- cùng layout nếu layout không được contract
- cùng binary bytes.

Chỉ yêu cầu observable semantics.

---

# 3. Test hierarchy

Cấu trúc:

```text
tests/
├── lexer/
├── parser/
├── resolver/
├── types/
├── traits/
├── ownership/
├── capabilities/
├── drop/
├── control/
├── concurrency/
├── async/
├── comptime/
├── gpu/
├── ffi/
├── layout/
├── abi/
├── mir/
├── optimization/
├── codegen/
├── object/
├── linker/
├── runtime/
├── diagnostics/
├── cross-target/
├── reproducibility/
├── fuzz/
└── bootstrap/
```

---

# 4. Compile-pass và compile-fail

Hai loại test nền tảng:

```text
pass
fail
```

Ví dụ:

```text
tests/ownership/use_after_move.ax
```

expected:

```text
compile_fail
EOWN_USE_AFTER_MOVE
```

Không được chỉ kiểm tra:

```text
compiler returned non-zero
```

vì compiler có thể fail vì lý do hoàn toàn khác.

---

# 5. Compile-fail test phải kiểm tra semantic code

Ví dụ:

```axiom
let a = String.from("hello");
let b = a;
print(a);
```

Test:

```text
expected:
    EOWN_USE_AFTER_MOVE
```

có thể thêm:

```text
primary_span
cause_span
```

để bảo đảm compiler phát hiện **đúng lỗi**.

---

# 6. Diagnostic tests

Dùng schema đã định nghĩa ở BOOTSTRAP-101:

```text
expected:
    code
    primary span
    secondary spans
    semantic facts
```

Text snapshot chỉ là supplementary.

Ví dụ:

```text
expect diagnostic.code == EOWN_USE_AFTER_MOVE
expect diagnostic.primary.span == line 3
```

---

# 7. Semantic test metadata

Mỗi test nên có metadata:

```text
test {
    category: ownership
    status: compile_fail
    target: any
    diagnostic: EOWN_USE_AFTER_MOVE
}
```

Hoặc metadata nằm trong test manifest.

Mục đích là test runner không phải đoán.

---

# 8. Execution tests

Pass compile chưa đủ.

Ví dụ:

```axiom
fn main() -> i32 {
    2 + 3
}
```

expected:

```text
exit_code = 5
```

Test runner:

```text
compile
→ link
→ execute
→ capture exit code/stdout/stderr
→ compare
```

---

# 9. Observable behavior

Conformance test chỉ được dựa vào behavior mà specification định nghĩa.

Ví dụ struct layout mặc định:

```axiom
struct A {
    x: u8,
    y: u64,
}
```

không được test:

```text
sizeof(A) == 16
```

nếu layout không có contract.

Nhưng:

```axiom
@repr(C)
struct A {
    x: u8,
    y: u64,
}
```

thì có thể test layout theo C ABI contract.

---

# 10. Undefined/unspecified behavior

Test suite phải biết ba loại:

```text
Defined
Implementation-defined
Unspecified
```

và không test behavior nằm ngoài contract.

Axiom nên giảm unspecified behavior tối đa trong Core.

Ví dụ:

- evaluation order → defined
- integer overflow → defined
- HashMap iteration order → unspecified
- default struct layout → compiler-controlled
- floating NaN payload → không nên yêu cầu bit pattern cụ thể.

---

# 11. Property tests

Một số semantics tốt hơn nếu test bằng property.

Ví dụ:

```text
Copy(x)
```

phải giữ:

```text
semantic value equality
```

và:

```text
Move(x)
```

không tạo thêm ownership.

---

# 12. Arithmetic property tests

Với integer:

```text
checked_add
wrapping_add
saturating_add
```

có properties riêng.

Ví dụ:

```text
wrapping_add(a,b)
```

phải tương đương modulo 2^N.

Trong khi ordinary arithmetic phải giữ overflow semantics đã frozen.

---

# 13. Ownership property tests

Có thể generate các CFG nhỏ:

```text
create
move
copy
drop
return
branch
loop
```

và kiểm tra invariant:

```text
no use-after-move
no double-drop
no drop-after-move
```

Đây là nơi fuzzing rất mạnh.

---

# 14. Capability property tests

Generate:

```text
view
mut_view
split
move
drop
relocate
```

và kiểm tra:

```text
WRITE + WRITE → reject
READ + WRITE → reject
READ + READ → allow
DISJOINT WRITE + WRITE → allow
UNKNOWN overlap → reject
```

Đây chính là executable form của:

```text
ACAP-...
```

---

# 15. Drop tests

Ví dụ resource:

```axiom
struct Tracker { ... }
```

với Drop counter.

Test:

```text
normal return
early return
break
continue
panic
partial move
branch merge
```

Expected:

```text
exactly once
```

cho mỗi live owned value.

---

# 16. Drop order

Axiom đã frozen:

> reverse declaration/initialization order.

Test:

```axiom
let a = Tracker("a");
let b = Tracker("b");
let c = Tracker("c");
```

expected semantic cleanup:

```text
c
b
a
```

Nhưng test không được phụ thuộc implementation-specific physical destruction machinery.

---

# 17. Panic tests

Profiles:

```text
panic=abort
panic=unwind
```

phải có test riêng.

### Abort

```text
panic
→ process terminates
```

### Unwind

```text
panic
→ cleanup initialized owned values
→ unwind
```

Không được yêu cầu unwind runtime khi profile không dùng.

---

# 18. Optimization correctness

Đây là một trong những test quan trọng nhất.

Compiler có:

```text
-O0
-O1
-O2
-O3
-LTO
-PGO
```

nhưng:

```text
observable behavior
```

phải tương đương nếu cùng semantic profile.

Test:

```text
program
→ build O0
→ build O3
→ execute
→ compare observable result
```

---

# 19. Differential optimization testing

Ví dụ:

```text
-O0 output
vs
-O3 output
```

So sánh:

```text
exit code
stdout
stderr
files intentionally produced
defined external effects
```

Không so sánh binary bytes.

---

# 20. MIR interpreter

Axiom nên có **MIR interpreter/reference executor** tương đối đơn giản.

Pipeline test:

```text
Source
 ↓
Verified MIR
 ↓
MIR Interpreter
 ↓
expected behavior
```

và:

```text
Verified MIR
 ↓
Codegen
 ↓
Native executable
 ↓
actual behavior
```

So sánh hai kết quả.

Đây là nền tảng cực mạnh để kiểm tra backend.

---

# 21. Reference interpreter

MIR interpreter không cần nhanh.

Mục tiêu:

> **Đơn giản, dễ audit, semantics rõ ràng.**

Nó có thể là "executable specification" của Axiom.

Ví dụ:

```text
MIR interpreter
```

phải hiểu:

- values
- ownership
- drop
- capabilities
- control flow
- panic
- Result/Option
- atomic abstract semantics ở mức phù hợp
- comptime subset.

---

# 22. Backend differential testing

Một source:

```text
test.ax
```

có thể compile:

```text
x86-64
AArch64
RISC-V
WASM
```

nếu semantics target-independent.

Expected behavior phải tương đương.

Target-specific behavior được đánh dấu riêng.

---

# 23. Cross-target matrix

Ví dụ:

| Feature | x86-64 | ARM64 | RISC-V | WASM |
|---|---:|---:|---:|---:|
| integer | ✓ | ✓ | ✓ | ✓ |
| float | ✓ | ✓ | ✓ | ✓ |
| ownership | ✓ | ✓ | ✓ | ✓ |
| SIMD | ✓ | ✓ | ✓* | ✓* |
| TLS | ✓ | ✓ | ✓ | profile |
| threads | ✓ | ✓ | ✓ | profile |
| GPU | target-specific | target-specific | target-specific | target-specific |

`*` tùy target feature.

---

# 24. ABI tests

C ABI cần test thật.

Ví dụ:

```text
Axiom
  ↓
@repr(C)
  ↓
C function
```

và ngược lại:

```text
C
 ↓
Axiom extern
```

Test:

- argument passing
- return
- struct layout
- alignment
- enum representation khi contracted
- strings
- callbacks
- ownership
- symbol naming
- TLS
- calling convention.

---

# 25. FFI ownership tests

Ví dụ:

```text
foreign_alloc()
```

phải xác định:

```text
OwnedByForeign
```

Không được compiler tự assume:

```text
OwnedByAxiom
```

Test phải cố tình tạo mismatch để bảo đảm compiler/API wrapper không suy diễn ownership.

---

# 26. Layout tests

Test ba tầng:

### Semantic

Field identity đúng.

### Contracted representation

`@repr(C)` đúng.

### Backend

Machine layout hợp lệ.

Không test default layout bằng hard-coded offset.

---

# 27. Generic tests

Cần test:

```text
Vec<i32>
Vec<f32>
Vec<u64>
Vec<MyStruct>
Vec<LargeType>
```

và:

```text
monomorphization
sharing
deduplication
specialization
LTO
incremental cache
```

Nhưng:

> code sharing là optimization, không phải semantic requirement.

Test chỉ cần xác nhận output đúng.

---

# 28. Binary-size tests

Không nên đặt:

```text
binary must always be <= X bytes
```

vì target/compiler evolution sẽ phá test.

Thay vào đó test invariants:

```text
unused runtime component absent
unused function absent
unused generic instance absent
```

Ví dụ:

```bash
axiom build --explain-runtime
```

expected:

```text
thread: not required
async: not required
gpu: not required
```

---

# 29. Runtime elimination tests

Test cực kỳ quan trọng:

```axiom
fn main() {
    let x = Box.new(42);
    print(*x);
}
```

Nếu optimization loại allocation:

```text
allocator capability
```

có thể không còn trong final runtime closure.

Test runtime graph:

```text
assert allocator not required
```

nhưng chỉ trong compiler/profile cho phép elimination.

---

# 30. Async tests

Test:

```text
async fn
await
Future
Poll
Pending
Ready
spawn
spawn_local
Send
cancellation
drop Future
```

Đặc biệt:

```text
view across await
```

phải reject nếu capability không hợp lệ.

---

# 31. Concurrency tests

Không nên chỉ test bằng một execution order.

Có:

```text
deterministic scheduler
stress scheduler
random scheduler
```

Test properties:

```text
no safe data race
channel ownership preserved
mutex guard exclusivity
atomic ordering
join synchronization
```

---

# 32. Memory model tests

Có thể dùng litmus tests:

```text
Store Release
Load Acquire
```

và:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Expected outcomes dựa trên Axiom memory model.

Đây là nơi cần một **memory-model test engine**, không chỉ unit test thông thường.

---

# 33. GPU conformance

GPU test chia:

```text
semantic front-end
GPU legality
GPU lowering
host/device ABI
actual device execution
```

Không phải mọi CI machine đều có GPU.

Vì vậy:

```text
compile-only
simulator
reference backend
real GPU
```

là các tầng khác nhau.

---

# 34. Comptime tests

Phải test:

```text
const
comptime
comptime fn
reflection
generated declarations
capability restrictions
cache
reproducibility
```

Đặc biệt:

```text
comptime output
```

phải giống nhau khi build reproducibly.

---

# 35. Comptime sandbox tests

Ví dụ code không được cấp Network:

```text
comptime network.fetch()
```

phải luôn:

```text
ECOMPTIME_CAPABILITY
```

Không phụ thuộc OS.

---

# 36. Reproducibility tests

Build hai lần:

```text
build A
build B
```

với cùng:

```text
source
dependencies
compiler
target
config
comptime inputs
```

expected:

```text
same artifact identity
```

Có thể kiểm tra content hash.

---

# 37. Cache correctness

Đây là test cực quan trọng.

### Change private implementation

Expected:

```text
consumer semantic cache remains valid
```

nếu public semantic fingerprint không đổi.

### Change public API

Expected:

```text
dependent cache invalidated
```

---

# 38. Cache poisoning tests

Cố tình sửa:

```text
cache entry
```

hoặc metadata:

```text
.axmeta
```

Compiler phải phát hiện:

```text
invalid cache
```

Không được dùng artifact không còn matching fingerprint.

---

# 39. Module/name-resolution tests

Test:

```text
import
alias
re-export
visibility
private
ambiguous names
extension methods
trait methods
@cfg
generated declarations
```

Ví dụ:

```text
import A::foo;
import B::foo;
foo();
```

phải:

```text
ERESOLVE_AMBIGUOUS
```

không có last-import-wins.

---

# 40. Parser fuzzing

Axiom nên có grammar-aware fuzzing:

```text
random tokens
random AST
random malformed source
```

Invariant:

```text
compiler never crashes
```

trừ lỗi resource exhaustion được hệ thống xác định riêng.

ICE có thể xảy ra trong giai đoạn bootstrap, nhưng conformance goal cuối cùng là:

> malformed user source không được làm compiler crash.

---

# 41. AST fuzzing

Tạo AST hợp lệ trực tiếp:

```text
AST
→ resolver
→ type checker
→ MIR
```

Mục tiêu tìm bugs giữa parser và semantic phases.

---

# 42. MIR fuzzing

Sinh MIR hợp lệ:

```text
MIR
→ verifier
→ optimizer
```

Kiểm tra:

```text
optimizer preserves semantics
```

Sinh MIR không hợp lệ:

```text
invalid MIR
→ verifier rejects
```

Không được crash.

---

# 43. Mutation testing

Một kỹ thuật rất hữu ích cho Axiom spec.

Compiler/test suite cố tình thay:

```text
ownership rule
drop order
capability conflict
numeric conversion
```

Nếu test suite vẫn pass:

> test coverage chưa đủ.

Điều này giúp phát hiện những invariant chưa được executable hóa.

---

# 44. Specification-linked tests

Đây là điểm tôi đặc biệt đề xuất.

Mỗi frozen invariant có test mapping:

```text
ACAP-67
    ↓
tests/capability/write_write_conflict.ax
```

Ví dụ:

```text
AINIT-29
    ↓
tests/initialization/no_global_constructor.ax

ARUNTIME-28
    ↓
tests/runtime/unused_component_elimination.ax

AMOD-27
    ↓
tests/modules/ambiguous_import.ax
```

Ta có thể tạo:

```text
axiom conformance coverage
```

để biết invariant nào chưa có test.

---

# 45. Conformance matrix

Compiler report:

```text
Axiom Conformance

Ownership          184/184
Capabilities       143/143
Async               97/97
Comptime             88/88
FFI                  76/76
ABI                  91/91
Runtime              64/64
Diagnostics          121/121
```

Nhưng không nên dùng một "điểm số" duy nhất làm đánh giá compiler.

Quan trọng là **test/invariant nào pass/fail**.

---

# 46. Versioned conformance

Axiom version:

```text
language_version
semantic_revision
target_profile
```

phải là một phần test environment.

Không thể nói:

```text
compiler conforms to Axiom
```

mà không nói:

```text
Axiom semantic version
```

---

# 47. Core vs optional features

Conformance chia:

```text
Core
Optional
Target-specific
Experimental
```

Ví dụ:

```text
Core:
    ownership
    types
    control flow

Optional:
    GPU
    async runtime

Target-specific:
    @interrupt
    system ABI
```

Compiler có thể claim:

```text
Core Conformant
GPU Not Implemented
```

thay vì pass/fail toàn bộ một cách mơ hồ.

---

# 48. Bootstrap conformance

Khi compiler được viết lại bằng Axiom:

```text
Stage 0 compiler
        ↓
compile
        ↓
Stage 1 Axiom compiler
```

hai compiler phải chạy cùng conformance suite.

Sau đó:

```text
Stage 1
 ↓ compile
Stage 2
```

và so sánh.

---

# 49. Self-host equivalence

Không yêu cầu binary compiler giống nhau.

Yêu cầu:

```text
same source
same target
same semantics
```

→ cùng observable behavior.

Có thể thêm:

```text
compiler build reproducibility
```

nhưng đó là property khác.

---

# 50. Compiler bootstrap fixed point

Một test rất mạnh:

```text
C0
 ↓ compile compiler.ax
C1

C1
 ↓ compile compiler.ax
C2

C2
 ↓ compile compiler.ax
C3
```

Sau một số stage:

```text
C2 semantic behavior == C3 semantic behavior
```

và artifact hash có thể hội tụ nếu reproducibility contract đủ mạnh.

---

# 51. Compiler regression suite

Mỗi bug đã sửa phải tạo:

```text
regression test
```

Không chấp nhận:

```text
bug fixed
```

mà không có test nếu bug có thể tái hiện.

---

# 52. Test runner architecture

CLI:

```bash
axiom test
axiom test --filter ownership
axiom test --target x86_64-linux
axiom test --compile-fail
axiom test --conformance
axiom test --fuzz
axiom test --reproducible
```

Machine output:

```bash
axiom test --format=json
```

phù hợp AI agent.

---

# 53. Test artifacts

Mỗi test có thể sinh:

```text
source
AST
HIR
MIR
diagnostics
runtime graph
object
binary
execution result
```

nhưng chỉ lưu những artifact được yêu cầu.

Ví dụ:

```bash
axiom test --emit-on-failure
```

---

# 54. Golden tests

Dùng cho:

- AST canonical form
- HIR
- MIR
- diagnostics
- runtime graph
- ABI representation
- compiler explanations.

Nhưng phải phân biệt:

```text
semantic golden
```

và:

```text
implementation golden
```

Implementation golden dễ thay đổi khi optimizer/backend cải tiến.

---

# 55. Semantic snapshots

Ví dụ MIR:

```text
semantic snapshot
```

nên canonicalize:

- IDs
- temporary names
- block ordering khi không semantic
- target-independent representation.

Nếu không, refactor compiler sẽ tạo hàng nghìn snapshot noise.

---

# 56. Performance tests

Performance suite riêng:

```text
compile-time
runtime
binary size
memory
codegen
incremental build
```

Không đưa benchmark vào conformance.

Một compiler chậm vẫn có thể conform.

Một compiler nhanh nhưng sai semantics không conform.

---

# 57. Compiler resource limits

Fuzzing/test runner phải kiểm soát:

```text
CPU
RAM
recursion depth
comptime execution
generated code size
diagnostic count
```

Comptime đặc biệt cần giới hạn để tránh:

```text
comptime infinite loop
```

làm compiler treo vô hạn.

---

# 58. Differential testing với compiler khác

Có thể dùng:

```text
C
Rust
Zig
LLVM IR
```

làm **oracle phụ** trong các feature tương đương.

Nhưng:

> Chúng không phải specification của Axiom.

Ví dụ integer semantics khác nhau thì không được ép Axiom giống C chỉ vì C là reference.

---

# 59. Randomized testing

Compiler test seed phải được ghi lại:

```text
seed = 0x...
```

Nếu failure:

```text
replay seed
```

để AI/compiler developer tái hiện.

---

# 60. Test failure machine record

Ví dụ:

```text
TestFailure {
    test_id
    compiler_version
    source_hash
    target
    profile
    seed
    stage
    diagnostic
    artifact_hashes
}
```

AI agent có thể trực tiếp nhận object này.

---

# 61. Axiom Conformance Manifest

Mỗi compiler build có thể khai báo:

```text
axiom-conformance.json
```

Ví dụ:

```text
language_semantic_version
compiler_version
target_support
features
passed_invariants
known_failures
```

Không dùng để "tự tuyên bố compliant"; test runner phải tạo kết quả độc lập.

---

# 62. Một nguyên tắc quan trọng

**Không test implementation detail nếu specification không yêu cầu.**

Ví dụ không nên test:

```text
"compiler must use SSA"
```

SSA chỉ là implementation architecture.

Nên test:

```text
"optimized code preserves semantics"
```

Tương tự:

```text
linear scan
graph coloring
LLVM
custom backend
```

đều không phải conformance requirement.

---

# 63. Test pipeline tổng thể

```text
                 Axiom Specification
                         │
                         ▼
                 Semantic Invariants
                         │
                         ▼
                 Conformance Tests
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Compile Pass   Compile Fail    Property/Fuzz
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Verified MIR
                         │
                 ┌───────┴───────┐
                 ▼               ▼
           MIR Interpreter    Native Code
                 │               │
                 └───────┬───────┘
                         ▼
                  Observable Result
                         │
                         ▼
                    Conformance
```

---

# 64. Frozen invariants

**ATEST-20** — Conformance Is Defined By Observable Semantics  
**ATEST-21** — Semantic Correctness Is Distinct From Compiler Implementation  
**ATEST-22** — Compiler Correctness Is Distinct From Toolchain Correctness  
**ATEST-23** — Conformance Is Versioned By Language Semantic Version  
**ATEST-24** — Core And Optional Features Have Separate Conformance Domains  
**ATEST-25** — Compile-Pass Tests Verify Successful Compilation  
**ATEST-26** — Compile-Fail Tests Verify Expected Semantic Failure  
**ATEST-27** — Compile-Fail Tests Must Validate Diagnostic Identity  
**ATEST-28** — Diagnostic Tests Use Structured Diagnostic Data  
**ATEST-29** — Text Diagnostic Snapshots Are Supplementary  
**ATEST-30** — Execution Tests Verify Observable Program Behavior  
**ATEST-31** — Tests Must Not Depend On Unspecified Behavior  
**ATEST-32** — Tests Must Not Depend On Uncontracted Representation  
**ATEST-33** — Property Tests May Verify Semantic Invariants  
**ATEST-34** — Ownership Invariants Must Be Executably Tested  
**ATEST-35** — Capability Invariants Must Be Executably Tested  
**ATEST-36** — Drop Invariants Must Be Executably Tested  
**ATEST-37** — Concurrency Invariants Must Be Executably Tested  
**ATEST-38** — Async Invariants Must Be Executably Tested  
**ATEST-39** — Comptime Invariants Must Be Executably Tested  
**ATEST-40** — GPU Invariants Must Be Executably Tested  
**ATEST-41** — FFI Invariants Must Be Executably Tested  
**ATEST-42** — ABI Contracts Must Be Tested Independently  
**ATEST-43** — Layout Contracts Must Be Tested Only When Contracted  
**ATEST-44** — Optimization Must Preserve Observable Semantics  
**ATEST-45** — Optimization Levels Must Preserve Semantics  
**ATEST-46** — MIR May Serve As A Reference Execution Representation  
**ATEST-47** — Reference Execution Must Remain Semantically Simple  
**ATEST-48** — Native Code May Be Differentially Tested Against MIR  
**ATEST-49** — Cross-Target Tests Must Compare Only Portable Semantics  
**ATEST-50** — Target-Specific Semantics Must Have Target-Specific Tests  
**ATEST-51** — Runtime Elimination Must Be Testable  
**ATEST-52** — Unused Runtime Components Must Be Detectably Absent  
**ATEST-53** — Generic Specialization Must Preserve Semantics  
**ATEST-54** — Generic Code Sharing Is An Optimization Property  
**ATEST-55** — Binary Size Tests Must Prefer Structural Invariants  
**ATEST-56** — Incremental Compilation Must Be Tested  
**ATEST-57** — Semantic Fingerprint Invalidation Must Be Tested  
**ATEST-58** — Cache Reuse Must Be Validated  
**ATEST-59** — Cache Corruption Must Not Produce Valid Artifacts  
**ATEST-60** — Reproducible Builds Must Be Testable  
**ATEST-61** — Comptime Reproducibility Must Be Testable  
**ATEST-62** — Module Resolution Must Be Tested Independently  
**ATEST-63** — Name Resolution Must Be Tested Against Semantic IDs  
**ATEST-64** — Parser Recovery Must Be Tested  
**ATEST-65** — Malformed Source Must Not Cause Uncontrolled Compiler Failure  
**ATEST-66** — Valid AST Fuzzing Must Not Violate Compiler Invariants  
**ATEST-67** — MIR Fuzzing Must Test Verifier Robustness  
**ATEST-68** — Invalid MIR Must Be Rejected Deterministically  
**ATEST-69** — Fuzzing Failures Must Be Reproducible By Seed  
**ATEST-70** — Test Failures Must Produce Machine-Readable Records  
**ATEST-71** — Frozen Semantic Invariants Must Map To Conformance Tests  
**ATEST-72** — Missing Invariant Coverage Must Be Detectable  
**ATEST-73** — Mutation Testing May Validate Test-Suite Strength  
**ATEST-74** — Regression Bugs Must Produce Regression Tests  
**ATEST-75** — Test Results Must Be Deterministic Where Semantics Are Deterministic  
**ATEST-76** — Parallel Test Execution Must Not Change Results  
**ATEST-77** — Performance Tests Are Distinct From Conformance Tests  
**ATEST-78** — Compiler Resource Limits Must Be Explicit  
**ATEST-79** — Comptime Execution Must Have Enforceable Resource Limits  
**ATEST-80** — Differential Testing Against Other Languages Is Supplementary  
**ATEST-81** — External Compilers Are Not Axiom Semantic Oracles  
**ATEST-82** — Implementation Details Must Not Become Accidental Conformance Requirements  
**ATEST-83** — Backend Algorithms Are Not Language Semantics  
**ATEST-84** — Optimizer Architecture Is Not A Conformance Requirement  
**ATEST-85** — Register Allocation Strategy Is Not A Conformance Requirement  
**ATEST-86** — Object Layout Is Tested Only Under Representation Contracts  
**ATEST-87** — Conformance Results Are Machine-Readable  
**ATEST-88** — Conformance Results Are Versioned  
**ATEST-89** — Bootstrap Compiler Must Run The Same Conformance Suite  
**ATEST-90** — Self-Hosted Compiler Must Preserve Conformance  
**ATEST-91** — Bootstrap Stages Must Be Differentially Testable  
**ATEST-92** — Compiler Rebuilds Must Preserve Semantic Behavior  
**ATEST-93** — Conformance Must Be Independent Of Compiler Implementation Language  
**ATEST-94** — Conformance Must Remain Valid Across Backend Implementations  
**ATEST-95** — Axiom Specification Is The Semantic Authority  
**ATEST-96** — Tests Are Executable Evidence Of Specification Compliance  
**ATEST-97** — A Passing Build Alone Does Not Establish Conformance  
**ATEST-98** — Conformance Requires Correct Semantics And Required Diagnostics  
**ATEST-99** — Conformance Must Cover The Full Declared Feature Set  
**ATEST-100** — Test Infrastructure Must Not Change Language Semantics  

**BOOTSTRAP-102: FROZEN.**

---

# BOOTSTRAP-103 — Axiom Compiler Frontend Architecture: Lexer → Parser → AST → Resolver → HIR

Bước tiếp theo chuyển từ **"chúng ta biết compiler phải đúng thế nào"** sang **"compiler thực sự tổ chức frontend ra sao"**.

Ta sẽ khóa pipeline:

```text
UTF-8 Source
    ↓
Lexer
    ↓
Token Stream
    ↓
Parser
    ↓
Lossless/Canonical AST
    ↓
Name Resolution
    ↓
Declaration Graph
    ↓
Type/Generic Headers
    ↓
HIR
    ↓
Typed HIR
```

Đặc biệt sẽ giải quyết:

- Unicode identifiers
- comments/trivia
- string/raw string
- numeric literals
- operator precedence
- parser recovery
- AST identity
- source spans
- `import`
- `struct`
- `enum`
- `trait`
- `impl`
- `fn`
- generics
- attributes
- patterns
- closures
- `async`
- `comptime`
- `@kernel`
- ambiguity giữa syntax và semantic resolution
- và cách thiết kế frontend để **AI có thể generate Axiom code dễ dàng nhưng compiler vẫn parse cực kỳ deterministic**.