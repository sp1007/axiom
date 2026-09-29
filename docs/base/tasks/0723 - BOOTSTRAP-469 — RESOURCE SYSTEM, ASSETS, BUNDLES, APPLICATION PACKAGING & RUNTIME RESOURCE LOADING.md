# BOOTSTRAP-469 — RESOURCE SYSTEM, ASSETS, BUNDLES, APPLICATION PACKAGING & RUNTIME RESOURCE LOADING

**Trạng thái: COMPLETED / LOCKED**

469 định nghĩa resource/asset foundation dùng cho GUI, game, media, fonts, shaders, localization, models và native applications.

Nguyên tắc:

```text
Resource Identity
      ≠
Filesystem Path
      ≠
Memory Address
      ≠
Package Identity
      ≠
URL
```

và:

```text
Asset
  ↓
Logical Resource
  ↓
Loaded Resource
  ↓
CPU / GPU / Audio / Media Representation
```

Resource system phải hỗ trợ **embedded, external, lazy, streaming, memory-mapped và zero-copy** mà không ép tất cả assets vào RAM.

---

## 469.1 — Resource identity

Canonical:

```text
ResourceId {
    package
    namespace
    name
    version?
}
```

`ResourceId` là logical identity.

Không dùng absolute filesystem path làm identity.

---

## 469.2 — Resource URI

Có thể biểu diễn resource bằng URI-like syntax:

```text
res://package/name
```

Đây là logical resource reference, không phải filesystem path.

---

## 469.3 — Resource path

Filesystem path chỉ xuất hiện ở build/import/platform layer.

---

## 469.4 — Resource type

Resource có type:

```text
Image
Font
Shader
Audio
Video
Model
Mesh
Material
Text
Localization
Binary
Data
```

---

## 469.5 — MIME/type metadata

Resource có canonical type identifier và optional MIME type.

---

## 469.6 — Resource descriptor

Concept:

```text
ResourceDescriptor {
    id
    type
    size
    hash
    compression
    alignment
    dependencies
    capabilities
}
```

---

# 469.7 — Resource graph

Resources tạo directed dependency graph:

```text
Scene
 ├── Model
 │    ├── Mesh
 │    └── Material
 │          └── Texture
 ├── Font
 └── Audio
```

---

## 469.8 — Dependency identity

Dependency tham chiếu bằng `ResourceId`, không bằng memory address.

---

## 469.9 — Cycle detection

Resource compiler phải phát hiện dependency cycles khi loại resource không cho phép cycle.

---

## 469.10 — Lazy dependency

Resource dependency có thể được lazy-loaded.

---

# 469.11 — Resource loading

Loader:

```text
resolve
→ locate
→ validate
→ decode
→ construct
→ publish
```

---

## 469.12 — Loading states

```text
Unloaded
Loading
Loaded
Failed
Unloading
```

---

## 469.13 — Async loading

Resource loader hỗ trợ async theo 424.

---

## 469.14 — Blocking loading

Blocking load phải explicit.

---

## 469.15 — Lazy loading

Resource handle không đồng nghĩa resource data đã nằm trong memory.

---

## 469.16 — Resource handle

Handle:

```text
ResourceHandle<T>
```

có logical identity + loader/cache association.

---

## 469.17 — Handle lifetime

Handle không được trở thành dangling reference khi cache evict resource.

---

## 469.18 — Strong vs weak handle

Có thể hỗ trợ:

```text
StrongResource<T>
WeakResource<T>
```

Strong handle giữ resource alive; weak handle không.

---

# 469.19 — Resource cache

Cache có thể giữ decoded resources.

---

## 469.20 — Cache eviction

Eviction policy:

```text
LRU
LRU-cost
manual
budget-based
```

là library/runtime policy.

---

## 469.21 — Cache ≠ source

Cache mất đi không làm mất source asset.

---

## 469.22 — Memory budget

Application có thể đặt resource memory budget.

---

## 469.23 — GPU memory budget

GPU resources có thể có budget riêng.

---

## 469.24 — Audio memory budget

Audio decoded data có thể có budget riêng.

---

# 469.25 — Embedded resources

Resource có thể được embed trực tiếp vào native artifact:

```text
binary
 ├── code
 ├── data
 └── embedded resources
```

---

## 469.26 — Embedded lookup

Embedded resource được locate bằng logical `ResourceId`.

---

## 469.27 — Alignment

Embedded resource có alignment metadata.

---

## 469.28 — Read-only embedded data

Immutable resources có thể được map/read trực tiếp nếu target hỗ trợ.

---

## 469.29 — Zero-copy embedded resource

Nếu representation tương thích, loader có thể trả view trực tiếp vào embedded bytes.

---

# 469.30 — External resources

Resource có thể nằm ngoài executable/package.

---

## 469.31 — External path resolution

Path resolution phải dùng package/resource root, không nối string tùy tiện.

---

## 469.32 — Relative resource

Relative asset references được resolve từ resource namespace/package context.

---

## 469.33 — Resource search path

Search paths phải explicit và deterministic.

---

# 469.34 — Resource bundles

Bundle:

```text
Bundle {
    manifest
    index
    payloads
}
```

---

## 469.35 — Bundle index

Index map:

```text
ResourceId → offset,size,type,flags
```

---

## 469.36 — Bundle random access

Bundle hỗ trợ random-access resource lookup khi format cho phép.

---

## 469.37 — Bundle streaming

Large resources có thể stream trực tiếp từ bundle.

---

## 469.38 — Bundle compression

Compression metadata:

```text
None
Deflate
Zstd
LZ4
platform-specific
```

Provider có thể mở rộng.

---

## 469.39 — Compression tradeoff

Build system có thể chọn compression theo:

```textsize
startup
CPU
random-access
streaming
```

Không có một compression mode bắt buộc cho mọi target.

---

# 469.40 — Resource manifest

Manifest chứa:

```text resource ID
type
version
hash
size
compression
dependencies
platform
locale
```

---

## 469.41 — Content hash

Resource có content hash để:

- cache;
- reproducible builds;
- integrity;
- incremental packaging.

---

## 469.42 — Resource version

Logical version và content hash là hai khái niệm khác nhau.

---

# 469.43 — Resource compiler

Resource compiler có thể:

```textimport
validate
convert
compress
optimize
package
```

---

## 469.44 — Import pipeline

Ví dụ:

```text PNG
 ↓
validate
 ↓
optional conversion
 ↓
Axiom image resource
```

---

## 469.45 — Build-time preprocessing

Asset processing xảy ra build phase, không phải comptime mặc định.

---

## 469.46 — Comptime boundary

431 comptime không được tự ý đọc filesystem.

Resource build tools có thể là explicit build tools.

---

# 469.47 — Image resources

Image metadata:

```textwidth
height
format
color space
alpha
mip levels
compression
```

---

## 469.48 — Image zero-copy

Decoded image có thể expose CPU view nếu layout phù hợp.

---

## 469.49 — GPU texture

Image có thể upload thành GPU texture thông qua 459/460.

---

## 469.50 — Texture lifecycle

GPU representation có lifetime độc lập với source resource bytes.

---

# 469.51 — Font resources

Font resources tích hợp 464.

---

## 469.52 — Font loading

Font bytes có thể được loaded lazy.

---

## 469.53 — Font cache

Font cache có thể share decoded face data nhưng phải tôn trọng resource lifetime.

---

# 469.54 — Shader resources

Shader resource:

```text source
intermediate representation
compiled target binary
reflection metadata
```

---

## 469.55 — Shader target

Shader binary target-specific:

```text SPIR-V
DXIL
Metal representation
other platform format
```

---

## 469.56 — Shader fallback

Package có thể chứa nhiều compiled variants.

---

## 469.57 — Shader compilation

Runtime compilation là optional.

Build-time compilation được ưu tiên cho deterministic startup.

---

# 469.58 — Audio resources

Audio asset có thể tồn tại dưới dạng:

```text encoded
compressed
decoded PCM
stream descriptor
```

---

## 469.59 — Audio streaming

Long audio không cần decode toàn bộ.

Tích hợp 461.

---

# 469.60 — Video resources

Video asset có thể là container/encoded stream.

Không mặc định decode toàn bộ thành frames.

Tích hợp 462.

---

# 469.61 — Model resources

3D model có thể tham chiếu:

```text mesh
material
texture
animation
skeleton
```

---

## 469.62 — Model streaming

Large models hỗ trợ progressive/streaming loading.

---

# 469.63 — Localization resources

Localization resource:

```text language
catalog
messages
plural rules
format data
```

tích hợp 464.

---

## 469.64 — Locale fallback

Fallback chain phải deterministic.

---

## 469.65 — Resource locale selection

Resource loader có thể chọn:

```text vi-VN
vi
default
```

theo explicit fallback policy.

---

# 469.66 — Resource overrides

Development build có thể override packaged resource bằng external resource.

Release build có thể disable override.

---

## 469.67 — Hot reload

Development environment hỗ trợ resource hot reload.

---

## 469.68 — Hot reload safety

Hot reload không được invalidate live resource references.

Có thể:

```textnew version
→ publish
→ old version retained until no users
```

---

## 469.69 — Resource generations

Resource cache có thể dùng generation IDs để theo dõi versions.

---

# 469.70 — Resource ownership

Decoded resource có explicit ownership.

---

## 469.71 — Resource destruction

Resource destruction deterministic khi last owning reference/handle release theo abstraction được chọn.

---

## 469.72 — GPU destruction

GPU resource destruction có thể defer tới GPU synchronization point.

---

## 469.73 — Audio destruction

Audio resources phải không phá realtime callback semantics của 461.

---

# 469.74 — Memory mapping

Bundle/external resource có thể mmap qua 455.

---

## 469.75 — Mapping lifetime

Mapped bytes phải sống lâu hơn mọi view sử dụng chúng.

---

## 469.76 — Executable mapping

Executable resource mapping là unsafe và chịu 445.

---

# 469.77 — Resource streaming

Streaming API:

```text
open
read
seek?
close
```

với seek capability explicit.

---

## 469.78 — Sequential resources

Resource có thể chỉ hỗ trợ sequential access.

---

## 469.79 — Random-access capability

Consumer phải query capability trước khi seek.

---

## 469.80 — Backpressure

Streaming resource loader tích hợp 424 backpressure.

---

# 469.81 — Security

Resource files là untrusted nếu đến từ bên ngoài package trust boundary.

---

## 469.82 — Resource parser

Parser phải kiểm tra:

```textsize
offset
alignment
count
nesting
```

---

## 469.83 — Decompression limits

Compressed resources phải có giới hạn:

```textcompressed_size
expanded_size
ratio
CPU time
```

---

## 469.84 — Resource exhaustion

Loader phải chống memory/CPU exhaustion.

---

## 469.85 — Path traversal

Resource package không được phép escape resource root qua:

```text ../
absolute paths
device paths
```

khi format có filesystem references.

---

## 469.86 — Symlink policy

Symlink traversal phải là explicit platform policy.

---

## 469.87 — Package integrity

Package có thể có:

```text hash
signature
provenance
```

từ 447/445.

---

# 469.88 — Platform packaging

Platform package layer có thể generate:

```textWindows package id="j2k5m8"
macOS bundle
iOS app bundle
Android APK/AAB
WASM/web package
Linux package
```

---

## 469.89 — Platform resources

Platform-specific resources có conditional selection:

```text target.os
target.arch
target.environment
```

---

## 469.90 — Resource variants

Một logical resource có thể có nhiều target-specific implementations.

---

# 469.91 — Build graph

Resource compiler là node trong 432 build graph.

```text
source asset
 ↓
resource compiler
 ↓
bundle
 ↓
native artifact
```

---

## 469.92 — Incremental assets

Không rebuild resource nếu input content/dependencies không thay đổi.

---

## 469.93 — Deterministic bundle

Bundle output phải reproducible khi deterministic mode bật.

---

## 469.94 — Bundle ordering

Resource ordering phải deterministic.

---

# 469.95 — Application lifecycle

468 có thể request resource preload:

```text id="preload"
startup
window activation
scene activation
```

---

## 469.96 — Suspend

Application suspend có thể release reloadable resource caches.

---

## 469.97 — Resume

Resource handles phải có defined behavior khi underlying GPU/device resources đã bị invalidated.

---

# 469.98 — AI metadata

446 expose:

```text resource graph
resource size
dependencies
load state
cache state
memory cost
GPU cost
source
hash
platform variant
```

---

## 469.99 — Explain resource loading

AI tooling có thể trả lời:

```text
Why is resource X slow to load?
```

với structured causes:

```text
decode
decompression
disk IO
network
GPU upload
dependency chain
cache miss
```

---

# 469.100 — Testing

Test:

```text lookup
bundle
embedding
compression
lazy loading
async loading
streaming
mmap
cache
eviction
hot reload
localization
GPU upload
audio loading
video loading
model loading
```

---

## 469.101 — Fuzzing

Fuzz:

```text bundle headers
resource indexes
compression metadata
image parsers
font loaders
shader metadata
model metadata
```

---

## 469.102 — Corruption tests

Test truncated/corrupted bundle/resource.

Loader phải fail an toàn.

---

## 469.103 — Performance tests

Measure:

```text startup
lookup latency
decode latency
throughput
memory
cache hit/miss
GPU upload
streaming
```

---

# 469.104 — Hard invariants

1. Resource identity khác filesystem path.
2. Resource identity khác memory address.
3. Resource identity khác package identity.
4. Resource identity khác URL.
5. Resource type explicit.
6. Resource metadata machine-readable.
7. Resource dependencies tạo graph.
8. Invalid dependency cycles được phát hiện.
9. Lazy dependencies được hỗ trợ.
10. Loading state explicit.
11. Async loading được hỗ trợ.
12. Blocking loading phải explicit.
13. Resource handle không đồng nghĩa loaded bytes.
14. Resource lifetime tuân ownership model.
15. Cache không phải source of truth.
16. Cache eviction không làm mất source.
17. Memory budget có thể cấu hình.
18. GPU budget có thể tách riêng.
19. Embedded resources được hỗ trợ.
20. External resources được hỗ trợ.
21. Embedded data có thể zero-copy.
22. Alignment của embedded resources explicit.
23. External resource path không được tùy tiện concatenate.
24. Resource search path deterministic.
25. Resource bundle có manifest/index.
26. Bundle random access được hỗ trợ.
27. Bundle streaming được hỗ trợ.
28. Compression là optional.
29. Compression limits phải explicit.
30. Resource content hash hỗ trợ caching.
31. Resource version khác content hash.
32. Resource compiler tích hợp build graph.
33. Asset preprocessing không phải comptime mặc định.
34. Resource compiler có thể validate assets.
35. Image metadata đầy đủ.
36. Font resource tích hợp 464.
37. Shader resource hỗ trợ target variants.
38. Audio resource tích hợp 461.
39. Video resource tích hợp 462.
40. Model resource hỗ trợ dependency graph.
41. Localization tích hợp 464.
42. Locale fallback deterministic.
43. Development override có thể bật.
44. Release có thể disable override.
45. Hot reload không tạo dangling references.
46. Resource generation có thể được theo dõi.
47. GPU destruction tôn synchronization.
48. Audio destruction không phá realtime guarantees.
49. mmap resource được hỗ trợ.
50. mmap lifetime phải explicit.
51. Executable mapping là unsafe.
52. Streaming có capability model.
53. Seek không được giả định.
54. Backpressure tích hợp 424.
55. External resources là untrusted.
56. Resource parsers có bounds checking.
57. Decompression bomb được chống.
58. Path traversal được chống.
59. Package integrity có thể verify.
60. Package provenance tích hợp 447.
61. Platform packaging là layer riêng.
62. Target-specific resource variants được hỗ trợ.
63. Resource build là incremental.
64. Resource bundles có thể reproducible.
65. Application lifecycle có thể preload resources.
66. Suspend có thể release caches.
67. Resume có defined reload behavior.
68. AI có thể query resource graph.
69. AI có thể query resource cost.
70. AI có thể explain loading failures.
71. Resource system có fuzz tests.
72. Resource corruption có safe failure.
73. Resource performance có benchmark.
74. Resource system không yêu cầu GUI.
75. Resource system không yêu cầu GPU.
76. Resource system không yêu cầu audio.
77. Resource system không yêu cầu media.
78. Resource system không yêu cầu database.
79. Resource system không yêu cầu GC.
80. Resource system không yêu cầu borrow checker.
81. Resource system không tạo hidden threads.
82. Resource system không tạo hidden allocations ngoài loader contract.
83. Resource loader không tự execute arbitrary resource content.
84. Resource parsers có resource limits.
85. Resource metadata tích hợp 446.
86. Resource packaging tích hợp 432/447.
87. Native artifacts vẫn có thể embed resource trực tiếp.
88. Freestanding applications có thể bỏ toàn bộ resource subsystem.
89. **Axiom resource foundation phải biến assets thành các resource có identity, dependency, version, lifetime và loading semantics rõ ràng, đồng thời hỗ trợ embedded, external, lazy, streaming, mmap, zero-copy và target-specific packaging mà không áp đặt một runtime asset system nặng lên mọi chương trình.**

**BOOTSTRAP-469 hoàn tất.**

---

# BOOTSTRAP-470 — CONFIGURATION, SETTINGS, PREFERENCES, ENVIRONMENT, FEATURE FLAGS & RUNTIME POLICY SYSTEM

470 tách hoàn toàn **configuration/policy** khỏi application lifecycle 468 và package metadata 447.

Kiến trúc:

```text
Defaults
   │
   ├── System Config
   ├── User Preferences
   ├── Project Config
   ├── Environment
   ├── Command Line
   └── Session Override
             ↓
       Configuration Resolver
             ↓
        Typed Configuration
             ↓
 ┌───────────┼────────────┐
 ↓           ↓            ↓
Runtime    Library       Application
Policy     Policy        Behavior
```

Các phân biệt bắt buộc:

```text
Configuration
    ≠ Preference
    ≠ Environment
    ≠ Secret
    ≠ Feature Flag
    ≠ Session Override
    ≠ Compile-time Option
    ≠ Runtime Policy
```

470 sẽ khóa:

- typed configuration schema;
- defaults;
- precedence;
- immutable snapshots;
- dynamic configuration;
- environment variables;
- command-line overrides;
- project/user/system configuration;
- feature flags;
- compile-time features vs runtime flags;
- configuration validation;
- schema migration;
- configuration watching;
- atomic updates;
- persistence;
- secret references;
- secure storage boundary;
- platform configuration directories;
- deployment configuration;
- debug/release configuration;
- capability policies;
- runtime policies;
- network/storage/audio/GPU policies;
- allocator/runtime policies;
- logging levels;
- diagnostics policy;
- deterministic configuration resolution;
- reproducibility;
- AI-readable provenance;
- configuration diff/explain;
- configuration testing;
- sandbox/security;
- no hidden global mutable configuration;
- no configuration-dependent semantic ambiguity in the language/compiler.

Đặc biệt:

```text
Compile-time configuration
        ≠
Build feature
        ≠
Runtime configuration
        ≠
User preference
```

và mọi giá trị configuration cuối cùng phải có thể truy ra **nguồn gốc + schema + effective value**, để compiler, debugger và AI tooling có thể giải thích tại sao chương trình đang chạy với một policy cụ thể.