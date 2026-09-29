# BOOTSTRAP-740 — AXDESKTOP

**Namespace:** `AXDESKTOP`  
**Phase:** Axiom Civilization Runtime / Native Desktop Environment Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXWINDOW`, `AXDISPLAY`, `AXCOMPOSITOR`, `AXUI`, `AXINPUT`, `AXGRAPHICS`, `AXMEDIA`, `AXAUDIO`, `AXCOMPUTE`, `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXSECURITY`, `AXIDENTITY`, `AXASSET`

AXDESKTOP là tầng **desktop shell/environment**, nằm trên window/compositor/display infrastructure. Nó biến tập hợp window + display thành một môi trường desktop có tổ chức.

```text
AXAPPLICATION
      │
      ↓
     AXUI
      │
      ↓
   AXWINDOW
      │
      ↓
 AXCOMPOSITOR
      │
      ↓
  AXDISPLAY
      │
      ↓
    hardware

AXDESKTOP
    │
    ├── workspaces
    ├── taskbar / dock
    ├── launcher
    ├── desktop
    ├── window grouping
    ├── application switching
    ├── notifications
    ├── system areas
    └── session state
```

---

## 740.1 — Mục tiêu

AXDESKTOP phải cung cấp desktop runtime native cho:

```text
desktop shell
virtual desktops
workspaces
window management policy
taskbar
dock
launcher
application switcher
application groups
window tiling
window snapping
desktop icons
panels
system tray
status areas
notifications
quick actions
desktop wallpaper
multi-monitor desktop layout
session restore
login/logout integration
lock screen boundary
remote desktop
desktop persistence
desktop accessibility
desktop automation
desktop simulation
```

AXDESKTOP **không phải GUI toolkit**.

GUI semantics:

→ `AXUI`

Window semantics:

→ `AXWINDOW`

Composition:

→ `AXCOMPOSITOR`

---

# 740.2 — Desktop Environment Model

Canonical root:

```axiom
desktop_environment {
    id
    session
    displays
    workspaces
    windows
    panels
    launchers
    notifications
    policies
}
```

---

# 740.3 — Desktop Identity

```axiom
desktop_id
```

phải ổn định trong một desktop session.

---

# 740.4 — Desktop Session

```axiom
desktop_session {
    id
    user
    state
    started_at
    workspace
}
```

Session không đồng nghĩa authentication session của `AXSECURITY`.

---

# 740.5 — Session States

```text
CREATED
STARTING
READY
LOCKED
SUSPENDING
SUSPENDED
RESUMING
LOGGING_OUT
CLOSED
```

---

# 740.6 — Desktop State

Desktop state gồm:

```text
active workspace
window placement
panel configuration
launcher configuration
desktop items
notification state
display association
workspace layout
```

---

# 740.7 — Workspace

```axiom
workspace {
    id
    name
    index
    windows
    layout
}
```

Workspace là logical desktop context.

---

# 740.8 — Virtual Desktop

Virtual desktop là workspace có isolation về presentation/layout nhưng dùng chung underlying OS/session resources.

```text
Desktop
 ├── Workspace 1
 ├── Workspace 2
 ├── Workspace 3
 └── Workspace 4
```

---

# 740.9 — Workspace Isolation

Workspace không nhất thiết tạo process isolation.

Nó chỉ điều khiển:

```text
window visibility
window placement
active context
desktop presentation
```

---

# 740.10 — Workspace Switching

```axiom
switch_workspace(workspace_id)
```

phải là transactional state transition.

---

# 740.11 — Workspace Transition

Có thể hỗ trợ animation:

```text
workspace A
     ↓
transition
     ↓
workspace B
```

Animation thuộc presentation policy, không thay đổi logical state.

---

# 740.12 — Workspace Persistence

Desktop có thể persist:

```text
workspace identity
name
order
window placement
layout
display association
```

---

# 740.13 — Window Membership

Window có thể:

```text
belong to workspace
appear on all workspaces
be pinned
be transient
```

---

# 740.14 — Window Placement

```axiom
window_placement {
    workspace
    display
    bounds
    state
    z_order
}
```

---

# 740.15 — Placement vs Window State

Placement:

```text
x/y
width/height
display
workspace
```

khác:

```text
minimized
maximized
fullscreen
```

---

# 740.16 — Multi-Monitor Desktop

```text
Desktop
 ├── Display A
 │    ├── Workspace 1
 │    └── Workspace 2
 │
 └── Display B
      ├── Workspace 1
      └── Workspace 2
```

Policy có thể chọn:

```text
shared workspace
independent workspace
mirrored workspace
```

---

# 740.17 — Display Workspace Policy

```axiom
workspace_display_policy {
    shared
    independent
    mirrored
}
```

---

# 740.18 — Display Removal

Khi display biến mất:

```text
display lost
   ↓
resolve window placement
   ↓
migrate windows
   ↓
update desktop topology
```

AXDISPLAY cung cấp display event; AXDESKTOP quyết định desktop policy.

---

# 740.19 — Safe Placement

Window không được restore ra ngoài vùng hiển thị usable.

---

# 740.20 — Placement Resolver

```axiom
resolve_window_placement(
    requested,
    desktop_topology,
    policy
)
```

Output:

```text
accepted
adjusted
migrated
deferred
```

---

# 740.21 — Panels

```axiom
panel {
    id
    display
    edge
    size
    visibility
    items
}
```

Panel có thể nằm:

```text
top
bottom
left
right
floating
```

---

# 740.22 — Panel Edge

Panel phải respect:

```text
safe area
display work area
fullscreen policy
reserved areas
```

---

# 740.23 — Dock

Dock là panel chuyên biệt:

```text
application launcher
running applications
pinned applications
window groups
```

---

# 740.24 — Taskbar

Taskbar có thể cung cấp:

```text
start/launcher
running applications
window groups
workspace switcher
system status
clock
notifications
```

Không yêu cầu mọi desktop backend phải có tất cả thành phần.

---

# 740.25 — Launcher

```axiom
launcher {
    id
    entries
    search
    categories
}
```

---

# 740.26 — Application Entry

```axiom
application_entry {
    application_id
    name
    executable
    icon
    arguments
    capabilities
}
```

Application identity không được suy ra chỉ từ executable path.

---

# 740.27 — Application Launch

Flow:

```text
launcher
   ↓
application identity
   ↓
security validation
   ↓
process/application runtime
   ↓
window creation
   ↓
desktop placement
```

---

# 740.28 — Application Switching

```axiom
activate_application(application_id)
```

có thể activate:

```text
existing window
existing group
new instance
```

theo application policy.

---

# 740.29 — Window Switcher

```axiom
window_switcher {
    windows
    applications
    groups
    ordering
}
```

---

# 740.30 — Switch Ordering

Có thể duy trì:

```text
MRU
creation order
workspace order
explicit user order
```

Ordering là policy, không phải identity.

---

# 740.31 — Window Group

```axiom
window_group {
    id
    application
    windows
}
```

Một application có thể có nhiều group.

---

# 740.32 — Group Semantics

Group có thể được dùng cho:

```text
taskbar aggregation
switching
workspace organization
window arrangement
```

---

# 740.33 — Tiling

```axiom
tiling_layout {
    orientation
    children
    ratio
}
```

Ví dụ:

```text
┌─────────┬───────┐
│         │   B   │
│    A    ├───────┤
│         │   C   │
└─────────┴───────┘
```

---

# 740.34 — Tiling Tree

```text
split
 ├── window A
 └── split
      ├── window B
      └── window C
```

---

# 740.35 — Tiling Ratio

Ratio phải là deterministic fixed-point hoặc normalized representation.

Không dùng floating-point không kiểm soát cho persistent layout state.

---

# 740.36 — Snap

Snap zones:

```text
left half
right half
top
corner
custom zone
```

---

# 740.37 — Snap Preview

Preview chỉ là transient visual state.

Không thay đổi placement authoritative trước commit.

---

# 740.38 — Maximize

Desktop có thể resolve:

```text
maximize window
```

thành work-area bounds.

---

# 740.39 — Fullscreen

Fullscreen thuộc AXWINDOW semantics.

AXDESKTOP chỉ cung cấp desktop policy:

```text
exclusive
borderless
workspace fullscreen
display fullscreen
```

---

# 740.40 — Desktop Icons

```axiom
desktop_item {
    id
    position
    target
    icon
    label
}
```

---

# 740.41 — Desktop Item Identity

Desktop item identity độc lập với file identity.

---

# 740.42 — Wallpaper

```axiom
wallpaper {
    source
    mode
    display_policy
}
```

Modes:

```text
stretch
fit
fill
center
tile
span
per_display
```

---

# 740.43 — Dynamic Wallpaper

Dynamic content có thể được cung cấp bởi `AXMEDIA`.

AXDESKTOP chỉ quản lý placement/lifecycle.

---

# 740.44 — System Status Area

```axiom
status_area {
    items
    priority
    visibility
}
```

---

# 740.45 — System Tray

Tray item có thể cung cấp:

```text
icon
status
menu
notifications
actions
```

---

# 740.46 — Notification

```axiom
notification {
    id
    source
    title
    body
    priority
    timestamp
    actions
    lifetime
}
```

---

# 740.47 — Notification Priority

```text
low
normal
high
critical
```

Priority chỉ quyết định presentation policy, không tự động bypass security.

---

# 740.48 — Notification Actions

```axiom
notification_action {
    id
    label
    capability
}
```

Action phải capability-checked.

---

# 740.49 — Notification Persistence

Notification có thể:

```text
ephemeral
persistent
history
```

---

# 740.50 — Notification Security

Notification không được tự động truy cập:

```text
private window contents
secure session data
authentication secrets
```

---

# 740.51 — Lock Screen Boundary

Lock screen thuộc desktop/security integration.

Khi locked:

```text
normal desktop
      ↓
locked presentation
```

---

# 740.52 — Lock Screen Isolation

Normal application surfaces không được render trên lock screen trừ khi explicitly authorized system surfaces.

---

# 740.53 — Secure Desktop

```axiom
secure_desktop {
    mode
    owner
    allowed_surfaces
}
```

---

# 740.54 — Login Boundary

AXDESKTOP không xác thực credentials.

Authentication:

→ `AXSECURITY` / `AXIDENTITY`

Desktop nhận authentication/session state.

---

# 740.55 — Logout

Logout flow:

```text
request logout
    ↓
application close negotiation
    ↓
session cleanup
    ↓
desktop state persistence
    ↓
session closed
```

---

# 740.56 — Forced Logout

Nếu application không phản hồi:

```text
graceful close
     ↓
timeout
     ↓
forced termination
```

Security policy quyết định quyền force termination.

---

# 740.57 — Session Restore

Restore:

```text
desktop session
 ↓
workspaces
 ↓
applications
 ↓
windows
 ↓
placements
```

---

# 740.58 — Restore Is Not Replay

Session restore không phải deterministic replay.

Restore tái tạo desired state; replay tái tạo event history.

---

# 740.59 — Application Restore

Application có thể cung cấp:

```axiom
restore_token
```

để khôi phục logical state.

---

# 740.60 — Desktop State Store

Persistent desktop state:

```text
AXDESKTOP
   ↓
AXSTORAGE
   ↓
AXDATABASE
```

---

# 740.61 — Atomic State Save

Desktop configuration phải commit atomically.

---

# 740.62 — Crash Recovery

Nếu desktop crash:

```text
last committed state
```

phải được phục hồi.

---

# 740.63 — Dirty State

Runtime state:

```text
clean
dirty
saving
recovered
```

---

# 740.64 — Desktop Transactions

```axiom
begin_desktop_transaction()

move_window()
switch_workspace()
change_panel()
change_dock()

commit_desktop_transaction()
```

---

# 740.65 — Atomic Desktop Update

Nhiều thay đổi liên quan phải có thể commit cùng nhau:

```text
move window
+
change workspace
+
update taskbar
```

---

# 740.66 — Event Model

```text
desktop_created
workspace_created
workspace_switched
window_added
window_removed
window_moved
window_grouped
window_snapped
window_tiled
panel_changed
notification_posted
notification_closed
session_locked
session_unlocked
session_suspended
session_resumed
session_closed
```

---

# 740.67 — Event Ordering

Desktop events phải có:

```text
sequence
timestamp
session
source
```

---

# 740.68 — Accessibility

AXDESKTOP phải expose:

```text
workspace names
window ordering
application groups
notification state
panel controls
launcher entries
```

cho accessibility layer của AXUI.

---

# 740.69 — Keyboard Navigation

Desktop actions có thể được invoke bằng:

```text
keyboard
pointer
touch
pen
controller
assistive input
```

Input normalization:

→ `AXINPUT`.

---

# 740.70 — Global Shortcuts

```axiom
desktop_shortcut {
    gesture
    action
    scope
    capability
}
```

Scope:

```text
desktop
workspace
application
session
```

---

# 740.71 — Shortcut Security

Global shortcut registration phải chịu capability policy.

Ứng dụng không được mặc định hijack toàn bộ desktop input.

---

# 740.72 — Desktop Command

Canonical command:

```axiom
desktop_command {
    action
    target
    parameters
    capability
}
```

---

# 740.73 — Command Examples

```axiom
switch_workspace(...)
focus_window(...)
tile_window(...)
snap_window(...)
minimize_window(...)
restore_window(...)
launch_application(...)
close_window(...)
show_launcher(...)
post_notification(...)
```

---

# 740.74 — AI Desktop Assistant

AI có thể đề xuất:

```text
window organization
workspace grouping
application launch
layout optimization
notification summarization
```

---

# 740.75 — AI Authority Boundary

AI không được tự động:

```text
close arbitrary application
terminate process
change security policy
unlock session
bypass permissions
access private window contents
```

nếu không có explicit authority.

---

# 740.76 — AI Action Proposal

```axiom
desktop_ai_proposal {
    action
    reason
    affected_windows
    confidence
    required_capabilities
}
```

Proposal khác command.

---

# 740.77 — Remote Desktop

Remote desktop có thể expose:

```text
desktop state
composition stream
input channel
```

nhưng phải phân biệt:

```text
remote control
remote observation
remote rendering
```

---

# 740.78 — Remote Observation

Chỉ capture những surfaces được policy cho phép.

---

# 740.79 — Remote Control

Input từ remote client:

```text
AXNETWORK
    ↓
AXINPUT
    ↓
AXDESKTOP
```

phải đi qua capability boundary.

---

# 740.80 — Multi-User Desktop

Một hệ thống có thể hỗ trợ:

```text
user A → session A
user B → session B
```

Desktop state không được nhầm lẫn giữa các session.

---

# 740.81 — Fast User Switching

Có thể:

```text
session A
 ↓
suspend
 ↓
session B
```

mà không destroy session A.

---

# 740.82 — Session Isolation

Session khác nhau phải không truy cập desktop surfaces của nhau nếu không được cấp capability.

---

# 740.83 — Desktop Resource Policy

Desktop có thể giới hạn:

```text
notification rate
panel updates
wallpaper animation
desktop effects
background activity
```

---

# 740.84 — Power-Aware Desktop

Khi power constrained:

```text
dynamic wallpaper → reduce/disable
effects → reduce
animation → reduce
composition frequency → adapt
```

AXDESKTOP gửi policy hints; energy semantics thuộc `AXENERGY`.

---

# 740.85 — Thermal-Aware Desktop

Có thể giảm:

```text
animation
blur
background refresh
thumbnail generation
```

khi system thermal policy yêu cầu.

---

# 740.86 — Thumbnail

Window thumbnail có thể được tạo từ:

```text
AXCOMPOSITOR capture
window surface
application-provided preview
```

---

# 740.87 — Thumbnail Cache

Thumbnail cache phải:

```text
versioned
bounded
invalidatable
security-aware
```

---

# 740.88 — Application Preview

Preview có thể là:

```text
live
snapshot
application supplied
```

Không được coi preview là authoritative application state.

---

# 740.89 — Desktop Search

Launcher/search có thể tìm:

```text
applications
files
settings
windows
workspaces
notifications
```

Search backend có thể sử dụng `AXDATABASE`.

---

# 740.90 — Search Security

Search index phải tôn trọng capability và user/session privacy.

---

# 740.91 — Desktop Settings

```axiom
desktop_settings {
    theme
    scaling
    wallpaper
    workspace_policy
    panel_policy
    notification_policy
    shortcut_policy
}
```

Display hardware settings:

→ `AXDISPLAY`.

---

# 740.92 — Theme

Theme thuộc AXUI.

AXDESKTOP chỉ quản lý desktop-level theme reference.

---

# 740.93 — Desktop Policy

```axiom
desktop_policy {
    placement
    workspace
    notifications
    shortcuts
    power
    security
}
```

---

# 740.94 — Policy Version

Policy phải versioned:

```text
policy_id
version
effective_from
```

---

# 740.95 — Deterministic Desktop Simulation

```axiom
desktop_simulation {
    displays
    windows
    workspaces
    input_events
    policies
}
```

Simulation không tác động desktop production.

---

# 740.96 — Desktop Replay

Replay sequence:

```text
session_created
workspace_created
window_created
window_moved
workspace_switched
window_closed
...
```

---

# 740.97 — Replay Determinism

Cùng:

```text
initial_state
event_sequence
policy_version
```

phải tạo cùng logical desktop state.

---

# 740.98 — Digital Twin

```axiom
desktop_digital_twin {
    session
    displays
    workspaces
    windows
    policies
}
```

Dùng cho:

```text
testing
simulation
automation
performance analysis
```

---

# 740.99 — Desktop Telemetry

Metrics:

```text
window_count
workspace_count
switch_latency
launch_latency
restore_latency
notification_rate
composition_latency
frame_drop_rate
```

---

# 740.100 — Desktop Performance

Hot path phải tránh:

```text
heap allocation
reflection
dynamic string lookup
database query
blocking IPC
```

cho mỗi input/frame.

---

# 740.101 — Dense Runtime State

Hot structures:

```text
window_index
workspace_index
display_index
panel_index
application_index
```

dùng integer handles + generation counters.

---

# 740.102 — Cold Metadata

Cold data:

```text
labels
icons
descriptions
history
diagnostics
provenance
```

tách khỏi hot state.

---

# 740.103 — Desktop Event Queue

Event queue phải:

```text
bounded or explicitly growable
timestamped
ordered
coalescible
nonblocking where possible
```

---

# 740.104 — Event Coalescing

Ví dụ:

```text
move A
move A
move A
move A
```

có thể coalesce thành final movement trước khi consumer xử lý nếu semantic contract cho phép.

---

# 740.105 — Window Move Coalescing

Không được mất:

```text
begin move
end move
```

nếu application cần lifecycle events.

---

# 740.106 — Workspace Switch Coalescing

Intermediate workspace switches có thể coalesce trong presentation layer nhưng committed logical transitions phải được xác định rõ.

---

# 740.107 — Desktop Native API

```axiom
create_desktop()
destroy_desktop()

create_session()
close_session()

create_workspace()
destroy_workspace()
switch_workspace()

list_workspaces()
rename_workspace()

add_window()
remove_window()
move_window()
focus_window()

tile_window()
untile_window()
snap_window()

create_panel()
destroy_panel()

create_dock()
destroy_dock()

register_launcher()
launch_application()

group_windows()
ungroup_windows()

show_window_switcher()

create_desktop_item()
move_desktop_item()
remove_desktop_item()

set_wallpaper()

post_notification()
dismiss_notification()

lock_desktop()
unlock_desktop()

suspend_session()
resume_session()

save_desktop_state()
restore_desktop_state()

begin_desktop_transaction()
commit_desktop_transaction()
cancel_desktop_transaction()

create_desktop_simulation()
record_desktop()
replay_desktop()

get_desktop_diagnostics()
```

---

# 740.108 — Canonical Flow: Application Launch

```text
launcher
   ↓
AXDESKTOP
   ↓
application identity
   ↓
AXSECURITY
   ↓
application runtime
   ↓
AXWINDOW
   ↓
window surface
   ↓
AXCOMPOSITOR
   ↓
AXDISPLAY
```

---

# 740.109 — Canonical Flow: Workspace Switch

```text
input
 ↓
AXINPUT
 ↓
AXDESKTOP
 ↓
validate workspace
 ↓
desktop transaction
 ↓
update window visibility
 ↓
AXCOMPOSITOR
 ↓
present
```

---

# 740.110 — Canonical Flow: Display Removal

```text
AXDISPLAY
    ↓
display_removed
    ↓
AXDESKTOP
    ↓
placement resolver
    ↓
migrate affected windows
    ↓
update workspace/display association
    ↓
AXWINDOW
    ↓
AXCOMPOSITOR
```

---

# 740.111 — Canonical Flow: Crash Recovery

```text
desktop crash
    ↓
restart desktop runtime
    ↓
load last committed state
    ↓
restore workspace topology
    ↓
restore application descriptors
    ↓
restore window placements
    ↓
rebuild panels/dock
    ↓
READY
```

---

# 740.112 — Formal Invariants

```text
DSK-INV-01   Every desktop has a stable desktop identity.
DSK-INV-02   Every desktop session has a unique session identity.
DSK-INV-03   Desktop session identity is distinct from authentication identity.
DSK-INV-04   Workspace identity is stable within its lifecycle.
DSK-INV-05   Workspace membership is explicit.
DSK-INV-06   Workspace switching is an explicit state transition.
DSK-INV-07   Workspace state is distinct from process state.
DSK-INV-08   Window placement is distinct from window lifecycle state.
DSK-INV-09   Display topology is not owned by AXDESKTOP.
DSK-INV-10   Display removal always triggers explicit placement resolution.

DSK-INV-11   A window cannot be silently placed outside the usable desktop region.
DSK-INV-12   Multi-display placement is display-aware.
DSK-INV-13   Shared and independent workspace policies are explicit.
DSK-INV-14   Tiling layout state is deterministic.
DSK-INV-15   Snap preview cannot silently mutate committed placement.
DSK-INV-16   Panel identity is stable.
DSK-INV-17   Dock/taskbar semantics are distinct from generic panels.
DSK-INV-18   Application identity is distinct from executable path.
DSK-INV-19   Window identity is distinct from application identity.
DSK-INV-20   Window groups have explicit membership.

DSK-INV-21   Notification identity is stable.
DSK-INV-22   Notification actions require explicit capability.
DSK-INV-23   Lock-screen surfaces are isolated from normal application surfaces.
DSK-INV-24   Desktop unlock requires security authority.
DSK-INV-25   Global shortcuts require explicit authorization.
DSK-INV-26   Remote desktop input is capability-controlled.
DSK-INV-27   Remote observation cannot bypass capture policy.
DSK-INV-28   Session state cannot cross users without explicit authorization.
DSK-INV-29   Persistent desktop state is versioned.
DSK-INV-30   Desktop state commits are atomic.

DSK-INV-31   Crash recovery uses committed state only.
DSK-INV-32   Session restore is distinct from event replay.
DSK-INV-33   Replay does not mutate production desktop state.
DSK-INV-34   Simulation does not mutate production desktop state.
DSK-INV-35   AI proposals are distinct from authorized commands.
DSK-INV-36   AI cannot bypass desktop security boundaries.
DSK-INV-37   Desktop hot paths do not require database access.
DSK-INV-38   Event coalescing cannot violate required lifecycle semantics.
DSK-INV-39   Desktop logical state is independent of compositor/GPU resource lifetime.
DSK-INV-40   Replaying identical state, events, and policy produces identical logical desktop state.
```

---

# 740.113 — Completion Criteria

`BOOTSTRAP-740` phải freeze:

1. Desktop environment identity.
2. Desktop session.
3. Session lifecycle.
4. Workspace.
5. Virtual desktop.
6. Workspace isolation.
7. Workspace switching.
8. Workspace persistence.
9. Window membership.
10. Window placement.
11. Placement resolver.
12. Multi-monitor topology integration.
13. Display removal migration.
14. Panels.
15. Dock.
16. Taskbar.
17. Launcher.
18. Application entries.
19. Application launching.
20. Application switching.
21. Window switcher.
22. Window grouping.
23. Tiling.
24. Tiling tree.
25. Snap.
26. Maximize policy.
27. Desktop icons.
28. Wallpaper.
29. Dynamic wallpaper boundary.
30. System status area.
31. System tray.
32. Notifications.
33. Notification actions.
34. Notification persistence.
35. Notification security.
36. Lock screen.
37. Secure desktop.
38. Login boundary.
39. Logout.
40. Forced logout.
41. Session restore.
42. Application restore.
43. Persistent state.
44. Atomic state save.
45. Crash recovery.
46. Desktop transactions.
47. Event model.
48. Accessibility.
49. Global shortcuts.
50. Desktop commands.
51. AI proposal boundary.
52. Remote desktop.
53. Multi-user sessions.
54. Fast user switching.
55. Power-aware behavior.
56. Thermal-aware behavior.
57. Window thumbnails.
58. Desktop search.
59. Desktop settings.
60. Desktop policy.
61. Deterministic simulation.
62. Replay.
63. Digital twin.
64. Telemetry.
65. Performance architecture.
66. Hot/cold state separation.
67. Event coalescing.
68. Native API.
69. Canonical flows.
70. 40 formal invariants.

---

# 740.114 — Definition of Done

```text
BOOTSTRAP-740
STATUS: COMPLETE / FROZEN

AXDESKTOP
 ├── Desktop Environment
 ├── Desktop Session
 ├── Workspace
 ├── Virtual Desktop
 ├── Multi-Monitor Policy
 ├── Window Placement
 ├── Panels
 ├── Dock
 ├── Taskbar
 ├── Launcher
 ├── Application Switching
 ├── Window Groups
 ├── Tiling
 ├── Snapping
 ├── Desktop Items
 ├── Wallpaper
 ├── System Tray
 ├── Notifications
 ├── Lock Screen Boundary
 ├── Session Persistence
 ├── Crash Recovery
 ├── Desktop Transactions
 ├── Accessibility
 ├── Global Shortcuts
 ├── Remote Desktop
 ├── Multi-User Sessions
 ├── AI Boundary
 ├── Simulation
 ├── Replay
 ├── Digital Twin
 ├── Telemetry
 ├── Native API
 ├── Performance Architecture
 ├── 40 Formal Invariants
 └── Desktop Environment Runtime 5.0
```

**BOOTSTRAP-740 / AXDESKTOP — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-741 — AXSHELL

**Native System Shell & Human-Environment Runtime — system menus, command palette, global actions, system search, application menu, quick settings, notification center, status orchestration, context menus, system dialogs, file/application pickers, clipboard integration, drag-and-drop coordination, system-wide UI surfaces, shell extensions, accessibility shell integration, secure shell surfaces, shell policy, session-aware shell state, deterministic shell simulation và System Shell Runtime 5.0.**