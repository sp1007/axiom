Đúng. Bây giờ nên đi vào phần **khó nhất của Axiom compiler: MIR + Ownership Verifier**. Tôi sẽ coi đây là **AXIOM MIR v0.1**, kế thừa semantic freeze vừa rồi.

# AXIOM MIR v0.1

Mục tiêu của MIR không phải là “IR giống LLVM”.

MIR phải biểu diễn chính xác những gì Axiom cần chứng minh:

```text
type
control flow
ownership
access
resource lifetime
alias/view
concurrency
cleanup
```

Sau khi qua verifier, optimizer mới được phép tự do biến đổi representation.

---

# 1. MIR có 3 loại thông tin

Tôi đề xuất tách rõ:

```text
MIR
├── Value state
├── Resource state
└── Control-flow state
```

### Value state

```text
i32
f64
Point
Vec<i32>
view<i32>
...
```

### Resource state

```text
UNINIT
OWNED
MOVED
DROPPED
```

### Control-flow state

```text
basic block
branch
return
panic
trap
suspend
```

Điểm quan trọng:

> **SSA quản lý value; ownership state không nhất thiết phải là SSA.**

Đây là lý do tôi vẫn giữ quan điểm Axiom MIR nên là **hybrid SSA + ownership graph**, thay vì pure SSA.

---

# 2. MIR instruction set

Bộ tối thiểu:

```text
CONST
COPY
MOVE

FIELD
INDEX

LOAD
STORE

VIEW
VIEW_MUT

CALL
RETURN

BRANCH
SWITCH
PHI

ALLOC
DEALLOC
DROP

ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS

SPAWN
SEND
RECEIVE

SUSPEND
RESUME

PANIC
TRAP
```

Nhưng có một điểm quan trọng:

`ALLOC` **không có nghĩa là malloc**.

Nó có nghĩa:

> tạo storage/resource theo semantic requirement.

Backend có thể biến nó thành:

```text
register
stack
inline
heap
arena
nothing
```

---

# 3. Ví dụ source → MIR

Source:

```axiom id="s0l2n1"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

MIR:

```text id="0jzv8c"
fn add(a: i32, b: i32) -> i32

bb0:
    %r0 = ADD %a, %b
    RETURN %r0
```

Rất đơn giản.

---

# 4. Move

Source:

```axiom id="2g9wzi"
fn test() {
    let x = make_buffer()
    consume(x)
}
```

MIR:

```text id="av1l6m"
bb0:
    %x = CALL make_buffer()
    MOVE %x -> %arg0
    CALL consume(%arg0)
    RETURN
```

Ownership state:

```text id="b8y02e"
%x:
    UNINIT
      ↓
    OWNED
      ↓
    MOVED
```

Sau `MOVE`, `%x` không còn usable.

---

# 5. Copy

```axiom id="u5e4b7x"
let a = 10
let b = a
```

MIR:

```text id="g89c4r"
%a = CONST i32 10
%b = COPY %a
```

Ownership:

```text id="v2b6dx"
%a = OWNED/COPYABLE
%b = OWNED/COPYABLE
```

Không có move state transition.

---

# 6. Place

`Place` không cần xuất hiện trong source.

Nó cực kỳ hữu ích trong MIR.

Ví dụ:

```axiom id="1d4s78"
p.x = 10
```

MIR:

```text id="t5k0dn"
%px = FIELD_PLACE %p, x
STORE %px, 10
```

Hoặc:

```text id="5b5r3x"
a[i] = 10
```

→

```text id="6u5hzo"
%p = INDEX_PLACE %a, %i
STORE %p, 10
```

`Place` cho phép verifier biết **chính xác vùng nào đang được accessed**.

---

# 7. Đây là chìa khóa để xử lý alias

Ví dụ:

```axiom id="r5j6xv"
let a = view(x)
let b = view(x)
```

Verifier có thể biểu diễn:

```text id="t6qv5r"
a → region R
b → region R
```

Hai READ:

```text id="3cgj1v"
READ(R)
READ(R)
```

→ OK.

Nhưng:

```axiom id="h9a2yq"
let a = view(x)
let b = mut_view(x)
```

thành:

```text id="4f0p0f"
READ(R)
WRITE(R)
```

→ conflict.

---

# 8. Region là abstraction nội bộ

Tôi đề xuất MIR có khái niệm:

```text id="smx6hb"
MemoryRegion
```

Ví dụ:

```text id="jyf9mi"
x
 └── Region #12

view(x)
 └── Region #12

x.field
 └── Region #13
```

Region không phải runtime object.

Nó chỉ tồn tại trong compiler.

Điều này giúp Axiom xử lý:

```text
field aliasing
array slices
views
partial mutation
```

mà không cần expose borrow syntax cho programmer.

---

# 9. Ownership verifier

Verifier chạy sau Typed MIR.

Nó phải kiểm tra:

```text id="6rv9hy"
V1: definite initialization
V2: use-after-move
V3: use-after-drop
V4: double-drop
V5: view lifetime
V6: mutable alias conflict
V7: ownership transfer
V8: Send
V9: Share
V10: cleanup completeness
```

---

# 10. Definite initialization

Ví dụ:

```axiom id="lxy3un"
let x

if condition {
    x = Resource()
}

use(x)
```

Control-flow:

```text id="u4p6ps"
          bb0
           │
       condition
       /         \
     bb1         bb2
      │           │
   x=OWNED      x=UNINIT
       \         /
        \       /
          bb3
           │
         use(x)
```

Verifier thấy:

```text id="qydr3g"
OWNED ∩ UNINIT
```

không tạo ra definite `OWNED`.

→ compile error.

---

# 11. Nhưng Drop phải khác

Nếu:

```axiom id="8z0b6v"
let x

if condition {
    x = Resource()
}
```

ra khỏi scope:

```text id="3z3w4f"
bb3:
    conditional_drop(x)
```

MIR:

```text id="m6kzq5"
DROP_IF_OWNED %x
```

Sau đó optimizer có thể simplify.

---

# 12. Cleanup graph

Đây là một phần tôi muốn Axiom làm tốt hơn C++.

Mỗi scope có cleanup region.

Ví dụ:

```axiom id="pxf3gk"
fn f() {
    let a = A()
    let b = B()

    if x {
        return
    }

    work()
}
```

Compiler tạo:

```text id="c5b1tc"
scope S1
│
├── a
├── b
│
├── normal exit
│     ↓
│   drop(b)
│   drop(a)
│
└── early return
      ↓
    drop(b)
    drop(a)
    return
```

Sau canonicalization:

```text id="v9y0d8"
multiple exits
      ↓
cleanup block
      ↓
return
```

Điều này làm optimizer dễ hơn rất nhiều.

---

# 13. View phải mang theo provenance

Tôi muốn thêm một thuộc tính nội bộ:

```text id="8f3xqu"
VIEW_PROVENANCE
```

Ví dụ:

```axiom id="h1v8pp"
let x = view(a)
```

MIR:

```text id="g1v7jp"
%v = VIEW
     base = %a
     region = R12
     provenance = %a
```

Compiler biết:

```text id="6g3w0v"
v thuộc storage của a
```

Nếu:

```axiom id="y0k2gc"
destroy(a)
use(v)
```

→ reject.

---

# 14. Vec reallocation

Ví dụ:

```axiom id="c4n8wl"
let x = view(v)

v.push(10)

use(x)
```

`push` có semantic effect:

```text id="1w6r8n"
MAY_INVALIDATE(v.storage)
```

Verifier thấy:

```text id="g1f7qv"
x → Region R1

push(v)
→ R1 may become invalid
```

Sau đó:

```text id="jj8j7f"
use(x)
```

→ reject.

Nếu optimizer/prover chứng minh `push` không reallocate:

```text id="g1q4o8"
capacity sufficient
```

thì invalidation event có thể được loại bỏ.

---

# 15. Đây là điểm rất hay của Axiom

Compiler không cần bảo thủ kiểu:

```text
"Vec.push luôn invalidates mọi view"
```

Nó có thể reason:

```text
old capacity = 100
length = 20
push = 1
```

→ no reallocation.

Do đó:

```text id="t8z9i4"
view remains valid
```

Đây là **proof-based safety**, không phải rule-based restriction.

---

# 16. Nhưng không được biến compiler thành theorem prover vô hạn

Đây là giới hạn quan trọng.

Axiom compiler nên có:

```text id="5m9k4y"
sound analysis
```

nhưng không yêu cầu:

```text id="4v2xqp"
complete analysis
```

Tức là:

> Nếu compiler chứng minh được → accept.

> Nếu compiler không chứng minh được → reject hoặc yêu cầu explicit unsafe/alternative API.

Không được đoán.

Nhưng chúng ta cũng không nên biến mọi trường hợp khó thành lỗi vô lý.

Về lâu dài có thể bổ sung các analysis mạnh hơn mà **không thay đổi language semantics**.

---

# 17. Ownership transfer qua function

Source:

```axiom id="3s8n9c"
consume(x)
```

Nếu parameter:

```axiom id="9z6yq2"
fn consume(x: Buffer)
```

thì HIR/MIR biết đây là:

```text id="s1zjbi"
OWNERSHIP TRANSFER
```

Không cần programmer viết:

```text
move x
```

`move` nếu có chỉ là explicit assertion/diagnostic aid.

---

# 18. `view` parameter

```axiom id="m3w8nz"
fn read(v: view<i32>)
```

Call:

```axiom id="v8u0h4"
read(a)
```

Compiler có thể tạo view tạm thời:

```text id="f3q1zm"
TEMP_VIEW(a)
CALL read
END_VIEW
```

Không cần programmer viết:

```text
view(a)
```

trong trường hợp compiler có thể infer conversion an toàn.

Điều này giúp syntax thực sự đơn giản.

---

# 19. Mutable receiver

Source:

```axiom id="v2p6w9"
v.normalize()
```

Nếu:

```text id="d5x3q7"
fn normalize(self: mut_view<Vec2>)
```

MIR:

```text id="3l8j4k"
%v_mut = MUT_VIEW %v
CALL normalize(%v_mut)
```

Verifier đảm bảo không có conflicting READ/WRITE trong thời gian call.

---

# 20. Function calls là semantic barriers có điều kiện

Đây là chỗ khó.

Ví dụ:

```axiom id="s5d7h1"
use(x)
use(y)
```

Compiler phải biết function `use` có:

```text id="6c7w8m"
READ
WRITE
MOVE
```

đối với argument.

Typed HIR/MIR phải có effect/access summary.

Ví dụ:

```text id="7gq2k9"
fn read(x: view<T>)
    effect = READ

fn modify(x: mut_view<T>)
    effect = WRITE

fn consume(x: T)
    effect = MOVE
```

---

# 21. Tôi đề xuất thêm Function Effect Summary

Không phải effect system khổng lồ.

Chỉ cần compiler nội bộ tracking:

```text id="9y6t0a"
READ
WRITE
MOVE
ALLOC
DROP
PANIC
IO
ATOMIC
SUSPEND
```

Ví dụ:

```text id="5l2z6d"
read:
    READ

modify:
    READ + WRITE

consume:
    MOVE + DROP

print:
    IO
```

Sau này optimizer cũng dùng được thông tin này.

---

# 22. Async MIR

Source:

```axiom id="9q7c4w"
async fn fetch() {
    let x = load()
    await network()
    use(x)
}
```

Lower:

```text id="7z4p8m"
state 0:
    x = CALL load
    state = 1
    SUSPEND

state 1:
    RESUME
    use(x)
    DROP x
    RETURN
```

Async frame conceptually:

```text id="f0r7ne"
Frame {
    state
    x
}
```

Nhưng frame allocation:

```text id="c3t5ha"
heap?
stack?
inline?
caller?
```

không phải semantic guarantee.

---

# 23. Send checking async

Nếu executor có thể migrate task:

```text id="6c7v9j"
state frame
     ↓
thread A
     ↓
await
     ↓
thread B
```

mọi captured state sống qua suspension phải đáp ứng `Send`.

Verifier kiểm tra:

```text id="q2x5v1"
Frame : Send
```

Nếu không:

```text id="8y5z1c"
spawn(...)
```

→ reject.

---

# 24. Verified MIR invariant

Tại thời điểm verifier hoàn thành:

```text id="f9d2m6"
VERIFIED MIR guarantees:

1. definite initialization
2. no use-after-move
3. no double-drop
4. no use-after-drop
5. no dangling safe view
6. no conflicting safe mutable alias
7. Send constraints satisfied
8. Share constraints satisfied
9. cleanup paths complete
10. control flow well-typed
11. atomic operations semantically valid
12. async suspension state valid
```

Đây là **trust boundary** của optimizer.

---

# 25. Optimizer từ đây trở đi được “tàn bạo”

Sau Verified MIR:

```text id="5u3q2j"
INLINE
DCE
CSE
SROA
ESCAPE ANALYSIS
SCALAR REPLACEMENT
LOOP OPTIMIZATION
VECTORIZE
DEAD STORE ELIMINATION
BOUNDS CHECK ELIMINATION
TAIL CALL
CONSTANT PROPAGATION
SPECIALIZATION
```

miễn:

```text id="5w7r9e"
observable semantics preserved
```

Đặc biệt:

```text id="p0c7h1"
ownership metadata
```

có thể được loại bỏ dần sau khi không còn cần cho correctness.

---

# 26. Và đây chính là kiến trúc tôi muốn khóa

```text
                    AXIOM SOURCE
                         │
                         ▼
                       AST
                         │
                         ▼
                       HIR
                         │
              ┌──────────┴──────────┐
              │                     │
           TYPE                    EFFECT
              │                     │
              └──────────┬──────────┘
                         ▼
                       MIR
                         │
             ┌───────────┼───────────┐
             │           │           │
         Ownership     Alias      Concurrency
             │           │           │
             └───────────┼───────────┘
                         ▼
                 DROP ELABORATION
                         │
                         ▼
                  MIR VERIFIER
                         │
                         ▼
                  VERIFIED MIR
                         │
               ╔═════════╧═════════╗
               ║ SEMANTIC BOUNDARY ║
               ╚═════════╤═════════╝
                         │
                         ▼
                     OPTIMIZER
                         │
                         ▼
                       LIR
                         │
                         ▼
                    MACHINE IR
                         │
                         ▼
                   NATIVE CODE
```

### Một quyết định tôi cho rằng rất đáng giữ

**Không để LLVM trở thành semantic verifier của Axiom.**

LLVM có thể là backend/bootstrap:

```text
Axiom MIR
   ↓
LLVM IR
   ↓
LLVM
```

nhưng semantic correctness đã phải được Axiom chứng minh **trước đó**.

Sau này khi Axiom tự viết backend:

```text
Axiom MIR
   ↓
Axiom LIR
   ↓
x86-64 / ARM64 / RISC-V / WASM
```

hoàn toàn không cần LLVM.

---

Bước tiếp theo sau MIR là **đóng băng `AXIOM EFFECT + OWNERSHIP VERIFIER v0.1`**. Đây mới là nơi ta phải giải quyết những ca cực khó như **function call có alias, field-level ownership, loop, closure capture, recursion, generic function, `Vec` invalidation và async frame**. Nếu làm được phần này, kiến trúc compiler của Axiom về cơ bản đã có “bộ não semantics”; parser/backend sau đó tương đối thẳng.