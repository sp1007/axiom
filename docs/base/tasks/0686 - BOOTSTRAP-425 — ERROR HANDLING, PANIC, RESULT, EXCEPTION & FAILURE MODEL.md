# BOOTSTRAP-425 — ERROR HANDLING, PANIC, RESULT, EXCEPTION & FAILURE MODEL

Axiom cần phân biệt rõ **expected failure** và **program failure**.

Ví dụ:

```text
open("missing.txt")
```

là expected failure.

Trong khi:

```text
assert(index < len)
```

không đúng là program invariant failure.

Không nên dùng một cơ chế duy nhất cho cả hai.

Mô hình đề xuất:

```text
Expected failure
    ↓
Result<T, E>

Optional absence
    ↓
Option<T>

Program invariant failure
    ↓
panic

Unrecoverable failure
    ↓
abort
```

Exception/unwind chỉ là **optional runtime mechanism**, không phải cách xử lý lỗi mặc định.

---

## 425.1 — Mục tiêu

Error model phải đạt:

```text
zero-cost success path
explicit failure
no mandatory exceptions
no mandatory heap allocation
no mandatory runtime
good FFI
good async integration
easy propagation
AI-friendly syntax
```

---

# 425.2 — `Result<T, E>`

Primitive semantic type:

```text
Result<T, E>
```

gồm:

```text
Ok(T)
Err(E)
```

Ví dụ:

```text
fn open(path: str) -> Result<File, IOError>
```

---

# 425.3 — `Option<T>`

Absence không phải error:

```text
Option<T>
```

gồm:

```text
Some(T)
None
```

Ví dụ:

```text
fn find_user(id: UserId) -> Option<User>
```

Không cần tạo exception cho `not found`.

---

# 425.4 — Representation

`Result<T,E>` phải là ordinary value.

Không bắt buộc:

```text
heap allocation
object header
runtime exception object
```

Compiler có thể layout:

```text
tag + payload
```

hoặc áp dụng niche optimization từ BOOTSTRAP-422.

---

# 425.5 — Zero-cost success path

Code:

```text
result := parse(data)
```

phải có khả năng compile gần như:

```text
call parse
test status
branch
```

Không tạo exception machinery nếu chỉ sử dụng `Result`.

---

# 425.6 — Error propagation

Axiom cần một syntax ngắn để propagate lỗi.

Conceptual:

```text
value := try read()
```

Nếu:

```text
Ok(x)
```

→ `value = x`.

Nếu:

```text
Err(e)
```

→ return `Err(e)` từ current function.

Tên operator/syntax cuối cùng sẽ khóa ở syntax task, nhưng semantic phải tương đương.

---

# 425.7 — Propagation phải không allocation

Ví dụ:

```text
fn load() -> Result<Data, Error> {
    x := try read()
    y := try parse(x)
    return Ok(y)
}
```

không được yêu cầu tạo heap object cho mỗi error propagation.

---

# 425.8 — Error conversion

Nếu:

```text
read() -> Result<Bytes, IOError>
```

nhưng function trả:

```text
Result<Data, AppError>
```

compiler/library có thể thực hiện:

```text
IOError → AppError
```

thông qua conversion trait/function.

Không implicit string formatting nếu programmer không yêu cầu.

---

# 425.9 — Typed errors

Error nên là type bình thường:

```text
struct IOError {
    code: i32
}
```

hoặc enum:

```text
enum IOError {
    NotFound
    PermissionDenied
    InvalidPath
}
```

Không cần một universal runtime exception class.

---

# 425.10 — Error trait/interface

Standard library có thể định nghĩa capability:

```text
Error
```

với các operation như:

```text
message()
source()
code()
```

nhưng `Error` không được bắt buộc mọi error phải heap allocate.

---

# 425.11 — Static error types

High-performance code có thể:

```text
Result<T, SmallError>
```

với error nằm hoàn toàn inline.

Ví dụ:

```text
Result<i32, ParseError>
```

có thể chỉ là vài bytes.

---

# 425.12 — Dynamic errors

Library vẫn có thể cung cấp:

```text
DynamicError
```

cho application-level systems.

Nếu dynamic error cần heap:

```text
Box<Error>
```

thì allocation là explicit/visible ở abstraction level.

---

# 425.13 — Error context

Có thể thêm context:

```text
err.with_context("loading configuration")
```

Nhưng context không nên bắt buộc.

Minimal systems code có thể:

```text
return Err(err)
```

không allocation.

---

# 425.14 — Error stack traces

Stack trace không thuộc `Result` core.

Debug build có thể:

```text
capture stack trace
```

Release build có thể:

```text
omit
```

hoặc chỉ capture khi explicitly requested.

---

# 425.15 — Panic

`panic` biểu diễn:

> Chương trình không thể tiếp tục theo normal control flow tại vị trí này.

Ví dụ:

```text
panic("internal invariant violated")
```

Panic không phải expected business error.

---

# 425.16 — Panic payload

Panic có thể chứa:

```text
message
code
location
payload
```

nhưng minimal mode chỉ cần:

```text
panic(code)
```

để tránh runtime overhead.

---

# 425.17 — Panic modes

Build configuration:

```text
panic = abort
```

hoặc:

```text
panic = unwind
```

---

# 425.18 — Abort

Abort:

```text
panic
 ↓
terminate
```

không cần unwinder.

Đây là default phù hợp cho:

```text
embedded
freestanding
tiny binaries
performance-critical software
```

---

# 425.19 — Unwind

Optional unwind:

```text
panic
 ↓
unwind stack
 ↓
run cleanup
 ↓
catch boundary
```

Cleanup sử dụng BOOTSTRAP-423.

---

# 425.20 — Panic cleanup

Nếu:

```text
a := acquire_A()
b := acquire_B()

panic(...)
```

unwind phải thực hiện:

```text
drop(b)
drop(a)
```

theo ownership rules.

---

# 425.21 — No exception by default

Axiom không biến:

```text
Result<T,E>
```

thành exception internally.

Đây là invariant quan trọng.

---

# 425.22 — Why Result is default

Expected errors:

```text
file missing
network unavailable
invalid input
parse failed
permission denied
```

có control flow bình thường.

Compiler có thể nhìn thấy toàn bộ flow:

```text
Ok
Err
```

và optimize accordingly.

---

# 425.23 — Exception as optional feature

Axiom có thể hỗ trợ exception/unwind cho interoperability hoặc application code.

Nhưng:

```text
exception support != language-required runtime
```

Một binary không dùng exception không mang exception machinery.

---

# 425.24 — Try/catch

Nếu exception mode được bật:

```text
try {
    work()
}
catch e {
    recover(e)
}
```

được lower thành unwind landing pads/exception tables theo target ABI.

Không cần tồn tại trong binaries không dùng.

---

# 425.25 — Result catch

`Result` không dùng `catch` theo exception semantics.

Ví dụ:

```text
match read() {
    Ok(x)  => process(x)
    Err(e) => recover(e)
}
```

đây là ordinary control flow.

---

# 425.26 — Match integration

`Result` và `Option` phải integrate với `match`.

```text
match result {
    Ok(value) => use(value)
    Err(error) => handle(error)
}
```

Compiler phải hỗ trợ exhaustive checking.

---

# 425.27 — Exhaustiveness

Compiler phải cảnh báo/error khi:

```text
match option {
    Some(x) => use(x)
}
```

bỏ qua:

```text
None
```

trừ khi programmer explicitly dùng wildcard hoặc equivalent.

---

# 425.28 — Error propagation across async

Async function:

```text
async fn load() -> Result<Data, Error>
```

có thể:

```text
x := try await read()
```

Compiler phải kết hợp:

```text
await
+
Result propagation
```

mà không tạo temporary exception object.

---

# 425.29 — Error propagation across thread

Thread function có thể:

```text
fn worker() -> Result<(), WorkerError>
```

Join trả:

```text
Result<Result<(), WorkerError>, ThreadError>
```

hoặc standard library có thể flatten thành một abstraction dễ dùng hơn.

Core không cần special-case.

---

# 425.30 — Error aggregation

Parallel tasks có thể cần:

```text
join_all(tasks)
```

trả collection của results.

Không nên ép core language có một parallel-error mechanism riêng.

---

# 425.31 — Error conversion protocol

Một conversion capability:

```text
From<SourceError> for TargetError
```

cho phép:

```text
try operation()
```

tự động convert error trong phạm vi function signature.

Conversion phải deterministic và không được âm thầm swallow error.

---

# 425.32 — No implicit error stringification

Compiler không tự biến:

```text
Error
```

thành:

```text
String
```

chỉ để hiển thị.

Formatting là library operation.

---

# 425.33 — Error codes

Low-level API có thể dùng:

```text
enum ErrorCode
```

hoặc integer code.

Ví dụ OS/FFI:

```text
errno
HRESULT
NTSTATUS
Win32 error
```

được wrap thành Axiom error types.

---

# 425.34 — FFI error ABI

C function:

```text
int foo(...)
```

có thể map:

```text
0 = success
nonzero = error
```

library wrapper biến thành:

```text
Result<T, Error>
```

Không cần runtime exception bridge.

---

# 425.35 — C errno

Axiom FFI layer phải cho phép:

```text
call C function
read errno
convert to Error
```

và không giả định `errno` là ordinary global variable.

Platform ABI xử lý TLS/OS semantics phù hợp.

---

# 425.36 — HRESULT / Windows-style APIs

Có thể wrap:

```text
HRESULT
NTSTATUS
GetLastError()
```

thành typed Axiom errors.

Đây là standard library/platform layer.

---

# 425.37 — Error ownership

Error value mặc định là value.

Nếu error chứa:

```text
String
Buffer
Resource
```

thì nó sử dụng ownership model 423.

Không có special error GC.

---

# 425.38 — Error copying

Small errors có thể `Copy`.

Large/resource errors có thể `Move`.

Ví dụ:

```text
ParseError: Copy
FileError: Move/Clone tùy representation
```

---

# 425.39 — Error destructors

Error có thể sở hữu resource.

Do đó:

```text
Result<T,E>
```

phải cleanup cả:

```text
T
E
```

theo active variant.

---

# 425.40 — Error ABI

Compiler phải classify:

```text
Result<T,E>
```

giống aggregate/enum theo BOOTSTRAP-421/422.

Có thể return qua:

```text
registers
sret
hidden status
```

tùy layout/ABI.

---

# 425.41 — Niche optimization

Ví dụ:

```text
Option<Pointer>
```

có thể biểu diễn:

```text
null = None
non-null = Some
```

không cần thêm tag.

Tương tự một số `Result` có thể tận dụng invalid/niche values.

---

# 425.42 — No mandatory dynamic dispatch

Errors không mặc định dùng:

```text
virtual dispatch
```

Enum/static types preferred cho zero-cost paths.

Dynamic error là explicit abstraction.

---

# 425.43 — Error handling in `no_std`/freestanding

Freestanding code có thể dùng:

```text
Result
Option
panic = abort
```

mà không cần:

```text
filesystem
threads
heap
exception runtime
```

---

# 425.44 — Compile-time errors

Compiler phải phân biệt với runtime errors.

Ví dụ:

```text
undefined variable
type mismatch
use after move
non-exhaustive match
```

→ compile-time.

---

# 425.45 — Runtime expected errors

Ví dụ:

```text
file missing
socket refused
invalid user input
```

→ `Result`.

---

# 425.46 — Undefined behavior

Một số low-level violations:

```text
invalid raw pointer dereference
data race in unsafe code
invalid FFI contract
```

không biến thành `Result`.

Chúng thuộc unsafe/native semantics.

---

# 425.47 — Assertions

Axiom có:

```text
assert(condition)
debug_assert(condition)
```

`assert` có thể panic.

`debug_assert` có thể bị compiler remove ở release mode.

---

# 425.48 — Unreachable

Compiler intrinsic:

```text
unreachable()
```

biểu diễn:

```text
program invariant says this path cannot execute
```

Nếu execute → undefined behavior hoặc panic tùy API.

Core phải phân biệt hai forms:

```text
unreachable_unchecked()
unreachable()
```

nếu cần.

---

# 425.49 — Bounds errors

Ordinary safe array access:

```text
a[i]
```

có thể kiểm tra bounds.

Nếu compiler chứng minh:

```text
0 <= i < len
```

check được loại bỏ.

Unsafe unchecked access:

```text
a.get_unchecked(i)
```

cho phép bỏ check explicit.

---

# 425.50 — Error checking optimization

Ví dụ:

```text
x := try parse(...)
```

compiler có thể:

```text
call
test result tag
branch
```

và inline function.

Không có mandatory runtime dispatcher.

---

# 425.51 — Branch prediction

Error path có thể được đánh dấu:

```text
cold
unlikely
```

để optimizer/layout đặt failure path xa hot path.

Đây là optimization metadata, không thay đổi semantics.

---

# 425.52 — Error path code splitting

Compiler có thể tách:

```text
hot success path
cold error path
```

giúp instruction cache.

Đặc biệt hữu ích cho:

```text
parsers
network servers
serialization
system APIs
```

---

# 425.53 — Error context without allocation

Có thể dùng:

```text
struct Error {
    code: u32
    location: SourceLocation
}
```

thay vì:

```text
String message
```

để giữ allocation-free.

Formatting xảy ra chỉ khi log/display.

---

# 425.54 — Error location

Compiler có thể encode:

```text
file
line
column
function
```

chỉ trong debug/diagnostic builds.

Release build có thể strip.

---

# 425.55 — Error backtrace

Backtrace phải optional.

```text
Build profile:
    backtrace = off
```

→ không có metadata/runtime overhead ngoài mức cần thiết.

---

# 425.56 — Error logging

Logging không phải error semantics.

```text
log(error)
```

là side effect riêng.

Không được tự động log mọi `Err`.

---

# 425.57 — Error recovery

Function có thể:

```text
return Err(e)
```

hoặc recover:

```text
match e {
    ...
}
```

Axiom không tự retry.

Retry policy thuộc application/library.

---

# 425.58 — Error wrapping

Có thể:

```text
AppError.wrap(IOError)
```

nhưng wrapping không bắt buộc heap allocation.

Compiler/library có thể cung cấp inline error enums.

---

# 425.59 — Error hierarchy

Không cần class hierarchy:

```text
Error
 ├── IOError
 ├── ParseError
 └── NetworkError
```

Thay vào đó:

```text
enum AppError {
    IO(IOError)
    Parse(ParseError)
    Network(NetworkError)
}
```

Phù hợp với struct-only/classless design của Axiom.

---

# 425.60 — Dynamic error interface

Khi cần plugin architecture:

```text
Box<dyn Error>
```

hoặc equivalent interface object.

Đây là explicit dynamic dispatch.

Không ảnh hưởng static error code.

---

# 425.61 — Error interface and vtable

Nếu dùng dynamic error:

```text
data pointer
+
vtable pointer
```

theo model dynamic interface object của 422.

Không có hidden universal object header.

---

# 425.62 — Panic boundary across FFI

Axiom không được để panic/unwind xuyên qua foreign ABI một cách mặc định.

Ví dụ:

```text
Axiom → C
```

panic phải:

```text
catch
convert
abort
```

theo declared boundary.

---

# 425.63 — C callback into Axiom

Ngược lại:

```text
C → Axiom callback
```

callback phải có defined panic behavior.

Recommended:

```text
panic at FFI boundary → catch + error/abort
```

không unwind qua C nếu ABI không hỗ trợ.

---

# 425.64 — Exception ABI

Nếu bật exceptions:

Compiler cần abstraction:

```text
ExceptionPersonality
LandingPad
CleanupPad
Throw
Catch
Resume
```

Nhưng đây chỉ là IR/backend feature.

---

# 425.65 — Exception tables

Native target có thể dùng:

```text
EH tables
unwind metadata
landing pads
```

Chỉ emitted khi unwind/exception được sử dụng.

---

# 425.66 — Exception versus Result

Không đặt một cơ chế “thắng” cơ chế kia.

Rule:

```text
Result → expected/recoverable failure
Panic → violated invariant/unrecoverable local failure
Exception → optional dynamic/unwind mechanism
Abort → terminal failure
```

---

# 425.67 — Panic should not replace Result

Không khuyến khích semantics kiểu:

```text
open() → File
```

rồi:

```text
missing file → panic
```

nếu missing file là expected application condition.

API nên:

```text
open() -> Result<File, IOError>
```

---

# 425.68 — No hidden exception edges

Ordinary function:

```text
fn add(a: i32, b: i32) -> i32
```

không có hidden:

```text
throws
```

control-flow edge.

Đây giúp optimizer và ABI đơn giản.

---

# 425.69 — Function effect metadata

Advanced compiler IR có thể track:

```text
MayPanic
NoPanic
MayAllocate
NoAllocate
MayBlock
Async
```

Nhưng không nhất thiết đưa toàn bộ thành source-level type system.

---

# 425.70 — `no_panic`

Có thể hỗ trợ attribute:

```text
@no_panic
fn critical() { ... }
```

Compiler diagnostic nếu function có path panic.

Useful cho:

```text
embedded
kernel
signal handlers
critical runtime
```

---

# 425.71 — `no_alloc`

Tương tự:

```text
@no_alloc
```

yêu cầu function không allocation.

Compiler/static analyzer có thể enforce trong phạm vi khả thi.

---

# 425.72 — `no_block`

Có thể:

```text
@no_block
```

cho realtime/async-sensitive code.

Đây là effect metadata, không phải mandatory core complexity.

---

# 425.73 — Error contracts

Function signature:

```text
fn parse(input: str) -> Result<Ast, ParseError>
```

đã document failure domain.

Không cần:

```text
throws ParseError
```

cho ordinary errors.

---

# 425.74 — Generic Result

`Result<T,E>` phải là generic ordinary type.

Không phải compiler magic object.

Compiler chỉ cần optimization special cases.

---

# 425.75 — Monomorphization

Static generic:

```text
Result<i32, IOError>
Result<Data, ParseError>
```

có thể monomorphize.

Không cần dynamic runtime generic.

---

# 425.76 — Result layout specialization

Compiler có thể specialize:

```text
Result<T, E>
```

theo:

```text
T layout
E layout
niche
ABI
```

để giảm size.

---

# 425.77 — Error propagation and tail calls

Nếu:

```text
fn a() -> Result<T,E> {
    return b()
}
```

compiler có thể thực hiện tail call nếu ABI/semantics cho phép.

Không cần unwrap/rewrap unnecessarily.

---

# 425.78 — Result + ownership

Nếu:

```text
x := try make_resource()
```

ownership của `x` thuộc caller scope.

Nếu subsequent operation fail:

```text
return Err(e)
```

compiler phải cleanup `x` trước return nếu nó chưa moved.

---

# 425.79 — Result + partial initialization

Nếu Result error xảy ra trong constructor:

```text
a acquired
b failed
```

compiler cleanup:

```text
drop(a)
return Err
```

không drop uninitialized `b`.

---

# 425.80 — Error in destructor

Destructor failure là vấn đề đặc biệt.

Axiom nên quy định:

> **Destructor không được phép trả ordinary `Result` trong implicit scope cleanup.**

Destructor phải:

```text
succeed
```

hoặc:

```text
panic/abort
```

theo explicit semantics.

Lý do là nếu destructor vừa fail vừa đang xử lý một failure khác, error composition rất phức tạp.

---

# 425.81 — Panic during panic cleanup

Nếu đang unwind và destructor panic lần nữa:

Recommended policy:

```text
double panic during unwind → abort
```

để tránh recursive failure không kiểm soát.

---

# 425.82 — Async panic

Async task panic:

```text
Future poll
   ↓
panic
```

executor xử lý theo task policy.

Owned state của future phải được cleanup.

---

# 425.83 — Channel error

Channel có thể trả:

```text
SendError<T>
ReceiveError
```

thay vì panic khi channel closed.

Ví dụ:

```text
try tx.send(value)
```

Nếu send thất bại, ownership của `value` phải có semantics rõ ràng — thường trả lại value cho sender nếu chưa được accepted.

---

# 425.84 — Cancellation error

Cancellation nên là một trạng thái/error có thể phân biệt:

```text
Cancelled
```

nhưng không nhất thiết là panic.

---

# 425.85 — Timeout

Timeout là expected failure:

```text
TimeoutError
```

không phải panic.

---

# 425.86 — Retry

Retry không thuộc core error semantics.

Library có thể:

```text
retry(operation, policy)
```

với `Result`.

---

# 425.87 — Error composition

Parallel operations:

```text
A
B
C
```

có thể cần:

```text
Vec<Error>
```

Standard library xử lý aggregation.

Core chỉ cần generic `Result`.

---

# 425.88 — Diagnostics

Compiler phải phân biệt:

```text
error[E001] type mismatch
error[E002] non-exhaustive match
error[E003] value moved
error[E004] panic across FFI boundary
```

Error IDs ổn định để AI tooling dễ parse.

---

# 425.89 — Machine-readable diagnostics

Compiler phải có format:

```text
--diagnostic=json
```

hoặc tương đương.

Output:

```text
{
    "code": "...",
    "severity": "...",
    "file": "...",
    "range": "...",
    "message": "...",
    "notes": [...]
}
```

Điều này rất quan trọng với AI agent.

---

# 425.90 — Compiler optimization contract

Compiler có thể:

```text
inline Result
remove redundant tag tests
merge error blocks
cold-split failure paths
eliminate impossible branches
specialize error layout
```

nhưng không được thay đổi observable error semantics.

---

# 425.91 — Error path code generation

Ví dụ:

```text
fn parse(x) -> Result<i32, Error>
```

có thể compile:

```text
call parse
test status
jne .error
; hot path
...
.error:
...
```

Failure path có thể nằm xa hot path trong text section.

---

# 425.92 — Minimal runtime

Một program chỉ dùng:

```text
Result
Option
match
```

không cần exception runtime.

Một program dùng:

```text
panic = abort
```

chỉ cần minimal panic handler.

---

# 425.93 — Kernel/freestanding error model

Kernel code có thể:

```text
Result<T,E>
panic = abort
```

mà không cần:

```text
heap
filesystem
threads
exception runtime
```

---

# 425.94 — WebAssembly

WASM target có thể dùng:

```text
Result
Option
```

native.

Exception proposal support nếu target/runtime hỗ trợ có thể là optional backend.

---

# 425.95 — Error handling test matrix

Compiler conformance cần test:

```text
Result
Option
match
try propagation
error conversion
move-on-error
drop-on-error
panic
abort
unwind
nested cleanup
FFI
async failure
thread failure
channel failure
OOM
```

---

# 425.96 — Golden ABI tests

Phải có tests:

```text
Result<i32,i32>
Result<i64,SmallError>
Option<Pointer>
Option<NonZeroInt>
Result<LargeStruct,Error>
```

trên:

```text
x86-64 SysV
x86-64 Win64
AArch64
WASM
```

---

# 425.97 — Hard invariants

BOOTSTRAP-425 khóa:

1. `Result<T,E>` là cơ chế expected failure mặc định.
2. `Option<T>` biểu diễn absence.
3. `panic` dành cho invariant/program failure.
4. `abort` là panic mode tối giản.
5. `unwind` là optional.
6. Exception không phải error mechanism mặc định.
7. `Result` không cần heap allocation.
8. Error value là ordinary type.
9. Error có thể Copy/Move tùy semantics.
10. Cleanup của error dùng ownership model 423.
11. `Result` integrate với `match`.
12. Error propagation phải có syntax ngắn, zero-allocation.
13. FFI boundary không được unwind tùy tiện.
14. Async/thread errors sử dụng ordinary Result/error types.
15. Destructor không trả ordinary Result.
16. Double panic trong unwind → abort.
17. Success path phải tối ưu gần zero-cost.
18. Không có hidden exception edges trong ordinary functions.
19. Exception machinery chỉ emitted khi cần.
20. Compiler diagnostics phải machine-readable.

---

# 425.98 — Final Axiom failure model

```text
                         FAILURE
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
       Expected          Invariant        Terminal
          │                 │                 │
       Result             Panic             Abort
          │                 │
          │          ┌──────┴──────┐
          │          ▼             ▼
          │        abort         unwind
          │                        │
          │                   optional catch
          │
          └──────────────┐
                         ▼
                    normal control
```

Đây là mô hình phù hợp với mục tiêu của Axiom hơn việc biến mọi failure thành exception.

---

# BOOTSTRAP-426 — GENERICS, TRAITS, INTERFACES & STATIC/DYNAMIC POLYMORPHISM

Phần tiếp theo cần giải quyết một câu hỏi lớn của thiết kế Axiom: **làm sao có abstraction mạnh mà không cần class hierarchy và virtual dispatch mặc định**.

Mục tiêu sẽ là:

```text
426.1    generic design goals
426.2    generic functions
426.3    generic structs
426.4    generic enums
426.5    generic aliases
426.6    type parameters
426.7    const parameters
426.8    compile-time parameters
426.9    trait model
426.10   trait declaration
426.11   trait implementation
426.12   trait constraints
426.13   static dispatch
426.14   monomorphization
426.15   specialization
426.16   associated types
426.17   associated constants
426.18   default implementations
426.19   extension methods
426.20   struct-first methods
426.21   override model
426.22   interface objects
426.23   vtables
426.24   dynamic dispatch
426.25   object safety
426.26   generic + dynamic interoperability
426.27   type erasure
426.28   existential values
426.29   operator traits
426.30   conversion traits
426.31   equality/order traits
426.32   iteration traits
426.33   async traits
426.34   Send/Share integration
426.35   ABI of generics
426.36   FFI generics
426.37   code bloat control
426.38   linker deduplication
426.39   compile-time performance
426.40   diagnostics
426.41   AI-friendly generic syntax
426.42   conformance tests
426.43   final generic/trait contract
```

Trọng tâm của **426** sẽ là khóa kiến trúc **struct-only + trait + static dispatch mặc định + dynamic interface khi programmer yêu cầu**, thay vì đưa class/inheritance vào core.