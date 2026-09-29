# BOOTSTRAP-781 — AXSTANDARD

**Title:** Native Axiom Standard Library, Core Collections, String/UTF-8, Option/Result/Error, Iteration, Algorithms, Math, Formatting, Parsing, Conversion, Time/Random Facades, File/Path Facades & Zero-Cost Standard Library Architecture 5.0  
**Namespace:** `AXSTANDARD`  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXSTANDARD` là **standard library của ngôn ngữ Axiom**, nằm trên `AXRUNTIME` nhưng dưới các thư viện/framework cấp cao.

```text
                         APPLICATION
                              │
                              ▼
                       ┌─────────────┐
                       │ AXSTANDARD │
                       ├─────────────┤
                       │ String      │
                       │ Collections │
                       │ Option/Result
                       │ Algorithms  │
                       │ Formatting  │
                       │ Parsing     │
                       │ Math        │
                       │ Path        │
                       │ Time facade │
                       │ Random facade│
                       └──────┬──────┘
                              │
                         AXRUNTIME
                              │
          ┌───────────────────┼──────────────────┐
          ▼                   ▼                  ▼
       AXMEMORY            AXTIME            AXRANDOM
          │                                      │
          └────────────── OS / PLATFORM ─────────┘
```

Mục tiêu chính:

1. API phong phú nhưng modular.
2. Không biến standard library thành mandatory monolith.
3. Không GC.
4. Không reference counting ngầm.
5. Không hidden allocation.
6. UTF-8 native.
7. Generic/monomorphized.
8. Zero-cost abstraction khi có thể.
9. Có thể dùng trong `no_std`/freestanding subset.
10. Binary size phải phụ thuộc API thực sự được sử dụng.

---

# 2. Nguyên tắc thiết kế

AXSTANDARD phải tuân theo:

```text
explicit > implicit
value > hidden object
generic > boxed
static dispatch > dynamic dispatch
borrowed view > unnecessary copy
stack > heap when lifetime permits
specialized > universal runtime machinery
```

---

# 3. Boundary

### AXSTANDARD sở hữu

- common language-level utility types;
- collections;
- strings;
- UTF-8;
- byte utilities;
- Option/Result facade;
- standard errors;
- iteration;
- algorithms;
- formatting;
- parsing;
- numeric utilities;
- path abstraction;
- basic environment abstraction;
- standard conversion traits/interfaces.

### Không sở hữu

```text
AXRUNTIME
→ process/runtime bootstrap

AXMEMORY
→ fundamental memory model

AXTIME
→ authoritative time subsystem

AXRANDOM
→ RNG implementation

AXSTORAGE
→ filesystem/storage engine

AXNETWORK
→ networking

AXDATABASE
→ database

AXCRYPTO
→ cryptography

AXGRAPHICS
→ graphics

AXWINDOW
→ windowing
```

AXSTANDARD chỉ cung cấp facade/adapters khi cần.

---

# 4. Modular structure

Không có một `std` monolith bắt buộc.

Conceptual modules:

```text
ax.standard.core
ax.standard.option
ax.standard.result
ax.standard.string
ax.standard.bytes
ax.standard.collections
ax.standard.iter
ax.standard.algorithm
ax.standard.numeric
ax.standard.math
ax.standard.format
ax.standard.parse
ax.standard.path
ax.standard.env
ax.standard.time
ax.standard.random
```

---

# 5. Profiles

```text
MINIMAL
CORE
STANDARD
EXTENDED
```

### MINIMAL

```text
core
option
result
basic conversion
```

### CORE

+

```text
string
bytes
slice
iter
collections
```

### STANDARD

+

```text
format
parse
math
path
time facade
random facade
```

### EXTENDED

Các tiện ích bổ sung.

---

# 6. No mandatory `std`

Freestanding program có thể:

```text
import ax.core
```

mà không kéo toàn bộ AXSTANDARD.

---

# 7. Core error model

AXSTANDARD dùng:

```text
Option<T>
Result<T, E>
```

làm primitive error/recovery model.

---

# 8. Option

Conceptual:

```text
enum Option<T> {
    None
    Some(T)
}
```

Compiler có thể áp dụng niche optimization khi ABI cho phép.

---

# 9. Result

```text
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Không cần exception runtime.

---

# 10. Option ABI

Không có heap allocation bắt buộc.

---

# 11. Result ABI

Nếu `T/E` nhỏ, Result có thể truyền trực tiếp qua registers theo AXABI.

---

# 12. Error type

Standard error interface:

```text
trait Error {
    fn code(self) -> ErrorCode
    fn message(self) -> StrView
}
```

Không bắt buộc dynamic allocation.

---

# 13. Error chaining

Có thể hỗ trợ:

```text
source()
cause()
context()
```

nhưng context phải explicit.

---

# 14. No implicit exception

Standard library không biến `Err` thành exception.

---

# 15. String architecture

Axiom phân biệt:

```text
String
Str
Bytes
ByteSlice
```

---

# 16. Owned String

```text
String
```

là UTF-8 owned string.

Conceptual representation:

```text
String {
    ptr
    len
    capacity
}
```

---

# 17. String ownership

`String` sở hữu storage.

Move là default.

---

# 18. Borrowed string

```text
Str
```

là immutable UTF-8 view.

Conceptual:

```text
Str {
    ptr
    len
}
```

---

# 19. Mutable string view

```text
StrMut
```

cho phép sửa bytes nếu caller đảm bảo UTF-8 invariant.

---

# 20. UTF-8 invariant

`String` và `Str` phải chứa valid UTF-8.

---

# 21. Invalid UTF-8

External data dùng:

```text
Bytes
```

hoặc conversion API trả `Result`.

---

# 22. UTF-8 validation

```text
utf8_validate(bytes)
```

phải có fast path SIMD khi target hỗ trợ.

---

# 23. UTF-8 decoding

Iterator:

```text
for ch in bytes.utf8()
```

không được allocate.

---

# 24. Unicode scalar

`char` đại diện Unicode scalar value theo language core.

---

# 25. Grapheme

Grapheme cluster không phải primitive `char`.

Unicode text segmentation thuộc higher-level text module.

---

# 26. String indexing

Không cho phép giả định:

```text
string[index]
```

là O(1) character indexing.

UTF-8 variable width phải được tôn trọng.

---

# 27. Byte indexing

Có thể:

```text
str.as_bytes()[i]
```

với semantics rõ ràng.

---

# 28. String slicing

Slicing theo byte phải đảm bảo boundary UTF-8.

Invalid boundary:

```text
Result::Err(...)
```

hoặc explicit unsafe API.

---

# 29. Unsafe string slicing

Có thể cung cấp:

```text
str.slice_unchecked(...)
```

nhưng phải là unsafe.

---

# 30. String concatenation

Compiler/library nên tối ưu:

```text
a + b + c
```

thành một allocation khi kích thước có thể biết trước.

---

# 31. String builder

```text
StringBuilder
```

dùng khi output dynamic.

---

# 32. String formatting

Formatting phải hỗ trợ preallocation.

---

# 33. String interpolation

Axiom có thể có syntax:

```text
"Hello {name}"
```

Compiler lowering phải tránh tạo intermediate strings.

---

# 34. Formatting trait

```text
trait Display
trait Debug
trait Format
```

API cuối cùng có thể hợp nhất nhưng semantics phải phân biệt human/debug representation.

---

# 35. Formatter

```text
Formatter {
    output
    options
    locale?
}
```

---

# 36. Formatter output

Formatter nên viết trực tiếp vào:

```text
StringBuilder
Writer
Buffer
```

thay vì tạo temporary strings.

---

# 37. Numeric formatting

Hỗ trợ:

```text
integer
float
hex
binary
octal
scientific
fixed
```

---

# 38. Integer formatting

Integer-to-string phải có allocation-free low-level API:

```text
format_i64_into(buffer, value)
```

---

# 39. Float formatting

Phải deterministic trong cùng formatting profile.

---

# 40. Parsing

Standard parsing:

```text
parse_i32()
parse_u64()
parse_f64()
parse_bool()
```

trả `Result`.

---

# 41. Parsing allocation

Primitive parsing không allocate.

---

# 42. Parser interfaces

```text
trait FromStr<T>
trait Parse
```

cho phép generic parsing.

---

# 43. Conversion

Standard conversion:

```text
Into
From
TryInto
TryFrom
As
```

Tên cụ thể có thể điều chỉnh, semantics phải explicit.

---

# 44. Implicit conversion

Chỉ cho phép implicit conversion an toàn và lossless mà compiler core đã định nghĩa.

---

# 45. Numeric narrowing

Ví dụ:

```text
i64 → i32
```

phải explicit hoặc trả Result nếu API conversion checked.

---

# 46. Checked arithmetic

```text
checked_add
checked_sub
checked_mul
checked_div
```

---

# 47. Wrapping arithmetic

```text
wrapping_add
wrapping_sub
wrapping_mul
```

---

# 48. Saturating arithmetic

```text
saturating_add
saturating_sub
```

---

# 49. Overflow policy

Native arithmetic behavior phải được language core định nghĩa; AXSTANDARD cung cấp các variant explicit.

---

# 50. Collections

Baseline:

```text
Array
Vec
Slice
Deque
List
Map
Set
```

Không phải tất cả đều phải có heap.

---

# 51. Vec

```text
Vec<T>
```

là contiguous growable array.

---

# 52. Vec representation

```text
Vec<T> {
    ptr
    len
    capacity
}
```

---

# 53. Vec growth

Growth policy là implementation detail, nhưng phải có upper-bound validation.

---

# 54. Vec reserve

```text
vec.reserve(n)
```

cho phép caller kiểm soát allocation.

---

# 55. Vec reserve_exact

Nếu cần:

```text
reserve_exact
```

để tránh growth slack.

---

# 56. Vec push

`push` có thể allocate khi capacity exhausted.

Đây là behavior explicit của collection operation, không phải hidden runtime allocation.

---

# 57. Vec no-allocation mode

Có thể dùng:

```text
try_push()
```

để trả error khi allocation thất bại.

---

# 58. FixedVec

```text
FixedVec<T, N>
```

lưu trên caller-provided storage hoặc inline storage.

---

# 59. SmallVec

Optional optimization:

```text
SmallVec<T, N>
```

có inline capacity.

Không được là core mandatory feature.

---

# 60. Slice

```text
Slice<T>
```

borrowed contiguous view.

---

# 61. Mutable slice

```text
SliceMut<T>
```

---

# 62. Array

```text
[T; N]
```

compile-time sized.

---

# 63. Deque

```text
Deque<T>
```

ring-buffer based.

---

# 64. Map

Baseline hash map:

```text
HashMap<K,V>
```

---

# 65. Hash map requirements

Phải có:

- deterministic API;
- configurable hasher;
- explicit collision behavior;
- reserve;
- capacity query.

---

# 66. Hash randomization

Hash seed randomization không được ảnh hưởng ABI/layout contract.

---

# 67. Deterministic HashMap

Build/test environments có thể chọn deterministic hasher.

---

# 68. TreeMap

Optional:

```text
TreeMap<K,V>
```

cho ordered operations.

---

# 69. Set

```text
HashSet<T>
TreeSet<T>
```

cùng semantics tương ứng.

---

# 70. Entry API

HashMap hỗ trợ:

```text
entry(key)
```

để tránh lookup hai lần.

---

# 71. Iteration

Canonical:

```text
Iterator<T>
```

---

# 72. Iterator model

Iterator phải hỗ trợ zero-cost monomorphized chains.

---

# 73. Iterator next

```text
fn next(self) -> Option<T>
```

---

# 74. Reference iterator

Để tránh copy:

```text
Iterator<&T>
```

hoặc equivalent view semantics.

---

# 75. Iterator adapters

Baseline:

```text
map
filter
take
skip
zip
enumerate
chain
flatten
flat_map
```

---

# 76. Terminal operations

```text
collect
fold
reduce
sum
min
max
any
all
find
```

---

# 77. Lazy iterators

Iterator adapters phải lazy.

---

# 78. No virtual iterator requirement

Iterator generic code phải monomorphize/static-dispatch mặc định.

---

# 79. Dynamic iterator

Nếu cần dynamic iterator:

```text
DynIterator<T>
```

phải explicit và có runtime cost.

---

# 80. Iterator allocation

Iterator chain không được mặc định heap allocate.

---

# 81. Algorithms

Standard algorithms:

```text
sort
stable_sort
binary_search
reverse
rotate
partition
copy
fill
```

---

# 82. Sorting

Default `sort` có thể dùng introsort/pdqsort-like algorithm, implementation không đóng đinh miễn semantics giữ.

---

# 83. Stable sorting

Separate API nếu stability required.

---

# 84. Parallel algorithms

Không phải default.

Có thể cung cấp:

```text
parallel_sort
parallel_for
```

qua AXTASK.

---

# 85. Numeric module

```text
abs
min
max
clamp
sign
pow
sqrt
```

---

# 86. Math

Baseline:

```text
sin
cos
tan
asin
acos
atan
atan2
exp
log
log2
log10
sqrt
cbrt
```

---

# 87. Math implementation

Compiler có thể lower tới:

- hardware instruction;
- intrinsic;
- platform math implementation.

Không bắt buộc libc.

---

# 88. Constants

```text
PI
TAU
E
LN2
LN10
SQRT2
```

---

# 89. Numeric limits

```text
min_value
max_value
epsilon
infinity
nan
```

---

# 90. Floating classification

```text
is_nan
is_inf
is_finite
is_normal
```

---

# 91. Bit operations

```text
count_ones
count_zeros
leading_zeros
trailing_zeros
rotate_left
rotate_right
reverse_bits
```

---

# 92. Endian conversion

```text
to_le
to_be
from_le
from_be
```

---

# 93. Byte order

Không được phụ thuộc host endian khi serialize dữ liệu.

---

# 94. Memory utilities

AXSTANDARD có thể cung cấp:

```text
copy
move
fill
compare
```

nhưng low-level implementation thuộc AXMEMORY/compiler intrinsics.

---

# 95. Unsafe memory operations

```text
ptr_copy
ptr_read
ptr_write
```

nằm trong explicit unsafe API.

---

# 96. Comparison

Traits:

```text
Eq
Ord
Hash
```

---

# 97. Equality

`Eq` phải có equivalence semantics.

---

# 98. Ordering

```text
Less
Equal
Greater
```

hoặc equivalent enum.

---

# 99. Hash

Hashing phải explicit.

Không hash raw object bytes mặc định vì padding/representation.

---

# 100. Clone/copy

Phân biệt:

```text
Copy
Clone
```

`Copy` không allocation.

`Clone` có thể allocation nếu type yêu cầu.

---

# 101. Default

```text
Default
```

không được giả định zero-initialization trừ khi type contract yêu cầu.

---

# 102. Iterator ownership

Iterator consuming collection phải move/borrow theo source semantics.

---

# 103. Collection invalidation

Mutation rules phải document:

```text
push
remove
reserve
```

có thể invalidate references/iterators.

---

# 104. Stable handles

Collection không mặc định cung cấp stable addresses.

---

# 105. Arena-backed collections

Có thể cung cấp collection sử dụng caller-owned arena.

---

# 106. Allocation failure

Standard collections phải có `try_*` variants ở các operation có thể allocate.

---

# 107. OOM policy

Runtime profile quyết định:

```text
abort
panic
Result
```

nhưng library API phải không che giấu allocation failure khi contract yêu cầu recoverability.

---

# 108. Byte buffers

```text
ByteBuffer
```

là growable `u8` storage.

---

# 109. Reader/Writer

Generic interfaces:

```text
Reader
Writer
```

---

# 110. Reader

```text
read(buffer) -> Result<usize, Error>
```

---

# 111. Writer

```text
write(buffer) -> Result<usize, Error>
flush() -> Result
```

---

# 112. Partial I/O

API phải cho phép partial read/write.

Không assume một call xử lý toàn bộ buffer.

---

# 113. Buffered reader

Optional:

```text
BufferedReader<R>
```

---

# 114. Buffered writer

Optional:

```text
BufferedWriter<W>
```

---

# 115. Formatting integration

Formatter có thể target `Writer` trực tiếp.

---

# 116. Path

```text
Path
PathBuf
```

---

# 117. Path semantics

Path không phải raw string.

Nó phải có platform-aware semantics.

---

# 118. Windows path

Support:

- drive letters;
- UNC;
- separator rules;
- UTF-16 platform conversion.

---

# 119. Unix path

Support raw bytes where OS permits.

---

# 120. UTF-8 path representation

Axiom API ưu tiên UTF-8 nhưng phải preserve Unix raw path bytes khi cần.

---

# 121. Path normalization

Không tự động resolve symlink hoặc filesystem semantics khi chỉ normalize lexical path.

---

# 122. Filesystem boundary

Actual filesystem operations thuộc AXSTORAGE.

AXSTANDARD chỉ facade types/API.

---

# 123. Environment

```text
env::get()
env::set()
env::remove()
```

phải forward tới AXPROCESS/platform layer.

---

# 124. Environment security

Environment data là untrusted input.

---

# 125. Process arguments

```text
args()
```

trả immutable view hoặc iterator.

---

# 126. Time facade

AXSTANDARD không định nghĩa clock implementation.

Dùng AXTIME:

```text
Instant
Duration
SystemTime
```

---

# 127. Duration

```text
Duration
```

là numeric value + unit semantics.

---

# 128. Random facade

AXSTANDARD có:

```text
Random
SecureRandom
DeterministicRandom
```

facade tới AXRANDOM.

---

# 129. No implicit random

Standard algorithms không được tự ý sử dụng cryptographic randomness.

---

# 130. Deterministic RNG

Tests có thể inject deterministic RNG.

---

# 131. Formatting locale

Core formatting phải deterministic và locale-independent.

Locale-sensitive formatting là optional.

---

# 132. Unicode normalization

Không tự động normalize mọi String.

API explicit:

```text
normalize_nfc()
normalize_nfd()
```

nếu Unicode data module được link.

---

# 133. Case conversion

Unicode case mapping là explicit operation.

---

# 134. ASCII fast path

UTF-8 operations nên có ASCII fast path.

---

# 135. SIMD string operations

Compiler có thể sử dụng SIMD cho:

- search;
- validation;
- copy;
- comparison.

---

# 136. Search

String:

```text
find
rfind
contains
starts_with
ends_with
```

---

# 137. Split

```text
split
split_once
lines
words
```

---

# 138. Allocation behavior

String splitting nên trả iterator views khi có thể.

---

# 139. Regex

Regex không thuộc core AXSTANDARD.

Có thể là separate package:

```text
ax.regex
```

để tránh binary bloat.

---

# 140. JSON

JSON không thuộc core AXSTANDARD.

Separate:

```text
ax.json
```

---

# 141. XML

Separate package.

---

# 142. Serialization

Standard serialization trait có thể tồn tại:

```text
Serialize
Deserialize
```

nhưng concrete formats là external modules.

---

# 143. Reflection

Không yêu cầu runtime reflection.

Compile-time metadata có thể hỗ trợ serialization/code generation.

---

# 144. Collections serialization

Không được raw-memory serialize.

---

# 145. Thread-safe collections

Không đưa mọi collection vào locking.

Optional:

```text
ConcurrentMap
ConcurrentQueue
```

dựa trên AXTASK/atomic primitives.

---

# 146. Atomic collections

Phải document memory-order semantics.

---

# 147. Synchronization wrappers

Standard library có thể cung cấp:

```text
Mutex
RwLock
Condvar
Once
Atomic*
```

nhưng implementation bridge tới AXMEMORY/AXTASK/AXPROCESS.

---

# 148. Mutex

Mutex ownership phải explicit.

---

# 149. Mutex poisoning

Không mặc định sử dụng poisoning.

Nếu hỗ trợ, phải explicit policy.

---

# 150. RwLock

Reader/writer fairness không được giả định nếu implementation không guarantee.

---

# 151. Once

```text
Once
OnceCell
Lazy
```

là useful standard primitives.

---

# 152. Lazy

Lazy initialization không được tạo deadlock với runtime initialization.

---

# 153. OnceCell

Có thể sử dụng để xây global immutable initialization.

---

# 154. Cell/atomic interior state

Phải dựa trên memory model của AXMEMORY.

---

# 155. Channels

Channels thuộc standard concurrency utilities:

```text
Channel<T>
```

nhưng scheduler integration nằm AXTASK.

---

# 156. Channel variants

```text
bounded
unbounded
oneshot
```

---

# 157. No hidden threads

Channel không tự tạo thread.

---

# 158. Select

Async/task channel có thể support:

```text
select
```

thông qua AXASYNC.

---

# 159. Synchronization error

Closed channel phải trả explicit state/error.

---

# 160. Collections and ABI

Collection layouts không stable public ABI mặc định.

---

# 161. ABI-stable collection

Nếu cần FFI:

```text
#[abi_stable]
```

phải expose explicit C-compatible view.

---

# 162. FFI strings

Standard library cung cấp:

```text
CString
CStr
```

hoặc equivalent.

---

# 163. CString invariant

Không chứa interior NUL nếu API contract yêu cầu C string.

---

# 164. CStr

Borrowed NUL-terminated view.

---

# 165. C UTF conversion

UTF-8 ↔ platform wide string conversion explicit.

---

# 166. OS handles

Standard library không wrap mọi OS handle thành generic object.

Platform handle types nằm platform modules.

---

# 167. File abstraction

`File` có thể thuộc AXSTORAGE facade.

AXSTANDARD chỉ define common traits `Reader/Writer/Seek`.

---

# 168. Seek

```text
Seek {
    seek(position)
}
```

---

# 169. Buffered I/O

Buffer size configurable.

---

# 170. Memory mapping

`Mmap` thuộc AXSTORAGE/AXMEMORY, không core standard.

---

# 171. Error taxonomy

Baseline:

```text
InvalidInput
NotFound
PermissionDenied
AlreadyExists
Busy
Timeout
Interrupted
OutOfMemory
Unsupported
Io
Overflow
Encoding
```

---

# 172. OS error

Preserve native error code:

```text
OsError {
    platform
    code
}
```

---

# 173. Error conversion

Không discard native error code khi chuyển thành standard error.

---

# 174. Formatting error

Formatting APIs có error type nhẹ.

---

# 175. Parse error

```text
ParseError {
    kind
    position
}
```

---

# 176. UTF error

```text
Utf8Error {
    position
}
```

---

# 177. Collection error

Các operation có thể fail:

```text
TryReserveError
IndexError
CapacityError
```

---

# 178. Indexing

Safe indexing:

```text
vec[index]
```

có thể panic nếu out-of-range, tùy language operator semantics.

Explicit:

```text
vec.get(index) -> Option<&T>
```

---

# 179. Bounds-check elimination

Compiler được phép eliminate bounds checks khi chứng minh an toàn.

---

# 180. Unsafe indexing

```text
get_unchecked()
```

là unsafe.

---

# 181. Iteration and bounds checks

Compiler có thể lower iterator loops thành bounds-check-free loops.

---

# 182. Range

```text
Range<T>
```

là zero-cost value type.

---

# 183. Range forms

```text
a..b
a..=b
..b
a..
..
```

nếu language syntax hỗ trợ.

---

# 184. Range iteration

Integer range phải compile thành native loop khi optimization bật.

---

# 185. Generic algorithms

Generic algorithm phải monomorphize khi static dispatch.

---

# 186. Code bloat

Compiler có thể deduplicate identical instantiations.

---

# 187. Dynamic dispatch

Chỉ khi user explicit hoặc type semantics yêu cầu.

---

# 188. Allocator-aware collections

Future extension có thể support:

```text
Vec<T, A>
```

nhưng default allocator phải đơn giản.

---

# 189. Custom allocator

Không làm custom allocator bắt buộc cho normal applications.

---

# 190. No implicit copy

Large collections/strings không copy khi move.

---

# 191. Move semantics

AXSTANDARD types phải tuân core move semantics.

---

# 192. Clone semantics

Explicit clone.

---

# 193. Equality cost

Collection equality là O(n) trừ khi type-specific optimization.

---

# 194. Hash cost

Không hash capacity/uninitialized memory.

---

# 195. Deterministic iteration

HashMap iteration order không mặc định là stable API.

Nếu cần deterministic order:

```text
OrderedMap
```

---

# 196. Stable ordered map

`TreeMap` cung cấp sorted iteration.

---

# 197. Memory layout inspection

Compiler có thể expose:

```text
size_of<T>()
align_of<T>()
```

compile-time intrinsic.

---

# 198. Type identity

Standard generic types phải có deterministic compiler identity.

---

# 199. Generic ABI

Standard generic types không được coi là stable cross-compiler ABI mặc định.

---

# 200. Standard library source

AXSTANDARD phải được viết chủ yếu bằng Axiom.

---

# 201. Intrinsics

Một số primitive có thể được compiler intrinsic:

```text
memcpy
memset
ctpop
sqrt
fma
```

---

# 202. Intrinsic boundary

Intrinsic semantics phải được compiler spec và AXSTANDARD thống nhất.

---

# 203. Hardware acceleration

Standard algorithms có thể dispatch:

```text
baseline
CPU extension
```

---

# 204. CPU feature dispatch

AXTOOLCHAIN/AXCOMPILER cung cấp CPU feature information.

---

# 205. Multiversioning

Optional:

```text
#[target_feature("avx2")]
```

hoặc equivalent.

---

# 206. Runtime CPU dispatch

Nếu dynamic dispatch cần thiết:

```text
feature_detect()
```

chỉ chạy một lần hoặc cache kết quả.

---

# 207. Security-sensitive operations

Crypto không thuộc AXSTANDARD.

Dùng AXCRYPTO.

---

# 208. Constant-time

Standard equality/hash không mặc định constant-time.

Crypto code phải dùng AXCRYPTO-specific APIs.

---

# 209. Standard library threading

Không tự start worker pool.

---

# 210. Global thread pool

Nếu cần, thuộc AXTASK runtime, opt-in.

---

# 211. Blocking APIs

Blocking API phải annotate:

```text
@blocking
```

---

# 212. Allocation annotation

APIs có thể annotate:

```text
@allocates
```

---

# 213. Panic annotation

```text
@panic
```

cho phép compiler/AI biết behavior.

---

# 214. Thread-safety annotation

```text
@thread_safe
@thread_affine
```

---

# 215. Ownership metadata

Standard APIs phải expose ownership semantics cho AI/compiler tooling.

---

# 216. AI-readable standard API

Manifest:

```text
StandardApiMetadata {
    module
    symbol
    signature
    effects
    allocation
    blocking
    ownership
    panic
    thread_safety
}
```

---

# 217. Effect metadata

Có thể mô tả:

```text
allocates
blocks
io
throws/panics
unsafe
```

---

# 218. Effect metadata không thay thế type system

Đây là supplementary metadata.

---

# 219. Documentation generation

`ax doc` có thể đọc AXSTANDARD metadata.

---

# 220. Source compatibility

Standard library API changes phải follow semantic versioning.

---

# 221. Binary compatibility

Core generic library không guarantee binary ABI.

Stable FFI facade mới guarantee ABI.

---

# 222. Standard library ABI facade

Ví dụ:

```text
ax.standard.cabi
```

có thể expose stable ABI functions.

---

# 223. Static linking default

AXSTANDARD mặc định static-link friendly.

---

# 224. Dead stripping

Unused generic/functions phải được eliminated.

---

# 225. Link-time optimization

AXSTANDARD được thiết kế để LTO dễ dàng.

---

# 226. Inline functions

Small standard functions nên inlineable.

---

# 227. Cold functions

Parsing/error formatting có thể đánh dấu cold.

---

# 228. Error paths

Error formatting không được làm hot path chậm.

---

# 229. Allocation-free APIs

Nên cung cấp:

```text
*_into(buffer)
*_with_capacity()
try_*
```

cho performance-sensitive code.

---

# 230. Buffer reuse

Caller có thể reuse buffers.

---

# 231. Zero-copy APIs

String/bytes parsing nên ưu tiên views.

---

# 232. Copy-on-write

Không dùng CoW String mặc định.

Lý do:

- hidden atomic/refcount;
- unpredictable cost;
- concurrency complexity.

---

# 233. Reference counting

Không dùng implicit RC trong core standard types.

---

# 234. Garbage collection

Không có.

---

# 235. Hidden finalizers

Không có implicit finalizer mechanism.

---

# 236. Resource cleanup

Dùng deterministic scope/drop semantics của language core.

---

# 237. File cleanup

`File` ownership phải deterministic.

---

# 238. Lock cleanup

Mutex guards có deterministic lifetime.

---

# 239. Collection cleanup

Collection destructor giải phóng storage khi owner kết thúc.

---

# 240. Iterator cleanup

Iterator không giữ hidden global state.

---

# 241. String cleanup

String destructor/free theo allocator contract.

---

# 242. Panic during destructor

Destructor panic policy phải thuộc language/runtime panic model.

---

# 243. Double panic

Second panic trong cleanup phải terminate hoặc follow explicit policy.

---

# 244. Standard library testing

Mọi module phải có:

- unit tests;
- property tests;
- fuzz tests khi parser;
- performance tests;
- allocation tests.

---

# 245. String fuzzing

Fuzz:

- invalid UTF-8;
- boundary bytes;
- overlong sequences;
- surrogate encodings;
- truncation.

---

# 246. Collection fuzzing

Fuzz sequences:

```text
push
remove
insert
reserve
clear
```

---

# 247. Parser fuzzing

Không crash hoặc infinite-loop với arbitrary bytes.

---

# 248. Formatter fuzzing

Format strings malformed phải trả error hoặc compile-time diagnostic.

---

# 249. Iterator property tests

Kiểm tra:

```text
map/filter/fold
```

compositional correctness.

---

# 250. Numeric property tests

Checked/wrapping/saturating arithmetic phải có reference model.

---

# 251. Cross-platform tests

Standard APIs phải test:

```text
Windows
Linux
macOS
Android
WASM
```

những phần platform-relevant.

---

# 252. WASM standard subset

WASM build phải loại bỏ APIs không host-supported.

---

# 253. Freestanding standard subset

```text
ax.standard.core
ax.standard.option
ax.standard.result
ax.standard.bytes
```

phải có khả năng chạy không OS.

---

# 254. No-libc standard subset

Core algorithms/string/numeric không được phụ thuộc libc.

---

# 255. Platform library adapters

Platform-dependent APIs nằm module adapter.

---

# 256. Standard library package layout

Conceptual:

```text
ax/
 └── standard/
     ├── core
     ├── option
     ├── result
     ├── string
     ├── bytes
     ├── collections
     ├── iter
     ├── algorithm
     ├── numeric
     ├── math
     ├── format
     ├── parse
     ├── path
     ├── env
     ├── time
     └── random
```

---

# 257. Standard prelude

Axiom có thể cung cấp:

```text
prelude
```

nhưng prelude phải nhỏ.

---

# 258. Prelude contents

Chỉ những thứ dùng cực kỳ thường xuyên:

```text
Option
Result
basic traits
basic iterator
basic numeric types
```

Không import toàn bộ collections.

---

# 259. Explicit imports

Heavy modules phải explicit import.

---

# 260. Compile-time import elimination

Unused imports không kéo binary code.

---

# 261. Namespace collisions

Standard names nằm namespace `ax`.

---

# 262. User override

User có thể shadow/import aliases nhưng không thay đổi intrinsic semantics.

---

# 263. Standard trait coherence

Không cho phép arbitrary conflicting implementations.

---

# 264. Extension methods

Có thể cung cấp qua traits.

---

# 265. Trait method overhead

Static trait calls phải inline/monomorphize khi possible.

---

# 266. Dynamic trait calls

Explicit trait objects mới có indirect-call cost.

---

# 267. Iterator fusion

Compiler có thể fuse iterator adapters.

---

# 268. Bounds-check elimination

Collection iteration phải cho optimizer đủ metadata để eliminate redundant checks.

---

# 269. Alias information

Mutable slice APIs cung cấp compiler đủ information về aliasing khi semantics cho phép.

---

# 270. SIMD algorithms

Standard numeric/byte algorithms có thể sử dụng SIMD automatically.

---

# 271. CPU fallback

SIMD implementation luôn phải có baseline fallback khi target không hỗ trợ extension.

---

# 272. Constant evaluation

Các API pure phù hợp có thể được đánh dấu `const`.

---

# 273. Const formatting

Chỉ compile-time-safe subset.

---

# 274. Compile-time parsing

Simple numeric/string parsers có thể chạy trong const evaluation.

---

# 275. Compile-time collections

Fixed arrays/tuples hỗ trợ const construction.

---

# 276. Runtime-only APIs

I/O, random secure, process/environment mutation không được const-evaluate.

---

# 277. Standard library and compiler

Compiler phải recognize một số intrinsic operations nhưng không được hard-code toàn bộ standard library.

---

# 278. Compiler/library boundary

```text
AXCOMPILER
 ├── language intrinsics
 └── generic optimization
        ↓
AXSTANDARD
 └── ordinary Axiom code
```

---

# 279. Standard library and AXABI

Internal generic calls sử dụng AXABI native convention.

---

# 280. Standard library and AXRUNTIME

Runtime dependencies phải explicit.

---

# 281. Standard library and AXMEMORY

Allocation operations delegate tới AXMEMORY/AXRUNTIME allocator.

---

# 282. Standard library and AXTIME

Time facade delegates to AXTIME.

---

# 283. Standard library and AXRANDOM

Random facade delegates to AXRANDOM.

---

# 284. Standard library and AXSTORAGE

Path/File adapters delegate storage operations.

---

# 285. Standard library and AXNETWORK

Socket/URL abstractions không thuộc core AXSTANDARD.

---

# 286. Standard library and AXCRYPTO

Không implement crypto primitives duplicate trong standard core.

---

# 287. Standard library and AXDIAGNOSTICS

Error/panic metadata có thể feed diagnostics.

---

# 288. Standard library and AXLOGGING

Formatting can feed logger nhưng không phụ thuộc logger.

---

# 289. Standard library and AXTASK

Parallel algorithms/channel async adapters có thể optional.

---

# 290. Standard library and security

Environment/path/file APIs không tự bypass AXSECURITY.

---

# 291. Standard library security

Input parsing phải validate lengths/overflow.

---

# 292. Resource exhaustion

Collection reserve với absurd size phải fail deterministic.

---

# 293. Integer overflow

Capacity calculations phải checked trước allocation.

---

# 294. Length multiplication

Ví dụ:

```text
count * sizeof(T)
```

phải check overflow trước allocation.

---

# 295. Alignment validation

Custom allocation requests phải validate power-of-two/target rules.

---

# 296. Lifetime safety

Standard collection references phải invalidation semantics rõ ràng.

---

# 297. Thread safety

Collections mặc định **không synchronized**.

Điều này tránh hidden locks.

---

# 298. Explicit synchronization

User chọn:

```text
Mutex<Vec<T>>
ConcurrentMap<K,V>
```

khi cần.

---

# 299. Formal invariants

```text
STD-INV-01
AXSTANDARD không được yêu cầu GC.

STD-INV-02
AXSTANDARD không được yêu cầu implicit reference counting.

STD-INV-03
AXSTANDARD không được tạo OS thread cho operation thông thường.

STD-INV-04
AXSTANDARD không được là mandatory monolithic runtime.

STD-INV-05
Unused standard modules phải có khả năng bị loại khỏi binary.

STD-INV-06
String và Str phải bảo toàn UTF-8 invariant.

STD-INV-07
Bytes phải có khả năng biểu diễn arbitrary byte sequences.

STD-INV-08
UTF-8 validation phải reject invalid sequences.

STD-INV-09
String byte slicing phải không tạo invalid String/Str.

STD-INV-10
String indexing không được giả định O(1) Unicode character indexing.

STD-INV-11
Option không được yêu cầu heap allocation.

STD-INV-12
Result không được yêu cầu heap allocation.

STD-INV-13
Error propagation không được mặc định sử dụng exception.

STD-INV-14
Generic standard APIs phải ưu tiên static dispatch.

STD-INV-15
Iterator chains không được yêu cầu heap allocation.

STD-INV-16
Collection allocation phải có explicit semantics.

STD-INV-17
Collection capacity calculations phải kiểm tra overflow.

STD-INV-18
Safe indexing phải có defined failure semantics.

STD-INV-19
Unsafe indexing phải explicit unsafe.

STD-INV-20
Move của owned standard containers không được copy toàn bộ storage.

STD-INV-21
Clone phải explicit.

STD-INV-22
Standard collections mặc định không tự động synchronized.

STD-INV-23
HashMap iteration order không được mặc định là stable ABI/API contract.

STD-INV-24
Ordered collections phải cung cấp explicit ordering semantics.

STD-INV-25
Raw object memory không được mặc định là serialization format.

STD-INV-26
Numeric narrowing phải explicit hoặc checked.

STD-INV-27
Checked/wrapping/saturating arithmetic phải có semantics phân biệt.

STD-INV-28
Core formatting APIs phải có allocation-controlled variants.

STD-INV-29
Primitive parsing phải không yêu cầu allocation.

STD-INV-30
Standard library không được phụ thuộc libc cho core functionality.

STD-INV-31
Platform-specific functionality phải nằm sau explicit platform abstraction.

STD-INV-32
Filesystem/network/crypto/database functionality không được kéo vào core standard library.

STD-INV-33
Standard library không được tự grant security capabilities.

STD-INV-34
External input phải được xử lý với overflow/resource-limit validation.

STD-INV-35
Standard API ownership/lifetime semantics phải deterministic.

STD-INV-36
Standard API metadata phải có thể mô tả allocation/blocking/panic/ownership khi cần.

STD-INV-37
Standard library phải hỗ trợ no-heap/no-libc core subset khi target cho phép.

STD-INV-38
Standard library phải có cross-target conformance tests.

STD-INV-39
Standard library implementation phải ưu tiên zero-cost abstraction và compiler optimization.

STD-INV-40
AXSTANDARD là library layer; không được hấp thụ ownership của AXRUNTIME, AXMEMORY hoặc các subsystem chuyên biệt.
```

---

# 300. Definition of Done

`AXSTANDARD 5.0` được freeze khi có:

### Core types

- `Option`
- `Result`
- `Error`
- conversions
- comparisons
- hashing
- ownership helpers

### Text/data

- UTF-8
- String
- Str
- Bytes
- slices
- formatting
- parsing

### Collections

- Vec
- fixed arrays
- slices
- deque
- hash map
- hash set
- ordered map/set
- collection iterators

### Algorithms

- sort
- search
- copy
- fill
- partition
- numeric algorithms

### Numeric

- checked arithmetic
- wrapping arithmetic
- saturating arithmetic
- bit operations
- math
- floating-point utilities

### Concurrency utilities

- synchronization wrappers
- channels
- once/lazy primitives

nhưng không tạo scheduler riêng.

### Platform facades

- Path
- environment
- Reader/Writer
- time facade
- random facade

### Compiler integration

- const evaluation;
- intrinsics;
- iterator optimization;
- bounds-check elimination;
- SIMD;
- monomorphization;
- dead-code elimination;
- LTO.

### Performance

- no hidden GC;
- no implicit RC;
- no mandatory allocation;
- no mandatory threads;
- modular linking;
- zero-copy views;
- allocation-controlled APIs.

### Validation

- unit tests;
- property tests;
- fuzzing;
- cross-platform tests;
- no-libc tests;
- freestanding tests;
- ABI tests;
- size regression;
- performance regression.

**AXSTANDARD 5.0 → FROZEN.**

---

# Chuỗi kiến trúc hiện tại

```text
AXCOMPILER
    ↓
AXABI
    ↓
AXOBJECT
    ↓
AXLINKER
    ↓
AXBINARY
    ↓
AXLOADER
    ↓
AXSTARTUP
    ↓
AXRUNTIME
    ↓
AXSTANDARD
    ↓
APPLICATION
```

Đây là một ranh giới rất quan trọng: **AXRUNTIME cung cấp cơ chế chạy chương trình; AXSTANDARD cung cấp công cụ lập trình hằng ngày.** Vì vậy một chương trình Axiom tối thiểu không phải kéo theo String/HashMap/Formatting/Math nếu nó không dùng chúng.

---

# BOOTSTRAP-782 — AXTEST

**Native Axiom Testing, Unit/Integration/System/Compiler/ABI/Runtime Testing, Property Testing, Fuzzing, Golden Tests, Differential Testing, Deterministic Replay, Cross-Target Conformance, Performance Regression & Self-Hosting Verification 5.0**

Bước tiếp theo là xây **AXTEST**. Đây không chỉ là test framework thông thường; với Axiom, nó phải trở thành **conformance infrastructure** để kiểm chứng compiler → ABI → object → linker → binary → loader → startup → runtime → standard library trên tất cả target.