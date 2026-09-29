# BOOTSTRAP-422 — MEMORY LAYOUT, DATA REPRESENTATION & TYPE ABI

Ta tiếp tục **BOOTSTRAP-422**. Task này đặc biệt quan trọng với hướng Axiom mà ta đã thống nhất: **không dựa vào GC, không bắt buộc borrow checker, hạn chế pointer/reference complexity**, nhưng vẫn phải có memory model đủ chặt để compiler tối ưu mạnh và FFI/native ABI chính xác.

---

## 422.1 — Nguyên tắc nền tảng

Axiom phân biệt rõ 4 khái niệm:

```text
Language Type
      ↓
Type Layout
      ↓
Memory Representation
      ↓
ABI Representation
```

Ví dụ:

```text
i32
```

có:

```text
semantic type = i32
size          = 4
alignment     = 4
representation = 32-bit two's complement
ABI class     = INTEGER
```

Không được trộn các tầng này thành một khái niệm duy nhất.

---

# 422.2 — Target Data Model

Mỗi target có:

```text
DataModel {
    pointer_size
    pointer_alignment

    usize_size
    isize_size

    wchar_size?
    max_align

    endianness
}
```

Ví dụ phổ biến:

```text
x86-64:
    pointer = 64-bit
    usize   = 64-bit
    isize   = 64-bit
```

AArch64 cũng có thể dùng mô hình tương tự.

Axiom **không giả định mọi target đều 64-bit**.

---

# 422.3 — Integer representation

Axiom integer:

```text
i8
i16
i32
i64
i128

u8
u16
u32
u64
u128
```

được biểu diễn bằng binary integer tương ứng.

Signed integer sử dụng:

```text
two's complement
```

Điều này phải là language guarantee, không phụ thuộc compiler/CPU.

---

# 422.4 — Integer overflow

Axiom cần phân biệt:

```text
checked arithmetic
wrapping arithmetic
saturating arithmetic
```

Ví dụ conceptual:

```text
a + b
```

theo context/compiler mode có thể:

```text
checked
```

hoặc explicit:

```text
wrapping_add(a, b)
saturating_add(a, b)
```

Không được để overflow behavior phụ thuộc optimization level.

---

# 422.5 — Native integer size

Không có:

```text
int
```

với kích thước compiler tùy ý.

Axiom ưu tiên:

```text
i32
i64
usize
isize
```

`usize/isize` phụ thuộc pointer width.

Điều này giúp FFI rõ ràng.

---

# 422.6 — Floating-point

Core:

```text
f16
f32
f64
```

và có thể:

```text
f128
```

khi target/compiler hỗ trợ.

Representation của `f32/f64` phải tương thích IEEE-754 ở mức binary representation.

Compiler không được tự ý thay đổi object representation chỉ vì optimization.

---

# 422.7 — Float semantic versus representation

Axiom phân biệt:

```text
numeric semantics
```

với:

```text
bit representation
```

Do đó cần primitive operations:

```text
bitcast<T>()
```

cho phép chuyển interpretation mà không thay đổi bit pattern, khi hai loại có representation tương thích.

---

# 422.8 — Bool representation

Source:

```text
bool
```

semantic chỉ có:

```text
false
true
```

Memory representation mặc định:

```text
1 byte
```

với:

```text
0 = false
1 = true
```

Compiler không được để các byte khác `0/1` trở thành các giá trị bool hợp lệ trong semantic model.

Khi đọc memory không hợp lệ qua unsafe/raw mechanism, behavior phải được quy định riêng.

---

# 422.9 — Character

Axiom không nên dùng một `char` mơ hồ giống nhiều ngôn ngữ cũ.

Ta tách:

```text
u8
Unicode scalar value
UTF-8 sequence
```

Một Unicode scalar value có representation:

```text
char
```

nhưng encoding khi lưu text là:

```text
UTF-8
```

---

# 422.10 — UTF-8 mặc định

String/text của Axiom:

```text
UTF-8 by default
```

không dùng:

```text
UTF-16
UTF-32
```

làm default memory representation.

Các encoding khác chỉ xuất hiện khi API yêu cầu.

Điều này phù hợp với mục tiêu Axiom **UTF-8 native**.

---

# 422.11 — String representation

Không nên biến `string` thành một object GC-managed.

Axiom phân biệt:

```text
String
StringSlice
CString
```

Conceptual:

```text
StringSlice {
    ptr
    len
}
```

`len` tính bằng **byte**, không phải Unicode code point.

Ví dụ:

```text
"Việt"
```

có:

```text
len = UTF-8 byte count
```

không phải số ký tự hiển thị.

---

# 422.12 — Owned String

Một `String` sở hữu vùng memory của nó:

```text
String {
    ptr
    len
    capacity
}
```

Conceptual representation:

```text
┌──────┬─────┬──────────┐
│ ptr  │ len │ capacity │
└──────┴─────┴──────────┘
            │
            ▼
       UTF-8 bytes
```

Nhưng representation này là **library/runtime type**, không phải compiler intrinsic bắt buộc cho mọi text abstraction.

---

# 422.13 — Slice

Slice:

```text
[T]
```

hoặc syntax tương đương phải có representation:

```text
ptr + length
```

Không chứa capacity.

Ví dụ:

```text
slice = {
    ptr: *T
    len: usize
}
```

Do đó truyền slice qua ABI thường tương đương aggregate hai machine words, tùy target ABI.

---

# 422.14 — Array

Array:

```text
[T; N]
```

có layout contiguous:

```text
T T T T T ... T
```

với:

```text
size = N * sizeof(T)
```

nếu không overflow layout calculation.

Không có hidden header.

---

# 422.15 — Array alignment

Array alignment:

```text
align([T; N]) = align(T)
```

trừ các target-specific constraints đặc biệt.

Element `i`:

```text
offset = i * stride(T)
```

Trong layout thông thường:

```text
stride(T) = size(T)
```

nếu `size(T)` đã bao gồm trailing padding cần thiết.

---

# 422.16 — Struct layout

Struct mặc định sử dụng **field order ổn định**:

```text
struct S {
    a: u8
    b: u32
    c: u16
}
```

Compiler không được tự ý reorder:

```text
a
b
c
```

thành:

```text
b
c
a
```

chỉ để giảm padding.

Điều này giúp:

- predictable memory layout
- debugging
- FFI
- serialization
- low-level programming.

---

# 422.17 — Struct padding

Compiler được chèn padding giữa fields:

```text
struct S {
    a: u8
    b: u64
}
```

Conceptual:

```text
a
padding
padding
...
b
```

Padding không phải field semantic.

---

# 422.18 — Struct alignment

```text
align(S) = max(align(field_i))
```

với điều chỉnh theo representation attributes/target.

Total size phải được round lên multiple của struct alignment.

Do đó:

```text
sizeof(S)
```

luôn phù hợp khi tạo array:

```text
[S; N]
```

---

# 422.19 — Struct offset introspection

Compiler phải cung cấp compile-time information:

```text
sizeof(T)
alignof(T)
offsetof(T, field)
```

Ví dụ:

```text
const SIZE = sizeof(Point)
const XOFF = offsetof(Point, x)
```

Các giá trị phải được compiler evaluate.

---

# 422.20 — `@repr(C)`

Để FFI:

```text
@repr(C)
struct Point {
    x: f64
    y: f64
}
```

Compiler sử dụng C-compatible field layout và ABI representation.

`repr(C)` là guarantee explicit.

---

# 422.21 — Native representation

Default Axiom struct representation:

```text
@repr(Axiom)
```

Có thể được compiler tối ưu **nếu không có observable layout requirement**.

Nhưng vì Axiom hướng tới native/low-level programming, ta khóa một nguyên tắc:

> **Field order vẫn được giữ nguyên trong memory-visible representation.**

Compiler chỉ được thay đổi representation khi semantics cho phép và object không exposed qua layout-sensitive boundary.

---

# 422.22 — Layout attributes

Core representation attributes:

```text
@repr(Axiom)
@repr(C)
@repr(packed)
@repr(align(N))
```

Không đưa hàng chục biến thể vào core.

Compiler có thể bổ sung target-specific representation attributes sau này.

---

# 422.23 — Packed structs

```text
@repr(packed)
struct Header {
    tag: u8
    size: u32
}
```

có thể loại bỏ padding.

Nhưng:

```text
packed field access
```

có thể tạo unaligned load/store.

Backend phải tự chọn:

```text
byte loads
unaligned instruction
multiple loads
```

tùy ISA.

---

# 422.24 — Packed access safety

Compiler không được giả định mọi CPU cho phép unaligned access hiệu quả hoặc an toàn.

Vì vậy packed access được xem là:

```text
layout feature
```

chứ không phải:

```text
performance optimization
```

---

# 422.25 — Explicit alignment

```text
@repr(align(64))
struct CacheLine {
    ...
}
```

đảm bảo alignment tối thiểu.

Compiler phải reject:

```text
align < natural required alignment
```

nếu representation không cho phép.

---

# 422.26 — Enum representation

Axiom enum:

```text
enum Color {
    Red
    Green
    Blue
}
```

có logical variants.

Compiler có thể biểu diễn:

```text
tag
```

bằng integer phù hợp.

Ví dụ:

```text
0 = Red
1 = Green
2 = Blue
```

Nhưng **tag size là layout decision**, không mặc định luôn `i32`.

---

# 422.27 — Tagged union

```text
enum Value {
    Integer(i64)
    Float(f64)
    Text(String)
}
```

conceptual layout:

```text
┌──────────┬──────────────────┐
│   tag    │ payload          │
└──────────┴──────────────────┘
```

Payload phải đủ lớn cho variant lớn nhất và phù hợp alignment.

---

# 422.28 — Niche optimization

Compiler có thể tối ưu representation:

```text
Option<Pointer>
```

thành:

```text
null = None
non-null = Some(ptr)
```

nếu type có invalid/niche representation hợp lệ.

Nhưng:

> Niche optimization là compiler optimization, không phải guarantee mặc định của source language.

Ngoại lệ chỉ khi specification explicitly cam kết representation.

---

# 422.29 — Nullable pointer

Axiom có thể biểu diễn:

```text
*T
```

với nullability semantics được xác định riêng.

Nhưng ta không cần tạo một hệ thống reference type phức tạp chỉ để biểu diễn optional pointer.

Ví dụ:

```text
*T?
```

có thể là nullable pointer nếu syntax cuối cùng của type system chọn mô hình này.

Điểm quan trọng là representation:

```text
pointer-sized
```

và null phải được xác định.

---

# 422.30 — Pointer representation

Raw pointer:

```text
*T
```

có:

```text
size = pointer_size
alignment = pointer_alignment
```

Pointer value có thể:

```text
null
valid address
```

và các trạng thái đặc biệt tùy target.

Axiom không giả định mọi pointer arithmetic đều hợp lệ.

---

# 422.31 — Pointer arithmetic

Pointer arithmetic chỉ được phép theo memory-object semantics.

Ví dụ:

```text
p + i
```

hợp lệ khi `p` trỏ vào một object/array thích hợp.

Không coi toàn bộ virtual address space là một giant array.

Điều này cho phép compiler vẫn thực hiện:

- bounds reasoning
- alias analysis
- optimization

mà không cần borrow checker.

---

# 422.32 — Reference model

Để tránh complexity mà ta đã thảo luận trước đây, Axiom **không cần một hệ thống reference type độc lập phức tạp trong core**.

Có thể có:

```text
*T
```

raw/address-bearing pointer

và:

```text
&T
```

nếu sau này cần semantic reference abstraction.

Nhưng `&T` không nên trở thành cơ chế quản lý lifetime bắt buộc toàn ngôn ngữ.

---

# 422.33 — Ownership không nằm trong ABI

Nếu Axiom có ownership/resource conventions ở language/library level, chúng không được xuất hiện trong native representation trừ khi semantics yêu cầu.

Ví dụ:

```text
String
```

không mang:

```text
GC header
reference count
runtime type ID
```

một cách mặc định.

---

# 422.34 — Không có GC header mặc định

Object memory của Axiom không tự động chứa:

```text
GC metadata
object header
type pointer
mark bit
```

trừ khi type/runtime cụ thể yêu cầu.

Do đó:

```text
struct Point
```

có thể thực sự chỉ là:

```text
x
y
```

trong memory.

Đây là invariant quan trọng cho mục tiêu native performance.

---

# 422.35 — Dynamic allocation

Heap allocation không phải language primitive bắt buộc.

Library/runtime có thể cung cấp:

```text
alloc
free
realloc
```

Compiler chỉ cần biết các intrinsic/ABI boundary khi optimization hoặc lowering yêu cầu.

Điều này cho phép:

```text
freestanding
embedded
kernel
custom allocator
```

---

# 422.36 — Allocator model

Axiom không khóa một allocator duy nhất.

Có thể có:

```text
SystemAllocator
Arena
Pool
StackAllocator
CustomAllocator
```

Compiler không cần biết implementation của allocator.

Một API generic có thể nhận allocator abstraction nếu library cần.

---

# 422.37 — Memory address space

Target có thể có:

```text
DEFAULT
STACK
HEAP
TLS
MMIO
CODE
CONSTANT
```

nhưng semantic core không nên biến chúng thành các pointer type khác nhau.

Address-space attributes chỉ cần khi target/API yêu cầu.

---

# 422.38 — Volatile memory

Axiom phải có:

```text
volatile_load
volatile_store
```

hoặc intrinsic tương đương.

Compiler không được:

```text
remove
merge
reorder
```

volatile accesses theo các rule mà volatile semantics cấm.

Đây là yêu cầu cho:

- MMIO
- device drivers
- embedded
- OS code.

---

# 422.39 — Atomic representation

Atomic types phải có alignment/size phù hợp target:

```text
AtomicU8
AtomicU16
AtomicU32
AtomicU64
```

hoặc generic:

```text
atomic<T>
```

nếu `T` đáp ứng target requirements.

Atomicity không được suy ra chỉ từ kích thước type.

---

# 422.40 — Memory ordering

Representation task chỉ khóa representation.

Memory ordering thuộc concurrency/memory model, nhưng ABI cần biết kích thước/alignment của atomic operations.

Các ordering:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

sẽ được khóa ở task memory/concurrency tương ứng.

---

# 422.41 — Endianness

Axiom source semantics không phụ thuộc endian.

Target descriptor:

```text
endianness = little
endianness = big
```

Memory layout của integer:

```text
little endian
```

hoặc:

```text
big endian
```

theo target.

Binary serialization không được giả định native endian nếu format yêu cầu endian cố định.

---

# 422.42 — Explicit byte conversion

Axiom cần primitive/library APIs cho:

```text
to_le_bytes
to_be_bytes
from_le_bytes
from_be_bytes
```

Nhờ đó code serialization không phụ thuộc CPU endian.

---

# 422.43 — Zero-sized types

Axiom có thể có zero-sized types:

```text
struct Marker {}
```

Semantic size:

```text
0
```

Nhưng ABI representation phải được target ABI classifier xử lý riêng.

Trong array:

```text
[Marker; N]
```

không nhất thiết chiếm `N` bytes.

Compiler không được tạo memory access thực sự cho zero-sized value nếu không cần.

---

# 422.44 — Empty struct

Empty struct:

```text
struct Empty {}
```

có thể là zero-sized.

Nhưng:

```text
@repr(C)
```

FFI compatibility phải tuân theo target C ABI rules.

Axiom không tự tuyên bố rằng mọi empty struct tương thích C.

---

# 422.45 — SIMD/vector layout

Vector:

```text
vec4<f32>
```

có:

```text
size
alignment
lane count
element type
```

Ví dụ conceptual:

```text
f32 f32 f32 f32
```

Memory contiguous.

ABI classification được 421 xử lý.

---

# 422.46 — Matrix layout

Matrix không nên là primitive ABI đặc biệt.

Ví dụ:

```text
matrix<f32, 4, 4>
```

được lower thành aggregate/vector/array representation.

Library có thể quy định:

```text
row-major
column-major
```

cho semantic API.

Không để compiler tự chọn.

---

# 422.47 — String literal representation

String literal:

```text
"hello"
```

được đặt trong read-only data:

```text
.rodata
```

hoặc target-equivalent.

Compiler tạo:

```text
pointer + length
```

nếu expression yêu cầu string slice.

Null terminator chỉ được thêm nếu representation/API yêu cầu.

---

# 422.48 — C string

C string phải là abstraction riêng:

```text
CString
```

hoặc explicit conversion.

Compiler không được giả định:

```text
String == NUL-terminated C string
```

Điều này tránh mất byte `0` semantics và cho phép UTF-8 strings chứa NUL.

---

# 422.49 — Function representation

Function itself không phải data object thông thường.

Function pointer:

```text
fn(...) -> ...
```

có target-defined representation.

Không được assume:

```text
function pointer == data pointer
```

trên mọi target.

---

# 422.50 — Fat pointers

Slice/interface/trait-object-like abstractions có thể cần:

```text
pointer + metadata
```

Nhưng core phải phân biệt:

```text
thin pointer
fat pointer
```

để backend và ABI classifier biết kích thước chính xác.

---

# 422.51 — Dynamic interface object

Nếu Axiom sau này có interface/trait object:

```text
dyn Shape
```

representation có thể:

```text
data_ptr
vtable_ptr
```

nhưng **đây không phải representation của ordinary struct**.

Vtable là compiler-generated data.

---

# 422.52 — Vtable layout

Nếu dynamic dispatch được bật, vtable phải có specification riêng:

```text
drop/destructor?
size
alignment
method pointers
metadata
```

Không đưa vtable vào mọi struct.

Điều này giữ struct-only design nhẹ.

---

# 422.53 — Type metadata

Axiom không mặc định lưu runtime type information.

Không có:

```text
RTTI pointer
type ID
class pointer
```

trong mỗi object.

Nếu reflection/runtime metadata được yêu cầu, compiler tạo metadata **chỉ khi feature được sử dụng**.

---

# 422.54 — Compile-time type information

Ngược lại, compiler phải có type metadata đầy đủ:

```text
TypeInfo {
    kind
    size
    alignment
    layout
    fields
    variants
}
```

nhưng thông tin này tồn tại trong compiler, không nhất thiết trong executable.

---

# 422.55 — Binary serialization boundary

Axiom phải phân biệt:

```text
in-memory representation
```

và:

```text
wire representation
```

Không được mặc định:

```text
write_bytes(&struct)
```

là portable serialization.

Nếu cần binary serialization:

```text
Serialize
Deserialize
```

phải định nghĩa endian/version/schema.

---

# 422.56 — `bitcast`

`bitcast<T>` chỉ hợp lệ khi:

```text
sizeof(Source) == sizeof(Target)
```

và alignment/representation rules cho phép.

Ví dụ:

```text
f32 → u32
```

là candidate hợp lệ.

Nhưng:

```text
struct → u64
```

chỉ hợp lệ nếu size/layout thỏa điều kiện.

---

# 422.57 — Transmute-like operation

Không nên đưa một `transmute<T>()` quá quyền lực vào safe language core.

Nếu cần:

```text
unsafe bit reinterpretation
```

thì đó là low-level escape hatch.

Mục tiêu:

```text
simple default
powerful escape hatch
```

thay vì làm mọi operation trở nên unsafe.

---

# 422.58 — Alias semantics

Đây là điểm quan trọng để đạt hiệu năng mà **không cần borrow checker**.

Compiler phải có alias information ở IR:

```text
MemoryAccess {
    address
    size
    alignment
    alias_class
}
```

Compiler có thể biết:

```text
noalias
readonly
writeonly
```

khi chứng minh được.

Nhưng source programmer không bắt buộc phải annotate mọi pointer.

---

# 422.59 — No implicit alias guarantee

Axiom không tuyên bố:

```text
*p
*q
```

luôn không alias.

Nếu có khả năng alias:

```text
compiler must assume alias
```

trừ khi có:

- type semantics
- compiler proof
- explicit annotation
- optimization contract

cho phép mạnh hơn.

---

# 422.60 — `restrict`-like optimization

Có thể cung cấp:

```text
@noalias
```

ở low-level boundary.

Nhưng đây là **optimization contract**, không phải mặc định.

Ví dụ:

```text
@noalias
fn copy(dst: *u8, src: *u8, n: usize)
```

chỉ hợp lệ nếu caller đảm bảo contract.

Compiler không được tự thêm `noalias` nếu không chứng minh được.

---

# 422.61 — Memory lifetime

Memory lifetime không được gắn cứng vào pointer type.

Có ba nguồn lifetime:

```text
stack scope
explicit allocation
owner/resource abstraction
```

Compiler có thể tối ưu allocation khi chứng minh object không escape.

Ví dụ:

```text
allocate
 ↓
use
 ↓
free
```

có thể được:

```text
stack/promoted
```

nếu semantics vẫn đúng.

---

# 422.62 — Escape analysis

Compiler có thể thực hiện:

```text
EscapeAnalysis
```

để xác định object có:

```text
escape function
escape thread
escape module
```

hay không.

Điều này tạo optimization mà không cần GC.

---

# 422.63 — Stack promotion

Heap object không escape có thể được chuyển thành stack object:

```text
heap allocation
      ↓
escape analysis
      ↓
stack allocation
```

hoặc thậm chí register/scalar replacement.

Đây là optimization, không thay đổi source semantics.

---

# 422.64 — Scalar replacement

Struct:

```text
Point { x, y }
```

có thể không tồn tại thực sự trong memory.

Compiler có thể:

```text
Point
 ↓
x register
y register
```

nếu không có observable address.

Điều này rất quan trọng với mục tiêu hiệu năng.

---

# 422.65 — Address-taking

Nếu code:

```text
&p
```

lấy địa chỉ object, compiler phải xem object là memory-observable trong phạm vi cần thiết.

Tuy nhiên escape analysis vẫn có thể chứng minh address không escape.

---

# 422.66 — Memory model principle

Axiom memory model không dựa trên:

```text
GC
```

và không yêu cầu:

```text
borrow checker
```

làm điều kiện compile.

Thay vào đó:

```text
explicit memory ownership conventions
+
well-defined pointer semantics
+
compiler alias analysis
+
optional contracts
+
runtime/library allocators
```

được dùng để đạt safety/performance balance.

---

# 422.67 — Safety tiers

Axiom có thể phân tầng:

```text
safe
unsafe
intrinsic
```

Normal code:

```text
safe
```

Low-level:

```text
unsafe {
    ...
}
```

Compiler internals/intrinsics:

```text
intrinsic
```

Nhưng **unsafe không có nghĩa compiler được phép tạo machine code tùy ý**.

Undefined behavior vẫn phải được specification định nghĩa.

---

# 422.68 — Memory UB

Các hành vi như:

```text
use-after-free
out-of-bounds
invalid alignment
invalid pointer dereference
data race
```

phải có semantic classification.

Compiler được phép tối ưu dựa trên assumption rằng chương trình **không thực hiện undefined behavior**, giống mô hình native systems languages.

---

# 422.69 — Bounds

Array/slice semantics phải phân biệt:

```text
compile-time known bound
runtime bound
unchecked raw access
```

Normal indexing có thể:

```text
bounds check
```

nếu language semantics yêu cầu.

Unchecked access là explicit low-level operation.

Compiler có thể eliminate check nếu chứng minh index hợp lệ.

---

# 422.70 — Bounds-check elimination

Ví dụ:

```text
for i in 0..len(a) {
    x = a[i]
}
```

compiler nên có khả năng chứng minh:

```text
0 <= i < len(a)
```

và loại bỏ repeated bounds checks.

Không cần programmer dùng unsafe chỉ để đạt hiệu năng.

---

# 422.71 — Memory layout query

Compile-time API:

```text
sizeof(T)
alignof(T)
offsetof(T, field)
strideof(T)
```

`strideof` hữu ích cho:

```text
arrays
FFI
SIMD
serialization
custom allocators
```

---

# 422.72 — Layout stability

Default Axiom layout:

```text
field order stable
alignment deterministic
size deterministic
```

Nhưng compiler vẫn có thể thực hiện scalar replacement/register allocation khi object không exposed.

Điều này đạt được cả:

```text
predictable layout
```

và:

```text
aggressive optimization
```

---

# 422.73 — FFI layout contract

FFI type phải thỏa:

```text
known size
known alignment
known field offsets
known ABI classification
```

Generic/dynamic language abstractions không tự động FFI-safe.

---

# 422.74 — Cross-target layout

Cùng:

```text
struct S
```

không nhất thiết có cùng:

```text
size
alignment
```

trên mọi target nếu type chứa:

```text
usize
pointer
platform-dependent ABI type
```

Ví dụ:

```text
struct S {
    p: *u8
    n: usize
}
```

có layout phụ thuộc pointer width.

Đây là expected behavior.

---

# 422.75 — Explicit fixed-width FFI

Nếu layout cần portable:

```text
i32
u32
i64
u64
```

thay vì:

```text
int
long
usize
```

trừ khi API thực sự yêu cầu native-size type.

---

# 422.76 — Data layout descriptor

Compiler target cần:

```text
DataLayout {
    endian
    pointer_layout
    integer_layout
    float_layout
    vector_layout
    aggregate_layout
    alignment_rules
}
```

Đây là counterpart của:

```text
ABI Descriptor
```

421.

---

# 422.77 — DataLayout + ABI

Pipeline cuối:

```text
Type
 ├── DataLayout
 │      ↓
 │   memory representation
 │
 └── ABI
        ↓
     call representation
```

Hai hệ thống dùng chung:

```text
TypeLayout
```

nhưng không được đồng nhất.

---

# 422.78 — Representation optimization

Compiler có thể thực hiện:

```text
enum niche optimization
empty-field elimination
scalar replacement
register promotion
constant folding
dead-field elimination
```

chỉ khi representation không observable hoặc specification cho phép.

---

# 422.79 — Observable representation

Representation trở thành observable khi:

```text
@repr(C)
raw pointer access
offsetof
sizeof
FFI
volatile access
serialization primitive
```

Trong các trường hợp này compiler phải tôn trọng layout contract.

---

# 422.80 — Final memory architecture

Axiom memory representation lúc này:

```text
                    Axiom Type
                         │
                         ▼
                   Type Layout
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Memory Representation    ABI Classification
              │                     │
              ▼                     ▼
       Stack / Heap / Data      Register / Stack
              │                     │
              └──────────┬──────────┘
                         ▼
                   Machine IR
                         │
                         ▼
                 Machine Encoder
```

Điểm quan trọng nhất:

> **Memory layout được xác định rõ nhưng không buộc compiler phải materialize object trong memory.**

Một `struct` có layout 16 byte nhưng trong optimized machine code hoàn toàn có thể không tồn tại dưới dạng 16 byte memory object.

---

# 422.81 — Completion criteria

**BOOTSTRAP-422 chỉ được DONE khi compiler specification có:**

- primitive representation
- integer/float/bool representation
- UTF-8 representation
- pointer model
- slice/string model
- array layout
- struct layout
- padding/alignment
- enum/tagged union
- optional/niche representation
- vector layout
- atomic representation
- endian model
- `repr(C)`
- packed/explicit alignment
- FFI representation
- volatile access
- alias semantics
- lifetime model
- escape analysis boundary
- bounds semantics
- layout introspection
- cross-target DataLayout
- layout conformance tests.

**422 được khóa ở mức architecture/specification.**

---

# BOOTSTRAP-423 — MEMORY MANAGEMENT, OWNERSHIP, ALLOCATION & RESOURCE LIFETIME

Đây là task tiếp theo và là một trong những task quan trọng nhất đối với định hướng Axiom của chúng ta.

422 trả lời:

> **Object nằm trong memory và được biểu diễn thế nào?**

423 phải trả lời:

> **Ai chịu trách nhiệm tạo, sử dụng, di chuyển và giải phóng memory/resource đó — mà không cần GC và không ép toàn bộ Axiom vào borrow checker?**

Chuỗi 423 sẽ khóa:

```text
423.1   memory model goals
423.2   stack allocation
423.3   explicit heap allocation
423.4   allocator abstraction
423.5   ownership model
423.6   move semantics
423.7   copy semantics
423.8   clone semantics
423.9   destruction
423.10  deterministic resource release
423.11  scope cleanup
423.12  defer
423.13  RAII-like behavior
423.14  ownership without borrow checker
423.15  aliasing
423.16  mutable aliasing
423.17  shared access
423.18  unique ownership
423.19  reference counting as library feature
423.20  arenas
423.21  pools
423.22  custom allocators
423.23  allocation elision
423.24  escape analysis
423.25  stack promotion
423.26  lifetime analysis
423.27  resource types
423.28  file/socket/device ownership
423.29  thread ownership
423.30  send/share semantics
423.31  concurrency interaction
423.32  unsafe memory operations
423.33  use-after-free semantics
423.34  double-free semantics
423.35  dangling pointer semantics
423.36  allocation failure
423.37  OOM policy
423.38  zero-size allocation
423.39  realloc
423.40  alignment allocation
423.41  destructor ordering
423.42  panic/unwind cleanup
423.43  abort cleanup
423.44  FFI ownership
423.45  C malloc/free interoperability
423.46  ownership annotations
423.47  compiler diagnostics
423.48  optimizer assumptions
423.49  memory-management conformance tests
423.50  final Axiom memory-management contract
```

**BOOTSTRAP-423 là task kế tiếp trong chuỗi.**