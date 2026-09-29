# BOOTSTRAP-304 — NATIVE EXECUTABLE / SHARED IMAGE WRITER

## 304.1. Mục tiêu

Xây dựng tầng cuối biến:

```text
LinkedImage
    ↓
BOOTSTRAP-304
    ↓
Native Image
```

Các output chính:

```text
Windows  → PE/COFF EXE / DLL
Linux    → ELF ET_EXEC / ET_DYN
macOS    → Mach-O executable / dylib
iOS      → Mach-O executable / dylib/framework-compatible image
Android  → ELF executable / shared object
WASM     → final WebAssembly module
```

Điểm rất quan trọng:

> **304 không link lại.**

Symbol resolution, section GC, relocation resolution, address assignment... đã hoàn thành ở `BOOTSTRAP-303`.

304 chỉ chuyển `LinkedImage` thành **physical binary image** đúng format.

---

# 304.2. Kiến trúc

```text
                    LinkedImage
                         │
              ┌──────────┴──────────┐
              │                     │
        Image Policy          Target Metadata
              │                     │
              └──────────┬──────────┘
                         ↓
                Native Image Builder
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
        ELF            PE/COFF        Mach-O
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                  Binary Artifact
```

Core phải dùng:

```text
ImageWriter
```

và target-specific:

```text
ElfImageWriter
PeImageWriter
MachOImageWriter
WasmImageWriter
```

---

# 304.3. Output kinds

Định nghĩa rõ:

```text
Executable
SharedLibrary
RelocatableImage
DynamicModule
WasmModule
```

Ví dụ:

```text
Linux:
    Executable → ELF ET_EXEC / ET_DYN
    SharedLibrary → ELF ET_DYN

Windows:
    Executable → PE executable
    SharedLibrary → PE DLL

macOS:
    Executable → Mach-O MH_EXECUTE
    SharedLibrary → Mach-O MH_DYLIB
```

PIE có thể khiến Linux executable dùng `ET_DYN`; đây là **policy**, không được hard-code `Executable == ET_EXEC`.

---

# 304.4. Image IR

Không serialize trực tiếp từ `LinkedImage`.

Tạo:

```text
ImageLayout
```

gồm:

```text
ImageLayout {
    format
    architecture
    entry_point
    file_size
    memory_size

    sections[]
    segments[]
    imports[]
    exports[]

    relocation_metadata[]
    dynamic_metadata[]

    security_metadata
    debug_metadata
    unwind_metadata

    headers
}
```

Quy trình:

```text
LinkedImage
    ↓
ImageLayout
    ↓
Format serialization
    ↓
bytes
```

---

# 304.5. Physical layout

Mỗi segment:

```text
SegmentLayout {
    virtual_address
    file_offset
    file_size
    memory_size
    alignment
    permissions
    sections[]
}
```

Invariant:

```text
file_size <= memory_size
```

với:

```text
memory_size > file_size
```

cho phần zero-fill như:

```text
.bss
```

Không ghi `.bss` thành hàng triệu byte zero vào file.

---

# 304.6. File offset vs virtual address

Phải phân biệt tuyệt đối:

```text
FileOffset
VirtualAddress
RVA
VA
SectionOffset
```

Không cho phép dùng cùng một integer type.

Đề xuất type-level distinction:

```text
FileOffset
VirtualAddress
RelativeVirtualAddress
SectionOffset
```

Điều này tránh các bug linker cực khó phát hiện.

---

# 304.7. ELF image writer

Linux/Unix ELF writer phải hỗ trợ:

```text
ET_EXEC
ET_DYN
```

và architecture:

```text
x86-64
AArch64
RISC-V64
```

Header:

```text
Elf64_Ehdr
```

với:

```text
e_type
e_machine
e_entry
e_phoff
e_shoff
e_flags
e_ehsize
e_phentsize
e_phnum
e_shentsize
e_shnum
e_shstrndx
```

---

# 304.8. ELF program headers

Đây là điểm khác biệt quan trọng giữa object và executable.

Executable cần:

```text
PT_LOAD
PT_DYNAMIC
PT_INTERP
PT_TLS
PT_GNU_STACK
PT_GNU_RELRO
PT_NOTE
```

khi cần.

Ví dụ:

```text
R-X LOAD
RW- LOAD
```

và:

```text
PT_INTERP
    → dynamic loader
```

chỉ xuất hiện khi image cần dynamic loading.

---

# 304.9. ELF section vs segment

Không được coi:

```text
section == segment
```

Một segment có thể chứa:

```text
.text
.rodata
.eh_frame
```

hoặc các section tương thích khác.

Ngược lại section có thể không được load:

```text
.debug_info
.debug_line
```

Image builder phải thực hiện:

```text
Sections → Segments
```

theo policy.

---

# 304.10. ELF dynamic image

Nếu dynamic linking:

```text
.dynsym
.dynstr
.gnu.hash / .hash
.rela.dyn
.rela.plt
.dynamic
.got
.plt
```

phải được tạo từ metadata mà linker đã chuẩn bị.

304 không được tự tìm unresolved symbol.

---

# 304.11. ELF interpreter

Nếu cần dynamic loader:

```text
PT_INTERP
```

phải chứa interpreter path do target/platform policy cung cấp.

Ví dụ Linux có thể sử dụng loader phù hợp architecture.

Không hard-code trong generic ELF writer.

---

# 304.12. ELF entry point

304 chỉ làm:

```text
LinkedImage.entry_point
    ↓
ELF e_entry
```

Không được tìm `main` lại.

Nếu:

```text
entry = _start
```

thì `_start` đã được linker resolve.

---

# 304.13. ELF RELRO / GNU stack

Security metadata phải được biểu diễn ở `LinkedImage`.

Ví dụ:

```text
GNU_RELRO
GNU_STACK
```

Policy mặc định nên hướng tới:

```text
non-executable stack
```

trừ khi target/runtime contract yêu cầu khác.

Writer chỉ serialize policy, không tự phát minh policy mới.

---

# 304.14. PE image writer

Windows output:

```text
PE32+
```

cho 64-bit.

Cấu trúc:

```text
DOS Header
DOS Stub
PE Signature
COFF File Header
Optional Header
Section Headers
Section Data
Directories
```

Optional Header chứa:

```text
ImageBase
SectionAlignment
FileAlignment
SizeOfImage
SizeOfHeaders
AddressOfEntryPoint
Subsystem
DllCharacteristics
DataDirectory[]
```

---

# 304.15. PE sections

Ví dụ:

```text
.text
.rdata
.data
.pdata
.xdata
.reloc
.rsrc
```

Không bắt buộc phải dùng chính xác các tên này nếu image policy không cần, nhưng semantic section phải map đúng.

---

# 304.16. PE RVA model

PE sử dụng mạnh:

```text
RVA
```

Do đó phải phân biệt:

```text
VA
RVA
FileOffset
```

Mapping:

```text
RVA
 ↓
Section
 ↓
FileOffset
```

phải được kiểm tra bằng verifier.

---

# 304.17. PE Import Directory

Dynamic imports phải tạo:

```text
Import Directory
Import Descriptor
ILT/INT
IAT
Hint/Name
DLL names
```

Ví dụ:

```text
kernel32.dll
    CreateFileW
    ...
```

Nhưng danh sách import đã được linker quyết định.

304 chỉ serialize.

---

# 304.18. PE Export Directory

Nếu Axiom shared library/DLL export:

```text
Export Directory
Export Address Table
Name Pointer Table
Ordinal Table
```

Mapping:

```text
LinkedImage.exports
      ↓
PE Export Directory
```

Không tự export toàn bộ global symbol.

---

# 304.19. PE Base Relocation

Nếu image không thể load đúng preferred base:

```text
.reloc
```

phải tồn tại nếu relocation policy yêu cầu.

304 phải serialize relocation blocks:

```text
IMAGE_BASE_RELOCATION
```

với:

```text
page RVA
entry type
entry offset
```

Nếu image được cấu hình:

```text
no dynamic base
```

thì policy phải explicit.

---

# 304.20. Windows unwind

x64/ARM64 Windows cần unwind metadata.

Ví dụ:

```text
.pdata
.xdata
```

304 phải nhận unwind records từ compiler/linker.

Không được bỏ unwind chỉ vì executable vẫn chạy trong trường hợp đơn giản.

Unwind cần cho:

- exception handling
- stack walking
- debugger
- crash reporting.

---

# 304.21. Mach-O executable

macOS/iOS output:

```text
MH_EXECUTE
MH_DYLIB
```

Header:

```text
mach_header_64
```

và Load Commands.

Ví dụ:

```text
LC_SEGMENT_64
LC_SYMTAB
LC_DYSYMTAB
LC_LOAD_DYLIB
LC_LOAD_DYLINKER
LC_MAIN
LC_UUID
LC_CODE_SIGNATURE
```

tùy image.

---

# 304.22. Mach-O segments

Các segment điển hình:

```text
__TEXT
__DATA_CONST
__DATA
__LINKEDIT
```

Sections:

```text
__TEXT,__text
__TEXT,__const
__TEXT,__cstring
__DATA_CONST,__const
__DATA,__data
__DATA,__bss
```

Writer phải tạo từ semantic section/segment layout, không hard-code mọi section.

---

# 304.23. Mach-O entry point

Modern Mach-O có thể dùng:

```text
LC_MAIN
```

với:

```text
entryoff
stacksize
```

`entryoff` phải được tính từ:

```text
LinkedImage.entry_point
```

và file/segment layout.

---

# 304.24. Mach-O dynamic linking

Nếu dynamic:

```text
LC_LOAD_DYLIB
LC_LOAD_WEAK_DYLIB
LC_LOAD_DYLINKER
```

và các metadata liên quan:

```text
dyld info
bind
rebase
export trie
```

được serialize từ linker metadata.

Không resolve symbol lần nữa.

---

# 304.25. Mach-O code signature

Apple platforms có yêu cầu code signing.

Thiết kế:

```text
CodeSignatureProvider
```

thay vì nhúng signing logic vào Mach-O core.

Pipeline:

```text
LinkedImage
 ↓
Mach-O layout
 ↓
Code-signature placeholder
 ↓
final hashes
 ↓
Code signature
 ↓
final image
```

Để hỗ trợ:

```text
unsigned development build
signed production build
```

mà không làm linker core phụ thuộc vào signing implementation.

---

# 304.26. WASM final writer

WASM final module không dùng native executable header.

Writer tạo:

```text
\0asm
version
sections...
```

Các section:

```text
Type
Import
Function
Table
Memory
Global
Export
Start
Element
Code
Data
DataCount
Custom
```

WASM module phải nhận:

```text
LinkedImage
```

đã resolve function/data symbols.

---

# 304.27. WASM start function

Nếu Axiom program có entry point:

```text
LinkedImage.entry_point
```

writer map thành:

```text
Start section
```

hoặc export theo target policy.

Không tự tìm `main`.

---

# 304.28. Final binary permissions

Image writer phải enforce:

```text
Code     → R-X
ReadOnly → R--
Data     → RW-
```

Không được vô tình tạo:

```text
RWX
```

do section grouping.

Nếu target yêu cầu khác, policy phải explicit.

---

# 304.29. Header placement

Image layout phải đảm bảo:

```text
headers
 ↓
alignment padding
 ↓
segments
```

Không được hard-code offsets trước khi toàn bộ size được biết.

Pipeline:

```text
Compute Metadata
      ↓
Compute Header Size
      ↓
Compute Segment Layout
      ↓
Compute Section Offsets
      ↓
Finalize Header
      ↓
Serialize
```

---

# 304.30. Binary serialization

Serializer phải hỗ trợ:

```text
ByteWriter
```

với API an toàn:

```text
write_u8
write_u16
write_u32
write_u64

write_bytes
write_at
reserve
patch
align
```

`write_at()` phải kiểm tra bounds.

Không sử dụng raw pointer arithmetic trong format writer safe code.

---

# 304.31. Endianness

Mọi format field phải được ghi theo endian của format/target.

Không dựa vào:

```text
memory reinterpret cast
```

để serialize struct trực tiếp.

Ví dụ:

```text
write_u32_le(...)
write_u64_le(...)
```

hoặc:

```text
BinaryEncoding
```

target-specific.

---

# 304.32. No native struct dumping

Cấm:

```text
write_bytes(&ElfHeader, sizeof(ElfHeader))
```

làm serialization contract.

Lý do:

- padding
- alignment
- host endian
- compiler layout
- ABI differences.

Phải serialize field-by-field.

---

# 304.33. Binary verifier

Sau serialization phải có:

```text
ImageVerifier
```

kiểm tra:

### ELF

```text
ELF magic
class
machine
entry
program headers
section/segment mapping
file bounds
alignment
dynamic metadata
```

### PE

```text
MZ
PE signature
optional header
RVA mapping
section bounds
directories
entry point
```

### Mach-O

```text
magic
CPU type
load command bounds
segment bounds
entry
dyld metadata
code signature placement
```

### WASM

```text
magic
version
section ordering
section lengths
index bounds
function/code consistency
```

---

# 304.34. Round-trip parser

Axiom phải có:

```text
ImageParser
```

để kiểm tra:

```text
serialize(ImageLayout)
        ↓
binary
        ↓
parse(binary)
        ↓
ImageLayout'
```

và:

```text
canonical(ImageLayout)
==
canonical(ImageLayout')
```

---

# 304.35. External tool differential test

Bootstrap có thể dùng:

```text
readelf
objdump
llvm-readobj
dumpbin
otool
wasm-objdump
```

để kiểm tra output.

Nhưng:

> Đây chỉ là test oracle; final Axiom toolchain không phụ thuộc vào chúng.

Ví dụ:

```text
Axiom
 ↓
foo.o
 ↓
Axiom Linker
 ↓
LinkedImage
 ↓
Axiom ELF Writer
 ↓
a.out
```

sau đó:

```text
readelf -h a.out
readelf -l a.out
```

chỉ để verify.

---

# 304.36. Crash-safe output

Không được ghi trực tiếp:

```text
program.exe
```

rồi nếu serializer lỗi để lại file hỏng.

Phải:

```text
serialize → temporary artifact
verify → atomic replace
```

Đặc biệt quan trọng với compiler build systems.

---

# 304.37. Deterministic binary

Deterministic mode phải kiểm soát:

```text
timestamps
UUID
build IDs
padding
section ordering
symbol ordering
metadata ordering
randomized hashes
```

Có thể hỗ trợ:

```text
BuildIdentity
```

nhưng phải được tạo từ semantic inputs:

```text
compiler version
source fingerprint
target
features
link inputs
```

thay vì random.

---

# 304.38. Build ID

Image writer có abstraction:

```text
BuildId {
    algorithm
    value
}
```

Có thể:

```text
SHA-256
SHA-1
UUID-like
TargetSpecific
```

Build ID phải được tính theo policy.

Không để build ID trở thành nguồn nondeterminism.

---

# 304.39. Debug stripping

Image writer phải hỗ trợ:

```text
KeepDebug
StripDebug
SplitDebug
```

Ví dụ:

```text
program
program.debug
```

hoặc target equivalent.

Quan trọng:

```text
strip debug
```

không được thay đổi machine semantics.

---

# 304.40. Unwind stripping

Debug và unwind là hai khái niệm khác nhau.

Không được:

```text
--strip-debug
```

đồng nghĩa với:

```text
remove unwind
```

Unwind có thể cần trong production runtime.

Policy phải tách:

```text
DebugPolicy
UnwindPolicy
```

---

# 304.41. Security metadata

Image writer phải có abstraction:

```text
SecurityPolicy {
    nx_stack
    pie
    relro
    aslr
    control_flow_metadata
    cet
    branch_protection
    code_signature
}
```

Không phải target nào cũng hỗ trợ tất cả.

Mỗi property có:

```text
Supported
Unsupported
Required
Optional
```

Không silently bỏ qua security option.

---

# 304.42. Platform policy

Tách:

```text
Architecture
ABI
OS
Format
SecurityPolicy
```

Ví dụ:

```text
x86_64 + Linux + SysV ABI + ELF
x86_64 + Windows + MS ABI + PE
arm64 + macOS + Darwin ABI + Mach-O
arm64 + iOS + Darwin ABI + Mach-O
```

Không dùng:

```text
if windows
```

trải khắp codebase.

Phải có:

```text
TargetPlatform
```

và backend policy.

---

# 304.43. Implementation tree

```text
compiler/backend/image/
│
├── image_ir.ax
├── image_layout.ax
├── image_writer.ax
├── binary_writer.ax
├── binary_reader.ax
├── verifier.ax
├── debug_policy.ax
├── unwind_policy.ax
├── security_policy.ax
│
├── elf/
│   ├── elf_image.ax
│   ├── program_headers.ax
│   ├── dynamic.ax
│   ├── tls.ax
│   ├── security.ax
│   └── writer.ax
│
├── pe/
│   ├── pe_image.ax
│   ├── headers.ax
│   ├── imports.ax
│   ├── exports.ax
│   ├── relocations.ax
│   ├── unwind.ax
│   └── writer.ax
│
├── macho/
│   ├── macho_image.ax
│   ├── load_commands.ax
│   ├── dyld.ax
│   ├── code_signature.ax
│   ├── exports.ax
│   └── writer.ax
│
└── wasm/
    ├── module.ax
    ├── sections.ax
    ├── indices.ax
    └── writer.ax
```

---

# 304.44. Public API

```text
fn emit_image(
    linked: LinkedImage,
    target: Target,
    options: ImageOptions
) -> Result<BinaryArtifact, ImageError>
```

Trong đó:

```text
BinaryArtifact {
    format
    architecture
    bytes
    entry_point
    sections
    segments
    debug_artifacts
    metadata
}
```

---

# 304.45. Invariants

```text
AIMG-20  Image writer chỉ nhận LinkedImage.

AIMG-21  Image writer không thực hiện symbol resolution.

AIMG-22  Image writer không thực hiện section GC.

AIMG-23  Image writer không thực hiện linker optimization.

AIMG-24  Image writer không được tự tìm entry symbol.

AIMG-25  FileOffset và VirtualAddress là các semantic type khác nhau.

AIMG-26  RVA không được nhầm với VA.

AIMG-27  Section và Segment là hai abstraction khác nhau.

AIMG-28  File size và memory size được theo dõi độc lập.

AIMG-29  BSS không được materialize thành file zero-fill không cần thiết.

AIMG-30  Segment alignment phải được bảo toàn.

AIMG-31  Không tạo RWX segment nếu policy không explicit.

AIMG-32  Header serialization phải field-by-field.

AIMG-33  Không dump native structs trực tiếp thành binary format.

AIMG-34  Endianness phải explicit.

AIMG-35  ELF executable phải có program headers hợp lệ.

AIMG-36  PE image phải có RVA/file-offset mapping hợp lệ.

AIMG-37  Mach-O load commands phải nằm trong bounds.

AIMG-38  WASM section lengths/indexes phải hợp lệ.

AIMG-39  Dynamic metadata phải được serialize từ linker metadata.

AIMG-40  Image writer không tự resolve dynamic imports.

AIMG-41  Entry point phải thuộc executable/loadable region hợp lệ.

AIMG-42  Debug stripping không được làm thay đổi code semantics.

AIMG-43  Unwind policy độc lập với debug policy.

AIMG-44  Security policy phải explicit.

AIMG-45  Code signing không được làm thay đổi linker semantics.

AIMG-46  Deterministic mode phải tạo binary deterministic.

AIMG-47  Build ID không được tạo nondeterminism ngoài policy.

AIMG-48  Serialized image phải pass ImageVerifier.

AIMG-49  serialize → parse phải giữ nguyên semantic image layout.

AIMG-50  Output lỗi không được để lại artifact cuối cùng bị hỏng.

AIMG-51  External binary inspection tools chỉ là test oracle.

AIMG-52  Final Axiom toolchain không cần external executable writer.

AIMG-53  Target-specific format logic không được lan vào Linker Core.

AIMG-54  Image writer phải hỗ trợ runtime-free images.

AIMG-55  Image writer phải hỗ trợ dynamic-runtime images.

AIMG-56  Shared library và executable dùng chung Image IR.

AIMG-57  Security metadata phải được kiểm tra trước serialization.

AIMG-58  Physical layout phải hoàn tất trước khi final header được serialize.

AIMG-59  Binary writer không được dùng unchecked offset arithmetic.

AIMG-60  Native image generation phải có thể self-host hoàn toàn.
```

---

# 304.46. Definition of Done

Axiom phải có khả năng:

```text
main.ax
   ↓
compiler
   ↓
Machine Code
   ↓
.o
   ↓
Linker
   ↓
LinkedImage
   ↓
Image Writer
   ↓
┌───────────────────────┐
│ Linux     → ELF       │
│ Windows   → PE        │
│ macOS     → Mach-O    │
│ iOS       → Mach-O    │
│ Android   → ELF       │
│ WASM      → WASM      │
└───────────────────────┘
```

và artifact phải:

- được OS/toolchain tương ứng nhận diện đúng format;
- có entry point hợp lệ;
- có section/segment mapping hợp lệ;
- có dynamic metadata khi cần;
- có unwind/debug metadata theo policy;
- có security metadata theo target;
- deterministic khi bật deterministic mode;
- pass Axiom `ImageVerifier`;
- không cần assembler;
- không cần external linker;
- không cần external executable writer.

Sau **304**, về mặt backend native, Axiom đã có chuỗi:

```text
Source
  ↓
Typed HIR
  ↓
MIR
  ↓
Verified MIR
  ↓
Optimized MIR
  ↓
Machine IR
  ↓
Machine Code
  ↓
Object
  ↓
LinkedImage
  ↓
Native Executable / Shared Library
```

Đây là mốc rất quan trọng: từ đây compiler không còn chỉ là một compiler “phát sinh assembly”, mà đã có kiến trúc để **tự tạo binary native hoàn chỉnh**.