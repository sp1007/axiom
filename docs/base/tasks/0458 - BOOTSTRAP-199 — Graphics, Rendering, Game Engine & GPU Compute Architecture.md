# BOOTSTRAP-199 — Graphics, Rendering, Game Engine & GPU Compute Architecture

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của phần này là mở rộng GPU model đã có thành một graphics stack đủ mạnh cho:

- GUI
- 2D
- 3D
- game engine
- CAD
- visualization
- scientific computing
- AI/tensor
- video processing
- compute
- ray tracing

nhưng **không biến graphics thành một phần bắt buộc của Axiom Core**.

Nguyên tắc trung tâm:

> **Axiom Core định nghĩa execution/storage/capability semantics; Graphics Library định nghĩa GPU resource và rendering semantics; compiler/backend chuyển chúng thành Vulkan/Metal/D3D12/WebGPU hoặc backend khác.**

---

# 199.1. Tách GPU Compute và Graphics

Không tạo một GPU abstraction duy nhất quá lớn.

Có hai lớp:

```text
GPU
├── Compute
│   ├── Kernel
│   ├── Buffer
│   ├── Tensor
│   └── Dispatch
│
└── Graphics
    ├── Texture
    ├── Sampler
    ├── Pipeline
    ├── RenderPass
    ├── Command
    └── RenderGraph
```

Chúng chia sẻ:

```text
Device
Queue
Memory
Synchronization
Resource ownership
Execution domain
```

---

# 199.2. GPU không phải một loại CPU khác

Không mô hình hóa:

```text
GPU = Thread lớn
```

GPU có execution/storage semantics riêng.

Axiom đã có:

```text
ExecutionDomain
StorageDomain
```

nên graphics chỉ mở rộng chúng.

Ví dụ:

```text
CPU
GPU Compute
GPU Vertex
GPU Fragment
GPU Ray
GPU Copy
```

---

# 199.3. Một GPU có nhiều execution queues

GPU device có thể có:

```text
GraphicsQueue
ComputeQueue
CopyQueue
```

Không phải hardware nào cũng có các queue vật lý riêng.

API abstraction cho phép backend map chúng vào target tương ứng.

---

# 199.4. `Device`

`Device` là resource đại diện cho một GPU/device context.

Conceptually:

```axiom
struct Device {
    ...
}
```

Nó là owning resource.

Drop giải phóng resource theo contract.

Không có global singleton GPU bắt buộc.

---

# 199.5. `DeviceBuffer`

```axiom
struct DeviceBuffer<T> {
    ...
}
```

semantic:

- owns device storage
- không Copy
- Move được
- Drop release
- có thể Send/Share tùy device/runtime contract

Truy cập dữ liệu thông qua:

```text
DeviceView<T>
```

không dùng raw pointer trong safe API.

---

# 199.6. CPU `Buffer` và GPU `DeviceBuffer` khác nhau

Không cho:

```text
Buffer<T>
=
DeviceBuffer<T>
```

vì storage domain khác nhau.

```text
CPU memory
GPU device memory
GPU shared memory
external memory
```

là những storage domain khác nhau.

---

# 199.7. Unified memory

Nếu hardware hỗ trợ:

```text
UnifiedBuffer<T>
```

có thể tồn tại.

Nhưng unified memory không được làm thay đổi semantic ownership.

Compiler/runtime vẫn biết:

```text
storage domain
access domain
synchronization state
```

---

# 199.8. GPU View

Tương tự CPU:

```text
view<T>
mut_view<T>
```

GPU có semantic equivalents:

```text
DeviceView<T>
DeviceMutView<T>
```

Nhưng đây là library/compiler GPU types, không cần thêm syntax mới vào Core.

---

# 199.9. Host ↔ Device transfer

Transfer là explicit.

Ví dụ:

```axiom
device.upload(data)
device.download(buffer)
```

hoặc:

```text
copy Host → Device
copy Device → Host
```

Không có implicit:

```text
GPU pointer → CPU pointer
```

---

# 199.10. Zero-copy

Nếu hardware cho phép:

```text
Host
 ↕
Shared/Unified Memory
 ↕
GPU
```

compiler/runtime có thể chọn zero-copy.

Nhưng:

> **Zero-copy là optimization/storage strategy, không phải semantic requirement.**

---

# 199.11. GPU synchronization

GPU synchronization mở rộng memory model hiện có:

```text
Atomic
Fence
Semaphore
Barrier
Event
```

Không tạo một memory model hoàn toàn khác.

---

# 199.12. `GpuEvent`

Launch:

```axiom
let event = queue.submit(...);
```

trả về:

```text
GpuEvent
```

Nó biểu diễn completion dependency.

Không đồng nghĩa với CPU `ThreadHandle`.

---

# 199.13. GPU event và async

Có thể:

```axiom
let event = queue.submit(...);
event.await;
```

nhưng implementation async là library/runtime.

Core chỉ cần hiểu suspension nếu code thực sự là `async`.

---

# 199.14. Command Buffer

GPU operations được ghi vào:

```text
CommandBuffer
```

Ví dụ:

```text
begin
copy
bind
draw
dispatch
barrier
end
```

CommandBuffer là resource có ownership rõ ràng.

---

# 199.15. Command recording

Có thể:

```text
CPU Thread A
   ↓
CommandBuffer A

CPU Thread B
   ↓
CommandBuffer B
```

sau đó:

```text
submit(A, B)
```

Nếu backend cho phép parallel command recording.

---

# 199.16. CommandBuffer không nhất thiết thread-safe

Mặc định:

```text
CommandBuffer
Send = có thể
Share = không
```

tùy implementation.

Không tự động cho phép hai thread mutate cùng command buffer.

---

# 199.17. RenderPass

Render pass biểu diễn:

```text
attachments
load/store
dependencies
subpasses nếu backend cần
```

Nhưng abstraction không bị khóa vào Vulkan-style subpass.

---

# 199.18. Render Graph

Đây là abstraction quan trọng nhất của graphics layer.

Ví dụ:

```text
Shadow
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

Developer khai báo dependency graph.

Framework/compiler/runtime có thể tự:

- schedule
- insert barriers
- allocate transient resources
- alias memory
- reorder independent passes
- merge compatible passes

---

# 199.19. Resource lifetime trong RenderGraph

Một texture:

```text
ShadowMap
```

chỉ cần tồn tại từ:

```text
ShadowPass
```

đến:

```text
LightingPass
```

RenderGraph có thể tự động:

```text
allocate
alias
reuse
release
```

mà không cần developer quản lý từng allocation.

Đây là một ví dụ rất tốt của triết lý:

> **Compiler/runtime complexity thay cho programmer complexity.**

---

# 199.20. Transient resources

RenderGraph hỗ trợ:

```text
TransientTexture
TransientBuffer
```

Compiler/runtime có thể reuse cùng GPU memory cho các resource có lifetime không overlap.

Ví dụ:

```text
A: [-----]
B:       [-----]
```

có thể dùng cùng physical allocation.

---

# 199.21. Resource aliasing

Nếu:

```text
A lifetime != B lifetime
```

thì:

```text
GPU allocation A
      ↓
reused
      ↓
GPU allocation B
```

được phép.

Nếu lifetime overlap:

```text
A [---------]
B    [-----]
```

không được alias nếu không có explicit compatible contract.

---

# 199.22. GPU alias analysis

Đây là phần nối trực tiếp với Axiom capability/alias system.

Compiler/runtime có thể biết:

```text
Resource A
Resource B
```

có:

```text
NO_ALIAS
MAY_ALIAS
UNKNOWN
```

và không được giả định `NO_ALIAS` nếu chưa chứng minh.

---

# 199.23. Barrier inference

Developer không phải viết hàng loạt barrier thủ công trong abstraction-level API.

RenderGraph biết:

```text
Pass A writes Texture X
Pass B reads Texture X
```

nên suy ra:

```text
WRITE → READ dependency
```

và tạo barrier thích hợp.

---

# 199.24. Backend barrier lowering

RenderGraph semantic barrier:

```text
Write → Read
```

có thể thành:

```text
Vulkan barrier
D3D12 resource barrier
Metal encoder boundary
WebGPU synchronization
```

Backend chịu trách nhiệm.

---

# 199.25. Không đảm bảo backend giống nhau hoàn toàn

Nếu target có capability:

```text
RayTracing
MeshShader
Bindless
AsyncCompute
```

framework có thể expose capability detection.

Không giả vờ rằng mọi GPU đều có cùng feature set.

---

# 199.26. GPU feature model

Device query:

```axiom
device.features()
```

trả:

```text
FeatureSet
```

Ví dụ:

```text
RayTracing
MeshShader
VariableRateShading
FP16
BF16
Tensor
Atomics64
```

---

# 199.27. Feature gating

API yêu cầu feature:

```text
ray_tracing_pipeline(...)
```

phải có:

```text
RayTracing
```

Nếu không:

```text
Result<..., UnsupportedFeature>
```

hoặc compile-time target restriction nếu feature là compile-time known.

---

# 199.28. Shader model

Axiom cần giải quyết một câu hỏi quan trọng:

> Shader có phải một ngôn ngữ riêng không?

Quyết định:

**Không tạo một ngôn ngữ shader thứ hai cho Axiom.**

Thay vào đó:

```text
Axiom subset/profile
```

có thể compile thành shader.

---

# 199.29. `@kernel` và graphics entry point

Đã có:

```axiom
@kernel
fn add(...)
```

Graphics bổ sung:

```axiom
@vertex
fn vertex(...)
```

```axiom
@fragment
fn fragment(...)
```

```axiom
@compute
fn compute(...)
```

```axiom
@raygen
fn raygen(...)
```

Đây là compiler annotations, không phải ngôn ngữ mới.

---

# 199.30. Shader legality

Không phải mọi Axiom function đều hợp lệ trong GPU shader.

Compiler kiểm tra:

```text
@fragment fn ...
```

có:

- loại call hợp lệ
- storage hợp lệ
- control flow hợp lệ
- no OS IO
- no arbitrary allocation
- no unsupported recursion
- no invalid synchronization
- valid address spaces

---

# 199.31. Shader address spaces

GPU shader có:

```text
Private
Local
Shared
Uniform
Storage
Constant
```

đây là GPU storage/address-space semantics.

Không cần biến thành `*mut T` variants trong Core.

---

# 199.32. Shader type system

Shader sử dụng cùng:

```text
bool
i/u
f32/f64 nếu target hỗ trợ
vector
matrix
struct
array
enum subset nếu backend cho phép
```

Nhưng compiler kiểm tra legality theo target.

---

# 199.33. CPU/GPU shared types

Một struct:

```axiom
struct Vertex {
    position: Vec3
    normal: Vec3
    uv: Vec2
}
```

có thể dùng ở:

```text
CPU
GPU
```

nếu:

```text
GpuLegal
```

và layout contract phù hợp.

---

# 199.34. GPU layout

Không được giả định:

```text
CPU struct layout == shader layout
```

Compiler tạo:

```text
GpuLayout
```

và kiểm tra:

```text
alignment
padding
offset
scalar/vector layout
```

---

# 199.35. Explicit GPU representation

Có thể dùng:

```axiom
@repr(gpu)
struct Camera {
    ...
}
```

để yêu cầu layout contract.

Không dùng `@repr(C)` như một cách giải quyết mọi GPU ABI.

---

# 199.36. Shader compilation pipeline

```text
Axiom Source
     ↓
AST
     ↓
Typed HIR
     ↓
GPU legality
     ↓
GPU MIR
     ↓
GPU optimization
     ↓
Shader IR
     ↓
Target backend
     ↓
SPIR-V / DXIL / MSL / WGSL / native
```

---

# 199.37. Shader cache

Shader compilation có thể tốn thời gian.

Cache key:

```text
Source fingerprint
+
Shader entry
+
Target GPU
+
Feature set
+
Optimization profile
+
Compiler semantic version
```

đã phù hợp với build/cache architecture.

---

# 199.38. Shader hot reload

Có thể hỗ trợ ở tooling/runtime layer.

Nhưng pipeline:

```text
new shader
 ↓
compile
 ↓
verify
 ↓
ABI/resource layout check
 ↓
replace pipeline
```

Không được bypass verification.

---

# 199.39. Resource binding

Graphics API cần binding:

```text
Texture
Sampler
Buffer
Uniform
Storage
```

Axiom có thể dùng typed descriptors thay vì untyped integer slots ở high level.

Ví dụ concept:

```axiom
struct Material {
    albedo: Texture2D
    normal: Texture2D
    sampler: Sampler
}
```

Compiler/backend sinh binding layout.

---

# 199.40. Bindless

Bindless resources là backend optimization/feature.

Axiom có thể hỗ trợ:

```text
ResourceTable
Handle<Texture>
```

nhưng handle là logical resource identity, không phải raw GPU pointer.

---

# 199.41. Texture

Texture là resource:

```text
Texture2D<T>
Texture3D<T>
TextureCube<T>
TextureArray<T>
```

Có metadata:

```text
format
extent
mip_levels
layers
usage
sample_count
```

---

# 199.42. Typed vs runtime formats

Có thể:

```axiom
Texture2D<Rgba8>
Texture2D<Rgba16F>
Texture2D<Depth24>
```

để compiler biết format.

Nhưng dynamic texture formats vẫn được hỗ trợ bằng runtime descriptor.

---

# 199.43. Sampler

Sampler tách khỏi Texture:

```text
Texture
Sampler
```

cho phép backend reuse sampler state.

---

# 199.44. Pipeline

Graphics pipeline gồm:

```text
Vertex shader
Fragment shader
Raster state
Depth state
Blend state
Vertex layout
Resource layout
```

Pipeline có thể immutable sau creation.

---

# 199.45. Pipeline caching

Runtime có thể cache:

```text
PipelineKey
```

dựa trên:

```text
shader fingerprint
resource layout
render state
target format
device features
```

---

# 199.46. Compute pipeline

Compute:

```text
ComputePipeline
```

chỉ cần:

```text
compute shader
resource layout
workgroup configuration
```

Không kéo graphics subsystem nếu application chỉ dùng compute.

---

# 199.47. Compute và tensor

Tensor library sử dụng cùng:

```text
DeviceBuffer
DeviceView
Kernel
GpuEvent
```

Ví dụ:

```text
Tensor<f32>
   ↓
GPU kernel
   ↓
Tensor<f32>
```

Không cần tạo một GPU runtime thứ hai cho AI.

---

# 199.48. Matrix/tensor layout

Tensor có:

```text
shape
stride
dtype
storage
device
```

Compiler/library có thể tối ưu:

```text
contiguous
broadcast
transpose
tiling
fusion
```

---

# 199.49. Kernel fusion

Ví dụ:

```text
A → add → B → multiply → C
```

compiler/runtime có thể fuse:

```text
A
 ↓
fused kernel
 ↓
C
```

nếu semantic/effect/capability conditions cho phép.

---

# 199.50. CPU/GPU fallback

API high-level:

```axiom
tensor.matmul(a, b)
```

có thể chọn:

```text
CPU SIMD
GPU
special accelerator
```

nhưng semantics giống nhau.

Execution backend là implementation policy.

---

# 199.51. Numerical semantics

GPU fast math không được tự động thay đổi Core numerical semantics.

Nếu muốn:

```text
fast_math
```

phải là explicit profile/annotation/contract.

Ví dụ:

```text
@fast_math
```

cho phép:

- reassociation
- approximate transcendental
- relaxed floating behavior

theo contract.

---

# 199.52. Determinism

Graphics không nhất thiết deterministic pixel-for-pixel trên mọi GPU.

Axiom phân biệt:

```text
semantic determinism
numeric reproducibility
render reproducibility
```

Không tuyên bố GPU rendering giống bit-for-bit giữa mọi vendor.

---

# 199.53. Ray tracing

Ray tracing được model như graphics execution domain/resource capability:

```text
AccelerationStructure
RayTracingPipeline
ShaderBindingTable
```

Không cần thay đổi Core ownership model.

---

# 199.54. Acceleration structures

```text
BLAS
TLAS
```

là GPU resources.

Ownership:

```text
Build
Update
Use
Drop
```

và synchronization được kiểm tra.

---

# 199.55. Mesh/task shaders

Nếu target hỗ trợ:

```text
@mesh
@task
```

được compiler annotation.

Không có:

```text
class MeshShader
```

language primitive.

---

# 199.56. Multi-GPU

Một process có:

```text
Device A
Device B
```

mỗi Device là storage/execution domain riêng.

Resource không tự động chuyển device.

Explicit:

```text
copy
peer_copy
shared_memory
```

---

# 199.57. GPU ownership transfer

Ví dụ:

```text
CPU owns Buffer
 ↓ upload
GPU owns DeviceBuffer
```

không nhất thiết là ownership transfer của cùng object; có thể là copy.

Semantic model phải phân biệt:

```text
copy
move
transfer
alias
shared resource
```

---

# 199.58. External GPU resources

Interop:

```text
CUDA
DirectML
CUDA external memory
Metal external texture
Vulkan external memory
```

được biểu diễn bằng explicit external resource contracts.

Không giả định foreign GPU handle là safe `DeviceBuffer`.

---

# 199.59. GPU synchronization correctness

Ví dụ:

```text
Pass A writes X
Pass B reads X
```

RenderGraph phải chứng minh ordering.

Nếu:

```text
A writes X
B writes X
```

không có ordering:

```text
compile/runtime validation error
```

tùy API abstraction.

---

# 199.60. GPU race detection

Compiler có thể bắt các race statically trong trường hợp biết đủ thông tin.

Runtime/debug layer có thể bổ sung:

```text
validation layers
GPU race analysis
resource tracking
```

Nhưng debug tooling không thay đổi semantics.

---

# 199.61. GPU memory allocation

Không mặc định:

```text
malloc per resource
```

Runtime dùng:

```text
GPU arena
suballocation
buddy allocator
pool
dedicated allocation
```

và resource lifetime từ RenderGraph.

---

# 199.62. Transient GPU allocator

RenderGraph có thể tạo:

```text
TransientHeap
```

và reuse memory dựa trên lifetime graph.

Đây là một điểm Axiom có thể đạt hiệu năng cao mà API vẫn đơn giản.

---

# 199.63. Presentation

Swapchain/presentation là platform capability:

```text
Surface
Swapchain
Present
```

Không có trong GPU Core compute.

---

# 199.64. Headless GPU

Compute application có thể:

```text
Device
Queue
Buffer
Kernel
```

mà không cần:

```text
Window
Surface
Swapchain
```

---

# 199.65. Graphics without window

Server rendering/offscreen:

```text
OffscreenTexture
RenderGraph
GPU
```

không cần GUI runtime.

---

# 199.66. Backend hierarchy

Axiom Graphics API:

```text
Axiom Graphics
       │
       ▼
Graphics Backend Interface
       │
 ┌─────┼────────┬────────┐
 ▼     ▼        ▼        ▼
Vulkan Metal   D3D12   WebGPU
```

Platform-specific implementations nằm ngoài Core.

---

# 199.67. Backend selection

Build target có thể:

```text
graphics_backend = auto
```

hoặc explicit:

```text
vulkan
metal
d3d12
webgpu
```

---

# 199.68. Capability-based backend selection

`auto`:

```text
Target
 ↓
available backend
 ↓
device features
 ↓
select backend
```

không thay đổi source semantics.

---

# 199.69. Graphics package layering

```text
graphics-core
     ↓
graphics-resource
     ↓
graphics-render
     ↓
graphics-ui
     ↓
game/engine frameworks
```

Compute:

```text
gpu-core
   ↓
gpu-compute
   ↓
tensor
```

GUI chỉ phụ thuộc những phần cần thiết.

---

# 199.70. Game engine không phải Core

Axiom không tích hợp:

```text
Entity
Scene
Physics
Animation
Audio
```

vào language Core.

Chúng là framework/library.

---

# 199.71. ECS

Một game engine có thể implement ECS:

```text
Entity
Component
System
```

bằng Axiom struct/generic/iterator/concurrency primitives.

Compiler không cần hiểu ECS.

---

# 199.72. Data-oriented design

Axiom hỗ trợ tự nhiên:

```text
SoA
AoS
AoSoA
```

với explicit layout/types.

Ví dụ:

```text
Position[]
Velocity[]
Health[]
```

có thể được vectorize tốt.

---

# 199.73. GPU-friendly ECS

Engine có thể map:

```text
Component storage
 ↓
DeviceBuffer
 ↓
GPU kernel
```

với explicit transfer/synchronization.

Không cần pointer-heavy object graph.

---

# 199.74. Game frame

Framework có thể tổ chức:

```text
Input
 ↓
Simulation
 ↓
Animation
 ↓
Physics
 ↓
RenderGraph
 ↓
Present
```

Đây là application architecture, không phải language semantics.

---

# 199.75. Frame scheduling

Runtime có thể sử dụng dependency graph:

```text
Physics ─────┐
             ├── Render
Animation ───┘
```

Các task độc lập có thể chạy song song nếu Send/Share/effect rules cho phép.

---

# 199.76. Graphics and async

GPU submission có thể:

```text
async
```

nhưng GPU event != Future.

Adapter:

```text
GpuEvent
 ↓
Future
```

nếu runtime cung cấp.

---

# 199.77. GPU callback safety

Không callback arbitrary CPU closure từ GPU.

GPU completion:

```text
GpuEvent
```

sau đó scheduler/UI/event loop xử lý.

---

# 199.78. Shader and AI tooling

CompilerDB có thể expose:

```text
Shader entry
Resource bindings
GPU legality
Register usage
Shared memory
Occupancy estimate
Target features
```

AI tooling có thể query thay vì đoán từ source.

---

# 199.79. GPU optimization explainability

Tool:

```text
ax explain gpu kernel
```

có thể cho:

```text
vectorization: yes
shared memory: 32 KB
registers: 42
occupancy: constrained
memory-bound: estimated
fusion: applied
```

Các con số runtime/performance estimate phải được phân biệt với semantic facts.

---

# 199.80. Graphics invariants

### `AGFX-20`
Graphics shall remain outside mandatory Language Core.

### `AGFX-21`
GPU compute and graphics shall share the established GPU execution/storage model.

### `AGFX-22`
GPU resources shall have explicit ownership and lifetime semantics.

### `AGFX-23`
CPU and GPU storage domains shall remain distinct unless an explicit shared/unified-memory contract exists.

### `AGFX-24`
Host/device transfers shall not occur implicitly without an explicit semantic contract.

### `AGFX-25`
GPU views shall preserve capability/provenance semantics.

### `AGFX-26`
GPU synchronization shall participate in the Axiom synchronization model.

### `AGFX-27`
GPU events shall represent explicit completion dependencies.

### `AGFX-28`
Command buffers shall obey normal ownership and concurrency rules.

### `AGFX-29`
RenderGraph shall model resource dependencies explicitly.

### `AGFX-30`
Unknown resource overlap shall never be treated as proven non-overlap.

### `AGFX-31`
Transient resources may be physically aliased only when lifetime and compatibility requirements are proven.

### `AGFX-32`
Graphics barriers may be inferred from proven resource dependencies.

### `AGFX-33`
Backend-specific synchronization shall be generated from semantic synchronization requirements.

### `AGFX-34`
GPU resource layouts shall be explicit and target-valid.

### `AGFX-35`
CPU layout compatibility shall not be assumed to imply GPU layout compatibility.

### `AGFX-36`
Axiom shader entry points shall use the Axiom type/ownership model subject to GPU legality restrictions.

### `AGFX-37`
Shader compilation shall pass through normal type and safety verification.

### `AGFX-38`
GPU shader code shall not acquire host OS authority implicitly.

### `AGFX-39`
GPU code shall not perform unsupported arbitrary allocation or blocking operations.

### `AGFX-40`
GPU feature requirements shall be explicit.

### `AGFX-41`
Backend differences shall not alter defined Axiom semantics.

### `AGFX-42`
Fast-math or relaxed numerical semantics shall require an explicit contract.

### `AGFX-43`
GPU resource allocation strategy shall remain an implementation concern unless storage behavior is explicitly observable.

### `AGFX-44`
Graphics APIs shall support headless/offscreen execution.

### `AGFX-45`
Compute-only programs shall not require graphics/window runtime components.

### `AGFX-46`
GUI shall not require a graphics presentation surface when operating headlessly.

### `AGFX-47`
GPU and graphics libraries shall be removable from programs that do not use them.

### `AGFX-48`
Graphics backends shall be replaceable without changing language semantics.

### `AGFX-49`
GPU external-resource interop shall use explicit foreign-resource contracts.

### `AGFX-50`
GPU-generated code shall be reverified before execution.

### `AGFX-51`
GPU memory lifetime shall not depend on garbage collection.

### `AGFX-52`
RenderGraph optimization shall preserve semantic resource dependencies.

### `AGFX-53`
Graphics optimizations shall not weaken ownership, capability, synchronization, or numerical guarantees.

### `AGFX-54`
Axiom shall support CPU fallback where a library abstraction defines equivalent semantics.

### `AGFX-55`
GPU tooling shall expose structured compiler/runtime facts to IDE and AI tools.

### `AGFX-56`
Shader and graphics artifacts shall participate in deterministic build/cache identity.

### `AGFX-57`
GPU pipeline caching shall be keyed by semantic/resource/backend-relevant fingerprints.

### `AGFX-58`
Axiom shall not require a single graphics API as the universal backend.

### `AGFX-59`
Game-engine abstractions shall remain libraries/frameworks rather than Core language primitives.

### `AGFX-60`
Graphics architecture shall support 2D, 3D, compute, ray tracing and visualization without requiring all subsystems simultaneously.

---

# Kiến trúc Graphics hoàn chỉnh

```text
                         AXIOM GPU
                            │
              ┌─────────────┴─────────────┐
              │                           │
          COMPUTE                     GRAPHICS
              │                           │
       ┌──────┴──────┐             ┌──────┴──────┐
       │             │             │             │
     Kernel       Tensor         Render       Ray Trace
       │             │             │             │
       └──────┬──────┘             └──────┬──────┘
              │                           │
              └───────────┬───────────────┘
                          ▼
                   GPU Resources
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Buffer      Texture      Sampler
              │           │           │
              └───────────┼───────────┘
                          ▼
                     RenderGraph
                          │
                    CommandBuffer
                          │
                 ┌────────┼────────┐
                 ▼        ▼        ▼
              Vulkan    Metal    D3D12
                 │        │        │
                 └────────┼────────┘
                          ▼
                       Hardware
```

Điểm rất quan trọng: **RenderGraph + ownership/capability + compiler-generated synchronization** là nơi Axiom có thể làm API cấp cao nhưng vẫn đạt hiệu năng gần với API GPU thấp cấp.

---

# BOOTSTRAP-200 — AI, Tensor, Automatic Differentiation & Heterogeneous Computing

**TRẠNG THÁI: NEXT**

Đây là một mốc lớn vì nó chạm trực tiếp mục tiêu ban đầu của Axiom: **AI support trên CPU + GPU theo kiểu PyTorch nhưng không cần một runtime khổng lồ và không hy sinh hiệu năng native.**

Cần chốt:

```text
Axiom
 │
 ├── Scalar
 ├── SIMD
 ├── Matrix
 ├── Tensor
 ├── GPU Kernel
 ├── Automatic Differentiation
 ├── Graph Compilation
 ├── CPU backend
 ├── GPU backend
 └── Accelerator backend
```

Các vấn đề quan trọng:

- Tensor có phải Core type không?
- Shape là compile-time hay runtime?
- Static shape + dynamic shape.
- `Tensor<f32, [N,M]>`.
- Layout/stride.
- Broadcasting.
- View/slice/reshape/transpose không copy.
- Ownership của tensor storage.
- CPU/GPU unified API.
- Kernel fusion.
- Lazy graph vs eager execution.
- Automatic differentiation.
- Reverse/forward mode.
- Gradient ownership.
- Memory planning.
- Operator registry.
- Custom kernels.
- Quantization: INT8/FP16/BF16/FP8.
- Mixed precision.
- SIMD/vectorization.
- GPU tensor cores.
- accelerator/NPU.
- distributed tensors.
- compile-time shape reasoning.
- dynamic graph.
- static graph.
- AI model serialization.
- ONNX/foreign model interoperability.
- checkpointing.
- inference vs training.
- graph compilation/cache.
- làm sao để **AI programming trong Axiom không biến thành một Python-like dynamic runtime**, mà vẫn giữ được native performance và type safety.