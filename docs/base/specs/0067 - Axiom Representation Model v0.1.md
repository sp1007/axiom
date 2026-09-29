Tiếp tục với **Memory Layout + Representation v0.1**. Đây là phần tôi nghĩ nên chốt trước khi đi sâu hơn vào FFI, vì layout quyết định Axiom có thực sự phù hợp với OS/network/graphics/embedded hay chỉ là một high-level systems language.

# Axiom Representation Model v0.1

Nguyên tắc trung tâm:

> **Semantic type và memory representation là hai tầng khác nhau, nhưng programmer có thể yêu cầu representation cụ thể khi ABI, hardware, file format hoặc FFI cần nó.**

```text
Semantic Type
     │
     ▼
Representation Policy
     │
     ├── compiler-controlled
     ├── explicit stable representation
     └── target-specific representation
     │
     ▼
ABI Representation
     │
     ▼
Machine Representation
```

---

# 1. Struct mặc định: compiler được tự do layout

Ví dụ:

```axiom
struct Foo {
    a: u8
    b: u64
    c: u8
}
```

Không nên mặc định cam kết:

```text
a @ offset 0
b @ offset 1
c @ offset 9
```

Compiler có thể reorder:

```text
a @ 0
c @ 1
padding
b @ 8
```

hoặc một layout khác tốt hơn.

Mục tiêu:

- giảm padding;
- tăng alignment;
- tối ưu cache;
- register passing;
- scalar replacement.

---

# 2. Nhưng programmer có thể yêu cầu layout

Ví dụ:

```axiom
@repr(C)
struct PacketHeader {
    version: u8
    flags: u8
    length: u16
}
```

`@repr(C)` có nghĩa:

> Layout phải tương thích với quy tắc layout C của target ABI tương ứng.

Đây là **representation contract**, không phải inheritance hay object model.

---

# 3. Không nên có `repr(C)` mặc định

Nếu mọi struct đều mặc định C layout, compiler mất rất nhiều freedom.

Ví dụ:

```axiom
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

Compiler có thể muốn:

```text
register/register/register
```

hoặc vectorize.

Không nên bị ràng buộc bởi một ABI layout chỉ vì programmer không yêu cầu.

---

# 4. Representation attributes nên rất ít

Tôi đề xuất Core chỉ cần nhóm:

```text
@repr(C)
@repr(transparent)
@repr(packed)
@align(N)
@size(N)       // cân nhắc, chưa nên freeze
```

Không nên có hàng chục loại `repr`.

---

# 5. `repr(transparent)`

Ví dụ:

```axiom
@repr(transparent)
struct UserId(u64)
```

Semantic type:

```text
UserId != u64
```

nhưng representation:

```text
UserId == u64
```

ở ABI boundary.

Rất hữu ích cho:

- handle;
- ID;
- unit types;
- FFI wrappers;
- strong typing.

---

# 6. `repr(transparent)` phải có điều kiện

Chỉ được áp dụng cho wrapper phù hợp:

```text
one representation-bearing field
```

Ví dụ:

```axiom
@repr(transparent)
struct FileHandle(u64)
```

OK.

Nhưng:

```axiom
@repr(transparent)
struct Foo {
    x: u64
    y: u64
}
```

→ compile error.

---

# 7. Alignment

Ví dụ:

```axiom
@align(64)
struct CacheLine {
    ...
}
```

nghĩa là:

```text
alignof(CacheLine) >= 64
```

Compiler phải đảm bảo.

Nhưng `@align` không nhất thiết làm:

```text
size = 64
```

Đó là hai khái niệm khác nhau.

---

# 8. Alignment và size

Nếu:

```text
alignof(T) = 16
sizeof(T) = 24
```

thì trong array:

```text
T[0]
T[1]
T[2]
```

stride phải là multiple của alignment.

Do đó layout engine cần:

```text
size
alignment
stride
field offsets
```

chứ không chỉ `sizeof`.

---

# 9. `packed`

```axiom
@repr(packed)
struct Header {
    a: u8
    b: u32
}
```

có thể tạo:

```text
offset(a) = 0
offset(b) = 1
size = 5
```

Nhưng `b` có thể không aligned.

Vì vậy:

> `packed` phải thuộc unsafe/system-level representation.

Không nên để safe code tùy ý lấy:

```axiom
&header.b
```

rồi giả định pointer alignment bình thường.

---

# 10. Packed không có nghĩa “mọi access đều an toàn”

Đây là distinction quan trọng:

```text
packed representation
≠
normal aligned object
```

Compiler có thể phải generate:

```text
byte loads
combine
```

hoặc target-specific unaligned load.

Do đó:

```text
@repr(packed)
```

là một semantic warning rằng programmer đang yêu cầu representation đặc biệt.

---

# 11. Bitfield

Tôi **không muốn bitfield trở thành struct field primitive của Core**.

Ví dụ không muốn:

```axiom
struct Flags {
    a: bool: 1
    b: bool: 1
    mode: u3
}
```

ngay trong Core.

Lý do:

- endian complexity;
- ABI differences;
- bit ordering;
- atomic access;
- compiler implementation complexity;
- C bitfield vốn đã có nhiều semantics khó chịu.

---

# 12. Thay vào đó: bit operations

Có thể viết:

```axiom
struct Flags(u32)
```

và library/intrinsic:

```axiom
flags.get_bit(3)
flags.set_bits(4, 7, mode)
```

hoặc compile-time masks:

```axiom
const MODE_MASK: u32 = 0b111 << 4;
```

Compiler vẫn có thể generate:

```text
AND
OR
SHR
SHL
```

rất rẻ.

---

# 13. Nhưng embedded/FFI có thể cần bitfield

Do đó không nên nói “Axiom không hỗ trợ bitfield”.

Tôi đề xuất:

```text
Core:
    integer bit operations

System/FFI layer:
    explicit bitfield representation facility
```

Ví dụ sau này:

```axiom
@repr(bitfield, order = lsb0)
struct Register {
    enable: bits(0..0)
    mode: bits(1..3)
    irq: bits(4..7)
}
```

Đây là **representation DSL**, không phải type-system primitive.

---

# 14. Enum representation

Ví dụ:

```axiom
enum Color {
    Red,
    Green,
    Blue
}
```

Compiler được quyền chọn:

```text
u8
```

hoặc:

```text
u16
```

hoặc representation tối ưu khác.

Không nên mặc định:

```text
tag = u64
```

như một số object-oriented runtime.

---

# 15. Enum có payload

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

Conceptually:

```text
┌─────────┬─────────────┐
│ tag     │ payload     │
└─────────┴─────────────┘
```

nhưng đây **không phải semantic requirement**.

Compiler có thể tìm representation tốt hơn.

---

# 16. Niche optimization

Đây là một optimization rất đáng có.

Ví dụ:

```text
Option<NonNull<T>>
```

thay vì:

```text
tag + pointer
```

có thể dùng:

```text
null pointer = None
non-null      = Some
```

Nếu type có một số bit pattern không hợp lệ.

Nhưng:

> Niche optimization là compiler optimization, không phải source-level guarantee.

---

# 17. Không expose niche layout mặc định

Không nên cho programmer dựa vào:

```text
Option<Pointer>
sizeof == sizeof(Pointer)
```

trừ khi representation contract nói rõ.

Nếu cần FFI:

```axiom
@repr(C)
```

hoặc một representation primitive tương lai.

---

# 18. Vì sao điều này quan trọng?

Nếu programmer viết:

```axiom
let x: Option<*mut Foo>;
```

thì semantic là:

```text
Some(pointer)
None
```

Compiler có thể:

```text
null = None
```

hoặc representation khác.

Programmer không cần biết.

Nhưng optimizer vẫn có thể đạt binary cực nhỏ.

---

# 19. `Option<T>` không cần runtime overhead

Ví dụ:

```axiom
fn find(...) -> Option<i64>
```

Compiler có thể dùng:

```text
RAX = value
RDX = discriminant
```

hoặc:

```text
RAX = sentinel/value
```

tùy representation.

Không có:

```text
heap object
header
GC metadata
```

---

# 20. `Result<T,E>` cũng vậy

```axiom
Result<T, E>
```

là ADT.

Compiler có thể:

```text
tag + payload
```

hoặc tối ưu niche.

Không cần exception object.

Đây là một điểm tôi muốn giữ rất chắc:

> **Result không phải exception.**

---

# 21. Layout engine

Compiler nên có một component riêng:

```text
compiler/
└── layout/
    ├── type_layout
    ├── struct_layout
    ├── enum_layout
    ├── alignment
    ├── niche
    └── abi_layout
```

API conceptual:

```text
Layout {
    size
    alignment
    stride
    fields[]
    variants[]
    niches[]
}
```

---

# 22. Layout không chỉ là `sizeof`

Ví dụ:

```text
Layout<T>
├── size
├── alignment
├── stride
├── field offsets
├── variant layout
├── niche information
└── ABI classification
```

Đặc biệt:

```text
Layout
≠
ABI classification
```

Một struct có layout 16 bytes chưa chắc ABI pass theo cách giống nhau trên mọi target.

---

# 23. ABI classification là bước sau

Pipeline:

```text
Type
 ↓
Semantic Layout
 ↓
Representation
 ↓
Target ABI Classification
 ↓
Machine representation
```

Ví dụ SysV AMD64:

```text
struct Vec2 { f64, f64 }
```

có thể được pass bằng XMM registers.

Nhưng đó là **ABI decision**, không phải frontend type semantics.

---

# 24. Endianness

Axiom integer semantics không phụ thuộc endian.

```text
u32 value = 0x12345678
```

luôn có giá trị đó.

Endian chỉ xuất hiện khi:

```text
value
 ↓
bytes
```

Ví dụ:

```axiom
x.to_le_bytes()
x.to_be_bytes()
u32.from_le_bytes(...)
```

---

# 25. Không có global endian mode

Không nên:

```text
@big_endian
```

thay đổi semantics của integer.

Một chương trình chạy trên ARM64 little-endian và một target big-endian vẫn phải có cùng integer semantics.

Endian chỉ nằm ở:

- serialization;
- FFI;
- memory-mapped hardware;
- binary formats.

---

# 26. Byte representation

`u32`:

```text
semantic value
```

`Array<u8, 4>`:

```text
byte sequence
```

Không tự động coi hai thứ là cùng type.

Muốn chuyển:

```axiom
x.to_le_bytes()
```

hoặc:

```axiom
u32.from_le_bytes(bytes)
```

Điều này tránh rất nhiều bug serialization.

---

# 27. SIMD

Tôi vẫn không muốn đưa hàng trăm vector types vào Core.

Thay vào đó:

```text
Vector<T, N>
```

hoặc compiler-known intrinsic.

Ví dụ conceptual:

```axiom
let a: Vector<f32, 4>;
```

Compiler target có thể map:

```text
Vector<f32,4>
      ↓
XMM/YMM
```

hoặc scalarize nếu target không hỗ trợ.

---

# 28. SIMD semantics không phụ thuộc CPU register width

Không nên:

```text
Vec4f = XMM register
```

về mặt semantic.

`Vector<f32,4>` là logical vector.

Target backend quyết định:

```text
XMM
YMM
scalar
multiple registers
```

---

# 29. SIMD intrinsics vẫn cần

Systems programmers đôi khi cần instruction-specific features:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
```

Có thể:

```text
std.simd
std.arch.x86
std.arch.arm
```

và unsafe/intrinsic APIs.

Core chỉ cần abstraction đủ để compiler hiểu vector operations.

---

# 30. Explicit layout assertions

Rất hữu ích cho systems/FFI:

```axiom
const _: assert(size_of<Foo>() == 16);
const _: assert(align_of<Foo>() == 8);
```

hoặc compiler directive:

```axiom
@assert_size(Foo, 16)
@assert_align(Foo, 8)
```

Tôi thích compile-time assertion hơn việc tạo thêm nhiều `repr`.

---

# 31. Stable layout

Mặc định:

```text
struct Foo
```

→ layout **không phải stable ABI contract**.

Nếu:

```axiom
@repr(C)
struct Foo
```

→ C-compatible layout.

Nếu:

```axiom
@repr(transparent)
struct UserId(u64)
```

→ transparent ABI representation.

Do đó public library có thể thay đổi internal layout nếu không expose representation contract.

---

# 32. Public API không đồng nghĩa public layout

Ví dụ:

```axiom
pub struct User {
    name: Text
    age: i32
}
```

Một package khác có thể dùng:

```text
User
```

nhưng không nhất thiết được phép:

```text
offsetof(User, age)
```

nếu layout không stable.

Điều này cho compiler freedom rất lớn.

---

# 33. FFI boundary bắt buộc representation rõ

Ví dụ:

```axiom
@repr(C)
extern struct CPoint {
    x: f32
    y: f32
}
```

hoặc:

```axiom
extern fn c_function(x: CPoint) -> i32;
```

Compiler biết:

```text
FFI boundary
↓
stable representation required
```

Không được đưa arbitrary Axiom struct layout qua C ABI.

---

# 34. Raw byte access

Axiom vẫn cần khả năng cực thấp-level:

```axiom
unsafe {
    let p: *mut u8 = ...;
}
```

Nhưng:

```text
raw bytes
```

không automatically become typed object.

Programmer phải thực hiện conversion/reinterpretation đúng semantics.

Điều này giữ safe type system sạch.

---

# 35. `transmute` không nên tồn tại dưới dạng “joker”

Tôi không muốn:

```axiom
unsafe {
    transmute<A, B>(x)
}
```

là công cụ phổ biến.

Nếu cần:

```text
bit reinterpretation
```

thì API phải kiểm tra:

```text
size
alignment
valid bit patterns
```

Ví dụ:

```axiom
bitcast<u32>(f32_value)
```

có semantics rõ:

```text
same bits
different interpretation
```

Khác với:

```text
numeric conversion
```

---

# 36. Ba loại conversion phải tách biệt

Đây là điểm nên freeze:

```text
VALUE CONVERSION
    i32 → i64

BIT CAST
    f32 → u32

POINTER CAST
    *T → *U
```

Không dùng một operation mơ hồ cho cả ba.

Conceptually:

```text
as
bitcast
ptr_cast
```

hoặc syntax tương đương.

---

# 37. Stable-address types

Layout không giải quyết address stability.

Ví dụ:

```axiom
Box<T>
```

có semantic:

```text
stable dynamic storage
```

nếu address exposed.

Trong khi:

```text
Vec<T>
```

có thể relocate.

Do đó:

```text
representation stability
≠
address stability
```

Hai contract phải độc lập.

---

# 38. Compiler freedom matrix

Tôi đề xuất bảng nguyên tắc:

| Source | Layout | Address | ABI |
|---|---|---|---|
| `struct Foo` | compiler | compiler | compiler |
| `@repr(C) Foo` | C-compatible | compiler | C-compatible |
| `@repr(transparent)` | underlying | compiler | transparent |
| `Box<T>` | compiler | stable khi exposed | compiler |
| `Vec<T>` | compiler | có thể relocate | compiler |
| `dyn Trait` | implementation-defined | runtime object | dynamic ABI |
| `@repr(packed)` | explicit packed | explicit | system-level |

---

# 39. Representation invariants

Tôi đề xuất thêm:

### AREP-01 — Semantic/Representation Separation
Type semantics không phụ thuộc machine layout trừ khi representation contract được công bố.

### AREP-02 — Compiler Layout Freedom
Layout mặc định thuộc quyền compiler.

### AREP-03 — Explicit Stable Representation
FFI/stable ABI phải yêu cầu representation contract.

### AREP-04 — No Mandatory Object Header
Không type nào tự động có header.

### AREP-05 — Enum Optimization Freedom
Compiler được dùng niche/tag compression khi semantics không thay đổi.

### AREP-06 — Alignment Correctness
Mọi generated access phải tuân thủ alignment contract.

### AREP-07 — Packed Is Explicit
Packed representation thuộc system/unsafe domain.

### AREP-08 — Endian Independence
Integer semantics không phụ thuộc endian.

### AREP-09 — ABI Separation
Type layout không đồng nhất với ABI classification.

### AREP-10 — No Joker Reinterpretation
Bitcast/numeric conversion/pointer cast là các semantic operations khác nhau.

### AREP-11 — Representation Assertions
Programmer có thể kiểm chứng layout bằng compile-time assertions.

### AREP-12 — Abstraction Erasure
Strong types/newtypes/generic wrappers không tạo overhead nếu representation contract cho phép loại bỏ.

---

# 40. Một điểm tôi muốn thay đổi nhẹ so với hướng trước

Trước đây ta có xu hướng:

```text
@repr(packed)
```

được coi là một attribute khá đơn giản.

Sau khi nhìn toàn bộ representation model, tôi nghĩ nên phân loại attributes thành:

```text
Semantic attributes
Representation attributes
ABI attributes
Target attributes
Optimization hints
```

Ví dụ:

```text
@repr(C)        → representation/ABI
@repr(packed)   → representation
@align(64)      → representation
@inline         → optimization hint
@cold           → optimization/codegen
@export("foo")  → ABI/linkage
```

Compiler phải biết attribute nào là **semantic contract** và attribute nào chỉ là **optimization request**.

Không được để:

```text
@inline
```

vô tình trở thành correctness requirement.

---

# 41. Toàn bộ representation pipeline

Đến đây kiến trúc compiler khá đẹp:

```text
                 TYPE SYSTEM
                      │
                      ▼
              Semantic Type
                      │
                      ▼
              Representation
                 ┌────┴────┐
                 │         │
             implicit    explicit
              layout      repr
                 │         │
                 └────┬────┘
                      ▼
                 Type Layout
                      │
             ┌────────┴────────┐
             │                 │
          ABI Lowering    Optimization
             │                 │
             └────────┬────────┘
                      ▼
                 Axiom LIR
                      │
                      ▼
                Machine IR
```

Điểm quan trọng là **MIR vẫn giữ semantic type**, còn LIR bắt đầu mất dần abstraction.

---

## Và tôi nghĩ chúng ta đã đến một mốc khá quan trọng

Hiện Axiom đã có gần đủ **semantic foundation**:

```text
              AXIOM CORE
                  │
     ┌────────────┼────────────┐
     │            │            │
   TYPES      OWNERSHIP     CONTROL
     │            │            │
 struct        Move/Copy     match
 enum          Drop          loop
 generic       View          async
 trait         Region        closure
     │            │            │
     └────────────┼────────────┘
                  │
             REPRESENTATION
                  │
        ┌─────────┼─────────┐
        │         │         │
      layout     ABI      machine
```

**Phần tiếp theo tôi muốn đi vào là `Error / Result / Panic / Exception model`**, vì nó liên kết trực tiếp với:

- `never`
- `Drop`
- deterministic cleanup
- zero-runtime-cost
- async
- FFI
- OS-level programming.

Đặc biệt cần quyết định một vấn đề lớn: **Axiom có nên có `?` operator không, và nếu có thì nó phải lower thế nào để không tạo exception/runtime overhead.** Đây cũng là nơi ta có thể khóa hẳn nguyên tắc **“recoverable error ≠ panic ≠ hardware trap ≠ process termination”**.