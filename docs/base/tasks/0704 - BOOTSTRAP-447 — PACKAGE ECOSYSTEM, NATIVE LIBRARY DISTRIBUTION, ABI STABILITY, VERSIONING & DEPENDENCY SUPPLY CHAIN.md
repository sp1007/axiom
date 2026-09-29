# BOOTSTRAP-447 — PACKAGE ECOSYSTEM, NATIVE LIBRARY DISTRIBUTION, ABI STABILITY, VERSIONING & DEPENDENCY SUPPLY CHAIN

**Trạng thái: COMPLETED / LOCKED**

Task này khóa cách Axiom biến một package từ source code thành một đơn vị có thể:

- dùng như source dependency;
- dùng như binary dependency;
- phân phối static library;
- phân phối dynamic library;
- phân phối WASM;
- cross-compile;
- cache;
- verify;
- reproduce;
- được AI/tooling hiểu mà không cần đọc toàn bộ source.

Mục tiêu quan trọng:

```text
Axiom package
    ≠ chỉ là source archive

Axiom package
    =
source/API
+ semantic metadata
+ native artifacts
+ ABI metadata
+ dependency graph
+ provenance
+ reproducibility information
```

---

## 447.1 — Package identity

Mỗi package có identity ổn định:

```text
PackageId
```

bao gồm tối thiểu:

```text
namespace/name
version
source identity
```

---

## 447.2 — Package name

Tên package phải:

- ASCII-safe cho tooling;
- case-sensitive hoặc case-normalized theo một rule duy nhất;
- không collision với reserved package names.

---

## 447.3 — Package version

Version là metadata semantic, không phải một phần của source module name.

---

## 447.4 — Version scheme

Axiom mặc định dùng semantic-version-compatible model:

```text
MAJOR.MINOR.PATCH
```

nhưng compiler không được giả định mọi versioning policy của ecosystem đều tuân SemVer.

---

## 447.5 — API version

API compatibility được đánh giá độc lập với package version.

---

## 447.6 — ABI version

ABI compatibility là một dimension riêng:

```text
API compatibility
ABI compatibility
source compatibility
binary compatibility
```

---

## 447.7 — ABI identity

ABI identity phụ thuộc:

```text
target
architecture
ABI
calling convention
layout
exported symbols
compiler ABI version
relevant language ABI rules
```

---

## 447.8 — Package manifest

Mỗi package có manifest.

Conceptual:

```text
package = {
    name,
    version,
    edition,
    targets,
    dependencies,
    features,
    artifacts,
    exports
}
```

---

## 447.9 — Manifest không chứa build logic tùy tiện

Build configuration và build script được phân biệt.

Manifest phải có schema có thể parse deterministic.

---

## 447.10 — Source root

Manifest xác định source root.

Default convention có thể là:

```text
src/
```

---

## 447.11 — Package layout

Một package có thể chứa:

```text
package.ax
src/
tests/
examples/
build/
docs/
assets/
```

nhưng compiler không hard-code tất cả directory names nếu manifest override được.

---

## 447.12 — Library package

Library package không nhất thiết có executable entry point.

---

## 447.13 — Binary package

Package có thể phân phối prebuilt artifacts.

---

## 447.14 — Mixed package

Một package có thể chứa:

```text
source
+ library
+ executable
+ tools
```

nếu manifest cho phép.

---

## 447.15 — Artifact kinds

Artifact kind:

```text
executable
static-library
dynamic-library
object
wasm
metadata
debug-info
```

---

## 447.16 — Target-specific artifact

Một package có thể có nhiều artifacts:

```text
windows-x86_64
linux-x86_64
linux-aarch64
macos-aarch64
ios-aarch64
android-aarch64
wasm32
```

---

## 447.17 — Target selection

Package resolver chọn artifact phù hợp target hiện tại.

---

## 447.18 — Source fallback

Nếu package có source nhưng thiếu native binary cho target:

```text
source build
```

được phép.

---

## 447.19 — Binary-only package

Package có thể chỉ phân phối binary.

---

## 447.20 — Binary-only limitation

Binary-only package phải cung cấp đủ:

```text
API metadata
ABI metadata
target artifact
```

---

## 447.21 — No source requirement

Consumer không cần source implementation nếu binary artifact đủ.

---

## 447.22 — Public semantic metadata

Binary package phải có public semantic metadata để compiler/tooling hiểu exported API.

---

## 447.23 — Private metadata

Private implementation metadata không cần phân phối.

---

## 447.24 — Generic library

Generic API yêu cầu một trong hai:

```text
generic source/IR available
```

hoặc:

```text
precompiled generic instances
```

---

## 447.25 — Generic binary package

Binary-only generic package phải mô tả supported instantiations.

---

## 447.26 — Generic fallback

Nếu requested generic instance chưa tồn tại và implementation không được phân phối:

```text
compile error
```

thay vì silently dùng một implementation khác.

---

## 447.27 — ABI manifest

Native artifact phải có ABI manifest.

Conceptual:

```text
artifact {
    target
    abi
    exports
    imports
    layout_hash
    abi_hash
}
```

---

## 447.28 — Exported symbol

Mỗi exported symbol có:

```text
name
kind
signature
visibility
ABI
```

---

## 447.29 — Symbol mangling

Axiom internal symbols có thể mangled.

---

## 447.30 — Stable external names

FFI/public native exports có thể dùng:

```text
@export("foo")
```

hoặc equivalent mechanism.

---

## 447.31 — Language symbol vs native symbol

Hai identity phải được phân biệt:

```text
Axiom SymbolId
Native SymbolName
```

---

## 447.32 — ABI hash

ABI hash được tính từ các ABI-relevant components.

Không bao gồm:

```text
comments
whitespace
internal implementation
```

nếu chúng không ảnh hưởng artifact ABI.

---

## 447.33 — API hash

API hash bao gồm public semantic interface.

---

## 447.34 — Source hash

Source/content hash xác định exact source inputs.

---

## 447.35 — Artifact hash

Artifact hash xác định exact bytes.

---

## 447.36 — Bốn loại identity

Axiom phân biệt:

```text
SourceHash
Semantic/APIHash
ABIHash
ArtifactHash
```

---

## 447.37 — Hash independence

Thay đổi implementation có thể:

```text
SourceHash changes
ArtifactHash changes
```

nhưng:

```text
APIHash unchanged
ABIHash unchanged
```

---

## 447.38 — ABI-compatible implementation update

Nếu ABI/API không đổi, binary consumer có thể tiếp tục dùng dynamic library theo compatibility rules.

---

## 447.39 — Static library limitation

Static linking copies code vào consumer artifact.

Thay đổi library yêu cầu relink để nhận implementation mới.

---

## 447.40 — Dynamic library model

Dynamic library có:

```text
ABI
exports
version
platform target
```

---

## 447.41 — ABI compatibility check

Loader/package manager có thể reject incompatible ABI.

---

## 447.42 — Symbol compatibility

Missing required exported symbol là hard incompatibility.

---

## 447.43 — Signature compatibility

Changed parameter/return representation có thể invalidate ABI.

---

## 447.44 — Struct layout compatibility

Public FFI-visible struct layout change có thể break ABI.

---

## 447.45 — Private struct layout

Private implementation layout không affect public ABI nếu không exposed.

---

## 447.46 — Opaque types

Library nên dùng opaque handles khi muốn thay đổi implementation mà không break ABI.

---

## 447.47 — ABI-stable interface

Axiom hỗ trợ explicit ABI-stable API boundary.

---

## 447.48 — Default internal ABI

Axiom internal ABI không nhất thiết forever-stable giữa compiler releases.

---

## 447.49 — Stable ABI marker

Library có thể yêu cầu:

```text
@stable_abi
```

cho API cần long-term binary compatibility.

---

## 447.50 — ABI evolution

Stable ABI change phải:

```text
new ABI version
```

hoặc backward-compatible extension.

---

## 447.51 — Symbol versioning

ELF-style symbol versioning có thể được backend hỗ trợ.

---

## 447.52 — Platform ABI

Native ABI backend quyết định details cho:

```text
SysV64
Win64
AAPCS64
Apple AArch64
WASM
```

---

## 447.53 — Package target compatibility

Package resolver không được chọn artifact chỉ dựa trên architecture.

Phải xét:

```text
OS
ABI
architecture
CPU features
runtime requirements
```

---

## 447.54 — CPU features

Artifact có thể yêu cầu:

```text
avx2
avx512
neon
sve
```

---

## 447.55 — Feature compatibility

Artifact yêu cầu unsupported CPU feature phải bị reject hoặc package manager chọn fallback artifact.

---

## 447.56 — Multi-variant package

Package có thể chứa:

```text
generic
optimized
```

variants.

---

## 447.57 — Runtime CPU dispatch

Library có thể dùng runtime feature detection.

---

## 447.58 — CPU dispatch safety

Function pointer dispatch phải preserve ABI.

---

## 447.59 — Static linking

Axiom linker có thể link `.a`/archive-equivalent.

---

## 447.60 — Dynamic linking

Axiom linker tạo executable với import tables phù hợp target.

---

## 447.61 — Native library consumption

Axiom có thể consume:

```text
Axiom library
C library
native platform library
```

qua explicit ABI declaration.

---

## 447.62 — Third-party compiler independence

Axiom không cần LLVM/GCC/Clang để consume native library.

---

## 447.63 — Object dependency

Package có thể phân phối object files.

---

## 447.64 — Object compatibility

Object phải match:

```text
target
ABI
relocation model
object format
```

---

## 447.65 — C interoperability package

Package có thể wrap C ABI.

---

## 447.66 — C header integration

Header translation không phải compiler core requirement.

Một tool riêng có thể generate/import declarations.

---

## 447.67 — Imported C metadata

Imported declarations phải được materialize thành Axiom semantic declarations.

---

## 447.68 — Native SDK

Platform SDK có thể được represented as Axiom package metadata + native libraries.

---

## 447.69 — System library package

OS libraries có thể được modeled như target-provided packages.

---

## 447.70 — No central registry requirement

Axiom package ecosystem không phụ thuộc một registry duy nhất.

---

## 447.71 — Dependency sources

Allowed dependency sources:

```text
path
git
registry
archive
local cache
system package
platform SDK
```

---

## 447.72 — Path dependency

Dùng local package.

---

## 447.73 — Git dependency

Manifest có:

```text
repository
revision/tag
```

---

## 447.74 — Git reproducibility

Production lockfile nên pin immutable revision.

---

## 447.75 — Registry dependency

Registry packages được xác định bằng:

```text
name
version
registry identity
```

---

## 447.76 — Multiple registries

Project có thể configure nhiều registries.

---

## 447.77 — Registry trust

Registry identity là một phần dependency source identity.

---

## 447.78 — Archive dependency

Archive phải có hash.

---

## 447.79 — Content-addressed dependency

Cache key có thể dựa trên content hash.

---

## 447.80 — Lockfile

Lockfile ghi exact resolved dependency graph.

---

## 447.81 — Lockfile contents

Tối thiểu:

```text
package
version
source
revision/hash
dependencies
```

---

## 447.82 — Lockfile deterministic

Cùng manifest + registry state + lockfile phải resolve cùng graph.

---

## 447.83 — Offline build

Nếu dependencies đã cached, project có thể build offline.

---

## 447.84 — Vendoring

Project có thể vendor dependency source/artifacts.

---

## 447.85 — Vendor identity

Vendored dependency vẫn giữ original provenance metadata.

---

## 447.86 — Dependency override

Developer có thể override dependency bằng path/local source.

Override phải visible trong build metadata.

---

## 447.87 — Patch dependency

Temporary patch mechanism được hỗ trợ ở package manager layer.

---

## 447.88 — Dependency graph

Graph:

```text
Application
 ├── A
 │   ├── C
 │   └── D
 └── B
     └── C
```

---

## 447.89 — Duplicate dependency versions

Có thể coexist nếu package identity/version khác nhau.

---

## 447.90 — Type identity across versions

Types từ hai package versions khác nhau không tự động được coi là cùng type.

---

## 447.91 — Dependency unification

Resolver chỉ unify versions khi compatibility rules cho phép.

---

## 447.92 — Cyclic dependencies

Package-level dependency cycles bị reject mặc định.

---

## 447.93 — Module cycles

Module cycles được xử lý riêng theo module rules.

---

## 447.94 — Build dependency vs runtime dependency

Manifest phải phân biệt:

```text
build dependency
runtime dependency
development dependency
```

---

## 447.95 — Test dependency

Test-only dependencies không được link vào production artifact.

---

## 447.96 — Build tool dependency

Build tool không tự trở thành application runtime dependency.

---

## 447.97 — Feature flags

Features là named capabilities.

---

## 447.98 — Feature resolution

Feature graph phải deterministic.

---

## 447.99 — Feature unification

Nếu dependency được dùng ở nhiều nơi, feature resolution phải có deterministic rule.

---

## 447.100 — No hidden features

Feature phải được phản ánh trong build metadata.

---

# 447.101 — Package capability manifest

Package có thể khai báo:

```text
requires:
    threads
    filesystem
    network

provides:
    compression
    parser
```

---

## 447.102 — Capability propagation

Application dependency có thể kéo runtime capability tương ứng.

---

## 447.103 — Capability pruning

Unused capabilities không được link nếu linker/compiler chứng minh không cần.

---

## 447.104 — Static dependency pruning

Dead code elimination áp dụng xuyên static library boundaries nếu artifact format/linker metadata cho phép.

---

## 447.105 — Dynamic dependency

Dynamic library dependency không thể bị dead-code eliminated như static code.

---

## 447.106 — Dependency tree

Tool:

```text
axiom tree
```

có thể hiển thị dependency graph.

---

## 447.107 — Binary dependency tree

Tool cũng có thể hiển thị:

```text
artifact
→ dynamic libraries
→ native imports
→ runtime capabilities
```

---

## 447.108 — Dependency size

Package manager/tooling có thể báo contribution vào binary size.

---

## 447.109 — Dependency security metadata

Package metadata có thể chứa:

```text
hash
publisher
signature
source
license
```

---

## 447.110 — Signature

Package registry có thể sign package metadata/artifact.

---

## 447.111 — Signature verification

Package manager có thể verify signature.

---

## 447.112 — Signature ≠ correctness

Signature chứng minh provenance/integrity theo trust model, không chứng minh package không có bug.

---

## 447.113 — Trust policy

Project có thể yêu cầu trusted publishers/registries.

---

## 447.114 — Untrusted package

Package có thể được build trong isolated environment/tooling policy.

---

## 447.115 — Build script isolation

Build scripts có thể bị sandbox/restricted tùy security mode.

---

## 447.116 — Package audit

Tooling có thể report:

```text
unsafe usage
FFI
build scripts
native binaries
network capabilities
filesystem capabilities
```

---

## 447.117 — Native binary provenance

Prebuilt native artifact phải ghi:

```text
producer
compiler
target
source hash
build profile
```

khi available.

---

## 447.118 — Compiler provenance

Metadata:

```text
compiler version
compiler build hash
```

---

## 447.119 — Reproducible package

Package build phải có khả năng reproduce nếu inputs deterministic.

---

## 447.120 — Reproducibility inputs

Bao gồm:

```text
source
dependencies
compiler
target
features
environment inputs
```

---

## 447.121 — Environment capture

Build system phải tránh implicit environment dependencies.

---

## 447.122 — Build timestamp

Timestamp không được âm thầm làm artifact nondeterministic.

---

## 447.123 — Build path

Absolute local paths không được embedded vào release artifact nếu không cần.

---

## 447.124 — Random build IDs

Nếu cần unique IDs, reproducible builds phải có deterministic mode.

---

## 447.125 — Debug artifacts

Debug information có thể được phân phối riêng.

---

## 447.126 — Source archive

Source package có thể chứa exact source snapshot.

---

## 447.127 — Binary archive

Binary package có thể chỉ chứa target artifacts + metadata.

---

## 447.128 — Universal package

Một package archive có thể chứa nhiều target artifacts.

---

## 447.129 — Artifact selection

Consumer chỉ tải/use artifact cần target nếu registry hỗ trợ partial retrieval.

---

## 447.130 — Cache

Global cache có thể lưu:

```text
source package
semantic metadata
object files
native libraries
debug artifacts
```

---

## 447.131 — Cache key

Cache key phải bao gồm relevant:

```text
compiler
target
features
dependencies
source/semantic hashes
```

---

## 447.132 — Cache correctness

Cache hit không được thay đổi semantics.

---

## 447.133 — Cache poisoning

Cache artifact phải được verify bằng hash/provenance khi security mode yêu cầu.

---

## 447.134 — Local cache trust

Developer có thể chọn trust policy cho local cache.

---

## 447.135 — Shared cache

CI có thể dùng remote shared cache.

---

## 447.136 — Remote cache

Remote cache entries phải content-addressed và integrity-checked.

---

## 447.137 — Cache eviction

Eviction không ảnh hưởng correctness.

---

## 447.138 — Precompiled semantic metadata

Compiler có thể skip parsing source nếu metadata đủ và source unchanged.

---

## 447.139 — Precompiled object

Compiler có thể reuse object code khi relevant semantic/target inputs unchanged.

---

## 447.140 — Incremental package compilation

Chỉ changed package units được compile.

---

## 447.141 — Cross-package invalidation

Thay đổi public ABI/API invalidates consumers cần thiết.

Private implementation change không nhất thiết invalidate downstream semantic analysis.

---

## 447.142 — ABI boundary caching

Stable ABI package có thể giảm recompilation.

---

## 447.143 — LTO package

Package có thể cung cấp IR/LTO metadata tùy distribution mode.

---

## 447.144 — No mandatory IR distribution

Axiom không yêu cầu package phải public compiler IR.

---

## 447.145 — Closed-source package

Commercial/proprietary package có thể phân phối:

```text
native artifact
+ public metadata
```

mà không public implementation.

---

## 447.146 — Closed-source generics

Generic API phải dùng precompiled instances hoặc dynamic/type-erased boundary.

---

## 447.147 — Static closed-source library

Static binary package vẫn có thể export public ABI metadata.

---

## 447.148 — Dynamic closed-source library

Dynamic library có thể giữ implementation hoàn toàn private.

---

## 447.149 — Package documentation

Package có thể phân phối docs gắn SymbolId.

---

## 447.150 — AI package metadata

AI agent có thể query:

```text
package
→ public API
→ types
→ traits
→ dependencies
→ effects
→ capabilities
→ ABI
→ examples
```

---

# 447.151 — Package compatibility matrix

Tooling phải có khả năng phân biệt:

| Thay đổi | Source compatibility | API | ABI |
|---|---|---|---|
| Comment | Có | Có | Có |
| Private implementation | Thường có | Có | Có |
| Public function body | Thường có | Có | Có |
| Remove public function | Không | Không | Có thể |
| Đổi public signature | Không | Không | Thường không |
| Đổi private struct layout | Có | Có | Có |
| Đổi public `repr(C)` layout | Có thể không | Có thể không | Không |
| Đổi native calling convention | Có thể không | Có thể | Không |

Đây là **ma trận kỹ thuật**, không phải ranking.

---

## 447.152 — Compatibility checker

Tool:

```text
axiom api-check old new
```

có thể phân tích public changes.

---

## 447.153 — ABI checker

```text
axiom abi-check old new
```

phân tích native compatibility.

---

## 447.154 — Package migration

Breaking API change có thể đi kèm migration metadata.

---

## 447.155 — Deprecation

Declaration có thể được đánh dấu:

```text
@deprecated("...")
```

---

## 447.156 — Deprecation metadata

Compiler biết:

```text
since
replacement
reason
```

---

## 447.157 — Removal policy

Deprecation không tự động remove symbol.

---

## 447.158 — API edition

Axiom edition có thể thay đổi language behavior mà không phá package cũ.

---

## 447.159 — Package edition

Manifest ghi edition.

---

## 447.160 — Mixed editions

Workspace có thể chứa packages dùng editions khác nhau.

---

## 447.161 — Edition boundary

Package API phải có compatibility translation nếu language semantics thay đổi.

---

## 447.162 — Compiler compatibility

Compiler mới có thể compile package cũ theo edition metadata.

---

## 447.163 — Minimum compiler version

Package có thể khai báo:

```text
requires_compiler >= X
```

---

## 447.164 — Maximum compiler version

Không nên dùng trừ trường hợp compatibility contract thật sự cần thiết.

---

## 447.165 — Compiler feature requirements

Package có thể yêu cầu specific language/compiler capabilities.

---

## 447.166 — Target feature requirements

Tách:

```text
compiler feature
target CPU feature
OS capability
```

---

## 447.167 — Dependency feature conflict

Resolver phải báo conflict deterministic.

---

## 447.168 — Version conflict diagnostics

Diagnostic phải chỉ rõ:

```text
requester
requested range
resolved version
conflicting constraint
```

---

## 447.169 — Dependency provenance graph

Tooling có thể trace:

```text
application
→ dependency
→ registry
→ exact artifact
→ hash
```

---

## 447.170 — SBOM-style metadata

Axiom ecosystem có thể xuất software component inventory.

---

## 447.171 — License metadata

Package manifest có thể khai báo license metadata.

Compiler không enforce legal interpretation.

---

## 447.172 — Source attribution

Artifact có thể giữ provenance tới package/source.

---

## 447.173 — Reproducible verification

Consumer có thể:

```text
download source
build
hash
compare artifact
```

---

## 447.174 — Binary transparency

Registry có thể publish immutable artifact records.

---

## 447.175 — Package immutability

Published package version không được silently replace trong secure registry model.

---

## 447.176 — Yank policy

Package version có thể bị yanked khỏi resolver mới nhưng existing lockfiles vẫn có thể reference nếu artifact còn available.

---

## 447.177 — Lockfile preservation

Existing reproducible build không bị phá chỉ vì package bị yanked.

---

## 447.178 — Offline lock

Lockfile phải đủ thông tin để identify exact dependency versions/revisions.

---

## 447.179 — Missing artifact

Nếu artifact không còn available:

```text
rebuild from source
```

nếu source available.

---

## 447.180 — Artifact fallback

Package resolver có thể chọn source build nếu binary artifact không tồn tại.

---

## 447.181 — Deterministic fallback

Source fallback phải obey same dependency lock/features/target.

---

## 447.182 — Package build graph

```text
Resolve
  ↓
Fetch
  ↓
Verify
  ↓
Metadata
  ↓
Compile
  ↓
Link
  ↓
Artifact
```

---

## 447.183 — Fetch phase

Fetch không được thay đổi semantic dependency resolution.

---

## 447.184 — Verify phase

Integrity verification xảy ra trước consumption trong secure mode.

---

## 447.185 — Metadata phase

Compiler đọc API/ABI metadata trước implementation compilation nếu binary package.

---

## 447.186 — Compile phase

Only required source/generic units được compile.

---

## 447.187 — Link phase

Axiom linker resolves native dependencies.

---

## 447.188 — Artifact phase

Output được hashed và recorded.

---

## 447.189 — Package graph serialization

Build graph có thể serialize để AI/CI inspect.

---

## 447.190 — Build provenance

Final executable metadata có thể trace:

```text
binary
→ object
→ package
→ source
→ compiler
→ target
```

---

## 447.191 — Binary introspection

Tool:

```text
axiom inspect binary
```

có thể show:

```text
target
ABI
symbols
dependencies
capabilities
debug ID
build hash
```

---

## 447.192 — Package introspection

```text
axiom inspect package
```

show:

```text
API
ABI
dependencies
targets
artifacts
features
```

---

## 447.193 — AI package context

```text
axiom query-context package.foo
```

trả context compact cho agent.

---

## 447.194 — No natural-language dependency guessing

AI tooling không cần đoán API từ README nếu semantic metadata tồn tại.

---

## 447.195 — Documentation remains useful

Metadata không loại bỏ docs/examples.

---

## 447.196 — Example metadata

Examples có thể link với API symbols.

---

## 447.197 — API usage search

AI/IDE có thể query:

```text
examples_using(SymbolId)
```

---

## 447.198 — Dependency migration support

Tool có thể xác định downstream usages trước API migration.

---

## 447.199 — Ecosystem architecture

```text
                 Axiom Registry / Git / Local
                            │
                            ▼
                    Package Resolver
                            │
                    Lock + Verify
                            │
                            ▼
                    Semantic Metadata
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
       Source Compile                Binary Consume
             │                             │
             └──────────────┬──────────────┘
                            ▼
                       Axiom Linker
                            │
                            ▼
                  Native/WASM Artifact
```

---

# 447.200 — Hard invariants

1. Package có identity ổn định.
2. Package version và ABI version là hai khái niệm khác nhau.
3. API hash, ABI hash, source hash và artifact hash được phân biệt.
4. Binary-only package phải cung cấp public semantic metadata.
5. Native artifact phải target-aware.
6. Artifact selection phải xét architecture + OS + ABI + required CPU features.
7. Axiom có thể consume native libraries mà không cần LLVM/GCC/Clang.
8. Static và dynamic linking là hai mô hình khác nhau.
9. Static library thay đổi implementation cần relink để nhận code mới.
10. Dynamic library compatibility phụ thuộc ABI.
11. Public struct layout có thể là ABI contract.
12. Opaque types cho phép giữ implementation private.
13. Stable ABI phải explicit.
14. Internal Axiom ABI không bắt buộc stable vĩnh viễn.
15. Generic binary packages phải có implementation/instances phù hợp.
16. Package resolver hỗ trợ path dependencies.
17. Package resolver hỗ trợ git dependencies.
18. Package resolver hỗ trợ registry dependencies.
19. Package resolver hỗ trợ archive/local dependencies.
20. Lockfile ghi exact dependency resolution.
21. Lockfile phải deterministic.
22. Offline build phải được hỗ trợ khi dependency data đã cached.
23. Vendoring phải preserve provenance.
24. Dependency graph phải deterministic.
25. Package cycles bị reject theo package dependency rules.
26. Build/test/dev dependencies được phân biệt.
27. Feature resolution phải deterministic.
28. Không có hidden dependency features.
29. Runtime capabilities phải có thể được biểu diễn.
30. Unused static dependencies/capabilities có thể được prune.
31. Package cache phải có deterministic keys.
32. Cache eviction không ảnh hưởng correctness.
33. Remote cache phải integrity-checkable.
34. Precompiled metadata có thể được reuse.
35. Precompiled objects có thể được reuse khi inputs phù hợp.
36. Public API changes có thể được phát hiện bằng semantic metadata.
37. ABI changes có thể được phát hiện bằng ABI metadata.
38. Closed-source native packages được hỗ trợ.
39. Closed-source generic packages phải có precompiled instances hoặc type-erased boundary.
40. Package có thể phân phối static library.
41. Package có thể phân phối dynamic library.
42. Package có thể phân phối WASM artifact.
43. Package có thể phân phối nhiều target variants.
44. Package manager không phụ thuộc một registry duy nhất.
45. Registry identity là một phần dependency provenance.
46. Package signatures có thể được verify.
47. Signature không được coi là proof of software correctness.
48. Package provenance phải có thể truy vấn.
49. Native artifact provenance phải có thể truy vấn.
50. Compiler provenance phải có thể truy vấn.
51. Reproducible package build phải có thể xác định inputs.
52. Build timestamp không được âm thầm phá reproducibility.
53. Absolute local paths không nên leak vào release artifacts.
54. Package versions đã publish không được silently mutate trong secure registry model.
55. Yank không được phá existing locked builds nếu artifact/source còn tồn tại.
56. API compatibility và ABI compatibility được đánh giá độc lập.
57. Package edition được lưu trong manifest.
58. Compiler version requirement có thể được khai báo.
59. Target CPU requirements được tách khỏi compiler requirements.
60. Package metadata phải AI-readable.
61. Dependency graph phải AI-queryable.
62. API usage/examples có thể liên kết với SymbolId.
63. Binary có thể trace về package/source khi provenance được giữ.
64. Package tooling có thể inspect artifact mà không cần source.
65. Package tooling không được yêu cầu một compiler bên thứ ba.
66. Axiom linker là thành phần chính thức của native dependency model.
67. Package system không được biến runtime thành dependency bắt buộc.
68. Binary size phải phụ thuộc vào code/capability thực sự được link.
69. Native package consumption phải respect ABI/layout contracts.
70. **Axiom package phải là một đơn vị phân phối source + semantics + native artifact + provenance, đủ mạnh để hỗ trợ cả open-source lẫn closed-source ecosystem mà không hy sinh native compiler/linker độc lập.**

**BOOTSTRAP-447 hoàn tất.**

---

# BOOTSTRAP-448 — BUILD SYSTEM, INCREMENTAL COMPILATION, PARALLELISM, CACHE, CROSS-COMPILATION & REPRODUCIBLE BUILD GRAPH

Task tiếp theo khóa **build engine thực sự** của Axiom.

Mục tiêu:

```text
Source
   ↓
Package Graph
   ↓
Query Graph
   ↓
Incremental Build Graph
   ↓
Parallel Compilation
   ↓
Cache
   ↓
Link
   ↓
Artifact
```

Axiom build system không chỉ là wrapper gọi compiler. Nó phải là một **dependency-aware incremental execution engine**.

---

## 448.1 — Build graph

Build graph gồm nodes và edges.

Node có thể là:

```text
package
module
source file
semantic query
generic instance
object
library
executable
```

---

## 448.2 — Build graph ≠ dependency graph

Dependency graph mô tả semantic dependencies.

Build graph mô tả operations cần thực thi.

---

## 448.3 — Query graph

Compiler query graph từ 436 là nền tảng của incremental compilation.

---

## 448.4 — Dirty state

Node dirty khi relevant input thay đổi.

---

## 448.5 — Clean state

Node clean nếu cached result vẫn valid.

---

## 448.6 — Fine-grained invalidation

Thay đổi function body không nên mặc định recompile toàn package.

---

## 448.7 — Public API invalidation

Thay đổi public signature invalidates dependent semantic queries.

---

## 448.8 — Private implementation invalidation

Private body change chủ yếu invalidate codegen/link-dependent artifacts.

---

## 448.9 — Layout invalidation

Thay đổi public layout invalidates consumers phụ thuộc layout.

---

## 448.10 — Trait invalidation

Thay đổi trait contract invalidates relevant implementations/constraints.

---

## 448.11 — Generic invalidation

Generic source change invalidates affected instances.

---

## 448.12 — Comptime invalidation

Comptime result invalidated khi:

```text
function
arguments
dependencies
target
```

relevant changes.

---

## 448.13 — Dependency invalidation

Dependency semantic hash changes propagate only tới dependent queries.

---

## 448.14 — Content hash

Source file identity sử dụng content hash.

---

## 448.15 — Semantic hash

Semantic hash xác định meaning-relevant state.

---

## 448.16 — Codegen hash

Codegen key bao gồm:

```text
MIR/LIR
target
optimization profile
CPU features
ABI
```

---

## 448.17 — Link hash

Link key bao gồm relevant:

```text
objects
libraries
linker options
target
exports
runtime components
```

---

## 448.18 — Cache layers

Axiom có nhiều cache:

```text
source cache
parse cache
semantic cache
comptime cache
MIR cache
codegen cache
object cache
link cache
artifact cache
```

---

## 448.19 — Cache independence

Một cache layer có thể invalidate mà không cần invalidate tất cả layers phía trên nếu dependency remains valid.

---

## 448.20 — Cache storage

Cache có thể local hoặc remote.

---

## 448.21 — Content-addressed cache

Immutable cache entries nên dùng content-addressed IDs.

---

## 448.22 — Cache metadata

Mỗi entry ghi:

```text
key
producer
compiler
target
dependencies
artifact hash
```

---

## 448.23 — Cache corruption

Corrupted cache entry phải bị loại bỏ/recomputed.

---

## 448.24 — Cache correctness

Cache result phải byte/semantic equivalent với fresh build theo cùng reproducibility mode.

---

## 448.25 — Parallel compilation

Independent graph nodes được compile song song.

---

## 448.26 — Deterministic scheduling

Parallel execution không được thay đổi semantic result.

---

## 448.27 — CPU utilization

Build scheduler có thể dùng toàn bộ available CPU.

---

## 448.28 — Memory-aware scheduling

Scheduler phải tránh khởi chạy quá nhiều compiler workers gây OOM.

---

## 448.29 — Job pools

Có thể có:

```text
frontend workers
codegen workers
link workers
```

---

## 448.30 — Link bottleneck

Linking có thể là serialized hoặc partitioned tùy backend.

---

## 448.31 — Parallel codegen

Generic instances/functions độc lập có thể codegen song song.

---

## 448.32 — Deterministic object ordering

Parallel compilation vẫn tạo deterministic object ordering.

---

## 448.33 — Build cancellation

User có thể cancel build.

---

## 448.34 — Cancellation cleanup

Cancellation phải cleanup temporary resources.

---

## 448.35 — Incremental daemon

`axiom build --watch` giữ compiler database trong memory.

---

## 448.36 — Daemon invalidation

File changes trigger only affected queries.

---

## 448.37 — LSP shared database

LSP và build daemon có thể share compiler snapshot architecture.

---

## 448.38 — Snapshot isolation

Running build không làm LSP thấy inconsistent intermediate state.

---

## 448.39 — Build profiles

Minimum:

```text
debug
release
```

---

## 448.40 — Optimization profile

Profile controls:

```text
optimization level
debug info
LTO
sanitizers
assertions
```

---

## 448.41 — Optimization levels

Conceptual:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

---

## 448.42 — Debug profile

Ưu tiên:

```text
fast compile
debuggability
```

---

## 448.43 — Release profile

Ưu tiên:

```text
performance
size
determinism
```

theo project configuration.

---

## 448.44 — Size profile

Có thể ưu tiên binary size.

---

## 448.45 — LTO

Modes:

```text
off
thin
full
```

hoặc equivalent implementation.

---

## 448.46 — Incremental LTO

Compiler có thể cache LTO-relevant partitions.

---

## 448.47 — PGO

Profile-guided optimization là optional build feature.

---

## 448.48 — PGO workflow

```text
instrument
→ run
→ collect profile
→ optimize
```

---

## 448.49 — Profile identity

Profile data phải identify:

```text
binary version
source/build identity
target
```

---

## 448.50 — Stale profile

Stale PGO data phải bị reject hoặc explicitly treated as approximate.

---

## 448.51 — Cross compilation

Host và target được phân biệt rõ.

```text
HOST
TARGET
```

---

## 448.52 — Build host

Compiler chạy trên host.

---

## 448.53 — Target

Artifact chạy trên target.

---

## 448.54 — Host tools

Build tools execute on host unless explicitly configured otherwise.

---

## 448.55 — Target runtime

Runtime components selected for target.

---

## 448.56 — Build triple

Target identity:

```text
architecture-os-abi
```

với extensions cho environment/features.

---

## 448.57 — Native cross compiler

Axiom compiler có target backends độc lập.

---

## 448.58 — No host compiler dependency

Cross compilation không gọi host GCC/Clang để produce target code.

---

## 448.59 — Sysroot

Target SDK/sysroot được coi là input dependency.

---

## 448.60 — Platform SDK

iOS/Android/macOS/Windows/Linux SDK metadata/artifacts là external platform inputs.

---

## 448.61 — SDK identity

Build graph ghi:

```text
SDK version
SDK hash
target
```

---

## 448.62 — Toolchain identity

Axiom toolchain:

```text
compiler
linker
assembler if internally used
runtime
SDK
```

có identity.

---

## 448.63 — Internal assembler

Axiom machine encoder là default.

External assembler không phải dependency bắt buộc.

---

## 448.64 — External linker

Axiom linker là default native linker.

---

## 448.65 — Platform signing

iOS/Android executable signing có thể yêu cầu platform tools/credentials.

Đây là deployment phase, không phải core compilation.

---

## 448.66 — Build phases

```text
Resolve
→ Fetch
→ Check
→ Compile
→ Link
→ Package
→ Sign
→ Deploy
```

---

## 448.67 — Signing separation

Signing không thay đổi compiled program semantics.

---

## 448.68 — Reproducible compile

Compile phase phải deterministic khi deterministic mode bật.

---

## 448.69 — Reproducible link

Linker phải deterministic.

---

## 448.70 — Object ordering

Link order phải explicit/deterministic.

---

## 448.71 — Symbol ordering

Symbol tables phải deterministic nếu format cho phép.

---

## 448.72 — Section ordering

Sections phải deterministic.

---

## 448.73 — UUID/build ID

Deterministic mode phải derive IDs từ artifact/input identity.

---

## 448.74 — Timestamp fields

PE/ELF/Mach-O timestamp-like metadata phải deterministic hoặc omitted/fixed.

---

## 448.75 — Debug paths

Debug paths phải hỗ trợ path remapping.

---

## 448.76 — Path remapping

Ví dụ conceptual:

```text
source=/home/user/project
debug=/src
```

---

## 448.77 — Environment variables

Build chỉ phụ thuộc environment variables được manifest khai báo.

---

## 448.78 — Undeclared environment

Undeclared environment dependency có thể bị diagnostic trong reproducible mode.

---

## 448.79 — Network access

Compiler core không tự động network access.

---

## 448.80 — Dependency fetching

Package manager chịu trách nhiệm fetch dependencies.

---

## 448.81 — Build scripts

Build scripts có explicit input/output declarations.

---

## 448.82 — Build script cache

Build script result cache keyed by:

```text
script source
inputs
environment
target
compiler/tool version
```

---

## 448.83 — Generated artifacts

Generated files phải là explicit build graph outputs.

---

## 448.84 — Generated source

Generated source có provenance.

---

## 448.85 — Build graph cycle

Illegal build cycle phải được report rõ path.

---

## 448.86 — Parallel dependency resolution

Independent package fetch/verification có thể chạy song song.

---

## 448.87 — Registry concurrency

Resolver phải giữ deterministic resolution dù network completion order khác nhau.

---

## 448.88 — Network failure

Build phải fail deterministically khi required dependency unavailable và không có cache.

---

## 448.89 — Offline mode

```text
axiom build --offline
```

cấm network dependency fetching.

---

## 448.90 — Frozen mode

Conceptual:

```text
--locked
```

reject dependency resolution changes.

---

## 448.91 — Update mode

Dependency updates là explicit operation.

---

## 448.92 — Lock update

```text
axiom update
```

cập nhật lockfile theo resolver rules.

---

## 448.93 — Minimal update

Có thể update một dependency mà không thay toàn graph nếu constraints cho phép.

---

## 448.94 — Build reproducibility report

Tool:

```text
axiom reproducibility
```

có thể show mismatched inputs.

---

## 448.95 — Build trace

Compiler có thể export:

```text
query
cache hit/miss
duration
memory
worker
```

---

## 448.96 — Performance diagnostics

Build trace giúp tìm:

```text
slow frontend
slow trait solving
slow comptime
slow codegen
slow linking
```

---

## 448.97 — Query profiling

Compiler query engine có timing counters.

---

## 448.98 — Memory profiling

Build engine có thể report peak memory.

---

## 448.99 — Incremental effectiveness

Compiler có thể report:

```text
reused
recompiled
invalidated
```

---

## 448.100 — Build summary

Ví dụ conceptual:

```text
packages: 12
files: 184
recompiled: 7
cache hits: 96%
codegen: 18 functions
link: 1
artifact: ...
```

---

# 448.101 — Build graph visualization

Tool có thể export Graphviz/JSON hoặc equivalent.

---

## 448.102 — AI build diagnosis

AI agent có thể query:

```text
why_rebuilt(file)
why_invalidated(symbol)
why_linked(library)
why_slow(query)
```

---

## 448.103 — Rebuild explanation

Compiler phải có khả năng giải thích invalidation chain machine-readably.

---

## 448.104 — Example

```text
Foo.body changed
→ MIR(Foo) invalidated
→ codegen(Foo) invalidated
→ object(packageA) invalidated
→ executable invalidated
```

---

## 448.105 — Minimal rebuild

Không rebuild unrelated package chỉ vì source timestamp thay đổi.

---

## 448.106 — Timestamp independence

Content hash, không timestamp, là primary source identity.

---

## 448.107 — Filesystem watcher

Watch mode có thể dùng OS file notification.

---

## 448.108 — Watcher fallback

Polling fallback có thể tồn tại.

---

## 448.109 — Atomic source update

Editor save operations tạo temporary files/renames; compiler phải xử lý safely.

---

## 448.110 — Partial writes

Compiler không nên cache half-written source.

---

## 448.111 — Build isolation

Parallel builds của projects khác nhau không được corrupt shared cache.

---

## 448.112 — Cache locking

Cache writes phải atomic.

---

## 448.113 — Cache transaction

Artifact chỉ trở thành visible sau khi hoàn thành và verified.

---

## 448.114 — Crash recovery

Compiler crash không để lại cache state khiến subsequent build sai.

---

## 448.115 — Temporary artifacts

Temp files có cleanup policy.

---

## 448.116 — Disk quota

Cache có thể có configurable size limit.

---

## 448.117 — Remote cache authentication

Remote cache có optional authentication.

---

## 448.118 — Remote cache trust

Security-sensitive builds có thể yêu cầu artifact verification.

---

## 448.119 — Cache sharing

Different users/machines có thể reuse immutable artifacts nếu keys match.

---

## 448.120 — Build machine independence

Artifact không được phụ thuộc machine-specific details ngoài declared inputs.

---

## 448.121 — CPU-specific build

Nếu artifact được CPU-specialized, CPU feature set phải nằm trong build identity.

---

## 448.122 — Generic target

Generic target artifacts không assume host CPU beyond declared baseline.

---

## 448.123 — Native optimization

Target-specific optimization phải explicit qua target profile/features.

---

## 448.124 — Cross target runtime

Runtime components được compile cho target, không reuse host binaries.

---

## 448.125 — Host build scripts

Host-executed build scripts được compile/run theo host.

---

## 448.126 — Target build scripts

Nếu build script cần target execution, phải explicit và thường không thể chạy trong cross build nếu target unavailable.

---

## 448.127 — Build environment manifest

Có thể khai báo:

```text
host tools
target SDK
environment
```

---

## 448.128 — Tool version locking

External deployment tools có thể được version-pinned.

---

## 448.129 — Native compiler version

Axiom compiler version nằm trong build identity.

---

## 448.130 — Language edition

Edition nằm trong build identity.

---

## 448.131 — Dependency lock

Lockfile hash nằm trong build identity.

---

## 448.132 — Build configuration

Optimization/security/features nằm trong build identity.

---

## 448.133 — Runtime configuration

Selected runtime components nằm trong build identity.

---

## 448.134 — Linker configuration

Link options nằm trong link identity.

---

## 448.135 — Artifact cache correctness

Nếu bất kỳ semantic input nào thay đổi, stale artifact không được reuse.

---

## 448.136 — Conservative invalidation

Nếu compiler không chứng minh được cache validity:

```text
recompute
```

thay vì reuse unsafe cache.

---

## 448.137 — False cache hit forbidden

Correctness ưu tiên cache hit rate.

---

## 448.138 — Cache misses acceptable

Cache miss chỉ ảnh hưởng performance, không semantics.

---

## 448.139 — Distributed build

Future distributed compilation có thể dùng immutable query/artifact cache.

---

## 448.140 — Distributed determinism

Worker placement/order không được ảnh hưởng output.

---

## 448.141 — Remote compilation

Có thể gửi codegen jobs tới remote workers nếu trust/security policy cho phép.

---

## 448.142 — Source privacy

Remote build phải respect package/source privacy.

---

## 448.143 — Build attestation

CI có thể record:

```text
source hash
dependency hash
compiler hash
target
artifact hash
```

---

## 448.144 — Build provenance chain

```text
Source
→ Dependency
→ Compiler
→ Build Config
→ Object
→ Link
→ Artifact
```

---

## 448.145 — Artifact verification

Consumer có thể verify final artifact hash.

---

## 448.146 — Rebuild verification

Independent machine có thể reproduce artifact trong deterministic mode.

---

## 448.147 — Binary reproducibility

Exact byte equality là mục tiêu khi platform/object format cho phép.

---

## 448.148 — Semantic reproducibility

Nếu exact byte equality không khả thi vì platform metadata, compiler vẫn phải support semantic equivalence verification where defined.

---

## 448.149 — Build cache architecture

```text
                  Build Request
                       │
                       ▼
                 Dependency Graph
                       │
                       ▼
                  Query Engine
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Frontend     Comptime      Codegen
          │            │            │
          └────────────┼────────────┘
                       ▼
                     Object
                       │
                       ▼
                     Link
                       │
                       ▼
                    Artifact
```

---

# 448.150 — Hard invariants

1. Build graph và semantic dependency graph được phân biệt.
2. Incremental compilation là first-class.
3. Source identity dùng content hash.
4. Public API changes propagate tới consumers.
5. Private body changes không mặc định rebuild toàn workspace.
6. Layout changes invalidate layout-dependent consumers.
7. Generic changes invalidate affected instances.
8. Comptime changes invalidate dependent results.
9. Query cache là first-class compiler facility.
10. Codegen cache target-specific.
11. Link cache link-input-specific.
12. Cache correctness quan trọng hơn cache hit rate.
13. False cache hit bị cấm.
14. Cache corruption phải recoverable.
15. Cache writes phải atomic.
16. Compiler crash không được corrupt persistent cache.
17. Independent build nodes có thể chạy song song.
18. Parallelism không được thay đổi semantic result.
19. Worker completion order không được thay đổi deterministic artifact.
20. Memory-aware scheduler phải tránh OOM không cần thiết.
21. Build cancellation phải cleanup.
22. Watch mode dùng incremental compiler database.
23. LSP có thể share compiler semantic architecture.
24. Snapshot isolation phải được duy trì.
25. Debug/release/size profiles được phân biệt.
26. Optimization level là build configuration.
27. LTO là optional.
28. PGO là optional.
29. Stale PGO data phải được phát hiện.
30. Host và target được phân biệt.
31. Cross compilation là first-class.
32. Axiom không cần host GCC/Clang/LLVM để compile target.
33. Target SDK/sysroot là explicit input.
34. Platform signing là deployment phase.
35. Axiom machine encoder là native backend mặc định.
36. Axiom linker là native linker mặc định.
37. Reproducible build là first-class mode.
38. Build timestamps không được âm thầm phá reproducibility.
39. Local absolute paths có thể được remap.
40. Undeclared environment dependencies phải được phát hiện trong reproducible mode.
41. Compiler core không tự network.
42. Dependency fetch thuộc package manager.
43. Build scripts là explicit build graph nodes.
44. Generated artifacts có provenance.
45. Build graph cycles phải có diagnostics.
46. Offline mode được hỗ trợ.
47. Locked/frozen dependency mode được hỗ trợ.
48. Dependency updates là explicit.
49. Registry/network completion order không ảnh hưởng resolution.
50. Build trace có thể được xuất.
51. Query profiling có thể được bật.
52. Build memory usage có thể được đo.
53. Incremental hit/miss statistics có thể được đo.
54. AI tooling có thể query why-rebuilt.
55. AI tooling có thể query why-invalidated.
56. AI tooling có thể query why-linked.
57. AI tooling có thể query why-slow.
58. Minimal rebuild là mục tiêu bắt buộc của incremental architecture.
59. Distributed/remote build có thể bổ sung mà không thay đổi semantic model.
60. Remote build phải respect source privacy.
61. Artifact provenance có thể trace về source/dependency/compiler.
62. Reproducible artifacts có thể independently verify.
63. Cache eviction không ảnh hưởng correctness.
64. Build machine-specific state không được implicit input.
65. CPU feature set phải nằm trong build identity.
66. Runtime configuration phải nằm trong build identity.
67. Linker configuration phải nằm trong link identity.
68. Language edition phải nằm trong compilation identity.
69. Compiler version phải nằm trong compilation identity.
70. **Axiom build system phải đạt incremental + parallel + deterministic + cross-platform + reproducible build mà không biến compiler thành một wrapper phụ thuộc toolchain bên ngoài.**

**BOOTSTRAP-448 hoàn tất.**

---

# BOOTSTRAP-449 — OPTIMIZATION PIPELINE, COST MODEL, AUTO-VECTORIZATION, INLINING, ESCAPE ANALYSIS & ZERO-COST ABSTRACTION CONTRACT

Task kế tiếp sẽ khóa phần trực tiếp quyết định mục tiêu:

> **Axiom phải có khả năng tạo native code có hiệu năng ít nhất ngang C/C++ trong các workload tương đương, trong khi abstraction của trait/generic/iterator/struct-method không tự tạo runtime overhead.**

Các phần sẽ khóa gồm:

- optimization pipeline từ HIR → MIR → LIR → Machine IR;
- SSA optimization;
- constant propagation;
- dead-code elimination;
- scalar replacement;
- escape analysis;
- allocation elimination;
- inlining;
- devirtualization;
- specialization;
- generic optimization;
- bounds-check elimination;
- alias analysis;
- loop optimization;
- vectorization/SIMD;
- strength reduction;
- register pressure;
- instruction scheduling;
- PGO;
- size/performance cost model;
- optimization diagnostics;
- `@inline`/`@noinline`;
- zero-cost abstractions;
- optimization correctness;
- fast compilation vs maximum optimization;
- benchmark-driven regression detection;
- AI-readable optimization reports.

**BOOTSTRAP-449 là task kế tiếp.**