Tiếp tục từ đó. Phần này nên được **freeze rất kỹ**, vì Drop Elaboration là cầu nối giữa ownership semantics và native code.

# AXIOM DROP ELABORATION v0.1

## 1. Nguyên tắc nền tảng

Axiom có:

```text
Ownership semantics
        ↓
Verifier
        ↓
Drop Elaboration
        ↓
Explicit cleanup CFG
        ↓
Verified MIR
```

Điểm quan trọng:

> **Drop không phải là một lời gọi hàm mà programmer tự viết; Drop là semantic obligation được compiler hiện thực hóa.**

Ví dụ:

```axiom
fn work() {
    let a = File.open(...)
    let b = Buffer(...)
    use(a, b)
}
```

Programmer không cần:

```text
b.close()
a.close()
```

Compiler phải đảm bảo resource được release đúng thứ tự.

---

# 2. Drop order

Quy tắc v0.1:

> Các local owning resources được Drop theo **reverse declaration order**, trừ khi ownership đã được move/consumed hoặc resource đã được explicitly released theo semantics của type.

Ví dụ:

```axiom
fn test() {
    let a = A()
    let b = B()
    let c = C()
}
```

Semantic order:

```text
construct A
construct B
construct C

drop C
drop B
drop A
```

Không phụ thuộc physical layout của struct.

---

# 3. Logical declaration order ≠ memory layout

Ví dụ:

```axiom
struct S {
    a: A
    b: B
    c: C
}
```

Compiler có thể layout:

```text
c | a | b
```

nếu ABI native cho phép.

Nhưng Drop semantics vẫn:

```text
c
b
a
```

theo **logical field declaration order reversed**.

Do đó:

```text
logical order
```

và:

```text
physical layout
```

hoàn toàn độc lập.

---

# 4. Drop plan

Compiler tạo một internal structure:

```text
DropPlan {
    locals
    fields
    conditions
    order
}
```

Ví dụ:

```text
a: Drop
b: Drop
c: Drop
```

thành:

```text
DropPlan:
    c
    b
    a
```

---

# 5. Basic return

Source:

```axiom
fn f() -> i32 {
    let a = Resource()
    let b = Resource()

    return 42
}
```

Raw MIR có thể:

```text
B0:
    a = Resource()
    b = Resource()
    v = 42
    RETURN v
```

Drop elaboration biến thành:

```text
B0:
    a = Resource()
    b = Resource()
    v = 42
    JUMP cleanup.return

cleanup.return:
    DROP b
    DROP a
    RETURN v
```

---

# 6. Nhưng return value có thể là owning value

Ví dụ:

```axiom
fn make() -> Buffer {
    let a = Buffer(...)
    return a
}
```

Không được:

```text
DROP a
RETURN a
```

Ownership của `a` chuyển sang caller.

MIR:

```text
a = Buffer(...)
MOVE a -> return_value
RETURN return_value
```

Drop plan:

```text
a = MOVED
```

=> không Drop `a`.

---

# 7. Move một phần

```axiom
fn f() -> String {
    let p = Person(...)
    return p.name
}
```

Sau:

```text
MOVE p.name
```

state:

```text
p.name = MOVED
p.age  = OWNED
p      = PARTIAL
```

Cleanup:

```text
DROP p.age
```

Không:

```text
DROP p.name
```

vì `name` đã chuyển ownership.

Đây là lý do Drop Elaboration **bắt buộc phải hiểu partial ownership**.

---

# 8. Drop flags

Không phải lúc nào compiler biết statically một field có còn owned hay không.

Ví dụ:

```axiom
fn f(cond: bool) {
    let x = Resource()

    if cond {
        consume(x)
    }
}
```

CFG:

```text
        B0
        │
     branch
      /   \
    B1     B2
 consume   no-op
      \   /
       B3
```

Tại B3:

```text
x = MAYBE_MOVED
```

Cleanup không thể đơn giản:

```text
DROP x
```

vì có path đã move.

---

# 9. Conditional Drop

Compiler tạo:

```text
if x_is_owned {
    DROP x
}
```

MIR:

```text
DROP_IF_OWNED x
```

hoặc compiler có thể lower thành:

```text
BRANCH drop_flag_x
    → drop_x
    → skip_x
```

`DROP_IF_OWNED` nên được xem là **elaboration-level operation**, sau đó canonicalize trước optimizer.

---

# 10. Có cần runtime drop flag không?

**Không phải lúc nào.**

Compiler có ba khả năng:

### Case A — statically known

```text
x = OWNED
```

=> trực tiếp:

```text
DROP x
```

### Case B — statically moved

```text
x = MOVED
```

=> không emit Drop.

### Case C — path-dependent

```text
x = MAYBE_MOVED
```

=> cần conditional cleanup.

Nhưng optimizer có thể loại bỏ flag nếu chứng minh được:

```text
if cond {
    consume(x)
}
```

và các path đã được phân tích chính xác.

---

# 11. Không nên biến mọi Drop thành runtime branch

Đây là một điểm tôi muốn freeze:

> **Drop flags là semantic fallback, không phải object metadata mặc định.**

Không có:

```text
object header:
    refcount
    dropflag
    typeinfo
```

Axiom không được đi theo hướng đó.

Drop state có thể hoàn toàn nằm ở compiler/control-flow.

---

# 12. Branch cleanup

Source:

```axiom
fn f(cond: bool) {
    let a = A()
    let b = B()

    if cond {
        return
    }

    use(a, b)
}
```

Nhánh return:

```text
B → DROP b → DROP a → RETURN
```

Nhánh normal:

```text
use(a,b)
→ DROP b
→ DROP a
→ RETURN
```

Có thể merge thành cleanup chung:

```text
if cond:
    jump cleanup

normal:
    use(a,b)
    jump cleanup

cleanup:
    DROP b
    DROP a
    RETURN
```

Đây là **cleanup sharing**.

---

# 13. Early return

Tất cả:

```text
return
return x
return err
return ? 
panic
```

đều phải đi qua cleanup semantics thích hợp.

Ví dụ:

```axiom
fn f() -> Result<i32, Error> {
    let file = open()?
    let x = calculate()?
    return Ok(x)
}
```

Có hai loại exit:

```text
success
error
```

Nhưng cả hai đều phải resolve:

```text
file
x / temporary resources
```

---

# 14. `?` đặc biệt quan trọng

Giả sử:

```axiom
let file = open()?
let data = read(file)?
```

Nếu:

```text
read(file)
```

trả:

```text
Err(e)
```

thì:

```text
file
```

vẫn đang OWNED.

Compiler phải:

```text
receive Err(e)
    ↓
cleanup
    ↓
return Err(e)
```

Không được return trực tiếp bỏ qua Drop.

---

# 15. Canonical lowering của `?`

Có thể hạ:

```text
x = call()?
```

thành:

```text
tmp = call()

switch tmp:
    Ok(value):
        x = value
        continue

    Err(error):
        jump cleanup.error(error)
```

Cleanup block:

```text
cleanup.error(error):
    DROP resources
    RETURN Err(error)
```

---

# 16. Panic

Source:

```axiom
let a = A()
panic("bad")
```

Không được:

```text
PANIC
```

rồi bỏ resource.

Nếu profile:

```text
--panic=unwind
```

thì cleanup cần được thực hiện.

Nếu:

```text
--panic=abort
```

thì process terminate.

Điểm quan trọng:

> **Panic strategy là execution policy; resource correctness vẫn phải được xác định rõ.**

Với `abort`, OS reclaim toàn bộ process memory, nhưng resource semantics có thể không chạy destructor nếu chương trình đã terminate.

Do đó `Drop` không nên được hứa là luôn chạy sau `trap/abort`.

---

# 17. `panic=unwind`

CFG semantic:

```text
normal path
     │
     ▼
  cleanup
     │
     ▼
 return

panic path
     │
     ▼
 cleanup
     │
     ▼
 unwind
```

Drop phải được chạy đúng thứ tự trước khi unwind qua frame.

---

# 18. `panic=abort`

```text
PANIC
  ↓
terminate
```

Không cần tạo cleanup path cho process termination.

Nhưng nếu panic xảy ra trong một context mà semantics yêu cầu local cleanup trước khi panic được observable, compiler phải tuân theo profile semantics.

Vì vậy tôi đề xuất Axiom định nghĩa:

```text
panic=unwind
```

là cleanup-guaranteed.

```text
panic=abort
```

là process termination; no local Drop guarantee after abort point.

---

# 19. `trap`

`trap` khác `panic`.

```text
trap()
```

là machine/execution-level termination.

Mặc định:

```text
TRAP
```

không unwind.

Không nên ép compiler tạo destructor chain giống exception.

---

# 20. `break`

Ví dụ:

```axiom
while cond {
    let resource = Resource()

    if done {
        break
    }
}
```

`resource` phải Drop trước khi thoát iteration.

CFG:

```text
body
 │
 ├── normal iteration → cleanup_iteration → loop
 │
 └── break → cleanup_iteration → loop_exit
```

---

# 21. `continue`

Tương tự:

```text
continue
```

phải cleanup những locals có scope kết thúc trước khi quay về loop header.

```text
continue
   ↓
cleanup locals
   ↓
loop header
```

---

# 22. Scope không phải Drop order duy nhất

Đây là điểm quan trọng.

Không nên implement Drop bằng:

```text
AST lexical scopes
```

một cách đơn giản.

Bởi vì:

- move
- partial move
- early return
- branch
- loop
- closure
- async
- `?`

đều khiến resource state phức tạp hơn lexical scope.

Đúng hơn:

```text
Semantic ownership CFG
        ↓
Drop obligations
        ↓
Cleanup CFG
```

---

# 23. Cleanup stack

Verifier có thể duy trì internal:

```text
CleanupFrame {
    resource
    condition
    ownership_state
    drop_order
}
```

Ví dụ:

```text
a = A()
b = B()
c = C()
```

cleanup stack:

```text
[c, b, a]
```

Nhưng đây chỉ là representation thuận tiện.

**Semantic truth vẫn là ownership state + declaration/drop ordering.**

---

# 24. Nested scope

```axiom
fn f() {
    let a = A()

    {
        let b = B()
        use(a, b)
    }

    use(a)
}
```

Semantic:

```text
create a

create b
use
drop b

use a
drop a
```

Cleanup graph:

```text
inner_exit:
    DROP b

function_exit:
    DROP a
```

Không được drop `a` tại inner scope.

---

# 25. Struct Drop

Giả sử:

```text
struct X {
    a: A
    b: B
    c: C
}
```

Nếu `X` có implicit structural Drop:

```text
DROP X
```

được elaborate thành semantic:

```text
DROP c
DROP b
DROP a
```

Nhưng implementation **không nhất thiết phải gọi 3 function riêng biệt**.

Optimizer có thể inline/eliminate/merge.

---

# 26. User-defined Drop

Nếu sau này cho phép:

```axiom
impl Drop for File {
    fn drop(self: mut_view<File>) { ... }
}
```

thì Drop function là semantic destructor.

Nhưng có một quy tắc tôi đề xuất:

> `Drop` không được consume resource theo cách khiến compiler mất khả năng chứng minh ownership.

Nói cách khác:

```text
Drop
```

là terminal ownership operation.

Không được:

```text
drop(x)
    → resurrect x
```

hoặc:

```text
drop(x)
    → move x somewhere else
```

---

# 27. Drop không trả Result

Ta đã quyết định:

```text
Drop -> no recoverable error
```

Do đó:

```text
DROP file
```

không được:

```text
return Err(...)
```

Nếu đóng file có thể thất bại:

```axiom
file.close()?
```

phải được gọi **trước Drop**.

Ví dụ:

```axiom
fn save(file: File) -> Result<(), Error> {
    write(file)?
    file.close()?
}
```

Sau `close()`:

```text
file
```

có thể trở thành resource state đã closed.

Drop sau đó chỉ là final cleanup.

---

# 28. Resource state và ownership state

Đây là một distinction nên giữ:

```text
Ownership:
    OWNED / MOVED / DROPPED

Resource:
    OPEN / CLOSED / ...
```

Không trộn hai khái niệm.

Ví dụ:

```text
File:
    ownership = OWNED
    resource_state = OPEN
```

sau:

```text
file.close()
```

có thể:

```text
ownership = OWNED
resource_state = CLOSED
```

sau Drop:

```text
ownership = DROPPED
```

Điều này sẽ cực kỳ hữu ích cho networking, GPU, sockets, locks...

---

# 29. MutexGuard là ví dụ tuyệt vời

```axiom
let guard = mutex.lock()
use(guard)
```

Khi:

```text
guard
```

Drop:

```text
unlock mutex
```

Đây là **observable resource effect**.

Compiler **không được tự ý hoist Drop lên sớm** chỉ vì `guard` không còn được dùng.

Nếu Drop unlock mutex sớm hơn:

```text
resource lifetime
```

có thể thay đổi synchronization semantics.

---

# 30. Vì vậy Drop có hai loại

Internal classification:

```text
DROP_OBSERVABLE
DROP_NONOBSERVABLE
```

Ví dụ:

### Non-observable

Một temporary compiler-generated buffer không có external effect.

### Observable

```text
MutexGuard
File
Socket
GPU mapping
lock
transaction
```

Optimizer:

```text
non-observable Drop
```

có thể eliminate/move nếu semantics preserved.

Nhưng:

```text
observable Drop
```

phải giữ ordering.

---

# 31. Early Drop optimization

Source:

```axiom
fn f() {
    let a = LargeResource()

    use(a)

    do_other_work()
}
```

Compiler có thể thấy:

```text
last_use(a) = instruction 5
```

và nếu:

```text
Drop(a)
```

không có observable effect ảnh hưởng tới `do_other_work()`,

có thể:

```text
use(a)
DROP a
do_other_work()
```

thay vì:

```text
use(a)
do_other_work()
DROP a
```

Nhưng với observable resource:

```text
File
MutexGuard
```

không được tùy tiện.

---

# 32. Đây tạo ra một optimization rất mạnh

Axiom có thể đạt:

```text
deterministic resource lifetime
```

mà vẫn cho phép compiler:

```text
early destruction
```

khi semantic equivalence được chứng minh.

Điều này tốt hơn việc buộc programmer dùng lexical scope để tối ưu memory.

---

# 33. Drop Elaboration algorithm

Pseudo-code:

```text
elaborate_drops(function):

    ownership = verified_ownership(function)

    for block in CFG:
        determine_exit_kind(block)

    for each terminating edge:
        obligations = ownership.obligations_at(edge)

        cleanup = build_cleanup(obligations)

        redirect edge → cleanup

    canonicalize_cleanup_blocks()

    return function
```

---

# 34. `build_cleanup`

```text
build_cleanup(obligations):

    sort obligations by semantic_drop_order

    for resource in obligations:
        if state(resource) == OWNED:
            emit DROP(resource)

        else if state(resource) == MAYBE:
            emit DROP_IF_OWNED(resource)

        else if state(resource) == MOVED:
            skip

        else if state(resource) == PARTIAL:
            emit partial_drop(resource)
```

---

# 35. Partial drop

```text
partial_drop(p):
    for field in reverse_declaration_order(p):
        if field == OWNED:
            DROP field

        if field == MAYBE:
            DROP_IF_OWNED field
```

Ví dụ:

```text
p.name = MOVED
p.age = OWNED
p.file = OWNED
```

=>:

```text
DROP p.file
DROP p.age
```

---

# 36. Cleanup sharing

Không nên tạo:

```text
100 identical cleanup blocks
```

nếu function có nhiều return.

Compiler có thể canonicalize:

```text
return path A ─┐
return path B ─┼→ cleanup → return
return path C ─┘
```

Nhưng chỉ merge được nếu:

```text
cleanup obligations
+
return payload
+
control semantics
```

tương thích.

---

# 37. Return payload phải sống qua cleanup

Ví dụ:

```axiom
return create_buffer()
```

Compiler không thể để return buffer bị Drop trong cleanup.

MIR:

```text
tmp = create_buffer()
MOVE tmp → return_value
cleanup
RETURN return_value
```

Ownership của return value nằm ngoài cleanup ownership set.

---

# 38. Caller-allocated return

Sau này optimizer có thể biến:

```text
fn make() -> BigStruct
```

thành ABI:

```text
fn make(out: *mut BigStruct)
```

nhưng đây là **ABI optimization**, không phải thay đổi ownership semantics.

Semantic MIR vẫn:

```text
return OWNED(BigStruct)
```

LIR/backend mới quyết định hidden return pointer.

---

# 39. Async và Drop

Đây là phần khó nhất.

```axiom
async fn f() {
    let file = open()
    await something()
    use(file)
}
```

Sau lowering:

```text
State {
    file
    state_id
}
```

`file` phải sống qua suspension.

Do đó:

```text
DROP file
```

không thể đặt trước `SUSPEND`.

---

# 40. Async state machine

Ví dụ:

```text
State0:
    file = open()
    goto State1

State1:
    SUSPEND await
    goto State2

State2:
    use(file)
    DROP file
    COMPLETE
```

Nếu task bị cancelled giữa State1 và State2:

```text
cancel
   ↓
destroy async frame
   ↓
Drop file
```

Do đó async frame destruction cần Drop elaboration.

---

# 41. Async cancellation

Axiom không có arbitrary async kill.

Cancellation là:

```text
request cancellation
```

sau đó task/frame được cleanup theo semantics.

Nếu frame sở hữu:

```text
File
Buffer
MutexGuard
```

thì frame destruction phải resolve ownership.

---

# 42. Async frame Drop

Compiler sinh implicit destructor cho state machine:

```text
drop_async_frame(frame):
    switch frame.state:
        State0:
            drop initialized resources

        State1:
            drop file

        State2:
            drop remaining resources
```

Nhưng chỉ Drop những field đã thực sự initialized.

Đây là một application rất tự nhiên của:

```text
DROP_IF_OWNED
```

---

# 43. MIR sau Drop Elaboration

Raw:

```text
B0:
    a = A()
    b = B()
    if cond -> B1/B2

B1:
    return

B2:
    use(a,b)
    return
```

Verified/elaborated:

```text
B0:
    a = A()
    b = B()
    BRANCH cond → B1 / B2

B1:
    JUMP cleanup.return

B2:
    use(a,b)
    JUMP cleanup.return

cleanup.return:
    DROP b
    DROP a
    RETURN
```

Đây là MIR mà interpreter có thể thực thi trực tiếp.

---

# 44. Một nguyên tắc rất đáng freeze

> **Sau Drop Elaboration, mọi implicit resource cleanup cần thiết phải trở thành explicit MIR control/resource operations.**

Tức là:

```text
Verified MIR
```

không còn phụ thuộc vào:

```text
"compiler sẽ nhớ Drop ở đâu đó"
```

Mọi semantic obligation đã được materialize.

Điều này cực kỳ quan trọng cho:

- interpreter
- optimizer
- backend
- formal verification
- differential testing
- debug
- AI compiler agents

---

# 45. Pipeline chính thức

Tôi đề xuất freeze pipeline này:

```text
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
Raw MIR
 ↓
Type Verification
 ↓
Ownership Verification
 ↓
Region Verification
 ↓
Capability Verification
 ↓
Effect Verification
 ↓
Concurrency Verification
 ↓
Async Verification
 ↓
DROP ELABORATION
 ↓
CLEANUP NORMALIZATION
 ↓
VERIFIED MIR
 ↓
Semantic Oracle
 ↓
Optimizer
 ↓
LIR
 ↓
Machine IR
 ↓
Native
```

---

# 46. Và một thay đổi kiến trúc nhỏ nhưng quan trọng

Ta không nên gọi:

```text
Raw MIR Verification
```

chỉ là `verifier`.

Nên chia thành:

```text
MIR Validation
MIR Verification
MIR Elaboration
```

### Validation

Kiểm tra MIR có cấu trúc hợp lệ:

```text
SSA
CFG
types
terminators
references
```

### Verification

Chứng minh semantic safety:

```text
ownership
views
regions
effects
concurrency
async
```

### Elaboration

Biến implicit semantics thành explicit operations:

```text
Drop
cleanup
state flags
exception/panic paths
```

Sau đó:

```text
Verified MIR
```

là **semantic executable form**.

---

# 47. Điều này cũng giải quyết một vấn đề lớn của Axiom

Ta từng lo:

> Không có borrow checker/lifetime syntax thì làm sao compiler biết lúc nào được giải phóng?

Câu trả lời hoàn chỉnh bây giờ là:

```text
Programmer
    ↓
ownership intent bằng value semantics + move
    ↓
compiler
    ↓
dataflow + region + capability + effect analysis
    ↓
ownership proof
    ↓
drop elaboration
    ↓
explicit cleanup CFG
```

Programmer **không cần viết lifetime**.

Compiler vẫn có một lifetime model rất mạnh ở bên trong.

---

## 48. Bộ test bắt buộc cho Drop Elaboration

Từ đây nên thêm riêng:

```text
tests/drop/
├── basic_drop
├── reverse_order
├── early_return
├── branch
├── loop_break
├── loop_continue
├── move_then_exit
├── partial_move
├── maybe_moved
├── result_question
├── panic_unwind
├── panic_abort
├── trap
├── nested_scope
├── observable_drop
├── nonobservable_drop
├── async_frame_drop
├── cancellation
├── returned_ownership
└── cleanup_dedup
```

Mỗi test không chỉ kiểm tra output.

Phải kiểm tra cả:

```text
source
→ raw MIR
→ verified MIR
→ interpreter result
→ observable Drop event sequence
```

Ví dụ:

```text
DROP_ORDER_001

expected:
    CREATE A
    CREATE B
    CREATE C
    DROP C
    DROP B
    DROP A
```

---

# 49. Tiếp theo nên làm gì?

Sau Drop Elaboration, **không nên nhảy ngay sang optimizer**.

Còn một lớp cực kỳ quan trọng:

```text
                 ┌───────────────┐
                 │  Verified MIR │
                 └───────┬───────┘
                         │
              ┌──────────▼──────────┐
              │   Semantic Oracle   │
              │      Interpreter    │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │ Conformance Suite   │
              └──────────┬──────────┘
                         │
                    correctness
                         │
              ┌──────────▼──────────┐
              │      Optimizer      │
              └─────────────────────┘
```

Vì vậy bước kế tiếp hợp lý nhất là **`AXIOM SEMANTIC ORACLE + MIR INTERPRETER v0.1`**.

Nó sẽ biến toàn bộ các quy tắc vừa xây thành một thứ có thể **chạy được và kiểm chứng được** trước khi ta viết backend x86-64/ARM64. Đây cũng là điểm giúp Axiom tránh rơi vào tình trạng “spec rất đẹp nhưng compiler agent tự diễn giải semantics theo cách khác”.