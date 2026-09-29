# BOOTSTRAP-308 — AXIOM PACKAGE, MODULE & DEPENDENCY SYSTEM

## 1. Mục tiêu

Thiết kế hệ thống **Package / Module / Import / Dependency** hoàn chỉnh cho Axiom.

Mục tiêu không chỉ là `import` file, mà phải giải quyết đồng thời:

- namespace;
- module;
- package;
- visibility;
- API public/private;
- dependency graph;
- versioning;
- reproducible build;
- workspace;
- package cache;
- cross-compilation;
- conditional compilation;
- FFI package;
- comptime dependency;
- incremental compilation;
- circular dependency;
- package security;
- binary/source dependency;
- AI-friendly project structure.

Nguyên tắc:

> **Module tổ chức code. Package tổ chức phân phối. Build Graph tổ chức dependency. Compiler quản lý semantic identity.**

---

# 2. Phân biệt Module và Package

Axiom phải phân biệt rõ:

```text
Module
    = đơn vị namespace + compilation semantics

Package
    = đơn vị phân phối + version + dependency + build metadata
```

Ví dụ:

```text
myapp/
├── package.axm
├── src/
│   ├── main.axm
│   ├── math.axm
│   └── ui/
│       ├── mod.axm
│       └── widget.axm
```

Có thể hiểu:

```text
Package: myapp

Modules:
    myapp
    myapp.math
    myapp.ui
    myapp.ui.widget
```

---

# 3. Package Identity

Package không được định danh chỉ bằng tên.

Identity:

```text
PackageIdentity {
    registry/source
    namespace
    name
    version
}
```

Ví dụ:

```text
registry.example
    /graphics
    /image
    /2.4.1
```

Source identity và package version phải tách biệt.

---

# 4. Semantic Package Identity

Compiler cần một ID nội bộ:

```text
PackageId
```

không dùng string package name làm identity chính.

Ví dụ:

```text
PackageId(42)
```

tham chiếu tới:

```text
PackageRecord
```

Điều này phù hợp với `CompilerDB` đã frozen.

---

# 5. Package Manifest

File:

```text
package.axm
```

chứa:

```text
package {
    name = "myapp"
    version = "1.0.0"

    edition = "1"

    targets = [
        "windows-x64",
        "linux-x64"
    ]

    dependencies = [
        ...
    ]
}
```

Manifest phải declarative.

Không cho manifest trở thành một scripting language tùy ý.

---

# 6. Dependency Declaration

Ví dụ:

```text
dependencies {
    math = "2.4"
    image = "1.7"
}
```

Có thể hỗ trợ:

```text
path dependency
git/source dependency
registry dependency
local workspace dependency
binary dependency
system dependency
```

Nhưng semantic dependency vẫn phải được chuẩn hóa thành một `DependencySpec`.

---

# 7. DependencySpec

Định nghĩa:

```text
DependencySpec {
    package_identity
    version_requirement
    source
    features
    target_condition
    optional
    default_features
}
```

Ví dụ:

```text
image {
    version = "^2.1"
    optional = true
}
```

---

# 8. Version Resolution

Axiom cần dependency resolver deterministic.

Input:

```text
A
 ├── B ^1.2
 └── C ^2.0

C
 └── B ^1.4
```

Resolver tìm version thỏa tất cả constraint.

Nếu không có:

```text
error: incompatible dependency requirements
```

Không chọn version ngẫu nhiên.

---

# 9. Lockfile

Project application nên có:

```text
axiom.lock
```

chứa resolved dependency graph:

```text
package
version
source
checksum
dependencies
features
```

Build từ lockfile phải reproducible.

---

# 10. Dependency Fingerprint

Dependency fingerprint phải tham gia build identity.

Ví dụ:

```text
ArtifactKey =
    compiler_semantic_version
    target
    profile
    source_hash
    public_api_hash
    dependency_fingerprint
    comptime_inputs
    feature_set
```

Nếu dependency ABI/API thay đổi:

```text
dependent package
```

được invalidate chính xác.

---

# 11. Semantic vs Textual Dependency

Không phải mọi thay đổi dependency source đều cần rebuild toàn bộ project.

Ví dụ:

```text
library implementation changed
```

nhưng:

```text
public API
types
traits
ABI
comptime outputs
```

không thay đổi.

Dependent code có thể không cần compile lại.

Đây là yêu cầu quan trọng cho incremental compilation.

---

# 12. Public API Fingerprint

Mỗi package/module cần:

```text
PublicFingerprint
```

bao gồm:

```text
public declarations
public types
public traits
public generic constraints
public constants
public repr/ABI
public comptime outputs
public exported symbols
```

Không bao gồm implementation details không quan sát được.

---

# 13. Module Declaration

Axiom nên có syntax rõ ràng:

```text
module myapp.math
```

hoặc module được suy ra từ filesystem.

Khuyến nghị:

> **Filesystem structure là mặc định, explicit module declaration dùng để xác nhận identity.**

Không bắt programmer lặp lại tên file ở mọi nơi nếu compiler đã biết.

---

# 14. Import

Ví dụ:

```text
import std.collections.HashMap
import myapp.math
```

Không dùng import để execute code.

Import chỉ tạo semantic dependency.

---

# 15. Selective Import

```text
import std.collections {
    HashMap
    HashSet
}
```

hoặc:

```text
use std.collections.HashMap
```

Axiom cần chọn một syntax duy nhất trong Core.

Không nên có nhiều cách biểu diễn cùng một semantic operation nếu không có lợi ích rõ ràng.

---

# 16. Alias

```text
import graphics.Image as Img
```

Alias chỉ thay đổi local name.

Không thay đổi:

```text
TypeId
DeclarationId
PackageId
```

---

# 17. Re-export

Module có thể:

```text
export Image
export graphics.Image
```

để tạo public facade.

Ví dụ:

```text
myapp/
    public_api.axm
```

có thể re-export:

```text
Image
Texture
Renderer
```

mà không expose toàn bộ internal modules.

---

# 18. Visibility

Axiom nên có các mức tối thiểu:

```text
private
module
package
public
```

Semantic:

```text
private
    current declaration/module

module
    current module hierarchy

package
    same package

public
    external packages
```

Không nên tạo quá nhiều visibility modifiers.

---

# 19. Public ≠ Exported Binary Symbol

Một function:

```text
public fn calculate(...)
```

không đồng nghĩa:

```text
binary symbol exported
```

Muốn ABI-level export:

```text
@export
fn plugin_entry(...)
```

Điều này giữ abstraction và cho phép optimizer loại bỏ symbol không thực sự cần.

---

# 20. Module Privacy

Compiler phải kiểm tra visibility trước monomorphization/codegen.

Không để:

```text
private type
```

vô tình xuất hiện trong public API.

Ví dụ:

```text
private struct Internal

public fn create() -> Internal
```

→ compile error.

---

# 21. Package API Boundary

Package public API là boundary quan trọng cho incremental compilation.

Compiler phải tạo:

```text
PackageInterface
```

chứa:

```text
public declarations
types
traits
constants
generic constraints
ABI metadata
comptime metadata
capability/effect contracts
```

Implementation không cần expose toàn bộ MIR.

---

# 22. Generic Dependency

Package có:

```text
public fn sort<T: Comparable>(...)
```

thì dependent package phải biết:

```text
Comparable
generic signature
constraints
ABI-relevant properties
```

nhưng không nhất thiết nhận toàn bộ implementation.

Monomorphization xảy ra khi cần.

---

# 23. Generic Code Distribution

Có ba mô hình:

```text
source distribution
IR/interface distribution
precompiled generic instances
```

Axiom nên hỗ trợ cả ba.

Mục tiêu cuối:

```text
Package Interface
+
Generic IR/metadata
+
Compiled native objects
```

để tối ưu build time.

---

# 24. Binary Package

Một package có thể cung cấp:

```text
Axiom API
+
precompiled native implementation
```

Ví dụ:

```text
graphics.axpkg
```

chứa:

```text
interface
target objects
debug metadata
ABI metadata
```

Compiler không cần source implementation nếu ABI contract đủ.

---

# 25. Cross Compilation

Dependency resolution phải target-aware.

Ví dụ:

```text
app
 └── graphics
```

graphics có:

```text
windows provider
linux provider
macos provider
```

Build:

```text
--target linux-x64
```

chỉ resolve provider phù hợp.

---

# 26. Conditional Compilation

Axiom đã có `@cfg`.

Package system phải hỗ trợ:

```text
@cfg(target_os = "windows")
```

và:

```text
@cfg(target_arch = "x86_64")
```

Nhưng `@cfg` phải được xử lý trước những phase không phù hợp với target.

Không parse/resolve một declaration không thuộc target rồi mới loại bỏ quá muộn nếu điều đó gây lỗi giả.

---

# 27. Features

Package có thể định nghĩa:

```text
features {
    png
    jpeg
    gpu
    async
}
```

Dependency:

```text
image {
    features = ["png"]
}
```

Feature phải là compile-time configuration.

Không biến feature thành runtime flag trừ khi library chủ động làm vậy.

---

# 28. Feature Unification

Nếu:

```text
A → image(features = png)
B → image(features = jpeg)
```

thì resolver phải có quy tắc deterministic:

```text
image = png + jpeg
```

nếu feature additive.

Nhưng feature không mặc định additive nếu semantics cho phép conflict.

Ví dụ:

```text
allocator_system
allocator_custom
```

có thể xung đột.

---

# 29. Optional Dependency

```text
dependencies {
    cuda = optional
}
```

Nếu không bật feature:

```text
cuda
```

không xuất hiện trong dependency graph thực tế.

Không compile.

Không link.

---

# 30. Circular Package Dependency

Không cho package dependency cycle:

```text
A → B
B → C
C → A
```

Build graph phải reject.

Tuy nhiên module nội bộ có thể có semantic relationships không tạo compilation cycle nếu compiler có interface phase.

Ví dụ:

```text
module A
    references public declaration from B

module B
    references public declaration from A
```

Nếu cần hỗ trợ mutual recursion, phải xử lý ở **declaration/interface phase**, không tạo package dependency cycle.

---

# 31. Workspace

Một workspace:

```text
workspace/
├── workspace.axm
├── compiler/
├── std/
├── tools/
└── tests/
```

có nhiều package:

```text
axiom.compiler
axiom.std
axiom.tools
axiom.tests
```

Workspace dependency được resolve local trước registry.

---

# 32. Monorepo

Workspace phải hỗ trợ monorepo lớn.

Compiler không được compile lại tất cả package chỉ vì một package thay đổi.

Graph:

```text
Package A
   ↓
Package B
   ↓
Package C
```

Nếu implementation A thay đổi nhưng public interface không:

```text
B/C
```

có thể giữ artifact.

---

# 33. Build Profiles

Package có thể có:

```text
dev
release
test
bench
debug
size
```

Nhưng profile không được thay đổi language semantics.

Ví dụ:

```text
release
```

có thể:

```text
LTO
PGO
vectorization
dead stripping
```

nhưng không được làm:

```text
ownership valid → invalid
```

hay thay đổi observable overflow semantics.

---

# 34. Dependency Capabilities

Dependency có thể yêu cầu:

```text
network
filesystem
process
compiler tool
GPU
```

Đặc biệt quan trọng với `comptime`.

Ví dụ package:

```text
schema_generator
```

có:

```text
comptime:
    ReadSource
    WriteGenerated
```

Build system phải biết điều này.

---

# 35. Comptime Dependency Tracking

Nếu comptime đọc:

```text
schema.json
```

thì file này phải trở thành dependency.

Graph:

```text
source
  ↓
comptime
  ↓
schema.json
  ↓
generated declaration
```

Schema thay đổi:

```text
generated declaration
↓
package interface
↓
dependent packages
```

được invalidate chính xác.

---

# 36. Generated Code

Generated code phải có identity:

```text
GeneratedSourceId
```

và source provenance:

```text
generated from:
    declaration
    comptime invocation
    input files
```

Code generated vẫn phải đi qua:

```text
resolution
type checking
ownership
capability
effect
ABI
verification
```

Không có generated-code bypass.

---

# 37. Dependency Security

Package registry cần checksum:

```text
sha256
```

hoặc hash hiện đại tương đương.

Lockfile phải pin:

```text
version
source
checksum
```

Build system phát hiện package content thay đổi ngoài lockfile.

---

# 38. Offline Build

Axiom phải hỗ trợ:

```text
axiom build --offline
```

nếu dependency đã có trong local cache.

Không được tự động network access trong compiler/build.

Network capability phải explicit.

---

# 39. Package Cache

Cache layout semantic:

```text
cache/
    registry/
    source/
    interface/
    object/
    generic/
    comptime/
    final/
```

Artifact key dùng fingerprint.

Cache không được dựa đơn giản trên:

```text
filename + timestamp
```

---

# 40. Package Manager

Không để package manager nằm trong compiler frontend.

Có thể có:

```text
axiom
    build
    add
    remove
    update
    fetch
    test
    publish
    run
```

nhưng architecture tách:

```text
CLI
 ↓
Package Resolver
 ↓
Build Graph
 ↓
Compiler
```

---

# 41. Registry

Registry API tối thiểu:

```text
publish
download
metadata
versions
dependencies
checksums
```

Registry không phải một phần của language semantics.

Axiom vẫn phải build được từ:

```text
local packages
filesystem
git
vendor directory
```

---

# 42. Vendoring

Hỗ trợ:

```text
vendor/
```

để project có thể đóng gói toàn bộ dependency.

Điều này hữu ích cho:

- offline build;
- reproducibility;
- embedded;
- enterprise;
- compiler bootstrap;
- security auditing.

---

# 43. Dependency Override

Workspace/dev build có thể:

```text
override image → ../local/image
```

nhưng phải tạo dependency identity rõ ràng.

Không được khiến artifact cache nhầm:

```text
registry/image
```

với:

```text
local/image
```

---

# 44. Package ABI Compatibility

Nếu binary package:

```text
image 2.1
```

được build trước, dependent package phải kiểm tra:

```text
target
ABI
calling convention
repr
compiler compatibility
feature set
runtime ABI
```

Không chỉ kiểm tra version string.

---

# 45. Package Interface File

Đề xuất artifact:

```text
foo.axif
```

Axiom Interface.

Nó chứa:

```text
package identity
public API
type metadata
trait metadata
generic metadata
ABI metadata
effect contracts
comptime metadata
target constraints
dependency fingerprints
compiler compatibility
```

Không nhất thiết chứa implementation.

---

# 46. AI-Friendly Package Interface

Đây là điểm Axiom nên làm tốt hơn các compiler truyền thống.

`foo.axif` có thể được compiler expose dưới dạng structured JSON:

```text
{
    "package": "...",
    "types": [...],
    "functions": [...],
    "traits": [...],
    "effects": [...],
    "abi": [...],
    "examples": [...],
    "diagnostics": [...]
}
```

AI agent có thể hỏi compiler:

```text
what can I call?
what type does this function expect?
what ownership does it consume?
can this cross threads?
does it allocate?
can it block?
```

Không cần đọc toàn bộ source.

---

# 47. Compiler Query API

Package/module system phải tích hợp `CompilerDB`.

Các query:

```text
resolve_package(PackageId)
resolve_module(ModuleId)
public_interface(PackageId)
dependency_graph(PackageId)
type_of(DeclarationId)
visibility_of(DeclarationId)
abi_of(DeclarationId)
effects_of(FunctionId)
```

Các query này phải incremental và memoized.

---

# 48. Diagnostics

Ví dụ:

```text
error[PKG021]:
package `image` requires feature `png`

dependency chain:

myapp
  └── renderer
       └── image
```

Hoặc:

```text
error[MOD014]:
`InternalTexture` is private to package `renderer`
but appears in public API of `renderer::Renderer`.
```

Compiler phải hiển thị dependency chain.

---

# 49. Import Cycle Diagnostics

Nếu module cycle hợp lệ ở declaration phase nhưng illegal ở initialization/comptime phase, diagnostic phải phân biệt:

```text
declaration cycle
initialization cycle
comptime dependency cycle
runtime dependency cycle
package dependency cycle
```

Không gộp thành một lỗi chung.

---

# 50. Definition of Done

BOOTSTRAP-308 hoàn thành khi:

- Package/Module có identity riêng.
- Dependency graph deterministic.
- Version resolver deterministic.
- Lockfile reproducible.
- Incremental compilation dựa semantic fingerprint.
- Public interface có artifact riêng.
- Binary package được hỗ trợ.
- Generic package metadata được hỗ trợ.
- Cross compilation target-aware.
- Feature/optional dependency rõ ràng.
- Comptime inputs tham gia dependency graph.
- Generated code có provenance.
- Workspace/monorepo được hỗ trợ.
- Offline/vendored build hoạt động.
- Registry chỉ là distribution mechanism.
- Package manager tách khỏi compiler semantic core.
- AI có thể query package interface có cấu trúc.
- Package dependency không phá vỡ runtime-free/freestanding model.

---

## Invariants

```text
APKG-20
Package identity is distinct from module identity.

APKG-21
Module identity is distinct from filesystem path.

APKG-22
Dependency resolution is deterministic.

APKG-23
Resolved dependency graphs are acyclic at package level.

APKG-24
Lockfiles produce reproducible dependency resolution.

APKG-25
Dependency source identity participates in artifact identity.

APKG-26
Public API changes invalidate dependent interfaces when semantically required.

APKG-27
Private implementation changes do not require dependent recompilation when the public semantic fingerprint is unchanged.

APKG-28
Public APIs cannot expose inaccessible private types.

APKG-29
Binary package interfaces explicitly describe ABI requirements.

APKG-30
Generic packages expose sufficient metadata for correct instantiation.

APKG-31
Comptime external inputs are tracked as dependencies.

APKG-32
Generated declarations re-enter ordinary compiler verification.

APKG-33
Target-specific dependencies are resolved according to target configuration.

APKG-34
Unused optional dependencies are absent from the effective graph.

APKG-35
Feature resolution is deterministic.

APKG-36
Package manager behavior does not define language semantics.

APKG-37
Registry availability is not required for local/offline builds.

APKG-38
Package cache identity is content/semantic based, not timestamp based.

APKG-39
Workspace builds preserve package boundaries.

APKG-40
Package interfaces are queryable through CompilerDB.

APKG-41
AI-facing package metadata cannot bypass compiler verification.

APKG-42
Module imports create semantic dependencies but do not execute initialization.

APKG-43
Runtime dependencies are represented independently from package dependencies.

APKG-44
FFI/system dependencies require explicit target and ABI contracts.

APKG-45
Package resolution must preserve reproducibility across machines given identical inputs.

APKG-46
A package may be implemented in Axiom without requiring C/C++ package infrastructure.

APKG-47
Source, interface, object, and final artifacts have distinct identities.

APKG-48
Dependency resolution occurs before code generation for the affected compilation units.

APKG-49
No package mechanism may implicitly introduce a mandatory global runtime.

APKG-50
Package/module architecture must remain compatible with eventual Axiom self-hosting.
```