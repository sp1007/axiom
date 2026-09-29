# BOOTSTRAP-778 — AXSTARTUP

**Title:** Native Platform Startup, CRT-Free Entry, PE64/ELF64/Mach-O/Android/iOS Process Bootstrap, Stack/Arguments/Environment Extraction, Auxiliary Vector, Platform TLS Bootstrap, Initial Thread Construction & Handoff to AXRUNTIME 5.0  
**Namespace:** `AXSTARTUP`  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXSTARTUP` là lớp cực thấp chịu trách nhiệm biến **OS/platform entry state** thành một trạng thái chuẩn để `AXRUNTIME` có thể khởi động.

```text
OS / Platform
     │
     ▼
┌──────────────┐
│ AXSTARTUP    │
│              │
│ raw entry    │
│ stack        │
│ registers    │
│ args/env     │
│ auxv         │
│ TLS bootstrap│
│ platform ABI │
└──────┬───────┘
       ▼
┌──────────────┐
│  AXRUNTIME   │
└──────┬───────┘
       ▼
   application
```

AXSTARTUP phải càng nhỏ càng tốt.

Nó **không phải runtime đầy đủ**.

---

# 2. Architectural boundary

### AXSTARTUP sở hữu

- platform entry point;
- raw startup state;
- stack/register extraction;
- argument extraction;
- environment extraction;
- auxiliary startup metadata;
- initial stack normalization;
- platform TLS bootstrap;
- platform-specific startup adaptation;
- minimal startup validation;
- handoff sang AXRUNTIME.

### Không sở hữu

```text
AXCOMPILER
→ compilation

AXLINKER
→ final linking

AXBINARY
→ executable format serialization

AXLOADER
→ general module loading

AXPROCESS
→ process lifecycle

AXMEMORY
→ general memory management

AXRUNTIME
→ application runtime

AXTASK
→ task scheduler

AXASYNC
→ async execution

AXSECURITY
→ policy authority
```

---

# 3. Core principle

Axiom phải hỗ trợ:

```text
CRT-free startup
```

Nghĩa là executable native không bắt buộc phải phụ thuộc:

```text
C runtime startup
libc startup object
C++ runtime startup
third-party startup framework
```

---

# 4. Startup layers

```text
                OS
                 │
                 ▼
          platform entry
                 │
                 ▼
          AXSTARTUP
                 │
          ┌──────┴──────┐
          ▼             ▼
     normalize       validate
          │             │
          └──────┬──────┘
                 ▼
           AXRUNTIME
                 │
                 ▼
              main()
```

---

# 5. Supported startup targets

Baseline:

```text
Windows x86_64 PE64
Windows AArch64 PE64

Linux x86_64 ELF64
Linux AArch64 ELF64

macOS x86_64 Mach-O
macOS AArch64 Mach-O

iOS AArch64 Mach-O
iOS simulator targets

Android AArch64 ELF64

WASM32
```

---

# 6. Startup modes

```text
NATIVE_OS
FREESTANDING
EMBEDDED
WASM_HOSTED
```

---

# 7. Native OS mode

OS directly creates process and transfers control to executable entry.

---

# 8. Freestanding mode

Application controls its own entry contract.

```text
@entry
fn start(...)
```

có thể bypass AXRUNTIME hoàn toàn.

---

# 9. Embedded mode

Axiom runtime được embedded vào một host application.

AXSTARTUP không cần own OS process entry.

---

# 10. WASM mode

Không có native process stack entry tương đương.

WASM host tạo instance và gọi exported/start function.

AXSTARTUP chỉ cung cấp adapter khi cần.

---

# 11. Raw startup state

```text
RawStartupState {
    architecture
    stack_pointer
    instruction_pointer
    registers?
    process_handle?
    environment_source?
    argument_source?
    platform_data
}
```

---

# 12. Normalized startup state

```text
StartupState {
    target
    args
    env
    process
    main_thread
    tls
    platform
    aux
}
```

---

# 13. Startup transition

```text
RawStartupState
       ↓
platform_decode()
       ↓
StartupState
       ↓
runtime_bootstrap()
```

---

# 14. Entry point contract

Mỗi target phải có một canonical startup symbol:

```text
__ax_start
```

hoặc target-specific equivalent được AXBINARY/AXLINKER chọn.

---

# 15. Entry point responsibilities

Entry code chỉ:

1. preserve required state;
2. establish ABI assumptions;
3. obtain startup parameters;
4. initialize minimal TLS/platform state;
5. construct startup state;
6. call AXRUNTIME.

---

# 16. Entry code must not

Không:

- allocate arbitrary heap;
- initialize full scheduler;
- initialize logging;
- scan filesystem;
- load plugins;
- execute user constructors trước runtime contract;
- perform unnecessary syscalls.

---

# 17. x86_64 register state

Compiler backend phải biết exact platform entry ABI.

Không được giả định một calling convention duy nhất cho mọi OS.

---

# 18. AArch64 register state

AArch64 startup adapter tương tự nhưng dùng target ABI tương ứng.

---

# 19. Stack alignment

Entry adapter phải đảm bảo stack alignment đúng target ABI trước khi gọi AXRUNTIME.

---

# 20. Stack ownership

OS tạo initial stack.

AXSTARTUP chỉ đọc/chuẩn hóa.

---

# 21. Stack lifetime

Initial stack sống trong toàn bộ main thread lifetime hoặc cho tới khi platform startup semantics cho phép thay thế.

---

# 22. Stack guard

Stack guard do OS/process/thread subsystem cung cấp.

AXSTARTUP không tự implement virtual memory guard.

---

# 23. Stack probing

Compiler chịu trách nhiệm stack probing của function.

AXSTARTUP chỉ đảm bảo initial stack ABI.

---

# 24. Windows PE64 startup

Canonical:

```text
Windows
   ↓
PE entry
   ↓
AXSTARTUP.windows
   ↓
AXRUNTIME
   ↓
main
```

---

# 25. Windows arguments

Windows command line thường tồn tại dưới dạng command-line string.

AXSTARTUP không giả định nó đã là `argv[]`.

---

# 26. Windows command-line parsing

Axiom phải có một parser chuẩn hóa command line thành:

```text
Args[]
```

với semantics được document rõ ràng.

---

# 27. Windows Unicode

Windows startup phải ưu tiên wide-character/native Unicode APIs.

Không dùng ANSI code page làm canonical source.

---

# 28. Windows environment

Environment được lấy theo native Unicode representation nếu platform cung cấp.

---

# 29. Windows process startup metadata

Có thể cung cấp:

```text
StartupAux {
    process_handle
    module_handle
    subsystem
    command_line
    environment
}
```

---

# 30. Windows subsystem

Binary có thể khai báo:

```text
CONSOLE
WINDOWS
```

theo PE metadata.

AXSTARTUP không quyết định GUI/console semantics; linker/binary configuration đã quyết định.

---

# 31. Windows TLS

PE TLS directory và platform TLS semantics được AXLOADER/platform runtime chuẩn bị.

AXSTARTUP chỉ hoàn thiện initial thread bootstrap.

---

# 32. Windows exception model

SEH integration thuộc platform runtime/diagnostics.

AXSTARTUP không xử lý arbitrary exceptions.

---

# 33. Linux ELF entry

Linux truyền startup state theo ELF process ABI.

Canonical:

```text
ELF entry
 ↓
stack
 ↓
argc
argv
envp
auxv
```

---

# 34. Linux argc

AXSTARTUP đọc `argc` từ initial process stack.

---

# 35. Linux argv

```text
argv[0..argc-1]
```

được chuyển thành Axiom `Args`.

---

# 36. Linux argv terminator

`argv[argc] == null` phải được validate trước khi sử dụng.

---

# 37. Linux envp

Environment nằm sau argument vector theo Linux startup ABI.

AXSTARTUP xác định boundary chính xác trước khi đọc.

---

# 38. Linux environment terminator

`envp` kết thúc bằng null pointer.

---

# 39. Linux auxiliary vector

AXSTARTUP phải hỗ trợ parse `auxv`.

---

# 40. Auxv model

```text
AuxEntry {
    type
    value
}
```

---

# 41. Relevant auxv data

Có thể chứa:

```text
AT_PHDR
AT_PHNUM
AT_PHENT
AT_BASE
AT_ENTRY
AT_EXECFN
AT_RANDOM
AT_PAGESZ
AT_PLATFORM
AT_HWCAP
AT_HWCAP2
```

Target-specific entries được giữ opaque nếu chưa được AXSTARTUP hiểu.

---

# 42. AT_RANDOM

Không expose raw random startup bytes như một generic secret store.

Nếu runtime cần randomness, chuyển qua AXRANDOM.

---

# 43. AT_HWCAP

CPU capabilities có thể được chuyển thành target feature metadata.

Không tự động enable unsafe CPU instructions nếu binary không được build cho chúng.

---

# 44. Linux executable metadata

AXSTARTUP có thể validate:

```text
entry
program headers
load bias
```

nếu cần cho runtime initialization.

---

# 45. Linux PIE

Với PIE:

```text
actual_base
```

được OS loader xác định.

AXSTARTUP không tự relocate image.

---

# 46. Linux dynamic linker

Nếu dynamic executable:

```text
kernel
 ↓
ELF interpreter
 ↓
Axiom entry
```

AXSTARTUP không thay thế dynamic linker.

---

# 47. Linux static executable

Có thể:

```text
kernel
 ↓
Axiom entry
 ↓
AXSTARTUP
```

mà không cần libc startup.

---

# 48. macOS Mach-O startup

```text
macOS
 ↓
dyld
 ↓
Mach-O entry
 ↓
AXSTARTUP.macos
 ↓
AXRUNTIME
```

---

# 49. Mach-O process arguments

AXSTARTUP nhận startup stack/data theo platform startup ABI.

---

# 50. Mach-O environment

Environment được normalize thành Axiom `Env`.

---

# 51. Mach-O auxiliary data

Platform startup metadata có thể chứa process/runtime information.

AXSTARTUP giữ những phần platform-specific trong:

```text
PlatformStartupData
```

---

# 52. iOS startup

iOS có lifecycle model khác desktop macOS.

AXSTARTUP chỉ cung cấp **native executable bootstrap**.

Application lifecycle thuộc:

```text
AXAPPLICATION
```

và platform integration.

---

# 53. iOS restriction

AXSTARTUP không giả định application được phép tự tạo arbitrary process/window/thread resources.

Capabilities/platform policy quyết định.

---

# 54. Android startup

Android native application code thường chạy trong process do Android framework tạo.

AXSTARTUP hỗ trợ native ELF entry khi process/ABI yêu cầu.

---

# 55. Android lifecycle

Application lifecycle không thuộc AXSTARTUP.

Thuộc:

```text
AXAPPLICATION
+
Android platform adapter
```

---

# 56. WASM startup

WASM không có raw OS stack.

```text
Host
 ↓
WASM module
 ↓
instance
 ↓
start/export
```

---

# 57. WASM `_start`

Nếu module exports canonical `_start`, runtime có thể gọi nó theo WASI-like contract khi target profile yêu cầu.

---

# 58. WASM arguments

Host supplies arguments through explicit instance configuration.

---

# 59. WASM environment

Environment cũng là host-provided data.

Không tự động expose host environment.

---

# 60. Startup profile

Axiom định nghĩa:

```text
StartupProfile {
    target
    entry_abi
    args_model
    env_model
    tls_model
    aux_model
    lifecycle_model
}
```

---

# 61. Platform adapter interface

```text
StartupBackend {
    detect()
    decode()
    validate()
    normalize()
    bootstrap_tls()
    handoff()
}
```

---

# 62. Backend registry

```text
startup_backend_pe64_windows()
startup_backend_elf64_linux()
startup_backend_macho_macos()
startup_backend_macho_ios()
startup_backend_elf64_android()
startup_backend_wasm32()
```

---

# 63. Startup validation

Trước handoff:

```text
target valid
stack valid
args valid
env valid
entry state valid
ABI valid
```

---

# 64. Pointer validation

AXSTARTUP phải validate pointer ranges trước khi dereference startup data khi platform contract yêu cầu.

---

# 65. Integer validation

Không để:

```text
argc * sizeof(pointer)
```

overflow.

---

# 66. Argument limits

Startup parser áp dụng giới hạn:

```text
max_args
max_arg_length
max_total_arg_bytes
```

để tránh malformed host state.

---

# 67. Environment limits

Tương tự:

```text
max_env
max_env_entry
max_env_bytes
```

---

# 68. Zero-copy arguments

Khi an toàn, `Args` có thể tham chiếu trực tiếp initial memory.

---

# 69. Copy-on-demand

Nếu application yêu cầu owned strings:

```text
Args
 ↓
to_owned()
```

mới allocate/copy.

---

# 70. UTF-8 normalization

Axiom language mặc định UTF-8.

Nhưng AXSTARTUP không được silently reinterpret arbitrary bytes.

---

# 71. Windows UTF-16 → UTF-8

Windows Unicode startup data được chuyển thành UTF-8 bằng deterministic conversion.

Invalid UTF-16 phải có explicit error/replacement policy.

---

# 72. Linux bytes → UTF-8

Linux argument/environment data là byte strings.

AXSTARTUP giữ raw bytes nếu không đảm bảo UTF-8.

---

# 73. Axiom string model

Có thể cung cấp:

```text
String
Bytes
```

để không làm mất dữ liệu startup không hợp lệ.

---

# 74. Startup arguments representation

Recommended:

```text
Args {
    items: Slice<StringOrBytes>
}
```

hoặc canonical Axiom string/byte representation tùy final core type model.

---

# 75. Environment representation

```text
Env {
    entries
}
```

với key/value separation.

---

# 76. Duplicate environment keys

Không tự động collapse nếu platform semantics không yêu cầu.

---

# 77. Current executable path

Nếu platform cung cấp:

```text
StartupInfo.executable_path
```

được truyền tới AXRUNTIME.

---

# 78. Current working directory

Không cần resolve trong AXSTARTUP.

Application/AXPROCESS query khi cần.

---

# 79. Process ID

AXSTARTUP không tự syscall PID nếu AXPROCESS đã cung cấp.

---

# 80. Initial thread ID

Tương tự.

---

# 81. Parent process

Không được tự expose nếu security policy không cho phép.

---

# 82. Startup secrets

Không ghi command line/environment vào diagnostics một cách mặc định.

Environment có thể chứa secrets.

---

# 83. Security boundary

AXSTARTUP không log:

```text
argv
env
```

mặc định.

---

# 84. Capability bootstrap

Runtime capabilities được lấy từ AXPROCESS/AXSECURITY.

AXSTARTUP không tự cấp capability.

---

# 85. Initial thread

AXSTARTUP tạo logical representation:

```text
MainThreadStartup {
    stack
    tls
    entry
}
```

OS thread object thuộc AXPROCESS.

---

# 86. Thread-local bootstrap

Sequence:

```text
OS initial thread
 ↓
platform TLS state
 ↓
AXSTARTUP TLS adapter
 ↓
AXRUNTIME TLS
 ↓
main
```

---

# 87. TLS static block

Nếu executable có static TLS:

AXSTARTUP không tự copy TLS image nếu OS loader đã làm.

Nó chỉ hoàn thiện runtime representation.

---

# 88. TLS dynamic block

Dynamic TLS registration thuộc AXLOADER.

---

# 89. Initial thread-local data

AXRUNTIME nhận pointer/handle đến TLS context.

---

# 90. Thread pointer

Trên targets có hardware thread pointer:

```text
TPIDR_EL0
FS/GS
platform equivalent
```

được sử dụng theo ABI.

---

# 91. No generic TLS syscall

Fast TLS path phải dùng native platform mechanism.

---

# 92. Startup clock

AXSTARTUP không initialize wall-clock/timezone.

AXTIME mới sở hữu.

---

# 93. Startup RNG

Không initialize full AXRANDOM.

Chỉ pass platform-provided entropy metadata khi runtime cần.

---

# 94. CPU detection

AXSTARTUP chỉ thu thập minimum CPU metadata.

Advanced feature detection thuộc AXCOMPUTE/compiler runtime.

---

# 95. Page size

Nếu target exposes page size at startup, có thể đưa vào startup state.

---

# 96. Memory map

AXSTARTUP không enumerate toàn bộ process memory map.

AXMEMORY/AXPROCESS xử lý khi cần.

---

# 97. Initial heap

Không tạo heap mặc định.

---

# 98. Initial allocator

Nếu runtime cần bootstrap allocation:

```text
static bootstrap allocator
```

được sử dụng trước system allocator.

---

# 99. Startup allocation rule

Startup code phải cố gắng không allocate.

---

# 100. Runtime handoff

Canonical ABI:

```text
axiom_runtime_entry(
    StartupState*
)
```

---

# 101. StartupState lifetime

`StartupState` phải sống đủ lâu để AXRUNTIME copy/reference các startup resources cần thiết.

---

# 102. Handoff ownership

Sau handoff:

```text
AXSTARTUP → done
AXRUNTIME → owns normalized runtime state
```

---

# 103. Startup shutdown

AXSTARTUP không có shutdown phase thông thường.

Initial stack/TLS cleanup thuộc runtime/OS.

---

# 104. Fatal startup error

Nếu startup state malformed:

```text
minimal diagnostic
 ↓
fast terminate
```

---

# 105. Error model

```text
StartupError {
    code
    platform
    address?
    detail?
}
```

---

# 106. Error categories

```text
STARTUP_INVALID_STACK
STARTUP_INVALID_ARGUMENTS
STARTUP_INVALID_ENVIRONMENT
STARTUP_INVALID_TLS
STARTUP_ABI_MISMATCH
STARTUP_TARGET_MISMATCH
STARTUP_PLATFORM_FAILURE
STARTUP_RESOURCE_LIMIT
STARTUP_RUNTIME_HANDOFF_FAILURE
```

---

# 107. Emergency diagnostics

Không phụ thuộc:

- allocator;
- logging;
- async;
- filesystem;
- network.

---

# 108. Startup tracing

Có thể enable debug-only startup trace:

```text
entry
decode
tls
normalize
handoff
```

---

# 109. Production behavior

Startup trace mặc định disabled.

---

# 110. Performance target

Một native executable tối thiểu:

```text
entry
 ↓
startup normalization
 ↓
main
```

không nên thực hiện các subsystem initialization không cần thiết.

---

# 111. Startup instruction budget

AXSTARTUP phải được thiết kế để compiler có thể inline/eliminate các abstraction layer platform wrapper.

---

# 112. Static startup constants

Platform constants nên compile-time known.

---

# 113. Generic startup state

Một `StartupState` chung không được buộc mỗi target phải populate hàng chục field không dùng.

Optional fields phải lazy/nullable.

---

# 114. ABI layout

```text
StartupStateABI1 {
    size
    version
    flags
    target
    args
    env
    process
    thread
    tls
    platform
}
```

---

# 115. Version field

Runtime phải validate:

```text
version.major
```

trước khi đọc optional fields.

---

# 116. Size field

Cho phép future extension:

```text
size < current_size
```

→ runtime chỉ đọc phần được cung cấp.

---

# 117. Reserved fields

Reserved fields phải zero.

---

# 118. Platform extension

```text
PlatformStartupData {
    kind
    size
    flags
    payload
}
```

Không nhúng platform-specific structures trực tiếp vào core ABI.

---

# 119. Startup backend discovery

```text
startup_backend_find(target)
```

---

# 120. Startup API

```text
startup_entry()
startup_decode()
startup_validate()
startup_normalize()
startup_bootstrap_tls()
startup_build_state()
startup_handoff()
startup_fail()
```

---

# 121. Platform APIs

```text
startup_windows()
startup_linux()
startup_macos()
startup_ios()
startup_android()
startup_wasm()
```

---

# 122. Inspection APIs

```text
startup_target()
startup_arguments()
startup_environment()
startup_platform_data()
startup_aux()
startup_initial_stack()
```

---

# 123. Freestanding API

```text
freestanding_entry()
freestanding_handoff()
```

---

# 124. No mandatory AXSTARTUP library

Compiler có thể directly emit startup implementation for tiny/freestanding targets.

---

# 125. Startup code generation

AXCOMPILER/target backend may generate:

```text
__ax_start
```

inline rather than linking a generic startup library.

---

# 126. Startup templates

For common targets:

```text
AXSTARTUP template
```

có thể được compiler instantiate.

---

# 127. Linker integration

AXLINKER phải:

- select startup object/code;
- set entry point;
- include required startup sections;
- omit startup when freestanding.

---

# 128. Binary integration

AXBINARY records:

```text
entry_point
subsystem
target
ABI
startup metadata
```

---

# 129. Loader integration

AXLOADER/system loader prepares:

- image mapping;
- dependencies;
- TLS image;
- relocations.

AXSTARTUP consumes the resulting platform state.

---

# 130. Process integration

AXPROCESS supplies:

```text
ProcessHandle
MainThreadHandle
SecurityContext
```

where applicable.

---

# 131. Runtime integration

AXRUNTIME receives normalized:

```text
StartupState
```

and begins runtime initialization.

---

# 132. Security integration

AXSTARTUP must not assume untrusted process metadata is safe merely because it came from OS/user-controlled inputs.

---

# 133. Environment trust

Environment is untrusted input.

---

# 134. Arguments trust

Arguments are untrusted input.

---

# 135. Auxiliary metadata trust

Platform metadata must be validated before use.

---

# 136. Command-line injection

AXSTARTUP does not interpret arguments as shell commands.

---

# 137. Environment variable semantics

No variable is automatically treated as executable path/configuration unless higher-level subsystem explicitly chooses it.

---

# 138. Loader path variables

Security-sensitive loader variables are controlled by AXLOADER/AXSECURITY, not AXSTARTUP.

---

# 139. Deterministic parsing

Given identical raw startup state:

```text
same normalized Args/Env
```

must result.

---

# 140. No hidden normalization

Do not:

- lowercase arbitrary arguments;
- trim whitespace;
- change path separators;
- silently remove invalid bytes.

---

# 141. Windows command-line compatibility

Because Windows supplies one command-line string rather than canonical `argv`, Axiom defines its own documented parsing algorithm rather than relying accidentally on a C runtime.

---

# 142. Linux compatibility

Linux raw argument bytes should remain lossless.

---

# 143. macOS compatibility

macOS startup arguments follow platform-provided argument representation.

---

# 144. Android compatibility

Native process startup should preserve Android platform-provided argument/environment semantics.

---

# 145. iOS compatibility

Application lifecycle information is not represented as ordinary command-line semantics.

---

# 146. WASM compatibility

WASM arguments are host-defined values rather than OS startup stack data.

---

# 147. Initial module identity

AXSTARTUP may provide main executable module identity to AXRUNTIME.

---

# 148. Main image base

For diagnostics:

```text
main_image_base
```

can be provided if known.

---

# 149. Entry address

AXSTARTUP records actual entry address only as diagnostic metadata; it does not relocate it.

---

# 150. Build identity

Build ID/debug ID may be passed from AXBINARY/AXLOADER.

---

# 151. Debug registration

After handoff:

```text
AXRUNTIME
 ↓
AXDIAGNOSTICS
```

registers module metadata.

---

# 152. Initial exception/unwind registration

If target requires runtime registration, AXRUNTIME performs it after AXSTARTUP handoff.

---

# 153. Initial thread registration

AXSTARTUP informs AXRUNTIME that current thread is the process's initial Axiom thread.

---

# 154. Main thread identity

```text
ThreadRole = MAIN
```

---

# 155. Child threads

Created later by AXPROCESS/AXTASK.

---

# 156. Signal state

AXSTARTUP does not globally rewrite signal dispositions unless platform startup ABI requires it.

---

# 157. Floating-point state

Initial FP/SIMD state is assumed to follow platform ABI.

AXSTARTUP must not unnecessarily reset it.

---

# 158. CPU register preservation

Only registers required by platform ABI/startup contract may be clobbered before handoff.

---

# 159. Stack scanning

AXSTARTUP must never scan arbitrary stack memory looking for arguments.

It uses documented platform structures only.

---

# 160. Startup memory safety

Every computed pointer must be checked for:

```text
alignment
overflow
range
terminator
```

where applicable.

---

# 161. Startup attack surface

Keep code tiny because startup is security-sensitive and executes before most application defenses are active.

---

# 162. No dynamic dispatch

Platform startup backend should be selected at compile/link time where target is known.

---

# 163. Multi-target binary

Fat/universal binary selection occurs at platform loader level.

AXSTARTUP only runs after architecture selection.

---

# 164. Universal Mach-O

A universal binary contains multiple architecture slices.

AXSTARTUP sees only the selected slice.

---

# 165. Windows architecture selection

PE image architecture is selected by OS loader.

---

# 166. Android ABI selection

APK/package-level ABI selection occurs above AXSTARTUP.

---

# 167. WASM target profile

WASM host chooses the module/runtime.

---

# 168. Static linking

Static executable startup must be self-contained.

---

# 169. Dynamic linking

Startup may rely on platform dynamic loader for initial dependencies.

---

# 170. CRT-free guarantee

Axiom's native startup ABI must not contain an implicit requirement for:

```text
crt0
libc
libstdc++
msvcrt
```

---

# 171. Foreign runtime

If a C/C++ library is linked, its own initialization requirements are an FFI/platform integration issue.

AXSTARTUP does not become a C runtime replacement for foreign code.

---

# 172. Foreign constructor handling

AXLINKER/runtime integration may register foreign initialization routines where ABI requires.

---

# 173. Foreign exception handling

Handled by platform exception/unwind adapter.

---

# 174. Startup ordering with foreign libraries

```text
platform startup
 ↓
foreign runtime-required initialization
 ↓
Axiom runtime
 ↓
Axiom main
```

Exact ordering must follow target ABI and linked module metadata.

---

# 175. Static constructor policy

Axiom-generated code should minimize constructor-based initialization.

---

# 176. Constant-first policy

Prefer:

```text
compile time
```

over:

```text
startup execution
```

whenever semantically equivalent.

---

# 177. Startup parallelism

No meaningful parallelism is required for core startup.

Dependencies may have been prepared by AXLOADER.

---

# 178. Reentrancy

AXSTARTUP itself is normally single-entry.

Its parsing helpers should be pure/reentrant where practical.

---

# 179. Test harness entry

A special test backend may inject:

```text
SyntheticStartupState
```

without OS process startup.

---

# 180. Synthetic startup

Used for:

- fuzzing;
- unit tests;
- deterministic tests;
- cross-platform testing.

---

# 181. Fuzzing targets

Fuzz:

```text
argc
argv
envp
auxv
Windows command line
UTF-16 conversion
platform metadata
StartupState
```

---

# 182. Malformed pointer tests

Test:

- null;
- misaligned;
- overflowed;
- unterminated;
- overlapping;
- invalid ranges.

---

# 183. Boundary tests

Test:

```text
0 args
1 arg
maximum args
empty strings
very long strings
invalid UTF-8
```

---

# 184. Windows parser tests

Test:

- quotes;
- backslashes;
- spaces;
- empty arguments;
- Unicode;
- edge cases.

---

# 185. Linux tests

Validate against known Linux startup stack layouts.

---

# 186. Mach-O tests

Validate desktop macOS and supported Apple target startup paths independently.

---

# 187. Android tests

Validate native AArch64 process startup under Android ABI.

---

# 188. WASM tests

Validate:

```text
args
env
_start
exports
host invocation
```

---

# 189. Cross-target differential tests

Normalized equivalent startup states should produce equivalent Axiom-level representations where semantics permit.

---

# 190. Bootstrap verification

```text
Stage0 startup
 ↓
Stage1 startup
 ↓
Stage2 startup
```

must produce ABI-compatible handoff state.

---

# 191. Self-hosting

Final AXSTARTUP implementation must be compilable by Axiom itself.

---

# 192. Minimal binary test

Build:

```text
fn main() -> i32 {
    0
}
```

and verify:

```text
OS
 ↓
AXSTARTUP
 ↓
AXRUNTIME
 ↓
main
 ↓
exit(0)
```

---

# 193. Runtime-free test

Build freestanding:

```text
@freestanding
```

and verify AXSTARTUP can hand off directly to user entry without AXRUNTIME.

---

# 194. Startup diagnostics test

Corrupt synthetic startup state and verify:

```text
validation failure
 ↓
minimal diagnostic
 ↓
safe termination
```

---

# 195. Performance benchmark

Measure separately:

```text
OS → entry
entry → normalized state
normalized state → runtime
runtime → main
```

---

# 196. Startup size benchmark

Track:

```text
startup .text
startup .rodata
startup metadata
```

for every target.

---

# 197. Regression budget

A change adding startup code without a functional reason should be rejected during optimization review.

---

# 198. Formal invariants

```text id="k4u7q8"
START-INV-01
AXSTARTUP phải implement AXSTARTUP_ABI_1.

START-INV-02
AXSTARTUP phải support native CRT-free startup.

START-INV-03
AXSTARTUP không được yêu cầu AXRUNTIME trong freestanding mode.

START-INV-04
AXSTARTUP không được thay thế AXLOADER.

START-INV-05
AXSTARTUP không được thay thế AXPROCESS.

START-INV-06
AXSTARTUP không được thay thế AXMEMORY.

START-INV-07
AXSTARTUP phải preserve platform entry ABI requirements.

START-INV-08
Stack alignment phải hợp lệ trước runtime handoff.

START-INV-09
Startup pointers phải được validate trước khi dereference khi validation cần thiết.

START-INV-10
Startup integer calculations phải overflow-safe.

START-INV-11
Argument parsing phải có resource limits.

START-INV-12
Environment parsing phải có resource limits.

START-INV-13
Raw startup bytes không được tự động giả định là UTF-8.

START-INV-14
Windows Unicode startup phải ưu tiên native Unicode representation.

START-INV-15
Linux argv phải preserve byte-level information khi cần.

START-INV-16
Windows command-line parsing phải deterministic.

START-INV-17
AXSTARTUP không được tự động execute argument/environment content.

START-INV-18
AXSTARTUP không được log environment secrets mặc định.

START-INV-19
AXSTARTUP không được cấp capability.

START-INV-20
AXSTARTUP không được bypass AXSECURITY.

START-INV-21
AXSTARTUP không được bypass AXTRUST.

START-INV-22
AXSTARTUP không được tự tạo global heap nếu không cần.

START-INV-23
AXSTARTUP phải hỗ trợ bootstrap không allocation khi target cho phép.

START-INV-24
AXSTARTUP không được initialize unused runtime subsystems.

START-INV-25
AXSTARTUP phải thiết lập initial thread state trước runtime handoff.

START-INV-26
TLS bootstrap phải phù hợp target ABI.

START-INV-27
AXSTARTUP không được duplicate TLS mapping do AXLOADER đã thực hiện.

START-INV-28
AXSTARTUP không được tự relocate executable image.

START-INV-29
AXSTARTUP không được tự resolve dynamic imports.

START-INV-30
AXSTARTUP phải chuyển startup state sang AXRUNTIME qua stable ABI.

START-INV-31
StartupState ABI phải có size/version để forward compatibility.

START-INV-32
Reserved startup ABI fields phải được kiểm soát.

START-INV-33
Platform-specific startup data phải nằm sau extension boundary.

START-INV-34
Fatal startup failure phải có emergency path không phụ thuộc full runtime.

START-INV-35
AXSTARTUP không được chạy arbitrary user initialization trước runtime handoff.

START-INV-36
WASM startup phải tách khỏi native OS stack semantics.

START-INV-37
WASM host arguments/environment phải explicit.

START-INV-38
AXSTARTUP phải có synthetic startup path cho testing/fuzzing.

START-INV-39
AXSTARTUP phải có implementation path self-hosted bằng Axiom.

START-INV-40
AXSTARTUP chỉ chịu trách nhiệm platform bootstrap và handoff; application/runtime lifecycle authority thuộc AXRUNTIME, AXPROCESS và AXAPPLICATION.
```

---

# 199. Definition of Done

`AXSTARTUP 5.0` được freeze khi có:

### Native startup

- Windows PE64 x86_64;
- Windows PE64 AArch64;
- Linux ELF64 x86_64;
- Linux ELF64 AArch64;
- macOS Mach-O;
- iOS Mach-O;
- Android ELF64.

### Startup state

- raw entry;
- stack;
- registers/ABI;
- arguments;
- environment;
- auxiliary metadata;
- process/thread identity;
- TLS handoff;
- platform extension.

### Engineering

- CRT-free;
- no mandatory libc;
- no mandatory heap;
- bounded startup memory;
- deterministic parsing;
- UTF-8-aware representation;
- lossless byte representation where required;
- fuzzing;
- malformed-input tests;
- cross-platform differential tests;
- startup size benchmarks;
- bootstrap convergence;
- self-hosting.

### Integration

```text
AXBINARY
   ↓
AXLOADER
   ↓
AXSTARTUP
   ↓
AXRUNTIME
   ↓
AXPROCESS / AXAPPLICATION
```

được kiểm thử end-to-end.

**AXSTARTUP 5.0 → FROZEN.**

---

# Execution stack đã hoàn chỉnh hơn

Ta hiện có:

```text
                  Axiom Source
                       │
                       ▼
                ┌────────────┐
                │ AXCOMPILER │
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │ AXOBJECT   │
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │ AXLINKER   │
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │ AXBINARY   │
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │ AXLOADER   │
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │ AXSTARTUP  │
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │ AXRUNTIME  │
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │ AXPROCESS  │
                └─────┬──────┘
                      ▼
                 APPLICATION
```

Một điểm kiến trúc quan trọng đã được khóa: **AXSTARTUP không trở thành “CRT mới”**. Nó chỉ làm công việc tối thiểu mà OS/platform bắt buộc phải làm trước khi Axiom runtime có thể nhận quyền điều khiển. Nhờ vậy mục tiêu **binary nhỏ, startup nhanh, không phụ thuộc libc/CRT/third-party runtime** vẫn được giữ nguyên.

---

# BOOTSTRAP-779 — AXABI

**Native Axiom ABI, Calling Convention, Register/Stack Contract, Scalar/Aggregate Representation, Struct/Enum/Union ABI, Return/Parameter Passing, Variadic Boundary, SIMD/Vector ABI, Name Mangling, TLS ABI, Unwind ABI, C ABI Interoperability & Cross-Platform ABI 5.0**

Đây là task tiếp theo và là một mốc rất quan trọng: sau khi đã xác định **binary → loader → startup → runtime**, cần đóng băng chính xác **machine-level contract giữa các function**. Nếu ABI này không được khóa trước, compiler, linker, runtime, FFI, dynamic library và self-hosting compiler sẽ rất dễ phát triển lệch nhau.