# BOOTSTRAP-468 — APPLICATION LIFECYCLE, WINDOW/SESSION STATE, CONFIGURATION, PERSISTENCE & STATE RESTORATION

**Trạng thái: COMPLETED / LOCKED**

468 định nghĩa application lifecycle dùng chung cho desktop, mobile, WASM, editor, IDE và game mà không tạo một application runtime bắt buộc.

Nguyên tắc:

```text id="1p0q2r"
Process Lifetime
      ≠
Application Lifetime
      ≠
Window Lifetime
      ≠
Session Lifetime
      ≠
Persistent State Lifetime
```

và:

```text id="m8r4s1"
Configuration
      ≠
User Preference
      ≠
Session State
      ≠
Cache
      ≠
Secret
```

---

## 468.1 — Application identity

Mỗi application/package có:

```text id="8b2xqk"
ApplicationId
PackageId
Version
BuildId
```

`ApplicationId` là identity logical, không phải process ID.

---

## 468.2 — Process identity

Mỗi process có:

```text id="0k3t9f"
ProcessId
StartTime
ParentProcessId?
```

Process identity thuộc platform/runtime.

---

## 468.3 — Application object

Conceptual:

```text id="5m9q2d"
Application {
    identity
    lifecycle
    windows
    activation
    configuration
    state
}
```

---

## 468.4 — Startup

Lifecycle cơ bản:

```text id="v8c2l1"
Created
   ↓
Initializing
   ↓
Ready
```

---

## 468.5 — Activation

Application có thể được activate bởi:

```text id="q7n4xa"
launcher
file
URI
notification
another instance
OS
user action
```

---

## 468.6 — Activation payload

Activation event có typed payload:

```text id="4x8m2p"
Launch
OpenFile
OpenUri
Command
Notification
RestoreSession
```

---

## 468.7 — Multiple activation

Application đang chạy có thể nhận activation mới mà không cần tạo process mới.

---

# 468.8 — Window lifecycle

Window:

```text id="e3v6k2"
Created
Shown
Active
Inactive
Hidden
Closing
Closed
```

---

## 468.9 — Window identity

Mỗi window có stable `WindowId` trong lifecycle của window.

---

## 468.10 — Window state

Có thể query:

```text id="s2c8m4"
position
size
scale
state
monitor
visibility
```

---

## 468.11 — Window state

Platform states có thể gồm:

```text id="u1n5r7"
Normal
Minimized
Maximized
Fullscreen
Hidden
```

---

## 468.12 — Window activation

Window activation khác application activation.

---

## 468.13 — Window close

Close request có thể bị application từ chối nếu cần save state.

---

## 468.14 — Forced close

OS/user có thể force terminate; application không được giả định luôn có cơ hội cleanup.

---

# 468.15 — Dirty state

Document/application có thể đánh dấu:

```text id="p3f7w2"
clean
dirty
```

---

## 468.16 — Save request

Lifecycle có thể phát:

```text id="k9d1v4"
SaveRequested
```

---

## 468.17 — Save result

Save có:

```text id="a5m8c3"
Saved
Cancelled
Failed
```

---

## 468.18 — Graceful shutdown

Shutdown:

```text id="j2r7n5"
request
→ save
→ close windows
→ release resources
→ exit
```

---

## 468.19 — Cleanup

Cleanup tuân 423:

```text ownership
move
drop
defer
```

Không cần một GC shutdown pass.

---

# 468.20 — Suspend

Mobile/OS có thể chuyển application sang:

```text id="b4k8s2"
Suspending
Suspended
```

---

## 468.21 — Resume

```text id="n6q1x8"
Resuming
Resumed
```

---

## 468.22 — Background

Application có thể chuyển background mà process vẫn tồn tại.

---

## 468.23 — Foreground

Foreground transition không đồng nghĩa process creation.

---

## 468.24 — Resource pressure

OS có thể báo resource pressure trước khi termination.

---

## 468.25 — Memory pressure

Application có thể giải phóng cache/nonessential memory.

Cache không được nhầm với persistent state.

---

# 468.26 — Mobile lifecycle

Mobile adapter có thể expose:

```text id="r8c3p1"
Launch
Foreground
Background
Suspend
Resume
Terminate
```

---

## 468.27 — No shutdown guarantee

Application phải luôn giả định termination có thể xảy ra mà không có graceful shutdown.

---

## 468.28 — Persistent state

State cần phục hồi phải được ghi trước khi có nguy cơ termination.

---

# 468.29 — Session

Session đại diện một logical user/application session.

---

## 468.30 — Session state

Ví dụ:

```text id="c7v2m9"
open documents
window geometry
navigation position
selected workspace
active tab
```

---

## 468.31 — Session state ≠ application data

Session state có thể bị xóa mà không làm mất user documents.

---

## 468.32 — Restore

Application có thể khôi phục session state khi startup.

---

## 468.33 — Partial restore

Nếu một resource không còn tồn tại, restore phải có thể bỏ qua riêng resource đó thay vì fail toàn bộ session.

---

# 468.34 — Configuration

Configuration có thể đến từ:

```text id="f2k6r9"
built-in defaults
system
user
environment
command line
project
session
```

---

## 468.35 — Configuration precedence

Precedence phải deterministic và được khai báo.

---

## 468.36 — Configuration schema

Configuration có schema/version.

---

## 468.37 — Invalid configuration

Invalid config phải tạo diagnostic rõ ràng.

Không silently dùng giá trị nguy hiểm/khác nghĩa.

---

## 468.38 — User preferences

Preferences là user-facing configuration:

```text id="y5m1q8"
theme
language
font size
input settings
accessibility preferences
```

---

## 468.39 — Cache

Cache có thể bị xóa bất kỳ lúc nào.

Application không được coi cache là authoritative state.

---

## 468.40 — Secrets

Secrets không được lưu cùng plain configuration nếu platform secure storage tồn tại.

---

# 468.41 — Application directories

Platform layer cung cấp logical directories:

```text id="w7n2c5"
config
data
cache
state
temp
```

---

## 468.42 — Directory semantics

Mỗi directory có retention/backup semantics khác nhau.

---

## 468.43 — Portable applications

Application có thể request portable configuration/data mode.

---

## 468.44 — Environment

Environment variables là external input và phải được parse/validate.

---

# 468.45 — Command-line arguments

Startup có:

```text id="h3q9v1"
args: []StringView
```

hoặc equivalent.

---

## 468.46 — Command-line parsing

CLI parser là library, không phải compiler primitive.

---

## 468.47 — Deep links

URI activation:

```text id="t6p2w8"
axiomapp://...
https://...
```

được chuyển thành activation payload.

---

## 468.48 — File activation

OS có thể launch/activate application với file paths/URIs.

---

## 468.49 — Protocol registration

Protocol/file association thuộc package/platform metadata.

---

# 468.50 — Single-instance policy

Application có thể chọn:

```text id="q4m7s2"
multi-instance
single-instance
single-instance-per-user
single-instance-per-workspace
```

---

## 468.51 — Instance coordination

Single-instance implementation dùng OS IPC/locking.

Không dùng global memory hack.

---

## 468.52 — Secondary activation

Instance mới có thể chuyển activation payload tới primary instance.

---

## 468.53 — Activation failure

Nếu primary instance không thể nhận request → explicit failure.

---

# 468.54 — Autosave

Autosave là application/library feature.

Không tự động bật cho mọi application.

---

## 468.55 — Atomic state update

Persistent state nên ghi:

```text id="k8v3m6"
temporary
→ flush
→ atomic replace
```

khi platform hỗ trợ.

---

## 468.56 — Crash consistency

State storage phải tránh để crash tạo một state file hợp lệ về syntax nhưng sai logic.

---

## 468.57 — Versioning

Persistent state có schema version.

---

## 468.58 — Migration

Migration:

```text id="n2r7c4"
old version
→ validate
→ migrate
→ validate
→ commit
```

---

## 468.59 — Migration failure

Migration failure không được silently destroy original state.

---

## 468.60 — Backup

Important state có thể giữ previous version/backup.

---

# 468.61 — State corruption

Corrupt state phải tạo explicit diagnostic.

---

## 468.62 — Recovery

Recovery options:

```text id="b6p1x9"
restore backup
reset session
skip component
reset preferences
```

---

## 468.63 — State isolation

Một component không được tùy tiện overwrite state của component khác.

---

# 468.64 — Window persistence

Có thể persist:

```text id="u4k8m2"
window size
position
monitor
maximized
fullscreen
```

---

## 468.65 — Monitor disappearance

Nếu monitor không còn tồn tại, window phải được đưa về safe/default display.

---

## 468.66 — DPI change

Window restore phải tính đến scale/DPI thay đổi.

---

## 468.67 — Orientation change

Mobile restore phải xử lý orientation khác session trước.

---

# 468.68 — Background tasks

Background task phải explicit.

Không tự động tạo thread chỉ vì application background.

---

## 468.69 — Lifecycle cancellation

OS lifecycle cancellation phải tích hợp 424 cancellation.

---

## 468.70 — Resource release

Suspend có thể yêu cầu release:

```text id="x7m2q9"
GPU resources
audio devices
network sockets
large caches
```

theo application policy.

---

# 468.71 — GUI integration

468 tích hợp 452:

```text Application
   ↓
Window
   ↓
GUI tree
```

---

## 468.72 — Input integration

465 activation/focus/input events có thể trigger lifecycle transitions.

---

## 468.73 — Accessibility

466 có thể thông báo lifecycle state changes cho assistive technology.

---

## 468.74 — Media

461/462 resources phải có lifecycle-aware release/resume semantics.

---

## 468.75 — GPU

459/460 GPU contexts/resources không được giả định survive suspend.

---

# 468.76 — WASM

WASM application lifecycle có thể phụ thuộc browser:

```text id="z5c2n8"
page load
visibility change
focus
background
unload
```

Không được giả định `process exit` tồn tại.

---

## 468.77 — Browser persistence

Có thể dùng:

```text id="p8r4w1"
IndexedDB
local storage
browser file APIs
```

thông qua platform libraries, không đưa browser APIs vào core.

---

# 468.78 — Error handling

Lifecycle callbacks trả `Result` khi failure có thể recover.

Panic không được dùng làm ordinary lifecycle control flow.

---

## 468.79 — Shutdown timeout

Platform may impose shutdown deadline.

Application không được phụ thuộc vô hạn cleanup.

---

## 468.80 — Forced termination

Forced termination có thể bỏ qua destructors.

Persistent critical state phải được commit trước đó.

---

# 468.81 — Testing

Lifecycle test matrix:

```text id="k2m8v5"
startup
activation
multiple activation
window creation
close
cancel close
save
suspend
resume
background
foreground
crash
restore
migration
corrupt state
multi-instance
DPI
monitor removal
```

---

## 468.82 — Crash testing

Test terminate application tại các điểm khác nhau trong persistence transaction.

---

## 468.83 — Migration testing

Mỗi supported schema version phải có migration test.

---

## 468.84 — Determinism

Configuration resolution và state migration phải deterministic.

---

# 468.85 — Security

Configuration và activation data là external input.

---

## 468.86 — URI validation

Deep links phải validate scheme, host, path, query và payload.

---

## 468.87 — File validation

Activated file paths không được mặc định trusted.

---

## 468.88 — Secret handling

Không log:

```text id="7q1m5c"
password
token
credential
secret configuration
```

mặc định.

---

## 468.89 — Sandbox

Application sandbox permissions vẫn do platform quyết định.

---

# 468.90 — AI metadata

446 có thể expose:

```text id="n4x8s2"
application lifecycle
windows
activation
configuration source
state schema
migration
dirty resources
pending save
```

---

## 468.91 — Explain configuration

AI tooling có thể trả lời:

```text
Why does this setting have this value?
```

với source:

```text id="j6r2v9"
default
system
user
environment
project
command line
session
```

---

## 468.92 — Explain restore failure

Có thể truy vấn:

```text id="c5m9w3"
resource_missing
schema_mismatch
corrupt_state
permission_denied
migration_failed
```

---

# 468.93 — Performance

Lifecycle system phải không tạo overhead cho applications không sử dụng persistence/windowing.

---

## 468.94 — Lazy state

State component có thể được load lazy.

---

## 468.95 — Incremental persistence

Large application state có thể persist incremental.

---

## 468.96 — No mandatory database

Application state không yêu cầu database.

---

## 468.97 — Storage integration

468 có thể sử dụng 455 atomic file/storage primitives.

---

# 468.98 — Hard invariants

1. Process lifetime khác application lifetime.
2. Application lifetime khác window lifetime.
3. Session lifetime khác persistent state lifetime.
4. Configuration khác preference.
5. Preference khác session state.
6. Session state khác cache.
7. Cache khác secret.
8. Application có stable logical identity.
9. Process có runtime identity riêng.
10. Activation là typed event.
11. Multiple activation được hỗ trợ.
12. Window lifecycle explicit.
13. Window close có thể bị từ chối.
14. Forced termination không được giả định cleanup.
15. Dirty state explicit.
16. Save operation có Result.
17. Graceful shutdown có lifecycle.
18. Suspend/resume được hỗ trợ.
19. Background/foreground khác process creation.
20. Resource pressure được biểu diễn.
21. Persistent critical state không phụ thuộc shutdown callback.
22. Session state có thể partial restore.
23. Configuration precedence deterministic.
24. Configuration có schema.
25. Invalid configuration tạo diagnostic.
26. Cache không được coi là authoritative.
27. Secrets có storage boundary riêng.
28. Config/data/cache/state/temp directories có semantics khác nhau.
29. Environment là external input.
30. CLI arguments là external input.
31. Deep links là external input.
32. File activation là external input.
33. Single-instance là explicit policy.
34. Instance coordination dùng IPC/OS primitives.
35. Secondary activation có thể chuyển tới primary.
36. Autosave không bắt buộc.
37. State writes có thể atomic.
38. State migration có version.
39. Migration không được destroy original state khi thất bại.
40. Corrupt state có recovery path.
41. Window geometry có thể persist.
42. Monitor disappearance được xử lý.
43. DPI changes được xử lý.
44. Mobile lifecycle không giả định desktop process semantics.
45. WASM lifecycle không giả định process exit.
46. Background tasks không tự động tạo thread.
47. Lifecycle cancellation tích hợp 424.
48. GPU resources không được giả định survive suspend.
49. Audio resources không được giả định survive suspend.
50. Network resources có explicit lifecycle.
51. Lifecycle callbacks không dùng panic làm ordinary control flow.
52. Shutdown deadlines được hỗ trợ.
53. URI activation được validate.
54. Activated files được coi là untrusted.
55. Secrets không log mặc định.
56. Sandbox không bị bypass.
57. Lifecycle metadata tích hợp 446.
58. Configuration provenance có thể inspect.
59. Restore failures có machine-readable reasons.
60. Lifecycle testing gồm crash/recovery.
61. Migration testing bắt buộc.
62. Lifecycle resolution deterministic.
63. State persistence không bắt buộc database.
64. State có thể dùng 455 storage.
65. Application lifecycle không thuộc language core.
66. Không mandatory application framework.
67. Không mandatory GUI.
68. Không mandatory persistence.
69. Không mandatory runtime thread.
70. Không mandatory GC.
71. Ownership tuân 423.
72. Errors tuân 425.
73. Native applications vẫn có thể chạy freestanding.
74. Lifecycle APIs có thể bị loại khỏi executable nếu không dùng.
75. **Axiom application lifecycle phải cung cấp một contract nhất quán cho desktop, mobile và WASM, đồng thời giữ process, window, session, configuration, cache và persistent state thành các khái niệm độc lập, có semantics rõ ràng và không tạo hidden runtime machinery.**

**BOOTSTRAP-468 hoàn tất.**

---

# BOOTSTRAP-469 — RESOURCE SYSTEM, ASSETS, BUNDLES, APPLICATION PACKAGING & RUNTIME RESOURCE LOADING

469 tiếp tục từ lifecycle 468 sang **resource/asset layer** — rất quan trọng cho GUI, game, media, localization, fonts, shaders, models và native applications.

Kiến trúc:

```text id="z1a7f4"
Source / Generated Assets
          ↓
     Resource Graph
          ↓
   Resource Compiler
          ↓
      Asset Bundle
          ↓
 ┌────────┼───────────┐
 ↓        ↓           ↓
Native   Embedded    External
File     Resource    Resource
 └────────┼───────────┘
          ↓
     Runtime Loader
          ↓
 Resource Cache / Stream
```

469 sẽ khóa:

- resource identity;
- asset URI/path;
- embedded resources;
- external resources;
- resource bundles;
- manifest;
- MIME/type;
- localization resources;
- font resources;
- shader resources;
- images/audio/video/models;
- compressed resources;
- alignment;
- memory mapping;
- zero-copy loading;
- streaming resources;
- lazy loading;
- asynchronous loading;
- resource dependency graph;
- resource version/hash;
- cache;
- hot reload;
- development vs release assets;
- platform-specific resources;
- Windows/Apple/Android/WASM packaging;
- executable embedding;
- static/dynamic resource libraries;
- resource signing/provenance;
- sandbox;
- path traversal;
- decompression bombs/resource exhaustion;
- memory ownership;
- GPU upload;
- audio upload;
- media integration;
- localization 464;
- lifecycle 468;
- package model 447;
- AI-readable resource graph.

Đặc biệt sẽ phân biệt:

```text id="m5q2k8"
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

```text id="v7n3c1"
Asset on disk
      ↓
Logical Resource
      ↓
Loaded Resource
      ↓
GPU/Audio/Media representation
```

Resource loader không được mặc định load toàn bộ assets vào RAM; resource phải hỗ trợ **lazy loading, streaming, memory mapping và zero-copy khi representation/lifetime cho phép**.