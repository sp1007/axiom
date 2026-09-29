# BOOTSTRAP-461 — AUDIO, DSP, REAL-TIME AUDIO, MIXING, STREAMING & MEDIA PIPELINE FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu: xây audio foundation native, low-latency, deterministic, phù hợp cả ứng dụng thông thường lẫn DAW/game/media/AI audio, nhưng **không đưa audio vào language core hoặc mandatory runtime**.

Kiến trúc:

```text
Axiom Core
    ↓
Numeric / SIMD 458
    ↓
Audio Core
    ├── Audio Device
    ├── Audio Stream
    ├── Audio Buffer
    ├── Format
    ├── Mixer
    ├── DSP
    ├── Spatial Audio
    ├── Codec
    ├── Recording
    └── Media Synchronization
```

---

## 461.1 — Audio architecture

Chia thành:

```text
audio-core
audio-device
audio-buffer
audio-stream
audio-format
audio-mixer
audio-dsp
audio-resampler
audio-spatial
audio-codec
audio-file
audio-record
audio-analysis
audio-sync
audio-debug
```

Không module nào tự động được link.

---

## 461.2 — Audio device

Conceptual:

```text
AudioDevice
AudioDeviceInfo
AudioDeviceId
AudioDeviceCapabilities
```

Device có thể là:

```text
Output
Input
Duplex
Virtual
Network
```

---

## 461.3 — Device discovery

Application có thể enumerate audio devices.

---

## 461.4 — Default device

API có thể lấy system default device nhưng việc dùng default device phải explicit.

---

## 461.5 — Device selection

Có thể chọn device bằng ID.

---

## 461.6 — Device capabilities

Expose:

```text
sample_rates
channel_counts
sample_formats
min_buffer_size
max_buffer_size
exclusive_mode
low_latency
```

---

## 461.7 — Device hot-plug

Device arrival/removal được biểu diễn bằng event.

---

## 461.8 — Device loss

Audio stream phải có trạng thái rõ ràng khi device biến mất.

---

## 461.9 — Reconfiguration

Sample rate/channel/device change phải explicit.

---

## 461.10 — No hidden device switching

Runtime không tự động đổi device giữa các stream nếu API không yêu cầu.

---

# 461.11 — Audio format

Audio format gồm:

```text
sample_format
sample_rate
channels
channel_layout
interleaving
```

---

## 461.12 — Sample formats

Foundation:

```text
i16
i24
i32
f32
f64
```

Backend-specific formats có thể bổ sung.

---

## 461.13 — Real-time canonical format

`f32` được chọn làm canonical internal format mặc định.

---

## 461.14 — Integer conversion

Integer ↔ float conversion explicit.

---

## 461.15 — Sample rate

Sample rate là integer Hz.

---

## 461.16 — Common rates

Ví dụ:

```text
44100
48000
88200
96000
192000
```

nhưng Axiom không hard-code chỉ các giá trị này.

---

## 461.17 — Channel count

Mono/stereo/multichannel được biểu diễn bằng channel count + layout.

---

## 461.18 — Channel layout

Có thể mô tả:

```text
Mono
Stereo
2.1
5.1
7.1
Ambisonic
Custom
```

---

## 461.19 — Interleaved

Samples:

```text
L R L R L R
```

---

## 461.20 — Planar

Samples:

```text
LLLL...
RRRR...
```

---

# 461.21 — Audio buffer

Conceptual:

```text
AudioBuffer<T>
AudioView<T>
```

---

## 461.22 — Buffer ownership

Theo ownership model 423.

---

## 461.23 — Non-owning audio view

Audio processing ưu tiên view thay vì copy.

---

## 461.24 — Frame

Một frame chứa một sample cho mỗi channel.

---

## 461.25 — Frame count

Buffer size tính theo frame, không chỉ byte.

---

## 461.26 — Channel access

API cho phép channel view mà không copy nếu layout phù hợp.

---

## 461.27 — Buffer slicing

Slice/view phải giữ bounds semantics của 445.

---

## 461.28 — Alignment

SIMD audio buffers có thể yêu cầu alignment explicit.

---

## 461.29 — Ring buffer

Lock-free SPSC ring buffer là primitive quan trọng.

---

## 461.30 — MPMC queue

MPMC queue là library-level abstraction khi cần.

---

# 461.31 — Real-time audio thread

Real-time callback có contract đặc biệt:

```text no allocation
no blocking
no filesystem
no network
no arbitrary lock
no panic
no unpredictable syscall
```

---

## 461.32 — `@realtime`

Có thể đánh dấu function:

```text
@realtime
fn process(...)
```

Compiler/tooling kiểm tra effect constraints.

---

## 461.33 — Real-time call graph

446 ghi lại call graph từ realtime function.

---

## 461.34 — Allocation violation

Call tới allocator trong realtime path tạo diagnostic.

---

## 461.35 — Blocking violation

Call `@blocking` từ realtime function tạo diagnostic.

---

## 461.36 — Panic violation

Call potentially-panic operation từ strict realtime path tạo diagnostic.

---

## 461.37 — Dynamic allocation

Dynamic allocation bị cấm trong strict realtime path.

---

## 461.38 — Lock

Mutex/RwLock không được sử dụng trong strict realtime path.

---

## 461.39 — Lock-free communication

Realtime ↔ non-realtime communication dùng lock-free queue/ring buffer hoặc preallocated mailbox.

---

## 461.40 — Priority

Audio callback có thể chạy với OS realtime priority khi platform hỗ trợ.

---

# 461.41 — Audio stream

Stream đại diện continuous audio processing.

States:

```text
Created
Prepared
Running
Stopped
Draining
Error
Closed
```

---

## 461.42 — Output stream

Application supplies audio frames.

---

## 461.43 — Input stream

Application receives microphone/input frames.

---

## 461.44 — Duplex stream

Input/output đồng thời.

---

## 461.45 — Callback mode

Low-level API có realtime callback.

---

## 461.46 — Pull mode

Application can pull frames from stream.

---

## 461.47 — Push mode

Application can push frames to stream.

---

## 461.48 — Async mode

Async stream integrates with 424.

---

## 461.49 — Blocking mode

Explicit and marked `@blocking`.

---

## 461.50 — Stream latency

Latency estimate exposed by device/backend.

---

# 461.51 — Buffer scheduling

Buffer duration determines latency/CPU tradeoff.

---

## 461.52 — Fixed callback size

Backend may provide fixed callback frame count.

---

## 461.53 — Variable callback size

API must support backend variable block size where applicable.

---

## 461.54 — Internal block processing

DSP graph may process fixed-size blocks using buffering.

---

## 461.55 — Underrun

Output underrun is explicit diagnostic/statistic.

---

## 461.56 — Overrun

Input overrun is explicit diagnostic/statistic.

---

## 461.57 — Drop policy

Application chooses drop/recover behavior.

---

## 461.58 — Silence fallback

Optional output silence on underrun.

---

## 461.59 — Recovery

Stream can attempt recovery after device/backend error.

---

## 461.60 — No infinite recovery loop

Recovery must have explicit policy.

---

# 461.61 — Mixer

Mixer combines multiple sources.

Operations:

```text
mix
gain
pan
mute
solo
```

---

## 461.62 — Gain

Gain represented as floating-point scalar.

---

## 461.63 — Volume

User-facing volume may be mapped to gain at higher layer.

---

## 461.64 — Pan

Stereo/multichannel panning is library-level.

---

## 461.65 — Channel routing

Explicit routing matrix:

```text
input channel → output channel
```

---

## 461.66 — Mixing precision

Internal accumulation can use `f32` or `f64`.

---

## 461.67 — Clipping

Mixer must document clipping behavior.

---

## 461.68 — Limiter

Limiter is DSP component, not automatic mixer behavior.

---

## 461.69 — Dithering

Dithering is explicit conversion operation.

---

## 461.70 — No hidden processing

Mixer does not silently normalize/limit/compress unless configured.

---

# 461.71 — DSP architecture

DSP nodes process:

```text
AudioView
```

and return status/control metadata separately.

---

## 461.72 — DSP node

Conceptual:

```text
trait AudioProcessor {
    fn process(self, input: AudioView, output: AudioView)
}
```

---

## 461.73 — In-place processing

Processor may process input/output in place when alias contract permits.

---

## 461.74 — Out-of-place processing

Processor may use separate input/output buffers.

---

## 461.75 — Processing graph

```text
Source
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

---

## 461.76 — DSP graph

Graph is higher-level library abstraction.

---

## 461.77 — Graph compilation

Graph can be compiled into optimized processing schedule.

---

## 461.78 — Graph topological ordering

Dependencies determine execution order.

---

## 461.79 — Graph cycle

Cycles are rejected unless explicit feedback-node semantics exist.

---

## 461.80 — Feedback

Delay-based feedback can create explicit graph cycles.

---

# 461.81 — DSP memory

DSP graph preallocates working memory.

---

## 461.82 — Scratch buffers

Temporary buffers come from preallocated arena/pool.

---

## 461.83 — Realtime scratch allocator

A fixed-capacity bump allocator can be used per callback.

---

## 461.84 — Capacity overflow

Overflow is detected/configured before realtime operation where possible.

---

## 461.85 — No realtime heap

Strict realtime mode never falls back to general heap.

---

## 461.86 — Node state

Persistent DSP state belongs to processor instance.

---

## 461.87 — State ownership

Processor owns its state.

---

## 461.88 — Parameter updates

Control thread communicates parameters through atomic/snapshot mechanism.

---

## 461.89 — Parameter smoothing

Optional smoothing avoids discontinuities.

---

## 461.90 — Lock-free parameter exchange

Realtime-safe parameter updates should use atomics or immutable snapshots.

---

# 461.91 — Standard DSP

Foundation/library implementations:

```text
Gain
Pan
Mix
Delay
Biquad
FIR
IIR
EQ
Compressor
Limiter
Gate
Envelope
Reverb
Chorus
Flanger
Distortion
```

---

## 461.92 — Filter coefficients

Coefficient updates should avoid realtime allocation.

---

## 461.93 — Biquad

Biquad implementation must specify numerical stability expectations.

---

## 461.94 — FIR

SIMD-friendly FIR implementation.

---

## 461.95 — Convolution

Supports direct and FFT convolution.

---

## 461.96 — FFT

Uses numeric/SIMD 458.

---

## 461.97 — STFT

Short-time Fourier transform library component.

---

## 461.98 — Spectrogram

Analysis API.

---

## 461.99 — Window functions

Hann/Hamming/Blackman/etc. as library functions.

---

## 461.100 — FFT plans

Reusable FFT plans can preallocate working memory.

---

# 461.101 — Resampling

Resampler supports:

```text
source_rate
target_rate
channels
quality
```

---

## 461.102 — Resampling algorithms

Possible:

```text
linear
cubic
polyphase
sinc
windowed-sinc
```

---

## 461.103 — Quality modes

Explicit quality/CPU tradeoff.

---

## 461.104 — Streaming resampler

State preserved across blocks.

---

## 461.105 — Realtime resampler

No allocation during process.

---

## 461.106 — Drift correction

Optional clock-drift correction.

---

## 461.107 — Device clock

Input/output clocks may differ.

---

## 461.108 — Synchronization

Long-running streams need explicit drift handling.

---

## 461.109 — Sample-accurate scheduling

Higher-level audio engine may schedule events by sample position.

---

## 461.110 — No wall-clock assumption

Audio sample position and system time remain distinct.

---

# 461.111 — Spatial audio

Spatial layer supports:

```text
listener
source
position
orientation
velocity
```

---

## 461.112 — 3D attenuation

Distance attenuation is library-level.

---

## 461.113 — Panning

Stereo/multichannel panning.

---

## 461.114 — Doppler

Optional.

---

## 461.115 — HRTF

Optional.

---

## 461.116 — Ambisonics

Optional.

---

## 461.117 — Room simulation

Reverb/room acoustics library.

---

## 461.118 — Spatializer

Spatializer consumes mono/multichannel source and produces output layout.

---

## 461.119 — Spatial state

Spatial parameter updates must be realtime-safe.

---

## 461.120 — Audio + graphics

3D audio position may be driven by 3D engine transforms from 460.

---

# 461.121 — Recording

Input recording supports streaming to:

```text
raw PCM
WAV
other codecs through codec layer
```

---

## 461.122 — Recording thread

Input callback remains realtime-safe.

---

## 461.123 — Writer thread

File encoding/writing occurs off realtime thread.

---

## 461.124 — Ring buffer bridge

```text
Microphone
   ↓
Realtime callback
   ↓
RingBuffer
   ↓
Writer/Encoder
   ↓
File
```

---

## 461.125 — Drop policy

If writer cannot keep up, policy is explicit.

---

## 461.126 — Recording metadata

Sample rate/channel/layout/duration metadata preserved.

---

## 461.127 — Timestamp

Captured audio may include device timestamps.

---

## 461.128 — Clock domain

Capture timestamp and system clock may belong to different domains.

---

## 461.129 — Drift

Long recordings can compensate clock drift.

---

## 461.130 — Recording failure

Disk/encoder failure must not block realtime callback.

---

# 461.131 — Audio codecs

Codec layer is separate.

Potential codecs:

```text
PCM
WAV container
FLAC
Opus
MP3
AAC
Vorbis
```

---

## 461.132 — Codec distinction

Codec ≠ container.

---

## 461.133 — Container

Foundation supports conceptually:

```text
WAV
Ogg
MP4/M4A
WebM
custom
```

---

## 461.134 — Decoder interface

```text
AudioDecoder
```

---

## 461.135 — Encoder interface

```text
AudioEncoder
```

---

## 461.136 — Streaming decode

Decoder can produce blocks incrementally.

---

## 461.137 — Streaming encode

Encoder consumes blocks incrementally.

---

## 461.138 — Seek

Codec/container declares whether seek is supported.

---

## 461.139 — Metadata

Tags are separate metadata layer.

---

## 461.140 — Third-party codecs

External codec implementations are optional libraries/providers, not language dependencies.

---

# 461.141 — Audio streaming

Streaming architecture:

```text
Network/File
 ↓
Decoder
 ↓
Ring Buffer
 ↓
Resampler
 ↓
DSP
 ↓
Mixer
 ↓
Device
```

---

## 461.142 — Network streaming

Uses 454.

---

## 461.143 — File streaming

Uses 455.

---

## 461.144 — Async decoder

Decoder can run asynchronously.

---

## 461.145 — Buffering

Application controls buffering policy.

---

## 461.146 — Prebuffer

Streaming player may prebuffer before playback.

---

## 461.147 — Starvation

Buffer starvation generates event/statistic.

---

## 461.148 — Adaptive buffering

Higher-level streaming library may adapt buffer size.

---

## 461.149 — No hidden network thread

Streaming library must expose worker/runtime requirements.

---

## 461.150 — Backpressure

Decoder/network pipeline supports backpressure.

---

# 461.151 — Media synchronization

Audio is primary timing reference in many media applications, but API must not impose universal master clock.

---

## 461.152 — Media clock

Conceptual:

```text
MediaClock
Timestamp
Duration
```

---

## 461.153 — Audio timestamp

Audio frames can carry presentation timestamp.

---

## 461.154 — Video synchronization

Video system from future media task can synchronize to audio clock.

---

## 461.155 — Lip sync

Higher-level application concern.

---

## 461.156 — Clock correction

Can use:

```text
resampling
frame adjustment
clock drift correction
```

---

## 461.157 — No silent time warping

Audio engine does not arbitrarily alter playback rate without explicit synchronization policy.

---

## 461.158 — Seeking

Seek resets decoder/DSP state according to explicit policy.

---

## 461.159 — Flush

Decoder/DSP buffers can be flushed.

---

## 461.160 — End-of-stream

Explicit EOS state.

---

# 461.161 — Audio analysis

Library APIs:

```text
RMS
Peak
LUFS
Spectrum
Pitch
Zero-crossing
Envelope
```

---

## 461.162 — Metering

Meters should be optionally inserted into DSP graph.

---

## 461.163 — Peak detection

Configurable sample/true-peak analysis.

---

## 461.164 — Loudness

LUFS implementation is analysis library, not automatic normalization.

---

## 461.165 — Normalization

Explicit operation.

---

## 461.166 — Pitch

Pitch analysis is not part of audio device layer.

---

## 461.167 — Voice processing

Noise suppression/AGC/echo cancellation can be optional providers.

---

## 461.168 — ML audio

Speech/voice AI uses 458/459 and ecosystem libraries.

---

## 461.169 — Tensor interoperability

Audio blocks can be represented as tensor views without copying where layout permits.

---

## 461.170 — Zero-copy tensor/audio

Ownership and alignment contracts must be satisfied.

---

# 461.171 — SIMD audio

Audio DSP must exploit 458 vector primitives.

---

## 461.172 — SIMD channel processing

Multiple channels/samples can be processed vectorized.

---

## 461.173 — Scalar fallback

Every portable DSP primitive needs scalar fallback.

---

## 461.174 — Runtime dispatch

ISA-specific DSP variants can use 458 CPU feature dispatch.

---

## 461.175 — FMA

DSP filters may use FMA when available.

---

## 461.176 — Denormal handling

DSP runtime can configure handling of subnormal numbers.

---

## 461.177 — Floating-point mode

Realtime DSP must document FP environment assumptions.

---

## 461.178 — Fast math

Fast-math DSP is explicit.

---

## 461.179 — Deterministic DSP

Strict numerical profile available where reproducibility matters.

---

## 461.180 — NaN/Inf

DSP behavior on non-finite input must be documented.

---

# 461.181 — Audio thread synchronization

Preferred communication:

```text
SPSC ring buffer
atomic state
immutable snapshot
lock-free queue
```

---

## 461.182 — Mutex exclusion

Mutex is prohibited in strict realtime processing.

---

## 461.183 — Allocation exclusion

Heap allocation prohibited.

---

## 461.184 — Logging exclusion

General logging is prohibited in strict realtime path.

---

## 461.185 — Debug telemetry

Realtime-safe fixed-size telemetry may be written to preallocated buffer.

---

## 461.186 — Error signaling

Realtime callback should write error state atomically rather than throw/panic.

---

## 461.187 — Deferred error

Non-realtime thread observes error state and handles it.

---

## 461.188 — Callback exception

Exceptions/panic must not escape realtime callback.

---

## 461.189 — Cleanup

Realtime processor resources are pre-established before callback starts.

---

## 461.190 — Reconfiguration

Complex graph/resource reconfiguration occurs off realtime thread.

---

# 461.191 — Graph hot swap

DSP graph can be prepared on control thread and atomically swapped.

---

## 461.192 — Double buffering

Old/new graphs can coexist briefly.

---

## 461.193 — Epoch reclamation

Old graph resources are released after audio callback leaves old epoch.

---

## 461.194 — Deterministic reclamation

No GC required.

---

## 461.195 — Preallocated graph

Graph can be fully allocated before activation.

---

## 461.196 — Graph validation

Cycle/type/channel/rate compatibility validated before activation.

---

## 461.197 — Sample-accurate parameter event

Parameters may be scheduled at sample offset.

---

## 461.198 — Automation

Automation curves are higher-level data structures.

---

## 461.199 — MIDI integration

MIDI event processing can feed audio graph.

---

## 461.200 — MIDI timing

MIDI timestamps must be converted to audio sample time explicitly.

---

# 461.201 — Audio MIDI foundation

MIDI belongs separate but interoperates:

```text
midi-core
midi-device
midi-message
midi-clock
```

---

## 461.202 — MIDI messages

Typed representations rather than raw bytes where convenient.

---

## 461.203 — MIDI raw mode

Raw bytes available for low-level access.

---

## 461.204 — MIDI device

Input/output devices explicit.

---

## 461.205 — MIDI realtime

MIDI realtime messages must not block audio callback.

---

## 461.206 — Event queue

MIDI→audio synchronization uses timestamped event queue.

---

## 461.207 — Audio parameter mapping

MIDI CC can update DSP parameters through lock-free mechanism.

---

## 461.208 — MIDI not mandatory

Audio-only applications need not link MIDI.

---

## 461.209 — Audio graph + MIDI

Higher-level workstation applications can combine both.

---

## 461.210 — Plugin architecture

Audio plugin support is ecosystem-level.

---

# 461.211 — Plugin ABI

Future plugin API can define:

```text
AudioPlugin
AudioPluginDescriptor
AudioProcessor
```

---

## 461.212 — Plugin ownership

Plugin resources follow FFI/ownership 451.

---

## 461.213 — Plugin realtime contract

Plugin processor can declare `@realtime`.

---

## 461.214 — Plugin sandbox

Untrusted plugins should run in process/WASM/OS sandbox.

---

## 461.215 — Plugin ABI stability

Separate from language ABI.

---

## 461.216 — Plugin binary

Native plugin can be static or dynamic library.

---

## 461.217 — Plugin discovery

Dynamic loading is explicit.

---

## 461.218 — Plugin state

State serialization is plugin-defined.

---

## 461.219 — Plugin latency

Plugin reports processing latency.

---

## 461.220 — Plugin tail

Plugin may report tail duration for rendering/export.

---

# 461.221 — Audio backend

Platform implementations may include:

```text
Windows
Linux
macOS
iOS
Android
WASM
```

---

## 461.222 — Native backend

Backend uses OS-native audio APIs.

---

## 461.223 — Cross-platform abstraction

Application sees common `AudioDevice/Stream` API.

---

## 461.224 — Backend capabilities

Capabilities exposed rather than hidden.

---

## 461.225 — Exclusive mode

Backend-specific low-latency mode explicit.

---

## 461.226 — Shared mode

System mixer/shared mode explicit.

---

## 461.227 — WASM

Browser audio integrates with browser audio model.

---

## 461.228 — Mobile

Mobile suspend/resume/device-route changes explicit.

---

## 461.229 — Bluetooth

Bluetooth devices may have changing latency/sample rate.

---

## 461.230 — Device route

Mobile/OS route changes emit events.

---

# 461.231 — Audio file API

Uses 455 storage abstractions.

---

## 461.232 — File decoding

Decoding occurs outside realtime callback.

---

## 461.233 — Memory mapping

Large uncompressed audio may use mmap when beneficial.

---

## 461.234 — Streaming file reader

Avoid loading entire audio files unnecessarily.

---

## 461.235 — Chunking

Audio files can be decoded in blocks.

---

## 461.236 — Metadata preservation

Format metadata is preserved separately from raw samples.

---

## 461.237 — Large-file support

64-bit offsets where target supports them.

---

## 461.238 — Corrupt files

Decoder returns structured error.

---

## 461.239 — Untrusted parser

Codec/container parser follows 445.

---

## 461.240 — Fuzzing

Audio decoders must be fuzz-tested under 435.

---

# 461.241 — Audio memory management

Uses:

```text
system allocator
arena
pool
ring buffer
frame allocator
custom realtime allocator
```

---

## 461.242 — Realtime memory arena

Fixed-capacity.

---

## 461.243 — Audio buffer pool

Reusable fixed-size blocks.

---

## 461.244 — No GC

Audio subsystem cannot depend on GC.

---

## 461.245 — No borrow checker requirement

Realtime API uses ownership/flow semantics from 423.

---

## 461.246 — No hidden allocation

Strict realtime path.

---

## 461.247 — Stack allocation

Small DSP state may use stack.

---

## 461.248 — Heap allocation

Control/setup phase may allocate.

---

## 461.249 — Allocation phase distinction

Setup-time and realtime-time contracts are explicit.

---

## 461.250 — Memory accounting

Audio engine can expose allocation/peak memory statistics.

---

# 461.251 — Error model

Uses 425:

```text Result
Option
panic
abort
```

---

## 461.252 — Device errors

`Result`.

---

## 461.253 — Decode errors

`Result`.

---

## 461.254 — Realtime errors

Atomic/deferred status rather than thrown error.

---

## 461.255 — Invalid DSP graph

Compile/setup-time error.

---

## 461.256 — Buffer mismatch

Compile/setup-time error where possible.

---

## 461.257 — Runtime underrun

Event/statistic.

---

## 461.258 — Device loss

Typed stream error.

---

## 461.259 — Fatal invariant

Only panic/abort for actual program/runtime invariant violations.

---

## 461.260 — No hidden exception

Audio APIs do not silently throw exceptions.

---

# 461.261 — Audio testing

Tests:

```text
format conversion
buffer operations
mixer
DSP
FFT
resampling
device abstraction
recording
codec
streaming
```

---

## 461.262 — DSP reference

Numerically verified reference implementations.

---

## 461.263 — SIMD differential test

SIMD and scalar outputs compared.

---

## 461.264 — Realtime allocation test

Instrument callback and fail if allocation occurs.

---

## 461.265 — Realtime blocking test

Instrument callback and detect blocking operations.

---

## 461.266 — Underrun test

Artificially stress callback.

---

## 461.267 — Ring-buffer stress

Producer/consumer concurrency testing.

---

## 461.268 — Resampler test

Test frequency/phase/error characteristics.

---

## 461.269 — Codec roundtrip

Encode/decode quality and correctness tests.

---

## 461.270 — Corrupt-input fuzzing

Required for parsers/decoders.

---

# 461.271 — Audio benchmarks

Measure separately:

```text
callback CPU time
DSP throughput
latency
jitter
allocation
memory
resampling
codec
streaming
```

---

## 461.272 — Callback deadline

Measure percentage/deadline misses.

---

## 461.273 — Jitter

Record distribution, not merely average.

---

## 461.274 — DSP throughput

Samples/second and CPU cycles/sample.

---

## 461.275 — SIMD speed

Scalar vs ISA-specific implementations measured independently.

---

## 461.276 — Resampler quality

Performance and error are separate metrics.

---

## 461.277 — Codec benchmark

Encode/decode throughput separately.

---

## 461.278 — Startup

Device initialization time separate.

---

## 461.279 — Memory

Peak and steady-state memory separate.

---

## 461.280 — No aggregate audio score

No universal audio-performance score.

---

# 461.281 — AI metadata

446 records:

```text
realtime functions
allocation effects
blocking effects
audio graph
DSP nodes
buffer ownership
device dependencies
codec
latency
sample-rate conversion
```

---

## 461.282 — Realtime call graph

AI can query all functions reachable from callback.

---

## 461.283 — Allocation explanation

Tool can answer where allocation occurs.

---

## 461.284 — Blocking explanation

Tool can answer why a function violates realtime contract.

---

## 461.285 — Graph visualization

DSP graph exported as machine-readable graph.

---

## 461.286 — Audio timeline

Events/parameters can be queried by sample position.

---

## 461.287 — Device diagnostics

AI can query device capabilities/errors.

---

## 461.288 — Performance diagnostics

AI can query callback deadline misses and hotspots.

---

## 461.289 — Codec provenance

Decoder/encoder provider metadata is recorded.

---

## 461.290 — Security metadata

Untrusted decoder/plugin boundaries exposed.

---

# 461.291 — Media interoperability

Audio can exchange:

```text
PCM
AudioBuffer
TensorView
ByteBuffer
```

with explicit layout.

---

## 461.292 — Video synchronization

Future media subsystem can use AudioClock.

---

## 461.293 — Graphics synchronization

460 render timeline can correlate with audio timestamps.

---

## 461.294 — Network synchronization

454 network timestamps can feed streaming playback.

---

## 461.295 — Storage synchronization

455 file timestamps/streaming state integrate with playback.

---

## 461.296 — AI pipeline

Audio chunks can feed speech/audio ML pipelines without mandatory copies.

---

## 461.297 — Zero-copy conditions

Only when representation/alignment/lifetime permit.

---

## 461.298 — Ownership conversion

Tensor/audio view conversion must preserve ownership.

---

## 461.299 — Device audio

Future audio accelerator support can reuse 459.

---

## 461.300 — GPU DSP

FFT/convolution/DSP can run on GPU through 459/460.

---

# 461.301 — GPU audio

Audio engine may dispatch GPU DSP.

---

## 461.302 — Realtime GPU caution

GPU dispatch latency/jitter means GPU cannot automatically be considered suitable for strict realtime callback processing.

---

## 461.303 — Explicit GPU DSP

GPU audio path must be explicitly selected.

---

## 461.304 — Block processing

GPU DSP should operate on sufficiently large batches.

---

## 461.305 — CPU fallback

Portable audio processing must have CPU path.

---

## 461.306 — Device synchronization

GPU audio output must synchronize through 459.

---

## 461.307 — Audio clock

GPU completion timestamps cannot automatically replace audio device clock.

---

## 461.308 — Hybrid DSP

CPU/GPU DSP graphs are possible.

---

## 461.309 — Scheduling

Cross-device scheduling is higher-level.

---

## 461.310 — No hidden accelerator

Ordinary audio DSP remains CPU unless explicitly configured.

---

# 461.311 — Implementation stages

**Stage 1**

```text
AudioFormat
AudioBuffer
AudioDevice
AudioStream
```

---

## 461.312 — Stage 2

Native platform output/input backends.

---

## 461.313 — Stage 3

Ring buffer + realtime callback contract.

---

## 461.314 — Stage 4

Mixer + core DSP.

---

## 461.315 — Stage 5

FFT/resampler/SIMD.

---

## 461.316 — Stage 6

Recording/file/codec.

---

## 461.317 — Stage 7

Streaming + async.

---

## 461.318 — Stage 8

Spatial audio.

---

## 461.319 — Stage 9

Plugin/advanced DSP architecture.

---

## 461.320 — Stage 10

GPU/AI/tensor interoperability.

---

# 461.321 — Hard invariants

1. Audio is not language core.
2. Audio is not mandatory runtime.
3. CPU-only applications do not link audio runtime.
4. Audio resources follow ownership model 423.
5. Audio device lifetime is deterministic.
6. Audio stream lifetime is deterministic.
7. Audio format is explicit.
8. Sample rate is explicit.
9. Channel count is explicit.
10. Channel layout is explicit.
11. Interleaved/planar representation is explicit.
12. `f32` is the canonical internal realtime format unless another format is explicitly selected.
13. Buffer length is represented in frames.
14. Audio views are non-owning.
15. Bounds safety follows 445.
16. Raw audio memory access follows unsafe rules.
17. SIMD audio uses 458.
18. Scalar fallback exists for portable DSP.
19. Realtime callback is a distinct execution contract.
20. Strict realtime code cannot allocate.
21. Strict realtime code cannot block.
22. Strict realtime code cannot perform arbitrary filesystem/network operations.
23. Strict realtime code cannot allow panic/exception escape.
24. Strict realtime code must avoid unpredictable synchronization.
25. Realtime call graph is machine-readable.
26. Realtime violations should be diagnosable statically where possible.
27. Runtime instrumentation can detect remaining violations.
28. Audio callback communication uses realtime-safe mechanisms.
29. Mutex is not permitted in strict realtime path.
30. General logging is not permitted in strict realtime path.
31. Realtime buffers should be preallocated.
32. DSP state must have deterministic lifetime.
33. DSP graph is explicit.
34. DSP graph cycles require explicit feedback semantics.
35. DSP graph validation occurs before realtime activation.
36. Graph reconfiguration occurs outside the realtime callback.
37. Graph hot-swap uses safe epoch/resource reclamation.
38. Mixer does not silently normalize.
39. Mixer does not silently compress/limit.
40. Clipping behavior is documented.
41. Resampling is explicit.
42. Resampling state persists across blocks.
43. Device clock and system clock are distinct.
44. Clock drift must be explicitly handled.
45. Recording separates realtime capture from file encoding.
46. File writes cannot block the realtime callback.
47. Network operations cannot block the realtime callback.
48. Codec operations cannot allocate unpredictably in realtime callback.
49. Decoder input is treated as untrusted.
50. Codec/container parsers are fuzz-tested.
51. Codec and container are separate abstractions.
52. Streaming uses explicit buffering/backpressure.
53. Underrun/overrun are observable.
54. Device loss is observable.
55. Device hot-plug is observable.
56. Device selection is explicit.
57. Backend capabilities are queryable.
58. Platform backends are replaceable.
59. Audio API does not require a particular OS.
60. WASM/mobile/desktop are separate backend targets.
61. Audio APIs do not silently switch devices.
62. Audio errors use `Result` where synchronous failure is expected.
63. Realtime errors use deferred signaling.
64. No hidden exceptions.
65. No mandatory GC.
66. No mandatory borrow checker.
67. No hidden heap allocation.
68. Audio memory pools are optional.
69. Realtime arenas are fixed-capacity.
70. Tensor/audio interoperability preserves layout and ownership.
71. GPU DSP is optional.
72. GPU is not automatically used for realtime audio.
73. CPU fallback remains available.
74. Audio clock remains authoritative where device timing requires it.
75. Spatial audio is a library layer.
76. HRTF is optional.
77. Ambisonics is optional.
78. MIDI is separate from audio core.
79. MIDI/audio synchronization uses explicit timestamps.
80. Plugin ABI is separate from language ABI.
81. Native plugins are external trust boundaries.
82. Untrusted plugins require sandbox/process/WASM isolation.
83. Plugin realtime contracts are explicit.
84. Plugin latency is explicit.
85. Plugin tail behavior is explicit.
86. Audio debug metadata integrates with 440.
87. Audio performance metadata integrates with 450.
88. Audio semantic metadata integrates with 446.
89. Audio FFI integrates with 451.
90. Audio storage integrates with 455.
91. Audio networking integrates with 454.
92. Audio GPU processing integrates with 459/460.
93. Audio numerical operations integrate with 458.
94. Audio compilation remains independent of third-party compiler infrastructure.
95. External codec/device drivers are platform/ecosystem dependencies, not compiler dependencies.
96. Native audio binaries can omit unused subsystems.
97. Headless/offline audio rendering is first-class.
98. Deterministic offline rendering is supported where DSP/backend semantics permit.
99. Realtime performance is measured by latency, jitter and deadline misses rather than a single score.
100. **Axiom audio must make low-latency, allocation-free, predictable realtime processing a first-class capability without imposing realtime constraints on ordinary application code.**

**BOOTSTRAP-461 hoàn tất.**

---

# BOOTSTRAP-462 — MEDIA PIPELINE, VIDEO, CODECS, DEMUX/MUX, TIMELINE, FRAME SYNCHRONIZATION & HARDWARE ACCELERATION

Task tiếp theo được khóa với phạm vi:

```text
Axiom
 ├── 454 Network
 ├── 455 Storage
 ├── 458 Numeric/SIMD
 ├── 459 GPU
 ├── 460 Graphics
 └── 461 Audio
          ↓
     MEDIA FOUNDATION
          ├── Container
          ├── Demux
          ├── Decode
          ├── Encode
          ├── VideoFrame
          ├── AudioFrame
          ├── Timeline
          ├── Clock
          ├── A/V Sync
          ├── Streaming
          ├── Hardware Decode
          ├── Hardware Encode
          └── Media Graph
```

462 sẽ tập trung vào nền tảng để Axiom có thể tự xây **video player, video editor, transcoder, streaming engine, screen recorder và media-processing pipeline**, với các nguyên tắc tương tự audio:

- frame ownership deterministic;
- zero-copy video frames khi có thể;
- CPU/GPU frame interoperability;
- pixel formats/color spaces/HDR;
- demux/decode/encode tách biệt;
- seek/keyframe/reference-frame semantics;
- PTS/DTS/timebase;
- A/V synchronization;
- frame dropping/duplication;
- hardware codec abstraction;
- software codec fallback;
- streaming và backpressure;
- subtitle/caption tracks;
- metadata;
- media graph;
- asynchronous pipeline;
- codec/container plugins;
- fuzzing và security boundary;
- và **không để media runtime/codec/GPU stack bị link vào ứng dụng Axiom không sử dụng media**.