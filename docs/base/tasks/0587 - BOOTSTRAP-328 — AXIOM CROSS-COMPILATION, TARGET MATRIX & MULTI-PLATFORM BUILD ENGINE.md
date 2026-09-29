# BOOTSTRAP-328 — AXIOM CROSS-COMPILATION, TARGET MATRIX & MULTI-PLATFORM BUILD ENGINE

Sau Platform-327, Axiom đã biết **một target có những capability/API nào**. Nhiệm vụ tiếp theo là biến điều đó thành một hệ thống build thực sự mạnh: **một source tree có thể build cho nhiều target, cross-compile, chọn backend đúng, kiểm tra dependency/ABI/platform trước khi codegen và tạo artifact reproducibly**.

Điểm quan trọng: đây **không phải Build Graph mới**. BOOTSTRAP-305 đã định nghĩa build graph. Task này bổ sung **target orchestration và cross-target semantics** cho build graph đó.

---

## 1. Mục tiêu

Axiom phải hỗ trợ:

```text
Windows x86_64
Windows ARM64
Linux x86_64
Linux ARM64
macOS ARM64
iOS ARM64
Android ARM64
WASM32
WASM64
freestanding targets
custom embedded targets
```

và có thể:

```text
host = Windows x86_64
target = Linux ARM64
```

mà không cần chạy compiler trên Linux ARM64.

Kiến trúc:

```text
                Axiom Source
                     │
                     ▼
               Semantic Build
                     │
          ┌──────────┴──────────┐
          │                     │
     Host Configuration    Target Configuration
          │                     │
          └──────────┬──────────┘
                     ▼
               Target Matrix
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Win64        Linux-A64     WASM32
        │            │            │
      PE/COFF      ELF         WASM
```

---

# 2. Host ≠ Target

Đây phải là invariant cơ bản.

```text
Host:
compiler đang chạy ở đâu

Target:
binary đang được tạo cho đâu
```

Ví dụ:

```text
Host = Windows x86_64
Target = Linux aarch64
```

Compiler được phép sử dụng:

```text
host filesystem
host CPU
host memory
```

để thực hiện compilation.

Nhưng semantic target phải lấy từ:

```text
TargetProfile(Linux/AArch64)
```

không phải host.

---

# 3. Build Configuration

Mỗi compilation phải có:

```text
BuildConfiguration {
    host
    target
    profile
    optimization
    debug
    features
    cpu_features
    platform_features
    runtime_profile
    allocator_profile
    panic_profile
    linker_profile
    reproducibility
}
```

Ví dụ:

```text
target = linux-aarch64
optimization = release
debug = false
panic = abort
runtime = minimal
cpu = generic
```

---

# 4. Target Triple chưa đủ

Target triple truyền thống:

```text
x86_64-linux-gnu
```

chưa mô tả đủ Axiom semantics.

Axiom cần:

```text
TargetSpec
```

bao gồm:

```text
architecture
os
abi
environment
endianness
pointer_width
atomic_widths
float_features
vector_features
calling_convention
object_format
link_format
platform_profile
runtime_profile
```

Ví dụ:

```text
TargetSpec {
    arch = AArch64
    os = Linux
    abi = SysV
    object = ELF
    pointer_width = 64
    endian = Little
}
```

---

# 5. Target fingerprint

Mỗi target phải có fingerprint:

```text
TargetFingerprint =
    hash(
        architecture
        OS
        ABI
        CPU baseline
        target features
        platform profile
        runtime profile
        object format
    )
```

Fingerprint tham gia:

- incremental compilation
- `.axif`
- cache
- artifact identity
- PGO
- compatibility checking

Nếu target thay đổi semantic assumptions:

```text
cache ≠ reusable
```

---

# 6. Target matrix

Một project có thể khai báo:

```toml
targets = [
    "windows-x86_64",
    "linux-x86_64",
    "linux-aarch64",
    "macos-aarch64",
    "wasm32"
]
```

Build system tạo:

```text
TargetMatrix
```

với mỗi target là một independent semantic/codegen graph.

Ví dụ:

```text
Project
 ├── Target Win64
 │    ├── semantic
 │    ├── platform
 │    ├── codegen
 │    └── linker
 │
 ├── Target Linux-A64
 │    ├── semantic
 │    ├── platform
 │    ├── codegen
 │    └── linker
 │
 └── Target WASM32
      ├── semantic
      ├── platform
      ├── codegen
      └── linker
```

---

# 7. Chia sẻ compilation giữa targets

Không phải mọi thứ đều compile lại.

Có ba mức:

```text
TargetIndependent
TargetParameterized
TargetSpecific
```

### TargetIndependent

Ví dụ:

```text
parser
generic AST
pure algorithms
business logic
type-independent source metadata
```

có thể cache dùng chung.

### TargetParameterized

Ví dụ:

```text
usize
pointer width
layout-dependent generic
cfg
atomic capabilities
```

phải specialize.

### TargetSpecific

Ví dụ:

```text
Win32 backend
Linux syscall backend
ARM NEON implementation
AVX2 implementation
WASM import
```

phải compile riêng.

---

# 8. Semantic compilation và codegen compilation

Axiom nên tách:

```text
Source
 ↓
Target-independent semantic analysis
 ↓
Target-dependent semantic specialization
 ↓
Optimization
 ↓
Target lowering
 ↓
Machine code
```

Điều này giúp cross-compilation hiệu quả.

Ví dụ:

```text
struct definitions
trait resolution
generic constraints
ownership rules
```

phần lớn không phụ thuộc CPU.

Trong khi:

```text
size_of(usize)
calling convention
vector ABI
atomic width
```

phụ thuộc target.

---

# 9. `@cfg` resolution

`@cfg` phải được resolve từ TargetSpec:

```axiom
@cfg(os = "windows")
fn backend() { ... }

@cfg(os = "linux")
fn backend() { ... }
```

Compiler không được parse cả hai thành hai implementation cạnh tranh rồi để type checker xử lý như overload bình thường.

Quá trình:

```text
Parse
 ↓
CFG condition evaluation
 ↓
Inactive declarations removed
 ↓
Normal semantic resolution
```

Điều này giảm ambiguity và compile cost.

---

# 10. Feature configuration

Phân biệt:

```text
OS
Architecture
CPU Feature
Platform Capability
Library Feature
Application Feature
```

Ví dụ:

```axiom
@cfg(cpu_feature = "avx2")
```

khác:

```axiom
@cfg(os = "windows")
```

và khác:

```axiom
@cfg(feature = "http")
```

Không được gom tất cả thành một namespace `cfg`.

---

# 11. Target feature hierarchy

Compiler cần:

```text
Target
 └── Architecture
      └── CPU baseline
           └── Optional features
```

Ví dụ:

```text
x86_64
 ├── SSE2
 ├── AVX
 ├── AVX2
 └── AVX512

AArch64
 ├── NEON
 ├── SVE
 └── SVE2
```

Compiler phải đảm bảo:

```text
required feature ⊆ guaranteed target features
```

Nếu không:

```text
compile error
```

hoặc tạo runtime dispatch nếu programmer yêu cầu.

---

# 12. Runtime dispatch

Cho phép:

```axiom
@multiversion
fn dot(a: view<f32>, b: view<f32>) -> f32 {
    ...
}
```

Compiler có thể tạo:

```text
dot.scalar
dot.avx2
dot.avx512
```

và:

```text
dot.dispatch
```

Runtime chọn implementation.

Nhưng dispatch không được thay đổi semantic behavior.

---

# 13. Cross compilation toolchain

Axiom compiler cuối cùng phải tự chủ, nhưng target có thể yêu cầu:

```text
system SDK
system libraries
linker inputs
frameworks
startup objects
platform metadata
```

Build system phải phân biệt:

```text
Axiom compiler
Axiom linker
Foreign linker
System SDK
Foreign libraries
```

Không được nhầm:

> "cross compilation" = "compiler phải có target OS runtime".

Compiler có thể emit object mà không cần target OS chạy trên máy host.

---

# 14. Sysroot

Target profile có:

```text
Sysroot
```

chứa:

```text
headers
libraries
startup objects
ABI metadata
frameworks
platform definitions
```

Nhưng Axiom không bắt buộc sử dụng C sysroot.

Có thể có:

```text
Axiom Native Sysroot
```

về sau.

Ví dụ:

```text
/sysroots/linux-aarch64/
    lib/
    abi/
    platform/
    axif/
```

---

# 15. Native Axiom SDK

Đây là bước quan trọng cho mục tiêu **không phụ thuộc compiler/library bên thứ ba**.

Cuối cùng có thể có:

```text
Axiom SDK
├── core
├── std
├── platform
├── libc-compat
├── system-abi
├── linker
├── startup
├── crt
└── target-specs
```

Nhưng:

```text
libc-compat
```

chỉ là interoperability layer, không phải dependency bắt buộc.

---

# 16. Startup model

Native binary không phải lúc nào cũng bắt đầu trực tiếp tại:

```text
main()
```

Axiom cần model:

```text
StartupContract
```

Ví dụ:

```text
Hosted
Freestanding
Kernel
Embedded
WASM
Mobile
```

Hosted:

```text
OS loader
 ↓
CRT/startup
 ↓
Axiom entry
 ↓
main
```

Freestanding:

```text
bootloader
 ↓
entry
```

---

# 17. Entry point

Không hard-code `main`.

Compiler/linker nên hỗ trợ:

```text
@entry
fn main(...)
```

hoặc platform-specific entry contract.

Ví dụ:

```axiom
@entry
fn kernel_main() -> never {
    ...
}
```

Compiler kiểm tra signature theo target.

---

# 18. Link profile

Mỗi target có:

```text
LinkProfile {
    object_format
    executable_format
    linker
    startup_objects
    default_libraries
    default_frameworks
    dynamic_loader
    relocation_model
    code_model
    section_rules
}
```

Ví dụ:

```text
Windows
 → PE/COFF

Linux
 → ELF

macOS/iOS
 → Mach-O

WASM
 → WASM module
```

---

# 19. Static vs dynamic

Build profile:

```text
link_mode = static
```

hoặc:

```text
link_mode = dynamic
```

hoặc:

```text
link_mode = hybrid
```

Compiler không được mặc định kéo dynamic runtime nếu project không yêu cầu.

---

# 20. Deployment profile

Build và deployment nên tách.

Ví dụ:

```text
Build:
linux-aarch64
```

nhưng deployment:

```text
minimum_glibc = X
required_kernel = Y
required_cpu = generic
```

hoặc:

```text
fully-static
```

Deployment contract phải được ghi trong artifact metadata.

---

# 21. Reproducible cross-build

Hai máy:

```text
Windows host A
Linux host B
```

cùng compile:

```text
target = linux-aarch64
source = identical
configuration = identical
```

phải tạo semantic-equivalent artifact.

Mục tiêu mạnh hơn:

```text
bit-for-bit reproducible
```

khi build profile yêu cầu.

Loại bỏ:

- timestamp ngẫu nhiên
- absolute paths
- random symbol ordering
- hash-map iteration order
- host-dependent metadata
- nondeterministic comptime input

---

# 22. Hermetic build

Build có thể chạy ở:

```text
local
CI
sandbox
remote build worker
```

và chỉ được sử dụng những dependency được khai báo.

Build graph phải biết:

```text
Source
Package
Comptime input
SDK
Sysroot
TargetSpec
Compiler version
Platform metadata
Environment capability
```

---

# 23. Cross-target comptime

Đây là điểm rất dễ sai.

Khi:

```text
host = x86_64 Windows
target = ARM64 Linux
```

`comptime` phải phân biệt:

```text
HostCompileEnvironment
TargetEnvironment
```

Ví dụ:

```axiom
comptime {
    size_of::<usize>()
}
```

phải trả:

```text
8
```

theo **target**, không phải theo host.

Trong khi:

```text
comptime filesystem read
```

đọc filesystem của host/build environment nếu capability cho phép.

---

# 24. `comptime` host/target contract

Cần hai namespace semantic:

```text
Host
Target
```

Ví dụ:

```axiom
comptime target.arch
comptime target.os
comptime target.pointer_width
```

và:

```axiom
comptime host.arch
comptime host.os
```

Không được nhầm lẫn.

---

# 25. Target-dependent constants

Compiler cung cấp:

```text
target.arch
target.os
target.abi
target.pointer_width
target.endianness
target.cache_line
target.page_size
target.atomic_widths
target.features
```

Nhưng chỉ những giá trị có contract ổn định mới được compile-time query.

---

# 26. Generic target programming

Không nên bắt programmer viết:

```axiom
#if ...
```

khắp nơi.

Thay vào đó:

```axiom
trait PlatformTimer {
    fn now() -> Instant;
}
```

và platform implementation:

```text
WindowsTimer
LinuxTimer
AppleTimer
WasmTimer
```

Target resolver chọn implementation.

Portable code chỉ dùng trait.

---

# 27. Target specialization

Compiler có thể specialize:

```text
generic<T>
```

theo:

```text
type
target
CPU feature
platform
```

nhưng không tạo ABI instability ngoài boundary.

Ví dụ:

```text
Vec<T>
```

có thể được optimize khác nhau trên:

```text
x86_64
AArch64
WASM
```

nhưng semantic API giống nhau.

---

# 28. Target compatibility

Package có thể khai báo:

```text
supports:
    windows-x86_64
    windows-aarch64
    linux-x86_64
    linux-aarch64
```

Nếu package chỉ hỗ trợ:

```text
windows-x86_64
```

mà project target:

```text
linux-aarch64
```

resolver phải báo lỗi ở dependency resolution, không chờ tới linker.

---

# 29. Target capability negotiation

Package metadata:

```text
PackageTargetContract {
    supported_targets
    required_features
    required_platform_capabilities
    required_abis
    required_system_libs
}
```

Dependency resolver thực hiện:

```text
Project requirements
        ∩
Package capabilities
        ∩
Target capabilities
```

Nếu tập hợp rỗng:

```text
target unsupported
```

---

# 30. Fat binaries

Axiom có thể hỗ trợ:

```text
fat binary
```

ví dụ:

```text
macOS:
    x86_64
    arm64
```

hoặc:

```text
CPU multiversion binary
```

Nhưng cần phân biệt:

```text
MultiTargetArtifact
```

và:

```text
MultiCPUArtifact
```

Artifact manifest mô tả từng slice.

---

# 31. Universal package

Package có thể chứa:

```text
package.axpkg
├── windows-x86_64/
├── linux-x86_64/
├── linux-aarch64/
├── macos-arm64/
└── wasm32/
```

Dependency resolver chọn đúng artifact.

Không compile lại source nếu package đã có binary/semantic artifact phù hợp.

---

# 32. `.axif` và cross-target

Một package có thể có:

```text
foo.axif
```

và nhiều target section:

```text
TARGETS
 ├── linux-x86_64
 ├── linux-aarch64
 ├── windows-x86_64
 └── wasm32
```

Semantic API có thể giống nhau.

ABI/layout/platform contract khác nhau.

---

# 33. Cache architecture

Cache key:

```text
SourceFingerprint
+
SemanticFingerprint
+
CompilerSemanticVersion
+
TargetFingerprint
+
FeatureFingerprint
+
ComptimeInputFingerprint
+
DependencyFingerprint
```

Không dùng:

```text
source hash
```

đơn thuần.

---

# 34. Distributed build

Kiến trúc phải cho phép:

```text
Developer
   │
   ▼
Build Coordinator
   │
   ├── Windows worker
   ├── Linux worker
   ├── ARM worker
   └── WASM worker
```

Worker chỉ cần:

```text
compiler
target SDK
cache
declared dependencies
```

Không cần host OS giống target.

---

# 35. Build scheduler

Build scheduler tối ưu:

```text
independent target builds
```

song song.

Ví dụ:

```text
Win64 ───────┐
Linux x64 ───┼── parallel
Linux ARM ───┤
WASM ────────┘
```

Các phần shared semantic analysis có thể reuse.

---

# 36. Diagnostics

Cross compile error phải nói rõ:

```text
AXTARGET031

Target:
    linux-aarch64

Dependency:
    foo@2.4

Unsupported requirement:
    x86_64-only implementation

Available targets:
    windows-x86_64
    linux-x86_64
```

Không chỉ báo:

```text
linker error
```

---

# 37. Compiler architecture

Thêm:

```text
compiler/target/
    spec/
        target_spec.ax
        target_triple.ax
        target_fingerprint.ax

    profile/
        target_profile.ax
        platform_profile.ax
        runtime_profile.ax
        link_profile.ax

    matrix/
        target_matrix.ax
        target_instance.ax

    cfg/
        cfg_evaluator.ax

    feature/
        cpu_feature.ax
        target_feature.ax
        feature_solver.ax

    cache/
        target_cache.ax

    deployment/
        deployment_contract.ax
```

CompilerDB:

```text
TargetSpecDB
TargetProfileDB
TargetMatrixDB
TargetFeatureDB
TargetCacheDB
DeploymentDB
```

---

# 38. API chính

```text
resolve_target()
load_target_spec()
validate_target()
compute_target_fingerprint()

evaluate_cfg()
resolve_target_features()
check_feature_requirements()

create_target_instance()
create_target_matrix()

resolve_platform_dependency()
resolve_target_dependency()

compute_cross_target_cache_key()
check_cross_target_compatibility()

build_target()
build_target_matrix()

generate_fat_binary()
generate_universal_package()

inspect_target()
explain_target_failure()
```

CLI:

```text
axiom target list
axiom target inspect
axiom target check
axiom target matrix
axiom target build
axiom target features
axiom target deps
axiom target explain
```

---

# 39. Invariants

```text
ATARGET-01
Host and target environments are semantically distinct.

ATARGET-02
Target semantics are determined by TargetSpec, never by host properties.

ATARGET-03
@cfg selection is target-deterministic.

ATARGET-04
Target-dependent constants use target semantics.

ATARGET-05
Comptime host capabilities and target properties are explicitly separated.

ATARGET-06
Target fingerprint participates in cache identity.

ATARGET-07
Different ABI targets cannot share ABI artifacts implicitly.

ATARGET-08
Target-independent semantic artifacts may be shared when proven safe.

ATARGET-09
Target-dependent layouts must be recomputed for each incompatible target.

ATARGET-10
Unsupported target dependencies fail before code generation.

ATARGET-11
CPU feature requirements must be validated before generating feature-dependent code.

ATARGET-12
Runtime CPU dispatch must never execute an unsupported implementation.

ATARGET-13
Cross compilation must not require execution of target binaries on the host.

ATARGET-14
Build configuration must be deterministic.

ATARGET-15
Reproducible mode must reject undeclared nondeterministic inputs.

ATARGET-16
Platform capabilities participate in dependency resolution.

ATARGET-17
System SDK dependencies are explicit build inputs.

ATARGET-18
Target linker configuration is target-specific.

ATARGET-19
Startup/entry contracts are target-specific.

ATARGET-20
Freestanding targets must not acquire hosted runtime dependencies implicitly.

ATARGET-21
WASM target semantics are distinct from native OS targets.

ATARGET-22
Multi-target artifacts must identify each target slice independently.

ATARGET-23
Cross-target cache reuse requires semantic compatibility proof.

ATARGET-24
Target-specific optimizer assumptions require explicit target guarantees.

ATARGET-25
Target requirements participate in .axif and binary compatibility fingerprints.

ATARGET-26
Target matrix builds may execute independently and in parallel.

ATARGET-27
A target backend must not silently fall back to a different target.

ATARGET-28
Foreign system libraries must be resolved against the target, not the host.

ATARGET-29
Target-specific security requirements participate in build validation.

ATARGET-30
The same source + same compiler semantics + same target configuration must produce deterministic semantic output.
```

---

# 40. Kết quả sau BOOTSTRAP-328

Chuỗi architecture lúc này trở thành:

```text
324  ABI
 │
325  Dynamic Components / Plugins / Hot Reload
 │
326  FFI / Foreign Interop
 │
327  OS / Platform API
 │
328  Cross Compilation / Target Matrix
 │
 ▼
Native Multi-Platform Axiom
```

Và quan trọng hơn, Axiom hiện có khả năng đi từ:

```text
một source tree
```

tới:

```text
Windows EXE
Linux ELF
macOS Mach-O
iOS binary
Android binary
WASM module
Freestanding binary
```

mà **không cần biến ngôn ngữ Core thành một tập hợp các đặc biệt hóa cho từng hệ điều hành**.

Nguyên tắc kiến trúc được chốt ở task này là:

> **Host quyết định nơi compiler chạy. Target quyết định chương trình được hiểu và sinh ra như thế nào. Platform quyết định môi trường mà chương trình có thể sử dụng. ABI quyết định binary giao tiếp ra sao. FFI quyết định foreign code được tin tưởng ở mức nào.**