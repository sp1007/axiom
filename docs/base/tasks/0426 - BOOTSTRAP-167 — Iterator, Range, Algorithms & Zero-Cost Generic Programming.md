# BOOTSTRAP-167 — Iterator, Range, Algorithms & Zero-Cost Generic Programming
**STATUS: FROZEN / COMPLETED**

> **Axiom phải cho phép programmer viết abstraction ở mức rất cao, nhưng compiler có thể biến abstraction đó thành vòng lặp machine-level trực tiếp: không object iterator, không allocation, không virtual dispatch, không overhead nếu các semantics không yêu cầu.**

Đây là bước nối trực tiếp giữa **container system** và **optimization/vectorization engine** đã frozen trước đó.

---

## 1. Iterator không phải object runtime

Axiom không bắt buộc mô hình:

```text
Iterator object
    ↓
next()
    ↓
virtual dispatch
    ↓
heap allocation
```

Thay vào đó:

```text
Iterator<T>
```

là một **compile-time generic protocol**.

Ví dụ:

```ax
for x in values {
    process(x);
}
```

có thể lower trực tiếp thành:

```text
load
process
increment
branch
```

---

# 2. Iterator contract

Đề xuất:

```ax
trait Iterator {
    type Item;

    fn next(self: mut_view<Self>) -> Option<Self::Item>;
}
```

Nhưng đây chỉ là semantic interface.

Compiler có thể inline toàn bộ:

```text
next()
Option
match
```

thành control flow trực tiếp.

---

# 3. Không có hidden iterator allocation

Code:

```ax
let iter = values.iter();
```

không mặc định tạo heap object.

Iterator thường là:

```text
small value
```

có thể:

- register;
- stack;
- SSA;
- hoàn toàn bị eliminate.

---

# 4. Range

Range là abstraction đặc biệt quan trọng.

Ví dụ:

```ax
for i in 0..n {
    ...
}
```

Range có thể biểu diễn:

```text
start
end
step
```

nhưng compiler thường scalarize thành induction variable.

---

# 5. Range semantics

Phải phân biệt:

```text
0..n
```

và:

```text
0..=n
```

### `..`

half-open:

```text
[start, end)
```

### `..=`

inclusive:

```text
[start, end]
```

Đây cũng là semantics được dùng trong range analysis.

---

# 6. Range không phải container

```text
0..1_000_000_000
```

không tạo một tỷ phần tử.

Nó là lazy iteration domain.

Đây là abstraction compiler rất dễ optimize.

---

# 7. Reverse range

Có thể:

```ax
for i in (0..n).rev() {
    ...
}
```

Compiler nhận biết induction direction.

Không tạo collection trung gian.

---

# 8. Step

API:

```ax
(0..n).step_by(2)
```

semantic:

```text
i = start
while i < end:
    ...
    i += 2
```

Compiler có thể trực tiếp đưa step vào Scalar Evolution.

---

# 9. Overflow trong range

Không được để range arithmetic trở thành C-style undefined behavior.

Ví dụ:

```ax
i += step
```

phải có defined integer semantics.

Compiler có thể chứng minh overflow không xảy ra và loại bỏ checks.

---

# 10. Iterator adapters

Các adapter cơ bản:

```text
map
filter
filter_map
enumerate
zip
take
skip
step_by
chain
flatten
flat_map
peekable
scan
```

Tất cả đều generic.

---

# 11. `map`

```ax
values.map(fn(x) => x * 2)
```

semantic:

```text
input element
→ transform
→ output element
```

Không tạo intermediate collection.

---

# 12. `filter`

```ax
values.filter(fn(x) => x > 0)
```

không tạo danh sách mới.

Compiler có thể fuse predicate trực tiếp vào loop.

---

# 13. Map + filter fusion

Ví dụ:

```ax
let sum =
    values
        .map(fn(x) => x * 2)
        .filter(fn(x) => x > 10)
        .sum();
```

mục tiêu machine-level:

```text
for x:
    y = x * 2
    if y > 10:
        sum += y
```

Không:

```text
temporary array 1
temporary array 2
iterator objects
```

---

# 14. Fold

```ax
values.fold(0, fn(acc, x) => acc + x)
```

có thể thành:

```text
acc = 0
for x:
    acc += x
```

---

# 15. Reduce

`reduce` khác `fold` ở điểm initial value có thể lấy từ phần tử đầu.

```ax
values.reduce(fn(a, b) => a + b)
```

Empty collection phải có semantics rõ:

```text
Option<T>
```

hoặc Result tùy API.

---

# 16. `sum`

Không nhất thiết implement riêng bằng abstraction chậm.

Compiler/std có thể specialize:

```text
sum<i32>
sum<i64>
sum<f32>
sum<f64>
```

và vectorize.

---

# 17. Reduction vectorization

Ví dụ:

```ax
let sum = values.iter().sum();
```

có thể thành:

```text
vector accumulator
+
horizontal reduction
```

nếu:

- alias hợp lệ;
- FP semantics cho phép;
- target có lợi.

Strict floating point không tự động reassociate.

---

# 18. `zip`

```ax
a.iter().zip(b.iter())
```

semantic:

```text
(a[0], b[0])
(a[1], b[1])
...
```

Compiler có thể tạo một loop với hai loads.

---

# 19. Zip length

Default:

```text
zip
```

kết thúc khi iterator ngắn hơn kết thúc.

Không đọc vượt bounds.

Range analysis có thể eliminate checks khi lengths được chứng minh.

---

# 20. `zip_exact`

Có thể cung cấp API yêu cầu hai sequence có cùng length:

```text
zip_exact
```

Nếu compiler chứng minh:

```text
len(a) == len(b)
```

không cần runtime check.

Nếu không chứng minh được:

```text
Result / runtime validation
```

tùy contract.

---

# 21. `enumerate`

```ax
for (i, x) in values.enumerate() {
    ...
}
```

không tạo tuple runtime bắt buộc.

Compiler có thể giữ:

```text
i
x
```

ở hai register.

---

# 22. Pattern matching trong iterator

```ax
for Some(x) in values {
    ...
}
```

có thể lower trực tiếp thành discriminant check.

Không cần allocation.

---

# 23. `flatten`

```ax
nested.flatten()
```

có thể lower thành nested loops.

Ví dụ:

```text
for outer:
    for inner:
        process(inner)
```

---

# 24. `flat_map`

Compiler có thể fuse:

```ax
xs.flat_map(fn(x) => make_items(x))
```

nếu returned iterator/container không escape.

---

# 25. Iterator lifetime

Iterator giữ capability đối với underlying container nếu cần.

Ví dụ:

```ax
let iter = v.iter();
v.push(x);
```

nếu iterator có active view:

→ relocation/mutation conflict phải được compiler phát hiện.

---

# 26. Mutable iterator

```ax
let iter = v.iter_mut();
```

iterator mang exclusive capability.

Không cho:

```ax
let a = v.iter_mut();
let b = v.iter_mut();
```

nếu hai capability có thể overlap.

---

# 27. Disjoint iteration

Compiler có thể chứng minh:

```ax
let left = v[..mid];
let right = v[mid..];
```

là:

```text
DISJOINT
```

Sau đó:

```text
mut_view left
+
mut_view right
```

được phép đồng thời.

Đây là một trong những lợi ích lớn nhất của region-aware capability model.

---

# 28. Iterator invalidation

Mỗi iterator implementation phải có contract:

```text
preserves
invalidates
relocates
```

Ví dụ `Vec.iter()`:

```text
mutation capable of relocation
→ invalidates iterator capability
```

Compiler không cho sử dụng iterator sau đó nếu contract không đảm bảo validity.

---

# 29. Iterator over stable storage

`StablePool` có thể cung cấp iterator mà insertion không invalidate existing element views nếu contract đảm bảo.

Compiler không cần biết implementation cụ thể.

Chỉ cần contract.

---

# 30. Algorithm traits

Các algorithm generic nên dựa trên semantic requirements.

Ví dụ:

```text
sort<T: Ord>
```

không yêu cầu:

```text
T: Clone
```

nếu algorithm có thể Move/swap.

---

# 31. Swap

Compiler/std cần primitive:

```text
swap(a, b)
```

có thể lower thành register exchange hoặc move sequence.

Không cần heap temporary.

---

# 32. Sorting

Standard library:

```text
sort
sort_unstable
sort_by
sort_by_key
```

Khác nhau về:

- stability;
- allocation;
- comparator;
- complexity.

---

# 33. Stable sort

Stable sort phải bảo toàn relative order của equal keys.

Compiler không được biến thành unstable algorithm chỉ vì nhanh hơn.

---

# 34. Unstable sort

`sort_unstable` cho phép implementation mạnh hơn:

```text
introsort
quicksort
heapsort
pdqsort-like
```

Standard library có thể chọn target-specific implementation.

---

# 35. Integer sort specialization

Compiler/std có thể có specialized:

```text
radix sort
counting sort
SIMD partition
```

cho types phù hợp.

Không thay đổi semantics.

---

# 36. Search

```text
binary_search
lower_bound
upper_bound
find
find_index
```

Generic nhưng có thể specialize.

---

# 37. Bounds-check elimination

Ví dụ:

```ax
for i in 0..xs.len() {
    process(xs[i]);
}
```

Compiler chứng minh:

```text
0 <= i < len
```

→ eliminate bounds check.

Đây chính là kết quả trực tiếp của:

```text
Scalar Evolution
+
Range Analysis
+
Capability/Bounds facts
```

---

# 38. Nested loops

Ví dụ:

```ax
for i in 0..rows {
    for j in 0..cols {
        matrix[i][j] += 1;
    }
}
```

compiler có thể suy ra:

```text
0 <= i < rows
0 <= j < cols
```

và eliminate appropriate checks.

---

# 39. Range-aware indexing

Không chỉ:

```text
i < len
```

Compiler có thể biết:

```text
i + 1 < len
```

hoặc:

```text
i + 4 < len
```

để vectorize unrolled loop.

---

# 40. Iterator + vectorization

Ví dụ:

```ax
for x in a.iter().zip(b.iter()) {
    out.push(x.0 + x.1);
}
```

Compiler có thể nhận ra:

```text
contiguous a
contiguous b
contiguous output
disjoint storage
```

→ vector loop.

Không cần programmer viết SIMD.

---

# 41. Parallel iterator

Có thể có explicit API:

```text
parallel_iter()
```

nhưng không biến mọi iterator thành parallel mặc định.

Vì parallelization có thể thay đổi:

- scheduling;
- ordering;
- performance;
- floating-point reduction behavior;
- side effects.

---

# 42. Parallel map

```ax
values.par_map(f)
```

có thể yêu cầu:

```text
f is Send
f has compatible effects
output independent
```

Compiler kiểm tra.

---

# 43. Parallel reduce

Không được tự động biến:

```ax
sum()
```

thành parallel reduction nếu strict semantics không cho phép reassociation.

Có thể:

```text
parallel_sum
```

với explicit relaxed reduction semantics.

---

# 44. Deterministic parallel algorithms

Có thể có:

```text
par_map
par_reduce
par_sort
```

và profile:

```text
deterministic
```

để đảm bảo kết quả/ordering theo contract.

---

# 45. Side effects

Iterator:

```ax
map(fn(x) => print(x))
```

không được compiler tự ý reorder/fuse nếu IO observable.

Effect system quyết định legality.

---

# 46. Pure iterator pipelines

Nếu closure:

```text
Pure
```

compiler có nhiều freedom.

Ví dụ:

```text
map
filter
reduce
```

có thể:

- inline;
- fuse;
- reorder;
- vectorize;

theo semantics.

---

# 47. Effectful iterator pipelines

Nếu closure có:

```text
IO
Atomic
Synchronize
Foreign
Volatile
```

optimization phải bảo toàn ordering/effects.

---

# 48. Iterator abstraction và async

Không để:

```text
Iterator
```

và:

```text
AsyncStream
```

trộn semantic.

Có thể có:

```text
AsyncIterator
```

riêng.

---

# 49. AsyncIterator

```ax
while let Some(x) = stream.next().await {
    process(x);
}
```

`await` là suspension boundary.

Compiler kiểm tra:

- values live across await;
- capabilities;
- Send nếu task migratable;
- resource ownership.

---

# 50. Async iterator fusion

Compiler vẫn có thể fuse:

```text
next()
await
map
filter
```

nhưng không được loại bỏ suspension semantics nếu observable.

---

# 51. Stream

`Stream<T>` có thể là library abstraction:

```text
poll_next()
```

hoặc async iterator interface.

Không phải runtime primitive.

---

# 52. Collection → iterator

Các container chuẩn nên cung cấp:

```text
iter()
iter_mut()
into_iter()
```

với semantics khác nhau.

### `iter`

READ capability.

### `iter_mut`

WRITE capability.

### `into_iter`

MOVE ownership từ container.

---

# 53. `into_iter`

Ví dụ:

```ax
let v = Vec(...);

for x in v.into_iter() {
    consume(x);
}
```

`v` bị move.

Compiler không cần copy elements.

---

# 54. Partial consumption

Nếu iterator consume container và loop break giữa chừng:

compiler phải đảm bảo:

```text
remaining elements
```

vẫn được Drop đúng semantics.

Không leak.

---

# 55. Iterator Drop

Iterator itself có thể có Drop.

Compiler có thể eliminate Drop nếu trivial.

Nếu iterator owns resources:

```text
Drop
```

vẫn observable.

---

# 56. Lazy vs eager APIs

`map/filter/take`:

```text
lazy
```

`collect`:

```text
eager
```

Ví dụ:

```ax
let result =
    xs.iter()
      .map(f)
      .filter(p)
      .collect<Vec<_>>();
```

`collect` là nơi materialization xảy ra.

Compiler có thể allocate trực tiếp final Vec.

---

# 57. `collect` specialization

Compiler biết target container:

```text
collect<Vec<T>>
```

có thể:

1. estimate size;
2. reserve;
3. fill directly;
4. eliminate intermediate iterators.

---

# 58. Size hints

Iterator có thể cung cấp:

```text
size_hint()
```

nhưng đây là optimization fact, không phải semantic proof nếu chỉ là lower bound/upper bound.

Compiler không được coi heuristic size hint là memory-safety proof.

---

# 59. Exact size

Trait:

```text
ExactSizeIterator
```

có thể guarantee:

```text
remaining_count == exact length
```

Nếu verified, compiler/std có thể reserve chính xác.

---

# 60. Trusted iterator contracts

Một iterator implementation có thể cung cấp:

```text
TrustedLength
```

nhưng đây phải là compiler-verified/trusted implementation property.

Programmer không được gắn annotation để nói dối compiler.

---

# 61. Fused iterator

Iterator có thể có contract:

```text
FusedIterator
```

sau khi trả `None`, tiếp tục `next()` vẫn `None`.

Compiler có thể exploit nếu observable semantics phù hợp.

---

# 62. Random access iterator

Trait/property:

```text
RandomAccessIterator
```

cho phép:

```text
nth(i)
```

O(1).

Không cần ép mọi iterator thành random-access.

---

# 63. Bidirectional iterator

```text
next()
prev()
```

cho phép reverse traversal.

Compiler có thể map `.rev()` trực tiếp vào decrement loop.

---

# 64. Contiguous iterator

Đây là property rất quan trọng cho vectorization:

```text
ContiguousIterator<T>
```

có thể expose:

```text
logical sequence
↔ contiguous storage
```

Compiler có thể nhận biết memory stride.

---

# 65. Strided iterator

Có thể:

```text
StridedIterator<T>
```

với:

```text
base
stride
count
```

hữu ích cho:

- matrix columns;
- SoA;
- image channels;
- tensor views.

Compiler có thể vectorize nếu stride phù hợp.

---

# 66. Algorithms should consume capabilities

Ví dụ:

```ax
fn sort<T: Ord>(x: mut_view<T>)
```

không cần:

```text
pointer + length
```

ở source level.

ABI lowering có thể thành:

```text
pointer
length
```

nếu target phù hợp.

---

# 67. Algorithm contracts

Ví dụ `sort` cần:

```text
WRITE capability
READ/compare capability
```

Không cần ownership.

Vì vậy:

```ax
sort(view)
```

không hợp lệ nếu mutation cần thiết.

```ax
sort(mut_view)
```

hợp lệ.

---

# 68. Algorithm parallel safety

Parallel algorithm có thể yêu cầu:

```text
Send<T>
Share<T>
```

tùy execution strategy.

Compiler derive từ closure/element type.

---

# 69. No hidden cloning in algorithms

Ví dụ:

```ax
sort(mut_view<T>)
```

không được âm thầm clone toàn bộ collection để tránh alias issues.

Nếu algorithm cần buffer:

- API phải contract;
- compiler có thể optimize allocation;
- hoặc dùng in-place algorithm.

---

# 70. Generic specialization

Ví dụ:

```ax
fn sum<T: Add + Zero>(xs: view<T>) -> T
```

compiler có thể tạo:

```text
sum<i32>
sum<i64>
sum<f32>
...
```

và mỗi specialization có machine strategy riêng.

---

# 71. Representation specialization

Nếu hai `T` có representation tương đương và semantics cho phép, compiler có thể share machine implementation.

Ví dụ:

```text
Wrapper<i32>
NewType<i32>
```

có thể cùng machine representation nhưng vẫn giữ semantic type identity.

---

# 72. Algorithm specialization

Có thể specialize:

```text
sort<i32>
```

thành optimized integer sort.

Không cần source-level overload explosion.

---

# 73. Const generic algorithms

Ví dụ:

```ax
fn dot<const N: usize>(
    a: [f32; N],
    b: [f32; N]
) -> f32
```

Compiler biết `N`.

Có thể:

- unroll;
- vectorize;
- specialize.

---

# 74. Small N

Với:

```text
N = 3
N = 4
N = 8
```

compiler có thể scalarize hoàn toàn.

Không cần runtime loop.

---

# 75. Large N

Với runtime N:

```text
for
```

được tối ưu bằng:

```text
vectorization
unrolling
remainder loop
```

theo target cost model.

---

# 76. Algorithm semantics vs optimization

Không được để:

```text
-O3
```

thay đổi:

```text
sort stability
iterator ordering
side effects
error behavior
panic semantics
```

Optimization chỉ thay đổi implementation.

---

# 77. Iterator error propagation

Có thể có:

```ax
for x in reader.iter()? {
    ...
}
```

hoặc:

```ax
reader.map(|x| x?)
```

Compiler lower `?` thành control flow.

Không cần exception machinery.

---

# 78. Iterator + Result

Ví dụ:

```text
Iterator<Result<T,E>>
```

và:

```text
collect<Result<Vec<T>,E>>
```

có thể specialize thành một loop:

```text
for:
    value = next()
    if error:
        cleanup
        return error
    append(value)
```

---

# 79. Iterator + Option

Tương tự:

```text
Iterator<Option<T>>
```

có thể optimize discriminant handling.

Niche representation có thể giảm overhead.

---

# 80. Core principle

Chốt:

> **Iterator là semantic protocol; iterator object là một possible representation, không phải requirement.**

---

# 81. Compiler boundary

Compiler không cần special-case:

```text
map
filter
fold
```

bằng tên function.

Thay vào đó:

```text
inline
+
generic specialization
+
effect analysis
+
escape analysis
+
range analysis
+
loop optimization
+
vectorization
```

tự nhiên tạo ra fusion.

---

# 82. Khi nào compiler không fuse?

Nếu abstraction có observable identity:

```text
function pointer
dynamic trait object
address escape
FFI boundary
reflection
opaque external call
```

thì không được giả định có thể erase.

---

# 83. Iterator as zero-cost abstraction test

Một benchmark chuẩn của Axiom sẽ là:

```ax
let s =
    values
        .iter()
        .map(f)
        .filter(p)
        .map(g)
        .sum();
```

So với hand-written loop.

Mục tiêu:

```text
same semantics
same or equivalent optimized machine code
```

không phải “iterator nhanh hơn loop” một cách thần kỳ.

---

# 84. AI/compiler inspection

Đề xuất:

```text
axc inspect iterator foo
axc inspect iterator foo --pipeline
axc inspect fusion foo
axc inspect range foo
axc inspect bounds foo
axc inspect algorithm foo
axc inspect vectorize foo
```

Ví dụ:

```text
Iterator pipeline:
    iter
    → map
    → filter
    → map
    → sum

Fusion:
    successful

Intermediate allocations:
    0

Bounds checks:
    4 proven removable
    0 remaining

Vectorization:
    AVX2 x 8 lanes

Dynamic dispatch:
    none
```

Đây rất phù hợp với mục tiêu **AI-native compiler** của Axiom.

---

# 85. Frozen invariants

### `AITER-20`
Iterator is a semantic protocol, not a mandatory runtime object.

### `AITER-21`
Iterator implementations may be fully erased by optimization when semantics permit.

### `AITER-22`
Iterator creation does not imply heap allocation.

### `AITER-23`
Iterator adapters preserve deterministic semantic ordering.

### `AITER-24`
Range iteration uses explicit half-open/inclusive semantics.

### `AITER-25`
Range arithmetic follows Axiom's defined integer semantics.

### `AITER-26`
Reverse and stepped ranges preserve their documented traversal order.

### `AITER-27`
`map` is lazy unless explicitly materialized.

### `AITER-28`
`filter` does not implicitly allocate.

### `AITER-29`
Iterator fusion may remove intermediate abstractions when unobservable.

### `AITER-30`
Fusion cannot remove observable effects.

### `AITER-31`
Iterator capabilities preserve owner provenance.

### `AITER-32`
Mutable iterators provide exclusive capabilities.

### `AITER-33`
Overlapping mutable iteration is rejected unless disjointness is proven.

### `AITER-34`
Iterator invalidation rules are explicit semantic contracts.

### `AITER-35`
Container mutation cannot invalidate a live safe iterator capability.

### `AITER-36`
`iter`, `iter_mut` and `into_iter` have distinct access/ownership semantics.

### `AITER-37`
`into_iter` transfers element ownership rather than implicitly cloning.

### `AITER-38`
Partially consumed owning iterators preserve Drop correctness for remaining elements.

### `AITER-39`
Iterator Drop follows ordinary Axiom deterministic cleanup.

### `AITER-40`
`fold` preserves sequential semantics unless an explicitly different reduction contract is selected.

### `AITER-41`
Parallel reduction cannot silently alter strict floating-point semantics.

### `AITER-42`
`zip` never reads beyond either iterator's valid range.

### `AITER-43`
Exact-size iterator contracts may improve allocation/optimization decisions but do not replace semantic verification.

### `AITER-44`
Iterator hints are not memory-safety proofs.

### `AITER-45`
Trusted iterator properties must originate from verified/trusted implementations.

### `AITER-46`
Random-access iterator properties expose explicit complexity guarantees.

### `AITER-47`
Contiguous iterators may expose layout information required for vectorization.

### `AITER-48`
Strided iterators expose explicit stride semantics.

### `AITER-49`
Algorithm requirements are expressed through semantic traits/capabilities.

### `AITER-50`
Algorithms cannot silently introduce Clone operations.

### `AITER-51`
Algorithms may specialize for concrete representations.

### `AITER-52`
Const-generic algorithms may specialize on compile-time dimensions.

### `AITER-53`
Generic iterator code remains subject to ordinary ownership/capability verification.

### `AITER-54`
Generic iterator code remains subject to ordinary Send/Share verification.

### `AITER-55`
Iterator closures retain their ordinary effect semantics.

### `AITER-56`
IO/atomic/volatile/foreign effects constrain iterator transformation.

### `AITER-57`
Async iteration is semantically distinct from synchronous iteration.

### `AITER-58`
Async iterator suspension points retain normal await verification.

### `AITER-59`
Iterator pipelines may be compiled directly into loops.

### `AITER-60`
Iterator pipelines may be vectorized when legality and profitability are proven.

### `AITER-61`
Iterator pipelines may be parallelized only when explicit semantics permit.

### `AITER-62`
Parallel algorithms preserve their documented ordering/result guarantees.

### `AITER-63`
`Result`/`Option` propagation through iterators preserves cleanup and early-return semantics.

### `AITER-64`
Intermediate allocations may be eliminated when escape and identity permit.

### `AITER-65`
Iterator abstraction erasure cannot cross observable ABI/FFI/reflection boundaries incorrectly.

### `AITER-66`
Optimization level cannot alter iterator semantics.

### `AITER-67`
Iterator optimization relies on generic compiler analyses rather than type-name-specific hacks where practical.

### `AITER-68`
Iterator and algorithm decisions are inspectable through compiler tooling.

### `AITER-69`
Bounds-check elimination requires semantic proof, not profile evidence alone.

### `AITER-70`
Iterator optimization cannot weaken the safety verifier.

### `AITER-71`
Iterator APIs must remain usable without programmer-written lifetimes.

### `AITER-72`
Iterator APIs should expose enough structure for zero-cost generic compilation.

### `AITER-73`
Standard algorithms should have predictable complexity contracts.

### `AITER-74`
Stable algorithm properties such as sort stability are semantic and cannot be optimized away.

### `AITER-75`
Axiom's iterator system is intended to make high-level and hand-written low-level loops converge at optimized machine level.

---

# Kiến trúc tổng hợp sau BOOTSTRAP-167

Đến đây, chuỗi abstraction đã khá rõ:

```text
                     SOURCE
                       │
                       ▼
                  Generic API
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          Container           Iterator
             │                   │
             └─────────┬─────────┘
                       ▼
                  Generic MIR
                       │
              Ownership/Capability
                       │
             Alias / Effect / Escape
                       │
                       ▼
                     SSA
                       │
                  MemorySSA
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Fusion       Range        SROA
          │            │            │
          └────────────┼────────────┘
                       ▼
                   Loop Opt
                       │
                  Vectorization
                       │
                 Microarchitecture
                       │
                       ▼
                    MACHINE
```

Điểm quan trọng là **không cần xây một “Iterator Optimizer” khổng lồ**. Iterator chỉ là test case rất mạnh chứng minh rằng hệ thống generic + ownership + effects + escape + SSA + loop optimizer của Axiom thực sự hoạt động.

---

# BOOTSTRAP-168 — Numeric System, SIMD Types, Math Semantics & Fast Numerical Computing

Bước kế tiếp nên chốt **hệ thống số của Axiom**, vì đây là nền móng cho:

- CPU SIMD;
- GPU;
- tensor;
- AI/ML;
- scientific computing;
- graphics;
- game engine;
- DSP;
- crypto;
- compiler optimization.

Đặc biệt cần giải quyết một vấn đề quan trọng: **Axiom có primitive vector/matrix trong Core hay chỉ có scalar primitive + `std::simd` + compiler vector IR?**

Đây là quyết định kiến trúc lớn và nên chốt trước khi đi sâu thêm vào GPU/tensor/AI.