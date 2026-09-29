Tiếp tục từ **Axiom Ownership & Effect Verifier v0.1**, bước hợp lý nhất bây giờ là **đập phá semantics bằng các chương trình adversarial** trước khi viết compiler.

Mục tiêu không phải chứng minh Axiom “đúng”, mà tìm ra những trường hợp mà quy tắc hiện tại **mâu thuẫn, quá chặt, hoặc cho phép lỗi**.

## 1. Partial move + dùng toàn bộ struct

```axiom
struct User {
    name: String
    age: i32
}

fn test(mut user: User) {
    let name = user.name
    print(user.age)
    print(user)
}
```

### Phân tích

Sau:

```axiom
let name = user.name
```

trạng thái:

```text
user
├── name → MOVED
└── age  → OWNED
```

Do đó:

```axiom
print(user.age)
```

**HỢP LỆ**

Nhưng:

```axiom
print(user)
```

**LỖI**

vì `user` không còn là một giá trị hoàn chỉnh.

Verifier:

```text
user.name : MOVE
    ↓
user.name = MOVED
user.age  = OWNED
user      = PARTIAL
```

Đây là semantics tốt và nên giữ.

---

# 2. Partial move + Drop

Đây mới là case nguy hiểm.

```axiom
struct FileData {
    file: File
    data: Buffer<u8>
}

fn test(x: FileData) {
    let file = x.file
}
```

Cuối scope, compiler phải drop:

```text
file      → DROP
x.data    → DROP
x.file    → ??? already MOVED
x         → ??? 
```

Không được phép:

```text
DROP x
```

nếu `DROP x` lại drop `file`.

Vì vậy Drop elaboration phải hiểu **field ownership state**.

### MIR

```text
%x.file = FIELD %x
%file   = MOVE %x.file

...

DROP %file
DROP %x.data
```

Không có:

```text
DROP %x
```

### Kết luận

Axiom cần một invariant mạnh:

> **DROP của aggregate phải được elaboration thành các phần còn sở hữu; không được giả định aggregate vẫn nguyên vẹn.**

Đây nên trở thành:

```text
AOV-16:
Drop elaboration MUST be ownership-aware and partial-move-safe.
```

---

# 3. Branch move

```axiom
fn test(x: Buffer<u8>, flag: bool) {
    if flag {
        consume(x)
    }

    use(x)
}
```

CFG:

```text
       flag?
      /     \
     /       \
 MOVE x      OWNED x
     \       /
      \     /
       JOIN
         |
       use(x)
```

Tại JOIN:

```text
OWNED + MOVED
```

không thể coi là `OWNED`.

Verifier:

```text
x = MAYBE_MOVED
```

→

```text
use(x)
```

**REJECT**

Đây là hành vi bắt buộc.

---

# 4. Branch move nhưng mọi nhánh đều move

```axiom
fn test(x: Buffer<u8>, flag: bool) {
    if flag {
        consume(x)
    } else {
        consume(x)
    }
}
```

Hai nhánh:

```text
true  → MOVED
false → MOVED
```

JOIN:

```text
MOVED + MOVED = MOVED
```

Do đó hợp lệ.

Đây là lý do verifier phải là **dataflow analysis**, chứ không thể chỉ kiểm tra lexical scope.

---

# 5. Loop move

```axiom
fn test(x: Buffer<u8>) {
    while condition() {
        consume(x)
    }
}
```

Iteration 1:

```text
x → MOVED
```

Iteration 2:

```text
consume(x)
```

không hợp lệ.

Verifier phải phát hiện fixed point:

```text
ENTRY
  ↓
OWNED
  ↓
LOOP
  ↓
MOVED
  ↓
back-edge
  ↓
LOOP
```

→ reject.

---

## Nhưng trường hợp này phải hợp lệ

```axiom
fn test(mut x: Buffer<u8>) {
    while condition() {
        let tmp = move x
        consume(tmp)

        x = Buffer.new()
    }
}
```

Mỗi iteration:

```text
OWNED
 ↓
MOVE
 ↓
MOVED
 ↓
REINIT
 ↓
OWNED
```

Vì vậy verifier cần phân biệt:

```text
MOVED
```

với:

```text
MOVED + REINITIALIZED
```

Đây là một điểm rất quan trọng cho usability.

---

# 6. Hai field độc lập

```axiom
struct Person {
    name: String
    age: i32
}

fn test(mut p: Person) {
    modify(p.name)
    p.age = 20
}
```

Nếu:

```text
modify(p.name)
```

chỉ:

```text
WRITE(p.name)
```

thì:

```text
WRITE(p.name)
WRITE(p.age)
```

không conflict.

Region:

```text
Person
├── R1 = name
└── R2 = age

R1 ∩ R2 = ∅
```

→ **ACCEPT**

Đây là một ưu điểm rất lớn của region-based verifier.

---

# 7. Nhưng whole-object write phải conflict

```axiom
fn reset(mut p: Person) {
    p = Person.new()
}
```

Trong lúc một view đang tồn tại:

```axiom
let age = view(p.age)

reset(p)
```

Verifier thấy:

```text
READ  p.age
WRITE p
```

vì:

```text
p contains p.age
```

→ conflict.

**REJECT**

Đây chính là lý do quan hệ region phải có:

```text
SAME
DISJOINT
CONTAINS
CONTAINED_BY
OVERLAPS
```

chứ chỉ có “cùng biến / khác biến” là không đủ.

---

# 8. Vec + view — điểm nguy hiểm nhất

```axiom
var v = Vec.new()

v.push(10)

let x = view(v)

v.push(20)

print(x)
```

Nếu `push()` có thể realloc:

```text
old buffer
    ↓
[10]
    ↓
reallocation
    ↓
[new buffer]
```

thì `x` trở thành dangling view.

Axiom phải reject:

```text
ACTIVE VIEW x
      ↓
v.push()
      ↓
possible reallocation
```

Nhưng:

```axiom
var v = Vec.with_capacity(100)

let x = view(v)

v.push(20)
```

vẫn **không nhất thiết** an toàn, vì semantics của `push` có thể thay đổi length nhưng không nhất thiết invalidate pointer.

Điều này cho thấy:

> **View validity phải phụ thuộc vào contract của operation, không chỉ tên operation.**

Ví dụ:

```text
Vec.push:
    WRITE length
    MAY_REALLOCATE storage
```

Verifier thấy `MAY_REALLOCATE` → invalidates existing views.

Một API khác:

```text
Vec.push_no_grow:
    WRITE element
    WRITE length
    NO_REALLOCATE
```

→ có thể cho phép.

---

# 9. Đây là nơi Axiom nên tránh một cái bẫy

Không nên bắt programmer viết:

```axiom
borrow(v)
borrow_mut(v)
lifetime(...)
```

Thay vào đó API chỉ cần khai báo semantic contract.

Ví dụ nội bộ:

```text
push:
    WRITE(self.storage)
    WRITE(self.length)
    MAY_REALLOCATE(self.storage)
```

Compiler tự biết.

Programmer chỉ thấy:

```axiom
v.push(x)
```

Đây chính xác là triết lý:

> **Explicit at semantic boundaries, implicit within the compiler.**

---

# 10. View trả về từ function

```axiom
fn first(v: view<i32>) -> view<i32> {
    return v.slice(0, 1)
}
```

Hợp lệ.

Nhưng:

```axiom
fn make() -> view<i32> {
    var x = Array<i32, 10>()
    return view(x)
}
```

phải **REJECT**.

Vì:

```text
x
 ↓
local owner
 ↓
function returns
 ↓
x destroyed
 ↓
view dangling
```

Verifier phải theo dõi **provenance**:

```text
view V
    provenance = x
    region = x[0..10]
```

Khi `x` chết trước `V`:

```text
INVALID
```

---

# 11. Helper function không được “che giấu” dangling view

Case khó hơn:

```axiom
fn make_view() -> view<i32> {
    var x = Array<i32, 10>()
    return helper(x)
}

fn helper(x: view<i32>) -> view<i32> {
    x
}
```

Compiler **không được** chỉ nhìn `helper()` rồi bỏ qua provenance.

Phải truyền provenance xuyên function boundary:

```text
make_view
    x
    ↓
helper
    ↓
view provenance = x
    ↓
return
    ↓
REJECT
```

Đây là lý do effect/ownership summary phải chứa **region/provenance relation**, không chỉ:

```text
READ(arg0)
```

mà còn có dạng:

```text
RETURN_VIEW_FROM(arg0)
```

---

# 12. Closure capture

```axiom
fn make_task(x: Buffer<u8>) -> Task {
    return || {
        use(x)
    }
}
```

Closure escape khỏi function.

Compiler thấy:

```text
closure lifetime > x lexical lifetime
```

Không thể capture bằng view.

Nhưng có thể capture bằng ownership:

```text
closure environment:
    x: OWNED
```

Compiler tự chuyển capture mode:

```text
VIEW       → invalid
COPY       → nếu Copy
MOVE       → valid
```

Do đó:

```text
non-escaping closure
    ↓
VIEW capture có thể OK

escaping closure
    ↓
VIEW capture phải chứng minh owner sống đủ lâu
```

Nếu không:

```text
compiler error
```

hoặc compiler có thể **tự chọn capture-by-value** nếu semantics của chương trình cho phép.

---

# 13. Async là adversarial test rất quan trọng

```axiom
async fn work(x: Buffer<u8>) {
    await network()

    use(x)
}
```

`x` sống qua suspension.

Compiler phải đưa `x` vào async state:

```text
AsyncFrame {
    state
    x: Buffer<u8>
}
```

Không nhất thiết heap.

Compiler có thể:

```text
stack frame
heap frame
caller-owned frame
register/state optimized
```

tùy executor.

### Nếu task migratable

```text
spawn(work(x))
```

thì state surviving `await` phải thỏa:

```text
Send(AsyncFrame)
```

Nếu có:

```axiom
struct LocalThing {
    ...
}
```

và:

```text
!Send(LocalThing)
```

thì migratable task phải reject.

---

# 14. Nhưng `spawn_local` phải khác

```axiom
spawn_local(work(x))
```

Executor đảm bảo task không chuyển execution context.

Khi đó:

```text
Send requirement
```

có thể được loại bỏ.

Như vậy:

```text
spawn()
    → Send required

spawn_local()
    → Send not required
```

Đây là một ví dụ rất rõ về việc:

> **Axiom không cần đưa async/thread semantics vào syntax của ownership.**

Chúng chỉ là constraints mà verifier áp dụng lên execution context.

---

# 15. FFI là lỗ hổng lớn

```axiom
extern @abi(C)
fn external(p: *mut Buffer)
```

Compiler không biết function làm gì.

Nếu programmer viết:

```axiom
let v = view(buffer)

external(&mut buffer)

use(v)
```

compiler **không được giả định** `v` vẫn hợp lệ.

Có hai lựa chọn:

### Conservative

FFI mặc định:

```text
UNKNOWN_MEMORY_EFFECT
```

→ invalidates những view/alias liên quan.

### Explicit contract

```text
@ffi_effects(
    read(arg0),
    write(arg1)
)
```

Compiler biết chính xác hơn.

Tôi nghiêng mạnh về **cả hai**:

```text
unknown FFI → conservative
annotated FFI → precise
```

---

# 16. Unsafe không nên phá verifier hoàn toàn

Ví dụ:

```axiom
unsafe {
    *p = 123
}
```

Không nên hiểu:

```text
unsafe = compiler bỏ qua mọi thứ
```

Mà:

```text
unsafe = programmer nhận trách nhiệm cho memory invariant
```

Compiler vẫn phải kiểm tra:

```text
type correctness
ABI
calling convention
control flow
machine legality
```

Nhưng không thể chứng minh:

```text
*p không alias với x
```

→ compiler phải xử lý đây như một **semantic escape boundary**.

---

# 17. Một vấn đề mới: function pointer

Ví dụ:

```axiom
let f = choose_function()
f(x)
```

Nếu compiler không biết `f` trỏ tới function nào thì effect summary không thể chính xác.

Không thể giả định:

```text
READ
```

hay:

```text
WRITE
```

Do đó:

```text
unknown indirect call
```

phải có conservative effect.

Ví dụ:

```text
UNKNOWN_CALL
    → may READ
    → may WRITE
    → may MOVE? 
    → may retain view?
    → may invalidate resources?
```

Nhưng **không nên quá conservative**, nếu không Axiom sẽ trở nên khó dùng.

Giải pháp tốt hơn là function type mang **effect contract** ở IR/compiler level.

Ví dụ conceptual:

```text
fn(T) -> U
```

và internal:

```text
fn(T) -> U
    effects: READ(arg0)
```

Programmer không nhất thiết phải viết effect annotation.

Compiler suy ra:

```text
body
 ↓
effect inference
 ↓
function effect summary
```

Chỉ những boundary như:

```text
FFI
dynamic dispatch
function pointer
unsafe external operation
```

mới cần contract rõ ràng hoặc conservative fallback.

---

# 18. Resource Drop + optimizer

Giả sử:

```axiom
{
    let f = File.open("x")
}
```

Compiler không được tùy tiện biến thành:

```text
nothing
```

nếu `File` destruction có observable behavior.

Ví dụ `close()` ghi dữ liệu hoặc flush buffer.

Do đó:

```text
DROP(File)
```

là:

```text
RESOURCE_RELEASE
```

→ observable.

Ngược lại:

```axiom
struct Temp {
    x: i32
}
```

nếu Drop chỉ là semantic no-op sau optimization:

```text
DROP Temp
```

có thể biến mất hoàn toàn.

---

# 19. Đây là một phân biệt cực kỳ quan trọng

Axiom nên chia:

```text
SEMANTIC EFFECT
```

và:

```text
OBSERVABLE EFFECT
```

Ví dụ:

| Effect | Semantic | Observable |
|---|---:|---:|
| READ | ✓ | không nhất thiết |
| WRITE | ✓ | không nhất thiết |
| MOVE | ✓ | không |
| DROP | ✓ | không nhất thiết |
| ALLOC | ✓ | không nhất thiết |
| IO | ✓ | ✓ |
| ATOMIC | ✓ | ✓ |
| SYNC | ✓ | ✓ |
| VOLATILE | ✓ | ✓ |
| FFI | ✓ | có thể |
| PANIC | ✓ | ✓ |
| TRAP | ✓ | ✓ |

Optimizer được phép xóa:

```text
MOVE
READ
ALLOC
DROP
```

**nếu không còn observable consequence.**

Nhưng không được xóa:

```text
IO
VOLATILE
ATOMIC
SYNC
observable DROP
```

---

# 20. Kết quả adversarial test

Sau khi “đập” semantics, kiến trúc hiện tại đứng khá vững:

```text
                 Axiom Source
                       │
                       ▼
                  Typed HIR
                       │
                       ▼
                      MIR
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Ownership      Regions      Effects
          │            │            │
          └────────────┼────────────┘
                       ▼
                   Verifier
                       │
              ┌────────┴────────┐
              │                 │
           REJECT            VERIFIED
              │                 │
           diagnostic           ▼
                            Optimizer
```

Điểm tôi đặc biệt hài lòng là **programmer không phải học một hệ thống borrow/lifetime phức tạp**, nhưng compiler vẫn có thể thực hiện phân tích tương đương hoặc sâu hơn.

---

## Tuy nhiên, có 5 thứ tôi cho rằng chưa nên đóng băng

Sau adversarial test, tôi sẽ **chưa freeze** 5 điểm này:

### 1. `view<T>` creation

Cần quyết định chính xác:

```axiom
let v = view(x)
```

có phải syntax hợp lệ trực tiếp không, và compiler tạo view thế nào.

### 2. View invalidation

Đặc biệt:

```text
Vec
Buffer
String
Map
Set
```

operation nào invalidate view.

### 3. Drop + partial move

Semantics hiện tại đã đúng hướng, nhưng cần formalize destructor behavior.

### 4. Unknown call

Cần specification chính xác cho:

```text
function pointer
dynamic dispatch
FFI
unsafe call
```

### 5. Effect summary

Tôi **không khuyến nghị đưa effect annotations vào syntax của programmer ở v0.1**.

Nên để:

```text
source
  ↓
compiler inference
  ↓
internal effect summary
```

và chỉ expose annotation khi cần cho:

```text
FFI / unsafe / external ABI
```

---

## Và có một kết luận quan trọng hơn

Sau toàn bộ các test này, tôi nghĩ Axiom đang hình thành một mô hình rất rõ:

> **Axiom không cố làm cho memory safety đơn giản bằng cách làm yếu compiler. Nó làm compiler phức tạp hơn để programmer không phải mang complexity đó.**

Tức là:

```text
Rust:
    Programmer complexity ↑
    Compiler complexity  ↑

C++:
    Programmer complexity ↔
    Compiler complexity   ↑

C:
    Programmer complexity ↑ ở memory/resource
    Compiler complexity   ↓

Axiom:
    Programmer-facing complexity ↓
    Compiler analysis complexity ↑
```

Đây có thể trở thành một trong những nguyên tắc kiến trúc quan trọng nhất của Axiom:

> **Compiler Complexity Is Not Language Complexity.**

Và tôi nghĩ bước kế tiếp nên chuyển từ việc kiểm tra semantics sang **đóng băng chính xác `view/mut_view + invalidation + partial Drop + effect summary`**, bởi đây là 4 điểm có khả năng gây ra những thay đổi kiến trúc lớn nhất nếu để muộn.