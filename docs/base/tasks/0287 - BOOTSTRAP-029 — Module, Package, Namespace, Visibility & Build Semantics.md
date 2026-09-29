Tiếp tục.

# BOOTSTRAP-029 — Module, Package, Namespace, Visibility & Build Semantics

Đây là phần rất quan trọng vì nếu thiết kế không tốt, một ngôn ngữ đơn giản có thể biến thành hệ thống build cực kỳ phức tạp.

Tôi đề xuất Axiom đi theo nguyên tắc:

> **Compiler hiểu module; package manager quản lý dependency; build system chỉ là lớp điều phối.**

Không biến ngôn ngữ thành một hệ sinh thái build bắt buộc kiểu “mọi thứ phải đi qua một runtime/build framework khổng lồ”.

---

## 1. Ba khái niệm phải tách biệt

Axiom có:

```text
Module
Package
Workspace
```

### Module

Đơn vị namespace + compilation.

```axiom
module math.vector
```

### Package

Đơn vị phân phối/dependency.

```text
package axiom.math
version 1.2.0
```

Một package có thể chứa nhiều module.

### Workspace

Nhiều package cùng phát triển:

```text
workspace
├── compiler
├── std
├── tools
└── app
```

Workspace không phải language semantic.

---

# 2. Module là đơn vị compiler hiểu

Ví dụ:

```text
src/
├── main.ax
├── math/
│   ├── vector.ax
│   └── matrix.ax
└── io/
    └── file.ax
```

Có thể tương ứng:

```text
app
├── main
├── math.vector
├── math.matrix
└── io.file
```

Compiler xây dependency graph:

```text
main
 ├── math.vector
 ├── math.matrix
 └── io.file
```

Sau đó compile theo graph.

---

# 3. Không dùng textual `#include`

Axiom **không có C-style textual include** trong Core.

Không:

```c
#include "foo.h"
```

Thay bằng:

```axiom
import math.vector
```

Compiler import **module interface/semantic information**, không copy text vào source.

Điều này giúp:

- incremental compilation
- deterministic symbol resolution
- nhanh hơn
- diagnostics tốt hơn
- tránh macro/include explosion.

---

# 4. `import` và `use`

Nên phân biệt hai việc:

```text
import → đưa module vào dependency graph
use    → đưa symbol vào lexical namespace
```

Ví dụ:

```axiom
import math.vector

use math.vector.Vec2
```

Sau đó:

```axiom
let p = Vec2(1, 2)
```

Hoặc không `use`:

```axiom
let p = math.vector.Vec2(1, 2)
```

---

# 5. Không cần namespace declaration dài dòng

Tên module đã là namespace.

```text
math.vector
```

tạo namespace:

```text
math.vector.Vec2
math.vector.dot
math.vector.length
```

Không cần:

```axiom
namespace math {
    namespace vector {
        ...
    }
}
```

---

# 6. Visibility

Core chỉ cần:

```text
private
pub
```

Mặc định:

```text
private
```

Ví dụ:

```axiom
struct Vec2 {
    pub x: f32
    pub y: f32

    fn normalize(self: mut_view<Vec2>) {
        ...
    }
}
```

`Vec2` private nếu không có:

```axiom
pub struct Vec2
```

---

# 7. Visibility theo module

```text
module A
    private X
    pub Y
```

Module khác:

```axiom
import A

use A.Y
```

có thể thấy `Y`, không thấy `X`.

Compiler enforce visibility trước monomorphization/codegen.

---

# 8. Không cần nhiều tầng visibility trong Core v1

Tôi **không khuyến nghị** ngay từ đầu có:

```text
pub(crate)
pub(super)
protected
internal
friend
package-private
```

Chúng làm semantic model phức tạp.

Core:

```text
private
pub
```

là đủ.

Nếu sau này cần `pub(package)` thì thêm bằng extension, không phá model.

---

# 9. Struct field visibility

Mỗi field có visibility riêng:

```axiom
pub struct User {
    pub id: u64
    name: String
}
```

Module ngoài có thể:

```axiom
user.id
```

nhưng không:

```axiom
user.name
```

Điều này cho phép encapsulation mà không cần class.

---

# 10. Function visibility

```axiom
pub fn parse(data: view<[u8]>) -> Result<Message, Error>
```

chỉ `pub` mới trở thành API module.

Private function có thể được compiler tối ưu mạnh hơn vì toàn bộ call graph có thể biết được.

---

# 11. Module interface

Compiler nên tạo một **semantic interface artifact**.

Ví dụ:

```text
math.vector.axmi
```

Không nhất thiết đây là format cuối cùng.

Nó chứa:

```text
module identity
public types
public functions
public traits
public constants
ABI information
generic signatures
visibility
compiler metadata
dependency fingerprints
```

Không chứa toàn bộ implementation nếu không cần.

---

# 12. Interface không phải ABI

Phải phân biệt:

```text
Module Interface
    ↓
compiler semantic compatibility

ABI
    ↓
binary calling/layout compatibility
```

Một module có thể thay implementation:

```text
Vec2.length()
```

mà interface không thay đổi.

Binary ABI lại là vấn đề khác.

---

# 13. Generic module

Ví dụ:

```axiom
pub fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Interface cần lưu:

```text
max
T
constraint: Ord
```

Không cần lưu tất cả instantiation.

Compiler instantiate khi cần:

```text
max<i32>
max<f64>
max<MyType>
```

---

# 14. Incremental compilation

Đây là nơi Axiom có thể mạnh hơn nhiều hệ thống truyền thống.

Mỗi semantic entity có fingerprint.

Ví dụ:

```text
Vec2
 ├── layout fingerprint
 ├── API fingerprint
 ├── implementation fingerprint
 └── dependency fingerprint
```

Nếu chỉ sửa:

```axiom
fn internal_helper()
```

không cần rebuild toàn bộ module consumer nếu public semantic interface không thay đổi.

---

# 15. Public API fingerprint

Compiler có thể tính:

```text
Public API Hash
```

dựa trên:

```text
public types
public fields
public functions
public signatures
public traits
ABI contracts
repr contracts
generic constraints
```

Không dựa vào whitespace/comment.

---

# 16. Dependency fingerprint

Build identity:

```text
Source
+ Compiler version
+ Target
+ Profile
+ Comptime inputs
+ Dependencies
+ Configuration
```

→ compilation identity.

Điều này kết nối trực tiếp với:

```text
ACOMP-25
ACOMP-37
ACOMP-79
```

đã đóng băng ở Comptime.

---

# 17. Comptime dependency phải ảnh hưởng incremental cache

Ví dụ:

```axiom
const VERSION = comptime read_file("version.txt")
```

Compiler phải biết:

```text
module
   ↓
version.txt
```

là dependency.

Nếu file thay đổi:

```text
invalidate
```

Không được cache kết quả cũ.

---

# 18. `@cfg`

`@cfg` dùng để **chọn code**.

Ví dụ:

```axiom
@cfg(os == "windows")
fn platform_name() -> str {
    "Windows"
}
```

và:

```axiom
@cfg(os == "linux")
fn platform_name() -> str {
    "Linux"
}
```

Compiler loại bỏ branch không phù hợp **trước semantic/codegen stages thích hợp**.

---

# 19. `@cfg` khác `comptime`

Rất rõ:

```text
@cfg
    → code selection

comptime
    → computation / declaration generation
```

Ví dụ:

```axiom
@cfg(arch == "x86_64")
```

chọn implementation.

Trong khi:

```axiom
const N = comptime calculate_size()
```

tính giá trị.

Không trộn hai cơ chế.

---

# 20. Target configuration

Compiler cung cấp compile-time target information:

```text
arch
os
environment
ptr_width
endianness
cpu_features
simd_features
gpu_features
```

Nhưng không cho code runtime truy cập trực tiếp nếu không materialize.

---

# 21. Cross compilation

Axiom compiler phải coi target là explicit:

```text
axiom build --target x86_64-linux
axiom build --target aarch64-windows
axiom build --target aarch64-ios
axiom build --target wasm32
```

Compiler semantic pipeline:

```text
Source
  ↓
Target-independent semantics
  ↓
Target configuration
  ↓
Target-specific lowering
```

---

# 22. Không fork source code theo target quá nhiều

Thay vì:

```text
foo_linux.ax
foo_windows.ax
foo_macos.ax
```

có thể:

```axiom
@cfg(os == "linux")
...
```

Nhưng target-specific implementation nên được module hóa:

```text
platform
├── generic
├── windows
├── linux
├── macos
└── wasm
```

---

# 23. Package identity

Package không chỉ là tên folder.

Nó cần identity:

```text
PackageID =
    namespace/name
    + version
    + source identity
```

Ví dụ:

```text
axiom.crypto
```

không đồng nghĩa với bất kỳ folder nào trên disk.

---

# 24. Dependency version

Axiom nên hỗ trợ semantic versioning-style constraints ở package layer:

```text
axiom.crypto >= 2.1 < 3.0
```

Nhưng đây là **package manager semantics**, không phải Core language semantics.

Compiler chỉ nhận package graph đã resolve.

---

# 25. Lockfile

Project application cần reproducible dependency resolution:

```text
axiom.lock
```

ghi:

```text
package
version
source
content hash
dependencies
```

Build reproducible không phụ thuộc việc package registry hiện tại trả version nào.

---

# 26. Dependency source

Package có thể đến từ:

```text
registry
git
local path
archive
vendor
system
```

Nhưng compiler interface thống nhất:

```text
Resolved Package
       ↓
Module Graph
```

Compiler không cần biết package lấy từ đâu.

---

# 27. Không bắt buộc package manager để compile file đơn

Đây là điểm rất quan trọng.

Axiom phải cho phép:

```bash
axiom build main.ax
```

hoặc:

```bash
axiom main.ax
```

để compile một chương trình đơn giản.

Không nên bắt programmer tạo:

```text
project.toml
manifest
lockfile
workspace
registry
```

chỉ để:

```text
Hello World
```

---

# 28. Project mode

Khi project lớn:

```text
axiom build
```

đọc:

```text
axiom.toml
```

hoặc một manifest tương đương.

Manifest chỉ là build/package configuration.

Không phải language syntax.

---

# 29. Đề xuất manifest cực nhỏ

Ví dụ:

```toml
[package]
name = "myapp"
version = "0.1.0"

[dependencies]
http = "2"
json = "1"

[targets]
main = "src/main.ax"
```

Không cần biến manifest thành một programming language.

---

# 30. Workspace

Ví dụ compiler source:

```text
axiom/
├── axiom.toml
├── compiler/
├── frontend/
├── backend/
├── std/
└── tools/
```

Workspace build:

```text
compiler
    ↓
frontend
    ↓
backend
    ↓
tools
```

Package graph và module graph được tách.

---

# 31. Circular dependencies

Module cycle:

```text
A → B
B → A
```

nên **không được phép trong Core module graph**.

Thay vào đó:

```text
A
 ↓
interface
 ↓
B
```

hoặc refactor common module:

```text
A → common
B → common
```

Điều này giúp compilation deterministic.

---

# 32. Package cycle cũng không nên cho phép

```text
package A → B
package B → A
```

reject ở dependency resolver.

Không cần runtime initialization trick để giải quyết dependency cycle.

---

# 33. Module initialization

Đây là vấn đề dễ gây thảm họa.

Tôi đề xuất:

> **Không có arbitrary module-level runtime initialization trong Core.**

Không:

```axiom
var database = connect_database()
```

ở global scope rồi compiler tự quyết định thứ tự initialization.

---

# 34. Global constants

Được:

```axiom
const MAX_SIZE: usize = 1024
```

vì compile-time.

Static storage:

```axiom
static TABLE: [u8; 256] = ...
```

nếu initializer là constant/comptime-materializable.

---

# 35. Runtime static initialization phải explicit

Nếu thực sự cần:

```axiom
static_lazy CONFIG = ...
```

đây là library/runtime abstraction.

Ví dụ:

```text
OnceLock<T>
Lazy<T>
```

Không đưa "global constructor magic" vào Core.

---

# 36. Điều này giúp startup cực nhanh

Executable:

```text
entry
 ↓
main
```

không cần:

```text
runtime init registry
global constructor scan
GC init
reflection init
module init
```

trừ khi binary thực sự sử dụng component đó.

Phù hợp mục tiêu:

> **runtime-free / freestanding / binary nhỏ.**

---

# 37. Symbol export

Visibility không đồng nghĩa binary export.

Đã có quyết định:

```axiom
@export("my_function")
pub fn foo() { ... }
```

Ví dụ:

```text
pub
    ↓
language-level visibility

@export
    ↓
binary symbol visibility
```

Một public function hoàn toàn có thể bị:

- inline
- internalize
- dead-code eliminate

nếu không phải ABI/export boundary.

---

# 38. `extern`

FFI module:

```axiom
extern "C" {
    fn malloc(size: usize) -> *mut u8
}
```

hoặc individual:

```axiom
extern "C" fn foo(...)
```

FFI boundary phải chỉ rõ:

```text
calling convention
representation
ownership
error convention
```

Không suy đoán.

---

# 39. Package không được tự động kéo runtime

Ví dụ:

```text
import math
```

không đồng nghĩa:

```text
link entire std runtime
```

Linker chỉ giữ symbol/object cần thiết.

Đây là **dead-code elimination + component linking**.

---

# 40. Standard library nên chia module nhỏ

Không:

```text
libaxiom_runtime.so
```

khổng lồ.

Thay vào đó:

```text
std.core
std.mem
std.collections
std.text
std.io
std.fs
std.net
std.thread
std.async
std.gpu
std.unicode
```

Program chỉ dùng:

```text
std.text
```

thì không phải kéo:

```text
std.net
std.gpu
std.async
```

---

# 41. Freestanding

Một chương trình có thể:

```axiom
@freestanding
fn kernel_main() { ... }
```

và không có:

```text
OS
allocator
thread runtime
filesystem
network
Unicode runtime
```

nếu không sử dụng.

---

# 42. Build profile

Core nên có một số profile chuẩn:

```text
debug
release
size
freestanding
```

Ví dụ:

```text
debug
    optimization low
    debug info high

release
    optimization high

size
    optimize for size

freestanding
    no hosted runtime assumptions
```

Nhưng đây là compiler/build configuration, không phải language semantics.

---

# 43. Deterministic build

Build identity nên bao gồm:

```text
Source hash
Module API hash
Compiler version
Target
CPU feature configuration
Optimization profile
Comptime dependencies
Package lock
Build configuration
```

Kết quả:

```text
same inputs
    →
same semantic program
```

Compiler vẫn có thể có nondeterministic internal scheduling, nhưng không được thay đổi observable result.

---

# 44. Parallel compilation

Module graph:

```text
       common
      /      \
     A        B
      \      /
       main
```

`A` và `B` có thể compile song song.

Điều này rất quan trọng cho Axiom compiler lớn.

---

# 45. Compilation cache

Cache hierarchy:

```text
Source
 ↓
Parse cache
 ↓
AST/HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
Monomorphized MIR
 ↓
Machine/Object
```

Không nhất thiết cache mọi tầng trong mọi profile.

Compiler quyết định dựa trên cost.

---

# 46. AI-friendly build metadata

Vì Axiom có mục tiêu AI-friendly, module interface nên machine-readable.

Compiler có thể cung cấp:

```text
axiom inspect module
axiom inspect type
axiom inspect symbol
axiom inspect dependencies
axiom inspect ABI
axiom inspect diagnostics
```

AI agent không cần parse hàng nghìn dòng source chỉ để biết:

```text
Vec<T>
    push(T)
    pop() -> Option<T>
    len() -> usize
```

---

# 47. Semantic API metadata

Một module interface có thể biểu diễn:

```text
Type:
    Vec<T>

Traits:
    Copy?
    Clone
    Send
    Share

Methods:
    push
    pop
    reserve

Effects:
    allocation may occur
    mutation
    panic conditions
```

Nhưng lưu ý:

**Không đưa một full effect system vào Core chỉ để phục vụ AI.**

Đây là metadata/compiler query, không phải source-level bureaucracy.

---

# 48. Dependency graph phải là DAG

Formal:

```text
ModuleGraph = DAG
PackageGraph = DAG
```

Compiler có thể topologically sort.

Nếu cycle:

```text
error E-MODULE-CYCLE
```

Diagnostics machine-readable.

---

# 49. Module boundary và optimization

Module boundary **không nên trở thành optimization barrier**.

Compiler có thể:

```text
import A
 ↓
inline A.foo
 ↓
constant fold
 ↓
dead-code eliminate
 ↓
specialize generic
```

nếu visibility/ABI không cấm.

---

# 50. Nhưng ABI boundary là optimization boundary có điều kiện

Ví dụ:

```axiom
@export("foo")
extern "C" fn foo(...)
```

Compiler phải giữ ABI contract.

Bên trong:

```text
inline
vectorize
constant fold
```

vẫn được.

Nhưng không thể thay đổi externally observable calling convention/layout.

---

# 51. Module semantics và class-free design khớp nhau

Axiom không có class nhưng vẫn có encapsulation:

```text
module
 ├── struct
 ├── private fields
 ├── public methods/functions
 ├── private implementation
 └── public trait/API
```

Không cần:

```text
class
private/protected inheritance
friend
```

---

# 52. Invariants BOOTSTRAP-029

```text
AMOD-20   Module is a compiler-visible semantic unit.

AMOD-21   Package is a distribution/dependency unit.

AMOD-22   Workspace is a multi-package development unit.

AMOD-23   Module identity is independent of filesystem layout.

AMOD-24   Textual include is not a Core module mechanism.

AMOD-25   Import establishes module dependency.

AMOD-26   Use establishes lexical symbol visibility.

AMOD-27   Private is the default visibility.

AMOD-28   Public visibility is explicit.

AMOD-29   Field visibility is independently controlled.

AMOD-30   Module graphs are acyclic.

AMOD-31   Package dependency graphs are acyclic.

AMOD-32   Module interface is distinct from binary ABI.

AMOD-33   Public API has a stable semantic identity.

AMOD-34   Implementation changes need not invalidate consumers when API is unchanged.

AMOD-35   Generic declarations are represented in module interfaces.

AMOD-36   Monomorphization occurs only for required instantiations.

AMOD-37   Compilation caches are keyed by semantic dependencies.

AMOD-38   Comptime external inputs participate in cache identity.

AMOD-39   Target configuration participates in compilation identity.

AMOD-40   Package resolution is separate from language semantics.

AMOD-41   Lockfiles can provide reproducible package resolution.

AMOD-42   Single-file programs do not require package manifests.

AMOD-43   Project builds may use a manifest.

AMOD-44   Manifest syntax is not Core language syntax.

AMOD-45   Runtime module initialization is not implicit.

AMOD-46   Constant/static initialization must be compile-time materializable unless explicit runtime abstraction is used.

AMOD-47   Global runtime initialization is not a hidden language mechanism.

AMOD-48   Binary export is distinct from source visibility.

AMOD-49   FFI boundaries require explicit ABI contracts.

AMOD-50   Package imports do not imply linking the entire standard library.

AMOD-51   Standard library components are independently linkable.

AMOD-52   Freestanding programs need not link hosted runtime components.

AMOD-53   Module boundaries do not inherently prevent optimization.

AMOD-54   ABI boundaries preserve declared representation/calling contracts.

AMOD-55   Independent modules may compile in parallel.

AMOD-56   Build results are determined by declared inputs.

AMOD-57   Dependency source identity is part of package resolution.

AMOD-58   Compiler metadata is machine-readable.

AMOD-59   Compiler inspection APIs do not alter language semantics.

AMOD-60   Build configuration is distinct from source semantics.
```

---

# 53. Kiến trúc build Axiom sau quyết định này

Tôi đề xuất pipeline tổng thể:

```text
                 ┌──────────────┐
                 │ Source Files │
                 └──────┬───────┘
                        │
                  Module Resolver
                        │
                 ┌──────▼───────┐
                 │ Module Graph │
                 └──────┬───────┘
                        │
                 Package Resolver
                        │
                 ┌──────▼───────┐
                 │ Package DAG  │
                 └──────┬───────┘
                        │
                Interface Loading
                        │
                 ┌──────▼───────┐
                 │ Semantic HIR │
                 └──────┬───────┘
                        │
                    MIR/Codegen
                        │
                 ┌──────▼───────┐
                 │ Object Files │
                 └──────┬───────┘
                        │
                      Linker
                        │
                 ┌──────▼───────┐
                 │ Native Binary│
                 └──────────────┘
```

Điểm quan trọng là **Package Resolver nằm ngoài compiler semantic core**.

Compiler có thể nhận một resolved module graph trực tiếp.

---

# 54. Tôi chốt một nguyên tắc lớn cho Axiom

Axiom nên có **hai chế độ sử dụng**:

### Chế độ đơn giản

```bash
axiom main.ax
```

và:

```axiom
fn main() {
    println("Hello")
}
```

Thế là đủ.

### Chế độ project

```bash
axiom build
```

với:

```text
axiom.toml
axiom.lock
src/
```

Có dependency, cross compilation, caching, workspace, packaging.

Nhưng **chế độ project không được làm ô nhiễm Core language**.

---

## 55. Một thay đổi kiến trúc quan trọng tôi muốn bổ sung

Với mục tiêu cuối cùng của Axiom là **tự build compiler**, chúng ta không nên thiết kế package manager trước compiler.

Thứ tự bootstrap nên là:

```text
Phase 0
    single-file compiler

Phase 1
    module/import

Phase 2
    multi-file project

Phase 3
    package dependency

Phase 4
    incremental compilation

Phase 5
    package registry/tooling

Phase 6
    self-hosted compiler
```

Như vậy compiler đầu tiên không phải tự xây cả một Cargo/CMake ecosystem mới có thể compile chính nó.

---

# 56. Sau BOOTSTRAP-029

Phần semantic core của Axiom hiện đã khá đầy.

Logical bước tiếp theo tôi đề xuất là:

# **BOOTSTRAP-030 — Error, Panic, Result, Option & Failure Semantics**

Phần này cần chốt rất kỹ:

```text
Result<T,E>
Option<T>
panic
trap
abort
unwind
?
error propagation
Drop khi lỗi
OOM
allocation failure
FFI errors
OS errors
async errors
thread panic
task panic
GPU failure
```

Đặc biệt phải giải quyết một câu hỏi quan trọng:

> **Axiom không dùng exception kiểu C++, nhưng làm sao vẫn có error handling cực kỳ tiện mà không biến `Result` thành hàng đống boilerplate?**

Đây sẽ là phần ảnh hưởng trực tiếp đến **performance, API ergonomics và code AI-generated**, nên nên đóng băng trước khi đi sang standard library.