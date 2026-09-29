# BOOTSTRAP-324 — AXIOM ABI STABILITY, BINARY COMPATIBILITY & VERSIONED INTEROPERABILITY ENGINE

Sau 323, Axiom đã có `.axif` để truyền **semantic knowledge** giữa các compilation unit.

Nhưng `.axif` mới giải quyết phần **compiler hiểu dependency**. Vẫn còn một vấn đề nền tảng:

> Khi một library được build hôm nay, chương trình được build ngày mai có thể dùng lại binary cũ đến mức nào mà không cần rebuild?

Điều này đặc biệt quan trọng với mục tiêu của Axiom:

- static library;
- shared library;
- plugin;
- OS API;
- FFI;
- package binary;
- ABI ổn định;
- hot reload/plugin;
- cross-version dependency;
- native interoperability.

Vì vậy bước tiếp theo là xây dựng **ABI Compatibility Engine** độc lập với type system và linker.

---

# 324.1. Mục tiêu

Axiom phải phân biệt rõ 4 câu hỏi:

```text
Source Compatible?
Semantic Compatible?
ABI Compatible?
Binary Compatible?
```

Ví dụ:

```text
fn foo(x: i32) -> i32
```

thay implementation nhưng giữ ABI:

```text
ABI-compatible
```

Một struct thay đổi private field:

```text
semantic/API có thể compatible
ABI có thể không compatible
```

Một library đổi calling convention:

```text
ABI incompatible
```

Một binary được build cho:

```text
x86_64-linux
```

không thể coi là compatible với:

```text
aarch64-linux
```

chỉ vì source API giống nhau.

---

# 324.2. Compatibility Matrix

Axiom định nghĩa:

```text
Compatibility {
    Source
    API
    Semantic
    ABI
    Binary
    Target
    FFI
}
```

Không được dùng một fingerprint duy nhất để đại diện cho tất cả.

Ví dụ:

```text
API compatible
Semantic compatible
ABI incompatible
```

là trạng thái hoàn toàn hợp lệ.

---

# 324.3. ABI Contract

Mỗi public binary boundary có:

```text
AbiContract {
    abi_version
    target
    architecture
    os
    calling_convention

    type_layout
    parameter_lowering
    return_lowering

    alignment
    aggregate_passing

    symbol_naming
    symbol_visibility

    panic_model
    unwind_model

    async_abi
    gpu_abi

    allocator_contract
}
```

---

# 324.4. ABI Không Phải Chỉ Là Calling Convention

Ví dụ:

```text
fn foo(x: BigStruct) -> BigStruct
```

ABI còn phải quyết định:

- truyền qua register hay memory;
- hidden return pointer;
- alignment;
- padding;
- ownership transfer;
- caller/callee cleanup;
- aggregate classification.

Do đó:

```text
Type System
    ≠
Layout
    ≠
ABI
```

Ba tầng phải tiếp tục độc lập như kiến trúc trước đã đóng băng.

---

# 324.5. ABI Type Classification

Compiler cần:

```text
AbiTypeClass
```

ví dụ:

```text
Integer
Float
Vector
Pointer
Aggregate
Tuple
Enum
Indirect
Opaque
ZeroSized
```

Sau đó target ABI quyết định cách lower.

Ví dụ:

```text
struct Vec2 {
    x: f32
    y: f32
}
```

có thể được truyền:

```text
register
```

trên target A nhưng:

```text
stack
```

trên target B.

---

# 324.6. Stable ABI vs Internal ABI

Axiom có hai loại.

### Internal Axiom ABI

Dùng giữa:

```text
Axiom compiler units
```

Có thể thay đổi giữa compiler semantic versions.

### Stable Axiom ABI

Dùng cho:

- public shared libraries;
- plugin;
- long-lived binary interfaces;
- OS-facing libraries;
- external ecosystem.

Stable ABI phải có compatibility guarantees mạnh hơn.

---

# 324.7. Không Nên Ép Mọi Type Có Stable ABI

Đây là nguyên tắc quan trọng.

Không nên mặc định:

```text
struct Foo
```

có layout cố định mãi mãi.

Thay vào đó:

```text
internal type
```

có compiler-controlled layout.

Muốn ABI stability:

```text
@stable_abi
```

hoặc một interface/ABI declaration tương đương.

---

# 324.8. ABI Boundary

Một ABI boundary được tạo khi có:

```text
@export
extern
stable_abi
plugin_entry
dynamic_library
FFI
```

Tại boundary:

```text
Semantic Type
      ↓
ABI Type
      ↓
Target ABI
```

phải được resolve hoàn toàn.

---

# 324.9. Stable Struct

Ví dụ:

```text
@repr(C)
struct Config {
    version: u32
    flags: u32
}
```

Axiom có thể đảm bảo layout C-compatible.

Nhưng:

```text
@repr(C)
```

không đồng nghĩa tự động:

```text
API stable forever
```

ABI stability còn phụ thuộc:

- field semantics;
- size;
- alignment;
- ownership;
- versioning;
- reserved fields.

---

# 324.10. Versioned ABI

Public interface phải có:

```text
AbiVersion
```

ví dụ:

```text
1.0
1.1
2.0
```

Nhưng semantic version không được tự động quyết định ABI compatibility.

Compiler phải tính:

```text
AbiCompatibilityReport
```

từ ABI contract.

---

# 324.11. ABI Compatibility Categories

```text
Exact
BackwardCompatible
ForwardCompatible
BiCompatible
Conditional
Incompatible
Unknown
```

Ví dụ thêm một optional symbol có thể:

```text
BackwardCompatible
```

nhưng thay đổi layout public struct:

```text
Incompatible
```

---

# 324.12. Symbol Compatibility

Symbol identity phải tách:

```text
SourceName
QualifiedName
AbiSymbol
LinkerSymbol
```

Ví dụ:

```text
math::sin
```

không nhất thiết trực tiếp trở thành:

```text
math__sin
```

Compiler có:

```text
SymbolIdentity
```

độc lập.

---

# 324.13. Symbol Versioning

Một shared library có thể có:

```text
foo@AXIOM_1
foo@AXIOM_2
```

Axiom linker có thể resolve version-aware symbols.

Điều này cho phép library giữ compatibility cũ.

---

# 324.14. Function ABI Compatibility

Compiler phải so sánh:

```text
parameters
return
calling convention
register classification
stack layout
alignment
variadic rules
panic behavior
unwind behavior
ownership
```

Ví dụ:

```text
fn foo(x: i32) -> i32
```

đổi thành:

```text
fn foo(x: i64) -> i32
```

→ ABI incompatible.

---

# 324.15. Ownership ABI

Đây là điểm Axiom cần mạnh hơn C ABI.

Ví dụ:

```text
fn create() -> Buffer
```

Không chỉ cần biết:

```text
return register
```

mà phải biết:

```text
ownership transferred to caller
```

Ngược lại:

```text
fn inspect(x: view<Buffer>)
```

không transfer ownership.

ABI contract phải biểu diễn semantic ownership.

---

# 324.16. Allocator ABI

Không được giả định:

```text
allocate()
```

và:

```text
deallocate()
```

có thể gọi xuyên library tùy ý.

Ví dụ:

```text
library A allocates
library B frees
```

có thể sai nếu allocator domain khác.

Do đó:

```text
AllocationDomain
```

là một phần ABI contract.

Ví dụ:

```text
AxiomRuntime
OS
CRT
CustomAllocator
Arena
Foreign
```

---

# 324.17. Ownership-Compatible FFI

Ví dụ library export:

```text
fn create() -> Buffer
```

consumer phải biết:

```text
caller owns returned Buffer
```

và cách cleanup:

```text
destroy(Buffer)
```

nếu resource domain yêu cầu.

Không được suy đoán allocator từ type.

---

# 324.18. String ABI

Không có một `String` ABI duy nhất.

Axiom phân biệt:

```text
ByteString
Utf8
Text
CString
Utf16
ForeignString
```

FFI contract phải nói rõ:

```text
encoding
termination
length
ownership
mutability
allocator
```

Ví dụ C:

```text
const char*
```

không tự động trở thành:

```text
String
```

---

# 324.19. Enum ABI

Enum public stable phải có contract về:

```text
discriminant
representation
valid values
size
alignment
niche usage
```

Nếu compiler đổi:

```text
niche optimization
```

thì ABI compatibility có thể thay đổi.

Do đó stable ABI không được phụ thuộc vào layout optimization chưa được freeze.

---

# 324.20. Option/Result ABI

Axiom có thể tối ưu:

```text
Option<T>
Result<T,E>
```

nhưng public ABI phải quyết định:

```text
stable representation
```

nếu type đi qua stable boundary.

Internal code vẫn được niche-optimize tùy ý.

---

# 324.21. Generic ABI

Generic function:

```text
fn max<T: Ord>(a: T, b: T) -> T
```

không nhất thiết có một ABI cố định.

Axiom phân biệt:

```text
generic semantic interface
```

và:

```text
monomorphized ABI instance
```

Ví dụ:

```text
max<i32>
max<i64>
max<f64>
```

có thể có ABI khác nhau.

---

# 324.22. Generic Export

Mặc định không nên export generic implementation trực tiếp qua stable binary ABI.

Thay vào đó:

```text
export specialized instance
```

hoặc:

```text
stable dynamic interface
```

Điều này tránh việc ABI của generic compiler internals trở thành public contract ngoài ý muốn.

---

# 324.23. Trait ABI

Trait:

```text
trait Writer {
    fn write(...);
}
```

không mặc định có stable binary representation.

Nếu dùng:

```text
dyn Writer
```

ở binary boundary, Axiom cần một:

```text
StableTraitABI
```

bao gồm:

- object representation;
- vtable layout;
- method ordering;
- metadata;
- drop function;
- type identity.

Nếu không có stable contract:

```text
dyn Trait
```

chỉ được dùng nội bộ cùng compiler ABI version.

---

# 324.24. ABI Versioning cho Trait

Không được cho phép:

```text
v1:
write()
flush()

v2:
flush()
write()
```

mà vẫn coi vtable compatible.

Stable trait ABI phải có:

```text
method_slot_id
```

ổn định, không chỉ index.

---

# 324.25. Closure ABI

Capturing closure không nên có stable ABI mặc định.

Internal:

```text
closure environment
```

compiler-controlled.

Nếu cần FFI:

```text
extern "C" fn(...)
```

hoặc wrapper function.

Không expose closure representation tùy tiện.

---

# 324.26. Async ABI

`async fn` tạo Future state machine.

Internal layout:

```text
compiler-controlled
```

Stable ABI không được phụ thuộc trực tiếp vào state machine layout.

Public async boundary nên dùng một contract:

```text
StableFutureABI
```

hoặc:

```text
poll/callback/opaque handle
```

---

# 324.27. Panic/Unwind ABI

ABI phải xác định:

```text
PanicBehavior
```

ví dụ:

```text
Abort
Unwind
ForeignException
NoPanic
```

Không được gọi function có:

```text
Unwind
```

qua boundary chỉ hỗ trợ:

```text
Abort
```

mà không có adapter.

---

# 324.28. FFI ABI

Các ABI chuẩn:

```text
C
C++
System
Win64
SysV64
AArch64
WASM
```

được model trong:

```text
AbiDB
```

Không hard-code ABI logic vào từng frontend declaration.

---

# 324.29. ABI Adapter

Nếu:

```text
Axiom ABI
```

và:

```text
C ABI
```

khác nhau, compiler tạo:

```text
ABI Adapter
```

```text
Axiom function
      ↓
ABI Adapter
      ↓
C function
```

Adapter phải được verifier kiểm tra ownership/effects/layout.

---

# 324.30. Binary Compatibility Engine

Thêm:

```text
AbiCompatibilityEngine
```

Input:

```text
old.axif
new.axif
```

Output:

```text
CompatibilityReport
```

Ví dụ:

```text
foo:
    signature: compatible
    calling convention: compatible
    ownership: compatible
    panic contract: changed
    ABI: incompatible
```

---

# 324.31. Compatibility Diff

Compiler phải có:

```text
axiom abi diff old.axif new.axif
```

Ví dụ:

```text
Changed:
    struct Config
        + field timeout: u32

Impact:
    layout changed
    size changed
    alignment unchanged

ABI:
    incompatible

Affected:
    libfoo ABI consumers
```

Đây là công cụ cực kỳ hữu ích cho library developer.

---

# 324.32. API Diff ≠ ABI Diff

Ví dụ:

```text
private implementation changed
```

API:

```text
unchanged
```

ABI:

```text
unchanged
```

Semantic:

```text
unchanged
```

→ consumer không cần rebuild.

Ngược lại:

```text
public struct layout changed
```

API declaration có thể gần như giống nhau nhưng:

```text
ABI changed
```

→ binary consumers phải được xử lý.

---

# 324.33. Compatibility Firewall

Compiler không được link:

```text
old binary
+
new incompatible interface
```

một cách âm thầm.

Phải có:

```text
CompatibilityFirewall
```

kiểm tra:

```text
source
semantic
ABI
target
allocator
panic
FFI
```

trước linking.

---

# 324.34. Plugin ABI

Plugin architecture:

```text
Host
  ↓
Plugin ABI
  ↓
Plugin
```

Host phải biết:

```text
PluginABI {
    abi_version
    required_host_version
    provided_symbols
    required_symbols
    type_contracts
    ownership_contracts
    allocator_contract
    threading_contract
}
```

Plugin không được giả định host dùng cùng compiler version.

---

# 324.35. ABI Capability Negotiation

Thay vì chỉ:

```text
version == 3
```

có thể:

```text
Plugin supports:
    logging.v2
    memory.v1
    gpu.v3
```

Host negotiate:

```text
common capability set
```

Điều này hữu ích cho plugin ecosystem lâu dài.

---

# 324.36. Binary Package Compatibility

Package binary metadata:

```text
AxiomBinaryPackage {
    package_id
    package_version

    axif
    objects
    targets
    abi_contracts
    required_runtime
}
```

Compiler chọn artifact:

```text
target
ABI
CPU features
runtime profile
```

---

# 324.37. CPU Feature Compatibility

Binary có thể yêu cầu:

```text
AVX2
AVX512
SVE
NEON
```

Đây là:

```text
TargetFeatureContract
```

Không được coi:

```text
x86_64
```

là đủ để binary chạy trên mọi x86_64 CPU.

---

# 324.38. Multi-Version Binary

Axiom có thể hỗ trợ:

```text
foo.baseline
foo.avx2
foo.avx512
```

runtime dispatch:

```text
CPU features
    ↓
select implementation
```

Nhưng semantic contract của mọi variant phải tương đương.

---

# 324.39. ABI + `.axif`

323 cung cấp:

```text
SemanticSummary
```

324 bổ sung:

```text
AbiContract
```

Do đó:

```text
.axif
├── Semantic Interface
├── Semantic Summaries
├── ABI Contract
└── Compatibility Metadata
```

Không cần tạo một artifact semantic khác.

---

# 324.40. Integration với Linker 303

Linker trước khi resolve:

```text
symbol
```

phải có thể hỏi:

```text
AbiCompatibilityEngine
```

Ví dụ:

```text
foo@ABI3
```

vs:

```text
foo@ABI4
```

→ reject hoặc tìm adapter/version phù hợp.

---

# 324.41. Integration với Image Builder 304

Executable metadata có thể chứa:

```text
required ABI
required runtime
required CPU features
required dynamic libraries
```

Image builder kiểm tra consistency.

---

# 324.42. Integration với Package System 308

Package resolver phải có thể chọn:

```text
package version
+
target
+
ABI
+
runtime
+
CPU feature
```

Ví dụ:

```text
foo 2.4
    ABI 3
    x86_64
    Linux
```

khác:

```text
foo 2.4
    ABI 4
    x86_64
    Linux
```

---

# 324.43. Integration với Security 314

ABI artifact cần provenance:

```text
AbiProvenance {
    compiler
    spec
    target
    source_fingerprint
    build_identity
}
```

Nếu binary được ký:

```text
signature
```

có thể bao phủ:

```text
.axif
+
object
+
ABI metadata
```

---

# 324.44. Integration với 323

`.axif` semantic facts:

```text
ownership
effects
capabilities
```

không được tách khỏi ABI contract.

Ví dụ:

```text
fn create() -> Buffer
```

ABI compatibility chỉ đúng nếu:

```text
return ABI
+
ownership semantics
+
allocator domain
```

đều compatible.

---

# 324.45. Compiler API

```text
check_abi_compatibility()
```

```text
compare_abi()
```

```text
diff_abi()
```

```text
compute_abi_fingerprint()
```

```text
validate_abi_contract()
```

```text
resolve_abi_version()
```

```text
find_abi_adapter()
```

```text
check_plugin_compatibility()
```

```text
check_binary_compatibility()
```

```text
explain_abi_break()
```

```text
generate_abi_adapter()
```

```text
query_target_abi()
```

---

# 324.46. CLI

```text
axiom abi inspect lib.axif
```

```text
axiom abi diff old.axif new.axif
```

```text
axiom abi check package
```

```text
axiom abi verify plugin
```

```text
axiom abi explain-change
```

Ví dụ:

```text
$ axiom abi diff v1.axif v2.axif

ABI BREAK:
    Config.size: 32 → 40
    Config.layout: changed

SEMANTIC:
    compatible

API:
    compatible

BINARY:
    incompatible

Affected:
    libfoo.so consumers
```

---

# 324.47. Implementation Tree

```text
compiler/abi/
├── model/
│   ├── contract.ax
│   ├── type_class.ax
│   ├── calling_convention.ax
│   ├── layout.ax
│   └── target.ax
│
├── lowering/
│   ├── parameter.ax
│   ├── return.ax
│   ├── aggregate.ax
│   ├── enum.ax
│   └── generic.ax
│
├── compatibility/
│   ├── checker.ax
│   ├── classifier.ax
│   ├── diff.ax
│   ├── firewall.ax
│   └── report.ax
│
├── versioning/
│   ├── abi_version.ax
│   ├── symbol_version.ax
│   └── capability.ax
│
├── adapters/
│   ├── generator.ax
│   ├── ownership.ax
│   ├── allocator.ax
│   ├── panic.ax
│   └── ffi.ax
│
├── plugin/
│   ├── contract.ax
│   ├── negotiation.ax
│   └── loader.ax
│
├── fingerprint/
│   ├── abi.ax
│   └── binary.ax
│
└── database/
    └── abi_db.ax
```

---

# 324.48. Invariants

```text
AABI-20  API compatibility and ABI compatibility are distinct properties.

AABI-21  Semantic compatibility and ABI compatibility are distinct properties.

AABI-22  Internal compiler layout is not automatically a stable ABI.

AABI-23  Stable ABI requires an explicit ABI contract.

AABI-24  ABI contracts include calling convention and data representation.

AABI-25  Ownership semantics at ABI boundaries are part of compatibility.

AABI-26  Allocation domains at ABI boundaries are explicit.

AABI-27  Panic/unwind behavior is part of ABI compatibility.

AABI-28  Async ABI is distinct from internal Future representation.

AABI-29  Trait object ABI is not stable unless explicitly contracted.

AABI-30  Closure representation is not stable by default.

AABI-31  Generic implementation ABI is not automatically stable.

AABI-32  FFI ABI must be explicit.

AABI-33  ABI adapters must preserve semantic contracts.

AABI-34  ABI incompatibility must be detected before unsafe linking.

AABI-35  Binary compatibility depends on target compatibility.

AABI-36  CPU feature requirements are part of binary compatibility.

AABI-37  Symbol identity is distinct from source name.

AABI-38  Symbol versioning must preserve ABI identity.

AABI-39  ABI fingerprints must be deterministic.

AABI-40  ABI changes must participate in incremental invalidation.

AABI-41  Stable ABI types must not depend on unfrozen optimization choices.

AABI-42  Private implementation changes must not create false ABI breaks.

AABI-43  ABI compatibility reports must identify the concrete breaking property.

AABI-44  Unknown ABI compatibility must not be treated as compatible.

AABI-45  Plugin boundaries require explicit version/capability negotiation.

AABI-46  FFI boundaries must declare allocator and ownership contracts where relevant.

AABI-47  Multi-version implementations must preserve semantic equivalence.

AABI-48  ABI metadata participates in binary provenance.

AABI-49  ABI checks cannot weaken ownership, capability, security, or correctness verification.

AABI-50  Axiom must support runtime-free ABI boundaries.
```

---

# 324.49. Definition of Done

BOOTSTRAP-324 hoàn thành khi:

1. Có `AbiContract`.
2. Có `AbiDB`.
3. Có target ABI database.
4. Có ABI type classification.
5. Có parameter/return lowering model.
6. Có stable ABI mode.
7. Có internal ABI mode.
8. Có ABI fingerprint.
9. Có ABI compatibility checker.
10. Có semantic/API/ABI compatibility distinction.
11. Có ABI diff engine.
12. Có symbol identity/versioning.
13. Có ownership-aware ABI.
14. Có allocator-aware ABI.
15. Có panic/unwind ABI.
16. Có async ABI.
17. Có trait-object ABI model.
18. Có generic ABI model.
19. Có FFI ABI adapters.
20. Có plugin ABI.
21. Có capability negotiation.
22. Có CPU-feature compatibility.
23. Có binary compatibility validation.
24. Có linker integration.
25. Có package-manager integration.
26. Có `.axif` integration.
27. Có security/provenance integration.
28. Có deterministic ABI metadata.
29. Có ABI breaking-change diagnostics.
30. Có test old/new library compatibility.
31. Có test ABI mismatch detection.
32. Có test allocator mismatch.
33. Có test panic-model mismatch.
34. Có test struct-layout break.
35. Có test trait-vtable break.
36. Có test generic boundary.
37. Có test plugin compatibility.
38. Có test FFI adapter.
39. Có test cross-target rejection.
40. Có test multi-version binary dispatch.
41. Có test ABI-compatible implementation replacement không rebuild consumer.
42. Có test ABI-incompatible change bắt buộc invalidation.
43. Có test `.axif` + binary + linker consistency.

---

## Nguyên tắc đóng băng của 324

> **Axiom không mặc định ổn định binary layout của mọi thứ; Axiom chỉ cam kết ABI stability ở những boundary mà lập trình viên hoặc package contract yêu cầu.**

Điều này giữ được cả hai mục tiêu:

```text
Internal code
→ compiler tự do tối ưu layout tối đa
```

và:

```text
Public ABI
→ contract ổn định, kiểm chứng được, version được
```

Kiến trúc hiện tại vì vậy đã hình thành chuỗi khá hoàn chỉnh:

```text
318  Semantic Equivalence
 ↓
319  Proof-Carrying Passes
 ↓
320  Adaptive Optimization
 ↓
321  Whole-Program Analysis
 ↓
322  PGO / Auto-Tuning
 ↓
323  Semantic Interface (.axif)
 ↓
324  ABI / Binary Compatibility
```

Bước này đặc biệt quan trọng trước khi đi sâu hơn vào **plugin, dynamic loading, hot reload và binary ecosystem**, vì nếu chưa khóa được ABI contract thì các hệ thống đó rất dễ tạo ra những ngoại lệ phá vỡ ownership/capability model của Axiom.