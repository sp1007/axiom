# BOOTSTRAP-773 — AXOBJECT

**Title:** Native Object Artifact Model, COFF/PE64, ELF64, Mach-O, WASM Object Representation, Sections, Symbols, Relocations, Debug/Unwind Metadata & Cross-Platform Object ABI 5.0  
**Namespace:** `AXOBJECT`  
**Phase:** Axiom Native Toolchain / Binary Artifact Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXOBJECT` định nghĩa **object artifact model trung gian chuẩn của Axiom**.

Nó nằm giữa compiler/assembler và linker:

```text
AXSOURCE
   ↓
AXCOMPILER
   ↓
AXIR / machine lowering
   ↓
AXASSEMBLER
   ↓
┌──────────────────┐
│    AXOBJECT      │
│                  │
│ sections         │
│ symbols          │
│ relocations      │
│ metadata         │
│ debug            │
│ unwind           │
└────────┬─────────┘
         ↓
     AXLINKER
         ↓
 PE64 / ELF / Mach-O / WASM
```

Mục tiêu quan trọng nhất:

> **Compiler và linker không được kết nối bằng một internal data structure bí mật.**

Thay vào đó chúng giao tiếp qua một object contract ổn định.

---

# 2. Tại sao cần AXOBJECT?

Nếu không có lớp này:

```text
AXCOMPILER → AXLINKER
```

sẽ tạo coupling rất lớn.

Compiler phải biết:

- linker internals;
- section layout;
- symbol database;
- relocation implementation;
- từng binary format.

Với AXOBJECT:

```text
AXCOMPILER
    ↓
Object Artifact
    ↓
AXLINKER
```

Compiler chỉ cần tạo object hợp lệ.

Linker chỉ cần consume object.

---

# 3. Nguyên tắc kiến trúc

AXOBJECT phải:

1. compact;
2. binary-friendly;
3. deterministic;
4. zero-runtime;
5. architecture-aware;
6. ABI-aware;
7. extensible;
8. memory-efficient;
9. mmap-friendly;
10. streamable;
11. cache-friendly;
12. security-conscious.

---

# 4. Boundary

### AXOBJECT sở hữu

- object container;
- section model;
- symbol model;
- relocation model;
- string table;
- metadata;
- debug references;
- unwind references;
- target identity;
- ABI identity;
- object validation;
- object serialization;
- object inspection.

### AXOBJECT không sở hữu

```text
AXCOMPILER
→ source semantics

AXASSEMBLER
→ instruction encoding

AXLINKER
→ global symbol resolution/layout

AXTOOLCHAIN
→ target/toolchain identity authority

AXBUILD
→ build graph

AXPACKAGE
→ distribution

AXCRYPTO
→ signing primitives
```

---

# 5. Object artifact

Canonical abstraction:

```text
object_artifact {
    format
    version
    target
    abi
    flags
    sections[]
    symbols[]
    relocations[]
    strings
    metadata[]
}
```

---

# 6. Object identity

Mỗi object có:

```text
object_id
content_hash
format
format_version
target_id
abi_id
```

`object_id` không thay thế content hash.

---

# 7. Object hash

Canonical content hash phải bỏ qua các trường không deterministic như:

```text
build timestamp
temporary path
machine-local state
```

nếu reproducible mode được bật.

---

# 8. Object format

Internal enum:

```text
AXOBJECT_NATIVE
COFF
ELF
MACHO
WASM
FOREIGN
```

---

# 9. Native AXOBJECT format

Axiom nên có **native object container riêng**.

Ví dụ:

```text
AXO
```

Mục đích:

```text
AXCOMPILER
 ↓
.axo
 ↓
AXLINKER
```

trong toolchain nội bộ.

---

# 10. Tại sao không dùng trực tiếp ELF/COFF?

Có thể, nhưng native AXO có lợi thế:

- metadata phong phú;
- generic relocation;
- compiler IR metadata;
- AI metadata;
- ABI metadata;
- deterministic cache;
- không bị giới hạn bởi format legacy.

Sau đó AXLINKER chuyển:

```text
AXO
 ↓
PE/ELF/Mach-O/WASM
```

---

# 11. AXO không phải executable

`.axo` chỉ là intermediate object artifact.

Không chạy trực tiếp.

---

# 12. AXO header

Conceptual:

```text
AXOHeader {
    magic
    version
    flags
    target_id
    abi_id
    section_count
    symbol_count
    relocation_count
    metadata_count
    table_offsets
}
```

---

# 13. Magic

Ví dụ:

```text
AXO\0
```

Magic chỉ là nhận diện format, không phải security boundary.

---

# 14. Version

Object version:

```text
major
minor
```

---

# 15. Compatibility

### Major khác

→ incompatible.

### Minor mới hơn

Có thể đọc nếu reader hỗ trợ required feature subset.

---

# 16. Endianness

AXO canonical representation:

```text
little-endian
```

cho baseline.

Target object data vẫn có target endianness metadata.

---

# 17. Integer encoding

Fixed-width integer fields cho header/index.

Không dùng variable-length encoding ở các hot random-access tables nếu làm mất khả năng mmap/index trực tiếp.

---

# 18. Object sections

Canonical:

```text
section {
    id
    name
    type
    flags
    alignment
    file_offset
    file_size
    memory_size
    virtual_address
    data
}
```

---

# 19. Section ID

Mỗi section có:

```text
SectionId : u32
```

Ổn định trong object.

---

# 20. Section types

```text
CODE
CONST
DATA
BSS
TLS_DATA
TLS_BSS
METADATA
DEBUG
UNWIND
LINKER_DATA
```

---

# 21. Section flags

```text
ALLOC
READ
WRITE
EXEC
TLS
MERGE
DISCARD
DEBUG
NOLOAD
```

---

# 22. Alignment

Section có explicit:

```text
alignment : u64
```

---

# 23. Section size

AXOBJECT phân biệt:

```text
file_size
memory_size
```

để biểu diễn BSS/zero-fill.

---

# 24. BSS

BSS không cần lưu zero bytes.

```text
file_size = 0
memory_size > 0
```

---

# 25. Section content

Section có thể:

```text
INLINE
EXTERNAL
ZERO_FILL
COMPRESSED
```

Native linker có thể chỉ support INLINE + ZERO_FILL ban đầu.

---

# 26. Section compression

Compression không thuộc core object semantics.

Có thể là optional storage optimization.

---

# 27. Merge sections

Section có:

```text
merge_key
```

nếu compiler muốn linker merge compatible entities.

---

# 28. Unique sections

Compiler có thể yêu cầu:

```text
unique_section = true
```

để tránh merge.

---

# 29. COMDAT-like groups

AXOBJECT hỗ trợ:

```text
group {
    group_id
    selection
    members[]
}
```

---

# 30. Group selection

Baseline:

```text
ANY
EXACT_MATCH
LARGEST
NO_DUPLICATES
ASSOCIATIVE
```

Target backend map sang semantics phù hợp.

---

# 31. Symbol

Canonical:

```text
symbol {
    id
    name
    binding
    visibility
    type
    section
    value
    size
    flags
}
```

---

# 32. Symbol binding

```text
LOCAL
GLOBAL
WEAK
IMPORT
EXPORT
```

---

# 33. Symbol type

```text
NOTYPE
FUNCTION
OBJECT
SECTION
TLS
ABSOLUTE
```

---

# 34. Symbol section

Symbol có thể:

```text
section_id
```

hoặc:

```text
ABSOLUTE
UNDEFINED
COMMON
```

---

# 35. Symbol value

Value là offset tương đối với section nếu symbol section-relative.

---

# 36. Symbol size

Symbol size dùng cho:

- debug;
- diagnostics;
- binary inspection;
- size reports;
- linker optimization.

Không nhất thiết có semantic effect.

---

# 37. Symbol visibility

```text
DEFAULT
HIDDEN
PROTECTED
PRIVATE
```

Target backend map theo capability.

---

# 38. Symbol flags

Có thể bao gồm:

```text
ADDRESS_SIGNIFICANT
NO_ICF
RETAIN
NO_STRIP
HOT
COLD
```

---

# 39. Undefined symbol

```text
section = UNDEFINED
```

---

# 40. Absolute symbol

```text
section = ABSOLUTE
```

---

# 41. Symbol aliases

AXOBJECT có thể encode:

```text
alias_symbol → target_symbol
```

---

# 42. Symbol version

Optional:

```text
symbol_version_id
```

ELF backend có thể sử dụng.

---

# 43. String table

Tất cả:

- symbol names;
- section names;
- metadata names;

dùng canonical string table.

---

# 44. String deduplication

Tên giống nhau chỉ lưu một lần.

---

# 45. String offsets

Tables sử dụng:

```text
StringOffset : u32/u64
```

tùy object size.

---

# 46. Relocation

Canonical:

```text
relocation {
    section
    offset
    type
    symbol
    addend
    flags
}
```

---

# 47. Relocation semantics

AXOBJECT định nghĩa relocation bằng **semantic class**, không chỉ numeric code.

Ví dụ:

```text
ABS
PC_REL
GOT
PLT
TLS
SECTION
HIGH
LOW
BRANCH
PAGE
PAGEOFF
WASM_INDEX
```

---

# 48. Target relocation

Mỗi target backend ánh xạ semantic relocation:

```text
AXReloc
 ↓
x86_64 relocation
```

hoặc:

```text
AXReloc
 ↓
AArch64 relocation
```

---

# 49. Relocation width

Explicit:

```text
width = 8
```

hoặc:

```text
width = 16/32/64
```

tùy instruction/field.

---

# 50. Signedness

Relocation definition phải biết:

```text
signed
unsigned
pc-relative
```

để detect overflow chính xác.

---

# 51. Addend

AXOBJECT hỗ trợ explicit addend.

Không phụ thuộc vào bytes trong instruction nếu target format cho phép.

---

# 52. Place

Relocation evaluation cần biết:

```text
P = address(section) + offset
```

---

# 53. Symbol value

Generic:

```text
S = final symbol address
```

---

# 54. Common formulas

### Absolute

```text
S + A
```

### PC-relative

```text
S + A - P
```

### Image-relative

```text
S + A - image_base
```

---

# 55. Relocation overflow

AXOBJECT metadata cung cấp width/range.

AXLINKER phải reject overflow.

---

# 56. Relaxation

Relocation có thể có:

```text
relaxation_class
```

để linker biết instruction sequence có thể rút gọn.

---

# 57. Relaxation safety

Relaxation chỉ được thực hiện khi:

```text
range valid
ABI valid
instruction semantics preserved
```

---

# 58. GOT

AXOBJECT có generic relocation class:

```text
GOT
```

---

# 59. PLT

Generic:

```text
PLT
```

cho dynamic call semantics.

---

# 60. TLS

Relocation class:

```text
TLS_LOCAL
TLS_GLOBAL
TLS_MODULE
TLS_OFFSET
```

---

# 61. Thread-local data

Sections:

```text
.tdata
.tbss
```

được biểu diễn bằng:

```text
TLS_DATA
TLS_BSS
```

---

# 62. Debug metadata

AXOBJECT không định nghĩa toàn bộ DWARF.

Nó định nghĩa:

```text
debug_reference
debug_section
debug_format
```

---

# 63. Debug formats

Baseline:

```text
DWARF
PDB-compatible metadata
CodeView
AXDBG
```

AXDBG là native abstraction có thể được triển khai sau.

---

# 64. Source mapping

Compiler metadata:

```text
source_file_id
line
column
instruction_range
```

---

# 65. Build identity

Object chứa:

```text
compiler_id
compiler_version
source_revision?
```

nếu provenance mode bật.

---

# 66. Unwind metadata

AXOBJECT có:

```text
unwind_info {
    format
    section
    range
}
```

---

# 67. Windows unwind

Có thể chứa references tới:

```text
.pdata
.xdata
```

---

# 68. ELF unwind

Có thể chứa:

```text
.eh_frame
```

---

# 69. Mach-O unwind

Object representation có thể lưu target-specific unwind records.

---

# 70. Exception metadata

Nếu Axiom dùng Result/trap model mặc định, exception tables không bắt buộc.

Nhưng ABI interoperability vẫn phải hỗ trợ foreign exception/unwind metadata.

---

# 71. Compiler metadata

AXOBJECT cho phép metadata:

```text
compiler.*
```

Ví dụ:

```text
compiler.inline_hint
compiler.noinline
compiler.hot
compiler.cold
compiler.address_significant
```

---

# 72. AI metadata

Axiom có thể emit:

```text
ai.symbol_summary
ai.type_schema
ai.source_map
ai.dependency_map
ai.intent
```

Nhưng metadata này:

- không ảnh hưởng runtime semantics;
- không tự cấp quyền;
- có thể strip khỏi release binary.

---

# 73. Metadata namespace

Tên metadata phải namespace:

```text
axiom.*
compiler.*
debug.*
ai.*
platform.*
linker.*
```

---

# 74. Metadata version

Mỗi metadata schema có:

```text
namespace
name
version
payload
```

---

# 75. Unknown metadata

Reader phải có thể bỏ qua metadata không hiểu nếu metadata không mandatory.

---

# 76. Required metadata

Metadata có flag:

```text
REQUIRED
OPTIONAL
```

Unknown `REQUIRED` metadata → reject.

---

# 77. Target descriptor

Object phải record:

```text
target_id
architecture
os
environment
endianness
pointer_width
```

---

# 78. ABI descriptor

```text
abi_id
calling_convention
alignment
scalar_abi
aggregate_abi
tls_abi
unwind_abi
```

---

# 79. CPU features

Object có thể yêu cầu:

```text
SSE2
AVX2
AVX512
NEON
SVE
```

hoặc Axiom canonical feature IDs.

---

# 80. Feature compatibility

Linker phải đảm bảo tất cả objects compatible với target feature baseline.

---

# 81. Function attributes

Compiler có thể emit:

```text
function {
    calling_convention
    stack_alignment
    unwind
    hotness
    code_model
}
```

---

# 82. Calling convention

AXOBJECT không chỉ lưu symbol.

Function ABI metadata có thể specify:

```text
AX
C
SYSTEM
FAST
VECTOR
```

tùy ABI.

---

# 83. Code model

Metadata:

```text
SMALL
MEDIUM
LARGE
PIC
PIE
```

hoặc target-specific equivalent.

---

# 84. Stack requirements

Object metadata có thể declare unusual:

```text
stack_alignment
red_zone
stack_probe
```

---

# 85. Stack probing

Windows/large-stack targets có thể yêu cầu compiler/linker startup metadata.

---

# 86. Register preservation

ABI descriptor controls:

```text
caller_saved
callee_saved
special_registers
```

Không hardcode trong object reader.

---

# 87. Architecture-independent representation

Generic symbol/section/relocation model không phụ thuộc x86.

---

# 88. Architecture-specific extension

Có extension namespace:

```text
arch.x86_64.*
arch.aarch64.*
arch.wasm32.*
```

---

# 89. Foreign COFF

AXOBJECT reader phải import standard COFF objects.

---

# 90. PE/COFF separation

COFF object:

```text
COFF object
```

khác:

```text
PE executable
```

AXOBJECT giữ distinction này.

---

# 91. ELF reader

AXOBJECT có ELF reader để consume:

```text
.o
```

từ GCC/Clang/Rust hoặc toolchain khác khi ABI-compatible.

---

# 92. Mach-O object

Support:

```text
.o
```

Mach-O relocatable objects.

---

# 93. WASM object

Nếu input toolchain sử dụng WASM relocatable/custom linking model, AXOBJECT có adapter.

---

# 94. Foreign ABI marker

Object imported từ external compiler phải mark:

```text
origin = FOREIGN
```

---

# 95. Foreign object trust

Origin metadata không phải security authority.

Object vẫn được validate như untrusted data.

---

# 96. Archive integration

AXOBJECT defines archive member interface nhưng archive container chính thuộc AXLINKER/toolchain artifact layer.

---

# 97. Native archive

Axiom có thể có:

```text
.axlib
```

native archive.

---

# 98. AXLIB

Concept:

```text
AXLIB {
    header
    member_index
    members[]
    metadata
}
```

---

# 99. Archive index

Map:

```text
symbol_hash
 →
member_id
```

để lazy extraction.

---

# 100. Archive duplicate members

Duplicate object identity phải được xác định bằng member ID/content hash, không filename.

---

# 101. Object dependencies

Object metadata có thể khai báo:

```text
required_symbols
provided_symbols
required_features
```

để build/link planning nhanh hơn.

---

# 102. Interface hash

Compiler emits:

```text
interface_hash
```

---

# 103. ABI hash

Compiler emits:

```text
abi_hash
```

---

# 104. Implementation hash

Compiler emits:

```text
implementation_hash
```

---

# 105. Build fingerprint

AXOBJECT có thể lưu:

```text
build_fingerprint
```

dùng bởi AXBUILD.

---

# 106. Incremental compilation

AXBUILD có thể xác định:

```text
interface unchanged
ABI unchanged
```

→ không cần rebuild dependents.

---

# 107. Incremental linker

Object identity/hash giúp AXLINKER reuse parsed metadata.

---

# 108. Object cache

AXBUILD cache:

```text
source hash
+
compiler fingerprint
+
target
+
ABI
+
options
```

→ AXO.

---

# 109. Content addressing

AXOBJECT nên hỗ trợ:

```text
object_hash
```

làm cache key.

---

# 110. Memory mapping

AXO tables nên được layout để:

```text
mmap
 ↓
read-only access
```

mà không cần deserialize toàn bộ.

---

# 111. Zero-copy strings

String table có thể được truy cập bằng offset.

---

# 112. Zero-copy sections

Section data có thể expose:

```text
slice<byte>
```

trực tiếp từ mapped file.

---

# 113. Lazy relocation parsing

Relocation tables lớn có thể parse on-demand.

---

# 114. Lazy debug loading

Debug metadata không cần load trong release link.

---

# 115. Object inspection

CLI:

```text
axiom obj info foo.axo
axiom obj symbols foo.axo
axiom obj sections foo.axo
axiom obj relocations foo.axo
```

---

# 116. Section dump

```text
axiom obj dump-section foo.axo .text
```

---

# 117. Symbol dump

Output:

```text
address
size
binding
visibility
section
name
```

---

# 118. Relocation dump

Output:

```text
offset
type
symbol
addend
```

---

# 119. Metadata dump

Developer can inspect compiler/AI/build metadata.

---

# 120. Object validation

```text
axiom obj validate foo.axo
```

phải kiểm tra:

- header;
- offsets;
- sizes;
- tables;
- section ranges;
- symbol references;
- relocation references;
- metadata lengths;
- alignment.

---

# 121. Bounds checking

Mọi offset:

```text
offset + size <= file_size
```

phải được checked overflow-safe.

---

# 122. Integer overflow

Parser tuyệt đối không được:

```text
offset + size
```

bằng integer arithmetic unchecked.

---

# 123. Resource limits

Reader phải có:

```text
max_sections
max_symbols
max_relocations
max_metadata
max_strings
max_file_size
```

---

# 124. Malformed object

Malformed object:

```text
→ diagnostic
```

không:

```text
→ crash
```

---

# 125. Untrusted input

AXOBJECT parser không được execute:

- constructors;
- scripts;
- code;
- metadata callbacks.

---

# 126. Compression bombs

Nếu compressed object extension được hỗ trợ:

```text
compressed_size
uncompressed_size
```

phải có limits.

---

# 127. Signing

Object có thể có:

```text
signature_reference
```

nhưng signature verification thuộc AXCRYPTO/AXTRUST.

---

# 128. Integrity

Content hash có thể được verify trước khi link.

---

# 129. Trust

Object integrity ≠ object trust.

Trust decision thuộc AXTRUST/AXSECURITY.

---

# 130. Reproducibility

AXOBJECT canonical serializer phải deterministic.

---

# 131. Canonical ordering

Các bảng phải có canonical order hoặc stable IDs.

---

# 132. Symbol ordering

Internal symbol IDs có thể phụ thuộc compiler.

Canonical exported serialization phải deterministic theo configured rule.

---

# 133. Section ordering

Compiler-generated sections phải được canonicalized.

---

# 134. Metadata ordering

Metadata records sorted by:

```text
namespace
name
version
```

trong reproducible mode.

---

# 135. Padding

Padding bytes phải được zeroed.

---

# 136. Reserved fields

Reserved bytes phải:

```text
zero
```

trong canonical serialization.

---

# 137. Build timestamps

Không lưu timestamp trong canonical hash trừ khi explicitly configured.

---

# 138. Debug timestamps

Debug metadata phải áp dụng source reproducibility rules.

---

# 139. Object ABI

Native interface:

```text
AXOBJECT_ABI_1
```

---

# 140. Reader API

```text
object_open()
object_close()
object_validate()
object_header()
object_target()
object_abi()
```

---

# 141. Section API

```text
object_section_count()
object_section_get()
object_section_data()
object_section_flags()
```

---

# 142. Symbol API

```text
object_symbol_count()
object_symbol_get()
object_symbol_name()
object_symbol_section()
```

---

# 143. Relocation API

```text
object_relocation_count()
object_relocation_get()
object_relocation_type()
object_relocation_symbol()
```

---

# 144. Metadata API

```text
object_metadata_count()
object_metadata_get()
object_metadata_find()
```

---

# 145. Writer API

```text
object_create()
object_add_section()
object_add_symbol()
object_add_relocation()
object_add_metadata()
object_write()
```

---

# 146. Builder API

Compiler có thể dùng:

```text
object_builder_create()
object_builder_section()
object_builder_symbol()
object_builder_relocation()
object_builder_finalize()
```

---

# 147. Writer validation

`object_write()` không được emit invalid object.

---

# 148. Object finalization

```text
builder
 ↓
validate
 ↓
canonicalize
 ↓
hash
 ↓
serialize
```

---

# 149. Compiler integration

AXCOMPILER:

```text
typed IR
 ↓
machine lowering
 ↓
instruction encoding
 ↓
AXOBJECT builder
```

---

# 150. Assembler integration

AXASSEMBLER có thể output trực tiếp:

```text
AXOBJECT
```

thay vì bắt buộc emit native `.o`.

---

# 151. Native assembly

Pipeline:

```text
Axiom compiler
 ↓
AXOBJECT
```

---

# 152. External assembly

Pipeline:

```text
foreign assembly
 ↓
COFF/ELF/Mach-O
 ↓
AXOBJECT reader
 ↓
AXLINKER
```

---

# 153. Internal vs external object

AXOBJECT abstraction làm hai loại object tương thích ở linker boundary.

---

# 154. No third-party dependency

Native AXOBJECT reader/writer phải do Axiom implement.

External libraries chỉ là optional interoperability tools.

---

# 155. Object format conversion

Tool:

```text
axiom obj convert
```

có thể chuyển:

```text
COFF → AXO
ELF  → AXO
Mach-O → AXO
```

nếu semantics đủ để preserve.

---

# 156. Lossy conversion

Nếu foreign format có semantics không representable:

```text
conversion error
```

hoặc explicit lossy mode.

---

# 157. No silent metadata loss

Default conversion không được silently discard required metadata.

---

# 158. ABI adapter

C ABI object có thể được annotated:

```text
foreign_abi = C
```

---

# 159. Struct layout

AXOBJECT có thể record ABI-relevant layout metadata:

```text
size
alignment
field offsets
```

chỉ khi foreign ABI interoperability cần.

---

# 160. Name decoration

COFF symbol decoration được giữ nguyên ở foreign boundary.

---

# 161. Calling convention metadata

AXOBJECT phải preserve calling convention của foreign symbols.

---

# 162. Exception interoperability

Foreign exception metadata chỉ được preserve nếu target ABI hỗ trợ.

---

# 163. Global constructors

Object metadata có thể chứa initialization arrays:

```text
INIT
FINI
```

---

# 164. Initialization ordering

Linker must preserve required ordering semantics.

---

# 165. Initialization cycles

Compiler/runtime policy determines semantics; object model only represents dependencies/order metadata.

---

# 166. TLS initialization

TLS object sections and relocation metadata are preserved.

---

# 167. Resource sections

Native application resources có thể represented:

```text
RESOURCE
```

nhưng resource format semantics thuộc platform layer.

---

# 168. Windows resources

PE backend maps resource sections to PE resource directory.

---

# 169. Apple resources

Mach-O/resource bundling remains build/package boundary.

---

# 170. WASM metadata

WASM custom sections can carry AXOBJECT metadata where appropriate.

---

# 171. Object-level capabilities

Object metadata may declare:

```text
required_capabilities
```

nhưng linker chỉ propagates.

---

# 172. Compiler provenance

Object may contain:

```text
compiler_build_id
```

để diagnostics/reproducibility.

---

# 173. AI provenance

AI-generated source/metadata có thể be recorded, nhưng không ảnh hưởng code semantics.

---

# 174. AI compiler metadata

Compiler có thể emit:

```text
ai.symbol
ai.type
ai.callgraph
ai.source_region
```

để IDE/agent tools.

---

# 175. Metadata stripping

Release linker có thể strip AI/compiler-private metadata.

---

# 176. Debug stripping

Debug sections có thể được externalized.

---

# 177. Object size

Object format phải ưu tiên:

```text
small tables
shared strings
zero-fill
compact IDs
```

---

# 178. Object loading speed

Hot path:

```text
header
sections
symbols
relocations
```

phải có direct offsets.

---

# 179. Object cache locality

Frequently accessed metadata nên nằm gần nhau.

---

# 180. Parser architecture

```text
Reader
 ↓
HeaderView
 ↓
SectionView
 ↓
SymbolView
 ↓
RelocationView
```

không cần materialize toàn bộ object graph.

---

# 181. Immutable view

Mapped object được expose read-only.

---

# 182. Mutable builder

Writer sử dụng riêng mutable builder.

---

# 183. No GC

AXOBJECT implementation không yêu cầu garbage collector.

---

# 184. Allocation model

Builder dùng arena/region allocation.

Reader dùng:

```text
mmap
+
stack/local metadata
```

---

# 185. Thread safety

Immutable `ObjectView` có thể được đọc concurrent.

Builder mặc định single-owner.

---

# 186. Parallel object inspection

Multiple ObjectViews có thể process parallel.

---

# 187. Cache concurrency

Object cache phải hỗ trợ concurrent readers.

---

# 188. Atomic cache publication

Object cache entry:

```text
write temp
 ↓
validate
 ↓
atomic rename/publish
```

---

# 189. Corrupt cache

Corrupt object cache entry bị invalidate, không làm build fail nếu source/object có thể regenerate.

---

# 190. Object dependency graph

Metadata hỗ trợ AXBUILD xây graph nhanh:

```text
object
 ↓
provided symbols
required symbols
```

---

# 191. Link-time diagnostics

AXLINKER có thể trace:

```text
symbol foo
defined by object A
referenced by object B
```

nhờ AXOBJECT IDs.

---

# 192. Source diagnostics

Symbol metadata có thể link back tới:

```text
source_file
line
column
```

---

# 193. Machine code diagnostics

AXOBJECT giữ:

```text
machine_code_range
source_range
```

để disassembly/debug.

---

# 194. Instruction boundaries

Optional metadata:

```text
instruction_map
```

---

# 195. Code alignment

Function alignment được represented bằng section/symbol alignment metadata.

---

# 196. Function sections

Compiler có thể tạo:

```text
.text.foo
.text.bar
```

để linker section GC/ICF.

---

# 197. Data sections

Tương tự:

```text
.rodata.foo
.data.foo
```

---

# 198. Constant pooling

Compiler có thể emit constants riêng; linker có thể merge.

---

# 199. Address significance

Object metadata phải cho linker biết address có observable significance hay không.

---

# 200. Zero-cost principle

AXOBJECT tồn tại hoàn toàn ở compile/link time.

**Không có AXOBJECT runtime.**

---

# 201. Native ABI stability

`AXOBJECT_ABI_1` phải versioned độc lập với:

```text
AXLINKER_ABI_1
AXCOMPILER_ABI_1
AXTOOLCHAIN_ABI_1
```

---

# 202. ABI evolution

Minor extension:

```text
AXOBJECT_ABI_1.x
```

không break existing readers nếu optional.

Major:

```text
AXOBJECT_ABI_2
```

khi binary contract không còn compatible.

---

# 203. Object compatibility matrix

Compiler/linker phải kiểm tra:

```text
object ABI
target ABI
linker ABI
toolchain capabilities
```

trước link.

---

# 204. Feature negotiation

Object có thể yêu cầu:

```text
required_linker_features[]
```

---

# 205. Unsupported feature

Nếu required feature không được linker hỗ trợ:

```text
LINK_UNSUPPORTED_OBJECT_FEATURE
```

---

# 206. Object capability query

```text
object_required_features()
object_provided_features()
```

---

# 207. Versioned metadata

Mọi extension phải versioned.

Không parse metadata theo heuristic.

---

# 208. Error model

Canonical:

```text
OBJECT_INVALID
OBJECT_BAD_MAGIC
OBJECT_UNSUPPORTED_VERSION
OBJECT_TRUNCATED
OBJECT_OUT_OF_RANGE
OBJECT_OVERFLOW
OBJECT_INVALID_SECTION
OBJECT_INVALID_SYMBOL
OBJECT_INVALID_RELOCATION
OBJECT_INVALID_METADATA
OBJECT_TARGET_MISMATCH
OBJECT_ABI_MISMATCH
OBJECT_FEATURE_UNSUPPORTED
OBJECT_LIMIT_EXCEEDED
OBJECT_INTEGRITY_FAILURE
OBJECT_FORMAT_UNSUPPORTED
```

---

# 209. Diagnostics severity

```text
INFO
WARNING
ERROR
FATAL
```

---

# 210. Error localization

Error phải chỉ rõ:

```text
object
offset
table
entry
field
```

nếu parse failure.

---

# 211. Reproducible test

Test:

```text
same compiler
same source
same config
```

→ same AXO hash.

---

# 212. Cross-machine test

Build trên hai máy:

```text
Windows
Linux
```

cùng target/toolchain snapshot phải produce same canonical object.

---

# 213. Cross-process test

Parallel compiler workers phải produce identical objects.

---

# 214. Round-trip test

```text
AXO
 ↓ read
object model
 ↓ write
AXO
```

phải preserve canonical semantics.

---

# 215. Foreign round-trip

```text
ELF
 ↓ AXOBJECT reader
AXO
 ↓ AXLINKER
ELF
```

phải preserve executable-relevant semantics trong supported subset.

---

# 216. Relocation golden tests

Mỗi relocation type có test:

```text
symbol address
place
addend
expected bytes
overflow
```

---

# 217. Fuzz testing

Fuzz:

- header;
- section table;
- symbols;
- relocations;
- metadata;
- string offsets.

---

# 218. Differential tests

Compare native reader against established parsers during development.

Không phụ thuộc chúng trong production.

---

# 219. Security tests

Test:

```text
truncated file
integer overflow
huge count
recursive metadata
invalid offset
overlapping tables
malformed relocation
```

---

# 220. Resource exhaustion

Fuzzer không được làm AXOBJECT allocate unbounded memory.

---

# 221. Deterministic diagnostics

Same malformed object should produce deterministic primary error.

---

# 222. Linker integration test

Canonical:

```text
AXCOMPILER
 ↓
AXOBJECT
 ↓
AXLINKER
 ↓
binary
 ↓
execute
```

---

# 223. PE64 test

Build:

```text
hello.exe
```

validate:

```text
PE header
entry
.text
.rdata
.data
imports
```

---

# 224. ELF test

Build:

```text
hello
```

validate:

```text
ELF header
segments
entry
symbols
relocations
```

---

# 225. Mach-O test

Validate:

```text
Mach header
load commands
segments
entry/start
symbols
```

---

# 226. WASM test

Validate:

```text
type
function
code
data
imports
exports
```

---

# 227. Static library test

```text
A.axo
B.axo
 ↓
libA.axlib
```

then link consumer.

---

# 228. Dead stripping test

Unused object/function phải biến mất khi enabled.

---

# 229. Weak symbol test

Test:

```text
weak
+
strong
```

resolution.

---

# 230. Duplicate symbol test

Hai strong symbols → deterministic failure.

---

# 231. ABI mismatch test

Object x86-64/C ABI incompatible với Axiom ABI → diagnostic.

---

# 232. TLS test

Compile thread-local variable and verify target-specific relocation/layout.

---

# 233. Debug test

Source line → machine instruction mapping phải survive link.

---

# 234. Unwind test

Stack unwinding phải locate function boundaries sau linking.

---

# 235. Reproducibility test

Compare:

```text
SHA-256(object1)
SHA-256(object2)
```

from identical inputs.

---

# 236. Incremental test

Change implementation only:

```text
interface hash unchanged
ABI hash unchanged
```

→ dependent object remains reusable.

---

# 237. Metadata test

Unknown optional metadata must be ignored.

Unknown required metadata must fail.

---

# 238. Security invariant

AXOBJECT parser must never treat metadata as executable instructions.

---

# 239. Performance target

For large projects:

- mmap-friendly;
- no mandatory full-file copy;
- no mandatory object graph allocation;
- parallel object reading;
- compact symbol representation;
- lazy debug loading.

---

# 240. Formal invariants

```text
OBJECT-INV-01
Mọi object phải có valid magic/version.

OBJECT-INV-02
Object version không được silently reinterpret.

OBJECT-INV-03
Mọi table offset phải nằm trong file bounds.

OBJECT-INV-04
Mọi size arithmetic phải overflow-safe.

OBJECT-INV-05
Section references phải reference SectionId hợp lệ.

OBJECT-INV-06
Symbol references phải reference SymbolId hợp lệ.

OBJECT-INV-07
Relocation references phải reference section/symbol hợp lệ.

OBJECT-INV-08
Unknown required metadata phải reject.

OBJECT-INV-09
Unknown optional metadata phải có thể bỏ qua.

OBJECT-INV-10
Object target phải được xác định explicit.

OBJECT-INV-11
Object ABI phải được xác định explicit.

OBJECT-INV-12
Object architecture không được suy luận mơ hồ từ filename.

OBJECT-INV-13
Section alignment phải được validate.

OBJECT-INV-14
Section file range không được vượt file.

OBJECT-INV-15
Section memory size phải hợp lệ.

OBJECT-INV-16
BSS/zero-fill không được yêu cầu lưu toàn bộ zero bytes.

OBJECT-INV-17
Symbol section references phải consistent với symbol state.

OBJECT-INV-18
Undefined symbols phải được biểu diễn explicit.

OBJECT-INV-19
Absolute symbols phải được biểu diễn explicit.

OBJECT-INV-20
Symbol binding phải preserve ABI semantics.

OBJECT-INV-21
Symbol visibility phải preserve ABI semantics.

OBJECT-INV-22
Relocation type phải có semantic definition.

OBJECT-INV-23
Relocation width/range phải được xác định.

OBJECT-INV-24
Relocation addend semantics phải explicit.

OBJECT-INV-25
Relocation overflow không được silently truncate.

OBJECT-INV-26
TLS relocation phải preserve target ABI semantics.

OBJECT-INV-27
Debug metadata không được thay đổi executable semantics.

OBJECT-INV-28
Unwind metadata phải remain associated với code ranges hợp lệ.

OBJECT-INV-29
Object parser không được execute embedded code.

OBJECT-INV-30
Object parser phải enforce resource limits.

OBJECT-INV-31
Canonical serialization phải deterministic.

OBJECT-INV-32
Padding/reserved bytes trong canonical mode phải deterministic.

OBJECT-INV-33
Canonical object hash không phụ thuộc machine-local nondeterminism.

OBJECT-INV-34
Immutable object views phải safe cho concurrent readers.

OBJECT-INV-35
Object cache entry phải integrity-check trước reuse.

OBJECT-INV-36
Foreign object không được tự động trở thành trusted object.

OBJECT-INV-37
AXOBJECT không được cấp security authority.

OBJECT-INV-38
AXOBJECT phải support native AXO và required foreign object formats.

OBJECT-INV-39
Native object ABI phải expose `AXOBJECT_ABI_1`.

OBJECT-INV-40
AXOBJECT chỉ định nghĩa artifact contract; compiler semantics, instruction encoding và global linking semantics thuộc các subsystem tương ứng.
```

---

# 241. Definition of Done

`AXOBJECT 5.0` được freeze khi có:

- native AXO;
- object header;
- target descriptor;
- ABI descriptor;
- sections;
- section flags;
- alignment;
- BSS;
- symbols;
- bindings;
- visibility;
- aliases;
- versioned symbols;
- relocations;
- relocation formulas;
- addends;
- overflow metadata;
- relaxation metadata;
- GOT/PLT semantics;
- TLS semantics;
- COMDAT/group semantics;
- debug references;
- unwind references;
- compiler metadata;
- AI metadata;
- interface hash;
- ABI hash;
- implementation hash;
- build fingerprint;
- foreign COFF;
- ELF;
- Mach-O;
- WASM object adapters;
- deterministic serialization;
- content hashing;
- mmap/zero-copy reader;
- lazy loading;
- object builder;
- object validation;
- resource limits;
- fuzzing;
- cache integration;
- incremental-build integration;
- linker integration;
- PE64/ELF/Mach-O/WASM tests;
- native ABI `AXOBJECT_ABI_1`;
- 40 invariants.

**AXOBJECT 5.0 → FROZEN.**

---

# BOOTSTRAP-774 — AXASSEMBLER

Task tiếp theo sẽ khóa lớp còn thiếu trong chuỗi native binary:

```text
AXCOMPILER
    ↓
AXOBJECT
    ↑
AXASSEMBLER
    ↓
AXLINKER
```

**BOOTSTRAP-774 — AXASSEMBLER: Native Machine Instruction Encoder, Register/Instruction Model, Assembly Parser, Relocation Generation, ISA Backends, Inline Assembly & Deterministic Machine-Code Emission Runtime 5.0**

Đây là task sẽ đặc biệt quan trọng đối với mục tiêu của Axiom là **không phụ thuộc assembler bên ngoài** và có thể trực tiếp tạo machine code cho x86-64/PE64, AArch64 và WASM.