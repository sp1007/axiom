# BOOTSTRAP-121 — Ownership, Capability & Lifetime Inference Engine

**Trạng thái: FROZEN / COMPLETED**

Đây là một trong những phần quan trọng nhất của Axiom.

Mục tiêu không phải tạo một bản sao của Rust Borrow Checker, mà là:

> **Compiler phải tự chứng minh ownership, lifetime, aliasing và capability; programmer chỉ mô tả ý định ở những ranh giới semantic cần thiết.**

Axiom vì vậy **không có lifetime syntax trong Core v0.1**.

---

# 1. Kiến trúc tổng thể

```text
Typed HIR
   │
   ├── Place Construction
   │
   ├── Ownership Inference
   │
   ├── Capability Inference
   │
   ├── Region / Provenance Analysis
   │
   ├── Escape Analysis
   │
   ├── Lifetime Inference
   │
   ├── Move / Partial-Move Analysis
   │
   ├── Drop Analysis
   │
   ├── Send / Share Analysis
   │
   └── Async / GPU / FFI Boundary Analysis
             │
             ↓
       Verified Ownership Model
             │
             ↓
            MIR
```

Không nên gọi toàn bộ hệ thống là "borrow checker".

Tên chính thức:

> **Ownership & Capability Verification Engine — OCVE**

---

# 2. Ba khái niệm phải tách biệt

Axiom có:

```text
Ownership
Capability
Lifetime
```

Chúng liên quan nhưng **không đồng nhất**.

### Ownership

Ai chịu trách nhiệm với value?

### Capability

Ai được phép truy cập region nào?

### Lifetime

Capability/value còn hợp lệ trong khoảng nào?

Ví dụ:

```ax
var user = User.new();
let name = view(user.name);
```

Ta có:

```text
user
 └── ownership = OWNED

name
 └── capability = READ
 └── provenance = user.name
 └── lifetime ⊆ lifetime(user)
```

---

# 3. Ownership state

Mỗi `Place` có trạng thái dataflow:

```text
UNINIT
OWNED
MOVED
PARTIALLY_MOVED
DROPPED
```

Có thể mở rộng nội bộ:

```text
BORROWED
CAPABILITY_ONLY
```

nhưng đây là verifier state, không phải source-level type.

---

# 4. Ownership transition

Các transition chính:

```text
UNINIT
  ↓ initialize
OWNED
  ↓ move
MOVED
```

hoặc:

```text
OWNED
  ↓ drop
DROPPED
```

hoặc:

```text
OWNED
  ↓ partial move
PARTIALLY_MOVED
```

---

# 5. Move

Ví dụ:

```ax
let a = make_buffer();
let b = a;
```

Nếu `Buffer` không Copy:

```text
a: OWNED
    ↓ MOVE
a: MOVED

b: OWNED
```

Move không yêu cầu compiler phải physically copy memory.

---

# 6. Copy

```ax
let a: i32 = 10;
let b = a;
```

Nếu `i32: Copy`:

```text
a: OWNED
b: OWNED
```

Không có ownership transfer.

Compiler có thể thực hiện:

```text
register reuse
constant propagation
no physical copy
```

---

# 7. Clone

```ax
let b = a.clone();
```

là operation semantic thực sự.

Compiler không được coi Clone là Copy.

```text
a: OWNED
b: OWNED
```

nhưng có thể có cost/runtime behavior.

---

# 8. Place Tree

Ownership không chỉ tracking variable.

Ví dụ:

```ax
struct User {
    id: u64,
    profile: Profile,
}
```

Place tree:

```text
user
├── user.id
└── user.profile
    ├── ...
```

Nếu:

```ax
let p = user.profile;
```

thì:

```text
user          PARTIALLY_MOVED
user.id       OWNED
user.profile  MOVED
```

---

# 9. Partial move

Partial move được phép với compiler-derived Drop:

```ax
let profile = user.profile;
use(user.id);
```

Nhưng:

```text
user.profile = MOVED
user.id = OWNED
```

`user` không thể được dùng như toàn object.

---

# 10. Custom Drop

Nếu user định nghĩa custom Drop cho:

```text
User
```

Axiom v0.1 áp dụng quy tắc đơn giản:

> **Không cho partial move từ type có custom Drop.**

Điều này giúp compiler không phải giải quyết quá nhiều semantic interaction.

---

# 11. Capability model

Capability:

```text
Capability {
    CapabilityId
    provenance
    region
    access
    lifetime
    storage_domain
    execution_domain
}
```

Access:

```text
READ
WRITE
MOVE
DROP
```

---

# 12. `view<T>`

`view<T>`:

```text
READ
non-owning
provenance-bound
duplicable
```

Ví dụ:

```ax
let a = view(data);
let b = a;
```

có thể tạo hai read capabilities:

```text
data
├── READ capability A
└── READ capability B
```

Không tạo ownership mới.

---

# 13. `mut_view<T>`

`mut_view<T>`:

```text
WRITE
non-owning
exclusive
nonduplicable
```

Ví dụ:

```ax
let v = mut_view(data);
```

Trong thời gian `v` còn active:

```text
data cannot be mutated through another capability
data cannot be mutably viewed again
conflicting READ capability cannot exist
```

---

# 14. READ + READ

Cho phép:

```text
READ
READ
READ
```

nếu cùng provenance/overlap.

---

# 15. READ + WRITE

Không cho:

```text
READ(data)
WRITE(data)
```

nếu regions có thể overlap.

---

# 16. WRITE + WRITE

Không cho:

```text
WRITE(data)
WRITE(data)
```

nếu overlap không chứng minh được là disjoint.

---

# 17. Region lattice

Compiler sử dụng:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Ví dụ:

```text
user.id
user.name
```

có thể:

```text
DISJOINT
```

---

# 18. Unknown không phải Disjoint

Đây là invariant cực kỳ quan trọng:

```text
UNKNOWN ≠ DISJOINT
```

Nếu compiler không chứng minh được hai regions độc lập:

> **Không được giả định chúng độc lập trong safe code.**

---

# 19. Ví dụ field-sensitive

```ax
struct Pair {
    a: i32,
    b: i32,
}
```

Compiler có thể cho:

```ax
fn update(a: mut_view<i32>, b: mut_view<i32>) {}

update(mut_view(p.a), mut_view(p.b));
```

vì:

```text
region(p.a) ∩ region(p.b) = ∅
```

---

# 20. Dynamic index

Ví dụ:

```ax
a[i]
a[j]
```

Compiler thường không chứng minh:

```text
i != j
```

Do đó:

```text
region(a[i])
region(a[j])
```

có thể là:

```text
UNKNOWN
```

và hai `mut_view` sẽ bị reject nếu cần đồng thời.

---

# 21. Explicit disjoint abstraction

Thay vì bắt programmer viết lifetime/unsafe logic, stdlib có thể cung cấp abstraction:

```ax
split_at_mut(buffer, index)
```

trả về:

```text
(mut_view<A>, mut_view<B>)
```

với contract:

```text
region(A) DISJOINT region(B)
```

Compiler verify abstraction boundary.

---

# 22. Đây là điểm khác Rust syntax

Programmer không cần viết:

```text
'a
'b
where 'a: 'b
```

Compiler tự infer:

```text
capability region
capability lifetime
provenance
```

---

# 23. Lifetime không phải một source variable

Lifetime được biểu diễn nội bộ:

```text
RegionLifetime {
    start
    required_uses
    end
}
```

Không nhất thiết là một thời gian runtime.

Nó chủ yếu là:

> **khoảng semantic mà capability phải còn hợp lệ.**

---

# 24. Lifetime inference

Ví dụ:

```ax
fn length(x: view<String>) -> usize {
    x.len()
}
```

Compiler thấy `x` chỉ được dùng trong function.

Do đó capability lifetime:

```text
entry(length)
        ↓
call len
        ↓
return
```

Không cần programmer khai báo.

---

# 25. Return view

Ví dụ:

```ax
fn name(user: view<User>) -> view<Str> {
    view(user.name)
}
```

Compiler phải chứng minh:

```text
lifetime(returned view)
    ⊆
lifetime(user provenance)
```

Nếu caller owner vẫn sống:

```text
valid
```

Nếu không:

```text
reject
```

---

# 26. Không cho dangling view

Ví dụ:

```ax
fn bad() -> view<i32> {
    var x = 10;
    return view(x);
}
```

Compiler phát hiện:

```text
provenance = local x
lifetime(x) ends at function return
return capability requires lifetime > function return
```

→ reject.

---

# 27. Owner → ephemeral view

Axiom cho phép:

```ax
fn print_name(x: view<User>) {}

var user = User.new();
print_name(user);
```

Compiler tự tạo ephemeral capability:

```text
user
  ↓
temporary READ capability
  ↓
call
  ↓
capability ends
```

Không tạo escaping view.

---

# 28. Escape analysis

Compiler phân loại:

```text
NO_ESCAPE
ARGUMENT_ESCAPE
RETURN_ESCAPE
HEAP_ESCAPE
THREAD_ESCAPE
EXTERNAL_ESCAPE
UNKNOWN_ESCAPE
```

Ví dụ:

```ax
fn foo(x: view<Data>) {
    consume(x);
}
```

Nếu `consume` không lưu view:

```text
NO_ESCAPE
```

---

# 29. View storage

Ví dụ:

```ax
let v = view(data);
```

đây là explicit capability.

Compiler phải track:

```text
v → provenance(data)
```

Nếu:

```ax
drop(data);
use(v);
```

reject.

---

# 30. Relocation barrier

Một điểm rất quan trọng với `Vec`.

```ax
var v = Vec<i32>();
let view = view(v);
v.push(x);
```

Nếu `push` có thể realloc:

```text
view → potentially invalid
```

Compiler phải reject operation có khả năng invalidate storage khi view đang sống.

---

# 31. Compiler có thể shorten lifetime

Ví dụ:

```ax
let view = view(v);
use(view);
v.push(x);
```

Nếu `view` không còn được sử dụng sau `use(view)`:

```text
lifetime(view) ends here
```

Compiler cho phép:

```text
use(view)
↓
capability dead
↓
v.push(x)
```

Đây là một trong những lợi ích lớn nhất của lifetime inference.

---

# 32. Programmer không cần `drop(view)`

Compiler tự xác định last use.

`drop(view)` vẫn tồn tại khi programmer muốn kết thúc capability sớm:

```ax
use(view);

drop(view);

v.push(x);
```

---

# 33. Ownership vs physical storage

Ví dụ:

```ax
let b = Box.new(Data);
```

Ownership engine chỉ biết:

```text
b owns Data
```

Không nhất thiết biết:

```text
heap address = 0x...
```

Storage optimization xảy ra sau.

---

# 34. Escape-based allocation

Nếu:

```ax
fn make() -> Data {
    let x = Data.new();
    return x;
}
```

compiler có thể:

```text
caller allocation
```

thay vì:

```text
allocate heap
copy
free
```

Ownership semantics không thay đổi.

---

# 35. Address observability

Nếu programmer làm:

```ax
unsafe {
    address_of(x)
}
```

thì storage identity trở thành observable.

Compiler không được tùy tiện:

```text
move x
relocate x
scalarize x
```

nếu phá contract.

---

# 36. Stable address

Stable address phải là explicit contract.

Ví dụ library abstraction:

```text
StableBox<T>
```

có thể yêu cầu:

```text
storage address remains stable
```

Compiler không được stack-promote/eliminate theo cách phá semantic contract.

---

# 37. Escape analysis và optimization

Nếu:

```text
NO_ESCAPE
```

compiler có thể:

```text
stack allocate
register allocate
scalarize
eliminate allocation
```

Nếu:

```text
THREAD_ESCAPE
```

thì cần storage phù hợp execution domain.

---

# 38. Closure interaction

Ví dụ:

```ax
var x = Data.new();

let f = || x.value;
```

Compiler xác định:

```text
capture x = READ
```

Nếu closure sống lâu hơn scope x:

```text
capture must become owning or otherwise preserve provenance
```

Compiler không được tạo dangling capture.

---

# 39. Mutable closure

```ax
let f = || {
    x.value += 1;
};
```

capture:

```text
WRITE
```

Do đó compiler phải đảm bảo closure invocation không tạo conflicting mutable access.

---

# 40. Move closure

```ax
let f = move || use(x);
```

capture:

```text
MOVE
```

Sau đó:

```text
x = MOVED
```

theo ownership semantics bình thường.

---

# 41. Async interaction

Ví dụ:

```ax
async fn foo(data: view<Data>) {
    await network();
    use(data);
}
```

Compiler phải reject nếu `data` không có storage/lifetime contract cho phép sống qua suspension.

Không có rule:

> "async function tự động được borrow".

---

# 42. Owned value qua await

```ax
async fn foo(data: Data) {
    await network();
    use(data);
}
```

Nếu `Data` được giữ trong Future state:

```text
FutureState {
    data: Data
}
```

hoàn toàn hợp lệ.

---

# 43. Send across await

Nếu Future có thể migrate execution domain:

```text
Future: Send
```

mọi state sống qua suspension phải đáp ứng Send requirements.

---

# 44. Spawn

```ax
spawn(foo(data));
```

`spawn` yêu cầu Future phù hợp execution domain.

Compiler kiểm tra:

```text
Future: Send
captured state: Send
storage: valid
```

Không cần programmer viết lifetime.

---

# 45. Mutex guard

Ví dụ:

```ax
let guard = lock(mutex);
await something();
use(guard);
```

mặc định reject:

```text
sync guard cannot cross await
```

trừ khi abstraction/runtime contract explicitly cho phép.

---

# 46. Channel

Channel là ownership boundary.

```ax
sender.send(data);
```

sau successful transfer:

```text
sender side: data = MOVED
receiver: ownership acquired
```

Không cần shared ownership.

---

# 47. Arc

```ax
let a = Arc.new(data);
```

Ownership model nhìn thấy:

```text
a owns Arc handle
```

Arc library tự quản lý shared ownership.

Compiler không coi refcount là Core primitive.

---

# 48. Unsafe boundary

Ví dụ:

```ax
unsafe {
    let p = raw_pointer(x);
    ...
}
```

Unsafe có thể establish:

```text
trusted provenance
trusted alignment
trusted initialization
trusted bounds
```

nhưng verifier sau đó tiếp tục tracking capability.

---

# 49. Unsafe không phải "tắt borrow checker"

Đây là quyết định quan trọng.

Không có:

```text
unsafe {
    // compiler ignores everything
}
```

Thay vào đó:

```text
unsafe operation
    ↓
trusted precondition
    ↓
safe semantic state reconstructed
    ↓
normal verification continues
```

---

# 50. Raw pointer → view

Ví dụ system wrapper:

```ax
unsafe fn as_view(p: *const T, len: usize) -> view<T> {
    ...
}
```

Unsafe contract phải establish:

```text
p valid
alignment valid
range valid
initialized
lifetime valid
```

Sau boundary:

```text
view<T>
```

được verifier quản lý như capability bình thường.

---

# 51. FFI

Foreign call mặc định:

```text
aliasing = UNKNOWN
```

trừ khi FFI contract khai báo rõ.

Do đó optimizer không tự giả định:

```text
foreign function does not mutate x
```

---

# 52. FFI borrowed pointer

Wrapper có thể chuyển:

```text
view<T>
```

thành C ABI:

```text
const T*
```

nhưng chỉ tại FFI boundary.

Compiler phải bảo đảm lifetime đủ dài cho foreign call.

---

# 53. GPU

`DeviceView<T>` phải có provenance:

```text
DeviceBuffer
```

Không được:

```text
HostBuffer → DeviceView
```

bằng implicit conversion.

Transfer là operation semantic rõ ràng.

---

# 54. GPU mutable capability

```ax
kernel(a, out);
```

compiler kiểm tra:

```text
a: READ device capability
out: WRITE device capability
```

và:

```text
region(a) ∩ region(out)
```

phải thỏa kernel contract.

---

# 55. Thread-local storage

TLS capability không được coi như ordinary global mutable memory.

Compiler biết:

```text
storage_domain = TLS
```

do đó mỗi execution domain có instance riêng.

---

# 56. Static storage

Static:

```ax
static CONFIG: Config = ...;
```

có lifetime chương trình.

Nhưng mutable static phải tuân thủ synchronization/capability rules.

Không có ngoại lệ:

> "global nên compiler bỏ qua alias checking".

---

# 57. Dataflow algorithm

OCVE dùng generic framework đã khóa:

```text
DataflowAnalysis<State> {
    initial()
    transfer(instruction, state)
    join(a, b)
    equals(a, b)
}
```

Forward analyses:

```text
ownership
initialization
capability creation
```

Backward:

```text
liveness
escape
drop requirement
```

---

# 58. Fixed-point

CFG:

```text
A → B → C
 \       ↑
  → D ───┘
```

Analysis lặp tới fixed point.

Compiler phải bảo đảm:

```text
termination
determinism
```

Không phụ thuộc traversal order.

---

# 59. Ownership lattice

Conceptually:

```text
             PARTIALLY_MOVED
             /            \
         OWNED             ...
        /     \
    UNINIT   MOVED
                \
               DROPPED
```

Implementation có thể dùng richer product state.

---

# 60. Capability state

Mỗi region có:

```text
READ(n)
WRITE(1)
NONE
```

và provenance.

Ví dụ:

```text
Region R:
    READ = 3
    WRITE = 0
```

hoặc:

```text
WRITE = 1
READ = 0
```

---

# 61. Capability conflict algorithm

Khi tạo capability mới:

```text
new_capability(region, access)
```

compiler query:

```text
for existing capability:
    relation = region_relation(existing, new)
    if conflict(relation, access):
        reject
```

---

# 62. Region conflict matrix

| Existing | New | Result |
|---|---|---|
| READ | READ | OK |
| READ | WRITE | conflict nếu overlap |
| WRITE | READ | conflict nếu overlap |
| WRITE | WRITE | conflict nếu overlap |
| MOVE | anything | ownership-dependent |
| DROP | anything | conflict |

---

# 63. Last-use lifetime shortening

Đây là optimization-safe semantic analysis.

Nếu:

```ax
let v = view(x);
foo(v);
bar(x);
```

thì compiler nhận:

```text
last use(v) = foo
```

và capability hết tại đó.

Không cần giữ đến cuối lexical scope.

---

# 64. Lexical scope không phải lifetime

Đây là nguyên tắc:

```text
scope ≠ lifetime
```

Scope quyết định name visibility.

Lifetime quyết định semantic validity.

Điều này giúp Axiom ít verbose hơn Rust.

---

# 65. Drop analysis

Compiler tính:

```text
must_drop(place)
```

ở mọi CFG exit.

Ví dụ:

```ax
fn foo() {
    let a = A();
    if condition {
        return;
    }
    use(a);
}
```

`a` phải được cleanup trên cả:

```text
normal exit
return path
panic/unwind path nếu profile yêu cầu
```

---

# 66. Drop flags

Compiler có thể tạo nội bộ:

```text
drop_flag
```

cho partial initialization/move.

Nhưng nếu dataflow chứng minh trạng thái tĩnh:

```text
drop_flag
```

có thể bị eliminate.

---

# 67. Exactly-once destruction

Invariant:

```text
Every owned Drop obligation is discharged exactly once.
```

Không:

```text
double drop
```

Không:

```text
leaked semantic ownership
```

trừ những API explicitly represent intentional leak/forget semantics trong unsafe/system layer.

---

# 68. Resource lifetime ≠ memory lifetime

Ví dụ:

```text
File
```

Drop có thể close OS handle.

Nhưng physical memory của `File` có thể:

```text
stack
register
heap
```

Hai lifetime khác nhau.

---

# 69. Memory lifetime ≠ capability lifetime

Một object có thể vẫn tồn tại:

```text
memory alive
```

nhưng capability đã hết:

```text
capability dead
```

Điều này cho phép compiler tự do reuse storage sau last use.

---

# 70. Ownership verifier không quyết định allocator

OCVE không nói:

```text
malloc
free
stack
heap
arena
```

Nó chỉ nói:

```text
ownership valid
lifetime valid
drop obligation valid
```

Allocation strategy thuộc later compiler/runtime/library layers.

---

# 71. Optimization independence

Một chương trình phải verify giống nhau với:

```text
-O0
-O2
-O3
-size
-LTO
```

Nếu optimization có thể làm chương trình "an toàn" hoặc "không an toàn":

> compiler architecture sai.

---

# 72. Unsafe contract representation

Compiler nội bộ lưu:

```text
UnsafeContract {
    preconditions
    established_facts
    provenance
    source_span
}
```

Không cần biến thành full dependent contract system.

---

# 73. Diagnostics

Ví dụ:

```ax
var v = Vec<i32>();
let x = view(v);
v.push(1);
use(x);
```

Diagnostic:

```text
EOWN_RELOCATION_CONFLICT

operation:
    Vec::push

reason:
    operation may relocate storage

active capability:
    READ view of v

conflicting region:
    v

suggestions:
    end the view before push
    or use an API with stable-address semantics
```

---

# 74. AI-readable explanation

Compiler có thể xuất:

```text
{
  "error": "EOWN_RELOCATION_CONFLICT",
  "owner": "v",
  "capability": "cap_17",
  "access": "READ",
  "operation": "Vec.push",
  "reason": "potential_relocation",
  "last_use": "line 8",
  "required_change": "capability must end before mutation"
}
```

Đây là một lợi thế lớn cho mục tiêu AI-assisted programming.

---

# 75. Complexity control

OCVE **không** cố giải quyết mọi alias relationship chính xác.

Thứ tự ưu tiên:

```text
1. Prove safe
2. Prove disjoint
3. Infer safe lifetime
4. Otherwise reject / require explicit abstraction
```

Không chạy solver vô hạn để cố chứng minh một chương trình.

---

# 76. Programmer escape hatch

Khi compiler không chứng minh được:

```text
UNKNOWN
```

programmer có thể dùng:

```text
safe library abstraction
```

trước khi dùng:

```text
unsafe
```

Mục tiêu là:

```text
unsafe = last resort
```

chứ không phải cách bình thường để làm compiler im lặng.

---

# 77. Core invariant

### `AOWN-80`
Every owned value has exactly one semantic owner.

### `AOWN-81`
Move transfers ownership.

### `AOWN-82`
Copy does not transfer ownership.

### `AOWN-83`
Clone is explicit.

### `AOWN-84`
Moved values cannot be read or moved again without reinitialization.

### `AOWN-85`
Partial moves are field-sensitive.

### `AOWN-86`
Custom Drop types prohibit partial move in Core v0.1.

### `AOWN-87`
Drop obligations are discharged exactly once.

### `AOWN-88`
Drop runs on all required control-flow exits.

---

# 78. Capability invariants

### `ACAP-80`
Every safe capability has valid provenance.

### `ACAP-81`
A capability cannot outlive its provenance.

### `ACAP-82`
READ capabilities may coexist.

### `ACAP-83`
Conflicting WRITE capabilities may not coexist.

### `ACAP-84`
READ and WRITE capabilities may not overlap incompatibly.

### `ACAP-85`
`mut_view` is nonduplicable.

### `ACAP-86`
Unknown overlap is never treated as disjoint.

### `ACAP-87`
Disjoint fields may have independent capabilities.

### `ACAP-88`
Live views prevent storage relocation when relocation would invalidate them.

### `ACAP-89`
Last-use analysis may shorten capability lifetime.

### `ACAP-90`
Safe dangling capabilities are rejected.

---

# 79. Lifetime invariants

### `ALIFE-20`
Scope and lifetime are distinct concepts.

### `ALIFE-21`
Programmer-written lifetime parameters are not required in Core v0.1.

### `ALIFE-22`
Capability lifetime is inferred from semantic use.

### `ALIFE-23`
Returned capabilities preserve provenance.

### `ALIFE-24`
A returned view cannot outlive its owner.

### `ALIFE-25`
Async suspension is a lifetime boundary.

### `ALIFE-26`
FFI calls are lifetime boundaries requiring explicit validation.

### `ALIFE-27`
Thread/task transfer requires valid storage lifetime.

### `ALIFE-28`
Stable-address requirements are explicit.

### `ALIFE-29`
Lifetime inference is deterministic.

### `ALIFE-30`
Lifetime inference must terminate.

---

# 80. Unsafe invariants

### `AUNSAFE-80`
Unsafe operations may establish trusted preconditions.

### `AUNSAFE-81`
Unsafe does not globally disable verification.

### `AUNSAFE-82`
Safe verification resumes after an unsafe boundary.

### `AUNSAFE-83`
Trusted facts are explicit in compiler state.

### `AUNSAFE-84`
Raw pointers do not automatically become safe capabilities.

### `AUNSAFE-85`
Integer addresses do not establish pointer provenance.

---

# 81. Concurrency invariants

### `ACONCUR-135`
Send is independent from Share.

### `ACONCUR-136`
Ownership transfer across execution domains is a Move.

### `ACONCUR-137`
Shared ownership does not imply mutable sharing.

### `ACONCUR-138`
A safe data race is impossible.

### `ACONCUR-139`
Synchronization capabilities obey ownership rules.

### `ACONCUR-140`
Synchronous guards cannot cross await unless explicitly supported.

### `ACONCUR-141`
Future state crossing execution domains must satisfy Send/storage requirements.

---

# 82. Final OCVE architecture

```text
                  Typed HIR
                      │
        ┌─────────────┼──────────────┐
        ↓             ↓              ↓
   Place Builder   Type Props    CFG Builder
        │             │              │
        └─────────────┼──────────────┘
                      ↓
             Ownership Analysis
                      ↓
             Capability Analysis
                      ↓
            Region/Provenance
                      ↓
              Escape Analysis
                      ↓
             Lifetime Inference
                      ↓
               Drop Analysis
                      ↓
         Async / Thread / GPU / FFI
                      ↓
              Safety Verification
                      ↓
                Verified MIR
```

Đây là điểm Axiom đạt được triết lý quan trọng nhất:

> **Programmer không quản lý lifetime bằng syntax; programmer quản lý ownership ở semantic boundaries, compiler suy luận phần còn lại.**

---

# BOOTSTRAP-121 hoàn tất

Kiến trúc Axiom lúc này đã khóa được chuỗi:

```text
Syntax
 ↓
AST
 ↓
HIR
 ↓
Type/Trait
 ↓
Ownership
 ↓
Capability
 ↓
Lifetime
 ↓
Verified MIR
```

Phần tiếp theo cần giải quyết là **làm sao chứng minh engine này thực sự đúng**, thay vì chỉ thiết kế lý thuyết.

# BOOTSTRAP-122 — Compiler Verification, Conformance & Adversarial Test Architecture

Task tiếp theo sẽ xây **hệ thống test/compiler correctness chính thức**, gồm:

```text
Language Conformance
Semantic Tests
Ownership Tests
Capability Tests
Trait Solver Tests
Compile-fail Tests
Diagnostic Tests
MIR Verification Tests
Optimization Equivalence
Backend Differential Testing
Fuzzing
Property-based Testing
Parser Fuzzing
Comptime Fuzzing
FFI Boundary Tests
GPU Verification
Async/Concurrency Stress Tests
Cross-target Tests
Bootstrap Tests
Reproducible-build Tests
Miscompilation Detection
Compiler Crash vs User Error
```

Đặc biệt sẽ khóa một nguyên tắc rất quan trọng:

> **Mỗi semantic rule của Axiom phải có ít nhất một executable conformance test và một negative/adversarial test; compiler không được coi “compile được” là bằng chứng correctness.**