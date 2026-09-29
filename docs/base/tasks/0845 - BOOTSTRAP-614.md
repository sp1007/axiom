Tiếp tục với **BOOTSTRAP-614 — Native Device, Hardware, Peripheral, Sensor, GPU/Accelerator & OS Resource I/O Runtime 5.0**.

:::writing{variant="document" id="74126" title="BOOTSTRAP-614 — Native Device, Hardware, Peripheral, Sensor, GPU/Accelerator & OS Resource I/O Runtime 5.0"}
# BOOTSTRAP-614
## Native Device, Hardware, Peripheral, Sensor, GPU/Accelerator & OS Resource I/O Runtime 5.0

**Status:** Architecture Specification  
**Layer:** Native Hardware / Device Runtime  
**Depends on:** BOOTSTRAP-600 → 613  
**Primary dependencies:** 603 Security, 606 Resource Governor, 607 Scheduler, 608 Synchronization, 609 Networking, 610 Cryptography, 611 Storage, 612 Serialization, 613 Packaging  
**Target:** Windows / Linux / macOS / Android / iOS / WASM / Embedded

---

# 1. Purpose

BOOTSTRAP-614 defines Axiom's native abstraction for physical and OS-managed devices.

It covers:

- device discovery;
- device identity;
- device capabilities;
- device handles;
- device lifetime;
- hardware resources;
- peripheral access;
- buses;
- USB;
- PCI/PCIe;
- Bluetooth;
- serial devices;
- HID/input;
- display;
- audio;
- cameras;
- sensors;
- GPU;
- accelerators;
- DMA;
- device memory;
- command queues;
- synchronization;
- device events;
- hot-plug;
- power state;
- thermal state;
- device reset;
- device loss;
- embedded peripherals;
- platform-specific device backends.

The design must provide a common Axiom model without pretending that all platforms expose identical hardware capabilities.

---

# 2. Core Principle

The architecture separates:

```text
Physical Device
      ↓
OS Device Object
      ↓
Axiom Device Backend
      ↓
Typed Device Handle
      ↓
Capability
      ↓
Device API
```

Axiom never assumes that possession of a device handle automatically grants unrestricted hardware access.

---

# 3. Non-Goals

This specification does not define:

- a universal GPU shader language;
- a complete graphics API;
- a complete audio DSP framework;
- a complete camera-processing framework;
- a universal driver-development language;
- kernel implementation;
- replacement for OS device managers;
- firmware implementation;
- automatic hardware overclocking;
- unsafe raw MMIO by default.

Those can be built above this layer.

---

# 4. Fundamental Invariants

1. Every device has a stable runtime identity.
2. Device handles are generation-safe.
3. A closed/lost device cannot be used.
4. Device capabilities are explicit.
5. Device operations obey BOOTSTRAP-603.
6. Device resource consumption obeys BOOTSTRAP-606.
7. Blocking device operations do not block async executors unnecessarily.
8. Device buffers have explicit ownership/lifetime.
9. DMA mappings are explicitly represented.
10. GPU device loss is recoverable where the platform permits.
11. Hot-plug does not invalidate unrelated device handles.
12. Device removal produces deterministic events.
13. Raw physical addresses are not exposed to ordinary application code.
14. MMIO requires explicit privileged capability.
15. Driver boundaries remain platform-specific.
16. No mandatory global device lock exists.
17. Device enumeration is deterministic within a snapshot.
18. Device metadata is inspectable without opening the device.
19. Device discovery never executes device-provided code.
20. Unsupported hardware features fail explicitly.

---

# 5. Device Model

Axiom defines:

```text
Device
DeviceId
DeviceClass
DeviceHandle
DeviceInfo
DeviceCapabilities
DeviceState
DeviceEvent
```

Example:

```text
device = Device.find("gpu:0")
```

---

# 6. Device Identity

A device identity contains:

```text
DeviceId {
    domain
    bus
    address
    function
    instance
    generation
}
```

Not every platform exposes every component.

The backend maps native identifiers into the logical model.

---

# 7. Device Identity Stability

`DeviceId` must distinguish:

```text
same physical device
different device instance
same device after replacement
```

Generation prevents stale handles from accidentally referring to a newly attached device.

---

# 8. Device Classes

Standard classes:

```text
Compute
Gpu
Display
Audio
Camera
Input
Storage
Network
Usb
Bluetooth
Serial
Sensor
Power
Thermal
Timer
Dma
Accelerator
Custom
```

A device may implement multiple classes.

---

# 9. Device State

Logical states:

```text
Unknown
Discovered
Available
Opening
Open
Suspended
Resetting
Lost
Removed
Faulted
Closed
```

---

# 10. State Transitions

Normal:

```text
Discovered
    ↓
Available
    ↓
Opening
    ↓
Open
    ↓
Closed
```

Failure:

```text
Open
 ↓
Faulted
 ↓
Resetting
 ↓
Open
```

or:

```text
Open
 ↓
Lost
 ↓
Removed
```

---

# 11. Device Snapshot

Enumeration returns a snapshot:

```text
DeviceSnapshot
```

containing immutable metadata.

A snapshot does not guarantee the device remains present.

---

# 12. Device Enumeration

API:

```text
devices.enumerate()
devices.find()
devices.watch()
```

Example:

```text
for device in Device.enumerate():
    print(device.info())
```

---

# 13. Device Enumeration Filters

Filters:

```text
class
vendor
product
bus
name
capability
architecture
driver
```

Example:

```text
Device.enumerate(
    DeviceFilter {
        class: DeviceClass.Gpu
    }
)
```

---

# 14. Device Information

`DeviceInfo` contains:

```text
id
class
vendor_id
device_id
subsystem_id
revision
name
manufacturer
driver
driver_version
bus
location
serial
firmware
capabilities
```

Sensitive identifiers may be redacted according to policy.

---

# 15. Device Capability Model

Capabilities describe supported operations.

Examples:

```text
GpuCompute
GpuGraphics
Dma
MappedMemory
UsbTransfer
CameraCapture
AudioPlayback
AudioCapture
SensorRead
DisplayOutput
HidInput
```

Capabilities are descriptive.

Authority still comes from BOOTSTRAP-603.

---

# 16. Device Access Capability

Security capabilities may include:

```text
device.enumerate
device.open
device.reset
device.configure
device.raw_io
device.dma
device.mmio
device.usb
device.camera
device.microphone
device.display
device.gpu
```

---

# 17. Device Handle

A device handle contains internally:

```text
device_id
generation
backend_reference
rights
state
```

Applications never depend on native pointer layout.

---

# 18. Generation Safety

If:

```text
Device A generation 7
```

is removed and a new device appears:

```text
Device A generation 8
```

a handle to generation 7 cannot access generation 8.

---

# 19. Handle Rights

Rights:

```text
Observe
Open
Read
Write
Configure
Reset
Map
Dma
Submit
```

Rights can be attenuated.

---

# 20. Device Backend

```text
trait DeviceBackend {
    enumerate()
    open()
    close()
    query()
    event()
}
```

Backends are platform-specific.

---

# 21. Backend Architecture

```text
Device API
    ↓
Device Registry
    ↓
Platform Backend
    ├── Windows
    ├── Linux
    ├── macOS
    ├── Android
    ├── iOS
    ├── WASM
    └── Embedded
```

---

# 22. Windows Backend

Possible sources:

- SetupAPI;
- Configuration Manager;
- device interfaces;
- DirectX;
- WASAPI;
- HID;
- WinUSB;
- WDDM interfaces;
- Media Foundation/Windows camera APIs.

The core abstraction must not require all of them.

---

# 23. Linux Backend

Possible sources:

- sysfs;
- udev where available;
- `/dev`;
- ioctl;
- DRM;
- ALSA;
- V4L2;
- HID;
- USB;
- PCI;
- IIO;
- Vulkan/OpenCL/CUDA-compatible external providers where configured.

---

# 24. macOS Backend

Possible sources:

- IOKit;
- Metal;
- CoreAudio;
- AVFoundation;
- HID;
- Bluetooth frameworks.

---

# 25. Android Backend

Possible sources:

- Android device APIs;
- Camera2;
- AudioTrack/AudioRecord;
- Sensor framework;
- Vulkan;
- USB Host;
- Bluetooth;
- NNAPI where available.

---

# 26. iOS Backend

Possible sources:

- Metal;
- AVFoundation;
- CoreAudio;
- CoreMotion;
- ExternalAccessory where permitted;
- platform input APIs.

---

# 27. WASM Backend

WASM normally has no direct hardware access.

Devices are supplied by the host:

```text
Host Device Provider
        ↓
WASM Device Backend
```

---

# 28. Embedded Backend

Embedded targets may expose devices through:

```text
MMIO
interrupts
DMA
memory-mapped peripherals
```

but these require explicit privileged device profiles.

---

# 29. Bus Model

Axiom represents common buses:

```text
PCI
PCIe
USB
I2C
SPI
UART
CAN
GPIO
Bluetooth
Platform
Virtual
```

---

# 30. PCI/PCIe

Logical PCI information:

```text
domain
bus
slot
function
vendor
device
class
revision
BARs
interrupts
```

Raw BAR access is privileged.

---

# 31. USB

USB device model:

```text
UsbDevice
UsbConfiguration
UsbInterface
UsbEndpoint
UsbTransfer
```

Transfers:

```text
Control
Bulk
Interrupt
Isochronous
```

---

# 32. USB Security

USB access requires explicit capability.

Applications cannot automatically access arbitrary USB devices merely because they are connected.

---

# 33. USB Hot-Plug

Events:

```text
Connected
Configured
Disconnected
Reset
Faulted
```

Hot-plug callbacks are asynchronous.

---

# 34. Bluetooth

Logical abstraction:

```text
BluetoothAdapter
BluetoothDevice
BluetoothService
BluetoothConnection
```

The low-level radio implementation remains platform-specific.

---

# 35. Serial Devices

API:

```text
SerialPort
SerialConfig
SerialStream
```

Configuration:

```text
baud_rate
data_bits
stop_bits
parity
flow_control
```

---

# 36. Serial Async

Serial I/O integrates with BOOTSTRAP-607.

No polling loop is required when the OS provides event-driven I/O.

---

# 37. HID/Input

Axiom provides:

```text
InputDevice
InputEvent
InputSnapshot
```

Events:

```text
Key
Button
Pointer
Touch
Gamepad
Pen
```

---

# 38. Input Event

Example:

```text
InputEvent {
    device
    timestamp
    kind
    code
    value
}
```

Timestamps use a monotonic clock.

---

# 39. Display

Logical display device:

```text
DisplayDevice
DisplayMode
DisplayOutput
DisplaySurface
```

Metadata:

```text
resolution
refresh_rate
pixel_format
color_space
HDR
orientation
```

---

# 40. Display Ownership

The device runtime does not define window-management policy.

Higher-level GUI runtime owns:

```text
window
surface
presentation
```

---

# 41. Display Buffers

A display surface may reference:

```text
system memory
shared GPU memory
GPU-local memory
platform surface
```

Ownership is explicit.

---

# 42. Audio

Logical devices:

```text
AudioOutput
AudioInput
AudioDevice
AudioStream
```

Properties:

```text
sample_rate
channels
format
latency
device_clock
```

---

# 43. Audio Buffering

Audio buffers use bounded ring buffers.

The audio callback must avoid:

- blocking;
- unbounded allocation;
- filesystem access;
- arbitrary locks.

---

# 44. Camera

Logical model:

```text
CameraDevice
CameraMode
CameraFrame
CameraStream
```

Metadata:

```text
resolution
pixel_format
fps
exposure
focus
sensor_mode
```

---

# 45. Camera Security

Camera access requires explicit capability:

```text
camera.capture
```

OS-level permission remains authoritative.

---

# 46. Microphone Security

Microphone access requires:

```text
microphone.capture
```

The runtime must not provide silent access.

---

# 47. Sensor Model

Sensors may include:

```text
Accelerometer
Gyroscope
Magnetometer
Barometer
Temperature
Light
Proximity
GPS/GNSS
Orientation
Custom
```

---

# 48. Sensor Reading

```text
SensorReading {
    sensor
    timestamp
    sequence
    values
    accuracy
}
```

---

# 49. Sensor Streaming

Sensors may expose:

```text
stream()
subscribe()
poll()
```

Streaming is integrated with async scheduling.

---

# 50. Sensor Timestamp

Sensor timestamps must preserve the platform's monotonic ordering where possible.

Wall-clock conversion is separate.

---

# 51. GPU Model

GPU is represented as:

```text
GpuDevice
GpuQueue
GpuBuffer
GpuImage
GpuCommandBuffer
GpuFence
GpuEvent
GpuMemory
```

---

# 52. GPU Abstraction Boundary

614 provides resource/device primitives.

It does not attempt to replace:

- Vulkan;
- Direct3D;
- Metal;
- OpenGL;
- WebGPU.

Those can be implemented as higher-level APIs/providers.

---

# 53. Native GPU Provider

```text
trait GpuProvider {
    enumerate()
    create_device()
    create_queue()
    allocate_memory()
    submit()
}
```

---

# 54. GPU Queues

Logical queue classes:

```text
Graphics
Compute
Copy
Transfer
VideoDecode
VideoEncode
```

Not every GPU supports every queue.

---

# 55. GPU Queue Submission

```text
queue.submit(command_buffer)
```

Submission returns:

```text
GpuSubmission
```

which can be awaited.

---

# 56. GPU Synchronization

Use:

```text
GpuFence
GpuSemaphore
GpuEvent
```

rather than ordinary CPU locks for device-to-device synchronization.

---

# 57. GPU Command Buffer

Command buffers are recorded separately:

```text
begin()
record()
end()
submit()
```

This is a primitive abstraction.

Graphics-specific commands belong above 614.

---

# 58. GPU Memory

Logical classes:

```text
DeviceLocal
HostVisible
HostCoherent
HostCached
Unified
Shared
```

The actual flags depend on the backend.

---

# 59. GPU Buffer

```text
GpuBuffer {
    size
    usage
    memory
}
```

Usage:

```text
Vertex
Index
Uniform
Storage
TransferSource
TransferDestination
Indirect
```

Higher-level graphics APIs can extend usage.

---

# 60. GPU Image

```text
GpuImage {
    width
    height
    depth
    format
    usage
    memory
}
```

---

# 61. GPU Mapping

Mapping a GPU buffer requires explicit capability.

For non-coherent memory:

```text
map
write
flush
unmap
```

or:

```text
map
read
invalidate
unmap
```

---

# 62. DMA

DMA is represented as:

```text
DmaBuffer
DmaMapping
DmaRegion
```

A DMA mapping defines:

```text
device
buffer
direction
length
mapping_state
```

---

# 63. DMA Ownership

Before device submission:

```text
CPU ownership → Device ownership
```

After completion:

```text
Device ownership → CPU ownership
```

The exact synchronization depends on platform coherency.

---

# 64. DMA Security

Arbitrary DMA is privileged.

Applications must not obtain unrestricted physical memory access.

IOMMU-backed isolation should be used where available.

---

# 65. DMA Buffer Lifetime

A DMA buffer cannot be reclaimed while:

```text
device may still access it
```

The runtime must track in-flight submissions.

---

# 66. Physical Addresses

Physical addresses are not ordinary application-level values.

Only privileged driver/device code may access them.

---

# 67. MMIO

Memory-mapped device registers are represented through:

```text
MmioRegion
MmioRegister
```

Access requires:

```text
device.mmio
```

capability.

---

# 68. MMIO Safety

MMIO APIs must enforce:

- alignment;
- access width;
- bounds;
- volatile semantics;
- ordering requirements.

---

# 69. Volatile Device Access

Device registers are not ordinary memory.

The compiler must preserve required volatile semantics.

---

# 70. Interrupts

Logical abstraction:

```text
InterruptSource
InterruptHandler
InterruptToken
```

Interrupt handling should be minimal.

Heavy work must be deferred to a scheduler task.

---

# 71. Interrupt Safety

Interrupt handlers must not perform arbitrary blocking operations.

Compiler/runtime profiles may restrict available operations in interrupt context.

---

# 72. Event Delivery

Device events can flow through:

```text
interrupt
 → backend
 → event queue
 → executor
 → application
```

---

# 73. Device Watch

```text
Device.watch(filter)
```

returns an async stream:

```text
Added
Removed
Changed
Reset
Faulted
```

---

# 74. Hot-Plug Semantics

When a device disappears:

1. emit `Removed`;
2. mark handle generation invalid;
3. cancel affected I/O;
4. release mappings;
5. complete pending operations with `DeviceRemoved`;
6. reclaim backend state after references disappear.

---

# 75. Device Reset

Reset requires explicit capability:

```text
device.reset
```

Reset may invalidate:

- queues;
- mappings;
- pending commands;
- device state.

The backend reports exactly which resources became invalid.

---

# 76. Device Loss

GPU/device loss is not treated as ordinary application failure.

Possible result:

```text
DeviceLost
```

Applications can:

```text
recreate device
reload resources
rebuild pipelines
resume
```

where the backend supports recovery.

---

# 77. Resource Rebuild

Package/resource infrastructure 613 enables deterministic resource reload:

```text
package
 ↓
resource
 ↓
GPU upload
```

This is an important integration between 613 and 614.

---

# 78. GPU Resource Cache

GPU resources may be cached by:

```text
resource_hash
device_id
driver_id
format
```

Cache invalidation occurs when the driver/device identity changes incompatibly.

---

# 79. Shader Cache Boundary

Compiled shader caches are optional.

A cache key should include:

```text
shader_hash
compiler_version
driver_version
device_identity
target_format
```

---

# 80. Accelerator Model

Generic accelerator:

```text
AcceleratorDevice
AcceleratorQueue
AcceleratorBuffer
AcceleratorSubmission
```

Classes:

```text
NPU
DSP
TPU-like
Video
Crypto
AI
FPGA
Custom
```

---

# 81. Accelerator Command Model

Minimal:

```text
submit(command)
wait(submission)
```

Higher-level libraries define actual kernels/operators.

---

# 82. CPU/GPU/Accelerator Separation

Axiom scheduler distinguishes:

```text
CpuExecutor
GpuQueue
AcceleratorQueue
IoReactor
```

A GPU submission does not consume a CPU worker while waiting.

---

# 83. Async Device Operations

Example:

```text
frame = await camera.next_frame()
result = await gpu.submit(command)
await dma.wait()
```

Compiler lowers async control flow through BOOTSTRAP-607.

---

# 84. Device Future

Device operations return typed futures:

```text
Future<Result<T, DeviceError>>
```

No hidden blocking is permitted.

---

# 85. Blocking Device APIs

Synchronous wrappers may exist:

```text
frame = camera.next_frame_blocking()
```

but they must be explicit.

They may consume a blocking executor worker.

---

# 86. Device Timeouts

Operations may specify:

```text
timeout
deadline
cancellation
```

Timeout does not automatically imply device reset unless policy explicitly specifies it.

---

# 87. Device Cancellation

Cancellation semantics must distinguish:

```text
request cancellation
device command cancellation
device reset
```

Some hardware commands cannot be cancelled once submitted.

The API must report this accurately.

---

# 88. Device Queues and Backpressure

Queues have bounded limits.

If full:

```text
WouldBlock
Backpressure
QueueFull
```

is returned or the async operation waits.

---

# 89. Device Resource Governor

BOOTPSTRAP-606 tracks:

```text
GPU memory
GPU queues
GPU submissions
DMA mappings
USB transfers
camera streams
audio streams
device handles
```

---

# 90. Device Quotas

Examples:

```text
max_gpu_memory
max_dma_bytes
max_usb_transfers
max_camera_streams
max_audio_streams
max_open_devices
```

---

# 91. GPU Memory Pressure

At pressure levels:

```text
Normal
Warning
Critical
```

the runtime may:

- reject new allocations;
- trigger cache eviction;
- reduce resource residency;
- notify applications.

It must not silently destroy live application-owned GPU resources.

---

# 92. Device Priority

Device queues can have priorities:

```text
Realtime
High
Normal
Low
```

but security/resource policies may cap them.

A process cannot self-elevate beyond its capability.

---

# 93. Priority Inversion

The runtime should avoid:

```text
high-priority task
waiting indefinitely
on low-priority device submission
```

where platform support exists.

---

# 94. Device Affinity

A task may request:

```text
gpu = gpu0
numa_node = 1
device = camera0
```

Requests are hints unless the API requires a specific device.

---

# 95. Multi-GPU

Applications can enumerate:

```text
gpu0
gpu1
...
```

Each has independent:

- memory;
- queues;
- capabilities;
- generation.

---

# 96. Peer-to-Peer GPU Memory

Optional capability:

```text
GpuPeerMemory
```

If supported:

```text
GPU0 → GPU1
```

may transfer without CPU staging.

---

# 97. Unified Memory

Platforms with unified memory may expose:

```text
Unified
```

but the API must not assume unified memory semantics on discrete GPUs.

---

# 98. CPU/GPU Shared Buffers

A shared buffer tracks:

```text
cpu_access
device_access
coherency
ownership
```

Synchronization remains explicit.

---

# 99. Memory Ordering

CPU/device synchronization is separate from ordinary CPU atomic memory ordering.

GPU memory barriers are represented by the device backend/API.

---

# 100. Device Fences

A fence can represent:

```text
submission completed
DMA completed
transfer completed
```

It integrates with BOOTSTRAP-607 await.

---

# 101. Device Events

Events include:

```text
TransferCompleted
FrameReady
DeviceRemoved
DeviceReset
DeviceLost
QueueCompleted
MemoryPressure
ThermalWarning
PowerChanged
```

---

# 102. Thermal Model

Devices may report:

```text
temperature
thermal_state
power_state
throttling
```

The runtime exposes measurements but does not force unsafe thermal behavior.

---

# 103. Power State

Logical states:

```text
Active
Idle
Suspended
LowPower
Unavailable
```

The OS remains authoritative.

---

# 104. Power Management

Applications may request:

```text
keep_awake
performance_hint
low_power_hint
```

but requests are advisory unless the platform grants stronger control.

---

# 105. Battery

Power devices may expose:

```text
Battery
Charger
PowerSource
```

with:

```text
charge_percent
voltage
current
temperature
state
```

---

# 106. Device Permissions

Examples:

```text
camera
microphone
bluetooth
usb
location
motion_sensor
gpu
raw_device
```

OS permissions are mapped into Axiom capability state.

---

# 107. Permission Denied

A permission failure must be distinguishable from:

```text
device absent
device busy
device unsupported
device fault
```

---

# 108. Device Busy

If another process owns an exclusive device:

```text
DeviceBusy
```

is returned.

The runtime must not attempt unauthorized stealing.

---

# 109. Shared Device Access

Devices may support:

```text
Shared
Exclusive
Session
Stream
```

access modes.

---

# 110. Exclusive Access

Exclusive ownership is required for operations such as:

- some USB configurations;
- device reset;
- raw MMIO;
- exclusive camera modes;
- low-level driver configuration.

---

# 111. Device Session

A device session groups:

```text
handle
queues
buffers
events
configuration
```

Closing the session releases owned resources.

---

# 112. Session Failure

If the process crashes:

```text
OS/backend cleanup
```

must release session resources where supported.

---

# 113. Device Driver Boundary

Axiom distinguishes:

```text
Application API
Device Provider
Kernel Driver
Firmware
Hardware
```

The application layer does not directly depend on driver implementation details.

---

# 114. Driver ABI

Provider ABI must define:

```text
enumeration
open
close
query
submit
map
unmap
event
reset
```

with versioning.

---

# 115. External Driver Libraries

External vendor drivers are allowed.

They are not considered part of Axiom's compiler/runtime dependency.

Axiom defines the integration boundary.

---

# 116. Native Driver-Free Profiles

Where OS APIs already provide device access, Axiom can use platform APIs directly without shipping a custom driver.

---

# 117. Custom Driver Profile

Embedded/system software may implement:

```text
Axiom Device Backend
```

directly over MMIO/interrupt/DMA.

This requires privileged execution.

---

# 118. Kernel Boundary

Axiom user applications should not directly access:

```text
kernel memory
physical RAM
arbitrary MMIO
interrupt controllers
IOMMU configuration
```

unless explicitly running in a privileged system profile.

---

# 119. Driver Development Profile

A future privileged Axiom profile may expose:

```text
Mmio
Interrupt
Dma
Iommu
PciConfig
Firmware
```

but this is outside the ordinary application runtime.

---

# 120. Device Serialization

Device metadata can use BOOTSTRAP-612 for:

```text
DeviceInfo
DeviceCapabilities
DeviceConfiguration
```

Actual live handles must not be serialized as portable values.

---

# 121. Device Handles and Checkpointing

BOOTSTRAP-600 checkpoints must not assume live device handles survive process restart.

Instead store:

```text
device identity
configuration
resource identity
```

and reopen/recreate at recovery.

---

# 122. GPU Checkpointing

GPU resources may be reconstructed from:

```text
package resources
resource hashes
application state
```

rather than serializing native driver handles.

---

# 123. Device Diagnostics

Every device operation can carry:

```text
device_id
generation
driver
submission_id
resource_id
```

into BOOTSTRAP-602 diagnostics.

---

# 124. Device Error Context

A failure should expose:

```text
operation
device
driver
error_code
recoverability
```

without leaking privileged information.

---

# 125. Device Error Classes

```text
DeviceNotFound
DeviceRemoved
DeviceBusy
PermissionDenied
Unsupported
InvalidConfiguration
Timeout
Cancelled
OutOfMemory
QueueFull
DeviceLost
DriverFailure
IoFailure
DmaFailure
```

---

# 126. Recovery Policy

Recovery tiers:

```text
Retry
Reopen
Reset
Recreate
FailOperation
FailService
```

The runtime does not automatically reset hardware unless explicitly configured.

---

# 127. Supervisor Integration

A service using a device can declare:

```text
required_devices
```

The supervisor can delay readiness until required devices are available.

---

# 128. Device Availability

Example:

```text
Service:
    required:
        gpu0
        camera0
```

Service readiness becomes false if a mandatory device is lost.

---

# 129. Device Hot-Plug + Supervisor

If a required device disappears:

```text
DeviceRemoved
 ↓
service degraded
 ↓
optional recovery/restart
```

according to service policy.

---

# 130. Device Discovery Cache

Enumeration metadata can be cached briefly.

Cache invalidation occurs on device-change events.

---

# 131. Device Event Ordering

For one device generation:

```text
Added
Configured
Available
Changed*
Removed
```

must preserve logical ordering.

`Changed` may occur multiple times.

---

# 132. Device Event Overflow

If an event queue overflows:

```text
EventOverflow
```

must be reported.

Consumers should rescan the device snapshot.

---

# 133. Snapshot + Events Pattern

Correct pattern:

```text
snapshot = enumerate()
subscribe(events)
rescan_if_overflow()
```

This avoids depending on an infinite reliable event history.

---

# 134. Device Configuration

Configuration uses immutable snapshots:

```text
DeviceConfig
```

Applying a new configuration produces a new configuration state.

---

# 135. Configuration Transactions

Where supported:

```text
tx = device.configure_begin()
tx.set(...)
tx.commit()
```

Failure leaves the old configuration active where the hardware permits atomic configuration.

---

# 136. Partial Hardware Configuration

If a device cannot configure atomically, the backend must report partial application explicitly.

---

# 137. Device Profiles

A device may expose profiles:

```text
Performance
Balanced
PowerSaving
LowLatency
Custom
```

Profiles are policy hints, not guaranteed behavior.

---

# 138. Latency Classes

Operations may declare:

```text
Realtime
Interactive
Normal
Background
```

Scheduler/resource policies coordinate with device queues.

---

# 139. Real-Time Restrictions

Real-time operations should avoid:

- allocation;
- blocking;
- unpredictable locks;
- filesystem operations.

---

# 140. Audio Real-Time Example

```text
audio_callback(buffer):
    mix(buffer)
```

The callback should execute deterministic, bounded work.

---

# 141. Camera Pipeline

Example:

```text
Camera
 ↓
DMA Buffer
 ↓
CPU/GPU Shared Buffer
 ↓
GPU Processing
 ↓
Encoder
```

Each boundary has explicit ownership.

---

# 142. GPU Pipeline

Example:

```text
Package Resource
 ↓
CPU/Storage Buffer
 ↓
DMA Upload
 ↓
GPU Buffer
 ↓
Compute Queue
 ↓
GPU Result
 ↓
Mapped/Transfer Buffer
```

---

# 143. AI Accelerator Pipeline

Example:

```text
AXPK Model
 ↓
Object/Chunk Store
 ↓
Host Buffer
 ↓
DMA
 ↓
Accelerator Memory
 ↓
Accelerator Queue
 ↓
Output Buffer
```

This supports large-model streaming without requiring all weights in CPU memory.

---

# 144. Memory Ownership Model

Every device buffer has one of:

```text
CpuOwned
DeviceOwned
Shared
InFlight
Released
```

Illegal transitions are rejected.

---

# 145. Buffer State Machine

```text
Allocated
 ↓
Mapped
 ↓
Ready
 ↓
InFlight
 ↓
Completed
 ↓
Reusable
 ↓
Released
```

---

# 146. Use-After-Free Prevention

A buffer cannot be released while:

```text
submission_count > 0
```

The runtime tracks in-flight references.

---

# 147. Zero-Copy

Zero-copy is permitted when:

- hardware supports shared memory;
- alignment is valid;
- ownership is synchronized;
- security policy allows it.

Otherwise the runtime uses explicit copies.

---

# 148. Scatter/Gather DMA

DMA APIs may support:

```text
DmaSegment[]
```

instead of requiring contiguous physical memory.

---

# 149. IOMMU

Where available, DMA mappings should use IOMMU isolation.

The application sees:

```text
DmaMapping
```

rather than arbitrary physical addresses.

---

# 150. Device Memory Accounting

GPU/DMA allocations charge the resource group that owns them.

Shared allocations use explicit attribution.

---

# 151. Device Memory Budget

The runtime can expose:

```text
used
reserved
available
budget
pressure
```

for GPU/device memory.

---

# 152. Device Memory Eviction

Only resources marked:

```text
Reconstructible
Cacheable
```

may be automatically evicted.

Authoritative application data must not be silently discarded.

---

# 153. Reconstructible Resources

Resource metadata may declare:

```text
reconstructible = true
```

and reference the source package object.

This integrates directly with 613.

---

# 154. GPU Resource Restoration

After device loss:

```text
package object
 → CPU resource
 → GPU upload
```

can recreate reconstructible resources.

---

# 155. Device Feature Query

API:

```text
device.supports(feature)
```

must return explicit capability.

Applications must not infer support from vendor names.

---

# 156. Feature Sets

GPU feature sets may include:

```text
fp16
fp64
int8
tensor
ray_tracing
mesh_shader
video_decode
video_encode
```

but feature names remain extensible.

---

# 157. Device Limits

Query:

```text
max_buffer_size
max_texture_size
max_queue_count
max_workgroup_size
max_shared_memory
```

---

# 158. Vendor Extensions

Extensions can be represented:

```text
VendorExtensionId
```

without polluting the core abstraction.

---

# 159. Extension Safety

Vendor-specific extensions require:

```text
provider
capability
version
```

and explicit support checks.

---

# 160. Driver Version

Device cache compatibility must include driver identity/version where driver-dependent resources exist.

---

# 161. Firmware Version

Firmware information is diagnostic metadata.

Firmware updates are outside ordinary application runtime authority.

---

# 162. Device Reset Security

Reset can disrupt other processes.

Therefore reset requires stronger capability than ordinary device use.

---

# 163. Device Sharing

The backend determines whether:

```text
Shared
Exclusive
Partitioned
Virtualized
```

access is available.

Axiom must not emulate unsafe sharing.

---

# 164. Virtual Devices

Virtual devices are first-class:

```text
VirtualGpu
VirtualNetwork
VirtualSensor
VirtualCamera
VirtualStorage
```

Useful for:

- tests;
- containers;
- VMs;
- WASM;
- deterministic simulation.

---

# 165. Device Test Backend

A deterministic fake device backend must support:

```text
create_device()
remove_device()
emit_event()
submit()
complete()
fail()
```

---

# 166. Hardware Simulation

Tests can simulate:

```text
device loss
DMA failure
timeout
queue overflow
hot unplug
memory pressure
```

without real hardware.

---

# 167. Device Fuzzing

Fuzz:

- device descriptors;
- USB descriptors;
- PCI metadata;
- sensor packets;
- camera metadata;
- GPU capability tables;
- driver responses.

---

# 168. Driver Fuzz Boundary

Driver/provider responses are treated as untrusted data at the API boundary.

Length and enum validation are mandatory.

---

# 169. Device Descriptor Validation

Malformed descriptors must not cause:

- buffer overflow;
- integer overflow;
- unbounded allocation;
- invalid handle creation.

---

# 170. Security Boundary for Vendor Drivers

Vendor drivers execute outside Axiom's normal memory-safety boundary.

The provider interface must validate all returned metadata.

---

# 171. Device Capability Delegation

A privileged process can delegate an attenuated device handle to another process through BOOTSTRAP-604.

Example:

```text
GPU Submit
```

without:

```text
GPU Reset
```

---

# 172. Device Handle Transfer

Transferred handles retain:

```text
device identity
generation
rights
expiry
```

where policy requires.

---

# 173. Device Capability Revocation

A delegated capability can be revoked by invalidating its generation/token.

---

# 174. Cross-Process GPU

Optional:

```text
DeviceHandle
SharedBuffer
SubmissionCapability
```

can be transferred through IPC.

The receiving process does not automatically gain the sender's other privileges.

---

# 175. Cross-Process DMA

Highly restricted.

Only explicitly authorized mappings can cross process boundaries.

---

# 176. Device Service Architecture

A system may isolate device access:

```text
Application
   ↓ IPC
Device Service
   ↓
Driver
```

This is useful when device drivers need stronger isolation.

---

# 177. Direct Device Architecture

High-performance applications may use:

```text
Application
   ↓
Axiom Device API
   ↓
OS Driver
```

without a user-space broker.

---

# 178. Broker Choice

Brokered vs direct access is deployment policy, not language semantics.

---

# 179. Device Resource Naming

Stable logical names:

```text
gpu/0
camera/0
audio/output/0
sensor/accelerometer/0
```

Names are convenience identifiers.

`DeviceId` remains authoritative.

---

# 180. Device URI

Optional URI-like representation:

```text
device://gpu/0
device://camera/0
device://usb/1-2
```

These are serialized references, not security authority.

---

# 181. Device Configuration Serialization

Configuration can be represented as AXBIN:

```text
device.config.axbin
```

but native handles cannot.

---

# 182. Device Capability Manifest

Applications may declare:

```text
@requires_device(gpu.compute)
@requires_device(camera.capture)
```

The compiler emits deployment metadata.

---

# 183. Package Integration

BOOTSTRAP-613 package manifests may declare:

```text
required_devices
optional_devices
device_features
```

Example:

```text
requires:
    gpu.compute
    accelerator.tensor
```

---

# 184. Package + Device Selection

An application package may contain variants:

```text
cpu
gpu
npu
```

The runtime selects only among explicitly declared compatible variants.

---

# 185. No Implicit Native Code Selection

A package must not silently load arbitrary vendor binaries based only on device detection.

Selection must be constrained by trusted package metadata.

---

# 186. Device-Specific Resources

Examples:

```text
shader.dxil
shader.spirv
shader.msl
model.npu
model.cpu
```

Selection uses explicit target metadata.

---

# 187. GPU Pipeline Cache

Pipeline caches may be stored in the object store.

Identity:

```text
package_root
shader_hash
device_id
driver_version
pipeline_config
```

---

# 188. Pipeline Cache Safety

A pipeline cache is disposable.

If invalid, the runtime recompiles/recreates the pipeline.

---

# 189. Device Event Diagnostics

Every event includes:

```text
timestamp
device_id
generation
event_type
backend
```

---

# 190. Device Metrics

Recommended:

```text
device_open_count
device_error_count
gpu_memory_used
gpu_memory_budget
queue_depth
submission_latency
dma_bytes
usb_transfer_rate
camera_frame_rate
audio_underruns
device_temperature
```

---

# 191. Audio Diagnostics

Important events:

```text
AudioUnderrun
AudioOverrun
DeviceChanged
ClockDrift
FormatRejected
```

---

# 192. Camera Diagnostics

Events:

```text
FrameDrop
ExposureChange
DeviceRemoved
FormatChange
CaptureError
```

---

# 193. GPU Diagnostics

Events:

```text
QueueTimeout
DeviceLost
OutOfMemory
Reset
ShaderFailure
SubmissionError
```

---

# 194. Thermal Diagnostics

Events:

```text
ThermalNormal
ThermalWarning
ThermalCritical
Throttling
```

---

# 195. Resource Governor Integration

The governor can react to device pressure:

```text
GPU memory pressure
 ↓
cache eviction
 ↓
allocation throttling
 ↓
application notification
```

without automatically terminating arbitrary applications.

---

# 196. Scheduler Integration

CPU workers:

```text
submit GPU command
→ suspend
→ await fence
→ resume
```

No CPU busy-wait is required.

---

# 197. Synchronization Integration

CPU/GPU synchronization uses:

```text
GpuFence
```

while CPU-side coordination uses:

```text
Mutex
Atomic
Event
Channel
```

from BOOTSTRAP-608.

---

# 198. Networking Integration

Network-received data can flow:

```text
network buffer
→ DMA/shared buffer
→ accelerator/GPU
```

when the platform supports compatible memory.

---

# 199. Storage Integration

Storage can stream directly toward device memory when the platform supports:

```text
storage → DMA → GPU
```

otherwise:

```text
storage → CPU buffer → GPU
```

---

# 200. Package Integration

613 provides:

```text
immutable source resource
```

614 provides:

```text
device-resident representation
```

This creates a clean CPU/storage/device boundary.

---

# 201. Zero-Copy Package-to-Device

Future optimized path:

```text
AXPK chunk
 ↓
storage DMA
 ↓
device memory
```

The API may expose this only when all platform constraints are satisfied.

---

# 202. Decompression-to-GPU

A future provider may support:

```text
compressed chunk
 ↓
GPU/accelerator decompression
 ↓
device buffer
```

The public API remains generic.

---

# 203. Device Resource Import

```text
device.import(resource)
```

may create device-resident data directly from a package resource.

---

# 204. Device Resource Export

```text
device.export(resource)
```

may stream data back to package/storage.

This must not overwrite immutable package content.

---

# 205. Device Memory Snapshot

Device memory is generally not directly checkpointable.

The application should persist reconstructible source data instead.

---

# 206. Recovery Model

```text
Application State
       +
Package Objects
       +
Device Capability
       ↓
Recreate Device Resources
```

---

# 207. Device Recovery

Recovery sequence:

```text
detect loss
 ↓
cancel dependent submissions
 ↓
invalidate device handles
 ↓
reopen device
 ↓
recreate resources
 ↓
resume
```

Only supported when backend/device permits.

---

# 208. Device Failure Escalation

If recovery fails:

```text
operation failure
→ component degraded
→ service failure
→ supervisor recovery
```

according to BOOTSTRAP-605.

---

# 209. No Hidden Reset

Device loss must not silently trigger destructive reset of shared hardware.

Reset is explicit or policy-driven with sufficient capability.

---

# 210. Embedded Interrupt Example

Conceptually:

```text
interrupt gpio0:
    signal(event)

task:
    await event
    process()
```

The interrupt handler remains minimal.

---

# 211. Embedded MMIO Example

Privileged profile:

```text
gpio.write(pin, true)
```

compiles to validated MMIO access.

The application does not manipulate arbitrary physical addresses.

---

# 212. GPIO

Logical API:

```text
GpioController
GpioPin
```

operations:

```text
input
output
high
low
toggle
interrupt
```

---

# 213. I2C

```text
I2cBus
I2cDevice
I2cTransaction
```

supports:

```text
write
read
write_read
```

with transaction boundaries.

---

# 214. SPI

```text
SpiBus
SpiDevice
SpiTransfer
```

supports:

```text
full_duplex
half_duplex
chip_select
clock
mode
```

---

# 215. CAN

Optional embedded profile:

```text
CanBus
CanFrame
CanFilter
```

with bounded queues.

---

# 216. UART

UART supports asynchronous read/write and configurable framing.

---

# 217. Peripheral Discovery

Embedded boards may use static device manifests:

```text
board.axdevice
```

rather than dynamic discovery.

---

# 218. Device Tree Boundary

Linux/embedded systems may import device-tree information.

Axiom converts it into validated `DeviceInfo`.

The raw device tree is not itself the application API.

---

# 219. ACPI Boundary

Windows/Linux x86 platforms may expose ACPI-derived metadata.

The application sees normalized device information.

---

# 220. Device Metadata Trust

Hardware metadata is treated as untrusted input until validated.

---

# 221. Resource Ownership

Every device resource must have one owner:

```text
process
service
device session
resource group
```

Shared ownership requires explicit reference/lease semantics.

---

# 222. Resource Transfer

Resources can transfer through:

```text
move
share
duplicate
IPC capability transfer
```

according to device semantics.

---

# 223. No Implicit Aliasing

Two handles referencing the same device resource must have explicit identity.

This prevents accidental ownership confusion.

---

# 224. Lifetime Rules

```text
Device
 └── Session
      ├── Queue
      ├── Buffer
      ├── Mapping
      └── Submission
```

Destroying a parent must either:

- safely drain children;
- explicitly invalidate them.

---

# 225. Structured Device Ownership

Axiom can use structured lifetime:

```text
with device.open() as d:
    ...
```

without requiring a garbage collector.

---

# 226. Device Handle RAII

Compiler-generated cleanup may release:

```text
device handles
buffers
queues
mappings
sessions
```

at deterministic scope exit.

---

# 227. No Hidden Finalizer

Device resource cleanup must not depend on nondeterministic garbage collection.

---

# 228. Explicit Close

For asynchronous resources:

```text
await handle.close()
```

may be required when pending operations exist.

---

# 229. Error on Premature Close

If a device resource is still in flight:

```text
ResourceBusy
```

may be returned.

---

# 230. Device Scope

A structured scope can ensure:

```text
open
→ use
→ drain
→ close
```

before leaving the scope.

---

# 231. Compiler Lifetime Metadata

The compiler may track:

```text
resource owner
in-flight use
close state
```

without implementing a global borrow checker.

This is a narrow resource-lifetime safety mechanism, not a general language ownership system.

---

# 232. Pointer-Free Device API

Applications should normally manipulate:

```text
DeviceHandle
BufferHandle
QueueHandle
```

rather than raw pointers.

---

# 233. Unsafe Device API

Privileged systems programming may explicitly opt into:

```text
unsafe mmio
unsafe dma
unsafe interrupt
```

but this is isolated from normal application APIs.

---

# 234. Capability + Unsafe

`unsafe` means:

```text
compiler safety guarantees are reduced
```

It does not grant:

```text
device.raw_io
```

Capability remains required.

---

# 235. Compiler Validation

For device APIs the compiler can validate:

- handle types;
- resource states where statically representable;
- required capabilities;
- async usage;
- alignment;
- buffer usage flags.

---

# 236. Runtime Validation

Runtime validates:

- device generation;
- bounds;
- state;
- permissions;
- queue state;
- resource lifetime;
- backend support.

---

# 237. Compile-Time Device Requirements

Example:

```text
@requires_device(gpu.compute)
fn run_model(...)
```

The compiler emits deployment metadata.

---

# 238. Runtime Device Selection

Example:

```text
gpu = Device.select(
    class = Gpu,
    requires = [Compute, FP16]
)
```

Selection returns a concrete generation-safe handle.

---

# 239. Deterministic Device Selection

When multiple devices match, selection policy must be explicit:

```text
first
preferred_vendor
highest_memory
lowest_latency
explicit_id
```

The runtime must not silently claim that one policy is universally superior.

---

# 240. Device Selection Policy

Application configuration can specify:

```text
gpu_preference
accelerator_preference
camera_preference
audio_preference
```

through BOOTSTRAP-601.

---

# 241. Multi-Device Scheduling

Applications can create independent queues per device:

```text
gpu0.compute
gpu1.compute
npu0.inference
```

The scheduler tracks them separately.

---

# 242. Cross-Device Synchronization

Where supported:

```text
GpuFence
SharedEvent
DmaFence
```

can coordinate devices.

Otherwise explicit staging is required.

---

# 243. Device Interoperability

Interop handles may bridge:

```text
GPU ↔ Video
GPU ↔ Camera
GPU ↔ Display
GPU ↔ Accelerator
GPU ↔ Network
```

only where the backend supports it.

---

# 244. No Universal Zero-Copy Promise

Axiom exposes zero-copy as a capability, not a guaranteed property.

---

# 245. Device Buffer Alignment

Each backend reports:

```text
required_alignment
optimal_alignment
```

The compiler/runtime uses typed allocation APIs.

---

# 246. Pinned CPU Memory

Pinned memory is explicitly represented:

```text
PinnedBuffer
```

because it consumes special OS/device resources.

---

# 247. Pinned Memory Quota

Pinned memory is charged against BOOTSTRAP-606.

---

# 248. Device Memory Allocation Failure

Failure must distinguish:

```text
OutOfDeviceMemory
OutOfHostMemory
QuotaExceeded
Fragmentation
Unsupported
```

where the backend can identify the reason.

---

# 249. Device Fragmentation

The runtime should prefer:

- suballocation;
- pools;
- arenas;
- buddy allocators

where beneficial.

The exact allocator is internal.

---

# 250. Device Memory Pool

```text
DeviceMemoryPool
```

can reduce allocation overhead.

Pool lifetime is bounded by device/session lifetime.

---

# 251. Pool Reclamation

Unused pool memory can be returned to the device allocator under memory pressure.

---

# 252. GPU Descriptor Resources

Descriptor sets/tables can be exposed by higher-level graphics APIs.

614 only needs generic device resource allocation/synchronization.

---

# 253. Graphics Boundary

Axiom graphics runtime may later build:

```text
RenderDevice
RenderPass
Pipeline
Shader
Texture
Sampler
```

on top of 614.

---

# 254. Compute Boundary

Axiom compute runtime may build:

```text
Tensor
Kernel
ComputeGraph
```

on top of 614.

This is intentionally separate from the base device layer.

---

# 255. AI Runtime Boundary

An AI runtime can map:

```text
Tensor buffer
→ AcceleratorBuffer
```

without changing the core device abstraction.

---

# 256. Camera/Media Boundary

A media subsystem can build:

```text
VideoFrame
AudioFrame
Codec
CapturePipeline
```

on top of 614.

---

# 257. Device Package Metadata

613 packages may contain:

```text
device compatibility
required features
compiled variants
resource formats
```

614 interprets these declaratively.

---

# 258. Package Resource Import

Example:

```text
model = await gpu.import_resource(
    package.resource("model.weights")
)
```

The package remains immutable.

---

# 259. Device Resource Cache Key

A device resource cache uses:

```text
content_hash
device_id
driver_version
feature_set
format
```

---

# 260. Cache Invalidation

Changing any incompatible component invalidates the device cache.

---

# 261. Device Resource Security

Sensitive resources can remain encrypted in storage and be decrypted only into authorized buffers.

---

# 262. Secure Device Path

Possible architecture:

```text
Encrypted AXPK
 ↓
Secure Key
 ↓
Decrypt stream
 ↓
Pinned/Device buffer
 ↓
GPU/Accelerator
```

Plaintext may never need to be persisted to disk.

---

# 263. Protected Memory

Where platform hardware supports secure/protected memory, a provider may expose:

```text
ProtectedBuffer
```

with restricted CPU mapping.

---

# 264. Protected Buffer Policy

Applications must not assume that protected buffers are readable from CPU memory.

---

# 265. Secure Camera Path

Future media providers may support:

```text
Camera
 ↓
ProtectedBuffer
 ↓
GPU/Encoder
```

without CPU-visible frames.

---

# 266. Device Attestation Boundary

Hardware-backed attestation may be exposed by a security provider.

614 only exposes the device identity/capability boundary.

Trust decisions remain with BOOTSTRAP-610/603.

---

# 267. Hardware Randomness

A hardware RNG may appear as:

```text
RandomDevice
```

but cryptographic randomness should still use BOOTSTRAP-610's secure random provider.

---

# 268. Hardware Crypto

Crypto accelerators may be surfaced through BOOTSTRAP-610 providers rather than directly exposed to ordinary applications.

---

# 269. Device Discovery Cost

Enumeration should be:

```text
lazy
snapshot-based
cached
```

where platform APIs are expensive.

---

# 270. Device Event Subscription Cost

Subscriptions are per-filter/per-device.

A global polling loop is not required.

---

# 271. Event Backpressure

If device events exceed queue capacity:

```text
overflow
→ rescan snapshot
```

rather than unbounded memory growth.

---

# 272. Device Resource Limits

Every subsystem must expose bounded limits.

Example:

```text
max_pending_transfers
max_queue_depth
max_event_queue
max_mapped_memory
```

---

# 273. Device API Determinism

The API itself is deterministic.

Hardware timing and scheduling obviously remain nondeterministic.

---

# 274. Test Determinism

Virtual devices can provide deterministic:

```text
timestamps
completion order
errors
device insertion/removal
```

---

# 275. Performance Requirements

Targets:

```text
device lookup: O(1) average
handle validation: O(1)
event delivery: bounded
buffer allocation: low overhead
queue submission: near-native backend overhead
```

---

# 276. Zero Allocation Fast Path

Frequently repeated operations should support:

```text
preallocated command buffers
preallocated event buffers
pool-backed DMA buffers
```

---

# 277. Hot Path Locks

Device submission should avoid global locks.

Use:

```text
per-device queues
per-queue synchronization
atomics
```

where practical.

---

# 278. ABI Stability

Device ABI includes:

```text
backend version
device interface version
feature set
struct layout version
```

Opaque handles prevent layout coupling.

---

# 279. FFI

External native APIs can be wrapped through FFI.

The wrapper should convert native pointers/handles into safe Axiom handles where possible.

---

# 280. No Third-Party Runtime Requirement

Axiom's device abstraction itself requires no third-party framework.

Vendor drivers remain external OS/platform components.

---

# 281. Minimal Device Runtime

Minimal profile may include only:

```text
device enumeration
device handles
events
basic storage/device I/O
```

GPU/media stacks can be omitted.

---

# 282. Full Device Runtime

Full profile may add:

```text
USB
Bluetooth
camera
audio
GPU
accelerators
DMA
MMIO
embedded peripherals
```

---

# 283. Embedded Minimal Profile

Possible:

```text
GPIO
I2C
SPI
UART
CAN
DMA
interrupt
MMIO
```

with no desktop device enumeration.

---

# 284. WASM Minimal Profile

Possible:

```text
host devices
virtual filesystem
GPU/WebGPU provider
audio/input host provider
```

---

# 285. Error ABI

Device errors must have stable numeric codes plus structured metadata.

---

# 286. Diagnostics ABI

Every backend should be able to emit:

```text
backend
operation
native_error_code
native_error_domain
```

without requiring applications to know platform-specific codes.

---

# 287. Native Error Preservation

The runtime should preserve the native error for advanced diagnostics while exposing a portable error classification.

---

# 288. Device Test Contract

Every backend must pass:

```text
enumeration
open
close
event
error
lifetime
concurrency
resource limit
hot-plug
```

tests applicable to its platform.

---

# 289. Acceptance Criteria

1. Device enumeration exists.
2. Device snapshots are immutable.
3. Device identities include generation safety.
4. Device handles are opaque.
5. Device states are explicit.
6. Device classes are extensible.
7. Device capabilities are queryable.
8. Device authority is capability-based.
9. Device enumeration does not grant device access.
10. Platform backends are isolated.
11. Windows backend boundary is defined.
12. Linux backend boundary is defined.
13. macOS backend boundary is defined.
14. Android backend boundary is defined.
15. iOS backend boundary is defined.
16. WASM host-device boundary is defined.
17. Embedded backend is defined.
18. USB abstraction exists.
19. PCI/PCIe abstraction exists.
20. Serial abstraction exists.
21. Bluetooth abstraction exists.
22. HID/input abstraction exists.
23. Display abstraction exists.
24. Audio abstraction exists.
25. Camera abstraction exists.
26. Sensor abstraction exists.
27. GPU abstraction exists.
28. Accelerator abstraction exists.
29. DMA abstraction exists.
30. MMIO boundary exists.
31. Interrupt boundary exists.
32. IOMMU isolation is supported where available.
33. Physical addresses are not ordinary application values.
34. DMA ownership is explicit.
35. Device buffer lifetime is explicit.
36. In-flight buffers cannot be prematurely reclaimed.
37. Device queues support asynchronous submission.
38. Device fences integrate with async/await.
39. Blocking wrappers are explicit.
40. Cancellation semantics are explicit.
41. Timeout semantics are explicit.
42. Queue backpressure is bounded.
43. Device hot-plug is supported.
44. Device removal invalidates the correct generation.
45. Event overflow causes rescan rather than unbounded memory.
46. Device reset is capability-protected.
47. Device loss is represented explicitly.
48. GPU device loss can trigger resource recreation where supported.
49. Device memory is accounted by BOOTSTRAP-606.
50. Pinned memory is accounted.
51. GPU memory budgets are visible.
52. Device allocation failures are typed.
53. Shared device resources have explicit ownership.
54. Cross-process device capabilities can be transferred through IPC.
55. Transferred capabilities are attenuable.
56. Device permissions integrate with BOOTSTRAP-603.
57. Package resources integrate with BOOTSTRAP-613.
58. Device metadata integrates with BOOTSTRAP-612.
59. Storage/device streaming integrates with BOOTSTRAP-611.
60. Async operations integrate with BOOTSTRAP-607.
61. Synchronization integrates with BOOTSTRAP-608.
62. Device network/remote providers can integrate with BOOTSTRAP-609.
63. Hardware cryptography can integrate with BOOTSTRAP-610.
64. Diagnostics integrate with BOOTSTRAP-602.
65. Service readiness can depend on devices.
66. Device failure can propagate to supervision.
67. Checkpointing does not serialize live native handles.
68. Recovery can recreate device resources.
69. GPU resources can reference package content identity.
70. Shader/device caches include device/driver identity.
71. Resource caches are disposable.
72. Device-specific package variants are explicit.
73. Package metadata cannot silently grant hardware privileges.
74. Vendor extensions are isolated.
75. Driver ABI is versioned.
76. Driver responses are validated.
77. Device descriptors are fuzz-tested.
78. USB descriptors are fuzz-tested.
79. GPU capability metadata is fuzz-tested.
80. Device removal is stress-tested.
81. DMA failure is tested.
82. Queue timeout is tested.
83. Device reset is tested.
84. Device loss is tested.
85. Resource reconstruction is tested.
86. Device hot-plug is tested.
87. Event overflow is tested.
88. Virtual devices exist for deterministic tests.
89. Device APIs can operate without a garbage collector.
90. Device resource cleanup is deterministic.
91. Struct-only APIs are possible.
92. Static dispatch is possible.
93. Minimal profiles can dead-strip unused device classes.
94. Raw MMIO is privileged.
95. Unsafe does not grant capabilities.
96. No arbitrary physical-memory access exists in ordinary application mode.
97. Device selection policy is explicit.
98. Multi-device operation is supported.
99. Cross-device synchronization is explicit.
100. Zero-copy is capability-based rather than assumed.
101. Device resource alignment is queryable.
102. Pinned memory has quotas.
103. Real-time callbacks have bounded behavior requirements.
104. Audio callbacks can avoid blocking.
105. Camera streams support asynchronous frames.
106. Sensor streams support bounded backpressure.
107. GPU queues expose completion primitives.
108. Accelerator queues expose completion primitives.
109. Package-to-device streaming is possible.
110. Large model resources can be streamed into accelerator memory.
111. Protected buffers can be represented where supported.
112. Device attestation can integrate with the security layer.
113. Native errors remain diagnosable.
114. Platform-specific native error codes can be preserved.
115. Device APIs have stable ABI contracts.
116. Backend conformance tests exist.
117. Resource limits are enforceable.
118. Device operations produce structured diagnostics.
119. Device handles cannot silently alias replacement devices.
120. Unsupported device features fail explicitly.

---

# 290. Final Device Architecture

```text
                         ┌────────────────────────────┐
                         │      Axiom Application      │
                         └─────────────┬──────────────┘
                                       │
                         ┌─────────────▼──────────────┐
                         │      Device API 614        │
                         └─────────────┬──────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
             ┌──────▼─────┐     ┌──────▼─────┐    ┌──────▼──────┐
             │ CPU Device │     │ GPU/Accel. │    │ Peripheral  │
             │ Resources  │     │ Resources  │    │ Resources   │
             └──────┬─────┘     └──────┬─────┘    └──────┬──────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       │
                         ┌─────────────▼──────────────┐
                         │     Device Registry        │
                         └─────────────┬──────────────┘
                                       │
             ┌─────────────────────────┼─────────────────────────┐
             │                         │                         │
      ┌──────▼──────┐          ┌───────▼───────┐         ┌──────▼──────┐
      │ Windows     │          │ Linux         │         │ macOS       │
      │ Backend     │          │ Backend       │         │ Backend     │
      └─────────────┘          └───────────────┘         └─────────────┘
             │                         │                         │
      ┌──────▼──────┐          ┌───────▼───────┐         ┌──────▼──────┐
      │ Android     │          │ iOS           │         │ Embedded    │
      │ Backend     │          │ Backend       │         │ Backend     │
      └─────────────┘          └───────────────┘         └─────────────┘

                    Security 603
                         │
                    Resources 606
                         │
                    Scheduler 607
                         │
                 Synchronization 608
                         │
                    Storage 611
                         │
                 Package/Resource 613
```

---

# 291. Cross-Layer Resource Flow

```text
                    AXPK / Object Store
                           │
                           ▼
                    Storage Buffer
                           │
                    ┌──────┴──────┐
                    │             │
                  CPU          DMA/Map
                    │             │
                    └──────┬──────┘
                           ▼
                    Device Buffer
                           │
                    ┌──────┼──────┐
                    │      │      │
                  GPU     NPU    Video
                    │      │      │
                    └──────┼──────┘
                           ▼
                    Device Result
                           │
                    ┌──────┴──────┐
                    │             │
                 Display        CPU
```

---

# 292. Architectural Boundary

BOOTSTRAP-614 deliberately establishes the lowest ordinary application-facing hardware layer.

The resulting hierarchy is:

```text
600  Application State
601  Configuration
602  Diagnostics
603  Security
604  IPC
605  Supervision
606  Resource Governance
607  Scheduling / Async
608  Synchronization
609  Networking
610  Cryptography
611  Storage / VFS
612  Serialization / Structured Storage
613  Packaging / Objects / Resources
614  Devices / Hardware / Accelerators
```

This is an important milestone because the language/runtime now has a complete path from:

```text
persistent bytes
      ↓
structured data
      ↓
package/resource
      ↓
CPU memory
      ↓
DMA
      ↓
GPU / NPU / peripheral
      ↓
application computation
```

without requiring a separate mandatory runtime framework.

---

# 293. Task Completion

**BOOTSTRAP-614 is complete.**

The next architecture task is:

## BOOTSTRAP-615 — Native Graphics, Windowing, Display Composition, Rendering Pipeline & GPU Command Runtime 5.0

It will build above 614 and define the actual graphics-facing layer: windows/surfaces, swapchains, render targets, command recording, pipelines, shaders, textures, samplers, render graphs, synchronization, frame pacing, HDR/color management, multi-window, headless rendering, software rendering fallback, WebGPU/Metal/Vulkan/D3D/embedded mappings, and integration with Axiom's device/resource/package model.
:::