# BOOTSTRAP-349 — AXIOM DATA, COLLECTIONS, TEXT & ZERO-COPY BUFFER ENGINE

Sau `348 — Native Memory, Allocator & Resource Management`, bước tiếp theo hợp lý là xây dựng **data layer thực sự của Axiom**.

Đây là lớp mà gần như mọi chương trình đều sử dụng:

```text
String
Bytes
Buffer
Array
Slice/View
Vec
Map
Set
Queue
Deque
RingBuffer
Iterator
```

Mục tiêu của task này là tránh tình trạng Axiom có memory model rất mạnh nhưng Standard Library lại buộc programmer phải:

- copy dữ liệu liên tục,
- dùng allocation không cần thiết,
- chuyển đổi `String → bytes → String`,
- tạo object wrapper,
- dùng GC-like container,
- hoặc mất kiểm soát layout.

Nguyên tắc chính:

> **Data abstraction phải có semantic rõ ràng nhưng compiler có thể xóa abstraction và đưa về contiguous memory, registers, SIMD hoặc zero-copy view khi có thể.**

---

# 1. Kiến trúc data layer

Axiom nên chia thành:

```text
Primitive Data
      │
      ├── Array<T,N>
      ├── Bytes
      ├── Text
      └── Scalar
             │
             ▼
       View / Buffer Layer
             │
      ┌──────┼──────┐
      │      │      │
    view   Buffer  mut_view
      │      │      │
      └──────┼──────┘
             ▼
       Collections
             │
    ┌────────┼─────────┐
    │        │         │
   Vec      Map       Set
    │
 Queue / Deque / Ring
             │
             ▼
      Algorithms / Iterators
```

---

# 2. Phân biệt Bytes và Text

Đây là invariant rất quan trọng.

Không được có:

```text
String == bytes
```

Axiom phải có:

```text
Bytes
Text
```

khác nhau về semantic.

### `Bytes`

Là dữ liệu nhị phân:

```text
Bytes
view<u8>
mut_view<u8>
```

Có thể chứa bất kỳ byte nào.

### `Text`

Là Unicode text hợp lệ theo contract của Axiom.

Không được coi:

```text
Text
```

là một chuỗi byte tùy ý.

---

# 3. UTF-8 mặc định

Axiom dùng:

```text
Text = valid UTF-8
```

nhưng representation không nhất thiết bị cố định.

Có thể:

```text
inline
stack
heap
arena
static
```

Compiler/library chịu trách nhiệm representation.

---

# 4. Text không được expose byte indexing

Không cho:

```text
text[3]
```

trả về một ký tự Unicode theo nghĩa đơn giản, vì:

```text
UTF-8 byte index != character index
```

Thay vào đó:

```text
text.byte_at(...)
text.codepoint_at(...)
text.grapheme_at(...)
```

và mỗi operation có complexity được mô tả rõ.

---

# 5. Không gọi Unicode code point là "character"

Axiom cần phân biệt:

```text
Byte
CodePoint
Grapheme
Text
```

Ví dụ một glyph hiển thị có thể gồm nhiều code point.

Vì vậy:

```text
Text.length()
```

phải xác định rõ là:

```text
byte length
code point count
grapheme count
```

Không nên có một `length()` mơ hồ.

Có thể:

```text
text.byte_len()
text.codepoint_count()
text.grapheme_count()
```

---

# 6. Unicode validation

Khi tạo Text từ bytes:

```text
Text.from_utf8(bytes)
```

trả:

```text
Result<Text, Utf8Error>
```

Không được silently sửa dữ liệu.

Nếu programmer biết dữ liệu hợp lệ:

```text
unsafe Text.from_utf8_unchecked(bytes)
```

nhưng sau đó Axiom xem invariant:

```text
Text => valid UTF-8
```

là đã được establish.

---

# 7. Text literal

Literal:

```text
let name = "Hưng"
```

có semantic:

```text
TextLiteral
```

Compiler có thể lưu trực tiếp trong:

```text
.rodata
```

và không allocation.

Nếu immutable:

```text
static text
```

có thể được zero-copy sử dụng.

---

# 8. String và Text

Nên tránh tên `String` mang quá nhiều semantics.

Đề xuất:

```text
Text
MutableText
```

hoặc:

```text
String
TextView
```

Trong đó semantic rõ nhất:

```text
Text
```

= owning Unicode text.

```text
view<u8>
```

= byte view.

```text
view<CodePoint>
```

= codepoint view nếu library cung cấp.

---

# 9. TextView không copy

Ví dụ:

```text
let line = text.slice(start, end)
```

không nên mặc định tạo allocation.

Nó tạo:

```text
view<...>
```

hoặc một semantic text slice.

Compiler đảm bảo:

```text
Text owner
    │
    └── TextView
```

View không thể sống lâu hơn owner.

---

# 10. Mutable Text

Mutable text phải tách:

```text
Text
MutableText
```

Không cho:

```text
view<Text>
```

tự động mutable.

Mutable access phải tuân thủ:

```text
mut_view
```

và alias rules hiện tại.

---

# 11. Bytes

`Bytes` là owning binary container.

Semantic:

```text
Bytes
```

có:

```text
len
capacity
storage
```

và:

```text
Bytes.view()
Bytes.view_mut()
```

trả capability tương ứng.

---

# 12. Buffer

`Buffer<T>` là abstraction thấp hơn `Vec<T>`.

```text
Buffer<T>
```

mô tả:

```text
contiguous storage
capacity
alignment
initialized region
```

Có thể hỗ trợ:

```text
Buffer<u8>
Buffer<T>
```

cho systems programming.

---

# 13. Initialized Length và Capacity

Phải phân biệt:

```text
capacity
allocated size
initialized length
```

Ví dụ:

```text
Buffer<u8>:
    capacity = 4096
    length = 128
```

128 byte đầu là initialized.

Phần còn lại:

```text
UNINIT
```

Không được đọc.

---

# 14. Reserve không initialize

```text
buffer.reserve(4096)
```

chỉ đảm bảo storage capacity.

Không được biến:

```text
UNINIT
```

thành:

```text
INIT
```

Đây là điều rất quan trọng cho performance.

---

# 15. Uninitialized Fill

API thấp cấp có thể:

```text
buffer.reserve_uninit(4096)
```

trả:

```text
mut_view<MaybeUninit<u8>>
```

Sau khi OS/FFI ghi dữ liệu:

```text
buffer.assume_initialized(n)
```

chỉ safe nếu contract chứng minh bytes đã được ghi.

---

# 16. Read Directly Into Buffer

Thay vì:

```text
read()
→ temporary Bytes
→ copy
→ Buffer
```

Axiom nên cho:

```text
file.read_into(buffer.uninit_view())
```

hoặc:

```text
socket.receive_into(buffer)
```

Pipeline:

```text
OS
 ↓
Buffer storage
```

không có intermediate copy.

---

# 17. Zero-Copy Principle

Standard library phải ưu tiên:

```text
view
mut_view
Buffer
slice
move
```

thay vì:

```text
copy
clone
temporary allocation
```

khi semantics cho phép.

Ví dụ:

```text
fn parse(packet: view<u8>)
```

không cần:

```text
Bytes(packet)
```

---

# 18. Ownership Transfer

Nếu API cần ownership:

```text
fn consume(data: Bytes)
```

thì:

```text
consume(buffer)
```

move storage.

Không copy.

Nếu API chỉ đọc:

```text
fn parse(data: view<u8>)
```

thì không ownership transfer.

---

# 19. Vec

`Vec<T>` là dynamic contiguous collection:

```text
Vec<T> {
    ptr/storage
    len
    capacity
}
```

nhưng representation không phải ABI contract.

Compiler có thể optimize.

---

# 20. Vec Growth

Growth policy không phải language semantic.

Library có thể:

```text
grow ~1.5x
grow ~2x
exact
custom
```

Nhưng phải có API:

```text
reserve
reserve_exact
shrink_to_fit
```

nếu cần.

---

# 21. Relocation và View

Nếu:

```text
let v = vec.view()
```

đang tồn tại:

```text
v
```

thì:

```text
v.push(...)
```

có thể relocate storage.

Do đó verifier phải reject:

```text
mutable operation that may relocate while view is live
```

hoặc library phải có API chứng minh capacity đủ.

---

# 22. `reserve` và View

Ngay cả:

```text
reserve()
```

cũng có thể relocate.

Vì vậy:

```text
view lifetime
```

không chỉ cấm `push`.

Nó cấm mọi operation có thể invalidate storage identity.

---

# 23. StableVec

Một collection có stable element address nên là type riêng:

```text
StableVec<T>
```

hoặc:

```text
StableStorage<T>
```

Không làm `Vec<T>` chậm chỉ để đảm bảo stability.

---

# 24. Array

```text
Array<T, N>
```

là:

- fixed-size
- inline/value semantic
- contiguous
- compile-time length.

Ví dụ:

```text
let a: Array<i32, 4>
```

không allocation.

---

# 25. Slice/View

View là capability abstraction đã frozen.

Vì vậy:

```text
view<T>
mut_view<T>
```

là primitive data access layer.

Array:

```text
Array<T,N>.view()
```

Vec:

```text
Vec<T>.view()
```

Buffer:

```text
Buffer<T>.view()
```

tất cả dùng cùng semantic mechanism.

---

# 26. Iterator

Iterator không nên là object/vtable mặc định.

```text
trait Iterator {
    type Item

    fn next(self: mut_view<Self>)
        -> Option<Self::Item>
}
```

Generic iterator:

```text
for x in collection {
}
```

được monomorphize.

Không allocation.

---

# 27. Iterator Fusion

Compiler/optimizer có thể biến:

```text
collection
    .map(...)
    .filter(...)
    .map(...)
    .sum()
```

thành một loop duy nhất.

Không tạo:

```text
temporary collection
iterator object
heap allocation
```

nếu semantics cho phép.

---

# 28. Iterator không được che giấu complexity

API documentation phải thể hiện:

```text
O(1)
O(n)
allocation
```

nếu operation có chi phí đáng kể.

Ví dụ:

```text
Vec.get(i)       O(1)
Vec.push()       amortized O(1)
Vec.insert(i)    O(n)
Map.lookup()     average O(1)
```

---

# 29. Map

Axiom nên cung cấp nhiều map implementations.

Không chỉ:

```text
HashMap
```

mà:

```text
HashMap
TreeMap
OrderedMap
FlatMap
```

Tùy workload.

---

# 30. HashMap

Default:

```text
HashMap<K,V>
```

phải có:

```text
Hasher
Hash
Equality
```

Compiler specialization có thể inline:

```text
hash
compare
probe
```

không dynamic dispatch.

---

# 31. Hash Security

HashMap không nên có một hash algorithm cố định ở language semantic.

Có:

```text
FastHasher
SecureHasher
DeterministicHasher
```

Application có thể chọn.

---

# 32. Deterministic Hashing

Build/compiler tools thường cần deterministic behavior.

Có:

```text
DeterministicHasher
```

để iteration/order reproducible khi API yêu cầu.

Không nên mặc định mọi HashMap iteration order là stable.

---

# 33. FlatMap

Đối với collection nhỏ:

```text
FlatMap<K,V>
```

dùng contiguous arrays.

Có thể nhanh hơn hash tree vì locality.

Đây là abstraction rất phù hợp với mục tiêu Axiom:

> data layout là một phần performance model.

---

# 34. Set

```text
HashSet<T>
TreeSet<T>
FlatSet<T>
```

được xây trên cùng semantic contracts.

---

# 35. Queue / Deque

```text
Queue<T>
Deque<T>
```

không nên mặc định linked list.

Ưu tiên:

```text
RingBuffer
```

vì locality tốt.

---

# 36. RingBuffer

```text
RingBuffer<T,N>
```

fixed capacity:

```text
producer
    ↓
[ ][ ][ ][ ][ ]
    ↓
consumer
```

Không allocation sau initialization.

Rất hữu ích cho:

- audio
- realtime
- networking
- producer/consumer
- async runtime

---

# 37. Concurrent Ring Buffer

Không được chỉ thêm `Atomic` vào RingBuffer bình thường.

Cần các specialization:

```text
SpscRing<T>
MpscRing<T>
SpmcRing<T>
MpmcQueue<T>
```

với semantic memory ordering đã được chứng minh.

---

# 38. Struct-of-Arrays

Axiom nên có library abstraction:

```text
SoA<T>
```

hoặc:

```text
StructOfArrays<Entity>
```

Ví dụ:

```text
AoS:
[x,y,z]
[x,y,z]
[x,y,z]
```

vs:

```text
SoA:
[x,x,x]
[y,y,y]
[z,z,z]
```

rất quan trọng cho SIMD/GPU/ECS.

---

# 39. Array-of-Structs

Mặc định:

```text
Array<Particle>
```

là AoS.

Không cần language syntax mới.

Compiler không tự đổi AoS ↔ SoA nếu layout observable hoặc semantic assumptions thay đổi.

Library abstraction cho phép programmer lựa chọn rõ.

---

# 40. Packed Data

Không nên dùng:

```text
@repr(packed)
```

cho mọi data performance.

Packed có thể gây:

- misalignment
- slow access
- hardware fault

`@repr(packed)` vẫn thuộc unsafe/system.

---

# 41. SIMD Collections

Data layer nên cung cấp:

```text
Simd<T,N>
SimdArray<T,N>
```

nhưng semantics dựa trên:

```text
VectorType
```

đã được compiler backend hỗ trợ.

Không hard-code SSE/AVX/NEON vào Core.

---

# 42. Numeric Buffer

ML/GPU code thường cần:

```text
TensorBuffer<T>
MatrixBuffer<T>
```

nhưng không nên đưa Tensor vào Core.

Data layer chỉ cần hỗ trợ:

```text
contiguous
strided
aligned
device
```

để Tensor library xây bên trên.

---

# 43. Strided View

Ngoài contiguous:

```text
view<T>
```

cần library/system abstraction:

```text
StridedView<T>
```

với:

```text
base
length
stride
```

Ví dụ matrix column.

Compiler không được giả định stride = 1.

---

# 44. Multi-dimensional View

Có thể:

```text
View2D<T>
View3D<T>
```

nhưng representation nên compile-time generic:

```text
View<T, Rank>
```

nếu không làm API khó dùng.

---

# 45. Ownership của View

Mọi view phải tuân theo model hiện tại:

```text
owner
  ↓
view
```

View:

- không own storage
- không kéo dài lifetime owner
- không tự deallocate
- không tạo ownership cycle

---

# 46. Serialization

Data layer nên có:

```text
Serialize
Deserialize
```

nhưng phải phân biệt:

```text
Memory representation
```

và:

```text
Wire representation
```

Không bao giờ mặc định:

```text
serialize = memcpy
```

---

# 47. Binary Encoding

Có:

```text
BinaryReader
BinaryWriter
```

với explicit:

```text
endianness
alignment
encoding
version
```

Ví dụ:

```text
read_u32_le()
read_u32_be()
```

hoặc generic endian type.

---

# 48. Zero-Copy Deserialization

Có thể map:

```text
view<u8>
```

thành structured view nếu:

- alignment đúng
- endian đúng
- representation hợp lệ
- lifetime hợp lệ
- ABI/layout contract đúng.

Nếu không, phải decode/copy.

Không được unsafe cast tùy tiện.

---

# 49. Text Parsing

Parser API:

```text
Parser {
    input: view<u8>
}
```

hoặc:

```text
input: view<CodePoint>
```

không copy source.

Compiler/parser của chính Axiom cũng có thể sử dụng data layer này.

---

# 50. Copy Semantics

Collection APIs phải phân biệt:

```text
copy
clone
move
view
```

Ví dụ:

```text
let b = a
```

nếu `a: Vec<T>`:

```text
Move
```

không copy buffer.

Nếu:

```text
let b = a.clone()
```

thì duplicate storage.

Nếu:

```text
let b = a.view()
```

thì zero-copy read capability.

---

# 51. Copy-on-Write

Không nên đưa COW thành semantic mặc định.

Nếu cần:

```text
Cow<T>
```

là library abstraction.

Compiler không được giả định COW semantics cho mọi immutable value.

---

# 52. Small String Optimization

`Text` có thể sử dụng:

```text
SSO
```

nhưng đây là representation optimization.

Không được để programmer phụ thuộc:

```text
size_of(Text)
```

trừ khi ABI/repr contract cho phép.

---

# 53. Static Data

Literal/static data:

```text
static DATA: Text = "hello"
```

có thể nằm trong:

```text
.rodata
```

không allocation.

Compiler phải tận dụng literal pooling nếu semantics cho phép.

---

# 54. Interned Text

Compiler và runtime/library có thể cung cấp:

```text
InternedText
Symbol
Atom
```

cho:

- compiler
- parser
- ECS
- lookup
- metadata.

Nhưng intern pool ownership phải rõ ràng.

Không được biến interned strings thành memory leak mặc định.

---

# 55. Symbol

Một abstraction cực hữu ích:

```text
Symbol
```

semantic:

```text
interned immutable identifier
```

Có thể representation:

```text
u32
u64
```

nhưng ID chỉ có ý nghĩa trong một `SymbolTable`.

Không được coi Symbol là String.

---

# 56. Collection Allocator Integration

Mọi collection dynamic phải hỗ trợ:

```text
Allocator
```

nhưng default API đơn giản:

```text
Vec<T>
```

và advanced:

```text
Vec<T, A>
```

hoặc tương đương.

Ví dụ:

```text
Vec<Node, ArenaAllocator>
```

cho compiler.

---

# 57. Compiler Collections

Compiler Axiom nên ưu tiên:

```text
Arena
BumpAllocator
Vec
SmallVec
FlatMap
InternedString
Symbol
BitSet
SparseSet
```

thay vì general-purpose structures ở mọi nơi.

Điều này giúp compiler nhanh và giảm allocation.

---

# 58. Sparse Data Structures

Compiler/graph algorithms cần:

```text
BitSet
BitVector
SparseSet
IndexSet
DenseMap
```

để tránh:

```text
HashMap
```

ở mọi nơi.

---

# 59. Generational Collections

Kết hợp `348`:

```text
SlotMap
GenerationalArena
StableVec
```

cho:

```text
NodeId
TypeId
FunctionId
InstructionId
```

đã dùng trong CompilerDB.

---

# 60. Iterator + Ownership Verification

Ví dụ:

```text
for x in vec {
    vec.push(x)
}
```

phải bị reject nếu iterator giữ view/mutable capability khiến relocation hoặc mutation conflict.

Compiler hiểu iterator semantics.

Không cần programmer viết lifetime.

---

# 61. Collection Mutation During Iteration

Safe default:

```text
collection iteration
```

không cho phép mutation gây invalidation.

Các API đặc biệt:

```text
drain
retain
partition
extract
```

có semantic contract rõ ràng.

---

# 62. `retain`

```text
vec.retain(fn(x) -> bool)
```

không tạo temporary collection.

Compiler/library có thể:

```text
read
predicate
move survivors
drop removed
```

in-place.

---

# 63. `drain`

```text
vec.drain(range)
```

chuyển ownership các phần tử ra iterator.

Không copy.

Đây là ví dụ tốt cho:

```text
Move + capability
```

---

# 64. Collection Layout Contract

Mặc định:

```text
Vec<T>
HashMap<K,V>
String
```

không có stable ABI layout.

Nếu cần FFI:

```text
@repr(C)
```

hoặc explicit FFI wrapper.

---

# 65. Performance Metadata

Mỗi collection API nên có machine-readable metadata:

```text
Complexity
AllocationBehavior
InvalidationBehavior
ThreadSafety
Ordering
Stability
```

Ví dụ:

```text
Vec.push:
    complexity: amortized O(1)
    may_allocate: true
    may_relocate: true
    ordering: preserves
```

Compiler/AI tooling có thể đọc metadata.

---

# 66. Compiler Cost Model Integration

Compiler có thể dùng collection metadata để cảnh báo:

```text
AXPERF:
repeated Vec growth detected in hot loop
```

gợi ý:

```text
reserve(expected_size)
```

Không tự động thay đổi semantics.

---

# 67. Borrow/Ownership Complexity vẫn không lộ ra

Ví dụ:

```text
let name = users[i].name()
```

compiler tự biết:

```text
users
 ↓
element
 ↓
name view
```

Nếu sau đó:

```text
users.push(...)
```

và push có thể relocate:

```text
compile error
```

hoặc programmer kết thúc view trước.

Không cần:

```text
'a
'b
&'a
&'b
```

---

# 68. Data Race

Collection bình thường:

```text
Vec<T>
```

không tự nhiên trở thành thread-safe.

Muốn chia sẻ:

```text
Arc<Vec<T>>
```

và mutable concurrency phải dùng:

```text
Mutex
RwLock
Atomic
Channel
```

theo model `348` + concurrency baseline.

---

# 69. Immutable Collection

Có thể cung cấp:

```text
FrozenVec<T>
FrozenMap<K,V>
```

cho data structure immutable.

Compiler có thể chia sẻ read-only data giữa threads nếu `T: Share`.

---

# 70. Persistent Collections

Không cần Core.

Standard/Ecosystem có thể cung cấp:

```text
PersistentVector
PersistentMap
PersistentSet
```

với structural sharing.

Nhưng đây là explicit abstraction, không phải semantics mặc định.

---

# 71. Memory Locality

Collection design phải ưu tiên:

```text
contiguous
cache-friendly
prefetch-friendly
SIMD-friendly
```

khi semantics phù hợp.

Đây là lý do Axiom không nên mặc định dùng linked structures.

---

# 72. Linked Structures

Vẫn phải hỗ trợ:

```text
LinkedList
IntrusiveList
```

cho các trường hợp thật sự cần.

Nhưng intrusive structures có thể yêu cầu:

```text
unsafe/system
```

vì pointer/link invariants.

---

# 73. Intrusive Collections

Ví dụ:

```text
IntrusiveList<Node>
```

node chứa linkage.

Compiler không được tự assume node address stable.

API phải yêu cầu explicit stable storage contract.

---

# 74. Resource Collections

Có thể:

```text
Vec<File>
Vec<Socket>
```

Drop semantics:

```text
Vec destruction
 ↓
Drop each element
 ↓
release vector storage
```

Bulk destruction chỉ được bỏ qua nếu element trivial.

---

# 75. Parallel Algorithms

Data layer có thể cung cấp:

```text
parallel_map
parallel_reduce
parallel_sort
```

nhưng không thuộc Core.

Compiler/runtime có thể chọn:

```text
threads
SIMD
GPU
```

nếu API contract cho phép.

---

# 76. GPU Buffer Compatibility

Collections có thể có:

```text
DeviceVec<T>
DeviceBuffer<T>
```

với explicit storage domain.

Không implicit:

```text
Vec<T> → GPU
```

copy nếu operation yêu cầu zero-copy semantics.

---

# 77. Serialization + Device

Không cho serializer vô tình đọc device memory như host memory.

Storage domain là một phần capability.

---

# 78. CompilerDB bổ sung

```text
CollectionDB
BufferTypeDB
TextDB
EncodingDB
IteratorDB
AlgorithmDB
HashDB
LayoutContractDB
DataViewDB
StridedViewDB
SymbolDB
InternDB
SerializationDB
CollectionPerformanceDB
CollectionInvalidationDB
```

---

# 79. MIR/Optimizer Integration

Optimizer có thể nhận metadata:

```text
Contiguous
Aligned
LengthKnown
NoAlias
ReadOnly
MutableExclusive
StrideKnown
```

Ví dụ:

```text
view<f32>
```

đã chứng minh:

```text
NoAlias
```

thì vectorizer có thể dùng fact đó.

Nếu không:

```text
UNKNOWN
```

không được tự suy luận `NoAlias`.

---

# 80. Zero-Copy Optimization

Ví dụ:

```text
fn parse(data: view<u8>) -> Header
```

Compiler có thể:

```text
network buffer
      ↓
view
      ↓
parser
      ↓
Header
```

không copy.

Nếu Header representation phù hợp:

```text
load directly
```

Nếu endian/alignment không phù hợp:

```text
decode
```

Compiler không được dùng bitcast sai semantics.

---

# 81. Data-Oriented API

Axiom Standard Library nên hỗ trợ cả:

```text
Object-oriented style
```

theo nghĩa method syntax, nhưng data model vẫn:

```text
struct
array
buffer
view
```

Ví dụ:

```text
particles.position
particles.velocity
```

hoặc SoA.

Không cần class hierarchy.

---

# 82. Invariants

### `ADATA-01`
Bytes and Text are distinct semantic types.

### `ADATA-02`
Text represents valid Unicode according to its declared encoding contract.

### `ADATA-03`
UTF-8 is the default Text representation contract.

### `ADATA-04`
Byte indexing must not be confused with Unicode character indexing.

### `ADATA-05`
Code point and grapheme semantics are distinct.

### `ADATA-06`
Text slices must not outlive their source storage.

### `ADATA-07`
Buffer capacity does not imply initialized data.

### `ADATA-08`
Reserve operations do not initialize memory.

### `ADATA-09`
Uninitialized memory cannot be safely read.

### `ADATA-10`
Collection move does not imply element/storage copy.

### `ADATA-11`
Collection clone explicitly duplicates storage when required.

### `ADATA-12`
Views do not own collection storage.

### `ADATA-13`
Potentially relocating operations invalidate conflicting views.

### `ADATA-14`
Stable-address collections must have explicit stable-storage semantics.

### `ADATA-15`
Default collections do not guarantee stable physical addresses.

### `ADATA-16`
Collection layout is not stable ABI unless explicitly declared.

### `ADATA-17`
Iterators must participate in ownership/capability verification.

### `ADATA-18`
Safe iteration cannot permit invalidating mutation.

### `ADATA-19`
Iterator abstraction must not require dynamic dispatch by default.

### `ADATA-20`
Iterator chains may be fused without changing observable semantics.

### `ADATA-21`
Collection APIs must preserve specified ordering semantics.

### `ADATA-22`
Hash iteration order is not stable unless explicitly contracted.

### `ADATA-23`
Hashing strategy is independent from collection semantic identity.

### `ADATA-24`
Serialization is distinct from in-memory representation.

### `ADATA-25`
Zero-copy conversion requires representation, alignment and lifetime validity.

### `ADATA-26`
Device buffers are distinct storage domains.

### `ADATA-27`
Host collections cannot implicitly alias device storage.

### `ADATA-28`
Collection allocation behavior participates in performance/effect analysis.

### `ADATA-29`
Collection APIs must expose invalidation behavior.

### `ADATA-30`
All collection optimizations must preserve ownership, capability and observable semantics.

---

# 83. Definition of Done

`BOOTSTRAP-349` hoàn thành khi Axiom có:

```text
✓ Bytes
✓ Text
✓ UTF-8 validation
✓ CodePoint
✓ Grapheme abstraction
✓ Text views
✓ Mutable text
✓ Buffer<T>
✓ Initialized/uninitialized buffer API
✓ Zero-copy I/O integration
✓ Array<T,N>
✓ Vec<T>
✓ Stable collection model
✓ Iterator
✓ Iterator fusion
✓ HashMap
✓ TreeMap
✓ FlatMap
✓ HashSet
✓ TreeSet
✓ Queue
✓ Deque
✓ RingBuffer
✓ Concurrent ring-buffer variants
✓ BitSet
✓ SparseSet
✓ SlotMap
✓ Generational collections
✓ StridedView
✓ Multi-dimensional view
✓ SoA/AoS support
✓ SIMD data abstraction
✓ Serialization foundation
✓ Endian-aware binary IO
✓ Symbol/interning
✓ Collection allocator integration
✓ Allocation/invalidation metadata
✓ Complexity metadata
✓ Compiler optimization integration
✓ GPU buffer integration
✓ FFI-safe data adapters
✓ Conformance tests
✓ Performance benchmarks
```

---

# 84. Kết quả kiến trúc sau BOOTSTRAP-349

Lúc này Axiom có một data stack khá hoàn chỉnh:

```text
                    DATA
                     │
       ┌─────────────┼─────────────┐
       │             │             │
     VALUE         TEXT          RESOURCE
       │             │             │
   Array<T,N>       Text          File
   Struct           Bytes         Socket
   Enum             Buffer        MemoryMap
       │             │             │
       └─────────────┼─────────────┘
                     │
               view / mut_view
                     │
                     ▼
                 Buffer<T>
                     │
          ┌──────────┼──────────┐
          │          │          │
         Vec       Ring       Strided
          │
      Collections
          │
   ┌──────┼─────────┐
   │      │         │
  Map    Set      Queue
   │
 Algorithms / Iterators
          │
          ▼
    Compiler Optimizer
          │
   ┌──────┼─────────┐
   │      │         │
 SIMD   CPU       GPU
```

Điểm quan trọng nhất của task này là Axiom bắt đầu có một **data model thống nhất từ byte-level tới high-level collection**, nhưng không ép programmer phải trả chi phí abstraction.

Ví dụ cùng một dữ liệu có thể đi:

```text
Socket
  ↓
uninitialized Buffer
  ↓
view<u8>
  ↓
parser
  ↓
struct
```

mà không cần:

```text
Socket buffer
→ temporary String
→ temporary Array
→ deserialize
→ copy
→ application object
```

nếu representation và semantics cho phép.

Đây là nền tảng cần thiết trước khi Axiom xây tiếp các lớp lớn hơn như **I/O framework, serialization, networking, filesystem, GUI, application framework và các thư viện cấp cao**, bởi tất cả chúng đều sẽ dựa trực tiếp vào data/ownership/zero-copy model này.