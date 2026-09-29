Tiếp tục. Phần này rất quan trọng vì **ABI + Data Layout** là cầu nối trực tiếp từ semantic của Axiom xuống CPU.

Tôi sẽ giữ nguyên các quyết định đã freeze trước đó và chỉ bổ sung phần chưa có.

# AXIOM ABI & DATA LAYOUT v0.1

**Trạng thái: PROPOSED**

## 1. Nguyên tắc nền tảng

Axiom phải phân biệt rõ:

```text
TYPE SEMANTICS
      │
      ▼
DATA REPRESENTATION
      │
      ▼
ABI REPRESENTATION
      │
      ▼
MACHINE REPRESENTATION
```

Một type có semantic:

```text
struct Point {
    x: f32
    y: f32
}
```

không có nghĩa compiler bắt buộc phải tạo:

```text
memory:
+0 x
+4 y
```

Nếu function chỉ cần `x` và `y`, compiler có thể giữ chúng trong:

```text
XMM0
XMM1
```

hoặc thậm chí tối ưu toàn bộ struct biến mất.

Vì vậy:

> **Source-level type layout và physical storage phải được tách biệt, trừ khi programmer yêu cầu ABI/layout ổn định.**

---

# 2. Ba loại layout

Tôi đề xuất Axiom có ba chế độ.

| Layout | Mục đích |
|---|---|
| `native` | compiler tự tối ưu |
| `repr(C)` | tương thích C ABI |
| `repr(...)` | programmer yêu cầu layout cụ thể |

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

là:

```text
native
```

Compiler tự quyết định.

Còn:

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

thì layout phải tương thích C.

---

# 3. Native layout

Đây nên là default.

Compiler được phép:

- reorder field nếu semantic cho phép
- thêm padding
- chọn alignment
- scalarize
- split aggregate
- pass bằng register
- eliminate aggregate
- thay đổi physical representation

Nhưng có một giới hạn quan trọng:

> Nếu programmer có thể quan sát layout thông qua safe language semantics thì compiler không được thay đổi nó tùy tiện.

Vì vậy tôi đề xuất:

### Native layout không được phép expose raw field offset.

Ví dụ không có:

```axiom
offset_of(Point.x)
```

trừ khi type có explicit representation.

---

# 4. `repr(C)`

Dùng cho:

- FFI
- OS API
- shared library ABI
- binary protocol structures
- hardware structures
- interoperability.

Ví dụ:

```axiom
@repr(C)
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

Compiler phải giữ:

```text
field order
alignment
padding
size
ABI rules
```

theo C-compatible representation.

---

# 5. `repr(packed)`

Tôi **không muốn cho phép packed struct một cách tùy tiện trong safe code**.

Ví dụ:

```text
@repr(packed)
struct Header {
    flag: u8
    value: u32
}
```

có thể tạo unaligned access.

CPU x86 có thể chịu được một số trường hợp.

ARM có thể có vấn đề hoặc performance penalty.

Do đó:

```text
packed
```

nên thuộc unsafe/system-level representation.

---

# 6. Alignment

Axiom phải có alignment semantics rõ ràng.

Ví dụ:

```text
u8  → alignment 1
u16 → alignment 2
u32 → alignment 4
u64 → alignment 8
```

nhưng không nên đóng băng tất cả target-specific alignment thành language rule.

Có:

```text
natural alignment
```

và target backend quyết định ABI cụ thể.

---

# 7. Struct layout

Ví dụ:

```axiom
struct A {
    a: u8
    b: u64
    c: u8
}
```

Compiler có thể tạo layout kiểu:

```text
offset 0 : a
offset 1-7 : padding
offset 8 : b
offset 16 : c
offset 17-23 : padding
```

size = 24.

Nhưng với native layout, programmer không được dựa vào con số này.

---

# 8. Compiler có thể reorder field?

Tôi đề xuất:

**Có, nhưng chỉ với native-layout types.**

Ví dụ:

```axiom
struct A {
    a: u8
    b: u64
    c: u8
}
```

compiler có thể thấy:

```text
u8
u8
u64
```

giúp giảm size.

Nhưng cần cẩn thận: nếu destructor/field evaluation order có semantic observable effects thì reorder physical layout không được làm thay đổi **destruction order semantic**.

Đây là một ví dụ điển hình:

```text
logical field order
≠
physical field order
```

---

# 9. Field order và Drop order

Ta phải giữ distinction:

```text
source order
```

và:

```text
physical memory order
```

Drop vẫn theo:

```text
semantic declaration order
```

ví dụ:

```axiom
struct X {
    a: ResourceA
    b: ResourceB
}
```

khi destruction:

```text
DROP b
DROP a
```

dù compiler physical layout có thể là:

```text
b
a
```

hoặc:

```text
a
padding
b
```

---

# 10. Value representation

Axiom nên coi:

```text
T
```

là một semantic value.

Compiler có thể biểu diễn nó bằng:

```text
register
stack
memory
multiple registers
multiple memory locations
constant
nothing
```

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

có thể trở thành:

```text
XMM0 = x
XMM1 = y
```

không cần memory.

---

# 11. Zero-sized types

Nên hỗ trợ.

Ví dụ:

```axiom
struct Marker {}
```

có thể có:

```text
size = 0
```

về semantic representation.

Compiler không cần cấp memory thực tế nếu không cần.

Điều này hữu ích cho:

- marker types
- compile-time capabilities
- phantom-like generic types
- empty state
- type-level configuration.

---

# 12. Arrays

Fixed array:

```axiom
Array<T, N>
```

semantic:

```text
N elements
```

Nếu `T` có size `S`:

```text
size ≈ N × stride(T)
```

nhưng compiler vẫn có thể optimize.

Ví dụ:

```axiom
let a: Array<i32, 4>
```

có thể trở thành:

```text
r0
r1
r2
r3
```

nếu escape analysis cho phép.

---

# 13. Slice / view

Đây là nơi `view<T>` rất quan trọng.

Conceptual ABI:

```text
view<T>
+----------------+
| address        |
+----------------+
| length         |
+----------------+
```

thường:

```text
2 machine words
```

Ví dụ x86-64:

```text
RDI = pointer
RSI = length
```

nhưng Axiom ABI **không nên đóng băng x86 register cụ thể trong language semantics**.

---

# 14. `mut_view<T>`

Representation có thể giống:

```text
pointer + length
```

nhưng semantic khác:

```text
view<T>
    read-only

mut_view<T>
    exclusive mutable access
```

Đây là ví dụ rất hay về:

> **same physical representation, different type semantics.**

---

# 15. String

Tôi vẫn không muốn `String` là primitive.

Nên tách:

```text
Bytes
Text
String
StringView
```

ở library/type-system level.

Một `StringView` có thể về ABI gần:

```text
pointer + byte_length
```

nhưng Unicode semantics thuộc Text library.

Điều này tránh nhét Unicode runtime vào core.

---

# 16. Option representation

Đây là một optimization rất quan trọng.

Ví dụ:

```axiom
Option<*mut T>
```

không nhất thiết cần:

```text
tag + pointer
```

Compiler có thể dùng:

```text
null pointer = None
non-null = Some
```

nhưng **chỉ khi representation đó không phá semantic guarantees**.

Tương tự:

```text
Option<NonZeroU64>
```

có thể tận dụng giá trị `0` làm discriminant.

Đây thường được gọi là niche optimization.

---

# 17. Nhưng native representation không được observable

Ví dụ:

```axiom
Option<u64>
```

compiler có thể dùng:

```text
tag + value
```

hoặc:

```text
optimized encoding
```

Programmer không được viết code giả định:

```text
sizeof(Option<u64>) == ...
```

trừ khi Axiom specification explicitly đảm bảo.

Điều này cho optimizer rất nhiều tự do.

---

# 18. Enum

Ví dụ:

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Semantic:

```text
discriminant
+
payload
```

Physical layout:

```text
compiler-defined
```

với explicit representation nếu cần FFI.

---

# 19. Function ABI

Axiom function:

```axiom
fn add(a: i32, b: i32) -> i32
```

không nên mặc định có:

```text
Axiom runtime call wrapper
```

Compiler hạ trực tiếp xuống target calling convention.

Ví dụ x86-64 có thể dùng register ABI.

ARM64 dùng register ABI tương ứng.

---

# 20. Calling convention

Axiom nên có:

```text
@abi(axiom)
```

là default.

Ngoài ra:

```text
@abi(C)
@abi(system)
@abi(platform)
```

tùy target.

Ví dụ:

```axiom
extern @abi(C) fn malloc(size: usize) -> *mut u8
```

Cần tránh syntax quá phức tạp; exact spelling có thể chốt ở FFI spec.

---

# 21. Return values

Compiler phải hỗ trợ:

```text
scalar return
aggregate return
hidden return pointer
multi-register return
```

nhưng programmer chỉ thấy:

```axiom
fn make_point() -> Point
```

Không cần:

```text
out parameter
```

trong source.

---

# 22. Return Value Optimization

Ví dụ:

```axiom
fn make() -> BigStruct {
    return BigStruct(...)
}
```

Axiom không nên tạo:

```text
temporary
copy
return copy
destroy temporary
```

một cách máy móc.

Compiler có thể:

```text
caller allocates result storage
          ↓
callee constructs directly
```

hoặc register-return nếu nhỏ.

---

# 23. No implicit object pointer

Vì Axiom không có class/object model nên:

```axiom
fn move(self: Vec2, dx: f32)
```

không có hidden:

```text
this
vptr
object header
runtime metadata
```

Method syntax:

```axiom
v.move(1)
```

chỉ là sugar cho:

```axiom
move(v, 1)
```

---

# 24. Trait object

Nếu:

```axiom
dyn Drawable
```

được sử dụng, lúc đó mới có dynamic dispatch metadata.

Conceptual:

```text
+----------------+
| data pointer   |
+----------------+
| dispatch ptr   |
+----------------+
```

Có thể sau này chứa:

```text
drop function
method table
type metadata
```

Nhưng chỉ dynamic abstraction mới phải trả giá.

---

# 25. Generic types

Generic:

```axiom
struct Vec<T> {
    data: ...
}
```

không mặc định có runtime type information.

Sau monomorphization:

```text
Vec<i32>
Vec<f64>
Vec<MyStruct>
```

là các specialized machine representations.

Không có:

```text
T's runtime descriptor
```

trừ khi programmer explicitly yêu cầu runtime type information.

---

# 26. FFI boundary

FFI phải cực kỳ rõ.

Ví dụ:

```axiom
@repr(C)
struct CPoint {
    x: f64
    y: f64
}

extern @abi(C) fn c_process(p: *const CPoint)
```

Compiler biết:

```text
layout
alignment
calling convention
pointer semantics
```

nhưng `unsafe` boundary chịu trách nhiệm về validity.

---

# 27. ABI stability

Axiom nên phân biệt:

```text
source compatibility
binary compatibility
ABI compatibility
```

Một module build bằng:

```text
Axiom compiler 0.1
```

không nhất thiết binary-compatible với:

```text
Axiom compiler 0.2
```

nếu dùng native ABI.

Muốn ABI ổn định:

```text
C ABI
```

hoặc một:

```text
Axiom Stable ABI
```

sẽ được định nghĩa riêng sau.

Tôi **không khuyên freeze Stable Axiom ABI quá sớm**.

---

# 28. Data layout và flat memory

Bây giờ quay lại vấn đề bạn từng đặt ra:

> "Flat memory có nhanh hơn và tránh fragmentation không?"

Câu trả lời chính xác là:

**Không phải trực tiếp.**

Flat address space:

```text
0x0000
...
0xFFFF
```

chỉ là cách CPU nhìn memory.

Fragmentation phụ thuộc vào:

```text
allocator
allocation lifetime
allocation size
reuse strategy
object locality
```

Ví dụ hai allocator đều chạy trên flat address space:

```text
General malloc
Arena allocator
```

có fragmentation behavior hoàn toàn khác.

---

# 29. Axiom nên chọn memory strategy nào?

Tôi không khuyên chọn **một allocator duy nhất**.

Thay vào đó:

```text
                 Axiom Memory
                      │
        ┌─────────────┼─────────────┐
        │             │             │
       Stack        Heap          Arena
        │             │             │
      local       long-lived     batch
                    │
              ┌─────┴─────┐
              │           │
            Pool         Custom
```

Compiler/runtime/library có thể chọn.

---

# 30. Điều Axiom thực sự cần tối ưu

Không phải:

> "mọi object đều nằm trong một flat heap"

mà là:

> **Không ép programmer sử dụng heap khi semantic không cần heap.**

Ví dụ:

```axiom
fn foo() {
    let p = Point(...)
}
```

lý tưởng:

```text
register
```

hoặc:

```text
stack
```

không phải:

```text
heap allocation
```

---

# 31. Allocation hierarchy

Tôi đề xuất Axiom compiler ưu tiên:

```text
Register
   ↓
Inline
   ↓
Stack
   ↓
Arena/Pool
   ↓
Heap
   ↓
OS/External resource
```

Nhưng đây **không phải semantic guarantee**.

Compiler được phép thay đổi.

---

# 32. Một ví dụ cực kỳ quan trọng

Source:

```axiom
fn process() {
    let data = Buffer(1024)

    transform(data)

    save(data)
}
```

Không nên suy luận:

```text
Buffer
 ↓
heap
 ↓
malloc
 ↓
free
```

Compiler có thể phát hiện:

```text
data không escape
```

và chọn:

```text
stack/arena
```

Hoặc nếu `Buffer` cần dynamic size:

```text
heap
```

Nhưng allocator có thể dùng:

```text
thread-local arena
```

thay vì general malloc.

---

# 33. Đây là lợi thế của ownership model

Compiler biết:

```text
who owns object
when object dies
whether it escapes
whether it is shared
```

nên có đủ thông tin để tối ưu allocator.

Đây là lý do tôi đánh giá:

> **Ownership semantics trong Axiom không chỉ để memory safety; nó còn là information cho optimizer.**

---

# 34. ABI invariants

Tôi đề xuất:

```text
AABI-01
Native layout is compiler-controlled unless explicitly represented.

AABI-02
Explicit representation makes required layout observable and stable.

AABI-03
repr(C) provides C-compatible layout and ABI semantics.

AABI-04
Physical representation may differ from source abstraction when semantics permit.

AABI-05
Field physical order does not define destruction order.

AABI-06
Compiler may scalarize aggregates.

AABI-07
Compiler may eliminate aggregate storage.

AABI-08
Compiler may return aggregates in registers when target ABI permits.

AABI-09
Compiler may use hidden return storage when required by target ABI.

AABI-10
Generic types do not require runtime type metadata.

AABI-11
Dynamic dispatch metadata exists only at explicit dynamic abstraction boundaries.

AABI-12
No mandatory object header exists.

AABI-13
No mandatory heap allocation exists.

AABI-14
Axiom core does not mandate a single allocator.

AABI-15
FFI types must use explicit ABI/layout contracts.

AABI-16
Native ABI stability is not guaranteed unless explicitly specified.

AABI-17
Compiler may change physical storage without changing source semantics.

AABI-18
Unsafe code may access explicit representations only under applicable layout guarantees.
```

---

# 35. Một quyết định cần đặc biệt chú ý

Tới đây tôi thấy có một nguyên tắc rất mạnh đang hình thành:

### Axiom không nên có "reference type" như một primitive storage model.

Thay vào đó:

```text
Value
View
Mutable View
Pointer
```

là đủ.

```text
Value
```

là mặc định.

```text
view<T>
```

là non-owning read access.

```text
mut_view<T>
```

là non-owning mutable access.

```text
*T
```

là raw pointer trong unsafe.

Điều này làm type system đơn giản hơn rất nhiều.

---

# 36. Kiến trúc hiện tại

Ta đã có một tầng rất rõ:

```text
                    SOURCE
                       │
                ┌──────┴──────┐
                │   TYPE      │
                │  SEMANTICS  │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │   MEMORY    │
                │  OWNERSHIP  │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │ CONCURRENCY │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │     MIR     │
                └──────┬──────┘
                       │
               VERIFIED MIR
                       │
                ┌──────▼──────┐
                │ OPTIMIZER   │
                └──────┬──────┘
                       │
                    Axiom LIR
                       │
                ┌──────▼──────┐
                │     ABI     │
                │   LOWERING  │
                └──────┬──────┘
                       │
                 MACHINE CODE
```

Điểm đáng chú ý là **ABI nằm sau optimizer**, chứ không nên để source-level programmer phải suy nghĩ về register/stack/hidden return pointer.

---

## Bước tiếp theo tôi đề xuất

Sau ABI, **chưa nên viết Standard Library**.

Ta nên khóa một thứ còn nền tảng hơn:

### `AXIOM EXECUTION & ERROR SEMANTICS v0.1`

Nó sẽ quyết định chính xác:

- `panic`
- `trap`
- `Result`
- `Option`
- `return`
- `defer` có cần hay không
- cleanup khi early return
- cleanup khi panic
- integer overflow
- divide-by-zero
- bounds check
- unreachable
- assertion
- process abort
- exception có hoàn toàn bị loại khỏi core không
- debug vs release behavior
- deterministic evaluation order

Đặc biệt, tôi muốn xử lý **`defer` thật kỹ trước khi loại bỏ hoặc giữ nó**, vì với mục tiêu của Axiom, một cơ chế cleanup đơn giản có thể rất hữu ích — nhưng nếu thiết kế sai, nó sẽ phá deterministic destruction và làm compiler khó tối ưu.