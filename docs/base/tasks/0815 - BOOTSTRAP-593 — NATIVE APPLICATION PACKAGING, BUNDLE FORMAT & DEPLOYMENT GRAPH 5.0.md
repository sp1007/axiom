# BOOTSTRAP-593 — NATIVE APPLICATION PACKAGING, BUNDLE FORMAT & DEPLOYMENT GRAPH 5.0
## APP BUNDLE, RESOURCES, NATIVE LIBRARIES, RUNTIME DEPENDENCIES, PLATFORM PACKAGING, APPLICATION MANIFEST, SIGNING BOUNDARY, SANDBOX/CAPABILITY DECLARATION, PORTABLE DEPLOYMENT & REPRODUCIBLE APPLICATION PACKAGE

**Trạng thái: COMPLETED / LOCKED**

`593` định nghĩa lớp nằm sau `584/589/590/591/592`: biến native executable + libraries + resources + runtime dependencies thành **một application deployment artifact hoàn chỉnh**.

Nguyên tắc lớn:

> Axiom compiler tạo code. Linker tạo native image. Package system tạo package. Deployment system tạo application bundle/installable artifact.

Không trộn bốn lớp này thành một.

---

# 593.1. Deployment architecture

```text
                    Axiom Project
                         │
                         ▼
                 Package Graph 591
                         │
                         ▼
                 Build Graph 592
                         │
                         ▼
                 Native Artifacts
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Executable      Libraries       Resources
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                Deployment Graph
                         │
                         ▼
                Application Bundle
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Windows         Linux          Apple
       Package        Package         Bundle
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                 Signing Boundary
                         │
                         ▼
                Distribution Artifact
```

---

# 593.2. Deployment artifact

Deployment artifact là immutable representation của application có thể được:

- cài đặt;
- chạy;
- phân phối;
- archive;
- verify;
- sign.

---

# 593.3. Không đồng nhất executable với application

```text
program.exe
```

chỉ là executable.

Application có thể gồm:

```text
executable
shared libraries
resources
fonts
configuration
localization
plugins
runtime files
metadata
```

---

# 593.4. Deployment graph

```text
DeploymentGraph {
    application
    executables[]
    libraries[]
    resources[]
    runtimes[]
    permissions[]
    platform_requirements[]
    installation_rules[]
}
```

---

# 593.5. Graph identity

Deployment graph có canonical identity:

```text
DeploymentGraphID =
Hash(canonical(DeploymentGraph))
```

---

# 593.6. Application identity

```text
ApplicationID {
    namespace
    name
    variant
}
```

Ví dụ:

```text
com.example.editor
```

---

# 593.7. Application version

Application version độc lập với Axiom language version.

---

# 593.8. Package version

Deployment package có:

```text
major
minor
patch
build metadata
```

---

# 593.9. Application manifest

Mỗi deployable application phải có manifest.

```text
ApplicationManifest {
    id
    version
    display_name
    publisher
    entrypoints[]
    targets[]
    dependencies[]
    resources[]
    permissions[]
    capabilities[]
}
```

---

# 593.10. Manifest không chứa secret

Private signing key, credential hoặc token không được nằm trong application manifest.

---

# 593.11. Entry point

Application có thể có:

```text
main executable
GUI entry
service entry
worker entry
WASM entry
```

---

# 593.12. Multiple executable applications

Một package có thể chứa nhiều executable nếu manifest phân biệt rõ từng entrypoint.

---

# 593.13. Library dependency

Library dependency phải được biểu diễn bằng identity, không chỉ filename.

```text
LibraryDependency {
    id
    ABI
    version
    target
    artifact_hash
}
```

---

# 593.14. Dynamic library

Dynamic library:

```text
Windows → DLL
Linux → SO
Apple → DYLIB/framework
```

---

# 593.15. Static library

Static library có thể được đóng gói nhưng thường được link vào executable trước deployment.

---

# 593.16. Static linking preference

Application có thể chọn:

```text static
dynamic
hybrid
```

theo target/policy.

---

# 593.17. Runtime dependency

Runtime component được coi là dependency nếu executable không self-contained.

---

# 593.18. Self-contained application

Application có thể bundle runtime components cần thiết.

---

# 593.19. System runtime

Application có thể depend on OS-provided runtime.

Manifest phải khai báo requirement.

---

# 593.20. Runtime compatibility

Runtime dependency phải kiểm tra:

```text version
ABI
architecture
platform
feature set
```

---

# 593.21. Deployment target

Target descriptor từ `588` được reuse.

```text windows-x64
linux-x64
linux-arm64
macos-x64
macos-arm64
ios-arm64
android-arm64
wasm32
```

---

# 593.22. Platform variant

Một application có thể có nhiều platform variants.

```text
App
 ├── Windows
 ├── Linux
 ├── macOS
 ├── iOS
 ├── Android
 └── WASM
```

---

# 593.23. Variant identity

Mỗi variant có identity riêng.

---

# 593.24. Universal application

Nếu platform cho phép, package có thể chứa nhiều architecture.

---

# 593.25. Universal binary

Universal binary phải ghi rõ architecture slices.

---

# 593.26. Architecture slice

```text
Slice {
    architecture
    cpu_features
    executable
    libraries
}
```

---

# 593.27. Resource model

Resource có:

```text
path
type
content_hash
compression
permissions
```

---

# 593.28. Resource namespace

Resource paths nằm trong logical package namespace.

---

# 593.29. No arbitrary host paths

Package không được reference absolute developer filesystem paths.

---

# 593.30. Resource lookup

Runtime API:

```text
resource.open("images/logo.png")
```

phải resolve trong application resource namespace.

---

# 593.31. Resource identity

Resource identity dựa trên content hash.

---

# 593.32. Resource deduplication

Các package resources cùng content có thể share CAS object.

---

# 593.33. Compression

Compression là packaging optimization, không ảnh hưởng logical content identity.

---

# 593.34. Resource streaming

Large resources phải hỗ trợ streaming.

---

# 593.35. Memory mapping

Read-only resources có thể memory-map nếu platform cho phép.

---

# 593.36. Writable resources

Application resources immutable.

Data cần thay đổi phải nằm ngoài application bundle.

---

# 593.37. User data

Không lưu user-generated mutable data bên trong immutable application package.

---

# 593.38. Configuration separation

```text Application Bundle
        │
        ├── immutable code
        ├── immutable resources
        │
        └── external configuration/data
```

---

# 593.39. Application data directory

Runtime phải cung cấp platform-neutral API:

```text app.data_dir()
app.cache_dir()
app.config_dir()
```

---

# 593.40. Platform adapter

Platform adapter ánh xạ các logical directories sang OS-specific locations.

---

# 593.41. Installation graph

Installation là graph operation:

```text
Package
 ↓
Files
 ↓
Directories
 ↓
Permissions
 ↓
Registrations
 ↓
Shortcuts/services/etc.
```

---

# 593.42. Installation manifest

Manifest khai báo installation actions.

---

# 593.43. Declarative installation

Ưu tiên declarative package description.

---

# 593.44. Arbitrary install scripts

Không được chạy arbitrary native code trong installer mặc định.

---

# 593.45. Install hooks

Nếu target bắt buộc custom installation logic:

```text capability = install_hook
```

phải được khai báo.

---

# 593.46. Install sandbox

Install hook phải chạy với capability tối thiểu.

---

# 593.47. Installer privileges

Package không được tự động yêu cầu administrator/root.

---

# 593.48. Elevated installation

Nếu cần privilege:

```text manifest → declared requirement
```

và platform UI quyết định authorization.

---

# 593.49. Installation transaction

```text
prepare
 ↓
verify
 ↓
stage
 ↓
commit
```

---

# 593.50. Atomic installation

Nếu commit thất bại, system phải rollback tới trạng thái trước installation nếu platform cho phép.

---

# 593.51. Staging directory

Installation trước tiên vào staging location.

---

# 593.52. Final activation

Sau khi verification hoàn tất mới activate package.

---

# 593.53. Upgrade

Upgrade cũng là transaction:

```text old
 ↓
stage new
 ↓
verify
 ↓
switch
 ↓
cleanup old
```

---

# 593.54. Rollback

Nếu new version không thể activate:

```text new → inactive
old → active
```

---

# 593.55. Side-by-side installation

Nhiều versions có thể tồn tại nếu platform/policy cho phép.

---

# 593.56. Version activation

Active version được xác định bằng installation metadata.

---

# 593.57. Uninstall

Uninstall phải biết chính xác files/registrations thuộc package.

---

# 593.58. Ownership tracking

Installer lưu:

```text file → package identity
```

---

# 593.59. Shared files

Shared system resources không được xóa nếu package khác còn reference.

---

# 593.60. Dependency reference count

Package dependency graph quản lý references logic.

---

# 593.61. Application package format

Axiom định nghĩa logical format:

```text
AXPK
```

Tên này là placeholder cho package container format v5.

---

# 593.62. AXPK container

```text
AXPK
 ├── Header
 ├── Manifest
 ├── Dependency Table
 ├── Artifact Table
 ├── Resource Table
 ├── Signature Metadata
 ├── Provenance
 └── Content Objects
```

---

# 593.63. Container magic

Package bắt đầu bằng fixed magic/version fields để nhận diện.

---

# 593.64. Header

```text
AXPKHeader {
    magic
    format_version
    flags
    manifest_offset
    manifest_size
}
```

---

# 593.65. Canonical manifest

Manifest encoding phải deterministic.

---

# 593.66. Package content

Large package contents có thể nằm trong chunked CAS structure.

---

# 593.67. Package index

Package chứa index:

```text
logical path → content digest
```

---

# 593.68. Zero-copy extraction

Runtime/installers có thể access immutable content directly nếu platform hỗ trợ.

---

# 593.69. Package verification

Verification pipeline:

```text
parse
 ↓
schema validation
 ↓
content hash verification
 ↓
dependency verification
 ↓
target validation
 ↓
signature verification
 ↓
provenance validation
```

---

# 593.70. Invalid package

Package không qua verification không được install.

---

# 593.71. Signature boundary

Signing nằm **sau package construction**.

```text
Build
 ↓
Package
 ↓
Canonicalize
 ↓
Hash
 ↓
Sign
```

---

# 593.72. Signature does not alter logical identity

Signature metadata được tách khỏi unsigned content identity.

---

# 593.73. Publisher identity

Package có publisher identity.

---

# 593.74. Trust policy

Trust policy xác định publisher nào được phép.

---

# 593.75. Revocation

Publisher/package signing identity có thể revoked.

---

# 593.76. Revoked package

Không được install nếu policy cấm revoked artifact.

---

# 593.77. Signature rotation

Publisher có thể rotate signing key mà không thay đổi package logical identity nếu signature envelope hỗ trợ.

---

# 593.78. Multiple signatures

Package có thể có nhiều signatures:

```text publisher
builder
distributor
```

---

# 593.79. Signature threshold

Enterprise/release policy có thể yêu cầu nhiều independent signatures.

---

# 593.80. Signature does not prove source quality

Signature chỉ xác nhận signing authority theo policy.

---

# 593.81. Provenance

Package provenance:

```text source revision
dependency graph
build manifest
compiler
toolchain
target
artifact hashes
```

---

# 593.82. Provenance chain

```text Source
 ↓
Package
 ↓
Build Action
 ↓
Compiler
 ↓
Toolchain
 ↓
Artifact
 ↓
Application Package
```

---

# 593.83. Source package provenance

Nếu source package được distributed, source hash phải được recorded.

---

# 593.84. Binary package provenance

Binary artifact phải reference source/build identity nếu publisher cung cấp.

---

# 593.85. Binary/source relationship

Package có thể chứa:

```text source_hash
binary_hash
build_manifest_id
```

---

# 593.86. Rebuild verification

Third party có thể rebuild source package và compare artifact identity nếu build reproducible.

---

# 593.87. Deployment reproducibility

Packaging cũng phải deterministic.

Cùng deployment graph + inputs:

```text same package content identity
```

---

# 593.88. Package timestamp

Build timestamp không được ảnh hưởng canonical package identity trong reproducible mode.

---

# 593.89. File ordering

Package entries phải canonical order.

---

# 593.90. Compression determinism

Compression phải dùng deterministic settings trong reproducible profile.

---

# 593.91. Platform package wrappers

AXPK là logical package.

Platform-specific wrapper có thể bao ngoài:

```text AXPK
 ↓
MSIX / installer
DMG / PKG
APK
IPA
Linux package
WASM distribution
```

---

# 593.92. Windows package

Windows deployment có thể produce:

```text EXE
DLL
resources
installer package
```

---

# 593.93. PE resources

Windows-specific native resources được tạo ở image/package boundary.

---

# 593.94. Linux package

Linux có thể produce:

```text ELF
shared objects
resources
launcher
distribution package
```

Axiom không bắt buộc một Linux distribution packaging format duy nhất.

---

# 593.95. macOS bundle

Application bundle:

```text
App.app/
    Contents/
        MacOS/
        Resources/
        Frameworks/
        Info.plist
```

Logical structure được abstract hóa trong deployment model.

---

# 593.96. iOS bundle

iOS application phải tạo platform-required bundle metadata và signing boundary.

---

# 593.97. Android package

Android package cần:

```text manifest
resources
native libraries
application code
```

theo platform requirements.

---

# 593.98. WASM package

WASM deployment có thể chứa:

```text wasm module
runtime metadata
assets
JavaScript/browser adapter nếu cần
```

---

# 593.99. Platform-specific metadata

Metadata platform-specific nằm trong adapter layer, không làm ô nhiễm core deployment graph.

---

# 593.100. Platform adapter interface

```text
PlatformPackager {
    validate(graph)
    layout(graph)
    emit(graph)
    verify(package)
}
```

---

# 593.101. Windows adapter

```text WindowsPackager
```

---

# 593.102. Linux adapter

```text LinuxPackager
```

---

# 593.103. Apple adapter

```text ApplePackager
```

---

# 593.104. Android adapter

```text AndroidPackager
```

---

# 593.105. WASM adapter

```text WasmPackager
```

---

# 593.106. Platform independence

Core deployment graph không được chứa:

```text Windows registry key
macOS plist syntax
Android XML
```

làm semantic primitives.

---

# 593.107. Extension metadata

Platform adapter có extension namespace:

```text platform.windows.*
platform.apple.*
platform.android.*
platform.wasm.*
```

---

# 593.108. Capability model

Application khai báo capabilities:

```text filesystem
network
camera
microphone
GPU
bluetooth
location
notifications
```

---

# 593.109. Capability declaration

Capability phải được khai báo trước deployment nếu platform hỗ trợ permission model.

---

# 593.110. Capability ≠ permission grant

Manifest chỉ yêu cầu capability.

OS/user quyết định grant.

---

# 593.111. Capability minimization

Application không được tự động nhận toàn bộ host privileges.

---

# 593.112. Runtime capability query

Runtime:

```text capability.available(...)
capability.granted(...)
```

---

# 593.113. Permission denial

Application phải xử lý permission denied bằng Result/error semantics.

---

# 593.114. Capability inheritance

Child process không mặc định thừa hưởng tất cả capabilities.

---

# 593.115. Process capability set

Mỗi process có capability set riêng.

---

# 593.116. Plugin capability

Plugin được cấp subset capability của host.

---

# 593.117. Plugin trust

Plugin không tự động trở thành trusted code chỉ vì nằm trong application package.

---

# 593.118. Plugin isolation

Plugin có thể chạy:

```text same-process
sandbox-process
```

tùy policy.

---

# 593.119. Native plugin ABI

Plugin API phải sử dụng stable ABI boundary.

---

# 593.120. Plugin package

Plugin package có identity/version/ABI/target.

---

# 593.121. Plugin loading

Dynamic loading phải validate:

```text ABI
architecture
signature
trust
capabilities
```

---

# 593.122. Runtime dependency resolver

Application runtime có thể resolve bundled/system libraries.

---

# 593.123. Library search order

Search order phải deterministic.

Ví dụ:

```text application-private
application-bundle
declared runtime
system
```

Target adapter định nghĩa exact policy.

---

# 593.124. No accidental library injection

Application không được tự động load arbitrary library từ current working directory nếu security policy cấm.

---

# 593.125. DLL/SO hijacking defense

Platform adapter phải có safe library loading policy.

---

# 593.126. Library ABI fingerprint

```text ABIFingerprint
```

được generated bởi compiler/toolchain.

---

# 593.127. ABI mismatch

ABI mismatch là deployment error, không phải runtime warning.

---

# 593.128. Runtime architecture mismatch

x64 executable + ARM64 library phải bị reject trước launch.

---

# 593.129. Dependency closure

Application deployment package phải xác định complete dependency closure hoặc explicit system dependencies.

---

# 593.130. Missing dependency

Missing required dependency phải được detect trong verification/install stage.

---

# 593.131. Optional dependency

Manifest có thể đánh dấu:

```text optional
```

---

# 593.132. Feature dependency

Dependency có thể conditional theo feature.

---

# 593.133. Resource localization

Resources có thể:

```text locale
fallback
region
```

---

# 593.134. Locale resolution

```text exact locale
 ↓
language-region fallback
 ↓
language fallback
 ↓
default
```

---

# 593.135. No duplicate localization logic

Text engine `464` cung cấp Unicode/localization semantics; deployment chỉ package resources.

---

# 593.136. Font packaging

Application có thể bundle fonts.

---

# 593.137. Font licensing metadata

Font resource có thể có license/provenance metadata.

---

# 593.138. Resource license

Package metadata phải hỗ trợ license records cho distributed resources.

---

# 593.139. Third-party notices

Application package có thể chứa machine-readable:

```text licenses/
NOTICE
```

---

# 593.140. License does not affect execution semantics

Legal metadata không được ảnh hưởng executable identity.

---

# 593.141. Package SBOM

Deployment package có thể contain machine-readable dependency inventory.

---

# 593.142. SBOM identity

SBOM references exact package/artifact identities.

---

# 593.143. Vulnerability metadata

Package tooling có extension point để associate security advisories.

---

# 593.144. Advisory does not mutate package

Security advisory chỉ là external/policy metadata.

---

# 593.145. Offline verification

Package có thể verify hoàn toàn offline nếu trust roots/metadata đã local.

---

# 593.146. Online verification

Online revocation/update checks là optional policy.

---

# 593.147. Networkless install

Local package phải install được offline nếu dependencies và trust metadata đầy đủ.

---

# 593.148. Package cache

Deployment package có thể lưu trong CAS.

---

# 593.149. Deduplication

Executable/resource/library giống nhau có thể share CAS objects.

---

# 593.150. Package layering

Application variants có thể share base layer:

```text Base Runtime
      │
      ├── Windows
      ├── Linux
      └── macOS
```

---

# 593.151. Layer identity

Mỗi layer có content identity.

---

# 593.152. Delta updates

Updater có thể truyền only changed content blocks.

---

# 593.153. Delta correctness

Delta phải reconstruct exact target package identity.

---

# 593.154. Update manifest

Update package chứa:

```text old_identity
new_identity
delta_objects
```

---

# 593.155. Atomic update

Apply delta vào staging trước.

---

# 593.156. Failed update

Nếu verification thất bại:

```text old application remains active
```

---

# 593.157. Crash-safe update

Update state machine:

```text
Idle
Preparing
Staged
Verified
Activated
Committed
Rollback
```

---

# 593.158. Update marker

Installer lưu durable marker để recover sau power loss.

---

# 593.159. Application launcher

Launcher phải verify package activation state.

---

# 593.160. Startup validation

Application runtime có thể verify critical libraries/resources trước startup.

---

# 593.161. Fast startup

Không cần rehash toàn bộ package mỗi lần launch nếu immutable verified installation state đã tồn tại.

---

# 593.162. Verification cache

Verification state có thể cache theo content hash.

---

# 593.163. Verification invalidation

Nếu package bytes thay đổi:

```text verification cache invalidated
```

---

# 593.164. Mutable installation detection

Installed application immutable files nên được monitored hoặc verified theo platform policy.

---

# 593.165. Self-update

Application không được tự sửa executable đang chạy nếu platform không cho phép.

---

# 593.166. External updater

Khuyến nghị updater process riêng.

---

# 593.167. Updater trust

Updater là privileged component và phải có trust metadata riêng.

---

# 593.168. Rollback retention

Updater có thể giữ previous version.

---

# 593.169. Garbage collection

Old versions chỉ được xóa khi không còn active/reference.

---

# 593.170. Service application

Axiom application manifest có thể khai báo service.

---

# 593.171. Service lifecycle

```text install
start
stop
restart
upgrade
remove
```

được platform adapter mapping.

---

# 593.172. Service privileges

Service phải khai báo required capabilities.

---

# 593.173. Daemon/service identity

Service identity không đồng nhất với application process identity.

---

# 593.174. Background task

Application có thể khai báo background execution requirement.

---

# 593.175. Platform restrictions

Platform adapter phải validate whether requested capability is supported.

---

# 593.176. Unsupported capability

Deployment phải fail clearly nếu capability bắt buộc không tồn tại trên target.

---

# 593.177. Optional capability

Nếu optional:

```text capability unavailable → application still installable
```

---

# 593.178. Deployment validation report

```text
axiom package verify
```

trả về:

```text manifest
dependency closure
ABI
target
capabilities
signatures
provenance
reproducibility
```

---

# 593.179. Package inspection

```text
axiom package inspect app.axpk
```

---

# 593.180. Package contents

```text
axiom package contents app.axpk
```

---

# 593.181. Package graph

```text
axiom package graph
```

---

# 593.182. Package build

```text
axiom package build
```

---

# 593.183. Package sign

```text
axiom package sign
```

Signing operation nằm ngoài compiler semantics.

---

# 593.184. Package verify

```text
axiom package verify
```

---

# 593.185. Package install

```text
axiom package install
```

Platform adapter thực hiện installation.

---

# 593.186. Package uninstall

```text
axiom package uninstall
```

---

# 593.187. Package update

```text
axiom package update
```

---

# 593.188. Package rollback

```text
axiom package rollback
```

---

# 593.189. Package export

```text
axiom package export --target ...
```

---

# 593.190. Package inspect AI API

AI semantic tooling có thể query:

```text
ApplicationManifest
DeploymentGraph
DependencyClosure
Artifact
Capability
Signature
Provenance
```

---

# 593.191. AI deployment planning

AI có thể lập deployment plan nhưng không được tự grant privileges/sign package nếu không có authorization.

---

# 593.192. AI package modification

Mọi AI-generated manifest change phải:

```text plan
 ↓
preview
 ↓
validate
 ↓
apply
 ↓
build
 ↓
verify
```

---

# 593.193. No hidden deployment mutation

AI/IDE không được silently install application.

---

# 593.194. User-visible installation

Installation actions phải được user/automation policy explicitly authorize.

---

# 593.195. Deployment audit

Package operation có audit record:

```text action
package
version
identity
operator/automation identity
result
```

---

# 593.196. Privacy

Audit log không được lưu secret payload.

---

# 593.197. Deployment provenance

```text
SourceRevision
 ↓
BuildManifestID
 ↓
ArtifactHash
 ↓
DeploymentGraphID
 ↓
PackageHash
 ↓
Signature
```

---

# 593.198. Release artifact

Release artifact phải reference tất cả identity cần thiết để reproduce/verify deployment.

---

# 593.199. Reproducible package

```text same inputs
same graph
same packaging policy
      ↓
same canonical package
```

---

# 593.200. Package byte identity

Canonical AXPK package có byte-stable representation trong reproducible mode.

---

# 593.201. Native image relationship

```text Package
  └── NativeImageHash
```

Package không được mutate native image.

---

# 593.202. Post-link resources

Resource injection sau linker phải tạo package identity mới, không giả vờ native image hash unchanged nếu executable bytes thay đổi.

---

# 593.203. Embedded resources

Nếu resources được embedded vào executable:

```text resource change → executable artifact changes
```

---

# 593.204. External resources

Nếu resources external:

```text resource change → package changes
native executable unchanged
```

---

# 593.205. Deployment optimization

Tooling có thể chọn embedded/external resources theo target nhưng identity phải phản ánh lựa chọn.

---

# 593.206. Library bundling

Dynamic library có thể:

```text bundled
system-provided
optional
```

---

# 593.207. System library declaration

System library phải reference platform ABI identity.

---

# 593.208. SDK dependency

SDK không nhất thiết phải ship với application.

Application chỉ ship resulting runtime dependency.

---

# 593.209. Static system dependency

Nếu statically linked system library, license/provenance vẫn phải record nếu applicable.

---

# 593.210. Runtime loader compatibility

Package verifier có thể inspect:

```text PE
ELF
Mach-O
WASM
```

để xác nhận dependency declarations.

---

# 593.211. Native image introspection

Verifier có thể compare:

```text declared imports
actual imports
```

---

# 593.212. Dependency mismatch

Declared library nhưng không có import → warning/optimization metadata.

Undeclared import → error.

---

# 593.213. Resource mismatch

Declared resource absent → error.

Unreferenced resource → allowed.

---

# 593.214. Entry point mismatch

Manifest entrypoint phải tồn tại trong artifact.

---

# 593.215. ABI verification

Native dependency graph được check trước installation.

---

# 593.216. Architecture verification

Every native component phải compatible với target architecture.

---

# 593.217. CPU feature verification

Required CPU features phải được manifest/artifact metadata expose.

---

# 593.218. Minimum platform version

Manifest:

```text min_os_version
```

---

# 593.219. Platform compatibility

Package verifier reject target below required OS version nếu requirement mandatory.

---

# 593.220. Runtime capability requirements

Application may declare:

```text required
optional
```

cho từng runtime capability.

---

# 593.221. Capability-aware package selection

Package resolver có thể chọn variant phù hợp target capabilities.

---

# 593.222. Multi-platform package

Một distribution artifact có thể chứa multiple platform packages nhưng mỗi package variant vẫn identity riêng.

---

# 593.223. Universal distribution

Distribution manifest:

```text
Distribution
 ├── Windows package
 ├── Linux package
 ├── macOS package
 ├── Android package
 └── iOS package
```

---

# 593.224. Distribution identity

```text DistributionID =
Hash(all platform package identities + distribution metadata)
```

---

# 593.225. Installer independence

AXPK không phụ thuộc installer framework bên thứ ba.

---

# 593.226. Native installer generation

Axiom tooling có thể generate minimal native installer artifacts.

---

# 593.227. OS package integration

OS-native package formats có thể được generated bởi platform adapter.

---

# 593.228. Third-party package generators

Có thể sử dụng externally nếu user muốn, nhưng không phải compiler dependency.

---

# 593.229. No third-party compiler dependency

593 không được đưa LLVM/GCC/Clang/MSVC vào packaging pipeline.

---

# 593.230. No mandatory third-party runtime

Application bundle phải có khả năng self-contained theo target policy.

---

# 593.231. Runtime boundary

Nếu Axiom runtime cần OS APIs:

```text Axiom Runtime
      ↓
Platform Adapter
      ↓
OS
```

---

# 593.232. WASM runtime

WASM host/runtime nằm ngoài WASM module semantics.

---

# 593.233. Browser deployment

Browser-specific JS glue là adapter/package layer, không phải Axiom core.

---

# 593.234. Native mobile deployment

iOS/Android signing và store-specific submission nằm ngoài core compiler.

---

# 593.235. External signing tools

Platform-specific signing tool có thể nằm ở final deployment boundary.

Điều này giữ invariant của `588`:

> Compiler/linker không phụ thuộc signing infrastructure bên ngoài để tạo native code.

---

# 593.236. Signing service

Enterprise deployment có thể dùng remote signing service.

---

# 593.237. Signing service isolation

Private key không được đưa vào generic build worker.

---

# 593.238. Secure release pipeline

```text Build
 ↓
Verify
 ↓
Package
 ↓
Verify
 ↓
Sign
 ↓
Verify signature
 ↓
Publish
```

---

# 593.239. Publication

Publishing package sang registry/distribution service là operation riêng.

---

# 593.240. Registry relationship

`591` lưu package identities.

`593` tạo application distribution artifacts.

---

# 593.241. Build relationship

`592` tạo binary/resource artifacts.

---

# 593.242. Package relationship

`593` combine artifacts thành deployable graph.

---

# 593.243. Debug relationship

Debug artifacts từ `589` có thể được attached separately.

---

# 593.244. Debug package

Distribution có thể publish:

```text application package
debug symbol package
source package
```

riêng biệt.

---

# 593.245. Debug symbol privacy

Production package không bắt buộc ship private source/debug symbols.

---

# 593.246. Crash symbol lookup

Symbol server có thể resolve artifact hash → debug artifact.

---

# 593.247. Application crash provenance

Crash report có thể reference:

```text application version
binary hash
deployment package hash
```

---

# 593.248. Update compatibility

Updater phải verify old/new application identities trước delta application.

---

# 593.249. Downgrade

Downgrade được phép nếu policy cho phép và package trust hợp lệ.

---

# 593.250. Migration scripts

Database/data migration là separate deployment capability, không được coi là ordinary file installation.

---

# 593.251. Migration transaction

Nếu migration cần thiết cho upgrade:

```text preflight
backup
migration
activate
```

---

# 593.252. Migration failure

Không activate new application nếu mandatory migration failed.

---

# 593.253. Migration rollback

Khả năng rollback data phải explicit; không giả định mọi migration reversible.

---

# 593.254. Configuration migration

Configuration schema migration phải có version identity.

---

# 593.255. Package lifecycle

```text
Created
Verified
Signed
Published
Installed
Activated
Updated
Retired
Revoked
```

---

# 593.256. Revocation

Revoked package không nhất thiết bị physically deleted.

---

# 593.257. Retired package

Retired khác Revoked:

```text Retired → no longer distributed
Revoked → trust/security invalidated
```

---

# 593.258. Application identity stability

App ID không đổi giữa patch/minor updates trừ khi intentionally create a new application.

---

# 593.259. Publisher identity

Publisher identity không được suy ra từ package name.

---

# 593.260. Namespace ownership

Registry `591` quản lý namespace ownership.

---

# 593.261. Package collision

Hai publisher không được publish cùng globally scoped application identity nếu registry policy cấm.

---

# 593.262. Local applications

Local/private apps có private namespace.

---

# 593.263. Enterprise namespace

Enterprise deployments có thể dùng organization-owned namespace.

---

# 593.264. Development package

Development build có thể có ephemeral application identity.

---

# 593.265. Release package

Release application identity phải stable.

---

# 593.266. Package channels

Distribution có thể có:

```text stable
beta
nightly
```

Channels là metadata, không thay đổi application identity.

---

# 593.267. Channel security

Channel metadata không override signature/trust policy.

---

# 593.268. Update selection

Updater chỉ chọn version thỏa:

```text application identity
target
compatibility
trust policy
channel policy
```

---

# 593.269. Automatic update

Automatic update là optional deployment service.

---

# 593.270. Update policy

User/admin có thể configure:

```text manual
notify
automatic
disabled
```

---

# 593.271. No forced update in core

Language/runtime không tự ép application update.

---

# 593.272. Portable application

Axiom có thể tạo portable bundle:

```text app/
    executable
    libraries
    resources
    manifest
```

không cần installer.

---

# 593.273. Portable verification

Portable bundle vẫn phải verify dependencies.

---

# 593.274. AppImage-like model

Linux adapter có thể tạo self-contained portable image.

Không biến một format cụ thể thành language primitive.

---

# 593.275. Windows portable

Windows có thể tạo directory bundle/portable executable.

---

# 593.276. macOS portable

macOS `.app` bundle là primary logical application representation.

---

# 593.277. Mobile portability

Mobile targets chịu platform signing/install restrictions.

---

# 593.278. WASM portability

WASM package có thể target browser/server/WASI environments.

---

# 593.279. WASM capability declaration

WASM package phải declare host imports/capabilities.

---

# 593.280. Host import verification

Undeclared WASM imports phải fail validation.

---

# 593.281. Native import verification

Tương tự với ELF/PE/Mach-O imports.

---

# 593.282. Package inspection API

Core:

```text
PackageReader
PackageVerifier
PackageBuilder
DeploymentPlanner
PlatformPackager
Installer
Updater
```

---

# 593.283. PackageBuilder

Input:

```text DeploymentGraph
```

Output:

```text canonical package
```

---

# 593.284. DeploymentPlanner

Resolve:

```text artifact
library
resource
runtime
platform
capability
```

---

# 593.285. PlatformPackager

Chuyển logical deployment graph thành target-native representation.

---

# 593.286. PackageVerifier

Không install nếu graph không hợp lệ.

---

# 593.287. Installer

Thực thi installation transaction.

---

# 593.288. Updater

Thực thi version transition.

---

# 593.289. Uninstaller

Xóa owned resources và registrations theo manifest.

---

# 593.290. Package cache

Package artifact có thể được CAS-store từ `592`.

---

# 593.291. Deployment cache

Packaging action cũng là build action:

```text DeploymentGraph
+
Artifacts
+
PackagingToolchain
→
Package
```

---

# 593.292. Package action identity

```text PackageActionID =
Hash(
    DeploymentGraphID
    artifact identities
    packaging policy
    platform adapter
)
```

---

# 593.293. Zero-repackage

Nếu deployment inputs không đổi:

> không rebuild package.

---

# 593.294. Platform packager identity

Platform adapter version phải nằm trong package action identity.

---

# 593.295. Installer identity

Nếu installer format changes:

```text package identity changes
```

---

# 593.296. Resource-only package update

Nếu resource external:

```text resource change
→ package action reruns
→ executable action remains cached
```

---

# 593.297. Binary-only update

Nếu executable changes:

```text executable action
→ package action
```

resource actions không cần rebuild.

---

# 593.298. Dependency-only update

Nếu library changes:

```text library build
→ deployment package
```

---

# 593.299. Package graph explanation

Tooling phải trả lời:

```text Why is this file in my application?
```

---

# 593.300. Dependency explanation

```text app
 ↓
library A
 ↓
runtime B
```

phải inspect được.

---

# 593.301. AI deployment query

AI có thể hỏi:

```text why included?
why missing?
which package owns this file?
which dependency provides this library?
```

---

# 593.302. No hidden package contents

Mọi shipped executable/library/resource phải có manifest entry hoặc explicit platform-generated metadata.

---

# 593.303. Generated platform files

Platform adapter-generated files phải có provenance:

```text generated_by
generator_version
input_identity
```

---

# 593.304. Generated installer

Installer output phải reference source deployment graph.

---

# 593.305. Reproducible installer

Nếu installer format hỗ trợ deterministic construction, output phải deterministic.

---

# 593.306. Platform-generated nondeterminism

Nếu OS package format bắt buộc nondeterministic fields:

- normalize khi có thể;
- canonical semantic package identity vẫn phải stable.

---

# 593.307. Deployment validation

Trước publish:

```text dependency closure
ABI
target
resource closure
capabilities
signature
provenance
```

phải được validate.

---

# 593.308. Publish validation

Registry `591` chỉ nhận package thỏa package schema/trust policy.

---

# 593.309. Distribution manifest

Distribution artifact có:

```text DistributionManifest {
    application
    versions[]
    platform_variants[]
    signatures[]
}
```

---

# 593.310. CDN compatibility

Distribution layer có thể dùng CDN/object storage.

Axiom logical package không phụ thuộc CDN.

---

# 593.311. Download integrity

Downloaded package được verify bằng content hash/signature trước install.

---

# 593.312. Partial download

Partial package không được coi là installable.

---

# 593.313. Resumable package download

Package download phải hỗ trợ resume nếu transport cho phép.

---

# 593.314. Delta distribution

Update có thể sử dụng content-addressed delta objects.

---

# 593.315. Delta verification

Final reconstructed package phải match expected identity.

---

# 593.316. Package mirror

Mirror có thể serve package theo content identity.

---

# 593.317. Mirror trust

Mirror không được trở thành trust root.

---

# 593.318. Registry trust

Publisher trust vẫn được kiểm tra independent of mirror.

---

# 593.319. Offline mirror

`591` offline registry có thể cung cấp packages cho `593`.

---

# 593.320. Air-gapped deployment

Có thể export:

```text application
dependencies
signatures
trust roots
provenance
```

thành một deployment bundle.

---

# 593.321. Air-gap verification

Target machine không cần Internet để verify nếu trust roots/metadata đã bundled.

---

# 593.322. Deployment bundle

```text
AXDEP
 ├── packages
 ├── dependencies
 ├── trust metadata
 ├── manifest
 └── provenance
```

---

# 593.323. Deployment bundle identity

`AXDEP` có content identity riêng.

---

# 593.324. Deployment import

```text
axiom deploy import bundle.axdep
```

---

# 593.325. Deployment preflight

Trước installation:

```text target
architecture
OS
dependencies
storage
capabilities
signature
```

---

# 593.326. Insufficient storage

Installation phải fail trước commit nếu không đủ storage khi có thể detect.

---

# 593.327. Insufficient capability

Mandatory capability unavailable → preflight failure.

---

# 593.328. ABI conflict

ABI conflict → preflight failure.

---

# 593.329. Signature failure

Signature failure → no activation.

---

# 593.330. Provenance failure

Nếu release policy yêu cầu provenance và provenance thiếu → no activation.

---

# 593.331. Package schema failure

Malformed package → reject.

---

# 593.332. Runtime compatibility failure

Required runtime unavailable/incompatible → reject.

---

# 593.333. Platform adapter failure

Unsupported platform feature → explicit deployment error.

---

# 593.334. Installation rollback

Any failure before activation leaves previous active state intact.

---

# 593.335. Crash recovery

Installer state machine phải recover after process/system crash.

---

# 593.336. Update atomicity

Activation switch phải atomic theo platform capability.

---

# 593.337. Multi-process applications

Manifest có thể khai báo multiple processes.

---

# 593.338. Process graph

```text
Application
 ├── GUI
 ├── worker
 └── helper
```

---

# 593.339. Process dependency

Process graph có startup/shutdown ordering.

---

# 593.340. Process capability

Mỗi process có capability subset.

---

# 593.341. IPC

Process graph có thể khai báo IPC endpoints.

---

# 593.342. IPC security

IPC endpoints phải có identity/capability policy.

---

# 593.343. Shared memory

Nếu application dùng shared memory, deployment metadata có thể khai báo required platform facility.

---

# 593.344. GPU runtime

GPU dependencies phải được distinguish:

```text bundled runtime
system driver
```

---

# 593.345. Driver dependency

Application không bundle arbitrary kernel driver trong ordinary application package.

---

# 593.346. Driver capability

Driver installation là separate privileged deployment operation.

---

# 593.347. Hardware requirements

Manifest có thể declare:

```text CPU features
RAM minimum
GPU features
storage
OS version
```

---

# 593.348. Hardware requirement semantics

Hardware requirement failure phải được phát hiện trước activation khi có thể.

---

# 593.349. Optional hardware

Optional hardware capabilities không block installation.

---

# 593.350. Application metadata

Display name/icon/category/description nằm trong metadata.

---

# 593.351. Icon resources

Icons được package như resources.

---

# 593.352. Branding metadata

Branding không ảnh hưởng code semantics.

---

# 593.353. Localization metadata

Application metadata có thể localized.

---

# 593.354. Accessibility metadata

Package có thể declare accessibility features/requirements.

---

# 593.355. Accessibility does not alter ABI

Accessibility metadata nằm deployment/UI layer.

---

# 593.356. GUI integration

GUI application từ `452` được represent như application entrypoint.

---

# 593.357. Console integration

Console application có console entrypoint.

---

# 593.358. Service integration

Service application có service lifecycle metadata.

---

# 593.359. Library-only package

Không có application entrypoint vẫn có thể dùng deployment package để distribute library.

---

# 593.360. Framework package

Một package có thể export:

```text libraries
headers/FFI metadata
resources
runtime metadata
```

---

# 593.361. Native SDK package

SDK package có thể chứa:

```text headers
ABI metadata
libraries
docs
tools
```

nhưng SDK distribution khác application deployment.

---

# 593.362. Package role

Manifest khai báo:

```text application
library
framework
plugin
runtime
sdk
tool
```

---

# 593.363. Role validation

Application package phải có required entrypoint.

Library package không bắt buộc entrypoint.

---

# 593.364. Package composition

Application có thể consume library/framework/plugin packages.

---

# 593.365. Immutable package content

Published package contents immutable.

---

# 593.366. Repackaging

Repackaging creates new package identity.

---

# 593.367. Metadata-only mutation

Metadata mutation cũng tạo package identity mới nếu metadata thuộc canonical package.

---

# 593.368. Signature envelope

Signature có thể thay đổi mà không đổi unsigned logical content identity.

---

# 593.369. Trust metadata

Trust metadata có separate identity.

---

# 593.370. Package trust state

```text
Unknown
Verified
Trusted
Revoked
Quarantined
```

---

# 593.371. No numerical trust score

Deployment trust sử dụng categorical policy state, không numerical ranking.

---

# 593.372. Package security scanner

External security scanner có thể attach report.

---

# 593.373. Scanner result

Scanner result không thay đổi package content identity.

---

# 593.374. Scanner policy

Release policy có thể yêu cầu scanner result.

---

# 593.375. Scanner independence

Compiler không phụ thuộc scanner.

---

# 593.376. SBOM verification

SBOM phải reference actual shipped identities.

---

# 593.377. Dependency closure verification

SBOM/package graph phải khớp deployment graph.

---

# 593.378. Supply-chain continuity

```text Registry 591
      ↓
Build 592
      ↓
Package 593
      ↓
Deployment
```

không được mất provenance ở bất kỳ boundary nào.

---

# 593.379. Package build action

Package generation được integrate vào `592`.

---

# 593.380. Remote package build

Packaging action có thể chạy remote nếu hoàn toàn hermetic.

---

# 593.381. Signing remains isolated

Signing private key không được đưa vào ordinary remote package build.

---

# 593.382. Signed package build

```text package build
 ↓
package verify
 ↓
secure signer
 ↓
signature
```

---

# 593.383. Deployment verification chain

```text Content Hash
      ↓
Schema
      ↓
Dependency
      ↓
ABI
      ↓
Target
      ↓
Provenance
      ↓
Signature
      ↓
Policy
      ↓
Install
```

---

# 593.384. Final application identity

```text ApplicationArtifactID =
Hash(
    deployment graph
    artifact identities
    resource identities
    package policy
)
```

---

# 593.385. Final package identity

```text PackageID =
Hash(canonical AXPK content)
```

---

# 593.386. Native artifact identity

Không thay đổi khi package chỉ wrap artifact.

---

# 593.387. Package identity changes

Package identity thay đổi nếu:

- executable thay đổi;
- library thay đổi;
- resource thay đổi;
- manifest canonical content thay đổi;
- dependency closure thay đổi;
- packaging policy thay đổi.

---

# 593.388. Signature change

Signature envelope có thể thay đổi mà không necessarily đổi unsigned package identity.

---

# 593.389. Deployment graph explainability

Mọi package file phải truy ngược được:

```text file
→ artifact
→ build action
→ source/package
```

nếu provenance policy yêu cầu.

---

# 593.390. Reproducible deployment test

CI:

```text Build machine A
        ↓
      AXPK A

Build machine B
        ↓
      AXPK B

compare canonical identity
```

---

# 593.391. Platform verification test

Mỗi target:

```text package
→ install simulation
→ dependency verification
→ launch validation
```

---

# 593.392. Installer test

Test:

```text fresh install
upgrade
rollback
uninstall
interrupted install
interrupted update
corrupt package
missing dependency
wrong architecture
invalid signature
```

---

# 593.393. Package fuzzing

AXPK parser/verifier phải fuzz:

```text header
manifest
tables
chunks
signatures
malformed offsets
```

---

# 593.394. Parser safety

Malformed package không được gây memory corruption hoặc arbitrary code execution trong verifier.

---

# 593.395. Installer safety

Package parsing phải hoàn tất trước privileged installation actions khi có thể.

---

# 593.396. Privilege separation

Installer frontend và privileged backend nên tách process.

---

# 593.397. Privileged helper

Privileged helper chỉ nhận validated declarative operations.

---

# 593.398. No arbitrary installer code

Default AXPK installation không execute package-provided native code.

---

# 593.399. Installer capability escalation

Explicit install hook nếu tồn tại phải có separate security boundary.

---

# 593.400. FINAL HARD INVARIANTS

### Invariant 1 — package ≠ executable

> Application package là deployment graph, không phải chỉ native executable.

### Invariant 2 — immutable deployment identity

> Cùng deployment inputs phải tạo cùng canonical package identity trong reproducible mode.

### Invariant 3 — complete dependency closure

> Mọi runtime dependency phải được bundled hoặc explicit system dependency.

### Invariant 4 — target correctness

> Không được cài artifact sai OS, architecture, ABI hoặc CPU feature.

### Invariant 5 — deterministic packaging

> File order, metadata, compression và serialization phải canonical trong reproducible mode.

### Invariant 6 — content verification

> Package contents phải được hash-verify trước activation.

### Invariant 7 — provenance continuity

> Source → build → artifact → package phải giữ được provenance chain.

### Invariant 8 — signature separation

> Signing xác nhận authority/trust; không thay thế content verification.

### Invariant 9 — no arbitrary installer execution

> Package installation mặc định là declarative và không chạy code tùy ý.

### Invariant 10 — transactional installation

> Installation/update phải stage → verify → activate → commit.

### Invariant 11 — rollback safety

> Failure trong update không được để lại một application state nửa cũ/nửa mới.

### Invariant 12 — capability separation

> Manifest khai báo capability; OS/user quyết định permission grant.

### Invariant 13 — immutable application code

> Installed application code/resources không được coi là mutable application data.

### Invariant 14 — native ABI validation

> Native dependency mismatch phải được phát hiện trước execution.

### Invariant 15 — platform isolation

> Platform-specific packaging logic nằm trong adapter layer, không làm ô nhiễm Axiom core semantics.

### Invariant 16 — offline deployment

> Package đã chứa đủ dependency/trust metadata phải có khả năng verify/install offline.

### Invariant 17 — cache integration

> Packaging là build action và được hưởng incremental/distributed cache của `592`.

### Invariant 18 — no compiler dependency

> Application packaging không phụ thuộc LLVM/GCC/Clang/MSVC để tạo native artifacts.

### Invariant 19 — signing-key isolation

> Private signing keys không được đưa vào generic compiler/build workers.

### Invariant 20 — AI deployment safety

> AI có thể lập kế hoạch và giải thích deployment nhưng không được tự ý bypass verification, cấp privilege hoặc ký artifact.

---

# 593 — LOCKED

Axiom giờ đã có chuỗi:

```text
                    AXIOM SOURCE
                         │
                         ▼
                 Semantic Compiler
                         │
                         ▼
                  Native Machine Code
                         │
                         ▼
                    Object/Link
                         │
                         ▼
                   Native Image
                         │
                         ▼
                 Package Registry
                         │
                         ▼
                 Distributed Build
                         │
                         ▼
                Deployment Graph
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Windows         Linux          Apple
       Package        Package         Bundle
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                 Signed Distribution
                         │
                         ▼
                   Installed App
```

Đây là boundary quan trọng: **Axiom không chỉ là compiler nữa mà đã có một native software delivery model hoàn chỉnh**, trong khi compiler core vẫn được giữ độc lập với package/deployment infrastructure.

---

# NEXT — BOOTSTRAP-594

## NATIVE APPLICATION RUNTIME & PROCESS SUPERVISION 5.0
### PROCESS TREE, APPLICATION INSTANCE, STARTUP/SHUTDOWN, CRASH RECOVERY, SERVICE LIFECYCLE, IPC SUPERVISION, CHILD PROCESS, RESOURCE LIMITS, SIGNALS, HEALTH STATE, GRACEFUL TERMINATION & CROSS-PLATFORM PROCESS MODEL

```text
                    Application
                         │
                         ▼
                  Runtime Supervisor
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Main Process    Worker         Helper
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                    IPC / Events
                         │
                         ▼
                  Health / Lifecycle
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Running        Failed         Stopped
          │              │
          │              ▼
          │          Recovery Policy
          │              │
          └──────────────┴──────→ Restart / Exit
```

`594` sẽ định nghĩa **process model ở runtime/application level**, tách biệt với OS process primitives của `441`, đồng thời kết nối trực tiếp với application bundle `593`, concurrency `424`, task system `471`, actor system `472`, IPC `454` và debugger/crash model `589`.