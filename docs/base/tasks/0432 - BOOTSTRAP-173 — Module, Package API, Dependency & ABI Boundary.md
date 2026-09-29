# BOOTSTRAP-173 — Module, Package API, Dependency & ABI Boundary
**FROZEN / COMPLETED**

Task này cần phân biệt thật rõ 4 khái niệm:

```text
Module
Package
API
ABI
```

Nếu trộn chúng với nhau, compiler incremental, package manager, LTO và binary compatibility sẽ nhanh chóng trở nên phức tạp.

Nguyên tắc của Axiom:

> **Source boundary, semantic boundary, compilation boundary và binary boundary là những thứ khác nhau.**

---

## 173.1. Module

Module là đơn vị tổ chức namespace và semantic declarations.

```ax
package app;

import std::io::File;

fn load() { ... }
```

Module có:

```text
ModuleId
parent
children
declarations
imports
visibility
interface fingerprint
implementation fingerprint
```

Module không nhất thiết tương ứng 1 file.

Một file có thể chứa nhiều module, và một module có thể được tổ chức bởi nhiều source file theo package convention.

---

# 173.2. Package

Package là đơn vị phân phối/version/dependency.

```text
Package
├── modules
├── public API
├── dependencies
├── build configuration
├── metadata
└── artifacts
```

Package có identity:

```text
Name + Version + SourceIdentity
```

đã được đóng băng trong Build System.

---

# 173.3. Workspace

Workspace chỉ là tập hợp package cùng được phát triển/build:

```text
Workspace
├── package A
├── package B
├── package C
└── ...
```

Workspace không tạo một namespace global.

Không có chuyện package này tự động nhìn thấy declaration package kia.

---

# 173.4. Dependency

Dependency là quan hệ:

```text
A → B
```

A sử dụng public interface của B.

Package graph vẫn là DAG.

```text
A
├── B
├── C
│   └── D
└── E
```

Package cycle:

```text
A → B → A
```

bị reject.

Module cycle bên trong một package vẫn có thể được phép.

---

# 173.5. Public API

`pub` xác định source-level visibility.

Ví dụ:

```ax
pub struct User {
    pub id: UserId;
    name: String;
}

pub fn load_user(id: UserId) -> Result<User, Error>
```

Public API gồm semantic information như:

```text
types
fields
traits
functions
generic constraints
associated types
constants
visibility
attributes affecting ABI
```

Không nhất thiết bao gồm implementation.

---

# 173.6. `pub` không đồng nghĩa exported symbol

Đã đóng băng:

```text
pub
    ≠
native export
```

Muốn export binary:

```ax
@export("axiom_load_user")
pub fn load_user(...) { ... }
```

Điều này rất quan trọng.

Một package có thể có hàng nghìn public functions nhưng binary chỉ export một số API.

---

# 173.7. Private implementation

Ví dụ:

```ax
pub fn sort_users(...) {
    quick_sort_impl(...);
}

fn quick_sort_impl(...) {
    ...
}
```

Thay đổi:

```text
quick_sort_impl
```

không nhất thiết invalidate downstream semantic compilation nếu public interface không đổi.

Đây là nền tảng incremental compilation.

---

# 173.8. Interface Fingerprint

Mỗi module/package có:

```text
InterfaceFingerprint
```

được tạo từ semantic public API.

Ví dụ:

```text
pub fn foo(x: i32) -> i64
```

thay đổi thành:

```text
pub fn foo(x: i32) -> i32
```

→ fingerprint thay đổi.

Nhưng:

```text
loop optimization
variable name
private helper
private algorithm
```

không nhất thiết thay đổi interface fingerprint.

---

# 173.9. Implementation Fingerprint

Ngoài interface:

```text
ImplementationFingerprint
```

ghi nhận implementation dependencies.

Nhờ đó compiler biết:

```text
interface unchanged
implementation changed
```

và có thể quyết định có cần:

```text
recompile
re-optimize
re-link
```

hay không.

---

# 173.10. Semantic Metadata `.axmeta`

Package nên phân phối metadata:

```text
package.axmeta
```

chứa:

```text
public declarations
TypeId information
Trait information
generic signatures
ABI contracts
representation contracts
effect summaries
ownership/capability summaries
inline candidates
generic bodies when required
source/debug mapping references
compiler semantic version
target information
```

Không phải toàn bộ source code.

---

# 173.11. Vì sao `.axmeta` quan trọng?

Package A có thể compile:

```text
A → B.axmeta
```

mà không cần parse toàn bộ implementation của B.

Compiler biết:

```text
B::foo
type
traits
ABI
effects
generic constraints
```

đủ để resolve/type-check A.

Điều này giúp build lớn nhanh hơn.

---

# 173.12. Generic API

Có một ngoại lệ quan trọng.

Nếu:

```ax
pub fn max<T: Ord>(a: T, b: T) -> T
```

được public và compiler cần specialize implementation:

```text
interface
+
generic semantic body
```

có thể cần được phát hành trong metadata hoặc một artifact tương đương.

Do đó `.axmeta` có thể có:

```text
API metadata
Generic semantic metadata
Optimization metadata
```

với mức visibility khác nhau.

---

# 173.13. Generic body privacy

Không phải mọi private implementation đều phải expose.

Ví dụ:

```ax
pub fn public_api<T>(x: T) -> T {
    private_impl(x)
}
```

compiler chỉ expose semantic generic body nếu specialization downstream thực sự yêu cầu.

Nếu package đã cung cấp compiled specialization:

```text
Axiom may reuse it
```

thay vì yêu cầu source.

---

# 173.14. Monomorphization boundary

Generic function có thể được specialize:

```text
Package A
    ↓
B::sort<i32>
```

Compiler có thể:

```text
reuse existing specialization
```

hoặc:

```text
generate new specialization
```

tùy metadata/artifact/cache.

Generic instance identity đã được canonicalize bởi:

```text
GenericInstanceId
```

---

# 173.15. Zero-cost abstraction xuyên package

Package boundary **không tự động trở thành optimization wall**.

Nếu function:

```ax
pub fn add(a: i32, b: i32) -> i32
```

được dùng trong hot loop, compiler có thể inline nếu:

```text
legality ✓
visibility/metadata ✓
profitability ✓
```

Có thể:

```text
package A
→
package B
→
inline
→
constant fold
→
vectorize
```

---

# 173.16. Binary ABI boundary

Ngược lại, nếu package được dùng như stable dynamic library:

```text
Application
     ↓
libfoo.axso
```

thì ABI boundary có thể ngăn:

```text
inlining
layout changes
generic specialization
```

nếu không có compatibility contract.

Do đó:

> **Package boundary không phải ABI boundary.**

---

# 173.17. Static library

Static library:

```text
.axlib
```

có thể được link demand-driven.

Compiler/linker có thể loại bỏ:

```text
unused functions
unused generic instances
unused sections
```

như đã định nghĩa trong linker architecture.

---

# 173.18. Shared library

Shared library:

```text
.axso
```

hoặc target-native equivalent:

```text
.dll
.so
.dylib
```

có ABI contract.

Dynamic loading làm closed-world assumptions yếu đi.

Compiler phải bảo thủ hơn với:

```text
DCE
devirtualization
symbol reachability
ABI
```

---

# 173.19. Stable ABI

Axiom không nên tuyên bố:

> mọi Axiom binary đều ABI-compatible với mọi compiler version.

Thay vào đó có:

```text
Axiom ABI
Stable Axiom ABI
C ABI
System ABI
Platform ABI
```

Stable ABI chỉ áp dụng khi programmer/package explicit chọn.

---

# 173.20. Default ABI

Default Axiom ABI có thể được compiler tối ưu tự do giữa các compatible compilation units.

Không hứa:

```text
struct layout
register assignment
calling convention
symbol naming
```

ổn định qua compiler versions nếu không có stable ABI contract.

---

# 173.21. ABI contract

Khi package cần binary compatibility:

```text
@abi(stable)
```

hoặc package-level configuration tương đương.

Khi đó các thứ observable phải được khóa:

```text
calling convention
layout
alignment
field offsets
enum representation
symbol ABI
ownership transfer
error ABI
```

---

# 173.22. Stable ABI không khóa implementation

Một function:

```ax
@abi(stable)
pub fn hash(x: HashInput) -> Hash
```

có thể thay implementation:

```text
algorithm A
→
algorithm B
```

miễn ABI/semantic contract vẫn tương thích.

Nhưng nếu thay đổi observable behavior, đó là semantic/API change.

---

# 173.23. Semantic compatibility vs ABI compatibility

Có hai câu hỏi riêng:

```text
Semantic compatibility:
    chương trình vẫn có cùng meaning?

ABI compatibility:
    binary cũ và mới có thể giao tiếp?
```

Có thể:

```text
semantic compatible
nhưng ABI incompatible
```

hoặc ngược lại ở mức thấp.

Axiom không gộp hai khái niệm.

---

# 173.24. API versioning

Package version:

```text
1.2.3
```

dùng semantic versioning theo package policy.

Nhưng compiler cũng có:

```text
semantic compiler version
```

và ABI version.

Do đó build identity có thể chứa:

```text
package version
compiler semantic version
ABI version
target
profile
features
```

---

# 173.25. Breaking API change

Ví dụ:

```ax
pub fn foo(x: i32) -> i32
```

đổi thành:

```ax
pub fn foo(x: i64) -> i32
```

là API semantic change.

Downstream cần re-resolve/re-typecheck.

Compiler không cố "tự conversion" để giữ compatibility.

---

# 173.26. Additive API change

Thêm:

```ax
pub fn bar(...)
```

thường không invalidate code đang sử dụng API cũ về mặt semantics.

Nhưng `.axmeta` fingerprint vẫn thay đổi vì public surface thay đổi.

Compiler có thể xử lý dependency rất tinh hơn:

```text
API additions
→
có thể không invalidate consumers
```

nếu declaration resolution graph chứng minh không liên quan.

---

# 173.27. Fine-grained dependency tracking

Không chỉ:

```text
Package B changed
```

mà:

```text
B::Foo changed
```

CompilerDB có thể theo dõi:

```text
A::main
depends on B::foo
```

thay vì invalidate toàn bộ A.

Đây là mục tiêu quan trọng của incremental compiler.

---

# 173.28. Re-export

```ax
pub use other::Type;
```

không tạo declaration mới.

Nó chỉ tạo public binding tới declaration hiện có.

Do đó type identity vẫn:

```text
TypeId = original TypeId
```

không phát sinh wrapper.

---

# 173.29. Facade package

Có thể xây:

```text
app
 ↓
facade
 ├── parser
 ├── compiler
 └── backend
```

Facade re-export API ổn định.

Implementation packages có thể thay đổi mà application chỉ phụ thuộc facade.

---

# 173.30. Import không phụ thuộc filesystem magic

Import:

```ax
import compiler::mir::Function;
```

được resolve thông qua ModuleDB.

Không nên suy luận:

```text
module name == exact file path
```

bắt buộc.

Filesystem layout là package/build concern.

---

# 173.31. Conditional compilation

Axiom hỗ trợ:

```text
@cfg(target_os = "windows")
@cfg(target_arch = "x86_64")
@cfg(feature = "gpu")
```

Nhưng `@cfg` xảy ra trước semantic analysis của branch không được chọn.

Điều này tránh compiler phải type-check code không thuộc target.

---

# 173.32. Feature flags

Feature:

```text
feature = "gpu"
```

là build configuration.

Không nên biến feature flag thành runtime global variable.

Compiler biết feature tại compile time.

Unused feature code có thể không được compile/link.

---

# 173.33. Platform-specific APIs

Package có thể expose:

```text
std::os::windows
std::os::linux
std::os::android
std::os::ios
```

với conditional modules.

Core API không cần chứa mọi platform detail.

---

# 173.34. Prelude

Prelude là implicit import rất nhỏ.

Không để prelude trở thành:

```text
global namespace magic
```

Mục tiêu:

```text
basic Option
Result
Iterator
common traits
primitive utilities
```

Các API lớn phải import explicit.

---

# 173.35. Import order

Import order không được ảnh hưởng semantics.

```ax
import A;
import B;
```

và:

```ax
import B;
import A;
```

phải tương đương nếu không có explicit conflict.

---

# 173.36. Import ambiguity

Nếu:

```text
A::foo
B::foo
```

cùng import vào namespace:

```text
foo()
```

ambiguous.

Compiler báo lỗi.

Không chọn theo:

```text
import order
file order
package version
```

một cách ngầm.

---

# 173.37. Dependency feature resolution

Dependency graph phải resolve configuration trước khi codegen.

Ví dụ:

```text
A
 └── B [gpu]
```

có thể khiến B compile GPU-related modules.

Nhưng nếu A không sử dụng GPU API, linker vẫn có thể loại bỏ runtime GPU components.

---

# 173.38. Dependency isolation

Package không được tự ý truy cập:

```text
private declaration
private source file
private module
```

của dependency.

Ngay cả khi compiler có source code đầy đủ.

Đây là semantic boundary.

---

# 173.39. Source distribution vs binary distribution

Package có thể phân phối:

```text
Source package
Binary package
Mixed package
```

Binary package cần metadata:

```text
.axmeta
ABI
target
features
dependencies
compiler compatibility
```

để compiler/linker hiểu artifact.

---

# 173.40. Binary compatibility matrix

Một binary artifact có identity:

```text
Package
Compiler semantic version
Target
Architecture
ABI
CPU requirements
Profile
Features
```

Compiler không được sử dụng binary incompatible artifact chỉ vì:

```text
same package name
```

---

# 173.41. Cross compilation

Package metadata không được chứa assumption:

```text
host == target
```

Ví dụ:

```text
build host = Windows x86-64
target = Linux ARM64
```

build system phải resolve target dependencies riêng.

---

# 173.42. Build dependencies

Phân biệt:

```text
normal dependency
build dependency
test dependency
bench dependency
system dependency
```

Build tool không tự trở thành runtime dependency.

---

# 173.43. Package cycles

Package:

```text
A → B
B → A
```

bị reject.

Nếu cần shared abstraction:

```text
A
↑
Core
↓
B
```

hoặc restructure module.

Điều này giữ package graph đơn giản và cacheable.

---

# 173.44. Module cycles

Trong cùng package:

```text
module A → B
module B → A
```

có thể được phép vì declaration collection diễn ra trước body resolution.

Resolver dùng stable DeclarationIds thay vì compile tuần tự file-by-file.

---

# 173.45. API stability

Package author có thể đánh dấu:

```text
stable API
experimental API
deprecated API
internal API
```

Core v0.1 chỉ cần semantic visibility đơn giản.

Các metadata này chủ yếu phục vụ tooling/documentation/versioning.

---

# 173.46. Deprecation

Deprecated declaration vẫn resolve được trong compatibility period nhưng compiler có diagnostic:

```text
W_DEPRECATED
```

Không tự động rewrite API.

Tooling có thể cung cấp machine-readable replacement.

---

# 173.47. API evolution

Axiom ưu tiên:

```text
additive evolution
```

thay vì inheritance-heavy compatibility.

Ví dụ trait có thể thêm behavior theo version policy, nhưng breaking trait changes phải được compiler xác định rõ.

---

# 173.48. Trait API boundary

Public trait là một phần interface fingerprint.

Thay đổi:

```text
associated type
required method
where constraint
method signature
```

có thể làm downstream generic code phải recompile.

Implementation private của trait impl không nhất thiết làm như vậy nếu ABI/API không bị ảnh hưởng.

---

# 173.49. Generic ABI boundary

Không export generic chưa specialize qua C ABI.

Ví dụ:

```ax
@export("foo")
pub fn foo<T>(x: T) { ... }
```

không hợp lệ như một C symbol duy nhất.

Phải có concrete specialization hoặc ABI-erased explicit interface.

---

# 173.50. ABI-erased interface

Nếu cần dynamic plugin:

```text
Plugin
 ↓
Stable ABI
 ↓
opaque handle
 ↓
explicit function table
```

có thể dùng.

Không cần ép Axiom object model vào plugin ABI.

---

# 173.51. Package + LTO

Có ba mức:

```text
No LTO
Thin LTO
Full LTO
```

No LTO:

```text
package ABI boundary
```

Thin LTO:

```text
cross-package summaries
```

Full LTO:

```text
whole-program semantic optimization
```

nhưng stable dynamic ABI vẫn là boundary.

---

# 173.52. Metadata trust

`.axmeta` chứa compiler facts nhưng không được coi là "source of truth" cao hơn semantic verifier.

Hierarchy:

```text
source semantics
>
verified compiler facts
>
optimization metadata
>
profile
```

Metadata không thể tự cấp quyền:

```text
unsafe
NoAlias
Send
Share
FfiSafe
```

nếu không có semantic basis.

---

# 173.53. Stale metadata

Nếu:

```text
source
≠
.axmeta identity
```

compiler không sử dụng metadata như authoritative.

Build identity/hash phải phát hiện mismatch.

Không có "maybe vẫn dùng được".

---

# 173.54. Package cache

Package artifacts có thể cache theo:

```text
source hash
dependency fingerprint
compiler semantic version
target
ABI
features
profile
comptime inputs
```

Như Build System đã định nghĩa.

---

# 173.55. AI/compiler interface

AI có thể query:

```text
axc inspect package
axc inspect api
axc inspect abi
axc inspect dependencies
axc inspect exports
axc inspect generic
axc inspect invalidation
```

Ví dụ:

```text
"Why did package A recompile?"
```

compiler có thể trả:

```text
A::foo depends on B::Type
B::Type interface fingerprint changed
therefore:
    HIR invalidated
    MIR invalidated
    codegen invalidated
```

Đây là một lợi thế rất lớn cho AI-assisted development.

---

# 173.56. Compiler boundary

Architecture:

```text
                  Package
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
      Interface             Implementation
          │                     │
       .axmeta                source
          │                     │
          └──────────┬──────────┘
                     ↓
                CompilerDB
                     │
              semantic analysis
                     │
                Verified MIR
                     │
              package artifact
```

---

# 173.57. Nguyên tắc quan trọng nhất

Axiom không nên chọn:

> "Package boundary = compilation boundary."

Thay vào đó:

```text
Package boundary
    = distribution/version boundary

Module boundary
    = namespace/semantic boundary

Interface boundary
    = dependency invalidation boundary

ABI boundary
    = binary compatibility boundary

LTO boundary
    = optimization visibility boundary
```

Bốn boundary này có thể trùng nhau trong một số trường hợp, nhưng **không được định nghĩa là cùng một thứ**.

---

# 173.58. Invariants đóng băng

### Module

- **AMOD-20** — Module là semantic namespace unit.
- **AMOD-21** — Module identity độc lập filesystem path.
- **AMOD-22** — Declaration resolution dùng stable IDs.
- **AMOD-23** — Declaration collection precedes body resolution.
- **AMOD-24** — Module cycles có thể tồn tại trong một package.
- **AMOD-25** — Import order không thay đổi semantics.
- **AMOD-26** — Ambiguous imports phải diagnostic deterministic.
- **AMOD-27** — Private declarations không được dependency truy cập.

### Package

- **APKG-20** — Package là unit của distribution/version/dependency.
- **APKG-21** — Package identity = Name + Version + SourceIdentity.
- **APKG-22** — Package dependency graph phải acyclic.
- **APKG-23** — Package không tạo global namespace.
- **APKG-24** — Dependency visibility chỉ thông qua public API.
- **APKG-25** — Binary package phải cung cấp đủ metadata để semantic resolution.
- **APKG-26** — Package cache identity bao gồm semantic dependencies.
- **APKG-27** — Host/target dependency resolution độc lập.

### API

- **AAPI-20** — `pub` là source visibility, không phải native symbol export.
- **AAPI-21** — `@export` là binary export contract.
- **AAPI-22** — Public interface có semantic fingerprint.
- **AAPI-23** — Implementation change không mặc định invalidate unrelated consumers.
- **AAPI-24** — Fine-grained dependency tracking được ưu tiên.
- **AAPI-25** — Re-export không tạo declaration/type identity mới.
- **AAPI-26** — Generic public APIs có thể cần semantic generic metadata.
- **AAPI-27** — Deprecated APIs có diagnostic riêng.
- **AAPI-28** — API evolution không dựa trên class inheritance.

### ABI

- **AABI-80** — Package boundary không mặc định là ABI boundary.
- **AABI-81** — Default Axiom ABI không đảm bảo cross-version binary stability.
- **AABI-82** — Stable ABI phải explicit.
- **AABI-83** — Stable ABI khóa mọi representation/ownership/calling behavior observable tại boundary.
- **AABI-84** — Semantic compatibility và ABI compatibility là hai khái niệm độc lập.
- **AABI-85** — Generic C ABI export phải specialize hoặc ABI-erase.
- **AABI-86** — FFI ABI ownership phải explicit.

### Optimization

- **APKGOPT-20** — Package boundaries không ngăn zero-cost optimization nếu metadata cho phép.
- **APKGOPT-21** — Cross-package inlining phụ thuộc legality/profitability.
- **APKGOPT-22** — LTO có thể vượt compilation boundaries nhưng không vượt stable ABI semantics.
- **APKGOPT-23** — Closed-world optimization không áp dụng tùy tiện cho dynamic libraries/plugins.
- **APKGOPT-24** — `.axmeta` optimization facts không được override semantic verification.
- **APKGOPT-25** — Stale metadata không được coi authoritative.

### Incremental

- **AINTERFACE-20** — Interface fingerprint và implementation fingerprint là distinct.
- **AINTERFACE-21** — Public API change có thể invalidate dependent semantic queries.
- **AINTERFACE-22** — Implementation-only change không mặc định invalidate consumers.
- **AINTERFACE-23** — Invalidation phải deterministic.
- **AINTERFACE-24** — Cache identity phải bao gồm compiler semantic version khi semantics phụ thuộc compiler.
- **AINTERFACE-25** — Conditional compilation được resolve theo target/config trước codegen.

---

# BOOTSTRAP-173 hoàn tất

Kiến trúc package của Axiom giờ có một điểm rất quan trọng:

```text
                 SOURCE
                   │
              ┌────┴────┐
              │  Module │
              └────┬────┘
                   │
              Public API
                   │
              .axmeta
                   │
             Package boundary
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
      Static      LTO      Stable ABI
      link                  boundary
        │          │          │
        └──────────┴──────────┘
                   ↓
              Final binary
```

Nhờ vậy Axiom vừa có thể **compile incremental rất nhanh**, vừa có thể **LTO xuyên package**, vừa có **ABI ổn định khi thực sự cần**, thay vì ép tất cả package vào một mô hình compilation cứng nhắc.

---

# BOOTSTRAP-174 — Reflection, Metadata, Compile-Time Introspection & Runtime Type Information

Task tiếp theo cần khóa phần mà Axiom đặc biệt quan tâm vì **AI tooling, serialization, GUI, editor, debugger, FFI và framework generation** đều sẽ cần nó:

```text
reflection
Type
fields
methods
traits
attributes
layout metadata
ABI metadata
generic metadata
source metadata
runtime RTTI
serialization generation
GUI binding
FFI binding
comptime introspection
```

Câu hỏi trung tâm:

> **Axiom có thể cung cấp reflection mạnh đến đâu mà không biến mọi binary thành một "runtime metadata blob", không tạo hidden runtime và vẫn giữ được khả năng strip toàn bộ metadata khi chương trình không cần?**