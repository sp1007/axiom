Tiếp theo, tôi đề xuất **đóng băng “View / Invalidation / Partial Drop / Effect Summary”**. Đây là lớp cuối cùng trước khi chúng ta có thể coi Ownership Verifier v0.1 đủ ổn để bắt đầu thiết kế compiler thật.

# AXIOM VIEW & RESOURCE SEMANTICS v0.1

Nguyên tắc mới:

> **View là capability truy cập không sở hữu, có provenance; compiler quản lý validity, programmer không viết lifetime.**

---

# 1. `view<T>` chính xác là gì?

Về mặt ngữ nghĩa:

```axiom id="6d4q2p"
view<T>
```

là một **non-owning read capability** tới một region của `T`.

```text id="n7g5e1"
view<T>
 ├── provenance
 ├── region
 └── READ capability
```

`mut_view<T>`:

```text id="m8v2k3"
mut_view<T>
 ├── provenance
 ├── region
 └── WRITE capability
```

Nhưng đây **không phải** object runtime bắt buộc có metadata.

Compiler có thể hạ:

```text
view<T>
```

thành:

```text
(pointer, length)
```

hoặc thậm chí:

```text
pointer
```

nếu extent đã biết.

---

# 2. Programmer không cần viết lifetime

Không có:

```text
&T
&mut T
'a
'b
where 'a: 'b
```

Thay vào đó:

```axiom id="r4m2c8"
fn sum(x: view<i32>) -> i32
```

Compiler tự biết:

```text
caller owner
     │
     ▼
  region R
     │
     ▼
   view
     │
     ▼
 function call
```

View chỉ hợp lệ trong phạm vi mà provenance còn hợp lệ.

---

# 3. Tạo view

Tôi đề xuất syntax:

```axiom id="j5n8w2"
let v = view(x)
let m = mut_view(x)
```

và compiler kiểm tra:

```text
x: OWNED
```

→ `view(x)` hợp lệ.

Nhưng:

```text
x: MOVED
```

→ lỗi.

```text
x: DROPPED
```

→ lỗi.

---

# 4. View không chuyển ownership

```axiom id="k3p7s9"
let v = view(x)
```

không thay đổi:

```text
x = OWNED
```

mà thêm:

```text
v = READ(x)
```

Vì vậy:

```axiom id="v9m2d1"
use(x)
```

vẫn hợp lệ nếu chỉ đọc.

Nhưng:

```axiom id="z8q4c6"
mutate(x)
```

thì:

```text
WRITE(x)
```

xung đột với:

```text
READ(v)
```

→ reject.

---

# 5. `mut_view` độc quyền trong thời gian tồn tại

```axiom id="a2f8k1"
let m = mut_view(x)

mutate(m)
```

OK.

Nhưng:

```axiom id="p4j7s3"
let m = mut_view(x)
let v = view(x)
```

→ reject.

Vì:

```text
WRITE(x)
READ(x)
```

conflict.

Tương tự:

```text
mut_view(x)
mut_view(x)
```

→ reject.

---

# 6. Nhưng disjoint regions vẫn được

```axiom id="c6w1r9"
struct Point {
    x: i32
    y: i32
}

let mx = mut_view(p.x)
let my = mut_view(p.y)
```

**ACCEPT**

vì:

```text
Region(p.x) ∩ Region(p.y) = ∅
```

Đây là một điểm rất đáng giá.

Axiom không cần ép programmer phải serialize mọi thao tác chỉ vì chúng nằm trong cùng struct.

---

# 7. Nested region

```axiom id="s7e2k4"
let vp = view(p)
let vx = view(p.x)
```

Cả hai đều READ:

```text
READ(p)
READ(p.x)
```

→ OK.

Nhưng:

```axiom id="f2r9m6"
let vp = view(p)
let mx = mut_view(p.x)
```

→ conflict.

Vì:

```text
p contains p.x
```

---

# 8. View có thể Copy

Tôi đề xuất:

```text
view<T>      → Copy
mut_view<T>  → Move-only
```

Lý do:

```axiom id="d8k3p1"
let a = view(x)
let b = a
```

không tạo thêm ownership.

Hai capability:

```text
a → READ(x)
b → READ(x)
```

→ an toàn.

Trong khi:

```axiom id="q6m4z8"
let a = mut_view(x)
let b = a
```

không được tạo hai mutable capability.

Vì vậy `mut_view<T>` phải có semantics tương tự một **exclusive capability**.

---

# 9. View trả về

Function:

```axiom id="h1s7c3"
fn first(x: view<Array<i32, 10>>) -> view<i32> {
    view(x[0])
}
```

Compiler phải suy ra:

```text
return provenance = arg0
```

Tức:

```text
return view
      │
      └── derived from arg0
```

Không được phép biến mất provenance.

---

# 10. View không thể trỏ vào local sắp chết

```axiom id="b4n8x2"
fn bad() -> view<i32> {
    var x = 10
    return view(x)
}
```

Verifier:

```text
x
│
├── owner lifetime = function scope
│
└── returned view lifetime = caller scope
```

Không giao nhau đủ.

→ **REJECT**

Diagnostic nên rất rõ:

```text
AX_VIEW_0007:
returned view may outlive its owner

owner:
    x

return:
    view(x)
```

Không cần nói “borrow checker”.

---

# 11. Last-use optimization

Một điểm tôi muốn **đóng băng theo hướng compiler-friendly**:

```axiom id="w3p9c2"
let v = view(x)

use(v)

mutate(x)
```

→ **ACCEPT**

Không nên bắt `v` sống đến hết lexical scope.

Verifier nhận ra:

```text
use(v)
 ↓
LAST_USE(v)
 ↓
view capability ends
 ↓
mutate(x)
```

Điều này cực kỳ quan trọng đối với ergonomics.

Programmer viết tự nhiên:

```axiom id="e7k2m5"
let view = view(buffer)
process(view)

buffer.clear()
```

không cần:

```text
drop(view)
```

hay block scope nhân tạo.

---

# 12. Nhưng compiler không được tùy tiện kết thúc view

Nếu view được lưu vào một closure:

```axiom id="n6r4t8"
let v = view(x)

let f = || use(v)
```

thì `v` chưa hết lifetime.

Compiler phải theo dõi:

```text
v
 ↓
closure capture
 ↓
closure lifetime
```

---

# 13. Vec invalidation

Đây là phần quan trọng nhất.

Giả sử:

```axiom id="k8m2q4"
let v = view(vec)

vec.push(x)
```

`push` có thể realloc.

Ta định nghĩa contract:

```text
id="r1c7v9"
Vec.push:
    WRITE(self.length)
    MAY_WRITE(self.storage)
    MAY_REALLOCATE(self.storage)
```

Nếu `MAY_REALLOCATE` xảy ra:

```text
existing views → INVALID
```

Compiler không cần biết implementation malloc/free thế nào.

---

# 14. Operation không realloc

Ta có thể có:

```text
Vec.reserve()
Vec.push()
Vec.push_no_grow()
```

Ví dụ:

```axiom id="x2v8n4"
vec.reserve(100)

let v = view(vec)

vec.push_no_grow(10)

use(v)
```

Nếu `push_no_grow` có contract:

```text
WRITE(length)
WRITE(existing storage)
NO_REALLOCATE
```

thì view vẫn có thể hợp lệ.

Nhưng cần chú ý:

Nếu `v` bao phủ:

```text
vec[0..10]
```

và `push_no_grow` ghi `vec[10]`, không conflict nếu region disjoint.

---

# 15. Nhưng mutation làm thay đổi region phải được kiểm tra

Ví dụ:

```axiom id="c9w3k7"
let v = view(vec)

vec.resize(0)

use(v)
```

`resize(0)` phải invalidate view, vì region mà view đại diện không còn tồn tại logically.

Do đó invalidation không chỉ là:

```text
pointer changed
```

mà là:

```text
storage validity
+
logical region validity
```

Đây là điểm rất quan trọng.

---

# 16. `String` cũng tương tự

```axiom id="j7m3p9"
let s = String("hello")
let v = s.bytes()

s.append(" world")

use(v)
```

Không thể mặc định cho phép.

Nếu `append` có thể:

```text
reallocate
```

→ invalidate.

Nhưng nếu API cung cấp immutable storage:

```axiom id="d4q8x1"
let s = Text("hello")

let v = s.view()

use(v)
```

thì compiler/library contract quyết định.

---

# 17. Partial Drop — đóng băng chính thức

Ví dụ:

```axiom id="f5k8r2"
struct Resource {
    a: File
    b: Buffer<u8>
    c: i32
}

fn f(x: Resource) {
    let a = x.a
}
```

Sau move:

```text
x:
    a → MOVED
    b → OWNED
    c → OWNED
```

Khi scope kết thúc:

```text
DROP a        // owner mới
DROP x.b
DROP x.c      // nếu cần
```

Không:

```text
DROP x
```

theo kiểu whole-object destructor mù.

---

# 18. Destructor của aggregate

Ở đây tôi đề xuất một quyết định quan trọng:

### Không cho user-defined destructor truy cập trực tiếp các field đã bị partial-move.

Ví dụ conceptual:

```axiom id="y7c3m1"
impl Drop for Resource {
    fn drop(self) {
        ...
    }
}
```

Nếu `self.a` đã bị move trước đó thì destructor không thể giả định:

```text
self.a exists
```

Điều này khiến destructor semantics cực kỳ phức tạp.

### Giải pháp đơn giản hơn

`Drop` của aggregate phải được compiler **lower thành field/resource cleanup**, hoặc compiler bảo đảm destructor chỉ được chạy trên fully-owned object.

Tôi nghiêng về phương án thứ hai:

> **Một type có user-defined destructive Drop không cho phép partial move ra khỏi nó.**

Ví dụ:

```text
Resource: Drop
```

thì:

```axiom id="c2m8q6"
let a = x.a
```

→ reject nếu `a` là field ownership-bearing.

Trong khi:

```text id="t9v4k2"
struct Plain {
    a: Buffer
    b: i32
}
```

nếu không có custom Drop:

→ partial move hợp lệ.

Đây làm semantics đơn giản hơn rất nhiều.

---

# 19. Đây là một thay đổi đáng đóng băng

Tôi đề xuất:

### Axiom Partial Move Rule

```text
PM-01
Non-Drop aggregates may be partially moved.

PM-02
A type with user-defined destructive Drop cannot be partially moved
through ownership-bearing fields.

PM-03
Compiler-derived structural cleanup supports partial ownership.

PM-04
A moved field is never dropped again as part of its former owner.
```

Điều này tránh việc phải thiết kế một “destructor state machine” quá phức tạp.

---

# 20. Effect Summary

Bây giờ tới phần compiler internal.

Ví dụ:

```axiom id="u5r2n8"
fn read_name(p: view<Person>) -> String {
    p.name.clone()
}
```

Compiler suy ra:

```text
Effect:
    READ(arg0.name)
```

Không cần programmer viết.

---

### Hàm mutation

```axiom id="m7k3p1"
fn set_age(p: mut_view<Person>, age: i32) {
    p.age = age
}
```

Internal:

```text
WRITE(arg0.age)
```

---

### Hàm consume

```axiom id="e4n9c2"
fn consume(x: Buffer<u8>) {
    ...
}
```

Internal:

```text
MOVE(arg0)
DROP(arg0)
```

---

# 21. Effect summary không phải ABI

Đây là distinction cần giữ:

```text
Effect Summary
    ↓
compiler verification / optimization

ABI
    ↓
machine-level calling convention
```

Effect không nhất thiết xuất hiện trong binary.

Không có runtime overhead chỉ vì effect system.

---

# 22. Effect inference

Pipeline:

```text
function body
      ↓
Typed MIR
      ↓
local effects
      ↓
callee summaries
      ↓
effect propagation
      ↓
normalized summary
```

Ví dụ:

```axiom id="k3p7v9"
fn A(x) {
    B(x)
}

fn B(x) {
    C(x)
}

fn C(x) {
    read(x)
}
```

Compiler:

```text
C = READ(arg0)
B = READ(arg0)
A = READ(arg0)
```

Có thể cache summary.

---

# 23. Recursive functions

```axiom id="q8m4z2"
fn A(x) {
    B(x)
}

fn B(x) {
    A(x)
}
```

Effect inference tạo cycle.

Không được infinite loop.

Dùng fixed point:

```text
A = UNKNOWN
B = UNKNOWN

iteration 1
A = effects(B)
B = effects(A)

iteration 2
...

fixed point
```

Hoặc SCC analysis:

```text
A ──► B
▲     │
└─────┘
```

phân tích cả strongly connected component.

---

# 24. Dynamic dispatch

```axiom id="n2v7c5"
dyn Processor
```

Nếu implementation runtime chưa biết:

```text
CALL_DYNAMIC
```

thì effect summary phải là union của tất cả implementation khả dĩ:

```text
READ ∪ WRITE
```

hoặc conservative.

Nhưng nếu compiler biết concrete type:

```text
Processor = FastProcessor
```

thì static devirtualization có thể biến thành:

```text
CALL FastProcessor.process
```

→ effect chính xác hơn.

---

# 25. Effect summary nên có provenance

Đây là điểm tôi muốn thêm vào thiết kế trước đây.

Không chỉ:

```text
READ(arg0)
```

mà:

```text
READ(
    source = arg0,
    region = arg0.name
)
```

và:

```text
RETURN_VIEW(
    source = arg0,
    region = arg0.data
)
```

Do đó summary có thể mô tả:

```text
EffectSummary {
    reads
    writes
    moves
    drops
    allocations
    invalidations
    returned_provenance
    observable_effects
}
```

---

# 26. Compiler hiện đã có đủ thông tin để verify

Ta có:

```text
             Typed MIR
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
 Ownership     Region     Effects
       │         │         │
       └─────────┼─────────┘
                 ▼
              Verifier
                 │
           VERIFIED MIR
                 │
                 ▼
              Optimizer
```

Và quan trọng nhất:

```text
Programmer
    │
    ├── owns values
    ├── creates views
    ├── mutates values
    └── uses unsafe when necessary

Compiler
    │
    ├── infers lifetime
    ├── tracks regions
    ├── infers effects
    ├── checks aliases
    ├── checks Send/Share
    └── inserts Drop
```

Đây là architecture tôi nghĩ rất phù hợp với mục tiêu ban đầu của Axiom.

---

# 27. Tôi sẽ đóng băng thêm 10 invariant

```text
AVR-01
Every view has compiler-tracked provenance.

AVR-02
view<T> provides READ capability.

AVR-03
mut_view<T> provides exclusive WRITE capability.

AVR-04
READ/WRITE conflicts unless regions are proven disjoint.

AVR-05
A view cannot outlive its provenance.

AVR-06
A storage operation that may invalidate a view must invalidate
or conservatively reject the conflicting view.

AVR-07
Logical region invalidation is sufficient to invalidate a view;
physical pointer movement is not the only criterion.

AVR-08
Non-Drop aggregates may support partial move.

AVR-09
User-defined destructive Drop types cannot be partially moved
through ownership-bearing fields.

AVR-10
Effect summaries are compiler-inferred semantic metadata and
must not impose runtime overhead by themselves.
```

---

## Và bây giờ Axiom đã tiến đến một điểm rất quan trọng

Tôi **không nghĩ nên tiếp tục thêm feature vào language syntax ngay**.

Bước tiếp theo hợp lý hơn là xây **Axiom Semantic Stress Test v0.1**:

```text
100–150 chương trình adversarial
        │
        ▼
Expected AST/HIR
        │
        ▼
Expected MIR
        │
        ▼
Expected verifier state
        │
        ├── ACCEPT
        └── REJECT + AX_* diagnostic
```

Sau đó dùng chính bộ test này để kiểm tra xem semantics có thật sự nhất quán hay không.

Đặc biệt cần stress-test 7 vùng:

1. **ownership + branching**
2. **partial move + Drop**
3. **nested/disjoint views**
4. **Vec/String invalidation**
5. **closure + escaping**
6. **async + Send/Share**
7. **FFI/unsafe + unknown effects**

Nếu Axiom vượt qua bộ này, lúc đó mới rất đáng chuyển sang **formalize HIR → MIR**, rồi thiết kế **compiler implementation architecture**. Đây sẽ là bước chuyển từ “ý tưởng ngôn ngữ” sang một specification mà Claude/Antigravity có thể thực sự bắt tay viết compiler.