Tiếp theo, ta nên **đóng API và semantics của `Box`, `Vec`, `Arena`, `Pool`**. Đây là bước quan trọng hơn việc thiết kế syntax, vì nếu các primitive này đúng thì phần lớn collection/memory library phía trên sẽ tự nhiên.

# Axiom Storage API v0.1

## 1. Một nguyên tắc trước khi thiết kế API

Tôi đề xuất không để programmer phải suy nghĩ:

> “Object này đang ở heap hay stack?”

Mà chỉ cần nghĩ:

> “Tôi cần ownership nào và storage contract nào?”

Có 4 nhu cầu thực tế:

| Nhu cầu | Abstraction |
|---|---|
| Giá trị bình thường | `T` |
| Một object sở hữu độc lập, địa chỉ ổn định | `Box<T>` |
| Dãy phần tử contiguous, có thể tăng giảm | `Vec<T>` |
| Nhiều object cùng lifetime | `Arena<T>` |
| Nhiều object cùng kích thước, reuse nhanh | `Pool<T>` |

---

# 2. `Box<T>`

Semantic tối giản:

```axiom
let x = Box.new(Foo(...))
```

`x` là **owner**.

```text
x ─────owns────→ Foo
```

Assignment:

```axiom
let y = x
```

không copy `Foo`.

```text
x = MOVED

y ─────owns────→ Foo
```

## API đề xuất

```axiom
Box.new(value)
Box.get(box) -> view<T>
Box.get_mut(box) -> mut_view<T>
Box.into_value(box) -> T
```

Nhưng method syntax cho phép:

```axiom
x.get()
x.get_mut()
```

`Box.get()` không tạo ownership mới.

---

# 3. Có cần `Box<T>.deref()` không?

**Không nên.**

Đây là kiểu API dễ khiến programmer phải học một abstraction reference/dereference.

Axiom nên cho phép:

```axiom
let b = Box.new(Foo(...))

b.method()
b.field
```

Compiler tự hiểu access vào object được Box sở hữu.

Ví dụ:

```axiom
let b = Box.new(Player(...))

b.hp -= 10
b.move()
```

Semantically:

```text
Box owner
   ↓
owned T
   ↓
temporary mutable capability
```

Không cần viết:

```text
*b
&mut *b
```

Đây là một điểm khác biệt UX rất đáng giá so với Rust/C++.

---

# 4. Nhưng Box có stable address

Nếu:

```axiom
let b = Box.new(Foo(...))
```

thì storage identity của `Foo` ổn định.

Move Box:

```axiom
let c = b
```

chỉ chuyển ownership handle.

Object không relocation.

```text
Before:

b ──→ allocation #7

After:

c ──→ allocation #7
```

Điều này cho phép cấu trúc self-referential/system-level object về mặt storage.

Tuy nhiên safe Axiom vẫn không cho programmer tự tạo dangling raw pointer.

---

# 5. `Vec<T>`

Đây là abstraction cần thiết kế cẩn thận nhất.

Semantic:

```text
Vec<T>
 ├── owns elements
 ├── contiguous
 ├── length
 ├── capacity
 └── relocatable
```

Ví dụ:

```axiom
var xs = Vec<i32>()

xs.push(10)
xs.push(20)
xs.push(30)
```

---

# 6. `push`

```axiom
xs.push(40)
```

có thể:

```text
capacity đủ:
    append

capacity thiếu:
    allocate new storage
    move elements
    release old storage
```

Do đó:

```text
Vec<T> ≠ stable-address container
```

---

# 7. Nhưng `push` không nhất thiết luôn relocate

Compiler/library có thể có:

```text
MAY_RELOCATE
```

như một semantic effect.

Đây là một concept tôi nghĩ rất hữu ích cho compiler.

Ví dụ:

```text
Vec.push
Vec.insert
Vec.resize
Vec.reserve
```

có thể mang:

```text
StorageEffect = MAY_RELOCATE
```

trong semantic metadata.

Còn:

```text
Vec[index]
```

thường:

```text
StorageEffect = NO_RELOCATE
```

---

# 8. View vào Vec

```axiom
let first = view(xs)
```

`first` là capability tới storage hiện tại.

Nếu:

```axiom
print(first)

xs.push(100)
```

compiler thấy `first` đã hết last-use trước `push`.

→ hợp lệ.

Nhưng:

```axiom
let first = view(xs)

xs.push(100)

print(first)
```

→ lỗi.

Diagnostic nên nói theo ngôn ngữ programmer:

```text
AX_VIEW_0007:
`xs.push(...)` may relocate the storage referenced by `first`,
but `first` is still in use.

End or consume `first` before this operation,
or use a stable storage container.
```

Không cần nói:

```text
borrow checker
lifetime 'a
```

---

# 9. `Vec.get()`

Tôi đề xuất:

```axiom
xs.get(i) -> Option<view<T>>
```

nhưng trong thực tế syntax indexing:

```axiom
xs[i]
```

sẽ tiện hơn.

Semantic:

```axiom
let x = xs[i]
```

Nếu `T` là Copy:

```text
COPY value
```

Nếu `T` không Copy:

không được âm thầm move element qua indexing thông thường.

Đây là chỗ cần phân biệt:

```axiom
xs[i]
```

với:

```axiom
xs.remove(i)
```

`remove()` mới là operation ownership-transfer rõ ràng.

---

# 10. Tránh "move out of index" mặc định

Ví dụ:

```axiom
var files = Vec<File>()

let f = files[0]
```

Không nên hiểu là:

```text
take ownership of files[0]
```

vì nó tạo ra rất nhiều vấn đề với container invariant.

Thay vào đó:

```axiom
let f = files.remove(0)
```

hoặc:

```axiom
let f = files.take(0)
```

là explicit ownership extraction.

Đây là một quyết định UX rất tốt.

---

# 11. API Vec đề xuất

Core collection API ban đầu:

```axiom
Vec.new()
Vec.with_capacity(n)

push(value)
pop() -> Option<T>

insert(index, value)
remove(index) -> T

clear()
len()
capacity()

reserve(n)
shrink_to_fit()

is_empty()

get(index) -> Option<view<T>>
get_mut(index) -> Option<mut_view<T>>

view()
mut_view()
```

Ngoài ra:

```axiom
first()
last()
first_mut()
last_mut()
```

là convenience API.

---

# 12. `remove()` và relocation

```axiom
let x = xs.remove(i)
```

có thể:

```text
elements after i shift left
```

nên những view tới các element liên quan có thể bị invalidated.

Compiler không cần theo dõi từng element bằng địa chỉ vật lý.

Nó chỉ cần biết:

```text
Vec storage mutation
```

có thể invalidates dependent views.

Đây là abstraction rất mạnh:

> Compiler theo dõi **capability dependency**, không theo dõi pointer arithmetic của implementation.

---

# 13. `swap_remove`

Nên có:

```axiom
xs.swap_remove(i)
```

Semantic:

```text
remove element i
move last element into i
O(1)
```

Đây là API rất hữu ích cho game/engine/data-oriented code.

---

# 14. `Arena`

API có thể rất đơn giản:

```axiom
let arena = Arena.new()

let a = arena.alloc(Node(...))
let b = arena.alloc(Node(...))
```

`alloc()` trả về:

```text
view<T>
```

hoặc một **arena-owned handle/capability**, tùy API cuối cùng.

Tôi nghiêng về:

```axiom
let a = arena.alloc(Node(...))
```

trả về một **stable owning arena handle** thay vì raw view.

Ví dụ:

```axiom
a.value
a.field
```

Arena vẫn là owner thật sự.

---

# 15. Tại sao không trả `Box<T>` từ Arena?

Vì:

```text
Box<T>
```

ngụ ý:

```text
T có ownership độc lập
```

Trong Arena:

```text
Arena
 ├── T
 ├── T
 ├── T
 └── ...
```

Arena mới là owner.

Nếu trả Box, programmer có thể hiểu nhầm rằng:

```text
drop(box)
```

sẽ release riêng allocation.

Không đúng với arena semantics.

Do đó nên có:

```text
ArenaHandle<T>
```

hoặc một abstraction tương đương.

---

# 16. Nhưng có cần một type `ArenaHandle<T>` không?

Có thể tránh nếu thiết kế:

```axiom
let n = arena.alloc(Node(...))
```

và compiler biết:

```text
n provenance → arena
```

Tuy nhiên tôi nghĩ **một type rõ ràng vẫn tốt hơn**.

Ví dụ:

```axiom
Arena<T>
ArenaRef<T>
```

Nhưng `ArenaRef<T>` không nên là reference/lifetime abstraction kiểu Rust.

Nó đơn giản là:

> handle tới allocation thuộc một Arena cụ thể.

---

# 17. Arena không được escape

Ví dụ:

```axiom
fn create() -> ArenaRef<Node> {
    let arena = Arena.new()
    return arena.alloc(Node(...))
}
```

Compiler reject.

Diagnostic:

```text
AX_ARENA_0001:
Arena-owned value cannot escape its Arena.
```

Không cần bắt programmer viết lifetime.

---

# 18. Pool

Pool phù hợp:

```axiom
let pool = Pool<Node>.new()

let a = pool.alloc(...)
let b = pool.alloc(...)
```

Khi:

```axiom
pool.release(a)
```

slot được recycle.

Một abstraction thú vị:

```text
PoolHandle<T>
```

có thể chứa:

```text
slot index + generation
```

nhưng đó là implementation detail.

Compiler/library có thể dùng generation để phát hiện stale handles trong debug.

Release build có thể tối ưu nếu safe semantics đã đảm bảo.

---

# 19. `PoolHandle<T>` khác `Box<T>`

### Box

```text
ownership
one allocation
stable address
destruction of T on owner drop
```

### PoolHandle

```text
pool owns storage
handle identifies slot
pool controls allocation/reuse
```

Điều này rất phù hợp cho:

- ECS
- game engine
- entity systems
- UI objects
- networking objects
- object pools.

---

# 20. Có cần `Rc`/`Arc` ngay không?

Nên có **library**, nhưng không nên làm memory primitive.

```axiom
Arc<T>
```

là:

```text
explicit shared ownership
```

và:

```axiom
let a = Arc.new(data)
let b = a.clone()
```

`clone()` ở đây là explicit.

Không:

```axiom
let b = a
```

rồi compiler tự tăng refcount.

Điều đó giữ được tính predictable.

---

# 21. Shared mutable data

Không:

```axiom
Arc<T>
```

→ tự động mutable.

Muốn:

```axiom
Arc<Mutex<T>>
```

hoặc:

```axiom
Arc<RwLock<T>>
```

hoặc atomic abstraction.

Như vậy:

```text
Arc = ownership sharing
Mutex = mutation synchronization
```

hai vấn đề không bị trộn.

---

# 22. Allocator trait nên nằm ở đâu?

Tôi đề xuất:

```text
Core
    ↓
Memory primitives/intrinsics

Core Library
    ↓
Allocator trait
    ↓
Box / Vec / Arena / Pool

Std
    ↓
OS allocator
    ↓
thread allocator
    ↓
specialized allocators
```

Core không cần:

```text
malloc
free
allocator object
```

---

# 23. Allocator không nên bắt buộc generic ở mọi collection

Đây là một điểm dễ làm API Axiom trở nên xấu.

Không nên biến:

```axiom
Vec<T>
```

thành:

```axiom
Vec<T, GlobalAllocator>
```

trong source code thông thường.

Có thể compiler/library có default allocator:

```axiom
Vec<T>
```

và advanced API:

```axiom
Vec.with_allocator<T>(allocator)
```

hoặc một storage policy khác.

Mục tiêu:

```text
90% code:
Vec<T>

10% systems code:
explicit allocator
```

---

# 24. Một điểm còn quan trọng hơn: relocation semantics không nên là effect mà programmer phải khai báo

Tôi muốn chỉnh một chút so với phần trước.

`MAY_RELOCATE` nên là **compiler-internal semantic property**, không phải syntax:

```axiom
fn push(...) !relocate
```

Programmer không cần học effect annotation.

Compiler biết:

```text
Vec.push → MAY_RELOCATE
Box.get → NO_RELOCATE
Arena.alloc → STABLE
```

và verifier dùng thông tin đó.

Đây chính là:

> **Compiler Complexity Is Not Language Complexity.**

---

# 25. `StableAddress` cũng không nên là trait thông thường

Không nên yêu cầu:

```axiom
trait StableAddress
```

rồi programmer implement nó tùy ý.

Vì đây là **semantic storage guarantee**.

Nếu user tự implement sai:

```axiom
impl StableAddress for MyMovingContainer
```

compiler không thể tin.

Do đó stable-address property nên xuất phát từ **trusted storage abstractions / compiler-known contracts**.

---

# 26. Một abstraction rất mạnh: `storage<T>`

Tôi thậm chí nghĩ Axiom có thể có internal semantic notion:

```text
StorageIdentity
```

MIR:

```text
ALLOC storage #17
```

Views giữ:

```text
provenance → storage #17
region → [offset,length]
```

Khi:

```text
Vec reallocates
```

thì:

```text
storage #17
      ↓
storage #23
```

View cũ vẫn trỏ về #17 và trở thành invalid sau operation.

Compiler có thể verify điều này **mà không cần mô hình hóa pointer lifetime kiểu Rust**.

---

# 27. Điều này làm verifier rất sạch

Ví dụ:

```axiom
var xs = Vec<i32>()

let a = view(xs)

xs.push(10)

print(a)
```

MIR:

```text
ALLOC storage#1
VIEW storage#1 → cap#1

CALL Vec.push
    MAY_RELOCATE storage#1

USE cap#1
```

Verifier:

```text
cap#1 ACTIVE
       ↓
MAY_RELOCATE
       ↓
cap#1 invalidated
       ↓
USE
       ↓
ERROR
```

Không cần lifetime parameter.

Không cần borrow checker syntax.

---

# 28. Nhưng nếu compiler biết `push` không relocate?

Ví dụ capacity đủ và implementation chứng minh:

```text
len < cap
```

thì theoretically:

```text
push
```

không relocate.

Compiler có thể giữ view.

Đây là một optimization có thể làm rất sâu.

Nhưng **không nên biến điều này thành semantic guarantee của `Vec.push`**.

API vẫn:

```text
MAY_RELOCATE
```

để code không phụ thuộc vào implementation detail.

Compiler chỉ được phép relax constraint khi chứng minh operation thực tế không gây relocation trong execution path.

---

# 29. Đây là distinction rất quan trọng

```text
Semantic guarantee:
    push MAY relocate

Compiler knowledge:
    this particular push cannot relocate
```

Nếu compiler biết chắc:

```text
capacity = 100
len = 3
push 4
```

nó có thể tối ưu.

Nhưng programmer không được viết code phụ thuộc vào điều đó.

---

# 30. Tổng thể Memory API

Tôi đề xuất baseline:

```text
                    OWNERSHIP
                       │
        ┌──────────────┼──────────────┐
        │              │              │
       T             Box<T>        Shared<T>
        │              │              │
     inline        stable owner    shared owner
                       │
                ┌──────┴───────┐
                │              │
              Arena          Pool
                │              │
             region          slots
             
Vec<T>
  │
  ├── owned
  ├── contiguous
  └── relocatable
```

Views:

```text
T owner
 │
 ├── view<T>
 └── mut_view<T>
```

Và tuyệt đối không có:

```text
GC
implicit RC
implicit pointer
implicit borrow syntax
implicit heap
implicit stable address
```

---

## Tôi sẽ chốt thêm một nguyên tắc cho Axiom

### **Storage Choice Is Not Ownership Choice**

Hai thứ này phải độc lập.

Ví dụ:

```axiom
let x = Foo(...)
```

`x` có ownership.

Nhưng compiler tự chọn:

```text
register
stack
inline
heap
```

Còn:

```axiom
let x = Box.new(Foo(...))
```

thì programmer đang yêu cầu **dynamic owning storage semantics**, và `Box` cung cấp stable storage identity.

Đây là ranh giới rất đẹp giữa high-level code và systems code.

---

### Và một nguyên tắc nữa:

> **Stable address phải trả giá bằng một semantic constraint; nhưng programmer chỉ cần yêu cầu nó khi thực sự cần.**

Nếu không cần địa chỉ ổn định, Axiom được phép relocation, scalarize, stack-promote, eliminate allocation, caller-allocate return, v.v.

Nếu cần, dùng `Box`, `Arena`, `Pool` hoặc external storage phù hợp.

Như vậy ta tránh được cả hai cực:

```text
C/C++:
programmer quá dễ vô tình quản lý address/lifetime

Rust:
programmer thường xuyên phải đối mặt với reference/lifetime constraints
```

Axiom nằm ở giữa:

```text
                    Axiom
                      │
       programmer ────┼──── compiler
                      │
            ownership intent
                      │
                 inferred lifetime
                      │
                verified safety
                      │
             optimized storage
```

**Bước tiếp theo nên đi vào một phần còn quan trọng hơn nữa: `String/Text/Bytes`, `Array/Slice/View` và Data-Oriented Collections.** Đây là nơi quyết định Axiom có thể vừa nhanh như C/C++ vừa tránh được sự lằng nhằng của pointer/reference trong code thực tế hay không.