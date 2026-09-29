# BOOTSTRAP-253 — AXIOM GENERATORS, `yield`, ITERATOR STATE MACHINES & LAZY CONTROL FLOW

**TRẠNG THÁI: FROZEN / COMPLETED**

## 1. Quyết định kiến trúc

Axiom **có `yield` trong Core v1**.

Lý do không phải để tạo thêm một abstraction riêng, mà vì `yield` cho phép compiler biểu diễn trực tiếp một dạng control flow rất hữu ích:

```text
function
    ↓
state machine
    ↓
Iterator
```

Generator không phải runtime object đặc biệt.

> **Generator là một hàm tạo ra một state machine thực hiện Iterator protocol.**

Do đó:

```text
Generator
    ≈
compiler-generated state machine
    +
Iterator contract
```

---

# 2. Tại sao không chỉ dùng closure?

Có thể biểu diễn generator bằng closure + state bên ngoài, nhưng sẽ khiến programmer phải tự quản lý:

- state;
- program counter;
- resume logic;
- termination;
- cleanup;
- ownership giữa các lần resume.

Đây chính xác là loại complexity Axiom muốn **compiler hấp thụ thay programmer**.

Vì vậy `yield` là một syntax feature nhỏ nhưng có semantic value lớn.

---

# 3. Cú pháp

Ví dụ:

```axiom
fn numbers(n: i32) -> Generator<i32> {
    let mut i = 0

    while i < n {
        yield i
        i += 1
    }
}
```

Sử dụng:

```axiom
for x in numbers(10) {
    print(x)
}
```

---

# 4. Generator không phải collection

```axiom
let xs = numbers(1_000_000)
```

không tạo một triệu phần tử.

Generator chỉ giữ state cần thiết để sinh phần tử tiếp theo.

---

# 5. Lazy semantics

Generator:

```axiom
fn numbers(n: i32) -> Generator<i32> {
    let mut i = 0

    while i < n {
        yield i
        i += 1
    }
}
```

chưa thực hiện loop khi generator được tạo.

Nó chỉ thực hiện khi:

```text
next()
```

được gọi.

---

# 6. Generator creation

Semantic operation:

```text
MakeGenerator
```

tạo:

```text
GeneratorState {
    state = Initial
    locals...
}
```

nhưng chưa chạy body.

---

# 7. `yield`

`yield expr` có semantics:

1. evaluate `expr`;
2. lưu state cần thiết;
3. trả `Some(value)`;
4. suspend generator;
5. lần `next()` tiếp theo resume tại điểm sau `yield`.

---

# 8. Ví dụ state machine

Source:

```axiom
fn f() -> Generator<i32> {
    yield 10
    yield 20
    yield 30
}
```

Compiler có thể lower thành:

```text
State0
  ↓
yield 10
  ↓
State1
  ↓
yield 20
  ↓
State2
  ↓
yield 30
  ↓
Done
```

---

# 9. Không cần coroutine runtime

State machine này có thể là:

```text
struct GeneratedGenerator {
    state: u8
}
```

hoặc thậm chí chỉ là một vài register/stack fields sau optimization.

---

# 10. Generator không phải async

Đây là distinction quan trọng:

```text
Generator
    → suspend/resume computation
    → produces values

Future
    → suspend/resume computation
    → eventually produces one result
```

---

# 11. Iterator vs Generator

Iterator là **protocol**:

```text
next() -> Option<Item>
```

Generator là **cách compiler tạo implementation của protocol đó**.

Do đó:

```text
Generator ⊂ Iterator implementations
```

về mặt behavior.

---

# 12. Generator return type

Surface syntax có thể cho phép:

```axiom
fn numbers(n: i32) -> Generator<i32>
```

Compiler biết đây là generator function.

Không cần programmer tự khai báo state-machine type.

---

# 13. `Generator<T>` nên là library abstraction

Core chỉ cần semantic support cho:

```text
yield
suspension
resume
state machine
```

`Generator<T>` là library-facing abstraction.

---

# 14. Vì sao?

Nếu `Generator` là Core built-in object type, Axiom sẽ tạo thêm một runtime type hierarchy không cần thiết.

Core chỉ cần compiler hiểu control flow.

---

# 15. Lowering

Pipeline:

```text
AST
 ↓
HIR
 ↓
Generator Analysis
 ↓
Yield Points
 ↓
Live-State Analysis
 ↓
Generator State Machine
 ↓
MIR
 ↓
Ownership Verification
 ↓
Optimization
```

---

# 16. `YieldPointId`

Compiler tạo:

```text
YieldPointId
```

tương tự:

```text
SuspensionPointId
```

của async.

---

# 17. Generator state

Mỗi state tương ứng với một điểm resume.

Ví dụ:

```text
State 0 = before first yield
State 1 = after yield #1
State 2 = after yield #2
State 3 = done
```

---

# 18. Chỉ giữ live state

Nếu local:

```axiom
let temporary = expensive()
yield 10
```

nhưng `temporary` không được dùng sau yield:

```text
temporary
```

không cần tồn tại trong generator state.

---

# 19. State-field liveness

Compiler thực hiện:

```text
LiveAcrossYield
```

tương tự:

```text
LiveAcrossAwait
```

---

# 20. Ví dụ

```axiom
fn f() -> Generator<i32> {
    let a = 10
    yield a

    let b = 20
    yield b
}
```

State machine chỉ giữ những locals thực sự cần cho resume.

---

# 21. Không lưu toàn bộ stack frame

Generator không có nghĩa:

```text
copy entire stack frame
```

Compiler chỉ spill những state cần thiết.

---

# 22. Generator stackless

Mặc định:

> Generator là **stackless state machine**.

Điều này giúp:

- kích thước nhỏ;
- dễ tối ưu;
- dễ inline;
- không cần segmented stack;
- không cần coroutine runtime.

---

# 23. Stackful coroutine không phải Core

Nếu cần stackful coroutine:

```text
Fiber
```

thuộc runtime/library.

Generator không tự động trở thành fiber.

---

# 24. `yield` không phải `await`

`yield`:

```text
producer → consumer
```

`await`:

```text
task → executor
```

Hai semantic mechanisms khác nhau.

---

# 25. Generator không schedule

Generator:

```text
next()
```

được caller điều khiển.

Không có:

```text
scheduler
thread
executor
```

ẩn bên dưới.

---

# 26. Generator không chạy concurrent

Hai generator:

```axiom
let a = numbers(10)
let b = numbers(20)
```

không chạy song song.

Caller quyết định thứ tự:

```text
a.next()
b.next()
a.next()
...
```

---

# 27. Iterator protocol

Generator có thể implement:

```text
Iterator {
    type Item
    fn next(self: mut_view<Self>) -> Option<Item>
}
```

---

# 28. Generator mutation

`next()` phải mutate internal state.

Do đó conceptual receiver:

```text
mut_view<Self>
```

---

# 29. Generator ownership

Generator sở hữu những giá trị cần sống qua các `yield`.

Ví dụ:

```axiom
fn lines(file: File) -> Generator<Str> {
    ...
}
```

Nếu generator owns `File`, file sống cùng generator.

---

# 30. Drop generator

Nếu generator bị drop khi chưa hoàn thành:

```text
drop(generator)
```

compiler phải cleanup mọi state còn live.

---

# 31. Đây là điểm rất quan trọng

Generator không được:

```text
drop state silently
```

hoặc:

```text
leak resource
```

chỉ vì nó đang suspended.

---

# 32. Generator Drop state

Ví dụ:

```axiom
fn g() -> Generator<Data> {
    let resource = acquire()

    yield make_value()

    use(resource)
}
```

Nếu caller drop generator sau `yield`, `resource` vẫn phải được cleanup.

---

# 33. Ownership qua yield

Một owner có thể sống qua nhiều yield:

```text
State0
  owner A
    ↓
yield
    ↓
State1
  owner A
    ↓
yield
    ↓
State2
  owner A
```

Verifier theo dõi ownership xuyên state transitions.

---

# 34. View qua yield

Mặc định:

```text
view<T>
```

không được phép sống qua yield nếu provenance/storage contract không đảm bảo.

---

# 35. Ví dụ nguy hiểm

Conceptually:

```axiom
fn bad() -> Generator<Str> {
    let s = String(...)
    let v = view(s)

    yield ...
    use(v)
}
```

Compiler phải kiểm tra `v` có hợp lệ qua suspension hay không.

---

# 36. View yield

Quan trọng hơn:

```axiom
fn lines(...) -> Generator<Str> {
    ...
    yield view(buffer)
}
```

Giá trị yielded `Str` có thể tồn tại **sau khi `next()` trả về**.

Do đó generator API phải định nghĩa lifetime/capability của yielded view.

---

# 37. Quyết định

Axiom **không cho phép một generator yield một ephemeral view có lifetime chỉ gắn với generator's internal `next()` call**.

Nếu yielded value là view:

```text
view provenance
```

phải bao phủ thời gian consumer có thể sử dụng nó.

---

# 38. Hai trường hợp

### Trường hợp A — owned yield

```text
yield String
```

an toàn và đơn giản.

Generator chuyển ownership cho consumer.

### Trường hợp B — borrowed yield

```text
yield view<T>
```

chỉ hợp lệ nếu generator API/compiler chứng minh storage vẫn valid và không bị relocation/mutation conflict.

---

# 39. Generator + `Vec`

Ví dụ:

```axiom
fn values() -> Generator<view<i32>> {
    let data = Vec(...)
    yield view(data)
}
```

không được tự động coi là safe chỉ vì `data` đang nằm trong generator.

Compiler phải kiểm tra:

```text
generator owns data
+
yielded view depends on data
+
next/resume can mutate/reallocate data?
```

---

# 40. Self-referential generator state

Đây là một vấn đề quan trọng.

Compiler-generated state machine có thể chứa:

```text
buffer
view(buffer)
```

Đây là self-reference.

Axiom **không đưa `Pin<T>` vào Core** chỉ để giải quyết chuyện này.

---

# 41. Quyết định cho v1

Generator state machine **không được phép có self-referential capability representation mặc định**.

Compiler phải lower theo một trong các cách:

```text
1. recompute view when resumed
2. store logical indices/ranges instead of address
3. store owned value instead
4. use explicit stable-storage contract
```

---

# 42. Đây là một quyết định rất quan trọng

Nó giúp Axiom tránh một trong những nguồn complexity lớn của coroutine systems:

```text
self-referential movable objects
```

---

# 43. Generator relocation

Generator có thể relocate nếu:

```text
no stable-address obligation
```

Nếu state machine chứa capability phụ thuộc địa chỉ:

→ compiler phải reject hoặc yêu cầu explicit stable storage.

---

# 44. Stable generator

Nếu API thực sự cần stable address:

```text
Box<GeneratorState>
```

hoặc storage abstraction tương ứng có thể cung cấp contract.

Không có `Pin<T>` Core.

---

# 45. Generator and `mut_view`

Nếu caller có:

```text
mut_view(generator)
```

thì chỉ một mutable `next()` operation tại một thời điểm.

Không concurrent mutation generator.

---

# 46. Generator is not Copy

Generator thường chứa state và có thể chứa owners.

Do đó:

```text
Generator<T>
```

mặc định là non-Copy.

---

# 47. Generator Move

```axiom
let a = numbers(10)
let b = a
```

`a` moved.

```text
b.next()
```

hợp lệ.

```text
a.next()
```

không hợp lệ.

---

# 48. Generator Clone

Không implicit clone.

Nếu state có thể clone và API định nghĩa:

```text
Clone
```

thì explicit:

```axiom
let b = a.clone()
```

---

# 49. Clone semantics

Clone generator không nhất thiết rẻ.

Có thể phải duplicate:

- buffers;
- parser state;
- file state;
- internal collections.

---

# 50. Generator Send

Generator là `Send` nếu toàn bộ state có thể transfer qua execution domain.

---

# 51. Generator Share

Generator không mặc định Share vì `next()` mutates state.

Nếu shared execution cần thiết:

```text
Mutex<Generator<T>>
```

hoặc abstraction tương ứng.

---

# 52. Generator + thread

Có thể:

```axiom
spawn(|| consume(generator))
```

nếu generator và closure đáp ứng Send.

---

# 53. Generator + async

Một generator có thể được consumed bởi async code:

```axiom
async fn process() {
    for item in generator {
        await consume(item)
    }
}
```

Generator state không tự động trở thành Future.

---

# 54. Async generator

Axiom **v1 không thêm `async fn -> Generator` như một semantic type đặc biệt**.

Thay vào đó, library có thể định nghĩa:

```text
AsyncIterator
```

và compiler hỗ trợ async state machine + iterator protocol.

---

# 55. Có thể có syntax

Axiom có thể cho:

```axiom
async fn stream() -> AsyncGenerator<Item> {
    yield item
}
```

nhưng đây chỉ là syntactic composition:

```text
async state machine
+
yield suspension
+
AsyncIterator protocol
```

không phải một runtime primitive thứ ba.

---

# 56. Async generator lowering

```text
Source
 ↓
Async Generator
 ↓
combined suspension analysis
 ↓
state machine
 ↓
Future/AsyncIterator
 ↓
MIR
```

---

# 57. Hai loại suspension

Compiler phân biệt:

```text
YieldSuspension
AwaitSuspension
```

---

# 58. State machine unified internally

Có thể có:

```text
SuspensionPoint {
    kind: Yield | Await
    id
    live_state
}
```

Điều này tránh hai hệ thống compiler hoàn toàn độc lập.

---

# 59. Nhưng semantics vẫn khác

`yield`:

```text
produce value
```

`await`:

```text
wait for readiness
```

Không được hợp nhất chúng thành cùng một language-level operation.

---

# 60. Generator completion

Khi body kết thúc:

```text
next() → None
```

và state chuyển:

```text
Done
```

---

# 61. Done is terminal

Sau:

```text
next() → None
```

các `next()` tiếp theo phải tiếp tục trả:

```text
None
```

hoặc implementation có thể exploit terminal-state knowledge.

---

# 62. No implicit restart

Generator không tự reset về State0.

---

# 63. `return` trong generator

Axiom v1:

```text
return
```

kết thúc generator.

Giá trị `return value` không được coi là yielded item.

---

# 64. Nếu cần final value

Có thể thiết kế library protocol riêng, nhưng Core `Iterator` chỉ có:

```text
Option<Item>
```

Do đó không thêm complexity vào `yield`.

---

# 65. `yield` trong nested closure

Một closure bên trong generator:

```axiom
fn g() -> Generator<i32> {
    let f = || 10
    yield f()
}
```

`f` không tự trở thành generator.

---

# 66. `yield` chỉ tác động tới enclosing generator function

Parser/resolver phải xác định nearest generator body.

---

# 67. `yield` trong normal function

Compile error:

```text
AYIELD-E001
`yield` is only valid inside a generator context
```

---

# 68. `yield` trong closure

Nếu closure không được khai báo generator-capable:

→ reject.

Nếu future syntax hỗ trợ generator closures:

→ compiler tạo generator closure state machine.

Không implicit.

---

# 69. Generator closure

Có thể hỗ trợ:

```axiom
let f = generator |x| {
    yield x
}
```

nhưng **không cần trong Core v1 syntax**.

Named generator functions và library adapters đủ cho initial implementation.

---

# 70. Generator and `for`

`for` sử dụng Iterator protocol.

Vì vậy:

```axiom
for x in numbers(10) {
    ...
}
```

không cần compiler biết generator-specific syntax tại loop site.

---

# 71. Generator adapter fusion

Ví dụ:

```axiom
numbers(1_000_000)
    .map(|x| x * 2)
    .filter(|x| x > 100)
```

Compiler có thể fuse:

```text
Generator
+
Map
+
Filter
```

thành một loop/state machine duy nhất.

---

# 72. Không tạo intermediate collection

Lazy semantics giữ:

```text
O(1)
```

storage theo state, thay vì materialize toàn bộ sequence.

---

# 73. Generator + `take`

```axiom
numbers(1_000_000).take(10)
```

consumer chỉ resume generator 10 lần.

---

# 74. Generator + infinite sequence

```axiom
fn naturals() -> Generator<u64> {
    let mut n = 0

    loop {
        yield n
        n += 1
    }
}
```

Hợp lệ.

Generator không cần biết sequence finite.

---

# 75. Drop infinite generator

Caller có thể:

```axiom
let g = naturals()
...
drop(g)
```

state cleanup deterministic.

---

# 76. Generator resource lifetime

Infinite generator vẫn có thể own:

```text
File
Socket
Buffer
Device resource
```

và Drop khi generator bị destroyed.

---

# 77. Generator cancellation

Generator không có cancellation protocol riêng trong Core.

Dropping generator là semantic termination của producer.

Nếu external operation cần cancellation:

→ library contract.

---

# 78. Async generator cancellation

Async generator cancellation là:

```text
Future/AsyncIterator Drop
+
resource cleanup
```

không phải forced thread cancellation.

---

# 79. Generator exceptions

Không có exceptions.

Generator có thể yield:

```text
Result<T,E>
```

Ví dụ:

```axiom
fn read_lines(file: File) -> Generator<Result<Str, Error>> {
    ...
}
```

---

# 80. Error propagation

`?` trong generator áp dụng theo return/result semantics.

Compiler không tự biến error thành `yield Err`.

Nếu muốn:

```text
yield Err(error)
```

phải explicit.

---

# 81. Alternative generator protocol

Library có thể define:

```text
FallibleIterator
```

nhưng không cần Core syntax.

---

# 82. Generator + panic

Panic terminates generator according to panic profile.

Resources cleanup theo Drop/unwind rules.

---

# 83. Generator state machine and Drop

Mỗi state phải có cleanup map.

Ví dụ:

```text
State0:
    A initialized

State1:
    A initialized
    B initialized

State2:
    A initialized
```

Nếu drop tại State1:

```text
drop B
drop A
```

theo ownership order.

---

# 84. Partial initialization

Generator state verifier phải support:

```text
PartiallyInitialized
```

giống normal MIR.

---

# 85. Yield and borrow-like capabilities

Internal capability:

```text
view(buffer)
```

được xem là live across suspension.

Nếu buffer relocation xảy ra sau resume:

→ invalid.

Compiler phải:

```text
prevent relocation
```

hoặc:

```text
recompute view
```

hoặc:

```text
reject
```

---

# 86. No unsafe escape through yield

`unsafe` không cho compiler bỏ qua state/capability verifier.

---

# 87. Raw pointer across yield

Raw pointer có thể tồn tại machine-level, nhưng safe dereference sau resume vẫn cần unsafe preconditions.

Generator không tự biến pointer thành safe capability.

---

# 88. Generator + external memory

Nếu state references external memory:

```text
DeviceBuffer
MappedFile
SharedMemory
```

storage contract phải remain valid across suspension.

---

# 89. GPU generator

Generator **không chạy trong GPU kernel** trong v1.

Lý do:

GPU kernel control model không phù hợp với arbitrary host-style resumable state machine.

---

# 90. GPU alternative

GPU algorithms sử dụng:

```text
iterators
loops
kernel fusion
```

chứ không dùng general generator suspension.

---

# 91. Comptime generator

Có thể chạy generator tại comptime nếu:

- generator body comptime-safe;
- resources hợp lệ;
- suspension state tồn tại trong compiler execution.

Compiler có thể materialize kết quả.

---

# 92. Comptime infinite generator

Compiler phải có evaluation budget.

Infinite execution → comptime diagnostic/resource limit.

Không phải runtime hang.

---

# 93. Generator and optimization

Một generator:

```text
yield
```

không nhất thiết giữ state machine ở machine code nếu compiler có thể prove usage.

---

# 94. Full consumer optimization

Ví dụ:

```axiom
let sum = numbers(100).sum()
```

compiler có thể biến:

```text
generator state machine
```

thành:

```text
direct loop
```

nếu semantics equivalent.

---

# 95. Generator elimination

Nếu generator only used locally:

```text
generator
 ↓
consumer
 ↓
inline
 ↓
state machine eliminated
```

---

# 96. Đây là mục tiêu zero-cost

Source:

```axiom
for x in numbers(100) {
    sum += x
}
```

không nên mặc định tạo:

```text
heap object
virtual dispatch
iterator object
generator runtime
```

---

# 97. Dynamic generator

Nếu programmer chọn:

```text
dyn Iterator<Item = T>
```

thì dynamic dispatch là explicit.

---

# 98. Static generator

Default:

```text
Generator<T>
```

có static concrete implementation.

---

# 99. Generator object safety

Dynamic iterator follows existing trait object rules.

Không tạo special object model.

---

# 100. Generator and ABI

Anonymous generated state machine layout không stable ABI.

Stable APIs nên expose:

```text
dyn Iterator
```

hoặc named opaque ABI contract.

---

# 101. `impl Iterator`

Generator function có thể expose:

```axiom
fn numbers(n: i32) -> impl Iterator<Item = i32> {
    ...
}
```

Compiler giữ concrete generator type opaque.

---

# 102. Concrete type identity

Generated generator có:

```text
GeneratorTypeId
```

nhưng programmer không cần biết tên compiler-generated.

---

# 103. Generator fingerprints

Semantic fingerprint bao gồm:

```text
generator source identity
yield type
captured/environment state
control-flow shape
relevant effects
```

Không bao gồm physical register allocation.

---

# 104. Incremental compilation

Thay đổi body generator có thể invalidate:

```text
generator state layout
```

nhưng không nhất thiết invalidate unrelated functions.

---

# 105. Debugger

Debugger có thể hiển thị:

```text
Generator G17
state: after yield #3

locals:
    i = 42
    buffer = ...
```

ngay cả khi optimized layout khác source.

---

# 106. AI compiler interface

```text
ax explain generator G17
```

có thể trả:

```text
yield points: 3
state fields: 4
captured owners: 2
live capabilities across yield: 1
Send: proven
Share: not proven
stable address required: no
```

---

# 107. Generator verification pipeline

```text
Generator AST
 ↓
Yield discovery
 ↓
State partition
 ↓
Live-across-yield analysis
 ↓
Ownership state-machine verification
 ↓
Capability verification
 ↓
Drop-state generation
 ↓
Send/Share analysis
 ↓
Async/GPU legality
 ↓
Verified MIR
```

---

# 108. State machine correctness

Compiler phải chứng minh:

```text
Every resume state is reachable only through a valid suspension.
```

---

# 109. Invalid state

Machine-level corrupted state chỉ có thể xuất hiện qua:

```text
unsafe
FFI
memory corruption
```

Safe generator code không được tạo invalid internal state.

---

# 110. State transition invariant

Mỗi transition:

```text
State A → State B
```

phải có ownership/capability state transition hợp lệ.

---

# 111. No double resume during active `next`

Một generator không thể đồng thời có hai active mutable executions của `next()` trong safe Core.

---

# 112. Reentrant generator

Generator không được re-enter chính nó trong cùng execution context.

Ví dụ conceptual:

```text
next()
  → callback
      → next()
```

phải bị reject hoặc API phải cung cấp explicit reentrancy-safe abstraction.

---

# 113. Vì sao?

State machine mutable state:

```text
current_state
```

không thể đồng thời bị mutate bởi hai active executions.

---

# 114. Generator + callback

Nếu generator gọi callback:

```text
yielded value
```

callback không được implicit acquire conflicting capability tới generator.

---

# 115. Thread-safe iteration

Concurrent consumption phải explicit synchronization.

Ví dụ:

```text
Mutex<Generator<T>>
```

không phải compiler tự lock.

---

# 116. Parallel iteration

Generator bản thân không parallel.

Parallel adapter có thể:

```text
split()
```

nếu sequence có semantic capability cho phép partition.

---

# 117. Infinite generator + parallel

Không tự động parallelize vì không có finite partition boundary.

Explicit bounded chunking cần library contract.

---

# 118. Generator and random access

Generator mặc định chỉ:

```text
next()
```

Không có random access guarantee.

---

# 119. Specialized generator

Nếu compiler/library chứng minh:

```text
ExactSize
Bidirectional
RandomAccess
```

thì có thể expose trait tương ứng.

---

# 120. `yield` type checking

`yield expr` phải unify:

```text
type(expr)
```

với generator `Item`.

---

# 121. Mismatch

```text
Generator<i32>
yield "hello"
```

compile error.

---

# 122. Expected type flows inward

Generator return annotation cung cấp expected `Item` type.

Nếu:

```axiom
fn g() -> Generator<_> {
    yield 10
}
```

compiler infer item type.

---

# 123. Generic generator

```axiom
fn repeat<T: Clone>(value: T, n: usize) -> Generator<T> {
    ...
}
```

ordinary generic semantics.

---

# 124. Clone explicit

Nếu generator cần produce multiple owned values:

```text
value.clone()
```

phải explicit.

Không implicit clone mỗi lần yield.

---

# 125. Generator consuming owner

```axiom
fn consume<T>(items: Vec<T>) -> Generator<T> {
    for item in items {
        yield item
    }
}
```

ownership chuyển:

```text
Vec
 → iterator
 → generator
 → consumer
```

không clone.

---

# 126. Partial consumption

Nếu consumer chỉ lấy vài elements:

```text
take(10)
```

remaining owned elements vẫn thuộc generator/iterator state và được cleanup khi generator dropped.

---

# 127. Đây là invariant quan trọng

Lazy iteration không được tạo resource leak chỉ vì consumer dừng sớm.

---

# 128. Generator Drop after partial iteration

```text
Generator state
+
remaining elements
```

được Drop theo ownership semantics.

---

# 129. Collection conversion

```axiom
let v = numbers(100).collect<Vec<i32>>()
```

materializes.

Compiler có thể preallocate nếu size hint/exact length proven.

---

# 130. Size hint

Generator có thể expose:

```text
size_hint()
```

nhưng size hint không phải safety proof.

---

# 131. Exact length

Nếu generator biết chính xác số yields:

```text
ExactSizeIterator
```

có thể được compiler/library-derived.

---

# 132. TrustedLength

Chỉ compiler hoặc verified trusted abstraction được đánh dấu.

User không được fake safety-critical property.

---

# 133. Generator and side effects

`yield` không làm pure function trở thành pure.

Ví dụ:

```axiom
fn g() -> Generator<i32> {
    print("hello")
    yield 10
}
```

`print` xảy ra khi execution reaches that point during `next()`.

---

# 134. Lazy side effects

Generator creation:

```text
no side effect
```

Body side effects occur during resume.

---

# 135. Observable ordering

Nếu:

```axiom
yield 10
print("A")
yield 20
```

consumer nhận `10` trước `"A"`.

Optimizer không được reorder side effect trước yield.

---

# 136. Yield is observable control boundary

Unlike ordinary compiler-internal basic block, a yield is semantically observable because control returns to caller.

---

# 137. Optimizer may eliminate yield only when

Compiler proves consumer cannot observe the intermediate suspension.

Ví dụ fully inlined local reduction.

---

# 138. FFI

Generator cannot be directly exported as stable C ABI.

Need explicit polling adapter.

---

# 139. C-style callback adapter

Library/system layer can expose:

```text
next(context, output) -> Status
```

with explicit context lifetime.

---

# 140. Dynamic loading

Generator type identity cannot cross plugin boundary without explicit ABI contract.

---

# 141. Serialization

Generator state is not serializable by default.

Serialization of execution state requires explicit application-level checkpointing.

---

# 142. Why?

Generator state may contain:

```text
OS resources
raw handles
views
foreign resources
non-serializable compiler state
```

---

# 143. Persistence

If an application needs resumable persistent computation:

```text
explicit checkpoint struct
```

rather than serializing compiler-generated generator state.

---

# 144. Generator + database

Database cursor can internally use generator-like state machine, but persistent cursor identity remains explicit.

---

# 145. Generator + network stream

Network streaming API can implement:

```text
AsyncIterator<Buffer>
```

using async state machine.

---

# 146. Zero-copy network generator

Yielding `view<Bytes>` requires buffer ownership/storage contract extending beyond the yield.

Safer API often yields an owned/moveable `NetworkBuffer`.

---

# 147. Generator + parser

Parser combinators can use generators for token streams.

Zero-copy token views must obey source buffer lifetime.

---

# 148. Generator + filesystem

Directory traversal:

```axiom
for entry in directory(path) {
    ...
}
```

can be implemented using generator/iterator state.

OS handle remains owned by traversal state.

---

# 149. Generator + GUI

GUI event stream can conceptually expose:

```text
EventStream
```

but UI event loops are externally driven.

Generator does not replace the event loop.

---

# 150. Generator + GPU

No general suspension inside GPU kernels.

Host-side stream generation is allowed.

---

# 151. Generator + tensor

Tensor iteration can use ordinary iterators; generator useful for lazy input streams.

---

# 152. Generator + AI/ML

Dataset pipeline:

```text
dataset
 → map
 → shuffle
 → batch
 → prefetch
```

can use generator/iterator abstractions.

Compiler can fuse pure stages.

---

# 153. Backpressure

Generator itself has implicit pull-based backpressure:

```text
consumer calls next()
→ producer generates one item
```

No buffering required.

---

# 154. Push streams

For push-based systems:

```text
Channel
```

or async stream abstraction is more appropriate.

Do not force generator semantics onto push systems.

---

# 155. Generator is pull-based

Core generator contract:

```text
consumer controls progress
```

---

# 156. No hidden threads

Generator cannot spontaneously execute in background.

---

# 157. No hidden scheduler

No scheduler/runtime required.

---

# 158. No mandatory heap

Generator storage may be:

```text
register
stack
inline
caller allocated
heap
arena
```

depending on escape/storage.

---

# 159. Escape analysis

Generator escape categories:

```text
NoEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
```

same framework as closures/futures.

---

# 160. Generator elimination

If:

```text
generator
```

never escapes and consumer is known:

→ state machine may disappear.

---

# 161. Generator inlining

If `next()` statically resolves:

```text
inline
```

can expose loop/control flow.

---

# 162. Yield fusion

Adjacent lazy adapters can be fused into a single state machine.

---

# 163. State minimization

Compiler removes:

- dead fields;
- constant fields;
- recomputable values;
- redundant state tags;
- redundant suspension metadata.

---

# 164. State tag optimization

If control flow permits, state can be encoded into:

```text
existing enum/discriminant
```

or implicit CFG state.

---

# 165. No required state byte

`state: u8` is illustrative only.

---

# 166. Generator machine representation

Internal MIR:

```text
GeneratorStateSwitch {
    state
    cases
}
```

followed by normal basic blocks.

---

# 167. Eventually normal machine code

No special generator backend required.

Pipeline:

```text
Generator
 → MIR state machine
 → normal optimization
 → normal LIR
 → normal machine code
```

---

# 168. This is architecturally ideal

Axiom avoids multiplying backend complexity.

Generator, async, closures eventually converge toward ordinary compiler IR.

---

# 169. Unified suspension framework

Compiler should implement:

```text
SuspensionAnalysis
```

with:

```text
Kind:
    Yield
    Await
```

Future extensions:

```text
    FiberSwitch
    Coroutine
```

can reuse it.

---

# 170. But no semantic over-generalization

The unified compiler machinery must not imply:

```text
Yield == Await == FiberSwitch
```

They have distinct semantics.

---

# 171. CompilerDB additions

```text
GeneratorDB
YieldDB
SuspensionDB
GeneratorStateDB
GeneratorLayoutDB
GeneratorEscapeDB
```

Some can share underlying infrastructure with `AsyncDB`.

---

# 172. Generator IDs

```text
GeneratorId
YieldPointId
GeneratorStateId
GeneratorFieldId
```

---

# 173. HIR

Conceptual:

```text
GeneratorExpr {
    generator_id
    body
    item_type
}
```

`YieldExpr`:

```text
YieldExpr {
    yield_id
    value
}
```

---

# 174. MIR

Possible operations:

```text
GeneratorInit
GeneratorResume
Yield
GeneratorComplete
GeneratorDrop
```

---

# 175. Lowering

Eventually:

```text
GeneratorResume
```

becomes normal MIR CFG.

---

# 176. Verified MIR

No generator-specific semantic loophole.

Ownership verifier sees:

```text
normal locals
+
state transitions
+
suspension boundaries
```

---

# 177. Ownership state across yield

For every yield:

```text
BeforeYield
AfterYield
```

ownership states must correspond.

---

# 178. Capability state across yield

For every yield:

```text
active capabilities
```

must be representable in resumed state.

---

# 179. Unknown validity

If compiler cannot prove a capability remains valid:

```text
reject
```

not:

```text
assume valid
```

---

# 180. Same fundamental rule

> **UNKNOWN ≠ SAFE**

---

# 181. Generator and relocation

A live internal view or stable-address dependency blocks relocation exactly as in ordinary ownership/storage model.

---

# 182. Generator and `Vec` reallocation

If state contains:

```text
Vec
view<Vec>
```

and `Vec` may grow/reallocate before view use:

→ conflict unless compiler proves no relocation or view is recomputed.

---

# 183. Generator and field disjointness

If:

```text
view(a.x)
mutate(a.y)
```

and regions are proven disjoint:

→ potentially valid.

Same capability model as normal code.

---

# 184. Generator state is not magic

It obeys:

```text
Ownership
Capability
Drop
Effect
Send
Share
Storage
```

exactly like every other Axiom value.

---

# 185. Generator effects

Generator callable type includes effects of its execution.

Suspension itself is part of generator semantics, not necessarily an external effect.

---

# 186. Pure generator

A generator that only computes values can remain optimizable as pure lazy computation.

---

# 187. Side-effecting generator

IO/atomic/volatile/synchronization effects prevent unsafe reordering across yields.

---

# 188. Generator and deterministic evaluation

Yield expression evaluation remains deterministic.

---

# 189. Generator and concurrency

Safe generator code cannot introduce data races.

If state shared across threads:

```text
Share/synchronization
```

must explicitly establish safety.

---

# 190. Generator and atomic memory model

Atomic operations inside generator retain normal ordering semantics across suspension.

---

# 191. Generator and `Send`

Sending generator transfers ownership of its entire live state.

---

# 192. Generator and `Share`

Sharing a generator requires synchronization because `next()` changes state.

---

# 193. Generator and `Arc`

```text
Arc<Mutex<Generator<T>>>
```

is the ordinary composition.

No special shared-generator runtime.

---

# 194. Generator and cancellation

For synchronous generator:

```text
drop = stop
```

For async:

```text
drop Future/stream state
```

according to async cancellation semantics.

---

# 195. Generator and panic unwind

Cleanup graph must cover every suspension state and panic exit.

---

# 196. Generator and optimizer correctness

Any transformation:

```text
generator → loop
generator → direct function
generator → fused state machine
```

must preserve:

- yielded values;
- ordering;
- side effects;
- panic;
- cleanup;
- external resource behavior.

---

# 197. Reference interpreter

`ax-ref` can implement generator directly:

```text
GeneratorValue {
    pc
    locals
}
```

and execute `next()`.

---

# 198. Differential testing

Test:

```text
reference generator
vs
MIR generator
vs
optimized generator
vs
native generator
```

---

# 199. Adversarial testing

Phải có test cho:

```text
yield after move
yield with live view
yield with mutable capability
drop while suspended
panic while suspended
nested generators
generator returned from function
generator moved between scopes
Send generator
Share generator
async generator
infinite generator
partial consumption
resource-owning generator
generator relocation
FFI adapter
```

---

# 200. Core design conclusion

Axiom không cần:

```text
GeneratorRuntime
CoroutineObject
GeneratorBaseClass
GeneratorGC
```

Thay vào đó:

```text
yield
 ↓
compiler state-machine lowering
 ↓
Iterator trait
```

là đủ.

---

# 201. Frozen invariants

```text
AGEN-20
Axiom Core supports yield in generator contexts.

AGEN-21
A generator is a compiler-generated state machine implementing an iterator-like protocol.

AGEN-22
Generator creation does not execute the generator body.

AGEN-23
Generator execution is lazy.

AGEN-24
Generator progress is controlled by explicit resume/next operations.

AGEN-25
Generators do not implicitly spawn threads.

AGEN-26
Generators do not implicitly schedule tasks.

AGEN-27
Generators do not require a runtime.

AGEN-28
Generators do not require heap allocation.

AGEN-29
Generator storage follows ordinary Axiom storage semantics.

AGEN-30
Generator ownership follows ordinary Axiom ownership semantics.

AGEN-31
Generators are non-Copy by default.

AGEN-32
Generator Move transfers generator state ownership.

AGEN-33
Generator Clone is explicit.

AGEN-34
Captured generator state is verified by the ownership system.

AGEN-35
Generator locals live across yield only when semantically required.

AGEN-36
Dead locals are not required in generated generator state.

AGEN-37
Every yield has a stable semantic YieldPointId.

AGEN-38
Every resumable state has a valid state identity.

AGEN-39
Invalid generator state transitions are rejected by semantic verification.

AGEN-40
Yield expression evaluation is deterministic.

AGEN-41
Yield suspends after evaluating its yielded value.

AGEN-42
The consumer receives yielded values according to iterator semantics.

AGEN-43
Generator completion is terminal.

AGEN-44
Completed generators do not implicitly restart.

AGEN-45
Dropping a suspended generator performs required cleanup.

AGEN-46
Generator cleanup is deterministic.

AGEN-47
Partially initialized generator state is tracked precisely.

AGEN-48
Moved generator state is never dropped twice.

AGEN-49
Generator state with Drop resources obeys ordinary Drop semantics.

AGEN-50
A generator cannot retain a dangling safe capability across yield.

AGEN-51
Ephemeral capabilities cannot implicitly escape through yield.

AGEN-52
Yielded views require valid provenance for their complete observable lifetime.

AGEN-53
Unknown capability validity across yield is not treated as valid.

AGEN-54
Generator state cannot implicitly become self-referential through unsafe compiler lowering.

AGEN-55
Self-referential state requires an explicit stable-storage contract or equivalent transformation.

AGEN-56
Generator relocation is allowed only when all state capabilities permit relocation.

AGEN-57
Stable-address obligations prevent invalid generator relocation.

AGEN-58
Generator Send is derived from complete live generator state.

AGEN-59
Generator Share is distinct from Generator Send.

AGEN-60
Shared generator mutation requires synchronization.

AGEN-61
Generator execution cannot create safe data races.

AGEN-62
Generator atomic operations obey the Axiom memory model.

AGEN-63
Generator synchronization effects remain observable.

AGEN-64
Generator IO effects remain observable.

AGEN-65
Generator panic semantics follow the configured panic model.

AGEN-66
Generator cleanup occurs correctly on panic/unwind.

AGEN-67
Generator return without value completes the generator.

AGEN-68
Generator return does not implicitly yield a final item.

AGEN-69
Generator errors are represented by ordinary Result/Option/value semantics.

AGEN-70
The compiler does not implicitly convert errors into yielded values.

AGEN-71
Generator iteration uses the ordinary iterator abstraction.

AGEN-72
Generator-specific syntax does not create a second object model.

AGEN-73
Generator state-machine representation is compiler-controlled.

AGEN-74
Generated generator layout is not stable ABI by default.

AGEN-75
Stable foreign generator interfaces require explicit ABI adapters.

AGEN-76
Generator state is not serializable by default.

AGEN-77
Persistent resumable computation requires an explicit checkpoint representation.

AGEN-78
Generator execution is pull-based by default.

AGEN-79
Generators do not imply buffering.

AGEN-80
Generators do not imply backpressure queues.

AGEN-81
Push-based streaming is represented by explicit channel/stream abstractions.

AGEN-82
Generator infinite execution is valid when the consumer controls progress.

AGEN-83
Dropping an infinite generator terminates its ownership state and performs cleanup.

AGEN-84
Generator recursion requires ordinary supported recursion/indirection rules.

AGEN-85
A generator cannot safely re-enter an active mutable resume operation.

AGEN-86
Reentrant generator behavior requires an explicit supported abstraction.

AGEN-87
Generator generic parameters use ordinary Axiom generic semantics.

AGEN-88
Generator yielded values do not receive implicit Clone.

AGEN-89
Owned yielded values transfer ownership according to ordinary Move semantics.

AGEN-90
Partially consumed owning generators retain ownership of remaining state.

AGEN-91
Remaining generator-owned resources are cleaned when the generator is dropped.

AGEN-92
Generator adapters preserve iterator semantics.

AGEN-93
Lazy generator pipelines do not require intermediate materialization.

AGEN-94
Generator fusion is an optimization, not a semantic requirement.

AGEN-95
Generator state-machine elimination is legal only when observable behavior is preserved.

AGEN-96
Generator inlining is legal only when observable behavior is preserved.

AGEN-97
Generator optimization cannot reorder observable effects across yield boundaries.

AGEN-98
Yield is an observable control boundary unless proven unobservable through whole-program semantics.

AGEN-99
Generator optimization cannot change yielded-value order.

AGEN-100
Generator optimization cannot change cleanup behavior.

AGEN-101
Generator optimization cannot change panic behavior.

AGEN-102
Generator optimization cannot change external effects.

AGEN-103
Generator optimization cannot change synchronization semantics.

AGEN-104
Generator optimization cannot change ownership semantics.

AGEN-105
Generator optimization cannot change capability validity.

AGEN-106
Generator optimization cannot change Send/Share legality.

AGEN-107
Generator state can be scalarized when semantic equivalence is proven.

AGEN-108
Generator state fields can be eliminated when they are semantically dead.

AGEN-109
Generator state tags may be optimized when state identity remains semantically preserved.

AGEN-110
Generator state need not physically exist when the compiler eliminates the generator abstraction.

AGEN-111
Generator execution lowers to ordinary MIR control flow.

AGEN-112
Generator-specific backend machinery is not required.

AGEN-113
Reference interpretation models generator suspension explicitly.

AGEN-114
Generator behavior is covered by differential compiler testing.

AGEN-115
Generator behavior is covered by ownership adversarial testing.

AGEN-116
Generator behavior is covered by capability adversarial testing.

AGEN-117
Generator behavior is covered by panic/cleanup testing.

AGEN-118
Generator behavior is covered by concurrency testing.

AGEN-119
Generator behavior is covered by async composition testing.

AGEN-120
Generator behavior is independent of optimization level.

AGEN-121
Generator behavior is independent of physical storage location.

AGEN-122
Generator behavior is independent of register allocation.

AGEN-123
Generator state analysis is incremental.

AGEN-124
Generator state analysis is deterministic.

AGEN-125
Generator diagnostics expose yield points and live state.

AGEN-126
AI tooling may query generator state facts but cannot override verification.

AGEN-127
Generator comptime execution obeys comptime capability restrictions.

AGEN-128
Comptime generator execution does not imply runtime generator allocation.

AGEN-129
Generator use in GPU execution is not permitted unless a future GPU-specific profile explicitly defines resumable execution semantics.

AGEN-130
Async generators are a composition of async suspension and yield semantics, not a third mandatory runtime primitive.

AGEN-131
Async generator state obeys ordinary async ownership rules.

AGEN-132
Async generator Send is derived from complete suspended state.

AGEN-133
Async generator cancellation is distinct from synchronous generator exhaustion.

AGEN-134
Generator state does not implicitly become a Fiber.

AGEN-135
Stackful coroutine semantics belong to explicit Fiber/runtime abstractions.

AGEN-136
Generator semantics remain independent of scheduler implementation.

AGEN-137
Generator semantics remain independent of executor implementation.

AGEN-138
Generator semantics remain independent of heap allocator implementation.

AGEN-139
Generator semantics remain independent of object-header/runtime conventions.

AGEN-140
Generator abstraction overhead should be eliminated when provably unnecessary.
```

---

# 202. Kiến trúc control-flow hiện tại

Sau 253, Axiom đã có một mô hình rất nhất quán:

```text
                 CONTROL FLOW
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    ordinary       generator       async
       │              │              │
      CFG          yield/state     await/state
       │              │              │
       └──────────────┼──────────────┘
                      │
                  MIR / CFG
                      │
             Ownership + Capability
                      │
                  Optimization
```

Điểm quan trọng là **generator và async không tạo hai backend/compiler model hoàn toàn khác nhau**.

Cả hai đều cuối cùng trở thành:

```text
ordinary MIR
+
state
+
suspension points
```

---

# 203. Một quyết định lớn vừa được chốt

Đến đây Axiom có thể có cả:

```text
closure
iterator
generator
async
future
```

mà vẫn không bị “phình” thành một ngôn ngữ có quá nhiều primitive.

Quan hệ của chúng:

```text
Closure
   │
   └── callable computation

Generator
   │
   └── lazy resumable computation
           │
           └── Iterator

Async function
   │
   └── resumable computation
           │
           └── Future

Async Generator
   │
   └── resumable computation
       + yield
       + await
           │
           └── AsyncIterator
```

Compiler có thể dùng chung:

```text
Capture Analysis
Escape Analysis
Suspension Analysis
State Liveness
Ownership Verification
Capability Verification
Drop Elaboration
SSA
Optimization
```

Đây là hướng rất tốt cho mục tiêu của Axiom: **compiler phức tạp nhưng ngôn ngữ phía programmer vẫn tương đối đơn giản.**

---

## BOOTSTRAP-254 tiếp theo

Phần logic tiếp theo nên chốt **AXIOM `DEFER`, SCOPE CLEANUP, DESTRUCTOR ELABORATION & EARLY-EXIT CONTROL FLOW**.

Nó sẽ giải quyết một điểm cực kỳ quan trọng còn lại của ngôn ngữ:

```text
scope
 ├── let
 ├── Drop
 ├── defer/ScopeGuard
 ├── return
 ├── break
 ├── continue
 ├── ?
 ├── panic
 ├── yield
 └── await
```

và đặc biệt phải quyết định dứt khoát:

> **Axiom có cần `defer` trong Core hay Drop + ScopeGuard đã đủ?**

Đây là chỗ cần thiết kế rất cẩn thận, vì nó ảnh hưởng trực tiếp đến **RAII, cleanup CFG, async, generator, error propagation và compiler-generated cleanup paths**.