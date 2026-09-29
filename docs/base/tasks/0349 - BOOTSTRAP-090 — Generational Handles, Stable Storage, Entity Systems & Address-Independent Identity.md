# BOOTSTRAP-090 — Generational Handles, Stable Storage, Entity Systems & Address-Independent Identity

**Trạng thái: FROZEN**

Đây là phần rất quan trọng để hoàn thiện hướng thiết kế **không buộc lập trình viên phải dùng pointer/reference** trong code ứng dụng, nhưng vẫn hỗ trợ game engine, ECS, GUI, scene graph, database, compiler AST, resource manager… với hàng triệu object.

---

# 1. Vấn đề cốt lõi

Axiom đã tách ba khái niệm:

```text
Value Identity
Storage Identity
Logical Identity
```

Cần giữ chúng **tách biệt tuyệt đối**.

Ví dụ:

```text
Player
```

có thể:

- là một value;
- nằm trong `Vec<Player>`;
- bị di chuyển khi `Vec` grow;
- nhưng các hệ thống khác vẫn cần nhận biết đó **vẫn là Player #123**.

Nếu dùng raw pointer:

```text
Player* p
```

thì relocation có thể làm `p` dangling.

Nếu dùng reference:

```text
&Player
```

thì programmer phải đối mặt với lifetime/aliasing.

Axiom giải quyết bằng:

```text
Handle<Player>
```

Handle biểu diễn **logical identity**, không phải địa chỉ bộ nhớ.

---

# 2. Ba loại Identity

## 2.1 Value Identity

Một value được xác định bởi chính giá trị của nó.

Ví dụ:

```text
let a = Vec2(10, 20)
let b = a
```

Nếu `Vec2: Copy`:

```text
a ≠ b
```

theo identity vật lý, dù:

```text
a == b
```

theo semantic equality.

Value identity không yêu cầu object phải có địa chỉ ổn định.

---

# 3. Storage Identity

Storage identity trả lời:

> Đây có phải cùng một vùng storage hay không?

Ví dụ:

```text
Box<Player>
Pool<Player>
Arena<Player>
```

Một object có thể có storage identity ổn định trong một khoảng thời gian.

Nhưng:

```text
Vec<Player>
```

không đảm bảo storage identity ổn định vì relocation có thể xảy ra.

Do đó:

```text
storage identity ≠ logical identity
```

---

# 4. Logical Identity

Logical identity trả lời:

> Đây có phải cùng một thực thể mà hệ thống đang quản lý hay không?

Ví dụ:

```text
EntityId
TextureId
MeshId
WindowId
AstNodeId
FileId
ResourceId
```

Đây là thứ ứng dụng thường thực sự cần.

Ví dụ ECS:

```text
EntityId = 918273
```

Entity có thể chuyển:

```text
Archetype A
    ↓
Archetype B
    ↓
Archetype C
```

nhưng:

```text
EntityId
```

vẫn có thể giữ nguyên.

---

# 5. Handle

Axiom Core/Library chuẩn hóa khái niệm:

```text
Handle<T>
```

với semantics:

> Một giá trị định danh logic tới một resource/object thuộc một hệ quản lý nào đó.

Handle **không phải**:

```text
pointer
reference
ownership
view
mut_view
```

Nó chỉ là identity/capability key ở cấp abstraction.

Ví dụ:

```text
let player: Handle<Player>
let texture: Handle<Texture>
let ast: Handle<AstNode>
```

Không có nghĩa:

```text
Handle<Player> == *Player
```

---

# 6. Generational Handle

Handle đơn giản có vấn đề:

```text
slot = 42
```

Object cũ bị xóa:

```text
slot 42 → free
```

Object mới được tạo lại:

```text
slot 42 → NewObject
```

Handle cũ vẫn chứa:

```text
42
```

và có thể vô tình truy cập object mới.

Axiom sử dụng **generation**.

Một handle điển hình về mặt implementation:

```text
Handle<T> {
    index
    generation
}
```

Ví dụ:

```text
Handle<Player> {
    index: 42,
    generation: 7
}
```

Slot:

```text
slot[42] {
    generation: 7,
    value: Player
}
```

Xóa:

```text
generation = 8
```

Handle cũ:

```text
(42, 7)
```

không còn hợp lệ.

---

# 7. Validation

Lookup:

```text
pool.get(handle)
```

logic:

```text
if handle.index out of range:
    invalid

if slot.generation != handle.generation:
    stale

otherwise:
    valid
```

Kết quả:

```text
Option<view<T>>
```

hoặc:

```text
Option<mut_view<T>>
```

tùy API.

Ví dụ:

```text
if let Some(player) = players.get(player_id) {
    ...
}
```

Không cần:

```text
Player*&
Player**
lifetime annotation
```

---

# 8. Handle không phải ownership

Đây là invariant cực kỳ quan trọng.

```text
Handle<T>
```

**không giữ object sống**.

Ví dụ:

```text
let h = players.create(player)

players.destroy(h)
```

Sau `destroy`:

```text
h
```

có thể vẫn tồn tại như một value, nhưng nó là stale.

Vì vậy:

```text
Handle<T> ≠ Owner<T>
```

Nếu muốn sở hữu object:

```text
Box<T>
```

Nếu muốn logical identity:

```text
Handle<T>
```

Nếu muốn đọc:

```text
view<T>
```

Nếu muốn sửa:

```text
mut_view<T>
```

---

# 9. Handle không phải capability bộ nhớ

Một handle hợp lệ không đồng nghĩa với việc programmer được phép giữ reference lâu dài.

Ví dụ:

```text
let h = entities.create(...)
```

Sau đó:

```text
let v = entities.get(h)
```

`v` vẫn là:

```text
view<T>
```

và chịu toàn bộ capability/lifetime rules.

Handle có thể sống lâu hơn object.

View thì không.

Đây là sự phân tách rất mạnh:

```text
Handle
    ↓ resolve
view / mut_view
    ↓
actual access
```

---

# 10. Handle có thể cực kỳ nhỏ

Một generational handle không cần object header.

Ví dụ:

```text
u32 index
u32 generation
```

= 8 bytes.

Có thể tối ưu thành:

```text
u64
```

nếu ABI/implementation phù hợp.

Ví dụ:

```text
63 bits index
1 bit generation
```

hoặc phân chia tùy container.

Đây là **representation optimization**, không phải semantic requirement.

---

# 11. Generation không nhất thiết phải là integer cố định

Semantics chỉ yêu cầu:

> Handle cũ không được trở thành handle hợp lệ tới một object khác một cách âm thầm.

Implementation có thể dùng:

```text
generation counter
version
epoch
salt
incarnation
```

Tuy nhiên implementation mặc định nên là:

```text
index + generation
```

vì đơn giản và hiệu quả.

---

# 12. Overflow generation

Generation eventually có thể overflow.

Không được:

```text
generation += 1
```

rồi quay về generation cũ mà không có semantics rõ ràng.

Axiom quy định:

> Generation reuse phải không tạo ra aliasing âm thầm trong phạm vi validity contract của container.

Container có thể:

- retire slot;
- mở rộng generation;
- dùng quarantine;
- dùng epoch;
- hoặc có giới hạn rõ ràng.

Không được silently biến stale handle thành valid handle.

---

# 13. Stable Storage

Một số hệ thống thực sự cần địa chỉ ổn định.

Ví dụ:

```text
OS resource
DMA buffer
memory-mapped object
foreign API
GPU resource
intrusive data structure
```

Lúc này không nên giả vờ rằng mọi storage đều relocatable.

Axiom có:

```text
Stable Storage Contract
```

Ví dụ library:

```text
StableBox<T>
StablePool<T>
```

hoặc:

```text
Pool<T>
```

có slot identity ổn định.

---

# 14. Stable address ≠ Stable identity

Hai khái niệm này phải tiếp tục tách biệt.

Ví dụ:

```text
Pool<T>
```

có:

```text
stable address
```

nhưng logical identity vẫn có thể là:

```text
Handle<T>
```

Ngược lại:

```text
Vec<T>
```

có thể relocation:

```text
address thay đổi
```

nhưng:

```text
Handle<T>
```

vẫn giữ logical identity.

Do đó:

```text
Stable Address
    ≠
Logical Identity
```

---

# 15. Pool

Pool phù hợp khi:

- object cùng kích thước;
- tạo/xóa thường xuyên;
- cần slot ổn định;
- cần cache-friendly access;
- cần handle.

Ví dụ:

```text
Pool<Particle>
Pool<Component>
Pool<Entity>
```

Representation có thể là:

```text
[slot][slot][slot][slot]...
```

Mỗi slot:

```text
generation
occupied
value
```

Nhưng metadata có thể được tách khỏi value storage để tối ưu cache.

---

# 16. Slot map

Một abstraction rất phù hợp Axiom:

```text
SlotMap<T>
```

Semantic:

```text
Handle<T> insert(T)
Option<T> remove(Handle<T>)
Option<view<T>> get(Handle<T>)
Option<mut_view<T>> get_mut(Handle<T>)
```

Ví dụ:

```text
let id = players.insert(Player(...))

if let Some(player) = players.get_mut(id) {
    player.hp -= 10
}

players.remove(id)
```

Không có pointer/reference trong application-level API.

---

# 17. ECS

Axiom đặc biệt phù hợp với ECS.

Ví dụ:

```text
EntityId
```

không cần trỏ trực tiếp vào object.

Có thể:

```text
EntityId
    ↓
EntityLocation
    ↓
Archetype
    ↓
Row
```

Ví dụ:

```text
EntityId {
    index,
    generation
}
```

và:

```text
EntityLocation {
    archetype,
    row
}
```

Khi entity chuyển archetype:

```text
Archetype A / row 17
        ↓
Archetype B / row 5
```

`EntityId` không thay đổi.

---

# 18. ECS không cần object-oriented identity

Điều này củng cố triết lý:

```text
struct + functions + handles
```

thay vì:

```text
class + object pointer + inheritance
```

Ví dụ:

```text
struct Transform {
    position: Vec3
    rotation: Quat
}

fn translate(
    t: mut_view<Transform>,
    delta: Vec3
) {
    t.position += delta
}
```

ECS:

```text
fn update_transforms(
    transforms: mut_view<Transform>,
    velocities: view<Velocity>
)
```

Handle chỉ dùng để xác định entity.

Data thực tế vẫn có thể nằm contiguous.

---

# 19. Scene Graph

Scene graph có thể dùng:

```text
NodeId
```

thay vì:

```text
Node*
```

Ví dụ:

```text
struct Node {
    parent: Option<NodeId>
    first_child: Option<NodeId>
    next_sibling: Option<NodeId>
}
```

Sau đó:

```text
scene.get_mut(node_id)
```

Object có thể được relocate trong storage mà graph vẫn đúng.

---

# 20. GUI

GUI framework thường có:

```text
WindowId
WidgetId
ControlId
TextureId
FontId
```

Axiom khuyến khích:

```text
WidgetId
```

thay vì để mọi callback giữ pointer tới widget.

Ví dụ:

```text
fn on_click(ui: mut_view<Ui>, widget: WidgetId)
```

Resolve:

```text
ui.get_mut(widget)
```

Điều này cũng làm lifecycle của UI rõ hơn.

---

# 21. Resource Manager

Ví dụ:

```text
TextureHandle
MeshHandle
ShaderHandle
MaterialHandle
AudioHandle
```

Resource manager:

```text
textures.get(texture_handle)
```

Resource có thể:

- unload;
- reload;
- relocate;
- stream;
- upload GPU;
- thay đổi storage;

mà code client không cần giữ địa chỉ vật lý.

---

# 22. Database

Database cũng có logical identity tự nhiên:

```text
UserId
OrderId
RowId
PageId
TransactionId
```

Không nên map database identity trực tiếp thành memory address.

Ví dụ:

```text
struct UserId {
    value: u64
}
```

hoặc:

```text
Handle<User>
```

là abstraction hợp lý.

---

# 23. Compiler / AST

Đây là một trường hợp đặc biệt quan trọng với chính compiler Axiom.

CompilerDB đã thiết kế:

```text
TypeId
FunctionId
DeclarationId
ModuleId
TraitId
FieldId
...
```

Đây thực chất là **logical handles**.

Ví dụ:

```text
DeclarationId
    ↓
DeclarationDB
```

Không cần:

```text
Declaration*
```

Điều này cho phép:

- incremental compilation;
- interning;
- caching;
- parallel queries;
- serialization metadata;
- stable semantic references;
- relocation của compiler memory.

---

# 24. Handle và incremental compiler

Ví dụ:

```text
TypeId = 9182
```

không nên phụ thuộc trực tiếp vào:

```text
heap address
```

CompilerDB có thể thay đổi implementation:

```text
arena
intern pool
database revision
parallel storage
```

mà semantic identity vẫn độc lập.

Đây là lý do Axiom compiler nên sử dụng **ID-centric architecture**.

---

# 25. Handle + generation không phải lúc nào cũng cần

Không nên biến:

```text
Handle<T>
```

thành một abstraction bắt buộc cho mọi thứ.

Nếu object chỉ sống trong scope:

```text
fn process(x: view<Data>)
```

thì dùng view.

Nếu object là value:

```text
Data
```

thì dùng value.

Nếu ownership rõ:

```text
Box<Data>
```

thì dùng owner.

Handle chỉ phù hợp khi cần:

> identity tồn tại độc lập với storage location/lifetime của một object cụ thể.

---

# 26. Handle resolution phải có chi phí rõ ràng

Axiom không được tuyên bố:

> Handle luôn zero-cost.

Không đúng.

Ví dụ:

```text
pool.get(id)
```

có thể phải:

```text
bounds check
generation check
index lookup
```

Tuy nhiên compiler có thể tối ưu khi chứng minh được:

```text
id valid
```

hoặc khi iteration đã chuyển sang direct contiguous access.

---

# 27. Bulk access

Để tránh:

```text
for id in entities {
    entities.get(id)
}
```

với lookup liên tục, container nên cung cấp API bulk:

```text
query<Transform, Velocity>()
```

hoặc:

```text
view_components(...)
```

để chuyển từ:

```text
Handle-centric access
```

sang:

```text
data-oriented contiguous access
```

Đây là điểm rất quan trọng:

> Handle là abstraction identity; không phải abstraction iteration.

---

# 28. Handle validation có thể được loại bỏ

Ví dụ:

```text
let id = pool.insert(x)

if let Some(x) = pool.get_mut(id) {
    process(x)
}
```

Trong một phạm vi compiler chứng minh:

```text
id originates from this pool
id has not been destroyed
id generation unchanged
pool unchanged in conflicting way
```

thì checks có thể được loại bỏ.

Semantics vẫn là checked.

Machine code có thể trở thành:

```text
direct indexed access
```

Đây là đúng triết lý:

> Safety ở semantic layer, zero-cost khi compiler chứng minh được.

---

# 29. Handle ownership

Handle mặc định nên:

```text
Copy
```

nếu representation phù hợp.

Bởi vì:

```text
copying Handle<T>
```

không copy resource.

Ví dụ:

```text
let a = texture
let b = texture
```

cả hai chỉ biểu diễn cùng logical identity.

Không có:

```text
double free
```

vì Handle không sở hữu resource.

---

# 30. Typed Handle

Không nên để:

```text
Handle
```

không có type.

Axiom ưu tiên:

```text
Handle<Texture>
Handle<Mesh>
Handle<Entity>
Handle<File>
```

để:

```text
Handle<Texture>
```

không thể vô tình truyền vào:

```text
fn destroy(mesh: Handle<Mesh>)
```

Đây là type safety rất rẻ.

---

# 31. Generational Handle và resource type

Ví dụ:

```text
TextureHandle = Handle<Texture>
```

có thể phân biệt:

```text
TextureHandle
MeshHandle
MaterialHandle
```

dù representation giống nhau.

Có thể dùng newtype:

```text
struct TextureId(Handle<Texture>)
```

nếu domain cần identity semantics riêng.

---

# 32. Resource identity và lifetime

Một resource có thể có:

```text
logical lifetime
```

khác:

```text
memory lifetime
```

Ví dụ GPU texture:

```text
TextureHandle
       ↓
GPU allocation
       ↓
device resource
```

Khi unload:

```text
Handle stale
GPU resource released
CPU metadata released
```

Nhưng handle value có thể vẫn tồn tại ở nơi khác.

Các API resolve sẽ trả:

```text
None
```

thay vì dangling reference.

---

# 33. Generation + asynchronous systems

Đặc biệt quan trọng với async.

Ví dụ:

```text
let request = requests.create(...)
spawn(async_process(request))
```

Request có thể bị destroy/reuse trước khi task chạy lại.

Task giữ:

```text
RequestHandle
```

không phải:

```text
view<Request>
```

Khi resume:

```text
requests.get(request)
```

Nếu generation không khớp:

```text
None
```

Task không đọc nhầm request mới.

---

# 34. Handle + concurrency

Handle bản thân có thể là `Copy + Send + Share` nếu representation của nó đáp ứng các điều kiện.

Nhưng:

```text
Handle<T>: Send
```

**không có nghĩa**:

```text
T: Send
```

và cũng không có nghĩa:

```text
T: Share
```

Handle chỉ là identity.

Thread muốn access resource vẫn phải đi qua abstraction có synchronization phù hợp.

---

# 35. Không cho Handle tự động thành view

Không có:

```text
let x: view<T> = handle
```

vì điều này sẽ che giấu:

- container;
- lifetime;
- synchronization;
- validity;
- generation;
- storage domain.

Phải resolve qua owner/manager:

```text
pool.get(handle)
```

hoặc abstraction tương đương.

---

# 36. Handle và relocation

Một invariant quan trọng:

```text
Relocation MUST NOT change logical identity.
```

Ví dụ:

```text
Vec<T>
```

từ:

```text
address A
```

sang:

```text
address B
```

không được làm:

```text
Handle<T>
```

thay đổi.

Nếu container semantics yêu cầu identity stable, nó phải dùng storage strategy phù hợp.

---

# 37. Handle và deletion

Deletion:

```text
destroy(handle)
```

phải làm:

```text
logical identity invalid
```

trước hoặc đồng thời với việc resource trở nên reusable.

Không được có trạng thái trong đó:

```text
old handle
```

có thể hợp lệ tới:

```text
new object
```

mà không có semantics generation/identity tương ứng.

---

# 38. Handle không giải quyết mọi ABA problem

Generational handle giúp chống:

```text
A → deleted → B
```

với cùng slot.

Nhưng concurrent lock-free algorithms còn có các ABA pattern phức tạp hơn.

Axiom **không tuyên bố**:

```text
Handle = universal ABA protection
```

Lock-free algorithms vẫn cần:

```text
atomic
version
epoch
hazard pointer
RCU
```

hoặc abstraction library phù hợp.

---

# 39. Handle API chuẩn

Library nên có một abstraction tương đương:

```text
SlotMap<T>
```

với semantic API:

```text
insert(value) -> Handle<T>

get(handle) -> Option<view<T>>

get_mut(handle) -> Option<mut_view<T>>

remove(handle) -> Option<T>

contains(handle) -> bool
```

và:

```text
iter() -> iterator
iter_mut() -> iterator
```

Iteration không cần thông qua Handle lookup từng phần tử.

---

# 40. StablePool

Cho trường hợp cần address stability:

```text
StablePool<T>
```

semantic:

```text
insert -> Handle<T>
get -> view<T>
get_mut -> mut_view<T>
remove
```

nhưng storage contract đảm bảo:

```text
live T does not move
```

trong thời gian storage contract.

Điều này khác:

```text
SlotMap<T>
```

nếu SlotMap cho phép relocation nội bộ.

---

# 41. Arena + Handle

Arena có thể tạo:

```text
Handle<T>
```

nhưng semantics khác.

Arena thường:

```text
allocate
...
destroy arena
```

thay vì destroy từng object.

Handle validity bị giới hạn bởi:

```text
Arena lifetime
```

Có thể có:

```text
ArenaId
Generation
LocalIndex
```

nhưng không nên biến Arena thành GC.

---

# 42. Generation và arena

Arena bulk destruction:

```text
arena.destroy()
```

phải invalidate toàn bộ handles liên quan.

Cách implementation có thể là:

```text
ArenaGeneration += 1
```

thay vì sửa từng handle.

Ví dụ:

```text
Handle {
    arena_generation,
    index
}
```

Sau destroy:

```text
generation mismatch
```

toàn bộ handle trở thành stale.

Đây là cách rất rẻ.

---

# 43. Identity trong Axiom không phải object-oriented identity

Axiom không cần:

```text
class Object {
    identity...
    virtual...
}
```

để hỗ trợ identity.

Có thể xây:

```text
struct EntityId
struct TextureId
struct NodeId
```

hoặc:

```text
Handle<T>
```

và kết hợp:

```text
struct + trait + function + storage
```

Đủ để xây các hệ thống lớn.

---

# 44. Quy tắc lựa chọn abstraction

Axiom nên có decision model rất rõ:

```text
Tôi cần dữ liệu?
        ↓
Value

Tôi cần sở hữu dữ liệu?
        ↓
Owner / Box / Container

Tôi chỉ cần đọc?
        ↓
view<T>

Tôi cần sửa?
        ↓
mut_view<T>

Tôi cần địa chỉ ổn định?
        ↓
Stable storage

Tôi cần identity tồn tại độc lập với địa chỉ?
        ↓
Handle<T>

Tôi cần identity chống stale reference?
        ↓
Generational Handle

Tôi cần concurrent shared access?
        ↓
Share + synchronization

Tôi cần machine address?
        ↓
raw pointer + unsafe
```

Đây là một trong những điểm mà Axiom có thể đơn giản hơn C++ rất nhiều.

---

# 45. Core vs Library

Không nên đưa toàn bộ `SlotMap`, `Pool`, `ECS` vào language core.

Core chỉ cần semantics hỗ trợ:

```text
Handle-like logical identity
```

Còn:

```text
SlotMap
StablePool
Arena
ECS
ResourceManager
EntityStore
```

là library abstractions.

Điều này giữ Core không bị phình bởi domain-specific structures.

---

# 46. Compiler có thể tối ưu Handle

Handle representation:

```text
struct {
    index: usize
    generation: u32
}
```

có thể được:

- register allocate;
- constant propagate;
- bounds-check eliminate;
- generation-check eliminate;
- inline lookup;
- devirtualize;
- vectorize bulk operations.

Không có requirement:

```text
heap allocation
object header
virtual call
runtime metadata
```

---

# 47. Handle và cache performance

Không nên lạm dụng:

```text
Handle → random lookup → object
```

trong hot loop.

Axiom data-oriented design ưu tiên:

```text
Handle
   ↓
cold/control path

view<T>
   ↓
hot/data path
```

Ví dụ:

```text
let player = players.get(id)

for transform in transforms {
    update(transform)
}
```

thay vì lookup handle cho từng entity ở mỗi instruction.

---

# 48. Handle không phải reference replacement 1:1

Đây là quyết định thiết kế quan trọng.

Axiom không nói:

> "Pointer/reference xấu, thay tất cả bằng Handle."

Mà là:

> **Pointer/reference giải quyết physical access; Handle giải quyết logical identity.**

Hai bài toán khác nhau.

Trong safe application code:

```text
view/mut_view
```

là access mechanism.

Trong long-lived systems:

```text
Handle
```

là identity mechanism.

Trong system/FFI:

```text
raw pointer
```

vẫn tồn tại.

---

# 49. FFI

Foreign APIs thường đưa:

```text
void*
HANDLE
uint64_t id
```

Axiom không tự động biến chúng thành:

```text
Handle<T>
```

Nếu foreign API cung cấp logical handle:

```text
struct WindowHandle(...)
```

có thể wrap thành Axiom newtype.

Nếu là pointer:

```text
*mut CWidget
```

vẫn là raw pointer/unsafe boundary.

---

# 50. Debugging

Generational handles có lợi thế lớn cho debugging.

Thay vì:

```text
0x7FF82A1234
```

ta có:

```text
EntityId(index=1827, generation=4)
```

Tooling có thể hiển thị:

```text
Entity #1827
Generation 4
Archetype Transform+Velocity
```

IDE/debugger có thể resolve logical identity.

Đây cũng rất tốt cho AI tooling của Axiom.

---

# 51. Serialization

Không nên serialize raw address.

Có thể serialize:

```text
EntityId
ResourceId
AssetId
```

nhưng phải phân biệt:

```text
runtime generation handle
```

với:

```text
persistent identity
```

Một generation handle không nhất thiết ổn định qua:

```text
process restart
save/load
network session
```

Nếu cần identity lâu dài:

```text
AssetId
UUID
DatabaseId
StableId
```

là abstraction khác.

---

# 52. Persistent ID ≠ Runtime Handle

Axiom chính thức phân biệt:

```text
RuntimeHandle<T>
```

và:

```text
PersistentId<T>
```

Runtime:

```text
index + generation
```

Persistent:

```text
stable serialized identity
```

Không được mặc định coi chúng là cùng một thứ.

---

# 53. Network identity

Tương tự:

```text
NetworkEntityId
```

không nên là:

```text
memory handle
```

Server có thể map:

```text
NetworkEntityId
        ↓
Handle<Entity>
```

Client cũng có mapping riêng.

Đây là cách identity không phụ thuộc memory layout.

---

# 54. Resource hot reload

Ví dụ:

```text
TextureHandle
```

texture cũ:

```text
generation 7
```

hot reload có thể:

```text
replace storage
```

mà giữ logical resource identity nếu semantics yêu cầu.

Hoặc:

```text
destroy + recreate
```

thì generation thay đổi.

Điều này phải là quyết định của resource manager, không phải language core.

---

# 55. No hidden identity

Một struct bình thường:

```text
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

không tự nhiên có:

```text
object_id
vtable
header
refcount
generation
```

Đây là invariant quan trọng.

Identity chỉ tồn tại khi programmer/library yêu cầu.

---

# 56. No mandatory object header

Ngay cả:

```text
Handle<T>
```

cũng không yêu cầu `T` chứa:

```text
generation
id
vtable
```

Metadata có thể nằm ngoài:

```text
Handle
   ↓
Container metadata
   ↓
T
```

Điều này cực kỳ tốt cho data-oriented design.

---

# 57. Handle validity và capability validity

Hai hệ thống phải được phân biệt:

```text
Handle validity
```

trả lời:

> Object identity còn tồn tại không?

Trong khi:

```text
Capability validity
```

trả lời:

> Tôi có quyền truy cập vùng dữ liệu này trong thời điểm này không?

Ví dụ:

```text
Handle<Player> h
```

có thể valid.

Nhưng:

```text
view<Player>
```

có thể không được giữ qua một operation làm relocation.

Handle sống:

```text
long
```

View sống:

```text
short
```

Đây là thiết kế rất sạch.

---

# 58. Handle + capability

Mô hình chuẩn:

```text
Handle
    ↓ resolve
Capability
    ↓
Access
```

Ví dụ:

```text
let player = players.get_mut(player_id)
```

Sau lookup:

```text
player : mut_view<Player>
```

Capability verifier vẫn áp dụng toàn bộ:

- alias;
- lifetime;
- relocation;
- ownership;
- concurrency.

Handle không bypass verifier.

---

# 59. Safe API không cần expose generation

Library có thể expose:

```text
Handle<T>
```

nhưng không cần programmer thao tác:

```text
handle.generation
```

Generation là implementation detail trừ khi API/debugging cần nó.

Điều này giúp tránh programmer nhầm rằng generation là một phần business logic.

---

# 60. Frozen semantic rules

Axiom chính thức chốt:

### Identity

**AHANDLE-20 — Value Identity Is Distinct From Storage Identity**

**AHANDLE-21 — Storage Identity Is Distinct From Logical Identity**

**AHANDLE-22 — Logical Identity Is Address-Independent**

**AHANDLE-23 — Ordinary Values Have No Implicit Object Identity**

**AHANDLE-24 — Object Headers Are Not Required For Identity**

---

### Handle

**AHANDLE-25 — Handle Is Logical Identity, Not Ownership**

**AHANDLE-26 — Handle Is Not A Memory Capability**

**AHANDLE-27 — Handle Does Not Imply Stable Address**

**AHANDLE-28 — Handle Does Not Imply Resource Lifetime**

**AHANDLE-29 — Handle Does Not Imply Send Or Share Of The Referenced Value**

**AHANDLE-30 — Typed Handles Are Preferred**

**AHANDLE-31 — Handle Copy Does Not Duplicate Ownership**

---

### Generation

**AHANDLE-32 — Generational Handles Detect Stale Slot Identity**

**AHANDLE-33 — Stale Handles Must Not Silently Resolve To A Different Object**

**AHANDLE-34 — Generation Reuse Must Respect Handle Validity Semantics**

**AHANDLE-35 — Generation Overflow Must Not Create Silent Identity Reuse**

**AHANDLE-36 — Handle Validation Is A Semantic Guarantee**

**AHANDLE-37 — Handle Validation May Be Optimized Away When Proven**

---

### Storage

**AHANDLE-38 — Relocation Must Not Change Logical Identity**

**AHANDLE-39 — Stable Address Requires Explicit Storage Contract**

**AHANDLE-40 — Stable Address Is Distinct From Logical Identity**

**AHANDLE-41 — Pool Storage May Provide Stable Slots**

**AHANDLE-42 — Arena Lifetime Bounds Arena-Allocated Identity**

**AHANDLE-43 — Bulk Arena Destruction Invalidates Dependent Handles**

---

### Capability

**AHANDLE-44 — Handle Resolution Produces An Explicit Access Capability**

**AHANDLE-45 — Handle Does Not Implicitly Become A View**

**AHANDLE-46 — Resolved Views Follow Normal Capability Rules**

**AHANDLE-47 — Handle Lifetime May Exceed Resolved Capability Lifetime**

**AHANDLE-48 — Handle Validity Is Distinct From Capability Validity**

**AHANDLE-49 — Handle Resolution Does Not Bypass Ownership Verification**

**AHANDLE-50 — Handle Resolution Does Not Bypass Concurrency Verification**

---

### Performance

**AHANDLE-51 — Handle Representation Has No Mandatory Heap Allocation**

**AHANDLE-52 — Handle Representation Has No Mandatory Object Header**

**AHANDLE-53 — Handle Lookup May Be Inlined**

**AHANDLE-54 — Proven Handle Checks May Be Eliminated**

**AHANDLE-55 — Bulk Iteration Should Prefer Direct Data Access Over Repeated Handle Lookup**

**AHANDLE-56 — Handle Semantics Do Not Guarantee Constant-Time Resolution**

---

### Concurrency

**AHANDLE-57 — Handle Is Not A Universal ABA Solution**

**AHANDLE-58 — Lock-Free Identity Requires Appropriate Synchronization Abstractions**

**AHANDLE-59 — Handle Copy Is Safe Only As A Value Operation**

**AHANDLE-60 — Concurrent Resource Access Requires Explicit Synchronization**

---

### Persistence

**AHANDLE-61 — Runtime Handle Identity Is Not Necessarily Persistent Identity**

**AHANDLE-62 — Persistent IDs Are Distinct From Runtime Generational Handles**

**AHANDLE-63 — Serialized Identity Must Not Depend On Memory Address**

**AHANDLE-64 — Network Identity Is Distinct From Runtime Storage Identity**

---

### Architecture

**AHANDLE-65 — Pointer Is Not A Replacement For Logical Identity**

**AHANDLE-66 — Handle Is Not A Replacement For Memory Capability**

**AHANDLE-67 — Safe Application Code Should Prefer Logical Identity Over Physical Address When Long-Lived Identity Is Required**

**AHANDLE-68 — Physical Address Is Observable Only Through Explicit Storage/System Contracts**

**AHANDLE-69 — Identity Mechanisms Are Library Abstractions Unless Core Semantics Require Them**

**AHANDLE-70 — Identity Must Not Imply Hidden Runtime Machinery**

---

# 61. Kiến trúc tổng thể sau BOOTSTRAP-090

Axiom hiện có một mô hình khá hoàn chỉnh:

```text
                    ┌─────────────────┐
                    │     Value       │
                    │ Copy / Move     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Ownership    │
                    │ Who owns value? │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
       ┌─────────────┐               ┌──────────────┐
       │   view<T>   │               │ mut_view<T>  │
       │    READ     │               │    WRITE     │
       └──────┬──────┘               └──────┬───────┘
              │                             │
              └──────────────┬──────────────┘
                             ▼
                       Actual Access
                             ▲
                             │
                         resolve
                             │
                       ┌─────┴─────┐
                       │ Handle<T> │
                       │ Identity  │
                       └─────┬─────┘
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
                Pool       Arena      SlotMap
                  │          │          │
                  └──────────┼──────────┘
                             ▼
                       Physical Storage
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
              Relocatable             Stable
                 storage              storage
```

Và bên cạnh đó:

```text
Send / Share
     +
Synchronization
     +
Execution Domain
```

quản lý concurrency.

---

## Kết luận kiến trúc

Sau BOOTSTRAP-090, Axiom đã giải quyết khá triệt để một vấn đề tưởng như bắt buộc phải dùng pointer:

> **Object có thể có identity lâu dài mà không cần identity đó chính là địa chỉ bộ nhớ.**

Đây là một điểm rất mạnh của thiết kế hiện tại:

```text
Pointer     → physical location
View        → temporary access capability
Owner       → ownership
Handle      → logical identity
StableBox   → stable storage contract
EntityId    → domain identity
PersistentId→ persistent identity
```

Mỗi khái niệm trả lời **một câu hỏi duy nhất**, thay vì `T*`/`T&` phải gánh quá nhiều nghĩa.

### Chuỗi kiến trúc tiếp theo

Sau identity/storage, phần hợp lý tiếp theo là **BOOTSTRAP-091 — Axiom Resource & Lifetime Architecture nâng cao**, tập trung vào một vấn đề còn rất lớn:

```text
Memory lifetime
Resource lifetime
Handle lifetime
Capability lifetime
Async lifetime
Thread lifetime
GPU in-flight lifetime
Process lifetime
```

và đặc biệt là **làm sao tất cả các lifetime này phối hợp mà không biến Axiom thành Rust/C++ phiên bản phức tạp**.