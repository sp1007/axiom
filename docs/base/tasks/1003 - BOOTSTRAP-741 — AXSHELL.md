# BOOTSTRAP-741 — AXSHELL

**Namespace:** `AXSHELL`  
**Phase:** Axiom Civilization Runtime / Native System Shell Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXDESKTOP`, `AXWINDOW`, `AXDISPLAY`, `AXCOMPOSITOR`, `AXUI`, `AXINPUT`, `AXGRAPHICS`, `AXMEDIA`, `AXAUDIO`, `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXSECURITY`, `AXIDENTITY`, `AXAPPLICATION`, `AXASSET`

AXSHELL là tầng **system shell** nằm trên desktop environment. Nếu `AXDESKTOP` quản lý **desktop state**, thì `AXSHELL` quản lý những **điểm tương tác hệ thống dùng chung** mà người dùng có thể gọi từ bất kỳ application nào.

```text
AXAPPLICATION
      │
      ▼
    AXUI
      │
      ▼
  AXWINDOW
      │
      ▼
 AXCOMPOSITOR
      │
      ▼
   AXDISPLAY

AXDESKTOP
      │
      ▼
   AXSHELL
      ├── system menu
      ├── command palette
      ├── global search
      ├── quick settings
      ├── notification center
      ├── system dialogs
      ├── pickers
      ├── clipboard
      ├── drag/drop
      └── shell extensions
```

---

# 741.1 — Mục tiêu

AXSHELL phải cung cấp native infrastructure cho:

```text
system menu
application menu
command palette
global search
quick settings
notification center
system status
context menus
system dialogs
file picker
application picker
color picker
font picker
clipboard
clipboard history
drag-and-drop
system actions
global actions
shell extensions
system notifications
accessibility shell
secure shell surfaces
shell policy
shell state
shell simulation
shell replay
```

AXSHELL **không phải GUI toolkit**.

AXUI vẫn sở hữu:

```text
widgets
layout
controls
text rendering semantics
accessibility primitives
```

AXSHELL sở hữu:

```text
system-wide interaction semantics
```

---

# 741.2 — Strong Boundary

### AXSHELL owns

```text
system-wide menus
system commands
system dialogs
pickers
clipboard coordination
drag/drop coordination
global search
quick settings
notification center
system status aggregation
shell extensions
system-level UI surfaces
```

### AXDESKTOP owns

```text
workspaces
desktop
taskbar
dock
window grouping
window placement
desktop session
```

### AXWINDOW owns

```text
window lifecycle
window geometry
focus
fullscreen
window surface
```

### AXUI owns

```text
widgets
controls
layout
UI rendering semantics
```

### AXSECURITY owns

```text
authentication
authorization
capabilities
secure storage
security policy
```

---

# 741.3 — Shell Root

```axiom
shell_environment {
    id
    desktop_session
    state
    surfaces
    menus
    dialogs
    services
    policies
}
```

---

# 741.4 — Shell Lifecycle

```text
CREATED
   ↓
INITIALIZING
   ↓
READY
   ↓
SUSPENDING
   ↓
SUSPENDED
   ↓
RESUMING
   ↓
READY
   ↓
CLOSING
   ↓
CLOSED
```

---

# 741.5 — Shell Surface

System shell surfaces phải có identity riêng:

```axiom
shell_surface {
    id
    type
    owner
    priority
    security_level
}
```

Không dùng application window identity làm shell identity.

---

# 741.6 — Shell Surface Types

```text
SYSTEM_MENU
COMMAND_PALETTE
SEARCH
QUICK_SETTINGS
NOTIFICATION_CENTER
CONTEXT_MENU
SYSTEM_DIALOG
PICKER
TOOLTIP
OVERLAY
SECURE_SURFACE
```

---

# 741.7 — Shell Surface Priority

```text
NORMAL
ELEVATED
SYSTEM
SECURE
```

Priority không tự động cấp quyền.

---

# 741.8 — Global Action

```axiom
global_action {
    id
    name
    command
    scope
    capability
}
```

Ví dụ:

```text
open_launcher
open_search
open_quick_settings
show_notifications
lock_session
switch_workspace
open_settings
```

---

# 741.9 — Command Palette

Command palette là registry + UI của các system actions.

```axiom
command_palette {
    commands
    search
    recent
    categories
}
```

---

# 741.10 — Command

```axiom
shell_command {
    id
    label
    description
    action
    parameters
    capability
}
```

---

# 741.11 — Command Discovery

Command có thể đến từ:

```text
AXSHELL
AXDESKTOP
AXAPPLICATION
system services
authorized shell extensions
```

Nhưng command registry không đồng nghĩa quyền thực thi.

---

# 741.12 — Command Authorization

Flow:

```text
discover
   ↓
select
   ↓
resolve target
   ↓
authorize
   ↓
execute
   ↓
report result
```

---

# 741.13 — Command Result

```axiom
command_result {
    status
    output
    error
    changed_state
}
```

States:

```text
SUCCESS
REJECTED
DENIED
CANCELLED
FAILED
TIMEOUT
```

---

# 741.14 — Global Search

```axiom
shell_search {
    query
    scope
    filters
    results
}
```

Search sources:

```text
applications
files
settings
commands
windows
workspaces
notifications
system resources
```

---

# 741.15 — Search Provider

```axiom
search_provider {
    id
    scope
    capabilities
    query()
}
```

Provider phải được capability-controlled.

---

# 741.16 — Search Result

```axiom
search_result {
    id
    provider
    title
    subtitle
    icon
    action
    relevance
}
```

`relevance` chỉ là search metadata, không phải security authority.

---

# 741.17 — Search Privacy

Search không được index dữ liệu mà current principal không có quyền đọc.

---

# 741.18 — Search Result Security

Một kết quả có thể tồn tại trong index nhưng không được hiển thị nếu quyền hiện tại không còn hợp lệ.

Do đó:

```text
indexability ≠ visibility ≠ actionability
```

---

# 741.19 — Quick Settings

```axiom
quick_settings {
    controls
    status
    actions
}
```

Có thể điều khiển:

```text
network
audio
display
brightness
power
connectivity
input devices
privacy switches
```

Nhưng mỗi subsystem vẫn giữ authority riêng.

---

# 741.20 — Quick Setting Adapter

Ví dụ:

```text
AXSHELL
   ↓
quick setting
   ↓
AXNETWORK
```

AXSHELL không trực tiếp sửa network hardware state.

---

# 741.21 — System Status

```axiom
system_status {
    network
    audio
    display
    power
    storage
    compute
    security
    time
}
```

Đây là aggregation layer.

---

# 741.22 — Status Ownership

AXSHELL không trở thành source of truth.

Ví dụ:

```text
AXENERGY → energy state
AXNETWORK → network state
AXAUDIO → audio state
AXDISPLAY → display state
AXSTORAGE → storage state
```

AXSHELL chỉ trình bày.

---

# 741.23 — Notification Center

AXDESKTOP quản lý notification lifecycle ở desktop level.

AXSHELL cung cấp:

```text
notification center UI
grouping
filtering
history presentation
actions
```

---

# 741.24 — Notification Group

```axiom
notification_group {
    source
    notifications
    collapsed
}
```

---

# 741.25 — Notification Filtering

```text
all
unread
priority
application
system
security
```

Filter chỉ ảnh hưởng presentation.

---

# 741.26 — Context Menu

```axiom
context_menu {
    target
    items
    groups
}
```

Target có thể là:

```text
window
desktop item
file
application
text selection
system object
```

---

# 741.27 — Context Menu Provider

```axiom
context_provider {
    target_type
    actions
    capabilities
}
```

Provider không được tự động nhận quyền đối với target.

---

# 741.28 — Context Menu Security

Action phải kiểm tra authorization **tại thời điểm thực thi**, không chỉ lúc menu được tạo.

---

# 741.29 — System Dialog

```axiom
system_dialog {
    id
    type
    owner
    modality
    security_level
}
```

---

# 741.30 — Dialog Types

```text
CONFIRMATION
ERROR
WARNING
INFORMATION
AUTHENTICATION_REQUEST
PERMISSION_REQUEST
FILE_PICKER
SAVE_PICKER
OPEN_PICKER
COLOR_PICKER
APPLICATION_PICKER
```

---

# 741.31 — Modal Dialog

Modal relationship:

```text
dialog
   ↓
owner window
```

Dialog không được tự ý block toàn bộ desktop trừ khi system policy yêu cầu.

---

# 741.32 — File Picker

```axiom
file_picker {
    mode
    initial_location
    filters
    permissions
}
```

Modes:

```text
OPEN
SAVE
SELECT_DIRECTORY
```

---

# 741.33 — File Picker Boundary

AXSHELL cung cấp UI/selection semantics.

Actual filesystem authority:

→ `AXSTORAGE` + `AXSECURITY`.

---

# 741.34 — File Selection

```axiom
file_selection {
    uri
    file_id
    capability
}
```

Application nhận capability/reference thay vì shell tự cấp filesystem quyền rộng.

---

# 741.35 — Application Picker

```axiom
application_picker {
    purpose
    accepted_capabilities
    applications
}
```

Dùng cho:

```text
open with
default application
share with
choose handler
```

---

# 741.36 — Default Handler

```axiom
handler_registration {
    resource_type
    application
    priority
}
```

Default handler policy không được bypass security policy.

---

# 741.37 — Clipboard

```axiom
clipboard {
    owner
    formats
    content
    timestamp
}
```

---

# 741.38 — Clipboard Formats

Có thể hỗ trợ:

```text
UTF-8 text
UTF-16 text
rich text
HTML
image
audio
video
file references
custom typed data
```

---

# 741.39 — Clipboard Ownership

Clipboard ownership phải explicit.

```text
application A
      ↓
clipboard
      ↓
application B
```

---

# 741.40 — Clipboard Capability

Sensitive clipboard data có thể yêu cầu:

```text
foreground access
explicit paste
user confirmation
capability
```

---

# 741.41 — Clipboard History

```axiom
clipboard_history {
    entries
    retention
    policy
}
```

Sensitive content có thể bị excluded hoặc expire.

---

# 741.42 — Clipboard Persistence

Clipboard history mặc định không nên đồng nghĩa persistent storage.

Retention phải explicit.

---

# 741.43 — Clipboard Synchronization

Có thể đồng bộ giữa devices:

```text
device A
   ↓
AXNETWORK
   ↓
device B
```

nhưng phải có explicit user/security policy.

---

# 741.44 — Drag and Drop

```axiom
drag_session {
    source
    target
    payload
    effects
    state
}
```

---

# 741.45 — Drag Effects

```text
COPY
MOVE
LINK
NONE
```

---

# 741.46 — Drag Lifecycle

```text
STARTED
DRAGGING
ENTERED_TARGET
OVER_TARGET
LEFT_TARGET
DROPPED
CANCELLED
COMPLETED
```

---

# 741.47 — Drag Security

Target không được nhận quyền source chỉ vì drag operation.

Payload capability phải được explicit.

---

# 741.48 — Cross-Process Drag

Cross-process drag phải dùng secure transferable representation:

```axiom
drag_payload {
    type
    reference
    capability
    expiration
}
```

---

# 741.49 — System Picker Transactions

Picker selection có thể được transactional:

```text
open
   ↓
select
   ↓
validate
   ↓
commit
```

Cancel không làm thay đổi target state.

---

# 741.50 — System Menu

```axiom
system_menu {
    entries
    groups
    shortcuts
    dynamic_items
}
```

Menu có thể chứa:

```text
application actions
system actions
recent items
workspace actions
settings
power actions
```

---

# 741.51 — Application Menu

Application menu có thể được supplied bởi:

```text
AXAPPLICATION
AXUI
```

AXSHELL chỉ quản lý shell integration.

---

# 741.52 — Menu Merge

Application menu có thể merge vào shell menu:

```text
system
+
application
+
context
```

nhưng namespace và capability phải giữ riêng.

---

# 741.53 — Shell Extension

```axiom
shell_extension {
    id
    provider
    surfaces
    capabilities
}
```

---

# 741.54 — Extension Points

```text
search
context menu
file picker
application picker
notification
status item
quick setting
clipboard format
drag/drop
```

---

# 741.55 — Extension Isolation

Extension phải:

```text
sandboxed
capability-limited
versioned
revocable
```

---

# 741.56 — Extension Failure

Một extension crash không được làm crash toàn bộ shell.

```text
extension failure
      ↓
isolate
      ↓
disable/restart
      ↓
shell continues
```

---

# 741.57 — Shell Process Model

AXSHELL có thể triển khai:

```text
single shell process
multi-process shell
isolated extension processes
```

Kiến trúc API không phụ thuộc deployment model.

---

# 741.58 — Shell IPC

Nếu shell component chạy process khác:

```text
AXNETWORK / IPC substrate
```

phải truyền:

```text
typed messages
capabilities
handles
deadlines
cancellation
```

---

# 741.59 — Shell State

Phân biệt:

```text
authoritative state
derived state
presentation state
transient state
```

Ví dụ:

```text
clipboard content
   → authoritative

clipboard preview
   → derived

menu animation
   → transient
```

---

# 741.60 — Shell Persistence

Persist:

```text
recent commands
menu configuration
picker preferences
clipboard history if enabled
shell preferences
extension configuration
```

Không persist secrets mặc định.

---

# 741.61 — Shell Checkpoint

```axiom
shell_checkpoint {
    version
    session
    state
    timestamp
}
```

---

# 741.62 — Crash Recovery

```text
shell crash
   ↓
restart
   ↓
load checkpoint
   ↓
validate against current policy
   ↓
discard stale state
   ↓
READY
```

---

# 741.63 — Policy Revalidation

Persistent state không được tự động cấp lại capability cũ.

Mọi restored action phải revalidate authority.

---

# 741.64 — Secure Shell

Secure shell surface có thể dùng cho:

```text
authentication
privileged confirmation
security warnings
permission elevation
```

---

# 741.65 — Secure Surface Isolation

Secure shell không được share arbitrary application rendering paths.

---

# 741.66 — Password Boundary

AXSHELL không sở hữu credential storage.

Credentials:

→ `AXSECURITY`.

Identity:

→ `AXIDENTITY`.

---

# 741.67 — Accessibility

AXSHELL phải expose semantic tree cho:

```text
screen readers
keyboard navigation
switch devices
voice input
high contrast
large text
reduced motion
```

---

# 741.68 — Reduced Motion

Shell animation phải hỗ trợ:

```text
full
reduced
disabled
```

---

# 741.69 — High Contrast

Shell surfaces phải nhận system accessibility policy từ AXUI/accessibility subsystem.

---

# 741.70 — Input Integration

```text
AXINPUT
   ↓
raw input
   ↓
AXDESKTOP
   ↓
AXSHELL
   ↓
command
```

AXSHELL không trực tiếp đọc hardware.

---

# 741.71 — Global Input Routing

Routing:

```text
hardware
 ↓
AXINPUT
 ↓
focus/global shortcut resolution
 ↓
AXDESKTOP
 ↓
AXSHELL
```

---

# 741.72 — Shortcut Conflict

Nếu nhiều providers đăng ký cùng shortcut:

```text
system
 > secure
 > desktop
 > application
 > extension
```

theo explicit policy.

Không dùng registration order làm authority.

---

# 741.73 — System Actions

Canonical actions:

```axiom
lock_session()
logout()
shutdown()
restart()
sleep()
open_settings()
open_search()
open_notifications()
open_quick_settings()
switch_workspace()
show_desktop()
```

---

# 741.74 — Power Action Boundary

AXSHELL không trực tiếp tắt hardware.

Power action:

```text
AXSHELL
 ↓
authorized system service
 ↓
AXENERGY / platform backend
```

---

# 741.75 — System Settings

Settings UI có thể be shell-launched:

```text
AXSHELL
   ↓
settings application
```

Settings data vẫn thuộc subsystem tương ứng.

---

# 741.76 — Shell Search + AI

AI có thể hỗ trợ:

```text
natural-language command discovery
search expansion
result summarization
command suggestions
```

---

# 741.77 — AI Shell Boundary

AI không được tự động biến câu hỏi thành privileged action.

Ví dụ:

```text
"turn off security protection"
```

phải trở thành:

```text
proposal
→ explicit authorization
→ security policy
→ execution
```

---

# 741.78 — AI Search

AI search result phải phân biệt:

```text
indexed fact
AI-generated summary
action proposal
```

---

# 741.79 — AI Provenance

```axiom
shell_ai_result {
    source_ids
    generated_at
    model
    actionability
}
```

---

# 741.80 — Shell Simulation

```axiom
shell_simulation {
    desktop_state
    shell_state
    commands
    input_events
    policies
}
```

---

# 741.81 — Shell Replay

Replay phải hỗ trợ:

```text
menu open
command search
command execution
picker selection
clipboard transfer
drag/drop
notification interaction
```

---

# 741.82 — Deterministic Simulation

Cùng:

```text
initial_state
event_sequence
policy_version
```

→ cùng logical shell state.

---

# 741.83 — Digital Twin

```axiom
shell_digital_twin {
    desktop
    shell
    services
    policies
}
```

Có thể dùng để test:

```text
desktop automation
accessibility
security
UI workflows
failure recovery
```

---

# 741.84 — Telemetry

Shell telemetry:

```text
command_latency
search_latency
menu_open_latency
picker_latency
clipboard_transfer_latency
drag_drop_latency
notification_latency
shell_restart_count
extension_failure_count
```

---

# 741.85 — Performance Architecture

Shell hot path phải tránh:

```text
database queries
blocking filesystem operations
heap allocation storms
reflection
full UI tree rebuild
```

---

# 741.86 — Command Registry

Commands được index bằng:

```text
command_id
namespace
scope
capability
```

Không tìm command bằng full-text scan mỗi lần.

---

# 741.87 — Search Index

Search index phải incremental:

```text
register
update
remove
invalidate
```

---

# 741.88 — Lazy UI

Shell UI chỉ materialize:

```text
visible menu items
visible search results
visible notification groups
```

---

# 741.89 — Zero-Copy Transfer

Clipboard/file references nên ưu tiên:

```text
capability
shared buffer
memory mapping
file reference
```

thay vì copy payload lớn nhiều lần.

---

# 741.90 — Large Clipboard Data

Video/image/audio/file collections không nên đi qua shell message body.

Thay vào đó:

```text
metadata
+
capability
+
shared storage reference
```

---

# 741.91 — Drag Large Payload

Tương tự:

```text
drag metadata
+
capability
+
resource reference
```

---

# 741.92 — Shell Transactions

```axiom
begin_shell_transaction()

register_command()
update_menu()
update_notification()
update_status()

commit_shell_transaction()
```

---

# 741.93 — Transaction Failure

Nếu transaction fail:

```text
rollback
```

không để shell rơi vào trạng thái nửa cập nhật.

---

# 741.94 — Shell Event

Canonical events:

```text
shell_started
shell_ready
shell_suspended
shell_resumed
shell_closed

menu_opened
menu_closed

command_registered
command_executed
command_failed

search_started
search_completed

dialog_opened
dialog_closed

picker_opened
selection_changed
selection_committed
selection_cancelled

clipboard_changed
drag_started
drag_dropped

extension_loaded
extension_failed

secure_surface_opened
secure_surface_closed
```

---

# 741.95 — Event Metadata

Mỗi event có:

```axiom
shell_event {
    sequence
    timestamp
    session
    source
    target
    event_type
}
```

---

# 741.96 — Native API

```axiom
create_shell()
destroy_shell()

create_shell_surface()
destroy_shell_surface()

register_global_action()
unregister_global_action()

register_command()
unregister_command()
execute_command()

open_command_palette()

register_search_provider()
search()

open_quick_settings()

open_system_menu()
open_context_menu()

open_system_dialog()
close_system_dialog()

open_file_picker()
open_save_picker()
open_application_picker()

clipboard_set()
clipboard_get()
clipboard_clear()
clipboard_history()

begin_drag()
update_drag()
drop_drag()
cancel_drag()

register_shell_extension()
unregister_shell_extension()

lock_shell()
unlock_shell()

save_shell_state()
restore_shell_state()

begin_shell_transaction()
commit_shell_transaction()
cancel_shell_transaction()

create_shell_simulation()
record_shell()
replay_shell()

get_shell_diagnostics()
```

---

# 741.97 — Canonical Flow: Global Command

```text
keyboard/input
      ↓
AXINPUT
      ↓
AXDESKTOP
      ↓
AXSHELL
      ↓
command lookup
      ↓
capability validation
      ↓
command execution
      ↓
subsystem
      ↓
result
      ↓
AXSHELL
```

---

# 741.98 — Canonical Flow: File Picker

```text
application
    ↓
AXSHELL
    ↓
open_file_picker()
    ↓
AXSTORAGE discovery
    ↓
AXSECURITY validation
    ↓
user selection
    ↓
capability creation
    ↓
application
```

---

# 741.99 — Canonical Flow: Clipboard

```text
application A
      ↓
AXSHELL
      ↓
clipboard owner
      ↓
application B requests paste
      ↓
authorization
      ↓
typed transfer
      ↓
application B
```

---

# 741.100 — Canonical Flow: Drag & Drop

```text
source
 ↓
AXINPUT
 ↓
AXSHELL drag session
 ↓
target discovery
 ↓
capability validation
 ↓
drop
 ↓
resource transfer
```

---

# 741.101 — Canonical Flow: Secure Confirmation

```text
application
   ↓
privileged request
   ↓
AXSECURITY
   ↓
AXSHELL secure surface
   ↓
user confirmation
   ↓
security decision
   ↓
application/system service
```

AXSHELL **presents** the secure interaction; AXSECURITY remains authority.

---

# 741.102 — Formal Invariants

```text
SHL-INV-01   Every shell instance has a stable shell identity.
SHL-INV-02   Shell session identity is distinct from user identity.
SHL-INV-03   Shell surface identity is distinct from application window identity.
SHL-INV-04   Shell lifecycle transitions are explicit.
SHL-INV-05   Global commands have stable identities.
SHL-INV-06   Command discovery does not imply authorization.
SHL-INV-07   Command execution always performs current authorization checks.
SHL-INV-08   Search visibility respects current access policy.
SHL-INV-09   Search index state is distinct from authoritative source state.
SHL-INV-10   Search results cannot grant authority.

SHL-INV-11   Quick settings do not own underlying subsystem state.
SHL-INV-12   System status is derived from authoritative subsystem state.
SHL-INV-13   Context-menu actions are capability-checked.
SHL-INV-14   System dialogs have explicit ownership and modality.
SHL-INV-15   Picker selection does not itself grant unrestricted filesystem access.
SHL-INV-16   Clipboard ownership is explicit.
SHL-INV-17   Clipboard history obeys retention policy.
SHL-INV-18   Sensitive clipboard data may be restricted.
SHL-INV-19   Drag payload authority is explicit.
SHL-INV-20   Cross-process drag operations cannot implicitly transfer authority.

SHL-INV-21   Shell extensions are isolated by capability.
SHL-INV-22   Extension failure cannot invalidate the shell core.
SHL-INV-23   Secure shell surfaces are isolated from normal application surfaces.
SHL-INV-24   Shell cannot store authentication secrets as authoritative credentials.
SHL-INV-25   Global shortcuts require explicit authorization.
SHL-INV-26   Power actions require subsystem authorization.
SHL-INV-27   Remote shell operations require capability checks.
SHL-INV-28   Persistent shell state cannot restore expired capabilities.
SHL-INV-29   Shell checkpoints are versioned.
SHL-INV-30   Shell state commits are atomic.

SHL-INV-31   Crash recovery uses only committed shell state.
SHL-INV-32   Shell restore is distinct from event replay.
SHL-INV-33   Simulation cannot mutate production shell state.
SHL-INV-34   Replay cannot mutate production shell state.
SHL-INV-35   AI suggestions are distinct from executable commands.
SHL-INV-36   AI cannot bypass security authorization.
SHL-INV-37   Shell hot paths do not require persistent database access.
SHL-INV-38   Large payloads use references/shared resources instead of unnecessary copying.
SHL-INV-39   Logical shell state is independent of UI/GPU resource lifetime.
SHL-INV-40   Identical initial state, event sequence, and policy produce identical logical shell state.
```

---

# 741.103 — Completion Criteria

`BOOTSTRAP-741` phải freeze:

1. Shell environment.
2. Shell lifecycle.
3. Shell surfaces.
4. Global actions.
5. Command registry.
6. Command palette.
7. Command authorization.
8. Command result model.
9. Global search.
10. Search providers.
11. Search security.
12. Quick settings.
13. System status aggregation.
14. Notification center.
15. Context menus.
16. System dialogs.
17. File picker.
18. Save picker.
19. Application picker.
20. Handler selection.
21. Clipboard.
22. Clipboard formats.
23. Clipboard ownership.
24. Clipboard history.
25. Clipboard synchronization.
26. Drag/drop.
27. Cross-process drag.
28. System menu.
29. Application menu integration.
30. Shell extensions.
31. Extension isolation.
32. Extension failure recovery.
33. Shell process architecture.
34. Shell IPC.
35. Authoritative/derived/transient state.
36. Persistent shell state.
37. Checkpoint.
38. Crash recovery.
39. Policy revalidation.
40. Secure shell.
41. Authentication boundary.
42. Accessibility.
43. Reduced-motion support.
44. Global input routing.
45. Shortcut conflict resolution.
46. System actions.
47. Power-action boundary.
48. AI shell integration.
49. AI authority boundary.
50. Shell simulation.
51. Shell replay.
52. Digital twin.
53. Telemetry.
54. Command indexing.
55. Search indexing.
56. Lazy UI.
57. Zero-copy transfer.
58. Large-payload handling.
59. Shell transactions.
60. Shell event model.
61. Native API.
62. Canonical command flow.
63. File-picker flow.
64. Clipboard flow.
65. Drag/drop flow.
66. Secure-confirmation flow.
67. 40 formal invariants.

---

# 741.104 — Definition of Done

```text
BOOTSTRAP-741
STATUS: COMPLETE / FROZEN

AXSHELL
 ├── Shell Environment
 ├── Shell Lifecycle
 ├── System Menus
 ├── Command Registry
 ├── Command Palette
 ├── Global Search
 ├── Quick Settings
 ├── System Status
 ├── Notification Center
 ├── Context Menus
 ├── System Dialogs
 ├── File Picker
 ├── Application Picker
 ├── Clipboard
 ├── Clipboard History
 ├── Drag & Drop
 ├── Shell Extensions
 ├── Secure Shell
 ├── Accessibility
 ├── Global Shortcuts
 ├── Remote Shell
 ├── Persistence
 ├── Checkpoint / Recovery
 ├── AI Boundary
 ├── Simulation
 ├── Replay
 ├── Digital Twin
 ├── Telemetry
 ├── Zero-Copy Data Transfer
 ├── Native API
 ├── 40 Formal Invariants
 └── System Shell Runtime 5.0
```

**BOOTSTRAP-741 / AXSHELL — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-742 — AXAPPLICATION

**Native Application & Process Lifecycle Runtime — application identity, executable instances, process lifecycle, process groups, application launch/termination, sandbox integration, resource limits, application permissions, IPC integration, application state, crash/restart, background execution, service integration, multi-instance policy, package metadata, application-to-window mapping, session restore, application checkpoints, deterministic application simulation, application telemetry và Application Runtime 5.0.**