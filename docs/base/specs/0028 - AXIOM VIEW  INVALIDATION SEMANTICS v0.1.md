Tiếp tục. Ta sẽ **đóng 3 điểm semantic còn hở**, vì nếu không chốt chúng thì Verifier không thể có đặc tả ổn định.

Tôi đề xuất thêm một nguyên tắc:

> **Axiom ưu tiên implicit ở nơi compiler có thể chứng minh duy nhất và an toàn; explicit ở nơi thay đổi capability/lifetime theo cách programmer cần nhìn thấy.**

---

# AXIOM VIEW / INVALIDATION SEMANTICS v0.1

## 1. Có nên tự động chuyển Value → `view<T>`?

Tôi đề xuất **CÓ, nhưng chỉ đối với ephemeral view trong một biểu thức/call**.

Ví dụ:

```axiom
fn sum(v: view<i32>) -> i32 {
    ...
}

let numbers = Vec<i32>(...)
let x = sum(numbers)
```

Compiler hiểu tương đương semantic:

```text
numbers
   │
   └── ephemeral READ view
            │
            └── sum()
                   │
                   └── view kết thúc
```

Programmer **không cần viết**:

```axiom
sum(view(numbers))
```

---

## 2. Nhưng binding một view phải explicit

Nếu muốn giữ capability:

```axiom
let v = view(numbers)
```

phải viết rõ.

Tức:

| Trường hợp | Syntax |
|---|---|
| truyền vào `view<T>` | implicit |
| tạo view local lâu hơn expression | `view(x)` |
| tạo mutable view | `mut_view(x)` |
| raw pointer | explicit + unsafe |

Điều này tạo một ranh giới rất đẹp:

```text
temporary capability → compiler tự quản lý
persistent capability → programmer nhìn thấy
```

---

# 3. Tại sao không cho `let v = numbers` tự biến thành view?

Không nên.

Ví dụ:

```axiom
let a = numbers
```

phải luôn giữ semantics value/ownership bình thường.

Nếu compiler tùy ý quyết định:

```text
a = MOVE(numbers)
```

hoặc:

```text
a = view(numbers)
```

thì source trở nên khó dự đoán.

Do đó:

```text
VALUE → VALUE
```

là semantics mặc định.

Chỉ khi **expected type yêu cầu view**:

```text
fn foo(v: view<T>)
```

compiler mới thực hiện implicit ephemeral view.

---

# 4. Conversion rule chính thức

Đề xuất:

```text
OWNED<T>
    ├── expected T       → MOVE/COPY theo T
    ├── expected view<T> → ephemeral READ capability
    └── expected mut_view<T>
             → ephemeral WRITE capability
```

Nhưng có điều kiện.

### `view<T>`

Được implicit từ:

```text
OWNED<T>
mut_view<T>
view<T>
```

với capability READ.

### `mut_view<T>`

Chỉ được tạo từ:

```text
OWNED<T>
```

hoặc một capability mutable tương thích.

Không được:

```text
view<T> → mut_view<T>
```

---

# 5. Ví dụ

```axiom
fn inspect(x: view<Data>) { ... }

fn modify(x: mut_view<Data>) { ... }

let data = make_data()

inspect(data)
modify(data)
```

Cả hai đều hợp lệ vì view của `inspect` kết thúc sau call.

Semantic:

```text
inspect(data)
    READ(data)
    end capability

modify(data)
    WRITE(data)
    end capability
```

---

# 6. Nhưng cái này phải reject

```axiom
fn save(x: view<Data>) {
    global_view = x
}

let data = make_data()

save(data)
```

Nếu `global_view` escape ra ngoài call:

```text
ephemeral view
      ↓
escape
```

Verifier phát hiện.

Không thể dùng implicit conversion để “lách” lifetime.

---

# 7. Return view

Đây là trường hợp đặc biệt.

```axiom
fn get_name(x: view<Person>) -> view<String> {
    x.name
}
```

Accept.

Vì return view có provenance từ input.

Semantic:

```text
return_region ⊆ input_region
```

Caller phải đảm bảo input owner vẫn sống.

---

Nhưng:

```axiom
fn make_name() -> view<String> {
    let x = String(...)
    view(x)
}
```

Reject.

Không có owner sống sau return.

---

# 8. View từ temporary

Ví dụ:

```axiom
consume(view(make_buffer()))
```

Cần reject nếu view được sử dụng sau khi temporary chết.

Nhưng trong một call không escape:

```axiom
inspect(make_buffer())
```

có thể hợp lệ nếu API chỉ đọc trong call.

Semantic:

```text
make_buffer()
     ↓
temporary owner
     ↓
ephemeral view
     ↓
inspect()
     ↓
DROP temporary
```

Đây là một khả năng rất hữu ích.

---

# 9. `mut_view` cũng áp dụng nguyên tắc tương tự

```axiom
fn normalize(x: mut_view<Vec2>) { ... }

let p = Vec2(...)
normalize(p)
```

Compiler tạo temporary mutable capability.

Sau call:

```text
mut_view capability → END
```

`p` lại usable.

---

# 10. Không implicit `view` qua nhiều tầng tùy tiện

Ví dụ:

```axiom
fn a(x: view<Data>)
fn b(x: view<Data>)

let d = ...
a(d)
b(d)
```

OK.

Nhưng:

```axiom
let v = some_function_returning_view(d)
foo(v)
```

thì `v` là một **actual view value**, không phải owner.

Verifier phải theo provenance của `v`.

---

# 11. Vec invalidation

Đây là phần khó hơn.

Một `Vec<T>` có thể thay đổi backing storage.

Ví dụ:

```text
Vec
├── ptr
├── len
└── capacity
```

`push()` có thể:

```text
old allocation
      ↓
reallocate
      ↓
new allocation
```

Nếu đang có:

```text
view<T>
```

trỏ vào old allocation, view sẽ dangling.

Axiom **không được phụ thuộc vào việc allocator “may mắn” không move**.

---

# 12. Quy tắc invalidation

Tôi đề xuất mọi operation có khả năng thay đổi identity/storage của region phải có effect:

```text
RELOCATE(region)
```

Ví dụ:

```text
Vec.push
Vec.reserve
Vec.resize
Vec.insert
Vec.append
```

có thể:

```text
WRITE
RELOCATE
```

`RELOCATE` có nghĩa:

> Operation có thể làm cho physical storage backing region thay đổi, vì vậy các view/provenance phụ thuộc vào storage đó có thể mất validity.

---

# 13. Nhưng `push` không phải lúc nào cũng reallocate

Đây là điểm quan trọng.

Không được encode semantics thành:

```text
push = always invalidate
```

vì như vậy quá bảo thủ.

Thay vào đó function effect:

```text
push:
    WRITE
    MAY_RELOCATE
```

Verifier thấy:

```text
active view(buffer)
```

và:

```text
push(buffer)
```

=> không thể chứng minh view còn hợp lệ.

Do đó:

```text
REJECT
```

nếu view còn live.

---

# 14. Sau last-use thì được

```axiom
let v = view(buffer)

use(v)

push(buffer, x)
```

Compiler xác định:

```text
last_use(v) = use(v)
```

nên tại `push`:

```text
active views = none
```

=> Accept.

---

# 15. Có thể có API không invalidate

Ví dụ:

```text
Vec.set(index, value)
```

không đổi allocation.

Effect:

```text
WRITE(element)
```

không:

```text
RELOCATE
```

Do đó:

```axiom
let v = view(buffer)

set(buffer, 3, 10)

use(v)
```

có thể **không bị reject** nếu semantic model cho phép READ view quan sát mutation.

Nhưng đây dẫn tới một câu hỏi khác:

> View có được phép thấy mutation của owner trong khi nó tồn tại không?

Tôi đề xuất **có**, nếu access không conflict.

Ví dụ:

```text
v = READ(buffer[0..10])
set(buffer[20], 5)
use(v)
```

OK vì region disjoint.

Nhưng:

```text
v = READ(buffer[0..10])
set(buffer[5], 5)
use(v)
```

phải reject nếu `v` còn active.

---

# 16. Vì vậy `RELOCATE` chưa đủ

Effect model nên có:

```text
READ(region)
WRITE(region)
MOVE(region)
DROP(region)
RELOCATE(region)
```

`RELOCATE` không phải access thông thường.

Conflict:

```text
RELOCATE(R)
```

conflicts với mọi live capability có provenance phụ thuộc vào `R`.

---

# 17. Provenance dependency

Ví dụ:

```text
Vec allocation
    R0
    │
    ├── view[0..10] → V1
    └── view[20..30] → V2
```

Nếu:

```text
RELOCATE(R0)
```

thì cả V1 và V2 invalid.

Không thể chỉ xét region:

```text
V1 region = [0..10]
```

vì relocation thay đổi **storage identity**, không phải chỉ bytes.

Đây là lý do `provenance` phải tách khỏi `region`.

---

# 18. `Vec::set` khác `Vec::push`

```text
set:
    WRITE(element)
```

```text
push:
    WRITE(new element)
    MAY_RELOCATE(storage)
```

```text
reserve:
    MAY_RELOCATE(storage)
```

```text
clear:
    WRITE(elements)
    DROP(elements)
```

```text
sort:
    READ/WRITE(elements)
```

Không phải operation nào cũng invalidate view.

---

# 19. Buffer

Đối với `Buffer<T>` tôi đề xuất semantics tương tự Vec nhưng có khả năng mạnh hơn.

Ví dụ Buffer có:

```text
Buffer<T>
├── storage identity
├── length
├── capacity
└── initialization state
```

Các API có thể phân loại:

```text
read          → READ
write         → WRITE
resize        → WRITE + MAY_RELOCATE
reserve       → MAY_RELOCATE
set_len       → WRITE/INIT semantics
```

Điều này đặc biệt hữu ích cho:

- network
- file I/O
- serialization
- GPU
- FFI

---

# 20. Last-use có phải semantics không?

Tôi đề xuất:

## **Có, nhưng chỉ ở mức capability lifetime.**

Đây là distinction rất quan trọng.

Axiom có:

### Semantic lifetime

Quy định:

```text
view capability tồn tại đến semantic last-use
```

### Physical lifetime

Compiler tự quyết:

```text
stack
heap
register
inline
arena
...
```

### Resource lifetime

`Drop` phải tuân thủ observable semantics.

Ba thứ này không được trộn.

---

# 21. Ví dụ

```axiom
let file = open()
let v = view(file)

read(v)

other_work()

close(file)
```

Nếu `v` không được sử dụng sau:

```text
read(v)
```

capability đã hết.

Nhưng:

```text
file
```

vẫn OWNED.

`close(file)` hợp lệ.

---

# 22. Nhưng Drop observable là ngoại lệ

Ví dụ:

```axiom
let lock = mutex.lock()

use(lock)

other_work()
```

Không thể vì `use(lock)` là last-use mà tự động:

```text
DROP(lock)
```

ngay sau đó nếu semantics của `lock` yêu cầu programmer-visible lexical/resource scope.

Tôi đề xuất phân biệt:

```text
Capability lifetime
```

và:

```text
Resource ownership lifetime
```

**Last-use tự động kết thúc capability, không mặc định kết thúc ownership.**

Đây là điểm rất quan trọng.

---

# 23. Do đó Axiom có hai lifetime model

```text
                  VALUE
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   Capability lifetime    Ownership lifetime
          │                   │
       last-use             Drop
          │                   │
       compiler            deterministic
```

Ví dụ:

```axiom
let buffer = create()
let v = view(buffer)

use(v)

modify(buffer)
```

`v` chết tại last-use.

Nhưng:

```text
buffer
```

vẫn sống đến Drop.

---

# 24. Ownership lifetime cũng có thể kết thúc sớm

Compiler **có thể** Drop resource sớm nếu semantics cho phép.

Ví dụ:

```axiom
let temp = create_resource()

use(temp)

do_other_work()
```

Nếu `Drop(temp)` không observable và không ảnh hưởng tới các operation sau:

```text
DROP(temp)
```

có thể được đưa lên sớm.

Nhưng đây là:

> **optimization subject to observable semantics**

không phải programmer-visible last-use rule.

---

# 25. Resource dependency

Ví dụ:

```axiom
let lock = mutex.lock()
use(lock)
write(shared_data)
```

Nếu Drop lock unlock mutex, compiler không được:

```text
DROP(lock)
write(shared_data)
```

nếu điều đó thay đổi synchronization semantics.

Verifier/optimizer phải xem:

```text
DROP(lock)
```

có:

```text
RESOURCE_RELEASE
SYNC
```

hay không.

---

# 26. Chốt semantics

Tôi đề xuất đóng băng như sau:

### VIEW-01

`view<T>` là non-owning READ capability.

### VIEW-02

`mut_view<T>` là non-owning WRITE capability.

### VIEW-03

Implicit owner → view chỉ tồn tại cho **ephemeral call argument** khi expected parameter type là `view<T>`/`mut_view<T>`.

### VIEW-04

Binding view thành biến phải explicit:

```axiom
let v = view(x)
```

### VIEW-05

`view<T>` không thể outlive provenance owner.

### VIEW-06

`view<T>` không chuyển thành `mut_view<T>`.

### VIEW-07

View return phải giữ provenance hợp lệ.

### VIEW-08

Capability lifetime kết thúc tại semantic last-use.

### VIEW-09

Ownership lifetime độc lập với capability lifetime.

### VIEW-10

Implicit conversion không được phép tạo escaping view.

---

# 27. Invalidation semantics

### INV-01

Mọi storage operation có khả năng thay đổi backing storage phải có `MAY_RELOCATE`.

### INV-02

`MAY_RELOCATE(R)` conflicts với mọi live view có provenance phụ thuộc vào `R`.

### INV-03

Compiler không được giả định operation sẽ không relocate chỉ vì implementation hiện tại chưa relocate.

### INV-04

Operation không có `MAY_RELOCATE` không tự động invalidate view.

### INV-05

Access conflict vẫn được kiểm tra độc lập với relocation.

### INV-06

Unknown/opaque operation mặc định conservative.

---

# 28. Một hệ quả rất hay

Điều này cho phép API compiler hiểu:

```axiom
let v = view(vec)

vec[0] = 10
```

Nếu `v` READ toàn vec:

```text
WRITE(vec[0])
```

=> conflict.

Nhưng:

```axiom
let v = view(vec[0..10])

vec[20] = 10
```

=> disjoint.

Accept.

Và:

```axiom
vec.push(10)
```

=> `MAY_RELOCATE(vec)`.

Reject nếu `v` còn sống.

Đây là memory safety **theo region**, không phải kiểu “hễ có reference là khóa toàn bộ object”.

---

# 29. Đây là lợi thế lớn của Axiom so với mô hình quá đơn giản

Ví dụ:

```text
Person
├── name
├── age
└── address
```

Axiom có thể đồng thời:

```text
view(person.name)
mut_view(person.age)
```

nếu chúng thực sự disjoint.

Không cần programmer:

```text
split borrow
```

hay:

```text
reborrow
```

Compiler tự chứng minh.

---

# 30. Verifier algorithm bây giờ có thể được đóng thành 7 bước

```text
MIR
 │
 ▼
1. Initialization Analysis
 │
 ▼
2. Ownership Dataflow
 │
 ▼
3. Place / Region Construction
 │
 ▼
4. Capability + Last-use Analysis
 │
 ▼
5. Effect / Invalidation Analysis
 │
 ▼
6. Drop + Cleanup Elaboration
 │
 ▼
7. Send/Share + Async Verification
 │
 ▼
VERIFIED MIR
```

Trong đó **Ownership Dataflow + Region + Capability** là lõi.

---

# 31. Và tôi muốn thêm một invariant mới

### AOV-16 — Capability Lifetime Independence

> Kết thúc lifetime của một non-owning capability không được tự động kết thúc ownership lifetime của provenance object.

Điều này giúp compiler tự do tối ưu view mà không ảnh hưởng resource semantics.

### AOV-17 — Relocation Safety

> Mọi operation có khả năng thay đổi storage identity phải được biểu diễn bằng effect `MAY_RELOCATE` hoặc tương đương; optimizer không được loại bỏ effect nếu việc relocation có thể ảnh hưởng observable capability validity.

### AOV-18 — Ephemeral View Safety

> Implicit value-to-view conversion chỉ được phép nếu compiler chứng minh capability không escape khỏi expression/call boundary.

Ba invariant này rất đáng để đưa vào core verifier.

---

# 32. Kiến trúc hiện tại đã khá hoàn chỉnh

Ta đang có:

```text
                   Axiom Source
                         │
                         ▼
                       AST
                         │
                         ▼
                       HIR
                         │
               Type / Trait Resolution
                         │
                         ▼
                       MIR
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
 Ownership             Region           Effects
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                  Capabilities
                         │
                    Last-use
                         │
                    Invalidation
                         │
                  Drop Elaboration
                         │
                Send / Share / Async
                         │
                         ▼
                  VERIFIED MIR
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       MIR Interpreter          Optimizer
                                    │
                                    ▼
                                   LIR
                                    │
                                    ▼
                              Native Backend
```

Và quan trọng nhất:

**Programmer-facing complexity vẫn rất nhỏ:**

```text
let
var
struct
enum
trait
impl
fn
view<T>
mut_view<T>
move
unsafe
Send
Share
```

Trong khi compiler có thể làm một lượng phân tích rất lớn phía sau.

---

## Bước tiếp theo

Giờ tôi nghĩ đã đến lúc **không tiếp tục thêm semantics bằng lời nữa**, mà chuyển sang một thứ có giá trị triển khai trực tiếp:

### `AXIOM-VERIFIER-SPEC-v0.1`

Đặc tả **pseudo-code thuật toán thật**, bao gồm:

```text
VerifierState
PlaceState
Region
Capability
Effect
Merge()
Transfer()
MayOverlap()
CreateView()
EndCapability()
Move()
Drop()
HandleCall()
HandleBranch()
HandleLoop()
HandleSuspend()
```

và một **worked example hoàn chỉnh**, từ source:

```axiom
let p = create_person()
let name = view(p.name)

if condition {
    modify(p.age)
}

use(name)
```

→ CFG → state từng block → merge → region → capability → kết luận ACCEPT/REJECT.

Đó sẽ là bước chuyển từ **“thiết kế language” sang “thuật toán compiler có thể giao thẳng cho AI agent implement”**.