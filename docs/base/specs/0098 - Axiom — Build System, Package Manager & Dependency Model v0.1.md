Tiếp tục.

# Axiom — Build System, Package Manager & Dependency Model v0.1

Phần này tôi muốn thiết kế theo hướng **đơn giản hơn Cargo/CMake/npm**, nhưng không đánh đổi khả năng xây dựng project lớn.

Nguyên tắc:

> **Build system là công cụ; package system là dependency graph; compiler chỉ chịu trách nhiệm compile semantics.**

Không để compiler trở thành package manager.

---

# 1. Tách 4 khái niệm

Axiom cần phân biệt:

```text
Package
Module
Artifact
Workspace
```

### Package

Đơn vị phân phối:

```text
my_app/
    axiom.toml
```

### Module

Đơn vị namespace/source:

```text
app
app.audio
app.renderer
```

### Artifact

Kết quả build:

```text
.exe
ELF
.dylib
.so
.a
.lib
.o
```

### Workspace

Nhiều package cùng phát triển:

```text
workspace/
    axiom.toml
    compiler/
    std/
    tools/
```

---

# 2. Một package không nhất thiết chỉ có một executable

Ví dụ:

```text
graphics/
    library
    tools
    examples
    tests
```

Một package có thể tạo:

```text
library
binary
test binary
benchmark binary
generated bindings
```

---

# 3. `axiom.toml`

Tôi đề xuất metadata rất nhỏ:

```toml
[package]
name = "my_app"
version = "0.1.0"

[targets]
kind = "binary"

[dependencies]
math = "1.2"
image = "2.0"
```

Không nên biến file này thành một programming language.

---

# 4. Dependency specification

Cho phép:

```toml
math = "1.2"
```

hoặc:

```toml
math = { version = "1.2", features = ["simd"] }
```

hoặc:

```toml
math = { path = "../math" }
```

hoặc:

```toml
math = { git = "...", rev = "..." }
```

Git dependency nên là **development/distribution mechanism**, không phải dependency identity cuối cùng.

---

# 5. Lock file

Project application nên có:

```text
axiom.lock
```

Nó ghi:

```text
package
version
source
content hash
dependency graph
```

Build phải resolve:

```text
axiom.toml
      ↓
lock
      ↓
exact dependency graph
```

---

# 6. Content hash

Tôi khuyến nghị package identity không chỉ dựa trên:

```text
name + version
```

mà:

```text
name
version
source
content hash
```

Ví dụ:

```text
sha256(...)
```

Điều này giúp reproducibility và supply-chain verification.

---

# 7. Semantic package identity

Compiler không cần biết Git URL.

Nó nhận:

```text
ResolvedPackage
```

với:

```text
PackageId
Version
ContentHash
InterfaceFingerprint
```

---

# 8. Semantic Interface Fingerprint

Ta đã định nghĩa SIF.

Ví dụ:

```text
Package
 ↓
public declarations
 ↓
generic definitions
 ↓
ABI contracts
 ↓
attributes
 ↓
SIF
```

Nếu implementation private thay đổi nhưng public semantic interface không đổi:

```text
SIF unchanged
```

→ incremental compilation có thể giữ lại downstream artifacts.

---

# 9. Dependency graph

Ví dụ:

```text
app
├── graphics
│   ├── math
│   └── image
└── audio
    └── math
```

Package manager phải deduplicate:

```text
math
```

nếu version compatible.

---

# 10. Không dùng dependency version ambiguity

Nếu:

```text
graphics → math 1.x
audio    → math 2.x
```

không nên tự ý chọn một version.

Graph có thể:

```text
math@1
math@2
```

cùng tồn tại nếu type identity được quản lý đúng.

---

# 11. Nhưng type identity giữa package versions phải rõ

```text
math@1::Vec2
```

và:

```text
math@2::Vec2
```

không mặc định là cùng type.

Điều này tránh ABI/type confusion.

---

# 12. Re-export

Package A:

```axiom
pub import math.Vec2
```

package user có thể thấy:

```text
A::Vec2
```

nhưng semantic type identity vẫn giữ nguồn gốc.

---

# 13. Feature flags

Feature nên chỉ điều khiển:

```text
optional implementation
optional module
optional backend
```

Không được thay đổi language semantics.

Ví dụ:

```toml
features = ["avx2", "png"]
```

hợp lý.

Nhưng:

```text
feature = "different_ownership_rules"
```

không hợp lệ.

---

# 14. Feature unification

Nếu:

```text
A → lib(feature=a)
B → lib(feature=b)
```

package resolver phải có deterministic rule.

Có thể:

```text
features = union(a,b)
```

nhưng nếu feature conflict:

```text
compile error
```

Không được chọn ngẫu nhiên.

---

# 15. Target-specific dependencies

Ví dụ:

```toml
[target.linux.dependencies]
epoll = "..."

[target.windows.dependencies]
iocp = "..."
```

Nhưng platform abstraction nên nằm trong std/library khi có thể.

---

# 16. Build profiles

Nên có:

```text
dev
release
test
bench
size
debug
freestanding
```

Ví dụ:

```text
release:
    optimization = aggressive
    debug_info = false
```

```text
size:
    optimization = size
    lto = true
```

---

# 17. Optimization profile

Không nên chỉ có:

```text
-O0
-O1
-O2
-O3
```

Axiom có thể có:

```text
speed
size
balanced
debug
```

Compiler mapping:

```text
speed → inlining/vectorization/PGO opportunities
size → code-size aware optimization
```

---

# 18. Nhưng semantics không được thay đổi

`--opt=speed` không được biến:

```text
checked integer
```

thành:

```text
wrapping integer
```

Optimization profile chỉ thay đổi implementation.

---

# 19. Fast-math là ngoại lệ

Vì fast-math thay đổi floating semantics, nó phải là explicit semantic/profile choice:

```text
--float-mode=strict
--float-mode=fast
```

hoặc module/function attribute.

Compiler phải ghi nó vào compilation configuration/fingerprint.

---

# 20. Reproducible builds

Hai máy:

```text
machine A
machine B
```

với cùng:

```text
source
lock
compiler version
target
build config
```

nên tạo artifact byte-identical nếu target/toolchain deterministic.

---

# 21. Nhưng timestamp không được lọt vào binary

Compiler/linker phải tránh:

```text
build timestamp
machine path
random UUID
```

trừ khi explicit.

---

# 22. Build ID

Debugging vẫn cần build identity.

Có thể:

```text
BuildId = hash(source + compiler + target + config)
```

thay vì timestamp.

---

# 23. Build cache

Axiom có thể có:

```text
~/.axiom/cache/
```

cache key:

```text
Package content
Compiler version
Target
Features
Optimization
Relevant environment
```

---

# 24. Không cache theo filename

Không nên:

```text
foo.axiom → foo.o
```

một cách đơn giản.

Vì:

```text
same filename
different source
```

sẽ gây stale artifacts.

Hash-based cache an toàn hơn.

---

# 25. Incremental compilation

Graph:

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
Verified MIR
 ↓
LIR
 ↓
Object
```

Có thể cache từng stage.

---

# 26. Nhưng cache semantic stages trước

Ưu tiên:

```text
AST/HIR
Typed HIR
MIR
Verified MIR
```

Sau đó:

```text
LIR/object
```

vì backend target-specific.

---

# 27. Generic compilation

Ví dụ:

```axiom
fn max<T: Ord>(...)
```

Không cần instantiate tất cả ngay.

Chỉ instantiate:

```text
max<i32>
max<f32>
```

nếu được dùng.

---

# 28. Cross-package generics

Package interface phải chứa generic semantic body đủ để downstream specialize.

Không thể chỉ ship:

```text
max<T>
```

signature mà không có implementation nếu muốn monomorphization.

Do đó package artifact có:

```text
public semantic IR
```

hoặc source/interface representation.

---

# 29. ABI package artifact

Đối với dynamic libraries, cần ABI-stable interface.

Nhưng Axiom native ABI:

```text
compiler-version dependent
```

như đã chốt.

Do đó:

```text
Axiom package
```

không nên mặc định hứa:

> binary ABI ổn định mãi mãi.

---

# 30. Stable ABI

Nếu muốn plugin lâu dài:

```text
extern "C"
@repr(C)
```

hoặc một ABI versioned explicit.

Ví dụ tương lai:

```text
extern "axiom-v1"
```

---

# 31. Build script

Đây là phần tôi muốn **khác Cargo**.

Không nên mặc định cho package chạy:

```text
build.sh
```

arbitrary shell code.

Vì:

```text
download package
↓
compile
↓
execute arbitrary code
```

là supply-chain risk lớn.

---

# 32. Không có arbitrary build script mặc định

Thay vào đó:

```text
code generation
native compilation
resource generation
binding generation
```

được mô tả declaratively.

Ví dụ:

```toml
[generate]
input = "schema/foo.idl"
output = "src/generated.axiom"
tool = "axiom-bindgen"
```

---

# 33. Nếu cần arbitrary code?

Cho phép:

```text
build capability
```

explicit.

Ví dụ:

```text
axiom build --allow-build-code
```

hoặc package metadata:

```toml
[build]
requires_process = true
requires_network = true
```

Build system phải cảnh báo/hiển thị.

---

# 34. Sandbox build

Tốt hơn nữa:

```text
Build Environment
 ├── source: read
 ├── output: write
 ├── package cache: read
 ├── network: denied
 ├── process: denied
 └── filesystem: restricted
```

Code generation bình thường không cần Internet.

---

# 35. Build capabilities

Có thể:

```text
Capability:
    ReadSource
    WriteGenerated
    ExecuteTool
    Network
    Environment
    Filesystem
```

Package khai báo capability.

Build engine cấp capability.

---

# 36. Đây rất phù hợp với Axiom

Ta đã có triết lý:

> Explicit at semantic boundaries.

Build system cũng áp dụng:

```text
normal build
→ deterministic/sandboxed

exceptional build
→ explicit capability
```

---

# 37. FFI binding generation

Ví dụ:

```text
foo.h
 ↓
axiom bindgen
 ↓
foo.axiom
```

Tool chạy trong build environment.

Compiler cuối cùng chỉ compile:

```text
foo.axiom
```

Không cần Clang làm compiler dependency cuối cùng.

---

# 38. Native dependency

Nếu package cần C library:

```toml
[native]
libraries = ["z"]
```

Build system tìm:

```text
system library
package-provided binary
source build
```

theo policy.

---

# 39. Axiom-native dependency

Ưu tiên:

```text
Axiom source
 ↓
Axiom compiler
 ↓
Axiom object
```

Không cần C compiler.

---

# 40. C dependency

Nếu cần C:

```text
extern "C"
```

là ABI boundary.

Nhưng build tool có thể compile C source **nếu compiler C được explicit cung cấp**.

Axiom final toolchain không phụ thuộc vào C compiler để compile Axiom itself.

---

# 41. Package registry

Registry nên lưu:

```text
package
version
archive
hash
metadata
signature
dependencies
```

Không cần registry server hiểu source semantics.

---

# 42. Package signing

Có thể hỗ trợ:

```text
publisher signature
artifact hash
transparency log
```

nhưng không nên bắt buộc mọi package phải dùng một central authority.

---

# 43. Offline build

Nếu:

```text
axiom.lock
cache đầy đủ
```

thì:

```text
axiom build --offline
```

phải hoạt động.

Không được tự động gọi Internet.

---

# 44. Vendoring

Cho phép:

```text
axiom vendor
```

đưa dependency vào:

```text
vendor/
```

Build hoàn toàn offline.

---

# 45. Workspace

Ví dụ chính compiler:

```text
axiom/
├── axiom.toml
├── compiler/
├── std/
├── runtime/
├── targets/
├── tools/
└── tests/
```

Mỗi module/package có thể build incremental.

---

# 46. Compiler bootstrap

Workspace cần hỗ trợ:

```text
stage0 compiler
      ↓
build stage1 compiler
      ↓
stage1 builds itself
      ↓
stage2
```

Cuối cùng:

```text
Axiom compiler
```

tự compile bằng chính Axiom.

---

# 47. Bootstrap compiler không phải dependency của language

Stage0 có thể là:

```text
prototype compiler
```

viết bằng:

```text
C
Rust
Axiom subset
```

nhưng đó chỉ là bootstrap artifact.

Mục tiêu:

```text
stageN compiler
```

không còn cần source dependency của stage0.

---

# 48. Compiler determinism

Build phải có:

```text
--deterministic
```

và compiler tránh:

```text
hash-map random order
random symbol ordering
unstable traversal
```

trong semantic output.

---

# 49. Parallel compilation

Package graph:

```text
A
├── B
├── C
└── D
```

có thể compile:

```text
B ─┐
C ─┼→ A
D ─┘
```

song song.

Compiler internals cũng có thể parallelize:

```text
module
function
generic instantiation
backend
```

nhưng output phải deterministic.

---

# 50. Dependency cycles

Package cycle:

```text
A → B
B → A
```

tôi đề xuất **không cho phép** ở package level.

Module-level cycle có thể được phép trong declaration-only scenarios, như đã chốt.

Package graph DAG giúp:

- build
- cache
- versioning
- incremental compilation

đơn giản hơn rất nhiều.

---

# 51. Module cycle

Ví dụ:

```text
Axiom module A
 └── type A
     references B::Type

module B
 └── references A::Type
```

Nếu không tạo recursive layout vô hạn thì compiler có thể resolve.

---

# 52. Package cycle khác hoàn toàn

Package là distribution/build unit.

Cho phép:

```text
A package → B package → A package
```

sẽ làm:

```text
version resolution
bootstrap
build order
cache
```

phức tạp.

→ **Reject package cycles.**

---

# 53. Dependency features không được thay semantic identity

Nếu:

```text
lib(feature=simd)
```

và:

```text
lib(feature=scalar)
```

cùng package identity nhưng tạo type layout khác nhau, đó là vấn đề.

Feature phải được đưa vào:

```text
Build Configuration Fingerprint
```

và package instance.

---

# 54. Build configuration

Một compilation unit identity nên conceptually:

```text
CompilationKey =
    SourceHash
    CompilerVersion
    LanguageVersion
    Target
    ABI
    Features
    OptimizationProfile
    FloatMode
    RelevantFlags
```

---

# 55. Không dùng environment variable ngầm

Ví dụ:

```text
CFLAGS
RUSTFLAGS
CC
```

không nên âm thầm thay đổi semantic build.

Nếu environment ảnh hưởng compilation:

```text
explicit build input
```

và được đưa vào fingerprint.

---

# 56. Toolchain manifest

Có thể có:

```text
axiom-toolchain.toml
```

chứa:

```text
compiler version
stdlib version
target support
linker
sysroot
```

nhưng Axiom cuối cùng có thể tự chứa linker/backend.

---

# 57. Sysroot

Compiler cần biết:

```text
core
runtime
std
platform
```

để compile target.

Ví dụ:

```text
sysroot/
 ├── core/
 ├── std/
 ├── linux/
 ├── windows/
 └── wasm/
```

---

# 58. `core` đặc biệt

`core` phải build được trước:

```text
stdlib
```

và không phụ thuộc:

```text
stdlib
```

tránh circular bootstrap.

---

# 59. Build graph cuối cùng

```text
Package
   ↓
Dependency Resolution
   ↓
Workspace Graph
   ↓
Module Graph
   ↓
Semantic Interface
   ↓
Typed HIR
   ↓
Verified MIR
   ↓
Target LIR
   ↓
Object
   ↓
Link
   ↓
Artifact
```

---

# 60. Package invariants

Chốt:

```text
APKG-01  Package Is A Distribution Unit
APKG-02  Module Is A Semantic Namespace Unit
APKG-03  Artifact Is A Build Output
APKG-04  Workspace Groups Related Packages
APKG-05  Package Graph Is Acyclic
APKG-06  Module Cycles May Exist Under Semantic Rules
APKG-07  Lock File Records Exact Dependencies
APKG-08  Dependency Identity Includes Content
APKG-09  Package Version Alone Is Not Full Identity
APKG-10  Semantic Interface Fingerprints Enable Incremental Builds
APKG-11  Generic Implementations Are Available For Specialization
APKG-12  Native Axiom ABI Is Not Automatically Stable
APKG-13  Stable ABI Requires Explicit ABI Contract
APKG-14  Features Cannot Change Core Language Semantics
APKG-15  Build Profiles Cannot Change Program Correctness
APKG-16  Build Artifacts Are Content-Addressable
APKG-17  Incremental Compilation Is Semantic
APKG-18  Builds Are Deterministic
APKG-19  Parallel Builds Preserve Deterministic Results
APKG-20  Offline Builds Are Supported
APKG-21  Vendoring Is Supported
APKG-22  Arbitrary Build Code Is Not Default
APKG-23  Build Capabilities Are Explicit
APKG-24  Build Sandboxing Is Supported
APKG-25  Network Access Is Not Implicit
APKG-26  Process Execution Is Not Implicit
APKG-27  FFI Binding Generation Is A Build Artifact
APKG-28  Native Dependencies Are Explicit
APKG-29  Axiom Does Not Require A C Compiler For Axiom Compilation
APKG-30  Bootstrap Dependencies Are Temporary
APKG-31  Package Resolver Is Separate From Compiler Semantics
APKG-32  Build Configuration Is Part Of Compilation Identity
APKG-33  Hidden Environment State Must Not Alter Semantic Builds
APKG-34  Core Builds Before Std
APKG-35  Package Management Cannot Redefine Language Semantics
```

---

# 61. Một quyết định lớn tôi muốn giữ

Axiom không nên cố trở thành:

> **“một hệ sinh thái khổng lồ tích hợp mọi thứ vào compiler”**

Mà nên là:

```text
                 AXIOM TOOLCHAIN

        ┌────────────┬──────────────┐
        │            │              │
     Compiler      Builder       Package
        │            │              │
        └────────────┼──────────────┘
                     │
              deterministic graph
                     │
          ┌──────────┼──────────┐
          │          │          │
        Source      Cache      Registry
```

Compiler tập trung vào **language + optimization + native code**.

Build system tập trung vào **graph + reproducibility**.

Package manager tập trung vào **distribution + versions**.

---

# Tiếp tục → Toolchain tự chủ & Linker/Assembler/Object Format

Bây giờ chúng ta đã gần đến một cột mốc quan trọng: **Axiom có đủ language semantics để bắt đầu thiết kế toolchain thật sự**.

Phần tiếp theo tôi sẽ chốt:

```text
Axiom Compiler
        ↓
Machine Encoder
        ↓
Object Writer
        ↓
Axiom Linker
        ↓
PE / ELF / Mach-O / WASM
```

và đặc biệt:

- có cần assembler không;
- có cần LLVM không;
- relocation model;
- symbol resolution;
- static/shared linking;
- TLS;
- weak/strong symbols;
- COMDAT;
- section GC;
- ICF;
- LTO;
- debug information;
- DWARF/PDB;
- linker script;
- import/export;
- PE/ELF/Mach-O khác nhau thế nào;
- làm sao để **cuối cùng Axiom có thể tự build chính nó từ source → native executable mà không cần GCC/Clang/MSVC/LLVM**.

Đây sẽ là phần trực tiếp biến mục tiêu “ngôn ngữ mới” thành **một toolchain native hoàn chỉnh**.