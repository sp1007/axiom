Tiếp tục với **BOOTSTRAP-035 — Error Handling, Panic, Unwind & Failure Semantics**.

Đây là task cần chốt khá kỹ, vì error model ảnh hưởng trực tiếp tới **ABI, Drop, async, thread, FFI, binary size và runtime**.

# BOOTSTRAP-035 — Error Handling & Failure Semantics

## 1. Tách 4 loại "lỗi"

Axiom không nên gom tất cả vào `Exception`.

```text
Recoverable Error
    ↓
Result<T, E>

Absence
    ↓
Option<T>

Programmer / invariant failure
    ↓
panic

Process / machine fatal failure
    ↓
abort / trap
```

Đây là mô hình chính.

---

# 2. `Result<T, E>` là cơ chế lỗi chính

Ví dụ:

```axiom
fn read_file(path: view<str>) -> Result<File, IoError>
```

Caller:

```axiom
let file = read_file("test.txt")?
```

Không có hidden exception table.

Semantically:

```text
call
 ↓
Result
 ↓
match
 ↓
return error
```

Compiler có thể optimize representation.

---

# 3. `Option<T>` không phải error

```axiom
fn find(id: usize) -> Option<Item>
```

Có nghĩa:

```text
có / không có
```

không phải:

```text
thành công / lỗi
```

Ví dụ:

```text
Option<User>
```

vs:

```text
Result<User, DatabaseError>
```

phải giữ semantic distinction.

---

# 4. `?` chỉ là control-flow sugar

```axiom
let x = foo()?
```

tương đương semantic:

```text
match foo() {
    Ok(v) => v
    Err(e) => return Err(e)
}
```

Không tạo exception.

Không stack unwinding.

Không runtime lookup.

---

# 5. Error propagation không cần allocation

Ví dụ:

```axiom
enum Error {
    NotFound,
    PermissionDenied,
    InvalidInput
}
```

Compiler có thể truyền:

```text
register
```

hoặc stack.

Không có:

```text
heap Error object
```

bắt buộc.

---

# 6. Error type là ordinary type

Không có:

```text
Exception
Throwable
RuntimeException
```

đặc biệt trong Core.

`Error` chỉ là:

```text
enum
struct
```

hoặc type người dùng định nghĩa.

---

# 7. Error composition

Generic library có thể cung cấp:

```text
map
map_err
and_then
or_else
```

nhưng đây là library semantics.

Core chỉ cần:

```text
Result
match
?
```

---

# 8. Panic khác Error

Ví dụ:

```axiom
fn divide(a: i32, b: i32) -> i32 {
    if b == 0 {
        panic("division by zero")
    }

    a / b
}
```

Panic biểu thị:

> computation không thể tiếp tục theo normal contract.

Không dùng panic cho business error.

---

# 9. Panic không phải C++ exception

C++:

```text
throw
 ↓
stack unwind
 ↓
catch
```

Axiom:

```text
panic
 ↓
panic policy
 ├── abort
 └── unwind
```

và **không có `catch` trong Core v1**.

Đây là quyết định tôi đề xuất freeze.

---

# 10. Tại sao không có `catch`?

Nếu có:

```axiom
try {
    foo()
}
catch e {
    ...
}
```

thì exception becomes a second error-control system.

Kéo theo:

- hidden control flow
- exception tables
- ABI complexity
- destructor complexity
- FFI complexity
- optimizer complexity
- async interaction
- debugging complexity

Trong khi `Result` đã đủ cho recoverable failure.

---

# 11. Nhưng unwind vẫn có thể tồn tại

Điều này rất quan trọng.

Không có `catch` không có nghĩa:

> Axiom không thể unwind.

Có thể hỗ trợ:

```text
panic strategy = abort
panic strategy = unwind
```

Unwind là **runtime/compiler implementation policy**, không phải application error API.

---

# 12. Abort profile

Default release có thể:

```text
panic
 ↓
abort process
```

Ưu điểm:

```text
no unwind tables
smaller binary
simpler runtime
predictable
```

Rất phù hợp mục tiêu native nhỏ.

---

# 13. Unwind profile

Debug/test hoặc platform cần có thể:

```text
panic
 ↓
unwind
 ↓
Drop resources
 ↓
thread boundary / process termination
```

Nhưng không có user-level catch.

---

# 14. Vậy unwind dùng để làm gì?

Ví dụ:

```text
Thread
  ↓
task
  ↓
function A
  ↓
function B
  ↓
panic
```

Unwind có thể đi tới:

```text
thread root
```

scheduler/runtime quan sát:

```text
ThreadResult::Panicked
```

hoặc:

```text
JoinError::Panic
```

---

# 15. Thread panic

Ví dụ:

```axiom
let h = Thread.spawn(fn() {
    panic("failure")
})

let result = h.join()
```

`join()` không tự panic lại.

Nó có thể:

```text
Result<T, ThreadError>
```

với:

```text
ThreadError::Panicked
```

Nếu muốn re-panic, application tự quyết định.

---

# 16. Detached thread

Nếu:

```axiom
Thread.detach(...)
```

panic không có caller để nhận.

Runtime policy:

```text
log
terminate worker
report
abort process
```

có thể tùy profile.

Không nên để semantics phụ thuộc scheduler implementation.

---

# 17. Async panic

```axiom
async fn foo() -> Result<T, E>
```

có hai failure paths:

```text
Result
    ↓
recoverable

panic
    ↓
panic policy
```

`.await` không biến panic thành Result.

---

# 18. Future panic

Future có state:

```text
Pending
Ready
Panicked
```

về semantic control flow, nhưng public API không nhất thiết phải expose `Panicked` như một `Poll` variant.

`Poll` vẫn:

```text
Ready(T)
Pending
```

Panic là exceptional termination của computation.

---

# 19. Drop khi panic

Đây là invariant rất quan trọng.

Nếu unwind:

```text
panic
 ↓
scope exit
 ↓
Drop owned resources
 ↓
caller
```

Ví dụ:

```axiom
let a = ResourceA()
let b = ResourceB()

panic(...)
```

thì:

```text
Drop(b)
Drop(a)
```

theo reverse initialization order.

---

# 20. Moved values không Drop

Nếu:

```axiom
let a = Resource()
let b = move a
panic(...)
```

thì:

```text
b → Drop
a → no Drop
```

Không double destruction.

---

# 21. Partial move khi panic

Nếu derived Drop type cho phép partial move:

```text
struct Pair {
    a: ResourceA
    b: ResourceB
}
```

sau:

```text
move p.a
panic()
```

thì:

```text
p.a → already moved
p.b → Drop
```

Compiler theo dõi field state.

---

# 22. User-defined Drop

Đã freeze:

> User-defined destructive Drop không cho partial move.

Điều này tránh semantic ambiguity trong destructor.

---

# 23. Panic trong Drop

Không nên cho:

```text
Drop
 ↓
panic
 ↓
Drop
 ↓
panic
```

tạo nested-unwind complexity.

Đề xuất:

### Normal execution

Drop panic → panic policy.

### Active unwind

Drop panic → **terminate/abort process hoặc execution domain**.

Không tiếp tục unwind một panic thứ hai.

---

# 24. Drop không trả `Result`

Đã freeze:

```text
Drop = cleanup
```

không phải business operation.

Không:

```axiom
impl Drop for File {
    fn drop(...) -> Result<...>
}
```

Nếu close có thể thất bại:

```axiom
file.close() -> Result<(), Error>
```

caller phải xử lý trước khi object bị Drop.

---

# 25. Ví dụ File

```axiom
var file = File.open(path)?
...
file.close()?
```

Nếu quên:

```text
Drop(file)
```

vẫn giải phóng resource.

Nhưng lỗi close cuối cùng không được phép "ném ngược" qua Drop.

---

# 26. Allocation failure

Đây là vấn đề đặc biệt.

Không nên mặc định:

```text
malloc fails
 ↓
panic
```

cho mọi API.

Library có thể:

```axiom
Vec.try_reserve(n)
    -> Result<(), AllocError>
```

và có convenience API:

```axiom
Vec.reserve(n)
```

có thể panic/abort khi không thể đáp ứng.

---

# 27. OOM policy

Axiom nên hỗ trợ profile:

```text
fallible allocation
infallible allocation
```

nhưng semantic distinction phải rõ.

Ví dụ:

```text
try_allocate<T>()
    -> Result<Box<T>, AllocError>
```

là recoverable.

Trong application:

```text
allocate<T>()
```

có thể dùng configured panic/OOM policy.

---

# 28. Không có global OOM exception

Không:

```text
OutOfMemoryException
```

được ném xuyên arbitrary stack.

Thay vào đó:

```text
Result
```

hoặc configured fatal policy.

---

# 29. Integer errors

Axiom đã chốt không có C-style signed overflow UB.

Có các semantics rõ ràng:

```text
checked
wrapping
saturating
```

Ví dụ:

```axiom
x.checked_add(y)?
```

hoặc operator mặc định theo profile/defined language semantics.

Không được để compiler tùy ý biến overflow thành arbitrary behavior.

---

# 30. Bounds failure

Safe indexing:

```axiom
a[i]
```

nếu compiler không chứng minh `i < len`:

```text
bounds check
```

Nếu fail:

```text
panic/trap
```

Không phải:

```text
memory corruption
```

---

# 31. Unchecked access

System code có thể:

```text
unsafe
```

để bỏ bounds check.

Ví dụ conceptual:

```axiom
unsafe {
    a.get_unchecked(i)
}
```

Programmer chịu invariant:

```text
0 <= i < len
```

---

# 32. Division by zero

Safe operation:

```text
a / b
```

với `b == 0`:

```text
panic/trap
```

Nếu muốn recoverable:

```text
checked_div
```

→ `Option`/`Result`.

---

# 33. Panic message

Panic message không nên yêu cầu heap allocation.

Có thể:

```text
panic("division by zero")
```

là static string.

Formatting panic:

```text
panic_fmt(...)
```

là library/runtime feature.

---

# 34. Panic payload

Không nên có arbitrary:

```text
panic(Box<dyn Any>)
```

như mô hình exception payload.

Core panic có thể là:

```text
PanicInfo
```

với:

```text
message
source location
module
function
```

Runtime/debugger có thể sử dụng.

---

# 35. Binary size

Release profile có thể chọn:

```text
panic = abort
```

để bỏ:

- unwind tables
- unwinder
- personality functions
- landing pads

nếu target cho phép.

Đây là một trong những cách Axiom đạt executable nhỏ.

---

# 36. Unwind không được bắt buộc

Một chương trình:

```axiom
fn main() {
    ...
}
```

không dùng panic/unwind.

Compiler có thể:

```text
không link unwinder
không link panic runtime
```

---

# 37. Panic runtime modular

Runtime components:

```text
libaxiom_panic_abort
libaxiom_panic_unwind
```

conceptually.

Nhưng final executable chỉ link cái cần.

---

# 38. Freestanding

Freestanding program:

```text
panic
```

có thể:

```text
trap
```

hoặc:

```text
abort
```

mà không cần OS runtime.

Ví dụ kernel/bootloader.

---

# 39. `never`

Đã có:

```text
never
```

cho computation không trở lại.

Ví dụ:

```axiom
fn abort() -> never
```

Sau đó:

```axiom
let x = abort()
```

có thể type-check trong mọi compatible context.

---

# 40. `trap`

Cần phân biệt:

```text
panic
```

và:

```text
trap
```

### Panic

Language/runtime semantic failure.

### Trap

Machine/execution-domain termination.

Ví dụ:

```text
invalid instruction
hardware fault
explicit trap
```

System layer có thể expose:

```axiom
trap()
```

→ `never`.

---

# 41. Hardware fault

Không nên cố biến mọi hardware fault thành `Result`.

Ví dụ:

```text
page fault
illegal instruction
general protection fault
```

thuộc OS/machine layer.

Axiom không giả định portable recovery.

---

# 42. Signal/SEH

Platform có thể catch:

```text
SIGSEGV
SEH
Mach exception
```

nhưng đó là platform runtime layer.

Không phải Core error mechanism.

---

# 43. FFI boundary

Đã thống nhất:

```text
Axiom panic
```

không tự xuyên qua:

```text
extern "C"
```

boundary.

Ngược lại foreign exception cũng không tự trở thành Axiom panic.

---

# 44. C `errno`

FFI wrapper:

```text
C API
 ↓
errno
 ↓
Axiom Result
```

Ví dụ:

```axiom
fn open(...) -> Result<File, IoError>
```

Wrapper chuyển foreign convention thành Axiom convention.

Core không cần hiểu `errno`.

---

# 45. Windows error codes

Tương tự:

```text
GetLastError()
```

→ wrapper:

```text
Result<T, WindowsError>
```

Không đưa Windows error semantics vào Core.

---

# 46. Async cancellation

Cancellation không phải error.

```text
cancel()
```

là control operation.

Future có thể:

```text
drop
```

nhưng external operation vẫn có thể đang chạy.

Do đó cancellation API phải explicit.

---

# 47. Cancellation result

Library có thể định nghĩa:

```text
Cancelled
```

trong Result:

```text
Result<T, AsyncError>
```

nhưng Core không coi cancellation là panic.

---

# 48. Thread cancellation

Không có:

```text
force_kill_thread()
```

an toàn trong Core.

Thread cancellation là cooperative/system-level.

Không được force-free stack/resources của thread đang chạy.

---

# 49. Process failure

`process::exit(code)`:

```text
never
```

và không phải panic.

Ví dụ:

```axiom
if invalid_config {
    process.exit(2)
}
```

Đây là explicit termination.

---

# 50. Error taxonomy hoàn chỉnh

```text
                         Failure
                            │
             ┌──────────────┼──────────────┐
             │              │              │
        Recoverable      Exceptional     Fatal
             │              │              │
          Result          Panic          Trap
          Option           │              │
                           ├─ abort       └─ machine/process
                           └─ unwind
```

Và:

```text
Cancellation
```

là control state riêng, không nằm trong taxonomy trên.

---

# 51. Exception hoàn toàn bị loại khỏi Core

Tôi đề xuất freeze:

> **Axiom Core v1 không có `throw`, `try`, `catch`, exception hierarchy hoặc implicit exception propagation.**

Nếu một package muốn mô phỏng exception-style API, nó có thể xây bằng:

```text
Result
state machine
callbacks
task/future
```

nhưng không được yêu cầu compiler runtime exception machinery.

---

# 52. Tại sao mô hình này hợp với mục tiêu Axiom?

Vì có hai đường rất rõ:

### Normal application

```text
Result<T,E>
```

### Low-level system

```text
panic
trap
abort
unsafe
```

Không có "nửa safe nửa hidden".

---

# 53. Compiler lowering

`Result`:

```text
source
 ↓
match / ?
 ↓
CFG
 ↓
MIR
 ↓
branch
```

Panic:

```text
panic
 ↓
PANIC MIR
 ↓
abort/unwind lowering
```

Không có:

```text
exception object lookup
catch search
```

trong abort profile.

---

# 54. Unwind lowering

Nếu profile unwind:

```text
MIR
 ↓
cleanup edges
 ↓
landing pads
 ↓
target unwind ABI
```

Drop elaboration đã tồn tại nên compiler biết chính xác:

```text
which values initialized
which moved
which must Drop
```

---

# 55. Panic không phá optimizer

Compiler vẫn có thể:

```text
inline
DCE
constant fold
branch elimination
tail call
```

vì panic path là explicit semantic CFG edge.

---

# 56. Panic cold path

Compiler có thể đánh dấu:

```text
panic path = cold
```

để:

```text
hot code
```

không bị phình bởi error machinery.

---

# 57. `Result` optimization

Compiler có thể tối ưu:

```text
Result<T,E>
```

thông qua:

- niche representation
- register return
- branch prediction hints
- enum layout optimization
- scalar replacement

nhưng representation vẫn private.

---

# 58. `Option`/`Result` không nhất thiết tăng binary size

Ví dụ:

```text
Option<NonNull<T>>
```

có thể dùng null niche.

```text
Result<usize, SmallError>
```

có thể fit vào register.

Zero-cost abstraction vẫn là mục tiêu.

---

# 59. Error context

Không đưa stacktrace bắt buộc vào mỗi Error.

Library có thể:

```text
Error
 ├── kind
 ├── message
 ├── source
 └── cause
```

nhưng application lựa chọn.

Không mandatory heap-linked error chain.

---

# 60. Error source location

Compiler có thể tự thêm debug metadata:

```text
file
line
column
function
```

nhưng release build có thể strip.

Error semantic không phụ thuộc debug symbols.

---

# 61. Invariants BOOTSTRAP-035

```text
AERR-20   Recoverable failure uses Result.

AERR-21   Absence uses Option.

AERR-22   Result is an ordinary algebraic type.

AERR-23   Option is an ordinary algebraic type.

AERR-24   Error propagation via ? is explicit control-flow lowering.

AERR-25   ? does not perform stack unwinding.

AERR-26   Recoverable errors do not require heap allocation.

AERR-27   Panic is distinct from recoverable failure.

AERR-28   Panic is not an exception object.

AERR-29   Core v1 has no throw/catch exception system.

AERR-30   Panic policy is configurable.

AERR-31   Abort is a valid panic policy.

AERR-32   Unwind is an optional panic policy.

AERR-33   Unwind is not required for ordinary programs.

AERR-34   Programs not using unwind need not link an unwinder.

AERR-35   Panic paths may be optimized as cold paths.

AERR-36   Panic does not imply heap allocation.

AERR-37   Drop runs during unwind for initialized owned resources.

AERR-38   Moved values are not dropped.

AERR-39   Partial-move state is respected during unwind.

AERR-40   User-defined destructive Drop restricts partial moves.

AERR-41   Drop does not return recoverable errors.

AERR-42   Cleanup failure is distinct from recoverable business failure.

AERR-43   Panic during active unwind terminates the execution domain.

AERR-44   Thread panic is observable through join.

AERR-45   Detached execution has an explicit panic policy.

AERR-46   Async panic follows normal panic semantics.

AERR-47   Future polling does not convert panic into Result.

AERR-48   Cancellation is distinct from panic.

AERR-49   Cancellation is distinct from Result failure.

AERR-50   Process exit is explicit and distinct from panic.

AERR-51   Trap is distinct from panic.

AERR-52   Hardware faults are not portable Result values.

AERR-53   Foreign exceptions do not automatically become Axiom panic.

AERR-54   Axiom panic does not implicitly cross foreign ABI boundaries.

AERR-55   FFI wrappers may convert foreign error conventions into Result.

AERR-56   Allocation failure may be represented as Result.

AERR-57   Fatal allocation policy may be configured independently.

AERR-58   OOM does not require a global exception mechanism.

AERR-59   Safe bounds failures cannot silently corrupt memory.

AERR-60   Unchecked access is an explicit unsafe operation.

AERR-61   Integer overflow semantics are defined, not C-style accidental UB.

AERR-62   Error representation remains compiler-controlled.

AERR-63   Result/Option layout may be optimized.

AERR-64   Panic implementation is runtime-optional.

AERR-65   Freestanding programs may use trap/abort without an OS runtime.

AERR-66   Panic metadata is separable from semantic error values.

AERR-67   Debug stack traces are not mandatory runtime semantics.

AERR-68   Error propagation does not require exception tables.

AERR-69   Unwind metadata is emitted only when the selected panic/ABI profile requires it.

AERR-70   Panic policy does not change Result semantics.

AERR-71   Compiler optimization cannot remove observable recoverable errors.

AERR-72   Compiler may eliminate unreachable panic paths when proven impossible.

AERR-73   Error handling does not require a monolithic runtime.

AERR-74   Core failure mechanisms remain usable in freestanding environments.

AERR-75   Core v1 intentionally excludes general exception handling.
```

---

# Chốt BOOTSTRAP-035

Mô hình Axiom lúc này rất sạch:

```text
               NORMAL CONTROL
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
       Option                Result
    "có/không"             "ok/error"
          │                     │
          └──────────┬──────────┘
                     ↓
                     ?

             ABNORMAL CONTROL
                     │
                   panic
                  /     \
               abort   unwind
                         │
                        Drop

             MACHINE CONTROL
                     │
                    trap
```

**Không có exception system trong Core.**

Đây cũng giúp giữ đúng mục tiêu ban đầu của Axiom: **mạnh nhưng không để complexity của compiler/runtime biến thành complexity của ngôn ngữ**.

---

## BOOTSTRAP-036 tiếp theo

Tiếp theo là **Attributes, Compiler Directives & Intrinsics**.

Đây là phần rất đáng làm ngay vì từ các task vừa rồi ta đã có rất nhiều annotation:

```text
@repr(...)
@export(...)
@align(...)
@packed
@inline
@noinline
@cold
@kernel
@tls
@naked
@interrupt
@syscall
@test
@cfg
@derive(...)
```

Cần gom lại thành **một hệ thống attribute thống nhất**, đồng thời quyết định cái gì là:

- language semantic,
- compiler hint,
- ABI contract,
- target-specific attribute,
- intrinsic,
- unsafe/system-only,

để Axiom không biến thành một mớ `@xxx` không kiểm soát.