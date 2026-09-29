Tiếp tục. Bây giờ đi vào phần quan trọng nhất của Axiom: **Ownership / Region / Capability Verifier v0.1**.

Nếu phần này thiết kế tốt, Axiom có thể đạt mục tiêu khá đặc biệt:

> **Programmer không phải viết lifetime/borrow annotation, nhưng compiler vẫn chứng minh được ownership, aliasing và lifetime của safe code.**

---

# AXIOM VERIFIER v0.1

## 1. Nguyên tắc kiến trúc

Verifier không phải một pass duy nhất.

Tôi đề xuất:

```text
                         Typed MIR
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Initialization    Ownership       Region
          Analysis       Analysis       Analysis
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     Capability Analysis
                            │
                            ▼
                       Effect Analysis
                            │
                            ▼
                     Drop / Cleanup
                            │
                            ▼
                   Concurrency Analysis
                            │
                            ▼
                      VERIFIED MIR
```

Nhưng các pass này không hoàn toàn độc lập.

Chúng chia sẻ một **Verifier State**.

---

# 2. Verifier State

Đề xuất cấu trúc:

```text
VerifierState {
    locals
    values
    ownership
    initialization
    places
    regions
    capabilities
    effects
    cleanup
    concurrency
}
```

Trong đó:

```text
ownership:
    LocalId → OwnershipState

initialization:
    Place → InitState

capabilities:
    ViewId → Capability

regions:
    Place → Region

cleanup:
    Scope/Block → CleanupState
```

---

# 3. Ownership state

Đừng chỉ dùng:

```text
OWNED / MOVED
```

Vì partial move và branch cần nhiều trạng thái hơn.

Internal lattice:

```text
                    MAYBE
                   /     \
               OWNED     MOVED
                  \       /
                   PARTIAL
                      │
                 DROPPED
```

Nhưng thực tế nên biểu diễn dạng cấu trúc thay vì một enum đơn giản.

Ví dụ:

```text
OwnershipState {
    status: OWNED | MOVED | PARTIAL | DROPPED | MAYBE
    children: FieldStateMap
}
```

Với:

```text
Person
├── name → OWNED
└── age  → MOVED
```

thì:

```text
Person = PARTIAL
```

---

# 4. Initialization cũng phải độc lập

Ownership và initialization **không phải cùng một thứ**.

Ví dụ:

```axiom
var x: Buffer

if condition {
    x = create()
}

use(x)
```

`x` có thể:

```text
initialized = MAYBE
ownership = MAYBE_OWNED
```

Cho nên cần:

```text
InitState:
    UNINIT
    INIT
    MAYBE_INIT
```

Không nên suy luận initialization chỉ từ ownership.

---

# 5. Place là đơn vị phân tích

Đây là quyết định rất quan trọng.

Không phân tích:

```text
variable x
```

mà phân tích:

```text
Place
```

Ví dụ:

```text
p
p.name
p.age
p.address
p.address.city
```

Mỗi Place có region.

```text
Region(p)
Region(p.name)
Region(p.age)
Region(p.address.city)
```

---

# 6. Region model

Region không cần phải là byte address.

Nó là **semantic memory region**.

Ví dụ:

```text
R0 = Person
R1 = Person.name
R2 = Person.age
R3 = Person.address
R4 = Person.address.city
```

Quan hệ:

```text
R1 DISJOINT R2

R4 CONTAINS? R4 is contained by R3

R0 CONTAINS R1
R0 CONTAINS R2
R0 CONTAINS R3
```

---

# 7. Region overlap

Verifier cần hàm:

```text
may_overlap(R1, R2)
```

Kết quả:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Trong đó `UNKNOWN` phải được xử lý như potentially overlapping.

Ví dụ:

```axiom
fn f(p: mut_view<Person>) {
    write(p.name)
    write(p.age)
}
```

Compiler biết:

```text
Region(p.name)
DISJOINT
Region(p.age)
```

=> OK.

Nhưng:

```axiom
fn f(a: mut_view<Person>) {
    write(a)
    read(a.age)
}
```

thì:

```text
Region(a)
CONTAINS
Region(a.age)
```

=> conflict.

---

# 8. Access capability

Tôi muốn nâng cấp mô hình trước đây một chút.

Thay vì chỉ:

```text
READ
WRITE
MOVE
DROP
```

nên có:

```text
Capability {
    region
    mode
    provenance
    owner
    lifetime
}
```

Mode:

```text
READ
WRITE
MOVE
DROP
```

Ví dụ:

```text
view(p.name)
```

tạo:

```text
Capability #7

region     = p.name
mode       = READ
provenance = p
```

---

# 9. Conflict algorithm

Khi compiler gặp access:

```text
access(A, modeA)
```

tìm các capability/access đang active.

Với mỗi:

```text
access(B, modeB)
```

nếu:

```text
may_overlap(A.region, B.region)
```

thì:

| A | B | Kết quả |
|---|---|---|
| READ | READ | OK |
| READ | WRITE | ERROR |
| WRITE | READ | ERROR |
| WRITE | WRITE | ERROR |
| MOVE | anything | ERROR |
| anything | MOVE | ERROR |
| DROP | anything | ERROR |
| anything | DROP | ERROR |

Nhưng có một điểm quan trọng:

**Không phải mọi access đều tạo capability sống lâu.**

Một READ thông thường:

```axiom
print(x)
```

chỉ tồn tại trong thời gian của operation.

Không được biến nó thành borrow kéo dài đến cuối scope.

Đây là cách Axiom tránh phần lớn phiền phức của Rust.

---

# 10. View mới là capability dài hạn

Ví dụ:

```axiom
let v = view(buffer)
```

thì capability:

```text
READ(buffer.region)
```

được giữ cho đến semantic last-use của `v`.

Trong khi:

```axiom
use(buffer)
```

chỉ tạo:

```text
READ(buffer)
```

trong một instruction/call.

Do đó:

```axiom
let v = view(buffer)

use(buffer)
```

bị reject.

Nhưng:

```axiom
use(buffer)

let v = view(buffer)
```

OK.

---

# 11. Last-use analysis

Đây là thứ giúp Axiom đơn giản hơn Rust.

Compiler trước tiên xác định:

```text
uses(v)
```

Ví dụ:

```axiom
let v = view(buffer)

foo(v)
bar(v)

modify(buffer)
```

CFG/use analysis xác định:

```text
last_use(v) = foo? 
```

Không, vì còn:

```text
bar(v)
```

nên:

```text
last_use(v) = bar(v)
```

Sau đó capability kết thúc:

```text
READ(buffer)
```

và:

```text
modify(buffer)
```

được phép.

---

# 12. Nhưng có một giới hạn quan trọng

Last-use không được phá semantics của escaping references.

Ví dụ:

```axiom
fn save(v: view<u8>) {
    global_view = v
}
```

Nếu `global_view` có lifetime dài hơn owner:

```text
escape
```

Verifier phải phát hiện.

Do đó cần:

```text
EscapeAnalysis
```

với trạng thái:

```text
NON_ESCAPING
LOCAL_ESCAPE
RETURN_ESCAPE
GLOBAL_ESCAPE
THREAD_ESCAPE
ASYNC_ESCAPE
UNKNOWN_ESCAPE
```

---

# 13. Function call là điểm khó nhất

Ví dụ:

```axiom
foo(buffer)
```

Verifier phải biết `foo` làm gì.

Không thể chỉ nhìn kiểu:

```text
foo(Buffer)
```

Mà cần effect summary.

Ví dụ:

```text
foo:
    READ(arg0)
```

hoặc:

```text
foo:
    WRITE(arg0)
```

hoặc:

```text
foo:
    MOVE(arg0)
```

---

# 14. Effect summary

Mỗi function có semantic summary:

```text
FunctionEffects {
    accesses
    ownership
    allocations
    resource
    concurrency
    panic
}
```

Ví dụ:

```text
fn length(v: view<Vec>) -> usize
```

summary:

```text
READ(arg0)
```

Ví dụ:

```text
fn clear(v: mut_view<Vec>)
```

summary:

```text
WRITE(arg0)
```

Ví dụ:

```text
fn consume(b: Buffer)
```

summary:

```text
MOVE(arg0)
DROP(arg0)
```

---

# 15. Effects phải có region projection

Đây là chỗ rất mạnh.

Không chỉ:

```text
READ(arg0)
```

mà:

```text
READ(arg0.name)
```

Ví dụ:

```axiom
fn get_age(p: view<Person>) -> i32 {
    p.age
}
```

Summary:

```text
READ(arg0.age)
```

Sau đó:

```axiom
let v = mut_view(person.name)

get_age(person)
```

có thể **được phép** nếu compiler chứng minh:

```text
person.name
DISJOINT
person.age
```

Đây là khả năng mà một ownership system quá đơn giản sẽ bỏ lỡ.

---

# 16. Unknown function

Nếu compiler không biết effect:

```text
extern fn mysterious(...)
```

thì không được giả định:

```text
READ nothing
```

Mặc định:

```text
UNKNOWN
```

và conservative.

Ví dụ:

```axiom
let v = view(buffer)
foreign_call(buffer)
use(v)
```

Nếu `foreign_call` không có effect contract:

```text
REJECT / require unsafe
```

Tùy API boundary.

---

# 17. FFI effect contract

Cho phép:

```axiom
@ffi_effects(
    read(arg0),
    write(arg1)
)
extern @abi(C) fn foo(...)
```

Compiler lúc này biết chính xác hơn.

Nhưng contract là **trusted information**.

Nếu programmer khai sai:

```text
@ffi_effects(read(arg0))
```

trong khi native function thực tế write:

```text
```

thì đó là lỗi unsafe/FFI boundary, không phải verifier bug.

---

# 18. CFG Dataflow

Verifier chạy forward dataflow.

Ví dụ:

```text
       B0
       │
       ▼
    branch
    /     \
   B1     B2
    \     /
     ▼   ▼
       B3
```

Mỗi block:

```text
IN[B]
OUT[B]
```

Với:

```text
OUT[B] = Transfer(B, IN[B])
```

và:

```text
IN[B] = Merge(OUT[pred1], OUT[pred2], ...)
```

Lặp đến fixed point.

---

# 19. Merge ownership

Ví dụ:

```text
B1:
    x = OWNED
```

```text
B2:
    x = MOVED
```

join:

```text
B3:
    x = ?
```

Không thể chọn:

```text
OWNED
```

phải:

```text
MAYBE
```

Sau đó:

```axiom
use(x)
```

=> reject.

---

# 20. Merge partial states

Ví dụ:

Path 1:

```text
p.name = MOVED
p.age  = OWNED
```

Path 2:

```text
p.name = OWNED
p.age  = OWNED
```

Join:

```text
p.name = MAYBE_MOVED
p.age  = OWNED
```

Do đó:

```axiom
use(p.age)
```

OK.

Nhưng:

```axiom
use(p.name)
```

không OK.

Đây là lý do ownership phải được tracking **theo Place**, không chỉ Local.

---

# 21. Loop fixed point

Ví dụ:

```axiom
let x = create()

while cond {
    use(x)
}
```

Iteration đầu:

```text
x = OWNED
```

sau body:

```text
x = OWNED
```

fixed point ngay.

Accept.

Nhưng:

```axiom
while cond {
    consume(x)
}
```

sau iteration:

```text
x = MOVED
```

join với trạng thái loop entry:

```text
OWNED + MOVED
```

=> MAYBE.

Iteration tiếp theo:

```text
consume(x)
```

không chứng minh được an toàn.

Reject.

---

# 22. Partial move + loop

Ví dụ khó hơn:

```axiom
let p = create()

while cond {
    consume(p.name)
}

use(p.age)
```

Điều này **có thể Accept**.

Bởi:

```text
p.name
```

không ảnh hưởng:

```text
p.age
```

Nhưng chỉ nếu:

```text
consume(p.name)
```

không có semantic effect lên whole `p`.

Đây là một test rất tốt cho region analysis.

---

# 23. Ownership state không nên là một enum duy nhất

Tôi khuyên compiler nội bộ dùng:

```text
PlaceState {
    init
    owner
    moved
    drop
    capability_set
}
```

Ví dụ:

```text
p:
    init = INIT
    owner = PARTIAL

p.name:
    init = INIT
    owner = MOVED

p.age:
    init = INIT
    owner = OWNED
```

Điều này dễ mở rộng hơn nhiều.

---

# 24. Drop analysis

Sau ownership analysis, compiler chạy:

```text
Drop Elaboration
```

Mục tiêu:

> Mỗi resource phải được release đúng một lần trên mọi terminating path.

Ví dụ:

```axiom
fn f() {
    let a = create_a()
    let b = create_b()

    if cond {
        return
    }

    use(a)
}
```

Compiler tạo cleanup:

```text
return_path:
    DROP b
    DROP a
    RETURN

normal_path:
    DROP b
    DROP a
    RETURN
```

Sau đó optimizer có thể hợp nhất cleanup.

---

# 25. Drop flags

Conditional initialization cần:

```text
drop_flag(a)
```

Ví dụ:

```axiom
var a: Resource

if condition {
    a = create()
}
```

Cleanup:

```text
if initialized(a) {
    DROP a
}
```

Nhưng đây chỉ là **compiler IR concept**.

Native optimizer có thể biến nó thành branch rất nhỏ hoặc loại bỏ hoàn toàn.

---

# 26. Partial Drop

Ví dụ:

```text
p.name = MOVED
p.age = OWNED
```

Drop elaborator phải sinh:

```text
DROP_IF_OWNED(p.age)
```

và:

```text
DO_NOT_DROP(p.name)
```

Không cần instruction `DO_NOT_DROP`; đó chỉ là logic verifier.

---

# 27. Một nguyên tắc rất quan trọng cho Drop

**Drop không phải ownership access bình thường.**

Nó có semantic quyền đặc biệt:

```text
DROP
```

chỉ được phép nếu:

```text
OWNED
```

hoặc:

```text
PARTIAL
```

và chỉ drop những child còn OWNED.

Không được:

```text
DROP(MOVED)
```

---

# 28. `Drop` không được throw

Ta nên chốt điều này trong verifier:

```text
Drop:
    cannot return Result
    cannot throw
    cannot suspend
```

Nếu cleanup cần lỗi:

```axiom
close(file) -> Result<(), Error>
```

phải được gọi explicit trước.

Sau đó:

```text
Drop<File>
```

là fallback deterministic cleanup.

Điều này làm compiler cực kỳ đơn giản.

---

# 29. Concurrency verifier

Sau ownership/capability, ta có:

```text
Send
Share
```

Mỗi type có property:

```text
Send(T)
Share(T)
```

Ví dụ:

```text
i32:
    Copy
    Send
    Share

Vec<T>:
    Send if T: Send
    Share = false

Arc<T>:
    Send if T: Send
    Share if T: Share
```

Đây là compiler-known property, không phải trait bình thường.

---

# 30. Spawn

Ví dụ:

```axiom
let x = create()
spawn(move || use(x))
```

Compiler thấy closure capture:

```text
capture x = MOVE
```

Sau đó:

```text
spawn
```

yêu cầu:

```text
Send(captured environment)
```

Nếu:

```text
Send(x)
```

=> OK.

Nếu không:

```text
REJECT
```

---

# 31. Share không thay thế Send

Đây là invariant quan trọng:

```text
Send != Share
```

Một object có thể:

```text
Send = true
Share = false
```

Ví dụ một mutable container.

Có thể chuyển ownership:

```text
thread A
    ↓ MOVE
thread B
```

nhưng không thể cùng truy cập.

---

# 32. Async

Verifier xử lý:

```text
SUSPEND
```

như một boundary đặc biệt.

Tất cả value/capability sống qua:

```text
SUSPEND
```

phải được kiểm tra.

Ví dụ:

```axiom
let v = view(x)
await foo()
use(v)
```

thì:

```text
v
x
```

phải cùng tồn tại hợp lệ xuyên suspension.

---

# 33. Async + mutable view

Đây là case nguy hiểm:

```axiom
let v = mut_view(x)

await foo()

modify(v)
```

Nếu executor có thể migrate task, state phải an toàn theo semantics.

Ngoài ra không được có:

```text
other access to x
```

xen giữa suspension nếu capability vẫn sống.

Do đó async verifier cần kiểm tra:

```text
live capabilities across suspension
```

---

# 34. Một cải tiến quan trọng: Capability không nhất thiết phải sống đến lexical scope

Axiom nên sử dụng:

```text
semantic lifetime
```

chứ không:

```text
lexical lifetime
```

Ví dụ:

```axiom
{
    let v = view(buffer)
    print(v)
    modify(buffer)
}
```

Không nên reject chỉ vì `v` còn nằm trong `{}`.

Compiler thấy:

```text
last use(v)
```

và kết thúc capability tại đó.

Đây chính là một trong những điểm tôi nghĩ Axiom có thể **đơn giản hơn đáng kể đối với programmer**.

---

# 35. Nhưng compiler không được tự ý kéo dài/thu ngắn lifetime qua observable semantics

Ví dụ:

```axiom
let lock = mutex.lock()
use(lock)
...
```

Nếu Drop của `lock` unlock mutex, thì lifetime của `lock` có observable synchronization effect.

Compiler không được tùy tiện:

```text
DROP(lock)
```

sớm hơn semantics cho phép.

Do đó:

```text
semantic last use
```

không đồng nghĩa:

```text
free at any arbitrary point
```

Đây là lý do cần `RESOURCE_RELEASE` / `DROP_OBSERVABLE`.

---

# 36. Verifier hoàn chỉnh

Sau tất cả, pipeline sẽ là:

```text
                  MIR
                   │
                   ▼
          Definite Initialization
                   │
                   ▼
            Ownership Analysis
                   │
                   ▼
             Place Analysis
                   │
                   ▼
             Region Analysis
                   │
                   ▼
          Capability Validation
                   │
                   ▼
             Effect Analysis
                   │
                   ▼
              Escape Analysis
                   │
                   ▼
            Drop Elaboration
                   │
                   ▼
         Concurrency / Send / Share
                   │
                   ▼
             Async Validation
                   │
                   ▼
             VERIFIED MIR
```

---

# 37. Nhưng có một điều tôi **không** muốn Axiom làm

Không nên biến hệ thống này thành một “Rust borrow checker 2.0”.

Tức là không nên thêm vào ngôn ngữ:

```text
'a
&'a T
&'mut T
where lifetime...
```

hay bắt programmer giải quyết:

```text
lifetime parameter
```

Mọi thứ đó thuộc:

```text
Compiler internal model
```

Programmer chỉ cần hiểu:

```text
OWNING VALUE
view<T>
mut_view<T>
MOVE
unsafe
Send
Share
```

Đó là abstraction boundary rất đẹp.

---

# 38. Kiến trúc cuối cùng của memory safety

Có thể tóm lại bằng một câu:

> **Axiom exposes ownership capabilities, not lifetime machinery.**

Programmer:

```text
Buffer
view<Buffer>
mut_view<Buffer>
move
unsafe
Send
Share
```

Compiler:

```text
Ownership
+
Places
+
Regions
+
Capabilities
+
Effects
+
Escape
+
Dataflow
+
Drop
```

Đây là hướng tôi nghĩ phù hợp nhất với mục tiêu ban đầu của bạn: **hiệu năng hệ thống cao nhưng không bắt programmer chịu toàn bộ độ phức tạp của memory model**.

---

## Một vấn đề còn phải giải quyết trước khi gọi Verifier v0.1 là “đóng băng”

Có **3 quyết định semantic** hiện vẫn chưa nên để AI agent tự suy diễn:

1. **Khi nào owning value tự động chuyển thành `view<T>`?**
   ```axiom
   fn sum(v: view<i32>)
   let a = Vec(...)
   sum(a)
   ```
   Có implicit view hay bắt buộc:
   ```axiom
   sum(view(a))
   ```

2. **`Vec` mutation nào invalidate view?**
   `push`, `reserve`, `sort`, `clear`, `resize`, v.v.

3. **Last-use có phải semantic rule hay chỉ là compiler optimization?**

Tôi nghiêng về một hướng khá mạnh:

```text
view<T> là explicit trong type/API,
nhưng creation có thể implicit ở những conversion an toàn,
và compiler tự kết thúc capability tại semantic last-use.
```

Ví dụ:

```axiom
fn sum(v: view<i32>) -> i32

let numbers = Vec(...)
sum(numbers)
```

có thể tự tạo temporary view **chỉ trong thời gian call**.

Nhưng nếu muốn giữ view:

```axiom
let v = view(numbers)
```

phải thể hiện rõ trong source.

Điều này giữ được mục tiêu **API rõ ràng + programmer không phải quản lý lifetime**.

Bước tiếp theo nên là **đóng chính xác 3 semantics này + thiết kế `Vec/Buffer` invalidation model**, rồi mới viết pseudo-code chính thức cho thuật toán verifier.