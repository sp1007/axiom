Đây thực sự là **một trong những quyết định kiến trúc quan trọng nhất của Axiom**. Và sau những gì chúng ta đã thống nhất, tôi sẽ **không chọn GC, cũng không chọn Rust-style ownership/borrow checker làm mô hình mặc định**.

Tôi cũng không nghĩ nên gọi đơn giản là "flat memory" rồi dùng nó cho mọi thứ. Tôi đề xuất một mô hình **hybrid nhưng ưu tiên flat/contiguous memory**.

## Đề xuất của tôi: Value + Region/Arena + Explicit Heap

Có thể hình dung:

```text
                    AXIOM MEMORY
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        VALUE          REGION         HEAP
          │              │              │
       stack/inline   arena/pool    long-lived
          │              │              │
          └──────────────┼──────────────┘
                         │
                    RAW MEMORY
```

Trong đó **90% code ứng dụng không cần biết những tầng này tồn tại**.

---

# 1. Mặc định: value semantics + contiguous data

Ví dụ:

```axiom
struct Vec3 {
    x: f32
    y: f32
    z: f32
}

p := Vec3(1, 2, 3)
```

`p` chỉ là một value.

Không có:

```text
new Vec3
GC object
reference counting
heap object
```

Compiler có thể đặt nó:

```text
register
stack
inline trong struct khác
```

tùy optimization.

Đây là nền tảng rất quan trọng.

---

# 2. Collection nên ưu tiên flat/contiguous

Ví dụ:

```axiom
users := Array<User>()
```

về mặc định nên là dạng:

```text
Array
┌──────────────────────────────┐
│ User │ User │ User │ User │
└──────────────────────────────┘
```

chứ không phải:

```text
Array
 │
 ├──> User
 ├──> User
 ├──> User
 └──> User
```

Mô hình contiguous có những lợi ích rất lớn:

- locality tốt
- cache-friendly
- ít pointer chasing
- ít allocation
- SIMD dễ hơn
- prefetching tốt
- allocator fragmentation thấp hơn
- serialization dễ
- truyền sang GPU dễ hơn

Đặc biệt với game/graphics/AI/data processing, đây là một lợi thế lớn.

---

# 3. Nhưng "flat memory" không nên có nghĩa là một heap duy nhất

Đây là điểm tôi muốn sửa một chút từ giả định ban đầu.

Nếu tất cả object đều nhét vào **một vùng memory phẳng duy nhất**:

```text
[ A ][ B ][ C ][ D ][      ][ E ][ F ]
```

thì sau một thời gian vẫn có thể xảy ra:

```text
[ A ][free][ C ][free][ D ][       ][ F ]
```

Tức là fragmentation vẫn có thể xuất hiện.

Vì vậy tôi thích:

## Region / Arena

Ví dụ:

```axiom
region frame {
    ...
}
```

Memory:

```text
Frame Region
┌──────────────────────────────────┐
│ A │ B │ C │ D │ E │ F │ G │ ... │
└──────────────────────────────────┘
                                ↑
                              cursor
```

Khi frame kết thúc:

```text
region.reset()
```

→ toàn bộ vùng được giải phóng gần như tức thời.

Không cần:

```text
free(A)
free(B)
free(C)
...
```

Đây là một mô hình cực kỳ phù hợp với:

- game frame
- rendering
- compiler
- parser
- temporary computation
- request processing
- AI inference
- audio processing

---

# 4. Region không cần borrow checker

Đây là điểm tôi nghĩ rất phù hợp với Axiom.

Axiom có thể cho programmer:

```axiom
region frame {
    data := create_data()
    process(data)
}
```

Compiler biết:

```text
data lifetime <= frame
```

nhưng **không bắt programmer viết lifetime annotation**.

Nếu programmer cố đưa một object ra ngoài region:

```axiom
region frame {
    global_data = create_data()
}
```

compiler báo lỗi:

```text
value allocated in region `frame`
cannot escape region
```

Đây là **escape analysis**, không nhất thiết phải biến thành Rust borrow checker.

---

# 5. Long-lived object mới cần Heap

Có những thứ không biết trước lifetime:

```text
window
asset
scene
database
network connection
user-created object
```

Khi đó:

```text
heap
```

là cần thiết.

Nhưng tôi không muốn mỗi object đều là một allocation.

Thay vào đó:

```text
Heap
 ├── Arena A
 ├── Arena B
 ├── Pool A
 ├── Pool B
 └── Large allocations
```

Ví dụ game engine:

```text
Asset Arena
Entity Arena
Component Arena
Frame Arena
Temporary Arena
```

Fragmentation được kiểm soát ở cấp **region**, thay vì để một global allocator xử lý tất cả.

---

# 6. Object identity vẫn phải tồn tại

Đây là chỗ chúng ta cần rất cẩn thận.

Flat/value memory rất tốt cho:

```text
Vec3
Transform
Color
Matrix
Component
Particle
Vertex
```

Nhưng không phải mọi thứ đều nên copy.

Ví dụ:

```text
Scene
 ├── Camera
 ├── Mesh
 ├── Material
 └── Light
```

Nếu copy cả `Scene` mỗi lần truyền function thì rất tệ.

Axiom vì vậy cần một abstraction kiểu:

```text
value
view
handle
```

Tôi nghiêng về **handle/index** hơn pointer trong phần lớn high-level code.

Ví dụ:

```axiom
mesh := meshes.create(...)
draw(mesh)
```

`mesh` có thể thực chất là:

```text
index / handle
```

thay vì:

```text
*Mesh
```

Như vậy programmer không phải thường xuyên đối mặt với pointer.

---

# 7. Data-oriented programming sẽ rất hợp Axiom

Ví dụ thay vì:

```text
Entity
 ├── Transform
 ├── Velocity
 ├── Health
 └── Mesh
```

có thể lưu:

```text
Transforms:
[T0][T1][T2][T3][T4]...

Velocities:
[V0][V1][V2][V3][V4]...

Health:
[H0][H1][H2][H3][H4]...
```

Rồi:

```axiom
for entity in entities {
    transform.position += velocity * dt
}
```

compiler/runtime có thể tối ưu thành data-oriented loop.

Đây là một hướng tôi rất muốn Axiom hỗ trợ **tự nhiên**, không cần programmer phải học ECS framework.

---

# 8. Có nên có pointer?

**Có.**

Nhưng tôi không muốn pointer trở thành cách giao tiếp mặc định.

Có thể có tầng:

```text
Value
 ↓
View
 ↓
Handle
 ↓
Reference
 ↓
Raw pointer
 ↓
Address
```

Programmer bình thường chủ yếu dùng:

```text
value
view
handle
```

Programmer hệ thống có thể dùng:

```text
reference
pointer
address
```

Như vậy Axiom vẫn đủ sức viết:

- allocator
- OS code
- driver
- renderer
- compiler
- embedded code

mà không bắt toàn bộ ecosystem phải sống với pointer.

---

# 9. Một điểm cực kỳ quan trọng: không được biến `reference` thành "Rust-lite"

Tôi **không muốn**:

```text
&mut T
&T
'a
where 'a: ...
```

xuất hiện khắp code.

Thay vào đó, compiler có thể áp dụng các rule đơn giản:

### Rule 1

Value mặc định.

### Rule 2

View/reference không sở hữu memory.

### Rule 3

Không cho phép reference sống lâu hơn storage mà nó trỏ tới.

### Rule 4

Compiler tự kiểm tra khi có thể.

### Rule 5

Low-level unsafe/raw memory có escape hatch rõ ràng.

Đủ.

Không cần xây cả một hệ thống ownership type theory chỉ để viết application code.

---

# 10. Còn garbage collection?

Tôi sẽ **không đưa tracing GC vào Axiom Core**.

Không phải vì GC luôn chậm.

Mà vì nó tạo ra một runtime model mà chúng ta không cần nếu có:

```text
value
+ region
+ arena
+ pool
+ explicit heap
```

Nếu sau này cần GC cho một ecosystem cụ thể, có thể xây:

```text
Axiom GC Library/Runtime
```

trên Axiom.

Không nên bắt toàn bộ ngôn ngữ phải dùng nó.

---

# Mô hình tôi hiện nghiêng về

```text
                    Axiom
                      │
          ┌───────────┴───────────┐
          │                       │
       VALUE                  ALLOCATION
          │                       │
     ┌────┴────┐          ┌───────┼────────┐
     │         │          │       │        │
   inline    stack      region   arena    heap
                         │       │        │
                         └───────┴────────┘
                                 │
                              pools
                                 │
                           large objects
```

Và programmer nhìn thấy API đơn giản:

```axiom
x := Foo()
```

```axiom
region frame {
    ...
}
```

```axiom
items := Array<Item>()
```

```axiom
handle := resources.load(...)
```

chứ không phải:

```text
Box
Rc
Arc
RefCell
Cell
Weak
Pin
MutexGuard
lifetime...
```

---

# Có một điều tôi muốn nhấn mạnh về "flat memory"

**Flat/contiguous memory không tự động nhanh hơn mọi mô hình.**

Nó đặc biệt tốt khi workload có:

- nhiều phần tử cùng kiểu
- truy cập tuần tự
- xử lý hàng loạt
- SIMD
- cache locality

Nhưng một cấu trúc tree/graph với các node có kích thước khác nhau vẫn có thể cần indirection.

Vì vậy tôi không muốn Axiom biến:

> **flat memory**

thành một giáo điều.

Tôi muốn biến nó thành:

> **contiguous memory là default khi semantic của dữ liệu cho phép.**

Compiler có thể tự chọn representation khi semantic không yêu cầu identity/address ổn định.

---

# Nếu chốt hướng này, tôi sẽ đề xuất Memory Model của Axiom có 6 khái niệm

| Khái niệm | Mục đích |
|---|---|
| **Value** | mặc định, đơn giản nhất |
| **View** | truy cập dữ liệu không sở hữu |
| **Handle** | identity ổn định, tránh pointer phổ biến |
| **Region** | lifetime theo scope |
| **Arena/Pool** | allocation hiệu quả cho nhóm object |
| **Raw Memory** | tầng thấp nhất cho system programming |

**Không GC bắt buộc. Không borrow checker bắt buộc. Không reference counting bắt buộc.**

Và quan trọng nhất: **compiler phải tối ưu representation phía dưới**, để programmer không phải quyết định stack/heap/arena cho từng biến.

Tôi cho rằng hướng này phù hợp với mục tiêu Axiom mà chúng ta vừa thống nhất hơn cả việc cố xây một "memory model tối giản". Nó ưu tiên **performance + đơn giản + khả năng kiểm soát**, thay vì tối ưu một tiêu chí duy nhất.