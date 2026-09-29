# BOOTSTRAP-108 — Axiom ABI Lowering & Physical Representation
**FROZEN / COMPLETED**

Đây là boundary cực kỳ quan trọng của Axiom:

> **Từ đây trở xuống, compiler bắt đầu quyết định giá trị semantic của Axiom sẽ xuất hiện như thế nào trong binary.**

Mục tiêu là:

- semantics của Axiom không phụ thuộc CPU;
- layout tối ưu mặc định;
- ABI native hiệu quả;
- FFI có contract rõ ràng;
- abstraction không tạo overhead bắt buộc;
- vẫn giữ `@repr(C)` để tương tác C;
- không biến representation detail thành burden cho programmer.

---

# 1. Vị trí chính thức

```text
Verified MIR
      ↓
Semantic Optimization
      ↓
OptIR
      ↓
━━━━━━━━━━━━━━━━━━━━
ABI / Representation Boundary
━━━━━━━━━━━━━━━━━━━━
      ↓
Representation Selection
      ↓
Layout
      ↓
ABI Classification
      ↓
Argument / Return Lowering
      ↓
Drop / Cleanup ABI
      ↓
FFI ABI
      ↓
ABI MIR
      ↓
Axiom LIR
      ↓
Target Lowering
```

Điểm quan trọng:

```text
Type
Representation
Layout
ABI
Machine instruction
```

là **5 khái niệm khác nhau**.

---

# 2. Type ≠ Representation

Ví dụ:

```axiom
struct Vec2 {
    x: f32,
    y: f32
}
```

Semantic type:

```text
Vec2
```

không nói rằng compiler bắt buộc phải:

```text
memory:
[x][y]
```

Compiler có thể dùng:

```text
register XMM
```

hoặc:

```text
two registers
```

hoặc memory.

Miễn observable semantics không thay đổi.

---

# 3. Layout mặc định

Axiom mặc định:

```text
@repr(Axiom)
```

hoặc tương đương implicit.

Compiler được phép:

- reorder fields;
- chọn padding;
- chọn alignment;
- dùng niche;
- thay đổi physical representation;
- scalarize;
- pack vào registers;
- eliminate object storage.

Mục đích:

> **Layout mặc định là compiler optimization space, không phải programmer contract.**

---

# 4. Khi nào layout trở thành contract?

Khi programmer yêu cầu explicit representation:

```axiom
@repr(C)
struct Point {
    x: f32,
    y: f32
}
```

hoặc:

```axiom
@repr(transparent)
struct UserId(u64);
```

Lúc đó compiler phải tuân thủ contract tương ứng.

---

# 5. `@repr(C)`

`@repr(C)` đảm bảo representation tương thích với C ABI trong phạm vi Axiom quy định.

Nó khóa:

- field order;
- alignment;
- padding;
- scalar representation;
- aggregate representation.

Nhưng:

```text
@repr(C)
```

không tự động làm type:

```text
FFI-safe
```

Ví dụ field bên trong vẫn có thể không FFI-safe.

---

# 6. `@repr(transparent)`

Ví dụ:

```axiom
@repr(transparent)
struct UserId(u64);
```

Semantic:

```text
UserId != u64
```

nhưng physical ABI:

```text
UserId ≈ u64
```

Điều này cực kỳ hữu ích cho:

- type safety;
- FFI;
- handles;
- newtypes;
- zero-cost abstractions.

---

# 7. `@repr(packed)`

Giữ lại nhưng thuộc unsafe/system territory:

```axiom
@repr(packed)
struct Header {
    ...
}
```

Vì packed layout có thể tạo:

```text
misaligned access
```

Compiler không được giả định alignment thông thường.

---

# 8. `@repr(align(N))`

Cho phép yêu cầu alignment tối thiểu:

```axiom
@repr(align(64))
struct CacheLine {
    ...
}
```

Đây là representation contract.

---

# 9. Layout engine

ABI phase sử dụng:

```text
LayoutDB
```

với:

```text
Layout {
    size
    alignment
    fields
    padding
    niches
    scalarization
    representation
}
```

Ví dụ:

```text
LayoutId
```

được cache/intern theo:

```text
TypeId + Target + RepresentationContract
```

---

# 10. `size_of`, `align_of`, `offset_of`

Các giá trị này là compile-time queries:

```axiom
size_of<T>()
align_of<T>()
offset_of<T, field>()
```

Nhưng:

> Không nên expose physical layout nếu type không có representation contract.

Nếu layout có thể thay đổi theo compiler/target, giá trị vẫn hợp lệ **trong compilation hiện tại**.

---

# 11. `size_of<T>()` không đồng nghĩa heap size

Ví dụ:

```axiom
size_of<Vec<i32>>
```

chỉ nói representation của `Vec` value.

Không nói:

```text
number of elements allocated
```

Đây là logical container state vs backing storage.

---

# 12. Scalarization

Ví dụ:

```axiom
struct Pair {
    a: i64,
    b: i64
}
```

Function:

```axiom
fn add(x: Pair) -> i64 {
    x.a + x.b
}
```

ABI optimizer có thể biến:

```text
Pair
```

thành:

```text
rdi = a
rsi = b
```

mà không cần materialize Pair.

---

# 13. Aggregate ABI classification

ABI classifier nhận:

```text
Type
+
Layout
+
Target ABI
```

và quyết định:

```text
Register
Stack
Indirect
Split
SRet
```

Ví dụ:

```text
small scalar → register
small aggregate → registers
large aggregate → memory
```

Nhưng quy tắc cụ thể target-dependent.

---

# 14. Không hard-code “struct luôn truyền bằng memory”

Đây là một lỗi thiết kế dễ gặp.

Axiom semantic:

```text
struct
```

không nên map cứng thành:

```text
pointer-to-struct
```

Nếu struct nhỏ, compiler phải tận dụng register ABI.

---

# 15. Large return value

Ví dụ:

```axiom
fn make_matrix() -> Matrix4x4
```

Không nhất thiết copy 64 bytes qua registers.

ABI lowering có thể biến thành:

```text
caller allocates result storage
        ↓
callee receives hidden result pointer
        ↓
callee initializes result
```

Đây là:

```text
sret / indirect return
```

---

# 16. Caller allocation

Semantic:

```axiom
fn make() -> BigStruct
```

không thay đổi.

Physical ABI:

```text
fn make(out: *mut BigStruct) -> void
```

có thể được compiler tạo nội bộ.

Programmer không phải viết pointer API.

---

# 17. Return value ownership

Điểm rất quan trọng:

```text
return ownership
```

không đồng nghĩa:

```text
copy memory
```

Compiler có thể:

```text
construct directly in caller storage
```

hoặc:

```text
move registers
```

tùy ABI.

---

# 18. `view<T>` representation

Semantic:

```text
view<T>
```

là:

```text
READ capability
```

Physical representation thông thường có thể là:

```text
(pointer, length)
```

nhưng đây **không phải semantic definition**.

Compiler được phép dùng representation khác khi ABI/optimization cho phép.

---

# 19. `mut_view<T>`

Tương tự:

```text
mut_view<T>
```

có thể physical là:

```text
(pointer, length)
```

nhưng semantic vẫn là:

```text
exclusive mutable capability
```

Không được hiểu:

```text
pointer + length = mutable safety
```

Safety đã được verifier chứng minh trước ABI lowering.

---

# 20. Capability metadata có thể biến mất

Trước verification:

```text
CapabilityId
RegionId
Provenance
Access
Lifetime
```

Sau khi chứng minh:

```text
Verified
```

những thông tin chỉ phục vụ compiler có thể bị erase.

Binary thường chỉ còn representation cần thiết:

```text
pointer
length
```

hoặc thậm chí:

```text
pointer
```

nếu length đã compile-time known.

---

# 21. Fixed-size view

Ví dụ tương lai:

```axiom
view<[T; 16]>
```

compiler có thể biết:

```text
length = 16
```

và không cần truyền runtime length.

Đây là một ví dụ tốt về:

> semantic abstraction → ABI tối thiểu.

---

# 22. Slice/view ABI không cố định toàn cầu

Không nên frozen:

```text
view<T> == { ptr, len }
```

như một language-level ABI.

Thay vào đó:

```text
default Axiom ABI
```

quyết định representation.

C ABI wrapper có thể explicit:

```text
@repr(C)
struct CSlice<T> {
    ptr: *const T,
    len: usize
}
```

---

# 23. `String`, `Str`, `Bytes`

Không được coi chúng là cùng ABI.

Ví dụ:

```text
Str
```

có thể:

```text
(ptr, len)
```

Trong khi:

```text
String
```

có thể:

```text
(ptr, len, capacity)
```

và ownership semantics khác.

---

# 24. `Option<T>`

Axiom nên tận dụng **niche optimization**.

Ví dụ:

```axiom
Option<Box<T>>
```

không nhất thiết:

```text
tag + pointer
```

Có thể dùng:

```text
null pointer = None
non-null = Some
```

nếu representation contract cho phép.

---

# 25. Nhưng niche optimization không phải semantic

Programmer chỉ biết:

```text
Option<Box<T>>
```

chứ không được dựa vào:

```text
null == None
```

trừ khi explicit representation contract.

---

# 26. Enum layout

Semantic:

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

Compiler quyết định:

```text
tag
payload
niche
alignment
```

Có thể:

```text
tag + union
```

hoặc niche representation.

---

# 27. Enum optimization

Ví dụ:

```text
Option<bool>
```

có thể cần representation khác:

```text
Option<u8>
```

Compiler tự chọn layout tối ưu.

---

# 28. Pattern matching không phụ thuộc tag layout

MIR đã biến:

```text
match x
```

thành semantic control flow.

ABI/backend mới biết:

```text
physical tag nằm ở đâu
```

Do đó optimizer có thể thay đổi enum representation mà không phá semantic pipeline.

---

# 29. `dyn Trait`

Dynamic trait object là explicit abstraction.

Ví dụ:

```axiom
dyn Drawable
```

có thể physical:

```text
data pointer
+
vtable pointer
```

Nhưng:

```text
dyn Trait
```

không được tự động xuất hiện chỉ vì trait tồn tại.

---

# 30. VTable

VTable có thể chứa:

```text
method pointers
drop glue
type metadata
size/alignment metadata
```

tùy nhu cầu ABI.

Không cần object header trong object itself.

Đây là điểm quan trọng:

```text
object ≠ vtable-bearing object
```

---

# 31. Dynamic dispatch chỉ khi yêu cầu

```axiom
fn render(x: dyn Renderable)
```

→ dynamic dispatch.

Trong generic:

```axiom
fn render<T: Renderable>(x: T)
```

→ static dispatch mặc định.

---

# 32. Devirtualization

Như BOOTSTRAP-107 đã khóa:

```text
dyn call
    ↓
concrete target proven
    ↓
direct call
```

ABI layer phải cho phép transformation này.

---

# 33. Closure ABI

Closure semantic:

```text
code + environment
```

ABI có thể:

```text
closure struct {
    fn_ptr
    env_ptr
}
```

hoặc compiler-specialized representation.

Capturing closure **không tự động heap allocate**.

---

# 34. Noncapturing closure

Nếu:

```axiom
let f = |x| x + 1;
```

không capture:

```text
closure → fn pointer
```

có thể zero-cost.

---

# 35. Capturing closure

Ví dụ:

```axiom
let factor = 10;
let f = |x| x * factor;
```

Compiler tạo anonymous environment:

```text
Env {
    factor
}
```

Có thể:

```text
inline
```

hoặc:

```text
register
```

hoặc:

```text
stack
```

không có heap requirement.

---

# 36. Closure khi truyền FFI

Không được tự động truyền closure Axiom sang C function pointer.

Cần adapter explicit:

```text
callback function
+
context pointer
```

và contract lifetime.

---

# 37. Function pointer

Axiom phân biệt:

```text
fn(T) -> R
```

và:

```text
closure
```

Function pointer không có environment.

Do đó ABI đơn giản hơn.

---

# 38. Trait method ABI

Static trait call:

```text
T::method(...)
```

sau specialization:

```text
direct function call
```

Dynamic:

```text
dyn Trait
```

→ vtable dispatch.

Không có hidden vtable cho static trait implementation.

---

# 39. Drop ABI

Compiler có thể tạo:

```text
drop_glue<T>
```

nhưng đây là compiler-generated code.

Ví dụ:

```text
drop Vec<T>
```

sẽ recursively drop:

```text
elements
storage
```

theo semantic rules.

---

# 40. Drop glue không phải runtime GC

Đây chỉ là deterministic compiler-generated cleanup.

Không có:

```text
GC scan
```

hay:

```text
global object registry
```

---

# 41. Drop glue specialization

Nếu:

```text
T: !Drop
```

và chứa no drop-bearing field:

```text
drop(T)
```

có thể compile thành:

```text
nothing
```

---

# 42. Trivial destruction

Compiler nên derive:

```text
TriviallyDrop
```

ở internal representation.

Ví dụ:

```text
i32
f64
struct of trivial fields
```

không cần runtime cleanup.

---

# 43. Drop flags

Partial move có thể yêu cầu compiler-generated state.

Ví dụ:

```axiom
struct S {
    a: Resource,
    b: Resource
}
```

sau:

```text
move s.a
```

compiler phải biết:

```text
a = MOVED
b = OWNED
```

Physical drop flag có thể:

- tồn tại;
- được optimized;
- biến mất nếu CFG chứng minh trạng thái.

---

# 44. Drop flags không nhất thiết runtime

Ví dụ compiler thấy:

```text
move a
return
```

thì biết chính xác cleanup.

Không cần tạo dynamic flag.

---

# 45. `Copy` và ABI

`Copy` không yêu cầu memcpy.

Ví dụ:

```text
Copy<u64>
```

có thể:

```text
register move
```

---

# 46. `Clone`

`Clone` là semantic operation.

ABI có thể:

```text
direct call
inline
specialize
```

nhưng compiler không được biến:

```text
Clone
```

thành implicit copy nếu semantics khác.

---

# 47. Newtype ABI

Ví dụ:

```axiom
struct UserId(u64);
struct ProductId(u64);
```

Semantic:

```text
UserId != ProductId
```

nhưng default Axiom ABI có thể truyền cả hai như:

```text
u64
```

nếu compiler có thể erase wrapper.

Đây là **zero-cost type safety**.

---

# 48. Tuple ABI

Tuple:

```axiom
(i32, f32)
```

không bắt buộc materialize thành memory.

Có thể:

```text
register 1
register 2
```

tùy target ABI.

---

# 49. ZST

Zero-sized types:

```axiom
struct Marker {}
```

có:

```text
size = 0
```

về semantic layout.

Compiler không cần allocate storage cho từng instance nếu address không observable.

---

# 50. ZST và identity

Nếu programmer cần:

```text
unique physical address
```

thì đó là storage identity contract khác.

Không được suy luận:

```text
different ZST values
→ different addresses
```

---

# 51. Alignment

Mỗi layout:

```text
size
alignment
```

được target-aware.

Compiler phải đảm bảo:

```text
address % alignment == 0
```

cho storage hợp lệ.

---

# 52. Padding

Padding:

```text
not semantic data
```

Không được giả định:

```text
padding bytes == 0
```

trừ explicit initialization/representation contract.

---

# 53. Bytewise equality

Không được compiler mặc định:

```text
memcmp(a,b) == semantic equality
```

Ví dụ floating-point:

```text
NaN
-0
+0
```

và enum niches.

Semantic equality và representation equality là hai thứ khác nhau.

---

# 54. `bitcast`

Axiom cần phân biệt:

```text
CAST
```

và:

```text
BITCAST
```

`CAST`:

```text
semantic conversion
```

`BITCAST`:

```text
same bits
different type interpretation
```

---

# 55. Bitcast legality

`bitcast<T,U>` chỉ hợp lệ khi compiler chứng minh:

```text
size compatible
alignment compatible
representation valid
```

Nếu không:

```text
unsafe/system
```

hoặc compile error.

---

# 56. Endianness

Default semantic types không expose endian.

Endianness chỉ trở thành concern ở:

```text
serialization
FFI
wire format
device memory
packed representation
```

Ví dụ:

```axiom
u32.to_le_bytes()
```

là semantic conversion.

---

# 57. Serialization ≠ memory representation

Đây là invariant quan trọng.

```text
@repr(C)
```

không có nghĩa:

```text
wire format
```

và:

```text
serialize(T)
```

không được mặc định memcpy object memory.

---

# 58. ABI MIR

Sau lowering, compiler có:

```text
AbiFunction {
    params
    returns
    hidden_params
    calling_convention
    stack_layout
    register_assignments
    sret
    varargs
    drop_abi
}
```

Ví dụ semantic:

```axiom
fn create() -> BigStruct
```

có thể thành:

```text
ABI:
    param0 = hidden_result_pointer
    return = void
```

---

# 59. ABI MIR không còn abstract như MIR

MIR:

```text
return value
```

ABI MIR:

```text
write result into sret location
```

MIR:

```text
call f(x)
```

ABI MIR:

```text
arg0 → RDI
arg1 → RSI
call symbol
```

Nhưng register allocation thực sự vẫn thuộc backend.

---

# 60. ABI lowering không phải register allocation

Tách:

```text
ABI classification
```

khỏi:

```text
physical register allocation
```

ABI có thể nói:

```text
first integer argument → integer argument class
```

Backend sau đó chọn:

```text
RDI
```

hoặc register cụ thể theo target.

---

# 61. Calling conventions

Axiom cần concept:

```text
CallingConvention
```

với tối thiểu:

```text
Axiom
C
System
```

Sau này:

```text
Fast
Vector
GPU
WASM
```

có thể mở rộng.

---

# 62. Axiom ABI

Dùng cho:

```text
Axiom ↔ Axiom
```

Ưu tiên:

- performance
- optimization freedom
- compiler-controlled representation
- versioning

Không nên hứa stable binary ABI quá sớm.

---

# 63. C ABI

Dùng:

```axiom
extern "C" fn foo(...)
```

hoặc syntax tương đương.

Contract phải xác định:

- layout
- calling convention
- symbol
- ownership
- nullability
- strings
- callbacks
- allocator domain.

---

# 64. System ABI

Dùng cho:

- OS syscall wrappers
- platform API
- ABI-specific calls
- Windows/Linux/macOS APIs.

Không nhất thiết giống C ABI trong mọi trường hợp.

---

# 65. `pub` ≠ exported symbol

```text
pub fn foo()
```

chỉ visibility trong Axiom package/module graph.

Muốn binary symbol:

```axiom
@export("foo")
pub fn foo(...)
```

hoặc tương đương.

---

# 66. Symbol naming

Default Axiom symbols có thể name-mangle:

```text
package::module::function
```

để tránh collision.

Ví dụ conceptually:

```text
_ZAX_package_module_function...
```

Format cụ thể chưa cần frozen ở 108.

---

# 67. Explicit export

```axiom
@export("my_function")
extern "C" fn foo(...)
```

Binary symbol:

```text
my_function
```

Compiler phải validate ABI signature.

---

# 68. Generic export

Không được:

```axiom
@export("foo")
fn foo<T>(x: T)
```

vì foreign caller không biết T là gì.

Phải specialize:

```axiom
@export("foo_i32")
fn foo(x: i32)
```

hoặc compiler-generated concrete wrapper.

---

# 69. Variadic

Core language không cần general C-style variadic.

Chỉ hỗ trợ trong:

```text
extern "C"
system
```

và FFI-safe ABI.

---

# 70. TLS

```axiom
@tls
static X: T
```

ABI lowering tạo target-specific TLS representation.

Không để TLS semantics rò vào generic MIR.

---

# 71. Static data

Compiler phân loại:

```text
read-only
mutable
zero-init
TLS
relocatable
```

và map vào:

```text
.rodata
.data
.bss
.tdata
.tbss
```

ở ObjectWriter.

---

# 72. Global initialization

Axiom không nên mặc định có:

```text
global constructor runtime
```

để initialize arbitrary globals.

Ưu tiên:

```text
compile-time constant initialization
```

Nếu runtime initialization thật sự cần:

```text
explicit initialization mechanism
```

và linker/runtime contract rõ ràng.

Điều này giúp binary nhỏ và startup deterministic.

---

# 73. FFI ownership

ABI signature không chỉ gồm:

```text
type
```

mà cần FFI contract:

```text
ownership
nullability
lifetime
allocator
threading
calling convention
```

Ví dụ:

```text
char* returned
```

không tự nói:

```text
ai free?
```

Axiom phải bắt contract đó được xác định ở wrapper/API.

---

# 74. Foreign allocator

Không được:

```text
foreign malloc
↓
Axiom free
```

mặc định.

Allocator domains phải explicit.

Ví dụ:

```text
OwnedByForeign
```

→ foreign release function.

---

# 75. C string

`String` Axiom không tự động là:

```text
char*
```

Cần explicit:

```text
CString
CStr
```

hoặc FFI conversion.

Điều này tránh:

- missing NUL
- ownership ambiguity
- UTF-8 mismatch.

---

# 76. Raw pointer ABI

Raw pointer:

```text
*const T
*mut T
```

là machine-level pointer.

Nhưng:

```text
pointer representation
```

không đồng nghĩa:

```text
valid safe capability
```

ABI lowering không được bỏ qua provenance semantics ở boundary.

---

# 77. FFI boundary làm mất một phần proof

Foreign function:

```text
unknown alias
unknown mutation
unknown lifetime
```

nếu không có contract.

Do đó optimizer phải mặc định conservative.

Ví dụ foreign call có thể:

```text
read memory
write memory
retain pointer
```

nếu contract không hạn chế.

---

# 78. FFI contract

Compiler có thể có internal:

```text
FfiContract {
    reads
    writes
    ownership
    may_retain
    may_callback
    may_panic
    may_block
    synchronization
}
```

Không nhất thiết tất cả phải là source syntax trong Core v1.

---

# 79. ABI contract và optimization

Ví dụ:

```text
@repr(C)
struct Vec3
```

layout bị khóa.

Nhưng compiler vẫn có thể:

```text
pass Vec3 in registers
```

nếu C ABI cho phép.

Representation contract không đồng nghĩa memory materialization.

---

# 80. ABI MIR invariant quan trọng nhất

Sau ABI lowering:

> **mọi abstraction còn tồn tại trong ABI MIR đều phải có lý do observable hoặc ABI-required.**

Không được còn:

```text
ownership checker
view lifetime
trait generic
closure abstraction
```

chỉ vì compiler quên erase.

Chúng phải được:

```text
lower
specialize
erase
```

hoặc biến thành physical requirement thực sự.

---

# 81. Pipeline hoàn chỉnh tới đây

Ta hiện có:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Verification
  ↓
Verified MIR
  ↓
OptIR
  ↓
Optimization
  ↓
ABI MIR
```

Và semantic boundary đã rất rõ:

```text
MIR
 = "program means what?"

OptIR
 = "how can we make it faster?"

ABI MIR
 = "how must the result be represented to call machine code?"
```

---

# 82. Invariants — `AABI-20..`

### `AABI-20`
Semantic type identity is distinct from physical representation.

### `AABI-21`
Default Axiom representation is compiler-controlled unless explicitly constrained.

### `AABI-22`
Explicit representation attributes create representation contracts.

### `AABI-23`
`@repr(C)` provides a C-compatible representation contract within the defined FFI-safe subset.

### `AABI-24`
`@repr(transparent)` preserves the required underlying representation contract without merging semantic type identity.

### `AABI-25`
Packed representation may create alignment hazards and belongs to unsafe/system usage.

### `AABI-26`
Alignment is part of physical layout correctness.

### `AABI-27`
Padding is not semantic data.

### `AABI-28`
Semantic equality is not automatically bytewise equality.

### `AABI-29`
Enum representation is compiler-controlled unless explicitly constrained.

### `AABI-30`
Niche optimization may be used when representation semantics permit it.

### `AABI-31`
Niche representation is not exposed as a semantic assumption unless explicitly contracted.

### `AABI-32`
Small aggregates may be passed or returned in registers when the target ABI permits.

### `AABI-33`
Large aggregates may use indirect/caller-allocated return mechanisms.

### `AABI-34`
Caller allocation does not imply heap allocation.

### `AABI-35`
Returning an owned value does not inherently require a physical memory copy.

### `AABI-36`
Move semantics do not imply physical movement.

### `AABI-37`
Copy semantics do not imply physical copying.

### `AABI-38`
`view<T>` and `mut_view<T>` representations are ABI details, not their complete semantic definitions.

### `AABI-39`
Compiler-only capability metadata may be erased after verification.

### `AABI-40`
Dynamic dispatch exists only when explicitly represented by the source semantics or required by an ABI boundary.

### `AABI-41`
Static trait dispatch does not require a vtable.

### `AABI-42`
`dyn Trait` may use explicit dynamic-dispatch metadata such as a vtable.

### `AABI-43`
Closure representation is compiler-controlled unless crossing an explicit ABI boundary.

### `AABI-44`
Noncapturing closures may lower to ordinary function pointers.

### `AABI-45`
Capturing closures do not inherently require heap allocation.

### `AABI-46`
Drop glue is compiler-generated deterministic cleanup, not garbage collection.

### `AABI-47`
Trivially destructible values require no unnecessary runtime cleanup.

### `AABI-48`
Drop flags may be eliminated when control-flow analysis proves their state statically.

### `AABI-49`
Newtype semantic identity is preserved even when physical representation is transparent.

### `AABI-50`
`CAST` and `BITCAST` are semantically distinct operations.

### `AABI-51`
Bitcasts require valid representation, size, and alignment conditions.

### `AABI-52`
Memory representation is distinct from serialization/wire representation.

### `AABI-53`
Endianness is explicit at serialization/device/FFI boundaries rather than implicit in ordinary semantic types.

### `AABI-54`
ABI classification is distinct from register allocation.

### `AABI-55`
Calling conventions are explicit compiler concepts.

### `AABI-56`
Axiom ABI, C ABI, and System ABI are distinct contracts.

### `AABI-57`
`pub` visibility does not automatically export a binary symbol.

### `AABI-58`
Binary exports require explicit export semantics.

### `AABI-59`
Generic functions cannot be directly exported through an ABI requiring a concrete signature without specialization.

### `AABI-60`
Foreign allocator ownership is explicit.

### `AABI-61`
Axiom strings are not implicitly C strings.

### `AABI-62`
Foreign pointers do not automatically establish safe ownership or capability validity.

### `AABI-63`
Foreign calls are conservatively modeled unless an explicit contract provides stronger facts.

### `AABI-64`
ABI lowering must preserve ownership, Drop, synchronization, atomic, volatile, FFI, async, and GPU semantics.

### `AABI-65`
ABI MIR contains no unresolved generic or semantic representation decisions.

### `AABI-66`
Compiler-only abstractions must be erased, specialized, or lowered before machine code generation.

### `AABI-67`
ABI lowering must preserve source-to-machine debug provenance.

### `AABI-68`
ABI decisions are target-aware but must preserve target-independent Axiom semantics.

### `AABI-69`
Representation constraints must never silently weaken safe-code guarantees.

### `AABI-70`
ABI lowering cannot introduce mandatory heap allocation, object headers, GC, or runtime services unless explicitly required by the program's semantics or ABI contract.

---

# Trạng thái Axiom hiện tại

Chúng ta đã đi qua một đoạn rất quan trọng:

```text
103 Frontend
104 Type System / Elaboration
105 HIR → MIR
106 Verification
107 Optimization
108 ABI / Representation
```

Nó tạo thành một compiler semantic core khá hoàn chỉnh:

```text
                    ┌──────────────────┐
                    │   Axiom Source   │
                    └────────┬─────────┘
                             ↓
                         Frontend
                             ↓
                       Typed HIR
                             ↓
                           MIR
                             ↓
                    ┌────────────────┐
                    │   Verification │
                    └───────┬────────┘
                            ↓
                      Verified MIR
                            ↓
                      Semantic Facts
                            ↓
                         OptIR
                            ↓
                     Optimized OptIR
                            ↓
                       ABI Lowering
                            ↓
                         ABI MIR
                            ↓
                         Axiom LIR
```

Và đây là một điểm rất đáng chú ý: **Axiom không cần chọn giữa “an toàn” và “nhanh” bằng cách bắt programmer chuyển sang pointer/unsafe.** Ownership + capability + verification đang trở thành nguồn thông tin trực tiếp cho optimizer.

---

## BOOTSTRAP-109 tiếp theo

Bước hợp lý tiếp theo là:

# **BOOTSTRAP-109 — Axiom LIR & Target Machine Backend**

Từ:

```text
ABI MIR
   ↓
Axiom LIR
   ↓
Target Lowering
   ↓
Machine IR
```

sẽ khóa:

- virtual register model;
- integer/FP/vector register classes;
- machine instruction representation;
- x86-64;
- AArch64;
- RISC-V;
- WASM;
- instruction selection;
- legalization;
- addressing modes;
- flags/condition codes;
- calling convention lowering;
- stack frame;
- register allocation;
- spill/reload;
- SIMD;
- tail call;
- branch lowering;
- atomic instruction mapping;
- memory barriers/fences;
- inline assembly;
- debug/unwind information;
- code emission.

Đây chính là bước chuyển từ **compiler semantics** sang **CPU semantics**.