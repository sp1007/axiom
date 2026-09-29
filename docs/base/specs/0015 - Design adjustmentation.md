Tiếp tục từ điểm đang dở: **đừng thêm feature mới ngay**. Với Axiom hiện tại, bước quan trọng nhất là biến các quyết định đã có thành **testable semantics**.

Tôi đề xuất đi tiếp theo thứ tự này:

### 1. Khóa Formal Test Suite v0.1

Đây sẽ là “hợp đồng” giữa spec và compiler.

Ví dụ:

```axiom
// ownership/move_basic.ax

fn consume(x: Vec<i32>) {}

fn main() {
    let a = Vec.new<i32>()
    consume(a)

    print(a)   // ERROR: moved value
}
```

Compiler phải trả về một diagnostic ổn định kiểu:

```text
AX_OWN_0001
use of moved value

value: a
state: MOVED
moved_at: consume(a)
used_at: print(a)
```

Không chỉ kiểm tra compiler có báo lỗi, mà test còn kiểm tra **semantic state**.

---

### 2. Đặc biệt kiểm tra `view` — đây là điểm khó nhất

Ví dụ:

```axiom
fn first(v: view<i32>) -> i32 {
    v[0]
}

fn main() {
    var a = [1, 2, 3]

    let v = view(a)

    print(first(v))
}
```

→ hợp lệ.

Nhưng:

```axiom
fn bad() -> view<i32> {
    var a = [1, 2, 3]
    view(a)
}
```

→ phải reject vì `a` chết khi function kết thúc.

Điểm quan trọng là **programmer không viết lifetime**.

Compiler tự suy ra:

```text
a
├── lifetime: [init → return]
└── v
    └── lifetime: [view(a) → return]  ← vượt owner
```

Diagnostic nên chỉ ra **nguyên nhân**, không bắt người dùng học borrow-checker syntax.

---

### 3. Kiểm tra trường hợp khó hơn: reallocation

Đây mới là test quyết định Axiom có thực sự đơn giản hơn Rust/C++ hay không.

```axiom
fn test() {
    var v = Vec.new<i32>()

    v.push(1)
    v.push(2)

    let x = view(v)

    v.push(3)

    print(x)
}
```

Compiler phải phát hiện:

```text
x có thể trỏ vào storage cũ
v.push(3) có thể reallocate
```

→ reject.

Nhưng nếu compiler chứng minh được capacity còn đủ:

```axiom
var v = Vec.with_capacity<i32>(100)

let x = view(v)

v.push(3)

print(x)
```

thì **không nhất thiết** phải reject chỉ vì `push`.

Đây là nơi Axiom có thể khác biệt:

> Không bắt programmer quản lý lifetime bằng annotation; compiler phân tích khả năng invalidation thực tế.

---

### 4. Sau đó kiểm tra `Drop`

Ví dụ:

```axiom
struct File {
    handle: Handle
}

fn test() {
    let a = File.open("a")
    let b = File.open("b")

    return
}
```

Semantic cleanup:

```text
return
  ↓
drop(b)
  ↓
drop(a)
  ↓
return
```

Nhưng physical code có thể được optimizer biến thành một sequence hoàn toàn khác miễn observable semantics giống nhau.

Điều này rất quan trọng với mục tiêu hiệu năng của Axiom:

```text
SOURCE
  ↓
semantic Drop
  ↓
cleanup region
  ↓
optimizer
  ↓
actual machine cleanup
```

**Drop là semantic guarantee, không phải lời gọi destructor bắt buộc xuất hiện trong machine code.**

---

### 5. Kiểm tra conditional initialization

Ví dụ:

```axiom
fn test(flag: bool) {
    let file

    if flag {
        file = File.open("x")
    }

    return
}
```

Compiler không được:

```text
drop(file)
```

nếu `file` chưa được khởi tạo.

MIR cần có trạng thái kiểu:

```text
file:
    UNINIT
       │
       ├── if false ──> UNINIT
       │
       └── if true ───> OWNED
```

Cleanup:

```text
if OWNED:
    DROP file
```

Optimizer sau đó có thể đơn giản hóa.

Đây là một trong những lý do tôi muốn **ownership state nằm trong MIR**, thay vì cố nhồi toàn bộ logic vào type checker.

---

## 6. Tiếp theo là `Send/Share`

Axiom nên giữ một nguyên tắc rất rõ:

```text
Copy
Send
Share
Drop
Sized
```

**không phải cùng một khái niệm.**

Ví dụ:

```axiom
let data = Vec.new<i32>()

spawn(fn() {
    process(data)
})
```

Compiler kiểm tra:

```text
data
 └── Vec<i32>
       ├── Send   ✓
       ├── Share  ?
       └── Copy   ✗
```

Nếu spawn chuyển ownership:

```text
MOVE(data)
      ↓
new task owns data
```

thì `Send` là đủ.

Nhưng:

```axiom
spawn(fn() {
    read(data)
})

read(data)
```

nếu `data` được dùng đồng thời thì cần semantics `Share`.

Do đó:

```text
Send ≠ Share
```

Đây là một quyết định rất đáng giữ.

---

# 7. Một điểm tôi muốn điều chỉnh nhẹ trong thiết kế hiện tại

Có một nguy cơ:

> Nếu Axiom cố chứng minh mọi alias/lifetime/concurrency bằng static analysis quá mạnh, compiler sẽ trở thành một “Rust compiler nhưng giấu borrow syntax”.

Đó **không phải** mục tiêu chúng ta muốn.

Axiom nên có ba tầng:

```text
                 Axiom
                   │
        ┌──────────┴──────────┐
        │                     │
      SAFE                  UNSAFE
        │                     │
 compiler proves          programmer guarantees
        │                     │
 ownership              raw pointer
 lifetime               address
 alias                  hardware
 Send/Share             FFI tricks
 race freedom
```

Nhưng `unsafe` không nên biến thành:

> “từ giờ compiler bỏ mặc mọi thứ”.

Ví dụ:

```axiom
unsafe {
    let p: *mut i32 = ...
}
```

Compiler vẫn phải biết:

```text
p : *mut i32
```

và vẫn type-check:

```axiom
*p = "hello"   // type error
```

`unsafe` chỉ chuyển trách nhiệm **memory validity** sang programmer.

---

# 8. Và đây là điểm rất quan trọng cho mục tiêu “hiệu năng hơn C/C++”

Axiom không nên cố đảm bảo:

> “mọi abstraction đều nhanh bằng code C viết tay”.

Mục tiêu thực tế hơn và mạnh hơn:

> **Axiom phải cho compiler đủ thông tin để biến abstraction thành code tương đương với implementation tối ưu bằng C/C++.**

Ví dụ:

```axiom
fn sum(v: view<i32>) -> i32 {
    var total = 0

    for x in v {
        total += x
    }

    total
}
```

Semantic representation:

```text
view<i32>
    base
    length
```

MIR có thể là:

```text
i = 0
sum = 0

loop:
    if i >= length -> exit

    x = load(base + i * 4)
    sum += x
    i += 1

    goto loop
```

Optimizer có thể tiếp tục:

```text
bounds-check elimination
+
loop optimization
+
vectorization
+
register allocation
```

Machine code cuối cùng **không cần có object `view` nào cả**.

Đây chính là:

> **semantic abstraction ≠ physical abstraction**

và tôi nghĩ đây nên trở thành một trong những nguyên tắc trung tâm của Axiom.

---

# 9. Sau Formal Test Suite, tôi đề xuất khóa thêm một tầng

Ta sẽ có:

```text
AXIOM SPEC
    │
    ├── Core
    ├── Memory
    ├── Type
    ├── Concurrency
    ├── ABI
    └── Error
          │
          ▼
SEMANTIC TEST SUITE
          │
          ▼
HIR
          │
          ▼
MIR
          │
          ▼
VERIFIED MIR
          │
          ▼
OPTIMIZER
          │
          ▼
MACHINE CODE
```

Và **Verified MIR phải trở thành boundary cực kỳ quan trọng**.

Trước boundary:

```text
compiler đang chứng minh chương trình hợp lệ
```

Sau boundary:

```text
optimizer được tự do biến đổi representation
```

với invariant:

```text
observable semantics không thay đổi
```

Điều này giúp Axiom tránh một vấn đề rất lớn khi compiler ngày càng phức tạp: **semantic correctness bị trộn lẫn với optimization correctness**.

---

## 10. Thứ tự xây Axiom mà tôi khuyên dùng lúc này

Không phải:

```text
parser
→ compiler
→ thêm feature
→ sửa bug
→ thêm feature
```

mà là:

```text
                  AXIOM SPEC
                      │
                      ▼
              SEMANTIC TESTS
                      │
                      ▼
                  TYPE CORE
                      │
                      ▼
                    HIR
                      │
                      ▼
                    MIR
                      │
              ┌───────┴───────┐
              ▼               ▼
        OWNERSHIP          CONTROL FLOW
              │               │
              └───────┬───────┘
                      ▼
               VERIFIED MIR
                      │
                      ▼
                SIMPLE CODEGEN
                      │
                      ▼
                 EXECUTABLE
                      │
                      ▼
                 OPTIMIZER
```

**Chưa cần GUI, package manager, async runtime, standard library lớn, IDE...**

Trước tiên phải chứng minh được 5 thứ:

1. `struct`
2. `function`
3. `ownership/move`
4. `view`
5. `Drop`

chạy đúng từ source → native executable.

Sau đó mới đưa `trait/generic`, rồi concurrency, rồi async.

Tôi nghĩ đây là mốc quan trọng: **Axiom hiện đã đủ nhiều ý tưởng để bắt đầu “đóng băng semantics” thay vì tiếp tục brainstorm feature.**