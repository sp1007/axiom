# BOOTSTRAP-116 — Compiler Correctness, Conformance & Validation Architecture

**Trạng thái: FROZEN / COMPLETED**

Từ task này, mục tiêu không còn là “Axiom có feature gì”, mà là:

> **Làm sao chứng minh compiler Axiom thực sự triển khai đúng những semantics đã khóa.**

Đây là lớp bảo đảm giữa **Specification** và **Compiler**.

---

# 1. Nguyên tắc nền tảng

Axiom cần phân biệt 3 thứ:

```text
Specification
    ↓
Conformance
    ↓
Implementation
```

Compiler không phải nguồn định nghĩa language.

Ví dụ:

```text
Specification:
    Move consumes ownership.

Compiler:
    axc implements ownership verification.

Test:
    verifies that every conforming implementation rejects invalid use-after-move.
```

---

# 2. Không có "reference compiler" làm semantic authority

Không được thiết kế:

```text
Reference Compiler
       ↓
     Axiom
```

theo nghĩa compiler đầu tiên tự định nghĩa semantics.

Thay vào đó:

```text
Axiom Specification
       ↓
Semantic Rules
       ↓
Executable Tests
       ↓
Any Compiler
```

Compiler chỉ là implementation.

---

# 3. Test taxonomy

Axiom có các lớp test:

```text
tests/
├── syntax/
├── resolution/
├── types/
├── traits/
├── ownership/
├── capabilities/
├── control_flow/
├── errors/
├── comptime/
├── concurrency/
├── async/
├── gpu/
├── ffi/
├── abi/
├── layout/
├── optimization/
├── codegen/
├── linker/
├── runtime/
├── std/
├── diagnostics/
├── incremental/
└── bootstrap/
```

---

# 4. Syntax tests

Kiểm tra:

```text
source
 ↓
AST
```

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

phải tạo đúng AST.

Không kiểm tra optimizer ở đây.

---

# 5. Parser negative tests

Ví dụ:

```text
fn foo( {
```

phải sinh:

```text
EPARSE_EXPECTED_TOKEN
```

Test không nên phụ thuộc chính xác toàn bộ wording của message.

---

# 6. Resolution tests

Kiểm tra:

```text
name
module
import
visibility
method
trait
extension
```

Ví dụ:

```text
import math::Vec3;
```

phải resolve đúng `DeclarationId`.

---

# 7. Type tests

Kiểm tra:

```text
inference
casts
operators
generic
associated types
function types
closure types
enum types
newtypes
```

---

# 8. Trait solver tests

Đây là vùng cần test cực mạnh.

Phải kiểm tra:

```text
proven
not proven
ambiguous
cycle
overflow
coherence
associated type resolution
```

Ví dụ:

```text
trait Add<Rhs> {
    type Output;
}
```

compiler phải resolve deterministic.

---

# 9. Ownership conformance

Đây là một trong các test suite quan trọng nhất.

Mỗi test phải kiểm tra các state:

```text
Owned
Moved
PartiallyMoved
Dropped
Uninit
```

và transitions hợp lệ/không hợp lệ.

---

# 10. Move tests

Ví dụ:

```text
let a = value;
consume(a);
use(a);
```

phải reject:

```text
EOWN_MOVED
```

---

# 11. Copy tests

```text
let a: i32 = 10;
let b = a;
use(a);
```

phải hợp lệ.

Compiler không được coi mọi assignment là Move.

---

# 12. Clone tests

```text
consume(a.clone());
use(a);
```

phải hợp lệ nếu `Clone`.

Quan trọng:

```text
clone()
```

không bao giờ được compiler tự chèn.

---

# 13. Drop tests

Kiểm tra:

```text
normal exit
return
break
continue
panic
partial initialization
partial move
nested scopes
```

Mỗi resource phải được cleanup đúng semantic số lần.

---

# 14. Drop oracle

Có thể dùng test type:

```text
struct Tracker {
    id: usize
}
```

với Drop ghi event.

Expected:

```text
A created
B created
B dropped
A dropped
```

Không test physical deallocation.

Chỉ test **semantic Drop order**.

---

# 15. Capability tests

Kiểm tra:

```text
READ
WRITE
MOVE
DROP
```

và:

```text
DISJOINT
SAME
OVERLAP
UNKNOWN
```

---

# 16. View tests

Ví dụ:

```text
let v = view(x);
use(x);
```

hợp lệ nếu `x` vẫn tồn tại.

Nhưng:

```text
drop(x);
use(v);
```

phải reject.

---

# 17. Mutable capability tests

```text
let a = mut_view(x);
let b = mut_view(x);
```

phải reject nếu overlap.

Nhưng:

```text
let a = mut_view(x.left);
let b = mut_view(x.right);
```

có thể hợp lệ nếu compiler chứng minh:

```text
DISJOINT
```

---

# 18. Unknown overlap

Test bắt buộc:

```text
UNKNOWN
```

không được compiler biến thành:

```text
NO_ALIAS
```

chỉ để code compile.

Đây là test bảo vệ optimizer.

---

# 19. Escape tests

Kiểm tra:

```text
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
```

Ví dụ compiler có thể stack-promote một object nếu:

```text
NoEscape
```

nhưng không được làm vậy khi:

```text
ExternalEscape
```

---

# 20. Async conformance

Kiểm tra:

```text
async fn
await
Future
Poll
suspension
cancellation
Drop
Send
```

Ví dụ:

```text
view<T>
```

không được sống qua `.await` nếu không có storage contract phù hợp.

---

# 21. Async semantic test

Không test executor cụ thể.

Test:

```text
Future::poll()
```

phải tuân thủ:

```text
Ready(value)
Pending
```

và wake semantics.

Executor là implementation/runtime layer.

---

# 22. Concurrency tests

Phải có test cho:

```text
Send
Share
Atomic
Mutex
RwLock
Channel
Thread start
Join
Happens-before
```

---

# 23. Memory model tests

Đây là vùng không thể chỉ test bằng một lần chạy.

Cần:

```text
litmus tests
```

Ví dụ các pattern:

```text
Store Release
      ↓
Load Acquire
```

và kiểm tra các outcome được phép/cấm.

---

# 24. Memory-model oracle

Test không nên giả định một scheduling duy nhất.

Thay vào đó:

```text
AllowedOutcomes
ForbiddenOutcomes
```

Ví dụ:

```text
program execution
       ↓
observed outcome
       ↓
must ∈ AllowedOutcomes
```

---

# 25. Atomic tests

Mỗi ordering:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

phải có test riêng.

Không được dùng `SeqCst` implementation để giả lập semantics rồi tuyên bố backend đúng.

---

# 26. FFI tests

Kiểm tra:

```text
C ABI
System ABI
Axiom ABI
```

và:

```text
struct layout
alignment
calling convention
return ABI
variadic
TLS
symbol export
```

---

# 27. ABI golden tests

Ví dụ:

```text
struct Pair {
    a: i32
    b: f32
}
```

với:

```text
@repr(C)
```

phải có golden ABI cho từng target.

---

# 28. Layout tests

Phải phân biệt:

```text
semantic equality
```

với:

```text
physical layout
```

Test:

```text
size_of
align_of
offset_of
```

chỉ được kiểm tra stable nếu representation contract yêu cầu.

---

# 29. Optimization correctness

Đây là lớp cực kỳ quan trọng.

Mọi optimization:

```text
MIR
 ↓
OptIR'
```

phải bảo toàn semantics.

---

# 30. Optimization invariant

Nếu:

```text
P
```

là chương trình hợp lệ và optimizer tạo:

```text
P'
```

thì:

```text
ObservableSemantics(P)
=
ObservableSemantics(P')
```

ngoại trừ những khác biệt được language specification cho phép.

---

# 31. Không test optimizer bằng output assembly בלבד

Assembly giống nhau không chứng minh semantics đúng.

Cần kiểm tra:

```text
input behavior
vs
optimized behavior
```

---

# 32. Differential testing

Trong bootstrap:

```text
Axiom compiler
        ↓
native
```

có thể so sánh với:

```text
reference implementation
LLVM backend
interpreter
```

nhưng chỉ như **validation oracle**.

Không được coi LLVM là language authority.

---

# 33. Interpreter / semantic executor

Axiom nên có một:

```text
Semantic Interpreter
```

ở mức MIR/Verified MIR.

Nó không cần nhanh.

Mục đích:

```text
source
 ↓
MIR
 ↓
interpreter
```

để tạo semantic oracle độc lập với machine backend.

Đây sẽ cực kỳ hữu ích cho compiler development.

---

# 34. Interpreter không phải runtime

Semantic interpreter:

```text
compiler/testing infrastructure
```

không được link vào application.

Production binary không cần nó.

---

# 35. Metamorphic testing

Một kỹ thuật rất phù hợp Axiom.

Ví dụ:

```text
P
```

và transformation semantics-preserving:

```text
P'
```

phải có cùng observable result.

Các phép biến đổi:

```text
inline
noinline
reorder-independent-expression
constant-fold
dead-code-removal
generic-specialization
```

---

# 36. Example

Nếu:

```text
x + 0
```

được optimize thành:

```text
x
```

test phải chứng minh transformation hợp lệ theo numeric semantics Axiom.

Không được dựa vào giả định C-style undefined overflow.

---

# 37. Fuzzing

Fuzz:

```text
lexer
parser
resolver
type checker
trait solver
comptime
MIR builder
verifier
optimizer
backend
object writer
linker
```

Mỗi layer có fuzz target riêng.

---

# 38. Structured fuzzing

Không chỉ random bytes.

Có:

```text
AST generator
HIR generator
MIR generator
Type generator
Trait graph generator
CFG generator
```

Điều này tìm được bug compiler sâu hơn.

---

# 39. MIR verifier fuzzing

Đặc biệt:

```text
random invalid MIR
```

phải:

```text
reject safely
```

không được:

```text
compiler crash
memory corruption
accept invalid MIR
```

---

# 40. Backend fuzzing

Có thể tạo:

```text
valid LIR
```

sau đó kiểm tra:

```text
LIR
 ↓
Machine IR
 ↓
execute
```

so với:

```text
semantic interpreter
```

---

# 41. Object/linker fuzzing

Input:

```text
malformed object
malformed relocation
duplicate symbol
invalid section
invalid alignment
```

phải tạo diagnostic.

Không được crash compiler/linker.

---

# 42. Reproducibility tests

Build hai lần:

```text
Build A
Build B
```

với cùng:

```text
source
compiler
target
dependencies
configuration
```

phải có:

```text
same semantic fingerprint
```

Trong reproducible mode:

```text
same binary
```

là mục tiêu.

---

# 43. Incremental correctness

So sánh:

```text
clean build
```

với:

```text
incremental build
```

phải có:

```text
same semantic result
same diagnostics
same artifact semantics
```

Không nhất thiết byte-identical nếu build mode không yêu cầu.

---

# 44. Bootstrap correctness

Test quan trọng:

```text
Seed Compiler
      ↓
Axiom Compiler 1
      ↓
Axiom Compiler 2
      ↓
Axiom Compiler 3
```

Nếu compiler tự compile chính nó:

```text
axc1 == compiler compiled by axc1
```

phải tiếp tục bootstrap ổn định.

---

# 45. Three-stage bootstrap test

Định kỳ:

```text
Stage0 → Stage1
Stage1 → Stage2
Stage2 → Stage3
```

và:

```text
Stage2(Stage2 source)
```

phải tương đương semantic với:

```text
Stage3(Stage2 source)
```

---

# 46. Cross-target conformance

Cùng source test:

```text
x86-64
AArch64
RISC-V
WASM
```

phải có cùng language semantics.

Khác biệt chỉ khi target-specific behavior được specification cho phép.

---

# 47. Target-specific tests

Không trộn với Core tests.

Ví dụ:

```text
tests/core/
tests/target/x86_64/
tests/target/aarch64/
tests/target/wasm/
```

---

# 48. GPU conformance

GPU cần:

```text
host semantics
kernel legality
storage domain
synchronization
atomic
memory ordering
launch
event
```

và so sánh kết quả với CPU reference implementation khi phù hợp.

---

# 49. Comptime conformance

Comptime phải test:

```text
evaluation
sandbox
capability
dependency tracking
cache
reproducibility
reflection
generated declarations
```

Đặc biệt:

```text
comptime result
```

phải deterministic trong reproducible mode.

---

# 50. Stdlib conformance

Mỗi stdlib module có:

```text
API tests
semantic tests
platform tests
performance tests
ABI tests nếu có
```

Ví dụ `Vec` phải test:

```text
move
drop
reallocation
view invalidation
capacity
zero-sized types
panic safety
```

---

# 51. Compile-fail corpus

Axiom cần một kho lớn:

```text
tests/compile-fail/
```

Các nhóm:

```text
ownership
capability
type
trait
async
concurrency
ffi
abi
comptime
gpu
```

Mục tiêu không chỉ “compiler báo lỗi”, mà:

> **Compiler phải reject đúng chương trình mà specification yêu cầu reject.**

---

# 52. Positive corpus

Ngược lại:

```text
tests/pass/
```

để đảm bảo compiler không quá strict.

Đặc biệt:

```text
valid disjoint views
valid partial moves
valid Send types
valid async state
valid generic code
```

---

# 53. Specification tests

Đây là lớp cao nhất:

```text
spec/
tests/
```

Mỗi semantic rule quan trọng phải có ít nhất:

```text
valid example
invalid example
boundary example
```

Ví dụ:

```text
AMEM-...
ACAP-...
AASYNC-...
ACONCUR-...
AABI-...
```

được map tới test IDs.

---

# 54. Traceability

Mỗi rule có:

```text
Rule ID
    ↓
Specification section
    ↓
Conformance tests
    ↓
Compiler implementation
    ↓
Diagnostic
```

Ví dụ:

```text
ACAP-31
 ↓
tests/capability/validity/
 ↓
Verifier capability pass
 ↓
ECAP_DANGLING
```

Đây là cách tránh “spec viết một đằng, compiler làm một nẻo”.

---

# 55. Conformance manifest

Có thể có:

```text
conformance.ax
```

hoặc metadata tương đương:

```text
Rule
Test
Target
Expected
```

Compiler CI đọc trực tiếp.

---

# 56. Compiler validation levels

Axiom CI có:

```text
Level 0 — smoke
Level 1 — unit
Level 2 — semantic
Level 3 — conformance
Level 4 — fuzz
Level 5 — differential
Level 6 — bootstrap
Level 7 — cross-target
Level 8 — long-running stress
```

---

# 57. Compiler correctness boundary

Kiến trúc cuối:

```text
Source
  ↓
Frontend
  ↓
Typed HIR
  ↓
MIR
  ↓
VERIFIER
  ↓
Verified MIR
  │
  ├── semantic interpreter
  │
  └── optimizer
         ↓
       OptIR
         ↓
        ABI
         ↓
        LIR
         ↓
     Machine Code
```

Verifier là **trust boundary**.

---

# 58. Nếu verifier reject

Không được:

```text
"optimizer thử xem sao"
```

hoặc:

```text
"unsafe compiler mode"
```

để vượt verifier.

Chỉ có:

```text
Verified MIR → optimization
```

---

# 59. Unsafe không bypass conformance

`unsafe` cho phép programmer đưa vào trusted precondition.

Nhưng compiler vẫn phải đảm bảo:

```text
unsafe boundary
 ↓
contract
 ↓
safe verification resumes
```

Test phải xác minh điều này.

---

# 60. Compiler soundness vs completeness

Axiom ưu tiên:

```text
Soundness > Completeness
```

Nếu compiler không chứng minh được:

```text
safe
```

thì reject.

Nhưng điều này phải được kiểm soát để tránh verifier trở thành quá conservative.

Vì vậy positive conformance suite đặc biệt quan trọng.

---

# 61. Compiler performance không được là semantic shortcut

Không được vì compile nhanh mà bỏ:

```text
ownership verification
capability verification
trait correctness
ABI checks
```

Thay vào đó:

```text
incremental
memoization
parallelism
cache
```

được dùng để tăng tốc.

---

# 62. Validation invariants

### `AVAL-20`
The specification is the semantic authority.

### `AVAL-21`
A compiler implementation is not the language definition.

### `AVAL-22`
Every major semantic rule has conformance coverage.

### `AVAL-23`
Positive and negative conformance tests are both required.

### `AVAL-24`
Compile-fail tests use stable diagnostic identities.

### `AVAL-25`
Ownership verification is independently tested.

### `AVAL-26`
Capability verification is independently tested.

### `AVAL-27`
Concurrency memory ordering has executable litmus tests.

### `AVAL-28`
Async semantics are tested independently from executor implementation.

### `AVAL-29`
ABI semantics are target-tested independently.

### `AVAL-30`
Optimization must preserve observable semantics.

### `AVAL-31`
Optimizer legality derives from verified facts.

### `AVAL-32`
Unknown aliasing cannot become proven no-alias through optimization.

### `AVAL-33`
Differential testing is validation, not semantic authority.

### `AVAL-34`
A semantic interpreter may serve as an implementation-independent execution oracle.

### `AVAL-35`
Metamorphic tests validate semantics-preserving transformations.

### `AVAL-36`
Compiler fuzzing must cover every major compiler boundary.

### `AVAL-37`
Invalid IR must be rejected safely.

### `AVAL-38`
Compiler crashes are distinct from user-program errors.

### `AVAL-39`
Incremental and clean builds must be semantically equivalent.

### `AVAL-40`
Reproducible builds must have stable semantic identity.

### `AVAL-41`
Bootstrap stages must preserve compiler semantics.

### `AVAL-42`
Cross-target compilation must preserve language semantics.

### `AVAL-43`
GPU compilation must obey the same fundamental ownership/capability rules.

### `AVAL-44`
Comptime-generated code re-enters ordinary verification.

### `AVAL-45`
Unsafe does not disable semantic verification after its trusted boundary.

### `AVAL-46`
Stdlib conformance is separate from compiler-core conformance.

### `AVAL-47`
Runtime implementation details must not become accidental language semantics.

### `AVAL-48`
Test results must be deterministic where the language semantics are deterministic.

### `AVAL-49`
Every compiler transformation has a legality condition.

### `AVAL-50`
A failed proof must prevent the transformation rather than weaken semantics.

### `AVAL-51`
Compiler correctness must be testable without relying exclusively on native execution.

### `AVAL-52`
Semantic behavior must be traceable from specification rule to implementation and tests.

### `AVAL-53`
Compiler optimization must not introduce mandatory runtime machinery absent from the source semantics.

### `AVAL-54`
Bootstrap compiler trust must be documented and reproducible.

### `AVAL-55`
Axiom's correctness architecture must scale independently of any particular backend.

---

# Kiến trúc Axiom đã đạt tới đâu?

Sau 116, chúng ta có:

```text
                  AXIOM SPECIFICATION
                          │
             ┌────────────┴────────────┐
             │                         │
       Semantic Rules            Conformance
             │                         │
             └────────────┬────────────┘
                          ↓
                    CompilerDB
                          ↓
       ┌──────────────────┴──────────────────┐
       │                                     │
   Frontend                              Verifier
       │                                     │
       └──────────────────┬──────────────────┘
                          ↓
                    Verified MIR
                          │
                ┌─────────┴─────────┐
                │                   │
          Semantic VM           Optimizer
                                    │
                                    ↓
                                  OptIR
                                    ↓
                                   ABI
                                    ↓
                                   LIR
                                    ↓
                              Machine Backend
                                    ↓
                              Object / Linker
                                    ↓
                              Native Binary
```

Đây là một mốc rất quan trọng: **chúng ta không còn chỉ thiết kế một programming language; chúng ta đã thiết kế cả trust architecture của compiler.**

---

# BOOTSTRAP-117 — Core Specification Consolidation

Bây giờ nên **ngừng thêm architecture feature mới trong một lúc**.

Task kế tiếp là gom toàn bộ những gì đã frozen thành **Axiom Core Language Specification v0.1** duy nhất.

Nó sẽ xử lý:

1. **Lexical grammar**
2. **Concrete syntax**
3. **Identifiers / keywords**
4. **Declarations**
5. **Expressions**
6. **Statements**
7. **Types**
8. **Struct**
9. **Enum**
10. **Trait**
11. **Generics**
12. **Functions / methods**
13. **Closures**
14. **Ownership**
15. **Move / Copy / Clone**
16. **Drop**
17. **`view` / `mut_view`**
18. **Control flow**
19. **Pattern matching**
20. **Option / Result**
21. **Error / panic**
22. **Comptime**
23. **Concurrency**
24. **Async**
25. **FFI**
26. **Unsafe**
27. **ABI**
28. **Memory model**
29. **GPU**
30. **Attributes**
31. **Modules**
32. **Visibility**
33. **Evaluation order**
34. **Numeric semantics**
35. **String/UTF-8 semantics**
36. **Undefined behavior policy**
37. **Implementation-defined vs target-defined behavior**
38. **Conformance requirements**

Và quan trọng nhất, task 117 sẽ trả lời một câu hỏi:

> **Nếu đưa file `.ax` bất kỳ cho hai compiler Axiom độc lập, chính xác những gì bắt buộc phải giống nhau, và những gì compiler được phép tự do lựa chọn?**

Đây sẽ là bước chuyển từ **“kiến trúc Axiom” → “ngôn ngữ Axiom có specification chính thức”**.