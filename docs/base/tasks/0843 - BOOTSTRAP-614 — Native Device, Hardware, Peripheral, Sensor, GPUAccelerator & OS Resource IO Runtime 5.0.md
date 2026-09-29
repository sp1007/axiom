:::writing{variant="document" id="58327" title="BOOTSTRAP-614 — Native Device, Hardware, Peripheral, Sensor, GPU/Accelerator & OS Resource I/O Runtime 5.0"}

# BOOTSTRAP-614 — Native Device, Hardware, Peripheral, Sensor, GPU/Accelerator & OS Resource I/O Runtime 5.0

**Status:** Architecture Specification — Completed  
**Layer:** Native Hardware / Device / OS Integration  
**Depends on:** BOOTSTRAP-600..613  
**Primary dependencies:** 603 Security, 606 Resource Governor, 607 Scheduler, 608 Synchronization, 609 Networking, 610 Cryptography, 611 Storage, 613 Packaging

---

# 1. Purpose

BOOTSTRAP-614 defines Axiom's unified native abstraction for interacting with:

- CPUs;
- memory and NUMA topology;
- GPUs;
- NPUs;
- AI accelerators;
- displays;
- keyboards;
- mice;
- touch devices;
- cameras;
- microphones;
- speakers;
- audio devices;
- serial ports;
- USB devices;
- Bluetooth devices;
- HID devices;
- game controllers;
- sensors;
- timers/clocks;
- storage devices;
- network interfaces;
- PCI/PCIe devices;
- platform-specific hardware;
- embedded peripherals;
- OS device resources.

The design must expose hardware without turning the language runtime into an enormous platform-specific framework.

The central abstraction is:

```text
Axiom Application
       ↓
Device / Hardware API
       ↓
Capability
       ↓
Resource Governor
       ↓
Device Backend
       ↓
Operating System
       ↓
Hardware
```

---

# 2. Design Goals

614 must provide:

1. native performance;
2. predictable overhead;
3. capability-controlled access;
4. asynchronous operation;
5. zero-copy where possible;
6. explicit resource ownership;
7. deterministic device lifetime;
8. cross-platform abstractions;
9. platform-specific escape hatches;
10. GPU/accelerator support;
11. CPU topology discovery;
12. device enumeration;
13. hot-plug handling;
14. event-driven I/O;
15. bounded resource consumption;
16. safe device handles;
17. no mandatory garbage collector;
18. no mandatory third-party runtime;
19. struct-only APIs;
20. compiler-visible hardware metadata.

---

# 3. Non-Goals

614 does not attempt to become:

- a complete graphics engine;
- a complete audio engine;
- a complete ML framework;
- a complete OS kernel API;
- a universal device-driver framework;
- a hardware abstraction that hides every platform difference;
- a mandatory GUI toolkit.

Those may be built above 614.

---

# 4. Fundamental Principle

Axiom exposes a **common semantic layer**, not a lowest-common-denominator API.

Therefore:

```text
common capability
+
common lifetime model
+
common synchronization
+
common scheduling
+
common resource accounting
+
platform-specific extension
```

is preferred over forcing every platform into identical semantics.

---

# 5. Device Model

Every device is represented logically as:

```text
Device {
    id
    class
    generation
    state
    capabilities
    properties
}
```

Identity:

```text
DeviceId = {
    provider
    physical_id
    generation
}
```

Generation prevents stale handles from accidentally referencing a newly attached device.

---

# 6. Device Classes

Base classes:

```text
CPU
Memory
GPU
NPU
Accelerator
Display
Camera
Microphone
Speaker
AudioInput
AudioOutput
HID
Keyboard
Mouse
Touch
Gamepad
Sensor
USB
Bluetooth
Serial
Network
Storage
PCI
Virtual
Other
```

New classes can be added without changing the core handle model.

---

# 7. Device State

Common states:

```text
Discovered
Available
Opening
Open
Suspended
Reconnecting
Unavailable
Removed
Faulted
Closed
```

State transitions are explicit.

---

# 8. Device Discovery

API:

```text
DeviceManager.enumerate()
DeviceManager.find()
DeviceManager.watch()
```

Enumeration returns metadata without necessarily opening the device.

This is important for security and performance.

---

# 9. Device Metadata

Metadata may include:

```text
vendor
model
serial
bus
driver
firmware
architecture
features
memory
power_state
location
permissions
```

Sensitive identifiers are policy-controlled.

---

# 10. Device Provider

Platform backend:

```text
trait DeviceProvider {
    fn enumerate(...)
    fn open(...)
    fn close(...)
    fn watch(...)
}
```

Implementations:

```text
WindowsDeviceProvider
LinuxDeviceProvider
MacOSDeviceProvider
AndroidDeviceProvider
IOSDeviceProvider
WasmDeviceProvider
EmbeddedDeviceProvider
```

---

# 11. Device Capabilities

A device exposes capabilities:

```text
DeviceCapability {
    read
    write
    stream
    configure
    control
    map_memory
    execute
    reset
}
```

Possessing a `DeviceHandle` does not automatically imply every operation.

---

# 12. Capability Integration

Opening a device requires BOOTSTRAP-603 authority.

Examples:

```text
camera.open()
```

requires:

```text
camera.read
```

GPU compute requires:

```text
gpu.compute
```

Microphone input:

```text
microphone.capture
```

USB raw access:

```text
device.usb.raw
```

---

# 13. Capability Attenuation

A device handle can be restricted:

```text
read_only = device.attenuate(Read)
```

A child component must never receive more authority than its parent.

---

# 14. Device Handle

Device handles are opaque:

```text
DeviceHandle<T>
```

Internally:

```text
slot
generation
rights
provider
```

Stale generation detection prevents use-after-remove.

---

# 15. Device Lifetime

Default:

```text
open
→ use
→ close
```

No implicit finalizer is required.

Resource lifetime is deterministic.

---

# 16. Device Removal

If hardware disappears:

```text
Open
 ↓
Removed
```

existing operations return:

```text
DeviceRemoved
```

The handle becomes invalid for new operations.

---

# 17. Hot Plug

Device watchers emit:

```text
DeviceAdded
DeviceRemoved
DeviceChanged
DeviceSuspended
DeviceResumed
DeviceFaulted
```

Events are delivered asynchronously through BOOTSTRAP-607.

---

# 18. Device Event Ordering

Events from one physical device are ordered.

Across unrelated devices no global ordering is guaranteed.

This avoids a global synchronization bottleneck.

---

# 19. Device I/O Model

All I/O should support:

```text
synchronous
asynchronous
streaming
buffered
zero-copy
```

where supported by the underlying device.

---

# 20. Common I/O Interface

```text
trait DeviceIo {
    fn read(...)
    fn write(...)
    fn submit(...)
    fn cancel(...)
    fn flush(...)
}
```

Device-specific operations remain separate.

---

# 21. Async Device Operations

Every async operation returns a scheduler-compatible handle:

```text
IoOperation<T>
```

It integrates with:

```text
await
CancelToken
Deadline
Executor
```

from BOOTSTRAP-607.

---

# 22. DMA Model

Devices may transfer data using DMA.

Axiom abstracts:

```text
DmaBuffer
DmaRegion
DmaMapping
```

The application does not manipulate physical addresses directly.

---

# 23. DMA Security

DMA mappings require explicit capability.

The runtime must prevent arbitrary device DMA from accessing unrelated application memory.

---

# 24. DMA Ownership

A DMA buffer has:

```text
owner
device
direction
size
state
mapping
```

Directions:

```text
HostToDevice
DeviceToHost
Bidirectional
```

---

# 25. DMA Synchronization

On platforms requiring cache maintenance:

```text
flush_for_device()
invalidate_from_device()
```

are explicit backend operations.

Architectures with coherent DMA may implement them as no-ops.

---

# 26. Shared Buffers

A buffer can be shared between:

```text
CPU
GPU
NPU
camera
audio
network
storage
```

when the platform supports it.

The runtime tracks ownership and synchronization.

---

# 27. Buffer State

```text
CPUOwned
DeviceOwned
Shared
Pending
Mapped
Unmapped
Invalid
```

Invalid transitions are rejected.

---

# 28. Zero-Copy

Zero-copy is preferred when:

```text
same physical storage
compatible device mapping
compatible lifetime
correct synchronization
```

can be guaranteed.

Otherwise a copy is explicit or internally performed.

---

# 29. Copy Semantics

Axiom must not falsely promise zero-copy.

APIs may expose:

```text
copy_required()
```

or capability metadata.

---

# 30. Memory Integration

Device memory is integrated with BOOTSTRAP's memory model as a distinct memory domain:

```text
HostMemory
DeviceMemory
UnifiedMemory
MappedMemory
PinnedHostMemory
SharedMemory
```

---

# 31. Device Memory

GPU/NPU memory:

```text
DeviceAllocation<T>
```

is not an ordinary CPU pointer.

CPU access requires an explicit mapping or unified-memory capability.

---

# 32. Address Model

Axiom must not expose arbitrary physical addresses as ordinary application values.

Physical addresses belong to privileged driver/kernel boundaries.

This preserves safety and portability.

---

# 33. CPU Topology

614 exposes:

```text
CpuTopology {
    logical_cpus
    physical_cores
    packages
    numa_nodes
    cache_levels
    feature_sets
}
```

---

# 34. CPU Features

Feature discovery:

```text
SSE
SSE2
AVX
AVX2
AVX512
NEON
SVE
SVE2
AES
SHA
FMA
```

and future features.

Compiler can specialize code based on these capabilities.

---

# 35. CPU Dispatch

Axiom supports:

```text
if cpu.has(AVX2)
    fast_path()
else
    fallback()
```

The compiler may generate multi-versioned functions:

```text
generic
SSE
AVX2
AVX512
NEON
SVE
```

---

# 36. Compile-Time CPU Features

Compiler target metadata:

```text
@target(cpu = "x86-64-v3")
```

or:

```text
@requires_cpu("avx2")
```

The compiler must reject unsupported deployment targets when the requirement is mandatory.

---

# 37. Runtime CPU Dispatch

For portable binaries:

```text
dispatch(feature_set)
```

selects the best supported implementation.

The dispatch result may be cached.

---

# 38. NUMA

If supported:

```text
NumaTopology
NumaNode
```

provide:

```text
memory_size
cpu_set
distance
```

Scheduler and allocator can use this information.

---

# 39. NUMA Allocation

Optional:

```text
allocate_on(node)
allocate_local_to(cpu)
interleave(nodes)
```

These are performance hints unless policy makes them strict.

---

# 40. Cache Topology

Expose:

```text
L1
L2
L3
```

sizes and sharing relationships.

Applications can use this for high-performance algorithms without depending on hard-coded CPU assumptions.

---

# 41. Power and Thermal Information

Where available:

```text
PowerState
Temperature
ThermalState
BatteryState
```

are read-only device/system metrics.

They are advisory unless explicitly documented by the platform.

---

# 42. GPU Architecture

GPU is represented as:

```text
GpuDevice
GpuContext
GpuQueue
GpuBuffer
GpuTexture
GpuPipeline
GpuFence
GpuEvent
```

---

# 43. GPU Backend Boundary

Supported conceptual backends:

```text
Direct3D
Vulkan
Metal
OpenGL
OpenCL
CUDA
HIP
WebGPU
Platform-specific
```

No single API is mandatory.

---

# 44. GPU Runtime Principle

Axiom's core runtime defines:

```text
resource lifetime
memory model
command submission
synchronization
capabilities
```

while backend modules implement actual API translation.

---

# 45. GPU Adapter Discovery

```text
GpuManager.enumerate()
```

returns:

```text
vendor
model
driver
VRAM
shared_memory
compute_units
features
queues
formats
limits
```

---

# 46. GPU Context

A GPU context owns:

```text
queues
allocators
pipelines
descriptor state
device synchronization
```

Context lifetime is explicit.

---

# 47. GPU Queue

Queue types:

```text
Graphics
Compute
Transfer
Copy
VideoDecode
VideoEncode
```

Actual availability is device-dependent.

---

# 48. GPU Command Buffer

Commands are recorded:

```text
CommandBuffer.begin()
...
CommandBuffer.end()
queue.submit(command_buffer)
```

Command buffers are reusable only when the backend guarantees it.

---

# 49. GPU Synchronization

GPU synchronization uses:

```text
Fence
Semaphore
Event
Barrier
TimelineValue
```

where supported.

These integrate with BOOTSTRAP-608.

---

# 50. GPU/CPU Synchronization

Example:

```text
CPU writes buffer
→ memory barrier
→ GPU reads
→ GPU fence
→ CPU reads
```

The runtime must make ownership transitions explicit.

---

# 51. GPU Memory Allocation

Allocation classes:

```text
DeviceLocal
HostVisible
HostCoherent
HostCached
Unified
Transient
```

Backend reports actual properties.

---

# 52. GPU Memory Pools

The runtime may use:

```text
PageAllocator
SlabAllocator
BuddyAllocator
Suballocator
```

internally.

Applications see logical allocations.

---

# 53. GPU Memory Budget

GPU allocations count against BOOTSTRAP-606.

Metrics:

```text
allocated
resident
committed
mapped
evicted
```

where supported.

---

# 54. GPU Out-of-Memory

Failure:

```text
GpuOutOfMemory
```

must not silently fall back to arbitrary host allocation.

Fallback requires explicit application policy.

---

# 55. GPU Pipeline

Pipeline objects represent compiled device programs:

```text
ComputePipeline
GraphicsPipeline
RayTracingPipeline
```

where supported.

---

# 56. Shader Model

614 only defines loading and execution boundaries.

A future graphics/shader subsystem defines:

```text
shader language
reflection
pipeline layout
material system
render graph
```

---

# 57. GPU Program Security

GPU executable code requires:

```text
gpu.execute
```

and may require package trust.

Unsigned/untrusted shader packages can be blocked by deployment policy.

---

# 58. GPU Binary Cache

Compiled GPU pipelines can use BOOTSTRAP-613 content-addressed cache.

Cache key includes:

```text
shader hash
driver version
GPU identity
pipeline configuration
compiler version
```

---

# 59. GPU Cache Invalidity

Driver updates may invalidate GPU binary caches.

The cache must therefore be disposable.

---

# 60. NPU / AI Accelerator

Generic abstraction:

```text
AcceleratorDevice
AcceleratorContext
AcceleratorBuffer
AcceleratorGraph
AcceleratorCommand
```

---

# 61. Accelerator Backends

Examples:

```text
DirectML
Core ML
NNAPI
TensorRT
CUDA
ROCm
Metal
Vulkan Compute
WebGPU
vendor-specific NPU
```

These are optional providers.

---

# 62. Accelerator Model

The core API should support:

```text
tensor
buffer
graph
operator
compiled graph
queue
event
```

without forcing one tensor framework into the language core.

---

# 63. Accelerator Memory

AI workloads commonly use:

```text
Host → Device
Device → Device
Device → Host
```

and should reuse 614's shared-buffer and DMA model.

---

# 64. Accelerator Graph

A graph:

```text
input
 ↓
operator
 ↓
operator
 ↓
output
```

can be compiled into backend-specific executable state.

---

# 65. Accelerator Compilation

Compiled graphs may be cached through BOOTSTRAP-613.

Cache key:

```text
graph fingerprint
device fingerprint
backend version
compiler options
```

---

# 66. Accelerator Synchronization

Accelerator completion integrates with:

```text
Future
Fence
Event
Task
```

so CPU threads do not need busy waiting.

---

# 67. Display Devices

Generic:

```text
DisplayDevice
DisplayMode
DisplaySurface
DisplayFrame
```

Metadata:

```text
resolution
refresh_rate
pixel_format
HDR
color_space
orientation
```

---

# 68. Display Enumeration

Applications can enumerate:

```text
primary display
secondary display
virtual display
headless target
```

without assuming a GUI exists.

---

# 69. Presentation

Display subsystem exposes:

```text
acquire_frame()
present(frame)
```

Synchronization may use:

```text
vsync
fence
present_event
```

---

# 70. Windowing Boundary

Window creation belongs above the low-level display API.

614 provides the display/device primitives needed by a future GUI/windowing subsystem.

---

# 71. Camera Model

```text
CameraDevice
CameraFormat
CameraStream
CameraFrame
```

Metadata:

```text
resolution
pixel_format
fps
exposure
gain
focus
orientation
```

---

# 72. Camera Capture

Pipeline:

```text
Camera
 ↓
DMA buffer
 ↓
Frame
 ↓
Application / GPU / Encoder
```

Zero-copy paths should be preferred where supported.

---

# 73. Camera Permissions

Opening camera requires:

```text
camera.capture
```

and OS-level user permission where applicable.

Axiom capability does not bypass OS consent.

---

# 74. Camera Hot Plug

USB cameras may appear/disappear.

The stream must emit:

```text
CameraDisconnected
```

rather than blocking indefinitely.

---

# 75. Microphone

```text
AudioInputDevice
AudioFormat
AudioStream
AudioBuffer
```

supports:

```text
sample_rate
channels
sample_format
buffer_size
```

---

# 76. Speaker

```text
AudioOutputDevice
```

supports:

```text
play
pause
flush
drain
```

with explicit buffering semantics.

---

# 77. Audio Clock

Audio devices may have independent clocks.

The runtime must expose:

```text
AudioClock
```

for synchronization with:

```text
system clock
video clock
network clock
```

---

# 78. Audio Latency

Applications can request:

```text
low_latency
balanced
power_efficient
```

The backend reports actual achievable latency.

---

# 79. Audio Real-Time Safety

Real-time audio callbacks must avoid:

- blocking locks;
- arbitrary allocation;
- filesystem access;
- network access;
- unbounded operations.

The compiler/runtime should provide annotations to detect violations where possible.

---

# 80. HID Devices

Generic HID:

```text
HidDevice
HidReport
HidDescriptor
```

supports:

```text
input
output
feature
```

---

# 81. Keyboard

Keyboard events:

```text
KeyDown
KeyUp
TextInput
ModifierChanged
```

Physical key identity and logical text input must remain distinct.

---

# 82. Mouse

Events:

```text
Move
ButtonDown
ButtonUp
Wheel
DeviceAdded
DeviceRemoved
```

Raw mouse input may be exposed under a separate capability.

---

# 83. Touch

Touch point:

```text
TouchId
position
pressure
contact_size
phase
timestamp
```

Phases:

```text
Down
Move
Up
Cancel
```

---

# 84. Game Controller

Generic controller:

```text
button
axis
trigger
hat
rumble
```

Rumble/output requires explicit device write capability.

---

# 85. Sensor Model

Generic:

```text
SensorDevice
SensorSample
SensorStream
```

Examples:

```text
accelerometer
gyroscope
magnetometer
barometer
proximity
light
temperature
GPS/GNSS
```

---

# 86. Sensor Timestamping

Every sample should contain:

```text
device_timestamp
host_timestamp?
sequence
```

Device time and host time must not be conflated.

---

# 87. Sensor Sampling

Applications can request:

```text
frequency
batch_size
latency
accuracy
power_mode
```

Actual values are reported by the backend.

---

# 88. Sensor Privacy

Location, microphone, camera and biometric-related sensors require explicit capabilities and platform permission.

---

# 89. Serial Devices

```text
SerialDevice
SerialConfig
```

supports:

```text
baud_rate
data_bits
stop_bits
parity
flow_control
```

---

# 90. USB

USB abstraction:

```text
UsbDevice
UsbInterface
UsbEndpoint
UsbTransfer
```

Raw USB access is privileged.

---

# 91. USB Transfer Types

```text
Control
Bulk
Interrupt
Isochronous
```

where supported.

---

# 92. USB Hot Plug

USB watcher:

```text
UsbAdded
UsbRemoved
UsbReset
UsbPermissionChanged
```

---

# 93. Bluetooth

Generic:

```text
BluetoothAdapter
BluetoothDevice
BluetoothService
BluetoothConnection
```

Higher-level profiles can be separate modules.

---

# 94. Bluetooth Security

Pairing/authentication is delegated to the OS/provider.

Raw key handling belongs to BOOTSTRAP-610 where cryptographic material is exposed.

---

# 95. Network Interface Devices

614 exposes hardware/network interface metadata:

```text
NetworkInterface
InterfaceAddress
LinkState
LinkSpeed
HardwareAddress
```

Actual socket networking remains BOOTSTRAP-609.

---

# 96. Storage Devices

614 exposes device-level information:

```text
StorageDevice
Volume
BlockDevice
```

while filesystem operations remain BOOTSTRAP-611.

---

# 97. Block Device Boundary

Privileged environments may expose:

```text
read_blocks
write_blocks
flush
discard
```

Raw block access requires elevated capability.

---

# 98. PCI/PCIe

Privileged/device-driver environments may enumerate:

```text
PciDevice {
    vendor_id
    device_id
    class
    bus
    slot
    function
}
```

---

# 99. PCI Memory Mapping

BAR regions are not exposed as ordinary pointers.

A privileged backend may provide:

```text
MappedDeviceRegion
```

with explicit bounds and access rights.

---

# 100. Interrupts

Hardware interrupt handling is a driver/kernel responsibility.

User-space applications receive:

```text
event
completion
notification
```

rather than arbitrary interrupt vectors.

---

# 101. Driver Boundary

614 does not require Axiom applications to implement kernel-mode drivers.

Driver development can use a separate privileged Axiom profile in future work.

---

# 102. Driver ABI

Future driver ABI should use:

```text
fixed-width ABI types
opaque handles
versioned interfaces
capabilities
explicit ownership
```

rather than compiler-private layouts.

---

# 103. Platform Device Backends

### Windows

Potential sources:

```text
SetupAPI
CM APIs
WMI where appropriate
DirectX
WASAPI
Media Foundation
WinUSB
HID
IOCP
```

### Linux

Potential sources:

```text
sysfs
udev
evdev
ALSA
V4L2
DRM
Vulkan
CUDA/ROCm
io_uring
```

### macOS

Potential sources:

```text
IOKit
CoreAudio
AVFoundation
Metal
CoreBluetooth
```

### Android

Potential sources:

```text
Camera2
AAudio
AudioTrack
USB Host
Bluetooth
Sensor APIs
Vulkan
NNAPI
```

### iOS

Potential sources:

```text
AVFoundation
CoreAudio
Metal
CoreMotion
CoreML
ExternalAccessory where permitted
```

### WASM

Host APIs provide device access.

### Embedded

Board-specific providers implement the same semantic interfaces.

---

# 104. Platform Extensions

Applications can explicitly request backend-specific functionality:

```text
device.native<Windows>()
device.native<Linux>()
device.native<Metal>()
```

Such code is clearly marked platform-dependent.

---

# 105. Native Handle Wrapping

Platform handles remain opaque:

```text
NativeHandle<T>
```

Examples:

```text
HANDLE
file descriptor
Mach port
CoreFoundation object
JNI reference
WASM host handle
```

---

# 106. Native Handle Ownership

Every wrapped handle declares:

```text
Owned
Borrowed
Shared
Transferred
```

The wrapper must not accidentally double-close a borrowed handle.

---

# 107. FFI Handle Transfer

Handle transfer through FFI must specify:

```text
ownership
close responsibility
thread affinity
validity lifetime
```

---

# 108. Device Thread Affinity

Some platform devices are thread-affine.

A device can declare:

```text
ThreadAffine
TaskAffine
AnyThread
```

Scheduler integration enforces the declared constraint.

---

# 109. Device Task Affinity

For devices that require a particular event loop:

```text
DeviceTaskAffinity
```

binds operations to the appropriate executor.

---

# 110. Blocking Device APIs

If an OS API blocks:

```text
blocking_pool
```

from BOOTSTRAP-607 must be used.

Blocking device calls must never silently occupy async workers.

---

# 111. Device Timeouts

Every potentially blocking operation supports:

```text
Deadline
Timeout
CancelToken
```

where the hardware/backend permits cancellation.

---

# 112. Device Reset

Reset capability:

```text
device.reset()
```

must require explicit privilege.

It may invalidate:

```text
buffers
contexts
streams
handles
```

and therefore emits a generation change.

---

# 113. Device Fault Recovery

Possible recovery:

```text
retry
reconnect
reset
reinitialize
disable
```

Recovery policy integrates with BOOTSTRAP-605.

---

# 114. Device Watchdog

Long-running hardware operations may have watchdogs.

Examples:

```text
GPU command timeout
camera stream stall
USB transfer timeout
sensor silence
```

---

# 115. GPU Hang

A GPU reset must not crash the entire application unless platform semantics require it.

Affected GPU resources become invalid.

Application receives:

```text
GpuDeviceLost
```

---

# 116. Device Generation

After reset/reconnect:

```text
DeviceId:
    physical = X
    generation = 8
```

becomes:

```text
generation = 9
```

Old handles cannot access the new generation.

---

# 117. Resource Governor Integration

Every device resource can be charged:

```text
CPU
GPU memory
DMA memory
device queues
camera streams
audio streams
USB transfers
sensor streams
```

to the correct resource group.

---

# 118. Device Quotas

Examples:

```text
max_gpu_memory
max_camera_streams
max_audio_streams
max_usb_devices
max_dma_bytes
max_accelerator_jobs
```

---

# 119. Admission Control

Before opening a resource:

```text
capability check
→ quota check
→ device availability
→ allocation
```

This avoids partially acquired resources.

---

# 120. Resource Reservation

High-priority workloads may reserve:

```text
GPU memory
DMA buffers
audio buffers
device queues
```

through BOOTSTRAP-606.

---

# 121. Scheduling Integration

Device operations become scheduler tasks.

The scheduler handles:

```text
completion
timeout
cancellation
priority
resource group
```

---

# 122. Interrupt-to-Task Translation

Backend:

```text
hardware/OS event
       ↓
native callback/event
       ↓
executor wake
       ↓
Axiom task
```

Callbacks must remain bounded and avoid arbitrary application execution in interrupt context.

---

# 123. Synchronization Integration

Device fences can be represented as synchronization objects compatible with BOOTSTRAP-608.

Examples:

```text
GpuFence
IoEvent
DeviceEvent
```

can participate in wait sets.

---

# 124. Async Wait

A device event can be awaited:

```text
await gpu_fence.wait()
```

without blocking an OS thread.

---

# 125. Multi-Device Synchronization

Example:

```text
Camera frame
    ↓
GPU processing
    ↓
NPU inference
    ↓
Network transmission
```

Each stage can pass buffers and synchronization tokens without unnecessary CPU copies.

---

# 126. Pipeline Model

Axiom supports device pipelines:

```text
Source
 ↓
Buffer
 ↓
GPU
 ↓
Accelerator
 ↓
Encoder
 ↓
Network
```

The runtime tracks resource ownership between stages.

---

# 127. Backpressure

If downstream device capacity is exhausted:

```text
producer
→ pause
→ drop
→ block
→ degrade
```

according to explicit policy.

No unlimited hidden queues.

---

# 128. Frame Dropping

For real-time streams:

```text
DropOldest
DropNewest
DropNonKey
Block
Adaptive
```

may be selected.

---

# 129. Real-Time Mode

Devices can request:

```text
RealTime
LowLatency
BestEffort
Throughput
PowerSave
```

The scheduler/resource governor applies corresponding policies.

---

# 130. Real-Time Guarantees

Axiom must not claim hard real-time guarantees on general-purpose operating systems unless the platform/backend explicitly provides them.

---

# 131. Power Management

Devices may expose:

```text
Active
Idle
Sleep
Off
```

Power transitions may be OS-controlled.

---

# 132. Power Hints

Application hints:

```text
keep_awake()
allow_sleep()
prefer_low_power()
prefer_performance()
```

are advisory unless platform guarantees exist.

---

# 133. Battery Integration

Mobile systems may expose:

```text
BatteryLevel
ChargingState
PowerSaver
ThermalLevel
```

Applications can adapt workload.

---

# 134. Thermal Throttling

Thermal state can be integrated into resource governor pressure:

```text
Normal
Warm
Hot
Critical
```

The application can receive notifications.

---

# 135. Device Notifications

Unified event:

```text
DeviceEvent {
    device_id
    generation
    kind
    timestamp
}
```

---

# 136. Device Property API

Properties are typed:

```text
Property<T>
```

Examples:

```text
resolution: Resolution
sample_rate: u32
temperature: Temperature
memory: Bytes
```

Avoid string-only device metadata.

---

# 137. Device Configuration

Configuration should use typed structures:

```text
CameraConfig
AudioConfig
GpuConfig
SensorConfig
SerialConfig
```

Unknown fields are rejected unless explicitly extensible.

---

# 138. Configuration Atomicity

Device reconfiguration:

```text
validate
→ reserve
→ apply
→ commit
```

If application fails:

```text
restore previous configuration
```

where hardware permits.

---

# 139. Streaming Configuration

Changing a stream's format while active may require:

```text
stop
→ reconfigure
→ restart
```

The API must not hide such transitions.

---

# 140. Device Errors

Common errors:

```text
DeviceNotFound
DeviceBusy
DeviceRemoved
DevicePermissionDenied
UnsupportedFeature
InvalidConfiguration
ResourceExhausted
DeviceLost
TransferFailed
Timeout
Cancelled
DriverError
HardwareFault
```

---

# 141. Error Preservation

Backend-specific error codes may be attached:

```text
DeviceError {
    common_code
    provider
    native_code
}
```

Applications can inspect native details when necessary.

---

# 142. Device Logging

Diagnostics include:

```text
device_id
generation
operation
duration
result
provider
```

No sensitive serial identifiers unless explicitly permitted.

---

# 143. Device Metrics

Metrics:

```text
operations
bytes
latency
errors
timeouts
queue_depth
memory
power
temperature
```

---

# 144. Tracing

A device operation can create a span:

```text
Device.Open
Device.Read
Device.Write
Gpu.Submit
Gpu.Wait
Camera.Capture
Audio.Write
```

---

# 145. Security Logging

Security-sensitive events:

```text
DeviceAccessDenied
RawUsbDenied
CameraPermissionDenied
MicrophonePermissionDenied
GpuExecutionDenied
DmaMappingDenied
DeviceResetDenied
```

---

# 146. Package Integration

Device shaders, firmware blobs, model binaries and configuration may be packaged using BOOTSTRAP-613.

Package metadata can declare:

```text
required_device_feature
minimum_driver
firmware_version
```

---

# 147. Firmware Boundary

Firmware updates are not ordinary resource loading.

They require:

```text
firmware_update capability
signed firmware
device-specific validation
rollback support where available
```

---

# 148. Firmware Verification

Firmware packages must be verified through BOOTSTRAP-610.

Unsigned firmware must not be flashed merely because it exists in an AXPK package.

---

# 149. Driver Version Requirements

Package metadata may specify:

```text
driver.vendor
driver.minimum_version
driver.maximum_version?
```

The runtime reports incompatibility before resource activation.

---

# 150. GPU Feature Requirements

A package may declare:

```text
requires:
    gpu.compute
    shader_model >= X
    vram >= Y
```

Deployment checks these requirements before activation.

---

# 151. Accelerator Feature Requirements

Similarly:

```text
requires:
    npu
    tensor_dtype = fp16
    accelerator_memory >= 4GB
```

---

# 152. Resource Selection by Device

613/614 together allow:

```text
model.fp32
model.fp16
model.int8
```

selection based on actual device capabilities.

---

# 153. Device-Aware Resource Resolver

Resolver inputs:

```text
target OS
architecture
CPU features
GPU features
accelerator features
memory budget
power profile
```

Output:

```text
selected resource variant
```

---

# 154. Device Fingerprint

A non-sensitive device capability fingerprint may include:

```text
architecture
feature set
memory class
driver/API version
```

It should not necessarily include unique hardware identifiers.

---

# 155. Cache Key

Device-specific compiled artifacts use:

```text
resource_hash
+
device_capability_fingerprint
+
driver_version
+
compiler/backend_version
```

---

# 156. Device Context Cache

Disposable cache:

```text
GPU pipeline
NPU compiled graph
shader binary
device-specific kernel
```

can be stored using BOOTSTRAP-613.

---

# 157. Cache Invalidation

Invalidate on:

```text
driver update
firmware update
device generation change
backend version change
resource hash change
```

---

# 158. Device Memory Pressure

When device memory is pressured:

```text
release cache
evict disposable resources
reduce prefetch
spill where explicitly supported
```

Never silently spill resources whose semantics require device-local memory.

---

# 159. Unified Memory

If platform supports unified memory:

```text
UnifiedBuffer<T>
```

may avoid explicit transfer.

The API must still expose synchronization semantics.

---

# 160. Explicit Transfer

For predictable performance:

```text
buffer.upload()
buffer.download()
buffer.copy_to(device_buffer)
```

remain available.

---

# 161. Device Copy Engine

If hardware provides a transfer queue:

```text
TransferQueue
```

can execute copies asynchronously.

---

# 162. Peer-to-Peer Device Transfer

If supported:

```text
GPU0 → GPU1
GPU → NPU
camera → GPU
```

may use direct transfer.

Capability must explicitly report support.

---

# 163. Peer Transfer Fallback

If direct transfer is unavailable:

```text
device A
→ host staging
→ device B
```

may be used.

The runtime must not promise equivalent performance.

---

# 164. Staging Buffers

Staging buffers are pooled and budgeted through 606.

Pools must be bounded.

---

# 165. Device Resource Pools

Reusable pools:

```text
DmaPool
GpuBufferPool
AudioBufferPool
FramePool
DescriptorPool
```

can reduce allocation overhead.

---

# 166. Pool Lifetime

Pools are scoped:

```text
application
service
device context
task
```

and are released deterministically.

---

# 167. No Hidden Infinite Pool

All pools have:

```text
maximum capacity
current usage
eviction/reuse policy
```

---

# 168. Memory Fragmentation

614 should prefer:

```text
suballocation
slabs
page allocation
pooling
```

for device resources where appropriate.

---

# 169. CPU Memory for DMA

Pinned memory is expensive.

It must be separately accounted for and limited.

---

# 170. Pinned Memory API

```text
PinnedBuffer<T>
```

requires explicit allocation.

Normal application memory must not automatically become permanently pinned.

---

# 171. Device Mapping

Mapping a device buffer into CPU space:

```text
map()
```

returns a scoped mapping.

The mapping lifetime ends explicitly.

---

# 172. Mapping Rules

A buffer may not be simultaneously:

```text
CPU mutable
+
GPU exclusive write
```

unless synchronization semantics explicitly permit concurrent access.

---

# 173. Data Race Model

Device/CPU concurrent access is considered a data race unless synchronization establishes ordering.

This extends BOOTSTRAP-608's memory model to device memory.

---

# 174. Device Memory Ordering

Device APIs define:

```text
HostWrite
DeviceRead
DeviceWrite
HostRead
```

transitions.

Barriers establish visibility.

---

# 175. GPU Barrier

Conceptually:

```text
barrier(
    resource,
    from_state,
    to_state
)
```

Examples:

```text
CopyDst → ShaderRead
ShaderWrite → CopySrc
```

---

# 176. Accelerator Barrier

Accelerators may expose simpler:

```text
wait(event)
signal(event)
```

semantics.

Backend maps them to native primitives.

---

# 177. Device Event Loop

Device backends can integrate:

```text
IOCP
epoll
kqueue
dispatch
Android Looper
iOS run loop
WASM callbacks
```

with BOOTSTRAP-607.

---

# 178. Event Loop Ownership

An event loop may be:

```text
ApplicationOwned
RuntimeOwned
PlatformOwned
```

The API must state who drives it.

---

# 179. Callback Safety

Callbacks must not unexpectedly execute on arbitrary threads.

Documentation identifies:

```text
executor
thread
task
```

context.

---

# 180. Callback to Async Conversion

Backend callback:

```text
native event
→ promise completion
→ Axiom await
```

is the preferred application-facing model.

---

# 181. Device Polling

Polling is permitted for devices without event notification.

The runtime should use adaptive polling:

```text
active
→ backoff
→ sleep
```

under low activity.

---

# 182. Busy Polling

Busy polling is an explicit low-latency mode requiring:

```text
cpu_affinity
priority
resource budget
```

and should never be silently enabled.

---

# 183. Interrupt Coalescing

Where supported, applications may request latency/throughput tradeoffs.

---

# 184. Device Batching

Batch APIs reduce overhead:

```text
submit_many()
read_many()
write_many()
```

Useful for:

- sensor samples;
- network packets;
- GPU commands;
- accelerator jobs.

---

# 185. Vectorized Device Access

The compiler can optimize batches without changing semantic ordering.

---

# 186. Device Queue Depth

Every asynchronous device queue has a bounded or policy-controlled depth.

Overflow returns:

```text
QueueFull
```

rather than unlimited allocation.

---

# 187. Device Backpressure

Backpressure integrates with channels from 608.

A producer can await capacity:

```text
await queue.ready()
```

---

# 188. Device Cancellation

Cancellation of hardware operations is backend-dependent.

If physical cancellation is impossible:

```text
cancel_requested
```

is recorded and the completion is discarded safely.

---

# 189. Completion Semantics

An operation has exactly one terminal state:

```text
Success
Failed
Cancelled
TimedOut
DeviceLost
```

---

# 190. Duplicate Completion

Backend events must not complete the same operation twice.

Generation-safe operation IDs are used.

---

# 191. Operation Identity

```text
IoOperationId {
    device_generation
    sequence
}
```

prevents stale completion events.

---

# 192. Device Restart

After device restart:

```text
old generation
→ invalid
new generation
→ new handles
```

The runtime must not silently resurrect old handles.

---

# 193. Supervisor Integration

A service can declare:

```text
requires device camera
requires device gpu
```

Supervisor waits for readiness where appropriate.

---

# 194. Device Dependency

Service dependency states may include:

```text
DeviceUnavailable
DeviceReady
DeviceDegraded
```

This integrates with BOOTSTRAP-605.

---

# 195. Device Recovery

Example:

```text
GPU lost
→ service degraded
→ reinitialize GPU
→ recreate resources
→ service ready
```

Application state remains separate.

---

# 196. Checkpoint Boundary

Hardware contexts generally cannot be checkpointed.

Checkpoint stores:

```text
configuration
resource descriptors
logical state
```

not:

```text
GPU execution state
DMA transaction state
device register state
```

---

# 197. Recovery Reconstruction

After restore:

```text
logical resource state
→ reopen device
→ recreate device resources
→ replay initialization
```

---

# 198. Device State Serialization

Serializable descriptors use BOOTSTRAP-612.

Opaque native handles are never serialized as persistent application state.

---

# 199. Security Boundary for Native APIs

Raw native access requires:

```text
unsafe
+
capability
+
platform permission
```

where appropriate.

`unsafe` alone does not grant authority.

---

# 200. Unsafe Device Operations

Examples:

```text
raw PCI access
DMA configuration
firmware flashing
device reset
MMIO mapping
raw USB
```

require explicit privileged APIs.

---

# 201. No Ambient Hardware Authority

An Axiom process does not automatically gain:

```text
camera
microphone
GPU
USB
serial
PCI
```

access merely because the OS user account can technically access them.

---

# 202. Sandboxed Applications

Sandboxed environments receive only the device handles explicitly granted by the host.

---

# 203. Browser/WASM Security

WASM device access is host-mediated.

Axiom cannot bypass browser permission models.

---

# 204. Mobile Security

Camera, microphone, location and Bluetooth access follows platform permission and user-consent mechanisms.

---

# 205. Desktop Security

Device capabilities may map to:

```text
OS ACL
sandbox
broker
device interface permission
```

depending on platform.

---

# 206. Embedded Security

Embedded targets may use static capability provisioning:

```text
device:
    camera
    i2c
    spi
    uart
```

at firmware build time.

---

# 207. Embedded Bus Abstraction

Generic buses:

```text
I2C
SPI
UART
CAN
GPIO
PWM
ADC
DAC
```

can be exposed by embedded providers.

---

# 208. GPIO

```text
GpioPin {
    direction
    pull
    drive
}
```

operations:

```text
read()
write()
configure()
```

---

# 209. GPIO Safety

Pins must not be configured in conflicting modes simultaneously.

The backend tracks ownership.

---

# 210. I2C

```text
I2cBus
I2cAddress
I2cTransaction
```

supports:

```text
write
read
write_read
```

with transaction deadlines.

---

# 211. SPI

```text
SpiBus
SpiDevice
SpiTransfer
```

supports:

```text
clock
mode
bits_per_word
chip_select
```

---

# 212. UART

UART supports:

```text
stream read/write
configuration
line events
break
flush
```

through async APIs.

---

# 213. CAN

Optional embedded interface:

```text
CanFrame
CanBus
```

with bounded receive/transmit queues.

---

# 214. ADC/DAC

Typed sample APIs:

```text
AdcChannel
DacChannel
Sample
```

with calibration metadata.

---

# 215. PWM

```text
PwmChannel
```

supports:

```text
frequency
duty_cycle
enable
disable
```

---

# 216. Embedded Clock Sources

Clock abstraction:

```text
ClockSource
Timer
Counter
```

supports monotonic and device clocks.

---

# 217. Clock Model

Distinguish:

```text
MonotonicClock
WallClock
DeviceClock
AudioClock
GpuTimestamp
```

Never treat them as interchangeable.

---

# 218. Clock Conversion

A clock can expose:

```text
to_host_time()
```

when calibration is available.

---

# 219. Timestamp Precision

Use fixed-width integer ticks with declared frequency.

Avoid floating-point timestamps for core timing.

---

# 220. Timer Integration

Hardware timers integrate with BOOTSTRAP-607.

Timers should wake tasks rather than require dedicated threads.

---

# 221. High-Resolution Timing

Applications can request high-resolution timers, subject to OS/power policy.

---

# 222. Timer Coalescing

Power-efficient profiles may coalesce timers.

Low-latency profiles can request stricter timing.

---

# 223. Device Resource Discovery

A machine-readable inventory:

```text
axiom device list
axiom device info <id>
axiom device capabilities <id>
```

---

# 224. Device Graph

Hardware topology may be represented:

```text
PCI
 └── GPU
      ├── VRAM
      └── Display

USB
 └── Camera
```

This helps scheduling and diagnostics.

---

# 225. Device Graph Identity

Graph nodes use stable logical identities where available, but unique hardware serials are not required.

---

# 226. Device Grouping

Applications can group devices:

```text
GPU + Display
Camera + Microphone
NPU + Memory
```

for pipeline scheduling.

---

# 227. Multi-GPU

Axiom supports multiple GPU devices.

Each has independent:

```text
context
memory
queues
generation
```

---

# 228. Multi-Accelerator

Multiple NPU/accelerators can be selected based on:

```text
capabilities
memory
latency
power
availability
```

The runtime does not silently migrate work unless policy permits.

---

# 229. Device Selection Policy

Selection can use:

```text
Exact
Preferred
AnyCapable
LowestLatency
HighestThroughput
LowestPower
```

These are policies, not hard-coded assumptions.

---

# 230. Device Affinity

Tasks may be associated with:

```text
GPU
NUMA node
CPU set
accelerator
device queue
```

to improve locality.

---

# 231. Device Migration

Migration between devices requires explicit compatibility checks.

For GPU resources:

```text
export
transfer
import
```

may be required.

---

# 232. External Memory

Platform-specific external memory handles:

```text
DMABUF
D3D shared handle
Metal IOSurface
AHardwareBuffer
```

can be wrapped by `ExternalBuffer`.

---

# 233. External Buffer Security

External buffers require explicit import capability and ownership rules.

---

# 234. Cross-Process GPU Sharing

GPU buffers may be shared through secure OS handles.

This integrates with BOOTSTRAP-604 IPC handle transfer.

---

# 235. Cross-Process Device Access

A device broker can expose restricted capabilities:

```text
Application
   ↓
IPC
   ↓
Device Broker
   ↓
Hardware
```

Useful when OS sandboxing prohibits direct access.

---

# 236. Device Broker

Broker policy:

```text
client identity
device
operation
quota
rate limit
```

is enforced by BOOTSTRAP-603/606.

---

# 237. Device Rate Limits

Examples:

```text
camera frames/sec
USB requests/sec
sensor samples/sec
GPU submissions/sec
```

can be limited.

---

# 238. Device Abuse Prevention

A process must not be able to consume unlimited:

```text
GPU
DMA
camera
microphone
USB
sensor
```

resources.

---

# 239. Privacy Indicators

Where platform supports privacy indicators, Axiom must use the OS mechanisms.

It must not attempt to suppress them.

---

# 240. Camera/Microphone Lifetime

Permission may be revoked while a stream is active.

The stream transitions to:

```text
PermissionRevoked
```

and releases hardware resources.

---

# 241. Device Permission Change

Watcher events:

```text
PermissionGranted
PermissionRevoked
```

allow services to recover gracefully.

---

# 242. Device Privacy Metadata

Diagnostics should avoid logging:

```text
raw camera frames
audio samples
location traces
sensor payloads
```

unless application explicitly opts in.

---

# 243. Device Data Classification

Data may be classified:

```text
Public
Internal
Sensitive
Restricted
```

to integrate with security/diagnostics policies.

---

# 244. Secure Device Buffers

Sensitive capture buffers can be marked:

```text
NoDump
NoLog
ZeroOnRelease
```

where supported.

---

# 245. Crash Diagnostics Integration

BOOTSTRAP-602 must avoid automatically including:

```text
camera frame
microphone buffer
GPU model data
sensor history
```

in crash artifacts.

---

# 246. Device Resource Cleanup

On process termination:

```text
device handles
DMA mappings
GPU contexts
camera streams
audio streams
USB transfers
```

must be released or the OS must reclaim them.

---

# 247. Emergency Cleanup

If graceful cleanup fails, OS/process termination provides final reclamation.

Axiom must not require a GC to guarantee OS resource reclamation.

---

# 248. Leak Detection

Debug mode can track:

```text
device handle
allocation
mapping
stream
queue
```

and report unreleased resources.

---

# 249. Device Resource Debugging

Example:

```text
axiom device leaks
```

outputs:

```text
GpuBuffer #41
created at source.ax:182
owner task 92
size 256MB
```

---

# 250. Compiler Annotations

Useful annotations:

```text
@device
@device_affine
@realtime
@dma
@gpu
@npu
@requires_device
@no_block
```

---

# 251. `@no_block`

Compiler/static analysis should warn when code marked `@no_block` invokes potentially blocking device operations.

---

# 252. `@realtime`

Real-time callbacks may be restricted from:

```text
allocation
blocking
filesystem
network
unbounded locks
```

---

# 253. Device-Aware Static Analysis

Compiler can identify:

```text
device resource escapes
missing synchronization
wrong thread affinity
invalid buffer ownership
```

where sufficient metadata exists.

---

# 254. Device IR

Introduce IR concepts:

```text
device_open
device_close
device_submit
device_wait
device_map
device_unmap
buffer_transfer
device_fence
device_event
```

---

# 255. GPU IR

GPU-specific lowerings:

```text
gpu_alloc
gpu_copy
gpu_dispatch
gpu_barrier
gpu_submit
gpu_wait
```

---

# 256. Accelerator IR

```text
accelerator_compile
accelerator_execute
accelerator_copy
accelerator_wait
```

---

# 257. DMA IR

```text
dma_alloc
dma_map
dma_unmap
dma_sync
```

These remain privileged operations.

---

# 258. Optimization

Compiler may optimize:

```text
CPU → GPU copy
```

into:

```text
shared buffer
```

when aliasing and lifetime rules prove it safe.

---

# 259. Device Operation Fusion

Backends may fuse compatible operations:

```text
copy
→ transform
→ compute
```

but only when observable semantics remain identical.

---

# 260. Device Graph Compilation

A pipeline:

```text
camera → GPU → NPU → network
```

may be represented as a graph and optimized.

Graph optimization belongs to a higher layer, but 614 provides the resource/synchronization foundation.

---

# 261. Device Error Recovery Policy

Default:

```text
transient error → retry
device removal → reconnect
device reset → recreate
permanent failure → fail operation
```

Never retry indefinitely.

---

# 262. Retry Budget

Retry policies integrate with BOOTSTRAP-605/606:

```text
max_attempts
time_window
backoff
resource_budget
```

---

# 263. Device Circuit Breaker

Repeated hardware failures can open a circuit:

```text
Closed
→ Failing
→ Open
→ Probe
→ Closed
```

This prevents infinite retry storms.

---

# 264. Device Health

Device health:

```text
Healthy
Degraded
Unresponsive
Faulted
Removed
```

is exposed to supervision.

---

# 265. Device Health Probes

Examples:

```text
GPU heartbeat
camera stream test
audio device availability
sensor sample freshness
```

---

# 266. Device Diagnostics

`axiom device diagnose` can report:

```text
device
driver
firmware
capabilities
permissions
resource usage
health
errors
```

without exposing sensitive data by default.

---

# 267. Hardware Benchmarking

Axiom tooling may benchmark:

```text
memory bandwidth
GPU throughput
device latency
DMA throughput
storage I/O
```

Benchmark results are descriptive measurements, not compiler guarantees.

---

# 268. Benchmark Reproducibility

Benchmark records:

```text
CPU
GPU
driver
OS
power state
temperature
compiler version
```

where available.

---

# 269. Device Capability Snapshot

A deployment can store:

```text
DeviceCapabilitySnapshot
```

for reproducibility.

The snapshot describes requirements, not authority.

---

# 270. Device Compatibility Check

Before launch:

```text
package requirements
+
actual device capabilities
```

produce:

```text
Compatible
PartiallyCompatible
Incompatible
```

---

# 271. Graceful Degradation

Applications can provide fallback resources:

```text
GPU model
→ CPU model

HDR texture
→ SDR texture

high-resolution camera
→ lower resolution
```

The resolver selects only explicitly declared compatible variants.

---

# 272. No Hidden Performance Claims

Axiom does not guarantee that a device backend has equal performance across OSes.

The API exposes capabilities and actual backend behavior.

---

# 273. Minimal Hardware Profile

Small targets can compile only:

```text
GPIO
UART
SPI
I2C
Timer
```

without GPU, desktop devices or multimedia systems.

---

# 274. Desktop Profile

Desktop can include:

```text
CPU
GPU
Display
Audio
HID
Camera
Storage
Network
USB
Bluetooth
```

as selected.

---

# 275. Server Profile

Server typically enables:

```text
CPU
NUMA
GPU
Accelerator
Network
Storage
PCI
```

while excluding GUI/input components.

---

# 276. Mobile Profile

Mobile includes:

```text
GPU
Camera
Audio
Sensors
Bluetooth
Storage
Network
NPU
```

subject to platform policy.

---

# 277. WASM Profile

WASM exposes only host-granted devices.

No assumption of physical hardware exists.

---

# 278. Testing Architecture

Required test layers:

```text
Unit
Integration
Backend
Conformance
Stress
Fuzz
Race
Fault Injection
Power/Resume
Hot Plug
```

---

# 279. Fake Device Backend

Tests use:

```text
FakeDevice
FakeGpu
FakeCamera
FakeAudio
FakeSensor
FakeUsb
FakeAccelerator
```

with deterministic behavior.

---

# 280. Deterministic Device Clock

Tests use a controllable clock:

```text
FakeClock.advance()
```

to test:

```text
timeouts
watchdogs
sensor timestamps
audio synchronization
```

without real-time delays.

---

# 281. Fake Device Removal

Tests can trigger:

```text
device.remove()
```

during any operation.

The runtime must produce the correct generation/error behavior.

---

# 282. DMA Fault Testing

Simulate:

```text
mapping failure
device access violation
partial transfer
device reset
```

without requiring actual hardware faults.

---

# 283. GPU Conformance

GPU abstraction must be tested against at least one backend where available.

Backend-specific tests remain separate from core semantic tests.

---

# 284. Cross-Backend Conformance

Common operations must produce equivalent logical results:

```text
buffer copy
fence completion
resource lifetime
device loss
error semantics
```

where the underlying APIs provide equivalent capabilities.

---

# 285. Device ABI Tests

Validate:

```text
handle size
alignment
calling convention
struct layout
ownership
versioning
```

for all stable FFI interfaces.

---

# 286. Security Tests

Required:

```text
unauthorized device open
capability attenuation
DMA denial
raw USB denial
camera denial
microphone denial
firmware denial
device reset denial
sandbox escape attempts
```

---

# 287. Resource Exhaustion Tests

Test:

```text
GPU OOM
DMA quota
too many camera streams
too many USB transfers
queue exhaustion
descriptor exhaustion
device memory exhaustion
```

Expected behavior is bounded failure, not process-wide corruption.

---

# 288. Hot-Plug Tests

Test:

```text
connect
open
use
disconnect
reconnect
```

and:

```text
open
disconnect during I/O
reconnect
```

---

# 289. Suspend/Resume Tests

Devices may transition:

```text
active
→ suspend
→ resume
```

Open handles must either recover or report invalidation according to backend semantics.

---

# 290. Mobile Lifecycle Tests

Test:

```text
foreground
→ background
→ permission revoked
→ foreground
```

without assuming continuous device access.

---

# 291. Thermal Tests

Simulate:

```text
Normal
→ Warm
→ Hot
→ Critical
```

and verify workload adaptation hooks.

---

# 292. Power Tests

Simulate:

```text
battery
charging
power saver
low battery
```

and verify that applications receive notifications rather than unexpected termination from the runtime.

---

# 293. Acceptance Criteria

614 is complete only when:

1. Device abstraction exists.
2. Device generations prevent stale handles.
3. Device enumeration is implemented.
4. Device watching is implemented.
5. Capability checks integrate with 603.
6. Device resource accounting integrates with 606.
7. Async operations integrate with 607.
8. Device synchronization integrates with 608.
9. Storage devices integrate with 611.
10. GPU devices have a generic abstraction.
11. Accelerator devices have a generic abstraction.
12. CPU topology is discoverable.
13. CPU feature dispatch is supported.
14. NUMA topology can be queried where available.
15. DMA buffers have explicit lifetime.
16. DMA mappings are capability-controlled.
17. Zero-copy buffers are supported where hardware permits.
18. Device memory is distinct from host memory.
19. GPU queues are supported.
20. GPU buffers are supported.
21. GPU synchronization is supported.
22. GPU device-loss semantics exist.
23. Accelerator graph execution is supported.
24. Accelerator compilation can use 613 caching.
25. Camera abstraction exists.
26. Camera streaming is asynchronous.
27. Microphone abstraction exists.
28. Audio output abstraction exists.
29. Audio clock is represented separately.
30. HID abstraction exists.
31. Keyboard events are represented.
32. Mouse events are represented.
33. Touch events are represented.
34. Game controller abstraction exists.
35. Sensor abstraction exists.
36. Sensor timestamps are represented.
37. USB abstraction exists.
38. Serial abstraction exists.
39. Bluetooth boundary exists.
40. Network interface enumeration exists.
41. Storage device enumeration exists.
42. PCI enumeration boundary exists.
43. Embedded GPIO abstraction exists.
44. Embedded I2C abstraction exists.
45. Embedded SPI abstraction exists.
46. Embedded UART abstraction exists.
47. Embedded timer abstraction exists.
48. Device hot-plug is supported.
49. Device removal invalidates old handles.
50. Device reset creates a new generation.
51. Device operations support cancellation where possible.
52. Device operations support deadlines.
53. Blocking device APIs use the blocking executor.
54. Device queues are bounded.
55. Device backpressure exists.
56. Device failures have structured errors.
57. Device health integrates with supervision.
58. Device diagnostics integrate with 602.
59. Device requirements can be expressed in package metadata.
60. Device-specific resources can be selected from packages.
61. GPU binaries can be cached through 613.
62. Device firmware packages require verification.
63. Firmware updates have a separate privileged boundary.
64. Native handles have explicit ownership.
65. FFI device handles have stable ABI wrappers.
66. Device thread affinity is represented.
67. Device task affinity is represented.
68. CPU feature dispatch can generate specialized implementations.
69. GPU memory is resource-budgeted.
70. DMA memory is resource-budgeted.
71. Camera/audio stream counts are resource-budgeted.
72. Device permissions can be revoked.
73. Privacy-sensitive data is excluded from diagnostics by default.
74. Package opening never grants device authority.
75. Package shader execution is separately authorized.
76. Cross-process device handles integrate with IPC.
77. Shared device buffers can use IPC handle transfer.
78. Device state can be reconstructed after application recovery.
79. Native hardware handles are not persisted as application state.
80. Device backends can be replaced without changing high-level APIs.
81. Platform-specific extensions are explicit.
82. Windows backend architecture exists.
83. Linux backend architecture exists.
84. macOS backend architecture exists.
85. Android backend architecture exists.
86. iOS backend architecture exists.
87. WASM host backend architecture exists.
88. Embedded backend architecture exists.
89. Deterministic fake devices exist.
90. Device removal fault injection exists.
91. Device-loss fault injection exists.
92. DMA fault injection exists.
93. Resource exhaustion tests exist.
94. Hot-plug tests exist.
95. suspend/resume tests exist.
96. security tests exist.
97. fuzzing exists for device metadata and binary descriptors.
98. race tests exist for device lifetime.
99. no mandatory GC is required.
100. no mandatory third-party runtime is required.
101. minimal profiles can exclude unused device subsystems.
102. device APIs use struct-only Axiom style.
103. compiler IR represents device operations.
104. compiler annotations can express device constraints.
105. real-time APIs prohibit inappropriate blocking where statically detectable.
106. device capability snapshots are serializable.
107. device-specific cache invalidation is correct.
108. multi-device operation is supported.
109. device pipelines can transfer buffers safely.
110. cross-device synchronization is represented.
111. physical addresses are not exposed to ordinary safe code.
112. raw hardware access requires explicit privileged boundaries.
113. device reset cannot silently resurrect stale handles.
114. package/device compatibility can be checked before activation.
115. device resource cleanup does not depend on GC.
116. crash recovery cannot serialize arbitrary native device state.
117. package trust and hardware trust remain separate concepts.
118. device authority never derives merely from package presence.
119. platform user-consent rules are respected.
120. all core device operations have deterministic lifetime semantics.

---

# 294. Final Architecture

```text
                         ┌───────────────────────┐
                         │      Axiom App        │
                         └───────────┬───────────┘
                                     │
                         Device / Hardware API
                                     │
                ┌────────────────────┼────────────────────┐
                │                    │                    │
             CPU/NUMA              GPU/NPU            Devices
                │                    │                    │
         ┌──────┴──────┐       ┌─────┴─────┐       ┌────┴─────┐
         │             │       │           │       │          │
       CPU          Memory    GPU       Accelerator  IO      Sensors
                                     │
                ┌────────────────────┼────────────────────┐
                │                    │                    │
             Buffers              Queues              Events
                │                    │                    │
                └────────────────────┼────────────────────┘
                                     │
                          Scheduler / Executor
                              BOOTSTRAP-607
                                     │
                         Synchronization 608
                                     │
                         Resource Governor 606
                                     │
                          Security 603
                                     │
                 ┌───────────────────┼───────────────────┐
                 │                   │                   │
             Storage 611         Network 609         Crypto 610
                 │
             Package 613
                 │
             State 600
                 │
          Configuration 601
                 │
          Diagnostics 602
                 │
          Supervision 605
                 │
                 ▼
        ┌───────────────────────┐
        │   Platform Backend    │
        ├───────────────────────┤
        │ Windows               │
        │ Linux                 │
        │ macOS                 │
        │ Android               │
        │ iOS                   │
        │ WASM                  │
        │ Embedded              │
        └───────────┬───────────┘
                    │
                    ▼
             OS / Kernel / Driver
                    │
                    ▼
                 Hardware
```

---

# 295. Architectural Invariants

The 614 subsystem is valid only if these invariants hold:

```text
Device handle != physical address

Device identity != permission

Capability != device availability

Package presence != hardware authority

GPU memory != ordinary CPU memory

Device generation != process generation

Device failure != automatic application failure

Native handle != persistent application state

DMA mapping != unrestricted memory access

Unsafe != privileged

Async operation != dedicated thread

Device event != arbitrary callback execution

Hardware reset != handle resurrection
```

The central security/resource chain is:

```text
OS / Hardware
      ↓
Platform Driver
      ↓
Axiom Device Backend
      ↓
Capability 603
      ↓
Resource Admission 606
      ↓
Device Handle
      ↓
Scheduler 607
      ↓
Synchronization 608
      ↓
Application
```

The central data path is:

```text
Device
   ↓
DMA / Shared Buffer
   ↓
Axiom Buffer
   ↓
GPU / NPU / CPU
   ↓
Synchronization
   ↓
Application / Storage / Network
```

---

# 296. Completion

**BOOTSTRAP-614 is complete.**

Axiom now has a native hardware boundary covering:

```text
CPU
NUMA
memory topology
GPU
NPU
AI accelerators
display
camera
microphone
audio
HID
keyboard
mouse
touch
gamepad
sensors
USB
Bluetooth
serial
network interfaces
storage devices
PCI/PCIe
embedded buses
GPIO
I2C
SPI
UART
CAN
PWM
ADC/DAC
timers
```

while maintaining:

```text
capability security
resource quotas
async scheduling
device synchronization
zero-copy buffers
DMA isolation
device generations
hot-plug
device recovery
package integration
GPU/accelerator caching
cross-process device sharing
mobile/WASM/embedded portability
```

The architecture deliberately leaves **device drivers, graphics engines, GUI frameworks, media frameworks and ML frameworks above the low-level 614 boundary**, preventing the Axiom core runtime from becoming unnecessarily large.

**Next architecture task:**

# BOOTSTRAP-615 — Native Graphics, Windowing, Display Composition, 2D/3D Rendering, GPU Resource Graph & Cross-Platform UI Foundation 5.0

This next layer will build directly on 614's GPU/display/input primitives and define the native graphics/UI foundation without forcing Axiom to depend on a particular framework such as Qt, Electron, WPF or a single graphics API.

:::