# BOOTSTRAP-466 — ACCESSIBILITY, SEMANTIC UI, SCREEN READER, NAVIGATION, AUTOMATION & ASSISTIVE TECHNOLOGY CONTRACT

**Trạng thái: COMPLETED / LOCKED**

466 xây dựng accessibility foundation trên **452 GUI + 464 Text + 465 Input**, nhưng không phụ thuộc vào GUI toolkit cụ thể.

Kiến trúc:

```text
                    Axiom UI
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
        Visual Tree         Semantic Tree
             │                   │
             ↓                   ↓
         Rendering         Accessibility
                                 │
               ┌─────────────────┼────────────────┐
               ↓                 ↓                ↓
         Screen Reader      Navigation       Automation
               │                 │                │
               └─────────────────┴────────────────┘
                                 ↓
                    Platform Accessibility APIs
```

Nguyên tắc nền tảng:

```text
Visual representation
        ≠
Interaction representation
        ≠
Accessibility representation
```

Một UI custom-rendered bằng GPU vẫn phải có thể cung cấp semantic tree cho assistive technology.

---

## 466.1 — Accessibility không thuộc language core

Accessibility nằm ở:

```text
Axiom Core
    ↓
Standard Library
    ↓
GUI / Text / Input
    ↓
Accessibility
    ↓
Platform Accessibility
```

Executable console/headless không tự động link accessibility subsystem.

---

# 466.2 — Semantic tree

Accessibility tree là một semantic representation riêng.

Node:

```text
AccessibleNode {
    id
    role
    name
    description
    value
    state
    bounds
    actions
    children
    parent
}
```

---

## 466.3 — Stable node identity

Mỗi semantic node có `AccessibleId`.

ID phải ổn định trong vòng đời logical element khi có thể.

Không dùng memory address làm semantic identity.

---

## 466.4 — Role

Role mô tả chức năng:

```text
Window
Dialog
Button
Checkbox
Radio
Text
Heading
TextField
List
ListItem
Tree
TreeItem
Table
Row
Cell
Slider
ProgressBar
Menu
MenuItem
Tab
TabPanel
Image
Link
Group
```

Danh sách có thể mở rộng theo platform bridge.

---

## 466.5 — Name

Accessible name là tên mà assistive technology sử dụng để nhận diện element.

Nguồn có thể là:

```text
explicit label
associated label
semantic content
platform-derived name
```

---

## 466.6 — Description

Description cung cấp thông tin bổ sung, không thay thế name.

---

## 466.7 — Value

Controls có thể có semantic value:

```text
text
numeric
range
selection
progress
```

---

## 466.8 — State

State có thể gồm:

```text
enabled
disabled
focused
selected
checked
expanded
collapsed
pressed
busy
invalid
readonly
required
```

---

## 466.9 — Hidden

Node có thể:

```text
visible
hidden
```

nhưng hidden visual không nhất thiết đồng nghĩa removed semantic tree.

---

## 466.10 — Disabled

Disabled element vẫn có thể tồn tại trong accessibility tree để assistive technology biết control tồn tại nhưng không tương tác được.

---

# 466.11 — Bounds

Node có semantic bounds trong coordinate space xác định.

---

## 466.12 — Transform

Accessibility node có thể có transform từ local → window/screen coordinates.

---

## 466.13 — Offscreen

Node có thể tồn tại trong semantic tree nhưng hiện tại không visible.

---

## 466.14 — Virtualized content

Virtualized lists không bắt buộc phải instantiate toàn bộ visual widgets chỉ để accessibility.

Semantic provider có thể expose logical children.

---

# 466.15 — Parent/child hierarchy

Accessibility tree có hierarchy riêng.

Không bắt buộc 1:1 với visual tree.

---

## 466.16 — Semantic grouping

Nhiều visual primitives có thể được gộp thành một semantic node.

Ví dụ:

```text
[icon] [text] [background]
          ↓
       Button
```

---

## 466.17 — Decorative elements

Decorative graphics có thể đánh dấu:

```text
decorative = true
```

để screen reader bỏ qua.

---

## 466.18 — Semantic image

Image có thể có:

```text
role = Image
name = ...
description = ...
```

---

## 466.19 — Text semantics

Text phải lấy semantics từ 464.

Không tự phân tích UTF-8 bằng accessibility layer.

---

# 466.20 — Accessible text range

Text control có thể expose:

```text
TextRange
selection
caret
```

theo semantic text positions.

---

## 466.21 — Text position

Accessibility text position không được phụ thuộc byte offset nếu platform yêu cầu grapheme-aware positions.

464 cung cấp:

```text
byte
scalar
grapheme
```

representations.

---

## 466.22 — Caret

Caret position phải có thể được truy vấn.

---

## 466.23 — Selection

Text selection có:

```text
start
end
affinity
```

khi cần.

---

# 466.24 — Accessibility focus

Phải phân biệt:

```text
keyboard focus
pointer focus
accessibility focus
```

---

## 466.25 — Accessibility focus synchronization

Platform bridge có thể đồng bộ accessibility focus với logical UI focus nhưng không được giả định chúng luôn giống nhau.

---

## 466.26 — Focus movement

Actions:

```text
focus
move_focus
```

---

## 466.27 — Navigation order

Navigation order có thể explicit.

---

## 466.28 — Tab navigation

GUI controls có:

```texttab_stop
tab_index
```

hoặc equivalent semantic ordering.

---

## 466.29 — Spatial navigation

TV/gamepad/mobile interfaces có thể dùng:

```textup
down
left
right
```

navigation.

---

## 466.30 — Navigation policy

Navigation algorithm thuộc GUI/accessibility layer, không phải input device layer.

---

# 466.31 — Accessible actions

Canonical actions:

```text
Activate
Focus
SetValue
Increment
Decrement
Expand
Collapse
Select
Deselect
Scroll
ShowMenu
Dismiss
```

---

## 466.32 — Action parameters

Action có thể có typed parameter.

Ví dụ:

```text
SetValue(0.75)
```

---

## 466.33 — Action result

Action trả về `Result`.

Không dùng exception bắt buộc.

---

## 466.34 — Unsupported action

Nếu node không hỗ trợ action → explicit failure.

---

# 466.35 — Screen reader

Screen reader integration sử dụng semantic tree + events.

Axiom không tự trở thành screen reader.

---

## 466.36 — Accessibility events

Ví dụ:

```text
NodeCreated
NodeRemoved
NameChanged
ValueChanged
StateChanged
FocusChanged
SelectionChanged
TextChanged
LayoutChanged
```

---

## 466.37 — Live regions

Dynamic content có thể khai báo mức announcement:

```text
Off
Polite
Assertive
```

Platform bridge quyết định cơ chế thực thi.

---

## 466.38 — Announcement

Application có thể yêu cầu semantic announcement.

Không được spam screen reader mặc định.

---

## 466.39 — Progress updates

Progress controls có thể expose value updates.

---

## 466.40 — Error announcements

Validation errors có thể được expose semantic relationship với control tương ứng.

---

# 466.41 — Label relationship

Ví dụ:

```text
Label("Username")
      ↓
TextField
```

semantic relation:

```text
labelled_by
```

---

## 466.42 — Description relationship

Có thể:

```text
described_by
```

---

## 466.43 — Error relationship

Có thể:

```text
invalid_reason
```

---

## 466.44 — Help relationship

Có thể:

```text
help_text
```

---

# 466.45 — Form semantics

Form controls phải có thể expose:

```text
required
readonly
disabled
invalid
value
label
```

---

## 466.46 — Checkbox

Expose:

```text
checked
unchecked
mixed
```

nếu control hỗ trợ tri-state.

---

## 466.47 — Radio

Radio groups phải expose mutual selection semantics.

---

## 466.48 — Slider

Slider:

```text
minimum
maximum
step
value
```

---

## 466.49 — Progress

Progress có thể:

```text
determinate
indeterminate
```

---

## 466.50 — Toggle

Toggle semantic state phải độc lập visual representation.

---

# 466.51 — Lists

List semantics:

```text
List
ListItem
position
set_size
```

nếu cần.

---

## 466.52 — Trees

Tree:

```text
Tree
TreeItem
expanded
selected
level
```

---

## 466.53 — Tables

Table:

```text
Table
Row
Column
Cell
Header
```

---

## 466.54 — Table relationships

Cells có thể expose row/column headers.

---

# 466.55 — Menus

Menu hierarchy:

```text
Menu
MenuItem
Submenu
Separator
```

---

## 466.56 — Menu keyboard semantics

Menu interaction dùng 465 logical actions thay vì hard-code physical keys.

---

## 466.57 — Dialog

Dialog phải expose:

```text
role
name
modal
focus target
dismiss action
```

---

## 466.58 — Modal behavior

Modal dialog có explicit focus scope.

---

# 466.59 — Custom controls

Custom-rendered control phải có thể implement accessibility provider.

---

## 466.60 — Custom semantic node

API concept:

```text
AccessibleProvider
```

cho phép custom controls cung cấp semantics.

---

## 466.61 — Canvas accessibility

Canvas/custom graphics không được trở thành accessibility black box.

Có thể expose logical child objects trên canvas.

---

## 466.62 — Game accessibility

Game layer có thể expose:

```text
player
menu
inventory
dialogue
map
objective
```

như semantic objects.

Không yêu cầu mọi pixel phải trở thành accessibility node.

---

# 466.63 — Automation

UI automation sử dụng cùng semantic tree.

---

## 466.64 — Automation selectors

Selectors có thể dùng:

```text
AccessibleId
role
name
automation_id
```

---

## 466.65 — Stable automation ID

Developer có thể chỉ định stable `automation_id`.

---

## 466.66 — Automation isolation

Automation API không được mặc định bypass OS security boundaries.

---

## 466.67 — Automation actions

Automation có thể invoke semantic actions thay vì giả lập mouse/keyboard.

---

# 466.68 — Accessibility tree updates

Tree updates phải có transaction/batch capability.

---

## 466.69 — Atomic update

Một logical UI update có thể publish một semantic snapshot mới thay vì expose trạng thái trung gian.

---

## 466.70 — Snapshot

Accessibility consumers có thể đọc immutable snapshot.

---

## 466.71 — Incremental update

Không bắt buộc rebuild toàn bộ tree khi một node thay đổi.

---

## 466.72 — Tree cache

Platform bridge có thể cache semantic nodes.

---

## 466.73 — Cache invalidation

Invalidation phải deterministic.

---

# 466.74 — Localization

Accessible names/descriptions phải hỗ trợ localization thông qua 464 I18N.

---

## 466.75 — Language

Node có thể cung cấp language tag.

---

## 466.76 — Direction

Text semantics phải hỗ trợ:

```text
LTR
RTL
Auto
```

---

## 466.77 — Pronunciation

Accessibility provider có thể expose pronunciation metadata khi platform hỗ trợ.

Không sửa nội dung text chỉ để phục vụ pronunciation.

---

# 466.78 — User preferences

Accessibility preferences có thể bao gồm:

```text
text scale
high contrast
reduced motion
reduced transparency
screen reader active
keyboard navigation
```

---

## 466.79 — High contrast

GUI toolkit có thể query high-contrast preference.

---

## 466.80 — Reduced motion

Animations phải có thể giảm/tắt theo preference.

---

## 466.81 — Reduced transparency

Visual system có thể giảm transparency.

---

## 466.82 — Text scaling

Text engine 464 phải nhận scale preference.

---

## 466.83 — Contrast

Accessibility system có thể cung cấp contrast-related preferences/requirements.

Không ép một universal color palette vào language core.

---

# 466.84 — Platform bridges

Kiến trúc:

```text
Accessibility Core
        ↓
Platform Bridge
 ┌──────┼───────┬────────┐
Windows macOS Android Linux/WASM
```

---

## 466.85 — Windows

Bridge tới Windows accessibility/UI automation mechanisms.

---

## 466.86 — Apple

Bridge hỗ trợ macOS/iOS accessibility model.

---

## 466.87 — Android

Bridge hỗ trợ Android accessibility framework.

---

## 466.88 — Linux

Bridge hỗ trợ Linux desktop accessibility frameworks.

---

## 466.89 — Browser

WASM/web mapping phải tận dụng semantic DOM/accessibility tree khi thích hợp.

---

# 466.90 — Native vs custom UI

Native widget toolkit có thể lấy accessibility semantics trực tiếp từ native controls.

Custom UI phải tự publish semantic tree.

---

## 466.91 — No duplicated semantics

Visual widget và accessibility provider nên dùng chung semantic model khi có thể.

---

## 466.92 — Renderer independence

Accessibility không phụ thuộc:

```text GPU
OpenGL
Vulkan
DirectX
Metal
```

---

# 466.93 — Input integration

466 sử dụng 465:

```text accessibility action
       ↓
semantic command
       ↓
GUI
```

Không bắt buộc:

```text accessibility
→ fake mouse
→ fake keyboard
```

---

## 466.94 — Keyboard navigation

Keyboard navigation dùng logical actions của 465.

---

## 466.95 — Screen reader + IME

Text controls phải hỗ trợ đồng thời:

```text 464 Text
465 IME
466 Accessibility
```

mà không trộn composition với committed text.

---

# 466.96 — Privacy

Accessibility APIs có thể expose nội dung UI nhạy cảm.

Application phải có semantic privacy policy.

---

## 466.97 — Sensitive content

Node có thể đánh dấu:

```text sensitive
password
private
```

---

## 466.98 — Password fields

Password field không nên expose plaintext value cho automation/screen reader nếu platform policy không yêu cầu.

---

## 466.99 — Permission boundary

OS-level accessibility permissions remain external.

---

# 466.100 — AI integration

446 có thể query:

```text accessible_tree
node
role
name
state
value
relations
actions
focus
```

---

## 466.101 — Explainability

AI tooling có thể hỏi:

```text Why is this control inaccessible?
```

và nhận:

```text missing_name
invalid_role
no_focus_path
unsupported_action
broken_label_relation
```

---

## 466.102 — Semantic diff

Compiler/UI tooling có thể so sánh accessibility tree trước/sau thay đổi.

---

## 466.103 — Accessibility diagnostics

Diagnostics machine-readable:

```text AX001 missing accessible name
AX002 invalid role
AX003 broken relation
AX004 unreachable control
AX005 invalid state
```

---

# 466.104 — Testing

Test categories:

```text semantic tree
roles
names
labels
focus
navigation
actions
screen reader events
IME integration
localization
dynamic updates
virtualization
automation
platform bridges
```

---

## 466.105 — Accessibility conformance

UI component tests phải có accessibility contract.

---

## 466.106 — Golden tree

Có thể snapshot:

```text semantic tree → canonical JSON
```

để regression testing.

---

## 466.107 — Interaction testing

Test:

```text keyboard
pointer
touch
screen reader action
automation action
```

đều có thể kích hoạt cùng semantic command khi appropriate.

---

## 466.108 — Fuzzing

Fuzz:

```text semantic tree
relations
role/state combinations
automation selectors
accessibility events
```

---

# 466.109 — Performance

Accessibility không được làm chậm rendering khi accessibility chưa được sử dụng.

---

## 466.110 — Lazy activation

Platform accessibility bridge có thể activate khi cần.

---

## 466.111 — Incremental semantics

Large trees phải hỗ trợ incremental update.

---

## 466.112 — No mandatory allocation

Core semantic representation có thể sử dụng arena/pool/incremental storage.

---

## 466.113 — No hidden threads

Accessibility subsystem không tự tạo background thread nếu platform contract không yêu cầu.

---

## 466.114 — No hidden polling

Không polling accessibility state liên tục nếu event-driven mechanism tồn tại.

---

# 466.115 — Freestanding

Freestanding executable có thể omit accessibility hoàn toàn.

---

## 466.116 — Runtime boundary

Accessibility không thuộc mandatory runtime.

---

## 466.117 — Native artifact

Accessibility-enabled applications vẫn emit native code trực tiếp qua compiler/linker 420+.

---

# 466.118 — Hard invariants

1. Accessibility không thuộc language core.
2. Accessibility tree độc lập visual tree.
3. Semantic representation độc lập rendering.
4. Custom GPU UI có thể accessible.
5. Node có stable logical identity.
6. Không dùng memory address làm semantic identity.
7. Role là semantic property.
8. Name là semantic property.
9. Description là semantic property.
10. Value là semantic property.
11. State là semantic property.
12. Hidden semantics được xác định rõ.
13. Disabled node có thể vẫn tồn tại semantic tree.
14. Bounds có coordinate space rõ ràng.
15. Transform được biểu diễn rõ ràng.
16. Virtualized UI có semantic representation.
17. Decorative graphics có thể bị bỏ qua.
18. Text semantics tích hợp 464.
19. Text positions không được giả định chỉ là byte offsets.
20. Caret có thể truy vấn.
21. Selection có thể truy vấn.
22. Keyboard focus khác accessibility focus.
23. Pointer focus khác keyboard focus.
24. Focus transitions có semantics rõ ràng.
25. Tab navigation có thể cấu hình.
26. Spatial navigation có thể cấu hình.
27. Navigation không phụ thuộc physical keycodes.
28. Accessible actions là semantic actions.
29. Action có typed arguments khi cần.
30. Action failure dùng Result semantics.
31. Screen reader sử dụng semantic tree.
32. Accessibility events được chuẩn hóa.
33. Dynamic updates không bắt buộc rebuild toàn tree.
34. Live regions có mức announcement.
35. Không spam announcement mặc định.
36. Label relationships được biểu diễn rõ ràng.
37. Description relationships được biểu diễn rõ ràng.
38. Error relationships được biểu diễn rõ ràng.
39. Form controls expose required/readonly/disabled/invalid state.
40. Checkbox hỗ trợ tri-state khi cần.
41. Slider expose range/value.
42. Progress expose determinate/indeterminate.
43. Lists có semantic position metadata khi cần.
44. Trees expose expansion/selection semantics.
45. Tables expose row/column semantics.
46. Menus expose menu semantics.
47. Dialogs expose modality/focus semantics.
48. Custom controls có accessibility provider.
49. Canvas không bắt buộc là accessibility black box.
50. Game UI có thể expose semantic objects.
51. Automation sử dụng semantic tree.
52. Automation selectors có stable IDs.
53. Automation không mặc định bypass OS security.
54. Semantic actions ưu tiên hơn simulated physical input.
55. Accessibility tree hỗ trợ snapshots.
56. Accessibility tree hỗ trợ incremental updates.
57. Semantic updates có thể transaction/batch.
58. Cache invalidation deterministic.
59. Localization dùng 464.
60. Language metadata được giữ.
61. RTL/LTR semantics được giữ.
62. Accessibility preferences được expose.
63. Reduced motion có thể được tôn trọng.
64. High contrast có thể được tôn trọng.
65. Text scaling có thể được tôn trọng.
66. Platform bridges không thay đổi core semantics.
67. Windows bridge là platform layer.
68. Apple bridge là platform layer.
69. Android bridge là platform layer.
70. Linux bridge là platform layer.
71. WASM bridge là platform layer.
72. Accessibility không phụ thuộc GPU.
73. Accessibility không phụ thuộc renderer.
74. Accessibility tích hợp 465.
75. IME semantics vẫn giữ composition/commit distinction.
76. Sensitive content có privacy metadata.
77. Password plaintext không được expose tùy tiện.
78. OS accessibility permissions là external boundary.
79. Accessibility có thể lazy activate.
80. Accessibility không bắt buộc runtime.
81. Không hidden accessibility threads.
82. Không hidden accessibility polling.
83. Large trees phải scale incrementally.
84. Accessibility có thể hoạt động với native widgets.
85. Accessibility có thể hoạt động với custom widgets.
86. Accessibility có machine-readable diagnostics.
87. AI tooling có thể query accessibility tree.
88. AI tooling có thể explain accessibility failures.
89. Accessibility tree có thể snapshot để regression test.
90. Semantic tree được fuzz-tested.
91. Platform adapters được test riêng.
92. Accessibility action semantics deterministic.
93. Accessibility state không phụ thuộc visual styling.
94. Accessibility không tự tạo keyboard/mouse events.
95. Accessibility không yêu cầu GC.
96. Accessibility không yêu cầu borrow checker.
97. Accessibility tuân ownership model 423.
98. Accessibility errors dùng Result/policy 425.
99. Accessibility metadata tích hợp 446.
100. **Axiom accessibility phải biến semantic UI thành một contract machine-readable, platform-independent và có thể truy cập được bởi screen reader, keyboard navigation, automation và assistive technology mà không ép GUI phải sử dụng một renderer hoặc toolkit cụ thể.**

**BOOTSTRAP-466 hoàn tất.**

---

# BOOTSTRAP-467 — CLIPBOARD, DRAG & DROP, SELECTION, COPY/PASTE, DATA TRANSFER & INTER-APPLICATION INTERACTION

Tiếp theo là lớp interaction giữa ứng dụng với hệ điều hành và ứng dụng khác:

```text
                Axiom Application
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
      Selection     Clipboard    Drag/Drop
          │            │            │
          └────────────┼────────────┘
                       ↓
                Transfer Model
                       ↓
              Platform Clipboard
                       ↓
              Other Applications
```

467 sẽ khóa:

- clipboard ownership;
- text/UTF-8 clipboard;
- plain text vs rich text;
- HTML/RTF;
- image/audio/file clipboard;
- MIME/type negotiation;
- multiple clipboard representations;
- lazy/deferred clipboard rendering;
- clipboard lifetime;
- copy/cut/paste;
- primary selection trên Linux;
- selection semantics;
- drag source;
- drop target;
- drag payload;
- allowed operations;
- copy/move/link;
- drag preview;
- drag cancellation;
- cross-process transfer;
- large payload streaming;
- temporary files;
- URI/file-list transfer;
- security/trust boundary;
- sandbox permissions;
- clipboard privacy;
- sensitive/password content;
- ownership/resource lifetime;
- asynchronous transfer;
- backpressure;
- GUI 452 integration;
- text 464 integration;
- input 465 integration;
- accessibility 466 integration;
- native platform bridges;
- WASM/browser clipboard permissions;
- AI-readable transfer diagnostics.

Mô hình quan trọng:

```text
Clipboard/Drag Payload
        ≠
Memory Pointer
        ≠
Serialized Object
        ≠
File Path
```

Axiom phải cho phép một object cung cấp **nhiều representation**:

```text
Application Object
      │
      ├── UTF-8 text
      ├── HTML
      ├── image
      ├── serialized binary
      └── file/URI list
```

và consumer chọn representation phù hợp mà không bắt application phải tạo toàn bộ dữ liệu ngay từ đầu.

