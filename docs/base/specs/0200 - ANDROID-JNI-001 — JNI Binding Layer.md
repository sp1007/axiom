Tiếp tục với **ANDROID-JNI-001**. Tôi đã đối chiếu với tài liệu Android hiện tại để tránh thiết kế JNI dựa trên giả định cũ. JNI là lớp interop giữa Java/Kotlin và native code; Android cũng hỗ trợ đăng ký native methods trong `JNI_OnLoad`, thay vì bắt buộc dựa vào tên hàm JNI tự động. citeturn0search2turn0search8

# ANDROID-JNI-001 — JNI Binding Layer

Mục tiêu:

```text
Java/Kotlin
    ↓
JNI
    ↓
Axiom JNI library
    ↓
Axiom C ABI
    ↓
AArch64 ABI
    ↓
libaxiom.so
```

**Không thêm JNI vào Axiom Core.**

---

## 1. Kiến trúc

Tạo:

```text
std/android/
└── jni/
    ├── vm.ax
    ├── env.ax
    ├── object.ax
    ├── class.ax
    ├── method.ax
    ├── field.ax
    ├── string.ax
    ├── array.ax
    ├── reference.ax
    ├── exception.ax
    ├── native.ax
    ├── registration.ax
    ├── signature.ax
    └── tests/
```

JNI là **foreign platform library**.

---

# 2. Ba tầng JNI

Không trộn mọi thứ vào một `JNIEnv`.

```text
JNI API
├── Raw JNI ABI
├── Safe-ish Axiom wrappers
└── Application-level bindings
```

### Raw

```text
JNIEnvRaw
JavaVMRaw
JObjectRaw
JClassRaw
JStringRaw
...
```

Đây là `unsafe`.

### Wrapper

```text
JNIEnv
JavaObject
JavaClass
JavaString
...
```

Quản lý capability/lifetime ở mức Axiom.

### Generated binding

Sau này:

```text
android.foo.Bar
```

có thể generate:

```text
Bar
Bar.method(...)
```

nhưng đây là tooling/library, không phải Core.

---

# 3. JNI handle không phải pointer thông thường

Đây là điểm phải freeze.

Không định nghĩa:

```text
type JObject = *mut ...
```

theo semantic model.

Thay vào đó:

```text
foreign type JObject
```

hoặc tương đương một opaque foreign representation.

Lý do: JNI references có semantics do VM quản lý. Android cũng coi JNI local/global references là các reference giữ object reachable từ GC roots. citeturn0search1

Do đó:

```text
JObject != *mut JavaObjectMemory
```

---

# 4. Foreign handle model

Đưa vào FFI abstraction:

```text
ForeignHandle<T> {
    raw
    ownership
    domain
}
```

Ví dụ:

```text
ForeignHandle<JavaObject>
```

nhưng:

```text
domain = JVM
```

Không phải:

```text
domain = AxiomHeap
```

---

# 5. Local reference

JNI local reference có lifetime gắn với native invocation/frame.

Wrapper:

```text
LocalRef<T>
```

semantic:

```text
LocalRef<T>:
    non-owning VM capability
    valid only within JNI local frame
```

Không được:

```text
return local_ref
```

ra ngoài nếu wrapper không chuyển nó sang một reference type có lifetime hợp lệ.

---

# 6. Global reference

```text
GlobalRef<T>
```

khác hoàn toàn:

```text
LocalRef<T>
```

Global reference có thể sống lâu hơn native invocation.

Do đó:

```text
LocalRef<T>
    ──promote──>
GlobalRef<T>
```

là explicit operation.

Không implicit.

---

# 7. Weak global

Thêm:

```text
WeakGlobalRef<T>
```

nhưng semantic phải phản ánh:

```text
may become invalid / cleared
```

Không coi weak reference là ownership.

---

# 8. API

Conceptual:

```axiom
fn new_global<T>(env: JNIEnv, local: LocalRef<T>)
    -> Result<GlobalRef<T>, JniError>
```

và:

```axiom
fn new_weak_global<T>(...)
    -> Result<WeakGlobalRef<T>, JniError>
```

Drop:

```text
GlobalRef<T>.drop()
```

gọi VM release operation.

Nhưng:

> Drop của Axiom wrapper không có nghĩa Java object bị destroy.

Nó chỉ release **JNI reference**.

---

# 9. Đây là ví dụ AMEM-43

Ta có ba lifetime:

```text
Java object lifetime
JNI reference lifetime
Axiom wrapper lifetime
```

Chúng không đồng nhất.

```text
Axiom Drop
    ↓
release JNI reference
    ↓
Java object may remain alive
```

GC của Java/ART quyết định object memory.

Axiom không quản lý Java heap.

---

# 10. `JNIEnv`

`JNIEnv` phải là thread-local capability.

Không nên:

```text
static JNIEnv GLOBAL_ENV
```

và chia sẻ giữa threads.

JNI environment gắn với native thread/VM interaction; mỗi thread cần environment phù hợp.

Thiết kế:

```text
JNIEnv<'thread>
```

nhưng **không expose lifetime syntax `'thread` cho programmer**.

Axiom compiler vẫn kiểm tra capability nội bộ.

---

# 11. Vì Axiom không có lifetime syntax

Ta biểu diễn:

```text
JNIEnv
```

và compiler intrinsic capability:

```text
Capability {
    provenance = CurrentJNIThread
}
```

Khi rời thread:

```text
capability invalid
```

Không cần programmer viết lifetime.

---

# 12. Thread attachment

Native thread tạo bởi Axiom:

```text
Axiom thread
    ↓
JNI call
```

không được mặc định giả định đã attach JVM.

Library API:

```text
fn attach_current_thread(vm: JavaVM)
    -> Result<AttachedEnv, JniError>
```

và:

```text
fn detach_current_thread(...)
```

hoặc scoped abstraction:

```text
with_attached_thread(vm, fn)
```

---

# 13. Structured attachment

Ưu tiên:

```axiom
with_jni(vm) |env| {
    ...
}
```

Compiler/lifetime verifier đảm bảo:

```text
env
```

không escape khỏi scope.

Điều này rất hợp với triết lý Axiom:

> programmer không quản lý lifetime bằng annotation; compiler kiểm tra capability.

---

# 14. `JavaVM`

```text
JavaVM
```

là process/VM-level handle.

Khác:

```text
JNIEnv
```

Semantic:

```text
JavaVM:
    VM identity

JNIEnv:
    thread-local invocation environment
```

Không hoán đổi.

---

# 15. `JClass`

```text
JClass
```

là một Java reference.

Không phải:

```text
TypeId
```

của Axiom.

Do đó:

```text
Axiom TypeId
```

và:

```text
Java Class identity
```

hoàn toàn khác.

---

# 16. Class lookup

Raw:

```text
FindClass(...)
```

wrapper:

```text
fn find_class(
    env: JNIEnv,
    name: JniClassName
) -> Result<LocalRef<JClass>, JniError>
```

`JniClassName` nên là type riêng để tránh nhầm:

```text
"java/lang/String"
```

với:

```text
"java.lang.String"
```

---

# 17. Method ID

JNI method ID không phải Java method object.

Tạo:

```text
MethodId<T>
```

opaque.

Ví dụ:

```text
fn get_method(
    class: JClass,
    name: MethodName,
    signature: MethodSignature
) -> Result<MethodId, JniError>
```

Method ID có VM-defined identity.

---

# 18. Signature

Đây là nơi nên có một parser nhỏ.

Ví dụ JNI signature:

```text
(I)I
```

hoặc:

```text
(Ljava/lang/String;I)V
```

Tạo:

```text
JniSignature
```

và parser:

```text
parse_signature(...)
```

Không dùng string tự do trong mọi API.

---

# 19. Signature AST

```text
JniType =
    Void
    Boolean
    Byte
    Char
    Short
    Int
    Long
    Float
    Double
    Object(ClassName)
    Array(JniType)
```

Function:

```text
JniMethodSignature {
    params[]
    return_type
}
```

Sau đó encoder:

```text
JniSignature
    ↓
"(Ljava/lang/String;I)V"
```

---

# 20. Không nhầm JNI type với Axiom type

Ví dụ:

```text
JNI jint
```

có thể map:

```text
Axiom i32
```

nhưng đây là **ABI representation**, không phải semantic alias.

Do đó:

```text
type jint = i32
```

không nên làm Core identity.

Platform library có thể expose:

```text
type JInt = i32
```

nếu representation đã được xác định.

---

# 21. Java String

Không map:

```text
jstring → Text
```

một cách implicit.

Java `String` và Axiom `Text` có memory/encoding/lifetime khác nhau.

API:

```text
JavaString
```

và explicit conversion:

```text
to_text()
from_text()
```

---

# 22. UTF-16 boundary

Java String là UTF-16 based abstraction.

Axiom Text có thể dùng representation riêng.

Do đó:

```text
JavaString
    ↓
UTF conversion
    ↓
Axiom Text
```

Conversion có thể allocate/copy.

Không hứa zero-copy nếu semantics không cho phép.

---

# 23. UTF-8 JNI API

JNI có API kiểu UTF-8 nhưng semantics của modified UTF-8 cần được xử lý rõ.

Do đó không tạo:

```text
String.as_utf8_bytes()
```

ngầm.

Tạo:

```text
JniModifiedUtf8
```

nếu cần raw JNI API.

---

# 24. Arrays

Tách:

```text
JavaArray<T>
PrimitiveArray<T>
ObjectArray<T>
```

Ví dụ:

```text
JIntArray
JByteArray
JObjectArray
```

và operations:

```text
length
get
set
elements
release
```

---

# 25. Array access

Nếu JNI cung cấp pointer tới array elements:

```text
GetIntArrayElements
```

Axiom wrapper phải coi pointer đó là:

```text
mut_view<i32>
```

**chỉ trong capability scope hợp lệ**.

Ví dụ conceptual:

```axiom
with_elements(array) |view| {
    ...
}
```

Không trả raw `*mut i32` vào safe code.

---

# 26. Critical array sections

JNI có các API critical access.

Đây phải là:

```text
unsafe / restricted foreign capability
```

vì VM/runtime có thể có những hạn chế về việc code làm gì trong critical section.

Không expose như:

```text
normal mut_view
```

---

# 27. Exception model

Đây là điểm rất quan trọng.

JNI có trạng thái exception pending.

Ví dụ:

```text
CallObjectMethod
    ↓
Java throws
    ↓
JNI exception pending
```

Trong khi Axiom có:

```text
Result
panic
```

Không được để Java exception tự động trở thành Axiom panic.

---

# 28. JNI exception state

Tạo:

```text
JniExceptionState =
    Clear
    Pending
```

Sau foreign call:

```text
call
 ↓
check_exception
 ↓
Result
```

Wrapper high-level:

```axiom
fn call(...) -> Result<T, JavaException>
```

---

# 29. Không dùng C++-style exception crossing

JNI boundary:

```text
Java exception
       ↓
JniError
       ↓
Result
```

Axiom:

```text
panic
       X
       │
       └──> Java exception
```

không implicit.

---

# 30. Java exception wrapper

```text
JavaException {
    throwable: GlobalRef<JThrowable>
}
```

hoặc local tùy API.

Có:

```text
fn exception_occurred(...)
fn exception_clear(...)
fn throw(...)
fn throw_new(...)
```

Raw operations `unsafe`.

High-level wrapper có thể chuyển thành `Result`.

---

# 31. Native → Java throw

Ví dụ:

```axiom
fn foo(env: JNIEnv) -> Result<i32, JavaException>
```

Nếu lỗi:

```text
throw Java exception
return JNI default
```

JNI semantics yêu cầu native method không tiếp tục sử dụng API như bình thường khi exception pending.

Wrapper phải enforce bằng state machine/capability càng nhiều càng tốt.

---

# 32. Native method return

JNI method có ABI return type:

```text
void
jboolean
jint
jlong
jobject
...
```

Axiom source có thể:

```axiom
fn native_add(a: i32, b: i32) -> i32
```

Platform binding generates ABI adapter:

```text
Java
 ↓
JNI entry
 ↓
Axiom adapter
 ↓
Axiom function
```

---

# 33. Adapter là điểm rất quan trọng

Không export trực tiếp application function nếu signature không đúng JNI ABI.

```text
Axiom function
        ↓
JNI Adapter
        ↓
JNI symbol
```

Adapter chịu trách nhiệm:

- lấy `JNIEnv`;
- nhận `jobject`;
- decode JNI arguments;
- chuyển sang Axiom types;
- xử lý Result/error;
- encode return;
- exception conversion.

---

# 34. Generated adapter

Ví dụ semantic:

```axiom
fn add(a: i32, b: i32) -> Result<i32, JavaException>
```

Tooling có thể sinh adapter.

Không cần programmer viết:

```text
Java_com_xxx_xxx(...)
```

bằng tay.

---

# 35. Native registration

Ưu tiên:

```text
JNI_OnLoad
    ↓
RegisterNatives
    ↓
method table
```

Android documentation cũng dùng mô hình `JNI_OnLoad` + `JNINativeMethod` để đăng ký native methods. citeturn0search2turn0search5

Axiom nên chọn đây làm **primary mechanism**.

---

# 36. Không dựa vào symbol name mangling

Có thể vẫn hỗ trợ JNI exported-name convention cho compatibility:

```text
Java_com_example_Foo_bar
```

nhưng không dùng làm cơ chế nội bộ chính.

Primary:

```text
JNI_OnLoad
→ RegisterNatives
```

Ưu điểm:

- không phụ thuộc tên symbol dài;
- kiểm soát mapping tập trung;
- adapter generation dễ;
- rename Java method không cần phụ thuộc linker symbol name.

---

# 37. `JNI_OnLoad`

Axiom library có thể sinh:

```text
@export("JNI_OnLoad")
extern "C"
fn JNI_OnLoad(...)
```

nhưng function implementation được compiler/runtime support generate.

Conceptual:

```text
JNI_OnLoad
    ↓
get JNIEnv
    ↓
register generated native methods
    ↓
return JNI_VERSION_1_6
```

JNI version phải là platform metadata.

---

# 38. Registration table

Axiom internal:

```text
NativeMethod {
    class_name
    method_name
    signature
    function
}
```

Lower:

```text
JNINativeMethod {
    name
    signature
    fn_ptr
}
```

`fn_ptr` là foreign ABI function pointer.

---

# 39. Closure không được dùng trực tiếp

Không:

```axiom
register(method, |x| ...)
```

nếu closure capture state.

JNI callback cần:

```text
function pointer + context
```

giống FFI rule đã freeze.

Nếu cần state:

```text
GlobalRef
Handle
userdata
```

và adapter.

---

# 40. Java callback

Native → Java:

```text
Axiom thread
 ↓
JNIEnv
 ↓
JavaVM
 ↓
Java method
```

Nếu callback xảy ra trên worker thread:

```text
thread
 ↓
attach
 ↓
JNIEnv
 ↓
call Java
 ↓
detach
```

Android application process/thread model vẫn do platform quản lý; native worker threads có lifecycle riêng. citeturn0search14

---

# 41. Thread safety

Không đánh dấu:

```text
JavaObject: Share
```

mặc định.

Một Java object reference có thể được giữ qua threads bằng cơ chế JNI reference, nhưng **Java API cụ thể** có thể có thread-safety rules riêng.

Axiom wrapper nên conservative:

```text
GlobalRef<T>
    Send = platform-contract dependent
    Share = platform-contract dependent
```

Không tự suy ra từ bit representation.

---

# 42. UI đặc biệt

Axiom không được giả định:

```text
JavaObject
```

có thể gọi từ bất kỳ thread nào.

Android UI toolkit có main-thread constraints; Android documentation cũng nêu UI toolkit không thread-safe và việc cập nhật UI phải trên UI thread. citeturn0search14

Đây là **library/platform contract**, không phải ownership rule của Core.

---

# 43. JNI capability

Mô hình:

```text
JNIEnv
 └── capability: CurrentJNIThread
```

Các object reference:

```text
LocalRef
 └── provenance: JNILocalFrame

GlobalRef
 └── provenance: JVM

WeakGlobalRef
 └── provenance: JVMWeak
```

Compiler có thể dùng provenance này để ngăn một số lỗi rõ ràng.

---

# 44. Không cố biến JNI thành memory-safe tuyệt đối

Điều này quan trọng.

Axiom wrapper có thể ngăn:

```text
dangling local ref
invalid Axiom view
use after wrapper drop
```

nhưng không thể chứng minh toàn bộ:

```text
Java object invariants
Java API thread safety
VM behavior
reflection semantics
```

Do đó:

```text
JNI raw = unsafe
JNI safe wrapper = contract-based abstraction
```

---

# 45. JNI raw layer

Repository:

```text
std/android/jni/raw/
├── types.ax
├── vm.ax
├── env.ax
├── object.ax
├── method.ax
├── field.ax
├── array.ax
├── string.ax
└── constants.ax
```

Raw layer gần C ABI nhất.

---

# 46. JNI safe layer

```text
std/android/jni/
├── reference.ax
├── environment.ax
├── class.ax
├── method.ax
├── field.ax
├── string.ax
├── array.ax
├── exception.ax
└── registration.ax
```

Safe layer không được tự ý sử dụng raw pointer ngoài unsafe boundary.

---

# 47. Generated bindings

Sau này:

```text
tools/android/jnigen/
├── java_parser.ax
├── signature.ax
├── generator.ax
└── tests/
```

Input:

```text
Java/Kotlin API metadata
```

Output:

```text
Axiom binding
JNI adapters
registration table
```

Không cần runtime reflection.

---

# 48. Đây là điểm rất phù hợp với Axiom

Axiom có:

```text
comptime
reflection
```

nhưng không cần runtime reflection.

JNI binding generator có thể chạy:

```text
comptime/tooling
```

và sinh binding tĩnh.

Kết quả runtime:

```text
zero reflection overhead
```

nếu API được bind statically.

---

# 49. Error taxonomy

Thêm:

```text
AX_JNI_0001
JNI environment unavailable

AX_JNI_0002
JNI reference escaped its valid frame

AX_JNI_0003
JNI global reference required

AX_JNI_0004
JNI exception pending

AX_JNI_0005
JNI signature invalid

AX_JNI_0006
JNI method registration mismatch

AX_JNI_0007
JNI thread is not attached

AX_JNI_0008
JNI reference type mismatch

AX_JNI_0009
JNI array access lifetime violation

AX_JNI_0010
JNI foreign callback violates thread contract
```

---

# 50. Acceptance test 1 — native function

Java:

```text
Native.add(20, 22)
```

Axiom:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Pipeline:

```text
Java
 ↓
JNI
 ↓
generated adapter
 ↓
Axiom add
 ↓
42
```

---

# 51. Acceptance test 2 — registration

```text
JNI_OnLoad
 ↓
RegisterNatives
 ↓
Native.add
```

Không cần JNI mangled symbol:

```text
Java_com_example_...
```

trừ compatibility test.

---

# 52. Acceptance test 3 — String

```text
Java String
 ↓
JString
 ↓
Axiom Text
 ↓
processing
 ↓
JString
```

Phải kiểm tra:

- Unicode;
- surrogate pairs;
- embedded NUL;
- invalid conversion;
- allocation;
- lifetime.

---

# 53. Acceptance test 4 — exception

Java:

```text
throw RuntimeException
```

Axiom:

```text
Result<T, JavaException>
```

Expected:

```text
JNI exception
 ↓
JavaException
 ↓
Result::Err
```

Không biến thành native process panic.

---

# 54. Acceptance test 5 — global reference

```text
LocalRef
 ↓
GlobalRef
 ↓
store in object
 ↓
later callback
 ↓
release
```

Compiler phải không cho local reference escape thay cho global reference.

---

# 55. Acceptance test 6 — thread

```text
Axiom worker
 ↓
attach JVM
 ↓
JNIEnv
 ↓
Java callback
 ↓
detach
```

Không cho `JNIEnv` được lưu vào global shared state.

---

# 56. Acceptance test 7 — Java array

```text
JIntArray
 ↓
with_elements
 ↓
mut_view<i32>
 ↓
modify
 ↓
release
```

View không được sống sau `with_elements`.

Đây là test trực tiếp cho CAP-001 + FFI.

---

# 57. Acceptance test 8 — JNI_OnLoad failure

Nếu:

```text
FindClass
```

thất bại:

```text
JNI_OnLoad
 → JNI_ERR
```

Không:

```text
panic
```

và không để exception state không xác định.

---

# 58. Acceptance test 9 — no external toolchain

```text
Axiom source
 ↓
Axiom compiler
 ↓
libfoo.so
 ↓
APK
 ↓
Android
```

không:

```text
clang
gcc
CMake
Gradle
```

trong native compilation path.

---

# 59. Invariants

```text
AJNI-20
JNI is a platform library, not a Core language primitive.

AJNI-21
JNI handles are foreign VM references, not ordinary memory pointers.

AJNI-22
JNIEnv is associated with the current JNI-capable thread.

AJNI-23
JavaVM identity is distinct from JNIEnv identity.

AJNI-24
Local references have bounded JNI-frame lifetime.

AJNI-25
Global references have explicit VM-managed lifetime.

AJNI-26
Weak global references do not imply ownership.

AJNI-27
Axiom Drop of a JNI wrapper releases a JNI reference, not the Java object itself.

AJNI-28
JNI reference lifetime is distinct from Java object lifetime.

AJNI-29
JNI operations may establish foreign capabilities.

AJNI-30
Foreign JNI capabilities do not automatically become Axiom ownership.

AJNI-31
Raw JNI operations are unsafe.

AJNI-32
Safe JNI wrappers must preserve reference provenance.

AJNI-33
JNI exceptions do not implicitly become Axiom panics.

AJNI-34
Axiom panics do not implicitly become Java exceptions.

AJNI-35
JNI exception state must be explicitly observed or handled.

AJNI-36
JNI signatures have a dedicated semantic representation.

AJNI-37
JNI method IDs are foreign opaque identities.

AJNI-38
JNI adapters mediate between Java ABI and Axiom functions.

AJNI-39
Application functions are not implicitly JNI ABI functions.

AJNI-40
JNI registration is explicit.

AJNI-41
JNI_OnLoad is a platform initialization entry.

AJNI-42
RegisterNatives is the preferred generated registration mechanism.

AJNI-43
JNI name-mangled exports are compatibility mechanisms, not required internal mechanisms.

AJNI-44
JNI callbacks require explicit thread/environment validity.

AJNI-45
JNIEnv must not be treated as globally shareable state.

AJNI-46
Java object thread-safety is a platform/library contract.

AJNI-47
JNI array views cannot outlive their acquisition scope.

AJNI-48
JNI string conversion is explicit.

AJNI-49
JNI foreign memory does not automatically become Axiom memory ownership.

AJNI-50
JNI binding generation can be compile-time/tooling based.

AJNI-51
Generated JNI bindings need not use runtime reflection.

AJNI-52
JNI bindings must not alter Core language semantics.
```

---

# 60. Một quyết định kiến trúc quan trọng

Sau JNI-001, tôi đề xuất **không tiếp tục đào sâu Android Java framework**.

Ta đã chứng minh được:

```text
Axiom Core
   ↓
FFI
   ↓
AArch64 ABI
   ↓
ELF
   ↓
Android
   ↓
JNI
```

Nếu tiếp tục làm:

```text
Activity
View
Looper
Intent
Service
Binder
Camera
Audio
Vulkan
...
```

thì compiler project sẽ bị kéo thành Android SDK clone.

Thay vào đó, các API đó thuộc:

```text
std/android/
```

và có thể phát triển độc lập.

---

# 61. Bước tiếp theo: iOS-MACHO-001

Đây là milestone rất quan trọng tiếp theo:

```text
AArch64
   ↓
Apple ABI
   ↓
Mach-O
   ↓
iOS
```

Nó sẽ kiểm tra một vấn đề mà Android không kiểm tra được:

> **Cùng AArch64 + Mach-O như macOS, nhưng platform execution/deployment model khác rất mạnh.**

Ta sẽ thiết kế:

```text
IOS-MACHO-001
├── iOS target triple
├── Apple AArch64 ABI
├── Mach-O reuse
├── arm64 device target
├── simulator target separation
├── framework/dylib model
├── app bundle
├── Info.plist
├── entitlements
├── code-signing abstraction
├── provisioning boundary
└── IPA packaging
```

Đặc biệt sẽ giữ nguyên nguyên tắc:

```text
macOS Mach-O implementation
          ↑
          │ reuse
          ↓
iOS Mach-O implementation
```

chỉ khác **Apple platform policy**, không fork Mach-O backend.