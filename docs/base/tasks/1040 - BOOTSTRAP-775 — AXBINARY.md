# BOOTSTRAP-775 — AXBINARY

**Title:** Native Executable Image Model, PE64/ELF64/Mach-O/WASM Binary Construction, Headers, Segments, Imports/Exports, Entry Point, Load Layout, Binary Validation & Cross-Platform Native Image ABI 5.0  
**Namespace:** `AXBINARY`  
**Phase:** Axiom Native Toolchain / Final Binary Artifact Layer  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXBINARY` là lớp cuối cùng biến **linked image model** thành binary artifact mà hệ điều hành hoặc runtime target có thể load.

```text
AXSOURCE
   ↓
AXCOMPILER
   ↓
AXASSEMBLER
   ↓
AXOBJECT
   ↓
AXLINKER
   ↓
┌──────────────────────┐
│      AXBINARY        │
│                      │
│ image                │
│ segments             │
│ headers              │
│ imports / exports    │
│ entry point          │
│ TLS                  │
│ load configuration   │
│ platform metadata    │
└──────────┬───────────┘
           ↓
 PE64 / ELF64 / Mach-O / WASM
           ↓
 Native Artifact
```

AXBINARY không phải linker.

Nó nhận **final linked image** và chịu trách nhiệm biểu diễn chính xác image đó thành format binary target.

---

# 2. Boundary

### AXBINARY sở hữu

- executable image model;
- image headers;
- loadable segments;
- virtual/file layout;
- entry point representation;
- imports;
- exports;
- dynamic metadata;
- TLS image metadata;
- platform-specific binary structures;
- section-to-segment mapping;
- binary serialization;
- binary validation;
- executable image inspection.

### AXBINARY không sở hữu

```text
AXCOMPILER
→ source semantics / optimization

AXASSEMBLER
→ instruction encoding

AXOBJECT
→ relocatable object representation

AXLINKER
→ global symbol resolution / final link decisions

AXTOOLCHAIN
→ SDK/sysroot/toolchain identity

AXBUILD
→ build graph/cache

AXTRUST / AXCRYPTO
→ signing/cryptography

AXSECURITY
→ runtime security policy

OS loader
→ actual process loading
```

---

# 3. Nguyên tắc

AXBINARY phải:

- native;
- deterministic;
- dependency-free;
- architecture-aware;
- loader-compatible;
- streamable;
- inspectable;
- verifiable;
- compact;
- reproducible.

---

# 4. Linked image vs binary file

Phải phân biệt:

```text
LinkedImage
```

và:

```text
BinaryFile
```

`LinkedImage` là semantic representation.

`BinaryFile` là serialized representation.

```text
LinkedImage
    ↓
AXBINARY
    ↓
BinaryFile
```

Điều này cho phép một image có thể serialize thành nhiều format.

---

# 5. Canonical image model

```text
BinaryImage {
    format
    target
    abi
    image_type
    image_base
    entry_point
    segments[]
    sections[]
    imports[]
    exports[]
    tls
    dynamic_info
    debug_info
    unwind_info
    metadata[]
}
```

---

# 6. Image types

```text
EXECUTABLE
SHARED_LIBRARY
STATIC_LIBRARY
RELOCATABLE
WASM_MODULE
WASM_COMPONENT
```

Static library thực tế thường do archive layer xử lý, nhưng image abstraction có thể biểu diễn nó khi cần.

---

# 7. Target identity

Image bắt buộc có:

```text
architecture
os
environment
endianness
pointer_width
abi
```

---

# 8. Architecture baseline

AXBINARY 5.0:

```text
x86_64
aarch64
wasm32
```

Thiết kế mở rộng cho:

```text
riscv64
arm64e
x86
```

và các target sau này.

---

# 9. Platform baseline

```text
windows
linux
macos
ios
android
wasm
```

---

# 10. Segment model

Binary image sử dụng segment làm đơn vị load chính:

```text
Segment {
    type
    flags
    file_offset
    file_size
    virtual_address
    memory_size
    alignment
    sections[]
}
```

---

# 11. Segment flags

```text
READ
WRITE
EXECUTE
TLS
LOAD
DISCARD
```

---

# 12. W^X

AXBINARY validator phải reject image có segment:

```text
WRITE + EXECUTE
```

trừ khi target/platform descriptor explicitly cho phép.

Default:

> **Không tạo RWX segment.**

---

# 13. File-to-memory mapping

Mỗi loadable segment:

```text
file_offset
file_size
virtual_address
memory_size
```

cho phép biểu diễn:

```text
file data
+
zero-fill
```

---

# 14. Zero-fill

Nếu:

```text
memory_size > file_size
```

phần dư là zero-initialized memory.

Dùng cho:

```text
.bss
.tbss
```

---

# 15. Segment alignment

Mỗi segment có:

```text
alignment
```

và serializer phải bảo đảm:

```text
virtual_address % alignment == 0
```

theo target requirements.

---

# 16. Page alignment

Executable images thường page-align loadable segments.

AXBINARY nhận policy từ target ABI/platform.

---

# 17. Section model

Sections vẫn được giữ trong image để:

- debug;
- symbol inspection;
- platform metadata;
- tooling.

Nhưng loader thường quan tâm segments hơn.

---

# 18. Section-to-segment mapping

Mỗi section có:

```text
segment_id
```

hoặc:

```text
NO_SEGMENT
```

---

# 19. Section permissions

Section flags không được phép mâu thuẫn với segment permissions.

Ví dụ:

```text
EXEC section
```

không được nằm trong non-executable segment nếu section cần execute.

---

# 20. Image layout

Canonical planning:

```text
headers
 ↓
RX segments
 ↓
RO segments
 ↓
RW segments
 ↓
TLS
 ↓
metadata/debug
```

Actual ordering target-specific.

---

# 21. Header region

AXBINARY có:

```text
header_size
header_alignment
```

và reserved space nếu target cần.

---

# 22. Image base

Windows/ELF/Mach-O image có thể có:

```text
preferred_base
```

hoặc:

```text
image_base
```

---

# 23. PIE

ELF executable có thể:

```text
PIE = true
```

khi target ABI yêu cầu.

---

# 24. ASLR

AXBINARY không bật ASLR trực tiếp.

Nó biểu diễn các flags/relocations để platform loader có thể thực hiện.

---

# 25. Entry point

Canonical:

```text
entry_point {
    virtual_address
    symbol_id?
}
```

---

# 26. Entry validation

Entry phải:

- nằm trong executable segment;
- có valid mapped address;
- không nằm ngoài image.

---

# 27. Startup boundary

AXBINARY chỉ serialize entry point.

Startup implementation thuộc runtime/platform layer.

Ví dụ:

```text
OS
 ↓
Axiom startup
 ↓
main
```

---

# 28. Windows PE64

AXBINARY phải native-generate:

```text
PE32+
```

cho x86-64/AArch64 Windows khi supported.

---

# 29. DOS header

PE serializer có thể emit minimal valid DOS header/stub structure.

Không cần phụ thuộc DOS runtime.

---

# 30. PE signature

```text
PE\0\0
```

được emit tại đúng offset.

---

# 31. COFF header

PE image phải có:

```text
Machine
NumberOfSections
TimeDateStamp
PointerToSymbolTable
NumberOfSymbols
SizeOfOptionalHeader
Characteristics
```

với reproducibility rules phù hợp.

---

# 32. PE optional header

AXBINARY quản lý:

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

# 33. PE reproducibility

Timestamp phải có deterministic policy.

Trong reproducible mode:

```text
timestamp = canonical value
```

hoặc target-supported reproducible representation.

---

# 34. PE sections

Typical:

```text
.text
.rdata
.data
.pdata
.xdata
.reloc
.rsrc
```

AXBINARY không bắt buộc exact names cho internal sections, nhưng PE mapping phải đúng semantics.

---

# 35. PE import directory

Imports:

```text
DLL
 ↓
ImportDescriptor
 ↓
ImportNameTable
 ↓
IAT
```

---

# 36. PE export directory

Exports:

```text
name
ordinal
RVA
```

phải deterministic.

---

# 37. PE IAT

Import Address Table phải được layout đúng và writable khi loader cần patch.

---

# 38. PE delay imports

Optional metadata có thể represent:

```text
delay_import
```

---

# 39. PE base relocations

Nếu image hỗ trợ dynamic relocation:

```text
.reloc
```

được generated từ link relocation plan.

---

# 40. PE relocation type

AXBINARY không tự suy luận relocation.

AXLINKER cung cấp resolved image relocation records.

---

# 41. PE TLS

PE TLS directory có thể chứa:

```text
start_address_of_raw_data
end_address_of_raw_data
address_of_index
address_of_callbacks
size_of_zero_fill
characteristics
```

---

# 42. PE TLS callbacks

Callbacks phải được ordered deterministic.

---

# 43. PE exception data

x64:

```text
.pdata
.xdata
```

được emit theo unwind metadata.

---

# 44. PE subsystem

Image metadata xác định:

```text
CONSOLE
WINDOWS
EFI
OTHER
```

target policy quyết định valid values.

---

# 45. PE DLL

Shared library:

```text
IMAGE_FILE_DLL
```

và export/import metadata.

---

# 46. ELF64

AXBINARY native serializer phải hỗ trợ:

```text
ELF64
```

---

# 47. ELF header

Bao gồm:

```text
e_ident
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

# 48. ELF program headers

Loadable image phải generate:

```text
PT_LOAD
```

và khi cần:

```text
PT_DYNAMIC
PT_TLS
PT_GNU_STACK
PT_GNU_RELRO
PT_PHDR
```

---

# 49. PT_LOAD

Mỗi load segment:

```text
p_offset
p_vaddr
p_paddr
p_filesz
p_memsz
p_flags
p_align
```

---

# 50. ELF section headers

Có thể retain:

```text
.text
.rodata
.data
.bss
.symtab
.strtab
.debug*
```

nhưng production stripping có thể remove non-required tables.

---

# 51. ELF dynamic section

Shared/dynamic executable có:

```text
.dynamic
```

với entries phù hợp.

---

# 52. ELF imports

Dynamic symbols:

```text
.dynsym
.dynstr
```

và relocation metadata.

---

# 53. ELF exports

Public dynamic symbols được đặt trong dynamic symbol table khi required.

---

# 54. GOT

AXBINARY layout có thể include:

```text
.got
.got.plt
```

nếu ABI/link model yêu cầu.

---

# 55. PLT

PLT stubs được AXLINKER/ABI lowering quyết định; AXBINARY serialize final bytes/sections.

---

# 56. RELRO

Nếu enabled:

```text
PT_GNU_RELRO
```

được tạo và boundaries validated.

---

# 57. GNU_STACK

Nếu target Linux sử dụng:

```text
PT_GNU_STACK
```

AXBINARY phải emit non-executable stack by default.

---

# 58. ELF TLS

Support:

```text
PT_TLS
```

với:

```text
.tdata
.tbss
```

---

# 59. ELF PIE

ET_DYN + entry/load layout theo platform ABI khi PIE enabled.

---

# 60. ELF shared library

```text
ET_DYN
```

với dynamic metadata.

---

# 61. ELF static executable

Có thể tạo:

```text
ET_EXEC
```

hoặc target-appropriate static image.

---

# 62. Mach-O

AXBINARY hỗ trợ:

```text
Mach-O 64-bit
```

---

# 63. Mach-O header

```text
mach_header_64
```

với:

```text
cputype
cpusubtype
filetype
ncmds
sizeofcmds
flags
reserved
```

---

# 64. Load commands

AXBINARY emit canonical load-command sequence.

---

# 65. Segments

Baseline:

```text
__TEXT
__DATA
__LINKEDIT
```

và target-required variants.

---

# 66. Mach-O `__TEXT`

Có thể chứa:

```text
__text
__cstring
__const
```

---

# 67. Mach-O `__DATA`

Có thể chứa:

```text
__data
__bss
__common
```

---

# 68. Mach-O linkedit

Có thể chứa:

```text
symbol table
string table
dyld info
export trie
code signature structures
```

---

# 69. Dyld information

AXBINARY biểu diễn required dynamic loader structures.

---

# 70. Imports

Mach-O imports được biểu diễn qua:

```text
undefined symbols
binding information
```

theo target ABI.

---

# 71. Exports

Có thể dùng:

```text
export trie
```

hoặc target-supported equivalent.

---

# 72. Mach-O relocations

Relocations còn cần ở relocatable object layer; final image chỉ giữ structures cần thiết cho runtime/linker semantics.

---

# 73. Mach-O PIE

Executable có flags/load commands phù hợp với PIE policy.

---

# 74. Mach-O dylib

Shared library:

```text
MH_DYLIB
```

với identity/install-name metadata.

---

# 75. Framework/app boundary

AXBINARY không trở thành package manager.

`.app`, framework bundle và signing workflow thuộc platform/package layers.

---

# 76. iOS

iOS target sử dụng Mach-O nhưng có platform-specific requirements.

AXBINARY phải nhận:

```text
platform = ios
```

và apply target validation.

---

# 77. iOS signing boundary

AXBINARY **không sign executable**.

Pipeline:

```text
AXBINARY
 ↓
unsigned Mach-O
 ↓
AXTRUST / platform signing
```

---

# 78. Android

Android native executable/library sử dụng ELF64 trên baseline AArch64.

AXBINARY dùng ELF serializer với Android target descriptor.

---

# 79. Android-specific validation

Target descriptor có thể yêu cầu:

- ABI;
- page alignment;
- dynamic loader constraints;
- API level.

AXBINARY validate metadata nhưng không tự quản lý Android package.

---

# 80. WASM

WASM binary khác CPU executable.

AXBINARY hỗ trợ:

```text
WASM_MODULE
```

---

# 81. WASM sections

Canonical:

```text
TYPE
IMPORT
FUNCTION
TABLE
MEMORY
GLOBAL
EXPORT
START
ELEMENT
CODE
DATA
CUSTOM
```

---

# 82. WASM module order

WASM section ordering phải tuân thủ format specification.

---

# 83. WASM function index

Final function index phải deterministic.

---

# 84. WASM imports

```text
module
name
kind
type/index
```

---

# 85. WASM exports

```text
name
kind
index
```

---

# 86. WASM memory

Image có thể define:

```text
initial_pages
maximum_pages?
shared
```

theo target runtime.

---

# 87. WASM table

Nếu dùng indirect calls:

```text
table
element segments
```

phải được serialize.

---

# 88. WASM start function

Nếu có:

```text
START
```

phải trỏ tới valid function index.

---

# 89. WASM custom AX metadata

Axiom có thể emit:

```text
custom section:
axiom.*
```

cho:

- debug;
- source map;
- AI metadata;
- ABI metadata.

---

# 90. WASM validation

AXBINARY phải validate:

- section order;
- indices;
- function/code counts;
- memory limits;
- exports;
- start function;
- custom section lengths.

---

# 91. Binary image address space

Canonical image model dùng:

```text
VA
RVA
FileOffset
```

tách biệt.

---

# 92. Address conversion

Mỗi format backend phải define:

```text
VA → file offset
RVA → file offset
section offset → VA
```

không dùng công thức platform-independent giả định.

---

# 93. Overflow

Mọi address arithmetic phải checked.

---

# 94. Image size

```text
image_size
```

phải fit target address width.

---

# 95. Header size validation

Headers không được overlap loadable data.

---

# 96. Segment overlap

Loadable segments không được overlap trái phép.

---

# 97. File overlap

Hai binary regions không được overlap nếu semantics không cho phép.

---

# 98. Alignment padding

Padding phải deterministic và zeroed khi không phải code padding.

---

# 99. Code padding

Code alignment có thể dùng architecture-specific NOP.

---

# 100. Data padding

Data padding mặc định zero.

---

# 101. Binary layout algorithm

Canonical:

```text
collect sections
    ↓
classify permissions
    ↓
group into segments
    ↓
apply target alignment
    ↓
assign virtual addresses
    ↓
assign file offsets
    ↓
place headers
    ↓
place metadata
    ↓
emit image
```

---

# 102. Layout ownership

Final layout decision thuộc AXLINKER.

AXBINARY nhận layout plan và serialize/validate.

Nếu AXBINARY cần target-specific constraints, nó có thể reject layout không hợp lệ.

---

# 103. Linker correction boundary

AXBINARY **không âm thầm thay đổi** linker decisions.

Ví dụ:

```text
segment too small
```

→ diagnostic, không tự di chuyển symbol.

---

# 104. Final address stability

Sau khi AXBINARY bắt đầu serialization:

> Final virtual addresses phải immutable.

---

# 105. Imports model

```text
Import {
    library
    symbol
    ordinal?
    flags
}
```

---

# 106. Export model

```text
Export {
    symbol
    name
    ordinal?
    flags
}
```

---

# 107. Library identity

Shared library identity phải explicit.

Ví dụ:

```text
libfoo.so
foo.dll
Foo.framework
```

nhưng filename không phải identity duy nhất.

---

# 108. Dynamic dependency

```text
Dependency {
    identity
    version
    required
}
```

---

# 109. Dependency ordering

Dynamic dependencies phải deterministic.

---

# 110. Import validation

Mọi import phải:

- target-valid;
- ABI-compatible;
- format-representable.

---

# 111. Export validation

Không cho phép export symbol không tồn tại.

---

# 112. Duplicate exports

Phải deterministic error hoặc target-defined resolution.

---

# 113. Symbol stripping

Release mode có thể strip:

- local symbols;
- debug;
- compiler metadata;
- AI metadata.

Không được strip required dynamic exports.

---

# 114. Debug artifact separation

Có thể emit:

```text
app.exe
app.debug
```

hoặc platform-equivalent.

---

# 115. Debug link identity

Executable giữ debug artifact ID:

```text
debug_id
```

---

# 116. Build ID

Final image có:

```text
build_id
```

để map crash → exact artifact.

---

# 117. Content hash

Final binary có canonical content hash.

Không hash field chứa chính hash.

---

# 118. Reproducible binary

Cùng:

```text
source
compiler
toolchain
SDK
options
target
```

→ cùng binary trong reproducible mode.

---

# 119. Non-reproducible fields

Nếu platform bắt buộc timestamp/random UUID:

AXBINARY phải hỗ trợ:

```text
canonical build value
```

hoặc explicit non-reproducible mode.

---

# 120. UUID

Mach-O có UUID/load identity semantics.

Axiom build system phải derive deterministic UUID khi reproducibility được bật và platform cho phép.

---

# 121. PE timestamp

Không dùng wall-clock time làm identity trong reproducible build.

---

# 122. ELF build ID

Có thể derive từ canonical image content.

---

# 123. Binary cache

AXBINARY output có thể cache bằng:

```text
image_hash
+
toolchain_fingerprint
```

---

# 124. Atomic publication

Binary output:

```text
temp
 ↓ validate
 ↓ fsync nếu policy yêu cầu
 ↓ atomic rename
```

---

# 125. Crash safety

Không để build crash tạo file executable tưởng là hoàn chỉnh.

---

# 126. Binary writer

API:

```text
binary_create()
binary_add_segment()
binary_add_section()
binary_set_entry()
binary_add_import()
binary_add_export()
binary_set_tls()
binary_set_debug()
binary_finalize()
binary_write()
```

---

# 127. Validator API

```text
binary_validate()
binary_validate_headers()
binary_validate_layout()
binary_validate_entry()
binary_validate_imports()
binary_validate_exports()
binary_validate_tls()
```

---

# 128. Reader API

```text
binary_open()
binary_format()
binary_target()
binary_headers()
binary_segments()
binary_sections()
binary_imports()
binary_exports()
binary_entry()
```

---

# 129. Inspection CLI

```text
axiom bin info app.exe
axiom bin sections app.exe
axiom bin segments app.exe
axiom bin symbols app.exe
axiom bin imports app.exe
axiom bin exports app.exe
axiom bin validate app.exe
```

---

# 130. Cross-format inspection

CLI phải cho phép cùng abstraction:

```text
axiom bin info
```

đối với:

```text
.exe
ELF
Mach-O
.wasm
```

---

# 131. Format detection

Magic/header được dùng để detect.

Không dựa filename.

---

# 132. Reader safety

Binary reader coi input là untrusted.

---

# 133. Parser resource limits

Có:

```text
max_sections
max_segments
max_symbols
max_imports
max_exports
max_metadata
max_file_size
```

---

# 134. Integer safety

Mọi:

```text
offset + size
VA + size
RVA + size
```

phải overflow-safe.

---

# 135. Malformed binary

Không được:

```text
panic
out-of-bounds
arbitrary allocation
```

---

# 136. No execution

AXBINARY reader không được load hoặc execute binary code.

---

# 137. Dynamic library inspection

Inspection `.dll/.so/.dylib` chỉ parse metadata.

Không gọi loader.

---

# 138. Signature boundary

AXBINARY có thể preserve:

```text
signature_blob
```

nhưng verification thuộc AXTRUST/AXCRYPTO.

---

# 139. Certificate boundary

PE certificate table, Apple code-signature structures và tương tự được treated as platform signing artifacts.

---

# 140. Signing order

Canonical pipeline:

```text
AXLINKER
 ↓
AXBINARY
 ↓
validate
 ↓
AXTRUST/AXCRYPTO signing
 ↓
final signed artifact
```

---

# 141. Signing effect

Nếu signing modifies file bytes, final artifact hash phải được calculated **after signing**.

---

# 142. Platform metadata

AXBINARY supports opaque target metadata:

```text
platform.*
```

với versioned schemas.

---

# 143. Subsystem metadata

```text
windows.subsystem
android.api_level
ios.minimum_os
linux.abi
wasm.features
```

---

# 144. Target policy

`AXTOOLCHAIN` cung cấp target policy.

AXBINARY chỉ validate.

---

# 145. Binary ABI

```text
AXBINARY_ABI_1
```

độc lập với:

```text
AXOBJECT_ABI_1
AXLINKER_ABI_1
AXASSEMBLER_ABI_1
```

---

# 146. In-memory image

AXBINARY phải có khả năng tạo:

```text
BinaryImage
```

mà chưa cần serialize.

Điều này phục vụ:

- validation;
- inspection;
- testing;
- future in-memory loader tooling.

---

# 147. No runtime loader

Axiom OS process loading vẫn do OS.

AXBINARY không trở thành user-space executable loader.

---

# 148. Future custom loader

Nếu Axiom sau này có custom runtime/embedded environment, AXBINARY model vẫn có thể được dùng.

---

# 149. Kernel/boot image

Thiết kế nên cho phép:

```text
IMAGE_KIND = KERNEL
BOOT
FIRMWARE
```

nhưng không nằm trong mandatory 5.0 desktop pipeline.

---

# 150. Embedded target

Segment model đủ generic để hỗ trợ embedded sau này.

---

# 151. Static executable minimalism

AXBINARY phải cho phép binary cực nhỏ:

```text
headers
+
required code
+
required data
```

Không tự thêm runtime sections nếu không cần.

---

# 152. Runtime minimization

Axiom executable không được tự động link:

```text
large runtime
```

chỉ vì dùng một primitive.

---

# 153. Dead metadata elimination

Unused debug/compiler/AI metadata có thể strip.

---

# 154. Section garbage collection boundary

AXLINKER quyết định reachability.

AXBINARY serialize kết quả.

---

# 155. Binary compression

Không nén executable trong core binary serializer.

Compression thuộc packaging/distribution.

---

# 156. Package boundary

Ví dụ:

```text
.exe
.apk
.app
.wasm
```

không phải tất cả đều là AXBINARY artifacts.

`APK`, `APP bundle` thuộc package/deployment layers.

---

# 157. Windows application

Pipeline:

```text
AXCOMPILER
 ↓
AXOBJECT
 ↓
AXLINKER
 ↓
AXBINARY
 ↓
PE64 .exe
```

---

# 158. Linux application

```text
AXCOMPILER
 ↓
AXOBJECT
 ↓
AXLINKER
 ↓
AXBINARY
 ↓
ELF64
```

---

# 159. macOS application

```text
...
 ↓
AXBINARY
 ↓
Mach-O
 ↓
package/sign
```

---

# 160. iOS application

```text
...
 ↓
Mach-O
 ↓
platform packaging/signing
```

---

# 161. Android native library

```text
...
 ↓
ELF64
 ↓
Android packaging
```

---

# 162. WASM application

```text
...
 ↓
AXBINARY
 ↓
WASM module
```

---

# 163. Final binary validation

Before write:

```text
linker result
 ↓
AXBINARY validate
 ↓
serialize
 ↓
read-back validate
```

---

# 164. Mandatory read-back validation

Production deterministic mode nên hỗ trợ:

```text
write
 ↓
reopen
 ↓
validate
```

để phát hiện serializer bugs.

---

# 165. Binary round-trip

```text
Binary
 ↓
Reader
 ↓
ImageModel
 ↓
Writer
 ↓
Binary
```

phải preserve canonical semantics.

---

# 166. Format-specific round-trip

PE:

```text
PE → model → PE
```

ELF:

```text
ELF → model → ELF
```

Mach-O:

```text
Mach-O → model → Mach-O
```

WASM:

```text
WASM → model → WASM
```

trong supported canonical subset.

---

# 167. External binary compatibility

AXBINARY reader phải đọc executable được tạo bởi external toolchains ở supported formats.

---

# 168. Native writer independence

Native writer không gọi:

```text
lld
ld
link.exe
ld64
wasm-ld
```

để generate binary.

---

# 169. External compatibility mode

External tools chỉ được dùng trong bootstrap/interoperability path.

---

# 170. Performance architecture

Hot serialization path:

```text
precomputed offsets
+
linear writes
+
buffered IO
```

---

# 171. Two-pass serialization

Recommended:

```text
PASS 1
calculate sizes/offsets

PASS 2
emit bytes
```

---

# 172. Why two-pass

Tránh:

```text
realloc
backpatch explosion
```

và giúp deterministic layout.

---

# 173. Streaming

Nếu target format cho phép, large sections có thể stream.

---

# 174. Random-access metadata

Headers/segment tables phải được written early.

---

# 175. Memory bound

AXBINARY không cần giữ duplicate copies của toàn bộ machine code.

---

# 176. Zero-copy section source

Image builder có thể reference immutable AXOBJECT/AXLINKER buffers.

---

# 177. Ownership

Writer không được mutate input linked image.

---

# 178. Immutable linked image

Sau khi handoff:

```text
AXLINKER → AXBINARY
```

linked image là immutable.

---

# 179. Parallel format generation

Không cần generate nhiều formats cùng lúc trong một process, nhưng architecture không được cản trở.

---

# 180. Deterministic section ordering

Target backend phải có canonical ordering function.

---

# 181. Deterministic symbol ordering

Dynamic/public symbols phải được serialized deterministic.

---

# 182. Deterministic import ordering

Sort theo canonical:

```text
library identity
symbol identity
ordinal
```

theo target rules.

---

# 183. Deterministic export ordering

Canonical symbol identity/order.

---

# 184. Deterministic dependency ordering

Dependencies phải stable.

---

# 185. PE directory ordering

Data directories có fixed semantic indices theo PE specification.

---

# 186. ELF program-header ordering

Canonical order:

```text
PHDR
INTERP
LOAD
DYNAMIC
TLS
GNU_RELRO
...
```

chỉ khi applicable; backend phải tuân target ABI.

---

# 187. Mach-O load command ordering

Canonical target-defined ordering.

---

# 188. WASM section ordering

Strict format order.

---

# 189. Binary error taxonomy

```text
BIN_INVALID
BIN_UNSUPPORTED_FORMAT
BIN_UNSUPPORTED_TARGET
BIN_HEADER_INVALID
BIN_LAYOUT_INVALID
BIN_SEGMENT_INVALID
BIN_SECTION_INVALID
BIN_ADDRESS_OVERFLOW
BIN_ENTRY_INVALID
BIN_IMPORT_INVALID
BIN_EXPORT_INVALID
BIN_TLS_INVALID
BIN_DYNAMIC_INVALID
BIN_RELOCATION_INVALID
BIN_METADATA_INVALID
BIN_ALIGNMENT_INVALID
BIN_RESOURCE_LIMIT
BIN_SERIALIZATION_FAILURE
BIN_INTEGRITY_FAILURE
BIN_SIGNATURE_INVALID
```

---

# 190. Error localization

Diagnostics phải chỉ:

```text
format
file offset
virtual address
structure
field
```

khi có thể.

---

# 191. Binary inspection metadata

CLI có thể hiển thị:

```text
Image type
Architecture
ABI
Entry
Image size
Segments
Imports
Exports
TLS
Debug ID
Build ID
```

---

# 192. Security hardening

Validator phải kiểm tra:

- overlapping load regions;
- malformed imports;
- invalid entry;
- invalid segment permissions;
- integer overflow;
- impossible sizes;
- invalid TLS;
- invalid dynamic structures.

---

# 193. W^X validation

Default:

```text
RWX → ERROR
```

trừ explicit platform exception.

---

# 194. Non-executable stack

Nếu target có stack metadata:

```text
NX stack
```

là default.

---

# 195. Read-only metadata

Metadata không cần mutation runtime phải được đặt vào RO region.

---

# 196. Relro

Nếu platform hỗ trợ:

```text
RELRO
```

được applied theo link policy.

---

# 197. Import hardening

Import structures không được nằm trong executable-only segment nếu loader cần write access.

---

# 198. Export hardening

Không expose symbol ngoài public export policy.

---

# 199. Minimal permissions

Segment permissions phải là minimum cần thiết.

---

# 200. Image trust

Một binary hợp lệ về format **không đồng nghĩa trusted**.

Trust:

```text
AXBINARY validation
        ≠
AXTRUST verification
```

---

# 201. API — image

```text
binary_image_create()
binary_image_destroy()

binary_image_set_target()
binary_image_set_type()
binary_image_set_entry()
binary_image_set_base()

binary_image_add_segment()
binary_image_add_section()

binary_image_add_import()
binary_image_add_export()

binary_image_set_tls()
binary_image_set_dynamic()
binary_image_add_metadata()
```

---

# 202. API — layout

```text
binary_plan_layout()
binary_assign_addresses()
binary_assign_file_offsets()
binary_validate_layout()
```

---

# 203. API — serialization

```text
binary_serialize()
binary_write()
binary_finalize()
```

---

# 204. API — inspection

```text
binary_open()
binary_header()
binary_segments()
binary_sections()
binary_imports()
binary_exports()
binary_entry()
binary_metadata()
```

---

# 205. API — validation

```text
binary_validate()
binary_validate_format()
binary_validate_target()
binary_validate_headers()
binary_validate_segments()
binary_validate_sections()
binary_validate_entry()
binary_validate_dynamic()
binary_validate_tls()
```

---

# 206. API — format backend

```text
binary_backend_find()
binary_backend_pe64()
binary_backend_elf64()
binary_backend_macho64()
binary_backend_wasm32()
```

---

# 207. Backend contract

```text
BinaryFormatBackend {
    detect()
    validate()
    plan()
    serialize()
    inspect()
}
```

---

# 208. Backend independence

PE backend không được biết ELF internals.

ELF backend không được biết Mach-O internals.

---

# 209. Common model

Các backend chỉ giao tiếp qua:

```text
BinaryImage
```

---

# 210. Platform extension

Target-specific extension:

```text
windows.*
linux.*
apple.*
android.*
wasm.*
```

---

# 211. Native ABI

```text
AXBINARY_ABI_1
```

là binary image API contract.

---

# 212. Bootstrap

Stage 0:

```text
external linker/writer
```

có thể tạo executable.

Stage 1:

```text
Axiom AXBINARY
```

được compile bởi external compiler.

Stage 2:

```text
Axiom compiler
 + AXOBJECT
 + AXLINKER
 + AXBINARY
```

tạo chính toolchain.

---

# 213. Self-hosted toolchain

Mục tiêu:

```text
Axiom source
 ↓
Axiom compiler
 ↓
Axiom assembler
 ↓
Axiom object
 ↓
Axiom linker
 ↓
Axiom binary
```

Không cần:

```text
GCC
LLVM
MSVC linker
GNU ld
```

trong production toolchain.

---

# 214. Bootstrap verification

So sánh:

```text
external-built toolchain
        vs
self-built toolchain
```

qua:

- binary hashes;
- object hashes;
- compiler outputs;
- test suite.

---

# 215. PE64 acceptance test

Input:

```text
fn main() {
    ...
}
```

Output:

```text
hello.exe
```

Validator kiểm tra:

```text
PE32+
x86_64
valid entry
valid sections
valid imports
valid image size
```

---

# 216. ELF acceptance test

Output:

```text
hello
```

kiểm tra:

```text
ELF64
x86_64
valid PT_LOAD
valid entry
```

---

# 217. AArch64 acceptance

```text
hello
```

target:

```text
aarch64-linux
```

---

# 218. Mach-O acceptance

```text
hello
```

target:

```text
aarch64-macos
```

---

# 219. iOS acceptance

Native library/application Mach-O generation phải pass target structural validation.

Signing được test ở integration layer.

---

# 220. Android acceptance

AArch64 ELF shared library:

```text
libhello.so
```

pass Android target validation.

---

# 221. WASM acceptance

Generate:

```text
hello.wasm
```

validate module structure and execute through an external WASM runtime in integration tests.

---

# 222. Dynamic library tests

Test:

```text
foo.dll
libfoo.so
libfoo.dylib
```

with import/export symbols.

---

# 223. TLS tests

Test executable and shared library TLS.

---

# 224. PIE tests

Build PIE ELF and validate relocatable image properties.

---

# 225. ASLR-related tests

Validate required relocation structures without claiming runtime security behavior beyond platform semantics.

---

# 226. Debug tests

Executable:

```text
binary
+
debug artifact
```

must retain exact build/debug identity relationship.

---

# 227. Strip tests

Debug/compiler/AI metadata stripping must not alter runtime semantics.

---

# 228. Reproducibility tests

Build twice in separate directories:

```text
/project/A
/project/B
```

with same canonical inputs.

Expected:

```text
same canonical hash
```

---

# 229. Environment independence

Build output must not depend on:

- absolute source path;
- hostname;
- username;
- current time;

unless explicitly configured.

---

# 230. Fuzz testing

Fuzz all readers:

```text
PE
ELF
Mach-O
WASM
```

---

# 231. Mutation testing

Take valid binary and mutate:

- offsets;
- sizes;
- counts;
- flags;
- addresses.

Reader must reject or safely handle.

---

# 232. Differential validation

Compare native parser against authoritative format behavior during development.

Native implementation remains independent.

---

# 233. Large image test

Test images with:

```text
thousands of sections
millions of symbols
large .rodata
large code
```

subject to practical resource limits.

---

# 234. Minimal image test

Also test smallest valid executable for each format.

---

# 235. Address boundary tests

Test:

```text
0
max-1
max
overflow
```

for address arithmetic.

---

# 236. Alignment boundary tests

Test:

```text
1
2
4
...
page_size
```

and invalid non-power-of-two values where target forbids them.

---

# 237. Import/export tests

Test:

```text
0 imports
1 import
many imports
0 exports
many exports
```

---

# 238. Binary determinism

Repeated serialization of identical `BinaryImage` must produce identical bytes.

---

# 239. Immutable model

Once finalized:

```text
BinaryImage
```

cannot mutate without creating a new image.

---

# 240. Formal invariants

```text id="u2h4x1"
BIN-INV-01
Mọi BinaryImage phải có valid target descriptor.

BIN-INV-02
Mọi BinaryImage phải có valid image type.

BIN-INV-03
Format backend phải tương thích target.

BIN-INV-04
Header size phải nằm trong file bounds.

BIN-INV-05
Mọi segment file range phải nằm trong file.

BIN-INV-06
Mọi segment memory range phải fit target address space.

BIN-INV-07
Mọi section phải map tới segment hợp lệ hoặc explicit NO_SEGMENT.

BIN-INV-08
Section permissions không được mâu thuẫn với segment permissions.

BIN-INV-09
RWX segments bị reject mặc định.

BIN-INV-10
Segment alignment phải hợp lệ.

BIN-INV-11
File offsets phải overflow-safe.

BIN-INV-12
Virtual addresses phải overflow-safe.

BIN-INV-13
File regions không được overlap trái phép.

BIN-INV-14
Memory regions không được overlap trái phép.

BIN-INV-15
Entry point phải nằm trong executable region.

BIN-INV-16
Entry point phải phù hợp image type.

BIN-INV-17
Zero-fill region phải có memory_size >= file_size.

BIN-INV-18
Import phải reference valid dependency identity.

BIN-INV-19
Export phải reference symbol tồn tại.

BIN-INV-20
Duplicate exports phải được xử lý deterministic.

BIN-INV-21
Dynamic metadata phải phù hợp image type.

BIN-INV-22
TLS metadata phải phù hợp target ABI.

BIN-INV-23
PE images phải có valid PE32+ structures.

BIN-INV-24
ELF images phải có valid ELF64 structures.

BIN-INV-25
Mach-O images phải có valid 64-bit Mach-O structures.

BIN-INV-26
WASM modules phải tuân thủ section ordering và index validity.

BIN-INV-27
Binary serialization phải deterministic trong canonical mode.

BIN-INV-28
Padding trong canonical mode phải deterministic.

BIN-INV-29
Build identity không được phụ thuộc machine-local nondeterminism trong reproducible mode.

BIN-INV-30
Binary reader không được execute input code.

BIN-INV-31
Binary reader phải enforce resource limits.

BIN-INV-32
Malformed binary không được gây memory-unsafe behavior.

BIN-INV-33
AXBINARY không được tự ý thay đổi final linker addresses.

BIN-INV-34
Final image phải immutable trước serialization.

BIN-INV-35
Signing không thuộc AXBINARY core authority.

BIN-INV-36
Binary validity không đồng nghĩa binary trust.

BIN-INV-37
Native binary writer không được yêu cầu third-party linker/loader.

BIN-INV-38
AXBINARY phải hỗ trợ AXBINARY_ABI_1.

BIN-INV-39
Mọi format backend phải implement common BinaryFormatBackend contract.

BIN-INV-40
AXBINARY chỉ chịu trách nhiệm final binary image representation/serialization; symbol resolution và link decisions thuộc AXLINKER.
```

---

# 241. Definition of Done

`AXBINARY 5.0` được freeze khi có đầy đủ:

### Core

- BinaryImage;
- target identity;
- ABI identity;
- image types;
- sections;
- segments;
- permissions;
- alignment;
- file/memory mapping;
- entry point;
- imports;
- exports;
- TLS;
- dynamic metadata;
- debug identity;
- build identity.

### PE64

- DOS/PE headers;
- COFF header;
- optional header;
- section table;
- data directories;
- imports;
- exports;
- IAT;
- relocations;
- TLS;
- exception/unwind data;
- subsystem;
- DLL image;
- reproducible output.

### ELF64

- ELF header;
- program headers;
- sections;
- PT_LOAD;
- PT_DYNAMIC;
- PT_TLS;
- dynamic symbols;
- GOT/PLT;
- RELRO;
- PIE;
- shared libraries;
- static images.

### Mach-O

- Mach header;
- load commands;
- segments;
- sections;
- dyld metadata;
- imports;
- exports;
- dylib;
- PIE;
- TLS/target structures;
- code-signing boundary.

### WASM

- type;
- import;
- function;
- table;
- memory;
- global;
- export;
- start;
- element;
- code;
- data;
- custom sections.

### Infrastructure

- deterministic serialization;
- reproducible build;
- content hashing;
- binary cache;
- read-back validation;
- mmap/stream-friendly reader;
- fuzzing;
- malformed-input hardening;
- resource limits;
- cross-format inspection;
- self-host bootstrap;
- `AXBINARY_ABI_1`;
- 40 invariants.

**AXBINARY 5.0 → FROZEN.**

---

# Chuỗi native toolchain hiện tại

Đến đây architecture đã có một đường đi khá rõ:

```text
                 AXTOOLCHAIN
                      │
                      ▼
SOURCE ───────► AXCOMPILER
                      │
                      ▼
                Machine IR
                      │
                      ▼
                AXASSEMBLER
                      │
                      ▼
                  AXOBJECT
                      │
                      ▼
                  AXLINKER
                      │
                      ▼
                  AXBINARY
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        PE64        ELF64      Mach-O
          │           │           │
        .exe        Linux      macOS/iOS

                      +
                    WASM
```

Điểm rất quan trọng là **Axiom giờ đã có thể đi từ source → machine code → object → link → native executable mà không cần compiler/assembler/linker bên thứ ba trong production architecture**.

---

# BOOTSTRAP-776 — AXLOADER

Task kế tiếp:

**Native Executable Loader, PE64/ELF64/Mach-O/WASM Image Mapping, Relocation, Imports, TLS, Memory Permissions, Entry Transfer & Process Image Activation Runtime 5.0**

Nó sẽ hoàn thiện boundary:

```text
AXBINARY
    ↓
   file
    ↓
AXLOADER
    ↓
memory image
    ↓
AXPROCESS
    ↓
entry point
```

và đặc biệt phải giữ ranh giới rất rõ giữa **binary construction** của `AXBINARY` và **actual process image activation** của `AXLOADER`.