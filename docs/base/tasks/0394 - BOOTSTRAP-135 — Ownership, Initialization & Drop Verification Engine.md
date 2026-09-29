# BOOTSTRAP-135 — Ownership, Initialization & Drop Verification Engine

**Trạng thái: FROZEN / COMPLETED**

Đây là một trong những thành phần cốt lõi nhất của Axiom. Mục tiêu là đạt được:

> **Memory safety mạnh nhưng không bắt programmer viết lifetime, borrow annotation hoặc reference syntax.**

Compiler phải tự suy luận ownership/lifetime từ MIR.

---

# 1. Vị trí của verifier

```text
Typed HIR
   ↓
MIR
   ↓
Structural MIR Validation
   ↓
Ownership Verification
   ↓
Initialization Verification
   ↓
Capability Verification
   ↓
Drop Verification
   ↓
Concurrency / Async / GPU / FFI Verification
   ↓
VERIFIED MIR
```

Không có bước:

```text
Programmer writes lifetime
        ↓
Borrow checker checks lifetime
```

Thay vào đó:

```text
Programmer writes intent
        ↓
Compiler derives semantic facts
```

---

# 2. Verification State

Verifier duy trì state tại mỗi program point:

```text
VerificationState {
    OwnershipState
    InitializationState
    CapabilityState
    DropState
    EscapeState
    StorageState
    ExecutionDomain
}
```

Các analysis dùng chung framework dataflow đã frozen.

---

# 3. Place Tree

Ownership không chỉ tracking Local.

Ví dụ:

```ax
struct User {
    id: u64,
    name: String,
    address: Address,
}
```

MIR verifier tạo:

```text
user
├── id
├── name
│   └── ...
└── address
    ├── city
    └── country
```

Đây là **Place Tree**.

---

# 4. Initialization State

Mỗi Place có trạng thái:

```text
UNINIT
INIT
MOVED
PARTIAL
DROPPED
```

Ví dụ:

```text
user.name = MOVED
user.id   = INIT
```

thì:

```text
user = PARTIAL
```

---

# 5. Join của initialization

Nếu CFG:

```text
        bb0
       /   \
      A     B
       \   /
        bb3
```

và:

```text
A: x INIT
B: x INIT
```

→ `x INIT`.

Nhưng:

```text
A: x INIT
B: x UNINIT
```

→ không được coi là INIT.

Compiler phải chứng minh mọi path đều initialized trước khi đọc.

---

# 6. Definite Initialization

Invariant:

> **Một Place chỉ được đọc khi compiler chứng minh Place đã được initialize trên mọi reachable path.**

Ví dụ:

```ax
var x: i32;

if condition {
    x = 10;
}

print(x);
```

→ reject.

---

# 7. Move Analysis

```ax
let a = make_resource();
let b = a;
use(a);
```

Nếu `a` non-Copy:

```text
Move(a)
```

sau đó:

```text
a = MOVED
b = INIT
```

`use(a)` → diagnostic.

---

# 8. Move không phải physical copy

Verifier chỉ ghi:

```text
Ownership:
    a → b
```

Không quan tâm backend có:

```text
mov register
memcpy
pointer transfer
```

hay hoàn toàn eliminate storage.

---

# 9. Copy Analysis

Nếu:

```ax
let a: i32 = 10;
let b = a;
use(a);
```

MIR:

```text
Copy(a)
```

Ownership:

```text
a = INIT
b = INIT
```

---

# 10. Copy không dựa trên bitwise layout

Một struct:

```text
struct X {
    ...
}
```

có thể bitwise-copy được nhưng không có nghĩa:

```text
X: Copy
```

`Copy` là semantic trait.

---

# 11. Clone

```ax
let b = a.clone();
```

Ownership:

```text
a = INIT
b = INIT
```

Nhưng compiler thấy một explicit operation:

```text
Call(Clone::clone)
```

Không có special hidden ownership shortcut.

---

# 12. Partial Move

Ví dụ:

```ax
let user = make_user();
let name = user.name;
```

Nếu `name` non-Copy:

```text
user.name → MOVED
user.id   → INIT
```

Whole `user`:

```text
PARTIAL
```

---

# 13. Partial Move và field independence

Nếu:

```ax
let id = user.id;
```

với `id: Copy`:

```text
user.id → INIT
id      → INIT
```

Không phải:

```text
user.id → MOVED
```

---

# 14. Partial move nhiều cấp

```ax
let city = user.address.city;
```

có thể dẫn tới:

```text
user.address.city = MOVED
user.address.country = INIT
user.name = INIT
user.id = INIT
```

Place Tree cho phép verifier xử lý chính xác.

---

# 15. Partial move + assignment

Sau:

```ax
let name = user.name;
```

có thể reinitialize:

```ax
user.name = new_name;
```

Khi đó:

```text
user.name = INIT
```

và `user` có thể trở lại:

```text
INIT
```

nếu mọi field cần thiết đều initialized.

---

# 16. Move rồi reinitialize

```ax
let x = make_resource();

let y = x;

x = make_resource();

use(x);
```

Hợp lệ.

State:

```text
x: INIT
 ↓ Move
x: MOVED
 ↓ Assign
x: INIT
```

---

# 17. Read after move

```ax
let y = x;
print(x);
```

→ `E_USE_AFTER_MOVE`.

Diagnostic nên chỉ rõ:

```text
x was moved here
use occurs here
```

---

# 18. Double move

```ax
let y = x;
let z = x;
```

→ reject.

Không có runtime check.

---

# 19. Move from borrowed/viewed region

Nếu một live:

```text
view<T>
```

đang phụ thuộc vào owner:

```text
owner
  ↓
view
```

không được move/destroy owner theo cách làm view dangling.

Ví dụ:

```ax
let v = view(x);
let y = x;
```

Nếu `x` bị consume thì verifier phải reject nếu `v` vẫn live.

---

# 20. Capability dependency graph

Verifier duy trì:

```text
Owner
  │
  ├── Capability A
  ├── Capability B
  └── Capability C
```

Mỗi capability:

```text
CapabilityId
Owner/Provenance
Region
Access
Lifetime
```

---

# 21. Capability lifetime

Compiler không yêu cầu programmer viết:

```text
'a
```

Thay vào đó:

```text
first_use
last_use
escape
suspension
owner lifetime
```

được phân tích tự động.

---

# 22. Example

```ax
let x = buffer();
let v = view(x);

use(v);
drop(x);
```

Nếu `v` không còn dùng sau `use(v)`:

```text
use(v)
↓
v dead
↓
drop(x)
```

hợp lệ.

Compiler không cần programmer viết scope/lifetime annotation.

---

# 23. Capability lifetime có thể ngắn hơn lexical scope

Ví dụ:

```ax
let v = view(x);

use(v);

do_other_work();

drop(x);
```

Dù `v` vẫn nằm trong lexical scope, semantic lifetime của capability có thể kết thúc sau:

```text
use(v)
```

Đây là một điểm quan trọng để tránh borrow-checker bureaucracy.

---

# 24. Capability state

```text
VALID
EXPIRED
MOVED
DROPPED
INVALID
```

`mut_view` không Copy.

---

# 25. Read capability

Nhiều:

```text
view<T>
```

có thể cùng tồn tại:

```text
x
├── view A READ
├── view B READ
└── view C READ
```

Không conflict.

---

# 26. Write capability

`mut_view<T>`:

```text
x
└── mut_view WRITE
```

Không được có:

```text
view READ
```

overlap trong cùng region nếu write semantics cần exclusivity.

---

# 27. Disjoint fields

Axiom cho phép:

```ax
let a = mut_view(user.name);
let b = mut_view(user.address);
```

nếu compiler chứng minh:

```text
Region(name)
DISJOINT
Region(address)
```

Điều này cho phép parallelism và optimization tốt hơn.

---

# 28. Unknown overlap

Nếu compiler chỉ biết:

```text
R1 = UNKNOWN
R2 = UNKNOWN
```

thì:

```text
R1 may overlap R2
```

Không được giả định disjoint.

---

# 29. Không dùng “best effort” cho safety

Nếu không chứng minh được:

```text
disjoint
```

thì safe code:

```text
reject
```

chứ không:

```text
assume safe
```

---

# 30. Ownership vs Capability

Đây là distinction trung tâm:

```text
Ownership
    = ai chịu trách nhiệm value?

Capability
    = ai được access region?

Synchronization
    = access nào được phép xảy ra đồng thời?
```

Không gộp ba khái niệm.

---

# 31. Drop Analysis

Drop verifier phải trả lời:

> **Mỗi owned resource sẽ được cleanup chính xác một lần trên mọi execution path hợp lệ.**

---

# 32. Drop trên normal path

```ax
fn f() {
    let a = make_a();
    let b = make_b();
}
```

Semantic:

```text
create a
create b
drop b
drop a
return
```

---

# 33. Drop trên early return

```ax
fn f() {
    let a = make_a();

    if condition {
        return;
    }
}
```

`return` phải đi qua cleanup:

```text
return
 ↓
drop(a)
 ↓
Return
```

---

# 34. Drop trên panic

Với:

```text
panic=unwind
```

cleanup graph phải bảo đảm:

```text
panic
 ↓
drop live resources
 ↓
unwind
```

Với:

```text
panic=abort
```

có thể bỏ unwind machinery.

---

# 35. Drop order

Default:

```text
reverse initialization order
```

Ví dụ:

```ax
let a = ...
let b = ...
let c = ...
```

→

```text
drop c
drop b
drop a
```

---

# 36. Field Drop order

Compiler phải phân biệt:

```text
semantic declaration order
```

với:

```text
physical layout order
```

Layout optimizer có thể reorder fields vật lý.

Drop order không thay đổi.

---

# 37. Custom Drop

Nếu type có:

```ax
impl Drop for Resource
```

compiler tạo DropGlue:

```text
Resource::drop
```

và verifier đảm bảo:

```text
exactly once
```

---

# 38. Drop cannot consume arbitrary aliases

Nếu resource có live capability:

```text
resource
  ↓
view
```

không được drop resource.

Phải:

```text
capability ends
↓
drop resource
```

---

# 39. Explicit `drop(x)`

```ax
drop(x);
```

semantic:

```text
request ownership cleanup now
```

Sau đó:

```text
x = DROPPED
```

Không đảm bảo physical memory đã được returned OS.

---

# 40. Drop after explicit drop

```ax
drop(x);
drop(x);
```

→ reject.

---

# 41. Explicit drop và reinitialization

```ax
drop(x);
x = make_resource();
use(x);
```

hợp lệ.

State:

```text
INIT
 ↓
DROPPED
 ↓
INIT
```

---

# 42. Drop cannot fail recoverably

`Drop` không trả:

```text
Result
```

và không được yêu cầu await.

Nếu resource cleanup có thể fail:

```ax
resource.close()?;
```

phải explicit.

Sau đó Drop chỉ là fallback deterministic cleanup.

---

# 43. Drop trong panic

Nếu:

```text
panic=unwind
```

và Drop lại panic:

```text
panic
 ↓
drop
 ↓
panic
```

không được để tạo recursive uncontrolled unwind.

Profile phải có policy:

```text
terminate/abort
```

---

# 44. Exactly-once cleanup

Verifier kiểm tra:

```text
∀ execution path:
    resource initialized
    ⇒ exactly one cleanup
```

trừ trường hợp resource ownership đã được chuyển.

---

# 45. Ownership transfer

Ví dụ:

```ax
let a = make();
let b = a;
```

cleanup responsibility:

```text
before:
a owns

after:
b owns
```

Không có hai Drop.

---

# 46. Function argument ownership

```ax
fn consume(x: Resource)
```

Call:

```ax
consume(r);
```

ownership:

```text
caller r
   ↓ Move
callee x
```

Caller không drop `r` sau call.

---

# 47. Return ownership

```ax
fn make() -> Resource
```

Return:

```text
callee local
   ↓ Move
caller result
```

Không tạo double-drop.

---

# 48. Caller allocation

Compiler có thể lower:

```text
fn make() -> Large
```

thành hidden caller result storage:

```text
make(out_ptr)
```

nhưng semantic ownership vẫn:

```text
callee creates
caller owns
```

---

# 49. Closure capture

Verifier xử lý closure environment như ordinary aggregate.

Nếu:

```ax
let r = resource;

let f = || use(r);
```

compiler xác định capture:

```text
MOVE
COPY
READ_VIEW
MUT_VIEW
```

tùy body.

---

# 50. Capture không dùng runtime reference mặc định

Closure không nhất thiết chứa:

```text
pointer to outer variable
```

Compiler có thể:

```text
move value into environment
```

hoặc:

```text
scalarize capture
```

---

# 51. Escape Analysis

Mỗi Place có escape state:

```text
NO_ESCAPE
ARGUMENT_ESCAPE
RETURN_ESCAPE
HEAP_ESCAPE
THREAD_ESCAPE
EXTERNAL_ESCAPE
UNKNOWN_ESCAPE
```

---

# 52. Stack promotion

Nếu:

```text
x: Box<T>
```

nhưng address không escape:

```text
NO_ESCAPE
```

compiler có thể eliminate heap allocation.

Đây là một trong các cơ chế giúp Axiom tránh “heap = chậm”.

---

# 53. Returning a view

```ax
fn get_view(x: T) -> view<U>
```

chỉ hợp lệ nếu returned view có provenance hợp lệ.

Ví dụ:

```ax
fn get_name(user: User) -> view<String>
```

nếu `user` là by-value local thì return view vào local là invalid.

---

# 54. Valid returned view

Nếu owner được truyền dưới capability/contract phù hợp:

```ax
fn name(user: view<User>) -> view<String>
```

returned capability có provenance:

```text
caller-owned User
    ↓
User.name
```

---

# 55. Escape verifier

Nếu capability:

```text
view(x)
```

được return:

```text
return v
```

verifier hỏi:

```text
Does owner outlive returned capability?
```

Nếu không chứng minh được:

```text
reject
```

---

# 56. Heap escape

Nếu:

```ax
store_global(v)
```

thì:

```text
v → External/Global Escape
```

Compiler phải kiểm tra provenance.

Không cho phép:

```text
local x
↓
global view(x)
```

---

# 57. Thread escape

Nếu:

```ax
spawn(|| use(x))
```

compiler xác định captured values.

Nếu move:

```text
x → ThreadEscape
```

và phải thỏa:

```text
Send
```

---

# 58. Share không thay ownership transfer

Nếu:

```ax
Arc<T>
```

capture sang thread:

```text
shared ownership
```

khác:

```text
Move unique T
```

Verifier phải phân biệt.

---

# 59. `Send`

Verifier hỏi:

```text
Does value safely transfer to another execution domain?
```

Nếu không:

```text
reject spawn
```

---

# 60. `Share`

Verifier hỏi riêng:

```text
Can value be safely concurrently accessed?
```

Không suy ra:

```text
Send ⇒ Share
```

hoặc:

```text
Share ⇒ mutable access
```

---

# 61. Await verification

Trước:

```text
await future
```

compiler tính:

```text
LiveAcrossAwait
```

Ví dụ:

```text
x → live
v → dead
future → live
```

Chỉ `x` và future cần state.

---

# 62. View across await

Nếu:

```ax
let v = view(x);
await something();
use(v);
```

mặc định reject nếu contract không chứng minh owner/storage/capability hợp lệ qua suspension.

Đây là cách Axiom tránh Pin/lifetime syntax mà vẫn an toàn.

---

# 63. Mutex guard

```ax
let guard = mutex.lock();
await future;
```

Mặc định:

```text
reject
```

vì synchronous lock guard không được giữ qua await.

---

# 64. Async-aware lock

Library có thể cung cấp:

```text
AsyncMutexGuard
```

với semantics riêng.

Verifier nhận capability contract của type đó.

---

# 65. Data race verification

Compiler tìm:

```text
concurrent accesses
```

và kiểm tra:

```text
READ + READ → OK
READ + WRITE → conflict
WRITE + WRITE → conflict
```

nếu không có synchronization.

---

# 66. Atomics

Atomic access không tạo:

```text
mut_view<T>
```

vào ordinary `T`.

Ví dụ:

```text
Atomic<i32>
```

có semantic type riêng.

---

# 67. Synchronization edges

Verifier/Concurrency analysis ghi:

```text
sequenced-before
synchronizes-with
happens-before
```

Các edges đến từ:

- atomics;
- mutex;
- channels;
- thread spawn/join;
- task synchronization;
- GPU events.

---

# 68. Unsafe boundary

Ví dụ:

```ax
unsafe {
    *ptr = value;
}
```

MIR không biến mọi thứ thành unchecked.

Thay vào đó:

```text
UnsafeOperation
    ↓
TrustedPrecondition
    ↓
subsequent safe verification
```

---

# 69. Unsafe không tắt verifier

Đây là invariant cực kỳ quan trọng.

Không có:

```text
unsafe
→ compiler stops checking everything
```

Thay vào đó:

```text
unsafe
→ programmer assumes machine-level responsibility
→ compiler continues checking everything it can
```

---

# 70. Trusted assumptions

Một unsafe operation có thể establish:

```text
pointer aligned
pointer valid
region initialized
region writable
```

nhưng chỉ trong phạm vi contract.

Compiler không được biến:

```text
unsafe { ... }
```

thành global trust.

---

# 71. Verification facts

Internal fact system:

```text
Fact {
    Kind
    Subject
    Region
    SourceOrigin
    ValidUntil
    Provenance
}
```

Ví dụ:

```text
Pointer p
VALID_FOR_WRITE
Region R
until block bb7
```

---

# 72. Fact invalidation

Nếu:

```text
owner moves
owner drops
storage reallocates
```

facts phụ thuộc vào owner phải invalidate.

Đây là cách ngăn stale proofs.

---

# 73. Vector reallocation

Ví dụ:

```ax
let v = view(vec);
vec.push(x);
use(v);
```

Nếu `push` có thể reallocate:

```text
v → invalidated
```

Compiler phải reject nếu `v` vẫn live.

---

# 74. `reserve`

```ax
vec.reserve(100);
```

không tự tạo stable-address guarantee vĩnh viễn.

Chỉ abstraction có contract rõ ràng mới tạo được:

```text
StableAddress
```

---

# 75. Stable storage

Nếu programmer cần:

```text
stable address
```

phải sử dụng abstraction như:

```text
stable storage
arena
pinned storage
handle
```

chứ không biến mọi reference thành stable pointer.

---

# 76. Verification complexity

Điểm quan trọng:

> Axiom không cố làm ownership verifier “đơn giản”.

Mục tiêu là:

```text
Compiler complexity ↑
Programmer complexity ↓
```

Verifier có thể thực hiện:

- dataflow;
- alias analysis;
- region reasoning;
- escape analysis;
- lifetime inference;
- constraint solving.

Programmer không cần biểu diễn các chi tiết đó bằng annotation trong trường hợp phổ biến.

---

# 77. Fail-safe rule

Nếu compiler không chứng minh được safety:

```text
safe code → reject
```

không:

```text
safe code → assume
```

Nhưng programmer luôn có đường xuống:

```text
unsafe
```

cho hệ thống-level code.

---

# 78. Performance implication

Verifier **không chạy runtime**.

Toàn bộ:

```text
ownership
lifetime
alias
capability
drop correctness
```

là compile-time.

Sau verification, metadata không observable có thể bị erase.

Đây chính là cơ sở cho:

> **memory safety không đồng nghĩa runtime overhead.**

---

# 79. Verification và optimization

Verifier cung cấp facts cho optimizer:

```text
verified non-alias
verified initialized
verified immutable
verified range
verified lifetime
verified no escape
```

Optimizer có thể dùng chúng để:

- bỏ bounds check;
- scalarize;
- stack promote;
- eliminate allocation;
- CSE;
- load/store forwarding;
- vectorize;
- reorder non-observable operations.

---

# 80. Nhưng optimizer không được tạo safety proof

Chiều phụ thuộc:

```text
Verifier
    ↓
facts
    ↓
Optimizer
```

Không:

```text
Optimizer
    ↓
maybe safe
    ↓
Verifier
```

Điều này giữ compiler architecture rõ ràng.

---

# 81. Dataflow framework

Tất cả verifier dùng chung:

```text
DataflowAnalysis<State> {
    initial()
    transfer(block, state)
    join(a, b)
    equals(a, b)
}
```

Các analysis:

```text
DefiniteInit
Ownership
Capability
Drop
Liveness
Escape
Send
Share
Await
```

có thể chạy độc lập hoặc phối hợp.

---

# 82. Fixed-point

CFG loops:

```ax
loop {
    ...
}
```

yêu cầu fixed-point analysis.

Verifier phải có:

```text
worklist
join
convergence
```

và termination guarantee.

---

# 83. Incremental verification

Nếu chỉ function:

```text
foo()
```

thay đổi, không cần verify toàn bộ package nếu dependency contract không đổi.

Cache key:

```text
FunctionId
+
GenericInstanceId
+
MIR fingerprint
+
semantic compiler version
```

---

# 84. Parallel verification

Các function độc lập có thể verify song song.

Trong function:

```text
independent CFG/dataflow regions
```

cũng có thể parallelize khi deterministic join semantics được bảo đảm.

---

# 85. Verification result

```text
VerificationResult {
    status: VERIFIED | REJECTED | INTERNAL_ERROR
    facts
    diagnostics
    provenance
}
```

`INTERNAL_ERROR` khác hoàn toàn với source error.

---

# 86. Compiler bug boundary

Nếu MIR đã thỏa tất cả invariant nhưng optimizer tạo:

```text
use-after-free
double-drop
data-race
```

thì đây là:

```text
compiler correctness bug
```

không phải UB của chương trình safe.

---

# 87. Diagnostic model

Ví dụ:

```text
error[E_USE_AFTER_MOVE]:
value `user.name` was moved

move occurs here:
    let name = user.name;

use occurs here:
    print(user.name);

note:
    `String` does not implement `Copy`

help:
    use `clone()` if an independent copy is intended
```

---

# 88. Diagnostic không ép Clone

Compiler có thể gợi ý:

```text
clone
```

nhưng không tự chèn Clone.

Điều này bảo vệ performance predictability.

---

# 89. Capability diagnostic

Ví dụ:

```text
error[E_CAPABILITY_CONFLICT]:
cannot create mutable access to `buffer`

existing read capability:
    view at line ...

requested:
    mut_view(buffer)

the two regions may overlap
```

---

# 90. Lifetime diagnostic không dùng `'a`

Axiom không cần báo:

```text
borrowed value does not live long enough
```

theo kiểu lifetime syntax.

Thay vào đó:

```text
error[E_CAPABILITY_LIFETIME]:
owner `x` would be destroyed while capability `v` is still live
```

và chỉ rõ:

```text
owner creation
capability creation
last required use
destruction
```

---

# 91. Điều này giải quyết vấn đề reference complexity

Programmer viết:

```ax
let v = view(data);
process(v);
drop(data);
```

không cần:

```text
<'a>
&'a
where 'a: ...
```

Compiler tự tính lifetime.

---

# 92. Nhưng Axiom vẫn không “giấu mọi thứ”

Ở semantic boundary, programmer vẫn phải explicit:

```text
view
mut_view
clone
move-sensitive ownership
unsafe
Arc
Mutex
Atomic
await
GPU transfer
FFI
```

Đây là nguyên tắc:

> **Ẩn complexity của implementation, không ẩn semantic cost.**

---

# 93. Đây là điểm cân bằng quan trọng

Không muốn:

```text
C/C++
→ quá nhiều programmer responsibility
```

nhưng cũng không muốn:

```text
GC language
→ runtime tự làm mọi thứ
```

Axiom chọn:

```text
Programmer
    ↓
semantic intent
    ↓
Compiler
    ↓
static verification
    ↓
zero/near-zero runtime overhead
```

---

# 94. Invariants

### `AVERIFY-20`
Every reachable read requires definite initialization.

### `AVERIFY-21`
Moved values cannot be read or moved again without reinitialization.

### `AVERIFY-22`
Ownership state is tracked at Place granularity.

### `AVERIFY-23`
Partial moves are represented explicitly.

### `AVERIFY-24`
Copy does not consume ownership.

### `AVERIFY-25`
Move transfers ownership responsibility.

### `AVERIFY-26`
Clone is explicit.

### `AVERIFY-27`
No implicit cloning is introduced by verification.

### `AVERIFY-28`
Every owned resource has deterministic cleanup.

### `AVERIFY-29`
Cleanup occurs on all required control-flow exits.

### `AVERIFY-30`
A resource is never semantically dropped twice.

### `AVERIFY-31`
Moved fields are not dropped.

### `AVERIFY-32`
Custom Drop restrictions are enforced.

### `AVERIFY-33`
Owner destruction is forbidden while dependent capabilities remain live.

### `AVERIFY-34`
Capability lifetime cannot exceed provenance lifetime.

### `AVERIFY-35`
Unknown overlapping regions are never assumed disjoint.

### `AVERIFY-36`
Proven disjoint regions may be accessed independently.

### `AVERIFY-37`
Mutable capabilities are exclusive.

### `AVERIFY-38`
Read capabilities may coexist when non-conflicting.

### `AVERIFY-39`
Raw pointers do not automatically create safe capabilities.

### `AVERIFY-40`
Integer-to-pointer conversion cannot establish provenance.

### `AVERIFY-41`
Unsafe operations establish only explicit trusted facts.

### `AVERIFY-42`
Trusted facts are invalidated when their preconditions cease to hold.

### `AVERIFY-43`
Returned capabilities preserve valid provenance.

### `AVERIFY-44`
Escaping capabilities satisfy their destination lifetime requirements.

### `AVERIFY-45`
Thread-crossing values satisfy Send requirements.

### `AVERIFY-46`
Concurrent shared access satisfies Share/synchronization requirements.

### `AVERIFY-47`
Safe data races are rejected.

### `AVERIFY-48`
Synchronous guards cannot cross await unless explicitly permitted.

### `AVERIFY-49`
Live values crossing await satisfy storage/execution requirements.

### `AVERIFY-50`
GPU domain crossings are explicitly verified.

### `AVERIFY-51`
Foreign operations are verified against their declared contracts.

### `AVERIFY-52`
Comptime execution obeys equivalent ownership and capability rules.

### `AVERIFY-53`
Generated code re-enters the same verifier.

### `AVERIFY-54`
Verification is independent of optimization level.

### `AVERIFY-55`
Verification results are deterministic.

### `AVERIFY-56`
Verification is incrementally cacheable.

### `AVERIFY-57`
Independent verification work may execute in parallel.

### `AVERIFY-58`
Verification diagnostics retain source provenance.

### `AVERIFY-59`
Safe semantic failures are compile-time errors, not runtime UB.

### `AVERIFY-60`
Verified MIR is the correctness boundary before optimization.

### `AVERIFY-61`
Optimizer may consume verifier facts but may not weaken them.

### `AVERIFY-62`
Compiler-generated semantic transformations are subject to verification.

### `AVERIFY-63`
No unverified capability may reach code generation.

### `AVERIFY-64`
No unverified ownership state may reach code generation.

### `AVERIFY-65`
No unverified Drop state may reach code generation.

### `AVERIFY-66`
Physical storage optimization cannot alter semantic ownership.

### `AVERIFY-67`
Physical relocation cannot violate an established stable-address contract.

### `AVERIFY-68`
Allocation elimination cannot invalidate capability provenance.

### `AVERIFY-69`
Verification state has explicit source/IR provenance.

### `AVERIFY-70`
Compiler internal verification failure is distinct from user program error.

---

# BOOTSTRAP-135 đã khóa

Đến đây Axiom đã có một chuỗi rất quan trọng:

```text
             SOURCE
                │
                ▼
        ┌───────────────┐
        │   Typed HIR   │
        └───────┬───────┘
                ▼
             Pattern
                │
                ▼
              MIR
                │
        ┌───────┴────────┐
        │   VERIFIER     │
        │                │
        │ Ownership      │
        │ Initialization │
        │ Capability     │
        │ Drop           │
        │ Escape         │
        │ Send/Share     │
        │ Async          │
        │ GPU            │
        │ FFI            │
        └───────┬────────┘
                ▼
          VERIFIED MIR
                │
                ▼
             OptIR
```

Đây chính là nền tảng để Axiom đạt mục tiêu ban đầu: **không bắt lập trình viên mang theo một đống lifetime/reference machinery nhưng vẫn có safety tĩnh mạnh và không cần GC**.

---

# BOOTSTRAP-136 — Capability & Alias Analysis

Task kế tiếp sẽ đi sâu vào phần còn lại của bài toán memory model:

```text
Verified MIR
     │
     ├── Region
     ├── Provenance
     ├── Alias
     ├── NoAlias
     ├── MustAlias
     ├── PartialAlias
     ├── MayAlias
     ├── Unknown
     ├── Range overlap
     ├── Field disjointness
     ├── Escape
     ├── Mutation
     └── Relocation
          ↓
       AliasInfo
```

Đây sẽ là phần quyết định trực tiếp **compiler có thể tối ưu mạnh đến mức nào** mà vẫn giữ memory safety.

Đặc biệt BOOTSTRAP-136 sẽ giải quyết:

- làm sao compiler tự suy ra `noalias` mà không cần programmer viết `restrict`;
- alias giữa `view`/`mut_view`;
- alias qua field;
- alias qua index/range;
- alias sau function call;
- alias qua closure;
- alias qua `Box`/`Vec`/`Arc`;
- alias khi storage relocate;
- alias trong multi-thread;
- alias ở FFI;
- cách chuyển capability facts thành optimizer `NoAlias`;
- và giới hạn chính xác để **UNKNOWN không bao giờ bị biến thành NO_ALIAS**.