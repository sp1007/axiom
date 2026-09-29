# BOOTSTRAP-151 — Link-Time Code Generation, Section GC, Binary Size & Post-Link Optimization
**STATUS: FROZEN / COMPLETED**

> **Binary cuối cùng phải chứa gần nhất có thể với những gì chương trình thực sự cần: code, data, metadata và runtime đều phải trải qua reachability analysis và dead elimination.**

Đây là tầng cuối của optimization trước khi artifact được giao cho OS/loader.

---

## 1. Vị trí

```text
Optimized OptIR
      ↓
ABI MIR
      ↓
Axiom LIR
      ↓
Machine IR
      ↓
Machine Code
      ↓
Object Writer
      ↓
Object Files
      ↓
LTO / Link Graph
      ↓
Section GC
      ↓
ICF / Data Merging
      ↓
Code/Data Layout
      ↓
Relocation Optimization
      ↓
Binary Layout
      ↓
Post-Link Optimization
      ↓
FINAL BINARY
```

Điểm quan trọng: **151 không thay đổi semantics của chương trình.**

---

# 2. Binary Size Model

Axiom cần xem binary như:

```text
Binary =
    Code
  + ReadOnlyData
  + MutableData
  + BSS
  + TLS
  + Runtime
  + Relocations
  + Metadata
  + Debug/Unwind
  + Platform-required structures
```

Mục tiêu size optimization phải xét từng thành phần.

Ví dụ:

```text
Code            600 KB
Runtime         180 KB
ROData          120 KB
Relocations      30 KB
Unwind           20 KB
Metadata         10 KB
```

Không thể chỉ tối ưu instruction count.

---

# 3. Section Reachability

Linker xây:

```text
LinkGraph
```

với:

```text
Root
 ↓
Symbol
 ↓
Section
 ↓
Relocation
 ↓
Referenced Section
```

Ví dụ:

```text
main
 ↓
foo
 ↓
bar
```

nhưng:

```text
unused()
```

không có đường tới root.

→ loại bỏ.

---

# 4. Section GC

Thay vì chỉ loại bỏ function:

```text
unused_function
```

Axiom nên loại bỏ **section fragment**.

Ví dụ:

```text
foo
 ├── hot code
 ├── cold error path
 ├── unused helper
 └── unused constant
```

Linker có thể loại từng phần nếu section graph cho phép.

---

# 5. Function Sections

Codegen nên hỗ trợ:

```text
one function / logical section
```

hoặc granular fragments phù hợp.

Ví dụ:

```text
.text.foo
.text.bar
.text.baz
```

Sau đó:

```text
unused baz
→ remove
```

Mục tiêu là tránh:

```text
giữ cả một object lớn
```

chỉ vì một function nhỏ được sử dụng.

---

# 6. Data Sections

Tương tự với data:

```text
.rodata.string1
.rodata.string2
.data.config1
.data.config2
```

Nếu:

```text
string2
```

không reachable:

```text
remove
```

Điều này đặc biệt hữu ích với generated code và generic-heavy applications.

---

# 7. Generic Explosion

Generic specialization có thể tạo:

```text
foo<T1>
foo<T2>
foo<T3>
foo<T4>
...
```

Nếu một số instance không reachable:

```text
DCE
```

Nếu nhiều instance tạo implementation tương đương:

```text
ICF / code sharing
```

---

# 8. Identical Code Folding

Ví dụ:

```text
foo()
bar()
baz()
```

sau codegen đều thành cùng machine implementation.

Có thể:

```text
foo ─┐
bar ─┼→ shared implementation
baz ─┘
```

nhưng chỉ khi:

- ABI tương thích;
- function identity không observable;
- address identity không observable;
- unwind/debug semantics vẫn xử lý đúng;
- export requirements không bị phá;
- profiler/debugger contract cho phép.

---

# 9. Function Address Identity

Đây là ngoại lệ quan trọng.

Nếu chương trình làm:

```ax
let p = address_of(foo);
```

hoặc function pointer identity được observable, compiler không được giả định:

```text
foo == bar
```

chỉ vì machine code giống nhau.

Do đó:

```text
Semantic Function Identity
        ≠
Machine Code Equality
```

---

# 10. Data Merging

Có thể có:

```text
const A = "hello";
const B = "hello";
```

Nếu identity không observable:

```text
A ─┐
   ├→ shared data
B ─┘
```

Nhưng nếu address identity được quan sát:

```text
address(A) != address(B)
```

thì không được merge.

---

# 11. String pooling

String literals có thể được deduplicate:

```text
"hello"
"hello"
"hello"
```

→ một storage instance nếu semantics cho phép.

Điều này giúp giảm:

```text
ROData
```

đặc biệt ở ứng dụng lớn.

---

# 12. Zero-sized / Empty Data

Các object không có runtime storage cần thiết có thể được loại bỏ physical allocation.

Ví dụ semantic:

```text
struct Marker {}
```

không nhất thiết cần byte storage.

Nhưng ABI/FFI/layout contracts vẫn phải được tôn trọng.

---

# 13. BSS optimization

Zero-initialized global:

```ax
static buffer: [u8; 1_000_000] = zero;
```

không nhất thiết phải chứa 1 MB zero trong file.

Có thể:

```text
BSS = 1 MB
file contribution ≈ 0
```

Loader tạo zero pages.

Đây là optimization của object/binary representation, semantics không thay đổi.

---

# 14. Relocation Optimization

Relocation có thể làm binary lớn và ảnh hưởng loading.

Axiom linker cần phân tích:

```text
absolute
PC-relative
GOT
PLT
TLS
section-relative
image-relative
```

và chọn relocation nhỏ/đơn giản nhất phù hợp target.

---

# 15. Direct Call Optimization

Nếu:

```text
foo → bar
```

đã được chứng minh local/static:

```text
indirect call
```

có thể trở thành:

```text
direct call
```

nếu ABI và relocation cho phép.

Điều này vừa:

```text
size ↓
overhead ↓
```

vừa giúp:

```text
branch prediction
```

---

# 16. PLT/GOT elimination

Trong static hoặc closed-world executable, một số dynamic indirection không cần thiết.

Ví dụ:

```text
call foo@PLT
```

có thể trở thành direct call nếu linker chứng minh:

```text
foo is local/non-preemptible
```

Điều này giảm:

- indirection;
- relocation;
- code;
- runtime overhead.

---

# 17. Symbol visibility

Axiom đã phân biệt:

```text
pub
```

và:

```text
@export
```

Linker dùng chính distinction này.

Một symbol không cần external visibility có thể:

```text
localize
```

→ thêm optimization freedom.

---

# 18. Symbol preemption

Dynamic linking có thể khiến external symbol bị thay thế.

Nếu target ABI cho phép preemption:

```text
foo()
```

không thể luôn biến thành local direct call.

Nhưng nếu:

```text
non-preemptible
```

thì linker có thể tối ưu mạnh hơn.

---

# 19. Hot/Cold Binary Layout

Sau PGO:

```text
HOT
 ├── main
 ├── process
 ├── vector_loop
 └── parser_fast

COLD
 ├── error
 ├── panic
 ├── diagnostics
 └── rare path
```

Linker sắp xếp:

```text
.text.hot
.text
.text.cold
```

để tối ưu instruction locality.

---

# 20. Function ordering

Có thể xây:

```text
CallGraph
```

và tìm ordering:

```text
A → B
A → C
B → D
```

để đặt:

```text
A B D C
```

thay vì random:

```text
C D A B
```

Mục tiêu:

```text
I-cache
iTLB
branch locality
page locality
```

---

# 21. Code alignment

Alignment đôi khi giúp performance:

```text
function alignment
loop alignment
hot block alignment
```

nhưng alignment cũng làm:

```text
padding ↑
binary size ↑
```

Vì vậy 151 phải có:

```text
AlignmentCostModel
```

chứ không align mọi thứ tối đa.

---

# 22. Size optimization mode

Axiom nên có:

```text
-Oz
```

hoặc tương đương:

```text
--opt=size
```

Mục tiêu:

```text
binary size
```

thay vì:

```text
maximum throughput
```

Compiler có thể chọn:

```text
less inlining
less unrolling
more code sharing
smaller instruction encodings
less alignment
```

---

# 23. Speed mode

Ngược lại:

```text
-O3
```

có thể ưu tiên:

```text
execution speed
```

và chấp nhận:

```text
code size ↑
```

Ví dụ:

```text
-Oz
→ shared implementation

-O3
→ specialized implementation
```

Cả hai vẫn semantic-equivalent.

---

# 24. Balanced mode

Đề xuất default:

```text
-O2
```

hoặc Axiom tương đương:

```text
balanced
```

cân bằng:

```text
speed
size
compile time
```

---

# 25. Post-Link Optimization

Sau khi link:

```text
Executable
```

vẫn có thể tối ưu một số thứ:

```text
binary layout
branch relaxation
padding
relocation
instruction relaxation
section placement
```

Nhưng post-link optimizer phải **không phá machine-code correctness**.

---

# 26. Binary rewriting boundary

Post-link optimizer chỉ được phép thay đổi:

```text
machine representation
```

khi có:

```text
verified transformation
```

Không được suy luận lại:

```text
ownership
capability
type
trait
```

vì những semantic facts đó đã kết thúc trước machine code.

---

# 27. Debug information

Debug info:

```text
DWARF
PDB
CodeView
```

không được làm thay đổi release binary semantics.

Có thể:

```text
release
→ strip debug
```

hoặc:

```text
debug
→ preserve
```

---

# 28. Unwind information

Nếu:

```text
panic=abort
```

và platform không yêu cầu unwind:

```text
unwind metadata
→ eliminate
```

Nếu:

```text
panic=unwind
```

thì phải giữ:

```text
cleanup paths
unwind tables
personality information
```

theo target ABI.

---

# 29. Runtime size

Do Axiom không có monolithic runtime:

```text
program
 ↓
runtime dependency graph
 ↓
reachable components
```

Ví dụ:

```text
STARTUP
ALLOCATOR
IO
```

nhưng không:

```text
ASYNC
GPU
REFLECTION
UNICODE
```

→ runtime components không dùng được loại bỏ.

---

# 30. Startup optimization

Minimal program:

```ax
fn main() {
    return;
}
```

không nên kéo theo:

```text
network runtime
async executor
thread runtime
reflection
GC
```

Startup path nên tối thiểu:

```text
OS loader
 ↓
Axiom entry
 ↓
minimal initialization
 ↓
main
 ↓
exit
```

---

# 31. Dynamic initialization elimination

Nếu compiler chứng minh:

```text
global initialization
```

chỉ phụ thuộc compile-time constants:

```text
comptime
 ↓
materialized static
```

thì không cần runtime initializer.

Điều này giúp:

```text
startup time ↓
binary code ↓
runtime dependencies ↓
```

---

# 32. Section compression

Một số platform/artifact có thể hỗ trợ:

```text
compressed debug
compressed metadata
```

Nhưng executable loader-visible sections phải tuân target requirements.

Không nên tự tạo custom compressed executable format nếu OS loader không hiểu.

---

# 33. WASM

WASM có một số optimization riêng:

```text
function section
code section
data section
element section
custom section
```

Có thể:

```text
unused functions → remove
unused data → remove
custom metadata → strip
```

và dùng WASM-specific code size optimizations.

---

# 34. Mach-O

Mach-O cần giữ:

```text
load commands
segments
symbols
relocations
codesign-related structures
```

nếu target yêu cầu.

Do đó:

```text
binary minimization
```

không có nghĩa:

```text
remove arbitrary metadata
```

---

# 35. PE/COFF

Windows executable cần xét:

```text
PE headers
sections
imports
exports
relocations
TLS
unwind
resources
```

Linker phải biết phần nào platform-required.

---

# 36. ELF

Linux/Unix-like targets cần xét:

```text
ELF headers
segments
sections
dynamic table
relocations
TLS
GNU/OS metadata
unwind
```

Axiom linker abstraction giữ semantics chung, backend xử lý platform details.

---

# 37. Binary correctness validator

Sau linker nên có:

```text
BinaryValidator
```

kiểm tra:

```text
headers
sections
alignment
symbols
relocations
imports
exports
entry
segment permissions
TLS
unwind
platform constraints
```

Sau đó:

```text
Validated Binary
```

mới được xuất.

---

# 38. Binary reproducibility

Với:

```text
--reproducible
```

phải kiểm soát:

```text
section ordering
symbol ordering
timestamps
UUID/build IDs policy
padding
hashes
metadata ordering
```

trong phạm vi platform cho phép.

Hai build cùng input:

```text
same semantic inputs
+
same target/config
+
same profile
```

→ deterministic output policy.

---

# 39. Binary inspection

Axiom nên có:

```text
axc inspect binary app
axc inspect binary app --sections
axc inspect binary app --symbols
axc inspect binary app --imports
axc inspect binary app --exports
axc inspect binary app --relocations
axc inspect binary app --size
axc inspect binary app --roots
```

Ví dụ:

```text
Binary Size: 842 KB

.text       401 KB
.rodata     133 KB
.data        21 KB
.bss          8 KB
.runtime     61 KB
.metadata    12 KB
.headers     17 KB
```

---

# 40. “Binary nhỏ như ASM” — cần định nghĩa lại

Không thể cam kết:

> Axiom binary luôn nhỏ bằng assembly.

Vì binary còn phụ thuộc:

```text
OS ABI
loader
security metadata
unwind
dynamic linking
CPU architecture
debug
runtime requirements
```

Nhưng Axiom có thể đặt mục tiêu chính xác hơn:

> **Không thêm binary overhead chỉ vì ngôn ngữ có abstraction.**

Ví dụ:

```ax
v.length()
```

không nên tự động tạo:

```text
method object
virtual dispatch
object header
runtime metadata
```

nếu semantics không yêu cầu.

Đây là mục tiêu thực tế và mạnh hơn.

---

# 41. Binary-size optimization hierarchy

Toàn bộ chiến lược:

```text
Language
 ↓
No mandatory runtime
 ↓
Compiler DCE
 ↓
Generic DCE
 ↓
LTO
 ↓
Section GC
 ↓
ICF
 ↓
Data merging
 ↓
Runtime component GC
 ↓
Hot/cold layout
 ↓
Instruction-size optimization
 ↓
Relocation optimization
 ↓
Post-link optimization
```

---

# 42. Invariants

Đóng băng:

### `ABINOPT-20`
Binary optimization preserves executable semantics.

### `ABINOPT-21`
Unreachable code may be removed.

### `ABINOPT-22`
Unreachable data may be removed.

### `ABINOPT-23`
Section-level reachability may be finer than function-level reachability.

### `ABINOPT-24`
Generic instances not reachable may be eliminated.

### `ABINOPT-25`
Identical implementations may be folded when observable identity permits.

### `ABINOPT-26`
Function address identity prevents invalid code folding.

### `ABINOPT-27`
Data address identity prevents invalid data merging.

### `ABINOPT-28`
String pooling is permitted where identity semantics permit.

### `ABINOPT-29`
BSS representation may replace stored zero data where platform semantics permit.

### `ABINOPT-30`
Relocation optimization must preserve target ABI.

### `ABINOPT-31`
Local/non-preemptible calls may replace dynamic indirection.

### `ABINOPT-32`
Exported symbols remain externally observable according to ABI.

### `ABINOPT-33`
Dynamic loading constraints prevent invalid dead stripping.

### `ABINOPT-34`
Reflection roots must be preserved according to reflection contract.

### `ABINOPT-35`
Hot/cold code layout is non-semantic optimization.

### `ABINOPT-36`
Code alignment must balance performance and binary size.

### `ABINOPT-37`
Debug metadata may be removed without changing program semantics.

### `ABINOPT-38`
Unwind metadata may be removed only when the selected panic/ABI profile permits.

### `ABINOPT-39`
Unused runtime components may be removed.

### `ABINOPT-40`
Compile-time initialization may replace runtime initialization where semantics permit.

### `ABINOPT-41`
Post-link optimization must operate only on verified machine-level transformations.

### `ABINOPT-42`
Post-link optimization cannot recreate or bypass semantic verification.

### `ABINOPT-43`
Platform loader requirements must always be preserved.

### `ABINOPT-44`
PE/ELF/Mach-O/WASM constraints remain target-specific.

### `ABINOPT-45`
Size optimization may trade execution speed for binary size but cannot alter semantics.

### `ABINOPT-46`
Speed optimization may trade binary size for execution performance but cannot alter semantics.

### `ABINOPT-47`
Reproducible builds must produce deterministic binary layout given identical inputs.

### `ABINOPT-48`
Binary artifacts must remain inspectable.

### `ABINOPT-49`
Binary-size decisions must have explainable roots and retained sections.

### `ABINOPT-50`
No language abstraction creates mandatory runtime/binary overhead unless its semantics require it.

---

# Một mốc quan trọng đã đạt được

Đến `BOOTSTRAP-151`, Axiom đã có kiến trúc gần như hoàn chỉnh:

```text
┌─────────────────────────────────────────────┐
│                LANGUAGE                     │
│ Syntax / Types / Traits / Ownership         │
│ Capability / Async / Concurrency / GPU      │
└──────────────────────┬──────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│              SEMANTIC COMPILER              │
│ HIR / MIR / Verification                    │
└──────────────────────┬──────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│                OPTIMIZER                    │
│ Alias / Effect / Escape / SSA / MemorySSA   │
│ Inline / Specialize / Loop / Memory / DOD   │
│ SIMD / Microarchitecture / PGO / LTO        │
└──────────────────────┬──────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│                 BACKEND                     │
│ ABI / LIR / Machine / Register Allocation   │
│ Scheduling / Encoding                       │
└──────────────────────┬──────────────────────┘
                       ↓
┌─────────────────────────────────────────────┐
│             BINARY TOOLCHAIN                │
│ Object / Linker / Section GC / ICF / Layout │
│ PE / ELF / Mach-O / WASM                    │
└─────────────────────────────────────────────┘
```

Điểm này cũng cho thấy một điều quan trọng: **không cần tiếp tục thêm hàng loạt tính năng ngôn ngữ chỉ để “làm compiler mạnh hơn”**. Phần compiler core đã có nền móng rất sâu. Từ đây nên bắt đầu xử lý những thành phần còn thiếu để biến architecture thành **một hệ thống có thể thực thi được**.

## BOOTSTRAP-152 — Compiler Driver, CLI, Build Orchestration & Compilation Pipeline

Task kế tiếp sẽ chuyển từ “compiler architecture” sang **cách `axc` thực sự vận hành**:

```text
axc
 ├── build
 ├── check
 ├── run
 ├── test
 ├── bench
 ├── emit
 ├── link
 ├── inspect
 ├── profile
 └── tune

        ↓

Workspace
        ↓
Package Graph
        ↓
Target Resolution
        ↓
Incremental CompilerDB
        ↓
Parallel Compilation
        ↓
Cache
        ↓
LTO
        ↓
Object
        ↓
Link
        ↓
Native Artifact
```

Đặc biệt sẽ cần chốt **một pipeline build thực tế có thể dùng để bootstrap Axiom compiler**, bao gồm cache, dependency scheduling, cross-compilation, diagnostics, cancellation, parallelism và cách chuyển dần từ compiler bootstrap bên ngoài sang `axc` tự build chính nó.