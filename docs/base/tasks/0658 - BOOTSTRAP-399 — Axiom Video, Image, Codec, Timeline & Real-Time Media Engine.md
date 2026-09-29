# BOOTSTRAP-399 — Axiom Video, Image, Codec, Timeline & Real-Time Media Engine

Sau **398 — Audio, DSP, MIDI & Real-Time Signal Processing**, bước tiếp theo hợp lý là **Video + Image + Media Timeline**.

Axiom hiện đã có gần đủ nền tảng để xây một media engine native:

```text
GUI
OS
I/O
Memory
SIMD
Parallel
GPU
Tensor
Computer Vision
Audio
```

398 xử lý **1 chiều theo thời gian**. 399 mở rộng sang **không gian + thời gian**, đồng thời kết nối trực tiếp với 384 Computer Vision, 385 ML, 390 I/O và 397 GUI/Rendering.

Nguyên tắc chính:

> **Video là một dòng dữ liệu có cấu trúc theo thời gian, không phải một mảng ảnh khổng lồ và cũng không phải một tập hợp object/frame runtime.**

---

# 1. Video không thuộc Core

Core chỉ cần các primitive cần thiết:

```text
Numeric
Tensor
Image
Audio
Stream
Time
Execution
I/O
GPU
SIMD
```

Video là domain layer:

```text
Video
 ├── Frame
 ├── Pixel Format
 ├── Color
 ├── Codec
 ├── Decoder
 ├── Encoder
 ├── Timeline
 ├── Synchronization
 ├── Video Graph
 └── Media Container
```

---

# 2. Video Frame

Frame là logical value/resource:

```text
VideoFrame<T>
```

nhưng representation có thể là:

```text
CPU memory
GPU memory
DMA buffer
mapped memory
external buffer
```

Không được mặc định frame = heap object.

---

# 3. Frame Timestamp

Mỗi frame có:

```text
presentation_time
decode_time
duration
```

không được gộp thành một timestamp.

---

# 4. PTS và DTS

Video codec cần phân biệt:

```text
PTS = Presentation Timestamp
DTS = Decode Timestamp
```

Đặc biệt với B-frame:

```text
decode order != presentation order
```

Compiler/media engine phải giữ distinction này.

---

# 5. Frame Identity

Không dùng physical address làm frame identity.

Có thể có:

```text
FrameId
Generation
```

nhưng frame identity chỉ là logical identity.

---

# 6. Image và VideoFrame

384 định nghĩa:

```text
Image<T, Shape, PixelFormat, ColorSpace, Layout>
```

VideoFrame có thể chứa:

```text
Image
+
Timestamp
+
FrameMetadata
```

---

# 7. Zero-Copy

Nếu decoder trả GPU buffer:

```text
Compressed
   ↓
Decoder
   ↓
GPU Frame
   ↓
Shader / CV / ML
```

không cần:

```text
GPU → CPU → GPU
```

nếu backend cho phép.

---

# 8. Storage Domain

Video reuse storage domain:

```text
HOST
DEVICE
SHARED
LOCAL
EXTERNAL
MAPPED
```

---

# 9. Pixel Format

Cần explicit:

```text
RGB
RGBA
BGR
BGRA
Gray
YUV420
YUV422
YUV444
NV12
P010
```

---

# 10. YUV Planar

Ví dụ YUV420:

```text
Y plane
U plane
V plane
```

không được giả định là một contiguous RGB-like buffer.

---

# 11. Chroma Subsampling

Semantic metadata:

```text
4:4:4
4:2:2
4:2:0
```

và chroma siting phải được xác định khi conversion cần chính xác.

---

# 12. Bit Depth

```text
8-bit
10-bit
12-bit
16-bit
float
```

là format semantics, không chỉ là integer type.

---

# 13. Color Space

384 đã có color semantics.

Video bổ sung:

```text
BT.601
BT.709
BT.2020
DCI-P3
```

và transfer characteristics.

---

# 14. Transfer Function

Phải phân biệt:

```text
Linear
Gamma
sRGB
PQ
HLG
```

Không được compiler tự coi encoded RGB là linear RGB.

---

# 15. HDR

HDR frame cần metadata:

```text
transfer
primaries
matrix
range
mastering metadata
content light level
```

---

# 16. Range

Video YUV/RGB có thể có:

```text
Limited
Full
```

Không được silently đổi semantics.

---

# 17. Color Conversion

Ví dụ:

```text
YUV420 BT.709 limited
        ↓
RGB linear
```

là một semantic pipeline.

Compiler có thể fuse:

```text
decode
→ YUV conversion
→ resize
→ normalization
```

nếu proof cho phép.

---

# 18. Frame Rate

Không nên chỉ dùng:

```text
f64
```

cho frame rate.

Dùng rational:

```text
FrameRate {
    numerator
    denominator
}
```

để biểu diễn chính xác:

```text
24/1
30000/1001
60000/1001
```

---

# 19. Variable Frame Rate

Video stream có thể VFR.

Do đó frame duration phải là property của frame/segment, không phải luôn là `1 / fps`.

---

# 20. Timeline

Timeline là logical mapping:

```text
MediaTime
    ↓
Audio
Video
Subtitle
Metadata
```

---

# 21. Media Clock

Phải phân biệt:

```text
WallClock
AudioClock
VideoClock
MediaClock
DeviceClock
```

398 đã định nghĩa audio clock.

---

# 22. A/V Synchronization

Audio thường là clock master trong playback systems, nhưng đây là **policy**, không phải Core semantic rule.

Có thể chọn:

```text
audio master
video master
external clock
adaptive clock
```

---

# 23. Synchronization Error

Video renderer có thể phát hiện:

```text
video ahead
video behind
```

và policy:

```text
present
drop
repeat
delay
resync
```

---

# 24. Frame Dropping

Dropping frame phải là explicit playback policy.

Không phải compiler optimization.

---

# 25. Frame Repetition

Nếu video thiếu frame:

```text
repeat previous frame
```

có thể là presentation policy.

---

# 26. Video Stream

Conceptual:

```text
Stream<VideoFrame>
```

nhưng implementation có thể sử dụng specialized queue.

---

# 27. Compressed Stream

Không nên decode toàn bộ trước.

Pipeline:

```text
ByteStream
 ↓
Demuxer
 ↓
CompressedPacket
 ↓
Decoder
 ↓
VideoFrame
```

---

# 28. Packet

```text
Packet {
    bytes
    pts
    dts
    duration
    flags
}
```

ownership rõ ràng.

---

# 29. Demuxer

Container:

```text
MP4
MKV
WebM
AVI
MOV
TS
```

có thể có:

```text
Demuxer
```

nhưng không phải class hierarchy bắt buộc.

---

# 30. Container Track

Một media container có thể chứa:

```text
Video Track
Audio Track
Subtitle Track
Metadata Track
```

---

# 31. Track

```text
MediaTrack<T>
```

với type specialization:

```text
VideoTrack
AudioTrack
SubtitleTrack
```

---

# 32. Codec

Codec interface:

```text
trait Decoder {
    fn decode(...)
}
```

concrete:

```text
H264Decoder
H265Decoder
AV1Decoder
VP9Decoder
```

Không cần inheritance.

---

# 33. Dynamic Codec

Nếu codec runtime-loaded:

```text
dyn VideoDecoder
```

dynamic dispatch chỉ xuất hiện tại boundary.

---

# 34. Decoder State

Decoder state:

```text
DecoderState
```

là explicit owning state.

Không hidden global state.

---

# 35. Decoder Reordering

Codec có thể yêu cầu frame reorder buffer.

Compiler/runtime phải biểu diễn:

```text
DecodeOrder
PresentationOrder
```

riêng biệt.

---

# 36. Hardware Decoder

Backend có thể:

```text
CPU
GPU
Video Decode Engine
```

Axiom abstraction không được giả định decoder luôn chạy CPU.

---

# 37. Hardware Encoder

Tương tự:

```text
CPU encoder
GPU encoder
hardware media engine
```

---

# 38. Device Buffer

Hardware decoder có thể trả:

```text
DeviceBuffer<VideoFrame>
```

và renderer dùng trực tiếp.

---

# 39. Frame Mapping

Nếu CPU cần đọc:

```text
device_frame.map()
```

là explicit storage-domain transition.

---

# 40. Mapping Lifetime

Mapped view không được tồn tại sau khi mapping contract kết thúc.

Reuse capability model.

---

# 41. Video Pipeline

Ví dụ:

```text
File
 ↓
Demux
 ↓
Decode
 ↓
Color Convert
 ↓
Resize
 ↓
Computer Vision
 ↓
Tensor
 ↓
GPU
 ↓
Render
```

Axiom phải có khả năng compile/optimize pipeline này.

---

# 42. Pipeline Fusion

Nếu:

```text
Decode → ColorConvert → Resize
```

backend hỗ trợ trực tiếp, compiler có thể chọn fused kernel/backend.

---

# 43. CPU SIMD

384/366 cung cấp:

```text
vec<T,N>
```

để xử lý:

```text
YUV conversion
resize
blur
color transform
```

---

# 44. GPU

397 cung cấp rendering.

367 cung cấp GPU compute.

Video engine kết nối cả hai.

---

# 45. Compute → Render

Ví dụ:

```text
VideoFrame
 ↓
GPU tensor
 ↓
segmentation
 ↓
GPU texture
 ↓
Renderer
```

không cần copy GPU→CPU.

---

# 46. Video → Vision

384 có thể nhận:

```text
VideoFrame
```

trực tiếp.

Không cần API trung gian bắt buộc.

---

# 47. Video → ML

385 nhận:

```text
TensorView
```

từ video frame khi layout compatible.

---

# 48. Frame Batch

ML/video workloads có thể gom:

```text
Frame[0..N]
```

thành tensor batch.

Compiler có thể chọn:

```text
NCHW
NHWC
```

theo backend/layout contract.

---

# 49. Video Preprocessing

Các operation phổ biến:

```text
resize
crop
normalize
letterbox
colorspace conversion
denoise
sharpen
```

có thể fuse.

---

# 50. Video Processing Graph

Giống DSP graph:

```text
Input
 ↓
Decode
 ↓
Resize
 ├→ Detector
 └→ Encoder
```

compiler/runtime có thể xây DAG.

---

# 51. Static Graph

Nếu graph known compile-time:

```text
VideoGraph<T>
```

có thể được specialize mạnh.

---

# 52. Dynamic Graph

Nếu graph runtime:

```text
DynamicVideoGraph
```

dùng runtime scheduling.

---

# 53. Backpressure

Video pipeline phải hỗ trợ:

```text
producer
 ↓
bounded queue
 ↓
consumer
```

Không mặc định unbounded.

---

# 54. Queue Policy

Khi queue đầy:

```text
BLOCK
DROP_OLDEST
DROP_NEWEST
REPLACE
ERROR
```

policy explicit.

---

# 55. Realtime Capture

Camera capture có thể yêu cầu:

```text
@realtime_video
```

với constraints tương tự Audio:

```text
bounded
nonblocking
preallocated
```

---

# 56. Camera Clock

Camera có thể có clock riêng.

Timestamp từ camera phải được preserve.

---

# 57. Camera Capture

Pipeline:

```text
Camera
 ↓
DMA
 ↓
GPU/CPU buffer
 ↓
Vision
```

zero-copy nếu driver/backend hỗ trợ.

---

# 58. DMA Ownership

DMA buffer ownership transition phải giống 390/396:

```text
Device owns
     ↓
CPU owns
```

không được truy cập đồng thời nếu contract không cho phép.

---

# 59. Camera Format Negotiation

Camera có thể expose:

```text
resolution
fps
pixel format
bit depth
color space
```

application chọn configuration.

---

# 60. Format Conversion

Nếu hardware hỗ trợ native format, compiler/backend có thể giữ format đó xuyên pipeline.

Không ép mọi thứ thành RGB.

---

# 61. Subtitle

Subtitle là temporal text stream:

```text
SubtitleCue {
    start
    end
    text
}
```

---

# 62. Subtitle Text

Text dùng Unicode/UTF-8.

Text shaping/rendering reuse GUI engine.

---

# 63. Subtitle Timeline

Subtitle phải sync với:

```text
MediaTime
```

không trực tiếp phụ thuộc wall clock.

---

# 64. Caption Layout

Subtitle renderer có thể dùng:

```text
text shaping
font
layout
GPU render
```

từ 397.

---

# 65. Media Composition

Một timeline có thể chứa:

```text
video
audio
subtitle
image
effect
```

---

# 66. Clip

Clip chỉ là logical interval:

```text
MediaClip {
    source
    start
    duration
    transform
}
```

Không bắt buộc object runtime.

---

# 67. Non-Destructive Editing

Timeline không cần mutate source media.

Chỉ lưu:

```text
source
trim
transform
effect
timing
```

---

# 68. Render Graph

397 render graph có thể consume media graph.

```text
MediaGraph
 ↓
RenderGraph
 ↓
GPU
```

---

# 69. Effects

Video effects:

```text
blur
color grade
sharpen
warp
keying
blend
transition
```

có thể biểu diễn như functions/struct state.

---

# 70. Transition

Ví dụ:

```text
A
 ↓
crossfade
 ↓
B
```

có thể được compile thành GPU kernel/render pass.

---

# 71. Color Grading

Color pipeline:

```text
decode color space
 ↓
linearize
 ↓
grade
 ↓
tone map
 ↓
display transform
```

không được reorder tùy tiện.

---

# 72. Tone Mapping

HDR→SDR là semantic transform:

```text
PQ
 ↓
tone map
 ↓
SDR
```

cần policy.

---

# 73. Frame Cache

Video playback có thể cache frames.

Cache là optimization, không thay đổi semantics.

---

# 74. Memory Budget

Video có thể chiếm RAM/VRAM lớn.

Runtime có thể có:

```text
MemoryBudget
```

và eviction policy.

---

# 75. Cache Eviction

Có thể:

```text
LRU
LFU
deadline-aware
cost-aware
```

nhưng cache không được thay đổi observable media result.

---

# 76. Prefetch

390 đã có prefetch.

Video engine có thể prefetch dựa:

```text
playback direction
seek position
decode dependency
```

---

# 77. Seeking

Seek không đơn giản là byte offset.

Phải tính:

```text
keyframe
decode dependency
presentation time
```

---

# 78. Random Access

Decoder có thể expose:

```text
seek(timestamp)
```

với precision contract:

```text
keyframe
nearest
exact
```

---

# 79. Reverse Playback

Reverse playback thường yêu cầu decode theo dependency rồi present ngược.

Không giả định codec hỗ trợ native reverse decode.

---

# 80. Scrubbing

Editor có thể cần:

```text
fast preview
keyframe decode
lower resolution
proxy media
```

là policy layer.

---

# 81. Proxy

Proxy media:

```text
Original
 ↓
Proxy
```

mapping logical source identity.

---

# 82. Media Cache

Proxy/cache storage phải không làm thay đổi logical source semantics.

---

# 83. Variable Resolution

Timeline có thể chứa clip khác resolution.

Compositor cần explicit transform/scaling.

---

# 84. Pixel Aspect Ratio

Phải phân biệt:

```text
pixel aspect ratio
display aspect ratio
frame dimensions
```

---

# 85. Rotation Metadata

Video có thể có orientation metadata.

Không được tự động bake thành pixel transform nếu điều đó làm thay đổi observable file/export semantics.

---

# 86. Interlaced Video

Có thể có:

```text
progressive
interlaced
```

với field order:

```text
TFF
BFF
```

---

# 87. Deinterlacing

Deinterlace là explicit processing operation.

---

# 88. Frame Rate Conversion

Ví dụ:

```text
24 fps → 60 fps
```

có thể dùng:

```text
duplicate
blend
motion interpolation
```

policy explicit.

---

# 89. Motion Interpolation

Có thể kết nối Computer Vision/ML:

```text
Frame A
Frame B
 ↓
motion estimation
 ↓
intermediate frame
```

---

# 90. Optical Flow

384 đã có optical flow.

Video engine chỉ cung cấp temporal stream semantics.

---

# 91. Audio + Video Composition

Một `MediaTimeline` có thể giữ:

```text
VideoTrack
AudioTrack
SubtitleTrack
```

và map tất cả vào một MediaClock.

---

# 92. Drift Correction

Nếu audio/video clock drift:

```text
resample audio
drop/repeat video
adjust presentation
```

policy explicit.

---

# 93. Media Rate

Playback rate:

```text
0.5x
1x
2x
```

không nhất thiết chỉ scale timestamp; audio pitch/video frame policy cần explicit.

---

# 94. Pause

Pause chỉ ngừng presentation/consumption.

Không nhất thiết destroy decoder state.

---

# 95. Seek

Seek có thể invalidate:

```text
decode buffers
pending frames
presentation queue
```

capability generation phải được cập nhật.

---

# 96. Cancellation

Async decode:

```text
Future<VideoFrame>
```

theo 360–361.

Cancellation không được để stale buffer tiếp tục truy cập tài nguyên.

---

# 97. Media Errors

Phân biệt:

```text
ContainerError
CodecError
CorruptPacket
UnsupportedFormat
DeviceError
TimestampError
EndOfStream
```

---

# 98. Corrupt Frame

Policy:

```text
fail
skip
conceal
repeat
```

phải explicit.

---

# 99. CompilerDB

Bổ sung:

```text
VideoDB
VideoFrameDB
VideoFrameMetadataDB
VideoTimestampDB
VideoPresentationDB
VideoDecodeTimeDB
VideoFrameDurationDB
VideoFrameIdentityDB

VideoFormatDB
VideoPixelFormatDB
VideoBitDepthDB
VideoChromaDB
VideoChromaSitingDB
VideoColorSpaceDB
VideoTransferDB
VideoPrimariesDB
VideoMatrixDB
VideoRangeDB
VideoHdrDB
VideoHdrMetadataDB

VideoRateDB
VideoFrameRateDB
VideoVariableRateDB
VideoTimeBaseDB
VideoClockDB
VideoClockSyncDB

VideoPacketDB
VideoPacketTimestampDB
VideoPacketOrderDB
VideoDemuxDB
VideoTrackDB
MediaContainerDB
MediaTrackDB
MediaMetadataDB

VideoCodecDB
VideoDecoderDB
VideoEncoderDB
VideoCodecStateDB
VideoDecodeOrderDB
VideoPresentationOrderDB
VideoReorderDB
VideoKeyframeDB
VideoSeekDB
VideoRandomAccessDB

VideoHardwareDecoderDB
VideoHardwareEncoderDB
VideoDeviceBufferDB
VideoDmaDB
VideoMappedBufferDB
VideoExternalBufferDB

VideoPipelineDB
VideoGraphDB
VideoGraphNodeDB
VideoGraphEdgeDB
VideoScheduleDB
VideoFusionDB
VideoBufferDB
VideoQueueDB
VideoBackpressureDB
VideoPrefetchDB
VideoCacheDB
VideoMemoryBudgetDB

VideoCaptureDB
CameraDB
CameraDeviceDB
CameraCapabilityDB
CameraConfigDB
CameraClockDB
CameraCaptureDB
CameraFormatNegotiationDB

MediaDB
MediaTimelineDB
MediaClockDB
MediaClipDB
MediaCompositionDB
MediaPlaybackDB
MediaSeekDB
MediaRateDB
MediaSyncDB
MediaDriftDB
MediaProxyDB
MediaCacheDB

SubtitleDB
SubtitleCueDB
SubtitleTimelineDB
SubtitleRenderDB

VideoEffectDB
VideoBlurDB
VideoSharpenDB
VideoColorGradeDB
VideoToneMapDB
VideoTransitionDB
VideoBlendDB
VideoWarpDB
VideoKeyingDB
VideoDeinterlaceDB
VideoFrameRateConvertDB
VideoMotionInterpolationDB

VideoVisionDB
VideoTensorDB
VideoMlDB
VideoGpuDB
VideoSimdDB
VideoParallelDB
VideoRenderDB

VideoErrorDB
VideoRecoveryDB
VideoCostModelDB
VideoOptimizationDB
VideoVerificationDB
```

---

# 100. MIR

```text id="r8v5yl"
VIDEO_FRAME_CREATE
VIDEO_FRAME_VIEW
VIDEO_FRAME_MUT_VIEW
VIDEO_FRAME_TIMESTAMP
VIDEO_FRAME_DURATION

VIDEO_PACKET_CREATE
VIDEO_PACKET_VIEW

VIDEO_DEMUX_BEGIN
VIDEO_DEMUX_NEXT
VIDEO_DEMUX_END

VIDEO_DECODER_CREATE
VIDEO_DECODE
VIDEO_REORDER
VIDEO_SEEK
VIDEO_KEYFRAME

VIDEO_ENCODER_CREATE
VIDEO_ENCODE

VIDEO_DEVICE_DECODE
VIDEO_DEVICE_ENCODE
VIDEO_DEVICE_MAP
VIDEO_DEVICE_UNMAP

VIDEO_CAPTURE_OPEN
VIDEO_CAPTURE_START
VIDEO_CAPTURE_STOP
VIDEO_CAPTURE_NEXT
VIDEO_CAPTURE_TIMESTAMP

VIDEO_COLOR_CONVERT
VIDEO_TONE_MAP
VIDEO_RESIZE
VIDEO_CROP
VIDEO_WARP
VIDEO_BLUR
VIDEO_SHARPEN
VIDEO_COLOR_GRADE
VIDEO_BLEND
VIDEO_TRANSITION
VIDEO_DEINTERLACE
VIDEO_FRAME_RATE_CONVERT

VIDEO_GRAPH_BEGIN
VIDEO_GRAPH_END
VIDEO_GRAPH_NODE
VIDEO_GRAPH_CONNECT
VIDEO_GRAPH_SCHEDULE
VIDEO_GRAPH_FUSE

VIDEO_QUEUE_PUSH
VIDEO_QUEUE_POP
VIDEO_QUEUE_DROP
VIDEO_QUEUE_BACKPRESSURE

VIDEO_PREFETCH
VIDEO_CACHE_LOOKUP
VIDEO_CACHE_INSERT
VIDEO_CACHE_EVICT

MEDIA_TIMELINE_BEGIN
MEDIA_TIMELINE_END
MEDIA_CLIP
MEDIA_SYNC
MEDIA_SEEK
MEDIA_RATE
MEDIA_PAUSE
MEDIA_PRESENT
MEDIA_DROP_FRAME
MEDIA_REPEAT_FRAME

SUBTITLE_CREATE
SUBTITLE_CUE
SUBTITLE_RENDER

VIDEO_TENSOR_VIEW
VIDEO_TENSOR_MUT_VIEW

VIDEO_GPU_UPLOAD
VIDEO_GPU_DOWNLOAD
VIDEO_GPU_PROCESS
VIDEO_GPU_RENDER
```

---

# 101. Proof System

```text id="u0h6cg"
VideoFrameFormatProof
VideoPixelFormatProof
VideoChromaProof
VideoColorSpaceProof
VideoTransferProof
VideoHdrProof

VideoTimestampProof
VideoTimeBaseProof
VideoFrameRateProof
VideoVfrProof
VideoClockProof
VideoClockSyncProof

VideoPacketOwnershipProof
VideoDecodeOrderProof
VideoPresentationOrderProof
VideoReorderProof
VideoSeekProof
VideoKeyframeProof

VideoBufferOwnershipProof
VideoViewLifetimeProof
VideoDmaProof
VideoMappedBufferProof
VideoDeviceOwnershipProof

VideoZeroCopyProof
VideoCopyEliminationProof
VideoLayoutProof
VideoAlignmentProof

VideoGraphProof
VideoGraphDependencyProof
VideoScheduleProof
VideoFusionProof
VideoBufferReuseProof

VideoBackpressureProof
VideoQueueProof
VideoPrefetchProof
VideoCacheProof
VideoMemoryBudgetProof

VideoCaptureProof
CameraFormatProof
CameraTimestampProof
CameraClockProof
CameraDmaProof

VideoColorConversionProof
VideoToneMapProof
VideoResizeProof
VideoWarpProof
VideoEffectProof
VideoTransitionProof

VideoSimdProof
VideoParallelProof
VideoGpuProof
VideoTensorProof
VideoVisionProof

MediaTimelineProof
MediaSyncProof
MediaDriftProof
MediaSeekProof
MediaRateProof

SubtitleTimingProof
SubtitleEncodingProof
SubtitleRenderProof

VideoCodecProof
VideoDecoderProof
VideoEncoderProof
VideoHardwareCodecProof

VideoErrorRecoveryProof
VideoCostModelProof
VideoOptimizationProof
VideoVerificationProof
```

---

# 102. Invariants

### `AVIDEO-01`
VideoFrame phải có timestamp semantics rõ ràng.

### `AVIDEO-02`
PTS và DTS không được đồng nhất.

### `AVIDEO-03`
Decode order và presentation order phải độc lập.

### `AVIDEO-04`
Frame duration phải được preserve trong VFR.

### `AVIDEO-05`
Pixel format phải được preserve khi observable.

### `AVIDEO-06`
Chroma subsampling phải được preserve khi conversion semantics yêu cầu.

### `AVIDEO-07`
Color space phải được preserve qua pipeline.

### `AVIDEO-08`
Transfer function không được bị coi là linear implicit.

### `AVIDEO-09`
HDR metadata phải được preserve nếu observable.

### `AVIDEO-10`
Limited/full range không được bị thay đổi ngầm.

### `AVIDEO-11`
Video buffer ownership phải rõ ràng.

### `AVIDEO-12`
Mapped/device buffer không được truy cập ngoài lifetime contract.

### `AVIDEO-13`
DMA ownership transition phải được verify.

### `AVIDEO-14`
Zero-copy optimization không được thay đổi logical frame semantics.

### `AVIDEO-15`
Pipeline backpressure phải có policy rõ ràng.

### `AVIDEO-16`
Queue overflow không được mặc định biến thành unbounded memory growth.

### `AVIDEO-17`
Frame dropping phải là observable playback policy, không phải compiler optimization.

### `AVIDEO-18`
Graph scheduling phải preserve dependency ordering.

### `AVIDEO-19`
Graph fusion phải preserve numerical/color semantics.

### `AVIDEO-20`
SIMD conversion phải preserve declared numerical contract.

### `AVIDEO-21`
GPU processing phải preserve storage-domain ownership.

### `AVIDEO-22`
CPU↔GPU transfer chỉ được loại bỏ khi zero-copy proof hợp lệ.

### `AVIDEO-23`
Camera timestamp phải preserve source clock semantics.

### `AVIDEO-24`
Camera format negotiation không được giả định một format cố định.

### `AVIDEO-25`
Media timeline phải phân biệt media time và wall clock.

### `AVIDEO-26`
A/V synchronization policy phải explicit.

### `AVIDEO-27`
Seek phải tôn trọng codec decode dependencies.

### `AVIDEO-28`
Subtitle timing phải gắn với MediaTime.

### `AVIDEO-29`
Hardware codec phải không trở thành mandatory runtime dependency.

### `AVIDEO-30`
Chương trình không sử dụng Video/Media subsystem không được kéo theo video runtime.

---

# 103. Kiến trúc quan trọng nhất của 399

Sau task này, Axiom có thể biểu diễn một pipeline kiểu:

```text
┌──────────────┐
│ Camera/File  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ DMA / Buffer │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Decoder      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ VideoFrame   │
└──────┬───────┘
       │
   ┌───┴───────────────┐
   ▼                   ▼
Computer Vision       Render
   │                   │
   ▼                   ▼
Tensor / ML          GPU Texture
   │                   │
   └────────┬──────────┘
            ▼
         Display
```

Trong trường hợp tốt, compiler/backend có thể biến toàn bộ thành:

```text
Camera DMA
    ↓
GPU decode
    ↓
GPU color conversion
    ↓
GPU resize
    ↓
GPU vision kernel
    ↓
GPU ML
    ↓
GPU render
```

mà **không cần GPU → CPU → GPU copy**.

Đây chính là nơi các task **367 + 384 + 385 + 390 + 397 + 398 + 399** bắt đầu hội tụ thành một hệ thống thống nhất thay vì một tập hợp thư viện rời rạc.

Và quan trọng hơn: programmer vẫn chỉ mô tả **logical data + transformations + ownership**, còn compiler quyết định **buffer placement, layout, SIMD, fusion, parallelism, GPU execution và copy elimination**.