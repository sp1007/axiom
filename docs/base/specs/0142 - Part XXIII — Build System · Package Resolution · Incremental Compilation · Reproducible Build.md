# Part XXIII — Build System · Package Resolution · Incremental Compilation · Reproducible Build

Part XXII đã chốt **semantic model** của package/module. Bây giờ cần thiết kế hệ thống biến source code thành artifact mà không biến Axiom thành một "ngôn ngữ phụ thuộc vào Cargo/CMake/MSBuild".

Mục tiêu:

> **Axiom compiler và Axiom build system cuối cùng phải là một hệ thống native độc lập.**

Nhưng bootstrap ban đầu vẫn có thể dùng compiler/backend bên ngoài như một bước chuyển tiếp.

---

# XXIII.1. Ba tầng phải tách biệt

Axiom build system nên chia thành:

```text
                    BUILD
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
      Resolution   Compilation   Packaging
          │           │           │
       package       compiler     artifact
       graph         pipeline     metadata
```

### Resolution

Xác định:

```text
package nào
version nào
source nào
```

### Compilation

Biến:

```text
source → machine artifact
```

### Packaging

Đóng gói:

```text
library
executable
package
headers
debug symbols
metadata
```

Không nên để package manager biết semantics của MIR.

---

# XXIII.2. `axiom.toml`

File manifest chính:

```toml
[package]
name = "myapp"
version = "0.1.0"

[dependencies]
math = "2.1"
graphics = "1.4"
```

Target:

```toml
[targets]
windows = true
linux = true
```

Feature:

```toml
[features]
gpu = ["graphics/gpu"]
```

Profile:

```toml
[profile.release]
optimization = "speed"
panic = "abort"
```

---

# XXIII.3. Manifest Không Phải Build Script

`axiom.toml` là **data declaration**, không phải chương trình.

Không cho:

```toml
run = "rm -rf ..."
```

hoặc:

```toml
build = arbitrary executable
```

theo kiểu mặc định.

Nếu cần custom generation:

```text
comptime
+
explicit build capability
```

---

# XXIII.4. Package Identity

Resolver phải tạo identity:

```text id="hmnqgi"
PackageIdentity {
    name
    version
    source
    content_hash
}
```

Ví dụ:

```text id="0fy9v5"
math
2.1.0
registry
sha256:abcd...
```

Không dùng chỉ:

```text id="math@2.1.0"
```

vì cùng version có thể đến từ source khác.

---

# XXIII.5. Dependency Specification

Cho phép:

```toml
[dependencies]
math = "2.1"
foo = { version = "1.3", source = "git" }
bar = { path = "../bar" }
```

Nhưng sau resolution, lock file phải biến thành identity cụ thể.

---

# XXIII.6. `axiom.lock`

Ví dụ:

```toml
[[package]]
name = "math"
version = "2.1.3"
source = "registry"
checksum = "sha256:..."

[[package]]
name = "foo"
version = "1.4.0"
source = "git"
revision = "..."
checksum = "..."
```

Build với lock file:

```text id="mlj2m5"
dependency resolution = deterministic
```

---

# XXIII.7. Resolver

Resolver phải giải quyết:

```text
A → B ^1
A → C
C → B ^2
```

thành:

```text
B@1
B@2
C
A
```

nếu hai version có thể coexist.

Không ép toàn workspace dùng một version chỉ để đơn giản resolver.

---

# XXIII.8. Type Identity Với Multiple Versions

Nếu:

```text id="y5w91n"
math@1::Vec2
math@2::Vec2
```

thì:

```text id="0j72tw"
math@1::Vec2 != math@2::Vec2
```

Không implicit convert.

Nếu cần adapter:

```axiom id="o9f7xy"
fn convert(x: math1.Vec2) -> math2.Vec2
```

là ordinary function.

---

# XXIII.9. Resolver Không Được Dựa Vào Source Order

Không:

```text id="b3x9pi"
"package nào xuất hiện trước thì thắng"
```

Resolution phải deterministic độc lập với filesystem order.

---

# XXIII.10. Package Graph

Ví dụ:

```text
app
├── ui
│   └── math@2
├── engine
│   └── math@1
└── io
```

Resolver tạo DAG semantic.

Compiler sau đó tạo build graph.

---

# XXIII.11. Package Graph ≠ Build Graph

Package graph:

```text
app → engine
```

Build graph có thể:

```text
engine
 ├── comptime generator
 ├── generated source
 ├── shader
 ├── resource compiler
 ├── Axiom compilation
 └── linker
```

Do đó build system phải hỗ trợ artifact dependencies.

---

# XXIII.12. Artifact Types

Axiom build system có semantic artifact:

```text
source
generated-source
object
static-library
shared-library
executable
debug-info
resource
shader
metadata
```

Artifact dependency phải explicit.

---

# XXIII.13. Compilation Unit

Không nhất thiết:

```text
1 file → 1 compilation unit
```

Compiler có thể compile:

```text
module
package
SIF unit
```

tùy incremental strategy.

---

# XXIII.14. Semantic Interface File — SIF

Một package sau khi compile interface có thể sinh:

```text
foo.sif
```

SIF chứa:

```text
public types
public functions
public constants
public traits
public impls
generic constraints
associated types
re-exports
relevant attributes
API fingerprint
```

Không chứa toàn bộ private implementation.

---

# XXIII.15. SIF Không Phải ABI

Đừng nhầm:

```text
SIF
```

với:

```text
ABI metadata
```

SIF trả lời:

> "Compiler cần biết gì để compile consumer?"

ABI metadata trả lời:

> "Machine-level interface là gì?"

Có thể có:

```text
foo.sif
foo.abi
```

tách biệt.

---

# XXIII.16. Incremental Compilation

Compiler cần tránh:

```text
sửa 1 dòng
→ compile lại toàn package/world
```

Dependency graph:

```text
A
↓
B
↓
C
```

Nếu A thay private implementation:

```text
A private changed
```

thì B/C không nhất thiết compile lại.

---

# XXIII.17. API Fingerprint

Compiler tính:

```text
API(A)
```

Nếu:

```text
implementation changed
API fingerprint unchanged
```

→ consumer không cần semantic re-check.

---

# XXIII.18. Generic Dependency

Có một complication:

```axiom
pub fn map<T: Trait>(...)
```

Consumer có thể monomorphize.

Do đó thay đổi generic implementation có thể ảnh hưởng generated machine code.

Cần phân biệt:

```text
interface invalidation
```

và:

```text
codegen invalidation
```

Ví dụ:

```text
SIF unchanged
```

nhưng specialization cache phải invalidated nếu generic body thay đổi.

---

# XXIII.19. Semantic Hash

Compiler nên có nhiều hashes:

```text
SourceHash
SyntaxHash
SemanticHash
APIHash
ABIHash
CodegenHash
ArtifactHash
```

Không dùng một hash duy nhất.

---

# XXIII.20. Source Hash

Hash raw source:

```text id="s5v0p3"
SHA256(source)
```

chỉ phục vụ cache/provenance.

Whitespace change có thể làm SourceHash khác.

---

# XXIII.21. Semantic Hash

Sau parsing/type checking:

```text id="h71w9z"
SemanticHash
```

có thể bỏ qua những thứ không ảnh hưởng semantics.

Ví dụ:

```text
let x = 1
```

format thành:

```text
let x=1
```

→ semantic hash giống.

---

# XXIII.22. API Hash

Chỉ public semantic surface.

Private implementation:

```text id="9d86jv"
changed
```

→ APIHash có thể giữ nguyên.

---

# XXIII.23. ABI Hash

Nếu:

```text id="3g2o6m"
@repr(C)
```

field layout đổi:

```text
ABIHash changes
```

dù API high-level có thể vẫn tương thích source.

---

# XXIII.24. Codegen Hash

Codegen hash phụ thuộc:

```text
MIR
target
CPU features
optimization profile
compiler backend version
ABI
```

Do đó cùng API không đồng nghĩa cùng machine code.

---

# XXIII.25. Cache

Cache nên có hierarchy:

```text
Source Cache
     ↓
SIF Cache
     ↓
Typed/HIR Cache
     ↓
MIR Cache
     ↓
LIR Cache
     ↓
Object Cache
```

Không nhất thiết mọi stage phải persist ngay v0.1.

---

# XXIII.26. Content-Addressable Cache

Artifact cache:

```text
hash → artifact
```

Ví dụ:

```text
~/.axiom/cache/ab/cd/abcdef...
```

Không dùng path:

```text
project/build/foo.o
```

làm identity duy nhất.

---

# XXIII.27. Cache Safety

Compiler cache phải verify:

```text
compiler semantic version
target
profile
dependency identity
capability inputs
ABI
CPU features
```

Không được lấy stale object chỉ vì filename giống.

---

# XXIII.28. Reproducible Build

Mục tiêu:

```text
same semantic inputs
→ same semantic output
```

và trong reproducible profile:

```text
same inputs
→ byte-identical artifact
```

nếu target/toolchain deterministic.

---

# XXIII.29. Timestamp

Compiler không được embed timestamp ngẫu nhiên vào binary.

Nếu cần build timestamp:

```text
@build_input("timestamp")
```

phải explicit.

---

# XXIII.30. Randomness

Comptime:

```text
random()
```

không mặc định.

Nếu muốn:

```text
BuildEntropy
```

phải là explicit build input.

---

# XXIII.31. Host Environment

Không được tự động phụ thuộc:

```text
HOME
PATH
CPU count
current directory
timezone
hostname
```

trong semantic build.

Nếu cần → explicit capability/input.

---

# XXIII.32. Target vs Host

Build:

```text
Host: Windows x86-64
Target: Linux ARM64
```

phải tạo:

```text
host configuration
target configuration
```

riêng biệt.

Ví dụ:

```axiom
@cfg(target.os = "linux")
```

không được dùng host OS.

---

# XXIII.33. Cross Compilation

Build system cần:

```bash
axiom build --target linux-aarch64
```

Compiler sử dụng:

```text
target
ABI
sysroot
linker model
```

Không cần target machine chạy compiler.

---

# XXIII.34. Sysroot

Để cross compile, Axiom cần khái niệm:

```text
TargetSysroot
```

chứa:

```text
platform ABI
startup
system libraries
headers/metadata nếu cần FFI
linker support
```

Nhưng không bắt buộc phải là một C compiler toolchain.

---

# XXIII.35. Native Axiom Runtime

Final Axiom không nên yêu cầu:

```text
libstdc++
libgcc
MSVC CRT
C compiler
LLVM runtime
```

cho một chương trình freestanding hoặc runtime-free.

Tuy nhiên hosted OS application có thể link:

```text
OS libraries
system runtime
third-party native libraries
```

nếu program yêu cầu.

---

# XXIII.36. Profiles

Chốt profiles:

```text
dev
release
test
bench
size
debug
freestanding
```

### dev

Compile nhanh.

### release

Optimize mạnh.

### size

Ưu tiên binary size.

### debug

Debug metadata đầy đủ.

### freestanding

Không runtime/OS assumptions mặc định.

---

# XXIII.37. Optimization Profile

Không nên cho:

```text
profile = "fast"
```

thay đổi semantics.

Nó chỉ thay đổi:

```text
inlining
vectorization
LTO
unrolling
code layout
```

Không thay đổi:

```text
overflow
panic
atomic ordering
ownership
```

---

# XXIII.38. Panic Profile

Ví dụ:

```toml
[profile.release]
panic = "abort"
```

hoặc:

```toml
panic = "unwind"
```

`abort` giúp binary nhỏ.

---

# XXIII.39. LTO

Build system hỗ trợ:

```text
none
thin
full
```

LTO.

LTO xảy ra sau semantic verification.

Không được dùng LTO để bypass ABI/ownership contracts.

---

# XXIII.40. Static Linking

Mục tiêu native:

```text
Axiom object
+
Axiom libraries
+
system objects
→
executable
```

Static linking first-class.

---

# XXIII.41. Dynamic Linking

Dynamic linking explicit:

```text
[dependencies.system]
type = "shared"
```

Không tự động biến mọi dependency thành DLL/SO.

---

# XXIII.42. Object Ownership

Build system phải biết:

```text
object
static lib
shared lib
```

nhưng linker không cần hiểu:

```text
Move
Drop
view
ownership
```

Như đã chốt:

> Native linker understands machine contracts, not Axiom ownership.

---

# XXIII.43. Build Script

Tôi không khuyến nghị cấm hoàn toàn build scripting.

Nhưng thay vì:

```text
build.sh
build.py
arbitrary process
```

Axiom nên có:

```text
comptime/build capability
```

trong build graph.

Nếu thực sự cần external tool:

```text
ExecuteTool
```

được khai báo rõ.

---

# XXIII.44. Build Capability

Ví dụ:

```toml
[build.capabilities]
filesystem = ["generated/**"]
tools = ["shaderc"]
network = false
```

Build system có thể sandbox.

---

# XXIII.45. Build Sandbox

Mặc định:

```text
filesystem = denied
network = denied
process = denied
environment = denied
```

trừ capability được cấp.

Điều này rất quan trọng khi package từ registry được build.

---

# XXIII.46. Vendor

Axiom hỗ trợ:

```text
axiom vendor
```

để tạo:

```text
vendor/
```

và build offline.

Vendor dependency phải giữ:

```text
source identity
checksum
license metadata
```

nếu package metadata cung cấp.

---

# XXIII.47. Registry

Registry không phải một phần language semantics.

Có thể có:

```text
official registry
private registry
local registry
filesystem source
git
```

Compiler chỉ cần package source abstraction.

---

# XXIII.48. Package Manager Không Phải Compiler

Kiến trúc:

```text
axiom
 ├── compiler
 ├── resolver
 ├── build
 ├── package
 └── linker
```

nhưng semantics phải tách:

```text
resolver
    ↓
resolved package graph
    ↓
compiler
```

Compiler không được gọi HTTP để tìm dependency.

---

# XXIII.49. Build Plan

Resolver sinh:

```text
BuildPlan
```

Ví dụ:

```text
BuildPlan {
    target
    profile
    packages
    modules
    generated_artifacts
    compiler_inputs
    link_inputs
    capabilities
}
```

Sau đó compiler/build executor thực thi plan.

Điều này cực kỳ hữu ích cho AI và IDE.

---

# XXIII.50. Dry Run

Có thể:

```bash
axiom build --plan
```

để xuất:

```json
{
  "target": "x86_64-linux",
  "packages": [...],
  "compile_units": [...],
  "link_inputs": [...]
}
```

Compiler không cần AI để hiểu project.

---

# XXIII.51. Build Determinism

Build plan phải deterministic.

Cùng:

```text
axiom.toml
axiom.lock
source
target
profile
capabilities
```

→ cùng package graph và compile graph.

Filesystem traversal order không được làm thay đổi build.

---

# XXIII.52. Parallel Build

Build graph có thể chạy parallel:

```text
A ──┐
    ├── D
B ──┤
    │
C ──┘
```

A/B/C compile song song.

Deterministic output không phụ thuộc execution order.

---

# XXIII.53. Incremental Build

Nếu A unchanged:

```text
cache hit
```

Nếu B private changed:

```text
B rebuild
```

Nếu B API changed:

```text
B rebuild
C semantic check/rebuild
```

Nếu ABI changed:

```text
dependent native artifacts may relink
```

---

# XXIII.54. ABI-only Change

Ví dụ:

```text
@repr(C)
struct X {
    a: u32
    b: u32
}
```

đổi layout.

Semantic API có thể vẫn tương tự nhưng:

```text
ABIHash changed
```

→ native dependents cần rebuild/relink nếu ABI sử dụng.

---

# XXIII.55. Generic Code Invalidation

Generic body:

```axiom
pub fn map<T>(...)
```

thay đổi implementation.

SIF:

```text
same
```

nhưng instantiated machine code:

```text
stale
```

→ codegen cache invalidated.

Đây là lý do phải tách:

```text
APIHash
CodegenHash
```

---

# XXIII.56. Build Artifact Metadata

Object có thể chứa:

```text
Axiom compiler version
target
ABI
API/ABI fingerprint
source mapping
build profile
```

Debug metadata có thể được strip.

---

# XXIII.57. Debug/Release

Debug:

```text
full source mapping
variable info
type info
ownership info
```

Release:

```text
minimal
```

nhưng semantic artifact không được khác.

---

# XXIII.58. Semantic Build Equivalence

Compiler có thể build:

```text
debug
release
size
```

với machine code khác nhau nhưng phải giữ:

```text
observable semantics
```

giống nhau.

---

# XXIII.59. `test`

Test build profile có thể:

```text
axiom test
```

Compiler build test artifacts.

Không cần test framework built into language.

`test` attribute/API có thể là std/tooling layer.

---

# XXIII.60. `bench`

Benchmark:

```text
axiom bench
```

có thể build profile tối ưu nhưng instrumentation explicit.

Không được compiler benchmark bằng instrumentation mặc định làm thay đổi semantics/performance mà user không biết.

---

# XXIII.61. Size Optimization

`size` profile:

```text
-Osize
```

có thể:

- reduce inlining;
- merge constants;
- strip symbols;
- optimize cold paths;
- compress metadata;
- section GC;
- identical code folding.

Không được bỏ:

```text
required panic behavior
atomic semantics
FFI ABI
volatile
```

---

# XXIII.62. Freestanding

```bash
axiom build --profile freestanding
```

cho phép:

```text
no heap
no threads
no async runtime
no panic runtime
no std
```

nếu source không dùng chúng.

Đây là một mục tiêu rất quan trọng cho:

- kernel;
- bootloader;
- embedded;
- firmware;
- GPU support code;
- tiny executable.

---

# XXIII.63. Capability-Driven Runtime Linking

Một program:

```axiom
fn main() {
    let x = 1 + 2
}
```

không được tự động link:

```text
GC
async runtime
thread runtime
network runtime
reflection runtime
```

Compiler chỉ link những runtime components thực sự cần.

---

# XXIII.64. Runtime Dependency Graph

Compiler có thể sinh:

```text
Program
 ├── allocator
 ├── panic
 ├── thread
 ├── async
 └── reflection
```

chỉ khi cần.

Ví dụ:

```text
hello world
→ startup + IO support

freestanding arithmetic
→ startup only
```

---

# XXIII.65. Bootstrap

Axiom cuối cùng muốn:

```text
Axiom compiler
    compiled by
Axiom compiler
```

nhưng compiler đầu tiên không thể tự compile chính nó.

Do đó bootstrap stages:

```text
Stage 0
external compiler/backend
        ↓
Stage 1
Axiom compiler prototype
        ↓
Stage 2
own MIR/LIR
        ↓
Stage 3
Axiom compiler written in Axiom
        ↓
Stage 4
self-hosted compiler
        ↓
Stage 5
own linker/object toolchain
```

---

# XXIII.66. LLVM Chỉ Là Bootstrap Tool

Ở giai đoạn đầu có thể:

```text
Axiom
 ↓
MIR
 ↓
LLVM IR
 ↓
LLVM
```

Nhưng semantic source of truth vẫn là Axiom.

Không được để:

```text
LLVM behavior
```

trở thành language semantics.

---

# XXIII.67. Bootstrap Compiler Không Được Thành Language Spec

Nếu prototype compiler:

```text
cho phép X
```

nhưng spec:

```text
cấm X
```

thì compiler phải sửa.

Không:

> "LLVM làm được nên Axiom cho phép."

---

# XXIII.68. Self-Hosted Build

Cuối cùng:

```text
axiom compiler source
      ↓
axiom compiler
      ↓
native binary
```

không cần:

```text
Rust
C++
Go
LLVM
CMake
Cargo
```

để compile compiler.

Nhưng có thể vẫn link:

```text
OS ABI
system libraries
```

nếu compiler cần.

---

# XXIII.69. Own Linker

Mục tiêu cuối:

```text
Axiom Compiler
 ├── parser
 ├── type checker
 ├── MIR
 ├── optimizer
 ├── backend
 ├── object writer
 └── linker
```

Target đầu tiên hợp lý:

```text
ELF64 x86-64
```

sau đó:

```text
PE/COFF
Mach-O
ELF ARM64
WASM
RISC-V
```

---

# XXIII.70. Không Cần Tự Viết Everything Ngay

Điều này rất quan trọng về chiến lược.

Final architecture:

```text
own compiler
own backend
own object writer
own linker
```

không có nghĩa:

```text
day 1 phải viết assembler + linker + libc + OS SDK
```

Bootstrap phải thực dụng.

---

# XXIII.71. Build Tooling CLI

Core commands:

```text
axiom init
axiom check
axiom build
axiom run
axiom test
axiom bench
axiom clean
axiom update
axiom fetch
axiom vendor
axiom fmt
axiom doc
axiom inspect
axiom profile
axiom trace
```

Package commands:

```text
axiom package
axiom publish
```

ABI:

```text
axiom api-check
axiom abi-check
```

---

# XXIII.72. `axiom check`

Không codegen machine:

```text
source
 ↓
parse
 ↓
resolve
 ↓
type check
 ↓
ownership
 ↓
capability
 ↓
verified MIR
```

Rất nhanh.

IDE dùng `check`/incremental compiler.

---

# XXIII.73. `axiom build`

```text
resolve
 ↓
compile
 ↓
optimize
 ↓
lower
 ↓
object
 ↓
link
```

---

# XXIII.74. `axiom inspect`

Rất quan trọng cho Axiom:

```bash
axiom inspect --type User
axiom inspect --layout User
axiom inspect --ownership function
axiom inspect --mir foo
axiom inspect --abi foo
axiom inspect --deps
```

AI agent cũng có thể dùng những interface này thay vì phải đọc compiler internals.

---

# XXIII.75. Build System và AI

Một AI agent có thể:

```text
axiom check
axiom inspect --type ...
axiom inspect --mir ...
axiom api-check
axiom test
```

và nhận structured output:

```json
{
  "code": "AX_VIEW_0001",
  "location": {...},
  "message": "...",
  "expected": "...",
  "found": "..."
}
```

Điều này phù hợp với triết lý:

> **Compiler is the semantic authority; AI is a consumer of compiler facts.**

---

# XXIII.76. Normative Invariants

### Manifest / Resolution

**ABUILD-20 — Manifest Is Declarative**

**ABUILD-21 — Manifest Does Not Define Language Semantics**

**ABUILD-22 — Package Identity Includes Source Identity**

**ABUILD-23 — Dependency Resolution Is Deterministic**

**ABUILD-24 — Lock State Can Freeze Resolution**

**ABUILD-25 — Multiple Package Versions May Coexist**

**ABUILD-26 — Different Package Versions Have Distinct Type Identity**

### Build Graph

**ABUILD-27 — Package Graph Is Distinct From Build Graph**

**ABUILD-28 — Build Artifacts Are Explicit Graph Nodes**

**ABUILD-29 — Generated Artifacts Are First-Class Build Inputs**

**ABUILD-30 — Build Graph Execution Order Does Not Affect Semantics**

**ABUILD-31 — Independent Build Nodes May Execute In Parallel**

### Incremental

**ABUILD-32 — API Changes Determine Semantic Consumer Invalidation**

**ABUILD-33 — Private Implementation Changes Need Not Invalidate Consumers**

**ABUILD-34 — Generic Implementation Changes May Invalidate Codegen Caches**

**ABUILD-35 — ABI Changes May Require Native Relinking**

**ABUILD-36 — Cache Keys Must Include Relevant Semantic Inputs**

### Reproducibility

**ABUILD-37 — Hidden Environment State Cannot Affect Deterministic Builds**

**ABUILD-38 — Build Capabilities Are Explicit Inputs**

**ABUILD-39 — Host And Target Configuration Are Distinct**

**ABUILD-40 — Reproducible Builds Must Not Depend On Filesystem Enumeration Order**

**ABUILD-41 — Reproducible Builds Must Not Depend On Hidden Timestamps**

**ABUILD-42 — Explicit Nondeterministic Inputs Become Build Inputs**

### Cache

**ABUILD-43 — Cache Identity Is Content/Semantic Based**

**ABUILD-44 — Stale Cache Entries Must Not Be Used**

**ABUILD-45 — API Cache And Codegen Cache Are Distinct**

**ABUILD-46 — ABI Changes Invalidate Relevant Native Artifacts**

### Runtime

**ABUILD-47 — Runtime Components Are Capability-Driven**

**ABUILD-48 — Unused Runtime Components Are Not Mandatory Dependencies**

**ABUILD-49 — Freestanding Programs Need Not Link A Global Runtime**

### Security

**ABUILD-50 — Build Capabilities Are Explicit**

**ABUILD-51 — Network Access Is Not Implicit**

**ABUILD-52 — Arbitrary Process Execution Is Not Implicit**

**ABUILD-53 — Package Dependency Does Not Grant Host Privileges**

**ABUILD-54 — Build Sandbox Boundaries Are Semantic Build Inputs**

### Bootstrap

**ABUILD-55 — Bootstrap Toolchains Are Not Language Semantics**

**ABUILD-56 — Bootstrap Dependencies Are Not Required By Final Self-Hosted Axiom**

**ABUILD-57 — Self-Hosting Must Preserve Language Semantics**

**ABUILD-58 — Native Object/Linker Tooling Is A Long-Term Axiom Toolchain Goal**

---

# XXIII.77. Kiến trúc Build cuối

Như vậy pipeline hoàn chỉnh hiện tại:

```text
                axiom.toml
                     │
                     ▼
              Dependency Resolver
                     │
                     ▼
                Build Plan
                     │
          ┌──────────┼──────────┐
          │          │          │
       Package     Comptime   Generated
        Graph       Graph      Artifacts
          │          │          │
          └──────────┼──────────┘
                     ▼
                  Compiler
                     │
              Verified MIR
                     │
              Optimization
                     │
                  ABI/LIR
                     │
              Machine Backend
                     │
                  Object
                     │
                   Link
                     │
                     ▼
                 Artifact
```

Và cache nằm **xuyên suốt pipeline**, không chỉ ở object level.

---

# XXIII.78. Một quyết định quan trọng đã được chốt

Axiom build system **không nên cố bắt chước Cargo/CMake**.

Nó nên lấy những ý tưởng tốt từ chúng nhưng kiến trúc dựa trên:

```text
Semantic Build Graph
+
Capability-based Build
+
Content-addressed Cache
+
SIF
+
API/ABI Fingerprints
+
Native Compiler
```

Điều này đặc biệt phù hợp với mục tiêu cuối của Axiom là **self-hosted, compiler độc lập, native binary trực tiếp**.

---

## Tiếp theo — Part XXIV: Runtime · Startup · Profiles · Panic Runtime · Optional Runtime

Part XXIII đã chốt cách **xây artifact**. Part XXIV sẽ chốt cách **artifact chạy**:

```text
_process_start
startup
main
exit
allocator
panic
unwind
threads
async executor
TLS
reflection runtime
freestanding
hosted
runtime linking
OS ABI
```

Đây sẽ là phần quyết định trực tiếp việc Axiom có thực sự đạt mục tiêu **“không có runtime bắt buộc, binary cực nhỏ nhưng vẫn có thể xây ứng dụng lớn”** hay không.