# BOOTSTRAP-460 — GRAPHICS, RENDERING PIPELINE, GPU RESOURCE MODEL, SHADER SYSTEM & CROSS-PLATFORM 2D/3D FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của 460 là xây dựng graphics foundation trên BOOTSTRAP-459 mà **không biến graphics thành một phần của language core**.

Nguyên tắc:

```text
Axiom Core
    ↓
Standard Library
    ↓
GPU / Accelerator 459
    ↓
Graphics Foundation 460
    ↓
2D / 3D / GUI / Game / Visualization
```

Graphics API của Axiom phải đủ thấp để xây renderer/engine riêng, nhưng đủ rõ để application không phải trực tiếp thao tác với từng API vendor.

---

## 460.1 — Graphics architecture

Graphics được chia thành:

```text
graphics-core
graphics-device
graphics-memory
graphics-resource
graphics-shader
graphics-pipeline
graphics-command
graphics-renderpass
graphics-framegraph
graphics-texture
graphics-buffer
graphics-sampler
graphics-swapchain
graphics-2d
graphics-3d
graphics-raytracing
graphics-debug
```

Không module nào bắt buộc phải được link nếu chương trình không dùng.

---

## 460.2 — Graphics device

Graphics device được xây trên `Device` của 459.

```text
GraphicsDevice
GraphicsDeviceInfo
GraphicsFeatures
GraphicsLimits
```

---

## 460.3 — Graphics backend

Backend abstraction ban đầu cho:

```text
Vulkan
Direct3D 12
Metal
WebGPU
```

và có thể mở rộng:

```text
OpenGL
OpenGL ES
```

cho legacy/platform compatibility.

---

## 460.4 — Backend independence

Application code không được phụ thuộc trực tiếp vào Vulkan/D3D/Metal nếu sử dụng API graphics portable.

Vendor-specific escape hatch vẫn được phép qua backend API/FFI.

---

## 460.5 — Feature discovery

Graphics feature được query:

```text
compute
indirect_draw
instancing
multisampling
texture_compression
ray_tracing
mesh_shader
bindless
```

---

## 460.6 — Capability-based renderer

Renderer phải có thể chọn pipeline theo capability.

Không assume GPU hiện đại có mọi feature.

---

# 460.7 — Graphics resource model

Các resource chính:

```text
Buffer
Texture
TextureView
Sampler
Shader
Pipeline
BindGroup
RenderPass
Framebuffer
QueryPool
```

---

## 460.8 — Resource ownership

Mọi GPU resource là resource-owning type theo 423.

---

## 460.9 — Resource destruction

Destroy/drop phải tuân thủ 459. Resource đang được GPU sử dụng không được giải phóng trong safe abstraction.

---

## 460.10 — Resource handles

Runtime có thể dùng opaque handles internally.

Public Axiom type không cần expose driver pointer.

---

## 460.11 — Generational handles

Backend có thể sử dụng generation counters để phát hiện stale handle.

---

## 460.12 — Resource identity

Resource identity ổn định trong lifetime của resource.

---

# 460.13 — Buffer

Buffer là vùng GPU-accessible memory có usage contract.

Usage:

```text
Vertex
Index
Uniform
Storage
Indirect
CopySource
CopyDestination
```

---

## 460.14 — Buffer size

Size được biết chính xác.

---

## 460.15 — Buffer alignment

API expose alignment requirements từ device.

---

## 460.16 — Buffer views

Non-owning buffer view có:

```text
buffer
offset
length
element type
```

---

## 460.17 — Typed buffer

Có thể biểu diễn:

```text
Buffer<T>
```

nhưng layout của `T` phải phù hợp shader ABI.

---

## 460.18 — Raw buffer

Byte buffer:

```text
Buffer<u8>
```

được hỗ trợ cho low-level operations.

---

## 460.19 — Vertex buffer

Vertex layout explicit.

---

## 460.20 — Index buffer

Index type phải được khai báo:

```text
u16
u32
```

hoặc loại backend hỗ trợ.

---

# 460.21 — Uniform data

Uniform/constant data là read-only shader resource.

---

## 460.22 — Storage buffer

Storage buffer hỗ trợ read/write GPU data khi target cho phép.

---

## 460.23 — Indirect buffer

Buffer có thể chứa GPU-generated draw/dispatch arguments.

---

## 460.24 — GPU-driven rendering

GPU có thể generate:

```text
draw commands
dispatch commands
instance counts
```

và submit qua indirect APIs.

---

## 460.25 — Persistent resources

Long-lived buffers/textures không bị copy ngầm.

---

# 460.26 — Texture

Texture foundation hỗ trợ:

```text
1D
2D
3D
Cube
Array
CubeArray
```

---

## 460.27 — Texture dimensions

Texture descriptor:

```text
width
height
depth
layers
mip_levels
samples
format
usage
```

---

## 460.28 — Texture format

Formats explicit.

Foundation gồm:

```text
RGBA8
BGRA8
RGBA16F
RGBA32F
R8
RG8
R16F
R32F
depth formats
compressed formats
```

và target-specific formats.

---

## 460.29 — Color space

Texture format và color space là hai khái niệm riêng.

---

## 460.30 — sRGB

sRGB textures/render targets được explicit.

---

## 460.31 — HDR

HDR formats được hỗ trợ qua floating-point/appropriate packed formats.

---

## 460.32 — Depth

Depth textures có format riêng.

---

## 460.33 — Stencil

Depth-stencil formats được hỗ trợ.

---

## 460.34 — Multisampling

MSAA texture có explicit sample count.

---

## 460.35 — Mipmap

Mipmap levels được tạo/upload/generate explicit.

---

## 460.36 — Texture view

TextureView chọn:

```text
mip range
layer range
format interpretation
aspect
```

---

## 460.37 — Texture aliasing

Aliasing/reinterpretation chỉ hợp lệ khi backend/resource format cho phép.

---

## 460.38 — Texture residency

Residency phụ thuộc memory system của 459.

---

## 460.39 — Sparse textures

Sparse/virtual textures là optional advanced capability.

---

## 460.40 — Streaming textures

Texture streaming thuộc higher-level asset system.

---

# 460.41 — Sampler

Sampler mô tả:

```text
min_filter
mag_filter
mipmap_filter
address_u
address_v
address_w
lod_min
lod_max
anisotropy
compare
```

---

## 460.42 — Sampler state

Sampler state immutable sau creation.

---

## 460.43 — Comparison sampler

Depth comparison sampling explicit.

---

## 460.44 — Border color

Backend capability-dependent.

---

## 460.45 — Sampler reuse

Samplers nên được cache/deduplicate ở library level.

---

# 460.46 — Shader model

Shader là GPU program của 459.

Các stage:

```text
Vertex
Fragment
Compute
Geometry
TessellationControl
TessellationEvaluation
Mesh
Task
RayGeneration
AnyHit
ClosestHit
Miss
Intersection
Callable
```

Chỉ stage được backend hỗ trợ mới được sử dụng.

---

## 460.47 — Shader source

Axiom hỗ trợ shader source bằng Axiom shader subset hoặc shader IR.

---

## 460.48 — Shader language

Không tạo một language hoàn toàn độc lập nếu không cần.

Shader sử dụng:

```text
Axiom syntax
+
GPU semantic restrictions
+
shader-specific builtins
```

---

## 460.49 — Shader subset

Shader code không được gọi API OS/runtime tùy ý.

---

## 460.50 — Shader entry point

Mỗi compiled shader artifact có explicit entry point.

---

## 460.51 — Shader stage declaration

Ví dụ conceptual:

```text
shader vertex fn main(input: VertexInput) -> VertexOutput
```

---

## 460.52 — Fragment output

Fragment shader khai báo output/resource semantics.

---

## 460.53 — Compute shader

Compute shader sử dụng kernel execution model của 459.

---

## 460.54 — Shader interfaces

Compiler kiểm tra input/output giữa shader stages.

---

## 460.55 — Interface mismatch

Mismatch là compile/link error.

---

# 460.56 — Shader types

Shader có thể dùng:

```text
scalar
vector
matrix
array
struct
```

từ 430/458.

---

## 460.57 — Shader memory types

Shader type system bổ sung:

```text
uniform
storage
texture
sampler
workgroup
private
```

---

## 460.58 — Shader address spaces

Address-space semantics kế thừa 459.

---

## 460.59 — Shader layout

Compiler phải tính layout theo shader ABI, không đơn giản dùng CPU ABI.

---

## 460.60 — Layout metadata

Shader resource layout được xuất vào semantic metadata 446.

---

# 460.61 — Resource binding

Shader resource binding phải explicit.

Ví dụ conceptual:

```text
@group(0)
@binding(0)
uniform Camera
```

---

## 460.62 — Binding groups

Resource bindings được gom thành logical groups.

---

## 460.63 — BindGroup

`BindGroup` chứa resources tương ứng với shader layout.

---

## 460.64 — BindGroupLayout

Mô tả resource contract.

---

## 460.65 — Binding validation

Runtime/debug build kiểm tra resource compatibility.

---

## 460.66 — Static binding validation

Compiler có thể phát hiện mismatch giữa Axiom shader và host code.

---

## 460.67 — Dynamic binding

Runtime binding được phép cho resource thay đổi.

---

## 460.68 — Bindless

Bindless/resource indexing là optional advanced feature.

---

## 460.69 — Descriptor indexing

Capability-dependent.

---

## 460.70 — Resource arrays

Shader có thể index texture/buffer arrays nếu backend hỗ trợ.

---

# 460.71 — Graphics pipeline

Pipeline gồm:

```text
shader stages
vertex layout
rasterization state
depth/stencil state
blend state
multisample state
primitive topology
resource layouts
```

---

## 460.72 — Immutable pipeline

Pipeline được tạo với explicit state.

---

## 460.73 — Pipeline creation

Creation có thể expensive và được cache.

---

## 460.74 — Pipeline cache

Cache key:

```text
shader hashes
render target formats
vertex layout
pipeline state
device features
backend version
```

---

## 460.75 — Pipeline compilation

Pipeline compilation có thể async nếu backend hỗ trợ.

---

## 460.76 — Pipeline failure

Compilation failure trả typed diagnostic.

---

## 460.77 — Pipeline compatibility

Render pass/target state phải compatible với pipeline.

---

# 460.78 — Render pass

Render pass mô tả rendering operation.

---

## 460.79 — Attachments

Attachment gồm:

```text
color
depth
stencil
resolve
```

---

## 460.80 — Load operation

Explicit:

```text
Load
Clear
DontCare
```

---

## 460.81 — Store operation

Explicit:

```text
Store
DontCare
```

---

## 460.82 — Clear value

Clear value phải đúng format/type.

---

## 460.83 — Resolve

MSAA resolve explicit.

---

## 460.84 — Render pass lifetime

Attachment resources phải sống đến completion.

---

## 460.85 — Subpasses

Portable abstraction không bắt buộc phải expose subpass semantics nếu backend không có tương đương.

---

# 460.86 — Frame graph

Frame graph là higher-level scheduling abstraction.

```text
Pass A
 ↓
Pass B ──→ Pass C
 ↓
Pass D
```

---

## 460.87 — Resource dependencies

Frame graph biết resource read/write dependencies.

---

## 460.88 — Automatic barriers

Frame graph có thể generate GPU barriers từ dependency graph.

---

## 460.89 — No hidden global synchronization

Barriers chỉ được sinh từ dependency graph.

---

## 460.90 — Transient resources

Frame graph có thể allocate transient textures/buffers.

---

## 460.91 — Resource aliasing

Transient resources có thể reuse memory khi lifetimes không overlap.

---

## 460.92 — Aliasing safety

Aliasing chỉ được compiler/runtime thực hiện khi dependency graph chứng minh an toàn.

---

## 460.93 — Pass culling

Pass không ảnh hưởng output có thể bị loại bỏ.

---

## 460.94 — Pass merging

Compatible passes có thể được merge.

---

## 460.95 — Scheduling

Independent passes có thể reorder.

---

## 460.96 — Multi-queue graph

Frame graph có thể target graphics/compute/copy queues.

---

## 460.97 — Queue ownership

Cross-queue transfers được explicit trong graph.

---

## 460.98 — Async compute

Compute pass có thể chạy song song graphics khi dependency cho phép.

---

## 460.99 — Graph compilation

Frame graph có thể compile thành command graph.

---

## 460.100 — Graph cache

Static/repeated frame graphs có thể cache.

---

# 460.101 — Command encoder

Command encoder ghi:

```text
draw
draw_indexed
draw_indirect
dispatch
copy
clear
barrier
begin/end pass
```

---

## 460.102 — Render commands

Các lệnh render cơ bản:

```text
set_pipeline
set_vertex_buffer
set_index_buffer
set_bind_group
set_viewport
set_scissor
draw
draw_indexed
```

---

## 460.103 — Compute commands

```text
set_compute_pipeline
set_bind_group
dispatch
dispatch_indirect
```

---

## 460.104 — Copy commands

```text
copy_buffer
copy_texture
buffer_to_texture
texture_to_buffer
```

---

## 460.105 — Clear commands

Clear buffer/texture explicit.

---

## 460.106 — Timestamp queries

GPU timestamp query optional.

---

## 460.107 — Occlusion queries

Optional.

---

## 460.108 — Pipeline statistics

Optional.

---

## 460.109 — Debug markers

Command streams có thể chứa debug labels trong debug/profile builds.

---

## 460.110 — Command validation

Invalid resource/state combinations phải tạo diagnostic.

---

# 460.111 — Barriers

Graphics API cần explicit resource state transitions ở backend cần chúng.

---

## 460.112 — Portable barrier abstraction

Portable API biểu diễn:

```text
resource
previous usage
next usage
visibility
queue
```

---

## 460.113 — Backend lowering

Vulkan/D3D12/Metal/WebGPU barrier model được backend mapping.

---

## 460.114 — Barrier optimization

Redundant barriers có thể loại bỏ.

---

## 460.115 — Barrier correctness

Optimization không được làm thay đổi memory visibility.

---

# 460.116 — Swapchain

Swapchain liên kết graphics với window system.

---

## 460.117 — Swapchain images

Application acquire image.

---

## 460.118 — Present

Command completion sau đó present.

---

## 460.119 — Present modes

Backend expose:

```text
FIFO
MAILBOX
IMMEDIATE
```

nếu platform hỗ trợ.

---

## 460.120 — VSync

VSync là swapchain/presentation property.

---

## 460.121 — Resize

Resize yêu cầu recreate/reconfigure swapchain khi backend yêu cầu.

---

## 460.122 — Minimized window

Zero-size surface phải được xử lý rõ ràng.

---

## 460.123 — Surface loss

Surface/device loss trả explicit error.

---

## 460.124 — HDR display

HDR presentation capability-dependent.

---

## 460.125 — Color management

Color conversion/presentation profile phải explicit.

---

# 460.126 — Window integration

Graphics foundation kết nối 452:

```text
Window
 ↓
Surface
 ↓
Swapchain
 ↓
Render target
```

---

## 460.127 — No GUI dependency

Graphics không phụ thuộc GUI toolkit.

---

## 460.128 — Headless rendering

Graphics device có thể chạy không cần window.

---

## 460.129 — Offscreen rendering

Texture render targets hỗ trợ server/render-farm/headless use.

---

## 460.130 — Screenshot/readback

Explicit texture-to-buffer/readback.

---

# 460.131 — Vertex model

Vertex là application-defined struct.

---

## 460.132 — Vertex attributes

Attribute descriptor:

```text
location
format
offset
binding
```

---

## 460.133 — Interleaved vertex

Supported.

---

## 460.134 — Separate vertex streams

Supported.

---

## 460.135 — Instancing

Instance buffer/instance rate explicit.

---

## 460.136 — Primitive topology

```text
point
line
triangle
strip
fan
```

target-dependent.

---

## 460.137 — Face culling

```text
none
front
back
```

---

## 460.138 — Front face

CW/CCW explicit.

---

## 460.139 — Depth test

Explicit compare function.

---

## 460.140 — Depth write

Explicit enable/disable.

---

# 460.141 — Blending

Blend state:

```text
src factor
dst factor
operation
```

---

## 460.142 — Independent blending

Optional per-render-target blend state.

---

## 460.143 — Alpha semantics

Premultiplied vs straight alpha phải explicit ở higher-level texture/material layer.

---

## 460.144 — Color write mask

Per-channel write mask.

---

## 460.145 — Stencil

Stencil read/write masks and operations explicit.

---

# 460.146 — Viewport

Viewport có:

```text
x
y
width
height
min_depth
max_depth
```

---

## 460.147 — Scissor

Scissor rectangle explicit.

---

## 460.148 — Dynamic state

Some pipeline state có thể set dynamically nếu backend hỗ trợ.

---

## 460.149 — State validation

Command encoder kiểm tra dynamic state requirements.

---

## 460.150 — No implicit global state

Axiom graphics API không mô phỏng kiểu hidden global state như legacy OpenGL.

---

# 460.151 — 2D rendering

2D foundation gồm:

```text
Sprite
TextureRegion
Quad
Shape
Path
Text
Transform2D
```

---

## 460.152 — 2D batching

Renderer có thể batch các draw calls tương thích.

---

## 460.153 — Instanced sprites

Sprite rendering hỗ trợ instancing.

---

## 460.154 — Texture atlas

Atlas là library-level resource organization.

---

## 460.155 — Nine-patch

Higher-level UI/2D library.

---

## 460.156 — Vector graphics

Path/tessellation library có thể xây trên graphics foundation.

---

## 460.157 — Anti-aliasing

2D AA là renderer/library concern.

---

## 460.158 — Text rendering

Text rendering không thuộc language core.

---

## 460.159 — Glyph atlas

Font renderer có thể dùng GPU texture atlas.

---

## 460.160 — UTF-8

Text pipeline nhận UTF-8 từ Axiom string system.

---

# 460.161 — 3D rendering

3D foundation:

```text
Transform
Camera
Mesh
Material
Texture
Light
RenderTarget
```

---

## 460.162 — Transform

Transform thường gồm:

```text
position
rotation
scale
```

---

## 460.163 — Matrix

Matrix dùng numeric foundation 458.

---

## 460.164 — Coordinate system

Renderer phải document:

```text
handedness
up axis
clip-space convention
depth range
```

---

## 460.165 — No universal coordinate system

Graphics core không ép application dùng một convention duy nhất nếu API semantics không cần.

---

## 460.166 — Camera

Camera là library-level abstraction.

---

## 460.167 — Projection

Perspective/orthographic.

---

## 460.168 — Mesh

Mesh gồm vertex/index streams và optional morph/attribute streams.

---

## 460.169 — Material

Material là higher-level shader/resource binding abstraction.

---

## 460.170 — Material system

Không thuộc graphics core bắt buộc.

---

# 460.171 — Lighting

Graphics foundation không ép một lighting model.

Higher-level library có thể implement:

```text
Phong
PBR
unlit
custom
```

---

## 460.172 — PBR

PBR thuộc rendering library.

---

## 460.173 — Shadow

Shadow mapping thuộc renderer.

---

## 460.174 — Deferred rendering

Optional renderer architecture.

---

## 460.175 — Forward rendering

Supported naturally.

---

## 460.176 — Forward+

Higher-level renderer.

---

## 460.177 — G-buffer

Higher-level renderer resource graph.

---

## 460.178 — Post-processing

Fullscreen passes sử dụng frame graph.

---

## 460.179 — HDR pipeline

HDR render targets + tone mapping pass.

---

## 460.180 — Tone mapping

Library/shader responsibility.

---

# 460.181 — GPU-driven rendering

Foundation supports:

```text
indirect draw
compute culling
GPU-generated instances
GPU-generated command buffers
```

---

## 460.182 — Frustum culling

Can run CPU or GPU.

---

## 460.183 — Occlusion culling

Optional GPU algorithm.

---

## 460.184 — Instance culling

Compute-based.

---

## 460.185 — Meshlet

Meshlet representation is optional advanced feature.

---

## 460.186 — Mesh shaders

Optional backend capability.

---

## 460.187 — Task shaders

Optional.

---

## 460.188 — Bindless renderer

Optional.

---

## 460.189 — Descriptor heap

Backend abstraction where useful.

---

## 460.190 — GPU scene

A high-level GPU scene database can use structured buffers + indirect rendering.

---

# 460.191 — Ray tracing

Ray tracing is optional.

---

## 460.192 — Acceleration structure

Resource:

```text
BLAS
TLAS
```

---

## 460.193 — BLAS

Bottom-level acceleration structure contains geometry.

---

## 460.194 — TLAS

Top-level structure contains instances/transforms.

---

## 460.195 — Ray tracing pipeline

Pipeline stages use 460 shader model.

---

## 460.196 — Ray generation

Explicit ray-generation shader.

---

## 460.197 — Hit shaders

Closest-hit/any-hit/intersection stages as supported.

---

## 460.198 — Ray payload

Payload type must have explicit shader ABI.

---

## 460.199 — Ray recursion

Recursion depth is explicit device/runtime limit.

---

## 460.200 — Ray tracing fallback

Renderer may provide raster/compute fallback at higher level; graphics core does not promise semantic equivalence of performance.

---

# 460.201 — Shader compilation pipeline

```text
Axiom source
 ↓
AST
 ↓
HIR
 ↓
Shader semantic analysis
 ↓
GPU IR
 ↓
Optimization
 ↓
Backend shader IR
 ↓
Device shader artifact
```

---

## 460.202 — Shared compiler

Shader compiler reuses:

```text
lexer
parser
type checker
traits
generics
comptime
layout
optimizer
```

---

## 460.203 — Shader-specific checks

Adds:

```text
stage rules
resource rules
address spaces
uniformity
derivative legality
```

---

## 460.204 — Derivatives

Fragment shader derivatives:

```text
ddx
ddy
fwidth
```

if supported.

---

## 460.205 — Derivative legality

Derivative operations restricted to stages where meaningful.

---

## 460.206 — Texture sampling

Sampling requires texture + sampler/resource contract.

---

## 460.207 — Texture gather

Optional.

---

## 460.208 — Atomic image operations

Capability-dependent.

---

## 460.209 — Barrier operations

Shader barriers map to 459 synchronization.

---

## 460.210 — Shader optimization

Use 437/438 optimizer infrastructure adapted for GPU execution.

---

# 460.211 — Shader specialization

Specialize on:

```text
constant values
feature flags
material configuration
tile sizes
```

---

## 460.212 — Permutation control

Compiler/build system must prevent uncontrolled shader permutation explosion.

---

## 460.213 — Shader variant cache

Variant cache keyed by semantic inputs.

---

## 460.214 — Runtime specialization

Allowed when backend supports JIT/specialization.

---

## 460.215 — Precompiled shader package

Can distribute compiled shader artifacts.

---

## 460.216 — Shader reflection

Compiler-generated metadata is preferred over runtime parsing of shader binaries.

---

## 460.217 — Reflection metadata

Includes:

```text
inputs
outputs
bindings
formats
workgroup size
features
```

---

## 460.218 — Host binding generation

Compiler can generate strongly typed host-side bindings.

---

## 460.219 — Binding mismatch

Mismatch should ideally be caught at compile time.

---

## 460.220 — AI shader knowledge

446 exposes shader semantic metadata.

---

# 460.221 — Graphics memory barriers

Barriers integrate with 459 memory model.

---

## 460.222 — Resource states

Portable states:

```text
VertexRead
IndexRead
UniformRead
StorageRead
StorageWrite
ColorAttachment
DepthAttachment
ShaderRead
CopySource
CopyDestination
Present
```

---

## 460.223 — State transitions

Backend lowers states to native barriers.

---

## 460.224 — Read-after-write

Requires appropriate dependency.

---

## 460.225 — Write-after-read

Requires appropriate dependency.

---

## 460.226 — Write-after-write

Requires serialization/dependency.

---

## 460.227 — Read-after-read

Normally no write visibility barrier required.

---

## 460.228 — Barrier elimination

Compiler/frame graph can eliminate unnecessary barriers.

---

## 460.229 — Barrier diagnostics

Debug tooling can explain why a barrier exists.

---

## 460.230 — AI barrier analysis

AI can query redundant/missing/expensive synchronization.

---

# 460.231 — Asset boundary

Graphics core does not prescribe file formats.

Higher-level asset libraries can support:

```text
PNG
JPEG
KTX2
DDS
glTF
OBJ
custom
```

---

## 460.232 — Asset decoding

CPU-side decode is separate from GPU resource creation.

---

## 460.233 — Streaming

Asset streaming integrates with async 424/454.

---

## 460.234 — Upload queue

Large assets can use asynchronous transfer queues.

---

## 460.235 — Staging buffers

Backend may use staging resources automatically inside explicit upload APIs.

---

## 460.236 — Hidden allocation rule

Temporary staging allocation may be an implementation detail only inside an API whose contract explicitly allows it.

---

## 460.237 — Zero-copy upload

Used when backend permits.

---

## 460.238 — Resource residency manager

Optional higher-level component.

---

## 460.239 — Virtual texture

Optional.

---

## 460.240 — Streaming mipmap

Optional.

---

# 460.241 — Cross-platform mapping

Conceptual:

```text
Axiom Graphics
 ├── Vulkan
 ├── D3D12
 ├── Metal
 └── WebGPU
```

---

## 460.242 — Windows

Primary modern backend:

```text
D3D12
Vulkan
```

---

## 460.243 — Linux

Primary:

```text
Vulkan
```

---

## 460.244 — macOS

Primary:

```text
Metal
```

---

## 460.245 — iOS

Primary:

```text
Metal
```

---

## 460.246 — Android

Primary:

```text
Vulkan
```

---

## 460.247 — Web

Primary:

```text
WebGPU
```

---

## 460.248 — Legacy OpenGL

Optional compatibility layer.

---

## 460.249 — Backend feature matrix

Tooling exposes backend capability matrix.

---

## 460.250 — Portability levels

Renderer can declare:

```text
portable-baseline
enhanced
advanced
vendor-specific
```

---

# 460.251 — Debug graphics

Debug layer validates:

```text
resource lifetime
binding
format
state transitions
pipeline compatibility
command validity
```

---

## 460.252 — GPU labels

All major resources/commands can have developer labels.

---

## 460.253 — GPU capture

Backend integration can export capture information.

---

## 460.254 — Shader source maps

Shader machine instructions map to Axiom source.

---

## 460.255 — Render graph visualization

Frame graph can be exported as machine-readable graph.

---

## 460.256 — Resource lifetime visualization

Tooling can show resource creation/use/destroy.

---

## 460.257 — GPU memory report

Expose:

```text
allocated
resident
transient
staging
peak
```

---

## 460.258 — GPU timing

Expose per-pass/per-kernel timing.

---

## 460.259 — Pipeline statistics

Optional hardware counters.

---

## 460.260 — AI debugging

AI tooling can query:

```text
render pass
resource dependency
shader
pipeline
barrier
GPU timing
memory usage
```

---

# 460.261 — 2D/3D coexistence

2D and 3D renderer may share:

```text
device
buffers
textures
pipelines
frame graph
```

---

## 460.262 — UI rendering

452 GUI can render through 460.

---

## 460.263 — Native widgets

Native widget rendering can remain platform-specific.

---

## 460.264 — Custom UI

Custom GPU UI uses 460.

---

## 460.265 — Text UI

Text rendering library can share GPU resources.

---

## 460.266 — Video rendering

Video frames can become GPU textures through platform/video APIs.

---

## 460.267 — Compute + graphics

Compute kernels can generate data consumed by graphics.

---

## 460.268 — Graphics + compute synchronization

Uses 459/460 resource dependency model.

---

## 460.269 — Shared resources

Buffers/textures can be shared between compute and graphics when usage flags permit.

---

## 460.270 — No duplicate memory requirement

Interop should avoid unnecessary CPU round trips.

---

# 460.271 — Rendering architecture for Axiom

Recommended higher-level stack:

```text
graphics-core
      ↓
render-resource
      ↓
render-command
      ↓
frame-graph
      ↓
renderer-2d / renderer-3d
      ↓
engine / GUI / game / visualization
```

---

## 460.272 — Renderer independence

Applications may bypass high-level renderer and use graphics-core directly.

---

## 460.273 — Engine independence

Axiom does not mandate one game engine architecture.

---

## 460.274 — ECS independence

ECS remains library-level.

---

## 460.275 — Scene graph independence

Scene graph remains library-level.

---

## 460.276 — Material system independence

Material system remains library-level.

---

## 460.277 — Physics independence

Physics remains library/ecosystem.

---

## 460.278 — Audio independence

Audio remains separate subsystem.

---

## 460.279 — Asset pipeline independence

Asset pipeline is build/tool ecosystem.

---

## 460.280 — Graphics foundation completeness

460 must provide enough primitives to implement all those higher-level systems without modifying language core.

---

# 460.281 — Performance model

Graphics API must make expensive operations visible.

---

## 460.282 — No hidden draw calls

High-level batching may combine draws, but low-level API does not silently generate unexpected work.

---

## 460.283 — No hidden synchronization

No implicit global GPU flush.

---

## 460.284 — No hidden CPU-GPU transfer

Low-level graphics APIs do not silently transfer resources between CPU/device.

---

## 460.285 — No hidden allocation

Creation APIs explicitly represent resource allocation.

---

## 460.286 — Command recording

Command recording should be cheap enough for multithreaded rendering.

---

## 460.287 — Multi-thread recording

Independent command buffers can be recorded concurrently.

---

## 460.288 — Worker threads

Rendering library may use worker threads, but they must be explicit runtime/library resources.

---

## 460.289 — Submission thread

Backend may require a dedicated submission context; this must be documented.

---

## 460.290 — Frame latency

Renderer can expose frames-in-flight configuration.

---

# 460.291 — Frames in flight

Multiple frames may execute concurrently.

---

## 460.292 — Per-frame resources

Transient resources can be allocated per frame.

---

## 460.293 — Frame synchronization

Frame fences/events explicitly track reuse.

---

## 460.294 — Triple buffering

Optional presentation strategy.

---

## 460.295 — CPU pacing

Renderer may wait on frame availability, explicitly marked as blocking.

---

## 460.296 — GPU pacing

Presentation backend handles synchronization.

---

## 460.297 — Frame allocator

Arena allocator 423 can efficiently allocate transient frame data.

---

## 460.298 — Frame reset

Frame allocator reset only after dependent GPU work completes.

---

## 460.299 — Resource recycling

Resources can be recycled rather than repeatedly allocated.

---

## 460.300 — Deterministic frame lifecycle

Renderer exposes lifecycle sufficiently for predictable memory/performance behavior.

---

# 460.301 — Compiler integration

Compiler supports graphics through:

```text
type/layout metadata
shader compilation
GPU IR
comptime
resource ABI
reflection metadata
```

---

## 460.302 — Shader compile-time reflection

Shader bindings can be generated at compile time.

---

## 460.303 — Typed pipeline creation

Compiler-generated descriptors can eliminate string-based resource lookup.

---

## 460.304 — Typed vertex layout

Vertex structs can generate GPU layout metadata.

---

## 460.305 — Typed uniform blocks

Uniform structs can generate shader-compatible layouts.

---

## 460.306 — Layout validation

Host/shader layouts are compared at compile time where both are visible.

---

## 460.307 — Semantic hashes

Shader ABI changes invalidate dependent pipeline artifacts.

---

## 460.308 — Incremental shader compilation

Unchanged shaders are reused.

---

## 460.309 — Pipeline cache invalidation

Pipeline invalidation follows shader/resource semantic hashes.

---

## 460.310 — AI metadata

Graphics metadata is integrated into 446.

---

# 460.311 — Graphics testing

Required tests:

```text
resource creation
buffer upload
texture upload
shader compile
pipeline creation
draw
dispatch
synchronization
swapchain
readback
```

---

## 460.312 — Headless test

Most rendering tests should support offscreen targets.

---

## 460.313 — Golden images

Image-based rendering tests can compare against reference images.

---

## 460.314 — Tolerance

Floating/color comparison uses explicit tolerance.

---

## 460.315 — Determinism

Deterministic render tests must control:

```text
GPU target
driver
shader compiler
random seeds
```

---

## 460.316 — Cross-backend tests

Portable shader/render semantics tested across representative backends.

---

## 460.317 — Capability tests

Unsupported feature tests are capability-aware.

---

## 460.318 — Shader fuzzing

Shader parser/type checker/compiler fuzzing integrates with 435.

---

## 460.319 — Render graph fuzzing

Randomized dependency graphs validate barrier/scheduling correctness.

---

## 460.320 — Resource lifetime fuzzing

Stress resource creation/destruction while commands are in flight.

---

# 460.321 — Graphics benchmarks

Measure separately:

```text
CPU submission
command recording
draw calls
GPU frame time
shader compile
pipeline creation
upload bandwidth
readback bandwidth
memory
```

---

## 460.322 — CPU overhead

Measure API submission overhead independently from GPU work.

---

## 460.323 — GPU frame time

Measure GPU timestamp duration.

---

## 460.324 — End-to-end frame

Measure application-visible frame latency separately.

---

## 460.325 — Shader compilation

Cold and cached compilation measured separately.

---

## 460.326 — Pipeline cache

Cache hit/miss rates exposed.

---

## 460.327 — Render graph overhead

Graph compilation and per-frame execution overhead measured separately.

---

## 460.328 — Draw-call scaling

Benchmark varying draw counts.

---

## 460.329 — Resource binding overhead

Benchmark binding strategies.

---

## 460.330 — No aggregate graphics score

450 rules remain unchanged.

---

# 460.331 — Security

Graphics inputs may originate from untrusted assets/shaders.

---

## 460.332 — Shader validation

Safe shader compiler validates type/resource/stage rules.

---

## 460.333 — Foreign shader

Foreign binary shader is an external trust boundary.

---

## 460.334 — Driver boundary

GPU driver remains external trust boundary.

---

## 460.335 — Asset parser

Image/model parsers must treat file data as untrusted.

---

## 460.336 — Resource limits

Applications should impose texture/buffer/shader limits for untrusted content.

---

## 460.337 — Shader compilation sandbox

Build-time shader compilation can be isolated by tooling.

---

## 460.338 — Runtime JIT

Runtime shader compilation is explicit capability.

---

## 460.339 — Executable code

GPU executable code follows 445's executable-memory/trust principles.

---

## 460.340 — No arbitrary shader execution

Loading arbitrary GPU binaries requires explicit API.

---

# 460.341 — Package model

Graphics packages may contain:

```text
shader source
compiled shaders
pipeline descriptions
materials
textures
meshes
```

---

## 460.342 — Cross-platform shader package

Package can include multiple backend artifacts.

---

## 460.343 — Shader source fallback

If compiled artifact unavailable, build system can compile from source.

---

## 460.344 — Offline graphics build

Fully precompiled graphics package supported.

---

## 460.345 — Runtime shader compilation optional

Production builds may omit compiler components.

---

## 460.346 — Shader compiler separation

Runtime application need not ship shader compiler.

---

## 460.347 — Asset compiler

Asset preprocessing belongs tooling.

---

## 460.348 — Build cache

Graphics artifacts use 432/446 cache infrastructure.

---

## 460.349 — Artifact provenance

Shader/pipeline artifacts contain compiler/backend provenance.

---

## 460.350 — Reproducible graphics builds

Same inputs should produce reproducible artifacts where backend guarantees deterministic output.

---

# 460.351 — Hard invariants

1. Graphics is not language core.
2. Graphics is not mandatory runtime.
3. CPU-only applications must not link graphics code.
4. Graphics is built on 459.
5. Device/resource ownership follows 423.
6. GPU resource lifetime is deterministic.
7. In-flight GPU resources cannot be safely destroyed.
8. Buffer ownership is explicit.
9. Texture ownership is explicit.
10. Texture views are non-owning unless explicitly owning.
11. Sampler state is explicit.
12. Resource formats are explicit.
13. Color space is distinct from resource format.
14. Shader stage is explicit.
15. Shader entry point is explicit.
16. Shader ABI is explicit.
17. Host/shader layouts must be compatible.
18. Binding layouts are explicit.
19. Resource binding cannot rely on hidden global state.
20. Pipeline state is explicit.
21. Pipeline compilation can be cached.
22. Shader compilation can be cached.
23. Shader variants have deterministic cache identities.
24. Shader permutation explosion must be controllable.
25. Shader source uses Axiom semantic infrastructure.
26. GPU IR remains vendor-independent.
27. Backend-specific behavior remains backend-specific.
28. Unsupported GPU features produce explicit diagnostics.
29. Workgroup/subgroup semantics follow 459.
30. Graphics synchronization follows 459.
31. Resource barriers are explicit or generated from an explicit dependency graph.
32. Barrier generation must preserve correctness.
33. Redundant barriers may be optimized away.
34. Frame graph is optional.
35. Frame graph may cull unused passes.
36. Frame graph may alias transient resources only when lifetime analysis proves safety.
37. Frame graph may reorder independent work.
38. Multi-queue scheduling remains explicit.
39. Compute and graphics can share GPU resources when legal.
40. CPU/GPU transfers are not hidden at low level.
41. GPU synchronization is not hidden at low level.
42. GPU allocation is not hidden at low level.
43. Command recording can be multithreaded.
44. Command buffers have deterministic lifetime.
45. Swapchain is separate from graphics core resource model.
46. Headless rendering is first-class.
47. Offscreen rendering is first-class.
48. Windowing remains 452's responsibility.
49. GUI is not required for graphics.
50. 2D is implemented above the graphics foundation.
51. 3D is implemented above the graphics foundation.
52. ECS is not part of graphics core.
53. Scene graph is not part of graphics core.
54. Material system is not mandatory.
55. Lighting model is not mandated.
56. PBR is not mandatory.
57. Rasterization is not the only possible rendering model.
58. Ray tracing is optional.
59. Mesh shaders are optional.
60. Bindless is optional.
61. GPU-driven rendering is supported by appropriate primitives.
62. Indirect drawing is supported where backend permits.
63. Compute-driven rendering integrates with 459.
64. Shader reflection should preferably come from compiler metadata.
65. Runtime string reflection is not required.
66. Typed shader/resource bindings are preferred.
67. Shader layout metadata integrates with 446.
68. Graphics debug information integrates with 440.
69. Graphics performance metadata integrates with 450.
70. Graphics security integrates with 445.
71. Graphics packages integrate with 447.
72. Graphics builds integrate with 432.
73. Shader compilation does not require a third-party compiler in the final Axiom architecture.
74. External graphics drivers remain platform dependencies.
75. Vulkan is an optional backend.
76. D3D12 is an optional backend.
77. Metal is an optional backend.
78. WebGPU is an optional backend.
79. OpenGL/OpenGL ES are compatibility backends.
80. Backend-specific APIs remain available as explicit escape hatches.
81. Axiom must not pretend all backends have identical capabilities.
82. Capability discovery is mandatory for optional features.
83. Portability levels must be explicit.
84. Debug validation may be removed from release builds.
85. Profiling instrumentation may be removed from release builds.
86. GPU memory usage must be measurable.
87. GPU timing must be measurable.
88. Shader compilation time must be measurable.
89. CPU submission overhead must be measurable.
90. GPU frame time and end-to-end latency are separate metrics.
91. No universal graphics performance score exists.
92. Rendering correctness tests may use golden images.
93. Floating-point image comparison uses explicit tolerances.
94. Cross-backend tests must account for valid numerical differences.
95. Graphics asset parsers treat input as untrusted.
96. Foreign shader binaries are external trust boundaries.
97. Runtime JIT compilation is explicit.
98. Production applications can omit shader compiler components.
99. Graphics artifacts carry provenance/cache identity.
100. **Axiom graphics must expose enough native GPU control to build a serious 2D/3D renderer while preserving Axiom's core principles: explicit resource ownership, predictable synchronization, zero hidden allocations/transfers, native performance, incremental compilation, cross-platform backends, and no mandatory graphics runtime.**

**BOOTSTRAP-460 hoàn tất.**

---

# BOOTSTRAP-461 — AUDIO, DSP, REAL-TIME AUDIO, MIXING, STREAMING & MEDIA PIPELINE FOUNDATION

Task tiếp theo:

```text
Axiom Core
    ↓
Numeric / SIMD 458
    ↓
GPU / Graphics 459–460
    ↓
Audio Core
    ├── Device
    ├── Stream
    ├── Buffer
    ├── Format
    ├── Mixer
    ├── DSP
    ├── Codec
    ├── Recording
    ├── Playback
    └── Media synchronization
```

461 sẽ khóa kiến trúc cho **audio engine native**, với trọng tâm đặc biệt là:

- low-latency real-time audio;
- audio callback không allocation/block/panic;
- sample format và channel layout;
- ring buffer/lock-free queue;
- mixer;
- DSP graph;
- SIMD audio processing;
- resampling;
- FFT/filter/convolution;
- microphone/recording;
- WAV/FLAC/Opus/AAC/MP3 boundary;
- streaming audio;
- spatial audio;
- 3D audio;
- synchronization với video/graphics;
- async audio;
- audio device hot-plug;
- WASM/mobile/desktop;
- và quan trọng nhất: **không để GC, hidden allocation hoặc scheduler gây jitter vào real-time audio path**.