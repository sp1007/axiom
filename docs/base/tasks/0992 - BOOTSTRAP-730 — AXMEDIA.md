# BOOTSTRAP-730 — AXMEDIA

**Namespace:** `AXMEDIA`  
**Phase:** Axiom Civilization Runtime / Native Media & Multimedia Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXCOMPUTE`, `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXAI`, `AXSECURITY`, `AXIDENTITY`, `AXGEOSPATIAL`, `AXASSET`

> `AXMEDIA` là media substrate native của Axiom: từ raw bytes, sample và pixel đến audio/video/image pipelines, codec/container, capture, playback, streaming, editing, synchronization và GPU-accelerated processing. Nó không phải một video-editor application; nó cung cấp primitives để các ứng dụng media cấp cao được xây dựng trực tiếp trên Axiom.

---

# 730.0 — Mục tiêu

Kiến trúc:

```text
                         AXMEDIA
                            │
          ┌─────────────────┼──────────────────┐
          ↓                 ↓                  ↓
       AUDIO              VIDEO              IMAGE
          │                 │                  │
          └─────────────────┼──────────────────┘
                            ↓
                     MEDIA PIPELINE
                            ↓
                    AXCOMPUTE / AXAI
                            ↓
              CPU / GPU / NPU / DSP
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
          STORAGE         NETWORK        DEVICE
```

Phải hỗ trợ:

```text
audio
video
image
animation
subtitles
captions
metadata
live media
recording
playback
editing
transcoding
streaming
speech
multimedia AI
```

---

# 730.1 — Media Boundary

`AXMEDIA` sở hữu:

```text
media sample
media frame
audio buffer
video frame
image
timeline
stream
track
container
codec interface
capture
playback
synchronization
media pipeline
transcoding
media metadata
subtitle
caption
media indexing
media processing
media clock
```

Không sở hữu:

```text
physical device identity      → AXASSET
physical network              → AXNETWORK / AXTELECOM
persistent storage            → AXSTORAGE
database semantics            → AXDATABASE
AI model                      → AXAI
cryptography                  → AXSECURITY
legal copyright/rights        → AXLAW / domain
```

---

# 730.2 — Media Core Model

Media phải phân biệt:

```text
media
container
stream
track
sample
frame
packet
codec
timeline
clock
```

Đặc biệt:

```text
container ≠ codec
stream ≠ track
packet ≠ frame
timestamp ≠ duration
```

---

# 730.3 — Media Object

```axiom
media {
    media_id
    type
    streams
    metadata
    duration
    timebase
}
```

Types:

```text
AUDIO
VIDEO
IMAGE
ANIMATION
MULTIMEDIA
SUBTITLE
```

---

# 730.4 — Media Stream

```axiom
media_stream {
    stream_id
    media_id
    kind
    codec
    format
    timebase
}
```

Kinds:

```text
audio
video
subtitle
metadata
data
```

Một media container có thể chứa nhiều streams.

---

# 730.5 — Track

Track là logical presentation channel:

```axiom
track {
    track_id
    stream_reference
    language
    role
    timeline
}
```

Ví dụ:

```text
Video track
Audio Vietnamese track
Audio English track
Subtitle Vietnamese
Subtitle English
```

---

# 730.6 — Packet

```axiom
media_packet {
    data
    timestamp
    duration
    flags
    stream_id
}
```

Packet là encoded representation.

Không được giả định:

```text
1 packet = 1 frame
```

---

# 730.7 — Frame

```axiom
media_frame {
    timestamp
    duration
    format
    buffer
}
```

Frame là decoded media unit.

Video:

```text
frame = image representation
```

Audio:

```text
frame = sample block
```

---

# 730.8 — Sample

Audio sample:

```axiom
audio_sample<T>
```

Ví dụ:

```text
i16
i24
i32
f32
f64
```

---

# 730.9 — Audio Buffer

```axiom
audio_buffer<T> {
    samples
    channels
    sample_rate
    layout
    timestamp
}
```

---

# 730.10 — Audio Channel

Layouts:

```text
mono
stereo
2.1
5.1
7.1
ambisonic
custom
```

Channel identity phải explicit.

---

# 730.11 — Sample Rate

Native representation:

```text
sample_rate {
    numerator
    denominator
}
```

Cho phép:

```text
44100
48000
96000
```

và fractional rates.

---

# 730.12 — Audio Format

```axiom
audio_format {
    sample_type
    sample_rate
    channels
    layout
    interleaving
}
```

Interleaving:

```text
interleaved
planar
```

---

# 730.13 — Audio Processing

Core:

```text
mix
gain
normalize
resample
channel_convert
delay
filter
equalize
compress
limit
pan
fade
```

---

# 730.14 — Audio Resampling

```axiom
resample(
    source,
    target_rate,
    quality
)
```

Quality phải explicit:

```text
FAST
NORMAL
HIGH
REFERENCE
```

---

# 730.15 — Audio Clock

Audio device có clock riêng.

Không được giả định:

```text
audio clock == system clock
```

---

# 730.16 — Video Frame

```axiom
video_frame {
    width
    height
    pixel_format
    color_space
    color_range
    transfer_function
    timestamp
    duration
    planes
}
```

---

# 730.17 — Pixel Format

Native formats:

```text
RGB8
RGBA8
RGB10
RGBA16
GRAY8
GRAY16
YUV420
YUV422
YUV444
NV12
P010
FLOAT
```

Có thể mở rộng backend.

---

# 730.18 — Image

```axiom
image<T> {
    width
    height
    channels
    format
    color_space
    buffer
}
```

Image là data object.

Video frame là temporal media object.

---

# 730.19 — Color Space

```axiom
color_space {
    primaries
    transfer
    matrix
    range
}
```

Không được coi:

```text
RGB
```

là đầy đủ color metadata.

---

# 730.20 — HDR

Native metadata:

```text
HDR10
HDR10+
HLG
Dolby-like extensible metadata
```

Không hard-code một HDR standard vào core.

---

# 730.21 — Video Resolution

```axiom
resolution {
    width
    height
    pixel_aspect_ratio
}
```

Pixel aspect ratio không mặc định là 1:1.

---

# 730.22 — Frame Rate

```axiom
frame_rate {
    numerator
    denominator
}
```

Hỗ trợ:

```text
24
23.976
25
29.97
30
50
59.94
60
120
```

Không lưu frame rate authoritative dưới dạng floating-point.

---

# 730.23 — Timebase

Mọi media timestamp phải dùng rational/integer representation:

```axiom
timebase {
    numerator
    denominator
}
```

Không dùng floating-point timestamp làm authoritative timeline.

---

# 730.24 — Timestamp

```axiom
timestamp {
    value
    timebase
}
```

Phải hỗ trợ:

```text
PTS
DTS
duration
presentation order
decode order
```

---

# 730.25 — Presentation vs Decode Order

Codec có thể có:

```text
decode order
    ≠
presentation order
```

Runtime phải preserve cả hai khi cần.

---

# 730.26 — Media Clock

```axiom
media_clock {
    source
    rate
    timestamp
}
```

Clock sources:

```text
audio
video
system
external
network
capture_device
```

---

# 730.27 — Synchronization

Media sync phải hỗ trợ:

```text
audio-video sync
multi-camera sync
multi-device sync
external clock sync
live stream sync
subtitle sync
```

---

# 730.28 — Sync Policy

```text
MASTER_AUDIO
MASTER_VIDEO
MASTER_EXTERNAL
MASTER_SYSTEM
ADAPTIVE
```

---

# 730.29 — Drift

Runtime phải đo:

```text
clock drift
timestamp drift
buffer drift
network jitter
```

Có thể corrective bằng:

```text
resampling
frame duplication
frame dropping
clock adjustment
buffer adjustment
```

---

# 730.30 — Container

```axiom
container {
    format
    streams
    metadata
    duration
}
```

Ví dụ adapter:

```text
MP4
MOV
MKV
WebM
AVI
WAV
AIFF
FLAC container
```

Container support là adapter, không hard-code semantic vào core.

---

# 730.31 — Codec

```axiom
codec {
    name
    media_type
    capabilities
    encoder
    decoder
}
```

---

# 730.32 — Codec Capability

```axiom
codec_capability {
    formats
    profiles
    levels
    bit_depth
    resolution
    frame_rate
    hardware_support
}
```

---

# 730.33 — Decoder

```axiom
decoder {
    open()
    decode()
    flush()
    close()
}
```

Decode output là typed frames.

---

# 730.34 — Encoder

```axiom
encoder {
    open()
    encode()
    flush()
    close()
}
```

Input/output timing phải explicit.

---

# 730.35 — Codec Hardware Acceleration

Codec backend có thể sử dụng:

```text
CPU
GPU
DSP
NPU
dedicated media engine
```

Runtime phải expose capability.

---

# 730.36 — Transcoding

```text
input
 ↓
demux
 ↓
decode
 ↓
process
 ↓
encode
 ↓
mux
 ↓
output
```

---

# 730.37 — Remuxing

Nếu codec compatible:

```text
container A
 ↓
demux
 ↓
packet
 ↓
mux
 ↓
container B
```

Không decode/re-encode nếu không cần.

---

# 730.38 — Media Pipeline

```axiom
media_pipeline {
    source
    stages
    scheduler
    sink
}
```

---

# 730.39 — Pipeline Stage

```axiom
media_stage {
    input_format
    output_format
    process()
}
```

Stages:

```text
capture
decode
transform
filter
mix
encode
mux
output
```

---

# 730.40 — Pipeline Graph

```text
source
 ├── audio → process → encode
 └── video → process → encode
                    ↓
                   mux
```

Graph phải hỗ trợ fan-out/fan-in.

---

# 730.41 — Backpressure

Pipeline phải có native backpressure:

```text
producer
   ↓
buffer
   ↓
consumer
```

Nếu consumer chậm:

```text
pause
throttle
drop
buffer
```

policy phải explicit.

---

# 730.42 — Real-Time Mode

```axiom
pipeline_mode = REALTIME
```

Có deadline:

```text
frame deadline
buffer budget
latency budget
```

---

# 730.43 — Offline Mode

```axiom
pipeline_mode = OFFLINE
```

Có thể ưu tiên:

```text
quality
throughput
compression
```

thay vì latency.

---

# 730.44 — Capture Device

```axiom
capture_device {
    device_id
    capabilities
    formats
}
```

Sources:

```text
camera
microphone
screen
sensor
network
file
```

---

# 730.45 — Capture Session

```axiom
capture_session {
    device
    format
    clock
    timestamp
}
```

Capture timestamp phải giữ source clock provenance.

---

# 730.46 — Camera

Camera capabilities:

```text
resolution
frame_rate
pixel_format
HDR
exposure
focus
white_balance
```

Hardware control integration → `AXASSET` / device adapter.

---

# 730.47 — Microphone

Microphone capabilities:

```text
sample_rate
channels
sample_format
latency
clock
```

---

# 730.48 — Screen Capture

```axiom
screen_capture {
    display
    region
    resolution
    frame_rate
    color_space
}
```

---

# 730.49 — Playback

```axiom
player {
    source
    clock
    tracks
    output_devices
}
```

State:

```text
STOPPED
LOADING
READY
PLAYING
PAUSED
BUFFERING
SEEKING
ENDED
ERROR
```

---

# 730.50 — Seeking

```axiom
seek(
    timestamp,
    mode
)
```

Modes:

```text
EXACT
KEYFRAME
NEAREST
FAST
```

---

# 730.51 — Playback Buffer

```axiom
playback_buffer {
    target_duration
    min_duration
    max_duration
}
```

Streaming playback phải adapt buffer theo network conditions.

---

# 730.52 — Media Timeline

```axiom
timeline {
    tracks
    duration
    timebase
    markers
}
```

Timeline là logical editing representation.

---

# 730.53 — Timeline Clip

```axiom
clip {
    source
    source_in
    source_out
    timeline_in
    timeline_out
    speed
}
```

Không copy media data khi chỉ tạo clip reference.

---

# 730.54 — Speed Change

```axiom
speed = 0.5
speed = 1.0
speed = 2.0
```

Speed transformation phải preserve timestamp semantics.

---

# 730.55 — Reverse Playback

Timeline có thể:

```text
direction = forward
direction = reverse
```

Codec/keyframe constraints phải được runtime xử lý.

---

# 730.56 — Transition

```axiom
transition {
    start
    duration
    type
}
```

Core chỉ cần primitive:

```text
crossfade
dissolve
cut
wipe
```

Advanced transitions là higher-level library.

---

# 730.57 — Compositing

```axiom
composite {
    layers
    transform
    opacity
    blend_mode
}
```

---

# 730.58 — Transform

Video/image transform:

```text
translate
scale
rotate
crop
mirror
perspective
```

---

# 730.59 — Blend

```text
normal
add
multiply
screen
overlay
custom
```

Blend implementation có thể GPU accelerated.

---

# 730.60 — Alpha

Hỗ trợ:

```text
opaque
straight alpha
premultiplied alpha
```

Alpha semantics phải explicit.

---

# 730.61 — Subtitle

```axiom
subtitle {
    start
    end
    text
    style
    language
}
```

---

# 730.62 — Subtitle Track

```axiom
subtitle_track {
    language
    entries
    style
}
```

---

# 730.63 — Caption vs Subtitle

Phân biệt:

```text
subtitle
    → dialogue / translation

caption
    → dialogue + relevant audio/context information
```

---

# 730.64 — Timed Text

Core representation phải hỗ trợ:

```text
plain text
styled text
position
alignment
speaker
language
reading order
```

---

# 730.65 — Media Metadata

```axiom
media_metadata {
    key
    value
    namespace
    source
}
```

Metadata có thể là:

```text
technical
capture
creative
location
rights-reference
application
```

---

# 730.66 — Metadata Provenance

Metadata phải biết:

```text
source
created_at
modified_at
authority
```

Không coi mọi embedded metadata là authoritative.

---

# 730.67 — Media Location

Có thể chứa:

```axiom
location_reference
```

nhưng actual spatial semantics:

→ `AXGEOSPATIAL`.

---

# 730.68 — Media Identity

```axiom
media_reference {
    media_id
    version
}
```

Identity không phụ thuộc file path.

---

# 730.69 — Content Addressing

Media artifact có thể có:

```axiom
content_id
```

dựa trên content hash.

Integration:

→ `AXSTORAGE`.

---

# 730.70 — Media Version

Original:

```text
media v1
```

Edited:

```text
media v2
```

không được overwrite immutable artifact nếu artifact đã published.

---

# 730.71 — Media Edit Graph

```text
source A ──┐
           ├─→ edit graph → output
source B ──┘
```

Edit graph có thể preserve source references.

---

# 730.72 — Non-Destructive Editing

Core media model ưu tiên:

```text
source media
     ↓
references
     ↓
timeline
     ↓
effects
     ↓
render
```

không bắt buộc render intermediate sau mỗi operation.

---

# 730.73 — Render

```axiom
render(
    timeline,
    output_format
)
```

Render planner:

```text
decode
→ transform
→ composite
→ effect
→ encode
```

---

# 730.74 — Smart Rendering

Nếu một đoạn không thay đổi:

```text
encoded packet
```

có thể được copy trực tiếp.

Không re-encode toàn bộ timeline nếu không cần.

---

# 730.75 — Image Processing

Core:

```text
resize
crop
rotate
flip
blur
sharpen
convolution
color_transform
tone_map
denoise
```

---

# 730.76 — GPU Image Processing

Image graph có thể compile thành:

```text
GPU kernels
```

và giữ buffers trên GPU qua nhiều stages.

---

# 730.77 — Audio Graph

```axiom
audio_graph {
    sources
    processors
    mixers
    outputs
}
```

Ví dụ:

```text
Mic A ─┐
       ├→ Mixer → EQ → Compressor → Output
Mic B ─┘
```

---

# 730.78 — Audio Routing

```axiom
audio_route {
    source
    destination
    channels
    gain
}
```

---

# 730.79 — Spatial Audio

Native primitives:

```text
listener
source
position
orientation
distance
attenuation
```

3D coordinates → `AXGEOSPATIAL` compatible.

---

# 730.80 — Spatial Audio Scene

```axiom
audio_scene {
    listener
    sources
    environment
}
```

Có thể support:

```text
stereo
binaural
surround
object-based audio
ambisonics
```

---

# 730.81 — Speech Media Boundary

Speech waveform và timing:

→ `AXMEDIA`

Speech recognition / synthesis model:

→ `AXAI`

Flow:

```text
audio
 ↓
AXMEDIA
 ↓
tensor
 ↓
AXAI
 ↓
speech model
 ↓
tensor
 ↓
AXMEDIA
 ↓
audio
```

---

# 730.82 — Video AI Boundary

Video decoding:

→ `AXMEDIA`

Visual model:

→ `AXAI`

Pipeline:

```text
video frame
 ↓
tensor conversion
 ↓
AXAI
 ↓
prediction
 ↓
metadata/result
```

---

# 730.83 — Media AI Metadata

AI-generated result:

```axiom
media_ai_result {
    media_reference
    model_reference
    timestamp
    region
    result
    confidence
    provenance
}
```

AI result không tự sửa original media.

---

# 730.84 — Media Search

Media indexing:

```text
media
 ↓
metadata
 ↓
transcript
 ↓
embedding
 ↓
AXDATABASE
```

---

# 730.85 — Media Transcript

```axiom
transcript {
    language
    segments
    words
    timestamps
    confidence
}
```

Transcript phải giữ timing provenance.

---

# 730.86 — Word Timing

```axiom
word_timing {
    word
    start
    end
    confidence
}
```

Có thể dùng cho:

```text
subtitles
search
karaoke-like alignment
editing
```

---

# 730.87 — Live Streaming

```axiom
live_stream {
    source
    tracks
    protocol
    latency_mode
}
```

Latency:

```text
ULTRA_LOW
LOW
NORMAL
```

---

# 730.88 — Live Pipeline

```text
capture
 ↓
encode
 ↓
packetize
 ↓
network
 ↓
buffer
 ↓
decode
 ↓
play
```

---

# 730.89 — Streaming Protocol Boundary

`AXMEDIA` chỉ định media semantics.

Transport:

→ `AXNETWORK`.

Có thể adapter:

```text
HTTP streaming
WebSocket
QUIC-like transport
RTP-like transport
```

---

# 730.90 — Adaptive Streaming

Có thể chọn:

```text
bitrate
resolution
frame rate
codec profile
```

dựa trên:

```text
network bandwidth
latency
device capability
buffer state
```

---

# 730.91 — Media Quality Policy

```axiom
quality_policy {
    target_quality
    max_bitrate
    max_latency
    max_memory
}
```

Scheduler tối ưu theo policy.

---

# 730.92 — Recording

```axiom
recording_session {
    sources
    format
    clock
    destination
}
```

Hỗ trợ:

```text
single stream
multi-track
multi-camera
screen + audio
```

---

# 730.93 — Multi-Camera

```axiom
camera_group {
    cameras
    synchronization
}
```

Sync có thể dựa trên:

```text
hardware clock
shared timestamp
visual alignment
audio alignment
```

---

# 730.94 — Media Buffer

```axiom
media_buffer<T> {
    pointer
    size
    alignment
    memory_domain
    ownership
}
```

Memory domains:

```text
CPU
GPU
shared
device
mapped
```

---

# 730.95 — Zero-Copy Media

Ideal path:

```text
capture
 ↓
GPU buffer
 ↓
GPU processing
 ↓
hardware encoder
```

không:

```text
GPU → CPU → GPU
```

trừ khi required.

---

# 730.96 — DMA / Device Transfer

Media pipeline có thể use:

```text
DMA
shared memory
mapped buffers
device-local memory
```

Implementation thuộc hardware backend.

---

# 730.97 — Media Scheduling

Scheduler phải xét:

```text
frame deadline
buffer occupancy
decode complexity
encode complexity
GPU load
memory bandwidth
network condition
```

---

# 730.98 — Dropping Policy

Khi overload:

```text
DROP_NONE
DROP_LATE
DROP_NON_REFERENCE
DROP_OLDEST
ADAPTIVE
```

Policy explicit.

---

# 730.99 — Error Recovery

Media runtime phân biệt:

```text
DECODE_ERROR
ENCODE_ERROR
CORRUPTED_PACKET
MISSING_FRAME
TIMESTAMP_ERROR
CLOCK_DRIFT
DEVICE_ERROR
NETWORK_ERROR
BUFFER_UNDERFLOW
BUFFER_OVERFLOW
UNSUPPORTED_FORMAT
```

---

# 730.100 — Corrupted Media

Decoder có thể:

```text
strict
recover
skip
conceal
```

Result phải expose recovery state.

Không silently pretend corrupted frame là original frame.

---

# 730.101 — Media Integrity

Artifact có thể có:

```axiom
media_integrity {
    hash
    signature_reference
    provenance
}
```

Cryptography:

→ `AXSECURITY`.

---

# 730.102 — Media Security

Protected media có thể yêu cầu:

```text
identity
capability
decryption
secure playback
output restriction
```

AXMEDIA chỉ consumes security capabilities.

---

# 730.103 — Media Privacy

Metadata có thể chứa sensitive information:

```text
location
device
timestamp
voice
face
```

Privacy classification phải propagate.

---

# 730.104 — Media Access Control

Access:

```text
read
write
edit
export
stream
capture
derive
share
```

được kiểm soát bởi capability/security layer.

---

# 730.105 — Media Events

```axiom
media_event {
    event_id
    media
    type
    actor
    timestamp
}
```

Types:

```text
MEDIA_CREATED
MEDIA_IMPORTED
MEDIA_CAPTURED
MEDIA_EDITED
MEDIA_RENDERED
MEDIA_ENCODED
MEDIA_EXPORTED
MEDIA_PUBLISHED
MEDIA_ARCHIVED
MEDIA_RETIRED
```

---

# 730.106 — Media Replay

Media pipeline có thể record:

```text
input references
pipeline version
codec version
configuration
hardware
timestamps
```

để replay deterministic workflows.

---

# 730.107 — Deterministic Media Processing

Reference mode có thể yêu cầu:

```axiom
deterministic = true
```

Đặc biệt cho:

```text
rendering
transcoding
scientific media analysis
testing
```

---

# 730.108 — Media Simulation

Có thể mô phỏng:

```text
capture
network jitter
packet loss
decoder load
GPU load
buffer behavior
stream latency
```

---

# 730.109 — Media Digital Twin

```axiom
media_digital_twin {
    sources
    devices
    pipelines
    codecs
    network
    storage
}
```

Dùng để test media infrastructure trước production.

---

# 730.110 — Distributed Media Processing

```text
source
 ↓
decode node
 ↓
processing nodes
 ↓
encode node
 ↓
storage
```

Partition có thể theo:

```text
frame
segment
stream
track
pipeline stage
```

---

# 730.111 — Distributed Media Consistency

Mỗi segment cần:

```text
source reference
time range
codec configuration
dependency
```

Không được nối hai segment với timestamp assumptions khác nhau.

---

# 730.112 — Media Chunk

```axiom
media_chunk {
    media
    start
    end
    packets
    keyframe_state
}
```

Chunk là transport/storage unit, không nhất thiết là semantic track.

---

# 730.113 — Media Index

```axiom
media_index {
    time
    keyframe
    packet_offset
    frame_reference
}
```

Index có thể tăng tốc seek mà không trở thành source of truth.

---

# 730.114 — Thumbnail

```axiom
thumbnail {
    source
    timestamp
    image
}
```

Thumbnail là derived artifact.

---

# 730.115 — Waveform

```axiom
waveform {
    source
    resolution
    peaks
}
```

Waveform là derived representation, không phải audio source.

---

# 730.116 — Proxy Media

```axiom
proxy {
    source
    format
    resolution
    quality
}
```

Proxy chỉ là performance representation.

Original remains authoritative media source.

---

# 730.117 — Media Cache

Cache có thể giữ:

```text
decoded frame
thumbnail
waveform
proxy
compiled shader
encoded segment
```

Cache miss không thay đổi semantic state.

---

# 730.118 — Media Storage

```text
AXMEDIA
   ↓
AXSTORAGE
   ↓
filesystem / object / content-addressed storage
```

Media runtime không tự phát minh storage engine.

---

# 730.119 — Media Database

Metadata:

```text
media IDs
tracks
timestamps
transcripts
AI results
indexes
```

→ `AXDATABASE`.

Raw media:

→ `AXSTORAGE`.

---

# 730.120 — Native APIs

```axiom
open_media()
create_media()
inspect_media()

open_container()
demux()
mux()

create_decoder()
decode()
flush_decoder()

create_encoder()
encode()
flush_encoder()

transcode()
remux()

create_audio_buffer()
resample()
mix()
filter_audio()

create_image()
transform_image()
convert_color()

create_video_frame()
transform_frame()
composite()

create_pipeline()
add_stage()
connect_stage()
run_pipeline()

create_timeline()
add_track()
add_clip()
add_transition()
render()

create_capture_device()
start_capture()
stop_capture()

create_player()
play()
pause()
seek()
stop()

create_stream()
publish_stream()
consume_stream()

create_subtitle_track()
add_caption()

create_transcript()

index_media()
generate_thumbnail()
generate_proxy()
generate_waveform()

record_media()
replay_media()

simulate_media_pipeline()
create_media_digital_twin()
```

---

# 730.121 — Formal Invariants

```text
MED-INV-01   Container and codec are distinct concepts.
MED-INV-02   Stream and track are distinct concepts.
MED-INV-03   Packet and frame are distinct concepts.
MED-INV-04   Media timestamps use explicit timebases.
MED-INV-05   Authoritative timestamps do not use floating-point representation.
MED-INV-06   PTS and DTS remain distinguishable when applicable.
MED-INV-07   Audio sample rate is explicit.
MED-INV-08   Audio channel layout is explicit.
MED-INV-09   Video pixel format is explicit.
MED-INV-10   Video color metadata is explicit.

MED-INV-11   Frame rate uses exact rational representation.
MED-INV-12   Clock source is explicit.
MED-INV-13   Clock drift is measurable.
MED-INV-14   Synchronization policy is explicit.
MED-INV-15   Media pipeline preserves declared timing semantics.
MED-INV-16   Backpressure behavior is explicit.
MED-INV-17   Real-time pipelines have explicit latency/deadline policy.
MED-INV-18   Offline pipelines may not silently claim real-time guarantees.
MED-INV-19   Dropped frames are distinguishable from decoded frames.
MED-INV-20   Recovered/corrupted frames expose recovery state.

MED-INV-21   A media reference is independent of file path.
MED-INV-22   Published media versions are immutable.
MED-INV-23   Non-destructive edits preserve source references.
MED-INV-24   Timeline clips do not imply media duplication.
MED-INV-25   Smart rendering cannot alter unaffected source data.
MED-INV-26   Derived thumbnails/proxies are distinguishable from originals.
MED-INV-27   Cache data is never authoritative media state.
MED-INV-28   Metadata provenance is preserved.
MED-INV-29   AI-derived media metadata is distinguishable from source metadata.
MED-INV-30   Media processing provenance can be recorded.

MED-INV-31   Zero-copy operations preserve buffer ownership semantics.
MED-INV-32   Device-local buffers are not implicitly copied through host memory.
MED-INV-33   GPU processing may retain media buffers on device.
MED-INV-34   Hardware acceleration is capability-driven.
MED-INV-35   Unsupported codec operations are explicit failures.
MED-INV-36   Remuxing does not imply transcoding.
MED-INV-37   Transcoding does not silently claim bit-exact preservation.
MED-INV-38   Media replay cannot mutate source artifacts.
MED-INV-39   Media simulation cannot mutate production state.
MED-INV-40   Security and cryptographic authority remain outside AXMEDIA.
```

---

# 730.122 — Performance Architecture

Hot path:

```text
Capture
  ↓
Native Media Buffer
  ↓
GPU / DSP
  ↓
Codec Hardware
  ↓
Network / Storage
```

Mục tiêu tránh:

```text
device
 ↓
generic object
 ↓
serialization
 ↓
CPU copy
 ↓
generic buffer
 ↓
GPU copy
```

---

# 730.123 — Compile-Time Media Pipeline

Axiom compiler có thể biết:

```text
pixel format
sample format
resolution
dtype
device
codec capability
pipeline topology
```

Từ đó generate specialized pipeline.

---

# 730.124 — Pipeline Specialization

Ví dụ:

```axiom
pipeline<NV12, GPU> {
    decode
    resize
    color_convert
    encode
}
```

Compiler có thể eliminate unnecessary conversions.

---

# 730.125 — Format Conversion Elimination

Nếu:

```text
decoder output = NV12
processor input = NV12
```

không cần:

```text
NV12 → RGB → NV12
```

---

# 730.126 — Audio Zero-Copy

Nếu processor hỗ trợ cùng layout:

```text
input planar f32
      ↓
processor
      ↓
output planar f32
```

không allocate intermediate buffer không cần thiết.

---

# 730.127 — Media + AXAI Fast Path

```text
camera
 ↓
GPU frame
 ↓
tensor view
 ↓
AXAI
 ↓
prediction
```

Không bắt buộc:

```text
GPU frame
 ↓
CPU image
 ↓
serialized image
 ↓
tensor
```

---

# 730.128 — Media + AXCOMPUTE

AXMEDIA gửi workload:

```text
decode
encode
filter
render
```

cho `AXCOMPUTE`.

`AXCOMPUTE` quản lý physical resource scheduling.

---

# 730.129 — Media + AXNETWORK

Network layer cung cấp:

```text
transport
buffering
packet delivery
connection
```

AXMEDIA quyết định:

```text
codec
framing
timestamp
media adaptation
```

---

# 730.130 — Media + AXGEOSPATIAL

Media có thể reference:

```text
camera location
capture region
trajectory
orientation
```

nhưng canonical geometry:

→ `AXGEOSPATIAL`.

---

# 730.131 — Media + AXIDENTITY

Mỗi capture/publish operation có thể record:

```text
creator
operator
device_identity
service_identity
```

---

# 730.132 — Media + AXSECURITY

Protected media:

```text
identity
 ↓
capability
 ↓
decrypt/read
 ↓
decode
 ↓
render
```

---

# 730.133 — Media + AXAI

AXAI có thể:

```text
speech_to_text
text_to_speech
image_understanding
video_understanding
generation
enhancement
denoise
super_resolution
```

Nhưng model semantics thuộc AXAI.

---

# 730.134 — Media + AXDATABASE

Database indexes:

```text
media metadata
time ranges
transcripts
faces/objects references
embeddings
scene segments
```

AI-generated information phải được đánh dấu derived.

---

# 730.135 — Media Application Layer

Các hệ thống cấp cao có thể xây trên AXMEDIA:

```text
video editor
audio editor
DAW
player
streaming server
screen recorder
NLE
broadcast system
podcast system
photo editor
animation system
VFX system
subtitle editor
media archive
```

AXMEDIA không cần chứa UI logic của các ứng dụng này.

---

# 730.136 — Completion Criteria

`BOOTSTRAP-730` phải freeze:

1. Media object.
2. Stream.
3. Track.
4. Packet.
5. Frame.
6. Sample.
7. Audio buffer.
8. Audio channel.
9. Sample rate.
10. Audio format.
11. Video frame.
12. Image.
13. Pixel format.
14. Color space.
15. HDR.
16. Resolution.
17. Frame rate.
18. Timebase.
19. Timestamp.
20. Media clock.
21. Synchronization.
22. Container.
23. Codec.
24. Codec capability.
25. Decoder.
26. Encoder.
27. Hardware acceleration.
28. Transcoding.
29. Remuxing.
30. Media pipeline.
31. Pipeline stages.
32. Pipeline graph.
33. Backpressure.
34. Real-time mode.
35. Offline mode.
36. Capture device.
37. Camera.
38. Microphone.
39. Screen capture.
40. Playback.
41. Seeking.
42. Playback buffering.
43. Timeline.
44. Clip.
45. Speed/reverse.
46. Transition.
47. Compositing.
48. Transform.
49. Blend.
50. Alpha.
51. Subtitle.
52. Caption.
53. Timed text.
54. Metadata.
55. Metadata provenance.
56. Media identity.
57. Content addressing.
58. Media versioning.
59. Non-destructive editing.
60. Render.
61. Smart rendering.
62. Image processing.
63. Audio graph.
64. Spatial audio.
65. Speech integration.
66. Video AI integration.
67. AI metadata.
68. Media search.
69. Transcript.
70. Live streaming.
71. Adaptive streaming.
72. Recording.
73. Multi-camera.
74. Native media buffers.
75. Zero-copy.
76. DMA/device transfer.
77. Media scheduling.
78. Drop policy.
79. Error recovery.
80. Media integrity.
81. Security.
82. Privacy.
83. Access control.
84. Media events.
85. Replay.
86. Deterministic processing.
87. Simulation.
88. Digital twin.
89. Distributed media.
90. Media chunks.
91. Media index.
92. Thumbnail.
93. Waveform.
94. Proxy media.
95. Cache.
96. AXSTORAGE integration.
97. AXDATABASE integration.
98. AXNETWORK integration.
99. AXCOMPUTE integration.
100. AXAI integration.
101. AXGEOSPATIAL integration.
102. AXIDENTITY integration.
103. AXSECURITY integration.
104. Native APIs.
105. Formal invariants.
106. Compiler integration.
107. Performance architecture.

---

# 730.137 — Definition of Done

```text
BOOTSTRAP-730
STATUS: COMPLETE / FROZEN

AXMEDIA
 ├── Audio Runtime
 ├── Image Runtime
 ├── Video Runtime
 ├── Codec Infrastructure
 ├── Container Infrastructure
 ├── Capture Runtime
 ├── Playback Runtime
 ├── Timeline Runtime
 ├── Non-Destructive Editing
 ├── Media Pipeline
 ├── Real-Time Processing
 ├── Streaming
 ├── Recording
 ├── Subtitle / Caption Runtime
 ├── Spatial Audio
 ├── Speech Integration
 ├── Media AI Integration
 ├── GPU / DSP Acceleration
 ├── Zero-Copy Media Buffers
 ├── Media Indexing
 ├── Media Provenance
 ├── Media Security
 ├── Distributed Media Processing
 ├── Media Simulation
 └── Media Digital Twin
```

**BOOTSTRAP-730 / AXMEDIA — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-731 — AXGRAPHICS

**Native Graphics & Rendering Runtime — 2D/3D primitives, GPU command model, rendering pipeline, shaders, materials, textures, meshes, cameras, lighting, scene graph, render graph, compute shaders, GPU memory, synchronization, frame scheduling, rasterization, ray tracing, global illumination, post-processing, UI rendering primitives, font rendering, vector graphics, animation, particle systems, physics-render integration, XR/display integration, deterministic rendering, distributed rendering, graphics debugging & Graphics Runtime 5.0.**