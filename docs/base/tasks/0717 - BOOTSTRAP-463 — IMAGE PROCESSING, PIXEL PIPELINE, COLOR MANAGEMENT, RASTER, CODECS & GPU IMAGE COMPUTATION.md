# BOOTSTRAP-463 — IMAGE PROCESSING, PIXEL PIPELINE, COLOR MANAGEMENT, RASTER, CODECS & GPU IMAGE COMPUTATION

**Trạng thái: COMPLETED / LOCKED**

463 xây dựng image foundation độc lập nhưng interoperable với **458 Numeric/SIMD, 459 GPU, 460 Graphics, 461 Audio, 462 Media, 455 Storage**.

Mục tiêu là đủ thấp để xây image library/texture engine/CV preprocessing, đồng thời đủ cao để xây **image editor, texture painter, compositing engine, thumbnailer, scientific image processing** mà không đưa toàn bộ graphics/media stack vào executable.

---

# 463.1 — Kiến trúc

```text
Axiom Core
    ↓
Numeric / SIMD 458
    ↓
Memory / Ownership
    ↓
IMAGE CORE
    ├── Image
    ├── ImageView
    ├── PixelFormat
    ├── PixelPlane
    ├── ColorSpace
    ├── ColorProfile
    ├── HDR
    ├── Raster
    ├── Transform
    ├── Composite
    ├── Filter
    ├── Convolution
    ├── Morphology
    ├── Histogram
    ├── Codec
    ├── ImageSequence
    ├── GPUImage
    └── ImageGraph
```

Module:

```text
image-core
image-pixel
image-layout
image-color
image-profile
image-hdr
image-raster
image-transform
image-composite
image-filter
image-convolution
image-morphology
image-histogram
image-codec
image-file
image-sequence
image-gpu
image-graph
image-texture
image-analysis
```

---

# 463.2 — Image object

Canonical abstraction:

```text
struct Image<T> {
    storage: ImageStorage
    format: PixelFormat
    width: usize
    height: usize
    layout: ImageLayout
    color: ColorInfo
}
```

`T` không nhất thiết phải xuất hiện ở runtime representation; typed pixel access có thể được monomorphize.

---

# 463.3 — ImageView

Non-owning view:

```text
ImageView {
    planes[]
    width
    height
    format
}
```

Không copy dữ liệu.

---

# 463.4 — Ownership

`Image` sở hữu storage.

`ImageView` không sở hữu storage.

---

# 463.5 — Mutable view

```text
ImageViewMut
```

cho phép chỉnh sửa tại chỗ khi ownership/aliasing contract cho phép.

---

# 463.6 — Pixel format

Pixel format mô tả:

```text
channels
channel_types
channel_bits
packing
planes
subsampling
alpha
endianness
```

---

# 463.7 — Channel types

Foundation hỗ trợ:

```text
u8
u16
u32
i8
i16
f16
f32
f64
```

---

# 463.8 — Common formats

Ví dụ:

```text
Gray8
Gray16
RGB8
RGBA8
BGRA8
RGB16
RGBA16
RGBA16F
RGBA32F
```

---

# 463.9 — Planar formats

Ví dụ:

```text
YUV420P
YUV422P
YUV444P
```

---

# 463.10 — Packed formats

Ví dụ:

```text
RGB565
RGB10A2
R11G11B10F
```

---

# 463.11 — Alpha

Alpha semantics phải chỉ rõ:

```text
None
Straight
Premultiplied
```

---

# 463.12 — No implicit alpha assumption

`RGBA8` không tự động đồng nghĩa với premultiplied alpha.

---

# 463.13 — Premultiplied alpha

Compositing operations có thể yêu cầu premultiplied representation.

---

# 463.14 — Alpha conversion

Straight ↔ premultiplied là operation explicit.

---

# 463.15 — Channel ordering

RGB/BGR/RGBA/BGRA là những format khác nhau.

Không được tự đảo channel.

---

# 463.16 — Bit depth

Bit depth là property của format, không phải color space.

---

# 463.17 — Integer normalization

API phải phân biệt:

```text
raw integer
normalized [0,1]
```

---

# 463.18 — Floating pixel

Floating-point pixel không mặc định bị clamp `[0,1]`.

---

# 463.19 — HDR linear values

Linear-light values có thể vượt `[0,1]`.

---

# 463.20 — Pixel access

API:

```text
pixel(x, y)
set_pixel(x, y, value)
```

có bounds checking trong safe API.

---

# 463.21 — Unchecked access

Low-level:

```text
unsafe pixel_unchecked(...)
```

---

# 463.22 — Stride

Mỗi row có thể có padding.

---

# 463.23 — Negative stride

External image buffers có thể có negative stride nếu adapter hỗ trợ.

---

# 463.24 — Alignment

SIMD/GPU alignment được biểu diễn explicit.

---

# 463.25 — Image origin

Image metadata xác định origin:

```text
TopLeft
BottomLeft
```

---

# 463.26 — No hidden vertical flip

Import/export không tự lật image nếu metadata không yêu cầu.

---

# 463.27 — Tiling

Image storage có thể:

```text
Linear
Tiled
BlockCompressed
OpaqueGPU
```

---

# 463.28 — Tile layout

Tile dimensions và addressing được encapsulate.

---

# 463.29 — Sparse image

Sparse/tiled virtual image là optional advanced storage.

---

# 463.30 — Huge images

Dimensions phải được validate trước khi tính:

```text
width × height × stride
```

để tránh overflow.

---

# 463.31 — Image allocation

Allocation explicit theo 423.

---

# 463.32 — Allocation overflow

Image creation phải reject nếu kích thước storage overflow.

---

# 463.33 — Lazy image

Image có thể đại diện computation graph chưa materialize.

---

# 463.34 — Materialization

Explicit:

```text
image.materialize()
```

---

# 463.35 — Copy-on-write

Có thể là optimization/library feature, nhưng không được làm thay đổi semantics ownership.

---

# 463.36 — Subimage

Subimage có thể tạo `ImageView` không copy.

---

# 463.37 — Crop

Crop có thể trả view nếu geometry/layout cho phép.

---

# 463.38 — Clone

Deep copy phải explicit.

---

# 463.39 — Image identity

Source/storage identity được tách khỏi pixel content hash.

---

# 463.40 — Content hash

Hash toàn bộ logical image có thể dùng cho cache.

---

# 463.41 — Color model

Color information:

```text
ColorInfo {
    primaries
    transfer
    matrix
    range
    white_point
}
```

---

# 463.42 — Color spaces

Foundation phải hỗ trợ các khái niệm:

```text
sRGB
Display P3
BT.709
BT.2020
scRGB
```

---

# 463.43 — Linear RGB

Linear RGB là representation riêng với gamma-encoded RGB.

---

# 463.44 — Gamma

Không gọi mọi transfer function là "gamma".

Transfer function phải được mô tả chính xác.

---

# 463.45 — White point

Color-space conversion phải bảo toàn/biến đổi white point theo profile.

---

# 463.46 — Chromatic adaptation

Có thể hỗ trợ:

```text
Bradford
CAT02
```

và các adaptation method khác.

---

# 463.47 — Color conversion

API:

```text
convert_color(image, destination_space)
```

---

# 463.48 — Explicit conversion

Color conversion là operation observable trong image graph.

---

# 463.49 — No silent conversion

Image APIs không tự chuyển color space trừ khi contract của API nói rõ.

---

# 463.50 — ICC profile

Image có thể chứa ICC profile.

---

# 463.51 — Profile object

```text
ColorProfile {
    data
    identity
    version
}
```

---

# 463.52 — ICC parsing

ICC parser là untrusted-input parser.

---

# 463.53 — Profile validation

Profile phải được validate trước khi sử dụng.

---

# 463.54 — Profile transform

Profile transform có thể được CPU hoặc GPU thực hiện.

---

# 463.55 — Profile cache

Transform computation có thể cache.

---

# 463.56 — Profile provenance

Output có thể ghi profile transformation provenance.

---

# 463.57 — HDR

HDR image phải biểu diễn được:

```text
high dynamic range
wide gamut
transfer function
```

---

# 463.58 — HDR metadata

Hỗ trợ metadata từ 462 khi image là video frame.

---

# 463.59 — PQ

PQ là transfer function riêng.

---

# 463.60 — HLG

HLG là transfer function riêng.

---

# 463.61 — SDR conversion

HDR→SDR là explicit tone-mapping operation.

---

# 463.62 — Tone mapping

Ví dụ:

```text
Reinhard
ACES-like
Filmic
CustomCurve
```

là library algorithms, không phải semantics bắt buộc.

---

# 463.63 — Tone-map parameters

Phải được lưu trong operation/configuration để reproducibility.

---

# 463.64 — Gamut mapping

Wide-gamut→narrow-gamut là explicit operation.

---

# 463.65 — Clipping

Clipping và gamut mapping không được đánh đồng.

---

# 463.66 — Dithering

Dithering là explicit export/conversion option.

---

# 463.67 — Quantization

Bit-depth reduction là explicit.

---

# 463.68 — Color pipeline

Canonical pipeline:

```text
Decode
 ↓
Interpret Source Color
 ↓
Convert to Working Space
 ↓
Linearize if required
 ↓
Process
 ↓
Tone/Gamut Map
 ↓
Convert Output Space
 ↓
Quantize
 ↓
Encode
```

---

# 463.69 — Working space

Image graph có thể chỉ định working color space.

---

# 463.70 — Scene-linear

Scene-linear processing profile được hỗ trợ.

---

# 463.71 — Display-referred

Display-referred workflow được hỗ trợ.

---

# 463.72 — Color intent

Transform có thể chỉ định intent.

---

# 463.73 — Color pipeline determinism

Deterministic profile phải cố định relevant transform parameters.

---

# 463.74 — Raster coordinate

Canonical coordinate:

```text
x: horizontal
y: vertical
```

---

# 463.75 — Pixel center

Pixel-center convention phải được định nghĩa trong raster operations.

---

# 463.76 — Sampling

Sampling operations phải chỉ rõ filter.

---

# 463.77 — Resize

```text
resize(image, width, height, filter)
```

---

# 463.78 — Resize filters

Có thể hỗ trợ:

```text
Nearest
Linear
Bilinear
Bicubic
Lanczos
Area
```

---

# 463.79 — Crop

Crop geometry được biểu diễn bằng integer hoặc subpixel rectangle tùy operation.

---

# 463.80 — Rotate

90° rotations có thể dùng layout-only optimization khi phù hợp.

---

# 463.81 — Arbitrary rotation

Arbitrary angle rotation cần resampling.

---

# 463.82 — Affine transform

Foundation:

```text
Transform2D
```

---

# 463.83 — Perspective transform

Homography/perspective transform là optional raster operation.

---

# 463.84 — Sampling border

Border modes:

```text
Clamp
Repeat
Mirror
Constant
Transparent
```

---

# 463.85 — Coordinate precision

Transform engine có thể dùng `f32` hoặc `f64` tùy profile.

---

# 463.86 — Rasterization

Image foundation cung cấp primitive rasterization:

```text
line
rectangle
circle
polygon
path
```

---

# 463.87 — Anti-aliasing

Anti-aliasing là explicit raster mode.

---

# 463.88 — Coverage

Coverage có thể được biểu diễn fractional.

---

# 463.89 — Compositing

Canonical Porter-Duff style operations:

```text
Source
Destination
SourceOver
DestinationOver
SourceIn
SourceOut
SourceAtop
Xor
Clear
Copy
```

---

# 463.90 — Blend modes

Higher-level blend modes:

```text
Multiply
Screen
Overlay
Darken
Lighten
Difference
Add
Subtract
```

là library operations.

---

# 463.91 — Premultiplied compositing

Core compositing pipeline nên ưu tiên premultiplied representation để tránh artifact.

---

# 463.92 — Blend precision

Blend operations phải xác định intermediate precision.

---

# 463.93 — Integer blend

Integer arithmetic có defined rounding semantics.

---

# 463.94 — Float blend

Floating operations phải tuân theo FP mode từ 458.

---

# 463.95 — Layer

Layer abstraction:

```text
Image
Mask
Opacity
Transform
BlendMode
```

---

# 463.96 — Mask

Mask có thể là:

```text
binary
u8
f16
f32
```

---

# 463.97 — Alpha mask

Mask có thể điều khiển alpha hoặc effect intensity.

---

# 463.98 — Image filter

Filter API:

```text
trait ImageFilter {
    fn process(self, input: ImageView) -> Image
}
```

---

# 463.99 — In-place filters

Chỉ cho phép nếu filter có explicit alias-safe contract.

---

# 463.100 — Filter graph

Multiple filters có thể được fused.

---

# 463.101 — Convolution

Generic 1D/2D convolution.

---

# 463.102 — Kernel

```text
Kernel<T> {
    width
    height
    coefficients[]
}
```

---

# 463.103 — Separable convolution

Planner có thể tách kernel 2D thành hai 1D passes.

---

# 463.104 — SIMD convolution

458 SIMD được sử dụng khi layout cho phép.

---

# 463.105 — GPU convolution

459 compute backend có thể chạy convolution.

---

# 463.106 — Gaussian blur

Gaussian blur là standard library operation.

---

# 463.107 — Box blur

Box blur có implementation optimized.

---

# 463.108 — Sharpen

Sharpening là convolution/filter operation.

---

# 463.109 — Edge detection

Foundation có thể cung cấp:

```text
Sobel
Scharr
Prewitt
Laplacian
```

---

# 463.110 — Morphology

Operations:

```text
Erode
Dilate
Open
Close
```

---

# 463.111 — Structuring element

Có thể là:

```text
rectangle
ellipse
custom mask
```

---

# 463.112 — Threshold

Explicit threshold operation.

---

# 463.113 — Histogram

Histogram hỗ trợ configurable bins/range/channel.

---

# 463.114 — Histogram accumulation

Có thể chạy song song/SIMD.

---

# 463.115 — Statistics

Image analysis:

```text
min
max
mean
variance
histogram
percentile
```

---

# 463.116 — Per-channel statistics

Statistics có thể tính riêng từng channel.

---

# 463.117 — Region statistics

ROI statistics không cần copy image.

---

# 463.118 — Integral image

Foundation có thể cung cấp summed-area/integral image.

---

# 463.119 — Connected components

Có thể là image-analysis library feature.

---

# 463.120 — Feature extraction

CV algorithms nằm ngoài image core nhưng dùng ImageView.

---

# 463.121 — Image graph

```text
Source
 ↓
Decode
 ↓
ColorConvert
 ↓
Resize
 ↓
Filter
 ↓
Composite
 ↓
Encode
```

---

# 463.122 — Typed graph edges

Edges có type:

```text
Image
ImageView
GPUImage
Mask
Scalar
Metadata
```

---

# 463.123 — Format negotiation

Graph có thể chọn pixel format tối ưu giữa các node.

---

# 463.124 — Conversion insertion

Planner có thể insert:

```text
FormatConvert
ColorConvert
Upload
Download
```

---

# 463.125 — Observable conversion

Inserted operations phải xuất hiện trong graph diagnostics.

---

# 463.126 — Graph fusion

Các operation có thể fuse nếu semantics không đổi.

---

# 463.127 — Example fusion

```text
Resize
+
ColorConvert
+
Premultiply
```

có thể thành một GPU/CPU kernel.

---

# 463.128 — Fusion correctness

Fusion không được thay đổi kết quả trong deterministic/strict mode ngoài sai số được specification cho phép.

---

# 463.129 — Lazy evaluation

Graph có thể lazy.

---

# 463.130 — Eager evaluation

Caller có thể yêu cầu materialization.

---

# 463.131 — CPU backend

Reference backend sử dụng Axiom CPU/SIMD.

---

# 463.132 — GPU backend

GPU backend sử dụng 459.

---

# 463.133 — GPU image

GPU image abstraction:

```text
GpuImage {
    device
    format
    dimensions
    usage
    resource
}
```

---

# 463.134 — GPU usage

Usage flags:

```text
Sampled
Storage
RenderTarget
TransferSrc
TransferDst
```

---

# 463.135 — GPU image view

Subresource view:

```text
Mip
Layer
Plane
Format
```

---

# 463.136 — Synchronization

GPU image access uses explicit synchronization from 459.

---

# 463.137 — CPU mapping

GPU image may be mapped/read back if backend permits.

---

# 463.138 — Readback

GPU→CPU readback is explicit.

---

# 463.139 — Upload

CPU→GPU upload is explicit.

---

# 463.140 — Persistent GPU processing

Multiple image operations should remain GPU-resident when possible.

---

# 463.141 — Texture interoperability

Image ↔ Graphics texture conversion must avoid copies when resource-compatible.

---

# 463.142 — Video interoperability

462 `VideoFrame` can be converted to Image/ImageView without copy when compatible.

---

# 463.143 — Audio independence

Image foundation does not depend on 461.

---

# 463.144 — Media independence

Image core does not require 462 codecs.

---

# 463.145 — Texture semantics

Texture-specific concepts:

```text
mipmaps
array layers
cube faces
compression
```

---

# 463.146 — Mipmaps

Image can represent mip chains.

---

# 463.147 — Mip generation

Mip generation is explicit.

---

# 463.148 — Mip filter

Mipmap generation may use box, triangle, Kaiser or custom filters.

---

# 463.149 — Texture arrays

Optional image storage supports layers.

---

# 463.150 — Cubemaps

Six-face image collections can be represented without forcing graphics dependency into Image Core.

---

# 463.151 — Block compression

Image foundation may represent:

```text
BC
ETC
ASTC
```

as opaque/block-compressed formats.

---

# 463.152 — Compressed pixel access

Random arbitrary pixel mutation may require decompression.

---

# 463.153 — Lossy codecs

Codec API must distinguish lossy from lossless.

---

# 463.154 — Codec interface

```text
trait ImageDecoder
trait ImageEncoder
```

---

# 463.155 — Decoder

```text
decode(source) -> Result<Image, ImageError>
```

---

# 463.156 — Streaming decode

Large images can decode progressively if codec supports it.

---

# 463.157 — Incremental decode

Decoder state is explicit and owns its buffers.

---

# 463.158 — Encoder

```text
encode(image, destination, options)
```

---

# 463.159 — Encode options

Quality/bitrate/compression settings are codec-specific.

---

# 463.160 — Codec capabilities

Applications can query:

```text
formats
bit depths
alpha
metadata
lossless
progressive
animation
```

---

# 463.161 — Common image codecs

Ecosystem/provider implementations may support:

```text
PNG
JPEG
WebP
AVIF
TIFF
BMP
GIF
QOI
OpenEXR
```

Không codec nào bắt buộc phải nằm trong core runtime.

---

# 463.162 — Codec/container distinction

Image file format can combine:

```text
container
codec
metadata
```

nhưng API phải giữ các khái niệm riêng khi cần.

---

# 463.163 — PNG

Lossless raster codec/container.

---

# 463.164 — JPEG

Lossy raster codec.

---

# 463.165 — WebP

Codec/container provider.

---

# 463.166 — AVIF

Codec/container provider.

---

# 463.167 — OpenEXR

High-dynamic-range image format provider.

---

# 463.168 — Animated images

Animation represented as:

```text
ImageSequence
```

---

# 463.169 — ImageSequence

```text
ImageSequence {
    frames
    timestamps
    durations
}
```

---

# 463.170 — Variable frame duration

Supported.

---

# 463.171 — Image sequence streaming

Sequence decoder need not materialize every frame.

---

# 463.172 — Sequence random access

Optional index.

---

# 463.173 — Image metadata

Metadata categories:

```text
Exif
XMP
ICC
Orientation
Camera
CaptureTime
Custom
```

---

# 463.174 — Metadata separation

Pixel data and metadata have separate representations.

---

# 463.175 — Metadata preservation

Transform may preserve metadata where semantically valid.

---

# 463.176 — Metadata invalidation

Operations such as crop/resize may invalidate specific metadata.

Tooling should identify affected fields.

---

# 463.177 — EXIF orientation

Import may expose orientation metadata without immediately modifying pixels.

---

# 463.178 — Metadata normalization

Explicit operation may bake orientation into pixels.

---

# 463.179 — Privacy

Metadata stripping must be explicit.

---

# 463.180 — Metadata security

Metadata parsers are untrusted input.

---

# 463.181 — Image file security

All image decoders are untrusted-input boundaries.

---

# 463.182 — Dimension validation

Validate dimensions before allocation.

---

# 463.183 — Memory budget

Decoder receives optional memory budget.

---

# 463.184 — Decode limits

Possible limits:

```text max_width
max_height
max_pixels
max_frames
max_metadata_bytes
max_output_bytes
```

---

# 463.185 — Decompression bomb protection

Decoder must not blindly allocate based on attacker-controlled dimensions.

---

# 463.186 — Integer overflow

All storage-size calculations checked.

---

# 463.187 — Recursion limits

Recursive formats/parsers require depth limits.

---

# 463.188 — Malformed metadata

Invalid metadata returns structured error.

---

# 463.189 — Fuzzing

Every bundled parser/decoder is fuzzable.

---

# 463.190 — Sandbox

High-risk third-party codecs may run out-of-process/WASM.

---

# 463.191 — Error model

Uses 425:

```text
Result<Image, ImageError>
```

---

# 463.192 — Error categories

```text
InvalidFormat
UnsupportedFormat
CorruptData
ResourceLimit
IoError
ColorError
GpuError
CodecError
Cancelled
```

---

# 463.193 — Partial decode

If supported, partial result must be explicitly marked incomplete.

---

# 463.194 — No fake completeness

Decoder cannot report complete image when required data was unavailable.

---

# 463.195 — Cancellation

Long image operations support cooperative cancellation.

---

# 463.196 — Parallel processing

Independent tiles/rows/channels can execute concurrently.

---

# 463.197 — Deterministic parallelism

Deterministic mode defines reduction ordering where floating-point accumulation is involved.

---

# 463.198 — Threading

Image library does not create hidden worker threads.

---

# 463.199 — Executor integration

Optional parallel execution uses 424 abstractions.

---

# 463.200 — Memory pools

Image processing can use arena/pool allocators from 423.

---

# 463.201 — Scratch buffers

Filters may reuse caller-provided scratch storage.

---

# 463.202 — Realtime image processing

Optional `@realtime` restrictions can reuse 461's real-time contract where applicable.

---

# 463.203 — No mandatory allocation

Pure image views/operations may operate allocation-free where API allows.

---

# 463.204 — In-place processing

Explicit in-place APIs avoid hidden temporary images.

---

# 463.205 — Temporary elimination

Optimizer can eliminate temporary buffers when safe.

---

# 463.206 — Tile processing

Large images may be processed tile-by-tile.

---

# 463.207 — Streaming tile pipeline

```text
Decode tile
 ↓
Process
 ↓
Encode/write
```

without full-image materialization where format permits.

---

# 463.208 — Out-of-core images

Images larger than RAM can use 455-backed tiled storage.

---

# 463.209 — Memory mapping

Large raw images can use memory-mapped storage.

---

# 463.210 — Mapped lifetime

Mapped image views obey 455 mapping lifetime.

---

# 463.211 — AI tooling

446 exposes:

```text
image dimensions
format
layout
color space
profile
graph
memory domain
GPU transfers
codec
metadata
cache
```

---

# 463.212 — Explain conversion

AI can query:

```text
why was RGB8 converted to RGBA16F?
```

---

# 463.213 — Explain allocation

AI can query why a temporary image was materialized.

---

# 463.214 — Explain GPU transfer

AI can identify CPU↔GPU synchronization and copies.

---

# 463.215 — Explain color transform

AI can identify source profile, destination profile and transform.

---

# 463.216 — Explain cache

AI can inspect image graph/cache invalidation.

---

# 463.217 — Image provenance

Derived image may record:

```text source
operations
parameters
software version
color transform
```

---

# 463.218 — Reproducible processing

Deterministic image graph stores all relevant processing parameters.

---

# 463.219 — Exact vs approximate

Algorithms can declare:

```text Exact
Approximate
DeviceDependent
```

---

# 463.220 — GPU numerical variance

GPU result differences must be documented where floating-point execution differs.

---

# 463.221 — Benchmark dimensions

Measure separately:

```text decode throughput
encode throughput
pixels/sec
latency
memory
allocations
CPU utilization
SIMD utilization
GPU utilization
VRAM
CPU↔GPU copies
```

---

# 463.222 — Filter benchmarks

Benchmark each filter independently.

---

# 463.223 — Color benchmark

Color transforms measured separately.

---

# 463.224 — Codec benchmark

Codec benchmarks record codec/profile/quality/format.

---

# 463.225 — GPU benchmark

Record GPU/device/backend.

---

# 463.226 — No aggregate image score

No universal image performance/quality score.

---

# 463.227 — Testing

Tests include:

```text pixel layout
stride
channel order
alpha
color conversion
HDR
resize
crop
rotation
blend
filter
convolution
metadata
codec
sequence
GPU interoperability
```

---

# 463.228 — Reference images

Small canonical test images:

```text solid
gradient
checkerboard
alpha pattern
HDR ramp
color chart
noise
```

---

# 463.229 — Exact tests

Use exact comparison where mathematically appropriate.

---

# 463.230 — Tolerance tests

Floating-point/color operations may use explicitly documented tolerances.

---

# 463.231 — Perceptual tests

Optional metrics for lossy processing.

---

# 463.232 — Round-trip tests

```text encode
 ↓
decode
 ↓
validate
```

---

# 463.233 — Metadata round-trip

Codec tests verify supported metadata preservation.

---

# 463.234 — Fuzz corpus

Keep minimized malformed-image corpus.

---

# 463.235 — Differential testing

Compare independent decoder implementations where available and legally usable.

---

# 463.236 — GPU/CPU equivalence

Compare CPU/GPU results under defined numerical tolerance.

---

# 463.237 — Image graph tests

Verify graph optimization/fusion preserves semantics.

---

# 463.238 — Cache tests

Verify cache invalidation after source/config changes.

---

# 463.239 — Security tests

Resource exhaustion, malformed headers, oversized dimensions and metadata attacks.

---

# 463.240 — Implementation order

### Phase 1

```text
Image
ImageView
PixelFormat
Plane
Stride
```

### Phase 2

```text
ColorInfo
ColorSpace
ColorProfile
ColorConversion
```

### Phase 3

```text
Raster
Transform
Crop
Resize
Composite
```

### Phase 4

```text
Filters
Convolution
Morphology
Histogram
Analysis
```

### Phase 5

```text
ImageDecoder
ImageEncoder
PNG/JPEG/etc. providers
```

### Phase 6

```text
ImageGraph
Lazy evaluation
Fusion
Cache
```

### Phase 7

```text
GPUImage
CPU/GPU interoperability
Compute filters
```

### Phase 8

```text
HDR
Advanced color
EXR
Texture/mipmap
Out-of-core image
```

---

# 463.241 — Compiler integration

Image processing requires no new fundamental language semantics.

Nó tận dụng:

```text
458 Numeric/SIMD
459 GPU
423 Ownership
424 Concurrency
431 Comptime
445 Safety
446 Semantic metadata
450 Benchmarking
455 Storage
460 Graphics
462 Media
```

---

# 463.242 — Comptime image operations

Small constant images/tables có thể được tạo bằng `comptime`.

Ví dụ:

```text
const LUT = comptime make_lut()
```

Không được cho phép filesystem/network side effects.

---

# 463.243 — Compile-time generated kernels

`comptime` có thể chuyên biệt hóa:

```text
pixel type
channel count
kernel size
image dimensions
```

---

# 463.244 — Generic image algorithms

Ví dụ:

```text
fn blur<T, const N: usize>(image: ImageView<T>) -> Image<T>
```

được monomorphize khi phù hợp.

---

# 463.245 — Code-size control

Generic image kernels có thể được chia sẻ/outlining/linker dedup theo 426/450.

---

# 463.246 — No mandatory image runtime

Executable chỉ dùng core Axiom không được kéo image subsystem.

---

# 463.247 — No mandatory GPU

CPU-only image application phải hoạt động không cần GPU runtime.

---

# 463.248 — No mandatory codec

Raw image processing không cần link codec libraries.

---

# 463.249 — No mandatory color profile

Basic pixel processing không cần ICC subsystem.

---

# 463.250 — Native implementation

Image engine phải có thể được implement hoàn toàn bằng Axiom.

Không yêu cầu:

```text
LLVM
GCC
Clang
C/C++ runtime
```

---

# 463.251 — FFI

External image codecs/libraries có thể dùng 451.

FFI boundary phải explicit.

---

# 463.252 — Plugin

Codec/filter providers có thể dynamic-load.

---

# 463.253 — Plugin trust

Third-party plugin là foreign code và tuân theo 445.

---

# 463.254 — Plugin ABI

Plugin ABI version độc lập với image API version.

---

# 463.255 — Plugin capabilities

Provider khai báo:

```text formats
operations
GPU support
metadata
threading
allocation
```

---

# 463.256 — No hidden thread

Provider không được tạo background thread mà không khai báo capability/effect.

---

# 463.257 — No hidden allocation

Provider metadata có thể khai báo allocation behavior.

---

# 463.258 — No hidden color conversion

Provider phải khai báo conversion behavior.

---

# 463.259 — No hidden GPU transfer

CPU/GPU transfer phải observable trong graph.

---

# 463.260 — API stability

Image public API và binary codec ABI được version riêng.

---

# 463.261 — Hard invariants

1. Image is not language core.
2. Image is not mandatory runtime.
3. Image ownership follows 423.
4. ImageView is non-owning.
5. Mutable views require valid aliasing.
6. Pixel format is explicit.
7. Channel order is explicit.
8. Channel bit depth is explicit.
9. Numeric representation is explicit.
10. Alpha semantics are explicit.
11. Straight/premultiplied alpha are distinct.
12. Stride is explicit.
13. Alignment is explicit.
14. Plane layout is explicit.
15. Planar and packed formats are distinct.
16. Subsampling is explicit.
17. Image dimensions are validated.
18. Storage-size arithmetic is overflow-safe.
19. Arbitrary floating pixel values are not implicitly clamped.
20. Integer and normalized values are distinct concepts.
21. Color space is distinct from pixel format.
22. Primaries are explicit.
23. Transfer function is explicit.
24. Matrix coefficients are explicit.
25. Range is explicit.
26. White point is explicit where relevant.
27. ICC profiles are explicit metadata.
28. ICC data is treated as untrusted.
29. HDR is explicitly represented.
30. HDR→SDR is an explicit operation.
31. Tone mapping is explicit.
32. Gamut mapping is explicit.
33. Quantization is explicit.
34. Dithering is explicit.
35. No silent color conversion.
36. No silent channel reorder.
37. No silent vertical flip.
38. No silent alpha reinterpretation.
39. Raster coordinate semantics are deterministic.
40. Sampling filter is explicit.
41. Resize is explicit.
42. Crop is explicit.
43. Rotation is explicit.
44. Transform precision is defined.
45. Border behavior is explicit.
46. Compositing semantics are explicit.
47. Blend mode is explicit.
48. Blend precision is defined.
49. Convolution semantics are defined.
50. Filter aliasing requirements are defined.
51. SIMD is an optimization/backend, not a semantic dependency.
52. GPU processing is optional.
53. CPU fallback is possible.
54. GPU image lifetime is deterministic.
55. CPU↔GPU transfer is explicit.
56. Graphics texture interoperability can be zero-copy.
57. Video frame interoperability can be zero-copy.
58. Image codecs are separate from Image Core.
59. Decoder and encoder are separate.
60. Lossless/lossy semantics are explicit.
61. Progressive decoding is explicit.
62. Partial decode cannot masquerade as complete.
63. Image sequences support variable duration.
64. Metadata is separate from pixels.
65. Metadata preservation is format-dependent and explicit.
66. Metadata invalidation is observable.
67. Metadata stripping is explicit.
68. Image files are untrusted input.
69. Decoder dimensions are validated before allocation.
70. Resource limits are supported.
71. Decompression-bomb protection is required.
72. Integer overflow in decoders is forbidden.
73. Recursive parser depth is bounded.
74. Bundled decoders are fuzz targets.
75. Third-party codecs are trust boundaries.
76. High-risk codecs may be sandboxed.
77. Errors use `Result`.
78. Cancellation is cooperative.
79. Image processing does not create hidden threads.
80. Image processing does not require GC.
81. Image processing does not require a borrow checker.
82. Temporary allocations are explicit/optimizable.
83. In-place processing requires alias-safe contracts.
84. Tile processing is supported.
85. Out-of-core processing can use 455.
86. Memory mapping follows 455 lifetime semantics.
87. Image graph edges are typed.
88. Graph format negotiation is explicit.
89. Automatically inserted conversions remain observable.
90. Graph fusion must preserve declared semantics.
91. Lazy evaluation is optional.
92. Materialization is explicit.
93. Cache invalidation is deterministic.
94. Provenance can be preserved.
95. Deterministic profiles define numerical behavior.
96. Device-dependent behavior is identifiable.
97. CPU/GPU numerical differences are documented.
98. Image operations can use comptime specialization.
99. Generic image algorithms use 426 semantics.
100. Image metadata integrates with 446.
101. Image performance integrates with 450.
102. Image storage integrates with 455.
103. Image GPU processing integrates with 459.
104. Image rendering integrates with 460.
105. Video interoperability integrates with 462.
106. Image FFI integrates with 451.
107. Unused image modules are omitted from binaries.
108. Unused codecs are omitted from binaries.
109. GPU image functionality is not linked into CPU-only programs.
110. Axiom does not require external compiler infrastructure to implement image processing.
111. External image libraries remain optional FFI dependencies.
112. Native image processing can be implemented entirely in Axiom.
113. AI can inspect image graph semantics.
114. AI can inspect color transformations.
115. AI can inspect CPU/GPU transfers.
116. AI can inspect allocation behavior.
117. AI can inspect codec/provider capabilities.
118. AI can inspect image provenance.
119. Image benchmark metrics remain independent.
120. No aggregate image quality/performance score is defined.
121. Image operations remain composable.
122. Image representation remains independent from GUI.
123. Image representation remains independent from media containers.
124. Image representation remains independent from any particular GPU API.
125. **Axiom image foundation must support high-performance raster/image/texture processing from raw pixels through GPU pipelines without forcing image, graphics, codec or GPU infrastructure into unrelated native applications.**

**BOOTSTRAP-463 hoàn tất.**

---

# BOOTSTRAP-464 — TEXT ENGINE, UNICODE, SCRIPTING, SHAPING, FONT, LAYOUT & INTERNATIONALIZATION FOUNDATION

Task tiếp theo chuyển từ **pixel-level** sang **text rendering/input**, một foundation quan trọng cho GUI 452, graphics 460, image 463 và media/subtitle 462.

Kiến trúc dự kiến:

```text
Axiom Core
    ↓
UTF-8 / Unicode
    ↓
TEXT FOUNDATION
    ├── Text
    ├── Unicode Scalar
    ├── Grapheme
    ├── Unicode Properties
    ├── Normalization
    ├── Segmentation
    ├── Bidirectional Text
    ├── Script Detection
    ├── Font
    ├── Glyph
    ├── Shaping
    ├── Text Layout
    ├── Line Breaking
    ├── Measurement
    ├── Text Rasterization
    ├── Emoji
    ├── Locale
    ├── Collation
    └── Internationalization
```

Điểm đặc biệt của 464 sẽ là phải giải quyết rõ một vấn đề rất quan trọng với Axiom:

```text
UTF-8 bytes
     ↓
Unicode scalar values
     ↓
grapheme clusters
     ↓
script runs
     ↓
font selection
     ↓
glyph shaping
     ↓
glyph positions
     ↓
line layout
     ↓
raster/GPU
```

và **không được nhầm `byte`, `Unicode character`, `grapheme`, `glyph` là cùng một khái niệm**.

**BOOTSTRAP-464 là task tiếp theo, chưa hoàn tất.**