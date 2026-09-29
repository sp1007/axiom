Tiếp tục với **BOOTSTRAP-619** — đây là lớp GUI native cấp cao đầu tiên, nằm trên Window/Input/Text/Graphics đã hoàn thiện ở 615, 617 và 618.

:::writing{variant="document" id="32681" title="BOOTSTRAP-619 — Native GUI Windowing, Controls, Layout, Accessibility, Clipboard, Drag-and-Drop & Desktop UI Runtime 5.0"}
# BOOTSTRAP-619 — Native GUI Windowing, Controls, Layout, Accessibility, Clipboard, Drag-and-Drop & Desktop UI Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Native Runtime / GUI & Desktop Interaction  
**Depends on:** BOOTSTRAP-600 → 618

---

# 1. Purpose

BOOTSTRAP-619 defines the native GUI foundation for Axiom applications:

- application windows;
- views;
- controls;
- layout;
- panels;
- buttons;
- text fields;
- lists;
- trees;
- tables;
- menus;
- toolbars;
- dialogs;
- popups;
- tabs;
- scrolling;
- focus;
- keyboard navigation;
- accessibility;
- clipboard;
- drag-and-drop;
- context menus;
- native file dialogs;
- system dialogs;
- themes;
- high-DPI rendering;
- localization;
- RTL UI;
- UI state;
- event routing;
- retained-mode rendering;
- immediate-mode interoperability;
- native/platform adapters.

The primary architectural goal is:

> **Axiom GUI must provide a coherent cross-platform retained UI model without forcing applications to depend on a specific operating-system widget toolkit.**

---

# 2. Scope

619 sits above:

```text
614 Device
615 Graphics / Window
617 Text / Unicode / Typography
618 Input / Interaction
```

and below:

```text
Application UI
IDE
Document Editor
Game Editor
Business Application
Designer
```

---

# 3. Non-Goals

619 does not define:

- application business logic;
- document models;
- game UI frameworks;
- 3D scene graphs;
- web HTML/CSS compatibility;
- a browser engine;
- platform-specific application frameworks as the core API.

---

# 4. Architecture

```text
                    AXIOM APPLICATION
                           │
                           ▼
                    UI COMPONENT TREE
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Controls       Layout       Styling
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                     GUI RUNTIME
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
     Input               Text              Graphics
      618                617                 615
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                      Window / OS
```

---

# 5. Core GUI Objects

```text
GuiApplication
Window
View
Control
Container
Layout
Style
Theme
UiContext
UiNode
UiTree
UiEvent
UiCommand
UiState
FocusManager
Clipboard
DragDropManager
AccessibilityManager
Dialog
Menu
Popup
```

---

# 6. Struct-Only Architecture

619 does not require classes.

Example:

```text
struct Button {
    id: ControlId
    state: ButtonState
    label: String
}

fn Button.click(self) {
    ...
}
```

---

# 7. UI Node

Every visual element has:

```text
UiNodeId
parent
children
bounds
visibility
enabled
focusability
style
```

---

# 8. Node Identity

UI identity is stable during the lifetime of the UI node.

---

# 9. Generation Safety

Destroyed/recreated nodes use a new generation.

Stale node handles must fail safely.

---

# 10. UI Tree

619 uses a retained tree:

```text
Window
 └── Root
      ├── Toolbar
      ├── Content
      │    ├── Sidebar
      │    └── MainView
      └── StatusBar
```

---

# 11. Logical vs Visual Tree

The logical tree describes semantic ownership.

The visual tree describes actual rendered elements.

They may differ.

---

# 12. Tree Mutation

Tree changes are explicit:

```text
append_child()
insert_child()
remove_child()
replace_child()
```

---

# 13. UI Thread Affinity

A UI tree normally belongs to one UI context/executor.

Mutation from other threads must be marshalled through the UI executor.

---

# 14. UI Context

```text
UiContext
```

contains:

```text
event loop
root tree
theme
locale
font context
clipboard
accessibility
scheduler
```

---

# 15. Multiple UI Contexts

An application may have multiple windows sharing one UI context or isolated contexts.

---

# 16. UI Event

Events include:

```text
Pointer
Keyboard
Text
Focus
Window
Gesture
Command
DragDrop
Accessibility
```

---

# 17. Event Phases

Events use:

```text
Capture
Target
Bubble
DefaultAction
```

---

# 18. Event Consumption

Handlers return explicit propagation status.

---

# 19. Reentrancy

UI event dispatch defaults to non-reentrant nested dispatch.

Events generated during dispatch are queued.

---

# 20. Commands

Actions can be represented by:

```text
UiCommand
```

with:

```text
id
enabled
checked
visible
shortcut
execute
```

---

# 21. Command Routing

Commands route through:

```text
focused control
focused window
active context
application
```

---

# 22. Command Example

```text
Command::Save
Command::Undo
Command::Redo
Command::Copy
Command::Paste
```

---

# 23. Command State

A command can expose:

```text
Enabled
Disabled
Checked
Unchecked
Indeterminate
```

---

# 24. Control Model

Base semantic capabilities:

```text
Focusable
Clickable
Editable
Scrollable
Selectable
Draggable
DropTarget
```

are traits/interfaces rather than a mandatory inheritance hierarchy.

---

# 25. Button

```text
Button {
    label
    command
    state
}
```

supports keyboard and pointer activation.

---

# 26. Toggle Button

```text
ToggleButton {
    checked
}
```

---

# 27. Check Box

States:

```text
Unchecked
Checked
Indeterminate
```

---

# 28. Radio Group

Radio controls share an explicit selection group.

---

# 29. Text Label

```text
Label {
    text
    style
}
```

uses 617 for shaping/layout.

---

# 30. Text Field

Supports:

- UTF-8 text;
- cursor;
- selection;
- clipboard;
- undo;
- redo;
- IME;
- validation;
- password mode.

---

# 31. Multiline Text Field

Supports:

- paragraphs;
- wrapping;
- scrolling;
- selection;
- IME;
- bidirectional text.

---

# 32. Password Field

Password controls:

- hide display;
- enable secure input;
- prevent accidental diagnostic logging;
- use platform secure-input semantics.

---

# 33. Numeric Field

A numeric field has:

```text
value_type
min
max
step
format
```

and uses explicit parsing rather than locale-dependent application logic.

---

# 34. Slider

```text
Slider {
    min
    max
    value
    step
}
```

---

# 35. Progress Bar

```text
ProgressBar {
    value
    state
}
```

States:

```text
Normal
Indeterminate
Paused
Error
```

---

# 36. Scroll View

```text
ScrollView {
    content
    offset
    viewport
}
```

---

# 37. Scrollbar

Supports:

- vertical;
- horizontal;
- proportional thumb;
- keyboard navigation;
- pointer interaction.

---

# 38. List

List supports:

```text
single selection
multiple selection
keyboard navigation
virtualization
scrolling
```

---

# 39. Tree

Tree supports:

```text
expand
collapse
selection
keyboard navigation
lazy children
```

---

# 40. Table

Table supports:

```text
columns
rows
selection
sorting boundary
resizing
scrolling
virtualization
```

Sorting itself belongs to application/data models.

---

# 41. Virtualization

Large lists/tables must not instantiate one UI node per data item.

---

# 42. Virtualized View

The control creates visual children only for visible/near-visible items.

---

# 43. Selection Model

Selection is independent of visual controls:

```text
SelectionModel<T>
```

---

# 44. Selection Modes

```text
None
Single
Multiple
Extended
```

---

# 45. Tab Control

Tabs provide:

```text
TabHeader
TabContent
SelectedIndex
```

---

# 46. Menu

Menu supports:

```text
items
submenus
commands
shortcuts
checked state
radio groups
separators
```

---

# 47. Context Menu

Context menus are attached to:

```text
control
selection
pointer position
```

---

# 48. Menu Keyboard Navigation

Supports directional navigation and platform conventions.

---

# 49. Toolbar

Toolbar contains command-bound controls.

---

# 50. Dialog

Dialog supports:

```text
modal
modeless
result
buttons
focus
```

---

# 51. Modal Dialog

A modal dialog creates a temporary input context.

---

# 52. Dialog Result

```text
DialogResult {
    Accepted
    Cancelled
    Custom(CommandId)
}
```

---

# 53. Popup

Popup is a transient visual surface associated with another UI node.

---

# 54. Tooltip

Tooltip is delayed contextual information.

It should not steal keyboard focus by default.

---

# 55. Notification

Toast/notification UI is a higher-level component built on popup infrastructure.

---

# 56. Layout System

619 defines a constraint-oriented layout engine.

Primary layouts:

```text
Stack
Row
Column
Grid
Flow
Overlay
Dock
Absolute
```

---

# 57. Layout Pipeline

```text
Measure
    ↓
Arrange
    ↓
Render
```

---

# 58. Measure

A child reports its desired size under constraints.

---

# 59. Arrange

Parent assigns final bounds.

---

# 60. Render

The control emits drawing commands through 615.

---

# 61. Layout Constraints

```text
MinWidth
MaxWidth
PreferredWidth
MinHeight
MaxHeight
PreferredHeight
```

---

# 62. Size Units

Supports:

```text
Pixels
DIP
Percent
Auto
Content
Fraction
```

---

# 63. DPI

UI dimensions use logical units and convert to physical pixels at rendering time.

---

# 64. Fractional Coordinates

Layout retains fractional coordinates.

---

# 65. Pixel Snapping

Controls may request snapping for sharp borders/text.

---

# 66. Row/Column Grid

Grid supports:

```text
Fixed
Auto
Fraction
```

tracks.

---

# 67. Stack Layout

Stack supports:

```text
Horizontal
Vertical
```

with spacing.

---

# 68. Flow Layout

Flow wraps children according to available width.

---

# 69. Overlay

Overlay permits children to occupy the same region.

---

# 70. Dock

Dock supports:

```text
Top
Bottom
Left
Right
Fill
```

---

# 71. Layout Cache

Stable layout trees may cache measurements.

---

# 72. Incremental Layout

Changing one control should invalidate only affected layout regions.

---

# 73. Dirty Flags

Nodes can be marked:

```text
MeasureDirty
ArrangeDirty
RenderDirty
StyleDirty
AccessibilityDirty
```

---

# 74. Render Invalidation

Controls request repaint using dirty regions.

---

# 75. Dirty Region

Only affected areas need redrawing when backend permits.

---

# 76. Retained Rendering

The UI tree retains semantic state.

Rendering commands may be regenerated from dirty regions.

---

# 77. Immediate Rendering Interop

Custom controls may emit direct 615 rendering commands.

---

# 78. Custom Draw

```text
CustomView {
    on_render(ctx)
}
```

---

# 79. Render Context

Provides:

```text
draw_rect
draw_path
draw_image
draw_text
clip
transform
```

through 615/617.

---

# 80. GPU Safety

UI shaders/custom GPU operations remain constrained by 615 security rules.

---

# 81. Theme

```text
Theme
```

defines semantic styles rather than hard-coded widget appearance.

---

# 82. Theme Tokens

Examples:

```text
color.surface
color.text
color.accent
spacing.small
radius.control
font.body
```

---

# 83. Style

A style can define:

```text
font
foreground
background
border
padding
margin
radius
shadow
opacity
```

---

# 84. State Styling

Styles may vary by:

```text
Normal
Hover
Pressed
Focused
Disabled
Selected
Checked
Error
```

---

# 85. Pseudo-State

Pseudo-states are derived from UI state.

---

# 86. Theme Inheritance

Styles inherit from parent contexts.

---

# 87. Style Resolution

Style resolution should be cached and invalidated incrementally.

---

# 88. No CSS Requirement

619 does not require HTML/CSS semantics.

Its style system is native typed data.

---

# 89. Theme Serialization

Themes may use:

```text
.axtheme
```

---

# 90. Theme Resource

A theme contains:

```text
colors
metrics
fonts
icons
control styles
animation settings
```

---

# 91. Dark/Light Theme

Theme selection is explicit.

---

# 92. System Theme

Applications may request system theme preference through a platform provider.

---

# 93. High Contrast

Accessibility settings can override normal theme tokens.

---

# 94. Reduced Motion

Animations can respect system/user reduced-motion preferences.

---

# 95. UI Animation

Animation system supports:

```text
Property
Duration
Easing
Timeline
```

---

# 96. Animation Constraints

Animations must not prevent input or shutdown indefinitely.

---

# 97. Reduced Motion

The runtime can replace animations with immediate state transitions.

---

# 98. Focus Management

Focus manager provides:

```text
request_focus()
release_focus()
move_next()
move_previous()
```

---

# 99. Focus Navigation

Default navigation:

```text
Tab
Shift+Tab
Arrow keys
```

can be customized.

---

# 100. Focus Scope

A dialog or popup can create a focus scope.

---

# 101. Focus Restoration

Closing a temporary UI can restore previous focus when valid.

---

# 102. Keyboard Navigation

Controls must expose semantic activation independent of pointer events.

---

# 103. Default Button

Dialogs may define a default command.

---

# 104. Cancel Button

Dialogs may define an escape/cancel command.

---

# 105. Access Keys

Controls may expose optional keyboard access keys.

---

# 106. Accessibility

619 defines a semantic accessibility tree.

---

# 107. Accessibility Node

```text
AccessibilityNode {
    role
    name
    description
    value
    state
    bounds
    actions
    children
}
```

---

# 108. Accessibility Roles

Examples:

```text
Window
Button
CheckBox
RadioButton
TextField
Text
List
ListItem
Tree
TreeItem
Table
TableCell
Slider
Menu
MenuItem
Dialog
Image
```

---

# 109. Accessibility State

States include:

```text
Focused
Disabled
Selected
Checked
Expanded
Collapsed
Busy
Invalid
ReadOnly
```

---

# 110. Accessibility Actions

Examples:

```text
Activate
Focus
Select
Expand
Collapse
Increment
Decrement
Scroll
SetValue
```

---

# 111. Accessibility Values

Controls expose typed semantic values where appropriate.

---

# 112. Accessibility Text

617 provides Unicode text.

---

# 113. Accessibility Tree Independence

The accessibility tree may differ from the visual tree.

---

# 114. Accessibility Updates

Changes generate incremental accessibility notifications.

---

# 115. Screen Reader Boundary

Platform adapters expose the semantic tree to:

```text
Windows
macOS
iOS
Android
WASM
```

accessibility systems.

---

# 116. Keyboard Accessibility

Every actionable control should have a keyboard-accessible semantic action unless intentionally noninteractive.

---

# 117. Focus Visibility

Theme may render a visible focus indicator.

---

# 118. Accessibility Labels

Visual controls can expose:

```text
accessible_name
accessible_description
```

---

# 119. Accessibility Relations

Nodes may expose:

```text
labelled_by
described_by
controls
controlled_by
```

---

# 120. Live Regions

Dynamic content can request accessibility announcements.

---

# 121. Clipboard

```text
Clipboard
```

supports typed formats.

---

# 122. Clipboard Data

Formats:

```text
Text
HTML
RichText
Image
Files
Custom
```

---

# 123. Clipboard Ownership

Clipboard data may be lazily supplied by the owner.

---

# 124. Clipboard Security

Applications must not assume clipboard data is trusted.

---

# 125. Clipboard Access

Some platforms restrict background clipboard access.

The adapter must respect platform policy.

---

# 126. Clipboard Text

Plain text uses 617 UTF-8.

---

# 127. Clipboard Lifetime

Clipboard contents may outlive the application depending on platform.

---

# 128. Clipboard Cancellation

Large clipboard transfers support cancellation.

---

# 129. Drag-and-Drop

```text
DragSource
DropTarget
DragSession
DropPayload
```

---

# 130. Drag Lifecycle

```text
Start
Enter
Over
Leave
Drop
Cancel
```

---

# 131. Drag Effects

```text
Copy
Move
Link
None
```

---

# 132. Drop Validation

Drop targets explicitly advertise accepted formats.

---

# 133. File Drops

File references are capability-checked through 603.

---

# 134. External Drops

External applications are untrusted sources.

---

# 135. Native File Dialog

619 defines a portable abstraction:

```text
OpenFileDialog
SaveFileDialog
SelectFolderDialog
```

---

# 136. Dialog Provider

Native platform dialogs may be used through:

```text
DialogProvider
```

---

# 137. Custom Dialog Fallback

Axiom can provide a toolkit-rendered fallback when native dialogs are unavailable.

---

# 138. File Dialog Security

Selected files become explicit filesystem capabilities.

---

# 139. Dialog Result

A successful selection returns capability-safe file handles/paths according to 603/611 policy.

---

# 140. Window Integration

Each GUI context attaches to a 615 `Window`.

---

# 141. Window State

619 can expose:

```text
Normal
Minimized
Maximized
Fullscreen
Hidden
```

through the window boundary.

---

# 142. Window Decorations

Platform-native decorations remain under 615/platform control.

---

# 143. Client Area

619 controls the application content area.

---

# 144. Custom Title Bar

Applications may request custom title-bar rendering where the platform allows it.

---

# 145. Window Commands

Commands:

```text
Minimize
Maximize
Restore
Close
Move
Resize
```

---

# 146. Window Lifecycle

GUI state follows:

```text
Created
Shown
Active
Inactive
Suspended
Closing
Closed
```

---

# 147. Shutdown

Window close requests may be vetoed by application state.

---

# 148. Forced Shutdown

OS-forced termination cannot be blocked indefinitely.

---

# 149. Multi-Window

Applications may create multiple windows.

Each window has its own:

```text
root UI tree
focus state
layout
render surface
```

---

# 150. Shared Resources

Windows can share:

```text
Theme
Fonts
Commands
Clipboard
Application State
```

---

# 151. Window Groups

Related windows may belong to a logical group.

---

# 152. Modal Ownership

Dialogs may be owned by a parent window.

---

# 153. Z-Order

Window z-order is managed by 615/OS.

Popup z-order is managed by GUI runtime within the application's permitted surface.

---

# 154. Multi-Monitor

Window and UI layout account for monitor DPI from 615.

---

# 155. Display Scale

Changing DPI triggers layout invalidation.

---

# 156. Text Integration

All GUI text uses 617.

---

# 157. Font Fallback

GUI controls inherit 617 font fallback.

---

# 158. Localization

Controls can bind to localization IDs rather than hard-coded text.

---

# 159. RTL

The UI tree supports:

```text
LTR
RTL
Auto
```

layout direction.

---

# 160. Mirroring

Directional UI layouts can mirror:

```text
left/right
leading/trailing
```

while preserving semantic ordering.

---

# 161. Logical Directions

Layout uses:

```text
Start
End
Before
After
```

where appropriate.

---

# 162. Localization Reload

Changing locale can invalidate:

```text
text
layout
accessibility tree
```

without reconstructing the whole application.

---

# 163. Input Integration

618 events enter the GUI tree through the event router.

---

# 164. Text Input Integration

IME composition is routed to the focused text control.

---

# 165. Pointer Integration

Hit testing maps pointer coordinates to UI nodes.

---

# 166. Hit Testing

Hit testing considers:

```text
visibility
enabled
bounds
clip
z-order
pointer-events policy
```

---

# 167. Transparent Controls

A visual element may be:

```text
HitTestable
NonHitTestable
```

independently of visibility.

---

# 168. Pointer Events

Controls can opt into:

```text
hover
press
release
drag
wheel
```

---

# 169. Keyboard Events

Focused controls receive keyboard events through 618 routing.

---

# 170. Command Translation

A control may translate keyboard/pointer input into a `UiCommand`.

---

# 171. Undo/Redo Boundary

Text controls expose edit transactions to higher-level undo managers.

---

# 172. UI State

State is separate from visual rendering.

---

# 173. Binding

Optional binding abstraction:

```text
Binding<T>
```

connects UI properties to application state.

---

# 174. One-Way Binding

```text
State → UI
```

---

# 175. Two-Way Binding

```text
State ↔ UI
```

---

# 176. Binding Validation

Invalid values produce typed validation state.

---

# 177. No Hidden Global State

UI bindings are explicitly scoped.

---

# 178. State Updates

Multiple state changes can be batched into one layout/render transaction.

---

# 179. UI Transaction

```text
UiTransaction {
    state_changes
    invalidations
    accessibility_updates
}
```

---

# 180. Render Scheduling

The runtime coalesces multiple updates before the next frame where appropriate.

---

# 181. Frame Integration

615 controls presentation.

619 schedules UI updates and render invalidation.

---

# 182. Frame Budget

The UI runtime exposes frame timing diagnostics.

---

# 183. Slow Handler Detection

602 can report handlers exceeding configured latency budgets.

---

# 184. UI Freeze Detection

605/602 can detect an unresponsive UI executor.

---

# 185. Resource Budgets

606 limits:

```text
UI nodes
layout memory
textures
glyph caches
clipboard data
drag payloads
animations
```

---

# 186. Large UI Trees

The runtime supports virtualization and incremental layout.

---

# 187. Custom Controls

Developers can compose controls without subclassing.

---

# 188. Control Composition

Example:

```text
struct SearchBox {
    container: Row
    icon: Image
    field: TextField
    clear: Button
}
```

---

# 189. Behavior Traits

Controls can implement traits:

```text
Focusable
Clickable
Selectable
Scrollable
Editable
```

---

# 190. Override Model

Because Axiom uses struct-only composition, behavior replacement is achieved through explicit function/provider binding rather than class inheritance.

---

# 191. Example Override

```text
struct MyButton {
    base: Button
}

fn MyButton.on_activate(self, ctx: UiContext) {
    ...
}
```

---

# 192. Event Hook

Custom controls can override behavior through explicit hooks:

```text
on_pointer
on_key
on_text
on_focus
on_render
```

---

# 193. No Virtual Method Requirement

Compiler can statically dispatch hooks where concrete type is known.

---

# 194. Dynamic UI Components

Dynamic dispatch is available only when explicitly requested.

---

# 195. UI Component Lifetime

Components use explicit ownership.

No tracing GC is required.

---

# 196. Resource Disposal

Controls release:

```text
subscriptions
GPU resources
timers
clipboard providers
drag sessions
```

during disposal.

---

# 197. Async UI

Async operations must not block the UI thread.

---

# 198. Async Completion

Background operations post results back to the owning UI context.

---

# 199. Cancellation

Closing a UI component can cancel associated asynchronous work.

---

# 200. UI Task Ownership

Tasks may be associated with a UI scope.

Destroying the scope cancels owned tasks unless detached explicitly.

---

# 201. Dialog Async API

```text
let result = await dialog.show()
```

must lower to an executor-compatible state machine.

---

# 202. No Hidden Blocking

GUI APIs do not silently block the UI thread on network/filesystem operations.

---

# 203. File Dialog Async

Native file dialogs can expose asynchronous completion.

---

# 204. Clipboard Async

Large clipboard transfers can be asynchronous.

---

# 205. Drag-and-Drop Async

External data retrieval can be asynchronous and cancellable.

---

# 206. Accessibility Async

Accessibility providers can receive incremental updates asynchronously.

---

# 207. Serialization

UI state may be serialized when explicitly requested.

---

# 208. UI Checkpoint

600 may checkpoint:

```text
window preferences
selected tab
splitter positions
non-sensitive UI state
```

but not live OS handles.

---

# 209. Recovery

After application restart:

```text
UI state
 ↓
recreate windows
 ↓
recreate controls
 ↓
restore safe state
```

---

# 210. Security

UI controls must not automatically gain capabilities merely because they exist.

---

# 211. Capability Boundary

File/network/process operations still require 603 capabilities.

---

# 212. Untrusted UI Content

Text/HTML imported into a UI remains data.

---

# 213. No Arbitrary Markup Execution

The native style/resource format cannot execute arbitrary code.

---

# 214. Resource Loading

Themes/icons/fonts/localization use 611/613 capability-safe loading.

---

# 215. Image Resources

Images are loaded through 615/613 with resource limits.

---

# 216. Clipboard Security

Clipboard content is treated as untrusted external data.

---

# 217. Drag Security

Dropped paths do not automatically grant arbitrary directory access.

---

# 218. Accessibility Security

Accessibility APIs can expose sensitive content.

Applications can mark nodes:

```text
Sensitive
Private
HiddenFromAccessibility
```

where platform semantics permit.

---

# 219. Password Accessibility

Password controls follow platform accessibility conventions without exposing secret contents unnecessarily.

---

# 220. UI Diagnostics

602 tracks:

```text
layout duration
render duration
event dispatch
input latency
frame drops
binding updates
accessibility updates
```

---

# 221. UI Inspection

Development mode can inspect:

```text
tree
bounds
styles
focus
layout constraints
accessibility
render regions
```

---

# 222. UI Inspector

Optional:

```text
axiom ui inspect
```

---

# 223. Deterministic UI Testing

619 provides:

```text
UiTestContext
```

with virtual:

```text
window
clock
input
clipboard
filesystem
dialog provider
```

---

# 224. Screenshot Testing

A test can render a UI to an offscreen 615 surface.

---

# 225. Golden Tests

Golden rendering tests can pin:

```text
font
DPI
theme
rasterizer
locale
```

for reproducibility.

---

# 226. Semantic UI Tests

Tests can inspect accessibility roles/values without relying on pixels.

---

# 227. Input Tests

Tests can inject logical 618 events.

---

# 228. Layout Tests

Tests can assert:

```text
bounds
alignment
overflow
visibility
```

---

# 229. Accessibility Tests

Tests can verify:

```text
role
name
state
actions
focus order
```

---

# 230. Localization Tests

Tests can switch locale and verify:

```text
text
layout
RTL
pluralization
```

---

# 231. Stress Tests

Stress:

- 100,000 list items;
- rapid resizing;
- DPI changes;
- theme changes;
- locale changes;
- device removal;
- repeated dialog creation;
- clipboard transfers.

---

# 232. Fuzzing

Fuzz:

```text
layout constraints
style resources
localization data
clipboard payloads
drag payloads
accessibility trees
event sequences
```

---

# 233. Cross-Platform Backends

Platform window/input/accessibility providers:

```text
Windows
Linux
macOS
iOS
Android
WASM
Embedded
```

---

# 234. Native vs Portable Controls

619 controls are portable semantic controls.

A native provider can map selected controls to OS-native widgets where appropriate.

---

# 235. Native Widget Adapter

```text
NativeControlProvider
```

may provide:

```text
NativeTextField
NativeMenu
NativeDialog
NativeAccessibility
```

---

# 236. Rendering Policy

Application chooses:

```text
PortableRendered
NativeControl
Hybrid
```

per component/context.

---

# 237. Hybrid UI

An application may combine native dialogs with custom-rendered controls.

---

# 238. WebAssembly

WASM can use:

```text
Canvas/WebGPU
DOM boundary
browser accessibility
```

through a provider.

---

# 239. Embedded GUI

Embedded systems can use the same semantic UI tree with framebuffer/GPU providers.

---

# 240. Server GUI

Server binaries can exclude 619 entirely unless remote GUI functionality is explicitly required.

---

# 241. Package Integration

AXPK may contain:

```text
theme
icons
fonts
localization
images
cursor resources
```

---

# 242. Resource URI

GUI resources use package/VFS URIs rather than arbitrary filesystem paths where possible.

---

# 243. Theme Version

`.axtheme` includes:

```text
schema_version
theme_id
dependencies
```

---

# 244. Accessibility Metadata

Themes cannot remove required accessibility semantics.

---

# 245. Compiler Integration

Compiler metadata:

```text
@ui
@control
@theme
@accessibility
@command
```

may assist tooling.

---

# 246. UI Schema

Optional generated metadata:

```text
.axui
```

contains:

```text
controls
bindings
commands
accessibility
resources
```

---

# 247. Code Generation

Typed UI definitions can generate:

```text
control IDs
command IDs
binding types
localization IDs
```

---

# 248. Dead Stripping

Unused controls/layout engines/theme systems should be removable.

---

# 249. Minimal GUI Profile

A simple application can link only:

```text
Window
Text
Button
Stack
Input
```

without table/tree/editor infrastructure.

---

# 250. Rich GUI Profile

An IDE/editor can enable:

```text
Docking
Tree
Table
Virtualization
Menus
Toolbars
Dialogs
Accessibility
```

---

# 251. Game UI Profile

A game may use:

```text
Canvas
Text
Image
Button
Input
Gamepad
```

without desktop-native controls.

---

# 252. Accessibility-First Profile

An application can enable the semantic accessibility layer even with custom rendering.

---

# 253. UI ABI

Stable native boundaries include:

```text
UiNodeHandle
WindowHandle
CommandId
ControlId
AccessibilityNodeId
```

with generation-safe handles.

---

# 254. No Raw Native Widget Pointers

Platform widgets are hidden behind provider handles.

---

# 255. Plugin Boundary

UI plugins require explicit trust/capabilities.

---

# 256. Supervision

Long-running UI provider failures can be reported to 605.

---

# 257. UI Recovery

A failed noncritical provider may be recreated without destroying application state when feasible.

---

# 258. Shutdown Ordering

```text
Stop new input
 ↓
cancel UI tasks
 ↓
close dialogs
 ↓
dispose controls
 ↓
destroy UI tree
 ↓
release surfaces
 ↓
destroy windows
```

---

# 259. Resource Ownership

Every UI resource has an explicit owner or scope.

---

# 260. No Hidden Global Singleton Requirement

`GuiApplication` may be the root object, but the implementation does not require a global singleton.

---

# 261. Threading

UI mutations are serialized by the owning `UiContext`.

Background work uses 607.

---

# 262. Synchronization

Shared immutable UI resources may be used concurrently.

Mutable tree state remains UI-context confined.

---

# 263. Performance

Target:

- O(visible nodes) rendering;
- incremental layout;
- virtualized large collections;
- low allocation event dispatch;
- no global UI lock;
- cached style resolution;
- cached text layout;
- GPU batching where possible.

---

# 264. Rendering Batching

Compatible controls should batch:

```text
rectangles
images
glyphs
```

into efficient 615 command buffers.

---

# 265. Draw Order

Rendering follows visual-tree z-order and clipping.

---

# 266. Clip Stack

Controls can establish clipping rectangles/path boundaries.

---

# 267. Transform Stack

Nested UI elements may apply transforms.

---

# 268. Opacity

Opacity can be inherited and composited.

---

# 269. Layer Promotion

Expensive/effect-heavy controls may be promoted to offscreen surfaces.

---

# 270. Cache Surfaces

Static UI regions may use cached render surfaces.

---

# 271. Cache Invalidation

Changes to a cached subtree invalidate only the affected cache.

---

# 272. Input/Render Separation

Rendering a UI tree must not mutate logical input state.

---

# 273. Layout/Render Separation

Rendering must consume layout results rather than changing layout during drawing.

---

# 274. Determinism

Given the same:

```text
UI state
theme
locale
font set
DPI
input sequence
```

the semantic UI result must be deterministic.

---

# 275. Final Invariants

1. GUI is retained-mode by default.
2. UI nodes use generation-safe identities.
3. GUI controls are structs/traits, not mandatory classes.
4. Input routing uses 618.
5. Text uses 617.
6. Rendering uses 615.
7. File/device/network access uses existing capabilities.
8. UI mutation is context-confined.
9. Background work uses 607.
10. No hidden blocking on the UI thread.
11. Layout is constraint based.
12. Layout and rendering are separate phases.
13. Large collections are virtualizable.
14. Accessibility is semantic and independent of visual representation.
15. Clipboard data is untrusted.
16. Drag-and-drop data is untrusted.
17. Native dialogs are capability-aware.
18. RTL is a first-class layout direction.
19. Localization can invalidate UI text/layout incrementally.
20. UI state is separate from rendering.
21. UI state can be checkpointed without serializing native handles.
22. Theme is typed data.
23. Themes cannot execute arbitrary code.
24. Animations respect reduced-motion settings.
25. Global input capture remains privileged.
26. Sensitive UI can be marked.
27. Rendering is DPI-aware.
28. Dead stripping removes unused GUI subsystems.
29. No GC is required.
30. Cross-platform behavior is implemented through providers.

---

# 276. Acceptance Criteria

### Window/UI

1. GuiApplication.
2. UiContext.
3. Window integration.
4. UiNode.
5. UiTree.
6. generation-safe IDs.
7. multiple windows.
8. modal windows.
9. popup surfaces.
10. lifecycle.

### Controls

11. Label.
12. Button.
13. ToggleButton.
14. CheckBox.
15. RadioButton.
16. TextField.
17. MultilineTextField.
18. PasswordField.
19. NumericField.
20. Slider.
21. ProgressBar.
22. ScrollView.
23. List.
24. Tree.
25. Table.
26. TabControl.
27. Menu.
28. Toolbar.
29. Dialog.
30. Tooltip.

### Layout

31. Measure.
32. Arrange.
33. Render.
34. Stack.
35. Row.
36. Column.
37. Grid.
38. Flow.
39. Overlay.
40. Dock.
41. constraints.
42. DPI.
43. RTL.
44. incremental invalidation.
45. virtualization.

### Styling

46. Theme.
47. Style.
48. state styles.
49. inheritance.
50. theme serialization.
51. dark/light.
52. high contrast.
53. reduced motion.
54. focus styling.
55. resource packaging.

### Input

56. keyboard routing.
57. pointer routing.
58. touch.
59. pen.
60. gamepad.
61. IME.
62. focus.
63. capture.
64. gesture.
65. command routing.

### Accessibility

66. semantic tree.
67. roles.
68. states.
69. actions.
70. values.
71. labels.
72. relations.
73. live regions.
74. keyboard accessibility.
75. platform adapter.

### Clipboard/Drag

76. clipboard.
77. text.
78. image.
79. file payload.
80. custom formats.
81. lazy clipboard.
82. drag source.
83. drop target.
84. drag effects.
85. payload validation.

### Dialogs

86. open file.
87. save file.
88. select folder.
89. modal dialog.
90. modeless dialog.
91. native provider.
92. custom fallback.
93. capability-safe results.
94. async dialog.
95. cancellation.

### Performance

96. incremental layout.
97. dirty regions.
98. render batching.
99. glyph reuse.
100. virtualized lists.
101. bounded memory.
102. low allocation.
103. no global UI lock.
104. async operations.
105. UI frame diagnostics.

### Security

106. capability boundaries.
107. untrusted clipboard.
108. untrusted drop.
109. secure text input.
110. accessibility privacy.
111. native dialog security.
112. plugin restrictions.
113. resource limits.
114. theme sandbox.
115. privileged operations.

### Testing

116. fake UI context.
117. virtual input.
118. layout tests.
119. semantic accessibility tests.
120. screenshot tests.
121. golden rendering.
122. localization tests.
123. RTL tests.
124. DPI tests.
125. stress tests.
126. fuzzing.

### Cross-Platform

127. Windows.
128. Linux.
129. macOS.
130. iOS.
131. Android.
132. WASM.
133. embedded.
134. native widget provider.
135. portable renderer.
136. hybrid UI.

---

# 277. Final Architecture

```text
                         APPLICATION
                              │
                              ▼
                       GuiApplication
                              │
                       ┌──────┴──────┐
                       ▼             ▼
                   UiContext      Commands
                       │
                       ▼
                     UiTree
                       │
       ┌───────────────┼─────────────────┐
       ▼               ▼                 ▼
    Controls         Layout            Style
       │               │                 │
       └───────────────┼─────────────────┘
                       ▼
                 Event / Focus
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
            618       617      615
           Input      Text    Graphics
              │        │        │
              └────────┼────────┘
                       ▼
                  OS / Device
```

Cross-cutting:

```text
600 State
602 Diagnostics
603 Security
604 IPC
605 Supervision
606 Resources
607 Async
608 Sync
611 Storage
612 Serialization
613 Packaging
614 Devices
```

---

# 278. Architectural Decision

BOOTSTRAP-619 establishes the first complete **native application GUI layer** for Axiom.

The key design decision is to avoid both extremes:

```text
Pure OS-native widgets
```

would make Axiom heavily platform-dependent.

While:

```text
Pure custom rendering
```

would force every application to rebuild accessibility, IME, focus, dialogs and desktop interaction.

Axiom therefore uses a **semantic cross-platform UI tree + portable renderer + optional native providers**:

```text
               Axiom UI
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
    Portable   Native    Hybrid
    Controls   Provider  Controls
        │         │         │
        └─────────┼─────────┘
                  ▼
             Platform
```

This allows the same application architecture to target Windows, Linux, macOS, iOS, Android, WASM and embedded systems while preserving native integration where it provides real value.

---

# 279. Task Completion

**BOOTSTRAP-619 — COMPLETE**

**Next queued task: BOOTSTRAP-620 — Native Application Data Binding, Reactive State, UI State Synchronization, Commands, Undo/Redo & Model/View Runtime 5.0**
:::