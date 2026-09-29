# BOOTSTRAP-193 — API Evolution, Axiom ABI, Versioning & Binary Compatibility

**TRẠNG THÁI: FROZEN / COMPLETED**

## 193.1. Vấn đề cốt lõi

Axiom phải giải quyết được một mâu thuẫn:

> **ABI ổn định để binary có thể sống lâu, nhưng compiler vẫn phải được tự do tối ưu layout, generic, inline, dispatch và machine code.**

Nếu ép toàn bộ Axiom phải có ABI cố định thì compiler sẽ mất rất nhiều quyền tối ưu.

Vì vậy quyết định kiến trúc là:

> **Axiom có nhiều mức ổn định ABI, không có một ABI duy nhất áp lên mọi code.**

```text
                    Axiom Program
                         │
             ┌───────────┴───────────┐
             │                       │
       Internal ABI             Public ABI
       tối ưu tự do             ổn định có hợp đồng
             │                       │
      compiler freedom          compatibility
```

---

# 193.2. Ba lớp ABI

Axiom phân biệt:

```text
1. Internal ABI
2. Package ABI
3. Stable/Public ABI
```

### Internal ABI

Dùng giữa các compilation unit mà compiler kiểm soát hoàn toàn.

Compiler được phép:

- thay đổi calling convention
- reorder layout
- inline
- monomorphize
- specialize
- eliminate function
- thay đổi register allocation
- thay đổi symbol
- thay đổi generic representation

Không có binary compatibility guarantee.

Đây là nơi compiler đạt hiệu năng tối đa.

---

### Package ABI

Dùng giữa các `.axlib`/compiled packages.

Có metadata đủ để compiler hiểu:

```text
type
generic
trait
ABI
layout
effects
ownership contracts
optimization summaries
```

Compiler có thể recompilation hoặc link trực tiếp tùy artifact.

---

### Stable/Public ABI

Chỉ áp dụng khi programmer **yêu cầu**.

Ví dụ concept:

```axiom
@abi(stable)
pub fn process(x: Data) -> Result;
```

Lúc này compiler phải duy trì contract qua version.

---

# 193.3. Không mặc định stable ABI

Đây là quyết định quan trọng.

Nếu:

```axiom
pub fn foo(x: MyStruct) -> MyStruct
```

thì **không có nghĩa** binary ABI của `MyStruct` phải vĩnh viễn ổn định.

Mặc định:

```text
pub
≠
stable ABI
```

`pub` chỉ là source/package visibility.

Muốn binary compatibility:

```text
@abi(stable)
```

hoặc tương đương.

---

# 193.4. Source API ≠ ABI

Axiom phân biệt:

```text
Source API
Semantic API
ABI
Binary implementation
```

Ví dụ:

```axiom
pub fn calculate(x: i32) -> i32
```

có thể giữ nguyên source API nhưng compiler thay đổi:

```text
register allocation
instruction selection
inlining
function body
code layout
```

mà không ảnh hưởng compatibility.

---

# 193.5. Semantic compatibility

Một version mới của package phải phân biệt:

```text
Source-compatible
ABI-compatible
Semantic-compatible
```

Ví dụ:

```axiom
fn foo(x: i32) -> i32
```

giữ nguyên signature nhưng thay đổi:

```text
foo(0) → 1
```

thành:

```text
foo(0) → 2
```

có thể ABI-compatible nhưng **không semantic-compatible**.

Compiler không thể tự chứng minh mọi semantic compatibility của arbitrary implementation.

Do đó package versioning phải dựa trên:

```text
declared API
ABI contracts
semantic version policy
tests/contracts
```

chứ không giả định ABI = behavior.

---

# 193.6. Stable type representation

Một stable ABI type phải có representation contract.

Ví dụ:

```axiom
@repr(C)
@abi(stable)
pub struct Point {
    pub x: f64,
    pub y: f64,
}
```

Compiler không được tự ý:

```text
reorder x/y
change size
change alignment
change ABI classification
```

trong phạm vi stable contract.

---

# 193.7. Nhưng không nên ép `@repr(C)` cho mọi Axiom ABI

Axiom ABI có thể hiệu quả hơn C ABI.

Ví dụ:

```text
Axiom stable ABI
```

có thể hiểu được:

```text
Option<T>
Result<T,E>
slice
string view
trait object
owned handle
```

mà C ABI không hiểu trực tiếp.

Do đó:

```text
C ABI
≠
Axiom ABI
```

Axiom ABI có semantic metadata phong phú hơn.

---

# 193.8. Stable ABI types

Stable ABI v1 chỉ cho phép một tập type có contract rõ ràng:

```text
bool
integer
float
fixed arrays
stable structs
stable enums
transparent newtypes
stable views
stable handles
stable function pointers
explicit dyn Trait
```

Các type như:

```text
closure
compiler-generated Future
internal iterator
opaque generic
compiler-private type
```

không tự động stable ABI.

---

# 193.9. Generic ABI

Đây là điểm đặc biệt quan trọng.

Không nên cố tạo một universal runtime generic ABI kiểu:

```text
generic<T>
```

cho tất cả trường hợp.

Axiom mặc định:

```text
generic
   ↓
monomorphization/specialization
   ↓
native optimized code
```

Do đó generic ABI nội bộ có thể thay đổi tự do.

---

# 193.10. Stable generic boundary

Nếu cần expose generic qua stable ABI:

```axiom
@abi(stable)
pub fn sort<T: Comparable>(...)
```

thì compiler không nên expose machine-level monomorphized implementation trực tiếp.

Thay vào đó có thể sử dụng:

```text
stable generic interface
       ↓
metadata/type descriptor
       ↓
versioned instantiation
```

hoặc yêu cầu một explicit erased ABI.

Điều này tránh khóa compiler vào representation của generic implementation.

---

# 193.11. Generic static dispatch vẫn là mặc định

Stable ABI **không đồng nghĩa** mọi generic phải dynamic dispatch.

Trong cùng package:

```text
generic<T>
```

vẫn có thể:

```text
inline
specialize
vectorize
constant-propagate
monomorphize
```

Chỉ boundary giữa binary độc lập mới cần ABI contract.

---

# 193.12. `dyn Trait` ABI

Dynamic dispatch là một ABI concern.

Concept:

```axiom
dyn Drawable
```

có:

```text
data pointer
dispatch metadata
type identity
```

nhưng representation không được mặc định ổn định giữa compiler versions.

Nếu cần plugin ABI:

```axiom
@abi(stable)
dyn Drawable
```

thì compiler phải sử dụng **versioned trait-object ABI**.

---

# 193.13. Stable trait ABI

Một stable trait interface phải khóa:

```text
trait identity
method order/IDs
argument ABI
return ABI
associated ABI contracts
error behavior
object safety
version
```

Thay vì phụ thuộc vào:

```text
vtable layout ngẫu nhiên của compiler
```

nên dùng semantic method IDs hoặc versioned dispatch metadata.

---

# 193.14. Trait evolution

Nếu version 1:

```axiom
trait Renderer {
    fn draw(self);
}
```

version 2 thêm:

```axiom
fn resize(self);
```

thì không được giả định binary cũ tự động tương thích.

Axiom có thể hỗ trợ:

```text
trait versioning
optional methods
default methods
adapter
```

nhưng phải có explicit compatibility rule.

---

# 193.15. Struct evolution

Stable struct:

```axiom
@abi(stable)
struct Config {
    width: u32,
    height: u32,
}
```

Thêm field:

```text
width
height
fullscreen
```

không tự động safe ABI-compatible.

Các lựa chọn:

1. versioned struct
2. reserved fields
3. opaque struct + accessor
4. explicit extensible layout

Axiom ưu tiên:

> **Opaque stable types cho API lâu dài.**

Ví dụ:

```text
pub opaque Config
```

và:

```text
config.width()
config.height()
```

Compiler có thể thay đổi representation nội bộ mà ABI bên ngoài không đổi.

---

# 193.16. Opaque type

Đây sẽ là công cụ cực kỳ quan trọng cho binary compatibility.

```axiom
pub opaque Image;
```

Consumer chỉ biết:

```text
Image identity
ownership
ABI
allowed operations
```

Không biết layout.

Do đó library có thể chuyển:

```text
struct ImageV1
```

sang:

```text
struct ImageV2
```

mà không phá binary contract.

---

# 193.17. Stable handles

External resources nên ưu tiên:

```text
Handle<T>
```

hoặc opaque identity thay vì expose layout.

Ví dụ:

```axiom
pub opaque Database;
```

API:

```text
Database.open()
Database.query()
Database.close()
```

Library có thể thay đổi implementation mà ABI vẫn ổn định.

---

# 193.18. Function ABI

Stable function contract bao gồm:

```text
symbol identity
calling convention
parameter ABI
return ABI
alignment
unwind/panic behavior
effect contract
version
```

Không chỉ có:

```text
name + parameter types
```

---

# 193.19. Symbol versioning

Axiom binary symbols nên có semantic identity:

```text
Package
Module
Declaration
ABI version
```

Compiler có thể generate:

```text
symbol identity
```

không nhất thiết trùng source name.

Ví dụ concept:

```text
foo::Image::open
```

→ mang fingerprint/version internally.

Dynamic linker có thể phát hiện:

```text
required ABI = 3
provided ABI = 2
```

và từ chối load thay vì crash ngẫu nhiên.

---

# 193.20. ABI fingerprint

Mỗi stable public declaration có:

```text
AbiFingerprint
```

được tính từ:

```text
ABI version
type representation
calling convention
parameter ABI
return ABI
trait ABI
error ABI
visibility
target ABI rules
```

Implementation body không tham gia fingerprint nếu không ảnh hưởng ABI.

Do đó thay đổi:

```text
algorithm
optimization
machine code
```

không phá ABI.

---

# 193.21. API fingerprint

Tách:

```text
SemanticFingerprint
AbiFingerprint
CodegenFingerprint
```

### SemanticFingerprint

Theo dõi semantic interface.

### AbiFingerprint

Theo dõi binary contract.

### CodegenFingerprint

Theo dõi machine implementation.

Điều này rất hữu ích cho incremental compilation.

---

# 193.22. Version compatibility matrix

Compiler/package manager có thể xác định:

```text
Source compatibility
ABI compatibility
Metadata compatibility
Compiler compatibility
```

Ví dụ:

```text
Package A v2
requires:
    API >= 1
    ABI >= 3
```

package manager không chỉ nhìn:

```text
version number
```

mà có thể kiểm tra metadata.

---

# 193.23. Semantic versioning

Axiom package manager sử dụng SemVer-compatible policy nhưng compiler có thể hiểu sâu hơn.

Concept:

```text
major
minor
patch
```

### Patch

Không đổi public semantic contract.

### Minor

Có thể thêm API backward-compatible.

### Major

Có thể phá source/API/ABI compatibility.

Nhưng compiler **không tuyên bố** rằng SemVer tự động chứng minh behavior compatibility.

---

# 193.24. ABI versioning độc lập

Có thể có:

```text
Package v10
Axiom ABI v4
```

hoặc:

```text
Package v11
Axiom ABI v4
```

Nếu implementation thay đổi nhưng public ABI không đổi:

```text
ABI remains compatible.
```

Ngược lại package version có thể tăng nhưng ABI vẫn giữ nguyên.

---

# 193.25. Multiple ABI versions

Library có thể đồng thời export:

```text
ABI v3
ABI v4
```

nếu cần migration.

Dynamic loader chọn:

```text
consumer required ABI
```

→ compatible implementation.

Điều này rất hữu ích cho:

- plugin
- graphics engine
- database
- OS integration
- long-lived applications

---

# 193.26. Binary-only package

`.axlib` + `.axmeta` phải đủ để compiler sử dụng package mà không cần source.

Ví dụ:

```text
foo.axlib
foo.axmeta
```

`.axmeta` chứa:

```text
public declarations
types
traits
ABI
generic metadata
ownership contracts
effects
dependencies
compiler compatibility
```

Implementation vẫn nằm trong `.axlib`.

---

# 193.27. Compiler version compatibility

Compiler mới không nhất thiết phải chạy được mọi `.axlib` cũ.

Artifact có:

```text
compiler semantic version
metadata format version
ABI version
target
```

Compiler kiểm tra compatibility.

Nếu metadata quá cũ:

```text
recompile from source
```

hoặc:

```text
migration tool
```

thay vì đoán.

---

# 193.28. ABI compatibility không phụ thuộc compiler version

Nếu:

```text
@abi(stable, v4)
```

thì compiler Axiom 10 và Axiom 11 có thể cùng generate/consume ABI v4 **nếu compiler implementation tuyên bố hỗ trợ contract đó**.

Đây là điểm phân biệt:

```text
Compiler compatibility
        ≠
ABI compatibility
```

---

# 193.29. Dynamic library compatibility

Khi load:

```text
foo.dll
libfoo.so
libfoo.dylib
```

loader kiểm tra:

```text
target
architecture
ABI
symbol
ABI fingerprint
dependency
required runtime components
```

Không load nếu contract không phù hợp.

---

# 193.30. Plugin ABI

Plugin interface nên dùng:

```text
stable opaque types
stable function tables
explicit version
capability negotiation
```

Ví dụ:

```text
PluginV1
PluginV2
```

không nên dựa trên compiler-private class/vtable/layout.

---

# 193.31. Capability negotiation

Plugin có thể khai báo:

```text
supports:
    Renderer
    Audio
    Compute
```

và version:

```text
Renderer ABI 3
```

Host kiểm tra trước khi gọi.

Không cần:

```text
global runtime registry
```

---

# 193.32. Async ABI

`Future<T>` compiler-generated state machine **không stable ABI mặc định**.

Đây là chủ ý.

Nếu expose async qua stable boundary:

```text
async function
```

được chuyển thành:

```text
poll interface
state handle
completion callback
```

hoặc một explicitly versioned async ABI.

Điều này giữ compiler tự do thay đổi coroutine layout.

---

# 193.33. Closure ABI

Closure environment là compiler-generated.

Do đó:

```text
fn foo(callback: closure)
```

không stable ABI mặc định.

Stable callback:

```text
extern fn(...)
```

hoặc:

```text
@abi(stable)
Callback<T>
```

với explicit environment representation.

---

# 193.34. Error ABI

`Result<T,E>` có thể có ABI tối ưu nội bộ.

Stable boundary phải xác định:

```text
success representation
error representation
ownership
destruction
error version
```

Không được expose một enum layout compiler-private rồi coi đó là stable mãi mãi.

---

# 193.35. Panic/exception ABI

Stable Axiom ABI mặc định:

```text
panic does not cross boundary
```

Một stable function phải chọn:

```text
abort
Result
explicit foreign exception mapping
```

Điều này tiếp tục nguyên tắc FFI-192.

---

# 193.36. ABI adapters

Compiler/toolchain có thể tự tạo:

```text
Internal ABI
      ↓
ABI Adapter
      ↓
Stable ABI
```

Ví dụ:

```text
internal optimized struct
          ↓
adapter
          ↓
stable opaque handle
```

Nhờ vậy **internal implementation không bị đóng băng**.

Đây là một trong những cơ chế quan trọng nhất của Axiom.

---

# 193.37. Stable ABI không phải optimization barrier toàn chương trình

Chỉ boundary bị giới hạn.

Ví dụ:

```text
Application
   │
   ├── internal functions → aggressive optimization
   │
   ├── internal generic → specialization
   │
   └── stable library ABI → adapter boundary
```

LTO vẫn có thể tối ưu qua boundary nếu compiler có source/metadata và compatibility không yêu cầu binary isolation.

---

# 193.38. LTO và stable ABI

Nếu cả hai module cùng được compiler nhìn thấy:

```text
stable ABI declaration
```

không nhất thiết cấm:

```text
inline
devirtualize
constant propagate
```

Compiler có thể tạo optimized private path nhưng phải giữ stable exported entry point.

Ví dụ:

```text
stable foo()
     │
     ├── external callers
     │
     └── internal optimized foo_impl()
```

---

# 193.39. ABI Adapter + Optimization

Pattern:

```text
Public ABI
    ↓
thin adapter
    ↓
internal representation
    ↓
optimized implementation
```

Adapter có thể rất nhỏ.

Compiler có thể:

- inline adapter
- eliminate conversions
- scalarize
- devirtualize
- specialize

khi boundary không còn externally observable.

---

# 193.40. Hot reload

Hot reload không được coi là mặc định.

Một module muốn hot reload phải khai báo:

```text
@reloadable
```

và có:

```text
stable ABI
state migration
version
resource ownership rules
```

Compiler không tự ý thay code đang chạy nếu state representation incompatible.

---

# 193.41. State migration

Nếu:

```text
StateV1
```

→

```text
StateV2
```

cần:

```text
migrate(V1 → V2)
```

explicit.

Không dùng:

```text
memcpy
```

hay reinterpretation để giả định layout tương thích.

---

# 193.42. ABI compatibility checker

Tooling:

```text
ax abi-check old.axmeta new.axmeta
```

có thể báo:

```text
BREAKING:
  Foo.width changed u32 → u64

BREAKING:
  function parameter ABI changed

COMPATIBLE:
  private implementation changed

COMPATIBLE:
  function body optimized
```

Điều này rất hữu ích cho library developers.

---

# 193.43. API diff

Tương tự:

```text
ax api-diff v1.axmeta v2.axmeta
```

phân tích:

```text
added
removed
changed
deprecated
ABI-breaking
source-breaking
semantic-contract-changing
```

Compiler không biến những phân tích này thành “rating”; chỉ báo cáo fact.

---

# 193.44. Deprecation

Axiom hỗ trợ:

```text
@deprecated("use new_api")
```

Nhưng deprecation không tự động remove symbol.

Một API có thể tồn tại nhiều ABI versions để migration từ từ.

---

# 193.45. Binary compatibility boundary

Chốt:

```text
                    Package
                       │
          ┌────────────┴────────────┐
          │                         │
      Internal                   Public
       world                     world
          │                         │
    unstable ABI              stable ABI
    aggressive opt            explicit contract
          │                         │
          └────────────┬────────────┘
                       ▼
                 ABI Adapter
```

---

# 193.46. Những gì KHÔNG làm

Axiom **không**:

- đóng băng layout của mọi struct
- biến mọi generic thành dynamic
- bắt mọi function có stable ABI
- dùng universal object header
- yêu cầu universal runtime
- tạo vtable cho mọi trait
- bắt closure có stable representation
- bắt Future có stable layout
- biến package version thành ABI version
- coi SemVer là bằng chứng semantic correctness
- giữ ABI bằng cách hy sinh toàn bộ optimizer

---

# 193.47. Invariants — BOOTSTRAP-193

### `AABI-20`
Internal ABI shall remain freely optimizable unless an explicit compatibility contract applies.

### `AABI-21`
Public visibility shall not imply stable binary ABI.

### `AABI-22`
Stable ABI shall require an explicit ABI contract.

### `AABI-23`
Stable ABI compatibility shall be distinct from source compatibility.

### `AABI-24`
ABI compatibility shall be distinct from semantic compatibility.

### `AABI-25`
Stable representations shall have explicit layout and calling-convention contracts.

### `AABI-26`
Compiler-private representations shall not become stable ABI implicitly.

### `AABI-27`
Opaque public types shall permit implementation representation changes while preserving their ABI contract.

### `AABI-28`
Generic monomorphization shall remain available inside non-stable boundaries.

### `AABI-29`
Stable generic interfaces shall not require freezing compiler-private monomorphized representations.

### `AABI-30`
Dynamic trait ABI shall be explicitly versioned when exposed across stable binary boundaries.

### `AABI-31`
Compiler-generated closure representations shall not be stable ABI by default.

### `AABI-32`
Compiler-generated async state-machine representations shall not be stable ABI by default.

### `AABI-33`
Stable ABI functions shall define panic/error boundary behavior.

### `AABI-34`
Stable binary symbols shall carry sufficient identity/version information to detect incompatible interfaces.

### `AABI-35`
ABI fingerprints shall represent binary contracts independently of implementation code.

### `AABI-36`
Semantic, ABI, and code-generation fingerprints shall remain distinct.

### `AABI-37`
Multiple ABI versions may coexist when explicitly supported.

### `AABI-38`
Dynamic loading shall verify ABI compatibility before exposing foreign symbols as callable capabilities.

### `AABI-39`
Plugin interfaces shall use explicit versioned contracts rather than compiler-private layout assumptions.

### `AABI-40`
Hot reload shall require an explicit stable ABI and state-migration contract.

### `AABI-41`
State migration shall not rely on unverified layout reinterpretation.

### `AABI-42`
Stable ABI boundaries shall not unnecessarily prevent internal optimization.

### `AABI-43`
ABI adapters may translate stable external representations into optimized internal representations.

### `AABI-44`
LTO may optimize across a stable boundary only where observable ABI obligations remain preserved.

### `AABI-45`
Binary-only packages shall provide sufficient metadata for compatibility verification.

### `AABI-46`
Compiler-version compatibility shall be distinct from stable ABI compatibility.

### `AABI-47`
ABI incompatibility shall be diagnosed before unsafe binary invocation whenever statically or dynamically detectable.

### `AABI-48`
ABI compatibility rules shall be target-specific where the target ABI requires it.

### `AABI-49`
Stable ABI contracts shall not require a mandatory runtime or object header.

### `AABI-50`
ABI verification shall remain independent of optimization level.

---

# Kết luận BOOTSTRAP-193

Kiến trúc này giải quyết được vấn đề mà các language ecosystem thường phải đánh đổi:

```text
ABI ổn định
      ↕
compiler optimization
```

Axiom không chọn một phía.

Nó tạo:

```text
                 Axiom
                   │
       ┌───────────┴───────────┐
       │                       │
 Internal ABI              Stable ABI
       │                       │
 free optimization        explicit contract
       │                       │
 generics                  opaque types
 specialization            versioning
 inlining                  adapters
 vectorization             compatibility
       │                       │
       └───────────┬───────────┘
                   ▼
              Native Binary
```

**Đây là hướng phù hợp với mục tiêu “nhanh như C/C++ nhưng không bắt ngôn ngữ phải đóng băng compiler để có ABI”.**

---

# BOOTSTRAP-194 — Compiler/Build Architecture cho Cross-Compilation, Multi-Target & Universal Native Toolchain

**TRẠNG THÁI: NEXT**

Sau 193, một phần rất lớn của kiến trúc Axiom đã hoàn chỉnh. Bước tiếp theo nên xử lý **cross-compilation và target abstraction** ở mức compiler/build system.

Đặc biệt cần giải quyết:

```text
Axiom source
     │
     ├── Windows x64 → PE/COFF
     ├── Linux x64   → ELF
     ├── Linux ARM64 → ELF
     ├── macOS ARM64 → Mach-O
     ├── iOS ARM64   → Mach-O
     ├── Android ARM64 → ELF
     ├── WASM
     ├── GPU
     └── future targets
```

Nhưng không chỉ là “thêm target”.

Cần thiết kế một **Target Model thống nhất**:

```text
Target
 ├── Architecture
 ├── OS
 ├── ABI
 ├── Object Format
 ├── Calling Convention
 ├── Data Layout
 ├── Endianness
 ├── Pointer Model
 ├── CPU Features
 ├── SIMD Features
 ├── Atomic Capabilities
 ├── TLS
 ├── Exception/Unwind
 ├── Page/Memory Model
 ├── Linker Model
 ├── System Libraries
 ├── SDK
 ├── GPU Targets
 └── Runtime Profile
```

Đồng thời phải quyết định rõ:

> **Axiom compiler có thực sự cần một “cross compiler” riêng biệt không, hay mọi compiler đều là multi-target compiler và target chỉ là một input của CompilerDB?**

Hướng thứ hai có khả năng phù hợp hơn với kiến trúc hiện tại, vì mục tiêu cuối cùng của Axiom là **một compiler native duy nhất có thể phát sinh nhiều loại binary**, thay vì mỗi nền tảng có một compiler riêng.