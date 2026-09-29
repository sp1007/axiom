# BOOTSTRAP-467 — CLIPBOARD, DRAG & DROP, SELECTION, COPY/PASTE, DATA TRANSFER & INTER-APPLICATION INTERACTION

**Trạng thái: COMPLETED / LOCKED**

467 định nghĩa nền tảng trao đổi dữ liệu giữa Axiom application, GUI, OS và application khác.

Nguyên tắc:

```text
Application Data
      ↓
Transfer Provider
      ↓
Representation Negotiation
      ↓
Clipboard / Drag & Drop / Selection
      ↓
Platform
      ↓
Other Application
```

Và:

```text
Clipboard Payload
    ≠ Memory Pointer
    ≠ Serialized Object
    ≠ File Path
```

Một object có thể cung cấp nhiều representation:

```text
Document
 ├── UTF-8 text
 ├── HTML
 ├── RTF
 ├── image
 ├── binary
 └── file/URI list
```

---

## 467.1 — Transfer model

Core abstraction:

```text
TransferOffer {
    formats
    operations
    source
    capabilities
}
```

Consumer chọn format phù hợp.

---

## 467.2 — Transfer format

Format được nhận diện bằng canonical MIME/type identifier.

Ví dụ:

```text
text/plain
text/html
image/png
application/octet-stream
```

---

## 467.3 — Multiple representations

Một payload có thể đồng thời cung cấp nhiều representation.

---

## 467.4 — Preferred representation

Consumer có thể đưa ra danh sách preference.

Provider chọn representation tương thích.

---

## 467.5 — Lazy rendering

Representation lớn có thể được tạo lazy khi consumer thực sự yêu cầu.

---

## 467.6 — Deferred transfer

Clipboard/drag source không bắt buộc serialize toàn bộ dữ liệu ngay tại thời điểm copy/drag.

---

## 467.7 — Transfer lifetime

Provider phải giữ dữ liệu đủ lâu theo platform contract.

Không được trả về pointer tới object đã destroyed.

---

# 467.8 — Clipboard

Clipboard là OS/application-mediated transfer channel.

---

## 467.9 — Clipboard ownership

Clipboard có owner/provider logic.

Ownership semantics không đồng nghĩa với Axiom memory ownership.

---

## 467.10 — Clipboard set

API concept:

```text
clipboard.set(offer)
clipboard.get()
clipboard.clear()
```

---

## 467.11 — Clipboard read

Consumer query available formats trước khi request payload.

---

## 467.12 — Clipboard change

Applications có thể subscribe clipboard-change notification khi platform hỗ trợ.

---

## 467.13 — Plain text

`text/plain` sử dụng UTF-8 ở Axiom boundary.

---

## 467.14 — Rich text

Rich text representation có thể dùng HTML/RTF hoặc ecosystem-specific formats.

---

## 467.15 — Image

Clipboard có thể cung cấp:

```text
image/png
image/jpeg
raw image
```

khi platform hỗ trợ.

---

## 467.16 — File list

File transfer có thể dùng URI/file-list representation.

---

## 467.17 — Binary

Arbitrary binary data có thể được transfer bằng application-specific MIME/type.

---

## 467.18 — Format negotiation

Consumer không được giả định provider luôn hỗ trợ một format cụ thể.

---

# 467.19 — Copy

Copy tạo transfer offer nhưng không xóa source.

---

## 467.20 — Cut

Cut gồm:

```text
copy
+
source removal
```

theo transaction semantics của application.

---

## 467.21 — Paste

Paste chọn representation rồi apply vào target.

---

## 467.22 — Paste failure

Paste trả `Result`, không dùng exception bắt buộc.

---

## 467.23 — Undo integration

Paste/cut nên tích hợp undo transaction của 452/editor layer.

---

# 467.24 — Selection

Selection là semantic range, không đơn thuần là highlighted pixels.

---

## 467.25 — Text selection

Text selection dùng 464 text-position model.

---

## 467.26 — Grapheme-aware selection

UI text selection phải có thể hoạt động theo grapheme cluster.

---

## 467.27 — Multi-selection

Editor có thể hỗ trợ nhiều selection ranges.

---

## 467.28 — Selection direction

Selection có thể giữ anchor/focus để hỗ trợ editing behavior.

---

## 467.29 — Non-text selection

Selection cũng có thể áp dụng cho:

```text
files
list items
table cells
objects
```

---

# 467.30 — Primary selection

Linux/X11-like environments có thể có primary selection riêng clipboard.

---

## 467.31 — Platform selection models

Platform-specific selection mechanisms được adapter hóa, không làm thay đổi core model.

---

# 467.32 — Drag & Drop

Drag lifecycle:

```text
DragBegin
    ↓
DragEnter
    ↓
DragOver*
    ↓
Drop / DragCancel
```

---

## 467.33 — Drag source

Source cung cấp `TransferOffer`.

---

## 467.34 — Drop target

Target khai báo accepted formats/operations.

---

## 467.35 — Operation

Canonical:

```text
Copy
Move
Link
None
```

---

## 467.36 — Negotiation

Target có thể chọn operation phù hợp.

---

## 467.37 — Drag feedback

Target có thể báo:

```text
accepted
rejected
operation
```

---

## 467.38 — Drag preview

Preview/ghost image thuộc GUI layer, không phải transfer core.

---

## 467.39 — Drag cancellation

Drag có thể bị cancel bởi:

```text
source
target
OS
user
window destruction
```

---

## 467.40 — Drop transaction

Drop nên có một logical transaction:

```text
validate
→ transfer
→ commit
```

Nếu thất bại, source không được ở trạng thái half-moved.

---

# 467.41 — File drag/drop

File payload có thể chứa:

```text
URI
native path
display name
metadata
```

---

## 467.42 — URI security

URI không mặc định là local filesystem path.

---

## 467.43 — External file

File từ application khác phải được coi là external/untrusted input.

---

## 467.44 — Temporary files

Large transfers có thể dùng temporary file managed bởi transfer subsystem.

---

## 467.45 — Streaming transfer

Payload lớn có thể transfer streaming thay vì load toàn bộ vào RAM.

---

## 467.46 — Backpressure

Streaming transfer tích hợp với 424 backpressure/cancellation.

---

## 467.47 — Async transfer

Large/network/browser transfers có thể là async.

---

# 467.48 — Cross-process transfer

Transfer không được dựa trên shared pointer.

Các cơ chế có thể là:

```text
OS clipboard
IPC
shared memory
temporary file
stream
```

---

## 467.49 — Zero-copy

Zero-copy được phép khi platform cung cấp shared representation và ownership/lifetime có thể chứng minh.

---

## 467.50 — Serialization

Serialization chỉ được thực hiện khi cần representation đó.

---

## 467.51 — Memory ownership

Transfer buffer có ownership rõ ràng theo 423.

---

# 467.52 — Security boundary

External transfer luôn được coi là untrusted.

---

## 467.53 — Clipboard injection

Application không được coi clipboard text/data là trusted configuration.

---

## 467.54 — Malformed formats

Parser phải validate length, encoding, nesting và resource limits.

---

## 467.55 — MIME confusion

Format identifier phải được kiểm tra cùng payload.

---

## 467.56 — File path traversal

File archives/URI/path transfer phải chống traversal khi application quyết định materialize dữ liệu.

---

## 467.57 — Executable content

Paste/drop dữ liệu executable không tự động execute.

---

## 467.58 — Clipboard privacy

Clipboard có thể chứa password/token/private data.

Application không được logging clipboard contents mặc định.

---

## 467.59 — Sensitive transfer

Transfer offer có thể đánh dấu:

```text
sensitive
```

để hạn chế diagnostics/logging.

---

## 467.60 — Password controls

Password widgets nên disable ordinary clipboard operations hoặc áp dụng platform policy.

---

# 467.61 — Accessibility integration

466 có thể expose:

```text
Copy
Cut
Paste
SelectAll
Drag
Drop
```

như semantic actions.

---

## 467.62 — Input integration

465 cung cấp input events.

467 không trực tiếp phụ thuộc physical keyboard/mouse events.

---

## 467.63 — GUI integration

452 chịu trách nhiệm:

```text
hit testing
drag visuals
selection rendering
focus
```

---

## 467.64 — Text integration

464 chịu trách nhiệm:

```text
Unicode
grapheme
text range
TextBuffer
```

467 chỉ cung cấp transfer semantics.

---

# 467.65 — Browser/WASM

Browser clipboard có thể yêu cầu user permission/gesture.

Axiom API phải phản ánh failure thay vì giả định quyền truy cập.

---

## 467.66 — Browser drag/drop

DOM drag/drop được adapter thành unified transfer model.

---

## 467.67 — Sandboxed application

Sandbox có thể hạn chế clipboard/file transfer.

Axiom không bypass sandbox.

---

# 467.68 — Platform adapters

```text
transfer-core
transfer-windows
transfer-macos
transfer-linux
transfer-android
transfer-ios
transfer-web
```

---

# 467.69 — AI tooling

446 có thể query:

```text
available_formats
selected_format
source
target
operation
transfer_size
security_flags
failure_reason
```

---

## 467.70 — Explain transfer

AI/debugger có thể trả lời:

```text
Why did paste fail?
```

với structured reason như:

```text
format_not_supported
permission_denied
invalid_payload
target_rejected
cancelled
resource_limit
```

---

# 467.71 — Testing

Bắt buộc test:

```text
text
HTML
image
binary
file list
copy
cut
paste
selection
drag
drop
cancel
large payload
async transfer
permission failure
malformed payload
```

---

## 467.72 — Cross-application tests

Test giữa các application/platform adapters khi môi trường cho phép.

---

## 467.73 — Fuzzing

Fuzz:

```text
MIME/type identifiers
payload decoders
HTML/RTF parsers
URI lists
transfer metadata
```

---

## 467.74 — Large payload testing

Kiểm tra payload đủ lớn để phát hiện:

```text
overflow
OOM
blocking
unbounded allocation
```

---

# 467.75 — Performance

Small text transfer có thể hoàn toàn memory-based.

Large objects có thể:

```text
stream
mmap
shared-memory
temporary-file
```

---

## 467.76 — No hidden allocation

Core transfer API không yêu cầu heap allocation nếu caller cung cấp buffer/provider phù hợp.

---

## 467.77 — No hidden threads

Clipboard/drag subsystem không tự tạo thread ngoài platform requirement.

---

## 467.78 — No hidden serialization

Application object không bị serialize nếu consumer không yêu cầu representation đó.

---

# 467.79 — Hard invariants

1. Clipboard không phải memory pointer.
2. Drag payload không phải memory pointer.
3. Transfer có format negotiation.
4. Một payload có thể có nhiều representation.
5. Representation có thể được tạo lazy.
6. Clipboard ownership khác Axiom memory ownership.
7. Text clipboard mặc định UTF-8 ở Axiom boundary.
8. Rich text là representation riêng.
9. Binary transfer được hỗ trợ.
10. Image transfer được hỗ trợ.
11. File/URI transfer được hỗ trợ.
12. Consumer phải kiểm tra format.
13. Provider không được giả định consumer hỗ trợ format.
14. Copy không xóa source.
15. Cut có source-removal semantics.
16. Paste có Result/failure semantics.
17. Selection là semantic range.
18. Text selection tích hợp 464.
19. Grapheme-aware selection được hỗ trợ.
20. Multi-selection có thể được hỗ trợ.
21. Primary selection có thể được platform adapter hỗ trợ.
22. Drag có lifecycle rõ ràng.
23. Drop target có thể reject payload.
24. Operation có Copy/Move/Link.
25. Drag cancellation được hỗ trợ.
26. Drop transaction tránh half-move.
27. Large payload có thể streaming.
28. Streaming hỗ trợ backpressure.
29. Transfer hỗ trợ cancellation.
30. Cross-process transfer không dùng shared pointer.
31. Zero-copy chỉ khi lifetime/ownership hợp lệ.
32. Serialization chỉ khi representation yêu cầu.
33. External data là untrusted.
34. Clipboard không được mặc định trusted.
35. Payload parser phải có resource limits.
36. MIME/type confusion phải được xử lý.
37. File transfer không tự động execute.
38. Path traversal phải được xử lý khi materializing data.
39. Clipboard sensitive data không được log mặc định.
40. Password data có privacy policy.
41. Browser permission failure là explicit.
42. Sandbox không bị bypass.
43. Accessibility actions có thể invoke transfer.
44. Input layer không bị trộn với transfer semantics.
45. GUI chịu trách nhiệm visual drag/selection.
46. Text engine chịu trách nhiệm Unicode semantics.
47. Platform-specific clipboard APIs là adapter.
48. AI có thể inspect transfer decisions.
49. AI có thể inspect transfer failures.
50. Transfer APIs có structured diagnostics.
51. Fuzzing là bắt buộc cho parsers.
52. Large payload stress tests là bắt buộc.
53. Transfer không bắt buộc GUI.
54. Transfer không bắt buộc GPU.
55. Transfer không bắt buộc runtime thread.
56. Transfer không bắt buộc GC.
57. Transfer tuân ownership model 423.
58. Transfer errors tuân failure model 425.
59. Transfer metadata tích hợp 446.
60. **Axiom transfer foundation phải cho phép copy/paste, drag/drop và inter-application data exchange hiệu quả, an toàn và có khả năng streaming mà không biến dữ liệu trao đổi thành một abstraction phụ thuộc GUI hoặc memory layout nội bộ.**

**BOOTSTRAP-467 hoàn tất.**

---

# BOOTSTRAP-468 — APPLICATION LIFECYCLE, WINDOW/SESSION STATE, CONFIGURATION, PERSISTENCE & STATE RESTORATION

468 tiếp tục xây lớp application foundation:

```text
                Axiom Application
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    Lifecycle       Window         State
        │              │              │
        ↓              ↓              ↓
   Startup        Activation    Persistence
   Suspend        Focus         Restore
   Resume         Close         Migration
   Shutdown       Session
        │              │              │
        └──────────────┼──────────────┘
                       ↓
                Platform Adapter
```

Mục tiêu là chuẩn hóa lifecycle cho desktop/mobile/WASM nhưng **không ép một application runtime duy nhất**.

### 468 sẽ khóa các vấn đề:

- application identity;
- process vs application;
- startup/shutdown;
- main entry;
- application initialization;
- activation;
- multiple windows;
- window lifecycle;
- session lifecycle;
- foreground/background;
- suspend/resume;
- mobile lifecycle;
- WASM page lifecycle;
- graceful shutdown;
- forced termination;
- save-before-close;
- dirty state;
- state persistence;
- session restoration;
- crash recovery;
- autosave;
- configuration;
- environment/config precedence;
- command-line arguments;
- application data directories;
- cache directories;
- temporary directories;
- user preferences;
- portable configuration;
- secrets separation;
- schema/version migration;
- atomic state writes;
- corruption recovery;
- concurrent application instances;
- single-instance policy;
- inter-instance activation;
- deep links;
- URI activation;
- file activation;
- protocol registration;
- notification/activation events;
- background execution;
- resource pressure;
- OS termination;
- state size limits;
- privacy;
- sandbox;
- accessibility/GUI/input integration;
- AI-readable lifecycle/state diagnostics.

Đặc biệt sẽ phân biệt:

```text
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

```text
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

Điều này sẽ là nền cho desktop app, mobile app, editor, IDE, game và WASM application mà không kéo một application framework nặng vào mọi executable.