# BOOTSTRAP-194 — Cross-Compilation, Multi-Target & Universal Native Toolchain

**TRẠNG THÁI: FROZEN / COMPLETED**

## 194.1. Quyết định kiến trúc lớn

Axiom **không có các compiler riêng cho từng nền tảng**.

Không:

```text
axc-windows
axc-linux
axc-macos
axc-ios
axc-android
```

Mà là:

```text
                    Axiom Compiler
                         │
                    TargetSpec
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
      x86-64           ARM64             WASM
        │                │                 │
       PE              ELF              WASM
        │                │                 │
     Windows          Linux/macOS       Browser/WASI
```

> **Target là input của compiler, không phải một compiler khác.**

Điều này phù hợp trực tiếp với `CompilerDB` hiện tại.

---

# 194.2. `TargetSpec`

Compiler nhận một đối tượng semantic:

```text
TargetSpec
```

gồm:

```text
Architecture
OS
Environment
ABI
ObjectFormat
PointerWidth
Endianness
DataLayout
CallingConventions
CPUFeatures
SIMDFeatures
AtomicFeatures
TLS
UnwindModel
PageSize
LinkModel
SystemAPI
SDK
RuntimeProfile
GPUTargets
```

Ví dụ concept:

```text
x86_64-pc-windows-msvc
aarch64-unknown-linux-gnu
aarch64-apple-darwin
aarch64-apple-ios
wasm32-wasi
```

Nhưng Axiom không nhất thiết phải dùng target triple như semantic identity duy nhất.

Triple chỉ là **selector**.

---

# 194.3. Target Identity

Target identity:

```text
TargetId =
    Architecture
    + OS
    + Environment
    + ABI
    + ObjectFormat
    + PointerModel
    + FeatureSet
```

Ví dụ:

```text
x86_64 + Windows + MSVC ABI + PE/COFF
```

khác:

```text
x86_64 + Windows + GNU ABI + PE/COFF
```

dù cùng CPU và OS.

---

# 194.4. Host ≠ Target

Compiler chạy trên:

```text
HostTarget
```

nhưng tạo:

```text
BuildTarget
```

Hai target độc lập.

Ví dụ:

```text
Host:
Windows x64

Target:
Linux ARM64
```

Compiler vẫn chạy bình thường.

Điều này cũng áp dụng cho:

```text
Build tools
Comptime
Build scripts
Code generator
Compiler plugins
```

Host execution và target execution phải được phân biệt.

---

# 194.5. Build/Host/Target ba miền

Axiom sử dụng mô hình:

```text
Build machine
     │
     ▼
Host tools
     │
     ▼
Target program
```

Khi cross-compile compiler itself:

```text
Build → Host → Target
```

Điều này cho phép bootstrap compiler chạy trên một platform nhưng sinh compiler cho platform khác.

---

# 194.6. Target Configuration không phải Runtime Configuration

Ví dụ:

```text
target = linux-arm64
runtime = freestanding
```

hoặc:

```text
target = windows-x64
runtime = hosted
```

Runtime profile là một lớp riêng.

Do đó cùng target có thể tạo:

```text
Linux application
Linux kernel/freestanding code
Linux embedded program
```

nếu target profile cho phép.

---

# 194.7. Data Layout

Compiler có `DataLayout`.

Nó xác định:

```text
pointer size
pointer alignment
integer alignment
float alignment
aggregate alignment
endianness
vector alignment
ABI rules
```

Nhưng:

> **DataLayout là target fact, không phải language semantic rule.**

Ví dụ:

```text
usize
```

có thể là:

```text
u32
```

trên target 32-bit và:

```text
u64
```

trên target 64-bit.

---

# 194.8. Endianness

Axiom không giả định little-endian.

Compiler biết:

```text
LittleEndian
BigEndian
```

Nhưng source semantic:

```axiom
let x: u32 = ...
```

không thay đổi.

Endian chỉ ảnh hưởng:

- memory representation
- serialization
- ABI
- machine code
- explicit byte conversion

---

# 194.9. Pointer Model

Target khai báo:

```text
PointerModel
```

Ví dụ:

```text
Flat
Segmented
Capability
WASMLinear
```

Axiom semantic pointer/provenance model vẫn tồn tại phía trên representation.

Do đó:

```text
semantic pointer
       ↓
target pointer representation
```

không ngược lại.

---

# 194.10. Object Format

Backend target quyết định:

```text
PE/COFF
ELF
Mach-O
WASM
```

Nhưng object format không nên xuất hiện trong semantic frontend.

Pipeline:

```text
Typed HIR
   ↓
MIR
   ↓
Target-independent optimization
   ↓
Target lowering
   ↓
Target-specific codegen
   ↓
ObjectWriter
   ↓
PE/ELF/Mach-O/WASM
```

---

# 194.11. Target-independent MIR

Đây là một quyết định rất quan trọng.

Phần lớn:

```text
ownership
capability
effects
async
traits
patterns
generic semantics
```

không phụ thuộc CPU.

Vì vậy:

```text
Verified MIR
```

là điểm cross-compilation cực mạnh.

Một source có thể:

```text
compile once semantically
```

sau đó lower thành nhiều target.

---

# 194.12. Nhưng MIR không hoàn toàn target-independent

Một số facts phải parameterized:

```text
usize
alignment
atomic width
SIMD availability
calling convention
pointer width
FP capabilities
```

Do đó:

```text
Target-independent semantics
+
Target parameterization
```

thay vì hai compiler hoàn toàn khác nhau.

---

# 194.13. Target Features

Compiler nhận:

```text
TargetFeatures
```

ví dụ:

```text
SSE2
AVX2
AVX512
NEON
SVE
FMA
AES
SHA
atomics
```

Code có thể:

```text
if comptime target.has_feature(...)
```

nhưng semantic behavior phải không thay đổi nếu feature không ảnh hưởng language semantics.

---

# 194.14. CPU Feature Dispatch

Axiom hỗ trợ explicit multiversioning:

```text
@target_feature("avx2")
fn process_avx2(...)
```

và:

```text
fn process(...)
```

có thể chọn implementation.

Compiler có thể generate:

```text
baseline
AVX2
AVX512
NEON
SVE
```

nhưng API vẫn một.

---

# 194.15. Không được biến CPU feature thành semantic dependency ngầm

Không được:

```text
if CPU supports AVX2
```

rồi để behavior của chương trình thay đổi tùy CPU nếu semantics không cho phép.

Target feature chủ yếu ảnh hưởng:

```text
performance
instruction selection
vectorization
implementation choice
```

---

# 194.16. Atomic Capabilities

Target phải khai báo:

```text
atomic i8
atomic i16
atomic i32
atomic i64
atomic pointer
lock-free status
memory ordering support
```

Axiom memory model vẫn thống nhất.

Nếu hardware không có atomic primitive tương ứng:

```text
compiler/runtime/library
```

có thể dùng fallback khi profile cho phép.

---

# 194.17. SIMD Capability

Tương tự:

```text
VectorWidth
VectorTypes
MaskTypes
InstructionSets
```

Compiler có thể lower:

```axiom
Vector<f32, 8>
```

sang:

```text
AVX
```

hoặc:

```text
NEON/SVE
```

hoặc fallback.

---

# 194.18. ABI Target Layer

Target ABI mô tả:

```text
register passing
stack passing
return registers
aggregate passing
vector passing
alignment
variadic functions
stack alignment
callee/caller saved registers
```

ABI lowering diễn ra sau semantic verification.

---

# 194.19. OS API Layer

Axiom không đưa Windows/Linux/macOS API vào Core.

Thay vào đó:

```text
std::os::windows
std::os::linux
std::os::macos
std::os::android
std::os::ios
```

Compiler chỉ cung cấp target facts.

Library cung cấp API.

---

# 194.20. SDK

Một target có thể cần:

```text
Windows SDK
Apple SDK
Android NDK
WASI SDK
Linux sysroot
```

SDK là external build input.

Không hard-code SDK vào compiler binary.

---

# 194.21. Sysroot

Cross compilation sử dụng:

```text
Sysroot
```

bao gồm:

```text
headers
startup objects
system libraries
ABI metadata
runtime libraries
linker support
```

Axiom package manager/build system biết sysroot dependency.

---

# 194.22. Linker Strategy

Axiom compiler không nhất thiết tự link mọi platform ngay từ bootstrap.

Giai đoạn đầu:

```text
Axiom codegen
      ↓
native object
      ↓
system linker / LLD
```

Giai đoạn self-host:

```text
Axiom ObjectWriter
      ↓
Axiom Linker
```

Nhưng architecture của compiler không phụ thuộc linker implementation.

---

# 194.23. Startup

Target profile mô tả startup:

```text
entry point
CRT requirements
TLS
stack initialization
argv/env
process initialization
runtime initialization
```

Ví dụ:

```text
hosted application
```

có startup phức tạp hơn:

```text
freestanding
```

---

# 194.24. Freestanding

Axiom phải hỗ trợ:

```text
@freestanding
```

hoặc target profile tương đương.

Chương trình có thể không có:

```text
allocator
filesystem
thread runtime
async runtime
reflection
Unicode runtime
network
```

Compiler chỉ link những gì thực sự cần.

---

# 194.25. Hosted

Hosted profile có thể cung cấp:

```text
std
OS
allocator
threads
filesystem
network
async
Unicode
process
```

nhưng đây là library/runtime composition, không phải Core requirement.

---

# 194.26. Target-specific code

Axiom dùng:

```axiom
@cfg(os = "windows")
```

hoặc tương đương.

Điều kiện compile-time phải được resolve trước codegen.

Không compile cả hai nhánh rồi mới loại bỏ.

---

# 194.27. Target-specific declarations

Có thể có:

```axiom
@cfg(target_arch = "aarch64")
fn fast_path(...)

@cfg(target_arch = "x86_64")
fn fast_path(...)
```

Resolver chỉ đưa declaration phù hợp vào semantic graph.

---

# 194.28. Cross-target package resolution

Một package có thể khai báo:

```text
Windows dependency
Linux dependency
Android dependency
Apple dependency
```

Package graph đã có target conditions từ BOOTSTRAP-187.

194 hoàn thiện semantic target model phía dưới nó.

---

# 194.29. Universal Binary

Apple có thể yêu cầu:

```text
x86_64 + arm64
```

Axiom build system có thể:

```text
compile target A
compile target B
merge artifacts
```

thành:

```text
Universal Mach-O
```

Đây là **artifact composition**, không phải compiler semantic đặc biệt.

---

# 194.30. Multi-target build

Một invocation có thể:

```text
ax build --target linux-x64
ax build --target linux-arm64
```

hoặc:

```text
ax build --targets linux-x64,linux-arm64
```

CompilerDB có thể cache:

```text
frontend semantic facts
```

dùng chung giữa các target khi hợp lệ.

---

# 194.31. Cross-target cache

Cache phải phân biệt:

```text
source semantics
```

với:

```text
target codegen
```

Ví dụ:

```text
Source
  ↓
HIR
  ↓
Verified MIR
```

có thể tái sử dụng.

Nhưng:

```text
MIR → x86 machine code
```

không dùng cho ARM.

---

# 194.32. Target-specific semantic invalidation

Thay đổi:

```text
x86 CPU feature
```

không cần re-run parser/typechecker.

Có thể chỉ invalidate:

```text
target lowering
optimization
codegen
```

Đây là lợi ích lớn của CompilerDB.

---

# 194.33. GPU Target

GPU đã có execution/storage domains.

194 bổ sung:

```text
TargetSpec
 └── GPU target set
      ├── CUDA-like target
      ├── Vulkan/SPIR-V
      ├── Metal
      ├── DirectX
      └── future GPU ISA
```

GPU compilation là một target graph riêng nhưng dùng chung semantic frontend.

---

# 194.34. Heterogeneous compilation

Một chương trình có thể chứa:

```axiom
fn cpu_fn(...)

@kernel
fn gpu_fn(...)
```

Compiler tạo:

```text
CPU artifact
GPU artifact
host/device metadata
launch ABI
resource descriptors
```

Một source package có thể tạo nhiều artifacts.

---

# 194.35. CPU/GPU target không được trộn execution domain

Một `@kernel` không thể vô tình gọi:

```text
filesystem
socket
OS syscall
arbitrary host pointer
```

GPU legality verifier vẫn hoạt động.

---

# 194.36. WASM target

WASM được mô hình hóa như target bình thường:

```text
Architecture = wasm32/wasm64
OS = wasm-host
ObjectFormat = wasm
ABI = WASM
```

Sau đó WASM-specific ABI layer xử lý:

```text
imports
exports
linear memory
tables
component interfaces
```

---

# 194.37. Target capability query

CompilerDB cung cấp:

```text
target.pointer_width()
target.endianness()
target.has_atomic(...)
target.has_feature(...)
target.os()
target.abi()
target.object_format()
```

cho:

- comptime
- code generation
- library configuration
- tooling

Nhưng những query này phải deterministic đối với TargetSpec.

---

# 194.38. Target không phải Runtime

Đây là invariant rất quan trọng.

```text
Target
≠
Runtime
≠
SDK
≠
OS API
```

Ví dụ:

```text
Linux ARM64
```

có thể có:

```text
freestanding
minimal runtime
full std
custom runtime
```

---

# 194.39. Cross compilation và comptime

Comptime chạy ở **host** mặc định.

Code đang được sinh ra dành cho:

```text
target
```

Do đó:

```text
comptime host
≠
target runtime
```

Ví dụ không được giả định:

```text
comptime read("/etc/...")
```

là filesystem của target.

Nếu muốn truy cập target filesystem/configuration phải là explicit build input.

---

# 194.40. Cross compilation và external tools

Build tool chạy trên host:

```text
shader compiler
resource compiler
code generator
linker
packager
```

được mô tả là:

```text
HostTool
```

Không nhầm với:

```text
TargetExecutable
```

---

# 194.41. Target SDK fingerprint

Artifact identity bao gồm:

```text
TargetSpec
SDK identity
Sysroot identity
Linker identity/contract
System libraries
```

nếu các thành phần đó ảnh hưởng binary.

---

# 194.42. Reproducibility

Cùng:

```text
source
lockfile
TargetSpec
SDK
compiler
profile
comptime inputs
```

phải tạo cùng semantic artifact trong reproducible mode.

---

# 194.43. Universal toolchain

Mục tiêu cuối cùng:

```text
ax
│
├── check
├── build
├── run
├── test
├── link
├── package
├── inspect
└── target
```

không cần:

```text
ax-linux
ax-windows
ax-arm
ax-wasm
```

Target backend được chọn bởi:

```text
TargetSpec
```

---

# 194.44. Invariants — BOOTSTRAP-194

### `ATARGET-20`
Axiom shall use a unified multi-target compiler architecture.

### `ATARGET-21`
Target selection shall be an explicit compiler/build input.

### `ATARGET-22`
Host and target environments shall remain semantically distinct.

### `ATARGET-23`
Build tools shall execute in the host domain unless explicitly modeled otherwise.

### `ATARGET-24`
Target identity shall include architecture, OS/environment, ABI, object format, pointer model, and relevant features.

### `ATARGET-25`
Target data layout shall be explicit and target-specific.

### `ATARGET-26`
Language semantics shall not depend on object-file format.

### `ATARGET-27`
Verified MIR shall remain substantially target-independent.

### `ATARGET-28`
Target-dependent facts shall be parameterized rather than duplicated across language semantics.

### `ATARGET-29`
CPU feature selection shall not silently alter language semantics.

### `ATARGET-30`
Atomic availability shall be represented as target capability.

### `ATARGET-31`
SIMD availability shall be represented as target capability.

### `ATARGET-32`
ABI lowering shall occur after semantic verification.

### `ATARGET-33`
System SDKs and sysroots shall be explicit build inputs.

### `ATARGET-34`
Target-specific source shall be selected before irrelevant declarations enter production semantic/codegen paths.

### `ATARGET-35`
Host filesystem/environment shall not be confused with target environment during cross compilation.

### `ATARGET-36`
Comptime host capabilities shall not implicitly represent target runtime state.

### `ATARGET-37`
Freestanding compilation shall not require a monolithic runtime.

### `ATARGET-38`
Hosted runtime components shall remain optional and composable.

### `ATARGET-39`
Cross-target builds shall reuse target-independent compiler artifacts when valid.

### `ATARGET-40`
Target-specific cache keys shall prevent incompatible machine artifacts from being reused.

### `ATARGET-41`
GPU targets shall remain explicit execution/storage domains.

### `ATARGET-42`
WASM shall be modeled as a first-class target rather than a special frontend.

### `ATARGET-43`
Universal binaries shall be produced by explicit multi-target artifact composition.

### `ATARGET-44`
Target configuration shall not silently change ownership, capability, or safety semantics.

### `ATARGET-45`
Target facts exposed to comptime shall be deterministic for a fixed TargetSpec.

### `ATARGET-46`
Cross compilation shall not require a separate language/compiler semantic implementation per target.

### `ATARGET-47`
A target backend may be replaced without changing the Core language semantics.

### `ATARGET-48`
Target and runtime identity shall remain distinct.

### `ATARGET-49`
Target/SDK/linker dependencies shall participate in reproducible build identity where observable.

### `ATARGET-50`
The same Axiom source shall be capable of producing multiple native targets without source-language forks except where explicitly target-conditioned.

---

# Kết luận BOOTSTRAP-194

Kiến trúc compiler hiện tại đã hình thành một đường rất rõ:

```text
                  Axiom Source
                       │
                ┌──────▼──────┐
                │ CompilerDB  │
                └──────┬──────┘
                       │
                Verified MIR
                       │
            ┌──────────┼──────────┐
            │          │          │
          x86-64      ARM64      WASM
            │          │          │
           LIR        LIR        LIR
            │          │          │
           PE/ELF    ELF/Mach-O   WASM
```

Điểm mạnh là **không phải xây lại semantic compiler cho từng OS/CPU**.

---

# BOOTSTRAP-195 — Linker, Object Model, Binary Layout & Final Native Image

**TRẠNG THÁI: NEXT**

Bây giờ còn một mắt xích rất quan trọng để đi từ:

```text
Machine IR
```

đến:

```text
.exe / ELF / Mach-O / WASM
```

Axiom cần một **Binary Image Model** thống nhất.

Không chỉ là “gọi linker”.

Cần thiết kế:

```text
Object
 ├── Sections
 ├── Symbols
 ├── Relocations
 ├── COMDAT/weak/alias
 ├── TLS
 ├── Unwind
 ├── Debug
 ├── Resources
 ├── Imports
 ├── Exports
 ├── Constructors
 ├── Metadata
 ├── Security properties
 └── Target-specific notes
```

và quan trọng hơn:

### Axiom có nên tự viết linker hoàn chỉnh?

Mục tiêu cuối cùng của user là:

> **Không phụ thuộc compiler và thư viện bên thứ ba.**

Điều này có nghĩa kiến trúc cuối cùng cần cho phép:

```text
Axiom Compiler
      ↓
Axiom Object Writer
      ↓
Axiom Linker
      ↓
Native Executable
```

nhưng trong bootstrap có thể:

```text
Axiom Compiler
      ↓
Object
      ↓
LLD/system linker
```

Sau đó thay dần bằng linker native Axiom.

**BOOTSTRAP-195 sẽ thiết kế chính tầng cuối cùng này, bao gồm relocation, symbol resolution, section GC, TLS, startup objects, static/dynamic linking, import/export và cách tạo native executable hoàn toàn không cần LLVM/LLD ở trạng thái self-hosted cuối cùng.**