# BOOTSTRAP-244 — AXIOM PLACE MODEL, LVALUE/RVALUE SEMANTICS & MEMORY ACCESS LOWERING

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là một trong những phần quan trọng nhất của Axiom. Nó nối trực tiếp:

```text
Surface Syntax
      ↓
Typed HIR
      ↓
Place Model
      ↓
Ownership / Capability
      ↓
MIR
      ↓
Alias Analysis
      ↓
Optimization
      ↓
Machine Code
```

Mục tiêu lớn nhất:

> **Programmer thao tác với giá trị và cấu trúc dữ liệu; compiler tự quyết định khi nào cần địa chỉ, load/store, register, stack hay memory.**

Không đưa mô hình `lvalue/rvalue/pointer/reference` kiểu C++ vào surface language.

---

# 1. Vấn đề cần giải quyết

Xét:

```axiom
let p = person.address.city
```

Compiler phải biết:

```text
person
  └── address
       └── city
```

đây là **một vị trí có thể đọc**.

Nhưng:

```axiom
person.address.city = "Hanoi"
```

lại là **một vị trí có thể ghi**.

Còn:

```axiom
foo(person.address.city)
```

có thể là:

```text
Copy
Move
view
mut_view
```

tùy type và signature của `foo`.

Do đó Axiom cần một semantic abstraction mạnh hơn `lvalue/rvalue`.

---

# 2. Place

Axiom định nghĩa:

> **Place là một semantic location có thể được truy cập bằng ownership/capability rules.**

Ví dụ:

```axiom
x
x.field
x[i]
x[start:end]
```

đều có thể trở thành `Place`.

Một Place không nhất thiết có physical address.

---

# 3. Place ≠ memory address

Đây là quyết định cực kỳ quan trọng.

```text
Place
  ≠
Pointer
  ≠
Physical Address
```

Place có thể được compiler biểu diễn thành:

```text
register
SSA value
stack slot
inline aggregate
memory address
GPU register
GPU local memory
```

---

# 4. Place representation

MIR:

```text
Place {
    base: PlaceBase
    projections: [Projection]
}
```

Ví dụ:

```text
person.address.city
```

→

```text
Place {
    base = person
    projections = [
        Field(address),
        Field(city)
    ]
}
```

---

# 5. Place base

Các base hợp lệ:

```text
Local
Static
Argument
Temporary
ReturnSlot
Global
External
```

Raw pointer không tự động trở thành safe Place.

---

# 6. Projection

Projection là phép đi sâu từ một Place:

```text
Field
Index
DerefRaw
Slice
DowncastVariant
TupleField
```

Nhưng mỗi projection có safety contract riêng.

---

# 7. Field projection

```axiom
person.name
```

→

```text
Place(person)
  + Field(name)
```

Compiler biết field type/layout từ TypeDB/LayoutDB.

---

# 8. Nested projection

```axiom
a.b.c.d
```

không tạo bốn object trung gian.

Semantic Place:

```text
a
 └─ b
    └─ c
       └─ d
```

Compiler có thể trực tiếp tính offset hoặc scalarize.

---

# 9. Tuple projection

```axiom
point.0
```

là:

```text
Place(point) + TupleField(0)
```

---

# 10. Array indexing

```axiom
array[i]
```

là:

```text
Place(array)
  + Index(i)
```

`i` là runtime value.

---

# 11. Index safety

Safe indexing:

```axiom
array[i]
```

phải chứng minh:

```text
0 <= i < len(array)
```

hoặc runtime bounds check được chèn.

Optimizer có thể loại bỏ check nếu đã chứng minh range.

---

# 12. Slice

```axiom
array[start:end]
```

không tạo copy mặc định.

Nó tạo:

```text
view<T>
```

nếu context yêu cầu view.

Semantic object:

```text
{
    provenance
    region
    start
    length
    access
}
```

---

# 13. Slice không phải Place thông thường

Một slice/view là **capability** trỏ vào region.

Do đó:

```text
Place
    ↓
MakeView
    ↓
Capability
```

khác:

```text
Place
    ↓
Load
```

---

# 14. Mutable slice

```axiom
mut_view(array[start:end])
```

tạo:

```text
WRITE capability
```

với region:

```text
[start, end)
```

Capability verifier phải đảm bảo exclusive access.

---

# 15. Reading a Place

Khi compiler cần giá trị:

```axiom
let y = x.field
```

semantic operation:

```text
READ Place(x.field)
```

sau đó:

```text
produce Value
```

---

# 16. Load

MIR có thể biểu diễn:

```text
Load(Place)
```

Nhưng Load không nhất thiết tạo machine load.

Compiler có thể giữ value trong SSA/register.

---

# 17. Store

```axiom
x.field = value
```

→

```text
Store(Place(x.field), value)
```

nhưng physical store có thể bị:

```text
eliminated
merged
forwarded
scalarized
```

nếu semantic legality cho phép.

---

# 18. Move

```axiom
let b = a
```

nếu `a` non-Copy:

```text
Move(Place(a))
```

Sau đó:

```text
a = Moved
b = Owned
```

Không bắt buộc physical copy.

---

# 19. Copy

Nếu:

```text
T: Copy
```

thì:

```axiom
let b = a
```

semantic:

```text
Copy(Place(a))
```

`a` vẫn valid.

Physical machine code có thể:

```text
no copy
register reuse
constant propagation
```

---

# 20. Copy ≠ Load

Đây là distinction quan trọng:

```text
Copy
```

là semantic ownership/value operation.

```text
Load
```

là physical/IR access operation.

Một `Copy` không nhất thiết dẫn tới một machine load.

---

# 21. Move ≠ physical memcpy

Tương tự:

```text
Move
```

là ownership transition.

Không có yêu cầu:

```text
memcpy(source, destination)
```

Compiler có thể:

```text
rename SSA value
move register
return via ABI register
caller allocation
```

---

# 22. Assignment

```axiom
x = y
```

nếu `y` Copy:

```text
Copy y
Store x
```

nếu `y` owning non-Copy:

```text
Move y
Store x
```

---

# 23. Assignment overwrite

Nếu `x` đang chứa owning value:

```axiom
x = new_value
```

semantic:

```text
Drop(old x)
Move/Copy(new_value → x)
```

trừ khi compiler có thể prove old value không còn resource/effect.

---

# 24. Drop before overwrite

Ví dụ:

```axiom
let mut file = open(...)
file = open(...)
```

phải tránh leak resource cũ.

Semantic:

```text
old file
   ↓
Drop
   ↓
new file
```

---

# 25. Self-assignment

Không cần C++-style special handling:

```axiom
x = x
```

sẽ được semantic analyzer xử lý theo Copy/Move rules.

Với non-Copy:

```text
Move(x) → x
```

không hợp lệ nếu việc đó tạo use-after-move/invalid state.

Compiler không cần giả định programmer đang viết C++ self-assignment idiom.

---

# 26. Partial move

Ví dụ:

```axiom
struct User {
    name: String
    age: u32
}

let name = user.name
```

Compiler có thể đánh dấu:

```text
user.name = Moved
user.age  = Owned
```

→ `user` là `PartiallyMoved`.

---

# 27. Partial access

Sau đó:

```axiom
print(user.age)
```

hợp lệ.

Nhưng:

```axiom
print(user.name)
```

không hợp lệ.

---

# 28. Partial move + Drop

Nếu User có custom Drop:

```text
Drop(User)
```

thì partial move bị cấm theo frozen ownership rules.

Lý do:

Drop phải luôn nhìn thấy một valid semantic state.

---

# 29. Compiler-derived Drop

Nếu compiler-generated Drop có thể xử lý field state:

```text
user.name = Moved
```

thì compiler có thể generate:

```text
if name_initialized:
    drop(name)

if age_initialized:
    drop(age)
```

---

# 30. Initialization state

Mỗi Place có thể có state:

```text
UNINIT
INIT
MOVED
PARTIAL
DROPPED
```

Verifier theo dõi theo control flow.

---

# 31. Field-sensitive initialization

```axiom
var user: User
user.name = ...
```

không nhất thiết initialize toàn bộ `user`.

Compiler theo dõi:

```text
user.name = INIT
user.age  = UNINIT
```

---

# 32. Partial initialization

Cho phép nếu type/constructor semantics cho phép.

Ví dụ low-level/system code có thể cần:

```axiom
var packet: Packet
packet.header = ...
packet.payload = ...
```

nhưng chỉ được sử dụng `packet` khi required fields đã initialized.

---

# 33. Uninitialized memory

Core không cho đọc uninitialized value.

```text
UNINIT → READ
```

= compile error.

---

# 34. `Uninit<T>`

System/library layer có thể cung cấp:

```text
Uninit<T>
```

nhưng API phải giữ invariant:

```text
UNINIT
    ↓ initialize
INIT<T>
```

Không có implicit conversion.

---

# 35. Address-taking

Surface Core không có:

```text
&x
```

Thay vào đó:

```text
address_of(x)
```

chỉ ở unsafe/system boundary.

---

# 36. Why?

Compiler bình thường không cần programmer nói:

```text
“hãy lấy địa chỉ x”
```

Compiler tự tạo address nếu backend cần.

Address chỉ trở thành semantic observable khi programmer explicitly yêu cầu stable/raw address.

---

# 37. Address-taking changes observability

Ví dụ:

```axiom
let p = unsafe { address_of(x) }
```

giờ physical storage có thể trở thành observable.

Compiler phải bảo vệ:

```text
stable-address requirement
```

cho đến khi pointer contract kết thúc.

---

# 38. Raw pointer dereference

```axiom
unsafe {
    *p
}
```

→ raw pointer projection.

MIR:

```text
DerefRaw(p)
```

đây là unsafe Place construction.

---

# 39. Raw pointer does not gain provenance automatically

```axiom
let n: usize = ...
let p = n as *mut T
```

không tự động tạo safe Place.

Phải có explicit unsafe contract.

---

# 40. Unsafe boundary

Ví dụ:

```axiom
unsafe {
    let p = address_of(x)
    write(p, value)
}
```

unsafe code chịu trách nhiệm establish:

```text
valid address
alignment
initialization
non-overlap if required
lifetime
write permission
```

Sau boundary compiler chỉ tin contract đã explicit established.

---

# 41. Safe capability recovery

Nếu unsafe wrapper tạo:

```text
mut_view<T>
```

thì capability verifier tiếp tục từ:

```text
trusted precondition
```

không trở thành “unchecked mode”.

---

# 42. Place vs Capability

Một Place nói:

> “đây là semantic location.”

Capability nói:

> “được phép làm gì với location này.”

Ví dụ:

```text
Place(person.name)

Capability:
    READ
```

hoặc:

```text
Place(person.name)

Capability:
    WRITE
```

---

# 43. Capability does not equal Place

Một `view<T>` có thể bao phủ nhiều Place:

```text
array[10..20]
```

Capability region:

```text
array[10:20]
```

không cần enumerate từng element.

---

# 44. Region projection

Place:

```text
array[i]
```

region có thể là:

```text
Element(i)
```

Slice:

```text
array[i:j]
```

region:

```text
Range(i,j)
```

---

# 45. Unknown index

Nếu:

```axiom
foo(a[i], a[j])
```

compiler không biết:

```text
i != j
```

thì:

```text
RegionRelation = UNKNOWN
```

không được coi là DISJOINT.

---

# 46. Proven disjoint

Nếu:

```axiom
foo(a[0], a[1])
```

compiler có thể chứng minh:

```text
Element(0)
∩
Element(1)
=
∅
```

→ safe independent access.

---

# 47. Range proof

Nếu:

```axiom
for i in 0..n {
    use(a[i])
}
```

compiler có range facts:

```text
0 <= i < n
```

có thể:

```text
eliminate bounds checks
```

nếu `n <= len(a)` đã được chứng minh.

---

# 48. Place projection and relocation

Đây là điểm rất quan trọng với `Vec`.

```axiom
let p = view(v)
v.push(x)
```

Nếu `push` có thể realloc:

```text
p
```

có thể trở thành dangling.

Do đó verifier:

```text
live view
+
potential relocation
=
reject
```

hoặc `push` phải dùng operation contract chứng minh không relocate.

---

# 49. Reserve

```axiom
v.reserve(100)
```

không tự động tạo stable address contract.

Nó chỉ thay đổi capacity guarantee.

---

# 50. Stable address

Nếu programmer cần:

```text
stable storage
```

phải dùng abstraction có contract rõ ràng:

```text
PinnedStorage
StableBox
Arena
Handle
```

tùy library.

Không biến toàn bộ Axiom thành pointer-centric language.

---

# 51. `view` materialization

```axiom
let v = view(x)
```

semantic:

```text
MakeView {
    provenance = x
    region = region(x)
    access = READ
}
```

Không nhất thiết tạo object vật lý.

---

# 52. `mut_view`

```axiom
let v = mut_view(x)
```

→

```text
MakeMutView {
    provenance = x
    region = region(x)
    access = WRITE
}
```

Capability move-only.

---

# 53. View access

```axiom
v[i]
```

không cần dereference syntax.

Compiler biết:

```text
v
    ↓
READ capability
    ↓
region projection
    ↓
Place-like access
```

---

# 54. View mutation

```axiom
v[i] = x
```

chỉ hợp lệ nếu `v` là:

```text
mut_view<T>
```

và capability region cho phép WRITE.

---

# 55. Nested views

```axiom
let a = view(x)
let b = view(a)
```

có thể collapse semantic provenance:

```text
b → x
```

thay vì tạo chain runtime.

---

# 56. Mutable subview

```axiom
let whole = mut_view(array)
let part = mut_view(whole[0..10])
```

`part` phải lấy capability từ `whole`.

Sau khi `part` tồn tại:

```text
whole WRITE capability
```

không được sử dụng conflict với `part`.

---

# 57. Reborrowing

Axiom không expose thuật ngữ borrow checker cho programmer.

Nhưng compiler có thể nội bộ thực hiện:

```text
mut_view whole
     ↓
temporary sub-capability
     ↓
sub-call
     ↓
restore parent capability
```

Đây là compiler mechanism, không phải source syntax.

---

# 58. Đây là điểm khác biệt lớn của Axiom

Rust:

```text
programmer
    ↓
must understand borrow/lifetime syntax
```

Axiom:

```text
programmer
    ↓
express intent: value/view/mut_view
    ↓
compiler derives capability lifetime
```

Vẫn có safety mạnh, nhưng không bắt programmer viết lifetime graph.

---

# 59. Function parameter

Ví dụ:

```axiom
fn sum(data: view<i32>) -> i32
```

call:

```axiom
sum(array)
```

compiler tự tạo ephemeral view.

Programmer không cần:

```text
&array
```

---

# 60. Mutable parameter

```axiom
fn sort(data: mut_view<i32>)
```

call:

```axiom
sort(array)
```

compiler tạo mutable capability nếu safe.

---

# 61. Owning parameter

```axiom
fn consume(data: Vec<i32>)
```

call:

```axiom
consume(v)
```

→ Move.

---

# 62. Copy parameter

```axiom
fn square(x: i32)
```

→ semantic Copy/value passing.

---

# 63. Parameter intent is type-driven

Axiom tránh:

```text
&
&mut
*
&&
```

bằng:

```text
T
view<T>
mut_view<T>
```

Đây là một trong những điểm làm API dễ đọc hơn.

---

# 64. Return Place

```axiom
fn make() -> User
```

return value có thể được:

```text
register
caller-allocated return slot
NRVO-like direct construction
```

không cần temporary copy.

---

# 65. Return view

```axiom
fn name(user: view<User>) -> view<str>
```

compiler theo dõi provenance:

```text
returned view
    ↓
derived from argument capability
```

và lifetime relation được tự động kiểm tra.

---

# 66. View from temporary

```axiom
get_name(make_user())
```

Nếu `get_name` chỉ sử dụng view trong call:

→ hợp lệ nếu temporary sống đủ lâu.

Nhưng:

```axiom
let x = get_name(make_user())
```

nếu `x` là view và owner đã chết:

→ reject.

---

# 67. Place expressions vs value expressions

Compiler nội bộ phân biệt:

```text
Place expression
Value expression
```

nhưng **không expose lvalue/rvalue terminology bắt buộc cho programmer**.

---

# 68. Place-producing expressions

Ví dụ:

```text
x
x.field
x[i]
view[i]
```

có thể produce Place.

---

# 69. Value-producing expressions

Ví dụ:

```text
x + y
foo()
if ...
match ...
```

produce Value.

---

# 70. Context determines access

```axiom
x.field
```

không nhất thiết lập tức load.

Nếu context:

```axiom
let y = x.field
```

→ Read.

Nếu:

```axiom
x.field = y
```

→ Write destination.

Nếu:

```axiom
consume(x.field)
```

→ Move nếu parameter owning.

---

# 71. This is bidirectional with type inference

Đây là nơi task 241 kết nối với 244:

```text
Expected Type
     ↓
Access Mode
     ↓
Place / Value
     ↓
Ownership Operation
```

Ví dụ function signature:

```axiom
fn consume(x: String)
```

cho compiler biết argument cần:

```text
Move
```

trong khi:

```axiom
fn print(x: view<String>)
```

cần:

```text
READ capability
```

---

# 72. Autoderef không tồn tại

Axiom không cần:

```text
x
*x
**x
```

để truy cập nested ownership.

Semantic model tự resolve Place/Value.

Raw pointer là ngoại lệ system-level.

---

# 73. Auto-addressing

Compiler có thể generate:

```text
address
```

khi ABI/backend yêu cầu.

Programmer không cần biết.

---

# 74. Register promotion

Ví dụ:

```axiom
let p = Point{ x: 1, y: 2 }
let z = p.x + p.y
```

Compiler có thể biến thành:

```text
z = 3
```

không có memory object.

---

# 75. Scalar replacement

```text
Point{x,y}
```

có thể biến thành:

```text
x_register
y_register
```

Place semantics vẫn đúng.

---

# 76. Memory materialization

Chỉ khi cần:

```text
address observable
FFI
volatile
atomic
stable storage
escaping pointer
```

compiler phải materialize memory.

---

# 77. Address-observable boundary

Các operation có thể force materialization:

```text
address_of
raw pointer
FFI pointer
volatile
MMIO
stable storage API
```

---

# 78. Atomic Place

```axiom
atomic.load(x)
```

Place vẫn có provenance/region.

Nhưng access mode:

```text
ATOMIC_READ
```

khác ordinary READ.

---

# 79. Volatile Place

```text
volatile.read(x)
```

→:

```text
VOLATILE_READ
```

không được CSE như ordinary load.

---

# 80. GPU Place

GPU kernel cũng sử dụng Place model.

Ví dụ:

```axiom
out[i] = a[i] + b[i]
```

cùng semantic abstraction.

Backend thêm:

```text
AddressSpace
StorageDomain
ExecutionDomain
```

---

# 81. Device memory

Device pointer/address không được coi là host pointer.

Place chứa:

```text
StorageDomain = Device
```

và GPU legality kiểm tra access.

---

# 82. External memory

Memory từ foreign API:

```text
StorageDomain = External
```

phải có contract về:

```text
lifetime
alignment
size
ownership
access
```

---

# 83. FFI Place

Raw pointer từ C:

```text
*mut T
```

không tự động trở thành:

```text
mut_view<T>
```

Wrapper phải validate/assume contract.

---

# 84. Place identity

Hai Place có thể:

```text
MUST_ALIAS
NO_ALIAS
PARTIAL_ALIAS
MAY_ALIAS
UNKNOWN
```

đúng theo frozen alias model.

---

# 85. Place equality

Không có general runtime:

```text
place1 == place2
```

vì Place là compiler semantic concept.

Nếu cần runtime identity:

```text
pointer
Handle
EntityId
```

được dùng explicit.

---

# 86. Physical address identity

Không được dùng address làm semantic identity trừ khi explicitly requested.

Điều này cho phép:

```text
stack promotion
heap elimination
object relocation
register allocation
```

mạnh hơn.

---

# 87. Handle identity

Ví dụ collection:

```axiom
let id = entities.create(...)
```

`id` là logical identity.

Collection có thể relocate physical storage mà `id` vẫn hợp lệ theo generation/version contract.

---

# 88. Place invalidation

Operation có thể invalidate Place/capability nếu:

```text
relocation
deallocation
destruction
external mutation
```

Compiler tracks operation contract.

---

# 89. `Vec` example

```axiom
let mut v = Vec<i32>()
let p = view(v)

v.push(10)
```

Nếu `p` còn live:

```text
push
→ potential relocation
→ conflict
```

Compiler reject hoặc yêu cầu capability hết live trước operation.

---

# 90. Scope shortening

Compiler có thể thấy:

```axiom
let p = view(v)
use(p)
v.push(10)
```

và tự động kết luận:

```text
p lifetime ends after use(p)
```

Không cần programmer viết:

```text
drop(p)
```

trong trường hợp không cần.

---

# 91. Explicit `drop(view)`

Nếu cần force capability end:

```axiom
drop(p)
```

sau đó:

```axiom
v.push(10)
```

hợp lệ.

---

# 92. This is not GC

Scope shortening không phải garbage collection.

Compiler chỉ xác định:

```text
capability no longer used
```

và kết thúc semantic lifetime.

Không có tracing runtime.

---

# 93. Ownership and Place tree

Verifier duy trì:

```text
user
├── name
├── age
└── address
    ├── city
    └── zip
```

Mỗi node có state.

Điều này cho phép:

```text
partial move
partial initialization
field-level aliasing
field-level drop
```

---

# 94. Place tree + capabilities

Ví dụ:

```axiom
fn update(x: mut_view<User>) {
    x.age = 20
}
```

capability:

```text
User region
WRITE
```

write:

```text
User.age
```

được phép.

---

# 95. Disjoint field mutation

```axiom
foo(mut_view(user.name))
bar(mut_view(user.age))
```

có thể đồng thời hợp lệ nếu compiler chứng minh:

```text
name ∩ age = ∅
```

Đây là nền tảng cho parallelization sau này.

---

# 96. Automatic parallelization

Compiler có thể phát hiện:

```text
for i in ...
    out[i] = a[i] + b[i]
```

nếu:

```text
iterations independent
```

thì vectorize/parallelize.

Không cần programmer viết pointer alias annotations.

---

# 97. Internal `NoAlias`

Capability proof:

```text
DISJOINT
```

→ optimizer:

```text
NO_ALIAS
```

Đây là cách Axiom đạt lợi thế so với C mà không yêu cầu programmer viết `restrict`.

---

# 98. Unknown means conservative

Nếu compiler không chứng minh:

```text
i != j
```

thì:

```text
UNKNOWN
```

không được biến thành:

```text
NO_ALIAS
```

Compiler chọn:

```text
runtime check
hoặc
không tối ưu
hoặc
reject nếu safety-critical
```

tùy context.

---

# 99. Place lowering pipeline

```text
Typed HIR
   ↓
Place Construction
   ↓
Place Normalization
   ↓
Ownership Access Classification
   ↓
Capability Derivation
   ↓
Load/Store/Move/Copy
   ↓
MIR
```

---

# 100. Place normalization

Ví dụ:

```axiom
x.a.b[i].c
```

normalize:

```text
Base(x)
→ Field(a)
→ Field(b)
→ Index(i)
→ Field(c)
```

Mỗi projection mang type/region metadata.

---

# 101. Projection legality

Mỗi projection phải kiểm tra:

```text
type
initialization
ownership
capability
bounds
provenance
storage domain
execution domain
unsafe contract
```

---

# 102. No hidden pointer semantics

Một compiler implementation có thể internally represent:

```text
Place
```

bằng pointer/address.

Nhưng đó là implementation detail.

Language semantics chỉ nói:

```text
Place + access capability
```

---

# 103. No hidden alias promise

Compiler cũng không được mặc định:

```text
different source expressions = different memory
```

Alias phải được chứng minh.

---

# 104. Place and optimization independence

Optimization có thể biến:

```text
Place(x.field)
```

thành:

```text
SSA value
```

nhưng semantic identity remains.

---

# 105. Debugging

Debugger phải có thể map:

```text
source variable
↓
Place
↓
MIR local/SSA
↓
machine location
```

Nếu optimized away:

```text
“optimized out”
```

thay vì tạo giá trị giả.

---

# 106. `volatile` debugging

Volatile accesses phải giữ semantic source mapping chính xác hơn ordinary eliminated loads.

---

# 107. ABI lowering

Place semantics kết thúc trước physical ABI.

Ví dụ:

```axiom
fn foo(p: Point)
```

có thể ABI-lower thành:

```text
x in register
y in register
```

hoặc stack.

Programmer không cần biết.

---

# 108. Return slot

Large struct:

```axiom
fn create() -> Large
```

ABI có thể:

```text
caller allocates return slot
callee writes directly
```

Semantic vẫn là:

```text
return Large
```

không có intermediate copy.

---

# 109. In-place construction

Compiler có thể lower:

```axiom
let x = make()
```

thành:

```text
construct directly in final destination
```

nếu semantics cho phép.

---

# 110. Move optimization

```axiom
let a = make()
return a
```

có thể:

```text
construct directly in return slot
```

không cần physical Move.

---

# 111. Copy elision

```axiom
let x = make_copyable()
```

không bắt buộc physical copy nếu value chưa observable dưới dạng distinct storage identity.

---

# 112. Storage identity exception

Nếu programmer explicit yêu cầu:

```text
stable storage
address
FFI pointer
```

thì physical storage trở thành observable.

Compiler phải preserve.

---

# 113. Place and concurrency

Concurrent access kiểm tra trên Place regions.

Ví dụ:

```text
Thread A → WRITE a[0]
Thread B → WRITE a[1]
```

disjoint → có thể hợp lệ.

```text
Thread A → WRITE a[i]
Thread B → WRITE a[j]
```

unknown overlap → synchronization hoặc proof cần thiết.

---

# 114. Place and async

Một view sống qua:

```axiom
await
```

phải được kiểm tra theo async rules.

Nếu underlying storage có thể relocate hoặc execution context thay đổi:

→ reject nếu contract không cho phép.

---

# 115. Place and GPU launch

Device view passed to:

```axiom
launch(kernel, view)
```

capability lifetime phải kéo dài tới completion event.

Compiler không cho:

```text
destroy buffer
```

trước khi GPU operation complete.

---

# 116. Place and FFI

Foreign call:

```text
foo(pointer_to(x))
```

có thể làm storage escape.

Compiler phải đánh dấu:

```text
ExternalEscape
```

nếu contract không chứng minh pointer chỉ dùng trong call.

---

# 117. FFI contract can narrow escape

Nếu:

```text
@ffi(noescape)
```

hoặc tương đương được contract chính thức quy định:

```text
pointer only valid during call
```

thì compiler có thể giữ stack allocation.

Nhưng đây là ABI contract, không phải assumption.

---

# 118. Place and `@noalias`

Không cần source-level `restrict`.

Nếu FFI/API yêu cầu noalias:

```text
@noalias
```

chỉ là explicit external contract.

Safe internal Axiom code vẫn dựa vào proof.

---

# 119. Semantic vs physical memory

Axiom chính thức có ba tầng:

```text
Semantic Place
      ↓
Abstract Storage
      ↓
Physical Address/Registers
```

Điều này rất phù hợp với mục tiêu:

```text
high-level simplicity
+
systems-level control
+
aggressive optimization
```

---

# 120. Core invariants — FROZEN

```text
APLACE-20
A Place is a semantic location, not necessarily a physical memory address.

APLACE-21
Place semantics are independent of physical storage representation.

APLACE-22
A Place may be represented by a register, stack slot, inline storage, memory address, or target-specific storage.

APLACE-23
Axiom does not expose C/C++ lvalue/rvalue categories as required source concepts.

APLACE-24
The compiler internally distinguishes Place-producing and Value-producing expressions.

APLACE-25
A Place consists of a base and zero or more projections.

APLACE-26
Field access is represented as Field projection.

APLACE-27
Tuple access is represented as TupleField projection.

APLACE-28
Index access is represented as Index projection.

APLACE-29
Slice access produces a capability/view according to context.

APLACE-30
Raw pointer dereference is an unsafe projection.

APLACE-31
A raw pointer does not automatically become a safe Place.

APLACE-32
Integer-to-pointer conversion does not establish safe pointer provenance.

APLACE-33
Safe Place access requires valid ownership/capability state.

APLACE-34
Reading a Place requires a valid READ capability or owning value access.

APLACE-35
Writing a Place requires a valid WRITE capability.

APLACE-36
Moving from a Place consumes ownership of the selected value.

APLACE-37
Copying from a Place requires the selected type to satisfy Copy semantics.

APLACE-38
Move is a semantic ownership transition and does not imply physical copying.

APLACE-39
Copy is a semantic value duplication and does not imply physical copying.

APLACE-40
Load is a physical/IR access concept and is distinct from semantic Copy.

APLACE-41
Store is a physical/IR access concept and is distinct from semantic ownership assignment.

APLACE-42
Assignment of an owning value transfers ownership into the destination.

APLACE-43
Overwriting an owning destination performs required destruction of the previous value.

APLACE-44
Uninitialized Places cannot be read in safe code.

APLACE-45
Initialization state is tracked at Place granularity.

APLACE-46
Partial initialization is supported where type semantics permit it.

APLACE-47
Partial moves are field-sensitive where Drop semantics permit them.

APLACE-48
Custom destructive Drop forbids unsafe partial-move states.

APLACE-49
Moved Places cannot be read or moved again without valid reinitialization.

APLACE-50
Dropped Places cannot be accessed as initialized values.

APLACE-51
Place projections preserve type information.

APLACE-52
Place projections preserve ownership and capability provenance.

APLACE-53
Array indexing is bounds-safe in safe code.

APLACE-54
Bounds checks may be eliminated only when proven unnecessary.

APLACE-55
Unknown index relationships are not assumed disjoint.

APLACE-56
Proven disjoint regions may be independently accessed.

APLACE-57
Capability regions provide alias-analysis facts.

APLACE-58
UNKNOWN alias relations never become NO_ALIAS without proof.

APLACE-59
A safe mutable capability cannot coexist with conflicting safe access.

APLACE-60
A view is a non-owning capability derived from a valid provenance.

APLACE-61
A mutable view is an exclusive write capability.

APLACE-62
View lifetime cannot exceed its provenance lifetime.

APLACE-63
View construction does not imply heap allocation.

APLACE-64
Nested views may be normalized to their original provenance.

APLACE-65
Compiler-internal reborrowing does not require programmer-written lifetime syntax.

APLACE-66
Implicit owner-to-view conversion is allowed only for non-escaping expected-view contexts.

APLACE-67
Stored or escaping views require explicit capability semantics.

APLACE-68
A live view may block operations that can invalidate its storage.

APLACE-69
Potential relocation conflicts with live dependent views unless stability is proven.

APLACE-70
Reserve/capacity guarantees do not by themselves establish permanent stable addresses.

APLACE-71
Stable address is an explicit storage contract.

APLACE-72
Taking a raw address is an explicit unsafe/system operation.

APLACE-73
Address observation may make physical storage identity observable.

APLACE-74
When storage identity becomes observable, relocation is prohibited until the contract ends.

APLACE-75
Compiler-generated addresses for ABI/backend purposes do not expose storage identity.

APLACE-76
Semantic Place identity is distinct from physical address identity.

APLACE-77
Logical handles may represent identity without exposing physical storage.

APLACE-78
Place access may be scalarized or promoted to registers.

APLACE-79
Place materialization occurs only when required by semantics or target constraints.

APLACE-80
FFI pointer access requires an explicit foreign-memory contract.

APLACE-81
Foreign pointers do not implicitly become safe owners.

APLACE-82
Unsafe code may establish trusted Place preconditions only through explicit contracts.

APLACE-83
Safe verification resumes after an unsafe boundary.

APLACE-84
Atomic Place access follows atomic semantics.

APLACE-85
Volatile Place access follows volatile semantics.

APLACE-86
GPU Places carry storage and execution-domain constraints.

APLACE-87
Device Places are not implicitly host Places.

APLACE-88
External Places require explicit lifetime and access contracts.

APLACE-89
Place semantics participate in concurrency race analysis.

APLACE-90
Place semantics participate in async suspension analysis.

APLACE-91
Place semantics participate in GPU completion/lifetime analysis.

APLACE-92
Place semantics participate in FFI escape analysis.

APLACE-93
Place semantics participate in allocation and relocation analysis.

APLACE-94
Semantic Place representation is independent of optimization level.

APLACE-95
Physical load/store generation is an implementation decision after semantic verification.

APLACE-96
ABI lowering may replace aggregates with registers or caller-allocated storage.

APLACE-97
Move and Copy operations may be eliminated physically when semantic identity permits.

APLACE-98
Observable storage identity prevents transformations that would change the specified identity.

APLACE-99
Debug information maps source Places to MIR and machine locations where possible.

APLACE-100
No compiler optimization may violate Place ownership, capability, initialization, provenance, or observable storage semantics.
```

---

# 121. Kiến trúc sau BOOTSTRAP-244

Axiom hiện có một chuỗi rất rõ:

```text
             SOURCE
               │
               ▼
        Expression Semantics
               │
               ▼
          Typed HIR
               │
               ▼
          PLACE MODEL
        ┌──────┼──────┐
        ▼      ▼      ▼
     Value   Move    Capability
        │      │      │
        └──────┼──────┘
               ▼
              MIR
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
 Ownership   Alias    Effects
       │       │        │
       └───────┼────────┘
               ▼
           Verified MIR
               │
               ▼
             OptIR
               │
               ▼
          Physical Code
```

Điểm quan trọng nhất là:

> **Axiom không bỏ pointer/reference vì “memory không tồn tại”; Axiom bỏ chúng khỏi mô hình lập trình thông thường vì compiler đã có một abstraction tốt hơn: Place + Capability + Ownership.**

Programmer vẫn có thể xuống đến:

```text
raw pointer
address
volatile
MMIO
FFI
custom allocator
stable storage
```

nhưng đó là **system-level intent**, không phải cách code thông thường.

---

## TASK TIẾP THEO

### **BOOTSTRAP-245 — AXIOM PATTERN MATCHING, DESTRUCTURING & EXHAUSTIVENESS ENGINE**

Task tiếp theo sẽ hoàn thiện một mảnh rất quan trọng của type/value system:

```text
match
pattern
destructuring
enum
struct
tuple
array
Option
Result
guards
or-pattern
range-pattern
binding
move/copy semantics
partial move
refutable/irrefutable pattern
exhaustiveness
unreachable patterns
```

Đặc biệt sẽ phải giải quyết một vấn đề sâu:

```text
match user {
    User { name, age } => ...
}
```

khi `name: String` là owning non-Copy:

**pattern binding là Move, Copy, View hay chỉ là field access?**

Và compiler phải kết hợp **pattern engine + Place tree + ownership verifier** để bảo đảm pattern destructuring không tạo ra hidden copy hoặc dangling capability.