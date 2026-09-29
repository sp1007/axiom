# BOOTSTRAP-731 — AXGRAPHICS

**Namespace:** `AXGRAPHICS`  
**Phase:** Axiom Civilization Runtime / Native Graphics & Rendering Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXCOMPUTE`, `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXSECURITY`, `AXIDENTITY`, `AXGEOSPATIAL`, `AXMEDIA`, `AXASSET`, `AXENERGY`

> `AXGRAPHICS` là graphics substrate native của Axiom: từ GPU/device abstraction, buffers, textures, shaders, command execution đến 2D/3D rendering, scene, materials, lighting, animation, compute rendering, ray tracing, UI rendering và frame presentation. Nó không phải game engine hay GUI framework.

---

# 731.0 — Mục tiêu

Kiến trúc:

```text
                         AXGRAPHICS
                              │
             ┌────────────────┼────────────────┐
             ↓                ↓                ↓
           GPU              DISPLAY          SCENE
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                        RENDER GRAPH
                              ↓
             ┌────────────────┼────────────────┐
             ↓                ↓                ↓
          RASTER           COMPUTE         RAY TRACE
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                         AXCOMPUTE
```

Mục tiêu chính:

```text
native GPU execution
zero-copy
explicit resource lifetime
deterministic synchronization
low CPU overhead
high throughput
portable backend
compile-time specialization
2D + 3D
real-time + offline rendering
```

---

# 731.1 — Graphics Boundary

`AXGRAPHICS` sở hữu:

```text
graphics device
GPU
adapter
queue
command
command buffer
resource
buffer
texture
sampler
shader
pipeline
descriptor
render pass
render target
framebuffer
mesh
material
camera
light
scene
render graph
animation
particle
rasterization
ray tracing
compute rendering
presentation
display surface
```

Không sở hữu:

```text
physical GPU asset identity → AXASSET
compute resource scheduling → AXCOMPUTE
media codec                → AXMEDIA
physical geography         → AXGEOSPATIAL
persistent storage         → AXSTORAGE
identity/security          → AXIDENTITY / AXSECURITY
```

---

# 731.2 — Graphics Device

```axiom
graphics_device {
    device_id
    adapter
    capabilities
    memory
    queues
}
```

---

# 731.3 — Graphics Adapter

Một hệ thống có thể có:

```text
integrated GPU
discrete GPU
external GPU
virtual GPU
software renderer
```

Adapter discovery:

```axiom
enumerate_graphics_adapters()
```

---

# 731.4 — Capability Model

Capabilities:

```text
shader_model
compute
geometry
tessellation
ray_tracing
mesh_shader
variable_rate_shading
bindless
multiview
sparse_resources
async_compute
hardware_video
```

Không được giả định mọi GPU hỗ trợ cùng feature set.

---

# 731.5 — Graphics Backend

Backend abstraction:

```text
native
vulkan-like
metal-like
direct3d-like
software
```

Tên backend không trở thành semantic của AXGRAPHICS.

---

# 731.6 — Queue

GPU có thể có:

```text
graphics_queue
compute_queue
copy_queue
transfer_queue
```

Queue ownership phải explicit.

---

# 731.7 — Command

```axiom
graphics_command {
    type
    parameters
}
```

Command có thể:

```text
draw
dispatch
copy
clear
barrier
present
```

---

# 731.8 — Command Buffer

```axiom
command_buffer {
    commands
    queue_type
}
```

Có thể record trước:

```text
record
→ validate
→ submit
```

---

# 731.9 — Command Submission

```axiom
submit(
    queue,
    command_buffer,
    dependencies
)
```

Submission không đồng nghĩa command đã hoàn thành.

---

# 731.10 — Fence

```axiom
fence {
    value
}
```

Dùng để đồng bộ GPU/CPU và queue.

---

# 731.11 — Semaphore

```axiom
semaphore {
    signal
    wait
}
```

Cho synchronization giữa execution stages.

---

# 731.12 — Barrier

Resource state transition:

```text
UNDEFINED
↓
COPY_DEST
↓
SHADER_READ
↓
RENDER_TARGET
↓
PRESENT
```

Barrier semantics phải explicit.

---

# 731.13 — Resource

```axiom
graphics_resource {
    resource_id
    type
    memory_domain
    size
}
```

---

# 731.14 — Buffer

```axiom
gpu_buffer<T> {
    element_type
    count
    usage
    memory
}
```

Usage:

```text
vertex
index
uniform
storage
indirect
staging
readback
```

---

# 731.15 — Texture

```axiom
texture<T> {
    width
    height
    depth
    format
    mip_levels
    layers
    usage
}
```

---

# 731.16 — Texture Dimensions

Hỗ trợ:

```text
1D
2D
3D
2D array
cube
cube array
```

---

# 731.17 — Texture Format

Ví dụ:

```text
RGBA8
RGBA16
RGBA16F
RGBA32F
R8
R16F
R32F
D16
D24S8
D32
BC*
ASTC*
```

Format availability phụ thuộc backend/device.

---

# 731.18 — Mipmap

```axiom
generate_mipmaps(texture)
```

Mipmap chain phải có dimension semantics rõ ràng.

---

# 731.19 — Sampler

```axiom
sampler {
    min_filter
    mag_filter
    mip_filter
    address_u
    address_v
    address_w
}
```

Address modes:

```text
repeat
mirror
clamp
border
```

---

# 731.20 — Shader

Shader là executable GPU program:

```axiom
shader {
    stage
    code
    interface
}
```

Stages:

```text
vertex
fragment
geometry
tessellation_control
tessellation_evaluation
compute
mesh
task
ray_generation
closest_hit
any_hit
miss
intersection
```

---

# 731.21 — Shader Source

AXGRAPHICS có thể nhận:

```text
AXIOM shader source
intermediate shader IR
native shader binary
```

Compiler pipeline:

```text
Axiom Shader
 ↓
Shader IR
 ↓
backend compiler
 ↓
GPU binary
```

---

# 731.22 — Shader Type Safety

Shader interface phải kiểm tra:

```text
input type
output type
binding type
resource format
layout
```

từ compile time khi có thể.

---

# 731.23 — Shader Resource Binding

```axiom
shader_binding {
    slot
    resource
    visibility
}
```

---

# 731.24 — Descriptor

```axiom
descriptor {
    resource
    type
}
```

Types:

```text
buffer
texture
sampler
acceleration_structure
```

---

# 731.25 — Bindless

GPU có capability:

```text
bindless_resources
```

Cho phép shader truy cập resource table lớn mà không rebinding từng draw.

---

# 731.26 — Pipeline

```axiom
graphics_pipeline {
    shaders
    vertex_layout
    raster_state
    depth_state
    blend_state
    render_target_formats
}
```

Pipeline có thể compile trước.

---

# 731.27 — Compute Pipeline

```axiom
compute_pipeline {
    shader
    resources
}
```

---

# 731.28 — Render Pipeline

```text
vertex
 ↓
primitive assembly
 ↓
rasterization
 ↓
fragment
 ↓
depth/stencil
 ↓
blend
 ↓
render target
```

---

# 731.29 — Vertex

```axiom
vertex<T> {
    position
    attributes
}
```

Không bắt buộc position phải là một fixed built-in layout ở language level.

---

# 731.30 — Index Buffer

```axiom
index_buffer {
    type = u16 | u32
}
```

---

# 731.31 — Vertex Layout

```axiom
vertex_layout {
    attributes
    stride
    rate
}
```

Attribute có thể:

```text
position
normal
uv
color
tangent
custom
```

---

# 731.32 — Primitive

```text
point
line
triangle
patch
```

---

# 731.33 — Rasterization State

```axiom
raster_state {
    cull_mode
    front_face
    fill_mode
    depth_bias
}
```

---

# 731.34 — Depth/Stencil

```axiom
depth_state {
    test
    write
    compare
}
```

Stencil:

```text
stencil_test
stencil_reference
stencil_mask
```

---

# 731.35 — Blending

```axiom
blend_state {
    source_factor
    destination_factor
    operation
}
```

Có thể có per-render-target blend configuration.

---

# 731.36 — Render Target

```axiom
render_target {
    texture
    load_operation
    store_operation
}
```

---

# 731.37 — Depth Target

```axiom
depth_target {
    texture
    clear_value
    load_operation
    store_operation
}
```

---

# 731.38 — Render Pass

```axiom
render_pass {
    color_targets
    depth_target
    commands
}
```

---

# 731.39 — Framebuffer

Framebuffer là tập resource dùng cho một rendering operation:

```text
color attachments
depth attachment
stencil attachment
```

---

# 731.40 — Render Graph

Đây là thành phần quan trọng.

```axiom
render_graph {
    resources
    passes
    dependencies
}
```

Ví dụ:

```text
Shadow
   ↓
Depth
   ↓
GBuffer
   ↓
Lighting
   ↓
PostProcess
   ↓
UI
   ↓
Present
```

---

# 731.41 — Render Graph Compilation

Runtime phân tích:

```text
resource dependencies
read/write hazards
lifetimes
queue dependencies
barriers
transient resources
```

sau đó compile thành command schedule.

---

# 731.42 — Transient Resource

Resource chỉ tồn tại trong render graph:

```text
pass A
 ↓
temporary texture
 ↓
pass B
 ↓
release
```

Allocator có thể tái sử dụng memory.

---

# 731.43 — Resource Lifetime

Graphics resource có trạng thái:

```text
CREATED
RESIDENT
IN_USE
IDLE
DESTROY_PENDING
DESTROYED
```

Không được destroy khi GPU còn sử dụng.

---

# 731.44 — GPU Memory

Memory domains:

```text
device_local
host_visible
host_coherent
shared
unified
```

Backend mapping implementation-specific.

---

# 731.45 — Memory Allocation

Graphics allocator phải hỗ trợ:

```text
suballocation
alignment
pooling
defragmentation
budget
residency
```

---

# 731.46 — GPU Residency

Khi VRAM giới hạn:

```text
resident
evicted
streamed
```

Runtime phải biết resource residency state.

---

# 731.47 — Streaming Resources

Textures/meshes lớn có thể:

```text
low detail
 ↓
stream higher detail
 ↓
full detail
```

Không làm thay đổi logical asset identity.

---

# 731.48 — Scene

```axiom
scene {
    entities
    hierarchy
    components
    environment
}
```

Scene là logical rendering state, không phải ECS bắt buộc.

---

# 731.49 — Scene Node

```axiom
scene_node {
    transform
    parent
    children
    components
}
```

---

# 731.50 — Transform

```axiom
transform {
    position
    rotation
    scale
}
```

Có thể represent bằng:

```text
TRS
matrix
dual_quaternion
```

---

# 731.51 — Coordinate System

AXGRAPHICS phải support:

```text
right-handed
left-handed
Y-up
Z-up
custom
```

Coordinate convention phải explicit.

---

# 731.52 — Camera

```axiom
camera {
    projection
    position
    orientation
    near
    far
}
```

Projection:

```text
perspective
orthographic
custom
```

---

# 731.53 — Frustum

Camera frustum dùng cho:

```text
culling
LOD
visibility
shadow selection
```

---

# 731.54 — Culling

Core algorithms:

```text
frustum culling
backface culling
occlusion culling
distance culling
portal culling
```

---

# 731.55 — Level of Detail

```axiom
lod {
    levels
    thresholds
}
```

Có thể điều khiển theo:

```text
screen size
distance
performance budget
```

---

# 731.56 — Mesh

```axiom
mesh {
    vertex_buffer
    index_buffer
    primitives
    bounds
}
```

---

# 731.57 — Meshlet

GPU hiện đại có thể dùng:

```axiom
meshlet {
    vertices
    primitives
    bounds
}
```

Phù hợp mesh shader pipeline.

---

# 731.58 — Material

```axiom
material {
    shader
    parameters
    textures
}
```

Material là data, shader là executable.

---

# 731.59 — PBR

Core material model có thể hỗ trợ:

```text
base_color
metallic
roughness
normal
emissive
occlusion
```

PBR không được hard-code thành giới hạn duy nhất.

---

# 731.60 — Texture Coordinates

```axiom
uv
uvw
custom_coordinates
```

---

# 731.61 — Normal Mapping

Material có thể reference:

```text
normal map
tangent basis
```

---

# 731.62 — Lighting

```axiom
light {
    type
    position
    direction
    color
    intensity
}
```

Types:

```text
directional
point
spot
area
environment
```

---

# 731.63 — Shadow

Core shadow primitives:

```text
shadow_map
cascaded_shadow
cube_shadow
ray_traced_shadow
```

---

# 731.64 — Environment

```axiom
environment {
    sky
    atmosphere
    environment_map
}
```

---

# 731.65 — Global Illumination

Architecture phải cho phép:

```text
light probes
voxel GI
screen-space GI
ray-traced GI
path tracing
baked GI
```

Không ép một thuật toán duy nhất.

---

# 731.66 — Ray Tracing

Acceleration structure:

```axiom
bottom_level_acceleration_structure
top_level_acceleration_structure
```

---

# 731.67 — Ray

```axiom
ray {
    origin
    direction
    t_min
    t_max
}
```

---

# 731.68 — Ray Pipeline

```text
ray generation
 ↓
traversal
 ↓
intersection
 ↓
any hit / closest hit
 ↓
miss
```

---

# 731.69 — Ray Query

Ngoài full ray-tracing pipeline:

```axiom
ray_query {
    origin
    direction
}
```

Shader có thể query acceleration structure.

---

# 731.70 — Compute Rendering

GPU compute có thể thực hiện:

```text
particles
culling
animation
skin deformation
post-processing
lighting
simulation
image processing
```

---

# 731.71 — Indirect Rendering

```axiom
draw_indirect()
dispatch_indirect()
```

GPU có thể tự tạo command arguments.

Giảm CPU submission overhead.

---

# 731.72 — GPU-Driven Rendering

Pipeline:

```text
scene data
 ↓
GPU culling
 ↓
GPU LOD
 ↓
indirect commands
 ↓
GPU rendering
```

---

# 731.73 — Particle System

```axiom
particle_system {
    particles
    simulation
    rendering
}
```

Simulation có thể chạy GPU.

---

# 731.74 — Particle State

```axiom
particle {
    position
    velocity
    lifetime
    size
    color
    custom
}
```

---

# 731.75 — Animation

```axiom
animation {
    channels
    keyframes
    duration
}
```

Channels:

```text
translation
rotation
scale
morph
custom
```

---

# 731.76 — Skeleton

```axiom
skeleton {
    bones
    hierarchy
    inverse_bind_matrices
}
```

---

# 731.77 — Skinning

Có thể thực hiện:

```text
CPU
GPU vertex shader
GPU compute
```

---

# 731.78 — Morph Targets

```axiom
morph_target {
    deltas
    weight
}
```

---

# 731.79 — Vector Graphics

Native primitives:

```text
line
polyline
rectangle
circle
ellipse
path
bezier
text
```

---

# 731.80 — Path Rendering

```axiom
path {
    segments
}
```

Segments:

```text
line
quadratic
cubic
arc
```

---

# 731.81 — 2D Rendering

```text
canvas
 ↓
draw calls
 ↓
render graph
 ↓
GPU
```

2D không phải một hệ thống hoàn toàn riêng biệt.

---

# 731.82 — Text Rendering

AXGRAPHICS cung cấp:

```text
glyph atlas
glyph rasterization
vector glyph
text layout primitives
```

Typography semantics cao cấp có thể thuộc UI/text subsystem.

---

# 731.83 — Font Resource

```axiom
font_resource {
    font_data
    glyphs
    metrics
}
```

Font files lưu trữ:

→ `AXSTORAGE`.

---

# 731.84 — UI Rendering Boundary

AXGRAPHICS chỉ cung cấp:

```text
rectangles
paths
text
textures
clipping
transforms
compositing
```

GUI semantics:

→ higher-level `AXUI`.

---

# 731.85 — Display Surface

```axiom
display_surface {
    width
    height
    format
    refresh_rate
}
```

---

# 731.86 — Swapchain

```axiom
swapchain {
    surface
    images
    present_mode
}
```

Present modes:

```text
IMMEDIATE
FIFO
MAILBOX
ADAPTIVE
```

---

# 731.87 — Frame

```axiom
graphics_frame {
    index
    acquire
    render
    present
}
```

---

# 731.88 — Frame Pacing

Runtime theo dõi:

```text
CPU frame time
GPU frame time
display interval
latency
queue depth
```

---

# 731.89 — Variable Refresh

Nếu display hỗ trợ:

```text
VRR
```

runtime có thể điều chỉnh presentation timing.

---

# 731.90 — Multi-Display

```axiom
display_group {
    displays
    synchronization
}
```

Một application có thể render nhiều surfaces.

---

# 731.91 — HDR Display

Display capability:

```text
color space
peak brightness
HDR mode
bit depth
```

---

# 731.92 — XR Boundary

AXGRAPHICS cung cấp rendering primitives cho:

```text
VR
AR
MR
stereo rendering
multiview
```

XR device semantics có thể nằm ở higher-level `AXXR`.

---

# 731.93 — Multi-View Rendering

```axiom
view_group {
    views
}
```

Một scene có thể render:

```text
left eye
right eye
```

trong một submission khi hardware hỗ trợ.

---

# 731.94 — Graphics Resource Sharing

Resource có thể chia sẻ với:

```text
AXMEDIA
AXAI
AXCOMPUTE
```

Ví dụ:

```text
camera frame
 ↓
AXMEDIA
 ↓
GPU texture
 ├── AXGRAPHICS
 └── AXAI
```

---

# 731.95 — Media Interop

AXMEDIA frame:

```text
video_frame
```

có thể map thành:

```text
graphics_texture_view
```

không copy nếu backend hỗ trợ.

---

# 731.96 — Compute Interop

AXCOMPUTE GPU allocation có thể được import:

```axiom
graphics_import_buffer()
graphics_import_texture()
```

---

# 731.97 — AI Interop

AI tensor có thể share GPU resource:

```text
texture
 ↓
tensor view
 ↓
AXAI
```

và ngược lại.

---

# 731.98 — Synchronization Interop

Shared resource phải chia sẻ:

```text
ownership
fence
semaphore
layout/state
```

Không được giả định shared memory đồng nghĩa synchronized.

---

# 731.99 — Graphics Debugging

Native debug primitives:

```text
debug_marker
debug_label
gpu_timestamp
pipeline_statistics
resource_inspection
```

---

# 731.100 — GPU Profiling

Metrics:

```text
GPU duration
queue utilization
memory bandwidth
VRAM usage
pipeline occupancy
shader execution
draw count
dispatch count
```

---

# 731.101 — GPU Timestamp

```axiom
gpu_timestamp {
    value
    queue
}
```

Có thể đo:

```text
pass duration
GPU idle time
queue overlap
```

---

# 731.102 — Render Validation

Validation layer có thể kiểm tra:

```text
resource lifetime
binding compatibility
format compatibility
barrier correctness
shader interface
queue synchronization
```

Validation không nằm trên production hot path bắt buộc.

---

# 731.103 — Graphics Error Model

```text
DEVICE_LOST
OUT_OF_MEMORY
INVALID_RESOURCE
INVALID_PIPELINE
SHADER_COMPILE_ERROR
UNSUPPORTED_FEATURE
SYNC_ERROR
PRESENT_ERROR
```

---

# 731.104 — Device Lost Recovery

Application có thể:

```text
detect
stop submission
release invalid resources
recreate device
recreate resources
resume
```

---

# 731.105 — Shader Compilation Cache

Compiled shader binary có thể cache bằng:

```text
shader_hash
device_id
driver_version
backend_version
compiler_version
```

Cache:

→ `AXSTORAGE`.

---

# 731.106 — Pipeline Cache

Pipeline state có thể precompile:

```text
graphics_pipeline_cache
compute_pipeline_cache
```

Giảm runtime compilation stalls.

---

# 731.107 — Resource Descriptor Cache

Descriptor tables có thể cache nếu:

```text
resource identity
binding layout
sampler state
```

không đổi.

---

# 731.108 — Render Graph Cache

Nếu topology không đổi:

```text
render_graph
 ↓
compiled graph
```

có thể reuse.

---

# 731.109 — Compile-Time Rendering

Axiom có thể express:

```axiom
render_pipeline<MyVertex, PBRMaterial> {
    ...
}
```

Compiler biết:

```text
vertex layout
resource types
shader interface
```

và giảm runtime reflection.

---

# 731.110 — Reflection

Reflection được phép ở tooling/debugging.

Hot path không phụ thuộc runtime reflection.

---

# 731.111 — Graphics Asset Boundary

Asset semantics:

```text
mesh asset
texture asset
material asset
shader asset
animation asset
scene asset
```

Physical asset lifecycle:

→ `AXASSET`.

Graphics runtime chỉ consumes asset data.

---

# 731.112 — Asset Streaming

```text
asset reference
 ↓
AXSTORAGE
 ↓
decode
 ↓
GPU upload
 ↓
resident resource
```

---

# 731.113 — Graphics Cache

Có thể cache:

```text
texture
mesh
shader
pipeline
descriptor
render graph
```

Cache miss không thay đổi scene semantics.

---

# 731.114 — Distributed Rendering

Có thể partition:

```text
frame
tile
camera
scene
render pass
```

Worker:

```text
render node
 ↓
partial result
 ↓
compositor
```

---

# 731.115 — Offline Rendering

AXGRAPHICS phải hỗ trợ:

```text
real-time rasterization
offline rasterization
path tracing
batch rendering
```

---

# 731.116 — Deterministic Rendering

Reference mode:

```axiom
render_config {
    deterministic = true
}
```

Có thể yêu cầu:

```text
fixed random seed
fixed math mode
fixed resource ordering
fixed sampling
```

---

# 731.117 — Rendering Reproducibility

Render metadata có thể ghi:

```text
scene version
shader version
pipeline version
GPU
driver
compiler
configuration
random seed
```

---

# 731.118 — Render Snapshot

```axiom
render_snapshot {
    scene
    resources
    pipeline
    configuration
}
```

Snapshot có thể replay.

---

# 731.119 — Graphics Simulation

Simulation có thể mô phỏng:

```text
GPU load
VRAM
queue contention
frame timing
shader cost
resource streaming
display refresh
```

---

# 731.120 — Graphics Digital Twin

```axiom
graphics_digital_twin {
    device
    queues
    memory
    pipelines
    workloads
    display
}
```

Dùng để benchmark và capacity planning.

---

# 731.121 — Security

Graphics resource access có thể bị giới hạn bởi:

```text
capability
process sandbox
device access policy
memory isolation
```

AXSECURITY là authority.

---

# 731.122 — Privacy

GPU resource có thể chứa:

```text
camera frames
screen content
user interface
private data
```

Do đó resource sharing phải explicit.

---

# 731.123 — Graphics Events

```axiom
graphics_event {
    event_id
    device
    type
    timestamp
}
```

Types:

```text
DEVICE_CREATED
RESOURCE_CREATED
PIPELINE_CREATED
FRAME_SUBMITTED
FRAME_COMPLETED
PRESENTED
DEVICE_LOST
RESOURCE_DESTROYED
```

---

# 731.124 — Native APIs

```axiom
enumerate_adapters()
create_device()
create_queue()

create_buffer()
create_texture()
create_sampler()

create_shader()
compile_shader()

create_graphics_pipeline()
create_compute_pipeline()

create_descriptor()
create_descriptor_set()

create_command_buffer()
record_command()
submit()

create_fence()
create_semaphore()
insert_barrier()

create_render_pass()
create_render_graph()
compile_render_graph()

create_scene()
create_mesh()
create_material()
create_camera()
create_light()

draw()
draw_indexed()
draw_indirect()

dispatch()
dispatch_indirect()

trace_rays()

create_acceleration_structure()
build_acceleration_structure()

create_texture_view()
create_buffer_view()

create_swapchain()
acquire_frame()
present()

create_animation()
create_skeleton()

create_particle_system()

create_canvas()
draw_path()
draw_text()

import_media_texture()
import_compute_buffer()

profile_gpu()
capture_frame()
replay_frame()

simulate_graphics()
create_graphics_digital_twin()
```

---

# 731.125 — Formal Invariants

```text
GFX-INV-01   Graphics device identity is distinct from physical asset identity.
GFX-INV-02   Backend capability is explicit.
GFX-INV-03   Unsupported GPU features are explicit.
GFX-INV-04   Queue type is explicit.
GFX-INV-05   Command submission is asynchronous unless explicitly synchronized.
GFX-INV-06   Command completion is distinguishable from submission.
GFX-INV-07   Resource lifetime cannot end while GPU usage remains pending.
GFX-INV-08   Resource state transitions are explicit.
GFX-INV-09   Shared resources require explicit synchronization.
GFX-INV-10   Memory domain is explicit.

GFX-INV-11   Buffer element layout is explicit.
GFX-INV-12   Texture format is explicit.
GFX-INV-13   Texture dimensions are explicit.
GFX-INV-14   Shader resource interfaces are type-checkable.
GFX-INV-15   Shader stage is explicit.
GFX-INV-16   Pipeline configuration is immutable after compilation.
GFX-INV-17   Descriptor/resource compatibility is validated.
GFX-INV-18   Render targets have explicit formats.
GFX-INV-19   Depth/stencil state is explicit.
GFX-INV-20   Blend state is explicit.

GFX-INV-21   Render graph dependencies are explicit.
GFX-INV-22   Render graph compilation preserves resource hazards.
GFX-INV-23   Transient resources cannot escape their declared lifetime.
GFX-INV-24   GPU-generated commands remain synchronized with consumers.
GFX-INV-25   Coordinate system convention is explicit.
GFX-INV-26   Camera projection parameters are explicit.
GFX-INV-27   Scene transforms preserve hierarchy semantics.
GFX-INV-28   Material data is distinct from shader executable code.
GFX-INV-29   Asset identity is distinct from GPU resource identity.
GFX-INV-30   GPU residency is distinguishable from logical resource existence.

GFX-INV-31   Dropped/evicted resources do not silently change logical asset identity.
GFX-INV-32   Shared media/AI/compute resources preserve synchronization semantics.
GFX-INV-33   Zero-copy paths preserve ownership.
GFX-INV-34   GPU acceleration cannot silently change declared numerical semantics.
GFX-INV-35   Deterministic mode records required execution parameters.
GFX-INV-36   Render replay does not mutate original scene state.
GFX-INV-37   Simulation does not mutate production GPU state.
GFX-INV-38   Debug instrumentation is separable from production hot paths.
GFX-INV-39   Security authority remains outside graphics semantics.
GFX-INV-40   Graphics cache state is never authoritative application state.
```

---

# 731.126 — Performance Architecture

Hot path:

```text
Application
    ↓
Render Graph
    ↓
Compiled Commands
    ↓
GPU Queue
    ↓
GPU
```

Không:

```text
application
 ↓
generic object graph
 ↓
reflection
 ↓
serialization
 ↓
driver wrapper
 ↓
GPU
```

---

# 731.127 — CPU Overhead Reduction

Axiom phải hỗ trợ:

```text
command batching
persistent mapped buffers
bindless resources
indirect drawing
GPU culling
pipeline caching
descriptor caching
render graph compilation
multi-threaded command recording
```

---

# 731.128 — Multi-Threaded Recording

```text
CPU Thread A → command buffer A
CPU Thread B → command buffer B
CPU Thread C → command buffer C
                    ↓
                  merge
                    ↓
                   GPU
```

Không yêu cầu global graphics lock.

---

# 731.129 — NUMA / CPU Affinity

Render workers có thể pin vào CPU locality phù hợp.

GPU submission thread có thể có dedicated affinity.

---

# 731.130 — GPU Memory Efficiency

Ưu tiên:

```text
persistent allocation
suballocation
resource pooling
transient aliasing
streaming
compression
```

---

# 731.131 — Texture Compression

Compressed texture formats được xem là native resource format khi GPU hỗ trợ.

Không decode về RGBA chỉ để lưu trữ nếu shader có thể sample trực tiếp compressed texture.

---

# 731.132 — Geometry Compression

Mesh có thể dùng:

```text
quantized positions
compressed normals
compressed UV
index compression
meshlet representation
```

---

# 731.133 — Shader Specialization

Compiler có thể specialize shader theo:

```text
material feature
light count
texture presence
MSAA
HDR
shadow mode
GPU capability
```

Tránh một shader mega-branch cho mọi trường hợp.

---

# 731.134 — Frame Scheduling

Scheduler tối ưu:

```text
CPU workload
GPU workload
copy workload
display deadline
```

Frame deadline:

```text
frame_start
→ render
→ present
```

---

# 731.135 — Low-Latency Rendering

Hỗ trợ:

```text
late input sampling
short render queues
frame pacing
async compute
direct presentation
```

---

# 731.136 — Graphics + AXMEDIA

Ví dụ camera preview:

```text
Camera
 ↓
AXMEDIA capture
 ↓
GPU texture
 ├── AXGRAPHICS display
 └── AXAI inference
```

Một buffer có thể phục vụ cả ba subsystem.

---

# 731.137 — Graphics + AXCOMPUTE

`AXCOMPUTE` quyết định:

```text
GPU resource availability
scheduling
priority
quota
```

`AXGRAPHICS` quyết định:

```text
render semantics
pipeline dependencies
frame deadlines
```

---

# 731.138 — Graphics + AXSTORAGE

Persistent artifacts:

```text
shader cache
pipeline cache
texture assets
mesh assets
scene files
render snapshots
```

→ AXSTORAGE.

---

# 731.139 — Graphics + AXDATABASE

Database có thể lưu:

```text
asset metadata
material metadata
shader metadata
scene indexes
render statistics
```

Không lưu raw GPU resource state như database row semantics.

---

# 731.140 — Graphics + AXNETWORK

Remote rendering:

```text
client
 ↓
scene/command stream
 ↓
network
 ↓
render node
 ↓
compressed frame
 ↓
client
```

Network semantics → AXNETWORK.

---

# 731.141 — Graphics + AXSECURITY

GPU sandbox phải ngăn:

```text
unauthorized resource access
cross-process memory exposure
untrusted shader escape
device misuse
```

---

# 731.142 — Graphics Application Layers

Các subsystem có thể xây trên `AXGRAPHICS`:

```text
AXUI
AXGAME
AXVFX
AXCAD
AX3D
AXXR
AXSCIENTIFIC
AXSIMULATION
AXVISUALIZATION
```

Không đưa các domain này vào graphics core.

---

# 731.143 — Definition of Done

`BOOTSTRAP-731` phải freeze:

1. Graphics device.
2. Adapter.
3. Capability model.
4. Backend.
5. Queue.
6. Command.
7. Command buffer.
8. Submission.
9. Fence.
10. Semaphore.
11. Barrier.
12. Resource.
13. Buffer.
14. Texture.
15. Texture dimensions.
16. Texture format.
17. Mipmap.
18. Sampler.
19. Shader.
20. Shader compilation.
21. Shader interface.
22. Descriptor.
23. Bindless.
24. Graphics pipeline.
25. Compute pipeline.
26. Vertex model.
27. Index buffer.
28. Vertex layout.
29. Primitive topology.
30. Raster state.
31. Depth/stencil.
32. Blending.
33. Render target.
34. Render pass.
35. Framebuffer.
36. Render graph.
37. Render graph compilation.
38. Transient resources.
39. Resource lifetime.
40. GPU memory.
41. Residency.
42. Streaming.
43. Scene.
44. Scene node.
45. Transform.
46. Coordinate system.
47. Camera.
48. Frustum.
49. Culling.
50. LOD.
51. Mesh.
52. Meshlet.
53. Material.
54. PBR.
55. Lighting.
56. Shadow.
57. Environment.
58. Global illumination.
59. Ray tracing.
60. Acceleration structures.
61. Ray query.
62. Compute rendering.
63. Indirect rendering.
64. GPU-driven rendering.
65. Particles.
66. Animation.
67. Skeleton.
68. Skinning.
69. Morph targets.
70. Vector graphics.
71. Path rendering.
72. 2D rendering.
73. Text rendering.
74. Font resources.
75. UI rendering boundary.
76. Display surface.
77. Swapchain.
78. Frame lifecycle.
79. Frame pacing.
80. VRR.
81. Multi-display.
82. HDR display.
83. XR boundary.
84. Multi-view.
85. Media interop.
86. Compute interop.
87. AI interop.
88. Debugging.
89. GPU profiling.
90. Validation.
91. Error handling.
92. Device recovery.
93. Shader cache.
94. Pipeline cache.
95. Render graph cache.
96. Compile-time graphics.
97. Reflection boundary.
98. Asset integration.
99. Resource streaming.
100. Distributed rendering.
101. Offline rendering.
102. Deterministic rendering.
103. Render snapshots.
104. Graphics simulation.
105. Graphics digital twin.
106. Security.
107. Privacy.
108. Graphics events.
109. Native APIs.
110. Formal invariants.
111. Performance architecture.
112. AXMEDIA integration.
113. AXCOMPUTE integration.
114. AXSTORAGE integration.
115. AXDATABASE integration.
116. AXNETWORK integration.
117. AXSECURITY integration.

---

# 731.144 — Definition of Done

```text
BOOTSTRAP-731
STATUS: COMPLETE / FROZEN

AXGRAPHICS
 ├── GPU Device Runtime
 ├── Resource Runtime
 ├── Shader Runtime
 ├── Pipeline Runtime
 ├── Render Graph
 ├── 2D Renderer
 ├── 3D Renderer
 ├── Rasterization
 ├── Compute Rendering
 ├── Ray Tracing
 ├── Scene Runtime
 ├── Mesh Runtime
 ├── Material Runtime
 ├── Lighting
 ├── Animation
 ├── Particle Runtime
 ├── Vector Graphics
 ├── Text Rendering
 ├── Display / Presentation
 ├── GPU Memory
 ├── GPU Scheduling Integration
 ├── Media Interop
 ├── AI Interop
 ├── Distributed Rendering
 ├── Deterministic Rendering
 ├── Graphics Debugging
 ├── Graphics Simulation
 └── Graphics Digital Twin
```

**BOOTSTRAP-731 / AXGRAPHICS — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-732 — AXUI

**Native User Interface Runtime — windowing, controls, layout, input, text, accessibility, themes, styling, animation, retained/immediate rendering, event routing, focus, clipboard, drag/drop, menus, dialogs, forms, desktop/mobile UI, touch/pen/gamepad input, DPI/scaling, localization, RTL, UI state, data binding, virtualization, GPU rendering, accessibility tree, UI automation, declarative UI, native widgets, application shell, UI composition & UI Runtime 5.0.**