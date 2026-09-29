# BOOTSTRAP-427 — MODULES, PACKAGES, NAMESPACE, VISIBILITY & BUILD GRAPH

427 khóa hệ thống tổ chức mã nguồn và dependency của Axiom. Mục tiêu là **module hóa rõ ràng, compile song song, incremental build mạnh, cache deterministic**, nhưng không biến package manager thành một phần bắt buộc của compiler runtime.

---

## 427.1 — Source file

Một source file `.ax` là đơn vị vật lý của mã nguồn.

Ví dụ:

```text
src/
    main.ax
    math.ax
    io.ax
```

File không nhất thiết tương ứng 1:1 với public module.

---

## 427.2 — Module

Module là đơn vị semantic.

Ví dụ:

```text
module math
```

có thể được tổ chức:

```text
math.ax
```

hoặc:

```text
math/
    mod.ax
    vector.ax
    matrix.ax
```

Compiler nhìn vào module graph, không phụ thuộc cách tổ chức thư mục cụ thể.

---

## 427.3 — Submodule

Module có thể chứa module con:

```text
math
├── vector
├── matrix
└── geometry
```

Tên đầy đủ:

```text
math.vector
math.matrix
math.geometry
```

---

## 427.4 — Package

Package là đơn vị phân phối.

Ví dụ:

```text
package axiom.graphics
```

có thể chứa:

```text
graphics
├── image
├── color
├── mesh
└── render
```

Package không phải runtime object.

---

## 427.5 — Project

Project là đơn vị build/application.

Conceptual:

```text
project/
    axiom.project
    src/
    tests/
    assets/
    build/
```

Một project có thể chứa nhiều package nội bộ.

---

## 427.6 — Namespace

Namespace được hình thành từ module/package path.

Ví dụ:

```text
graphics.image.Image
```

Compiler có thể resolve symbol mà không cần runtime namespace table.

---

## 427.7 — Import

Syntax đề xuất:

```text
import math.vector
```

hoặc:

```text
import math.vector.Vector
```

---

## 427.8 — Selective import

Có thể:

```text
import math.vector.{Vector, VecOps}
```

để tránh đưa toàn bộ namespace vào lexical scope.

---

## 427.9 — Alias

```text
import math.vector as vec
```

sau đó:

```text
v := vec.Vector(...)
```

---

## 427.10 — Symbol alias

```text
import math.vector.Vector as V
```

cho phép:

```text
v := V(...)
```

---

## 427.11 — No wildcard import by default

Không khuyến khích:

```text
import math.*
```

Nếu hỗ trợ, nó phải explicit và compiler vẫn phải giữ deterministic resolution.

Mục tiêu là tránh:

```text
same name
→ multiple imported symbols
→ hidden ambiguity
```

---

# 427.12 — Export

Module có thể export:

```text
pub struct Vector { ... }
pub fn normalize(...)
```

Symbol không được `pub` mặc định là private.

---

# 427.13 — Visibility levels

Axiom dùng một hệ thống visibility nhỏ:

```text
private
module
package
public
```

Trong đó:

```text
private → declaration scope
module  → current module
package → current package
public  → external packages
```

Không cần hàng chục visibility modifiers.

---

# 427.14 — Default visibility

Default:

```text
private
```

Điều này giảm public API ngoài ý muốn.

---

# 427.15 — Public module

Một module có thể export module con:

```text
pub module vector
```

Client có thể:

```text
import math.vector
```

---

# 427.16 — Re-export

Ví dụ:

```text
pub use math.vector.Vector
```

cho phép package facade:

```text
import graphics.Vector
```

thay vì:

```text
import graphics.math.vector.Vector
```

---

# 427.17 — Qualified names

Khi ambiguity:

```text
math.Vector
graphics.Vector
```

có thể viết đầy đủ.

Compiler không tự đoán giữa các symbol đồng tên.

---

# 427.18 — Name resolution

Resolution nên thực hiện theo pipeline deterministic:

```text
local
→ current module
→ explicit imports
→ package exports
→ prelude
```

Nếu có nhiều candidate cùng precedence:

```text
AMBIGUOUS_SYMBOL
```

---

# 427.19 — Prelude

Axiom có thể có một prelude nhỏ:

```text
Option
Result
String
Array
```

nhưng prelude phải được kiểm soát.

Freestanding mode có thể:

```text
no_prelude
```

để build kernel/embedded.

---

# 427.20 — Circular imports

Module graph nên là DAG ở semantic import level.

Không cho:

```text
A → B
B → A
```

nếu hai module cần compile-time symbol dependency thực sự.

Compiler báo cycle với đường dẫn:

```text
A
 ↓
B
 ↓
C
 ↓
A
```

---

# 427.21 — Type-only cycles

Một số dependency type-level có thể được compiler xử lý nếu không tạo initialization dependency.

Do đó cần phân biệt:

```text
type dependency
value dependency
initialization dependency
```

---

# 427.22 — Module initialization

Axiom không nên có implicit arbitrary top-level executable code.

Ưu tiên:

```text
const
static
declaration
```

và initialization runtime rõ ràng.

Điều này giúp native startup deterministic.

---

# 427.23 — Static initialization

Nếu:

```text
static table: [u8; 256] = [...]
```

compiler nên emit trực tiếp vào:

```text
.rodata
.data
.bss
```

nếu có thể.

Không tạo runtime initializer.

---

# 427.24 — Runtime initialization

Nếu initialization thực sự cần code:

```text
static config = init_config()
```

compiler phải biểu diễn explicit initialization phase.

Không được tạo hàng loạt constructor ẩn kiểu C++.

---

# 427.25 — Package metadata

Project/package metadata cần chứa tối thiểu:

```text
name
version
source roots
target settings
dependencies
features
build configuration
```

---

# 427.26 — Dependency graph

Compiler xây:

```text
Package Graph
      ↓
Module Graph
      ↓
Symbol Graph
      ↓
Compilation Units
```

Mỗi node có fingerprint.

---

# 427.27 — Package dependency

Ví dụ:

```text
app
 ├── graphics
 ├── audio
 └── math
```

Compiler không cần compile `math` lại nếu artifact tương thích vẫn còn cache.

---

# 427.28 — Dependency versioning

Package có semantic version:

```text
major.minor.patch
```

Version constraint:

```text
graphics = 2.x
```

hoặc tương đương.

Package manager chịu trách nhiệm resolution; compiler chỉ nhận dependency graph đã resolve.

---

# 427.29 — Lockfile

Project application có:

```text
axiom.lock
```

để cố định dependency graph.

Build reproducibility không phụ thuộc việc registry hôm nay trả version khác hôm qua.

---

# 427.30 — Library dependency

Axiom phân biệt:

```text
Axiom package
native library
system library
framework
```

Compiler không giả định tất cả dependency là Axiom source.

---

# 427.31 — Native library

Project có thể khai báo:

```text
link libc
link user32
link Foundation
```

tùy target.

Việc linking được chuyển xuống native linker model của BOOTSTRAP-420.

---

# 427.32 — Static library

Package có thể phát hành:

```text
libfoo.a
foo.lib
```

Compiler/linker sử dụng symbol/object metadata.

---

# 427.33 — Dynamic library

Có thể:

```text
libfoo.so
foo.dll
foo.dylib
```

với import/export ABI đã khóa trong 420/421.

---

# 427.34 — C interoperability

Package có thể khai báo:

```text
extern package libc
```

hoặc tương đương.

Axiom không cần compile C source để link C library.

---

# 427.35 — Header/interface import

Để sử dụng C API, Axiom cần một mô tả ABI:

```text
fn malloc(size: usize) -> *mut u8
```

Compiler không cần phụ thuộc C compiler tại runtime build.

---

# 427.36 — Generated bindings

Có thể có tool:

```text
axiom bindgen
```

chuyển header/API description thành Axiom declarations.

Generated file sau đó trở thành ordinary Axiom source/interface metadata.

---

# 427.37 — Build script

Build script được phép thực hiện các tác vụ build:

```text
generate source
compile shader
generate bindings
copy resources
```

nhưng không được âm thầm thay đổi semantic compilation.

---

# 427.38 — Compiler plugins

Compiler plugin không được là dependency bắt buộc của core compiler.

Plugin API phải versioned.

---

# 427.39 — Macro boundary

Axiom có thể hỗ trợ compile-time code generation sau này.

Nhưng macro phải phân biệt:

```text
syntax transformation
semantic compilation
native code generation
```

Không cho macro tùy tiện phá compiler invariants.

---

# 427.40 — Compile-time execution

Một cơ chế `comptime` có thể được bổ sung:

```text
const
comptime
```

nhưng compile-time execution phải deterministic và có sandbox/resource limit.

Chi tiết sẽ được khóa ở task compile-time/metaprogramming riêng.

---

# 427.41 — Module interface

Axiom nên tạo metadata:

```text
foo.axiom-interface
```

chứa:

```text
public types
public functions
trait implementations
ABI information
generic definitions
compiler version
dependency fingerprints
```

Private implementation không cần đưa vào interface.

---

# 427.42 — Precompiled module

Nếu interface + relevant implementation artifact còn hợp lệ:

```text
source
 ↓
fingerprint
 ↓
interface/cache hit
 ↓
skip compilation
```

---

# 427.43 — Fingerprint

Fingerprint phải tính từ semantic inputs, ví dụ:

```text
source hash
compiler version
target triple
ABI
optimization mode
feature set
dependency interface hashes
relevant environment
```

Không dùng timestamp làm semantic identity.

---

# 427.44 — Incremental compilation

Thay đổi:

```text
private implementation
```

không nhất thiết invalidate downstream modules.

Thay đổi:

```text
public type layout
public signature
trait contract
ABI
```

có thể invalidate consumers.

---

# 427.45 — Fine-grained invalidation

Compiler nên track dependency:

```text
Module A
   │
   ├── symbol X
   └── symbol Y
```

Nếu chỉ Y thay đổi, không nhất thiết recompile code chỉ dùng X.

---

# 427.46 — Generic invalidation

Generic specialization phụ thuộc:

```text
generic body
constraints
type arguments
target
optimization configuration
```

Compiler cache riêng specialization.

---

# 427.47 — Parallel compilation

Module DAG cho phép:

```text
A ──┐
B ──┼──→ D
C ──┘
```

A, B, C compile song song.

Điều này là một yêu cầu kiến trúc chứ không chỉ optimization build tool.

---

# 427.48 — Deterministic build

Cùng:

```text
source
dependency graph
compiler version
target
configuration
```

phải tạo artifact equivalent.

Không để thứ tự thread compilation ảnh hưởng binary semantics.

---

# 427.49 — Build cache

Cache key:

```text
Hash(
    source/interface
    compiler
    target
    ABI
    flags
    dependencies
)
```

Cache artifact có thể chứa:

```text
AST/semantic cache
IR
generic specializations
object file
debug metadata
interface
```

---

# 427.50 — Content-addressed artifacts

Artifact nên lưu theo content/hash:

```text
cache/
    ab/cd/abcdef...
```

Thay vì tên phụ thuộc đường dẫn source.

Điều này thuận lợi cho distributed cache sau này.

---

# 427.51 — Local cache

Default:

```text
project/.axiom-cache
```

hoặc user-global cache.

Compiler phải cho phép disable cache để debugging/reproducibility testing.

---

# 427.52 — Remote cache

Kiến trúc cache phải đủ trừu tượng để sau này hỗ trợ:

```text
local cache
LAN cache
remote cache
CI cache
```

nhưng remote cache không phải core requirement.

---

# 427.53 — Package cache

Package manager có thể cache source/archive.

Compiler cache binary/intermediate artifacts.

Hai tầng không nên bị trộn semantic.

---

# 427.54 — Offline build

Nếu dependency đã được vendor/cache:

```text
network = disabled
```

vẫn build được.

---

# 427.55 — Vendoring

Project có thể:

```text
vendor/
    packageA/
    packageB/
```

để khóa dependency source.

---

# 427.56 — Dependency trust

Package metadata có thể chứa:

```text
publisher
signature
checksum
source hash
```

Nhưng compiler không bắt buộc một centralized registry.

---

# 427.57 — Reproducible dependency resolution

Lockfile + checksums đảm bảo package resolution không thay đổi ngoài ý muốn.

---

# 427.58 — Source maps

Compiler debug metadata phải map:

```text
native instruction
→ IR
→ AST
→ source file
→ line/column
```

Phục vụ debugger, profiler và AI tooling.

---

# 427.59 — Diagnostics across modules

Error:

```text
module A
    calls B.foo()
```

nếu `foo` thay đổi signature, diagnostic phải chỉ ra:

```text
A: call site
B: declaration
difference
```

---

# 427.60 — IDE integration

Module interface có thể được dùng để cung cấp:

```text
completion
go-to-definition
find references
type information
documentation
rename
```

mà không cần compile toàn bộ project.

---

# 427.61 — LSP

Axiom có thể cung cấp:

```text
axiom-lsp
```

nhưng LSP không thuộc compiler semantic core.

---

# 427.62 — AI-readable metadata

Đây là phần đặc biệt phù hợp với mục tiêu Axiom.

Compiler có thể xuất:

```text
axiom.symbols
axiom.interface
axiom.deps
axiom.diagnostics
```

machine-readable.

Ví dụ:

```text
{
    "symbol": "Vector.length",
    "kind": "function",
    "receiver": "Vector",
    "params": [],
    "returns": "f32",
    "visibility": "public"
}
```

Không bắt AI phải parse compiler text output.

---

# 427.63 — Semantic index

Project có thể có:

```text
semantic index
```

chứa:

```text
types
functions
traits
implementations
dependencies
call relationships
source locations
```

Đây là cơ sở tốt cho AI agent và IDE.

---

# 427.64 — AI metadata không ảnh hưởng binary

Metadata AI phải nằm ngoài executable hoặc trong optional section.

Release build có thể:

```text
strip AI metadata
```

---

# 427.65 — Module ABI

Module interface phải phân biệt:

```text
source compatibility
semantic compatibility
ABI compatibility
```

Một thay đổi implementation không nhất thiết phá ABI.

---

# 427.66 — ABI version

Native library interface có:

```text
ABI version
target
architecture
calling convention
layout hash
```

để tránh load nhầm binary.

---

# 427.67 — Build target

Target được biểu diễn bằng triple/config:

```text
x86_64-windows
x86_64-linux
aarch64-linux
aarch64-macos
aarch64-ios
aarch64-android
wasm32
```

Compiler frontend không cần biết OS-specific path nếu backend abstraction đã chuẩn hóa.

---

# 427.68 — Cross compilation

Một compiler binary có thể:

```text
host = x86_64-windows
target = aarch64-linux
```

miễn target backend/sysroot cần thiết có sẵn.

---

# 427.69 — Sysroot

Target configuration có thể chỉ tới:

```text
headers/interface
runtime support
system libraries
linker metadata
```

Axiom không bắt buộc sử dụng GCC/Clang sysroot.

---

# 427.70 — Freestanding project

Có thể:

```text
freestanding = true
```

Khi đó không cần:

```text
OS
libc
default runtime
thread runtime
allocator runtime
```

Phù hợp kernel/embedded.

---

# 427.71 — Hosted project

Hosted mode có:

```text
OS facilities
standard runtime/library
default allocator
threading
filesystem
networking
```

theo package/runtime configuration.

---

# 427.72 — Standard library

Standard library không nên bị nhúng cứng vào compiler nhiều hơn mức cần thiết.

Core/compiler intrinsic chỉ giữ:

```text
primitive types
low-level operations
ABI primitives
compiler intrinsics
```

Library cung cấp:

```text
collections
IO
filesystem
network
threads
async
serialization
```

---

# 427.73 — Runtime

Axiom runtime phải modular:

```text
axiom-core
axiom-memory
axiom-thread
axiom-async
axiom-os
```

Project có thể link phần cần thiết.

---

# 427.74 — Dead runtime elimination

Nếu application không dùng async:

```text
async runtime
```

không được link chỉ vì standard library tồn tại.

---

# 427.75 — Feature flags

Package có thể:

```text
feature graphics
feature audio
feature networking
```

Compiler/build graph phải đưa feature state vào fingerprint.

---

# 427.76 — Conditional compilation

Có thể:

```text
#if target(os == "windows")
...
#endif
```

nhưng expression system cần được khóa riêng.

Điều kiện compile-time phải deterministic.

---

# 427.77 — Platform modules

Platform API nên nằm trong namespace:

```text
platform.windows
platform.linux
platform.apple
```

Không pollute core namespace.

---

# 427.78 — Tests

Package:

```text
tests/
```

có thể compile thành test executable riêng.

Unit test không cần runtime framework bắt buộc.

---

# 427.79 — Examples/benchmarks

Project có thể có:

```text
examples/
benchmarks/
```

là compilation targets độc lập.

---

# 427.80 — Build graph artifacts

Mỗi node build có:

```text
input fingerprint
output fingerprint
dependencies
target
diagnostics
```

Build system có thể reconstruct graph mà không cần scan lại mọi source.

---

# 427.81 — Compiler daemon

Sau này có thể có:

```text
axiomd
```

giữ:

```text
AST cache
semantic graph
module interfaces
compiler state
```

để IDE/build incremental nhanh.

Compiler command-line vẫn phải hoạt động độc lập.

---

# 427.82 — No mandatory build daemon

Không được yêu cầu daemon để compiler hoạt động.

Điều này quan trọng cho:

```text
CI
embedded
bootstrap
debugging
portable builds
```

---

# 427.83 — Bootstrap compiler

Axiom compiler đầu tiên có thể dùng:

```text
stage0
```

để compile compiler source.

Sau khi Axiom compiler đủ mạnh:

```text
Axiom compiler
    ↓
compile itself
    ↓
self-hosted
```

---

# 427.84 — Bootstrap artifacts

Stage bootstrap phải có:

```text
compiler executable
core interface
minimal runtime
target backend
linker/object support
```

đủ để build stage tiếp theo.

---

# 427.85 — Compiler/package boundary

Package manager không được quyết định:

```text
type checking
ABI
machine code
linking semantics
```

Compiler vẫn kiểm soát những phần này.

---

# 427.86 — Build tool/package manager boundary

Package manager chịu trách nhiệm:

```text
download
resolve versions
verify checksum
vendor
cache source
```

Build/compiler chịu trách nhiệm:

```text
parse
analyze
compile
link
emit artifact
```

---

# 427.87 — No third-party compiler dependency

Package có thể depend native library, nhưng Axiom compiler không được cần:

```text
gcc
clang
msvc compiler
rustc
llvm
```

để thực hiện native compilation của Axiom source.

Điều này kế thừa invariant của 420.

---

# 427.88 — Package native code

Package có thể chứa prebuilt native artifact:

```text
native/
    windows-x64/
    linux-x64/
    macos-arm64/
```

và metadata ABI tương ứng.

---

# 427.89 — Source/native fallback

Một package có thể cung cấp:

```text
Axiom source
+
native prebuilt
```

Compiler chọn source hoặc native artifact tùy target/configuration.

---

# 427.90 — Binary compatibility

Artifact cache chỉ được reuse nếu:

```text
target
ABI
compiler-relevant configuration
dependency ABI
```

compatible.

Không reuse artifact chỉ vì source hash giống nhau.

---

# 427.91 — Build determinism test

Compiler test suite phải build cùng source nhiều lần:

```text
clean build
incremental build
parallel build
cached build
```

và kiểm tra artifact semantic equivalence/deterministic bytes theo build mode.

---

# 427.92 — Security boundary

Build script không được mặc định có quyền vô hạn nếu môi trường sandbox yêu cầu.

Có thể có:

```text
sandboxed build
trusted build
```

mode.

---

# 427.93 — Reproducibility

Build metadata phải tránh đưa:

```text
absolute local path
username
current timestamp
random ID
```

vào artifact release trừ khi explicitly requested.

---

# 427.94 — Debug vs release

Debug artifact có thể chứa:

```text
source paths
symbols
AI metadata
type metadata
```

Release có thể strip.

---

# 427.95 — Package API surface

Compiler có thể generate API report:

```text
public:
    Vector
    Matrix
    Image
```

để detect accidental breaking API changes.

---

# 427.96 — Semantic version automation

Compiler tooling có thể phát hiện:

```text
public signature changed
public layout changed
trait contract changed
```

nhưng không tự quyết định version bump.

---

# 427.97 — Conformance tests

427 phải có test groups:

```text
MODULE-001
IMPORT-001
VISIBILITY-001
PACKAGE-001
CYCLE-001
CACHE-001
INCREMENTAL-001
GENERIC-CACHE-001
ABI-001
FFI-001
CROSS-001
DETERMINISM-001
AI-META-001
BOOTSTRAP-001
```

---

# 427.98 — Hard invariants

1. Module graph deterministic.
2. Dependency graph explicit.
3. Default visibility private.
4. Public API explicit.
5. No mandatory global namespace.
6. Circular semantic imports prohibited.
7. Static initialization phải deterministic.
8. Package manager và compiler có boundary rõ ràng.
9. Incremental compilation là architectural feature.
10. Content-based fingerprints.
11. Generic specialization cache.
12. Parallel compilation.
13. Deterministic builds.
14. Offline/vendor build.
15. Native library support.
16. C ABI support.
17. Cross compilation.
18. Freestanding mode.
19. Optional runtime.
20. AI-readable semantic metadata.
21. Debug metadata tách khỏi release metadata.
22. Compiler không phụ thuộc compiler bên thứ ba.
23. Native artifact reuse phải kiểm tra ABI/target compatibility.
24. Build daemon là optional.
25. Package ecosystem không được trở thành dependency của language core.

---

# 427.99 — Final module architecture

```text
                         AXIOM PROJECT
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                 PACKAGES            TARGETS
                    │
             ┌──────┴──────┐
             ▼             ▼
          MODULES       DEPENDENCIES
             │             │
             └──────┬──────┘
                    ▼
              SEMANTIC GRAPH
                    │
          ┌─────────┼──────────┐
          ▼         ▼          ▼
       INTERFACE    IR       GENERICS
          │         │          │
          └─────────┼──────────┘
                    ▼
              BUILD CACHE
                    │
                    ▼
             NATIVE OBJECT
                    │
                    ▼
                 LINKER
                    │
                    ▼
              EXE / ELF /
          Mach-O / WASM / LIB
```

**BOOTSTRAP-427 hoàn tất về mặt kiến trúc.**

---

# BOOTSTRAP-428 — EXPRESSIONS, STATEMENTS, CONTROL FLOW & PATTERN MATCHING

Tiếp theo cần khóa **execution semantics của ngôn ngữ**. Đây là phần nối trực tiếp từ type system + ownership + error handling vào compiler IR.

## 428.1 — Mục tiêu

Axiom cần một control-flow model:

- dễ đọc;
- ít syntax thừa;
- compiler dễ lower;
- tối ưu branch tốt;
- hỗ trợ exhaustive pattern matching;
- hỗ trợ `Result`/`Option`;
- không tạo hidden allocation;
- phù hợp async lowering;
- phù hợp SSA/CFG backend.

---

## 428.2 — Expression-oriented design

Axiom nên theo hướng:

> **Expression có giá trị; statement chủ yếu là expression có side effect hoặc declaration.**

Ví dụ:

```text
x := if condition {
    10
} else {
    20
}
```

Compiler lower thành CFG + phi/select tùy optimization.

---

## 428.3 — Block expression

```text
x := {
    a := 10
    b := 20
    a + b
}
```

Giá trị cuối block là expression cuối.

---

## 428.4 — Statement

Các loại statement core:

```text
declaration
assignment
expression statement
return
break
continue
defer
```

Không cần một statement syntax riêng cho mọi tính năng.

---

## 428.5 — Declaration

Ví dụ:

```text
x := 10
```

là local declaration.

Type inference là default nếu compiler xác định được type.

---

## 428.6 — Explicit type

```text
x: i32 = 10
```

dùng khi programmer muốn khóa type.

---

## 428.7 — Assignment

```text
x = 20
```

chỉ hợp lệ nếu `x` là mutable storage.

Immutable-by-default sẽ giảm accidental mutation.

---

## 428.8 — Multiple assignment

Có thể hỗ trợ:

```text
a, b = b, a
```

Compiler phải đảm bảo evaluation semantics deterministic.

---

## 428.9 — Tuple expression

```text
(x, y)
```

là value aggregate.

---

## 428.10 — Destructuring

```text
(x, y) := point
```

hoặc pattern equivalent.

Compiler phải xử lý ownership/move của từng component theo 423.

---

## 428.11 — `if` expression

```text
value := if x > 0 {
    1
} else {
    -1
}
```

---

## 428.12 — `else if`

```text
if a {
    ...
} else if b {
    ...
} else {
    ...
}
```

---

## 428.13 — `if` không bắt buộc value

```text
if ready {
    process()
}
```

là ordinary control flow.

---

## 428.14 — `while`

```text
while condition {
    work()
}
```

Compiler lower trực tiếp thành CFG loop.

---

## 428.15 — Infinite loop

```text
loop {
    work()
}
```

không cần:

```text
while true
```

---

## 428.16 — `for`

Axiom nên có iteration-oriented syntax:

```text
for item in items {
    process(item)
}
```

---

## 428.17 — Range

```text
for i in 0..n {
    ...
}
```

Range semantics phải được định nghĩa rõ inclusive/exclusive.

Khuyến nghị:

```text
0..n
```

là `[0,n)`.

---

## 428.18 — Inclusive range

```text
0..=n
```

là `[0,n]`.

---

## 428.19 — Numeric loop optimization

Compiler phải nhận diện range loop và có thể lower trực tiếp thành:

```text
compare
increment
branch
```

không tạo iterator object nếu abstraction có thể được elide.

---

## 428.20 — `break`

```text
break
```

thoát loop gần nhất.

---

## 428.21 — Break with value

Expression loop có thể:

```text
result := loop {
    if done {
        break value
    }
}
```

Compiler tạo loop result.

---

## 428.22 — `continue`

```text
continue
```

nhảy tới next iteration.

---

## 428.23 — Labels

Nếu nested loop cần điều khiển rõ:

```text
break outer
continue outer
```

Label phải lexical và deterministic.

---

## 428.24 — `return`

```text
return value
```

kết thúc function.

Cleanup từ BOOTSTRAP-423 phải chạy trước return.

---

## 428.25 — `defer`

```text
defer close(file)
```

được thực thi khi scope/function exit theo semantics 423.

Compiler nên lower `defer` thành cleanup path, không yêu cầu runtime stack object.

---

## 428.26 — Match

Pattern matching là core language feature:

```text
match value {
    Pattern1 => expr1
    Pattern2 => expr2
}
```

---

## 428.27 — Exhaustiveness

Với enum:

```text
enum Result<T,E> {
    Ok(T)
    Err(E)
}
```

compiler kiểm tra:

```text
match result {
    Ok(x) => ...
    Err(e) => ...
}
```

đã đầy đủ.

---

## 428.28 — Missing pattern

Nếu thiếu case:

```text
NON_EXHAUSTIVE_MATCH
```

diagnostic phải chỉ rõ variant còn thiếu.

---

## 428.29 — Wildcard

```text
_ => ...
```

match mọi giá trị còn lại.

---

## 428.30 — Literal pattern

```text
match x {
    0 => ...
    1 => ...
    _ => ...
}
```

---

## 428.31 — Enum pattern

```text
match result {
    Ok(value) => ...
    Err(error) => ...
}
```

---

## 428.32 — Struct pattern

```text
match point {
    Vec2 { x: 0, y } => ...
    Vec2 { x, y } => ...
}
```

---

## 428.33 — Tuple pattern

```text
match value {
    (0, x) => ...
    (x, 0) => ...
    _ => ...
}
```

---

## 428.34 — Binding pattern

```text
Some(value)
```

vừa kiểm tra variant vừa bind value.

---

## 428.35 — Pattern guards

Có thể hỗ trợ:

```text
Some(x) if x > 10 => ...
```

Guard không thay thế exhaustiveness analysis của structural patterns.

---

## 428.36 — OR patterns

Có thể:

```text
0 | 1 | 2 => ...
```

Compiler kiểm tra overlap.

---

## 428.37 — Pattern ownership

Match phải tuân ownership rules.

Ví dụ match consuming value có thể move payload.

Match trên view/borrow chỉ đọc payload.

---

## 428.38 — Match optimization

Compiler được phép lower:

```text
enum match
```

thành:

```text
jump table
conditional branches
binary decision tree
```

tùy profile/codegen.

---

## 428.39 — Boolean short-circuit

```text
a && b
a || b
```

phải short-circuit.

`b` không được evaluate nếu semantic không yêu cầu.

---

## 428.40 — Null/Option semantics

Không có implicit nullable references.

Thay vào đó:

```text
Option<T>
```

là explicit.

---

## 428.41 — `?` / propagation

`Result`/`Option` propagation cần syntax compact.

Conceptual:

```text
value := try read()
```

Exact token sẽ được khóa trong syntax task.

---

## 428.42 — Panic path

```text
panic("message")
```

là divergent expression:

```text
Never
```

---

## 428.43 — Never type

Các expression không return:

```text
return
panic
abort
infinite loop
```

có thể có type:

```text
Never
```

Compiler dùng nó cho control-flow analysis.

---

## 428.44 — Unreachable code

Nếu compiler chứng minh:

```text
panic(...)
x := ...
```

`x` unreachable.

Diagnostic có thể cảnh báo, không nhất thiết error.

---

## 428.45 — Conditional operator

Không cần thêm ternary:

```text
condition ? a : b
```

vì:

```text
if condition { a } else { b }
```

đã đủ.

Giảm syntax surface.

---

## 428.46 — Match vs switch

Axiom không cần hai hệ thống:

```text
switch
match
```

`match` có thể xử lý:

```text
integer
enum
tuple
struct
patterns
```

Compiler tối ưu nó thành switch/jump table khi thích hợp.

---

## 428.47 — Fallthrough

Không có implicit fallthrough giữa match arms.

Nếu muốn nhiều pattern:

```text
A | B => ...
```

---

## 428.48 — Assignment expression

Khuyến nghị **không** coi:

```text
x = y
```

là value-producing expression.

Điều này tránh các bug kiểu:

```text
if (x = foo()) ...
```

---

## 428.49 — Increment operators

Không cần:

```text
x++
++x
x--
--x
```

Thay bằng:

```text
x += 1
x -= 1
```

Giảm semantic edge cases.

---

## 428.50 — Compound assignment

Hỗ trợ:

```text
+=
-=
*=
/=
%=
&=
|=
^=
<<=
>>=
```

nếu type cung cấp operation tương ứng.

---

## 428.51 — Arithmetic precedence

Compiler phải có precedence table deterministic.

Không để parser suy đoán theo context.

---

## 428.52 — User-defined operators

Operators custom chỉ được map thông qua core operator traits đã khóa ở 426.

Không cho phép định nghĩa arbitrary new punctuation operators trong core.

---

## 428.53 — Function call

```text
foo(a, b)
```

là expression.

Static function pointer/generic/dynamic interface call sẽ được phân biệt ở semantic lowering.

---

## 428.54 — Method call

```text
object.foo(x)
```

là sugar:

```text
foo(object, x)
```

theo struct-first model.

---

## 428.55 — Indexing

```text
array[i]
```

được map tới indexing capability.

Compiler có thể special-case native arrays.

---

## 428.56 — Bounds checking

Safe indexing:

```text
array[i]
```

có bounds checking nếu compiler không chứng minh `i` hợp lệ.

Unchecked:

```text
unsafe_array[i]
```

hoặc intrinsic tương ứng sẽ thuộc unsafe domain.

---

## 428.57 — Bounds-check elimination

Compiler có thể loại bounds check nếu chứng minh:

```text
0 <= i < len
```

Không yêu cầu programmer viết unsafe chỉ để đạt performance.

---

## 428.58 — Slice/range indexing

Có thể:

```text
array[a..b]
```

tạo view/slice, không copy data mặc định.

---

## 428.59 — Slice assignment

Nếu cần copy:

```text
copy(dst, src)
```

là explicit operation.

Không biến slice assignment thành hidden allocation/copy lớn.

---

## 428.60 — `defer` + loops

`defer` trong loop phải có semantics rõ:

```text
while ... {
    defer cleanup()
}
```

Cleanup thuộc scope iteration hay function phải được compiler xác định deterministic.

Khuyến nghị:

> defer gắn với lexical scope nơi nó xuất hiện.

---

## 428.61 — Exception/unwind interaction

Nếu panic/unwind xảy ra:

```text
defer
drop
cleanup
```

được chạy theo cleanup graph của 423.

---

## 428.62 — Async interaction

Trong async function:

```text
await
```

là suspension point.

Compiler phải lower thành state machine, không block OS thread.

---

## 428.63 — Await

Conceptual:

```text
value := await future
```

Nếu `future` pending:

```text
save state
return Pending
```

---

## 428.64 — No hidden thread

`await` không có nghĩa:

```text
spawn thread
```

Async semantics kế thừa 424.

---

## 428.65 — `select`

Sau này async runtime có thể hỗ trợ:

```text
select {
    a := await f1 => ...
    b := await f2 => ...
}
```

Nhưng semantic core chỉ cần một primitive suspension model; scheduler/select có thể thuộc library.

---

## 428.66 — Defer in async

Compiler phải đảm bảo cleanup semantics chính xác qua:

```text
suspend
resume
cancel
complete
```

Không để defer bị mất khi future bị cancel.

---

## 428.67 — Concurrency control flow

`spawn` là library/runtime operation, không phải implicit control flow.

Ví dụ:

```text
task := spawn(fn() { work() })
join(task)
```

---

## 428.68 — Error propagation through control flow

`try`/propagation phải compile thành branch:

```text
call
test Result tag
success → continue
error → return error
```

Không cần exception machinery.

---

## 428.69 — Match on Result

Compiler có thể tối ưu:

```text
match result {
    Ok(v) => ...
    Err(e) => ...
}
```

thành branch trên discriminant.

---

## 428.70 — Match on Option

Tương tự:

```text
match option {
    Some(x) => ...
    None => ...
}
```

---

## 428.71 — Constant conditions

Nếu:

```text
if comptime_condition
```

compiler có thể loại bỏ branch hoàn toàn.

---

## 428.72 — Compile-time control flow

Compile-time `if`/loop sẽ được phân biệt semantic với runtime control flow.

Ví dụ conceptual:

```text
comptime if target.arch == "x86_64" {
    ...
}
```

Chi tiết thuộc BOOTSTRAP task metaprogramming.

---

## 428.73 — CFG

Frontend phải lower control flow thành CFG:

```text
BasicBlock
    ↓
Terminator
```

Terminator gồm:

```text
branch
conditional branch
switch
return
unreachable
call-with-exception-edge
suspend
```

---

## 428.74 — SSA

IR có thể sử dụng SSA cho local values:

```text
x1
x2
x3
```

và `phi` tại merge points.

Điều này thuận lợi cho optimizer.

---

## 428.75 — Mutable variables

Source:

```text
x := 1
x = 2
```

có thể vẫn lower thành SSA:

```text
x0 = 1
x1 = 2
```

Không cần memory store nếu không address-taken.

---

## 428.76 — Address-taken variable

Nếu:

```text
ptr := &x
```

compiler phải materialize storage theo memory model 423.

---

## 428.77 — Tail position

Function call ở tail position có thể được compiler tối ưu thành tail call khi ABI cho phép.

Điều này kế thừa BOOTSTRAP-421.

---

## 428.78 — Recursion

Recursion được hỗ trợ bình thường.

Không có guarantee tail recursion trừ khi compiler/ABI có thể thực hiện tail-call optimization.

---

## 428.79 — Loop optimization

Compiler được phép:

```text
unroll
peel
vectorize
fuse
unswitch
strength-reduce
```

khi semantics cho phép.

---

## 428.80 — Side-effect ordering

Axiom phải có evaluation order deterministic.

Compiler chỉ được reorder operations nếu không thay đổi observable semantics theo memory model.

---

## 428.81 — Function arguments

Evaluation order của arguments phải được khóa.

Khuyến nghị:

```text
left-to-right
```

để AI và programmer dễ reason.

---

## 428.82 — Operator operands

Tương tự, operand evaluation:

```text
left-to-right
```

trừ những phép compiler intrinsic có semantic đặc biệt.

---

## 428.83 — Panic evaluation

Nếu:

```text
foo(bar(), baz())
```

`bar()` panic thì `baz()` không được evaluate nếu chưa tới lượt theo evaluation order.

---

## 428.84 — Pattern evaluation

Match scrutinee được evaluate **một lần**.

Không gọi lại expression cho mỗi arm.

---

## 428.85 — Guard evaluation

Guard chỉ được evaluate sau khi structural pattern match thành công.

---

## 428.86 — No implicit coercion control flow

Boolean conditions yêu cầu boolean:

```text
if x
```

không tự động biến:

```text
i32
pointer
string
```

thành truthy/falsy.

Điều này giảm bug.

---

## 428.87 — Explicit conversion

Nếu muốn kiểm tra:

```text
if x != 0
```

hoặc dùng explicit conversion capability.

---

## 428.88 — Exhaustiveness diagnostics

Compiler có thể báo:

```text
missing:
    None
```

hoặc:

```text
missing enum variants:
    Timeout
    Cancelled
```

---

## 428.89 — Unreachable match arms

Ví dụ:

```text
_ => ...
Some(x) => ...
```

arm sau `_` unreachable.

Compiler phải diagnostic.

---

## 428.90 — Overlapping patterns

Nếu:

```text
0..10 => ...
5..20 => ...
```

arm sau có phần overlap.

Compiler phải detect khi có thể.

---

## 428.91 — Pattern complexity

Pattern matching không được biến compiler thành một SAT solver bắt buộc.

Phân tích exhaustiveness có giới hạn deterministic.

Pattern quá phức tạp có thể nhận diagnostic thay vì treo compiler.

---

## 428.92 — Compile-time resource limits

Compile-time pattern analysis và generic expansion phải có giới hạn:

```text
recursion depth
instantiation count
memory budget
```

để chống compiler blow-up.

---

## 428.93 — Error recovery

Parser phải cố gắng tiếp tục sau syntax error để báo nhiều lỗi trong một compile.

Nhưng semantic compiler không được tạo ra artifact executable từ source đang có error trừ khi explicit IDE/error-tolerant mode.

---

## 428.94 — IDE partial semantics

IDE mode có thể tạo incomplete AST/semantic model để:

```text
completion
diagnostic
navigation
```

nhưng đây không phải language semantics của production build.

---

## 428.95 — Machine-readable control-flow diagnostics

Diagnostic API nên có:

```text
code
severity
file
span
expected
found
related spans
fix-it
```

Ví dụ:

```text
E428001 NON_EXHAUSTIVE_MATCH
```

---

## 428.96 — Conformance tests

Tối thiểu:

```text
FLOW-001 if
FLOW-002 if-expression
FLOW-003 while
FLOW-004 loop
FLOW-005 for
FLOW-006 break
FLOW-007 continue
FLOW-008 return
FLOW-009 defer
FLOW-010 match
FLOW-011 exhaustive enum
FLOW-012 wildcard
FLOW-013 struct pattern
FLOW-014 tuple pattern
FLOW-015 guard
FLOW-016 OR pattern
FLOW-017 Result propagation
FLOW-018 Option propagation
FLOW-019 bounds checking
FLOW-020 bounds elimination
FLOW-021 async await
FLOW-022 cleanup during panic
FLOW-023 cleanup during return
FLOW-024 SSA lowering
FLOW-025 deterministic evaluation
```

---

# 428.97 — Hard invariants

1. Expressions có thể produce value.
2. Blocks có thể là expressions.
3. Assignment không tạo value.
4. Evaluation order deterministic.
5. Function arguments evaluate left-to-right.
6. `if` có thể là expression.
7. `loop` có thể trả value.
8. `for` hỗ trợ iterator/range.
9. `match` là pattern matching core.
10. Enum match phải exhaustive trừ khi wildcard/explicit escape.
11. Không implicit fallthrough.
12. Pattern match evaluate scrutinee một lần.
13. Boolean condition phải là boolean.
14. Không implicit truthiness cho integer/pointer/string.
15. `Result`/`Option` propagation là branch-based.
16. Panic là divergent control flow.
17. Cleanup luôn tuân ownership model.
18. Async `await` là suspension, không phải thread spawn.
19. Bounds checking safe-by-default.
20. Compiler có quyền eliminate proven bounds checks.
21. Control flow lower được thành CFG.
22. SSA là representation phù hợp cho optimizer.
23. Tail-call optimization được phép khi ABI cho phép.
24. No hidden allocation do control-flow syntax.
25. No hidden thread creation.
26. Compile-time control flow tách khỏi runtime control flow.
27. Diagnostics machine-readable.

---

# 428.98 — Architecture snapshot

Đến đây pipeline semantic của Axiom đã nối khá hoàn chỉnh:

```text
SOURCE
  │
  ▼
LEXER / PARSER
  │
  ▼
AST
  │
  ▼
NAME RESOLUTION ───────── MODULE GRAPH (427)
  │
  ▼
TYPE CHECKING ─────────── GENERICS / TRAITS (426)
  │
  ▼
OWNERSHIP ─────────────── MEMORY MODEL (423)
  │
  ▼
CONTROL FLOW (428)
  │
  ▼
ERROR / PANIC ─────────── FAILURE MODEL (425)
  │
  ▼
ASYNC / THREAD ────────── CONCURRENCY (424)
  │
  ▼
SSA / AXIOM IR
  │
  ▼
ABI LOWERING (421)
  │
  ▼
MACHINE CODE (420)
  │
  ▼
OBJECT / LINKER
  │
  ▼
EXE / ELF / MACH-O / WASM
```

**BOOTSTRAP-428 hoàn tất về mặt kiến trúc.**

---

# BOOTSTRAP-429 — LEXICAL MODEL, SYNTAX, OPERATORS, LITERALS & FORMATTING

Task tiếp theo sẽ khóa **surface language**: lexer, token, identifier, keyword, string/number literals, comments, operator precedence, declaration syntax, generic syntax, trait syntax, module syntax và formatting rules.

Đây là bước cần thiết trước khi khóa parser/AST một cách thực thi được, vì từ 426–428 chúng ta đã xác định semantic nhưng chưa khóa chính xác cách programmer viết chúng.