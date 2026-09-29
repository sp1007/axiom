Tiếp theo tôi đề xuất chốt **Module / Package / Build / Link System v0.1**. Đây là phần dễ bị đánh giá thấp, nhưng với mục tiêu của Axiom — **native executable, không phụ thuộc compiler bên thứ ba về lâu dài, binary nhỏ, incremental build, cross-platform** — nó quan trọng gần ngang type system.

Tôi sẽ giữ nguyên nguyên tắc:

> **Module là semantic boundary. Package là distribution boundary. Object file là compilation/link boundary.**

Không trộn ba thứ này thành một.

---

# 1. Ba tầng cần tách biệt

```text
                    AXIOM PROJECT
                         │
                 ┌───────┴───────┐
                 │               │
              PACKAGE          MODULE
                 │               │
          distribution       semantics
                 │               │
                 └──────┬────────┘
                        │
                  COMPILATION UNIT
                        │
                      OBJECT
                        │
                      LINK
                        │
                 native executable
```

### Module

Quyết định:

- namespace
- visibility
- import/export
- name resolution
- dependency graph ở mức source

### Package

Quyết định:

- project
- version
- dependency
- source set
- target configuration
- build metadata

### Object

Quyết định:

- machine code
- symbols
- relocations
- sections
- debug info

---

# 2. Module không nên giống C++ header

Tôi muốn tránh:

```text
foo.h
foo.cpp
```

và tránh cả:

```text
#include "foo.h"
```

Axiom nên compile module trực tiếp.

Ví dụ:

```text
src/
    main.ax
    math.ax
    geometry.ax
```

`math.ax`:

```axiom
module math

pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

`main.ax`:

```axiom
import math

fn main() {
    let x = math.add(10, 20)
}
```

Không text substitution.

Không duplicate parsing.

Không macro preprocessing bắt buộc.

---

# 3. `import` là semantic dependency

```axiom
import math
```

compiler tạo:

```text
main
  │
  └── math
```

Không phải:

```text
copy source math vào main
```

Điều này giúp:

- incremental compilation
- caching
- deterministic build
- IDE indexing
- AI tooling
- dependency analysis

---

# 4. Visibility cực kỳ đơn giản

Tôi đề xuất chỉ cần:

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
struct User {
    id: u64
    name: Text
}

pub fn create_user(...) -> User
```

Nếu field không `pub`, module khác không được truy cập trực tiếp.

Không cần:

```text
protected
internal
friend
package-private
```

Đặc biệt **không có `friend`**.

---

# 5. Nhưng struct private field vẫn có thể có public method

Ví dụ:

```axiom
struct User {
    id: u64
    name: Text
}

impl User {
    pub fn id(self: view<User>) -> u64 {
        self.id
    }
}
```

Module ngoài:

```axiom
let id = user.id()
```

Điều này tạo abstraction mà không cần class.

---

# 6. Public API phải là semantic API

Compiler nên có thể tạo:

```text
Public API Surface
```

từ module.

Ví dụ:

```text
math
 ├── pub fn add
 ├── pub fn sqrt
 ├── pub struct Vec2
 │      ├── pub x
 │      └── pub y
 └── private helper
```

Private symbols không trở thành dependency ABI của package khác.

Đây sẽ rất hữu ích cho:

- incremental compilation
- ABI analysis
- documentation
- IDE
- AI agent.

---

# 7. Module path

Tôi nghiêng về:

```axiom
import std.io
import std.math
import graphics.renderer
```

Thay vì:

```axiom
import ../../../foo/bar
```

Filesystem chỉ là một implementation mapping.

Semantic identity:

```text
package::module
```

Ví dụ:

```text
mygame::render
```

---

# 8. Package identity

Package cần:

```text
name
version
source
dependencies
targets
features
build configuration
```

Ví dụ conceptually:

```text
axiom.toml
```

```toml
[package]
name = "mygame"
version = "1.0.0"

[dependencies]
math = "..."
graphics = "..."
```

Tôi chưa muốn freeze format cụ thể thành TOML. Đây chỉ là **đề xuất syntax**.

Quan trọng là semantic model.

---

# 9. Dependency không nên chỉ là version

Package dependency cần ít nhất:

```text
Package ID
Version
Source
Checksum
```

Ví dụ:

```text
math
version = 1.4.2
source = registry/...
hash = SHA-256(...)
```

Mục tiêu:

```text
same source
+
same compiler
+
same configuration
=
same build inputs
```

→ reproducibility.

---

# 10. Lock file

Project application nên có:

```text
axiom.lock
```

Nó đóng băng dependency graph:

```text
mygame
 ├── graphics 2.1.0
 │    └── math 1.7.2
 └── audio 3.0.1
      └── math 1.7.2
```

Nếu dependency graph thay đổi:

```text
lock file changes
```

Compiler/build system có thể phát hiện.

---

# 11. Không để compiler tự tải package

Tôi muốn tách:

```text
axiom compiler
```

và:

```text
axiom package/build tool
```

Compiler có nhiệm vụ:

```text
source → object
```

Build tool có nhiệm vụ:

```text
dependency resolution
source graph
cache
build plan
link invocation
```

Điều này cực kỳ quan trọng để giữ compiler nhỏ.

---

# 12. `axiom build`

CLI conceptually:

```bash
axiom build
```

Pipeline:

```text
project manifest
       ↓
dependency resolver
       ↓
build graph
       ↓
module graph
       ↓
incremental compiler
       ↓
object files
       ↓
linker
       ↓
executable
```

---

# 13. Compiler không nên luôn compile toàn bộ project

Ví dụ:

```text
1000 modules
```

sửa:

```text
module A
```

thì không được:

```text
compile 1000 modules
```

Compiler cache:

```text
A
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
object
```

và các module không bị ảnh hưởng được reuse.

---

# 14. Nhưng dependency phải phân biệt API và implementation

Đây là tối ưu rất quan trọng.

Ví dụ:

```text
A
 ├── public API
 └── private implementation
```

Nếu chỉ sửa private implementation:

```text
B
```

không cần compile lại chỉ vì:

```text
A private source hash changed
```

Nếu public semantic interface thay đổi:

```text
B
```

có thể cần recompile.

Do đó compiler cần tạo:

```text
Semantic Interface Fingerprint
```

hay gọi ngắn là:

```text
SIF
```

---

# 15. SIF

SIF chứa những thứ ảnh hưởng consumer:

```text
public types
public functions
public trait implementations
public constants
public layouts nếu ABI-visible
generic definitions cần thiết
visibility
ABI contract
```

Không chứa implementation detail không observable.

Ví dụ:

```axiom
pub fn add(a: i32, b: i32) -> i32
```

đổi:

```text
loop implementation
→ SIMD
→ different algorithm
```

không nhất thiết làm consumer compile lại.

---

# 16. Generic cần xử lý đặc biệt

Đây là chỗ phức tạp.

```axiom
pub fn max<T: Comparable>(a: T, b: T) -> T
```

Consumer có thể instantiate:

```text
max<i32>
```

Compiler cần source/IR generic definition.

Có hai chiến lược:

### A. Export generic IR

```text
package A
 └── generic HIR/MIR
```

Consumer specialize.

### B. Compiler tạo specialization trong package A

Nhưng không biết trước consumer sẽ dùng type nào.

Vì vậy tôi nghiêng mạnh về:

> **Generic public definitions được export dưới dạng typed generic IR/metadata, không phải machine code.**

Consumer compiler specialize khi cần.

---

# 17. Nhưng không export toàn bộ compiler internals

Không nên package chứa:

```text
raw AST
parser state
compiler debug internals
```

Thay vào đó:

```text
Axiom Interface Artifact
```

chứa:

```text
Public semantic interface
+
generic metadata
+
trait metadata
+
ABI metadata
+
source mapping optional
```

Ví dụ:

```text
foo.axiom-iface
```

Tên chỉ là đề xuất.

---

# 18. ABI boundary

Nếu:

```text
Package A → Package B
```

và cả hai compile cùng compiler/toolchain:

```text
Axiom ABI
```

có thể dùng native ABI.

Nhưng nếu muốn stable binary compatibility:

```text
@abi(C)
```

hoặc:

```text
@abi(system)
```

hoặc sau này:

```text
@abi("axiom-v1")
```

Không nên tuyên bố:

> Axiom native ABI luôn stable.

Nó sẽ khóa compiler quá sớm.

---

# 19. Dynamic library

Axiom phải hỗ trợ:

```text
Windows:
.dll

Linux:
.so

macOS:
.dylib
```

nhưng dynamic library không nên là semantic primitive.

Nó là:

```text
link/deployment mechanism
```

Ví dụ:

```axiom
@export("plugin_init")
pub extern @abi(C) fn plugin_init(...)
```

Plugin host:

```axiom
extern @abi(C) fn plugin_init(...)
```

Đây là boundary rõ ràng.

---

# 20. Static library

Tương tự:

```text
.lib
.a
```

là artifact packaging/linking.

Compiler có thể xuất:

```text
object
static library
dynamic library
executable
```

nhưng semantic language không phụ thuộc vào format.

---

# 21. Linker

Ban đầu:

```text
Axiom compiler
      ↓
native object
      ↓
system linker
```

Ví dụ:

```text
Windows → PE/COFF ecosystem
Linux → ELF
macOS → Mach-O
```

Về lâu dài:

```text
Axiom compiler
      ↓
Axiom object writer
      ↓
Axiom linker
      ↓
native executable
```

Điều này phù hợp mục tiêu **không phụ thuộc third-party compiler/toolchain trong final state**.

Nhưng tôi muốn phân biệt:

> **Không phụ thuộc compiler bên thứ ba ≠ không bao giờ được dùng linker hệ điều hành.**

Trong bootstrap, dùng system linker hoàn toàn hợp lý.

---

# 22. Axiom linker về lâu dài

Nếu tự xây linker:

```text
Object files
    ↓
symbol resolution
    ↓
relocation
    ↓
section layout
    ↓
dead stripping
    ↓
TLS
    ↓
imports/exports
    ↓
PE/ELF/Mach-O
```

Nhưng **không nên làm ngay**.

Compiler frontend + MIR + backend + object writer quan trọng hơn.

---

# 23. Dead code elimination

Có hai tầng:

### Compiler

```text
unused function
→ eliminate
```

### Linker

```text
unused object section
→ eliminate
```

Do đó stdlib có thể lớn:

```text
std
 ├── IO
 ├── networking
 ├── unicode
 ├── collections
 ├── threading
 ├── async
 └── ...
```

nhưng:

```axiom
fn main() {}
```

không kéo tất cả vào binary.

---

# 24. Runtime component linking

Đây là nơi thiết kế Runtime v0.1 trước đó kết nối rất đẹp.

Ví dụ:

```axiom
fn main() {
    let x = 10
}
```

dependency:

```text
main
 └── startup
```

Không:

```text
GC
thread runtime
async runtime
unicode runtime
reflection runtime
```

Nếu:

```axiom
spawn(...)
```

thì:

```text
main
 └── thread component
```

Nếu:

```axiom
Text.graphemes()
```

thì có thể link Unicode component nếu implementation yêu cầu.

---

# 25. Build profile

Nên có ít nhất:

```text
debug
release
size
```

### debug

```text
-O0 / low optimization
debug info
assertions
checks
trace-friendly
```

### release

```text
optimization
inlining
vectorization
LTO tùy cấu hình
```

### size

```text
optimize binary size
dead stripping
merge functions
minimize runtime
```

Không nên có hàng trăm profile mặc định.

---

# 26. Cross compilation

Target phải là một phần của build configuration:

```text
x86_64-windows
x86_64-linux
aarch64-linux
aarch64-macos
aarch64-ios
aarch64-android
wasm32
```

Nhưng target triple cụ thể có thể theo chuẩn riêng sau này.

Compiler:

```text
source
 ↓
target-independent MIR
 ↓
target config
 ↓
target backend
```

Không cần source code biết CPU nếu không sử dụng platform-specific API.

---

# 27. Target capability

Không nên chỉ có:

```text
if windows
if linux
```

trong language core.

Nên có compile-time target information:

```axiom
if @target.os == "windows" {
    ...
}
```

nhưng tôi nghiêng về việc đưa cơ chế này vào **build/platform layer**, không phải general-purpose macro system.

Ví dụ:

```text
platform/windows.ax
platform/linux.ax
```

Build system chọn module phù hợp.

---

# 28. Conditional compilation

Cần có, nhưng phải đơn giản.

Ví dụ:

```axiom
@when(os == "windows")
fn foo() { ... }
```

và:

```axiom
@when(arch == "aarch64")
```

Không nên biến nó thành:

```text
#if
#ifdef
#elif
#define
macro
```

như C.

---

# 29. Features

Package có thể có feature:

```text
features:
    networking
    gui
    gpu
```

Nhưng feature không được làm semantic type system thay đổi tùy tiện.

Ví dụ không nên:

```text
feature X → thay đổi ownership rules
```

Feature chỉ chọn:

```text
modules
implementations
dependencies
platform code
```

---

# 30. Reproducible build

Đây nên là mục tiêu chính thức.

Build artifact phải có thể truy nguyên:

```text
compiler version
compiler commit
source hash
dependency hashes
target
optimization profile
build flags
environment inputs
```

Không nên embed:

```text
absolute local path
username
timestamp
machine-specific random data
```

trừ khi explicit.

---

# 31. Build cache

Cache key conceptually:

```text
Hash(
    source semantic input
    compiler semantic version
    target
    optimization profile
    feature set
    dependency interface hashes
)
```

→ artifact.

Điều này cho phép local cache:

```text
~/.axiom/cache/
```

và sau này remote cache.

---

# 32. Không để build cache ảnh hưởng semantics

Nếu cache lỗi:

```text
wrong cache hit
```

không được làm chương trình compile thành semantics khác.

Cache phải là:

```text
optimization
```

không phải:

```text
source of truth
```

Có thể verify artifact metadata/hash.

---

# 33. Package manager

Tôi muốn package manager có kiến trúc:

```text
Resolver
Registry
Fetcher
Verifier
Cache
```

Nhưng package manager không thuộc compiler.

Có thể sau này:

```text
axiom pkg add foo
axiom pkg update
axiom pkg fetch
```

Compiler chỉ nhận:

```text
resolved dependency graph
```

---

# 34. Security của dependency

Về sau cần:

```text
checksum
signature
trusted registry
offline mode
vendor mode
```

Đặc biệt:

```bash
axiom build --offline
```

phải build được nếu dependency đã cached/vendor.

Điều này cực kỳ quan trọng cho systems/embedded.

---

# 35. Vendoring

Cho phép:

```text
vendor/
    foo/
    bar/
```

Build không cần internet.

Đây cũng giúp:

- reproducibility
- enterprise
- embedded
- air-gapped environment
- compiler bootstrap.

---

# 36. Freestanding

Package/build system phải hỗ trợ:

```text
freestanding
```

Ví dụ:

```text
kernel
bootloader
embedded firmware
UEFI
bare metal
```

Không được tự động link:

```text
OS runtime
stdio
heap
thread
```

Programmer có thể chọn:

```text
@profile(freestanding)
```

hoặc target profile.

---

# 37. `main` không phải bắt buộc

Hosted application:

```axiom
fn main() -> i32 {
    0
}
```

Freestanding:

```axiom
@entry
fn kernel_start(...) {
    ...
}
```

Compiler không nên giả định mọi chương trình đều có `main`.

---

# 38. Build graph

Cuối cùng toàn bộ hệ thống nên có graph:

```text
                    PACKAGE
                       │
                 dependency graph
                       │
                 ┌─────┴─────┐
                 │           │
              MODULE       MODULE
                 │           │
              semantic dependency
                 │
              interface
                 │
                 ↓
             Typed HIR
                 ↓
                MIR
                 ↓
            Verified MIR
                 ↓
               LIR
                 ↓
              OBJECT
                 │
          ┌──────┴──────┐
          │             │
      static lib    dynamic lib
          │             │
          └──────┬──────┘
                 ↓
               LINK
                 ↓
          EXE / ELF / Mach-O
```

---

# 39. Một quyết định rất quan trọng: không tạo "Axiom VM"

Axiom không nên có:

```text
source
 ↓
bytecode
 ↓
Axiom VM
```

làm execution model mặc định.

Semantic Oracle/MIR Interpreter mà ta đã thiết kế trước đó chỉ là:

```text
testing
verification
reference semantics
```

Còn production:

```text
MIR
 ↓
native machine code
```

Điều này phù hợp mục tiêu hiệu năng và binary nhỏ.

---

# 40. Module/package invariants

Tôi đề xuất freeze thêm:

```text
APKG-01
Module is a semantic namespace boundary.

APKG-02
Package is a distribution/dependency boundary.

APKG-03
Object file is a compilation/link boundary.

APKG-04
Import is semantic dependency, not textual inclusion.

APKG-05
Private implementation does not become public API.

APKG-06
Public semantic interface is sufficient for consumer compilation
except required generic metadata.

APKG-07
Generic public definitions may be exported as typed generic artifacts.

APKG-08
Native Axiom ABI is not implicitly stable across compiler versions.

APKG-09
Stable foreign ABI must be explicitly selected.

APKG-10
Dynamic dispatch metadata exists only when dynamic dispatch is used.

APKG-11
Unused runtime/library components must not create mandatory binary cost.

APKG-12
Build cache cannot alter language semantics.

APKG-13
Dependency resolution is outside core compiler semantics.

APKG-14
Compiler must support dependency-free/freestanding compilation.

APKG-15
Cross-compilation does not change source semantics.

APKG-16
Conditional platform code is explicit.

APKG-17
Reproducible builds are a language ecosystem goal.

APKG-18
Final native artifacts use platform-compatible object/executable formats.

APKG-19
Axiom semantics do not depend on a third-party compiler.

APKG-20
Bootstrap may temporarily use external assemblers/linkers/backends.
```

---

## 41. Kiến trúc Axiom hiện tại đã khá hoàn chỉnh

Nếu gom tất cả những gì ta đã chốt, tôi thấy Axiom hiện có một trục rất rõ:

```text
                    AXIOM SOURCE
                         │
              ┌──────────┴──────────┐
              │                     │
           MODULE                 PACKAGE
              │                     │
              └──────────┬──────────┘
                         ↓
                        AST
                         ↓
                        HIR
                         ↓
               Type / Trait / Generic
                         ↓
                        MIR
                         ↓
        ┌────────────────┼────────────────┐
        │                │                │
    Ownership        Capability       Concurrency
        │                │                │
        └────────────────┼────────────────┘
                         ↓
                    Verified MIR
                         ↓
                  Drop / Async Lowering
                         ↓
                    Optimization
                         ↓
                       LIR
                         ↓
                  Target Lowering
                         ↓
                    Machine IR
                         ↓
                  Register Allocation
                         ↓
                   Machine Encoder
                         ↓
                    Object Writer
                         ↓
                  ┌──────┴──────┐
                  │             │
                Link          Library
                  │
                  ↓
             Native Binary
```

Và điều đáng chú ý là **không có GC, VM, object header, class hierarchy, mandatory runtime, mandatory heap, borrow syntax, hay third-party compiler nằm trên đường đi bắt buộc**.

### Phần tiếp theo tôi muốn đi sâu nhất

Tôi sẽ chuyển sang **ABI + FFI + Object/Executable Generation v0.1**, bởi vì đây là nơi mục tiêu:

> **"Axiom phải thực sự tự tạo EXE/ELF/Mach-O, không chỉ compile qua LLVM"**

bắt đầu trở thành kiến trúc kỹ thuật cụ thể.

Ở phần đó cần thiết kế cả **calling convention, struct return, register classification, symbol mangling, relocation, TLS, unwind, stack frame, C ABI, syscall/OS ABI và cuối cùng là PE/ELF/Mach-O/WASM backend**. Đây cũng là nơi ta có thể kiểm tra thực tế liệu kiến trúc hiện tại có thực sự đạt mục tiêu **C/C++ performance nhưng abstraction đơn giản hơn** hay không.