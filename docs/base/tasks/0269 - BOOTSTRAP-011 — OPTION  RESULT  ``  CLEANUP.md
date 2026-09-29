Tiếp theo là **BOOTSTRAP-011 — Option/Result + `?` + Cleanup Control Flow**.

Đây là bước nối trực tiếp `enum/match` vừa hoàn thành với mô hình **ownership + Drop + error handling**. Tôi khuyến nghị hoàn thiện nó trước khi đi sâu vào Generic/Trait.

# BOOTSTRAP-011 — OPTION / RESULT / `?` / CLEANUP

## 1. Quyết định kiến trúc

Axiom không có exception mặc định.

Ba cơ chế hoàn toàn khác nhau:

```text
Result<T,E>   → recoverable failure
panic()       → unrecoverable program failure
trap/abort    → machine/runtime fatal
```

`Option<T>` biểu diễn:

```text
có giá trị / không có giá trị
```

`Result<T,E>` biểu diễn:

```text
thành công / lỗi
```

Cả hai đều chỉ là **enum bình thường**.

Không có:

```text
exception object
hidden stack unwinding
hidden error runtime
mandatory heap allocation
```

---

# 2. Option

Định nghĩa:

```axiom
enum Option<T> {
    Some(T),
    None,
}
```

Ví dụ:

```axiom
fn find_value(x: i32) -> Option<i32> {
    if x > 0 {
        return Some(x);
    }

    return None;
}
```

Không cần compiler primitive `Option`.

Compiler chỉ cần hỗ trợ:

```text
enum
generic
match
ownership
```

---

# 3. Result

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Ví dụ:

```axiom
fn divide(a: i32, b: i32) -> Result<i32, DivError> {
    if b == 0 {
        return Err(DivError::Zero);
    }

    return Ok(a / b);
}
```

Đây chỉ là return value bình thường.

Không có exception path ẩn.

---

# 4. `?` là control-flow sugar

Ví dụ:

```axiom
fn calculate() -> Result<i32, Error> {
    let a = load_a()?;
    let b = load_b()?;

    return Ok(a + b);
}
```

Không được hiểu là:

```text
throw
catch
exception propagation
```

Mà tương đương về semantic:

```axiom
let a_result = load_a();

let a = match a_result {
    Ok(v) => v,
    Err(e) => return Err(e),
};

let b_result = load_b();

let b = match b_result {
    Ok(v) => v,
    Err(e) => return Err(e),
};

return Ok(a + b);
```

---

# 5. Nhưng `?` phải chạy Drop

Đây là điểm quan trọng nhất.

Ví dụ:

```axiom
fn f() -> Result<i32, Error> {
    let file = open_file()?;
    let buffer = allocate_buffer()?;

    let x = read(file, buffer)?;

    return Ok(x);
}
```

Nếu:

```text
read(...)
→ Err
```

thì compiler phải:

```text
read
 ↓
Err
 ↓
DROP buffer
 ↓
DROP file
 ↓
return Err
```

Không được biến `?` thành một jump trực tiếp bỏ qua cleanup.

---

# 6. Cleanup Graph

Đây là lúc `CleanupGraph` trong Axiom trở thành thành phần thực tế.

Ví dụ:

```text
bb0
 │
 ▼
open file
 │
 ▼
bb1
 │
 ▼
allocate buffer
 │
 ▼
bb2
 │
 ├── success → bb3
 │
 └── error   → cleanup2
                 │
                 ▼
              cleanup1
                 │
                 ▼
             return Err
```

Compiler có thể tạo:

```text
CleanupRegion {
    resources
    parent
    exit_targets
}
```

---

# 7. Cleanup không phải exception

Cleanup Graph chỉ là compiler-generated CFG.

Nó không cần runtime exception machinery.

Ví dụ:

```text
return
break
continue
?
panic
unwind
```

đều có thể đi qua cleanup edges.

---

# 8. Normal return

```axiom
fn f() -> i32 {
    let a = acquire_a();
    let b = acquire_b();

    return 42;
}
```

Semantic CFG:

```text
return
 ↓
drop b
 ↓
drop a
 ↓
return 42
```

---

# 9. `?` return

```axiom
let x = foo()?;
```

Conceptual lowering:

```text
result = foo();

switch result {
    Ok(v):
        x = v;

    Err(e):
        cleanup;
        return Err(e);
}
```

Không tạo exception.

---

# 10. Nested scopes

Ví dụ:

```axiom
fn f() -> Result<i32, Error> {
    let a = acquire_a();

    {
        let b = acquire_b();
        use(b)?;
    }

    use(a)?;

    return Ok(42);
}
```

Nếu `use(b)` lỗi:

```text
drop b
drop a
return Err
```

Nếu inner block thành công:

```text
drop b
```

sau đó `a` vẫn còn sống.

---

# 11. Cleanup phải field-sensitive

Ví dụ:

```axiom
struct S {
    a: File,
    b: Buffer,
}
```

Nếu:

```axiom
let x = move s.a;
```

thì:

```text
s.a = Moved
s.b = Owned
```

cleanup:

```text
drop s.b
```

không được:

```text
drop s.a
```

---

# 12. Partial move + `?`

Ví dụ:

```axiom
let s = make_s();

let a = move s.a;

let x = foo()?;
```

Nếu `foo()` trả `Err`, cleanup chỉ được drop:

```text
s.b
```

và các resource khác còn owned.

Ownership verifier phải cung cấp trạng thái chính xác cho CleanupGraph.

---

# 13. `Option` với `?`

Axiom có thể cho phép `?` trên cả:

```text
Option<T>
```

Ví dụ:

```axiom
fn find() -> Option<i32> {
    let x = get_value()?;
    return Some(x + 1);
}
```

Lower:

```text
match get_value() {
    Some(x) => continue,
    None => return None,
}
```

Không phải mọi `?` đều là Result.

Compiler cần một abstraction kiểu:

```text
TryProtocol
```

nhưng tôi **không khuyến nghị expose trait này trong Core v0.1**.

Semantic compiler có thể nhận biết:

```text
Option
Result
```

trước.

Sau này mới xem xét generalized `Try`.

---

# 14. Không implicit convert Option ↔ Result

Không cho:

```text
Option<T>
```

tự động biến thành:

```text
Result<T,E>
```

hoặc ngược lại.

Ví dụ:

```axiom
let x: Result<i32, Error> = some_option?;
```

chỉ hợp lệ nếu có conversion rõ ràng.

Điều này giữ error semantics rõ ràng.

---

# 15. Error propagation type checking

Nếu:

```axiom
fn f() -> Result<i32, Error>
```

thì:

```axiom
let x = g()?;
```

với:

```text
g() -> Result<T, E>
```

compiler phải chứng minh `E` có thể trở thành error type của `f`.

MVP:

```text
E == Error
```

Sau này có thể hỗ trợ conversion trait.

Không nên để implicit arbitrary conversion trong Stage-0.

---

# 16. `?` không được dùng tùy tiện

Ví dụ:

```axiom
fn f() -> i32 {
    let x = g()?;
}
```

nếu `g()` trả:

```text
Result<i32, Error>
```

→ compile error.

Function phải có return context tương thích với propagation.

Diagnostic:

```text
AX1711 `?` cannot propagate this failure from function returning `i32`
```

---

# 17. `panic()`

Định nghĩa semantic:

```text
panic(message) -> never
```

`never` có thể coerce thành bất kỳ type cần thiết nào.

Ví dụ:

```axiom
let x: i32 = panic("failed");
```

hợp lệ về type.

CFG:

```text
bb0:
    ...
    call panic
    unreachable
```

---

# 18. Panic cũng phải cleanup

Ví dụ:

```axiom
fn f() -> i32 {
    let file = open();

    if bad_condition() {
        panic("bad");
    }

    return 42;
}
```

Panic path:

```text
panic
 ↓
cleanup file
 ↓
abort/unwind
```

Tùy panic profile.

---

# 19. Panic profile

Axiom giữ hai profile:

```text
panic = abort
panic = unwind
```

### Minimal

```text
panic=abort
```

Không cần unwind runtime.

### Unwind

Compiler sinh:

```text
unwind metadata
cleanup landing paths
runtime support
```

chỉ khi profile yêu cầu.

---

# 20. `panic` khác `Result`

Ví dụ:

```axiom
return Err(error);
```

là normal control flow.

Không cần unwind.

Trong khi:

```axiom
panic("fatal");
```

là abnormal termination/unwind.

Đây là distinction rất quan trọng cho optimizer.

---

# 21. Drop không được trả Result

Không cho:

```axiom
impl Drop for File {
    fn drop(...) -> Result<(), Error> // invalid
}
```

Lý do:

```text
cleanup
```

không nên trở thành một control-flow error propagation system.

Nếu đóng resource có thể thất bại:

```axiom
file.close() -> Result<(), Error>
```

phải gọi explicit.

Sau đó Drop chỉ là fallback cleanup.

---

# 22. `close()` và Drop

Ví dụ:

```axiom
let file = open()?;

file.write(data)?;
file.close()?;
```

Nếu `close()` thành công:

```text
resource already logically closed
```

Drop sau đó không được đóng lần hai.

Có thể dùng internal resource state:

```text
Open
Closed
Moved
Dropped
```

hoặc type-state library abstraction sau này.

---

# 23. Không double cleanup

Compiler phải đảm bảo:

```text
DROP
```

chỉ xuất hiện khi resource còn owned/initialized.

Ví dụ:

```text
move x
drop x
```

→ verifier reject.

MIR verifier phải bắt được ngay cả khi frontend có bug.

---

# 24. Cleanup và loops

Ví dụ:

```axiom
loop {
    let resource = acquire();

    if done() {
        break;
    }

    use(resource);
}
```

`break` phải cleanup:

```text
break
 ↓
drop resource
 ↓
loop exit
```

Không được coi `break` như jump trực tiếp.

---

# 25. `continue`

```axiom
while cond {
    let resource = acquire();

    if skip {
        continue;
    }

    use(resource);
}
```

`continue`:

```text
continue
 ↓
drop resource
 ↓
loop condition
```

---

# 26. Cleanup regions

Tôi đề xuất internal model:

```text
CleanupRegion {
    id
    parent: Option<CleanupRegionId>
    resources: ResourceSet
    exit_edges: Vec<CleanupExit>
}
```

Exit:

```text
CleanupExit {
    source_block
    target
    reason
}
```

Reason:

```text
Return
Break
Continue
QuestionMark
Panic
Unwind
```

---

# 27. Cleanup lowering

Không nên emit một chuỗi Drop ngay tại frontend.

Pipeline:

```text
Typed HIR
   ↓
Ownership verification
   ↓
Control-flow analysis
   ↓
CleanupGraph
   ↓
MIR
   ↓
Cleanup optimization
```

Sau đó optimizer có thể merge:

```text
drop a
drop b
return
```

vào shared cleanup block.

---

# 28. Cleanup optimization

Ví dụ:

```text
bb1:
    ...
    return x

bb2:
    ...
    return y
```

cả hai đều cần:

```text
drop resource
```

Có thể:

```text
bb1 ─┐
     ├→ cleanup → return
bb2 ─┘
```

hoặc duplicate cleanup nếu branch prediction/code-size trade-off có lợi.

Semantics không đổi.

---

# 29. Drop flags

Không nên mặc định tạo:

```text
bool dropped_a
bool dropped_b
bool dropped_c
...
```

cho mọi struct.

Compiler nên dùng **dataflow/state knowledge** trước.

Chỉ materialize runtime drop state khi control flow thực sự yêu cầu.

Ví dụ state machine/coroutine có thể cần encoded state.

Điều này phù hợp mục tiêu:

> Không biến ownership safety thành runtime overhead bắt buộc.

---

# 30. MIR example

Source:

```axiom
fn f() -> Result<i32, Error> {
    let a = acquire()?;
    let x = compute(a)?;

    return Ok(x);
}
```

MIR conceptually:

```text
bb0:
    %a_result = call acquire()

    switch_variant %a_result {
        Ok(%a)  -> bb1
        Err(%e) -> bb_err0
    }

bb1:
    %x_result = call compute(%a)

    switch_variant %x_result {
        Ok(%x)  -> bb2
        Err(%e) -> bb_err1
    }

bb2:
    drop %a
    %r = enum_construct Result::Ok(%x)
    return %r

bb_err1:
    drop %a
    %r = enum_construct Result::Err(%e)
    return %r

bb_err0:
    %r = enum_construct Result::Err(%e)
    return %r
```

Optimizer có thể sau đó:

```text
merge cleanup
remove unnecessary moves
eliminate temporaries
```

---

# 31. `?` không cần runtime helper

Đây là một mục tiêu quan trọng.

Không muốn compiler tạo:

```text
axiom_try_propagate(...)
```

cho mỗi `?`.

Thay vào đó:

```text
? → CFG
```

hoàn toàn compile-time.

Nếu tối ưu tốt, native code có thể gần tương đương code C viết bằng `if`.

---

# 32. Zero-cost error path

Ví dụ:

```axiom
fn parse(x: i32) -> Result<i32, Error> {
    if x < 0 {
        return Err(Error::Negative);
    }

    return Ok(x * 2);
}
```

Có thể compile thành:

```text
test x,x
js error
lea ...
ret
error:
...
ret
```

Không cần exception table.

Không cần heap.

Không cần runtime error object nếu `Error` là value type.

---

# 33. Error type cũng là ordinary type

Ví dụ:

```axiom
enum Error {
    Io,
    InvalidInput,
    NotFound,
}
```

hoặc:

```axiom
struct Error {
    code: u32,
}
```

Compiler không đặc biệt hóa object này.

Điều này giúp:

```text
Result<T,E>
```

có thể tối ưu như bất kỳ enum nào khác.

---

# 34. `Result<T,E>` có thể được tối ưu mạnh

Compiler có thể:

- niche optimization
- register return
- scalarize
- eliminate Result construction
- branch folding
- tail propagation
- inline callee
- specialize generic Result

Ví dụ:

```text
foo() -> Result<i32, Error>
bar() -> Result<i32, Error>
```

có thể được inline thành một CFG duy nhất.

Không có abstraction penalty bắt buộc.

---

# 35. `Option` cũng vậy

Ví dụ:

```axiom
fn get() -> Option<i32>
```

có thể trả:

```text
register
```

thay vì tạo object.

Với:

```text
Option<Pointer>
```

layout engine có thể tận dụng niche nếu ABI/validity rules cho phép.

---

# 36. Compiler architecture

BOOT-011 thêm một component:

```text
compiler/
├── control_flow/
│   ├── cleanup.rs
│   ├── cfg.rs
│   └── dominance.rs
│
├── patterns/
│   └── ...
│
└── semantics/
    ├── ownership/
    └── try/
```

Nhưng không tạo:

```text
exception_runtime/
```

trong core compiler.

Runtime unwind chỉ xuất hiện nếu profile yêu cầu.

---

# 37. Test ladder

### Option

```text
Some(42)
None
match
nested Option
ownership
Drop
```

### Result

```text
Ok(42)
Err(error)
match
nested Result
```

### `?`

```text
single ?
multiple ?
nested function
error propagation
Option ?
Result ?
```

### Cleanup

```text
return
?
break
continue
panic
nested scope
partial move
```

### Drop

```text
normal return
error return
panic
early return
loop exit
```

### Optimization

```text
-O0
-O1
-O2
-O3
```

phải cho cùng semantic result.

---

# 38. Compile-fail tests

Bắt buộc có:

```text
AX1711  ? in incompatible return context
AX1712  ? error type mismatch
AX1713  ? cannot propagate this failure
AX1714  invalid Drop state
AX1715  double drop
AX1716  drop of moved value
AX1717  cleanup would access moved field
AX1718  cleanup would access uninitialized field
AX1719  invalid control-flow cleanup
```

---

# 39. Invariants

```text
ATRY-20  Option Is An Ordinary Enum
ATRY-21  Result Is An Ordinary Enum
ATRY-22  Recoverable Failure Uses Result
ATRY-23  Absence Uses Option
ATRY-24  ? Is Control-Flow Sugar
ATRY-25  ? Does Not Require Exceptions
ATRY-26  ? Preserves Ownership
ATRY-27  ? Executes Required Cleanup
ATRY-28  ? Requires Compatible Return Context
ATRY-29  Option Propagation Is Explicitly Typed
ATRY-30  Result Propagation Is Explicitly Typed
ATRY-31  Error Conversion Is Not Implicitly Arbitrary
ATRY-32  Result Error Paths Are Ordinary CFG
ATRY-33  Result Does Not Require Heap Allocation
ATRY-34  Result Does Not Require Runtime Metadata

ACLEAN-20  Every Scope Exit Has Correct Cleanup
ACLEAN-21  Return Executes Required Drops
ACLEAN-22  Break Executes Required Drops
ACLEAN-23  Continue Executes Required Drops
ACLEAN-24  ? Executes Required Drops
ACLEAN-25  Panic Executes Required Drops
ACLEAN-26  Moved Values Are Never Dropped
ACLEAN-27  Uninitialized Values Are Never Dropped
ACLEAN-28  Partially Moved Aggregates Are Field Sensitive
ACLEAN-29  Cleanup Order Is Deterministic
ACLEAN-30  Cleanup Does Not Propagate Recoverable Errors
ACLEAN-31  Drop Is Non-Fallible
ACLEAN-32  Cleanup Does Not Imply Heap Allocation
ACLEAN-33  CleanupGraph Is Compiler Generated
ACLEAN-34  Cleanup Is Represented In CFG
ACLEAN-35  Cleanup May Be Optimized
ACLEAN-36  Cleanup Optimization Preserves Observable Semantics
ACLEAN-37  Runtime Drop Flags Are Not Mandatory
ACLEAN-38  Panic Abort Requires No Unwind Runtime
ACLEAN-39  Unwind Runtime Is Optional
ACLEAN-40  Exception Objects Are Not Required
```

---

# 40. BOOT-011 gate

```text
enum
  ↓
Option
  ↓
Result
  ↓
?
  ↓
CleanupGraph
  ↓
MIR
  ↓
MIR interpreter
  ↓
x86-64
  ↓
native
```

Phải chứng minh được:

```text
normal return        ✓
Result::Err          ✓
Option::None         ✓
multiple ?           ✓
nested cleanup       ✓
partial move         ✓
Drop                 ✓
panic=abort          ✓
-O0/O1/O2/O3         ✓
interpreter=native   ✓
```

---

## Điểm quan trọng nhất của BOOT-011

Sau bước này, Axiom có một mô hình control-flow rất sạch:

```text
                 ┌──────────────┐
                 │ Normal CFG   │
                 └──────┬───────┘
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
       return          ?            panic
          │             │              │
          └─────────────┼──────────────┘
                        ▼
                  CleanupGraph
                        │
                        ▼
                       MIR
```

Trong đó **`Result` không phải exception**, **`?` không phải exception**, và **Drop không phải runtime garbage collector**.

Điều này giữ đúng mục tiêu ban đầu của Axiom: programmer viết code cấp cao rất gọn, nhưng compiler vẫn có đủ thông tin để tạo machine code trực tiếp và không phải trả “runtime tax” chỉ vì sử dụng abstraction.