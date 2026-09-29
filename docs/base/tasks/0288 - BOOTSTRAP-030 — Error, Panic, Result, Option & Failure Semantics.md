Tiếp tục với **BOOTSTRAP-030 — Error, Panic, Result, Option & Failure Semantics**.

Đây là phần rất quan trọng. Tôi đề xuất Axiom **không có exception system trong Core**, nhưng cũng không để programmer phải viết quá nhiều boilerplate.

Mục tiêu:

> **Recoverable failure = `Result`; absence = `Option`; unrecoverable failure = `panic`/`trap`; propagation = `?`; cleanup luôn deterministic.**

---

# BOOTSTRAP-030 — Error, Panic, Result, Option & Failure Semantics

## 1. Ba loại "không thành công" phải tách rõ

Axiom phân biệt:

```text
Option<T>
    không có giá trị

Result<T, E>
    thao tác thất bại và có thông tin lỗi

panic/trap
    chương trình không thể tiếp tục theo semantic contract
```

Ví dụ:

```axiom
fn find_user(id: u64) -> Option<User>
```

không tìm thấy user là trạng thái bình thường.

Trong khi:

```axiom
fn read_file(path: str) -> Result<File, IOError>
```

có thể thất bại vì:

- file không tồn tại
- permission
- I/O error
- filesystem error.

---

# 2. `Option<T>`

Semantic:

```text
Option<T>
    = Some(T)
    | None
```

Ví dụ:

```axiom
let x = map.get(key)

match x {
    Some(value) => use(value)
    None => ...
}
```

Không có `null` trong safe Core.

---

# 3. `Result<T,E>`

Semantic:

```text
Result<T, E>
    = Ok(T)
    | Err(E)
```

Ví dụ:

```axiom
fn divide(a: i32, b: i32) -> Result<i32, MathError>
```

Không dùng exception.

---

# 4. `Option` và `Result` nên là enum chuẩn

Không cần compiler primitive riêng cho semantics.

Compiler chỉ cần **nhận biết chúng đủ sâu để tối ưu**.

Ví dụ:

```axiom
enum Option<T> {
    Some(T),
    None
}

enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

Sau monomorphization + optimization, chúng có thể trở thành:

```text
register
branch
conditional move
```

không cần heap allocation.

---

# 5. `Option<T>` không có nghĩa luôn thêm một byte/tag

Compiler có thể sử dụng **niche optimization**.

Ví dụ một type có representation dư:

```text
Option<NonNull<T>>
```

có thể biểu diễn:

```text
null      = None
non-null  = Some(ptr)
```

Nhưng đây là implementation optimization.

Không cho programmer phụ thuộc vào layout mặc định.

Điều này phù hợp với BOOTSTRAP-023.

---

# 6. `Result<T,E>` cũng có thể tối ưu

Ví dụ:

```axiom
fn parse() -> Result<u32, ParseError>
```

compiler có thể đưa:

```text
value
+
error/tag
```

vào registers hoặc stack.

Không:

```text
heap allocate Error object
throw exception
unwind runtime
```

---

# 7. `?` là cơ chế cực kỳ quan trọng

Axiom nên hỗ trợ:

```axiom
let data = read_file(path)?
let text = String.from_utf8(data)?
let value = parse(text)?
return value
```

Semantic:

```text
match expression {
    Ok(x) => x
    Err(e) => return Err(e)
}
```

Không có hidden exception.

---

# 8. `?` phải zero-cost

Sau lowering:

```text
Result
   ↓
branch
   ↓
success path
failure path
```

Optimizer có thể inline toàn bộ.

Không cần:

```text
exception table
stack unwinding
heap error object
runtime dispatch
```

cho `Result`.

---

# 9. Error conversion

Đây là nơi có thể gây boilerplate.

Ví dụ:

```axiom
fn load() -> Result<Data, AppError> {
    let bytes = read_file(path)?
    let text = String.from_utf8(bytes)?
    ...
}
```

`IOError` và `Utf8Error` phải có cách chuyển thành `AppError`.

Đề xuất trait:

```axiom
trait FromError<E> {
    fn from_error(e: E) -> Self
}
```

và `?` có thể thực hiện conversion:

```text
Err(E)
 ↓
FromError<E>
 ↓
Err(AppError)
```

nhưng **chỉ khi conversion duy nhất và deterministic**.

Không chạy arbitrary conversion chain.

---

# 10. Không có implicit conversion chain

Không cho:

```text
E1 → E2 → E3 → E4 → AppError
```

tự động.

Chỉ:

```text
E → TargetError
```

một bước.

Điều này giữ diagnostics dễ hiểu.

---

# 11. Error type không cần class hierarchy

Không cần:

```text
Exception
 ├── IOError
 ├── NetworkError
 └── ParseError
```

Thay:

```axiom
enum AppError {
    Io(IOError),
    Parse(ParseError),
    Network(NetworkError),
}
```

hoặc struct error phù hợp.

Pattern matching xử lý rất rõ.

---

# 12. Error có thể rất nhỏ

Ví dụ:

```axiom
enum IOErrorKind {
    NotFound,
    PermissionDenied,
    Interrupted,
    Other,
}
```

`IOError` có thể chứa:

```text
kind
OS error code
```

Không cần object allocation.

---

# 13. Error message không bắt buộc

Đây là một quyết định quan trọng cho binary size.

Không phải mọi error đều phải chứa:

```text
String message
```

Core error có thể chỉ là:

```text
error code
```

Message formatting thuộc library/debug layer.

Ví dụ release build có thể bỏ:

```text
"Permission denied while opening..."
```

nếu không cần.

---

# 14. Error metadata có thể compile-time

Compiler có thể cung cấp:

```text
ErrorCode
ErrorName
SourceLocation
```

nhưng runtime chỉ giữ những gì programmer yêu cầu.

Ví dụ:

```axiom
#[error(code = 1001)]
PermissionDenied
```

hoặc một syntax tương đương sau này.

Không cần chốt attribute syntax ngay.

---

# 15. `panic`

`panic` nghĩa là:

> computation không thể tiếp tục theo semantic contract hiện tại.

Ví dụ:

```axiom
panic("unreachable state")
```

Không phải cơ chế error handling thông thường.

---

# 16. Bounds check

Ví dụ:

```axiom
let x = array[i]
```

nếu compiler không chứng minh `i` hợp lệ:

```text
bounds check
```

Nếu fail:

```text
panic
```

Compiler có thể eliminate check khi chứng minh được:

```text
0 <= i < len
```

---

# 17. `panic` phải có nhiều runtime profile

Đề xuất:

```text
abort
unwind
custom
```

### `abort`

```text
panic → terminate process
```

nhỏ nhất, phù hợp embedded/freestanding.

### `unwind`

```text
panic
 ↓
unwind scopes
 ↓
Drop resources
 ↓
catch boundary nếu profile/API cho phép
```

Nhưng Core **không có exception catch**.

Unwind chủ yếu để:

- cleanup
- thread/task boundary
- testing/runtime policy.

---

# 18. Không có `catch` trong Core

Không:

```axiom
try {
    ...
}
catch e {
    ...
}
```

Nếu failure recoverable:

```text
Result
```

Nếu programmer muốn xử lý panic:

```text
runtime boundary / task boundary
```

có API explicit.

Ví dụ:

```text
task.join()
```

có thể trả:

```text
TaskResult<T>
```

bao gồm panic observation.

---

# 19. Thread panic

Nếu thread chạy:

```axiom
Thread.spawn(fn() {
    panic("failure")
})
```

panic không nhất thiết giết toàn bộ process.

Thread boundary có thể capture panic state.

```axiom
let result = thread.join()?
```

hoặc API tương ứng.

Điểm quan trọng:

> **panic propagation qua execution boundary là runtime policy, không phải exception propagation.**

---

# 20. Async task panic

Tương tự:

```text
Task
 ↓
panic
 ↓
task becomes failed
 ↓
JoinHandle observes failure
```

Scheduler không tự biến panic thành global process failure.

---

# 21. Detached task

Nếu programmer:

```axiom
spawn_detached(...)
```

thì không có consumer để observe kết quả.

Runtime policy có thể:

```text
log
terminate
discard
custom handler
```

Nhưng phải explicit configuration.

Không silently ignore panic trong mọi profile.

---

# 22. Panic != cancellation

Phải giữ riêng:

```text
panic
cancellation
Result::Err
```

### `Err`

business/operational failure.

### `panic`

program invariant failure / unrecoverable computation.

### cancellation

execution không cần tiếp tục nữa.

Ba semantic khác nhau.

---

# 23. OOM

Một câu hỏi cực kỳ quan trọng:

```text
Vec.push()
```

có thể allocation failure.

Không nên mặc định:

```text
OOM → panic
```

ở mọi môi trường.

Đề xuất allocator API có hai policy.

### Fallible allocation

```axiom
try_reserve(...)
    -> Result<(), AllocError>
```

### Convenience allocation

```axiom
reserve(...)
```

có thể:

```text
allocation failure → panic
```

theo hosted/default profile.

---

# 24. `AllocError`

Core-level semantic error:

```text
AllocError
```

không nhất thiết phải có message.

Ví dụ:

```axiom
match vec.try_push(x) {
    Ok(_) => ...
    Err(AllocError) => ...
}
```

---

# 25. Nhưng không bắt mọi allocation phải Result

Nếu:

```axiom
let v = Vec<i32>()
```

mọi `push` đều:

```axiom
try_push(...)?
```

thì code trở nên rất nặng.

Vì vậy API nên có cả:

```text
push()
try_push()
reserve()
try_reserve()
```

Programmer chọn policy.

---

# 26. Đây là pattern quan trọng của Axiom

Library nên cung cấp:

```text
convenience API
+
fully fallible API
```

Ví dụ:

```text
read_file()
try_read_file()

allocate()
try_allocate()

push()
try_push()
```

Default API có thể panic trên resource exhaustion.

Low-level/server/embedded code dùng fallible API.

---

# 27. Panic không được làm hỏng Drop

Nếu:

```axiom
fn foo() {
    let a = ResourceA()
    let b = ResourceB()

    panic("failure")
}
```

và profile là unwind:

```text
panic
 ↓
drop b
 ↓
drop a
 ↓
unwind
```

Theo reverse initialization order.

---

# 28. Nếu Drop lại panic?

Không nên cho phép nested panic tiếp tục vô hạn.

Nếu:

```text
panic
 ↓
Drop
 ↓
panic
```

thì:

```text
terminate/abort
```

theo panic runtime policy.

Không có:

```text
panic stack
panic stack
panic stack
...
```

---

# 29. Drop không trả Result

Đã đóng băng:

```text
Drop = non-fallible
```

Không:

```axiom
fn drop(self) -> Result<(), Error>
```

Nếu cleanup có thể fail:

```axiom
resource.close()?
```

sau đó Drop chỉ là fallback cleanup.

Ví dụ:

```axiom
let file = File.open(path)?

file.flush()?
file.close()?
```

hoặc library có semantic tương ứng.

---

# 30. Resource cleanup và business error tách biệt

Đây là nguyên tắc:

```text
Resource cleanup
    ↓
Drop

Business-level failure
    ↓
Result
```

Không trộn hai thứ.

---

# 31. `Option` convenience API

Các API nên có:

```text
unwrap()
expect()
unwrap_or()
unwrap_or_else()
map()
map_or()
and_then()
```

Nhưng đây là library methods.

`unwrap()`:

```text
Some → value
None → panic
```

`expect()`:

```text
None → panic with diagnostic message
```

---

# 32. `Result` convenience API

Tương tự:

```text
unwrap()
expect()
map()
map_err()
and_then()
or_else()
unwrap_or()
```

Tất cả có thể inline.

---

# 33. Không cần `try` keyword

Không:

```axiom
try read_file()
```

Axiom dùng:

```axiom
read_file()?
```

và explicit `Result`.

Điều này làm control flow nhìn thấy ngay tại call site.

---

# 34. Không cần `throw`

Không có:

```axiom
throw error
```

Thay:

```axiom
return Err(error)
```

Hoặc:

```axiom
return Ok(value)
```

Compiler biết chính xác control flow.

---

# 35. Không có hidden exceptions

Đây là một invariant cực quan trọng:

```text
Result<T,E>
    không tạo hidden stack-unwind path
```

Một function:

```axiom
fn foo() -> Result<T,E>
```

chỉ có failure path qua semantic Result.

---

# 36. Nhưng `panic` vẫn có thể xảy ra trong function Result

Ví dụ:

```axiom
fn foo() -> Result<i32, Error> {
    let x = array[100]
    ...
}
```

Nếu bounds invalid:

```text
panic
```

Không tự động biến thành:

```text
Err(...)
```

Điều này rất quan trọng.

Nếu programmer muốn recover:

```axiom
array.get(100)
```

có thể trả:

```text
Option<T>
```

---

# 37. API design: checked vs unchecked

Ví dụ array:

```text
array[i]
```

→ checked access.

```text
array.get(i)
```

→ Option.

```text
array.get_unchecked(i)
```

→ unsafe.

Ba semantic khác nhau.

---

# 38. Đây là mô hình rất đẹp cho Axiom

```text
safe convenience
       ↓
       panic

safe explicit
       ↓
    Option/Result

unsafe performance/system
       ↓
unchecked
```

Ví dụ:

```axiom
array[i]                 // panic if invalid
array.get(i)             // Option
unsafe array.get_unchecked(i)
```

Programmer tự chọn trade-off.

---

# 39. Error propagation qua async

Không có cơ chế riêng.

```axiom
async fn load() -> Result<Data, Error> {
    let bytes = read_async()?
    let data = parse(bytes)?
    Ok(data)
}
```

`?` hoạt động bình thường trong async state machine.

Future state machine chỉ lưu state cần thiết.

---

# 40. Error propagation qua thread

Thread return type có thể là:

```text
Thread<T>
```

hoặc:

```text
JoinHandle<T>
```

Nếu function:

```axiom
fn worker() -> Result<Data, Error>
```

thì join:

```text
join()
```

có thể trả:

```text
Result<Result<Data, Error>, JoinError>
```

về mặt semantic.

Library có thể cung cấp flattening convenience.

---

# 41. Panic observation

Một thread có thể có:

```text
JoinError
    ├── Panicked
    └── Cancelled / Terminated / PlatformError
```

Nhưng `Panicked` không nhất thiết chứa full stack trace.

Debug profile có thể attach diagnostics.

Release profile có thể chỉ giữ code/status nhỏ.

---

# 42. FFI errors

Không tự động biến C return code thành Result.

Ví dụ:

```c
int foo(...)
```

Axiom binding:

```axiom
extern "C" fn foo(...) -> i32
```

vẫn trả `i32`.

Safe wrapper:

```axiom
fn foo_safe(...) -> Result<(), FooError>
```

chuyển đổi explicit.

Điều này giữ FFI faithful.

---

# 43. Syscall

Tương tự.

Raw syscall layer:

```text
register → syscall → raw return
```

Safe OS layer:

```text
syscall
 ↓
Result<T, OsError>
```

Hai tầng.

---

# 44. GPU errors

GPU operation:

```text
launch()
```

có thể trả:

```text
Result<GpuEvent, GpuError>
```

Nhưng asynchronous execution failure có thể xuất hiện sau launch.

Do đó:

```text
launch
    ↓
Result<GpuEvent, LaunchError>

event.wait()
    ↓
Result<(), GpuError>
```

Không giả định launch success = kernel success.

---

# 45. Error context

Không nên ép mọi Error phải chứa stack/context.

Library có thể:

```text
Error
 ↓
Context
 ↓
source error
```

nhưng đây là optional.

Một release binary nhỏ có thể dùng:

```text
enum Error {
    NotFound,
    Permission,
    InvalidData,
}
```

---

# 46. Structured diagnostics

Compiler diagnostics và runtime Error là hai thứ khác nhau.

Compiler:

```text
E0007
source location
span
message
help
machine-readable fields
```

Runtime:

```text
ErrorCode
payload
```

Không trộn.

---

# 47. `panic` message

Nên cho:

```axiom
panic("invalid state")
```

và:

```axiom
panic_with(error)
```

nhưng message có thể bị loại bỏ trong size profile nếu không observable theo configuration.

Debug profile giữ source location.

---

# 48. Trap

Cần phân biệt `panic` và machine trap.

```text
panic
    → language-level failure

trap
    → deliberate target-level abnormal termination
```

System code có thể:

```axiom
unsafe trap()
```

hoặc compiler intrinsic.

Ví dụ:

```text
breakpoint
unreachable
illegal instruction
hardware trap
```

không nên biến tất cả thành `panic`.

---

# 49. `unreachable`

Compiler intrinsic:

```axiom
unreachable()
```

nói:

> execution không thể đến đây theo programmer-established invariant.

Nếu execution thực sự tới:

```text
panic/trap
```

tùy profile.

Optimizer được phép tận dụng assumption này.

Do đó phải cực kỳ cẩn thận: `unreachable` không phải `return`.

---

# 50. Error semantics và optimizer

Compiler có thể transform:

```axiom
match result {
    Ok(x) => x + 1,
    Err(e) => return Err(e)
}
```

thành branch machine-level.

Nhưng không được:

```text
remove Err path
```

nếu nó observable.

Ngược lại nếu compiler chứng minh operation không thể fail:

```text
Err path
→ unreachable
→ eliminate
```

được phép.

---

# 51. Error types có thể là zero-cost abstraction

Ví dụ:

```axiom
fn parse_u32(x: str) -> Result<u32, ParseError>
```

có thể compile thành:

```text
register eax = parsed value
register/flag = success
```

Không nhất thiết tạo object.

Đây là điểm quan trọng để Axiom tránh mô hình:

```text
"C++ exception performance"
```

mà vẫn có error handling rõ ràng.

---

# 52. Invariants BOOTSTRAP-030

```text
AERR-20   Option represents absence, not failure.

AERR-21   Result represents recoverable operation failure.

AERR-22   Panic represents unrecoverable language-level failure.

AERR-23   Trap represents target/system-level abnormal control transfer.

AERR-24   Option and Result are algebraic types.

AERR-25   Option does not require heap allocation.

AERR-26   Result does not require heap allocation.

AERR-27   Result propagation with ? preserves explicit control flow.

AERR-28   ? may perform one deterministic error conversion.

AERR-29   Implicit multi-step error conversion is forbidden.

AERR-30   Recoverable failure is not silently converted to panic.

AERR-31   Panic is not silently converted to Result.

AERR-32   Panic does not use ordinary exception semantics.

AERR-33   Core has no general exception catch mechanism.

AERR-34   Panic profile may select abort or unwind behavior.

AERR-35   Unwinding preserves deterministic Drop semantics.

AERR-36   Drop is non-fallible.

AERR-37   Cleanup failure is distinct from business-level failure.

AERR-38   Panic during active unwind terminates according to panic policy.

AERR-39   Bounds-checked access may panic on invalid access.

AERR-40   Explicit checked access may return Option.

AERR-41   Unchecked access is unsafe.

AERR-42   Allocation failure may be exposed through fallible APIs.

AERR-43   Convenience allocation APIs may panic on allocation failure.

AERR-44   Fallible allocation APIs do not require panic.

AERR-45   OOM policy is configurable by runtime/build profile.

AERR-46   Error payloads need not allocate.

AERR-47   Error messages are not mandatory runtime state.

AERR-48   Runtime error diagnostics are distinct from compiler diagnostics.

AERR-49   Thread panic is observable at an execution boundary.

AERR-50   Task panic is observable through its observation capability.

AERR-51   Detached task panic follows explicit runtime policy.

AERR-52   Cancellation is distinct from panic.

AERR-53   Cancellation is distinct from Result::Err.

AERR-54   Async Result propagation uses ordinary Result semantics.

AERR-55   FFI return codes are not implicitly converted to Result.

AERR-56   Safe FFI wrappers may explicitly construct Result.

AERR-57   GPU launch failure is distinct from asynchronous execution failure.

AERR-58   Error handling does not imply exception runtime support.

AERR-59   Error representation is compiler-optimizable.

AERR-60   Panic paths may be optimized when unreachable is proven.

AERR-61   Error semantics remain observable under optimization.

AERR-62   Error types do not require class inheritance.

AERR-63   Error composition can use enums and structs.

AERR-64   Error context is optional library functionality.

AERR-65   Panic messages are optional runtime diagnostics.

AERR-66   Runtime error metadata may be stripped by build profile.

AERR-67   Compiler diagnostics are machine-readable independently of runtime errors.

AERR-68   ? does not create hidden exception/unwind machinery.

AERR-69   Result failure paths remain explicit in MIR.

AERR-70   Option/Result are zero-cost abstraction targets.
```

---

# 53. Mô hình failure hoàn chỉnh

Như vậy Axiom có một cây rất rõ:

```text
                    Computation
                        │
              ┌─────────┼──────────┐
              │         │          │
           success    absence    failure
              │         │          │
              T      Option<T>  Result<T,E>
                                      │
                              recoverable failure
                                     
                        ┌─────────────┐
                        │             │
                      panic         trap
                        │             │
                language failure   machine/system
```

Và:

```text
cancellation
```

nằm **ngoài failure hierarchy**:

```text
Execution
   ├── completed
   ├── Result::Err
   ├── panic
   └── cancelled
```

---

# 54. Một điểm tôi muốn đóng băng mạnh

Axiom **không nên có "exceptions nhưng syntax đẹp hơn"**.

Tức là không tạo một hệ thống:

```text
throw
catch
finally
exception hierarchy
stack unwinding
```

rồi gọi nó là Result.

Thay vào đó:

```text
Result
    ↓
explicit data/control flow

panic
    ↓
exceptional runtime policy
```

Điều này phù hợp với toàn bộ kiến trúc trước đó:

```text
No GC
No mandatory runtime
No hidden allocation
No hidden aliasing
No hidden async
No hidden exception
```

---

# 55. Sau BOOTSTRAP-030

Axiom Core hiện đã giải quyết gần như toàn bộ **data/control/resource semantics**.

Các mảnh lớn còn lại trước khi chuyển sang compiler architecture là:

```text
030 Error / Failure                 ← vừa hoàn thành
031 Generics / Traits nâng cao
032 Closures / Function Values
033 Compile-time / Reflection       ← đã có, cần integration
034 FFI / ABI / C Interop
035 SIMD / Vector / CPU features
036 GPU programming model            ← high-level đã có
037 Atomics / concurrency            ← đã có
038 Attributes / Annotations
039 Unsafe / System / Intrinsics
040 Testing / Contracts / Assertions
041 Debug / Diagnostics / Tooling
042 Serialization / Wire formats
043 Standard Library Architecture
044 Compiler IR / MIR formalization
045 Optimization model
046 Linker / Object / Native backend
047 Runtime component architecture
048 Self-hosting / bootstrap
```

Tôi đề xuất bước tiếp theo là **BOOTSTRAP-031 — Generics, Traits, Associated Types, Specialization & Monomorphization**, vì phần này cần chốt trước compiler type checker và MIR.

Đặc biệt phải giải quyết một vấn đề lớn:

> **Axiom muốn vừa đạt hiệu năng C/C++, vừa tránh trait/generic system phức tạp kiểu Rust/C++, nhưng vẫn phải đủ mạnh để xây `Vec<T>`, `HashMap<K,V>`, GPU tensor, async, numeric code và abstraction zero-cost.**

Đây là một trong những phần có thể quyết định Axiom thực sự "đơn giản nhưng mạnh" hay trở thành một ngôn ngữ type-system quá nặng.