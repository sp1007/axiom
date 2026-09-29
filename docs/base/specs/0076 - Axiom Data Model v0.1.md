Tiếp tục. Phần này tôi muốn đi sâu vào **Data Model & Collections**, vì đây là nơi quyết định Axiom có thực sự “nhẹ như C nhưng tiện hơn C” hay cuối cùng lại biến thành một ngôn ngữ có runtime/object model nặng.

# Axiom Data Model v0.1

Nguyên tắc trung tâm:

> **Không có một kiểu dữ liệu “mọi thứ đều là object”.**

Axiom nên có nhiều abstraction mạnh, nhưng mỗi abstraction phải có semantics và cost rõ ràng.

```text
Value
├── Scalar
├── Struct
├── Tuple
├── Array
├── Enum
├── Union
├── Function
└── Closure

Storage / ownership
├── Box<T>
├── Vec<T>
├── Arena
├── Pool
└── custom storage

Capability
├── view<T>
└── mut_view<T>

Dynamic abstraction
└── dyn Trait
```

Không có:

```text
Object
Any
Variant
DynamicObject
```

làm nền tảng bắt buộc cho mọi giá trị.

---

# 1. Universal Object: không nên có

Ví dụ kiểu:

```text
Object {
    type_id
    size
    flags
    vtable
    refcount
    ...
}
```

rồi mọi thứ đều:

```text
Object*
```

sẽ gây rất nhiều vấn đề:

- object header;
- pointer indirection;
- allocation;
- cache miss;
- runtime type information;
- GC/RC pressure;
- ABI phức tạp;
- binary lớn;
- optimizer khó scalarize;
- embedded/freestanding khó dùng.

Điều này trái với mục tiêu Axiom.

---

# 2. Type information không phải runtime mặc định

Ví dụ:

```axiom
struct User {
    id: u64
    age: u32
}
```

binary không cần chứa:

```text
User.type_id
User.size
User.vtable
```

Compiler đã biết tất cả.

Nếu cần runtime type information:

```text
TypeInfo<T>
```

thì đó là **explicit capability/library feature**.

---

# 3. Struct

Struct là data aggregate cơ bản nhất.

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

Semantics:

```text
Vec2
 ├── x
 └── y
```

Không có:

```text
this pointer
object header
virtual table
hidden monitor
GC metadata
```

---

# 4. Struct layout mặc định

Compiler được phép:

```text
reorder fields
insert padding
scalarize fields
split fields
register-promote fields
```

miễn semantics không quan sát được layout.

Ví dụ:

```axiom
struct S {
    a: u8
    b: u64
    c: u8
}
```

không nhất thiết phải:

```text
a bbbbbbbb c
```

theo source order.

---

# 5. Khi nào layout trở thành observable?

Khi programmer yêu cầu:

```axiom
@repr(C)
struct Header {
    ...
}
```

hoặc:

```text
@repr(transparent)
@align(...)
@repr(packed)
```

hoặc dùng FFI/storage API yêu cầu layout.

Khi đó compiler phải tuân thủ contract.

---

# 6. Array

Array:

```axiom
let a: [i32; 4] = [1, 2, 3, 4];
```

là:

```text
4 × sizeof(i32)
```

liên tục và inline.

Không có header.

Không có allocation.

Không có length runtime bắt buộc.

---

# 7. Array length là compile-time information

```text
[i32; 4]
[i32; 8]
```

là hai type khác nhau.

Điều này rất hữu ích cho:

- embedded;
- SIMD;
- matrix;
- stack buffers;
- compile-time optimization.

---

# 8. Nhưng array không nên mang quá nhiều type-level machinery

Ta không cần:

```text
Array<T, N>
```

với một hệ dependent type phức tạp.

`N` chỉ là compile-time constant.

---

# 9. View

Đây là abstraction quan trọng nhất của Axiom collections.

```text
view<T>
```

là:

```text
read-only contiguous capability
```

conceptually:

```text
(pointer, length)
```

nhưng semantic model là:

```text
provenance
region
access=READ
length
```

---

# 10. `mut_view`

```text
mut_view<T>
```

là:

```text
(pointer, length)
+
exclusive WRITE capability
```

Không cho hai `mut_view` overlapping cùng vùng.

---

# 11. View không sở hữu dữ liệu

Ví dụ:

```axiom
fn sum(xs: view<i32>) -> i32
```

Không có allocation.

Không có copy cả array.

Không có reference-count.

Không có lifetime object runtime.

Compiler theo dõi lifetime/capability **ở compile time**.

---

# 12. Vec

`Vec<T>` là dynamic contiguous owner.

Conceptually:

```text
Vec<T>
├── storage identity
├── length
└── capacity
```

Implementation thường:

```text
pointer
length
capacity
```

nhưng đó không phải semantic ABI bắt buộc.

---

# 13. Vec không phải object

Ví dụ:

```axiom
let v = Vec<i32>();
```

không có:

```text
v → Object
```

mà là một owned value.

Compiler có thể giữ nó:

```text
register
stack
heap metadata
```

tùy situation.

---

# 14. Vec relocation

Đây là điểm quan trọng.

```axiom
let v = Vec<i32>();
```

sau:

```axiom
v.push(10);
```

storage **có thể relocate**.

Do đó:

```axiom
let x = view(v);
v.push(10); // potentially relocating
```

không được phép nếu `x` vẫn active và relocation có thể làm invalid view.

---

# 15. `reserve` không tạo stable address

Ví dụ:

```axiom
v.reserve(1000);
```

không nên có semantics:

> “địa chỉ của vĩnh viễn không đổi.”

Nó chỉ tạo capacity guarantee.

Compiler/library vẫn có thể relocate nếu semantic contract cho phép.

Nếu cần stable address:

```text
Box
stable storage
arena
pinned storage
```

phải explicit.

---

# 16. Đây là một khác biệt quan trọng với C++

C++ programmer thường phải suy nghĩ:

```text
vector reallocation?
iterator invalidation?
reference invalidation?
```

Axiom cố gắng chuyển phần lớn việc này thành:

```text
compiler detects dependency
```

Ví dụ:

```axiom
let item = view(v[0]);
v.push(1);
```

Compiler:

```text
active capability
      ↓
push MAY_RELOCATE
      ↓
potential conflict
      ↓
compile error
```

Programmer không cần nhớ từng API invalidation rule bằng tay nếu API contract được compiler hiểu.

---

# 17. Nhưng library contracts phải có semantic effects

Ví dụ `Vec.push` cần compiler biết:

```text
MAY_RELOCATE
WRITE
ALLOC
```

Không nhất thiết expose syntax annotation cho programmer.

Compiler IR có thể có:

```text
OperationEffect {
    memory: ...
    relocation: MAY_RELOCATE
}
```

---

# 18. Collection operation classes

Tôi đề xuất compiler/library contract có những semantic flags như:

```text
READ_ONLY
WRITE_IN_PLACE
MAY_RELOCATE
NO_RELOCATE
ALLOCATE
DEALLOCATE
INVALIDATE_VIEW
```

Những thứ này là **compiler metadata**, không phải runtime metadata.

---

# 19. String

Không nên có một `String` kiểu C:

```text
char*
```

vì Unicode hiện đại.

Tôi đề xuất:

```text
Bytes
Text
```

là hai abstraction khác nhau.

---

# 20. Bytes

```text
Bytes
```

là raw byte sequence.

Không có assumption:

```text
UTF-8
UTF-16
ASCII
```

Ví dụ:

```axiom
let data: view<u8>
```

đủ cho nhiều low-level APIs.

---

# 21. Text

```text
Text
```

có semantic invariant:

> dữ liệu biểu diễn một chuỗi Unicode hợp lệ.

Implementation có thể dùng UTF-8, nhưng **semantic model không phụ thuộc representation**.

---

# 22. Không cho implicit Bytes → Text

```axiom
let data: Bytes = ...
let text: Text = data;
```

→ lỗi.

Phải:

```axiom
Text.from_utf8(data)
```

và có thể trả:

```text
Result<Text, Utf8Error>
```

---

# 23. Vì sao không cho implicit?

Nếu:

```text
Bytes → Text
```

tự động:

- có thể fail;
- có thể validate;
- có thể allocate;
- có thể normalize.

Đây là conversion có semantics thực sự.

Không nên giấu sau assignment.

---

# 24. Text indexing

Tôi đề xuất **không có**:

```axiom
text[i]
```

với semantics “ký tự Unicode thứ i”.

Vì Unicode code point không phải fixed-width.

Thay vào đó:

```text
text.bytes()
text.chars()
text.graphemes()
```

---

# 25. Vì sao không bắt Text indexing O(1)?

Nếu:

```text
text[i]
```

có nghĩa:

> Unicode character thứ `i`

thì UTF-8 phải scan hoặc có index structure.

Axiom không nên hứa O(1) nếu representation không đảm bảo.

---

# 26. `chars()`

Có thể trả iterator:

```text
Iterator<Item = char>
```

nhưng `char` nên được định nghĩa rõ.

Tôi đề xuất:

```text
char = Unicode scalar value
```

không phải grapheme cluster.

Grapheme là library-level abstraction.

---

# 27. Option

```axiom
enum Option<T> {
    None
    Some(T)
}
```

Không phải object.

Compiler có thể optimize:

```text
Option<Box<T>>
```

thành pointer + niche.

---

# 28. Result

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

cũng là ordinary enum.

Không có exception runtime.

---

# 29. Compiler-known ADT nhưng vẫn ordinary type

Compiler có thể special-case:

```text
Option
Result
```

cho optimization/control flow.

Nhưng semantics vẫn:

```text
ordinary enum
```

Điều này giữ language model đơn giản.

---

# 30. Enum

Ví dụ:

```axiom
enum Shape {
    Circle(f32)
    Rect { w: f32, h: f32 }
    Point
}
```

Compiler quyết định:

```text
tag
payload
padding
niche
```

layout.

---

# 31. Enum không nhất thiết có explicit tag runtime

Nếu:

```text
Option<Box<T>>
```

compiler có thể dùng:

```text
null/non-null
```

làm niche.

Nếu:

```text
enum Boolish {
    False
    True
}
```

có thể chỉ cần một byte hoặc thậm chí bit/register representation phù hợp.

---

# 32. Nhưng semantic enum vẫn tagged

Programmer không được dựa vào:

```text
tag nằm byte thứ 0
```

trừ khi representation explicit.

---

# 33. Union

Union vẫn giữ trong Axiom nhưng là **system-level overlapping storage**.

```axiom
union U {
    i: i32
    f: f32
}
```

Không có runtime tag.

---

# 34. Union không nên chứa arbitrary Drop resources

Không:

```axiom
union Bad {
    file: File
    socket: Socket
}
```

trong safe Core nếu compiler không có active-member semantics đủ mạnh.

Tôi đề xuất union v0.1 giới hạn:

```text
Copy / trivially manageable representation
```

---

# 35. Nếu cần variant resource-managed

Dùng:

```axiom
enum Resource {
    File(File)
    Socket(Socket)
}
```

Enum có ownership semantics.

Union dành cho:

- FFI;
- hardware;
- bit-level representation;
- tagged-by-external-protocol data.

---

# 36. Bitset

Không cần tạo Core primitive:

```text
BitSet<T>
```

có thể là library.

Ví dụ:

```text
BitSet<u64, N>
```

compiler tối ưu nếu inline/generic.

---

# 37. SIMD vector

Tôi muốn phân biệt:

```text
Vector<T, N>
```

với:

```text
CPU register
```

Ví dụ:

```axiom
let v: Vector<f32, 4>;
```

semantic là 4-lane vector.

Compiler quyết định:

```text
XMM
YMM
ZMM
NEON
SVE
scalar
```

---

# 38. Đây là abstraction rất đáng giá

Programmer có thể viết:

```axiom
a = a + b;
```

trên:

```text
Vector<f32, 8>
```

Compiler chọn:

```text
AVX2
```

trên CPU hỗ trợ.

Nếu target không hỗ trợ:

```text
scalarization
```

hoặc target-specific implementation.

---

# 39. Nhưng SIMD width cần target constraints

Nếu code yêu cầu:

```text
Vector<f32, 16>
```

không nhất thiết machine instruction có register 16 lanes.

Compiler có thể lower thành:

```text
2 × AVX2
```

hoặc:

```text
4 × SSE
```

nếu semantic cho phép.

---

# 40. Matrix

Không cần Core `Matrix`.

Library có thể:

```text
Matrix<T, Rows, Cols>
```

dựa trên:

```text
Array<T, Rows * Cols>
```

hoặc storage khác.

Đây chính là sức mạnh của generic + const generic.

---

# 41. Map / Set

Đây là standard library, không Core.

Ví dụ:

```text
HashMap<K,V>
HashSet<T>
TreeMap<K,V>
```

Không có một universal `Map`.

---

# 42. Tại sao không universal Map?

Vì:

```text
HashMap
TreeMap
BTree
FlatMap
SparseMap
ArenaMap
```

có cost model rất khác.

Axiom nên để library chọn implementation.

---

# 43. Deque

```text
Deque<T>
```

library.

Không cần Core semantic knowledge ngoài generic/value/ownership.

---

# 44. Linked List

Cũng library.

Thậm chí không nên coi là primitive collection quan trọng.

Linked list thường có:

```text
pointer chasing
allocation
cache miss
```

nên Axiom không cần ưu tiên nó trong Core.

---

# 45. Iterator

Iterator là trait:

```axiom
trait Iterator {
    type Item;

    fn next(self: mut_view<Self>)
        -> Option<Self.Item>;
}
```

Compiler không cần runtime iterator object.

---

# 46. Iterator adapter

Ví dụ:

```axiom
xs
    .map(...)
    .filter(...)
    .take(...)
```

có thể tạo nested generic types.

Nhưng:

```text
source
 ↓
generic specialization
 ↓
inline
 ↓
loop
```

và cuối cùng machine code có thể giống hand-written loop.

---

# 47. Đây là nơi Abstraction Erasure phát huy

Source:

```text
map
filter
take
```

Machine:

```text
load
compare
branch
store
```

Không có:

```text
iterator object
virtual call
heap allocation
```

nếu không cần.

---

# 48. Nhưng đừng đưa toàn bộ iterator algebra vào compiler Core

Compiler chỉ cần hiểu:

```text
for
Iterator.next
```

còn:

```text
map
filter
enumerate
zip
scan
fold
```

là library.

---

# 49. Range

Range có thể là lightweight value:

```text
0..10
0..=10
```

Compiler nhận diện trong `for` và lower trực tiếp.

Ví dụ:

```axiom
for i in 0..n {
    sum += i;
}
```

có thể thành:

```text
i = 0
loop:
    if i >= n goto end
    ...
    i++
```

---

# 50. Không tạo Range heap object

Range nên là:

```text
start
end
step
```

hoặc thậm chí scalarized hoàn toàn.

---

# 51. Slice vs View

Tôi sẽ **không tạo một `Slice<T>` thứ ba** nếu:

```text
view<T>
mut_view<T>
```

đã đủ.

Có thể dùng:

```text
view<T>
```

cho contiguous readonly slice.

Điều này giảm số lượng abstraction.

---

# 52. Nhưng cần `view2D`?

Không nên nhét mọi thứ vào `view<T>`.

2D matrix có:

```text
pointer
rows
cols
stride
```

khác contiguous 1D view.

Có thể library định nghĩa:

```text
MatrixView<T>
```

hoặc:

```text
view2<T>
```

với compiler không cần hiểu nó.

---

# 53. Điều này cho thấy một nguyên tắc

> **Compiler cần hiểu semantic safety primitives, không cần hiểu domain data structures.**

Compiler cần biết:

```text
view
mut_view
ownership
move
Drop
```

Nhưng không cần biết:

```text
Matrix
Image
Tensor
Mesh
HashMap
Database
HTTP
```

---

# 54. Universal container cũng không cần

Nếu muốn heterogeneous collection:

```text
Vec<dyn Trait>
```

hoặc explicit enum:

```text
enum Value {
    Int(i64)
    Float(f64)
    Text(Text)
    ...
}
```

Programmer chọn semantics.

Không có:

```text
Vec<Object>
```

mặc định.

---

# 55. Dynamic heterogeneous data

Ví dụ JSON:

```text
JsonValue
├── Null
├── Bool
├── Number
├── String
├── Array
└── Object
```

đây là **library data model**, không phải language universal object.

Điều này cực kỳ quan trọng.

---

# 56. Serialization

Compiler không cần biết JSON.

Library:

```text
trait Serialize
trait Deserialize
```

generic/static dispatch nếu có thể.

Dynamic serializers có thể dùng `dyn Trait`.

---

# 57. `Any`

Axiom không có `Any` built-in.

Nếu library cần:

```text
DynamicValue
TypeId
TypeInfo
```

thì xây explicit.

Ví dụ plugin system có thể dùng:

```text
TypeId
dyn Any
```

nhưng đó là runtime feature được lựa chọn.

---

# 58. Runtime reflection

Không mặc định.

Source:

```axiom
struct User {
    id: u64
}
```

không tự động sinh metadata.

Nếu:

```text
derive(Reflect)
```

hoặc tương đương compile-time mechanism:

```text
generate TypeInfo<User>
```

thì metadata chỉ tồn tại khi sử dụng.

---

# 59. Đây là một nguyên tắc rất mạnh

```text
No use
   ↓
No generated metadata
   ↓
No binary cost
```

Một lần nữa:

> **Abstraction Erasure.**

---

# 60. Collection hierarchy đề xuất

Tôi nghĩ Standard Library nên có:

```text
                    Collection
                       │
        ┌──────────────┼───────────────┐
        │              │               │
    Contiguous      Sequence        Associative
        │              │               │
   ┌────┴────┐      ┌───┴────┐     ┌───┴─────┐
 Array      Vec    Deque   List   Map       Set
   │
 view<T>
 mut_view<T>
```

Nhưng đây là **library traits**, không phải class inheritance.

---

# 61. Có nên có `Collection` trait?

Có thể, nhưng không nên biến nó thành giant trait:

```text
Collection:
    size
    insert
    remove
    reserve
    iterator
    index
    ...
```

Tôi thích các capability nhỏ:

```text
Iterable
Contiguous
Resizable
Indexable
Mutable
```

vì generic constraint sẽ minimal hơn.

---

# 62. Ví dụ

Hàm chỉ cần đọc:

```axiom
fn sum<C: Iterable>(x: view<C>) ...
```

không nên yêu cầu:

```text
C: Collection + Sized + Indexable + Resizable + ...
```

nếu không cần.

---

# 63. Một vấn đề cần tránh

Nếu tạo quá nhiều micro-traits:

```text
Readable
Writable
Iterable
IterableMut
Indexable
IndexableMut
Resizable
Contiguous
CapacityAware
...
```

trait solver cũng trở nên khó chịu.

Do đó standard library cần **một bộ capability trait nhỏ**, không phải hàng trăm trait vụn.

---

# 64. Tôi đề xuất Core data types chính thức

Core:

```text
bool

i8 i16 i32 i64
u8 u16 u32 u64
isize usize

f32 f64

unit
never

tuple
array
struct
enum
union

function
closure

view<T>
mut_view<T>
```

Compiler semantic primitives:

```text
Option<T>
Result<T,E>
Copy
Drop
Send
Share
Sized
```

---

# 65. Core Library

```text
Array utilities
Option
Result
Range
Iterator base trait
basic numeric traits
basic comparison
basic conversion
basic atomics
```

---

# 66. Standard Library

```text
Vec
String/Text
Bytes
HashMap
HashSet
Deque
File
Socket
Thread
Channel
Arc
Mutex
RwLock
Async runtime
Future
Time
Random
Path
Process
```

---

# 67. Platform/Ecosystem

```text
HTTP
TLS
JSON
Database
GUI
GPU
Audio
Video
Image
ML
Tensor
Game
OpenGL/Vulkan/Metal/DirectX
```

Không để những thứ này làm phình language core.

---

# 68. Data model hoàn chỉnh

```text
                    AXIOM VALUE
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
     Scalar           Aggregate         Callable
       │                 │                 │
 bool/int/float    ┌─────┼─────┐       fn/closure
                    │     │     │
                 struct enum tuple
                    │     │
                  array  union
                         │
                    Option/Result


             STORAGE / OWNERSHIP
                     │
        ┌────────────┼────────────┐
        │            │            │
      inline       Box<T>       Vec<T>
        │                         │
      array                    view<T>
                              mut_view<T>


             DYNAMIC ABSTRACTION
                     │
                 dyn Trait
                     │
              explicit runtime
```

---

# 69. Điều tôi đặc biệt thích ở mô hình này

Một dòng:

```axiom
let x = Vec<i32>();
```

không ngầm kéo theo:

```text
GC
runtime
object system
RTTI
reference counting
virtual dispatch
```

Một dòng:

```axiom
let x: dyn Drawable = ...
```

thì programmer **đã yêu cầu** dynamic dispatch.

Một dòng:

```axiom
let p = Box::new(x);
```

thì programmer **đã yêu cầu semantic dynamic storage**, mặc dù optimizer vẫn có thể loại bỏ allocation nếu address/storage identity không observable.

Một dòng:

```axiom
let r = view(x);
```

thì programmer **đã tạo capability non-owning**, compiler theo dõi nhưng runtime không cần lifetime object.

Đây chính là:

> **Explicit semantic cost, implicit implementation optimization.**

---

# 70. Các invariant Data Model

Tôi đề xuất khóa:

```text
ADM-01  No Universal Object
ADM-02  No Mandatory Object Header
ADM-03  Runtime Type Information Is Explicit
ADM-04  Struct Is Primary Aggregate
ADM-05  Array Is Inline Value
ADM-06  View Is Non-Owning
ADM-07  MutView Is Exclusive
ADM-08  Vec Is Owned Dynamic Contiguous Storage
ADM-09  Vec Relocation Is Explicit Semantic Capability
ADM-10  Stable Address Must Be Explicit
ADM-11  Bytes ≠ Text
ADM-12  No Implicit Bytes→Text
ADM-13  Text Has Unicode Semantics
ADM-14  Text Indexing Does Not Promise O(1) Characters
ADM-15  Option Is Ordinary ADT
ADM-16  Result Is Ordinary ADT
ADM-17  Enum Layout Is Compiler-Controlled
ADM-18  Union Is Overlapping Storage
ADM-19  Union Does Not Implicitly Own Arbitrary Resources
ADM-20  SIMD Is Semantic Vector
ADM-21  Range Is Lightweight
ADM-22  Iterator Is Zero-Cost Abstraction
ADM-23  Collections Are Library Types
ADM-24  Heterogeneous Data Is Explicit
ADM-25  Reflection Is Opt-In
ADM-26  Dynamic Dispatch Is Explicit
ADM-27  No Mandatory Collection Runtime
ADM-28  No Mandatory Allocation
ADM-29  Representation Is Independent From Semantic Type
ADM-30  Abstraction Erasure
```

---

## Một điểm còn rất đáng quyết định

Sau phần này, tôi nghĩ Axiom đã tránh được một cái bẫy rất lớn: **không cần class/object/GC nhưng vẫn có abstraction mạnh**.

Phần tiếp theo tôi muốn xử lý là thứ ảnh hưởng trực tiếp đến **memory model và performance** mà chúng ta đã bàn trước đây:

# **Axiom Allocation & Storage Model v0.2**

Ở đó ta sẽ quyết định sâu hơn:

```text
stack
register
inline
heap
arena
pool
slab
static
thread-local
external memory
memory-mapped
custom allocator
alignment
cache locality
stable address
pinning
placement
small-object optimization
object relocation
NUMA
huge pages
DMA
GPU/device memory
```

Đặc biệt tôi muốn giải quyết một câu hỏi mà trước đây bạn đã đặt ra:

> **Có nên có một memory model “phẳng” duy nhất cho Axiom, hay nên để programmer thấy nhiều loại storage nhưng compiler vẫn thống nhất chúng dưới một abstract memory model?**

Theo hướng hiện tại, tôi nghiêng về **một abstract flat address space duy nhất ở semantic level + nhiều storage strategy ở implementation/library level**, thay vì biến stack/heap/arena/pool thành những memory type riêng trong Core.