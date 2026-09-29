Đúng. Và tôi nghĩ ý tưởng đó **vẫn rất đáng giữ**, thậm chí nó phù hợp hoàn toàn với định hướng mới: **không cố giảm Core bằng mọi giá, mà giảm complexity mà programmer phải đối mặt.**

Đặc biệt với `thread / async / parallelism`, tôi nghĩ Axiom có thể làm khác khá nhiều so với C++/Rust/JavaScript.

### Vấn đề hiện tại

Các ngôn ngữ thường tách thành rất nhiều khái niệm:

```text
thread
async function
await
future
promise
task
executor
runtime
event loop
mutex
condition variable
channel
thread pool
atomic
```

Trong khi nhu cầu thực tế thường chỉ là:

> "Tôi muốn đoạn code này chạy đồng thời."

---

# Axiom có thể thống nhất chúng

Ví dụ:

```axiom
spawn {
    calculate()
}
```

Compiler/runtime tự quyết định cách thực thi.

Có thể là:

```text
OS thread
    ↓
worker thread

task
    ↓
thread pool

async I/O
    ↓
event-driven

GPU
    ↓
GPU queue
```

Programmer không nhất thiết phải chọn ngay từ đầu.

---

## Nhưng vẫn cho phép kiểm soát

Khi cần kiểm soát:

```axiom
thread {
    realtime_audio()
}
```

hoặc:

```axiom
parallel {
    process_a()
    process_b()
    process_c()
}
```

và:

```axiom
await result
```

Những từ khóa này không nhất thiết tương ứng 1:1 với một implementation cụ thể.

---

# Tôi đặc biệt thích mô hình này

```axiom
fn work() {
    ...
}

spawn work()
```

và nếu cần kết quả:

```axiom
result := spawn calculate()
...
value := await result
```

Như vậy **async function không nhất thiết phải là một loại function khác**.

Không cần:

```axiom
async fn calculate() -> Future<Result<T>>
```

mà chỉ có:

```axiom
fn calculate() -> T
```

và **execution context** quyết định nó chạy đồng bộ hay bất đồng bộ.

Đây là một abstraction rất đẹp.

---

# Parallel cũng có thể là primitive riêng

Ví dụ:

```axiom
parallel {
    a := task_a()
    b := task_b()
    c := task_c()
}

use(a, b, c)
```

Compiler có thể phát hiện dependency.

Nếu:

```text
a ──┐
b ──┼──→ result
c ──┘
```

thì chạy song song.

Nếu máy chỉ có một core:

→ compiler/runtime có thể chạy tuần tự.

Không cần programmer viết:

```text
thread pool
join
future
mutex...
```

---

# Nhưng tôi sẽ không giấu concurrency primitives thấp tầng

Axiom vẫn cần:

```text
atomic
mutex
rwlock
semaphore
channel
barrier
thread
```

cho những người viết engine/runtime.

Điểm khác biệt là:

> **Chúng không phải thứ programmer thông thường bắt buộc phải học ngay từ đầu.**

---

## Và đây liên quan trực tiếp tới triết lý Axiom mà chúng ta vừa thống nhất

Không phải:

> "Xóa async vì nó làm Core lớn."

Mà là:

> **"Thiết kế concurrency sao cho programmer không phải học 7 mô hình khác nhau để làm cùng một việc."**

Đây chính là kiểu đơn giản hóa tôi nghĩ Axiom nên theo đuổi.

### Có thể gom lại thành:

```text
             EXECUTION
                 │
       ┌─────────┼─────────┐
       ↓         ↓         ↓
     normal     spawn    parallel
       │         │         │
    sequential  async    parallel
                 │
          compiler/runtime
                 │
       ┌─────────┼─────────┐
       ↓         ↓         ↓
    thread     pool      event
```

Programmer nhìn thấy **một mô hình đơn giản**.

Compiler/runtime chịu trách nhiệm biến nó thành mô hình phù hợp với platform.

Và đây chính là một trong những nơi tôi nghĩ Axiom có thể đạt được mục tiêu **"đơn giản hơn Rust/C++ nhưng không hy sinh khả năng hệ thống"** rất rõ ràng.