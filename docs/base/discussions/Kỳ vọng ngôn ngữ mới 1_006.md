Có — và đây chính là chỗ cần thiết kế kỹ. Với hướng **không có class**, Axiom vẫn nên hỗ trợ override, nhưng tôi nghĩ **không nên gọi mọi trường hợp là `override`**. Nên phân biệt 3 cơ chế khác nhau.

## 1. Override trait method — trường hợp chính

Ví dụ:

```axiom
trait Drawable {
    fn draw(self: &Self, canvas: &mut Canvas)
}
```

`Button` triển khai trait:

```axiom
struct Button {
    text: String
}

impl Drawable for Button {
    fn draw(self: &Button, canvas: &mut Canvas) {
        // Button implementation
    }
}
```

Ở đây:

```text
Drawable.draw
       ↓
Button.draw
```

Đây chính là **polymorphic override**.

Không cần `override` keyword vì compiler biết `draw` đang implement method của `Drawable`.

Nếu viết sai:

```axiom
impl Drawable for Button {
    fn render(self: &Button) { ... }
}
```

compiler báo:

```text
error: Drawable requires method `draw`
```

---

# 2. Override implementation của một trait đã có

Đây là trường hợp thú vị hơn.

Giả sử:

```axiom
trait Drawable {
    fn draw(self: &Self)
}
```

và có implementation mặc định:

```axiom
trait Drawable {
    fn draw(self: &Self) {
        default_draw(self)
    }
}
```

Struct có thể dùng mặc định:

```axiom
struct Button { ... }

impl Drawable for Button {}
```

hoặc override:

```axiom
impl Drawable for Button {
    fn draw(self: &Button) {
        // custom implementation
    }
}
```

Compiler hiểu:

```text
Drawable.draw
       │
       ├── default implementation
       │
       └── Button.draw ← override
```

Đây là dạng override tôi nghĩ Axiom **nên có chắc chắn**.

---

# 3. Nhưng còn "override function" tự do?

Ví dụ:

```axiom
fn log(message: String) {
    ...
}
```

Sau đó muốn một module thay thế:

```axiom
override fn log(message: String) {
    ...
}
```

Tôi **không khuyến khích cho phép override function tự do theo kiểu này**.

Vì nó tạo ra vấn đề rất lớn:

```text
module A → log()
module B → log()
module C → log()
```

AI/compiler sẽ phải trả lời:

> Cuối cùng `log()` là implementation nào?

Đây là một dạng global monkey patching.

Axiom nên tránh.

---

# 4. Thay vào đó: dependency injection / capability

Ví dụ:

```axiom
trait Logger {
    fn log(self: &Self, message: String)
}
```

Implementation:

```axiom
struct ConsoleLogger {}

impl Logger for ConsoleLogger {
    fn log(self: &ConsoleLogger, message: String) {
        ...
    }
}
```

Code sử dụng:

```axiom
fn run<L: Logger>(logger: &L) {
    logger.log("Hello")
}
```

Production:

```axiom
run(&console_logger)
```

Test:

```axiom
struct TestLogger {}

impl Logger for TestLogger {
    fn log(self: &TestLogger, message: String) {
        // capture message
    }
}
```

Không cần override global function.

---

# 5. Còn nếu muốn kế thừa behavior?

Đây là chỗ Axiom có thể làm khác Rust/Java/C++.

Ví dụ:

```axiom
struct Animal {
    name: String
}

extend Animal {
    fn speak(self: &Animal) {
        print(self.name)
    }
}
```

Sau đó:

```axiom
struct Dog {
    animal: Animal
}
```

Bạn có thể muốn:

```text
Animal.speak()
       ↓
Dog.speak()
```

Tôi **không nên dùng inheritance ngầm** ở đây.

Thay vào đó:

```axiom
trait Speak {
    fn speak(self: &Self)
}
```

```axiom
impl Speak for Animal {
    fn speak(self: &Animal) {
        print(self.name)
    }
}
```

```axiom
impl Speak for Dog {
    fn speak(self: &Dog) {
        print("Woof")
    }
}
```

Như vậy:

```text
Speak
 ├── Animal
 └── Dog
```

rõ ràng hơn:

```text
Animal
   ↓
Dog
```

---

# 6. Nhưng Axiom vẫn nên hỗ trợ `super`

Có một trường hợp thực tế rất cần.

Ví dụ:

```axiom
trait Logger {
    fn log(self: &Self, message: String) {
        print(message)
    }
}
```

Implementation:

```axiom
impl Logger for MyLogger {
    fn log(self: &MyLogger, message: String) {
        Logger.default_log(self, message)

        save_to_file(message)
    }
}
```

Tức là:

```text
default implementation
       ↓
MyLogger.log()
       ↓
additional behavior
```

Nhưng tôi thích syntax kiểu:

```axiom
impl Logger for MyLogger {
    override fn log(self: &MyLogger, message: String) {
        super.log(message)
        save_to_file(message)
    }
}
```

hơn.

`super` ở đây **không có nghĩa là superclass**.

Nó có nghĩa:

> gọi implementation mặc định của operation đang được override.

Điều này rất quan trọng về mặt thiết kế.

---

# 7. Một vấn đề lớn: extension conflict

Với mô hình của Axiom, có thể có:

```axiom
extend User {
    fn save(self: &User) { ... }
}
```

và file khác:

```axiom
extend User {
    fn save(self: &User) { ... }
}
```

Compiler phải **không tự chọn** một cái.

Nên báo:

```text
error AX0421:
multiple implementations of User.save

candidate:
    user.ax:12

candidate:
    persistence.ax:47

help:
    use `replace`, `impl`, or rename one operation
```

Đây cũng rất quan trọng cho AI.

AI không phải đoán "cái nào thắng".

---

# 8. Tôi đề xuất 4 mức behavior cho Axiom

| Cơ chế | Ý nghĩa |
|---|---|
| `fn` | function bình thường |
| `extend T` | thêm operation cho `T` |
| `impl Trait for T` | implementation của trait |
| `override` | thay implementation đã tồn tại |

Ví dụ hoàn chỉnh:

```axiom
struct Button {
    text: String
}

trait Drawable {
    fn draw(self: &Self) {
        default_draw()
    }
}

impl Drawable for Button {
    override fn draw(self: &Button) {
        custom_draw(self.text)
    }
}
```

---

## 9. Và tôi nghĩ nên có cả `final`

Nếu Axiom muốn xây framework lớn:

```axiom
trait Security {
    final fn validate(self: &Self) -> Result<void> {
        ...
    }
}
```

Không implementation nào được override:

```axiom
impl Security for User {
    override fn validate(...) { ... }
}
```

→ compiler error.

Nhưng `final` nên **rất hạn chế**, không biến Axiom thành Java.

---

# 10. Quan trọng nhất: phân biệt Override và Shadowing

Ví dụ:

```axiom
extend User {
    fn save(self: &User) { ... }
}
```

Một module khác:

```axiom
fn save(user: User) { ... }
```

**Không phải override.**

Nó chỉ là một function khác.

Trong semantic model:

```text
User.save
```

và:

```text
save(User)
```

có thể có quan hệ:

```text
related_to: User
```

nhưng không phải:

```text
overrides: User.save
```

Điều này cực kỳ tốt cho **AI semantic metadata** mà chúng ta vừa bàn trước đó.

---

# Kiến trúc tôi nghĩ Axiom nên chốt

```text
                     ┌───────────────┐
                     │     Trait     │
                     └───────┬───────┘
                             │
                    default implementation
                             │
                             ▼
                       ┌───────────┐
                       │ Operation │
                       └─────┬─────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
               default           override
                    │                 │
                    ▼                 ▼
                 impl A             impl B
```

Trong đó:

```text
struct
   │
   ├── fields
   │
   └── extend → operations

trait
   │
   └── abstract/default operations

impl Trait for Struct
   │
   └── implementations

override
   │
   └── explicitly replaces an inherited/default implementation
```

### Tôi đặc biệt khuyên Axiom **không có class inheritance**.

Thay vì:

```text
class Dog : Animal
      ↓
   override speak()
```

Axiom sẽ có:

```text
struct Dog

trait Speak
      ↓
impl Speak for Dog
      ↓
override speak()
```

Kết quả là **vẫn có đầy đủ polymorphism/override**, nhưng không phải mang theo cả hệ thống class/inheritance phức tạp.

Và quan trọng hơn, compiler có thể biểu diễn chính xác mọi quan hệ này trong **Axiom Semantic Model / `.axmeta`**, giúp IDE và AI agent biết *method này override cái gì, implement trait nào, default implementation nằm đâu, dispatch tĩnh hay động* mà không cần tự suy luận từ source code.