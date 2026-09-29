Tiếp tục sang **COMPILER-004 — Ownership + Capability Checker**.

Đây là bước trung tâm để hiện thực hóa triết lý khác biệt của Axiom:

> **Programmer không viết lifetime/borrow annotations. Compiler tự chứng minh ownership, lifetime và aliasing.**

Ta không nên xây “Rust Borrow Checker phiên bản khác”. Axiom nên có **Ownership State Machine + Capability Graph + Region/Provenance Analysis**, và phần lớn chỉ tồn tại trong compiler.

# COMPILER-004 — OWNERSHIP + CAPABILITY CHECKER

## 1. Mục tiêu

Input:

```text id="z9qv8e"
Typed HIR
```

Output:

```text id="j6j2ep"
Verified HIR
```

với các semantic facts:

```text id="c2xg4a"
Ownership
Move/Copy
Drop
Capability
Provenance
Region
Alias
Escape
Capture
Send/Share
```

Sau phase này, compiler phải có thể khẳng định:

```text id="n5x0dk"
safe code has no use-after-move
safe code has no double-drop
safe code has no dangling view
safe code has no conflicting mutable capability
safe code has no invalid ownership transfer
safe code has no data race
```

Nhưng:

```text id="kq8y8n"
không yêu cầu programmer viết lifetime
không yêu cầu programmer viết borrow
không yêu cầu programmer viết region
```

---

# 2. Ba thứ phải tách biệt

Axiom cần phân biệt tuyệt đối:

```text id="6qum7a"
Value Lifetime
Resource Lifetime
Storage Lifetime
```

Ví dụ:

```axiom id="2c2gpr"
var file = File.open(path)?;
```

`file` có:

```text
value lifetime
```

File resource có:

```text
resource lifetime
```

Underlying OS handle có:

```text
storage/resource identity
```

Drop:

```axiom id="q4j0o8"
drop(file);
```

kết thúc ownership/resource obligation.

Nhưng không nhất thiết có nghĩa:

```text id="z4a8c9"
physical memory immediately deallocated
```

Đúng với AMEM-62 và AMEM-43/44.

---

# 3. Ownership state machine

Mỗi owning local/value có semantic state.

Tối thiểu:

```text id="xg2g8k"
Uninitialized
Owned
Moved
PartiallyMoved
Dropped
Invalid
```

Ví dụ:

```axiom id="n6vyd2"
let x = make();

use(x);

use(x);
```

state:

```text id="e9t8x2"
x: Uninitialized
    ↓
Owned
    ↓
Owned
    ↓
Moved? / Read depending use
```

Nếu `use(x)` yêu cầu move:

```text id="4u2ubp"
Owned → Moved
```

lần thứ hai:

```text id="3u4m4r"
Moved → ERROR
```

---

# 4. Copy không phải Move

Nếu:

```axiom id="a4x5n8"
let a = point;
let b = point;
```

và `Point: Copy`:

```text id="7y9q6h"
point remains Owned
```

vì semantic operation là:

```text id="gq7d6e"
COPY
```

Nếu không Copy:

```text id="y7d9tc"
point → Moved
```

và `b` nhận ownership.

---

# 5. Move là semantic transition

Axiom không yêu cầu physical copy khi:

```axiom id="a4zv2f"
let b = a;
```

compiler chỉ cần:

```text id="1q2f9s"
ownership(a) → none
ownership(b) → resource
```

Backend có thể:

```text id="5w8v8h"
register transfer
stack slot reuse
no instruction
```

Move không phải machine `memcpy`.

---

# 6. Copy classification

Compiler cần intrinsic semantic property:

```text id="q4g5jg"
is_copy(T)
```

Nếu:

```text id="l1d7y0"
Copy(T) == true
```

thì value use có thể copy.

Nếu:

```text id="1j0o7e"
Copy(T) == false
```

thì consuming use là Move.

Không suy ra Copy chỉ từ:

```text id="4b3i4q"
sizeof(T)
```

hay bitwise copyability.

---

# 7. Drop classification

Compiler cũng cần:

```text id="34k8z8"
has_drop(T)
```

Invariant:

```text id="0n1jv7"
has_drop(T) → !Copy(T)
```

Một value có resource obligation không thể bị copy một cách vô hạn.

---

# 8. Implicit Drop

Ví dụ:

```axiom id="03n4jp"
fn process() {
    let file = open()?;
    work(file);
}
```

Compiler tạo semantic:

```text id="9q7m3w"
scope exit
    ↓
Drop(file)
```

Programmer không phải viết:

```text id="ym3t8v"
defer file.close()
```

---

# 9. Cleanup graph

Không nên chèn `DROP` ngay vào HIR.

Tạo:

```text id="q9eq4u"
CleanupGraph
```

Mỗi control-flow edge biết resource nào cần finalize.

Ví dụ:

```axiom id="6nyq4b"
fn foo() -> Result<()> {
    let a = open_a()?;
    let b = open_b()?;

    if condition {
        return Err(error);
    }

    Ok(())
}
```

Compiler phải biết:

```text id="u1q9o7"
normal exit:
    drop(b)
    drop(a)

error return:
    drop(b)
    drop(a)
```

CleanupGraph sau đó được lower thành MIR Drop operations.

---

# 10. Reverse initialization order

```axiom id="44e8eq"
let a = A();
let b = B();
let c = C();
```

mặc định:

```text id="h7x7s3"
drop(c)
drop(b)
drop(a)
```

Đây là deterministic.

---

# 11. Branch merging

Ví dụ:

```axiom id="xj1mru"
let x = make();

if condition {
    consume(x);
} else {
    use(x);
}

use(x);
```

Compiler không thể đơn giản chọn một state.

Sau branch:

```text id="r2f1a6"
then:  x = Moved
else:  x = Owned
```

merge:

```text id="v1k9oe"
x = Moved OR Owned
```

→ use sau branch không hợp lệ nếu không có path nào đảm bảo ownership.

Diagnostics:

```text
x may have been moved on another control-flow path
```

Đây là dataflow analysis.

---

# 12. Ownership lattice

Ta có thể dùng abstract state:

```text id="6r7q7r"
BOTTOM
Owned
Moved
PartiallyMoved
MAYBE_MOVED
TOP
```

Nhưng implementation không nhất thiết phải expose lattice.

Compiler internally dùng:

```text
OwnershipFact
```

---

# 13. Partial move

Ví dụ:

```axiom id="r2t8wy"
struct User {
    id: u64,
    name: String,
}
```

```axiom id="v0l1n2"
let user = make_user();

let name = user.name;

use(user.id);
```

Nếu `User` có compiler-derived Drop, có thể:

```text id="l9qg3f"
user.name → Moved
user.id   → Owned
```

Sau đó Drop(user) chỉ drop:

```text id="d1w8q6"
user.id
```

và không drop `name` lần nữa.

---

# 14. User-defined Drop

Nếu:

```axiom id="z3x9dy"
impl Drop for User {
    fn drop(self) {
        ...
    }
}
```

thì partial move bị cấm.

Ví dụ:

```axiom id="n3k8q2"
let name = user.name;
```

→ error nếu `user` còn cần custom Drop.

Lý do custom Drop có thể phụ thuộc toàn bộ object invariant.

---

# 15. Drop order và fields

Struct:

```axiom id="t5w4ey"
struct S {
    a: A,
    b: B,
}
```

compiler-derived Drop:

```text id="4k3q0f"
drop(b)
drop(a)
```

nhưng layout memory có thể:

```text id="x2c1c8"
b
padding
a
```

Drop order không phụ thuộc physical layout.

---

# 16. View capability

Ví dụ:

```axiom id="4br8te"
let data = Buffer<i32>.new();

let v = view(data);
```

compiler tạo:

```text id="c8g0ey"
Capability {
    kind: READ
    owner: data
    provenance: data
    region: whole(data)
}
```

`v` không sở hữu data.

---

# 17. `view<T>` có thể duplicate

```axiom id="w1c2pz"
let a = view(data);
let b = a;
```

có thể tạo:

```text id="w7x1c3"
READ(data)
READ(data)
```

Không conflict.

Đây không được xem là ordinary `Copy`.

Đó là intrinsic capability semantics.

---

# 18. `mut_view<T>` không duplicate

```axiom id="p0n0m7"
let a = mut_view(data);
let b = a;
```

không hợp lệ.

Vì:

```text id="a3t8kr"
WRITE(data)
```

phải unique.

Move:

```axiom id="l9f5h0"
a → b
```

thì hợp lệ.

---

# 19. Owner → view implicit conversion

Đã đóng:

```axiom id="6phw7m"
fn sum(x: view<i32>) {}
```

cho phép:

```axiom id="g9g8d0"
sum(data);
```

Compiler tạo ephemeral capability:

```text id="0ub7x9"
data
  ↓
READ capability
  ↓
call
  ↓
capability expires
```

Không tạo escaping view.

---

# 20. Escaping view

Không cho:

```axiom id="h8n4t4"
fn bad(data: Buffer<i32>) -> view<i32> {
    view(data)
}
```

vì `data` local owner sẽ chết.

Compiler phải phát hiện:

```text id="1p3j3n"
returned capability depends on local owner
```

---

# 21. Valid return view

Nếu owner sống ngoài:

```axiom id="n2x8kj"
fn first(data: view<i32>) -> view<i32> {
    data
}
```

có thể hợp lệ.

Capability provenance:

```text id="z7y7i8"
return capability
    provenance = input capability
```

Caller quyết định owner lifetime.

---

# 22. Capability provenance

Mỗi capability:

```text id="p70jdd"
Capability {
    owner
    provenance
    region
    access
    origin
    validity
}
```

Ví dụ:

```text id="a5kg4c"
owner = Buffer#42
provenance = field(data)
region = [0..100]
access = READ
```

---

# 23. Region

Compiler cần internal region algebra:

```text id="m4k5y2"
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Ví dụ:

```axiom id="x2u6hj"
struct Pair {
    a: i32,
    b: i32,
}
```

```text id="x7w4n4"
region(pair.a)
region(pair.b)
```

→ `DISJOINT`.

---

# 24. Disjoint mutable access

Do đó:

```axiom id="0q9q4b"
let a = mut_view(pair.a);
let b = mut_view(pair.b);
```

có thể hợp lệ.

Vì:

```text id="0kgf8r"
WRITE(pair.a)
WRITE(pair.b)
```

và:

```text id="h9b5bf"
DISJOINT
```

---

# 25. Unknown overlap

Ví dụ:

```axiom id="c8p2pj"
let a = get_mut_view(...);
let b = get_mut_view(...);
```

nếu compiler không chứng minh được disjoint:

```text id="j1s2u7"
UNKNOWN
```

→ reject safe code.

Không được giả định:

```text id="iqw8oc"
UNKNOWN == DISJOINT
```

---

# 26. READ + WRITE

```axiom id="b0n4pk"
let r = view(data);
let w = mut_view(data);
```

conflict:

```text id="g8z2cw"
READ(data)
WRITE(data)
```

→ error.

---

# 27. WRITE + WRITE

```text id="4m7yvh"
WRITE(region)
WRITE(overlapping_region)
```

→ error.

---

# 28. READ + READ

```text id="m20vkn"
READ(region)
READ(region)
```

→ allowed.

---

# 29. MOVE + capability

Nếu:

```axiom id="p1b3e5"
let v = view(data);
move(data);
```

không hợp lệ.

Owner không được move/destroy trong khi capability còn live.

---

# 30. Drop + capability

```axiom id="w7f4j6"
let v = view(data);
drop(data);
```

→ error.

Invariant:

```text id="5x9u0v"
owner cannot be destroyed while dependent capability is live
```

---

# 31. Capability expiration

Compiler không cần lifetime syntax.

Ví dụ:

```axiom id="3r2k1s"
{
    let v = view(data);
    read(v);
}

drop(data);
```

Khi scope đóng:

```text id="6d4s9r"
v capability expires
```

sau đó owner có thể Drop.

---

# 32. Last-use analysis

Axiom có thể tối ưu capability lifetime dựa trên last use.

Ví dụ:

```axiom id="g7e8x1"
let v = view(data);

read(v);

do_expensive_work();

drop(data);
```

Capability thực sự hết sau:

```text id="7o9y5v"
read(v)
```

Không cần chờ lexical scope.

Điều này rất quan trọng cho performance và flexibility.

---

# 33. Đây là khác biệt lớn với lifetime syntax

Programmer viết:

```axiom id="p0r3y4"
let v = view(data);
read(v);
```

Compiler có thể internally suy luận:

```text id="f7k1o5"
region(v) = [instruction 20..35]
```

Programmer không cần biết region đó.

---

# 34. Closure capture

Ví dụ:

```axiom id="k0w4p3"
let x = String("hello");

let f = || print(x);
```

Compiler phân tích capture.

Các capture mode:

```text id="i5b7w2"
READ
MUTATE
MOVE
```

Ví dụ chỉ đọc:

```text id="l0g8p4"
capture x as READ capability
```

Nếu closure cần ownership:

```axiom id="h8f3d9"
let f = move || consume(x);
```

→ Move.

---

# 35. Không mặc định heap allocate closure

Closure:

```axiom id="o2u8w5"
let f = |x| x + factor;
```

compiler có thể:

```text id="7m1z0g"
stack
register
inline
heap
```

tùy escape analysis.

Không có:

```text id="a7y3s6"
closure → heap
```

bắt buộc.

---

# 36. Closure escape

Nếu:

```axiom id="8p4t6s"
fn make() -> impl Callable {
    let x = 10;

    || x + 1
}
```

compiler phải biến capture thành owned state.

Không thể giữ pointer vào local stack frame sau return.

Do đó closure capture tự động chuyển từ:

```text id="l5c1u8"
borrowed capability
```

sang storage hợp lệ, hoặc compiler reject nếu abstraction không cho phép.

---

# 37. Async và capability

Đây là constraint rất quan trọng.

Không cho:

```axiom id="p0g4u8"
async fn foo(data: Buffer<i32>) {
    let v = view(data);

    await something();

    use(v);
}
```

nếu `v` là borrowed capability không thể tồn tại qua suspension.

Compiler báo:

```text
capability cannot live across await
```

---

# 38. Nhưng owned value được phép

```axiom id="z7c4m1"
async fn foo(data: Buffer<i32>) {
    let owned = data;

    await something();

    use(owned);
}
```

được.

Future state machine sở hữu `owned`.

---

# 39. Why this matters

Future có thể được:

```text id="7g5d2f"
moved
suspended
resumed
migrated
```

Một borrowed pointer tới stack frame tạm thời rất nguy hiểm.

Do đó:

> **Owned values có thể cross suspension; ordinary borrowed capabilities không.**

Đúng với AASYNC baseline.

---

# 40. Thread transfer

Ví dụ:

```axiom id="8j6h0y"
Thread.spawn(move || {
    use(data);
});
```

Closure phải satisfy:

```text id="s2z4r9"
Send(Closure)
```

Compiler kiểm tra tất cả captured values.

---

# 41. View không tự Send

Một:

```text id="3n4g5v"
view<T>
```

không tự động trở thành Send chỉ vì representation là pointer+length.

Provenance của nó có thể phụ thuộc execution domain/local owner.

Compiler cần semantic property tương ứng.

---

# 42. `Arc` và view

```axiom id="8w0r3q"
let data = Arc::new(Buffer(...));
let v = data.view();
```

Capability:

```text id="m9h3x1"
owner = Arc<T>
provenance = shared storage
```

Nếu Arc clone giữ owner alive:

```axiom id="4s7d9p"
let other = data.clone();
```

thì capability có thể sống phù hợp với storage contract.

---

# 43. Nhưng view không biến thành owner

```axiom id="h8x4k2"
view<T>
```

không increment reference count.

Nếu cần giữ storage alive:

```axiom id="m5z1w7"
Arc<T>
```

là abstraction đúng.

Đây là distinction rất quan trọng:

```text id="g7y2s1"
view = access capability
Arc = ownership/lifetime
```

---

# 44. Escape analysis

Compiler cần xác định:

```text id="5v0p3h"
Does this value/capability escape?
```

Ví dụ:

```axiom id="f4r2k8"
fn foo() -> i32 {
    let x = 42;
    x
}
```

`x` không escape physically.

Compiler có thể:

```text id="s1k9p4"
register
```

Ví dụ:

```axiom id="v4w8z2"
fn foo() -> view<i32> {
    ...
}
```

capability provenance phải escape hợp lệ.

---

# 45. Ownership graph

Compiler nên duy trì:

```text id="7m4x9a"
OwnershipGraph
```

Nodes:

```text id="z6v0e3"
Value
Field
Storage
Resource
```

Edges:

```text id="w3r8q1"
OWNS
CONTAINS
BORROWS
DERIVES
MOVES_TO
DROPS
```

Ví dụ:

```text id="q0s5h2"
user
 ├── owns id
 └── owns name

view(user.name)
       │
       └── READ capability
```

---

# 46. Capability Graph

Tách riêng:

```text id="j2n7x4"
CapabilityGraph
```

Node:

```text id="k6b1s3"
CapabilityId
```

Properties:

```text id="w7d2f9"
owner
provenance
region
access
origin
liveness
```

Edges:

```text id="c5q8v1"
DERIVED_FROM
DEPENDS_ON
INVALIDATED_BY
```

---

# 47. Vì sao tách OwnershipGraph và CapabilityGraph?

Bởi vì:

```text id="0r8j6m"
Ownership != Access
```

Một owner có thể có:

```text id="e5c2w4"
0 capability
1 capability
10 read capabilities
```

Một capability không tạo ownership.

Nếu trộn hai thứ, compiler sẽ rất khó xử lý:

- Arc;
- Mutex;
- GPU;
- async;
- mmap;
- DMA;
- FFI.

---

# 48. Memory region

Capability phải có region.

Ví dụ:

```axiom id="v3h7k1"
struct Image {
    pixels: Buffer<u8>,
    width: usize,
    height: usize,
}
```

```text id="t1y5z4"
view(image.pixels)
```

region không phải toàn `Image`.

Nó chỉ là:

```text id="2x8n0p"
Image.pixels
```

Do đó có thể:

```text id="q9f4w2"
read image.width
```

trong khi:

```text id="6m3z8x"
mutate pixels
```

nếu semantic rules cho phép.

---

# 49. Field-sensitive ownership

Axiom phải theo dõi field-level.

Ví dụ:

```axiom id="7g8x2s"
let name = user.name;
use(user.id);
```

Compiler không cần coi toàn bộ `user` là moved.

State:

```text id="r5m1q0"
user.id   = Owned
user.name = Moved
```

Đây là yêu cầu quan trọng để language không trở nên quá restrictive.

---

# 50. Array/slice regions

Compiler cần hỗ trợ region expressions:

```text id="f8k2m5"
array[0..4]
array[4..8]
```

Nếu compile-time prove:

```text id="x1y6q9"
[0..4] DISJOINT [4..8]
```

thì hai `mut_view` có thể cùng tồn tại.

Nếu:

```text id="e0r4s7"
array[i..j]
array[k..l]
```

không prove được:

```text id="z9n2c5"
UNKNOWN
```

→ safe overlap rejected.

---

# 51. Compiler có thể dùng runtime checks?

Đây là điểm đáng cân nhắc.

Axiom nên cho phép library/API explicit abstractions tạo dynamic disjointness proof.

Ví dụ:

```axiom id="4c8j1m"
let (left, right) = split_mut(buffer, index);
```

API contract đảm bảo:

```text id="3n7f5q"
left DISJOINT right
```

Compiler không cần tự chứng minh mọi index arithmetic.

Đây là cách tránh borrow-checker quá cứng.

---

# 52. Trusted safe abstractions

Không phải mọi proof đều phải compiler derive từ raw syntax.

Một abstraction library có thể expose semantic contract:

```text id="w6p3k9"
split_mut<T>(...)
    → (mut_view<T>, mut_view<T>)
```

với compiler-recognized capability rule hoặc intrinsic-safe primitive.

Nhưng contract phải được compiler hiểu ở semantic boundary, không phải comment tự nhận là safe.

---

# 53. Unsafe boundary

Ví dụ:

```axiom id="d1s7v4"
unsafe {
    let p: *mut i32 = ...;
}
```

Unsafe có thể tạo raw pointer.

Nhưng khi chuyển thành:

```text id="n5k8x2"
mut_view<i32>
```

compiler cần một explicit trusted operation:

```text id="u4c9j1"
unsafe view_from_raw(...)
```

Sau đó capability verifier tiếp tục hoạt động bình thường.

Unsafe không làm:

```text id="j6w2m0"
all checking disabled
```

---

# 54. Trusted semantic precondition

Unsafe operation có thể establish:

```text id="q8v5c3"
provenance valid
region valid
alignment valid
initialized
exclusive access
```

Compiler ghi nhận:

```text id="x3m7k2"
TrustedCapability
```

và từ đó safe code tiếp tục được kiểm tra.

Đúng với:

```text
AUNSAFE-56
AUNSAFE-57
```

---

# 55. No general contract language yet

Không biến:

```axiom id="a2f6k9"
unsafe fn foo(...)
```

thành full dependent contract system.

V1 chỉ cần compiler-known safety boundaries.

Documentation:

```text id="w7r4p1"
/// SAFETY:
/// caller guarantees ...
```

có thể được tooling sử dụng.

Nhưng comment không tự tạo semantic proof.

---

# 56. Alias facts cho optimizer

Sau verification:

```text id="e2k7m4"
mut_view(a)
mut_view(b)
```

nếu compiler chứng minh:

```text id="j5v9q0"
DISJOINT
```

có thể truyền xuống optimization:

```text id="c8w2n6"
NoAlias(a, b)
```

Đây là một trong những lợi ích lớn của ownership model Axiom.

Không cần programmer viết `restrict`.

---

# 57. Nhưng không overpromise `restrict`

Compiler chỉ được dùng:

```text id="x4m9q7"
NoAlias
```

khi proof thật sự tồn tại.

Không:

```text id="y2z5c1"
assume all parameters are independent
```

Nếu không chứng minh:

```text id="n7f3v8"
Alias = Unknown
```

---

# 58. Ownership checker không cần chạy ở runtime

Tất cả:

```text id="z5j2m8"
ownership state
capability graph
region graph
move analysis
```

là compile-time.

Executable không chứa:

```text id="c1x6v0"
borrow checker
GC metadata
ownership tables
```

trừ khi một abstraction runtime thực sự cần metadata của chính nó.

---

# 59. Drop elaboration

Sau verification:

```text id="u6h3p9"
Verified HIR
```

→ compiler tạo:

```text id="q2m7x5"
Drop-elaborated MIR
```

Ví dụ:

```axiom id="v3f9k1"
{
    let a = A();
    let b = B();
}
```

MIR:

```text id="g8r2w4"
a = CALL A
b = CALL B

DROP b
DROP a

RETURN
```

---

# 60. Move-aware Drop

```axiom id="n1c5x8"
let a = make();
let b = a;
```

MIR:

```text id="j7v3q2"
a = CALL make
MOVE a → b

DROP b
```

Không:

```text id="w5k8r0"
DROP a
DROP b
```

---

# 61. Partial move Drop

```text id="9q3m1v"
user.name moved
user.id remains
```

MIR cleanup phải biết:

```text id="b6x2k7"
DROP user.id
```

không drop `user.name`.

---

# 62. Explicit `drop(x)`

Nếu programmer viết:

```axiom id="e8w4n2"
drop(file);
```

semantic state:

```text id="h3j9p0"
file: Owned → Dropped
```

Sau đó:

```axiom id="d6v1c5"
use(file);
```

→ error.

`drop(x)` không có nghĩa compiler phải `free()` memory ngay.

---

# 63. `drop` không được fail

Đã frozen:

```text id="y8k4q3"
Drop = non-fallible
```

Không:

```axiom id="w2f7m9"
impl Drop for File {
    fn drop(self) -> Result<()> // invalid
}
```

Nếu cleanup có thể fail:

```axiom id="j1c6v8"
file.close()?;
```

trước khi ownership kết thúc.

---

# 64. Capability và Drop

Nếu:

```axiom id="p4s7z2"
let v = view(file);
drop(file);
```

reject.

Nếu:

```axiom id="g2m9x6"
{
    let v = view(file);
    read(v);
}

drop(file);
```

valid.

---

# 65. Control-flow analysis

Ownership checker phải chạy trên CFG.

HIR:

```text id="q5w8n3"
if
while
loop
match
return
break
continue
```

được lower tạm thành control-flow graph hoặc một abstract CFG.

Không cần chờ full MIR.

Tôi khuyến nghị:

```text id="f1k7v4"
HIR
 ↓
Ownership CFG
```

sau đó MIR lowering dùng lại CFG facts.

---

# 66. Match ownership

Ví dụ:

```axiom id="m4c8y1"
match result {
    Ok(value) => use(value),
    Err(error) => log(error),
}
```

mỗi arm có state riêng.

Sau match:

```text id="n7x2q5"
compiler merges ownership state
```

Nếu value chỉ tồn tại trong một arm, Drop/Move tương ứng được xử lý.

---

# 67. Pattern move

```axiom id="a6z3w8"
match user {
    User { name } => consume(name),
}
```

`name` được move khỏi user.

Ownership checker phải cập nhật field path:

```text id="j9p4r1"
user.name = Moved
```

Không chỉ:

```text id="v5c8k2"
user = Moved
```

nếu các field khác vẫn hợp lệ.

---

# 68. Pattern view

Nếu pattern chỉ đọc:

```text id="e7q2m5"
match view(data) {
    ...
}
```

capability là READ.

Không biến thành ownership move.

---

# 69. Ownership through function calls

Đây là nơi function signature trở thành semantic contract.

Ví dụ:

```axiom id="r8f3x6"
fn consume(x: String)
```

parameter `x` mặc định là owning parameter.

Call:

```axiom id="q1v7k4"
consume(s);
```

→ `s` moved nếu `String` !Copy.

---

# 70. View parameter

```axiom id="y3m6p8"
fn read(x: view<String>)
```

Call:

```axiom id="k5r2c9"
read(s);
```

→ ephemeral READ capability.

`s` vẫn Owned sau call.

---

# 71. Mut view parameter

```axiom id="t9x1v5"
fn edit(x: mut_view<String>)
```

Call:

```axiom id="c4m7q2"
edit(s);
```

→ ephemeral WRITE capability.

Sau call:

```text id="n8z3w6"
s vẫn Owned
```

nhưng compiler biết vùng đã bị mutable access.

---

# 72. Return ownership

```axiom id="k2r5v9"
fn make() -> String
```

return transfer:

```text id="x6m1p4"
callee ownership
        ↓
caller ownership
```

Không cần heap.

---

# 73. Return view

```axiom id="j8q3m5"
fn first(x: view<String>) -> view<u8>
```

return capability phải có provenance từ input.

Compiler không cho:

```text id="w4v7k2"
return view(local)
```

nếu local chết.

---

# 74. Ownership contract inference

Axiom có thể **infer ownership requirements của private functions**, nhưng public signatures vẫn explicit.

Ví dụ:

```axiom id="n9x2r5"
fn helper(x: T) {
    consume(x);
}
```

`x` đã là owning parameter do type signature.

Compiler không cần annotation:

```text id="q5m8v1"
@consumes
```

Không thêm effect syntax.

---

# 75. No explicit lifetime parameters

Tuyệt đối không có:

```text id="d7p2n6"
fn foo<'a>(...)
```

Region graph là compiler-internal.

Đây là một trong những core differentiators của Axiom.

---

# 76. Capability validity

Một capability hợp lệ khi:

```text id="u3k7m9"
owner/storage alive
provenance valid
region valid
access mode valid
execution domain valid
```

Nếu bất kỳ điều kiện nào false:

```text id="f6q1x4"
capability invalid
```

---

# 77. Capability invalidation events

Các operation có thể invalidate:

```text id="r8m2c5"
MOVE owner
DROP owner
REALLOC storage
TRANSFER ownership
END arena
END execution resource
```

Ví dụ `Vec.push()` có thể relocate storage.

Nếu đang có:

```axiom id="x7n4k1"
let v = view(vec);
vec.push(x);
```

compiler phải biết `push` **may relocate**.

→ conflict.

---

# 78. `reserve` không guarantee stable address

Đã frozen:

```text id="z5q8m2"
reserve(n)
```

không tạo permanent no-relocation guarantee.

Muốn stable address:

```text id="v2k6p9"
Box
Arena
Pool
stable storage abstraction
```

phải explicit.

---

# 79. Relocation effect là compiler fact

Collection API có internal semantic fact:

```text id="q4x1s7"
MAY_RELOCATE
```

Compiler dùng để invalidate/forbid dependent views.

Không cần user-facing effect system.

Điều này hoàn toàn phù hợp AEFFECT-20..36.

---

# 80. FFI

Ownership checker phải đặc biệt cẩn thận với:

```axiom id="j6p2x9"
extern "C" fn foo(p: *mut u8);
```

Raw pointer không tạo safe capability tự động.

Sau FFI:

```text id="n1v5r8"
compiler cannot infer foreign ownership semantics
```

API phải khai báo semantic wrapper rõ ràng.

---

# 81. Foreign ownership

Không cho compiler đoán:

```text id="e8c3m7"
foo(p) // foreign function frees p?
```

ABI chỉ nói calling convention/layout.

Ownership contract của FFI phải được biểu diễn bằng Axiom wrapper hoặc explicit unsafe boundary.

---

# 82. Send/Share checking

Ownership checker kết hợp trait facts:

```text id="g5r1x8"
spawn(closure)
```

closure captures:

```text id="v2m6q4"
a: T
b: U
```

checker yêu cầu:

```text id="z8k3n1"
Send(T)
Send(U)
```

Nếu closure shared:

```text id="f4p7c2"
Share(T)
Share(U)
```

---

# 83. Data race

Safe code không được có:

```text id="s3m9x6"
WRITE(shared region)
+
READ/WRITE(other concurrent execution)
```

trừ khi access đi qua:

```text id="w8q2k5"
Atomic
Mutex
RwLock
channel ownership transfer
specialized synchronization abstraction
```

Ownership checker + concurrency verifier phối hợp.

---

# 84. Lock guard

Ví dụ:

```axiom id="a7c2m9"
var guard = mutex.write();

guard.value = 10;
```

Guard sở hữu synchronization capability.

```text id="e3x8q1"
Drop(guard)
```

→ unlock.

Derived:

```text id="p5m7v2"
mut_view<T>
```

không được sống lâu hơn guard.

---

# 85. Capability chain

Ví dụ:

```text id="n6r2x4"
Mutex<T>
   ↓
MutexGuard
   ↓
mut_view<T>
   ↓
field view
```

Compiler cần biết:

```text id="j9k3m7"
field capability depends on guard
```

Guard Drop:

```text id="r4v8c1"
invalidates all dependent capabilities
```

---

# 86. Async lock

Synchronous guard:

```text id="w5m2q8"
MutexGuard
```

không được cross:

```text id="g8x1n6"
await
```

Async lock có abstraction khác:

```text id="c3v7k9"
AsyncMutexGuard
```

với semantics riêng.

Ownership checker không cần biết implementation scheduler.

---

# 87. Arena

Ví dụ:

```axiom id="r2q6m8"
let arena = Arena.new();

let x = arena.alloc(value);
```

`x` capability/storage dependency:

```text id="y4k9c2"
x → arena
```

Không được:

```axiom id="n1v7p5"
return x;
```

nếu arena local.

Arena Drop invalidates all allocations.

---

# 88. Pool

Pool có stable slot semantics.

```text id="j6c2x8"
pool.alloc()
```

có thể return handle/storage identity.

Compiler không được assume:

```text id="p4m9q1"
handle == raw pointer
```

Logical identity và storage identity vẫn tách biệt.

---

# 89. Logical Handle

```axiom id="s7x3k5"
EntityId
```

không phải capability.

Nó có thể survive:

```text id="z2m8v4"
storage relocation
```

nếu generation handle abstraction đảm bảo.

Đây là lý do Axiom không nên dùng pointer làm object identity mặc định.

---

# 90. Ownership checker output

Sau verification, mỗi HIR function có:

```text id="q5r8x2"
OwnershipFacts {
    local_states
    move_paths
    drop_paths
    capabilities
    regions
    escapes
    captures
    send_share
}
```

Những facts này được MIR lowering sử dụng.

---

# 91. Không giữ toàn bộ graph trong executable

Các graph:

```text id="v1k4m8"
OwnershipGraph
CapabilityGraph
RegionGraph
```

chỉ compiler internal.

Sau verification:

```text id="b8q2z6"
erase proof machinery
```

chỉ giữ những semantic consequences cần cho MIR:

```text id="m5x9r1"
MOVE
COPY
DROP
CALL
LOAD
STORE
ALLOC
DEALLOC
```

---

# 92. Ownership checker pipeline

```text id="f2c7n9"
Typed HIR
    │
    ├── Build CFG
    │
    ├── Infer ownership state
    │
    ├── Analyze moves
    │
    ├── Analyze drops
    │
    ├── Build capabilities
    │
    ├── Region analysis
    │
    ├── Alias conflict analysis
    │
    ├── Escape analysis
    │
    ├── Closure capture analysis
    │
    ├── Send/Share verification
    │
    └── Async suspension checks
              │
              ▼
       Verified HIR
```

---

# 93. Diagnostics

Namespace:

```text id="h3w7q1"
AX14xx
```

Ví dụ:

```text id="m2c8x5"
AX1401 use of moved value
AX1402 value may have been moved
AX1403 value already dropped
AX1404 partial move conflict
AX1405 value requires Drop
AX1406 dangling view
AX1407 capability conflict
AX1408 overlapping mutable access
AX1409 mutable access while read capability exists
AX1410 owner destroyed while capability is live
AX1411 capability cannot escape scope
AX1412 capability cannot cross await
AX1413 invalid closure capture
AX1414 value is not Send
AX1415 value is not Share
AX1416 storage may relocate while capability is live
AX1417 invalid ownership transfer
AX1418 unsafe capability precondition not established
AX1419 invalid partial move of custom-Drop type
AX1420 resource cleanup state inconsistent
```

---

# 94. Diagnostic phải chỉ ra “why”

Ví dụ:

```axiom id="1n7k4c"
let view = view(buffer);

buffer.push(x);

use(view);
```

Không chỉ:

```text
error AX1416
```

mà:

```text
error AX1416:
storage may relocate while capability is live

`view` depends on `buffer` storage.

`buffer.push(...)` may relocate its storage.

capability created here:
    let view = view(buffer);

relocation occurs here:
    buffer.push(x);

help:
    finish using the view before the operation,
    or use a storage abstraction with stable-address semantics.
```

Đây là loại diagnostic AI rất dễ xử lý.

---

# 95. Ownership checker không được “đoán để compile”

Một nguyên tắc rất quan trọng:

Nếu compiler không chứng minh được:

```text id="e7r2k9"
DISJOINT
```

thì không được tự giả định.

Nếu không biết:

```text id="m3v8c5"
owner alive
```

thì không được tự giả định.

Nếu không biết:

```text id="q6n1x4"
Send(T)
```

thì không được tự giả định.

> **Unknown → conservative rejection trong safe code.**

Unsafe/API abstraction là cách programmer cung cấp trusted semantic boundary.

---

# 96. Nhưng không được conservative quá mức

Đây là mặt còn lại.

Compiler phải có:

```text id="g8c2v7"
field sensitivity
path sensitivity
last-use analysis
disjointness analysis
escape analysis
known library contracts
```

Nếu không Axiom sẽ trở thành:

> Rust borrow checker nhưng không có syntax lifetime.

Đó **không phải mục tiêu**.

Mục tiêu là:

> Programmer không phải viết proof; compiler phải đầu tư đủ intelligence để tự tìm proof.

---

# 97. Ví dụ tổng hợp

```axiom id="m1q8c4"
struct Image {
    pixels: Buffer<u8>,
    width: usize,
    height: usize,
}

fn process(image: mut_view<Image>) {
    let pixels = mut_view(image.pixels);

    normalize(pixels);

    resize_metadata(image);
}
```

Compiler phải nhận ra:

```text id="r4v9x2"
pixels → WRITE(Image.pixels)
image metadata → WRITE(Image.width/height)
```

hai region disjoint.

Do đó hợp lệ.

Không cần programmer split object thành nhiều reference.

---

# 98. Ví dụ phải reject

```axiom id="h7c3m9"
fn bad(image: mut_view<Image>) {
    let pixels = mut_view(image.pixels);

    modify_entire_image(image);
}
```

Nếu `modify_entire_image` có:

```text id="q2v8k4"
WRITE(Image)
```

thì overlap với:

```text id="x5m1r7"
WRITE(Image.pixels)
```

→ reject.

---

# 99. Đây chính là lợi thế của Axiom

Rust programmer thường phải diễn đạt borrow structure.

Axiom programmer chỉ viết:

```axiom id="z8f2c6"
let pixels = mut_view(image.pixels);
```

Compiler tự xây:

```text id="j4r7n1"
provenance
region
access mode
lifetime
alias proof
```

Nếu proof tồn tại → compile.

Nếu không → diagnostic.

---

# 100. COMPILER-004 invariants

```text id="4m7n2q"
AOWN-80   Ownership Is A Compile-Time Semantic Property
AOWN-81   Ownership State Is Explicit In Compiler Facts
AOWN-82   Move Is An Ownership State Transition
AOWN-83   Move Does Not Imply Physical Copy
AOWN-84   Copy Is Semantic Value Duplication
AOWN-85   Copy Requires Copy Semantics
AOWN-86   Drop-Bearing Types Are Not Copy
AOWN-87   Ownership Is Path Sensitive
AOWN-88   Ownership Merge Is Conservative
AOWN-89   Moved Values Cannot Be Used
AOWN-90   Dropped Values Cannot Be Used
AOWN-91   Partial Move Is Field Sensitive
AOWN-92   Custom Drop Forbids Partial Move
AOWN-93   Drop Order Is Deterministic
AOWN-94   Drop Is Non-Fallible
AOWN-95   Cleanup Is Represented Before MIR Drop Elaboration

ACAP-40   View Is A Read Capability
ACAP-41   MutView Is An Exclusive Write Capability
ACAP-42   Read Capabilities May Coexist
ACAP-43   Conflicting Write Capabilities Are Rejected
ACAP-44   Read And Write Conflicts Are Rejected
ACAP-45   Capability Does Not Transfer Ownership
ACAP-46   Capability Requires Valid Provenance
ACAP-47   Owner Cannot Be Destroyed While Capability Is Live
ACAP-48   Capability Cannot Outlive Its Provenance
ACAP-49   Capability Lifetime Is Compiler Inferred
ACAP-50   Programmer Does Not Write Capability Lifetimes
ACAP-51   Ephemeral Owner-To-View Conversion Cannot Escape
ACAP-52   Persistent Views Require Explicit Binding
ACAP-53   MutView Is Not Duplicable
ACAP-54   View Duplication Is Capability Semantics
ACAP-55   Unknown Overlap Is Not Assumed Disjoint
ACAP-56   Disjoint Regions May Be Mutably Accessed Independently
ACAP-57   Field Regions Are Tracked Independently
ACAP-58   Collection Relocation Invalidates Dependent Address Capabilities
ACAP-59   Stable Address Requires Explicit Storage Contract
ACAP-60   Unsafe Does Not Disable Capability Verification
ACAP-61   Unsafe May Establish Trusted Semantic Preconditions
ACAP-62   Safe Verification Resumes After Trusted Unsafe Boundary

AESCAPE-20  Escape Analysis Is Compiler Internal
AESCAPE-21  Escaping Values Require Valid Storage Lifetime
AESCAPE-22  Returning A Local Capability Is Rejected
AESCAPE-23  Closure Capture Is Ownership Checked
AESCAPE-24  Non-Escaping Values May Be Stack Or Register Allocated
AESCAPE-25  Closure Allocation Is Not Mandatory
AESCAPE-26  Observable Address Identity Constrains Optimization

ACONC-60   Send Is Distinct From Share
ACONC-61   Execution-Domain Transfer Requires Send
ACONC-62   Concurrent Sharing Requires Share
ACONC-63   Closure Captures Participate In Send/Share Checking
ACONC-64   Safe Data Races Are Rejected
ACONC-65   Synchronization Abstractions Establish Controlled Access

AASYNC-71  Ordinary Borrowed Capabilities Cannot Cross Await
AASYNC-72  Owned Values May Cross Await
AASYNC-73  Future State Owns Values That Must Survive Suspension
AASYNC-74  Suspension Does Not Extend Invalid Capability Lifetime
```

---

# 101. Compiler architecture sau COMPILER-004

Bây giờ pipeline semantic core đã hoàn chỉnh hơn rất nhiều:

```text
                 SOURCE
                    │
                    ▼
                 Lexer
                    │
                    ▼
                 Parser
                    │
                   AST
                    │
                    ▼
             Name Resolution
                    │
                    ▼
                   HIR
                    │
                    ▼
              Type System
                    │
              Trait Solver
                    │
              Typed HIR
                    │
                    ▼
       ┌─────────────────────────┐
       │ Ownership Analysis      │
       │ Capability Analysis     │
       │ Region Analysis         │
       │ Move Analysis           │
       │ Drop Analysis           │
       │ Escape Analysis         │
       │ Send/Share Analysis     │
       │ Async Capture Analysis  │
       └────────────┬────────────┘
                    │
                    ▼
              Verified HIR
                    │
                    ▼
              Drop Elaboration
                    │
                    ▼
                   MIR
```

Đây chính là semantic heart của Axiom.

---

# 102. Một điều cần chốt ngay

Tôi **không khuyến nghị** xây Ownership Checker như một pass đơn độc kiểu:

```text
check_ownership()
```

Nó nên là một hệ thống facts dùng chung:

```text
SemanticFacts
├── TypeFact
├── OwnershipFact
├── CapabilityFact
├── RegionFact
├── EscapeFact
├── DropFact
├── SendFact
├── ShareFact
├── AsyncFact
├── UnsafeFact
└── ExecutionDomainFact
```

Sau này:

```text
MIR
Optimizer
Async lowering
GPU verifier
FFI
ABI
```

đều đọc các facts này thay vì tự xây logic riêng.

Đây là cách tránh việc compiler Axiom về sau biến thành **10 borrow checkers khác nhau**.

---

# 103. Bước tiếp theo: COMPILER-005

Semantic frontend đến đây đã có nền móng:

```text
COMPILER-001 Lexer/Parser
COMPILER-002 Resolver/HIR
COMPILER-003 Type/Trait
COMPILER-004 Ownership/Capability
```

Bước tiếp theo hợp lý nhất là:

## **COMPILER-005 — MIR Design + Lowering + Semantic Verification**

Đây là nơi ta phải đóng **IR quan trọng nhất của toàn bộ Axiom**:

```text
Typed HIR
    ↓
Verified HIR
    ↓
MIR
```

và định nghĩa chính xác các instruction:

```text
PARAM
CONST
COPY
MOVE
BORROW_READ
BORROW_WRITE
FIELD
INDEX
LOAD
STORE
ALLOC
DEALLOC
CALL
RETURN
BRANCH
SWITCH
PHI
DROP
PANIC
TRAP
AWAIT
SPAWN
ATOMIC
LOCK
UNLOCK
```

Đặc biệt phải quyết định **SSA của Axiom MIR có phải SSA thuần hay hybrid SSA + memory places**, cách biểu diễn partial move, capability, async state machine và cleanup CFG.

Đây sẽ là bước quyết định trực tiếp xem compiler Axiom sau này có thể đạt được mục tiêu **C/C++-class performance mà vẫn giữ frontend đơn giản** hay không.