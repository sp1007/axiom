# BOOTSTRAP-158 — Error Handling, Panic, Result, Diagnostics & Failure Semantics
**STATUS: FROZEN / COMPLETED**

> **Axiom không dùng exception như cơ chế điều khiển lỗi thông thường. `Result` biểu diễn recoverable failure; `panic` biểu diễn lỗi không thể tiếp tục theo contract hiện tại; `abort`/fault là process-level termination.**

Đây là quyết định quan trọng để giữ Axiom vừa hiệu năng cao vừa dễ phân tích bởi compiler.

---

## 1. Failure model thống nhất

Axiom phân biệt rõ:

```text id="q3f7a1"
                    FAILURE
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
   Recoverable      Contract          Process /
     failure         violation          system
       │               │                │
       ▼               ▼                ▼
    Result<E>         panic           abort/fault
```

Ngoài ra:

```text
Option<T>
```

không phải error.

Nó biểu diễn:

```text
có giá trị / không có giá trị
```

---

# 2. `Option` ≠ `Result`

```ax id="8j4h2p"
Option<T>
```

dùng khi:

> Không có giá trị là một trạng thái bình thường.

Ví dụ:

```ax
map.get(key) -> Option<&Value>
```

Trong Axiom syntax tương ứng sẽ dùng `view<Value>` thay vì reference syntax đã frozen.

---

`Result<T, E>`:

```ax
Result<T, E>
```

dùng khi:

> Thất bại mang thông tin mà caller có thể xử lý.

---

# 3. `Result` không cần runtime

```ax
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

chỉ là ordinary enum.

Compiler có thể biến:

```ax
return Result::Err(e);
```

thành:

```text
register
+
branch
```

hoặc thậm chí tối ưu hoàn toàn trong caller.

---

# 4. `?` là control-flow sugar

Ví dụ:

```ax
let x = read()?;
```

semantic tương đương:

```text id="5j9q3m"
call
 ↓
inspect Result
 ├── Ok → continue
 └── Err → return Err
```

Không có exception machinery.

---

# 5. `?` không phải exception

Điểm này phải frozen:

```text id="d1b4x8"
? = explicit typed control flow
exception = implicit non-local control flow
```

Compiler có thể nhìn thấy chính xác đường đi của `?`.

---

# 6. Error type là ordinary type

Ví dụ:

```ax id="3e6j9k"
enum FileError {
    NotFound,
    PermissionDenied,
    InvalidPath,
    Io(...)
}
```

Không cần một global exception hierarchy.

---

# 7. Không có `Object`/`Exception` hierarchy

Axiom không tạo:

```text id="q8l3nw"
Exception
 ├── IOError
 ├── NetworkError
 ├── ...
```

làm Core primitive.

Điều này tránh:

```text id="j7x0h2"
hidden allocation
RTTI
vtable
exception metadata
```

---

# 8. Trait-based errors

Library có thể định nghĩa:

```ax id="p7y6c1"
trait Error {
    message(...)
    source(...)
}
```

nhưng đây là abstraction của library.

Không biến mọi error thành dynamic object.

---

# 9. Static error handling mặc định

Ví dụ:

```ax id="3qv4f9"
fn load() -> Result<Data, LoadError>
```

được ưu tiên hơn:

```ax id="6m4g8x"
fn load() throws ...
```

trong Core v1.

---

# 10. Có cần `try/catch` không?

**Không đưa exception/`try-catch` vào Core v1.**

Lý do không phải “exception luôn chậm”.

Vấn đề lớn hơn là semantic complexity:

```text id="9y0xcs"
implicit control flow
hidden cleanup paths
hidden propagation
cross-function effects
exception tables
optimizer complexity
```

Axiom đã có:

```text id="x2z1ca"
Result
?
panic
unwind
```

nên không cần thêm một failure mechanism thứ tư.

---

# 11. Nhưng unwind vẫn được hỗ trợ

Đây là điểm rất quan trọng.

Axiom có thể compile:

```text id="f6b4tw"
panic
```

theo profile:

```text id="x4z8h3"
panic=abort
panic=unwind
```

`unwind` là **panic recovery mechanism**, không phải general exception mechanism.

---

# 12. `panic=abort`

Đây nên là profile rất quan trọng cho:

```text id="f0g9r3"
embedded
game
performance-critical
small binary
freestanding
```

Flow:

```text id="q5g0c6"
panic
 ↓
cleanup required by profile
 ↓
abort
```

Không cần unwind tables nếu target/profile cho phép.

---

# 13. `panic=unwind`

Flow:

```text id="n8w3a5"
panic
 ↓
cleanup
 ↓
unwind
 ↓
caller cleanup
 ↓
process boundary
```

Mục đích chính:

- cleanup resource;
- tooling/debugging;
- embedding/system integration;
- platform-specific recovery.

Không biến nó thành Java/C++ exception system.

---

# 14. Panic không phải recoverable error

Ví dụ:

```ax id="6f8b3a"
fn parse_user_input(...) -> Result<User, ParseError>
```

Sai input:

```text id="parse"
Result::Err
```

Trong khi:

```text id="f7a2k1"
internal compiler invariant violated
```

có thể:

```text id="panic"
panic
```

---

# 15. Panic không nhất thiết là programmer bug

Panic có thể biểu diễn:

```text id="5w9p2c"
unrecoverable contract failure
```

ví dụ:

```text index unexpectedly invalid
internal invariant broken
unrecoverable runtime condition
```

Nhưng API thiết kế tốt không nên dùng panic cho lỗi mà caller có thể xử lý.

---

# 16. Bounds violation

Safe indexing:

```ax id="c2p7mz"
xs[i]
```

nếu compiler không chứng minh:

```text
i < xs.len
```

thì runtime check có thể được sinh.

Nếu check fail:

```text id="4h1n7q"
panic
```

không phải undefined behavior.

---

# 17. Bounds-check elimination

Nếu compiler chứng minh:

```text id="w7d3f9"
0 <= i < len
```

thì:

```text id="z3m5x0"
runtime bounds check
```

biến mất.

Error semantics vẫn được bảo toàn vì compiler đã chứng minh failure path unreachable.

---

# 18. Allocation failure

Allocation API có thể:

```text id="a8k4p1"
Result<T, AllocError>
```

hoặc profile/runtime policy có thể chọn:

```text id="m6y9r2"
panic
abort
```

Không ép mọi application phải mang exception infrastructure.

---

# 19. I/O errors

Ví dụ:

```ax id="r7k2q4"
File.read(...)
    -> Result<usize, IoError>
```

Caller xử lý explicit.

---

# 20. Async errors

Async:

```ax id="p5x1q8"
Future<Result<T,E>>
```

là composition tự nhiên.

Không cần exception propagation xuyên coroutine.

---

# 21. Cancellation ≠ Error

Cancellation là:

```text id="c8w2z6"
execution control event
```

Không mặc định:

```text id="j9s4a2"
Err(Cancelled)
```

vì cancellation và domain error có semantics khác nhau.

Library có thể chọn API:

```ax
Future<Result<T, E>>
```

và cancellation handle riêng.

---

# 22. Panic ≠ cancellation

```text id="u4r6m8"
panic
```

là failure của execution.

```text id="q8p3v1"
cancel
```

là yêu cầu dừng công việc.

Hai cơ chế không được nhập làm một.

---

# 23. Hardware faults

Ví dụ:

```text id="a6f1z9"
page fault
illegal instruction
access violation
divide fault
```

không phải ordinary `Result`.

Đây là:

```text id="s5k3h7"
platform/process fault
```

System layer quyết định cách ánh xạ.

---

# 24. Raw-pointer violation

Trong safe Axiom:

```text id="safe"
invalid memory access
```

không được xảy ra.

Trong `unsafe`:

```text id="unsafe"
programmer assumes machine-level contract
```

Nếu contract bị vi phạm:

```text id="q1m8v4"
behavior depends on unsafe contract / target machine semantics
```

Không biến nó thành `Result`.

---

# 25. FFI failure

Foreign function:

```text id="e3r7w2"
extern "C"
```

không được tự động biến exception của foreign runtime thành Axiom `Result`.

Wrapper phải định nghĩa contract.

Ví dụ:

```text id="k9v4s1"
C API
 ↓
Axiom FFI wrapper
 ↓
Result<T, Error>
```

---

# 26. OS error

System layer có thể chuyển:

```text id="r4g7x2"
OS status code
```

thành:

```text id="z6p1k9"
Result<T, SystemError>
```

nhưng mapping thuộc platform layer.

---

# 27. Error propagation

Axiom nên làm propagation cực kỳ rẻ.

Ví dụ:

```ax id="q3f8m6"
fn process() -> Result<Data, Error> {
    let a = read_a()?;
    let b = read_b()?;
    return combine(a, b);
}
```

Compiler có thể biến thành:

```text id="k7y2p4"
direct branch
+
error register
```

không allocation.

---

# 28. Error type specialization

Generic:

```ax
Result<T, E>
```

có thể specialize theo:

```text id="w2j6n8"
E size
E alignment
E Drop
frequency
branch probability
```

Ví dụ hot success path có thể được tối ưu.

---

# 29. Cold error path

PGO có thể nhận ra:

```text id="b6t4r1"
Ok = 99.9%
Err = 0.1%
```

và compiler có thể:

```text id="x9p3v5"
hot path
cold error path
```

tách code.

Đây là optimization, không phải semantic assumption.

---

# 30. Error construction

Nếu error:

```ax
Err(FileError::NotFound)
```

nhỏ và không escape:

```text id="e7m1q3"
```

có thể chỉ tồn tại trong register.

Không bắt buộc heap allocation.

---

# 31. Dynamic error

Nếu application thực sự cần:

```ax id="w3k8r5"
dyn Error
```

thì dynamic dispatch là explicit.

Có thể có:

```text id="x2n6m9"
data pointer
+
vtable
```

nhưng không xuất hiện cho ordinary `Result<T,E>`.

---

# 32. Error context

Không cần exception stack để có context.

Library có thể:

```text id="j5r1c8"
Error::with_context(...)
```

và representation tùy nhu cầu.

---

# 33. Source location

Compiler có thể cung cấp diagnostics:

```text id="d4x8m2"
file
line
column
span
function
call chain
```

mà không bắt runtime error object phải chứa toàn bộ thông tin.

---

# 34. Runtime diagnostic

Runtime panic handler có thể nhận:

```text id="m7q2s5"
PanicInfo
```

bao gồm:

```text
message
source location
function
backtrace capability
```

tùy profile.

Minimal freestanding có thể bỏ gần như toàn bộ.

---

# 35. Debug vs release

Debug build có thể giữ:

```text id="r5k8v1"
rich panic information
```

Release:

```text id="c2m6x9"
minimal panic path
```

miễn semantic profile quy định rõ.

---

# 36. `expect`

Có thể có:

```ax id="x4q9n2"
option.expect(...)
result.expect(...)
```

nghĩa là:

```text id="p8m3k6"
Some/Ok → value
None/Err → panic
```

Đây là library operation.

---

# 37. `unwrap`

Có thể có:

```ax id="u7k1r5"
unwrap()
```

nhưng API documentation nên phân biệt:

```text id="s3m8x2"
recoverable path
vs
programmer-established invariant
```

Compiler vẫn biết panic branch.

---

# 38. No hidden failure

Một function:

```ax
fn foo() -> i32
```

không được âm thầm biến thành:

```text id="j8w4q1"
Result<i32, HiddenError>
```

do compiler.

Failure behavior là một phần semantic contract.

---

# 39. Effect system integration

Hiện đã có:

```text id="k5v2s7"
Effect:
    Panic
```

Function có thể được compiler xác định:

```text id="x1m8q4"
MayPanic
NoPanic
```

nhưng không cần programmer viết annotation thông thường.

---

# 40. Panic analysis

Compiler có thể suy ra:

```text id="f6q3n9"
foo()
 ↓
MayPanic
```

và:

```text id="b8r1x5"
bar()
 ↓
NoPanic
```

nếu tất cả đường gọi đều không panic.

Điều này hỗ trợ optimization và diagnostics.

---

# 41. `Result` không tạo `Panic` effect

```ax
fn read() -> Result<Data, Error>
```

nếu chỉ trả `Err`:

```text id="w9k2s4"
Panic effect = false
```

Đây là distinction rất quan trọng.

---

# 42. `?` cũng không tự tạo Panic

`?` chỉ propagate `Result`.

Do đó:

```text id="n3x7m1"
Result
```

không đồng nghĩa:

```text id="v8q2c6"
Panic
```

---

# 43. Unwinding và Drop

Nếu:

```text id="s6r4k2"
panic=unwind
```

compiler đã có:

```text id="h2m8p5"
Drop verification
```

nên unwind path phải chạy đúng cleanup.

Không được:

```text id="e4q7n1"
panic
 ↓
skip Drop
```

đối với resource phải cleanup.

---

# 44. Cleanup graph

MIR có thể biểu diễn:

```text id="j1w6s8"
normal edge
panic edge
cleanup edge
```

và Drop elaboration đã frozen.

---

# 45. `panic=abort` optimization

Khi abort:

```text id="q8m3v5"
no caller recovery
```

compiler có thể giảm:

```text id="c6r1x9"
landing pads
unwind tables
exception metadata
```

nhưng vẫn phải thực hiện semantic cleanup được profile yêu cầu trước termination.

---

# 46. FFI boundary

Nếu gọi foreign code:

```text id="m5k9w2"
Foreign
```

Effect system phải bảo thủ.

Ví dụ foreign function có thể:

```text id="f3x7p1"
write memory
panic/fault
synchronize
modify external state
```

nếu contract không mô tả rõ.

---

# 47. `noexcept` tương đương?

Không cần programmer viết:

```text id="d9v4s6"
noexcept
```

Compiler tự suy luận `MayPanic`.

Tại FFI/system boundary, contract có thể khai báo foreign behavior.

---

# 48. Error ABI

`Result<T,E>` có thể được ABI-lower thành:

```text id="z1q8m4"
tag + payload
```

hoặc:

```text id="n6r3x7"
niche
```

hoặc register pair.

ABI không phải semantic definition.

---

# 49. Error ABI optimization

Ví dụ:

```text id="v4p9k2"
Result<NonNull<T>, E>
```

có thể tận dụng niche.

Compiler quyết định representation nếu ABI contract không cố định.

---

# 50. Error path code size

Binary-size optimization có thể:

```text id="r8m2c5"
cold-split error handling
merge identical error paths
deduplicate panic strings
remove unreachable errors
```

miễn semantics preserved.

---

# 51. Panic string

Panic message không nhất thiết tồn tại trong binary nếu:

```text id="j6x1q4"
profile
```

quy định bỏ message/debug metadata.

Nhưng nếu program có thể quan sát message thì compiler phải giữ.

---

# 52. Diagnostics khác runtime errors

Đây là distinction rất quan trọng:

```text id="k4w8p2"
Compiler Diagnostic
Runtime Error
Panic
System Fault
```

là bốn tầng khác nhau.

---

# 53. Compiler diagnostics

Compiler phải có:

```text id="c9m5x1"
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message
    notes
    suggestions
    related_symbols
    semantic_facts
}
```

---

# 54. Stable diagnostic codes

Ví dụ:

```text id="w2q7n4"
E_USE_AFTER_MOVE
E_CAPABILITY_CONFLICT
E_CAPABILITY_LIFETIME
E_UNINITIALIZED
E_NON_EXHAUSTIVE_MATCH
E_TRAIT_AMBIGUOUS
E_INVALID_CAST
E_FFI_CONTRACT
```

đã phù hợp với AI tooling architecture.

---

# 55. Compiler diagnostics cho AI

AI không nên phải parse:

```text id="m8x3r6"
"something went wrong near line 42"
```

Thay vào đó:

```text id="s4k9p1"
DiagnosticCode
SourceSpan
Expected
Found
RelatedDeclaration
OwnershipFact
CapabilityFact
SuggestedFix
```

---

# 56. Machine-readable diagnostics

Compiler hỗ trợ:

```text id="f7n2c8"
JSON
JSONL
structured binary
human-readable
```

để IDE/AI/CI sử dụng.

---

# 57. Explain failure

Axiom có thể có:

```text id="p3x8m1"
axc explain E_CAPABILITY_CONFLICT
```

hoặc:

```text id="j6q4v9"
axc explain --at file.ax:42
```

Compiler hiển thị reasoning graph:

```text id="r5k1w7"
owner X
 ↓
mut_view A
 ↓
read/write operation
 ↓
overlap proven
 ↓
conflict
```

---

# 58. AI không được sửa semantics bằng cách đoán

Nếu compiler trả:

```text id="z7m2c4"
E_CAPABILITY_LIFETIME
```

AI agent phải sửa source.

Không được yêu cầu compiler:

```text id="n8q3x5"
ignore lifetime
```

trừ khi explicit unsafe/system operation thực sự thay đổi semantic contract.

---

# 59. `unsafe` và panic

Unsafe code không biến:

```text id="u5r9k2"
panic
```

thành:

```text id="d3m7x1"
Result
```

và ngược lại.

Failure semantics vẫn được giữ.

---

# 60. Quyết định lớn: Không có exception Core v1

Đóng băng:

```text id="5q8m2v"
NO GENERAL EXCEPTION SYSTEM
```

Axiom Core v1 có:

```text
Option
Result
?
panic
abort
unwind
```

nhưng **không có**:

```text
try/catch
throw
exception hierarchy
implicit exception propagation
```

`throws` từng được giữ làm future reserved keyword, nhưng **không có semantic trong Core v1**.

---

# 61. Tại sao lựa chọn này phù hợp Axiom

Pipeline failure cực kỳ rõ:

```text id="x4m8q2"
Expected failure
    ↓
Result<T,E>

Absence
    ↓
Option<T>

Unrecoverable contract failure
    ↓
panic

Process termination
    ↓
abort

Panic recovery
    ↓
unwind

Hardware/OS failure
    ↓
system/platform semantics
```

Không có hai cơ chế cùng giải quyết một semantic question.

---

# 62. Invariants

Đóng băng:

### `AERROR-20`
`Option<T>` represents semantic absence, not failure.

### `AERROR-21`
`Result<T,E>` represents typed recoverable failure.

### `AERROR-22`
`Result` is an ordinary algebraic type.

### `AERROR-23`
`Result` requires no mandatory runtime.

### `AERROR-24`
`?` is explicit typed control flow.

### `AERROR-25`
`?` does not constitute exception propagation.

### `AERROR-26`
Recoverable failure does not implicitly produce a panic effect.

### `AERROR-27`
Axiom Core v1 does not define a general exception hierarchy.

### `AERROR-28`
Axiom Core v1 does not define `try/catch`.

### `AERROR-29`
Axiom Core v1 does not define implicit `throw`.

### `AERROR-30`
Panic is distinct from recoverable failure.

### `AERROR-31`
Panic is distinct from cancellation.

### `AERROR-32`
Cancellation is an execution-control mechanism.

### `AERROR-33`
Hardware/process faults are distinct from ordinary `Result` failures.

### `AERROR-34`
FFI failures require explicit wrapper semantics.

### `AERROR-35`
Foreign exceptions are not implicitly translated into Axiom exceptions or Results.

### `AERROR-36`
Panic behavior is controlled by an explicit panic profile.

### `AERROR-37`
`panic=abort` may remove unwind machinery where valid.

### `AERROR-38`
`panic=unwind` preserves required cleanup semantics.

### `AERROR-39`
Drop obligations remain valid during panic cleanup.

### `AERROR-40`
Panic does not bypass ownership verification.

### `AERROR-41`
Bounds failures in safe code are defined failures, not undefined behavior.

### `AERROR-42`
Bounds checks may be eliminated only through proof.

### `AERROR-43`
Allocation failure has explicit API/profile semantics.

### `AERROR-44`
Error propagation does not require heap allocation.

### `AERROR-45`
Error values remain ordinary typed values.

### `AERROR-46`
Dynamic error dispatch is explicit.

### `AERROR-47`
`Result<T,E>` ABI is representation-independent at the semantic level.

### `AERROR-48`
Compiler may optimize error representation without changing semantics.

### `AERROR-49`
Cold error paths may be separated through optimization.

### `AERROR-50`
Unreachable error branches may be eliminated when proven unreachable.

### `AERROR-51`
Error-path optimization may use PGO but PGO cannot establish semantic validity.

### `AERROR-52`
Panic messages are retained whenever observability requires them.

### `AERROR-53`
Diagnostic metadata is distinct from runtime error metadata.

### `AERROR-54`
Compiler diagnostics use stable machine-readable codes.

### `AERROR-55`
Diagnostics contain structured source and semantic provenance.

### `AERROR-56`
AI/IDE tooling can inspect diagnostic reasoning without parsing human prose.

### `AERROR-57`
Compiler diagnostics cannot be suppressed by optimization level when the program is semantically invalid.

### `AERROR-58`
Unsafe code does not globally disable failure semantics or verification.

### `AERROR-59`
No hidden failure channel may be introduced by the compiler.

### `AERROR-60`
A function's observable failure behavior is part of its semantic contract.

### `AERROR-61`
Effect analysis tracks panic behavior independently from `Result`.

### `AERROR-62`
`Result` does not imply `Panic`.

### `AERROR-63`
Compiler optimizations must preserve all observable failure behavior.

### `AERROR-64`
Runtime failure mechanisms must not become a mandatory monolithic runtime.

### `AERROR-65`
The standard library may provide richer error abstractions without changing Core semantics.

### `AERROR-66`
Error abstractions must preserve ownership, capability and Drop rules.

### `AERROR-67`
Async error propagation composes through ordinary typed values.

### `AERROR-68`
Async cancellation remains distinct from failure values.

### `AERROR-69`
Error handling must remain compatible with freestanding and runtime-free profiles where applicable.

### `AERROR-70`
Axiom failure semantics are deterministic and target-independent except for explicitly platform-defined faults/contracts.

---

# Kiến trúc hiện tại sau BOOTSTRAP-158

Axiom giờ có một failure model khá sạch:

```text
                  VALUE
                    │
          ┌─────────┴─────────┐
          │                   │
       Option              Result
          │                   │
       absence          recoverable error
                              │
                              ▼
                       explicit `?`
                              │
                              ▼
                          caller
```

Trong khi:

```text
                 EXECUTION FAILURE
                        │
              ┌─────────┴─────────┐
              │                   │
            panic              fault
              │                   │
       ┌──────┴──────┐       OS/hardware
       │             │
     abort         unwind
```

Và compiler:

```text
                  COMPILER
                     │
                     ▼
               DiagnosticDB
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
    human          IDE             AI
    output       structured      structured
```

Điều này rất phù hợp với mục tiêu ban đầu của Axiom: **không cần exception runtime nặng nhưng vẫn có failure semantics đầy đủ và deterministic**.

---

# BOOTSTRAP-159 — Testing, Assertions, Contracts & Verification-Aware Debugging

Bước tiếp theo nên đi sâu vào **test architecture của chính ngôn ngữ và compiler**, nối `Result/panic`, verifier, comptime, optimizer và native execution thành một hệ thống test mạnh.

Trọng tâm:

```text
Source
  ↓
Unit Test
  ↓
Property Test
  ↓
Compile-fail Test
  ↓
MIR Verification Test
  ↓
Optimization Equivalence
  ↓
Backend Test
  ↓
Native Runtime Test
  ↓
Cross-target Test
```

và đặc biệt:

> **Axiom có thể dùng chính compiler verifier + semantic interpreter làm oracle để phát hiện compiler miscompilation, ownership bug, optimization bug và backend bug như thế nào mà không biến test framework thành một phần nặng của runtime?**