Tiếp tục. Bây giờ tôi nghĩ **không nên thêm feature mới ngay**. Ta nên làm việc quan trọng hơn: **đóng formal semantics của Verifier v0.1**, để sau này AI agent không tự “sáng tạo” ownership rule khác nhau ở từng module.

# AXIOM VERIFIER FORMAL CORE v0.1

Mục tiêu của phần này:

```text
Typed MIR
   ↓
Formal abstract state
   ↓
Transfer rules
   ↓
Join rules
   ↓
Fixed-point
   ↓
Verified MIR / Reject
```

Nếu phần này ổn, compiler có thể được chia cho nhiều AI agent mà semantics vẫn thống nhất.

---

# 1. Bốn loại sự thật mà Verifier theo dõi

Tôi đề xuất không gom tất cả thành một “borrow checker”.

Verifier có 4 hệ thống độc lập:

```text
┌─────────────────────────────┐
│ 1. Ownership                │
│    "Ai sở hữu giá trị?"     │
├─────────────────────────────┤
│ 2. Initialization           │
│    "Có giá trị hợp lệ?"     │
├─────────────────────────────┤
│ 3. Capability / Region      │
│    "Ai đang được truy cập?" │
├─────────────────────────────┤
│ 4. Effects / Concurrency    │
│    "Operation ảnh hưởng gì?"│
└─────────────────────────────┘
```

Điều này cực kỳ quan trọng.

Ví dụ:

```text
OWNED
```

không có nghĩa:

```text
WRITE allowed
```

Một value có thể:

```text
OWNED
+
READ capability đang active
```

và vì thế mutation có thể bị cấm.

---

# 2. Formal Place

Mọi memory access trong MIR đều phải quy về một `Place`.

Ta định nghĩa:

```text
Place ::= 
    Local(L)
  | Field(P, F)
  | Index(P, I)
  | Deref(P)
```

Ví dụ:

```axiom
person.name
```

thành:

```text
Field(
    Local(person),
    name
)
```

Còn:

```axiom
buffer[i]
```

thành:

```text
Index(
    Local(buffer),
    i
)
```

---

# 3. Place không phải Value

Đây là một phân biệt rất quan trọng.

```text
Place
    = nơi chứa giá trị

Value
    = giá trị lấy ra từ nơi đó
```

Ví dụ:

```axiom
let x = person.age
```

MIR:

```text
p = FIELD_PLACE person.age
x = LOAD p
```

`FIELD_PLACE` không đọc dữ liệu.

Nó chỉ xác định:

```text
"địa điểm cần truy cập"
```

---

# 4. Region là abstraction của Place

Mỗi Place có thể ánh xạ thành một semantic region:

```text
R(Place)
```

Ví dụ:

```text
R(person)       = R0
R(person.name)  = R1
R(person.age)   = R2
```

với:

```text
R1 ⊂ R0
R2 ⊂ R0
R1 ∩ R2 = ∅
```

---

# 5. Region relation

Region relation chính thức:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Ta có:

```text
R1 DISJOINT R2
```

thì:

```text
READ(R1)
WRITE(R2)
```

không conflict.

Nhưng:

```text
READ(R1)
WRITE(R0)
```

conflict vì:

```text
R1 CONTAINED_BY R0
```

---

# 6. Conflict relation

Định nghĩa:

```text
Conflict(A, B)
```

nếu:

```text
Region(A) MAY_OVERLAP Region(B)
```

và access mode conflict.

Bảng:

| A | B | Conflict |
|---|---|---|
| READ | READ | Không |
| READ | WRITE | Có |
| WRITE | READ | Có |
| WRITE | WRITE | Có |
| MOVE | READ | Có |
| MOVE | WRITE | Có |
| MOVE | MOVE | Có |
| DROP | READ | Có |
| DROP | WRITE | Có |
| DROP | MOVE | Có |

`DROP` đặc biệt quan trọng vì Drop thay đổi ownership/resource state.

---

# 7. MOVE không chỉ là WRITE

Tôi muốn khóa điều này.

```text
MOVE(x)
```

không đơn giản là:

```text
WRITE(x)
```

Nó làm thay đổi:

```text
ownership(x):
    OWNED → MOVED
```

và vì vậy mọi capability phụ thuộc vào ownership đó phải được xử lý.

Ví dụ:

```axiom
let v = view(buffer)

consume(buffer)
```

không thể coi là:

```text
WRITE(buffer)
```

mà là:

```text
MOVE(buffer)
INVALIDATE dependent capabilities
```

---

# 8. Capability

Formal:

```text
Capability {
    id
    provenance
    region
    access
    origin
}
```

Ví dụ:

```axiom
let v = view(buffer)
```

tạo:

```text
C1:
    provenance = Storage(S1)
    region     = R(buffer)
    access     = READ
```

`mut_view`:

```text
C2:
    provenance = Storage(S1)
    region     = R(buffer)
    access     = WRITE
```

---

# 9. Capability không sở hữu dữ liệu

Đây là invariant quan trọng:

```text
Capability ≠ Ownership
```

Ví dụ:

```text
buffer:
    OWNED

v:
    READ capability
```

Có hai semantic entities.

Nếu:

```text
DROP(buffer)
```

thì:

```text
buffer → DROPPED
v → INVALID
```

nhưng `v` không phải resource cần Drop.

---

# 10. Capability lifetime

Capability có lifecycle:

```text
ABSENT
   ↓
ACTIVE
   ↓
EXPIRED
```

Không cần:

```text
DROP(view)
```

theo nghĩa resource destruction.

Compiler có thể expire capability tại last-use.

---

# 11. Last-use formal rule

Nếu:

```text
Uses(C) = {u1, u2, ..., un}
```

thì:

```text
LastUse(C) = un
```

Sau `un`:

```text
C = EXPIRED
```

nếu không có escape/suspend/closure capture.

Ví dụ:

```axiom
let v = view(buffer)

read(v)
modify(buffer)
```

Nếu:

```text
read(v)
```

là last-use:

```text
C_v → EXPIRED
```

nên `modify(buffer)` hợp lệ.

---

# 12. Escape làm mất last-use local

Ví dụ:

```axiom
let v = view(buffer)

save_for_later(v)

modify(buffer)
```

Compiler không thể coi `save_for_later(v)` là last-use.

Capability đã escape:

```text
C_v:
    ACTIVE
    ESCAPED
```

Owner mutation:

```text
modify(buffer)
```

=> reject nếu provenance còn sống.

---

# 13. Closure capture

```axiom
let v = view(buffer)

let f = {
    use(v)
}
```

Nếu `f` không escape:

```text
capture lifetime ≤ buffer lifetime
```

có thể hợp lệ.

Nếu:

```axiom
return f
```

thì capability escape function.

Nếu `buffer` là local:

```text
buffer lifetime < returned closure lifetime
```

=> reject.

Đây là cách Axiom tránh lifetime annotation nhưng vẫn đảm bảo lifetime.

---

# 14. Ownership state của aggregate

Ta cần hỗ trợ partial ownership.

Ví dụ:

```axiom
struct User {
    name: String
    age: i32
}
```

Sau:

```axiom
let name = move user.name
```

state:

```text
user:
    PARTIAL

    name → MOVED
    age  → OWNED
```

---

# 15. Whole-value access sau partial move

```axiom
let name = move user.name

print(user)
```

=> reject.

Vì:

```text
user = PARTIAL
```

không còn là complete value.

Nhưng:

```axiom
print(user.age)
```

=> hợp lệ.

---

# 16. Partial Drop

Khi:

```text
user.name = MOVED
user.age = OWNED
```

Drop `user` phải chỉ Drop:

```text
user.age
```

không Drop:

```text
user.name
```

Nếu không:

```text
double destruction
```

Do đó Drop elaboration phải đọc ownership tree.

---

# 17. Ownership tree

Ta có thể mô hình:

```text
user
├── name
│    └── MOVED
└── age
     └── OWNED
```

Khi:

```text
DROP(user)
```

compiler recursively xử lý:

```text
if field == OWNED:
    DROP(field)

if field == MOVED:
    skip

if field == PARTIAL:
    recurse
```

---

# 18. Assignment formal rule

Đây là phần execution semantics vừa đóng trước đó.

```axiom
x = expression
```

phải:

```text
1. evaluate RHS
2. resolve destination
3. validate replacement
4. drop old destination if necessary
5. move/store new value
```

Không được:

```text
drop x
evaluate RHS
```

vì:

```axiom
x = transform(x)
```

sẽ hỏng.

---

# 19. Self assignment

Ví dụ:

```axiom
x = x
```

Nếu `x: Copy`:

```text
COPY(x)
STORE(x)
```

hợp lệ.

Nếu `x` owning non-Copy:

```text
MOVE(x)
STORE(x)
```

sẽ tạo vấn đề ownership.

Do đó:

```text
REJECT
AX_OWN_....
self-assignment of non-Copy owning value
```

Đây là một trong những nơi Axiom nên **reject compile-time thay vì cố đoán ý programmer**.

---

# 20. Move semantics

Formal:

```text
MOVE(P)
```

requires:

```text
Ownership(P) == OWNED
Initialization(P) == INIT
```

result:

```text
Ownership(P) := MOVED
```

Nếu `P` có children:

```text
whole move
```

thì tất cả ownership subtree chuyển sang destination.

---

# 21. Copy semantics

```text
COPY(P)
```

requires:

```text
Copy(Type(P))
```

Sau đó:

```text
source remains OWNED
destination becomes OWNED
```

Không tạo shared alias.

Đây là invariant:

> **Copy không bao giờ biến hai value thành cùng một mutable object.**

---

# 22. Clone

Nếu programmer muốn tạo ownership mới nhưng type không `Copy`:

```axiom
let b = clone(a)
```

`clone` là function/trait behavior.

Compiler không được biến:

```axiom
let b = a
```

thành:

```text
clone(a)
```

vì sẽ tạo hidden allocation/copy cost và thay đổi semantics.

---

# 23. Function call

Mỗi parameter có mode semantic.

Có thể biểu diễn:

```text
ParamMode:
    IN
    VIEW
    MUT_VIEW
    OWN
```

Ví dụ:

```axiom
fn inspect(x: view<Data>)
```

call:

```axiom
inspect(data)
```

compiler tạo ephemeral capability.

---

# 24. `OWN` parameter

```axiom
fn consume(x: Data)
```

mặc định:

```text
argument → MOVE
```

Nếu:

```axiom
consume(x)
use(x)
```

=> reject nếu `Data` non-Copy.

Nếu `Data: Copy`, language có thể coi argument passing là copy theo value semantics.

---

# 25. Return ownership

```axiom
fn create() -> Buffer<u8>
```

MIR:

```text
ALLOC
...
RETURN OWNED(buffer)
```

Caller:

```text
let x = create()
```

nhận ownership.

Không có hidden reference counting.

---

# 26. Return view

Đây là nơi provenance trở thành bắt buộc.

```axiom
fn first(x: view<Array>) -> view<Item>
```

Return capability phải chứng minh:

```text
provenance(return) ⊆ provenance(input)
```

Ví dụ hợp lệ:

```text
input:
    Array storage S1

return:
    element region R1 ⊂ S1
```

---

# 27. Return local view

```axiom
fn bad() -> view<i32> {
    var x = 10
    return view(x)
}
```

Compiler:

```text
x lifetime ends at function return
```

nhưng returned capability sống sau return.

=> reject.

Diagnostic:

```text
AX_VIEW_0001
returned view may outlive its owner
```

---

# 28. Region subtyping

Có thể cho phép:

```text
view<Person>
```

derive:

```text
view<Person.name>
```

nhưng không ngược lại.

Ví dụ:

```text
R_name ⊂ R_person
```

Capability:

```text
READ(R_person)
```

có thể tạo:

```text
READ(R_name)
```

nhưng:

```text
READ(R_name)
```

không thể truy cập:

```text
R_person.age
```

---

# 29. `mut_view` phải exclusive

Nếu:

```axiom
let a = mut_view(buffer)
let b = mut_view(buffer)
```

thì:

```text
WRITE(R)
WRITE(R)
```

conflict.

=> reject.

Nhưng:

```axiom
let a = mut_view(person.name)
let b = mut_view(person.age)
```

có thể:

```text
R_name DISJOINT R_age
```

=> accept.

Đây chính là lợi thế của semantic region analysis.

---

# 30. READ views có thể nhiều

```axiom
let a = view(buffer)
let b = view(buffer)
```

=>:

```text
READ(R)
READ(R)
```

không conflict.

Có thể có:

```text
C1 READ
C2 READ
C3 READ
...
```

---

# 31. READ + MOVE

```axiom
let v = view(buffer)
consume(buffer)
```

=> conflict.

Không cần đợi tới khi `v` được sử dụng.

Lý do:

```text
MOVE(buffer)
```

làm owner thay đổi và storage có thể bị giải phóng.

---

# 32. `MAY_RELOCATE`

Đây nên là effect chính thức:

```text
MAY_RELOCATE(StorageIdentity)
```

Ví dụ:

```text
Vec.push
Vec.reserve
Vec.resize
Vec.insert
```

có thể:

```text
WRITE
MAY_RELOCATE
```

Trong khi:

```text
Vec.set
```

chỉ:

```text
WRITE(element)
```

---

# 33. Storage identity

Ta chính thức có:

```text
RegionIdentity
StorageIdentity
```

Khác nhau:

```text
Region = logical memory area
Storage = physical backing identity
```

Ví dụ:

```text
Vec
  Region R1
  Storage S1
```

reallocation:

```text
Region R1
Storage S1 → S2
```

Các capability:

```text
provenance = S1
```

=> expired.

---

# 34. Đây cũng giải quyết pointer stability

Axiom mặc định:

```text
ordinary value
```

không có stable address identity.

Nếu programmer cần:

```text
stable address
```

phải dùng abstraction:

```text
Box<T>
Pinned<T>
Stable<T>
```

hoặc system storage tương ứng.

Điều này cho phép compiler tự do:

```text
move
stack promote
register allocate
scalarize
```

mà không phá semantics.

---

# 35. `Box<T>` trở thành storage abstraction

```axiom
let x = Box.new(value)
```

semantic:

```text
x owns dynamic storage
```

Nhưng physical:

```text
heap
arena
custom allocator
```

là implementation detail của `Box`.

Nếu địa chỉ được expose:

```axiom
unsafe {
    raw_ptr(x)
}
```

thì storage identity trở thành observable boundary.

Compiler không được tùy tiện relocate sau đó.

---

# 36. Address identity là opt-in

Đây là nguyên tắc tôi nghĩ rất đáng giữ:

```text
ordinary value
    → no stable address guarantee

explicit storage/address API
    → stable address becomes semantic
```

Như vậy compiler có rất nhiều freedom để tối ưu.

---

# 37. Effect lattice

Không nên lưu effect chỉ là một list.

Có thể dùng:

```text
EffectSet
```

với bitsets:

```text
READ
WRITE
MOVE
DROP
ALLOC
DEALLOC
RELOCATE
SUSPEND

IO
ATOMIC
SYNC
VOLATILE
FFI
PANIC
TRAP
RESOURCE_RELEASE
```

Một function summary:

```text
EffectSet {
    READ(arg0)
    WRITE(arg1)
    MAY_RELOCATE(arg1)
}
```

---

# 38. Conservative effect inference

Nếu compiler không biết function làm gì:

```text
CALL unknown()
```

thì:

```text
UNKNOWN_EFFECT
```

không được suy ra:

```text
NO_EFFECT
```

Nhưng khi compiler có body:

```text
infer effects
```

rồi propagate summary.

Ví dụ:

```text
foo()
 └── bar()
      └── Vec.push()
```

=> `foo` có:

```text
MAY_RELOCATE(...)
```

nếu region mapping cho phép.

---

# 39. Inlining không thay đổi semantic effect

Trước optimization:

```text
CALL foo
```

sau inlining:

```text
WRITE R1
DROP R2
```

Effect semantics phải tương đương.

Optimizer có thể **mở function**, nhưng không được tạo semantics mới.

---

# 40. Formal Verified MIR condition

Một function được coi là Verified nếu:

```text
V1  mọi read có initialization proof
V2  mọi write có valid ownership/capability
V3  mọi move từ owned value
V4  mọi drop không double-drop
V5  mọi capability provenance còn sống
V6  không có conflicting safe accesses
V7  mọi Send crossing hợp lệ
V8  mọi Share crossing hợp lệ
V9  synchronization constraints hợp lệ
V10 mọi suspension state hợp lệ
V11 mọi exit path cleanup hợp lệ
V12 mọi FFI/unsafe boundary được đánh dấu
```

---

# 41. Một insight quan trọng

Đến đây có thể thấy:

**Axiom không thực sự cần “borrow checker”.**

Nó cần:

```text
Ownership verifier
+
Capability verifier
+
Region verifier
+
Effect verifier
+
Concurrency verifier
```

“Borrow checking” chỉ là **một kết quả emergent** của các hệ thống này.

Điều này tốt hơn về mặt kiến trúc vì sau này có thể thêm:

```text
GPU memory
DMA buffer
shared memory
network buffer
mmap
IPC
FFI
```

mà không phải mở rộng một borrow checker monolithic.

---

# 42. Đây là kiến trúc tôi muốn đóng băng

```text
                    AXIOM MEMORY SAFETY
                           │
          ┌────────────────┼────────────────┐
          │                │                │
      Ownership        Capability        Effects
          │                │                │
          │             Region              │
          │                │                │
          └────────────────┼────────────────┘
                           │
                    Concurrency
                           │
                    Send / Share
                           │
                  Synchronization
                           │
                     Async/Await
                           │
                           ↓
                       VERIFIER
                           │
                           ↓
                    VERIFIED MIR
```

Không có:

```text
GC
implicit RC
lifetime syntax
borrow syntax
mandatory heap
mandatory runtime
```

nhưng vẫn có:

```text
deterministic lifetime
use-after-free prevention
double-free prevention
dangling-view prevention
data-race prevention
relocation safety
partial-move safety
async safety
```

---

## 43. Bước tiếp theo nên chuyển sang một phần rất thực dụng

Sau khi formal hóa như trên, **không nên tiếp tục lý thuyết quá lâu**.

Tôi đề xuất bước tiếp theo là xây **AXIOM VERIFIER CONFORMANCE SUITE v0.1** gồm khoảng **50–70 chương trình Axiom cực ngắn**, mỗi chương trình có:

```text
TEST-ID
SOURCE
EXPECTED: ACCEPT / REJECT
DIAGNOSTIC
OWNERSHIP STATE
REGION STATE
CAPABILITY STATE
EXPECTED EFFECT
EXPECTED VERIFIED-MIR PROPERTY
```

Đặc biệt phải có những case “gài bẫy” như:

```text
x = transform(x)
partial move + Drop
view + Vec.reallocation
disjoint field mutation
view qua closure
view qua await
Send nhưng không Share
Share nhưng không Send
MutexGuard + last-use
atomic Relaxed
channel ownership transfer
branch + partial move
loop + move
unknown FFI
unsafe pointer
nested struct partial move
```

Nếu bộ test này chạy ổn, **chúng ta mới có cơ sở nói semantics của Axiom thực sự kín**, thay vì chỉ có một thiết kế nghe hợp lý trên giấy.

Và sau Verifier, phần tiếp theo tôi muốn làm là **Storage/Allocator Model v0.1** — vì đó sẽ trả lời trực tiếp câu hỏi bạn từng đặt ra: *Axiom nên dùng flat memory, stack/heap, arena, pool hay mô hình nào để vừa nhanh vừa tránh fragmentation mà không ép programmer quản lý con trỏ*.