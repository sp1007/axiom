Tiếp tục với **ELF-002 — Dynamic ELF**. Đây là bước hoàn thiện Linux/AArch64/Android nền tảng, đồng thời kiểm tra abstraction linker của Axiom có thực sự đủ tổng quát hay chưa.

# ELF-002 — Dynamic Linking, PIE, GOT/PLT và Shared Objects

Mục tiêu:

```text
Axiom
 ↓
LIR
 ↓
Machine IR
 ↓
ELF Object
 ↓
Axiom ELF Linker
 ├── static executable
 ├── PIE executable
 ├── shared object
 └── dynamically linked executable
```

Không đưa kiến thức ELF vào frontend.

---

## 1. Tách ELF static và dynamic

Hiện tại:

```text
Object
 ↓
ELF Linker
 ↓
Executable
```

mở rộng thành:

```text
ELF Linker
 ├── StaticLink
 │    └── ET_EXEC / freestanding
 │
 ├── PieLink
 │    └── ET_DYN executable
 │
 ├── SharedLink
 │    └── ET_DYN shared object
 │
 └── DynamicLink
      └── executable + external libraries
```

Đây là **link mode**, không phải language mode.

---

# 2. ELF semantic model

Tạo:

```text
compiler/object/elf/
├── header.ax
├── program.ax
├── section.ax
├── symbol.ax
├── relocation.ax
├── dynamic.ax
├── version.ax
├── tls.ax
├── hash.ax
├── gnu_hash.ax
├── writer.ax
├── reader.ax
├── verifier.ax
└── tests/
```

Linker:

```text
compiler/linker/elf/
├── graph.ax
├── symbols.ax
├── sections.ax
├── layout.ax
├── reloc.ax
├── dynamic.ax
├── got.ax
├── plt.ax
├── tls.ax
├── pie.ax
├── shared.ax
├── version.ax
├── entry.ax
├── debug.ax
├── unwind.ax
├── builder.ax
├── writer.ax
├── verifier.ax
└── tests/
```

---

# 3. Symbol visibility

ELF có nhiều hơn mô hình symbol đơn giản.

Generic linker nên có:

```text
SymbolBinding {
    Local
    Global
    Weak
}
```

và:

```text
SymbolVisibility {
    Default
    Hidden
    Protected
}
```

Không cho ELF details lọt vào semantic symbol.

---

# 4. Dynamic symbol table

Static symbol:

```text
.symtab
```

dynamic symbol:

```text
.dynsym
```

Phải phân biệt:

```text
StaticSymbolTable
DynamicSymbolTable
```

Không dùng một vector symbol rồi "lọc lúc writer".

Dynamic symbols có ABI/runtime semantics riêng.

---

# 5. `DT_NEEDED`

Shared library dependency:

```text
DT_NEEDED
```

semantic:

```text
DynamicDependency {
    library_name
}
```

Ví dụ:

```text
libc.so.6
libm.so.6
```

Nhưng compiler không tự đoán dependency từ function name.

Platform/package metadata quyết định.

---

# 6. GOT

Đây là abstraction quan trọng.

Không để Machine IR có:

```text
GOT_ENTRY
```

thay vào đó generic linker IR:

```text
DynamicAddressSlot {
    symbol
    binding_kind
}
```

ELF mapping:

```text
DynamicAddressSlot
        ↓
GOT
```

Mach-O mapping có thể dùng cơ chế tương ứng của dyld.

PE:

```text
DynamicAddressSlot
        ↓
IAT
```

Như vậy linker architecture thực sự dùng chung được.

---

# 7. PLT

Tương tự:

```text
DynamicCall {
    symbol
}
```

ELF linker có thể lower:

```text
DynamicCall
 ↓
PLT entry
 ↓
GOT slot
 ↓
dynamic linker
```

Không cho compiler frontend biết PLT tồn tại.

---

# 8. Direct vs indirect foreign call

Ví dụ:

```text
extern "C"
fn foo(x: i32) -> i32
```

Nếu `foo` được link statically:

```text
CALL foo
```

Nếu dynamic:

```text
CALL foo@PLT
```

hoặc target-specific equivalent.

Semantic call không đổi.

Đây là một invariant rất quan trọng:

> **Dynamic linking strategy không thay đổi source-level call semantics.**

---

# 9. GOT/PLT lazy binding

MVP có thể hỗ trợ:

```text
eager binding
```

trước.

Sau đó:

```text
lazy binding
```

Lazy binding không cần trở thành language feature.

Nó là linker/runtime policy:

```text
LinkMode {
    Static
    Dynamic
    Pie
}
```

và:

```text
BindingPolicy {
    Eager
    Lazy
}
```

---

# 10. PIE

PIE:

```text
Position Independent Executable
```

semantic linker mode:

```text
LinkMode::PIE
```

Executable:

```text
ELF Type = ET_DYN
```

nhưng có executable entry.

Không nên tạo:

```text
@pie
```

trong language.

---

# 11. Position independence

Axiom backend phải có target-neutral concept:

```text
AddressModel {
    Absolute
    PositionIndependent
}
```

LIR:

```text
ADDRESS_OF_GLOBAL symbol
```

Target lowering quyết định:

```text
x86-64:
    RIP-relative

AArch64:
    ADRP + ADD/LDR
```

Ví dụ AArch64:

```asm
adrp x0, symbol@PAGE
add  x0, x0, symbol@PAGEOFF
```

ELF linker giải relocation.

---

# 12. x86-64 PIE

Ví dụ:

```text
ADDRESS_OF_GLOBAL foo
```

có thể thành:

```asm
lea rax, [rip + foo]
```

Không hard-code trong ELF linker.

Đó là responsibility của x86-64 target lowering.

---

# 13. Relocation model

Generic:

```text
Relocation {
    place
    symbol
    addend
    kind
}
```

ELF mapping:

```text
R_X86_64_PC32
R_X86_64_PLT32
R_X86_64_64
R_X86_64_GOTPCREL
...
```

AArch64:

```text
R_AARCH64_CALL26
R_AARCH64_ADR_PREL_PG_HI21
R_AARCH64_ADD_ABS_LO12_NC
...
```

Relocation kind phải được target-specific.

---

# 14. REL vs RELA

ELF hỗ trợ:

```text
Elf64_Rel
Elf64_Rela
```

Axiom internal representation nên dùng:

```text
Relocation {
    offset
    symbol
    type
    addend: Optional<i64>
}
```

Writer quyết định:

```text
REL
```

hay:

```text
RELA
```

theo target/platform.

Không để code generator biết.

---

# 15. Dynamic relocation

Static relocation:

```text
link-time
```

Dynamic relocation:

```text
runtime loader
```

Ví dụ:

```text
R_X86_64_RELATIVE
R_X86_64_GLOB_DAT
R_X86_64_JUMP_SLOT
```

Semantic:

```text
DynamicRelocation {
    location
    symbol
    kind
}
```

Dynamic linker encoder chuyển thành ELF `.rela.dyn` / `.rela.plt`.

---

# 16. Rebase tương ứng

Mach-O:

```text
REBASE
```

ELF:

```text
R_*_RELATIVE
```

PE:

```text
base relocation
```

Đây củng cố abstraction đã tạo:

```text
ImageFixup {
    location
    target
    kind
}
```

Format-specific writer encode thành format tương ứng.

---

# 17. Export

ELF shared library:

```text
.dynsym
```

chứa exported symbols.

Generic:

```text
ExportSymbol {
    symbol
    visibility
}
```

ELF:

```text
GLOBAL + DEFAULT
```

hoặc visibility tương ứng.

---

# 18. Hidden symbol

Axiom có thể hỗ trợ:

```text
@visibility(hidden)
```

sau này.

Nhưng MVP có thể dùng compiler-internal linkage policies:

```text
Internal
Public
Exported
```

Mapping:

```text
Internal → STB_LOCAL
Public internal → not necessarily dynsym
Exported → dynamic symbol
```

Đừng đồng nhất `pub` với ELF export.

---

# 19. Symbol versioning

Đây là một vấn đề đặc biệt của Linux.

Ví dụ conceptual:

```text
foo@LIB_1.0
foo@@LIB_2.0
```

Axiom Core không cần syntax cho việc này.

Đưa vào platform linker metadata:

```text
SymbolVersion {
    name
    version
    default
}
```

Sau này package/FFI layer có thể dùng.

---

# 20. Hash tables

Dynamic loader cần symbol lookup.

MVP:

```text
DT_HASH
```

sau đó:

```text
DT_GNU_HASH
```

Kiến trúc:

```text
DynamicSymbolIndex
 ↓
HashStrategy
 ├── SysVHash
 └── GnuHash
```

Không để symbol resolver phụ thuộc hash implementation.

---

# 21. TLS

Đây là phần quan trọng vì Axiom đã có TLS semantic.

Source:

```axiom
static thread_local COUNTER: i32
```

semantic:

```text
StorageClass::TLS
```

ELF lowering có thể sử dụng TLS models:

```text
Local Exec
Initial Exec
Local Dynamic
General Dynamic
```

MVP:

```text
General Dynamic
```

hoặc target-appropriate subset.

Không expose bốn TLS model này cho programmer trong Core.

---

# 22. TLS invariant

```text
ATLS-20
TLS identity is per-thread.

ATLS-21
TLS storage has thread lifetime.

ATLS-22
TLS model is target/linker controlled.

ATLS-23
TLS access does not imply heap allocation.

ATLS-24
TLS representation is ABI-specific.

ATLS-25
TLS relocation is resolved according to target ABI.
```

---

# 23. Shared object

Command conceptual:

```text
axiom build foo.ax \
    --crate-type shared
```

Output:

```text
libfoo.so
```

Nhưng tốt hơn:

```text
axiom build foo.ax --artifact shared
```

vì `crate-type` là Rust-specific terminology.

Artifact model đã có:

```text
ArtifactKind {
    Executable
    StaticLibrary
    SharedLibrary
    Object
    Interface
}
```

---

# 24. Static library

Axiom cũng cần:

```text
libfoo.a
```

Đây không phải ELF executable.

Thực tế:

```text
Axiom Object
 ↓
Axiom archive writer
 ↓
libfoo.a
```

Nên tạo generic:

```text
object/archive/
```

thay vì nhét archive vào ELF linker.

Archive format Unix `ar` có thể là backend riêng.

---

# 25. Static archive model

```text
Archive {
    members[]
    symbol_index
}
```

Linker:

```text
foo.o
bar.o
libbaz.a
 ↓
Archive extraction
 ↓
Resolved object graph
```

MVP archive index có thể đơn giản, sau tối ưu.

---

# 26. Shared object dependency graph

Ví dụ:

```text
app
 ├── libfoo.so
 │    └── libc.so.6
 └── libbar.so
      └── libc.so.6
```

Linker chỉ cần tạo:

```text
DynamicDependencyGraph
```

Runtime loader quyết định load order thực tế.

Compiler không mô phỏng dynamic loader.

---

# 27. `-fPIC` equivalent

Không đưa compiler flag kiểu GCC vào semantics.

Axiom:

```text
CodeModel {
    Static
    PositionIndependent
}
```

Build profile:

```text
PIC = true
```

Shared library mặc định PIC.

PIE executable cũng PIC.

---

# 28. Code model

Sau này có:

```text
CodeModel {
    Small
    Large
    Kernel
    PositionIndependent
}
```

MVP chỉ cần:

```text
Default
PIC
```

Target lowering mới quyết định instruction sequences.

---

# 29. ELF entry

Giống Windows/Mach-O:

```text
main
```

không phải raw kernel entry.

Hosted Linux:

```text
kernel
 ↓
_start
 ↓
Axiom startup
 ↓
main
 ↓
exit
```

Axiom-generated startup:

```text
_start
```

sử dụng SysV ABI/system process startup contract.

---

# 30. Không cần libc cho runtime tối thiểu

Axiom phải hỗ trợ:

```text
@freestanding
```

hoặc profile tương đương:

```text
kernel
 ↓
_start
 ↓
Axiom code
```

không cần:

```text
libc
libstdc++
libgcc
```

để compiler tạo executable.

Hosted profile có thể dùng:

```text
libc
```

nhưng đó là platform library dependency.

---

# 31. `libgcc` cũng không nên là compiler dependency

Đây là điểm quan trọng với mục tiêu ban đầu của Axiom.

Nếu compiler phát sinh:

```text
__divdi3
__udivdi3
__muloti4
```

rồi yêu cầu GCC runtime, thì:

> Axiom vẫn chưa độc lập toolchain.

Do đó compiler cần intrinsic lowering hoặc compiler runtime của chính Axiom:

```text
runtime/compiler/
├── integer.ax
├── float.ax
├── div.ax
├── overflow.ax
└── ...
```

Nhưng chỉ link các routine cần thiết.

---

# 32. Runtime library vẫn optional

Ví dụ:

```text
i64 division
```

trên target không có instruction phù hợp có thể cần helper.

Compiler có thể:

```text
inline
```

hoặc:

```text
call __axiom_i64_div
```

Runtime linker chỉ đưa helper đó vào nếu cần.

Không có:

```text
monolithic libaxiom-runtime.so
```

bắt buộc.

---

# 33. ELF unwind

Dùng generic unwind model:

```text
Unwind IR
 ↓
DWARF CFI
 ↓
.eh_frame
```

Nếu panic profile:

```text
abort
```

vẫn có thể emit unwind/debug metadata cho debugger.

---

# 34. Debug

Pipeline:

```text
Debug IR
 ↓
DWARF
 ↓
ELF sections
```

MVP sections:

```text
.debug_info
.debug_abbrev
.debug_line
.debug_str
```

sau đó:

```text
.debug_loclists
.debug_rnglists
.debug_frame
```

Không đưa DWARF structures vào semantic Debug IR.

---

# 35. Acceptance: static executable

```axiom
fn main() -> i32 {
    42
}
```

Build:

```text
axiom build hello.ax --target x86_64-linux --static
```

Expected:

```text
ELF64
ET_EXEC
entry = _start
exit = 42
```

Không cần GCC/Clang/LLD.

---

# 36. Acceptance: PIE

```text
axiom build hello.ax \
    --target x86_64-linux \
    --pie
```

Expected:

```text
ELF64
ET_DYN
position independent
valid entry
exit = 42
```

---

# 37. Acceptance: shared library

```axiom
@export("add")
extern "C"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Output:

```text
libadd.so
```

Kiểm tra:

```text
.dynsym
exported add
```

---

# 38. Acceptance: dynamic executable

Conceptual:

```axiom
extern "C"
fn puts(s: *const u8) -> i32
```

Link:

```text
hello
 ↓
puts
 ↓
libc
```

Expected:

```text
ELF
DT_NEEDED
.dynsym
.plt
.got
dynamic relocations
```

---

# 39. Acceptance: cross-object

```text
main.ax
foo.ax
```

```text
foo:
    add(20, 22)

main:
    foo()
```

Build:

```text
main.o
foo.o
 ↓
Axiom ELF linker
 ↓
app
```

Không external linker.

---

# 40. Acceptance: no libc

```text
_start
 ↓
syscall
 ↓
exit
```

để chứng minh:

```text
Axiom compiler
```

không phụ thuộc libc.

Syscall wrapper là `unsafe` platform library.

---

# 41. ELF invariants

```text
AELF-20
ELF format handling is independent of source semantics.

AELF-21
Static and dynamic linking share the same symbol resolution model.

AELF-22
Dynamic symbols are distinct from static symbols.

AELF-23
GOT is a linker/runtime mechanism, not a source-level concept.

AELF-24
PLT is a linker/runtime mechanism, not a source-level concept.

AELF-25
Dynamic dependencies are explicit linker metadata.

AELF-26
PIE is a link mode, not a language feature.

AELF-27
Position independence is a target/code-generation property.

AELF-28
Relocations remain symbolic until their required resolution phase.

AELF-29
Dynamic relocations are distinct from static relocations.

AELF-30
REL/RELA representation is format-specific.

AELF-31
TLS semantic identity is independent of ELF TLS model.

AELF-32
ELF symbol versioning is platform/linker metadata.

AELF-33
Dynamic loader addresses are not compile-time constants.

AELF-34
Shared libraries do not require a language-level shared-object type.

AELF-35
Static archives are distinct from ELF executable images.

AELF-36
ELF linking does not require an external linker.

AELF-37
Compiler runtime helpers are linked only when required.

AELF-38
Hosted execution may depend on platform libraries without compiler dependence on them.

AELF-39
Freestanding execution need not depend on libc.

AELF-40
ELF debug data is generated from Debug IR.

AELF-41
ELF unwind data is generated from generic Unwind IR.

AELF-42
ELF layout uses distinct file and virtual address domains.

AELF-43
ELF builds are deterministic under reproducible-build mode.

AELF-44
Dynamic linking does not alter source-level function semantics.

AELF-45
The linker never invents ownership semantics for foreign symbols.
```

---

# 42. Kiến trúc linker hiện tại đã đạt mức khá hoàn chỉnh

Ta có:

```text
                    Generic Linker
                         │
       ┌─────────────────┼──────────────────┐
       ↓                 ↓                  ↓
      PE                ELF               Mach-O
       │                 │                  │
      IAT              GOT/PLT          dyld binding
      PE reloc         ELF reloc        Mach reloc
      PDB              DWARF            DWARF
```

Và phía ISA:

```text
             Target-independent LIR
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       x86-64        AArch64      RISC-V
          │            │            │
       Windows       Linux       Linux
       Linux         Android     Android
                     macOS
                     iOS
```

Đây là điểm mà Axiom bắt đầu có một backend architecture thực sự có khả năng mở rộng.

---

# 43. Bước tiếp theo

Tiếp theo tôi sẽ chuyển sang **Android-AArch64-001**:

```text
AArch64
   ↓
AAPCS64
   ↓
ELF64
   ↓
Android/Bionic ABI
   ↓
.so
   ↓
JNI/NDK boundary
   ↓
APK/AAB native artifact
```

Nhưng **không đưa Android vào Core**.

Ta sẽ đặc biệt xử lý:

- Bionic thay vì giả định glibc;
- Android ELF dynamic linking;
- API level;
- `libc.so`, `libdl.so`, `liblog.so`;
- JNI ABI;
- Android TLS;
- Android-specific relocation constraints;
- NDK không phải compiler dependency;
- tạo `.so` trực tiếp;
- sau đó mới xây lớp packaging APK/AAB.

Điều này sẽ kiểm tra một điểm rất quan trọng của Axiom: **cùng AArch64 + ELF nhưng platform ABI khác Linux desktop**, mà frontend, type system, ownership và LIR vẫn không thay đổi.