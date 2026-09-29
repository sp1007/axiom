# BOOTSTRAP-380 — Axiom Geometry, Spatial Computing, Coordinate Systems & Computational Geometry Engine

Sau **379 — Constraint/Proof Engine**, Axiom đã có nền tảng để biểu diễn và chứng minh các thuộc tính hình học ở compile-time. Bước tiếp theo hợp lý là xây **Geometry/Spatial Computing** như một tầng thư viện + compiler semantic infrastructure.

Mục tiêu không phải tạo một “math library khổng lồ”, mà là để Axiom có thể biểu diễn **đồ họa 2D/3D, CAD, game engine, robotics, simulation, GIS, physics và computer vision** mà vẫn giữ:

- value semantics;
- zero-cost abstraction;
- SIMD/GPU;
- compile-time dimension/frame checking;
- không class hierarchy bắt buộc;
- không runtime object metadata.

---

## 1. Tách rõ Point và Vector

Đây là quy tắc nền tảng.

```text
Point<T, Frame>
Vector<T, Frame>
Direction<T, Frame>
Normal<T, Frame>
```

Không coi chúng chỉ là:

```text
Vector<f32, 3>
```

với alias khác nhau.

Semantic algebra:

```text
Point - Point   -> Vector
Point + Vector  -> Point
Point - Vector  -> Point

Vector + Vector -> Vector
Vector - Vector -> Vector
```

Nhưng:

```text
Point + Point
```

là không hợp lệ trong geometry semantics thông thường.

Điều này giúp compiler bắt được nhiều lỗi mà `Vec3` thuần túy không thể phát hiện.

---

# 2. Coordinate Frame là type-level information

Ví dụ:

```text
Point<f32, World>
Point<f32, Camera>
Point<f32, RobotArm>
```

Không cho phép:

```text
WorldPoint + CameraVector
```

nếu không có conversion hợp lệ.

Compiler có thể phát hiện lỗi ngay compile-time.

Đây là một trong những ứng dụng trực tiếp của **379 Constraint Engine**.

---

# 3. Frame transformation

Một transformation:

```text
Transform<From, To>
```

có semantics:

```text
Point<From> -> Point<To>
Vector<From> -> Vector<To>
```

Ví dụ:

```text
Transform<Camera, World>
```

không thể vô tình áp dụng cho:

```text
Point<Robot>
```

---

# 4. Không cần runtime frame tag

Điểm quan trọng:

```text
Point<f32, World>
Point<f32, Camera>
```

không nhất thiết khác representation.

Sau compile:

```text
Point<f32, World>
```

có thể chỉ còn:

```text
3 × f32
```

Frame information được erase.

Do đó:

> **Type safety của coordinate system không tạo runtime overhead.**

---

# 5. Frame graph

Trong hệ thống lớn có thể có:

```text
World
 ├── Vehicle
 │    └── Sensor
 └── Camera
```

Compiler/library có thể biểu diễn:

```text
FrameGraph
TransformGraph
```

và tự tìm chuỗi transformation:

```text
Sensor → Vehicle → World → Camera
```

---

# 6. Affine transformation

Core geometry nên hỗ trợ semantic:

```text
Translate
Rotate
Scale
AffineTransform
```

Transformation composition:

```text
T = T3 ∘ T2 ∘ T1
```

Compiler có thể compose thành một transformation duy nhất.

---

# 7. Homogeneous coordinates

Representation có thể sử dụng:

```text
4x4 matrix
```

nhưng semantic API không bắt buộc programmer thao tác trực tiếp bằng homogeneous coordinates.

Ví dụ:

```text
transform(point)
transform(vector)
```

để phân biệt translation behavior.

---

# 8. Vector transformation khác Point transformation

Ví dụ:

```text
translate(point)
```

có tác dụng.

Nhưng:

```text
translate(vector)
```

không.

Đây là lý do `Point` và `Vector` phải là semantic types khác nhau.

---

# 9. Normal transformation

Normal không đơn giản là vector thông thường khi có non-uniform scale.

Compiler/library phải biểu diễn:

```text
NormalTransform
```

với inverse-transpose semantics khi cần.

Không cho phép optimizer thay thế tùy tiện bằng ordinary vector transform.

---

# 10. Orientation

Geometry engine cần semantic orientation:

```text
Clockwise
CounterClockwise
RightHanded
LeftHanded
```

và:

```text
OrientationPredicate
```

cho các thuật toán hình học.

---

# 11. Basic primitives

Tầng geometry chuẩn hóa:

```text
Point
Vector
Direction
Normal

Line
Ray
Segment

Plane
Triangle
Quad

Circle
Sphere
Ellipse

Capsule
Cylinder
Cone

AABB
OBB
Frustum
```

Tất cả là value/generic types.

Không cần inheritance.

---

# 12. Generic scalar

Geometry không nên hard-code `f32`.

Ví dụ:

```text
Point<f32, World>
Point<f64, World>
Point<Fixed32, World>
Point<Decimal, World>
```

Có thể dùng:

```text
Numeric
Ordered
ApproxEq
```

traits phù hợp.

---

# 13. Geometry tolerance

Floating-point geometry có vấn đề:

```text
a == b
```

thường không phải predicate phù hợp.

Do đó:

```text
Approx<T>
Tolerance<T>
GeometryEpsilon
```

là semantic abstractions.

Nhưng tolerance phải explicit.

Không được có:

```text
global magic epsilon
```

áp dụng cho toàn chương trình.

---

# 14. Robust predicates

Các phép:

```text
orientation
inside/outside
intersection
coplanarity
```

cần robust implementation.

Geometry engine có thể hỗ trợ:

```text
Exact
FilteredExact
Floating
Approximate
```

numeric policy.

---

# 15. Filtered predicates

Ví dụ:

```text
orientation(a,b,c)
```

có thể:

```text
fast floating evaluation
        ↓
uncertain?
        ↓
higher precision / exact fallback
```

Programmer vẫn gọi một API.

Compiler/runtime implementation có thể tối ưu path.

---

# 16. Exact geometric predicates

Một số predicate cần kết quả chính xác hơn value computation.

Tách:

```text
GeometricPredicate
GeometricMeasurement
```

Ví dụ:

```text
orientation(...)
```

có thể exact.

Trong khi:

```text
distance(...)
```

có thể approximate.

---

# 17. Intersection semantics

Không trả về một kiểu mơ hồ.

Ví dụ:

```text
IntersectionResult
```

có thể là:

```text
None
Point
Segment
Coplanar
Overlap
```

và phụ thuộc primitive pair.

---

# 18. Distance semantics

Chuẩn hóa:

```text
distance(A, B)
squared_distance(A, B)
closest_point(A, B)
closest_points(A, B)
```

` squared_distance` rất quan trọng vì tránh:

```text
sqrt
```

khi chỉ cần so sánh khoảng cách.

---

# 19. Containment

Các primitive cung cấp:

```text
contains
inside
outside
on_boundary
```

với boundary semantics rõ ràng.

Ví dụ:

```text
AABB.contains(p)
```

phải định nghĩa inclusive/exclusive boundary.

---

# 20. Ray intersection

Chuẩn hóa:

```text
ray.intersect(sphere)
ray.intersect(triangle)
ray.intersect(aabb)
```

nhưng đây chỉ là method syntax.

Semantic operation vẫn là:

```text
intersect(ray, sphere)
```

phù hợp với struct/function philosophy của Axiom.

---

# 21. Triangle geometry

Triangle cần hỗ trợ:

```text
area
normal
barycentric
contains
closest_point
intersect
```

Barycentric coordinates đặc biệt quan trọng cho:

- rendering;
- interpolation;
- collision;
- FEM;
- geometry processing.

---

# 22. Barycentric coordinates

Compiler/library có thể biểu diễn:

```text
Barycentric<T>
```

với constraint:

```text
u + v + w = 1
```

379 có thể giữ proof của constraint này khi biết statically.

---

# 23. Mesh integration

Mesh không nên trở thành một class hierarchy.

Có thể:

```text
Mesh<Vertex, Edge, Face, Storage>
```

hoặc các cấu trúc dữ liệu chuyên biệt:

```text
TriangleMesh
HalfEdgeMesh
WingedEdgeMesh
IndexedMesh
```

vẫn dựa trên struct + trait.

---

# 24. Geometry vs topology

Phải phân biệt:

```text
Geometry
Topology
```

Geometry:

```text
position
normal
uv
```

Topology:

```text
vertex
edge
face
adjacency
```

Một mesh có thể thay đổi topology mà không thay đổi geometry.

---

# 25. Mesh mutation

Phân biệt:

```text
VertexValueMutation
TopologyMutation
```

Topology mutation có thể invalidate:

```text
adjacency views
face handles
BVH
spatial index
```

Proof system phải biết dependency này.

---

# 26. Stable logical identity

Không dùng pointer làm identity mặc định.

Mesh:

```text
VertexId
EdgeId
FaceId
```

có thể dùng generation:

```text
VertexId {
    index
    generation
}
```

để phát hiện stale handles.

---

# 27. Spatial acceleration structures

Geometry engine cần chuẩn hóa:

```text
BVH
KDTree
Octree
Quadtree
UniformGrid
RTree
SpatialHash
```

Không phải tất cả đều Core.

Chúng là library abstractions nhưng compiler cần hiểu semantic operations.

---

# 28. BVH

BVH đặc biệt quan trọng cho:

- rendering;
- ray tracing;
- collision;
- spatial queries.

Compiler/runtime có thể tối ưu:

```text
build
refit
traverse
intersect
```

---

# 29. Broad phase / narrow phase

Collision system tách:

```text
BroadPhase
NarrowPhase
```

Broad phase:

```text
AABB/BVH/grid
```

Narrow phase:

```text
triangle
sphere
capsule
GJK
SAT
```

Điều này cho phép thay implementation mà không đổi semantic API.

---

# 30. Collision semantics

Không chỉ:

```text
bool intersects
```

Mà có thể:

```text
CollisionResult {
    hit
    normal
    penetration
    contact_point
}
```

với ownership/value semantics rõ ràng.

---

# 31. GJK / SAT / CCD

Geometry engine nên chuẩn hóa primitives cho:

```text
GJK
EPA
SAT
Continuous Collision Detection
Ray Casting
Sweep Tests
```

nhưng algorithm selection thuộc cost model.

---

# 32. Spatial queries

Unified API:

```text
nearest
contains
intersects
raycast
overlap
range_query
```

Có thể hoạt động trên:

```text
BVH
KDTree
RTree
Grid
```

mà caller không cần biết implementation nếu API không expose storage.

---

# 33. Geometry + SIMD

Các phép:

```text
dot
cross
distance
transform
AABB test
ray test
```

phải được vectorization-friendly.

Ví dụ hàng triệu points:

```text
parallel_for(points)
    transform(point)
```

có thể tự động:

```text
SIMD
+
parallel
```

mà không cần viết SIMD thủ công.

---

# 34. Structure of Arrays

Geometry data thường phù hợp:

```text
AoS
SoA
AoSoA
```

Compiler/library nên cho phép semantic layout selection.

Ví dụ:

```text
PointSet<Layout = SoA>
```

Representation có thể thay đổi mà API vẫn giữ.

---

# 35. GPU geometry

Geometry operations có thể chạy:

```text
CPU
SIMD
Parallel CPU
GPU
```

Thông qua execution policy.

Ví dụ:

```text
raycast(mesh, rays, execution = auto)
```

compiler/cost model chọn implementation nếu semantics không đổi.

---

# 36. Geometry kernel

Các primitive operation nên có một semantic kernel layer:

```text
GeometryKernel
```

bao gồm:

```text
orientation
intersection
distance
projection
transform
containment
closest_point
```

Nó tương tự Linear Algebra kernel nhưng dành cho geometric predicates/operations.

---

# 37. Geometry + Units

Units và geometry phải kết hợp.

Ví dụ:

```text
Point<f64, World<Meter>>
```

hoặc conceptual:

```text
Point<Quantity<f64, Length>, World>
```

Nhưng:

```text
Point<Length, World>
```

không nên biến thành runtime wrapper bắt buộc.

---

# 38. Angle

Angle cần semantic distinction:

```text
Angle<Radian>
Angle<Degree>
```

Tránh:

```text
sin(90.0)
```

không rõ 90 là gì.

Compiler có thể erase unit sau conversion.

---

# 39. Geometry + AD

Các operation smooth:

```text
distance
transform
dot
normalize
```

có thể differentiable.

Các operation discontinuous:

```text
intersection
inside
sign
```

phải có semantics rõ ràng:

```text
NonDifferentiable
Subgradient
Piecewise
```

AD engine 371 sử dụng metadata này.

---

# 40. Geometry + physics

Physics engine có thể dùng:

```text
Point
Vector
Normal
Transform
Frame
AABB
Sphere
Capsule
Mesh
```

nhưng Geometry không phụ thuộc Physics.

Đây là dependency direction quan trọng:

```text
Geometry
   ↓
Physics
```

không ngược lại.

---

# 41. Geometry + robotics

Robotics cần:

```text
Frame
Transform
Pose
Twist
Wrench
Jacobian
```

Geometry cung cấp nền tảng:

```text
Frame
Point
Vector
Transform
```

Robotics layer nằm phía trên.

---

# 42. Geometry + computer vision

Vision có thể dùng:

```text
Point2
Point3
Ray
Plane
Transform
CameraModel
```

Geometry không cần phụ thuộc CV.

---

# 43. Projective geometry

Hỗ trợ:

```text
Homography
Projection
CameraProjection
Perspective
Orthographic
```

nhưng giữ distinction giữa:

```text
Euclidean
Affine
Projective
```

Không để compiler tùy tiện áp dụng algebraic identities không hợp lệ.

---

# 44. Transform canonicalization

Compiler có thể biến:

```text
T1(T2(T3(p)))
```

thành:

```text
(T1 ∘ T2 ∘ T3)(p)
```

nếu:

- transformations compatible;
- numerical contract cho phép;
- side-effect free.

Đây là application trực tiếp của Expression Engine 372.

---

# 45. Geometry expression fusion

Ví dụ:

```text
p2 = translate(
       rotate(
         scale(p)
       )
     )
```

không nhất thiết tạo:

```text
Vector temporary 1
Vector temporary 2
Vector temporary 3
```

Compiler có thể fuse thành machine operations hoặc một transform matrix.

---

# 46. Robustness contract

Geometry operations cần numerical contract:

```text
Strict
Robust
Fast
Approximate
```

Ví dụ:

```text
intersect(..., contract = Robust)
```

có thể sử dụng filtered/exact predicate.

Không được compiler tự ý đổi `Strict` thành `Fast`.

---

# 47. Coordinate system handedness

Handedness phải là semantic metadata:

```text
RightHanded
LeftHanded
```

đặc biệt khi interoperability với:

- graphics APIs;
- CAD;
- game engines;
- robotics;
- GIS.

Compiler có thể detect conversion mismatch.

---

# 48. Storage abstraction

Geometry data có thể nằm:

```text
Host
Device
Mapped
External
```

Geometry API không được mặc định rằng dữ liệu luôn ở CPU heap.

Điều này kế thừa GPU/Storage model trước đó.

---

# 49. External geometry

Interop với:

```text
OpenGL
Vulkan
DirectX
Metal
CUDA
CAD kernels
GIS
```

thông qua explicit FFI/storage contracts.

Không biến external pointer thành safe geometry view nếu chưa có proof.

---

# 50. CompilerDB

Bổ sung:

```text
GeometryDB
GeometryTypeDB
GeometryScalarDB
GeometryFrameDB
GeometryCoordinateDB
GeometryTransformDB
GeometryAffineDB
GeometryProjectiveDB
GeometryOrientationDB
GeometryToleranceDB
GeometryPredicateDB
GeometryRobustPredicateDB
GeometryIntersectionDB
GeometryDistanceDB
GeometryClosestPointDB
GeometryContainmentDB

PointDB
VectorDB
DirectionDB
NormalDB
LineDB
RayDB
SegmentDB
PlaneDB
TriangleDB
SphereDB
CapsuleDB
AabbDB
ObbDB
FrustumDB

MeshGeometryDB
MeshTopologyDB
MeshVertexDB
MeshEdgeDB
MeshFaceDB
MeshAdjacencyDB
MeshHandleDB
MeshMutationDB

SpatialDB
BvhDB
KdTreeDB
OctreeDB
QuadtreeDB
UniformGridDB
RTreeDB
SpatialHashDB

CollisionDB
BroadPhaseDB
NarrowPhaseDB
GjkDB
EpaDB
SatDB
CcdDB

GeometrySimdDB
GeometryParallelDB
GeometryGpuDB
GeometryAdDB
GeometryCostModelDB
GeometryProofDB
GeometryVerificationDB
```

---

# 51. MIR additions

Không cần biến mọi geometry function thành MIR primitive. Chỉ những operation có compiler optimization semantics:

```text
GEOM_POINT_CREATE
GEOM_VECTOR_CREATE
GEOM_TRANSFORM
GEOM_COMPOSE_TRANSFORM

GEOM_DOT
GEOM_CROSS
GEOM_NORMALIZE

GEOM_DISTANCE
GEOM_SQUARED_DISTANCE
GEOM_CLOSEST_POINT

GEOM_ORIENTATION
GEOM_INTERSECT
GEOM_CONTAINS
GEOM_PROJECT

GEOM_RAYCAST
GEOM_AABB_TEST
GEOM_BVH_TRAVERSE

GEOM_BROAD_PHASE
GEOM_NARROW_PHASE

GEOM_FRAME_CONVERT
GEOM_PREDICATE
GEOM_EXACT_FALLBACK
```

Các operation này sau đó có thể lower về:

```text
scalar
SIMD
parallel
GPU
```

---

# 52. Geometry proofs

379 cho phép geometry tạo proof:

```text
FrameCompatibilityProof
TransformCompatibilityProof
PointVectorAlgebraProof
DimensionProof
OrientationProof
BoundsProof
IntersectionProof
ContainmentProof
RobustPredicateProof
MeshTopologyProof
MeshHandleProof
SpatialIndexProof
BVHValidityProof
CollisionProof
CCDProof
AliasProof
StorageProof
DeviceProof
NumericalProof
TransformCompositionProof
```

---

# 53. Ví dụ compiler reasoning

Code:

```text
fn transform_mesh(
    mesh: view<Mesh<Vertex<World>>>,
    t: Transform<World, Camera>
) -> ...
```

Compiler biết:

```text
mesh vertices: World
t: World → Camera
```

nên:

```text
transform(vertex)
```

hợp lệ.

Nếu programmer viết:

```text
Transform<Robot, Camera>
```

compiler có thể báo:

```text
Cannot transform World geometry using Robot → Camera transform.
Required:
    Transform<World, Camera>

Found:
    Transform<Robot, Camera>
```

Không cần runtime check.

---

# 54. Ví dụ zero-cost frame safety

Source:

```text
let p: Point<f32, World> = ...
let camera: Transform<World, Camera> = ...

let q = camera.apply(p)
```

Semantic type:

```text
Point<f32, Camera>
```

Machine representation có thể chỉ là:

```text
{ f32, f32, f32 }
```

Không có:

```text
frame_id
runtime tag
virtual table
object header
```

---

# 55. Geometry invariants

### `AGEOM-01`
Point và Vector phải có semantics khác nhau.

### `AGEOM-02`
Point - Point phải tạo Vector khi frame tương thích.

### `AGEOM-03`
Point + Vector phải tạo Point.

### `AGEOM-04`
Không cho phép các phép Point/Vector không hợp lệ trong safe geometry algebra.

### `AGEOM-05`
Coordinate frame mismatch phải được phát hiện compile-time khi frame statically known.

### `AGEOM-06`
Frame metadata không được bắt buộc tạo runtime overhead.

### `AGEOM-07`
Transform phải xác định rõ source và destination frame.

### `AGEOM-08`
Normal transform phải tuân thủ đúng semantic transformation.

### `AGEOM-09`
Affine và projective operations phải được phân biệt.

### `AGEOM-10`
Handedness conversion phải explicit.

### `AGEOM-11`
Geometry tolerance phải explicit hoặc thuộc một contract rõ ràng.

### `AGEOM-12`
Robust predicates không được bị thay thế bằng approximate predicates khi contract không cho phép.

### `AGEOM-13`
Squared distance phải không tạo căn bậc hai không cần thiết.

### `AGEOM-14`
Boundary semantics của containment phải deterministic.

### `AGEOM-15`
Intersection result phải phân biệt các topology cần thiết.

### `AGEOM-16`
Mesh geometry và topology phải được quản lý như hai semantic domains liên quan nhưng khác nhau.

### `AGEOM-17`
Topology mutation phải invalidate các view/proof phụ thuộc.

### `AGEOM-18`
Logical mesh identity không được phụ thuộc trực tiếp vào physical address.

### `AGEOM-19`
Spatial index phải có validity relationship với source geometry.

### `AGEOM-20`
BVH/KDTree/Grid không được làm thay đổi semantic kết quả spatial query.

### `AGEOM-21`
Broad phase có thể false-positive nhưng không được false-negative nếu contract yêu cầu collision completeness.

### `AGEOM-22`
Narrow phase phải giữ đúng numerical/collision contract.

### `AGEOM-23`
Geometry operations phải tuân thủ ownership/capability model.

### `AGEOM-24`
GPU geometry không được implicit chuyển Host/Device memory.

### `AGEOM-25`
SIMD geometry phải giữ nguyên semantic kết quả theo numerical contract.

### `AGEOM-26`
Parallel geometry phải giữ đúng alias/race semantics.

### `AGEOM-27`
AD chỉ được sinh derivative khi geometry operation có derivative semantics hợp lệ.

### `AGEOM-28`
Transform composition chỉ được canonicalize khi semantic/numerical contract cho phép.

### `AGEOM-29`
Geometry abstraction không được yêu cầu runtime polymorphism nếu static dispatch đủ.

### `AGEOM-30`
Compile-time frame/unit/geometry proofs phải được erase hoàn toàn khi không còn observable runtime semantics.

---

## Kiến trúc Axiom lúc này

Sau 380, phần scientific/computational stack bắt đầu trở thành:

```text
                    Axiom
                      │
          ┌───────────┴───────────┐
          │                       │
     General Systems        Scientific/Spatial
          │                       │
   Ownership/Memory          Numeric
   Async/Threads             Tensor
   SIMD/GPU                  Linear Algebra
   FFI/ABI                   AD
                             Symbolic
                             FFT
                             Sparse
                             Graph
                             Probability
                             Solvers/PDE
                             Units
                             Constraints
                             Geometry
```

Và quan trọng hơn, **Geometry không tạo thêm một hệ type/verification riêng biệt**. Nó tận dụng:

```text
Type System
      +
Units/Dimensions
      +
Constraint/Proof Engine
      +
Numeric Contracts
      +
SIMD/Parallel/GPU
      +
AD
      +
Storage/Ownership
```

Đây chính là hướng giúp Axiom có thể phục vụ cùng một compiler cho **game engine, CAD, robotics, scientific computing, graphics và AI** mà không phải biến Core language thành một đống tính năng đặc thù.