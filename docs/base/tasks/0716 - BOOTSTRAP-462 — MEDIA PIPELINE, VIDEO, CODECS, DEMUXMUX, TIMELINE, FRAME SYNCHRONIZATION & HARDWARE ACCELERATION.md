# BOOTSTRAP-462 — MEDIA PIPELINE, VIDEO, CODECS, DEMUX/MUX, TIMELINE, FRAME SYNCHRONIZATION & HARDWARE ACCELERATION

**Trạng thái: COMPLETED / LOCKED**

462 xây dựng media foundation phía trên 454/455/458/459/460/461, đủ thấp để tự xây **video player, editor, transcoder, recorder, streaming engine**, nhưng không biến media thành thành phần bắt buộc của runtime.

---

## 462.1 — Media architecture

```text id="media-architecture"
Axiom Core
    ↓
Numeric / SIMD
    ↓
GPU / Graphics
    ↓
Audio
    ↓
MEDIA CORE
    ├── MediaTime
    ├── MediaPacket
    ├── VideoFrame
    ├── AudioFrame
    ├── SubtitleFrame
    ├── Container
    ├── Demuxer
    ├── Decoder
    ├── Encoder
    ├── Muxer
    ├── Timeline
    ├── Clock
    ├── Sync
    ├── MediaGraph
    └── HardwareAcceleration
```

Các module đề xuất:

```text
media-core
media-time
media-frame
media-pixel
media-color
media-container
media-demux
media-decode
media-encode
media-mux
media-video
media-audio
media-subtitle
media-timeline
media-clock
media-sync
media-stream
media-hw
media-graph
media-metadata
media-filter
media-edit
```

---

# 462.2 — MediaTime

Không dùng `f64 seconds` làm representation chính.

Canonical representation:

```text
struct MediaTime {
    ticks: i64
    timebase: Rational
}
```

Ví dụ:

```text
timebase = 1/90000
ticks = 180000
```

→ 2 giây.

---

## 462.3 — Rational

```text
struct Rational {
    num: i64
    den: i64
}
```

Invariant:

```text
den != 0
```

Canonicalization tùy API.

---

## 462.4 — Timebase

Mỗi media stream có timebase riêng.

Không được giả định mọi stream dùng cùng clock.

---

## 462.5 — Timestamp

Media packet/frame có thể có:

```text
pts: Option<MediaTime>
dts: Option<MediaTime>
duration: Option<MediaTime>
```

---

## 462.6 — PTS

Presentation Timestamp xác định thời điểm dữ liệu được trình bày.

---

## 462.7 — DTS

Decode Timestamp xác định thứ tự/thời điểm cần decode.

---

## 462.8 — PTS ≠ DTS

Codec có frame reordering phải giữ hai giá trị độc lập.

---

## 462.9 — Duration

Frame duration có thể khác nhau.

Variable-frame-rate media được hỗ trợ.

---

## 462.10 — Negative timestamps

API phải cho phép timestamp âm trong những container/codec hợp lệ.

---

# 462.11 — MediaPacket

```text
struct MediaPacket {
    data: ByteView
    stream_id: StreamId
    pts: Option<MediaTime>
    dts: Option<MediaTime>
    duration: Option<MediaTime>
    flags: PacketFlags
}
```

---

## 462.12 — Packet ownership

Packet có thể owning hoặc borrowing.

---

## 462.13 — Keyframe flag

Packet có thể đánh dấu random-access/keyframe.

---

## 462.14 — Corrupt packet

Packet corruption trả error/status; không được dẫn tới memory-unsafe behavior.

---

## 462.15 — Packet side data

Side data được biểu diễn typed hoặc opaque.

---

## 462.16 — Packet lifetime

Decoder phải tiêu thụ/copy/reference packet theo contract rõ ràng.

---

# 462.17 — VideoFrame

```text
VideoFrame {
    format
    width
    height
    planes[]
    strides[]
    pts
    duration
    color_info
}
```

---

## 462.18 — Planar video

Ví dụ:

```text
Y
U
V
```

---

## 462.19 — Packed video

Ví dụ:

```text
RGBA
BGRA
RGB
```

---

## 462.20 — Pixel format

Foundation cần mô tả:

```text
Gray8
RGB8
RGBA8
BGRA8
RGB10A2
RGBA16
RGBA16F
YUV420P
YUV422P
YUV444P
NV12
P010
```

Không giới hạn vào danh sách này.

---

# 462.21 — Plane

Mỗi plane có:

```text
pointer/view
stride
width
height
bytes_per_pixel
```

---

## 462.22 — Stride

Stride có thể lớn hơn `width × bytes_per_pixel`.

Không được giả định contiguous row packing.

---

## 462.23 — Chroma subsampling

Metadata:

```text
4:4:4
4:2:2
4:2:0
4:1:1
```

---

## 462.24 — Chroma location

Phải được biểu diễn khi format/container yêu cầu.

---

## 462.25 — Video frame ownership

Frame ownership tuân thủ 423.

---

## 462.26 — Frame views

Có thể tạo view của plane mà không copy.

---

## 462.27 — GPU frame

VideoFrame có thể reference GPU resource thay vì CPU pointer.

---

## 462.28 — Frame storage domain

Explicit:

```text
CPU
GPU
Shared
External
```

---

## 462.29 — Zero-copy

CPU→GPU copy có thể tránh nếu backend hỗ trợ compatible resource.

---

## 462.30 — Copy fallback

Nếu zero-copy không khả dụng, API phải có explicit transfer.

---

# 462.31 — Color model

Color metadata gồm:

```text
primaries
transfer
matrix
range
```

---

## 462.32 — Color primaries

Ví dụ:

```text
BT.709
BT.2020
P3
```

---

## 462.33 — Transfer functions

Ví dụ:

```text
sRGB
BT.1886
PQ
HLG
```

---

## 462.34 — Matrix

Ví dụ:

```text
BT.601
BT.709
BT.2020
```

---

## 462.35 — Range

```text
Limited
Full
```

---

## 462.36 — HDR

HDR là metadata + pixel representation, không phải chỉ "10-bit".

---

## 462.37 — HDR metadata

Có thể chứa:

```text
static metadata
dynamic metadata
mastering display
content light level
```

---

## 462.38 — Color conversion

Color conversion là explicit media operation.

---

## 462.39 — GPU color conversion

Có thể chạy trên GPU qua 459.

---

## 462.40 — CPU fallback

Phải tồn tại implementation CPU cho các conversion portable.

---

# 462.41 — Video scaling

API:

```text
scale(frame, width, height, filter)
```

---

## 462.42 — Scaling filters

Ví dụ:

```text
Nearest
Bilinear
Bicubic
Lanczos
```

---

## 462.43 — Rotation

Rotation/flip là transform operation.

---

## 462.44 — Crop

Crop tạo frame/view mới tùy format.

---

## 462.45 — Aspect ratio

Display aspect ratio và pixel aspect ratio được phân biệt.

---

## 462.46 — SAR

Sample Aspect Ratio được lưu trong stream metadata.

---

## 462.47 — DAR

Display Aspect Ratio có thể được tính từ dimensions + SAR.

---

## 462.48 — Orientation

Container metadata có thể chứa rotation/orientation.

---

## 462.49 — No silent transform

Decoder không tự xoay/scale màu nếu caller chưa yêu cầu.

---

## 462.50 — Video processing graph

Các transform có thể được nối thành graph.

---

# 462.51 — AudioFrame

AudioFrame reuse 461:

```text
AudioBuffer
sample_rate
channels
layout
pts
duration
```

---

## 462.52 — Audio/video common frame

Conceptual:

```text
MediaFrame =
    Video(VideoFrame)
    Audio(AudioFrame)
    Subtitle(SubtitleFrame)
```

---

## 462.53 — SubtitleFrame

```text
SubtitleFrame {
    start
    end
    payload
    style
}
```

---

## 462.54 — Subtitle payload

Có thể là:

```text
plain text
styled text
bitmap
structured cue
```

---

## 462.55 — Subtitle timing

Subtitle sử dụng cùng `MediaTime`.

---

# 462.56 — MediaStream

Stream metadata:

```text
StreamId
MediaType
CodecId
Timebase
Duration
Language
Disposition
```

---

## 462.57 — Media types

Foundation:

```text
Video
Audio
Subtitle
Data
Attachment
```

---

## 462.58 — Stream selection

Player/editor có thể chọn stream explicit.

---

## 462.59 — Multiple audio tracks

Supported.

---

## 462.60 — Multiple subtitle tracks

Supported.

---

## 462.61 — Multiple video tracks

Supported.

---

## 462.62 — Data tracks

Timed metadata/data tracks được hỗ trợ.

---

## 462.63 — Language metadata

Language tag không phải encoding assumption.

---

## 462.64 — Default stream

Container có thể đánh dấu default nhưng application vẫn có quyền chọn.

---

## 462.65 — Stream metadata

Metadata không được nhầm với codec configuration.

---

# 462.66 — Container abstraction

Container chứa:

```text tracks
packets
metadata
chapters
attachments
indexes
```

---

## 462.67 — Demuxer

```text
Demuxer.open(source)
Demuxer.read_packet()
Demuxer.seek()
```

---

## 462.68 — Muxer

```text
Muxer.add_stream()
Muxer.write_packet()
Muxer.finalize()
```

---

## 462.69 — Container ≠ codec

Một codec có thể nằm trong nhiều container.

---

## 462.70 — Codec ≠ stream

Codec configuration thuộc stream.

---

# 462.71 — Demux pipeline

```text id="demux-pipeline"
ByteSource
   ↓
ContainerParser
   ↓
MediaPacket
   ↓
StreamRouter
```

---

## 462.72 — Decode pipeline

```text
MediaPacket
   ↓
Decoder
   ↓
DecodedFrame
```

---

## 462.73 — Encode pipeline

```text
RawFrame
   ↓
Encoder
   ↓
MediaPacket
```

---

## 462.74 — Mux pipeline

```text
MediaPacket
   ↓
Muxer
   ↓
ByteSink
```

---

## 462.75 — Full transcode

```text
Input
 ↓
Demux
 ↓
Decode
 ↓
Process
 ↓
Encode
 ↓
Mux
 ↓
Output
```

---

# 462.76 — Codec abstraction

```text
trait VideoDecoder
trait VideoEncoder
trait AudioDecoder
trait AudioEncoder
```

---

## 462.77 — Codec descriptor

Descriptor:

```text
CodecId
name
media_type
profiles
levels
pixel_formats
sample_formats
hardware_support
```

---

## 462.78 — Codec capabilities

Application can query supported combinations.

---

## 462.79 — Codec configuration

Configuration explicit:

```text
profile
level
bitrate
quality
gop
b_frames
rate_control
```

---

## 462.80 — Codec presets

Presets are configuration data, not language semantics.

---

# 462.81 — Software codec

Software codec implementation follows normal Axiom code.

---

## 462.82 — Hardware codec

Hardware codec uses 459 accelerator abstraction.

---

## 462.83 — Hardware decode

Pipeline:

```text
Compressed Packet
       ↓
Hardware Decoder
       ↓
GPU VideoFrame
```

---

## 462.84 — Hardware encode

```text
GPU VideoFrame
       ↓
Hardware Encoder
       ↓
Compressed Packet
```

---

## 462.85 — Hardware fallback

If requested hardware backend unavailable:

```text
hardware unavailable
        ↓
explicit fallback policy
        ↓
software codec
```

Không tự fallback nếu caller yêu cầu strict hardware mode.

---

## 462.86 — Hardware capabilities

Expose:

```text
decode codecs
encode codecs
profiles
levels
formats
max resolution
max frame rate
```

---

## 462.87 — Device affinity

Decoder/encoder có thể gắn với GPU/device cụ thể.

---

## 462.88 — Multi-GPU

Application có thể chọn device.

---

## 462.89 — GPU/CPU synchronization

Explicit fence/event semantics từ 459.

---

## 462.90 — Avoid unnecessary copies

Frame graph phải track memory domain để tối ưu transfer.

---

# 462.91 — Decode reorder

Codec decoder có thể output frame khác packet order.

---

## 462.92 — Decode queue

Decoder giữ internal reorder state.

---

## 462.93 — Flush decoder

Explicit flush operation.

---

## 462.94 — End-of-stream drain

Decoder phải drain delayed frames trước EOS.

---

## 462.95 — Encoder delay

Encoder cũng có thể buffer frames.

---

## 462.96 — Encoder flush

Explicit.

---

## 462.97 — B-frames

PTS/DTS handling bắt buộc hỗ trợ reorder.

---

## 462.98 — Random access

Keyframe/index metadata dùng cho seek.

---

## 462.99 — Decoder reset

Seek có thể reset decoder state.

---

## 462.100 — Seek accuracy

API phân biệt:

```text
Exact
NearestKeyframe
Fast
```

---

# 462.101 — Timeline

Timeline là higher-level abstraction.

```text
Timeline
Track
Clip
Transition
Marker
```

---

## 462.102 — Track

Các loại:

```text
VideoTrack
AudioTrack
SubtitleTrack
DataTrack
```

---

## 462.103 — Clip

Clip tham chiếu media source + source range + timeline range.

---

## 462.104 — Source range

```text
source_in
source_out
```

---

## 462.105 — Timeline range

```text
timeline_in
timeline_out
```

---

## 462.106 — Speed

Clip playback speed là explicit transform.

---

## 462.107 — Reverse

Reverse playback/rendering là explicit operation.

---

## 462.108 — Freeze frame

Explicit clip operation.

---

## 462.109 — Gap

Timeline có thể chứa gap.

---

## 462.110 — Overlap

Overlapping clips require explicit compositing/mixing semantics.

---

# 462.111 — Transition

Transition:

```text
cut
crossfade
dissolve
wipe
custom
```

---

## 462.112 — Video transition

GPU shader/filter có thể implement transition.

---

## 462.113 — Audio transition

Crossfade/mix qua 461.

---

## 462.114 — Transition timing

Transition operates in timeline coordinates.

---

## 462.115 — Effects

Effects are graph nodes, not timeline primitives.

---

## 462.116 — Render graph

Timeline can compile to media processing graph.

---

## 462.117 — Graph compilation

```text
Timeline
 ↓
Dependency analysis
 ↓
MediaGraph
 ↓
Execution plan
```

---

## 462.118 — Parallelism

Independent tracks/nodes can execute concurrently.

---

## 462.119 — Determinism

Parallel execution must not change deterministic output where deterministic profile is enabled.

---

## 462.120 — Cache

Decoded/processed frames can be cached.

---

# 462.121 — Frame cache

Cache key includes at minimum:

```text
source identity
frame/time
decoder configuration
processing graph version
color configuration
```

---

## 462.122 — Cache invalidation

Source or processing change invalidates affected cache entries.

---

## 462.123 — Disk cache

Optional and uses 455.

---

## 462.124 — Memory cache

Optional LRU/clock policies.

---

## 462.125 — Cache ownership

Cache owns frames/resources explicitly.

---

## 462.126 — GPU cache

GPU resource cache is allowed.

---

## 462.127 — Cache budget

Explicit memory/VRAM budget.

---

## 462.128 — Eviction

Eviction cannot violate active frame ownership.

---

## 462.129 — No GC

Cache uses explicit ownership/eviction.

---

## 462.130 — Cache telemetry

Expose hits/misses/bytes/evictions.

---

# 462.131 — MediaClock

```text
MediaClock {
    now()
    rate()
    anchor()
}
```

---

## 462.132 — Clock sources

Possible:

```text
Audio
Video
System
External
Network
```

---

## 462.133 — Master clock

Application explicitly chooses master clock.

---

## 462.134 — Player default

For A/V playback, audio clock may commonly be selected, but this is policy rather than language semantics.

---

## 462.135 — Clock rate

Playback rate can be:

```text
0
positive
negative
```

according to supported engine semantics.

---

## 462.136 — Pause

Clock rate 0 or explicit paused state.

---

## 462.137 — Seek

Clock anchor changes.

---

## 462.138 — Clock drift

Measured independently from timestamp drift.

---

## 462.139 — External clock

Network synchronization may supply external clock.

---

## 462.140 — Clock discontinuity

Discontinuities are explicit events.

---

# 462.141 — A/V synchronization

For each frame:

```text
frame_time
master_clock_time
delta
```

---

## 462.142 — Video early

If video is early, wait/drop policy is applied according to player policy.

---

## 462.143 — Video late

If late, player can drop eligible frames.

---

## 462.144 — Frame dropping

Dropping is explicit playback policy.

---

## 462.145 — Frame duplication

Duplication can be used for presentation timing.

---

## 462.146 — Audio correction

Audio drift correction uses 461 resampling.

---

## 462.147 — Hard discontinuity

Large timestamp discontinuity resets synchronization state.

---

## 462.148 — Sync tolerance

Application configures tolerance.

---

## 462.149 — No universal threshold

Axiom does not hard-code one "acceptable sync" threshold.

---

## 462.150 — Sync diagnostics

Expose measured A/V offset.

---

# 462.151 — Media streaming

Uses 454 networking.

```text
Network
 ↓
Protocol
 ↓
Container/packet
 ↓
Jitter Buffer
 ↓
Decode
 ↓
Clock Sync
 ↓
Render
```

---

## 462.152 — Jitter buffer

Buffers packets against network jitter.

---

## 462.153 — Packet loss

Protocol-specific recovery.

---

## 462.154 — Late packet

Policy determines drop/recovery.

---

## 462.155 — Backpressure

Decode/render pipeline exposes backpressure.

---

## 462.156 — Adaptive bitrate

ABR is higher-level streaming logic.

---

## 462.157 — Segment

Streaming systems may represent media as segments.

---

## 462.158 — Manifest

Manifest parser is protocol/application layer.

---

## 462.159 — Live stream

Live streams have moving timeline and limited seek window.

---

## 462.160 — DVR window

Optional rolling seekable range.

---

# 462.161 — Subtitle

Subtitle foundation supports:

```text timed text
styled text
bitmap subtitle
```

---

## 462.162 — Subtitle parsing

Container/protocol parser is separate from rendering.

---

## 462.163 — Text shaping

Use future text/rendering subsystem.

---

## 462.164 — Unicode

Text follows Axiom UTF-8 semantics.

---

## 462.165 — Subtitle encoding

External encodings are explicitly decoded into UTF-8.

---

## 462.166 — Subtitle styling

Style data remains structured.

---

## 462.167 — Subtitle burn-in

Implemented as media filter/render graph operation.

---

## 462.168 — Subtitle overlay GPU

Can be rendered through 460/459.

---

## 462.169 — Subtitle export

Can be muxed as separate subtitle track.

---

## 462.170 — Subtitle timing

Uses MediaTime, not floating-point seconds.

---

# 462.171 — Media metadata

Metadata classes:

```text
ContainerMetadata
StreamMetadata
CodecMetadata
FrameMetadata
ColorMetadata
DeviceMetadata
```

---

## 462.172 — Metadata ownership

Metadata values follow normal ownership.

---

## 462.173 — Unknown metadata

Unknown fields may be preserved as opaque data.

---

## 462.174 — Metadata round-trip

Muxer should preserve supported metadata where format allows.

---

## 462.175 — Metadata security

Metadata is untrusted input.

---

## 462.176 — Metadata size limits

Parser applies resource limits.

---

## 462.177 — Chapters

Timeline can expose chapter markers.

---

## 462.178 — Attachments

Container attachments are separate resources.

---

## 462.179 — Cover art

Represented as attachment/image metadata.

---

## 462.180 — Provenance

Media pipeline can record source/provider/processing provenance.

---

# 462.181 — Media graph

Nodes:

```text
Source
Demux
Decode
Transform
Filter
Mix
Composite
Encode
Mux
Sink
```

---

## 462.182 — Typed edges

Edges declare:

```text
Packet
VideoFrame
AudioFrame
SubtitleFrame
ByteStream
```

---

## 462.183 — Graph validation

Reject incompatible edge types before execution.

---

## 462.184 — Format negotiation

Nodes negotiate compatible formats.

---

## 462.185 — Conversion insertion

Compiler/planner may insert explicit conversion nodes.

---

## 462.186 — Hidden conversion

Conversions should appear in graph/diagnostics, even if planner inserts them automatically.

---

## 462.187 — Graph scheduling

Scheduler computes dependency order.

---

## 462.188 — Resource planning

Planner computes CPU memory/GPU memory/buffer requirements.

---

## 462.189 — Pipeline parallelism

Decode, processing, encode can overlap.

---

## 462.190 — Cancellation

Cancellation propagates through graph.

---

# 462.191 — Async media

Uses 424.

---

## 462.192 — Async decode

Decoder can expose asynchronous frame production.

---

## 462.193 — Async encode

Encoder can expose asynchronous packet production.

---

## 462.194 — Blocking decoder

Blocking codecs are explicitly marked.

---

## 462.195 — Blocking file source

Uses 455 effects.

---

## 462.196 — Async network source

Uses 454.

---

## 462.197 — Cancellation cleanup

All media resources clean up deterministically.

---

## 462.198 — Pipeline shutdown

Order:

```text
stop input
drain/flush
stop workers
release graph
release device resources
```

---

## 462.199 — Worker ownership

Worker/task resources follow 424.

---

## 462.200 — No hidden threads

Media subsystem must declare worker requirements.

---

# 462.201 — Hardware acceleration abstraction

```text
MediaDevice
VideoDecoderBackend
VideoEncoderBackend
VideoSurface
GpuFrame
```

---

## 462.202 — Backend-independent API

Media engine does not expose only one vendor API.

---

## 462.203 — Backend adapters

Platform/vendor implementations are adapters.

---

## 462.204 — Hardware surfaces

Decoded frames may remain on hardware surface.

---

## 462.205 — Surface import

GPU graphics subsystem can import compatible media surface.

---

## 462.206 — Surface export

Render graph can export frame to encoder.

---

## 462.207 — Zero-copy editor path

Ideal path:

```text
Decode GPU
 ↓
GPU effects
 ↓
GPU composite
 ↓
GPU encode
```

---

## 462.208 — CPU fallback editor path

```text
Decode CPU
 ↓
CPU effects
 ↓
CPU encode
```

---

## 462.209 — Mixed path

Explicit transfers between CPU/GPU domains.

---

## 462.210 — Transfer diagnostics

Tooling records expensive domain transitions.

---

# 462.211 — Video renderer

Renderer integrates with 460.

---

## 462.212 — Presentation surface

Video frame can be presented to native window.

---

## 462.213 — Headless rendering

Media engine supports file rendering without a window.

---

## 462.214 — Offscreen rendering

Frame can render into offscreen GPU/CPU target.

---

## 462.215 — VSync

Presentation can synchronize with display clock.

---

## 462.216 — Frame pacing

Renderer controls presentation timing.

---

## 462.217 — Dropped presentation

Presentation drops are observable.

---

## 462.218 — HDR presentation

HDR metadata is passed to presentation layer where supported.

---

## 462.219 — Color-managed presentation

Renderer must know source/output color spaces.

---

## 462.220 — No silent SDR conversion

HDR→SDR requires explicit/policy-driven conversion.

---

# 462.221 — Media editor foundation

Timeline API is sufficient to build:

```text
cut
trim
split
merge
overlay
transition
audio mix
subtitle
filter
speed change
```

---

## 462.222 — Non-destructive editing

Timeline stores references/operations rather than modifying source media.

---

## 462.223 — Render

Timeline can compile into render graph.

---

## 462.224 — Preview

Preview can use lower resolution/quality policy.

---

## 462.225 — Proxy media

Proxy source can substitute original during preview.

---

## 462.226 — Proxy identity

Proxy/original relationship explicit.

---

## 462.227 — Offline render

Final rendering can switch back to source.

---

## 462.228 — Deterministic render

Deterministic mode freezes relevant processing parameters.

---

## 462.229 — Partial render

Only affected timeline ranges need re-render.

---

## 462.230 — Render cache

Render cache uses 455 storage.

---

# 462.231 — Export

Export configuration:

```text container
video codec
audio codec
resolution
frame rate
bitrate/quality
color
metadata
```

---

## 462.232 — Presets

Presets are reusable configuration objects.

---

## 462.233 — Export validation

Check codec/container compatibility before processing.

---

## 462.234 — Multi-output

One timeline can generate multiple outputs.

---

## 462.235 — Batch export

Multiple export configurations can run independently.

---

## 462.236 — Progress

Export reports progress by media time/work units.

---

## 462.237 — Cancellation

Export cancellation performs cleanup.

---

## 462.238 — Resume

Resume support is optional and format-dependent.

---

## 462.239 — Atomic output

Write temporary output then atomic rename where filesystem permits.

---

## 462.240 — Failed export

Partial artifact is clearly marked/non-final.

---

# 462.241 — Media security

Media files are untrusted input.

---

## 462.242 — Parser isolation

Complex decoders may optionally run out-of-process.

---

## 462.243 — Resource limits

Limits include:

```text max dimensions
max duration
max packets
max metadata
max memory
max decode time
```

---

## 462.244 — Integer overflow

Parser arithmetic must be checked.

---

## 462.245 — Bounds safety

All frame/packet parsing follows 445.

---

## 462.246 — Fuzzing

Demuxers/codecs/muxers are fuzz targets.

---

## 462.247 — Malformed timestamps

Must not cause invalid arithmetic or infinite loops.

---

## 462.248 — Malformed dimensions

Rejected before allocation.

---

## 462.249 — Compression bombs

Decode resource limits required.

---

## 462.250 — Untrusted subtitles

Subtitle text/styles are treated as untrusted input.

---

# 462.251 — Plugin architecture

External codec/container implementations can be plugins/providers.

---

## 462.252 — Plugin ABI

Independent from Axiom language ABI.

---

## 462.253 — Native plugin

Can be dynamic library.

---

## 462.254 — WASM plugin

Can be sandboxed.

---

## 462.255 — Plugin trust

Plugin code is foreign/untrusted according to 445.

---

## 462.256 — Plugin capability

Plugin declares supported formats/codecs.

---

## 462.257 — Plugin versioning

Provider ABI version independent from package version.

---

## 462.258 — Plugin failure

Provider crash isolation is optional; untrusted plugins should not execute in main process.

---

## 462.259 — Plugin discovery

Explicit registry/configuration.

---

## 462.260 — No mandatory plugin

Core media can operate without dynamic plugin discovery.

---

# 462.261 — Media testing

Tests:

```text
timebase
timestamps
packet ordering
decode reorder
seek
flush
demux
mux
frame layout
color conversion
scaling
A/V sync
timeline
graph
hardware transfer
```

---

## 462.262 — Golden media files

Small canonical media fixtures.

---

## 462.263 — Reference hashes

Deterministic outputs can use hashes.

---

## 462.264 — Perceptual comparison

Video/audio quality tests may use perceptual metrics separately from exact equality.

---

## 462.265 — No universal quality score

Different codecs/use cases require separate metrics.

---

## 462.266 — Decoder fuzzing

Mandatory for bundled parsers.

---

## 462.267 — Encoder correctness

Decode encoded output and validate expected semantics.

---

## 462.268 — Timestamp tests

VFR/B-frame/negative timestamp fixtures.

---

## 462.269 — Seek tests

Random seeks around keyframes.

---

## 462.270 — A/V sync tests

Known synchronized test media.

---

# 462.271 — Media benchmarks

Measure independently:

```text decode FPS
encode FPS
latency
CPU
GPU
VRAM
RAM
copies
throughput
startup
seek latency
```

---

## 462.272 — Hardware benchmark

Separate CPU and hardware codec measurements.

---

## 462.273 — Copy benchmark

Measure CPU↔GPU transfer cost.

---

## 462.274 — Pipeline benchmark

Measure stage overlap.

---

## 462.275 — Timeline benchmark

Measure render planning/execution.

---

## 462.276 — Cache benchmark

Measure hit/miss and storage overhead.

---

## 462.277 — Streaming benchmark

Measure jitter-buffer latency and recovery.

---

## 462.278 — Export benchmark

Separate demux/decode/process/encode/mux costs.

---

## 462.279 — Startup benchmark

Measure device/codec initialization independently.

---

## 462.280 — No aggregate media score

No single number represents media performance.

---

# 462.281 — AI metadata

446 exposes:

```text
media graph
stream graph
codec
container
format
timestamp
memory domain
GPU transfer
timeline
render cache
```

---

## 462.282 — Explain graph

AI can ask:

```text
why is this frame copied?
why is this conversion inserted?
which codec is active?
why is hardware decode unavailable?
```

---

## 462.283 — Frame provenance

Every derived frame may retain:

```text
source
timestamp
operation chain
```

---

## 462.284 — Render provenance

Output artifact can identify processing graph/configuration.

---

## 462.285 — Codec provenance

Record codec implementation/provider/version.

---

## 462.286 — Hardware provenance

Record device/backend/driver information.

---

## 462.287 — Timeline metadata

AI can inspect clips/tracks/transitions.

---

## 462.288 — Sync diagnostics

AI can inspect A/V offset and clock decisions.

---

## 462.289 — Performance explanation

AI can inspect CPU/GPU hotspots and transfer costs.

---

## 462.290 — Security explanation

AI can inspect parser/plugin trust boundaries.

---

# 462.291 — Implementation order

### Phase 1

```text
MediaTime
Rational
MediaPacket
MediaStream
VideoFrame
AudioFrame
```

### Phase 2

```text
Container
Demuxer
Muxer
```

### Phase 3

```text
Software Decoder
Software Encoder
```

### Phase 4

```text
Video processing
Color
Scaling
Frame conversion
```

### Phase 5

```text
MediaClock
A/V sync
Timeline
```

### Phase 6

```text
MediaGraph
Async pipeline
Streaming
```

### Phase 7

```text
GPU surfaces
Hardware decode
Hardware encode
```

### Phase 8

```text
Editor/export/cache
Subtitle
Advanced media
```

---

# 462.292 — Compiler interaction

Media does **not** require compiler special cases for ordinary codecs.

Compiler needs only:

```text
ownership
SIMD
comptime
GPU
FFI
async
```

from existing architecture.

---

## 462.293 — Media intrinsics

Optional compiler intrinsics can support:

```text
pixel conversion
vector shuffle
packed arithmetic
hardware codec fences
```

but high-level media semantics remain library-level.

---

## 462.294 — No media language syntax requirement

Axiom language itself does not need:

```text
video
audio
codec
timeline
```

keywords.

---

## 462.295 — Optional DSL

A future editor package may provide a declarative timeline DSL, but it is not core syntax.

---

# 462.296 — Binary size

A CLI utility that only uses:

```text
JPEG/PNG image processing
```

must not automatically link:

```text
audio
timeline
GPU
network streaming
```

---

## 462.297 — Feature linking

Media components remain separately linkable.

---

## 462.298 — Runtime independence

Media runtime is optional.

---

## 462.299 — Third-party dependency independence

Axiom compiler/linker does not depend on FFmpeg/LLVM/GCC/Clang.

External codec libraries may be consumed through 451 if the application chooses them.

---

## 462.300 — Native implementation

Axiom must provide enough low-level facilities to implement native media engines without requiring C/C++ as an implementation language.

---

# 462.301 — Hard invariants

1. Media is not language core.
2. Media is not mandatory runtime.
3. Audio and video are separate stream types.
4. Codec and container are separate.
5. Demux and decode are separate.
6. Encode and mux are separate.
7. PTS and DTS are distinct.
8. Timebase is explicit.
9. Floating-point seconds are not canonical media timestamps.
10. Negative timestamps are representable.
11. Variable frame rate is supported.
12. Frame duration is explicit.
13. Decoder reorder is supported.
14. Encoder delay is supported.
15. Flush/drain semantics are explicit.
16. Seek semantics are explicit.
17. Keyframe/random-access information is preserved.
18. Video planes have explicit stride.
19. Planar and packed formats are distinct.
20. Chroma subsampling is explicit.
21. Color primaries are explicit.
22. Transfer function is explicit.
23. Matrix coefficients are explicit.
24. Range is explicit.
25. HDR metadata is explicit.
26. No silent color conversion.
27. No silent scaling.
28. No silent rotation.
29. CPU and GPU frame domains are distinct.
30. Zero-copy is an optimization, not a semantic requirement.
31. Ownership follows 423.
32. Unsafe frame memory follows 445.
33. Audio frames reuse 461 semantics.
34. GPU frames reuse 459.
35. SIMD processing reuses 458.
36. Storage/cache uses 455.
37. Networking uses 454.
38. Async uses 424.
39. Timeline is higher-level than media packets.
40. Timeline is non-destructive by default.
41. Clips reference source ranges.
42. Timeline ranges are independent of source ranges.
43. Playback speed is explicit.
44. Reverse playback is explicit.
45. Transitions are explicit.
46. Effects are graph nodes.
47. MediaGraph has typed edges.
48. Graph format negotiation is explicit.
49. Automatically inserted conversions remain observable.
50. Graph cycles require explicit feedback semantics.
51. Pipeline parallelism must preserve declared semantics.
52. Cancellation is explicit.
53. Worker threads are not hidden.
54. Hardware acceleration is optional.
55. Hardware capabilities are queryable.
56. Hardware fallback policy is explicit.
57. Strict hardware mode does not silently fall back.
58. CPU fallback can exist.
59. CPU↔GPU transfers are observable.
60. GPU resource lifetime is deterministic.
61. Multi-GPU selection is explicit.
62. Video rendering integrates with graphics rather than duplicating GPU architecture.
63. Headless rendering is first-class.
64. Offline rendering is first-class.
65. Preview quality can differ explicitly from final render.
66. Proxy media is explicit.
67. Render caching is explicit.
68. Cache invalidation is deterministic.
69. Cache cannot violate ownership.
70. A/V synchronization uses explicit clocks.
71. Master clock is a policy.
72. Audio clock and system clock remain distinct.
73. Frame dropping is explicit policy.
74. Frame duplication is explicit policy.
75. Audio drift correction uses 461 facilities.
76. No universal synchronization threshold is embedded in language semantics.
77. Streaming uses explicit jitter buffering.
78. Streaming uses 454 networking.
79. Backpressure is explicit.
80. Live media is supported.
81. Subtitle timing uses MediaTime.
82. Subtitle text uses UTF-8 semantics.
83. Subtitle parser treats input as untrusted.
84. Metadata is structured.
85. Unknown metadata may be preserved.
86. Metadata is untrusted input.
87. Parser resource limits are mandatory.
88. Integer overflow in parsers must be handled safely.
89. Malformed dimensions must be rejected before dangerous allocation.
90. Compression/resource exhaustion attacks must be bounded.
91. Media parsers/codecs are fuzz targets.
92. External codec providers are trust boundaries.
93. Plugin ABI is separate from language ABI.
94. Untrusted plugins should be isolated.
95. Codec/provider version is queryable.
96. Hardware provider/version is queryable.
97. Media provenance can be recorded.
98. AI tooling can inspect media graphs.
99. AI tooling can explain format conversions and memory transfers.
100. Media performance is measured with independent metrics.
101. No universal media quality/performance score exists.
102. Media does not introduce GC.
103. Media does not introduce a borrow checker.
104. Media does not introduce hidden allocations.
105. Realtime audio constraints remain those of 461.
106. Video processing may allocate outside realtime paths.
107. Hardware acceleration does not become mandatory runtime infrastructure.
108. Media components are independently linkable.
109. Unused media subsystems are omitted from native artifacts.
110. Axiom does not depend on FFmpeg, LLVM, GCC or Clang to compile/link native applications.
111. External codec libraries remain optional FFI dependencies.
112. Axiom can implement a native media engine in Axiom itself.
113. Media artifacts can be deterministic under an explicit deterministic profile.
114. Device-dependent output is identified as device-dependent.
115. Release artifacts can strip debug/media provenance metadata when configured.
116. Media security metadata integrates with 445.
117. Media performance metadata integrates with 450.
118. Media semantic metadata integrates with 446.
119. Media ABI/FFI integrates with 451.
120. **Axiom media foundation must be capable of supporting a native video editor/player/transcoder/recorder without forcing any media capability onto unrelated executables.**

**BOOTSTRAP-462 hoàn tất.**

---

# BOOTSTRAP-463 — IMAGE PROCESSING, PIXEL PIPELINE, COLOR MANAGEMENT, RASTER, CODECS & GPU IMAGE COMPUTATION

Phạm vi tiếp theo:

```text
Image
 ├── Pixel formats
 ├── Planes / strides
 ├── Color spaces
 ├── ICC / color profiles
 ├── HDR
 ├── Resize
 ├── Crop
 ├── Rotate
 ├── Composite
 ├── Blend
 ├── Convolution
 ├── Morphology
 ├── Filters
 ├── GPU image
 ├── CPU SIMD image
 ├── PNG/JPEG/WebP/AVIF/etc.
 ├── Image sequence
 └── Media/Graphics interoperability
```

Mục tiêu là để cùng một foundation có thể xây **Photoshop/Substance-like image processing, texture tools, computer vision preprocessing, image editor và texture pipeline**, đồng thời tái sử dụng trực tiếp 458 SIMD, 459 GPU, 460 graphics, 455 storage và 462 media.