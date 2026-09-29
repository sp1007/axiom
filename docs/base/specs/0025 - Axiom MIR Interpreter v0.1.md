Tiếp tục từ **MIR v0.1**, bước hợp lý nhất là đóng thiết kế **Axiom MIR Interpreter v0.1**. Đây sẽ là “oracle” để sau này kiểm chứng backend native.

## 1. Vai trò của MIR Interpreter

Không phải VM để chạy Axiom production.

Nó là **reference implementation của semantics**:

```text
Axiom Source
    ↓
 AST
    ↓
 HIR
    ↓
 MIR
    ↓
 Ownership / Capability / Effect Verifier
    ↓
 Verified MIR
    ↓
 ┌──────────────────────┐
 │   MIR Interpreter    │  ← semantic oracle
 └──────────────────────┘
    ↓
 Observable result
```

Sau này:

```text
Verified MIR
   ├── MIR Interpreter
   │      └── expected behavior
   │
   └── Native Backend
          └── actual behavior
```

Nếu:

```text
Interpreter result != Native result
```

thì mặc định **backend sai**, không được sửa semantics để khớp backend.

---

# 2. Interpreter không được mô phỏng “CPU”

Đây là điểm rất quan trọng.

Không nên thiết kế interpreter như:

```text
MIR → giả lập register → giả lập stack → giả lập RAM
```

vì như vậy nó sẽ vô tình đóng băng implementation details.

Thay vào đó:

```text
MIR semantic model
```

và runtime state:

```text
InterpreterState
├── values
├── places
├── ownership
├── regions
├── allocations
├── resources
├── call_stack
├── control_state
├── async_state
└── observable_effects
```

Nó mô phỏng **ý nghĩa của MIR**, không mô phỏng x86/ARM.

---

# 3. Runtime value model

Có thể định nghĩa:

```text
RuntimeValue
├── Bool
├── Integer
├── Float
├── Tuple
├── Struct
├── Enum
├── Array
├── Function
├── Closure
├── View
├── MutView
└── RawPointer
```

Nhưng cần một nguyên tắc:

> RuntimeValue không phải representation của ABI.

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

Interpreter nhìn thấy:

```text
Struct(Point)
    x = 1.0
    y = 2.0
```

Không quan tâm native backend sau này truyền nó bằng:

```text
XMM0
XMM1
```

hay:

```text
stack[...]
```

hay scalarized thành hai registers.

---

# 4. Memory model của Interpreter

Đây là phần cực kỳ quan trọng đối với Axiom.

Không dùng:

```text
address → bytes
```

làm mô hình chính.

Thay vào đó:

```text
Allocation
├── AllocationId
├── TypeId
├── size
├── alignment
├── state
└── semantic contents
```

Ví dụ:

```text
Allocation #42
type = Buffer<u8>
state = OWNED
contents = [...]
```

Một `Place` trỏ đến semantic allocation:

```text
Place
    ↓
Allocation #42
    ↓
Field / Index / ...
```

Như vậy interpreter có thể phát hiện:

```text
use-after-move
use-after-drop
out-of-bounds
invalid-view
```

mà không cần dựa vào địa chỉ thật.

---

# 5. View phải được mô phỏng bằng provenance

Ví dụ:

```axiom
var buffer = Vec<i32>::new()

let v = view(buffer)

use(v)
```

Interpreter tạo:

```text
View {
    source = Allocation #42
    region = [0..N]
    capability = READ
}
```

Không đơn giản chỉ là:

```text
pointer = 0x123456
length = 10
```

Mà phải giữ:

```text
provenance
region
access capability
```

Ví dụ:

```text
View #7
├── source: Allocation #42
├── region: buffer[0..10]
└── access: READ
```

Điều này cực kỳ hữu ích cho verifier.

---

# 6. `mut_view`

Tương tự:

```text
MutView #8
├── source: Allocation #42
├── region: buffer[0..10]
└── access: WRITE
```

Interpreter phải bảo đảm semantic invariant:

```text
READ + READ     → OK
READ + WRITE    → conflict
WRITE + WRITE   → conflict
MOVE + anything → conflict
DROP + anything → conflict
```

Tuy nhiên interpreter **không nên tự thay thế verifier**.

Nếu Verified MIR đã hợp lệ:

```text
Verifier → ACCEPT
```

Interpreter có thể giả định invariant đó.

Nếu chạy Raw MIR ở chế độ debug:

```text
Interpreter --check
```

thì nó có thể phát hiện vi phạm để debug compiler.

---

# 7. Ownership state

Runtime cần state tương ứng:

```text
UNINIT
OWNED
PARTIAL
MOVED
DROPPED
```

Ví dụ:

```axiom
let a = File.open(...)
let b = a
```

Nếu `File` non-Copy:

```text
a = MOVED
b = OWNED
```

Sau đó:

```axiom
use(a)
```

Verifier phải reject trước interpreter.

Interpreter debug mode cũng có thể báo:

```text
AX_RUN_OWN_0001:
use of moved value
```

---

# 8. Partial move

Đây là một trong những lý do cần semantic memory model.

```axiom
struct Person {
    name: String
    age: i32
}

let p = Person(...)
let name = p.name
```

Runtime state:

```text
p
├── name → MOVED
└── age  → OWNED
```

Không được biến toàn bộ:

```text
p → MOVED
```

vì:

```axiom
print(p.age)
```

vẫn hợp lệ.

Khi scope kết thúc:

```text
DROP p
```

phải thực hiện:

```text
DROP age
```

nhưng **không DROP name lần nữa**.

Đây là test cực quan trọng cho Drop elaboration.

---

# 9. Drop

Interpreter phải coi `DROP` là **semantic operation**.

Ví dụ:

```axiom
{
    let f = open(...)
}
```

MIR:

```text
CALL open
...
DROP f
RETURN
```

Interpreter thực hiện:

```text
resource f → released
```

Nhưng không được giả định:

```text
DROP = free()
```

Vì:

```text
Drop<File>
Drop<MutexGuard>
Drop<Socket>
Drop<GPUResource>
Drop<Arena>
```

có semantics hoàn toàn khác nhau.

---

# 10. Observable Drop

Điểm này cần chốt khá sớm.

Ví dụ:

```axiom
struct Logger {
    ...
}

impl Drop for Logger {
    ...
}
```

Nếu Drop tạo observable side effect:

```text
DROP_OBSERVABLE
```

optimizer không thể tùy tiện biến:

```text
DROP
```

thành:

```text
nothing
```

Ngược lại nếu destruction chỉ giải phóng allocation mà allocation đã chết về mặt semantic:

```text
DROP
```

có thể được tối ưu.

Do đó tôi đề xuất:

```text
Drop effect
├── INTERNAL_RELEASE
└── OBSERVABLE_RELEASE
```

Interpreter phải ghi nhận observable effects.

---

# 11. Observable event log

Đây sẽ là một thành phần cực kỳ hữu ích.

Interpreter tạo:

```text
EventLog
```

Ví dụ:

```text
CALL open
ALLOC resource #3
WRITE stdout "hello"
DROP resource #3
RETURN 0
```

Không cần so sánh toàn bộ internal execution.

Test chỉ cần:

```text
expected:
    stdout = "hello"
    exit = 0
    resources = 0
```

Hoặc:

```text
expected:
    events contain DROP(File)
```

Điều này tránh việc test bị phụ thuộc vào optimizer.

---

# 12. Function call

Call frame:

```text
CallFrame
├── function_id
├── locals
├── SSA values
├── current_block
├── instruction_index
└── return_target
```

Stack:

```text
CallStack
├── main
├── foo
└── bar
```

Nhưng đây chỉ là interpreter stack.

Native compiler hoàn toàn có thể:

```text
inline foo()
```

hoặc:

```text
tail-call
```

hoặc loại bỏ stack frame.

---

# 13. CALL semantics

MIR:

```text
%r = CALL add(%a, %b)
```

Interpreter:

```text
resolve FunctionId
→ create frame
→ bind arguments
→ execute
→ return value
→ assign %r
```

Không cần dynamic linker hay ABI.

Đối với intrinsic:

```text
INTEGER_ADD
INTEGER_MUL
MEMCPY
ATOMIC_CAS
```

interpreter có semantic implementation riêng.

---

# 14. Generic

MIR sau specialization không còn ambiguity.

Ví dụ:

```axiom
fn max<T: Comparable>(...)
```

khi gọi:

```axiom
max<i32>(a, b)
```

MIR có thể đã trở thành:

```text
FunctionId = max<i32>
```

Interpreter chỉ chạy specialization.

Không cần interpreter hiểu toàn bộ generic system.

Đây là một lợi thế lớn.

---

# 15. Trait dispatch

Static:

```text
impl Drawable for Circle
```

sau resolution:

```text
CALL Circle::draw
```

Interpreter không cần trait lookup.

Dynamic:

```text
dyn Drawable
```

mới tạo:

```text
DynamicObject
├── data
└── dispatch
```

và:

```text
DYNAMIC_CALL
```

Interpreter dispatch qua semantic method table.

---

# 16. Panic / Trap

Interpreter phải phân biệt:

```text
PANIC
TRAP
```

Ví dụ:

```text
PANIC
├── reason
├── source location
└── optional payload
```

`TRAP`:

```text
TRAP
├── reason
└── machine-level termination semantics
```

Không nên gom cả hai thành một `return error`.

---

# 17. Bounds check

MIR:

```text
BOUNDS_CHECK index, length
```

Nếu thất bại:

```text
PANIC(bounds_error)
```

Nếu verifier/optimizer đã chứng minh:

```text
0 <= index < length
```

thì native backend có thể xóa check.

Interpreter vẫn phải hiểu:

```text
BOUNDS_CHECK
```

vì raw Verified MIR có thể còn check.

---

# 18. Arithmetic

Interpreter phải là **reference semantics**.

Ví dụ nếu sau này chốt:

```text
i32 checked
```

thì:

```text
2147483647 + 1
```

phải tạo:

```text
PANIC(overflow)
```

Nếu:

```text
wrapping
```

thì:

```text
-2147483648
```

v.v.

Điểm này cho thấy **overflow semantics phải được freeze trước khi interpreter trở thành oracle**.

Đây là một trong những mục tôi sẽ đưa vào Semantic Freeze Gate tiếp theo.

---

# 19. Async

Interpreter không cần scheduler thực.

Có thể có:

```text
VirtualExecutor
```

với:

```text
Task
├── task_id
├── state
├── frame
└── status
```

Status:

```text
READY
RUNNING
SUSPENDED
COMPLETED
CANCELLED
PANICKED
```

Ví dụ:

```text
async fn foo()
```

lower thành state machine:

```text
state 0
   ↓ await
state 1
   ↓ await
state 2
   ↓
return
```

Interpreter chỉ cần deterministic scheduler:

```text
run task
→ SUSPEND
→ queue task
→ resume
```

Không cần OS thread.

---

# 20. Concurrency

Không nên cố mô phỏng tất cả hardware concurrency trong v0.1.

Có hai chế độ:

### Deterministic mode

```text
--interp-deterministic
```

Scheduler kiểm soát hoàn toàn thứ tự task.

Dùng cho test.

### Stress mode

Sau này mới có:

```text
--interp-stress
```

cố tình thay đổi scheduling để tìm race/violation.

Nhưng semantics của atomics vẫn phải được định nghĩa độc lập với interpreter.

---

# 21. FFI

Interpreter không thể thực sự gọi mọi native API.

Do đó:

```text
extern fn
```

được phân thành:

```text
KNOWN_INTRINSIC
MOCK
HOST_CALLBACK
UNSUPPORTED
```

Ví dụ test:

```axiom
extern @abi(C) fn puts(...)
```

Interpreter có thể map:

```text
puts → host mock
```

hoặc:

```text
puts → stdout
```

nhưng không được coi implementation host là Axiom semantics.

---

# 22. Raw pointer

Đây là chỗ phải đặc biệt cẩn thận.

Interpreter có thể dùng:

```text
RawAddress
```

nhưng chỉ trong:

```text
unsafe
```

và debug interpreter có thể gắn:

```text
allocation provenance
bounds
alive/dead
```

Ví dụ:

```text
0x1000
    ↓
Allocation #42
    range [0..64]
```

Nếu:

```text
ptr + 100
```

thì debug interpreter có thể báo invalid access.

Nhưng **không được biến các debug checks này thành semantics của safe language**.

---

# 23. Interpreter modes

Tôi đề xuất ngay từ đầu có 4 mode:

```text
axiom run file.ax
```

→ compile/native bình thường sau này.

```text
axiom interpret file.ax
```

→ MIR interpreter.

```text
axiom interpret --check file.ax
```

→ interpreter + runtime invariant checking.

```text
axiom interpret --trace file.ax
```

→ event/instruction trace.

Ví dụ:

```text
[BB0]
%1 = CONSTANT 10
%2 = CONSTANT 20
%3 = INTEGER_ADD %1 %2

[BB1]
RETURN %3
```

---

# 24. Quan trọng nhất: Interpreter phải chạy Verified MIR

Tôi đề xuất invariant:

```text
Raw MIR
   ↓
Verifier
   ↓
Verified MIR
   ↓
Interpreter
```

Không:

```text
Source → Interpreter
```

và cũng không:

```text
Raw MIR → Interpreter
```

trong production path.

Debug mode có thể cho phép Raw MIR để debug compiler, nhưng phải ghi rõ:

```text
UNVERIFIED EXECUTION
```

---

# 25. Kiến trúc module

Tôi sẽ tách compiler thành:

```text
compiler/
├── lexer/
├── parser/
├── ast/
├── resolver/
├── hir/
├── typeck/
├── mir/
├── verifier/
├── interpreter/
│   ├── runtime_value
│   ├── memory
│   ├── ownership
│   ├── calls
│   ├── effects
│   ├── async
│   ├── intrinsics
│   └── trace
├── optimizer/
├── lir/
├── backend/
└── driver/
```

Interpreter **không được import backend**.

Backend có thể import MIR definition.

---

# 26. Test architecture

Đây mới là giá trị lớn nhất.

Mỗi semantic test có thể chạy:

```text
source
  ↓
MIR
  ↓
Verifier
  ↓
Interpreter
```

Sau khi có native backend:

```text
             ┌→ Interpreter → result A
Source → MIR ┤
             └→ Native      → result B

assert A == B
```

Đây là **differential execution**.

Ví dụ:

```text
tests/runtime/arithmetic_001.ax
tests/runtime/ownership_001.ax
tests/runtime/drop_order_001.ax
tests/runtime/partial_move_001.ax
tests/runtime/view_001.ax
tests/runtime/result_001.ax
tests/runtime/match_001.ax
```

---

# 27. Một thay đổi kiến trúc tôi khuyên chốt ngay

Từ đây Axiom nên có khái niệm:

```text
SEMANTIC ORACLE
```

với:

```text
Verified MIR
      ↓
┌──────────────────────────────┐
│ Semantic Oracle              │
│                              │
│ 1. Interpreter               │
│ 2. Conformance Test Suite    │
│ 3. Event Model               │
└──────────────────────────────┘
```

Mục tiêu:

> **Không có backend nào được phép định nghĩa semantics của Axiom.**

LLVM không định nghĩa Axiom.

x86 không định nghĩa Axiom.

ARM64 không định nghĩa Axiom.

WASM cũng không định nghĩa Axiom.

**Verified MIR + Semantic Oracle mới là chuẩn.**

Đây là điều đặc biệt quan trọng với mục tiêu cuối cùng của bạn là **Axiom tự viết compiler và tự sinh native executable**, bởi nếu không có semantic oracle thì khi compiler tự host, một lỗi compiler rất dễ biến thành “thay đổi ngôn ngữ” mà không ai nhận ra.

### Bước kế tiếp

Sau MIR Interpreter, tôi không khuyên nhảy ngay sang backend.

Nên đi theo thứ tự:

```text
MIR v0.1
   ↓
MIR Interpreter v0.1
   ↓
Adversarial Semantic Tests
   ↓
Ownership/Region Verifier v0.1
   ↓
Drop Elaboration
   ↓
MIR Optimizer v0.1
   ↓
Axiom LIR v0.1
   ↓
x86-64 Backend
```

**Bước tiếp theo hợp lý nhất là thiết kế bộ `Adversarial Semantic Tests v0.1`** — đặc biệt các case có thể làm lộ lỗi trong mô hình `ownership + region + view + partial move + Drop + async`. Đây sẽ là “bài kiểm tra phá ngôn ngữ” trước khi chúng ta cho AI agent bắt tay implement compiler.