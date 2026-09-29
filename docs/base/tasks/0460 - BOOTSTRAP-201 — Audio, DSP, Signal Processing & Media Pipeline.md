# BOOTSTRAP-201 — Audio, DSP, Signal Processing & Media Pipeline

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu:

> **Axiom phải có nền tảng native đủ mạnh cho audio real-time, DSP, TTS/STT, game audio, DAW, video/media processing và AI audio mà không cần GC, không bắt buộc runtime lớn và không biến realtime programming thành một hệ thống annotation phức tạp.**

Nguyên tắc:

```text
Audio/Media = library + compiler-aware optimization
Core = ownership + capability + concurrency + SIMD + async
```

---

# 201.1. Audio không thuộc Core

Core không cần biết:

```text
AudioBuffer
FFT
WAV
MP3
AAC
MIDI
VideoFrame
```

Các thành phần này nằm ở:

```text
std::audio
std::dsp
std::media
std::codec
```

hoặc package chuyên dụng.

---

# 201.2. Audio primitive

Đơn vị semantic cơ bản:

```text
Sample
Frame
Channel
Buffer
Stream
```

Ví dụ:

```text
AudioBuffer<f32>
```

không phải một mảng `f32` đơn thuần vì còn:

```text
sample_rate
channels
layout
frames
format
```

---

# 201.3. Sample type

Hỗ trợ:

```text
f32
f64
i16
i24
i32
```

và các format phần cứng nếu cần.

Nhưng DSP nội bộ thường ưu tiên floating-point.

---

# 201.4. Audio format

Audio format:

```text
SampleFormat
SampleRate
ChannelLayout
Interleaving
```

Ví dụ:

```text
48 kHz
stereo
f32
interleaved
```

là một semantic format.

---

# 201.5. Interleaved và planar

Cả hai:

```text
Interleaved:
L R L R L R

Planar:
L L L L
R R R R
```

được hỗ trợ.

Không ép một layout duy nhất.

---

# 201.6. Audio view

Không copy khi xử lý block:

```text
AudioView<f32>
AudioMutView<f32>
```

dựa trên capability system.

Ví dụ:

```text
process(input: AudioView<f32>,
        output: AudioMutView<f32>)
```

Compiler có thể kiểm tra overlap.

---

# 201.7. Block processing

DSP chủ yếu xử lý block:

```text
input block
     ↓
DSP
     ↓
output block
```

thay vì từng sample nếu thuật toán cho phép.

Điều này rất phù hợp SIMD/vectorization.

---

# 201.8. Sample-by-sample vẫn được hỗ trợ

Một DSP algorithm có thể:

```text
process_sample(x)
```

Compiler có thể inline và vectorize khi có thể.

---

# 201.9. Audio graph

Audio processing có thể biểu diễn:

```text
Input
  ↓
EQ
  ↓
Compressor
  ↓
Reverb
  ↓
Mixer
  ↓
Output
```

thành:

```text
AudioGraph
```

---

# 201.10. Graph không bắt buộc allocation runtime

Graph được xây dựng trước khi real-time execution.

Sau đó runtime có thể compile thành:

```text
AudioSchedule
```

và callback chỉ chạy schedule đã chuẩn bị.

---

# 201.11. Real-time callback

Đây là phần quan trọng nhất.

Audio callback có contract:

```text
no blocking
no unbounded allocation
no uncontrolled synchronization
bounded execution
```

---

# 201.12. Không dùng annotation cho từng dòng

Không muốn:

```text
@no_alloc
@no_lock
@realtime
@no_gc
@bounded
```

ở mọi function.

Thay vào đó có một execution contract:

```text
Realtime
```

cho entry point/subgraph.

Compiler phân tích call graph bên trong.

---

# 201.13. Real-time profile

Conceptually:

```text
@realtime
fn audio_callback(...)
```

là **một profile/contract**, không phải một ownership system mới.

Compiler kiểm tra:

```text
allocation
blocking
locks
IO
syscalls
unbounded loops
unknown foreign calls
```

---

# 201.14. Allocation trong realtime

Mặc định:

```text
Realtime
 └── dynamic allocation = forbidden
```

trừ khi allocation đã được chứng minh bounded/preallocated theo contract.

---

# 201.15. Preallocated memory

Pattern:

```text
AudioEngine
 ├── buffers
 ├── scratch
 ├── state
 └── queues
```

được allocate trước callback.

Realtime callback chỉ sử dụng chúng.

---

# 201.16. Scratch arena

DSP graph có thể dùng:

```text
ScratchArena
```

với:

```text
begin_frame
allocate bounded
reset
```

Không có individual heap allocation trong hot path.

---

# 201.17. Real-time lock prohibition

Không cho:

```text
Mutex.lock()
```

trong realtime profile nếu lock có thể block.

Compiler có thể biết:

```text
blocking synchronization
```

và reject.

---

# 201.18. Lock-free communication

Audio thread giao tiếp với UI:

```text
UI
 ↓
SPSC queue
 ↓
Audio
```

hoặc:

```text
Audio
 ↓
SPSC queue
 ↓
UI
```

Ownership/channel model vẫn được dùng.

---

# 201.19. Parameter updates

Thay vì mutate shared state:

```text
UI thread
   ↓
Parameter message
   ↓
Audio thread
```

Audio nhận một value snapshot.

Điều này tránh data race.

---

# 201.20. Atomic parameters

Các tham số nhỏ có thể dùng:

```text
Atomic<f32>
Atomic<i32>
```

nếu target hỗ trợ semantics tương ứng.

Atomic không biến thành ordinary mutable reference.

---

# 201.21. Audio thread execution domain

Audio callback có execution domain:

```text
RealtimeAudio
```

Đây là library/runtime execution domain.

Compiler có thể dùng nó để kiểm tra contracts.

---

# 201.22. Send/Share

Audio state:

```text
Send
Share
```

được suy luận như bình thường.

Một DSP object có thể không `Share` nếu chứa mutable state.

---

# 201.23. DSP trait

Conceptually:

```axiom
trait AudioProcessor {
    fn process(
        self: mut_view<Self>,
        input: AudioView<f32>,
        output: AudioMutView<f32>
    )
}
```

Không cần class/interface object.

---

# 201.24. Static DSP chain

Ví dụ:

```text
EQ<8>
  → Compressor
  → Reverb
```

có thể compile thành một chain concrete.

Compiler có thể:

- inline
- eliminate abstraction
- fuse loops
- vectorize

---

# 201.25. Dynamic DSP chain

Nếu plugin/runtime cần:

```text
dyn AudioProcessor
```

được phép.

Nhưng dynamic dispatch chỉ xuất hiện khi explicit.

---

# 201.26. DSP graph specialization

Nếu graph bất biến:

```text
Input → EQ → Compressor → Output
```

framework có thể generate:

```text
CompiledAudioGraph
```

với dispatch overhead tối thiểu.

---

# 201.27. DSP graph fusion

Hai nodes:

```text
Gain
→
Bias
```

có thể fuse thành một loop.

Nhưng chỉ khi effects/state semantics cho phép.

---

# 201.28. SIMD DSP

Compiler phải tận dụng:

```text
SSE
AVX2
AVX-512
NEON
SVE
```

hoặc target tương ứng.

Không để DSP library phải viết một implementation riêng cho từng CPU nếu auto-vectorization đủ.

---

# 201.29. Explicit SIMD

Khi cần kiểm soát:

```text
Simd<f32, 8>
```

được dùng.

Axiom đã có SIMD model ở numeric architecture.

---

# 201.30. FFT

FFT là library algorithm:

```text
FFT<T>
IFFT<T>
STFT
ISTFT
```

Compiler có thể specialize theo:

```text
N
dtype
SIMD width
CPU/GPU
```

---

# 201.31. Filter

Hỗ trợ:

```text
FIR
IIR
Biquad
Convolution
```

với state rõ ràng.

State là ordinary owned struct:

```text
BiquadState
```

không hidden runtime object.

---

# 201.32. Convolution

Có thể chọn:

```text
direct
FFT convolution
partitioned convolution
GPU
```

dựa trên workload.

---

# 201.33. Resampling

```text
Resampler
```

phải giữ state qua blocks.

Ownership model đảm bảo state không bị alias sai.

---

# 201.34. Ring buffer

Audio streaming cần:

```text
RingBuffer<T>
```

được tối ưu cho:

```text
SPSC
MPSC
```

và có thể:

```text
lock-free
```

nếu implementation contract đảm bảo.

---

# 201.35. Ring buffer memory

Có thể dùng:

```text
preallocated contiguous storage
```

và atomic indexes.

Không cần GC.

---

# 201.36. Audio I/O

Platform layer:

```text
AudioDevice
InputStream
OutputStream
```

là OS resources.

Drop release resource.

---

# 201.37. Audio stream lifetime

Audio stream:

```text
open
running
stopped
closed
```

là state machine.

Invalid transitions phải bị chặn bởi API/type design hoặc runtime validation.

---

# 201.38. Audio device hotplug

Device có thể biến mất.

Đây là external event.

API phải trả:

```text
Result
Event
```

thay vì giả định device luôn tồn tại.

---

# 201.39. Audio errors

Phân biệt:

```text
DeviceError
FormatError
BufferUnderrun
BufferOverrun
PermissionError
BackendError
```

Không dùng exception machinery.

---

# 201.40. XRuns

Audio realtime có:

```text
underrun
overrun
```

đây là runtime performance event, không nhất thiết là language panic.

Có thể:

```text
drop/recover/report
```

theo engine policy.

---

# 201.41. Audio clock

Audio device có clock riêng.

Không giả định:

```text
CPU clock == audio clock
```

Media synchronization cần clock abstraction.

---

# 201.42. Timestamp

Audio frame có thể gắn:

```text
SampleTime
Timestamp
DeviceTime
```

để sync video/audio.

---

# 201.43. Media clock

Media pipeline có:

```text
MasterClock
AudioClock
VideoClock
ExternalClock
```

và synchronization policy.

---

# 201.44. MIDI

MIDI là event stream:

```text
NoteOn
NoteOff
ControlChange
PitchBend
...
```

Không biến MIDI thành audio sample.

---

# 201.45. MIDI timing

MIDI event có timestamp/sample position.

Realtime MIDI có contract tương tự audio callback.

---

# 201.46. Audio + GPU

GPU DSP:

```text
AudioBlock
 ↓
DeviceBuffer
 ↓
GPU Kernel
 ↓
DeviceBuffer
```

nhưng latency phải được explicit.

GPU không mặc định phù hợp cho every realtime audio workload.

---

# 201.47. GPU audio suitability

Framework có thể chọn:

```text
CPU SIMD
```

cho low-latency processing và:

```text
GPU
```

cho:

- offline rendering
- large convolution
- AI audio
- batch processing

---

# 201.48. AI audio

Tensor layer đã có thể xử lý:

```text
mel spectrogram
STFT
embedding
vocoder
neural codec
```

Audio layer chỉ cần chuyển:

```text
AudioBuffer
↔
Tensor
```

với explicit conversion/view khi layout tương thích.

---

# 201.49. Zero-copy Audio ↔ Tensor

Nếu:

```text
AudioBuffer layout
==
Tensor layout
```

có thể tạo view.

Nếu không:

```text
conversion
```

được thực hiện explicit/optimized.

---

# 201.50. Streaming TTS

Axiom có thể biểu diễn:

```text
Text
 ↓
Tokenizer
 ↓
Model
 ↓
Audio chunks
 ↓
Audio stream
```

với async + channels.

Không cần toàn bộ audio nằm trong RAM.

---

# 201.51. Streaming ownership

Chunk:

```text
AudioChunk
```

được move:

```text
Model
 ↓
Channel
 ↓
Output
```

Không clone toàn bộ buffer.

---

# 201.52. Backpressure

Streaming pipeline cần:

```text
bounded channel
```

để tránh memory tăng vô hạn.

Producer bị suspend/block theo execution profile.

Audio realtime không dùng blocking path; dùng preallocated ring/bounded mechanism phù hợp.

---

# 201.53. Media pipeline

General model:

```text
Source
 ↓
Demux
 ↓
Decode
 ↓
Transform
 ↓
Process
 ↓
Encode
 ↓
Mux
 ↓
Sink
```

---

# 201.54. Media frame

```text
AudioFrame
VideoFrame
SubtitleFrame
Packet
```

là các type khác nhau.

Không tạo universal `MediaObject`.

---

# 201.55. Video frame

VideoFrame có:

```text
width
height
format
planes
stride
timestamp
storage
```

---

# 201.56. Pixel formats

Ví dụ:

```text
RGBA8
RGBA16F
NV12
P010
YUV420
RGB10A2
```

được biểu diễn bởi typed formats.

---

# 201.57. Planar video

Không coi:

```text
NV12
```

là một `Array<u8>` bình thường trong high-level API.

Các planes có layout/stride riêng.

---

# 201.58. Zero-copy video

Decode → GPU:

```text
Decoder
 ↓
GPU texture
 ↓
RenderGraph
```

có thể zero-copy nếu platform/backend hỗ trợ.

---

# 201.59. Video decoder

Hardware decoder là external device resource:

```text
Decoder
```

và output có storage domain rõ ràng.

---

# 201.60. Video encoder

Tương tự:

```text
Encoder
```

nhận:

```text
VideoFrame
```

hoặc GPU texture theo contract.

---

# 201.61. Codec architecture

Codec:

```text
Decoder
Encoder
```

là traits/library abstractions.

Backend:

```text
software
hardware
platform
external
```

---

# 201.62. Codec plugin

Codec plugin có:

```text
ABI
version
capabilities
formats
```

theo ABI architecture.

---

# 201.63. No universal codec dependency

Một audio app chỉ cần WAV không được kéo:

```text
H264
H265
AV1
AAC
Opus
```

runtime graph phải tree-shake.

---

# 201.64. Streaming media

Network pipeline:

```text
Network
 ↓
Packet
 ↓
JitterBuffer
 ↓
Decoder
 ↓
Audio/Video
```

Network là external effect.

Không trộn network semantics vào Media Core.

---

# 201.65. Jitter buffer

JitterBuffer là bounded storage.

Memory growth phải có policy.

---

# 201.66. Audio-video synchronization

Synchronization dựa trên timestamps/clocks.

Không dùng thread scheduling time làm semantic timestamp.

---

# 201.67. Subtitle

Subtitle là timed text:

```text
start
end
text
style
```

Có thể tích hợp vào video pipeline nhưng vẫn là distinct data type.

---

# 201.68. Text rendering

Subtitle sử dụng Unicode/text system đã khóa ở 169 và GUI/graphics architecture.

---

# 201.69. Media pipeline parallelism

Có thể chạy:

```text
Decode
Audio DSP
Video processing
Encode
```

song song khi dependencies cho phép.

Send/Share + channels + execution domains kiểm tra safety.

---

# 201.70. Pipeline scheduler

Runtime có thể xây DAG:

```text
Decode
 ├── Audio
 └── Video
       ↓
     Encode
```

và schedule tasks.

Không cần thread-per-node.

---

# 201.71. Backpressure propagation

Nếu encoder chậm:

```text
Encoder
 ↑
Transform
 ↑
Decoder
```

pipeline phải có bounded buffering.

Không được mặc định buffer vô hạn.

---

# 201.72. Resource reuse

Media buffers có thể được pool:

```text
BufferPool
```

và reuse theo lifetime.

Ownership verifier vẫn phải biết resource state.

---

# 201.73. Reference-counting trong media

`Arc` có thể dùng khi thật sự cần shared ownership.

Không biến mọi frame thành `Arc<Frame>` mặc định.

---

# 201.74. Frame identity

Frame identity không phụ thuộc memory address.

Có thể có:

```text
FrameId
Timestamp
SequenceNumber
```

---

# 201.75. Audio graph compiler

AudioGraph có thể compile:

```text
AudioGraph
 ↓
Dependency analysis
 ↓
Buffer lifetime
 ↓
Node fusion
 ↓
SIMD specialization
 ↓
Schedule
 ↓
RealtimePlan
```

---

# 201.76. RealtimePlan

`RealtimePlan` phải chứa những thứ đã chuẩn bị:

```text
buffers
scratch
node schedule
DSP state
routing
```

Callback runtime chỉ execute plan.

---

# 201.77. Real-time safety verifier

Compiler/tooling:

```text
ax explain realtime
```

có thể trả:

```text
allocation: none
blocking call: none
unbounded loop: none
foreign call: verified
atomic: bounded
scratch usage: 32 KB
```

---

# 201.78. AI-native realtime diagnostics

AI agent có thể query:

```text
RealtimeViolation
```

và nhận:

```text
call chain
reason
source span
contract
possible fixes
```

thay vì tự đọc toàn bộ source.

---

# 201.79. DSP numerical profile

Audio DSP thường cần:

```text
f32
```

và có thể chấp nhận:

```text
fast math
```

nhưng phải có profile rõ ràng.

Không tự ý bật global fast-math.

---

# 201.80. Denormals/subnormals

DSP backend có thể có target option:

```text
flush-to-zero
denormal handling
```

nhưng đây là numerical/backend contract.

---

# 201.81. Deterministic DSP

Offline rendering có thể yêu cầu deterministic mode.

Realtime audio có thể ưu tiên throughput/latency.

Hai profile có thể khác nhau nhưng semantics phải được khai báo.

---

# 201.82. Audio allocation invariant

Realtime callback không được phụ thuộc:

```text
GC
heap allocation
unbounded allocator
```

---

# 201.83. Audio effect system

Realtime contract có thể xem các effect:

```text
Allocate
Block
IO
Syscall
Network
Sleep
UnknownForeign
```

Nếu contract cấm effect đó → compile error.

---

# 201.84. Effect analysis reuse

Không tạo một effect checker riêng hoàn toàn.

Sử dụng `EffectInfo` đã có:

```text
Read
Write
Allocate
Drop
Atomic
Volatile
IO
Panic
Synchronize
Foreign
```

và thêm realtime constraints.

---

# 201.85. Realtime contract không thay đổi ownership

Đây là điểm kiến trúc quan trọng:

```text
Realtime
```

chỉ hạn chế behavior.

Nó không tạo:

```text
RealtimeOwnership
```

một hệ thống ownership thứ hai.

---

# 201.86. Media memory domains

Media có thể dùng:

```text
CPU
GPU
DMA
Mapped
External
```

và mọi transfer đều có storage contract.

---

# 201.87. DMA

DMA buffer là external/device storage resource.

Safe API phải mô tả:

```text
alignment
lifetime
ownership
device visibility
synchronization
```

---

# 201.88. Hardware timestamp

Hardware timestamps là external facts.

Không được coi là ordinary pure value nếu đọc từ device.

---

# 201.89. Media FFI

Native APIs:

```text
CoreAudio
WASAPI
ASIO
ALSA
PipeWire
Media Foundation
AVFoundation
V4L2
VideoToolbox
```

được bao bọc qua FFI/platform packages.

Axiom Core không phụ thuộc chúng.

---

# 201.90. Invariants — `AMEDIA`

### `AMEDIA-20`
Audio and media functionality shall remain outside mandatory Core.

### `AMEDIA-21`
Audio buffers shall have explicit sample, channel and layout semantics.

### `AMEDIA-22`
Audio views shall use Axiom capability semantics.

### `AMEDIA-23`
Realtime execution shall be represented by an explicit execution contract.

### `AMEDIA-24`
Realtime code shall reject uncontrolled blocking operations.

### `AMEDIA-25`
Realtime code shall reject unbounded dynamic allocation unless explicitly proven safe by the contract.

### `AMEDIA-26`
Realtime contracts shall reuse Axiom effect analysis.

### `AMEDIA-27`
Realtime contracts shall not introduce a second ownership system.

### `AMEDIA-28`
Audio state shall obey normal Send/Share rules.

### `AMEDIA-29`
Audio communication shall support bounded lock-free/low-latency queues where appropriate.

### `AMEDIA-30`
Audio graph compilation shall permit static scheduling and preallocation.

### `AMEDIA-31`
Audio graph optimization shall preserve stateful DSP semantics.

### `AMEDIA-32`
DSP implementations shall be eligible for SIMD/vectorization.

### `AMEDIA-33`
Audio numerical behavior shall respect the selected floating-point contract.

### `AMEDIA-34`
GPU DSP shall use the established GPU model.

### `AMEDIA-35`
Audio-to-tensor conversion shall not implicitly copy when a valid zero-copy view exists.

### `AMEDIA-36`
AI audio pipelines shall use ordinary tensor/ownership/concurrency semantics.

### `AMEDIA-37`
Media frames shall remain distinct semantic types.

### `AMEDIA-38`
Video frame layout and pixel format shall be explicit.

### `AMEDIA-39`
Hardware media resources shall use explicit external-resource contracts.

### `AMEDIA-40`
Codec implementations shall be replaceable software/hardware/platform backends.

### `AMEDIA-41`
Unused codecs shall not be linked into an application.

### `AMEDIA-42`
Media pipelines shall support bounded buffering and backpressure.

### `AMEDIA-43`
Audio/video synchronization shall use explicit clocks/timestamps.

### `AMEDIA-44`
Media pipeline scheduling shall respect ownership and dependency rules.

### `AMEDIA-45`
Media memory pools shall preserve ownership correctness.

### `AMEDIA-46`
DMA resources shall have explicit lifetime, alignment and synchronization contracts.

### `AMEDIA-47`
Hardware timestamps shall be treated as external/device effects where appropriate.

### `AMEDIA-48`
Media FFI shall remain isolated behind platform/foreign contracts.

### `AMEDIA-49`
Realtime callback execution shall not require a garbage collector.

### `AMEDIA-50`
Realtime callback execution shall not require a monolithic runtime.

### `AMEDIA-51`
Realtime diagnostics shall be queryable through CompilerDB.

### `AMEDIA-52`
AI tooling shall receive structured realtime/media compiler facts.

### `AMEDIA-53`
Audio graph compilation shall preserve deterministic semantics where the selected profile requires them.

### `AMEDIA-54`
Fast numerical modes shall be explicit.

### `AMEDIA-55`
Media optimization shall never weaken memory, ownership or concurrency safety.

### `AMEDIA-56`
Media libraries shall remain removable from programs that do not use them.

---

# Kiến trúc Media cuối cùng

```text
                         AXIOM MEDIA
                              │
              ┌───────────────┼────────────────┐
              │               │                │
            AUDIO           VIDEO            TEXT
              │               │                │
          DSP Graph       Frame Graph       Subtitle
              │               │                │
          Realtime        Decode/Encode       Unicode
              │               │                │
              └───────────────┼────────────────┘
                              │
                         Media Graph
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
                   CPU                 GPU
                    │                   │
                 SIMD/DSP         Compute/Graphics
                    │                   │
                    └─────────┬─────────┘
                              ▼
                       Platform / Codec
```

Đặc biệt, Axiom giờ đã có một đường rất rõ từ:

```text
AudioBuffer
   ↓
Tensor
   ↓
GPU Kernel
   ↓
RenderGraph
   ↓
VideoFrame
```

mà không cần các hệ runtime độc lập chồng chéo lên nhau.

---

# BOOTSTRAP-202 — Networking, Distributed Systems, RPC & High-Performance I/O

**TRẠNG THÁI: NEXT**

Đây là mảng tiếp theo cần khóa để hoàn thiện tầng hệ thống của Axiom.

Phạm vi:

```text
Network
├── TCP
├── UDP
├── QUIC
├── Unix Domain Socket
├── HTTP
├── WebSocket
├── TLS
├── DNS
│
├── Async I/O
├── io_uring
├── IOCP
├── epoll
├── kqueue
│
├── RPC
├── Serialization
├── Zero-copy networking
├── Shared memory
├── Distributed channels
└── Actor-style libraries
```

Nhưng điểm quan trọng nhất sẽ là giải quyết:

> **Axiom async + ownership + zero-copy + OS I/O phải kết hợp thế nào để network server có hiệu năng gần C/C++ nhưng programmer không phải quản lý lifetime buffer thủ công?**

Đồng thời cần chốt:

- `Socket` ownership.
- buffer lifetime qua async I/O.
- kernel/user-space buffer.
- scatter/gather I/O.
- vectored I/O.
- zero-copy send/receive.
- DMA/network buffers.
- cancellation.
- timeout.
- connection state machine.
- backpressure.
- async executor.
- io_uring/IOCP/kqueue/epoll abstraction.
- TLS resource model.
- serialization vs memory representation.
- RPC ABI.
- distributed ownership.
- network failure semantics.
- retry/idempotency.
- connection pooling.
- high-performance server architecture.
- WASM/browser networking.
- kernel/freestanding networking.

Mục tiêu là sau **202–203**, Axiom sẽ có đủ nền tảng cho một server native hiệu năng cao mà vẫn giữ nguyên triết lý:

**ownership rõ ràng + compiler quản lý lifetime + không GC + không borrow-checker bureaucracy + async không ép thread + zero-copy khi có thể.**