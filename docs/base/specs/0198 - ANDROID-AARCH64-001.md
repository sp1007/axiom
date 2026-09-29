Tiếp tục với **Android-AArch64-001**. Tôi đã kiểm tra lại các điểm Android-specific hiện tại vì Android khác Linux desktop ở lớp platform/linker, dù vẫn dùng ELF/AArch64. Android dùng Bionic và dynamic linker riêng; dynamic linker chịu trách nhiệm nạp `DT_NEEDED` và resolve undefined symbols, đồng thời Android có linker namespaces để kiểm soát phạm vi thư viện. citeturn0search35turn0search37

# ANDROID-AARCH64-001

Mục tiêu:

```text
Axiom
  ↓
AArch64
  ↓
AAPCS64 / Android ABI
  ↓
ELF64
  ↓
Bionic / Android dynamic linker
  ↓
libfoo.so
  ↓
Android application
```

Điểm quan trọng nhất:

> **Android không phải một backend mới. Nó là một Platform Target trên AArch64 + ELF.**

---

## 1. Target hierarchy

Không tạo:

```text
compiler/backend/android/
```

Thay vào đó:

```text
targets/
├── linux_aarch64/
├── macos_aarch64/
└── android_aarch64/
```

và dùng chung:

```text
compiler/backend/aarch64/
compiler/object/elf/
compiler/linker/elf/
compiler/abi/aarch64/
```

Kiến trúc:

```text
                 AArch64
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
       Linux      macOS    Android
          │         │         │
         ELF      Mach-O    ELF
```

---

# 2. Target descriptor

```text
AndroidAArch64Target {
    architecture: AArch64
    os: Android
    environment: Android
    object_format: ELF64
    endian: Little
    pointer_width: 64
    abi: AAPCS64
}
```

Nhưng cần thêm:

```text
AndroidApiLevel
```

Ví dụ:

```text
android-21
android-26
android-30
android-35
...
```

API level là **platform compatibility constraint**, không phải language version.

---

# 3. API level phải là một phần của target identity

Build identity:

```text
Target {
    arch
    os
    abi
    object_format
    api_level
}
```

Ví dụ:

```text
aarch64-android-api26
aarch64-android-api35
```

Điều này cực kỳ quan trọng vì API level quyết định API/platform surface mà native program có thể dựa vào.

Android NDK hiện cung cấp API-level-specific native APIs. citeturn0search0

---

# 4. Không phụ thuộc NDK để compile

Android documentation mô tả NDK/CMake là toolchain để build native C/C++. citeturn0search1

Axiom không nên yêu cầu chúng.

Mục tiêu:

```text
Axiom compiler
 ├── AArch64 codegen
 ├── ELF writer
 ├── ELF linker
 └── Android platform metadata
```

Không:

```text
Axiom
 ↓
clang
 ↓
lld
 ↓
.so
```

NDK chỉ có thể được dùng như:

- API/header reference;
- platform metadata source;
- testing/reference environment.

Không phải compiler dependency.

---

# 5. Android native artifact

Android native library nằm trong APK theo ABI directory. Với ARM64, directory là:

```text
lib/arm64-v8a/
```

citeturn0search11

Vì vậy artifact:

```text
libfoo.so
```

được package thành:

```text
app.apk
└── lib/
    └── arm64-v8a/
        └── libfoo.so
```

Đây là **packaging layer**, không phải ELF linker.

---

# 6. Tách `.so` generation khỏi APK

Pipeline:

```text
Axiom
 ↓
ELF shared object
 ↓
Android native artifact
 ↓
APK/AAB packaging
```

Không:

```text
Axiom ELF linker
 ↓
APK
```

Tạo:

```text
tools/android/
├── target.ax
├── api.ax
├── manifest.ax
├── apk.ax
├── zip.ax
└── packaging.ax
```

sau này.

---

# 7. Android ABI

Về calling convention, AArch64 Android sử dụng AArch64 procedure-call conventions; vì vậy phần lớn ABI register classification có thể dùng chung với AArch64 ABI layer.

```text
compiler/abi/aarch64/
```

không nên tạo:

```text
compiler/abi/android_aarch64/
```

trừ khi có khác biệt ABI thực sự.

Platform-specific khác biệt đặt ở:

```text
targets/android_aarch64/
```

---

# 8. FFI

Android native APIs chủ yếu được expose qua C-compatible interfaces trong NDK.

Do đó:

```axiom
extern "C"
fn ...
```

vẫn đi qua:

```text
Axiom FFI
 ↓
C ABI
 ↓
AArch64 ABI
 ↓
ELF
```

Không tạo một ABI:

```text
extern "android"
```

Đây là quyết định nên **freeze**.

---

# 9. Bionic là platform library

Không coi:

```text
libc.so
```

là Core runtime.

Architecture:

```text
Axiom Core
    ↓
Axiom Std
    ↓
Android platform layer
    ↓
Bionic
```

Nếu chương trình không cần libc:

```text
Axiom
 ↓
Android native interface
```

vẫn phải có khả năng build artifact phù hợp.

---

# 10. Dynamic linker

Android dynamic linker:

```text
/system/bin/linker64
```

là thành phần runtime nạp và liên kết ELF shared objects, xử lý `DT_NEEDED` và symbol resolution. citeturn0search35

Axiom linker chỉ tạo metadata để dynamic linker xử lý.

Do đó:

```text
Axiom linker
      ↓
DT_NEEDED
dynsym
relocations
...
      ↓
Android dynamic linker
```

Compiler **không mô phỏng** Android dynamic linker.

---

# 11. Linker namespace

Đây là khác biệt quan trọng so với Linux desktop.

Android có linker namespace để kiểm soát:

- library search;
- library visibility;
- symbol resolution.

citeturn0search37

Vì vậy generic linker model cần thêm:

```text
DynamicEnvironment {
    platform
    namespace
    dependencies
}
```

nhưng **không đưa namespace vào Core ABI**.

---

# 12. Namespace không phải linker namespace trong Axiom source

Không tạo:

```axiom
namespace system
```

cho mục đích này.

Đó là:

```text
Runtime Dynamic Linking Namespace
```

khác hoàn toàn:

```text
Axiom Module Namespace
```

Hai hệ thống phải độc lập.

---

# 13. Android library dependency

Generic:

```text
DynamicDependency {
    name
    kind
}
```

Android mapping:

```text
libfoo.so
libbar.so
```

và system libraries.

Không cho compiler tự suy ra:

```text
foo() → libfoo.so
```

trừ khi platform API metadata khai báo điều đó.

---

# 14. JNI không phải ABI của Axiom

Đây là điểm rất quan trọng.

JNI là một **interop protocol/API**, không phải calling convention mới.

Kiến trúc:

```text
Axiom
 ↓
C ABI
 ↓
JNI ABI/API
 ↓
ART
```

Ví dụ Android có thể load native library bằng `System.loadLibrary(...)` và gọi native function qua JNI. citeturn0search6

Axiom không cần:

```text
extern "JNI"
```

ở Core v1.

---

# 15. JNI binding layer

Sau này tạo:

```text
std/android/
├── jni/
│   ├── env.ax
│   ├── object.ax
│   ├── string.ax
│   ├── array.ax
│   ├── method.ax
│   └── native.ax
```

Đây là library.

Không compiler magic.

---

# 16. JNI function representation

JNI có những function signature phức tạp.

Axiom wrapper nên biến:

```text
JNIEnv*
jobject
jstring
jint
```

thành các Axiom types.

Ví dụ conceptual:

```axiom
fn native_add(env: JNIEnv, obj: JObject, a: i32, b: i32) -> i32
```

nhưng representation thực tế vẫn do JNI ABI wrapper kiểm soát.

---

# 17. Ownership không được giả định từ JNI

Một `jobject` không nên tự động trở thành:

```text
Box<JObject>
```

hoặc:

```text
Rc<JObject>
```

JNI handle lifetime là runtime contract.

Do đó:

```text
JNIHandle
```

là một foreign resource/capability.

Axiom wrapper phải mô tả:

```text
borrowed
local reference
global reference
weak global reference
```

nếu muốn cung cấp API an toàn.

---

# 18. Đây là ví dụ hoàn hảo cho nguyên tắc ownership

Axiom không nói:

> "Mọi pointer đều là ownership."

Thay vào đó:

```text
Foreign Handle
    ↓
foreign ownership contract
```

Sau đó wrapper tạo capability phù hợp.

---

# 19. Android native library entry

Đối với `.so`:

```text
libfoo.so
```

không có:

```text
main()
```

là application entry.

Nó có:

```text
exports
imports
initialization
```

Application framework/Java/Kotlin side hoặc native framework sẽ load library.

Do đó Axiom artifact model cần phân biệt:

```text
ArtifactKind::Executable
ArtifactKind::SharedLibrary
```

---

# 20. Library initialization

Không nên đưa global constructor magic vào Core.

Nếu cần:

```text
@init
```

sau này, nó phải có semantic model rõ ràng.

MVP tốt nhất:

```text
explicit initialization
```

Ví dụ:

```axiom
pub fn initialize() -> Result<unit, Error>
```

Thay vì:

```text
hidden global constructor
```

Điều này cũng giúp deterministic startup.

---

# 21. Android app packaging

Đừng biến compiler thành Gradle.

Tạo:

```text
Axiom Android Packager
```

có thể tạo:

```text
APK
```

từ:

```text
AndroidManifest.xml
resources
classes.dex
lib/arm64-v8a/*.so
assets
```

Nhưng compiler không cần hiểu Java/Kotlin.

---

# 22. Native-only Android

Axiom cũng nên hỗ trợ:

```text
native shared library
```

không nhất thiết build cả APK.

Ví dụ:

```text
axiom build lib.ax \
    --target aarch64-android \
    --artifact shared
```

→

```text
lib.ax.so
```

để ứng dụng Android khác package.

---

# 23. Android-specific C libraries

Không hard-code danh sách vào compiler.

Tạo platform manifest:

```text
targets/android_aarch64/platform.ax
```

Conceptual:

```text
PlatformLibrary {
    name
    soname
    api_min
    api_max
    symbols
}
```

Ví dụ:

```text
libc.so
libdl.so
liblog.so
```

---

# 24. API-level verifier

Nếu source dùng:

```text
android_api_30_function()
```

nhưng target:

```text
api26
```

compiler phải báo:

```text
AX_ANDROID_0001
API requires Android API level 30
target provides API level 26
```

Đây là compile-time platform verification.

Không phải type system mới.

---

# 25. Platform capability model

Tạo:

```text
PlatformCapability {
    name
    introduced_api
}
```

Resolver:

```text
required API <= target API
```

Nếu không:

```text
compile error
```

Nếu runtime fallback được phép:

```text
@available(...)
```

sau này.

---

# 26. `@available`

Có thể thiết kế:

```axiom
@available(android >= 30)
fn new_api() { ... }
```

Compiler có thể kiểm tra control flow:

```axiom
if android_api >= 30 {
    new_api()
}
```

Nhưng **chưa nên freeze syntax này** trong v1.0.

Trước mắt platform metadata đủ.

---

# 27. Android linker hardening

Axiom linker cần tránh tạo artifact dựa vào giả định:

```text
"Linux filesystem layout"
```

Thay vào đó:

```text
AndroidLinkPolicy {
    dynamic_loader
    library_paths
    namespace_policy
    relocation_policy
    symbol_policy
}
```

---

# 28. Native library visibility

Android có những quy tắc về native shared-library visibility và namespace. Ví dụ tài liệu Android ghi nhận rằng non-NDK vendor shared libraries không mặc định accessible với app target Android 12/API 31+, trừ khi khai báo phù hợp. citeturn0search3

Vì vậy Axiom **không được giả định**:

```text
mọi .so trên hệ thống đều link được.
```

Platform metadata phải quyết định library availability.

---

# 29. Android target profile

Đề xuất:

```text
AndroidProfile {
    api_level
    abi
    min_sdk
    platform_libraries
    dynamic_linker_policy
    packaging_policy
}
```

Không đặt trong language source.

---

# 30. Compiler command

MVP:

```text
axiom build app.ax \
    --target aarch64-android \
    --api-level 26
```

Output:

```text
build/
└── aarch64-android-api26/
    └── app.so
```

Hoặc:

```text
axiom build app.ax \
    --target aarch64-android \
    --api-level 26 \
    --artifact apk
```

sau này.

---

# 31. Không cần NDK để tạo `.so`

Acceptance test cực kỳ quan trọng:

```text
Axiom source
 ↓
Axiom AArch64 backend
 ↓
Axiom ELF writer
 ↓
Axiom ELF linker
 ↓
libhello.so
```

Không:

```text
clang
ld.lld
gcc
```

Đây là một trong những acceptance test quan trọng nhất cho mục tiêu "không phụ thuộc compiler bên thứ ba".

---

# 32. APK packaging là bước sau

Không gộp vào milestone này.

Thứ tự:

```text
ANDROID-AARCH64-001
    ↓
valid Android .so
    ↓
ANDROID-PACK-001
    ↓
APK
    ↓
ANDROID-JNI-001
    ↓
JNI integration
```

Như vậy debug dễ hơn rất nhiều.

---

# 33. Acceptance test A — pure native library

Source:

```axiom
pub extern "C"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Build:

```text
aarch64-android
api26
shared
```

Expected:

```text
libadd.so
```

Kiểm tra:

```text
ELF64
AArch64
ET_DYN
dynamic symbols
relocations
```

---

# 34. Acceptance test B — Android executable

Nếu target environment cho phép native executable:

```text
fn main() -> i32 {
    42
}
```

Expected:

```text
AArch64 ELF
entry
exit = 42
```

Test này kiểm tra:

```text
Axiom startup
+
Android process ABI
```

---

# 35. Acceptance test C — JNI

Architecture:

```text
Kotlin/Java
      ↓
JNI
      ↓
libaxiom.so
      ↓
Axiom function
```

Không cần compiler hiểu Kotlin.

Axiom chỉ cần generate đúng:

```text
JNI-compatible exported symbol
```

và ABI.

---

# 36. Acceptance test D — API level

Target:

```text
api26
```

Code yêu cầu:

```text
api30
```

Expected:

```text
AX_ANDROID_0001
```

Không tạo binary rồi mới thất bại khi link.

---

# 37. Acceptance test E — dynamic dependency

```text
libfoo.so
 ↓
DT_NEEDED
 ↓
Android dynamic linker
```

Kiểm tra Axiom linker tạo đúng dependency metadata.

Android dynamic linker sau đó chịu trách nhiệm load dependency và resolve symbols. citeturn0search35

---

# 38. Acceptance test F — no external toolchain

CI phải có job:

```text
PATH = minimal
```

không có:

```text
clang
gcc
ld
lld
as
```

nhưng vẫn:

```text
Axiom source
 ↓
Android .so
```

được.

Đây mới là test thực sự cho kiến trúc.

---

# 39. Android invariants

```text
AANDROID-20
Android is a platform target, not a language mode.

AANDROID-21
Android AArch64 reuses the AArch64 backend.

AANDROID-22
Android AArch64 reuses the ELF object model.

AANDROID-23
Android API level is part of target identity.

AANDROID-24
API level does not alter language semantics.

AANDROID-25
Bionic is a platform library layer, not Core runtime.

AANDROID-26
Android dynamic linking is performed by the platform dynamic linker.

AANDROID-27
Axiom linker emits dynamic-link metadata but does not emulate runtime loading.

AANDROID-28
Android linker namespaces are platform runtime concepts.

AANDROID-29
JNI is an interop API, not a Core calling convention.

AANDROID-30
Foreign JNI handles do not imply Axiom ownership.

AANDROID-31
Android native libraries are ordinary Axiom shared-library artifacts.

AANDROID-32
APK packaging is separate from ELF linking.

AANDROID-33
Axiom can produce Android ELF artifacts without an external C/C++ compiler.

AANDROID-34
Platform library availability is API-level constrained.

AANDROID-35
Platform API compatibility is checked before code generation when possible.

AANDROID-36
Android library visibility is not inferred from source imports.

AANDROID-37
Android dynamic dependencies are explicit linker metadata.

AANDROID-38
Axiom module namespaces are distinct from Android linker namespaces.

AANDROID-39
Android platform metadata is external to language semantics.

AANDROID-40
JNI ownership/lifetime contracts must be explicit.

AANDROID-41
Android shared libraries do not require a C runtime supplied by Axiom.

AANDROID-42
Android packaging does not alter native ABI semantics.

AANDROID-43
API-level target identity participates in build reproducibility.

AANDROID-44
Android target builds remain deterministic under fixed platform metadata.
```

---

# 40. Kiến trúc platform hiện tại

Sau milestone này:

```text
                         Axiom
                           │
                    Target-independent
                           │
                  ┌────────┴────────┐
                  │                 │
                 LIR            Debug IR
                  │                 │
          ┌───────┼───────┐    ┌────┴────┐
          ↓       ↓       ↓    ↓         ↓
       x86-64   AArch64  RISC-V CodeView DWARF
          │       │
    ┌─────┼───┐   ├───────────────┐
    ↓     ↓   ↓   ↓       ↓       ↓
 Windows Linux macOS Linux Android iOS
   PE    ELF   MachO ELF   ELF    MachO
```

Điểm quan trọng nhất là:

**Android không tạo thêm compiler core.**

Nó chỉ thêm:

```text
Target metadata
Platform ABI policy
Platform libraries
API-level verifier
Packaging layer
```

---

# 41. Tiếp theo: ANDROID-PACK-001

Bây giờ phần native `.so` đã có kiến trúc. Bước kế tiếp hợp lý là **Android packaging**, nhưng không nên nhảy ngay vào APK/AAB.

Ta cần trước tiên thiết kế:

```text
ANDROID-PACK-001
├── APK container
├── ZIP writer
├── AndroidManifest.xml
├── resources/assets model
├── lib/<abi>/*.so
├── deterministic packaging
├── APK signing abstraction
├── alignment
└── APK verifier
```

Sau đó mới:

```text
ANDROID-JNI-001
```

và:

```text
IOS-MACHO-001
```

Đặc biệt, **APK signing phải được tách khỏi compiler/linker**, giống như code signing của Apple. Điều này giữ cho Axiom native compiler không bị biến thành một Android Studio/Gradle replacement.