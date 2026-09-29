# BOOTSTRAP-092 — Error, Result, Panic, Cancellation & Failure Architecture

**Trạng thái: FROZEN**

Mục tiêu của phần này là thống nhất toàn bộ failure model của Axiom mà **không cần exception system kiểu C++/Java**, không bắt buộc runtime, không hidden allocation và không biến mọi lỗi thành `Result` dài dòng.

Nguyên tắc:

> **Recoverable failure là dữ liệu.  
> Panic là vi phạm invariant/programmer failure.  
> Cancellation là control-flow request.  
> Trap/abort là terminal machine/process failure.**

Bốn loại này không được nhập làm một.

---

# 1. Failure Taxonomy

Axiom phân loại failure thành:

```text
                 FAILURE
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
  Recoverable    Panic       Terminal
       │            │            │
     Result      panic()     trap/abort
       │
       └──── Cancellation là một
             control-flow state
```

Cụ thể:

| Loại | Ý nghĩa | Cách xử lý |
|---|---|---|
| `Result<T,E>` | thao tác có thể thất bại bình thường | caller xử lý |
| `Option<T>` | có/không có giá trị | caller xử lý |
| `panic` | invariant/programmer failure | panic policy |
| `trap` | lỗi máy/không thể tiếp tục | target behavior |
| `abort` | kết thúc execution domain/process | runtime/system |
| cancellation | yêu cầu dừng computation | cooperative |

---

# 2. Result

Core:

```text
enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

Đây chỉ là ADT bình thường.

Không có:

```text
exception object
stack unwinding metadata
global error runtime
```

trong `Result`.

Ví dụ:

```text
let file = File.open(path)?
```

về semantic tương đương:

```text
match File.open(path) {
    Ok(file) => ...
    Err(e) => return Err(e)
}
```

`?` chỉ là control-flow sugar.

---

# 3. Result không bắt buộc allocation

Ví dụ:

```text
Result<u64, IOError>
```

có thể nằm hoàn toàn trong:

```text
register
```

hoặc stack.

Compiler có thể biến:

```text
Result<T,E>
```

thành ABI:

```text
return value + status
```

hoặc:

```text
register pair
```

hoặc target-specific convention.

Không có requirement:

```text
heap allocation
```

---

# 4. Result không phải exception

Exception:

```text
throw
 ↓
search handler
 ↓
unwind
 ↓
catch
```

Result:

```text
call
 ↓
return Result
 ↓
caller decides
```

Axiom chọn mô hình thứ hai cho recoverable failure.

Điều này làm control flow explicit và compiler dễ tối ưu.

---

# 5. Option

`Option<T>` biểu diễn:

```text
Some(T)
None
```

Không được dùng:

```text
null
```

để biểu diễn absence trong safe Core.

Ví dụ:

```text
let player = players.get(id)
```

trả:

```text
Option<view<Player>>
```

Nếu object không tồn tại:

```text
None
```

Đây là **expected state**, không phải error.

---

# 6. Option và Result phải khác nhau

Ví dụ:

```text
get(id)
```

không tìm thấy:

```text
None
```

Trong khi:

```text
read(file)
```

OS báo lỗi:

```text
Err(IOError)
```

Không nên dùng:

```text
Option<Result<T,E>>
```

một cách tùy tiện nếu semantics không thực sự cần ba trạng thái.

---

# 7. Panic

`panic` dành cho:

> chương trình đã vi phạm invariant mà caller bình thường không thể/không nên recover.

Ví dụ:

```text
assert(index < len)
```

nếu invariant đã được programmer/compiler yêu cầu nhưng bị vi phạm.

Panic **không phải** API bình thường cho:

```text
file not found
network timeout
user input invalid
resource unavailable
```

những trường hợp này nên là `Result`.

---

# 8. Panic không phải Exception

Axiom không có:

```text
try
catch
throw
finally
```

trong Core v1.

Panic chỉ kích hoạt:

```text
PanicPolicy
```

của execution profile.

Ví dụ:

```text
debug → diagnostic + unwind
release → abort
freestanding → trap
```

Đây là policy, không phải semantics của `Result`.

---

# 9. Panic Payload

Axiom không yêu cầu panic phải tạo một exception object.

Có thể:

```text
panic("message")
```

nhưng compiler/runtime có thể triển khai:

```text
static string
error code
source location
```

mà không allocation.

Panic payload là implementation/profile concern.

---

# 10. Panic có thể unwind

Axiom cho phép hai profile chính:

```text
PanicAbort
PanicUnwind
```

Nếu unwind:

```text
panic
 ↓
stack unwinding
 ↓
Drop initialized resources
 ↓
handler / thread termination
```

Nếu abort:

```text
panic
 ↓
terminate execution domain
```

Không được để code phụ thuộc vào một profile cụ thể nếu API muốn portable.

---

# 11. Drop trong Panic

Nếu panic unwind:

```text
var a = ResourceA()
var b = ResourceB()

panic()
```

compiler phải cleanup:

```text
b.Drop()
a.Drop()
```

theo ownership/drop semantics.

Nếu:

```text
a
```

đã Move:

```text
```

thì không Drop lại.

Nếu partial move:

```text
```

chỉ drop những subobject vẫn owned.

---

# 12. Panic trong Drop

Axiom tiếp tục giữ nguyên quyết định:

> **Drop không được phép tạo recoverable failure.**

Nếu user-defined Drop gây panic trong quá trình panic unwind:

```text
panic A
 ↓
Drop
 ↓
panic B
```

execution domain phải:

```text
terminate/abort
```

theo panic policy.

Không tạo nested-unwind complexity vô hạn.

---

# 13. `Result` trong Drop không được bỏ qua

Ví dụ:

```text
file.close() -> Result
```

không thể biến thành:

```text
Drop(file) -> silently ignore Result
```

và coi đó là semantic equivalent.

Thay vào đó:

```text
close()
```

phải được gọi explicit nếu caller cần biết failure.

Drop chỉ cung cấp fallback cleanup không-fallible.

---

# 14. `?` Operator

Axiom giữ `?`.

Ví dụ:

```text
fn load() -> Result<Data, Error> {
    let file = File.open(path)?
    let data = file.read_all()?
    return Ok(parse(data)?)
}
```

`?` làm:

```text
Ok(x)  → x
Err(e) → return Err(e)
```

Compiler có thể lower trực tiếp thành CFG/MIR.

Không cần exception machinery.

---

# 15. `?` không chỉ dành cho Result

Có thể hỗ trợ:

```text
Option<T>
```

với semantics:

```text
Some(x) → x
None   → return None
```

Nhưng conversion giữa:

```text
Option
Result
```

phải explicit hoặc dựa trên trait/control-flow protocol rõ ràng.

Không tự động tạo error message.

---

# 16. Error Type

Không cần một:

```text
Error
```

base class toàn hệ thống.

Ví dụ:

```text
enum FileError {
    NotFound,
    PermissionDenied,
    InvalidPath,
    Io(SystemError)
}
```

hoặc:

```text
struct NetworkError {
    kind: NetworkErrorKind
    code: i32
}
```

Static typing cho phép compiler biết chính xác error domain.

---

# 17. Error không cần inheritance

Không có:

```text
class IOError : Error
class NetworkError : IOError
```

Thay vào đó:

```text
enum Error {
    Io(IOError),
    Network(NetworkError),
    Parse(ParseError)
}
```

hoặc generic abstraction:

```text
Result<T, E>
```

Traits cung cấp behavior chung:

```text
Display
Debug
Source
```

---

# 18. Error Context

Không cần exception stack để thêm context.

Có thể:

```text
return Err(error.with_context("loading config"))
```

hoặc library:

```text
Context<Result<T,E>>
```

Nhưng context creation phải explicit.

Không tự động build một heap-allocated exception chain cho mọi `Result`.

---

# 19. Error Conversion

Generic code đôi khi cần:

```text
Result<T, FileError>
```

chuyển thành:

```text
Result<T, AppError>
```

Axiom cho phép trait conversion:

```text
From<FileError> for AppError
```

và `?` có thể sử dụng conversion contract nếu compiler xác định được.

Không có implicit arbitrary conversion chain.

---

# 20. Error Stack Trace

Stack trace không phải semantic requirement của `Result`.

Toolchain có thể cung cấp:

```text
debug information
source maps
unwind information
```

để debugger tạo stack trace.

Release binary có thể:

```text
strip debug info
```

mà semantics của `Result` không thay đổi.

---

# 21. Allocation Failure / OOM

Axiom không có global:

```text
OutOfMemoryException
```

Khi allocation có thể thất bại, API có thể:

```text
Result<T, AllocError>
```

Ví dụ:

```text
let buffer = Buffer.try_new(size)?
```

Một API cấp thấp có thể dùng:

```text
allocate_unchecked
```

hoặc policy terminate.

---

# 22. Không ép mọi allocation thành Result

Điều này quan trọng để API không trở nên khó chịu.

Có thể có hai API:

```text
Buffer.new(size)
```

và:

```text
Buffer.try_new(size)
```

Trong đó:

```text
new
```

có thể panic/abort khi allocation không thể thực hiện theo contract.

Còn:

```text
try_new
```

trả:

```text
Result
```

Library API quyết định semantics cụ thể.

---

# 23. Bounds Failure

Safe indexing:

```text
array[i]
```

phải bảo đảm không tạo memory corruption.

Nếu compiler không chứng minh:

```text
i < len
```

thì operation có thể:

```text
panic
```

hoặc API có:

```text
get(i) -> Option<T>
```

Đây là hai semantics khác nhau:

```text
index = programmer asserts valid
get   = absence-aware query
```

---

# 24. `unchecked` Access

System code cần:

```text
array.get_unchecked(i)
```

thì phải là unsafe.

Compiler không được tự hiểu:

```text
unsafe = no checks everywhere
```

Unsafe chỉ bỏ qua/provide contract cho một operation cụ thể.

Các verifier khác vẫn hoạt động.

---

# 25. Integer Overflow

Đã frozen ở numeric model:

Arithmetic bình thường có deterministic failure semantics.

Ví dụ:

```text
u8
255 + 1
```

không được trở thành C-style UB.

Có thể có:

```text
checked_add
wrapping_add
saturating_add
```

và compiler có thể loại bỏ checked operation khi range proof chứng minh an toàn.

---

# 26. Division by Zero

Không có undefined behavior trong safe Core.

```text
x / 0
```

là arithmetic failure.

Compiler có thể:

```text
panic
trap
```

theo defined numeric/panic profile.

Unchecked machine operation phải đi qua unsafe/system semantics nếu được phép.

---

# 27. Cancellation

Cancellation không phải Error.

Ví dụ:

```text
Result<T, Error>
```

không nhất thiết:

```text
Error::Cancelled
```

trừ khi API domain muốn biểu diễn cancellation như một failure result.

Ở Core semantic level:

```text
Cancellation
```

là:

> request yêu cầu computation dừng khi đạt cancellation point.

---

# 28. Cooperative Cancellation

Axiom không hỗ trợ:

```text
kill thread immediately
```

như một primitive safe.

Cancellation:

```text
request_cancel()
```

sau đó computation:

```text
check cancellation
        ↓
stop cooperatively
```

Điều này tránh phá invariant ownership/resource.

---

# 29. Cancellation Token

Library:

```text
CancellationToken
CancellationSource
```

Ví dụ:

```text
async fn download(
    token: CancellationToken
) -> Result<Data, DownloadError>
```

Trong operation:

```text
if token.is_cancelled() {
    return Err(DownloadError::Cancelled)
}
```

Việc cancellation được encode thành `Result` hay một control-flow type khác là API-level decision.

---

# 30. Cancellation và Drop

Không:

```text
drop(future) == cancel
```

đã frozen.

Tương tự:

```text
drop(token)
```

không tự cancel mọi computation nếu token semantics không quy định.

Explicit source:

```text
source.cancel()
```

mới yêu cầu cancellation.

---

# 31. Timeout

Timeout là một loại condition riêng.

Ví dụ:

```text
read(timeout)
```

có thể:

```text
Result<Data, IoError>
```

với:

```text
IoError::Timeout
```

hoặc:

```text
TimeoutResult<T>
```

Library quyết định.

Core không cần `Timeout` primitive.

---

# 32. Deadline

Deadline khác timeout:

```text
timeout = duration
deadline = absolute point
```

Ví dụ:

```text
request(deadline)
```

nhiều operation có thể dùng chung deadline:

```text
DB query
 ↓
network
 ↓
filesystem
```

không cần cộng/trừ duration liên tục.

Đây là Standard Library concern.

---

# 33. Thread Failure

Thread:

```text
spawn(fn() -> T)
```

có thể:

```text
complete(T)
panic
```

`JoinHandle<T>` có thể trả:

```text
Result<T, JoinError>
```

Ví dụ:

```text
match handle.join() {
    Ok(value) => ...
    Err(error) => ...
}
```

Thread panic không tự panic caller.

Caller quyết định.

---

# 34. Async Failure

Future:

```text
Future<Result<T,E>>
```

có thể có:

```text
Ready(Ok(T))
Ready(Err(E))
Pending
```

Panic là một execution failure khác.

Không cần:

```text
Future<ExceptionObject>
```

---

# 35. Future cancellation

Một Future có thể bị:

```text
dropped
```

mà không đồng nghĩa external operation cancelled.

Nếu abstraction cần:

```text
cancel()
```

phải có cancellation contract.

Nếu Future sở hữu state nội bộ:

```text
Drop(Future)
```

vẫn phải Drop toàn bộ state đã initialized.

---

# 36. GPU Failure

GPU operation có thể fail sau khi submit.

Ví dụ:

```text
gpu.submit(...)
```

không nhất thiết phát hiện mọi lỗi ngay.

Do đó:

```text
GpuEvent.wait()
```

có thể:

```text
Result<(), GpuError>
```

Điều này khác:

```text
panic
```

vì device failure có thể là recoverable hoặc policy-dependent.

---

# 37. FFI Failure

Foreign function:

```text
extern fn foo(...) -> int
```

không tự động được coi là:

```text
Result
```

Wrapper có thể map:

```text
0  → Ok
-1 → Err
```

nhưng mapping phải nằm trong wrapper.

Không có magic ABI-level exception conversion.

---

# 38. Foreign Exception

Nếu gọi C++/foreign runtime có exception:

```text
foreign()
```

Axiom không tự động:

```text
foreign exception → Axiom Result
```

hoặc:

```text
foreign exception → panic
```

FFI boundary phải dùng adapter/ABI contract.

Axiom panic cũng không tự động đi qua foreign ABI.

---

# 39. Process Exit

Process exit không phải:

```text
Result
```

của mọi function.

System layer:

```text
process.exit(code)
```

là terminal control-flow.

Compiler không cần unwind toàn bộ application trước khi `exit` nếu API semantics quy định immediate termination.

---

# 40. Trap

`trap` dành cho machine/semantic terminal condition.

Ví dụ:

```text
unreachable
hardware fault abstraction
fatal arithmetic trap
```

Trap không nhất thiết có recoverable handler.

Target có thể:

```text
SIGILL
access violation
WASM trap
CPU exception
```

nhưng Axiom semantic model không phụ thuộc vào một OS cụ thể.

---

# 41. Abort

`abort`:

> kết thúc execution domain ngay lập tức theo profile.

Không đảm bảo:

```text
Drop all values
flush all files
run cleanup
```

Vì vậy programmer không nên dùng abort như resource management mechanism.

---

# 42. Panic / Trap / Abort

Ba mức:

```text
panic
  ↓
program-level invariant failure

trap
  ↓
machine/execution-level terminal failure

abort
  ↓
explicit immediate termination
```

Target backend có thể map một số trường hợp, nhưng source semantics phải giữ distinction.

---

# 43. Error Propagation không dùng hidden exception edges

MIR:

```text
x = call()
```

nếu:

```text
Result<T,E>
```

thì `?` lower thành explicit CFG:

```text
Call
 ↓
Switch Ok/Err
 ├── Ok → continue
 └── Err → return
```

Do đó:

- optimizer thấy control flow;
- branch prediction có thể tối ưu;
- inlining hoạt động;
- dead branch elimination hoạt động;
- no hidden exception table bắt buộc.

---

# 44. Error Path Optimization

Compiler có thể đánh dấu:

```text
Err path cold
```

thông qua:

```text
@cold
```

hoặc inferred profile.

Ví dụ:

```text
read_file()
```

happy path:

```text
Ok
```

error path:

```text
Err
```

có thể được layout thành cold block.

Không thay đổi semantics.

---

# 45. Result Niche Optimization

Do `Option`/`Result` là ADT, compiler có thể tối ưu representation.

Ví dụ:

```text
Option<NonNull<T>>
```

có thể dùng niche.

Tương tự một số:

```text
Result<T,E>
```

có thể có compact ABI.

Nhưng:

```text
representation
```

không được trở thành semantic contract trừ khi explicit `repr`.

---

# 46. Error Domain không cần Runtime Registration

Không có:

```text
register_error_type()
```

hay:

```text
global exception registry
```

Error type là static type.

Điều này rất phù hợp với:

```text
freestanding
embedded
kernel
WASM
```

---

# 47. No Global Error Handler bắt buộc

Không có:

```text
global_error_handler
```

cho mọi `Result`.

Application có thể xây:

```text
main() -> Result<(), AppError>
```

và runtime/startup wrapper xử lý kết quả cuối cùng.

Ví dụ:

```text
fn main() -> Result<(), AppError>
```

→ startup có thể:

```text
Ok    → exit 0
Err   → report + exit nonzero
```

nhưng đây là hosted profile.

---

# 48. `main -> Result`

Axiom khuyến nghị hỗ trợ:

```text
fn main() -> Result<(), AppError>
```

để application không phải:

```text
match ...
```

toàn bộ lỗi ở entry point.

Compiler/startup layer có thể cung cấp termination adapter.

Freestanding profile có thể định nghĩa entry ABI riêng.

---

# 49. Error + Resource Cleanup

Ví dụ:

```text
fn process() -> Result<(), Error> {
    let file = File.open(path)?
    let buffer = Buffer.new()?

    process(file, buffer)?

    Ok(())
}
```

Nếu `process()` trả `Err`:

```text
buffer.Drop()
file.Drop()
return Err
```

Compiler tự elaborate Drop.

Không cần:

```text
finally
```

---

# 50. Error + Move

Ví dụ:

```text
let file = File.open(path)?

let result = consume(file)

return result
```

Nếu `consume` đã Move `file`, error path không được Drop `file` lần nữa.

Ownership dataflow quyết định chính xác.

Đây là một ưu điểm lớn của việc Axiom đã xây ownership trước error architecture.

---

# 51. Error + Partial Move

Ví dụ:

```text
struct Transaction {
    connection: Connection,
    metadata: Metadata
}
```

Nếu:

```text
let connection = transaction.connection
```

thì trên error path compiler chỉ cleanup:

```text
metadata
```

nếu `connection` đã được Move.

Không double Drop.

---

# 52. Error + Capability

Nếu:

```text
let v = view(buffer)
```

và function trả `Err`, capability phải kết thúc đúng trước khi owner bị Drop.

Compiler không cho:

```text
Drop(buffer)
while v is live
```

ngay cả trên error edge.

Do đó:

```text
normal path
error path
panic path
```

đều đi qua cùng capability verifier.

---

# 53. Error + Async

Future state machine chứa:

```text
buffer
file
request
```

Nếu Future hoàn thành:

```text
Ready(Err(e))
```

các state field phải được cleanup đúng.

Không có:

```text
leaked state
```

và không cần GC.

---

# 54. Error + GPU

Nếu GPU command:

```text
in-flight
```

trả error:

```text
GpuError
```

thì resource lifetime vẫn phải được giữ cho tới completion/error acknowledgement theo contract.

Không được:

```text
Err
 ↓
release buffer
 ↓
GPU still accesses buffer
```

---

# 55. Unified Failure Model

Toàn bộ hệ thống có thể nhìn như:

```text
Operation
    │
    ├── success
    │      ↓
    │    T
    │
    ├── expected failure
    │      ↓
    │    Result<T,E>
    │
    ├── absence
    │      ↓
    │    Option<T>
    │
    ├── cancellation
    │      ↓
    │    cooperative stop
    │
    ├── invariant violation
    │      ↓
    │    panic
    │
    └── terminal execution failure
           ↓
        trap / abort
```

---

# 56. Quy tắc lựa chọn

Axiom nên có mental model cực đơn giản:

```text
"Có thể không có?"
        ↓
Option

"Có thể thất bại và caller xử lý?"
        ↓
Result

"Programmer invariant bị phá?"
        ↓
panic

"Execution không thể tiếp tục?"
        ↓
trap

"Tôi muốn kết thúc ngay?"
        ↓
abort

"Tôi muốn yêu cầu computation dừng?"
        ↓
cancellation
```

Đây chính là **One Semantic Question, One Mechanism**.

---

# 57. Không có `throws`

Axiom không cần:

```text
fn foo() throws Error
```

vì:

```text
fn foo() -> Result<T,E>
```

đã encode failure statically.

Điều này cũng khiến function signature machine-readable:

```text
FunctionType
    return = Result<T,E>
```

AI/compiler/IDE có thể hiểu chính xác.

---

# 58. Không có exception hierarchy

Không có:

```text
Throwable
Exception
RuntimeException
IOException
...
```

Core chỉ cần:

```text
Result<T,E>
Option<T>
panic
trap
abort
```

Library tự định nghĩa error domains.

---

# 59. Không có implicit catch

Không có behavior:

```text
foo()
```

tự động tìm enclosing:

```text
catch
```

Mọi recoverable error đều nằm trong type/control flow.

Điều này làm call graph dễ phân tích.

---

# 60. Optimizer có thể tận dụng failure semantics

Compiler có thể biết:

```text
Result<T,E>
```

và:

```text
Err path cold
```

hoặc:

```text
panic path unreachable under proven invariant
```

Sau range/type/dataflow analysis:

```text
bounds check
```

có thể biến mất.

Ví dụ:

```text
for i in 0..array.len {
    array[i]
}
```

range proof:

```text
0 ≤ i < len
```

→ không cần runtime bounds check.

---

# 61. Structured Diagnostics

Error compiler phải phân biệt:

```text
user Result
runtime failure
panic
compiler error
compiler ICE
```

Ví dụ:

```text
AERR-xxx
```

không được trộn với:

```text
ACOMP-xxx
```

Một compiler bug:

```text
Internal Compiler Error
```

không được báo như:

```text
program panic
```

---

# 62. Frozen Invariants

## Result / Option

**AFAIL-20 — Recoverable Failure Is Represented As Data**

**AFAIL-21 — Result Is A Normal Algebraic Type**

**AFAIL-22 — Option Represents Absence, Not General Failure**

**AFAIL-23 — Result Does Not Require Heap Allocation**

**AFAIL-24 — `?` Is Explicit Control-Flow Lowering**

**AFAIL-25 — Error Propagation Does Not Require Exception Runtime**

**AFAIL-26 — Result Error Types Are Statically Typed**

**AFAIL-27 — Arbitrary Implicit Error Conversion Is Forbidden**

---

## Panic

**AFAIL-28 — Panic Represents Program-Level Invariant Failure**

**AFAIL-29 — Panic Is Distinct From Recoverable Result Failure**

**AFAIL-30 — Panic Does Not Require An Exception Object**

**AFAIL-31 — Panic Policy May Be Abort Or Unwind**

**AFAIL-32 — Panic Unwind Must Respect Ownership And Drop Semantics**

**AFAIL-33 — Panic During Active Unwind Terminates According To Panic Policy**

**AFAIL-34 — Panic Is Not A General Error-Propagation Mechanism**

---

## Drop

**AFAIL-35 — Drop Is Non-Fallible**

**AFAIL-36 — Fallible Cleanup Requires Explicit API**

**AFAIL-37 — Drop Runs On Required Error Paths**

**AFAIL-38 — Moved Values Are Never Dropped Again**

**AFAIL-39 — Partial Move Cleanup Follows Ownership State**

**AFAIL-40 — Drop Does Not Imply Physical Deallocation**

---

## Cancellation

**AFAIL-41 — Cancellation Is Distinct From Error Semantics**

**AFAIL-42 — Cancellation Is Distinct From Panic**

**AFAIL-43 — Cancellation Is Cooperative By Default**

**AFAIL-44 — Forced Thread Termination Is Not A Safe Core Primitive**

**AFAIL-45 — Dropping A Future Does Not Imply External Cancellation**

**AFAIL-46 — Explicit Cancellation Contracts Define Cancellation Behavior**

---

## Async / Thread

**AFAIL-47 — Async Failure Is Representable Through Future Output**

**AFAIL-48 — Thread Failure Is Observable Through Join Semantics**

**AFAIL-49 — Thread Panic Does Not Implicitly Panic The Joining Thread**

**AFAIL-50 — Future State Is Cleaned According To Ownership Semantics**

**AFAIL-51 — Cancellation Does Not Bypass Resource Cleanup**

---

## Arithmetic / Memory

**AFAIL-52 — Safe Arithmetic Failure Is Deterministic**

**AFAIL-53 — Division By Zero Has Defined Failure Semantics**

**AFAIL-54 — Safe Bounds Failure Cannot Cause Memory Corruption**

**AFAIL-55 — Unchecked Memory Operations Require Unsafe/System Semantics**

---

## FFI / External

**AFAIL-56 — Foreign Exceptions Do Not Automatically Become Axiom Results**

**AFAIL-57 — Axiom Panic Does Not Automatically Cross Foreign ABI Boundaries**

**AFAIL-58 — FFI Error Conversion Requires An Explicit Adapter**

**AFAIL-59 — Foreign Failure Semantics Are Defined By The FFI Contract**

---

## Terminal

**AFAIL-60 — Trap Is Distinct From Panic**

**AFAIL-61 — Abort Is Distinct From Panic And Trap**

**AFAIL-62 — Abort Does Not Guarantee Normal Resource Cleanup**

**AFAIL-63 — Process Exit Is Distinct From Function-Level Result Failure**

---

## Performance

**AFAIL-64 — Result Propagation Has No Mandatory Heap Cost**

**AFAIL-65 — Result May Be Returned In Target ABI Registers**

**AFAIL-66 — Error Paths May Be Optimized As Cold Paths**

**AFAIL-67 — Proven Failure Conditions May Be Eliminated**

**AFAIL-68 — Panic Machinery Is Not Required For Programs Whose Profile Does Not Use It**

**AFAIL-69 — Exception Runtime Is Not A Core Requirement**

---

## Compiler

**AFAIL-70 — Failure Control Flow Is Represented Explicitly In MIR**

**AFAIL-71 — Error Paths Participate In Ownership Verification**

**AFAIL-72 — Error Paths Participate In Capability Verification**

**AFAIL-73 — Error Paths Participate In Drop Elaboration**

**AFAIL-74 — Async Error Paths Participate In Future-State Cleanup**

**AFAIL-75 — GPU/External Failure Paths Preserve In-Flight Lifetime Guarantees**

**AFAIL-76 — Compiler Failure Is Distinct From Program Failure**

**AFAIL-77 — Failure Semantics Are Deterministic**

---

# 63. Axiom Failure Model sau BOOTSTRAP-092

Ta hiện có một hệ thống khá sạch:

```text
                     Axiom Operation
                            │
              ┌─────────────┼─────────────┐
              │             │             │
           Success       Recoverable    Absent
              │          Failure          │
              ▼             ▼             ▼
              T         Result<T,E>    Option<T>
                            │
                            │
                     ┌──────┴──────┐
                     │             │
                 propagate      handle
                     │
                     ▼
                    `?`

             ┌─────────────────────┐
             │   Exceptional       │
             │   execution states  │
             └──────────┬──────────┘
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
            panic      trap      abort

             ┌─────────────────────┐
             │    Cancellation     │
             │ cooperative control │
             └─────────────────────┘
```

Điểm đáng chú ý là Axiom **không cần một “Exception System”** để có error handling hiện đại.

`Result` + `Option` + `panic` + `cancellation` + `trap/abort` đủ để bao phủ gần như toàn bộ failure domain, trong khi compiler có thể lower chúng thành CFG/MIR thông thường.

---

### Kiến trúc tiếp theo

Sau BOOTSTRAP-092, phần nền tảng tiếp theo nên là:

# **BOOTSTRAP-093 — Axiom API Design, Ergonomics & Syntax Architecture**

Tập trung vào một câu hỏi rất quan trọng: **Axiom hiện đã có semantic model mạnh, nhưng code thực tế có trở nên dài và “Rust-like” quá không?**

Ta sẽ thiết kế cách viết sao cho các thứ như:

```text
ownership
view
mut_view
Result
Option
Handle
traits
generics
async
concurrency
comptime
GPU
```

được **compiler xử lý mạnh phía sau**, còn syntax mà lập trình viên nhìn thấy vẫn ngắn, tự nhiên và dễ cho cả người lẫn AI viết.