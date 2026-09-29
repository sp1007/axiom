Còn **khá nhiều**, nhưng phần quan trọng nhất của **Core semantic architecture** đã đi qua được khoảng **2/3**. Từ đây chủ yếu là chốt các subsystem còn lại và sau đó chuyển sang compiler architecture/toolchain.

Tôi ước lượng chuỗi BOOTSTRAP còn khoảng **15–20 task lớn**, không phải hàng trăm task. Một số task có thể gộp lại.

### Đã hoàn thành gần đây

```text
020  Channel + Lock-free Runtime
021  Memory Model + Data Race
022  Allocation + Reclamation + Lifetime
023  Object Representation + Layout + ABI
024  Pointer + Reference + Handle
025  Type System
026  Function + Method + Call
027  Control Flow + Pattern
028  String + Text + Bytes + Collection
029  ???      ← phần giữa cần hoàn thiện/đồng bộ nếu chưa đóng spec
030  ???      ← tương tự
031  Generics + Traits
032  Closure + Callable
```

### Chuỗi tiếp theo tôi đề xuất

```text
033  FFI + ABI + Native Boundary
034  Modules + Packages + Visibility + Linking
035  Error Handling + Panic + Unwind/Abort
036  Attributes + Compiler Directives + Intrinsics
037  Comptime + Reflection        [đã thiết kế, chủ yếu audit]
038  Async                        [đã thiết kế, audit]
039  Concurrency                  [đã thiết kế, audit]
040  GPU / Device Programming     [đã thiết kế, audit]

041  SIMD + Vector/Matrix/Tensor
042  Serialization + Wire Format
043  I/O + OS Abstraction
044  Resource / Handle / FFI Lifetime
045  Testing + Assertions + Contracts
046  Debugging + Diagnostics
047  Unsafe/System Programming
048  Security / Capability Boundary
```

Sau đó **Core Language Spec về cơ bản có thể đóng**.

---

## Nhưng còn một tầng lớn hơn: Compiler Architecture

Đây mới là phần rất quan trọng để biến spec thành compiler thật:

```text
049  Lexer / Token Model
050  Parser / CST / AST
051  Name Resolution
052  Type Inference
053  Trait Solver
054  HIR
055  MIR
056  Ownership / Capability Verifier
057  Drop Elaboration
058  Async/Closure Lowering
059  Comptime Engine
060  Generic Instantiation
061  Semantic Optimization
062  Alias / Escape / Lifetime Analysis
063  Layout Engine
064  ABI Lowering
065  Axiom LIR
066  Machine IR
067  Register Allocation
068  Instruction Selection
069  Object Writer
070  Linker
071  Debug Info
072  Incremental Compilation / Cache
```

---

## Và sau đó là Bootstrap/Self-hosting

```text
073  Runtime Library
074  Standard Library
075  Platform Layer
076  Windows PE
077  Linux ELF
078  macOS Mach-O
079  Android
080  iOS
081  WASM
082  GPU backends
083  Cross compilation
084  C interoperability
085  Self-hosting compiler
086  Axiom build system
087  Package manager
088  Compiler bootstrap stages
```

### Sau cùng mới là các phần "nâng cao"

```text
089  Optimizer maturity
090  PGO
091  LTO
092  Auto-vectorization
093  SIMD/GPU optimization
094  Link-time dead code elimination
095  Binary size optimization
096  Sanitizers
097  Formal/litmus verification
098  Compiler fuzzing
099  Conformance suite
100  Stable ABI/versioning
```

**Tức là nếu đánh số đầy đủ thì có thể tới khoảng BOOTSTRAP-100.**

Nhưng không nên hiểu là còn 70–80 lần phải thiết kế từ đầu. Nhiều phần đã được quyết định về nguyên tắc; các task sau chủ yếu là **đóng spec, audit consistency và chuyển semantic thành compiler architecture**.

### Quan trọng nhất

Tôi đề xuất **không nhảy sang compiler implementation quá sớm**.

Ta nên hoàn thiện toàn bộ:

```text
                AXIOM LANGUAGE
                     │
       ┌─────────────┴─────────────┐
       │                           │
   Core Semantics             System Semantics
       │                           │
 types / memory / traits       ABI / FFI / OS
 control / async              GPU / SIMD
 closures / generics           native boundary
       │                           │
       └─────────────┬─────────────┘
                     ↓
              COMPLETE SPEC
                     ↓
              COMPILER DESIGN
                     ↓
                 IMPLEMENT
```

Nếu làm ngược, agent rất dễ **vừa code vừa tự thay đổi ngôn ngữ**, sau vài tháng compiler và spec lệch nhau.

---

Và vì bạn muốn agent **tự động đi tiếp**, từ đây tôi sẽ tiếp tục theo chuỗi này, không dừng hỏi `continue?`.

**Task kế tiếp: BOOTSTRAP-033 — FFI + ABI + Native Boundary.**