Tiếp tục.

# Axiom — Error Handling, Failure & Panic Model v0.1

Sau ownership, resource, concurrency và allocation, đây là mảnh ghép cuối để hoàn thiện semantics của **failure**.

Tôi đề xuất Axiom giữ mô hình rất rõ:

> **Recoverable failure = giá trị (`Result`/`Option`).  
> Programmer error / violated runtime condition = `panic`.  
> Catastrophic process failure = `abort`/OS termination.**

Không đưa exception kiểu C++/Java vào Core.

---

# 1. Ba loại failure

```text
                         Failure
                            │
              ┌─────────────┼─────────────┐
              │             │             │
         Recoverable     Contract       Fatal
           failure       violation      failure
              │             │             │
           Result          panic          abort
              │             │             │
          handled         policy        process
```

Ví dụ:

### Recoverable

```text
file not found
network timeout
invalid user input
GPU unavailable
database rejected
```

→ `Result<T, E>`

### Panic

```text
index out of bounds
division by zero
invalid internal invariant
failed assertion
```

→ `panic`

### Fatal

```text
process explicitly aborts
unrecoverable runtime failure
panic=abort
```

→ process termination.

---

# 2. `Result<T,E>` là abstraction trung tâm

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Ví dụ:

```axiom
fn read_file(path: Text) -> Result<Text, FileError>
```

Caller:

```axiom
let text = read_file(path)?
```

---

# 3. `?` không phải exception

Đây là điểm rất quan trọng.

```axiom
let data = read_file(path)?
```

về semantic tương đương:

```axiom
match read_file(path) {
    Ok(x) => x,
    Err(e) => return Err(e),
}
```

Compiler sau đó tối ưu.

Không có:

```text
throw
stack unwinding
exception object
handler table
```

trong happy path.

---

# 4. `Result` có thể zero-cost

Ví dụ:

```axiom
fn divide(a: i32, b: i32) -> Result<i32, DivError>
```

Compiler có thể biểu diễn:

```text
return value + status
```

hoặc:

```text
register pair
```

hoặc tận dụng:

```text
niche representation
```

tùy ABI.

Không bắt buộc heap allocation.

---

# 5. Error object không cần heap

Sai lầm cần tránh:

```text
Error
  ↓
heap allocation
  ↓
dynamic object
```

Axiom:

```text
Error
  ↓
enum / struct / integer / small value
```

Ví dụ:

```axiom
enum FileError {
    NotFound,
    PermissionDenied,
    Io(i32),
}
```

có thể chỉ là vài bytes.

---

# 6. Error type nên là value

Không cần:

```text
IError
ExceptionBase
Throwable
```

Không có exception hierarchy.

Thay vào đó:

```axiom
enum HttpError {
    Timeout,
    Connection,
    InvalidResponse,
}
```

---

# 7. Không có `AnyError` trong Core

Không nên có:

```text
Result<T, AnyError>
```

như abstraction bắt buộc.

Nếu cần type-erased error:

```text
Box<dyn Error>
```

có thể là library abstraction.

Static error types vẫn là mặc định.

---

# 8. Generic error propagation

Ví dụ:

```axiom
fn load() -> Result<Data, AppError> {
    let file = File.open(path)?
    let text = file.read_text()?
    parse(text)?
}
```

Các `?` được lower thành control flow.

Compiler không cần runtime exception machinery.

---

# 9. Error conversion

Ta cần cho phép:

```text
FileError
    ↓
AppError
```

nhưng **không implicit arbitrary conversion**.

Ví dụ trait:

```axiom
trait From<T> {
    fn from(value: T) -> Self
}
```

Compiler có thể cho `?` thực hiện conversion nếu có `From`.

Conceptually:

```text
Err(e)
 ↓
AppError.from(e)
 ↓
return Err(...)
```

---

# 10. Nhưng tránh conversion chain vô hạn

Không cho:

```text
A → B → C → D → ...
```

compiler tự tìm hàng chục conversion.

`?` chỉ nên dùng:

```text
identity
```

hoặc:

```text
one explicit From conversion
```

Nếu ambiguous → compile error.

---

# 11. `Option<T>`

```axiom
enum Option<T> {
    Some(T),
    None,
}
```

Dùng khi:

> absence là trạng thái bình thường, không phải failure.

Ví dụ:

```axiom
fn find(id: Id) -> Option<Item>
```

---

# 12. Không dùng `null`

Giữ nguyên:

```text
null
```

không tồn tại trong safe Core.

Thay:

```text
T*
```

bằng:

```text
Option<T>
```

nếu cần biểu diễn absence của value.

Raw null pointer chỉ:

```text
unsafe / FFI
```

---

# 13. `Option<T>` có thể zero-cost

Ví dụ:

```text
Option<&T>
```

trong các ngôn ngữ khác có thể niche-optimize thành pointer/null.

Axiom cũng cho phép:

```text
Option<T>
```

được representation-optimize khi observable semantics không thay đổi.

Không cần object wrapper.

---

# 14. `panic`

`panic` biểu diễn:

> chương trình không thể tiếp tục theo contract thông thường.

Ví dụ:

```axiom
panic("internal invariant violated")
```

Nhưng message không nhất thiết tạo heap string.

Compiler có thể dùng static data:

```text
.rodata
```

---

# 15. Bounds failure

```axiom
let x = a[i]
```

nếu không chứng minh:

```text
i < len(a)
```

compiler chèn bounds check.

Nếu fail:

```text
panic
```

Không phải undefined behavior trong safe code.

---

# 16. Compiler có thể loại bỏ bounds check

Ví dụ:

```axiom
for i in 0..a.len() {
    sum += a[i]
}
```

Compiler chứng minh:

```text
0 <= i < len(a)
```

→ bỏ check.

Do đó safe code không đồng nghĩa với:

```text
mọi array access đều chậm
```

---

# 17. Integer overflow

Đã chốt:

```text
+      checked
+%     wrapping
+|     saturating
```

Ví dụ:

```axiom
let x = a + b
```

overflow:

```text
panic/trap
```

Trong khi:

```axiom
let x = a +% b
```

wrap.

---

# 18. Không dùng C-style signed overflow UB

Axiom phải tránh:

```text
"compiler được phép giả định overflow không xảy ra"
```

vì điều đó làm semantics khó dự đoán.

Axiom có semantics rõ ràng.

---

# 19. Division

```text
a / b
```

với:

```text
b == 0
```

→ panic/trap.

Trường hợp signed:

```text
MIN / -1
```

nếu không representable:

→ panic/trap.

---

# 20. Shift

```text
x << n
```

nếu `n` ngoài phạm vi:

→ panic/trap.

Nếu muốn wrapping shift:

```text
x <<% n
```

hoặc API tương đương.

Không cần compiler-dependent behavior.

---

# 21. `panic` không phải `Result`

Không nên viết:

```axiom
fn parse() -> Result<T, Panic>
```

cho mọi runtime condition.

Ví dụ:

```text
invalid user input
```

→ `Result`.

Còn:

```text
internal impossible state
```

→ `panic`.

---

# 22. Assertion

Hai mức:

```axiom
assert(condition)
```

→ semantic runtime check.

```axiom
debug_assert(condition)
```

→ có thể bị loại trong release profile.

Nhưng `debug_assert` không được dùng để bảo vệ safety invariants mà safe compiler cần.

---

# 23. `unreachable`

```axiom
unreachable()
```

có type:

```text
never
```

và runtime behavior:

```text
trap
```

Compiler được dùng nó để tối ưu control flow.

---

# 24. `never`

Ví dụ:

```axiom
fn fail() -> never {
    panic("failure")
}
```

`never` hợp nhất với control-flow types.

Ví dụ:

```axiom
let x =
    if condition {
        42
    } else {
        panic("...")
    }
```

type:

```text
i32
```

---

# 25. Không biến `never` thành subtype hierarchy

`never` chỉ là:

> computation không tạo ra normal value.

Không cần general subtype system.

---

# 26. Panic strategy

Axiom cần hai profile cơ bản:

```text
panic=abort
panic=unwind
```

---

# 27. `panic=abort`

```text
panic
 ↓
cleanup required resources
 ↓
terminate process
```

Ưu điểm:

- binary nhỏ;
- runtime đơn giản;
- dễ freestanding;
- phù hợp embedded;
- không cần unwind tables đầy đủ.

Đây nên là lựa chọn rất quan trọng cho systems programming.

---

# 28. `panic=unwind`

```text
panic
 ↓
stack unwinding
 ↓
Drop resources
 ↓
catch boundary nếu abstraction cho phép
```

Tuy nhiên tôi **không muốn mở `try/catch` tổng quát** trong Core chỉ vì có unwind.

---

# 29. Unwind không đồng nghĩa exception language

Đây là hai khái niệm khác nhau:

```text
panic
 ↓
unwind
```

là implementation/control-flow mechanism.

Còn:

```text
throw
catch
finally
exception hierarchy
```

là application error model.

Axiom chỉ cần cái đầu.

---

# 30. Có catch panic không?

Tôi đề xuất:

> **Không có general `catch` trong Core v0.1.**

Nếu cần isolation boundary:

```text
panic::catch(...)
```

có thể là library/runtime API.

Ví dụ:

```axiom
let result = panic::catch(|| risky())
```

nhưng đây là **explicit boundary**, không biến panic thành application error mặc định.

---

# 31. Vì sao không có `try/catch`?

Vì nó tạo rất nhiều semantic baggage:

```text
exception tables
handler lookup
stack unwinding
destructor ordering
cross-FFI rules
async exception propagation
thread exception propagation
```

Trong khi:

```text
Result + ?
```

đã giải quyết phần lớn recoverable errors.

---

# 32. Async + Result

Đây là mô hình rất sạch:

```axiom
async fn fetch() -> Result<Data, Error>
```

và:

```axiom
let data = fetch().await?
```

Hai cơ chế độc lập:

```text
await
    → suspension

?
    → failure propagation
```

---

# 33. Async + panic

Nếu future panic:

```text
Future
 ↓
panic
 ↓
executor boundary
```

policy quyết định:

```text
abort
```

hoặc:

```text
task failure
```

với unwind-capable runtime.

---

# 34. Task panic

Một task không nên mặc định làm crash cả process nếu executor có isolation semantics.

Có thể:

```text
TaskHandle.join()
```

nhận:

```text
TaskResult<T>
```

trong đó panic là failure của task.

Nhưng `panic=abort` vẫn có quyền kết thúc process.

---

# 35. Thread panic

Tương tự:

```text
thread.spawn(...)
```

và:

```text
join()
```

có thể quan sát task/thread failure.

Không có exception propagation xuyên thread.

---

# 36. GPU errors

GPU API:

```axiom
fn launch(...) -> Result<GpuEvent, GpuError>
```

Không:

```text
throw GpuException
```

GPU asynchronous errors có thể xuất hiện khi:

```text
await event
```

hoặc:

```text
event.wait()
```

---

# 37. FFI errors

C:

```text
NULL
-1
errno
HRESULT
error code
```

được wrapper chuyển thành:

```text
Result<T, Error>
```

Safe Axiom không để C error convention lan ra toàn bộ application.

---

# 38. OS errors

Ví dụ:

```axiom
File.open(path)
```

→:

```text
Result<File, FileError>
```

`FileError` có thể giữ platform code:

```text
code: i32
kind: FileErrorKind
```

---

# 39. Không cần exception object

OS failure:

```text
ENOENT
```

không cần:

```text
new Exception(...)
```

Có thể chỉ là:

```text
enum + integer
```

---

# 40. OOM

OOM là trường hợp đặc biệt.

Có thể:

```text
try_allocate()
    → Result
```

cho system code.

High-level:

```text
Vec.push()
```

có thể:

```text
panic/abort
```

theo allocation failure policy.

---

# 41. Không được để OOM đi qua Drop

Nếu:

```text
Drop
```

cần allocate để cleanup thì đó là thiết kế resource không tốt.

Axiom nên khuyến nghị:

> **Drop phải có khả năng cleanup mà không cần recoverable allocation.**

---

# 42. Destructor failure

Đã chốt:

```text
Drop -> no Result
```

Ví dụ file:

```text
let f = File.open(...)?
```

Nếu muốn biết `close` thành công:

```axiom
f.close()?
```

Không chờ:

```text
Drop
```

báo lỗi.

---

# 43. `close()` + Drop

Pattern:

```text
OPEN
 │
 ├── close() -> CLOSED
 │
 └── Drop → cleanup if still OPEN
```

Nếu `close()` đã thành công:

```text
Drop
    ↓
no-op
```

hoặc minimal state cleanup.

---

# 44. Tại sao không cho Drop trả Result?

Vì:

```text
function returns Err
    ↓
Drop during propagation
    ↓
Drop returns another Err
```

sẽ tạo:

```text
error while handling error
```

rất khó định nghĩa.

Axiom tránh từ gốc.

---

# 45. `?` + Drop

Ví dụ:

```axiom
fn process() -> Result<(), Error> {
    let file = File.open(path)?
    let data = file.read()?
    save(data)?
    Ok(())
}
```

Nếu:

```text
read() → Err
```

compiler:

```text
cleanup data
cleanup file
return Err
```

Không cần programmer viết cleanup.

---

# 46. Đây là một trong những lợi thế lớn nhất của ownership model

Source:

```text
3 lines
```

Semantic MIR:

```text
CALL open
CHECK result
CALL read
CHECK result
DROP file
RETURN error
```

Compiler tự insert cleanup.

---

# 47. Error path vẫn deterministic

Không có:

```text
hidden GC
```

hay:

```text
exception handler magically freeing resources
```

Mọi resource có Drop semantics rõ ràng.

---

# 48. Error type design

Axiom nên ưu tiên:

```text
small enum
small struct
```

Ví dụ:

```axiom
enum ParseError {
    UnexpectedToken,
    InvalidNumber,
    UnexpectedEnd,
}
```

Không:

```text
dynamic inheritance tree
```

---

# 49. Error context

Có thể có:

```text
ParseError {
    kind: ParseErrorKind,
    location: Span,
}
```

`Span` có thể là:

```text
file_id
offset
length
```

Không cần heap.

---

# 50. Rich error chains

Application layer có thể xây:

```text
AppError
 ├── Config
 ├── Database
 ├── Network
 └── Io
```

hoặc:

```text
source: Box<dyn Error>
```

nếu thật sự cần dynamic polymorphism.

Nhưng không phải Core requirement.

---

# 51. No implicit error conversion

Không:

```text
fn f() -> Result<T, E1>

call returning E2

?
```

tự động convert bằng magic.

Chỉ khi compiler thấy:

```text
From<E2> for E1
```

hoặc explicit conversion.

---

# 52. `?` chỉ áp dụng cho Result/Option-like protocols

Không nên hard-code quá nhiều.

Có thể compiler-known:

```text
Result
Option
```

và sau này một generalized `Try` trait nếu thực sự cần.

Nhưng v0.1 tôi khuyên:

> **Chỉ Result và Option.**

Đơn giản hơn.

---

# 53. `?` trên Option

Ví dụ:

```axiom
fn find_name() -> Option<Text> {
    let user = find_user()?
    let name = user.name()?
    Some(name)
}
```

`None` propagate.

---

# 54. `?` không biến Option thành Result

Không implicit:

```text
None
 ↓
Error
```

Nếu cần:

```axiom
let x = optional()?
```

chỉ hoạt động trong function trả compatible Option.

---

# 55. Error propagation qua async

```axiom
async fn load() -> Result<Data, Error> {
    let x = read().await?
    Ok(x)
}
```

Compiler lower:

```text
async state machine
+
Result control flow
+
Drop cleanup
```

Ba hệ thống phối hợp nhưng không phụ thuộc semantic lẫn nhau.

---

# 56. Error propagation qua thread

```text
thread
 ↓
Result<T,E>
 ↓
join()
```

không cần exception.

Ví dụ:

```axiom
let h = thread.spawn(|| work())
let result = h.join()?? 
```

Có thể có hai lớp error:

```text
ThreadError
WorkError
```

API nên thiết kế để không tạo cú pháp `????`.

Library có thể cung cấp:

```text
join_result()
```

hoặc một error wrapper.

---

# 57. Tôi không khuyến khích syntax đặc biệt cho việc này

Không thêm:

```text
join!?
```

hay:

```text
try_join
```

vào Core.

Library composition là đủ.

---

# 58. Error handling không nên ảnh hưởng ABI quá mức

`Result<T,E>` là ordinary enum.

Compiler ABI lowering có thể biến thành:

```text
value + discriminant
```

hoặc niche.

Không cần runtime object.

---

# 59. Error path coldness

Compiler có thể nhận biết:

```text
Err(...)
panic(...)
```

là cold path.

Codegen có thể:

```text
hot path → compact
cold path → outlined
```

Ví dụ:

```text
if unlikely(error) {
    call cold_error_handler()
}
```

Nhưng đây là optimization, không thay đổi semantics.

---

# 60. Không mặc định heap-allocate panic message

Sai:

```text
panic("...")
 ↓
heap String
 ↓
runtime exception object
```

Đúng:

```text
static message
source location
optional formatting
```

---

# 61. Panic metadata

Compiler có thể tạo:

```text
PanicInfo {
    code
    message
    file
    line
    column
}
```

Trong release tối ưu:

```text
message/debug info
```

có thể được strip nếu policy cho phép.

---

# 62. `panic=abort` binary rất nhỏ

Ví dụ embedded:

```text
panic
 ↓
write diagnostic if configured
 ↓
trap/abort
```

Không cần:

- unwind tables;
- exception handler;
- dynamic runtime.

Đây là một lợi thế lớn.

---

# 63. `panic=unwind` vẫn không cần C++ exceptions

Axiom có thể có **Axiom-native unwind ABI**.

Compiler-generated Drop cleanup:

```text
cleanup landing pads
```

và unwind metadata.

Không cần tương thích C++ exception ABI trừ khi FFI adapter riêng.

---

# 64. FFI boundary

Không để panic tự nhiên xuyên qua C ABI.

Ví dụ:

```text
Axiom → extern C
```

nếu Axiom function panic:

```text
panic
 ↓
FFI boundary
```

phải có policy.

Tôi đề xuất:

> **Panic không được unwind xuyên FFI boundary mặc định.**

Nó phải:

```text
abort
```

hoặc được catch trước boundary.

---

# 65. Ngược lại C callback vào Axiom

Nếu callback Axiom panic:

```text
C
 ↓
Axiom callback
 ↓
panic
```

wrapper phải chặn boundary.

Không để C stack nhận Axiom unwind.

---

# 66. Đây là ABI invariant rất quan trọng

```text
AFERR-01  Result Represents Recoverable Failure
AFERR-02  Option Represents Absence
AFERR-03  Null Is Not A Safe Error Representation
AFERR-04  ? Is Control-Flow Propagation
AFERR-05  ? Does Not Require Exception Runtime
AFERR-06  Result Has Value Semantics
AFERR-07  Result Does Not Require Heap Allocation
AFERR-08  Error Values Are Ordinary Types
AFERR-09  Error Conversion Is Explicitly Constrained
AFERR-10  ? Uses At Most A Direct Compatible Error Conversion
AFERR-11  Panic Represents Non-Recoverable Program Failure
AFERR-12  Panic Is Distinct From Result
AFERR-13  Bounds Failure In Safe Code Is Defined
AFERR-14  Arithmetic Failure Is Defined
AFERR-15  Unreachable Has Never Type
AFERR-16  Assertions Are Explicit Runtime Checks
AFERR-17  Debug Assertions Are Not Safety Guarantees
AFERR-18  Panic Does Not Imply Exception Language
AFERR-19  Panic Strategy Is Configurable
AFERR-20  Abort Requires No Unwind Runtime
AFERR-21  Unwind Is Optional
AFERR-22  General Try/Catch Is Not Core v0.1
AFERR-23  Panic Catching Is An Explicit Boundary
AFERR-24  Panic Does Not Cross FFI Boundaries By Default
AFERR-25  Thread Panic Is Observed Through Thread Boundary
AFERR-26  Async Panic Is Observed Through Task Boundary
AFERR-27  GPU Failure Uses Explicit Result Semantics
AFERR-28  OS Failure Uses Explicit Result Semantics
AFERR-29  FFI Failure Is Wrapped By Explicit Contracts
AFERR-30  Drop Is Not Fallible
AFERR-31  Drop Does Not Return Result
AFERR-32  Explicit close May Return Result
AFERR-33  Resource Cleanup Occurs During Error Propagation
AFERR-34  Error Propagation Preserves Deterministic Cleanup
AFERR-35  OOM Is Distinct From Ordinary Resource Cleanup
AFERR-36  Allocation APIs May Provide Fallible Variants
AFERR-37  Panic Messages Need Not Be Heap Allocated
AFERR-38  Error Types Need Not Be Dynamically Allocated
AFERR-39  Error Handling Has No Mandatory Global Runtime
AFERR-40  Error Paths May Be Outlined As Optimization
AFERR-41  Error Optimization Cannot Change Observable Semantics
AFERR-42  Result/Option Are Compiler-Optimizable Ordinary Types
```

---

# 67. Một vấn đề còn phải quyết định: `try/catch` có thực sự cần không?

Ở v0.1 tôi đề xuất **không**.

Ta có:

```text
Result
Option
?
panic
abort
unwind
```

Đã đủ để biểu diễn:

```text
application errors
system errors
I/O errors
network errors
GPU errors
async errors
thread errors
resource cleanup
program invariant failures
```

Exception có thể xuất hiện sau này như một **library/runtime mechanism**, nhưng không được trở thành semantic foundation.

---

# 68. Error model hoàn chỉnh

```text
                       Axiom Failure Model
                              │
             ┌────────────────┼─────────────────┐
             │                │                 │
        Recoverable        Panic             Fatal
             │                │                 │
          Result            policy             abort
          Option              │
             │         ┌──────┴──────┐
             │         │             │
             │       abort        unwind
             │
          `?`
             │
        control flow
             │
        automatic Drop
```

Điểm quan trọng là **không có một global exception mechanism nằm giữa mọi thứ**.

---

# 69. Bây giờ Axiom đã có một semantic loop khá hoàn chỉnh

```text
Value
  ↓
Ownership
  ↓
Storage
  ↓
Resource
  ↓
Concurrency
  ↓
Failure
  ↓
Cleanup
  ↓
Ownership ends
```

Ví dụ:

```axiom
fn process(path: Text) -> Result<Data, Error> {
    let file = File.open(path)?
    let data = file.read()?
    process_data(data)
}
```

Compiler có thể biến thành:

```text
open
 ↓
ownership = file
 ↓
read
 ↓
success ────────────────┐
 ↓                      │
process                 │
 ↓                      │
success                  │
 ↓                      │
Drop(file)              │
 ↓                      │
return data             │
                        │
error ───────────────┐  │
                     ↓  │
                 Drop(file)
                     ↓
                return Err
```

Không GC.

Không exception object.

Không manual cleanup.

Không borrow syntax.

Không hidden runtime bắt buộc.

---

# 70. Một nguyên tắc Axiom rất đáng giữ

> **Failure propagation should be explicit in source, but cleanup should be implicit in compiler semantics.**

Tức là programmer thấy:

```text
?
```

nhưng không phải viết:

```text
close()
free()
unlock()
release()
```

ở mọi nhánh.

Đây là sự cân bằng rất tốt giữa **predictability** và **ergonomics**.

---

# Tiếp tục: Language Surface & Syntax v0.1

Hiện tại chúng ta đã thiết kế gần như toàn bộ semantic engine phía dưới. Bước tiếp theo không nên tiếp tục thêm feature ngẫu nhiên.

Cần chuyển sang việc **đóng băng hình thức của ngôn ngữ**:

```text
module
import
struct
enum
trait
impl
fn
let
var
match
if
for
while
closure
async
await
unsafe
comptime
const
static
view
mut_view
generic
attribute
```

và quan trọng nhất:

> **Viết một “Axiom Language Specification v0.1” thống nhất từ lexer → parser → type system → ownership → concurrency → runtime, để sau đó compiler agent có thể dùng chính spec này làm contract và bắt đầu implement.**

Phần đó sẽ giúp phát hiện những chỗ mà các quyết định trước đây đang **mâu thuẫn syntax hoặc semantic**, thay vì tiếp tục thêm feature một cách rời rạc.