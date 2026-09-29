Tiếp tục. Tôi sẽ xử lý **Execution & Error Semantics v0.1**, và đặc biệt chốt vấn đề `defer`, vì đây là chỗ dễ vô tình kéo Axiom về mô hình C++/Go/Rust quá phức tạp.

# AXIOM EXECUTION & ERROR SEMANTICS v0.1

**Trạng thái: PROPOSED**

Mục tiêu của phần này là làm cho câu hỏi:

> "Nếu chương trình gặp lỗi, return sớm, panic, overflow hoặc resource cleanup thì chính xác CPU phải làm gì?"

có câu trả lời **deterministic**.

---

# 1. Axiom không có exception như C++

Tôi đề xuất freeze:

> **Axiom Core không có exception mechanism kiểu C++/Java/C#.**

Không có:

```text
throw
try
catch
finally
```

trong core.

Lý do không phải vì exception luôn chậm, mà vì nó tạo ra một control-flow model khá phức tạp và khó dự đoán.

Axiom thay bằng:

```text
Result<T, E>
Option<T>
panic
trap
return
```

---

# 2. Bốn loại kết thúc execution

Một function có thể kết thúc bằng:

```text
                 FUNCTION EXIT
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    success          error       abnormal
       │              │              │
    return         Result         panic/trap
```

Cụ thể:

### Normal return

```axiom
return value
```

### Recoverable error

```axiom
return Err(error)
```

### Panic

Invariant chương trình bị phá hoặc lỗi không thể/không muốn recover.

```text
panic(...)
```

### Trap

Lỗi execution-level không thể tiếp tục.

Ví dụ:

```text
invalid instruction
hardware fault
explicit trap
```

---

# 3. `Result` là cơ chế error chính

Ví dụ:

```axiom
fn read_file(path: Text) -> Result<File, IOError>
```

Có:

```text
Ok(file)
Err(error)
```

Compiler không cần runtime exception machinery.

Với optimization:

```text
Result<File, IOError>
```

có thể được truyền bằng register/stack tùy ABI.

---

# 4. Error propagation phải cực kỳ đơn giản

Ta cần một cú pháp thuận tiện, nhưng **không nên freeze cú pháp vội**.

Conceptual:

```axiom
fn load() -> Result<Data, Error> {
    let file = open(path)?
    let data = read(file)?
    return Ok(data)
}
```

`?` chỉ là syntax sugar cho:

```text
match result {
    Ok(v) => v
    Err(e) => return Err(e)
}
```

Điều này rất hợp với Axiom vì:

```text
no exception runtime
no hidden control flow
```

---

# 5. `Option`

Null không phải giá trị mặc định của Axiom.

Thay:

```text
null
```

bằng:

```text
Option<T>
```

Ví dụ:

```axiom
fn find(id: u64) -> Option<User>
```

Có:

```text
Some(user)
None
```

---

# 6. `panic`

`panic` dành cho:

- invariant violation
- programmer error
- unrecoverable application error
- explicit assertion failure

Ví dụ:

```axiom
assert(index < length)
```

hoặc:

```axiom
panic("unreachable state")
```

---

# 7. Panic không nhất thiết phải unwind

Đây là điểm rất quan trọng đối với binary size/performance.

Axiom nên hỗ trợ các **panic profiles**.

### Abort

```text
panic
 ↓
cleanup policy
 ↓
terminate
```

### Unwind

```text
panic
 ↓
stack unwinding
 ↓
Drop resources
 ↓
handler/top-level boundary
```

Nhưng tôi không muốn:

```text
unwind
```

là requirement của language core.

---

# 8. Profile-based semantics

Có thể compile:

```text
--panic=abort
```

hoặc:

```text
--panic=unwind
```

Nhưng phải đảm bảo:

> Safe resource semantics không được phá.

Nếu abort:

```text
panic
 ↓
program terminates
```

OS sẽ reclaim process resources.

Nếu unwind:

```text
panic
 ↓
Drop
 ↓
stack unwind
```

---

# 9. Có catch panic không?

Tôi đề xuất:

**Không có general-purpose catch trong Core v0.1.**

Nếu sau này cần:

```text
catch_unwind
```

thì nó có thể là một **explicit runtime/library boundary**, không phải exception system.

Điều này giữ core đơn giản.

---

# 10. `trap`

`trap` khác `panic`.

`panic` là language-level abnormal termination.

`trap` là:

> yêu cầu execution engine/CPU/backend dừng tại điểm này.

Ví dụ:

```axiom
trap()
```

Compiler có thể hạ thành:

```text
ud2
brk
ebreak
unreachable
```

tùy target.

---

# 11. `unreachable`

Có một semantic operation:

```axiom
unreachable()
```

Nó nói:

> Control flow không được tới đây trong một chương trình đúng.

Compiler có thể dùng thông tin này để optimize.

Ví dụ:

```axiom
match state {
    Active => ...
    Closed => ...
    _ => unreachable()
}
```

Compiler có thể loại bỏ branch tương ứng.

---

# 12. Assertion

Nên phân biệt:

```text
assert
debug_assert
```

### `assert`

Semantic assertion luôn tồn tại.

```axiom
assert(x != 0)
```

### `debug_assert`

Chỉ bật trong debug profile.

```axiom
debug_assert(expensive_check())
```

Điểm quan trọng:

> Compiler phải biết `debug_assert` có thể bị loại bỏ hoàn toàn.

---

# 13. Bounds checking

Axiom safe code phải kiểm tra:

```axiom
array[index]
```

nếu compiler không chứng minh index hợp lệ.

Ví dụ:

```text
if index < length
    → load
else
    → panic/trap
```

Nhưng optimizer có thể chứng minh:

```text
for i in 0..10
```

và:

```text
array length = 10
```

→ eliminate bounds checks.

---

# 14. Bounds check không phải runtime tax cố định

Đây là một trong những mục tiêu optimizer:

```text
Source:
a[i]

MIR:
bounds_check
load

Optimizer:
prove i < len

Machine:
load
```

Vì vậy Axiom không nên hy sinh safety chỉ để có performance.

---

# 15. Integer overflow

Đây là vấn đề cần thiết kế kỹ.

Tôi không muốn Axiom có C-style:

```text
signed overflow = undefined behavior
```

vì điều đó khiến semantics khó dự đoán và dễ tạo bug.

Thay vào đó, có các operation semantics rõ:

```text
checked
wrapping
saturating
```

Ví dụ conceptual:

```axiom
let x = a.checked_add(b)
let y = a.wrapping_add(b)
let z = a.saturating_add(b)
```

và có thể có operator bình thường:

```axiom
a + b
```

với semantics profile/compiler-defined rõ ràng.

Tôi nghiêng về:

> **normal arithmetic trong safe code phải có deterministic semantics, và compiler được phép trap/panic khi overflow nếu type/profile yêu cầu.**

Không được biến nó thành UB âm thầm.

---

# 16. Divide by zero

Safe code:

```axiom
a / b
```

với:

```text
b == 0
```

→ deterministic runtime failure.

Có thể:

```text
panic
```

hoặc:

```text
trap
```

tùy operation/profile.

Nhưng không được là:

```text
undefined behavior
```

---

# 17. Shift

Tương tự, phải quy định:

```text
x << amount
x >> amount
```

khi:

```text
amount >= bit_width
```

không được phụ thuộc ngầm vào CPU.

Có thể cung cấp:

```text
checked_shift
wrapping_shift
```

nếu cần.

---

# 18. Evaluation order

Axiom phải **freeze evaluation order deterministic**.

Ví dụ:

```axiom
f(a(), b())
```

phải có thứ tự xác định.

Tôi đề xuất:

> **Arguments được evaluate từ trái sang phải.**

Tương tự:

```axiom
a[i()]
```

thứ tự evaluation phải rõ.

Điều này giúp:

- compiler dễ debug
- AI dễ reasoning
- FFI dễ dự đoán
- tránh C/C++-style unspecified behavior.

---

# 19. Side effect

Ví dụ:

```axiom
f(x++, x++)
```

Axiom không nên cho phép semantics mơ hồ.

Hoặc compiler xác định:

```text
left-to-right
```

→ deterministic.

Hoặc tốt hơn, nếu ngôn ngữ không có `++`, vấn đề gần như biến mất.

Tôi nghiêng về việc **không đưa `++`/`--` vào core syntax**.

```text
x += 1
```

rõ ràng hơn.

---

# 20. `defer` — có nên giữ?

Đây là điểm tôi đã muốn xem xét kỹ.

Có hai mô hình.

### Model A — không có defer

Resource cleanup hoàn toàn dựa vào:

```text
Drop
```

Ví dụ:

```axiom
let file = open()

...
```

Compiler tự:

```text
DROP file
```

### Model B — có defer

```axiom
defer close(file)
```

---

# 21. Vấn đề của `defer`

`defer` rất tiện cho:

```text
temporary cleanup
FFI resource
C API
manual cleanup
```

Nhưng nó có thể tạo:

```text
hidden control flow
capture semantics
execution ordering complexity
```

Đặc biệt:

```axiom
defer foo()
return x
```

thì `foo()` chạy trước return.

Khi có:

```text
nested scope
panic
early return
async
closure
```

semantics bắt đầu phức tạp.

---

# 22. Tôi đề xuất: **không có `defer` trong Core**

Thay vào đó:

```text
Drop
scope
explicit cleanup function
```

Ví dụ resource type:

```axiom
struct File {
    ...
}

impl Drop for File {
    fn drop(self) {
        close(...)
    }
}
```

Compiler tự cleanup.

Điều này thống nhất với Memory Model.

---

# 23. Nhưng FFI cần cleanup nhanh

Thay vì `defer`, có thể có library abstraction:

```axiom
let guard = cleanup_guard(...)
```

hoặc:

```text
ScopeGuard
Defer
Finally
```

ở standard library.

Khi đó:

```text
defer
```

không phải language primitive.

Đây là distinction rất tốt:

```text
Core:
Drop

Library:
Defer
ScopeGuard
CleanupGuard
```

---

# 24. Có một ngoại lệ

Tôi vẫn muốn compiler có **scope cleanup primitive nội bộ**:

```text
DEFER_DROP
```

trong MIR.

Nhưng programmer không nhất thiết có keyword `defer`.

Ví dụ:

```text
Source
 ↓
let file = open()
 ↓
MIR
 ↓
cleanup edge
 ↓
DROP file
```

Compiler có thể gọi nó là:

```text
cleanup region
```

---

# 25. Early return

Ví dụ:

```axiom
fn process() -> Result<()> {
    let a = open_a()
    let b = open_b()

    if error() {
        return Err(...)
    }

    Ok(())
}
```

Compiler tạo:

```text
normal path:
    DROP b
    DROP a
    return Ok

error path:
    DROP b
    DROP a
    return Err
```

Không cần programmer viết cleanup.

---

# 26. Multiple return paths

MIR nên canonicalize:

```text
return x
return y
return Err(e)
```

thành:

```text
cleanup block
      ↓
return
```

Conceptual:

```text
block A ─┐
block B ─┼──► cleanup ──► return
block C ─┘
```

Điều này cực kỳ thuận lợi cho optimizer.

---

# 27. Drop flags

Nếu resource được conditionally initialized:

```axiom
let file: File?

if condition {
    file = open()
}
```

compiler cần biết:

```text
file initialized?
```

MIR có thể dùng:

```text
drop flag
```

nhưng optimizer có thể loại bỏ flag nếu control flow chứng minh được.

Đây là compiler implementation detail, không phải runtime object header.

---

# 28. Resource cleanup và panic

Ví dụ:

```axiom
let a = ResourceA()
let b = ResourceB()

panic()
```

Nếu panic profile là unwind:

```text
panic
 ↓
DROP b
 ↓
DROP a
 ↓
unwind
```

Nếu abort:

```text
panic
 ↓
terminate
```

Không nhất thiết phải chạy arbitrary destructors nếu process sắp chết, nhưng language profile phải quy định rõ.

---

# 29. `Drop` không được throw

Tôi đề xuất:

> `Drop` không được tạo recoverable exception.

Không có:

```text
Drop
 ↓
throw
```

Nếu cleanup failure cần được biểu diễn:

```text
close() -> Result
```

phải được xử lý **trước** khi destruction hoặc theo explicit API.

Destructor không nên trở thành error propagation mechanism.

---

# 30. Vì sao điều này quan trọng?

Nếu:

```text
Drop A
  ↓
error
  ↓
Drop B
  ↓
error
  ↓
panic
```

thì error semantics trở thành nightmare.

Axiom nên tránh.

Nguyên tắc:

> **Destruction is cleanup, not business-level error propagation.**

---

# 31. `Drop` và async cancellation

Khi async task bị cancel:

```text
Task
 ↓
cancel request
 ↓
task reaches cancellation point
 ↓
cleanup state
 ↓
Drop resources
```

Không được cưỡng bức cắt ngang arbitrary instruction sequence.

Như vậy:

```text
Drop
```

vẫn deterministic.

---

# 32. `await` không phải cancellation point bắt buộc?

Tôi đề xuất:

> `await` là một điểm suspension có khả năng cancellation, nhưng cancellation semantics cụ thể thuộc async runtime.

Điều này tránh việc language core phải biết scheduler.

---

# 33. `return` trong `defer` không có

Vì không có language-level `defer`, ta tránh được các vấn đề như:

```text
defer {
    return x
}
```

hoặc:

```text
defer modifies return value
```

Đây là một simplification đáng giá.

---

# 34. Error handling hierarchy

Kiến trúc sẽ là:

```text
                  ERROR
                    │
       ┌────────────┼────────────┐
       │            │            │
   Expected      Unexpected    Machine
       │            │            │
    Result        panic         trap
       │
    Option
```

### Expected

```text
Result<T,E>
Option<T>
```

### Unexpected

```text
panic
```

### Machine/runtime failure

```text
trap
```

---

# 35. Không có hidden error channel

Function:

```axiom
fn foo() -> i32
```

không ngầm có:

```text
exception
error register
hidden error object
```

Nó chỉ return:

```text
i32
```

Điều này giúp ABI và optimization đơn giản.

Nếu cần error:

```axiom
fn foo() -> Result<i32, Error>
```

thì type system biết rõ.

---

# 36. Result có thể zero-cost

Ví dụ:

```axiom
fn parse() -> Result<i32, ParseError>
```

Nếu:

```text
ParseError
```

nhỏ, compiler có thể trả:

```text
register
```

Không cần heap allocation.

Không cần exception object.

Không cần GC.

---

# 37. Compiler optimization của Result

Source:

```axiom
let x = parse()?
use(x)
```

MIR:

```text
r = parse()

switch r:
    Ok(v)  → continue
    Err(e) → return Err(e)
```

Optimizer có thể:

```text
register
branch
```

rất trực tiếp.

---

# 38. Execution semantics invariant

Tôi đề xuất:

```text id="6l9z83"
AES-01
Normal function termination occurs through explicit return/control-flow completion.

AES-02
Recoverable errors use Result/Option semantics.

AES-03
Core has no C++-style exception mechanism.

AES-04
panic is an explicit abnormal execution mechanism.

AES-05
trap is an execution-level termination mechanism.

AES-06
Safe arithmetic has deterministic semantics.

AES-07
Signed integer overflow is never silently treated as language-level UB.

AES-08
Division by zero has deterministic failure semantics.

AES-09
Array/slice bounds violations have deterministic failure semantics.

AES-10
Expression evaluation order is deterministic.

AES-11
Resource cleanup is deterministic according to ownership/drop rules.

AES-12
Drop is not a recoverable error propagation mechanism.

AES-13
Core does not require a defer keyword.

AES-14
Compiler internally models cleanup regions.

AES-15
Result propagation does not require hidden runtime exception machinery.

AES-16
Panic behavior may vary by explicit compilation profile.

AES-17
Optimization cannot change observable error semantics.
```

---

# 39. Một thay đổi kiến trúc khá quan trọng

Sau khi xem toàn bộ Memory + Concurrency + Execution, tôi nghĩ Axiom nên có một nguyên tắc:

## **"Explicit at semantic boundaries, implicit within the compiler."**

Ví dụ:

### Programmer phải nói rõ:

```text
own
view
mut_view
unsafe
dynamic dispatch
Result
async
spawn
atomic
repr(C)
```

### Compiler tự làm:

```text
lifetime
drop insertion
cleanup
escape analysis
stack promotion
register allocation
generic specialization
borrow/alias analysis
async state machine
bounds-check elimination
```

Đây có thể trở thành **triết lý thiết kế cốt lõi của Axiom**.

---

# 40. Axiom hiện tại đã có một đặc điểm rất đáng giá

Ta đang tránh được khá nhiều "tax" mà các ngôn ngữ hiện đại thường mang theo:

```text
Axiom
──────────────────────────────
GC                       ❌
mandatory RC             ❌
object header            ❌
class hierarchy          ❌
virtual dispatch         ❌
exception runtime        ❌
mandatory async runtime  ❌
mandatory heap           ❌
borrow syntax            ❌
lifetime syntax          ❌
implicit mutable sharing ❌
```

nhưng vẫn có:

```text
Axiom
──────────────────────────────
static typing            ✓
ownership                ✓
deterministic Drop       ✓
safe views               ✓
generics                 ✓
traits                   ✓
async                    ✓
threads                  ✓
atomics                  ✓
RAII-like cleanup        ✓
zero-cost abstraction   ✓
native compilation      ✓
```

Đây chính là vùng thiết kế mà tôi nghĩ đáng tiếp tục.

---

## Bước tiếp theo

Sau phần này, tôi sẽ **không đi ngay vào Standard Library**.

Phần tiếp theo hợp lý nhất là:

# `AXIOM LANGUAGE SYNTAX v0.1`

Tức là biến toàn bộ semantic model hiện tại thành **một ngôn ngữ mà con người thực sự viết được**.

Ta sẽ chốt:

```text
fn
let / var
struct
enum
trait
impl
generic
view<T>
mut_view<T>
match
if / loop / for / while
closure
async / await
spawn
unsafe
extern
@repr
module/import
visibility
operators
pattern matching
type aliases / distinct types
```

và quan trọng nhất: **tìm cách làm syntax ngắn, dễ đọc nhưng không biến thành Rust/C++ thứ hai**.

Sau đó mới có thể viết một **Axiom Language Reference v0.1** hoàn chỉnh và dùng nó làm "nguồn sự thật" cho AI agent bắt đầu xây compiler.