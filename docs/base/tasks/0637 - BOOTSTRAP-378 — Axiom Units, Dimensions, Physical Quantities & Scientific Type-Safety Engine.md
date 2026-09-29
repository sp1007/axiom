# BOOTSTRAP-378 — Axiom Units, Dimensions, Physical Quantities & Scientific Type-Safety Engine

Sau **377 — Numerical Solvers & Scientific Simulation**, một thiếu sót lớn bắt đầu lộ ra: solver có thể đúng về mặt số học nhưng **sai về mặt vật lý**.

Ví dụ:

```text
velocity = distance + time
```

đều có thể là `f64`, nhưng về mặt vật lý là sai.

Hoặc:

```text
force = mass * velocity
```

thay vì:

```text
force = mass * acceleration
```

Compiler thông thường không phát hiện được.

Vì vậy Axiom nên có **Units/Dimensions** ở tầng generic/comptime, với mục tiêu:

> **Đưa càng nhiều lỗi vật lý và khoa học từ runtime xuống compile time mà không tạo runtime overhead.**

---

# 1. Dimension khác Unit

Đây là nguyên tắc nền tảng.

```text
Dimension
```

mô tả đại lượng vật lý:

```text
Length
Time
Mass
Temperature
...
```

Trong khi:

```text
Unit
```

mô tả cách biểu diễn:

```text
meter
kilometer
centimeter

second
millisecond
hour
```

Ví dụ:

```text
5 m
500 cm
0.005 km
```

có cùng:

```text
Dimension = Length
```

nhưng khác Unit.

---

# 2. Dimension vector

Không nên hard-code:

```text
Length
Time
Mass
```

thành compiler classes.

Dùng dimension vector:

```text
[L, M, T, I, Θ, N, J]
```

Ví dụ:

```text
Length = [1,0,0,0,0,0,0]

Time = [0,0,1,0,0,0,0]

Velocity = [1,0,-1,0,0,0,0]

Acceleration = [1,0,-2,0,0,0,0]

Force = [1,1,-2,0,0,0,0]
```

Đây là compile-time representation.

---

# 3. Derived dimensions

Compiler có thể tính:

```text
velocity = length / time
```

thành:

```text
[1,0,0] / [0,0,1]
=
[1,0,-1]
```

Không cần programmer khai báo mọi dimension mới.

---

# 4. Quantity type

Conceptually:

```text
Quantity<T, Dimension, Unit>
```

Ví dụ:

```text
Quantity<f64, Length, Meter>
```

nhưng đây là generic compile-time type.

Không cần runtime metadata.

---

# 5. Runtime representation

Nếu:

```text
Quantity<f64, Length, Meter>
```

thì representation có thể đơn giản là:

```text
f64
```

Compiler biết unit ở compile time.

Không cần:

```text
struct {
    value: f64
    unit: UnitTag
}
```

trừ khi programmer yêu cầu runtime unit metadata.

---

# 6. Zero-cost abstraction

Ví dụ:

```text
let distance: Meter<f64> = 10
let time: Second<f64> = 2

let velocity = distance / time
```

có thể compile thành:

```text
10.0 / 2.0
```

Không thêm:

- object;
- heap;
- unit tag;
- function call;
- runtime conversion.

---

# 7. Unit conversion

Ví dụ:

```text
1 km → 1000 m
```

conversion factor có thể là compile-time constant.

Compiler có thể biến:

```text
let x: Meter<f64> = 1.km()
```

thành:

```text
1000.0
```

nếu conversion exact/known.

---

# 8. Affine units

Temperature là trường hợp đặc biệt.

```text
0 °C != 0 K
```

vì conversion có offset.

Không được coi mọi unit conversion là:

```text
value * factor
```

Cần phân biệt:

```text
LinearUnit
AffineUnit
```

---

# 9. Celsius + Celsius

Không phải mọi operation giữa quantity cùng dimension đều có nghĩa vật lý.

Ví dụ:

```text
20°C + 30°C
```

không nhất thiết có semantics thông thường.

Do đó Unit system phải cho phép định nghĩa operation legality.

---

# 10. Temperature difference

Cần phân biệt:

```text
Temperature
TemperatureDelta
```

Ví dụ:

```text
30°C - 20°C = 10 Δ°C
```

nhưng:

```text
20°C + 10 Δ°C = 30°C
```

Đây là lý do chỉ kiểm tra dimension vector là chưa đủ.

---

# 11. Quantity algebra

Các phép toán cơ bản:

```text
+ -
* /
```

Compiler áp dụng algebraic rules.

### Addition

Chỉ cho phép:

```text
same dimension
```

### Multiplication

Dimension cộng exponent.

### Division

Dimension trừ exponent.

---

# 12. Power

Ví dụ:

```text
area = length ^ 2
```

dimension:

```text
[1,0,0] * 2
=
[2,0,0]
```

`pow` với exponent compile-time rational có thể tạo dimension mới.

Runtime arbitrary exponent không nhất thiết có thể tạo statically typed dimension.

---

# 13. Square root

Ví dụ:

```text
sqrt(area)
```

chỉ trả về dimension hợp lệ nếu exponent có thể chia cho 2.

```text
m² → m
```

nhưng:

```text
sqrt(m)
```

có thể tạo:

```text
m^(1/2)
```

nếu hệ thống dimension hỗ trợ rational exponents.

---

# 14. Dimensionless quantities

Có những đại lượng:

```text
dimension = 1
```

nhưng vẫn có semantic meaning:

```text
angle
probability
strain
refractive_index
```

Do đó:

> Dimensionless không đồng nghĩa interchangeable.

---

# 15. Semantic quantity categories

Có thể có:

```text
Dimensionless
Angle
Probability
Ratio
Count
```

để tránh:

```text
Probability + Angle
```

dù cả hai đều dimensionless.

---

# 16. Angle

Có thể dùng:

```text
radian
degree
turn
```

Radian dimensionless về SI nhưng semantic category riêng.

Ví dụ:

```text
sin(angle)
```

được phép.

Nhưng:

```text
sin(length)
```

bị reject.

---

# 17. Trigonometric functions

Compiler/library phải enforce:

```text
sin(angle)
cos(angle)
tan(angle)
```

và output:

```text
dimensionless
```

Không cho:

```text
sin(5.meter())
```

trong safe code.

---

# 18. Exponential/logarithm

Các hàm:

```text
exp
log
ln
```

yêu cầu dimensionless input.

Ví dụ:

```text
exp(3.0)
```

hợp lệ.

Nhưng:

```text
exp(3.meter())
```

bị reject.

---

# 19. Physical constants

Constants nên có type:

```text
speed_of_light: Meter / Second
gravitational_constant: ...
Planck_constant: ...
Boltzmann_constant: ...
```

Không phải bare `f64`.

Ví dụ:

```text
energy = mass * c^2
```

compiler tự verify dimension.

---

# 20. Constants + comptime

Unit system tích hợp trực tiếp với `comptime`.

Ví dụ:

```text
const c = 299792458.meter / second
```

Compiler có thể tính dimension và value tại compile time.

Không cần runtime unit processing.

---

# 21. Measurement uncertainty

Scientific computing thường cần:

```text
x = 10.0 ± 0.2
```

Có thể có library abstraction:

```text
Measurement<T, Unit>
```

với:

```text
value
uncertainty
```

Không nhất thiết là Core primitive.

---

# 22. Uncertainty propagation

Ví dụ:

```text
z = x + y
```

uncertainty propagation có thể dùng:

```text
σ_z
```

nhưng đây là statistical semantics.

Không nên compiler tự động thay đổi numeric computation chỉ vì type là `Measurement`.

---

# 23. Interval arithmetic

Có thể có:

```text
Interval<T>
```

với:

```text
[lower, upper]
```

Compiler có thể optimize arithmetic nhưng phải preserve enclosure semantics.

---

# 24. Physical quantity + Tensor

Ví dụ:

```text
Tensor<Velocity, [N,3]>
```

hoặc conceptually:

```text
Tensor<Quantity<f32, Velocity>, [N,3]>
```

Dimension metadata nằm ở type level.

Compiler không lưu unit cho từng tensor element.

---

# 25. Quantity + Sparse

Sparse matrix có thể chứa:

```text
Matrix<Force>
```

hoặc operators:

```text
StiffnessMatrix
```

Compiler có thể verify:

```text
K * displacement = force
```

nếu dimensions được encode.

---

# 26. Quantity + Graph

Graph edge có thể có:

```text
distance
time
capacity
energy
```

Graph algorithms có thể yêu cầu đúng quantity category.

Ví dụ Dijkstra:

```text
edge.weight
```

phải có semantics orderable và additive phù hợp.

Không phải mọi quantity đều là valid shortest-path weight.

---

# 27. Solver integration

ODE:

```text
dy/dt = f(t,y)
```

Compiler có thể kiểm tra dimension:

Nếu:

```text
y: Position
t: Time
```

thì:

```text
dy/dt: Velocity
```

và RHS phải có dimension Velocity.

Đây là một compile-time consistency check cực kỳ giá trị.

---

# 28. PDE integration

Ví dụ:

```text
∂T/∂t = α ∇²T
```

Nếu:

```text
T = Temperature
t = Time
α = Length² / Time
```

thì:

```text
α ∇²T
```

có đúng dimension:

```text
Temperature / Time
```

Compiler có thể verify toàn equation.

---

# 29. FEM integration

Trong FEM:

```text
K u = f
```

compiler có thể kiểm tra dimensional consistency của:

```text
K
u
f
```

Đây là một lợi ích lớn so với numeric-only languages.

---

# 30. Unit-aware literals

Có thể hỗ trợ syntax:

```text
10.m
5.s
20.km
100.ms
300.K
```

nhưng đây là syntax/library integration, không nhất thiết hard-code hàng nghìn units vào parser.

Comptime/unit registry có thể resolve.

---

# 31. User-defined units

Programmer có thể định nghĩa:

```text
unit furlong = 201.168.m
```

hoặc:

```text
unit widget = ...
```

Compiler phải biến nó thành compile-time unit definition.

Không cần runtime registry.

---

# 32. Unit systems

Có thể hỗ trợ:

```text
SI
CGS
Imperial
Custom
```

nhưng đây là compile-time/library configuration.

Không có “current unit system” global runtime state.

---

# 33. Unit conversion policy

Phải phân biệt:

```text
Exact
Approximate
Contextual
```

Ví dụ:

```text
1 inch = 0.0254 meter
```

exact theo định nghĩa.

Trong khi một số conversion có thể là approximate.

Numerical contract phải giữ thông tin này.

---

# 34. Unit erasure

Sau type checking:

```text
Meter<f64>
```

có thể trở thành:

```text
f64
```

trong machine representation.

Compiler vẫn giữ metadata trong debug/type information nếu cần.

---

# 35. ABI

Thông thường:

```text
Meter<f64>
```

có ABI tương đương:

```text
f64
```

nhưng explicit FFI ABI có thể yêu cầu unwrap:

```text
extern "C"
```

Compiler phải biết representation.

---

# 36. FFI

Không nên truyền:

```text
Meter<f64>
```

sang C một cách mù quáng.

ABI layer phải biết:

```text
representation = f64
```

và conversion semantic boundary rõ ràng.

---

# 37. Compile-time dimensional analysis

Compiler nên có:

```text
DimensionExpr
```

ví dụ:

```text
Mass * Acceleration
```

→

```text
Force
```

Dimension solver có thể canonicalize:

```text
m * s^-2
```

thành canonical vector.

---

# 38. Dimension constraints

Generic function:

```text
fn integrate<T: Quantity>(...)
```

có thể có constraint kiểu:

```text
Dim<T> == Length
```

hoặc:

```text
Dim<Y> == Dim<F> * Time
```

Đây là compile-time constraint.

Không runtime cost.

---

# 39. Generic scientific algorithms

Có thể viết:

```text
fn kinetic_energy<M, V>(
    mass: M,
    velocity: V
)
```

và compiler verify:

```text
M = Mass
V = Length / Time
```

result:

```text
Energy
```

Monomorphization tạo native code như ordinary numeric function.

---

# 40. No runtime unit dispatch

Không nên:

```text
switch(unit)
```

trong arithmetic thông thường.

Nếu programmer thực sự cần dynamic units:

```text
DynamicQuantity
```

có thể là library type.

Đây là distinction rất quan trọng:

```text
StaticQuantity
DynamicQuantity
```

---

# 41. Dynamic unit

Ví dụ application đọc file:

```text
unit_name = input()
```

thì compile-time không biết unit.

Library có thể cung cấp:

```text
DynamicUnit
DynamicQuantity
```

với runtime metadata.

Nhưng đây không phải default path.

---

# 42. Serialization

Quantity serialization có thể chọn:

```text
value only
value + unit
canonical SI value
```

tùy format contract.

Compiler không được tự động serialize compile-time type metadata nếu format không yêu cầu.

---

# 43. Debugging

Debugger nên hiển thị:

```text
velocity = 12.5 m/s
```

thay vì chỉ:

```text
velocity = 12.5
```

nếu debug metadata được emit.

Đây là debug-only metadata, không phải runtime overhead.

---

# 44. CompilerDB

Bổ sung:

```text id="cz45c4"
UnitDB
UnitTypeDB
UnitDefinitionDB
UnitSystemDB
UnitDimensionDB
UnitDimensionVectorDB
UnitExponentDB
UnitConversionDB
UnitConversionFactorDB
UnitConversionOffsetDB
UnitConversionPolicyDB
UnitRegistryDB
UnitLiteralDB
UnitCanonicalDB

QuantityDB
QuantityTypeDB
QuantityValueDB
QuantityDimensionDB
QuantityUnitDB
QuantityCategoryDB
QuantityAlgebraDB
QuantityConstraintDB
QuantityConversionDB
QuantityErasureDB
QuantityAbiDB

PhysicalConstantDB
MeasurementDB
MeasurementUncertaintyDB
UncertaintyPropagationDB
IntervalDB

DimensionSolverDB
DimensionExprDB
DimensionConstraintDB
DimensionProofDB
UnitProofDB
QuantityProofDB
PhysicalConsistencyDB
ScientificTypeCheckDB
```

---

# 45. MIR additions

Semantic MIR:

```text id="l9k2zw"
QUANTITY_CONSTRUCT
QUANTITY_ADD
QUANTITY_SUB
QUANTITY_MUL
QUANTITY_DIV
QUANTITY_POW

UNIT_CONVERT
UNIT_SCALE
UNIT_OFFSET

DIMENSION_CHECK
DIMENSION_CAST

MEASUREMENT_CREATE
UNCERTAINTY_PROPAGATE

INTERVAL_CREATE
INTERVAL_ADD
INTERVAL_SUB
INTERVAL_MUL
INTERVAL_DIV
```

Sau compile-time checking, các operation như:

```text
QUANTITY_MUL
UNIT_SCALE
DIMENSION_CHECK
```

thường biến mất hoàn toàn.

Ví dụ:

```text
5.km / 2.s
```

có thể cuối cùng chỉ còn:

```text
2500.0 / 2.0
```

với type information đã được compiler kiểm chứng.

---

# 46. Proof system

Cần:

```text id="b8u4vz"
DimensionEqualityProof
DimensionAdditionProof
DimensionMultiplicationProof
DimensionDivisionProof
DimensionPowerProof

UnitConversionProof
UnitAffineConversionProof
UnitExactnessProof

QuantityTypeProof
QuantityAlgebraProof
QuantityConstraintProof
QuantityErasureProof
QuantityAbiProof

PhysicalEquationProof
PhysicalConstantProof
PhysicalSolverProof
PhysicalTensorProof
PhysicalSparseProof
PhysicalGraphProof
PhysicalPdeProof
PhysicalOdeProof
```

---

# 47. Invariants

### `AUNIT-01`
Unit checking phải diễn ra compile time khi static information đầy đủ.

### `AUNIT-02`
Dimension phải khác Unit.

### `AUNIT-03`
Unit conversion phải preserve physical quantity semantics.

### `AUNIT-04`
Linear và affine conversion phải được phân biệt.

### `AUNIT-05`
Temperature không được xử lý như quantity linear thông thường khi có offset.

### `AUNIT-06`
Addition/subtraction phải kiểm tra dimension compatibility.

### `AUNIT-07`
Multiplication/division phải tính dimension algebra chính xác.

### `AUNIT-08`
Power phải kiểm tra exponent/dimension legality.

### `AUNIT-09`
Dimensionless không mặc nhiên có nghĩa interchangeable.

### `AUNIT-10`
Angle phải có semantic distinction phù hợp.

### `AUNIT-11`
Trigonometric functions phải kiểm tra input semantic category.

### `AUNIT-12`
`exp/log` phải yêu cầu dimensionless input trong safe static mode.

### `AUNIT-13`
Physical constants phải mang quantity semantics nếu được định nghĩa như physical constants.

### `AUNIT-14`
Quantity abstraction không được tạo mandatory runtime unit metadata.

### `AUNIT-15`
Static quantity có thể được representation-erased sau semantic checking.

### `AUNIT-16`
Unit conversion known at compile time phải có thể constant-fold.

### `AUNIT-17`
User-defined units phải được kiểm tra bằng cùng dimension engine.

### `AUNIT-18`
Generic quantity constraints phải được giải quyết tại compile time khi có thể.

### `AUNIT-19`
Dynamic units phải là explicit runtime abstraction.

### `AUNIT-20`
Static unit semantics không được tự động chuyển thành dynamic unit runtime.

### `AUNIT-21`
Quantity ABI phải được xác định rõ tại FFI boundary.

### `AUNIT-22`
Quantity metadata không được thay đổi machine representation ngoài ABI contract.

### `AUNIT-23`
Tensor quantity operations phải preserve dimension semantics.

### `AUNIT-24`
Sparse quantity operations phải preserve dimension semantics.

### `AUNIT-25`
Graph edge/node quantities phải được kiểm tra khi algorithm yêu cầu algebraic properties.

### `AUNIT-26`
ODE/PDE equations phải có thể được dimension-check khi biểu diễn đủ static information.

### `AUNIT-27`
Solver optimization không được loại bỏ physical consistency requirements.

### `AUNIT-28`
Measurement/uncertainty semantics phải khác ordinary quantity arithmetic.

### `AUNIT-29`
Compiler có thể erase unit operations sau khi proofs hoàn tất.

### `AUNIT-30`
Chương trình không sử dụng units/quantities không được chịu runtime dependency vì Unit Engine.

---

## Vị trí của 378

Axiom lúc này có thêm một tầng rất mạnh:

```text
                 Scientific Computing
                         │
              ┌──────────┴──────────┐
              │                     │
          Numerical              Physical
          Semantics              Semantics
              │                     │
      Numeric/Tensor/...       Units/Dimensions
              │                     │
              └──────────┬──────────┘
                         │
                  Solver / Simulation
                         │
                SIMD / Parallel / GPU
                         │
                     Native Code
```

Điểm quan trọng nhất của **378** là nó không biến Axiom thành một ngôn ngữ “đo lường” nặng nề. `Meter<f64>` về bản chất vẫn có thể chỉ là **một `f64` ở machine level**. Toàn bộ hệ thống dimension/unit chỉ tồn tại để compiler chứng minh rằng chương trình có ý nghĩa vật lý trước khi nó biến abstraction đó thành machine code.