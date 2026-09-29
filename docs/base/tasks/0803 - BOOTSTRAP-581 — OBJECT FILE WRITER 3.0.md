# BOOTSTRAP-581 — OBJECT FILE WRITER 3.0
## ELF64, PE/COFF, MACH-O, WASM MODULE, SECTION/SYMBOL/RELOCATION EMISSION, DEBUG/UNWIND/RESOURCE SECTIONS, TLS, COMDAT, LINKAGE & DETERMINISTIC OBJECT GENERATION

**Trạng thái: COMPLETED / LOCKED**

`581` định nghĩa tầng biến output của `580` thành **object/module artifact hoàn chỉnh**. Object writer không sửa Machine IR và không thực hiện optimization; nhiệm vụ duy nhất là đóng gói bytes, symbols, relocations, metadata và section layout theo từng object format.

```text id="o581arch"
Final Machine Bytes
        │
        ├── Code
        ├── RO Data
        ├── Data
        ├── BSS
        ├── TLS
        ├── Debug
        ├── Unwind
        └── Axiom Metadata
        │
        ▼
  Object Model
        │
        ├──────────┬───────────┬───────────┐
        ▼          ▼           ▼           ▼
      ELF64     PE/COFF      Mach-O      WASM
        │          │           │           │
        └──────────┴───────────┴───────────┘
                   ▼
           Deterministic Artifact
                   │
                   ▼
             Linker / Runtime
```

---

## 581.1. Object Writer boundary

Input:

```text
EncodedSections
Symbols
Relocations
DebugInfo
UnwindInfo
TLSInfo
ResourceInfo
TargetMetadata
```

Output:

```text
ObjectArtifact
```

---

## 581.2. Object model độc lập format

Axiom phải có intermediate object model:

```text id="objmodel"
Object
 ├── Header
 ├── Sections[]
 ├── Symbols[]
 ├── Relocations[]
 ├── COMDATGroups[]
 ├── Imports[]
 ├── Exports[]
 ├── TLS
 ├── Debug
 ├── Unwind
 └── Metadata
```

Object writer của ELF/PE/Mach-O chỉ serialize model này.

---

## 581.3. Không để target format leak vào backend

Machine encoder không được biết chi tiết ELF section index hay PE RVA.

---

## 581.4. Section identity

Mỗi section có stable identity:

```text
SectionId
Name
Kind
Flags
Alignment
Content
```

---

## 581.5. Section kinds

Canonical kinds:

```text
CODE
RODATA
DATA
BSS
TLS_DATA
TLS_BSS
UNWIND
DEBUG
RESOURCE
METADATA
LINKER_METADATA
```

---

## 581.6. Section flags

Flags độc lập:

```text
ALLOC
EXEC
WRITE
READONLY
TLS
DEBUG
MERGE
STRINGS
DISCARDABLE
```

Format adapter chuyển chúng thành format-specific flags.

---

## 581.7. Section alignment

Alignment là power-of-two hoặc target-defined legal value.

---

## 581.8. Empty sections

Empty sections có thể bị loại bỏ nếu format không yêu cầu chúng.

---

## 581.9. Section ordering

Canonical ordering phải deterministic.

Ví dụ:

```text
text
rodata
data
bss
tls
unwind
debug
metadata
```

Target format có thể override ordering nhưng phải deterministic.

---

## 581.10. Function sections

Function có thể nằm trong section riêng:

```text
.text.foo
.text.bar
```

để hỗ trợ section GC/linker optimization.

---

## 581.11. Data sections

Data tương tự có thể được split theo symbol/object identity.

---

## 581.12. Mergeable data

String/constant sections có thể khai báo mergeability.

---

## 581.13. COMDAT

Axiom object model phải biểu diễn:

```text
COMDAT {
    key
    selection
    members
}
```

---

## 581.14. COMDAT identity

COMDAT key phải deterministic và collision-resistant.

---

## 581.15. Weak linkage

Weak symbols được biểu diễn rõ ràng, không biến thành undefined hard failure ở object stage.

---

## 581.16. Symbol model

```text id="sym581"
Symbol {
    id
    name
    binding
    visibility
    type
    section
    offset
    size
    value
    linkage
}
```

---

## 581.17. Symbol binding

Support:

```text
LOCAL
GLOBAL
WEAK
IMPORT
EXPORT
```

---

## 581.18. Symbol type

Ít nhất:

```text
FUNCTION
OBJECT
SECTION
TLS
ABSOLUTE
NOTYPE
```

---

## 581.19. Symbol visibility

Canonical:

```text
DEFAULT
HIDDEN
PROTECTED
INTERNAL
```

nếu target format hỗ trợ.

---

## 581.20. Symbol size

Function/object size phải được ghi khi format hỗ trợ.

---

## 581.21. Undefined symbol

Undefined external symbol:

```text
section = UNDEFINED
```

---

## 581.22. Absolute symbol

Absolute symbol không thuộc section.

---

## 581.23. Section symbol

Object writer có thể tạo section symbols khi target format cần.

---

## 581.24. Symbol aliases

Aliases phải giữ cùng canonical symbol target.

---

## 581.25. Symbol version

Object model có thể biểu diễn symbol version metadata.

---

# ELF64

## 581.26. ELF header

ELF writer phải tạo chính xác:

```text
ELF identification
class
endianness
version
OS ABI
type
machine
entry metadata
```

---

## 581.27. ELF machine

Target `x86-64` → appropriate ELF machine ID.

Target `AArch64` → appropriate ELF machine ID.

---

## 581.28. ELF relocatable

Object `.o` được tạo với ELF relocatable type.

---

## 581.29. ELF sections

Writer phải hỗ trợ:

```text
.text
.rodata
.data
.bss
.tdata
.tbss
.eh_frame
.debug_*
.symtab
.strtab
.rela.*
```

khi cần.

---

## 581.30. ELF section header

Section header fields phải match section model.

---

## 581.31. ELF section flags

Canonical object flags được map thành `SHF_*`.

---

## 581.32. ELF section type

Writer phải chọn đúng:

```text
PROGBITS
NOBITS
SYMTAB
STRTAB
RELA
NOTE
```

và các type cần thiết.

---

## 581.33. ELF BSS

BSS không lưu zero bytes trong file.

---

## 581.34. ELF TLS

TLS sections map tới:

```text
.tdata
.tbss
```

với TLS section flags.

---

## 581.35. ELF relocations

Axiom phải hỗ trợ relocation kinds cần thiết cho từng target ABI.

---

## 581.36. ELF RELA

Nếu target relocation ABI sử dụng addend explicit, writer dùng RELA.

---

## 581.37. Relocation symbol index

Relocation symbol index phải trỏ đúng ELF symbol.

---

## 581.38. Relocation section link

Relocation section phải link đúng target section và symbol table.

---

## 581.39. Relocation ordering

Canonical:

```text
section offset
relocation type
symbol
addend
```

---

## 581.40. ELF string tables

String table phải deduplicate strings deterministic.

---

## 581.41. ELF symbol table

`st_name`, `st_info`, `st_other`, `st_shndx`, `st_value`, `st_size` phải được generate chính xác.

---

## 581.42. ELF local/global ordering

ELF symbol ordering phải thỏa invariant local symbols trước global symbols khi format yêu cầu.

---

## 581.43. ELF COMDAT

COMDAT được biểu diễn bằng section groups.

---

## 581.44. ELF section groups

Group signature phải map tới canonical COMDAT key.

---

## 581.45. ELF notes

Target/toolchain metadata có thể dùng NOTE sections.

---

## 581.46. ELF build identity

Build ID nếu enabled phải được tính từ deterministic artifact identity.

---

## 581.47. ELF debug

DWARF sections từ debug subsystem được đưa vào object mà không bị object writer diễn giải semantic.

---

# PE/COFF

## 581.48. COFF header

PE/COFF writer phải tạo machine, section count, timestamp policy, symbol table metadata phù hợp.

---

## 581.49. Deterministic timestamp

Deterministic mode không được dùng wall-clock timestamp.

---

## 581.50. COFF sections

Support:

```text
.text
.rdata
.data
.bss
.tls
.pdata
.xdata
.debug*
```

khi target cần.

---

## 581.51. Section characteristics

Map:

```text
READ
WRITE
EXECUTE
CODE
INITIALIZED_DATA
UNINITIALIZED_DATA
```

---

## 581.52. COFF relocation

Relocation type được map từ canonical Axiom relocation.

---

## 581.53. COFF symbol table

Symbols phải có:

```text
name
value
section
type
storage class
aux records
```

---

## 581.54. Long symbol names

Symbol names vượt inline-name capacity phải dùng string table.

---

## 581.55. COFF COMDAT

COMDAT selection phải map tới COFF section characteristics/auxiliary symbol metadata.

---

## 581.56. Weak externals

Weak external semantics phải được biểu diễn bằng COFF-compatible auxiliary records.

---

## 581.57. PE executable

PE executable emission thuộc linker/image writer; object writer chỉ cần tạo COFF-compatible input.

---

## 581.58. Windows unwind

`.pdata` / `.xdata` metadata được emit từ `440/579`.

---

## 581.59. TLS COFF

TLS section/relocation metadata phải match Windows TLS model.

---

# MACH-O

## 581.60. Mach-O header

Writer phải tạo:

```text
CPU type
CPU subtype
file type
load-command count
load-command size
flags
```

---

## 581.61. Mach-O sections

Canonical mappings gồm:

```text
__TEXT,__text
__TEXT,__const
__DATA,__data
__DATA,__bss
__DATA,__thread_data
__DATA,__thread_bss
```

khi cần.

---

## 581.62. Segment model

Section được group thành segments theo target policy.

---

## 581.63. Segment permissions

Executable segment:

```text
R-X
```

Data:

```text
RW-
```

Readonly:

```text
R--
```

trừ trường hợp target-specific khác.

---

## 581.64. Mach-O symbols

Support:

```text
local
external
undefined
private external
```

theo target requirement.

---

## 581.65. Mach-O string table

String offsets phải deterministic.

---

## 581.66. Mach-O relocations

Writer map canonical relocations thành Mach-O relocation entries.

---

## 581.67. External relocation

External relocation phải preserve symbol identity.

---

## 581.68. Local relocation

Local relocation có thể resolve sớm nếu legal.

---

## 581.69. GOT/stubs

Mach-O object model phải biểu diễn các symbol/stub requirements cần linker xử lý.

---

## 581.70. Thread-local storage

TLS sections và relocations phải match Mach-O TLS ABI.

---

## 581.71. Unwind

Mach-O unwind metadata phải preserve range/encoding information từ backend.

---

# WASM MODULE

## 581.72. WASM không phải object truyền thống

WASM artifact là module có index spaces và structured sections.

---

## 581.73. Type section

Function signatures phải được canonicalize/deduplicate.

---

## 581.74. Import section

External functions/globals/memory/table phải được emit deterministically.

---

## 581.75. Function section

Function declarations phải match code body ordering.

---

## 581.76. Table section

Table definitions phải match indirect-call requirements.

---

## 581.77. Memory section

Memory limits/flags phải được kiểm tra target policy.

---

## 581.78. Global section

Globals được encode với correct initializer expressions.

---

## 581.79. Export section

Exports phải được canonicalize.

---

## 581.80. Element section

Function-table initialization phải preserve indices.

---

## 581.81. Code section

Mỗi function body:

```text
locals
instructions
end
```

---

## 581.82. Data section

Static data phải preserve alignment/offset initialization.

---

## 581.83. Custom section

Axiom metadata/debug information có thể nằm trong custom sections.

---

## 581.84. WASM name section

Optional debug/name information được generate deterministic.

---

# Relocations

## 581.85. Canonical relocation

```text id="rel581"
Relocation {
    section
    offset
    kind
    symbol
    addend
    width
    pc_base
}
```

---

## 581.86. Relocation ownership

Encoder xác định field semantics; object writer serialize; linker resolve.

---

## 581.87. No relocation invention

Object writer không tự tạo relocation semantic mới.

---

## 581.88. Relocation bounds

Every relocation field phải nằm trong section bounds.

---

## 581.89. Relocation width

Width phải match target format relocation ABI.

---

## 581.90. Relocation expression

Canonical expression:

```text
S + A
S + A - P
```

và target-defined variants.

---

## 581.91. PC value

`P` phải được xác định chính xác theo relocation ABI.

---

## 581.92. Relocation overflow

Object writer không được silently truncate relocation values.

---

# Debug / Unwind / Metadata

## 581.93. Debug opacity

Object writer không sửa DWARF/CodeView semantics.

---

## 581.94. Debug sections

Debug emitter cung cấp raw section payload + metadata.

---

## 581.95. Source mapping

Machine offsets phải map đúng source location.

---

## 581.96. Unwind sections

Unwind subsystem cung cấp target-specific section payload.

---

## 581.97. Panic metadata

Panic/unwind ranges phải preserve function boundaries.

---

## 581.98. Axiom semantic metadata

Axiom-specific semantic metadata có thể nằm trong:

```text
.axm.*
```

hoặc target-specific custom sections.

---

## 581.99. Metadata version

Mọi Axiom custom section phải có format version.

---

## 581.100. Metadata compatibility

Unknown optional metadata phải có thể bị bỏ qua mà không phá native execution.

---

# Resources

## 581.101. Resource abstraction

Native resource objects được biểu diễn độc lập object format:

```text
Resource {
    type
    name
    language
    payload
}
```

---

## 581.102. Windows resources

PE linker stage có thể chuyển resource model thành `.rsrc`.

---

## 581.103. Mach-O resources

Resource bundle/package layer xử lý ngoài object writer nếu không có direct object equivalent.

---

## 581.104. ELF resources

Không ép resource semantics vào ELF nếu target không có native equivalent.

---

# Determinism

## 581.105. Deterministic object

Cùng input artifact identity → byte-identical object.

---

## 581.106. No timestamps

Deterministic mode không chứa:

- current timestamp;
- random UUID;
- machine hostname;
- process ID;
- absolute build path.

---

## 581.107. Stable section order

Section ordering deterministic.

---

## 581.108. Stable symbol order

Symbol ordering deterministic.

---

## 581.109. Stable relocation order

Relocation ordering deterministic.

---

## 581.110. Stable string tables

String insertion/order deterministic.

---

## 581.111. Stable COMDAT

COMDAT identity/order deterministic.

---

## 581.112. Stable padding

Padding bytes deterministic.

---

## 581.113. Stable metadata

Axiom metadata serialization deterministic.

---

# Validation

## 581.114. Object verifier

Mỗi object phải pass:

```text
Header validation
Section validation
Symbol validation
Relocation validation
Alignment validation
Range validation
Format validation
```

---

## 581.115. ELF verifier

Kiểm tra section/symbol/relocation graph của ELF.

---

## 581.116. COFF verifier

Kiểm tra section/symbol/COMDAT/relocation invariants.

---

## 581.117. Mach-O verifier

Kiểm tra load commands/segments/sections/symbols/relocations.

---

## 581.118. WASM verifier

Kiểm tra module index spaces, section ordering, types và function bodies.

---

## 581.119. Round-trip

Nếu có parser tương ứng:

```text
Object
 ↓ parse
ObjectModel
 ↓ serialize
Object'
```

phải giữ semantic identity.

---

## 581.120. Byte reproducibility

Serializer chạy nhiều lần phải tạo cùng bytes.

---

## 581.121. Malformed object tests

Parser/verifier phải reject malformed objects.

---

## 581.122. Relocation fuzzing

Random legal relocations được generate và verify.

---

## 581.123. Symbol fuzzing

Test symbol names:

- Unicode;
- long names;
- empty/edge cases;
- collisions;
- aliases.

---

## 581.124. Section fuzzing

Test alignment, zero-size, huge-size và section combinations.

---

# Integration

## 581.125. Input từ 580

Object writer nhận:

```text
EncodedCode
EncodedData
Fixups
```

---

## 581.126. Input từ 579

Nhận:

```text
CFI
Unwind
StackMap
FunctionRange
```

---

## 581.127. Input từ 565

Artifact metadata được serialize theo object artifact schema.

---

## 581.128. Output tới 564

Linker nhận canonical object graph.

---

## 581.129. Linker independence

Linker không cần biết compiler frontend.

---

## 581.130. Object writer independence

Object writer không cần semantic AST/HIR.

---

## 581.131. No repair stage

Object writer không được sửa:

- illegal instruction;
- invalid relocation;
- invalid ABI;
- invalid frame;
- unresolved virtual register.

Các lỗi đó phải bị bắt trước `581`.

---

# Incremental / Cache

## 581.132. Object fragment cache

Function/object fragments có thể được cache.

---

## 581.133. Cache identity

```text id="cache581"
EncodedFragmentHash
Target
ObjectFormat
ABI
EncoderVersion
ObjectWriterVersion
DebugPolicy
MetadataPolicy
```

---

## 581.134. Partial reuse

Không đổi function có thể reuse section payload.

---

## 581.135. Relocation regeneration

Nếu symbol layout thay đổi, relocation table có thể phải regenerate dù code bytes unchanged.

---

## 581.136. Debug invalidation

Source/debug policy thay đổi phải invalidate debug-dependent object data.

---

# Parallelism

## 581.137. Parallel section construction

Independent function/data sections có thể được build song song.

---

## 581.138. Canonical merge

Final object merge theo stable section/function IDs.

---

## 581.139. Parallel symbol collection

Symbol collection có thể parallel nhưng final ordering deterministic.

---

## 581.140. Parallel relocation collection

Relocation generation có thể parallel.

---

# Error model

## 581.141. Format error

Unsupported target format phải là structured diagnostic.

---

## 581.142. Relocation error

Diagnostic phải chứa:

```text
section
offset
symbol
relocation
width
expression
```

---

## 581.143. Symbol error

Duplicate/inconsistent symbol phải identify all relevant definitions.

---

## 581.144. Range error

Section/object-size overflow phải fail trước serialization.

---

## 581.145. Unsupported feature

Nếu object format không support requested feature, compiler phải:

1. lower sang representation hợp lệ khác; hoặc
2. báo lỗi rõ ràng.

Không silently drop semantics.

---

# Native artifact contract

## 581.146. Object ≠ executable

Object writer không tự quyết định final virtual addresses.

---

## 581.147. Linker responsibility

Linker chịu trách nhiệm:

```text
symbol resolution
layout
address assignment
relocation application
section GC
ICF
import/export
final image
```

---

## 581.148. Object responsibility

Object writer chịu trách nhiệm:

```text
bytes
sections
symbols
relocations
metadata
format serialization
```

---

## 581.149. No hidden linker

Object writer không chứa hidden linker.

---

## 581.150. Native independence

Full native pipeline:

```text id="native581"
Axiom Source
   ↓
Compiler
   ↓
Machine IR
   ↓
Encoder
   ↓
Object Writer
   ↓
Axiom Object
   ↓
Axiom Linker
   ↓
EXE / ELF / Mach-O / WASM
```

---

# Hard invariants

## 581.151

Mọi section phải có legal alignment.

## 581.152

Mọi symbol section reference phải tồn tại.

## 581.153

Mọi relocation section reference phải tồn tại.

## 581.154

Mọi relocation symbol reference phải tồn tại.

## 581.155

Mọi relocation offset phải nằm trong target section.

## 581.156

Mọi symbol offset phải nằm trong section bounds hoặc là explicit absolute/undefined symbol.

## 581.157

Không được emit relocation với width không tương thích.

## 581.158

Không được emit section flags mâu thuẫn.

## 581.159

Executable code không được đặt trong non-executable section nếu target semantics yêu cầu executable permission.

## 581.160

Writable data không được đánh dấu readonly.

## 581.161

TLS data phải có TLS section semantics.

## 581.162

BSS không được làm phình object bằng zero payload khi format hỗ trợ NOBITS/uninitialized representation.

## 581.163

COMDAT identity phải stable.

## 581.164

Weak/global/local linkage phải preserve semantic meaning.

## 581.165

Undefined symbols không được giả lập thành zero address.

## 581.166

External symbols phải preserve relocation information.

## 581.167

Debug ranges phải match final section offsets.

## 581.168

Unwind ranges phải match final function ranges.

## 581.169

Custom metadata không được làm thay đổi native code semantics.

## 581.170

Unknown optional metadata phải không làm object invalid nếu format cho phép.

## 581.171

Object writer không được thay đổi machine bytes.

## 581.172

Object writer không được thay đổi instruction semantics.

## 581.173

Object writer không được resolve external addresses.

## 581.174

Object writer không được tự ý remove relocation.

## 581.175

Object writer không được tự ý create semantic relocation.

## 581.176

Object serializer phải deterministic.

## 581.177

Object parser phải reject malformed structures.

## 581.178

Object verifier phải chạy trước artifact được đánh dấu trusted.

## 581.179

Remote-produced object phải được verify trước khi đưa vào trusted cache.

## 581.180

Object cache hit không được bypass compatibility/version checks.

## 581.181

ELF output phải satisfy ELF ABI structural invariants.

## 581.182

COFF output phải satisfy COFF structural invariants.

## 581.183

Mach-O output phải satisfy Mach-O structural invariants.

## 581.184

WASM output phải satisfy WASM binary/module invariants.

## 581.185

Format adapter không được làm mất canonical Axiom symbol identity.

## 581.186

Format adapter không được làm mất required relocation semantics.

## 581.187

Format-specific limitations phải được biểu diễn explicit.

## 581.188

Không được dùng external assembler để “fix” object.

## 581.189

Không được dùng external linker để repair malformed object.

## 581.190

Object generation phải reproducible.

## 581.191

Object identity phải bao gồm object-writer version.

## 581.192

Target identity phải bao gồm architecture + ABI + feature set.

## 581.193

Debug policy phải nằm trong artifact identity.

## 581.194

Metadata schema version phải nằm trong artifact identity.

## 581.195

Parallel object construction phải tạo cùng kết quả với serial construction.

## 581.196

Object writer failure phải fail closed.

## 581.197

Không được phát hành object đã verifier-fail như artifact hợp lệ.

## 581.198

Object writer không phải optimization stage.

## 581.199

Object writer không phải linker stage.

## 581.200 — FINAL HARD INVARIANT

> **Axiom Object Writer phải biến machine bytes + sections + symbols + relocations + debug/unwind/metadata thành object/module artifact hợp lệ cho ELF64, PE/COFF, Mach-O hoặc WASM một cách deterministic, không làm thay đổi semantics của machine code và không phụ thuộc assembler/compiler/linker bên thứ ba. Mọi relocation, symbol, section, alignment, linkage và metadata đều phải được kiểm tra structural validity trước khi artifact được chuyển sang linker hoặc runtime.**

# 581 — LOCKED

Kiến trúc native hiện đã nối kín:

```text
576 Optimization
      ↓
577 Register Allocation
      ↓
578 Instruction Scheduling
      ↓
579 Machine Finalization
      ↓
580 Machine Encoding
      ↓
581 Object Writer
      ↓
564 Linker
      ↓
Native Artifact
```

---

# NEXT — BOOTSTRAP-582

## NATIVE LINKER 4.0
### SYMBOL RESOLUTION, SECTION LAYOUT, RELOCATION APPLICATION, ARCHITECTURE RELAXATION, DEAD-SECTION GC, ICF, LTO OBJECT INTEGRATION, TLS, IMPORT/EXPORT, PLT/GOT/STUBS, PE IMPORT TABLE, MACH-O DYLD INFO & FINAL EXECUTABLE IMAGE

Pipeline tiếp theo:

```text id="l582"
Axiom Objects
     │
     ▼
Object Ingestion
     │
     ▼
Symbol Graph
     │
     ▼
Strong / Weak / COMDAT Resolution
     │
     ▼
Dead Section GC
     │
     ▼
ICF / Folding
     │
     ▼
Global Section Layout
     │
     ▼
Address Assignment
     │
     ▼
Relocation Application
     │
     ├── ELF
     ├── PE
     └── Mach-O
     │
     ▼
TLS / GOT / PLT / Stub Generation
     │
     ▼
Final Image Layout
     │
     ▼
Executable Verification
     │
     ▼
EXE / ELF / Mach-O
```

`582` sẽ khóa phần còn thiếu để pipeline **Axiom Source → native executable** thực sự hoàn chỉnh: **linker tự viết của Axiom**, bao gồm symbol resolution và final address assignment, thay vì dựa vào `ld`, `lld`, `link.exe` hay linker bên ngoài.