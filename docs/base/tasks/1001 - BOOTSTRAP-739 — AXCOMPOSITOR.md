# BOOTSTRAP-739 — AXCOMPOSITOR

**Namespace:** `AXCOMPOSITOR`  
**Phase:** Axiom Civilization Runtime / Native Composition & Presentation Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXUI`, `AXWINDOW`, `AXDISPLAY`, `AXGRAPHICS`, `AXMEDIA`, `AXAUDIO`, `AXINPUT`, `AXCOMPUTE`, `AXSECURITY`, `AXSTORAGE`, `AXNETWORK`, `AXASSET`

> `AXCOMPOSITOR` là tầng nằm giữa **rendered surfaces** và **display presentation**. Nó quyết định surface nào được compose, theo thứ tự nào, transform ra sao, clip thế nào, blend thế nào, surface nào có thể dùng hardware overlay/direct scanout và frame nào được present.

---

# 739.0 — Mục tiêu

AXCOMPOSITOR phải cung cấp composition runtime native cho:

```text
window composition
UI composition
video composition
desktop composition
multi-surface composition
offscreen composition
embedded composition
HDR composition
transparent surfaces
hardware overlays
remote composition
headless composition
XR-like multi-view composition
```

Pipeline tổng quát:

```text
AXUI
  │
  ↓
AXWINDOW
  │
  ├──────────────┐
  ↓              ↓
AXGRAPHICS     AXMEDIA
  │              │
  └──────┬───────┘
         ↓
   AXCOMPOSITOR
         │
   ┌─────┼──────────────┐
   ↓     ↓              ↓
 GPU   Overlay      Direct Scanout
   │     │              │
   └─────┴──────┬───────┘
                 ↓
             AXDISPLAY
                 ↓
              Display
```

---

# 739.1 — Boundary

AXCOMPOSITOR sở hữu:

```text
composition tree
surface ordering
z-order
transform
opacity
clip
blend
surface visibility
damage tracking
occlusion
composition transactions
composition scheduling
surface synchronization
overlay selection
composition color-space negotiation
presentation preparation
composition telemetry
```

Không sở hữu:

```text
UI semantics          → AXUI
window lifecycle      → AXWINDOW
GPU primitives        → AXGRAPHICS
display timing        → AXDISPLAY
raw input             → AXINPUT
media decoding        → AXMEDIA
audio                  → AXAUDIO
physical display asset→ AXASSET
security authority    → AXSECURITY
```

---

# 739.2 — Surface

Canonical composition primitive:

```axiom
surface {
    id
    resource
    bounds
    transform
    opacity
    visibility
    z_order
    clip
    blend
    color
    protection
}
```

Surface là **visual resource**, không phải window.

---

# 739.3 — Surface Identity

```axiom
surface_id
```

phải độc lập với:

```text
window_id
texture_id
GPU allocation
native handle
memory address
```

---

# 739.4 — Surface Ownership

Surface có thể được sở hữu bởi:

```text
AXUI
AXWINDOW
AXMEDIA
AXGRAPHICS
application
system compositor
```

AXCOMPOSITOR chỉ quản lý composition relationship.

---

# 739.5 — Composition Tree

```text
composition_root
 ├── surface
 │    ├── surface
 │    └── surface
 └── surface
```

Tree có thể khác UI tree.

---

# 739.6 — Composition Layer

Một surface có thể được lower thành:

```axiom
composition_layer {
    source
    destination
    transform
    clip
    opacity
    blend
    color_transform
}
```

---

# 739.7 — Layer Identity

```axiom
layer_id
```

stable trong composition graph version.

---

# 739.8 — Composition Graph

```axiom
composition_graph {
    version
    root
    layers
}
```

Mỗi committed composition có version.

---

# 739.9 — Composition Transaction

Thay đổi nhiều surface phải có transaction:

```axiom
begin_composition()

set_surface(...)
set_transform(...)
set_opacity(...)
set_clip(...)
set_z_order(...)

commit_composition()
```

---

# 739.10 — Atomicity

Nếu backend hỗ trợ atomic commit:

```text
old graph
    ↓
commit
    ↓
new graph
```

Không được present trạng thái nửa cũ/nửa mới.

---

# 739.11 — Composition Snapshot

```axiom
composition_snapshot {
    version
    layers
    transforms
    visibility
    damage
}
```

Dùng cho:

```text
debug
replay
simulation
recovery
```

---

# 739.12 — Z-Order

```axiom
z_order
```

phải có ordering deterministic.

Ví dụ:

```text
background
window A
window B
popup
cursor
overlay
```

---

# 739.13 — Parent/Child Composition

Child surface có thể inherit:

```text
transform
opacity
clip
visibility
color context
```

nhưng inheritance phải explicit.

---

# 739.14 — Transform

```axiom
surface_transform {
    translation
    scale
    rotation
    matrix
}
```

Canonical representation phải tránh mất precision không cần thiết.

---

# 739.15 — Transform Composition

Nếu:

```text
parent_transform
child_transform
```

thì:

```text
world_transform =
    parent_transform × child_transform
```

phải có quy ước matrix order cố định trong core ABI.

---

# 739.16 — Clip

```axiom
clip {
    rectangle
    rounded_rectangle
    path
    mask
}
```

---

# 739.17 — Clip Hierarchy

Clip có thể inherited từ parent.

---

# 739.18 — Clip Optimization

Compositor nên reduce:

```text
nested rectangles
```

thành effective clip khi có thể.

---

# 739.19 — Scissor

Rectangular clip đơn giản nên lower thành hardware scissor.

---

# 739.20 — Mask

Complex mask có thể lower thành:

```text
texture mask
stencil
shader operation
```

tùy backend.

---

# 739.21 — Opacity

```axiom
opacity : f32
```

canonical range:

```text
0.0 .. 1.0
```

---

# 739.22 — Opacity Inheritance

Effective opacity:

```text
effective =
parent_opacity × local_opacity
```

phải được tính deterministic.

---

# 739.23 — Blend Mode

Core modes:

```text
normal
add
multiply
screen
subtract
```

Backend có thể expose extensions.

---

# 739.24 — Blend Capability

Không được giả định mọi display/compositor backend hỗ trợ mọi blend mode.

Unsupported mode phải:

```text
reject
fallback
shader composition
```

theo explicit policy.

---

# 739.25 — Color Space

Mỗi composition surface có thể có:

```axiom
surface_color_space
```

Không được mặc định mọi surface đều sRGB.

---

# 739.26 — Color Conversion

Pipeline:

```text
surface color
     ↓
composition color space
     ↓
display color space
     ↓
AXDISPLAY
```

---

# 739.27 — HDR Composition

HDR surface có thể compose cùng SDR surface.

Compositor phải biết:

```text
surface transfer function
surface primaries
surface luminance range
```

---

# 739.28 — SDR-in-HDR

SDR surface phải được map rõ ràng vào HDR composition space.

Không được chỉ reinterpret byte values.

---

# 739.29 — HDR-in-SDR

Nếu HDR content được đưa vào SDR output:

```text
tone mapping
```

phải explicit.

---

# 739.30 — Tone Mapping

```axiom
tone_map {
    operator
    source_range
    target_range
}
```

---

# 739.31 — Alpha

Alpha modes:

```text
opaque
straight
premultiplied
```

Compositor phải biết alpha interpretation.

---

# 739.32 — Premultiplied Alpha

Canonical internal composition format nên ưu tiên premultiplied alpha để tránh nhiều edge cases trong blending.

---

# 739.33 — Surface Visibility

```text
visible
hidden
occluded
partially_visible
fully_visible
```

Visibility không đồng nhất với window visibility.

---

# 739.34 — Occlusion

Compositor phải có thể xác định:

```text
fully_occluded
partially_occluded
visible
```

---

# 739.35 — Occlusion Culling

Surface fully covered bởi opaque surfaces có thể bỏ khỏi composition workload.

---

# 739.36 — Damage Region

```axiom
damage_region {
    rectangles
    bounds
}
```

Chỉ vùng thay đổi cần recomposite khi backend hỗ trợ.

---

# 739.37 — Damage Tracking

Damage có thể phát sinh từ:

```text
content change
transform change
opacity change
clip change
z-order change
surface removal
surface addition
```

---

# 739.38 — Damage Propagation

Nếu surface thay đổi:

```text
surface damage
      ↓
affected composition region
      ↓
parent damage
      ↓
display damage
```

---

# 739.39 — Damage Coalescing

Nhiều damage regions có thể merge:

```text
rect A
rect B
rect C
   ↓
union
```

nhưng không được biến mọi update nhỏ thành full-screen redraw một cách mặc định.

---

# 739.40 — Partial Composition

Compositor phải hỗ trợ:

```text
full composition
partial composition
direct surface presentation
```

---

# 739.41 — Direct Scanout

Nếu một surface:

```text
opaque
full-screen
compatible format
compatible color
compatible transform
```

có thể bypass composition:

```text
surface
 ↓
display
```

---

# 739.42 — Direct Scanout Eligibility

```axiom
direct_scanout_candidate(surface, display)
```

phải kiểm tra:

```text
format
size
transform
color
protection
timing
display capability
```

---

# 739.43 — Hardware Overlay

Một số surface có thể được đưa trực tiếp lên overlay plane:

```text
GPU composition
      +
overlay plane
      ↓
display
```

---

# 739.44 — Overlay Candidate

```axiom
overlay_candidate {
    surface
    plane
    compatibility
}
```

---

# 739.45 — Overlay Assignment

Assignment phải giải quyết:

```text
plane count
format
scaling
transform
alpha
z-order
protection
bandwidth
```

---

# 739.46 — Overlay Fallback

Nếu overlay assignment thất bại:

```text
overlay
 ↓
GPU composition
```

không được làm semantic state thay đổi.

---

# 739.47 — Composition Strategy

```text
direct_scanout
overlay
gpu_composition
cpu_composition
```

Compositor chọn strategy phù hợp.

---

# 739.48 — Strategy Decision

Có thể dựa trên:

```text
latency
power
bandwidth
surface count
damage
GPU availability
display capability
protected content
```

---

# 739.49 — Composition Plan

```axiom
composition_plan {
    strategy
    layers
    overlays
    gpu_passes
    damage
    target
}
```

---

# 739.50 — Plan Compilation

Composition graph:

```text
composition graph
       ↓
validation
       ↓
occlusion analysis
       ↓
overlay analysis
       ↓
render pass generation
       ↓
composition plan
```

---

# 739.51 — GPU Composition

GPU path có thể tạo:

```text
render pass
pipeline
textures
buffers
scissor
blend state
```

thông qua `AXGRAPHICS`.

---

# 739.52 — CPU Composition

CPU fallback phải hỗ trợ tối thiểu:

```text
copy
blend
scale
clip
color conversion
```

---

# 739.53 — SIMD

CPU compositor có thể specialize:

```text
SSE
AVX
NEON
other vector ISA
```

nhưng đây là backend optimization.

---

# 739.54 — Zero-Copy

Ưu tiên:

```text
surface resource
      ↓
GPU compositor
      ↓
display
```

không copy qua CPU.

---

# 739.55 — Surface Import

```axiom
import_surface(resource)
```

có thể import:

```text
GPU texture
DMA buffer
shared memory
video frame
native surface
```

---

# 739.56 — Surface Export

```axiom
export_surface(surface)
```

chỉ khi capability cho phép.

---

# 739.57 — Cross-Process Surface

Cross-process surface phải dùng capability:

```axiom
surface_capability {
    surface
    permissions
}
```

---

# 739.58 — Surface Permissions

```text
read
write
compose
capture
export
destroy
```

---

# 739.59 — Protected Surface

```axiom
surface_protection {
    normal
    protected
    secure
}
```

Protected surface không được route qua insecure composition path.

---

# 739.60 — DRM/Protected Media Boundary

Video protected:

```text
AXMEDIA
    ↓
protected surface
    ↓
AXCOMPOSITOR
    ↓
protected overlay
    ↓
AXDISPLAY
```

---

# 739.61 — Secure Composition

Compositor phải reject hoặc isolate surface nếu composition path không đáp ứng protection requirement.

---

# 739.62 — Window Composition

AXWINDOW cung cấp:

```text
window surface
window bounds
window state
```

AXCOMPOSITOR quyết định composition.

---

# 739.63 — Window Z-Order

Window ordering thuộc AXWINDOW semantic layer.

Compositor nhận resolved ordering.

---

# 739.64 — Popup Composition

Popup/menu/dialog có thể có composition layer riêng.

---

# 739.65 — Modal Composition

Modal UI có thể tạo:

```text
application content
+
modal surface
+
optional backdrop
```

Backdrop không được coi là separate window bắt buộc.

---

# 739.66 — Transparency

Surface có thể:

```text
opaque
alpha
transparent
```

---

# 739.67 — Transparent Window

Transparent window cần composition path hỗ trợ alpha.

Nếu backend không hỗ trợ:

```text
unsupported
```

không được silently flatten.

---

# 739.68 — Blur / Backdrop Effects

Compositor có thể support:

```text
blur
background sampling
color filter
```

nhưng đây là composition effect.

---

# 739.69 — Backdrop Sampling

Backdrop effect phải respect:

```text
clip
security
protected content
color space
```

---

# 739.70 — Effect Graph

```axiom
composition_effect {
    type
    inputs
    parameters
}
```

---

# 739.71 — Effect Ordering

Ví dụ:

```text
clip
 ↓
transform
 ↓
opacity
 ↓
blend
 ↓
effect
```

Thứ tự phải được specification hóa, không backend-dependent.

---

# 739.72 — Surface Filter

Có thể có:

```text
nearest
linear
anisotropic
```

cho scaling.

---

# 739.73 — Scaling

Compositor phải hỗ trợ:

```text
upscale
downscale
non-uniform scale
```

nếu backend hỗ trợ.

---

# 739.74 — Scaling Quality

Policy:

```text
nearest
bilinear
bicubic
platform
application
```

---

# 739.75 — Rotation

Surface rotation:

```text
0
90
180
270
arbitrary
```

Arbitrary rotation thường cần GPU composition.

---

# 739.76 — Surface Transform Constraints

Direct scanout thường chỉ hỗ trợ subset transform.

---

# 739.77 — Composition Coordinate Space

Phải phân biệt:

```text
surface-local
window
composition-root
display
physical-pixel
```

---

# 739.78 — Composition Root

```axiom
composition_root {
    target_display
    viewport
    color_space
    layers
}
```

---

# 739.79 — Multi-Display Composition

Một composition graph có thể target:

```text
Display A
Display B
```

nhưng mỗi display có thể có:

```text
different resolution
different color
different refresh
different HDR
```

---

# 739.80 — Per-Display Plan

Một graph chung có thể compile thành:

```text
composition graph
   ├── display A plan
   └── display B plan
```

---

# 739.81 — Display-Specific Color

Cùng một source surface có thể được color-converted riêng cho từng display.

---

# 739.82 — Display-Specific Scaling

Một UI surface có thể được scale khác nhau theo display scale.

---

# 739.83 — Frame Scheduling

Compositor phải phối hợp:

```text
surface readiness
GPU completion
display timing
```

---

# 739.84 — Frame Deadline

```axiom
composition_deadline {
    display
    frame
    deadline
}
```

---

# 739.85 — Late Frame

Nếu frame không hoàn thành trước deadline:

```text
reuse_previous
drop_frame
partial_update
fallback
```

theo policy.

---

# 739.86 — Frame Drop

Frame drop phải observable.

Không coi drop là application semantic failure.

---

# 739.87 — Frame Reuse

Một surface có thể giữ frame cũ trong khi surface khác update.

---

# 739.88 — Independent Surface Timing

Video surface có thể update theo media clock trong khi UI update theo display clock.

Compositor phải synchronize tại composition boundary.

---

# 739.89 — Media Frame Synchronization

```text
AXMEDIA frame timestamp
       ↓
composition timeline
       ↓
display presentation timestamp
```

---

# 739.90 — Audio Sync Boundary

Audio timing:

→ `AXAUDIO`

Compositor chỉ expose presentation timestamps để media/audio subsystem đồng bộ.

---

# 739.91 — Triple Buffering

Backend có thể hỗ trợ:

```text
front
back
spare
```

nhưng buffering strategy không được leak thành application semantic API.

---

# 739.92 — Buffer Queue

```axiom
surface_queue {
    acquire()
    submit()
    present()
}
```

---

# 739.93 — Backpressure

Producer nhanh hơn compositor phải nhận:

```text
queue full
throttle
drop
replace_latest
```

policy explicit.

---

# 739.94 — Latest-Frame Policy

Realtime video/UI có thể dùng:

```text
replace_oldest
replace_latest
```

nhưng không được dùng cho transactional visual state nếu làm mất semantic state.

---

# 739.95 — Composition Transaction Ordering

Transactions phải có sequence:

```axiom
composition_sequence
```

---

# 739.96 — Transaction Cancellation

Transaction chưa commit có thể bị cancel.

Committed composition không bị rollback bằng cách implicit mutation.

---

# 739.97 — Composition Commit

Commit result:

```text
accepted
rejected
partially_supported
deferred
```

---

# 739.98 — Deferred Commit

Một commit có thể được schedule cho display boundary kế tiếp.

---

# 739.99 — Present

```axiom
present(composition_plan)
```

không đồng nghĩa:

```text
frame is physically visible
```

Physical presentation feedback đến từ AXDISPLAY.

---

# 739.100 — Presentation Feedback

```axiom
presentation_feedback {
    composition_version
    frame_id
    submitted
    accepted
    displayed
    display_timestamp
}
```

---

# 739.101 — Presentation Latency

Compositor telemetry:

```text
input
state
compose
GPU
submit
display
```

cho phép đo end-to-end latency.

---

# 739.102 — Frame Pacing

Compositor phải tránh:

```text
burst
idle
burst
idle
```

khi có thể dự đoán display timing.

---

# 739.103 — Adaptive Scheduling

Scheduler có thể điều chỉnh:

```text
composition start time
GPU workload
buffer strategy
```

dựa trên presentation deadline.

---

# 739.104 — Power Optimization

Có thể:

```text
reduce composition frequency
reuse unchanged layers
use overlay
direct scanout
```

để giảm năng lượng.

---

# 739.105 — Energy Boundary

Energy accounting:

→ `AXENERGY`.

AXCOMPOSITOR chỉ cung cấp telemetry/optimization hints.

---

# 739.106 — Remote Composition

Có hai mô hình:

```text
1. compose locally → encode final frame
2. send composition graph → compose remotely
```

Cả hai đều phải explicit.

---

# 739.107 — Remote Surface

```axiom
remote_surface {
    source
    transport
    format
    latency
}
```

Transport:

→ `AXNETWORK`.

---

# 739.108 — Remote Composition Security

Cross-machine surface sharing phải được capability-controlled.

---

# 739.109 — Headless Composition

Headless compositor:

```text
composition
 ↓
offscreen surface
 ↓
AXMEDIA/image
```

không cần physical display.

---

# 739.110 — Screenshot

Screenshot có thể được thực hiện từ:

```text
composition snapshot
display capture
window surface
```

Ba semantics khác nhau.

---

# 739.111 — Capture Semantics

Phân biệt:

```text
window capture
composition capture
display capture
surface capture
```

---

# 739.112 — Capture Security

Protected surface có thể làm:

```text
capture denied
redacted
black
secure path
```

theo policy.

---

# 739.113 — Composition Debugging

Debug API:

```axiom
inspect_composition()
inspect_surface()
inspect_damage()
inspect_occlusion()
inspect_overlay_plan()
inspect_color_pipeline()
```

---

# 739.114 — Visualizer

Debug overlay có thể hiển thị:

```text
surface bounds
z-order
damage
occlusion
clip
GPU passes
overlay planes
```

---

# 739.115 — Composition Trace

Trace event:

```text
surface_created
surface_updated
transaction_begin
transaction_commit
plan_compiled
frame_submitted
frame_displayed
```

---

# 739.116 — Deterministic Replay

Replay phải có:

```text
composition graph
surface updates
timing
transaction sequence
```

---

# 739.117 — Simulation

```axiom
composition_simulation {
    display
    surfaces
    timing
    gpu_model
}
```

---

# 739.118 — Simulated GPU

Có thể sử dụng abstract GPU model để kiểm tra:

```text
render pass
composition plan
overlay eligibility
damage
```

mà không cần physical GPU.

---

# 739.119 — Digital Twin

```axiom
composition_digital_twin {
    display
    surfaces
    graph
    timing
    resources
}
```

---

# 739.120 — AI Composition Optimization

AI có thể đề xuất:

```text
layer merging
overlay assignment
damage optimization
frame scheduling
power optimization
```

---

# 739.121 — AI Boundary

AI không được tự thay đổi:

```text
protected content policy
capture permissions
security boundaries
window ownership
```

---

# 739.122 — Composition Compiler

Graph có thể compile:

```text
composition graph
      ↓
validation
      ↓
dependency resolution
      ↓
occlusion
      ↓
damage
      ↓
overlay
      ↓
render passes
      ↓
presentation plan
```

---

# 739.123 — Compile-Time Composition

UI/static composition có thể precompile:

```text
static transform
static clip
static blend
static layer hierarchy
```

Runtime chỉ update dynamic fields.

---

# 739.124 — Hot/Cold Data Split

Hot:

```text
surface transform
opacity
visibility
z
damage
resource handle
```

Cold:

```text
debug metadata
accessibility metadata
source provenance
diagnostic labels
```

---

# 739.125 — Dense Surface Storage

Compositor nên dùng:

```text
surface index
layer index
dense arrays
generation counters
```

thay vì object allocation cho từng frame.

---

# 739.126 — Resource Lifetime

Resource destruction phải defer tới khi GPU/compositor không còn sử dụng.

---

# 739.127 — Fence

```axiom
composition_fence {
    id
    signal()
    wait()
}
```

Fence semantics phải phù hợp backend.

---

# 739.128 — Synchronization

Có thể dùng:

```text
fence
semaphore
event
timeline
```

nhưng canonical abstraction phải tránh phụ thuộc một GPU API cụ thể.

---

# 739.129 — Timeline Semaphore

```axiom
timeline_sync {
    value
    signal(value)
    wait(value)
}
```

---

# 739.130 — CPU/GPU Synchronization

Không được blocking CPU trong hot path nếu asynchronous path có thể sử dụng.

---

# 739.131 — Error Model

```text
invalid_surface
invalid_transaction
unsupported_format
unsupported_blend
unsupported_transform
protected_surface
display_unavailable
gpu_failure
resource_lost
deadline_missed
capture_denied
security_denied
```

---

# 739.132 — Device Loss

GPU/device loss:

```text
GPU_LOST
   ↓
invalidate transient composition resources
   ↓
rebuild
   ↓
restore composition graph
   ↓
resume
```

Semantic UI state không được mất chỉ vì GPU resource mất.

---

# 739.133 — Surface Recovery

Surface resource có thể được:

```text
recreated
reimported
redecoded
redrawn
```

tùy source.

---

# 739.134 — Composition Recovery

Compositor phải giữ đủ logical state để rebuild GPU plan.

---

# 739.135 — Platform Backends

Có thể có:

```text
Windows compositor backend
Linux compositor backend
macOS compositor backend
Android compositor backend
iOS compositor backend
embedded backend
headless backend
remote backend
```

---

# 739.136 — Desktop Backend

Desktop backend cần hỗ trợ:

```text
window surfaces
transparent windows
popups
multi-monitor
HDR
VRR
overlay
```

theo capability.

---

# 739.137 — Mobile Backend

Mobile ưu tiên:

```text
power
thermal
surface lifecycle
orientation
display sleep
GPU composition
```

---

# 739.138 — Embedded Backend

Embedded có thể chỉ cần:

```text
one root
few surfaces
fixed display
direct scanout
```

---

# 739.139 — Game/Realtime Backend

Realtime workloads cần:

```text
low latency
predictable frame pacing
minimal allocation
GPU-first composition
```

---

# 739.140 — UI Integration

```text
AXUI
 ↓
render tree
 ↓
surface
 ↓
AXCOMPOSITOR
```

AXCOMPOSITOR không cần hiểu button/text semantics.

---

# 739.141 — Media Integration

Video frame:

```text
AXMEDIA
 ↓
video surface
 ↓
AXCOMPOSITOR
```

Decoder có thể cung cấp GPU-native surface để tránh copy.

---

# 739.142 — Graphics Integration

AXGRAPHICS cung cấp:

```text
texture
render target
GPU fence
command buffer
```

Compositor tạo composition workload.

---

# 739.143 — Window Integration

AXWINDOW cung cấp:

```text
window surface
bounds
visibility
z-order
display association
```

Compositor tạo final visual composition.

---

# 739.144 — Display Integration

AXDISPLAY cung cấp:

```text
refresh
timing
color
HDR
VRR
display capability
presentation feedback
```

---

# 739.145 — Formal Invariants

```text
CMP-INV-01   Every composition surface has a stable surface identity.
CMP-INV-02   Surface identity is distinct from window identity.
CMP-INV-03   Surface identity is distinct from GPU resource identity.
CMP-INV-04   Composition graph versions are explicit.
CMP-INV-05   Composition transactions have explicit lifecycle.
CMP-INV-06   Transaction ordering is deterministic.
CMP-INV-07   Z-order is deterministic.
CMP-INV-08   Transform semantics are explicitly defined.
CMP-INV-09   Clip semantics are explicitly defined.
CMP-INV-10   Opacity semantics are explicitly defined.

CMP-INV-11   Alpha interpretation is explicit.
CMP-INV-12   Blend mode is explicit.
CMP-INV-13   Surface color space is explicit.
CMP-INV-14   HDR capability is distinct from HDR activation.
CMP-INV-15   Tone mapping is explicit.
CMP-INV-16   Surface visibility is distinct from window visibility.
CMP-INV-17   Occlusion state is derived explicitly.
CMP-INV-18   Damage regions are explicit.
CMP-INV-19   Damage propagation is deterministic.
CMP-INV-20   Full composition is not required when direct presentation is valid.

CMP-INV-21   Direct scanout eligibility is capability-checked.
CMP-INV-22   Overlay assignment is capability-checked.
CMP-INV-23   Overlay failure has an explicit fallback.
CMP-INV-24   GPU composition and CPU composition have equivalent semantic targets.
CMP-INV-25   Surface resource ownership is explicit.
CMP-INV-26   Cross-process surfaces require explicit capability.
CMP-INV-27   Protected surfaces cannot silently enter insecure paths.
CMP-INV-28   Composition coordinates are explicit.
CMP-INV-29   Display-specific color conversion is explicit.
CMP-INV-30   Multi-display composition has per-display output state.

CMP-INV-31   Presentation submission is distinct from physical display.
CMP-INV-32   Presentation feedback carries explicit timing information.
CMP-INV-33   Frame drops are observable.
CMP-INV-34   Frame reuse is explicit.
CMP-INV-35   Composition backpressure is explicit.
CMP-INV-36   GPU/device loss cannot invalidate logical UI state.
CMP-INV-37   Capture operations are security-aware.
CMP-INV-38   AI suggestions cannot silently cross security boundaries.
CMP-INV-39   Simulation cannot mutate production composition state.
CMP-INV-40   Replay preserves deterministic composition transaction ordering.
```

---

# 739.146 — Native API

```axiom
create_compositor()
destroy_compositor()

create_surface()
destroy_surface()

attach_surface()
detach_surface()

create_composition_root()
destroy_composition_root()

begin_composition()
commit_composition()
cancel_composition()

set_surface_transform()
set_surface_clip()
set_surface_opacity()
set_surface_blend()
set_surface_visibility()
set_surface_z_order()
set_surface_color_space()

get_surface_state()

compute_damage()
compute_occlusion()

build_composition_plan()
validate_composition_plan()

select_overlays()
check_direct_scanout()

compose()
present()

get_presentation_feedback()

create_fence()
create_timeline_sync()

capture_surface()
capture_composition()

inspect_composition()
inspect_damage()
inspect_occlusion()
inspect_overlay_plan()

create_composition_simulation()
record_composition()
replay_composition()

get_compositor_diagnostics()
```

---

# 739.147 — Canonical Flow: Desktop Frame

```text
AXUI
 ↓
UI render tree
 ↓
surface update
 ↓
AXWINDOW
 ↓
composition transaction
 ↓
AXCOMPOSITOR
 ↓
damage analysis
 ↓
occlusion
 ↓
overlay/direct-scanout analysis
 ↓
GPU composition
 ↓
presentation
 ↓
AXDISPLAY
 ↓
physical display
```

---

# 739.148 — Canonical Flow: Video Overlay

```text
AXMEDIA decoder
      ↓
GPU-native video surface
      ↓
AXCOMPOSITOR
      ↓
overlay candidate
      ↓
AXDISPLAY
```

Nếu overlay không khả dụng:

```text
video surface
 ↓
GPU composition
 ↓
display
```

---

# 739.149 — Canonical Flow: HDR Desktop

```text
SDR UI surface
       +
HDR video surface
       ↓
composition color space
       ↓
tone/color processing
       ↓
HDR display output
       ↓
AXDISPLAY
```

---

# 739.150 — Canonical Flow: GPU Loss

```text
GPU loss
   ↓
AXCOMPOSITOR
   ↓
invalidate GPU plan
   ↓
preserve logical composition graph
   ↓
AXGRAPHICS recovery
   ↓
recompile composition plan
   ↓
resume presentation
```

---

# 739.151 — Completion Criteria

`BOOTSTRAP-739` phải freeze:

1. Surface identity.
2. Surface ownership.
3. Composition tree.
4. Composition graph.
5. Composition versions.
6. Layer identity.
7. Transactions.
8. Atomic commit semantics.
9. Snapshots.
10. Z-order.
11. Parent/child composition.
12. Transform.
13. Clip.
14. Opacity.
15. Blend.
16. Alpha.
17. Visibility.
18. Occlusion.
19. Damage tracking.
20. Damage propagation.
21. Partial composition.
22. Direct scanout.
23. Hardware overlays.
24. Overlay assignment.
25. Composition strategy.
26. Composition plan.
27. GPU composition.
28. CPU fallback.
29. SIMD path.
30. Zero-copy.
31. Surface import/export.
32. Cross-process surfaces.
33. Protected surfaces.
34. Secure composition.
35. Window composition.
36. Popup composition.
37. Modal composition.
38. Transparency.
39. Backdrop effects.
40. Scaling.
41. Rotation.
42. Coordinate spaces.
43. Multi-display composition.
44. Per-display plans.
45. HDR composition.
46. SDR/HDR conversion.
47. Tone mapping.
48. Frame scheduling.
49. Frame deadlines.
50. Frame drops.
51. Frame reuse.
52. Buffer queues.
53. Backpressure.
54. Presentation feedback.
55. Presentation latency.
56. Frame pacing.
57. Power optimization.
58. Remote composition.
59. Headless composition.
60. Capture boundary.
61. Capture security.
62. Debugging.
63. Composition tracing.
64. Deterministic replay.
65. Simulation.
66. Digital twin.
67. AI optimization boundary.
68. Composition compiler.
69. Compile-time optimization.
70. Hot/cold data separation.
71. Dense memory model.
72. GPU synchronization.
73. Device-loss recovery.
74. Platform backends.
75. AXUI integration.
76. AXWINDOW integration.
77. AXGRAPHICS integration.
78. AXMEDIA integration.
79. AXDISPLAY integration.
80. 40 formal invariants.
81. Native API.
82. Canonical flows.
83. Performance architecture.

---

# 739.152 — Definition of Done

```text
BOOTSTRAP-739
STATUS: COMPLETE / FROZEN

AXCOMPOSITOR
 ├── Surface Model
 ├── Composition Tree
 ├── Composition Graph
 ├── Layer Model
 ├── Transactions
 ├── Z-Order
 ├── Transform
 ├── Clip
 ├── Opacity
 ├── Blend
 ├── Alpha
 ├── Color Management
 ├── HDR Composition
 ├── Tone Mapping
 ├── Damage Tracking
 ├── Occlusion
 ├── Direct Scanout
 ├── Hardware Overlay
 ├── GPU Composition
 ├── CPU Composition
 ├── Zero-Copy
 ├── Protected Surfaces
 ├── Secure Composition
 ├── Multi-Display Composition
 ├── Frame Scheduling
 ├── Presentation
 ├── Frame Pacing
 ├── Buffer Queues
 ├── Backpressure
 ├── Capture
 ├── Remote Composition
 ├── Headless Composition
 ├── Deterministic Replay
 ├── Simulation
 ├── Digital Twin
 ├── AI Boundary
 ├── Device Recovery
 ├── Diagnostics
 ├── Native API
 ├── Performance Architecture
 ├── 40 Formal Invariants
 └── Composition Runtime 5.0
```

**BOOTSTRAP-739 / AXCOMPOSITOR — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-740 — AXDESKTOP

**Native Desktop Environment Runtime — workspaces, virtual desktops, panels, taskbars/docks, launchers, application switching, desktop icons, notifications, system tray/status areas, desktop-level shortcuts, window grouping, tiling, snapping, workspace persistence, session management, multi-monitor desktop topology, desktop policies, application lifecycle integration, secure desktop surfaces, remote desktop semantics, accessibility, deterministic desktop simulation, desktop state replay và Desktop Environment Runtime 5.0.**