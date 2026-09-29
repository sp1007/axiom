Đúng. Nếu mục tiêu của Axiom là **giảm cognitive load** chứ không phải sao chép Rust, thì tôi cũng nghiêng về hướng **không để programmer phải nghĩ về reference/pointer trong code thông thường**.

Thậm chí tôi nghĩ có thể đặt nguyên tắc mạnh hơn:

> **Pointer/reference là implementation detail của compiler, không phải abstraction mà programmer phải sử dụng thường xuyên.**

### Tôi hình dung Axiom như thế này

Programmer viết:

```axiom
struct Player {
    name: string
    hp: i32
}

fn damage(player: Player, amount: i32) {
    player.hp -= amount
}
```

Compiler tự quyết định:

```text
copy?
move?
pass address?
register?
stack?
heap?
```

dựa trên kích thước type, escape analysis, lifetime và optimization.

Programmer **không cần viết**:

```text
&Player
*Player
ref Player
mut Player
Box<Player>
Rc<Player>
Arc<Player>
```

---

## Nhưng có một vấn đề cần giải quyết

Nếu `Player` lớn:

```axiom
struct Player {
    inventory: ...
    world_state: ...
    ...
}
```

thì:

```axiom
fn damage(player: Player)
```

không thể thực sự copy toàn bộ object mỗi lần gọi.

Vì vậy Axiom có thể áp dụng nguyên tắc:

### **Value semantics ở language level, optimized representation ở compiler level**

Programmer nghĩ:

```text
Player = một giá trị
```

Compiler có thể biến:

```text
damage(player)
```

thành:

```text
damage(&player)
```

nếu thấy cần.

Nhưng cái `&` đó **không xuất hiện trong source code**.

---

# Tôi nghĩ đây có thể là một trong những điểm đặc trưng nhất của Axiom

Ví dụ:

```axiom
fn move(player: Player, position: Vec3) {
    player.position = position
}
```

Với programmer:

```text
Player
 ↓
value
```

Compiler:

```text
small struct
→ register/value

large struct
→ hidden pointer

non-copyable resource
→ hidden ownership handle

temporary
→ stack/register

escaped object
→ heap
```

Tất cả đều là **implementation strategy**.

---

# Vậy object lớn nằm ở đâu?

Axiom có thể phân biệt:

```axiom
struct Player {
    ...
}
```

với:

```axiom
resource Texture {
    ...
}
```

`struct` có **value semantics**.

`resource` biểu thị thứ có lifetime/resource ownership đặc biệt.

Ví dụ:

```axiom
let texture = Texture.load("a.png")
```

Compiler biết texture không nên copy byte-for-byte.

Nhưng programmer vẫn chỉ thấy:

```axiom
texture
```

chứ không phải:

```text
Texture*
Rc<Texture>
Arc<Texture>
&Texture
&mut Texture
```

---

# Collection cũng không cần expose pointer

Ví dụ:

```axiom
let players = Array<Player>()
players.add(player)

for player in players {
    player.hp -= 10
}
```

Không cần:

```text
iterator
reference
mutable reference
borrow
lifetime
```

Compiler tự biến vòng lặp thành dạng hiệu quả nhất.

---

# Nhưng `unsafe` vẫn có thể cần pointer

Đây là ngoại lệ.

Ví dụ viết driver, allocator, OS kernel:

```axiom
unsafe {
    ...
}
```

lúc đó Axiom có thể cung cấp primitive:

```text
address
load
store
offset
atomic
volatile
asm
```

Nhưng tôi thậm chí **không nhất thiết expose `*T` như một type phổ biến**.

Có thể thiết kế low-level API theo kiểu:

```axiom
unsafe {
    let addr = memory.allocate(1024)
    memory.store(addr, value)
}
```

thay vì:

```axiom
let p: *mut Foo
*p = ...
```

Tức là ngay cả unsafe cũng ưu tiên abstraction có nghĩa.

---

# Điều này cũng giải quyết vấn đề "nhầm `value` với `reference`"

Một lỗi rất phổ biến ở các ngôn ngữ có reference semantics là programmer phải nhớ:

```text
cái này copy?
cái kia reference?
cái kia shared?
cái kia mutable?
```

Axiom có thể đặt quy tắc:

> **Mọi biến đều có value semantics về mặt ngôn ngữ.**

Compiler tự tối ưu representation.

Nếu cần chia sẻ state:

```axiom
let a = Shared<Player>()
let b = a
```

thì **`Shared` mới là một abstraction rõ ràng**, thay vì mọi object mặc định đều có reference semantics.

---

# Tôi sẽ tránh cả việc "ẩn reference" quá mức

Có một ranh giới quan trọng.

Không nên để:

```axiom
let a = Player()
let b = a
b.hp = 100
```

mà lúc thì `a.hp` cũng thay đổi, lúc thì không, tùy compiler.

Điều đó cực kỳ nguy hiểm.

Phải có semantic rõ ràng:

```text
a = Player
b = a

→ b là một value độc lập
```

Nếu muốn shared:

```text
a = Shared(Player)
b = a

→ a và b cùng một resource
```

**Compiler được tự do tối ưu implementation, nhưng không được thay đổi semantics.**

Đây là điểm rất quan trọng.

---

# Như vậy Axiom có thể tránh cả hai cực

### C

```text
value
pointer
pointer-to-pointer
manual lifetime
malloc/free
```

→ quá nhiều responsibility.

### Rust

```text
&T
&mut T
&T lifetime
Box<T>
Rc<T>
Arc<T>
ownership
borrowing
```

→ safety rất mạnh nhưng cognitive load cao.

### Axiom

```text
Value
Resource
Shared<T>
```

và phần còn lại:

```text
        Compiler
           ↓
 copy / move / address / heap / stack
           ↓
       machine code
```

Đây là hướng tôi **rất thích cho Axiom**.

---

## Tôi thậm chí sẽ đưa thành invariant

**Axiom Memory Model**

1. **No mandatory GC.**
2. **No mandatory borrow checker syntax.**
3. **No pointer/reference syntax in ordinary application code.**
4. **Variables have predictable value semantics.**
5. **Compiler may represent values using registers, stack, pointers or heap transparently.**
6. **Shared mutable state must be explicit through a language/library abstraction.**
7. **Manual memory manipulation exists only in explicit low-level/unsafe contexts.**
8. **Abstraction must not impose runtime overhead when it can be eliminated at compile time.**

Điểm số 8 đặc biệt quan trọng.

Nếu programmer viết:

```axiom
fn distance(a: Vec3, b: Vec3) -> f32
```

thì compiler có thể biến nó thành vài register và SIMD instruction.

Nếu programmer viết:

```axiom
let texture = Texture.load(...)
```

compiler có thể dùng handle/pointer/reference-counting bên dưới.

**Source code không cần biết.**

Tôi nghĩ đây là một hướng đáng để Axiom theo đuổi: **“semantic simplicity, implementation freedom.”** Compiler phải đủ thông minh để gánh phần phức tạp mà hiện nay C++/Rust bắt programmer phải gánh.