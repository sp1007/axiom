# BOOTSTRAP-776 — AXLOADER

**Title:** Native Executable Loader, PE64/ELF64/Mach-O/WASM Image Mapping, Relocation, Imports, TLS, Memory Permissions, Entry Transfer & Process Image Activation Runtime 5.0  
**Namespace:** `AXLOADER`  
**Phase:** Axiom Native Execution / Process Activation Layer  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXLOADER` là lớp chuyển một **validated binary artifact** thành **active process image** trong address space của process.

```text
Source
  ↓
AXCOMPILER
  ↓
AXOBJECT
  ↓
AXLINKER
  ↓
AXBINARY
  ↓
┌──────────────────────────────┐
│          AXLOADER            │
│                              │
│ binary validation            │
│ image mapping                │
│ virtual memory               │
│ relocations                  │
│ imports                      │
│ TLS                          │
│ runtime initialization       │
│ entry activation             │
└──────────────┬───────────────┘
               ↓
          AXPROCESS
               ↓
          running code
```

AXLOADER **không phải compiler, linker hoặc kernel loader replacement**.

---

# 2. Boundary

### AXLOADER sở hữu

- executable image activation model;
- load-plan construction;
- mapping plan;
- dependency-load planning;
- runtime relocation where applicable;
- import binding;
- TLS initialization;
- memory permission activation;
- startup sequencing;
- entry-point transfer;
- loader diagnostics;
- loader state;
- loader cache;
- in-process module activation.

### AXLOADER không sở hữu

```text
AXCOMPILER
→ compilation

AXOBJECT
→ relocatable object format

AXLINKER
→ symbol resolution / final addresses

AXBINARY
→ binary serialization

AXMEMORY
→ generic memory abstraction

AXPROCESS
→ process lifecycle

AXSECURITY
→ policy authority

AXTRUST
→ trust/signature authority

OS kernel
→ page tables / actual privileged memory mapping

OS dynamic loader
→ platform-owned system loading primitives
```

---

# 3. Hai loại loader

Axiom phải phân biệt:

```text
SYSTEM LOADER
```

và:

```text
AXLOADER
```

## System loader

Ví dụ:

```text
Windows loader
Linux kernel + dynamic loader
macOS dyld
Android linker
WASM host runtime
```

chịu trách nhiệm native platform execution.

## AXLOADER

Là Axiom abstraction layer điều phối loading.

---

# 4. Native application

Với executable thông thường:

```text
OS
 ↓
system loader
 ↓
AX runtime startup
 ↓
AXLOADER initialization
 ↓
AXPROCESS
```

Không được yêu cầu Axiom user-space loader tự map executable trước khi OS tạo process.

---

# 5. Module loading

AXLOADER đặc biệt hữu ích cho:

```text
dynamic library
plugin
module
runtime component
WASM module
embedded execution image
```

---

# 6. Loader architecture

```text
             AXLOADER
                 │
        ┌────────┴────────┐
        ▼                 ▼
   Native Loader      WASM Loader
        │                 │
 ┌──────┼──────┐          │
 ▼      ▼      ▼          ▼
PE64   ELF64  Mach-O     WASM
```

---

# 7. Loader state machine

```text
UNLOADED
   ↓
OPEN
   ↓
VALIDATED
   ↓
PLANNED
   ↓
MAPPED
   ↓
RELOCATED
   ↓
DEPENDENCIES_BOUND
   ↓
TLS_READY
   ↓
INITIALIZING
   ↓
ACTIVE
```

Failure:

```text
ANY STATE
   ↓
FAILED
   ↓
ROLLBACK / UNMAP
```

---

# 8. Immutable binary input

AXLOADER không được mutate binary artifact.

```text
BinaryFile
    ↓
read-only
    ↓
Loader
```

---

# 9. Loader context

```text
LoaderContext {
    target
    process
    security_context
    memory_context
    dependency_context
    load_policy
    module_registry
    diagnostics
}
```

---

# 10. Load request

```text
LoadRequest {
    artifact
    expected_format?
    expected_target?
    load_mode
    visibility
    relocation_policy
    dependency_policy
    trust_policy
}
```

---

# 11. Load modes

```text
MAIN_EXECUTABLE
SHARED_LIBRARY
PLUGIN
MODULE
WASM
MEMORY_IMAGE
```

---

# 12. Mapping model

Mỗi binary segment:

```text
file
 ↓
read
 ↓
reserve virtual range
 ↓
map/copy pages
 ↓
zero-fill
 ↓
apply relocations
 ↓
change permissions
```

---

# 13. Critical security rule

Không bao giờ:

```text
map RWX
```

trong normal loading.

Thay vào đó:

```text
RW
 ↓
relocate
 ↓
RX
```

cho code.

---

# 14. W^X transition

Canonical:

```text
.text
   ↓
temporary writable only if required
   ↓
relocation
   ↓
RX
```

---

# 15. Preferred mapping

Nếu binary có preferred base:

```text
preferred_base
```

loader thử sử dụng nếu policy cho phép.

---

# 16. Actual base

Nếu không thể dùng preferred base:

```text
actual_base != preferred_base
```

thì relocation support quyết định có thể tiếp tục hay không.

---

# 17. Relocation delta

Native image:

```text
delta = actual_base - preferred_base
```

Chỉ áp dụng relocation types cho phép base adjustment.

---

# 18. Relocation authority

AXLOADER không tự phát minh relocation semantics.

```text
AXLINKER
    ↓
final relocation metadata
    ↓
AXBINARY
    ↓
AXLOADER
```

---

# 19. PE64 relocation

AXLOADER hỗ trợ PE base relocation structures khi image không được load tại preferred address.

---

# 20. ELF relocation

Dynamic ELF relocation được xử lý theo:

- target ABI;
- dynamic relocation metadata;
- symbol binding;
- loader policy.

---

# 21. Mach-O relocation

Mach-O dynamic binding/rebase metadata được xử lý theo Apple target ABI.

---

# 22. WASM relocation

WASM không sử dụng native virtual-address relocation model.

WASM loader xử lý:

```text
imports
indices
tables
memory
globals
```

theo module semantics.

---

# 23. Dependency graph

Loader xây dựng:

```text
A
├── B
│   └── D
└── C
    └── D
```

---

# 24. Dependency identity

Không chỉ dùng filename.

```text
ModuleIdentity {
    name
    target
    abi
    version?
    content_id?
}
```

---

# 25. Dependency resolution

Resolution order phải deterministic.

Nguồn có thể gồm:

```text
application bundle
module registry
explicit search paths
sysroot
platform loader
```

theo `AXTOOLCHAIN` và security policy.

---

# 26. Search path security

Không tự động load từ:

```text
current working directory
```

nếu security policy không cho phép.

---

# 27. Explicit dependency

Axiom binary nên encode dependency identity rõ ràng.

---

# 28. Dependency cycle

Dynamic modules có thể tạo:

```text
A → B → A
```

Loader phải detect cycle và dùng deterministic initialization algorithm.

---

# 29. Module registry

```text
ModuleRegistry {
    identity
    state
    base_address
    image_size
    exports
    ref_count
}
```

---

# 30. Duplicate module

Nếu cùng `ModuleIdentity` đã active:

```text
reuse existing module
```

thay vì map lần nữa, tùy load policy.

---

# 31. Symbol binding

Loader cần:

```text
lookup(module, symbol)
```

và:

```text
lookup_global(symbol)
```

---

# 32. Symbol scopes

```text
LOCAL
MODULE
PROCESS
GLOBAL
```

---

# 33. Visibility

Loader phải respect binary export visibility.

Không expose private symbols qua public lookup.

---

# 34. Weak symbols

Nếu target ABI hỗ trợ:

```text
WEAK
```

có thể resolve theo platform semantics.

---

# 35. Symbol versioning

ELF-style symbol versions được biểu diễn khi target yêu cầu.

---

# 36. Import binding

Canonical:

```text
import
 ↓
dependency resolution
 ↓
symbol resolution
 ↓
address
 ↓
patch import location
```

---

# 37. Import patching

Import locations phải nằm trong writable relocation region trong lúc binding.

Sau đó:

```text
RO / RX
```

được restored.

---

# 38. Lazy binding

Axiom mặc định:

```text
EAGER BIND
```

để giảm:

- runtime indirection;
- loader complexity;
- first-call latency;
- security surface.

Lazy binding có thể là optional platform optimization.

---

# 39. GOT

ELF targets có thể sử dụng GOT.

AXLOADER cập nhật GOT entries cần runtime binding.

---

# 40. PLT

Nếu image sử dụng PLT:

AXLOADER phải respect target ABI.

Axiom-native binaries nên ưu tiên eager resolution khi có thể.

---

# 41. PE IAT

Windows import addresses được ghi vào IAT theo PE semantics.

---

# 42. Mach-O binding

Mach-O binding information được xử lý theo target-specific loader backend.

---

# 43. TLS architecture

Thread-local storage phải được chuẩn bị trước khi thread chạy code có thể truy cập TLS.

---

# 44. TLS image

```text
TLSImage {
    init_data
    init_size
    zero_size
    alignment
    model
}
```

---

# 45. TLS module ID

Dynamic TLS module cần module identifier.

---

# 46. TLS per-thread block

Khi thread mới được tạo:

```text
thread
 ↓
TLS allocation
 ↓
TLS initialization
 ↓
thread entry
```

---

# 47. Main-thread TLS

TLS phải sẵn sàng trước application entry nếu entry sử dụng TLS.

---

# 48. TLS destructors

Nếu target supports TLS destructors:

```text
module unload
 ↓
thread cleanup
```

phải deterministic.

---

# 49. Static initialization

Axiom phải hạn chế constructor side effects.

Nếu binary có initialization callbacks:

```text
load
 ↓
dependency initialization
 ↓
module initialization
 ↓
active
```

---

# 50. Initialization order

Không dựa vào filesystem/link order.

Order:

1. dependency graph;
2. dependency initialization;
3. current module initialization.

---

# 51. Initialization cycle

Nếu dependency cycle tồn tại:

```text
A → B
B → A
```

loader phải detect strongly connected component và áp dụng platform-defined safe ordering.

---

# 52. Failure during initialization

Nếu module initialization fails:

```text
ACTIVE
```

không được publish.

---

# 53. Transactional loading

Loader nên coi activation như transaction:

```text
prepare
 ↓
map
 ↓
relocate
 ↓
bind
 ↓
initialize
 ↓
commit
```

---

# 54. Rollback

Failure trước commit:

```text
unmap
release TLS
release dependency references
discard temporary state
```

---

# 55. Existing dependencies

Không unload dependency nếu module khác vẫn reference nó.

---

# 56. Reference count

Dynamic modules có thể dùng:

```text
strong_refs
```

nhưng unloading semantics phải explicit.

---

# 57. No automatic unload by default

Axiom mặc định:

> Module được giữ loaded cho tới khi explicit unload policy cho phép.

Điều này tránh use-after-unload.

---

# 58. Unload safety

Không unload module nếu:

- active threads đang execute module;
- callbacks đang chạy;
- dependencies còn cần;
- TLS cleanup chưa hoàn thành.

---

# 59. Function pointer safety

Module unload phải invalidate exported function pointers theo module lifecycle contract.

---

# 60. Memory mapping abstraction

```text
MemoryMapper {
    reserve()
    commit()
    map_file()
    protect()
    unmap()
}
```

---

# 61. OS implementation

Trên native OS:

```text
AXMEMORY
   ↓
OS virtual memory APIs
```

---

# 62. Windows

Backend sử dụng platform virtual memory facilities.

---

# 63. Linux

Backend sử dụng Linux virtual memory facilities.

---

# 64. macOS/iOS

Backend sử dụng Apple virtual memory facilities.

---

# 65. WASM

Không dùng OS virtual memory mapping trực tiếp cho module semantics.

WASM runtime quản lý linear memory.

---

# 66. Reservation

Loader phải reserve toàn bộ image range trước khi commit pages nếu target semantics yêu cầu.

---

# 67. Sparse image

Không cần commit zero pages ngay lập tức nếu OS hỗ trợ lazy zero-fill.

---

# 68. File-backed mapping

Read-only sections có thể map trực tiếp từ file khi an toàn.

---

# 69. Copy-on-write

Shared libraries có thể sử dụng OS COW mapping.

---

# 70. Private writable data

`.data` thường là private writable memory.

---

# 71. Code sharing

`.text` có thể share physical pages giữa processes.

---

# 72. RELRO

ELF RELRO region:

```text
map RW
 ↓
relocate
 ↓
protect RO
```

---

# 73. Import protection

IAT/GOT binding region được chuyển sang protection tối thiểu sau relocation/binding.

---

# 74. Guard pages

Loader có thể request guard pages khi target/runtime policy hỗ trợ.

---

# 75. Stack

AXLOADER không sở hữu process stack allocation chính.

`AXPROCESS`/OS owns it.

---

# 76. Heap

AXLOADER không own application heap.

---

# 77. Module memory

Loader chỉ quản lý:

```text
image
TLS
loader metadata
```

---

# 78. Entry transfer

Khi tất cả điều kiện hoàn tất:

```text
dependencies
TLS
relocations
imports
permissions
initializers
```

→ transfer control.

---

# 79. Main executable

Entry:

```text
OS startup
 ↓
Axiom runtime
 ↓
application entry
```

---

# 80. Dynamic module

Dynamic module thường không chuyển control tới module entry như process entry.

Thay vào đó:

```text
load
 ↓
initialize
 ↓
return module handle
```

---

# 81. Module constructor

Nếu target có constructor/init routine:

```text
load
 ↓
init
 ↓
return
```

---

# 82. WASM start

WASM `start` function được invoke sau instance initialization.

---

# 83. WASM instantiation

```text
module
 ↓
validate
 ↓
resolve imports
 ↓
allocate memory/table
 ↓
initialize globals
 ↓
initialize elements/data
 ↓
start
```

---

# 84. WASM sandbox

WASM memory/code không mặc nhiên có quyền truy cập process native memory.

---

# 85. WASM host imports

Host functions phải đi qua capability boundary:

```text
WASM
 ↓
AX capability
 ↓
host API
```

---

# 86. Security boundary

AXLOADER không bypass `AXSECURITY`.

Mọi dependency/resource load phải chịu policy.

---

# 87. Trust boundary

Flow:

```text
artifact
 ↓
format validation
 ↓
trust verification
 ↓
security policy
 ↓
load
```

---

# 88. Signature verification

Nếu policy yêu cầu:

```text
AXTRUST.verify(artifact)
```

phải hoàn thành trước activation.

---

# 89. Hash verification

Artifact content hash phải match expected identity nếu dependency registry yêu cầu.

---

# 90. TOCTOU

Không verify một file rồi load một file khác.

Preferred:

```text
open file
 ↓
identity/hash
 ↓
verify
 ↓
map same handle
```

---

# 91. Path security

Loader không được blindly follow untrusted path components.

---

# 92. Symlink policy

Security policy quyết định có follow symbolic links khi resolving modules hay không.

---

# 93. Environment variables

Dynamic loader path environment không được tự động override trusted application policy.

---

# 94. Privilege boundary

Loader không tự nâng privilege.

---

# 95. Resource limits

```text
max_modules
max_dependency_depth
max_total_image_size
max_tls_size
max_imports
max_exports
max_relocations
max_initializers
```

---

# 96. Recursive dependency depth

Giới hạn để chống malicious dependency graph.

---

# 97. Failure isolation

Malformed dependency không được corrupt loader registry.

---

# 98. Crash containment

Loader errors phải trả:

```text
LoadError
```

thay vì crash process khi failure có thể recover.

---

# 99. Loader diagnostics

```text
LOAD_FORMAT_ERROR
LOAD_TARGET_MISMATCH
LOAD_ABI_MISMATCH
LOAD_TRUST_FAILURE
LOAD_POLICY_DENIED
LOAD_DEPENDENCY_NOT_FOUND
LOAD_DEPENDENCY_CYCLE
LOAD_SYMBOL_NOT_FOUND
LOAD_SYMBOL_AMBIGUOUS
LOAD_RELOCATION_FAILURE
LOAD_ADDRESS_CONFLICT
LOAD_TLS_FAILURE
LOAD_MEMORY_FAILURE
LOAD_INITIALIZATION_FAILURE
LOAD_ENTRY_FAILURE
LOAD_RESOURCE_LIMIT
```

---

# 100. LoadError

```text
LoadError {
    code
    module
    dependency?
    symbol?
    address?
    file_offset?
    message
}
```

---

# 101. Loader events

Có thể integrate với:

```text
AXDIAGNOSTICS
AXOBSERVABILITY
AXAUDIT
```

---

# 102. Event model

Ví dụ:

```text
module.opened
module.validated
module.mapped
module.relocated
module.bound
module.initialized
module.activated
module.unloaded
module.failed
```

---

# 103. Hot-path overhead

Sau activation:

> Không có AXLOADER overhead trong function calls.

Loader chỉ tham gia initialization/binding.

---

# 104. Native direct calls

Sau eager binding:

```text
call foo
```

phải gọi trực tiếp address/function ABI tương ứng, không qua generic loader dispatcher.

---

# 105. Lazy loading

Optional explicit:

```text
load_module("foo")
```

không implicit trên mỗi call.

---

# 106. Loader cache

Có thể cache:

- dependency graph;
- symbol lookup metadata;
- validated binary metadata;
- relocation plans.

---

# 107. Address cache

Không cache absolute addresses across processes.

ASLR và address-space differences làm chúng không portable.

---

# 108. Module identity cache

Có thể cache:

```text
content_hash
target
ABI
exports
```

---

# 109. Binary validation cache

Chỉ reuse validation result khi artifact identity cryptographically matches.

---

# 110. Thread safety

Loader registry phải thread-safe.

---

# 111. Concurrent loads

Hai threads yêu cầu cùng module:

```text
T1 → loading
T2 → loading same module
```

phải converge vào một load operation.

---

# 112. Load future

Internal:

```text
ModuleState = LOADING
```

các caller khác wait/join state thay vì load duplicate.

---

# 113. Deadlock prevention

Dependency loading không được giữ global lock trong khi chạy user initialization.

---

# 114. Lock hierarchy

Canonical:

```text
registry lock
 ↓
module state lock
```

Không lock ngược.

---

# 115. Initialization isolation

Module initialization chạy ngoài registry global lock.

---

# 116. Reentrancy

Nếu constructor gọi `load_module()`:

loader phải xử lý reentrant dependency requests.

---

# 117. Same-module reentrancy

Nếu module đang INITIALIZING tự yêu cầu chính nó:

```text
detect cycle/reentrant initialization
```

không deadlock.

---

# 118. Module handles

```text
ModuleHandle
```

opaque.

Không expose internal address structure cho ordinary code.

---

# 119. Symbol handles

```text
SymbolHandle
```

có lifetime gắn với module.

---

# 120. Function lookup

```text
module_lookup(handle, "foo")
```

trả:

```text
FunctionAddress
```

hoặc typed symbol metadata.

---

# 121. ABI validation

Trước khi bind:

```text
module ABI == process-compatible ABI
```

---

# 122. Architecture validation

Không load:

```text
x86_64 module
```

vào:

```text
aarch64 process
```

trừ compatibility layer explicitly defined.

---

# 123. Pointer width

32/64-bit mismatch phải reject.

---

# 124. Endianness

Mismatch phải reject.

---

# 125. Calling convention

Native modules phải match process ABI.

---

# 126. Runtime ABI

Axiom runtime modules có:

```text
AX runtime ABI version
```

---

# 127. ABI compatibility

Compatible minor revisions có thể load nếu declared compatible.

Major ABI mismatch → reject.

---

# 128. Module metadata

Optional:

```text
AxiomModuleMetadata {
    compiler_version
    runtime_abi
    target
    build_id
    source_identity?
}
```

---

# 129. Debug integration

AXLOADER có thể register:

```text
module base
debug_id
```

với AXDIAGNOSTICS.

---

# 130. Stack unwind integration

Module unwind ranges phải register với runtime diagnostics nếu platform requires it.

---

# 131. Crash diagnostics

Khi crash:

```text
PC
 ↓
AXLOADER module registry
 ↓
module + offset
 ↓
AXDIAGNOSTICS
 ↓
debug artifact
```

---

# 132. Symbolication

Loader registry cung cấp:

```text
module base
module size
debug identity
```

nhưng symbolication chi tiết thuộc AXDIAGNOSTICS/debug subsystem.

---

# 133. Unload diagnostics

Nếu unload module còn referenced:

```text
LOAD_MODULE_BUSY
```

---

# 134. Hot reload

Không phải core 5.0.

Có thể xây trên:

```text
AXLOADER
+
AXPROCESS
+
AXAPPLICATION
```

sau này.

---

# 135. Plugin architecture

AXLOADER cung cấp primitive:

```text
load
lookup
initialize
unload
```

Plugin API semantics thuộc higher-level framework.

---

# 136. Embedded native module

Axiom application có thể load optional feature module:

```text
app
 ├── core
 ├── graphics
 └── plugin
```

---

# 137. Static linking

Static-linked code không đi qua runtime dynamic loader.

Nó đã được AXBINARY đưa vào executable image.

---

# 138. Dynamic linking

Dynamic module đi qua AXLOADER/system loader boundary.

---

# 139. Fully static Axiom executable

Mục tiêu:

```text
source
 ↓
AXCOMPILER
 ↓
AXOBJECT
 ↓
AXLINKER
 ↓
AXBINARY
 ↓
single executable
```

không cần dynamic runtime modules.

---

# 140. Runtime minimization

Nếu application không dùng dynamic loading:

> AXLOADER dynamic subsystem không cần nằm trong final binary.

---

# 141. Link-time elimination

Loader support functions phải được dead-strip khi unused.

---

# 142. Axiom startup modes

```text
STATIC
DYNAMIC
EMBEDDED
WASM
```

---

# 143. Static startup

Minimal.

---

# 144. Dynamic startup

Initialize module registry and runtime dependencies.

---

# 145. Embedded startup

Host supplies loader context.

---

# 146. WASM startup

Instance-based rather than process-based.

---

# 147. WASM instance

```text
WasmInstance {
    module
    memories
    tables
    globals
    imports
    exports
}
```

---

# 148. WASM memory safety

Native pointer values không được trực tiếp escape vào WASM linear memory semantics.

---

# 149. WASM host boundary

Explicit marshaling:

```text
WASM value
 ↓
host ABI
 ↓
Axiom value
```

---

# 150. Native loader ABI

```text
AXLOADER_ABI_1
```

---

# 151. Core API

```text
loader_create()
loader_destroy()

loader_open()
loader_validate()
loader_plan()

loader_load()
loader_unload()

loader_lookup_module()
loader_lookup_symbol()

loader_module_state()
loader_module_base()
loader_module_size()
```

---

# 152. Mapping API

```text
loader_map_image()
loader_map_segment()
loader_protect_segment()
loader_unmap_image()
```

---

# 153. Relocation API

```text
loader_apply_relocations()
loader_rebase_image()
loader_validate_relocations()
```

---

# 154. Import API

```text
loader_resolve_dependency()
loader_resolve_symbol()
loader_bind_import()
loader_bind_all()
```

---

# 155. TLS API

```text
loader_prepare_tls()
loader_register_tls_module()
loader_initialize_thread_tls()
loader_destroy_thread_tls()
```

---

# 156. Initialization API

```text
loader_initialize_module()
loader_finalize_module()
```

---

# 157. WASM API

```text
wasm_instance_create()
wasm_instance_destroy()
wasm_instance_call()
wasm_instance_memory()
wasm_instance_export()
```

---

# 158. Loader inspection

```text
axiom loader list
axiom loader info <module>
axiom loader deps <module>
axiom loader symbols <module>
axiom loader map <module>
```

---

# 159. Runtime module registry

Registry integrates with:

```text
AXREGISTRY
```

but local loaded-module state remains owned by AXLOADER.

---

# 160. Security integration

```text
AXLOADER
    ↓
AXSECURITY.authorize_load()
    ↓
AXTRUST.verify()
    ↓
map
```

---

# 161. Policy examples

Security policy may specify:

```text
allow unsigned local modules
deny unsigned system modules
require trusted publisher
allow only application-bundled modules
```

AXLOADER enforces policy result, but policy authoring belongs to AXSECURITY/AXPOLICY.

---

# 162. Capability integration

Module loading can require capability:

```text
CAP_LOAD_MODULE
```

---

# 163. Audit integration

Security-sensitive loading emits audit events when policy requires.

---

# 164. Diagnostics integration

Every active module should register:

```text
base
size
target
build_id
debug_id
```

---

# 165. Performance target

Native module activation should be approximately:

```text
O(number_of_segments
 + relocations
 + imports
 + dependencies)
```

not proportional to application runtime work.

---

# 166. Relocation performance

Relocations should be processed linearly and grouped by memory locality.

---

# 167. Symbol lookup

Use deterministic hash table:

```text
symbol_hash
 ↓
bucket
 ↓
candidate
```

---

# 168. Export lookup

For native modules, exported symbol lookup should be near:

```text
O(1)
```

average case.

---

# 169. Dependency lookup

Module identity hash:

```text
O(1)
```

average lookup.

---

# 170. Startup parallelism

Independent dependencies may be prepared in parallel.

Initialization ordering itself must remain deterministic where observable.

---

# 171. Parallel mapping

Independent module mappings may occur concurrently.

---

# 172. No parallel unsafe initialization

User initialization functions cannot execute concurrently merely because dependencies can map concurrently.

---

# 173. Deterministic initialization

Given same dependency graph:

```text
same initialization order
```

unless platform explicitly defines otherwise.

---

# 174. Loader shutdown

Process termination:

```text
application exit
 ↓
module finalization
 ↓
TLS cleanup
 ↓
loader shutdown
```

---

# 175. Finalization order

Reverse dependency order where safe and target semantics permit.

---

# 176. Crash path

If loader fails before runtime diagnostics initialized:

use minimal emergency diagnostics path.

---

# 177. No heap dependency in early failure

Early loader diagnostics should have bounded allocation.

---

# 178. Loader bootstrap

Minimal loader must itself be loadable without dynamic dependency cycles.

---

# 179. Runtime bootstrap graph

```text
kernel
 ↓
process
 ↓
Axiom startup
 ↓
minimal memory
 ↓
minimal loader
 ↓
runtime
 ↓
application
```

---

# 180. Self-hosting

Production AXLOADER implementation must eventually be written entirely in Axiom.

---

# 181. External loader dependency

Axiom executable does not require a third-party user-space loader library.

Platform loader primitives remain unavoidable at the OS boundary.

---

# 182. Important distinction

"Không phụ thuộc third-party loader" **không có nghĩa** Axiom tự thay thế Windows/Linux/macOS kernel loader.

Axiom chỉ own its user-space loading architecture.

---

# 183. PE64 process activation

Typical:

```text
Windows
 ↓
PE loader
 ↓
Axiom startup
 ↓
AXLOADER module runtime
 ↓
AXPROCESS
 ↓
main
```

---

# 184. ELF process activation

```text
Linux
 ↓
ELF loader
 ↓
Axiom startup
 ↓
AXLOADER
 ↓
main
```

---

# 185. Mach-O activation

```text
macOS/iOS
 ↓
dyld
 ↓
Axiom startup
 ↓
AXLOADER
```

---

# 186. WASM activation

```text
WASM runtime
 ↓
AXLOADER WASM backend
 ↓
instance
 ↓
start
```

---

# 187. Loader object lifecycle

```text
LoaderContext
    ↓
Module
    ↓
Mapping
    ↓
Activation
    ↓
ModuleHandle
```

---

# 188. Module state invariants

Không thể:

```text
UNLOADED → ACTIVE
```

bỏ qua validation/mapping/relocation.

---

# 189. Publication rule

Module chỉ được đưa vào global active registry sau:

```text
mapping
+
relocation
+
binding
+
TLS
+
initialization
```

thành công.

---

# 190. Partial failure

Module failed không được visible như active.

---

# 191. Address collision

Nếu requested mapping conflicts:

```text
try alternate address
```

nếu image relocation-capable.

Nếu không:

```text
LOAD_ADDRESS_CONFLICT
```

---

# 192. Fixed-address image

Image không hỗ trợ relocation phải được load đúng address hoặc fail.

---

# 193. ASLR compatibility

Relocation metadata phải đủ để target platform randomize base khi required.

---

# 194. Memory permissions finalization

Canonical:

```text
code → RX
rodata → R
data → RW
bss → RW
relro → R
TLS → target-specific
```

---

# 195. No writable code

Sau activation:

```text
code pages = RX
```

trừ explicit JIT capability.

---

# 196. JIT boundary

JIT-generated executable memory không thuộc AXLOADER normal module path.

Nó thuộc future execution/JIT subsystem và AXSECURITY policy.

---

# 197. Executable memory policy

AXLOADER không cấp executable memory tùy tiện.

---

# 198. Module metadata lifetime

Metadata cần crash/debug support phải sống cùng module.

---

# 199. Module unload and diagnostics

Khi unload:

```text
debug registry
```

phải remove mapping atomically.

---

# 200. Formal invariants

```text
LOAD-INV-01
Loader chỉ load artifact phù hợp target process.

LOAD-INV-02
Binary phải pass AXBINARY validation trước activation.

LOAD-INV-03
Trust verification phải hoàn thành khi policy yêu cầu.

LOAD-INV-04
Security policy phải authorize module load.

LOAD-INV-05
Mọi load operation phải có bounded resource usage.

LOAD-INV-06
Không map RWX trong normal loading.

LOAD-INV-07
Code phải chuyển sang executable protection trước activation.

LOAD-INV-08
Relocation phải dùng target-defined relocation semantics.

LOAD-INV-09
Loader không tự thay đổi linker symbol decisions.

LOAD-INV-10
Entry point phải thuộc executable region.

LOAD-INV-11
Dependency graph phải được resolve trước module activation.

LOAD-INV-12
Dependency cycles phải được phát hiện.

LOAD-INV-13
Không publish module trước khi initialization thành công.

LOAD-INV-14
Module failure phải rollback state chưa commit.

LOAD-INV-15
Import symbol phải resolve tới ABI-compatible target.

LOAD-INV-16
Export lookup không được expose private symbols.

LOAD-INV-17
TLS phải initialized trước code có thể truy cập TLS.

LOAD-INV-18
TLS module IDs phải unique trong process.

LOAD-INV-19
Actual load address phải fit target address space.

LOAD-INV-20
Fixed-address images phải fail nếu address không available.

LOAD-INV-21
Relocatable images phải apply base relocation khi cần.

LOAD-INV-22
File mapping phải không vượt file bounds.

LOAD-INV-23
Memory mapping phải không vượt address-space bounds.

LOAD-INV-24
Integer arithmetic trong mapping phải overflow-safe.

LOAD-INV-25
Malformed dependency metadata không được corrupt registry.

LOAD-INV-26
Concurrent requests cho cùng module phải converge vào một module instance.

LOAD-INV-27
Global loader locks không được giữ trong user initialization.

LOAD-INV-28
Loader phải tránh dependency deadlock.

LOAD-INV-29
Module state transitions phải monotonic ngoại trừ rollback.

LOAD-INV-30
Unload không được xảy ra khi module còn active execution/reference trái policy.

LOAD-INV-31
Loader không được execute untrusted binary trước validation/policy checks.

LOAD-INV-32
Loader không được bypass AXSECURITY.

LOAD-INV-33
Loader không được bypass AXTRUST khi trust policy yêu cầu.

LOAD-INV-34
Native module calls sau binding không được đi qua generic loader dispatch.

LOAD-INV-35
Loader metadata phải có stable module identity.

LOAD-INV-36
Diagnostics phải có khả năng map PC → module khi module active.

LOAD-INV-37
WASM instance không được có native-memory access ngoài explicit host boundary.

LOAD-INV-38
WASM imports/exports phải validate index/type consistency.

LOAD-INV-39
AXLOADER phải implement AXLOADER_ABI_1.

LOAD-INV-40
AXLOADER chỉ chịu trách nhiệm image activation/loading; process lifecycle authority thuộc AXPROCESS và OS.
```

---

# 201. Definition of Done

`AXLOADER 5.0` được freeze khi có:

### Native

- PE64 loading model;
- ELF64 loading model;
- Mach-O loading model;
- dynamic dependencies;
- import/export binding;
- relocations;
- TLS;
- memory protection;
- W^X;
- ASLR-compatible loading;
- module registry;
- module lifecycle;
- initialization/finalization;
- diagnostics integration.

### WASM

- module validation;
- imports;
- exports;
- functions;
- memory;
- tables;
- globals;
- initialization;
- start function;
- sandbox boundary.

### Security

- trust integration;
- security-policy integration;
- resource limits;
- safe dependency resolution;
- no RWX;
- no arbitrary execution during parsing;
- rollback.

### Performance

- linear relocation processing;
- hashed symbol lookup;
- concurrent dependency preparation;
- zero runtime dispatch overhead after binding;
- no unnecessary copying;
- minimal startup footprint.

### Toolchain

- native Axiom implementation;
- no third-party loader dependency;
- `AXLOADER_ABI_1`;
- fuzz tests;
- malformed-binary tests;
- relocation tests;
- TLS tests;
- concurrent-load tests;
- bootstrap tests;
- 40 invariants.

**AXLOADER 5.0 → FROZEN.**

---

# Vị trí hiện tại của Axiom

Chuỗi native execution đã hoàn chỉnh thêm một lớp quan trọng:

```text
             SOURCE
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
          │ AXPROCESS  │
          └─────┬──────┘
                ▼
             RUNNING
```

Điểm quan trọng nhất của thiết kế này là **AXBINARY và AXLOADER không bị trộn lẫn**:

```text
AXBINARY
= "Binary này được cấu tạo như thế nào?"

AXLOADER
= "Binary này được đưa vào address space và kích hoạt như thế nào?"
```

Điều này giữ cho compiler/linker/toolchain có thể tạo artifact mà không cần biết runtime process state, đồng thời cho phép `AXLOADER` load module mà không phải hiểu source-level semantics.

---

# BOOTSTRAP-777 — AXRUNTIME

**Native Axiom Runtime Core, Process Startup, Runtime ABI, Panic/Trap, Global Initialization, TLS Runtime, Allocation Hooks, Stack/Unwind Boundary, Shutdown, Minimal Runtime & Zero-Cost Runtime Architecture 5.0**

Task này sẽ giải quyết lớp còn thiếu ngay giữa:

```text
AXLOADER
    ↓
AXPROCESS
    ↓
AXRUNTIME
    ↓
Axiom application
```

và đặc biệt đóng băng **runtime ABI tối thiểu** để Axiom có thể thực sự tạo executable **không cần một runtime khổng lồ đi kèm**, nhưng vẫn có một lớp runtime nhỏ khi chương trình cần `panic`, TLS, startup, task/async, diagnostics, allocator hooks hoặc các dịch vụ hệ thống.