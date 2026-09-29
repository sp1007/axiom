# BOOTSTRAP-171 — Error Handling, Result/Option, Panic, Contracts & Failure Semantics
**FROZEN / COMPLETED**

Mục tiêu của Axiom:

> **Recoverable failure là dữ liệu. Unrecoverable failure là control flow. Không có exception machinery bắt buộc.**

Thiết kế này giữ error handling explicit, zero-cost khi không dùng và tương thích với ownership/Drop/async/FFI/GPU đã đóng băng.

---

## 171.1. Ba trạng thái phải tách biệt

Axiom phân biệt:

```text id="3xq6m8"
Option<T>
    có hoặc không có giá trị

Result<T,E>
    thành công hoặc recoverable error

Panic
    computation không thể tiếp tục theo normal contract
```

Không dùng một cơ chế duy nhất cho cả ba.

---

# 171.2. `Option<T>`

Dùng khi **absence là một trạng thái bình thường**.

```ax id="w9g7qv"
fn find(id: Id) -> Option<User>
```

Các trạng thái:

```text id="l8f2qy"
Some(value)
None
```

Không có `null`.

Compiler có thể tối ưu Option bằng niche representation khi representation không observable.

Ví dụ một Option của một kiểu có representation phù hợp có thể có cùng kích thước với kiểu đó.

---

# 171.3. `Result<T, E>`

Dùng khi failure mang thông tin hoặc có khả năng recover.

```ax id="4r9x0m"
fn read_file(path: Path) -> Result<String, IoError>
```

Semantic:

```text id="p6yq6b"
Ok(T)
Err(E)
```

Không tạo exception object.

Không yêu cầu stack unwinding.

Không yêu cầu runtime.

---

# 171.4. `?` — Error propagation

Axiom hỗ trợ:

```ax id="3o9v9p"
let data = read_file(path)?;
```

Semantic:

```text id="6i7b8m"
Ok(x)
    → continue

Err(e)
    → return Err(e)
```

`?` không phải exception.

Compiler lower trực tiếp thành branch/control flow.

Do đó:

```text id="2l4m5v"
Result
+
?
```

có thể compile gần như:

```text id="z6n2e5"
branch
```

không có hidden runtime.

---

# 171.5. Error propagation và Drop

Nếu function có:

```ax id="m5x0ne"
let a = acquire_a()?;
let b = acquire_b()?;
```

và `acquire_b()` thất bại:

```text id="w0y2g3"
b không tồn tại
a được Drop
Err được return
```

Compiler cleanup graph đảm bảo exactly-once destruction.

Không cần programmer viết:

```text id="9vtxx3"
try/finally
```

cho resource cleanup thông thường.

---

# 171.6. Error không được bỏ qua âm thầm

Một `Result<T,E>` không tự động biến thành `T`.

Nếu function trả:

```ax id="7p2x9n"
Result<T,E>
```

caller phải:

```text id="6kzjvf"
handle
?
match
map
unwrap/expect
explicit discard
```

tùy API policy.

Compiler có thể cảnh báo nếu `Result` bị bỏ qua.

---

# 171.7. Explicit discard

Nếu programmer thực sự không quan tâm:

```ax id="j4p1a8"
let _ = operation();
```

hoặc API tương đương.

Điều này phân biệt:

```text id="w1r9i5"
"I forgot to handle error"
```

với:

```text id="8v4c2x"
"I intentionally ignored it"
```

---

# 171.8. Error type là type bình thường

Không có một global `Exception` hierarchy.

Ví dụ:

```ax id="k3y1q8"
enum IoError {
    NotFound,
    PermissionDenied,
    InvalidData,
    Closed,
}
```

Error có thể là:

```text id="z8d4s2"
enum
struct
newtype
integer code
OS error
FFI error
```

tùy subsystem.

---

# 171.9. Không bắt buộc heap allocation cho error

Error:

```ax id="4m0k1z"
Err(IoError::NotFound)
```

có thể nằm hoàn toàn trong register/stack/return value.

Không cần:

```text id="7k5q1x"
heap allocation
virtual exception object
reference counting
```

trừ khi programmer/library semantic contract yêu cầu.

---

# 171.10. Error composition

Generic code có thể dùng error conversion explicit.

Ví dụ conceptual:

```ax id="5j4k8v"
fn load() -> Result<Data, AppError> {
    let x = read()?;
    let y = parse(x)?;
    Ok(y)
}
```

Compiler phải biết cách:

```text id="a6q4m3"
IoError → AppError
ParseError → AppError
```

thông qua explicit conversion/trait contract.

Không tự động chạy arbitrary conversion chỉ vì có thể.

---

# 171.11. `Result` không đồng nghĩa exception

Đây là invariant quan trọng:

```text id="8k2p6c"
Result<T,E>
    = ordinary value

panic
    = control-flow termination

unwind
    = optional panic implementation strategy
```

Không được để compiler implementation trộn ba khái niệm.

---

# 171.12. Panic

`panic` là diverging operation:

```text id="q7w5r2"
panic(...)
```

type:

```text id="f2k6x1"
never
```

Nó không return normally.

---

# 171.13. Panic policy

Build profile chọn:

```text id="8q3w5m"
panic = abort
panic = unwind
panic = custom
```

### `abort`

Không cần unwind machinery.

Binary nhỏ hơn.

Phù hợp:

```text id="j5h8q1"
embedded
freestanding
size-critical
some production binaries
```

### `unwind`

Stack cleanup được thực hiện.

Drop semantics vẫn phải chính xác.

---

# 171.14. Panic không phải recoverable error

Không thiết kế:

```text id="9y7p4b"
try {
   ...
}
catch panic {
   ...
}
```

làm cơ chế error handling thông thường.

Nếu operation dự kiến có failure:

```text id="m2d8q7"
Result<T,E>
```

Nếu programmer muốn panic recovery ở một boundary đặc biệt, đó là runtime/profile mechanism, không phải default error model.

---

# 171.15. Panic và Drop

Nếu:

```ax id="0r3j6c"
let resource = acquire();
panic("failure");
```

thì với:

```text id="5h9v1a"
panic=unwind
```

compiler phải đảm bảo cleanup.

Với:

```text id="v7d2n4"
panic=abort
```

không cần chạy arbitrary cleanup sau khi process abort.

Semantic distinction này cho phép binary nhỏ hơn.

---

# 171.16. Double panic

Nếu Drop đang xử lý unwind mà lại panic:

```text id="0q6x3m"
panic
 ↓
Drop
 ↓
panic again
```

không cho phép tiếp tục unwind bình thường.

Runtime policy có thể terminate/abort.

Mục tiêu là không tạo trạng thái cleanup không xác định.

---

# 171.17. Drop không trả Result

Không cho:

```text id="a1c6w9"
Drop::drop() -> Result<...>
```

vì compiler cleanup path không nên biến thành một exception/error propagation graph phức tạp.

Nếu cleanup có thể thất bại:

```ax id="v3x5p7"
resource.close() -> Result<(), Error>
```

phải được gọi explicit trước khi resource bị Drop.

---

# 171.18. `close()` và `Drop`

Mẫu:

```ax id="s4y7q2"
let file = File.open(path)?;

file.write(data)?;
file.close()?;
```

Nếu programmer quên `close()`:

```text id="r9m1k5"
Drop(file)
```

vẫn phải release resource.

Nhưng semantic "close succeeded" là trách nhiệm của explicit `close()`.

---

# 171.19. Contracts

Axiom cần contracts, nhưng không nên biến Core v0.1 thành một hệ thống Design-by-Contract khổng lồ.

Đề xuất:

```text id="h2k7m4"
assert
debug_assert
precondition
postcondition
invariant
```

được phân tầng.

---

# 171.20. `assert`

```ax id="c8n2w5"
assert(x < n);
```

là runtime check nếu compiler không chứng minh được.

Nếu compiler chứng minh:

```text id="d6v1q9"
x < n
```

thì có thể loại bỏ check.

Nếu assertion failure:

```text id="n5m8s2"
panic
```

hoặc configured failure policy.

---

# 171.21. `debug_assert`

```ax id="k7p3x1"
debug_assert(condition);
```

có thể được loại bỏ trong release profile.

Khác biệt với semantic safety checks:

> Compiler không được loại bỏ một check mà language semantics yêu cầu chỉ vì release mode.

`debug_assert` là explicit programmer-selected diagnostic behavior.

---

# 171.22. Preconditions

Boundary API có thể có precondition:

```text id="j8q4m6"
requires x < len
```

nhưng Axiom không yêu cầu programmer viết precondition cho mọi function.

Compiler/library có thể sử dụng contract metadata.

Nếu contract là semantic safety requirement, nó phải được verifier biết.

---

# 171.23. Contract hierarchy

```text id="2d8q5s"
Language semantic invariant
        ↑
Verified safety contract
        ↑
Explicit runtime contract
        ↑
Optimization assumption
        ↑
Profile observation
```

Không được đảo ngược.

Profile không thể biến một điều chưa được chứng minh thành safety fact.

---

# 171.24. Unsafe contracts

Unsafe API có thể yêu cầu:

```text id="c3v9m2"
/// SAFETY:
/// ptr points to N valid T elements
```

Compiler/tooling có thể lưu contract.

Nhưng:

```text id="f6k1p8"
unsafe
```

không có nghĩa:

```text
mọi thứ sau đó đúng
```

Trusted fact chỉ có phạm vi xác định.

---

# 171.25. Result + unsafe

Một unsafe operation vẫn có thể trả:

```text id="h5q8n1"
Result<T,E>
```

Ví dụ lỗi runtime vẫn có thể tồn tại dù memory preconditions đã được trusted.

Unsafe không biến mọi failure thành panic.

---

# 171.26. Assertions và optimizer

Ví dụ:

```ax id="g4m7x2"
assert(i < n);
out[i] = value;
```

Verifier/range analysis có thể ghi nhận:

```text id="p9c2v5"
i < n
```

và bounds-check phía sau có thể bị loại bỏ.

Nhưng nếu assertion có side effect observable, optimizer phải giữ semantics.

---

# 171.27. Error handling không được tạo hidden control flow

`Result`:

```text id="b6n1r4"
Ok
Err
```

là ordinary branch/data.

`?`:

```text id="u8q3k6"
branch
return
```

Panic:

```text id="m1v7x5"
diverge
```

Exception runtime không xuất hiện nếu programmer không chọn panic-unwind hoặc một library mechanism yêu cầu nó.

---

# 171.28. Async + Result

Async function:

```ax id="e4k8p2"
async fn fetch() -> Result<Data, Error>
```

trả Future chứa:

```text id="j9q5s3"
Future<Result<Data,Error>>
```

`?` trong async vẫn là normal Result propagation.

`await` chỉ thêm suspension.

Không tạo exception machinery.

---

# 171.29. Cancellation khác error

Cancellation không được encode mặc định thành panic.

Có thể có:

```text id="w2m6q9"
Result<T, E>
```

với cancellation error nếu API định nghĩa như vậy.

Nhưng compiler/runtime vẫn phân biệt:

```text id="s7k4p1"
failure
cancellation
panic
```

về semantics.

---

# 171.30. GPU errors

GPU launch:

```text id="v5q8m2"
launch(kernel)
```

có thể trả:

```text id="h1x6n4"
Result<GpuEvent, GpuError>
```

Device execution failure không tự động biến thành host panic.

API quyết định khi nào error được quan sát.

---

# 171.31. FFI errors

FFI phải có explicit mapping:

```text id="e3k7q1"
C errno
HRESULT
Win32 error
POSIX status
Objective-C/Swift error boundary
JNI status
```

thành Axiom `Result`.

Không giả định foreign function dùng Axiom panic/Result semantics.

---

# 171.32. Error ABI

`Result<T,E>` ABI được quyết định bởi ABI lowering.

Compiler có thể sử dụng:

```text id="s6n9w3"
register
multiple registers
hidden result
tag + payload
niche
```

tùy target.

Không yêu cầu một universal runtime representation.

---

# 171.33. Niche optimization

Ví dụ semantic:

```text id="p8c4y6"
Option<T>
Result<T,E>
```

có thể được representation optimizer nén nếu có unused bit patterns.

Nhưng:

```text id="r2v7m5"
representation optimization
```

không được thay đổi:

```text
match semantics
Drop semantics
validity
ABI contract
```

---

# 171.34. Error enums

Compiler nên tối ưu error enums mạnh.

Ví dụ:

```ax id="c5x1q8"
enum ParseError {
    UnexpectedEnd,
    InvalidDigit,
    Overflow,
}
```

có thể trở thành:

```text id="t9m4k2"
small integer/tag
```

nếu payload không cần.

Không cần object allocation.

---

# 171.35. Error context

Context có thể được thêm explicit:

```ax id="z7p2m6"
read(path)
    .context("loading configuration")?
```

Nếu context cần heap/string allocation thì cost phải xuất hiện trong abstraction semantics.

Không được bắt mọi error phải tạo stack trace/string.

---

# 171.36. Stack traces

Stack trace thuộc panic/debug runtime, không phải `Result`.

```text id="y4k8n2"
Result
    → no implicit stack trace

panic
    → stack trace optional
```

Điều này tránh overhead trên normal recoverable-error path.

---

# 171.37. Error logging

Không có global error logger implicit.

Programmer/library chọn:

```text id="q2m5v7"
stderr
logger
telemetry
structured error
ignore
```

Runtime-free applications không bị kéo theo logging runtime.

---

# 171.38. Typed error hierarchy

Không cần class inheritance.

Có thể dùng:

```text id="u5x8c1"
trait Error
```

và:

```text id="r7n2m4"
struct IoError
struct ParseError
struct NetworkError
```

Dynamic error:

```text id="k3q6p9"
dyn Error
```

chỉ khi programmer cần.

Static generic error là default.

---

# 171.39. `Error` trait

Nên có std trait nhỏ:

```text id="e8v1q5"
trait Error {
    fn message(self: view<Self>) -> Str;
}
```

nhưng không ép mọi error phải:

- allocate string
- capture stack
- dynamic dispatch
- heap box.

---

# 171.40. Error aggregation

Các API như:

```text id="b7m4x9"
collect_errors
validate_all
```

có thể aggregate nhiều errors.

Đây là library semantics, không phải exception system.

Ví dụ:

```text id="p1q6v8"
Vec<ValidationError>
```

hoàn toàn đủ.

---

# 171.41. Contracts và compile-time

Nếu contract có thể chứng minh tại comptime:

```ax id="x5n8c3"
const N = 16;
assert(N > 0);
```

compiler có thể evaluate.

Nếu thất bại:

```text id="q7m2v4"
compile-time diagnostic
```

Không sinh runtime check.

---

# 171.42. Contracts không được bypass verifier

Một programmer không thể viết:

```text id="g4c9x1"
@assume_safe(...)
```

rồi khiến verifier coi arbitrary memory operation là safe.

Chỉ các trusted/system boundaries được phép thiết lập trusted facts theo contract model.

---

# 171.43. Error và optimizer

Optimization được phép:

```text id="k6p3y8"
eliminate impossible Err branch
```

nếu compiler **đã chứng minh** branch unreachable.

Không được dùng profile:

```text "99.99% luôn Ok"
```

để xóa `Err`.

Profile chỉ ảnh hưởng profitability.

---

# 171.44. Error và code size

Một trong những lợi thế của model này:

```text id="v9m5q2"
Result<T,E>
```

không cần runtime nếu chương trình chỉ sử dụng static error flow.

Nếu:

```text id="x3k7n1"
panic=abort
```

compiler có thể loại bỏ toàn bộ unwind subsystem.

Binary size có thể rất nhỏ.

---

# 171.45. Error handling architecture

```text id="s4n8x2"
                Function
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
     Option     Result      Panic
        │          │          │
     absence    recoverable  terminate
                   │          │
                   ↓          ↓
                   ?       abort/unwind
                   │
                   ↓
                cleanup
```

Không có:

```text id="p6y2m9"
global exception runtime
```

---

# 171.46. Error lowering

```text id="z8q4c1"
Typed HIR
   ↓
MIR
   ↓
Result branches
   ↓
Drop/cleanup edges
   ↓
SSA
   ↓
branch optimization
   ↓
ABI lowering
```

`?` biến mất sau MIR lowering.

`Result` có thể tiếp tục tồn tại hoặc được scalarize.

---

# 171.47. Error + ownership

Đây là điểm Axiom có thể mạnh hơn nhiều language đơn giản:

```text id="w5m8k2"
Result<T,E>
```

được verifier xử lý như ordinary aggregate.

Ví dụ:

```text id="n3q7p1"
Result
 ├── Ok(T)
 │     └── ownership T
 │
 └── Err(E)
       └── ownership E
```

Chỉ active variant mới sở hữu payload.

Drop phải dựa trên discriminant.

---

# 171.48. Pattern matching

```ax id="j4x9m6"
match result {
    Ok(value) => use(value),
    Err(error) => handle(error),
}
```

được kiểm tra exhaustive.

Không cần:

```text
catch
finally
```

cho normal error flow.

---

# 171.49. Error conversion không implicit quá mạnh

Axiom nên tránh "magic":

```text id="u7p3k5"
mọi Error → mọi Error
```

Thay vào đó conversion phải có trait/API rõ ràng.

Điều này giúp compiler và AI xác định chính xác:

```text
source error
→ conversion
→ destination error
```

---

# 171.50. Invariants đóng băng

### Core failure semantics

- **AERR-20** — `Option<T>` biểu diễn absence.
- **AERR-21** — `Result<T,E>` biểu diễn recoverable failure.
- **AERR-22** — `Result` là ordinary value semantics.
- **AERR-23** — `?` là structured control-flow propagation, không phải exception.
- **AERR-24** — recoverable errors không yêu cầu heap allocation.
- **AERR-25** — `Result` không tự tạo stack trace.
- **AERR-26** — error handling không yêu cầu monolithic runtime.
- **AERR-27** — error payload tuân theo ownership/Drop semantics.
- **AERR-28** — chỉ active enum variant sở hữu payload.
- **AERR-29** — unused `Result` phải explicit hoặc compiler diagnostic.

### Panic

- **APANIC-20** — panic có type `never`.
- **APANIC-21** — panic không phải recoverable Result.
- **APANIC-22** — panic policy là build/profile/runtime configuration.
- **APANIC-23** — `panic=abort` không yêu cầu unwind machinery.
- **APANIC-24** — `panic=unwind` phải bảo đảm deterministic cleanup.
- **APANIC-25** — Drop không recoverably fail.
- **APANIC-26** — panic trong cleanup/unwind lần hai phải terminate/abort theo policy.
- **APANIC-27** — panic semantics không phụ thuộc optimization level.

### Contracts

- **ACONTRACT-20** — assertions là explicit runtime/compile-time checks.
- **ACONTRACT-21** — `debug_assert` có thể bị loại bỏ theo explicit profile.
- **ACONTRACT-22** — semantic safety checks không được loại bỏ tùy optimization profile.
- **ACONTRACT-23** — verified contracts có thể feed range/alias/optimization analysis.
- **ACONTRACT-24** — profile observation không phải semantic proof.
- **ACONTRACT-25** — unsafe contracts thiết lập trusted facts có phạm vi xác định.
- **ACONTRACT-26** — contracts không bypass ownership/capability verifier.

### Async/GPU/FFI

- **AERR-30** — async `Result` không tạo exception machinery.
- **AERR-31** — cancellation khác panic.
- **AERR-32** — GPU/device failure có error semantics riêng.
- **AERR-33** — FFI error conversion phải explicit.
- **AERR-34** — foreign code không tự động tuân theo Axiom panic/Result semantics.

### Optimization

- **AERR-40** — impossible error branches có thể được loại bỏ khi được chứng minh unreachable.
- **AERR-41** — profile không thể loại bỏ recoverable error branches.
- **AERR-42** — Result/Option representation có thể được niche-optimized.
- **AERR-43** — representation optimization không thay đổi semantic variant/drop behavior.
- **AERR-44** — error abstraction có thể được inline/scalarize/eliminate.
- **AERR-45** — error semantics phải được xác định trước ABI lowering.

---

## BOOTSTRAP-171 đã đóng băng

Kiến trúc error của Axiom giờ rất rõ:

```text
Option
  → absence

Result
  → expected/recoverable failure

panic
  → unrecoverable control flow

unsafe contract
  → trusted machine/safety precondition
```

và quan trọng nhất:

```text
Result + ?
       ↓
ordinary CFG
       ↓
Drop cleanup
       ↓
SSA/optimization
       ↓
native branch/register code
```

Không cần exception runtime chỉ để xử lý lỗi thông thường.

---

# BOOTSTRAP-172 — Conversions, Casting, Coercion & Type-Safe Interoperability

Task tiếp theo cần khóa một khu vực rất dễ làm ngôn ngữ systems trở nên nguy hiểm hoặc đầy "magic":

```text
implicit conversion
explicit cast
numeric conversion
pointer conversion
newtype conversion
Option/Result conversion
view conversion
String/Bytes conversion
FFI conversion
bitcast
transmute-like operations
coercion
generic conversion traits
```

Mục tiêu là chốt một nguyên tắc:

> **Axiom phải cho phép compiler hiểu và tối ưu conversion rất mạnh, nhưng programmer luôn biết khi nào dữ liệu thực sự thay đổi, khi nào chỉ thay đổi cách nhìn, và khi nào đang thực hiện một operation machine-level nguy hiểm.**