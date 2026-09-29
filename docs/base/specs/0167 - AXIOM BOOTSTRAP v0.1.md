Tiếp theo là **AXIOM BOOTSTRAP + SELF-HOSTING v0.1**. Đây là một trong những phần quan trọng nhất của toàn dự án, vì mục tiêu cuối cùng của Axiom là **compiler của Axiom được viết bằng chính Axiom và không cần compiler C/C++ để tồn tại**.

# AXIOM BOOTSTRAP v0.1

## 1. Mục tiêu cuối cùng

Ta muốn đi từ:

```text
                    Giai đoạn đầu
                         │
                         ▼
              C/C++ Bootstrap Compiler
                         │
                         ▼
                 Axiom Compiler
                         │
                         ▼
                Axiom compiler.ax
                         │
                         ▼
             Axiom compiler tự compile
                         │
                         ▼
              Axiom Self-Hosted Compiler
                         │
                         ▼
             Không còn C/C++ dependency
```

Nhưng có một điểm cần phân biệt:

> **“Compiler không phụ thuộc C/C++”** không có nghĩa là **“không bao giờ có thể link với C”**.

Axiom vẫn cần C ABI/FFI để interoperability.

Cái cần loại bỏ là:

```text
Axiom compiler
    ↓
requires GCC/Clang/MSVC
```

không phải:

```text
Axiom program
    ↓
extern "C"
```

---

# 2. Bootstrap không nên viết toàn bộ compiler C++

Đây là quyết định quan trọng.

Không nên:

```text
C++ compiler
 ├── lexer
 ├── parser
 ├── HIR
 ├── type checker
 ├── ownership
 ├── MIR
 ├── optimizer
 ├── backend
 └── linker
```

rồi sau đó port toàn bộ sang Axiom.

Quá tốn công và dễ tạo **hai compiler khác nhau về semantics**.

Thay vào đó:

> C/C++ chỉ được dùng để xây **Bootstrap Compiler tối thiểu** đủ để Axiom tự xây phần còn lại.

---

# 3. Bootstrap compiler tối thiểu

Giai đoạn B0:

```text
bootstrap/
├── lexer
├── parser
├── resolver
├── typeck
├── mir
├── verifier
├── basic_codegen
└── driver
```

Không cần:

```text
async
GPU
reflection
advanced optimizer
dynamic linker
```

Thậm chí chưa cần full trait solver.

Mục tiêu chỉ là:

```text
fn
struct
enum
let
var
if
while
function call
return
basic generics
ownership
basic view
```

đủ để compile compiler kernel.

---

# 4. Bootstrap compiler không phải production compiler

Đặt tên rõ:

```text
ax-bootstrap
```

và:

```text
axiomc
```

Production.

`ax-bootstrap` có thể:

- chậm
- ít optimization
- diagnostics xấu hơn
- hỗ trợ ít syntax
- chỉ target x86-64 Linux

Nhưng phải có một thuộc tính:

> **Semantic correctness đủ để compile Axiom compiler.**

---

# 5. Stage 0

```text
Stage 0
```

compiler viết bằng C/C++:

```text
bootstrap compiler
```

Input:

```text
*.ax
```

Output:

```text
x86-64 ELF
```

Pipeline:

```text
Axiom source
 ↓
C++ bootstrap compiler
 ↓
Axiom native binary
```

---

# 6. Stage 1

Ta bắt đầu viết production compiler bằng Axiom:

```text
compiler/
├── kernel/
├── source/
├── lexer/
├── parser/
...
```

Một phần đầu tiên:

```text
compiler/kernel/*.ax
compiler/lexer/*.ax
```

được compile bằng:

```text
ax-bootstrap
```

Kết quả:

```text
axiomc-stage1
```

---

# 7. Stage 2

Sau khi Stage 1 đủ mạnh:

```text
axiomc-stage1
```

tự compile source compiler:

```text
compiler/*.ax
```

→

```text
axiomc-stage2
```

Tức:

```text
C++ bootstrap
       ↓
 Axiom compiler 1
       ↓
 Axiom compiler 2
```

---

# 8. Self-hosting criterion

Không gọi là self-hosting chỉ vì compiler có source `.ax`.

Phải đạt:

```text
axiomc-stage1
    compiles
        ↓
axiomc-stage2
    compiles
        ↓
axiomc-stage3
```

và:

```text
stage2 ≡ stage3
```

về compiler behavior.

---

# 9. Three-stage bootstrap test

Đề nghị:

```text
Stage A:
bootstrap compiler

Stage B:
compile compiler source → compiler-B

Stage C:
compiler-B compile compiler source → compiler-C
```

Sau đó:

```text
compiler-B
    ↓ compile
compiler-C
```

Nếu:

```text
compiler-C
```

có thể tiếp tục tự compile:

```text
compiler-D
```

thì bootstrap đã ổn định.

---

# 10. Reproducibility mạnh hơn

Nếu có thể:

```text
compiler-B binary
```

dùng để compile source tạo:

```text
compiler-C binary
```

và:

```text
compiler-C
```

lại tạo:

```text
compiler-D
```

ta kiểm tra:

```text
hash(C) == hash(D)
```

Nếu giống byte-for-byte:

> Đây là **self-reproducing compiler**.

Nếu chưa giống byte-for-byte nhưng semantics tương đương thì vẫn có thể chấp nhận, nhưng deterministic bootstrap là mục tiêu cao hơn.

---

# 11. Compiler source tree

Production compiler cuối cùng:

```text id="boot-tree"
compiler/
├── kernel/
├── source/
├── lexer/
├── parser/
├── ast/
├── resolver/
├── hir/
├── typeck/
├── traits/
├── ownership/
├── capability/
├── drop/
├── async/
├── mir/
├── verifier/
├── optimizer/
├── abi/
├── lir/
├── backend/
├── object/
├── linker/
└── driver/
```

Tất cả:

```text
.ax
```

trừ một số thứ target-specific ban đầu nếu thực sự cần.

---

# 12. Không để bootstrap code trở thành “vĩnh viễn”

Tạo:

```text
bootstrap/
```

nhưng đặt quy tắc:

```text
bootstrap code ≠ production implementation
```

Bootstrap compiler chỉ tồn tại để:

```text
bootstrap → self-host
```

Sau đó có thể bỏ.

---

# 13. Stage 0 không cần own linker ngay?

Ở giai đoạn đầu:

```text
Axiom compiler
 ↓
Axiom object
 ↓
system linker
```

vẫn chấp nhận.

Nhưng sau khi:

```text
Axiom Linker v0.1
```

hoạt động:

```text
Axiom compiler
 ↓
Axiom Object
 ↓
Axiom Linker
 ↓
ELF
```

được dùng trong bootstrap.

Mục tiêu cuối:

```text
no GCC
no Clang
no GNU ld
no MSVC linker
```

cho native Axiom build.

---

# 14. Nhưng còn assembler?

Không cần.

Ta đã quyết định:

```text
Machine IR
 ↓
Encoder
 ↓
Object
```

Do đó:

```text
NO assembler dependency
```

Đây là một lợi thế lớn.

---

# 15. Toolchain cuối

Linux:

```text
axiom
axiomc
axiom-link
axiom-ar
axiom-objdump
axiom-nm
```

Tất cả được build bằng Axiom.

```text
Axiom source
 ↓
Axiom compiler
 ↓
Axiom linker
 ↓
Axiom executable
```

---

# 16. Bootstrap dependency graph

Cuối cùng:

```text
┌──────────────────────────────┐
│        Axiom Compiler        │
│          written in          │
│            Axiom             │
└──────────────┬───────────────┘
               │
               ▼
       Axiom Machine Code
               │
               ▼
          Axiom Object
               │
               ▼
          Axiom Linker
               │
               ▼
       Native Axiom Binary
```

Không có:

```text
C compiler
C++ compiler
LLVM
GCC
Clang
```

ở runtime/build dependency bắt buộc.

---

# 17. LLVM có được dùng không?

Có thể dùng **tạm thời** trong bootstrap nếu muốn tăng tốc phát triển.

Ví dụ:

```text
Axiom
 ↓
MIR
 ↓
LLVM bridge
 ↓
native
```

Nhưng đây phải là:

```text
bootstrap backend
```

không phải architecture chính.

Sau đó:

```text
LLVM backend
      ↓
Axiom x86 backend
```

và cuối cùng xóa LLVM dependency.

---

# 18. Tôi đề nghị chia bootstrap thành 4 lớp

### B0 — External bootstrap

```text
C/C++ or LLVM
```

### B1 — Axiom frontend self-host

```text
lexer
parser
resolver
typeck
HIR
```

### B2 — Axiom backend self-host

```text
MIR
optimizer
LIR
x86 backend
encoder
object
```

### B3 — Full toolchain self-host

```text
compiler
linker
ar
objdump
debug tools
```

---

# 19. Thứ tự chuyển sang Axiom

Không chuyển theo thư mục.

Chuyển theo dependency:

```text
1. kernel
2. source
3. diagnostics
4. lexer
5. parser
6. AST
7. resolver
8. HIR
9. typeck
10. trait solver
11. ownership
12. capability
13. MIR
14. verifier
15. optimizer
16. LIR
17. x86 backend
18. encoder
19. ELF writer
20. linker
21. driver
```

---

# 20. Compiler Kernel là thứ đầu tiên phải self-host

Ví dụ:

```text
compiler/kernel/
```

chứa:

```text
FileId
Span
SymbolId
TypeId
FunctionId
LocalId
BlockId
InstrId
Diagnostics
Interner
Arena
Query
Cache
```

Nếu kernel không ổn định, toàn compiler phía trên sẽ rất khó kiểm soát.

---

# 21. Query system phải self-host sớm

Axiom compiler có:

```text
parse(FileId)
resolve(ModuleId)
hir(ItemId)
type(TypeQuery)
mir(FunctionId)
verified_mir(FunctionId)
abi(FunctionId)
object(ObjectQuery)
```

Nếu query system viết bằng C++ mãi, compiler sẽ luôn phụ thuộc C++ infrastructure.

Vì vậy:

```text
kernel
 ↓
query system
```

nên chuyển sang Axiom sớm.

---

# 22. Self-host compiler không có nghĩa mọi thứ phải “dynamic”

Ngược lại.

Compiler Axiom nên dùng mạnh:

```text
struct
enum
trait
generic
arena
Vec
Map
Option
Result
```

nhưng compiler optimizer có thể erase abstraction.

Ví dụ:

```axiom id="boot-example"
struct Span {
    file: FileId
    start: u32
    end: u32
}
```

Trong machine code có thể chỉ là:

```text
3 × integer
```

không cần object.

---

# 23. Compiler memory strategy

Đây là nơi memory model Axiom vừa thiết kế sẽ được kiểm chứng thực tế.

Compiler có thể dùng:

```text
Arena
```

cho:

```text
AST
HIR
MIR
temporary analysis objects
```

và:

```text
Vec
Map
```

cho collections.

Không cần GC.

Ví dụ:

```text id="boot-memory"
CompilerSession
 ├── SourceArena
 ├── AstArena
 ├── HirArena
 ├── TypeInterner
 ├── SymbolTable
 └── QueryCache
```

Kết thúc compilation:

```text
drop session
```

→ cleanup toàn bộ arena.

---

# 24. Đây là bằng chứng quan trọng cho triết lý Axiom

Nếu compiler lớn có thể viết sạch bằng:

```text
ownership
arena
view
mut_view
```

mà không cần:

```text
GC
borrow syntax
lifetime annotations
```

thì chính compiler là một **dogfood test** cực mạnh cho thiết kế ngôn ngữ.

---

# 25. Compiler không nên dùng `unsafe` khắp nơi

Ban đầu có thể cần unsafe cho:

```text
OS
mmap
file I/O
machine code
ELF
memory mapped data
```

Nhưng architecture:

```text
unsafe boundary
      ↓
safe abstraction
      ↓
rest of compiler
```

Ví dụ:

```text
ELF parser
    ↓
unsafe byte access
    ↓
validated ELF structure
    ↓
safe linker
```

Không để toàn compiler biến thành unsafe code.

---

# 26. Self-hosting compiler phải tự compile chính nó

Test:

```text
axiom build compiler
```

→

```text
axiomc
```

Sau đó:

```text
./axiomc build compiler
```

→

```text
axiomc-next
```

Sau đó:

```text
./axiomc-next build compiler
```

→

```text
axiomc-next2
```

---

# 27. Compiler identity

Có một vấn đề tinh tế:

```text
compiler-B
```

compile:

```text
compiler source
```

thì source có thể tự nhận diện compiler version.

Không được embed timestamp ngẫu nhiên.

Compiler binary identity nên dựa trên:

```text
compiler source hash
spec hash
target
build profile
compiler configuration
```

---

# 28. Stage bootstrap manifest

Tạo:

```text
bootstrap/bootstrap.toml
```

concept:

```text
bootstrap_compiler = "external"

stage1:
    compiler = "bootstrap"

stage2:
    compiler = "stage1"

stage3:
    compiler = "stage2"

verify:
    reproducible = true
```

Không cần TOML thật nếu Axiom build system sau này dùng format riêng; đây chỉ là semantic model.

---

# 29. Trust bootstrap

Có một câu hỏi sâu hơn:

> Làm sao tin compiler bootstrap?

Dùng **diverse bootstrap verification**.

Ví dụ:

```text
C++ bootstrap
        ↓
compiler A
```

và:

```text
LLVM bootstrap
        ↓
compiler B
```

Cùng compile Axiom compiler source.

Nếu:

```text
A semantics == B semantics
```

ta giảm nguy cơ một bootstrap implementation có bug.

Đây là hướng về sau, không cần MVP.

---

# 30. Stage0 attack surface

Bootstrap compiler càng lớn:

```text
more code
→ more bugs
→ more trust
```

Vì vậy:

> Stage0 nên càng nhỏ càng tốt, nhưng **không cần ép production compiler có core nhỏ**.

Đây khớp với quyết định trước của chúng ta:

**Axiom không tối ưu “minimal language core”; chỉ tối ưu complexity mà programmer phải gánh.**

---

# 31. Self-hosting invariants

Chốt:

```text
ABOOT-20
Bootstrap compiler must compile the defined Axiom subset.

ABOOT-21
Bootstrap semantics must conform to Axiom specification.

ABOOT-22
Bootstrap implementation must not define Axiom semantics.

ABOOT-23
Production compiler semantics must not depend on bootstrap implementation details.

ABOOT-24
Stage N must be able to compile the production compiler source required by Stage N+1.

ABOOT-25
Self-hosting compiler must be capable of compiling itself.

ABOOT-26
Bootstrap compiler is transitional infrastructure.

ABOOT-27
System compiler dependencies are not required by the final native toolchain.

ABOOT-28
Assembler dependency is not required by the final native toolchain.

ABOOT-29
Axiom linker is sufficient for final native linking.

ABOOT-30
Bootstrap stages must be reproducible.

ABOOT-31
Compiler stage transitions must be independently testable.

ABOOT-32
Compiler binaries must not embed nondeterministic build identity.

ABOOT-33
Self-hosted compiler must pass the same conformance suite as bootstrap compiler.

ABOOT-34
Self-hosted compiler output must be differentially testable against Oracle.

ABOOT-35
Self-hosting does not require abandoning C ABI interoperability.

ABOOT-36
Bootstrap-specific code must not silently become part of the language specification.
```

---

# 32. Bootstrap milestones

```text
BOOT-010
Minimal external compiler

BOOT-011
Compile kernel.ax

BOOT-012
Compile lexer.ax

BOOT-013
Compile parser.ax

BOOT-014
Compile resolver.ax

BOOT-015
Compile type checker

BOOT-016
Compile MIR

BOOT-017
Compile verifier

BOOT-018
Compile optimizer

BOOT-019
Compile x86 backend

BOOT-020
Compile ELF writer

BOOT-021
Compile Axiom linker

BOOT-022
Stage-1 axiomc

BOOT-023
Stage-1 self-compilation

BOOT-024
Stage-2 axiomc

BOOT-025
Stage-2 reproducibility

BOOT-026
Remove external compiler

BOOT-027
Remove external linker

BOOT-028
Remove external assembler

BOOT-029
Fully self-hosted Linux toolchain
```

---

# 33. Nhưng còn Windows/macOS/ARM?

**Chưa chuyển ngay.**

Self-host đầu tiên:

```text
x86-64
Linux
ELF
```

vì đây là target backend + linker đầu tiên đã thiết kế.

Sau khi bootstrap ổn định:

```text
x86-64 Linux
       ↓
x86-64 Windows PE/COFF
       ↓
AArch64 Linux
       ↓
AArch64 Android
       ↓
AArch64 macOS
       ↓
WASM
```

Compiler frontend vẫn giữ nguyên.

Chỉ thay:

```text
Target
ABI
LIR legalization
Machine backend
Object writer
Linker
```

---

# 34. Một điều tôi muốn bổ sung vào kiến trúc hiện tại

Ta đã có:

```text
compiler/
targets/
oracle/
tests/
```

Bây giờ nên chính thức thêm:

```text id="boot-repo"
bootstrap/
├── README.md
├── stage0/
├── stage1/
├── stage2/
├── scripts/
└── verification/
```

và:

```text
tools/
├── harness/
├── bootstrap/
└── diagnostics/
```

---

# 35. Sau Bootstrap, chưa nên mở rộng language features

Khi đạt:

```text
BOOT-029
```

ta sẽ có một mốc cực lớn:

> **Axiom đã tự xây được chính compiler của nó.**

Lúc đó roadmap chuyển từ:

```text
"Xây compiler"
```

sang:

```text
"Hoàn thiện production language/toolchain"
```

và lúc đó mới đáng làm sâu:

```text
Standard Library
Build System
Package Manager
Debugger
Profiler
IDE/LSP
Cross Compilation
Windows backend
ARM64 backend
WASM
Dynamic Linking
PGO
SIMD
GPU
```

---

## Một điểm còn quan trọng hơn nữa

Sau bootstrap, bước tiếp theo tôi đề xuất **không phải Standard Library ngay**, mà là **Axiom Build System + Package Manager v0.1**.

Bởi vì nếu đã đạt:

```text
Axiom compiler
+
Axiom linker
+
Axiom object writer
```

nhưng build một project nhiều module vẫn phải:

```text
gcc ...
ld ...
ar ...
```

thì toolchain vẫn chưa thực sự độc lập.

Mục tiêu kế tiếp sẽ là:

```text
axiom build
        ↓
Package resolution
        ↓
Module graph
        ↓
Incremental compilation
        ↓
Parallel compilation
        ↓
Cache
        ↓
Axiom object
        ↓
Axiom linker
        ↓
Native executable
```

và đặc biệt phải thiết kế sao cho **build system không trở thành một “Cargo/MSBuild/CMake khổng lồ”**. Nó nên tận dụng trực tiếp query system, package graph và semantic cache mà chúng ta đã thiết kế.