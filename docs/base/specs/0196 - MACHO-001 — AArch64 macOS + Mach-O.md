Tiếp tục với **Mach-O-001**. Đây là milestone quan trọng vì nó kiểm tra khả năng tách **ISA / ABI / OS / object format** của Axiom.

# MACHO-001 — AArch64 macOS + Mach-O

Mục tiêu:

```text
AArch64 Machine IR
        ↓
Apple AArch64 ABI
        ↓
Mach-O Object
        ↓
Axiom Mach-O Linker
        ↓
macOS executable
```

Không thay đổi:

- frontend;
- type system;
- ownership;
- capability;
- MIR;
- LIR;
- register allocator;
- AArch64 instruction selector.

Chỉ thay:

```text
ABI
Object format
Linker
Startup/platform layer
```

---

## 1. Target descriptor

Thêm:

```text
targets/macos_aarch64/
├── target.ax
├── abi.ax
├── macho.ax
├── linker.ax
├── startup.ax
└── tests/
```

Target:

```text
Target {
    architecture: AArch64
    os: MacOS
    environment: Darwin
    object_format: MachO64
    endian: Little
    pointer_width: 64
}
```

Không hard-code:

```text
Apple Silicon
```

vào AArch64 backend.

AArch64 là ISA.

macOS là platform.

---

# 2. Phân tầng chính xác

```text
compiler/backend/aarch64/
    ← ISA

compiler/abi/aarch64/
    ← ABI

targets/macos_aarch64/
    ← macOS

compiler/object/macho/
    ← Mach-O format
```

Đặc biệt:

> **Mach-O không được đặt trong AArch64 backend.**

Sau này Intel macOS có thể dùng:

```text
x86_64 + macOS + Mach-O
```

mà không copy Mach-O implementation.

---

# 3. Mach-O object model

Tạo:

```text
compiler/object/macho/
├── header.ax
├── load_command.ax
├── segment.ax
├── section.ax
├── symbol.ax
├── relocation.ax
├── string_table.ax
├── dyld.ax
├── export.ax
├── bind.ax
├── rebase.ax
├── writer.ax
├── reader.ax
├── verifier.ax
└── tests/
```

Model:

```text
MachOFile {
    header
    load_commands[]
    segments[]
    sections[]
    symbols
    relocations
    linkedit
}
```

---

# 4. Mach-O header

Mach-O 64-bit sử dụng:

```text
MH_MAGIC_64
```

Target AArch64:

```text
CPU_TYPE_ARM64
```

Header cần semantic model:

```text
MachHeader {
    magic
    cpu_type
    cpu_subtype
    file_type
    ncmds
    sizeofcmds
    flags
}
```

Không để writer rải magic number khắp code.

---

# 5. File types

MVP cần:

```text
MH_OBJECT
MH_EXECUTE
```

Sau này:

```text
MH_DYLIB
MH_BUNDLE
MH_DYLINKER
```

Đây là object-format concern, không phải compiler semantic.

---

# 6. Load commands

Mach-O khác PE/ELF ở chỗ header đi kèm một danh sách **load commands**.

Model:

```text
LoadCommand {
    kind
    size
    payload
}
```

MVP cần:

```text
LC_SEGMENT_64
LC_SYMTAB
LC_DYSYMTAB
LC_MAIN
LC_LOAD_DYLINKER
LC_LOAD_DYLIB
LC_UUID
```

Một số command có thể thêm khi dynamic linking hoàn thiện.

---

# 7. Segment và section

Mach-O có:

```text
Segment
 ├── Section
 ├── vmaddr
 ├── vmsize
 ├── fileoff
 ├── filesize
 ├── maxprot
 ├── initprot
 └── flags
```

Semantic model:

```text
MachSegment {
    name
    virtual_address
    virtual_size
    file_offset
    file_size
    max_protection
    initial_protection
    sections[]
}
```

Section:

```text
MachSection {
    segment
    name
    address
    size
    file_offset
    alignment
    relocation_offset
    relocation_count
    flags
}
```

---

# 8. Không hard-code section layout

MVP có thể sinh:

```text
__TEXT,__text
__TEXT,__const
__DATA,__data
__DATA,__bss
```

nhưng implementation phải dựa trên semantic section:

```text
SectionKind {
    Code
    ReadOnlyData
    Data
    ZeroFill
    CString
    ...
}
```

Target layer quyết định:

```text
SectionKind::Code
→ __TEXT,__text
```

---

# 9. Mach-O relocation

Đây là phần cần tách khỏi AArch64 encoder.

Machine IR:

```text
CALL symbol
```

Encoder có thể tạo:

```text
MachORelocation {
    address
    type
    symbol
    pcrel
    length
    extern
}
```

Nhưng encoder không cần biết file offset cuối cùng.

Linker mới resolve.

---

# 10. AArch64 relocation

MVP cần những dạng phổ biến:

```text
ARM64_RELOC_BRANCH26
ARM64_RELOC_PAGE21
ARM64_RELOC_PAGEOFF12
ARM64_RELOC_UNSIGNED
```

Ví dụ:

```asm
bl _foo
```

có relocation:

```text
BRANCH26
```

Địa chỉ global:

```asm
adrp x0, _global@PAGE
add  x0, x0, _global@PAGEOFF
```

tương ứng:

```text
PAGE21
PAGEOFF12
```

Điểm quan trọng:

> AArch64 instruction encoder không được tự giải quyết symbol address.

---

# 11. Symbol model

Dùng generic symbol abstraction:

```text
LinkSymbol {
    name
    binding
    visibility
    section
    offset
    size
}
```

Mach-O mapping:

```text
Local
External
Undefined
Weak
PrivateExternal
```

Không để frontend biết `nlist_64`.

---

# 12. Name mangling

Axiom internal:

```text
_ZN...
```

không nên giả định.

Mach-O linker symbol có thể cần:

```text
_foo
```

cho C ABI.

Do đó:

```text
Axiom Symbol
      ↓
Linkage Symbol
      ↓
Mach-O Symbol
```

Cụ thể:

```axiom
extern "C"
@export("foo")
fn foo()
```

→ Mach-O symbol:

```text
_foo
```

Target object writer xử lý platform-specific symbol decoration.

---

# 13. `LC_MAIN`

macOS hiện đại có thể mô tả entry thông qua:

```text
LC_MAIN
```

thay vì phải đặt raw machine entry theo cách thủ công.

Semantic model:

```text
ExecutableEntry {
    symbol
}
```

Mach-O linker chuyển thành:

```text
LC_MAIN {
    entryoff
}
```

Điều này tương tự nguyên tắc Windows:

```text
main ≠ raw OS entry
```

---

# 14. Axiom startup trên macOS

Không export trực tiếp:

```text
main
```

làm OS entry.

Pipeline:

```text
dyld
 ↓
Axiom startup
 ↓
__axiom_main
 ↓
exit
```

Conceptual:

```text
@platform_entry
unsafe fn __axiom_start() -> never {
    let code = __axiom_main()
    exit(code as i32)
}
```

Nhưng macOS có runtime/process startup conventions riêng.

Vì vậy startup implementation phải nằm trong:

```text
targets/macos_aarch64/startup.ax
```

không nằm trong AArch64 backend.

---

# 15. Không phụ thuộc Xcode/clang để link

Mục tiêu Axiom vẫn giữ nguyên:

```text
axiom source
 ↓
Axiom compiler
 ↓
Axiom object writer
 ↓
Axiom Mach-O linker
 ↓
Mach-O executable
```

Không:

```text
clang
ld64
as
```

là dependency bắt buộc.

Tuy nhiên executable có thể sử dụng hệ thống macOS:

```text
dyld
libSystem
Foundation
Metal
...
```

Đây là **runtime/platform dependency của chương trình**, không phải compiler dependency.

---

# 16. Dynamic linking

Đây là nơi Mach-O khác đáng kể PE/ELF.

Cần model generic:

```text
DynamicLinkInfo {
    imports[]
    exports[]
    rebases[]
    binds[]
}
```

Mach-O implementation chuyển thành:

```text
__LINKEDIT
dyld info
```

và load commands liên quan.

---

# 17. Import symbol

Ví dụ:

```text
extern "C"
fn malloc(size: usize) -> *mut u8
```

semantic:

```text
ForeignSymbol {
    library
    name
}
```

Mach-O:

```text
LC_LOAD_DYLIB
```

và dynamic binding information.

Compiler không hard-code:

```text
libSystem.dylib
```

trong FFI semantic layer.

Platform library metadata mới nói:

```text
malloc → libSystem
```

---

# 18. Symbol binding

Cần tách ba khái niệm:

```text
Import declaration
Dynamic symbol
Runtime binding
```

Ví dụ:

```text
Axiom:
    malloc

Mach-O:
    undefined symbol _malloc

dyld:
    resolves _malloc
```

Compiler không biết địa chỉ cuối cùng.

---

# 19. GOT/IAT abstraction

Không nên gọi generic structure là:

```text
IAT
```

vì đó là PE terminology.

Tạo:

```text
DynamicAddressSlot
```

Platform mapping:

```text
Windows → IAT
ELF     → GOT/PLT
Mach-O  → dyld binding/stub mechanisms
```

Đây là một abstraction rất đáng thêm vào linker architecture.

---

# 20. Generic dynamic linker model

```text
compiler/linker/dynamic/
├── import.ax
├── export.ax
├── symbol.ax
├── relocation.ax
├── binding.ax
├── rebase.ax
└── tests/
```

Semantic operations:

```text
IMPORT
EXPORT
REBASE
BIND
LAZY_BIND
```

Format layer mới encode chúng.

---

# 21. Rebase

Một executable có absolute pointer:

```text
image_base + offset
```

có thể phải được dyld rebase.

Do đó linker cần:

```text
RebaseEntry {
    location
    kind
}
```

Mach-O writer chuyển thành rebase opcodes.

Không cho Machine IR biết `dyld rebase opcode`.

---

# 22. Export trie

Mach-O hiện đại có cơ chế export trie.

Đừng đưa trie vào symbol resolver.

Tách:

```text
ResolvedSymbolGraph
       ↓
ExportGraph
       ↓
MachOExportTrieEncoder
```

Như vậy ELF có thể dùng:

```text
.gnu.hash
.dynsym
...
```

mà không ảnh hưởng symbol resolution.

---

# 23. Code signing

Đây là điểm cần **không nhồi vào compiler core**.

macOS thực tế có code-signing requirements.

Kiến trúc:

```text
Mach-O executable
       ↓
CodeSign layer
       ↓
signed Mach-O
```

Tạo subsystem:

```text
compiler/platform/apple/
├── codesign/
├── entitlements/
├── provisioning/
└── tests/
```

Nhưng:

> Code signing không phải một phần của code generation semantics.

MVP có thể tạo unsigned executable cho development/toolchain tests; quy trình ký ứng dụng thực tế là platform deployment layer.

---

# 24. UUID

PDB của Windows có deterministic identity.

Mach-O cũng có:

```text
LC_UUID
```

Cần hỗ trợ reproducible mode:

```text
UUID = hash(build identity + relevant content)
```

không dùng random UUID trong deterministic build.

Nếu debug artifact thay đổi thì UUID phải phản ánh đúng debug/image identity theo policy.

---

# 25. Debug symbols

Kiến trúc hiện tại:

```text
Debug IR
 ↓
CodeView
 ↓
PDB
```

không áp dụng trực tiếp cho macOS.

Đây chính là lý do Debug IR đã được thiết kế độc lập.

Thêm:

```text
compiler/debug/dwarf/
├── abbrev.ax
├── info.ax
├── line.ax
├── frame.ax
├── ranges.ax
├── location.ax
└── writer.ax
```

Pipeline:

```text
Debug IR
   ↓
DWARF IR
   ↓
Mach-O __debug_* sections
```

Không sửa Debug IR.

---

# 26. Đây là lợi ích lớn của Debug IR

Windows:

```text
Debug IR
 ↓
CodeView
 ↓
PDB
```

macOS/Linux:

```text
Debug IR
 ↓
DWARF
 ↓
Mach-O / ELF
```

Axiom source/debug semantics chỉ cần định nghĩa **một lần**.

---

# 27. Unwind

AArch64 macOS cần unwind information.

Không nên hard-code unwind vào:

```text
AArch64 backend
```

vì AArch64 Linux cũng cần unwind nhưng format/runtime policy có thể khác.

Tạo:

```text
compiler/unwind/
├── model.ax
├── frame.ax
├── encoding.ax
└── tests/
```

Target format:

```text
Windows → PDATA/XDATA
ELF/Linux → .eh_frame / DWARF CFI
Mach-O → compact unwind / DWARF fallback
```

---

# 28. Unified unwind model

```text
UnwindInfo {
    function_range
    prologue
    epilogue
    saved_registers
    stack_adjustment
    frame_pointer
}
```

Sau đó:

```text
WindowsUnwindEncoder
ElfEhFrameEncoder
MachCompactUnwindEncoder
```

Đây là kiến trúc sạch hơn rất nhiều so với việc backend tự sinh từng format.

---

# 29. Panic strategy trên macOS

MVP:

```text
panic = abort
```

Do đó:

```text
Axiom panic
 ↓
platform abort
```

không cần exception runtime.

Sau này unwind:

```text
panic
 ↓
unwind personality
 ↓
cleanup
 ↓
termination/catch boundary
```

nhưng vẫn không đưa exception model vào Core.

---

# 30. Mach-O linker architecture

```text
compiler/linker/macho/
├── reader.ax
├── graph.ax
├── symbols.ax
├── sections.ax
├── layout.ax
├── reloc.ax
├── dynamic.ax
├── entry.ax
├── debug.ax
├── unwind.ax
├── builder.ax
├── writer.ax
├── verifier.ax
└── tests/
```

Pipeline:

```text
Mach-O Objects
      ↓
Read
      ↓
Object Graph
      ↓
Symbol Resolution
      ↓
Section Merge
      ↓
Dead Strip
      ↓
Layout
      ↓
Relocation
      ↓
Dynamic Binding
      ↓
Debug Contributions
      ↓
Unwind
      ↓
Entry
      ↓
Mach-O Builder
```

---

# 31. Không trộn linker và object writer

Giống COFF:

```text
Mach-O Object Writer
```

chỉ biết:

```text
MH_OBJECT
```

Còn:

```text
Mach-O Executable Linker
```

biết:

```text
MH_EXECUTE
dyld
entry
segments
rebases
binds
exports
```

Điều này rất quan trọng cho incremental linking sau này.

---

# 32. Mach-O linker layout

MVP conceptual:

```text
__TEXT
 ├── __text
 ├── __const
 └── startup/code metadata

__DATA
 ├── __data
 └── __bss

__LINKEDIT
 ├── symbol information
 ├── binding information
 ├── export information
 └── code signature later
```

Không hard-code file offsets.

Layout engine:

```text
SectionPlacement
SegmentPlacement
FileOffset
VMAddress
Alignment
```

---

# 33. Virtual address model

Mach-O cũng cần phân biệt:

```text
FileOffset
VMAddress
RelativeAddress
```

Không được dùng một `u64 address` chung.

Đề xuất generic:

```text
Address =
    FileOffset
    VirtualAddress
    RelativeOffset
    SectionOffset
```

Điều này sẽ làm linker ít bug hơn đáng kể.

---

# 34. Page alignment

Mach-O segment alignment phụ thuộc target/platform.

Do đó:

```text
PageSize
SegmentAlignment
SectionAlignment
```

phải là target configuration.

Không:

```text
const PAGE = 0x1000
```

rải trong linker.

---

# 35. Acceptance test đầu tiên

Source:

```axiom
fn main() -> i32 {
    42
}
```

Build:

```text
axiom build hello.ax \
    --target aarch64-macos
```

Expected:

```text
hello
```

Mach-O:

```text
CPU_TYPE_ARM64
MH_EXECUTE
LC_MAIN
__TEXT,__text
__DATA...
```

chạy:

```text
./hello
```

và:

```text
exit code = 42
```

---

# 36. Acceptance test thứ hai — function call

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}

fn main() -> i32 {
    add(20, 22) as i32
}
```

Phải kiểm chứng:

```text
Axiom
 ↓
MIR
 ↓
LIR
 ↓
AArch64 ISel
 ↓
AAPCS64
 ↓
Machine IR
 ↓
Mach-O
 ↓
macOS
```

ra:

```text
42
```

---

# 37. Acceptance test thứ ba — FFI

```axiom
extern "C"
fn puts(s: *const u8) -> i32
```

MVP có thể dùng wrapper/platform declaration thích hợp.

Mục tiêu:

```text
Axiom
 ↓
C ABI
 ↓
Mach-O undefined symbol
 ↓
dyld
 ↓
system library
```

Compiler không cần biết địa chỉ `puts`.

---

# 38. Acceptance test thứ tư — debug

```axiom
fn add(a: i32, b: i32) -> i32 {
    let c = a + b
    c
}

fn main() -> i32 {
    add(20, 22)
}
```

Build:

```text
-O0 -g
```

Expected:

```text
Debug IR
 ↓
DWARF
 ↓
Mach-O
```

Debugger có thể thấy:

```text
a
b
c
```

và source line mapping.

---

# 39. Acceptance test thứ năm — optimized debug

```text
-O2 -g
```

`c` có thể:

```text
optimized out
```

nhưng debugger không được hiển thị giá trị sai.

Invariant Debug IR trước đây vẫn giữ nguyên.

---

# 40. Mach-O invariants

```text
AMACHO-20
Mach-O encoding is independent of AArch64 semantic IR.

AMACHO-21
Mach-O object writer emits relocatable objects without final addresses.

AMACHO-22
Mach-O linker resolves symbols after object construction.

AMACHO-23
ISA backend does not depend on Mach-O structures.

AMACHO-24
Mach-O sections are semantic categories before final layout.

AMACHO-25
File offsets and virtual addresses are distinct.

AMACHO-26
Segment alignment is target-configurable.

AMACHO-27
Relocations remain symbolic until link time.

AMACHO-28
Dynamic imports are distinct from Axiom foreign declarations.

AMACHO-29
Dynamic loader addresses are not compiler-known constants.

AMACHO-30
Rebase information is generated by the linker.

AMACHO-31
Binding information is generated by the linker.

AMACHO-32
Export representation is independent of source symbol identity.

AMACHO-33
Mach-O debug information is generated from Debug IR.

AMACHO-34
Mach-O unwind information is generated from generic unwind data.

AMACHO-35
Code signing does not alter language semantics.

AMACHO-36
Mach-O builds are deterministic under reproducible-build mode.

AMACHO-37
Mach-O executable generation requires no external compiler or assembler.

AMACHO-38
Mach-O platform startup is separate from AArch64 instruction selection.

AMACHO-39
Mach-O dynamic linking is separate from FFI type semantics.

AMACHO-40
Mach-O verification is independent of frontend verification.
```

---

# 41. Sau Mach-O, Axiom có ba object ecosystem

```text
                  Axiom Machine IR
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
      PE/COFF           ELF             Mach-O
        │                │                │
     Windows           Linux          macOS/iOS
```

và:

```text
Debug IR
 ├── CodeView/PDB
 └── DWARF
```

Đây là dấu hiệu kiến trúc compiler đang thực sự độc lập với platform.

---

# 42. Bước tiếp theo: ELF-002 — Dynamic ELF

Sau Mach-O không nên lập tức làm iOS.

Ta cần quay lại ELF và hoàn thiện **dynamic linking**, vì ELF là nền tảng cho:

- Linux desktop;
- server;
- Android;
- nhiều embedded systems;
- RISC-V;
- AArch64.

Milestone tiếp theo:

```text
ELF-002
├── ELF dynamic symbol table
├── GOT
├── PLT
├── DT_NEEDED
├── dynamic relocations
├── TLS
├── PIE
├── shared objects
├── symbol versioning architecture
└── dynamic linker boundary
```

Sau đó mới:

```text
Android-AArch64
      ↓
Android ELF
      ↓
Bionic ABI
      ↓
APK/AAB/native library
```

và cuối cùng:

```text
iOS-AArch64
      ↓
Mach-O platform restrictions
      ↓
framework/dylib
      ↓
code signing
      ↓
app bundle
```

**Thứ tự này sẽ tránh việc Android/iOS-specific requirements làm ô nhiễm compiler core.**