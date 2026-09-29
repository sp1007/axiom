# XL — CAP-001: Capability, Region & Liveness

Sau `OWN-001`, ta xây lớp thứ hai: **capability analysis**. Đây là phần giúp Axiom có `view<T>` / `mut_view<T>` mà không bắt programmer viết lifetime.

Mục tiêu:

```text
Typed HIR
   ↓
Ownership Facts
   ↓
Capability Analysis
   ├── Capability creation
   ├── Provenance
   ├── Region
   ├── Liveness
   ├── Conflict
   └── Escape
   ↓
Capability Facts
```

---

## 1. Capability không phải reference syntax

`view<T>` không nên được hiểu đơn giản là:

```text
"một con trỏ + lifetime"
```

Semantic definition:

> `view<T>` là một **READ capability** đối với một vùng dữ liệu có provenance xác định.

`mut_view<T>`:

> `mut_view<T>` là một **exclusive WRITE capability**.

Do đó compiler theo dõi:

```text
Capability {
    id
    owner
    region
    access
    lifetime
    provenance
}
```

---

# 2. Capability ID

Thêm typed ID:

```text
CapabilityId
RegionId
```

Không dùng `LocalId` cho capability.

Ví dụ:

```text
s: Text
v: view<Text>
```

có thể có:

```text
Owner:
    LocalId(12)

Capability:
    CapabilityId(7)
```

---

# 3. Access mode

Chốt:

```text
CapabilityAccess
├── Read
└── Write
```

Không có:

```text
ReadWrite
```

ở semantic layer.

`mut_view<T>` là exclusive WRITE capability; nó có thể đọc dữ liệu thông qua API phù hợp, nhưng capability conflict model vẫn coi nó là WRITE.

Điều này làm rule đơn giản:

```text
READ  + READ   = OK
READ  + WRITE  = CONFLICT
WRITE + WRITE  = CONFLICT
```

---

# 4. Capability provenance

Capability phải biết nó đến từ đâu.

Ví dụ:

```axiom
let s = make_text()
let v = view(s)
```

ta có:

```text
Capability:
    owner = s
    region = Whole(s)
    access = Read
```

Không được tạo capability “mồ côi”.

Invariant:

```text
ACAP-32
Every safe capability has valid provenance.
```

---

# 5. Region model

Chốt region relation:

```text
SAME
DISJOINT
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Ví dụ:

```text
s.a
s.b
```

nếu `a`, `b` là hai field:

```text
s.a ↔ s.b = DISJOINT
```

Trong khi:

```text
s
s.a
```

là:

```text
s CONTAINS s.a
```

---

# 6. Region representation

Không nên lưu region bằng raw address.

```text
Region {
    root: Place
    projections: [...]
}
```

Ví dụ:

```text
view(s.name)
```

→

```text
Region {
    root = s
    projection = [Field(name)]
}
```

Đây là semantic region.

Machine address chỉ xuất hiện rất muộn.

---

# 7. Vì sao không dùng address

Nếu:

```text
Vec<T>
```

thay đổi storage:

```text
old address → new address
```

thì capability semantic vẫn phải biết:

```text
"đây là region của Vec element hiện tại"
```

chứ không phải:

```text
"địa chỉ 0x123456"
```

Điều này cho phép compiler kiểm soát relocation.

---

# 8. Ephemeral view

Ví dụ:

```axiom
fn print(x: view<Text>) {}

fn main() {
    let s = make_text()
    print(s)
}
```

Không cần:

```axiom
let v = view(s)
print(v)
```

Compiler tạo temporary capability:

```text
Capability C1:
    owner = s
    access = Read
    region = Whole(s)
    lifetime = call(print)
```

Sau call:

```text
C1 = DEAD
```

Không tồn tại persistent variable.

---

# 9. Đây là implicit conversion duy nhất

Axiom cho phép:

```text
Owner → ephemeral view
```

khi parameter yêu cầu:

```text
view<T>
mut_view<T>
```

Nhưng không cho:

```text
Owner → persistent view
```

một cách ngầm định.

Điều này giữ language đơn giản nhưng tránh alias ẩn.

---

# 10. Persistent view

Muốn giữ capability:

```axiom
let v = view(s)
```

Compiler tạo:

```text
C1:
    owner = s
    access = Read
    region = Whole(s)
```

và:

```text
v → C1
```

---

# 11. Mutable view

```axiom
let v = mut_view(s)
```

→:

```text
C1:
    owner = s
    access = Write
```

Từ thời điểm đó:

```text
s
```

không thể bị truy cập READ/WRITE xung đột nếu `v` còn live.

---

# 12. Capability lifetime

Không cần lifetime annotation.

Compiler tính:

```text
create
   ↓
uses
   ↓
last use
   ↓
dead
```

Ví dụ:

```axiom
let v = view(s)
print(v)
foo()
```

Capability `v` chết sau:

```text
print(v)
```

nếu không còn use.

Do đó:

```axiom
let v = view(s)
print(v)
modify(s)
```

có thể hợp lệ.

Không cần:

```text
drop(v)
```

trừ khi programmer muốn ép kết thúc lifetime.

---

# 13. Liveness không giống lexical scope

Đây là một optimization rất quan trọng.

Ví dụ:

```axiom
{
    let v = view(s)
    print(v)
}

modify(s)
```

lexical scope kết thúc sau `print`.

Nhưng:

```axiom
let v = view(s)
print(v)
modify(s)
```

compiler vẫn có thể nhận ra `v` dead sau `print`.

Do đó capability lifetime là:

> semantic liveness, không phải đơn thuần source scope.

---

# 14. Nhưng compiler không được làm thay đổi semantics

Nếu programmer làm:

```axiom
let v = view(s)
some_call()
modify(s)
use(v)
```

thì `v` vẫn live.

Compiler không được giả định nó chết chỉ vì không thấy use trực tiếp nếu `some_call()` có thể giữ capability qua closure/side effect được phép.

Do đó escape analysis phải tham gia.

---

# 15. Capability escape

Ví dụ:

```axiom
fn save(v: view<Text>) {
    global = v
}
```

Nếu `global` sống lâu hơn owner:

```text
owner s
    ↓
v
    ↓
global
```

→ reject.

Diagnostic:

```text
AX_VIEW_0002
view escapes owner
```

---

# 16. Return view

Ví dụ:

```axiom
fn bad() -> view<Text> {
    let s = make_text()
    view(s)
}
```

Không hợp lệ.

Vì:

```text
s lifetime < returned view lifetime
```

Compiler không cần lifetime syntax để biết điều này.

---

# 17. Return view từ caller-owned object

Nhưng:

```axiom
fn name(s: view<User>) -> view<Text> {
    view(s.name)
}
```

có thể hợp lệ **nếu compiler chứng minh returned capability không vượt provenance của input capability**.

Semantic relationship:

```text
input capability
      │
      └── region User
             │
             └── region User.name
```

Return capability:

```text
User.name
```

vẫn phụ thuộc input.

---

# 18. Capability dependency graph

Đây là cấu trúc rất hữu ích:

```text
CapabilityGraph

C1
 └── owner/provenance S

C2
 └── derived from C1
```

Ví dụ:

```axiom
let u = ...
let v = view(u)
let name = view(v.name)
```

graph:

```text
u
│
└── C1: view(u)
      │
      └── C2: view(u.name)
```

Nếu `C1` invalid → `C2` cũng invalid.

---

# 19. Derived capability

Các phép:

```text
view(field)
view(slice)
view(indexed region)
```

không tạo ownership.

Chỉ tạo capability phụ thuộc.

---

# 20. Mutable conflict

```axiom
let a = mut_view(x)
let b = mut_view(x)
```

→ conflict.

```text
C1:
    WRITE x

C2:
    WRITE x
```

Region:

```text
SAME
```

→ reject.

---

# 21. Read + write

```axiom
let a = view(x)
let b = mut_view(x)
```

→ conflict.

```text
READ x
WRITE x
```

---

# 22. Read + read

```axiom
let a = view(x)
let b = view(x)
```

→ valid.

Hai READ capabilities có thể tồn tại đồng thời.

Đây là lý do `view<T>` duplicable.

---

# 23. `view<T>` không phải Copy trait

Điểm này vẫn phải giữ.

Không nói:

```text
view<T>: Copy
```

mà semantic:

```text
view<T> has intrinsic capability duplication semantics
```

Ví dụ:

```axiom
let a = view(x)
let b = a
```

compiler có thể tạo thêm READ capability.

Nhưng đây không phải semantic `Copy` của ownership.

---

# 24. `mut_view<T>` không duplicable

```axiom
let a = mut_view(x)
let b = a
```

→ capability ownership transfer:

```text
a → MOVED
b → WRITE
```

Không được có hai WRITE capability.

---

# 25. Field splitting

Ví dụ:

```axiom
struct Pair {
    left: i32
    right: i32
}
```

```axiom
let a = mut_view(p.left)
let b = mut_view(p.right)
```

→ valid.

Region:

```text
p.left  DISJOINT p.right
```

Đây là một trong những lợi ích lớn nhất của region-aware capability.

---

# 26. Whole + field conflict

```axiom
let a = mut_view(p)
let b = mut_view(p.left)
```

→ conflict.

Vì:

```text
p CONTAINS p.left
```

WRITE + WRITE.

---

# 27. Whole read + field write

```axiom
let a = view(p)
let b = mut_view(p.left)
```

→ conflict.

Vì READ whole object bao phủ field đang WRITE.

---

# 28. Independent fields

```axiom
let a = view(p.left)
let b = mut_view(p.right)
```

→ valid.

Đây là invariant:

```text
ACAP-34
Disjoint proven regions may hold compatible capabilities concurrently.
```

---

# 29. Unknown overlap

Với:

```axiom
let a = mut_view(array[i])
let b = mut_view(array[j])
```

nếu compiler không biết `i != j`:

```text
region(a) = UNKNOWN
region(b) = UNKNOWN
```

Không được tự giả định DISJOINT.

→ reject nếu cần đồng thời tồn tại.

Đây là nguyên tắc:

> **Unknown is not disjoint.**

---

# 30. Range views

```axiom
let a = view(array[0..10])
let b = view(array[10..20])
```

compiler có thể chứng minh:

```text
DISJOINT
```

Nếu:

```text
array[0..10]
array[5..20]
```

→ `OVERLAPS`.

Nếu bounds runtime nhưng có constraint đủ mạnh:

```text
0 <= a.end <= b.start
```

thì optimizer/capability analysis có thể dùng proof.

---

# 31. Vec relocation

Đây là nơi capability kết nối memory model.

```axiom
let v = ...
let x = view(v)
v.push(...)
```

`push` có thể relocate storage.

Capability analyzer phải thấy:

```text
x → dependent on v storage
push(v) → MAY_RELOCATE
```

→ reject nếu relocation có thể xảy ra.

Diagnostic:

```text
AX_VIEW_0004
possible storage relocation while a dependent view is live
```

---

# 32. `reserve` không giải quyết triệt để

Không cho phép:

```axiom
v.reserve(100)
let x = view(v)
v.push(...)
```

và kết luận:

> chắc chắn không relocate.

Semantic contract của `reserve` không mặc định là stable address.

Nếu muốn stable address:

```text
Box
Arena
Pool
StableBuffer
```

hoặc abstraction tương ứng phải cung cấp storage contract.

---

# 33. Capability và `await`

Ví dụ:

```axiom
async fn foo() {
    let v = view(x)
    await something()
    use(v)
}
```

→ reject.

Lý do:

future state machine có thể suspend trong khi capability vẫn sống.

Rule:

```text
ACAP-35
view/mut_view cannot cross await.
```

Owned values thì được phép nếu Send/representation phù hợp.

---

# 34. Capability và closure

```axiom
let v = view(x)

let f = || use(v)
```

Compiler phải xác định closure capture.

Nếu closure không escape:

```text
C1
 ↓
closure
 ↓
call
 ↓
dead
```

có thể hợp lệ.

Nếu closure được return:

```axiom
fn make() -> Closure {
    ...
}
```

thì capability có thể escape.

Nếu owner không sống đủ lâu:

→ reject.

---

# 35. Capability và spawn

```axiom
spawn(|| use(view(x)))
```

không thể đơn giản cho phép.

Vì spawned task có lifetime khác.

Compiler cần:

```text
capture
→ escape
→ Send
→ owner lifetime
```

Trong CAP-001 chỉ ghi nhận:

```text
CapabilityEscape = Spawn
```

CONC-001 sẽ kiểm tiếp.

---

# 36. Unsafe boundary

Ví dụ:

```axiom
unsafe {
    let p: *mut T = ...
    ...
}
```

Unsafe có thể establish:

```text
TrustedCapability {
    provenance
    region
    access
    validity_contract
}
```

Sau đó safe analyzer tiếp tục.

Không phải:

```text
unsafe = disable verifier
```

mà:

```text
unsafe
 ↓
trusted semantic fact
 ↓
safe verification resumes
```

---

# 37. Capability Facts

Output:

```text
CapabilityFacts {
    capabilities
    provenance
    regions
    liveness
    conflicts
    escapes
    relocations
}
```

Ví dụ:

```text
C1:
    source = view(s)
    owner = Local(5)
    region = Whole(Local(5))
    access = Read
    live = [Block2:Instr3 .. Block2:Instr8]
    escape = None
```

---

# 38. Implementation layout

```text
compiler/capability/
├── capability.ax
├── provenance.ax
├── region.ax
├── relation.ax
├── liveness.ax
├── conflict.ax
├── escape.ax
├── relocation.ax
├── facts.ax
├── diagnostics.ax
└── tests/
    ├── read_read.ax
    ├── read_write.ax
    ├── write_write.ax
    ├── field_split.ax
    ├── unknown_overlap.ax
    ├── return_escape.ax
    ├── closure_escape.ax
    ├── await_escape.ax
    └── relocation.ax
```

---

# 39. Capability invariants

Chốt nhóm:

```text
ACAP-32
Every safe capability has valid provenance.

ACAP-33
Capability access mode is explicit.

ACAP-34
Proven disjoint regions may hold compatible capabilities concurrently.

ACAP-35
Capabilities cannot cross await.

ACAP-36
Capability lifetime is compiler-derived.

ACAP-37
Capability validity does not depend on lexical scope alone.

ACAP-38
Owner destruction cannot invalidate a live dependent capability.

ACAP-39
Owner relocation cannot invalidate a live dependent capability.

ACAP-40
Unknown overlap cannot be assumed disjoint.

ACAP-41
Read + Read is permitted for compatible regions.

ACAP-42
Read + Write conflicts when regions may overlap.

ACAP-43
Write + Write conflicts when regions may overlap.

ACAP-44
mut_view is exclusive and non-duplicable.

ACAP-45
view may be duplicated as a read capability.

ACAP-46
Capability duplication does not create ownership.

ACAP-47
Ephemeral owner-to-view conversion cannot create an escaping capability.

ACAP-48
Persistent capabilities require explicit creation.

ACAP-49
Returned capabilities must preserve valid provenance.

ACAP-50
Closure captures participate in capability escape analysis.

ACAP-51
Spawn boundaries participate in capability escape analysis.

ACAP-52
Capability analysis is independent of physical address representation.

ACAP-53
Capability analysis is independent of optimization level.

ACAP-54
Capability facts preserve source provenance.

ACAP-55
Unsafe may establish trusted capability preconditions.

ACAP-56
Safe verification resumes after an unsafe boundary only for the established contract.

ACAP-57
A live dependent capability blocks storage relocation that could invalidate it.
```

---

# 40. Bây giờ ghép Ownership + Capability

Ta có pipeline semantic thật:

```text
                 Typed HIR
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
     CFG Builder           Place Graph
          │                     │
          └──────────┬──────────┘
                     ↓
             Ownership Analysis
                     │
              Ownership Facts
                     │
                     ↓
             Capability Analysis
                     │
              Capability Facts
                     │
                     ↓
               Drop Analysis
                     │
                     ↓
                    MIR
```

Đây là kiến trúc nên giữ lâu dài.

**Không** gộp thành một analyzer khổng lồ.

---

# XLI — DROP-001: Drop Elaboration

Bước kế tiếp là `DROP-001`.

Đây là nơi ownership/capability facts bắt đầu biến thành **semantic cleanup operations**.

Ví dụ:

```axiom
fn foo() {
    let a = make_a()
    let b = make_b()
}
```

không được chỉ hiểu là:

```text
scope ends
```

Mà phải hạ thành semantic:

```text
DROP(b)
DROP(a)
RETURN
```

Nếu:

```axiom
let a = make_a()
consume(a)
```

thì:

```text
MOVE(a)
```

→ không được drop `a` lần nữa.

Nếu partial move:

```text
s.a → MOVED
s.b → OWNED
```

thì destructor phải chỉ cleanup phần còn owned.

Nếu custom Drop:

```text
partial move → compile error
```

Nếu early return:

```axiom
let a = ...
let b = ...

if cond {
    return
}
```

return path phải:

```text
DROP(b)
DROP(a)
RETURN
```

Nếu capability còn live:

```text
view(a)
return
```

thì return bị reject **trước** Drop elaboration vì owner không thể bị hủy khi capability còn tồn tại.

Sau `DROP-001`, ta sẽ có:

```text
Typed HIR
 → Ownership Facts
 → Capability Facts
 → Drop Facts
 → MIR
```

và lúc đó **MIR-001** có thể được đóng để vertical slice đầu tiên thực sự chạy được:

```text
fn main() -> i32 {
    42
}
```

→

```text
MIR
→ Verified MIR
→ LIR
→ x86-64 Machine IR
→ ELF object
→ axiom-link
→ executable
```

Đó mới là mốc **Axiom compiler thực sự bắt đầu tạo native binary**, thay vì chỉ là frontend.