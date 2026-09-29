# BOOTSTRAP-226 — OWNERSHIP / INITIALIZATION / DROP VERIFIER

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là lớp verifier trung tâm của Axiom memory model.

Mục tiêu không phải biến Axiom thành Rust với một borrow checker khác cú pháp. Mục tiêu là:

> **Programmer chỉ biểu diễn ownership ở những nơi semantic boundary cần thiết; compiler tự suy luận initialization, move, lifetime và cleanup.**

---

# 1. Vị trí trong compiler

```text
Typed HIR
   ↓
MIR
   ↓
┌─────────────────────────────┐
│ Ownership / Init / Drop     │
│ Verifier ← BOOTSTRAP-226    │
└──────────────┬──────────────┘
               ↓
Capability Verifier
               ↓
Effect Verifier
               ↓
Verified MIR
```

226 chỉ chịu trách nhiệm chính về:

- initialization;
- ownership;
- move;
- copy;
- partial move;
- drop;
- cleanup;
- lifetime của owned values.

Nó **không** chịu trách nhiệm thay Capability Verifier quyết định aliasing của `view<T>`/`mut_view<T>`.

---

# 2. Ba trạng thái phải phân biệt

Axiom không được dùng một trạng thái duy nhất kiểu:

```text
valid / invalid
```

Mà phải phân biệt:

```text
Initialization
Ownership
Drop obligation
```

Ví dụ:

```text
x = initialized
x = owned
x = requires_drop
```

Ba thuộc tính độc lập.

---

# 3. Ownership State

Core lattice:

```text
UNINIT
   ↓
OWNED
   ↓
MOVED
   ↓
DROPPED
```

Nhưng cần thêm:

```text
PARTIALLY_MOVED
```

nên mô hình thực tế:

```text
             ┌──────────┐
             │  UNINIT  │
             └────┬─────┘
                  ↓
             ┌──────────┐
             │  OWNED   │
             └──┬───┬───┘
                │   │
          partial   move
                │   │
                ↓   ↓
        ┌──────────┐ ┌────────┐
        │ PARTIAL  │ │ MOVED  │
        └────┬─────┘ └────────┘
             │
             ↓
          DROPPED
```

---

# 4. Không được suy diễn

`MOVED` không có nghĩa memory đã bị zero.

`DROPPED` không có nghĩa physical memory đã được `free`.

`OWNED` không có nghĩa chắc chắn đang ở heap.

Đây đều là **semantic state**.

---

# 5. Place Tree

Đây là cấu trúc quan trọng nhất.

Ví dụ:

```axiom
struct User {
    name: String
    age: u32
}
```

Verifier có:

```text
User
├── name : String
└── age  : u32
```

Không chỉ theo Local.

---

# 6. Vì sao cần Place Tree?

Ví dụ:

```axiom
let user = make_user()
let name = user.name
```

Nếu `String` không Copy:

```text
user.name → MOVED
user.age  → OWNED
```

Nhưng:

```text
user
```

không hoàn toàn MOVED.

Đây là lý do Axiom cần field-sensitive ownership.

---

# 7. Move Path

Mỗi move tạo một semantic path:

```text
user.name
```

không phải:

```text
user
```

nếu chỉ field `name` được move.

Move path:

```text
MovePath {
    base: LocalId
    projections: [Field(name)]
}
```

---

# 8. Parent/child ownership

Nếu:

```text
user.name → MOVED
```

thì:

```text
user
```

ở trạng thái:

```text
PARTIALLY_MOVED
```

trừ trường hợp type/Drop semantics cho phép xử lý khác.

---

# 9. Move toàn object

```axiom
let b = a
```

với non-Copy:

```text
a → MOVED
b → OWNED
```

Tất cả child paths của `a` trở thành unavailable thông qua `a`.

---

# 10. Move field

```axiom
let x = a.field
```

chỉ field đó bị move:

```text
a.field → MOVED
a.other → OWNED
a → PARTIALLY_MOVED
```

---

# 11. Đọc moved value

```axiom
let x = a.name
let y = a.name
```

sau lần đầu:

```text
a.name → MOVED
```

lần hai:

```text
ERROR: AMOVE-01
use of moved value
```

---

# 12. Move lại

```axiom
let x = a
let y = a
```

second move:

```text
ERROR: AMOVE-02
cannot move from moved place
```

---

# 13. Copy không consume

```axiom
let b = a
```

nếu `a: Copy`:

```text
a → OWNED
b → OWNED
```

Không có transition:

```text
a → MOVED
```

---

# 14. Clone

```axiom
let b = a.clone()
```

cả hai:

```text
a → OWNED
b → OWNED
```

Nhưng semantic cost của clone là explicit.

Compiler không được biến arbitrary `Clone` thành Copy.

---

# 15. Drop

Drop obligation gắn với type:

```text
Drop(T) = true/false
```

Ví dụ:

```text
i32      → no Drop
String   → Drop
Vec<T>   → Drop
File     → Drop
```

---

# 16. Copy và Drop

Invariant:

```text
Drop(T) ⇒ !Copy(T)
```

Một type có ownership resource không được vừa:

```text
semantic Copy
```

vừa:

```text
exactly-once Drop
```

nếu không sẽ tạo double-release.

---

# 17. Drop obligation không đồng nghĩa deallocation

Ví dụ:

```text
String
```

Drop có thể:

```text
release buffer
```

nhưng compiler có thể đã:

- stack allocate;
- eliminate allocation;
- scalarize;
- use caller storage.

Drop chỉ bảo đảm semantic cleanup.

---

# 18. Initialization

Một local mới:

```text
let x: T
```

ban đầu:

```text
UNINIT
```

Sau:

```text
x = make()
```

thành:

```text
OWNED
```

---

# 19. Read before initialization

```axiom
let x: i32
print(x)
```

Verifier:

```text
ERROR AINIT-01
use of uninitialized value
```

---

# 20. Conditional initialization

```axiom
let x: i32

if cond {
    x = 10
}

print(x)
```

Sau branch join:

```text
x = MAYBE_UNINIT
```

→ reject.

---

# 21. Definite initialization

```axiom
let x: i32

if cond {
    x = 10
} else {
    x = 20
}

print(x)
```

join:

```text
x = INIT
```

→ valid.

---

# 22. Dataflow lattice

Đề xuất:

```text
UNINIT
INIT
MAYBE_INIT
```

với:

```text
UNINIT ⊑ MAYBE_INIT
INIT   ⊑ MAYBE_INIT
```

`MAYBE_INIT` không bao giờ được xem là initialized.

---

# 23. Ownership join

Ví dụ:

```text
if cond {
    move x
} else {
    keep x
}
```

sau join:

```text
x = MAYBE_MOVED
```

Không thể:

```text
use x
```

an toàn.

---

# 24. Ownership state mở rộng

Thực tế verifier nên dùng:

```text
OwnershipFact {
    initialization
    ownership
    move_state
    drop_obligation
}
```

thay vì một enum khổng lồ.

---

# 25. Branch join

Ví dụ:

```text
BB1:
    x = OWNED

BB2:
    x = MOVED
```

join:

```text
x = MAYBE_MOVED
```

Nếu tiếp tục dùng x:

```text
reject
```

---

# 26. Không dùng optimistic join

Axiom tuyệt đối không:

```text
UNKNOWN → assume safe
```

Nguyên tắc:

> **Không chứng minh được → không được coi là đúng.**

---

# 27. Loops

Loops yêu cầu fixed-point analysis.

Ví dụ:

```axiom
while cond {
    x = make()
}
```

Verifier phải hội tụ trạng thái qua nhiều vòng.

---

# 28. Fixed-point

Pseudo-model:

```text
state(entry) = initial

repeat:
    new_state = transfer(block, input_state)
    output = join(previous, new_state)

until stable
```

Nếu không hội tụ trong giới hạn:

```text
verification failure
```

hoặc compiler internal diagnostic tùy trường hợp.

---

# 29. Initialization trong loop

```axiom
let x: i32

while cond {
    x = 10
}

use(x)
```

Không được giả định loop chạy ít nhất một lần.

Sau loop:

```text
x = MAYBE_INIT
```

→ reject.

---

# 30. Loop chạy chắc chắn

Nếu control-flow semantics chứng minh loop body luôn chạy ít nhất một lần, verifier có thể tận dụng fact đó.

Nhưng:

> Proof phải đến từ CFG/semantic analysis, không từ heuristic.

---

# 31. Reinitialization sau Move

Điểm quan trọng.

```axiom
let x = make()
consume(x)

x = make_again()
use(x)
```

Được phép.

State:

```text
OWNED
 ↓
MOVED
 ↓
OWNED
```

---

# 32. Reinitialization không cần Drop

Nếu `x` đã MOVED thì không Drop lần nữa.

Assignment mới tạo ownership mới.

---

# 33. Assignment lên field đã moved

```axiom
let x = make()
consume(x.name)

x.name = "new"
```

có thể hợp lệ nếu field có thể reinitialize.

State:

```text
x.name: MOVED
      ↓
      OWNED
```

---

# 34. Assignment lên parent

Nếu:

```text
x.name → MOVED
```

sau:

```text
x = make()
```

toàn bộ subtree reset:

```text
x
├── name OWNED
└── age  OWNED
```

---

# 35. Destructuring

```axiom
let User { name, age } = user
```

Verifier xử lý như các move/copy riêng tùy binding semantics.

Ví dụ non-Copy:

```text
user.name → MOVED
user.age  → MOVED
```

toàn bộ user consumed.

---

# 36. Pattern matching

```axiom
match user {
    User { name, age } => ...
}
```

Verifier phải biết pattern binding là:

- move;
- copy;
- view;
- reference-like capability.

Không được coi tất cả pattern binding là Copy.

---

# 37. Match và ownership

Ví dụ:

```axiom
match value {
    Some(x) => consume(x)
    None => ...
}
```

`x` chỉ tồn tại trong branch.

Sau branch, verifier merge ownership của `value` theo enum semantics.

---

# 38. Enum payload

Place Tree:

```text
value
├── discriminant
└── payload
    ├── field1
    └── field2
```

Nhưng chỉ variant đang active mới được coi là initialized.

---

# 39. Invalid inactive variant access

Không được:

```text
Some payload
```

khi actual value là:

```text
None
```

Pattern verifier đảm bảo điều này.

MIR verifier vẫn giữ invariant.

---

# 40. Drop của enum

Khi enum có Drop-bearing payload:

```text
Option<String>
```

chỉ payload active mới có Drop obligation.

`None` không được drop nonexistent payload.

---

# 41. Exactly-once Drop

Invariant cốt lõi:

> Mỗi owned resource phải được semantic cleanup **0 hoặc 1 lần tùy ownership path**, và không được có hai cleanup cho cùng ownership instance.

Nói chính xác hơn:

```text
Created ownership instance
        ↓
   exactly one
   terminal state:
     Move
     Drop
     Return ownership
```

---

# 42. Return ownership

Nếu:

```axiom
return x
```

ownership chuyển:

```text
local x
   ↓
caller return value
```

Không Drop x tại function exit.

---

# 43. Call ownership

```axiom
consume(x)
```

ownership:

```text
caller x
   ↓
callee parameter
```

Caller không Drop x sau call.

Callee cuối cùng chịu trách nhiệm theo signature semantics.

---

# 44. Copy call

```axiom
use(x)
```

nếu parameter `Copy`:

```text
Copy(x)
```

caller vẫn sở hữu x.

---

# 45. View call

```axiom
inspect(x)
```

nếu parameter `view<T>`:

```text
MakeView(x)
Call inspect(view)
Capability ends
```

Ownership của x không thay đổi.

---

# 46. Mutable view call

```axiom
modify(x)
```

nếu parameter `mut_view<T>`:

```text
MakeMutView(x)
Call modify(view)
Capability ends
```

Ownership vẫn thuộc caller.

Capability verifier chịu trách nhiệm exclusivity.

---

# 47. Ownership verifier và capability verifier

Phân công:

```text
Ownership:
    Who owns x?

Capability:
    Who may access x right now?
```

Ví dụ:

```text
x owned by A
view(x) active
```

Ownership verifier nói:

```text
A owns x
```

Capability verifier nói:

```text
read capability active
```

---

# 48. Drop với live capability

```axiom
let v = view(x)
drop(x)
use(v)
```

reject.

Nhưng đây chủ yếu là cross-verifier invariant:

```text
Ownership/Drop
+
Capability lifetime
```

---

# 49. Drop với mut_view

```axiom
let v = mut_view(x)
drop(x)
```

reject.

Owner không thể bị destroyed khi dependent capability còn sống.

---

# 50. Scope exit

```axiom
{
    let a = make_a()
    let b = make_b()
}
```

semantic cleanup:

```text
drop(b)
drop(a)
```

---

# 51. Reverse initialization order

Nếu:

```axiom
let a = make_a()
let b = make_b()
let c = make_c()
```

thì:

```text
drop(c)
drop(b)
drop(a)
```

---

# 52. Conditional resources

```axiom
let a = make_a()

if cond {
    let b = make_b()
}
```

`b` cleanup ở branch exit.

`a` cleanup ở enclosing scope exit.

---

# 53. Multiple exits

Compiler phải biến:

```text
return
break
continue
panic
```

thành cleanup-aware CFG.

Ví dụ:

```text
body
 ├── return → cleanup → return
 └── normal → cleanup → next
```

---

# 54. Cleanup duplication

Compiler không nên copy hàng loạt Drop sequence vào mọi branch nếu làm CFG phình to.

Có thể tạo:

```text
cleanup block
```

dùng chung.

---

# 55. Cleanup block

Ví dụ:

```text
BB_cleanup:
    Drop(b)
    Drop(a)
    Return
```

Các return path:

```text
BB1 → BB_cleanup
BB2 → BB_cleanup
BB3 → BB_cleanup
```

---

# 56. Drop flags

Đối với partially initialized/moved values, compiler cần biết field nào còn live.

Có hai lựa chọn:

### Explicit flags

```text
drop_flag_a
drop_flag_b
```

### Static path analysis

Nếu compiler chứng minh state compile-time:

```text
no runtime flag
```

Axiom nên hỗ trợ **cả hai**.

---

# 57. Drop flags không phải luôn runtime variable

Compiler có thể lower:

```text
if initialized
    drop
```

thành unconditional Drop nếu proof cho thấy luôn initialized.

Hoặc eliminate hoàn toàn nếu moved.

---

# 58. Drop flag optimization

Raw semantic model:

```text
DropIfLive(x)
```

Sau proof:

```text
Drop(x)
```

hoặc:

```text
nothing
```

---

# 59. No hidden reference counting

Ownership verifier **không** tự chèn:

```text
retain()
release()
```

Axiom không có implicit RC.

Nếu programmer dùng:

```text
Arc<T>
```

thì RC là semantics của library type đó.

---

# 60. No GC interaction

Verifier không tạo:

```text
GC root
write barrier
tracing metadata
```

vì Core không có tracing GC.

---

# 61. Storage independence

Verifier không được quan tâm:

```text
stack
heap
register
arena
pool
```

trừ khi type/storage contract yêu cầu.

---

# 62. Stable address

Nếu code yêu cầu stable address:

```text
Box<T>
```

hoặc explicit storage contract.

Verifier ghi:

```text
StableAddressRequired
```

Allocation optimizer không được relocate object nếu relocation observable/invalid.

---

# 63. Escape

Nếu owned value:

```text
return x
```

thì:

```text
Escape = ReturnEscape
```

Nếu:

```text
send(channel, x)
```

thì:

```text
Escape = Thread/Task transfer
```

Ownership transfer vẫn hợp lệ.

---

# 64. Escape không đồng nghĩa heap allocation

Ví dụ return value:

```text
fn make() -> BigStruct
```

có thể:

```text
caller allocated return slot
```

không cần heap.

---

# 65. Closure capture

Nếu closure move-capture:

```axiom
let f = || consume(x)
```

thì ownership:

```text
x → MOVED
closure.env.x → OWNED
```

---

# 66. Closure view capture

Nếu closure giữ view:

```text
closure.env.v → capability
```

thì lifetime của closure phải bị ràng buộc bởi provenance.

Không được để closure outlive owner.

---

# 67. Async

Async là điểm cực kỳ quan trọng.

```axiom
let x = make()
await foo()
use(x)
```

Nếu `x` live across await:

```text
x → Future state
```

Ownership verifier phải chuyển ownership từ local frame sang future state.

---

# 68. Async Drop

Khi Future bị drop:

```text
future state fields
```

phải được cleanup theo ownership semantics.

Không cần `AsyncDrop`.

---

# 69. Cancellation

Cancellation không phải:

```text
panic
```

Future bị drop phải cleanup owned state.

External operation cancellation là semantic của async library.

---

# 70. Thread spawn

```axiom
spawn(fn() => use(x))
```

Nếu closure move-captures x:

```text
x → closure
closure → task
```

Ownership transfer sang execution domain mới.

Send verifier sau đó kiểm tra `Send`.

---

# 71. Thread local closure

Nếu:

```text
spawn_local(...)
```

không yêu cầu Send theo cùng cách, nhưng lifetime/ownership vẫn phải đúng.

---

# 72. Channel send

```axiom
channel.send(x)
```

nếu channel nhận ownership:

```text
x → MOVED
channel message → OWNED
```

Không copy ngầm.

---

# 73. Error paths

```axiom
fn foo() -> Result<T,E> {
    let x = make()
    bar()?
    use(x)
}
```

Nếu `bar()` trả Err:

```text
cleanup(x)
return Err
```

Verifier phải chứng minh cleanup path.

---

# 74. Panic paths

Nếu panic profile = unwind:

```text
panic
 ↓
cleanup
 ↓
unwind
```

Nếu abort:

```text
panic
 ↓
abort
```

Không cần toàn bộ Drop chain nếu process chắc chắn terminate và profile semantic định nghĩa abort.

---

# 75. Nhưng resource semantics phải rõ

Axiom không được dùng:

> “program abort nên bỏ qua mọi cleanup”

như một optimizer shortcut không được định nghĩa.

Profile quyết định observable behavior.

---

# 76. `drop(x)` explicit

```axiom
drop(x)
```

state:

```text
OWNED
 ↓
DROPPED
```

Sau đó:

```text
use(x)
```

reject.

---

# 77. Drop idempotence?

Core không coi:

```text
drop(x)
drop(x)
```

là idempotent.

Lần thứ hai:

```text
ERROR AMOVE-03
use/drop of already dropped value
```

---

# 78. Drop implementation

User-defined:

```axiom
impl Drop for File {
    fn drop(mut_view<Self>) { ... }
}
```

hoặc semantic equivalent theo final syntax.

Compiler cần xác định:

```text
DropImplId
```

nhưng không biến Drop thành arbitrary exception mechanism.

---

# 79. Drop không fallible

Frozen rule:

```text
Drop → no recoverable Result
```

Nếu cần:

```text
file.close() -> Result<(), Error>
```

sau đó Drop là fallback deterministic release.

---

# 80. Drop không await

Drop không được:

```text
await
```

vì Drop là synchronous cleanup.

Async resource API phải có explicit async close.

---

# 81. Recursive Drop

Nested struct:

```text
struct A {
    b: B
}
```

Drop A phải cleanup B theo semantic rules.

Compiler có thể generate/drop-glue.

---

# 82. Drop glue

Không cần programmer viết:

```text
drop_A()
```

Compiler sinh:

```text
DropGlue<A>
```

và có thể inline/eliminate.

---

# 83. Drop glue specialization

Generic:

```text
Vec<T>
```

nếu `T: !Drop`:

```text
drop elements
```

có thể được loại bỏ.

Nếu:

```text
T: Drop
```

phải cleanup từng element.

---

# 84. Compile-time Drop

Comptime values cũng dùng ownership semantics.

Nhưng cleanup xảy ra trong:

```text
compiler execution environment
```

không tạo runtime Drop.

---

# 85. Static values

Program-lifetime static resource cần semantics riêng.

Không giả định:

```text
normal scope Drop
```

cho toàn bộ process lifetime object.

Nếu platform hỗ trợ process shutdown cleanup thì đó là explicit runtime/profile mechanism.

---

# 86. Global initialization

Không có implicit global constructor registry.

Global immutable constants có thể được materialize.

Global mutable/resource state phải explicit system/runtime mechanism.

---

# 87. Dataflow implementation

Đề xuất API:

```text
OwnershipAnalysis {
    fn initial_state(fn)
    fn transfer(block, state)
    fn join(a, b)
    fn equals(a, b)
}
```

Dùng framework chung:

```text
DataflowAnalysis<State>
```

đã được frozen trong architecture.

---

# 88. State representation

Không nên copy toàn bộ Place Tree cho mỗi CFG node.

Dùng persistent/interned structures:

```text
State {
    locals: BitSet / SparseMap
    move_paths: PersistentMap
    drop_flags: PersistentMap
}
```

Mục tiêu:

```text
O(changed facts)
```

thay vì:

```text
O(all locals)
```

cho mỗi instruction.

---

# 89. Worklist

Algorithm:

```text
worklist = [entry]

while worklist not empty:
    block = pop()
    input = join(predecessors)

    output = transfer(block, input)

    if output != old_output:
        push(successors)
```

---

# 90. Loop convergence

Join operation phải monotonic.

Không được:

```text
state A → B → A → B...
```

vô hạn.

---

# 91. Unknown state

Trong production verifier:

```text
UNKNOWN
```

không phải:

```text
safe
```

mà:

```text
cannot prove
```

→ reject nếu invariant yêu cầu proof.

---

# 92. Incremental verification

CompilerDB có thể cache:

```text
OwnershipSummary
```

theo:

```text
FunctionBodyFingerprint
DependencyFingerprint
CompilerSemanticVersion
```

Nếu body không đổi:

```text
reuse verification
```

---

# 93. Interprocedural summary

Không cần inline function để biết ownership.

Function signature có thể có semantic summary:

```text
OwnershipEffect {
    consumes arg #0
    borrows arg #1
    mut-borrows arg #2
    returns-owned
}
```

---

# 94. Ví dụ

```axiom
fn consume(s: String) {
    ...
}

fn test() {
    let s = make_string()
    consume(s)
}
```

Compiler biết:

```text
consume:
    arg0 = ownership consumed
```

nên tại caller:

```text
s → MOVED
```

---

# 95. Returned view

```axiom
fn name(s: String) -> Str
```

Không được tự động coi return là independent.

Summary:

```text
return view
provenance = arg0
```

Capability verifier tiếp tục xử lý lifetime.

---

# 96. Returned owned value

```axiom
fn make() -> String
```

summary:

```text
returns new ownership
```

caller:

```text
let s = make()
```

→ `s = OWNED`.

---

# 97. Borrow-like argument summary

```text
fn inspect(view<String>)
```

summary:

```text
does_not_consume(arg0)
creates READ capability
```

---

# 98. Mutating function

```text
fn normalize(mut_view<String>)
```

summary:

```text
does_not_consume(arg0)
requires WRITE capability
```

---

# 99. Function summary không thay verifier

Foreign/generic/opaque function nếu không có summary đủ tin cậy:

```text
conservative
```

Không được đoán.

---

# 100. FFI

C function:

```text
extern "C" fn foo(*mut T)
```

nếu không có contract:

```text
Ownership = conservative/unknown
```

Wrapper safe phải cung cấp contract.

---

# 101. Unsafe

Unsafe operation có thể establish trusted ownership precondition.

Nhưng sau boundary:

```text
verifier resumes
```

Không có:

```text
unsafe = everything valid
```

---

# 102. Raw pointer

Raw pointer không có ownership mặc định.

Ví dụ:

```text
p: *mut T
```

không tạo:

```text
Owned(T)
```

---

# 103. Unsafe reconstruction

Nếu:

```text
unsafe {
    make_owner_from_raw(p)
}
```

API contract có thể establish:

```text
Owned(T)
```

sau đó verifier quản lý ownership bình thường.

---

# 104. Memory safety boundary

226 đảm bảo các invariant:

```text
No use-before-init
No use-after-move
No double-drop
No invalid ownership transfer
No accidental ownership duplication
No missing cleanup
```

Capability verifier bổ sung:

```text
No dangling safe view
No conflicting safe access
```

---

# 105. Không đảm bảo mọi bug

Ví dụ:

```axiom
let index = user_input
array[index]
```

Ownership verifier không giải quyết bounds safety.

Đó là MIR bounds + range analysis.

Tương tự:

```text
integer overflow
data race
FFI contract violation
```

thuộc verifier/subsystem khác.

---

# 106. Proof obligation model

Mỗi operation tạo obligation.

Ví dụ:

```text
Move(x)
```

requires:

```text
x initialized
x owned
x not moved
x movable
```

---

# 107. Copy obligation

```text
Copy(x)
```

requires:

```text
x initialized
x accessible
type Copy
```

không consume x.

---

# 108. Drop obligation

```text
Drop(x)
```

requires:

```text
x initialized
x owns drop obligation
x not already moved
x not already dropped
no dependent capability
```

Một phần cuối thuộc capability verifier.

---

# 109. Assignment obligation

```text
x = value
```

requires:

```text
destination writable
```

Nếu destination đang OWNED và có Drop:

```text
old value must be dropped/replaced safely
```

---

# 110. Replace semantics

Ví dụ:

```axiom
x = new_value
```

nếu x đã chứa resource:

```text
drop(old_x)
x = new_value
```

hoặc compiler dùng move-assignment semantic đã định nghĩa.

Không được leak old resource.

---

# 111. Self assignment

Nếu semantic expression:

```text
x = x
```

phải được xử lý deterministic.

Không được:

```text
drop(x)
move(x)
```

theo thứ tự khiến source biến mất trước khi read.

Evaluation order và place overlap analysis xử lý trường hợp này.

---

# 112. Overlapping assignment

Ví dụ:

```text
x.a = x.b
```

MIR phải evaluate RHS/source semantics đúng trước khi mutation nếu cần.

Verifier không được dựa vào physical order.

---

# 113. Destruction order trong aggregate

Semantic Drop order:

```text
initialization order
```

không nhất thiết:

```text
physical memory order
```

---

# 114. No programmer lifetime annotations

Không có:

```text
'a
```

hoặc:

```text
where 'a: 'b
```

Compiler tự xây lifetime facts từ:

```text
CFG
Place
Capability
Escape
Suspension
```

---

# 115. Lifetime là derived fact

Axiom không cần first-class source lifetime syntax.

Verifier có thể tính:

```text
LiveRange(x)
```

hoặc:

```text
CapabilityLifetime(v)
```

nội bộ.

---

# 116. Lifetime shortening

Compiler có thể chứng minh:

```text
last_use(x) = instruction 20
```

và kết thúc semantic lifetime sau đó nếu không có observable destructor behavior cần giữ.

Nhưng phải preserve Drop semantics.

---

# 117. Last-use optimization

Ví dụ:

```text
use(x)
foo()
```

Nếu x không còn cần và Drop không có observable ordering conflict:

```text
Drop(x)
```

có thể sớm hơn scope end nếu language semantics cho phép.

Tuy nhiên default semantic Drop ordering phải được preserve khi observable.

---

# 118. Không tự ý early-drop observable resources

Ví dụ:

```text
let file = open()
do_work()
```

Drop của File có observable OS effect.

Compiler không thể tùy ý chuyển Drop lên trước `do_work()`.

---

# 119. Effect + ownership interaction

Drop có thể có effect:

```text
IO
Synchronize
Foreign
```

Do đó optimizer phải xem Drop effect.

---

# 120. Ownership verifier không phải optimizer

Nó chỉ chứng minh:

```text
legal
```

Không quyết định:

```text
fastest representation
```

---

# 121. Diagnostic quality

Mỗi ownership error nên có proof path.

Ví dụ:

```text
AMOVE-01 use of moved value

value: user.name

moved here:
    line 12: consume(user.name)

used here:
    line 15: print(user.name)

ownership state:
    user.name = MOVED
```

---

# 122. Conditional error

```text
AMOVE-04 possibly moved value
```

phải chỉ ra:

```text
path A: moved
path B: not moved
```

---

# 123. Uninitialized diagnostic

```text
AINIT-02 possibly uninitialized value

x is initialized only when:
    cond == true

control path reaching this use:
    cond == false
```

Đây rất quan trọng cho AI tooling.

---

# 124. Explain API

Compiler có thể expose:

```text
ax explain ownership x
```

trả:

```text
Initial: OWNED
Move: line 10
State after branch: MAYBE_MOVED
Use: line 14
Conclusion: rejected
```

---

# 125. AI không được sửa verifier

AI có thể đọc:

```text
OwnershipProof
```

và đề xuất:

```text
clone
move
reinitialize
change API
```

nhưng compiler vẫn tự verify patch.

---

# 126. Adversarial tests

Bắt buộc test:

```text
move twice
partial move
move then reinitialize
copy then use
drop twice
drop after move
return ownership
conditional move
loop move
match move
closure capture
async capture
spawn capture
channel transfer
FFI ownership
unsafe boundary
```

---

# 127. Test matrix

```text
Operation × TypeKind × CFGShape
```

Ví dụ:

```text
Move × Copy
Move × Drop
Move × PartialMove
Move × Enum
Move × Closure
Move × Async
Move × Loop
Move × Branch
```

---

# 128. Soundness checkpoint

Không được chuyển sang production compiler nếu chưa chứng minh bằng test suite:

```text
Every accepted ownership program
    satisfies ownership invariants

Every known invalid ownership pattern
    is rejected
```

---

# 129. Formal model

Có thể mô hình hóa transition:

```text
Γ ⊢ P : State
```

với:

```text
State =
    PlaceState
    + DropState
    + CapabilityDependency
```

Mỗi MIR instruction:

```text
State --instruction--> State'
```

Nếu precondition không thỏa:

```text
reject
```

---

# 130. Core theorem mục tiêu

Axiom compiler cần hướng tới theorem:

> Nếu một chương trình được compiler chấp nhận ở Verified MIR, thì chương trình đó không thực hiện use-after-move, double-drop, use-before-init hoặc safe ownership violation theo semantic model của Axiom.

Đây là **soundness target**, không phải tuyên bố formal proof hoàn chỉnh ngay phiên bản compiler đầu tiên.

---

# 131. Frozen invariants

```text
AOWN-20
Every owned value has an explicit compiler-tracked ownership state.

AOWN-21
Ownership state is tracked at Place granularity.

AOWN-22
Move consumes ownership.

AOWN-23
Copy does not consume ownership.

AOWN-24
Clone is explicit and never implicitly substituted for Move.

AOWN-25
A moved place cannot be read, moved, or dropped again until reinitialized.

AOWN-26
Partial moves are field-sensitive where permitted.

AOWN-27
Custom Drop types may prohibit partial moves.

AOWN-28
Drop-bearing types are not Copy.

AOWN-29
Reinitialization restores ownership of the reinitialized place.

AOWN-30
Returning an owned value transfers ownership rather than dropping it locally.

AOWN-31
Ownership transfer through consuming calls is explicit in MIR.

AOWN-32
Ownership transfer through channels is explicit.

AOWN-33
Closure capture has explicit ownership semantics.

AOWN-34
Async state preserves ownership semantics across suspension.

AOWN-35
Spawned tasks preserve ownership transfer semantics.

AOWN-36
Safe views do not transfer ownership.

AOWN-37
Raw pointers do not implicitly establish ownership.

AOWN-38
Unsafe operations may establish explicit trusted ownership preconditions.

AOWN-39
Safe verification resumes after an unsafe boundary.

AINIT-20
Every local starts in a defined initialization state.

AINIT-21
Reads require definite initialization.

AINIT-22
MAYBE_INIT is never treated as initialized.

AINIT-23
Branch joins conservatively combine initialization states.

AINIT-24
Loop analysis reaches a sound fixed point.

AINIT-25
Enum payload initialization follows active-variant semantics.

ADROP-20
Every Drop obligation is tracked explicitly.

ADROP-21
Every owned Drop value has at most one semantic destruction path.

ADROP-22
Moved values are not dropped.

ADROP-23
Dropped values are not dropped again.

ADROP-24
Required cleanup occurs on all applicable exits.

ADROP-25
Cleanup order is deterministic.

ADROP-26
Default cleanup follows reverse initialization order.

ADROP-27
Physical field layout does not determine semantic Drop order.

ADROP-28
Drop does not implicitly perform recoverable error propagation.

ADROP-29
Drop cannot await.

ADROP-30
Drop semantics are preserved across panic/unwind profiles.

ADROP-31
Drop flags are runtime state only when static analysis cannot eliminate them.

ADROP-32
Drop glue may be generated automatically.

ADROP-33
Drop glue is subject to ordinary optimization after verification.

AVERIFY-100
Ownership verification is a correctness boundary.

AVERIFY-101
Failure to prove an ownership invariant results in rejection.

AVERIFY-102
Unknown ownership state is never treated as safe.

AVERIFY-103
Ownership analysis is deterministic.

AVERIFY-104
Ownership analysis is independent of optimization level.

AVERIFY-105
Ownership facts are available to downstream capability and optimization passes.

AVERIFY-106
Accepted Verified MIR satisfies all ownership/init/drop invariants.
```

---

# 132. Kết quả kiến trúc

Sau 226, memory model của Axiom có hình dạng:

```text
                ┌──────────────────┐
                │      VALUE       │
                └────────┬─────────┘
                         │
                    ownership
                         │
                         ▼
             ┌──────────────────────┐
             │ Ownership Verifier   │
             │                      │
             │ Init                 │
             │ Move                 │
             │ Copy                 │
             │ Partial Move         │
             │ Drop                 │
             │ Cleanup              │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │ Capability Verifier  │
             │                      │
             │ view                 │
             │ mut_view              │
             │ alias                │
             │ provenance           │
             │ region               │
             └──────────┬───────────┘
                        │
                        ▼
                ┌──────────────┐
                │ Verified MIR │
                └──────────────┘
```

Điểm đáng chú ý là **programmer không phải viết lifetime/borrow annotation**, nhưng compiler vẫn có một hệ thống ownership analysis rất nghiêm ngặt bên dưới.

---

# BOOTSTRAP-227 — CAPABILITY / VIEW / MUT_VIEW VERIFIER

Bước tiếp theo sẽ xử lý phần còn lại của memory safety:

```text
view<T>
mut_view<T>
provenance
region
aliasing
READ / WRITE capability
disjoint fields
slice ranges
iterator invalidation
owner ↔ capability lifetime
relocation
escape
returning views
closure-held views
async-held views
GPU DeviceView
FFI views
unsafe → safe capability
```

Đây là task sẽ quyết định liệu Axiom có thực sự đạt được mục tiêu **“không có `&T`, `&mut T`, lifetime syntax, nhưng compiler vẫn có alias analysis đủ mạnh để tối ưu như `restrict` khi có proof”** hay không.