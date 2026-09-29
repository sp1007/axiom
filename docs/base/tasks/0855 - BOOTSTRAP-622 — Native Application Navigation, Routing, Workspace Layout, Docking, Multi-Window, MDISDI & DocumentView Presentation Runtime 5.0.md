Tiếp tục với **BOOTSTRAP-622** — lớp presentation/workspace phía trên Document và GUI, tập trung vào navigation, docking, multi-window và quản lý bố cục ứng dụng phức tạp.

:::writing{variant="document" id="31687" title="BOOTSTRAP-622 — Native Application Navigation, Routing, Workspace Layout, Docking, Multi-Window, MDI/SDI & Document/View Presentation Runtime 5.0"}
# BOOTSTRAP-622 — Native Application Navigation, Routing, Workspace Layout, Docking, Multi-Window, MDI/SDI & Document/View Presentation Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Native Application Presentation / Workspace Runtime  
**Depends on:** BOOTSTRAP-600 → 621

---

# 1. Purpose

BOOTSTRAP-622 defines the application-level presentation runtime above:

- BOOTSTRAP-619 GUI;
- BOOTSTRAP-620 State/Binding/Commands;
- BOOTSTRAP-621 Documents/History/Recovery.

It provides the infrastructure for applications containing:

- multiple windows;
- documents and document views;
- navigation;
- routes;
- tabs;
- docking panels;
- split views;
- tool windows;
- floating windows;
- MDI/SDI/hybrid presentation;
- workspaces;
- layout persistence;
- window restoration;
- presentation history;
- modal/non-modal navigation;
- deep links;
- URI-based application state.

It does **not** mandate a particular application UI architecture.

---

# 2. Design Principle

The core separation is:

```text
Document
    ≠
DocumentView
    ≠
Window
    ≠
Workspace
    ≠
NavigationEntry
```

A document may have multiple views.

A view may move between windows.

A window may belong to different workspaces over time.

Navigation state records presentation history, not ownership of domain data.

---

# 3. Layering

```text
Application
     │
     ▼
ApplicationShell
     │
 ┌───┼──────────────┐
 ▼   ▼              ▼
Router Workspace  WindowManager
 │      │              │
 ▼      ▼              ▼
Route  Layout        Windows
 │      │              │
 └──────┼──────────────┘
        ▼
   Document/View
        │
        ▼
       619
```

---

# 4. Core Objects

```text
ApplicationShell
NavigationManager
Router
Route
RouteId
RoutePattern
RouteValue
NavigationEntry
NavigationStack
NavigationHistory
NavigationRequest
NavigationResult
NavigationGuard
NavigationTransition
WindowManager
WindowGroup
Window
WindowState
Workspace
WorkspaceId
WorkspaceLayout
DockTree
DockNode
DockPanel
SplitNode
TabGroup
TabItem
FloatingPanel
ToolWindow
DocumentViewHost
ViewPlacement
Presentation
PresentationMode
```

---

# 5. Application Shell

```text
ApplicationShell
```

represents the application-level presentation environment.

It coordinates:

- windows;
- workspace;
- routing;
- commands;
- lifecycle;
- state restoration.

---

# 6. Shell Ownership

The shell owns presentation infrastructure but does not own domain documents unless explicitly configured.

---

# 7. Navigation

Navigation is a transition from one presentation state to another.

---

# 8. Route

A route identifies a destination.

Example:

```text
/editor/document/42
/settings/audio
/project/7/assets
```

---

# 9. Route Identity

```text
RouteId
```

is a stable application-defined identifier.

---

# 10. Route Pattern

A route can contain typed parameters:

```text
/project/{project_id}/document/{document_id}
```

---

# 11. Typed Route Values

Route parameters are strongly typed.

Example:

```text
document_id: DocumentId
```

rather than an unvalidated string.

---

# 12. Route Parsing

Invalid route parameters produce a typed navigation error.

---

# 13. Route Serialization

Routes can serialize to:

- URI;
- application deep-link format;
- workspace state.

---

# 14. URI Boundary

External URI parsing is treated as untrusted input.

---

# 15. Route Registration

Applications register routes explicitly.

---

# 16. No Mandatory Reflection

Route registration can be generated statically by the compiler.

---

# 17. Route Metadata

Compiler metadata may generate:

```text
.axroute
```

containing:

```text
route_id
pattern
parameter_types
required_capabilities
destination
```

---

# 18. Navigation Manager

```text
NavigationManager
```

provides:

```text
navigate
back
forward
replace
reload
reset
```

---

# 19. Navigation Entry

Each navigation entry contains:

```text
NavigationEntry {
    route
    presentation
    state
    timestamp
}
```

---

# 20. Navigation Stack

A stack represents sequential navigation.

```text
A → B → C
```

Back navigation returns:

```text
C → B
```

---

# 21. Navigation History

History is independent from document history.

---

# 22. Document History vs Navigation History

```text
Document History:
edit A → edit B → edit C

Navigation:
document A → settings → document B
```

They must never be conflated.

---

# 23. Back

Back removes the current navigation entry when policy permits.

---

# 24. Forward

Forward restores an entry invalidated by a back operation.

---

# 25. Divergent Navigation

Navigating to a new destination after back clears the normal forward branch.

---

# 26. Navigation Branches

Optional advanced history can retain branches.

---

# 27. Replace

`replace()` changes the current entry without adding a new history item.

---

# 28. Reset

`reset()` replaces the navigation stack with a new root state.

---

# 29. Navigation Request

```text
NavigationRequest {
    destination
    parameters
    presentation
    source
    options
}
```

---

# 30. Navigation Result

```text
NavigationResult {
    Completed
    Rejected
    Cancelled
    Failed
    Deferred
}
```

---

# 31. Navigation Guard

A guard can inspect a navigation request.

---

# 32. Guard Use Cases

Examples:

- unsaved document;
- authentication;
- permission;
- required resource;
- pending transaction.

---

# 33. Guard Must Be Explicit

Navigation must not silently block forever.

---

# 34. Async Guard

Guards may return:

```text
Future<NavigationDecision>
```

through 607.

---

# 35. Guard Cancellation

Navigation requests carry cancellation.

---

# 36. Guard Ordering

Guards execute in deterministic order.

---

# 37. Guard Failure

A failed guard produces a diagnostic and rejected navigation.

---

# 38. Navigation Transaction

Navigation itself can be transactional.

```text
Prepare
Validate
Commit Presentation
```

---

# 39. Presentation Transaction

A navigation transaction must not leave half-created windows or views.

---

# 40. Rollback

If destination creation fails, presentation state returns to its previous valid state.

---

# 41. Destination

A route resolves to a destination provider.

```text
DestinationProvider
```

---

# 42. Destination Provider

Responsible for creating:

- view;
- document view;
- tool panel;
- dialog;
- window;
- workspace.

---

# 43. Lazy Destination

Destinations may be instantiated only when navigated to.

---

# 44. Resource Control

Unused destinations should not remain alive solely because their route exists.

---

# 45. Route State

A route can carry transient presentation state.

---

# 46. Route State Example

```text
/editor/document/42?cursor=100&line=20
```

The application decides which parameters are durable.

---

# 47. Navigation State

Navigation entries may preserve:

- scroll;
- selection;
- focused control;
- query;
- filter;
- zoom.

---

# 48. State Separation

Document content remains in 621.

Presentation state remains in 622/619.

---

# 49. Window Manager

```text
WindowManager
```

controls application windows.

---

# 50. Window Identity

Windows have:

```text
WindowId
WindowGeneration
```

---

# 51. Window Groups

A `WindowGroup` groups windows belonging to one application/session.

---

# 52. Window Roles

```text
Main
Document
Tool
Dialog
Popup
Utility
Inspector
Preview
Floating
```

---

# 53. Window Ownership

A child window can explicitly reference its owner window.

---

# 54. Parent/Owner Relationship

Closing an owner may close owned transient windows according to policy.

---

# 55. Window Lifetime

Window lifetime is separate from document lifetime.

---

# 56. Multi-Window

One document can be displayed in multiple windows.

```text
Document
 ├── Window A
 └── Window B
```

---

# 57. Single-Window

An application can enforce:

```text
one document → one presentation
```

through policy.

---

# 58. SDI

Single Document Interface can be represented as:

```text
Window
 └── DocumentView
```

---

# 59. MDI

Multiple Document Interface can be represented as:

```text
Window
 └── Workspace
      ├── DocumentView A
      ├── DocumentView B
      └── DocumentView C
```

---

# 60. Hybrid

A hybrid application may use:

```text
Main Window
 ├── document tabs
 ├── docked tools
 └── floating inspectors
```

without a special runtime mode.

---

# 61. Presentation Mode

```text
PresentationMode
```

can specify:

```text
Embedded
Tab
Split
Floating
Window
Dialog
Modal
```

---

# 62. Workspace

A workspace is a persistent presentation environment.

---

# 63. Workspace Identity

```text
WorkspaceId
```

is stable.

---

# 64. Workspace Contents

A workspace may contain:

```text
documents
views
windows
dock panels
tabs
splits
navigation
selection
active item
```

---

# 65. Workspace Does Not Own Document Content

Workspace stores references/placements.

---

# 66. Workspace Layout

```text
WorkspaceLayout
```

is a tree.

---

# 67. Layout Tree

```text
Root
 ├── Split
 │    ├── TabGroup
 │    └── DockPanel
 └── FloatingWindow
```

---

# 68. Dock Tree

The dock layout is represented by:

```text
DockTree
```

---

# 69. Dock Nodes

```text
DockNode
SplitNode
TabNode
PanelNode
PlaceholderNode
```

---

# 70. Split Node

A split contains:

```text
orientation
children
ratios
```

---

# 71. Orientation

```text
Horizontal
Vertical
```

---

# 72. Split Ratio

Ratios are normalized.

---

# 73. Ratio Constraints

Minimum and maximum panel sizes are respected.

---

# 74. Tab Group

A tab group contains ordered views.

---

# 75. Tab Identity

Each tab references a stable:

```text
ViewId
```

---

# 76. Tab State

Tabs may contain:

```text
title
icon
dirty indicator
active state
close policy
```

---

# 77. Tab Title

Document titles come from 621 metadata unless overridden by presentation state.

---

# 78. Dirty Indicator

Dirty status is derived from document revision state.

---

# 79. Tab Close

Closing a tab closes its view/session, not necessarily the document.

---

# 80. Unsaved Close

If the document is dirty, close policy invokes 621 save/decision flow.

---

# 81. Dock Panel

A dock panel can be:

```text
Left
Right
Top
Bottom
Center
```

---

# 82. Dock State

A panel may be:

```text
Docked
Floating
AutoHidden
Hidden
```

---

# 83. Auto-Hide

Auto-hide panels collapse to a tab/strip.

---

# 84. Floating Panel

A floating panel has its own native window where supported.

---

# 85. Tool Window

Tool windows are reusable application panels such as:

- inspector;
- console;
- asset browser;
- navigator;
- properties.

---

# 86. Panel Identity

Tool panels have stable IDs independent from instances.

---

# 87. Panel Factory

```text
PanelProvider
```

creates panel instances.

---

# 88. Multiple Instances

Panels may permit:

```text
SingleInstance
MultipleInstances
```

---

# 89. Singleton Panel

A singleton panel has one active presentation instance per workspace.

---

# 90. Layout Constraints

Workspace layout validates:

- no cycles;
- valid child ownership;
- normalized ratios;
- unique panel/view placement;
- valid window references.

---

# 91. Layout Validation

Invalid persisted layouts are repaired through deterministic fallback.

---

# 92. No Arbitrary Layout Code

Persisted layouts contain data, not executable UI code.

---

# 93. Workspace Serialization

Workspace state uses 612.

---

# 94. Workspace Format

A native workspace may use:

```text
.axworkspace
```

---

# 95. Workspace Metadata

Contains:

```text
workspace_id
schema_version
layout
open_documents
windows
navigation
panel_state
```

---

# 96. Window Placement

Window state may include:

```text
position
size
monitor
DPI
state
fullscreen
```

---

# 97. Cross-Monitor Restoration

If a saved monitor no longer exists, the window is relocated to a valid display.

---

# 98. DPI Restoration

Logical coordinates are preferred over raw physical pixels.

---

# 99. Safe Window Placement

The runtime must prevent restoring a window completely outside available display bounds.

---

# 100. Window State

```text
Normal
Maximized
Minimized
Fullscreen
Hidden
```

---

# 101. Fullscreen

Fullscreen policy is platform-specific through 615.

---

# 102. Modal Presentation

Modal UI blocks interaction with selected presentation scopes.

---

# 103. Application Modal

Blocks the entire application.

---

# 104. Window Modal

Blocks only the owning window.

---

# 105. Document Modal

Blocks interaction with one document presentation.

---

# 106. Modal Ownership

Every modal presentation has an explicit owner.

---

# 107. Non-Modal Dialog

Non-modal dialogs behave as independent windows/views.

---

# 108. Dialog Result

```text
DialogResult<T>
```

returns typed data.

---

# 109. Popup

Popups are transient presentation objects.

---

# 110. Popup Lifetime

Closing/focus loss may close a popup according to explicit policy.

---

# 111. Presentation Stack

Transient presentations may use:

```text
PresentationStack
```

separate from navigation history.

---

# 112. Navigation vs Presentation

A popup opening does not necessarily create a navigation entry.

---

# 113. Deep Linking

External links can map to routes.

---

# 114. Deep-Link Security

External route parameters are validated before creating capabilities or opening resources.

---

# 115. URI Capability

A route itself never grants filesystem/network permissions.

---

# 116. Capability Acquisition

Required capabilities must be obtained through 603.

---

# 117. Navigation Security

Routes may declare required capabilities.

---

# 118. Unauthorized Route

Returns:

```text
NavigationDenied
```

without leaking protected resource details.

---

# 119. Route Aliases

Applications may register aliases.

---

# 120. Route Versioning

Routes can evolve without invalidating old deep links.

---

# 121. Route Migration

A route can redirect:

```text
old route → new route
```

through an explicit migration.

---

# 122. Redirect Loop

Router detects redirect cycles.

---

# 123. Maximum Redirects

A bounded redirect count prevents infinite navigation.

---

# 124. Navigation Events

622 emits:

```text
NavigationStarted
NavigationCommitted
NavigationCancelled
NavigationFailed
NavigationReplaced
```

---

# 125. Window Events

Window lifecycle events integrate with 619/615.

---

# 126. Workspace Events

Workspace changes emit:

```text
LayoutChanged
ViewAttached
ViewDetached
PanelDocked
PanelUndocked
WindowAdded
WindowRemoved
```

---

# 127. Event Coalescing

Rapid layout changes can be coalesced before persistence.

---

# 128. Layout Transactions

Docking operations occur inside layout transactions.

---

# 129. Layout Transaction

```text
Begin
Modify
Validate
Commit
```

---

# 130. Atomic Layout

Observers must not see half-built docking trees.

---

# 131. Undoable Layout

Workspace layout changes may optionally enter 620 undo history.

---

# 132. Layout Undo

Examples:

- dock panel;
- resize split;
- close tab;
- reorder tabs.

---

# 133. Document Undo Separation

Workspace layout undo must not alter document content.

---

# 134. Navigation Undo Separation

Back/forward history is not the same as 620 command undo.

---

# 135. Explicit History Domains

Axiom maintains independent histories:

```text
DocumentHistory
CommandUndoHistory
NavigationHistory
WorkspaceHistory
```

---

# 136. History Interaction

Applications may explicitly compose histories.

---

# 137. Workspace Profiles

Multiple workspace layouts can exist:

```text
Default
Editing
Debugging
Design
Review
```

---

# 138. Workspace Switching

Switching workspaces changes presentation state without closing documents.

---

# 139. Workspace Persistence

Each workspace stores its own layout.

---

# 140. Shared Documents Across Workspaces

A document can be referenced by multiple workspaces.

---

# 141. Workspace Isolation

Workspace-local UI state must not overwrite another workspace's layout.

---

# 142. Workspace Session

A workspace can be:

```text
Active
Inactive
Background
Closed
```

---

# 143. Workspace Activation

Activation restores presentation state.

---

# 144. Workspace Deactivation

The application may persist layout before deactivation.

---

# 145. Workspace Recovery

600 can restore the previous active workspace.

---

# 146. Session Restoration

On restart:

```text
Application
 → Workspace
 → Windows
 → Documents
 → Views
 → Navigation
```

can be restored.

---

# 147. Partial Restoration

If one document fails to load, the rest of the workspace should remain recoverable.

---

# 148. Missing Provider

If a plugin/provider is unavailable, its panel becomes a placeholder.

---

# 149. Placeholder

```text
MissingView
MissingPanel
MissingDocument
```

preserve enough metadata for later recovery.

---

# 150. Plugin Safety

Restoring a workspace must not automatically execute untrusted plugin code.

---

# 151. Workspace Trust

A workspace may declare trusted providers/capabilities.

---

# 152. Layout Security

Workspace files cannot grant capabilities merely by containing references.

---

# 153. Window Security

Window capture/automation permissions remain controlled by 603/614/619.

---

# 154. Accessibility

Workspace navigation integrates with 619 accessibility tree.

---

# 155. Keyboard Navigation

Commands from 620 can navigate:

- next tab;
- previous tab;
- next panel;
- focus document;
- activate workspace.

---

# 156. Command Integration

Examples:

```text
window.new
window.close
workspace.switch
workspace.reset_layout
panel.toggle
panel.dock
tab.next
tab.previous
navigation.back
navigation.forward
```

---

# 157. Command State

`can_execute` reflects current workspace/window/navigation state.

---

# 158. Shortcut Integration

Keyboard shortcuts remain 618/619 concerns.

622 only provides command targets.

---

# 159. Focus

Focus remains owned by 619.

622 may request focus changes.

---

# 160. Document View Host

```text
DocumentViewHost
```

embeds a document view into a presentation slot.

---

# 161. View Placement

```text
ViewPlacement {
    view_id
    workspace_id
    window_id
    dock_node
}
```

---

# 162. Multiple Views

One document can have:

```text
TextView
OutlineView
PreviewView
DiffView
```

simultaneously.

---

# 163. Linked Views

Views can observe the same 621 document state.

---

# 164. View-Specific State

Each view maintains its own:

```text
selection
scroll
zoom
cursor
filter
```

---

# 165. Synchronized Views

Views can synchronize selected state explicitly through 620.

---

# 166. Split Document View

A document can be split into multiple views without duplicating document content.

---

# 167. Preview View

A preview can be read-only.

---

# 168. Editor View

An editor receives write capability only when permitted.

---

# 169. Read-Only View

Read-only views must not expose mutation commands as executable.

---

# 170. Presentation Capability

View capabilities may include:

```text
ViewRead
ViewEdit
ViewClose
ViewDuplicate
ViewMove
```

---

# 171. Drag-and-Drop

619/618 provide interaction events.

622 interprets them for:

- tab reorder;
- panel docking;
- view movement;
- workspace movement.

---

# 172. Dock Preview

During drag, the runtime generates a non-committed preview layout.

---

# 173. Commit Dock

The preview becomes actual layout only after drop confirmation.

---

# 174. Cancel Dock

Cancelled drag restores the previous layout exactly.

---

# 175. Layout Persistence Debounce

Frequent drag/resize changes should not cause one disk write per pixel.

---

# 176. Layout Save Policy

Persist:

```text
AfterIdle
AfterCommit
OnWorkspaceSwitch
OnShutdown
Manual
```

---

# 177. Crash Safety

Workspace persistence uses atomic save/recovery from 600/611.

---

# 178. Autosave

Workspace autosave is independent from document autosave.

---

# 179. Document Save Dialog

Closing a workspace may trigger document save decisions without automatically discarding workspace state.

---

# 180. Close Ordering

Recommended order:

```text
View
→ Session
→ Window/Workspace placement
→ Document
```

but actual document closure depends on shared references.

---

# 181. Application Shutdown

Shutdown coordinates:

```text
622
621
620
619
605
600
```

---

# 182. Shutdown Blocking

A document save or navigation guard may delay shutdown.

---

# 183. Shutdown Timeout

The supervisor/resource layer can impose bounded shutdown time.

---

# 184. Forced Shutdown

Unsaved documents retain recovery data when possible.

---

# 185. Navigation Restoration

Navigation history can be restored after workspace restoration.

---

# 186. History Validation

Restored navigation entries are revalidated against currently available routes/resources.

---

# 187. Invalid History

Invalid entries are discarded individually rather than invalidating the entire workspace.

---

# 188. Navigation Serialization

Only serializable route/state information is persisted.

---

# 189. Non-Serializable State

Ephemeral handles are not persisted.

---

# 190. Native Handles

Window/device/UI handles are reconstructed after restore.

---

# 191. Stable Logical IDs

Persistent state uses logical IDs rather than native pointers/handles.

---

# 192. Handle Reconstruction

After restart:

```text
persistent ID
   ↓
provider lookup
   ↓
new native handle
```

---

# 193. Monitor Restoration

Display identity may change between sessions.

---

# 194. Safe Fallback

Unavailable monitor/window placement falls back to the primary available display.

---

# 195. DPI Scaling

Logical workspace dimensions are converted to current monitor DPI.

---

# 196. Orientation

Rotated displays are handled by 615/OS adapters.

---

# 197. Mobile

Mobile platforms may not support traditional docking.

622 maps workspace concepts onto:

- navigation stacks;
- scenes;
- panes;
- split views.

---

# 198. Android

Android presentation maps to activities/fragments-like host concepts through platform adapters without making them language primitives.

---

# 199. iOS

iOS presentation maps to scenes/navigation/split-view concepts.

---

# 200. WASM

WASM maps windows/workspaces to browser tabs/canvas/panes according to host capability.

---

# 201. Embedded

Embedded targets may expose only a single workspace and display surface.

---

# 202. Desktop

Desktop supports full:

- multi-window;
- docking;
- tabs;
- floating panels;
- MDI;
- SDI.

---

# 203. Headless

Headless applications may use navigation/workspace state without 619 rendering.

---

# 204. Server

Server applications can use route/state machinery without creating windows.

---

# 205. Serialization Schema

`.axworkspace` has:

```text
schema_id
schema_version
workspace_id
windows
layout
views
navigation
metadata
```

---

# 206. Version Migration

Workspace schema migrations are explicit.

---

# 207. Migration Safety

Failed migration leaves the previous workspace file untouched.

---

# 208. Unknown Fields

612 unknown-field preservation allows forward-compatible workspace files.

---

# 209. Deterministic Serialization

Workspace files use deterministic ordering.

---

# 210. Stable Layout IDs

Dock nodes use stable IDs where persistence requires them.

---

# 211. Layout Garbage

Orphaned views/panels are detected.

---

# 212. Orphan Policy

The application can:

```text
Restore
Hide
Placeholder
Remove
```

orphans.

---

# 213. Layout Repair

Repair produces diagnostics.

---

# 214. Layout Validation Complexity

Validation must be proportional to layout tree size.

---

# 215. Navigation Complexity

Route lookup should support near O(1) lookup for static route IDs.

Pattern matching remains bounded by registered route count/pattern complexity.

---

# 216. Window Lookup

Window lookup uses generation-safe IDs.

---

# 217. Workspace Lookup

Workspace lookup uses stable IDs.

---

# 218. No Global UI Lock

Presentation operations should use ownership/executor confinement rather than a global mutex.

---

# 219. Thread Affinity

Window/layout operations normally execute on the UI executor.

---

# 220. Background Preparation

Route resolution, document loading and layout deserialization may run asynchronously.

---

# 221. Commit on UI Executor

Presentation mutation is committed on the owning UI executor.

---

# 222. Stale Navigation

If a navigation request becomes obsolete, its completion cannot overwrite newer navigation state.

---

# 223. Navigation Generation

Each navigation operation has a generation token.

---

# 224. Async Destination

A destination can load data asynchronously before becoming visible.

---

# 225. Cancellation

Leaving a destination can cancel its pending loading operation.

---

# 226. Error Presentation

Navigation errors can map to 619 dialogs/views.

---

# 227. Error Recovery

A failed destination does not corrupt the previous route.

---

# 228. Route Loading

Routes may lazily load document/provider modules.

---

# 229. Package Integration

Providers and workspace resources may come from 613 packages.

---

# 230. Provider Version

Workspace metadata can record provider versions.

---

# 231. Provider Incompatibility

An incompatible provider becomes a missing-provider placeholder.

---

# 232. Plugin Boundary

Provider execution follows 603 capabilities and 605 supervision.

---

# 233. Process Isolation

Untrusted providers may run out-of-process through 604/605.

---

# 234. Diagnostics

602 records:

```text
navigation latency
route resolution
window creation
layout validation
workspace load/save
panel creation
restore failures
provider failures
```

---

# 235. Performance Metrics

Track:

```text
route lookup
layout rebuild
layout persistence
workspace restore
view creation
window creation
```

---

# 236. Layout Incrementality

Small layout changes should not rebuild unrelated layout branches.

---

# 237. Dirty Layout

Only affected nodes become dirty.

---

# 238. Render Integration

619 invalidates rendering after layout commit.

---

# 239. Frame Boundary

Layout mutations can be coalesced before the next 615 frame.

---

# 240. No Render Stall

Workspace persistence must never block rendering unnecessarily.

---

# 241. Testing

622 provides:

```text
NavigationTestContext
WorkspaceTestContext
LayoutTestContext
WindowTestContext
```

---

# 242. Deterministic Navigation

Tests can use fake:

- clock;
- executor;
- window provider;
- document provider.

---

# 243. Route Tests

Test:

- matching;
- typed parameters;
- invalid parameters;
- redirects;
- guards;
- cancellation;
- history.

---

# 244. Layout Tests

Test:

- docking;
- undocking;
- split;
- resize;
- reorder;
- floating;
- serialization;
- migration.

---

# 245. Restoration Tests

Simulate:

- missing monitor;
- missing provider;
- missing document;
- corrupt layout;
- outdated schema.

---

# 246. Crash Tests

Simulate crash during:

- workspace save;
- document save;
- navigation;
- layout persistence.

---

# 247. Security Tests

Verify:

- route capability isolation;
- malicious URI;
- malformed workspace;
- provider trust;
- unauthorized document access.

---

# 248. Property Tests

Required properties include:

```text
serialize(deserialize(layout)) == canonical(layout)
```

and:

```text
apply(layout_change, layout) == expected_layout
```

---

# 249. Navigation Property

For a valid stack:

```text
navigate(A)
navigate(B)
back()
```

restores A's presentation state.

---

# 250. Forward Property

```text
A → B → back → forward
```

restores B when no divergent navigation occurred.

---

# 251. Divergence Property

```text
A → B → back → C
```

clears the normal forward path.

---

# 252. Multi-View Property

Closing one view must not invalidate other views of the same document.

---

# 253. Window Property

Closing a window must not destroy documents still referenced by another window/session.

---

# 254. Workspace Property

Switching workspace must not mutate another workspace's layout.

---

# 255. Persistence Property

A successfully restored workspace must contain only validated logical state.

---

# 256. Resource Property

Workspace restoration must obey 606 resource limits.

---

# 257. Security Property

Workspace data cannot grant capabilities.

---

# 258. Performance Property

Docking one panel should not require rebuilding unrelated workspace branches.

---

# 259. Acceptance Criteria

### Navigation

1. Route registration.
2. typed route values.
3. route parsing.
4. route serialization.
5. navigation request.
6. navigation result.
7. navigation stack.
8. back.
9. forward.
10. replace.
11. reset.
12. guards.
13. async guards.
14. cancellation.
15. redirect.
16. redirect-loop detection.
17. navigation generations.
18. history persistence.
19. deep links.
20. invalid route handling.

### Windows

21. WindowManager.
22. WindowId.
23. generation.
24. window ownership.
25. window groups.
26. multi-window.
27. SDI.
28. MDI.
29. hybrid presentation.
30. modal window.
31. non-modal window.
32. dialog.
33. popup.
34. floating window.
35. monitor restoration.
36. DPI restoration.
37. safe placement.
38. fullscreen.
39. window lifecycle.
40. shutdown integration.

### Workspace

41. Workspace.
42. WorkspaceId.
43. workspace layout.
44. dock tree.
45. split node.
46. tab node.
47. panel node.
48. floating panel.
49. auto-hide.
50. tab ordering.
51. split ratios.
52. layout constraints.
53. layout validation.
54. layout repair.
55. workspace profiles.
56. workspace switching.
57. workspace persistence.
58. workspace recovery.
59. missing provider placeholders.
60. orphan handling.

### Documents/Views

61. document view host.
62. multiple views.
63. multi-window document.
64. view placement.
65. document/session separation.
66. view state.
67. document state.
68. read-only view.
69. editable view.
70. split document view.

### Commands

71. window commands.
72. panel commands.
73. tab commands.
74. navigation commands.
75. workspace commands.
76. command state.
77. command routing.
78. shortcut integration.
79. undoable layout.
80. separate history domains.

### Persistence

81. `.axworkspace`.
82. schema version.
83. deterministic serialization.
84. migration.
85. unknown field handling.
86. atomic save.
87. crash recovery.
88. layout debounce.
89. autosave.
90. partial restoration.

### Security

91. route capability declaration.
92. URI validation.
93. capability separation.
94. provider trust.
95. workspace trust.
96. malformed workspace protection.
97. parser limits.
98. plugin isolation.
99. document access controls.
100. no capability escalation.

### Async/Resources

101. async destination.
102. cancellation.
103. stale completion prevention.
104. UI executor confinement.
105. background route resolution.
106. resource quotas.
107. bounded history.
108. layout update coalescing.
109. no global UI lock.
110. non-blocking persistence.

### Diagnostics

111. route timing.
112. layout timing.
113. restore diagnostics.
114. provider diagnostics.
115. window diagnostics.
116. navigation tracing.
117. repair reporting.
118. persistence diagnostics.
119. security diagnostics.
120. resource diagnostics.

### Cross-Platform

121. Windows.
122. Linux.
123. macOS.
124. Android.
125. iOS.
126. WASM.
127. embedded.
128. headless.
129. desktop docking.
130. mobile mapping.

### Testing

131. deterministic navigation.
132. route tests.
133. guard tests.
134. layout tests.
135. serialization tests.
136. migration tests.
137. restoration tests.
138. multi-view tests.
139. multi-window tests.
140. crash tests.
141. security fuzzing.
142. malformed workspace fuzzing.
143. route fuzzing.
144. property tests.
145. performance tests.

---

# 260. Final Architecture

```text
                         APPLICATION
                              │
                              ▼
                    APPLICATION SHELL
                              │
          ┌───────────────────┼──────────────────┐
          ▼                   ▼                  ▼
       ROUTER             WORKSPACE         WINDOW MANAGER
          │                   │                  │
          ▼                   ▼                  ▼
    Navigation         WorkspaceLayout       Windows
       Stack                 │                  │
          │            ┌─────┼─────┐            │
          │            ▼     ▼     ▼            │
          │          Dock  Tabs  Panels         │
          │            │     │     │            │
          └────────────┼─────┼─────┼────────────┘
                       ▼     ▼     ▼
                     VIEWS / PRESENTATIONS
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                DOCUMENTS            UI STATE
                    │                   │
                   621                 620
                    │                   │
                    └─────────┬─────────┘
                              ▼
                             619
                              │
                             615
```

Cross-cutting:

```text
600  State / Recovery
602  Diagnostics
603  Security
604  IPC
605  Supervision
606  Resources
607  Scheduler / Async
608  Synchronization
609  Network
610  Crypto
611  Storage
612  Serialization
613  Package / CAS
614  Devices
615  Graphics
617  Text
618  Input
619  GUI
620  State / Binding / Commands / Undo
621  Documents / Revision / Diff / Merge
```

---

# 261. Architectural Decisions

Axiom adopts:

1. **Navigation is separate from document history.**
2. **Workspace layout is separate from document content.**
3. **Windows are presentation containers, not document owners by default.**
4. **One document can have many views.**
5. **One view can move between presentation containers.**
6. **SDI, MDI and hybrid applications use the same primitives.**
7. **Docking is a data structure, not hard-coded GUI behavior.**
8. **Workspace state is serializable and recoverable.**
9. **Native handles are reconstructed rather than persisted.**
10. **Deep links are typed and capability-aware.**
11. **Navigation guards are explicit.**
12. **Async navigation is cancellable and generation-safe.**
13. **Workspace layouts contain data, never executable code.**
14. **Provider failures do not invalidate the entire workspace.**
15. **Document undo and workspace undo remain separate.**
16. **Autosave and document save remain separate.**
17. **No mandatory MDI framework exists.**
18. **No mandatory routing framework exists.**
19. **No mandatory plugin system exists.**
20. **The entire layer can be dead-stripped from headless applications.**

---

# 262. Minimal API Example

```text
struct AppShell {
    router: Router
    workspaces: WorkspaceManager
    windows: WindowManager
}

fn AppShell.open_document(
    self,
    document: DocumentHandle
) -> Future<Result> {
    ...
}

fn AppShell.navigate(
    self,
    route: Route
) -> Future<NavigationResult> {
    ...
}

fn AppShell.switch_workspace(
    self,
    id: WorkspaceId
) -> Result {
    ...
}
```

---

# 263. Typical Editor Architecture

```text
Application
│
├── MainWindow
│   │
│   └── Workspace
│       │
│       ├── DocumentTabs
│       │   ├── DocumentView A
│       │   ├── DocumentView B
│       │   └── DocumentView C
│       │
│       ├── Inspector
│       ├── AssetBrowser
│       ├── Console
│       └── Preview
│
├── NavigationManager
├── DocumentManager
├── CommandManager
└── WorkspaceManager
```

This structure is fully expressible using the 619–622 layers without introducing classes into the Axiom language.

---

# 264. Task Completion

**BOOTSTRAP-622 — COMPLETE**

**Next queued task: BOOTSTRAP-623 — Native Application Plugin, Extension, Module, Hot-Reload, Package Discovery, Dependency Isolation & Extension Runtime 5.0**
:::