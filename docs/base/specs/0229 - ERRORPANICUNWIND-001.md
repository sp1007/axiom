Tiếp tục với **ERROR/PANIC/UNWIND-001**. Đây là phần cần chốt trước khi đi sâu hơn vào optimizer, vì `Result`, `panic`, `Drop`, `unwind`, `async cancellation` đều tác động trực tiếp đến MIR và runtime.

# ERROR/PANIC/UNWIND-001

Mục tiêu của Axiom:

```text
Recoverable error
    → Result<T, E>

Optional value
    → Option<T>

Programmer-requested unrecoverable failure
    → panic()

Machine/runtime fatal condition
    → trap / abort

Resource cleanup
    → Drop

Cleanup that can itself fail
    → explicit close() -> Result

Stack unwinding
    → optional runtime capability
```

Không có C++-style exception system trong Core.

---

# 1. Ba loại failure phải tách biệt

Axiom không nên gom tất cả thành "exception".

## Recoverable

```text
Result<T, E>
```

Ví dụ:

```text
let file = File.open(path)?
```

Đây là **ordinary control flow**.

---

## Unrecoverable program failure

```text
panic("...")
```

Ví dụ:

```text
assert(index < len)
```

Đây là:

```text
program cannot continue according to current execution contract
```

---

## Machine/runtime fatal failure

Ví dụ:

```text
invalid instruction
hardware fault
stack overflow
OS-level fatal condition
```

→ `trap` / `abort`, tùy target/runtime profile.

---

# 2. `Result<T,E>` là enum bình thường

Về Core:

```text
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Không có hidden runtime.

Không có:

```text
exception object
stack handler
global exception table
```

trong bản thân `Result`.

---

# 3. `Option<T>` cũng là enum

```text
enum Option<T> {
    Some(T),
    None,
}
```

Compiler có thể tối ưu representation.

Ví dụ:

```text
Option<Box<T>>
```

có thể sử dụng niche/null representation nếu ABI/layout cho phép.

Nhưng đây là optimization, không phải source semantics.

---

# 4. `Result` không phải exception

Ví dụ:

```text
fn read() -> Result<Data, IoError>
```

MIR:

```text
%r = call read()

switch %r:
    Ok(v)  → success
    Err(e) → failure
```

Không có:

```text
throw
catch
unwind
```

---

# 5. `?` là control-flow sugar

Source:

```text
let x = foo()?
```

desugar semantic:

```text
match foo() {
    Ok(v) => x = v,
    Err(e) => return Err(e),
}
```

MIR:

```text
%r = call foo()

switch %r:
    Ok(%v)  -> bb_ok
    Err(%e) -> bb_return_err

bb_ok:
    %x = move %v
    ...

bb_return_err:
    return Err(%e)
```

Không có exception.

---

# 6. `?` không được phép làm hidden allocation

Ví dụ:

```text
foo()?
```

không được tạo:

```text
exception object
heap allocation
runtime handler
```

Nó chỉ là branch/return.

---

# 7. Error propagation phải zero-cost khi không lỗi

Đây là mục tiêu quan trọng.

Ví dụ:

```text
fn process() -> Result<u32, Error> {
    let a = foo()?
    let b = bar(a)?
    Ok(b)
}
```

Success path có thể được optimize thành gần:

```text
call foo
check result
call bar
check result
return
```

Không cần exception machinery.

---

# 8. Error representation

`Result<T,E>` representation compiler-controlled.

Compiler có thể chọn:

```text
tag + payload
```

hoặc:

```text
niche
```

hoặc:

```text
register pair
```

hoặc ABI-specific representation.

Ví dụ:

```text
Result<u32, SmallError>
```

có thể trả bằng registers.

---

# 9. Error type nên nhỏ

Axiom không áp đặt một universal `Exception`.

Std có thể cung cấp:

```text
IoError
ParseError
Utf8Error
NetworkError
...
```

User có thể tạo:

```text
enum MyError {
    NotFound,
    Invalid,
    Io(IoError),
}
```

---

# 10. Error không phải resource

Một `Err(e)` là value.

Ví dụ:

```text
Result<File, IoError>
```

`File` là resource-owning.

`IoError` chỉ là error value.

Do đó:

```text
Err(e)
```

không tự tạo cleanup machinery ngoài Drop của các value thực sự sở hữu resource.

---

# 11. Drop khi `?` return

Đây là phần quan trọng.

```text
fn f() -> Result<(), Error> {
    let a = ResourceA()
    let b = ResourceB()

    foo()?
    
    Ok(())
}
```

Nếu `foo()` trả `Err`:

```text
foo()
  ↓
Err
  ↓
drop b
  ↓
drop a
  ↓
return Err
```

Compiler phải tự chèn Drop.

---

# 12. `?` không bypass Drop

Invariant:

> Mọi early return do `?` đều phải đi qua cleanup cần thiết.

Không có:

```text
? → jump directly out of function
```

bỏ qua resource.

---

# 13. `return Err(...)` cũng vậy

```text
return Err(error)
```

phải:

```text
evaluate error
cleanup locals
return
```

theo deterministic destruction semantics.

---

# 14. `panic()`

Định nghĩa:

```text
fn panic(message: ...) -> never
```

hoặc compiler intrinsic tương đương.

`never` nghĩa:

```text
panic()
```

không trở về caller bình thường.

---

# 15. Panic không phải Result

Sai:

```text
fn foo() -> Result<T,E> {
    if bad {
        panic()
    }
}
```

vẫn hợp lệ.

`Result` biểu diễn lỗi mà caller có thể xử lý.

`panic` biểu diễn failure mà execution path hiện tại không tiếp tục.

---

# 16. Panic profile

Axiom cần hai profile chính:

```text
panic = abort
panic = unwind
```

### Abort

```text
panic()
  ↓
terminate process
```

### Unwind

```text
panic()
  ↓
cleanup frames
  ↓
panic handler / catch boundary
```

---

# 17. Abort nên là baseline

Để đạt:

- binary nhỏ;
- runtime nhỏ;
- freestanding;
- embedded;
- systems programming;

default profile nên có:

```text
panic = abort
```

Không cần unwind tables/runtime nếu chương trình không yêu cầu.

---

# 18. Unwind là optional capability

Nếu build:

```text
axiom build --panic=unwind
```

compiler/runtime thêm:

```text
unwind metadata
personality/runtime support
cleanup landing paths
```

Chương trình bình thường vẫn không cần một "exception runtime" khổng lồ.

---

# 19. Panic cleanup

Nếu panic + unwind:

```text
let a = A()
let b = B()

panic()
```

phải:

```text
drop b
drop a
unwind
```

Điều này sử dụng cùng Drop machinery.

Không tạo một hệ cleanup thứ hai.

---

# 20. `Drop` là nền tảng

Điều này rất quan trọng:

```text
Result
panic
return
break
continue
unwind
```

đều phải dùng chung **Drop elaboration**.

Compiler không nên có:

```text
normal cleanup engine
panic cleanup engine
async cleanup engine
```

tách biệt.

Thay vào đó:

```text
Ownership/Drop facts
        ↓
Cleanup graph
        ↓
normal exit / panic exit / unwind
```

---

# 21. Drop không được trả Result

Không:

```text
fn Drop.drop(self) -> Result<(), Error>
```

vì điều này tạo vấn đề:

```text
cleanup failed
while handling another error
```

và đặc biệt:

```text
panic
  ↓
drop
  ↓
drop fails
  ↓
???
```

---

# 22. Cleanup có thể thất bại thì sao?

Dùng:

```text
close() -> Result<(), E>
```

Ví dụ:

```text
let file = File.open(path)?

file.write(data)?
file.close()?
```

Programmer xử lý failure **trước khi resource bị Drop**.

---

# 23. Drop sau `close()`

Nếu:

```text
file.close()?
```

thành công:

```text
resource state = CLOSED
```

Sau đó Drop:

```text
drop(file)
```

không được close lần nữa.

Do đó resource type có state semantics nội bộ.

---

# 24. Nếu programmer quên `close()`?

Drop vẫn phải cleanup:

```text
drop(file)
```

nhưng không propagate error.

Ví dụ OS close error:

```text
close() → Err
```

có thể được báo khi programmer gọi explicit close.

Nếu chỉ Drop:

```text
error cannot be propagated
```

runtime policy có thể:

- ignore;
- log/diagnostic trong debug;
- platform-specific handling.

Nhưng không được biến Drop thành exception.

---

# 25. `defer` có nên có?

Tôi đề xuất:

> **Không đưa `defer` vào Core v1.**

Lý do:

Axiom đã có:

```text
Drop
```

và deterministic cleanup.

Ví dụ C:

```text
defer close(fd)
```

Axiom:

```text
let file = File.open(...)
```

RAII-style deterministic Drop tự xử lý.

Nếu cần cleanup có logic phức tạp:

```text
struct Guard { ... }

impl Drop for Guard {
    ...
}
```

hoặc explicit function.

---

# 26. Nhưng `defer` đôi khi hữu ích

Đúng.

Nhưng `defer` rất dễ trở thành:

```text
second cleanup language
```

và gây ambiguity với ownership.

Nếu sau này cần, nên là library/compiler sugar được hạ xuống scope guard, không phải Core semantic primitive.

---

# 27. `panic!` macro không cần

Không cần macro system chỉ để:

```text
panic!("...")
```

Có thể:

```text
panic("...")
```

hoặc compiler intrinsic với formatting library.

Formatting chỉ được link khi thực sự sử dụng.

---

# 28. `assert`

Nên có:

```text
assert(condition)
assert_eq(a, b)
```

nhưng library/compiler intrinsic.

Semantics:

```text
if !condition {
    panic(...)
}
```

Compiler có thể eliminate nếu chứng minh condition luôn true.

---

# 29. `debug_assert`

Nên có:

```text
debug_assert(...)
```

nhưng đây là **configuration-level semantic difference có chủ ý**.

Ví dụ:

```text
debug build:
    check

release:
    eliminate
```

Điều này hợp lệ vì programmer đã explicit yêu cầu assertion chỉ trong debug.

Không giống:

```text
array bounds
```

là safety semantics mặc định.

---

# 30. Runtime trap

Trap dành cho machine/runtime-level failure.

Ví dụ:

```text
unreachable
integer divide-by-zero
invalid conversion
hardware fault
```

tùy semantics từng operation.

Trap không phải recoverable error.

---

# 31. Checked arithmetic

Ví dụ:

```text
let x = checked_add(a, b)
```

có thể:

```text
Result<T, Overflow>
```

hoặc compiler intrinsic.

Trong khi:

```text
a + b
```

theo semantics Axiom đã chọn phải có behavior xác định.

Tôi tiếp tục đề xuất:

- debug/release **không được đổi semantics**;
- checked overflow có explicit result;
- wrapping/saturating có explicit operations.

---

# 32. Integer overflow

Nên có các operation:

```text
checked_add
wrapping_add
saturating_add
```

Ví dụ:

```text
let x = a.wrapping_add(b)
```

→ modulo arithmetic.

```text
let x = a.saturating_add(b)
```

→ clamp.

```text
let x = a.checked_add(b)?
```

→ `Option`/`Result` tùy API.

---

# 33. Normal `+`

Tôi đề xuất normal arithmetic trong safe code có semantics:

> **deterministic checked arithmetic**, với overflow tạo runtime trap/panic theo profile, chứ không UB.

Điều này cho optimizer một semantics rõ ràng.

---

# 34. Nhưng performance?

Compiler có thể chứng minh:

```text
a <= MAX
b <= MAX-a
```

→ bỏ overflow check.

Do đó:

```text
safe arithmetic
```

có thể compile thành raw integer instruction nếu proof đủ mạnh.

---

# 35. FFI boundary

Một vấn đề rất quan trọng:

```text
extern "C"
fn foo(...)
```

Foreign C function không được phép ném exception qua Axiom boundary.

Nếu C++:

```text
C++ exception
    ↓
Axiom extern boundary
```

→ **không được phép xuyên boundary**.

Phải có adapter ở foreign side:

```text
C++ try/catch
    ↓
Result
    ↓
Axiom
```

---

# 36. Axiom panic qua C boundary

Ngược lại:

```text
Axiom panic
    ↓
extern "C"
```

không nên unwind qua C ABI mặc định.

Mặc định:

```text
panic → abort
```

hoặc boundary wrapper xử lý rõ ràng.

Nếu muốn unwind xuyên foreign ABI:

> phải có explicit ABI/unwind contract.

Không implicit.

---

# 37. `extern` function có panic contract?

Axiom source không cần effect system tổng quát.

Nhưng ABI metadata nội bộ phải biết:

```text
may_unwind
no_unwind
```

để backend tạo đúng unwind boundary.

---

# 38. Async cancellation

Cancellation không phải panic.

Không:

```text
cancel → panic
```

Mà:

```text
cancel request
    ↓
Future observes cancellation
    ↓
returns/carries cancellation result
    ↓
Drop state
```

---

# 39. Cancellation nên là cooperative

Ví dụ:

```text
let token = cancel_token()

foo(token).await
```

Future kiểm tra cancellation.

Không có:

```text
force kill arbitrary instruction
```

vì unsafe với resource state.

---

# 40. Drop Future

Một điểm đã chốt trước đó:

> Drop Future không mặc định có nghĩa OS operation đã bị cancel.

Ví dụ:

```text
let f = async_read(buffer)
drop(f)
```

Nếu operation đã submit xuống kernel:

```text
kernel may still own operation
```

Runtime phải đảm bảo buffer/resource dependency đến khi operation thực sự hoàn thành/cancel an toàn.

---

# 41. Cancellation handle

Nếu cần explicit cancellation:

```text
operation.cancel()
```

trả:

```text
Result<(), CancelError>
```

hoặc abstraction tương đương.

Không dùng panic.

---

# 42. Structured concurrency

Nếu:

```text
scope {
    spawn(child)
}
```

thì scope exit phải giải quyết child:

```text
join
cancel
wait
```

theo API semantics.

Không để:

```text
child silently references dead parent storage
```

Facts Engine kiểm tra dependency.

---

# 43. Thread panic

Thread:

```text
Thread.spawn(...)
```

nếu child panic:

không nhất thiết terminate toàn process.

Thread handle:

```text
join() -> Result<T, ThreadError>
```

có thể quan sát panic.

Ví dụ conceptually:

```text
child panic
    ↓
thread terminates
    ↓
join()
    ↓
Err(Panicked(...))
```

Profile/ABI có thể quyết định payload panic được giữ đến đâu.

---

# 44. Detached thread

Nếu:

```text
detach(thread)
```

thì thread không còn join owner.

Nhưng:

```text
owned values
```

được chuyển ownership đúng semantics.

Không được giữ view vào stack của parent.

Facts Engine bắt lỗi trước khi spawn.

---

# 45. Panic payload

Không nên bắt buộc:

```text
String
```

vì sẽ tăng allocation/runtime.

Có thể:

```text
panic(value)
```

với panic payload profile.

Minimal profile:

```text
panic()
```

chỉ gọi handler/abort.

Rich hosted profile:

```text
PanicInfo {
    message
    location
    ...
}
```

Runtime capability mới cung cấp formatting/backtrace.

---

# 46. Backtrace

Không phải Core semantic.

Debug build có thể link:

```text
unwind
debug info
symbolizer
```

Release/freestanding có thể bỏ toàn bộ.

---

# 47. Error context

Không nên biến mọi `Result` thành heap-allocated exception chain.

Std có thể cung cấp:

```text
Error
ErrorContext
```

nhưng representation tùy library.

Programmer chọn nếu cần.

---

# 48. `Result` layout tối ưu

Compiler có thể nhận biết:

```text
Result<T,E>
Option<T>
```

là algebraic types bình thường nhưng có optimization:

```text
niche optimization
uninhabited variant
register packing
branch elimination
```

Không cần runtime support.

---

# 49. Never/error types

`never` cực kỳ hữu ích:

```text
fn panic() -> never
fn abort() -> never
fn trap() -> never
```

Compiler biết:

```text
call panic()
```

→ successor unreachable.

Điều này giúp CFG optimizer rất mạnh.

---

# 50. `try` có nên là keyword?

Tôi đề xuất **không cần `try` trong Core v1**.

Có:

```text
?
match
```

đủ cho Result propagation.

Nếu sau này cần try-block:

```text
try {
    ...
}
```

có thể bổ sung như syntax sugar.

Không nên thêm chỉ vì các ngôn ngữ khác có.

---

# 51. `catch` cũng không có trong Core

Không có general:

```text
try {
}
catch {
}
```

cho Result.

Nếu cần panic recovery trong profile hỗ trợ unwind, có thể có **explicit API**:

```text
panic::catch(...)
```

nhưng đây là runtime capability, không phải general exception syntax.

---

# 52. Panic recovery

Ví dụ:

```text
catch_unwind(|| {
    risky()
})
```

có thể tồn tại ở std/runtime.

Semantics:

```text
panic
 ↓
unwind
 ↓
catch boundary
 ↓
Result
```

Nhưng:

- chỉ hoạt động với `panic=unwind`;
- không có trong minimal/abort profile;
- không được bắt foreign exception;
- Drop vẫn chạy.

---

# 53. Panic payload không được tự động biến thành Result

Chỉ explicit catch boundary mới làm vậy.

Không:

```text
panic
→ implicit Result
```

vì điều đó khiến control-flow semantics khó đoán.

---

# 54. FFI callback

Nếu Axiom callback được C gọi:

```text
extern "C" fn callback(...)
```

thì mặc định:

```text
panic → abort
```

hoặc wrapper:

```text
callback_boundary(...)
```

catch panic rồi trả error code.

Không để unwind xuyên C ABI.

---

# 55. OS errors

Không tạo hàng trăm exception classes.

Ví dụ:

```text
File.open()
```

→:

```text
Result<File, IoError>
```

`IoError`:

```text
kind
raw_code
operation
```

Ví dụ:

```text
NotFound
PermissionDenied
WouldBlock
Interrupted
InvalidInput
...
```

Raw OS error vẫn giữ được.

---

# 56. Error conversion

Có thể hỗ trợ trait:

```text
From<E> for F
```

để:

```text
foo()?
```

tự convert error nếu compiler tìm được conversion hợp lệ.

Nhưng conversion phải deterministic.

Không được có implicit arbitrary conversion.

---

# 57. Error propagation và generic

Ví dụ:

```text
fn f<T, E>(...) -> Result<T,E>
```

`?` yêu cầu error type tương thích.

Trait solver xử lý conversion trước MIR.

MIR chỉ thấy:

```text
convert error
return Err
```

---

# 58. Cleanup graph

Tôi đề xuất compiler có một representation:

```text
CleanupGraph
```

được xây từ ownership/drop facts.

Mỗi exit point:

```text
return
panic
trap
unwind
break
continue
```

đều truy vấn cleanup graph.

Ví dụ:

```text
          function
             │
        ┌────┴────┐
        │         │
     return     panic
        │         │
     cleanup   cleanup
        │         │
      exit      unwind
```

---

# 59. Cleanup graph không phải exception graph

Nó chỉ biểu diễn:

> Resource nào phải được finalized khi control flow rời khỏi region.

Không chứa:

```text
catch handler
exception matching
```

trừ khi unwind/catch profile thực sự cần.

---

# 60. Cleanup ordering

Mặc định:

```text
reverse declaration/initialization order
```

Nhưng field destruction:

```text
struct fields
```

nên có deterministic declaration order semantics.

Compiler không được reorder Drop nếu destructor behavior observable.

---

# 61. Drop optimization

Nếu compiler chứng minh:

```text
x
```

không có resource side effect:

```text
Drop(x) = trivial
```

có thể eliminate.

Ví dụ:

```text
struct Empty {}
```

không cần runtime cleanup.

---

# 62. User-defined Drop

Nếu:

```text
impl Drop for Foo
```

thì:

```text
Drop(Foo)
```

là observable call.

Optimizer có thể inline nó nếu semantics preserved.

Không được xóa chỉ vì "object không còn dùng".

---

# 63. Partial move và custom Drop

Quyết định trước đây vẫn giữ:

Nếu type có **user-defined Drop**, partial move không được phép.

Ví dụ:

```text
struct Foo {
    a: String,
    b: String
}

impl Drop for Foo { ... }
```

Không cho:

```text
let a = foo.a
```

vì compiler phải đảm bảo destructor nhìn thấy trạng thái object mà nó mong đợi.

Derived/compiler Drop có thể hỗ trợ partial move.

---

# 64. Panic trong Drop

Drop không được fail recoverably.

Nếu Drop panic trong quá trình normal execution:

```text
Drop
 ↓
panic
```

có thể bắt đầu panic.

Nếu đang unwind:

```text
panic
 ↓
Drop
 ↓
panic again
```

→ **terminate/abort**.

Không tiếp tục nested unwind vô hạn.

---

# 65. `close()` trong Drop

Nếu resource wrapper có:

```text
close() -> Result
```

thì:

```text
Drop
```

không gọi `close()` theo cách cần propagate error.

Thay vào đó resource state có thể được cleanup best-effort.

API documentation phải nói rõ.

---

# 66. Fatal allocation failure

Allocation failure là một vấn đề riêng.

Axiom không nên bắt buộc:

```text
alloc failure → panic
```

cho mọi profile.

Có thể:

```text
Box::try_new(...) -> Result<Box<T>, AllocError>
```

và:

```text
Box::new(...)
```

có policy:

```text
panic / abort
```

tùy runtime/profile.

---

# 67. Freestanding

Trong freestanding:

```text
panic = abort/trap
```

là hợp lý.

Không cần:

```text
String formatting
stack trace
unwind
```

trừ khi programmer link chúng.

---

# 68. Hosted

Hosted profile có thể thêm:

```text
panic handler
unwind
backtrace
logging
```

nhưng từng capability link độc lập.

---

# 69. Runtime graph

Ví dụ chương trình:

```text
Result
File
```

nhưng không panic/unwind:

```text
Executable
 ├── startup
 ├── allocator
 └── filesystem/OS ABI
```

Không tự động link:

```text
unwind
backtrace
exception runtime
```

---

# 70. Program dùng panic nhưng abort

Runtime:

```text
startup
panic_abort
```

Không cần:

```text
unwind runtime
```

Binary nhỏ.

---

# 71. Program dùng catch_panic

Runtime:

```text
startup
panic_unwind
unwind_metadata
panic_handler
```

Chỉ khi thực sự dùng.

---

# 72. Async panic

Nếu Future panic:

```text
poll()
 ↓
panic
```

với unwind profile:

```text
Future cleanup
 ↓
task boundary
```

Scheduler phải quyết định policy:

- task panic được lưu trong JoinHandle;
- detached task panic đi tới panic handler;
- process abort nếu configured.

Không được scheduler tự tạo semantics mới.

---

# 73. Async cancellation vs Drop

Nếu task bị cancel:

```text
task state
 ↓
drop Future/state
 ↓
drop owned values
```

nhưng external I/O operation có dependency thì phải được xử lý theo AIO contract.

Không được:

```text
free buffer
while kernel still writes
```

---

# 74. `Result` + cancellation

Cancellation có thể được biểu diễn:

```text
Result<T, Cancelled>
```

hoặc một error type lớn hơn:

```text
Result<T, IoError>
```

Tôi nghiêng về:

> cancellation là library/runtime policy, không phải một special language-level exception.

---

# 75. Error taxonomy cuối cùng

Axiom Core:

```text
Option<T>
Result<T,E>
panic()
never
```

Runtime:

```text
trap
abort
unwind
catch_panic
```

Library:

```text
IoError
AllocError
ThreadError
CancelError
...
```

Resource:

```text
Drop
close() -> Result
```

---

# 76. MIR representation

Sau lowering:

```text
Result:
    ordinary enum

?:
    SWITCH + RETURN

panic:
    PANIC

abort:
    ABORT

trap:
    TRAP

Drop:
    DROP

unwind:
    exceptional CFG/cleanup metadata
```

Điểm quan trọng:

> **Result không làm MIR phức tạp. Unwind mới là optional control-flow extension.**

---

# 77. Unwind implementation

Không nên đưa landing pads vào mọi MIR.

MIR semantic phase:

```text
PANIC
```

Sau khi chọn:

```text
panic=abort
```

→ lower:

```text
PANIC → CALL panic_abort / TRAP
```

Nếu:

```text
panic=unwind
```

→ compiler chạy:

```text
UnwindLowering
```

tạo cleanup/unwind metadata.

Như vậy MIR Core không bị ô nhiễm bởi C++-style exception implementation.

---

# 78. `panic=abort` optimization

Compiler biết:

```text
panic() -> never
```

nên CFG:

```text
panic
 ↓
unreachable
```

Có thể DCE code sau đó.

---

# 79. `panic=unwind` optimization

Compiler vẫn biết:

```text
panic -> non-local control flow
```

nhưng phải giữ cleanup obligations.

Optimizer không được xóa destructor observable.

---

# 80. Debug/release semantics

Các khác biệt được phép:

```text
debug_assert
debug logging
backtrace detail
optimization
```

Không được:

```text
Result semantics thay đổi
Drop order thay đổi
safe bounds semantics thay đổi
panic behavior thay đổi
```

trừ khi programmer chọn profile/configuration rõ ràng.

---

# 81. Frozen invariants

```text id="a8z2f4"
AERR-20 — Result Is An Ordinary Algebraic Value

AERR-21 — Option Is An Ordinary Algebraic Value

AERR-22 — Result Does Not Require Exception Runtime

AERR-23 — Question Propagation Is Explicit Control Flow

AERR-24 — Error Propagation Must Preserve Ownership

AERR-25 — Early Error Return Runs Required Drops

AERR-26 — Panic Is Distinct From Recoverable Error

AERR-27 — Panic Has Never Return Semantics

AERR-28 — Abort Is A Valid Panic Profile

AERR-29 — Unwind Is An Optional Runtime Capability

AERR-30 — Minimal Programs Need Not Link Unwind Runtime

AERR-31 — Panic Does Not Imply Heap Allocation

AERR-32 — Panic Payload Representation Is Profile Dependent

AERR-33 — Drop Is Deterministic

AERR-34 — Drop Is Not Recoverable Error Propagation

AERR-35 — Explicit close May Return Result

AERR-36 — Drop Must Not Require Result Handling

AERR-37 — Panic During Active Unwind Terminates

AERR-38 — Foreign Exceptions Must Not Cross Axiom ABI Implicitly

AERR-39 — Axiom Panic Must Not Cross Foreign ABI Implicitly

AERR-40 — FFI Exception Translation Requires Explicit Boundary

AERR-41 — Thread Panic Is Observable Through Join Semantics

AERR-42 — Detached Task Panic Uses Explicit Runtime Policy

AERR-43 — Async Cancellation Is Distinct From Panic

AERR-44 — Cancellation Is Cooperative

AERR-45 — Dropping A Future Does Not Imply External Operation Cancellation

AERR-46 — In-Flight Operations Preserve Resource Dependencies

AERR-47 — Cleanup Uses The Same Ownership/Drop Model Across Exit Paths

AERR-48 — Cleanup Graph Is Independent Of Exception Matching

AERR-49 — Drop Ordering Is Deterministic

AERR-50 — User Drop Is Observable

AERR-51 — Trivial Drop May Be Eliminated

AERR-52 — User-Defined Drop Prevents Unsafe Partial Move

AERR-53 — Allocation Failure Is Distinct From Cleanup Failure

AERR-54 — Runtime Failure Policy Is Profile Dependent

AERR-55 — Debug And Release Preserve Defined Error Semantics

AERR-56 — Result Success Paths Have No Required Exception Machinery

AERR-57 — Unwind Lowering Occurs Only When Required By Profile

AERR-58 — Panic/Unwind Metadata Is Not Required For Abort-Only Programs

AERR-59 — Error Types Preserve Relevant OS Error Information

AERR-60 — Error Propagation Is Deterministic

AERR-61 — Panic Recovery Requires Explicit Unwind Capability

AERR-62 — Core Does Not Define General Exception Matching

AERR-63 — Core v1 Does Not Require Defer

AERR-64 — Cleanup Cannot Be Skipped By Optimization

AERR-65 — Safe Failure Paths Must Preserve Memory Safety
```

---

# 82. Kiến trúc error hiện tại

Axiom bây giờ có một mô hình rất sạch:

```text
                    ┌───────────────┐
                    │   Operation   │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
          Success       Recoverable     Fatal
             │            Error            │
             │              │              │
             ↓              ↓              ↓
             T         Result<T,E>    panic/trap
                                           │
                              ┌────────────┴───────────┐
                              ↓                        ↓
                           abort                    unwind
```

Trong khi resource lifecycle chạy song song:

```text
Owner
  ↓
Drop
  ↓
cleanup
```

và **mọi control-flow exit đều đi qua cleanup graph**.

---

# 83. Một quyết định rất quan trọng đã đạt được

Axiom không cần một "exception system" lớn.

Thay vào đó:

```text
Result
    = ordinary value/control flow

panic
    = explicit non-local failure

unwind
    = optional implementation mechanism

Drop
    = deterministic resource cleanup
```

Điều này giữ cho compiler/runtime nhỏ hơn rất nhiều so với C++ nhưng vẫn có khả năng viết ứng dụng hosted đầy đủ.

---

# 84. Bước tiếp theo: `ABI-002 — Calling Convention & Return ABI`

Mặc dù ABI-001 đã thiết kế ở mức kiến trúc, giờ cần đi xuống **ABI lowering thực tế**, vì Axiom đã có:

- `Result`;
- `Option`;
- large struct;
- `Box`;
- `view`;
- `mut_view`;
- `dyn Trait`;
- closures;
- async Future;
- `never`;
- variadic;
- FFI.

Cần chốt chính xác:

```text
scalar return
small aggregate return
large aggregate return
sret
multi-register return
Option niche
Result representation
view/mut_view ABI
dyn Trait ABI
closure ABI
extern C ABI
variadic ABI
async ABI
panic/unwind ABI
```

Đây là bước rất quan trọng để từ **MIR semantic** thực sự đi xuống **LIR/Machine IR**, và cũng là nơi quyết định Axiom có thể đạt binary/performance gần C/C++ đến mức nào.