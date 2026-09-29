# BOOTSTRAP-432 — MODULE SYSTEM, PACKAGE MODEL, NAMESPACE, DEPENDENCY GRAPH & BUILD SEMANTICS

Task này khóa kiến trúc **project/build system** của Axiom. Mục tiêu là project nhỏ có thể chỉ cần compiler, còn project lớn có module/package/dependency/incremental build đầy đủ mà không biến build system thành một hệ thống quá phức tạp.

---

## 432.1 — Mục tiêu

Axiom phải phân biệt rõ:

```text
File
  ↓
Module
  ↓
Package
  ↓
Workspace
  ↓
Build
  ↓
Artifact
```

Trong đó:

- **File** — đơn vị lưu trữ vật lý.
- **Module** — đơn vị namespace/compilation.
- **Package** — đơn vị phân phối và dependency.
- **Workspace** — tập hợp nhiều package cùng phát triển.
- **Build** — một lần tạo artifact với configuration cụ thể.
- **Artifact** — executable/library/object/package output.

---

# 432.2 — Không phụ thuộc package manager bên thứ ba

Axiom compiler phải hiểu trực tiếp:

```text
axiom.toml
```

hoặc format tương đương của Axiom.

Không yêu cầu:

```text
npm
cargo
maven
gradle
cmake
conan
vcpkg
```

để compile một Axiom project.

---

# 432.3 — Compiler và build tool

Nên tách:

```text
axiom
```

thành compiler/build driver thống nhất.

Ví dụ:

```text
axiom build
axiom run
axiom test
axiom check
axiom clean
axiom package
```

Compiler backend bên dưới vẫn có thể được gọi độc lập.

---

# 432.4 — Project tối thiểu

Project nhỏ nhất:

```text
hello.ax
```

có thể compile trực tiếp:

```text
axiom hello.ax
```

Không bắt buộc tạo project manifest.

---

# 432.5 — Project có manifest

Project lớn:

```text
myapp/
    axiom.toml
    src/
        main.ax
        math.ax
```

---

# 432.6 — Manifest

Manifest mô tả:

```text
name
version
edition
targets
dependencies
features
build profiles
```

Ví dụ:

```toml
[package]
name = "myapp"
version = "1.0.0"
edition = "axiom1"

[dependencies]
math = "1.2"

[build]
entry = "src/main.ax"
```

Syntax TOML chỉ là ví dụ; format chính thức có thể được khóa sau.

---

# 432.7 — Package identity

Package identity:

```text
name + version + source identity
```

Không dùng tên package đơn độc để xác định dependency.

---

# 432.8 — Package version

Axiom sử dụng semantic versioning-compatible model:

```text
MAJOR.MINOR.PATCH
```

nhưng compiler không bắt buộc dependency phải dùng range nếu project muốn pin chính xác.

---

# 432.9 — Exact dependency pinning

Có thể:

```toml
math = "=1.2.3"
```

để reproducible build.

---

# 432.10 — Dependency source

Dependency có thể đến từ:

```text
local path
package registry
git repository
archive
system package
```

nhưng core compiler chỉ cần hiểu package identity + resolved source.

---

# 432.11 — Registry không thuộc compiler core

Registry là infrastructure.

Compiler không cần phụ thuộc vào một server cụ thể.

Có thể sử dụng:

```text
private registry
public registry
local cache
offline mirror
```

---

# 432.12 — Dependency lockfile

Build reproducibility dùng:

```text
axiom.lock
```

Lockfile chứa dependency graph đã resolve.

---

# 432.13 — Lockfile

Ví dụ conceptual:

```text
package A 1.2.3
    hash = ...

package B 4.0.1
    hash = ...
```

Hash xác nhận nội dung package.

---

# 432.14 — Content-addressed package cache

Package cache có thể:

```text
~/.axiom/cache/
    sha256/...
```

Dependency được nhận diện bằng content hash.

---

# 432.15 — Offline build

Nếu dependency đã có trong cache:

```text
axiom build --offline
```

không cần network.

---

# 432.16 — Source dependency verification

Compiler/build driver phải verify:

```text
declared version
resolved version
content hash
```

trước compilation.

---

# 432.17 — Module declaration

Một module có thể tương ứng file:

```text
math.ax
```

hoặc directory module:

```text
math/
    mod.ax
    vector.ax
```

---

# 432.18 — Explicit module declaration

Có thể dùng:

```text
module math
```

nhưng compiler cũng có thể derive module identity từ project layout.

Mục tiêu là tránh boilerplate.

---

# 432.19 — Import

Ví dụ:

```text
import math
```

hoặc:

```text
import math.Vector
```

---

# 432.20 — Selective import

```text
import math.{Vector, Matrix}
```

---

# 432.21 — Alias import

```text
import math.Vector as Vec
```

---

# 432.22 — Wildcard import

Không khuyến khích wildcard:

```text
import math.*
```

Nhưng có thể hỗ trợ.

Formatter/compiler tooling nên ưu tiên explicit imports.

---

# 432.23 — Namespace

Tên đầy đủ:

```text
myapp.math.Vector
```

Namespace được xác định từ package/module hierarchy.

---

# 432.24 — Declaration path

Một declaration có canonical path:

```text
package::module::submodule::Name
```

Ví dụ:

```text
myapp::math::Vector
```

---

# 432.25 — `pub`

Visibility cơ bản:

```text
pub fn add(...)
```

Không có `pub`:

```text
fn helper(...)
```

chỉ visible trong module theo rule visibility.

---

# 432.26 — Module-private mặc định

Axiom chọn:

> **private by default**

Điều này giảm accidental API exposure.

---

# 432.27 — Package visibility

Có thể cần:

```text
pub(package)
```

cho declaration chỉ public trong package.

---

# 432.28 — Module visibility

Có thể:

```text
pub(module)
```

nhưng vì module-private là default, syntax này chỉ cần nếu override một visibility context.

---

# 432.29 — Explicit public API

Package library nên expose một API surface rõ ràng:

```text
pub struct Vec2
pub fn normalize(...)
```

Compiler có thể xuất API metadata.

---

# 432.30 — No textual inclusion

Axiom không sử dụng:

```text
#include
```

như C.

Import là semantic dependency.

---

# 432.31 — Import không copy source

```text
import math
```

không có nghĩa copy text `math.ax` vào file hiện tại.

Compiler resolve module graph.

---

# 432.32 — Dependency graph

Compiler xây:

```text
Module A
 ├── Module B
 ├── Module C
 │    └── Module D
 └── Module E
```

---

# 432.33 — Graph node

Mỗi node chứa:

```text
package
module
source hash
compiler options
target
dependency interface hashes
```

---

# 432.34 — Incremental compilation

Nếu:

```text
A → B
```

và B thay đổi implementation nhưng **public semantic interface không đổi**:

A không nhất thiết phải recompile.

---

# 432.35 — Interface hash

Compiler tạo:

```text
API/interface hash
```

từ:

```text
public types
public functions
public constants
traits
ABI-relevant attributes
generic contracts
```

---

# 432.36 — Implementation hash

Đồng thời có:

```text
implementation hash
```

đại diện cho body/private implementation.

---

# 432.37 — Dependency invalidation

Nếu chỉ:

```text
private fn helper()
```

thay đổi:

```text
implementation hash changes
interface hash unchanged
```

dependent module không cần semantic re-check.

---

# 432.38 — Public API change

Nếu:

```text
pub struct User {
    ...
}
```

thay đổi layout/API:

```text
interface hash changes
```

dependent modules phải recompile/re-check theo ABI rules.

---

# 432.39 — Generic dependency

Generic code đặc biệt:

```text
fn foo<T: Trait>(...)
```

có thể phụ thuộc semantic definition của:

```text
Trait
T constraints
associated types
```

Interface hash phải bao phủ các dependency này.

---

# 432.40 — Monomorphization cache

Generic specialization:

```text
foo<i32>
foo<f64>
foo<MyStruct>
```

được cache riêng.

Key:

```text
generic definition hash
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

# 432.41 — Build cache

Axiom build cache có nhiều tầng:

```text
source cache
semantic cache
comptime cache
generic specialization cache
IR cache
object cache
link cache
```

---

# 432.42 — Cache correctness

Cache hit chỉ hợp lệ khi mọi input ảnh hưởng semantics vẫn giống nhau.

Không dùng timestamp đơn thuần để quyết định cache validity.

---

# 432.43 — Compiler version

Cache key phải chứa compiler identity:

```text
compiler_version
compiler_build_hash
```

---

# 432.44 — Target configuration

Cache phân biệt:

```text
x86_64-linux
x86_64-windows
aarch64-linux
aarch64-macos
...
```

---

# 432.45 — Optimization profile

Cache phải phân biệt:

```text
debug
release
size
speed
```

và các optimization flags ảnh hưởng code generation.

---

# 432.46 — Build profiles

V0:

```text
debug
release
```

Built-in.

Có thể thêm:

```text
size
release-fast
```

sau này.

---

# 432.47 — Debug build

Debug ưu tiên:

```text
fast compilation
debug information
minimal optimization
```

---

# 432.48 — Release build

Release ưu tiên:

```text
optimization
dead-code elimination
inlining
constant propagation
LTO where enabled
```

---

# 432.49 — Size optimization

Profile:

```text
size
```

có thể bật:

```text
function merging
outlining
aggressive dead stripping
smaller runtime structures
```

---

# 432.50 — Link-time optimization

Axiom linker đã được định nghĩa ở BOOTSTRAP-420.

Có thể:

```text
axiom build --lto
```

IR/object information được giữ đủ để linker/compiler thực hiện cross-module optimization.

---

# 432.51 — Module boundary không nhất thiết là optimization boundary

Compiler có thể inline xuyên module khi:

```text
public implementation metadata
```

được available.

---

# 432.52 — Library package

Package có thể build:

```text
static library
dynamic library
```

hoặc:

```text
executable
```

---

# 432.53 — Package targets

Manifest có thể định nghĩa:

```text
[[bin]]
name = "app"
entry = "src/main.ax"

[lib]
name = "core"
```

---

# 432.54 — Multiple binaries

Một package có thể có:

```text
app
tool
server
benchmark
```

---

# 432.55 — Test targets

Test source có thể:

```text
tests/
    math_test.ax
```

Compiler build thành test executable riêng.

Không cần runtime test framework bắt buộc.

---

# 432.56 — Benchmark targets

Tương tự:

```text
bench/
```

là tooling layer.

---

# 432.57 — Example targets

Có thể:

```text
examples/
```

nhưng chỉ build khi yêu cầu.

---

# 432.58 — Build scripts

Một package có thể cần native integration.

Không đưa arbitrary build script vào comptime language.

Thay vào đó:

```text
build tool phase
```

có sandbox/permission riêng.

---

# 432.59 — Build script isolation

Build script không được mặc định có quyền:

```text
modify arbitrary source
network
execute arbitrary command
```

Các quyền phải explicit.

---

# 432.60 — Build script vs comptime

Ranh giới:

```text
comptime
    = language-level deterministic computation

build script
    = project/environment orchestration
```

---

# 432.61 — Dependency cycle

Module cycle:

```text
A → B
B → A
```

không được phép nếu dependency là value-level compilation dependency.

---

# 432.62 — Type-only cycles

Một số cycle type declaration có thể được cho phép:

```text
A type → B type
B type → A type
```

nếu compiler có thể resolve declaration graph mà không yêu cầu hoàn thành definition trước.

---

# 432.63 — Value initialization cycle

Không cho:

```text
const A = B
const B = A
```

→ diagnostic rõ ràng.

---

# 432.64 — Function recursion

Function recursion **không phải module dependency cycle error**.

```text
fn a() { b() }
fn b() { a() }
```

hợp lệ nếu declarations đã resolve.

---

# 432.65 — Initialization order

Không dựa vào thứ tự file.

Static initialization phải có semantics deterministic.

---

# 432.66 — Static initialization

Ưu tiên:

```text
compile-time initialized data
```

thay vì runtime constructors.

---

# 432.67 — Runtime initialization graph

Nếu runtime initialization bắt buộc:

```text
init A
 ↓
init B
```

compiler phải tạo dependency graph rõ ràng.

Không cho initialization order phụ thuộc filesystem order.

---

# 432.68 — Entry point

Executable mặc định tìm:

```text
fn main()
```

hoặc:

```text
fn main() -> i32
```

---

# 432.69 — Entry point variants

Compiler có thể hỗ trợ:

```text
@entry
fn main(...)
```

cho embedded/freestanding targets.

---

# 432.70 — Freestanding package

Có thể build:

```text
no_std-like
```

nhưng không cần copy Rust terminology.

Ví dụ:

```text
[profile]
runtime = "none"
```

---

# 432.71 — Runtime layers

Axiom runtime được chia:

```text
language core
    ↓
platform runtime
    ↓
standard library
    ↓
application
```

Compiler không bắt buộc runtime cho mọi binary.

---

# 432.72 — Minimal executable

Một chương trình:

```text
fn main() {}
```

có thể emit binary mà không link toàn bộ standard library.

---

# 432.73 — Standard library dependency

Standard library là package/system component do Axiom ecosystem cung cấp.

Compiler core chỉ cần những intrinsic thực sự thuộc language/ABI.

---

# 432.74 — Platform library

OS integration:

```text
Windows
Linux
macOS
Android
iOS
```

được cung cấp bởi platform packages/runtime layers.

---

# 432.75 — System ABI dependency

Axiom compiler vẫn có thể link:

```text
kernel32
libc
system frameworks
```

khi target yêu cầu.

Điều này **không vi phạm** nguyên tắc compiler không phụ thuộc compiler bên thứ ba.

---

# 432.76 — Native library interoperability

Package có thể khai báo:

```text
extern "c"
```

và link:

```text
.a
.lib
.so
.dll
.dylib
framework
```

theo ABI 421.

---

# 432.77 — External dependency declaration

Ví dụ conceptual:

```toml
[native]
libraries = ["m"]
```

Compiler linker resolve native library theo target.

---

# 432.78 — Cross compilation

Build command:

```text
axiom build --target aarch64-linux
```

Compiler pipeline:

```text
source
 ↓
target-independent semantic analysis
 ↓
target configuration
 ↓
target ABI
 ↓
target code generation
 ↓
target linker
```

---

# 432.79 — Target specification

Target được xác định bởi:

```text
architecture
OS
ABI
object format
pointer width
endianness
CPU features
runtime
linker model
```

---

# 432.80 — Target-independent modules

Semantic analysis càng nhiều càng tốt được thực hiện target-independent.

---

# 432.81 — Conditional compilation

Dùng comptime system 431:

```text
comptime if target.os == "windows" {
    ...
}
```

---

# 432.82 — Feature flags

Package có thể khai báo:

```toml
[features]
simd = []
gpu = []
gui = []
```

---

# 432.83 — Feature resolution

Features là compile configuration.

Chúng không nên trở thành runtime global variables.

---

# 432.84 — Optional dependency

Một dependency có thể được bật theo feature.

---

# 432.85 — Dependency graph with features

Graph thực tế:

```text
package
    ↓
version
    ↓
features
    ↓
resolved dependencies
```

Cache key phải bao gồm feature configuration.

---

# 432.86 — Workspace

Workspace:

```text
workspace/
    axiom.toml
    packages/
        core/
        compiler/
        app/
```

---

# 432.87 — Shared workspace dependency

Package trong workspace có thể reference:

```text
path = "../core"
```

---

# 432.88 — Workspace build

```text
axiom build --workspace
```

compiler có thể chia sẻ:

```text
dependency resolution
cache
comptime cache
generic cache
```

---

# 432.89 — Workspace cycle

Package dependency cycle mặc định không được phép:

```text
A → B → A
```

---

# 432.90 — Build graph

Build system tạo DAG:

```text
       core
      /    \
   math    io
      \    /
       app
```

Các node độc lập có thể compile song song.

---

# 432.91 — Parallel compilation

Compiler được phép parallelize independent modules.

Kết quả phải deterministic.

---

# 432.92 — Deterministic module order

Nếu nhiều module compile song song:

```text
artifact result
```

không được phụ thuộc thread scheduling.

---

# 432.93 — Module interface artifact

Compiler có thể sinh:

```text
.mod
```

chứa semantic interface.

Nó không phải source code copy.

---

# 432.94 — Module metadata

Interface artifact có thể chứa:

```text
public declarations
types
traits
generic definitions
ABI metadata
comptime metadata
source mapping
semantic hash
```

---

# 432.95 — Private information

Private implementation không cần nằm trong public interface artifact.

Điều này giảm dependency invalidation.

---

# 432.96 — Generic library distribution

Library có generic code cần phân phối đủ information để downstream compiler instantiate.

Có hai chiến lược:

```text
source package
```

hoặc:

```text
generic IR/module artifact
```

Axiom hỗ trợ cả hai về mặt kiến trúc.

---

# 432.97 — Precompiled module

Compiler có thể consume:

```text
.axiommod
```

thay vì parse source lại.

---

# 432.98 — Precompiled module validity

Module artifact chỉ hợp lệ khi match:

```text
compiler compatibility
language edition
target
ABI
semantic dependencies
```

---

# 432.99 — ABI stability

Không mặc định hứa ABI ổn định giữa compiler versions.

Nếu package muốn stable external ABI:

```text
@repr(C)
extern "c"
```

vẫn là boundary chính.

---

# 432.100 — Package API versioning

Package versioning và language ABI versioning là hai vấn đề riêng.

---

# 432.101 — Edition

Axiom có thể có:

```text
edition = "axiom1"
```

Edition cho phép thay đổi syntax/semantic defaults mà không phá project cũ.

---

# 432.102 — Compiler compatibility

Compiler mới có thể compile edition cũ.

Compiler không được âm thầm đổi semantics của edition cũ.

---

# 432.103 — Namespace collision

Hai package có cùng module name:

```text
foo::math
bar::math
```

không xung đột vì package identity khác.

---

# 432.104 — Import ambiguity

Nếu:

```text
import foo.Math
import bar.Math
```

và gọi:

```text
Math.add()
```

→ compiler báo ambiguity.

Phải alias:

```text
import foo.Math as FooMath
import bar.Math as BarMath
```

---

# 432.105 — Import cycle diagnostics

Compiler phải hiển thị cycle:

```text
E432201 MODULE_CYCLE

A
 ↓
B
 ↓
C
 ↓
A
```

---

# 432.106 — Unused imports

Compiler warning:

```text
W432001 UNUSED_IMPORT
```

Formatter/IDE có thể tự remove.

---

# 432.107 — Public re-export

Có thể:

```text
pub import math.Vector
```

để expose:

```text
myapp::Vector
```

---

# 432.108 — Prelude

Axiom có thể có prelude tối thiểu.

Nhưng không nên implicit import quá nhiều API.

Mục tiêu:

```text
language primitives
Option
Result
basic traits
```

---

# 432.109 — Explicit standard library import

Các API lớn:

```text
io
fs
net
thread
async
graphics
```

không tự động đưa vào namespace.

---

# 432.110 — Package metadata

Package có thể chứa:

```text
description
license
authors
repository
documentation
keywords
```

Đây là distribution metadata, không ảnh hưởng semantics.

---

# 432.111 — Build metadata isolation

Build metadata không được tự động trở thành language constant.

Muốn đưa vào code:

```text
comptime configuration
```

phải explicit.

---

# 432.112 — Environment profiles

Có thể:

```text
debug
release
test
bench
```

nhưng compiler semantics vẫn deterministic.

---

# 432.113 — Test isolation

Test build có thể bật:

```text
test feature
```

nhưng production build không tự động mang test code.

---

# 432.114 — Dead package elimination

Dependency không được sử dụng có thể được loại khỏi final artifact.

Ở module level và object level.

---

# 432.115 — Static library extraction

Nếu package A phụ thuộc package B static library:

```text
linker
```

chỉ extract object sections thực sự cần.

Phù hợp với BOOTSTRAP-420.

---

# 432.116 — Dynamic library boundary

Dynamic library có explicit exported API.

Compiler không tự export toàn bộ `pub` declarations nếu package không yêu cầu.

---

# 432.117 — Export manifest

Có thể:

```toml
[exports]
functions = ["api_create", "api_destroy"]
```

để kiểm soát native ABI.

---

# 432.118 — Package capabilities

Về sau package có thể khai báo capability:

```text
requires:
    filesystem
    network
    gpu
```

nhưng đây là build/runtime metadata, không phải quyền ngầm.

---

# 432.119 — Source layout convention

Convention mặc định:

```text
src/
    main.ax
    lib.ax
    module.ax
```

Nhưng compiler không nên hard-code quá sâu.

---

# 432.120 — Canonical project

Một executable project:

```text
app/
├── axiom.toml
└── src/
    ├── main.ax
    ├── ui.ax
    └── model.ax
```

---

# 432.121 — Canonical library

```text
library/
├── axiom.toml
└── src/
    ├── lib.ax
    ├── vector.ax
    └── matrix.ax
```

---

# 432.122 — Package root

`lib.ax` là public package root.

Nó quyết định API nào được re-export.

---

# 432.123 — Main package root

Executable dùng:

```text
main.ax
```

làm entry module.

---

# 432.124 — Module tree

Ví dụ:

```text
lib.ax
math/
    vector.ax
    matrix.ax
```

semantic tree:

```text
package
└── math
    ├── vector
    └── matrix
```

---

# 432.125 — File-to-module mapping

Tên file không tạo type identity.

Module identity thuộc semantic package graph.

---

# 432.126 — Rename file safety

Đổi:

```text
vector.ax
```

thành:

```text
vec.ax
```

không nên thay đổi public semantic identity nếu module declaration explicit.

Nếu module identity derive từ path thì compiler tooling phải cập nhật imports tự động.

---

# 432.127 — Module declaration recommendation

Để ổn định lâu dài, Axiom nên cho phép:

```text
module math.vector
```

trong module root.

Path chỉ là default discovery mechanism.

---

# 432.128 — No textual macro imports

Không hỗ trợ kiểu:

```text
include("generated.ax")
```

như preprocessing.

Generated declaration phải đi qua module/generation system.

---

# 432.129 — Source generation

Build tool có thể generate source vào:

```text
generated/
```

nhưng generated source vẫn được compiler parse/type-check bình thường.

---

# 432.130 — Preferred generation

Khi có thể:

```text
comptime semantic generation
```

được ưu tiên hơn generated source files.

---

# 432.131 — Build graph invalidation

Thay đổi:

```text
source
```

→ source hash.

Thay đổi:

```text
dependency interface
```

→ dependent invalidation.

Thay đổi:

```text
compiler options
```

→ relevant cache invalidation.

---

# 432.132 — Minimal rebuild

Mục tiêu:

```text
edit private function
```

→ chỉ rebuild phần thực sự cần thiết.

Đây là một yêu cầu quan trọng cho Axiom vì compiler sẽ được dùng để phát triển compiler itself.

---

# 432.133 — Compiler self-hosting readiness

Build system phải hỗ trợ:

```text
Axiom compiler
    ↓
Axiom source
    ↓
Axiom compiler
```

và incremental rebuild nhanh.

---

# 432.134 — Bootstrap build stages

Có thể có:

```text
stage0
stage1
stage2
```

nhưng build system không nên yêu cầu stage metadata cho application thông thường.

---

# 432.135 — Compiler bootstrap verification

Compiler self-hosting có thể kiểm tra:

```text
stage1 output
==
stage2 output
```

hoặc semantic-equivalent reproducibility.

---

# 432.136 — Artifact naming

Target artifacts phải deterministic:

```text
app.exe
libfoo.a
libfoo.so
libfoo.dylib
app.wasm
```

---

# 432.137 — Build output tree

Convention:

```text
build/
    debug/
    release/
        target/
            package/
                artifacts
```

Exact layout là tooling detail, không phải language semantic.

---

# 432.138 — Dependency source integrity

Nếu dependency hash mismatch:

```text
E432401 DEPENDENCY_HASH_MISMATCH
```

không silently compile.

---

# 432.139 — Lockfile update

Dependency resolution thay đổi phải explicit:

```text
axiom update
```

hoặc:

```text
axiom lock
```

Build thông thường không tự ý đổi lockfile.

---

# 432.140 — Reproducible dependency resolution

Lockfile giúp:

```text
machine A
machine B
CI
```

resolve cùng dependency graph.

---

# 432.141 — Build fingerprint

Một build fingerprint có thể chứa:

```text
source root hash
dependency graph hash
compiler hash
target hash
profile hash
feature hash
```

---

# 432.142 — Artifact fingerprint

Final executable có thể chứa optional build ID.

Nếu reproducibility được yêu cầu, metadata không deterministic phải được loại bỏ hoặc explicit.

---

# 432.143 — Debug information

Debug info không ảnh hưởng semantic artifact.

Compiler có thể emit:

```text
DWARF
PDB
```

tùy target/platform.

---

# 432.144 — Source map

Comptime/generated code phải map được về source.

Điều này đặc biệt quan trọng với AI-generated code.

---

# 432.145 — AI project metadata

Module artifact có thể chứa machine-readable:

```text
symbol
type
visibility
documentation
source location
semantic hash
dependencies
generated origin
```

AI tooling có thể query thay vì parse toàn bộ source.

---

# 432.146 — Language server integration

Build graph cung cấp cho IDE/LSP:

```text
module dependencies
symbols
types
references
diagnostics
```

---

# 432.147 — Fast `check`

```text
axiom check
```

chỉ cần:

```text
parse
resolve
type-check
ownership-check
comptime validation
```

không emit/link binary.

---

# 432.148 — Fast `build`

```text
axiom build
```

tận dụng mọi cache.

---

# 432.149 — `run`

```text
axiom run
```

tương đương:

```text
build
+
execute
```

---

# 432.150 — `clean`

```text
axiom clean
```

xóa build artifacts nhưng **không nhất thiết xóa global dependency cache**.

---

# 432.151 — `cache clean`

Tách:

```text
axiom cache clean
```

để xóa compiler cache.

---

# 432.152 — Build daemon

Không bắt buộc daemon.

Sau này có thể:

```text
axiomd
```

để giữ compiler process trong memory và giảm startup cost.

Nhưng compiler phải hoạt động chính xác khi chạy one-shot.

---

# 432.153 — Compiler server

IDE có thể giữ:

```text
AST
semantic graph
module cache
```

trong memory.

Đây là optimization, không phải semantic requirement.

---

# 432.154 — Build parallelism

CLI:

```text
axiom build -j 8
```

hoặc auto-detect CPU.

---

# 432.155 — Deterministic parallel build

Thứ tự hoàn thành task không được ảnh hưởng:

```text
symbol resolution
artifact content
semantic result
```

---

# 432.156 — Build failure aggregation

Independent modules có thể compile song song.

Compiler có thể report nhiều diagnostics thay vì dừng ngay ở module đầu tiên.

---

# 432.157 — Error recovery

Parser 429 và build system phải hỗ trợ tiếp tục semantic analysis sau lỗi không nghiêm trọng.

Mục tiêu là diagnostic hữu ích cho cả IDE và AI.

---

# 432.158 — Dependency feature conflicts

Nếu hai dependencies yêu cầu incompatible configuration:

```text
E432501 FEATURE_CONFLICT
```

compiler/build resolver không tự chọn một bên.

---

# 432.159 — Multiple versions

Axiom có thể cho phép:

```text
app
 ├── foo 1.x
 └── bar
      └── foo 2.x
```

nếu chúng có package identities/version contexts khác nhau.

Không merge mù quáng.

---

# 432.160 — Type identity across package versions

```text
foo@1::User
```

và:

```text
foo@2::User
```

là hai nominal types khác nhau.

---

# 432.161 — Dependency alias

Có thể:

```toml
oldfoo = { package = "foo", version = "1.2" }
```

để tránh namespace ambiguity.

---

# 432.162 — Local development override

Workspace có thể override dependency bằng local path.

Override phải hiện rõ trong resolved graph.

---

# 432.163 — Vendor mode

Axiom có thể hỗ trợ:

```text
axiom vendor
```

để copy dependency sources vào project.

Sau đó build offline hoàn toàn.

---

# 432.164 — No hidden downloads

`axiom build` không được tự ý download dependency nếu project policy không cho phép.

Có thể có explicit:

```text
axiom fetch
```

---

# 432.165 — Security boundary

Package compilation không được tự động execute arbitrary package code chỉ vì package được dependency.

Comptime vẫn sandboxed.

Build scripts có permission boundary riêng.

---

# 432.166 — Package trust

Hash verifies content integrity.

Signing có thể được thêm:

```text
package signature
```

nhưng không phải language core requirement.

---

# 432.167 — Build policy

Project có thể yêu cầu:

```text
offline
locked
verified
reproducible
```

---

# 432.168 — `--locked`

Nếu dependency graph khác lockfile:

```text
axiom build --locked
```

→ fail thay vì update.

---

# 432.169 — `--offline`

Không network dependency resolution.

---

# 432.170 — `--reproducible`

Compiler/build driver phải disable nondeterministic metadata và enforce explicit inputs.

---

# 432.171 — Package publication

Publication tooling:

```text
axiom package
axiom publish
```

không thuộc compiler backend.

---

# 432.172 — Package archive

Package archive phải có:

```text
manifest
source
license
metadata
hash
```

và không chứa build cache.

---

# 432.173 — Package source cleanliness

Generated build artifacts không được vô tình trở thành package source.

---

# 432.174 — Dependency license metadata

Package manager có thể inspect license metadata nhưng compiler không áp đặt license policy.

---

# 432.175 — Build configuration precedence

Nên có thứ tự rõ ràng:

```text
language defaults
    ↓
target defaults
    ↓
profile
    ↓
manifest
    ↓
explicit CLI
```

CLI có precedence cao nhất.

---

# 432.176 — No hidden global compiler configuration

Global config chỉ được dùng cho:

```text
cache location
registry mirrors
toolchain selection
```

không nên silently thay đổi language semantics.

---

# 432.177 — Compiler flags reproducibility

Build fingerprint phải bao gồm flags ảnh hưởng:

```text
optimization
overflow behavior
panic mode
target features
debug
LTO
```

---

# 432.178 — Panic profile

425 quy định:

```text
panic=abort
panic=unwind
```

Build profile chọn policy.

---

# 432.179 — Allocation/runtime profile

Có thể chọn:

```text
runtime = "full"
runtime = "minimal"
runtime = "none"
```

để phù hợp application/freestanding.

---

# 432.180 — Standard library selection

Standard library version là dependency của package/build configuration, không hard-code toàn bộ vào compiler.

---

# 432.181 — Compiler intrinsics

Một số chức năng vẫn thuộc compiler:

```text
atomic
simd intrinsic
type queries
memory barriers
target features
```

vì chúng cần semantic/backend knowledge.

---

# 432.182 — Intrinsic stability

Intrinsic phải có namespace rõ ràng:

```text
core::intrinsic::...
```

hoặc equivalent.

---

# 432.183 — Build graph API

Compiler nội bộ nên biểu diễn:

```text
BuildGraph
PackageNode
ModuleNode
ArtifactNode
ResourceNode
```

---

# 432.184 — Dependency edge kinds

Ít nhất:

```text
Source
Type
Value
Comptime
Resource
Link
Runtime
```

Điều này giúp invalidation chính xác.

---

# 432.185 — Comptime dependency integration

431 resource/comptime dependency phải được đưa vào build graph.

Ví dụ:

```text
schema.json
      ↓
comptime generator
      ↓
generated API
      ↓
application
```

---

# 432.186 — Resource hash propagation

Schema đổi:

```text
schema hash changes
```

→ comptime node invalidated

→ generated declaration hash changes

→ dependent modules rebuild.

---

# 432.187 — No timestamp-based correctness

Timestamp chỉ có thể là optimization hint.

Correctness dựa trên content/semantic hashes.

---

# 432.188 — Build graph persistence

Compiler có thể lưu:

```text
build graph metadata
```

để incremental build sau đó không cần reconstruct toàn bộ dependency graph.

---

# 432.189 — Crash recovery

Build cache phải atomic.

Nếu compiler crash giữa artifact write:

```text
partial artifact
```

không được coi là valid cache entry.

---

# 432.190 — Atomic artifact commit

Compiler:

```text
write temporary
 ↓
validate
 ↓
fsync/commit policy
 ↓
rename
```

để cache không corrupt.

---

# 432.191 — Concurrent cache access

Nhiều compiler processes có thể dùng cùng cache.

Cache entries phải có content-addressed immutable identity.

---

# 432.192 — Cache garbage collection

Cache cleanup là tooling:

```text
axiom cache prune
```

Không ảnh hưởng build correctness.

---

# 432.193 — Build artifact provenance

Artifact metadata có thể lưu:

```text
compiler
source hash
dependency hash
target
profile
```

để debugging/reproducibility.

---

# 432.194 — Package dependency ABI

Dependency native library phải khai báo:

```text
target
architecture
ABI
link mode
```

để tránh link sai binary.

---

# 432.195 — Native library search

Build system có search paths explicit:

```text
[target]
library_paths = [...]
```

Không silently search arbitrary directories ngoài configured system paths.

---

# 432.196 — Cross-platform package

Một package có thể chứa:

```text
platform/
    windows.ax
    linux.ax
    macos.ax
```

và dùng target-aware comptime selection.

---

# 432.197 — Platform module abstraction

Library nên expose:

```text
io
filesystem
window
thread
```

qua common API, implementation target-specific.

---

# 432.198 — Package-level API contract

Public package API nên có:

```text
semantic signature
ABI annotations
documentation
version
```

Compiler có thể generate machine-readable API manifest.

---

# 432.199 — API diff

Tooling có thể:

```text
axiom api-diff old.mod new.mod
```

để xác định public API thay đổi.

Đây là tooling, không phải compiler semantic requirement.

---

# 432.200 — Final architecture

Axiom build architecture:

```text
                         PROJECT
                            │
                       axiom.toml
                            │
                  ┌─────────▼─────────┐
                  │  Dependency       │
                  │  Resolver         │
                  └─────────┬─────────┘
                            │
                       Package DAG
                            │
                  ┌─────────▼─────────┐
                  │   Module Graph    │
                  └─────────┬─────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
          Parse/AST      Comptime      Resources
              │             │             │
              └─────────────┼─────────────┘
                            │
                     Semantic IR
                            │
                    Incremental Cache
                            │
                       Code Generation
                            │
                    Object / Libraries
                            │
                         Linker
                            │
                     Native Artifact
```

---

# 432.201 — Các invariant đã khóa

Axiom build/module model chính thức:

1. **Module là semantic unit**, không phải textual include.
2. **Package là distribution/dependency unit**.
3. Private mặc định; public phải explicit.
4. Dependency graph phải deterministic.
5. Module cycle value-level bị cấm; declaration/type cycle chỉ cho phép khi semantic resolver xử lý được.
6. Lockfile hỗ trợ reproducible builds.
7. Dependency dùng content hash để đảm bảo integrity.
8. Incremental compilation dựa trên semantic/interface hashes.
9. Generic/comptime/resource caches là các tầng cache riêng.
10. Compiler version/target/profile phải nằm trong cache identity.
11. Build có thể chạy song song nhưng kết quả deterministic.
12. Registry/package manager không phải dependency của compiler core.
13. Comptime và build script là hai execution contexts khác nhau.
14. Native ABI dependency phải explicit.
15. Cross compilation là first-class.
16. Executable tối thiểu không bắt buộc full runtime.
17. Standard library/runtime là layer trên language core.
18. Compiler có thể consume precompiled semantic module artifacts.
19. ABI ổn định xuyên compiler versions không được mặc định hứa.
20. Build system phải đủ khả năng **self-host Axiom compiler** và hỗ trợ incremental compilation nhanh.

**BOOTSTRAP-432 hoàn tất.**

---

# BOOTSTRAP-433 — STANDARD LIBRARY, CORE LIBRARY & RUNTIME BOUNDARY

Task tiếp theo sẽ xác định một vấn đề rất quan trọng: **cái gì thuộc language core, cái gì thuộc standard library và cái gì thuộc runtime/platform layer**.

Đặc biệt sẽ khóa:

```text
core types
String
Array
Slice
Option
Result
collections
iterators
math
memory/allocator
IO
filesystem
process
network
time
thread
async
atomics
SIMD
random
formatting
logging
reflection
FFI
OS abstraction
```

và quan trọng nhất: làm sao để một chương trình Axiom có thể **chỉ dùng vài KB/runtime tối thiểu**, trong khi ứng dụng lớn vẫn có standard library đầy đủ.