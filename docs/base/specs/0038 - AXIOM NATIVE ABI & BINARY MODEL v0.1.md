Tiếp tục với **AXIOM NATIVE ABI & BINARY MODEL v0.1**. Đây là tầng nên khóa tương đối sớm, vì nó nối trực tiếp semantic type system → machine code → executable.

# AXIOM NATIVE ABI & BINARY MODEL v0.1

## 1. Nguyên tắc trung tâm

Axiom có 4 tầng:

```text
TYPE SEMANTICS
      ↓
DATA REPRESENTATION
      ↓
ABI REPRESENTATION
      ↓
MACHINE REPRESENTATION
```

Không được đảo ngược:

```text
CPU register convention
        ↓
ép language semantics
```

ABI chỉ trả lời:

> Một giá trị đã có semantic type thì khi đi qua function boundary, FFI boundary hoặc binary boundary được biểu diễn thế nào?

---

# 2. Ba loại ABI

Tôi đề xuất Axiom có đúng 3 nhóm chính ban đầu:

| ABI | Mục đích |
|---|---|
| `axiom` | native Axiom |
| `C` | C interoperability |
| `system` | platform calling convention |

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

mặc định:

```text
@abi(axiom)
```

FFI:

```axiom
extern @abi(C) fn puts(...)
```

Platform-specific:

```axiom
@abi(system)
```

---

# 3. Native Axiom ABI không cần stable giữa mọi compiler version

Đây là quyết định rất quan trọng.

Mặc định:

```text
Axiom ABI
```

có thể thay đổi giữa compiler releases.

Nếu muốn ABI ổn định:

```text
@abi(C)
```

hoặc một ABI version cụ thể sau này.

Như vậy compiler có tự do:

- reorder fields
- scalarize struct
- thay đổi register assignment
- thay đổi generic calling convention
- thay đổi niche representation

mà không phá language semantics.

---

# 4. `struct` không có một representation duy nhất

Ví dụ:

```axiom
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

Semantic:

```text
3 × f32
```

Machine representation có thể:

```text
xmm0/xmm1
```

hoặc:

```text
stack
```

hoặc:

```text
3 scalar registers
```

hoặc:

```text
memory
```

Compiler quyết định.

---

# 5. Aggregate passing

Axiom nên có khái niệm:

```text
ABI lowering
```

Ví dụ:

```text
Vec3
 ↓
lower_aggregate
 ↓
{ f32, f32, f32 }
 ↓
target ABI classifier
```

Không hard-code:

```text
struct = always pointer
```

vì điều đó sẽ tạo indirection không cần thiết.

---

# 6. Return value

Một function:

```axiom
fn make_point() -> Point
```

có thể:

```text
register return
```

hoặc:

```text
caller-allocated return storage
```

hoặc:

```text
hidden sret pointer
```

tùy target/size/ABI.

Source semantics không thay đổi.

---

# 7. Caller allocation

Đây là điểm rất phù hợp với mục tiêu hiệu năng của Axiom.

Ví dụ:

```axiom
fn make_buffer() -> Buffer
```

thay vì:

```text
callee allocates
→ creates temporary
→ copies
→ caller owns
```

compiler có thể:

```text
caller allocates destination
        ↓
callee constructs directly
```

Nhưng đây là optimization/ABI lowering.

Không đưa khái niệm `sret` vào language.

---

# 8. Move không đồng nghĩa memcpy

Ví dụ:

```axiom
let b = a
```

nếu `a` non-Copy:

```text
semantic:
    ownership(a) → ownership(b)
```

Không phải:

```text
memcpy(a,b)
```

Compiler có thể:

```text
register rename
```

hoặc:

```text
no machine instruction
```

hoặc thực sự copy bytes nếu cần.

---

# 9. `Copy`

Nếu:

```axiom
struct Point {
    x: f32
    y: f32
}
```

là `Copy`:

```axiom
let b = a
```

semantic:

```text
a remains valid
b becomes independent value
```

Machine-level:

```text
register copy
```

hoặc thậm chí compiler có thể duplicate SSA use mà không tạo physical copy.

---

# 10. View ABI

Semantic:

```axiom
view<T>
```

là:

```text
non-owning read capability
```

Nhưng ABI thường có thể là:

```text
(pointer, length)
```

Ví dụ:

```axiom
fn sum(x: view<i32>) -> i32
```

có thể lower thành:

```text
ptr + len
```

Nhưng **đây không phải language-level guarantee**.

---

# 11. `mut_view<T>`

Tương tự:

```text
(pointer, length)
```

nhưng semantic capability là:

```text
WRITE
```

Compiler vẫn kiểm tra:

```text
no conflicting active capability
owner alive
region valid
```

ABI chỉ mang representation.

---

# 12. View lifetime không nằm trong ABI

Ví dụ:

```axiom
fn sum(x: view<i32>) -> i32
```

không cần runtime lifetime field.

Không có:

```text
refcount
lifetime ID
GC metadata
```

Lifetime là compile-time property.

Đây là một lợi thế lớn.

---

# 13. Closure ABI

Closure:

```axiom
let f = |x| x + offset
```

semantic model:

```text
Closure {
    environment
    call_function
}
```

Compiler có thể lower thành:

```text
fn_ptr
env_ptr
```

nếu closure cần runtime identity.

Nhưng nếu closure không escape:

```text
inline
specialize
eliminate closure object
```

có thể xảy ra.

---

# 14. Closure không nhất thiết là heap object

Ví dụ:

```axiom
fn process(values: view<i32>) {
    let offset = 10

    map(values, |x| x + offset)
}
```

Compiler có thể biến thành:

```text
specialized loop
```

hoàn toàn không có:

```text
heap allocation
closure object
function pointer
```

---

# 15. Trait dispatch

Static:

```axiom
fn draw<T: Drawable>(x: view<T>)
```

sau monomorphization:

```text
draw<Circle>
draw<Square>
```

→ direct calls.

Không có:

```text
vtable
```

mặc định.

---

# 16. Dynamic dispatch

Nếu programmer thực sự yêu cầu dynamic dispatch:

```text
dyn Drawable
```

thì representation có thể:

```text
data_ptr
dispatch_ptr
```

hoặc target-specific equivalent.

Lúc đó vtable/dispatch metadata là **property của dynamic abstraction**, không phải object model của toàn ngôn ngữ.

---

# 17. Không có object header

Một:

```axiom
struct Vec3
```

không tự động thành:

```text
┌──────────────┐
│ type pointer  │
│ refcount      │
│ GC flags      │
├──────────────┤
│ x             │
│ y             │
│ z             │
└──────────────┘
```

Mà có thể đơn giản:

```text
x
y
z
```

Đây là một invariant cực kỳ quan trọng cho systems programming.

---

# 18. Enum representation

Ví dụ:

```axiom
enum Option<T> {
    None
    Some(T)
}
```

Semantic:

```text
None | Some(T)
```

Physical representation:

```text
tag + payload
```

nhưng compiler có quyền dùng:

```text
niche encoding
```

nếu an toàn.

Ví dụ một type có giá trị không hợp lệ tự nhiên có thể dành một bit-pattern cho `None`.

---

# 19. Nhưng niche optimization không được observable

Programmer không được viết code dựa trên:

```text
sizeof(Option<T>) == ...
```

trừ khi representation explicitly specified.

Nếu cần layout ổn định:

```axiom
@repr(...)
```

---

# 20. `repr(C)`

Đây là boundary rõ ràng:

```axiom
@repr(C)
struct CPoint {
    x: f32
    y: f32
}
```

Lúc này:

- field order
- alignment
- ABI compatibility

phải tuân theo C-compatible rules của target.

Đây là nơi programmer **được phép yêu cầu representation cụ thể**.

---

# 21. `repr(packed)`

Không nên coi đây là tính năng thông thường.

```axiom
@repr(packed)
```

nên thuộc unsafe/system-level vì:

- misalignment
- unaligned access
- ABI hazards
- performance penalty
- platform differences.

---

# 22. Explicit alignment

Cho phép:

```axiom
@align(64)
struct CacheLineData {
    ...
}
```

nhưng compiler phải kiểm tra alignment hợp lệ.

Đây là storage/layout property, không phải ownership feature.

---

# 23. Endianness

Core semantic integer:

```text
u32 = mathematical 32-bit value
```

không có endian.

Endian chỉ xuất hiện khi chuyển:

```text
value ↔ bytes
```

Ví dụ library:

```axiom
to_le_bytes(x)
to_be_bytes(x)
from_le_bytes(...)
```

Như vậy:

```text
u32
```

không bị gắn với little-endian.

---

# 24. Raw byte representation

Cần phân biệt:

```text
T
```

với:

```text
bytes
```

Không cho phép tùy tiện:

```axiom
reinterpret<u32>(SomeStruct)
```

trong safe code.

Raw reinterpretation:

```text
unsafe
```

và phải thỏa alignment/layout/validity rules.

---

# 25. Pointer representation

Raw pointer:

```axiom
*const T
*mut T
```

có machine representation target-dependent.

Compiler không được giả định:

```text
pointer == usize
```

về semantic type.

Nếu muốn convert:

```axiom
ptr as usize
```

phải là explicit unsafe/system operation.

---

# 26. Pointer provenance

Tôi đề xuất Axiom **không nên biến provenance thành một hệ thống type-level phức tạp**.

Thay vào đó:

```text
safe references/views
    → compiler tracks provenance

raw pointers
    → unsafe programmer responsibility
```

Điều này phù hợp mục tiêu:

> Không bắt programmer học một hệ thống pointer/lifetime cực kỳ phức tạp chỉ để viết code bình thường.

---

# 27. Symbol mangling

Native Axiom functions:

```axiom
fn add(a: i32, b: i32) -> i32
```

không nên export symbol `add` mặc định.

Compiler có thể mangle:

```text
_ZN5axiom3add...
```

hoặc format riêng.

Nhưng:

```axiom
@export("add")
```

có thể yêu cầu symbol name cụ thể.

---

# 28. Generic symbols

Ví dụ:

```axiom
fn max<T>(...)
```

sau specialization:

```text
max<i32>
max<f64>
```

có thể có symbol nội bộ riêng hoặc bị inline/eliminate.

Generic không yêu cầu runtime metadata.

---

# 29. Visibility

Tối thiểu:

```text
private
module
public
export
```

Tôi không khuyến nghị đưa một hệ thống visibility kiểu C++ với:

```text
friend
protected
```

vào Axiom.

Struct + module boundary đủ mạnh.

---

# 30. Static data

Phân biệt:

```text
const
static
thread_static
```

### `const`

Không nhất thiết có address.

### `static`

Có storage identity.

### `thread_static`

Có một instance cho mỗi execution context/thread.

Đây là distinction semantic rất quan trọng.

---

# 31. Global constructor

Tôi đề xuất:

> **Không có implicit arbitrary global constructors.**

Ví dụ không cho:

```text
global object
    ↓
constructor chạy trước main
```

một cách âm thầm.

Nếu cần initialization:

```axiom
static CONFIG = ...
```

phải là compile-time initialization nếu có thể.

Dynamic initialization phải explicit:

```axiom
init()
```

hoặc runtime registration mechanism.

Điều này giúp startup deterministic và binary nhỏ.

---

# 32. TLS

Có thể:

```axiom
@thread_local
static var state: State
```

Compiler map xuống native TLS.

Không cần:

```text
Axiom TLS runtime
```

trừ khi abstraction cao hơn yêu cầu.

---

# 33. Function pointer

Function pointer là:

```text
code address
```

về semantic.

Không gắn với closure environment.

Closure có environment thì representation riêng.

Điều này giúp tránh nhầm:

```text
fn pointer
≠
closure
```

---

# 34. Variadic

Cần rất cẩn thận.

Axiom function:

```text
fn foo(...)
```

không nên có variadic kiểu C tùy tiện trong safe code.

FFI:

```axiom
extern @abi(C)
fn printf(format: *const u8, ...)
```

có thể hỗ trợ.

Native Axiom variadic có thể để sau.

---

# 35. SIMD

Không nên nhét SIMD vào một hệ type đặc biệt quá sớm.

Có thể:

```text
Vector<T, N>
```

ở library/compiler intrinsic layer.

Compiler recognize:

```text
Vector<f32, 4>
```

và lower thành:

```text
SSE/AVX/NEON/SVE...
```

nếu target hỗ trợ.

---

# 36. ABI lowering pipeline

Tôi đề xuất pipeline cụ thể:

```text
Typed MIR
   ↓
ABI Lowering
   ↓
ABI MIR
   ↓
Axiom LIR
   ↓
Target ABI Classification
   ↓
Machine IR
```

Ví dụ:

```text
fn f(Point) -> Point
```

↓

```text
logical arguments
```

↓

```text
ABI arguments:
  xmm0
  xmm1
  xmm2
```

↓

```text
machine registers
```

---

# 37. ABI Lowering không được sửa semantics

Ví dụ ABI lowering phát hiện:

```text
Point return
→ hidden sret pointer
```

không được làm thay đổi:

```text
ownership
Drop
evaluation order
panic semantics
```

Nó chỉ thay representation.

---

# 38. FFI boundary

FFI phải là semantic boundary rõ ràng:

```text
Axiom
  │
  │ @abi(C)
  ↓
Foreign Function
```

Compiler phải biết:

- calling convention
- parameter layout
- return layout
- ownership contract
- pointer validity contract
- effects

---

# 39. FFI effects

Ví dụ:

```axiom
extern @abi(C)
@ffi_effects(READ(arg0))
fn inspect(...)
```

hoặc conservative:

```text
UNKNOWN
```

Nếu compiler không biết foreign function làm gì:

```text
assume conservative effects
```

để verifier không tối ưu sai.

---

# 40. Binary model

Một native Axiom binary nên conceptually gồm:

```text
Executable
├── executable code
├── read-only data
├── writable data
├── TLS
├── relocation information
├── symbols (optional)
├── debug information (optional)
└── unwind information (optional)
```

Không có:

```text
mandatory Axiom VM bytecode
mandatory GC metadata
mandatory runtime type table
```

---

# 41. Object file

Axiom compiler nên có object representation nội bộ:

```text
Axiom Object
├── sections
├── symbols
├── relocations
├── target metadata
├── ABI metadata
└── debug/unwind metadata
```

Sau đó:

```text
Axiom Object
   ↓
ELF / COFF / Mach-O
```

hoặc linker format.

---

# 42. Không nên tự viết mọi thứ ngay

Đây là chỗ cần tránh overengineering.

### Compiler v0.x

```text
Axiom
 ↓
own LIR
 ↓
own machine encoder
 ↓
ELF object
 ↓
system linker
```

### Sau này

```text
Axiom
 ↓
own object writer
 ↓
own linker
 ↓
native executable
```

Semantics không thay đổi.

---

# 43. Axiom Object Format riêng?

Tôi **không đề xuất** tạo một object format riêng.

Không cần:

```text
.axo
```

ở machine-linking layer.

Có thể có intermediate compiler artifacts riêng:

```text
.aim
.mir
```

nhưng final object nên dùng:

```text
ELF
COFF
Mach-O
WASM
```

để ecosystem có thể hiểu.

---

# 44. Binary reproducibility

Đây là một mục tiêu rất đáng đưa vào Axiom.

Cùng:

```text
source
compiler version
target
flags
dependencies
```

nên tạo binary deterministic nếu không có yếu tố external nondeterministic.

Compiler có thể cung cấp:

```text
--reproducible
```

và loại bỏ:

- timestamp
- random symbol ordering
- nondeterministic metadata

nếu target cho phép.

---

# 45. ABI invariants

Tôi đề xuất khóa nhóm này:

**AABI-01** Semantic type precedes ABI representation.

**AABI-02** Native ABI is compiler-controlled.

**AABI-03** C ABI is explicit.

**AABI-04** System ABI is explicit.

**AABI-05** No mandatory object header.

**AABI-06** No mandatory runtime metadata.

**AABI-07** Aggregate passing may use registers or memory.

**AABI-08** Aggregate return may use registers or caller storage.

**AABI-09** Move is semantic ownership transfer, not memcpy requirement.

**AABI-10** View has no mandatory runtime lifetime metadata.

**AABI-11** Static dispatch has no mandatory vtable.

**AABI-12** Dynamic dispatch metadata exists only when explicitly requested.

**AABI-13** Native layout is not ABI-stable unless specified.

**AABI-14** `repr(C)` establishes foreign-compatible layout.

**AABI-15** Raw pointer representation is target-dependent.

**AABI-16** Endianness belongs to byte representation, not integer semantics.

**AABI-17** FFI boundaries have explicit ABI/effect contracts.

**AABI-18** ABI lowering cannot alter observable language semantics.

**AABI-19** Generic specialization does not require runtime generic metadata.

**AABI-20** Ordinary values have no stable address guarantee unless explicitly requested.

---

# 46. Một điểm tôi muốn bổ sung vào kiến trúc tổng thể

Hiện tại Axiom có thể chia thành **5 lớp thực sự rõ ràng**:

```text
┌──────────────────────────────────────┐
│           AXIOM LANGUAGE             │
│ syntax / types / ownership / traits │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│         SEMANTIC COMPILER            │
│ HIR / MIR / verifier / oracle        │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│          OPTIMIZATION                │
│ specialization / escape / vectorize  │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│       ABI + MACHINE LAYER            │
│ LIR / ABI / encoder / object writer  │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│       OPTIONAL PLATFORM LAYER        │
│ allocator / OS / threads / async     │
└──────────────────────────────────────┘
```

Điều này rất hợp với mục tiêu ban đầu của bạn: **ngôn ngữ có thể mạnh và high-level ở phía trên, nhưng không bắt mọi chương trình phải trả chi phí cho những thứ nó không sử dụng.**

### Bước tiếp theo tôi đề xuất

Sau ABI, tầng hợp lý nhất là **`AXIOM STANDARD LIBRARY & CORE API MODEL v0.1`**.

Nhưng lần này không nên bắt đầu liệt kê hàng trăm API. Ta nên thiết kế trước **ranh giới Core ↔ Std ↔ Platform**, đặc biệt là:

```text
Core
 ├── primitives
 ├── Option / Result
 ├── Array / Tuple
 ├── view / mut_view
 ├── basic traits
 │
Std
 ├── Vec
 ├── String
 ├── Map
 ├── Box
 ├── Arena
 ├── File
 ├── Thread
 ├── Mutex
 └── Channel
 │
Platform
 ├── OS
 ├── sockets
 ├── GPU
 ├── filesystem
 └── system calls
```

Đây sẽ là bước quyết định **Axiom có giữ được sự đơn giản mà không biến thành “một ngôn ngữ khổng lồ chứa cả hệ điều hành” hay không**.