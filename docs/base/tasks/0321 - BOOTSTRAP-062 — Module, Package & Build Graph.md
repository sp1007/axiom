Tiếp tục với **BOOTSTRAP-062 — Module System, Package Resolution, Dependency Graph & Build Graph**.

Ở BOOTSTRAP-042 chúng ta đã freeze các nguyên tắc package/build. Vì vậy 062 **không thay đổi semantics đã đóng băng**, mà chuyển chúng thành một kiến trúc đủ cụ thể để sau này `axiomc` + package manager có thể thực sự triển khai.

---

# BOOTSTRAP-062 — Module, Package & Build Graph

## 1. Mục tiêu

Axiom cần giải quyết đồng thời:

```text
source
  ↓
module
  ↓
package
  ↓
workspace
  ↓
dependency graph
  ↓
build graph
  ↓
artifact graph
  ↓
native executable / library / wasm / GPU
```

và phải đảm bảo:

- build deterministic;
- incremental;
- parallel;
- cross-platform;
- cross-compilation;
- dependency isolation;
- không cần C/C++ compiler;
- không có hidden build runtime;
- package manager không trở thành một ngôn ngữ lập trình thứ hai.

---

# 2. Phân biệt 4 khái niệm

Đây là điểm cần freeze rất rõ.

```text
Module
Package
Workspace
Artifact
```

### Module

Đơn vị namespace + semantic declarations.

### Package

Đơn vị version/dependency/distribution.

### Workspace

Nhóm nhiều package cùng phát triển.

### Artifact

Kết quả build.

Ví dụ:

```text
Workspace
├── axiomc
├── axiom-core
├── axiom-std
└── axiom-test

          ↓

Artifacts
├── axiomc.exe
├── libaxiom_core.a
├── libaxiom_std.a
└── metadata.axmeta
```

---

# 3. Module không nhất thiết = file

Không freeze:

```text
one file = one module
```

Filesystem chỉ là mapping mặc định.

Có thể:

```text
src/
    math.ax
```

tương ứng:

```text
math
```

nhưng compiler semantic identity vẫn là `ModuleId`.

---

# 4. Module declaration

Tôi đề xuất cú pháp đơn giản:

```axiom
module math.vector

pub struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

Không cần bắt buộc mỗi file phải khai báo module nếu filesystem mapping đã đủ rõ.

---

# 5. Import

```axiom
import math.vector
```

hoặc:

```axiom
import math.vector.Vec3
```

Có thể hỗ trợ alias:

```axiom
import math.vector as vec
```

---

# 6. Import không phải runtime execution

Điều này cực kỳ quan trọng:

```text
import
```

chỉ có nghĩa:

```text
resolve declarations
load semantic metadata
compile dependency if required
```

Không có:

```text
import
→ chạy code module
```

---

# 7. Export

Visibility:

```axiom
pub struct Vec3
```

khác với native symbol export.

Ví dụ:

```axiom
@export("my_vec_add")
pub fn add(...)
```

`pub`:

> source-level visibility.

`@export`:

> binary-level external symbol contract.

Đã freeze từ ABI/build system.

---

# 8. Private mặc định

```axiom
struct InternalThing {}
```

private.

Chỉ:

```axiom
pub
```

mới trở thành public API của module/package theo visibility rules.

---

# 9. Package manifest

Đề xuất:

```text
axiom.toml
```

Ví dụ:

```toml
[package]
name = "my_app"
version = "0.1.0"

[dependencies]
json = "1.4"
image = "2.1"
```

Manifest là **declarative data**, không phải Axiom program.

---

# 10. Không có `build.ax` mặc định

Tôi tiếp tục giữ quyết định trước:

Không tạo:

```text
build.ax
```

như một ngôn ngữ build thứ hai.

Nếu build logic cần computation:

```text
comptime
```

hoặc một build capability API bị giới hạn.

---

# 11. Dependency phases

Mỗi dependency thuộc một phase:

```text
runtime
build
comptime
test/dev
```

Ví dụ:

```toml
[dependencies]
foo = "1.0"

[build-dependencies]
codegen_tool = "2.0"

[dev-dependencies]
test_framework = "1.2"
```

---

# 12. Runtime dependency

```text
A → B
```

nghĩa là artifact runtime của A có thể cần B.

---

# 13. Build dependency

```text
A
├── build dependency B
└── runtime dependency C
```

B chỉ tồn tại trong build environment.

Không được tự động lọt vào executable.

---

# 14. Comptime dependency

Nếu:

```axiom
comptime {
    ...
}
```

đọc metadata từ package khác, dependency graph phải ghi nhận nó.

Điều này rất quan trọng cho incremental compilation.

---

# 15. Test dependency

Test-only package:

```text
test
 ↓
dev dependency
```

không được xuất hiện trong release artifact.

---

# 16. Dependency graph

Ví dụ:

```text
app
├── graphics
│   ├── math
│   └── gpu
├── json
│   └── unicode
└── std
    └── core
```

Compiler/build system biến thành DAG.

---

# 17. Package cycles

Mặc định:

```text
A → B
B → A
```

**reject**.

Package dependency graph phải là DAG.

---

# 18. Module cycles

Module cycles là vấn đề khác.

Có thể cho phép một số:

```text
module A
 ↕
module B
```

nếu resolver có thể xử lý declaration graph.

Nhưng package cycle vẫn bị cấm.

---

# 19. Declaration graph

Compiler không build module theo thứ tự file đơn giản.

Nó xây:

```text
PackageGraph
    ↓
ModuleGraph
    ↓
DeclarationGraph
    ↓
Type/Trait dependency graph
```

Do đó forward references có thể được hỗ trợ tự nhiên.

---

# 20. Package identity

Identity:

```text
PackageId =
    name
    + version
    + source identity
```

Không dùng:

```text
filesystem path
```

làm semantic identity.

---

# 21. Hai version cùng tồn tại

Ví dụ:

```text
app
├── A → math@1
└── B → math@2
```

có thể tồn tại đồng thời nếu dependency graph yêu cầu.

Nhưng:

```text
math@1::Vec3
```

và:

```text
math@2::Vec3
```

là hai nominal types khác nhau.

Không implicit convert.

---

# 22. Dependency resolution

Resolver phải giải:

```text
constraints
→ candidate versions
→ source identity
→ feature configuration
→ target configuration
→ final resolved graph
```

---

# 23. Lock file

Kết quả resolution được lưu:

```text
axiom.lock
```

Ví dụ conceptually:

```text
package
version
source
content_hash
dependencies
```

---

# 24. Content hash

Không chỉ:

```text
json@1.4
```

mà còn:

```text
source identity
+
content hash
```

để chống việc package cùng version nhưng nội dung thay đổi.

---

# 25. Registry

Có thể có official registry:

```text
registry.axiom
```

nhưng compiler **không tự network fetch**.

Package manager chịu trách nhiệm.

---

# 26. Offline build

Nếu dependency đã cache:

```text
axiom build --offline
```

vẫn phải build được.

---

# 27. Compiler không quản lý network

Kiến trúc:

```text
axiom
   ↓
package manager
   ↓
registry/git/local/archive
```

thay vì:

```text
axiomc
   ↓
internet
```

Điều này giúp compiler deterministic hơn.

---

# 28. Source types

Dependency source có thể:

```text
registry
git
local
archive
system
```

đã được freeze.

---

# 29. Workspace

Ví dụ:

```text
axiom/
├── axiom.toml
├── compiler/
├── libraries/
│   ├── core/
│   └── std/
└── tools/
    ├── fmt/
    └── test/
```

Workspace root quản lý nhiều package.

---

# 30. Workspace dependency

Package trong workspace có thể tham chiếu nhau bằng identity:

```text
axiom-core
axiom-std
axiomc
```

không cần publish registry trước.

---

# 31. Build Graph khác Dependency Graph

Đây là điểm quan trọng.

Dependency graph:

```text
A depends on B
```

Build graph:

```text
source
 ↓
parse
 ↓
HIR
 ↓
MIR
 ↓
codegen
 ↓
object
 ↓
link
```

Một package dependency có thể tạo rất nhiều build nodes.

---

# 32. Build graph

Conceptually:

```text
Source
   ↓
Parse
   ↓
Resolve
   ↓
Type
   ↓
Trait
   ↓
HIR
   ↓
MIR
   ↓
Verify
   ↓
Optimize
   ↓
ABI
   ↓
Machine
   ↓
Object
   ↓
Link
   ↓
Artifact
```

---

# 33. Query engine chính là build engine lõi

Đây là chỗ BOOTSTRAP-054 và 060 kết nối với 062.

Không nên tạo một build engine hoàn toàn khác compiler query engine.

Dùng:

```text
CompilerDB
```

để query semantic artifacts.

---

# 34. Incremental compilation

Nếu sửa:

```text
private fn foo()
```

không nên rebuild mọi dependent package.

Nếu sửa:

```text
pub struct Vec3
```

có thể invalidate:

```text
layout
ABI
codegen
dependent interfaces
```

---

# 35. Interface metadata

Mỗi package có:

```text
.axmeta
```

chứa semantic interface.

Không phải source dump.

---

# 36. `.axmeta`

Nên chứa:

```text
public declarations
types
traits
generic signatures
ABI contracts
repr contracts
comptime dependencies
semantic fingerprints
```

Không cần chứa implementation private nếu không cần.

---

# 37. AI cũng dùng `.axmeta`

IDE/agent có thể hỏi:

```text
What public functions does package X expose?
```

compiler metadata trả lời trực tiếp.

Không cần load toàn bộ source.

---

# 38. Semantic fingerprint

Fingerprint của package:

```text
Public API
+ public types
+ traits
+ repr
+ ABI
+ comptime dependencies
+ compiler semantic version
```

---

# 39. Private implementation

Thay đổi:

```text
private implementation
```

chỉ invalidate artifact nội bộ nếu public semantic fingerprint không đổi.

---

# 40. Generic functions

Đây là vấn đề đặc biệt.

Package A:

```axiom
pub fn sort<T: Ord>(...)
```

Package B:

```axiom
sort<MyType>(...)
```

Compiler phải có đủ generic semantic metadata để specialize.

---

# 41. Generic cache

Có thể cache:

```text
GenericInstanceId
```

theo:

```text
generic definition
+
type arguments
+
const arguments
+
target
+
optimization configuration
```

---

# 42. Monomorphization across package

Không được buộc package A phải precompile mọi generic type.

Thay vào đó:

```text
generic definition metadata
       ↓
consumer specialization
       ↓
codegen
```

---

# 43. Duplicate generic code

Nếu:

```text
A → Vec<i32>
B → Vec<i32>
```

linker có thể deduplicate bằng COMDAT/linkonce nếu semantic/ABI/target contracts tương đương.

Đã freeze ở ALINK.

---

# 44. Feature flags

Ví dụ:

```toml
[features]
gpu = []
unicode = []
```

Feature là compile-time configuration.

Không phải runtime boolean.

---

# 45. `@cfg`

Ví dụ:

```axiom
@cfg(target = "windows")
fn platform_impl() { ... }
```

Code không phù hợp target bị loại trước type/codegen ở phase thích hợp.

---

# 46. `comptime` vs `@cfg`

Phân biệt rất rõ:

```text
@cfg
```

→ **select code**

```text
comptime
```

→ **compute/generate value/declaration**

---

# 47. Target triple

Build configuration phải phân biệt:

```text
host
target
```

Ví dụ:

```text
host   = x86_64-windows
target = aarch64-linux
```

Compiler chạy trên Windows nhưng tạo Linux ARM executable.

---

# 48. Comptime host/target

Đây là vấn đề dễ gây bug.

Nếu comptime chạy trên host:

```text
comptime
```

không được giả định rằng:

```text
usize
endianness
pointer size
OS APIs
```

giống target.

Compiler phải xác định execution context.

---

# 49. Build profiles

Ban đầu:

```text
debug
release
```

Có thể:

```text
profile.release
    optimization = aggressive
    debug_info = false
```

Nhưng profile không được thay đổi language semantics.

---

# 50. Debug/release invariant

```text
debug semantics == release semantics
```

Chỉ khác:

```text
optimization
debug info
assert policy nếu explicitly configured
```

Nếu một option thực sự thay đổi semantics thì phải là explicit semantic configuration, không phải “optimization”.

---

# 51. Build target

Ví dụ:

```text
axiom build
axiom build --target=x86_64-linux
axiom build --target=aarch64-linux
axiom build --target=wasm32
```

---

# 52. Artifact types

Build graph phải phân biệt:

```text
executable
static-library
shared-library
object
wasm
gpu-binary
metadata
```

---

# 53. Static library

```text
libfoo.a
```

hoặc tương đương target.

Không cần C compiler để tạo.

---

# 54. Shared library

```text
foo.dll
libfoo.so
libfoo.dylib
```

được tạo bởi Axiom ObjectWriter + Linker.

---

# 55. Foreign libraries

Ví dụ:

```text
libssl
```

là external artifact.

Manifest có thể khai báo system dependency.

Compiler không giả định nó được build bằng Axiom.

---

# 56. Native library search

Không nên để compiler tự:

```text
scan random filesystem
```

Một dependency system nên explicit:

```toml
[system-dependencies]
openssl = "3"
```

hoặc platform configuration.

---

# 57. Reproducible build

Build identity gồm:

```text
source
dependencies
compiler semantic version
target
features
comptime inputs
build configuration
```

---

# 58. Không dùng timestamp làm semantic identity

Timestamp chỉ có thể nằm trong metadata không ảnh hưởng binary identity nếu muốn reproducibility.

---

# 59. Randomness

Comptime random:

```text
random
```

phải được coi là external input.

Reproducible build cần:

```text
explicit seed
```

hoặc cấm capability này.

---

# 60. Generated files

Comptime có thể generate:

```text
declarations
resources
metadata
```

nhưng compiler quản lý dependency.

Không để:

```text
comptime
→ random file modification
→ compiler không biết
```

---

# 61. Build capabilities

Build/comptime filesystem access:

```text
ReadSource
ReadMetadata
ReadFilesystem
WriteGenerated
ExecuteTool
Environment
Network
Time
Random
```

theo capability model đã freeze.

---

# 62. Default sandbox

Mặc định:

```text
ReadSource
ReadMetadata
```

Các capability mạnh hơn phải explicit.

---

# 63. Build script không được tự do

Không cho:

```text
build script
→ shell
→ delete arbitrary files
→ network
→ modify compiler
```

trừ khi capability được cấp.

---

# 64. Package manager và compiler tách quyền

Kiến trúc:

```text
Package Manager
    │
    ├── network
    ├── registry
    ├── cache
    └── source acquisition
          │
          ▼
      Compiler
          │
          ├── parse
          ├── type
          ├── verify
          └── codegen
```

---

# 65. Cache architecture

Có nhiều cache:

```text
Source Cache
Dependency Cache
Parse Cache
Semantic Cache
Generic Cache
Comptime Cache
Codegen Cache
Object Cache
Link Cache
```

Không gom thành một cache mơ hồ.

---

# 66. Cache identity

Ví dụ codegen cache:

```text
Verified MIR
+ target
+ ABI
+ representation
+ compiler backend version
+ optimization configuration
```

---

# 67. Cache không được thay đổi semantics

Cache hit và build lại từ source phải cho:

```text
same semantic result
```

---

# 68. Parallel build

Nếu:

```text
A → C
B → C
```

A và B có thể build song song.

---

# 69. Parallel semantics

Bất kể:

```text
serial
```

hay:

```text
parallel
```

kết quả semantic phải giống nhau.

---

# 70. Cancellation

Nếu user sửa source trong lúc compiler đang build:

```text
revision N
```

có thể bị cancel khi:

```text
revision N+1
```

xuất hiện.

Query engine phải bỏ kết quả stale.

---

# 71. Package graph revision

Package graph cũng có revision.

Thay đổi:

```text
axiom.toml
```

có thể invalidate dependency resolution nhưng không nhất thiết invalidate parser của mọi source.

---

# 72. Lockfile stability

Nếu `axiom.lock` không thay đổi:

```text
dependency graph identity
```

ổn định.

---

# 73. Security

Package source cần integrity:

```text
package
version
hash
source
```

Có thể sau này thêm signing.

Signing là packaging/security layer, không phải language semantics.

---

# 74. Vendoring

Cho phép:

```text
vendor/
```

để build offline/reproducible.

Package manager vẫn giữ semantic identity.

---

# 75. Native SDK

Platform SDK:

```text
Windows SDK
Apple SDK
Android NDK/SDK
Linux system interfaces
```

là external system resources.

Không phải compiler semantic dependency.

---

# 76. iOS/Android

Build graph phải hỗ trợ nhiều artifact stages:

```text
Axiom source
 ↓
object
 ↓
native library/executable
 ↓
platform packaging
 ↓
signing
 ↓
IPA/APK/AAB
```

Compiler/linker chỉ chịu trách nhiệm phần native artifact.

Signing/package nằm platform tooling.

---

# 77. WASM

WASM cũng là native target của Axiom:

```text
Axiom
 ↓
WASM Machine IR
 ↓
WASM object/module
```

Không giả lập WASM bằng JavaScript runtime.

---

# 78. GPU artifacts

Một package có thể tạo:

```text
CPU object
+
GPU binary
```

Build graph:

```text
source
 ├── CPU target
 └── GPU target
```

nhưng semantic source vẫn là Axiom.

---

# 79. Multi-target package

Ví dụ:

```text
graphics
├── CPU implementation
├── Vulkan GPU
├── Metal GPU
└── DirectX GPU
```

`@cfg`/target selection quyết định implementation.

---

# 80. Package không được biết quá nhiều về compiler internals

Package chỉ nên phụ thuộc:

```text
language semantics
library contracts
target APIs
```

không phụ thuộc trực tiếp:

```text
MIR opcode #123
```

---

# 81. Compiler plugin

Tôi đề xuất **không cho compiler plugin native tùy ý trong Core v1**.

Không:

```text
compiler plugin
→ inject arbitrary MIR
```

Điều này phá deterministic semantics.

---

# 82. Typed code generation

Thay vào đó:

```text
comptime
@derive
generated declarations
```

được re-enter vào pipeline bình thường:

```text
generated HIR
 ↓
resolve
 ↓
type
 ↓
ownership
 ↓
verify
```

---

# 83. Dependency graph + AI agent

Đây là điểm rất phù hợp với mục tiêu Axiom.

Agent có thể query:

```text
package graph
module graph
public API
trait requirements
ABI
build dependencies
target support
```

thay vì đọc hàng nghìn source file.

---

# 84. CLI

Tôi đề xuất CLI nền tảng:

```text
axiom init
axiom new
axiom add
axiom remove
axiom update
axiom fetch
axiom check
axiom build
axiom run
axiom test
axiom bench
axiom clean
axiom doc
axiom fmt
```

---

# 85. Inspect commands

Rất quan trọng cho compiler/AI:

```text
axiom inspect package
axiom inspect module
axiom inspect type
axiom inspect trait
axiom inspect mir
axiom inspect abi
axiom inspect deps
axiom inspect artifact
```

---

# 86. Machine-readable mode

Mọi command quan trọng có:

```text
--format=json
```

Ví dụ:

```text
axiom check --format=json
```

---

# 87. Dependency explanation

```text
axiom explain deps
```

có thể trả:

```text
app
 ├─ foo@1.2
 │   └─ bar@3
 └─ baz@2
     └─ bar@4
```

---

# 88. Why rebuilt?

Đây là feature rất đáng có:

```text
axiom explain rebuild
```

Ví dụ:

```text
Rebuilt foo because:
  public type Vec changed
  → layout changed
  → ABI changed
  → dependent artifact invalidated
```

Điều này cực hữu ích cho cả developer lẫn AI agent.

---

# 89. Build graph visualization

Compiler có thể emit:

```text
--emit=build-graph
```

và tạo:

```text
build-graph.json
```

IDE/AI có thể visualize.

---

# 90. Artifact provenance

Artifact nên biết:

```text
source revision
package version
compiler version
target
features
dependency hashes
```

để debug/reproducibility.

---

# 91. Self-host bootstrap

Đây là nơi tất cả kết nối.

Ban đầu:

```text
external compiler
      ↓
axiomc stage1
```

Sau đó:

```text
axiomc stage1
      ↓
compile axiomc.ax
      ↓
axiomc stage2
```

---

# 92. Core bootstrap dependency

Phải tránh:

```text
axiomc
 ↓
std
 ↓
axiomc
```

Compiler bootstrap nên có dependency tối thiểu:

```text
axiomc
 └── axiom.core
```

và một bootstrap subset nếu cần.

---

# 93. `axiom.core` bootstrap profile

Có thể định nghĩa:

```text
axiom.core
```

là package đặc biệt nhưng **không phải compiler magic API khổng lồ**.

Nó chỉ phụ thuộc những semantics compiler đã biết.

---

# 94. `axiom.std` nằm trên Core

```text
axiomc
  ↓
axiom.core
  ↓
axiom.std
```

Compiler không phụ thuộc ngược vào std.

---

# 95. Compiler tooling

Sau khi compiler tự host:

```text
axiomc
axiom
axiom-fmt
axiom-test
axiom-doc
```

có thể là các Axiom executables riêng.

---

# 96. Package manager bootstrap

Package manager ban đầu có thể được viết bằng host language.

Sau đó:

```text
axiom package manager
```

được self-host.

---

# 97. Compiler và package manager không phải một binary bắt buộc

Có thể:

```text
axiomc
axiom-pkg
```

riêng.

CLI `axiom` chỉ là frontend orchestration.

---

# 98. Kiến trúc cuối

```text
                   axiom CLI
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
  Package Manager                 axiomc
        │                             │
        │                         CompilerDB
        │                             │
        ▼                             ▼
 Dependency Graph              Semantic Graph
        │                             │
        └──────────────┬──────────────┘
                       ▼
                  Build Graph
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
        Object       Library      Metadata
          │            │
          └────────────┴─────┐
                              ▼
                           Linker
                              │
                              ▼
                           Artifact
```

---

# 99. Quy tắc cực quan trọng

Axiom build system phải đảm bảo:

> **Dependency management, compilation, linking và packaging là bốn vấn đề khác nhau.**

Không tạo một “siêu build system” làm tất cả.

---

# 100. Frozen invariants — BOOTSTRAP-062

```text
ABUILD-101  Module identity is semantic, not filesystem-address identity.
ABUILD-102  Package identity is name + version + source identity.
ABUILD-103  Workspace groups packages without changing package identity.
ABUILD-104  Artifact identity is distinct from package identity.
ABUILD-105  Module dependency is distinct from package dependency.
ABUILD-106  Package dependency graphs are acyclic by default.
ABUILD-107  Module cycles are a separate resolver concern.
ABUILD-108  Import is compile-time name/dependency resolution.
ABUILD-109  Import does not imply runtime execution.
ABUILD-110  Visibility is distinct from native symbol export.
ABUILD-111  pub does not imply @export.
ABUILD-112  @export establishes an external symbol contract.
ABUILD-113  Package resolution is deterministic.
ABUILD-114  Resolved dependencies can be recorded in axiom.lock.
ABUILD-115  Lock identity includes source integrity information.
ABUILD-116  Different package versions have distinct nominal identities.
ABUILD-117  Incompatible package types cannot silently interoperate.
ABUILD-118  Dependency phases are distinct.
ABUILD-119  Build dependencies do not automatically become runtime dependencies.
ABUILD-120  Test dependencies do not automatically enter release artifacts.
ABUILD-121  Comptime dependencies participate in dependency identity.
ABUILD-122  Feature configuration is compile-time configuration.
ABUILD-123  @cfg selects configuration-specific code.
ABUILD-124  comptime computes or generates compile-time artifacts.
ABUILD-125  Host and target environments are distinct.
ABUILD-126  Cross-compilation is first-class.
ABUILD-127  Comptime host/target semantics are explicit.
ABUILD-128  Build profiles do not silently change language semantics.
ABUILD-129  Debug and release preserve language semantics.
ABUILD-130  Build graph is distinct from dependency graph.
ABUILD-131  Compiler queries participate in build graph construction.
ABUILD-132  Incremental compilation uses semantic fingerprints.
ABUILD-133  Timestamps are not semantic identities.
ABUILD-134  Public API changes may invalidate dependent interfaces.
ABUILD-135  Private implementation changes need not invalidate dependent semantics.
ABUILD-136  Generic definitions can be specialized in dependent packages.
ABUILD-137  Generic specializations are independently cacheable.
ABUILD-138  Equivalent generic artifacts may be deduplicated.
ABUILD-139  Cache identity includes relevant semantic and target configuration.
ABUILD-140  Cache hits must preserve build semantics.
ABUILD-141  Parallel build must have serial-equivalent semantics.
ABUILD-142  Stale revisions may be cancelled.
ABUILD-143  Dependency resolution is separate from source compilation.
ABUILD-144  Package acquisition is separate from compiler semantics.
ABUILD-145  The compiler does not implicitly fetch network dependencies.
ABUILD-146  Offline builds are supported when dependencies are available locally.
ABUILD-147  Build/comptime external effects are capability-gated.
ABUILD-148  Build scripts are not an unrestricted second programming language.
ABUILD-149  Generated declarations re-enter normal semantic verification.
ABUILD-150  Generated code cannot bypass ownership/capability verification.
ABUILD-151  Compiler plugins cannot arbitrarily mutate semantic IR in Core v1.
ABUILD-152  Native system dependencies are explicit.
ABUILD-153  Platform SDKs are external system resources.
ABUILD-154  Platform packaging is distinct from native compilation/linking.
ABUILD-155  Signing is distinct from compilation semantics.
ABUILD-156  Static libraries are first-class artifacts.
ABUILD-157  Shared libraries are first-class artifacts.
ABUILD-158  Object files are first-class artifacts.
ABUILD-159  WASM artifacts are first-class target artifacts.
ABUILD-160  GPU binaries are target-specific artifacts.
ABUILD-161  Multi-target packages may produce multiple target artifacts.
ABUILD-162  Target-specific implementation selection is compile-time.
ABUILD-163  Artifact provenance is inspectable.
ABUILD-164  Machine-readable build metadata is supported.
ABUILD-165  Build diagnostics are structured and stable.
ABUILD-166  Build explanations can identify invalidation causes.
ABUILD-167  Package metadata is sufficient for semantic dependency analysis.
ABUILD-168  .axmeta is semantic interface metadata, not a source replacement.
ABUILD-169  Private implementation details need not enter public interface metadata.
ABUILD-170  AI tooling may query build/semantic metadata.
ABUILD-171  AI tooling cannot alter semantic verification results.
ABUILD-172  Standard Library does not depend on compiler internals as source semantics.
ABUILD-173  Compiler does not depend on Standard Library implementation.
ABUILD-174  Core Library precedes Standard Library in dependency layering.
ABUILD-175  System libraries depend downward on explicit FFI/system contracts.
ABUILD-176  Dependency layering must not introduce mandatory runtime components.
ABUILD-177  Runtime components remain independently linkable.
ABUILD-178  Unused runtime components remain removable.
ABUILD-179  Bootstrap dependencies have an explicit removal path.
ABUILD-180  Stage-0 external tools are bootstrap vehicles, not final language dependencies.
ABUILD-181  Axiom compiler can ultimately compile itself.
ABUILD-182  Axiom package/build tooling can ultimately be self-hosted.
ABUILD-183  Self-hosting does not alter language semantics.
ABUILD-184  Package manager and compiler may remain separate executables.
ABUILD-185  axiom CLI may orchestrate package/build/compiler operations.
ABUILD-186  Dependency management, compilation, linking and packaging remain distinct layers.
ABUILD-187  Build graph determinism is required.
ABUILD-188  Reproducible configuration excludes uncontrolled semantic inputs.
ABUILD-189  External comptime inputs participate in cache identity.
ABUILD-190  Build architecture must support native targets without mandatory third-party compilers.
```

---

## Một điểm tôi muốn chốt thêm

Đến đây Axiom đã có một chuỗi khá hoàn chỉnh:

```text
061  Core/Std/System Library
 ↓
062  Module/Package/Build
 ↓
043  IR
 ↓
055  Verification
 ↓
056  Optimization
 ↓
057  ABI
 ↓
058  Machine Backend
 ↓
059  Object/Linker
 ↓
060  Self-hosting
```

Tức là **phần compiler pipeline và build architecture cơ bản đã nối kín**.

### Bước tiếp theo tôi đề xuất là BOOTSTRAP-063 — **Testing, Conformance, Language Specification & Formal Semantic Validation**

Đây là mốc cần thiết trước khi tiếp tục thêm tính năng: xây **test oracle của Axiom** để đảm bảo compiler tự viết sau này không âm thầm thay đổi semantics. Nó sẽ bao gồm conformance suite, ownership/capability tests, MIR verifier tests, differential testing, fuzzing, compile-fail tests, ABI golden tests, machine-code tests, bootstrap comparison và đặc biệt là cách định nghĩa **“Axiom program này phải có hành vi gì”** mà không cần formal theorem prover quá nặng.