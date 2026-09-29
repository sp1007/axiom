# BOOTSTRAP-172 — Conversions, Casting, Coercion & Type-Safe Interoperability
**FROZEN / COMPLETED**

Mục tiêu của task này là làm rõ một vấn đề rất quan trọng của Axiom:

> **Conversion phải phân biệt rõ "đổi giá trị", "đổi kiểu nhìn", "đổi representation" và "đổi machine-level interpretation".**

Axiom không đi theo hướng C/C++ với quá nhiều implicit conversion, nhưng cũng không muốn bắt programmer viết quá nhiều boilerplate.

---

## 172.1. Bốn loại conversion

Axiom phân biệt:

```text id="v8h3qk"
COERCION
    semantic-compatible conversion
    compiler tự thực hiện

CAST
    programmer yêu cầu conversion

BITCAST
    reinterpret bits
    không đổi bit pattern

TRANSMUTE / RAW REINTERPRETATION
    machine-level operation
    unsafe/system
```

Trong đó **transmute-like operation không thuộc safe Core**.

---

# 172.2. Coercion

Coercion chỉ tồn tại khi compiler biết conversion:

```text
safe
deterministic
lossless hoặc contract-defined
không tạo unexpected side effect
```

Ví dụ điển hình:

```ax id="j8c2m4"
fn print(s: Str) { ... }

let text = String("hello");

print(text);
```

`String → Str` có thể implicit trong argument position.

Không tạo copy.

Không allocation.

Không chuyển ownership.

---

# 172.3. Coercion không phải conversion trait

Axiom không để:

```text id="0a5y7k"
x → SomeArbitraryType
```

chạy một function ngầm chỉ vì tồn tại:

```text id="m3c8p2"
From<T>
Into<T>
```

Coercion là compiler semantic rule.

Conversion trait là explicit API.

Điều này giữ cho code predictable.

---

# 172.4. Các coercion được phép

Core nên giữ danh sách nhỏ và rõ.

Ví dụ:

```text id="w4n6s1"
T
→
view<T>
```

trong ephemeral argument context.

```text id="x8p2m5"
String
→
Str
```

read-only.

```text id="q7r3v9"
Array<T,N>
→
view<T>
```

read-only.

```text id="a6k1z8"
mut-capable owner
→
mut_view<T>
```

khi capability rules cho phép.

Các coercion này không tạo ownership mới.

---

# 172.5. Numeric conversion

Không implicit chain:

```text id="p4x7m2"
i32 → f64 → u64 → ...
```

Axiom yêu cầu explicit conversion khi semantic value thay đổi.

Ví dụ:

```ax id="k2v8q5"
let x: i32 = 10;
let y: i64 = x as i64;
```

Compiler có thể generate zero-cost instruction nếu target hỗ trợ.

---

# 172.6. Widening vs narrowing

Có thể phân loại:

```text id="c9x3m7"
widening
narrowing
signedness-changing
integer↔float
float↔integer
```

Nhưng không nên dùng "widening luôn implicit" một cách quá rộng.

Axiom ưu tiên:

> **Nếu conversion có thể thay đổi semantic value hoặc gây programmer surprise → explicit.**

---

# 172.7. Integer narrowing

```ax id="r6m2v9"
let x: i64 = ...;
let y: i32 = x as i32;
```

phải có semantics xác định.

Không UB.

Có thể có các API:

```text id="q5k8n3"
checked_cast
saturating_cast
wrapping_cast
```

hoặc syntax tương ứng.

Ví dụ:

```text id="t3p7w1"
checked → Result
saturating → clamp
wrapping → modulo/truncate theo contract
```

---

# 172.8. Numeric conversion không dùng exception

Ví dụ:

```ax id="x7n4m2"
let y = x.try_as::<i32>()?;
```

failure là `Result`.

Không exception.

Không hidden runtime.

---

# 172.9. Float conversion

Các conversion:

```text id="z8q2v5"
f64 → f32
f32 → i32
i32 → f32
```

đều phải có semantic specification rõ ràng về:

```text
rounding
overflow
NaN
Infinity
signed zero
```

Không phụ thuộc vào compiler optimization level.

---

# 172.10. `as`

`as` là primitive language cast.

Ví dụ:

```ax id="f3k8q1"
x as i64
```

Không tự động gọi arbitrary user code.

Do đó compiler luôn biết:

```text id="w2m7c9"
input type
output type
conversion kind
possible failure
```

---

# 172.11. `as` không phải `From`

Nếu có:

```ax id="s8p3x5"
impl From<MyType> for OtherType
```

thì:

```text id="j5n9q2"
x as OtherType
```

không tự động gọi implementation đó.

Nếu muốn conversion API:

```ax id="u4c7m1"
let y = x.into();
```

hoặc explicit method.

Như vậy compiler không phải suy luận arbitrary user code trong primitive cast.

---

# 172.12. `CAST` vs `BITCAST`

Đây là distinction bắt buộc.

### CAST

Thay đổi semantic value:

```text id="q2x6m8"
i32(10)
→
f32(10.0)
```

### BITCAST

Giữ nguyên bit pattern:

```text id="v7k3p1"
u32 bits
↔
f32 representation
```

với điều kiện representation hợp lệ.

---

# 172.13. Bitcast safety

Bitcast chỉ safe nếu compiler chứng minh:

```text id="m5q8x2"
size compatible
alignment compatible
representation valid
type permits representation
```

Nếu không:

```text id="n1c7w4"
unsafe/system
```

---

# 172.14. Bitcast không phải serialization

```text id="c6x2m9"
BITCAST
```

không có nghĩa:

```text id="a4v8q1"
serialize
```

Serialization phải xác định:

```text endian
field order
padding
encoding
version
wire format
```

như đã đóng băng ở representation architecture.

---

# 172.15. Newtype conversion

Ví dụ:

```ax id="h7m2p4"
struct UserId(u64);
struct ProductId(u64);
```

Hai type **không interchangeable**.

```text id="w9q5x3"
UserId ≠ ProductId
```

dù physical representation có thể giống nhau.

Đây là một cách rất mạnh để ngăn nhầm dữ liệu.

---

# 172.16. Transparent newtype

Nếu cần ABI tương đương:

```text id="f3k8v6"
@repr(transparent)
struct UserId(u64);
```

thì representation/ABI có thể tương đương `u64`.

Nhưng semantic type identity vẫn khác.

Do đó:

```text id="q5n1x8"
semantic distinction
+
zero-cost representation
```

cùng tồn tại.

---

# 172.17. Type alias

Ngược lại:

```ax id="m8c3y7"
type UserId = u64;
```

là alias.

Không tạo semantic type mới.

```text id="p4x9n2"
UserId == u64
```

về type identity.

---

# 172.18. `Option` conversion

Không implicit:

```text id="j7v2k5"
T → Option<T>
```

trong mọi context.

Có thể có explicit:

```ax id="r3x8m1"
Some(x)
```

Compiler có thể optimize wrapper hoàn toàn.

---

# 172.19. `Result` conversion

Không tự động chuyển:

```text id="n5q1z7"
T → Result<T,E>
```

ngoài các syntax/compiler rules được định nghĩa rõ.

Ví dụ:

```ax id="c2m8v4"
Ok(value)
Err(error)
```

rõ ràng hơn.

---

# 172.20. Error conversion

Error conversion có thể dùng trait:

```text id="u7p4x2"
From<SourceError> for AppError
```

nhưng invocation phải được semantic resolver xác định.

`?` có thể sử dụng conversion contract được compiler biết.

Không có arbitrary conversion search vô hạn.

---

# 172.21. String/Bytes conversion

Đây là một case quan trọng:

```text id="r8m3q6"
String
→
Str
```

coercion/read view.

```text id="x4p7n1"
String
→
view<u8>
```

read-only view.

Nhưng:

```text id="q6v2m8"
Bytes
→
Str
```

phải validate UTF-8 hoặc dùng trusted unsafe contract.

Không implicit.

---

# 172.22. OS string conversion

Không:

```text id="f5x8q3"
String
→
OsString
```

một cách mặc định.

Vì conversion có thể:

- fail
- encode differently
- allocate
- lose information.

Phải dùng explicit platform API.

---

# 172.23. Pointer conversion

Pointer conversions là system-level.

Ví dụ:

```text id="p9k4x1"
*const T
→
*const U
```

có thể thay đổi provenance/alignment/validity.

Không safe implicit.

Raw pointer conversion thuộc unsafe/system/FFI.

---

# 172.24. Integer → pointer

Không có:

```ax id="w3n7m2"
let p: *mut T = address as *mut T;
```

trong safe code.

Đây là unsafe/system operation.

Quan trọng:

```text id="n8q2v5"
integer address
≠
valid pointer provenance
```

như memory model đã quy định.

---

# 172.25. Pointer → integer

Tương tự:

```text id="x6m1q9"
pointer as usize
```

là machine-level operation.

Nếu address representation được quan sát, compiler phải bảo toàn semantics tương ứng.

Nhưng integer trở lại pointer không tự động khôi phục safe provenance.

---

# 172.26. Function conversion

Function types phải rõ:

```text id="z2p7k4"
fn(A) -> B
```

khác:

```text id="m6x3q8"
closure(A) -> B
```

Noncapturing closure có thể decay thành function pointer nếu ABI/semantics cho phép.

Capturing closure không tự động biến thành function pointer vì environment cần được giữ.

---

# 172.27. Trait object conversion

Static generic:

```ax id="r5n8v2"
T: Trait
```

không tự động chuyển thành:

```text id="q1x6m4"
dyn Trait
```

Nếu cần dynamic dispatch:

```text id="k7p3z9"
dyn Trait
```

phải explicit.

Điều này tránh hidden allocation/vtable.

---

# 172.28. Generic conversion

Có thể có:

```text id="u4m8x1"
From<T>
Into<T>
TryFrom<T>
TryInto<T>
```

nhưng:

```text id="p2q7n5"
From
```

không có nghĩa conversion luôn zero-cost.

Compiler/IDE nên hiển thị conversion cost nếu conversion:

- allocation
- clone
- IO
- validation
- expensive computation.

---

# 172.29. Conversion trait semantics

Nên có ba nhóm:

```text id="c8x3m6"
From<T>
    infallible

TryFrom<T>
    recoverable failure

As / primitive cast
    language-defined conversion
```

Không cần một trait "ConvertEverything".

---

# 172.30. Infallible không đồng nghĩa zero-cost

Ví dụ:

```text id="m7p2q5"
String → SomeOwnedWrapper
```

có thể thành công 100% nhưng vẫn allocate.

Vì vậy:

```text id="a3x8n1"
infallible
≠
free
```

Compiler inspect/tooling nên phân biệt.

---

# 172.31. Coercion cost

Core coercion phải ưu tiên:

```text id="v5q9m2"
no allocation
no hidden user function
no ownership duplication
no observable side effect
```

Nếu conversion không thỏa các tiêu chí này, nên trở thành explicit conversion.

---

# 172.32. Conversion resolution

Resolver/compiler dùng pipeline:

```text id="k1m7x4"
Expected Type
      ↓
Exact match
      ↓
Allowed coercion
      ↓
Explicit cast
      ↓
Trait conversion
      ↓
No match
```

Không tự động thử hàng trăm conversion chains.

---

# 172.33. Không có conversion chain tùy ý

Ví dụ nếu tồn tại:

```text id="j8q3m5"
A → B
B → C
C → D
```

Axiom không tự động suy ra:

```text id="p6x1n9"
A → D
```

trong một expression.

Nếu muốn chain:

```ax id="r4v8m2"
let b = a.into();
let c = b.into();
```

hoặc API explicit.

Điều này làm diagnostics deterministic.

---

# 172.34. Conversion và overload resolution

Operator/function overload không được dùng conversion chains tùy ý để tìm candidate.

Ưu tiên:

```text id="x7m2q5"
exact
coercion
explicitly requested conversion
```

Ambiguous conversion:

```text id="k3p8n1"
compile error
```

Không đoán.

---

# 172.35. Conversion và ownership

Conversion có thể:

```text id="m5x9q2"
Borrow/view
Copy
Move
Clone
Allocate
Consume
```

Compiler phải biết loại nào.

Ví dụ:

```text id="f8q2v6"
String → Str
```

không consume.

Trong khi:

```text id="n4m7x1"
String → SomeOwnedType
```

có thể consume tùy API.

Không được ẩn Move sau syntax trông như READ.

---

# 172.36. Conversion và alias

Nếu conversion tạo view:

```text id="j6p3x8"
String → Str
```

thì provenance được giữ.

Nếu conversion tạo owned copy:

```text id="q2v7m5"
String → String
```

thì allocation/ownership mới được tạo.

Alias analysis phải phân biệt hai trường hợp.

---

# 172.37. Conversion và Drop

Nếu conversion tạo owned temporary:

```text id="w8n4q1"
let x = convert(y);
```

temporary có Drop semantics bình thường.

Compiler có thể eliminate temporary nếu abstraction không observable.

Không được bỏ Drop nếu Drop observable.

---

# 172.38. Conversion và ABI

ABI lowering chỉ diễn ra sau khi semantic conversion đã được xác định.

Ví dụ:

```text id="p5x9m3"
UserId → u64
```

có thể representation-identical.

Nhưng:

```text id="h7q2v6"
UserId
```

vẫn là distinct semantic type.

ABI optimizer có thể pass cùng register.

---

# 172.39. FFI conversion

FFI wrapper nên nằm ở boundary:

```text id="n3m8x1"
Axiom type
    ↓
FFI adapter
    ↓
C/System ABI
```

Không lan foreign representation vào toàn bộ application.

Ví dụ:

```text id="v6p2q9"
String
    ↓
CString
    ↓
C API
```

với explicit lifetime/ownership contract.

---

# 172.40. Conversion không phá UTF-8 invariant

Compiler/library phải giữ:

```text id="c7x4m1"
String
Str
```

UTF-8 invariant.

Không có safe cast:

```text id="q9n3v5"
Bytes as Str
```

nếu chưa establish validity.

---

# 172.41. Compile-time conversion

Conversion có thể chạy ở comptime:

```ax id="s2m7x8"
const X = 100 as i64;
```

và:

```text id="j5q1n4"
compile-time failure
```

nếu conversion invalid.

Không tạo runtime cost.

---

# 172.42. Compile-time và runtime semantics

Một conversion không được có:

```text id="w3x8m6"
comptime behavior ≠ runtime behavior
```

ngoại trừ việc external capabilities của comptime bị giới hạn.

Numeric semantics, overflow, validity vẫn thống nhất.

---

# 172.43. Conversion diagnostics

Compiler nên giải thích:

```text id="r6m2q9"
E_CONVERSION_NOT_ALLOWED
E_CONVERSION_LOSSY
E_CONVERSION_AMBIGUOUS
E_INVALID_BITCAST
E_INVALID_REINTERPRETATION
E_POINTER_PROVENANCE
E_UTF8_VALIDATION_REQUIRED
```

AI/compiler API có thể query:

```text id="x8p3m1"
axc explain conversion
```

để trả:

```text
source type
target type
conversion kind
cost
ownership effect
capability effect
failure mode
ABI lowering
```

---

# 172.44. Conversion cost model

Compiler có thể internally annotate:

```text id="q4m8x2"
ZeroCost
RegisterOnly
ScalarInstruction
VectorInstruction
Copy
Allocation
Validation
Call
```

Nhưng đây là optimization information.

Không biến cost estimate thành language semantics.

---

# 172.45. Conversion optimization

Compiler được phép biến:

```text id="m7x3q1"
T → U → V
```

thành trực tiếp:

```text id="p2n8v5"
T → V
```

nếu intermediate conversions không observable.

Nhưng phải giữ:

```text id="j6q4m9"
side effects
failure behavior
ownership
Drop
evaluation order
```

---

# 172.46. Conversion elimination

Ví dụ:

```ax id="z5m1q8"
let x: i64 = value as i64;
use(x);
```

có thể không sinh instruction nếu `value` đã ở dạng tương thích.

Tương tự newtype transparent có thể hoàn toàn zero-cost.

---

# 172.47. Conversion + SIMD

Numeric conversion có thể vectorize:

```text id="n8q3m6"
Vector<i32>
→
Vector<f32>
```

nếu target hỗ trợ.

Compiler có thể sinh SIMD conversion.

Không cần programmer gọi intrinsic.

---

# 172.48. Conversion + GPU

GPU conversion phải tuân theo GPU legality.

Ví dụ host pointer → device pointer không phải numeric cast bình thường.

```text id="v4p9x2"
Host address
≠
Device address
```

Storage domain phải được giữ.

---

# 172.49. Conversion + capability

Một conversion không được âm thầm biến:

```text id="q7m3n8"
view<T>
```

thành:

```text id="x2p6v1"
owned T
```

vì điều đó thay đổi ownership.

Tương tự:

```text id="a8m4q5"
view<T>
→
mut_view<T>
```

không phải coercion thông thường.

Phải có capability proof.

---

# 172.50. Conversion + mutability

Read-only:

```text id="f5x1m7"
view<T>
```

không được implicit chuyển thành:

```text id="r8q3n2"
mut_view<T>
```

Không có cast syntax nào được phép bypass safe capability verifier.

Nếu cần unsafe conversion, phải đi qua unsafe contract.

---

# 172.51. Tổng kết kiến trúc

```text id="j4x8p2"
                 Conversion
                     │
        ┌────────────┼─────────────┐
        ↓            ↓             ↓
     Coercion       Cast        Bitcast
        │            │             │
      safe        explicit     representation
        │            │             │
        └────────────┴─────────────┘
                     │
                verifier
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
      Ownership   Capability   ABI
```

Còn:

```text id="x7m2q9"
raw reinterpretation
pointer fabrication
invalid bitcast
integer↔pointer provenance
```

đi vào:

```text
unsafe/system/FFI
```

---

# 172.52. Invariants đóng băng

### Conversion

- **ACONV-20** — Conversion semantics phải được xác định trước ABI lowering.
- **ACONV-21** — Coercion chỉ tồn tại cho compiler-defined safe conversions.
- **ACONV-22** — Coercion không tự gọi arbitrary user code.
- **ACONV-23** — Implicit conversion chains không tồn tại.
- **ACONV-24** — Ambiguous conversion là compile error.
- **ACONV-25** — Conversion không được âm thầm thay đổi ownership.
- **ACONV-26** — Conversion không được âm thầm tăng capability.
- **ACONV-27** — Conversion có thể được tối ưu/eliminate khi semantics cho phép.

### Numeric

- **ACONV-30** — Lossy/narrowing numeric conversion phải explicit.
- **ACONV-31** — Numeric conversion không có signed-overflow UB.
- **ACONV-32** — Checked conversion có thể trả `Result`.
- **ACONV-33** — Wrapping/saturating conversion có semantics xác định.
- **ACONV-34** — Float conversion có rounding/NaN/overflow semantics xác định.
- **ACONV-35** — Numeric conversion semantics không phụ thuộc optimization level.

### Representation

- **ACONV-40** — `CAST` và `BITCAST` là các semantic operation khác nhau.
- **ACONV-41** — BITCAST giữ bit pattern theo representation contract.
- **ACONV-42** — BITCAST yêu cầu size/alignment/valid-representation compatibility.
- **ACONV-43** — BITCAST không phải serialization.
- **ACONV-44** — Transparent newtype có thể zero-cost nhưng vẫn giữ semantic type identity.
- **ACONV-45** — Type alias không tạo type identity mới.

### Ownership/Capability

- **ACONV-50** — `String → Str` có thể là zero-copy read-only coercion.
- **ACONV-51** — `Bytes → Str` cần UTF-8 validation hoặc trusted contract.
- **ACONV-52** — `view<T> → mut_view<T>` không implicit.
- **ACONV-53** — raw pointer conversion không safe implicit.
- **ACONV-54** — integer→pointer không thiết lập safe provenance.
- **ACONV-55** — conversion-generated capabilities giữ provenance và lifetime.

### FFI/GPU

- **ACONV-60** — FFI conversion phải explicit ở ABI boundary.
- **ACONV-61** — foreign representation không tự lan vào semantic Axiom types.
- **ACONV-62** — Host/Device conversion không phải ordinary pointer cast.
- **ACONV-63** — GPU storage-domain constraints phải được giữ qua conversion.

### Compiler

- **ACONV-70** — Conversion resolution deterministic.
- **ACONV-71** — Compiler có thể scalarize/vectorize/eliminate conversion.
- **ACONV-72** — Optimization không được thay đổi failure/Drop/ownership semantics.
- **ACONV-73** — Conversion diagnostics phải machine-readable.
- **ACONV-74** — Conversion cost có thể được compiler phân tích nhưng không phải semantic requirement.
- **ACONV-75** — Unsafe conversion không được bypass verifier; nó chỉ có thể thiết lập trusted preconditions.

---

## Trạng thái kiến trúc

Chuỗi hiện tại đã đi từ:

```text
Core
→ Memory
→ Ownership
→ Capability
→ Concurrency
→ Async
→ Type/Trait
→ MIR
→ Verification
→ Optimization
→ ABI
→ Backend
→ Linker
→ Runtime
→ Build
→ Collections
→ Error
→ Conversion
```

Vì vậy **BOOTSTRAP-172 được FROZEN**.

### BOOTSTRAP-173 — Modules, Package API Design & Dependency/ABI Boundaries

Task tiếp theo nên khóa cách Axiom tổ chức **API lớn và hệ sinh thái package** ở cấp semantic, khác với build graph đã làm trước đó:

```text
module
package
pub API
private implementation
re-export
facade
generic API
ABI boundary
semantic versioning
binary compatibility
API stability
feature flags
platform API
conditional compilation
prelude
cyclic module dependencies
package isolation
```

Đặc biệt cần giải quyết một vấn đề quan trọng cho Axiom:

> **Làm sao package có thể thay đổi implementation rất mạnh mà không buộc toàn bộ dependency graph phải compile lại, đồng thời vẫn giữ được zero-cost abstraction và khả năng LTO xuyên package?**