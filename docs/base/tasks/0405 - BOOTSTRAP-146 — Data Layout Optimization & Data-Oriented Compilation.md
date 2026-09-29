# BOOTSTRAP-146 — Data Layout Optimization & Data-Oriented Compilation

**Trạng thái: FROZEN / COMPLETED**

Đây là bước hoàn thiện một trong những lợi thế lớn nhất mà Axiom có thể có:

> **Programmer thiết kế dữ liệu theo semantic model; compiler được quyền thiết kế lại physical representation để dữ liệu chạy nhanh nhất trên target.**

Điều này đặc biệt quan trọng cho:

- cache locality;
- SIMD;
- game/graphics;
- AI/tensor;
- database;
- scientific computing;
- ECS/data-oriented programming;
- giảm memory footprint.

Nhưng phải giữ ranh giới rất rõ:

```text
Semantic Struct
      ≠
Physical Layout
```

---

# 1. Vị trí trong compiler

```text id="layout146"
Typed HIR
    ↓
MIR
    ↓
Verification
    ↓
Alias / Effect / Escape
    ↓
SSA + MemorySSA
    ↓
Data Layout Analysis
    ↓
Layout Optimization
    ↓
SROA / Vectorization / Cache Optimization
    ↓
Representation Selection
    ↓
ABI MIR
```

Layout optimization diễn ra **trước ABI lowering**.

---

# 2. Semantic struct là bất biến

Ví dụ:

```ax
struct Particle {
    position: Vec3,
    velocity: Vec3,
    mass: f32,
    active: bool,
}
```

Compiler không được thay đổi semantic:

```text id="semanticfields"
Particle.position
Particle.velocity
Particle.mass
Particle.active
```

Các `FieldId` vẫn giữ nguyên.

---

# 3. Physical layout có thể thay đổi

Compiler có thể quyết định:

```text id="physlayout"
position
velocity
mass
active
padding
```

hoặc layout khác nếu:

- layout không observable;
- không có ABI contract;
- không có FFI;
- không có raw address dependency;
- không có explicit representation requirement.

---

# 4. Field reordering

Ví dụ:

```ax id="reorder"
struct A {
    a: u8,
    b: u64,
    c: u8,
}
```

compiler có thể đặt physical fields theo cách giảm padding.

Nhưng semantic access vẫn:

```text
a
b
c
```

theo FieldId.

---

# 5. Đây không phải source reordering

Compiler **không sửa AST/source**.

Chỉ:

```text id="fieldid"
FieldId
    ↓
LayoutDB
    ↓
physical offset
```

thay đổi.

---

# 6. `offset_of`

Nếu programmer hỏi:

```ax
offset_of(A, A.b)
```

thì layout trở thành observable.

Compiler phải tính theo **layout của compilation contract hiện tại**.

---

# 7. `@repr(C)`

```ax
@repr(C)
struct A {
    ...
}
```

khóa C-compatible representation.

Compiler không được reorder theo ý muốn.

---

# 8. `@repr(transparent)`

```ax
@repr(transparent)
struct UserId(u64);
```

Semantic type:

```text
UserId ≠ u64
```

nhưng representation/ABI tương thích theo contract.

---

# 9. `@repr(packed)`

```ax
@repr(packed)
struct Header {
    ...
}
```

là system/unsafe territory vì có thể gây unaligned access.

Compiler phải bảo toàn representation contract.

---

# 10. `@repr(align(N))`

Cho phép yêu cầu alignment tối thiểu.

Compiler vẫn được tối ưu các khía cạnh khác nếu không phá contract.

---

# 11. Stable address

Nếu:

```text id="stable"
address(x)
```

là observable và có contract ổn định:

```text
```

compiler không được biến physical representation thành thứ làm thay đổi địa chỉ quan sát được.

---

# 12. Raw pointer

Nếu address được đưa vào:

```text id="ptr"
foreign code
```

thì layout/storage freedom giảm mạnh.

---

# 13. FFI boundary

Ví dụ:

```ax
extern "C" fn process(p: *mut Particle);
```

Nếu `Particle` được truyền theo memory representation:

```text id="ffi"
```

layout phải là FFI-safe và được contract hóa.

---

# 14. Data layout analysis

Compiler tạo:

```text id="dla"
DataLayoutProfile {
    FieldAccessFrequency
    FieldSize
    FieldAlignment
    FieldHotness
    FieldEscape
    FieldAddressObserved
    FieldMutability
    FieldLifetime
    Vectorizability
    CacheLocality
}
```

---

# 15. Field hotness

PGO có thể phát hiện:

```text id="hot"
position → very hot
velocity → hot
mass → medium
debug_info → cold
```

Compiler có thể dùng thông tin này cho layout.

---

# 16. Hot/cold splitting

Semantic:

```text id="split"
Particle {
    hot fields
    cold fields
}
```

Physical:

```text id="split2"
HotParticleData
ColdParticleData
```

nhưng compiler phải bảo đảm access semantics vẫn đúng.

---

# 17. Khi nào splitting không được phép?

Ví dụ:

```text id="bad_split"
address_of(p)
```

sau đó code yêu cầu một contiguous `Particle`.

Hoặc:

```text id="bad_split2"
@repr(C)
```

Hoặc FFI.

→ không được tự ý split.

---

# 18. AoS

Thông thường:

```text id="aos"
Particle
Particle
Particle
Particle
```

là Array of Structures.

---

# 19. SoA

Workload:

```ax id="soa"
for p in particles {
    sum += p.position.x;
}
```

có thể hưởng lợi từ:

```text id="soa2"
positions[]
velocities[]
mass[]
```

---

# 20. Compiler có thể tự chuyển AoS → SoA không?

**Có, nhưng chỉ khi physical layout không observable và compiler có thể bảo toàn semantic identity.**

Đây là optimization rất mạnh nhưng cũng rất khó.

---

# 21. Không phải mọi struct đều chuyển được

Nếu:

```text id="notsoa"
```

có:

- address escape;
- stable pointer;
- FFI;
- runtime reflection về layout;
- explicit `repr`;
- externally visible representation;

thì transformation bị giới hạn hoặc cấm.

---

# 22. Logical identity

Nếu programmer có:

```ax
Handle<Particle>
```

thì logical identity có thể tồn tại độc lập với physical location.

Đây là trường hợp rất phù hợp với layout transformation.

---

# 23. Handle-oriented design

Thay vì:

```text id="addressidentity"
Particle*
```

application có thể dùng:

```text id="handle"
EntityId
```

Compiler/runtime có nhiều freedom hơn để thay đổi storage.

---

# 24. Value identity vs storage identity

Axiom giữ ba khái niệm:

```text id="identity"
Value Identity
Storage Identity
Logical Identity
```

Layout optimization không được nhầm ba khái niệm này.

---

# 25. Value identity

Hai values:

```text
a = Particle(...)
b = Particle(...)
```

có semantic value độc lập.

Physical representation có thể khác.

---

# 26. Storage identity

Nếu programmer/library yêu cầu stable storage:

```text id="storage"
```

thì address/identity contract được giữ.

---

# 27. Logical identity

Ví dụ:

```text id="entity"
EntityId(123)
```

có thể tồn tại dù entity di chuyển trong memory.

Đây là abstraction tốt cho data-oriented systems.

---

# 28. Field access lowering

Source:

```ax id="field"
p.position.x
```

semantic:

```text id="fieldsemantic"
FieldId(position)
FieldId(x)
```

physical:

```text id="fieldphysical"
base + physical_offset
```

---

# 29. Offset không phải semantic identity

Compiler có thể thay:

```text
position offset = 16
```

thành:

```text
position offset = 0
```

nếu representation không observable.

---

# 30. Padding elimination

Compiler có thể giảm:

```text id="padding"
unused padding
```

nếu không có:

- bytewise observation;
- FFI;
- serialization contract;
- explicit layout contract.

---

# 31. Bytewise equality

Axiom đã tách:

```text id="equal"
semantic equality
```

khỏi:

```text id="byteeq"
bytewise equality
```

Do đó compiler không được giả định:

```text semantic_equal == memcmp_equal
```

---

# 32. Serialization

Serialization:

```text id="serialize"
```

không sử dụng mặc định physical layout.

Wire format phải có schema/serialization semantics riêng.

---

# 33. Endianness

Wire representation có thể quy định:

```text id="endian"
little
big
explicit encoding
```

không liên quan trực tiếp đến in-memory default layout.

---

# 34. Niche optimization

Compiler có thể tận dụng invalid representations.

Ví dụ:

```text id="niche"
Option<Box<T>>
```

có thể dùng null-like niche trong physical representation.

Nhưng programmer không được phụ thuộc vào niche trừ khi representation contract nói rõ.

---

# 35. Enum layout

Enum:

```ax id="enum"
enum State {
    Idle,
    Running(u32),
    Error(Error),
}
```

có thể được layout:

```text id="enumlayout"
discriminant + payload
```

hoặc tối ưu bằng niche.

---

# 36. Enum + hot path

PGO có thể phát hiện:

```text id="enumhot"
Running → 99%
Error → 0.1%
Idle → 0.9%
```

Optimizer có thể tối ưu branch/layout dựa trên profile.

Semantics không thay đổi.

---

# 37. Struct field clustering

Compiler có thể gom các field thường truy cập cùng nhau:

```text id="cluster"
x,y,z
```

để cải thiện locality.

---

# 38. Access-frequency matrix

Compiler có thể xây:

```text id="matrix"
Field A accessed with B → high
Field A accessed with C → low
```

để tìm clustering.

---

# 39. Cache-aware field layout

Mục tiêu:

```text id="cache"
hot fields
→ same cache line

cold fields
→ away from hot path
```

nhưng không biến cache behavior thành language semantics.

---

# 40. False sharing

Trong concurrent structures:

```text id="false"
Thread A frequently writes field X
Thread B frequently writes field Y
```

compiler/library có thể dùng padding/alignment để giảm false sharing khi có đủ information/contract.

---

# 41. Automatic padding

Compiler có thể thêm padding.

Nhưng:

```text id="paddingobs"
@repr(C)
```

thì padding/layout phải tuân thủ ABI.

---

# 42. Structure splitting

Một object:

```text id="split3"
Hot fields
Cold fields
```

có thể physicalize thành hai regions.

Nếu pointer/address semantics không expose contiguous representation.

---

# 43. Structure merging

Một số independent objects có thể được coalesce nếu:

```text id="merge"
identity not observable
lifetime compatible
ownership valid
alignment valid
```

---

# 44. Scalar replacement

Nếu object chỉ tồn tại trong function:

```text id="scalar"
struct
↓
field SSA values
```

thì không cần physical struct.

---

# 45. Scalar replacement + layout

Đây là lý do layout optimization không chỉ dành cho heap objects.

Rất nhiều structs sẽ **không bao giờ tồn tại dưới dạng memory**.

---

# 46. Array layout

Array:

```ax id="array"
[Particle; N]
```

semantic order vẫn giữ.

Physical transformation có thể:

```text id="array2"
```

được phép nếu array layout không observable và compiler vẫn duy trì indexing semantics.

---

# 47. Nhưng fixed arrays có semantics contiguous?

Đây là điểm cần khóa.

Axiom nên quy định:

> **Array semantic ordering là bắt buộc; physical contiguity chỉ là representation property của array trong Core ABI/representation contract.**

Để tránh compiler biến array thành một cấu trúc hoàn toàn khác trong những trường hợp mà low-level code cần contiguous storage.

Với ordinary fixed array, **contiguous layout nên là guarantee**.

---

# 48. Vì vậy SoA không phải rewrite mọi array

Compiler không nên biến:

```text
[Particle; N]
```

thành:

```text
SoA
```

nếu điều đó phá vỡ guarantee của array representation.

Thay vào đó SoA transformation chỉ áp dụng khi semantic representation cho phép.

---

# 49. Explicit data-oriented container

Std có thể cung cấp:

```text id="soaapi"
SoA<T>
Column<T>
StructOfArrays<T>
```

để programmer yêu cầu data-oriented representation một cách rõ ràng.

---

# 50. Đây là sự cân bằng tốt

Có hai tầng:

```text id="balance"
Compiler automatic layout optimization
+
Explicit SoA/DOD containers
```

Compiler không cần đoán mọi trường hợp.

---

# 51. Vector-friendly layout

Compiler có thể phát hiện:

```text id="vecfriendly"
f32 fields
contiguous accesses
```

và chọn layout tốt cho vectorization.

---

# 52. Example

```ax id="particleloop"
for p in particles {
    p.position.x += velocity.x * dt;
}
```

Compiler có thể nhận:

```text id="vectorizable"
position.x
velocity.x
dt
```

và tối ưu thành vector loads/stores nếu physical representation cho phép.

---

# 53. Data layout + SIMD

```text id="layoutsimd"
Layout
  ↓
contiguous field stream
  ↓
SIMD
```

Đây là một trong những lý do layout optimizer cần tồn tại như subsystem riêng.

---

# 54. Data layout + cache

```text id="layoutcache"
Field clustering
  ↓
cache locality
  ↓
fewer cache misses
```

---

# 55. Data layout + escape

Nếu object:

```text id="noescape"
NoEscape
```

layout freedom rất cao.

Nếu:

```text id="external"
ExternalEscape
```

layout freedom thấp.

---

# 56. Data layout + ownership

Move không yêu cầu physical copy.

Do đó compiler có thể:

```text id="move"
rename SSA values
```

thay vì copy whole object.

---

# 57. Data layout + Drop

Nếu:

```text id="drop"
Drop
```

field order semantic destruction vẫn giữ nguyên.

Physical field order không được thay đổi Drop order semantics.

---

# 58. Đây là invariant rất quan trọng

Ví dụ source:

```ax id="dropstruct"
struct FilePair {
    a: File,
    b: File,
}
```

Compiler có thể physical layout:

```text
b
a
```

nhưng destruction semantic vẫn:

```text
drop b
drop a
```

theo initialization/drop rules đã khóa.

---

# 59. Data layout + capabilities

Active:

```text id="layoutcap"
view(p.field)
```

có thể tạo constraint lên physical relocation/layout.

Compiler không được thay đổi representation làm capability mất provenance.

---

# 60. Data layout + stable address

Nếu:

```text id="layoutstable"
stable address
```

thì compiler phải duy trì storage contract.

---

# 61. Data layout + async

Object fields sống qua `await` trở thành Future state.

Compiler có thể layout state machine:

```text id="asyncstate"
field clustering
state field packing
dead field elimination
```

nếu semantics giữ nguyên.

---

# 62. Data layout + GPU

GPU structures cần layout phù hợp:

```text id="gpulayout"
Host representation
≠
Device representation
```

Compiler có thể chọn device-specific layout.

---

# 63. Shared host/device structs

Không nên giả định một layout duy nhất cho cả:

```text
CPU
GPU
```

trừ khi explicit contract yêu cầu.

---

# 64. GPU ABI

Kernel arguments và device buffers có ABI riêng.

Layout optimizer phải chạy theo:

```text id="gpuabi"
GPU representation contract
```

---

# 65. Reflection

Nếu runtime reflection được bật và API yêu cầu:

```text
field offset
field order
field size
```

thì những property trở thành observable.

Compiler phải giữ metadata contract tương ứng.

---

# 66. Compile-time reflection

`comptime` có thể hỏi:

```text id="reflect"
size_of(T)
align_of(T)
offset_of(T, field)
```

Compiler trả lời theo representation đang được yêu cầu.

---

# 67. Không nên để runtime reflection mặc định

Nếu không dùng reflection:

```text id="noreflect"
```

compiler có nhiều freedom hơn.

---

# 68. Generic layout specialization

```ax id="generic"
fn process<T>(x: T)
```

có thể có physical implementation khác nhau cho:

```text
T = u64
T = SmallStruct
T = LargeStruct
```

và generic specialization engine đã có từ BOOTSTRAP-142.

---

# 69. Layout specialization + code sharing

Nếu hai generic types có cùng physical representation nhưng semantic types khác:

```text id="share"
```

compiler có thể chia sẻ machine implementation nếu không observable semantic identity bị phá.

---

# 70. Newtype

```ax id="newtype"
struct UserId(u64);
struct ProductId(u64);
```

có thể:

```text
same representation
```

nhưng:

```text
UserId ≠ ProductId
```

---

# 71. ABI boundary

Nếu:

```text id="abibound"
@export fn foo(UserId)
```

thì representation/ABI phải được cố định đủ để external caller hiểu.

---

# 72. Layout optimizer không chạy xuyên ABI

Sau:

```text
ABI MIR
```

layout contract đã được xác định.

Backend chỉ được thực hiện các transformation tương thích ABI.

---

# 73. Serialization contract

Nếu type:

```text id="serial"
@serialize(...)
```

thì wire layout là một contract riêng.

Compiler có thể vẫn tối ưu in-memory layout.

---

# 74. Đây là kiến trúc rất quan trọng

```text id="contracts"
Memory Layout
    │
    ├── Default → compiler controlled
    │
    ├── @repr(C) → C ABI
    │
    ├── @repr(transparent) → underlying representation
    │
    ├── @repr(packed) → packed contract
    │
    ├── @repr(align) → alignment contract
    │
    ├── GPU ABI → device contract
    │
    └── Serialization → wire contract
```

Không trộn các loại contract này.

---

# 75. Layout optimization modes

Compiler có thể có:

```text id="modes"
-O0
-O1
-O2
-O3
-Os
-Oz
```

Layout freedom tăng theo optimization, nhưng semantics không đổi.

---

# 76. Size optimization

`-Oz` có thể ưu tiên:

```text id="size"
smaller struct
fewer padding bytes
smaller code
smaller metadata
```

nhưng không phá ABI/representation contracts.

---

# 77. Speed optimization

`-O3` có thể ưu tiên:

```text id="speed"
cache locality
vectorization
alignment
hot/cold separation
field clustering
```

---

# 78. PGO

PGO bổ sung:

```text id="pgo"
actual field hotness
branch frequency
allocation frequency
object lifetime
cache-sensitive behavior
```

cho LayoutOptimizer.

---

# 79. Profile không phải semantics

PGO sai hoặc không đầy đủ:

```text id="pgo2"
```

chỉ khiến layout optimization kém hơn.

Không làm chương trình sai.

---

# 80. Determinism

Compiler phải có deterministic layout decision khi:

```text id="det"
same source
same compiler semantics
same target
same build config
same profile
```

→ cùng representation decision trong reproducible mode.

---

# 81. Explainability

```text id="explainlayout"
axc inspect layout Particle
```

Ví dụ:

```text
Semantic fields:
    position
    velocity
    mass
    active

Physical layout:
    position  offset=0
    velocity  offset=16
    mass      offset=32
    active    offset=36

Padding:
    3 bytes

Reason:
    alignment + hot-field clustering
```

---

# 82. Nếu bị khóa bởi FFI

```text id="ffilayout"
Layout optimization disabled

Reason:
    @repr(C)
    external ABI visible
```

---

# 83. Nếu bị khóa bởi address escape

```text id="addrlayout"
Structure splitting disabled

Reason:
    storage address escapes externally
```

---

# 84. Nếu được tự do

```text id="free"
AoS → field-specialized representation

Reason:
    no address escape
    no ABI exposure
    no reflection
    no stable-address requirement
```

---

# 85. Không để programmer phải tối ưu layout thủ công

Đây là mục tiêu:

```text id="goal"
C/C++:
    programmer often manually chooses layout

Axiom:
    programmer expresses semantic data model
    compiler chooses layout when safe
```

Tuy nhiên low-level programmer vẫn có:

```text id="lowlevel"
@repr(C)
@repr(align)
packed/system APIs
explicit SoA containers
```

khi cần kiểm soát.

---

# 86. Invariants đã khóa

### `ALAYOUT-20`
Semantic field identity is independent of physical field offset.

### `ALAYOUT-21`
Default struct layout is compiler-controlled unless explicitly contracted.

### `ALAYOUT-22`
Physical field reordering cannot change semantic field identity.

### `ALAYOUT-23`
Physical field reordering cannot change semantic Drop order.

### `ALAYOUT-24`
Physical layout optimization cannot violate ownership semantics.

### `ALAYOUT-25`
Physical layout optimization cannot invalidate capabilities.

### `ALAYOUT-26`
Stable-address contracts prevent invalid layout transformations.

### `ALAYOUT-27`
Observable addresses constrain representation optimization.

### `ALAYOUT-28`
FFI-visible representations require explicit ABI contracts.

### `ALAYOUT-29`
`@repr(C)` prevents incompatible physical reordering.

### `ALAYOUT-30`
`@repr(transparent)` preserves its representation contract.

### `ALAYOUT-31`
`@repr(packed)` is a representation/system contract.

### `ALAYOUT-32`
`@repr(align)` establishes an alignment requirement.

### `ALAYOUT-33`
Default padding is not semantic data.

### `ALAYOUT-34`
Semantic equality is distinct from bytewise equality.

### `ALAYOUT-35`
Serialization representation is distinct from memory representation.

### `ALAYOUT-36`
Endianness is a wire/representation concern, not semantic field identity.

### `ALAYOUT-37`
Niche optimization is permitted only when semantic validity is preserved.

### `ALAYOUT-38`
Enum layout is compiler-controlled unless explicitly contracted.

### `ALAYOUT-39`
Enum discriminant identity is independent of physical encoding.

### `ALAYOUT-40`
Field hotness may influence physical layout.

### `ALAYOUT-41`
PGO may influence layout decisions.

### `ALAYOUT-42`
PGO cannot alter semantic behavior.

### `ALAYOUT-43`
Hot/cold field separation requires observability analysis.

### `ALAYOUT-44`
Structure splitting requires address/ABI/reflection legality.

### `ALAYOUT-45`
Structure merging requires identity and lifetime legality.

### `ALAYOUT-46`
AoS-to-SoA transformation is permitted only where representation semantics allow it.

### `ALAYOUT-47`
Ordinary fixed arrays preserve semantic element ordering.

### `ALAYOUT-48`
Ordinary fixed arrays retain their required contiguous representation guarantee.

### `ALAYOUT-49`
Automatic SoA transformation cannot silently violate array representation guarantees.

### `ALAYOUT-50`
Explicit SoA containers may provide stronger data-oriented representation contracts.

### `ALAYOUT-51`
Layout optimization may improve SIMD locality.

### `ALAYOUT-52`
Layout optimization may improve cache locality.

### `ALAYOUT-53`
Layout optimization may reduce padding.

### `ALAYOUT-54`
Layout optimization may separate hot and cold data.

### `ALAYOUT-55`
Layout optimization may specialize generic representations.

### `ALAYOUT-56`
Newtypes may share physical representation while remaining semantically distinct.

### `ALAYOUT-57`
Representation sharing cannot merge observable semantic identities.

### `ALAYOUT-58`
Scalar replacement may eliminate physical aggregate storage.

### `ALAYOUT-59`
Aggregate elimination preserves ownership and Drop semantics.

### `ALAYOUT-60`
Layout optimization cooperates with escape analysis.

### `ALAYOUT-61`
Layout optimization cooperates with alias analysis.

### `ALAYOUT-62`
Layout optimization cooperates with MemorySSA.

### `ALAYOUT-63`
Layout optimization cooperates with SIMD/vectorization.

### `ALAYOUT-64`
Layout optimization cooperates with cache optimization.

### `ALAYOUT-65`
Layout optimization cooperates with GPU representation analysis.

### `ALAYOUT-66`
Host and device representations may differ.

### `ALAYOUT-67`
GPU ABI contracts constrain device layout.

### `ALAYOUT-68`
Runtime reflection may make layout properties observable.

### `ALAYOUT-69`
Compile-time reflection observes the representation contract requested by the program.

### `ALAYOUT-70`
Layout transformations cannot cross an incompatible ABI boundary.

### `ALAYOUT-71`
Layout decisions are target-aware.

### `ALAYOUT-72`
Layout decisions may use PGO information.

### `ALAYOUT-73`
Layout decisions remain deterministic under reproducible compilation.

### `ALAYOUT-74`
Optimization level cannot change semantic behavior.

### `ALAYOUT-75`
Failed layout optimization only reduces optimization opportunity.

### `ALAYOUT-76`
Layout transformations preserve source provenance.

### `ALAYOUT-77`
Compiler tooling can explain layout decisions.

### `ALAYOUT-78`
AI tooling can inspect semantic-to-physical field mapping.

### `ALAYOUT-79`
Layout optimization cannot create safety proofs.

### `ALAYOUT-80`
Verified MIR remains the semantic authority.

---

# Kiến trúc memory/data của Axiom lúc này

Ta đã có một chuỗi khá mạnh:

```text id="fullmemory"
             SEMANTIC DATA
                   │
                   ▼
              Ownership
                   │
                   ▼
             Capabilities
                   │
                   ▼
               Aliasing
                   │
                   ▼
               Lifetime
                   │
                   ▼
             Escape Analysis
                   │
                   ▼
              MemorySSA
                   │
          ┌────────┴────────┐
          ▼                 ▼
    Memory Optimize     Data Layout
          │                 │
          └────────┬────────┘
                   ▼
              Loop Optimize
                   │
                   ▼
              Vectorization
                   │
                   ▼
             Cache Optimize
                   │
                   ▼
              Representation
                   │
                   ▼
                 ABI
```

Đây là nền tảng rất tốt cho mục tiêu **C/C++-class performance mà không bắt programmer quản lý mọi chi tiết low-level**.

---

# BOOTSTRAP-147 — CPU Microarchitecture-Aware Optimization & Instruction-Level Optimization

Bước tiếp theo nên đi xuống **tầng CPU thực tế**.

Sau khi compiler đã biết:

- dữ liệu nằm thế nào;
- alias ra sao;
- loop thế nào;
- SIMD thế nào;

nó vẫn còn phải quyết định **instruction nào chạy tốt trên CPU cụ thể**.

Pipeline:

```text id="cpu147"
Optimized OptIR
      ↓
Instruction Selection
      ↓
Target Cost Model
      ↓
Instruction Scheduling
      ↓
Register Pressure
      ↓
Dependency Breaking
      ↓
Branch Optimization
      ↓
Instruction Fusion
      ↓
CPU Pipeline Optimization
      ↓
Machine IR
```

Đặc biệt cần khóa các vấn đề như:

- instruction latency vs throughput;
- register pressure;
- uop cost;
- branch prediction;
- instruction fusion;
- load/store ports;
- dependency chains;
- CPU-specific instruction selection;
- AVX/SSE transition;
- x86-64 vs AArch64 vs RISC-V;
- và quan trọng nhất: **Axiom phải tối ưu sâu đến mức nào mà không biến compiler thành một bộ “hard-code cho từng CPU”?**