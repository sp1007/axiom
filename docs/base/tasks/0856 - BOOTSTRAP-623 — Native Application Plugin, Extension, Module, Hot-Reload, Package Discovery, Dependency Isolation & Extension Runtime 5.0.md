Tiếp tục với **BOOTSTRAP-623** — lớp mở rộng ứng dụng, nhưng được thiết kế để giữ core Axiom nhỏ, an toàn và không biến plugin thành dependency bắt buộc.

:::writing{variant="document" id="74261" title="BOOTSTRAP-623 — Native Application Plugin, Extension, Module, Hot-Reload, Package Discovery, Dependency Isolation & Extension Runtime 5.0"}
# BOOTSTRAP-623 — Native Application Plugin, Extension, Module, Hot-Reload, Package Discovery, Dependency Isolation & Extension Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Application Extension / Module Runtime  
**Depends on:** BOOTSTRAP-600 → 622

---

# 1. Purpose

BOOTSTRAP-623 defines the native extension architecture for Axiom applications:

- modules;
- plugins;
- extensions;
- optional application features;
- package discovery;
- dependency resolution;
- ABI/API boundaries;
- extension lifecycle;
- isolation;
- capability provisioning;
- hot-load;
- hot-unload;
- hot-reload;
- version compatibility;
- extension configuration;
- extension resources;
- extension UI;
- extension commands;
- extension services;
- extension IPC;
- extension diagnostics.

The design must preserve Axiom's primary goals:

- native performance;
- small binaries;
- deterministic behavior;
- no mandatory plugin runtime;
- no mandatory garbage collector;
- no mandatory scripting VM;
- explicit security boundaries;
- static linking when preferred;
- dynamic loading only when explicitly requested.

---

# 2. Core Principle

An Axiom application must be able to exist in three forms:

```text
Static Application
    ↓
all required modules linked into executable

Modular Application
    ↓
modules loaded dynamically

Isolated Extension Application
    ↓
extensions execute out-of-process
```

The language itself does not require dynamic plugins.

---

# 3. Architectural Position

```text
613 Package / CAS
        │
        ▼
623 Extension Runtime
        │
 ┌──────┼───────────────┐
 ▼      ▼               ▼
Module Plugin       Extension
 │      │               │
 └──────┼───────────────┘
        ▼
Application Services
        │
 ┌──────┼─────────────┐
 ▼      ▼             ▼
620    621            622
State  Documents      Workspace
        │
        ▼
       619
```

---

# 4. Definitions

## Module

A compiled unit providing code and metadata.

## Plugin

A module intended to extend an existing application.

## Extension

A plugin plus declared extension points and application integration.

## Provider

A module implementing a runtime-defined service interface.

## Package

The distributable unit defined by 613.

---

# 5. No Mandatory Plugin Model

Axiom applications may contain no plugin system at all.

The compiler must eliminate unused extension runtime components.

---

# 6. Static Module

A static module is linked directly into the executable.

```text
app.exe
 ├── core
 ├── graphics
 └── editor
```

No dynamic loading occurs.

---

# 7. Dynamic Module

A dynamic module is loaded at runtime.

Platform mapping:

```text
Windows  → DLL
Linux    → SO
macOS    → DYLIB
Android  → platform-supported native module
iOS      → statically packaged / restricted dynamic model
WASM     → host module boundary
```

The runtime abstracts the native representation.

---

# 8. Module Identity

Every module has:

```text
ModuleId
PublisherId
ModuleVersion
BuildId
AbiId
TargetId
```

---

# 9. Module ID

`ModuleId` is globally unique within an application's package ecosystem.

Recommended representation:

```text
module.vendor.feature
```

---

# 10. Version

A module version contains:

```text
major
minor
patch
```

Optional prerelease/build metadata may exist.

---

# 11. Compatibility

Compatibility is determined by explicit declarations.

Axiom must not assume that:

```text
1.2.0
```

is ABI-compatible with:

```text
1.3.0
```

without metadata.

---

# 12. ABI Identity

Dynamic modules declare:

```text
AbiId
```

containing:

- target architecture;
- calling convention;
- pointer width;
- endianness;
- compiler ABI revision;
- runtime ABI revision;
- relevant feature ABI.

---

# 13. ABI Boundary

The ABI must use stable primitive/layout definitions.

---

# 14. ABI Rule

No implicit transfer of:

- compiler-private types;
- internal allocator state;
- private runtime objects;
- unstable closures;
- compiler-generated anonymous layouts.

---

# 15. Stable ABI Types

Allowed ABI values include:

```text
integers
floats
bool
UTF-8 slices
byte slices
stable structs
stable enums
opaque handles
function tables
error codes/results
```

---

# 16. Ownership

Every ABI resource has explicit ownership.

Possible policies:

```text
Borrowed
Owned
Shared
Transferred
```

---

# 17. No Raw Cross-Module Pointer Contract

A raw pointer may exist internally but must not be the default public plugin ABI.

Opaque handles are preferred.

---

# 18. Handle Identity

Handles use generation-safe IDs.

```text
Handle {
    index
    generation
}
```

---

# 19. Module Entry Point

Every dynamic module exposes one stable entry point:

```text
axiom_module_entry()
```

The exact binary signature is ABI-defined.

---

# 20. Module Descriptor

The entry point returns a static descriptor:

```text
ModuleDescriptor {
    abi
    metadata
    capabilities
    extension_points
    lifecycle
}
```

---

# 21. Descriptor Immutability

Descriptor memory must remain valid for the lifetime of the loaded module.

---

# 22. Module Initialization

Lifecycle:

```text
Discovered
→ Verified
→ Loaded
→ Initialized
→ Active
```

---

# 23. Shutdown Lifecycle

```text
Active
→ Quiescing
→ Stopping
→ Unloaded
```

---

# 24. Failure States

A module may enter:

```text
Rejected
Failed
Quarantined
Unloading
```

---

# 25. Module Lifecycle API

Conceptually:

```text
module_load()
module_initialize()
module_start()
module_quiesce()
module_stop()
module_unload()
```

---

# 26. Lifecycle Ownership

The extension manager owns module lifecycle.

Application code cannot arbitrarily unload a module still containing active resources.

---

# 27. Quiescence

Before unload:

```text
new calls blocked
active calls drained
tasks cancelled/drained
callbacks disconnected
resources released
```

---

# 28. No Unsafe Unload

If active references remain, unload fails or is deferred.

---

# 29. Extension Context

Every extension receives:

```text
ExtensionContext
```

containing only explicitly granted services/capabilities.

---

# 30. Context Services

Examples:

```text
Logger
Config
Storage
Scheduler
Network
IPC
Commands
Documents
Workspace
GUI
Graphics
Media
```

---

# 31. Capability Boundary

Services are capability-controlled through 603.

---

# 32. No Ambient Privilege

Loading a plugin does not automatically grant:

- filesystem access;
- network;
- process creation;
- camera;
- microphone;
- GPU;
- arbitrary native code execution outside the plugin itself.

---

# 33. Requested Capabilities

Module manifest declares:

```text
requires:
    filesystem.read
    network.connect
```

---

# 34. Granted Capabilities

Runtime computes:

```text
granted =
    declared
    ∩
    application policy
    ∩
    user policy
    ∩
    platform policy
```

---

# 35. Capability Attenuation

An extension may receive a restricted capability derived from the host capability.

---

# 36. Capability Revocation

Long-running extension capabilities may be revoked by 603.

The extension must handle resulting errors.

---

# 37. Trust Levels

A module may be classified:

```text
Trusted
Verified
Sandboxed
Untrusted
Blocked
```

These are security states, not quality rankings.

---

# 38. Signature Verification

Packages may contain publisher signatures through 610/613.

---

# 39. Publisher Identity

Publisher identity is independent from module identity.

---

# 40. Package Discovery

623 discovers extensions from:

```text
application package
installation directory
user extension directory
workspace-local package store
system package store
explicit runtime path
```

Only configured sources are searched.

---

# 41. Search Order

Search order is deterministic and configured by policy.

---

# 42. Path Security

Discovery must prevent:

- path traversal;
- unexpected relative paths;
- unsafe symlink traversal;
- DLL/SO hijacking;
- loading from untrusted directories when prohibited.

---

# 43. Package Integration

Extensions may be distributed through AXPK/613.

---

# 44. Package Manifest

Extension package contains:

```text
.axmanifest
```

with:

```text
module_id
version
publisher
targets
abi
dependencies
capabilities
extension_points
entry
resources
signature
```

---

# 45. Dependency Graph

Modules may depend on other modules.

```text
A
├── B
└── C
    └── D
```

---

# 46. Dependency Resolution

Resolver validates:

- module identity;
- version constraints;
- ABI;
- target;
- architecture;
- capabilities;
- trust;
- package integrity.

---

# 47. Dependency Cycles

Cycles are rejected unless an explicitly supported interface-only cycle is represented without runtime initialization dependency.

---

# 48. Initialization Order

Dependencies initialize before dependents.

---

# 49. Shutdown Order

Dependents stop before dependencies.

---

# 50. Optional Dependencies

Dependencies may be:

```text
Required
Optional
FeatureConditional
```

---

# 51. Feature Dependencies

A module may expose optional features:

```text
feature.audio
feature.video
feature.gpu
```

---

# 52. Capability vs Dependency

Dependency means:

> this module needs another implementation.

Capability means:

> this module is allowed to perform an operation.

They must remain distinct.

---

# 53. Module Resolver

```text
ModuleResolver
```

returns a deterministic dependency graph.

---

# 54. Lock File

Applications may maintain:

```text
.axlock
```

recording resolved package versions and hashes.

---

# 55. Reproducibility

Given identical:

- manifest;
- lock file;
- package store;

resolution must produce the same dependency graph.

---

# 56. Content Verification

Package content hashes are validated through 613/610.

---

# 57. Package Cache

Modules can be stored in the 613 CAS.

---

# 58. Duplicate Modules

Content-identical packages should share CAS objects.

---

# 59. Module Loading

The loader verifies:

```text
target
ABI
signature
hash
dependencies
```

before activation.

---

# 60. Dynamic Loader

Platform adapters provide:

```text
load_library
resolve_symbol
unload_library
```

---

# 61. Symbol Resolution

Public symbols are explicitly exported.

No automatic export of all module symbols.

---

# 62. Symbol Namespace

Module symbols use stable namespaces.

---

# 63. Symbol Versioning

ABI symbols may carry version identifiers.

---

# 64. Function Tables

Preferred ABI mechanism:

```text
HostApiV1
PluginApiV1
```

rather than unrestricted symbol coupling.

---

# 65. ABI Evolution

New API versions are additive.

---

# 66. API Negotiation

Module initialization negotiates supported API version.

---

# 67. Backward Compatibility

Host may expose multiple API versions simultaneously.

---

# 68. Forward Compatibility

Unknown optional function pointers are treated as unavailable.

---

# 69. Error Boundary

Cross-module failures use stable error/result representations.

---

# 70. Panic Boundary

A plugin panic/unhandled exception must not cross the ABI boundary.

---

# 71. Panic Conversion

It becomes:

```text
PluginFailure
```

and is reported through 602/605.

---

# 72. Resource Ownership

The extension runtime tracks resources associated with each module.

---

# 73. Resource Registry

```text
ExtensionResourceRegistry
```

tracks:

- tasks;
- subscriptions;
- windows;
- views;
- commands;
- timers;
- sockets;
- file handles;
- GPU objects;
- media sessions.

---

# 74. Automatic Cleanup

Automatic cleanup applies only to runtime-owned registrations.

It must not imply garbage collection.

---

# 75. Resource Cleanup

On extension stop:

```text
cancel
disconnect
close
release
```

resources according to ownership rules.

---

# 76. Task Cleanup

Tasks created by an extension are attached to an extension scope.

---

# 77. Task Cancellation

Quiescing cancels extension-owned tasks unless explicitly detached with policy approval.

---

# 78. Detached Tasks

Detached tasks require explicit ownership transfer.

---

# 79. Subscription Cleanup

620/619 subscriptions are automatically disconnected when owned by the extension context.

---

# 80. UI Extensions

Plugins can register:

```text
Control
Panel
ToolWindow
Menu
Toolbar
Command
Dialog
DocumentView
```

---

# 81. UI Registration

UI extensions use 619/622 registration APIs.

---

# 82. UI Unload

Before unload:

```text
views close
panels detach
commands unregister
bindings disconnect
```

---

# 83. Workspace Integration

Extensions can register workspace panels and layout contributions.

---

# 84. Workspace Persistence

Extension-specific workspace state must be namespaced.

Example:

```text
plugin.vendor.tool.settings
```

---

# 85. Missing Extension

If an extension is missing, its persisted state remains available as opaque data where safe.

---

# 86. Extension Restoration

When the extension returns, its state can be restored.

---

# 87. Command Extensions

Plugins can register commands with 620.

---

# 88. Command IDs

Command IDs are globally namespaced.

```text
vendor.plugin.command
```

---

# 89. Command Collision

Duplicate command IDs are rejected.

---

# 90. Menu Contributions

Extensions contribute declarative menu items.

---

# 91. No Arbitrary Menu Code

Menu declarations contain data and command IDs.

---

# 92. Document Extensions

Plugins can register document providers:

```text
*.foo
*.bar
```

---

# 93. Document Provider

Provider implements:

```text
open
load
save
validate
```

according to 621.

---

# 94. Format Detection

File type detection must not execute arbitrary file content.

---

# 95. Parser Isolation

Untrusted document parsers may execute out-of-process.

---

# 96. Service Extensions

Extensions may provide application services.

Example:

```text
SearchService
CompilerService
AssetService
LanguageService
```

---

# 97. Service Registry

```text
ServiceRegistry
```

maps stable interface IDs to providers.

---

# 98. Service Versioning

Interfaces have explicit versions.

---

# 99. Service Lifetime

Possible policies:

```text
Singleton
PerApplication
PerWorkspace
PerDocument
PerRequest
```

---

# 100. Provider Selection

Multiple implementations can coexist.

Selection is determined by explicit policy rather than hidden priority.

---

# 101. Extension Points

An application declares:

```text
ExtensionPointId
```

and its expected interface.

---

# 102. Extension Point Descriptor

Contains:

```text
id
api_version
allowed_scope
required_capabilities
lifecycle
multiplicity
```

---

# 103. Extension Registration

An extension registers only against known extension points.

---

# 104. Unknown Extension Point

The extension is not activated for unsupported points.

---

# 105. Optional Extension Point

Applications may expose optional extension points.

---

# 106. Declarative Contributions

Prefer metadata for:

- commands;
- menus;
- file types;
- themes;
- panels;
- routes;
- document providers.

---

# 107. Programmatic Contributions

Allowed when behavior genuinely requires code.

---

# 108. Declarative First

Declarative metadata improves:

- validation;
- startup;
- tooling;
- security;
- AI inspection.

---

# 109. Extension Metadata

Compiler generates:

```text
.axext
```

containing:

```text
module
extension_points
commands
routes
documents
resources
capabilities
dependencies
```

---

# 110. AI-Readable Metadata

Metadata should be deterministic and machine-readable.

---

# 111. Static Extension Registry

For static builds:

```text
StaticExtensionRegistry
```

is generated by the compiler/linker.

---

# 112. Dynamic Registry

For dynamic builds:

```text
DynamicExtensionRegistry
```

loads descriptors from packages.

---

# 113. Static vs Dynamic Equivalence

An extension should expose the same logical API regardless of static/dynamic packaging.

---

# 114. Link-Time Registration

Static extension registration should not require runtime discovery.

---

# 115. Dead Stripping

Unused static extensions must be removable by the linker.

---

# 116. Minimal Build

An application with no extension points should contain zero extension runtime code.

---

# 117. Hot Load

A module may be loaded while the application is running if its extension point permits dynamic loading.

---

# 118. Hot Unload

A module may be unloaded only after successful quiescence.

---

# 119. Hot Reload

Hot reload means:

```text
old module
→ quiesce
→ serialize transferable state
→ unload
→ load new module
→ validate
→ restore state
→ resume
```

---

# 120. Reload Boundary

Only declared transferable state participates.

---

# 121. Code State

Function pointers into the old module cannot survive reload.

---

# 122. Callback Safety

Every callback registered by a module is automatically invalidated during quiescence.

---

# 123. VTable Safety

Old vtables must never remain callable after unload.

---

# 124. Task Safety

Tasks executing old module code must finish/cancel before unload.

---

# 125. Thread Safety

Threads owned by the extension must terminate before unload.

---

# 126. Thread Transfer

Threads cannot silently become host-owned during reload.

---

# 127. GPU Safety

GPU resources containing module-specific callbacks/shader objects are drained/released or reconstructed.

---

# 128. GUI Safety

Views created by the old module are detached before unload.

---

# 129. State Migration

Reload can specify:

```text
state_schema_version
migration
```

---

# 130. Failed Reload

If the new module fails validation, the old module may remain active when technically possible.

---

# 131. Transactional Reload

Preferred sequence:

```text
prepare new
validate new
quiesce old
transfer state
activate new
commit
```

---

# 132. Rollback

If activation fails after old-module quiescence, rollback is attempted only if the old module remains loaded and valid.

---

# 133. Hard Failure

If rollback is impossible, the extension remains disabled and diagnostics preserve failure information.

---

# 134. Hot Reload Limitations

Some modules cannot safely hot reload:

- ABI providers with persistent external references;
- low-level device drivers;
- process-global hooks;
- platform modules requiring restart;
- modules with unsupported native state.

They must declare:

```text
hot_reload: false
```

---

# 135. Extension State

Extension state may be divided into:

```text
Configuration
PersistentState
SessionState
EphemeralState
```

---

# 136. Persistence

Persistent state uses 600/612/611.

---

# 137. Secret State

Secrets use `Secret<T>` and are excluded from ordinary extension-state serialization.

---

# 138. Session State

Session state may be restored after application restart.

---

# 139. Ephemeral State

Ephemeral state is never required for successful recovery.

---

# 140. State Namespacing

Every extension state key contains its stable module identity.

---

# 141. Configuration

Extension configuration integrates with 601.

---

# 142. Configuration Isolation

An extension cannot overwrite another extension's configuration namespace.

---

# 143. Configuration Capability

Only declared configuration fields are exposed to the extension.

---

# 144. Extension Logging

602 automatically attaches:

```text
module_id
publisher_id
instance_id
```

to extension logs.

---

# 145. Diagnostics

Extension failures include:

```text
module
version
build_id
abi
package_hash
capabilities
dependency_graph
```

---

# 146. No Secret Logging

Capability tokens, secrets and private keys are never automatically included.

---

# 147. Crash Handling

If an in-process extension crashes the host process, 602/605 records the extension identity.

---

# 148. Out-of-Process Extension

For stronger isolation:

```text
Application
    │
   IPC
    │
Extension Process
```

using 604/605.

---

# 149. Out-of-Process Advantages

Provides isolation for:

- untrusted parsers;
- unstable providers;
- large optional systems;
- risky third-party integrations.

---

# 150. IPC Contract

Out-of-process extensions use versioned 604 schemas.

---

# 151. Process Supervision

605 supervises extension processes.

---

# 152. Restart

Extension processes can be restarted independently.

---

# 153. State Recovery

State is reconstructed from 600/612 rather than relying on process memory.

---

# 154. Extension Health

An extension can expose:

```text
Healthy
Degraded
Unhealthy
```

to 605.

---

# 155. Resource Limits

606 may limit:

- CPU;
- memory;
- threads;
- handles;
- GPU;
- network;
- storage;
- IPC.

---

# 156. Extension Quotas

Applications can specify per-extension quotas.

---

# 157. Network Isolation

Network capability is explicit.

---

# 158. Filesystem Isolation

Filesystem capability uses 603 path-scoped capabilities.

---

# 159. Process Isolation

Extensions cannot spawn arbitrary processes without explicit capability.

---

# 160. Dynamic Code

A plugin is already executable code, but loading it does not grant additional dynamic-code capabilities to the plugin.

---

# 161. JIT

If an extension requests JIT execution, 603 policy applies separately.

---

# 162. Native FFI

Extensions may use FFI only according to their declared capability and package policy.

---

# 163. Unsafe Code

Unsafe code inside a trusted extension does not automatically grant unsafe privileges to the host.

---

# 164. Extension Sandboxing

Sandboxed extensions may receive only:

```text
ExtensionContext
```

with restricted APIs.

---

# 165. No Global Mutable Registry

Registries are scoped to an application/runtime instance.

---

# 166. Module Instances

One module binary may have multiple instances.

---

# 167. Instance Identity

```text
ExtensionInstanceId
```

distinguishes instances.

---

# 168. Instance Scope

An instance may be:

```text
Application
Workspace
Document
Window
```

scoped.

---

# 169. Instance Configuration

Each instance receives an immutable configuration snapshot.

---

# 170. Reconfiguration

Configuration changes create a new snapshot.

---

# 171. Live Configuration

Extensions may subscribe to configuration changes.

---

# 172. Configuration Transaction

Multiple configuration fields can update atomically.

---

# 173. Extension Events

Lifecycle events:

```text
Loaded
Initialized
Started
Suspended
Resumed
Quiescing
Stopped
Failed
Unloaded
```

---

# 174. Suspension

Mobile/background platforms may suspend an extension.

---

# 175. Resume

Resume must not assume native handles remain valid.

---

# 176. Device Loss

Extensions using 614/615 resources must support reconstruction after device loss.

---

# 177. Network Loss

Extensions using 609 must support reconnect or explicit failure.

---

# 178. Storage Loss

Extensions must handle read-only/full/unavailable storage.

---

# 179. Package Update

A package update creates a new immutable package version.

---

# 180. Atomic Extension Update

Update flow:

```text
download
verify
install
resolve
prepare
activate
```

---

# 181. Failed Update

Previous version remains available for rollback.

---

# 182. Version Pinning

Applications may pin exact package versions.

---

# 183. Dependency Update

Dependency changes require resolver validation before activation.

---

# 184. Update Isolation

Updating one extension must not silently replace another extension's dependencies.

---

# 185. Shared Dependency

If multiple modules share a dependency, update requires compatibility validation for all consumers.

---

# 186. Dependency Side-by-Side

Where ABI permits, multiple versions may coexist in isolated module contexts.

---

# 187. Global Singleton Restriction

A dependency requiring process-global singleton state may prevent side-by-side loading.

It must declare this restriction.

---

# 188. Module Isolation Modes

```text
SharedProcess
PrivateProcess
SandboxProcess
```

---

# 189. SharedProcess

Lowest overhead.

---

# 190. PrivateProcess

Independent failure domain.

---

# 191. SandboxProcess

Restricted capabilities.

---

# 192. Extension Startup

Startup should be lazy by default.

---

# 193. Activation Modes

```text
Always
OnDemand
OnCommand
OnRoute
OnFileType
OnWorkspace
OnServiceRequest
```

---

# 194. Lazy Activation

Opening a `.foo` document may activate only the provider supporting `.foo`.

---

# 195. Startup Performance

Extensions not required during startup must not execute startup code.

---

# 196. Parallel Initialization

Independent extensions may initialize concurrently.

---

# 197. Initialization Dependency

Dependent modules wait for required dependencies.

---

# 198. Initialization Timeout

Long initialization must be cancellable or bounded by policy.

---

# 199. Startup Failure

Optional extensions may fail without failing the application.

Required modules can fail application startup according to manifest policy.

---

# 200. Extension Disable

An extension can be disabled by:

- application policy;
- security policy;
- user configuration;
- crash-loop protection.

---

# 201. Crash Loop

Repeated extension crashes trigger quarantine.

---

# 202. Quarantine

Quarantined extensions are not automatically activated.

---

# 203. Recovery

The application can explicitly request reactivation.

---

# 204. Diagnostics for Quarantine

602 records:

```text
crash_count
failure_window
last_failure
package_hash
```

---

# 205. Extension Health Monitor

605 may supervise out-of-process extensions.

---

# 206. In-Process Health

In-process extensions cannot provide complete fault isolation; this is documented by the architecture.

---

# 207. Extension Contracts

Every extension point must define:

```text
ABI
lifecycle
ownership
threading
error model
capabilities
versioning
```

---

# 208. Threading Contract

Each extension point declares:

```text
UIThread
WorkerThread
AnyThread
SingleExecutor
```

---

# 209. Send/Sync

Cross-thread extension objects must satisfy 608's concurrency traits.

---

# 210. UI Thread

UI extensions execute on the 619 UI executor.

---

# 211. Background Service

Background extensions use 607 executors.

---

# 212. Callback Thread

Callback thread affinity must be explicit.

---

# 213. Async ABI

Async extension APIs use stable future/task handles rather than compiler-private coroutine layouts.

---

# 214. Cancellation

Every potentially long-running extension operation should support cancellation.

---

# 215. Timeout

Host may impose operation deadlines.

---

# 216. Backpressure

Streaming extension APIs must support bounded queues/backpressure.

---

# 217. Memory Ownership

Cross-module buffers use explicit:

```text
borrow
copy
owned
shared
```

semantics.

---

# 218. Shared Buffer

Shared memory buffers use 604/614 abstractions.

---

# 219. Zero-Copy

Zero-copy is permitted where provider and ABI allow compatible memory ownership.

---

# 220. Serialization Fallback

When zero-copy is unavailable, 612 serialization provides portable transfer.

---

# 221. Extension IPC

Out-of-process extension messages use schema-defined AXBIN/604 framing.

---

# 222. IPC Security

Capability tokens are transferred only through explicit 603 mechanisms.

---

# 223. Networked Extensions

A network service is not automatically an extension.

It becomes an extension only when registered through the extension protocol.

---

# 224. Remote Extension

Remote extension execution is an optional higher-level architecture.

---

# 225. Remote Trust

Remote modules require independent authentication and authorization.

---

# 226. Extension Marketplace Boundary

Axiom does not require a centralized marketplace.

---

# 227. Package Source

Package sources can be:

```text
local
enterprise
private registry
public registry
file
HTTP
```

subject to 603/610/613.

---

# 228. Registry Protocol

Registry communication is outside the core extension ABI.

---

# 229. Offline Installation

Packages can be installed from local AXPK files.

---

# 230. Package Verification Before Install

Package signature/hash is verified before activation.

---

# 231. No Install-Time Execution

Package installation itself must not execute extension code.

---

# 232. Activation-Time Execution

Code begins execution only when activation occurs.

---

# 233. Package Inspection

CLI/API:

```text
axiom ext inspect package.axpk
```

can display:

- identity;
- version;
- target;
- dependencies;
- capabilities;
- signatures;
- extension points.

---

# 234. Package Verification

```text
axiom ext verify package.axpk
```

performs integrity and policy checks.

---

# 235. Dependency Graph

```text
axiom ext graph
```

produces deterministic graph output.

---

# 236. Extension List

```text
axiom ext list
```

reports installed/loaded/disabled modules.

---

# 237. Extension Diagnostics

```text
axiom ext doctor
```

reports:

- ABI mismatch;
- missing dependency;
- invalid signature;
- denied capability;
- crash loop;
- resource exhaustion.

---

# 238. AI Metadata

CLI can export `.axext` metadata for AI tooling.

---

# 239. Compiler Integration

Compiler understands:

```text
@module
@plugin
@extension
@extension_point
@requires
@provides
@abi
```

---

# 240. Example

```text
@extension(
    id = "example.image_tools",
    version = "1.2.0",
    capabilities = ["filesystem.read"]
)
struct ImageTools {
}
```

---

# 241. Struct-Only Architecture

No plugin base class is required.

---

# 242. Extension Interface

An extension point is implemented by ordinary structs/functions satisfying a declared trait/interface contract.

---

# 243. Example Extension

```text
trait ImageImporter {
    fn can_open(self, path: Path) -> bool
    fn open(self, path: Path) -> Result<DocumentHandle>
}

struct PngImporter {
}

impl ImageImporter for PngImporter {
    ...
}
```

---

# 244. Registration

```text
register_provider(
    extension_point = ImageImporter,
    provider = PngImporter
)
```

---

# 245. Override

Extension providers may replace default implementations only when the extension point explicitly allows override.

---

# 246. Override Policy

Possible policies:

```text
Single
Multiple
Fallback
Chain
OverrideAllowed
```

---

# 247. No Accidental Override

Registration conflicts are explicit errors.

---

# 248. Provider Priority

Priority is used only when the extension point explicitly defines a deterministic priority mechanism.

---

# 249. No Hidden Magic

Axiom does not infer plugin precedence from load order.

---

# 250. Static Registration Example

```text
@provides(ImageImporter)
struct PngImporter {
}
```

Compiler generates registry metadata.

---

# 251. Dynamic Registration Example

Package manifest declares:

```text
provides:
    image.importer.v1
```

---

# 252. Registry Lookup

Lookup by stable interface ID + version.

---

# 253. Multiple Providers

The registry may return a collection of compatible providers.

---

# 254. Provider Lifecycle

Providers can be:

```text
Stateless
Singleton
Scoped
PerRequest
```

---

# 255. Service Shutdown

Services stop before their provider module unloads.

---

# 256. Extension Resource Namespace

Every extension gets a resource namespace.

Example:

```text
ext://vendor.image/icons/open.axpng
```

---

# 257. Resource Loading

Resources use 613 package/VFS abstractions.

---

# 258. Localization

Extension localization integrates with 617 and `.axloc`.

---

# 259. Theme Integration

Extension controls can contribute theme metadata without overriding host global theme definitions unless explicitly allowed.

---

# 260. Graphics

Extensions can contribute 615 resources.

---

# 261. Shader Packages

Shader resources are verified through 610/613 and validated by 615.

---

# 262. Media

Extensions can contribute codecs/providers through 616.

---

# 263. Device Providers

Low-level device providers may require privileged deployment and cannot assume ordinary plugin permissions.

---

# 264. Driver Boundary

Actual kernel/device drivers are outside ordinary 623 plugin execution.

---

# 265. Compiler Providers

An extension can provide compiler services but must respect compiler ABI boundaries.

---

# 266. Language Server

Language tooling may be an extension/service using 604/623.

---

# 267. AI Provider

AI-related services can be extensions.

The core language remains independent from any particular AI vendor/model.

---

# 268. Model Resource

Large models belong in 613 package/CAS infrastructure rather than inside the plugin binary.

---

# 269. Model Loading

Models use 614/606 resource governance and explicit filesystem/GPU capabilities.

---

# 270. Extension Configuration UI

Extensions can register configuration pages through 619/622.

---

# 271. Configuration Schema

Configuration schemas are statically inspectable.

---

# 272. Validation

Configuration validation can run before activation.

---

# 273. Async Validation

Async validation uses 607 and cancellation.

---

# 274. Extension Dependencies on UI

A headless application can reject extensions requiring GUI capabilities.

---

# 275. Target Filtering

Manifest declares supported:

```text
OS
architecture
ABI
feature set
```

---

# 276. Unsupported Target

The package remains installable but cannot activate on that target.

---

# 277. WASM

WASM extensions use host-defined module interfaces rather than native dynamic library loading.

---

# 278. Mobile

Mobile restrictions may require statically bundled extensions.

---

# 279. iOS

Dynamic code loading is subject to platform signing and distribution restrictions.

---

# 280. Android

Native module loading is subject to platform packaging/security constraints.

---

# 281. Reproducible Builds

Extension packages should support reproducible build metadata.

---

# 282. Build Fingerprint

Module metadata contains:

```text
source_hash
compiler_version
compiler_build
target
feature_set
```

when reproducibility metadata is enabled.

---

# 283. Debug Symbols

Debug symbols are separate from production extension packages unless explicitly embedded.

---

# 284. Symbol Server

External symbol storage is outside the core runtime.

---

# 285. Binary Size

Static extension code is dead-strippable.

---

# 286. Startup Cost

Lazy activation prevents unused extensions from increasing startup cost.

---

# 287. Runtime Overhead

Normal application execution must not traverse the extension manager for ordinary direct function calls.

---

# 288. Hot Path Rule

Extension dispatch may use:

```text
direct call
function table
cached provider pointer/handle
```

rather than repeated dynamic lookup.

---

# 289. Cache Invalidation

Provider caches invalidate when:

- module unloads;
- provider changes;
- capability changes;
- registry generation changes.

---

# 290. Registry Generation

The registry maintains a monotonic generation number.

---

# 291. Stale Provider

A stale provider handle is rejected through generation validation.

---

# 292. No Use-After-Unload

Generation validation plus quiescence prevents calling unloaded modules.

---

# 293. Concurrency

Registry mutations occur through controlled synchronization.

---

# 294. Read Path

Provider lookup should support low-contention read paths.

---

# 295. Copy-on-Update Registry

A snapshot registry may be used:

```text
readers → immutable snapshot
writer  → new snapshot
```

This minimizes contention.

---

# 296. Extension Transactions

Multiple extension registrations can be committed atomically.

---

# 297. Registration Rollback

If one required registration fails, the transaction rolls back.

---

# 298. Partial Optional Registration

Optional contributions may fail independently.

---

# 299. Determinism

Given the same:

- package set;
- policy;
- lock file;
- target;

the active extension graph must be deterministic.

---

# 300. Extension Graph Fingerprint

Runtime computes:

```text
ExtensionGraphFingerprint
```

from:

- module IDs;
- versions;
- hashes;
- ABI;
- dependency graph;
- policy.

---

# 301. Diagnostics Integration

602 records the extension graph fingerprint.

---

# 302. Crash Correlation

Crash reports identify the active module graph.

---

# 303. State Integration

600 checkpoints may record extension versions and state schemas.

---

# 304. Checkpoint Restore

Extensions are restored only when compatible with the checkpoint.

---

# 305. Incompatible Extension

State remains available for migration or is quarantined.

---

# 306. No Automatic Arbitrary Migration

Migration code must be explicitly registered and bounded.

---

# 307. Migration Sandbox

Migration can run under restricted capabilities.

---

# 308. Migration Failure

Original state remains unchanged.

---

# 309. Resource Limits

Migration is subject to CPU/memory/time limits.

---

# 310. Security Logging

Denied extension operations produce structured security events.

---

# 311. Privacy

Extension telemetry is disabled unless explicitly configured.

---

# 312. Data Ownership

An extension cannot assume ownership of host application data merely because it can read it.

---

# 313. Data Export

Explicit capability and user/application policy are required for export.

---

# 314. Clipboard

Clipboard access follows 619/603 capability policy.

---

# 315. Network

Network access follows 609/603.

---

# 316. Storage

Storage follows 611/603.

---

# 317. Documents

Document access follows 621/application policy.

---

# 318. Workspace

Workspace modification follows 622/620 command authorization.

---

# 319. UI

UI modifications occur through registered extension points.

---

# 320. Extension API Documentation

Every public extension point should expose machine-readable API metadata.

---

# 321. API Fingerprint

API metadata includes a stable interface fingerprint.

---

# 322. Compatibility Check

A module is compatible only if the requested API fingerprint is supported.

---

# 323. Breaking Change

Breaking API changes require a new major interface version.

---

# 324. Experimental APIs

Experimental extension APIs must be explicitly marked.

---

# 325. Stable APIs

Stable APIs have compatibility guarantees defined by the host application.

---

# 326. Deprecation

Deprecated APIs remain available for a declared compatibility period.

---

# 327. Removal

Removed APIs produce deterministic activation errors.

---

# 328. Documentation

Compiler can generate extension API documentation from metadata.

---

# 329. IDE Integration

622/619 can display extension-provided commands and panels.

---

# 330. Extension Discovery UI

Applications may show installed extensions.

The UI itself is not part of the mandatory core runtime.

---

# 331. Extension Enablement

Enable/disable state is persisted in 601 configuration.

---

# 332. Per-Workspace Enablement

Optional extensions can be enabled only for a workspace.

---

# 333. Per-Project Enablement

Project-level manifests may restrict active extensions.

---

# 334. Trust Prompt

Applications may request user confirmation before enabling a new extension.

---

# 335. Trust Decision

Trust decisions are stored as policy/configuration, not hidden application state.

---

# 336. Enterprise Policy

603 can enforce centrally configured extension allow/deny policies.

---

# 337. Blocked Publisher

Publisher identity can be denied by policy.

---

# 338. Allowed Publisher

Publisher allowlists can be configured.

---

# 339. Signature Rotation

610 supports publisher key rotation.

---

# 340. Revocation

Revoked signatures prevent future activation according to policy.

---

# 341. Already Running Extension

Policy defines whether revocation:

```text
Observe
DisableNextStart
QuiesceNow
TerminateProcess
```

is appropriate.

---

# 342. No Forced In-Process Termination

An in-process extension cannot safely be force-killed independently of the host process.

---

# 343. Process Isolation Recommendation

Applications requiring strong runtime isolation use out-of-process extensions.

---

# 344. Extension Process IPC

Process extensions use:

```text
604 IPC
605 supervision
606 resources
603 security
```

---

# 345. Extension Network Services

A networked extension process can expose a 604 service endpoint.

---

# 346. Service Discovery

The host discovers extension services through explicit registration.

---

# 347. Service Failure

Host receives a deterministic service-unavailable error.

---

# 348. Reconnection

607/604 can reconnect when service restart is allowed.

---

# 349. Extension Process Restart

605 may restart the extension without restarting the application.

---

# 350. Extension State After Restart

Persistent state comes from 600/612/611.

---

# 351. Hot Reload Process

Out-of-process extensions can restart with a new version more safely than in-process modules.

---

# 352. Binary Compatibility

A process boundary reduces ABI coupling but does not eliminate schema compatibility requirements.

---

# 353. Schema Versioning

604/612 schemas are versioned independently.

---

# 354. Fuzzing

All extension boundaries require:

- manifest fuzzing;
- ABI input fuzzing;
- schema fuzzing;
- IPC fuzzing;
- malformed package tests.

---

# 355. Fault Injection

Tests simulate:

- missing dependencies;
- invalid signatures;
- module crash;
- unload race;
- task leak;
- callback leak;
- device loss;
- network loss;
- storage failure;
- state migration failure.

---

# 356. Memory Leak Detection

Extension resource registry can report resources remaining at quiescence.

---

# 357. Leak Policy

Debug builds may fail unload on leaks.

Production policy may quarantine the extension instead.

---

# 358. Deterministic Test Host

A test host provides:

```text
fake scheduler
fake storage
fake network
fake UI
fake registry
fake capabilities
fake clock
```

---

# 359. Extension Contract Tests

Every extension point should have reusable contract tests.

---

# 360. Compatibility Test

A module must pass ABI/API compatibility tests before distribution.

---

# 361. Performance Tests

Measure:

- activation;
- provider lookup;
- IPC;
- dispatch;
- unload;
- reload;
- registry updates.

---

# 362. Performance Target

Direct statically linked provider calls should be indistinguishable from ordinary Axiom function calls after optimization.

---

# 363. Dynamic Provider Target

Cached dynamic dispatch should add only bounded dispatch overhead.

---

# 364. Startup Target

Unused extensions should contribute zero runtime initialization cost.

---

# 365. Memory Target

Extension metadata must be compact and unloadable where possible.

---

# 366. Static Build Target

Applications without dynamic extensions must not link:

- dynamic loader;
- package discovery;
- registry;
- hot reload;
- extension IPC.

---

# 367. Minimal Profile

```text
AXIOM_EXTENSION_NONE
```

removes the extension runtime.

---

# 368. Dynamic Profile

```text
AXIOM_EXTENSION_DYNAMIC
```

enables local dynamic modules.

---

# 369. Isolated Profile

```text
AXIOM_EXTENSION_ISOLATED
```

enables process-based extension hosting.

---

# 370. Full Profile

```text
AXIOM_EXTENSION_FULL
```

enables:

- package discovery;
- dynamic loading;
- hot reload;
- workspace integration;
- UI contributions;
- service registry.

---

# 371. Compiler Metadata

Relevant metadata:

```text
@module
@plugin
@extension
@extension_point
@provides
@requires
@capability
@abi
@hot_reload
@state_schema
```

---

# 372. IR Integration

IR may contain:

```text
module_load
module_call
module_handle_acquire
module_handle_release
provider_lookup
provider_call
```

but ordinary direct calls remain ordinary calls.

---

# 373. Linker Integration

Linker resolves:

- static extension registry;
- ABI symbols;
- module fingerprints;
- dead stripping.

---

# 374. Loader Integration

Runtime loader validates all dynamic metadata before executing initialization code.

---

# 375. Package Integration

613 owns:

- package storage;
- content addressing;
- extraction;
- verification;
- installation;
- rollback.

623 owns:

- module activation;
- extension lifecycle;
- extension registration.

---

# 376. Security Integration

603 owns:

- capabilities;
- policy;
- privilege;
- sandbox boundaries.

623 consumes those policies.

---

# 377. Crypto Integration

610 owns:

- signature verification;
- key handling;
- trust primitives.

623 consumes verification results.

---

# 378. Scheduler Integration

607 owns:

- tasks;
- executors;
- cancellation.

623 creates extension-scoped execution contexts.

---

# 379. Resource Integration

606 owns quotas.

623 attaches resource ownership to extension instances.

---

# 380. Diagnostics Integration

602 owns logs/traces/crash reports.

623 contributes extension identity and lifecycle metadata.

---

# 381. Supervision Integration

605 owns process supervision.

623 supplies extension process specifications.

---

# 382. IPC Integration

604 owns transport.

623 defines extension-specific service schemas.

---

# 383. GUI Integration

619 owns GUI primitives.

623 contributes extension UI registrations.

---

# 384. Workspace Integration

622 owns workspace layout.

623 contributes workspace extensions.

---

# 385. Document Integration

621 owns document lifecycle.

623 provides document providers.

---

# 386. Command Integration

620 owns command/undo infrastructure.

623 contributes commands.

---

# 387. Configuration Integration

601 owns configuration.

623 defines extension configuration schemas.

---

# 388. Persistence Integration

600 owns application recovery.

623 defines extension state restoration policy.

---

# 389. Serialization Integration

612 owns schema encoding.

623 defines extension metadata/state schemas.

---

# 390. Architecture Invariants

1. Dynamic plugins are optional.
2. Static modules are first-class.
3. ABI is explicit.
4. Ownership is explicit.
5. Capabilities are explicit.
6. Loading does not grant arbitrary privilege.
7. Dependencies are deterministic.
8. Dependency cycles are rejected.
9. Lifecycle is explicit.
10. Unload requires quiescence.
11. Old code cannot be called after unload.
12. Callback registrations are invalidated.
13. Task ownership is explicit.
14. Persistent state is versioned.
15. Secret state is protected.
16. Workspace state is namespaced.
17. Extension code cannot modify capabilities implicitly.
18. Package installation does not execute code.
19. Signature verification occurs before activation.
20. Static builds can eliminate extension runtime.
21. Out-of-process extensions have independent failure domains.
22. In-process extensions cannot claim independent crash isolation.
23. Provider precedence is explicit.
24. Registry mutations are transactional.
25. Async operations are cancellable.
26. Stale completions cannot mutate newer state.
27. Extension APIs are versioned.
28. Unknown optional APIs are tolerated.
29. Breaking API changes require new interface versions.
30. Persisted state cannot contain executable code.
31. Workspace restoration cannot grant capabilities.
32. Module resources are tracked.
33. Leaked resources are diagnosable.
34. Hot reload is opt-in.
35. Unsupported hot reload is explicit.
36. Failed activation does not corrupt the host.
37. Failed updates retain rollback information.
38. Extension graph is deterministic.
39. Extension graph has a fingerprint.
40. No mandatory plugin VM exists.
41. No mandatory GC exists.
42. No mandatory scripting engine exists.
43. No mandatory marketplace exists.
44. No mandatory network registry exists.
45. No global mutable extension registry exists.
46. Headless applications can omit GUI extension features.
47. WASM/mobile constraints are represented explicitly.
48. Native handles are never persisted as authoritative state.
49. Extension boundaries are fuzz-testable.
50. Extension runtime is dead-strippable.

---

# 391. Acceptance Criteria

### Module System
1. Static module.
2. Dynamic module.
3. Module identity.
4. Publisher identity.
5. Version.
6. ABI identity.
7. Module descriptor.
8. Stable entry point.
9. Lifecycle.
10. Failure states.

### ABI
11. Stable primitive ABI.
12. Stable structs.
13. Opaque handles.
14. Ownership rules.
15. Error boundary.
16. Panic boundary.
17. API negotiation.
18. API versioning.
19. ABI fingerprint.
20. Symbol control.

### Discovery
21. Package discovery.
22. Deterministic search.
23. Path validation.
24. Package manifest.
25. Lock file.
26. Hash verification.
27. Signature verification.
28. Target filtering.
29. Architecture filtering.
30. ABI filtering.

### Dependencies
31. Dependency graph.
32. Required dependency.
33. Optional dependency.
34. Feature dependency.
35. Cycle detection.
36. Initialization ordering.
37. Shutdown ordering.
38. Version constraints.
39. Side-by-side policy.
40. Graph fingerprint.

### Lifecycle
41. Load.
42. Initialize.
43. Start.
44. Quiesce.
45. Stop.
46. Unload.
47. Resource tracking.
48. Task cancellation.
49. callback cleanup.
50. leak detection.

### Capabilities
51. Capability declaration.
52. Capability grant.
53. Capability attenuation.
54. Capability revocation.
55. Filesystem.
56. Network.
57. Process.
58. Device.
59. GUI.
60. GPU.

### UI
61. Commands.
62. Panels.
63. Views.
64. Menus.
65. Toolbars.
66. Documents.
67. Routes.
68. Workspace contributions.
69. UI cleanup.
70. missing-provider placeholders.

### Hot Reload
71. hot load.
72. hot unload.
73. hot reload.
74. quiescence.
75. state transfer.
76. state migration.
77. rollback.
78. stale callback prevention.
79. task drain.
80. unsupported-module declaration.

### Process Isolation
81. out-of-process host.
82. IPC contract.
83. supervision.
84. restart.
85. resource limits.
86. capability isolation.
87. crash containment.
88. state restoration.
89. service discovery.
90. reconnect.

### State
91. configuration.
92. persistent state.
93. session state.
94. ephemeral state.
95. state version.
96. migration.
97. secret protection.
98. namespace isolation.
99. checkpoint compatibility.
100. recovery.

### Updates
101. package update.
102. verification.
103. atomic activation.
104. rollback.
105. version pinning.
106. dependency update.
107. shared dependency handling.
108. offline update.
109. quarantine.
110. revocation.

### Performance
111. lazy activation.
112. static dead stripping.
113. cached provider lookup.
114. low-contention registry.
115. snapshot registry.
116. bounded dispatch overhead.
117. zero-copy boundary.
118. resource accounting.
119. startup minimization.
120. compact metadata.

### Diagnostics
121. lifecycle logs.
122. module identity.
123. dependency diagnostics.
124. capability diagnostics.
125. crash correlation.
126. performance metrics.
127. reload diagnostics.
128. leak diagnostics.
129. quarantine diagnostics.
130. graph fingerprint.

### Testing
131. ABI tests.
132. package tests.
133. dependency tests.
134. lifecycle tests.
135. unload race tests.
136. hot reload tests.
137. state migration tests.
138. capability tests.
139. IPC fuzzing.
140. manifest fuzzing.
141. parser fuzzing.
142. crash injection.
143. resource exhaustion tests.
144. deterministic registry tests.
145. contract tests.

### Cross-Platform
146. Windows.
147. Linux.
148. macOS.
149. Android.
150. iOS.
151. WASM.
152. embedded.
153. static-only builds.
154. dynamic desktop builds.
155. isolated process builds.

---

# 392. Final Architecture

```text
                         AXIOM APPLICATION
                                │
                                ▼
                       EXTENSION MANAGER
                                │
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
        STATIC MODULES     DYNAMIC MODULES    ISOLATED MODULES
             │                  │                  │
             │             Native Loader           │
             │                  │                 IPC
             │                  ▼                  │
             │             Module Registry         ▼
             │                  │            Extension Process
             └──────────────────┼──────────────────┘
                                ▼
                       EXTENSION CONTEXT
                                │
       ┌──────────────┬─────────┼─────────┬──────────────┐
       ▼              ▼         ▼         ▼              ▼
     Commands       GUI      Documents   Services     Resources
       │              │         │         │              │
       ▼              ▼         ▼         ▼              ▼
      620            619       621       604           613
                                │
                                ▼
                         SECURITY / POLICY
                               603
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
               610            606            605
              Crypto        Resources      Supervision
```

---

# 393. Result

BOOTSTRAP-623 establishes an extension architecture where Axiom applications can grow from:

```text
single native executable
```

to:

```text
large modular desktop application
```

without forcing the language core to contain:

- a VM;
- garbage collector;
- scripting runtime;
- mandatory plugin framework;
- mandatory package registry;
- mandatory dynamic loader.

The architecture preserves a clean distinction between:

```text
language module
application extension
runtime service
package
process
capability
```

while providing a complete path from static linking to dynamically loaded and isolated extensions.

---

# 394. Task Completion

**BOOTSTRAP-623 — COMPLETE**

**Next queued task: BOOTSTRAP-624 — Native Application Scripting, Embedded Language Boundary, Automation, Macro, Expression Runtime & Sandboxed Dynamic Behavior 5.0**
:::