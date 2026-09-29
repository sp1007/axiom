Tiếp tục. Tôi sẽ chốt **Control Flow + Result/Option + cleanup** vì đây là phần nối trực tiếp giữa ngôn ngữ ở mức source và MIR/verifier.

# Axiom Control Flow v0.1

Mục tiêu:

- dễ viết như ngôn ngữ hiện đại;
- không có exception machinery mặc định;
- `Drop` luôn chính xác;
- `Result` không tạo runtime overhead không cần thiết;
- compiler có thể biến control flow thành machine code rất thấp;
- `async/await` sau này có thể dùng cùng semantic model.

---

## 1. Axiom có 3 loại control exit

Tôi đề xuất phân biệt rõ:

```text
NORMAL
RETURN
ABNORMAL
```

Cụ thể:

```text
fallthrough
return
break
continue
panic
trap
```

và `?` chỉ là **syntactic control-flow sugar**.

Không nên có một cơ chế “exception” chung rồi bắt compiler đoán.

---

# 2. `return`

Ví dụ:

```axiom
fn foo() -> i64 {
    let x = make_resource();
    return 42;
}
```

Semantic:

```text
make_resource()
      │
      ▼
     x
      │
      ▼
 return 42
      │
      ▼
 drop x
      │
      ▼
 return
```

Source không cần:

```text
defer
finally
```

cho cleanup thông thường.

Compiler tự tạo cleanup.

---

# 3. Cleanup phải là một phần của MIR

Ví dụ source:

```axiom
fn foo() -> i64 {
    let a = A.new();
    let b = B.new();

    if condition {
        return 1;
    }

    return 2;
}
```

MIR conceptual:

```text
bb0:
    a = alloc A
    b = alloc B
    branch condition, bb1, bb2

bb1:
    drop b
    drop a
    return 1

bb2:
    drop b
    drop a
    return 2
```

Nhưng compiler không nhất thiết phải materialize duplicate cleanup blocks cuối cùng; optimizer có thể hợp nhất:

```text
bb1 ──┐
      ├──> cleanup ──> return
bb2 ──┘
```

Đây là **Drop elaboration**.

---

# 4. `break` và `continue`

Ví dụ:

```axiom
while condition {
    let x = Resource.new();

    if should_stop() {
        break;
    }

    if skip() {
        continue;
    }

    use(x);
}
```

`break` phải:

```text
drop x
   ↓
loop exit
```

`continue` phải:

```text
drop x
   ↓
loop condition
```

Không được đơn giản biến:

```text
continue
```

thành jump trước cleanup.

---

# 5. `?` không phải exception

Ví dụ:

```axiom
fn load() -> Result<Data, Error> {
    let file = open()?;
    let data = read(file)?;
    Ok(data)
}
```

Semantic của:

```text
open()?
```

là:

```text
match open() {
    Ok(v) => continue,
    Err(e) => return Err(e),
}
```

Nhưng có một điểm rất quan trọng:

### trước `return Err(...)`, phải cleanup các resource đang sở hữu.

Ví dụ:

```axiom
fn foo() -> Result<i64, Error> {
    let file = open()?;
    let x = read(file)?;

    Ok(x)
}
```

Nếu `read(file)` trả `Err`:

```text
read
 ↓
Err
 ↓
drop file
 ↓
return Err
```

Không cần programmer viết:

```axiom
close(file);
```

nếu `File` có `Drop`.

---

# 6. `Result` nên là enum bình thường

Conceptually:

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

Không cần runtime exception object.

Compiler có thể optimize:

```text
Result<i64, Error>
```

thành representation rất nhỏ.

Ví dụ:

```text
register:
    success/value
```

hoặc:

```text
RAX = value
RDX = discriminant
```

tùy ABI.

Nếu `Error` có niche hoặc representation phù hợp, compiler có thể tối ưu tiếp.

---

# 7. `Option` cũng vậy

```axiom
enum Option<T> {
    Some(T),
    None
}
```

Không có null mặc định.

Nhưng compiler có thể áp dụng **niche optimization**.

Ví dụ conceptually:

```axiom
Option<Box<T>>
```

có thể dùng:

```text
null = None
non-null = Some
```

mà programmer vẫn không nhận được raw null semantics.

Đây là ví dụ rất đẹp của:

```text
high-level semantics
        ↓
low-level representation
```

---

# 8. Không có implicit null

Tôi vẫn giữ quyết định trước:

```text
T
```

không có null.

Muốn “có hoặc không”:

```text
Option<T>
```

Muốn pointer nullable ở system boundary:

```text
unsafe *mut T
```

hoặc FFI.

Điều này loại bỏ cả một lớp bug:

```text
null dereference
```

khỏi safe Axiom.

---

# 9. `panic`

`panic` không phải `Result`.

Ví dụ:

```axiom
fn divide(a: i64, b: i64) -> i64 {
    if b == 0 {
        panic("division by zero");
    }

    a / b
}
```

Semantic:

```text
panic
  ↓
cleanup
  ↓
panic handling policy
```

Không:

```text
panic
 ↓
return Result
```

---

# 10. Hai panic profile

### Abort

```text
--panic=abort
```

Flow:

```text
panic
 ↓
cleanup
 ↓
abort/trap/exit
```

Runtime rất nhỏ.

### Unwind

```text
--panic=unwind
```

Flow:

```text
panic
 ↓
unwind frames
 ↓
run cleanup
 ↓
handler / terminate
```

Cần metadata/runtime hỗ trợ.

Nhưng **unwind không biến Axiom thành C++ exception system**.

Không có:

```text
throw T
catch T
```

trong core v0.1.

---

# 11. `panic` và Drop có một vấn đề quan trọng

Nếu:

```text
Drop::drop()
```

lại panic thì sao?

Ví dụ:

```text
panic A
 ↓
drop B
 ↓
drop B panic
```

Nếu cho phép panic lồng nhau tùy ý, semantics trở nên rất phức tạp.

Tôi đề xuất:

> **Drop không được phát sinh recoverable error.**

Và tốt hơn nữa:

> **Drop failure/panic không được phép trong safe Drop.**

Resource API nên tách:

```text
close() -> Result<(), Error>
```

với:

```text
Drop
```

Ví dụ:

```axiom
file.close()?;
```

Nếu programmer không gọi:

```text
Drop(file)
```

vẫn cleanup resource.

Nhưng `Drop` không được biến thành:

```text
throw
```

---

# 12. Đây là một nguyên tắc cực quan trọng

```text
Drop = guaranteed cleanup
Close = fallible operation
```

Ví dụ:

```text
File
 ├── close() -> Result
 └── Drop    -> best-effort/final cleanup
```

Điều này giúp control flow cực kỳ dễ reasoning.

---

# 13. `defer` có cần không?

Tôi nghiêng về:

### Không đưa `defer` vào Core v0.1.

Vì resource cleanup đã được compiler quản lý.

Ví dụ thay vì:

```text
defer close(file)
```

ta có:

```axiom
let file = File.open(path)?;
```

và compiler biết:

```text
scope exit
    ↓
Drop(file)
```

`defer` chỉ thực sự cần cho:

- logging
- transaction rollback
- temporary state restoration
- arbitrary procedural cleanup.

Những thứ này có thể đưa vào library sau.

Nếu sau này thêm, nó nên được định nghĩa bằng semantic cleanup action chứ không tạo một hệ thống lifetime thứ hai.

---

# 14. Cleanup stack

Compiler có thể duy trì nội bộ:

```text
CleanupScope
```

Ví dụ:

```text
scope S1
 ├── owns A
 ├── owns B
 └── owns C
```

Khi exit:

```text
C
↓
B
↓
A
```

Nếu nested scope:

```text
S1
 ├── A
 │
 └── S2
      ├── B
      └── C
```

exit S2:

```text
C
B
```

sau đó exit S1:

```text
A
```

---

# 15. Nhưng đừng biến cleanup thành runtime stack

Đây chỉ là **compiler representation**.

Compiler có thể cuối cùng tạo:

```text
CALL close_file
```

hoặc:

```text
no code
```

hoặc:

```text
inline release
```

hoặc:

```text
merge cleanup blocks
```

Do đó:

```text
CleanupScope
```

không phải runtime abstraction bắt buộc.

---

# 16. Control-flow model trong MIR

Tôi đề xuất mở rộng terminator hiện tại:

```text
Return
Jump
Branch
Switch
Call
Trap
```

thành:

```text
Return
Jump
Branch
Switch
Call
Invoke
Trap
Panic
```

Nhưng `Invoke` chỉ cần nếu unwind profile tồn tại.

### Abort profile

```text
Call
```

đủ.

### Unwind profile

```text
Invoke {
    callee
    args
    normal_target
    unwind_target
}
```

Ví dụ:

```text
call foo()
 ├── success → bb_normal
 └── panic   → bb_cleanup
```

Điều này tránh nhét exception semantics vào MIR cơ bản nếu không sử dụng unwind.

---

# 17. `?` lowering

Source:

```axiom
let x = foo()?;
bar(x)
```

HIR:

```text
Call foo
Check Result
Branch
```

MIR:

```text
%r = call @foo()

switch tag(%r) {
    Ok  → bb_ok
    Err → bb_err
}

bb_ok:
    %x = payload(%r)
    call @bar(%x)
    ...

bb_err:
    %e = payload(%r)
    cleanup
    return Err(%e)
```

Sau optimization, nếu compiler biết ABI:

```text
call foo
test status
jne error
```

Rất gần C-level code.

---

# 18. `Result` có thể trở thành zero-cost

Ví dụ:

```axiom
fn parse(x: i64) -> Result<i64, Error>
```

Nếu ABI chọn:

```text
RAX = value
RDX = success
```

thì:

```axiom
let x = parse(v)?;
return x + 1;
```

có thể thành:

```text
call parse
test rdx, rdx
jne error
add rax, 1
ret
```

Không cần exception object.

Không cần heap.

Không cần runtime.

---

# 19. `break`/`continue` + Drop cần được verifier chứng minh

Ta thêm các invariant:

### ACF-01
Mọi `return` đều chạy cleanup cần thiết.

### ACF-02
Mọi `break` đều cleanup resource thuộc loop scope.

### ACF-03
Mọi `continue` đều cleanup resource thuộc iteration scope.

### ACF-04
`?` không bypass ownership cleanup.

### ACF-05
`panic` không bypass mandatory cleanup.

### ACF-06
Partial move không được drop field đã moved.

### ACF-07
Resource chỉ được drop tối đa một lần.

### ACF-08
Drop order deterministic.

### ACF-09
`Result` không yêu cầu exception runtime.

### ACF-10
`Option` không yêu cầu null semantics.

---

# 20. Điểm rất quan trọng: `Drop` không phải lúc nào cũng “reverse declaration order”

Ta nên nói chính xác hơn:

> Mặc định, **owned locals còn sống tại thời điểm scope exit** được drop theo reverse initialization/declaration dependency order.

Vì partial move có thể thay đổi tập resource còn sống.

Ví dụ:

```axiom
struct User {
    file: File
    name: Text
}

let user = ...
let file = move user.file;
```

Sau đó:

```text
user.file = MOVED
user.name = OWNED
```

Khi scope exit:

```text
drop user.name
```

không được:

```text
drop user.file
```

vì field đó không còn thuộc `user`.

---

# 21. Điều này dẫn đến một khái niệm rất đẹp: Drop Tree

Verifier có thể duy trì:

```text
Owner
│
├── field A → OWNED
│
├── field B → MOVED
│
└── field C
      └── resource → OWNED
```

Cleanup traversal:

```text
A
C.resource
```

B bị bỏ qua.

Đây là cách xử lý ownership rất sạch mà không cần reference counting.

---

# 22. `Result` + ownership

Một tình huống đáng chú ý:

```axiom
fn foo() -> Result<Resource, Error> {
    let r = create()?;
    Ok(r)
}
```

`r` không được Drop trước khi return.

Nó được:

```text
MOVE
 ↓
Result::Ok
 ↓
caller owns Resource
```

Do đó:

```text
return value
```

không đơn giản là “copy value ra ngoài”.

Đây là **ownership transfer across function boundary**.

ABI lowering sau đó quyết định:

```text
register
sret
caller allocation
move-elision
```

---

# 23. `Option` cũng có ownership semantics

```axiom
let x: Option<File> = Some(file);
```

thì:

```text
file
 ↓ MOVE
Option<File>
```

Nếu:

```axiom
match x {
    Some(f) => use(f),
    None => ...
}
```

thì branch `Some` nhận ownership `f`.

Nếu `f` không được move tiếp, compiler drop nó cuối branch.

Đây là lý do `match` phải được thiết kế cùng ownership verifier, không thể chỉ là syntax sugar đơn giản.

---

# 24. `match` nên là control-flow primitive

Tôi đề nghị:

```axiom
match value {
    Pattern1 => expr1,
    Pattern2 => expr2,
}
```

là Core.

Compiler lowering:

```text
match
 ↓
decision tree
 ↓
Switch / Branch
 ↓
MIR
```

Compiler có thể chọn:

```text
jump table
binary decision tree
if chain
computed branch
```

tùy profile.

---

# 25. Exhaustiveness

Ví dụ:

```axiom
match result {
    Ok(x) => x,
    Err(e) => handle(e),
}
```

OK.

Nhưng:

```axiom
match option {
    Some(x) => x,
}
```

→ compile error vì thiếu `None`.

Đây không chỉ là tiện ích syntax.

Nó cho phép compiler biết:

```text
all control paths covered
```

và hỗ trợ optimizer loại bỏ branch không thể xảy ra.

---

# 26. `unreachable`

Nên có semantic intrinsic:

```axiom
unreachable()
```

Compiler hiểu:

```text
control never continues
```

Nhưng **không có semantic `UNDEF`**.

Nếu chương trình thực sự đi tới:

```text
unreachable()
```

thì:

```text
TRAP
```

Điều này phù hợp với quyết định trước đây rằng Axiom không có `UNDEF` semantic.

---

# 27. Control-flow tổng thể

Axiom source:

```text
        expression
             │
       ┌─────┴─────┐
       │           │
     value       control
                   │
      ┌────────────┼────────────┐
      │            │            │
    return       branch       loop
      │            │            │
      └────────────┴────────────┘
                   │
                cleanup
                   │
              function exit
```

`panic` cũng đi vào cleanup:

```text
panic
  ↓
cleanup
  ↓
abort / unwind
```

---

# 28. Sau phần này, Axiom đã có một semantic control-flow khá hoàn chỉnh

Có thể tóm tắt:

```text
NORMAL
 ├── expression
 ├── if
 ├── match
 ├── while
 ├── loop
 └── for

STRUCTURED EXIT
 ├── return
 ├── break
 └── continue

ERROR CONTROL
 ├── Result
 ├── ?
 └── panic

TERMINAL
 ├── trap
 └── unreachable
```

Không cần:

```text
throw
catch
finally
goto
exception object
```

trong Core v0.1.

---

## Bước kế tiếp

Bây giờ có một phần còn **quan trọng hơn cả syntax**: **Axiom Type System v0.1 hoàn chỉnh**.

Ta đã có primitive/struct/enum/generic/trait/Option/Result, nhưng chưa chốt triệt để:

```text
numeric conversions
type inference
coercion
literal types
tuple
array
function types
never type
unit type
sized/unsized
variance
generic constraints
associated types
type aliases
newtype
```

Đặc biệt tôi muốn xem xét **`unit` và `never` type** trước. Hai type này làm control-flow, `panic`, `return`, `Result`, generic và MIR trở nên nhất quán hơn rất nhiều, mà gần như không làm ngôn ngữ phức tạp thêm.