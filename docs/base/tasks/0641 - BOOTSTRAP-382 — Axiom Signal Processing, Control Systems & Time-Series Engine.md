# BOOTSTRAP-382 — Axiom Signal Processing, Control Systems & Time-Series Engine

Sau **381 — Physics, Mechanics & Dynamics**, bước tiếp theo nên xây lớp **Signal Processing + Control**, vì đây là tầng kết nối trực tiếp:

```text
Sensors
   ↓
Signal / Time Series
   ↓
Filtering / FFT / Spectral Analysis
   ↓
State Estimation
   ↓
Control
   ↓
Physics / Robotics / Simulation
   ↓
Actuators
```

Đồng thời nó tận dụng gần như toàn bộ nền tảng Axiom đã có:

- Numeric;
- Tensor;
- Linear Algebra;
- FFT;
- Sparse;
- Probability;
- Solver;
- AD;
- Units;
- Geometry;
- Physics;
- Parallel/SIMD/GPU;
- Constraint/Proof Engine.

Mục tiêu của 382 là xây **semantic foundation**, không biến signal/control thành Core language.

---

# 1. Tách Signal khỏi Raw Array

Không nên để:

```text
f32[]
```

tự động được coi là signal.

Signal có semantic:

```text
Signal<T, Domain>
```

trong đó `Domain` có thể biểu diễn:

```text
Time
Frequency
Spatial
Event
DiscreteTime
ContinuousTime
```

Representation cuối vẫn có thể chỉ là:

```text
f32*
```

hoặc tensor.

---

# 2. Time Series

Một time series cần phân biệt:

```text
Sample
Timestamp
SamplingRate
Duration
Signal
```

Không giả định mọi signal có sampling rate cố định.

Có:

```text
UniformSignal
NonUniformSignal
EventSignal
```

---

# 3. Continuous và Discrete

Phân biệt:

```text
ContinuousSignal<T>
DiscreteSignal<T>
```

và:

```text
ContinuousTime
DiscreteTime
```

Điều này rất quan trọng khi chuyển:

```text
continuous system
        ↓
sampling
        ↓
digital controller
```

---

# 4. Sampling

Semantic operation:

```text
sample(signal, rate)
```

có thể tạo:

```text
DiscreteSignal<T>
```

Compiler/constraint engine kiểm tra:

```text
frequency
time unit
sample rate
```

---

# 5. Nyquist constraint

Nếu signal có bandwidth:

```text
B
```

và sampling rate:

```text
Fs
```

thì sampling condition có thể được biểu diễn thành constraint:

```text
Fs >= 2 * B
```

Nếu tất cả static:

```text
compile-time proof
```

Nếu dynamic:

```text
runtime validation
```

---

# 6. Signal Units

Signal phải tích hợp Units 378.

Ví dụ:

```text
Voltage
Current
Pressure
Acceleration
Temperature
```

Một signal có thể conceptually là:

```text
Signal<Voltage>
```

hoặc:

```text
Signal<Quantity<f32, VoltageDimension>>
```

nhưng unit metadata có thể erase.

---

# 7. Signal Frame

Sensor signal còn có spatial frame:

```text
Accelerometer<BodyFrame>
Gyroscope<BodyFrame>
Camera<CameraFrame>
```

Do đó một signal có thể mang cả:

```text
Value semantics
+
Unit semantics
+
Frame semantics
+
Time semantics
```

và compiler có thể kiểm tra compatibility.

---

# 8. Signal Operations

Chuẩn hóa:

```text
map
zip
combine
resample
delay
differentiate
integrate
window
clip
normalize
```

Các operation thuần có thể được fusion.

---

# 9. Zero-Copy Signal Pipeline

Ví dụ:

```text
sensor
 → filter
 → FFT
 → feature extraction
 → controller
```

không nên mặc định tạo:

```text
buffer1
buffer2
buffer3
buffer4
```

Compiler có thể:

```text
fuse
reuse
stream
```

các intermediate buffers.

---

# 10. Windowing

FFT/filtering thường cần:

```text
Window
```

như:

```text
Rectangular
Hann
Hamming
Blackman
Kaiser
Custom
```

Window function nên là generic/comptime-friendly.

---

# 11. Convolution

Signal convolution:

```text
y = x * h
```

phải phân biệt:

```text
Full
Same
Valid
Circular
```

và boundary semantics.

---

# 12. Direct vs FFT Convolution

Compiler/cost model có thể chọn:

```text
Direct convolution
```

hoặc:

```text
FFT
 ×
Pointwise multiply
 ×
IFFT
```

nếu numerical contract cho phép.

Task 373 đã cung cấp transform infrastructure.

---

# 13. FIR Filter

Semantic abstraction:

```text
FIRFilter<T, Coefficients>
```

Compiler có thể:

- unroll;
- SIMD;
- vectorize;
- fuse;
- use circular buffer;
- use FFT for long filters.

---

# 14. IIR Filter

Hỗ trợ:

```text
IIRFilter
Biquad
SOS
```

với stability metadata.

---

# 15. Filter Stability

Không được coi:

```text
IIR filter
```

chỉ là arbitrary coefficients.

Có thể có compile-time/static analysis:

```text
Stable
PotentiallyUnstable
Unknown
```

để diagnostic.

---

# 16. Frequency Response

Semantic operations:

```text
frequency_response
magnitude_response
phase_response
group_delay
```

Có thể được đánh giá compile-time nếu coefficients static.

---

# 17. Z-transform

Signal system có thể biểu diễn:

```text
ZTransform
```

và các operations:

```text
pole
zero
transfer_function
```

nhưng đây là symbolic/numerical library, không phải Core.

---

# 18. Transfer Function

Control system cần:

```text
TransferFunction<Input, Output>
```

với:

```text
numerator
denominator
```

Có thể dùng polynomial abstraction.

---

# 19. State-Space

Chuẩn hóa:

```text
StateSpace<A, B, C, D>
```

với:

```text
x_dot = A x + B u
y     = C x + D u
```

Shape constraints đảm bảo:

```text
A: N×N
B: N×M
C: P×N
D: P×M
```

---

# 20. Compile-Time Matrix Compatibility

Nếu dimensions static:

```text
A[N,N]
B[N,M]
```

compiler biết state-space operation hợp lệ.

Không cần runtime matrix dimension checking.

---

# 21. Control System

Control system:

```text
Controller
Plant
Sensor
Actuator
```

nhưng không cần class hierarchy.

Có thể dùng traits:

```text
trait Controller
trait Plant
trait Sensor
trait Actuator
```

---

# 22. Open-loop / Closed-loop

Semantic graph:

```text
Reference
   ↓
Controller
   ↓
Plant
   ↓
Sensor
   └──── feedback ────┘
```

Compiler không cần runtime graph object nếu topology static.

---

# 23. Static Control Graph

Ví dụ:

```text
controller(
    pid(
        filter(sensor())
    ),
    plant
)
```

có thể được compiler flatten thành:

```text
sensor
 → filter
 → PID
 → actuator
```

không tạo object graph runtime.

---

# 24. PID Controller

Chuẩn hóa:

```text
PID {
    kp
    ki
    kd
}
```

và:

```text
update(error, dt)
```

Units phải được kiểm tra.

Đặc biệt:

```text
Kp * error
Ki * integral(error)
Kd * derivative(error)
```

phải có output dimension tương thích.

---

# 25. PID với Units

Ví dụ controller cho:

```text
position [m]
```

và actuator:

```text
force [N]
```

thì gains không phải chỉ là `f32`.

Compiler có thể suy ra gain dimensions.

Đây là một ứng dụng rất mạnh của:

```text
Units
+
Constraint Solver
```

---

# 26. Discrete Controller

Digital controller cần:

```text
dt
```

hoặc:

```text
SamplingRate
```

và phải phân biệt:

```text
continuous controller
discrete controller
```

Không implicit convert.

---

# 27. Delay

Delay là semantic primitive:

```text
delay(signal, duration)
```

với:

```text
delay_samples(signal, N)
```

cho discrete signal.

---

# 28. State and History

Delay/filter/controller có internal state.

Axiom ownership model phải cho phép state được lưu:

```text
stack
heap
caller storage
arena
device
```

mà không thay đổi semantics.

---

# 29. Streaming State

Streaming filter:

```text
process(chunk)
```

không được giả định mỗi chunk độc lập.

Compiler phải biết state:

```text
FilterState
```

sống xuyên các invocation.

---

# 30. Streaming Pipeline

Ví dụ:

```text
Input
 → Resample
 → FIR
 → FFT
 → Feature
 → Controller
```

có thể compile thành pipeline:

```text
Read chunk
 ↓
Process
 ↓
Process
 ↓
Process
 ↓
Output
```

với bounded memory.

---

# 31. Backpressure

Nếu pipeline asynchronous:

```text
Producer
 ↓
Filter
 ↓
FFT
 ↓
Consumer
```

cần:

```text
bounded channel
```

đã có trong Async/Sync infrastructure.

Signal layer không tự tạo concurrency model mới.

---

# 32. Event Signals

Không phải mọi sensor đều là uniform samples.

Ví dụ:

```text
button press
packet arrival
collision event
interrupt
```

có thể biểu diễn:

```text
EventSignal<T>
```

---

# 33. Event Time

Event cần:

```text
Timestamp
```

và semantic ordering.

Nếu timestamps có thể bằng nhau:

```text
stable ordering
```

phải được xác định nếu observable.

---

# 34. State Estimation

Signal processing nối trực tiếp sang estimation:

```text
KalmanFilter
ExtendedKalmanFilter
UnscentedKalmanFilter
ParticleFilter
```

---

# 35. Kalman Filter

Semantic state:

```text
x
P
```

và:

```text
Prediction
Update
```

dựa trên Linear Algebra/Solver.

---

# 36. Extended Kalman Filter

EKF cần Jacobian.

Thay vì bắt programmer viết:

```text
F = ...
H = ...
```

có thể:

```text
@differentiate
```

để compiler sinh Jacobian.

---

# 37. Unscented Transform

UKF dùng:

```text
SigmaPoints
Weights
```

có thể tận dụng:

```text
Tensor
Parallel
SIMD
```

---

# 38. Particle Filter

Particle filter dùng:

```text
RNG
Probability
Parallel
```

đã có ở task 376.

Mỗi particle có thể xử lý độc lập.

---

# 39. Randomness

Không được có global hidden RNG.

Ví dụ particle sampling:

```text
rng.split(worker_id)
```

để bảo đảm parallel safety.

---

# 40. State Estimation + Units

Ví dụ:

```text
position : m
velocity : m/s
acceleration : m/s²
```

Kalman covariance phải có dimensions tương ứng.

Axiom có thể kiểm tra một phần dimensional consistency của covariance matrices.

---

# 41. Observability / Controllability

Linear control system có semantic operations:

```text
observability
controllability
```

và có thể tính rank.

Đây là library-level linear algebra.

---

# 42. Stability Analysis

Control layer cần:

```text
stable
unstable
marginal
unknown
```

cho các system.

Có thể dựa trên:

```text
eigenvalues
poles
Lyapunov
```

---

# 43. Lyapunov Analysis

Có thể biểu diễn:

```text
V(x)
```

và kiểm tra:

```text
V(x) > 0
dV/dt < 0
```

AD + Symbolic + Constraint Engine có thể hỗ trợ.

---

# 44. Optimization-based Control

Hỗ trợ semantic abstraction:

```text
MPC
TrajectoryOptimization
OptimalControl
```

dựa trên:

```text
Solver
AD
Linear Algebra
Physics
```

---

# 45. Model Predictive Control

MPC pipeline:

```text
State Estimate
      ↓
Prediction Model
      ↓
Optimization
      ↓
Control Action
      ↓
Plant
```

Compiler có thể specialize prediction horizon nếu static.

---

# 46. Control Constraints

Ví dụ:

```text
u_min <= u <= u_max
```

và:

```text
x_min <= x <= x_max
```

được biểu diễn bằng Constraint Engine + Solver.

---

# 47. Differentiable Control

AD có thể sinh:

```text
dLoss / dControllerParameter
```

phục vụ:

- controller tuning;
- system identification;
- learned controllers;
- differentiable robotics.

---

# 48. Neural Controller

Không cần tạo abstraction riêng.

Một neural network có thể đơn giản là:

```text
fn controller(state) -> action
```

và được compose vào ControlGraph.

Tensor/GPU infrastructure xử lý phần nặng.

---

# 49. Real-Time Contract

Control system thường cần:

```text
RealTime
```

semantic contract:

```text
NoAllocation
NoBlocking
BoundedExecution
Deterministic
```

Compiler có thể kiểm tra một phần.

Ví dụ:

```text
@realtime
fn control(...)
```

không được gọi API có:

```text
MayBlock
UnboundedAllocation
UnboundedLoop
```

nếu profile yêu cầu nghiêm ngặt.

---

# 50. Worst-Case Execution Metadata

Không phải compiler luôn chứng minh được WCET.

Do đó trạng thái:

```text
ProvenBounded
Estimated
Unknown
```

phải khác nhau.

Không được biến estimate thành guarantee.

---

# 51. Interrupt Integration

Sensor/actuator realtime có thể liên quan:

```text
Interrupt domain
```

đã được thiết kế ở Thread/Execution Domain.

Signal handler không được tự động:

- allocate;
- block;
- await;
- call arbitrary runtime.

---

# 52. Hardware I/O

Signal source có thể là:

```text
ADC
DAC
GPIO
SPI
I2C
UART
CAN
Ethernet
```

nhưng hardware access thuộc system/FFI layer.

Signal layer chỉ cần nhận semantic stream.

---

# 53. DMA / Zero-copy

High-performance sensor processing có thể dùng:

```text
DMA buffer
```

với storage domain:

```text
External
Pinned
Mapped
Device
```

Ownership contract phải explicit.

---

# 54. Frequency-domain pipeline

Một pipeline:

```text
samples
 ↓
window
 ↓
FFT
 ↓
magnitude
 ↓
feature
```

compiler có thể fuse intermediate operations.

Nếu `magnitude` chỉ cần một phần spectrum, không nhất thiết materialize toàn bộ intermediate nếu algorithm cho phép.

---

# 55. Streaming FFT

FFT planning phải hỗ trợ:

```text
batch FFT
overlap-save
overlap-add
STFT
```

và workspace reuse.

---

# 56. STFT

Semantic abstraction:

```text
STFT {
    window
    hop
    fft_size
}
```

output:

```text
Time × Frequency
```

có thể map trực tiếp sang Tensor.

---

# 57. Spectrogram

Không cần một runtime object đặc biệt.

Có thể:

```text
Tensor<Complex<T>, [Time, Frequency]>
```

kèm semantic metadata.

---

# 58. Signal graph

Signal processing pipeline có thể được biểu diễn compiler-level:

```text
SignalGraph
```

nodes:

```text
Source
Transform
Filter
Resample
FFT
Feature
Sink
```

Nếu graph static:

```text
compile-time graph optimization
```

---

# 59. Graph fusion

Ví dụ:

```text
Gain
 → Bias
 → Clamp
 → Activation
```

có thể fuse.

Tương tự:

```text
Window
 → FFT
 → Magnitude
```

nếu backend hỗ trợ.

---

# 60. Signal scheduling

Compiler có thể chọn:

```text
scalar
SIMD
parallel
GPU
streaming
```

dựa trên:

```text
sample rate
latency
buffer size
throughput
cost model
```

Không được thay đổi observable latency contract nếu programmer yêu cầu strict realtime.

---

# 61. Latency contract

Signal pipeline có thể khai báo:

```text
Latency:
    ThroughputOptimized
    LowLatency
    Bounded
    Exact
```

Compiler/backend sử dụng contract này.

---

# 62. Numerical contract

Kế thừa:

```text
Strict
Deterministic
Fast
Approximate
```

để kiểm soát:

- floating-point reassociation;
- FFT implementation;
- reduction;
- filter accumulation;
- parallel scheduling.

---

# 63. CompilerDB

Task 382 bổ sung:

```text id="vrh7js"
SignalDB
SignalTypeDB
SignalDomainDB
SignalTimeDB
SignalFrequencyDB
SignalSampleDB
SignalSamplingDB
SignalTimestampDB
SignalRateDB
SignalWindowDB

FilterDB
FirDB
IirDB
BiquadDB
FilterStabilityDB
FilterResponseDB

ConvolutionDB
CorrelationDB
ResamplingDB
InterpolationDB
DecimationDB

SpectralDB
STFTDB
SpectrogramDB
FrequencyResponseDB
TransferFunctionDB

ControlDB
ControllerDB
PlantDB
SensorDB
ActuatorDB
ControlGraphDB
FeedbackDB
PidDB
StateSpaceDB
DiscreteControlDB
ContinuousControlDB

StabilityDB
PoleZeroDB
LyapunovDB
ObservabilityDB
ControllabilityDB

EstimatorDB
KalmanDB
ExtendedKalmanDB
UnscentedKalmanDB
ParticleFilterDB
StateEstimationDB

MpcDB
OptimalControlDB
TrajectoryOptimizationDB
ControlConstraintDB

SignalPipelineDB
SignalFusionDB
SignalStreamingDB
SignalBufferDB
SignalBackpressureDB
SignalLatencyDB
SignalRealtimeDB

SignalSimdDB
SignalParallelDB
SignalGpuDB
SignalAdDB
SignalRngDB
SignalCostModelDB
SignalNumericalDB
SignalProofDB
SignalVerificationDB
```

---

# 64. MIR additions

```text id="y3qf1m"
SIGNAL_CREATE
SIGNAL_SAMPLE
SIGNAL_RESAMPLE
SIGNAL_DELAY
SIGNAL_MAP
SIGNAL_ZIP
SIGNAL_WINDOW
SIGNAL_CONVOLVE
SIGNAL_CORRELATE

FILTER_APPLY
FILTER_STATE
FILTER_RESET

FFT_STREAM
STFT
SPECTRUM
MAGNITUDE_SPECTRUM

TRANSFER_FUNCTION
STATE_SPACE_APPLY

CONTROL_STEP
CONTROL_FEEDBACK
CONTROL_PID
CONTROL_CONSTRAINT

ESTIMATE_PREDICT
ESTIMATE_UPDATE
KALMAN_PREDICT
KALMAN_UPDATE

MPC_PREDICT
MPC_OPTIMIZE

SIGNAL_FUSE
SIGNAL_BUFFER
SIGNAL_STREAM_BEGIN
SIGNAL_STREAM_END
SIGNAL_RESERVE
```

---

# 65. Signal/Control proofs

```text id="8q2s6c"
SamplingProof
NyquistProof
SamplingRateProof
SignalDimensionProof
SignalFrameProof

FilterStabilityProof
FilterShapeProof
FilterNumericalProof

ConvolutionProof
FFTShapeProof
SpectralProof

ControlDimensionProof
ControlFrameProof
ControlShapeProof
FeedbackProof
PidUnitProof
StateSpaceProof

StabilityProof
ObservabilityProof
ControllabilityProof

KalmanCovarianceProof
EstimatorShapeProof
EstimatorNumericalProof

MpcConstraintProof
OptimalControlProof

RealtimeProof
LatencyProof
BoundedExecutionProof
SignalAliasProof
SignalStorageProof
SignalGpuProof
SignalParallelProof
SignalAdProof
SignalDeterminismProof
```

---

# 66. Invariants

### `ASIGNAL-01`
Signal phải phân biệt domain/time semantics với raw storage.

### `ASIGNAL-02`
Continuous và discrete signal phải có semantic distinction.

### `ASIGNAL-03`
Sampling rate phải có đơn vị thời gian hợp lệ.

### `ASIGNAL-04`
Static sampling constraints phải được kiểm tra compile-time khi đủ thông tin.

### `ASIGNAL-05`
Dynamic sampling constraints phải có runtime validation khi cần.

### `ASIGNAL-06`
Signal units phải tương thích với operation.

### `ASIGNAL-07`
Signal frame phải tương thích với geometric/physical frame.

### `ASIGNAL-08`
Signal pipeline không được tạo implicit copies nếu zero-copy semantics có thể được duy trì.

### `ASIGNAL-09`
Signal fusion chỉ hợp lệ khi observable semantics được giữ nguyên.

### `ASIGNAL-10`
Filter state phải có lifetime rõ ràng.

### `ASIGNAL-11`
Filter stability phải được phân biệt giữa proven, estimated và unknown.

### `ASIGNAL-12`
Convolution boundary semantics phải explicit.

### `ASIGNAL-13`
FFT-based optimization không được thay đổi numerical contract trái phép.

### `ASIGNAL-14`
Streaming operation phải giữ đúng state qua các chunk.

### `ASIGNAL-15`
Event signal phải có timestamp semantics xác định.

### `ASIGNAL-16`
Control input/output dimensions phải tương thích.

### `ASIGNAL-17`
PID gains phải có dimensional semantics chính xác.

### `ASIGNAL-18`
State-space matrix shapes phải được kiểm tra compile-time khi static.

### `ASIGNAL-19`
Feedback graph phải không tạo dependency cycle ngoài semantics cho phép.

### `ASIGNAL-20`
State estimator phải giữ covariance/state shape consistency.

### `ASIGNAL-21`
Randomized estimators phải sử dụng explicit RNG state.

### `ASIGNAL-22`
Parallel particle processing không được sử dụng shared mutable RNG trái phép.

### `ASIGNAL-23`
Real-time contract không được bị phá bởi hidden allocation hoặc blocking operation.

### `ASIGNAL-24`
`BoundedExecution` chỉ được cấp khi compiler/runtime có đủ evidence.

### `ASIGNAL-25`
Latency guarantees phải phân biệt guarantee với estimate.

### `ASIGNAL-26`
GPU signal processing phải tuân thủ storage-domain rules.

### `ASIGNAL-27`
SIMD signal processing phải preserve numerical contract.

### `ASIGNAL-28`
AD-generated controller/estimator derivatives phải obey AD legality.

### `ASIGNAL-29`
Signal/control abstractions phải có thể compile away khi không cần runtime metadata.

### `ASIGNAL-30`
Không sử dụng signal/control nào thì chương trình không được kéo theo runtime dependency của signal/control.

---

## Kết quả kiến trúc

Sau 382, Axiom có thể biểu diễn một hệ thống hoàn chỉnh:

```text
┌──────────────────────────────────────────┐
│              Physical World             │
└───────────────────┬──────────────────────┘
                    │
                 Sensor
                    │
                    ▼
             Signal / Sampling
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       Filtering             FFT
          │                   │
          └─────────┬─────────┘
                    ▼
             State Estimation
                    │
                    ▼
               Controller
                    │
                    ▼
                Actuator
                    │
                    ▼
                 Physics
                    │
                    └────────── feedback
```

Điểm đáng chú ý là toàn bộ chuỗi này có thể được compiler nhìn thấy ở nhiều mức:

```text
Signal
   ↓
Tensor
   ↓
Linear Algebra
   ↓
Solver
   ↓
AD
   ↓
Units
   ↓
Constraint Proof
   ↓
SIMD / Parallel / GPU
```

Do đó một chương trình điều khiển robot hoặc xử lý sensor tốc độ cao có thể được viết ở mức rất cao, nhưng compiler vẫn có khả năng hạ xuống các vòng lặp `f32`, SIMD instructions, worker threads hoặc GPU kernels mà **không cần một runtime object hierarchy nặng nề**.