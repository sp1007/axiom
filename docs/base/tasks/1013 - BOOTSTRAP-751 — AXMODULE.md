# BOOTSTRAP-751 — AXMODULE

**Namespace:** `AXMODULE`  
**Phase:** Axiom Civilization Runtime / Native Module, Package, Library & Link Unit Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXABI`, `AXMEMORY`, `AXPROCESS`, `AXTASK`, `AXASYNC`, `AXSTORAGE`, `AXSECURITY`, compiler IR, object-format/linker layers, package/build infrastructure.

---

# 751.1 — Purpose

`AXMODULE` định nghĩa đơn vị **đóng gói, biên dịch, liên kết và phân phối native** của Axiom.

Nó giải quyết câu hỏi:

```text
Source
  ↓
Module
  ↓
Interface
  ↓
Object
  ↓
Static Library
  ↓
Dynamic Library
  ↓
Executable
```

và:

```text
module A
   ↓ imports
module B
   ↓ imports
module C
```

AXMODULE phải quản lý:

- module identity;
- interface;
- implementation;
- dependency graph;
- imports/exports;
- symbol ownership;
- ABI manifest;
- versioning;
- package mapping;
- target variants;
- feature variants;
- static/dynamic linking;
- module cache;
- incremental compilation;
- precompiled interfaces;
- reproducible builds;
- module security;
- module initialization;
- plugin boundaries;
- module inspection.

---

# 751.2 — Core Distinction

Axiom phải phân biệt rõ:

```text
MODULE
PACKAGE
COMPILATION UNIT
INTERFACE
OBJECT FILE
STATIC LIBRARY
DYNAMIC LIBRARY
EXECUTABLE
PLUGIN
```

Không được dùng các khái niệm này thay thế cho nhau.

---

# 751.3 — Module

`module` là đơn vị semantic/compiler/linkage.

Ví dụ:

```axiom
module ax.graphics
```

Module có:

```text
identity
interface
implementation
dependencies
ABI
exports
```

---

# 751.4 — Package

Package là đơn vị phân phối.

```text
package
 ├── modules
 ├── metadata
 ├── resources
 ├── licenses
 └── build information
```

Một package có thể chứa nhiều module.

---

# 751.5 — Compilation Unit

Compilation unit là đơn vị compiler đọc và phân tích.

Một module có thể gồm nhiều compilation units.

```text
module
 ├── source1.ax
 ├── source2.ax
 └── source3.ax
```

---

# 751.6 — Interface Unit

Interface unit chứa public semantic contract:

```text
types
functions
constants
traits
exports
ABI declarations
```

---

# 751.7 — Implementation Unit

Implementation unit chứa:

```text
function bodies
private types
private globals
compiler internals
```

---

# 751.8 — Interface/Implementation Separation

Compiler phải có khả năng compile dependent module chỉ từ interface artifact:

```text
A implementation
      ↓
A interface
      ↓
B compile
```

Không cần đọc toàn bộ source A.

---

# 751.9 — Precompiled Interface

Canonical artifact:

```text
.axi
```

hoặc extension được frozen sau trong toolchain.

Artifact chứa:

```text
semantic interface
ABI metadata
type metadata
dependency metadata
compiler compatibility
```

---

# 751.10 — Interface Is Not Object

Interface artifact không chứa executable machine code bắt buộc.

---

# 751.11 — Object

Object là machine-code/linker artifact:

```text
code
data
symbols
relocations
sections
ABI metadata
```

---

# 751.12 — Static Library

Static library:

```text
libA.a
A.lib
```

conceptually là archive của object files.

---

# 751.13 — Dynamic Library

Dynamic library:

```text
.dll
.so
.dylib
```

chứa executable code + exported/imported symbol metadata.

---

# 751.14 — Executable

Executable là final native artifact có entry point và platform metadata.

AXMODULE cung cấp các module cần thiết để tạo artifact này.

---

# 751.15 — Plugin

Plugin là dynamic module có lifecycle contract:

```text
discover
load
initialize
use
shutdown
unload
```

Plugin ABI dựa trên `AXABI`.

---

# 751.16 — Module Identity

Canonical identity:

```axiom
module_id {
    namespace
    name
    publisher
    major
}
```

---

# 751.17 — Identity Stability

Module identity không phụ thuộc:

```text
filesystem path
build directory
machine
timestamp
```

---

# 751.18 — Source Path

Source path chỉ là build-system location.

Không trở thành module identity.

---

# 751.19 — Module Version

Module version:

```text
major.minor.patch
```

---

# 751.20 — Semantic Version

Version semantics:

```text
major
→ incompatible API/ABI change

minor
→ backward-compatible additions

patch
→ compatible corrections
```

Module có thể áp dụng stricter compatibility rules nếu ABI contract yêu cầu.

---

# 751.21 — ABI Version

Module version và ABI version là hai khái niệm riêng:

```text
module_version
abi_version
```

---

# 751.22 — ABI Fingerprint

Module chứa:

```text
AXABI fingerprint
```

được dùng để xác định binary compatibility.

---

# 751.23 — Module Fingerprint

Module fingerprint bao gồm:

```text
module identity
public interface
ABI fingerprint
compiler semantic version
feature profile
target profile
```

---

# 751.24 — Interface Fingerprint

Interface fingerprint thay đổi khi public semantic interface thay đổi.

---

# 751.25 — Implementation Fingerprint

Implementation fingerprint thay đổi khi implementation thay đổi nhưng interface không nhất thiết thay đổi.

---

# 751.26 — Incremental Compilation

Compiler phân biệt:

```text
interface changed
implementation changed
```

---

# 751.27 — Dependency Rebuild Rule

Nếu A thay implementation:

```text
A interface unchanged
```

B không bắt buộc rebuild.

Nếu A public interface thay đổi:

```text
B
C
...
```

phụ thuộc có thể phải recompile.

---

# 751.28 — ABI-Only Change

Nếu semantic interface giữ nguyên nhưng ABI thay đổi:

```text
ABI fingerprint changed
```

dependent native artifacts phải được revalidated/relinked hoặc rebuilt theo policy.

---

# 751.29 — Dependency Graph

AXMODULE duy trì DAG:

```text
A
├── B
├── C
│   └── D
└── E
```

Circular dependency không được mặc định cho phép.

---

# 751.30 — Cycle

Nếu cần cycle:

```text
A → B → A
```

compiler phải yêu cầu explicit mechanism hoặc interface splitting.

---

# 751.31 — Interface Cycle

Các module có thể reference interface declarations theo SCC compilation model nếu compiler hỗ trợ, nhưng implementation initialization cycle vẫn phải được xử lý riêng.

---

# 751.32 — Dependency Edge

Mỗi dependency:

```axiom
module_dependency {
    module_id
    version_range
    abi_range
    features
    target_constraints
    optional
}
```

---

# 751.33 — Version Range

Ví dụ:

```text
>= 3.2 < 4.0
```

---

# 751.34 — ABI Range

Có thể yêu cầu:

```text
AXABI >= 5.0 < 6.0
```

---

# 751.35 — Optional Dependency

```axiom
dependency optional ax.audio
```

Nếu không có, module phải có fallback hoặc feature disabled.

---

# 751.36 — Required Dependency

Required dependency không resolve được:

```text
BUILD ERROR
```

---

# 751.37 — Feature Dependency

```axiom
dependency ax.graphics feature raytracing
```

chỉ active khi feature được bật.

---

# 751.38 — Target Dependency

Module có thể declare:

```text
windows
linux
macos
ios
android
wasm
```

---

# 751.39 — Platform Variant

Một module có thể có implementation:

```text
ax.window
 ├── windows
 ├── linux
 ├── macos
 └── wasm
```

---

# 751.40 — Variant Selection

Resolver chọn variant dựa trên:

```text
target
architecture
OS
ABI
features
build profile
```

---

# 751.41 — Deterministic Resolution

Cùng:

```text
source
lockfile
target
features
```

phải cho cùng dependency resolution.

---

# 751.42 — Module Lock

Build có thể tạo:

```text
axiom.lock
```

chứa resolved dependency versions/fingerprints.

---

# 751.43 — Lockfile

Lockfile không phải source semantic contract.

Nó cố định dependency graph cho reproducible build.

---

# 751.44 — Package-to-Module Mapping

Một package:

```text
ax.ui
```

có thể export:

```text
ax.ui.core
ax.ui.controls
ax.ui.layout
```

---

# 751.45 — Namespace

Namespace và package không nhất thiết giống nhau.

---

# 751.46 — Import

Canonical:

```axiom
import ax.graphics
```

---

# 751.47 — Selective Import

```axiom
import ax.graphics {
    Image
    Texture
    Renderer
}
```

---

# 751.48 — Alias

```axiom
import ax.graphics as gfx
```

---

# 751.49 — Symbol Resolution

Compiler resolve symbol theo:

```text
module
namespace
name
generic parameters
signature
```

---

# 751.50 — Ambiguity

Nếu hai modules export cùng symbol:

```text
ERROR: ambiguous symbol
```

Không tự chọn ngẫu nhiên.

---

# 751.51 — Qualified Access

```axiom
gfx.Renderer
```

loại bỏ ambiguity.

---

# 751.52 — Export

Public symbol phải explicit:

```axiom
export fn render(...)
```

---

# 751.53 — Export Surface

Module interface chỉ chứa những gì exported.

Private implementation không trở thành ABI public.

---

# 751.54 — Re-export

Module có thể:

```axiom
export from ax.math {
    Vec3
    Mat4
}
```

---

# 751.55 — Re-export Identity

Re-export không tạo duplicate type identity.

---

# 751.56 — Symbol Ownership

Mỗi exported symbol có một canonical owner module.

---

# 751.57 — Duplicate Symbol

Hai modules không được cùng sở hữu một canonical symbol trong cùng linkage scope.

---

# 751.58 — Weak Symbol

Weak symbol chỉ dùng tại platform/linker compatibility boundary.

Không phải semantic language feature mặc định.

---

# 751.59 — Symbol Visibility

AXMODULE dùng AXABI:

```text
PUBLIC
HIDDEN
PRIVATE
WEAK
IMPORT
EXPORT
```

---

# 751.60 — Private Symbol

Private symbol có thể được:

```text
inline
rename
remove
merge
specialize
```

tùy compiler.

---

# 751.61 — Module Initialization

Module có thể có initialization function.

```axiom
module_init {
    ...
}
```

---

# 751.62 — Initialization Order

Không dựa trên source-file order toàn cục.

Canonical order:

```text
dependency initialization
        ↓
dependent initialization
```

---

# 751.63 — Initialization Cycle

Nếu:

```text
A init → B
B init → A
```

build/linker phải phát hiện hoặc runtime phải có explicit cycle policy.

---

# 751.64 — Lazy Initialization

Global resource có thể:

```axiom
lazy let renderer = ...
```

để tránh startup cost.

---

# 751.65 — Thread-Safe Lazy Init

Lazy global initialization phải có exactly-once semantics nếu declaration yêu cầu.

---

# 751.66 — Module Shutdown

Module shutdown chạy khi:

```text
explicit unload
```

và mọi live references/callbacks/tasks đã được xử lý.

---

# 751.67 — No Arbitrary Destructor Order

Compiler không được phụ thuộc vào undefined global destructor ordering.

---

# 751.68 — Module Lifetime

```text
DISCOVERED
→ RESOLVED
→ LOADED
→ INITIALIZED
→ ACTIVE
→ SHUTDOWN
→ UNLOADED
```

---

# 751.69 — Module Failure

```text
RESOLUTION_FAILED
LOAD_FAILED
INIT_FAILED
ABI_INCOMPATIBLE
SECURITY_DENIED
```

---

# 751.70 — Module Load

Dynamic module:

```text
resolve
 ↓
security validate
 ↓
map
 ↓
relocate
 ↓
symbol bind
 ↓
initialize
```

---

# 751.71 — Security Boundary

Module loader phải phối hợp AXSECURITY.

Không load executable code từ untrusted source chỉ vì dependency resolution thành công.

---

# 751.72 — Module Capability

Manifest có thể yêu cầu:

```axiom
capabilities {
    filesystem.read
    network.connect
    gpu.compute
}
```

---

# 751.73 — Capability Non-Amplification

Module capability requirement không tự cấp authority.

Authority đến từ AXSECURITY/application sandbox.

---

# 751.74 — Trust Level

Module metadata:

```text
TRUSTED
SIGNED
VERIFIED
UNTRUSTED
```

Trust semantics thuộc AXSECURITY.

---

# 751.75 — Signature

Package/module có thể được cryptographically signed.

AXMODULE chỉ lưu/verify metadata; trust policy thuộc AXSECURITY.

---

# 751.76 — Package Structure

Canonical conceptual package:

```text
package/
    manifest
    lock
    interfaces/
    objects/
    libraries/
    binaries/
    resources/
    metadata/
```

---

# 751.77 — Source Package

Source distribution có:

```text
source
interface
manifest
build metadata
```

---

# 751.78 — Binary Package

Binary distribution có:

```text
precompiled interface
native artifacts
ABI manifest
target variants
```

---

# 751.79 — Multi-Target Package

Một package có thể chứa:

```text
windows-x64
linux-x64
linux-arm64
macos-arm64
ios-arm64
android-arm64
wasm32
```

---

# 751.80 — Target Selection

Resolver chọn artifact exact match trước.

---

# 751.81 — Architecture Fallback

Chỉ fallback sang compatible architecture khi package contract cho phép.

---

# 751.82 — CPU Feature Variant

Có thể có:

```text
baseline
avx2
avx512
neon
sve
```

---

# 751.83 — Runtime Dispatch

Nếu binary chứa nhiều variants:

```text
CPU detection
 ↓
select implementation
```

không thay đổi public ABI.

---

# 751.84 — Build Profile

Canonical profiles:

```text
debug
release
size
speed
realtime
instrumented
```

---

# 751.85 — Profile Compatibility

Debug/release module không nhất thiết binary-compatible nếu instrumentation ABI khác.

Manifest phải khai báo.

---

# 751.86 — Static Link

Static linking:

```text
main
 ↓
module objects
 ↓
dead-code elimination
 ↓
final executable
```

---

# 751.87 — Dynamic Link

Dynamic linking:

```text
main
 ↓
imports
 ↓
dynamic modules
 ↓
runtime resolution
```

---

# 751.88 — Static/Dynamic Selection

Dependency declaration có thể chỉ định:

```text
STATIC
DYNAMIC
EITHER
```

---

# 751.89 — Default Selection

Toolchain policy quyết định default nhưng build manifest phải ghi kết quả cuối.

---

# 751.90 — Whole Program Link

Nếu tất cả dependencies available:

```text
whole_program
```

cho phép aggressive optimization.

---

# 751.91 — Link-Time Optimization

AXMODULE phải giữ interface giữa:

```text
compiler
linker
LTO
```

---

# 751.92 — Thin Module Metadata

Module có thể cung cấp:

```text
function summaries
type summaries
call graph
constant metadata
```

cho incremental/LTO.

---

# 751.93 — Dead Code Elimination

Unused module symbols có thể bị loại khỏi final artifact.

---

# 751.94 — Dead Dependency

Nếu module dependency không tạo reachable symbol/code:

```text
linker may omit it
```

trừ side-effect initialization/resource contracts.

---

# 751.95 — Module Initialization Retention

Dependency có initialization side effect phải được giữ theo manifest.

---

# 751.96 — Resource Module

Một module có thể chứa:

```text
icons
shaders
templates
localization
models
audio
```

nhưng binary code và resources phải có ownership rõ ràng.

---

# 751.97 — Resource Linking

Resource có thể được:

```text
embedded
external
memory-mapped
package-resolved
```

---

# 751.98 — Embedded Resource

Embedded resources trở thành sections/data trong native artifact.

---

# 751.99 — External Resource

External resources được resolve qua AXSTORAGE/package runtime.

---

# 751.100 — Module Cache

Compiler cache:

```text
interface cache
semantic cache
IR cache
object cache
LTO cache
```

---

# 751.101 — Cache Key

Canonical:

```text
source_hash
interface_hash
dependency_interface_hashes
compiler_hash
ABI_hash
target_hash
feature_hash
profile_hash
```

---

# 751.102 — Cache Correctness

Nếu bất kỳ ABI-relevant input nào thay đổi:

```text
cache invalid
```

---

# 751.103 — Cache Poisoning Protection

Cache artifact phải validate:

```text
fingerprint
target
ABI
integrity
```

trước reuse.

---

# 751.104 — Precompiled Module

Module có thể phân phối semantic compiled form.

Mục tiêu:

```text
source parse
 ↓
semantic representation
```

không lặp lại giữa builds.

---

# 751.105 — Precompiled Module Security

Precompiled module phải chứa compiler/toolchain compatibility metadata.

---

# 751.106 — Compiler Version

Compiler version không nhất thiết invalidate native ABI nếu ABI contract unchanged, nhưng semantic IR compatibility phải được kiểm tra.

---

# 751.107 — IR Version

Precompiled IR có:

```text
IR_VERSION
```

---

# 751.108 — IR Compatibility

Không load IR của version incompatible.

---

# 751.109 — Module Metadata Version

Manifest có:

```text
module_format_version
interface_format_version
abi_version
```

tách biệt.

---

# 751.110 — Reproducible Module Build

Module build phải có thể reproduce khi:

```text
source
dependencies
toolchain
target
profile
```

giống nhau.

---

# 751.111 — Timestamp Independence

Timestamp không được ảnh hưởng:

```text
symbol identity
ABI fingerprint
semantic hash
```

---

# 751.112 — Path Independence

Absolute source paths không được đưa vào canonical module fingerprint.

---

# 751.113 — Build Environment

Environment-dependent features phải được explicit:

```text
target_env
feature_set
platform_sdk
```

---

# 751.114 — SDK Dependency

iOS/Android/Windows SDK versions có thể là build dependency metadata.

---

# 751.115 — Native Library Import

Axiom module có thể declare:

```axiom
extern module "user32"
```

hoặc platform-specific equivalent.

---

# 751.116 — System Module

System modules không nhất thiết là Axiom packages.

Ví dụ:

```text
Windows API
Linux libc/syscalls
Apple frameworks
```

được represented bằng external ABI modules.

---

# 751.117 — Third-Party Library

Axiom application có thể link third-party native library.

Nhưng:

> Axiom compiler/runtime core không phụ thuộc third-party compiler/runtime/library để tự build Axiom native programs.

---

# 751.118 — External ABI Module

External library có manifest:

```text
external_abi {
    symbols
    calling_conventions
    layouts
    dependencies
}
```

---

# 751.119 — C Library

C library được import qua:

```text
extern "c"
```

và ABI metadata.

---

# 751.120 — Library Search

Resolver search order phải deterministic:

```text
explicit path
package lock
target system paths
configured SDK paths
```

---

# 751.121 — No Ambient Dependency

Build không được silently resolve một random library từ machine.

---

# 751.122 — Dependency Pinning

Production build nên có lock/fingerprint.

---

# 751.123 — Module Registry

AXMODULE có thể query registry:

```text
module ID
version
target
ABI
signature
```

Registry itself không thuộc compiler core.

---

# 751.124 — Offline Build

Resolved binary package cache phải cho phép build offline.

---

# 751.125 — Vendor Dependencies

Project có thể vendor module/package trực tiếp vào source tree.

---

# 751.126 — Workspace

Workspace:

```text
workspace/
 ├── app/
 ├── core/
 ├── graphics/
 └── tools/
```

có một shared dependency graph.

---

# 751.127 — Workspace Module

Mỗi subproject vẫn giữ module identity riêng.

---

# 751.128 — Local Dependency

Workspace module có thể depend trực tiếp:

```text
path dependency
```

nhưng final manifest phải canonicalize identity.

---

# 751.129 — Package Override

Developer có thể override dependency để development/testing.

Override không được silently leak vào release lockfile.

---

# 751.130 — Module Alias

Dependency alias:

```text
ax.graphics.backend = local.graphics.backend
```

được ghi rõ trong build graph.

---

# 751.131 — Feature Unification

Nếu nhiều dependencies yêu cầu:

```text
A → B + feature X
C → B + feature Y
```

resolver phải produce deterministic combined feature set hoặc reject conflict.

---

# 751.132 — Feature Conflict

Ví dụ:

```text
feature X requires backend A
feature Y requires backend B
```

nếu incompatible:

```text
RESOLUTION_ERROR
```

---

# 751.133 — Optional Feature

Optional feature không làm dependency mandatory nếu không được enable.

---

# 751.134 — Conditional Compilation

Axiom hỗ trợ:

```axiom
#if target.windows
...
#endif
```

hoặc canonical compile-time feature mechanism.

---

# 751.135 — Conditional Module

Module graph có thể chứa:

```text
windows_only
linux_only
```

nodes.

---

# 751.136 — Conditional Export

Public interface phải deterministic cho target.

---

# 751.137 — Target Interface Fingerprint

Cùng module source có thể có interface fingerprint khác giữa targets nếu public declarations khác.

---

# 751.138 — Common Interface

Module nên có thể giữ common interface:

```text
ax.window
```

và platform-specific implementation bên dưới.

---

# 751.139 — Module Facade

Facade module:

```text
ax.window
 ↓
ax.window.windows
```

cho phép application không biết platform backend.

---

# 751.140 — Backend Module

Backend modules không nên expose internal platform details lên facade ABI trừ khi explicit.

---

# 751.141 — Module Boundaries

Module boundary là optimization boundary mặc định.

Compiler có thể phá boundary bằng:

```text
LTO
whole-program optimization
```

nếu binary configuration cho phép.

---

# 751.142 — Stable ABI Boundary

Stable dynamic library export không được tự ý inline implementation vào caller.

---

# 751.143 — Inline Export

Nếu muốn inline across stable ABI:

```axiom
@abi_inline
```

phải explicit và có fallback implementation.

---

# 751.144 — Binary Compatibility

Old caller + new dynamic library chỉ tương thích khi:

```text
ABI contract
symbol contract
behavioral contract
```

vẫn được duy trì.

---

# 751.145 — Behavioral Compatibility

AXMODULE kiểm tra structural ABI.

Behavioral compatibility là module author's contract và tests, không thể hoàn toàn suy ra từ binary metadata.

---

# 751.146 — Breaking Change

Ví dụ:

```text
remove exported function
change parameter type
change struct layout
change calling convention
change ownership contract
```

đều là ABI-breaking nếu public.

---

# 751.147 — Additive Change

Thêm symbol mới không nhất thiết break old consumers.

---

# 751.148 — Struct Extension

Không được tự động coi:

```text
struct V1
```

và:

```text
struct V2 { +field }
```

là ABI-compatible nếu caller trực tiếp depends on size/layout.

---

# 751.149 — Versioned Struct

Preferred stable ABI:

```axiom
struct ConfigV1
struct ConfigV2
```

hoặc opaque configuration handle.

---

# 751.150 — Opaque Stable Interface

Public module nên ưu tiên:

```text
create
operate
destroy
```

thay vì expose mutable internal layout nếu ABI longevity quan trọng.

---

# 751.151 — Module Service Interface

Dynamic module có thể expose service table:

```axiom
service {
    version
    capabilities
    functions[]
}
```

---

# 751.152 — Service Discovery

Runtime:

```axiom
module.get_service("renderer")
```

chỉ trả service đã export.

---

# 751.153 — Service Version

Service version độc lập với package version.

---

# 751.154 — Capability-Based Service

Service có thể yêu cầu capability token.

---

# 751.155 — Plugin Registration

Plugin:

```text
load
 ↓
descriptor
 ↓
validate ABI
 ↓
register services
```

---

# 751.156 — Plugin Shutdown

Plugin phải unregister services trước unload.

---

# 751.157 — Async Plugin Safety

Plugin không được unload khi:

```text
async task
callback
AXASYNC operation
```

còn reference tới plugin code.

---

# 751.158 — Task Frame Safety

AXTASK frame chứa function pointer tới module code phải giữ module alive.

---

# 751.159 — Closure Safety

Closure environment chứa module function pointer cũng giữ module lifetime contract.

---

# 751.160 — Function Pointer Registry

Hot reload/runtime loader có thể maintain indirection registry để detect stale pointers.

---

# 751.161 — Module Reference Count

Runtime có thể dùng:

```text
active_calls
active_tasks
active_callbacks
active_objects
```

để determine unload safety.

---

# 751.162 — No Mandatory Refcount

Reference counting là loader implementation choice, không phải language-wide memory model.

---

# 751.163 — Module Pin

Explicit:

```axiom
module.pin()
module.unpin()
```

có thể được dùng bởi long-lived subsystem.

---

# 751.164 — Unload Failure

Nếu module vẫn busy:

```text
MODULE_BUSY
```

không force unload mặc định.

---

# 751.165 — Force Unload

Force unload chỉ dành cho process termination/testing policies.

---

# 751.166 — Process Isolation

Untrusted plugin nên được chạy process-isolated khi security policy yêu cầu.

AXMODULE không biến dynamic library thành security sandbox.

---

# 751.167 — Package Resource Permissions

Package metadata có thể request permissions.

AXSECURITY quyết định grant/deny.

---

# 751.168 — Module Diagnostics

Native tool:

```text
ax module inspect app.axm
```

hiển thị:

```text
identity
version
target
ABI
dependencies
exports
imports
features
signature
```

---

# 751.169 — Dependency Graph Tool

```text
ax module graph
```

render:

```text
A → B → C
```

và detect:

```text
cycle
duplicate
unused
conflict
```

---

# 751.170 — ABI Inspection Integration

```text
ax module abi app.axm
```

delegates to AXABI.

---

# 751.171 — Module Diff

```text
ax module diff old.axm new.axm
```

hiển thị:

```text
interface changes
ABI changes
dependency changes
feature changes
```

---

# 751.172 — Module Size Analysis

Tool có thể report:

```text
code size
data size
dependency contribution
debug metadata
resource size
```

---

# 751.173 — Link Map

Linker generates optional:

```text
module
 → symbol
 → object
 → section
```

mapping.

---

# 751.174 — Dependency Size Attribution

Build tooling có thể identify module đóng góp bao nhiêu bytes vào final executable.

---

# 751.175 — Minimal Binary Mode

Release profile có thể strip:

```text
unused exports
debug info
module docs
AI metadata
unused runtime metadata
```

---

# 751.176 — Runtime Metadata Retention

Chỉ giữ metadata cần cho:

```text
reflection
dynamic loading
crash diagnostics
security
```

theo application configuration.

---

# 751.177 — Module Metadata Compression

Manifest có thể sử dụng compact binary encoding.

---

# 751.178 — Human Manifest

Source package vẫn có human-readable manifest:

```text
axiom.module
```

hoặc canonical format được toolchain frozen sau.

---

# 751.179 — Machine Manifest

Native binary chứa compact machine-readable metadata.

---

# 751.180 — Manifest Separation

Human manifest và machine manifest không được có hai nguồn sự thật.

Machine manifest phải được generated từ canonical project metadata.

---

# 751.181 — Source of Truth

Canonical:

```text
module declaration
project manifest
ABI metadata
```

Compiler generates derived artifacts.

---

# 751.182 — Generated Artifact

Không chỉnh sửa trực tiếp:

```text
compiled interface
ABI manifest
dependency lock metadata
object metadata
```

---

# 751.183 — Module Build Pipeline

```text
source
 ↓
lex/parse
 ↓
semantic analysis
 ↓
module interface
 ↓
dependency resolution
 ↓
IR
 ↓
optimization
 ↓
machine code
 ↓
object
 ↓
archive/link
 ↓
native module
```

---

# 751.184 — Interface-First Compilation

Compiler nên:

```text
parse interface
 ↓
load cached dependency interfaces
 ↓
compile implementation
```

để giảm thời gian build.

---

# 751.185 — Parallel Module Compilation

Independent modules:

```text
A
B
C
```

có thể compile song song.

---

# 751.186 — Critical Path

Build scheduler ưu tiên dependency critical path.

---

# 751.187 — Build Scheduler

AXMODULE build graph có thể feed AXCOMPUTE/AXTASK.

---

# 751.188 — Memory-Bounded Build

Compiler build scheduler phải hỗ trợ:

```text
max_parallel_modules
memory_budget
```

để tránh RAM exhaustion.

---

# 751.189 — Incremental Semantic Cache

AST/semantic graph có thể được cache theo source region/hash.

---

# 751.190 — Fine-Grained Invalidation

Thay đổi private function không nên invalidate toàn bộ module interface.

---

# 751.191 — Public Dependency Tracking

Compiler tracks which dependent modules actually use changed declarations.

---

# 751.192 — Symbol-Level Rebuild

Có thể tránh recompilation unrelated code nếu interface change chỉ ảnh hưởng một subset.

---

# 751.193 — Generic Cache

Monomorphized generic instances có cache key:

```text
generic_definition_hash
type_arguments_hash
ABI_target
optimization_profile
```

---

# 751.194 — Generic Cross-Module Reuse

Compiled specialization có thể được reused giữa modules nếu ABI-compatible.

---

# 751.195 — Module-Level Code Cache

Object cache có thể store:

```text
function machine code
relocations
metadata
```

---

# 751.196 — Cache Granularity

Toolchain được phép chọn:

```text
module
function
basic-block
```

nhưng module-level là baseline.

---

# 751.197 — Deterministic Dependency Resolution

Resolver tie-break phải deterministic.

Không dựa trên:

```text
directory enumeration order
network response order
thread scheduling
```

---

# 751.198 — Dependency Conflict

Nếu:

```text
A requires B 2.x
C requires B 3.x
```

resolver phải:

```text
select compatible graph
```

hoặc báo conflict.

---

# 751.199 — Multiple Versions

Multiple versions của cùng module có thể coexist chỉ nếu module identity/namespace/ABI model cho phép.

Default policy nên tránh duplicate runtime singletons.

---

# 751.200 — Runtime Singleton Modules

Một module đánh dấu:

```text
singleton
```

không được load nhiều independent instances trong cùng process nếu contract cấm.

---

# 751.201 — Multi-Instance Module

Module không singleton có thể có nhiều logical instances.

---

# 751.202 — Module Context

Service module có thể có:

```text
module_context
```

để chứa state thay vì global mutable state.

---

# 751.203 — Global State

Global mutable state phải explicit.

---

# 751.204 — Thread Local Module State

Module có thể dùng AXPROCESS TLS.

---

# 751.205 — Async Module State

Module async state phải tuân theo AXTASK/AXASYNC frame lifetime.

---

# 751.206 — Module Crash

Nếu dynamic module fault:

```text
process crash boundary
```

thường thuộc AXPROCESS.

AXMODULE cung cấp module identity để diagnostics.

---

# 751.207 — Module Crash Attribution

Crash record có thể chứa:

```text
module_id
module_version
symbol
offset
ABI fingerprint
```

---

# 751.208 — Module Update

Package manager có thể update module:

```text
old
 ↓
new
```

nhưng AXMODULE chỉ xác định compatibility.

---

# 751.209 — Rolling Update

Long-lived process chỉ có thể replace module nếu hot-reload contract cho phép.

---

# 751.210 — Migration

Nếu module state schema thay đổi:

```text
old state
 ↓
migration
 ↓
new module
```

migration logic thuộc module/application layer.

---

# 751.211 — Rollback

Rollback package phải restore compatible:

```text
module
ABI
dependencies
resources
```

---

# 751.212 — Module Security Update

Security metadata có thể đánh dấu minimum version.

---

# 751.213 — Revocation

Revoked package/module signature được AXSECURITY xử lý.

---

# 751.214 — Module Quarantine

Untrusted module có thể bị ngăn load trước relocation.

---

# 751.215 — Code Signing

Native module signing:

```text
module bytes
+
manifest
→
signature
```

---

# 751.216 — Signature Verification

Verify trước execution.

---

# 751.217 — Reproducible Signing

Signing metadata không được làm thay đổi semantic/ABI fingerprint.

---

# 751.218 — Content Address

Package artifact có thể có:

```text
content_hash
```

để integrity/cache.

---

# 751.219 — Content Hash vs Module Identity

Không dùng content hash thay module identity.

```text
identity = "ax.graphics"
hash = particular build
```

---

# 751.220 — Module Artifact Identity

Artifact:

```text
module_id
version
target
ABI
content_hash
```

---

# 751.221 — Native Artifact Matrix

Một source module có thể produce:

```text
ax.graphics
 ├── windows-x64.dll
 ├── linux-x64.so
 ├── linux-arm64.so
 ├── macos-arm64.dylib
 ├── ios-arm64
 └── wasm32
```

---

# 751.222 — Target Artifact Selection

Application build chỉ đưa artifact target tương ứng vào final graph.

---

# 751.223 — Cross Compilation

Cross compiler có thể compile:

```text
host = Windows x64
target = Linux ARM64
```

mà không cần target OS chạy trên host.

---

# 751.224 — Target SDK

Cross build phải có required target SDK/sysroot metadata.

---

# 751.225 — Sysroot

Module resolver có thể use:

```text
target sysroot
```

cho system modules.

---

# 751.226 — Standard Library

Axiom standard library được tổ chức thành modules:

```text
ax.core
ax.io
ax.memory
ax.concurrent
...
```

Không phải một monolithic mandatory runtime library.

---

# 751.227 — Runtime Feature Linking

Application chỉ link runtime components mà nó sử dụng khi architecture cho phép.

---

# 751.228 — Runtime Component Graph

Ví dụ:

```text
application
 ├── ax.memory
 ├── ax.task
 ├── ax.async
 └── ax.network
```

---

# 751.229 — Dead Runtime Elimination

Không dùng `AXNETWORK` thì network runtime code không nên bị kéo vào binary chỉ vì tồn tại trong standard runtime ecosystem.

---

# 751.230 — Freestanding Modules

Freestanding program có thể dùng:

```text
ax.core
ax.memory
```

mà không cần hosted modules.

---

# 751.231 — Module Capability Profile

Module có thể declare:

```text
HOSTED
FREESTANDING
KERNEL
EMBEDDED
WASM
```

---

# 751.232 — Kernel Module

Kernel-specific modules không được accidentally import user-space runtime.

---

# 751.233 — Layer Validation

Build graph checker phải detect:

```text
kernel → desktop
freestanding → filesystem service
low-level runtime → application UI
```

nếu dependency violates layer contract.

---

# 751.234 — Architecture Layer Rules

Module manifest có:

```axiom
layer = core | runtime | platform | application
```

---

# 751.235 — Dependency Direction

Default:

```text
core
 ↓
runtime
 ↓
platform
 ↓
application
```

không ngược lại.

---

# 751.236 — Circular Layer Dependency

Build phải reject nếu violates architecture policy.

---

# 751.237 — Module Documentation

Module interface có thể embed documentation metadata.

Không cần runtime load.

---

# 751.238 — AI-Friendly Interface

Interface metadata có thể expose:

```text
function purpose
parameter semantics
ownership
blocking
async
errors
thread safety
capabilities
```

---

# 751.239 — AI Module Discovery

AI tooling có thể query:

```text
find modules providing capability X
```

nhưng module metadata không cấp quyền truy cập.

---

# 751.240 — AI Boundary

AI có thể:

```text
analyze dependency graph
suggest module split
detect ABI break
explain build failure
suggest cache invalidation
find unused dependency
```

Không được:

```text
bypass module signature
load unauthorized module
ignore security policy
silently modify dependency lock
```

---

# 751.241 — Native Module Manifest

Canonical:

```axiom
module_manifest {
    module_id
    version
    abi_version
    interface_fingerprint
    abi_fingerprint
    content_hash

    targets[]
    features[]
    dependencies[]
    exports[]
    imports[]

    capabilities[]
    initialization_policy
    unload_policy

    compiler_requirements
    runtime_requirements
}
```

---

# 751.242 — Module Graph Node

```axiom
module_node {
    module_id
    version
    target
    features
    interface_hash
    abi_hash
}
```

---

# 751.243 — Module Graph Edge

```axiom
module_edge {
    from
    to
    dependency_kind
    version_range
    abi_range
    optional
}
```

---

# 751.244 — Resolver

Canonical resolver:

```axiom
resolve_module_graph(
    root,
    target,
    features,
    lock
)
```

returns immutable graph.

---

# 751.245 — Resolver Output

```axiom
resolved_graph {
    modules[]
    edges[]
    selected_variants[]
    unresolved[]
    conflicts[]
}
```

---

# 751.246 — Link Plan

Resolved graph feeds:

```axiom
link_plan {
    objects[]
    static_libraries[]
    dynamic_libraries[]
    imports[]
    exports[]
    initialization_order[]
}
```

---

# 751.247 — Link Plan Determinism

Same graph + target/profile phải tạo cùng logical link plan.

---

# 751.248 — Module Build API

```axiom
build_module(...)
build_interface(...)
compile_module(...)
link_module(...)
package_module(...)
inspect_module(...)
diff_module(...)
resolve_modules(...)
```

---

# 751.249 — Module Loader API

```axiom
load_module(...)
unload_module(...)
get_module(...)
get_module_info(...)
get_symbol(...)
get_service(...)
pin_module(...)
unpin_module(...)
```

---

# 751.250 — Module Build Flow

```text
source
 ↓
parse
 ↓
semantic analysis
 ↓
load dependency interfaces
 ↓
generate interface fingerprint
 ↓
compile implementation
 ↓
generate object
 ↓
ABI validation
 ↓
package
```

---

# 751.251 — Static Library Flow

```text
modules
 ↓
objects
 ↓
archive
 ↓
index symbols
 ↓
static library
```

---

# 751.252 — Dynamic Library Flow

```text
modules
 ↓
objects
 ↓
resolve exports/imports
 ↓
relocation metadata
 ↓
platform linker
 ↓
dynamic library
 ↓
ABI manifest
```

---

# 751.253 — Executable Flow

```text
application module
      ↓
resolve graph
      ↓
compile
      ↓
link
      ↓
runtime composition
      ↓
platform entry
      ↓
native executable
```

---

# 751.254 — Plugin Flow

```text
discover
 ↓
read manifest
 ↓
verify signature
 ↓
check ABI
 ↓
map/load
 ↓
resolve imports
 ↓
initialize
 ↓
register services
```

---

# 751.255 — Plugin Unload Flow

```text
stop new calls
 ↓
stop/cancel plugin tasks
 ↓
drain async operations
 ↓
unregister services
 ↓
shutdown
 ↓
release references
 ↓
unload
```

---

# 751.256 — Module Checkpoint

Module logical state có thể được checkpoint nếu module declares checkpoint schema.

---

# 751.257 — Module State Schema

```axiom
module_state_schema {
    version
    fields[]
    migration[]
}
```

---

# 751.258 — No Arbitrary Memory Snapshot

AXMODULE không assume process memory có thể serialize.

AXPROCESS/AXMEMORY checkpoint semantics vẫn giữ nguyên.

---

# 751.259 — Module Simulation

Module graph có thể chạy simulation với:

```text
virtual dependencies
mock services
deterministic interfaces
```

---

# 751.260 — Mock Module

Test build có thể thay:

```text
real.module
```

bằng:

```text
mock.module
```

nếu interface/ABI compatible.

---

# 751.261 — Test Module

Test-only module được mark:

```text
TEST_ONLY
```

không được accidentally package vào production.

---

# 751.262 — Build Assertions

Module manifest có thể yêu cầu:

```axiom
requires target.arch == "x86_64"
requires feature.simd
```

---

# 751.263 — Compile-Time Environment

Build expressions phải deterministic và sandboxed.

Không cho module resolver thực thi arbitrary network/system commands trong compiler process mặc định.

---

# 751.264 — Build Script Boundary

Custom build tooling là separate capability:

```text
AXBUILD
```

không phải module semantic code.

---

# 751.265 — Build Script Security

Build script phải được permission-gated.

---

# 751.266 — Module Fetch

Package fetcher thuộc package infrastructure.

AXMODULE chỉ consume resolved artifact.

---

# 751.267 — Offline Resolver

Không có network:

```text
local cache
vendor
lockfile
```

vẫn resolve được nếu dependencies available.

---

# 751.268 — Missing Artifact

Resolver báo:

```text
MODULE_NOT_FOUND
TARGET_ARTIFACT_NOT_FOUND
ABI_INCOMPATIBLE
```

phân biệt rõ.

---

# 751.269 — Duplicate Module

Nếu cùng canonical module được resolve từ hai sources:

```text
same identity
different content
```

resolver phải reject hoặc yêu cầu explicit override.

---

# 751.270 — Dependency Substitution

Substitution phải thay đổi graph fingerprint để build reproducibility không bị giả mạo.

---

# 751.271 — Module Provenance

Manifest có:

```text
source
publisher
build_toolchain
dependencies
signature
```

---

# 751.272 — Provenance Is Metadata

Provenance không thay thế ABI verification.

---

# 751.273 — Module Reproducibility Record

Build có thể emit:

```axiom
reproducibility_record {
    source_hash
    dependency_hashes[]
    toolchain_hash
    target
    profile
}
```

---

# 751.274 — Hermetic Build

Production build có thể chạy trong hermetic environment:

```text
fixed inputs
fixed target
fixed dependencies
fixed compiler
```

---

# 751.275 — Host Leakage

Build system phải detect/avoid implicit host-specific inputs.

---

# 751.276 — Generated Source

Generated `.ax` source được hash như source input.

---

# 751.277 — Generated Interface

Generated interface phải có stable generator fingerprint.

---

# 751.278 — Macro/Code Generation Boundary

Generated code phải preserve module identity.

---

# 751.279 — Macro Dependency

Nếu macro implementation thay đổi:

```text
macro fingerprint changed
```

dependent modules sử dụng macro phải rebuild.

---

# 751.280 — Module Ownership

Module owner metadata không quyết định runtime security authority.

---

# 751.281 — License Metadata

Package có thể chứa license information.

Không ảnh hưởng native ABI.

---

# 751.282 — Resource License

Resource licenses có thể khác module license.

---

# 751.283 — Module Documentation Versioning

Docs có thể update không làm ABI fingerprint thay đổi.

---

# 751.284 — Semantic Metadata

Public contracts như:

```text
@blocking
@thread_safe
@async
@unsafe
```

được coi là interface-relevant metadata nếu compiler/tooling contract dựa vào chúng.

---

# 751.285 — Contract Fingerprint

Nếu ABI/tooling-relevant contract thay đổi:

```text
interface fingerprint
```

phải thay đổi.

---

# 751.286 — API Compatibility

Module diff phân loại:

```text
ADDITIVE
NON_BREAKING
ABI_BREAKING
SOURCE_BREAKING
BEHAVIORAL_RISK
```

`BEHAVIORAL_RISK` là diagnostic category, không phải compiler proof.

---

# 751.287 — Source Compatibility

Một thay đổi có thể:

```text
ABI-compatible
```

nhưng source-incompatible.

Ví dụ ambiguity mới.

Tool phải report separately.

---

# 751.288 — Binary Compatibility

Một thay đổi có thể giữ source syntax nhưng break ABI.

Tool phải ưu tiên phát hiện binary break.

---

# 751.289 — Module API Snapshot

CI có thể freeze:

```text
api.snapshot
```

và compare release mới.

---

# 751.290 — ABI Snapshot

Tích hợp AXABI:

```text
abi.snapshot
```

---

# 751.291 — Module Governance

Public module có lifecycle:

```text
EXPERIMENTAL
STABLE
DEPRECATED
REMOVED
```

---

# 751.292 — Deprecation

Manifest ghi:

```text
deprecated_since
replacement
removal_target
```

---

# 751.293 — Removal

Removed symbol chỉ được remove sau major ABI/version boundary nếu stable ABI policy yêu cầu.

---

# 751.294 — Compatibility Shim

Old module API có thể được giữ bằng:

```text
shim module
```

thay vì sửa compiler.

---

# 751.295 — ABI Shim

Shim dùng AXABI thunks.

---

# 751.296 — Module Security Policy

Security policy có thể restrict:

```text
which publisher
which version
which capability
which target
```

AXMODULE cung cấp metadata để policy engine quyết định.

---

# 751.297 — Runtime Loader Policy

Loader phải reject:

```text
wrong architecture
invalid signature
ABI mismatch
missing dependency
```

trước activation.

---

# 751.298 — Loader Isolation

Module loading errors không được làm hỏng loader state của các module đã active.

---

# 751.299 — Atomic Module Activation

Dynamic module activation:

```text
load
validate
initialize
```

phải hoàn tất thành công trước khi publish module services.

---

# 751.300 — Failed Activation

Nếu initialization fail:

```text
rollback
unmap
release
```

và module không trở thành ACTIVE.

---

# 751.301 — Dependency Activation

Dependencies phải ACTIVE/READY trước dependent initialization.

---

# 751.302 — Parallel Loading

Independent dynamic modules có thể load/relocate song song.

Initialization order vẫn deterministic.

---

# 751.303 — Module Loader Locking

Loader phải tránh global lock kéo dài trong initialization code.

---

# 751.304 — Reentrant Loading

Nếu module A init yêu cầu module B:

```text
loader
 ↓
B
```

phải detect recursion/deadlock.

---

# 751.305 — Loader Context

Loader operations có context:

```axiom
module_load_context {
    requesting_module
    security_identity
    target
    dependency_stack
}
```

---

# 751.306 — Security Identity Propagation

Requesting module không được tự động elevate loader authority.

---

# 751.307 — Module Handle

Runtime module handle là generation-safe opaque handle.

---

# 751.308 — Symbol Handle

Dynamic symbol lookup có thể trả:

```axiom
symbol_handle {
    module_generation
    symbol_id
}
```

để detect stale unload.

---

# 751.309 — Stale Symbol

Calling stale symbol handle phải fail safely thay vì jump vào unmapped memory.

---

# 751.310 — Module Address

Raw module address không phải stable identity.

---

# 751.311 — Address Space

AXMODULE phụ thuộc AXMEMORY/AXPROCESS để map code/data.

---

# 751.312 — W^X

Dynamic module mapping phải tuân W^X policy của AXMEMORY/security backend.

---

# 751.313 — Relocation Permissions

Loader không được để writable+executable pages lâu hơn cần thiết.

---

# 751.314 — Code Integrity

Nếu platform hỗ trợ executable code signing/integrity, loader phải integrate.

---

# 751.315 — Module Unmapping

Code pages chỉ unmap khi no active references.

---

# 751.316 — Module Thread Affinity

Module shutdown có thể yêu cầu executor/thread affinity.

Metadata phải declare nếu có.

---

# 751.317 — Module Async Drain

AXMODULE shutdown integration:

```text
AXTASK cancel
→ AXASYNC drain
→ module shutdown
```

---

# 751.318 — Module Service Drain

Services phải reject new calls trong shutdown phase.

---

# 751.319 — In-Flight Service Calls

Loader chờ hoặc cancel theo service contract.

---

# 751.320 — Module Reload

Reload sequence:

```text
quiesce
 ↓
checkpoint/migrate if supported
 ↓
unload old
 ↓
load new
 ↓
restore state
 ↓
resume
```

---

# 751.321 — Reload Compatibility

New module phải pass:

```text
ABI
service
state migration
```

checks.

---

# 751.322 — No Implicit State Migration

Runtime không tự đoán cách chuyển state.

---

# 751.323 — Module Testing

Compiler suite phải test:

```text
single module
multi-module
cyclic dependency
ABI mismatch
FFI
static linking
dynamic linking
plugin
reload
cross-target
```

---

# 751.324 — Dependency Fuzzing

Resolver fuzzing:

```text
version conflicts
feature conflicts
cycles
duplicate sources
optional dependencies
```

---

# 751.325 — Linker Fuzzing

Generate random module graphs và symbol sets để test:

```text
resolution
dead stripping
relocation
ABI checks
```

---

# 751.326 — Loader Fuzzing

Malformed module manifests không được crash loader.

---

# 751.327 — Module Format Validation

Loader validate:

```text
magic
format version
lengths
offsets
hashes
ABI
target
```

trước đọc sâu.

---

# 751.328 — Bounds Safety

Metadata parser phải bounds-check mọi offset/length.

---

# 751.329 — Malformed Dependency Graph

Reject:

```text
self dependency
cycle where forbidden
invalid version
invalid ABI range
```

---

# 751.330 — Module Cache Integrity

Cached artifact phải verify content hash trước execution/linking.

---

# 751.331 — Build Artifact Ownership

Build outputs thuộc build system, không phải source module semantic runtime.

---

# 751.332 — Artifact Naming

Artifact name deterministic:

```text
module
+
target
+
architecture
+
profile
```

---

# 751.333 — Artifact Extension

Platform backend quyết định:

```text
.obj
.o
.lib
.a
.dll
.so
.dylib
.exe
```

---

# 751.334 — Module Container

Axiom có thể định nghĩa unified metadata container:

```text
AXM
```

nhưng native OS artifact vẫn phải dùng PE/ELF/Mach-O/WASM formats tương ứng.

---

# 751.335 — AXM Role

AXM nếu được sử dụng sẽ chứa:

```text
module metadata
ABI manifest
interface
dependency metadata
```

không thay thế native executable format.

---

# 751.336 — Native Artifact Independence

Axiom phải có thể tạo native artifact mà OS loader hiểu trực tiếp.

Không yêu cầu AXM runtime loader cho normal executable.

---

# 751.337 — Executable Startup

Normal executable:

```text
OS loader
→ native entry
```

không:

```text
OS
→ AXM VM
→ Axiom bytecode
```

---

# 751.338 — No Mandatory VM

AXMODULE không tạo bytecode VM requirement.

---

# 751.339 — WASM Exception

WASM là native target của Axiom nhưng chạy trong WASM execution environment.

---

# 751.340 — Module Toolchain CLI

Canonical commands:

```text
ax module build
ax module check
ax module inspect
ax module graph
ax module diff
ax module abi
ax module package
ax module verify
ax module clean
```

---

# 751.341 — Module Check

`check` không nhất thiết generate machine code.

Nó validate:

```text
imports
exports
dependencies
ABI
features
targets
```

---

# 751.342 — Module Verify

`verify` validate binary/package integrity:

```text
signature
hash
manifest
ABI
target
```

---

# 751.343 — Module Graph Export

Graph có thể output:

```text
JSON
binary
text
graphviz-compatible
```

---

# 751.344 — IDE Integration

IDE có thể query module graph để:

```text
jump to dependency
show public API
show ABI
show source
show target variants
```

---

# 751.345 — Language Server

LSP-like service có thể consume precompiled interfaces mà không compile implementation.

---

# 751.346 — Fast Code Completion

Public interface cache cho phép completion không cần full project rebuild.

---

# 751.347 — AI Context Artifact

Module interface có thể tạo AI-optimized compact description:

```text
module purpose
exports
types
contracts
dependencies
examples metadata
```

---

# 751.348 — AI Context Independence

AI metadata không được làm dependency bắt buộc cho compiler.

---

# 751.349 — AI Module Refactoring

Tooling có thể đề xuất:

```text
split module
merge module
remove dependency
replace import
```

nhưng changes phải qua normal build/ABI checks.

---

# 751.350 — Architecture Freeze

AXMODULE 5.0 khóa nguyên tắc:

```text
Module ≠ Package
Module ≠ Object
Module ≠ Library
Module ≠ Process
Module ≠ Application
```

và:

```text
Interface
≠
Implementation
```

---

# 751.351 — Canonical Module Model

```text
                       PACKAGE
                          │
                ┌─────────┴─────────┐
                │                   │
             MODULE A            MODULE B
                │                   │
        ┌───────┴───────┐           │
        │               │           │
    INTERFACE      IMPLEMENTATION   ...
        │               │
        └───────┬───────┘
                │
             OBJECT
                │
        ┌───────┴────────┐
        │                │
    STATIC LIB       DYNAMIC LIB
        │                │
        └────────┬───────┘
                 │
             EXECUTABLE
```

---

# 751.352 — Canonical Build Graph

```text
             SOURCE
                │
                ▼
         SEMANTIC MODULE
                │
       ┌────────┴────────┐
       ▼                 ▼
   INTERFACE          IMPLEMENTATION
       │                 │
       │                 ▼
       │                IR
       │                 │
       │                 ▼
       │              MACHINE CODE
       │                 │
       └────────┬────────┘
                ▼
              OBJECT
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
      STATIC  DYNAMIC   EXEC
```

---

# 751.353 — Canonical Dependency Flow

```text
             MODULE GRAPH
                  │
                  ▼
          DEPENDENCY RESOLVER
                  │
                  ▼
           ABI VALIDATION
                  │
                  ▼
             BUILD PLAN
                  │
                  ▼
               LINKER
```

---

# 751.354 — Canonical Dynamic Load Flow

```text
binary
  ↓
module manifest
  ↓
dependency resolution
  ↓
signature/security verification
  ↓
ABI validation
  ↓
memory mapping
  ↓
relocation
  ↓
symbol binding
  ↓
dependency initialization
  ↓
module initialization
  ↓
ACTIVE
```

---

# 751.355 — Canonical Incremental Build Flow

```text
source change
      ↓
hash comparison
      ↓
interface changed?
   ┌──┴──┐
  NO     YES
   │       │
   ▼       ▼
recompile  invalidate dependents
implementation
   │       │
   └──┬────┘
      ▼
    object
      ↓
    relink
```

---

# 751.356 — Performance Architecture

AXMODULE phải tối ưu:

```text
interface caching
parallel compilation
incremental invalidation
dependency graph caching
parallel linking
thin metadata
symbol indexing
LTO summaries
generic specialization caching
```

---

# 751.357 — Build Parallelism

Compiler có thể dùng AXTASK:

```text
Module A ─┐
Module B ─┼→ parallel compile
Module C ─┘
```

---

# 751.358 — Build Memory Budget

Compiler scheduler phải tránh:

```text
N modules × huge AST/IR
```

làm vượt RAM.

---

# 751.359 — Streaming Compilation

Large module có thể compile in phases để giảm peak memory.

---

# 751.360 — Symbol Index

Static library phải có symbol index để linker không scan toàn bộ objects.

---

# 751.361 — Fast Import

Interface loader phải index:

```text
symbol → module
type → module
```

---

# 751.362 — Lazy Interface Loading

Compiler chỉ load detailed declaration khi symbol được referenced.

---

# 751.363 — Lazy Object Extraction

Static linker chỉ extract object members cần thiết.

---

# 751.364 — Dynamic Symbol Lazy Binding

Platform linker có thể lazy-bind external symbols nếu target hỗ trợ.

---

# 751.365 — Eager Binding

Security/realtime profile có thể yêu cầu eager symbol resolution.

---

# 751.366 — Realtime Module Policy

Realtime application không nên dynamic-load/unload module trên critical path.

---

# 751.367 — Startup Optimization

Prelinked/static modules có thể giảm startup overhead.

---

# 751.368 — Module Prewarming

Runtime có thể pre-resolve frequently used modules.

---

# 751.369 — No Global Module Registry Requirement

Static executable không cần runtime module registry nếu không dùng dynamic loading/reflection.

---

# 751.370 — Final Runtime Cost

AXMODULE phải có:

```text
zero runtime cost
```

cho static modules sau link nếu metadata không cần runtime.

---

# 751.371 — Dynamic Runtime Cost

Dynamic modules chỉ trả cost cho:

```text
load
relocation
binding
lifecycle
```

---

# 751.372 — Module Boundary Optimization

Static whole-program build có thể eliminate abstraction overhead hoàn toàn.

---

# 751.373 — Native Performance Goal

Module boundary không được mặc định biến function call thành indirect dispatch.

Direct call vẫn là default.

---

# 751.374 — Cross-Module Direct Call

Nếu symbol known statically:

```text
CALL target
```

không cần service lookup.

---

# 751.375 — Dynamic Call

Dynamic symbol/service lookup chỉ khi explicitly requested.

---

# 751.376 — Module ABI Compatibility vs Performance

Stable dynamic ABI ưu tiên compatibility.

Static/LTO build ưu tiên optimization.

Cả hai cùng tồn tại trong Axiom.

---

# 751.377 — Formal Invariants

```text
MOD-INV-01   Every module has a deterministic canonical identity.
MOD-INV-02   Module identity is independent of filesystem path.
MOD-INV-03   Package identity and module identity are distinct.
MOD-INV-04   Interface and implementation are distinct artifacts/concepts.
MOD-INV-05   Every module dependency has explicit identity and version constraints.
MOD-INV-06   ABI compatibility is checked independently of semantic version compatibility.
MOD-INV-07   Dependency resolution is deterministic.
MOD-INV-08   Conflicting dependencies are never silently selected arbitrarily.
MOD-INV-09   Required dependencies must resolve before module activation.
MOD-INV-10   Optional dependencies cannot silently become required dependencies.

MOD-INV-11   Exported symbols have explicit ownership.
MOD-INV-12   Duplicate canonical symbol ownership is rejected.
MOD-INV-13   Re-export does not create a second type identity.
MOD-INV-14   Private implementation details are not automatically public ABI.
MOD-INV-15   Interface fingerprints change when ABI-relevant public contracts change.
MOD-INV-16   ABI fingerprints are delegated to AXABI's canonical rules.
MOD-INV-17   Target-specific variants are selected deterministically.
MOD-INV-18   Unsupported target variants fail before native linking.
MOD-INV-19   Static and dynamic linkage preserve declared ABI semantics.
MOD-INV-20   Native executable generation does not require a VM.

MOD-INV-21   Cached artifacts are reused only when all relevant fingerprints match.
MOD-INV-22   Dependency interface changes invalidate affected consumers.
MOD-INV-23   Private implementation changes do not unnecessarily invalidate unrelated consumers.
MOD-INV-24   Compiler-generated metadata is derived from canonical project/module state.
MOD-INV-25   Reproducible module identity cannot depend on timestamps or absolute paths.
MOD-INV-26   Precompiled interfaces cannot be loaded with incompatible format versions.
MOD-INV-27   Precompiled native artifacts cannot bypass ABI validation.
MOD-INV-28   Static library symbol indexing cannot change semantic symbol ownership.
MOD-INV-29   Dead-code elimination cannot remove required initialization side effects.
MOD-INV-30   Link plans are deterministic for identical resolved inputs.

MOD-INV-31   Dynamic module activation completes validation before services become visible.
MOD-INV-32   A failed module initialization cannot publish an ACTIVE module.
MOD-INV-33   A module cannot be unloaded while live execution state references its code.
MOD-INV-34   Async frames cannot outlive module code they reference.
MOD-INV-35   Module shutdown must quiesce declared services before unload.
MOD-INV-36   Module loading cannot grant security authority.
MOD-INV-37   Untrusted modules cannot bypass AXSECURITY policy.
MOD-INV-38   Malformed module metadata must be rejected without unsafe memory access.
MOD-INV-39   AI tooling cannot bypass dependency, ABI, or security validation.
MOD-INV-40   Every supported module format has mechanically testable validation rules.
```

---

# 751.378 — Native APIs

Core compiler/build APIs:

```axiom
module.create(...)
module.inspect(...)
module.check(...)
module.build(...)
module.compile(...)
module.build_interface(...)

module.resolve(...)
module.resolve_graph(...)

module.link_static(...)
module.link_dynamic(...)
module.link_executable(...)

module.package(...)
module.verify(...)
module.diff(...)

module.get_interface(...)
module.get_manifest(...)
module.get_fingerprint(...)
```

---

# 751.379 — Runtime APIs

```axiom
module.load(...)
module.unload(...)

module.get(...)
module.get_info(...)

module.get_symbol(...)
module.get_service(...)

module.pin(...)
module.unpin(...)

module.enumerate(...)
module.find(...)
```

---

# 751.380 — Build APIs

```axiom
build.create_workspace(...)
build.add_module(...)
build.add_dependency(...)
build.set_target(...)
build.set_profile(...)
build.enable_feature(...)
build.lock(...)
build.compile(...)
build.link(...)
build.package(...)
```

---

# 751.381 — Package APIs

```axiom
package.open(...)
package.inspect(...)
package.verify(...)
package.list_modules(...)
package.get_artifact(...)
package.get_manifest(...)
```

---

# 751.382 — Cache APIs

```axiom
module_cache.lookup(...)
module_cache.store(...)
module_cache.invalidate(...)
module_cache.verify(...)
module_cache.stats(...)
```

---

# 751.383 — Module Lifecycle State

```text
DISCOVERED
    ↓
RESOLVED
    ↓
VALIDATED
    ↓
LOADED
    ↓
INITIALIZING
    ↓
ACTIVE
    ↓
QUIESCING
    ↓
SHUTTING_DOWN
    ↓
UNLOADED
```

Failure states:

```text
NOT_FOUND
INCOMPATIBLE
DENIED
LOAD_FAILED
INIT_FAILED
CORRUPT
```

---

# 751.384 — Package Lifecycle

```text
DISCOVERED
→ VERIFIED
→ RESOLVED
→ INSTALLED/CACHED
→ AVAILABLE
→ REMOVED
```

---

# 751.385 — Module Graph Lifecycle

```text
SOURCE
 ↓
PARSED
 ↓
SEMANTIC
 ↓
INTERFACE
 ↓
RESOLVED
 ↓
CODEGEN
 ↓
LINKED
 ↓
PACKAGED
```

---

# 751.386 — Implementation Requirement

Compiler implementation phải tách các subsystem:

```text
module/
    identity
    parser-interface
    dependency
    resolver
    fingerprint
    cache
    package
    linker-integration
    loader
    lifecycle
    security
    diagnostics
```

---

# 751.387 — Compiler Ownership

Compiler owns:

```text
semantic module
interface generation
dependency analysis
fingerprints
build graph
object generation coordination
```

---

# 751.388 — Linker Ownership

Linker owns:

```text
symbol resolution
object extraction
relocations
section layout
dead stripping
final native image
```

AXMODULE orchestrates nhưng không duplicate linker implementation.

---

# 751.389 — Loader Ownership

Runtime loader owns:

```text
dynamic mapping
relocation
runtime symbol resolution
module lifecycle
```

Platform-specific loader backend chịu OS details.

---

# 751.390 — Package Manager Ownership

Package infrastructure owns:

```text
download
registry
cache distribution
installation
```

AXMODULE chỉ yêu cầu resolved artifacts.

---

# 751.391 — Security Ownership

AXSECURITY owns:

```text
signature trust
capability
sandbox
permission
revocation
```

AXMODULE provides metadata và invokes security checks.

---

# 751.392 — Storage Ownership

AXSTORAGE owns:

```text
package files
module artifacts
cache persistence
```

---

# 751.393 — Process Ownership

AXPROCESS owns:

```text
address space
thread
execution
module code mapping context
```

---

# 751.394 — Memory Ownership

AXMEMORY owns:

```text
mapping
allocation
protection
W^X
page lifecycle
```

---

# 751.395 — Task Ownership

AXTASK owns:

```text
tasks
futures
async frames
executors
```

AXMODULE only ensures module code remains valid while tasks reference it.

---

# 751.396 — Async Ownership

AXASYNC owns:

```text
in-flight I/O
completion
timer
async operation
```

AXMODULE coordinates module lifetime with those operations.

---

# 751.397 — Final Architecture

```text
                         AXMODULE
                            │
       ┌────────────────────┼─────────────────────┐
       │                    │                     │
    Identity            Dependency             ABI
       │                    │                     │
       ▼                    ▼                     ▼
   Module ID          Resolver/Graph          AXABI
       │                    │                     │
       └──────────────┬─────┴─────────────────────┘
                      ▼
                  Build Plan
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Object       Static      Dynamic
                      │           │
                      └─────┬─────┘
                            ▼
                       Executable
```

Runtime:

```text
Dynamic Module
      │
      ▼
 AXSECURITY
      │
      ▼
 AXMEMORY
      │
      ▼
 AXPROCESS
      │
      ▼
 AXMODULE Loader
      │
      ├── AXTASK
      └── AXASYNC
```

---

# 751.398 — Critical Architectural Decision

Axiom sẽ **không biến module thành một runtime object bắt buộc**.

Có hai chế độ hoàn toàn hợp lệ:

### Static native

```text
Axiom source
 → modules
 → objects
 → linker
 → PE64/ELF/Mach-O/WASM
```

Sau link, module abstraction có thể biến mất hoàn toàn.

### Dynamic native

```text
Executable
 ↓
dynamic loader
 ↓
module metadata
 ↓
library/plugin
```

Module runtime chỉ tồn tại khi application thực sự cần dynamic loading.

Điều này giữ được mục tiêu **binary nhỏ + native performance cao** của Axiom.

---

# 751.399 — Definition of Done

```text
BOOTSTRAP-751
STATUS: COMPLETE / FROZEN

AXMODULE 5.0
 ├── Module Identity
 ├── Package Identity
 ├── Compilation Units
 ├── Interface Units
 ├── Implementation Units
 ├── Module Graph
 ├── Dependency Resolution
 ├── Version Constraints
 ├── ABI Constraints
 ├── Feature Resolution
 ├── Target Variants
 ├── Platform Variants
 ├── Import
 ├── Export
 ├── Re-export
 ├── Symbol Ownership
 ├── Module Initialization
 ├── Module Shutdown
 ├── Static Linking
 ├── Dynamic Linking
 ├── Plugin Boundary
 ├── Hot Reload Boundary
 ├── Module Security Metadata
 ├── Package Mapping
 ├── Precompiled Interface
 ├── Incremental Compilation
 ├── Module Cache
 ├── Generic Compilation Cache
 ├── LTO Integration
 ├── Reproducible Builds
 ├── Cross Compilation
 ├── System ABI Modules
 ├── External Library Integration
 ├── Native Artifact Composition
 ├── Module Loader
 ├── Module Lifecycle
 ├── Service Discovery
 ├── Module Diagnostics
 ├── ABI Inspection
 ├── Dependency Graph Inspection
 ├── Module Diff
 ├── AI Metadata
 ├── Security Integration
 ├── Deterministic Resolution
 ├── Module Simulation
 ├── Module Fuzzing
 ├── 40 Formal Invariants
 └── Native Module Runtime 5.0
```

## AXMODULE 5.0 — FROZEN

Một nguyên tắc quan trọng được khóa:

> **Axiom module là compiler/linker semantic unit trước khi nó là runtime entity.**

Vì vậy chương trình static native có thể hoàn toàn loại bỏ module runtime overhead sau khi link, trong khi dynamic library/plugin vẫn có đầy đủ module identity, ABI, lifecycle và security metadata.

---

# BOOTSTRAP-752 — AXBUILD

**Native Build, Dependency Resolution & Reproducible Compilation Runtime — workspace model, project model, build graph, source discovery, module discovery, dependency resolution, target selection, feature resolution, configuration profiles, incremental compilation, parallel compilation, memory-bounded scheduling, compiler cache, interface cache, object cache, LTO cache, generated sources, build scripts, code generation, resource compilation, cross compilation, SDK/sysroot selection, static/dynamic linkage planning, linker orchestration, artifact naming, reproducible builds, hermetic builds, build provenance, lockfiles, package integration, build diagnostics, dependency visualization, remote/cache-aware compilation, deterministic build scheduling, CI integration, build simulation, fault recovery và Native Build Runtime 5.0.**