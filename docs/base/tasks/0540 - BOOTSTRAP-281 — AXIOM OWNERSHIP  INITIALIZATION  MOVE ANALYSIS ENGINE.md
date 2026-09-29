# BOOTSTRAP-281 — AXIOM OWNERSHIP / INITIALIZATION / MOVE ANALYSIS ENGINE
## FROZEN / COMPLETED

**Trạng thái:** `FROZEN`  
**Phụ thuộc trực tiếp:** `BOOTSTRAP-274`, `BOOTSTRAP-277`, `BOOTSTRAP-280`  
**Tiền đề:** `AOWN-*`, `AMIR-*`, `AVERIFY-*`

---

# 1. Mục tiêu

BOOTSTRAP-281 định nghĩa engine chịu trách nhiệm chứng minh:

- biến/field đã được khởi tạo trước khi đọc;
- ownership đang tồn tại trước khi Move/Drop;
- giá trị không bị dùng sau Move;
- không Drop hai lần;
- không bỏ sót Drop;
- partial move được xử lý chính xác;
- Copy không tiêu thụ ownership;
- Move tiêu thụ ownership;
- Clone tạo ownership mới;
- assignment/reinitialization khôi phục ownership hợp lệ;
- mọi control-flow path đều có trạng thái ownership hợp lệ;
- cleanup khi `return`, `break`, `continue`, `panic`, unwind;
- ownership tương tác chính xác với `view`, `mut_view`, async, closure, Send/Share, FFI và unsafe.

Engine này **không phải borrow checker kiểu Rust**.

Người lập trình **không viết lifetime hoặc borrow annotation**.

Nguyên tắc:

> **Programmer describes ownership semantically; compiler proves ownership automatically.**

---

# 2. Ranh giới semantic

Pipeline:

```text
Typed HIR
   ↓
MIR
   ↓
Ownership / Initialization / Move Analysis
   ↓
Capability Analysis
   ↓
Drop Verification
   ↓
Verified MIR
   ↓
Optimization
```

281 chỉ chịu trách nhiệm về:

```text
Initialization
Ownership
Move
Copy
Clone
Drop obligation
Replacement
Partial Move
Path State
```

Không chịu trách nhiệm trực tiếp về:

- register allocation;
- stack/heap selection;
- instruction scheduling;
- alias optimization;
- ABI;
- machine code.

---

# 3. Quyết định kiến trúc quan trọng

Không dùng một enum đơn giản:

```text
Owned
Moved
Uninit
Dropped
```

vì nó không đủ biểu diễn trạng thái tại branch.

Ví dụ:

```text
if condition {
    x = Resource()
} else {
    // x chưa tồn tại
}

use(x)
```

Sau merge:

```text
x = MaybeInitialized
```

Trong khi:

```text
if condition {
    move(x)
} else {
    keep(x)
}

use(x)
```

sẽ tạo:

```text
x = MaybeOwned
```

Do đó engine sử dụng **hai chiều phân tích liên kết**.

---

# 4. Ownership State Model

```text
PathState
├── InitializationState
└── OwnershipState
```

## 4.1 Initialization

```text
InitState =
    Uninit
    Init
    MaybeInit
```

`MaybeInit` **không phải runtime state**.

Nó chỉ là abstract state dùng trong dataflow.

---

# 5. Ownership state

```text
OwnState =
    NoOwnership
    Owned
    Moved
    Dropped
    MaybeOwned
```

Kết hợp:

```text
InitState × OwnState
```

nhưng compiler chỉ cho phép các combination hợp lệ.

Ví dụ:

| Init | Ownership | Ý nghĩa |
|---|---|---|
| Uninit | NoOwnership | chưa có value |
| Init | Owned | value hợp lệ, đang sở hữu |
| Init | Moved | storage còn nhưng ownership đã chuyển |
| Init | Dropped | đã cleanup |
| MaybeInit | MaybeOwned | path-dependent |
| Uninit | Owned | **invalid state** |

---

# 6. Không coi Maybe* là runtime state

Compiler tuyệt đối không generate:

```text
if state == MaybeOwned
```

trừ khi semantics của chương trình thực sự yêu cầu runtime discriminant.

Thông thường:

```text
MaybeOwned
```

chỉ là fact trong verifier.

Ví dụ:

```text
if condition {
    move(x)
}

use(x)
```

Compiler không cần tạo runtime ownership flag.

Thay vào đó:

```text
ownership proof = failed
→ compile error
```

---

# 7. MovePath

Ownership được theo dõi theo **place tree**, không chỉ theo variable.

Ví dụ:

```text
struct User {
    name: String
    age: u32
    address: Address
}
```

Compiler tạo:

```text
user
├── user.name
├── user.age
└── user.address
```

Move:

```text
move(user.name)
```

chỉ consume:

```text
user.name
```

không consume:

```text
user.age
user.address
```

---

# 8. MovePath representation

```text
MovePath {
    root: LocalId
    parent: Option<MovePathId>
    projection: Projection
    children: [MovePathId]
}
```

Có thể canonicalize:

```text
MovePathKey {
    base: LocalId
    projections: [ProjectionKey]
}
```

và intern trong `MovePathDB`.

---

# 9. Ownership tree

Ví dụ:

```text
x
├── a
│   ├── a.p
│   └── a.q
├── b
└── c
```

Cho phép compiler biết:

```text
move(x.a.p)
```

không đồng nghĩa:

```text
move(x)
```

---

# 10. Definite Initialization

Một read chỉ hợp lệ khi compiler chứng minh:

```text
InitState == Init
```

Ví dụ:

```text
let x: String

print(x)
```

→ reject.

Nhưng:

```text
let x: String

x = make_string()

print(x)
```

→ valid.

---

# 11. Reinitialization

Move không khóa vĩnh viễn variable.

Ví dụ:

```text
let x = String("hello")

consume(x)

x = String("world")

consume(x)
```

State:

```text
Owned
  ↓
Moved
  ↓
Owned
  ↓
Moved
```

Đây là một đặc tính quan trọng.

> **Moved-from place có thể được reinitialized.**

---

# 12. Move semantics

Semantic:

```text
Move(x)
```

thực hiện:

```text
source ownership → destination ownership
source → Moved
```

Không bắt buộc machine-level copy.

Ví dụ:

```text
let a = make_buffer()
let b = a
```

có thể trở thành:

```text
a: Moved
b: Owned
```

và physical implementation có thể chỉ là register/SSA rename.

---

# 13. Copy semantics

```text
Copy(x)
```

không consume source.

```text
x: Owned
```

sau:

```text
Copy(x)
```

vẫn:

```text
x: Owned
```

Destination nhận một value độc lập theo semantic `Copy`.

Compiler có thể không generate physical copy nếu optimization chứng minh không cần.

---

# 14. Clone

`Clone` hoàn toàn khác `Copy`.

```text
let b = x.clone()
```

semantic:

```text
x: Owned
b: Owned
```

và có thể có cost runtime.

Compiler **không được biến Clone thành Copy** trừ khi chứng minh implementation tương đương theo semantics.

---

# 15. Assignment semantics

Assignment vào một place đã có owning value phải xử lý replacement.

Ví dụ:

```text
x = new_value
```

nếu:

```text
x: Owned
```

thì semantic sequence tương đương:

```text
Drop(x)
Initialize(x, new_value)
```

với điều kiện type cho phép replacement.

Compiler có thể fuse/optimize thành:

```text
construct new value directly into x
```

nhưng semantic Drop cũ vẫn phải được bảo toàn.

---

# 16. Assignment vào moved place

```text
consume(x)

x = new_value
```

hợp lệ.

Trạng thái:

```text
x: Moved
      ↓
x = new_value
      ↓
x: Owned
```

---

# 17. Partial Move

Ví dụ:

```text
let user = User(...)

consume(user.name)

print(user.age)
```

hợp lệ nếu `User` cho phép partial move.

State:

```text
user
├── name      Moved
├── age       Owned
└── address   Owned
```

---

# 18. Partial Move + whole-object use

Sau:

```text
consume(user.name)
```

lệnh:

```text
consume(user)
```

không hợp lệ vì:

```text
user.name = Moved
```

Compiler phải reject whole-object Move.

---

# 19. Partial Move + reinitialization

```text
consume(user.name)

user.name = new_name

consume(user)
```

có thể hợp lệ.

Sau assignment:

```text
user
├── name      Owned
├── age       Owned
└── address   Owned
```

→ whole-object Move hợp lệ.

---

# 20. Custom Drop

Đây là trường hợp đặc biệt.

Nếu:

```text
struct Resource {
    handle: Handle
}

impl Drop for Resource {
    ...
}
```

compiler **không cho partial move mặc định**.

Ví dụ:

```text
consume(resource.handle)
```

→ reject.

Lý do:

`Drop(Resource)` cần nhìn thấy một `Resource` hợp lệ toàn vẹn.

Nếu cho:

```text
resource.handle = Moved
```

thì compiler không còn đảm bảo invariant của `Drop`.

---

# 21. Compiler-derived Drop

Nếu Drop được compiler derive và semantics cho phép field-sensitive cleanup:

```text
struct S {
    a: ResourceA
    b: ResourceB
}
```

thì:

```text
move(s.a)
```

có thể hợp lệ.

Cleanup cuối scope:

```text
drop(s.b)
```

chứ không:

```text
drop(s.a)
drop(s.b)
```

---

# 22. Exactly-once Drop

Invariant:

> Mỗi ownership obligation phải được cleanup đúng một lần hoặc được transfer.

Các kết quả hợp lệ:

```text
Owned → Move
Owned → Drop
Owned → Return
Owned → Transfer
```

Không hợp lệ:

```text
Owned → Drop
       → Drop
```

hoặc:

```text
Owned
→ Moved
→ Drop(source)
```

---

# 23. Drop không đồng nghĩa Deallocate

Ownership engine chỉ chứng minh:

```text
semantic cleanup
```

Không quyết định:

```text
free()
munmap()
heap deallocation
stack release
register lifetime
```

Ví dụ:

```text
drop(buffer)
```

có thể release resource nhưng physical memory vẫn được allocator giữ lại.

---

# 24. `StorageDead` khác `Drop`

Đây là distinction bắt buộc.

```text
Drop(x)
```

= semantic resource cleanup.

```text
StorageDead(x)
```

= compiler không còn cần storage của local.

Ví dụ:

```text
Drop(x)
StorageDead(x)
```

không có nghĩa:

```text
free(x)
```

---

# 25. Last-use optimization

Compiler có thể phát hiện:

```text
let x = Resource()

use(x)

do_other_work()
```

và xác định:

```text
last semantic use = use(x)
```

Sau đó có thể:

```text
Drop(x)
```

sớm hơn lexical scope.

Điều này chỉ hợp lệ nếu không thay đổi observable semantics.

---

# 26. Lexical scope không phải lifetime duy nhất

Axiom không bắt buộc:

```text
lifetime == {}
```

Compiler có thể rút ngắn lifetime.

Nhưng:

> Semantic destruction timing phải tuân thủ observable program semantics.

Nếu `Drop` có observable side effects, compiler không được tùy tiện di chuyển Drop.

---

# 27. Branch join

Ví dụ:

```text
if cond {
    x = Resource()
} else {
    x = Resource()
}

use(x)
```

Hai predecessor:

```text
Init + Owned
Init + Owned
```

join:

```text
Init + Owned
```

→ valid.

---

# 28. Branch không đồng nhất

```text
if cond {
    x = Resource()
} else {
    // nothing
}

use(x)
```

join:

```text
MaybeInit
MaybeOwned
```

→ reject.

---

# 29. Move branch

```text
if cond {
    consume(x)
}

use(x)
```

join:

```text
MaybeOwned
```

→ reject.

Compiler không được giả định branch nào xảy ra.

---

# 30. Path-sensitive refinement

Axiom vẫn cho phép compiler hiểu điều kiện path.

Ví dụ:

```text
match value {
    Some(x) => consume(x),
    None => ...
}
```

Mỗi arm có ownership state riêng.

Sau khi arm kết thúc, cleanup được tính riêng rồi merge.

---

# 31. Match

`match` tạo:

```text
discriminant
    ↓
Arm A
Arm B
Arm C
    ↓
Join
```

Mỗi arm có `PathState`.

Pattern binding có thể:

```text
Copy
Move
View
MutView
```

tùy binding semantics và type.

---

# 32. Loop

Loop tạo fixed-point dataflow.

Ví dụ:

```text
while cond {
    consume(x)
    x = make()
}
```

State phải hội tụ:

```text
Owned
 ↓
Moved
 ↓
Owned
 ↓
Moved
...
```

Compiler không mô phỏng runtime iteration.

Nó tính invariant của loop.

---

# 33. Loop convergence

Ownership analysis sử dụng lattice hữu hạn.

Ví dụ:

```text
Uninit
Init
MaybeInit
```

và:

```text
Owned
Moved
MaybeOwned
```

Join phải đơn điệu.

Không được có:

```text
Owned → MaybeOwned → Owned
```

do dataflow iteration.

---

# 34. Dataflow algorithm

```text
for block in CFG:
    state_in[block] = TOP/ENTRY

repeat:
    changed = false

    for block in deterministic_order:
        state = join(predecessors)

        state_out = transfer(block, state)

        if state_out != old:
            state_out[block] = state_out
            changed = true

until !changed
```

Parallel implementation được phép sau đó nhưng kết quả phải deterministic.

---

# 35. Transfer function

Các MIR operation chính:

```text
Move(place)
Copy(place)
Assign(place, value)
Drop(place)
Call(...)
MakeView(...)
MakeMutView(...)
Return
```

đều có ownership transfer function.

Ví dụ:

```text
Move(x)
```

requires:

```text
x == Owned
```

then:

```text
x = Moved
```

---

# 36. Call ownership summary

Call là phần cực kỳ quan trọng.

Compiler cần biết:

```text
fn consume(x: Resource)
```

consume argument.

Trong khi:

```text
fn inspect(x: view<Resource>)
```

không consume owner.

Function summary:

```text
FunctionOwnershipSummary {
    consumed_args
    copied_args
    borrowed_args
    mut_borrowed_args
    returned_ownership
    returned_capabilities
    retained_arguments
    escape_behavior
    send_effect
    share_effect
    drop_behavior
    panic_behavior
}
```

---

# 37. Ví dụ

```text
fn consume(x: Resource) -> Result
```

summary:

```text
arg0 = CONSUMED
return = OWNING
```

Call:

```text
consume(a)
```

sẽ tạo:

```text
a → Moved
```

---

# 38. Borrow/view call

```text
fn inspect(x: view<Resource>)
```

Call:

```text
inspect(a)
```

không tạo:

```text
a → Moved
```

mà:

```text
a → Owned
capability(view(a))
```

Capability engine chịu trách nhiệm về validity của view.

Ownership engine chỉ đảm bảo owner vẫn tồn tại.

---

# 39. Mutable view

```text
fn update(x: mut_view<Resource>)
```

Call:

```text
update(a)
```

không consume `a`.

Nhưng capability engine phải chứng minh:

```text
WRITE capability
```

hợp lệ.

---

# 40. Ownership + capability interaction

Không cho:

```text
owner destroyed
```

trong khi:

```text
dependent view alive
```

Ví dụ:

```text
let x = Buffer(...)
let v = view(x)

drop(x)
```

→ reject.

---

# 41. Move owner với live view

Ví dụ:

```text
let x = Buffer(...)
let v = view(x)

move(x)
```

không tự động được phép.

Compiler phải chứng minh việc Move có giữ nguyên provenance/storage contract hay không.

Mặc định:

```text
live dependent capability
+
ownership transfer potentially relocatable
=
reject
```

---

# 42. Stable-address contract

Nếu storage có contract:

```text
stable address
```

thì ownership transfer có thể giữ:

```text
same storage identity
same provenance
```

và compiler có thể cho phép một số hình thức transfer.

Nhưng đây là **explicit storage contract**, không phải mặc định.

---

# 43. Vec relocation

```text
let v = Vec(...)
let view = view(v)
```

Sau đó:

```text
v.push(...)
```

nếu push có thể relocate storage:

```text
live view
+
possible relocation
=
reject
```

hoặc compiler phải chứng minh operation không relocate.

---

# 44. Closure capture

Closure capture cũng được biểu diễn bằng ownership state.

Ví dụ:

```text
let resource = Resource()

let f = || consume(resource)
```

Compiler xác định:

```text
capture(resource) = Move
```

sau capture:

```text
resource = Moved
```

nếu closure trở thành owner của resource.

---

# 45. Borrowed capture

```text
let f = || inspect(resource)
```

có thể capture:

```text
view
```

nếu lifetime/provenance hợp lệ.

Closure không được vô tình escape cùng một view đã hết owner lifetime.

---

# 46. Closure escape

Nếu closure:

```text
return f
```

thì compiler phải phân tích:

```text
capture lifetime
escape
ownership
capability
```

Một borrowed closure không được return nếu capture provenance không sống đủ lâu.

Không cần programmer viết lifetime.

---

# 47. Async

Tại:

```text
await future
```

mọi value live across suspension phải được đưa vào future state machine.

Ownership engine kiểm tra:

```text
state field ownership
```

Ví dụ:

```text
let buffer = Buffer()

await io()

use(buffer)
```

`buffer` phải trở thành một phần của async state.

---

# 48. Move trước await

```text
consume(buffer)

await io()
```

sau `consume`:

```text
buffer = Moved
```

Không cần capture `buffer` vào future state.

---

# 49. View qua await

Mặc định:

```text
let v = view(buffer)

await io()

use(v)
```

→ reject.

Trừ khi API/execution/storage contract chứng minh:

```text
owner stable
capability valid across suspension
```

---

# 50. Send

Ownership transfer sang thread/task:

```text
spawn(move(x))
```

sẽ:

```text
x = Moved
```

và compiler kiểm tra:

```text
Type(x): Send
```

---

# 51. Send không phải Share

Một value:

```text
Send
```

không có nghĩa:

```text
Share
```

Ví dụ:

```text
Buffer
```

có thể chuyển sang worker:

```text
owner Thread A
→ Move
→ owner Thread B
```

nhưng không cho hai thread cùng mutate.

---

# 52. Share

Shared ownership thường là:

```text
Arc<T>
```

Ownership engine thấy:

```text
Arc<T>: Owned
```

nhưng semantic resource bên trong được quản lý bởi abstraction `Arc`.

Không suy diễn:

```text
Arc<T> => T mutable-safe
```

Share property được kiểm tra riêng.

---

# 53. Channel

Channel send:

```text
send(x)
```

nếu API consume ownership:

```text
x → Moved
```

receiver nhận:

```text
Owned
```

Đây là ownership transfer boundary.

---

# 54. Return

```text
fn create() -> Resource {
    let x = Resource()
    return x
}
```

Không Drop `x` tại return.

Semantic:

```text
x ownership
      ↓
return value
      ↓
caller owns
```

---

# 55. Return Copy

```text
return copy(x)
```

source vẫn:

```text
Owned
```

destination/caller nhận:

```text
Owned
```

---

# 56. Return view

```text
fn get_name(x: User) -> view<str>
```

nếu return view phụ thuộc vào `x`, compiler phải chứng minh provenance.

Không được:

```text
Drop(x)
return dangling_view
```

---

# 57. `?`

Ví dụ:

```text
fn f() -> Result<T, E> {
    let x = acquire()?
    use(x)
    ...
}
```

`?` được lowering thành branch.

Success:

```text
continue
```

Error:

```text
cleanup current owned values
return error
```

Ownership analysis xử lý hai path độc lập.

---

# 58. Panic / unwind

Nếu profile hỗ trợ unwind:

```text
panic()
```

có cleanup graph.

Ví dụ:

```text
x: Owned
y: Owned

panic()
```

cleanup:

```text
Drop(y)
Drop(x)
unwind
```

theo cleanup ordering semantics.

---

# 59. Abort profile

Nếu panic profile là abort:

```text
panic()
```

không cần runtime unwind.

Nhưng semantic ownership model vẫn phải biết:

```text
control flow terminates
```

Không được tiếp tục phân tích path sau `panic`.

---

# 60. Break / continue

```text
while ... {
    let x = Resource()

    if cond {
        break
    }

    use(x)
}
```

`break` phải đi qua cleanup của các scope đã rời.

MIR:

```text
break
 ↓
cleanup
 ↓
loop exit
```

---

# 61. Destructuring

Ví dụ:

```text
let User { name, age } = user
```

Compiler xác định binding mode.

Nếu binding là Move:

```text
user.name → Moved
user.age  → Moved
```

Nếu Copy:

```text
user.name remains Owned
```

Nếu view:

```text
capability created
```

---

# 62. Pattern binding

Mỗi binding phải có semantic mode rõ ràng:

```text
MOVE
COPY
VIEW
MUT_VIEW
```

Không được để MIR tự đoán.

---

# 63. Swap

Một primitive/library operation như:

```text
swap(a, b)
```

không được phân tích như hai Move tuần tự nếu điều đó làm mất trạng thái trung gian.

Compiler có thể có intrinsic semantic:

```text
SwapOwnership(a, b)
```

với precondition:

```text
a initialized
b initialized
```

và hậu điều kiện:

```text
ownership(a) = old ownership(b)
ownership(b) = old ownership(a)
```

---

# 64. Replace

```text
old = replace(x, new)
```

semantic:

```text
old = Move(x)
x = Move(new)
```

nhưng phải được biểu diễn atomic về ownership semantics.

Không được để compiler tạm thời tạo:

```text
x = Moved
```

rồi tạo false-positive Drop nếu operation hợp lệ.

---

# 65. `take`

Ví dụ:

```text
let value = take(x)
```

sau:

```text
value = Owned
x = Moved/Empty-state
```

Nếu API muốn sử dụng `x` tiếp tục mà không cần reinitialization, type phải có semantic representation hỗ trợ empty state, thường thông qua:

```text
Option<T>
```

---

# 66. Shadowing

```text
let x = Resource()
{
    let x = OtherResource()
}
```

hai declaration có:

```text
LocalId khác nhau
```

không được coi là cùng ownership state.

Scope exit:

```text
Drop(inner x)
```

sau đó:

```text
outer x
```

tiếp tục sống.

---

# 67. Initialization of aggregates

Compiler phải theo dõi field-level initialization.

Ví dụ:

```text
var user: User

user.name = ...
```

state:

```text
user.name = Init
user.age  = Uninit
user.addr = Uninit
```

Whole-object use:

```text
print(user)
```

→ reject.

---

# 68. Field-sensitive initialization

```text
user.name
```

có thể đọc nếu:

```text
user.name == Init
```

dù:

```text
user.age == Uninit
```

Nhưng chỉ khi operation không yêu cầu toàn bộ `User`.

---

# 69. Arrays

Array initialization được theo dõi theo element khi cần.

```text
a[0] = ...
a[1] = ...
```

Compiler có thể track:

```text
a[0] Init
a[1] Init
...
```

nhưng không nhất thiết tạo một node riêng cho mọi phần tử lớn.

Có thể dùng:

```text
range initialization summary
```

để giảm memory.

---

# 70. Dynamic collections

Với:

```text
Vec<T>
```

ownership engine không theo dõi từng runtime element bằng compile-time path.

Nó theo dõi:

```text
Vec<T> ownership
```

Còn element ownership là invariant của `Vec<T>` implementation.

---

# 71. Generics

Generic function:

```text
fn consume<T>(x: T)
```

ownership behavior không phụ thuộc vào concrete representation.

Compiler có thể biểu diễn:

```text
T: parameter consumed
```

và khi instantiate:

```text
consume<Resource>(x)
```

x bị Move.

---

# 72. Generic property

Ownership engine không được giả định:

```text
T: Copy
```

trừ khi trait obligation chứng minh.

Ví dụ:

```text
fn f<T>(x: T) {
    let y = x
    use(x)
}
```

không hợp lệ nếu `T` không có `Copy`.

Nếu:

```text
T: Copy
```

thì có thể dùng Copy semantics.

---

# 73. Drop generic

```text
fn f<T>(x: T)
```

compiler phải biết:

```text
T: Drop?
```

Nếu `T` có Drop, cleanup obligation được sinh ra.

Nếu `T` không có Drop:

```text
Drop(x)
```

có thể là no-op semantic và được eliminate.

---

# 74. Trait-driven ownership

Các property:

```text
Copy
Clone
Drop
Send
Share
```

là compiler-derived semantic facts.

Ownership engine query:

```text
TypeDB
TraitDB
```

thông qua CompilerDB.

Không tự tạo một trait solver riêng.

---

# 75. Unsafe

Unsafe có thể làm compiler mất một số proof.

Ví dụ:

```text
unsafe {
    p = raw_pointer(...)
}
```

nhưng unsafe **không biến mọi thứ thành Owned hợp lệ**.

Chỉ contract cụ thể mới có thể thiết lập:

```text
TrustedOwned<T>
```

hoặc tương đương semantic fact.

---

# 76. Unsafe contract

Ví dụ system intrinsic:

```text
unsafe fn assume_initialized<T>(...)
```

có contract:

```text
postcondition:
    place = Init + Owned
```

Ownership verifier tiếp nhận fact này.

Nhưng mọi thao tác sau đó vẫn được kiểm tra bình thường.

---

# 77. FFI

Function C:

```text
extern fn c_api(*mut T)
```

mặc định ownership semantics:

```text
UNKNOWN
```

Compiler không tự suy luận:

```text
consumes
retains
frees
borrows
```

Safe wrapper phải khai báo semantic contract.

---

# 78. FFI wrapper

Ví dụ:

```text
fn close(handle: Handle)
```

wrapper có thể định nghĩa:

```text
consumes handle
```

Sau đó:

```text
close(h)
```

→

```text
h = Moved
```

---

# 79. Foreign callback

Nếu foreign API giữ callback lâu dài:

```text
register(callback)
```

thì closure/captured ownership phải được đánh dấu:

```text
ExternalEscape
```

Ownership engine phối hợp với EscapeAnalysis.

---

# 80. Storage identity

Ownership không đồng nghĩa physical address.

Một:

```text
Box<T>
```

có:

```text
Value Ownership
Storage Identity
```

Move Box có thể chuyển ownership mà không nhất thiết copy object.

---

# 81. Stable address

Nếu API yêu cầu:

```text
stable address
```

ownership engine phải phối hợp:

```text
StorageAnalysis
CapabilityAnalysis
EscapeAnalysis
```

để cấm:

```text
relocation
```

khi còn contract phụ thuộc.

---

# 82. No optimization dependency

Đây là invariant rất quan trọng.

Ownership validity phải giống nhau với:

```text
-O0
-O1
-O2
-O3
-Os
-LTO
-PGO
```

Nếu chương trình:

```text
invalid ownership
```

thì không optimization nào được phép biến nó thành valid.

---

# 83. Optimization chỉ được dùng ownership facts

Ngược lại optimization có thể dùng:

```text
proven Move
proven no-use-after-move
proven disjoint
proven noescape
proven exactly-once Drop
```

để:

```text
eliminate copies
eliminate moves
stack promote
scalarize
remove allocation
inline
```

---

# 84. Ownership facts cho optimizer

Xuất ra:

```text
OwnershipFacts {
    initialized_places
    moved_places
    consumed_arguments
    drop_obligations
    noalias_capabilities
    relocation_constraints
    escape_facts
}
```

Nhưng optimizer không được sửa semantic facts trực tiếp.

---

# 85. Ownership + alias analysis

Nếu:

```text
a: Owned
v: view(a.field)
```

ownership engine nói:

```text
a alive
```

capability engine nói:

```text
field capability alive
```

Alias engine nói:

```text
region relation
```

Ba engine phối hợp qua CompilerDB.

---

# 86. Unified verifier

Kiến trúc:

```text
                    ┌──────────────┐
                    │ Ownership    │
                    │ Init / Move  │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              ↓                         ↓
       Capability                    Drop
       Analysis                     Analysis
              │                         │
              └────────────┬────────────┘
                           ↓
                    Verified MIR
```

Không có engine nào tự cấp “safe” status cuối cùng.

---

# 87. Dataflow state

Đề xuất implementation:

```text
OwnershipAnalysisState {
    places: MovePathStateTable
    capabilities: CapabilityFacts
    scopes: ScopeState
    escapes: EscapeFacts
}
```

Trong đó:

```text
MovePathState {
    init: InitState
    ownership: OwnershipState
}
```

---

# 88. Path state compression

Các state phổ biến:

```text
AllOwned
AllMoved
AllUninit
Partial(...)
```

có thể được intern.

Không lưu object graph lớn cho mỗi CFG node nếu không cần.

---

# 89. Sparse representation

Đối với function lớn:

```text
LocalId → state
```

chỉ lưu các path thay đổi.

Ví dụ:

```text
SparseMoveState {
    changed_paths: BitSet<MovePathId>
    states: SmallMap<MovePathId, PathState>
}
```

---

# 90. Join operation

Join phải bảo thủ.

Ví dụ:

```text
Owned ⊔ Owned = Owned
Moved ⊔ Moved = Moved
Uninit ⊔ Uninit = Uninit
Owned ⊔ Moved = MaybeOwned
Init ⊔ Uninit = MaybeInit
```

Không được:

```text
Owned ⊔ Moved = Owned
```

vì điều đó sẽ tạo unsafe false proof.

---

# 91. Error state

`Maybe*` không tự động là error tại merge.

Error xảy ra khi một operation yêu cầu proof mạnh hơn.

Ví dụ:

```text
MaybeOwned
```

không phải compile error ngay.

Nhưng:

```text
Move(x)
```

requires:

```text
Owned
```

→ error.

Điều này giúp compiler xử lý CFG chính xác mà không báo lỗi giả.

---

# 92. Definite Drop

Tại scope exit:

```text
Owned
```

→ Drop.

```text
Moved
```

→ không Drop.

```text
Uninit
```

→ không Drop.

```text
Partial
```

→ Drop các initialized owned subpaths còn lại.

```text
MaybeOwned
```

→ cleanup CFG phải phân nhánh hoặc compiler phải chứng minh state.

---

# 93. Conditional Drop

Ví dụ:

```text
var x: Resource

if cond {
    x = Resource()
}
```

scope exit có:

```text
x = MaybeOwned
```

Compiler tạo cleanup semantics tương ứng với initialization state.

Không được unconditional:

```text
Drop(x)
```

nếu một path chưa initialize.

---

# 94. Cleanup state machine

Có thể biểu diễn:

```text
CleanupPoint {
    live_owned_paths
}
```

và cleanup lowering tạo:

```text
if initialized(path):
    Drop(path)
```

Nhưng `initialized` thường là CFG/control-flow fact đã được compiler biết, không nhất thiết là runtime boolean.

Compiler có thể clone cleanup blocks để loại bỏ branch runtime.

---

# 95. Exactly-once cleanup proof

Mỗi CFG exit:

```text
return
break
continue
panic
unwind
```

phải có cleanup path tương ứng.

Verifier kiểm tra:

```text
owned obligation entered
→ exactly one terminal action
```

---

# 96. Function entry

Parameter states:

### Owning parameter

```text
fn f(x: Resource)
```

entry:

```text
x = Init + Owned
```

### View

```text
fn f(x: view<Resource>)
```

entry:

```text
x = Init + NonOwning
capability = READ
```

### Mut view

```text
x = Init + NonOwning
capability = WRITE
```

### Copy primitive

```text
x = Owned
```

nhưng semantics cho phép Copy.

---

# 97. Function exit

Return analysis kiểm tra:

```text
all local ownership obligations resolved
```

trừ những ownership values được:

```text
returned
transferred
intentionally leaked via explicit unsafe/system contract
```

---

# 98. Intentional leak

Nếu programmer thực sự muốn leak resource:

```text
leak(x)
```

phải là explicit system/library operation.

Semantics:

```text
ownership obligation intentionally abandoned
```

và compiler không tự coi đó là bug.

Nhưng đây là explicit effect, không phải mặc định.

---

# 99. Compiler diagnostics

Axiom diagnostics phải giải thích **ownership transition**, không chỉ:

```text
use of moved value
```

Ví dụ conceptually:

```text
AXM-OWN-001

`buffer` is no longer owned here.

Ownership was transferred at:
    line 18: send(channel, buffer)

The later use occurs at:
    line 23: buffer.len()

Possible fixes:
    • use `buffer` before sending it
    • send a Copy value if the type supports Copy
    • explicitly clone the buffer if duplication is intended
```

---

# 100. Branch explanation

Nếu:

```text
if cond {
    consume(x)
}

use(x)
```

diagnostic:

```text
`x` may have been moved.

Path A:
    condition == true
    → consume(x)
    → x becomes Moved

Path B:
    condition == false
    → x remains Owned

At the merge point ownership is not definite.
```

Đây là điểm rất quan trọng cho AI-assisted programming.

---

# 101. AI-readable ownership graph

Compiler có thể xuất structured data:

```text
{
  "place": "x",
  "state": "MaybeOwned",
  "causes": [
    {
      "path": "cond == true",
      "transition": "Move",
      "source": "..."
    }
  ]
}
```

AI agent có thể query trực tiếp CompilerDB.

Không cần parse diagnostic text.

---

# 102. Query API

CompilerDB cung cấp:

```text
ownership_state(function, block, place)

initialization_state(function, block, place)

move_origin(place)

move_consumers(place)

drop_obligation(place)

ownership_path_graph(function)

why_not_owned(place, location)

why_not_initialized(place, location)
```

---

# 103. Incremental analysis

Một source edit:

```text
function A
```

không được làm recompute toàn bộ project.

Query dependency:

```text
MIR(A)
 ↓
Ownership(A)
 ↓
FunctionSummary(A)
```

chỉ invalidates dependent queries.

---

# 104. Function summaries

Cross-function analysis dùng summary:

```text
OwnershipSummaryFingerprint
```

Nếu implementation thay đổi nhưng summary semantic không đổi:

```text
caller ownership analysis
```

có thể được giữ lại.

---

# 105. Parallel analysis

Các function độc lập có thể phân tích song song:

```text
f1 ─┐
f2 ─┼→ OwnershipAnalysis
f3 ─┤
f4 ─┘
```

Kết quả không phụ thuộc worker count.

---

# 106. Deterministic diagnostics

Nếu nhiều ownership errors tồn tại:

compiler phải có deterministic ordering dựa trên:

```text
SourceFileId
SourceSpan
FunctionId
DiagnosticCode
```

Không dựa vào thread completion order.

---

# 107. Verification boundary

Một MIR chỉ được chuyển tiếp khi:

```text
Ownership = Proven
Initialization = Proven
Drop = Proven
Capability interaction = Proven
```

Nếu:

```text
MaybeOwned
MaybeInit
Unknown
```

ở nơi cần definite proof:

```text
REJECT
```

Không:

```text
fallback to unsafe
```

---

# 108. Không có “ownership runtime”

Axiom không mặc định sinh:

```text
ownership flag
reference count
GC metadata
object header
runtime borrow table
```

Ownership engine là **compile-time proof system**.

---

# 109. Không có borrow checker syntax

Không có:

```text
'a
&'a T
&'a mut T
where 'a: ...
```

trong Core.

Programmer chỉ viết semantic operations:

```text
view(x)
mut_view(x)
move
copy
clone
```

khi cần.

Compiler tự suy luận phần lớn lifetime.

---

# 110. Core invariant

> **Ownership is a compile-time semantic property, not a runtime bookkeeping mechanism.**

---

# 111. Module architecture

Đề xuất:

```text
compiler/
└── analysis/
    └── ownership/
        ├── mod.ax
        ├── state.ax
        ├── init_state.ax
        ├── ownership_state.ax
        ├── move_path.ax
        ├── move_tree.ax
        ├── place_state.ax
        ├── transfer.ax
        ├── copy.ax
        ├── clone.ax
        ├── assignment.ax
        ├── replacement.ax
        ├── partial_move.ax
        ├── drop_obligation.ax
        ├── cleanup.ax
        ├── branch.ax
        ├── match.ax
        ├── loop.ax
        ├── call_summary.ax
        ├── return.ax
        ├── closure.ax
        ├── async.ax
        ├── send.ax
        ├── ffi.ax
        ├── unsafe.ax
        ├── join.ax
        ├── dataflow.ax
        ├── diagnostics.ax
        ├── fingerprint.ax
        ├── query.ax
        └── tests/
```

---

# 112. Implementation order

```text
01  InitState
02  OwnershipState
03  PathState
04  MovePath
05  MovePathTree
06  Place → MovePath mapping
07  Definite initialization
08  Move transfer
09  Copy
10  Clone
11  Reinitialization
12  Assignment / replacement
13  Partial moves
14  Custom Drop restrictions
15  Derived Drop
16  Exactly-once Drop
17  Branch joins
18  Match
19  Loop fixed-point
20  Return
21  Break / Continue
22  Panic / Unwind
23  Call summaries
24  Generic ownership
25  Closure capture
26  Async state
27  Send
28  Capability integration
29  Stable-address integration
30  Escape integration
31  FFI
32  Unsafe contracts
33  Diagnostics
34  CompilerDB queries
35  Incremental caching
36  Parallel execution
37  Property tests
38  Fuzzing
39  Adversarial tests
40  Verified-MIR gate
```

---

# 113. Test categories

## Initialization

```text
read-before-init
partial-init
branch-init
loop-init
match-init
reinit-after-move
```

## Move

```text
use-after-move
double-move
move-after-partial-move
whole-object-after-field-move
move-then-reinitialize
```

## Copy

```text
copy-does-not-consume
nested-copy
generic-copy
copy-vs-drop
```

## Drop

```text
exactly-once
early-return
break
continue
panic
unwind
partial-drop
custom-drop
```

## Calls

```text
consume-arg
borrow-arg
mut-borrow-arg
return-owner
return-view
```

## Async

```text
live-across-await
moved-before-await
view-across-await
send-future
```

## Concurrency

```text
send
share
channel-transfer
guard-drop
```

## Unsafe/FFI

```text
trusted-owned-contract
invalid-contract
foreign-consume
foreign-retain
foreign-unknown
```

---

# 114. Adversarial tests

Bắt buộc có:

```text
1000+ nested branches
1000+ nested structs
deep partial moves
large arrays
large generic types
recursive CFG
irreducible CFG
many loop backedges
mutually recursive functions
generic recursive ownership
closure capture chains
async nested suspension
panic on every branch
```

Mục tiêu:

```text
correctness
termination
determinism
reasonable compile time
```

---

# 115. Property-based tests

Các property:

```text
Copy never consumes source
Move always consumes source
Clone preserves source
Moved value cannot be read
Uninitialized value cannot be read
Drop never occurs twice
Drop never occurs for uninitialized path
Reinitialization restores ownership
Branch join is conservative
Optimization level does not change validity
CFG block order does not change semantic result
Worker count does not change semantic result
```

---

# 116. Fuzzing

Fuzz:

```text
AST
Typed HIR
MIR
CFG
MovePath trees
generic substitutions
pattern matching
cleanup graphs
```

Đặc biệt fuzz:

```text
MIR → Ownership Analysis
```

vì MIR là boundary quan trọng trước verification.

---

# 117. Invalid MIR handling

Nếu MIR chứa:

```text
Move(nonexistent_place)
Drop(nonexistent_place)
invalid projection
invalid LocalId
invalid type
invalid CFG edge
```

thì đây là:

```text
compiler invariant violation
```

không phải user ownership error.

Phân biệt:

```text
AXM-OWN-*   user program semantic error
AXM-ICE-*   compiler invariant violation
```

---

# 118. Performance

Ownership analysis phải tránh trở thành “Rust borrow checker nhưng nặng hơn”.

Các kỹ thuật:

```text
MovePath interning
Sparse states
BitSet
SmallVec
arena allocation
CFG dominator information
last-use information
summary caching
incremental queries
parallel function analysis
path compression
```

---

# 119. Complexity target

Mục tiêu thực tế:

```text
O(CFG × MovePaths)
```

trong trường hợp tổng quát.

Nhưng common case phải gần:

```text
O(instructions + changed_paths)
```

nhờ sparse propagation.

Không yêu cầu compile-time phải tuyến tính tuyệt đối, nhưng pathological cases phải có giới hạn và diagnostics.

---

# 120. Ownership engine không tự optimize

Engine này không được thực hiện:

```text
register allocation
copy elimination
stack allocation
load/store elimination
```

Nó chỉ tạo proof/facts.

Optimizer quyết định physical transformation sau:

```text
Verified MIR
```

---

# 121. Ownership facts immutable sau verification

Sau khi verifier hoàn thành:

```text
VerifiedOwnershipFacts
```

được publish vào CompilerDB.

Optimizer có thể đọc.

Optimizer không được sửa chúng.

Nếu transformation làm thay đổi ownership semantics:

```text
re-verify
```

hoặc transformation đó không hợp lệ.

---

# 122. Ownership fingerprint

Summary fingerprint bao gồm những gì observable về ownership:

```text
parameter consumption
return ownership
drop behavior
escape behavior
capability retention
Send/Share requirements
FFI ownership contract
```

Không bao gồm:

```text
register
stack offset
instruction selection
physical allocation
```

---

# 123. CompilerDB integration

```text
CompilerDB
├── TypeDB
├── TraitDB
├── MIRDB
├── OwnershipDB
│   ├── MovePathDB
│   ├── OwnershipStateDB
│   ├── DropDB
│   └── SummaryDB
├── CapabilityDB
├── EscapeDB
└── VerificationDB
```

Queries:

```text
ownership_of(...)
move_paths(...)
drop_obligations(...)
function_ownership_summary(...)
```

---

# 124. Relationship with BOOTSTRAP-136

281 trả lời:

> **Ai sở hữu value? Value đã được initialize chưa? Value đã bị Move chưa? Khi nào ownership obligation kết thúc?**

BOOTSTRAP-136 trả lời:

> **Ai được phép truy cập region đó và access có conflict không?**

Hai vấn đề liên quan nhưng không đồng nhất.

---

# 125. Relationship with Drop Verification

281 tạo:

```text
DropObligations
```

Drop verifier xác nhận:

```text
exactly-once cleanup
```

Do đó:

```text
Ownership Analysis
       ↓
Drop Obligation
       ↓
Drop Verification
```

---

# 126. Relationship with Escape Analysis

281 nói:

```text
x ownership transferred
```

Escape analysis nói:

```text
x storage escapes where?
```

Ví dụ:

```text
return x
```

Ownership:

```text
caller owns x
```

Escape:

```text
ReturnEscape
```

---

# 127. Relationship with Capability Analysis

Ví dụ:

```text
let v = view(x)
```

Ownership:

```text
x remains Owned
```

Capability:

```text
v = READ capability
```

Khi:

```text
drop(x)
```

Ownership engine phát hiện owner destruction.

Capability engine phát hiện:

```text
live dependent capability
```

→ combined verifier reject.

---

# 128. Relationship with storage optimization

Ownership:

```text
x = Owned
```

không có nghĩa:

```text
heap
```

hoặc:

```text
stack
```

Compiler vẫn có thể:

```text
register
stack
inline
heap
arena
caller allocation
scalar replacement
```

Ownership semantics không thay đổi.

---

# 129. Fundamental design principle

Axiom sử dụng mô hình:

```text
             PROGRAMMER
                 │
                 │ semantic ownership
                 ↓
          ┌───────────────┐
          │  Ownership    │
          │    Engine     │
          └───────┬───────┘
                  │ proof
                  ↓
          ┌───────────────┐
          │ Optimization  │
          └───────┬───────┘
                  │
                  ↓
             MACHINE CODE
```

Compiler làm phần khó.

Programmer không phải viết lifetime graph.

---

# 130. Frozen Invariants — AOWNENG

Các invariant sau được **freeze**:

```text
AOWNENG-20
Ownership analysis operates on MIR, not source syntax.

AOWNENG-21
Initialization and ownership are separate but coupled dataflow dimensions.

AOWNENG-22
MaybeInit and MaybeOwned are analysis states, not runtime states.

AOWNENG-23
A value may be read only when definite initialization is proven.

AOWNENG-24
An owning value may be moved only when ownership is definitely present.

AOWNENG-25
Move consumes semantic ownership.

AOWNENG-26
Move does not imply a physical memory copy.

AOWNENG-27
Copy does not consume source ownership.

AOWNENG-28
Clone explicitly creates a new semantic ownership obligation.

AOWNENG-29
Moved places may be reinitialized.

AOWNENG-30
Reinitialization restores ownership for the initialized path.

AOWNENG-31
Ownership analysis is place-sensitive.

AOWNENG-32
Partial moves are tracked at place granularity.

AOWNENG-33
Whole-object use is forbidden when required subpaths are moved.

AOWNENG-34
Custom Drop types cannot be partially moved unless an explicit semantic contract permits it.

AOWNENG-35
Compiler-derived Drop may support field-sensitive partial cleanup.

AOWNENG-36
Every owned obligation must be transferred, returned, explicitly leaked, or cleaned up exactly once.

AOWNENG-37
Uninitialized paths must never be unconditionally dropped.

AOWNENG-38
Moved paths must never be dropped as though still owned.

AOWNENG-39
StorageDead is distinct from semantic Drop.

AOWNENG-40
Ownership lifetime is not inherently identical to lexical scope.

AOWNENG-41
The compiler may shorten destruction lifetime only when observable semantics remain unchanged.

AOWNENG-42
Branch joins are conservative.

AOWNENG-43
Owned joined with Moved does not produce definite ownership.

AOWNENG-44
Initialized joined with Uninitialized does not produce definite initialization.

AOWNENG-45
Maybe states are rejected when a definite proof is required.

AOWNENG-46
Loops are solved using a convergent dataflow fixed point.

AOWNENG-47
Ownership analysis must terminate for every valid MIR.

AOWNENG-48
Function calls use ownership summaries rather than rediscovering callee semantics.

AOWNENG-49
Consumed parameters are explicitly represented in function summaries.

AOWNENG-50
Returned ownership is explicitly represented in function summaries.

AOWNENG-51
View and mut_view parameters do not implicitly consume their owner.

AOWNENG-52
Owner destruction is invalid while a dependent safe capability remains live.

AOWNENG-53
Potentially relocating storage cannot be moved or mutated in a way that invalidates a live capability.

AOWNENG-54
Stable-address behavior requires an explicit storage contract.

AOWNENG-55
Closure captures participate in ownership analysis.

AOWNENG-56
Async values live across suspension participate in ownership analysis.

AOWNENG-57
Send transfer consumes the sender's ownership when the API transfers ownership.

AOWNENG-58
Send does not imply Share.

AOWNENG-59
Share does not imply mutable access.

AOWNENG-60
Channel ownership transfer is represented as explicit ownership transfer.

AOWNENG-61
Unsafe operations may establish trusted ownership facts only through explicit contracts.

AOWNENG-62
Unsafe does not disable subsequent ownership verification.

AOWNENG-63
Unknown FFI ownership behavior is not guessed by the compiler.

AOWNENG-64
FFI ownership behavior requires explicit contracts or conservative safe wrappers.

AOWNENG-65
Generic ownership behavior depends only on proven type properties and constraints.

AOWNENG-66
Ownership validity is independent of optimization level.

AOWNENG-67
Optimization may consume ownership facts but cannot redefine them.

AOWNENG-68
Verified ownership facts are immutable after publication.

AOWNENG-69
Ownership analysis is deterministic.

AOWNENG-70
Parallel ownership analysis must produce the same result as serial analysis.

AOWNENG-71
Incremental ownership analysis is dependency-driven.

AOWNENG-72
CompilerDB is the authoritative owner of ownership analysis state.

AOWNENG-73
Ownership analysis uses shared compiler dataflow infrastructure.

AOWNENG-74
Ownership analysis must not create an independent type or trait system.

AOWNENG-75
Ownership diagnostics expose semantic transition causes.

AOWNENG-76
Ownership diagnostics have stable machine-readable identifiers.

AOWNENG-77
AI tooling may query structured ownership facts.

AOWNENG-78
AI-generated code cannot bypass ownership verification.

AOWNENG-79
Invalid MIR cannot become Verified MIR through ownership analysis fallback.

AOWNENG-80
Ownership verification is a prerequisite for optimization.

AOWNENG-81
No mandatory runtime ownership tracking is generated for safe programs.

AOWNENG-82
Axiom does not require programmer-written lifetime or borrow annotations for ownership verification.

AOWNENG-83
Physical storage location is independent from semantic ownership.

AOWNENG-84
Heap allocation is not implied by ownership.

AOWNENG-85
Ownership transfer may be implemented without physical copying.

AOWNENG-86
Copy may be implemented without a physical copy when semantics permit.

AOWNENG-87
Drop semantics are independent from physical deallocation.

AOWNENG-88
Ownership state is independent from object headers and tracing GC.

AOWNENG-89
Ownership analysis preserves source provenance.

AOWNENG-90
Ownership proofs must survive CFG canonicalization without semantic weakening.

AOWNENG-91
Cleanup paths must exist for all applicable exits.

AOWNENG-92
Return, break, continue and panic paths participate in ownership cleanup.

AOWNENG-93
Unwind cleanup, when enabled, must preserve exactly-once ownership semantics.

AOWNENG-94
Abort profiles may omit unwind machinery without changing ownership semantics.

AOWNENG-95
Partial initialization is represented explicitly where required.

AOWNENG-96
Partial ownership is represented explicitly where required.

AOWNENG-97
Array and aggregate analysis may use compressed representations without weakening correctness.

AOWNENG-98
Runtime collection internals are responsible for runtime element ownership invariants.

AOWNENG-99
Ownership summaries participate in semantic fingerprints when externally observable.

AOWNENG-100
Only MIR whose ownership obligations are proven may enter the next verification stage.
```

---

# 131. Kết luận kiến trúc

Sau BOOTSTRAP-281, Axiom đã có một nền tảng ownership rất khác Rust ở **trải nghiệm lập trình**, nhưng vẫn giữ được phần mạnh nhất của ownership:

```text
Rust-style safety guarantees
        +
compiler-managed lifetime inference
        +
no lifetime syntax
        +
no mandatory GC
        +
no mandatory RC
        +
no runtime ownership bookkeeping
        +
field-sensitive analysis
        +
zero-cost physical realization
```

Mô hình cốt lõi có thể cô đọng thành:

```text
                 VALUE
                   │
          ┌────────┴────────┐
          ↓                 ↓
   INITIALIZATION       OWNERSHIP
          │                 │
          └────────┬────────┘
                   ↓
             MOVE / COPY
                   │
                   ↓
                DROP
                   │
                   ↓
             VERIFIED MIR
```

Điểm quan trọng nhất là **Axiom không loại bỏ ownership để đạt hiệu năng**. Nó loại bỏ **gánh nặng biểu diễn ownership khỏi programmer**, trong khi compiler vẫn giữ ownership như một proof system mạnh.

**BOOTSTRAP-281 được freeze.**

### Chuỗi tiếp theo

Theo dependency graph hiện tại, bước hợp lý tiếp theo là:

**BOOTSTRAP-282 — AXIOM CAPABILITY / VIEW / ALIAS ANALYSIS ENGINE**

Tập trung vào việc compiler tự chứng minh:

```text
view<T>
mut_view<T>
READ / WRITE
region overlap
DISJOINT
MAY_ALIAS
UNKNOWN
lifetime/provenance
relocation blocking
```

và quan trọng nhất: biến mô hình `view/mut_view` thành một cơ chế **đơn giản cho programmer nhưng đủ mạnh để optimizer tự suy ra `noalias`**, thay vì bắt người lập trình viết các annotation kiểu `restrict`/lifetime.