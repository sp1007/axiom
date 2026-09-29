Tiếp tục từ **Axiom Build System + Package Manager v0.1**. Với toàn bộ semantic core đã freeze, tôi đề xuất thiết kế nó theo hướng **compiler-first**, tức build system không tự tạo thêm một hệ thống dependency/graph song song với compiler mà tận dụng trực tiếp Query System + Module Graph + Cache của `axiomc`.

# XXXI — Axiom Build System + Package Manager v0.1

## 1. Triết lý

Axiom build system nên có 5 nguyên tắc:

1. **Manifest đơn giản**
2. **Dependency graph xác định**
3. **Incremental compilation thực sự**
4. **Parallel nhưng deterministic**
5. **Không để build system can thiệp vào semantics của Axiom**

Pipeline:

```text
axiom build
    │
    ├── Read Manifest
    ├── Resolve Packages
    ├── Load Lockfile
    ├── Build Package Graph
    ├── Build Module Graph
    │
    ├── Query Compiler
    │      ├── Source
    │      ├── HIR
    │      ├── Typed HIR
    │      ├── MIR
    │      ├── Verified MIR
    │      ├── LIR
    │      └── Object
    │
    ├── Parallel Compilation
    ├── Link
    └── Artifact
```

Điểm quan trọng:

> **Package Manager quản lý source. Compiler quản lý semantics. Linker quản lý binary.**

Không trộn ba tầng này.

---

# 2. Cấu trúc project

Một project Axiom tối thiểu:

```text
myapp/
├── axiom.toml
├── axiom.lock
├── src/
│   └── main.ax
└── build/
```

Library:

```text
mylib/
├── axiom.toml
├── src/
│   └── lib.ax
└── build/
```

Workspace:

```text
workspace/
├── axiom.toml
├── axiom.lock
├── packages/
│   ├── app/
│   │   ├── axiom.toml
│   │   └── src/
│   ├── core/
│   │   ├── axiom.toml
│   │   └── src/
│   └── graphics/
│       ├── axiom.toml
│       └── src/
└── build/
```

---

# 3. `axiom.toml`

Không nên biến manifest thành một ngôn ngữ lập trình.

Ví dụ:

```toml
[package]
name = "hello"
version = "0.1.0"
edition = "1"

[package]
type = "binary"

[dependencies]
math = "1.2"
graphics = { version = "2.0", features = ["vulkan"] }

[build]
entry = "main"

[profile.release]
optimization = "O3"
debug = false
strip = true
```

Nhưng tôi đề xuất **không dùng `[package]` hai lần**. Schema chính thức nên là:

```toml
[package]
name = "hello"
version = "0.1.0"
edition = "1"
kind = "binary"

[dependencies]
math = "1.2"
graphics = { version = "2.0", features = ["vulkan"] }

[build]
entry = "main"

[profile.release]
optimization = "O3"
debug = false
strip = true
```

Library:

```toml
[package]
name = "math"
version = "1.2.0"
edition = "1"
kind = "library"
```

---

# 4. Package Identity

Đây là phần rất quan trọng.

Không được coi:

```text
name = "foo"
```

là identity đầy đủ.

Package identity:

```text
PackageId =
    Registry
  + Name
  + Version
  + Source
  + ContentHash
```

Ví dụ:

```text
registry.example/foo@1.4.2
```

và:

```text
registry.example/foo@2.0.0
```

là **hai package identity khác nhau**.

Thậm chí:

```text
foo@1.4.2
```

từ registry A và:

```text
foo@1.4.2
```

từ git/local source cũng không được tự động coi là cùng package.

Điều này rất quan trọng đối với type identity.

---

# 5. Package version

v0.1 dùng semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Dependency:

```toml
foo = "1.4"
```

có nghĩa là một range, không phải chính xác `1.4.0`.

Nhưng:

```toml
foo = "=1.4.2"
```

là exact version.

Lockfile sẽ ghi version thực tế.

---

# 6. Lockfile

`axiom.lock` là **kết quả resolution**, không phải input semantic của package source.

Ví dụ:

```toml
version = 1

[[package]]
name = "foo"
version = "1.4.2"
source = "registry+https://..."
checksum = "..."

[[package]]
name = "bar"
version = "2.1.0"
source = "registry+https://..."
checksum = "..."

[package.dependencies]
foo = "1.4.2"
```

Lockfile phải đảm bảo:

```text
same manifest
+
same registry metadata
+
same lockfile
=
same dependency graph
```

Nếu lockfile tồn tại, build bình thường **không tự ý nâng version**.

Muốn cập nhật:

```bash
axiom update
```

---

# 7. Dependency Graph

Package graph:

```text
app
├── graphics
│   ├── math
│   └── image
└── network
    └── crypto
```

Package graph phải là DAG.

```text
A → B → C
```

hợp lệ.

Nhưng:

```text
A → B
B → A
```

bị từ chối ở package layer.

Điều này khác với module graph.

### Package graph

```text
A → B
```

phải acyclic.

### Module graph

Có thể có declaration cycle tùy semantic rules đã freeze.

```text
module a
module b
```

không đồng nghĩa package cycle.

---

# 8. Dependency loại gì?

v0.1 nên có:

```text
normal
dev
build
```

Ví dụ:

```toml
[dependencies]
math = "1"

[dev-dependencies]
testkit = "1"

[build-dependencies]
codegen = "2"
```

Ý nghĩa:

### normal

Cần để compile package.

### dev

Chỉ phục vụ test/benchmark/example.

### build

Chỉ phục vụ build-time tooling.

Nhưng có một nguyên tắc rất quan trọng:

> **Build dependency không được tự động trở thành runtime dependency.**

---

# 9. Không dùng build script kiểu tùy ý

Tôi không khuyến nghị cho v0.1:

```text
build.sh
build.py
build.js
```

được chạy tùy tiện.

Nó phá deterministic build rất nhanh.

Thay vào đó:

```text
comptime
```

được dùng cho compile-time computation.

Nếu thật sự cần build tool:

```text
kind = "build-tool"
```

và capability phải được khai báo.

Ví dụ:

```text
ReadSource
WriteGenerated
ExecuteTool
Filesystem
Environment
Network
```

Điều này kế thừa trực tiếp thiết kế `comptime` đã freeze.

---

# 10. Comptime và Build System

Tách rất rõ:

```text
comptime
    ↓
compiler semantic execution
```

trong khi:

```text
build tool
    ↓
build orchestration
```

Ví dụ:

```axiom
const TABLE = comptime generate_table();
```

là compiler concern.

Trong khi:

```bash
axiom build
```

là build-system concern.

Không được nhập nhằng hai thứ.

---

# 11. Features

Features rất hữu ích nhưng dễ trở thành nguồn chaos.

Axiom nên có:

```toml
[features]
default = ["std"]
graphics = []
vulkan = ["graphics"]
```

Dependency:

```toml
graphics = {
    version = "2",
    optional = true
}
```

Nhưng có invariant:

> **Feature không được thay đổi semantics của ngôn ngữ.**

Nó chỉ thay đổi:

```text
dependency graph
conditional compilation
available APIs
```

Không được làm:

```text
feature A → `+` có semantics khác
```

hoặc:

```text
feature A → ownership rules khác
```

---

# 12. Conditional compilation

Axiom nên có:

```axiom
@cfg(target_os = "linux")
fn linux_only() {
}
```

và:

```axiom
@cfg(target_arch = "x86_64")
```

Build system cung cấp configuration:

```text
target_os
target_arch
target_env
target_abi
target_vendor
debug
release
feature(...)
```

Quan trọng:

> Declaration bị `@cfg` loại bỏ thì **không tồn tại trong semantic module graph**.

Điều này đã phù hợp với thiết kế trước đó.

---

# 13. Build Profiles

MVP:

```text
dev
release
```

### dev

```text
-O0
debug info
incremental
assertions
```

### release

```text
-O3
debug info optional
strip optional
LTO optional
```

Sau này:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

được hỗ trợ trực tiếp.

Build profile không được thay đổi semantics.

---

# 14. Target Profile

Ví dụ:

```bash
axiom build --target x86_64-linux
```

Compiler nhận:

```text
TargetTriple
```

ví dụ:

```text
x86_64-unknown-linux
```

Target configuration:

```text
Architecture
OS
Environment
ABI
PointerWidth
Endianness
Features
ObjectFormat
Linker
```

Compiler frontend không được biết chi tiết ELF instruction encoding.

---

# 15. Cross compilation

Thiết kế ngay từ đầu:

```text
Host
  ↓
Axiom Build System
  ↓
Target Compiler
  ↓
Target Object
  ↓
Target Linker
  ↓
Target Binary
```

Ví dụ:

```bash
axiom build --target x86_64-linux
axiom build --target aarch64-linux
axiom build --target x86_64-windows
```

Không được giả định:

```text
host == target
```

---

# 16. Compiler cache

Đây là nơi Axiom có thể vượt qua build systems truyền thống về incremental compilation.

Ta đã có Query System:

```text
parse(FileId)
resolve(ModuleId)
hir(ItemId)
type(TypeQuery)
mir(FunctionId)
verified_mir(FunctionId)
abi(FunctionId)
object(ObjectQuery)
```

Build system **không nên tạo một dependency graph thứ hai cho từng semantic computation**.

Nó chỉ cần:

```text
Package Graph
      ↓
Module Graph
      ↓
Compiler Query System
```

Compiler tự biết:

```text
function A changed
→ Typed HIR A changed
→ MIR A changed
→ Object A changed
```

Nhưng:

```text
function B unchanged
```

thì không compile lại B.

---

# 17. Cache key

Ví dụ object cache key:

```text
ObjectKey =
    CompilerVersion
  + LanguageEdition
  + Target
  + Profile
  + FeatureSet
  + PackageId
  + ModuleSemanticHash
  + ABIConfig
```

Không dùng:

```text
filename + timestamp
```

làm semantic identity.

Timestamp chỉ là optimization hint.

---

# 18. Parallel compilation

Ví dụ:

```text
             ┌── math
             │
app ─────────┼── graphics
             │
             ├── image
             │
             └── network
```

Các node độc lập:

```text
math
graphics
image
network
```

có thể compile song song.

Nhưng output phải deterministic.

Do đó:

```text
parallel build
```

và:

```text
serial build
```

phải tạo semantic-equivalent artifacts.

Tốt hơn nữa:

```text
hash(parallel artifact)
=
hash(serial artifact)
```

khi môi trường giống nhau.

---

# 19. Không dùng filesystem order

Không bao giờ:

```text
readdir()
→ compile theo thứ tự filesystem
```

rồi để thứ tự đó ảnh hưởng binary.

Graph traversal phải canonical:

```text
PackageId
ModuleId
FunctionId
```

được sort theo stable semantic identity.

---

# 20. Artifact

Một package build có thể tạo:

```text
build/
└── x86_64-linux/
    └── release/
        ├── deps/
        ├── objects/
        ├── metadata/
        ├── lib/
        └── bin/
```

Ví dụ:

```text
objects/foo.axo
lib/libfoo.axlib
bin/app
```

`axo` có thể là object format riêng của Axiom nếu cần metadata.

Nhưng **không bắt buộc**.

Compiler có thể output:

```text
.o
```

ngay từ đầu để tương tác với linker.

---

# 21. Axiom Interface Artifact

Đây là một điểm tôi nghĩ Axiom nên có ngay từ v0.1.

Khi package A dùng package B, A không nhất thiết phải đọc toàn bộ source của B.

Compiler có thể sinh:

```text
Axiom Interface
```

ví dụ:

```text
foo.axi
```

chứa:

```text
public types
public functions
public traits
public impls
associated types
ABI information
visibility
semantic API fingerprint
```

Không chứa implementation cần thiết cho client compile.

Pipeline:

```text
foo.ax
   ↓
foo.axi
foo.o
```

Consumer:

```text
bar.ax
   ↓
reads foo.axi
   ↓
compile bar
```

Điều này rất có giá trị cho:

- incremental compilation
- IDE
- AI tooling
- distributed compilation
- binary packages

---

# 22. Semantic API Fingerprint

Mỗi package/module public API có:

```text
ApiFingerprint
```

được tính từ:

```text
public types
public signatures
public trait obligations
public associated types
public repr/ABI
public impls affecting coherence
```

Không tính:

```text
private function body
private local variable
comments
formatting
```

Nếu:

```text
private implementation changed
```

thì downstream package **không cần compile lại**, nếu interface fingerprint không đổi.

Đây là nền tảng incremental compilation rất mạnh.

---

# 23. Public trait impl

Một thay đổi tưởng nhỏ:

```axiom
impl Display for Foo
```

có thể ảnh hưởng method/trait resolution ở package khác.

Do đó public impl phải nằm trong API fingerprint.

Đây là lý do trước đây chúng ta đã quy định:

> public trait implementations affect semantic API fingerprint.

---

# 24. Registry

Registry v0.1 không cần quá phức tạp.

Logical model:

```text
Registry
├── Package Index
├── Versions
├── Metadata
└── Package Archives
```

Ví dụ:

```text
math
 ├── 1.0.0
 ├── 1.1.0
 └── 2.0.0
```

Registry metadata:

```text
name
version
dependencies
features
checksum
source
license
```

Package archive có content hash.

---

# 25. Không tin registry

Package Manager phải coi package bên ngoài là **untrusted input**.

Kiểm tra:

```text
checksum
archive structure
manifest
package identity
dependency metadata
```

Không chạy code chỉ để resolve dependency.

Resolution phải là data-only.

---

# 26. Offline mode

Phải có:

```bash
axiom build --offline
```

Nếu package không có local cache:

```text
AXPKG_NET_0001
```

Không được tự động truy cập Internet.

---

# 27. Vendor

Cho deployment/reproducible builds:

```bash
axiom vendor
```

tạo:

```text
vendor/
├── foo/
├── bar/
└── ...
```

Sau đó:

```toml
[source]
mode = "vendor"
```

Build hoàn toàn offline.

---

# 28. Supply-chain security

Ngay từ đầu nên có:

```text
Package checksum
Lockfile checksum
Source hash
Registry identity
```

Sau này có thể thêm:

```text
signature
trusted registry
publisher identity
SBOM
provenance
```

Nhưng **không đưa chữ ký/package trust vào semantic language core**.

---

# 29. Native linker integration

Build system gọi:

```text
compiler
   ↓
.o
   ↓
axiom-link
   ↓
executable
```

Ví dụ:

```bash
axiom build
```

không cần người dùng biết:

```bash
axiomc ...
axiom-link ...
```

Driver orchestration:

```text
axiom
├── check
├── build
├── run
├── test
├── clean
├── update
├── vendor
├── package
└── publish
```

---

# 30. `axiom check`

Không tạo object:

```bash
axiom check
```

Pipeline:

```text
Source
→ Parse
→ Resolve
→ Type
→ Ownership
→ Capability
→ MIR
→ Verify
```

Dừng trước codegen.

---

# 31. `axiom build`

```text
check
→ optimize
→ LIR
→ backend
→ object
→ link
```

---

# 32. `axiom run`

```text
build
→ execute artifact
```

Không tự động rebuild nếu cache còn hợp lệ.

---

# 33. `axiom test`

Tận dụng Harness đã thiết kế:

```text
axiom test
```

có thể chạy:

```text
unit
conformance
negative
oracle
backend
```

Nhưng package-level test mặc định chỉ nên chạy:

```text
unit + integration
```

Các test compiler/harness là developer tooling.

---

# 34. Build Manifest không được trở thành DSL

Tôi muốn freeze nguyên tắc này:

**Không cho phép:**

```toml
command = "..."
script = "..."
eval = "..."
```

ở core manifest.

Manifest chỉ mô tả:

```text
WHAT
```

không mô tả:

```text
HOW
```

Build orchestration thuộc `axiom` driver.

Điều này giúp Axiom tránh rơi vào tình trạng:

```text
CMake
→ shell
→ Python
→ custom generator
→ compiler
→ linker
```

một project có 7 tầng build logic.

---

# 35. Workspace

Workspace root:

```toml
[workspace]
members = [
    "packages/app",
    "packages/core",
    "packages/graphics"
]
```

Workspace dùng chung:

```text
lockfile
target directory
package graph
cache
configuration
```

Nhưng mỗi package vẫn có identity riêng.

---

# 36. Dependency graph + query graph

Đây là kiến trúc quan trọng nhất:

```text
             Package Graph
                   │
             Module Graph
                   │
             Query Graph
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
       HIR       Typed       MIR
                  HIR
                   │
              Verified MIR
                   │
                 LIR
                   │
                Object
```

**Không được merge tất cả thành một graph khổng lồ.**

Mỗi graph có một trách nhiệm.

---

# 37. Build correctness

Build system phải đảm bảo:

```text
BUILD-20
same inputs → same dependency graph

BUILD-21
same semantic inputs → same compiler queries

BUILD-22
parallel build = serial semantics

BUILD-23
cache hit = fresh compilation semantics

BUILD-24
incremental compilation = clean compilation semantics

BUILD-25
profile does not alter language semantics

BUILD-26
features do not alter core language semantics

BUILD-27
target configuration is explicit

BUILD-28
lockfile pins dependency resolution

BUILD-29
checksum identifies package content

BUILD-30
offline mode performs no network access

BUILD-31
build scripts cannot silently alter compiler semantics

BUILD-32
private implementation changes need not invalidate unchanged API

BUILD-33
public API fingerprint changes invalidate dependents when required

BUILD-34
filesystem ordering cannot affect semantic result

BUILD-35
build system does not perform type/ownership semantics
```

---

# 38. Build diagnostics

Namespace:

```text
AXBUILD_*
AXPKG_*
AXLOCK_*
AXREG_*
```

Ví dụ:

```text
AXPKG_0001 package not found
AXPKG_0002 version conflict
AXPKG_0003 invalid manifest
AXPKG_0004 dependency cycle
AXPKG_0005 checksum mismatch

AXLOCK_0001 lockfile invalid
AXLOCK_0002 lockfile out of date

AXBUILD_0001 target not supported
AXBUILD_0002 artifact collision
AXBUILD_0003 cache corruption
AXBUILD_0004 deterministic build violation

AXREG_0001 registry unavailable
AXREG_0002 package checksum mismatch
```

Diagnostics vẫn theo schema JSON chung đã freeze.

---

# 39. Repository

Tôi đề xuất cập nhật:

```text
axiom/
├── build/
│   ├── manifest/
│   ├── package/
│   ├── workspace/
│   ├── resolver/
│   ├── lockfile/
│   ├── graph/
│   ├── profile/
│   ├── target/
│   ├── cache/
│   ├── scheduler/
│   ├── artifact/
│   ├── registry/
│   ├── vendor/
│   └── diagnostics/
│
├── compiler/
├── linker/
├── oracle/
├── runtime/
├── std/
├── tests/
├── tools/
└── bootstrap/
```

Executable:

```text
axiom
```

là frontend driver.

Internal:

```text
axiomc
axiom-link
```

có thể tồn tại trong development, nhưng user-facing CLI chỉ cần:

```text
axiom
```

---

# 40. Build System v0.1 Milestones

Tôi sẽ chia thành:

```text
BUILD-001 Manifest parser
BUILD-002 Package identity
BUILD-003 Local package
BUILD-004 Module discovery
BUILD-005 Package graph
BUILD-006 Dependency resolution
BUILD-007 Lockfile
BUILD-008 Compiler integration
BUILD-009 Incremental query cache
BUILD-010 Parallel compilation
BUILD-011 Deterministic scheduling
BUILD-012 Build profiles
BUILD-013 Target profiles
BUILD-014 Features
BUILD-015 Workspace
BUILD-016 Artifact manager
BUILD-017 Axiom linker integration
BUILD-018 Offline cache
BUILD-019 Vendor
BUILD-020 Registry client
BUILD-021 Checksums
BUILD-022 API fingerprint
BUILD-023 Interface artifact
BUILD-024 Cross compilation
BUILD-025 Reproducible build
BUILD-026 Build diagnostics
BUILD-027 Harness integration
BUILD-028 Bootstrap integration
```

---

# 41. Vertical slice quan trọng nhất

Không nên xây package manager hoàn chỉnh trước khi có executable.

Slice đầu tiên:

```text
hello/
├── axiom.toml
└── src/
    └── main.ax
```

```bash
axiom build
```

phải thực hiện:

```text
Manifest
 ↓
Package
 ↓
Module
 ↓
Parser
 ↓
Type
 ↓
Ownership
 ↓
MIR
 ↓
Verified MIR
 ↓
LIR
 ↓
x86-64
 ↓
ELF .o
 ↓
axiom-link
 ↓
ELF executable
```

Sau đó:

```bash
./build/.../hello
```

chạy được.

Đây mới là **BUILD-001 thực sự có giá trị**.

---

# 42. Một quyết định kiến trúc tôi muốn freeze

Axiom Build System **không phải Cargo clone**.

Kiến trúc đặc trưng của Axiom sẽ là:

```text
                    AXIOM
                      │
        ┌─────────────┴─────────────┐
        │                           │
 Package Graph                Query Graph
        │                           │
        │                  fine-grained incremental
        │                           │
        └──────────────┬────────────┘
                       ↓
                Semantic API
                  Fingerprint
                       ↓
                  LIR / Object
                       ↓
                 Axiom Linker
```

Điều này cho phép một thay đổi nhỏ:

```text
fn foo() { ... }
```

không nhất thiết dẫn tới:

```text
compile entire package
```

mà có thể chỉ:

```text
foo
 ↓
MIR(foo)
 ↓
object(foo)
```

Trong khi package phụ thuộc chỉ bị rebuild nếu **API fingerprint** thay đổi.

Đây là một trong những nơi Axiom có thể đạt được build time rất tốt mà **không cần hy sinh tính đơn giản của ngôn ngữ**.

---

## Bước tiếp theo: Standard Library v0.1

Sau Build System, không nên nhảy ngay vào hàng trăm API stdlib. Bước hợp lý tiếp theo là thiết kế **Axiom Standard Library Architecture** trước, đặc biệt:

```text
Core
 ├── primitive types
 ├── Option
 ├── Result
 ├── Array
 ├── Slice/View
 ├── Text/Bytes
 ├── Iterator
 ├── Box
 ├── Vec
 ├── String
 ├── HashMap
 └── basic traits

Platform
 ├── OS
 ├── File
 ├── Socket
 ├── Process
 ├── Thread
 ├── Sync
 └── Time

Runtime-optional
 ├── Async
 ├── Executor
 ├── Networking
 └── Reflection

Graphics/Compute
 ├── GPU
 ├── Tensor
 └── SIMD
```

Đặc biệt cần giải quyết một vấn đề rất quan trọng trước khi viết stdlib: **Axiom Core/Std nên dùng ownership + `view` + `mut_view` như thế nào để API vừa cực kỳ dễ dùng vừa không biến thành Rust thứ hai.** Đây sẽ là phép thử thực tế đầu tiên cho toàn bộ memory model đã thiết kế.