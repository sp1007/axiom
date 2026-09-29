Tiếp tục từ **Axiom Type System v0.1**, phần hợp lý tiếp theo là **Concurrency Model v0.1**. Đây là phần rất quan trọng vì nó quyết định Axiom có đạt được mục tiêu **nhanh như C/C++ nhưng không bắt lập trình viên chịu sự phức tạp kiểu Rust** hay không.

Tôi đề xuất không đưa thread/async/scheduler thành một “hệ thống ngôn ngữ khổng lồ”. Ta chỉ đóng băng **các quy tắc an toàn và memory visibility**, còn API thread, channel, executor… để thư viện xây trên đó.

# AXIOM CONCURRENCY MODEL v0.1

**Status: PROPOSED → nên freeze sau khi rà soát**

## 1. Mục tiêu

Axiom concurrency phải đạt:

1. Không data race trong safe code.
2. Không yêu cầu garbage collector.
3. Không yêu cầu reference counting cho mọi object.
4. Không bắt programmer viết lifetime/borrow annotation.
5. Thread và async dùng **cùng ownership model**.
6. Có thể viết code low-level gần C/C++.
7. Compiler có thể tối ưu concurrency primitives mà không phá semantics.
8. Không bắt buộc một runtime lớn.
9. Cho phép CPU/GPU/OS/library tự xây scheduler riêng.
10. Unsafe vẫn có thể truy cập primitive thấp hơn khi cần.

Điểm quan trọng:

> **Axiom không cố biến concurrency thành một hệ thống type-level cực kỳ phức tạp. Nó chỉ buộc những điều cần thiết để compiler chứng minh safe code không có data race/lifetime violation.**

---

# 2. Ba cách truyền dữ liệu

Axiom chỉ cần phân biệt rõ ba trường hợp:

```text
MOVE
READ SHARE
MUTABLE SHARE
```

### MOVE

Quyền sở hữu chuyển sang execution context khác.

```axiom
let buffer = Buffer.load(path)

spawn {
    process(buffer)
}
```

Sau `spawn`, `buffer` thuộc task mới.

Task hiện tại không được dùng tiếp:

```axiom
process(buffer)   // ERROR
```

Không cần:

```text
'a
&buffer
&'static
Send<'a>
```

như Rust.

Compiler tự phân tích.

---

# 3. Send

`Send` là **semantic property**, không phải trait bình thường.

Ý nghĩa:

> Một value có thể chuyển ownership từ execution context này sang execution context khác.

Ví dụ:

```axiom
struct Image {
    pixels: Buffer
    width: u32
    height: u32
}
```

Nếu `Buffer` là `Send`, compiler có thể suy ra:

```text
Image : Send
```

và:

```axiom
spawn {
    process(image)
}
```

hợp lệ.

---

# 4. Share

Tôi vẫn giữ `Share`, nhưng cần định nghĩa rất chặt.

`Share` nghĩa:

> Một giá trị có thể được nhiều execution context cùng giữ quyền truy cập **read-only** một cách an toàn.

Ví dụ conceptual:

```axiom
let config = Config.load()

spawn {
    read_config(config)
}

spawn {
    read_config(config)
}
```

Điều này chỉ hợp lệ nếu cơ chế chia sẻ của `config` thực sự cung cấp shared immutable access.

---

# 5. Send ≠ Share

Đây là distinction cực kỳ quan trọng.

| Property | Ý nghĩa |
|---|---|
| `Send` | chuyển ownership |
| `Share` | nhiều context cùng đọc |
| `Copy` | sao chép value |
| `Drop` | cần cleanup |
| `Sized` | kích thước xác định |

Ví dụ:

```text
int
```

có thể:

```text
Copy
Send
Share
Sized
```

Nhưng:

```text
Mutex<T>
```

có thể:

```text
Send
Share
```

trong khi bản thân `T` có thể không `Share`, vì `Mutex` cung cấp synchronization.

---

# 6. Không có mutable sharing tự do

Đây là invariant quan trọng nhất:

```text
READ + READ      OK
READ + WRITE     ERROR
WRITE + WRITE    ERROR
OWN + anything   ERROR
```

Ví dụ:

```axiom
let x = shared_data

spawn {
    x.read()
}

spawn {
    x.read()
}
```

OK nếu `x` có shared immutable semantics.

Nhưng:

```axiom
spawn {
    x.value = 10
}

spawn {
    x.value = 20
}
```

không được safe compiler chấp nhận nếu không có synchronization.

---

# 7. Mutex/RwLock/Atomic là library primitive

Không nên đưa:

```text
Mutex
RwLock
Atomic
Channel
Semaphore
Barrier
```

vào language core.

Chúng thuộc concurrency library.

Ví dụ:

```axiom
let counter = Mutex(0)

spawn {
    counter.lock().value += 1
}

spawn {
    counter.lock().value += 1
}
```

Compiler không cần biết implementation bên trong là:

```text
futex
spinlock
OS mutex
atomic CAS
```

Library/OS quyết định.

---

# 8. Atomic

Atomic là trường hợp đặc biệt.

Ví dụ:

```axiom
let counter = Atomic<u64>(0)

counter.fetch_add(1)
```

Không cần Mutex.

Compiler phải hiểu semantics của atomic operation đủ sâu để không reorder sai.

---

# 9. Memory ordering

Đây là chỗ tôi **không khuyên đơn giản hóa quá mức**.

Axiom vẫn cần memory ordering tương đương khả năng của hardware:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Nhưng API có thể thiết kế dễ dùng hơn C++.

Ví dụ conceptual:

```axiom
flag.store(true, Release)

while !flag.load(Acquire) {
    cpu_relax()
}
```

Không nhất thiết phải cho phép programmer sử dụng mọi memory order trong mọi API.

Có thể có:

```text
atomic.store(value)
atomic.load()
atomic.swap()
atomic.compare_exchange()
```

với default ordering an toàn/dễ hiểu, còn low-level programmer có thể chọn ordering explicit.

Điều này rất quan trọng để Axiom không hy sinh performance cho simplicity.

---

# 10. Channel

Channel nên là primitive library cực kỳ quan trọng.

Thay vì:

```text
shared memory
+ mutex
+ condition variable
```

Axiom khuyến khích:

```axiom
let (tx, rx) = channel<Work>()

spawn {
    tx.send(work)
}

let work = rx.receive()
```

`send()` có thể **move ownership**.

Do đó:

```axiom
tx.send(buffer)

use(buffer) // ERROR
```

Không cần reference counting.

Đây là một trong những cách Axiom có thể đạt concurrency an toàn mà vẫn đơn giản.

---

# 11. Thread

Thread là execution context cấp OS.

Conceptual API:

```axiom
let handle = thread.spawn(fn {
    process(data)
})

handle.join()
```

Compiler kiểm tra:

```text
captured values
      ↓
ownership
      ↓
Send
      ↓
thread boundary
```

Nếu capture không `Send`:

```text
AX_CON_0007
value cannot cross thread boundary
```

---

# 12. Closure + thread

Closure rất quan trọng.

Ví dụ:

```axiom
let image = load_image()

thread.spawn {
    encode(image)
}
```

Compiler coi closure environment tương đương conceptual:

```text
struct ClosureEnv {
    image: Image
}
```

Sau đó áp dụng ownership rules bình thường.

Không cần một hệ thống concurrency riêng cho closure.

---

# 13. Async

Async **không phải một loại thread**.

Đây là điểm tôi muốn đóng băng rõ.

```text
Thread
    = execution resource

Task
    = logical unit of work

Async
    = suspension/resumption mechanism

Executor
    = scheduler
```

Do đó:

```text
async function
```

không đồng nghĩa:

```text
new thread
```

---

# 14. Async lowering

Axiom compiler có thể biến:

```axiom
async fn download(url: String) -> Data {
    let connection = connect(url)
    let response = await connection.read()
    return response.data
}
```

thành conceptual state machine:

```text
State 0
  connect
      ↓
State 1
  wait
      ↓
State 2
  read
      ↓
State 3
  return
```

Compiler có thể tạo:

```text
struct DownloadState {
    state: u8
    connection: Connection
    ...
}
```

Nhưng đây chỉ là **compiler representation**.

Programmer không cần thấy nó.

---

# 15. Async không yêu cầu runtime bắt buộc

Một function:

```axiom
async fn foo()
```

chỉ mô tả khả năng suspension.

Executor có thể là:

```text
OS event loop
custom executor
GUI event loop
game engine
network runtime
embedded scheduler
single-thread loop
multi-thread pool
```

Axiom core không ép một implementation.

Đây là cách tránh vấn đề:

> "Muốn dùng async thì phải kéo theo một runtime 5 MB."

---

# 16. Async + ownership

Đây là phần rất quan trọng.

Nếu:

```axiom
async fn process(data: Buffer) {
    await io()

    use(data)
}
```

thì `data` phải tồn tại qua suspension point.

Compiler tự xác định:

```text
data
 ↓
live across await
 ↓
stored in async state
```

Không cần programmer viết lifetime.

---

# 17. Async migration giữa threads

Một task async có thể:

```text
Thread A
   ↓ await
executor
   ↓
Thread B
   ↓ resume
```

Nếu executor cho phép migration, state của task phải thỏa điều kiện cần thiết để chuyển thread.

Do đó:

```text
Task is Send
```

nếu nó có thể migrate.

Ngược lại có thể có:

```text
single-thread executor
```

cho phép task chứa state không `Send`.

Tôi đề xuất semantics:

```text
spawn(task)
```

mặc định là **potentially migratable**.

Nếu muốn task bị cố định:

```text
spawn_local(task)
```

hoặc tương đương.

Như vậy compiler biết chính xác boundary.

---

# 18. Structured concurrency

Tôi nghiêng về việc Axiom có **structured concurrency ở tầng thư viện**, không nhất thiết là core syntax.

Ví dụ conceptual:

```axiom
scope {
    spawn task_a
    spawn task_b
}
```

Khi scope kết thúc:

```text
child tasks
    ↓
must finish / cancel
    ↓
scope exits
```

Điều này giải quyết một vấn đề rất lớn của thread/task:

```text
function returns
    ↓
task vẫn chạy
    ↓
task giữ resource của function
```

Structured concurrency làm lifetime dễ hiểu hơn rất nhiều.

---

# 19. Detached task

Nhưng vẫn phải cho phép daemon/background task.

Ví dụ:

```axiom
detach(spawn background_service())
```

Lúc này programmer **explicitly** bỏ structured lifetime.

Compiler/library có thể yêu cầu task ownership độc lập.

Đây là nguyên tắc:

> nguy hiểm không bị cấm; nguy hiểm phải được biểu diễn rõ.

---

# 20. Cancellation

Cancellation không nên là "kill thread".

Async task nên có cooperative cancellation:

```text
request cancellation
        ↓
task observes cancellation
        ↓
cleanup
        ↓
Drop resources
        ↓
exit
```

Không nên có semantics:

```text
kill task immediately
```

vì có thể phá invariant resource.

---

# 21. Drop + concurrency

Ví dụ:

```axiom
let file = File.open(...)
let task = spawn {
    process(file)
}
```

ownership của `file` thuộc task.

Khi task kết thúc:

```text
task exit
   ↓
Drop(file)
```

Compiler phải đảm bảo cleanup deterministic.

Nếu task bị cancellation:

```text
cancel
 ↓
cleanup
 ↓
Drop
```

Không được:

```text
cancel
 ↓
memory/resource leaked arbitrarily
```

trong safe semantics.

---

# 22. Memory visibility

Axiom cần một **happens-before model**.

Ví dụ:

```axiom
x = 10

thread.spawn {
    print(x)
}
```

Nếu `x` được transfer ownership qua `spawn`, thì transfer boundary phải tạo đủ visibility guarantee.

Conceptually:

```text
Thread A
write x
   │
   │ ownership transfer
   ▼
Thread B
read x
```

Không được để compiler/CPU reorder thành trạng thái mà B nhìn thấy object chưa được publish đúng cách.

Tuy nhiên programmer không cần quản lý cache coherence.

---

# 23. Safe code và data race

Axiom định nghĩa:

> Safe code cannot contain a data race.

Data race:

```text
same memory
+ concurrent access
+ at least one write
+ no synchronization
```

Nếu compiler chứng minh được race → compile error.

Nếu code đi qua:

```axiom
unsafe {}
```

thì programmer chịu trách nhiệm.

---

# 24. Unsafe không tắt compiler hoàn toàn

Điểm này tôi muốn giữ rất mạnh.

Sai lầm thường gặp:

```text
unsafe = compiler không kiểm tra gì
```

Axiom không làm vậy.

`unsafe` chỉ cho phép những operations mà safe compiler không thể chứng minh.

Ví dụ:

```axiom
unsafe {
    let p: *mut u32 = ...
    *p = 10
}
```

Compiler vẫn kiểm tra:

```text
syntax
types
ABI
instruction validity
control flow
```

Nhưng không đảm bảo:

```text
p valid?
p points to initialized memory?
p aliases another mutable object?
```

Đó là trách nhiệm programmer.

---

# 25. Thread-safe library design

Một type có thể được thiết kế:

```text
struct Buffer
```

với:

```text
Buffer : Send
Buffer : !Share
```

Điều này rất hợp lý.

Nó có nghĩa:

```text
Thread A
    |
    | move
    ↓
Thread B
```

nhưng không:

```text
Thread A ──┐
           ├── same Buffer
Thread B ──┘
```

Nếu cần shared access:

```text
Shared<Buffer>
```

hoặc:

```text
Arc<Buffer>
```

hoặc một abstraction khác.

Nhưng đây là library-level design.

---

# 26. Vì sao không implicit Arc/GC?

Tôi cho rằng đây là quyết định rất quan trọng cho Axiom.

Nếu compiler tự động:

```text
capture object
 ↓
insert refcount
 ↓
atomic increment
 ↓
atomic decrement
```

thì một đoạn code tưởng như:

```axiom
spawn { process(data) }
```

có thể âm thầm tạo synchronization overhead.

Điều này đi ngược mục tiêu performance.

Axiom nên:

```text
Move → cheap
Share → explicit
Synchronization → explicit
```

---

# 27. Concurrency hierarchy

Kiến trúc tổng thể sẽ rất sạch:

```text
                 Axiom Concurrency
                         │
             ┌───────────┴───────────┐
             │                       │
          Parallel                Async
             │                       │
          Thread                   Task
             │                       │
             └───────────┬───────────┘
                         │
                    Ownership
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        Move           Share        Synchronize
          │              │              │
       Send          immutable     Mutex/Atomic/
                                    Channel
```

Compiler chỉ cần hiểu **ownership + boundary + synchronization semantics**.

Scheduler không cần nằm trong compiler semantics.

---

# 28. Core vs Library

Đây là ranh giới tôi đề xuất freeze:

| Thành phần | Core |
|---|---:|
| `Send` semantics | ✅ |
| `Share` semantics | ✅ |
| ownership across task/thread | ✅ |
| data-race rules | ✅ |
| memory visibility | ✅ |
| atomic semantic model | ✅ |
| Thread API | ❌ |
| Mutex | ❌ |
| RwLock | ❌ |
| Channel | ❌ |
| ThreadPool | ❌ |
| Executor | ❌ |
| Scheduler | ❌ |
| Async lowering | ✅ compiler |
| Async runtime | ❌ |
| GUI event loop | ❌ |
| OS thread API | ❌ |

Điều này rất hợp với mục tiêu **core nhỏ nhưng compiler mạnh**.

---

# 29. Các invariant mới

Tôi đề xuất đóng băng các invariant sau:

```text
ACON-01
Safe code has no data races.

ACON-02
Ownership transfer across concurrency boundaries requires Send.

ACON-03
Shared immutable access requires Share-compatible semantics.

ACON-04
Mutable shared state requires explicit synchronization.

ACON-05
Thread and async task use the same ownership model.

ACON-06
Async suspension preserves the lifetime of values live across suspension.

ACON-07
Async does not imply thread creation.

ACON-08
The language core does not mandate an executor or scheduler.

ACON-09
Cancellation cannot arbitrarily violate deterministic resource cleanup.

ACON-10
Unsafe may bypass memory-safety guarantees but does not disable type checking.

ACON-11
Synchronization semantics must define memory visibility.

ACON-12
Atomic operations have explicit memory-order semantics.

ACON-13
Channels may transfer ownership without shared mutable memory.

ACON-14
No implicit GC/RC is inserted merely because a value crosses a concurrency boundary.

ACON-15
Safe concurrency semantics must not require a mandatory runtime.
```

---

# 30. Test cases

### `send_001`

```axiom
let buffer = Buffer(...)

spawn {
    consume(buffer)
}

consume(buffer)
```

Expected:

```text
ERROR: value moved into spawned task
```

---

### `share_001`

```axiom
let config = SharedConfig(...)

spawn {
    print(config.name)
}

spawn {
    print(config.name)
}
```

Expected:

```text
SUCCESS
```

---

### `race_001`

```axiom
let x = 0

spawn {
    x += 1
}

spawn {
    x += 1
}
```

Expected:

```text
ERROR: conflicting concurrent mutable access
```

---

### `mutex_001`

```axiom
let x = Mutex(0)

spawn {
    x.lock().value += 1
}

spawn {
    x.lock().value += 1
}
```

Expected:

```text
SUCCESS
```

---

### `channel_001`

```axiom
let (tx, rx) = channel()

let data = Buffer(...)

spawn {
    tx.send(data)
}

let received = rx.receive()
```

Expected:

```text
SUCCESS
```

`data` ownership moves.

---

### `async_001`

```axiom
async fn process(data: Buffer) {
    await io()
    consume(data)
}
```

Expected:

```text
SUCCESS
```

`data` được lưu trong async state machine.

---

### `async_send_001`

Nếu task có thể migrate:

```axiom
spawn(process(data))
```

compiler yêu cầu state của task phù hợp với migration.

---

# 31. Một điểm tôi muốn thay đổi so với cách thiết kế ban đầu

Tôi **không muốn Axiom có quá nhiều loại reference/concurrency type**.

Không nên xuất hiện một đống thứ kiểu:

```text
&T
&mut T
&T + 'a
Arc<T>
Rc<T>
Weak<T>
MutexGuard<'a, T>
RwLockReadGuard<'a, T>
...
```

ở tầng ngôn ngữ.

Axiom nên giữ programmer-facing model gần:

```text
Value
Owned Value
view<T>
mut_view<T>
Shared<T>
```

và:

```text
Send
Share
```

Compiler tự xử lý phần còn lại.

Đây chính là chỗ Axiom có thể khác Rust:

> **Compiler vẫn làm phân tích ownership/alias/lifetime rất sâu, nhưng programmer không phải viết ra toàn bộ kết quả của phân tích đó.**

---

# 32. Kết quả kiến trúc hiện tại

Sau Core + Memory + Type + Concurrency, Axiom bắt đầu có một nền rất rõ:

```text
                    AXIOM
                      │
       ┌──────────────┼──────────────┐
       │              │              │
      TYPE          MEMORY       CONCURRENCY
       │              │              │
   struct/enum      ownership       Send
   trait            move            Share
   generic          view            atomic
   closure          drop            race-free
       │              │              │
       └──────────────┼──────────────┘
                      │
                    MIR
                      │
          ┌───────────┼───────────┐
          │           │           │
       optimize     async       unsafe
          │           │           │
          └───────────┼───────────┘
                      │
                  Axiom LIR
                      │
               Native Machine Code
```

Và quan trọng nhất:

**Axiom không cần class, GC, exception runtime, object header, implicit reference counting, mandatory async runtime hay borrow syntax để đạt được mô hình này.**

Bước tiếp theo tôi khuyên chuyển sang **`AXIOM-COMPILER-CONTRACT-v0.1` + thiết kế MIR chính thức**. Đây mới là nơi chúng ta kiểm chứng xem các quyết định Core/Memory/Type/Concurrency ở trên **có thực sự compile được thành machine code hiệu năng cao hay chỉ đẹp trên giấy**.