# BOOTSTRAP-214 — Self-Hosting, Bootstrap Trust, Reproducible Compiler & Compiler-as-Program

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là một mốc rất quan trọng. Từ đây Axiom không còn chỉ là specification của language/compiler, mà bắt đầu đặc tả **cách chính compiler Axiom tồn tại như một chương trình Axiom**.

Nguyên tắc trung tâm:

> **Compiler cuối cùng phải là một chương trình Axiom bình thường, sử dụng chính ownership, comptime, concurrency, GPU/CPU, package, build và tooling model của Axiom; không có “ngôn ngữ đặc biệt bên trong compiler”.**

---

# 214.1. Self-hosting không có nghĩa là bootstrap ngay lập tức

Lộ trình:

```text
Stage 0
External compiler
      │
      ▼
Axiom Frontend
      │
      ▼
LLVM/External Backend
      │
      ▼
Axiom Compiler #1
```

sau đó:

```text
Stage 1
Axiom Compiler source
      │
      ▼
Axiom compiler #1
      │
      ▼
Axiom compiler #2
```

và cuối cùng:

```text
Stage N
Axiom compiler
      │
      ├── Axiom frontend
      ├── Axiom MIR
      ├── Axiom optimizer
      ├── Axiom LIR
      ├── Axiom backend
      ├── Axiom object writer
      └── Axiom linker
```

---

# 214.2. Bootstrap compiler

Compiler ban đầu có thể viết bằng:

```text
C++
Rust
Axiom subset
```

nhưng đây chỉ là **bootstrap implementation**.

Nó không trở thành dependency cuối cùng của Axiom.

---

# 214.3. Bootstrap boundary

Giai đoạn đầu:

```text
Axiom source
    ↓
Bootstrap compiler
    ↓
LLVM
    ↓
LLD/system linker
```

Giai đoạn cuối:

```text
Axiom source
    ↓
Axiom compiler
    ↓
Axiom Machine Backend
    ↓
Axiom Object Writer
    ↓
Axiom Linker
```

---

# 214.4. Không self-host bằng cách bỏ qua verifier

Compiler Axiom phải tự sử dụng:

```text
ownership
capability
type checking
effect analysis
concurrency verification
unsafe contracts
```

như mọi chương trình khác.

Không có:

```text
compiler mode = safety disabled
```

---

# 214.5. Compiler được phép có unsafe

Compiler cần:

```text
file IO
memory mapping
JIT
OS APIs
threads
machine code generation
```

nên có thể dùng `unsafe`.

Nhưng unsafe vẫn phải nằm trong boundary rõ ràng.

---

# 214.6. Compiler architecture

Compiler source tree:

```text
compiler/
├── frontend/
├── syntax/
├── resolver/
├── types/
├── traits/
├── comptime/
├── hir/
├── mir/
├── verifier/
├── optimizer/
├── abi/
├── lir/
├── backend/
├── object/
├── linker/
├── diagnostics/
├── build/
└── driver/
```

---

# 214.7. CompilerDB trở thành semantic foundation

Compiler tiếp tục dùng:

```text
CompilerDB
```

làm trung tâm.

IDE, compiler, AI tooling và build system đều truy cập semantic database.

---

# 214.8. Compiler phases không được circular tùy tiện

Dependency graph phải rõ:

```text
Syntax
 ↓
Resolution
 ↓
Type
 ↓
HIR
 ↓
MIR
 ↓
Verification
 ↓
Optimization
 ↓
Backend
```

Không cho backend gọi ngược semantic frontend theo kiểu tùy tiện.

---

# 214.9. Query architecture

Compiler sử dụng query model:

```text
parse(file)
resolve(module)
type_of(expr)
lower_to_mir(function)
verify(function)
optimize(function)
codegen(function)
```

---

# 214.10. Incremental self-host compiler

Compiler phải hỗ trợ:

```text
source changed
    ↓
dependency invalidation
    ↓
recompute affected queries
```

không rebuild toàn bộ compiler.

---

# 214.11. Compiler bootstrap artifact

Compiler build tạo:

```text
axc
axld
ax
.axmeta
.axlib
```

tùy artifact/profile.

---

# 214.12. Compiler package

Compiler bản thân có thể là một Axiom package:

```text
package axiom.compiler
```

với dependencies được lock.

---

# 214.13. Compiler dependencies

Mục tiêu cuối:

```text
Axiom compiler
    ↓
Axiom core
    ↓
Axiom standard/system libraries
```

Không có:

```text
LLVM
Clang
GCC
Rust compiler
```

trong production toolchain dependency graph.

---

# 214.14. External libraries vẫn được phép

Điều này không có nghĩa Axiom phải tự viết:

```text
OS kernel
CPU microcode
GPU driver
system SDK
```

Các platform artifacts vẫn là external platform dependencies.

---

# 214.15. Compiler bootstrap dependency vs target dependency

Phân biệt:

```text
Bootstrap dependency
= dùng để xây compiler

Target dependency
= OS/SDK/system ABI cần để build application
```

---

# 214.16. Stage 0

```text
External Compiler
       ↓
Axiom frontend subset
       ↓
LLVM
       ↓
native axc
```

Mục tiêu: compiler có thể tự compile phần lớn compiler source.

---

# 214.17. Stage 1

Axiom compiler source đã compile được bằng chính `axc`.

```text
axc₀
 ↓
compile compiler.ax
 ↓
axc₁
```

---

# 214.18. Stage 2

`axc₁` compile lại chính source:

```text
axc₁
 ↓
compiler.ax
 ↓
axc₂
```

---

# 214.19. Bootstrap convergence

Kiểm tra:

```text
axc₁
→ axc₂
→ axc₃
```

Nếu compiler deterministic, artifact/semantic output phải hội tụ theo policy.

---

# 214.20. Semantic equivalence quan trọng hơn byte equality

Hai compiler có thể tạo machine code khác nhau nhưng:

```text
observable semantics
```

phải tương đương.

---

# 214.21. Reproducible compiler build

Với cùng:

```text
source
lockfile
compiler version
target
features
comptime inputs
build profile
```

phải tạo cùng semantic artifact.

---

# 214.22. Bit-reproducible build

Nếu target/profile hỗ trợ, mục tiêu cao hơn:

```text
same inputs
    ↓
same bytes
```

---

# 214.23. Non-deterministic metadata

Compiler phải loại bỏ hoặc canonicalize:

```text
timestamps
random IDs
filesystem ordering
thread scheduling artifacts
```

khỏi reproducible artifacts.

---

# 214.24. Deterministic IDs

Semantic IDs không được phụ thuộc vào:

```text
hash-map iteration order
thread scheduling
```

---

# 214.25. Deterministic parallel compilation

Compiler có thể compile song song:

```text
A
B
C
D
```

nhưng kết quả semantic phải deterministic.

---

# 214.26. Parallel compiler

Compiler itself sử dụng:

```text
Thread
Task
Work stealing
Incremental queries
```

để compile nhanh.

---

# 214.27. Compiler memory management

Compiler là test cực mạnh cho memory model Axiom.

Compiler không được cần:

```text
GC
```

để hoạt động.

---

# 214.28. Arena allocation

Compiler có thể dùng:

```text
Arena
BumpAllocator
InternPool
```

ở library layer.

---

# 214.29. Persistent semantic database

`CompilerDB` có thể sử dụng:

```text
interned immutable structures
arena
content-addressed storage
```

để giảm allocation.

---

# 214.30. Compiler cache

Cache key:

```text
SemanticFingerprint
+
CodegenFingerprint
+
Target
+
Profile
```

---

# 214.31. Semantic cache

Nếu source thay đổi nhưng public semantics không thay đổi:

```text
downstream semantic work
```

có thể được giữ lại.

---

# 214.32. Codegen cache

Machine artifact cache phải key theo:

```text
target
CPU features
optimization profile
compiler codegen version
```

---

# 214.33. Bootstrap compiler comparison

Build:

```text
bootstrap compiler
Axiom compiler
```

rồi compile cùng test suite.

---

# 214.34. Differential compiler testing

So sánh:

```text
ax-bootstrap
ax-selfhosted
reference interpreter
```

trên semantic corpus.

---

# 214.35. Translation validation

Các optimization vẫn được kiểm tra như 188:

```text
MIR before
      ↓
optimization
      ↓
MIR after
```

phải preserve semantics.

---

# 214.36. Compiler self-tests

Compiler binary chứa/đi kèm test suites:

```text
frontend tests
type tests
MIR tests
verifier tests
backend tests
linker tests
```

---

# 214.37. Stage-specific tests

Mỗi bootstrap stage phải chạy:

```text
L0 unit
L1 parser
L2 semantic
L3 MIR
L4 optimizer
L5 backend
L6 native execution
L7 self-host
```

---

# 214.38. Bootstrap invariant

Compiler mới không được coi là thành công chỉ vì:

```text
compiler builds itself
```

Mà phải:

```text
compiler builds itself
+
tests pass
+
semantic conformance pass
+
bootstrap convergence
```

---

# 214.39. Diverse double compilation

Một compiler bootstrap đáng tin cậy có thể:

```text
Compiler A
    ↓
compile compiler source
    ↓
Compiler B
```

và kiểm tra output.

---

# 214.40. Trust bootstrapping

Có thể dùng:

```text
trusted bootstrap compiler
```

ban đầu.

Sau đó giảm dần dependency trust.

---

# 214.41. Diverse bootstrap

Mục tiêu cao hơn:

```text
Bootstrap Compiler A
        ↓
Axiom Compiler B
        ↓
Axiom Compiler C
```

và kiểm tra B/C không phụ thuộc artifact bất thường của A.

---

# 214.42. Compiler self-reproduction

Compiler source phải có khả năng:

```text
ax build compiler
```

mà không cần script bí mật bên ngoài.

---

# 214.43. Build orchestration

Build graph:

```text
compiler source
 ↓
frontend
 ↓
semantic libs
 ↓
backend
 ↓
linker
 ↓
ax
```

được mô hình hóa bởi build system.

---

# 214.44. Compiler stages as packages/modules

Không nhất thiết mỗi compiler phase là package riêng.

Module boundary được thiết kế để:

```text
dependency direction
incremental compilation
testing
```

rõ ràng.

---

# 214.45. Compiler plugins

Không cho compiler plugin tùy tiện mutate semantic state.

Compiler extension phải dùng:

```text
defined compiler APIs
```

---

# 214.46. Backend plugins

Backend có thể modular:

```text
x86
ARM
RISC-V
WASM
GPU
```

nhưng interface được version hóa.

---

# 214.47. Backend loading

Compiler có thể:

```text
static backend
dynamic backend
```

tùy distribution.

Minimal compiler có thể chỉ chứa một target backend.

---

# 214.48. Cross compiler

Một compiler Axiom có thể:

```text
host = x86-64 Linux
target = ARM64 bare-metal
```

không cần compiler ARM riêng.

---

# 214.49. Bootstrap cross compilation

Stage bootstrap cần tối thiểu:

```text
host compiler
target backend
```

---

# 214.50. Canadian cross

Hỗ trợ:

```text
Build machine
Host machine
Target machine
```

độc lập.

Ví dụ:

```text
Build: x86 Linux
Host:  ARM64 Linux
Target: RISC-V
```

---

# 214.51. Compiler artifact portability

`.axlib`/`.axmeta` phải chứa đủ thông tin để compiler khác host có thể sử dụng.

---

# 214.52. Host-dependent comptime

Comptime execution phải phân biệt:

```text
host environment
target environment
```

đã được quy định ở 194.

---

# 214.53. Compiler itself and comptime

Compiler source có thể dùng comptime để generate:

```text
token tables
instruction tables
Unicode tables
ISA descriptions
```

---

# 214.54. Generated compiler code

Generated declarations:

```text
ISA table
opcode table
parser tables
```

đều quay lại pipeline:

```text
resolve
typecheck
verify
```

---

# 214.55. No hidden compiler language

Compiler không được cần một DSL bí mật cho:

```text
opcode definitions
parser definitions
optimization rules
```

trừ data-description format thuần túy khi thực sự cần.

---

# 214.56. Machine description

ISA database có thể là structured data:

```text
instruction
operands
encoding
feature
latency
throughput
constraints
```

Comptime generate backend tables.

---

# 214.57. Compiler rule representation

Optimization rules có thể là ordinary Axiom code:

```text
if proof_available(...) {
    transform(...)
}
```

nhưng transform API được kiểm soát.

---

# 214.58. Compiler IR mutation safety

Compiler được phép mutate internal IR vì đây là compiler implementation, nhưng:

```text
production semantic IR
```

phải luôn có explicit phase boundary.

---

# 214.59. Verified MIR boundary

Điểm trust quan trọng nhất:

```text
Typed MIR
   ↓
Verifier
   ↓
Verified MIR
```

Sau đó optimizer không được tự ý phá invariants.

---

# 214.60. Optimizer proof obligations

Mỗi pass:

```text
requires
ensures
preserves
```

được machine-readable.

---

# 214.61. Backend proof boundary

Machine lowering phải preserve:

```text
observable behavior
ABI
memory semantics
atomic semantics
volatile semantics
panic/error semantics
```

---

# 214.62. Linker correctness

Axiom linker cũng nằm trong trust chain:

```text
Object
 ↓
Link
 ↓
Executable
```

Không được xem linker như tool "ngoài semantic system".

---

# 214.63. Linker self-hosting

Cuối cùng:

```text
ax compiler
+
ax linker
```

đều do Axiom build.

---

# 214.64. Object writer self-hosting

Tương tự:

```text
PE
ELF
Mach-O
WASM
```

writers được implement bằng Axiom.

---

# 214.65. System linker không còn bắt buộc

Final toolchain:

```text
Axiom source
 ↓
Axiom compiler
 ↓
Axiom object writer
 ↓
Axiom linker
 ↓
native executable
```

---

# 214.66. Platform SDK vẫn tồn tại

Ví dụ Windows:

```text
Windows SDK
```

hoặc Linux system ABI vẫn có thể là target dependency.

Điều này **không mâu thuẫn** với "không phụ thuộc third-party compiler".

---

# 214.67. Compiler distribution

Có thể phân phối:

```text
ax.exe
axld.exe
stdlib
target databases
metadata
```

hoặc một integrated:

```text
ax.exe
```

---

# 214.68. Single-driver tool

User-facing:

```text
ax build
ax run
ax test
ax check
ax fmt
ax doc
ax inspect
ax explain
ax package
ax publish
```

---

# 214.69. Internal tools

Developer mode có thể expose:

```text
axc
axld
ax-ir
ax-mir
ax-opt
ax-obj
```

nhưng không cần người dùng bình thường biết.

---

# 214.70. Compiler as semantic server

`ax` có thể chạy persistent:

```text
IDE
  ↓
AXCP
  ↓
CompilerDB
```

để tránh reload compiler mỗi request.

---

# 214.71. Compiler daemon

Optional:

```text
axd
```

giữ:

```text
CompilerDB
PackageDB
cache
semantic snapshots
```

trong memory.

---

# 214.72. Compiler crash isolation

Một lỗi compiler:

```text
ICE
```

phải tạo:

```text
diagnostic
reproducer
semantic snapshot
```

nếu khả thi.

---

# 214.73. Compiler reproducible crash

AI/tooling có thể lấy:

```text
source revision
compiler version
target
feature set
comptime inputs
query
```

để tái hiện.

---

# 214.74. Compiler self-debugging

CompilerDB có thể inspect chính compiler:

```text
ax inspect compiler
ax explain compiler-query
```

---

# 214.75. Compiler performance

Compiler phải có profiling:

```text
parse
resolve
trait solve
comptime
MIR
verify
optimization
codegen
link
```

---

# 214.76. Incremental compiler metrics

Ví dụ:

```text
changed files: 3
reused queries: 98.2%
recompiled functions: 147
reused machine artifacts: 92%
```

---

# 214.77. AI compiler interface

AI có thể yêu cầu:

```text
compile
check
explain
inspect
```

và nhận structured response.

---

# 214.78. AI không được thay compiler

AI có thể:

```text
generate code
suggest fix
query semantic state
```

nhưng compiler vẫn quyết định:

```text
valid
invalid
safe
unsafe
```

---

# 214.79. Self-hosted AI tooling

Compiler source itself có thể expose:

```text
Semantic API
Diagnostic API
IR API
Optimization API
```

cho AI agents.

---

# 214.80. Compiler source as canonical specification

Một khi self-host hoàn tất:

```text
Language Specification
+
Reference semantics
+
Compiler implementation
+
Conformance tests
```

là ba lớp kiểm chứng lẫn nhau.

Không dùng compiler implementation một mình làm specification.

---

# 214.81. Reference interpreter vẫn tồn tại

`ax-ref` không bị xóa sau self-host.

Nó là semantic oracle.

---

# 214.82. MIR interpreter vẫn tồn tại

`ax-mir` giúp:

```text
compiler debugging
optimizer validation
backend differential testing
```

---

# 214.83. Bootstrap test matrix

Mỗi release compiler có thể test:

```text
Bootstrap A → B
B → C
C → D
```

và:

```text
Reference
MIR
Native
WASM
```

---

# 214.84. Compiler version identity

Phân biệt:

```text
LanguageSemanticVersion
CompilerVersion
CodegenVersion
ABI Version
ToolProtocolVersion
```

đã có từ các task trước.

---

# 214.85. Compiler update

Một compiler mới không được silently thay đổi semantics.

Thay đổi language semantics phải:

```text
language version
migration
conformance update
```

---

# 214.86. Compiler bug compatibility

Nếu compiler cũ compile sai chương trình:

```text
bug
```

không trở thành language semantic guarantee.

---

# 214.87. Miscompilation regression

Mỗi miscompile được thêm:

```text
regression test
```

và nếu có thể:

```text
minimal reproducer
```

---

# 214.88. Compiler security

Compiler xử lý:

```text
untrusted source
untrusted package
untrusted metadata
untrusted model/code generation
```

phải không được thực thi arbitrary code ngoài capability contract.

---

# 214.89. Untrusted comptime

Comptime sandbox vẫn áp dụng cho compiler source.

---

# 214.90. Build script isolation

Compiler build scripts không được có quyền vượt quá declared capability.

---

# 214.91. Supply chain

Compiler release có:

```text
source hash
artifact hash
signature
dependency provenance
build recipe
```

---

# 214.92. Reproducible release

Release pipeline:

```text
Source
 ↓
Pinned dependencies
 ↓
Hermetic build
 ↓
Compiler
 ↓
Tests
 ↓
Bootstrap
 ↓
Reproducibility check
 ↓
Artifact
```

---

# 214.93. Stage-N compiler trust

Compiler release chỉ được công nhận nếu:

```text
semantic conformance
+
bootstrap convergence
+
reproducible build
+
backend tests
+
linker tests
```

đạt.

---

# 214.94. Diverse bootstrap trust

Mục tiêu dài hạn:

```text
Independent implementation A
          ↓
       Axiom
          ↓
Compiler B

Independent implementation C
          ↓
       Axiom
          ↓
Compiler D
```

Nếu B và D hội tụ về artifact/semantic behavior, confidence tăng đáng kể.

---

# 214.95. Compiler source independence

Không để compiler source chứa:

```text
generated binary blob
```

là một phần bắt buộc của source tree.

Nếu generated tables cần thiết:

```text
source specification
→ comptime generation
```

phải tồn tại.

---

# 214.96. Bootstrap seed

Một release bootstrap có thể được cung cấp dưới dạng:

```text
binary
+
source
+
bootstrap metadata
```

để build lại.

---

# 214.97. Trust root

Trust chain:

```text
Axiom Language Semantics
        ↓
Reference Interpreter
        ↓
Conformance Tests
        ↓
Bootstrap Compiler
        ↓
Self-hosted Compiler
        ↓
Self-hosted Linker
        ↓
Native Toolchain
```

Không một compiler binary duy nhất được coi là "sự thật tuyệt đối".

---

# 214.98. Compiler invariants — `ACOMPILER`

### `ACOMPILER-20`
The final Axiom compiler shall be implementable in Axiom.

### `ACOMPILER-21`
Self-hosted compiler code shall obey ordinary Axiom semantic rules.

### `ACOMPILER-22`
Compiler self-hosting shall not require a special unsafe semantic mode.

### `ACOMPILER-23`
Bootstrap implementations shall be temporary implementation dependencies.

### `ACOMPILER-24`
Final compilation shall not require a third-party compiler.

### `ACOMPILER-25`
Final native linking shall not require a third-party linker.

### `ACOMPILER-26`
Platform SDKs and system ABI dependencies may remain legitimate target dependencies.

### `ACOMPILER-27`
Bootstrap stages shall be explicitly versioned.

### `ACOMPILER-28`
Self-hosting shall require semantic conformance, not merely successful compilation.

### `ACOMPILER-29`
Compiler bootstrap shall support deterministic rebuilds.

### `ACOMPILER-30`
Parallel compiler execution shall remain semantically deterministic.

### `ACOMPILER-31`
Compiler caches shall be keyed by complete semantic/codegen identity.

### `ACOMPILER-32`
Incremental compilation shall invalidate all semantically affected queries.

### `ACOMPILER-33`
Stale semantic data shall never enter production code generation.

### `ACOMPILER-34`
Verified MIR shall remain the compiler correctness boundary.

### `ACOMPILER-35`
Optimization passes shall declare proof preconditions and preserved invariants.

### `ACOMPILER-36`
Backend lowering shall preserve observable semantics.

### `ACOMPILER-37`
Linking shall preserve ABI and observable program behavior.

### `ACOMPILER-38`
Reference interpretation shall remain available as an independent semantic oracle.

### `ACOMPILER-39`
MIR interpretation shall remain available for intermediate validation.

### `ACOMPILER-40`
Compiler implementations shall be differentially testable.

### `ACOMPILER-41`
Every confirmed miscompilation shall become a regression test.

### `ACOMPILER-42`
Compiler output shall be reproducible under fixed build inputs where the target/profile permits.

### `ACOMPILER-43`
Build timestamps and nondeterministic ordering shall not contaminate reproducible artifacts.

### `ACOMPILER-44`
Compiler semantic IDs shall not depend on nondeterministic iteration order.

### `ACOMPILER-45`
Compiler source shall not depend on opaque generated binary blobs.

### `ACOMPILER-46`
Generated compiler tables shall have reproducible source specifications.

### `ACOMPILER-47`
Comptime-generated compiler code shall re-enter ordinary compiler verification.

### `ACOMPILER-48`
Compiler plugins shall not bypass semantic verification.

### `ACOMPILER-49`
Backend modules shall obey versioned compiler interfaces.

### `ACOMPILER-50`
Compiler and linker artifacts shall preserve target and ABI identity.

### `ACOMPILER-51`
Cross compilation shall distinguish Build, Host, and Target.

### `ACOMPILER-52`
Self-hosted compiler shall support incremental compilation.

### `ACOMPILER-53`
Self-hosted compiler shall support parallel compilation.

### `ACOMPILER-54`
Self-hosted compiler shall support compiler diagnostics through CompilerDB.

### `ACOMPILER-55`
Self-hosted compiler shall expose structured machine-readable diagnostics.

### `ACOMPILER-56`
AI tooling shall interact with compiler semantics through defined compiler interfaces.

### `ACOMPILER-57`
AI-generated compiler source shall undergo the same verification as human-written source.

### `ACOMPILER-58`
Compiler crash reports shall preserve sufficient reproducibility context.

### `ACOMPILER-59`
Bootstrap trust shall not rely solely on the output of one compiler implementation.

### `ACOMPILER-60`
Independent reference semantics and conformance tests shall remain part of the toolchain.

### `ACOMPILER-61`
Self-hosting shall not require garbage collection.

### `ACOMPILER-62`
Self-hosting shall not require a mandatory language runtime.

### `ACOMPILER-63`
Self-hosting shall be possible in hosted and appropriate freestanding configurations.

### `ACOMPILER-64`
The compiler shall be capable of compiling the complete Axiom language it claims to implement.

### `ACOMPILER-65`
The compiler shall be capable of compiling its own source tree.

### `ACOMPILER-66`
A successful self-build shall produce a functionally conforming compiler.

### `ACOMPILER-67`
Bootstrap convergence shall be continuously tested.

### `ACOMPILER-68`
Compiler implementation details shall not silently become language semantics.

### `ACOMPILER-69`
Language semantics shall remain independently specified and tested.

### `ACOMPILER-70`
The final Axiom toolchain shall be capable of existing as an Axiom-native software stack.

---

# 214.99. Kiến trúc bootstrap cuối cùng

Toàn bộ mục tiêu ban đầu của Axiom giờ có thể biểu diễn thành:

```text
                    AXIOM LANGUAGE
                          │
                          ▼
                    Axiom Compiler
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
    Frontend          Semantic Core       CompilerDB
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
                         MIR
                          │
                       Verifier
                          │
                    Verified MIR
                          │
                       OptIR
                          │
                    Axiom LIR
                          │
                    Machine Backend
                          │
                  Axiom Object Writer
                          │
                    Axiom Linker
                          │
                          ▼
                 Native Executable
```

Và chính compiler này:

```text
          Axiom Compiler Source
                    │
                    ▼
              Axiom Compiler
                    │
                    ▼
          recompiles itself
                    │
                    ▼
          Axiom Compiler 2
                    │
                    ▼
          reproducibility /
          conformance /
          bootstrap tests
```

Đây là **self-hosting thật sự**, chứ không chỉ là "compiler được viết bằng Axiom".

---

# BOOTSTRAP-215 — Compiler Specification hoàn chỉnh & Formal Semantic Kernel

**TRẠNG THÁI: NEXT**

Sau 214, phần còn thiếu quan trọng nhất không còn là thêm một feature ứng dụng. Đã đến lúc **khóa semantic foundation của toàn bộ Axiom**.

215 sẽ gom toàn bộ các quyết định đã đóng băng thành một **Formal Semantic Kernel**:

```text
Source
  ↓
Lexical semantics
  ↓
Expression semantics
  ↓
Type semantics
  ↓
Ownership semantics
  ↓
Capability semantics
  ↓
Effect semantics
  ↓
Concurrency semantics
  ↓
Async semantics
  ↓
Comptime semantics
  ↓
GPU semantics
  ↓
FFI semantics
  ↓
Observable behavior
```

Trọng tâm:

- small-step / big-step operational semantics;
- value/move/copy/drop semantics;
- capability validity;
- aliasing;
- evaluation order;
- panic/Result/never;
- atomic memory model;
- async suspension;
- GPU execution;
- FFI boundary;
- unsafe boundary;
- observable behavior;
- semantic equivalence;
- optimization correctness;
- MIR as executable semantic representation;
- Reference Interpreter;
- compiler conformance.

**215 sẽ là bước để biến hàng trăm quyết định `A...-xx` hiện tại thành một semantic model thống nhất, tránh tình trạng specification lớn dần nhưng các phần riêng lẻ vô tình mâu thuẫn nhau.**