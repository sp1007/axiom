Tiếp theo là **BOOTSTRAP-012 — Ownership + Capability Checker thực chiến**.

Đây là bước tôi muốn làm **trước Generic/Trait**, vì từ đây Axiom mới thực sự có được điểm khác biệt lớn nhất: **không bắt programmer viết lifetime/borrow checker như Rust, nhưng compiler vẫn bảo đảm memory safety và alias safety**.

# BOOTSTRAP-012 — OWNERSHIP + CAPABILITY EXECUTION MODEL

## 1. Mục tiêu

Axiom cần đạt:

```text
Programmer:
    không viết lifetime
    không viết borrow annotation
    không quản lý reference count
    không viết GC hint

Compiler:
    biết ownership
    biết lifetime
    biết alias
    biết provenance
    biết capability
    biết escape
    biết Drop
```

Nguyên tắc:

> **Compiler chịu trách nhiệm chứng minh; programmer chỉ phải diễn đạt semantic intent.**

---

# 2. Không gọi đây là Rust Borrow Checker

Mặc dù có một số vấn đề tương tự, architecture nên khác.

Rust có source-level concepts rất mạnh:

```text
'a
&'a T
&'a mut T
where ...
```

Axiom không đưa những thứ này lên source level.

Thay vào đó programmer chỉ gặp:

```axiom
view<T>
mut_view<T>
```

ở những semantic boundary cần thiết.

Ví dụ:

```axiom
fn sum(a: view<[i32]>) -> i32
```

hoặc:

```axiom
fn sort(a: mut_view<[i32]>)
```

Không cần:

```text
'a
'b
'c
```

---

# 3. Ownership state machine

Mỗi owning Place có state:

```text
Uninit
Owned
PartiallyMoved
Moved
Dropped
```

Không phải mọi type đều cần tất cả state trong runtime.

Đây là **compiler fact**, không phải runtime state.

Ví dụ:

```axiom
let x = make();
```

Compiler:

```text
x = Owned
```

Sau:

```axiom
let y = x;
```

nếu `x` non-Copy:

```text
x = Moved
y = Owned
```

---

# 4. Copy

Nếu:

```axiom
struct Point {
    x: i32,
    y: i32,
}
```

và `Point: Copy`:

```axiom
let a = point;
let b = a;
```

thì:

```text
a = Owned
b = Owned
```

Không consume `a`.

Compiler có thể tối ưu physical representation hoàn toàn.

---

# 5. Move

Move là:

```text
ownership state transition
```

không phải:

```text
memcpy
```

Ví dụ:

```axiom
let b = move a;
```

semantic:

```text
a: Owned → Moved
b: Uninit → Owned
```

Physical implementation có thể là:

```text
register transfer
pointer transfer
SSA rename
memcpy
nothing
```

tùy optimizer.

---

# 6. Field-sensitive ownership

Ví dụ:

```axiom
struct User {
    id: u64,
    name: String,
}
```

Sau:

```axiom
let name = move user.name;
```

state:

```text
user
├── id   → Owned
└── name → Moved
```

Không phải:

```text
user → Moved
```

Đây là một khác biệt rất quan trọng.

---

# 7. Reinitialization

Sau:

```axiom
let name = move user.name;
```

cho phép:

```axiom
user.name = String("new");
```

state:

```text
user
├── id   → Owned
└── name → Owned
```

Đây giúp compiler không cần áp dụng một quy tắc cứng kiểu:

> moved object forever invalid.

Chỉ phần đã move mới invalid.

---

# 8. Capability

Ownership nói:

> Ai sở hữu resource?

Capability nói:

> Ai đang được phép truy cập resource đó, theo cách nào?

Axiom có hai capability chính:

```text
view<T>
mut_view<T>
```

---

# 9. `view<T>`

`view<T>`:

```text
READ capability
non-owning
duplicable
```

Ví dụ:

```axiom
fn print_point(p: view<Point>) {
    ...
}
```

Có thể có:

```text
view1 → READ
view2 → READ
view3 → READ
```

đồng thời.

Không có ownership transfer.

---

# 10. `mut_view<T>`

`mut_view<T>`:

```text
WRITE capability
non-owning
exclusive
move-only
```

Ví dụ:

```axiom
fn update(p: mut_view<Point>) {
    p.x = 42;
}
```

Trong cùng vùng:

```text
mut_view1 → WRITE
mut_view2 → WRITE
```

→ conflict.

---

# 11. Capability representation

Internal:

```text
Capability {
    id
    owner
    region
    access
    validity
    origin
    storage
}
```

`access`:

```text
READ
WRITE
```

`region`:

```text
Point
Point.x
Point.y
array[0..10]
...
```

`owner`:

```text
LocalId
FieldId
StorageId
```

---

# 12. Capability không phải pointer

Đây là một nguyên tắc cần giữ cực kỳ chặt:

```text
view<T>
```

không có nghĩa semantic là:

```text
*T
```

Nó là:

```text
compiler-verified access capability
```

Sau khi verification hoàn tất, compiler có thể erase capability metadata.

Runtime có thể chỉ còn:

```text
pointer
length
```

hoặc thậm chí:

```text
scalar
```

---

# 13. Owner → ephemeral view

Cho phép implicit conversion ở function call:

```axiom
fn read(p: view<Point>) -> i32 {
    return p.x;
}

let point = ...;

read(point);
```

Compiler tạo ephemeral capability:

```text
point
  ↓
READ capability
  ↓
call
  ↓
capability ends
```

Không cần viết:

```axiom
read(view(point));
```

trong trường hợp này.

---

# 14. Nhưng binding view phải explicit

Không cho:

```axiom
let v: view<Point> = point;
```

implicit.

Phải:

```axiom
let v = view(point);
```

Lý do:

```text
implicit temporary view
```

và:

```text
stored capability
```

là hai semantic situations khác nhau.

---

# 15. Tương tự `mut_view`

Function call:

```axiom
fn update(p: mut_view<Point>) {
    ...
}

update(point);
```

có thể implicit.

Nhưng:

```axiom
let p = mut_view(point);
```

là explicit.

Điều này giúp code bình thường gọn mà capability escape vẫn nhìn thấy được.

---

# 16. View lifetime

Compiler tự suy ra lifetime.

Ví dụ:

```axiom
let v = view(x);

use(v);
```

Capability sống đến:

```text
last use(v)
```

sau đó chết.

Không cần:

```text
v: &'a T
```

hay:

```text
drop(v)
```

---

# 17. Owner destruction

Nếu:

```axiom
let v = view(x);

drop(x);
use(v);
```

→ reject.

Không phải vì programmer quên lifetime annotation.

Compiler biết:

```text
x
└── owner of capability v
```

nên:

```text
destroy(x)
```

bị chặn.

---

# 18. Mutability conflict

Ví dụ:

```axiom
let a = view(x);
let b = mut_view(x);
```

→ reject nếu `a` còn live.

Nếu:

```axiom
let a = view(x);
use(a);

let b = mut_view(x);
```

→ OK.

Compiler dùng:

```text
last-use analysis
```

để kết thúc capability `a`.

---

# 19. Multiple reads

Cho phép:

```axiom
let a = view(x);
let b = view(x);
let c = view(x);

print(a);
print(b);
print(c);
```

vì:

```text
READ + READ
```

không conflict.

---

# 20. Multiple writes

Không cho:

```axiom
let a = mut_view(x);
let b = mut_view(x);
```

nếu regions overlap.

---

# 21. Read + Write

Không cho:

```axiom
let a = view(x);
let b = mut_view(x);
```

khi cả hai live.

---

# 22. Disjoint fields

Đây là phần làm Axiom thực dụng hơn nhiều.

```axiom
struct Point {
    x: i32,
    y: i32,
}

let a = mut_view(p.x);
let b = mut_view(p.y);
```

Compiler chứng minh:

```text
Region(p.x)
DISJOINT
Region(p.y)
```

→ OK.

Đây là lý do region model phải field-sensitive.

---

# 23. Nested regions

Ví dụ:

```text
Region(p)
Region(p.x)
Region(p.y)
```

Quan hệ:

```text
p
├── x
└── y
```

Do đó:

```text
p.x ⊂ p
p.y ⊂ p
p.x ∩ p.y = ∅
```

Compiler có thể dùng region algebra:

```text
SAME
DISJOINT
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

---

# 24. Unknown overlap

Đây là rule cực kỳ quan trọng:

> **Không chứng minh được disjoint ≠ disjoint.**

Ví dụ:

```axiom
fn f(a: mut_view<[i32]>, b: mut_view<[i32]>) {
    ...
}
```

Compiler không thể tự giả định:

```text
a != b
```

Do đó API này phải có contract/abstraction phù hợp nếu muốn cho phép đồng thời.

---

# 25. Không có source-level `restrict`

Không cần:

```c
restrict
```

trong v0.1.

Compiler chỉ sử dụng:

```text
proven capability disjointness
```

cho optimization.

Nếu programmer thực sự biết hai vùng không overlap nhưng compiler không chứng minh được, sau này có thể có explicit system abstraction.

Không nên đưa `restrict` vào mọi API ngay từ đầu.

---

# 26. Capability provenance

Mỗi capability có:

```text
origin
```

Ví dụ:

```axiom
let v = view(x);
```

origin:

```text
Owner(x)
```

Sau:

```axiom
let v2 = subview(v, 10..20);
```

origin:

```text
Capability(v)
```

và provenance chain:

```text
x
 ↓
v
 ↓
v2
```

Compiler biết `v2` vẫn phụ thuộc vào `x`.

---

# 27. Capability cannot transfer ownership

Ví dụ:

```axiom
fn f(v: view<String>) {
    ...
}
```

Không thể:

```text
view<String>
     ↓
ownership of String
```

được.

View chỉ cho phép READ.

Nếu muốn transfer:

```axiom
fn f(s: String)
```

→ Move.

---

# 28. `mut_view` cũng không transfer ownership

```axiom
fn sort(a: mut_view<[i32]>)
```

gọi:

```axiom
sort(array);
```

không làm:

```text
array → Moved
```

Sau call:

```text
array → Owned
```

nhưng compiler biết trong khoảng call:

```text
WRITE capability active
```

---

# 29. Capability across function calls

Ví dụ:

```axiom
fn update(x: mut_view<i32>) {
    *x = 42;
}

let a = 0;
update(a);
print(a);
```

Sau call capability kết thúc.

Do đó `print(a)` hợp lệ.

---

# 30. Returning view

Đây là nơi verifier phải nghiêm.

Không cho:

```axiom
fn bad() -> view<i32> {
    let x = 42;
    return view(x);
}
```

vì:

```text
x lifetime < returned view lifetime
```

Compiler phát hiện provenance invalid.

---

# 31. Returning view của parameter

Trường hợp:

```axiom
fn first(x: view<[i32]>) -> view<i32> {
    return subview(x, 0..1);
}
```

về semantics có thể hợp lệ vì returned capability vẫn phụ thuộc vào input.

Compiler cần kiểm tra:

```text
returned capability
    ↓
provenance
    ↓
input owner/capability
```

và caller phải giữ owner/capability cần thiết.

Không cần lifetime annotation.

---

# 32. Escape analysis

Compiler cần phân loại:

```text
NoEscape
LocalEscape
ReturnEscape
ArgumentEscape
GlobalEscape
UnknownEscape
```

Ví dụ:

```axiom
fn f() {
    let x = 42;
    use(x);
}
```

`x`:

```text
NoEscape
```

Có thể register.

---

# 33. Address-taking

Nếu:

```axiom
unsafe {
    let p = address_of(x);
}
```

storage identity có thể trở thành observable.

Compiler phải thận trọng hơn.

Điều này quay lại:

```text
Storage Identity
```

và:

```text
Value Identity
```

là hai khái niệm khác nhau.

---

# 34. Unsafe boundary

Ví dụ:

```axiom
unsafe {
    let p: *mut i32 = raw_pointer(...);
}
```

Unsafe không có nghĩa:

```text
compiler stop checking
```

Mà:

```text
programmer establishes trusted precondition
```

Ví dụ:

```text
raw pointer
    ↓
unsafe validation/assumption
    ↓
safe capability
    ↓
normal verifier resumes
```

---

# 35. Unsafe không phá ownership state

Ví dụ:

```axiom
let x = resource();

unsafe {
    raw_destroy(&x);
}

use(x);
```

Không được compiler mặc nhiên coi `x` vẫn Owned.

Unsafe boundary phải có semantic contract để cập nhật ownership state nếu operation ảnh hưởng đến ownership.

Nếu không có contract phù hợp → reject hoặc giữ trạng thái conservatively.

---

# 36. Closure capture

Ownership checker cũng phải dùng cùng model cho closure.

Ví dụ:

```axiom
let x = String("hello");

let f = || print(x);
```

Compiler suy ra capture:

```text
READ
```

Không cần programmer viết capture type.

---

# 37. Mutable closure

```axiom
let mut x = 0;

let f = || {
    x += 1;
};
```

capture:

```text
WRITE
```

Compiler tạo capability tương ứng.

---

# 38. Move closure

```axiom
let x = String("hello");

let f = move || use(x);
```

capture:

```text
MOVE
```

Ownership:

```text
x
 ↓
closure environment
```

Không cần heap.

Closure environment có thể nằm:

```text
register
stack
inline aggregate
heap
```

tùy escape.

---

# 39. Send / Share

Ownership checker chuẩn bị facts:

```text
Send
Share
```

Ví dụ:

```axiom
spawn(move || use(x));
```

Nếu task chạy execution domain khác:

```text
x : Send
```

phải đúng.

`Share` là vấn đề khác:

```text
concurrent read access
```

không đồng nghĩa:

```text
ownership transfer
```

---

# 40. Data race

Safe Axiom phải ngăn:

```text
WRITE + WRITE
WRITE + READ
```

đồng thời trên overlapping region giữa concurrent execution domains.

Nhưng:

```text
READ + READ
```

được phép nếu `Share`/capability model chứng minh hợp lệ.

---

# 41. Internal checker architecture

Tôi đề xuất:

```text
OwnershipChecker
CapabilityChecker
RegionEngine
EscapeAnalyzer
DropAnalyzer
```

nhưng dùng chung một:

```text
SemanticFacts
```

Không tạo 5 hệ thống hoàn toàn độc lập.

---

# 42. Dataflow

Ownership checker chủ yếu là forward dataflow:

```text
Block
  ↓
Transfer
  ↓
State
  ↓
Successors
  ↓
Join
```

State:

```text
OwnershipState
CapabilitySet
InitializationState
```

---

# 43. Branch merge

Ví dụ:

```axiom
var x: String;

if condition {
    x = make();
} else {
    x = make();
}

use(x);
```

Sau merge:

```text
x = definitely initialized
```

Nhưng:

```axiom
var x: String;

if condition {
    x = make();
}

use(x);
```

→ `x` có trạng thái:

```text
MaybeUninit
```

→ reject.

---

# 44. Ownership lattice

Có thể dùng lattice:

```text
                 Unknown
                /       \
          Owned          Moved
             \           /
             Partial
                |
              Uninit
```

Nhưng implementation thực tế nên dùng state riêng + field tree, thay vì ép toàn bộ thành một lattice đơn giản.

---

# 45. Loops

Loop:

```axiom
while condition {
    ...
}
```

có back-edge.

Verifier phải tìm fixed point.

Ví dụ:

```axiom
var x: String;

while condition {
    x = make();
}

use(x);
```

không thể giả định `x` initialized sau loop nếu loop có thể chạy zero lần.

---

# 46. Capability last-use

Ví dụ:

```axiom
let a = view(x);

print(a);

let b = mut_view(x);
```

Compiler thấy:

```text
last_use(a) = print(a)
```

nên:

```text
a capability ends
```

trước `mut_view`.

Đây là **non-lexical capability lifetime**.

Không cần annotation.

---

# 47. Nhưng không được dùng quá aggressive

Ví dụ:

```axiom
let a = view(x);

if condition {
    use(a);
}

let b = mut_view(x);
```

Compiler phải biết:

```text
a
```

không được coi là dead nếu có path chưa thực hiện use nhưng capability vẫn có semantic possibility.

Dataflow phải merge chính xác.

---

# 48. Capability verification trước optimization

Thứ tự:

```text
Typed HIR
    ↓
Ownership
    ↓
Capability
    ↓
Drop
    ↓
Verified MIR
    ↓
Optimization
```

Không được:

```text
Typed HIR
 ↓
aggressive optimization
 ↓
ownership verification
```

vì optimizer có thể làm mất thông tin semantic cần để chứng minh safety.

---

# 49. Sau verification có thể erase

Khi:

```text
owner valid
capability valid
alias safe
lifetime valid
```

đã được chứng minh:

```text
CapabilityToken
Region metadata
Borrow facts
```

có thể biến mất.

Native code không nhất thiết chứa chúng.

Đây là:

> **Proof-carrying compilation, not proof-carrying runtime.**

---

# 50. Diagnostics

Đề xuất nhóm:

```text
AX1401 use of moved value
AX1402 use of partially moved value
AX1403 use of uninitialized value
AX1404 double move
AX1405 invalid reinitialization
AX1406 owner destroyed while view is live

AX1410 mutable capability conflicts with read capability
AX1411 mutable capability conflicts with mutable capability
AX1412 overlapping capability
AX1413 unknown overlap
AX1414 capability escapes owner
AX1415 returned view has invalid provenance

AX1420 unsafe operation requires trusted precondition
AX1421 unsafe operation invalidates ownership state
AX1422 raw pointer cannot be converted to safe capability

AX1430 value is not Send
AX1431 value is not Share
AX1432 concurrent access conflict
```

Diagnostic phải chỉ ra **hai đầu của conflict**.

Ví dụ:

```text
AX1410 mutable access conflicts with active read access

write: p.x
read:  p

read capability created here: ...
write capability created here: ...
last required use: ...
```

Không chỉ báo:

```text
borrow error
```

---

# 51. MIR facts

Sau checker, MIR có thể mang:

```text
OwnershipFacts
CapabilityFacts
RegionFacts
EscapeFacts
DropFacts
```

Ví dụ:

```text
Value %4:
    owner = Local(3)

Capability %7:
    owner = Local(3)
    region = Field(x)
    access = WRITE
    valid = [bb2, bb4]
```

Sau verification/optimization có thể erase.

---

# 52. Test quan trọng nhất

### Move

```axiom
let a = make();
let b = a;
use(a); // fail
```

### Copy

```axiom
let a = Point{};
let b = a;
use(a); // pass
```

### Partial move

```axiom
let b = move a.x;
use(a.y); // pass
use(a.x); // fail
```

### Reinitialize

```axiom
let b = move a.x;
a.x = make();
use(a.x); // pass
```

### Read/read

```axiom
let a = view(x);
let b = view(x);
use(a);
use(b);
```

→ pass.

### Read/write

```axiom
let a = view(x);
let b = mut_view(x);
```

→ fail.

### Sequential read/write

```axiom
let a = view(x);
use(a);

let b = mut_view(x);
```

→ pass.

### Disjoint fields

```axiom
let a = mut_view(p.x);
let b = mut_view(p.y);
```

→ pass.

### Return dangling

```axiom
fn bad() -> view<i32> {
    let x = 1;
    return view(x);
}
```

→ fail.

---

# 53. Benchmark bắt buộc

Đây là điểm tôi muốn thêm vào BOOT-012.

Không chỉ test correctness.

Phải có:

```text
source
 ↓
-O0
 ↓
native
```

và kiểm tra compiler không tạo runtime overhead không cần thiết cho:

```text
view
move
Copy
Drop
ownership checking
capability checking
```

Ví dụ:

```axiom
fn sum(a: view<[i32]>) -> i32 {
    ...
}
```

sau compile không được mặc định có:

```text
runtime borrow counter
runtime lifetime object
runtime ownership metadata
GC metadata
```

nếu semantics không yêu cầu.

---

# 54. Một benchmark đặc biệt quan trọng

So sánh:

```text
Axiom view
C pointer + length
Rust slice
```

về native assembly.

Mục tiêu không phải compiler luôn phải giống byte-for-byte, mà:

```text
semantic abstraction
      ↓
no mandatory runtime cost
```

---

# 55. BOOT-012 invariants

```text
AOWN-30  Ownership Is A Compile-Time Semantic Property
AOWN-31  Move Transfers Ownership
AOWN-32  Move Does Not Require Physical Copy
AOWN-33  Copy Duplicates Semantic Value
AOWN-34  Copy Does Not Require Physical Copy
AOWN-35  Ownership Is Field Sensitive
AOWN-36  Partial Move Is Supported Where Permitted
AOWN-37  Reinitialization Restores Ownership
AOWN-38  Moved Values Cannot Be Read
AOWN-39  Uninitialized Values Cannot Be Read
AOWN-40  Drop Applies Only To Owned Initialized State

ACAP-30  view Is Read Capability
ACAP-31  mut_view Is Exclusive Write Capability
ACAP-32  view Does Not Transfer Ownership
ACAP-33  mut_view Does Not Transfer Ownership
ACAP-34  Multiple Read Capabilities May Coexist
ACAP-35  Conflicting Write Capabilities Are Rejected
ACAP-36  Read/Write Conflict Is Rejected
ACAP-37  Disjoint Regions May Be Accessed Independently
ACAP-38  Unknown Overlap Is Not Assumed Disjoint
ACAP-39  Capability Has Provenance
ACAP-40  Capability Cannot Outlive Provenance
ACAP-41  Owner Cannot Be Destroyed While Capability Is Live
ACAP-42  Ephemeral Call Views May Be Implicit
ACAP-43  Stored Views Require Explicit Creation
ACAP-44  Capability Lifetime Is Compiler Inferred
ACAP-45  Capability Proof May Be Erased
ACAP-46  Capability Semantics Are Independent Of Physical Representation

AESCAPE-20  Escape Analysis Is Compiler Internal
AESCAPE-21  NoEscape Enables Storage Optimization
AESCAPE-22  Observable Address Constrains Storage Optimization
AESCAPE-23  Returned Capability Must Preserve Provenance
AESCAPE-24  Global Capability Escape Requires Explicit Safe Contract

AUNSAFE-60  Unsafe Does Not Disable All Verification
AUNSAFE-61  Unsafe May Establish Trusted Preconditions
AUNSAFE-62  Safe Verification Resumes After Trusted Boundary
AUNSAFE-63  Unsafe Cannot Implicitly Restore Invalid Ownership
AUNSAFE-64  Raw Pointers Are Distinct From Safe Capabilities

ACONCUR-20  Send Represents Ownership Transfer Across Execution Domains
ACONCUR-21  Share Represents Concurrent Access Capability
ACONCUR-22  Send And Share Are Distinct
ACONCUR-23  Safe Concurrent Writes Require Exclusive Access
ACONCUR-24  Safe Concurrent Read Sharing Requires Valid Share Semantics
```

---

# 56. BOOT-012 gate

Milestone này chỉ pass khi:

```text
Ownership
    ✓

Initialization
    ✓

Partial move
    ✓

Reinitialization
    ✓

Drop
    ✓

view
    ✓

mut_view
    ✓

Region analysis
    ✓

Disjoint fields
    ✓

Last-use analysis
    ✓

Escape analysis
    ✓

Returned view validation
    ✓

Unsafe boundary
    ✓

MIR ownership facts
    ✓

MIR capability facts
    ✓

Compile-fail diagnostics
    ✓

-O0/O1/O2/O3 equivalence
    ✓
```

---

## Và đây là một quyết định rất quan trọng cho triết lý Axiom

Sau BOOT-012, mô hình của Axiom có thể tóm lại thành:

```text
                 PROGRAMMER
                      │
          ┌───────────┴───────────┐
          │                       │
      OWNERSHIP               CAPABILITY
      "của ai?"              "được làm gì?"
          │                       │
          └───────────┬───────────┘
                      │
                COMPILER PROOF
                      │
          ┌───────────┴───────────┐
          │                       │
       SAFE CODE               UNSAFE CODE
          │                       │
       verified            trusted boundary
          │                       │
          └───────────┬───────────┘
                      │
                 VERIFIED MIR
                      │
                ERASE PROOFS
                      │
                NATIVE MACHINE
```

Điểm khác biệt cốt lõi là **Axiom không cố làm cho programmer trở thành người quản lý lifetime**.

Programmer nói:

```axiom
fn sort(a: mut_view<[i32]>)
```

Compiler tự giải quyết:

```text
provenance
lifetime
alias
region
escape
ownership
drop
storage
```

và sau khi chứng minh xong, phần lớn những thứ đó **biến mất trước khi xuống machine code**.

Đây chính là nền tảng để Axiom đạt mục tiêu ban đầu: **ngôn ngữ đơn giản hơn C++/Rust ở tầng lập trình viên, nhưng không phải trả giá bằng GC hoặc runtime ownership machinery.**