Tiếp tục. Sau Native Linker, bước hợp lý là **TOOLCHAIN-001 — Axiom Native Build Driver**. Đây là lớp biến toàn bộ compiler + linker thành một toolchain sử dụng được thực tế.

# TOOLCHAIN-001 — AXIOM NATIVE BUILD DRIVER

## 1. Mục tiêu

Axiom cần một lệnh duy nhất:

```text
axiom build
```

để thực hiện:

```text
Source
  ↓
Module discovery
  ↓
Dependency resolution
  ↓
Compilation
  ↓
Comptime
  ↓
Object generation
  ↓
Native linking
  ↓
Executable
```

Không để người dùng phải tự gọi:

```text
compiler
assembler
linker
objcopy
ar
```

Đặc biệt, **assembler bên ngoài không tồn tại trong pipeline cuối cùng**.

---

# 2. Driver không phải compiler

Cần tách:

```text
axiom-driver
    │
    ├── compiler
    ├── linker
    ├── archive manager
    ├── target manager
    ├── dependency manager
    ├── cache
    └── build database
```

Driver chỉ điều phối.

Nó **không được chứa semantic logic của ngôn ngữ**.

Ví dụ:

```text
Compiler:
    "x có type i32"

Driver:
    "file này cần compile"
```

---

# 3. Các command chính

Đóng băng CLI v1:

```bash
axiom build
axiom build --release

axiom check
axiom compile
axiom run
axiom test

axiom fmt
axiom doc

axiom clean

axiom inspect
```

Compiler nội bộ:

```bash
axiom compile main.ax
```

Linker:

```bash
axiom link main.o -o app
```

Nhưng người dùng bình thường:

```bash
axiom build
```

---

# 4. Project structure

Đề xuất:

```text
myapp/
├── axiom.toml
├── src/
│   ├── main.ax
│   ├── lib.ax
│   └── foo.ax
├── tests/
├── examples/
├── assets/
└── build/
```

Không nên bắt buộc quá nhiều file.

Một chương trình nhỏ có thể:

```text
hello.ax
```

và:

```bash
axiom build hello.ax
```

là đủ.

---

# 5. `axiom.toml`

Project lớn:

```toml
[package]
name = "myapp"
version = "0.1.0"

[build]
entry = "src/main.ax"

[target]
platform = "native"
arch = "x86_64"
```

Nhưng đây là **build metadata**, không phải ngôn ngữ.

---

# 6. Build Graph

Driver xây dựng:

```text
BuildGraph
```

Ví dụ:

```text
main.ax
 ├── math.ax
 │    └── vector.ax
 │
 └── io.ax
      └── os/linux.ax
```

Graph này khác với linker graph.

### Build graph

```text
source/module dependency
```

### Link graph

```text
symbol/section dependency
```

Không trộn hai loại graph.

---

# 7. Module → Object

Một module hoặc compilation unit có thể tạo:

```text
main.ax
    ↓
main.axm
    ↓
main.o
```

Trong đó:

```text
.axm
```

là semantic compilation artifact đã được đề cập trước đây.

Nó có thể chứa:

```text
module metadata
type metadata
generic metadata
trait metadata
comptime dependencies
incremental hashes
public declarations
ABI metadata
```

Nhưng:

> `.axm` không phải object file.

---

# 8. Incremental Compilation

Đây là một phần rất quan trọng nếu Axiom compiler được AI agent phát triển và sau này compiler lớn.

Ví dụ:

```text
main.ax
math.ax
vector.ax
```

Sửa:

```text
math.ax
```

Không nên compile lại:

```text
vector.ax
```

nếu semantic dependency không thay đổi.

Driver xây:

```text
Dependency Graph
```

và cache:

```text
Source
  ↓
Parse artifact
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Object
```

---

# 9. Semantic Hash

Không nên chỉ dùng:

```text
SHA256(source file)
```

để quyết định recompilation.

Ví dụ chỉ đổi whitespace:

```text
fn foo() {}
```

thành:

```text
fn foo( ) { }
```

không nên invalidate toàn bộ semantic artifacts.

Do đó cần:

```text
SyntaxHash
SemanticHash
ABIHash
CodegenHash
```

---

# 10. Dependency Invalidation

Ví dụ:

```text
foo.ax
```

đổi implementation nhưng public ABI không đổi.

Có thể:

```text
foo.ax
   ↓
recompile foo
   ↓
bar không cần type-check lại
```

Nếu đổi:

```text
pub fn foo(x: i32) -> i32
```

thành:

```text
pub fn foo(x: f64) -> i32
```

thì dependency sử dụng `foo` phải được invalidated.

---

# 11. Public Interface Artifact

Đây là nơi `.axm` trở nên rất hữu ích.

Module có:

```text
private implementation
public interface
```

Driver có thể lưu semantic interface:

```text
ModuleInterface {
    public_types
    public_functions
    public_traits
    public_constants
    public_abi
    generic_signatures
}
```

Module phụ thuộc chỉ cần đọc interface thay vì parse toàn bộ implementation.

---

# 12. Compilation Modes

Nên có:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

và:

```text
--debug
--release
```

Nhưng:

```text
debug ≠ different semantics
release ≠ different semantics
```

Chỉ khác:

```text
optimization
debug metadata
assert configuration
diagnostic level
```

---

# 13. Target Triple

Driver cần target abstraction:

```text
Target {
    architecture
    vendor
    os
    environment
    abi
    object_format
    pointer_width
    endian
    cpu
    features
}
```

Ví dụ:

```text
x86_64-linux
x86_64-windows
aarch64-linux
aarch64-android
aarch64-macos
aarch64-ios
riscv64-linux
wasm32-wasi
```

Không nên để compiler rải các string:

```text
if target == "x86_64-linux" ...
```

khắp codebase.

---

# 14. Target Database

Có:

```text
targets/
├── x86_64-linux.axcfg
├── x86_64-windows.axcfg
├── aarch64-linux.axcfg
├── aarch64-android.axcfg
├── aarch64-macos.axcfg
├── aarch64-ios.axcfg
└── wasm32-wasi.axcfg
```

hoặc equivalent internal representation.

Target config chứa:

```text
ABI
calling convention
object format
page size
stack alignment
TLS model
atomic capabilities
unwind format
default linker policy
CPU features
```

---

# 15. Cross Compilation

Một trong những mục tiêu lớn của Axiom:

```bash
axiom build --target=aarch64-linux
```

trên:

```text
x86_64 Windows
```

phải tạo:

```text
aarch64 Linux ELF
```

mà không cần cài:

```text
aarch64-gcc
aarch64-ld
```

nếu Axiom đã có backend/linker tương ứng.

---

# 16. Sysroot

Không nên mặc định phụ thuộc vào system `/usr`.

Axiom có:

```text
sysroot/
├── targets/
├── std/
├── runtime/
├── headers/        # only if FFI integration needs them
└── libs/
```

Nhưng cần phân biệt:

```text
Axiom standard library
```

với:

```text
OS SDK
```

Ví dụ iOS/macOS vẫn có thể cần SDK/platform frameworks.

---

# 17. Native SDK Integration

Không nên đặt mục tiêu:

> "Axiom không bao giờ sử dụng bất kỳ thư viện hệ thống nào."

Mục tiêu chính xác hơn:

> **Axiom compiler/linker không phụ thuộc vào toolchain compiler bên ngoài.**

Ví dụ Windows:

```text
Axiom
  ↓
native PE
  ↓
Windows API
```

có thể link/import:

```text
kernel32.dll
user32.dll
```

mà không cần MSVC để compile Axiom.

Tương tự Linux:

```text
Axiom
  ↓
ELF
  ↓
libc.so
```

nếu user chọn hosted model.

---

# 18. Build Profiles

Đề xuất:

```text
dev
release
size
freestanding
test
bench
```

Ví dụ:

```toml
[profile.release]
opt_level = 3
debug = false
panic = "abort"

[profile.size]
opt_level = "z"
panic = "abort"

[profile.freestanding]
runtime = "none"
panic = "abort"
```

---

# 19. Runtime Selection

Đây là chỗ philosophy của Axiom thể hiện rất rõ.

Không:

```text
every executable
    ↓
axiom_runtime.dll
```

Thay vào đó:

```text
Program requirements
       ↓
Runtime component selection
```

Ví dụ chương trình:

```text
fn main() {
    let x = 10;
}
```

có thể:

```text
runtime = none
```

Chương trình:

```text
thread.spawn(...)
```

thì:

```text
runtime:
    thread support
```

Async:

```text
runtime:
    executor
    I/O integration
```

---

# 20. Build Plan

Driver trước tiên tạo:

```text
BuildPlan
```

Ví dụ:

```text
BuildPlan {
    target
    profile
    modules
    comptime_jobs
    compilation_jobs
    object_files
    archives
    runtime_components
    linker_options
    output
}
```

Sau đó executor thực hiện plan.

Điều này cho phép:

```text
axiom build --dry-run
```

in:

```text
Compile:
    src/main.ax
    src/math.ax

Link:
    main.o
    math.o

Runtime:
    none

Target:
    x86_64-linux

Output:
    build/app
```

---

# 21. Parallel Compilation

Các module độc lập:

```text
A ─┐
B ─┼──→ C
D ─┘
```

có thể compile song song:

```text
A ──┐
B ──┼── parallel
D ──┘
```

sau đó:

```text
C
```

Driver scheduler có thể sử dụng thread pool của chính compiler.

Không cần runtime của executable.

---

# 22. Comptime Integration

Build graph phải biết comptime dependencies.

Ví dụ:

```text
comptime {
    embed("shader.bin")
}
```

thì:

```text
shader.bin
```

trở thành dependency của compilation artifact.

Nếu file đổi:

```text
shader.bin
   ↓
invalidate module
```

Đây là lý do trước đó ta đóng băng:

> External comptime inputs are part of incremental identity.

---

# 23. Build Cache

Có thể:

```text
build/cache/
    <semantic-hash>/
        hir
        mir
        object
        metadata
```

Cache key nên bao gồm:

```text
source semantic hash
compiler version
target
ABI
optimization level
feature flags
comptime inputs
relevant compiler configuration
```

Không được cache nhầm:

```text
x86_64 object
```

cho:

```text
aarch64
```

---

# 24. Reproducibility

Build:

```bash
axiom build
```

hai lần với cùng:

```text
source
compiler
target
dependencies
configuration
comptime inputs
```

phải tạo output giống nhau trong reproducible mode.

Driver phải loại bỏ:

```text
timestamp
machine path
random IDs
temporary paths
unordered iteration
```

khỏi semantic/build output.

---

# 25. Diagnostics

Driver không được biến lỗi compiler thành:

```text
Compilation failed.
```

một cách vô nghĩa.

Ví dụ:

```text
AX1507 MoveAfterMove

src/main.ax:17:9

value `x` was moved here

15 | let y = consume(x);
   |                  ^

17 | print(x);
   |       ^

`x` is no longer owned after the call.
```

Compiler diagnostic và driver diagnostic phải có cùng machine-readable format.

---

# 26. JSON Diagnostics

AI tooling cần:

```bash
axiom check --diagnostic-format=json
```

Ví dụ semantic structure:

```json
{
  "code": "AX1507",
  "severity": "error",
  "file": "src/main.ax",
  "range": {
    "start": 17,
    "end": 9
  },
  "message": "value was moved",
  "notes": []
}
```

Đây sẽ rất hữu ích cho:

- VS Code
- IDE
- LSP
- AI coding agents
- automated testing

---

# 27. `axiom inspect`

Đây nên là một công cụ **hạng nhất**, không phải debug feature phụ.

Ví dụ:

```bash
axiom inspect --ast file.ax
axiom inspect --hir file.ax
axiom inspect --types file.ax
axiom inspect --ownership file.ax
axiom inspect --mir file.ax
axiom inspect --async file.ax
axiom inspect --layout file.ax
axiom inspect --abi file.ax
axiom inspect --lir file.ax
axiom inspect --machine file.ax
```

Và:

```bash
axiom inspect --link-graph app
```

```bash
axiom inspect --symbols app
```

```bash
axiom inspect --sections app
```

---

# 28. Đây là điểm cực kỳ phù hợp với AI Agent

Compiler nên có:

```text
--json
--dump
--explain
--trace
```

Ví dụ:

```bash
axiom explain AX1507
```

hoặc:

```bash
axiom inspect --ownership foo.ax --format=json
```

AI agent có thể tự đọc:

```text
source
↓
diagnostic
↓
semantic facts
↓
MIR
↓
machine output
```

thay vì phải đoán compiler đang làm gì.

---

# 29. Toolchain không được có "magic"

Driver không nên tự động:

```text
download compiler
download linker
download gcc
download LLVM
```

nếu dependency đó không được project khai báo.

Final Axiom toolchain phải có khả năng:

```text
axiom
├── compiler
├── linker
├── object writer
├── machine encoders
├── archive manager
└── build driver
```

để tạo native binary.

---

# 30. Toolchain self-containment

Mục tiêu cuối:

```text
axiom
```

binary duy nhất có thể:

```text
axiom build hello.ax
```

và tạo:

```text
hello.exe
hello
hello
```

tùy target.

Không cần:

```text
clang
gcc
as
ld
lld
ar
objcopy
```

---

# 31. Bootstrap Reality

Tuy nhiên **bootstrap phase không cần tự trói mình**.

Stage 0:

```text
C/Python/Rust/etc.
      ↓
Axiom compiler
      ↓
LLVM/system linker
```

Stage 1:

```text
C bootstrap compiler
      ↓
Axiom Machine Encoder
      ↓
Axiom Object Writer
      ↓
Axiom Native Linker
```

Stage 2:

```text
Axiom compiler source
      ↓
Stage-1 Axiom compiler
      ↓
native Axiom compiler
```

Stage 3:

```text
Axiom compiler
      ↓
compile itself
      ↓
itself
```

---

# 32. Self-hosting Criterion

Không nên định nghĩa:

> "Compiler có source viết bằng Axiom là self-hosting."

Tiêu chí phải mạnh hơn:

```text
S0
  ↓
Axiom compiler source
  ↓
Axiom compiler
  ↓
compile Axiom compiler source
  ↓
Axiom compiler executable
```

và executable mới:

```text
compile chính source của nó
```

mà không cần:

```text
C compiler
LLVM
external assembler
external linker
```

cho target đã tuyên bố self-hosted.

---

# 33. Build Driver Architecture

Repository:

```text
compiler/
└── driver/
    ├── cli/
    ├── project/
    ├── target/
    ├── graph/
    ├── planner/
    ├── scheduler/
    ├── cache/
    ├── diagnostics/
    ├── profiles/
    ├── runtime/
    ├── linker/
    └── commands/
```

Các command:

```text
commands/
├── build
├── check
├── compile
├── link
├── run
├── test
├── fmt
├── doc
├── inspect
└── clean
```

---

# 34. Invariants

Đóng băng nhóm:

### ATOOL-20 — Driver Does Not Define Language Semantics

### ATOOL-21 — Build Graph Is Distinct From Link Graph

### ATOOL-22 — Compilation Units Have Stable Identity

### ATOOL-23 — Incremental Artifacts Are Content/Dependency Addressed

### ATOOL-24 — Semantic Interface Can Be Cached

### ATOOL-25 — Implementation Changes Need Not Invalidate Unchanged Interfaces

### ATOOL-26 — ABI Changes Invalidate ABI Dependents

### ATOOL-27 — Target Is Part Of Build Identity

### ATOOL-28 — Compiler Version Is Part Of Artifact Identity

### ATOOL-29 — Comptime Inputs Are Build Dependencies

### ATOOL-30 — External Comptime State Is Explicitly Tracked

### ATOOL-31 — Parallel Compilation Preserves Semantics

### ATOOL-32 — Build Order Is Deterministic

### ATOOL-33 — Diagnostics Have Stable Machine-Readable Identity

### ATOOL-34 — Build Profiles Do Not Change Language Semantics

### ATOOL-35 — Runtime Components Are Demand Driven

### ATOOL-36 — Runtime Is Not Implicitly Linked

### ATOOL-37 — Cross Compilation Is First-Class

### ATOOL-38 — Target Configuration Is Centralized

### ATOOL-39 — System SDK Dependencies Are Explicit

### ATOOL-40 — External Compiler Is Not Required By Final Toolchain

### ATOOL-41 — External Assembler Is Not Required By Final Toolchain

### ATOOL-42 — External Linker Is Not Required By Final Toolchain

### ATOOL-43 — Build Is Reproducible Under Reproducible Configuration

### ATOOL-44 — Cache Cannot Change Semantics

### ATOOL-45 — Cache Keys Include All Semantic Inputs

### ATOOL-46 — Inspectable Intermediate Representations Are Stable Enough For Tooling

### ATOOL-47 — Driver Can Emit Complete Build Plan

### ATOOL-48 — Driver Can Execute Native Linker Directly

### ATOOL-49 — Driver Can Produce Freestanding Executables

### ATOOL-50 — Toolchain Can Bootstrap Without Its Final Self-Hosted Implementation

---

# 35. Vertical Slice đầu tiên

Từ đây tôi khuyên **ngừng mở rộng kiến trúc lý thuyết một lúc** và xây vertical slice thực tế:

```text
hello.ax
```

↓

```text
Lexer
Parser
Resolver
Type Checker
Ownership
MIR
MIR Optimizer
ABI
LIR
x86_64 Machine IR
Register Allocation
Encoder
ELF Object Writer
Axiom Linker
ELF Executable
```

Kết quả:

```bash
./hello
```

và:

```text
Hello, Axiom!
```

**không libc, không LLVM, không assembler, không external linker.**

Đây sẽ là milestone quan trọng hơn việc tiếp tục thiết kế thêm 20 subsystem.

---

# 36. Sau TOOLCHAIN-001

Thứ tự tiếp theo tôi đề xuất là:

```text
TOOLCHAIN-001
Native Build Driver
        ↓
BOOTSTRAP-001
Stage-0 Compiler
        ↓
BOOTSTRAP-002
Minimal Axiom Compiler
        ↓
BOOTSTRAP-003
Compiler-in-Axiom
        ↓
SELFHOST-001
Self-hosted Axiom Compiler
```

Nhưng trước **BOOTSTRAP-001**, còn một phần nền tảng nên chốt:

## `STDLIB-001 — Axiom Core/Runtime/Std Boundary`

Vì lúc bắt đầu viết compiler bằng Axiom, ta phải trả lời rất rõ:

```text
Compiler cần gì từ Core?
Compiler cần gì từ Runtime?
Compiler cần gì từ Std?
Cái gì phải compile được khi không có Std?
Cái gì được phép gọi OS?
Cái gì phải freestanding?
```

Nếu không chốt boundary này trước, rất dễ rơi vào tình trạng **compiler tưởng là self-hosted nhưng thực tế phụ thuộc ngầm vào một runtime/stdlib khổng lồ**.