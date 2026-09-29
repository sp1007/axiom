# BOOTSTRAP-311 — AXIOM BOOTSTRAP, SELF-HOSTING & COMPILER INDEPENDENCE

## 311.1. Mục tiêu

Xây dựng lộ trình để Axiom Compiler chuyển từ:

```text
compiler được viết bằng ngôn ngữ khác
```

sang:

```text
compiler được viết hoàn toàn bằng Axiom
```

và cuối cùng:

> **Axiom có thể tự biên dịch chính compiler của nó, tự tạo object, tự link executable và không còn phụ thuộc vào compiler/linker/assembler bên ngoài.**

Đây là bước biến Axiom từ một thiết kế/compiler prototype thành một **ngôn ngữ độc lập có toolchain hoàn chỉnh**.

---

# 311.2. Nguyên tắc Bootstrap

### `BOOT-01` — Bootstrap dependency không phải Final dependency

Trong giai đoạn đầu có thể sử dụng:

- C/C++;
- Rust;
- LLVM;
- system linker;
- system assembler;
- Python;
- host compiler.

Nhưng chúng chỉ được coi là:

```text
Bootstrap Infrastructure
```

không phải:

```text
Axiom Toolchain Dependency
```

Final compiler phải có khả năng loại bỏ chúng.

---

# 311.3. Ba loại phụ thuộc

Axiom phải phân biệt rõ:

### Build dependency

Dùng để xây compiler trong bootstrap stage.

```text
LLVM
Clang
system compiler
```

### Test dependency

Dùng để kiểm chứng.

```text
objdump
readelf
native debugger
reference compiler
```

### Semantic dependency

Thứ compiler cuối cùng bắt buộc phải cần.

Mục tiêu:

```text
Final Semantic Dependency = Axiom compiler itself + OS/CPU primitives
```

Không có semantic dependency bắt buộc vào LLVM/GCC/Clang.

---

# 311.4. Bootstrap Stages

Định nghĩa chính thức:

```text
Stage 0
External toolchain
      ↓
Stage 1
Axiom compiler core
      ↓
Stage 2
Axiom compiler compiled by Axiom
      ↓
Stage 3
Stage-2 compiler rebuilds itself
      ↓
Stage 4+
Reproducible self-hosting
```

---

# 311.5. Stage 0

Stage 0 là compiler hiện tại được viết bằng ngôn ngữ bootstrap.

Có thể:

```text
C++ + LLVM
```

hoặc:

```text
Rust + LLVM
```

hoặc kiến trúc tương đương.

Stage 0 phải implement đủ:

```text
lexer
parser
resolver
type checker
trait solver
HIR
MIR
ownership verifier
capability verifier
comptime
basic optimizer
machine backend
object writer
linker
```

Nhưng có thể reuse LLVM trong giai đoạn này.

---

# 311.6. Stage 1

Stage 1 bắt đầu chứa các thành phần được viết bằng Axiom:

```text
axiom/
├── frontend/
├── semantic/
├── mir/
├── optimizer/
├── backend/
├── object/
├── linker/
├── driver/
└── runtime/
```

Stage 0 compile chúng.

Kết quả:

```text
axiom-stage1
```

---

# 311.7. Stage 2 — Self Compile

Stage 1 phải compile source của chính Stage 1:

```text
axiom-stage1
      │
      ▼
compiler source written in Axiom
      │
      ▼
axiom-stage2
```

Điểm quan trọng:

**Stage 2 không được được coi là self-hosting chỉ vì nó compile được một phần compiler.**

Phải chứng minh:

```text
Stage 2 compiler
```

có thể compile **toàn bộ compiler source tree**.

---

# 311.8. Stage 3 — Fixed Point

Chạy:

```text
Stage 2 → Stage 3
Stage 3 → Stage 4
Stage 4 → Stage 5
```

Sau đó kiểm tra semantic equivalence.

Nếu deterministic:

```text
Stage N binary == Stage N+1 binary
```

Nếu binary không hoàn toàn deterministic:

```text
semantic fingerprint(Stage N)
==
semantic fingerprint(Stage N+1)
```

và executable behavior phải tương đương.

---

# 311.9. Trust Chain

Axiom cần xây dựng một **Bootstrap Trust Chain**:

```text
External Compiler
       ↓
Stage 0
       ↓
Axiom source
       ↓
Stage 1
       ↓
Stage 2
       ↓
Stage 3
       ↓
Self-hosted compiler
```

Mỗi bước phải được kiểm tra:

```text
source identity
compiler identity
target identity
build configuration
dependency identity
artifact hash
semantic fingerprint
```

---

# 311.10. Compiler Provenance

Mỗi compiler binary phải chứa metadata có thể truy vấn:

```text
CompilerProvenance {
    compiler_version
    semantic_version
    source_revision
    target
    bootstrap_stage
    build_profile
    features
    dependency_fingerprint
    compiler_fingerprint
}
```

Ví dụ:

```text
axiom --version --verbose
```

có thể trả về:

```text
Compiler: Axiom
Version: 0.x
Semantic: ...
Target: x86_64-windows
Bootstrap Stage: 3
Source Revision: ...
Compiler Fingerprint: ...
```

---

# 311.11. Self-Hosting Boundary

Không phải toàn bộ compiler phải được chuyển sang Axiom cùng lúc.

Có thể chia:

```text
Phase A
frontend

Phase B
type system

Phase C
HIR/MIR

Phase D
verification

Phase E
optimization

Phase F
machine backend

Phase G
object writer

Phase H
linker

Phase I
driver/build system
```

Mỗi phase phải có interface ổn định với phần còn lại.

---

# 311.12. Compiler ABI nội bộ

Để bootstrap dễ dàng, các subsystem phải giao tiếp thông qua interface rõ ràng:

```text
SourceDB
    ↓
SyntaxDB
    ↓
HIRDB
    ↓
TypeDB
    ↓
MIRDB
    ↓
VerifiedMIR
    ↓
OptIR
    ↓
MachineIR
    ↓
ObjectIR
    ↓
LinkedImage
```

Không cho subsystem mới trực tiếp phụ thuộc implementation detail của subsystem khác.

Điều này đặc biệt quan trọng khi thay từng subsystem từ Stage 0 sang Axiom.

---

# 311.13. Self-Hosting CompilerDB

`CompilerDB` phải trở thành một trong những phần đầu tiên được self-host.

Bao gồm:

```text
SourceDB
PackageDB
ModuleDB
SyntaxDB
DeclarationDB
TypeDB
TraitDB
ConstDB
GenericDB
ComptimeDB
HIRDB
MIRDB
DiagnosticDB
SourceMapDB
LayoutDB
AbiDB
CodegenDB
BuildDB
TestDB
```

Compiler database không được phụ thuộc vào runtime đặc biệt của Stage 0.

---

# 311.14. Bootstrap Runtime

Một vấn đề quan trọng:

Compiler tự nó là một chương trình lớn.

Nếu Axiom compiler cần:

```text
GC
large runtime
reflection runtime
async runtime
```

thì self-hosting sẽ kéo theo rất nhiều dependency.

Do đó compiler phải có thể build với:

```text
@profile compiler
```

sử dụng:

```text
Freestanding/Minimal Hosted Runtime
```

chỉ chứa:

- memory allocation;
- filesystem;
- process;
- threads nếu cần;
- synchronization;
- UTF-8/text;
- hashing;
- file mapping;
- basic I/O.

Không kéo GPU/async/network/runtime component không cần thiết.

---

# 311.15. Compiler Memory Strategy

Compiler là workload rất khác application thông thường.

Không nên bắt compiler sử dụng:

```text
general heap allocation
```

cho mọi thứ.

Có thể dùng:

```text
Arena
Bump allocator
Intern pools
Region storage
Generational IDs
Query caches
```

để giảm allocation overhead.

Ví dụ:

```text
TypeDB
```

có thể sử dụng:

```text
TypeId → Interned Type
```

thay vì tạo nhiều object runtime độc lập.

---

# 311.16. Bootstrap-safe Data Structures

Các cấu trúc compiler quan trọng phải được viết bằng Axiom:

```text
Vec
HashMap
HashSet
Arena
Interner
String
BitSet
SparseSet
Graph
WorkQueue
IndexVec
GenerationalMap
```

và phải tránh phụ thuộc circular vào compiler.

Đặc biệt:

```text
CompilerDB
```

không được phụ thuộc ngược vào frontend implementation.

---

# 311.17. Compiler Internal IDs

Các ID:

```text
TypeId
FunctionId
ModuleId
DeclarationId
BasicBlockId
InstructionId
```

phải là những value type đơn giản.

Không dùng:

```text
raw pointer
object identity
GC reference
```

làm semantic identity.

Ví dụ:

```text
struct TypeId {
    index: u32
    generation: u32
}
```

hoặc representation tương đương.

---

# 311.18. Bootstrap không được dựa vào Undefined Behavior

Stage 0 có thể có implementation tricks, nhưng semantic behavior của compiler phải được định nghĩa.

Không cho phép:

```text
"compiler chạy được vì UB hiện tại chưa xảy ra"
```

Các subsystem quan trọng phải có:

```text
verified invariants
```

để Stage 1/2 có thể reproduce chính xác.

---

# 311.19. Native Backend Independence

Self-hosting thực sự chỉ hoàn thành khi Axiom compiler có thể tự:

```text
MachineIR
 ↓
Encoder
 ↓
ObjectWriter
 ↓
Linker
 ↓
ExecutableWriter
```

mà không cần:

```text
LLVM
Clang
GNU assembler
LLD
MSVC linker
```

trong production path.

External tools chỉ còn:

```text
testing
debugging
optional interoperability
```

---

# 311.20. Bootstrap Linker

Linker Axiom phải tự link chính compiler.

Đây là một milestone riêng:

```text
axiom compiler
      ↓
.axo/.obj
      ↓
Axiom Linker
      ↓
axiom.exe
```

Không được có vòng:

```text
Axiom compiler
 ↓
system linker
 ↓
Axiom compiler
```

ở final stage.

---

# 311.21. Bootstrap Object Writer

Tương tự:

```text
Axiom Encoder
 ↓
Axiom Object Writer
 ↓
ELF/COFF/Mach-O/WASM
```

phải tự tạo object.

External assembler chỉ được dùng để:

```text
differential validation
```

---

# 311.22. Bootstrap Compiler Build Graph

Final:

```text
axiom build compiler
```

phải tạo dependency graph:

```text
Compiler Source
     │
     ├── Frontend
     ├── Semantic
     ├── MIR
     ├── Optimizer
     ├── Backend
     ├── Object
     ├── Linker
     └── Driver
              │
              ▼
        Axiom Compiler
```

Build graph phải hỗ trợ incremental compilation của chính compiler.

---

# 311.23. Stage Boundary Validation

Mỗi bootstrap stage phải chạy:

```text
axiom test
axiom test --differential
axiom test --incremental
axiom test --reproducible
axiom test --bootstrap
```

Không được chuyển sang stage tiếp theo nếu stage hiện tại chưa pass validation.

---

# 311.24. Three-Compiler Validation

Ở giai đoạn quan trọng có thể dùng:

```text
Compiler A = Stage 0
Compiler B = Stage 1
Compiler C = Stage 2
```

Compile cùng source:

```text
A(source)
B(source)
C(source)
```

Sau đó so sánh:

```text
semantic result
IR
ABI
behavior
```

Nếu A và B đồng ý nhưng C khác:

```text
Stage 2 regression
```

Nếu B và C đồng ý nhưng A khác:

```text
Stage 0 bug
```

Đây là cơ chế rất mạnh để phát hiện bootstrap compiler miscompile.

---

# 311.25. Diverse Bootstrap

Về lâu dài có thể có:

```text
Bootstrap compiler A
Bootstrap compiler B
```

được implement bằng hai implementation độc lập.

Sau đó:

```text
A → compile Axiom compiler
B → compile Axiom compiler
```

so sánh kết quả.

Mục tiêu là giảm nguy cơ:

```text
single compiler implementation bug
```

được truyền qua toàn bộ bootstrap chain.

Không bắt buộc cho v1, nhưng architecture phải không cản trở.

---

# 311.26. Compiler Rebuild Test

CI phải thực hiện:

```text
Build Stage N
       ↓
Build compiler again using Stage N
       ↓
Compare
```

Nếu deterministic:

```text
hash1 == hash2
```

Nếu không:

```text
semantic fingerprint1 == semantic fingerprint2
```

và mọi khác biệt binary phải được giải thích.

---

# 311.27. Trust Root

Final Axiom distribution cần xác định:

```text
Trust Root
```

Có thể là:

```text
official prebuilt Axiom compiler
```

hoặc:

```text
independently verified bootstrap binary
```

Từ đó:

```text
Trust Root
   ↓
Axiom Source
   ↓
Self Build
   ↓
Self Verification
```

---

# 311.28. Stage 0 Removal

Cuối cùng repository phải cho phép:

```text
bootstrap/
```

chứa Stage 0.

Nhưng production build không được cần nó.

Ví dụ:

```text
bootstrap build
```

dùng Stage 0.

Còn:

```text
axiom build
```

dùng Axiom compiler hiện tại.

Khi đã self-host ổn định:

```text
bootstrap/
```

chỉ còn phục vụ:

- emergency bootstrap;
- new architecture;
- trusted rebuild;
- historical compiler recovery.

---

# 311.29. Cross Compilation During Bootstrap

Self-host compiler phải hỗ trợ:

```text
build host ≠ target
```

Ví dụ:

```text
Windows x64
    ↓
AArch64 Linux compiler
```

và:

```text
Windows x64
    ↓
AArch64 iOS compiler
```

Điều này đặc biệt quan trọng vì compiler phải tự build cho các nền tảng mà nó không chạy trực tiếp.

---

# 311.30. Canadian Cross

Architecture phải hỗ trợ cả:

```text
Build
Host
Target
```

khác nhau:

```text
Build machine
    ↓
compiler runs on Host
    ↓
compiler generates Target
```

Ví dụ:

```text
Windows x64
   ↓
Linux ARM64 compiler
   ↓
WASM32
```

Driver đã có khái niệm host/build/target từ BOOTSTRAP-305; nhiệm vụ 311 là biến nó thành bootstrap capability thực sự.

---

# 311.31. Compiler-as-a-Library

Compiler core phải có thể build thành:

```text
libaxiom_compiler
```

với API:

```text
compile(source)
check(source)
analyze(source)
lower(source)
optimize(module)
codegen(module)
link(objects)
```

Điều này giúp:

- IDE;
- language server;
- AI tooling;
- build server;
- documentation generator;
- static analyzer

sử dụng cùng semantic engine.

Không tạo một compiler thứ hai cho IDE.

---

# 311.32. Compiler-as-a-Tool

CLI:

```text
axiom check
axiom build
axiom run
axiom test
axiom fmt
axiom doc
axiom analyze
axiom explain
```

đều gọi cùng compiler core.

Không duplicate semantic implementation.

---

# 311.33. Self-Hosted Formatter

Formatter là một milestone nhỏ nhưng hữu ích.

```text
axiom fmt
```

phải được implement bằng Axiom.

Formatter không được phụ thuộc parser implementation của Stage 0.

Nó sử dụng:

```text
SyntaxDB
```

và semantic-aware formatting khi cần.

---

# 311.34. Self-Hosted Package Manager

Sau compiler ổn định, package manager cũng có thể được viết bằng Axiom:

```text
axiom pkg
```

Nhưng package registry/network không thuộc compiler Core.

Architecture:

```text
Axiom Compiler
Axiom Package Manager
Axiom Build Tool
```

là các executable/library độc lập.

---

# 311.35. Self-Hosted Test Runner

`axiom test` cuối cùng cũng phải chạy bằng chính Axiom.

Test runner sử dụng:

```text
TestDB
BuildDB
CompilerDB
Process
Filesystem
```

nhưng không cần compiler runtime đặc biệt.

---

# 311.36. Bootstrap Failure Recovery

Nếu Stage N bị hỏng:

```text
Stage N-1
```

phải có khả năng rebuild lại.

Không được để bootstrap chain trở thành:

```text
Stage N broken
→ no compiler
→ project chết
```

Do đó repository giữ:

```text
known-good bootstrap compiler
```

và:

```text
bootstrap recipe
```

có version rõ ràng.

---

# 311.37. Compiler Reproducibility Manifest

Mỗi bootstrap build phải có:

```text
bootstrap.manifest
```

chứa:

```text
source revision
compiler revision
target
features
profile
dependency lock
comptime inputs
bootstrap stage
toolchain fingerprint
```

Một build khác phải có thể tái tạo.

---

# 311.38. Self-Hosting Definition of Done

Axiom được coi là **self-hosted** khi đồng thời thỏa:

### Compiler

- compiler source chủ yếu/hoàn toàn viết bằng Axiom;
- Axiom compiler tự compile chính nó.

### Frontend

- lexer/parser/resolver/type system bằng Axiom.

### Semantic

- ownership;
- capability;
- effect;
- trait;
- comptime;
- async;
- GPU legality

đều do Axiom compiler tự xử lý.

### Backend

- MIR;
- optimizer;
- machine IR;
- instruction selection;
- register allocation;
- encoder.

### Binary

- object writer;
- linker;
- executable writer.

### Toolchain

- build graph;
- package integration;
- diagnostics;
- test runner.

### Independence

Production compiler không cần:

```text
LLVM
Clang
GCC
MSVC
GNU as
LLD
```

để tạo native executable.

---

# 311.39. Self-Hosting Definition — mạnh hơn

Không chỉ:

```text
Axiom compiler compiles Axiom compiler
```

mà:

```text
Axiom compiler
    ↓
compiles itself
    ↓
new compiler
    ↓
compiles itself
    ↓
same semantics
```

đạt fixed point.

Đây mới là **self-hosting hoàn chỉnh**.

---

# 311.40. Kiến trúc cuối

Sau BOOTSTRAP-311, toolchain đạt hình dạng:

```text
                    ┌──────────────────┐
                    │ Axiom Source     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Axiom Compiler   │
                    │ written in Axiom │
                    └────────┬─────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
   Frontend              Semantic              CompilerDB
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             ▼
                      Verified MIR
                             │
                             ▼
                        Optimizer
                             │
                             ▼
                       Machine IR
                             │
                             ▼
                         Encoder
                             │
                             ▼
                      Object Writer
                             │
                             ▼
                         Linker
                             │
                             ▼
                    Native Executable
```

Bootstrap:

```text
          Stage 0
      external compiler
             │
             ▼
       Axiom compiler
             │
             ▼
          Stage 1
             │
             ▼
       self compile
             │
             ▼
          Stage 2
             │
             ▼
       self compile
             │
             ▼
       Fixed Point
```

### Các invariant mới

`ABOOT-20` — Bootstrap compiler không phải final semantic dependency.

`ABOOT-21` — Mọi bootstrap stage phải pass toàn bộ semantic validation cần thiết trước khi trở thành trust source.

`ABOOT-22` — Self-hosted compiler phải có khả năng compile chính source tree của nó.

`ABOOT-23` — Self-hosted compiler không được yêu cầu external compiler/assembler/linker trên production path.

`ABOOT-24` — Bootstrap stage phải có provenance có thể kiểm chứng.

`ABOOT-25` — Build/Host/Target phải được phân biệt trong bootstrap.

`ABOOT-26` — Self-hosted compiler phải hỗ trợ cross compilation.

`ABOOT-27` — Compiler rebuild phải đạt deterministic hoặc semantic fixed point.

`ABOOT-28` — Stage N phải có khả năng phục hồi bằng Stage N-1.

`ABOOT-29` — Compiler semantic implementation không được duplicate giữa CLI, IDE, AI và build tools.

`ABOOT-30` — Final compiler phải có khả năng tự tạo object, link và executable.

`ABOOT-31` — External tools chỉ còn là bootstrap/test/debug dependencies, không phải production semantic dependencies.

`ABOOT-32` — Self-hosting không được làm suy yếu ownership, capability, ABI, concurrency hoặc optimization verification.

`ABOOT-33` — Bootstrap artifact phải truy nguyên được về source, compiler và build configuration.

`ABOOT-34` — Self-hosting chỉ được công nhận khi compiler đạt fixed-point validation.

`ABOOT-35` — Axiom compiler phải có khả năng xây dựng lại chính nó từ source theo một bootstrap procedure được định nghĩa và tái lập được.