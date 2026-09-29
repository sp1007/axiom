Tiếp tục. Đây là phần tôi cho rằng **quan trọng nhất về hiệu năng của Axiom**: không phải stack hay heap, mà là **compiler có được phép biết hai vùng nhớ có thể trùng nhau hay không**.

# AXIOM MEMORY ACCESS, POINTER & ALIASING v0.1

Mục tiêu:

> Safe code có memory safety mạnh, nhưng machine code sau optimization vẫn có thể gần với C/C++ hoặc tốt hơn trong những trường hợp compiler chứng minh được nhiều hơn.

---

# 1. Đầu tiên: đừng biến mọi thứ thành pointer

Axiom nên có 4 tầng:

```text
VALUE
  │
  ├── PLACE
  │
  ├── VIEW / MUT_VIEW
  │
  └── RAW POINTER
```

Trong đó:

| Loại | Safe | Ownership | Compiler biết provenance | Dùng chính |
|---|---:|---:|---:|---|
| Value | ✅ | Có | Có | thông thường |
| Place | ✅ | Không | Có | field/index/access |
| `view<T>` | ✅ | Không | Có | read access |
| `mut_view<T>` | ✅ | Không | Có | mutable access |
| `*const T` | ⚠️ unsafe | Không | hạn chế | low-level |
| `*mut T` | ⚠️ unsafe | Không | hạn chế | systems |

Điều này giúp phần lớn chương trình Axiom **không cần pointer syntax**.

---

# 2. Place mới là abstraction quan trọng

Ví dụ:

```axiom
person.age
```

không phải pointer.

Nó là:

```text
Place {
    base = person
    projection = Field(age)
}
```

Tương tự:

```axiom
buffer[i]
```

là:

```text
Place {
    base = buffer
    projection = Index(i)
}
```

Compiler có thể biết chính xác vùng nhớ.

---

# 3. Region

Mỗi Place được ánh xạ thành:

```text
MemoryRegion
```

Ví dụ:

```text
person.name
```

→

```text
R(person.name)
```

và:

```text
person.age
```

→

```text
R(person.age)
```

Compiler có thể chứng minh:

```text
R(person.name) DISJOINT R(person.age)
```

Do đó:

```axiom
mutate_name(person.name)
mutate_age(person.age)
```

có thể chạy an toàn đồng thời về mặt aliasing.

---

# 4. Đây chính là “restrict-like information”

C/C++ có những trường hợp programmer/compiler có thể biết:

```text
p != q
```

nhưng type system không luôn thể hiện được.

Axiom có thể biết điều đó **từ ownership/capability model**.

Ví dụ:

```axiom
fn process(a: mut_view<Data>, b: mut_view<Data>)
```

Nếu hai view có thể overlap:

```text
ERROR
```

Nếu compiler chứng minh:

```text
Region(a) DISJOINT Region(b)
```

→ accept.

---

# 5. Không cần programmer viết `restrict`

Tôi **không đề xuất**:

```axiom
fn foo(a: restrict mut_view<T>, ...)
```

vì đây chính là loại annotation mà chúng ta muốn loại bỏ.

Compiler tự suy luận từ semantic access.

---

# 6. READ aliasing

Cho phép:

```text
READ + READ = OK
```

Ví dụ:

```axiom
fn sum(a: view<i32>, b: view<i32>) -> i32
```

Hai view có thể cùng trỏ vào dữ liệu.

Không có vấn đề nếu chỉ đọc.

---

# 7. WRITE aliasing

```text
WRITE + WRITE = ERROR
```

nếu region có thể overlap.

Ví dụ:

```text
fn foo(a: mut_view<i32>, b: mut_view<i32>)
```

và caller tạo:

```text
foo(mut_view(x), mut_view(x))
```

→ reject.

---

# 8. READ + WRITE

```text
READ + WRITE = ERROR
```

nếu overlap.

Ví dụ conceptually:

```text
let r = view(x)
modify(mut_view(x))
use(r)
```

Không hợp lệ trong safe code.

---

# 9. MOVE

MOVE mạnh hơn WRITE:

```text
MOVE + anything = conflict
```

vì ownership chuyển đi.

Ví dụ:

```axiom
consume(x)
use(x)
```

→ rejected.

---

# 10. DROP

DROP cũng cần access capability.

```text
DROP + active READ = conflict
DROP + active WRITE = conflict
```

Ví dụ:

```text
let r = view(x)
drop(x)
use(r)
```

→ compiler reject.

---

# 11. View không phải runtime borrow object

Ví dụ:

```axiom
fn sum(v: view<i32>) -> i32
```

Machine code có thể đơn giản:

```text
pointer
length
```

Compiler semantic layer giữ:

```text
provenance
region
access=READ
```

Sau verification:

```text
provenance metadata
↓
erased
```

Đây là điểm quan trọng để không biến Axiom thành một runtime-managed reference language.

---

# 12. Lifetime cũng không cần runtime

Ví dụ:

```axiom
fn sum(v: view<i32>) { ... }
```

Không cần runtime:

```text
owner_id
lifetime_id
refcount
```

Compiler kiểm tra:

```text
owner alive
region valid
capability active
```

rồi xóa thông tin đó.

---

# 13. View return

Hợp lệ:

```axiom
fn first(v: view<i32>) -> view<i32> {
    return v
}
```

vì provenance:

```text
output ⊆ input
```

Không hợp lệ:

```axiom
fn bad() -> view<i32> {
    let x = ...
    return view(x)
}
```

vì:

```text
owner(x) dies
output survives
```

---

# 14. View từ owner

Đã khóa trước:

```axiom
fn sum(v: view<i32>)
```

caller:

```axiom
sum(array)
```

được implicit temporary view.

Nhưng:

```axiom
let v = array
```

không tự biến thành view.

Muốn giữ capability:

```axiom
let v = view(array)
```

Điều này tránh “reference everywhere”.

---

# 15. `mut_view`

```axiom
fn fill(v: mut_view<i32>, value: i32)
```

caller:

```axiom
fill(array, 0)
```

compiler tạo mutable capability trong phạm vi call.

Sau call:

```text
capability expired
```

Không cần programmer quản lý lifetime.

---

# 16. Multiple mutable views tới disjoint fields

Ví dụ:

```axiom
struct Point {
    x: i32
    y: i32
}
```

Có thể conceptually:

```text
mx = mut_view(p.x)
my = mut_view(p.y)
```

vì:

```text
R(p.x) DISJOINT R(p.y)
```

→ hợp lệ.

Đây là một lợi thế lớn của region-based verifier.

---

# 17. Array slicing

Giả sử:

```text
a[0..10]
a[10..20]
```

Compiler có thể chứng minh:

```text
[0,10) DISJOINT [10,20)
```

Do đó:

```axiom
fill(first)
fill(second)
```

có thể an toàn.

---

# 18. Overlapping slices

```text
a[0..10]
a[5..15]
```

Compiler:

```text
OVERLAPS
```

Nếu cả hai mutable:

```text
ERROR
```

Nếu read-only:

```text
OK
```

---

# 19. Dynamic index

Đây là trường hợp khó:

```axiom
a[i]
a[j]
```

Compiler không biết:

```text
i != j
```

→ region relation:

```text
UNKNOWN
```

Nếu cả hai mutable:

```text
reject
```

trong safe code.

---

# 20. Nhưng không nên quá bảo thủ

Compiler có thể chứng minh:

```axiom
if i != j {
    ...
}
```

sau đó trong branch:

```text
R(a[i]) DISJOINT R(a[j])
```

→ cho phép.

Đây là lý do verifier nên dùng **path-sensitive facts**.

---

# 21. Region algebra

Tôi đề xuất giữ:

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
R(array)
contains
R(array[0..10])
```

và:

```text
R(array[0..10])
disjoint
R(array[10..20])
```

---

# 22. Region không nhất thiết là byte range

Đây là điểm rất quan trọng.

Không nên biến mọi region thành:

```text
[address, address+size)
```

ở semantic layer.

Region có thể là:

```text
FieldRegion
ArrayRange
AllocationRegion
ExternalRegion
UnknownRegion
```

Address range chỉ là machine-level representation.

---

# 23. Điều này giúp struct field

```text
person.name
person.age
```

có region identity độc lập ngay cả khi compiler chưa quyết định offset vật lý.

---

# 24. Raw pointer

Axiom vẫn phải cho phép:

```axiom
unsafe {
    let p: *mut T = ...
}
```

Raw pointer không có safe ownership semantics.

Compiler không được giả định:

```text
p != q
```

trừ khi chứng minh từ context.

---

# 25. Unsafe không phải “tắt compiler”

Đây là nguyên tắc phải giữ:

```text
unsafe
```

cho phép:

- dereference raw pointer
- pointer arithmetic
- reinterpretation
- volatile
- external memory
- hardware
- FFI tricks

Nhưng compiler vẫn kiểm tra:

- type correctness
- CFG
- syntax
- ABI
- explicit unsafe boundary.

---

# 26. Raw pointer dereference

```axiom
unsafe {
    *p = value
}
```

semantic:

```text
WRITE unknown/external region
```

Compiler không thể prove alias safety.

Programmer chịu trách nhiệm.

---

# 27. Sau unsafe boundary

Không nên để compiler “quên” toàn bộ state.

Ví dụ:

```axiom
let x = ...
unsafe {
    external_write(...)
}
use(x)
```

Compiler phải coi external call có effect:

```text
MAY_READ
MAY_WRITE
MAY_ESCAPE
```

nếu ABI contract không đủ cụ thể.

---

# 28. FFI effects

Ví dụ:

```axiom
extern @abi(C)
fn foo(p: *mut i32)
```

compiler không biết function làm gì.

Mặc định:

```text
effect = UNKNOWN_MEMORY
```

→ optimizer phải conservative.

Nếu programmer/library cung cấp contract:

```text
READ(p)
WRITE(p)
NO_CAPTURE
```

compiler có thể optimize mạnh hơn.

---

# 29. Đây là nơi tôi đề xuất `effect contract`

Không expose effect system quá phức tạp trong source language v0.1.

Nhưng compiler IR phải có:

```text
EffectSet {
    reads
    writes
    moves
    allocates
    deallocates
    sync
    volatile
    ffi
    panic
}
```

---

# 30. Pure function

Axiom không nhất thiết cần keyword:

```text
pure
```

trong Core.

Compiler có thể suy luận:

```text
function has no observable effects
```

và optimizer sử dụng fact.

Nếu programmer muốn contract:

```text
@pure
```

có thể là compiler attribute sau này.

---

# 31. Alias analysis

Sau ownership verification, optimizer có information:

```text
a: READ R1
b: WRITE R2
R1 DISJOINT R2
```

→ có thể reorder:

```text
load a
store b
```

hoặc vectorize.

---

# 32. Ví dụ

```axiom
fn add_arrays(
    dst: mut_view<i32>,
    a: view<i32>,
    b: view<i32>
) {
    for i in 0..dst.len {
        dst[i] = a[i] + b[i]
    }
}
```

Nếu compiler biết:

```text
dst DISJOINT a
dst DISJOINT b
```

thì loop rất dễ vectorize.

Không cần:

```text
restrict
```

---

# 33. Nhưng nếu caller truyền overlap?

Safe API phải không cho tạo capability vi phạm rule.

Ví dụ:

```text
dst = a
```

và cùng lúc:

```text
a = READ
dst = WRITE
```

→ conflict.

Compiler reject call.

---

# 34. Đây là điểm Axiom có thể vượt C ở một số trường hợp

C:

```c
void add(float *dst, float *a, float *b)
```

compiler không chắc alias.

Axiom:

```axiom
fn add(dst: mut_view<f32>,
       a: view<f32>,
       b: view<f32>)
```

có semantic capability information.

Compiler có thể biết:

```text
WRITE dst
READ a
READ b
```

và enforce no-conflict.

Do đó optimization dễ hơn mà không cần programmer thêm `restrict`.

---

# 35. Nhưng không nên tuyên bố Axiom “luôn nhanh hơn C”

Vẫn có:

- opaque FFI
- unsafe code
- dynamic indexing
- aliasing unknown
- external memory
- synchronization.

Điểm đúng hơn:

> **Axiom cung cấp cho optimizer nhiều alias information đáng tin cậy hơn safe C-like code, trong khi không yêu cầu programmer viết lifetime/borrow annotations.**

---

# 36. `volatile`

Volatile dùng cho:

- MMIO
- hardware register
- memory mapped device
- special external memory.

```text
volatile_load
volatile_store
```

Không dùng volatile để thread synchronization.

---

# 37. `volatile != atomic`

Phải khóa:

```text
VOLATILE
≠
ATOMIC
```

Volatile đảm bảo compiler không loại bỏ/reorder operation theo ordinary-memory rules.

Atomic đảm bảo concurrency memory model.

---

# 38. Atomic

Ví dụ:

```axiom
atomic_load(x, Acquire)
atomic_store(x, value, Release)
atomic_add(x, 1, AcqRel)
```

Memory order explicit.

---

# 39. Atomic cũng là observable effect

Optimizer không được biến:

```text
atomic_load
```

thành ordinary:

```text
load
```

chỉ vì kết quả “thường giống nhau”.

---

# 40. `memcpy`

Axiom nên có compiler intrinsic:

```text
memcpy(dst, src, size)
memmove(dst, src, size)
memset(dst, value, size)
```

nhưng source-level API có thể nằm trong low-level library.

Compiler có thể lower:

```text
memcpy
```

thành:

- inline loads/stores
- SIMD
- target intrinsic
- libc/system call
- specialized loop.

---

# 41. Type safety của memcpy

Không nên cho:

```axiom
memcpy(&x, &y, 999)
```

trong safe code.

Raw byte memory operation là unsafe/system-level.

Safe abstraction:

```text
copy(view<T>, view<T>)
```

có length/type semantics.

---

# 42. Bounds checking

```axiom
a[i]
```

safe semantics:

```text
check 0 <= i < len
load
```

Nhưng optimizer có thể prove:

```text
0 <= i < len
```

và loại check.

---

# 43. Ví dụ loop

```axiom
for i in 0..a.len {
    sum += a[i]
}
```

Compiler biết range:

```text
0 <= i < a.len
```

→ bounds check có thể biến mất.

Machine code có thể giống C loop.

---

# 44. Dynamic access

```axiom
a[user_input]
```

không prove bounds:

```text
runtime check
```

bắt buộc trong safe code.

---

# 45. Unsafe unchecked access

Có thể có:

```text
unsafe_get(a, i)
```

nhưng phải explicit.

Không nên:

```text
a[i]
```

tự động unchecked trong release mode.

---

# 46. Đây là điểm khác với C

Axiom:

```text
safe
→ checked
→ compiler proves
→ check disappears
```

C:

```text
unchecked
→ programmer responsible
```

Axiom không hy sinh safety chỉ để có performance.

---

# 47. Escape analysis

Compiler theo dõi:

```text
value
↓
does it escape?
```

Ví dụ:

```axiom
fn distance() -> f32 {
    let p = Point(...)
    return p.x * p.x + p.y * p.y
}
```

`p` không escape.

Compiler có thể:

```text
Point memory
↓
scalar replacement
↓
x register
y register
```

Không allocation.

---

# 48. View escape

```axiom
let v = view(x)
return v
```

Compiler kiểm tra provenance.

Nếu x local:

```text
ERROR
```

Nếu x là input:

```text
potentially valid
```

---

# 49. Storage relocation

Đây là phần liên quan trực tiếp tới `Vec`.

```axiom
let v = view(buffer)
buffer.push(x)
```

Nếu push có thể relocate:

```text
MAY_RELOCATE
```

và `v` active:

```text
ERROR
```

---

# 50. `reserve`

Người dùng có thể:

```axiom
buffer.reserve(100)
let v = view(buffer)
```

Sau đó các operation không relocate được có thể hợp lệ.

Nhưng compiler/library phải phân biệt:

```text
MAY_RELOCATE
NO_RELOCATE
```

---

# 51. Đây không phải lifetime annotation

Programmer không viết:

```text
'a
```

Compiler tự biết:

```text
v depends on buffer storage
```

và chỉ chặn operation có thể phá provenance.

---

# 52. Pointer provenance

Axiom cần khái niệm nội bộ:

```text
AllocationIdentity
```

Ví dụ:

```text
Allocation #42
```

View:

```text
provenance = #42
region = [0,100)
```

Nếu allocation bị deallocated:

```text
#42 → DEAD
```

mọi view:

```text
→ INVALID
```

Compiler không cần runtime tracking trong safe code.

---

# 53. Raw pointers thì sao?

Raw pointer có thể escape compiler proof.

Ví dụ:

```axiom
unsafe {
    let p = raw_ptr(x)
    external_store(p)
}
```

Compiler coi:

```text
x MAY_ESCAPE
```

tùy effect contract.

---

# 54. No hidden alias checks

Đây là mục tiêu rất quan trọng.

Axiom không được biến:

```axiom
a[i]
```

thành runtime:

```text
check_owner_id
check_refcount
check_alias
check_lifetime
```

Safe ownership checking phải xảy ra compile-time.

Runtime chỉ còn những check semantic mà compiler không thể chứng minh:

```text
bounds
overflow
division zero
```

nếu profile yêu cầu.

---

# 55. Memory model tổng thể

Tôi đề xuất chốt thành:

```text
             AXIOM MEMORY
                  │
       ┌──────────┴──────────┐
       │                     │
   SAFE MEMORY            UNSAFE MEMORY
       │                     │
  Value / Place          Raw Pointer
  View / MutView         Address arithmetic
  Ownership              Reinterpretation
  Region                 Volatile
  Capability             MMIO / FFI
       │                     │
       └──────────┬──────────┘
                  ▼
             MIR MEMORY
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
    Region      Effect     Provenance
       │          │          │
       └──────────┼──────────┘
                  ▼
             OPTIMIZER
                  │
       Alias / Escape / SROA
       Vectorization / DCE
                  │
                  ▼
             MACHINE CODE
```

---

# 56. Memory access invariants

Tôi đề xuất thêm bộ invariant chính thức:

### AMA-01
Safe code cannot perform invalid memory access.

### AMA-02
Safe mutable accesses cannot overlap conflicting accesses.

### AMA-03
Read-only overlapping views are allowed.

### AMA-04
Disjoint mutable regions may be accessed independently.

### AMA-05
Region identity is semantic and not necessarily a physical address range.

### AMA-06
View provenance cannot outlive its source storage.

### AMA-07
Raw pointers are not ownership guarantees.

### AMA-08
Unsafe operations do not disable type checking.

### AMA-09
Unsafe memory operations are explicit.

### AMA-10
Bounds safety is a semantic guarantee in safe code.

### AMA-11
Bounds checks may be eliminated when proven unnecessary.

### AMA-12
Volatile is not synchronization.

### AMA-13
Atomic operations require explicit memory ordering.

### AMA-14
External/unknown memory effects are conservatively modeled.

### AMA-15
Compiler-known disjointness may be used for optimization.

### AMA-16
Programmer-written `restrict` is not required for ordinary safe code.

### AMA-17
Allocation identity is distinct from raw address identity.

### AMA-18
Relocation invalidates dependent views unless stability is guaranteed.

### AMA-19
Exposing an address makes storage identity potentially observable.

### AMA-20
No hidden runtime alias/lifetime checks are required for safe memory access.

---

# 57. Và đây là câu trả lời cho câu hỏi “flat memory có nhanh hơn không?”

**Không, bản thân flat virtual address space không làm chương trình nhanh hơn.**

Nó chỉ cho machine một address model đơn giản.

Performance thực tế phụ thuộc nhiều hơn vào:

```text
1. cache locality
2. allocation frequency
3. pointer chasing
4. branch predictability
5. alias analysis
6. vectorization
7. data layout
8. synchronization
9. fragmentation
10. compiler optimization
```

Vì vậy hướng Axiom hiện tại tốt hơn việc cố xây “flat memory model” như một tính năng ngôn ngữ.

Axiom nên:

```text
Flat virtual address space
+
Value semantics
+
Region/capability analysis
+
Compiler-controlled layout
+
Allocation strategy freedom
+
Aggressive optimizer
```

thay vì:

```text
mọi object = pointer
```

---

## Một hệ quả rất đáng chú ý

Với thiết kế hiện tại, Axiom **không cần một Borrow Checker kiểu Rust**.

Nó có:

```text
Ownership
+
Initialization
+
Place
+
Region
+
Capability
+
Effect
+
Provenance
+
Concurrency
```

và verifier kết hợp chúng.

Do đó programmer viết:

```axiom
fn transform(
    dst: mut_view<f32>,
    src: view<f32>
) {
    ...
}
```

thay vì phải mô tả lifetime/borrow relationship.

Compiler vẫn có đủ thông tin để sinh code tối ưu.

---

### Bước kế tiếp tôi đề xuất

Giờ phần **semantic core gần như đã đủ xương sống**. Tôi sẽ chuyển sang một thứ rất thực dụng:

# `AXIOM COLLECTION / STRING / ITERATOR / ERROR / RESOURCE API v0.1`

Tập trung vào:

```text
Vec<T>
Array<T,N>
view<T>
String / Text / Bytes
Option<T>
Result<T,E>
Iterator
Range
Map / Set
File / Socket / Buffer
Allocator / Arena / Pool
```

và đặc biệt sẽ thiết kế sao cho **không biến Standard Library thành một runtime khổng lồ**, đồng thời các abstraction như `Vec`, `String`, `Iterator` có thể compile xuống code gần như viết tay bằng C.