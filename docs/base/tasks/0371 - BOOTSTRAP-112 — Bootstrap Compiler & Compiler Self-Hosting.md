# BOOTSTRAP-112 — Bootstrap Compiler & Compiler Self-Hosting

**Trạng thái: FROZEN / COMPLETED**

Đây là task biến Axiom từ một **thiết kế ngôn ngữ** thành một hệ thống có khả năng **tự xây dựng chính compiler của nó**.

Mục tiêu cuối:

```text
Axiom source
    ↓
Axiom Compiler
    ↓
native Axiom Compiler
    ↓
biên dịch chính Axiom Compiler source
    ↓
Axiom Compiler mới
```

Hay:

```text
axc₀ → axc₁ → axc₂ → axc₃ ...
```

và từ một giai đoạn trở đi:

```text
axcₙ(Axiom compiler source)
      ↓
axcₙ₊₁
```

---

# 1. Không nhầm bootstrap với self-hosting

Có 3 khái niệm khác nhau:

### Bootstrap

Compiler ban đầu được xây bằng ngôn ngữ khác:

```text
Rust/C++/...
    ↓
bootstrap compiler
```

### Self-hosted

Compiler được viết bằng chính Axiom:

```text
Axiom
    ↓
Axiom Compiler
```

### Self-compiling

Compiler Axiom có thể compile source code của chính nó:

```text
Axiom Compiler Source
        ↓
      axc
        ↓
   new axc binary
```

Mục tiêu cuối cùng của Axiom là cả ba điều này hội tụ thành:

```text
SELF-HOSTED + SELF-COMPILING
```

---

# 2. Nguyên tắc bootstrap

Không được thiết kế:

```text
Axiom
 ↓
LLVM
 ↓
Clang
 ↓
LLD
 ↓
OS
```

như dependency vĩnh viễn.

Thay vào đó:

```text
Bootstrap dependencies
        ↓
temporary
```

Production:

```text
Axiom
 ↓
Axiom Compiler
 ↓
Axiom Backend
 ↓
Axiom ObjectWriter
 ↓
Axiom Linker
 ↓
Native Binary
```

---

# 3. Bootstrap stages

Đề xuất 5 stage:

```text
Stage 0
Seed compiler
```

↓

```text
Stage 1
Axiom frontend compiler
```

↓

```text
Stage 2
Axiom compiler + own MIR/LIR
```

↓

```text
Stage 3
Axiom compiler + own object/linker
```

↓

```text
Stage 4
Fully self-hosted Axiom compiler
```

---

# 4. Stage 0 — Seed Compiler

Stage 0 có thể viết bằng:

```text
C++
Rust
Zig
hoặc implementation language phù hợp
```

Mục tiêu **không phải** tạo compiler hoàn chỉnh.

Nó chỉ cần đủ để compile một subset Axiom:

```text
Axiom Core Bootstrap Subset
```

---

# 5. Bootstrap subset

Subset này phải rất nhỏ:

```text
types
struct
enum
fn
if
loop
match
modules
basic generics
basic ownership
basic arrays
basic strings
```

Không cần ban đầu:

```text
GPU
async
reflection
advanced comptime
dynamic loading
full FFI
```

Nhưng subset phải đủ để viết compiler architecture.

---

# 6. Bootstrap subset không phải ngôn ngữ thứ hai

Không tạo:

```text
Axiom Bootstrap Language
```

một cách độc lập.

Thay vào đó:

```text
Axiom v0.1
 ├── Core subset
 └── advanced features
```

Stage 0 chỉ hỗ trợ **một subset của Axiom Core**.

Điều này tránh việc phải maintain hai language.

---

# 7. Stage 0 output

Seed compiler:

```text
ax0
```

có thể dùng external backend:

```text
ax0
 ↓
LLVM / system compiler
 ↓
ax1
```

hoặc trong bootstrap đầu tiên:

```text
ax0
 ↓
C source
 ↓
system C compiler
```

Cách này đơn giản hơn để đạt bootstrap đầu tiên.

---

# 8. Axiom-to-C bootstrap

Một phương án rất thực dụng:

```text
Axiom source
    ↓
Axiom frontend
    ↓
C-like lowered representation
    ↓
C compiler
    ↓
native axc
```

Nhưng **chỉ dùng ở bootstrap**.

Không được để C ABI hoặc C semantics trở thành semantic foundation của Axiom.

---

# 9. Tại sao không dùng LLVM vĩnh viễn?

LLVM rất mạnh nhưng Axiom có mục tiêu:

- compiler nhỏ;
- binary nhỏ;
- backend kiểm soát được;
- semantic model riêng;
- self-hosting;
- không phụ thuộc third-party compiler;
- tối ưu theo capability/ownership riêng.

Do đó:

```text
LLVM = bootstrap accelerator
```

không phải:

```text
LLVM = Axiom architecture
```

---

# 10. Stage 1 — Axiom Frontend

Stage 1:

```text
ax0
 ↓
compile Axiom frontend
 ↓
ax1
```

`ax1` đã được viết phần lớn bằng Axiom.

Architecture:

```text
Source
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
Type Checker
 ↓
HIR
 ↓
MIR
```

Backend vẫn có thể external.

---

# 11. Stage 1 backend

```text
ax1
 ↓
Verified MIR
 ↓
LLVM IR
 ↓
LLVM
 ↓
native
```

Đây là giai đoạn rất hữu ích để kiểm tra:

- type system;
- ownership;
- traits;
- module system;
- comptime subset;
- compiler data structures.

---

# 12. Stage 2 — Own MIR/LIR

Tiếp theo:

```text
ax1
 ↓
Axiom compiler source
 ↓
own MIR
 ↓
own OptIR
 ↓
own ABI MIR
 ↓
own LIR
 ↓
external assembler/object writer
```

Hoặc:

```text
own LIR
 ↓
temporary external backend
```

Mục tiêu lúc này:

> **LLVM không còn nằm trong semantic/compiler middle-end của Axiom.**

---

# 13. Stage 3 — Own Object Writer

Sau BOOTSTRAP-110:

```text
Axiom Compiler
 ↓
Machine Code
 ↓
Axiom ObjectWriter
```

không cần LLVM object writer.

Ví dụ:

```text
x86-64
 ↓
ELF object
```

được Axiom tự tạo.

---

# 14. Stage 3 — Own Linker

Tiếp theo:

```text
Axiom Linker
```

xử lý:

```text
.o
.a
.so
.exe
ELF
Mach-O
PE
```

Lúc này production pipeline gần như hoàn toàn:

```text
Axiom source
 ↓
Axiom compiler
 ↓
Axiom backend
 ↓
Axiom object writer
 ↓
Axiom linker
 ↓
native binary
```

---

# 15. Stage 4 — Fully self-hosted

Điểm hoàn thiện:

```text
axc source
   ↓
axc
   ↓
axc-new
```

và:

```text
axc-new
   ↓
compile axc source
   ↓
axc-newer
```

Compiler không cần:

```text
C compiler
C++
Rust
LLVM
Clang
GCC
LLD
```

để build production compiler.

---

# 16. Trust boundary

Có một vấn đề cực kỳ quan trọng:

> Nếu compiler bootstrap có bug, làm sao tin compiler tự sinh ra?

Axiom cần **bootstrap trust chain**.

```text
Seed Compiler
      ↓
Bootstrap Compiler
      ↓
Self-hosted Compiler
```

Mỗi stage phải có artifact identity:

```text
CompilerVersion
SourceFingerprint
Target
Configuration
BootstrapSeed
```

---

# 17. Stage verification

Mỗi stage có thể compile cùng một test suite:

```text
ax0 → compiler-test
ax1 → compiler-test
ax2 → compiler-test
ax3 → compiler-test
```

Kết quả:

```text
semantic tests
ABI tests
codegen tests
runtime tests
link tests
```

---

# 18. Compiler equivalence

Không yêu cầu binary compiler giống hệt.

Có hai mức:

### Semantic equivalence

```text
axₙ(source)
```

và:

```text
axₙ₊₁(source)
```

phải có cùng observable semantics.

### Reproducible compiler

Nếu cùng:

```text
compiler source
compiler seed
target
configuration
dependencies
```

thì output binary deterministic.

---

# 19. Three-way bootstrap test

Một kỹ thuật rất mạnh:

```text
Compiler A
  ↓
Compiler B

Compiler B
  ↓
Compiler C

Compiler C
  ↓
Compiler D
```

Nếu:

```text
B
C
D
```

ổn định về semantics/build identity thì tăng độ tin cậy bootstrap.

---

# 20. Compiler self-rebuild test

Build:

```text
axc1
```

sau đó:

```text
axc1 compile compiler-source
→ axc2
```

sau đó:

```text
axc2 compile compiler-source
→ axc3
```

So sánh:

```text
axc2
axc3
```

Không nhất thiết byte-identical trong mọi profile, nhưng phải có deterministic mode để mục tiêu:

```text
axc2 == axc3
```

có thể đạt được.

---

# 21. Compiler seed manifest

Seed phải được ghi rõ:

```text
BootstrapManifest
{
    compiler_version
    source_hash
    target
    seed_compiler
    backend
    runtime_profile
    build_options
    dependencies
}
```

Không có:

```text
"compiler somehow appeared"
```

---

# 22. Cross compilation

Self-hosting không có nghĩa compiler chỉ compile cho chính máy nó.

Ví dụ:

```text
Axiom compiler chạy Linux x86-64
          ↓
       target
          ↓
Android ARM64
```

hoặc:

```text
Windows x86-64
      ↓
Linux ARM64
```

Architecture:

```text
Host Target
      │
      ▼
Compiler
      │
      ▼
Target Description
      │
      ▼
Target Backend
      │
      ▼
Target Object/Link
```

---

# 23. Host ≠ Target

Compiler phải luôn phân biệt:

```text
Host
Target
```

Ví dụ:

```text
Host:
Windows x86-64

Target:
Linux AArch64
```

Compiler runtime chạy trên Windows.

Generated program chạy trên Linux ARM64.

---

# 24. Build compiler cho target

Có hai khái niệm:

```text
build compiler
```

và:

```text
compile target program
```

Không được nhầm.

Ví dụ:

```text
axc --host=x86_64-windows
    --target=aarch64-linux
```

---

# 25. Bootstrap compiler target

Stage 0 có thể:

```text
host = x86-64
target = x86-64
```

sau đó mới mở rộng:

```text
target = AArch64
target = RISC-V
target = WASM
```

Self-hosting không nên bị block bởi multi-target quá sớm.

---

# 26. Compiler architecture phải bootstrap-friendly

Compiler không được phụ thuộc circular:

```text
Compiler
 ↓
Library
 ↓
Compiler
```

Compiler cần một tầng:

```text
Compiler Foundation
```

gồm:

```text
collections
strings
hashing
arena
diagnostics
filesystem abstraction
parallel utilities
```

nhưng những phần này phải có implementation bootstrap đơn giản.

---

# 27. Compiler memory strategy

Compiler là một application lớn.

Do đó có thể dùng:

```text
Arena
InternPool
GenerationalArena
BumpAllocator
HashMap
Vec
String
```

Compiler không nên cố tránh heap chỉ vì Axiom có thể chạy freestanding.

Đây là một ví dụ:

> **Language capability ≠ application restriction.**

Axiom compiler có thể dùng allocator/runtime đầy đủ.

---

# 28. Compiler parallelism

Axiom compiler architecture nên hỗ trợ:

```text
parallel parsing
parallel module resolution
parallel type checking
parallel comptime
parallel generic instantiation
parallel codegen
parallel object generation
```

nhưng deterministic output.

Parallelism không được thay đổi semantic result.

---

# 29. Compiler cache

Dùng architecture đã thiết kế:

```text
SemanticFingerprint
```

để cache:

```text
parse
resolve
typecheck
HIR
MIR
comptime
generic instantiation
codegen
object
```

Ví dụ:

```text
module A unchanged
module B changed
module C unchanged
```

chỉ rebuild B và dependency cần thiết.

---

# 30. Compiler package structure

Self-hosted compiler nên phân chia:

```text
compiler/
├── lexer
├── parser
├── syntax
├── resolver
├── types
├── traits
├── comptime
├── hir
├── mir
├── verify
├── optimize
├── abi
├── lir
├── backend
├── object
├── linker
├── diagnostics
├── incremental
└── driver
```

Không tạo một `compiler.ax` khổng lồ.

---

# 31. Compiler driver

CLI:

```text
axc build
axc check
axc run
axc test
axc bench
axc emit
axc link
axc inspect
```

Internal pipeline:

```text
driver
 ↓
build graph
 ↓
compiler DB
 ↓
frontend
 ↓
verification
 ↓
optimization
 ↓
codegen
 ↓
object
 ↓
link
```

---

# 32. Compiler introspection

Axiom compiler nên cho phép:

```text
axc inspect --ast
axc inspect --hir
axc inspect --mir
axc inspect --verified-mir
axc inspect --opt-ir
axc inspect --abi
axc inspect --lir
axc inspect --machine
axc inspect --object
axc inspect --link
```

Đây đặc biệt hữu ích cho AI agent.

AI có thể hỏi:

```text
Why was this allocation not eliminated?
Why is this capability considered overlapping?
Why did this function fail Send?
Why was this call indirect?
```

Compiler trả lời bằng structured diagnostics.

---

# 33. Compiler correctness boundary

Compiler có ba vùng:

```text
Trusted
Verified
Optimizing
```

### Trusted

```text
parser infrastructure
compiler internals
backend machinery
```

### Verified

```text
MIR ownership
capability
Send/Share
Drop
async
GPU
FFI
```

### Optimizing

```text
SSA
alias analysis
vectorization
LTO
register allocation
```

Optimization failure không được biến thành semantic bug.

---

# 34. Miscompilation defense

Compiler có:

```text
--verify
```

để chạy:

```text
MIR verifier
OptIR verifier
LIR verifier
Machine IR verifier
```

sau mỗi major pass.

Debug compiler:

```text
parse
→ verify
→ optimize
→ verify
→ lower
→ verify
→ emit
```

Release compiler có thể giảm số lần verify nhưng semantics không phụ thuộc optimization level.

---

# 35. Bootstrap testing

Test suite chia:

```text
tests/
├── lexer
├── parser
├── resolver
├── types
├── traits
├── ownership
├── capability
├── async
├── concurrency
├── comptime
├── gpu
├── ffi
├── abi
├── codegen
├── object
├── linker
├── runtime
└── integration
```

Compiler bootstrap test phải chạy toàn bộ phần phù hợp với stage.

---

# 36. Golden compiler tests

Ví dụ:

```text
source.ax
expected-mir.txt
expected-abi.txt
expected-object.txt
```

Nhưng binary golden test không nên là semantic oracle duy nhất.

Vì optimizer có thể thay đổi hợp lệ.

Ưu tiên:

```text
semantic result
ABI contract
machine behavior
```

---

# 37. Differential testing

Trong bootstrap:

```text
Axiom compiler
       vs
LLVM/reference compiler
```

có thể compile cùng chương trình.

So sánh:

```text
program output
exit code
observable behavior
ABI
```

Không coi LLVM output là định nghĩa semantics.

Nó chỉ là **reference implementation** trong bootstrap.

---

# 38. Fuzzing

Compiler cần fuzz:

```text
lexer
parser
resolver
type checker
trait solver
comptime
MIR verifier
optimizer
object writer
linker
```

Đặc biệt:

```text
random valid programs
random invalid programs
mutation of valid programs
```

Compiler crash:

```text
ICE
```

phải khác:

```text
user diagnostic
```

---

# 39. Compiler crash model

Có ba loại:

```text
USER_ERROR
UNSAFE_CONTRACT_ERROR
INTERNAL_COMPILER_ERROR
```

Không được biến user source lỗi thành:

```text
segmentation fault
```

trong compiler.

---

# 40. Bootstrap completion criterion

Axiom được coi là **self-hosted** khi:

```text
1. Compiler source chủ yếu viết bằng Axiom.
2. Axiom compiler tự compile chính source của nó.
3. Compiler không cần external compiler để production build.
4. Backend native không cần LLVM/Clang/GCC.
5. ObjectWriter không cần external library.
6. Linker không cần LLD/system linker cho supported targets.
7. Compiler có thể bootstrap từ một documented seed.
```

Không nhất thiết mọi target đều phải self-hosted ngay ngày đầu.

---

# 41. Bootstrap invariants

### `ABOOT-20`
Bootstrap compiler must implement a defined Axiom subset, not an undocumented second language.

### `ABOOT-21`
Bootstrap dependencies are temporary implementation dependencies.

### `ABOOT-22`
Bootstrap dependencies must not become semantic language dependencies.

### `ABOOT-23`
Every bootstrap stage has a reproducible build identity.

### `ABOOT-24`
Host and target are distinct concepts.

### `ABOOT-25`
Cross-compilation is supported by the compiler architecture.

### `ABOOT-26`
Stage transitions preserve Axiom source semantics.

### `ABOOT-27`
Compiler-generated code remains subject to the same semantic contracts.

### `ABOOT-28`
Self-hosting does not require a monolithic runtime.

### `ABOOT-29`
Compiler can compile its own source after reaching the required language subset.

### `ABOOT-30`
Compiler self-rebuild is deterministic in reproducible mode.

### `ABOOT-31`
Bootstrap artifacts identify their seed compiler.

### `ABOOT-32`
External reference compilers may be used for differential validation but are not semantic authorities.

### `ABOOT-33`
Compiler optimization cannot change language semantics.

### `ABOOT-34`
Compiler verification failures are distinct from user diagnostics.

### `ABOOT-35`
Compiler intermediate representations are inspectable.

### `ABOOT-36`
Compiler cache identities include all semantic dependencies affecting compilation.

### `ABOOT-37`
Incremental compilation does not change semantics.

### `ABOOT-38`
Parallel compilation does not change semantics.

### `ABOOT-39`
The self-hosted compiler can eventually replace the bootstrap compiler.

### `ABOOT-40`
Production Axiom builds do not require third-party compilers.

### `ABOOT-41`
Production native code generation does not require LLVM.

### `ABOOT-42`
Production linking does not require LLD.

### `ABOOT-43`
The compiler can generate its own native executable for supported targets.

### `ABOOT-44`
A bootstrap seed must remain reproducibly reconstructible.

### `ABOOT-45`
Self-hosting is a property of the compiler implementation, not of the language semantics.

---

# 42. Kiến trúc bootstrap cuối cùng

Toàn bộ chain hiện là:

```text
             ┌────────────────────┐
             │ Bootstrap Seed     │
             └─────────┬──────────┘
                       ↓
             ┌────────────────────┐
             │ axc₀               │
             │ external bootstrap │
             └─────────┬──────────┘
                       ↓
             ┌────────────────────┐
             │ axc₁               │
             │ Axiom frontend     │
             └─────────┬──────────┘
                       ↓
             ┌────────────────────┐
             │ axc₂               │
             │ own MIR/LIR        │
             └─────────┬──────────┘
                       ↓
             ┌────────────────────┐
             │ axc₃               │
             │ own object/linker  │
             └─────────┬──────────┘
                       ↓
             ┌────────────────────┐
             │ axc₄               │
             │ fully self-hosted  │
             └─────────┬──────────┘
                       │
                       └───────┐
                               ↓
                       axc₅ → axc₆ → ...
```

Từ đây Axiom đã có **đường thoát hoàn chỉnh khỏi compiler/toolchain bên ngoài**.

---

# BOOTSTRAP-113 — Build System, Package Graph & Artifact Model

Task tiếp theo là phần còn thiếu để biến compiler thành **một toolchain sử dụng được trong thực tế**.

Ta cần khóa:

```text
Source
  ↓
Package
  ↓
Workspace
  ↓
Dependency Graph
  ↓
Build Graph
  ↓
Compiler Cache
  ↓
Object Artifacts
  ↓
Libraries
  ↓
Executable
```

Đặc biệt cần giải quyết một vấn đề rất quan trọng đối với mục tiêu của Axiom:

> **Làm sao dependency/package system không biến thành một “npm/cargo khổng lồ”, nhưng vẫn hỗ trợ project lớn, cross-compilation, incremental build, cache và reproducible build?**

BOOTSTRAP-113 sẽ khóa:

- package identity;
- module/package/workspace;
- dependency graph;
- versioning;
- semantic version;
- source dependencies;
- binary dependencies;
- platform dependencies;
- feature flags;
- target-specific dependencies;
- build profiles;
- debug/release/size/performance;
- incremental compilation;
- artifact cache;
- `.axmeta`;
- `.axo` object;
- `.axlib`;
- executable artifacts;
- static/shared dependencies;
- lockfile;
- reproducible build;
- offline build;
- vendoring;
- registry nhưng không bắt buộc centralized registry;
- package manager;
- build script;
- generated source;
- comptime/build-time dependency;
- dependency trust/provenance;
- workspace;
- compiler bootstrap build graph.

Sau 113, chuỗi sẽ tiến tới **Standard Library Architecture**, bởi lúc đó compiler, linker, runtime, package/build system và artifact model đều đã có nền móng đầy đủ.