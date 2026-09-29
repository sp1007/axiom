# AXIOM LANGUAGE SPECIFICATION v0.1 — Part III
## Ownership · Capability · Move · Copy · View · Mut View · Drop · Lifetime

Đây là phần lõi của memory model. Mục tiêu là:

> **Programmer quản lý ownership ở mức ý nghĩa; compiler quản lý lifetime, aliasing và physical storage.**

Axiom không yêu cầu programmer viết lifetime annotation, borrow annotation hay pointer bookkeeping trong safe code.

---

# 1. Ownership model

Mỗi runtime value thuộc một trong hai nhóm:

```text
OWNING VALUE
NON-OWNING CAPABILITY
```

Owning value chịu trách nhiệm semantic resource lifetime.

Capability chỉ cho phép truy cập một vùng dữ liệu đang thuộc ownership khác.

---

# 2. Ownership uniqueness

Tại mỗi thời điểm, một resource/value có:

```text
0 hoặc 1 owning authority
```

Trong safe code không tồn tại:

```text
2 independent owners
```

cho cùng một resource identity.

Nếu muốn shared ownership phải dùng abstraction explicit:

```text
Rc<T>
Arc<T>
Shared<T>
```

hoặc abstraction tương đương.

---

# 3. Value semantics

Ordinary variables có value semantics:

```axiom
let a = ...
let b = a
```

sẽ là một trong:

```text
Copy
Move
```

tùy semantic properties của type.

Không có implicit shared alias.

---

# 4. Copy

Type `T: Copy` cho phép duplicate semantic value.

Ví dụ:

```axiom
let a: i32 = 10
let b = a
```

Sau đó cả:

```text
a
b
```

đều hợp lệ.

---

# 5. Copy không đồng nghĩa memcpy

Compiler có thể thực hiện:

```text
register duplication
constant propagation
SSA value duplication
scalar replacement
```

thay vì memory copy.

Do đó:

> `Copy` là semantic property, không phải machine instruction.

---

# 6. Move

Type không Copy:

```axiom
let a = buffer
let b = a
```

thực hiện Move.

Semantic state:

```text
a: MOVED
b: OWNED
```

`a` không còn usable.

---

# 7. Move không yêu cầu physical copy

Compiler có thể:

```text
rename SSA value
change owner metadata
forward register
reuse stack slot
```

mà không copy memory.

Invariant:

### AOWN-20
**Move is an ownership-state transition, not a required physical copy.**

---

# 8. Use-after-move

Ví dụ:

```axiom
let a = make_buffer()
let b = a

use(a)
```

→ compile error.

Diagnostic:

```text
AX_MOVE_0001
value used after move
```

Compiler SHOULD chỉ ra:

```text
move site
use site
original declaration
```

---

# 9. Copy và Move trong function call

```axiom
fn consume(x: Buffer)
```

gọi:

```axiom
consume(buffer)
```

→ Move.

Trong khi:

```axiom
fn inspect(x: view<Buffer>)
```

gọi:

```axiom
inspect(buffer)
```

→ tạo ephemeral read capability.

---

# 10. Return ownership

```axiom
fn create() -> Buffer {
    let x = make()
    x
}
```

`x` được transfer ownership cho caller.

Không tạo implicit clone.

### AOWN-31
**Returning an owned value transfers its semantic ownership.**

---

# 11. Returning Copy

Nếu:

```text
T: Copy
```

return value là semantic duplication.

Compiler vẫn có thể thực hiện return bằng register.

---

# 12. Explicit Clone

Nếu cần duplicate non-Copy resource:

```axiom
let b = a.clone()
```

Clone có thể:

```text
allocate
copy
transform
share
fail
```

tùy contract của type/API.

---

# 13. Partial move

Struct:

```axiom
struct User {
    id: u64
    name: String
}
```

Nếu:

```axiom
let name = user.name
```

và `String` không Copy:

```text
user.name → MOVED
user.id   → still owned
```

Do đó `user` trở thành:

```text
PARTIAL
```

---

# 14. Partial move usability

Sau:

```axiom
let name = user.name
```

có thể:

```axiom
use(user.id)
```

nhưng không thể:

```axiom
use(user.name)
```

và không thể sử dụng toàn bộ:

```axiom
use(user)
```

nếu operation yêu cầu full ownership.

---

# 15. Reinitialization

Partial-moved field có thể được reinitialized:

```axiom
user.name = make_string()
```

sau đó:

```text
user
```

có thể trở lại:

```text
OWNED
```

nếu mọi required fields đều valid.

---

# 16. Arrays và partial move

Array cũng hỗ trợ element-level ownership tracking.

```axiom
let x = items[3]
```

Nếu `items[3]` là non-Copy owned value:

```text
items[3] → MOVED
```

Các phần tử khác vẫn owned.

Compiler có thể dùng bitset/region tracking thay vì metadata runtime.

---

# 17. Tuple partial move

```axiom
let x = tuple.0
```

có thể move element `.0`.

`.1`, `.2` vẫn độc lập nếu type system chứng minh được.

---

# 18. Pattern move

Ví dụ:

```axiom
match message {
    Message.Text(text) => use(text)
    Message.Quit => ...
}
```

`text` được move khỏi owned `message` nếu pattern semantics yêu cầu ownership extraction.

Sau đó source variant được đánh dấu partial/moved tương ứng.

---

# 19. Pattern trên view

Nếu:

```axiom
let m = view(message)
```

thì:

```axiom
match m {
    ...
}
```

không được move payload.

Pattern chỉ tạo capabilities.

Đây là rule quan trọng:

### ACAP-31
**Pattern matching through a non-owning capability cannot transfer ownership.**

---

# 20. Custom Drop và partial move

Đây là một điểm cần chốt rõ.

Nếu type có user-defined Drop:

```axiom
impl Drop for User {
    ...
}
```

thì:

```text
partial move
```

bị cấm.

Ví dụ:

```axiom
let x = user.name
```

nếu `User` có custom Drop:

→ compile error nếu operation yêu cầu partial move.

Lý do: compiler không thể tự động giả định custom destructor có semantics độc lập với toàn bộ object.

---

# 21. Derived Drop

Nếu Drop được compiler derive/generated:

```text
User
 ├── id
 └── name
```

compiler biết chính xác destruction graph.

Do đó partial move được phép.

### ADROP-22
**Compiler-derived Drop may support partial move.**

---

# 22. Custom Drop rule

### ADROP-23
**A user-defined/custom Drop implementation forbids partial move of the containing value in v0.1.**

Điều này làm semantics rất dễ đoán.

---

# 23. Drop và Copy

Một type có semantic Drop obligation:

```text
MUST NOT implement Copy
```

### ADROP-24
**A Drop-bearing type is not Copyable.**

Không cho phép:

```text
Copy
+
double resource cleanup
```

---

# 24. Drop order

Trong scope:

```axiom
let a = A()
let b = B()
let c = C()
```

mặc định destruction order:

```text
c
b
a
```

tức:

> reverse successful initialization order.

---

# 25. Dependency-aware Drop

Nếu compiler có ownership dependency:

```text
b depends on a
```

thì `a` không được drop trước khi `b` hết semantic dependency.

Do đó Drop order thực tế là:

```text
reverse initialization
subject to ownership dependency constraints
```

Compiler có thể reorder independent drops nếu observable semantics được bảo toàn.

---

# 26. Early return

```axiom
fn foo() -> Result<T, E> {
    let a = A()
    let b = B()

    if fail {
        return Err(...)
    }

    ...
}
```

Khi `return`:

```text
b.Drop
a.Drop
return
```

---

# 27. `?` cleanup

```axiom
let a = acquire()?
let b = acquire2()?
```

Nếu second call trả `Err`:

```text
b chưa tồn tại
a.Drop
return Err
```

Deterministic.

---

# 28. Panic cleanup

Nếu panic strategy là `unwind`:

```text
panic
→ unwind
→ Drop owned resources
→ boundary
```

Nếu:

```text
panic = abort
```

thì process có thể terminate mà không thực hiện full language-level unwinding.

Đây là profile semantic choice.

---

# 29. Drop không fallible

`Drop` không trả `Result`.

Không được:

```axiom
impl Drop for File {
    fn drop(...) -> Result<(), Error>
}
```

Nếu cleanup có thể thất bại:

```axiom
file.close()?
```

phải được gọi explicit trước destruction.

---

# 30. Explicit `drop(x)`

```axiom
drop(file)
```

kết thúc ownership lifetime của `file`.

Compiler phải đảm bảo không còn live dependent capability.

Ví dụ:

```axiom
let v = view(file)
drop(file)
use(v)
```

→ compile error tại `drop(file)` hoặc capability creation/use theo diagnostic strategy.

---

# 31. Drop không nhất thiết deallocate

Ví dụ:

```text
Arena<T>
```

drop object có thể chỉ:

```text
resource state cleanup
```

Arena memory vẫn còn cho tới khi Arena drop.

Do đó:

> **Resource lifetime ≠ memory allocation lifetime.**

---

# 32. Capability model

Axiom định nghĩa hai source-level capability types:

```text
view<T>
mut_view<T>
```

---

# 33. `view<T>`

`view<T>` là:

```text
non-owning
read-only
typed capability
```

đến một valid region.

Nó không sở hữu memory.

---

# 34. `mut_view<T>`

`mut_view<T>` là:

```text
non-owning
exclusive-write
typed capability
```

đến region.

Tại cùng thời điểm, region không được có conflicting read/write capability.

---

# 35. `view` có thể duplicate

```axiom
let a = view(x)
let b = a
```

có thể tạo hai read capabilities.

Nhưng đây **không phải `Copy` trait**.

### ACAP-30
**Capability duplication is not value Copy.**

Đây là một semantic property intrinsic của `view`.

---

# 36. `mut_view` không duplicate

```axiom
let a = mut_view(x)
let b = a
use(a)
```

→ `a` đã bị move vào `b`.

`mut_view<T>` là non-duplicable capability.

---

# 37. Capability provenance

Mỗi capability conceptually có:

```text
Owner
Region
Access mode
Validity
```

Ví dụ:

```text
owner = user
region = user.name
access = READ
```

Compiler theo dõi các thông tin này trong verification phase.

---

# 38. Capability region

Region có thể là:

```text
single value
array
subarray
field
nested field
external buffer
device memory
```

Do đó `view<T>` không bị giới hạn semantic vào "slice".

---

# 39. View representation

Compiler MAY represent:

```text
view<T>
```

bằng:

```text
pointer
+
length/metadata
```

hoặc representation khác.

Đây không phải stable language-level representation trừ khi ABI contract yêu cầu.

---

# 40. View của single value

```axiom
let v = view(user)
```

có thể conceptually:

```text
region = entire User object
```

không nhất thiết là sequence.

---

# 41. View field projection

```axiom
let v = view(user)
let name = v.name
```

`name` là capability derived từ:

```text
region(user.name)
```

Không tạo ownership mới.

---

# 42. View → owned value

Không được:

```text
view<T> → T
```

bằng implicit conversion.

Chỉ có thể tạo owned value nếu:

```text
T: Copy
```

hoặc explicit:

```text
clone
```

---

# 43. View lifetime

Capability lifetime là **semantic last-use interval**, không nhất thiết lexical scope.

Ví dụ:

```axiom
let v = view(user)
print(v)
do_something()
```

Nếu `v` không còn được sử dụng sau `print(v)`, compiler có thể kết thúc capability lifetime tại đó.

---

# 44. Owner destruction constraint

Owner không được destroy khi dependent capability còn live.

Ví dụ:

```axiom
let v = view(user)
drop(user)
```

→ reject nếu `v` còn live.

Nếu:

```axiom
let v = view(user)
print(v)
drop(user)
```

→ hợp lệ vì capability đã hết semantic lifetime.

---

# 45. View không tự kéo dài owner

Capability không làm owner sống lâu hơn.

Ví dụ:

```text
view
```

không phải reference-count.

Owner vẫn quyết định resource lifetime.

---

# 46. Unknown aliasing

Nếu compiler không biết:

```text
region A
region B
```

có overlap hay không:

```text
UNKNOWN
```

safe code không được giả định chúng disjoint.

Ví dụ:

```axiom
mutate(a)
mutate(b)
```

nếu provenance không đủ chứng minh disjoint:

→ reject hoặc yêu cầu API abstraction có contract rõ ràng.

---

# 47. Region relations

Compiler sử dụng semantic relation:

```text
DISJOINT
SAME
CONTAINS
OVERLAPS
CONTAINED_BY
UNKNOWN
```

Ví dụ:

```text
user.name
user.age
```

→ DISJOINT.

```text
user
user.name
```

→ CONTAINS.

---

# 48. Read/read

Cho phép:

```text
view A
view B
```

nếu cả hai chỉ READ.

Ngay cả khi:

```text
A == B
```

vẫn hợp lệ.

---

# 49. Read/write

Không cho:

```text
view<T> A
mut_view<T> B
```

nếu:

```text
A overlaps B
```

và cả hai cùng live.

---

# 50. Write/write

Không cho:

```text
mut_view<T> A
mut_view<T> B
```

nếu regions có thể overlap.

---

# 51. Disjoint mutable access

Cho phép:

```axiom
let a = mut_view(user.name)
let b = mut_view(user.age)
```

nếu compiler chứng minh:

```text
name ∩ age = ∅
```

Điểm này cho phép compiler đạt mức an toàn gần borrow checker nhưng syntax đơn giản hơn rất nhiều.

---

# 52. Owner + capability

Nếu:

```text
v = view(user)
```

thì owner `user` vẫn tồn tại.

Nhưng owner không được:

```text
mutate user
drop user
move user
```

theo cách conflict với capability.

Read-only operations có thể vẫn được phép nếu semantics chỉ READ.

---

# 53. Mutable owner access

Ví dụ:

```axiom
let v = view(user)
user.age = 20
```

nếu `v` còn live và `age` nằm trong region của `v`:

→ reject.

Nếu `v` chỉ view một field khác:

```text
v = view(user.name)
user.age = 20
```

→ có thể hợp lệ.

---

# 54. Compiler không cần borrow syntax

Programmer không viết:

```text
&user
&mut user
'a
'a mut
```

Thay vào đó:

```axiom
view(user)
mut_view(user)
```

chỉ xuất hiện khi capability cần được lưu/đặt tên.

Call parameters tự động tạo ephemeral capability.

---

# 55. Ownership vs capability

Đây là phân biệt trung tâm:

```text
OWNERSHIP
    "Ai chịu trách nhiệm resource?"

CAPABILITY
    "Ai được phép truy cập resource lúc này?"
```

Một object có thể:

```text
1 owner
0..N read capabilities
0..1 exclusive write capability
```

---

# 56. Shared ownership

Nếu cần:

```text
multiple owners
```

phải explicit:

```text
Arc<T>
Rc<T>
Shared<T>
```

Shared ownership không được compiler âm thầm biến một ordinary `T` thành reference-counted object.

---

# 57. `Arc<T>` và capability

Ví dụ:

```axiom
let a: Arc<Data> = ...
let b = a.clone()
```

Hai owner logical references có thể tồn tại.

Nhưng access mutable vẫn phải qua synchronization abstraction.

`Arc<T>` không tự biến `T` thành mutable-safe.

---

# 58. Raw pointer

```text
*const T
*mut T
```

không phải capability an toàn.

Raw pointer có thể:

```text
null
dangling
misaligned
invalid
alias
```

và chỉ được thao tác ở unsafe/system boundary.

---

# 59. Unsafe → capability

Unsafe code có thể validate một pointer rồi tạo:

```text
view<T>
mut_view<T>
```

Ví dụ conceptual:

```axiom
unsafe {
    let v = from_raw_parts(ptr, len)
    use(v)
}
```

Sau khi capability được tạo, compiler lại theo dõi:

```text
provenance
region
access
lifetime
```

---

# 60. Unsafe không tắt verifier

Đây là rule cực kỳ quan trọng:

> `unsafe` chỉ suppress **specific proof obligations** mà programmer nhận trách nhiệm; nó không biến toàn bộ code còn lại thành unchecked mode.

Ví dụ unsafe pointer conversion có thể bypass:

```text
"compiler cannot prove pointer validity"
```

nhưng không bypass:

```text
type checking
name resolution
ABI validity
control-flow correctness
```

---

# 61. Storage strategy

Type semantics không quyết định:

```text
stack
heap
register
arena
pool
static
```

Compiler tự chọn nếu address/storage identity không observable.

---

# 62. Allocation elimination

Ví dụ:

```axiom
fn make() -> Point {
    Point { x: 1, y: 2 }
}
```

không được hiểu là:

```text
allocate Point
copy Point
return pointer
```

Nếu return-by-value phù hợp, compiler có thể:

```text
return registers
caller-allocated storage
SSA scalar
```

---

# 63. `Box<T>`

`Box<T>` là library type biểu diễn:

```text
owning dynamic storage
```

Nó có stable storage identity khi contract yêu cầu.

Nhưng compiler vẫn có thể eliminate allocation nếu address/storage identity không observable.

---

# 64. Stable address

Địa chỉ ổn định chỉ tồn tại khi storage contract yêu cầu.

### AMEM-61
**Stable address exists only when the storage contract requires it.**

Ví dụ:

```text
Box<T>
```

có thể yêu cầu stable address sau khi address được expose.

Trong khi:

```text
temporary value
```

không có stable-address guarantee.

---

# 65. Relocatable storage

Collections như `Vec<T>` có thể relocate storage.

Ví dụ:

```axiom
let mut v = Vec(...)
v.push(x)
```

`push` có thể reallocate.

Do đó view đang phụ thuộc vào vùng có khả năng relocate phải block operation hoặc kết thúc trước relocation.

---

# 66. View blocks invalid relocation

Nếu:

```axiom
let v = view(vec)
```

vẫn live:

```axiom
vec.push(x)
```

nếu operation có thể relocate region:

→ compiler phải:

```text
reject
```

hoặc API phải có semantic guarantee không relocate.

---

# 67. Reserve

```axiom
vec.reserve(n)
```

chỉ guarantee capacity theo collection contract.

Không mặc định guarantee:

```text
stable address forever
```

### AMEM-23
**Reserve does not imply stable address.**

---

# 68. Arena

Arena:

```text
owns allocations
```

Object trong arena không được escape vượt arena lifetime.

Ví dụ:

```axiom
fn bad() -> view<Node> {
    let arena = Arena()
    let node = arena.alloc(Node(...))
    view(node)
}
```

→ reject.

---

# 69. Pool / slab

Pool/slab là library storage abstractions.

Pool có thể cung cấp:

```text
stable reusable slots
```

nhưng đây là **storage contract**, không phải property của tất cả object.

---

# 70. Handle

Khi programmer cần identity ổn định nhưng không cần memory address:

```text
Handle<T>
```

là abstraction ưu tiên.

Ví dụ graph:

```text
Node
 ├─ Handle<Node>
 ├─ Handle<Node>
```

thay vì:

```text
raw pointer
```

---

# 71. Generation handle

Pool có thể dùng:

```text
(index, generation)
```

để phát hiện stale handles.

Ví dụ:

```text
Handle(42, generation=7)
```

sau khi slot recycled:

```text
generation=8
```

old handle không còn valid.

---

# 72. Logical identity

Axiom phân biệt:

```text
Value Identity
Storage Identity
Logical Identity
```

### Value identity

Do:

```text
Copy / Move
```

### Storage identity

Do:

```text
Box / Arena / Pool / Static
```

### Logical identity

Do:

```text
Handle / EntityId / generation handle
```

Không được đánh đồng ba khái niệm.

---

# 73. Lifetime

Axiom không expose lifetime syntax.

Compiler nội bộ vẫn tính:

```text
creation
last use
dependencies
drop point
capability interval
storage lifetime
```

---

# 74. Lifetime ≠ scope

Scope:

```text
source-level lexical structure
```

Lifetime:

```text
semantic validity interval
```

Ví dụ:

```axiom
{
    let x = resource()
    use(x)
    compute()
}
```

`x` có thể semantic-drop ngay sau `use(x)` nếu không còn observable reason phải giữ tới `}`.

---

# 75. Nhưng compiler không được tùy tiện Drop sớm

Nếu:

```text
Drop(x)
```

có observable side effect:

```text
file close
lock release
GPU resource release
FFI cleanup
```

thì compiler chỉ được shorten lifetime nếu observable semantics vẫn tương đương.

---

# 76. Lifetime proof

Compiler verifier phải chứng minh:

```text
Every capability use
    occurs while owner/storage is valid.
```

và:

```text
Every owner drop
    occurs only after dependent capabilities end.
```

---

# 77. Ownership state machine

MIR verifier có thể mô hình hóa:

```text
UNINIT
  │
  ▼
OWNED
  │
  ├──── Copy ────► OWNED + OWNED
  │
  ├──── Move ────► MOVED
  │
  ├──── partial ─► PARTIAL
  │
  └──── Drop ────► DROPPED
```

Partial:

```text
PARTIAL
  │
  ├── move remaining field
  ├── reinitialize field
  │
  └── restore all fields → OWNED
```

---

# 78. Capability state machine

```text
OWNER
 │
 ├── view ─────► READ CAPABILITY
 │                  │
 │                  └── duplicate READ
 │
 └── mut_view ─► WRITE CAPABILITY
                    │
                    └── move only
```

Capability không chuyển thành ownership.

---

# 79. Capability end

Capability kết thúc khi:

```text
semantic last use
```

hoặc explicit scope boundary.

Compiler MAY shorten lifetime.

---

# 80. Ownership verifier và optimizer

Ownership verifier chạy **trước semantic optimization**.

Sau khi verification hoàn tất:

```text
ownership facts
capability facts
alias facts
lifetime facts
```

được chuyển thành optimization facts.

Sau đó compiler có thể erase chúng khỏi release binary.

---

# 81. Memory model invariants

### AMEM-62
Ordinary values do not imply heap allocation.

### AMEM-63
Ownership does not imply physical storage location.

### AMEM-64
Capability does not transfer ownership.

### AMEM-65
Capability validity depends on provenance.

### AMEM-66
Owner destruction cannot invalidate a live capability.

### AMEM-67
Safe code cannot create conflicting mutable capabilities.

### AMEM-68
Unknown overlap cannot be assumed disjoint.

### AMEM-69
Compiler may shorten lifetime when semantics remain unchanged.

### AMEM-70
Observable address identity constrains storage optimization.

### AMEM-71
Relocatable storage cannot invalidate a live capability.

### AMEM-72
Stable address requires explicit storage contract.

---

# 82. Ownership invariants

### AOWN-30
A Drop-bearing type is not Copyable.

### AOWN-31
Returning an owned value transfers semantic ownership.

### AOWN-32
Use after Move is a compile-time error.

### AOWN-33
Move does not require physical copying.

### AOWN-34
Copy does not require physical copying.

### AOWN-35
Clone is explicit and may have arbitrary cost.

### AOWN-36
Partial move preserves ownership of unaffected fields.

### AOWN-37
Reinitialization can restore a partially moved value.

### AOWN-38
Custom Drop forbids partial move.

### AOWN-39
Derived Drop may support partial move.

### AOWN-40
Drop order is deterministic.

### AOWN-41
Drop is non-fallible.

### AOWN-42
Drop is distinct from deallocation.

---

# 83. Capability invariants

### ACAP-30
Capability duplication is not value Copy.

### ACAP-31
Pattern matching through a capability cannot move ownership.

### ACAP-32
`view<T>` is read-only.

### ACAP-33
`mut_view<T>` is exclusive-write.

### ACAP-34
`view<T>` may be duplicated.

### ACAP-35
`mut_view<T>` is move-only.

### ACAP-36
Capabilities do not own their target.

### ACAP-37
Capability provenance is tracked by the compiler.

### ACAP-38
Capability lifetime is semantic, not necessarily lexical.

### ACAP-39
Capabilities cannot outlive their valid owner/storage.

### ACAP-40
Conflicting capabilities cannot coexist in safe code.

### ACAP-41
Disjoint capabilities may coexist.

### ACAP-42
Unknown overlap is not assumed disjoint.

---

# 84. Đây là điểm khác biệt cốt lõi của Axiom

Rust-style ownership thường khiến programmer phải suy nghĩ nhiều về:

```text
& T
&mut T
'a
'a
'a mut
lifetimes
```

Axiom chuyển phần lớn vấn đề đó thành:

```text
Type
Ownership
Capability
```

ở compiler.

Source code thường chỉ cần:

```axiom
fn print(x: view<User>)
fn update(x: mut_view<User>)
fn consume(x: User)
```

Compiler tự quyết định:

```text
capability start
capability end
alias conflict
last use
drop point
relocation safety
```

---

# 85. Nhưng Axiom không "giấu" semantic boundary

Khi semantics thực sự quan trọng, source vẫn phải explicit:

```axiom
view(x)
mut_view(x)
move || ...
unsafe { ... }
Arc<T>
Box<T>
Handle<T>
dyn Trait
```

Đây chính là nguyên tắc:

> **Explicit at semantic boundaries, implicit within the compiler.**

---

# 86. Ví dụ hoàn chỉnh

```axiom
struct User {
    id: u64
    name: Text
}

fn print_name(user: view<User>) {
    print(user.name)
}

fn rename(user: mut_view<User>, name: Text) {
    user.name = name
}

fn consume(user: User) {
    print(user.name)
}

fn main() {
    var user = User {
        id: 10,
        name: "Axiom"
    }

    print_name(user)

    rename(user, "New")

    consume(user)
}
```

Semantic model:

```text
user
 │
 ├─ print_name
 │    └─ ephemeral READ capability
 │
 ├─ rename
 │    └─ ephemeral WRITE capability
 │
 └─ consume
      └─ MOVE ownership
```

Không có:

```text
heap allocation bắt buộc
GC
borrow object runtime
lifetime object runtime
reference counter
object header
```

---

# 87. Ví dụ compiler có thể tối ưu

Source:

```axiom
fn length(v: view<Vec2>) -> f32 {
    sqrt(v.x * v.x + v.y * v.y)
}
```

Sau verification:

```text
v
→ READ capability
→ valid
→ no alias conflict
```

Release machine code có thể chỉ còn:

```text
load x
load y
mul
mul
add
sqrt
return
```

Không cần runtime `view` object.

Đây chính là **zero-cost capability abstraction**.

---

# 88. Part III — Freeze

Memory model hiện đã có một invariant khá mạnh:

```text
                    Axiom value
                       │
              ┌────────┴────────┐
              │                 │
           OWNER            CAPABILITY
              │                 │
        unique authority    non-owning
              │                 │
      ┌───────┴───────┐     ┌───┴────┐
      │               │     │        │
    Copy            Move   view    mut_view
      │               │     │        │
 duplicate        transfer READ    WRITE
```

và:

```text
OWNER
  ↓
compiler-managed lifetime
  ↓
verified MIR
  ↓
capability/ownership metadata erased
  ↓
native code
```

**Không có foundational contradiction mới xuất hiện.**

---

# 89. Bước tiếp theo — Part IV

Tiếp tục theo thứ tự, phần kế tiếp là:

## **AXIOM LANGUAGE SPECIFICATION v0.1 — Part IV**
### Drop · Resource Semantics · Allocation · Box · Vec · Arena · Pool · Static · TLS · Stable Address

Phần này sẽ đặc biệt quan trọng vì nó trả lời sâu hơn vấn đề ban đầu của bạn về **"flat memory model có thực sự nhanh hơn không, fragmentation xử lý ở đâu, heap có bắt buộc không"**.

Ta sẽ chốt:

```text
stack/register/heap semantics
allocation MIR
deallocation MIR
Box
Vec
String
Arena
Pool
Slab
static
TLS
custom allocator
OOM
allocation failure
stable address
relocation
fragmentation
address observability
caller-allocated return
escape analysis
allocation elimination
```

Sau đó mới chuyển sang **Concurrency + Send/Share**, vì concurrency phụ thuộc trực tiếp vào ownership/capability model vừa khóa.