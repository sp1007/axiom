Tiếp tục với **BOOTSTRAP-616**, xây nền tảng media native phía trên Device/Graphics/Storage/Network Runtime, bao phủ audio, video, camera, codec, streaming và media pipeline nhưng vẫn giữ core không phụ thuộc framework bên thứ ba.

:::writing{variant="document" id="74163" title="BOOTSTRAP-616 — Native Audio, Video, Camera, Media Codec, Streaming, Capture & Media Pipeline Runtime 5.0"}
# BOOTSTRAP-616 — Native Audio, Video, Camera, Media Codec, Streaming, Capture & Media Pipeline Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Native Runtime / Media  
**Depends on:** BOOTSTRAP-600 → 615  
**Primary dependencies:** Device 614, Graphics 615, Scheduler 607, Synchronization 608, Resource Governor 606, Security 603, Networking 609, Crypto/TLS 610, Storage 611, Serialization 612, Package/CAS 613, Diagnostics 602, IPC 604, Supervision 605

---

# 1. Purpose

BOOTSTRAP-616 defines the native multimedia foundation of Axiom:

- audio devices;
- audio capture/playback;
- audio clocks;
- PCM formats;
- audio mixing;
- resampling;
- audio buffers;
- microphone input;
- speaker/headphone output;
- camera discovery;
- camera capture;
- video frames;
- pixel formats;
- hardware video acceleration;
- codec abstraction;
- encoded packets;
- demuxing/muxing;
- media timestamps;
- A/V synchronization;
- streaming;
- buffering;
- seeking;
- adaptive media pipelines;
- recording;
- screenshot/screen capture boundary;
- GPU/CPU media interop;
- zero-copy paths;
- media resource management;
- media pipeline scheduling;
- media diagnostics;
- media-device recovery.

The layer is designed to support:

```text
Applications
Games
GUI
Video Players
Audio Players
Recorders
Video Editors
Streaming Applications
Camera Applications
Voice Applications
AI/ML Media Pipelines
Broadcast/Streaming Tools
```

without imposing a high-level player/editor architecture.

---

# 2. Scope Boundary

616 provides primitives.

It does **not** define:

- video editor timelines;
- NLE editing models;
- DAW project formats;
- subtitle systems;
- music sequencers;
- animation systems;
- media player UI;
- streaming-service business logic;
- DRM policy;
- social-media APIs.

Those belong to higher layers.

---

# 3. Architecture

```text
                APPLICATION
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Player       Recorder       Editor
        │            │            │
        └────────────┼────────────┘
                     ▼
              BOOTSTRAP-616
 ┌────────────────────────────────────────┐
 │ Media Source / Sink                    │
 │ Demux / Mux                            │
 │ Codec                                  │
 │ Audio Pipeline                         │
 │ Video Pipeline                         │
 │ Camera Capture                         │
 │ Media Clock                            │
 │ A/V Synchronization                    │
 │ Buffering / Streaming                  │
 │ Frame / Packet Model                   │
 │ Hardware Acceleration                  │
 └───────────────────┬────────────────────┘
                     │
       ┌─────────────┼──────────────┐
       ▼             ▼              ▼
   609 Network    615 Graphics   611 Storage
       │             │              │
       └─────────────┼──────────────┘
                     ▼
                 614 Devices
```

---

# 4. Core Media Objects

Primary structures:

```text
MediaSystem
MediaDevice
AudioDevice
CameraDevice

MediaSource
MediaSink
MediaStream
MediaTrack

MediaPacket
MediaFrame
AudioBuffer
VideoFrame

AudioFormat
VideoFormat
PixelFormat

Codec
Decoder
Encoder

Demuxer
Muxer

MediaClock
MediaTimeline
SyncController

MediaBuffer
BufferPool

MediaPipeline
MediaNode
MediaLink

CaptureSession
PlaybackSession
RecordingSession
```

---

# 5. Media Handle Model

All externally visible media resources use generation-safe handles:

```text
Handle<T>
```

with:

```text
index
generation
device_id
```

No public media API exposes unmanaged native pointers.

---

# 6. Media Time Model

Media time must never use floating-point seconds as the canonical representation.

Canonical representation:

```text
MediaTime {
    ticks: i64
    timescale: u32
}
```

Example:

```text
90000 ticks / second
```

is common for video timing.

---

# 7. Duration

```text
MediaDuration {
    ticks
    timescale
}
```

Supports:

```text
finite
zero
unknown
infinite
```

where appropriate.

---

# 8. Timestamp

```text
MediaTimestamp {
    pts
    dts?
    duration?
}
```

with explicit timebase.

---

# 9. Presentation Timestamp

`PTS` determines when decoded content should be presented.

---

# 10. Decode Timestamp

`DTS` determines decode ordering for codecs that use reordering.

---

# 11. Timestamp Invariant

For encoded streams:

```text
DTS
```

may differ from:

```text
PTS
```

and the runtime must preserve both.

---

# 12. Media Packet

```text
MediaPacket {
    stream_id
    data
    pts
    dts
    duration
    flags
}
```

Flags:

```text
Keyframe
Config
EndOfStream
Discontinuity
Corrupt
Encrypted
```

---

# 13. Media Frame

```text
MediaFrame {
    stream_id
    timestamp
    duration
    format
    data
}
```

A frame may be:

```text
CPU resident
GPU resident
device resident
shared
```

---

# 14. Audio Frame

Audio data includes:

```text
sample_rate
channels
channel_layout
sample_format
frames
timestamp
```

---

# 15. Video Frame

Video data includes:

```text
width
height
pixel_format
color_space
transfer_function
range
timestamp
duration
```

---

# 16. Audio Sample Formats

Core formats:

```text
U8
S16
S24
S32
F32
F64
```

Native processing prefers:

```text
F32
```

where hardware permits.

---

# 17. Audio Channel Layout

Supported logical channels include:

```text
Mono
Stereo
2.1
3.0
4.0
5.1
7.1
7.1.4
```

and arbitrary channel maps.

---

# 18. Audio Sample Rate

Common rates:

```text
8000
16000
22050
24000
32000
44100
48000
88200
96000
192000
```

The runtime must not restrict applications to this list.

---

# 19. Audio Device

```text
AudioDevice {
    id
    direction
    name
    formats
    sample_rates
    channel_layouts
}
```

Directions:

```text
Input
Output
Duplex
```

---

# 20. Audio Device Discovery

```text
AudioDevice.enumerate()
```

must provide stable runtime IDs.

Device names are descriptive, not security identities.

---

# 21. Audio Device Lifecycle

States:

```text
Disconnected
Available
Opening
Running
Paused
Stopping
Lost
Recovering
Closed
```

---

# 22. Audio Output

```text
output = AudioOutput.open(device, format)
```

The API must support low-latency playback.

---

# 23. Audio Input

```text
input = AudioInput.open(device, format)
```

Microphone access requires a BOOTSTRAP-603 capability.

---

# 24. Audio Capture Permission

Permission categories:

```text
audio.capture
audio.playback
```

are separate.

Playback does not imply microphone access.

---

# 25. Audio Buffer

```text
AudioBuffer {
    format
    frame_count
    data
    timestamp
}
```

---

# 26. Audio Ring Buffer

Real-time audio uses bounded ring buffers.

Required properties:

- lock-free or wait-free where practical;
- no heap allocation in callback;
- bounded latency;
- explicit overrun/underrun reporting.

---

# 27. Audio Callback

Low-level output may provide:

```text
AudioCallback
```

The callback must prohibit:

- blocking;
- arbitrary allocation;
- synchronous filesystem I/O;
- synchronous network I/O;
- long-running computation.

---

# 28. Audio Thread

The OS audio callback/thread is treated as a high-priority real-time execution context.

It integrates with BOOTSTRAP-607 but must not use ordinary scheduler queues for every sample block.

---

# 29. Audio Real-Time Rule

The audio path must not depend on:

```text
GC
global mutex
unbounded queue
blocking syscall
network availability
disk availability
```

---

# 30. Audio Mixer

```text
AudioMixer
```

supports:

```text
multiple sources
volume
pan
mute
gain
routing
```

---

# 31. Mixer Graph

A mixer may be represented as:

```text
Source
   ↓
Gain
   ↓
Pan
   ↓
Effect
   ↓
Bus
   ↓
Master
   ↓
Output
```

---

# 32. Audio Processing

Core optional nodes:

```text
Gain
Pan
Mix
ChannelMap
Resample
Delay
Limiter
```

Advanced DSP belongs to higher-level modules.

---

# 33. Audio Resampler

```text
Resampler
```

converts sample rates.

Requirements:

- streaming;
- bounded latency;
- configurable quality;
- no timestamp drift.

---

# 34. Clock-Based Resampling

For A/V synchronization, resampling may continuously compensate small clock differences.

The correction must remain bounded.

---

# 35. Audio Drift

Independent hardware clocks can drift.

The runtime exposes:

```text
ClockOffset
ClockRateError
```

rather than assuming exact synchronization.

---

# 36. Audio Volume

Volume is represented linearly internally.

Optional decibel APIs convert to/from linear gain.

---

# 37. Clipping

The mixer may optionally provide a limiter.

Clipping behavior must be explicit.

---

# 38. Audio Device Loss

When an audio device disappears:

```text
DeviceLost
```

is emitted.

The pipeline can:

```text
pause
reconnect
switch device
terminate
```

according to application policy.

---

# 39. Audio Output Latency

Runtime exposes:

```text
buffer_latency
device_latency
estimated_output_latency
```

where available.

---

# 40. Exclusive/Shared Audio

Backend may expose:

```text
Shared
Exclusive
```

modes.

Exclusive mode requires explicit application request.

---

# 41. Audio Backend Abstraction

Possible backends:

```text
Windows:
WASAPI

Linux:
ALSA
PipeWire
PulseAudio compatibility

macOS/iOS:
Core Audio

Android:
AAudio
OpenSL ES compatibility

WASM:
Web Audio

Embedded:
I2S / vendor audio
```

The public API remains backend-independent.

---

# 42. Video Pixel Formats

Core formats include:

```text
RGBA8
BGRA8
RGB10A2
RGBA16F

Y8
Y16
NV12
P010
P016
I420
YV12
YUV444
```

Capability-dependent formats may be added.

---

# 43. Video Color Model

Video frames explicitly describe:

```text
primaries
transfer
matrix
range
```

Typical matrices:

```text
BT.601
BT.709
BT.2020
```

---

# 44. Video Range

```text
Full
Limited
```

must never be guessed from pixel format alone.

---

# 45. Video Frame Orientation

Camera/video frames may specify:

```text
rotation
mirror
display_orientation
```

without physically transforming pixels.

---

# 46. Video Frame GPU Interop

A decoded video frame may be:

```text
CPUFrame
GpuTexture
ExternalTexture
SharedTexture
```

---

# 47. Zero-Copy Video

Preferred path:

```text
Decoder
   ↓
GPU/Device Surface
   ↓
Graphics 615
   ↓
Display
```

instead of:

```text
Decoder
   ↓
CPU copy
   ↓
GPU upload
```

when hardware supports zero-copy.

---

# 48. Video Device

```text
VideoDevice
```

represents hardware decoding/encoding capabilities.

---

# 49. Codec Model

Codec abstraction:

```text
Codec
Decoder
Encoder
CodecConfig
CodecCapabilities
```

---

# 50. Codec Identification

Codecs use stable IDs:

```text
H264
HEVC
AV1
VP8
VP9
MPEG2
AAC
Opus
Vorbis
FLAC
PCM
```

The list is extensible.

---

# 51. Codec Availability

A codec may be:

```text
Software
Hardware
SystemProvided
External
Unavailable
```

---

# 52. No Mandatory Codec Dependency

The Axiom core runtime does not require FFmpeg, GStreamer, or another third-party media framework.

They may be used as optional external adapters.

---

# 53. Native Codec Provider

```text
CodecProvider
```

can expose:

```text
NativeProvider
PlatformProvider
HardwareProvider
ExternalProvider
TestProvider
```

---

# 54. Decoder

```text
decoder = Codec.open_decoder(codec, config)
```

Operations:

```text
send(packet)
receive()
flush()
reset()
```

---

# 55. Encoder

```text
encoder = Codec.open_encoder(codec, config)
```

Operations:

```text
send(frame)
receive()
flush()
reset()
```

---

# 56. Codec Backpressure

`send()` and `receive()` are nonblocking where possible.

The decoder may return:

```text
NeedMoreInput
NeedOutputConsumption
```

rather than allocating unbounded internal memory.

---

# 57. Decoder Reordering

The decoder must preserve:

```text
DTS
PTS
```

and return frames in presentation order.

---

# 58. Codec Configuration

Configuration contains:

```text
profile
level
bitrate
frame_rate
resolution
pixel_format
keyframe_interval
quality
latency_mode
```

---

# 59. Bitrate Control

Modes:

```text
ConstantBitrate
VariableBitrate
ConstantQuality
Lossless
```

where codec supports them.

---

# 60. Keyframes

Encoders expose:

```text
force_keyframe()
```

when supported.

---

# 61. GOP

Encoding configuration can define:

```text
gop_length
b_frame_count
reference_frame_count
```

subject to codec capability.

---

# 62. Hardware Encoding

Hardware encoders expose:

```text
HardwareCodecCapability
```

including:

```text
max_resolution
profiles
pixel_formats
rate_control
10bit
HDR
```

---

# 63. Hardware Decoding

Hardware decoding can output:

```text
GpuVideoFrame
```

directly.

---

# 64. Media Surface

A hardware decoder may target a GPU-backed surface:

```text
VideoSurface
```

which integrates with BOOTSTRAP-615.

---

# 65. Camera Model

```text
CameraDevice
CameraSession
CameraStream
```

---

# 66. Camera Discovery

```text
CameraDevice.enumerate()
```

returns:

```text
id
name
facing
capabilities
formats
```

---

# 67. Camera Facing

```text
Front
Back
External
Unknown
```

---

# 68. Camera Capability

Camera capabilities include:

```text
resolution
frame_rate
pixel_format
focus
exposure
white_balance
zoom
HDR
stabilization
depth
```

---

# 69. Camera Permission

Camera access requires:

```text
camera.capture
```

capability.

---

# 70. Camera Session

```text
session = camera.open({
    format,
    resolution,
    frame_rate
})
```

---

# 71. Camera Stream

A camera can expose multiple streams:

```text
Color
Depth
Infrared
Metadata
Motion
```

where supported.

---

# 72. Camera Controls

Controls are represented as typed properties:

```text
Exposure
Gain
Focus
WhiteBalance
Zoom
FrameRate
Torch
```

---

# 73. Camera Control Capability

Each control exposes:

```text
supported
range
step
current
automatic_mode
```

---

# 74. Auto Controls

Supported automatic modes:

```text
Auto
ContinuousAuto
Manual
```

depending on device.

---

# 75. Camera Timestamp

Frames should use device timestamps where available.

The runtime records clock domain:

```text
DeviceClock
SystemClock
MediaClock
```

---

# 76. Camera Frame Synchronization

Multi-camera systems may expose:

```text
HardwareSynchronized
SoftwareSynchronized
Unsynchronized
```

status.

---

# 77. Camera Hot Plug

USB/external cameras may appear/disappear at runtime.

The session receives:

```text
DeviceLost
```

without crashing the application.

---

# 78. Camera Preview

Preview can use:

```text
CameraFrame
   ↓
Graphics Texture
   ↓
615 Render Pipeline
```

with zero-copy where possible.

---

# 79. Camera Recording

Camera frames can feed:

```text
CaptureSession
   ↓
Encoder
   ↓
Muxer
   ↓
Storage
```

---

# 80. Screen Capture

Screen capture is separate from ordinary graphics rendering.

It requires an explicit security capability.

```text
ScreenCaptureSession
```

---

# 81. Screen Capture Sources

Possible sources:

```text
Display
Window
ApplicationSurface
GraphicsTexture
```

depending on OS capability.

---

# 82. Screen Capture Security

A normal graphics surface cannot automatically capture arbitrary applications.

OS privacy controls remain authoritative.

---

# 83. Media Source

```text
MediaSource
```

can represent:

```text
File
Memory
Network
Camera
Microphone
Screen
Pipe
Generated
```

---

# 84. Media Sink

```text
MediaSink
```

can represent:

```text
File
Network
AudioDevice
VideoDevice
GraphicsSurface
Memory
Encoder
```

---

# 85. Stream

```text
MediaStream {
    id
    type
    codec
    format
    timebase
}
```

Types:

```text
Audio
Video
SubtitleData
Metadata
Auxiliary
```

---

# 86. Track

A track groups logical media content.

Example:

```text
Track 0: video
Track 1: English audio
Track 2: Vietnamese audio
Track 3: subtitles
```

---

# 87. Demuxer

```text
demuxer = Media.open_demuxer(source)
```

provides:

```text
streams()
read_packet()
seek()
```

---

# 88. Muxer

```text
muxer = Media.open_muxer(sink, format)
```

provides:

```text
add_stream()
write_packet()
write_header()
write_trailer()
```

---

# 89. Container Formats

Compatibility boundary may support:

```text
MP4
MOV
MKV
WebM
AVI
WAV
AIFF
FLAC
Ogg
MPEG-TS
```

Availability is provider-dependent.

---

# 90. Native Container Layer

Axiom may define its own deterministic media container:

```text
AXMF
```

for internal/native use.

It is not intended to replace universal interchange formats.

---

# 91. AXMF

AXMF contains:

```text
header
stream table
metadata
packet index
chunk table
media chunks
optional integrity data
```

---

# 92. AXMF Goals

AXMF should support:

- deterministic writing;
- random access;
- streaming;
- crash recovery;
- chunk-level integrity;
- multiple audio/video streams;
- metadata;
- content hashes.

---

# 93. Streaming Source

Network streams integrate with BOOTSTRAP-609.

```text
Network
   ↓
MediaSource
   ↓
Demuxer
```

---

# 94. Streaming Protocol Boundary

Core streaming adapters may support:

```text
HTTP
HTTPS
WebSocket
RTP/RTSP
```

with additional protocols as optional modules.

---

# 95. HTTP Streaming

The media layer uses BOOTSTRAP-609 for:

- DNS;
- sockets;
- TLS;
- connection pooling;
- HTTP transport.

It does not implement another networking stack.

---

# 96. Progressive Download

A source can expose:

```text
known_size
available_range
downloaded_range
```

---

# 97. Byte-Range Requests

Media sources can request:

```text
read_range(offset, size)
```

for seekable HTTP resources.

---

# 98. Adaptive Streaming Boundary

Optional adaptive stream controller supports:

```text
Representation
BandwidthEstimate
BufferLevel
QualityLevel
```

---

# 99. Adaptive Bitrate

Selection may consider:

```text
network throughput
buffer duration
decode capability
device power
resolution
```

The policy is configurable.

---

# 100. Buffering

Media buffering is bounded.

Core states:

```text
Empty
Buffering
Ready
Playing
Stalled
Seeking
Ended
Failed
```

---

# 101. Buffer Policy

Applications configure:

```text
min_buffer
target_buffer
max_buffer
```

---

# 102. Memory Bound

The media runtime must never allow an unbounded packet/frame buffer.

Resource limits integrate with BOOTSTRAP-606.

---

# 103. Backpressure

Every pipeline edge can report:

```text
Ready
Full
Blocked
Closed
Failed
```

---

# 104. Media Pipeline

```text
MediaPipeline
```

is a directed graph:

```text
Source
 ↓
Demux
 ↓
Decode
 ↓
Transform
 ↓
Synchronize
 ↓
Sink
```

---

# 105. Pipeline Node

```text
MediaNode {
    input_ports
    output_ports
    format_constraints
    process()
}
```

---

# 106. Pipeline Link

A link defines:

```text
source
destination
media_type
format
capacity
```

---

# 107. Pipeline Negotiation

When nodes connect, the runtime negotiates:

```text
format
sample_rate
resolution
pixel_format
timebase
memory_domain
```

---

# 108. Format Conversion

Explicit conversion nodes:

```text
AudioResampler
AudioChannelMapper
VideoScaler
PixelConverter
ColorConverter
FrameRateConverter
```

---

# 109. No Implicit Expensive Conversion

The runtime must not silently insert expensive conversion operations without reporting them.

---

# 110. Zero-Copy Pipeline

Pipeline negotiation should prefer:

```text
GPU → GPU
Device → Device
Shared → Shared
```

over CPU copies.

---

# 111. CPU/GPU Boundary

Explicit memory domains:

```text
CPU
GPU
Shared
Device
```

---

# 112. GPU Video Processing

Video frames can pass through BOOTSTRAP-615 compute/render pipelines.

Examples:

```text
decode
 ↓
GPU texture
 ↓
shader processing
 ↓
encoder
```

where supported.

---

# 113. Media Fence

Media operations use synchronization primitives compatible with 608 and 615.

---

# 114. Frame Ownership

A frame may be owned by:

```text
Producer
Pipeline
Consumer
GPU
```

Only one active owner at a time unless explicitly shared.

---

# 115. Reference Lifetime

Frame references may remain valid until all consumers release them.

No tracing GC is required.

---

# 116. Frame Pool

Reusable frame pools:

```text
VideoFramePool
AudioBufferPool
PacketPool
```

reduce allocation.

---

# 117. Packet Pool

Packet buffers may use slabs from the resource governor.

---

# 118. Packet Zero Copy

Demuxers should expose packet memory without copying when container parsing permits.

---

# 119. Frame Zero Copy

Decoders should expose device-native frames directly where possible.

---

# 120. Media Clock

```text
MediaClock
```

supports:

```text
now()
rate()
pause()
resume()
seek()
```

---

# 121. Clock Sources

Possible sources:

```text
SystemMonotonic
AudioDevice
VideoDevice
ExternalReference
NetworkClock
```

---

# 122. Master Clock

Playback selects one master:

```text
AudioMaster
VideoMaster
ExternalMaster
SystemMaster
```

---

# 123. A/V Synchronization

The sync controller calculates:

```text
audio_time
video_time
master_time
drift
```

---

# 124. Video Sync

If video is early:

```text
delay/drop policy
```

If video is late:

```text
drop/duplicate policy
```

The policy is configurable.

---

# 125. Audio Sync

Audio is usually preferred for continuous playback because dropping arbitrary audio samples is perceptually disruptive.

Small drift may be corrected by resampling.

---

# 126. Sync Thresholds

Configuration:

```text
soft_sync_threshold
hard_sync_threshold
max_audio_correction
max_video_drop
```

---

# 127. Discontinuity

Seeking, network reconnection, device restart, or stream switch can produce:

```text
TimestampDiscontinuity
```

The sync controller resets its local prediction state.

---

# 128. Seeking

```text
pipeline.seek(time)
```

supports:

```text
Exact
NearestKeyframe
Fast
Accurate
```

---

# 129. Seek Sequence

```text
Pause
 ↓
Flush decoder
 ↓
Seek source
 ↓
Discard stale packets
 ↓
Decode from keyframe
 ↓
Restore synchronization
 ↓
Resume
```

---

# 130. Reverse Playback

Reverse playback is not mandatory in core.

A higher-level engine can implement it using forward decode windows.

---

# 131. Trick Play

Optional:

```text
0.5x
1x
1.5x
2x
4x
```

with codec/backend constraints.

---

# 132. Variable Frame Rate

The runtime must support variable frame duration.

It must not assume:

```text
1 / FPS
```

for every frame.

---

# 133. Constant Frame Rate

CFR streams remain supported.

---

# 134. Audio/Video End of Stream

EOS is explicit for every stream.

The pipeline may finish only after all connected streams drain.

---

# 135. Flush

Flush semantics:

```text
discard queued decode state
preserve configuration
```

---

# 136. Reset

Reset semantics:

```text
discard pipeline state
retain node configuration
```

---

# 137. Media Pipeline Errors

Errors are typed:

```text
SourceError
DemuxError
DecodeError
EncodeError
FormatError
DeviceError
NetworkError
StorageError
SyncError
PermissionError
ResourceLimit
```

---

# 138. Corrupt Media

A decoder may report recoverable corruption.

The pipeline can continue where the codec/container permits.

---

# 139. Strict Mode

Strict mode stops on malformed media.

---

# 140. Tolerant Mode

Tolerant mode may skip recoverable corrupt packets.

The skipped region is reported diagnostically.

---

# 141. DRM Boundary

DRM is not implemented by the core media layer.

A secure media provider may integrate with platform DRM APIs.

---

# 142. Protected Decode

Protected video surfaces may be represented as:

```text
ProtectedVideoFrame
```

with restricted CPU mapping/capture.

---

# 143. Secure Media Capability

Required capability:

```text
media.protected
```

---

# 144. Media Encryption

Encrypted media packets can carry:

```text
encryption_scheme
key_id
iv
subsamples
```

The actual key acquisition belongs to a secure provider.

---

# 145. Crypto Integration

BOOTSTRAP-610 provides:

- secure key storage;
- cryptographic primitives;
- TLS;
- key validation.

616 must not duplicate them.

---

# 146. Subtitle/Timed Metadata Boundary

616 transports timed data:

```text
TimedMetadata
```

but does not implement subtitle styling/layout.

---

# 147. Subtitle Stream

A subtitle track may be represented as packets:

```text
MediaPacket<SubtitleData>
```

Higher-level text systems render it.

---

# 148. Metadata

Media metadata can include:

```text
title
artist
album
language
creation_time
camera_model
location
orientation
encoder
```

Sensitive metadata requires policy-aware handling.

---

# 149. Metadata Privacy

Camera location/GPS metadata must not automatically propagate to network sinks.

Applications must explicitly choose export policy.

---

# 150. Media Permissions

Capabilities include:

```text
media.audio.capture
media.audio.playback
media.camera.capture
media.screen.capture
media.protected
media.device.enumerate
```

---

# 151. Device Selection

Applications may choose devices by:

```text
id
name
capabilities
preferred
default
policy
```

The runtime does not silently grant additional capabilities.

---

# 152. Hot Plug

Device events:

```text
Added
Removed
Changed
DefaultChanged
```

---

# 153. Default Device

Default device selection is OS-controlled unless the application explicitly selects another device.

---

# 154. Device Recovery

Recovery may:

```text
reopen
reconfigure
reconnect
fallback
stop
```

depending on policy.

---

# 155. Resource Quotas

BOOTSTRAP-606 accounts:

```text
decoded_frames
encoded_frames
audio_buffers
packet_memory
codec_instances
camera_streams
capture_sessions
encoder_sessions
decoder_sessions
```

---

# 156. CPU Budget

Codec processing consumes CPU budget.

Software codecs cannot bypass Resource Governor limits.

---

# 157. GPU Budget

Hardware video processing consumes GPU/device budgets.

---

# 158. Network Budget

Streaming consumes:

```text
bandwidth
connections
socket buffers
```

through 606/609.

---

# 159. Storage Budget

Recording consumes:

```text
disk bytes
IOPS
write bandwidth
file handles
```

through 606/611.

---

# 160. Recording Pipeline

Typical path:

```text
Camera/Microphone
       ↓
Capture
       ↓
Timestamp
       ↓
Encode
       ↓
Mux
       ↓
Storage
```

---

# 161. Live Streaming Pipeline

```text
Camera/Mic
    ↓
Capture
    ↓
Encode
    ↓
Packetize
    ↓
Network
```

---

# 162. Playback Pipeline

```text
Network/File
    ↓
Demux
    ↓
Decode
    ↓
Sync
    ↓
Audio Output / Graphics Surface
```

---

# 163. Screen Recording

```text
Graphics Surface
       ↓
Capture
       ↓
Color Conversion
       ↓
Encoder
       ↓
Muxer
```

---

# 164. Audio Recording

```text
Microphone
   ↓
AudioInput
   ↓
Optional DSP
   ↓
Encoder
   ↓
Muxer/File
```

---

# 165. Media Transcoding

A generic pipeline can connect:

```text
Decoder → Transform → Encoder
```

without storing the entire media file.

---

# 166. Streaming Transcoding

The same pipeline can operate incrementally.

Memory remains bounded.

---

# 167. Chunked Media

Large media files can be processed as bounded chunks.

No requirement to load an entire file into memory.

---

# 168. Cache

Media caches integrate with BOOTSTRAP-613 CAS.

Cached content may use:

```text
content_hash
stream_id
range
codec
format
```

---

# 169. Cache Validation

Cache entries must validate:

```text
content hash
media format
decoder compatibility
```

before reuse.

---

# 170. Media Package

AXPK can package:

```text
video
audio
textures
thumbnails
subtitles
metadata
codec variants
```

---

# 171. Resource URI

Logical resource identifiers:

```text
media://package/video/main
media://package/audio/vi
media://package/audio/en
```

---

# 172. Localization

A media package can contain:

```text
audio/en
audio/vi
audio/ja
subtitles/en
subtitles/vi
```

with deterministic fallback rules.

---

# 173. Audio Language Selection

Selection order can be configured:

```text
requested language
application language
default track
first compatible track
```

---

# 174. Video Track Selection

Multiple video representations may be selected based on:

```text
resolution
codec
device capability
bandwidth
power
policy
```

---

# 175. Audio Track Switching

Switching may occur at a synchronization boundary.

The runtime must avoid audible discontinuity where possible.

---

# 176. Stream Switching

Adaptive video switching should prefer keyframe-aligned boundaries.

---

# 177. Buffer Memory Domains

Media buffers identify:

```text
CPU
GPU
Shared
Device
```

to prevent accidental copies.

---

# 178. Buffer Mapping

Mapping device-only media surfaces to CPU must fail if unsupported or forbidden.

---

# 179. Media-to-Graphics Bridge

```text
VideoFrame.to_texture(device)
```

may:

- import native surface;
- share external memory;
- copy;
- fail.

The result reports which path was selected.

---

# 180. Graphics-to-Media Bridge

```text
Texture.to_video_frame()
```

supports encoder-compatible surfaces where the backend permits.

---

# 181. Hardware Fence Bridge

Native synchronization objects may be imported/exported between 615 and 616.

---

# 182. Audio Clock Bridge

Audio device clock can become the master media clock.

---

# 183. Camera Clock Bridge

Camera timestamps can be translated to system/media time.

---

# 184. Network Clock

Streaming applications may use an external network clock through a higher-level synchronization service.

---

# 185. Clock Conversion

Clock conversion requires explicit mapping:

```text
source_clock
destination_clock
offset
rate
uncertainty
```

---

# 186. Clock Drift

The runtime periodically estimates drift.

No assumption of perfect clock equality is allowed.

---

# 187. Media Scheduler

616 uses BOOTSTRAP-607 for:

```text
decode tasks
encode tasks
demux tasks
mux tasks
network refill
disk writes
```

Real-time audio callbacks remain specialized.

---

# 188. Priority

Real-time media tasks may request priority through 606/607.

They cannot bypass resource/security policies.

---

# 189. Blocking Isolation

Blocking codec/provider operations run in dedicated worker pools.

They must not block the async reactor.

---

# 190. Backpressure Propagation

If a sink is blocked:

```text
Sink
 ↑
Transform
 ↑
Decoder
 ↑
Source
```

backpressure propagates toward the source.

---

# 191. Drop Policy

Video pipelines may explicitly configure:

```text
DropOldest
DropNewest
DropNonKeyframes
Block
Fail
```

Audio generally defaults to blocking or bounded overflow handling rather than arbitrary dropping.

---

# 192. Latency Profiles

Built-in profiles:

```text
UltraLowLatency
LowLatency
Balanced
Quality
Offline
```

---

# 193. Offline Profile

Offline processing may prioritize:

```text
quality
compression
determinism
throughput
```

over latency.

---

# 194. Live Profile

Live processing prioritizes:

```text
bounded latency
bounded buffering
recovery
continuous output
```

---

# 195. Deterministic Media

For testing/offline rendering:

```text
DeterministicMedia
```

can use:

- fixed clocks;
- deterministic software codecs;
- deterministic resampling;
- deterministic packet ordering.

---

# 196. Media Diagnostics

Metrics include:

```text
decode_fps
encode_fps
dropped_frames
decoded_frames
buffer_level
buffer_underruns
audio_underruns
audio_overruns
network_jitter
decode_latency
encode_latency
pipeline_latency
clock_drift
```

---

# 197. Frame Drop Diagnostics

Every dropped frame should record a reason category:

```text
Late
Backpressure
ResourceLimit
DecodeError
Policy
DeviceLoss
```

---

# 198. Audio Underrun Diagnostics

Audio underruns emit stable events:

```text
MEDIA_AUDIO_UNDERRUN
```

with bounded diagnostic information.

---

# 199. Capture Diagnostics

Capture failures report:

```text
permission
device
format
resource
OS restriction
```

without leaking private metadata.

---

# 200. Codec Diagnostics

Codec errors contain:

```text
codec
profile
backend
error code
stream
timestamp
```

---

# 201. Pipeline Visualization

Debug tooling may export a graph:

```text
source → demux → decode → transform → sync → sink
```

as deterministic metadata.

---

# 202. AI-Readable Media Metadata

`.axmedia` can contain:

```text
streams
codecs
formats
duration
timebase
dependencies
pipeline graph
resource requirements
```

---

# 203. Compiler Metadata

Compiler may emit:

```text
@media_codec
@media_format
@media_realtime
@media_device
@media_capability
```

metadata.

---

# 204. Static Validation

The compiler/toolchain can validate:

- incompatible media formats;
- impossible codec targets;
- missing hardware capabilities;
- invalid pipeline connections.

---

# 205. Dead Stripping

A pure audio application must not link:

```text
camera
video decoder
GPU media backend
screen capture
```

unless referenced.

---

# 206. No Mandatory Media Framework

The native core must remain independently buildable.

External integrations are adapters.

---

# 207. Platform Providers

Provider architecture:

```text
MediaProvider
 ├── NativeProvider
 ├── PlatformProvider
 ├── HardwareProvider
 ├── ExternalProvider
 └── TestProvider
```

---

# 208. Windows Provider

Possible technologies:

```text
WASAPI
Media Foundation
Windows Camera APIs
DXVA
D3D11/D3D12 video surfaces
```

---

# 209. Linux Provider

Possible technologies:

```text
ALSA
PipeWire
V4L2
VA-API
Vulkan video
```

---

# 210. macOS Provider

Possible technologies:

```text
Core Audio
AVFoundation
VideoToolbox
CoreMedia
Metal
```

---

# 211. iOS Provider

Possible technologies:

```text
AVFoundation
Core Media
VideoToolbox
Core Audio
Metal
```

---

# 212. Android Provider

Possible technologies:

```text
AAudio
Camera2
MediaCodec
MediaExtractor
MediaMuxer
Vulkan
```

---

# 213. WASM Provider

Possible technologies:

```text
Web Audio
MediaDevices
MediaStream
WebCodecs
WebGPU
Canvas
```

subject to browser support.

---

# 214. Embedded Provider

Possible:

```text
I2S
V4L2
DMA
vendor codecs
framebuffer
hardware codec
```

---

# 215. External Provider

External media frameworks may be wrapped through FFI.

They cannot become hidden mandatory dependencies of Axiom core.

---

# 216. FFI Safety

External media pointers must be wrapped in explicit unsafe/native handles.

---

# 217. Provider Versioning

Each provider exposes:

```text
provider_id
provider_version
capability_fingerprint
```

---

# 218. Codec Cache

Compiled codec state may be cached where backend supports it.

Cache keys include:

```text
codec
profile
level
device
driver
provider
configuration
```

---

# 219. Encoder Session Reuse

Encoders may be reused across segments when codec permits.

---

# 220. Decoder Reuse

Decoder reset should be cheaper than destroying/recreating the decoder when supported.

---

# 221. Segmenting

Recording pipelines may emit segments:

```text
segment_0001
segment_0002
...
```

without closing the entire application.

---

# 222. Crash Recovery

Recording can use periodic durable checkpoints.

A crash may leave a recoverable partial segment.

---

# 223. Durable Recording

For durable capture:

```text
Capture
 ↓
Encoder
 ↓
Muxer
 ↓
Buffered Storage
 ↓
Durable Commit
```

integrates with 611.

---

# 224. Atomic Finalization

A successfully finalized recording is activated atomically where the container format permits.

---

# 225. Partial Media

Interrupted media remains explicitly marked:

```text
Incomplete
```

rather than being presented as fully valid.

---

# 226. Media Index

Seekable media can maintain:

```text
timestamp → byte_offset
```

indexes.

---

# 227. Index Persistence

Indexes may be stored separately and reconstructed.

---

# 228. Thumbnail Generation

Thumbnail generation is a higher-level operation but can use:

```text
Demux
Decode
Graphics
Image encode
```

from 616/615.

---

# 229. Waveform Generation

Audio waveform generation can process streamed PCM without loading the entire track.

---

# 230. Spectral Analysis Boundary

FFT/spectral processing belongs to an optional DSP layer built above the audio buffers.

---

# 231. Audio Effects Boundary

615/616 core does not force a fixed plugin architecture for DSP effects.

A later DSP layer can define:

```text
AudioNode
```

interfaces.

---

# 232. Plugin Boundary

Codec/audio/video providers can be dynamically loaded only when authorized by BOOTSTRAP-603.

---

# 233. Plugin Trust

Provider packages can carry:

```text
publisher
signature
capabilities
target
version
```

using BOOTSTRAP-610/613.

---

# 234. No Arbitrary Codec Code

Media data cannot cause arbitrary code execution through a parser.

Codec providers execute within their declared security boundary.

---

# 235. Parser Limits

Demuxers enforce:

```text
maximum packet size
maximum metadata size
maximum stream count
maximum nesting
maximum index size
```

---

# 236. Decoder Limits

Decoders enforce provider/device limits on:

```text
resolution
reference frames
memory
work queue
```

---

# 237. Network Stream Security

HTTPS/TLS uses BOOTSTRAP-610/609.

616 does not implement its own TLS.

---

# 238. Storage Security

Media files use 603/611 capabilities.

A media pipeline cannot bypass filesystem permissions.

---

# 239. Camera Privacy

Camera access is auditable.

Diagnostics must not record raw frames by default.

---

# 240. Microphone Privacy

Microphone access is auditable.

Audio content is never included in ordinary diagnostic logs.

---

# 241. Screen Capture Privacy

Screen capture is explicitly permissioned and does not inherit ordinary graphics rendering authority.

---

# 242. Sensitive Metadata

Location and device identifiers can be marked sensitive.

Export requires explicit policy.

---

# 243. Resource Lifetime

A media frame is retired only after:

```text
all consumers release
AND
GPU/device operations complete
```

---

# 244. No GC

Media lifetime uses:

```text
ownership
handles
reference-counted immutable metadata where useful
generation IDs
deferred destruction
pools
```

---

# 245. Real-Time Allocation Rule

Audio callback paths must perform zero mandatory heap allocation.

---

# 246. Steady-State Video Rule

A stable playback pipeline should reuse:

```text
packet buffers
frame buffers
decoder surfaces
GPU textures
descriptor resources
```

instead of allocating every frame.

---

# 247. Memory Pressure

Under pressure, the runtime may:

```text
reduce cache
reduce prefetch
drop optional decoded frames
request application policy
```

but must not silently destroy required playback state.

---

# 248. Cache Eviction

Media caches use explicit LRU/LFU/size policies from 613.

---

# 249. Prefetch

Streaming sources may prefetch within configured resource budgets.

---

# 250. Adaptive Prefetch

Prefetch can consider:

```text
network throughput
buffer level
seek behavior
resource budget
```

---

# 251. Offline Prefetch

Offline applications may explicitly preload media into CAS/package storage.

---

# 252. Media Pipeline Shutdown

Shutdown sequence:

```text
Stop source
 ↓
Drain/flush
 ↓
Stop sink
 ↓
Wait required device operations
 ↓
Release resources
```

---

# 253. Fast Shutdown

For forced shutdown, pipeline state may be abandoned.

The runtime must not perform unbounded draining.

---

# 254. Cancellation

Every long-running media operation supports cancellation.

Cancellation must be propagated through the pipeline.

---

# 255. Deadline

Operations support deadlines where meaningful:

```text
decode
network read
device open
flush
seek
```

---

# 256. Timeout Semantics

Timeout never implies that the underlying provider has necessarily stopped.

The runtime reports whether cancellation was confirmed.

---

# 257. Service Integration

A media service managed by BOOTSTRAP-605 can expose:

```text
ready
degraded
device_lost
recovering
failed
```

states.

---

# 258. IPC Media Transport

Media frames can be transferred between processes through:

```text
shared memory
DMA buffer
GPU external memory
encoded packet IPC
```

---

# 259. Zero-Copy IPC

Preferred path:

```text
producer
   ↓
shared/device memory
   ↓
consumer
```

with explicit synchronization.

---

# 260. IPC Capability

Cross-process raw media buffer sharing requires a capability from 603.

---

# 261. Media Service Architecture

A system may run:

```text
Application
    ↓ IPC
Media Service
    ↓
Hardware Codec
```

without forcing every application to load codec implementations.

---

# 262. Embedded Architecture

On embedded targets:

```text
Camera → DMA → Encoder → Storage
```

can bypass general desktop abstractions while preserving the logical API.

---

# 263. Platform Capability Matrix

Every backend publishes a machine-readable capability matrix:

```text
.axmediacaps
```

including:

```text
audio formats
camera formats
codec support
hardware acceleration
zero-copy
HDR
secure decode
```

---

# 264. Capability Fingerprint

The capability matrix receives a deterministic fingerprint.

---

# 265. Build-Time Media Selection

A build can target:

```text
audio-only
video-playback
camera
recording
streaming
full-media
```

profiles.

---

# 266. Link-Time Minimization

Unused codecs/providers are dead-stripped.

A WAV-only application should not link H.264/AV1 decoders.

---

# 267. Compiler IR

Media operations may lower to runtime calls:

```text
media_open
media_decode
media_encode
media_submit
media_receive
media_timestamp
media_sync
```

---

# 268. Async Lowering

Async media pipelines lower to scheduler state machines.

No hidden thread is created merely because an API is async.

---

# 269. Callback Boundary

Native callbacks can be converted to Axiom tasks without copying frame data.

---

# 270. Error Metadata

Compiler-visible media errors include:

```text
media capability missing
codec unavailable
permission required
unsupported format
resource limit
```

---

# 271. Package Build

A media package can contain:

```text
codec-independent source
platform codec variants
precomputed indexes
thumbnails
waveforms
metadata
```

---

# 272. Content Addressing

Media chunks use BOOTSTRAP-613 content hashes.

This enables:

- deduplication;
- resumable downloads;
- immutable caches;
- incremental packaging.

---

# 273. Merkle Media Package

Large media packages may use Merkle trees for integrity verification.

---

# 274. Streaming Verification

Chunks can be verified before becoming visible to the media pipeline.

---

# 275. Encrypted Media Storage

Encrypted package/media storage uses 610/613.

616 does not implement a second encryption system.

---

# 276. Deterministic Container Output

AXMF output must be deterministic when:

```text source
metadata
codec configuration
timestamp sequence
```

are identical.

---

# 277. Media Metadata Schema

Metadata schemas use AXBIN from 612.

---

# 278. Schema Evolution

Media metadata supports:

```text optional fields
unknown-field preservation
schema versions
migration
```

---

# 279. Media Pipeline Serialization

Pipeline configuration can be serialized.

Live handles cannot.

---

# 280. Pipeline Hash

A pipeline configuration receives:

```text PipelineHash
```

for diagnostics and caching.

---

# 281. AI-Friendly Pipeline Description

Example:

```text
camera
 -> nv12
 -> h264_encoder
 -> axmf_muxer
 -> file
```

is representable as deterministic metadata.

---

# 282. AI Tooling

Compiler/tooling can expose:

```text
media inspect
media devices
media codecs
media capabilities
media pipeline
media benchmark
media diagnose
```

commands.

---

# 283. Media Inspection

`media inspect` reports:

```text
streams
duration
codec
format
bitrate
timebase
metadata
```

without decoding the complete media file.

---

# 284. Media Device Inspection

`media devices` reports:

```text
audio inputs
audio outputs
cameras
video accelerators
codec providers
```

---

# 285. Media Benchmark

Benchmark modes:

```text decode
encode
capture
playback
resample
mux
demux
upload
zero-copy
```

---

# 286. Testing

Required tests include:

- codec known-answer tests;
- demux/mux roundtrip;
- timestamp tests;
- clock drift tests;
- A/V synchronization;
- buffer pressure;
- packet corruption;
- device loss;
- camera hot plug;
- audio underrun;
- encoder backpressure;
- network interruption;
- storage interruption.

---

# 287. Codec Fuzzing

Every parser/decoder provider must have fuzz entry points.

---

# 288. Container Fuzzing

Fuzz:

```text
headers
indexes
metadata
packet sizes
nested structures
timestamps
```

---

# 289. Pipeline Fuzzing

Randomly generated valid/invalid graphs must never:

- deadlock;
- overflow;
- access stale handles;
- leak resources;
- bypass security checks.

---

# 290. Timestamp Fuzzing

Test:

```text
negative timestamps
large timestamps
wraparound
non-monotonic PTS
DTS > PTS
variable durations
discontinuities
```

---

# 291. Clock Tests

Test:

```text
drift
jump
pause
resume
rate change
device replacement
```

---

# 292. Audio Tests

Verify:

- sample conversion;
- resampling;
- channel mapping;
- mixer correctness;
- underrun handling;
- clock correction.

---

# 293. Video Tests

Verify:

- pixel conversion;
- color range;
- rotation;
- scaling;
- frame ordering;
- hardware surface lifetime.

---

# 294. Camera Tests

Verify:

- permission;
- enumeration;
- format negotiation;
- capture;
- hot plug;
- timestamp correctness;
- recovery.

---

# 295. Security Tests

Verify:

- denied camera access;
- denied microphone access;
- denied screen capture;
- protected frame restrictions;
- provider capability isolation;
- malformed media handling.

---

# 296. Resource Tests

Verify quotas for:

```text
frames
packets
codec sessions
camera sessions
audio streams
disk
network
GPU memory
```

---

# 297. Crash Tests

Simulate:

```text
codec provider crash
device removal
audio backend crash
camera disappearance
network disconnect
disk full
GPU device loss
```

and verify controlled recovery.

---

# 298. Performance Acceptance

Steady-state playback should:

- reuse buffers;
- avoid per-frame heap allocation;
- avoid global locks;
- avoid unnecessary CPU/GPU copies;
- use hardware acceleration where available.

---

# 299. Latency Acceptance

Low-latency audio must have bounded callback scheduling and buffer latency.

Live video must expose measurable capture-to-display latency.

---

# 300. Memory Acceptance

No media pipeline may allocate unbounded memory as a consequence of source/network speed.

---

# 301. Recovery Acceptance

A recoverable device loss must not corrupt unrelated application state.

---

# 302. API Stability

Public media descriptors are versioned.

Backend internals are not ABI promises.

---

# 303. Native Escape Hatch

Advanced applications may access native codec/device objects through explicit:

```text
unsafe
```

FFI boundaries.

---

# 304. No Pointer-Centric API

Ordinary users interact with:

```text
Handle<T>
Frame
Packet
Buffer
Pipeline
Device
```

rather than raw pointers.

---

# 305. Struct-Only API

Example:

```text
struct Player {
    pipeline: MediaPipeline
    clock: MediaClock
}

fn Player.play(self) -> Result<()> {
    self.pipeline.start()
}
```

No class hierarchy is required.

---

# 306. Extension Model

New codec/provider types can implement:

```text
CodecProvider
MediaSourceProvider
MediaSinkProvider
CameraProvider
AudioProvider
```

without modifying core structs.

---

# 307. Override Model

Following Axiom's struct-only model, a specialized provider replaces behavior through explicit trait implementation/dispatch rather than class inheritance.

---

# 308. No Virtual Dispatch Requirement

Static dispatch is preferred where provider type is known at compile time.

Dynamic provider dispatch is available only at explicit abstraction boundaries.

---

# 309. Generic Media Pipeline

Generic pipeline code may use compile-time traits:

```text
Source<T>
Decoder<T>
Encoder<T>
Sink<T>
```

where specialization is profitable.

---

# 310. Dynamic Pipeline

Runtime-created pipelines use erased handles:

```text
MediaNodeHandle
```

for plugin/provider scenarios.

---

# 311. Zero-Copy Principle

The runtime should prefer:

```text
same memory domain
shared memory
device memory
external resource import
```

before copying.

---

# 312. Copy Visibility

If a copy is inserted automatically by a provider, diagnostics should expose:

```text
implicit_copy
source_domain
destination_domain
bytes
reason
```

---

# 313. Pipeline Optimization

The compiler/runtime may fuse compatible operations:

```text
decode → color convert → scale
```

into one hardware operation where supported.

---

# 314. Operation Fusion

Fusion must preserve:

- timestamps;
- color semantics;
- precision;
- synchronization;
- error semantics.

---

# 315. Hardware Capability Selection

The runtime may choose:

```text
software
hardware
GPU compute
```

based on explicit application policy and capability.

---

# 316. Policy Modes

```text
PreferHardware
RequireHardware
PreferSoftware
RequireSoftware
Auto
```

---

# 317. Hardware Failure

If `RequireHardware` is selected, fallback is forbidden.

If `PreferHardware` is selected, controlled fallback may occur.

---

# 318. Power Policy

Mobile systems may expose:

```text
Performance
Balanced
PowerSaving
```

media profiles.

---

# 319. Thermal Adaptation

Adaptive resolution/frame rate is optional policy.

Core runtime only reports pressure.

---

# 320. Media Session

A high-level playback/recording session may group:

```text
source
pipeline
clock
audio output
video output
```

---

# 321. Session Lifecycle

```text
Created
Preparing
Ready
Playing
Paused
Seeking
Stopping
Stopped
Failed
Recovering
```

---

# 322. Session State

The session state is observable and diagnostics-compatible.

---

# 323. Playback

Playback controls:

```text
play
pause
seek
stop
set_rate
select_track
set_volume
```

may be implemented by higher-level player runtime using 616 primitives.

---

# 324. Recording

Recording controls:

```text
start
pause
resume
stop
split
```

can use capture/encode/mux primitives.

---

# 325. Streaming

Streaming controls:

```text
connect
buffer
play
reconnect
switch_representation
stop
```

remain policy-driven.

---

# 326. Network Reconnect

Reconnect must preserve media session state where possible.

---

# 327. Stream Discontinuity

Reconnect creates explicit discontinuity metadata.

---

# 328. Media Session Recovery

Recovery may recreate:

```text
network source
decoder
audio output
video surface
```

without recreating unrelated application state.

---

# 329. Media State Checkpoint

Persistable state can include:

```text
source URI
position
selected tracks
volume
playback rate
representation
```

Live handles are excluded.

---

# 330. Privacy in Checkpoints

Camera/microphone raw data must never enter ordinary state checkpoints.

---

# 331. Logging

Media logs contain:

```text
session_id
stream_id
codec
backend
event
timestamp
```

but never raw media.

---

# 332. Tracing

Media spans:

```text
demux
decode
encode
upload
render
audio_output
network_read
storage_write
```

integrate with BOOTSTRAP-602.

---

# 333. Correlation IDs

A media session can carry:

```text
MediaSessionId
PipelineId
FrameId
PacketId
```

for diagnostics.

---

# 334. Frame IDs

Frame IDs are monotonically increasing within a pipeline generation.

---

# 335. Packet IDs

Packet IDs identify packet processing for diagnostics.

---

# 336. Resource IDs

Codec sessions and device sessions have generation-safe identities.

---

# 337. Error Propagation

A fatal upstream error propagates downstream.

A recoverable error can be represented as an event without terminating the graph.

---

# 338. Graceful Degradation

A pipeline may degrade:

```text
hardware → software
HDR → SDR
high resolution → lower resolution
surround → stereo
```

only according to configured policy.

---

# 339. Format Fallback

Fallback decisions must be observable.

---

# 340. No Silent Quality Change

The runtime must not silently lower media quality without reporting the selected format/representation.

---

# 341. API Introspection

Every media session can expose:

```text
active_format
active_codec
active_device
buffer_state
clock_state
latency
```

---

# 342. Final Public API Families

```text
media.device.*
media.audio.*
media.camera.*
media.video.*
media.codec.*
media.container.*
media.pipeline.*
media.clock.*
media.capture.*
media.stream.*
media.session.*
```

---

# 343. Core Invariants

1. Media timestamps use explicit timebases.
2. PTS and DTS are never conflated.
3. Buffering is bounded.
4. Audio real-time paths never require GC.
5. GPU frames retain device ownership.
6. Device loss invalidates stale handles.
7. Camera/microphone/screen access requires capability.
8. Protected frames cannot be captured through ordinary APIs.
9. Codec parsers cannot escape their memory boundary.
10. Media pipelines propagate backpressure.
11. No hidden unlimited buffering exists.
12. No mandatory third-party media framework exists.
13. Hardware acceleration is capability-driven.
14. Zero-copy is preferred but never falsely promised.
15. Implicit copies are observable.
16. Clock drift is modeled explicitly.
17. A/V synchronization is policy-driven.
18. Live device state is not checkpointed.
19. Raw media is excluded from ordinary diagnostics.
20. Codec/provider plugins cannot bypass security policy.

---

# 344. Acceptance Criteria

BOOTSTRAP-616 is complete when the following are verified.

### Audio

1. Audio device enumeration.
2. Input device opening.
3. Output device opening.
4. PCM playback.
5. PCM capture.
6. F32 processing.
7. S16 processing.
8. Channel mapping.
9. Resampling.
10. Ring-buffer playback.
11. Real-time callback.
12. Underrun detection.
13. Overrun detection.
14. Device-loss recovery.
15. Device hot-plug.
16. Low-latency profile.
17. Shared-mode output.
18. Exclusive-mode boundary.
19. Audio clock exposure.
20. Audio diagnostics.

### Camera

21. Camera enumeration.
22. Camera permission.
23. Camera session.
24. Format negotiation.
25. Resolution selection.
26. Frame-rate selection.
27. Camera timestamps.
28. Camera hot-plug.
29. Device loss.
30. Preview to graphics.
31. GPU-frame import where supported.
32. Camera controls.
33. Auto exposure boundary.
34. Focus boundary.
35. White-balance boundary.
36. Orientation metadata.
37. Multiple stream capability.
38. Capture diagnostics.

### Video

39. Video frame model.
40. Pixel format model.
41. Color metadata.
42. HDR metadata.
43. GPU video frame.
44. CPU video frame.
45. Zero-copy path where supported.
46. Scaling.
47. Pixel conversion.
48. Rotation metadata.
49. Frame-rate conversion boundary.
50. Video timing.

### Codecs

51. Codec discovery.
52. Decoder API.
53. Encoder API.
54. Codec configuration.
55. Hardware decoder boundary.
56. Hardware encoder boundary.
57. Software provider.
58. External provider boundary.
59. Decoder flushing.
60. Encoder flushing.
61. Reordered frames.
62. Keyframe detection.
63. Forced keyframe.
64. Codec capability query.
65. Codec cache.
66. Codec failure propagation.

### Containers

67. Demuxer API.
68. Muxer API.
69. Stream enumeration.
70. Packet reading.
71. Packet writing.
72. Seek.
73. Indexing.
74. Metadata.
75. AXMF.
76. Crash-recoverable recording.
77. Atomic finalization.
78. Partial-media detection.

### Pipeline

79. Source nodes.
80. Sink nodes.
81. Decoder nodes.
82. Encoder nodes.
83. Transform nodes.
84. Pipeline graph.
85. Format negotiation.
86. Backpressure.
87. Cancellation.
88. Deadline.
89. Pipeline reset.
90. Pipeline flush.
91. Pipeline recovery.
92. Bounded buffering.
93. Memory-domain tracking.
94. Zero-copy negotiation.

### Synchronization

95. Media clock.
96. Audio master.
97. Video master.
98. External master.
99. Clock drift.
100. A/V sync.
101. Timestamp discontinuity.
102. Seek synchronization.
103. Variable frame rate.
104. Frame drop policy.
105. Audio correction.

### Streaming

106. File source.
107. Memory source.
108. Network source.
109. HTTP streaming.
110. HTTPS streaming.
111. Range requests.
112. Progressive download.
113. Reconnect.
114. Adaptive buffering.
115. Adaptive representation.
116. Network interruption recovery.
117. Network diagnostics.

### Capture/Recording

118. Camera recording.
119. Microphone recording.
120. Screen recording boundary.
121. Audio/video synchronization.
122. Hardware encoding.
123. File recording.
124. Segmented recording.
125. Crash recovery.
126. Durable finalization.

### Graphics Integration

127. Video → GPU texture.
128. GPU texture → encoder surface where supported.
129. External GPU memory.
130. GPU synchronization.
131. Device-generation validation.
132. Zero-copy diagnostics.

### Security

133. Camera capability.
134. Microphone capability.
135. Screen-capture capability.
136. Protected-media capability.
137. External provider capability.
138. Parser bounds.
139. Decoder resource limits.
140. Sensitive metadata protection.
141. No raw media in ordinary logs.

### Resources

142. CPU quotas.
143. GPU quotas.
144. packet-memory quotas.
145. frame-memory quotas.
146. codec-session quotas.
147. camera-session quotas.
148. network quotas.
149. storage quotas.
150. bounded cache.

### Diagnostics

151. Media session IDs.
152. Pipeline IDs.
153. Frame IDs.
154. Packet IDs.
155. decode latency.
156. encode latency.
157. buffer level.
158. frame drops.
159. audio underruns.
160. clock drift.
161. device loss.
162. provider failures.

### Toolchain

163. `.axmedia` metadata.
164. `.axmediacaps`.
165. compiler media diagnostics.
166. media inspection CLI.
167. media device CLI.
168. media capability CLI.
169. dead stripping.
170. deterministic metadata.

### Testing

171. codec fuzzing.
172. demux fuzzing.
173. timestamp fuzzing.
174. pipeline fuzzing.
175. device-loss tests.
176. hot-plug tests.
177. audio underrun tests.
178. memory-limit tests.
179. network interruption tests.
180. crash-recovery tests.
181. security tests.
182. deterministic AXMF tests.
183. mock-provider tests.
184. software-provider regression tests.

---

# 345. Final Architecture

```text
                         AXIOM APPLICATION
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
            PLAYER           RECORDER          EDITOR
               │                │                │
               └────────────────┼────────────────┘
                                ▼
                         BOOTSTRAP-616
 ┌──────────────────────────────────────────────────────┐
 │                                                      │
 │  Audio                  Video / Camera               │
 │  ├─ Input              ├─ Capture                   │
 │  ├─ Output             ├─ Frame                     │
 │  ├─ Mixer              ├─ Pixel Format              │
 │  ├─ Resampler          ├─ Color                     │
 │  └─ Clock              └─ Device                    │
 │                                                      │
 │  Codec                  Container                   │
 │  ├─ Decoder             ├─ Demux                    │
 │  ├─ Encoder             ├─ Mux                      │
 │  ├─ Hardware            └─ AXMF                      │
 │  └─ Software                                         │
 │                                                      │
 │  Media Pipeline        Synchronization              │
 │  ├─ Source             ├─ Media Clock               │
 │  ├─ Transform          ├─ A/V Sync                  │
 │  ├─ Sink               ├─ Drift                     │
 │  └─ Backpressure       └─ Timestamp                 │
 │                                                      │
 └───────────────┬───────────────┬──────────────────────┘
                 │               │
        ┌────────┘               └─────────┐
        ▼                                  ▼
 BOOTSTRAP-615                         BOOTSTRAP-609
 Graphics/GPU                         Network/HTTP/TLS
        │                                  │
        └──────────────┬───────────────────┘
                       ▼
                BOOTSTRAP-614
              Device / Hardware
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
    Camera           Audio           Video Codec
       │               │                │
       └───────────────┼────────────────┘
                       ▼
              Native OS / Hardware
```

Cross-cutting:

```text
600 State / Recovery
602 Diagnostics
603 Security / Capabilities
604 IPC / Shared Memory
605 Supervision
606 Resource Governor
607 Scheduler / Async
608 Synchronization
609 Networking
610 Crypto / Secure Transport
611 Storage / VFS
612 Serialization
613 Package / CAS
614 Device
615 Graphics
```

---

# 346. Architectural Decision

BOOTSTRAP-616 establishes Axiom's **native media substrate** without turning the language runtime into a monolithic multimedia framework.

The central design decisions are:

```text
Explicit media time
        +
Bounded buffering
        +
Pipeline graph
        +
Hardware/software provider abstraction
        +
GPU zero-copy integration
        +
Real-time audio path
        +
Capability-controlled capture
        +
Native device recovery
```

The runtime deliberately avoids:

- mandatory FFmpeg/GStreamer dependency;
- hidden unbounded buffering;
- mandatory garbage collection;
- raw-pointer-centric APIs;
- implicit network/storage stacks;
- automatic quality degradation;
- implicit privacy-sensitive capture;
- coupling media APIs to a specific editor/player architecture.

This makes the layer suitable as the foundation for future:

- professional video editor;
- DAW;
- media player;
- screen recorder;
- camera application;
- streaming server/client;
- AI audio/video processing;
- speech/TTS/ASR systems;
- video generation pipeline.

---

# 347. Task Completion

**BOOTSTRAP-616 — COMPLETE**

**Next queued task: BOOTSTRAP-617 — Native Text, Unicode, Font, Shaping, Typography, Internationalization & Localization Runtime 5.0**
:::