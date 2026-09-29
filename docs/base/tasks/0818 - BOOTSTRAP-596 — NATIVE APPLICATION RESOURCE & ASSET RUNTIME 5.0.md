# BOOTSTRAP-596 — NATIVE APPLICATION RESOURCE & ASSET RUNTIME 5.0
## RESOURCE IDENTIFIERS, EMBEDDED ASSETS, FILESYSTEM ASSETS, STREAMING RESOURCES, LOCALIZATION, FONT/IMAGE/AUDIO/VIDEO RESOURCES, RESOURCE CACHE, MEMORY MAPPING, VERSIONING, HOT REPLACEMENT & ZERO-COPY RESOURCE ACCESS

**Trạng thái: COMPLETED / LOCKED**

`596` định nghĩa runtime resource layer thống nhất cho Axiom. Nó nối `469` Resource/Asset/Bundle, `593` Application Package, `455` Storage/File I/O, `464` Text/Font, `460` Graphics, `461` Audio và media layer.

Mục tiêu:

> Một asset phải có identity ổn định, được resolve thống nhất dù nằm embedded trong binary, trong application bundle hay bên ngoài; resource lớn phải có khả năng stream/memory-map; resource nhỏ có thể truy cập zero-copy; và application không phải biết platform đang dùng cơ chế bundle nào.

---

# 596.1. Resource abstraction

```text
                    Application
                         │
                         ▼
                  Resource Manager
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Embedded    Bundle     External
           Resource    Asset       Asset
              │          │          │
              └──────────┼──────────┘
                         ▼
                  Resource Resolver
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Memory           Stream            MMap
     Resource         Resource          Resource
```

---

# 596.2. Resource ≠ File

Resource là logical application data.

Một resource có thể không tương ứng với một filesystem file.

---

# 596.3. Resource ≠ Asset

Asset là một loại resource có nguồn từ application content.

---

# 596.4. Resource identity

Mỗi resource có stable logical identity:

```text
ResourceID
```

---

# 596.5. ResourceID

```text
ResourceID {
    namespace
    name
    variant
}
```

---

# 596.6. Resource namespace

Ví dụ:

```text
ui
images
fonts
audio
video
locales
models
data
```

---

# 596.7. Resource name

Resource name phải canonical và UTF-8.

---

# 596.8. Resource variant

Variant dùng cho:

```text
locale
platform
density
theme
architecture
quality
```

---

# 596.9. Content identity

Resource cũng có content hash:

```text
ResourceContentID
```

---

# 596.10. Logical vs content identity

```text
ResourceID        → semantic identity
ContentID         → exact bytes identity
```

---

# 596.11. Resource manifest

Bundle `593` có resource table.

```text
ResourceEntry {
    resource_id
    content_id
    type
    size
    compression
    flags
}
```

---

# 596.12. Resource type

Type metadata có thể là:

```text
bytes
text
image
font
audio
video
shader
model
data
custom
```

---

# 596.13. Custom resource type

Application/package có thể define custom resource types.

---

# 596.14. MIME/media metadata

Resource có thể chứa MIME-like type metadata nhưng semantic type là Axiom-defined type.

---

# 596.15. Embedded resource

Compiler/linker có thể embed resource trực tiếp vào native artifact.

---

# 596.16. Bundle resource

Resource có thể nằm ngoài executable trong `AXPK`.

---

# 596.17. External resource

Application có thể resolve resource từ filesystem hoặc provider được cấp quyền.

---

# 596.18. Generated resource

Runtime/plugin có thể tạo resource ephemeral.

---

# 596.19. Resource origin

```text
Embedded
Bundled
Filesystem
Provider
Generated
```

---

# 596.20. Resource resolution

```text
ResourceID
   ↓
Resolver
   ↓
Candidate sources
   ↓
Policy
   ↓
Selected resource
```

---

# 596.21. Resolution priority

Default:

```text
RuntimeOverride
ExternalOverride
Bundle
Embedded
```

Chỉ source được policy cho phép mới được override.

---

# 596.22. Production override

Production bundle có thể cấm external override để đảm bảo integrity.

---

# 596.23. Development override

Development environment có thể cho phép external assets.

---

# 596.24. Resource lookup

```text
resource.open(id)
```

không bắt buộc load toàn bộ content vào RAM.

---

# 596.25. Resource handle

```text
ResourceHandle
```

là managed resource reference.

---

# 596.26. Resource lifetime

Handle sử dụng ownership semantics `423`.

---

# 596.27. Resource metadata

```text
ResourceMetadata {
    id
    type
    size
    content_id
    origin
    compression
}
```

---

# 596.28. Resource existence

```text
resource.exists(id)
```

không cần load payload.

---

# 596.29. Resource open modes

```text
Read
Stream
Map
MetadataOnly
```

---

# 596.30. Read resource

Resource nhỏ có thể được read thành immutable byte buffer.

---

# 596.31. Immutable resource data

Bundle resources mặc định immutable.

---

# 596.32. Writable resources

Writable application data phải nằm ngoài immutable resource bundle.

---

# 596.33. Resource stream

```text
ResourceStream
```

có:

```text
read()
seek()
position()
size()
close()
```

nếu source hỗ trợ.

---

# 596.34. Sequential stream

Streaming source có thể không hỗ trợ seek.

---

# 596.35. Capability query

```text stream.capabilities()
```

trả:

```text Read
Seek
Map
Async
```

---

# 596.36. Async resource I/O

Resource stream có thể hỗ trợ async read tích hợp `424`.

---

# 596.37. Backpressure

Async resource streams phải hỗ trợ bounded buffering.

---

# 596.38. Zero-copy access

Resource có thể expose immutable byte view trực tiếp trên mapped/embedded memory.

---

# 596.39. Zero-copy contract

Zero-copy chỉ được guarantee khi resource source/lifetime đáp ứng điều kiện.

---

# 596.40. Mapped resource

```text
MappedResource {
    bytes
    offset
    length
}
```

---

# 596.41. Memory mapping

Large resource có thể memory-map thay vì allocate/copy.

---

# 596.42. Mapping granularity

Platform adapter xử lý page alignment.

---

# 596.43. Partial mapping

Resource manager có thể map subrange.

---

# 596.44. Unmap

Mapping release theo handle lifetime.

---

# 596.45. Mapping failure

Không được fallback âm thầm sang huge allocation nếu resource policy cấm.

---

# 596.46. Compression

Bundle resource có thể compressed.

---

# 596.47. Compression vs zero-copy

Compressed resource không thể zero-copy trực tiếp thành uncompressed payload.

---

# 596.48. Streaming decompression

Compressed resource lớn phải hỗ trợ streaming decompression nếu codec cho phép.

---

# 596.49. Resource compression metadata

```text
CompressionInfo {
    codec
    compressed_size
    uncompressed_size
}
```

---

# 596.50. Resource integrity

Content hash phải được verify theo package trust policy.

---

# 596.51. Hash verification

```text
bytes → Hash → expected ContentID
```

---

# 596.52. Corrupt resource

Hash mismatch:

```text ResourceIntegrityError
```

---

# 596.53. No silent corruption

Runtime không được sử dụng resource có integrity failure trừ khi explicit recovery policy.

---

# 596.54. Resource cache

Resource manager có cache layers:

```text
MetadataCache
CompressedCache
DecodedCache
MappedCache
```

---

# 596.55. Cache policy

Application có thể chọn cache behavior.

---

# 596.56. Cache size

Cache có bounded size.

---

# 596.57. Cache eviction

LRU/LFU/size-aware policies có thể được implementation-defined.

---

# 596.58. Cache correctness

Cache key phải chứa content identity và relevant decode parameters.

---

# 596.59. Cache invalidation

ContentID thay đổi → cached decoded resource không được reuse.

---

# 596.60. Resource deduplication

Identical ContentID resources có thể share physical storage.

---

# 596.61. Bundle deduplication

Package builder nên deduplicate identical payloads.

---

# 596.62. Memory deduplication

Runtime có thể share immutable decoded resources.

---

# 596.63. Resource pinning

Application có thể pin resource trong cache.

---

# 596.64. Pin limits

Pinning không được bypass global memory policy.

---

# 596.65. Resource priority

Resource có thể có:

```text Critical
Normal
Prefetch
Optional
```

---

# 596.66. Prefetch

```text resource.prefetch(id)
```

không đảm bảo resource đã available nếu provider failure.

---

# 596.67. Lazy loading

Default resource loading là lazy.

---

# 596.68. Startup optimization

Critical resources có thể preload trong startup phase.

---

# 596.69. No mandatory preload

Không được preload toàn bộ application assets mặc định.

---

# 596.70. Resource groups

```text
ResourceGroup
```

cho phép batch load/release.

---

# 596.71. Dependency

Resource có thể declare dependency:

```text shader → texture
scene → mesh/material
```

---

# 596.72. Resource dependency cycle

Circular resource dependency phải được phát hiện nếu graph được khai báo.

---

# 596.73. Resource graph

```text
Scene
 ├── Mesh
 ├── Material
 │    └── Texture
 └── Audio
```

---

# 596.74. Resource loading graph

Loader có thể parallelize independent resources.

---

# 596.75. Deterministic dependency resolution

Resource graph resolution phải deterministic.

---

# 596.76. Resource loader

```text ResourceLoader<T>
    load()
    decode()
    validate()
```

---

# 596.77. Generic loaders

Static generic loaders có thể monomorphize.

---

# 596.78. Dynamic loader

Runtime registry có thể map resource type → decoder.

---

# 596.79. Decoder registration

Custom decoder phải explicitly registered.

---

# 596.80. Decoder isolation

Untrusted/custom decoder không mặc định có arbitrary process/system capabilities.

---

# 596.81. Malformed resource

Decoder phải reject malformed resource thay vì crash runtime.

---

# 596.82. Decoder resource limits

Decoder có limits:

```text dimensions
memory
decode_time
nesting
```

---

# 596.83. Image resource

Image resource metadata:

```text width
height
format
color_space
mip_levels
```

---

# 596.84. Image lazy decode

Image payload có thể decode on demand.

---

# 596.85. GPU upload

GPU upload thuộc `460` và không được coi là resource storage primitive.

---

# 596.86. Texture resource

Texture có logical resource identity và GPU residency có lifecycle riêng.

---

# 596.87. GPU resource state

```text Asset
 ↓
Decoded
 ↓
GPUUploaded
 ↓
Resident
```

---

# 596.88. GPU eviction

GPU resource có thể evict mà asset vẫn tồn tại.

---

# 596.89. Font resource

Font resource tích hợp `464`.

---

# 596.90. Font loading

Font có thể được loaded từ bundle mà không cần install vào OS.

---

# 596.91. Audio resource

Audio resource tích hợp `461`.

---

# 596.92. Audio streaming

Long audio phải hỗ trợ streaming.

---

# 596.93. Video resource

Video resource phải hỗ trợ streaming và decoder lifecycle.

---

# 596.94. Large media

Large media không được mặc định decode toàn bộ vào memory.

---

# 596.95. Model resource

AI models/checkpoints có thể là resource type lớn.

---

# 596.96. Model streaming

Model loader có thể memory-map weight segments.

---

# 596.97. Model identity

Model content identity phải distinguish:

```text model logical ID
weight content ID
architecture/config ID
```

---

# 596.98. Localization resource

Localization resources:

```text
locales/en
locales/vi
locales/ja
```

---

# 596.99. Locale resolution

```text explicit locale
   ↓
application locale
   ↓
system locale
   ↓
default locale
```

---

# 596.100. Locale fallback

Ví dụ:

```text vi-VN
 ↓
vi
 ↓
default
```

---

# 596.101. Locale determinism

Fallback chain phải deterministic.

---

# 596.102. Missing translation

Application policy:

```text fallback
error
placeholder
```

---

# 596.103. No silent wrong locale

Locale mismatch phải observable.

---

# 596.104. Resource variant resolution

Variant dimensions được resolve theo explicit priority.

---

# 596.105. Density variants

GUI assets có thể:

```text 1x
2x
3x
```

---

# 596.106. Theme variants

```text light
dark
high_contrast
```

---

# 596.107. Platform variants

```text windows
linux
macos
android
ios
wasm
```

---

# 596.108. Architecture variants

```text x86_64
aarch64
wasm32
```

---

# 596.109. Variant conflict

Hai variants cùng priority và không thể resolve → configuration/resource resolution error.

---

# 596.110. Resource aliases

Logical resource có thể alias resource khác.

---

# 596.111. Alias cycle

Alias cycle là error.

---

# 596.112. Resource URI

Có thể hỗ trợ canonical resource URI:

```text
axres://namespace/name
```

---

# 596.113. URI identity

URI canonicalization không làm thay đổi underlying ResourceID.

---

# 596.114. Embedded binary layout

Embedded resource section phải được linker đặt trong read-only data segment khi phù hợp.

---

# 596.115. Resource alignment

Compiler/linker đảm bảo alignment required bởi resource format.

---

# 596.116. Embedded resource access

Embedded bytes có thể được expose bằng immutable slice.

---

# 596.117. No copy requirement

Small embedded resource access không được yêu cầu copy nếu caller chỉ cần immutable bytes.

---

# 596.118. Bundle access

Bundle resource có thể được đọc từ package container bằng offset/length.

---

# 596.119. Package locality

Resource package object phải hỗ trợ random access nếu format cho phép.

---

# 596.120. Package streaming

AXPK resource container phải hỗ trợ sequential extraction.

---

# 596.121. Resource index

Bundle resource table nên có efficient lookup:

```text ResourceID → entry
```

---

# 596.122. Resource index structure

Implementation có thể dùng sorted table/hash index.

---

# 596.123. Deterministic index

Package generation phải canonicalize index ordering.

---

# 596.124. Resource version

Logical resource có version metadata.

---

# 596.125. Content version

ContentID vẫn là authoritative identity của exact bytes.

---

# 596.126. Resource update

External resources có thể update độc lập bundle nếu policy cho phép.

---

# 596.127. Immutable bundle

Installed application bundle mặc định immutable.

---

# 596.128. Writable asset cache

Generated/processed resources có thể nằm trong writable cache.

---

# 596.129. Cache ≠ source asset

Cache corruption không được làm mất canonical source resource.

---

# 596.130. Cache rebuild

Invalid cache phải có khả năng regenerate.

---

# 596.131. Resource persistence

Application data persistence thuộc `455`, không thuộc immutable resource manager.

---

# 596.132. Resource installation

Installer `593` deploy resource package atomically.

---

# 596.133. Resource package verification

Resources phải verify trước activation nếu package integrity policy yêu cầu.

---

# 596.134. Partial deployment

Application không được active package nếu required resources chưa hoàn tất.

---

# 596.135. Deployment rollback

Resource deployment rollback phải atomic với application package activation.

---

# 596.136. Resource garbage collection

Axiom không có GC bắt buộc.

Resource cache eviction không phải memory GC.

---

# 596.137. Explicit resource lifetime

Application handles release deterministic.

---

# 596.138. Shared resource lifetime

Immutable resource có thể được shared bằng reference-counted library/runtime mechanism.

---

# 596.139. Resource ownership

Ownership semantics tuân `423`.

---

# 596.140. Async resource lifetime

Async operations giữ resource handle đủ lâu để operation hoàn tất.

---

# 596.141. Cancellation

Cancelled resource operation phải release pending resources.

---

# 596.142. Resource locking

Read-only resources không cần application-level lock.

---

# 596.143. External mutable resource

Mutable external resource phải dùng explicit synchronization.

---

# 596.144. File watching

External development assets có thể được watched.

---

# 596.145. Hot replacement

```text old resource
     ↓
new resource
     ↓
validate
     ↓
publish
```

---

# 596.146. Atomic resource replacement

Readers đang sử dụng old resource được phép hoàn thành.

---

# 596.147. New readers

New readers nhận resource version mới.

---

# 596.148. Resource generation

Resource runtime có:

```text generation
```

để detect replacement.

---

# 596.149. Stale resource handle

Handle tới replaced resource không tự động trỏ sang new content.

---

# 596.150. Explicit refresh

```text resource.refresh(id)
```

lấy current generation.

---

# 596.151. Resource subscription

Application có thể subscribe resource change events.

---

# 596.152. Change event

```text ResourceChanged {
    id
    old_content
    new_content
    generation
}
```

---

# 596.153. Secret-like resources

Resource chứa credentials/secrets phải được phân loại qua security layer, không dùng ordinary asset pipeline.

---

# 596.154. Executable resources

Native executable payloads phải được phân biệt với ordinary assets.

---

# 596.155. Executable loading

Resource manager không được tự execute resource.

---

# 596.156. Dynamic library resource

Native libraries phải đi qua deployment/loader contract `583/593`.

---

# 596.157. Shader resources

Shader code resource được load qua graphics subsystem.

---

# 596.158. WASM resource

WASM modules là executable content và phải qua execution/security policy.

---

# 596.159. Resource trust

Resource trust status:

```text Verified
Unverified
Rejected
```

---

# 596.160. Trusted resource execution

Executable resources chỉ được execute nếu trust/capability policy cho phép.

---

# 596.161. Resource metadata security

Metadata không được giả định là trustworthy nếu source chưa verify.

---

# 596.162. Path traversal

Bundle extraction phải reject paths:

```text ../
absolute paths
```

và equivalent platform escape forms.

---

# 596.163. Symlink policy

Package resources không được tự tạo arbitrary symlink ngoài explicit policy.

---

# 596.164. Resource namespace isolation

Một package không được override resource namespace của package khác ngoài dependency/overlay policy.

---

# 596.165. Dependency resources

Dependency resources có namespace riêng.

---

# 596.166. Resource collision

Collision phải resolve deterministic hoặc error.

---

# 596.167. Package-qualified ID

Có thể dùng:

```text
package::namespace::name
```

để tránh collision.

---

# 596.168. Resource localization

Localization package có thể được separate artifact.

---

# 596.169. Optional localization

Unused locale resources có thể được omitted khỏi deployment package.

---

# 596.170. Resource slicing

Deployment builder có thể tạo locale/platform-specific resource subset.

---

# 596.171. Resource dependency closure

Sliced package phải preserve complete required resource closure.

---

# 596.172. Resource size analysis

Build tooling phải report:

```text resource size
compressed size
decoded size
package contribution
```

---

# 596.173. Resource size budget

Application có thể đặt maximum resource package size.

---

# 596.174. Startup resource budget

Critical startup resources có thể có budget riêng.

---

# 596.175. Resource telemetry

Runtime có thể record:

```text load latency
cache hit
decode latency
I/O bytes
```

---

# 596.176. No mandatory telemetry

Telemetry disabled/removed trong minimal runtime.

---

# 596.177. Resource tracing

Resource operations có trace IDs khi tracing enabled.

---

# 596.178. Resource diagnostics

Diagnostics phải distinguish:

```text missing
corrupt
unsupported
permission_denied
decode_failed
```

---

# 596.179. Missing resource

Missing required resource có thể làm component initialization fail.

---

# 596.180. Optional resource

Optional resource failure không được crash application mặc định.

---

# 596.181. Resource fallback

Fallback resources phải được explicit khai báo.

---

# 596.182. Fallback chain

```text requested
 ↓
variant fallback
 ↓
locale fallback
 ↓
default
```

---

# 596.183. Fallback cycle

Cycle phải được detect.

---

# 596.184. Resource API type safety

Resource type mismatch:

```text ResourceTypeError
```

không undefined cast.

---

# 596.185. Generic typed resource

```text resource.open<Image>("ui/logo")
```

có thể kiểm tra type metadata.

---

# 596.186. Dynamic resource

Generic bytes API vẫn tồn tại cho custom data.

---

# 596.187. Decode API

```text resource.decode<T>()
```

phải sử dụng registered decoder.

---

# 596.188. Decoder determinism

Decoder output phải deterministic với cùng payload + decoder version/options, trừ explicitly nondeterministic media operations.

---

# 596.189. Decoder version

Decoded cache key phải bao gồm decoder version.

---

# 596.190. Resource compatibility

Resource schema version có thể khác application version.

---

# 596.191. Migration

Resource format migration có thể convert old resource thành current representation.

---

# 596.192. Migration cache

Migrated resource có thể cache theo source ContentID + migration version.

---

# 596.193. Original preservation

Migration không được overwrite canonical immutable source resource.

---

# 596.194. Resource garbage cleanup

Generated cache entries có thể delete khi stale.

---

# 596.195. Offline operation

Bundle resources phải hoạt động offline.

---

# 596.196. Remote resource provider

Remote resource providers là optional extension.

---

# 596.197. Remote cache

Remote resources nên cache content-addressably.

---

# 596.198. Remote integrity

Remote content phải verify ContentID.

---

# 596.199. Remote availability

Network failure không được coi là resource corruption.

---

# 596.200. Resource provider interface

```text
ResourceProvider {
    locate(id)
    metadata(id)
    open(id)
}
```

---

# 596.201. Provider priority

Provider priority phải deterministic.

---

# 596.202. Provider capability

Provider khai báo:

```text
Read
Stream
Seek
Map
Watch
```

---

# 596.203. Provider sandbox

Provider không được tự động có arbitrary filesystem/network privileges.

---

# 596.204. Resource manager architecture

```text
ResourceManager
 │
 ├── Registry
 ├── Resolver
 ├── ProviderSet
 ├── IntegrityVerifier
 ├── DecoderRegistry
 ├── Cache
 └── VariantResolver
```

---

# 596.205. Resource registry

Registry map:

```text ResourceID → ResourceDescriptor
```

---

# 596.206. Resolver

Resolver chọn provider/resource variant.

---

# 596.207. Integrity verifier

Verifier xác nhận exact content.

---

# 596.208. Decoder registry

Decoder registry maps resource type → decoder.

---

# 596.209. Cache

Cache stores decoded/mapped representations.

---

# 596.210. Variant resolver

Variant resolver chọn locale/platform/density/theme variant.

---

# 596.211. Resource load pipeline

```text
ResourceID
   ↓
Lookup
   ↓
Variant Resolve
   ↓
Provider Select
   ↓
Integrity Verify
   ↓
Open
   ↓
Decode/Map/Stream
   ↓
Cache
   ↓
Typed Resource
```

---

# 596.212. Error boundary

Mỗi phase phải preserve error category.

---

# 596.213. Resource cancellation

Pipeline phải propagate cancellation.

---

# 596.214. Resource deadline

Long decode/network operation có thể có deadline.

---

# 596.215. Resource priority scheduling

Loader có thể schedule critical resources before prefetch resources.

---

# 596.216. Parallel loading

Independent resources có thể load song song.

---

# 596.217. Deterministic publication

Parallel loading vẫn phải publish resource state deterministically.

---

# 596.218. Resource dependency failure

Dependent resource không được publish Ready khi required dependency failed.

---

# 596.219. Partial resource availability

Independent resources vẫn có thể Ready.

---

# 596.220. Resource state

```text
Unknown
Loading
Ready
Failed
Stale
```

---

# 596.221. Resource state machine

```text
Unknown
   │
   ▼
Loading
 ┌─┴──────┐
 ▼        ▼
Ready    Failed
 │
 ▼
Stale
 │
 ▼
Reloading
```

---

# 596.222. State generation

Mỗi successful publication increment generation.

---

# 596.223. Resource snapshots

Resource manager có thể expose immutable snapshot của registry.

---

# 596.224. IDE resource index

IDE `590` có thể index:

```text resource ID
source file
consumer
type
variants
```

---

# 596.225. Resource completion

IDE có thể autocomplete resource IDs.

---

# 596.226. Resource rename

Semantic rename có thể update known resource references.

---

# 596.227. Dead resource detection

Compiler/tooling có thể detect resources không có static consumers.

---

# 596.228. Dynamic references

Dynamic resource names làm static dead-resource detection không chắc chắn.

---

# 596.229. AI resource inspection

AI có thể query:

```text resource graph
resource sizes
dependencies
variants
integrity
```

---

# 596.230. AI no arbitrary loading

AI tooling không được tự động execute/decode untrusted executable resource.

---

# 596.231. AI provenance

AI output phải reference resource ContentID khi mô tả exact asset.

---

# 596.232. Package/resource provenance

```text Source
 ↓
Resource Build
 ↓
ContentID
 ↓
Package
 ↓
Deployment
```

---

# 596.233. Reproducible resource packaging

Resource ordering, metadata encoding và compression parameters phải canonicalizable.

---

# 596.234. Resource package hash

Resource changes làm thay đổi package identity nếu resource thuộc immutable package content.

---

# 596.235. External resources

External resources không thay đổi immutable package hash.

---

# 596.236. Development asset override

Development override phải observable trong runtime diagnostics.

---

# 596.237. Production override prevention

Production policy có thể reject unsigned external override.

---

# 596.238. Resource signature

Package signature covers resource table/content according to `593`.

---

# 596.239. Resource verification timing

Verification có thể:

```text package install
first access
both
```

theo security/performance policy.

---

# 596.240. Verified cache

Cache entry generated from verified content có thể carry verification status.

---

# 596.241. Cache trust

Unverified cached payload không được bypass required verification.

---

# 596.242. Resource manager startup

Minimal applications có thể omit ResourceManager nếu không dùng packaged resources.

---

# 596.243. Static embedding optimization

Compiler có thể optimize direct embedded resource access:

```text resource ID
→ static address + length
```

khi resource statically known.

---

# 596.244. Direct asset lowering

Static embedded byte resource có thể lower thành:

```text const byte[]
```

---

# 596.245. Runtime lookup elimination

Compiler có thể eliminate resource hash lookup khi resource identity compile-time known và bundle layout fixed.

---

# 596.246. Dynamic lookup preservation

Dynamic ResourceID vẫn dùng runtime registry.

---

# 596.247. No mandatory reflection

Resource system không yêu cầu full runtime reflection.

---

# 596.248. Binary size

Unused resource decoders/providers/cache code phải dead-strip được.

---

# 596.249. Resource format extensibility

Custom resource formats không được yêu cầu sửa compiler core.

---

# 596.250. Resource plugin boundary

Custom decoder có ABI/plugin boundary rõ ràng.

---

# 596.251. Plugin lifecycle

Plugin resource decoder có lifecycle riêng, không được giữ resource handles vô hạn.

---

# 596.252. Resource unload

```text resource.release()
```

giải phóng runtime-owned representation khi không còn references.

---

# 596.253. GPU unload

GPU resource release delegated to graphics subsystem.

---

# 596.254. Decoder unload

Dynamic decoder unload chỉ khi không còn active decode operations.

---

# 596.255. Thread safety

ResourceManager API phải document thread safety.

---

# 596.256. Concurrent lookup

Read-only lookup phải có thể chạy concurrent.

---

# 596.257. Concurrent load deduplication

Hai concurrent requests cùng ContentID có thể share một in-flight load.

---

# 596.258. In-flight load

```text Request A ─┐
Request B ──────┼→ Single Load → Shared Result
Request C ──────┘
```

---

# 596.259. Load cancellation

Cancellation của một caller không được cancel shared load nếu còn caller khác.

---

# 596.260. Final hard invariants

### Invariant 1 — stable identity

> ResourceID biểu diễn logical identity; ContentID biểu diễn exact content identity.

### Invariant 2 — immutable packaged resources

> Resource trong immutable application package không được mutate tại runtime.

### Invariant 3 — writable separation

> Writable application data không được giả dạng immutable bundle resource.

### Invariant 4 — deterministic resolution

> Resource provider/variant resolution phải deterministic.

### Invariant 5 — integrity

> Resource content đã yêu cầu verification phải được verify trước khi sử dụng.

### Invariant 6 — no silent corruption

> Integrity failure không được bị coi là successful resource load.

### Invariant 7 — zero-copy when possible

> Resource layer phải hỗ trợ immutable zero-copy/memory-mapped access khi source cho phép.

### Invariant 8 — no mandatory full load

> Resource system không được yêu cầu load toàn bộ asset vào RAM.

### Invariant 9 — streaming

> Large media/model/resource phải có đường streaming hoặc mapping khi provider hỗ trợ.

### Invariant 10 — bounded cache

> Resource cache phải có bounded resource policy.

### Invariant 11 — cache correctness

> Decoded cache phải phụ thuộc ContentID và decoder/options identity.

### Invariant 12 — lifetime safety

> Resource mappings/streams/decoded representations phải tuân deterministic ownership/lifetime.

### Invariant 13 — atomic hot reload

> Resource replacement chỉ publish version đã validate hoàn chỉnh.

### Invariant 14 — stale safety

> Resource handle của generation cũ không được âm thầm điều khiển generation mới.

### Invariant 15 — executable separation

> Resource manager không tự động execute executable resources.

### Invariant 16 — sandbox

> Resource providers/decoders không được tự động có filesystem/network/system privilege.

### Invariant 17 — package integrity

> Resource packaging phải giữ provenance và package integrity chain của `593`.

### Invariant 18 — cross-platform abstraction

> Application code không cần biết resource đang nằm trong PE/ELF/Mach-O section, AXPK hoặc platform bundle.

### Invariant 19 — minimal runtime

> Resource functionality không sử dụng phải có thể loại khỏi final binary.

### Invariant 20 — AI truth

> AI tooling chỉ được mô tả resource dựa trên structured resource metadata/content identity đã quan sát, không suy đoán trạng thái resource.

---

# 596 — LOCKED

Resource architecture hiện tại:

```text
593 Deployment
       │
       ▼
596 Resource Runtime
       │
       ├── ResourceID / ContentID
       ├── Bundle / Embedded / External
       ├── Variant Resolution
       ├── Stream / MMap / Zero-Copy
       ├── Cache
       ├── Image / Font / Audio / Video / Model
       ├── Localization
       ├── Hot Reload
       ├── Integrity
       └── AI / IDE Metadata
```

Điểm quan trọng: **Axiom không xây một “asset manager” nặng bắt buộc cho mọi chương trình**. Một resource được compiler biết chính xác có thể được tối ưu thẳng thành địa chỉ + length; resource lớn có thể stream/mmap; application đơn giản không dùng resource subsystem thì phần lớn runtime code bị loại bỏ.

---

# NEXT — BOOTSTRAP-597

## NATIVE APPLICATION LOCAL STORAGE & USER DATA 5.0
### APPLICATION DATA DIRECTORIES, CACHE, TEMPORARY DATA, USER DOCUMENTS, DATABASE/FILE STORAGE BOUNDARY, ATOMIC FILE UPDATE, FILE WATCHING, DATA MIGRATION, QUOTAS, BACKUP/RESTORE, PORTABLE MODE, SANDBOX STORAGE & CROSS-PLATFORM USER-DATA MODEL

```text
                 Application
                      │
                      ▼
                Storage Manager
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   App Data         Cache          Temp
       │              │              │
       ├──────────────┼──────────────┤
       ▼              ▼              ▼
   Documents      Databases      Generated Data
       │              │              │
       └──────────────┼──────────────┘
                      ▼
              Platform Storage
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Desktop      Mobile       WASM
```

`597` sẽ tách rõ **immutable resources của `596`** khỏi **dữ liệu do người dùng/application tạo ra**, đồng thời chuẩn hóa đường dẫn app-data/cache/temp/documents trên Windows/Linux/macOS/iOS/Android/WASM mà không ép application code phụ thuộc vào `%APPDATA%`, XDG, sandbox container hay các path native tương ứng.