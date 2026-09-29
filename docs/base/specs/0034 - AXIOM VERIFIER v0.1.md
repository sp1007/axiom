Tiếp tục. Bây giờ nên đi thẳng vào phần **quan trọng nhất của Axiom: AXIOM VERIFIER v0.1**.

Tôi muốn thiết kế nó theo hướng **compiler chứng minh chương trình an toàn**, nhưng không biến programmer thành người phải viết proof.

# AXIOM VERIFIER v0.1

## 1. Mục tiêu của Verifier

Verifier nhận:

```text
Typed MIR
   ↓
Ownership Analysis
   ↓
Initialization Analysis
   ↓
Region / Capability Analysis
   ↓
Effect Analysis
   ↓
Concurrency Analysis
   ↓
Drop / Cleanup Verification
   ↓
VERIFIED MIR
```

Sau bước này mới cho phép:

```text
Optimization
   ↓
LIR
   ↓
Machine Code
```

Điều quan trọng:

> **Optimizer chỉ được phép tối ưu Verified MIR.**

Như vậy compiler có thể rất phức tạp, nhưng semantic boundary vẫn cực kỳ rõ:

```text
                 SOURCE
                    ↓
              Typed MIR
                    ↓
             ┌─────────────┐
             │  VERIFIER   │
             └──────┬──────┘
                    ↓
              VERIFIED MIR
                    ↓
               OPTIMIZER
```

Nếu optimizer làm hỏng ownership/lifetime thì đó là compiler bug, không phải một chương trình hợp lệ trở thành không hợp lệ.

---

# 2. Abstract State

Mỗi basic block tại mỗi program point có một state.

```text
VerifierState {
    locals
    ownership
    initialization
    regions
    capabilities
    effects
    concurrency
    cleanup
}
```

Ví dụ:

```axiom
fn test() {
    var x = Buffer<u8>.new()
    use(x)
}
```

State:

```text
After new:

x:
    type          = Buffer<u8>
    ownership     = OWNED
    initialization= INIT
    region        = R1
    capability   = OWN
```

Sau:

```text
use(x)
```

nếu `use` nhận ownership:

```text
x:
    ownership = MOVED
```

Sau đó:

```axiom
use(x)
```

=> reject.

---

# 3. Ownership không nên chỉ là enum đơn giản

Không nên chỉ có:

```text
OWNED
MOVED
DROPPED
```

vì branch sẽ phá mô hình đó.

Ta cần lattice:

```text
                 UNKNOWN
                /       \
           OWNED       MOVED
             \          /
              MAYBE_OWNED
```

Nhưng thực tế nên tách **definite facts** thay vì cố nhét tất cả vào một enum.

Tôi đề xuất:

```text
OwnershipFact:

    DefinitelyOwned
    DefinitelyMoved
    DefinitelyDropped
    MaybeOwned
    MaybeMoved
    Partial
```

Trong đó:

```text
Partial
```

có cấu trúc con.

Ví dụ:

```text
Person
├── name  MOVED
├── age   OWNED
└── city  OWNED
```

---

# 4. Initialization phải là lattice riêng

Không nên trộn:

```text
ownership
```

với:

```text
initialization
```

Ví dụ:

```axiom
var x: Buffer<u8>

if condition {
    x = load()
}

use(x)
```

Ownership có thể vẫn là:

```text
not_owned
```

nhưng initialization là:

```text
MAYBE_INIT
```

Ta cần:

```text
Initialization:

UNINIT
INIT
MAYBE_INIT
```

và rule:

```text
READ requires INIT
```

---

# 5. Branch Join

Đây là chỗ verifier bắt đầu thực sự thú vị.

```axiom
var x = Buffer<u8>.new()

if condition {
    consume(x)
}

use(x)
```

Hai nhánh:

```text
true:
    x = MOVED

false:
    x = OWNED
```

Join:

```text
x = MAYBE_MOVED
```

Do đó:

```text
use(x)
```

=> reject.

---

Nhưng:

```axiom
var x = Buffer<u8>.new()

if condition {
    consume(x)
} else {
    consume(x)
}
```

Join:

```text
x = MOVED
```

=> hợp lệ.

Đây là lý do verifier phải sử dụng **path-sensitive dataflow**, ít nhất ở mức ownership.

---

# 6. Ownership Join Rule

Có thể formal hóa:

```text
OWNED  ⊔ OWNED  = OWNED

MOVED  ⊔ MOVED  = MOVED

DROPPED ⊔ DROPPED = DROPPED

OWNED  ⊔ MOVED   = MAYBE_MOVED

OWNED  ⊔ DROPPED = MAYBE_DROPPED

MOVED  ⊔ DROPPED = MAYBE_INVALID
```

Nhưng có một điểm:

`MAYBE_*` **không nhất thiết là error ngay tại join**.

Error chỉ xảy ra khi operation cần một fact chắc chắn.

Ví dụ:

```text
MAYBE_MOVED + READ
```

=> reject.

---

# 7. Loop cần fixed-point

Ví dụ:

```axiom
while condition {
    consume(buffer)
}
```

Lần đầu:

```text
buffer = OWNED
```

sau `consume`:

```text
buffer = MOVED
```

quay lại loop:

```text
MOVED ⊔ initial
```

=> state không còn chắc chắn.

Compiler phải phát hiện:

```text
buffer may be moved before next iteration
```

=> reject.

---

Nhưng:

```axiom
while condition {
    let item = create_item()
    process(item)
}
```

mỗi iteration:

```text
create_item
    ↓
OWNED
    ↓
process
    ↓
MOVED/DROPPED
    ↓
iteration end
```

iteration sau tạo object mới.

=> hợp lệ.

---

# 8. Không cần phân tích loop bằng symbolic theorem quá nặng

Đây là một điểm tôi muốn giữ.

Axiom không nên cố biến verifier thành theorem prover.

Ta dùng:

```text
forward dataflow
+
finite abstract state
+
fixed point
```

Ví dụ:

```text
Block A
   ↓
Block B ───→ Block C
   ↑           │
   └───────────┘
```

Verifier lặp:

```text
state(B)
state(C)
state(B)
...
```

cho tới khi:

```text
state_new == state_old
```

hoặc đạt conservative widening.

---

# 9. Region Algebra

Đây là phần giúp Axiom tránh borrow checker syntax.

Mỗi Place có region.

Ví dụ:

```axiom
struct Person {
    name: String
    age: i32
}
```

Compiler tạo:

```text
R0 = Person
R1 = Person.name
R2 = Person.age
```

Quan hệ:

```text
R1 DISJOINT R2
R1 CONTAINED_BY R0
R2 CONTAINED_BY R0
```

---

# 10. Region không chỉ là địa chỉ

Đây là điểm rất quan trọng.

Không nên định nghĩa:

```text
Region = memory address range
```

Region là **semantic memory identity**.

Ví dụ:

```text
Vec<u8>
```

có:

```text
logical region
storage identity
```

tách biệt.

```text
Vec
 ├── logical region R1
 └── storage S1
```

Sau realloc:

```text
Vec
 ├── logical region R1
 └── storage S2
```

View cũ:

```text
view
    provenance = S1
```

=> invalid.

---

# 11. Đây là cách xử lý Vec cực đẹp

```axiom
let v = Vec<i32>.new()

let a = view(v)

v.push(10)

use(a)
```

`push` có effect:

```text
WRITE(R_v)
MAY_RELOCATE(S_v)
```

`a` có:

```text
provenance = S_v
READ(R_v)
```

Verifier thấy:

```text
MAY_RELOCATE(S_v)
```

xung đột với active capability.

=> reject.

---

# 12. Nhưng `set` không nhất thiết invalidate view

```axiom
let v = Vec<i32>.new()

let a = view(v[0..10])

v.set(20, 100)

use(a)
```

Region:

```text
a = R[0..10]
set = R[20]
```

Nếu compiler chứng minh:

```text
R[0..10] DISJOINT R[20]
```

=> hợp lệ.

Đây là ưu điểm lớn của region analysis.

---

# 13. Capability là object semantic riêng

Tôi muốn chính thức hóa:

```text
Capability {
    provenance
    region
    access
    lifetime
}
```

Ví dụ:

```text
view(buffer)
```

tạo:

```text
Capability #17
    provenance = Storage S1
    region     = R1
    access     = READ
```

`mut_view`:

```text
Capability #18
    provenance = S1
    region     = R1
    access     = WRITE
```

---

# 14. Capability lifetime khác lexical scope

Ví dụ:

```axiom
let v = view(buffer)

read(v)

modify(buffer)
```

Nếu `read(v)` là last-use:

```text
Capability #1
    lifetime:
       create ───── read ──X
```

Sau đó:

```text
modify(buffer)
```

=> hợp lệ.

Không cần bắt programmer viết:

```text
drop(v)
```

hoặc tạo scope nhân tạo.

---

# 15. Nhưng compiler phải cực kỳ cẩn thận với closure

Ví dụ:

```axiom
let v = view(buffer)

let task = spawn_local({
    use(v)
})
```

Nếu closure escape:

```text
v capability
    ↓
closure
    ↓
task
```

thì `v` không còn là ephemeral local capability.

Compiler phải kiểm tra provenance.

Nếu `buffer` chết trước task:

```text
REJECT
```

Nếu closure không escape:

```axiom
apply({
    use(v)
})
```

compiler có thể inline/eliminate closure.

---

# 16. Effect System

Mỗi function cần semantic effect summary.

Ví dụ:

```axiom
fn read_age(p: view<Person>) -> i32
```

có:

```text
READ(arg0.age)
```

Trong khi:

```axiom
fn set_age(p: mut_view<Person>, x: i32)
```

có:

```text
WRITE(arg0.age)
```

Và:

```axiom
fn consume_file(file: File)
```

có:

```text
MOVE(arg0)
DROP(arg0)
RESOURCE_RELEASE
```

---

# 17. Effects phải phân thành hai tầng

### Internal effects

```text
READ
WRITE
MOVE
DROP
ALLOC
DEALLOC
SUSPEND
```

### Observable effects

```text
IO
ATOMIC
SYNC
VOLATILE
FFI
PANIC
TRAP
RESOURCE_RELEASE
```

Điều này cực kỳ hữu ích cho optimizer.

Ví dụ:

```axiom
let x = create_buffer()
drop(x)
```

Nếu allocation/deallocation không observable:

```text
ALLOC
DEALLOC
```

có thể bị eliminate.

Nhưng:

```text
MutexGuard
```

thì:

```text
DROP
    ↓
UNLOCK
    ↓
SYNC
```

observable.

Không được eliminate.

---

# 18. Function Summary phải có điều kiện

Ví dụ:

```axiom
fn maybe_write(flag: bool, x: mut_view<Data>)
```

effect không đơn giản:

```text
WRITE(x)
```

mà:

```text
if flag:
    WRITE(x)
else:
    no WRITE
```

Verifier không cần symbolic execution đầy đủ.

Có thể lưu:

```text
ConditionalEffect {
    condition = flag
    effect = WRITE(x)
}
```

hoặc conservatively:

```text
MAY_WRITE(x)
```

Ở v0.1 tôi nghiêng về **conservative summary** trước.

Đơn giản hơn:

```text
MAY_READ
MAY_WRITE
MAY_MOVE
MAY_DROP
```

sau đó tối ưu dần.

---

# 19. Unknown function call

Ví dụ FFI:

```axiom
extern @abi(C)
fn external_process(ptr: *mut Data)
```

Verifier không biết nó làm gì.

Không được giả định:

```text
READ only
```

Thay vào đó:

```text
UNKNOWN MEMORY EFFECT
```

=> conservative.

Có thể cho programmer/compiler contract:

```axiom
@ffi_effects(
    read(arg0),
    write(arg1)
)
extern @abi(C)
fn process(...)
```

Khi đó verifier sử dụng contract.

---

# 20. Unsafe không được “xóa state”

Đây là quyết định tôi rất muốn khóa.

Không nên:

```axiom
unsafe {
    ...
}
```

=> verifier:

```text
IGNORE EVERYTHING
```

Sai.

Thay vào đó:

```text
unsafe
```

cho phép các operation mà safe code không được phép:

```text
DEREF raw pointer
POINTER ARITHMETIC
REINTERPRET
VOLATILE
MANUAL MEMORY
```

nhưng verifier vẫn duy trì:

```text
type state
control flow
known ownership
known effects
ABI constraints
```

---

# 21. Raw pointer là escape hatch

Ví dụ:

```axiom
unsafe fn read_ptr(p: *const i32) -> i32 {
    *p
}
```

Compiler không chứng minh được:

```text
p != null
p aligned
p points to i32
p alive
```

Programmer chịu trách nhiệm.

Nhưng:

```text
*p
```

vẫn phải type-check thành:

```text
i32
```

và backend vẫn phải generate instruction hợp lệ.

---

# 22. Concurrency verifier

Bây giờ ghép tất cả.

Mỗi access có:

```text
AccessEvent {
    context
    region
    mode
    capability
    synchronization
}
```

Ví dụ:

```text
Task A:
    WRITE R1

Task B:
    READ R1
```

Verifier hỏi:

```text
same region?
conflicting access?
same execution period?
happens-before?
atomic?
lock?
channel transfer?
```

Nếu:

```text
WRITE + READ
+
same region
+
no synchronization
```

=> reject.

---

# 23. Happens-before graph

Ta có thể tạo graph nội bộ:

```text
Event A ───────→ Event B
```

Các cạnh được tạo bởi:

```text
thread spawn
thread join
channel send/receive
mutex unlock/acquire
atomic ordering
task completion
await/resume
```

Ví dụ:

```text
Task A
WRITE data
   │
   │ Release
   ↓
Atomic flag

Task B
Acquire flag
   │
   ↓
READ data
```

Graph:

```text
WRITE data
    ↓
Release
    ↓
Acquire
    ↓
READ data
```

=> hợp lệ.

---

# 24. Channel còn đơn giản hơn

```axiom
tx.send(data)
```

semantic:

```text
MOVE(data)
SYNC_SEND
```

và:

```axiom
let data = rx.receive()
```

semantic:

```text
SYNC_RECEIVE
OWNED(data)
```

Graph:

```text
producer
   │
 MOVE
   ↓
 SEND
   ↓
 RECEIVE
   ↓
 OWNED
consumer
```

Không cần shared memory.

---

# 25. Async verifier

Tại:

```text
await operation()
```

MIR:

```text
SUSPEND state_id
```

Verifier tạo:

```text
SuspensionState {
    live_values
    live_capabilities
    live_regions
    execution_context_requirements
}
```

Ví dụ:

```text
buffer      OWNED
connection  OWNED
view        READ
```

Nếu task migratable:

```text
buffer: Send ✓
connection: Send ✓
view provenance: valid ✓
```

=> suspend hợp lệ.

---

# 26. View qua await nên mặc định bị hạn chế?

Tôi muốn đưa ra **hai mức**.

### V0.1 conservative

Không cho:

```text
mut_view
```

sống qua `await`.

Vì nó tạo rất nhiều complexity và thường không cần thiết.

Cho phép:

```text
view<T>
```

qua `await` chỉ khi compiler chứng minh owner/state vẫn hợp lệ.

### Sau này

Có thể relax nếu verifier đủ mạnh.

Điều này giúp compiler v0.1 đơn giản hơn đáng kể.

---

# 27. Một nguyên tắc cực mạnh: `await` là semantic barrier

Tôi đề xuất:

```text
SUSPEND
```

được xem như một **effect boundary**.

Trước `await`:

```text
active capabilities
```

phải được kiểm tra.

Sau `await`:

```text
resume state
```

phải được kiểm tra lại.

Không được coi `await` đơn thuần như:

```text
CALL
```

---

# 28. Drop Elaboration

Sau khi verifier đã hiểu ownership:

```text
if condition {
    return x
}
```

compiler phải tự chèn cleanup.

Ví dụ:

```text
a = OWNED
b = OWNED

return a
```

MIR semantic:

```text
MOVE a
DROP b
RETURN a
```

Không cần programmer viết destructor logic.

---

# 29. Cleanup Graph

Compiler có thể tạo:

```text
normal path
     │
     ↓
 cleanup
     │
     ↓
 return

error path
     │
     ↓
 cleanup
     │
     ↓
 return error

panic path
     │
     ↓
 cleanup
     │
     ↓
 panic
```

Điều này đảm bảo:

```text
AOV-08
cleanup complete on every terminating path
```

---

# 30. Nhưng Drop không phải lúc nào cũng chạy khi `abort`

Nếu panic profile:

```text
--panic=abort
```

thì process terminate ngay theo semantics profile.

Nếu:

```text
--panic=unwind
```

thì cleanup cần chạy.

Do đó verifier/compiler phải biết:

```text
panic profile
```

khi elaborating cleanup.

---

# 31. Ownership verification và optimization

Đây là điểm rất quan trọng.

Source:

```axiom
fn foo() {
    let x = Buffer<u8>.new()
    process(x)
}
```

MIR semantic:

```text
ALLOC
MOVE x
CALL process
DROP
```

Optimizer có thể nhận ra:

```text
process
```

có thể dùng caller-provided storage.

Hoặc:

```text
Buffer allocation
```

không cần heap.

Có thể biến thành:

```text
stack/inline/register
```

miễn semantics không thay đổi.

Verifier không quan tâm physical location.

---

# 32. Đây chính là chỗ Axiom tránh “GC vs manual memory”

Axiom không nói:

```text
heap allocation = bad
stack allocation = good
```

Mà nói:

```text
semantic ownership
        ↓
compiler chooses storage
```

Ví dụ:

```text
Source:
Buffer<u8>

Possible machine implementation:

small  → inline
medium → stack
escaping → heap
arena   → arena
FFI     → external
```

Programmer không cần thay đổi code chỉ vì storage strategy thay đổi.

---

# 33. Abstract verifier state hoàn chỉnh

Tôi đề xuất state chính thức:

```text
VerifierState {
    OwnershipMap
    InitMap
    RegionMap
    CapabilitySet
    EffectState
    ContextState
    SyncState
    CleanupState
}
```

Trong đó:

```text
OwnershipMap:
    Place → OwnershipFact

InitMap:
    Place → InitFact

RegionMap:
    Place → Region

CapabilitySet:
    CapabilityId → Capability

EffectState:
    current semantic effects

ContextState:
    current execution context

SyncState:
    happens-before / synchronization facts

CleanupState:
    pending resources / drop obligations
```

---

# 34. Thuật toán tổng thể

```text
function verify(function):

    state = initial_state(function)

    worklist = [entry_block]

    while worklist not empty:

        block = pop(worklist)

        incoming = merge_predecessor_states(block)

        state = transfer(block, incoming)

        verify_accesses(state)

        verify_ownership(state)

        verify_capabilities(state)

        verify_effects(state)

        verify_concurrency(state)

        verify_cleanup(state)

        outgoing = state

        if outgoing != previous_state(block):
            update(block, outgoing)
            push(successors(block))

    verify_all_exit_paths()

    return VERIFIED
```

Đây là **forward dataflow analysis + fixed point**.

---

# 35. Nhưng cần thêm một thứ: diagnostic provenance

Khi reject:

```axiom
use(x)
```

compiler không nên chỉ nói:

```text
ERROR: use after move
```

Mà phải truy được:

```text
x moved here:
    line 12: consume(x)

x used here:
    line 18: use(x)
```

Nếu branch:

```text
x may have been moved here:
    line 12: consume(x)

other path leaves x owned.
```

Diagnostic ID:

```text
AX_OWN_0001
```

Machine-readable:

```text
{
    "code": "AX_OWN_0001",
    "kind": "use_after_move",
    "place": "x",
    "move_site": "...",
    "use_site": "...",
    "path_sensitive": true
}
```

Điều này cực kỳ quan trọng cho AI coding agent.

---

# 36. Axiom Verifier không nên phụ thuộc backend

Cùng source:

```text
x86-64
ARM64
RISC-V
WASM
```

phải nhận cùng semantic verdict.

```text
Source
  ↓
HIR
  ↓
MIR
  ↓
Verifier
  ↓
VERIFIED
  ├── x86 backend
  ├── ARM backend
  ├── RISC-V backend
  └── WASM backend
```

Backend không được nói:

> ARM không có instruction này nên chương trình invalid.

Đó là backend problem.

---

# 37. Một điều tôi muốn bổ sung: verifier certificate

Đây có thể là một feature rất mạnh về sau.

Verified MIR có metadata:

```text
VerificationCertificate {
    language_version
    verifier_version
    function_hash
    ownership_verified
    capability_verified
    concurrency_verified
    cleanup_verified
}
```

Không nhất thiết phải là formal proof.

Nó giống:

```text
"compiler đã đi qua semantic verification boundary"
```

Điều này rất hữu ích cho:

- incremental compilation
- cache
- distributed compilation
- compiler debugging
- AI agents
- formal validation về sau.

---

# 38. Về hiệu năng compiler

Một lo ngại hợp lý là:

> Verifier mạnh như vậy có khiến compiler chậm khủng khiếp không?

Không nhất thiết.

Vì:

```text
ownership
initialization
region
effects
```

đều là **finite dataflow analysis** trên MIR.

Ta không cần theorem proving tổng quát.

Có thể dùng:

```text
O(N × K)
```

hoặc gần như linear theo CFG trong nhiều trường hợp, với `K` là số lượng abstract states/facts.

Các phân tích đắt hơn như:

```text
alias analysis
escape analysis
interprocedural effect inference
```

có thể chạy ở các optimization tier khác nhau.

---

# 39. Quan trọng: Safe correctness không được phụ thuộc optimization

Ví dụ compiler không chứng minh được:

```axiom
a[i]
```

bounds-safe.

Thì:

```text
MIR:
BOUNDS_CHECK
```

được giữ lại.

Không được:

```text
"optimizer không chứng minh được"
→ undefined behavior
```

Axiom phải:

```text
cannot prove safe
        ↓
keep runtime check
```

chứ không phải:

```text
cannot prove safe
        ↓
UB
```

Đây là khác biệt rất lớn so với C/C++.

---

# 40. Kiến trúc hoàn chỉnh đến thời điểm này

Axiom hiện đã có một backbone khá rõ:

```text
                    AXIOM SOURCE
                          │
                          ↓
                     AST / HIR
                          │
                          ↓
                     TYPED MIR
                          │
             ┌────────────┼────────────┐
             ↓            ↓            ↓
        Ownership      Regions       Effects
             │            │            │
             └────────────┼────────────┘
                          ↓
                    Concurrency
                          │
                 ┌────────┴────────┐
                 ↓                 ↓
             Send/Share       Synchronization
                 │                 │
                 └────────┬────────┘
                          ↓
                       Verifier
                          │
                          ↓
                    VERIFIED MIR
                          │
             ┌────────────┼────────────┐
             ↓            ↓            ↓
         Optimize     Drop/Storage   Escape
             │            │            │
             └────────────┼────────────┘
                          ↓
                        Axiom LIR
                          ↓
                    Machine Backend
```

## Và triết lý cốt lõi đã rõ hơn

**Programmer-facing:**

```text
struct
fn
trait
generic
value
move
view
mut_view
Send
Share
Atomic
Mutex
Channel
async
unsafe
```

**Compiler-facing:**

```text
ownership lattice
initialization lattice
region algebra
capability lifetime
effect graph
happens-before graph
escape analysis
drop elaboration
storage optimization
```

Đây chính là hướng tôi nghĩ phù hợp nhất với mục tiêu ban đầu của bạn: **Axiom không cố làm compiler đơn giản; Axiom cố làm ngôn ngữ mà programmer phải suy nghĩ ít hơn, trong khi compiler suy nghĩ nhiều hơn.**

Bước kế tiếp hợp lý nhất là **đóng băng Verifier v0.1 bằng một bộ luật formal nhỏ**, đặc biệt là **Region Algebra + Ownership Join + Capability Lifetime + CFG/Loop rules**. Sau đó chúng ta có thể viết khoảng 30–50 chương trình adversarial và dùng chính chúng để kiểm tra xem mô hình có lỗ hổng trước khi bắt đầu code compiler.