# BOOTSTRAP-336 — AXIOM LINK-TIME SECTION GRAPH, RELOCATION OPTIMIZATION & FINAL BINARY LAYOUT ENGINE

Sau 335, Axiom đã biết **cái gì cần giữ và cái gì có thể loại bỏ**. Bước tiếp theo là tối ưu **cách những phần còn lại được đặt trong binary**.

Mục tiêu:

> **Binary không chỉ nhỏ về số byte; nó phải có layout tối ưu cho startup, instruction cache, page locality, relocation cost, loading time và memory footprint.**

Đây là tầng nằm giữa:

```text
Whole-Program Optimization
        ↓
Section Graph
        ↓
Final Binary Layout
        ↓
Relocation Optimization
        ↓
Object/Executable Writer
```

---

# 1. Phân biệt 3 loại kích thước

Axiom phải phân biệt:

```text
FileSize
MappedSize
WorkingSet
```

Ví dụ:

```text
Binary:
  file size       = 2.1 MB
  mapped pages    = 2.4 MB
  startup working = 180 KB
```

Không thể đánh giá binary chỉ bằng file size.

---

# 2. Layout Objective

Tùy build profile:

```text
MinFileSize
MinMappedSize
FastStartup
LowMemory
MaxThroughput
Balanced
```

Compiler tối ưu layout theo objective.

---

# 3. Section Graph

Thay vì chỉ:

```text
.text
.rodata
.data
.bss
```

Axiom tạo graph:

```text
.text.main
.text.foo
.text.bar
.rodata.strings
.rodata.tables
.data.config
.data.mutable
.bss
.metadata
```

và các edge:

```text
Code → Code
Code → ReadOnlyData
Code → MutableData
Data → Data
```

---

# 4. Hot/Cold Classification

Mỗi entity có:

```text
Hot
Warm
Cold
NeverExecuted
Unknown
```

Nguồn thông tin:

- static analysis
- PGO
- startup profile
- branch probabilities
- explicit attributes

---

# 5. Startup Set

Compiler xác định:

```text
StartupReachability
```

Ví dụ:

```text
entry
 ↓
runtime_init
 ↓
main
 ↓
config
```

Các function không cần lúc startup có thể đặt xa.

---

# 6. Startup Layout

Ví dụ:

```text
[entry]
[essential runtime]
[main]
[startup functions]
[hot functions]
[cold functions]
```

Giúp giảm page faults.

---

# 7. Hot Code Clustering

Nếu PGO cho biết:

```text
A → B → C
```

thường xuyên xảy ra:

```text
A B C
```

nên đặt gần nhau.

Mục tiêu:

```text
instruction cache locality
I-TLB locality
branch target locality
```

---

# 8. Cold Code Splitting

Function hiếm khi chạy:

```text
error_handler()
debug_path()
rare_parser()
```

có thể đưa vào cold section.

Ví dụ:

```text
.text.hot
.text
.text.cold
```

---

# 9. Error Path Isolation

Một chương trình có:

```text
normal path = 99.9%
error path = 0.1%
```

Không nên để error path chiếm cache/page cùng hot path nếu target cho phép tách.

---

# 10. Function Ordering

Axiom có:

```text
FunctionOrderGraph
```

Edge:

```text
caller → callee
```

trọng số:

```text
execution_frequency
```

Sau đó giải bài toán ordering.

Không cần tối ưu tuyệt đối NP-hard; heuristic đủ tốt.

---

# 11. PGO Integration

PGO cung cấp:

```text
call_count
branch_count
block_frequency
startup_frequency
```

Layout optimizer dùng trực tiếp.

Nếu không có PGO:

```text
static heuristic
```

được dùng.

---

# 12. Function Alignment

Không phải function nào cũng cần alignment lớn.

Ví dụ:

```text
hot_function → target-preferred alignment
cold_function → minimal alignment
```

Giảm padding.

---

# 13. Alignment Budget

Compiler có thể áp dụng:

```text
AlignmentBudget
```

để tránh:

```text
function size = 30 bytes
alignment padding = 28 bytes
```

trong binary nhỏ.

---

# 14. Data Layout

Tương tự code:

```text
hot_readonly
cold_readonly
hot_mutable
cold_mutable
startup_data
```

---

# 15. Read-only Data Sharing

335 đã xác định data folding.

336 quyết định **đặt chúng ở đâu**.

Ví dụ:

```text
.rodata.hot
.rodata
.rodata.cold
```

---

# 16. String Layout

Strings có thể được:

```text
clustered
deduplicated
sorted
compressed
```

nhưng chỉ khi ABI/runtime semantics cho phép.

Không tự động compress literal nếu runtime cần zero-copy raw access.

---

# 17. Pointer Relocation

Relocation là một nguồn chi phí.

Ví dụ:

```text
global pointer → global object
```

có thể tạo relocation.

Axiom nên cố giảm:

```text
absolute relocations
runtime relocations
```

---

# 18. Relative Addressing

Nếu target hỗ trợ:

```text
PC-relative
relative data reference
relative call
```

ưu tiên dùng chúng.

Lợi ích:

- smaller encoding
- fewer relocations
- position-independent code
- loader efficiency

---

# 19. Relocation Classes

Model:

```text
StaticAbsolute
StaticRelative
PCRelative
GOTRelative
TLS
Import
Export
Runtime
Dynamic
GPU
```

---

# 20. Relocation Cost

Mỗi relocation có:

```text
size
load-time-cost
writable-page-impact
sharing-impact
```

Compiler có thể tối ưu layout để giảm chúng.

---

# 21. Writable Relocation Problem

Một số relocation yêu cầu loader sửa code/data.

Điều này có thể:

```text
break code sharing
increase private memory
increase startup cost
```

Axiom nên ưu tiên relocation model cho phép:

```text
read-only executable pages
```

khi target hỗ trợ.

---

# 22. Position Independent Code

PIC/PIE nên là một policy:

```text
PIC
PIE
Static
PlatformDefault
```

Không phải semantic language rule.

---

# 23. ASLR Compatibility

Layout engine phải hỗ trợ target security requirements như ASLR.

Optimization không được phá:

```text
relocation validity
segment permissions
load address constraints
```

---

# 24. Segment Construction

Sau section layout:

```text
sections
   ↓
segments
```

Ví dụ:

```text
RX:
  .text.hot
  .text
  .text.cold

R:
  .rodata
  metadata

RW:
  .data
  .bss
```

---

# 25. Permission Separation

Không để:

```text
executable + writable
```

trừ khi platform contract bắt buộc.

Compiler phải bảo toàn:

```text
W^X
```

khi target/security profile yêu cầu.

---

# 26. Read-only After Relocation

Một số data ban đầu cần loader relocation nhưng sau đó không đổi.

Nếu OS hỗ trợ:

```text
relocate
→ seal read-only
```

Axiom có thể tận dụng.

---

# 27. BSS Optimization

Zero-initialized data:

```text
static x: [u8; 1_000_000] = zero
```

không cần 1 MB trong file.

Có thể:

```text
.bss = 1 MB
file contribution ≈ 0
```

---

# 28. Zero Page Sharing

Nếu platform hỗ trợ zero pages, compiler/loader có thể tận dụng.

Không cần physically allocate tất cả zero-initialized memory ngay startup.

---

# 29. Segment Ordering

Typical:

```text
headers
RX
R
RW
```

Nhưng tối ưu startup có thể yêu cầu khác.

Layout engine phải dựa trên target ABI.

---

# 30. Page Packing

Mục tiêu:

```text
minimize partially-used pages
```

Ví dụ:

```text
.text.hot = 14 KB
```

có thể ghép các code section liên quan để tránh page waste.

---

# 31. Page Coloring / Cache Awareness

Không phải target nào cũng cần.

Axiom architecture cho phép target backend cung cấp:

```text
CacheLineSize
PageSize
HugePageSize
ITLBEntries
DTLBEntries
```

nhưng optimizer không giả định chúng trong Core semantics.

---

# 32. Huge Page Policy

Server profile có thể yêu cầu:

```text
HugePageFriendly
```

Embedded profile có thể không.

---

# 33. Binary Padding

Padding phải được xem như cost:

```text
alignment padding
segment padding
page padding
```

Binary size optimizer phải đo.

---

# 34. Symbol Table Stripping

Release binary có thể loại:

```text
internal symbols
local names
debug symbols
```

nhưng giữ:

```text
exports
required dynamic symbols
unwind symbols
runtime-required symbols
```

---

# 35. Symbol Visibility

Mỗi symbol:

```text
Local
Hidden
Protected
Exported
Weak
Dynamic
```

Visibility càng hạn chế:

```text
→ càng nhiều optimization freedom
```

---

# 36. Export Minimization

Không nên biến mọi `pub fn` thành binary export.

Chỉ:

```text
@export
stable ABI
FFI
component service
```

mới tạo external binary symbol.

Điều này nối trực tiếp với 335.

---

# 37. Import Minimization

Nếu một imported function chỉ được dùng trong unreachable code:

```text
import
```

cũng phải bị loại.

---

# 38. Dynamic Dependency Minimization

Whole-program build nên biết:

```text
libA required
libB unused
```

Nếu link profile cho phép:

```text
libB
```

không xuất hiện trong final dependency set.

---

# 39. Startup Dependency Graph

OS loader có thể phải load:

```text
A → B → C
```

Axiom nên tối thiểu hóa dynamic dependency chain nếu profile yêu cầu startup speed.

---

# 40. Static vs Dynamic Policy

Build profile:

```text
StaticPreferred
DynamicPreferred
Hybrid
PlatformDefault
```

Compiler không tự thay đổi ABI contract.

---

# 41. Import Thunk Elimination

Nếu target tạo thunk:

```text
caller
 → thunk
 → function
```

và compiler có đủ visibility:

```text
caller
 → function
```

có thể loại thunk.

---

# 42. PLT/GOT Optimization

Trên target hỗ trợ:

```text
local call
```

có thể tránh indirect dynamic dispatch qua PLT/GOT nếu symbol visibility cho phép.

---

# 43. TLS Layout

TLS objects:

```text
thread_local
```

có layout riêng.

Compiler phải tính:

```text
TLS size
alignment
access model
relocation
```

---

# 44. TLS Model Selection

Có thể chọn:

```text
LocalExec
InitialExec
LocalDynamic
GeneralDynamic
```

tùy visibility/deployment.

Không expose lựa chọn này thành language semantics.

---

# 45. TLS Optimization

Nếu compiler chứng minh program:

```text
single-thread
```

một số TLS abstraction có thể được tối ưu.

Nhưng không được làm thay đổi behavior nếu thread creation là observable.

---

# 46. Exception / Unwind Sections

Nếu panic profile:

```text
abort
```

không cần full unwind metadata.

Nếu:

```text
unwind
```

phải giữ metadata cần thiết.

---

# 47. Unwind Table DCE

Chỉ function có thể tham gia unwind path mới cần relevant metadata.

Cold/unreachable function metadata có thể loại.

---

# 48. Runtime Metadata

Metadata categories:

```text
Required
Optional
DebugOnly
ToolingOnly
Reflection
DynamicABI
```

Mỗi category có retention policy riêng.

---

# 49. Minimal Runtime

336 phối hợp Runtime Component System:

```text
Program
 ↓
RequiredRuntimeComponents
 ↓
SectionGraph
 ↓
only required runtime sections
```

---

# 50. Binary Layout Verification

Sau layout:

```text
LayoutVerifier
```

kiểm tra:

- section overlap
- alignment
- relocation range
- segment permissions
- symbol addresses
- entry address
- TLS layout
- unwind metadata
- import/export tables
- ABI requirements

---

# 51. Final Address Assignment

Không được xem địa chỉ binary là semantic identity trừ khi contract cho phép.

Compiler có thể thay đổi:

```text
foo @ 0x1000
```

thành:

```text
foo @ 0x1800
```

mà semantics không đổi.

---

# 52. Address Observability

Nếu chương trình lưu:

```text
address_of(foo)
```

hoặc FFI/export yêu cầu stable symbol address semantics:

```text
address becomes observable
```

Layout optimizer phải bảo toàn contract tương ứng.

---

# 53. Deterministic Layout

Reproducible build yêu cầu:

```text
same semantic inputs
→ same layout
```

nếu profile yêu cầu bit-for-bit reproducibility.

Không được để:

```text
worker completion order
```

quyết định section ordering.

---

# 54. Layout Fingerprint

Tạo:

```text
LayoutFingerprint
```

dựa trên:

```text
target
ABI
section set
ordering policy
alignment policy
relocation model
layout algorithm version
```

---

# 55. Incremental Layout

Một function thay đổi không nhất thiết phải rebuild layout toàn bộ semantic graph.

Nhưng nếu kích thước thay đổi làm:

```text
addresses
relocations
page boundaries
```

thay đổi thì binary layout stage phải rerun phù hợp.

---

# 56. Layout Cache

Cache có thể lưu:

```text
previous section placement
```

và reuse nếu:

```text
section fingerprints unchanged
```

Nhưng phải validate lại relocation/range constraints.

---

# 57. Linker Relaxation

Một relocation/call có thể ban đầu dùng encoding lớn:

```text
long jump
```

sau layout phát hiện:

```text
target gần
```

→ đổi thành:

```text
short jump
```

Đây là target-specific relaxation.

---

# 58. Branch Range Optimization

Machine backend có thể lặp:

```text
layout
→ encode
→ detect range
→ relax
→ layout
```

cho đến fixed point.

Phải có giới hạn iteration.

---

# 59. Fixed-Point Requirement

```text
Layout
→ Encoding
→ Relaxation
→ Layout
```

phải hội tụ.

Không được có infinite oscillation.

---

# 60. Final Binary Pipeline

```text
WholeProgramOptimization
        ↓
SectionGraph
        ↓
ReachabilityValidation
        ↓
Function/Data Ordering
        ↓
Alignment
        ↓
Relocation Planning
        ↓
Segment Construction
        ↓
Address Assignment
        ↓
Machine Relaxation
        ↓
Relocation Finalization
        ↓
Binary Verification
        ↓
Executable
```

---

# 61. CompilerDB additions

```text id="5q5z5g"
SectionGraphDB
SectionLayoutDB
SegmentLayoutDB
RelocationDB
AddressAssignmentDB
SymbolVisibilityDB
ImportExportDB
TLSLayoutDB
UnwindLayoutDB
PageLayoutDB
LayoutCacheDB
BinaryLayoutVerificationDB
```

---

# 62. APIs

```text id="5m6l4k"
build_section_graph()

classify_hot_cold()

compute_function_order()

compute_data_order()

compute_alignment()

plan_relocations()

optimize_relocations()

build_segments()

assign_addresses()

relax_machine_code()

finalize_layout()

verify_binary_layout()

analyze_page_usage()
analyze_startup_footprint()

explain_layout()
explain_relocation()
compare_layout()
```

---

# 63. CLI

```text
axiom layout inspect
axiom layout explain
axiom layout diff
axiom layout stats

axiom binary analyze
axiom binary size
axiom binary pages
axiom binary relocations
axiom binary symbols
```

Ví dụ:

```text
axiom binary relocations app.exe
```

có thể trả:

```text
Static relative       142
PC-relative           381
Dynamic import         17
TLS                     3
Runtime                 0
```

---

# 64. Implementation tree

```text
compiler/
└── layout/
    ├── section_graph/
    ├── classification/
    ├── ordering/
    ├── alignment/
    ├── relocation/
    ├── symbol/
    ├── segment/
    ├── page/
    ├── tls/
    ├── unwind/
    ├── relaxation/
    ├── address/
    ├── cache/
    ├── verification/
    └── explain/
```

---

# 65. Invariants

```text
ALAYOUT-01
Every emitted section must have a valid retention reason.

ALAYOUT-02
Section layout must preserve ABI requirements.

ALAYOUT-03
Segment permissions must satisfy target security contracts.

ALAYOUT-04
Relocations must reference valid symbols and representable addresses.

ALAYOUT-05
Layout must not change observable program semantics.

ALAYOUT-06
Worker completion order must never determine semantic layout order.

ALAYOUT-07
Reproducible builds must use deterministic layout ordering.

ALAYOUT-08
Alignment padding must be accounted for in binary-size analysis.

ALAYOUT-09
Hot/cold classification must never alter semantic behavior.

ALAYOUT-10
PGO information may influence layout but cannot establish semantic facts.

ALAYOUT-11
Stable ABI symbols must retain required representation and calling conventions.

ALAYOUT-12
Internal symbols may use optimized layout when their addresses are not observable.

ALAYOUT-13
Function folding must preserve address-identity semantics where observable.

ALAYOUT-14
Data folding must preserve storage-identity semantics where observable.

ALAYOUT-15
Relocation optimization must preserve loader semantics.

ALAYOUT-16
W^X/security requirements must be preserved where required.

ALAYOUT-17
TLS layout must satisfy target ABI.

ALAYOUT-18
Unwind metadata must match the final machine code.

ALAYOUT-19
Relaxation must preserve instruction semantics.

ALAYOUT-20
Relaxation must terminate at a stable layout.

ALAYOUT-21
Layout cache entries require valid fingerprints.

ALAYOUT-22
Incremental layout must produce semantics equivalent to clean layout.

ALAYOUT-23
Binary verification is mandatory before final artifact publication.

ALAYOUT-24
Debug metadata may be removed only when the selected artifact profile permits it.

ALAYOUT-25
Final binary addresses are not semantic identities unless an explicit contract makes them observable.
```

---

# 66. Definition of Done

BOOTSTRAP-336 hoàn thành khi Axiom có:

- Section Graph.
- Hot/cold classification.
- Startup reachability layout.
- Function ordering.
- Data ordering.
- Alignment optimization.
- Alignment budget.
- Read-only data placement.
- String placement.
- Relocation classification.
- Relocation cost model.
- PC-relative optimization.
- PIC/PIE support.
- Segment construction.
- Permission verification.
- BSS optimization.
- Page-aware layout.
- Symbol visibility optimization.
- Import/export minimization.
- Dynamic dependency minimization.
- TLS layout.
- TLS model selection.
- Unwind metadata layout.
- Runtime metadata trimming.
- Minimal-runtime integration.
- Function/data address assignment.
- Address observability analysis.
- Deterministic layout.
- Layout fingerprints.
- Incremental layout cache.
- Linker relaxation.
- Branch-range relaxation.
- Fixed-point layout verification.
- Binary layout verifier.
- Page/startup footprint analyzer.
- Relocation analyzer.
- Layout explanation tools.
- Integration với 335 Whole-Program Optimization.
- Integration với 302 Object Writer.
- Integration với 303 Linker.
- Integration với 304 Native Executable Writer.
- Integration với 324 ABI.
- Integration với 325 Component.
- Integration với 326 FFI.
- Integration với 327 Platform.
- Integration với 328 Target Matrix.
- Integration với 331 Hermetic Build.
- Integration với 333 Incremental Build.
- Integration với 334 Scheduler.

## Nguyên tắc khóa

> **335 quyết định “cái gì tồn tại”. 336 quyết định “những thứ tồn tại được đặt như thế nào”.**

Và quan trọng nhất:

> **Axiom phải tối ưu binary ở cấp độ section, page, relocation và loader—not chỉ ở cấp độ instruction.**

Điều này tạo thành chuỗi hoàn chỉnh:

```text
Semantic Analysis
      ↓
Whole Program
      ↓
Dead Code Elimination
      ↓
Section Graph
      ↓
Binary Layout
      ↓
Relocation Optimization
      ↓
Machine Relaxation
      ↓
Verified Native Binary
```

Đây là một trong những nền tảng quan trọng để mục tiêu **native executable nhỏ, startup nhanh và runtime tối thiểu** của Axiom không chỉ dừng ở khẩu hiệu.