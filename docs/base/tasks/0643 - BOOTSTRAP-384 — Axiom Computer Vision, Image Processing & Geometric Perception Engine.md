# BOOTSTRAP-384 — Axiom Computer Vision, Image Processing & Geometric Perception Engine

Sau **383 — Robotics**, bước tự nhiên tiếp theo là **Computer Vision & Image Processing**. Đây là lớp perception, nối trực tiếp camera/sensor với Geometry, Tensor, Signal, Probability, AD và Robotics.

```text
Camera / Image Sensor
        ↓
Image / Video
        ↓
Preprocessing
        ↓
Feature / Segmentation / Detection
        ↓
Geometric Estimation
        ↓
Pose / Depth / Tracking
        ↓
State Estimation
        ↓
Robotics / Control
```

Mục tiêu: Axiom có thể viết vision pipeline ở mức cao nhưng compiler vẫn hạ được xuống **SIMD + parallel + GPU + zero-copy**, không yêu cầu một vision runtime bắt buộc.

---

## 1. Image không chỉ là Tensor

Không nên coi:

```text
Tensor<u8, [H,W,3]>
```

hoàn toàn tương đương với Image.

Image có semantic metadata:

```text
Image<T, Shape, PixelFormat, ColorSpace, Layout>
```

Trong đó:

```text
Shape
PixelFormat
ColorSpace
ChannelOrder
BitDepth
Storage
Layout
```

có thể là compile-time information.

Runtime representation vẫn có thể chỉ là buffer.

---

## 2. Pixel Format

Chuẩn hóa các dạng:

```text
Gray8
Gray16
RGB8
RGBA8
RGB16
RGBA16
RGBF32
YUV420
YUV422
YUV444
Depth16
Depth32F
```

nhưng không hard-code toàn bộ danh sách vào Core.

Pixel format là library/type-level metadata.

---

## 3. Color Space

Phân biệt:

```text
sRGB
LinearRGB
DisplayP3
Rec709
Rec2020
XYZ
Lab
HSV
YCbCr
```

Color space conversion phải là semantic operation.

Đặc biệt:

```text
sRGB → LinearRGB
```

không được coi là bitcast.

---

## 4. Gamma / Transfer Function

Image processing phải phân biệt:

```text
EncodedColor
LinearColor
```

để tránh các phép toán sai trên màu.

Ví dụ blending vật lý nên thực hiện trên linear representation.

---

## 5. Channel Semantics

Không chỉ là index:

```text
pixel[0]
pixel[1]
pixel[2]
```

mà compiler/library có thể biết:

```text
R
G
B
A
Y
Cb
Cr
Depth
```

Điều này cho phép diagnostic tốt hơn và giảm nhầm channel.

---

## 6. Image View

Image view:

```text
ImageView<T>
MutableImageView<T>
```

kế thừa capability model.

Không sở hữu buffer.

Do đó:

```text
crop
slice
channel
ROI
```

có thể zero-copy.

---

## 7. ROI

Region of Interest:

```text
roi(image, rect)
```

trả về view.

Không tạo buffer mới nếu không cần.

Compiler có thể giữ:

```text
base + offset + stride
```

thay vì copy pixels.

---

## 8. Image Layout

Hỗ trợ:

```text
Interleaved
Planar
SemiPlanar
Tiled
Blocked
```

Compiler/backend được phép chọn layout tối ưu.

---

## 9. Layout Conversion

Ví dụ:

```text
RGB interleaved
        ↓
planar RGB
```

là explicit semantic operation.

Không implicit copy chỉ vì API signature khác.

---

## 10. Image Resize

```text
resize(image, width, height)
```

có algorithm:

```text
Nearest
Bilinear
Bicubic
Lanczos
Area
Custom
```

Algorithm là semantic choice.

---

## 11. Resize Numerical Contract

Resize floating-point phải tuân theo numerical contract.

Không được tự động thay:

```text
exact defined interpolation
```

bằng approximate fast implementation nếu contract không cho phép.

---

## 12. Image Warp

Hỗ trợ:

```text
warp_affine
warp_projective
remap
```

dựa trên Geometry 380.

---

## 13. Coordinate Mapping

Pixel coordinate:

```text
(x, y)
```

phải phân biệt:

```text
PixelCenter
PixelCorner
NormalizedCoordinate
CameraCoordinate
WorldCoordinate
```

Đây là nguồn lỗi lớn trong computer vision.

---

## 14. Camera Model

Chuẩn hóa:

```text
PinholeCamera
OrthographicCamera
FisheyeCamera
OmnidirectionalCamera
```

và generic camera model.

---

## 15. Intrinsics

Camera intrinsic parameters:

```text
fx
fy
cx
cy
skew
```

có thể được biểu diễn bằng type:

```text
CameraIntrinsics
```

với units/coordinate semantics.

---

## 16. Extrinsics

Pose:

```text
CameraPose<World, Camera>
```

reuse Geometry frame system.

Không cho phép nhầm:

```text
Camera → World
```

với:

```text
World → Camera
```

nếu type system có đủ thông tin.

---

## 17. Projection

Semantic:

```text
project(camera, point)
```

và:

```text
unproject(camera, pixel, depth)
```

Compiler có thể specialize camera model.

---

## 18. Distortion

Hỗ trợ:

```text
Radial
Tangential
ThinPrism
Fisheye
Custom
```

Calibration model là generic.

---

## 19. Camera Calibration

Các operation:

```text
calibrate_camera
estimate_intrinsics
estimate_distortion
stereo_calibrate
```

có thể sử dụng Optimization + Solver + AD.

---

## 20. Stereo Vision

Stereo camera:

```text
LeftCamera
RightCamera
Baseline
```

có thể sinh:

```text
Disparity
Depth
PointCloud
```

---

## 21. Stereo Geometry

Epipolar geometry:

```text
EssentialMatrix
FundamentalMatrix
Homography
EpipolarLine
```

là typed mathematical structures.

---

## 22. Fundamental Matrix Constraints

Compiler/library có thể kiểm tra shape:

```text
F : 3 × 3
```

và solver đảm bảo rank constraint trong algorithm.

Không cần runtime type hierarchy.

---

## 23. Feature Detection

Chuẩn hóa:

```text
Corner
Edge
Blob
Keypoint
```

Algorithms có thể gồm:

```text
Harris
FAST
ShiTomasi
```

và library extensions.

---

## 24. Feature Descriptor

```text
Descriptor<T, D>
```

với:

```text
ORB
BRIEF
SIFT-like
Custom
```

Không cần inheritance.

---

## 25. Feature Matching

```text
match(descriptor_a, descriptor_b)
```

có thể dùng:

```text
L2
L1
Hamming
Cosine
Custom
```

Metric là generic.

---

## 26. Geometric Verification

Feature matches không tự động được coi là valid geometry.

Có:

```text
RANSAC
MAGSAC-like
LMedS
```

để estimate robust model.

---

## 27. RANSAC

RANSAC tích hợp Probability 376:

```text
sample
hypothesis
score
consensus
```

RNG phải explicit.

Parallel RANSAC có thể split RNG streams.

---

## 28. Edge Detection

Semantic:

```text
gradient
sobel
scharr
laplacian
canny
```

Các kernels thường rất phù hợp SIMD/GPU.

---

## 29. Image Filtering

Chuẩn hóa:

```text
Gaussian
Box
Median
Bilateral
Morphological
CustomKernel
```

Compiler có thể fuse kernel pipeline.

---

## 30. Separable Filter

Gaussian 2D:

```text
Kx × Ky
```

có thể lower thành:

```text
horizontal pass
+
vertical pass
```

giảm computational cost.

---

## 31. Convolution Optimization

Compiler có thể chọn:

```text
Direct
Separable
FFT
Winograd
GPU
SIMD
```

dựa trên:

```text
kernel size
image size
hardware
numerical contract
```

---

## 32. Integral Image

Semantic primitive:

```text
integral_image(image)
```

phục vụ:

- box filter;
- Haar-like features;
- fast region statistics.

---

## 33. Morphology

Operations:

```text
Erode
Dilate
Open
Close
Gradient
TopHat
BlackHat
```

với arbitrary structuring element.

---

## 34. Thresholding

```text
threshold
adaptive_threshold
otsu
```

kết quả có thể là:

```text
Mask
```

thay vì generic `bool tensor`.

---

## 35. Mask

`Mask<H,W>` có semantic boolean image.

Có thể lower thành:

```text
bitmask
SIMD mask
GPU predicate
```

thay vì byte-per-pixel bool.

---

## 36. Connected Components

```text
connected_components(mask)
```

trả về logical labels.

Có thể parallelize bằng:

```text
union-find
scan
tile merge
```

---

## 37. Segmentation

Phân biệt:

```text
BinaryMask
LabelMap
SemanticMask
InstanceMask
```

để tránh nhầm semantics.

---

## 38. Contours

Contour là geometric structure:

```text
Contour<Point2>
```

có thể hỗ trợ:

```text
area
perimeter
simplify
convex_hull
bounding_box
```

Geometry engine xử lý phần hình học.

---

## 39. Bounding Box

```text
AABB2
AABB3
OBB2
OBB3
```

reuse Geometry.

Vision không tạo một box type riêng nếu semantic identical.

---

## 40. Optical Flow

```text
OpticalFlow
```

có thể hỗ trợ:

```text
LucasKanade
HornSchunck
DenseFlow
SparseFlow
```

---

## 41. Tracking

Tracking abstraction:

```text
Track<State, Measurement>
```

kết hợp:

```text
Signal
Probability
State Estimation
Geometry
```

---

## 42. Kalman Tracking

Object tracking có thể dùng:

```text
Kalman
EKF
UKF
Particle
```

đã có infrastructure từ 382/376.

Không duplicate estimator implementations.

---

## 43. Multi-object Tracking

Track management:

```text
Detection
Association
TrackUpdate
TrackBirth
TrackDeath
```

Association có thể dùng:

```text
Hungarian
Greedy
Auction
```

---

## 44. Depth

Depth representation:

```text
DepthMap
```

phải có semantic:

```text
distance along optical axis
range
inverse depth
disparity
```

Không coi chúng là cùng một `f32`.

---

## 45. Point Cloud

```text
PointCloud<T, Frame>
```

là collection geometry-aware.

Có thể chứa:

```text
position
normal
color
intensity
timestamp
```

nhưng layout configurable.

---

## 46. Point Cloud View

Không copy:

```text
PointCloudView
```

có thể được tạo từ sensor DMA/device buffer.

---

## 47. Point Cloud Operations

```text
voxel_downsample
nearest_neighbor
radius_search
normal_estimation
registration
segmentation
```

---

## 48. Spatial Search

Reuse Geometry spatial structures:

```text
KDTree
Octree
BVH
UniformGrid
```

không duplicate implementation.

---

## 49. ICP

Point cloud registration:

```text
ICP
```

có các stages:

```text
correspondence
distance
robust weighting
transform estimation
update
```

có thể vectorize/parallelize.

---

## 50. Pose Estimation

Vision pose estimation:

```text
PnP
EssentialMatrix
Homography
StereoPose
```

output:

```text
Pose<Camera, Object>
```

với frame semantics.

---

## 51. PnP

```text
solve_pnp(points3d, points2d, camera)
```

Shape và frame constraints được kiểm tra.

---

## 52. Bundle Adjustment

383 đã giới thiệu Bundle Adjustment.

384 xác định vision-specific frontend:

```text
FeatureTracks
CameraModels
ReprojectionResidual
```

sau đó chuyển sang generic optimization engine.

---

## 53. Visual SLAM

Pipeline:

```text
Image
 ↓
Features
 ↓
Tracking
 ↓
Pose
 ↓
Mapping
 ↓
Optimization
```

có thể compose từ các module hiện có.

---

## 54. Image Pyramid

Semantic:

```text
ImagePyramid<T>
```

với levels có thể static/dynamic.

Compiler có thể fuse pyramid operations khi practical.

---

## 55. Multi-scale Processing

Algorithms có thể chạy:

```text
coarse → fine
```

và dùng pyramid để giảm cost.

---

## 56. Video

Video là:

```text
Stream<Image>
```

không cần một video object bắt buộc.

Metadata:

```text
frame_rate
timestamp
resolution
codec
color_space
```

là semantic metadata.

---

## 57. Frame Timing

Video frame không nên chỉ có index.

Có:

```text
Frame<Timestamp>
```

để hỗ trợ variable-rate video.

---

## 58. Zero-copy Video

Decoder → Vision:

```text
Decoder
   ↓
GPU Buffer
   ↓
ImageView
   ↓
CUDA/Metal/Vulkan kernel
```

không bắt buộc:

```text
GPU → CPU → GPU
```

---

## 59. Neural Vision

Axiom không cần neural-network-specific Core.

Model có thể chỉ là:

```text
fn infer(input: Tensor<...>) -> Tensor<...>
```

và reuse:

```text
Tensor
GPU
AD
Linear Algebra
```

---

## 60. CompilerDB

384 bổ sung:

```text
VisionDB
ImageDB
ImageTypeDB
PixelDB
PixelFormatDB
ColorSpaceDB
ColorTransformDB
ImageLayoutDB
ImageViewDB
ImageRoiDB
ImageChannelDB
ImageDepthDB

ImageFilterDB
ImageConvolutionDB
ImageResizeDB
ImageWarpDB
ImagePyramidDB
ImageMorphologyDB
ImageThresholdDB
ImageIntegralDB

MaskDB
LabelMapDB
ConnectedComponentDB
ContourDB
SegmentationDB

CameraModelDB
CameraIntrinsicsDB
CameraExtrinsicsDB
CameraProjectionDB
CameraDistortionDB
CameraCalibrationDB

StereoDB
DisparityDB
DepthDB
EpipolarDB
FundamentalMatrixDB
EssentialMatrixDB
HomographyDB

FeatureDB
KeypointDB
DescriptorDB
FeatureMatchDB
RansacDB
GeometricVerificationDB

OpticalFlowDB
TrackingDB
TrackAssociationDB
MultiObjectTrackingDB

PointCloudDB
PointCloudViewDB
PointCloudSearchDB
PointCloudRegistrationDB
IcpDB
PointCloudNormalDB

PoseEstimationDB
PnpDB
VisualOdometryDB
VisualSlamDB
BundleAdjustmentVisionDB

VideoDB
VideoFrameDB
VideoTimestampDB
VideoPipelineDB
VideoZeroCopyDB

VisionTensorDB
VisionGpuDB
VisionSimdDB
VisionParallelDB
VisionAdDB
VisionNumericalDB
VisionCostModelDB
VisionProofDB
VisionVerificationDB
```

---

# 61. MIR additions

```text
IMAGE_CREATE
IMAGE_VIEW
IMAGE_MUT_VIEW
IMAGE_ROI
IMAGE_CHANNEL
IMAGE_CONVERT_LAYOUT
IMAGE_COLOR_CONVERT
IMAGE_RESIZE
IMAGE_WARP
IMAGE_REMAP

IMAGE_FILTER
IMAGE_CONVOLVE
IMAGE_SEPARABLE_FILTER
IMAGE_MORPHOLOGY
IMAGE_THRESHOLD
IMAGE_INTEGRAL
IMAGE_PYRAMID

MASK_CREATE
MASK_APPLY
CONNECTED_COMPONENTS
CONTOUR_EXTRACT

CAMERA_PROJECT
CAMERA_UNPROJECT
CAMERA_DISTORT
CAMERA_UNDISTORT
CAMERA_CALIBRATE

STEREO_MATCH
STEREO_DISPARITY
DEPTH_RECONSTRUCT

FEATURE_DETECT
FEATURE_DESCRIBE
FEATURE_MATCH
RANSAC_ESTIMATE
GEOMETRIC_VERIFY

OPTICAL_FLOW
TRACK_CREATE
TRACK_UPDATE
TRACK_ASSOCIATE

POINTCLOUD_CREATE
POINTCLOUD_VIEW
POINTCLOUD_SEARCH
POINTCLOUD_DOWNSAMPLE
POINTCLOUD_NORMAL
POINTCLOUD_REGISTER

POSE_ESTIMATE
PNP_SOLVE
VISION_BUNDLE_ADJUST

VIDEO_FRAME
VIDEO_TIMESTAMP
VIDEO_STREAM_BEGIN
VIDEO_STREAM_END
```

---

# 62. Vision Proofs

```text
ImageFormatProof
ColorSpaceProof
ColorTransformProof
ImageLayoutProof
ImageViewProof
ImageRoiProof

PixelCoordinateProof
CameraProjectionProof
CameraFrameProof
CameraIntrinsicProof
CameraDistortionProof
CalibrationProof

StereoGeometryProof
DisparityDepthProof
EpipolarProof
HomographyProof

FeatureShapeProof
DescriptorProof
MatchMetricProof
RansacProof
GeometricVerificationProof

MaskProof
SegmentationProof
ContourProof

TrackingStateProof
TrackAssociationProof
OpticalFlowProof

PointCloudFrameProof
PointCloudLayoutProof
PointCloudSearchProof
PointCloudRegistrationProof

PoseEstimationProof
PnPProof
BundleAdjustmentProof

VideoTimestampProof
VideoPipelineProof
VideoStorageProof

VisionAliasProof
VisionBoundsProof
VisionNumericalProof
VisionParallelProof
VisionSimdProof
VisionGpuProof
VisionAdProof
VisionDeterminismProof
VisionZeroCopyProof
```

---

# 63. Invariants

### `AVISION-01`
Image phải có pixel-format semantics độc lập với raw storage.

### `AVISION-02`
Color space conversion không được coi là bitcast.

### `AVISION-03`
Linear và encoded color phải được phân biệt khi semantic yêu cầu.

### `AVISION-04`
Image view không sở hữu underlying storage.

### `AVISION-05`
ROI phải có thể được biểu diễn zero-copy khi layout cho phép.

### `AVISION-06`
Layout conversion phải là operation có semantics rõ ràng.

### `AVISION-07`
Pixel coordinate convention phải được xác định rõ.

### `AVISION-08`
Pixel coordinate và world/camera coordinate không được implicit interchange.

### `AVISION-09`
Camera projection phải preserve frame semantics.

### `AVISION-10`
Intrinsic/extrinsic parameters phải có shape và coordinate semantics đúng.

### `AVISION-11`
Distortion model phải explicit.

### `AVISION-12`
Stereo geometry phải preserve camera-frame consistency.

### `AVISION-13`
Depth và disparity phải là semantic types khác nhau.

### `AVISION-14`
Feature descriptor phải preserve declared element type/shape.

### `AVISION-15`
Feature matching phải sử dụng metric tương thích.

### `AVISION-16`
RANSAC/randomized vision algorithms phải dùng explicit RNG semantics.

### `AVISION-17`
Segmentation mask không được tự động coi là arbitrary numeric tensor.

### `AVISION-18`
Connected-component labels phải preserve label identity semantics.

### `AVISION-19`
Point cloud points phải giữ coordinate-frame semantics.

### `AVISION-20`
Spatial search phải preserve point-cloud ownership/view validity.

### `AVISION-21`
ICP/registration phải preserve transform direction.

### `AVISION-22`
Pose estimation phải xác định rõ source và destination frame.

### `AVISION-23`
Bundle adjustment phải preserve parameter/residual shape consistency.

### `AVISION-24`
Video frame ordering phải dựa trên timestamp semantics khi timestamp là observable.

### `AVISION-25`
Variable-rate video không được giả định uniform sampling.

### `AVISION-26`
GPU image processing phải preserve storage-domain rules.

### `AVISION-27`
SIMD image kernels phải preserve bounds, aliasing và numerical contract.

### `AVISION-28`
Vision pipelines không được tạo hidden copies khi zero-copy contract được yêu cầu.

### `AVISION-29`
Vision abstractions phải có khả năng compile away khi static specialization cho phép.

### `AVISION-30`
Không sử dụng Computer Vision thì compiler không được kéo theo vision runtime dependency.

---

# 64. Kiến trúc sau 384

Axiom lúc này đã hình thành một stack perception khá hoàn chỉnh:

```text
                   AUTONOMOUS SYSTEM
                          │
                    ┌─────┴─────┐
                    │ Robotics  │
                    └─────┬─────┘
                          │
                 Planning / Control
                          │
                  State Estimation
                          │
              ┌───────────┴───────────┐
              │                       │
         Computer Vision          Signals
              │                       │
        Image / Video              FFT
              │                       │
          Geometry             Probability
              │                       │
              └───────────┬───────────┘
                          │
                  Tensor / Algebra
                          │
                    Numeric / Units
                          │
                AD / Optimization
                          │
             SIMD / Parallel / GPU
                          │
                     Native Code
```

Đặc biệt, đây vẫn tuân thủ triết lý Axiom:

> **Programmer viết semantic intent; compiler quyết định representation và execution strategy.**

Một đoạn:

```text
edges = canny(image)
```

không nhất thiết tạo object `CannyFilter`.

Một pipeline:

```text
resize
→ color_convert
→ gaussian
→ gradient
→ threshold
```

có thể trở thành một chuỗi kernel SIMD/GPU được fusion.

Còn:

```text
project(camera, point)
```

có thể cuối cùng chỉ còn vài phép `fma`, division và load/store.

Đây là nền tảng rất tốt để bước kế tiếp xây **AI/ML execution model** trên Tensor + AD + GPU + Vision + Robotics, thay vì tạo một framework ML tách biệt khỏi ngôn ngữ.