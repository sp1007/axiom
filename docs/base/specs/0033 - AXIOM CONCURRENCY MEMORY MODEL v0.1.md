Tiếp tục từ **AXIOM EXECUTION SEMANTICS v0.1**, phần tiếp theo nên là **AXIOM CONCURRENCY MEMORY MODEL v0.1**.

Điểm tôi muốn giữ rất chặt: **Axiom không nên trở thành “Rust nhưng đổi cú pháp”**. Mục tiêu là compiler làm phần khó, còn programmer chỉ phải thể hiện những ranh giới thực sự có ý nghĩa.

# AXIOM CONCURRENCY MEMORY MODEL v0.1

## 1. Mục tiêu

Axiom phải đồng thời đạt 4 điều:

1. **Safe code không có data race.**
2. Không cần programmer viết lifetime/borrow annotation.
3. Không bắt buộc GC/RC/runtime.
4. Vẫn cho phép atomic, lock-free, SIMD, shared memory, OS primitives và raw pointer trong `unsafe`.

Mô hình tổng quát:

```text
                    Axiom Safe Code
                           │
             ┌─────────────┴─────────────┐
             │                           │
        Exclusive ownership         Shared access
             │                           │
           MOVE                    READ / SHARE
             │                           │
       another task/thread       immutable concurrent access
                                         │
                              mutable shared state
                                         │
                              explicit synchronization
                                         │
                         Mutex / Atomic / Channel / ...
```

Nguyên tắc:

> **Compiler tự quản lý ownership/capability; programmer chỉ chọn mô hình chia sẻ.**

---

# 2. Không nên có một khái niệm “thread-safe”

Một lỗi thiết kế dễ mắc là tạo một property kiểu:

```text
ThreadSafe
```

Tôi không khuyến nghị.

Thay vào đó Axiom có hai property cơ bản:

```text
Send
Share
```

### `Send`

Một giá trị có thể **chuyển quyền sở hữu** sang execution context khác.

Ví dụ:

```axiom
var buffer = Buffer<u8>.new()

spawn(move buffer)
```

Sau `spawn`:

```text
caller      -> không còn ownership
worker      -> ownership
```

### `Share`

Một giá trị có thể được **chia sẻ read-only** giữa nhiều execution context.

Ví dụ:

```axiom
let config = Arc<Config>.new(load_config())

spawn({
    read_config(config)
})

spawn({
    read_config(config)
})
```

Hai property độc lập:

| Type | Send | Share |
|---|---:|---:|
| `i32` | ✓ | ✓ |
| immutable `Point` | ✓ | ✓ |
| `Vec<T>` | thường ✓ | ✗ |
| `Arc<T>` | ✓ | tùy T |
| `Mutex<T>` | ✓ | ✓ qua synchronization |
| raw pointer | không mặc định | không mặc định |

Điểm quan trọng:

> `Send != Share`

Không được suy ra cái này từ cái kia.

---

# 3. Ba access mode đủ cho phần lớn safe concurrency

Ở mức semantic verifier, ta đã có:

```text
READ
WRITE
MOVE
DROP
```

Concurrency chỉ cần bổ sung execution-context ownership.

Ta có:

```text
MOVE
READ SHARE
MUTABLE SHARE
```

### MOVE

```axiom
spawn(move data)
```

Ownership chuyển sang task khác.

### READ SHARE

```axiom
spawn({
    inspect(data)
})
```

Nếu `data` có `Share`, nhiều context có thể đọc.

### MUTABLE SHARE

Không được phép mặc định.

Muốn:

```text
Task A ──┐
         ├──> shared mutable state
Task B ──┘
```

phải đi qua abstraction có synchronization semantics.

Ví dụ:

```axiom
let counter = Atomic<i64>.new(0)
```

hoặc:

```axiom
let state = Mutex<State>.new(...)
```

Đây là một quyết định rất quan trọng.

> **Axiom không cấm shared mutable memory; Axiom yêu cầu shared mutable memory phải có semantic synchronization.**

---

# 4. Vì sao không nên đưa Mutex/Atomic vào compiler core quá sâu?

Compiler cần hiểu **semantic effect** của chúng, nhưng không nên hard-code implementation.

Ví dụ:

```axiom
lock.acquire()
state.value += 1
lock.release()
```

Compiler không cần biết `Mutex` thực hiện bằng:

```text
futex
spinlock
pthread_mutex
Windows SRWLOCK
custom assembly
```

Thư viện định nghĩa contract:

```text
acquire:
    synchronization acquire

release:
    synchronization release
```

Compiler/verifier hiểu:

```text
LOCK
UNLOCK
```

nhưng implementation có thể nằm trong standard library/system layer.

Tương tự:

```axiom
Atomic<i32>
```

library type có thể map xuống intrinsic:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
```

---

# 5. Memory ordering phải là semantic primitive

Axiom không nên có atomic “mơ hồ”.

Các ordering cơ bản:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Ví dụ:

```axiom
counter.fetch_add(1, Relaxed)
```

hoặc:

```axiom
ready.store(true, Release)

while !ready.load(Acquire) {
}
```

Compiler được phép tối ưu instruction, nhưng không được phá:

```text
happens-before
```

đã được yêu cầu bởi chương trình.

---

# 6. Không nên có `volatile` = atomic

Đây là điểm cần khóa rõ.

```text
volatile != atomic
```

`volatile` dùng cho:

- memory-mapped I/O
- hardware register
- device memory
- compiler không được loại bỏ/reorder access theo cách vi phạm contract

Atomic dùng cho:

- inter-thread synchronization
- lock-free algorithms
- memory ordering

Ví dụ:

```axiom
volatile_read(register)
```

không đồng nghĩa với:

```axiom
atomic_load(register)
```

---

# 7. Channel nên là ownership transfer

Đây là một điểm Axiom có thể làm rất đẹp.

Thay vì:

```text
shared mutable queue
```

hãy ưu tiên:

```axiom
let (tx, rx) = channel<Buffer>()

spawn({
    tx.send(buffer)
})
```

`send` thực hiện:

```text
MOVE(buffer)
```

Sau khi gửi:

```text
sender:    MOVED
receiver:  OWNED
```

Điều này khiến concurrency trở thành extension tự nhiên của ownership system đã có.

Không cần:

```text
lock
atomic
reference counting
```

cho trường hợp truyền ownership thuần túy.

---

# 8. Thread spawn

Semantic model:

```axiom
fn spawn<T: Send>(task: fn() -> T) -> JoinHandle<T>
```

Nhưng đây chỉ là cách mô tả logic; API thật có thể khác.

Khi compiler gặp:

```axiom
var data = Buffer<u8>.new()

spawn(move {
    process(data)
})
```

compiler xác định closure environment:

```text
ClosureEnv {
    data: Buffer<u8>
}
```

Sau đó:

```text
ClosureEnv: Send
```

Nếu `Buffer<u8>` là `Send`:

```text
✓
```

Nếu closure capture thứ gì đó không `Send`:

```text
ERROR AX_CONC_....
value captured by spawned task is not Send
```

Không cần programmer viết lifetime.

---

# 9. `spawn` không nên tự động biến closure thành detached task

Tôi đề xuất:

```text
spawn()
```

tạo **owned task handle**.

Ví dụ:

```axiom
let task = spawn(worker)

let result = task.join()
```

Nếu muốn detached:

```axiom
detach(spawn(worker))
```

hoặc API tương đương.

Lý do:

Nếu detach là mặc định, compiler khó reason về resource lifetime và failure propagation.

Structured concurrency nên là:

```text
parent
 ├── child
 ├── child
 └── child
```

thay vì:

```text
program
 ──> random background tasks forever
```

Nhưng đây là **library/concurrency API policy**, không nhất thiết phải là hard-coded language syntax.

---

# 10. Async không phải Thread

Điểm này nên khóa.

```text
thread
    = execution resource

task
    = logical work

async
    = suspend/resume control flow

executor
    = scheduler
```

Ví dụ:

```axiom
async fn download() -> Result<Data, Error> {
    let connection = connect().await?
    let data = connection.read().await?
    data
}
```

Compiler có thể biến thành:

```text
StateMachine {
    state
    connection
    data
    ...
}
```

Không có nghĩa:

```text
async = spawn thread
```

---

# 11. View qua `await`

Đây là một trong những chỗ verifier phải cực kỳ nghiêm.

Ví dụ:

```axiom
async fn process(buffer: Buffer<u8>) {
    let v = view(buffer)

    use(v)

    await something()

    use(v)
}
```

Không thể đơn giản coi `await` là một function call bình thường.

Sau `await`, task có thể:

- chạy lại trên cùng thread
- chạy thread khác
- bị giữ lâu
- bị executor migrate

Do đó compiler phải xác định:

```text
value nào sống qua SUSPEND?
view nào sống qua SUSPEND?
ownership nào sống qua SUSPEND?
```

---

# 12. Rule đề xuất cho async

Tại mỗi:

```text
SUSPEND
```

compiler tạo một semantic checkpoint.

Ví dụ:

```text
Before await:

buffer       OWNED
view(buffer) READ capability
```

Nếu view tiếp tục tồn tại:

```text
After await:

buffer       OWNED
view(buffer) READ capability
```

thì view provenance phải vẫn hợp lệ.

Nếu async task có thể migrate:

```text
all state surviving suspension
```

phải thỏa các yêu cầu tương ứng, đặc biệt `Send`.

---

# 13. `spawn_local`

Để tránh ép mọi async task phải `Send`, nên có concept:

```axiom
spawn_local(async_task)
```

Nó cho phép task bị giới hạn trong executor/context hiện tại.

Ví dụ:

```axiom
let local_data = LocalState.new()

spawn_local(async {
    use(local_data)
    await io()
    use(local_data)
})
```

Nếu executor đảm bảo task không migrate:

```text
Send requirement có thể được relax
```

Nhưng:

```text
Share / alias / lifetime
```

vẫn phải được kiểm tra.

Điều này rất quan trọng vì nếu không có `spawn_local`, Axiom sẽ vô tình làm async quá restrictive.

---

# 14. Mutex guard nên là RAII resource

Ví dụ:

```axiom
let guard = mutex.lock()

guard.value += 1
```

`guard` là owning resource:

```text
OWNED
DROP
```

Khi ra khỏi scope:

```text
DROP guard
    ↓
UNLOCK mutex
```

Do đó:

```text
MutexGuard
    = !Copy
    = Drop
```

và `Drop` có observable synchronization effect:

```text
RESOURCE_RELEASE
UNLOCK
```

Compiler **không được tùy tiện kéo Drop lên sớm** nếu điều đó thay đổi synchronization semantics.

Đây chính là lý do trước đó ta phải tách:

```text
Capability lifetime
```

và:

```text
Ownership/resource lifetime
```

---

# 15. Last-use không được phá synchronization

Ví dụ:

```axiom
let guard = mutex.lock()

use(guard)

do_something()

use(guard)
```

Compiler có thể nhận ra lần cuối sử dụng `guard` ở dòng cuối.

Nhưng không được suy ra:

```text
DROP guard
```

ngay sau lần sử dụng trước đó nếu `Drop` làm:

```text
unlock()
```

vì việc unlock sớm là observable.

Đây là một nguyên tắc cực kỳ quan trọng:

> **Last-use kết thúc capability lifetime, không mặc định kết thúc resource lifetime.**

---

# 16. Data race definition

Axiom nên định nghĩa data race ở semantic level:

Có race khi tồn tại đồng thời:

```text
WRITE(region)
```

và:

```text
READ(region)
```

hoặc:

```text
WRITE(region)
WRITE(region)
```

trên cùng execution period mà:

```text
không có ordering/synchronization hợp lệ
```

Safe code phải bị reject.

Ví dụ:

```axiom
var x = 0

spawn({
    x += 1
})

spawn({
    x += 1
})
```

Nếu `x` được capture shared mutable:

```text
REJECT
```

Không được compiler âm thầm biến thành atomic.

---

# 17. Nhưng disjoint regions vẫn phải chạy song song

Đây là nơi region system của Axiom rất có giá trị.

```axiom
struct State {
    left: i64
    right: i64
}
```

Nếu:

```text
Task A → WRITE(state.left)
Task B → WRITE(state.right)
```

thì:

```text
Region(left) ∩ Region(right) = ∅
```

=> về mặt memory access:

```text
SAFE
```

Không cần lock toàn bộ `State`.

Đây là lý do tôi **không muốn bỏ region analysis**, dù chúng ta tránh borrow checker kiểu Rust.

Programmer không cần viết:

```text
&mut state.left
&mut state.right
```

Compiler tự chứng minh disjointness.

---

# 18. Region + synchronization

Verifier có thể xem access như:

```text
Access {
    region
    mode
    execution_context
    synchronization
}
```

Ví dụ:

```text
Task A
    WRITE R1
    RELEASE L

Task B
    ACQUIRE L
    READ R1
```

Có:

```text
happens-before(A.WRITE, B.READ)
```

=> hợp lệ.

Ngược lại:

```text
Task A
    WRITE R1

Task B
    READ R1
```

không synchronization:

```text
REJECT
```

---

# 19. Lock-free programming vẫn phải được hỗ trợ

Axiom không nên ép:

```text
Mutex everywhere
```

Atomic cho phép:

```axiom
var head = Atomic<usize>.new(0)

loop {
    let old = head.load(Acquire)

    if head.compare_exchange(
        old,
        old + 1,
        AcqRel,
        Acquire
    ) {
        break
    }
}
```

Compiler hiểu:

```text
ATOMIC_LOAD
ATOMIC_CAS
```

nhưng không can thiệp vào algorithm.

Đây là phần `unsafe`/system-level nếu programmer thao tác memory structure phức tạp hơn mà verifier không thể chứng minh.

---

# 20. Safe lock-free data structure

Tôi muốn phân biệt:

```text
Atomic<T>
```

với:

```text
Atomic pointer + manually managed memory
```

Trường hợp thứ hai có thể cần:

```axiom
unsafe
```

Ví dụ:

```axiom
unsafe fn push_node(...) {
    ...
}
```

Nhưng:

```text
unsafe
```

không có nghĩa:

```text
compiler bỏ hết kiểm tra
```

Nó chỉ nói:

> Programmer chịu trách nhiệm cho invariant mà compiler không thể chứng minh.

Compiler vẫn kiểm tra:

- type
- layout
- ABI
- instruction validity
- control flow
- generic constraints
- các invariant không bị unsafe override

---

# 21. Memory ordering không được suy luận quá “thông minh”

Tôi đề xuất:

```text
Atomic ordering là programmer-visible semantic choice.
```

Compiler có thể optimize trong phạm vi ordering cho phép.

Nhưng không được tự động biến:

```text
Relaxed
```

thành:

```text
Acquire
```

hay ngược lại chỉ vì optimizer nghĩ rằng “có vẻ ổn”.

Có thể thay instruction nếu observable semantics vẫn tương đương, nhưng **language semantics của ordering phải rõ ràng và kiểm chứng được**.

---

# 22. `Send` / `Share` nên là compiler properties

Không nên bắt programmer viết:

```axiom
impl Send for MyType
```

cho những type compiler có thể chứng minh.

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

Compiler tự suy ra:

```text
Copy
Send
Share
Sized
!Drop
```

Nếu:

```axiom
struct Foo {
    file: File
}
```

thì:

```text
!Copy
Drop
```

và `Send`/`Share` phụ thuộc property của `File`.

---

# 23. Không được suy ra `Share` chỉ vì immutable

Đây là một bẫy.

Một object immutable về mặt language nhưng chứa:

```text
interior mutable state
```

thì không nhất thiết `Share`.

Ví dụ:

```axiom
struct Cache {
    table: ...
    internal_counter: Atomic<i64>
}
```

có thể `Share`, vì mutation được synchronization bằng atomic.

Nhưng một type có hidden unsynchronized mutable state:

```text
Share = false
```

Do đó `Share` phải là **semantic property**, không đơn giản là “mọi field đều immutable”.

---

# 24. `Arc<T>` không tự động làm `T` thread-safe

Ví dụ:

```axiom
Arc<Vec<i32>>
```

không nên đồng nghĩa với:

```text
safe shared mutable Vec
```

`Arc` chỉ cung cấp:

```text
shared ownership
```

Không tự cung cấp:

```text
mutable synchronization
```

Vì vậy:

```text
Arc<T>
```

có thể `Send` nếu `T` phù hợp, nhưng việc chia sẻ/mutation vẫn phụ thuộc `Share`/synchronization semantics.

Đây là điểm giúp Axiom tránh rất nhiều bug API.

---

# 25. Memory model cấp thấp

Ta nên phân tầng:

```text
                 Axiom Memory Model
                        │
        ┌───────────────┼────────────────┐
        │               │                │
     Safe memory     Atomic memory    Unsafe memory
        │               │                │
 value/view        ordering         raw pointer
 ownership         happens-before   volatile
 bounds            CAS              MMIO
 lifetime           RMW              FFI
```

### Safe memory

Compiler chịu trách nhiệm.

### Atomic memory

Programmer chọn ordering, compiler đảm bảo semantics.

### Unsafe memory

Programmer chịu trách nhiệm cho invariants không chứng minh được.

---

# 26. Một điểm tôi đề xuất thêm: `Sync` không cần tồn tại

Một số ngôn ngữ tách:

```text
Send
Sync
```

Nhưng với Axiom:

```text
Send
Share
```

đã diễn đạt gần đúng nhu cầu semantic mà chúng ta muốn.

`Share` có thể hiểu:

> một giá trị có thể được read/shared giữa execution contexts theo contract của type.

Không cần sao chép nguyên mô hình Rust.

---

# 27. Concurrency invariant mới

Tôi đề xuất thêm vào Axiom Ownership/Verifier:

### AOV-19 — Data Race Freedom

Safe code không được tạo conflicting unsynchronized accesses đến cùng memory region.

### AOV-20 — Send Transfer

Giá trị crossing execution context bằng ownership transfer phải thỏa `Send`.

### AOV-21 — Share Safety

Giá trị được immutable-share giữa execution contexts phải thỏa `Share`.

### AOV-22 — Synchronization Semantics

Atomic/lock/channel primitives phải tạo synchronization semantics được verifier/compiler tôn trọng.

### AOV-23 — Atomic Ordering

Atomic operations phải giữ memory-order semantics được khai báo.

### AOV-24 — No Implicit Synchronization

Compiler không tự biến ordinary memory access thành atomic/lock/synchronization operation.

### AOV-25 — Async Suspension Safety

Mọi state sống qua `SUSPEND` phải hợp lệ theo execution-context model.

### AOV-26 — Local Task Isolation

`spawn_local` có thể relax `Send`, nhưng không được phá ownership/alias safety.

### AOV-27 — Resource Synchronization

Resource release có observable synchronization effect không được optimizer di chuyển tùy tiện.

---

# 28. Một thay đổi quan trọng đối với kiến trúc verifier

Ban đầu:

```text
Ownership
Access
Effects
```

Giờ nên chính thức thành:

```text
                         Typed MIR
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
        Ownership       Capability       Effects
             │              │              │
             └──────────────┼──────────────┘
                            ↓
                    Concurrency Analysis
                            │
                  ┌─────────┴─────────┐
                  ↓                   ↓
             Send / Share       Synchronization
                  │                   │
                  └─────────┬─────────┘
                            ↓
                        VERIFIER
                            ↓
                      VERIFIED MIR
```

Concurrency **không phải một hệ thống riêng biệt**.

Nó là extension của ownership + region + effects.

Đây là kiến trúc tôi đánh giá rất quan trọng đối với Axiom.

---

# 29. Ví dụ tổng hợp

```axiom
struct Image {
    pixels: Buffer<u8>
}

fn process(img: mut_view<Image>) {
    resize(img)
}

fn worker(img: Image) {
    process(mut_view(img))
}

fn main() {
    var image = load_image()

    let task = spawn(move {
        worker(image)
    })

    task.join()
}
```

Semantic flow:

```text
load_image()
      ↓
 Image OWNED
      ↓
 MOVE
      ↓
 closure environment
      ↓
 spawn
      ↓
 worker owns Image
      ↓
 mut_view(Image)
      ↓
 WRITE
      ↓
 task ends
      ↓
 DROP Image
```

Không có:

```text
GC
borrow annotation
lifetime annotation
Arc
Mutex
runtime ownership machinery
```

Nhưng vẫn có memory safety.

---

# 30. Còn trường hợp shared mutable

```axiom
let counter = Atomic<i64>.new(0)

spawn({
    counter.fetch_add(1, Relaxed)
})

spawn({
    counter.fetch_add(1, Relaxed)
})
```

Ở đây compiler không coi hai write là ordinary:

```text
WRITE + WRITE = race
```

mà là:

```text
ATOMIC_RMW + ATOMIC_RMW
```

với ordering semantics hợp lệ.

Do đó:

```text
SAFE
```

nếu `Atomic<i64>` contract cho phép.

---

# 31. Và trường hợp sai

```axiom
var counter = 0

spawn({
    counter += 1
})

spawn({
    counter += 1
})
```

Verifier phát hiện:

```text
Task A: WRITE counter
Task B: WRITE counter
```

không synchronization.

Kết quả:

```text
REJECT
AX_CONC_0001:
conflicting mutable accesses to shared region without synchronization
```

Không cần programmer hiểu borrow checker.

---

# 32. Kết luận kiến trúc

Tôi nghĩ mô hình hiện tại của Axiom đang đi đến một điểm khá mạnh:

```text
                 PROGRAMMER
                     │
          ┌──────────┴──────────┐
          │                     │
       ownership            synchronization
          │                     │
        MOVE              Atomic / Mutex /
        value              Channel / etc.
          │                     │
          └──────────┬──────────┘
                     ↓
                  COMPILER
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
     regions      lifetime      effects
        │            │            │
        └────────────┼────────────┘
                     ↓
                concurrency
                  verifier
                     ↓
                VERIFIED MIR
```

Điểm khác biệt cốt lõi so với Rust nên là:

> **Rust đưa nhiều ownership constraints vào cú pháp và mô hình programmer-facing; Axiom đưa phần lớn complexity vào compiler analysis.**

Programmer chủ yếu thấy:

```text
value
move
view
mut_view
Send
Share
Atomic
Mutex
Channel
unsafe
```

chứ không phải:

```text
'a
&'a mut T
where 'a: ...
```

và compiler phải đủ mạnh để tự thực hiện phần còn lại.

---

### Bước tiếp theo tôi đề xuất

Sau **Concurrency Memory Model**, phần quan trọng nhất không phải syntax mà là **định nghĩa chính xác thuật toán Ownership/Region/Concurrency Verifier**.

Cụ thể ta nên thiết kế:

```text
AXIOM VERIFIER v0.1
├── 1. Abstract State
├── 2. Ownership Lattice
├── 3. Initialization Lattice
├── 4. Region Algebra
├── 5. Capability Lifetime
├── 6. Effect System
├── 7. CFG Join
├── 8. Loop Fixed Point
├── 9. Send/Share
├── 10. Happens-Before
├── 11. Async Suspension
├── 12. Drop Elaboration
├── 13. Unsafe Boundary
└── 14. Proof → Verified MIR
```

Đây mới là **“trái tim” của Axiom**. Nếu thuật toán này thiết kế tốt, ta có thể đạt mục tiêu ban đầu của bạn: **ngôn ngữ đơn giản với programmer nhưng compiler đủ thông minh để đảm nhận complexity của ownership, lifetime, alias và concurrency mà không biến Axiom thành một ngôn ngữ nặng nề.**