Tiếp tục thì tôi nghĩ **không nên viết ngay 4 file spec hoàn chỉnh**. Trước hết cần khóa một số quyết định kiến trúc còn đang "mở", vì nếu không, sau này AI agent rất dễ tự diễn giải và làm Axiom lệch hướng.

Tôi đề xuất chốt tiếp **6 vấn đề nền tảng**.

---

# 1. Chốt Memory Model: Ownership ≠ Borrow Checker

Đây là quyết định quan trọng nhất.

Axiom nên có mô hình:

```text
                VALUE
                  │
        ┌─────────┴─────────┐
        │                   │
   independent          resource-owning
        │                   │
      Copy                 Move
                            │
                      deterministic
                         release
```

Nhưng **không biến ownership thành một hệ thống reference syntax**.

Ví dụ programmer viết:

```axiom
fn process(data: Buffer) {
    ...
}
```

không phải:

```rust
fn process<'a>(data: &'a mut Buffer)
```

Compiler tự xác định:

```text
data
 ├─ ownership?
 ├─ read?
 ├─ mutation?
 ├─ escape?
 ├─ alias?
 └─ lifetime?
```

### Tôi đề xuất invariant:

> **Axiom compiler MUST perform ownership/lifetime/alias analysis, but Axiom source code MUST NOT require explicit lifetime annotations for ordinary code.**

Đây là khác biệt rất lớn với Rust.

---

# 2. Nhưng cần một khái niệm mới: View

Nếu bỏ reference syntax quá mạnh, chúng ta sẽ gặp vấn đề:

```axiom
fn sum(array: Array<i32>) -> i32
```

Nếu `Array` là owning value thì truyền nó vào có thể move.

Ta cần một khái niệm **view**.

Ví dụ:

```axiom
fn sum(values: view<i32>) -> i32
```

hoặc syntax khác đẹp hơn mà sau này quyết định.

Semantic:

```text
view<T>
    address
    length
```

nhưng:

- không sở hữu data
- không được outlive owner
- không cần programmer quản lý lifetime
- compiler kiểm tra lifetime

Ví dụ:

```axiom
fn sum(values: view<i32>) -> i32 {
    ...
}

fn test() {
    let a = [1, 2, 3]
    let x = sum(a)
}
```

Compiler hiểu:

```text
a owns memory
 │
 └── view ──> a
```

View chỉ tồn tại trong phạm vi hợp lệ.

---

# 3. View có thể là chìa khóa để tránh "pointer hell"

Thay vì programmer thường xuyên viết:

```text
*T
&T
&mut T
```

Axiom có các abstraction semantic:

```text
T
view<T>
mut_view<T>
owned<T>
```

Conceptually:

```text
T
│
├── value
│
├── view<T>
│      └── read-only
│
└── mut_view<T>
       └── mutable access
```

Nhưng tôi **chưa muốn đóng băng syntax**.

Chỉ nên đóng băng semantic.

---

# 4. Shared ownership: cần cực kỳ cẩn thận

Core v0.1 nói shared ownership được phép, nhưng đây là chỗ rất dễ làm Axiom biến thành Rust/Swift/GC phiên bản khác.

Tôi đề xuất chia:

```text
Unique ownership
Shared immutable
Shared mutable
```

### Unique

```text
Owner ──> Resource
```

### Shared immutable

```text
       ┌── read
Owner ─┼── read
       └── read
```

### Shared mutable

Không cho phép tự do.

Phải thông qua:

```text
Atomic<T>
Mutex<T>
RwLock<T>
Channel<T>
```

hoặc primitive tương đương.

Như vậy:

```text
shared ≠ automatically thread-safe
```

---

# 5. Không nên đưa reference counting vào language semantics

Đây là một quyết định tôi muốn sửa cho rõ hơn so với mô tả trước.

Axiom có thể cung cấp:

```text
Rc<T>
Arc<T>
```

nhưng đây là **library types**, không phải memory model.

Ví dụ:

```text
Rc<T>
  ↓
reference counting implementation
```

không phải:

```text
mọi Axiom object
  ↓
implicit refcount
```

Điều này giữ được:

- binary nhỏ
- deterministic performance
- không hidden atomic operations
- không hidden allocation
- không object header bắt buộc.

---

# 6. Type System cần thêm một khái niệm rất quan trọng: Type Class

Không phải mọi type đều giống nhau.

Tôi đề xuất compiler phân loại type theo **properties**, không phải inheritance.

Ví dụ:

```text
Type
 │
 ├── Copy
 ├── Move
 ├── Drop
 ├── Send
 ├── Share
 ├── Sized
 └── ...
```

Ví dụ:

```text
i32
```

có:

```text
Copy
Send
Share
Sized
```

Một resource:

```text
File
```

có thể:

```text
Move
Drop
Send
!Copy
```

Điều này rất mạnh vì compiler có thể suy luận.

---

# 7. Auto trait nhưng không gọi nó là inheritance

Ví dụ:

```axiom
struct Packet {
    data: Buffer
}
```

Nếu:

```text
Buffer : Send
```

thì compiler có thể suy luận:

```text
Packet : Send
```

Đây là **structural property propagation**.

Không cần programmer viết:

```text
implements Send
```

trong mọi trường hợp.

Nhưng programmer có thể override/declare constraint nếu cần.

---

# 8. Đây cũng giải quyết concurrency

Khi:

```axiom
spawn {
    process(packet)
}
```

compiler kiểm tra:

```text
packet : Send ?
```

Nếu có:

```text
YES
→ transfer ownership
```

Nếu không:

```text
compile error
```

Không cần một API runtime phức tạp để bảo vệ programmer.

---

# 9. Trait nên có 2 loại

Tôi đề xuất phân biệt:

### Semantic trait

Có thể ảnh hưởng đến type checking:

```text
Copy
Send
Share
Sized
Comparable
```

### Behavioral trait

Cung cấp behavior:

```text
Drawable
Iterator
Serialize
Hash
Display
```

Compiler biết semantic trait đặc biệt.

Ví dụ:

```text
Send
```

không chỉ là một function collection.

---

# 10. Override / "method override"

Liên hệ với câu hỏi trước của bạn về struct + function.

Axiom không cần:

```text
class
extends
override
virtual
```

Thay vào đó:

```axiom
trait Drawable {
    fn draw(self)
}
```

Type A:

```axiom
struct Circle { ... }

impl Drawable for Circle {
    fn draw(self) {
        ...
    }
}
```

Type B:

```axiom
struct Rectangle { ... }

impl Drawable for Rectangle {
    fn draw(self) {
        ...
    }
}
```

Static call:

```text
draw(circle)
```

được resolve compile time.

Dynamic:

```text
Drawable
```

thì compiler tạo dispatch mechanism.

---

# 11. Điều này cho phép một abstraction rất quan trọng

Axiom có thể viết:

```axiom
fn render<T: Drawable>(x: T) {
    x.draw()
}
```

Compiler tạo:

```text
render<Circle>
render<Rectangle>
```

→ static dispatch.

Nếu thực sự cần heterogeneous collection:

```text
Drawable[]
```

→ dynamic dispatch.

Do đó:

```text
static dispatch = default
dynamic dispatch = explicit cost
```

Đây là nguyên tắc rất tốt cho performance.

---

# 12. Concurrency: tôi muốn bổ sung Channel vào Core semantic model

Không nhất thiết API channel phải nằm Core, nhưng Core nên hiểu semantic concept:

```text
send(value)
receive()
```

vì đây là một cách rất tự nhiên để tránh shared mutable state.

Ví dụ:

```text
Thread A
   │
   │ ownership transfer
   ▼
 Channel
   │
   ▼
Thread B
```

Không cần:

```text
global mutable object
+
lock
```

cho rất nhiều trường hợp.

---

# 13. Async nên compile xuống cùng một model

Ví dụ:

```axiom
async fn download() -> Data
```

không nên tạo:

```text
Async Memory Model
```

mới.

Nó vẫn là:

```text
ownership
+
state machine
+
Send/Share
+
executor
```

Ví dụ:

```text
async function
      ↓
state machine
      ↓
locals become state
      ↓
suspend/resume
```

Nếu local value sống qua `await`, compiler phải đưa nó vào state machine.

---

# 14. Đây là nơi compiler IR phải rất mạnh

MIR cần biểu diễn được:

```text
MOVE
COPY
BORROW/VIEW
DROP
AWAIT
SPAWN
SEND
RECEIVE
ATOMIC
LOCK
UNLOCK
```

Nhưng **không phải tất cả đều tồn tại tới Machine IR**.

Ví dụ:

```text
SEND
```

có thể cuối cùng trở thành:

```text
store
atomic operation
function call
```

hoặc bị optimize hoàn toàn.

---

# 15. Tôi đề xuất MIR instruction set ban đầu

Một MIR v0.1 có thể có:

```text
CONST
COPY
MOVE

LOAD
STORE

FIELD
INDEX

CALL
RETURN

BRANCH
SWITCH

ALLOC
DEALLOC
DROP

VIEW
VIEW_MUT

PHI

ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS

LOCK
UNLOCK

SPAWN
SEND
RECEIVE

SUSPEND
RESUME

PANIC
TRAP
```

Nhưng lưu ý:

**đây là semantic MIR**, không phải machine instruction.

---

# 16. Một điểm tôi muốn thay đổi trong thiết kế IR ban đầu

Không nên để:

```text
ALLOC
DEALLOC
```

là instruction bắt buộc cho mọi object.

Nó nên có semantic distinction:

```text
Storage class
```

Ví dụ:

```text
Value
Stack
Heap
Static
External
Arena
Unknown
```

Compiler sau đó quyết định.

Ví dụ source:

```axiom
let x = Buffer(...)
```

MIR có thể:

```text
x = create Buffer
```

Optimizer mới quyết định:

```text
heap allocation
```

hay:

```text
stack
```

hay:

```text
inline
```

hay:

```text
eliminate
```

Điều này giúp Axiom không khóa optimizer quá sớm.

---

# 17. Axiom IR nên có SSA

Tôi rất khuyến nghị:

> **MIR/LIR sử dụng SSA hoặc SSA-like representation.**

Ví dụ:

```text
BB0:
    x0 = load a
    branch x0 > 0, BB1, BB2

BB1:
    x1 = 10
    goto BB3

BB2:
    x2 = 20
    goto BB3

BB3:
    x3 = phi(x1, x2)
    return x3
```

SSA giúp:

- constant propagation
- dead code elimination
- register allocation
- value numbering
- inlining
- vectorization

dễ hơn rất nhiều.

---

# 18. Nhưng ownership không nên cố nhét hoàn toàn vào SSA

Đây là một lỗi kiến trúc dễ mắc.

SSA giải quyết:

```text
value definition/use
```

Ownership giải quyết:

```text
resource lifetime
```

Hai thứ liên quan nhưng không giống nhau.

Do đó MIR nên có:

```text
SSA values
+
ownership state
+
drop/lifetime metadata
```

Compiler có thể verify hai hệ thống song song.

---

# 19. Compiler architecture hoàn chỉnh

Tôi sẽ hướng Axiom về:

```text
                    SOURCE
                       │
                       ▼
                    Parser
                       │
                       ▼
                      AST
                       │
                       ▼
                      HIR
                       │
               syntax normalization
                       │
                       ▼
                  Typed HIR
                       │
          ┌────────────┼────────────┐
          │            │            │
       Type         Trait       Generic
       Check        Resolve     Expansion
          │            │            │
          └────────────┼────────────┘
                       ▼
                      MIR
                       │
          ┌────────────┼────────────┐
          │            │            │
      Ownership     Concurrency   Async
       Analysis      Analysis     Lowering
          │            │            │
          └────────────┼────────────┘
                       ▼
                 Verified MIR
                       │
                       ▼
                  Optimization
                       │
                       ▼
                    Axiom LIR
                       │
                       ▼
                Target Lowering
                       │
                       ▼
                  Machine IR
                       │
                       ▼
                Register Allocation
                       │
                       ▼
                Machine Encoder
                       │
                       ▼
             ELF / PE / Mach-O / WASM
```

---

# 20. Và có một "Compiler Contract" nên được đóng băng

Tôi đề xuất thêm một specification nữa:

## `AXIOM-COMPILER-CONTRACT-v0.1`

Nó quy định compiler **không được làm gì**.

Ví dụ:

### CC-01

Compiler optimization MUST NOT change observable semantics.

### CC-02

Compiler MUST NOT introduce mandatory runtime dependency for code that does not require runtime facilities.

### CC-03

Compiler MUST NOT introduce GC implicitly.

### CC-04

Compiler MUST NOT introduce hidden reference counting unless semantics explicitly require it.

### CC-05

Compiler MAY change storage location.

```text
register ↔ stack ↔ heap
```

miễn semantics không đổi.

### CC-06

Compiler MAY eliminate allocation.

### CC-07

Compiler MAY specialize generic code.

### CC-08

Compiler MAY inline trait/function calls.

### CC-09

Compiler MUST preserve deterministic destruction semantics.

### CC-10

Compiler MUST NOT depend on AI for semantic compilation.

---

# 21. Tôi nghĩ đây mới là "linh hồn" của Axiom

Nếu gom toàn bộ những gì chúng ta đã thảo luận thành một mô hình:

```text
                   AXIOM
                     │
       ┌─────────────┼─────────────┐
       │             │             │
      VALUE       OWNERSHIP      TRAIT
       │             │             │
       │          LIFETIME       GENERIC
       │             │             │
       └─────────────┼─────────────┘
                     │
                  SAFETY
                     │
          ┌──────────┴──────────┐
          │                     │
       SAFE CODE             UNSAFE
          │                     │
     native fast             raw power
          │                     │
          └──────────┬──────────┘
                     │
                  MIR/LIR
                     │
              ┌──────┼──────┐
              ▼      ▼      ▼
             x64    ARM64   RISC-V
```

Điểm đặc biệt là:

> **Axiom không cố làm compiler thông minh bằng cách làm language phức tạp.**

Ngược lại:

> **Axiom giữ source semantics đơn giản, rồi để compiler làm phần phức tạp.**

Đây chính là hướng phù hợp với mục tiêu ban đầu của bạn: **người lập trình không phải vật lộn với pointer/lifetime/thread/async, nhưng compiler vẫn tạo ra native code có hiệu năng gần với mức mà một compiler C/C++ tốt có thể đạt được.**

Bước tiếp theo hợp lý nhất là tôi viết tiếp **spec normative thực sự** cho 4 phần này, bắt đầu bằng **`AXIOM-MEMORY-MODEL-v0.1.md`**, trong đó định nghĩa cụ thể **Copy/Move/Drop/View/Alias/Escape/Stack/Heap/Shared Ownership/Unsafe** bằng `MUST / MUST NOT / SHOULD / MAY` và đưa ra khoảng 30–50 test case mà compiler Axiom bắt buộc phải pass.