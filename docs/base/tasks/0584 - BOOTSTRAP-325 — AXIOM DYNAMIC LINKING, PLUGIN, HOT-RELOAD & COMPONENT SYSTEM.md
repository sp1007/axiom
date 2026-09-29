# BOOTSTRAP-325 — AXIOM DYNAMIC LINKING, PLUGIN, HOT-RELOAD & COMPONENT SYSTEM

Sau 324, Axiom đã có ABI Contract và Binary Compatibility Engine. Đây là nền tảng để giải quyết một bài toán lớn hơn:

> **Làm thế nào để chương trình có thể nạp code/type/service mới tại runtime mà vẫn giữ ownership, capability, ABI, security và correctness của Axiom?**

Điểm quan trọng: Axiom **không nên coi dynamic loading là `dlopen + function pointer` được nâng cấp**.

Nó cần một **Component Model** rõ ràng.

---

# 325.1. Mục tiêu

Hệ thống phải hỗ trợ:

```text
Static linking
Dynamic library
Plugin
Component
Runtime loading
Optional unloading
Hot reload
Version negotiation
Capability negotiation
Sandbox boundary
```

nhưng vẫn giữ:

```text
Ownership
Capability
Effect
Concurrency
ABI
Security
```

---

# 325.2. Component ≠ Library

Phân biệt:

```text
Library
    reusable code/data

Dynamic Library
    independently loadable binary

Plugin
    dynamically discovered component

Component
    explicit ABI + capability + lifecycle contract
```

Một `.dll/.so/.dylib` chưa chắc là một Axiom Component.

---

# 325.3. Component Contract

Định nghĩa:

```text
ComponentContract {
    component_id
    version

    abi_version
    target

    exports
    imports

    types
    capabilities
    effects

    ownership_contracts

    lifecycle
    threading
    async

    security_policy
}
```

Ví dụ:

```text
ImageCodec
version 2.1

exports:
    decode
    encode

requires:
    filesystem.read

supports:
    async

threading:
    Send

abi:
    axiom-component-1
```

---

# 325.4. Component Identity

Không dùng filename làm identity.

Không:

```text
plugin.dll
```

làm identity.

Dùng:

```text
ComponentId
```

có thể là:

```text
package_id
component_name
publisher_namespace
```

Binary filename chỉ là deployment artifact.

---

# 325.5. Component Manifest

Mỗi component có metadata:

```text
component.axc
```

hoặc metadata section bên trong binary.

Ví dụ:

```text
component:
    id = "org.example.image"
    version = "2.1.0"

abi:
    axiom = 3

exports:
    image.decode
    image.encode

requires:
    memory
    logging

capabilities:
    filesystem.read

threading:
    concurrent

async:
    supported
```

---

# 325.6. Discovery

Host có thể tìm component theo:

```text
ComponentId
Version
ABI
Target
Capabilities
Features
```

Không load binary trước khi kiểm tra metadata nếu không cần thiết.

---

# 325.7. Version Negotiation

Host yêu cầu:

```text
ImageCodec >= 2.0 < 3.0
```

Component cung cấp:

```text
2.4.1
```

→ candidate.

Nhưng version matching chưa đủ.

Phải kiểm tra:

```text
ABI
capabilities
target
runtime
security
```

---

# 325.8. Capability Negotiation

Host:

```text
requires:
    image.decode
```

Plugin:

```text
provides:
    image.decode
```

Nhưng plugin còn yêu cầu:

```text
filesystem.read
network
gpu
```

Host không được cấp quyền ngầm.

Phải có:

```text
CapabilityGrant
```

---

# 325.9. Capability Boundary

Dynamic component là trust boundary.

Do đó:

```text
Host
  ↓
Component Boundary
  ↓
Plugin
```

mọi resource crossing boundary phải có contract.

Không được tự động truyền:

```text
raw pointer
view
mut_view
```

qua dynamic boundary nếu lifetime/provenance không được chứng minh.

---

# 325.10. Ownership Across Component Boundary

Ví dụ:

```text
create() -> Buffer
```

Component phải khai báo:

```text
return:
    owned
allocator:
    component
```

Nếu host muốn giải phóng:

```text
destroy(buffer)
```

thì contract phải chỉ rõ allocator/lifecycle.

---

# 325.11. Không Truyền Raw Pointer Mặc Định

Dynamic boundary không nên cho phép:

```text
*mut T
```

trở thành interface thông thường.

Nếu cần:

```text
unsafe extern
```

và phải có:

```text
ForeignContract
```

hoặc:

```text
ComponentUnsafeBoundary
```

---

# 325.12. Handle-Based Resources

Đối với resource dài hạn:

```text
GpuContext
File
Socket
Window
PluginObject
```

nên dùng:

```text
Handle<T>
```

hoặc opaque component handle.

Ví dụ:

```text
ImageHandle
DecoderHandle
```

Handle biểu diễn:

```text
logical identity
```

không phải raw memory address.

---

# 325.13. Component Object

Nếu component cần object identity:

```text
ComponentObject<T>
```

có thể cung cấp:

```text
handle
method dispatch
lifecycle
```

nhưng representation không được mặc định là C++-style object.

---

# 325.14. Trait Boundary

Trait object qua component boundary chỉ hợp lệ khi:

```text
@stable_trait_abi
```

hoặc contract tương đương.

Nếu không:

```text
dyn Trait
```

chỉ dùng nội bộ cùng ABI contract.

---

# 325.15. Component Interface

Interface có thể khai báo:

```text
interface ImageCodec {
    fn decode(input: view<u8>) -> Result<Image>
    fn encode(image: view<Image>) -> Result<Buffer>
}
```

Nhưng binary ABI sẽ được compiler lower thành:

```text
stable component ABI
```

Không expose trực tiếp internal representation.

---

# 325.16. Lifecycle

Component lifecycle:

```text
Discovered
    ↓
Validated
    ↓
Loaded
    ↓
Initialized
    ↓
Running
    ↓
Stopping
    ↓
Unloaded
```

Mỗi transition có precondition.

---

# 325.17. Initialization

Component initialization có thể:

- allocate;
- register services;
- start worker;
- open resources.

Nhưng phải khai báo effects.

Ví dụ:

```text
init:
    allocation
    thread_spawn
    filesystem.read
```

Host biết trước component sẽ làm gì.

---

# 325.18. Shutdown

Shutdown phải xử lý:

- active calls;
- outstanding handles;
- tasks;
- async operations;
- callbacks;
- external resources.

Không được:

```text
unload()
```

rồi để function pointer/task/callback trỏ vào code đã unload.

---

# 325.19. Unload Safety

Đây là invariant cực kỳ quan trọng.

Không được unload component nếu còn:

```text
live component object
live handle
live callback
live task
live future
live thread
live foreign pointer
```

Compiler/runtime phải theo dõi:

```text
ComponentLiveness
```

---

# 325.20. Reference Count Không Đủ

Không nên giải quyết bằng:

```text
Arc<Plugin>
```

một cách mù quáng.

Vì còn:

```text
callbacks
tasks
FFI handles
GPU events
thread-local state
```

Do đó cần:

```text
ComponentLease
```

hoặc:

```text
ComponentGeneration
```

để biểu diễn dependency của resource vào component code.

---

# 325.21. Component Lease

Ví dụ:

```text
let decoder = component.acquire<Decoder>()
```

`decoder` giữ:

```text
ComponentLease
```

Khi lease còn sống:

```text
component cannot unload
```

Compiler/runtime có thể tối ưu lease nếu lifetime statically known.

---

# 325.22. Hot Reload

Hot reload không đơn giản là:

```text
unload old
load new
```

Phải:

```text
Old Component
      ↓
Freeze
      ↓
Quiesce
      ↓
Migrate State
      ↓
Load New Component
      ↓
Validate ABI
      ↓
Restore State
      ↓
Resume
```

---

# 325.23. Quiescence

Trước reload:

```text
ComponentState = Quiescing
```

Không cho phép tạo operation mới.

Chờ:

```text
active_calls = 0
active_tasks = 0
callbacks = 0
```

hoặc chuyển chúng sang migration-safe state.

---

# 325.24. State Migration

Component v1:

```text
struct StateV1 {
    counter: u32
}
```

v2:

```text
struct StateV2 {
    counter: u64
    flags: u32
}
```

Không được memcpy:

```text
StateV1 → StateV2
```

trừ khi ABI/layout contract cho phép.

Thay vào đó:

```text
migrate_v1_to_v2()
```

được khai báo rõ.

---

# 325.25. Versioned State

State có:

```text
StateSchemaId
```

Ví dụ:

```text
ImageCodecState
schema = 4
```

Migration graph:

```text
1 → 2 → 3 → 4
```

Có thể cho phép:

```text
1 → 4
```

nếu migration trực tiếp tồn tại.

---

# 325.26. Hot Reload Safety

Hot reload chỉ được bật khi component khai báo:

```text
reloadable
```

và cung cấp:

```text
quiesce()
serialize_state()
deserialize_state()
resume()
```

hoặc compiler/runtime-generated equivalent.

---

# 325.27. Code Pointer Safety

Một vấn đề đặc biệt:

```text
callback = component.foo
```

Nếu component unload:

```text
callback → dangling code pointer
```

Axiom không cho phép.

Callback phải giữ:

```text
ComponentLease
```

hoặc được unregister trước unload.

---

# 325.28. Future Safety

Nếu:

```text
let f = plugin.async_operation()
```

Future giữ code của plugin.

Do đó:

```text
plugin.unload()
```

phải bị chặn khi Future còn sống.

---

# 325.29. Thread Safety

Nếu plugin spawn:

```text
worker thread
```

thread đó giữ component code.

Không thể unload cho đến khi:

```text
thread terminated
```

hoặc thread chuyển sang code/runtime khác theo contract.

---

# 325.30. GPU Safety

GPU kernel của component cũng có thể đang chạy.

Ví dụ:

```text
plugin.launch_kernel()
```

trả:

```text
GpuEvent
```

Component không được unload trước khi GPU work hoàn thành nếu kernel code nằm trong component image.

Do đó:

```text
GpuEvent
```

có thể giữ:

```text
ComponentLease
```

---

# 325.31. Dynamic Symbol Resolution

Resolver:

```text
Host
 ↓
SymbolTable
 ↓
Component
 ↓
Export
```

Symbol lookup phải kiểm tra:

```text
name
ABI
version
type
ownership
effect
capability
```

Không chỉ:

```text
strcmp(name)
```

---

# 325.32. Typed Symbol Lookup

Thay vì:

```text
get_symbol("foo")
```

rồi cast:

```text
unsafe_cast(...)
```

Axiom nên hỗ trợ:

```text
component.get<fn(i32) -> i32>("foo")
```

Compiler kiểm tra ABI contract.

Nếu type mismatch:

```text
LoadError::AbiMismatch
```

---

# 325.33. No Arbitrary Cast

Không cho:

```text
symbol → arbitrary function type
```

trong safe code.

Unsafe API vẫn có thể tồn tại cho system programming:

```text
unsafe resolve_raw_symbol(...)
```

nhưng phải chuyển qua verifier boundary.

---

# 325.34. Component Services

Component có thể export service:

```text
service Logger
service Allocator
service ImageCodec
service GPUBackend
```

Host resolve:

```text
get_service<ImageCodec>()
```

Service contract chứa:

```text
type
version
ABI
capabilities
lifecycle
```

---

# 325.35. Dependency Graph

Component dependencies:

```text
App
├── Graphics
│   ├── GPU
│   └── Window
└── ImageCodec
    └── Compression
```

Runtime phải giải dependency graph trước load.

Cycle:

```text
A → B
B → A
```

không nhất thiết luôn lỗi, nhưng phải có:

```text
Initialization SCC
```

và lifecycle semantics rõ ràng.

---

# 325.36. Component Initialization SCC

Nếu:

```text
A ↔ B
```

có thể:

```text
allocate
construct
link
initialize
```

theo phases:

```text
Load
Resolve
Construct
Initialize
Start
```

Không gọi arbitrary user initialization trong khi dependency chưa hoàn tất.

---

# 325.37. Sandboxed Component

Không phải plugin nào cũng trusted.

Axiom hỗ trợ:

```text
Trusted Component
Restricted Component
Sandboxed Component
Foreign Component
```

Sandbox boundary có thể giới hạn:

```text
filesystem
network
GPU
process
environment
memory
```

---

# 325.38. Component Effects

Manifest:

```text
effects:
    filesystem.read
    network.connect
    gpu.execute
```

Host policy:

```text
allowed:
    filesystem.read

denied:
    network.connect
```

Component load vẫn có thể thành công nhưng operation bị từ chối, hoặc host có thể reject trước load tùy policy.

---

# 325.39. Component Security

Component provenance:

```text
ComponentProvenance {
    publisher
    package
    version
    source_fingerprint
    build_fingerprint
    compiler
    signature
}
```

Security policy có thể yêu cầu:

```text
trusted publisher
signed artifact
known ABI
known source
```

---

# 325.40. Component Capability Revocation

Nếu host thu hồi:

```text
filesystem.read
```

component không được giữ một capability hợp lệ mãi mãi nếu policy yêu cầu revocation.

Có thể dùng:

```text
CapabilityToken
```

với:

```text
generation
revocation state
```

Tuy nhiên revocation semantics phải được thiết kế riêng, không được phá vỡ các invariant ownership hiện có.

---

# 325.41. Dynamic Dispatch Performance

Component boundary không nhất thiết chậm.

Compiler có thể tối ưu:

```text
known component
+
known ABI
+
unique implementation
```

thành direct call.

Nếu dynamic:

```text
indirect call
```

vẫn phải giữ ABI contract.

PGO từ 322 có thể giúp:

```text
hot component call
```

và devirtualize nếu uniqueness được chứng minh.

---

# 325.42. Component + Whole Program Analysis

Nếu component static:

```text
WholeProgramDB
```

có thể phân tích sâu.

Nếu dynamic:

```text
DynamicBoundary
```

thì compiler giữ conservative boundary.

Không được giả định:

```text
dynamic component = no effects
```

---

# 325.43. Component + `.axif`

Component đi kèm:

```text
component.axif
```

chứa:

- public interface;
- ABI;
- ownership;
- capability;
- effects;
- version;
- lifecycle;
- security;
- async/GPU contracts.

Runtime không cần parse toàn bộ compiler object model.

---

# 325.44. Component Binary Layout

Một binary component có thể:

```text
AXC image
├── Native code
├── Read-only data
├── Relocations/imports
├── Component manifest
├── ABI metadata
├── Semantic interface reference
├── Security metadata
└── Optional debug/profile metadata
```

---

# 325.45. Component Loader

Pipeline:

```text
Locate
 ↓
Read manifest
 ↓
Check target
 ↓
Check ABI
 ↓
Check version
 ↓
Check capabilities
 ↓
Check security policy
 ↓
Map image
 ↓
Resolve dependencies
 ↓
Relocate
 ↓
Verify exports
 ↓
Initialize
 ↓
Publish services
```

Không publish component trước khi validation hoàn thành.

---

# 325.46. Atomic Load

Component load phải có transactional semantics.

Nếu:

```text
dependency A loaded
dependency B failed
```

không để hệ thống ở trạng thái:

```text
half initialized
```

trừ khi dependency lifecycle contract cho phép.

---

# 325.47. Component Failure

Failure types:

```text
NotFound
VersionMismatch
AbiMismatch
TargetMismatch
CapabilityDenied
SecurityDenied
DependencyFailure
InitializationFailure
MigrationFailure
UnloadBlocked
```

Không biến mọi lỗi thành panic.

---

# 325.48. Integration với Runtime 306

Runtime component system hiện tại:

```text
Runtime Component
```

và 325:

```text
Dynamic Application Component
```

nên dùng chung lifecycle infrastructure.

Nhưng phải phân biệt:

```text
runtime component
```

với:

```text
application plugin
```

Runtime component có trust/capability level khác.

---

# 325.49. Integration với ABI 324

324 cung cấp:

```text
AbiContract
AbiCompatibilityEngine
```

325 không tạo ABI riêng.

Nó **sử dụng** 324 để validate:

```text
plugin ↔ host
service ↔ consumer
component ↔ component
```

---

# 325.50. Integration với Security 314

Security layer kiểm tra:

```text
signature
provenance
capability
trust level
sandbox
```

Component loader không được tự tạo security semantics mới.

---

# 325.51. Integration với Async

Nếu component có:

```text
async fn
```

Future phải giữ component lifetime.

Nếu:

```text
Future dropped
```

lease được release khi state machine không còn giữ component code.

---

# 325.52. Integration với Concurrency

Component boundary không phá:

```text
Send
Share
```

Nếu service không `Send`:

```text
cannot migrate to arbitrary thread
```

Nếu service `Share`:

```text
shared access
```

vẫn phải tuân synchronization contract.

---

# 325.53. Integration với GPU

GPU component:

```text
GpuBackend
```

có thể export:

```text
kernel
device service
allocator
```

Component lease phải sống đủ lâu cho:

```text
kernel
event
device resource
```

nếu code/resource phụ thuộc component.

---

# 325.54. Compiler APIs

```text
load_component_manifest()
```

```text
validate_component()
```

```text
resolve_component()
```

```text
negotiate_component()
```

```text
grant_component_capability()
```

```text
load_component()
```

```text
unload_component()
```

```text
check_unload_safety()
```

```text
quiesce_component()
```

```text
migrate_component_state()
```

```text
reload_component()
```

```text
resolve_service()
```

```text
resolve_typed_symbol()
```

```text
explain_component_failure()
```

---

# 325.55. Runtime APIs

```text
component.load()
component.acquire()
component.release()
component.quiesce()
component.reload()
component.services()
component.capabilities()
component.version()
component.abi()
```

API thực tế có thể được thiết kế lại khi Standard Library spec được mở rộng.

---

# 325.56. Implementation Tree

```text
runtime/component/
├── model/
│   ├── component.ax
│   ├── manifest.ax
│   ├── contract.ax
│   └── identity.ax
│
├── loader/
│   ├── discover.ax
│   ├── load.ax
│   ├── relocate.ax
│   ├── resolve.ax
│   └── publish.ax
│
├── lifecycle/
│   ├── state.ax
│   ├── initialize.ax
│   ├── shutdown.ax
│   ├── quiesce.ax
│   └── unload.ax
│
├── negotiation/
│   ├── version.ax
│   ├── abi.ax
│   ├── capability.ax
│   └── service.ax
│
├── ownership/
│   ├── lease.ax
│   ├── handle.ax
│   └── lifetime.ax
│
├── reload/
│   ├── reload.ax
│   ├── state.ax
│   ├── migration.ax
│   └── generation.ax
│
├── security/
│   ├── trust.ax
│   ├── sandbox.ax
│   └── provenance.ax
│
└── service/
    ├── registry.ax
    ├── resolver.ax
    └── dispatch.ax
```

Compiler side:

```text
compiler/component/
├── manifest/
├── contract/
├── compatibility/
├── interface/
├── validation/
├── symbol/
└── reload/
```

---

# 325.57. Invariants

```text
ACOMP-20  Dynamic loading is an explicit component boundary.

ACOMP-21  A dynamic library is not automatically an Axiom component.

ACOMP-22  Component identity is independent of filename.

ACOMP-23  Component loading requires ABI validation.

ACOMP-24  Component loading requires target compatibility.

ACOMP-25  Component capability requirements are explicit.

ACOMP-26  Host capabilities are never implicitly granted.

ACOMP-27  Raw pointers do not cross safe component boundaries.

ACOMP-28  Ownership crossing a component boundary is explicit.

ACOMP-29  Allocator domains crossing a component boundary are explicit.

ACOMP-30  Component handles represent logical identity, not implicit ownership of code.

ACOMP-31  A component cannot unload while live code-dependent resources remain.

ACOMP-32  Futures depending on component code keep the component alive.

ACOMP-33  Callbacks depending on component code keep the component alive.

ACOMP-34  Threads executing component code prevent unsafe unload.

ACOMP-35  GPU work depending on component code prevents unsafe unload.

ACOMP-36  Hot reload requires explicit reloadability.

ACOMP-37  Hot reload requires quiescence before code replacement.

ACOMP-38  Component state migration is explicit and versioned.

ACOMP-39  State layout cannot be assumed compatible across versions.

ACOMP-40  Symbol lookup must validate type and ABI.

ACOMP-41  Arbitrary symbol casts are unsafe.

ACOMP-42  Dynamic dispatch does not weaken ownership or capability rules.

ACOMP-43  Dynamic boundaries are conservative for whole-program analysis.

ACOMP-44  Component initialization is transactional.

ACOMP-45  Partial initialization cannot be published as a valid component.

ACOMP-46  Component security policy is enforced before capability-sensitive execution.

ACOMP-47  Component provenance is preserved.

ACOMP-48  Component failure is represented explicitly.

ACOMP-49  Runtime component infrastructure and application components share lifecycle principles but remain distinct trust domains.

ACOMP-50  Hot reload must preserve observable semantics or explicitly invalidate the affected state contract.
```

---

# 325.58. Definition of Done

BOOTSTRAP-325 hoàn thành khi:

1. Có Component Contract.
2. Có Component Manifest.
3. Có Component Identity.
4. Có dynamic discovery.
5. Có version negotiation.
6. Có ABI negotiation.
7. Có capability negotiation.
8. Có service registry.
9. Có typed symbol resolution.
10. Có component loader.
11. Có lifecycle state machine.
12. Có transactional initialization.
13. Có safe unload.
14. Có ComponentLease.
15. Có handle-based resource model.
16. Có callback lifetime tracking.
17. Có Future/component lifetime tracking.
18. Có thread/component lifetime tracking.
19. Có GPU/component lifetime tracking.
20. Có hot-reload protocol.
21. Có quiescence.
22. Có versioned state schema.
23. Có state migration.
24. Có component generation tracking.
25. Có sandboxed component model.
26. Có capability revocation model.
27. Có security/provenance integration.
28. Có `.axif` integration.
29. Có ABI engine integration.
30. Có linker integration.
31. Có runtime integration.
32. Có async integration.
33. Có concurrency integration.
34. Có GPU integration.
35. Có whole-program/dynamic-boundary integration.
36. Có tests load/unload.
37. Có tests ABI mismatch.
38. Có tests capability denial.
39. Có tests dangling callback prevention.
40. Có tests Future preventing unload.
41. Có tests thread preventing unload.
42. Có tests GPU preventing unload.
43. Có tests state migration.
44. Có tests failed migration rollback.
45. Có tests malicious/corrupt component.
46. Có tests sandbox boundary.
47. Có tests typed symbol lookup.
48. Có tests static-vs-dynamic component equivalence.
49. Có tests hot reload không tạo dangling code reference.
50. Có end-to-end plugin lifecycle.

---

## Nguyên tắc đóng băng của 325

> **Code có thể được nạp và thay thế dynamically, nhưng ownership của code cũng phải được quản lý như ownership của dữ liệu.**

Đây là điểm khác biệt quan trọng của Axiom.

Thay vì:

```text
DLL
 ↓
function pointer
 ↓
hope it remains valid
```

Axiom hướng tới:

```text
Component
   ↓
ABI Contract
   ↓
Capability Contract
   ↓
Ownership/Lifetime Contract
   ↓
Component Lease
   ↓
Typed Service
   ↓
Verified Execution
```

Và hot reload:

```text
Running
   ↓
Quiesce
   ↓
Verify no dependent code remains
   ↓
Migrate state
   ↓
Load new generation
   ↓
Validate ABI
   ↓
Publish
   ↓
Resume
```

Như vậy dynamic loading không trở thành một “lỗ hổng” nằm ngoài semantic model của Axiom, mà trở thành **một execution/storage/trust boundary được compiler và runtime hiểu chính thức**.