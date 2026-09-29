# BOOTSTRAP-417 — ABI, CALLING CONVENTION, DATA LAYOUT & BINARY COMPATIBILITY

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 409 Type System, 410 Trait/Method Resolution, 413 MIR, 415 Drop, 416 Optimization  
**Mục tiêu:** định nghĩa chính xác cách Axiom biến **semantic types + functions + resources** thành ABI có thể gọi được từ machine code, thư viện native và ngôn ngữ khác.

Đây là bước bắt buộc trước khi đi sâu vào LIR/codegen.

---

## 417.1. Tách 4 khái niệm

Axiom phải tuyệt đối phân biệt:

```text
Type Identity
Representation
Layout
ABI
```

Ví dụ:

```text
struct Vec2 {
    x: f32
    y: f32
}
```

`Vec2` có thể có:

```text
Type Identity:
    Vec2

Representation:
    two f32

Layout:
    offset(x)=0
    offset(y)=4
    size=8
    align=4

ABI:
    có thể truyền qua 2 FP registers
    hoặc một aggregate register
    tùy target
```

Do đó:

> Layout không phải ABI.

---

# 417.2. ABI không phải Core Type System

Type system nói:

```text
fn add(a: Vec2, b: Vec2) -> Vec2
```

ABI quyết định:

```text
argument registers
return registers
stack layout
alignment
calling convention
aggregate passing
```

Không được để target ABI làm thay đổi semantic type.

---

# 417.3. Default Axiom ABI

Axiom có:

```text
ABI = "axiom"
```

Đây là ABI mặc định cho code Axiom ↔ Axiom.

Mục tiêu:

- tối ưu;
- compact;
- deterministic;
- dễ compiler tự sinh;
- không phụ thuộc C ABI.

---

# 417.4. Explicit External ABI

FFI phải chỉ rõ:

```axiom
extern "C" fn foo(...)
```

hoặc:

```axiom
extern "system" fn foo(...)
```

Các ABI chuẩn có thể gồm:

```text
"C"
"system"
"stdcall"
"fastcall"
"vectorcall"
"wasm"
"platform"
```

Danh sách cụ thể phụ thuộc target backend.

---

# 417.5. ABI Contract

Mỗi externally visible function có:

```text
AbiFunctionContract {
    calling_convention
    parameter_abi
    return_abi
    aggregate_rules
    alignment_rules
    unwind_behavior
    ownership_contract
    effect_contract
}
```

---

# 417.6. Function ABI

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

Semantic:

```text
i32 + i32 → i32
```

ABI target có thể:

```text
arg0 = register
arg1 = register
return = register
```

Không cần programmer biết.

---

# 417.7. Large Aggregate Return

Ví dụ:

```axiom
fn create() -> HugeStruct
```

ABI có thể chọn:

```text
return registers
```

nếu nhỏ, hoặc:

```text
hidden caller-allocated result pointer
```

nếu lớn.

Điểm quan trọng:

> Hidden ABI parameter không phải source-level parameter.

---

# 417.8. Caller-Allocated Return

Ví dụ:

```text
create() -> HugeStruct
```

có thể lower thành semantic ABI:

```text
create(result_storage: *mut HugeStruct)
```

nhưng pointer này chỉ tồn tại ở ABI/Machine level.

Programmer không phải viết pointer.

---

# 417.9. Ownership của Return Storage

Nếu function:

```axiom
fn make() -> Resource
```

trả ownership:

```text
caller owns returned Resource
```

Nếu ABI dùng hidden result pointer:

```text
callee initializes caller storage
```

Sau đó ownership transfer:

```text
callee
   ↓
caller
```

phải được ghi trong ABI contract.

---

# 417.10. Parameter Ownership

Function:

```axiom
fn consume(x: Resource)
```

semantic:

```text
caller ownership
        ↓
callee ownership
```

ABI chỉ truyền representation.

Compiler phải giữ ownership semantics ở MIR.

---

# 417.11. Borrow/View ABI

```axiom
fn read(x: view<T>)
```

`view<T>` semantic có:

```text
provenance
region
access=READ
```

Nhưng ABI có thể chỉ cần:

```text
pointer
length
```

hoặc:

```text
pointer
metadata
```

Tùy representation.

Provenance là semantic compiler metadata, không nhất thiết là machine bits.

---

# 417.12. `mut_view<T>`

Có thể ABI thành:

```text
pointer
length
```

nhưng compiler semantic contract vẫn phải ghi:

```text
exclusive WRITE capability
```

Không được vì ABI chỉ thấy pointer mà bỏ qua capability.

---

# 417.13. View Metadata

Các dạng view:

```text
view<T>
view<T, N>
slice<T>
strided_view<T>
tensor_view<T>
```

có thể có metadata:

```text
pointer
length
stride
shape
layout
```

Nhưng metadata nào tồn tại runtime phải phụ thuộc type.

---

# 417.14. Zero-Sized Types

Ví dụ:

```axiom
struct Marker {}
```

có:

```text
size = 0
```

Compiler không được bắt buộc allocate byte vật lý chỉ vì value tồn tại.

ABI có thể:

```text
pass nothing
return nothing
```

nếu target convention cho phép.

---

# 417.15. Empty Struct

Tương tự:

```axiom
struct Empty {}
```

không nhất thiết chiếm storage.

Nếu địa chỉ identity được yêu cầu:

```text
storage contract
```

thì mới cần representation phù hợp.

---

# 417.16. Alignment

Mỗi type có:

```text
size
alignment
```

Layout phải thỏa:

```text
offset(field) % alignment(field) == 0
```

trừ explicit packed representation.

---

# 417.17. Struct Layout mặc định

Mặc định:

```text
struct S {
    a: u8
    b: u64
    c: u16
}
```

**không đảm bảo** source order == physical order.

Compiler được phép reorder để:

- giảm padding;
- cải thiện locality;
- vectorization;
- cache behavior.

Trừ khi representation contract yêu cầu.

---

# 417.18. Explicit Representation

Axiom hỗ trợ:

```axiom
@repr(C)
struct Packet {
    ...
}
```

Khi đó:

```text
C-compatible layout
```

được khóa.

Các dạng:

```text
@repr(C)
@repr(transparent)
@repr(packed)
@repr(align(N))
```

---

# 417.19. `repr(C)`

`repr(C)` phải khóa:

- field order;
- alignment rules;
- padding rules;
- enum representation theo ABI contract;
- aggregate ABI compatibility ở mức cần thiết.

Mục đích:

```text
Axiom ↔ C/C++/Rust/etc.
```

---

# 417.20. `repr(transparent)`

Ví dụ:

```axiom
@repr(transparent)
struct UserId {
    value: u64
}
```

Semantic type:

```text
UserId != u64
```

nhưng ABI representation:

```text
UserId ≈ u64
```

Điều này rất quan trọng cho:

- newtype;
- type-safe handles;
- FFI.

---

# 417.21. Packed Representation

```axiom
@repr(packed)
struct Header {
    ...
}
```

Cho phép alignment thấp hơn bình thường.

Nhưng compiler phải cảnh báo/kiểm soát:

```text
unaligned access
```

Không được biến packed field thành ordinary aligned load nếu ABI yêu cầu byte-level representation.

---

# 417.22. Struct ABI Classification

Mỗi target có thể phân loại aggregate:

```text
INTEGER
FLOAT
VECTOR
MEMORY
MIXED
```

Ví dụ:

```text
Vec2<f32>
```

có thể:

```text
FLOAT/FLOAT
```

trong registers.

Một struct lớn có thể:

```text
MEMORY
```

---

# 417.23. Tuple ABI

Tuple:

```axiom
(i32, f64, i32)
```

semantic là structural type.

ABI classifier quyết định:

```text
registers
stack
aggregate
```

Không cần tạo runtime tuple object nếu không escape.

---

# 417.24. Array ABI

Fixed array:

```axiom
[u32; 4]
```

là inline value.

Compiler có thể truyền:

```text
registers
```

hoặc:

```text
memory
```

tùy target.

Không tự động biến thành pointer.

---

# 417.25. Enum ABI

Ví dụ:

```axiom
enum Option<T> {
    None
    Some(T)
}
```

Compiler có thể dùng:

```text
tag + payload
```

nhưng representation không nhất thiết là một object.

---

# 417.26. Niche Optimization

Ví dụ semantic:

```text
Option<Box<T>>
```

Nếu `Box<T>` có representation với giá trị machine-level có thể dành một niche cho `None`, compiler có thể biểu diễn:

```text
Option<Box<T>>
```

bằng một machine word thay vì:

```text
tag + pointer
```

Nhưng đây là **representation optimization**, không thay đổi semantic `Option`.

---

# 417.27. Enum Layout Không Được Lộ Nếu Không Có Contract

Programmer không được giả định:

```text
enum layout
```

trừ khi:

```text
@repr(...)
```

hoặc API/compiler contract quy định.

Điều này cho phép optimizer thay đổi layout.

---

# 417.28. Function Pointer

Axiom có function value:

```text
fn(i32) -> i32
```

Representation có thể là:

```text
code pointer
```

hoặc target-specific pair nếu closure/environment cần thiết.

Function pointer và closure value phải phân biệt semantic type.

---

# 417.29. Closure ABI

Closure:

```axiom
let f = |x| x + captured
```

có semantic:

```text
code
environment
```

ABI có thể:

```text
{ code_ptr, env_ptr }
```

nhưng compiler có thể:

- inline;
- specialize;
- eliminate environment;
- convert to direct function.

---

# 417.30. `dyn Trait` ABI

Dynamic trait object là explicit.

Conceptually:

```text
data pointer
dispatch metadata
```

Có thể là:

```text
data_ptr
vtable_ptr
```

nhưng representation không được coi là Core language syntax.

Vtable có thể chứa:

```text
drop
size
align
method pointers
type metadata
```

tùy ABI.

---

# 417.31. Trait Object Safety

Trait chỉ có thể trở thành:

```text
dyn Trait
```

nếu compiler chứng minh trait ABI-compatible với dynamic dispatch.

Các item không phù hợp có thể bị loại khỏi dyn interface hoặc khiến trait không dyn-compatible.

Ví dụ generic method không có type-erased ABI rõ ràng:

```text
fn foo<T>(...)
```

không thể tự động trở thành vtable slot.

---

# 417.32. Generic ABI

Generic function:

```axiom
fn max<T: Ordered>(...)
```

sau monomorphization:

```text
max_i32
max_f64
max_UserType
```

mỗi specialization có ABI cụ thể.

Generic interface artifact phải chứa đủ metadata để compiler khác tiếp tục specialize.

---

# 417.33. ABI Stable Generic

Không mặc định coi:

```text
generic function
```

là stable binary ABI.

Muốn binary-compatible generic interface cần explicit contract.

Điều này tránh khóa compiler vào representation nội bộ.

---

# 417.34. ABI Stability Levels

Axiom định nghĩa:

```text
Source Compatible
Semantic Compatible
ABI Compatible
Binary Compatible
```

khác nhau.

### Source compatible

Code vẫn compile.

### Semantic compatible

Hành vi language-level giữ tương thích.

### ABI compatible

Calling/layout contracts giữ nguyên.

### Binary compatible

Artifact cũ có thể link/chạy với artifact mới theo contract.

---

# 417.35. Internal ABI

Trong cùng compilation unit:

```text
Axiom ABI
```

có thể thay đổi tự do bởi optimizer.

Không cần stable.

---

# 417.36. Package ABI

Giữa binary packages:

```text
Package ABI
```

có versioning.

Interface artifact chứa:

```text
ABI fingerprint
```

Compiler kiểm tra mismatch.

---

# 417.37. ABI Fingerprint

Ví dụ:

```text
AbiFingerprint {
    target
    pointer_width
    endian
    calling_convention
    type_layout_hash
    exported_function_hash
    enum_representation
    alignment
    unwind_model
}
```

Nếu mismatch:

```text
ABI incompatible
```

compiler không link silent.

---

# 417.38. Symbol Naming

Axiom internal symbol:

```text
package::module::function
```

không nhất thiết là linker symbol.

Compiler có:

```text
Semantic SymbolId
```

và:

```text
Linker Symbol
```

mapping.

---

# 417.39. Name Mangling

Default Axiom ABI có mangling chứa đủ identity cần thiết:

```text
package
module
function
generic specialization
ABI version
```

Nhưng không nhất thiết expose semantic implementation details.

---

# 417.40. `extern` Symbol

FFI:

```axiom
extern "C" {
    fn printf(...)
}
```

symbol có thể:

```text
printf
```

không mangling Axiom.

---

# 417.41. Calling Convention

Function ABI phải xác định:

```text
integer arguments
floating arguments
vector arguments
aggregate arguments
return values
variadic arguments
stack alignment
callee/caller saved registers
shadow space
stack cleanup
```

Tất cả target-specific.

---

# 417.42. Variadic Functions

Variadic:

```axiom
extern "C" fn printf(format: *const u8, ...)
```

chỉ hợp lệ với ABI hỗ trợ variadic.

Core type system không nên cố mô phỏng C varargs như ordinary generic tuple.

---

# 417.43. `noreturn`

Function:

```axiom
fn abort() -> never
```

ABI/codegen có thể đánh dấu:

```text
noreturn
```

để:

- loại bỏ unreachable code;
- tối ưu CFG;
- tối ưu register lifetime.

---

# 417.44. `nounwind`

Nếu function ABI contract:

```text
nounwind
```

compiler có thể bỏ unwind metadata/call edges phù hợp.

---

# 417.45. `readonly` / Effect ABI

Không nên đưa C-style qualifiers trực tiếp vào source language chỉ để optimizer.

Axiom semantic effect system đã có.

ABI artifact có thể export:

```text
effect summary
```

để optimizer module khác sử dụng.

---

# 417.46. FFI Ownership ABI

Ví dụ:

```axiom
extern "C"
fn create_handle() -> Handle
```

phải biết:

```text
caller owns result
```

và:

```axiom
extern "C"
fn destroy_handle(h: Handle)
```

có:

```text
consumes Handle
```

Nếu không có ownership contract:

```text
unsafe FFI
```

không được compiler tự giả định.

---

# 417.47. Callback ABI

Axiom function/closure truyền vào C:

```text
C callback
```

phải có:

```text
extern-compatible function ABI
```

Closure có capture không thể tự động truyền thành raw C function pointer nếu cần environment.

Compiler phải yêu cầu adapter/thunk:

```text
C callback
    ↓
Axiom thunk
    ↓
closure environment
```

---

# 417.48. Exception/Unwind ABI

Axiom phải định nghĩa:

```text
unwind personality
landing pad representation
panic ABI
```

theo target.

Nhưng Core semantics chỉ cần:

```text
panic
trap
abort
unwind
```

Backend chịu trách nhiệm mapping.

---

# 417.49. Thread-Local ABI

`static`/TLS:

```text
thread_local
```

có ABI/storage contract riêng.

Compiler không được biến TLS thành ordinary global.

---

# 417.50. Global / Static ABI

Global object có:

```text
symbol
section
alignment
initialization
destruction
visibility
```

Dynamic initialization chỉ tồn tại nếu library/runtime model yêu cầu.

Freestanding program không bị ép có global constructor runtime.

---

# 417.51. Initialization ABI

Axiom ưu tiên:

```text
static constant initialization
```

hơn runtime initializer.

Nếu initializer compile-time được:

```text
comptime
```

thì artifact chứa dữ liệu đã materialize.

---

# 417.52. Destruction ABI

Global resource có thể cần:

```text
destructor registration
```

nhưng đây **không phải Core bắt buộc**.

Freestanding profile có thể:

```text
no global destruction runtime
```

và yêu cầu explicit resource management.

---

# 417.53. Binary Interface Artifact

Package interface nên chứa:

```text
AXABI {
    package identity
    ABI version
    target
    exported symbols
    exported types
    layouts
    calling conventions
    trait interfaces
    ownership contracts
    effects
    unwind contracts
}
```

Không cần source code.

---

# 417.54. Linker Contract

Compiler frontend/backend tạo:

```text
Object
```

Linker nhận:

```text
symbols
relocations
sections
COMDAT/linkonce
TLS
unwind info
debug info
```

Axiom linker cuối cùng sẽ hiểu semantic metadata ở mức cần thiết nhưng output vẫn là native object format.

---

# 417.55. Link-Time Optimization

Sau ABI lowering, vẫn có thể:

```text
LTO
```

nhưng LTO phải dựa trên:

```text
semantic summaries
ABI contracts
machine-level information
```

không cần source.

---

# 417.56. ABI Boundary là Optimization Boundary

Compiler không được tối ưu xuyên ABI boundary nếu semantics không cho phép.

Ví dụ:

```text
Axiom
  ↓
extern "C"
  ↓
C library
```

Không được assume C function là pure nếu contract không nói.

---

# 417.57. `extern "axiom"`

Cho phép package/binary interface dùng:

```axiom
extern "axiom"
```

để biểu diễn:

> function/type tuân theo Axiom ABI contract.

Điều này hữu ích cho dynamic libraries.

---

# 417.58. Dynamic Library

Axiom có thể export:

```text
.dll
.so
.dylib
```

với:

```text
stable exported ABI
```

nếu package chọn ABI-stable profile.

---

# 417.59. Static Library

Static library:

```text
.lib
.a
```

có thể chứa:

- machine code;
- relocation;
- debug;
- Axiom ABI metadata;
- generic/interface metadata nếu cần.

---

# 417.60. Cross-Version Compatibility

Compiler không được giả định:

```text
Axiom 1.x ↔ Axiom 2.x
```

tương thích binary.

Phải kiểm tra:

```text
ABI version
semantic compatibility
target
layout
calling convention
```

---

# 417.61. CompilerDB

Thêm:

```text
ABIDB
AbiFunctionDB
AbiTypeDB
AbiLayoutDB
AbiCallConvDB
AbiSymbolDB
AbiFingerprintDB
AbiCompatibilityDB
AbiFFIDB
AbiTraitObjectDB
AbiClosureDB
AbiGenericDB
AbiGlobalDB
AbiTLSDB
AbiUnwindDB
AbiExportDB
AbiImportDB
```

---

# 417.62. Proof Artifacts

```text
AbiLoweringProof
TypeLayoutProof
StructLayoutProof
EnumLayoutProof
CallingConventionProof
AggregatePassingProof
ReturnABIProof
OwnershipABIProof
ViewABIProof
ClosureABIProof
TraitObjectABIProof
FFIABIProof
UnwindABIProof
SymbolResolutionProof
ABICompatibilityProof
BinaryCompatibilityProof
```

---

# 417.63. Invariants `AABI`

```text id="c8q2c4"
AABI-01  Type identity is distinct from representation.
AABI-02  Representation is distinct from layout.
AABI-03  Layout is distinct from ABI.
AABI-04  ABI lowering preserves source semantics.
AABI-05  Ownership semantics survive ABI lowering.
AABI-06  View capability semantics survive ABI lowering.
AABI-07  Drop responsibility survives ABI lowering.
AABI-08  Hidden ABI parameters are never source-level parameters.
AABI-09  Aggregate passing follows target ABI rules.
AABI-10  Aggregate returns preserve ownership.
AABI-11  Zero-sized values do not require physical storage without contract.
AABI-12  Default struct layout is not assumed stable.
AABI-13  Explicit repr contracts are preserved.
AABI-14  Packed layout preserves byte-level representation.
AABI-15  Transparent representation preserves nominal type identity.
AABI-16  Dynamic trait dispatch has explicit ABI representation.
AABI-17  Generic ABI is not implicitly binary-stable.
AABI-18  FFI ABI must be explicit.
AABI-19  FFI ownership contracts must be explicit.
AABI-20  Calling convention is target-specific metadata.
AABI-21  Symbol identity is distinct from semantic SymbolId.
AABI-22  ABI fingerprints detect incompatible interfaces.
AABI-23  ABI boundaries restrict unsafe optimization assumptions.
AABI-24  Unwind behavior is part of relevant ABI contracts.
AABI-25  TLS semantics survive ABI lowering.
AABI-26  Global initialization semantics survive lowering.
AABI-27  Global destruction is not implicitly required in freestanding profiles.
AABI-28  Binary compatibility is never assumed without an ABI contract.
AABI-29  ABI-lowered MIR remains verifiable.
AABI-30  Machine code generation cannot alter ABI-visible semantics.
```

---

# 417.64. Kiến trúc hoàn chỉnh của tầng ABI

Sau 417:

```text
                    Verified MIR
                         │
                         ▼
                Semantic Optimization
                         │
                         ▼
             Optimized Verified MIR
                         │
                         ▼
                    ABI Lowering
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Type ABI    Call ABI    Data ABI
              │          │          │
              └──────────┼──────────┘
                         ▼
                     ABI MIR
                         │
                         ▼
                       LIR
                         │
                         ▼
                    Machine IR
                         │
                         ▼
                  Native Object
```

Và một nguyên tắc rất quan trọng được khóa:

> **Axiom source language không phải là “C với syntax mới”. Axiom có semantic ownership/type/capability model riêng; chỉ tại ABI boundary nó mới biến những semantics đó thành pointer, register, stack slot, vtable, calling convention và native layout cần thiết.**

Điều này cho phép Axiom giữ được mục tiêu ban đầu: **source code đơn giản, compiler thông minh, nhưng cuối cùng vẫn tạo ra native binary rất gần với mức machine code tối ưu.**

**BOOTSTRAP-417 — SPECIFIED / FROZEN.**