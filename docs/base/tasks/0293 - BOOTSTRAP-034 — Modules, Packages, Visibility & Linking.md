Tiếp tục với **BOOTSTRAP-034 — Modules, Packages, Visibility & Linking**.

Đây là tầng tổ chức chương trình. Tôi đề xuất Axiom **không sao chép nguyên mô hình Cargo/package/module của Rust hay C++**, mà tách rõ 4 khái niệm: **module → package → artifact → link**.

# BOOTSTRAP-034 — Modules, Packages, Visibility & Linking

## 1. Bốn tầng phải tách biệt

```text
Source File
    ↓
Module
    ↓
Package
    ↓
Artifact
    ↓
Link
```

### Module

Đơn vị namespace + semantic compilation.

### Package

Đơn vị dependency/version/build.

### Artifact

Kết quả biên dịch:

```text
.exe
.dll
.so
.dylib
.a
.lib
.o
.obj
.wasm
```

### Link

Ghép các artifact thành executable/library.

Không được để `package` và `module` trở thành một khái niệm.

---

# 2. Module không nhất thiết = file

Ví dụ:

```text
math/
    vector.ax
    matrix.ax
```

có thể tạo:

```text
module math
```

Một module có thể gồm nhiều source file.

Ngược lại một file cũng có thể chứa nhiều declaration/module con nếu ngôn ngữ cho phép.

### Đề xuất

MVP:

> **Một directory/module namespace có thể chứa nhiều source file; file chỉ là đơn vị vật lý, module là đơn vị semantic.**

Điều này rất hữu ích cho compiler và IDE.

---

# 3. Module declaration

Có thể dùng:

```axiom
module math.vector
```

hoặc để compiler suy ra từ package layout.

Tôi nghiêng về:

```axiom
module math.vector
```

chỉ khi cần explicit module identity.

Thông thường cấu trúc thư mục có thể tự xác định.

---

# 4. Import

Ví dụ:

```axiom
import math.vector
```

Sau đó:

```axiom
let v = math.vector.Vec2(...)
```

Hoặc alias:

```axiom
import math.vector as vec

let v = vec.Vec2(...)
```

---

# 5. Import symbol trực tiếp

Cho phép:

```axiom
import math.vector.Vec2
```

sau đó:

```axiom
let v = Vec2(...)
```

Nhưng không nên mặc định import toàn bộ symbol vào namespace hiện tại.

---

# 6. Wildcard import

Tôi đề xuất:

```axiom
import math.vector.*
```

**không khuyến khích trong Core style**, nhưng có thể cho phép.

Compiler phải phát hiện ambiguity:

```text
A.foo
B.foo
```

nếu:

```axiom
import A.*
import B.*
```

Không được chọn theo thứ tự import.

---

# 7. Import có thứ tự không?

Không.

Đây là nguyên tắc quan trọng:

```text
import A
import B
```

và:

```text
import B
import A
```

phải có cùng semantic result.

Không để thứ tự import ảnh hưởng overload/method resolution.

---

# 8. Visibility

MVP chỉ cần:

```text
private
module
package
public
```

Nhưng tôi đề xuất syntax đơn giản hơn:

```axiom
fn foo()
pub fn bar()
```

và:

```text
private = mặc định
pub = exported semantic API
```

`module/package` visibility có thể bổ sung bằng modifier:

```axiom
module fn ...
package fn ...
```

nếu thực sự cần.

---

# 9. Mặc định private

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

pub fn create() -> Vec2
```

`Vec2` private thì `create()` không thể expose `Vec2` ra ngoài module/package theo API public.

Compiler phải kiểm tra **visibility leakage**.

---

# 10. Public không đồng nghĩa exported symbol

Đã thống nhất ở FFI:

```text
pub
```

là semantic visibility.

Còn:

```text
@export("foo")
```

là native linker symbol.

Hai thứ hoàn toàn khác:

```text
pub
  → programmer/API visibility

@export
  → binary symbol visibility
```

---

# 11. Package

Package là:

```text
source
+ metadata
+ dependency graph
+ build configuration
+ targets
```

Ví dụ:

```text
my_app/
    axiom.toml
    src/
        main.ax
        app.ax
```

Tên file metadata chỉ là ví dụ; **không cần khóa `axiom.toml` ngay**.

---

# 12. Package không phải runtime

Package manager có thể tồn tại:

```text
axiom package
```

nhưng executable cuối cùng không cần package manager.

Sau build:

```text
my_app.exe
```

không chứa:

```text
package manager
dependency resolver
compiler
```

trừ khi application thực sự yêu cầu runtime/library đó.

---

# 13. Dependency graph

Ví dụ:

```text
Application
   ├── graphics
   │      ├── math
   │      └── platform
   └── audio
          └── math
```

Compiler xây DAG:

```text
Package Graph
      ↓
Module Graph
      ↓
Semantic Dependency Graph
```

Không compile đơn giản theo thứ tự file.

---

# 14. Circular module dependency

Ví dụ:

```text
A → B
B → A
```

Không nên cấm tuyệt đối.

Điều cần phân biệt:

### Type-level cycle

Có thể hợp lệ:

```axiom
module A
import B

module B
import A
```

nếu chỉ cần declarations/metadata.

### Initialization cycle

Nguy hiểm.

```text
A.init()
 ↓
B.init()
 ↓
A.init()
```

Phải có quy tắc riêng.

---

# 15. Không có global constructor magic

Để tránh C++-style initialization complexity, Axiom không nên cho:

```text
static object
```

tự động chạy arbitrary constructor trước `main`.

Thay vào đó:

```axiom
fn main() {
    ...
}
```

hoặc explicit initialization API.

---

# 16. Static data

Cho phép:

```axiom
static MAX_SIZE: usize = 1024
```

Nếu immutable:

```text
program lifetime
```

Nếu mutable:

```axiom
static mut ...
```

thì phải có synchronization/system contract.

Tốt hơn, ordinary global mutable state nên rất khó tạo.

---

# 17. Constant vs static

Tách:

```text
const
static
```

### `const`

Compile-time value.

Có thể inline.

Không có storage identity bắt buộc.

### `static`

Có storage identity và program lifetime.

Đây là khác biệt rất quan trọng.

---

# 18. TLS

Cho phép system/runtime layer:

```axiom
@tls
static current: ThreadState
```

Semantic:

```text
one instance per OS thread
```

TLS initialization/destruction phải deterministic.

Không nên biến TLS thành một phần mandatory runtime.

---

# 19. Package API

Package nên có một API surface rõ:

```text
internal
public
exported
```

Compiler có thể tạo:

```text
package interface metadata
```

chứa:

```text
public types
public functions
trait implementations
constants
ABI metadata
generic definitions cần thiết
```

---

# 20. Generic code xuyên package

Đây là điểm quan trọng.

Nếu:

```axiom
pub fn max<T: Ord>(a: T, b: T) -> T
```

package A cung cấp.

Package B sử dụng:

```axiom
max(x, y)
```

compiler B phải có đủ semantic information để instantiate.

Không được chỉ có machine code của package A rồi mất generic definition.

---

# 21. Package interface không nhất thiết là source

Compiler có thể tạo:

```text
package interface
```

tương tự metadata/object nhưng giàu semantic information hơn.

Ví dụ:

```text
.axmi
```

chỉ là tên đề xuất, **chưa freeze extension**.

Nó có thể chứa:

```text
types
traits
generic bodies
visibility
ABI
attributes
dependency hashes
compiler metadata
```

---

# 22. Incremental compilation

Package graph:

```text
A
↓
B
↓
C
```

Nếu sửa implementation private của A:

```text
A implementation changed
```

không nhất thiết rebuild:

```text
B
C
```

nếu public semantic interface không thay đổi.

---

# 23. Semantic fingerprint

Mỗi module/package nên có:

```text
InterfaceHash
ImplementationHash
DependencyHash
TargetHash
CompilerSemanticVersion
```

Ví dụ:

```text
InterfaceHash(A) unchanged
```

→ downstream có thể reuse artifact.

---

# 24. Không cache chỉ dựa trên timestamp

Không:

```text
source modified time
```

làm cache identity.

Phải dựa vào content/semantic identity.

Điều này rất phù hợp với mục tiêu compiler nhanh.

---

# 25. Build graph

Compiler nên có graph:

```text
Source
 ↓
Parse
 ↓
Resolve
 ↓
Typecheck
 ↓
MIR
 ↓
Codegen
```

và cache ở từng tầng.

Không nhất thiết compile lại toàn bộ:

```text
source → machine code
```

mỗi lần.

---

# 26. Package dependency version

Package dependency cần:

```text
name
version
source/artifact identity
target constraints
features
```

Nhưng **version resolution thuộc package manager**, không thuộc Core language semantics.

Compiler chỉ nhận dependency graph đã resolved.

---

# 27. Package manager không phải compiler

Kiến trúc:

```text
axiom
    compiler

axiom-pkg
    dependency resolver

axiom-build
    build orchestration
```

về sau có thể gộp CLI:

```text
axiom build
axiom run
axiom test
axiom package
```

nhưng semantic responsibilities vẫn tách.

---

# 28. Không phụ thuộc build system thứ ba

Mục tiêu cuối:

```text
Axiom source
     ↓
Axiom compiler
     ↓
Axiom linker
     ↓
native executable
```

Không bắt buộc:

```text
CMake
Ninja
MSBuild
Cargo
LLVM
GCC
Clang
```

Các tool này có thể là integration tùy chọn.

---

# 29. Linker

Axiom toolchain cuối cùng cần có khả năng:

```text
Object files
    ↓
Symbol resolution
    ↓
Relocation
    ↓
Section layout
    ↓
Import/export
    ↓
Executable
```

Nhưng compiler và linker nên là hai subsystem.

```text
axiomc
axiomld
```

có thể là hai executable hoặc một executable với subcommands.

---

# 30. Object file

Compiler backend tạo:

```text
.o
.obj
```

Linker nhận:

```text
Axiom object
C object
ASM object
foreign library
system library
```

Do đó Axiom có interoperability ngay cả khi chưa có native linker hoàn chỉnh.

---

# 31. Native linker compatibility

Giai đoạn bootstrap đầu tiên có thể:

```text
Axiom compiler
    ↓
ELF/COFF/Mach-O object
    ↓
system linker
```

Sau này:

```text
Axiom compiler
    ↓
Axiom linker
```

Điều này không mâu thuẫn mục tiêu "không phụ thuộc third-party compiler".

**Bootstrap dependency ≠ final dependency.**

---

# 32. Symbol resolution

Linker cần xử lý:

```text
defined
undefined
weak
local
global
hidden
exported
```

và:

```text
symbol collision
duplicate definition
unresolved symbol
ABI mismatch
```

---

# 33. Static linking

Axiom phải hỗ trợ:

```text
main.o
 ↓
libA.a
 ↓
libB.a
 ↓
system libs
 ↓
app.exe
```

Linker chỉ lấy các object/sections cần thiết nếu có thể.

---

# 34. Dead code elimination

Nếu library có:

```text
1000 functions
```

application dùng:

```text
3
```

final binary không nên bắt buộc chứa 997 function còn lại.

Có thể phối hợp:

```text
module DCE
+
LTO
+
section GC
+
symbol reachability
```

---

# 35. Dynamic linking

Nếu:

```text
libfoo.so
```

được dùng:

```text
app
 ↓
dynamic import
 ↓
libfoo.so
```

thì final executable không chứa implementation của `foo`.

ABI compatibility trở thành runtime contract.

---

# 36. Axiom library metadata

Dynamic/static libraries của Axiom có thể chứa:

```text
ABI version
target
architecture
endianness
feature set
public symbol metadata
type metadata
debug metadata
```

Không phải tất cả đều cần nằm trong executable.

---

# 37. Link-time generic code

Một vấn đề:

```text
package A
generic fn foo<T>()
```

package B instantiate.

Có hai chiến lược:

### Compile-time monomorphization

B tạo machine code.

### Link-time instantiation

A cung cấp generic semantic IR.

Tôi đề xuất:

> **MVP: monomorphization trước codegen ở package sử dụng.**

Đơn giản hơn.

Sau này có thể LTO/generic sharing.

---

# 38. Package-private symbols

Package có thể có:

```text
pub
package
private
```

Nhưng native linker không nhất thiết phải biết package visibility.

Compiler có thể lower:

```text
private
package
```

thành local/hidden symbols.

---

# 39. Module initialization

Không có implicit arbitrary module constructor.

Nếu module cần init:

```axiom
pub fn init(...)
```

hoặc package-level explicit initialization framework sau này.

Điều này tránh:

```text
global initialization order fiasco
```

kiểu C++.

---

# 40. Main entry point

Application profile có:

```axiom
fn main()
```

Compiler biến thành native entry point:

```text
Windows → mainCRTStartup/entry policy
Linux   → _start/main policy
macOS   → platform entry
WASM    → module entry
```

Không expose platform entry details cho application thông thường.

---

# 41. Freestanding

Có profile:

```text
@freestanding
```

hoặc build target configuration.

Khi đó:

```text
no main requirement
no OS runtime
no allocator
no threads
no std
```

Programmer có thể định nghĩa entry point/system ABI.

---

# 42. Library profile

Một package có thể build thành:

```text
static library
dynamic library
object library
```

mà không cần `main`.

---

# 43. Executable profile

Application:

```text
main()
```

Compiler xác định root:

```text
main
 ↓
reachable symbols
 ↓
code/data graph
```

Sau đó DCE.

---

# 44. Dependency features

Không nên compile toàn bộ stdlib vào executable.

Ví dụ:

```text
axiom.std
 ├── io
 ├── fs
 ├── net
 ├── thread
 ├── async
 ├── unicode
 └── gpu
```

Application chỉ dùng:

```text
std.io
```

thì các module còn lại không trở thành mandatory runtime.

---

# 45. Module dependency ≠ runtime dependency

Một module có thể dùng API compile-time:

```text
comptime
```

nhưng generated runtime code không cần package đó.

Do đó compiler graph nên phân biệt:

```text
compile dependency
runtime dependency
link dependency
```

---

# 46. Comptime package

Ví dụ:

```text
schema generator
```

chỉ chạy ở compile time.

Sau khi generate:

```text
generated types
```

được materialize.

Runtime executable không nhất thiết link schema package.

Đây là hệ quả trực tiếp của ACOMP-27/38/84.

---

# 47. Package capabilities

Về sau package metadata có thể khai báo:

```text
requires:
    filesystem
    network
    gpu
```

nhưng đây là **build/runtime capability metadata**, không nên biến thành permission system phức tạp ở Core.

---

# 48. Module path identity

Một module không nên được định danh đơn giản bằng absolute filesystem path.

Nên:

```text
PackageIdentity
+
ModulePath
```

Ví dụ:

```text
com.example.math
+
vector
```

Filesystem chỉ là source location.

Điều này giúp reproducible build.

---

# 49. Rename/move source file

Nếu chuyển:

```text
src/math/vector.ax
```

sang:

```text
src/core/vector.ax
```

nhưng module identity vẫn:

```text
math.vector
```

thì semantic identity không nhất thiết thay đổi.

Cache có thể reuse nếu content/interface/dependencies không đổi.

---

# 50. Package identity

Package nên có:

```text
PackageName
PackageVersion
PackageSourceIdentity
```

Không dùng path local làm identity duy nhất.

---

# 51. Dependency isolation

Package A không được tự động truy cập private implementation của B.

```text
A
 ↓
B public API
```

Không:

```text
A
 ↓
B internal symbol
```

trừ explicit compiler/system feature.

---

# 52. Re-export

Cho phép:

```axiom
pub import math.vector.Vec2
```

để package facade expose:

```text
graphics.Vec2
```

nhưng semantic identity vẫn là:

```text
math.vector.Vec2
```

Không tạo type duplicate.

---

# 53. Namespace collision

Nếu:

```axiom
import A.foo
import B.foo
```

compiler:

```text
AMBIGUOUS_IMPORT
```

Không chọn cái đầu tiên.

Có thể:

```axiom
import A.foo as AFoo
import B.foo as BFoo
```

---

# 54. Trait implementation visibility

Nếu package A định nghĩa:

```axiom
trait Display
```

package B:

```axiom
impl Display for MyType
```

thì trait solver phải biết implementation theo package visibility/coherence rules đã thiết kế.

Không cho dependency order thay đổi kết quả trait resolution.

---

# 55. Orphan/coherence

Tiếp tục rule từ generics:

Package chỉ được định nghĩa impl nếu:

```text
trait owned by current package
OR
type owned by current package
```

Điều này tránh:

```text
Package A
    Trait T

Package B
    Type X

Package C
    impl T for X

Package D
    another impl T for X
```

gây ambiguity toàn hệ thống.

---

# 56. Linker và ODR

Axiom không nên có C++-style ODR phức tạp.

Compiler phải đảm bảo:

```text
one semantic definition
```

cho mỗi exported symbol.

Nếu duplicate:

```text
LINK_DUPLICATE_SYMBOL
```

trừ explicit weak/linker contract.

---

# 57. Symbol versioning

Có thể hỗ trợ về sau:

```text
foo@AXIOM_1
foo@AXIOM_2
```

nhưng chưa cần Core syntax.

System linker layer xử lý.

---

# 58. Build target

Package build phải phân biệt:

```text
target
host
build
```

Ví dụ:

```text
Host:
    Windows x64

Target:
    Linux ARM64
```

Comptime compiler tools chạy trên Host.

Generated application chạy Target.

Đây sẽ rất quan trọng cho cross compilation.

---

# 59. Cross compilation

Kiến trúc:

```text
                 ┌── x86_64 Windows
Axiom source ────┼── x86_64 Linux
                 ├── ARM64 Linux
                 ├── ARM64 Android
                 ├── ARM64 macOS/iOS
                 └── WASM
```

Compiler không cần chạy trên target.

---

# 60. Build profiles

Nên có khái niệm:

```text
debug
release
freestanding
test
bench
```

nhưng đây là build-system configuration, không phải Core language.

---

# 61. Tests không phải module đặc biệt

Test function có thể là ordinary Axiom function với attribute:

```axiom
@test
fn test_add() {
    ...
}
```

Compiler/test runner phát hiện metadata.

Không cần test runtime luôn được link vào production executable.

---

# 62. Package artifact reproducibility

Artifact identity nên phụ thuộc:

```text
source content
dependencies
compiler semantic version
target
compiler flags ảnh hưởng semantics
comptime inputs
ABI
```

không phụ thuộc:

```text
absolute path
timestamp
machine username
```

trừ khi programmer explicit yêu cầu.

---

# 63. Link reproducibility

Nếu muốn reproducible binary:

```text
timestamp
build path
random build ID
```

phải được kiểm soát.

Debug info có thể chứa source path được remap.

---

# 64. Kiến trúc compiler

Sau task này compiler sẽ có graph:

```text
                    Workspace
                       │
                  Package Graph
                       │
                 Module Graph
                       │
              Semantic Dependency
                       │
                 Typed HIR
                       │
                     MIR
                       │
               Package Artifact
                       │
                  Object File
                       │
                 ┌─────┴─────┐
                 │           │
             Static       Dynamic
             Link          Link
                 │           │
                 └─────┬─────┘
                       ↓
                 Native Artifact
```

---

# 65. Một quyết định rất quan trọng

Tôi đề xuất Axiom **không coi source file là đơn vị compilation tối cao**.

Đơn vị compiler nên là:

```text
Package
    ↓
Module
    ↓
Semantic Unit
```

Còn source file chỉ là:

```text
physical representation
```

Điều này giúp:

- IDE tốt hơn
- incremental compilation tốt hơn
- multi-file module
- generated code
- comptime
- package interface
- parallel compilation
- AI tooling

---

# 66. Invariants BOOTSTRAP-034

```text
AMOD-20   Module identity is distinct from source-file identity.

AMOD-21   Package identity is distinct from filesystem location.

AMOD-22   Package is a dependency/build unit.

AMOD-23   Module is a semantic namespace unit.

AMOD-24   Artifact is distinct from package.

AMOD-25   Linking is distinct from semantic compilation.

AMOD-26   Import order does not affect semantics.

AMOD-27   Ambiguous imports are compile errors.

AMOD-28   Visibility is deterministic.

AMOD-29   Private is the default visibility.

AMOD-30   Public visibility does not imply native symbol export.

AMOD-31   Native symbol export requires an explicit export contract.

AMOD-32   Package boundaries do not bypass visibility.

AMOD-33   Re-export does not create a duplicate type identity.

AMOD-34   Generic definitions required by downstream compilation remain semantically available.

AMOD-35   Package interface metadata may replace source access for downstream compilation.

AMOD-36   Interface identity is distinct from implementation identity.

AMOD-37   Incremental compilation is content/semantic based.

AMOD-38   Timestamps are not semantic cache identity.

AMOD-39   Module dependency order does not define semantic resolution order.

AMOD-40   Type-level module cycles may be permitted.

AMOD-41   Runtime initialization cycles require explicit handling.

AMOD-42   Arbitrary module constructors are not implicit.

AMOD-43   const has no mandatory storage identity.

AMOD-44   static has storage identity.

AMOD-45   TLS has per-thread storage identity.

AMOD-46   TLS does not imply mandatory global runtime support.

AMOD-47   Runtime dependencies are distinct from compile-time dependencies.

AMOD-48   Comptime-only dependencies need not enter the runtime artifact.

AMOD-49   Package dependency resolution is outside Core language semantics.

AMOD-50   Compiler consumes a resolved dependency graph.

AMOD-51   Package features do not implicitly become runtime dependencies.

AMOD-52   Unused library functionality may be removed.

AMOD-53   Reachability participates in dead-code elimination.

AMOD-54   Static linking may eliminate unreachable sections.

AMOD-55   Dynamic linking establishes an explicit binary dependency.

AMOD-56   Symbol identity includes ABI-relevant information.

AMOD-57   Duplicate strong symbol definitions are link errors.

AMOD-58   Cross-compilation separates host and target environments.

AMOD-59   Build tools are not semantic compiler dependencies.

AMOD-60   Axiom source can eventually compile without a third-party compiler.

AMOD-61   Native object generation is an Axiom compiler responsibility.

AMOD-62   Linking is a separate toolchain responsibility.

AMOD-63   An Axiom linker may eventually replace system linkers.

AMOD-64   Bootstrap dependencies are not final toolchain dependencies.

AMOD-65   Package artifacts carry target identity.

AMOD-66   Package artifacts carry compiler/ABI compatibility identity.

AMOD-67   Reproducible builds exclude undeclared environmental identity.

AMOD-68   Absolute filesystem paths are not semantic module identity.

AMOD-69   Visibility leakage is rejected at compile time.

AMOD-70   Coherence rules apply across package boundaries.

AMOD-71   Trait resolution cannot depend on import order.

AMOD-72   Package-private implementation details are not public ABI.

AMOD-73   Stable ABI requires an explicit ABI version.

AMOD-74   C ABI stability is distinct from Axiom ABI stability.

AMOD-75   Build configuration does not redefine language semantics.
```

---

# Trạng thái kiến trúc sau 034

Đến đây Axiom đã có một chuỗi khá hoàn chỉnh:

```text
TYPE
 ↓
OWNERSHIP
 ↓
CAPABILITY
 ↓
MEMORY
 ↓
REPRESENTATION
 ↓
ABI
 ↓
FFI
 ↓
MODULE
 ↓
PACKAGE
 ↓
OBJECT
 ↓
LINK
 ↓
EXECUTABLE
```

Điểm quan trọng là **không có tầng nào bắt buộc phải kéo theo runtime lớn**.

Ví dụ một chương trình:

```axiom
fn main() {
    let x = 10
    println(x)
}
```

không vì có:

- module
- package
- ownership
- async support
- thread support
- reflection
- GPU
- allocator

mà executable phải chứa toàn bộ những thứ đó.

Compiler chỉ link những capability/runtime component thực sự cần.

---

## Tiếp theo: BOOTSTRAP-035

Task kế tiếp nên là:

**Error Handling, Panic, Unwind/Abort & Failure Semantics**

Phần này cần chốt dứt điểm một số vấn đề rất quan trọng còn nằm rải rác:

```text
Result
Option
?
panic
trap
abort
unwind
catch có hay không
destructor khi panic
FFI boundary
async failure
thread failure
process failure
OOM
allocation failure
fatal compiler/runtime errors
```

Đặc biệt tôi sẽ xử lý câu hỏi lớn: **Axiom có cần `try/catch/exception` hay hoàn toàn không?** Và làm sao có error handling mạnh mà vẫn giữ được mục tiêu **nhẹ, predictable và không có exception runtime bắt buộc**.