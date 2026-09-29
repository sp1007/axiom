# BOOTSTRAP-580 — MACHINE CODE ENCODING 4.0
## ISA ENCODER, INSTRUCTION BYTES, PREFIX/REX/EVEX, AARCH64 ENCODING, WASM BINARY EMISSION, FIXUPS, RELAXATION, CONSTANT POOLS, LITERAL POOLS & VERIFIED MACHINE BYTE GENERATION

**Trạng thái: COMPLETED / LOCKED**

`580` khóa tầng biến **Final Machine IR → machine bytes**. Đây là ranh giới quan trọng: từ đây Axiom không còn cần compiler/assembler bên thứ ba để tạo instruction bytes.

```text id="e8c4n7"
Final Machine IR
       │
       ▼
Instruction Legality
       │
       ▼
Operand Encoding
       │
       ▼
ISA Encoder
 ┌─────┼─────────┐
 ▼     ▼         ▼
x86   AArch64   WASM
       │
       ▼
Fixups / Relocations
       │
       ▼
Pools / Relaxation
       │
       ▼
Encoded Sections
       │
       ▼
Byte Verifier
       │
       ▼
Object / Executable
```

---

# 580.1. Encoder principle

Encoder là **pure deterministic transformation**:

```text
MachineInstruction + TargetDescription
        ↓
EncodedInstruction
```

---

# 580.2. Không dùng assembler ngoài

Axiom encoder không gọi:

- LLVM MC;
- GNU assembler;
- NASM;
- MASM;
- Clang;
- GCC;
- MSVC assembler.

---

# 580.3. Không phụ thuộc thư viện encoding bên thứ ba

ISA encoding tables là một phần của Axiom compiler/toolchain.

---

# 580.4. Target description

Encoder nhận target description từ `562`.

```text id="h6j3m0"
opcode
operand classes
encoding forms
prefix rules
immediates
register fields
feature requirements
```

---

# 580.5. Instruction encoding form

Mỗi instruction có một hoặc nhiều encoding forms.

```text id="q9s4k2"
Instruction
 ├─ Form A
 ├─ Form B
 └─ Form C
```

---

# 580.6. Form selection

Legalization/encoder chọn form phù hợp operand + target feature.

---

# 580.7. Encoding priority

Nếu nhiều encoding hợp lệ, chọn canonical/shortest/profitable form theo target policy.

---

# 580.8. Exact bytes

Encoder phải tạo byte sequence chính xác theo ISA specification.

---

# 580.9. Instruction length

Encoder phải biết chính xác encoded length trước emission hoặc hỗ trợ provisional length.

---

# 580.10. Variable-length ISA

x86-64 được xử lý bằng form/prefix/operand encoding pipeline.

---

# 580.11. Fixed-length ISA

AArch64 instructions mặc định có fixed-width instruction encoding.

---

# 580.12. Byte order

Target description xác định endianness.

---

# 580.13. x86 opcode map

Encoder phải support opcode maps cần thiết:

```text id="3w7p9a"
legacy
0F
0F38
0F3A
VEX/EVEX maps
```

---

# 580.14. Legacy prefixes

Encoder xử lý:

```text id="v2k8m1"
LOCK
REP
REPNE
segment
operand-size
address-size
```

khi instruction yêu cầu.

---

# 580.15. Prefix ordering

Prefix order phải canonical và ISA-valid.

---

# 580.16. REX

x86-64 REX prefix được sinh khi cần:

```text id="m5x2p8"
W
R
X
B
```

---

# 580.17. REX correctness

REX phải tương thích với operand/register selection.

---

# 580.18. VEX

VEX encoding phải support relevant vector instructions.

---

# 580.19. EVEX

EVEX encoding phải support:

```text id="8n4q6s"
vector length
masking
broadcast
register extensions
rounding
```

khi target feature bật.

---

# 580.20. EVEX validation

Encoder không được emit EVEX nếu target feature không enabled.

---

# 580.21. ModRM

x86 memory/register operands được encode bằng ModRM.

---

# 580.22. SIB

Addressing modes cần SIB phải được encode chính xác.

---

# 580.23. Displacement

Encoder chọn displacement width hợp lệ.

---

# 580.24. Immediate encoding

Immediate phải fit encoding form.

---

# 580.25. Immediate relaxation

Nếu short immediate form hợp lệ, encoder ưu tiên form compact khi policy cho phép.

---

# 580.26. Signed immediate

Sign-extension semantics phải match ISA.

---

# 580.27. Unsigned immediate

Unsigned immediate encoding phải giữ bit pattern chính xác.

---

# 580.28. Branch displacement

Branch operand được biểu diễn bằng symbolic fixup trước khi final layout.

---

# 580.29. PC-relative

Encoder hỗ trợ PC-relative references.

---

# 580.30. Absolute references

Absolute addresses chỉ được dùng khi target/relocation policy cho phép.

---

# 580.31. Relocation placeholder

Chưa biết target address → emit placeholder + relocation record.

---

# 580.32. Fixup

```text id="p6h9v2"
Fixup {
    offset
    width
    kind
    symbol
    addend
    pc_relative
}
```

---

# 580.33. Fixup width

Fixup width phải match encoded field.

---

# 580.34. Fixup signedness

Fixup interpretation phải được target relocation model xác định.

---

# 580.35. Addend

Relocation addend được lưu explicit.

---

# 580.36. Symbol reference

Symbol identity phải dùng canonical symbol ID từ linker/object model.

---

# 580.37. Local labels

Local branch targets có thể resolve trong encoder/layout stage.

---

# 580.38. External symbols

External symbols tạo relocation.

---

# 580.39. Weak symbols

Weak linkage được xử lý bởi object/linker, không encode thành hard address.

---

# 580.40. TLS references

TLS encoding sử dụng target-specific TLS relocation.

---

# 580.41. GOT/PLT-like references

Dynamic-linking targets có thể yêu cầu GOT/PLT relocation forms.

---

# 580.42. Position-independent code

PIC references phải dùng target-legal PC-relative/TLS/GOT mechanism.

---

# 580.43. PIE

PIE output sử dụng PIC-compatible encoding.

---

# 580.44. Static executable

Static mode có thể resolve nhiều references sớm hơn.

---

# 580.45. Branch relaxation

Branch encoder phải hỗ trợ nhiều displacement widths khi ISA cho phép.

---

# 580.46. Short branch

Nếu target nằm trong range, dùng short form.

---

# 580.47. Long branch

Nếu vượt range, dùng long form.

---

# 580.48. Relaxation loop

```text id="r7m3q0"
estimate
 ↓
layout
 ↓
check range
 ↓
expand
 ↓
repeat
```

---

# 580.49. Relaxation convergence

Mỗi relaxation iteration phải monotonic hoặc có bounded fallback.

---

# 580.50. No oscillation

Không cho phép short ↔ long oscillation.

---

# 580.51. Branch islands

Nếu target architecture yêu cầu, linker/backend có thể tạo branch islands/stubs.

---

# 580.52. Jump tables

Jump-table entries phải có target-specific encoding.

---

# 580.53. Switch lowering

Switch/jump table references phải integrate với relocation/layout.

---

# 580.54. Constant pools

Targets có literal-pool requirements phải hỗ trợ constant pools.

---

# 580.55. Literal pools

Literal values có thể được đặt trong read-only data/literal sections.

---

# 580.56. Pool identity

Identical constants có thể deduplicate nếu address identity không observable.

---

# 580.57. Pool placement

Pool placement phải satisfy target range constraints.

---

# 580.58. Pool islands

Large functions có thể cần multiple pools.

---

# 580.59. Pool reachability

Every literal reference must reach its pool within ISA range.

---

# 580.60. AArch64 encoding

AArch64 encoder sử dụng fixed 32-bit instruction forms.

---

# 580.61. AArch64 register fields

Encoder hỗ trợ:

```text id="h0q6v9"
Rn
Rm
Rd
Rt
Ra
```

và các field khác theo instruction form.

---

# 580.62. AArch64 immediate fields

Immediate encoding phải respect từng instruction's bit layout.

---

# 580.63. AArch64 branches

Conditional/unconditional branches tạo appropriate PC-relative fixups.

---

# 580.64. AArch64 literal loads

Literal load range phải được kiểm tra.

---

# 580.65. AArch64 ADR/ADRP

PC-relative page/address encoding phải support relocation/fixup.

---

# 580.66. AArch64 pair instructions

Load/store pair offsets phải fit signed immediate range.

---

# 580.67. AArch64 extensions

Feature-specific instruction forms chỉ emit khi CPU feature enabled.

---

# 580.68. AArch64 endianness

Default target mode phải explicit trong target description.

---

# 580.69. WASM binary encoding

WASM encoder không emit native CPU bytes; nó emit canonical WASM binary instructions.

---

# 580.70. WASM LEB128

Integer operands phải encode đúng signed/unsigned LEB128 rules.

---

# 580.71. WASM block structure

Structured control-flow phải được encode đúng nesting.

---

# 580.72. WASM function indices

Function references được resolve qua module index space.

---

# 580.73. WASM type indices

Type references phải resolve deterministic.

---

# 580.74. WASM locals

Register-allocation semantics đã được lower thành WASM locals/stack operations.

---

# 580.75. WASM memory

Memory access encoding phải preserve alignment/offset semantics.

---

# 580.76. WASM globals

Global indices phải được resolved trong module construction.

---

# 580.77. WASM tables

Indirect call/table references phải được encoded chính xác.

---

# 580.78. WASM sections

Encoder phải support required sections:

```text id="y5f3x7"
Type
Import
Function
Table
Memory
Global
Export
Element
Code
Data
Custom
```

---

# 580.79. WASM custom metadata

Axiom semantic/debug metadata có thể được đặt trong custom sections.

---

# 580.80. Section ordering

WASM section ordering phải tuân thủ format.

---

# 580.81. Section size

Section payload size phải được computed sau encoding.

---

# 580.82. Nested size

WASM vectors/blocks cần size prefixes phải encode sau payload size known.

---

# 580.83. Two-pass encoding

Encoder được phép:

```text id="9k4n2w"
layout pass
→ emission pass
```

---

# 580.84. Streaming encoding

Encoder có thể stream sections nếu length information đã known.

---

# 580.85. Object section

Machine bytes được đặt vào canonical object sections.

---

# 580.86. Text/data separation

Executable code và data không được trộn nếu target object format yêu cầu separation.

---

# 580.87. Alignment directives

Object layout có thể insert alignment padding.

---

# 580.88. NOP padding

Executable alignment dùng target-specific NOP sequences.

---

# 580.89. NOP correctness

NOP sequence phải legal trên minimum target CPU.

---

# 580.90. Zero padding

Non-executable sections có thể dùng zero padding theo object format.

---

# 580.91. Section flags

Code/data/readonly/TLS sections phải có correct flags.

---

# 580.92. COMDAT/linkonce

Encoded artifacts phải preserve linkage grouping metadata khi required.

---

# 580.93. Function sections

Compiler có thể đặt mỗi function vào riêng section để linker GC/ICF.

---

# 580.94. Data sections

Constants có thể được deduplicate.

---

# 580.95. Relocation records

Encoder không tự resolve external relocation.

---

# 580.96. Relocation type

Relocation type phải match target object format.

---

# 580.97. Overflow

Relocation overflow phải fail deterministic.

---

# 580.98. Range checking

Encoder phải detect branch/immediate/fixup range overflow.

---

# 580.99. No silent truncation

Không được truncate operand/fixup ngoài ISA-defined semantics.

---

# 580.100. Encoding error

Encoding failure phải structured diagnostic/internal compiler error.

---

# 580.101. Instruction verifier

Mỗi encoded instruction phải có metadata liên kết về source Machine IR instruction.

---

# 580.102. Round-trip validation

Có thể decode bytes trở lại canonical instruction representation để verify.

---

# 580.103. Internal decoder

Axiom nên có **minimal target decoder** tương ứng encoder.

---

# 580.104. Encoder/decoder independence

Decoder không được đơn giản gọi encoder ngược lại để che bug.

---

# 580.105. Decode verification

```text id="4v8m6j"
Machine IR
 ↓ encode
bytes
 ↓ decode
instruction
 ↓ compare
```

---

# 580.106. Semantic comparison

So sánh opcode/operands/flags/effects, không chỉ raw syntax.

---

# 580.107. Known-relocation comparison

Symbolic fixups được so sánh ở symbolic level.

---

# 580.108. Reference ISA corpus

Encoder phải có corpus từ ISA-defined encodings.

---

# 580.109. Golden bytes

Mỗi instruction form có golden-byte tests.

---

# 580.110. Negative tests

Illegal operand combinations phải bị reject.

---

# 580.111. Feature tests

Instruction yêu cầu CPU feature chưa bật phải bị reject.

---

# 580.112. Immediate boundary tests

Test min/max/range overflow.

---

# 580.113. Register boundary tests

Test register encoding extension bits.

---

# 580.114. Addressing tests

Test base/index/scale/displacement combinations.

---

# 580.115. Prefix tests

Test prefix combinations và conflicting prefixes.

---

# 580.116. Vector tests

Test vector lengths/masks/broadcast/rounding.

---

# 580.117. Branch tests

Test displacement boundaries.

---

# 580.118. Relaxation tests

Test transition short → long.

---

# 580.119. Pool tests

Test literal pool range boundaries.

---

# 580.120. Relocation tests

Test mỗi relocation kind supported.

---

# 580.121. TLS tests

Test TLS relocation and instruction sequences.

---

# 580.122. PIC tests

Test position-independent references.

---

# 580.123. Object integration

Encoded bytes phải map chính xác tới section offsets.

---

# 580.124. Symbol offsets

Symbol values được tính từ final section layout.

---

# 580.125. Fixup offsets

Fixup offset phải trỏ chính xác vào encoded field.

---

# 580.126. Addend verification

Relocation addend phải match symbolic expression.

---

# 580.127. Linker contract

Linker `564` nhận object relocation records canonical.

---

# 580.128. No encoder/linker ambiguity

Relocation semantics chỉ có một canonical definition.

---

# 580.129. Relaxation ownership

Mỗi relaxation transformation phải có owner rõ:

```text id="q1r7k2"
encoder
or
object layout
or
linker
```

---

# 580.130. No double relaxation

Cùng một branch không được relaxed hai lần theo conflicting rules.

---

# 580.131. Final layout dependency

Encoding length changes có thể làm thay đổi symbol offsets.

---

# 580.132. Layout iteration

Object layout phải lặp lại khi instruction lengths thay đổi.

---

# 580.133. Layout convergence

Iteration phải bounded.

---

# 580.134. Long-form fallback

Nếu relaxation không converge, compiler chuyển sang universally valid long form nếu target hỗ trợ.

---

# 580.135. Constant pool fallback

Nếu literal không reach được pool, compiler tạo pool gần hơn hoặc materialize constant bằng instructions.

---

# 580.136. Immediate materialization

Large constants có thể được tạo bằng instruction sequence thay vì literal pool.

---

# 580.137. Cost model

Choice giữa:

```text id="8h5n0x"
immediate sequence
literal load
constant pool
```

dựa trên size/speed.

---

# 580.138. Constant folding boundary

Encoder không thực hiện semantic constant folding; đó là optimizer `576`.

---

# 580.139. Instruction selection boundary

Encoder không chọn algorithmic instruction sequence; `561/562/576` chịu trách nhiệm.

---

# 580.140. Encoding-only principle

Encoder biến **đã chọn instruction** thành representation bytes.

---

# 580.141. No hidden optimization

Encoder không được âm thầm thay instruction bằng semantic khác ngoài explicitly declared peephole contract.

---

# 580.142. Optional encoding peepholes

Nếu có, phải là target-local verified transformations.

---

# 580.143. Byte determinism

Cùng Machine IR + target + feature set → cùng encoded bytes.

---

# 580.144. Relocation determinism

Relocation ordering canonical theo:

```text id="m6x2c8"
section
offset
type
symbol
addend
```

---

# 580.145. Symbol determinism

Symbol table ordering canonical.

---

# 580.146. Padding determinism

Padding bytes deterministic.

---

# 580.147. Alignment determinism

Alignment decisions deterministic.

---

# 580.148. Pool determinism

Constant/literal pool ordering deterministic.

---

# 580.149. Function ordering

Function order do linker/build policy quyết định và phải deterministic.

---

# 580.150. Parallel encoding

Functions độc lập có thể encode song song.

---

# 580.151. Parallel byte assembly

Encoded function fragments được ghép theo canonical ordering.

---

# 580.152. Parallel determinism

Parallel encoding không thay đổi final object.

---

# 580.153. Incremental encoding

Unchanged functions có thể reuse encoded fragments.

---

# 580.154. Encoding cache key

```text id="f5q8c1"
MachineIR hash
target
ISA features
encoder version
object format
optimization policy
```

---

# 580.155. Cache validation

Cache artifact phải được byte-verified trước reuse nếu trust level yêu cầu.

---

# 580.156. Remote encoding

Remote worker có thể encode nhưng output phải pass local validation.

---

# 580.157. Malicious worker

Invalid bytes/relocations không được accepted chỉ dựa trên worker declaration.

---

# 580.158. Security boundary

Encoder là trusted compiler component.

---

# 580.159. Signed target tables

Distributed toolchains có thể sign/verify target descriptions.

---

# 580.160. Versioning

ISA table version phải là part of compiler version/build identity.

---

# 580.161. Backward compatibility

Encoded artifacts không mặc nhiên compatible với target khác.

---

# 580.162. CPU feature metadata

Object có thể record required ISA features.

---

# 580.163. Feature validation

Linker/distributor không được strip required CPU feature metadata.

---

# 580.164. Baseline target

Compiler phải có explicit minimum ISA baseline.

---

# 580.165. CPU dispatch

Multi-versioned functions có thể encode nhiều ISA variants.

---

# 580.166. Variant metadata

Mỗi variant có required feature set.

---

# 580.167. Dispatch correctness

Dispatcher chỉ chọn legal variant.

---

# 580.168. x86-64 baseline

Baseline instruction subset được target profile xác định.

---

# 580.169. AArch64 baseline

Baseline ARM64 instruction subset được target profile xác định.

---

# 580.170. WASM feature set

WASM features phải được ghi trong target/module configuration.

---

# 580.171. Debug mapping

Encoded instruction offsets phải map tới source/debug locations.

---

# 580.172. Line table

Final offsets được dùng để generate debug line tables.

---

# 580.173. Unwind offsets

CFI/unwind ranges phải được update sau final encoding/layout.

---

# 580.174. Exception ranges

Exception/panic metadata phải trỏ đúng final machine offsets.

---

# 580.175. Stack maps

Nếu enabled, stack-map instruction offsets phải được remap sau encoding.

---

# 580.176. Security metadata

CFI/branch-protection metadata phải map đúng encoded ranges.

---

# 580.177. Byte-level verifier

Verifier kiểm tra:

```text id="3c7w1m"
length
opcode
operands
feature legality
fixups
offsets
```

---

# 580.178. Section verifier

Kiểm tra section size/alignment/flags.

---

# 580.179. Relocation verifier

Kiểm tra relocation target/field/range.

---

# 580.180. Symbol verifier

Symbol offsets phải nằm trong legal section ranges.

---

# 580.181. Object verifier

Encoded object phải satisfy object-format invariants từ `420/565`.

---

# 580.182. Differential execution

Generated executable có thể được chạy against reference/unoptimized executable.

---

# 580.183. ISA emulator

Axiom test suite có thể dùng emulator/reference implementation để validate instruction semantics.

---

# 580.184. Fuzz encoding

Random legal Machine IR phải produce decodable/legal bytes.

---

# 580.185. Mutation testing

Mutated instruction fields phải được decoder/verifier phát hiện khi invalid.

---

# 580.186. Exhaustive encoding subsets

Các instruction forms nhỏ có thể được exhaustively tested.

---

# 580.187. Large ISA coverage

Các ISA extensions quan trọng phải có golden corpus riêng.

---

# 580.188. Performance

Encoder phải ưu tiên table-driven/constant-time lookup cho common instructions.

---

# 580.189. Memory efficiency

Không cần giữ toàn bộ compiler IR khi streaming object emission.

---

# 580.190. Streaming

Function encoded bytes có thể được emit incrementally vào object builder.

---

# 580.191. Error recovery

Encoding failure phải identify:

```text id="n9f4z0"
function
instruction
operand
target
encoding form
```

---

# 580.192. Internal compiler error

Illegal Machine IR sau final verifier là compiler bug, không phải user source error.

---

# 580.193. Repro artifact

Compiler phải có khả năng dump:

```text id="2k8s5p"
Machine IR
encoding form
bytes
fixups
relocations
```

cho reproduction.

---

# 580.194. AI tooling

AI semantic tooling có thể query:

> instruction này được encode thành bytes nào và vì sao chọn form này?

nhưng canonical bytes vẫn do compiler quyết định.

---

# 580.195. No third-party toolchain

Native code path:

```text id="n4c7x2"
Axiom Source
→ Axiom Compiler
→ Axiom Encoder
→ Axiom Object
→ Axiom Linker
→ Native Artifact
```

không yêu cầu external assembler/compiler.

---

# 580.196. Native bootstrap requirement

Axiom compiler cuối cùng phải có khả năng tự encode chính binary compiler của nó.

---

# 580.197. Self-hosting implication

Stage compiler không được phụ thuộc vào external assembler để bootstrap final native artifact sau trust chain hoàn chỉnh.

---

# 580.198. Final machine-byte invariant

Mọi byte executable/data code do Axiom emitter tạo ra phải có provenance:

```text id="q8d2f6"
Source
→ MIR
→ Machine IR
→ Instruction
→ Encoding Form
→ Bytes
```

---

# 580.199. FINAL HARD INVARIANT

> **Axiom Machine Encoder phải tự tạo machine bytes trực tiếp từ Final Machine IR bằng target-defined encoding tables, không phụ thuộc compiler/assembler bên thứ ba. Mọi instruction encoding, immediate, register field, prefix, displacement, branch, literal pool, fixup và relocation phải được kiểm tra range/legality và có thể truy ngược về Machine IR. Cùng một Final Machine IR + target + ISA feature set + encoder version phải tạo cùng encoded representation; không được silent truncation, illegal encoding hoặc unresolved machine constraint.**

# 580.200. LOCK

**BOOTSTRAP-580: LOCKED.**

---

# NEXT — BOOTSTRAP-581

## OBJECT FILE WRITER 3.0
### ELF64, PE/COFF, MACH-O, WASM MODULE, SECTION/SYMBOL/RELOCATION EMISSION, DEBUG/UNWIND/RESOURCE SECTIONS, TLS, COMDAT, LINKAGE & DETERMINISTIC OBJECT GENERATION

Pipeline:

```text id="q4m7x1"
Final Machine Bytes
        │
        ├── Code
        ├── Read-only Data
        ├── Data
        ├── BSS
        ├── TLS
        ├── Debug
        ├── Unwind
        └── Metadata
        │
        ▼
   Object Builder
        │
   ┌────┼──────────┐
   ▼    ▼          ▼
 ELF  PE/COFF    Mach-O
   │    │          │
   └────┼──────────┘
        ▼
   WASM Module
        │
        ▼
 Deterministic Object
        │
        ▼
 Linker 564
```

`581` sẽ khóa **cách Axiom tự xây object file hoàn chỉnh** từ bytes + symbols + relocations, bao gồm ELF/PE/Mach-O và WASM, thay vì chỉ dừng ở machine-code encoding.