Được. Ta chuyển hẳn sang **AXIOM-VERIFIER-SPEC v0.1** ở mức thuật toán. Đây là phần AI agent có thể lấy làm cơ sở để code verifier, thay vì diễn giải bằng văn xuôi.

# AXIOM VERIFIER SPEC v0.1

## 1. Mục tiêu

Verifier nhận:

```text
Typed MIR
```

và chỉ tạo:

```text
Verified MIR
```

nếu chứng minh được:

```text
- definite initialization
- ownership
- valid moves
- valid drops
- valid views
- valid region access
- no conflicting safe capabilities
- no invalid relocation
- valid Send/Share
- valid async suspension state
```

Verifier **không tối ưu**.

Verifier cũng **không quyết định ABI**.

Pipeline:

```text
MIR
 │
 ├── type validity
 ├── initialization
 ├── ownership
 ├── region
 ├── capability
 ├── effects
 ├── escape
 ├── drop
 ├── concurrency
 └── async
 │
 ▼
Verified MIR
```

---

# 2. Các kiểu dữ liệu nội bộ

## 2.1 Place

```text
Place =
    Local(LocalId)
  | Field(Place, FieldId)
  | Index(Place, ValueId)
  | Deref(Place)
```

Ví dụ:

```text
p.name
```

là:

```text
Field(
    Local(p),
    name
)
```

---

# 3. Region

```text
Region {
    root: PlaceRoot
    projection: ProjectionPath
}
```

Ví dụ:

```text
p
p.name
p.address.city
```

thành:

```text
R0 = (p, [])
R1 = (p, [name])
R2 = (p, [address, city])
```

---

# 4. Region relation

Hàm:

```text
relation(R1, R2)
```

trả:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Quy tắc cơ bản:

```text
p.name vs p.age
    → DISJOINT

p vs p.name
    → CONTAINS

p.name vs p.name
    → SAME

unknown dynamic index
    → UNKNOWN
```

`UNKNOWN` được xử lý conservative như có khả năng overlap.

---

# 5. Capability

```text
Capability {
    id
    provenance
    region
    mode
    origin
    state
}
```

Mode:

```text
READ
WRITE
```

Ở mức operation, verifier vẫn có:

```text
MOVE
DROP
```

nhưng chúng không phải long-lived capability như view.

---

# 6. Ownership

```text
OwnershipState =
    UNOWNED
    OWNED
    PARTIAL
    MOVED
    DROPPED
    MAYBE
```

Partial:

```text
PartialOwnership {
    whole: PARTIAL
    fields: Map<FieldId, OwnershipState>
}
```

Ví dụ:

```text
p:
    PARTIAL

p.name:
    MOVED

p.age:
    OWNED
```

---

# 7. Initialization

```text
InitState =
    UNINIT
    INIT
    MAYBE_INIT
```

Ownership và initialization độc lập.

Ví dụ:

```text
UNINIT + no ownership
```

khác:

```text
MAYBE_INIT + MAYBE ownership
```

---

# 8. VerifierState

Đặc tả:

```text
VerifierState {
    locals: Map<LocalId, LocalState>
    places: Map<Place, PlaceState>
    capabilities: Set<Capability>
    effects: EffectSet
    cleanup: CleanupState
    async: AsyncState
}
```

`LocalState`:

```text
LocalState {
    type
    init
    ownership
}
```

---

# 9. State merge

Đây là một trong những phần quan trọng nhất.

## Initialization

```text
INIT + INIT       = INIT
UNINIT + UNINIT   = UNINIT
INIT + UNINIT     = MAYBE_INIT
```

## Ownership

```text
OWNED + OWNED     = OWNED
MOVED + MOVED     = MOVED
DROPPED + DROPPED = DROPPED
OWNED + MOVED     = MAYBE
```

Partial state được merge theo từng child.

Ví dụ:

```text
Path A:
p.name = MOVED
p.age  = OWNED

Path B:
p.name = OWNED
p.age  = OWNED
```

kết quả:

```text
p.name = MAYBE
p.age  = OWNED
p      = PARTIAL
```

---

# 10. Dataflow algorithm

Mỗi BasicBlock:

```text
IN[block]
OUT[block]
```

Khởi tạo:

```text
IN[entry] = initial_state
IN[other] = UNKNOWN_STATE
```

Sau đó:

```text
repeat
    changed = false

    for block in CFG:
        new_in = merge(OUT[pred]...)
        new_out = transfer(block, new_in)

        if new_in != IN[block]:
            IN[block] = new_in
            changed = true

        if new_out != OUT[block]:
            OUT[block] = new_out
            changed = true

until !changed
```

Đây là fixed-point iteration.

---

# 11. Vì sao fixed point cần thiết?

Loop:

```text
while cond {
    ...
}
```

có cạnh:

```text
body → header
```

nên không thể xử lý CFG chỉ một lần.

Verifier phải lặp cho tới khi trạng thái ổn định.

---

# 12. Transfer function

Mỗi MIR instruction:

```text
new_state = transfer(instruction, state)
```

Ví dụ:

```text
MOVE p → x
```

thực hiện:

```text
check_readable_or_owned(p)
set_ownership(p, MOVED)
set_ownership(x, OWNED)
```

---

# 13. READ

MIR:

```text
LOAD place
```

Verifier:

```text
verify_initialized(place)
verify_read_capability(place)
```

Sau đó:

```text
effect += READ(region(place))
```

READ không làm mất ownership.

---

# 14. WRITE

MIR:

```text
STORE place, value
```

Verifier:

```text
verify_initialized_or_assignable(place)
verify_write_capability(place)
```

effect:

```text
WRITE(region(place))
```

Nếu place chứa Drop value đang sống, assignment phải xử lý replacement semantics đúng cách.

Đây là một điểm sau này cần test riêng.

---

# 15. MOVE

```text
MOVE place
```

Algorithm:

```text
verify_initialized(place)
verify_owned(place)
verify_no_active_conflicting_capability(place)

set ownership(place, MOVED)
```

Nếu `place` là field:

```text
p.name
```

chỉ field đó chuyển sang MOVED.

---

# 16. COPY

```text
COPY place
```

Yêu cầu:

```text
Copy(type(place)) == true
```

Sau đó:

```text
verify_initialized(place)
```

Không thay đổi ownership của source.

---

# 17. DROP

```text
DROP place
```

Yêu cầu:

```text
ownership(place) == OWNED
```

hoặc:

```text
PARTIAL
```

Sau đó:

```text
mark_dropped(place)
effect += DROP
```

Nếu partial:

```text
drop only owned children
```

---

# 18. Tạo view

MIR:

```text
VIEW place
```

Algorithm:

```text
verify_initialized(place)
verify_readable(place)

region = region_of(place)

cap = Capability(
    mode = READ,
    provenance = root(place),
    region = region
)

add(cap)
```

---

# 19. Tạo mutable view

```text
VIEW_MUT place
```

Algorithm:

```text
verify_initialized(place)
verify_writable(place)

if any active capability overlaps region:
    error

cap = Capability(
    mode = WRITE,
    provenance = root(place),
    region = region
)

add(cap)
```

---

# 20. Capability conflict

Hàm:

```text
conflicts(capA, capB)
```

trước tiên:

```text
relation = relation(capA.region, capB.region)
```

Nếu:

```text
DISJOINT
```

=> false.

Nếu:

```text
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

thì xét mode.

```text
READ + READ
    → false

READ + WRITE
    → true

WRITE + READ
    → true

WRITE + WRITE
    → true
```

---

# 21. Capability lifetime

Không giữ capability đến lexical scope.

Verifier chạy use analysis.

Ví dụ:

```axiom id="7l2hkk"
let v = view(buffer)

use(v)

modify(buffer)
```

Tại:

```text
use(v)
```

verifier biết đây là last use.

Sau instruction:

```text
remove capability(v)
```

Do đó `modify(buffer)` hợp lệ.

---

# 22. Last-use algorithm

Với mỗi SSA/local value:

```text
uses(value)
```

ta tính:

```text
last_use(value)
```

Trong CFG không tuyến tính, đây không chỉ là “instruction cuối cùng theo số thứ tự”.

Cần tính **liveness**.

Một value live tại block nếu:

```text
value is used in block
OR
value is live in successor
```

trừ khi đã consumed.

Vì vậy:

```text
LiveIn[B]
LiveOut[B]
```

cũng là backward dataflow.

---

# 23. Axiom cần hai dataflow direction

Đây là điểm kiến trúc quan trọng:

```text
Ownership:
    FORWARD

Initialization:
    FORWARD

Region/capability validity:
    FORWARD

Last-use/liveness:
    BACKWARD
```

Sau đó kết hợp.

```text
        CFG
       /   \
 forward   backward
    │         │
 ownership   liveness
    │         │
    └────┬────┘
         ▼
   capability lifetime
```

---

# 24. Ephemeral view

Implicit:

```axiom id="dwn0k2"
sum(numbers)
```

không tạo một local view persistent.

Verifier tạo capability:

```text
temporary capability
```

trong thời gian call:

```text
CALL:
    add READ capability
    verify callee effect
    execute call semantics
    remove capability
```

Nếu effect summary cho thấy callee giữ reference:

```text
ESCAPE
```

=> reject.

---

# 25. Function effect verification

Giả sử:

```text
foo:
    READ(arg0.age)
```

Call:

```axiom id="m0w99s"
foo(person)
```

Mapping:

```text
arg0 → person
```

nên effect thành:

```text
READ(person.age)
```

Nếu đang có:

```text
mut_view(person.name)
```

thì:

```text
person.name
DISJOINT
person.age
```

=> OK.

---

# 26. Effect `MAY_RELOCATE`

Function summary:

```text
Vec.push:
    WRITE(arg0.elements)
    MAY_RELOCATE(arg0.storage)
```

Nếu:

```text
active_view.provenance == arg0.storage
```

=> conflict.

Nếu không có active dependent capability:

=> OK.

---

# 27. Provenance dependency

Capability:

```text
Capability {
    provenance = Allocation #42
}
```

Relocation:

```text
MAY_RELOCATE(Allocation #42)
```

invalidate:

```text
all capabilities where provenance == #42
```

Không cần so sánh byte region.

---

# 28. Return view

Function:

```text
fn first(x: view<Vec>) -> view<T>
```

return capability phải có provenance:

```text
provenance(return) = provenance(input)
```

Verifier kiểm tra:

```text
return capability
    ⊆ lifetime(input provenance)
```

Nếu input là ephemeral view:

```text
returning it
```

thì capability escape khỏi call.

Compiler chỉ cho phép nếu API semantics đảm bảo input capability itself is long-lived.

Ví dụ:

```text
fn first(x: view<Vec>) -> view<T>
```

caller:

```text
let v = first(view(vec))
```

không được phép nếu temporary view của `vec` kết thúc khi call kết thúc.

Đây là một case phải reject.

---

# 29. Escape analysis

Mọi view được phân loại:

```text
NON_ESCAPING
RETURN
GLOBAL
HEAP
CLOSURE
TASK
UNKNOWN
```

Rules:

```text
NON_ESCAPING
    → OK

RETURN
    → only if provenance lifetime sufficient

GLOBAL
    → owner must have global/static lifetime

TASK
    → requires ownership transfer or valid shared capability

UNKNOWN
    → reject in safe code
```

---

# 30. Closure

Closure environment được coi như struct.

Ví dụ:

```axiom id="4j9gpp"
let v = view(buffer)

let f = || use(v)
```

Capture:

```text
closure.field0 = v
```

Verifier xem:

```text
closure lifetime
```

như lifetime của capability.

Nếu closure escape khỏi owner:

```text
buffer
```

thì reject.

Nếu closure non-escaping:

```text
f()
```

có thể hoàn toàn hợp lệ.

---

# 31. Spawn

```text
spawn(|| use(buffer))
```

closure escape vào execution context.

Compiler phải quyết định capture:

```text
MOVE
VIEW
COPY
```

Nếu capture VIEW:

```text
requires valid cross-context shared capability
```

Nếu capture MOVE:

```text
requires Send(buffer)
```

Đây là chỗ `Send` và capability interaction xảy ra.

---

# 32. Async suspend

Trước:

```text
SUSPEND
```

verifier lấy:

```text
live values
live capabilities
```

Nếu capability còn live:

```text
view(x)
```

thì provenance `x` phải tồn tại xuyên suspension.

Nếu task migratable:

```text
all relevant state must satisfy Send
```

Nếu local executor:

```text
spawn_local
```

có thể không yêu cầu Send, nhưng ownership/lifetime vẫn phải đúng.

---

# 33. Cleanup verification

Sau khi ownership dataflow hoàn tất, verifier phải đảm bảo:

```text
every owning value
```

đi đến một trong:

```text
MOVE
DROP
RETURN ownership
```

trên mọi terminating path.

Không được:

```text
OWNED → function end
```

mà không có semantic resolution.

Trừ:

```text
Copy
```

hoặc:

```text
static/global ownership
```

theo rule riêng.

---

# 34. Worked example

Ta dùng:

```axiom id="1e0cbx"
struct Person {
    name: String
    age: i32
}

fn example(cond: bool) {
    let p = create_person()
    let name = view(p.name)

    if cond {
        modify(p.age)
    }

    use(name)
}
```

---

## CFG

Compiler tạo:

```text id="vvx1l2"
B0:
    p = create_person()
    name = VIEW(p.name)
    BRANCH cond → B1 / B2

B1:
    modify(p.age)
    JUMP B3

B2:
    JUMP B3

B3:
    use(name)
    DROP p
    RETURN
```

---

# 35. B0 state

Sau:

```text
p = create_person()
```

```text id="jfq1z5"
p       = OWNED
p.name  = OWNED
p.age   = OWNED
```

Sau:

```text
name = VIEW(p.name)
```

capability:

```text id="5k9n0h"
C1:
    provenance = p
    region = p.name
    mode = READ
```

---

# 36. B1

```text
modify(p.age)
```

Effect:

```text id="sg2t7m"
WRITE(p.age)
```

Conflict:

```text id="cy4sz6"
C1 = READ(p.name)
```

So verifier calculates:

```text id="j0f9eg"
relation(p.name, p.age)
    = DISJOINT
```

=> no conflict.

B1 output:

```text id="wz03u7"
p.name = OWNED
p.age  = OWNED
C1      = active
```

---

# 37. B2

Không có mutation.

```text id="t2h4x6"
p.name = OWNED
p.age  = OWNED
C1 = active
```

---

# 38. Merge B3

Hai trạng thái giống nhau:

```text id="hph9b8"
p.name = OWNED
p.age  = OWNED
C1 = active
```

---

# 39. `use(name)`

READ capability:

```text id="x3kqk0"
READ(p.name)
```

`C1` cũng READ:

```text id="6t8s6c"
READ(p.name)
```

READ + READ:

```text id="r0x3w2"
OK
```

Nếu đây là last-use của `name`:

```text id="5n3a4q"
remove C1
```

---

# 40. `DROP p`

Bây giờ không còn active capability.

```text id="9g8n3v"
DROP p
```

`p` vẫn:

```text
name = OWNED
age  = OWNED
```

nên:

```text id="p0qz5x"
DROP p.name
DROP p.age
```

Nếu `String` có Drop.

Accept.

---

# 41. Thay đổi một dòng

Nếu B1 là:

```axiom id="aj4of9"
modify(p)
```

thì effect:

```text
WRITE(p)
```

Region:

```text
p CONTAINS p.name
```

Capability:

```text
READ(p.name)
```

=> conflict.

Compiler reject.

Đây chính xác là hành vi chúng ta muốn.

---

# 42. Thay đổi khác

Nếu B1:

```axiom id="r2d0i7"
modify(p.name)
```

thì:

```text
WRITE(p.name)
```

conflict:

```text
READ(p.name)
```

=> reject.

---

# 43. Nhưng:

```axiom id="gk2q6m"
modify(p.age)
```

=> OK.

Đây là bằng chứng rằng region analysis hoạt động ở cấp field.

---

# 44. Loop example

```axiom id="g5n8zi"
let p = create_person()
let name = view(p.name)

while cond {
    modify(p.age)
}

use(name)
```

Mỗi iteration:

```text
READ(p.name)
WRITE(p.age)
```

DISJOINT.

Fixed point ổn định:

```text
C1 remains valid
```

=> Accept.

---

# 45. Loop relocation

```axiom id="n3p9eg"
let p = create_person()
let name = view(p.name)

while cond {
    grow(p)
}

use(name)
```

Nếu:

```text
grow(p):
    WRITE(p)
    MAY_RELOCATE(p.storage)
```

thì:

```text
C1.provenance = p.storage
```

và:

```text
MAY_RELOCATE(p.storage)
```

=> conflict.

Reject.

---

# 46. Đây là điểm rất đáng chú ý

Verifier không cần biết:

```text
grow()
```

thực tế có reallocate hay không.

Chỉ cần:

```text
MAY_RELOCATE
```

là đủ.

Native optimizer sau này có thể biết:

```text
capacity > len
```

và chứng minh lần `push` này không relocate.

Khi đó optimizer/backend có thể bỏ restriction **sau khi semantic validity đã được chứng minh**?

Cần cẩn thận: safe program không thể dựa vào runtime branch để tạo dangling view.

Do đó v0.1 nên conservative ở language level.

Optimization không được biến một chương trình bị reject thành accepted.

---

# 47. Đây dẫn tới một nguyên tắc

> **Verifier operates on worst-case semantic effects; optimizer may remove operations, but may not strengthen source-level guarantees retroactively.**

Nói đơn giản:

```text
MAY_RELOCATE
```

đủ để verifier reject.

Không được nói:

> “Optimizer biết lần này không relocate nên source hợp lệ.”

Điều đó làm semantics phụ thuộc optimization.

---

# 48. Error model

Verifier nên trả diagnostics có cấu trúc:

```text
VerifierError {
    code
    primary_span
    related_spans[]
    reason
    operation
    region_a
    region_b
    capability_a
    capability_b
}
```

Ví dụ:

```text
AX_VIEW_0042
cannot mutate `p.age` while a view of overlapping storage is active
```

Nhưng trong trường hợp `p.name` vs `p.age`, không báo lỗi.

---

# 49. Compiler implementation architecture

Tôi khuyên không viết verifier thành một file khổng lồ.

```text
verifier/
├── state
│   ├── ownership
│   ├── initialization
│   └── capabilities
│
├── place
│   ├── projection
│   └── region
│
├── dataflow
│   ├── forward
│   ├── backward
│   └── fixed_point
│
├── effects
│   ├── summary
│   ├── conflict
│   └── invalidation
│
├── ownership
│   ├── move
│   ├── copy
│   └── partial_move
│
├── views
│   ├── create
│   ├── provenance
│   ├── last_use
│   └── escape
│
├── drop
│   ├── analysis
│   └── elaboration
│
├── concurrency
│   ├── send
│   └── share
│
├── async
│   └── suspension
│
└── diagnostics
```

AI agent sẽ dễ implement/test từng phần hơn rất nhiều.

---

# 50. Verifier Contract

Ta có thể freeze thêm:

### AOV-19

Mọi safe MIR `LOAD` phải có valid initialization và READ proof.

### AOV-20

Mọi safe MIR `STORE` phải có valid WRITE proof.

### AOV-21

Mọi `MOVE` phải consume đúng ownership state.

### AOV-22

Mọi `DROP` chỉ được áp dụng lên resource còn ownership hợp lệ.

### AOV-23

Mọi persistent view phải có provenance hợp lệ.

### AOV-24

Mọi ephemeral view phải chứng minh non-escape.

### AOV-25

Mọi active capability conflict phải được chứng minh DISJOINT hoặc phải bị reject.

### AOV-26

Mọi `MAY_RELOCATE` phải được kiểm tra với active dependent capabilities.

### AOV-27

Mọi terminating path phải resolve ownership/resource obligations.

### AOV-28

Mọi async suspension phải preserve state cần thiết.

### AOV-29

Mọi cross-context transfer phải satisfy `Send`.

### AOV-30

Mọi cross-context immutable sharing phải satisfy `Share`.

---

# 51. Một kết luận quan trọng về hiệu năng

Đây chính là chỗ cần phân biệt:

```text
Compiler cost
```

và:

```text
Program runtime cost
```

Verifier có thể cực kỳ phức tạp:

```text
CFG
+
fixed-point
+
region analysis
+
escape analysis
+
effect inference
```

nhưng sau compilation:

```text
runtime overhead = 0
```

trong rất nhiều trường hợp.

Ví dụ:

```axiom id="3k8x4x"
fn sum(v: view<i32>) -> i32
```

Source có view semantics.

Native optimizer có thể tạo:

```text
pointer + length
```

hoặc thậm chí scalarize/eliminate hoàn toàn.

Không cần:

```text
GC
RC
object header
runtime borrow tracking
```

Đây chính xác là hướng **compiler phức tạp, language đơn giản, runtime nhẹ** mà Axiom đang hướng tới.

---

# 52. Nhưng tôi muốn dừng lại ở đây trước một bước rất quan trọng

Bây giờ chúng ta đã có đủ cơ sở để chuyển từ verifier sang **Drop Elaboration + MIR normalization**.

Pipeline nên chính thức thành:

```text
Typed MIR
   │
   ▼
Raw MIR Verification
   │
   ▼
Ownership / Region / Capability Proof
   │
   ▼
Drop Elaboration
   │
   ▼
Cleanup Normalization
   │
   ▼
Verified MIR v0.1
   │
   ▼
Semantic Oracle
   │
   ├── Interpreter
   │
   └── Conformance Tests
   │
   ▼
Optimizer
```

Và đây là điểm rất quan trọng:

**Verifier không nên tự chèn Drop một cách lẫn lộn với proof.**

Nên tách:

```text
Verification
    ↓
"chương trình hợp lệ"

Drop Elaboration
    ↓
"đã biến ownership semantics thành control-flow/resource operations cụ thể"
```

Nếu làm vậy, MIR sau Drop Elaboration sẽ trở thành một **semantic executable IR rất sạch**, cực kỳ thuận lợi cho interpreter và backend.

Bước kế tiếp vì vậy nên là **`AXIOM DROP ELABORATION v0.1`**: cách compiler tự động sinh cleanup block cho `return`, `break`, `continue`, `panic`, `Result ?`, branch, partial move và async suspension — đây là phần quyết định Axiom có thực sự đạt được deterministic resource management mà không cần programmer viết `defer` hay destructor boilerplate hay không.