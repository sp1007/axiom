Tiếp tục với **BOOTSTRAP-059**. Đây là phần biến machine code thành **object, library và executable thực sự**. Sau 059, Axiom về mặt kiến trúc đã có gần đủ một native toolchain hoàn chỉnh.

# BOOTSTRAP-059 — Object Writer, Linker & Native Binary Architecture

## 1. Mục tiêu

Axiom không nên dừng ở:

```text
Axiom
  ↓
Machine Code
  ↓
.o / .obj
```

Mục tiêu cuối:

```text
.ax
 ↓
Compiler
 ↓
Machine Code
 ↓
Object
 ↓
Axiom Linker
 ↓
┌──────────────┬──────────────┬──────────────┐
│ ELF          │ PE/COFF      │ Mach-O       │
│ Linux        │ Windows      │ macOS/iOS    │
└──────────────┴──────────────┴──────────────┘
```

và:

```text
static library
shared library
executable
WASM module
```

đều là output native của Axiom.

---

# 2. Tách Object Writer và Linker

Không gộp hai thành phần.

```text
Machine Code
     ↓
ObjectWriter
     ↓
Object File
     ↓
Linker
     ↓
Executable / Shared Library
```

ObjectWriter biết:

```text
ELF
PE/COFF
Mach-O
WASM
```

Linker có semantic model riêng.

---

# 3. Object model nội bộ

Axiom nên có một object representation trung gian:

```text
ObjectFile {
    format
    architecture
    sections[]
    symbols[]
    relocations[]
    comdats[]
    debug_info
    tls_info
    metadata
}
```

Sau đó:

```text
ObjectFile
 ↓
ELFWriter
PEWriter
MachOWriter
WasmWriter
```

Điều này tránh việc codegen phải hiểu ELF/Mach-O/PE.

---

# 4. Sections

Object model cần hỗ trợ ít nhất:

```text
.text
.rodata
.data
.bss
.tdata
.tbss
.debug_*
```

và target-specific sections.

---

# 5. Section flags

Mỗi section có properties:

```text
ALLOC
EXEC
WRITE
READ_ONLY
TLS
MERGE
DISCARDABLE
DEBUG
```

Không nên dùng một enum quá đơn giản vì PE/ELF/Mach-O khác nhau.

---

# 6. Symbol

Symbol:

```text
Symbol {
    name
    binding
    visibility
    section
    offset
    size
    type
}
```

Ví dụ:

```text
main
foo
axiom_internal_7F31
```

---

# 7. `pub` không phải symbol export

Đã freeze từ trước:

```text
pub
```

là source-level visibility.

Còn:

```text
@export("foo")
```

là binary-level symbol contract.

Ví dụ:

```axiom
pub fn internal_api() {}

@export("my_api")
pub fn public_api() {}
```

Không nhất thiết cả hai đều trở thành external symbols.

---

# 8. Symbol binding

Linker cần phân biệt:

```text
LOCAL
GLOBAL
WEAK
```

và target-specific equivalents.

---

# 9. Name mangling

Axiom ABI có thể tạo:

```text
_ZN...
```

hoặc format riêng.

Nhưng:

```text
@export("foo")
```

phải cho phép tên external chính xác:

```text
foo
```

không bị mangling.

---

# 10. Relocation

Object code thường chưa biết địa chỉ cuối cùng.

Ví dụ:

```text
call foo
```

machine code chứa placeholder.

Object:

```text
.text
  instruction
  relocation → foo
```

Linker sau đó resolve.

---

# 11. Relocation model

Internal:

```text
LOCAL
GLOBAL
```

External:

```text
UNRESOLVED
IMPORT
```

có thể có:

```text
PC_RELATIVE
ABSOLUTE
GOT_RELATIVE
TLS
SECTION_RELATIVE
```

---

# 12. Target relocation không nên leak lên compiler

LIR không biết:

```text
R_X86_64_PC32
IMAGE_REL_AMD64_REL32
ARM64_BRANCH26
```

Machine/Object layer mới biết.

---

# 13. Static library

Axiom phải tạo được:

```text
libfoo.a
foo.lib
```

tùy platform.

Conceptually:

```text
Archive {
    members: ObjectFile[]
}
```

---

# 14. Archive symbol index

Static linker cần index:

```text
symbol → object member
```

để không phải load toàn bộ library.

---

# 15. Linker input

```text
main.ax
   ↓
main.o

libA
libB
system libs
   ↓
Axiom Linker
```

---

# 16. Link graph

Linker xây:

```text
Root symbols
     ↓
Referenced symbols
     ↓
Referenced sections
     ↓
Referenced objects
```

Những phần không reachable có thể loại bỏ.

---

# 17. Dead code elimination

Ví dụ library có:

```text
foo()
bar()
baz()
```

application chỉ gọi:

```text
foo()
```

linker không nhất thiết đưa:

```text
bar()
baz()
```

vào executable.

---

# 18. Section GC

Không chỉ function.

Các:

```text
constant
jump table
metadata
helper
```

cũng có thể dead-strip nếu không reachable.

---

# 19. COMDAT / LinkOnce

Generic monomorphization có thể tạo cùng một instance ở nhiều module:

```text
Vec<i32>::push
```

Compiler cần cho linker biết các bản sao là equivalent.

Dùng:

```text
COMDAT
linkonce
weak ODR-like
```

tùy target.

---

# 20. Generic deduplication

Pipeline:

```text
Module A → Vec<i32>
Module B → Vec<i32>
```

→

```text
one machine implementation
```

nếu semantic fingerprint tương đương.

---

# 21. Nhưng không deduplicate mù quáng

Phải xét:

```text
target features
ABI
visibility
debug configuration
representation
comptime result
```

Hai function cùng source không nhất thiết cùng machine implementation nếu target/config khác.

---

# 22. Linker symbol resolution

Ví dụ:

```text
A.o → foo
B.o → foo
```

nếu cả hai strong:

```text
duplicate definition
```

→ linker error.

Nếu:

```text
strong + weak
```

thì strong thắng theo target/link contract.

---

# 23. Undefined symbols

Nếu:

```text
main → foo
```

nhưng không có `foo`:

```text
undefined symbol: foo
```

Diagnostic phải machine-readable.

---

# 24. Symbol visibility

Nên hỗ trợ:

```text
hidden
internal
default/public
```

trên target có hỗ trợ.

Giúp:

- giảm dynamic symbol table
- tối ưu dynamic linking
- tăng dead stripping.

---

# 25. Executable layout

Linker tạo:

```text
Executable {
    headers
    text
    rodata
    data
    bss
    tls
    relocations
    dynamic metadata
    debug
}
```

---

# 26. Virtual address assignment

Linker quyết định:

```text
section VA
alignment
file offset
segment mapping
```

---

# 27. Segment vs section

ELF đặc biệt quan trọng:

```text
Sections → linker organization
Segments → loader organization
```

Không được nhầm hai khái niệm.

Executable cần `PT_LOAD`, dynamic segments, TLS segments... tùy trường hợp.

---

# 28. Memory permissions

Executable mapping phải giữ nguyên tắc:

```text
.text    RX
.rodata  R
.data    RW
.bss     RW
```

Không biến toàn bộ binary thành RWX.

---

# 29. PIE

Axiom nên hỗ trợ:

```text
PIE
non-PIE
```

nhưng đây là linker/target policy, không phải language semantic.

---

# 30. ASLR

PIE/shared library cho phép loader randomize base address.

Axiom compiler không cần biết địa chỉ runtime cuối cùng.

Relocations phải hỗ trợ mô hình đó.

---

# 31. Dynamic linking

Shared library:

```text
Linux: .so
Windows: .dll
macOS: .dylib
```

cần:

```text
imports
exports
relocations
loader metadata
```

---

# 32. ELF GOT/PLT

Đối với ELF dynamic linking:

```text
call external_function
```

có thể đi qua:

```text
PLT
 ↓
GOT
 ↓
dynamic loader
```

Linker chịu trách nhiệm tạo structures phù hợp.

---

# 33. Symbol interposition

Đây là một vấn đề quan trọng.

Nếu ELF cho phép symbol interposition, compiler không thể luôn giả định:

```text
foo() = exact local foo
```

Linker visibility và `-Bsymbolic`-like policies có thể ảnh hưởng.

Axiom cần có target policy rõ ràng.

---

# 34. Axiom mặc định có thể ưu tiên optimization

Trong native Axiom libraries:

```text
internal/private symbol
```

nên được local/hidden khi có thể.

Chỉ external API thực sự cần export mới public.

---

# 35. Windows PE/COFF

Axiom linker phải xử lý:

```text
PE header
COFF sections
imports
exports
relocations
TLS
unwind
entry point
```

---

# 36. Windows import

Ví dụ:

```text
Kernel32.dll
User32.dll
```

Executable cần import table.

Axiom FFI:

```axiom
extern "system" fn ...
```

có thể tạo dependency tương ứng.

---

# 37. Windows export

```axiom
@export("my_api")
pub fn my_api(...) {}
```

→ export table entry.

---

# 38. Windows calling convention

Axiom ABI layer phải phân biệt:

```text
Axiom ABI
C
system / Win64
vectorcall
```

nếu target hỗ trợ.

Machine backend + linker cùng dùng contract đó.

---

# 39. Mach-O

macOS/iOS cần:

```text
Mach-O header
load commands
segments
sections
symbols
rebasing
binding
exports
code signatures
```

Một số phần có thể cần platform SDK/tooling ở bước packaging/signing.

---

# 40. iOS

Không nên coi:

```text
iOS = chỉ một Mach-O executable
```

Packaging còn liên quan:

```text
app bundle
Info.plist
frameworks
entitlements
code signing
```

Axiom compiler/linker có thể tạo native Mach-O; **SDK/signing layer** là một tầng riêng.

---

# 41. Android

Tương tự:

```text
ELF
+
APK/AAB packaging
+
Android ABI
```

Compiler chịu native binary.

Packaging là build-system/platform layer.

---

# 42. WASM

WASM không nên ép vào mô hình native executable.

Backend tạo:

```text
WasmModule {
    types
    functions
    tables
    memories
    globals
    exports
    imports
    data
    elements
}
```

---

# 43. WASM relocation

Nếu build object-style WASM:

```text
relocatable wasm
```

có thể link sau.

Nếu final module:

```text
imports/exports
```

được resolve thành module hoàn chỉnh.

---

# 44. TLS

Axiom đã có:

```text
@tls
```

Object/linker cần hỗ trợ:

```text
ELF TLS
PE TLS
Mach-O TLS
```

target-specific.

---

# 45. Static TLS vs dynamic TLS

Compiler không cần quyết định bằng source semantics.

Linker/runtime target quyết định model phù hợp.

---

# 46. Startup

Hosted program:

```text
OS loader
 ↓
platform entry
 ↓
Axiom startup
 ↓
main()
```

Axiom có thể cung cấp startup object/runtime component.

Nhưng:

```text
freestanding
```

có thể:

```text
entry
 ↓
user function
```

không cần CRT.

---

# 47. Không phụ thuộc libc

Một mục tiêu quan trọng của Axiom:

```text
fn main() { ... }
```

không bắt buộc:

```text
libc
libstdc++
MSVC CRT
```

nếu chương trình không sử dụng chúng.

---

# 48. Nhưng OS API vẫn có thể được dùng

Ví dụ Linux:

```text
syscall
```

Windows:

```text
Win32 API
```

macOS:

```text
system framework
```

đây là FFI/System layer, không phải compiler dependency.

---

# 49. Runtime components

Nếu chương trình dùng:

```text
Arc
threads
async
panic unwind
Unicode
```

linker có thể đưa component tương ứng.

Không dùng thì không link.

---

# 50. Runtime component graph

Ví dụ:

```text
Application
 ├── allocator
 ├── thread runtime
 └── async executor
```

hoặc:

```text
Freestanding
 └── nothing
```

---

# 51. Runtime static linking

Có thể:

```text
libaxiom_rt.a
```

nhưng linker chỉ lấy object cần thiết.

Kết quả:

```text
dead runtime code
```

bị loại bỏ.

---

# 52. Shared runtime

Có thể hỗ trợ:

```text
axiom_rt.dll
libaxiom_rt.so
libaxiom_rt.dylib
```

nhưng không bắt buộc.

---

# 53. Dynamic runtime versioning

Nếu dùng shared runtime, cần ABI version:

```text
runtime ABI version
component ABI
compiler compatibility
```

Đây là package/toolchain concern.

---

# 54. Reproducible linking

Cùng:

```text
source
dependencies
compiler
target
config
link inputs
```

phải tạo binary deterministic nếu reproducible mode được bật.

---

# 55. Build ID

Executable có thể chứa:

```text
build-id
```

phục vụ:

```text
debug symbol lookup
crash reports
artifact identification
```

nhưng build ID phải không phá reproducibility nếu deterministic mode.

---

# 56. Debug sections

Debug info nên có thể:

```text
embedded
separate file
stripped
```

Ví dụ Linux:

```text
program
program.debug
```

---

# 57. Strip

Release build có thể:

```text
remove debug
remove local symbols
remove unused sections
```

mà không thay đổi semantics.

---

# 58. Linker garbage collection

Đề xuất:

```text
--gc-sections
```

hoặc mặc định trong release nếu an toàn.

Nhưng external exports và linker-retained sections phải được giữ.

---

# 59. Linker script

Không nên đưa một linker scripting language phức tạp vào Core.

Thay vào đó:

```text
system/build layer
```

có target-specific linker configuration.

---

# 60. Custom sections

System programming đôi khi cần:

```text
@section(".init_array")
```

hoặc tương đương.

Đây là system/ABI attribute, không phải ordinary application feature.

---

# 61. Linker-defined symbols

Ví dụ:

```text
__start
__end
```

hoặc linker symbols.

Axiom system layer cần cách khai báo chúng an toàn ở FFI/system boundary.

---

# 62. Link order

Static library resolution có thể phụ thuộc thứ tự ở một số toolchains.

Axiom linker nên xây dependency graph thay vì phụ thuộc vào thứ tự càng nhiều càng tốt.

---

# 63. Circular static dependencies

Ví dụ:

```text
libA → libB
libB → libA
```

Axiom linker có thể xử lý bằng graph resolution/archive rescanning thay vì yêu cầu người dùng lặp library thủ công.

---

# 64. Link-time generic metadata

Axiom object có thể chứa compiler metadata:

```text
type fingerprints
generic instances
inline bodies
trait information
optimization summaries
```

nhưng phải phân biệt:

```text
runtime binary data
compiler metadata
```

Compiler metadata có thể bị strip khỏi final executable.

---

# 65. Incremental linking

Linker có thể cache:

```text
object → layout contribution
symbol resolution
relocation
```

nhưng correctness phải dựa trên fingerprint, không timestamp đơn thuần.

---

# 66. Link cache identity

Nên bao gồm:

```text
object content hash
target
link configuration
linker semantic version
system libraries
```

---

# 67. LTO boundary

Có hai kiểu:

```text
semantic LTO
machine LTO
```

Axiom nên ưu tiên:

```text
Typed/semantic metadata
 ↓
OptIR
 ↓
whole-program optimization
 ↓
Machine
```

khi compiler có đủ information.

---

# 68. Nhưng linker không nên trở thành compiler thứ hai

Kiến trúc:

```text
Compiler
  semantic optimization
  ↓
LIR/Machine IR

Linker
  symbol/layout/relocation
```

Linker không được tự phân tích ownership/type semantics.

---

# 69. Thin LTO

Sau này có thể hỗ trợ summary:

```text
FunctionSummary {
    size
    hotness
    calls
    attributes
    effects
}
```

để quyết định cross-module optimization mà không load toàn bộ IR.

---

# 70. PGO

PGO information có thể truyền:

```text
function hotness
branch probability
call frequency
```

đến optimizer.

Linker có thể dùng để layout functions.

---

# 71. Hot/cold section

Compiler có thể tạo:

```text
.text.hot
.text.unlikely
```

hoặc target equivalent.

Linker gom chúng hợp lý.

---

# 72. Security hardening

Build system có thể bật:

```text
PIE
RELRO
NX
stack protector
CF protection
```

tùy target.

Đây là target/security policy, không thay đổi language semantics.

---

# 73. Stack protector

Nếu compiler cần:

```text
stack canary
```

đây là compiler security instrumentation.

Không phải mặc định bắt buộc.

---

# 74. CFI

Control Flow Integrity có thể là optional instrumentation.

Không nên đưa CFI runtime vào mọi binary.

---

# 75. Binary size

Axiom có lợi thế từ:

```text
no mandatory runtime
dead stripping
generic deduplication
LTO
section GC
small startup
no object headers
```

nhưng không nên hứa:

> “Axiom binary luôn nhỏ hơn C.”

Mục tiêu đúng là:

> **Không có overhead kiến trúc bắt buộc chỉ vì sử dụng abstraction của Axiom.**

---

# 76. Linker architecture

Tôi đề xuất:

```text
                 Axiom Linker
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Input Reader   Symbol Engine   Layout Engine
        │             │             │
        └─────────────┼─────────────┘
                      ▼
               Relocation Engine
                      │
                      ▼
               Binary Writer
```

---

# 77. Input Reader

Đọc:

```text
Axiom Object
ELF
COFF
Mach-O
WASM
Archive
```

Axiom object format có thể được native.

Foreign object support cần thiết để interoperability.

---

# 78. Symbol Engine

Xử lý:

```text
definition
reference
weak
visibility
export
import
COMDAT
```

---

# 79. Layout Engine

Tính:

```text
section placement
alignment
segment placement
VA
file offset
```

---

# 80. Relocation Engine

Resolve:

```text
symbol address
PC-relative displacement
absolute address
GOT/PLT
TLS
target relocation
```

---

# 81. Binary Writer

Cuối cùng:

```text
ELFWriter
PEWriter
MachOWriter
WasmWriter
```

---

# 82. Foreign linker compatibility

Trong bootstrap, Axiom có thể:

```text
Axiom Object
 ↓
system linker
```

nhưng production path hướng tới:

```text
Axiom Object
 ↓
Axiom Linker
```

---

# 83. LLVM/LLD không phải semantic dependency

Có thể bootstrap bằng:

```text
LLVM
LLD
system linker
```

nhưng chúng không xuất hiện trong:

```text
Axiom language specification
```

và không cần có mặt trong final native compiler.

---

# 84. Native toolchain hoàn chỉnh

Sau 059:

```text
             AXIOM COMPILER
                   │
                   ▼
              Verified MIR
                   │
                   ▼
                 OptIR
                   │
                   ▼
                ABI MIR
                   │
                   ▼
                Axiom LIR
                   │
                   ▼
              Machine IR
                   │
                   ▼
             Machine Code
                   │
                   ▼
             Object Writer
                   │
                   ▼
             Axiom Object
                   │
                   ▼
              Axiom Linker
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
         ELF      PE       Mach-O
          │        │        │
        Linux    Windows   macOS/iOS
```

Đây là **native compilation path hoàn chỉnh**, không còn khoảng trống kiến trúc lớn giữa compiler và executable.

---

# 85. Frozen invariants — BOOTSTRAP-059

```text
ALINK-20   Object representation is distinct from machine IR.
ALINK-21   Object writing is distinct from linking.
ALINK-22   Object files contain sections, symbols and relocations as required by the target.
ALINK-23   Relocations are explicit linker inputs.
ALINK-24   Target relocation formats do not leak into semantic IR.
ALINK-25   Symbol identity is distinct from source visibility.
ALINK-26   @export establishes an external symbol contract.
ALINK-27   Internal symbols may be mangled.
ALINK-28   Strong duplicate symbol definitions are link errors unless a target contract permits otherwise.
ALINK-29   Weak/linkonce/COMDAT semantics are target-aware.
ALINK-30   Generic instantiations may be deduplicated when their semantic and target contracts are equivalent.
ALINK-31   Deduplication cannot violate ABI or representation contracts.
ALINK-32   Static libraries are first-class link inputs.
ALINK-33   Static archives may provide symbol indexes.
ALINK-34   Link resolution follows symbol reachability.
ALINK-35   Unreachable sections may be removed.
ALINK-36   Dead stripping preserves externally reachable symbols.
ALINK-37   Section garbage collection is permitted.
ALINK-38   Linker layout is target-specific.
ALINK-39   Sections and loadable segments are distinct concepts.
ALINK-40   Executable memory permissions must follow target security contracts.
ALINK-41   Code and read-only data need not be writable.
ALINK-42   Writable data need not be executable.
ALINK-43   PIE is a linker/target policy, not a language semantic.
ALINK-44   ASLR compatibility is provided through target-appropriate binary layout.
ALINK-45   Shared libraries are first-class artifacts.
ALINK-46   Dynamic imports and exports are explicit binary contracts.
ALINK-47   ELF GOT/PLT mechanisms remain target-specific.
ALINK-48   PE import/export mechanisms remain target-specific.
ALINK-49   Mach-O rebasing/binding/export mechanisms remain target-specific.
ALINK-50   TLS layout is target-specific.
ALINK-51   TLS semantics originate from the Axiom storage model.
ALINK-52   Freestanding executables need not depend on a C runtime.
ALINK-53   Hosted startup is distinct from language semantics.
ALINK-54   Startup code is target-specific.
ALINK-55   Runtime components are independently linkable.
ALINK-56   Unused runtime components need not enter the final binary.
ALINK-57   Runtime presence is determined by reachable program requirements.
ALINK-58   Runtime-free programs remain valid Axiom programs.
ALINK-59   Foreign libraries may be linked through explicit FFI contracts.
ALINK-60   FFI does not implicitly change ownership semantics.
ALINK-61   FFI allocation domains remain explicit.
ALINK-62   Foreign object formats may be accepted for interoperability.
ALINK-63   Axiom-native objects are independent of any external compiler's semantic IR.
ALINK-64   Debug information is separable from executable semantics.
ALINK-65   Debug sections may be stripped without changing program semantics.
ALINK-66   Unwind information is emitted only when required by the selected profile.
ALINK-67   Freestanding abort-only programs need not contain unwind infrastructure.
ALINK-68   Link-time metadata is distinct from runtime metadata.
ALINK-69   Compiler metadata may be removed from final binaries when not required.
ALINK-70   Link caching uses content/semantic identity rather than timestamps alone.
ALINK-71   Reproducible linking is deterministic for fixed inputs and configuration.
ALINK-72   Linker diagnostics are structured and machine-readable.
ALINK-73   Linker does not reinterpret Axiom ownership semantics.
ALINK-74   Linker does not reinterpret Axiom capability semantics.
ALINK-75   Linker preserves ABI contracts.
ALINK-76   Linker preserves representation contracts.
ALINK-77   Linker preserves relocation semantics.
ALINK-78   Linker preserves TLS contracts.
ALINK-79   Linker preserves exported/imported symbol contracts.
ALINK-80   Linker may perform layout optimization without changing observable semantics.
ALINK-81   PGO may influence layout and optimization but cannot override correctness constraints.
ALINK-82   Hot/cold code separation is an optimization strategy.
ALINK-83   Function ordering is an optimization strategy.
ALINK-84   LTO metadata does not redefine language semantics.
ALINK-85   Linker is not a second semantic compiler.
ALINK-86   ELF, PE/COFF, Mach-O and WASM remain distinct binary formats.
ALINK-87   Axiom can eventually write its supported native object formats directly.
ALINK-88   Axiom can eventually link supported native targets without LLVM/LLD.
ALINK-89   External linkers may be used during bootstrap.
ALINK-90   External linkers are not required language dependencies.
ALINK-91   Static libraries are independently consumable artifacts.
ALINK-92   Shared libraries have explicit ABI/version contracts.
ALINK-93   Executables have explicit entry-point contracts.
ALINK-94   Packaging is distinct from compilation and linking.
ALINK-95   Platform SDK/signing/package systems remain outside the language semantic core.
ALINK-96   WASM linking uses WASM-native concepts rather than pretending WASM is ELF.
ALINK-97   Binary layout decisions are deterministic under fixed target/configuration.
ALINK-98   Security hardening options are explicit target/build policies.
ALINK-99   Binary-size optimization cannot remove semantically reachable behavior.
ALINK-100  Native binary generation does not require a third-party compiler backend in the final architecture.
```

## Điểm cần chốt

Đến đây, kiến trúc Axiom đã có chuỗi:

**Ngôn ngữ → Type System → Ownership → Capability → Concurrency → Async/GPU → MIR → Verification → Optimization → ABI → Machine Code → Object → Linker → Native Binary.**

Điều quan trọng nhất là **không còn cần thêm một “runtime magic layer” để nối các tầng này lại**.

### Bước tiếp theo: **BOOTSTRAP-060 — Compiler Bootstrap, Self-Hosting & Axiom Compiler Architecture**

Đây sẽ là bước chuyển từ *thiết kế compiler* sang *thiết kế chính compiler `axiomc`*: cấu trúc source tree, compiler crates/modules, query engine, incremental compilation, diagnostic engine, cache, bootstrap compiler, stage-0 → stage-1 → stage-2, self-hosting, compiler build graph và kế hoạch triển khai thực tế từ prototype đầu tiên đến **Axiom compiler tự biên dịch chính nó**.