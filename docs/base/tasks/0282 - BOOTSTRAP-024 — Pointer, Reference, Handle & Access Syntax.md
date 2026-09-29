Tiếp tục với **BOOTSTRAP-024 — Pointer, Reference, Handle & Access Syntax**.

Mục tiêu của phần này là giải quyết đúng vấn đề bạn đã quan tâm từ đầu: **Axiom vẫn phải có toàn bộ sức mạnh mức máy của C/C++, nhưng lập trình viên bình thường không phải sống chung với `*`, `&`, lifetime, dangling reference, pointer arithmetic...**

---

# BOOTSTRAP-024 — Pointer, Reference, Handle & Access Syntax

## 1. Quyết định lớn

Tôi đề xuất Axiom **không có reference type kiểu C++ `T&` / `T&&` trong Core language**.

Thay vào đó:

| Khái niệm | Axiom |
|---|---|
| Giá trị | `T` |
| Read-only access | `view<T>` |
| Mutable access | `mut_view<T>` |
| Ownership | `T`, `Box<T>`, ... |
| Raw pointer | `*const T`, `*mut T` |
| Logical identity | `Handle<T>` |
| Function pointer | `fn(...) -> T` |
| Lifetime annotation | **Không có** |
| Pointer arithmetic | `unsafe` |
| Dereference raw pointer | `unsafe` |

Đây là một điểm rất quan trọng:

> **Reference không cần biến mất về mặt compiler semantics; chỉ cần biến mất khỏi programmer-facing model.**

Compiler vẫn có thể dùng khái niệm reference/place/provenance nội bộ để phân tích.

---

# 2. Ordinary code không cần pointer

Ví dụ:

```axiom
struct Player {
    hp: i32
    name: String
}

fn damage(player: mut_view<Player>, amount: i32) {
    player.hp -= amount
}

fn print_player(player: view<Player>) {
    println(player.name)
}

fn main() {
    var p = Player {
        hp: 100,
        name: "Hero"
    }

    damage(p, 20)
    print_player(p)
}
```

Lập trình viên không phải viết:

```text
&mut p
&p
*p
p->hp
```

Compiler tự hiểu:

```text
p
 ├── owner
 └── temporary mutable/read capability
```

khi gọi hàm.

Đây chính là cơ chế:

> **Implicit ephemeral owner → view conversion**

đã được chốt trong memory model.

---

# 3. Khi muốn lưu view thì phải nói rõ

Ví dụ:

```axiom
var player_view = view(p)
```

hoặc:

```axiom
var player_view = mut_view(p)
```

Điều này cố tình khác với implicit conversion.

### Tại sao?

Nếu mọi conversion đều implicit:

```axiom
var x = p
```

thì compiler phải suy luận:

- `x` là value?
- owner?
- view?
- mutable view?
- có escape không?
- lifetime bao lâu?

Điều đó làm semantic model khó đoán.

Axiom nên có nguyên tắc:

> **Implicit access chỉ tồn tại trong phạm vi lời gọi tức thời.**

Muốn tạo một capability có lifetime dài hơn expression hiện tại → viết rõ.

---

# 4. Không có `&T` / `&mut T`

Tôi đề xuất **không hỗ trợ**:

```axiom
&T
&mut T
```

trong safe Core.

Thay vào đó:

```axiom
view<T>
mut_view<T>
```

Ví dụ:

```axiom
fn sort(data: mut_view<[i32]>) {
    ...
}
```

và:

```axiom
fn sum(data: view<[i32]>) -> i64 {
    ...
}
```

Điểm mạnh là khi đọc code, capability rất rõ.

```text
T            → ownership/value
view<T>      → read access
mut_view<T>  → write access
*const T     → raw machine pointer
*mut T       → raw machine pointer
```

Không phải nhớ hàng loạt quy tắc của `&`, `&mut`, `&&`, `&&mut`, rvalue reference...

---

# 5. Raw pointer vẫn phải cực mạnh

Axiom không nên biến thành một ngôn ngữ "safe-only".

Cho phép:

```axiom
*const T
*mut T
```

nhưng đây là **machine-level abstraction**.

Ví dụ:

```axiom
unsafe fn read_value(p: *const i32) -> i32 {
    *p
}
```

Hoặc:

```axiom
unsafe fn write_value(p: *mut i32, value: i32) {
    *p = value
}
```

Pointer arithmetic:

```axiom
unsafe {
    let p2 = p + 4
}
```

Cũng được.

Nhưng đây không phải đường đi bình thường của application code.

---

# 6. Dereference chỉ có ý nghĩa với raw pointer

Có thể dùng:

```axiom
*p
```

với:

```axiom
*const T
*mut T
```

nhưng **không dùng `*` để biểu diễn reference**.

Điều này giúp `*` có đúng một ý nghĩa machine-level:

> **Dereference raw pointer.**

Không có tình trạng:

```text
*T
&T
&&T
*T&
T&&
```

với hàng loạt ngữ nghĩa khác nhau.

---

# 7. Có nên dùng `p->field` không?

Tôi đề xuất **có**.

Cho raw pointer:

```axiom
unsafe {
    p->next
}
```

tương đương semantic với:

```axiom
(*p).next
```

Nhưng:

```axiom
p->next
```

dễ đọc hơn nhiều trong system code.

Trong safe code:

```axiom
player.hp
```

Trong raw-pointer code:

```axiom
player_ptr->hp
```

Nhìn vào code lập tức biết abstraction level.

---

# 8. Address-of không nên là thao tác bình thường

Không nên biến:

```axiom
&x
```

thành syntax phổ biến.

Nếu thực sự cần raw address:

```axiom
unsafe {
    let p = address_of(x)
}
```

hoặc API system tương đương.

Lý do:

```text
value
   ↓
address
   ↓
raw pointer
   ↓
arithmetic
   ↓
dereference
```

là một **unsafe escape path**.

Nó nên nhìn thấy rõ trong source.

---

# 9. Raw pointer không sở hữu object

Đây là quy tắc cực quan trọng.

```axiom
*mut T
```

**không có ownership**.

Ví dụ:

```axiom
let p = ...
```

copy `p` không làm tăng ownership.

```text
Box<T>
    │
    ├── owner
    │
    ├── *mut T ──────┐
    ├── *mut T ──────┤ non-owning
    └── *const T ────┘
```

Nếu cần ownership:

```axiom
Box<T>
```

hoặc abstraction tương ứng.

Không bao giờ dùng raw pointer để biểu diễn ownership trong safe semantics.

---

# 10. Raw pointer có thể Copy

Tôi đề xuất:

```text
*const T : Copy
*mut T   : Copy
```

về mặt machine representation.

Nhưng:

> Copy raw pointer **không tạo thêm ownership và không tạo thêm safe access capability**.

Ví dụ:

```axiom
unsafe {
    let a = p
    let b = p
}
```

hoàn toàn hợp lệ.

Nhưng:

```axiom
*a
*b
```

vẫn chịu toàn bộ trách nhiệm unsafe.

Điều này phản ánh đúng bản chất machine pointer.

---

# 11. Chuyển raw pointer → view phải qua unsafe boundary

Ví dụ:

```axiom
unsafe {
    let p: *mut i32 = ...
    let v = assume_mut_view(p, 10)
}
```

Compiler không thể tự biết:

- pointer có hợp lệ không
- alignment đúng không
- vùng nhớ có đủ 10 phần tử không
- object còn sống không
- có alias mutable khác không

Do đó programmer phải establish contract.

Sau đó:

```axiom
fn process(v: mut_view<[i32]>) {
    ...
}
```

phần safe code trở lại semantics bình thường.

Đây chính là:

> **Unsafe establishes trusted preconditions → safe verifier resumes.**

---

# 12. Unsafe không phải "tắt compiler"

Đây là điểm cần giữ rất chặt.

Sai:

```text
unsafe {
    compiler stops checking everything
}
```

Đúng:

```text
unsafe
  ↓
programmer establishes machine-level invariant
  ↓
compiler records resulting capability
  ↓
safe verification continues
```

Ví dụ:

```axiom
unsafe {
    let v = assume_mut_view(ptr, len)
}

process(v)
```

Compiler vẫn phải kiểm tra:

- `v` không outlive provenance
- `v` không bị dùng sau invalidation
- `v` không xung đột capability khác
- `v` không được đưa vào context không hợp lệ

---

# 13. `Handle<T>` hoàn toàn khác pointer

Đây là abstraction tôi nghĩ Axiom nên coi trọng.

Ví dụ game engine:

```axiom
let player: Handle<Player> = world.spawn(Player {...})
```

Handle không phải:

```axiom
*Player
```

và cũng không phải:

```axiom
view<Player>
```

Nó là **logical identity**.

Ví dụ:

```text
Handle<Player>
      │
      ▼
EntityId + generation
      │
      ▼
World storage
      │
      ▼
Player
```

Object có thể di chuyển trong memory nhưng handle vẫn giữ identity.

Điều này rất hữu ích cho:

- game
- ECS
- GUI
- resource manager
- asset system
- async jobs
- database/cache
- object pools

và giảm đáng kể nhu cầu programmer tự quản lý pointer.

---

# 14. Ba loại identity cần giữ riêng

Axiom hiện có mô hình rất sạch:

### Value identity

```axiom
Player
```

"Đây là một giá trị."

### Storage identity

```axiom
Box<Player>
Pool<Player>
Arena<Player>
```

"Object này có storage identity."

### Logical identity

```axiom
Handle<Player>
EntityId
```

"Object này có identity độc lập với địa chỉ memory."

Không được đồng nhất:

```text
address == identity
```

Đây là một sai lầm thiết kế phổ biến trong các hệ thống pointer-heavy.

---

# 15. Stable address

Nếu programmer thật sự cần địa chỉ ổn định:

```axiom
Box<T>
Pool<T>
Static<T>
```

hoặc abstraction chuyên dụng.

Nhưng:

```axiom
Vec<T>
```

vẫn có quyền relocate.

Ví dụ:

```axiom
let x = vec[0]
vec.push(y)
```

Compiler/runtime không cần hứa rằng địa chỉ của `vec[0]` vẫn giống cũ.

Nếu đang có:

```axiom
let v = mut_view(vec[0])
```

thì relocation sẽ bị chặn bởi capability rules.

---

# 16. Không có `Pin<T>` trong Core

Tôi tiếp tục giữ quyết định này.

Không đưa:

```axiom
Pin<T>
```

vào Core.

Thay vào đó:

> **Stable address là storage contract.**

Nếu một abstraction cần stable address:

```text
Box
Pool
Static
TLS
PinnedStorage (library)
```

nó tự cung cấp contract.

Điều này tránh biến một vấn đề rất đặc thù thành một khái niệm mà mọi lập trình viên phải hiểu.

---

# 17. Slice/view syntax

Đây là phần nên làm rất đẹp.

Ví dụ:

```axiom
fn sum(values: view<[i32]>) -> i32 {
    var total = 0

    for x in values {
        total += x
    }

    return total
}
```

Mutable:

```axiom
fn clear(values: mut_view<[u8]>) {
    for i in 0..values.len {
        values[i] = 0
    }
}
```

Compiler biết:

```text
view<[T]>
    READ capability
    contiguous region

mut_view<[T]>
    WRITE capability
    contiguous region
```

Không cần:

```text
pointer + length
iterator lifetime
borrow lifetime
```

trong source.

---

# 18. Array và view phải khác nhau

```axiom
let a: [i32; 1024]
```

là **array value**.

Còn:

```axiom
let v: view<[i32]>
```

là **access capability**.

Ví dụ:

```axiom
fn process(x: view<[i32]>) { ... }

let a = [1, 2, 3, 4]

process(a)
```

compiler tạo ephemeral view.

Không copy toàn bộ array.

---

# 19. `mut_view` là capability độc quyền

Ví dụ:

```axiom
let a = [1, 2, 3]

let x = mut_view(a)
let y = mut_view(a)
```

→ lỗi.

Nhưng:

```axiom
let x = mut_view(a[0..2])
let y = mut_view(a[2..3])
```

có thể hợp lệ nếu compiler chứng minh:

```text
[0,2) ∩ [2,3) = ∅
```

Điều này rất quan trọng cho optimizer.

Compiler có thể biết:

```text
x and y cannot alias
```

mà programmer không cần viết `restrict`.

---

# 20. Function parameter là nơi implicit view phát huy tác dụng

Đây là UX tôi muốn chốt:

```axiom
fn update(x: mut_view<T>)
```

cho phép:

```axiom
update(object)
```

Compiler tự tạo ephemeral capability.

Nhưng không cho:

```axiom
let x: mut_view<T> = object
```

một cách implicit.

Muốn lưu:

```axiom
let x = mut_view(object)
```

Như vậy syntax đơn giản nhưng semantics vẫn deterministic.

---

# 21. FFI

Raw pointer trở thành cầu nối rất tự nhiên.

Ví dụ C API:

```axiom
extern "C" {
    fn memcpy(
        dst: *mut u8,
        src: *const u8,
        size: usize
    )
}
```

Wrapper Axiom có thể cung cấp API an toàn hơn:

```axiom
fn copy(
    dst: mut_view<[u8]>,
    src: view<[u8]>
) -> Result<(), CopyError> {
    ...
}
```

Như vậy:

```text
C ABI
  ↓
raw pointer
  ↓
unsafe wrapper
  ↓
Axiom capability
  ↓
safe application code
```

Đây nên là pattern chuẩn của ecosystem.

---

# 22. Pointer null

Không nên biến `null` thành giá trị bình thường của safe Axiom.

Raw pointer có thể biểu diễn null ở unsafe/FFI.

Safe code:

```axiom
Option<T>
```

hoặc:

```axiom
Option<Handle<T>>
```

tùy semantics.

Đối với C ABI nullable pointer, ABI layer có thể cho phép:

```text
*mut T
```

nhưng wrapper phải kiểm tra trước khi tạo capability.

Không nên bắt ABI C phải có representation giống `Option` nếu chưa có `@repr` contract.

---

# 23. Pointer vs Handle vs View

Tôi đề xuất bảng chính thức:

| Type | Ownership | Dereference | Stable address | Safe sharing |
|---|---:|---:|---:|---:|
| `T` | Có | Không | Không đảm bảo | Theo semantics |
| `Box<T>` | Có | Qua API | Có contract | Không mặc định |
| `view<T>` | Không | Có, safe | Phụ thuộc owner | Read |
| `mut_view<T>` | Không | Có, safe | Phụ thuộc owner | Exclusive |
| `*const T` | Không | Unsafe | Không đảm bảo | Không |
| `*mut T` | Không | Unsafe | Không đảm bảo | Không |
| `Handle<T>` | Không | Không trực tiếp | Không phụ thuộc | Qua API |
| `Arc<T>` | Shared owner | Qua API | Theo storage contract | Có, nếu `T: Share` |

Điều này tạo ra một abstraction hierarchy khá sạch.

---

# 24. Compiler internal model

Source:

```axiom
fn update(x: mut_view<Player>) {
    x.hp += 1
}
```

không nhất thiết MIR phải giữ nguyên `mut_view<Player>`.

Compiler có thể lower:

```text
MIR capability:
    owner = p
    region = Player
    access = WRITE
    lifetime = call
```

Sau verification:

```text
verified mutable access
```

Sau optimization:

```text
direct SSA/register access
```

Cuối cùng có thể thành:

```asm
add ...
```

Không có:

```text
view object
reference object
lifetime object
```

trong binary nếu chúng không observable.

Đây chính là **zero-cost capability abstraction**.

---

# 25. Các quy tắc chính của BOOTSTRAP-024

Tôi đề xuất đóng băng các invariant:

```text
APTR-20  Ordinary values do not require programmer-visible pointers.

APTR-21  Safe Core has no general reference type.

APTR-22  view<T> represents read capability.

APTR-23  mut_view<T> represents exclusive write capability.

APTR-24  Raw pointers are non-owning.

APTR-25  Raw pointers are unsafe access mechanisms.

APTR-26  Raw pointer dereference requires unsafe context.

APTR-27  Raw pointer arithmetic requires unsafe context.

APTR-28  Raw pointer copies do not transfer ownership.

APTR-29  Ownership is never represented by a raw pointer.

APTR-30  address-of raw storage is unsafe/system-level.

APTR-31  Owner-to-view implicit conversion is ephemeral only.

APTR-32  Stored views require explicit construction.

APTR-33  Views cannot outlive their provenance.

APTR-34  Mutable capabilities are exclusive.

APTR-35  Read capabilities may be duplicated.

APTR-36  Disjoint mutable regions may coexist.

APTR-37  Unknown overlap cannot be assumed disjoint.

APTR-38  Unsafe may establish capability preconditions.

APTR-39  Safe verification resumes after established unsafe contracts.

APTR-40  Unsafe does not disable structural compiler verification.

APTR-41  Pointer provenance is distinct from integer value.

APTR-42  Integer-to-pointer conversion is unsafe.

APTR-43  Null raw pointers are unsafe/FFI concerns.

APTR-44  Safe code uses Option for absence.

APTR-45  Handle is logical identity, not pointer identity.

APTR-46  Handle dereference is performed through its owning storage API.

APTR-47  Stable address is a storage contract.

APTR-48  Relocatable storage may move when no capability depends on its address.

APTR-49  Pin is not a Core primitive.

APTR-50  FFI may expose raw pointers through explicit ABI contracts.

APTR-51  FFI wrappers should establish safe capabilities.

APTR-52  view representation is compiler-controlled.

APTR-53  mut_view representation is compiler-controlled.

APTR-54  Capability metadata may disappear after verification.

APTR-55  Capability abstraction must not require runtime overhead.

APTR-56  Raw pointers do not imply Send or Share.

APTR-57  Handle safety is independent of physical address.

APTR-58  Logical identity survives storage relocation when contract permits.

APTR-59  Pointer operations cannot bypass ownership semantics in safe code.

APTR-60  Pointer semantics are target-aware but Core rules are target-independent.
```

---

# 26. Kết luận kiến trúc

Tôi nghĩ đây là hướng rất phù hợp với mục tiêu Axiom:

```text
                         Axiom
                           │
              ┌────────────┴────────────┐
              │                         │
         Normal code              System code
              │                         │
          T / struct              *const T
              │                    *mut T
        view<T>                    unsafe
        mut_view<T>                    │
              │                         │
              └──────────┬──────────────┘
                         │
                     Compiler
                         │
              Ownership / Capability
                  / Alias / Lifetime
                         │
                         ▼
                       MIR
                         │
                         ▼
                  optimized machine
```

**Điểm quan trọng nhất:** Axiom không cố "loại bỏ pointer khỏi máy". Nó chỉ **đẩy pointer xuống đúng tầng mà nó thuộc về**.

Application code:

```axiom
player.hp += 10
```

Systems code:

```axiom
unsafe {
    p->hp += 10
}
```

Cả hai cuối cùng đều có thể sinh ra cùng machine code.

Nhưng chỉ tầng thứ hai buộc lập trình viên chịu trách nhiệm về machine-level invariants.

---

## BOOTSTRAP-024 hoàn tất

Với phần này, ta đã gần như khóa xong **memory/access model** của Axiom:

**Value → Ownership → Capability → Pointer → Storage → Lifetime → Concurrency → ABI**

Bước tiếp theo hợp lý là **BOOTSTRAP-025 — Type System hoàn chỉnh**, tập trung vào phần hiện còn thiếu để compiler có thể thực sự vận hành:

- `struct`
- `enum`
- `trait`
- generic
- associated type
- associated const
- type alias
- newtype
- `Option` / `Result`
- function type
- closure type
- `dyn Trait`
- generic dispatch vs dynamic dispatch
- type inference
- coercion/conversion
- operator overloading
- `Copy/Clone/Drop/Send/Share`
- specialization/monomorphization

Đây sẽ là phần rất quan trọng vì nó quyết định **Axiom có thực sự đơn giản hơn C++ nhưng vẫn đủ mạnh để xây OS/game/AI framework/compiler hay không**.