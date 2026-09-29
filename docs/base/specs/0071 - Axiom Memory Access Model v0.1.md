Tiếp tục. Phần này nên **khóa Memory Access Model v0.1**, vì đây là ranh giới giữa mô hình an toàn của Axiom và khả năng làm những thứ rất thấp như kernel, driver, allocator, engine, MMIO.

# Axiom Memory Access Model v0.1

Nguyên tắc trung tâm:

> **Value ≠ Address ≠ Pointer ≠ View.**

Bốn thứ này phải tách biệt hoàn toàn.

```text
                 VALUE
                   │
              owned storage
                   │
              ┌────┴────┐
              │         │
            view      mut_view
              │         │
              └────┬────┘
                   │
             safe capability
                   │
                unsafe
                   ↓
             RAW POINTER
                   │
                   ↓
                ADDRESS
```

---

# 1. Value

Ví dụ:

```axiom
let x: i64 = 42;
```

Semantic:

```text
x = value 42
```

Không có nghĩa rằng programmer được phép hỏi:

```text
address_of(x)
```

trong safe code.

Compiler hoàn toàn có quyền đặt `x` vào:

```text
register
stack
memory
```

hoặc loại bỏ nó hoàn toàn.

---

# 2. `view<T>`

```axiom
let x = 42;
let v = view(x);
```

`v` không sở hữu `x`.

Nó là:

```text
READ capability
```

Conceptually:

```text
view<T>
    provenance → owner
    region
    READ
```

Nhưng những metadata này **không nhất thiết tồn tại runtime**.

---

# 3. `mut_view<T>`

```axiom
var x = 42;
let v = mut_view(x);
```

Semantic:

```text
WRITE capability
```

và quan trọng:

```text
mut_view<T> != Copy
```

dù representation vật lý có thể chỉ là pointer.

---

# 4. Raw pointer

Chỉ trong unsafe:

```axiom
unsafe {
    let p: *mut i32 = ...
}
```

Raw pointer là machine-level abstraction.

Nó có thể:

- null;
- dangling;
- misaligned;
- point outside allocation;
- alias bất hợp lệ;
- trỏ tới MMIO;
- trỏ tới foreign memory.

Compiler không được giả định raw pointer luôn safe.

---

# 5. Nhưng `unsafe` không biến mọi thứ thành “UB tự do”

Đây là điểm tôi đề nghị giữ rất mạnh.

```axiom
unsafe {
    ...
}
```

có nghĩa:

> Programmer chịu trách nhiệm cho các invariant mà compiler không thể chứng minh.

Nhưng compiler vẫn kiểm tra:

```text
syntax
type
ABI
calling convention
instruction legality
```

Không có chuyện:

```text
unsafe → tắt compiler
```

---

# 6. Có cần kiểu `addr` không?

Tôi nghiêng về **có**.

```text
addr
```

là integer-like representation của một machine address.

Nhưng:

```text
addr != usize
addr != *T
```

Ba semantic khác nhau.

```text
usize
    integer dùng cho kích thước/index

addr
    machine address value

*T
    typed raw pointer
```

---

# 7. Vì sao không dùng `usize` cho address?

Nếu:

```axiom
let p: usize = ...
```

thì compiler rất khó phân biệt:

```text
array length
index
file size
address
```

và optimizer mất semantic information.

Axiom nên giữ:

```text
Pointer ≠ Integer
```

---

# 8. Pointer → address

Unsafe:

```axiom
let a: addr = address_of(p);
```

hoặc:

```text
ptr.to_addr()
```

Việc này làm mất một phần provenance information.

Compiler phải coi:

```text
pointer → addr
```

là boundary.

---

# 9. Address → pointer

Ngược lại:

```axiom
let p: *mut T = addr.to_ptr<T>();
```

phải là unsafe.

Compiler không thể chứng minh:

```text
alignment
allocation
lifetime
type validity
```

của address.

---

# 10. Pointer arithmetic

Raw pointer có thể:

```axiom
unsafe {
    let q = p.add(4);
}
```

nhưng semantic phải định nghĩa rõ.

Tôi đề xuất:

```text
p.add(n)
```

là arithmetic theo **element size**:

```text
address(p) + n * sizeof(T)
```

chứ không phải byte offset.

Byte-level:

```text
p.byte_add(n)
```

explicit.

---

# 11. Pointer subtraction

```text
p - q
```

không nên là integer subtraction tùy tiện.

Chỉ có ý nghĩa khi:

```text
same allocation / compatible provenance
```

Nếu không, unsafe operation vẫn có thể tồn tại nhưng semantic phải được đánh dấu machine-dependent/unsafe.

---

# 12. Pointer provenance

Đây là một trong những phần quan trọng nhất.

Ví dụ:

```text
allocation A
address = 0x1000
```

sau đó convert:

```text
pointer → addr → pointer
```

Compiler có nên biết pointer mới vẫn thuộc A?

Tôi đề xuất:

### Provenance-preserving conversion

Nếu compiler biết conversion không làm mất provenance:

```text
*T → addr → *T
```

có thể giữ provenance trong một số explicit intrinsic/API.

### Provenance-erasing conversion

Nếu address được tạo từ arbitrary integer:

```text
42 → addr → *T
```

thì provenance:

```text
UNKNOWN
```

---

# 13. Tại sao provenance quan trọng?

Optimizer có thể giả định:

```text
view<T>
```

không tùy tiện alias với một allocation khác.

Nếu mọi pointer đều có thể magically trỏ vào mọi thứ mà không có semantics rõ ràng, alias analysis sẽ yếu đi rất nhiều.

Axiom cần:

```text
safe alias guarantees
```

nhưng vẫn cho phép:

```text
unsafe arbitrary machine access
```

---

# 14. Safe code

Safe code không được tạo raw pointer tùy ý.

Ví dụ:

```axiom
fn sum(a: view<i64>) -> i64 {
    ...
}
```

Compiler biết:

```text
a
 ↓
valid region
 ↓
read-only
```

Điều này cho phép tối ưu.

---

# 15. Unsafe pointer không phải view

Không cho:

```text
implicit *T → view<T>
```

Vì nếu làm vậy:

```text
dangling pointer
```

có thể biến thành safe capability mà compiler tưởng hợp lệ.

Phải có explicit operation:

```axiom
unsafe {
    let v = view_from_ptr(p, len);
}
```

và operation này phải chịu trách nhiệm chứng minh/assume preconditions.

---

# 16. `view_from_ptr`

Conceptually:

```text
unsafe fn view_from_ptr<T>(
    ptr: *const T,
    len: usize
) -> view<T>
```

Preconditions:

```text
ptr valid
alignment correct
allocation covers len * sizeof(T)
memory readable
lifetime sufficient
```

Compiler không tự chứng minh được.

Programmer chịu trách nhiệm.

---

# 17. Mutable view từ pointer

```text
unsafe fn mut_view_from_ptr<T>(
    ptr: *mut T,
    len: usize
) -> mut_view<T>
```

Preconditions còn mạnh hơn:

```text
memory writable
no conflicting aliases
exclusive access
valid lifetime
```

Đây là một trong những nơi `unsafe` tạo safe capability.

---

# 18. Một nguyên tắc cực kỳ quan trọng

> **Unsafe có thể tạo capability mà safe code sử dụng, nhưng capability sau khi tạo vẫn phải tuân theo verifier.**

Ví dụ:

```axiom
unsafe {
    let v = mut_view_from_ptr(p, 100);
}

safe_function(v);
```

Sau khi `v` tồn tại:

```text
ownership/capability verifier
```

vẫn theo dõi `v`.

`unsafe` không biến nó thành invisible.

---

# 19. Slice / view representation

`view<T>` với contiguous data conceptually:

```text
pointer + length
```

nhưng semantic:

```text
region
access capability
provenance
```

Compiler có thể lower:

```text
view<T>
```

thành:

```text
(ptr, len)
```

nếu cần.

Không có runtime lifetime field.

---

# 20. `view<T>` không nhất thiết contiguous?

Tôi đề xuất **có**:

```text
view<T>
    = contiguous sequence
```

Điều này giúp:

- indexing;
- vectorization;
- memcpy;
- SIMD;
- FFI;
- cache optimization.

Nếu cần non-contiguous abstraction:

```text
StrideView<T>
MatrixView<T>
Iterator
```

là library types.

---

# 21. `mut_view<T>`

Cũng contiguous:

```text
mut_view<T>
    = contiguous writable sequence
```

Điều này làm contract cực rõ.

---

# 22. Indexing

```axiom
v[i]
```

Safe code:

```text
bounds checked
```

Compiler có thể loại bounds check nếu chứng minh:

```text
0 <= i < len
```

Ví dụ:

```axiom
for i in 0..len {
    sum += v[i];
}
```

MIR có thể prove bounds.

Machine code:

```text
load
```

không cần branch mỗi iteration.

---

# 23. Unsafe unchecked indexing

Có thể có:

```axiom
unsafe {
    v.get_unchecked(i)
}
```

Nhưng tôi nghiêng về API/library hơn là thêm syntax:

```text
unchecked_index(v, i)
```

Compiler intrinsic có thể được sử dụng.

---

# 24. Null pointer

Safe Axiom:

```text
null không phải value của view<T>
```

Không có:

```text
view<T> = null
```

Raw pointer:

```text
*const T
```

có thể null trong unsafe/FFI.

---

# 25. Optional pointer

Nếu API cần nullable pointer:

```text
Option<*const T>
```

hoặc FFI-specific nullable pointer.

Compiler có thể niche-optimize.

Không cần `null` language-wide.

---

# 26. Alignment

Mỗi type có:

```text
size_of(T)
align_of(T)
```

Compiler biết statically nếu T concrete.

Raw pointer dereference yêu cầu:

```text
address % align_of(T) == 0
```

Nếu không:

```text
unsafe violation
```

---

# 27. Unaligned access

System programming cần unaligned access.

Có thể:

```text
read_unaligned<T>(ptr)
write_unaligned<T>(ptr, value)
```

là intrinsic/library.

Không cần phá alignment semantics chung.

---

# 28. Packed structs

```axiom
@repr(packed)
struct Header {
    ...
}
```

là system/unsafe representation.

Compiler không được tạo:

```text
load aligned
```

nếu field có thể misaligned.

Access có thể tự động lower thành byte operations hoặc unaligned load.

---

# 29. Volatile

Cần:

```text
volatile_load
volatile_store
```

cho:

- MMIO;
- device registers;
- compiler-visible hardware state.

Nhưng:

> **volatile không phải atomic.**

Volatile chỉ nói:

```text
compiler không được loại bỏ/gộp tùy tiện access
```

Nó không tạo thread synchronization.

---

# 30. Atomic

Atomic:

```text
atomic_load
atomic_store
atomic_rmw
compare_exchange
```

có memory ordering:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Đây đã được khóa trong concurrency model.

---

# 31. MMIO

Ví dụ conceptual:

```axiom
struct RegisterBlock {
    control: u32
    status: u32
}
```

System code:

```text
volatile pointer
```

Compiler phải hỗ trợ:

```text
volatile load/store
```

nhưng không cần hiểu “device”.

Platform library có thể cung cấp:

```text
Mmio<T>
```

---

# 32. Memory-mapped region

Có thể có API:

```text
unsafe map_mmio(addr, size)
```

trả:

```text
mut_view<u8>
```

hoặc một typed wrapper.

Điều này rất phù hợp Axiom:

```text
OS-specific API
        ↓
unsafe boundary
        ↓
safe capability
```

---

# 33. FFI pointer

C:

```c
void* data;
size_t len;
```

Axiom có thể map thành:

```text
*mut u8
usize
```

ở ABI boundary.

Không nên tự động map thành:

```text
mut_view<u8>
```

vì C pointer không đảm bảo provenance/lifetime.

Wrapper:

```text
extern function
      ↓
unsafe validation
      ↓
mut_view
```

---

# 34. `repr(C)`

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: f64
    y: f64
}
```

cam kết:

```text
C-compatible layout
```

Bao gồm:

- field order;
- alignment;
- padding;
- representation;
- ABI-compatible aggregate rules.

---

# 35. Default struct layout

Không nên mặc định C layout.

```axiom
struct Point {
    x: f64
    y: f64
}
```

compiler có thể:

```text
reorder
pack
scalarize
```

nếu observable semantics không thay đổi.

Đây rất quan trọng cho optimization.

---

# 36. Stable address

Một struct value:

```axiom
var p = Point{...};
```

không có guarantee:

```text
address(p) stable
```

trừ khi storage abstraction yêu cầu.

Ví dụ:

```text
Box<Point>
```

có stable identity/address theo contract.

---

# 37. Đây là lý do `Box` rất quan trọng

```text
Point
```

là value.

```text
Box<Point>
```

là owning stable-storage abstraction.

```text
view<Point>
```

là temporary/non-owning capability.

```text
*mut Point
```

là unsafe machine pointer.

Ba semantic levels rõ ràng.

---

# 38. Pointer lifetime

Raw pointer:

```text
p: *mut T
```

không được compiler coi là ownership.

Nếu:

```axiom
let p = address_of(box);
drop(box);
```

thì:

```text
p
```

có thể dangling.

Trong unsafe code programmer chịu trách nhiệm.

Nhưng nếu cố chuyển `p` thành safe `view<T>` sau đó:

```text
unsafe {
    view_from_ptr(p, 1)
}
```

thì programmer đang chịu responsibility rằng allocation vẫn sống.

---

# 39. Safe view lifetime

Khác raw pointer:

```text
view<T>
```

luôn có provenance/lifetime obligation được verifier theo dõi.

Do đó:

```text
owner destroyed
```

trong khi view active:

```text
compile error
```

---

# 40. `view` return

Cho phép:

```axiom
fn first(x: view<Array<i64, 4>>) -> view<i64> {
    ...
}
```

nếu provenance bắt nguồn từ input.

Không cho:

```axiom
fn bad() -> view<i64> {
    var x = 10;
    view(x)
}
```

vì:

```text
x lifetime < returned view
```

---

# 41. `static` là exception hợp lệ

```axiom
static X: i64 = 10;

fn get() -> view<i64> {
    view(X)
}
```

hợp lệ vì:

```text
Static lifetime
```

---

# 42. Heap object

```axiom
fn make() -> Box<Data> {
    Box::new(...)
}
```

return ownership:

```text
caller owns Box
```

view từ Box:

```text
Box<Data>
    ↓
view<Data>
```

chỉ valid khi Box còn sống.

---

# 43. Region model

Tôi đề xuất mở rộng region semantics:

```text
Region =
    Local(LocalId)
    Field(Region, FieldId)
    ArraySlice(Region, start, len)
    Allocation(AllocationId)
    Static(SymbolId)
    External(ExternalId)
    Unknown
```

Relations:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

---

# 44. Alias analysis

Safe:

```axiom
fn foo(a: mut_view<A>, b: mut_view<B>)
```

Compiler cần chứng minh:

```text
region(a) ∩ region(b) = ∅
```

hoặc reject nếu không chứng minh được.

Đây là Axiom equivalent của alias safety nhưng không bắt programmer viết:

```text
'a
```

hay:

```text
&'a mut
```

---

# 45. Restrict-like semantics

Tôi **không nghĩ Axiom cần một keyword `restrict`** ở source v0.1.

Vì:

```text
mut_view<T>
```

đã cung cấp rất nhiều alias information.

Compiler có thể internally derive:

```text
exclusive write region
```

cho optimizer.

Nếu FFI cần C `restrict`, có thể có:

```text
@noalias
```

ở ABI/system boundary sau này.

---

# 46. Một ví dụ tối ưu rất quan trọng

```axiom
fn add(
    a: mut_view<f64>,
    b: view<f64>,
    n: usize
) {
    for i in 0..n {
        a[i] += b[i];
    }
}
```

Compiler biết:

```text
a = WRITE
b = READ
```

và verifier đã đảm bảo không conflict.

Optimizer có thể vectorize:

```text
load 4/8 floats
add
store
```

mà không cần programmer viết `restrict`.

---

# 47. Nhưng alias không phải lúc nào cũng disjoint

Ví dụ:

```axiom
let a = view(data);
let b = view(data);
```

READ + READ:

```text
OK
```

Compiler vẫn biết chúng alias.

Không được biến thành:

```text
assume disjoint
```

một cách sai.

---

# 48. Mutable field splitting

Ví dụ:

```axiom
struct Pair {
    a: i64
    b: i64
}
```

Có thể:

```text
mut_view(p.a)
mut_view(p.b)
```

cùng lúc nếu:

```text
Region(p.a) ∩ Region(p.b) = ∅
```

Đây là một điểm rất mạnh của region-based verifier.

---

# 49. Array slices

Nếu:

```text
a = mut_view(data[0..10])
b = mut_view(data[20..30])
```

compiler có thể chứng minh:

```text
DISJOINT
```

và cho phép concurrent/parallel access nếu các điều kiện Send/Share phù hợp.

---

# 50. Overlap

```text
a = mut_view(data[0..10])
b = mut_view(data[5..15])
```

→

```text
OVERLAPS
```

Hai mutable views:

```text
reject
```

Safe code.

---

# 51. Unknown regions

Nếu:

```text
extern "C" fn unknown(p: *mut u8);
```

compiler không biết function làm gì.

Effect:

```text
UNKNOWN
```

Alias:

```text
UNKNOWN
```

Optimizer phải conservative quanh call.

---

# 52. Nhưng explicit FFI contract có thể cải thiện

Sau này:

```text
extern "C" @reads(p)
extern "C" @writes(p)
extern "C" @noalias(...)
```

có thể cung cấp optimization metadata.

Không cần đưa vào v0.1 core.

---

# 53. Memory operations trong MIR

MIR semantic:

```text
LOAD
STORE
VIEW
VIEW_MUT
ALLOC
DEALLOC
```

Sau verification:

```text
ownership/view semantics
```

có thể dần bị erase.

Ví dụ:

```text
VIEW
```

có thể hoàn toàn biến mất.

---

# 54. Xuống LIR

LIR chỉ cần:

```text
LOAD
STORE
PTR_ADD
MEMCPY
MEMMOVE
MEMSET
```

và metadata alias/effect nếu optimizer cần.

Không còn:

```text
view
ownership
borrow
lifetime
```

như runtime concepts.

Đây là **Abstraction Erasure**.

---

# 55. Axiom không cần một “fat pointer” bắt buộc

`view<T>` conceptually có:

```text
pointer + length
```

nhưng compiler có thể:

```text
register pair
```

hoặc:

```text
pointer + statically-known length
```

hoặc eliminate length hoàn toàn.

Không có hidden reference count/lifetime metadata.

---

# 56. Một số primitive machine-level nên có

Tôi đề xuất system intrinsic tối thiểu:

```text
size_of<T>()
align_of<T>()

ptr_add<T>()
ptr_byte_add()
ptr_diff()

read<T>()
write<T>()

read_unaligned<T>()
write_unaligned<T>()

volatile_load<T>()
volatile_store<T>()

atomic_load()
atomic_store()
atomic_rmw()
compare_exchange()

memcpy()
memmove()
memset()
```

Nhưng nhiều cái có thể expose qua std/system library thay vì source-level syntax.

---

# 57. Memory safety boundary

Ta có thể mô hình hóa:

```text
SAFE
────────────────────────────
value
struct
array
Vec
view
mut_view
Box
Option
Result
────────────────────────────
UNSAFE
raw pointer
address
pointer arithmetic
arbitrary cast
MMIO
volatile
FFI raw memory
manual allocation
────────────────────────────
```

Điểm quan trọng:

> Unsafe không phải một “mode của toàn chương trình”. Nó là boundary cục bộ.

---

# 58. Memory invariants

### AMEM-01 — Value/Address Separation
Value không đồng nghĩa storage address.

### AMEM-02 — Pointer/Integer Separation
Pointer không phải integer.

### AMEM-03 — View Is Capability
View biểu diễn quyền truy cập, không phải ownership.

### AMEM-04 — Mutable View Is Exclusive
`mut_view` không được alias mutable capability chồng lấn.

### AMEM-05 — Provenance Preservation
Safe capability phải có provenance hợp lệ.

### AMEM-06 — Unsafe Pointer Boundary
Raw pointer chỉ xuất hiện trong unsafe/system/FFI contexts.

### AMEM-07 — No Implicit Pointer Dereference
Pointer không tự động biến thành safe memory access.

### AMEM-08 — Explicit Address Conversion
Pointer/address conversion phải explicit.

### AMEM-09 — Alignment
Typed access phải thỏa alignment.

### AMEM-10 — Volatile ≠ Atomic
Hai semantics hoàn toàn khác nhau.

### AMEM-11 — FFI Conservative
FFI không có contract được coi là unknown.

### AMEM-12 — View Lifetime
Safe view không được outlive provenance owner.

### AMEM-13 — Storage Identity Explicit
Stable address chỉ tồn tại khi storage abstraction yêu cầu.

### AMEM-14 — Safe Alias Knowledge
Compiler được phép tận dụng alias guarantees của safe capabilities.

### AMEM-15 — Unsafe Does Not Erase Types
Unsafe không vô hiệu hóa type checking.

---

# 59. Toàn bộ Memory Model lúc này

```text
                         AXIOM MEMORY
                              │
             ┌────────────────┴────────────────┐
             │                                 │
           VALUE                            STORAGE
             │                                 │
       ┌─────┴─────┐                ┌──────────┼──────────┐
       │           │                │          │          │
    Copyable     Owning          Local      Static     Dynamic
       │           │                │          │          │
       │       ┌───┴────┐          │          │         Box
       │       │        │          │          │         Vec
       │      Move     Drop        │          │         Arena
       │                          │          │         Pool
       └──────────────┬───────────┘          │
                      │                      │
                  Capability                 │
                 ┌────┴────┐                 │
                 │         │                 │
               view    mut_view              │
                 │         │                 │
                 └────┬────┘                 │
                      │                      │
                   unsafe                    │
                      ↓                      │
                 raw pointer                 │
                      │                      │
                    addr                     │
                      │                      │
               machine/FFI/MMIO              │
```

Điểm rất đáng chú ý là **raw pointer nằm ở dưới cùng**, chứ không phải nền tảng mà toàn bộ language model phải xoay quanh.

---

# 60. Và tôi nghĩ đây là một quyết định kiến trúc rất quan trọng

Axiom không nên cố biến mình thành:

> “Rust nhưng bỏ lifetime syntax.”

Mà nên trở thành một mô hình khác:

```text
Programmer:
    value
    ownership intent
    capability intent
    unsafe boundary

Compiler:
    regions
    provenance
    lifetime
    alias analysis
    escape analysis
    storage placement
    ABI
    machine representation
```

Tức là **compiler vẫn làm công việc khó**, nhưng programmer không phải viết lại proof của compiler bằng hàng loạt annotation.

---

## Bước tiếp theo

Sau Memory Model, phần còn thiếu rất lớn là **Object Representation + Layout + ABI Interop**.

Cần khóa:

```text
struct layout
enum layout
niche optimization
padding
alignment
bitfields?
packed
union?
transparent/newtype
repr(C)
repr(transparent)
endianness
serialization
FFI ABI
variadic functions
SIMD/vector ABI
calling convention
```

Đặc biệt có một câu hỏi cần quyết định trước khi đi tiếp:

> **Axiom có cần `union` và `bitfield` trong language core không, hay chỉ cần `struct + enum + raw byte operations + `repr(C)` là đủ?**

Đây là điểm ảnh hưởng trực tiếp đến khả năng viết **kernel/driver/FFI**, nhưng nếu đưa quá nhiều low-level constructs vào Core thì lại đi ngược mục tiêu “core mạnh nhưng không phình to”.