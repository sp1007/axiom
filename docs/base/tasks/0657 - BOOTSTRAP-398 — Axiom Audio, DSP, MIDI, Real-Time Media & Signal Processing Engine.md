# BOOTSTRAP-398 — Axiom Audio, DSP, MIDI, Real-Time Media & Signal Processing Engine

Sau **397 — GUI, Windowing, Rendering & Native UI**, bước tiếp theo là **Audio + Digital Signal Processing + Real-Time Media**.

Đây là domain đặc biệt vì nó kiểm tra rất nghiêm khắc các quyết định trước đó của Axiom:

- memory model;
- ownership;
- SIMD;
- parallelism;
- GPU;
- realtime execution;
- zero-copy I/O;
- numerical semantics;
- units;
- async;
- device ownership.

Audio cũng là một trong những lĩnh vực mà **GC, allocation không kiểm soát, hidden locks, hidden copies và jitter** gây vấn đề rõ rệt. Vì vậy nó rất phù hợp để kiểm chứng kiến trúc Axiom.

Nguyên tắc:

> **Audio processing là deterministic numerical/dataflow computation chạy trên time-sensitive execution domain; không phải một hệ thống object/plugin runtime bắt buộc.**

---

# 1. Audio không thuộc Core

Core chỉ cần:

```text
Numeric
Tensor
SIMD
Concurrency
I/O
Memory
Execution Domain
```

Audio nằm phía trên:

```text
Audio
 ├── PCM
 ├── DSP
 ├── Mixer
 ├── MIDI
 ├── Codec
 ├── Device
 └── RealTime
```

---

# 2. Audio Data Model

Không nên chỉ dùng:

```text
Vec<f32>
```

vì audio cần semantic metadata.

Khái niệm:

```text
AudioBuffer<T>
AudioView<T>
AudioMutView<T>
AudioFormat
AudioLayout
AudioChannelLayout
SampleRate
```

---

# 3. Sample

Sample là numeric value:

```text
f32
f64
i16
i24
i32
```

nhưng semantics phụ thuộc audio format.

---

# 4. Sample Rate

Ví dụ:

```text
44.1 kHz
48 kHz
96 kHz
192 kHz
```

nên biểu diễn bằng Units engine:

```text
Quantity<f64, Frequency>
```

hoặc compile-time specialization.

---

# 5. Time

Audio time cần phân biệt:

```text
WallClockTime
AudioSampleTime
DeviceTime
HostTime
```

Audio processing không được dựa vào wall clock để xác định sample position.

---

# 6. Sample Index

```text
SampleIndex
```

là logical discrete time.

Ví dụ:

```text
sample 0
sample 1
sample 2
...
```

---

# 7. Audio Frame

Một audio frame chứa một sample của mỗi channel.

Ví dụ stereo:

```text
Frame {
    left
    right
}
```

---

# 8. Audio Block

Realtime DSP thường xử lý block:

```text
AudioBlock<T, NChannels, NFrames>
```

NFrames có thể static hoặc dynamic.

---

# 9. Channel Layout

Phải phân biệt:

```text
Mono
Stereo
5.1
7.1
Ambisonic
Custom
```

Channel identity không nên chỉ dựa vào array index nếu semantic layout observable.

---

# 10. Interleaved

Ví dụ stereo:

```text
L R L R L R
```

---

# 11. Planar

```text
L L L L
R R R R
```

Cả hai đều có cùng logical semantics.

Data Layout Engine 389 có thể chuyển đổi representation.

---

# 12. Audio Layout Contract

```text
Interleaved
Planar
Blocked
Packed
```

Nếu layout không observable, compiler có thể tự lựa chọn.

---

# 13. Audio View

```text
AudioView<T>
AudioMutView<T>
```

tái sử dụng capability semantics.

Audio callback nhận `AudioMutView` để xử lý in-place.

---

# 14. No Hidden Allocation

Realtime callback contract có thể yêu cầu:

```text
@realtime
fn process(...)
```

và compiler kiểm tra:

```text
no allocation
no blocking
no syscall
no await
no unbounded loop
```

nếu profile yêu cầu.

---

# 15. Realtime Execution Domain

Mở rộng 364:

```text
REALTIME_AUDIO
```

với contract:

```text
bounded
nonblocking
allocation-free
deterministic scheduling assumptions
```

---

# 16. Realtime không có nghĩa tuyệt đối

Compiler không thể đảm bảo toàn bộ OS scheduling.

Do đó cần phân biệt:

```text
RealtimeContract
RealtimeSafe
RealtimeBestEffort
```

và các target guarantees.

---

# 17. Audio Callback

Conceptual:

```text
fn process(
    input: AudioView<f32>,
    output: AudioMutView<f32>
)
```

Compiler có thể lower thành:

```text
pointer + length + channel metadata
```

hoặc flat pointers.

---

# 18. Callback Lifetime

Input/output buffers chỉ valid trong callback contract.

Không được lưu view ra ngoài callback.

---

# 19. Buffer Ownership

Device có thể tạm thời sở hữu buffer.

Tương tự DMA:

```text
CPU
 ↓
AudioDevice
 ↓
CPU
```

ownership transition phải rõ.

---

# 20. Ring Buffer

Audio streaming cần:

```text
SPSC RingBuffer
```

và đôi khi:

```text
MPSC
MPMC
```

nhưng SPSC là primitive quan trọng cho low-latency audio.

---

# 21. Lock-Free

Không nên dùng mutex trong audio callback.

Có thể dùng:

```text
Atomic
SPSC
preallocated queue
```

theo contract.

---

# 22. Lock-Free không đồng nghĩa Wait-Free

Compiler phải phân biệt:

```text
lock-free
wait-free
obstruction-free
```

nếu API công bố guarantee.

---

# 23. Audio Parameter Updates

GUI thread có thể thay đổi:

```text
volume
frequency
filter cutoff
```

audio thread đọc thông qua:

```text
Atomic
snapshot
SPSC message
```

không dùng shared mutable unsynchronized state.

---

# 24. Parameter Smoothing

Thay vì:

```text
volume = new_value
```

có thể cần:

```text
ramp
interpolation
one-pole smoothing
```

để tránh discontinuity.

Đây là DSP semantics.

---

# 25. DSP Function

DSP primitive:

```text
gain
mix
pan
delay
filter
convolution
resample
FFT
```

có thể là pure numeric transformation.

---

# 26. DSP Graph

Audio processing có thể biểu diễn:

```text
Input
 ↓
Gain
 ↓
EQ
 ↓
Compressor
 ↓
Reverb
 ↓
Output
```

---

# 27. Audio Graph IR

Compiler-level:

```text
ADSPIR
```

có thể biểu diễn:

```text
INPUT
OUTPUT
GAIN
MIX
FILTER
DELAY
FFT
IFFT
CONVOLUTION
RESAMPLE
PLUGIN
```

---

# 28. Graph Compilation

Graph:

```text
A → B → C
```

có thể compile thành một flat processing function.

Không cần runtime node object cho static graph.

---

# 29. DSP Fusion

Ví dụ:

```text
gain
→ EQ
→ gain
```

có thể fuse thành một loop nếu semantics cho phép.

---

# 30. Buffer Fusion

Nếu:

```text
A → B
```

B không cần tồn tại riêng:

```text
A
 ↓
in-place
```

có thể loại bỏ intermediate buffer.

---

# 31. DSP Allocation

Static graph:

```text
DSP graph known at compile-time
```

có thể preallocate toàn bộ scratch memory.

---

# 32. Dynamic DSP Graph

Runtime graph vẫn được hỗ trợ:

```text
DynamicAudioGraph
```

nhưng cần allocation/locking policy riêng.

---

# 33. Graph Reconfiguration

Không nên mutate audio graph trực tiếp trong realtime callback.

Mô hình:

```text
Control Thread
      ↓
build new graph
      ↓
publish snapshot
      ↓
Audio Thread switches safely
```

---

# 34. Graph Snapshot

Audio thread có thể sở hữu immutable graph snapshot.

Không cần lock trong processing path.

---

# 35. Double Buffering

Graph/config có thể dùng:

```text
active
pending
```

sau đó atomic swap.

---

# 36. SIMD DSP

DSP rất phù hợp với 366.

Ví dụ:

```text
N samples
 ↓
vec<f32, 8>
 ↓
multiply
 ↓
store
```

---

# 37. Vectorized Filter

Compiler có thể vectorize:

```text
y[i] = a*x[i] + b*y[i-1]
```

nếu dependency structure cho phép.

Nếu recurrence ngăn vectorization, compiler không được phá semantics.

---

# 38. Parallel DSP

Các channel độc lập có thể parallel.

Nhưng không được tạo worker per audio block.

Worker pool nên được tạo trước.

---

# 39. Audio Scheduling

Realtime scheduler phải ưu tiên:

```text
bounded execution
low jitter
predictable memory
```

hơn throughput tổng thể.

---

# 40. Priority

Audio thread có thể yêu cầu realtime priority.

Đây là OS contract từ 396.

---

# 41. CPU Affinity

Audio processing có thể yêu cầu CPU affinity.

Nhưng đây là performance policy, không thay đổi semantics.

---

# 42. NUMA

Large audio/video workloads có thể tận dụng NUMA.

Small realtime buffers thường cần locality.

Compiler cost model có thể chọn placement.

---

# 43. Audio Device

Device:

```text
AudioInputDevice
AudioOutputDevice
AudioDuplexDevice
```

là OS/hardware resource.

---

# 44. Device Capability

Open device trả capability:

```text
AudioDeviceCapability
```

bao gồm:

```text
sample rates
formats
channels
buffer sizes
latency
```

---

# 45. Device Configuration

```text
AudioDeviceConfig {
    sample_rate
    channels
    format
    buffer_size
}
```

---

# 46. Device Clock

Audio device có clock riêng.

Có thể drift so với system clock.

---

# 47. Clock Synchronization

Đối với long-running stream:

```text
device clock
      ↓
resampling / drift correction
      ↓
application clock
```

---

# 48. Latency

Latency cần phân biệt:

```text
input latency
processing latency
output latency
round-trip latency
device latency
```

Không gộp thành một số duy nhất.

---

# 49. Timestamp

Audio buffer có timestamp:

```text
AudioTimestamp {
    sample_position
    device_time
}
```

---

# 50. Dropout

Nếu realtime processing không hoàn thành deadline:

```text
XRUN / Dropout
```

là observable event.

Không nên biến thành silent retry/block.

---

# 51. Deadline

Audio callback:

```text
deadline
```

phải hoàn thành trước deadline theo device contract.

---

# 52. Overrun Policy

Có thể:

```text
silence
repeat_last
drop_block
recover
```

policy phải explicit.

---

# 53. Underflow

Output buffer thiếu dữ liệu là semantic device condition.

Không tự động block realtime callback.

---

# 54. Resampling

Resampling:

```text
44.1kHz
 ↓
48kHz
```

có thể sử dụng:

```text
linear
polyphase
sinc
windowed sinc
```

Algorithm lựa chọn dựa numerical/quality contract.

---

# 55. Resampling Quality

Có thể có:

```text
Fast
HighQuality
LinearPhase
MinimumPhase
```

nhưng mỗi policy phải có semantics rõ ràng.

---

# 56. FFT

373 đã định nghĩa FFT.

Audio chỉ specialize:

```text
FFT(audio block)
```

không tạo FFT engine mới.

---

# 57. Convolution

Có thể sử dụng:

```text
direct convolution
partitioned convolution
FFT convolution
```

Cost model chọn algorithm.

---

# 58. Filters

Library cung cấp:

```text
FIR
IIR
Biquad
StateVariable
Ladder
```

---

# 59. Filter State

Filter state là owning value:

```text
FilterState
```

có thể nằm trên stack/register nếu nhỏ.

---

# 60. DSP State

State không nên là hidden global.

Ví dụ:

```text
struct Biquad {
    z1: f32
    z2: f32
    ...
}
```

method:

```text
process(filter, buffer)
```

phù hợp triết lý struct + function của Axiom.

---

# 61. No Class-Based DSP

Không cần:

```text
class AudioProcessor
class Filter
class Compressor
```

Thay bằng:

```text
trait Processor {
    fn process(self, ...)
}
```

và concrete structs.

---

# 62. Dynamic Plugin

Nếu cần plugin runtime:

```text
dyn AudioProcessor
```

là explicit dynamic dispatch.

Vtable chỉ xuất hiện ở boundary đó.

---

# 63. Plugin ABI

Plugin ABI phải explicit:

```text
create
process
reset
destroy
```

ownership contract phải rõ.

---

# 64. Plugin Memory

Plugin không được tự ý:

```text
free Axiom memory
```

nếu allocator domains khác nhau.

---

# 65. Plugin Realtime Contract

Plugin process callback phải khai báo:

```text
realtime_safe
```

nếu được phép chạy trong realtime thread.

---

# 66. MIDI

MIDI là event stream, không phải audio samples.

Semantic:

```text
MidiEvent
MidiStream
```

---

# 67. MIDI Event

Có thể có:

```text
NoteOn
NoteOff
ControlChange
ProgramChange
PitchBend
Aftertouch
Clock
SysEx
```

---

# 68. MIDI Timing

MIDI event cần:

```text
timestamp
```

có thể theo:

```text
sample position
device time
host monotonic time
```

---

# 69. MIDI → Audio

Pipeline:

```text
MIDI event
 ↓
synth state
 ↓
DSP
 ↓
audio buffer
```

---

# 70. Audio → MIDI

Feature extraction có thể:

```text
pitch detection
onset detection
energy
beat
```

sau đó emit MIDI/events.

---

# 71. Codec

Audio codec nằm library/domain:

```text
PCM
WAV
FLAC
MP3
AAC
Opus
Vorbis
```

Codec implementation không phải Core.

---

# 72. Streaming Codec

Decoder nên hỗ trợ:

```text
input stream
 ↓
decode
 ↓
audio frames
```

không cần load toàn bộ file.

---

# 73. Zero-Copy Decode

Nếu decoder output trực tiếp vào audio buffer:

```text
compressed data
 ↓
decoder
 ↓
AudioBuffer
```

có thể tránh intermediate copy.

---

# 74. Audio File

Audio file metadata:

```text
sample rate
channels
format
duration
codec
layout
```

---

# 75. Metadata

Metadata:

```text
title
artist
album
comment
cover
```

không nên nằm trong audio sample buffer.

---

# 76. Audio + I/O

390 cung cấp:

```text
Stream
Buffer
Async I/O
Zero-copy
```

Audio chỉ chuyên biệt hóa data format.

---

# 77. Audio + GPU

GPU có thể xử lý:

```text
FFT
convolution
spectral processing
large batch DSP
neural audio
```

nhưng không nên mặc định dùng GPU cho low-latency callback.

---

# 78. GPU/Realtime Boundary

Một GPU operation có latency không xác định theo realtime deadline.

Vì vậy:

```text
GPU DSP
```

thường nằm ngoài hard realtime path trừ khi explicit hardware contract.

---

# 79. Neural Audio

ML engine 385 có thể xử lý:

```text
audio tensor
 ↓
neural network
 ↓
audio
```

không cần Audio engine định nghĩa neural network riêng.

---

# 80. Audio Tensor

Audio có thể map thành:

```text
Tensor<f32, [channels, frames]>
```

hoặc:

```text
Tensor<f32, [frames, channels]>
```

với layout contract.

---

# 81. Audio ↔ Tensor

Nếu representation compatible:

```text
AudioView
 ↔
TensorView
```

có thể là zero-copy semantic view.

---

# 82. Audio + Units

Amplitude không đơn giản là physical quantity.

Phải phân biệt:

```text
normalized amplitude
linear amplitude
dBFS
SPL
```

Không cho compiler coi mọi `f32` là cùng physical quantity.

---

# 83. Decibel

dB là logarithmic quantity.

Các operation:

```text
linear → dB
dB → linear
```

phải explicit.

---

# 84. Loudness

Loudness metrics:

```text
LUFS
RMS
Peak
TruePeak
```

là domain semantics.

---

# 85. Numerical Contract

DSP thường cần:

```text
Strict
Fast
Approximate
```

373/368 numerical semantics được tái sử dụng.

---

# 86. Denormal Handling

Audio DSP có thể cần xử lý subnormal values.

Có thể có explicit policy:

```text
FlushToZero
PreserveSubnormal
```

không được compiler âm thầm thay đổi nếu observable.

---

# 87. NaN/Infinity

Audio DSP phải có policy về:

```text
NaN
Inf
```

đặc biệt khi dùng fast math.

---

# 88. Saturation

Audio integer DSP thường cần:

```text
wrap
clamp
saturate
```

Axiom numeric semantics đã phân biệt chúng.

---

# 89. Fixed-Point Audio

Embedded/realtime targets có thể sử dụng:

```text
Q15
Q31
```

library numeric types.

---

# 90. Sample Conversion

Ví dụ:

```text
i16 PCM
 ↓
f32 normalized
```

là numeric conversion có semantics rõ ràng.

---

# 91. Channel Mixing

Downmix:

```text
5.1 → Stereo
```

không phải simple array truncation.

Mix matrix phải explicit.

---

# 92. Spatial Audio

Có thể hỗ trợ:

```text
Binaural
Ambisonics
HRTF
3D panning
```

dựa trên Geometry + Linear Algebra + DSP.

---

# 93. Audio Scene

Spatial audio có thể dùng:

```text
Source
Listener
Position
Orientation
Velocity
```

từ Geometry 379.

---

# 94. Doppler

Doppler effect cần:

```text
velocity
speed of sound
sample rate
```

Units/geometry đảm bảo consistency.

---

# 95. Audio Graph + Parallelism

Independent graph branches:

```text
A ──┐
    ├→ Mix
B ──┘
```

có thể parallel.

---

# 96. Graph Scheduling

Compiler có thể topologically sort:

```text
dependency graph
```

và tạo execution schedule.

---

# 97. Static Schedule

Nếu graph static:

```text
schedule
buffer assignment
scratch memory
```

có thể compile-time.

---

# 98. Dynamic Schedule

Dynamic graph dùng runtime scheduler.

Nhưng realtime path vẫn có thể dùng precomputed schedule sau graph publication.

---

# 99. CompilerDB

Bổ sung:

```text
AudioDB
AudioTypeDB
AudioFormatDB
AudioSampleDB
AudioFrameDB
AudioBlockDB
AudioBufferDB
AudioViewDB
AudioLayoutDB
AudioChannelDB
AudioChannelLayoutDB

SampleRateDB
AudioTimeDB
SampleIndexDB
AudioTimestampDB
AudioClockDB
AudioDeviceClockDB
AudioClockSyncDB

AudioDeviceDB
AudioInputDB
AudioOutputDB
AudioDuplexDB
AudioDeviceConfigDB
AudioDeviceCapabilityDB
AudioDeviceBufferDB
AudioDeviceLatencyDB
AudioDeviceXrunDB

RealtimeDB
RealtimeProfileDB
RealtimeContractDB
RealtimeSafetyDB
RealtimeDeadlineDB
RealtimeAllocationDB
RealtimeBlockingDB
RealtimeSchedulingDB
RealtimeAffinityDB

AudioRingBufferDB
AudioSpscDB
AudioQueueDB
AudioParameterDB
AudioParameterAtomicDB
AudioParameterSmoothingDB

DspDB
DspNodeDB
DspGraphDB
DspGraphNodeDB
DspGraphEdgeDB
DspScheduleDB
DspSnapshotDB
DspStateDB
DspProcessorDB
DspFusionDB
DspBufferDB
DspScratchDB
DspAllocationDB

GainDB
MixDB
PanDB
DelayDB
FilterDB
FirDB
IirDB
BiquadDB
CompressorDB
LimiterDB
GateDB
EqDB
ConvolutionDB
ResamplerDB

AudioFftDB
AudioSpectrumDB
AudioWindowDB
AudioAnalysisDB
PitchDetectionDB
OnsetDetectionDB
BeatDetectionDB
LoudnessDB
RmsDB
PeakDB
TruePeakDB

MidiDB
MidiEventDB
MidiStreamDB
MidiDeviceDB
MidiTimestampDB
MidiRoutingDB

AudioCodecDB
PcmCodecDB
WavDB
FlacDB
Mp3DB
AacDB
OpusDB
VorbisDB
AudioDecoderDB
AudioEncoderDB
AudioStreamingDB
AudioMetadataDB

AudioPluginDB
AudioPluginAbiDB
AudioPluginProcessorDB
AudioPluginRealtimeDB
AudioPluginMemoryDB

SpatialAudioDB
AudioSourceDB
AudioListenerDB
AudioPanningDB
HrtfDB
AmbisonicsDB
BinauralDB
DopplerDB

AudioTensorDB
AudioGpuDB
AudioSimdDB
AudioParallelDB
AudioIoDB
AudioZeroCopyDB

AudioNumericalDB
AudioPrecisionDB
AudioSaturationDB
AudioDenormalDB
AudioNanPolicyDB

AudioSecurityDB
AudioCapabilityDB

AudioCostModelDB
AudioOptimizationDB
AudioVerificationDB
```

---

# 100. MIR

```text id="m9u8j1"
AUDIO_DEVICE_OPEN
AUDIO_DEVICE_CLOSE
AUDIO_DEVICE_START
AUDIO_DEVICE_STOP
AUDIO_DEVICE_CONFIGURE

AUDIO_BUFFER_CREATE
AUDIO_BUFFER_VIEW
AUDIO_BUFFER_MUT_VIEW
AUDIO_BUFFER_REUSE

AUDIO_CALLBACK_BEGIN
AUDIO_CALLBACK_END
AUDIO_DEADLINE_CHECK
AUDIO_XRUN

AUDIO_TIMESTAMP
AUDIO_CLOCK_READ
AUDIO_CLOCK_SYNC

AUDIO_RING_PUSH
AUDIO_RING_POP
AUDIO_RING_PEEK

AUDIO_PARAMETER_LOAD
AUDIO_PARAMETER_STORE
AUDIO_PARAMETER_RAMP

DSP_BEGIN
DSP_END
DSP_NODE
DSP_CONNECT
DSP_SCHEDULE
DSP_PROCESS
DSP_FUSE
DSP_SNAPSHOT
DSP_SWAP

DSP_GAIN
DSP_MIX
DSP_PAN
DSP_DELAY
DSP_FILTER
DSP_CONVOLUTION
DSP_RESAMPLE

DSP_FFT
DSP_IFFT

DSP_ANALYZE
DSP_RMS
DSP_PEAK
DSP_LOUDNESS
DSP_PITCH
DSP_ONSET

MIDI_OPEN
MIDI_CLOSE
MIDI_SEND
MIDI_RECEIVE
MIDI_TIMESTAMP

AUDIO_DECODE
AUDIO_ENCODE
AUDIO_STREAM

AUDIO_PLUGIN_LOAD
AUDIO_PLUGIN_PROCESS
AUDIO_PLUGIN_UNLOAD

AUDIO_GPU_UPLOAD
AUDIO_GPU_PROCESS
AUDIO_GPU_DOWNLOAD

AUDIO_TENSOR_VIEW
AUDIO_TENSOR_MUT_VIEW

AUDIO_CHANNEL_MIX
AUDIO_SPATIALIZE
AUDIO_DOPPLER
```

---

# 101. Proof System

```text id="cnwq80"
AudioFormatProof
AudioLayoutProof
AudioChannelProof
AudioSampleRateProof

AudioBufferOwnershipProof
AudioViewLifetimeProof
AudioDeviceOwnershipProof
AudioDeviceCapabilityProof

RealtimeAllocationProof
RealtimeBlockingProof
RealtimeDeadlineProof
RealtimeSafetyProof
RealtimeAffinityProof

AudioRingBufferProof
AudioSpscProof
AudioParameterRaceProof
AudioParameterVisibilityProof

DspGraphProof
DspGraphDependencyProof
DspScheduleProof
DspSnapshotProof
DspGraphSwapProof

DspBufferLifetimeProof
DspScratchMemoryProof
DspFusionProof
DspAliasProof

DspSimdProof
DspParallelProof
DspNumericalProof
DspSaturationProof
DspDenormalProof

ResamplingProof
ConvolutionProof
FilterStabilityProof
AudioFftProof

MidiOrderingProof
MidiTimestampProof

CodecFormatProof
CodecStreamingProof
CodecBufferProof

AudioPluginAbiProof
AudioPluginOwnershipProof
AudioPluginRealtimeProof

SpatialAudioGeometryProof
SpatialAudioUnitProof

AudioTensorLayoutProof
AudioTensorZeroCopyProof
AudioGpuProof

AudioSecurityProof
AudioCapabilityProof

AudioCostModelProof
AudioOptimizationProof
AudioVerificationProof
```

---

# 102. Invariants

### `AAUDIO-01`
Audio sample semantics phải độc lập với physical buffer representation.

### `AAUDIO-02`
Sample rate phải được xác định trong audio format contract.

### `AAUDIO-03`
Audio time không được đồng nhất với wall-clock time.

### `AAUDIO-04`
Audio buffer ownership phải rõ ràng.

### `AAUDIO-05`
Audio view không được vượt lifetime của buffer/device contract.

### `AAUDIO-06`
Interleaved và planar layout phải có semantic equivalence khi layout không observable.

### `AAUDIO-07`
Channel identity phải được preserve khi channel layout observable.

### `AAUDIO-08`
Realtime callback không được thực hiện operation bị realtime contract cấm.

### `AAUDIO-09`
Realtime callback không được implicit allocation khi profile yêu cầu allocation-free.

### `AAUDIO-10`
Realtime callback không được implicit blocking.

### `AAUDIO-11`
Realtime callback không được implicit await.

### `AAUDIO-12`
Shared parameters giữa control thread và audio thread phải có synchronization semantics.

### `AAUDIO-13`
SPSC queue phải preserve ownership transfer.

### `AAUDIO-14`
Lock-free không được bị compiler/runtime mô tả sai thành wait-free.

### `AAUDIO-15`
Audio graph execution phải tuân thủ dependency ordering.

### `AAUDIO-16`
Graph fusion không được thay đổi numerical/ordering semantics.

### `AAUDIO-17`
Graph snapshot phải bất biến đối với audio thread trong processing interval.

### `AAUDIO-18`
Graph reconfiguration không được invalidate state mà active audio processing còn sử dụng.

### `AAUDIO-19`
Intermediate buffer elimination chỉ được thực hiện khi alias/lifetime proof hợp lệ.

### `AAUDIO-20`
SIMD DSP phải preserve declared numerical contract.

### `AAUDIO-21`
Parallel DSP chỉ được thực hiện khi dependency analysis chứng minh legality.

### `AAUDIO-22`
Resampling phải preserve declared sample-rate conversion semantics.

### `AAUDIO-23`
Filter optimization không được thay đổi declared stability/numerical semantics.

### `AAUDIO-24`
FFT/convolution optimization phải tuân thủ numerical contract.

### `AAUDIO-25`
MIDI event ordering phải được preserve trong ordering scope đã công bố.

### `AAUDIO-26`
Codec streaming không được yêu cầu toàn bộ media nằm trong memory.

### `AAUDIO-27`
Plugin memory ownership không được vượt allocator/ABI boundary.

### `AAUDIO-28`
Spatial audio operations phải preserve coordinate frame và unit semantics.

### `AAUDIO-29`
GPU audio execution không được tự động được coi là hard-realtime-safe.

### `AAUDIO-30`
Chương trình không sử dụng Audio/DSP subsystem không được kéo theo audio runtime bắt buộc.

---

## Điểm quan trọng nhất của 398

Audio làm lộ rõ một ưu điểm của kiến trúc Axiom:

```text
struct state
     ↓
function
     ↓
view
     ↓
SIMD
     ↓
parallel
     ↓
native device
```

Ví dụ một DSP processor có thể về mặt source chỉ là:

```text
struct Gain {
    value: f32
}

fn process(
    self: Gain,
    input: view<f32>,
    output: mut_view<f32>
) {
    ...
}
```

Nhưng compiler có thể biến nó thành:

```text
audio callback
    ↓
raw buffer
    ↓
vector registers
    ↓
SIMD multiply
    ↓
store
```

**không class, không virtual dispatch, không GC, không object header, không hidden allocation.**

Đồng thời nếu graph đủ tĩnh:

```text
Input
 ↓
Gain
 ↓
EQ
 ↓
Compressor
 ↓
Output
```

có thể trở thành **một native processing loop duy nhất** sau DSP graph fusion.

Đó là một phép thử rất mạnh cho triết lý cốt lõi của Axiom:

> **Abstraction có thể rất cao ở source level, nhưng representation cuối cùng có thể thấp đến mức gần với cách một programmer viết assembly tối ưu bằng tay.**