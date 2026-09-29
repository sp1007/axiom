# BOOTSTRAP-583 — NATIVE IMAGE LOADER CONTRACT 2.0
## ELF/PE/MACH-O LOADABILITY, ENTRY POINT, PROCESS STARTUP, DYNAMIC LINKING, IMPORT RESOLUTION, TLS INITIALIZATION, MEMORY MAPPING, LOAD-TIME RELOCATION & AXIOM RUNTIME STARTUP

**Trạng thái: COMPLETED / LOCKED**

`583` khóa hợp đồng giữa **native image do Axiom Linker tạo ra** và **OS loader/runtime startup**.

Đây là tầng trả lời câu hỏi:

> Sau khi `582` tạo EXE/ELF/Mach-O, OS phải load nó như thế nào và Axiom phải bắt đầu thực thi từ đâu?

```text id="583arch"
                 Native Image
                      │
                      ▼
                  OS Loader
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
      ELF            PE          Mach-O
        │             │             │
        └─────────────┼─────────────┘
                      ▼
               Memory Mapping
                      │
                      ▼
             Dynamic Relocation
                      │
                      ▼
                TLS Setup
                      │
                      ▼
              Runtime Startup
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
      Args          Env          Runtime
        │             │             │
        └─────────────┼─────────────┘
                      ▼
                  Axiom Main
```

---

# 583.1. Loader boundary

Axiom phân chia trách nhiệm thành:

```text id="bound583"
OS
 └── image loading / virtual memory / process creation

Axiom Linker
 └── image metadata required by OS

Axiom Startup
 └── language/runtime initialization

Axiom Application
 └── user program
```

---

# 583.2. Không tự viết OS loader

Axiom không thay thế Windows/Linux/macOS loader.

Axiom chỉ tạo image tuân thủ loader contract của target.

---

# 583.3. Loader contract

Final image phải cung cấp đủ thông tin để OS:

1. nhận diện image;
2. map memory;
3. thiết lập permissions;
4. resolve required imports;
5. apply required runtime relocations;
6. initialize TLS;
7. transfer control tới entry point.

---

# 583.4. Entry point

Mỗi native image phải có một entry point hợp lệ.

```text
EntryPoint:
    address
    section
    calling_environment
```

---

# 583.5. Entry point không phải `main`

Entry point OS-level khác với Axiom source-level:

```text
OS entry
   ↓
Axiom startup
   ↓
runtime initialization
   ↓
user main
```

---

# 583.6. Main contract

Axiom `main` được compiler lower thành runtime-defined callable interface.

---

# 583.7. Startup ABI

Startup ABI phải được target-specific.

```text id="startupabi"
x86-64 Windows
x86-64 Linux
AArch64 Linux
AArch64 macOS
AArch64 iOS
...
```

không được giả định cùng startup convention.

---

# 583.8. Minimal runtime

Axiom phải hỗ trợ executable không cần full standard runtime.

```text id="freestand"
_start
   ↓
user_entry
```

cho freestanding/profile phù hợp.

---

# 583.9. Hosted runtime

Hosted application sử dụng:

```text id="hosted"
OS startup
 ↓
Axiom startup
 ↓
runtime
 ↓
main
```

---

# 583.10. Runtime profile

Build configuration xác định:

```text
freestanding
minimal
hosted
full
```

---

# 583.11. No mandatory runtime

Một chương trình không sử dụng allocator, async, reflection, GUI... không được buộc link toàn bộ runtime.

---

# 583.12. Runtime component GC

Runtime components được link theo reachability.

---

# 583.13. Startup object

Axiom startup code là native Axiom code hoặc target-specific startup implementation thuộc Axiom toolchain.

---

# 583.14. Startup provenance

Startup code phải có compiler/toolchain provenance giống các compiler-generated functions khác.

---

# 583.15. Process arguments

Hosted startup phải expose command-line arguments theo canonical Axiom API.

Ví dụ:

```text id="args"
fn main(args: Args) -> Result
```

---

# 583.16. Environment

Environment variables được expose qua runtime/OS abstraction.

---

# 583.17. Standard streams

Hosted runtime có thể initialize:

```text
stdin
stdout
stderr
```

nhưng freestanding profile không yêu cầu.

---

# 583.18. Exit status

Axiom `main` result được chuyển thành process exit status.

---

# 583.19. Normal exit

```text
main returns
   ↓
runtime shutdown
   ↓
exit(status)
```

---

# 583.20. Explicit exit

Application có thể gọi platform exit primitive.

---

# 583.21. Exit cleanup

Explicit exit policy phải xác định cleanup nào được thực hiện.

---

# 583.22. Panic at startup

Startup panic phải có deterministic failure path.

---

# 583.23. Panic before runtime

Nếu panic xảy ra trước runtime initialization, sử dụng minimal panic path.

---

# 583.24. Fatal startup failure

Failure không thể recover phải terminate process với platform-valid status.

---

# ELF LOADING

# 583.25. ELF identification

ELF image phải có valid:

```text
EI_CLASS
EI_DATA
EI_VERSION
EI_OSABI
```

---

# 583.26. ELF architecture

`e_machine` phải match target architecture.

---

# 583.27. ELF type

Executable:

```text
ET_EXEC
```

hoặc PIE:

```text
ET_DYN
```

theo linker policy.

---

# 583.28. Program headers

OS loader sử dụng program headers, không phải section headers, để load executable.

---

# 583.29. PT_LOAD

Mỗi loadable segment phải có:

```text
file offset
virtual address
file size
memory size
flags
alignment
```

hợp lệ.

---

# 583.30. File-to-memory mapping

Loader mapping phải satisfy:

```text
p_offset ↔ p_vaddr
```

alignment constraints của ELF ABI.

---

# 583.31. Segment overlap

Loadable segments không được tạo mapping conflict ngoài allowed page sharing.

---

# 583.32. Memory size

`p_memsz >= p_filesz`.

---

# 583.33. BSS loading

Phần:

```text
p_memsz - p_filesz
```

được zero-initialize.

---

# 583.34. ELF permissions

`PF_R`, `PF_W`, `PF_X` phải match final section permissions.

---

# 583.35. Entry address

`e_entry` phải nằm trong executable mapped range.

---

# 583.36. PIE entry

PIE entry phải được tính relative tới load base khi cần.

---

# 583.37. ELF interpreter

Dynamically linked ELF có thể chứa `PT_INTERP`.

---

# 583.38. Dynamic loader

Axiom không thay thế system dynamic loader trong hosted dynamic-linking mode.

---

# 583.39. Static ELF

Static ELF có thể không cần `PT_INTERP`.

---

# 583.40. Dynamic ELF

Dynamic dependencies phải được biểu diễn trong dynamic section.

---

# 583.41. DT_NEEDED

Required shared libraries được encode deterministic.

---

# 583.42. Dynamic symbols

Runtime-resolved symbols phải có dynamic symbol representation.

---

# 583.43. Runtime relocations

Chỉ relocations mà OS dynamic loader cần mới được giữ trong final image.

---

# 583.44. ELF RELRO

Linker có thể mark relocation-dependent structures read-only sau relocation.

---

# 583.45. ELF GNU hash

Nếu compatibility profile yêu cầu, Axiom có thể emit compatible hash structures.

---

# 583.46. ELF symbol lookup

Runtime symbol lookup semantics phải match selected dynamic ABI.

---

# PE LOADING

# 583.47. PE signature

Image phải có valid PE signature.

---

# 583.48. PE architecture

COFF machine field phải match target.

---

# 583.49. Optional header

PE optional header phải chứa valid:

```text
image base
section alignment
file alignment
image size
headers size
entry RVA
subsystem
data directories
```

---

# 583.50. PE entry

`AddressOfEntryPoint` phải trỏ vào executable section.

---

# 583.51. PE section mapping

Mỗi section phải có:

```text
VirtualAddress
VirtualSize
PointerToRawData
SizeOfRawData
Characteristics
```

hợp lệ.

---

# 583.52. PE raw alignment

Raw section offsets phải satisfy `FileAlignment`.

---

# 583.53. PE virtual alignment

Virtual section addresses phải satisfy `SectionAlignment`.

---

# 583.54. PE image size

`SizeOfImage` phải bao phủ toàn bộ mapped image.

---

# 583.55. PE headers

`SizeOfHeaders` phải bao phủ headers + section table.

---

# 583.56. PE imports

Import directory phải trỏ tới valid structures.

---

# 583.57. DLL names

Imported DLL identifiers phải được encode canonical.

---

# 583.58. IAT

Import Address Table phải có đủ entries cho runtime-resolved functions.

---

# 583.59. Delay imports

Delay-load imports là optional linker feature và phải được explicit.

---

# 583.60. PE base relocations

Relocation directory phải tồn tại nếu image policy yêu cầu relocatable image.

---

# 583.61. ASLR

PE image có thể enable ASLR bằng appropriate image characteristics/relocation data.

---

# 583.62. PE TLS

TLS directory phải map đúng:

```text
TLS raw data
zero-fill
index
callbacks
```

khi sử dụng TLS.

---

# 583.63. TLS callbacks

TLS callback addresses phải thuộc mapped executable ranges.

---

# 583.64. PE unwind

Exception/unwind metadata phải map đúng function address ranges.

---

# 583.65. Subsystem

Console/GUI subsystem là image configuration.

---

# 583.66. DLL image

Shared-library build có DLL entry contract thay vì ordinary executable entry.

---

# MACH-O LOADING

# 583.67. Mach-O header

Header phải match:

```text
CPU type
CPU subtype
file type
```

---

# 583.68. Load commands

Load-command table phải nằm hoàn toàn trong header region.

---

# 583.69. Segment commands

Mỗi mapped segment phải có valid:

```text
vmaddr
vmsize
fileoff
filesize
maxprot
initprot
```

---

# 583.70. `__TEXT`

Executable/read-only content thường được đặt trong `__TEXT`.

---

# 583.71. `__DATA`

Writable content nằm trong appropriate data segment.

---

# 583.72. `__LINKEDIT`

Dynamic-linking/symbol/signature structures có thể nằm trong `__LINKEDIT`.

---

# 583.73. Entry point

Modern Mach-O executable entry metadata phải resolve tới executable code.

---

# 583.74. Dyld

Dynamic linking sử dụng system dyld semantics trong hosted mode.

---

# 583.75. Rebase

Image rebasing metadata phải match actual pointers requiring adjustment.

---

# 583.76. Bind

External symbol binding metadata phải match imported symbols.

---

# 583.77. Export trie

Exported symbols phải be represented consistently.

---

# 583.78. Chained fixups

Nếu deployment profile sử dụng chained fixups, final image phải contain valid chain information.

---

# 583.79. Code signature

Platform-required signing data là post-link artifact.

---

# 583.80. Signature ordering

Signing phải diễn ra sau final image bytes/layout.

---

# 583.81. iOS restrictions

iOS target có thể yêu cầu signing/provisioning/platform metadata ngoài compiler semantics.

---

# MEMORY MAPPING CONTRACT

# 583.82. Virtual address

Mỗi loadable segment có virtual address range.

---

# 583.83. Page alignment

Mapped regions phải page-aligned theo OS/ABI.

---

# 583.84. Protection

Default:

```text id="wx"
code     → R-X
rodata   → R--
data     → RW-
bss      → RW-
```

---

# 583.85. W^X

Final image không yêu cầu writable executable memory.

---

# 583.86. JIT exception

Nếu runtime có JIT, executable memory policy được tách khỏi ordinary native image contract.

---

# 583.87. No runtime patching

Native code không được mặc định yêu cầu writable code pages.

---

# 583.88. RELRO-like hardening

Structures có thể chuyển từ writable → readonly sau loader relocation.

---

# 583.89. Zero-fill

Uninitialized memory phải được zero-initialized theo loader contract.

---

# 583.90. Memory reservation

Loader determines actual virtual address placement.

---

# 583.91. ASLR compatibility

Internal image references phải support randomized load base khi image mode yêu cầu.

---

# LOAD-TIME RELOCATION

# 583.92. Static-resolved relocation

Linker phải resolve mọi relocation có thể resolve statically.

---

# 583.93. Runtime relocation

Remaining relocation phải explicitly declare loader responsibility.

---

# 583.94. No hidden relocation

Không được có absolute pointer trong image mà không có corresponding relocation khi ASLR/PIC yêu cầu.

---

# 583.95. Relocation bounds

Runtime relocation target phải nằm trong mapped writable/legally patchable area.

---

# 583.96. Code relocation

Runtime loader không được buộc patch executable code nếu target security model cấm.

---

# 583.97. Data relocation

Preferred runtime relocations target data structures.

---

# 583.98. RELRO ordering

Loader applies relocation trước khi region trở thành readonly.

---

# 583.99. Relocation idempotence

Relocation không được áp dụng hai lần.

---

# 583.100. Relocation identity

Mỗi runtime relocation có unique identity/offset.

---

# 583.101. Relocation overflow

Loader/linker contract phải guarantee field width đủ lớn.

---

# 583.102. Architecture-specific relocation

ELF/PE/Mach-O relocation semantics phải target-specific.

---

# TLS INITIALIZATION

# 583.103. TLS model

Axiom TLS abstraction từ `423/424` map xuống target TLS ABI.

---

# 583.104. Static TLS

Static TLS data được loader initialize khi process/thread creation.

---

# 583.105. Dynamic TLS

Dynamic TLS modules được runtime/OS mechanism xử lý.

---

# 583.106. Thread-local zero fill

TLS BSS phải zero-initialize.

---

# 583.107. TLS alignment

TLS blocks phải respect ABI alignment.

---

# 583.108. TLS destructor

Nếu Axiom resource model yêu cầu TLS destructors, chúng phải được registered deterministic.

---

# 583.109. TLS startup

Main thread TLS phải initialized trước user code truy cập TLS.

---

# 583.110. New threads

Mỗi OS thread phải có valid Axiom TLS state trước khi chạy Axiom thread entry.

---

# 583.111. Async tasks

Async task-local state không được nhầm với OS TLS.

---

# 583.112. TLS vs task-local

Hai abstraction phải độc lập:

```text
OS Thread Local
Task Local
```

---

# PROCESS STARTUP

# 583.113. Startup stages

```text id="start583"
OS
 ↓
entry
 ↓
minimal platform setup
 ↓
TLS/runtime base
 ↓
allocator (optional)
 ↓
panic subsystem
 ↓
I/O subsystem (optional)
 ↓
global initialization
 ↓
main
```

---

# 583.114. Minimal startup

Không dùng subsystem nào → không initialize subsystem đó.

---

# 583.115. Initialization dependency graph

Runtime init phải có DAG dependency.

---

# 583.116. No initialization cycles

Circular runtime initialization phải bị compiler/linker detect hoặc fail deterministic.

---

# 583.117. Global initialization

Global values cần dynamic initialization được register.

---

# 583.118. Static initialization

Compile-time known globals được đặt trực tiếp vào image.

---

# 583.119. Dynamic initialization

Runtime-required initialization chạy trước `main`.

---

# 583.120. Initialization ordering

Axiom package/module initialization order phải defined by language/runtime specification, không phụ thuộc incidental linker order.

---

# 583.121. Finalization

Shutdown hooks/destructors được execute theo reverse dependency/order policy.

---

# 583.122. Abnormal termination

OS crash/forced termination không guarantee ordinary finalization.

---

# 583.123. Signal/exception

Platform exceptions được chuyển vào panic/unwind layer nếu enabled.

---

# 583.124. Startup stack

Entry stack assumptions được target startup adapter encapsulate.

---

# 583.125. Stack alignment

Startup phải establish ABI-required stack alignment trước gọi Axiom functions.

---

# 583.126. Calling convention

Startup → runtime → main phải match `421`.

---

# 583.127. Register state

Startup code không được assume arbitrary callee-saved register values.

---

# 583.128. Floating-point state

Runtime có thể establish required FP/vector environment nếu language profile yêu cầu.

---

# 583.129. CPU feature state

Runtime không được sử dụng unsupported CPU feature trước feature dispatch initialization.

---

# 583.130. CPU dispatch

Multiversioned runtime functions phải select legal variant.

---

# 583.131. Command-line decoding

Platform-specific command line được chuyển thành canonical UTF-8 representation.

---

# 583.132. Windows arguments

Windows wide-character process arguments phải được chuyển sang UTF-8.

---

# 583.133. Unix arguments

Unix byte arguments phải được exposed với explicit encoding semantics.

---

# 583.134. Environment encoding

Environment API phải document encoding behavior theo platform.

---

# 583.135. Working directory

Runtime có thể expose process working directory.

---

# 583.136. Process identity

PID/process metadata là platform service, không phải language primitive bắt buộc.

---

# 583.137. Exit status width

Axiom process exit status phải map được sang target OS range.

---

# 583.138. Startup error reporting

Nếu standard I/O chưa sẵn sàng, startup có minimal platform diagnostic.

---

# DYNAMIC LINKING

# 583.139. Dynamic library dependency graph

```text id="dyngraph"
Executable
 ├── libA
 │    └── libB
 └── libC
```

---

# 583.140. Dependency identity

Library identity phải canonical.

---

# 583.141. Version policy

Dynamic library compatibility có version policy.

---

# 583.142. ABI compatibility

Dynamic symbol chỉ compatible nếu ABI-compatible.

---

# 583.143. Symbol name equality

Cùng tên không đảm bảo cùng ABI.

---

# 583.144. Import contract

Import declaration gồm:

```text
name
ABI
calling convention
version
required features
```

khi cần.

---

# 583.145. Export contract

Export declaration có:

```text
name
address
ABI metadata
visibility
```

---

# 583.146. Symbol preemption

Platform-specific preemption semantics phải được preserve.

---

# 583.147. Lazy binding

Có thể bật lazy binding nếu platform hỗ trợ.

---

# 583.148. Eager binding

Security/performance profile có thể yêu cầu eager binding.

---

# 583.149. Missing library

Missing dynamic dependency → loader/link failure, không substitute silently.

---

# 583.150. Missing symbol

Missing required symbol → deterministic startup failure.

---

# 583.151. Library initialization

Dynamic libraries có initialization contract.

---

# 583.152. Library shutdown

Library finalization phải follow platform semantics.

---

# 583.153. Runtime ABI version

Axiom runtime dynamic libraries có ABI version.

---

# 583.154. Runtime compatibility

Compiler-generated calls phải target compatible runtime ABI.

---

# 583.155. Static runtime

Có thể statically link runtime components.

---

# 583.156. Hybrid runtime

Một số components static, một số dynamic.

---

# 583.157. Runtime-free

Freestanding program có thể không link Axiom runtime.

---

# 583.158. FFI dynamic linking

`extern` imports phải đi qua same symbol/import contract.

---

# FREESTANDING

# 583.159. Freestanding entry

Freestanding application có thể cung cấp:

```text
@entry
fn start() -> never
```

hoặc canonical equivalent.

---

# 583.160. No OS assumption

Freestanding profile không giả định:

- filesystem;
- process;
- sockets;
- threads;
- environment.

---

# 583.161. Bare-metal

Target-specific linker script/image configuration có thể được cung cấp mà không thay đổi language semantics.

---

# 583.162. Firmware

Firmware image không nhất thiết có ELF/PE/Mach-O final form; target artifact adapter có thể tạo raw/binary/firmware image.

---

# 583.163. Kernel

Kernel profile có custom entry/memory layout.

---

# 583.164. Interrupt entry

Interrupt handlers có dedicated ABI/attribute.

---

# 583.165. Naked functions

Naked functions bypass ordinary prologue/epilogue nhưng phải explicit và restricted.

---

# 583.166. Startup safety

Compiler không được tự chèn runtime calls vào freestanding code nếu profile cấm runtime dependency.

---

# WEBASSEMBLY

# 583.167. WASM loading model

WASM không dùng OS native image loader.

```text
Module
 ↓
WASM Runtime
 ↓
Instantiation
 ↓
Start function
 ↓
Exported function
```

---

# 583.168. WASM start function

Optional start function chạy sau instantiation.

---

# 583.169. WASM imports

Imports được resolve bởi host.

---

# 583.170. WASM memory

Linear memory được host runtime allocate/map.

---

# 583.171. WASM TLS

OS TLS semantics không áp dụng trực tiếp; Axiom runtime mô phỏng task/thread-local semantics theo WASM host capabilities.

---

# 583.172. WASM arguments

Host adapter cung cấp argument representation.

---

# 583.173. WASM exit

Exit status là host convention.

---

# 583.174. WASI

Nếu target profile dùng WASI, Axiom std layer map sang WASI interfaces.

---

# 583.175. Browser

Browser profile map runtime services sang JavaScript/Web APIs hoặc explicit host imports.

---

# SECURITY

# 583.176. Loader hardening

Generated images phải tương thích với:

- ASLR;
- DEP/NX;
- W^X;
- RELRO;
- CFI/CFG;
- stack protections.

---

# 583.177. No executable writable data

Default linker policy không tạo RWX.

---

# 583.178. Import hardening

Dynamic imports phải được explicit.

---

# 583.179. Runtime code generation

JIT capability không được implicit.

---

# 583.180. Privileged instructions

User-mode executable không được emit privileged instructions trừ explicit target/kernel profile.

---

# 583.181. Security metadata

Security metadata phải match final image addresses.

---

# 583.182. Signature

Code signing là artifact integrity layer, không phải language semantics.

---

# 583.183. Signature timing

Signing luôn xảy ra sau final relocation/layout.

---

# 583.184. Signed artifact modification

Sau signing, bất kỳ byte modification nào phải invalidate signature.

---

# VALIDATION

# 583.185. Loadability test

Mỗi target phải có test:

```text id="loadtest"
compile
 ↓
link
 ↓
OS loader
 ↓
entry
 ↓
main
 ↓
exit
```

---

# 583.186. Static executable test

Test executable không dynamic dependency.

---

# 583.187. Dynamic executable test

Test executable + shared library.

---

# 583.188. TLS test

Test main thread + spawned threads + TLS initialization.

---

# 583.189. ASLR test

Test image dưới randomized load base khi platform cho phép.

---

# 583.190. Import test

Test external symbol resolution.

---

# 583.191. Export test

Test exported function/data.

---

# 583.192. Unwind test

Test panic/exception stack unwinding từ entry/main và nested functions.

---

# 583.193. Startup argument test

Test Unicode command-line arguments.

---

# 583.194. Environment test

Test environment access.

---

# 583.195. Exit test

Test return code mapping.

---

# 583.196. Minimal-runtime test

Program không dùng standard runtime component không được link component đó.

---

# 583.197. Freestanding test

Freestanding build phải không reference unavailable hosted APIs.

---

# 583.198. WASM test

WASM module phải instantiate và invoke entry/export theo target host contract.

---

# 583.199. FINAL HARD INVARIANT

> **Mọi native image do Axiom Linker tạo ra phải tuân thủ chính xác loader contract của target: headers, segments/sections, permissions, address mapping, entry point, imports/exports, runtime relocations, TLS, unwind và security metadata. Sau khi OS loader chuyển quyền điều khiển, Axiom startup phải thiết lập đúng ABI, TLS và runtime tối thiểu trước khi gọi user entry/main. Không được yêu cầu external linker/loader shim để sửa image; mọi thông tin cần thiết cho load-time behavior phải được tạo chính xác ngay trong Axiom toolchain.**

# 583 — LOCKED

Chuỗi native execution hiện hoàn chỉnh đến mức:

```text id="complete583"
Axiom Source
     │
     ▼
Compiler Frontend
     │
     ▼
HIR / MIR
     │
     ▼
Optimization
     │
     ▼
Register Allocation
     │
     ▼
Instruction Scheduling
     │
     ▼
Machine Finalization
     │
     ▼
Machine Encoder
     │
     ▼
Object Writer
     │
     ▼
Axiom Linker
     │
     ▼
Native Image
     │
     ▼
OS Loader
     │
     ▼
Axiom Startup
     │
     ▼
Runtime Init
     │
     ▼
main()
     │
     ▼
Native Program
```

Điểm đáng chú ý là **583 không biến Axiom thành một OS/runtime nặng**. Runtime vẫn được thiết kế theo nguyên tắc **pay-for-what-you-use**: chương trình càng thấp tầng thì càng có thể bỏ qua nhiều tầng runtime.

---

# NEXT — BOOTSTRAP-584

## NATIVE EXECUTABLE IMAGE FORMAT 3.0
### FINAL ELF/PE/MACH-O IMAGE CONSTRUCTION, SEGMENT PACKING, ENTRY/STARTUP STUBS, IMPORT/EXPORT TABLES, DYNAMIC RELOCATION, TLS IMAGE, UNWIND/DWARF/CODEVIEW, RESOURCE PACKING & REPRODUCIBLE FINAL BINARY

`584` sẽ hợp nhất `582 + 583` thành **final image construction pipeline**, tức từ linked sections đến **file EXE/ELF/Mach-O hoàn chỉnh ở mức byte**, bao gồm cả các cấu trúc mà OS loader thực sự đọc:

```text id="584next"
Linked Sections
       │
       ▼
Segment Builder
       │
       ├── RX
       ├── R
       ├── RW
       ├── TLS
       └── Special
       │
       ▼
Address / File Layout
       │
       ▼
Entry / Startup
       │
       ▼
Dynamic Metadata
       │
       ▼
TLS / Unwind / Debug
       │
       ▼
Import / Export
       │
       ▼
Final Image
       │
       ├── Windows → .exe / .dll
       ├── Linux   → ELF
       ├── macOS   → Mach-O
       ├── iOS     → Mach-O
       └── WASM    → Module
       │
       ▼
Byte-level Image Verification
       │
       ▼
Reproducible Artifact
```

`584` sẽ là bước **đóng gói final native binary**, trước khi chuyển sang các tầng cao hơn như installer/distribution/deployment.