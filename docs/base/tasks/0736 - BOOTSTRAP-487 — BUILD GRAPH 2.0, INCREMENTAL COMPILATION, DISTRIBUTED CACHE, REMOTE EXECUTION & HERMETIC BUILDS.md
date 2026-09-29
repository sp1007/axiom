# BOOTSTRAP-487 — BUILD GRAPH 2.0, INCREMENTAL COMPILATION, DISTRIBUTED CACHE, REMOTE EXECUTION & HERMETIC BUILDS

**Trạng thái: COMPLETED / LOCKED**

487 nâng build system của Axiom từ incremental compilation cơ bản thành một **content-addressed, dependency-aware, hermetic build engine**, có thể tận dụng cache local/remote và remote execution nhưng **không bắt buộc**.

Kiến trúc tổng thể:

```text id="f3k8w2"
                    Axiom Project
                         │
                  Manifest / Config
                         │
                    Build Graph
                         │
              ┌──────────┼──────────┐
              ↓          ↓          ↓
          Source      Dependency   Toolchain
          Nodes         Nodes        Nodes
              │          │          │
              └──────────┼──────────┘
                         ↓
                  Semantic Queries
                         │
                  Compilation Graph
                         │
              ┌──────────┼──────────┐
              ↓          ↓          ↓
          Local Cache  Remote Cache  Remote Exec
              │          │          │
              └──────────┼──────────┘
                         ↓
                     Artifacts
                         │
                     Link / Package
```

---

## 487.1 — Build graph ≠ dependency graph

Dependency graph trả lời:

> Package/module nào phụ thuộc module nào?

Build graph trả lời:

> Artifact nào cần được tạo từ những inputs nào bằng operation nào?

Ví dụ:

```text id="x7p4m1"
source.ax
    ↓
parse
    ↓
HIR
    ↓
MIR
    ↓
codegen
    ↓
object.o
    ↓
link
    ↓
app.exe
```

---

## 487.2 — Build node

Canonical representation:

```text id="q8n2v5"
BuildNode {
    id
    operation
    inputs[]
    environment
    toolchain
    target
    configuration
    outputs[]
}
```

---

## 487.3 — Build edge

Edge biểu diễn dependency giữa build nodes.

---

## 487.4 — Node identity

Build node identity phải content-based:

```text id="m4r9k2"
NodeKey =
    hash(
        operation
        inputs
        toolchain
        target
        configuration
        declared_environment
    )
```

---

## 487.5 — Source content hash

Source file được nhận diện bằng:

```text id="c1x7p8"
FileId
ContentHash
```

không chỉ timestamp.

---

## 487.6 — Timestamp

Timestamp chỉ là optimization hint để phát hiện thay đổi nhanh.

Không phải correctness authority.

---

## 487.7 — Semantic dependency

Compiler có thể biết function A chỉ phụ thuộc semantic declaration của B thay vì toàn bộ file B.

---

## 487.8 — Fine-grained invalidation

Ví dụ:

```text id="h5w2n9"
B private implementation changes
        ↓
A's API unchanged
        ↓
some downstream queries remain valid
```

---

## 487.9 — Query-level cache

436 query architecture cho phép cache riêng:

```text id="v7k3q1"
parse
resolve
type_of
layout
trait_impl
const_eval
lower
codegen
```

---

## 487.10 — Artifact cache

Artifact cache có thể chứa:

- AST;
- semantic metadata;
- MIR;
- object;
- library;
- executable;
- documentation;
- test results.

---

## 487.11 — Cache ≠ source of truth

Cache mất hoặc bị xóa không được làm project mất correctness.

---

## 487.12 — Content-addressed cache

Artifact được address bằng content-derived key.

---

## 487.13 — Cache metadata

Mỗi entry:

```text id="r6m1z8"
key
artifact type
size
hash
producer
dependencies
target
compiler
schema
```

---

## 487.14 — Cache validation

Cache hit phải validate identity/provenance trước khi sử dụng.

---

## 487.15 — Corrupt cache

Corrupt/malformed cache entry:

```text id="j2p8x4"
invalidate
→ rebuild
```

Không làm compiler crash.

---

## 487.16 — Local cache

Local cache là default.

---

## 487.17 — Remote cache

Remote cache là optional.

---

## 487.18 — Remote cache protocol

Conceptual operations:

```text id="s5v0q7"
has(key)
get(key)
put(key, artifact)
```

---

## 487.19 — Cache immutability

Một content-addressed cache object sau khi publish không được mutate.

---

## 487.20 — Cache trust

Downloaded artifact phải được integrity-check.

---

## 487.21 — Remote cache không được tự động trusted

Artifact cần verify:

```text id="p4n8w1"
hash
producer
toolchain identity
target
schema
```

---

## 487.22 — Cache namespace

Cache có thể namespace theo:

```text id="z3k7m2"
compiler
platform
organization
project
```

---

## 487.23 — Cache sharing

Sharing artifact chỉ an toàn nếu semantic/toolchain identity compatible.

---

## 487.24 — Generic instance cache

447 precompiled generic instances tích hợp build graph.

---

## 487.25 — LTO cache

LTO artifacts có thể cache nếu toàn bộ relevant inputs match.

---

## 487.26 — Link cache

Link result có thể cache nếu:

```text id="n9q4c6"
objects
link options
target
linker version
SDK
layout
```

match.

---

## 487.27 — Build configuration

Configuration từ 470 là build graph input.

---

## 487.28 — Environment

Chỉ environment variables được khai báo mới trở thành build inputs.

---

## 487.29 — Hermetic build

Hermetic build nghĩa operation chỉ được quan sát inputs đã khai báo.

---

## 487.30 — Hidden filesystem dependency

Compiler/build operation không được đọc arbitrary files ngoài declared inputs.

---

## 487.31 — Hidden network dependency

Build không được âm thầm tải network resource.

---

## 487.32 — Hidden clock dependency

Build result không được phụ thuộc current time trừ khi explicitly declared.

---

## 487.33 — Randomness

Random input phải explicit và reproducibly seeded nếu build artifact phụ thuộc nó.

---

## 487.34 — Process environment

PATH, HOME, locale, environment variables... không được implicit build dependencies.

---

## 487.35 — Tool discovery

Nếu external tool được dùng:

```text id="w5r1k8"
tool path
tool identity
tool version
```

phải trở thành build input.

---

## 487.36 — Compiler itself

Compiler identity là build input:

```text id="f2m8q4"
compiler build ID
version
edition
```

---

## 487.37 — Target SDK

483 SDK identity/hash là build input.

---

## 487.38 — Dependency graph

Package lock state là build input.

---

## 487.39 — Reproducible environment

Build environment có thể được materialize thành manifest:

```text id="k7p2n5"
BuildEnvironment {
    compiler
    target
    sdk
    dependencies
    features
    declared_env
    tools
}
```

---

## 487.40 — Build sandbox

Hermetic operations có thể chạy sandboxed.

Sandbox implementation là platform-specific.

---

## 487.41 — Sandboxing ≠ language safety

Build sandbox bảo vệ host khỏi build actions.

445 language safety bảo vệ program execution.

Hai lớp độc lập.

---

## 487.42 — Build scripts

Build script là external build operation.

Nó phải khai báo:

- inputs;
- outputs;
- environment;
- tools;
- network requirement.

---

## 487.43 — Build script network

Network access phải explicit capability.

---

## 487.44 — Build script filesystem

Filesystem access phải explicit input/output scope nếu hermetic mode bật.

---

## 487.45 — Generated source

Generated source trở thành build graph node:

```text id="u6x3m9"
generator
 + inputs
 → generated source
```

---

## 487.46 — Resource compiler

469 resource compiler cũng là build graph node.

---

## 487.47 — Documentation

485 documentation generation là build graph node.

---

## 487.48 — Tests

Test compilation/execution là build graph node.

---

## 487.49 — Benchmarks

Benchmark execution là build graph node nhưng result artifact phải phân biệt với deterministic compilation artifact.

---

## 487.50 — Profile-guided builds

PGO profile là explicit build input.

---

## 487.51 — Stale profile

Profile không match binary/source/toolchain phải bị đánh dấu stale.

---

## 487.52 — Sanitizer builds

Sanitizer configuration là build graph input.

---

## 487.53 — Debug builds

Debug level/optimization/debug info là inputs.

---

## 487.54 — Feature resolution

Package features từ 432/484 trở thành graph inputs.

---

## 487.55 — Target matrix

Build graph có thể expand:

```text id="e4m8x2"
targets × profiles × features
```

---

## 487.56 — Parallel execution

Independent nodes có thể execute parallel.

---

## 487.57 — Deterministic scheduling

Parallel execution không được thay đổi build semantics.

---

## 487.58 — Failure propagation

Nếu dependency node fail, dependent nodes không được chạy như thể dependency thành công.

---

## 487.59 — Cancellation

Build cancellation phải:

- stop new work;
- cancel cancellable work;
- cleanup temporary artifacts.

---

## 487.60 — Partial results

Completed immutable cache objects vẫn có thể giữ lại sau cancellation.

---

## 487.61 — Atomic outputs

Final artifact publication phải atomic.

---

## 487.62 — Temporary files

Incomplete artifact không được xuất hiện như valid final artifact.

---

## 487.63 — Remote execution

Remote execution là optional:

```text id="y1c5m7"
BuildNode
   ↓
Scheduler
   ↓
Remote Worker
   ↓
Artifact
```

---

## 487.64 — Execution requirements

Remote worker phải match:

```text id="r3n8k2"
target
toolchain
SDK
declared environment
CPU features
sandbox policy
```

---

## 487.65 — Worker identity

Worker identity/version có thể là build input nếu operation phụ thuộc implementation.

---

## 487.66 — Reproducible remote execution

Same NodeKey phải produce semantically identical artifact.

Binary byte identity là mục tiêu nếu toolchain/platform cho phép deterministic emission.

---

## 487.67 — Remote execution security

Worker không được nhận secrets ngoài declared inputs.

---

## 487.68 — Secret handling

Secrets không được đưa vào cache keys hoặc artifacts.

---

## 487.69 — Cache poisoning

Artifact verification phải ngăn artifact giả mạo key.

---

## 487.70 — Remote cache poisoning

Remote cache response phải verify cryptographically/content-wise trước use.

---

## 487.71 — Build provenance

Mỗi artifact có:

```text id="c8w2m5"
inputs
operations
toolchain
target
worker
cache provenance
```

---

## 487.72 — Build explanation

Tool:

```text id="m7q1x9"
axiom build --explain
```

có thể cho biết tại sao node được rebuild.

---

## 487.73 — Rebuild reason

Ví dụ:

```text id="n4k8p2"
source changed
API changed
compiler changed
SDK changed
dependency changed
feature changed
cache missing
```

---

## 487.74 — AI build query

AI API:

```text id="z8r3w6"
why_rebuilt(node)
why_invalidated(symbol)
cache_status(node)
dependency_graph()
build_path(target)
```

---

## 487.75 — Build graph visualization

Có thể export:

```text id="q2m7x5"
JSON
DOT
HTML
```

---

## 487.76 — Critical path

Build system có thể xác định critical path để tối ưu compile time.

Không tạo aggregate project quality score.

---

## 487.77 — Resource scheduling

Scheduler có thể giới hạn:

```text id="h6p1v9"
CPU
RAM
disk
network
GPU
```

---

## 487.78 — Memory pressure

Compiler phải tránh spawning unlimited compilation workers.

---

## 487.79 — Disk pressure

Cache eviction có thể dùng:

```text LRU
size budget
age
cost
```

---

## 487.80 — Cache eviction correctness

Evict cache chỉ làm rebuild, không làm project invalid.

---

## 487.81 — Remote/local preference

Policy có thể chọn:

```text id="b9w2c6"
local-first
remote-first
cache-first
offline
```

---

## 487.82 — Offline mode

Offline mode cấm:

- remote cache;
- remote execution;
- package download;
- network build scripts.

---

## 487.83 — Air-gapped builds

Có thể build hoàn toàn offline nếu inputs local.

---

## 487.84 — Rebuild determinism

Repeated build với cùng inputs phải tạo equivalent artifacts.

---

## 487.85 — Byte reproducibility

Toolchain có thể yêu cầu bit-for-bit reproducibility.

---

## 487.86 — Non-deterministic platform metadata

Nếu platform embeds nondeterministic information, linker phải có deterministic mode hoặc record difference.

---

## 487.87 — Build timestamps

Không embed current timestamp mặc định.

---

## 487.88 — Build IDs

Build ID có thể content-derived.

---

## 487.89 — Path normalization

Absolute host paths không được leak vào release artifacts nếu reproducibility mode yêu cầu.

---

## 487.90 — Debug paths

Debug information có thể dùng source remapping/path normalization.

---

## 487.91 — Incremental correctness

Incremental result phải equivalent với clean build.

Đây là invariant quan trọng.

---

## 487.92 — Cache invalidation correctness

False cache hit là correctness failure.

False cache miss chỉ là performance loss.

---

## 487.93 — Build graph persistence

Build graph metadata có thể persist giữa compiler invocations.

---

## 487.94 — Compiler daemon

436 compiler daemon có thể giữ graph in-memory.

---

## 487.95 — Crash recovery

Compiler crash không được để graph metadata ở trạng thái khiến subsequent clean build sai.

---

## 487.96 — Versioned graph schema

Build graph schema có version.

---

## 487.97 — Schema migration

Old graph có thể invalidate/rebuild khi incompatible.

---

## 487.98 — Distributed cache garbage collection

Unused remote artifacts có thể được GC theo retention policy.

---

## 487.99 — Artifact ownership

Project/user/organization ownership phải rõ khi dùng shared cache.

---

## 487.100 — Build access control

Private project artifact không được publish vào public cache.

---

## 487.101 — Dependency confidentiality

Private dependency source/metadata không được leak qua cache keys/logs.

---

## 487.102 — Build logs

475 integration cho phép structured build logs.

---

## 487.103 — Build tracing

476 có thể profile build graph.

---

## 487.104 — Build benchmark

450 theo dõi:

```text id="s4n8q1"
clean build
incremental build
cache-hit build
distributed build
```

---

## 487.105 — Build performance attribution

Compiler phải phân biệt:

```text id="v2m7c5"
front-end
semantic
codegen
link
cache
scheduler
I/O
remote transfer
```

---

## 487.106 — AI optimization

AI có thể tìm:

- repeated rebuild;
- poor cache hit;
- oversized dependency;
- critical-path bottleneck.

Không tự động kết luận nguyên nhân nếu evidence không đủ.

---

## 487.107 — Build graph API

Canonical API:

```text id="j6p3w8"
graph.nodes()
graph.dependencies(node)
graph.dependents(node)
graph.explain(node)
graph.artifacts(node)
```

---

## 487.108 — Hard invariants

1. Build graph khác dependency graph.
2. Build nodes có operation/input/output.
3. Node identity content-based.
4. Source content hash là correctness input.
5. Timestamp không phải correctness authority.
6. Semantic dependencies được hỗ trợ.
7. Fine-grained invalidation được hỗ trợ.
8. Compiler queries có cache.
9. Artifacts có thể cache.
10. Cache không phải source of truth.
11. Cache content-addressed.
12. Cache entries có provenance.
13. Cache hit phải verify.
14. Corrupt cache phải rebuild.
15. Local cache là default.
16. Remote cache optional.
17. Remote cache immutable.
18. Remote cache không implicit trusted.
19. Cache sharing cần compatible identity.
20. Generic cache tích hợp.
21. LTO cache tích hợp.
22. Link cache tích hợp.
23. Config là graph input.
24. Environment dependencies phải explicit.
25. Hermetic builds được hỗ trợ.
26. Hidden filesystem dependency bị cấm trong hermetic mode.
27. Hidden network dependency bị cấm.
28. Hidden clock dependency bị cấm.
29. Randomness dependency phải explicit.
30. Tool discovery phải deterministic.
31. Compiler identity là input.
32. SDK identity là input.
33. Dependency lock là input.
34. Build environment có manifest.
35. Build sandbox được hỗ trợ.
36. Build sandbox khác language safety.
37. Build scripts là graph nodes.
38. Build script network phải explicit.
39. Generated source là graph node.
40. Resource compilation là graph node.
41. Documentation là graph node.
42. Tests là graph nodes.
43. Benchmarks phân biệt khỏi deterministic build artifacts.
44. PGO profiles là explicit inputs.
45. Stale profiles phải detect.
46. Sanitizer config là input.
47. Debug/optimization config là input.
48. Feature resolution là input.
49. Target matrix được hỗ trợ.
50. Independent nodes chạy parallel.
51. Scheduling không thay semantics.
52. Failure propagation deterministic.
53. Cancellation được hỗ trợ.
54. Partial immutable results có thể giữ.
55. Final outputs atomic.
56. Temporary outputs không được coi là final.
57. Remote execution optional.
58. Worker phải match target/toolchain/SDK.
59. Worker identity được kiểm soát.
60. Remote execution reproducible.
61. Secrets không được cache.
62. Cache poisoning phải được ngăn.
63. Build provenance được giữ.
64. Build explanation được hỗ trợ.
65. Rebuild reasons machine-readable.
66. AI build queries được hỗ trợ.
67. Build graph visualization được hỗ trợ.
68. Critical path có thể đo.
69. Resource scheduling có giới hạn.
70. Cache eviction không ảnh hưởng correctness.
71. Offline mode được hỗ trợ.
72. Air-gapped build được hỗ trợ.
73. Repeated builds deterministic.
74. Current timestamps không embed mặc định.
75. Host absolute paths không leak trong reproducibility mode.
76. Incremental build phải equivalent clean build.
77. False cache hit là correctness failure.
78. Persistent graph được version.
79. Crash recovery không làm sai subsequent build.
80. Private artifacts không leak public cache.
81. Build logs structured.
82. Build profiling được hỗ trợ.
83. Build performance được đo.
84. Cache/scheduler/I/O overhead được phân biệt.
85. Build graph API được expose.
86. Remote execution không phải requirement.
87. Remote cache không phải requirement.
88. External build tools phải explicit.
89. Compiler independence vẫn được giữ.
90. **Axiom build engine phải đạt mục tiêu “incremental khi có thể, clean-build equivalent khi cần, deterministic khi inputs giống nhau”, trong đó cache và remote execution chỉ là optimization của build process chứ không bao giờ trở thành nguồn correctness.**

**BOOTSTRAP-487 hoàn tất / LOCKED.**

---

# BOOTSTRAP-488 — SELF-HOSTING COMPILER, STAGED BOOTSTRAP, TRUST ROOT, STAGE0/STAGE1/STAGE2 & COMPILER SELF-VERIFICATION

488 khóa một trong những mục tiêu quan trọng nhất của Axiom:

> **Axiom cuối cùng phải có khả năng tự build compiler của chính nó mà không cần LLVM/GCC/Clang/MSVC làm compiler backend.**

Kiến trúc:

```text id="u4n8p2"
                 Bootstrap Seed
                      │
                      ↓
                  Stage 0
                trusted seed
                      │
                      ↓
              compile Axiom compiler
                      │
                      ↓
                  Stage 1
               native Axiomc
                      │
                      ↓
              compile Axiom compiler
                      │
                      ↓
                  Stage 2
                      │
             ┌────────┴────────┐
             ↓                 ↓
        compare/prove       test/verify
             │                 │
             └────────┬────────┘
                      ↓
               Self-hosted Axiom
```

---

## 488.1 — Bootstrap compiler

Stage0 là compiler seed đủ nhỏ để tạo Stage1.

---

## 488.2 — Stage0 không phải final compiler

Stage0 có thể:

- ít optimization;
- ít target;
- subset language;
- tooling tối thiểu.

---

## 488.3 — Stage1

Stage1 là compiler được viết chủ yếu bằng Axiom và compile bằng Stage0.

---

## 488.4 — Stage2

Stage2 được Stage1 compile từ cùng compiler source.

---

## 488.5 — Bootstrap convergence

Mục tiêu:

```text id="r7m2x9"
Stage1(compiler source)
≈
Stage2(compiler source)
```

về semantic/compiler behavior theo validation rules.

---

## 488.6 — Trust root

Trust root phải được xác định rõ:

```text id="f3q8k1"
bootstrap source
+
seed compiler binary
+
build environment
```

---

## 488.7 — Trust root nhỏ

Stage0 nên nhỏ và audit được.

---

## 488.8 — Stage0 implementation language

Stage0 có thể được viết bằng:

- một subset Axiom;
- hoặc temporary implementation language/tool.

Nhưng final self-hosted chain phải loại bỏ dependency compiler ngoài.

---

## 488.9 — No permanent LLVM dependency

LLVM không được là requirement của final Axiom compiler.

---

## 488.10 — No permanent GCC dependency

GCC không được là requirement của final compiler.

---

## 488.11 — No permanent Clang dependency

Clang không được là requirement của final compiler.

---

## 488.12 — Bootstrap transition

Bootstrap phases:

```text id="m5w9c3"
external seed
   ↓
Axiom Stage0
   ↓
Axiom Stage1
   ↓
Axiom Stage2
   ↓
self-hosting
```

---

## 488.13 — Stage0 target

Stage0 chỉ cần target bootstrap chính, ví dụ:

```text id="x2k6p8"
x86_64 + Windows
```

hoặc target được project chọn.

---

## 488.14 — Native backend bootstrap

Stage0 phải có đủ backend/object/linker functionality để build Stage1.

---

## 488.15 — Bootstrap order

Recommended implementation dependency:

```text id="j8v4n1"
lexer
→ parser
→ AST
→ symbols
→ types
→ HIR
→ MIR
→ basic optimizer
→ target backend
→ object writer
→ linker
→ executable
```

---

## 488.16 — Bootstrap compiler subset

Stage0 có thể omit:

- advanced optimization;
- LSP;
- distributed build;
- profiler;
- GUI;
- advanced diagnostics.

---

## 488.17 — Semantic bootstrap subset

Stage0 vẫn phải implement semantics cần thiết để compile Stage1 correctly.

---

## 488.18 — Self-hosting source

Compiler source tree phải có thể build chính compiler.

---

## 488.19 — Compiler package structure

Concept:

```text id="q6m2x8"
compiler/
  frontend/
  semantic/
  hir/
  mir/
  optimizer/
  codegen/
  object/
  linker/
  driver/
  runtime/
  tools/
```

---

## 488.20 — Compiler dependencies

Final compiler phải ưu tiên Axiom standard/core libraries.

---

## 488.21 — Compiler bootstrap dependencies

Stage0 dependency set phải minimal và frozen.

---

## 488.22 — Bootstrap manifest

Bootstrap configuration:

```text id="n4r7p2"
BootstrapManifest {
    stage
    compiler
    source
    target
    dependencies
    expected_artifacts
    verification
}
```

---

## 488.23 — Stage identity

Artifact phải identify:

```text id="w8m3c5"
stage0
stage1
stage2
```

---

## 488.24 — Reproducible bootstrap

Bootstrap build phải reproducible.

---

## 488.25 — Bootstrap timestamp

Compiler binary không được embed uncontrolled build timestamp.

---

## 488.26 — Bootstrap path

Host paths phải canonicalize để tránh accidental differences.

---

## 488.27 — Stage comparison

Có thể compare:

- binary hash;
- symbol table;
- object sections;
- generated machine code;
- semantic metadata;
- compiler test results.

---

## 488.28 — Binary equality

Binary equality là useful evidence nhưng không phải universal correctness proof.

---

## 488.29 — Semantic equivalence

Stage1/Stage2 có thể được kiểm tra bằng test/conformance suite.

---

## 488.30 — Compiler test suite

435 suite phải compile/run dưới từng bootstrap stage.

---

## 488.31 — Golden tests

Stage outputs có thể có golden references.

---

## 488.32 — Differential bootstrap testing

Có thể chạy:

```text id="k1q7v4"
Stage0 compile source
Stage1 compile source
```

và compare results.

---

## 488.33 — Miscompilation detection

Nếu Stage1 và Stage2 khác behavior:

```text id="s5x2n8"
investigate
```

không tự động chọn một stage là đúng.

---

## 488.34 — Compiler self-test

Compiler binary khi build có thể chạy:

```text id="v8p4m2"
lexer tests
parser tests
type tests
IR tests
backend tests
linker tests
```

---

## 488.35 — Bootstrap smoke test

Minimal:

```text id="g2n9x5"
fn main() -> i32 {
    42
}
```

phải compile/link/run.

---

## 488.36 — Compiler-on-compiler

Stage1 phải compile Stage1 source.

---

## 488.37 — Fixed point

Khái niệm:

```text id="m7r3c8"
C1 = compile(S, C0)
C2 = compile(S, C1)
```

Kiểm tra C1/C2 đạt convergence criteria.

---

## 488.38 — Multi-stage bootstrap

Có thể tiếp tục:

```text id="j5p8w1"
C3 = compile(S, C2)
```

để xác nhận stability.

---

## 488.39 — Bootstrap reproducibility matrix

Test:

```text id="x8q2k6"
Stage
Host
Target
Optimization
Profile
```

---

## 488.40 — Cross-bootstrap

Compiler có thể bootstrap compiler cho target khác nếu host compiler hỗ trợ target.

---

## 488.41 — Canadian cross

Có thể có:

```text id="r4m8z1"
Host A
Build compiler for B
Compiler B builds compiler for C
```

---

## 488.42 — Bootstrap artifact chain

Provenance:

```text id="p7n3c9"
Stage2
 ↓
Stage1
 ↓
Stage0
 ↓
bootstrap seed
```

---

## 488.43 — Seed provenance

Seed compiler phải có:

- source provenance nếu available;
- version;
- hash;
- build environment;
- trust declaration.

---

## 488.44 — Binary transparency

Bootstrap artifacts có thể publish hashes/manifests để independent parties verify.

---

## 488.45 — Independent rebuild

Một bên khác có thể rebuild Stage1/Stage2 từ source và compare.

---

## 488.46 — Diverse bootstrap

Có thể sử dụng nhiều independent seed implementations để giảm correlated compiler trust risk.

---

## 488.47 — Diverse double compilation

Diverse bootstrap có thể phát hiện compiler backdoor/miscompilation classes.

Không coi đây là absolute proof.

---

## 488.48 — Trust statement

Bootstrap artifact phải nói rõ:

```text id="c4w9m2"
what is trusted
what was verified
what was not verified
```

---

## 488.49 — Compiler self-modification

Compiler không được tự sửa source/compiler binary trong build.

---

## 488.50 — Build isolation

Compiler build process không được phụ thuộc hidden external state.

---

## 488.51 — Bootstrap network

Bootstrap phải có thể chạy offline.

---

## 488.52 — Bootstrap dependencies

Bootstrap dependencies phải vendored/frozen.

---

## 488.53 — Dependency compiler ban

Final self-hosting build không được invoke arbitrary external compiler.

---

## 488.54 — External assembler

Final compiler không nên require external assembler nếu Axiom machine encoder đã hỗ trợ target.

---

## 488.55 — External linker

Final compiler không nên require external linker cho Axiom-controlled native targets.

---

## 488.56 — Object reader

Bootstrap compiler phải có object writer/reader cần thiết để test/link.

---

## 488.57 — Self-hosted linker

Axiom linker phải có khả năng build chính compiler.

---

## 488.58 — Self-hosted standard library

Core compiler dependencies phải có thể compile bằng Axiom.

---

## 488.59 — Self-hosted tests

Test runner đủ để validate compiler mà không phụ thuộc external language runtime.

---

## 488.60 — Compiler runtime

Compiler application có thể sử dụng std runtime nhưng target compiler executable không được nhầm với target application runtime.

---

## 488.61 — Stage0 simplification

Stage0 có thể có runtime/tooling đơn giản hơn final compiler.

---

## 488.62 — Optimization bootstrap

Stage0 có thể build Stage1 bằng `-O0` hoặc optimization subset.

---

## 488.63 — Optimization maturation

Stage1/Stage2 sau đó build optimized compiler.

---

## 488.64 — Bootstrap compiler performance

Bootstrap correctness ưu tiên trước performance.

---

## 488.65 — Final compiler performance

Sau self-hosting, compiler phải đạt performance targets 450.

---

## 488.66 — Self-hosting benchmark

Track:

```text id="y2m8q4"
clean compiler build
incremental compiler build
compiler startup
compile throughput
memory
binary size
```

---

## 488.67 — Compiler binary size

Compiler có thể lớn hơn runtime applications; mục tiêu “compact native output” áp dụng application artifact, không ép compiler nhỏ bất hợp lý.

---

## 488.68 — Bootstrap debugging

Stage compiler phải có debug artifacts để điều tra miscompilation.

---

## 488.69 — Miscompilation minimization

Compiler có tool để reduce failing source:

```text id="f1k6n8"
full program
→ minimal reproducer
```

---

## 488.70 — Compiler crash

Compiler crash phải tạo machine-readable diagnostic/crash artifact.

---

## 488.71 — Compiler determinism

Cùng input phải produce equivalent compiler behavior.

---

## 488.72 — Parallel compiler determinism

Parallel query evaluation không được thay semantic output.

---

## 488.73 — Hash stability

Semantic hashes phải stable theo defined schema/version.

---

## 488.74 — Bootstrap cache

487 cache có thể được dùng trong bootstrap nhưng clean bootstrap phải có thể thực hiện.

---

## 488.75 — Cache independence

Bootstrap correctness không được phụ thuộc cache hit.

---

## 488.76 — Stage isolation

Stage1 không được implicitly execute Stage0 code ngoại trừ explicit build process.

---

## 488.77 — Compiler provenance

Every compiler-generated artifact phải có compiler identity.

---

## 488.78 — Security audit surface

Stage0 nên giữ dependency count và code surface thấp để dễ audit.

---

## 488.79 — Formal verification boundary

Một số compiler components có thể được formal verify sau này.

Không yêu cầu toàn bộ compiler formal verification để self-host.

---

## 488.80 — Verified components

Có thể ưu tiên verify:

```text id="p8m4x1"
lexer
parser
type checker
ownership
IR verifier
machine encoder
linker
```

---

## 488.81 — IR verifier

IR verifier là trust-critical component.

Nó phải kiểm tra structural invariants trước optimization/codegen.

---

## 488.82 — Machine encoder verifier

Machine encoder phải có validation/golden tests theo ISA.

---

## 488.83 — Object verifier

Object writer/reader phải validate:

- section;
- symbol;
- relocation;
- alignment;
- architecture.

---

## 488.84 — Linker verifier

Linker phải validate:

- symbols;
- relocations;
- section ranges;
- entry;
- permissions;
- target constraints.

---

## 488.85 — Bootstrap target expansion

Sau target bootstrap đầu tiên:

```text id="t5n9q3"
x86-64
→ AArch64
→ WASM
→ additional native targets
```

---

## 488.86 — Self-hosting target matrix

Self-hosting compiler không cần bootstrap simultaneously trên mọi target.

---

## 488.87 — Target-independent frontend

Frontend/semantic compiler code nên được shared across targets.

---

## 488.88 — Target-specific backend

Codegen/object/linker target-specific modules remain isolated.

---

## 488.89 — Bootstrap architecture

```text id="a6w3p7"
Axiom Compiler
├── Frontend        [target-independent]
├── Semantic        [target-independent]
├── MIR             [mostly target-independent]
├── Optimizer       [mostly target-independent]
├── Backend
│   ├── x86_64
│   ├── AArch64
│   └── WASM
├── Object
├── Linker
└── Driver
```

---

## 488.90 — Self-hosted compiler can build tools

Sau bootstrap, compiler có thể tự build:

- formatter;
- LSP;
- documentation;
- package manager;
- test runner;
- debugger tools;
- profiler tools.

---

## 488.91 — Bootstrap completion criterion

Axiom được coi là self-hosting khi:

```text id="r8m1k5"
Axiom compiler source
    ↓
Axiom compiler
    ↓
Axiom compiler source
```

có thể build hoàn toàn bằng Axiom toolchain, không cần external compiler.

---

## 488.92 — Full bootstrap criterion

Final criterion:

```text id="u7q4n2"
clean source
+
pinned dependencies
+
bootstrap seed
+
target SDK
```

→ native Axiom compiler

→ native Axiom compiler rebuilds itself.

---

## 488.93 — Bootstrap independence

LLVM/GCC/Clang/MSVC có thể được dùng để tạo seed trong giai đoạn lịch sử bootstrap, nhưng không nằm trong final dependency graph.

---

## 488.94 — Seed replacement

Seed có thể được thay thế bằng Stage2 trong future release.

---

## 488.95 — Bootstrap ceremony

Mỗi release compiler có thể thực hiện:

```text id="m3x8p1"
seed
→ stage1
→ stage2
→ verify
→ publish
```

---

## 488.96 — Release verification

Release phải lưu:

```text id="q5n7c2"
source hash
toolchain hash
stage hashes
target
SDK
test result
verification result
```

---

## 488.97 — Reproducible release

Release build có thể được independently reproduced.

---

## 488.98 — Bootstrap audit log

Build system có thể xuất machine-readable audit trail.

---

## 488.99 — AI bootstrap query

AI API:

```text id="z4p8m2"
bootstrap_status()
stage_dependencies()
stage_diff()
trust_root()
verification_results()
self_hosting_targets()
```

---

## 488.100 — No false certainty

Tooling phải phân biệt:

```text id="w6r2k9"
tested
reproduced
hash-matched
formally-verified
not-verified
```

---

## 488.101 — Bootstrap failure

Nếu stage verification fail:

```text id="c9m4x7"
release/build marked failed
```

không silently continue.

---

## 488.102 — Bootstrap quarantine

Failed compiler artifacts không được đưa vào trusted release channel.

---

## 488.103 — Compiler update

484 versioning + 487 reproducibility + 488 bootstrap verification phối hợp khi phát hành compiler mới.

---

## 488.104 — Supply-chain integration

447 provenance/signatures + 483 toolchain identity + 488 bootstrap chain.

---

## 488.105 — Hard invariants

1. Axiom phải có bootstrap compiler.
2. Stage0 là trust seed.
3. Stage0 không nhất thiết là final compiler.
4. Stage1 được build bằng Stage0.
5. Stage2 được build bằng Stage1.
6. Bootstrap convergence được kiểm tra.
7. Trust root phải explicit.
8. Stage0 nên nhỏ/audit được.
9. Bootstrap seed phải có identity.
10. Final compiler không phụ thuộc LLVM.
11. Final compiler không phụ thuộc GCC.
12. Final compiler không phụ thuộc Clang.
13. Final compiler không phụ thuộc MSVC compiler.
14. Bootstrap transition được xác định.
15. Stage0 có thể chỉ hỗ trợ bootstrap target.
16. Stage0 có native backend đủ để build Stage1.
17. Bootstrap dependency order được kiểm soát.
18. Stage0 semantics phải đủ để compile Stage1.
19. Compiler source có self-build path.
20. Bootstrap manifest được hỗ trợ.
21. Stage identity được ghi.
22. Bootstrap reproducibility được yêu cầu.
23. Build timestamp không uncontrolled.
24. Host paths được canonicalize.
25. Stage outputs có provenance.
26. Binary comparison được hỗ trợ.
27. Binary equality không được coi là proof duy nhất.
28. Semantic/test comparison được hỗ trợ.
29. Compiler conformance suite chạy trên stages.
30. Golden tests được hỗ trợ.
31. Differential bootstrap được hỗ trợ.
32. Miscompilation phải được điều tra.
33. Compiler self-test được hỗ trợ.
34. Minimal bootstrap smoke test được hỗ trợ.
35. Compiler-on-compiler được hỗ trợ.
36. Fixed-point testing được hỗ trợ.
37. Multi-stage bootstrap được hỗ trợ.
38. Bootstrap matrix được hỗ trợ.
39. Cross bootstrap được hỗ trợ.
40. Canadian cross có thể được hỗ trợ.
41. Bootstrap provenance giữ toàn bộ chain.
42. Binary transparency được hỗ trợ.
43. Independent rebuild được hỗ trợ.
44. Diverse bootstrap có thể được hỗ trợ.
45. Trust statements phải nêu rõ verification scope.
46. Compiler không tự sửa source/binary.
47. Bootstrap build có thể offline.
48. Bootstrap dependencies phải frozen/vendored.
49. Final build không invoke arbitrary external compiler.
50. External assembler không mandatory.
51. External linker không mandatory cho Axiom-controlled targets.
52. Axiom object writer/reader phải self-hostable.
53. Axiom linker phải self-hostable.
54. Standard library cần thiết cho compiler phải self-hostable.
55. Test runner cần thiết cho bootstrap phải self-hostable.
56. Stage0 có thể dùng simpler runtime.
57. Stage0 optimization có thể hạn chế.
58. Stage1/Stage2 có thể mature optimization.
59. Bootstrap correctness được ưu tiên trước performance.
60. Final compiler performance được benchmark.
61. Compiler build performance được đo.
62. Compiler binary size được đo nhưng không áp đặt application-size criterion.
63. Bootstrap compiler có debug capability.
64. Miscompilation reducer được hỗ trợ.
65. Compiler crashes có structured artifacts.
66. Parallel compilation deterministic.
67. Semantic hash stability được version.
68. Bootstrap cache không phải correctness dependency.
69. Stage isolation được giữ.
70. Generated artifacts có compiler provenance.
71. Stage0 attack surface nên nhỏ.
72. Formal verification là optional enhancement.
73. IR verifier là trust-critical.
74. Machine encoder có validation.
75. Object format có validation.
76. Linker có validation.
77. Backend target expansion độc lập với bootstrap completion.
78. Frontend được target-independent tối đa.
79. Backend được target-isolated.
80. Self-hosted compiler có thể build compiler tools.
81. Self-hosting criterion được định nghĩa rõ.
82. Full bootstrap criterion được định nghĩa rõ.
83. Historical external compiler có thể tồn tại ở seed stage.
84. Final dependency graph loại bỏ external compiler.
85. Seed replacement được hỗ trợ.
86. Release bootstrap ceremony được định nghĩa.
87. Release verification artifacts được lưu.
88. Independent reproduction được hỗ trợ.
89. Bootstrap audit trail được hỗ trợ.
90. AI bootstrap queries được hỗ trợ.
91. Evidence states được phân biệt.
92. Verification failure không được silently ignore.
93. Failed artifacts bị quarantine.
94. Compiler versioning tích hợp 484.
95. Build reproducibility tích hợp 487.
96. Package provenance tích hợp 447.
97. Toolchain identity tích hợp 483.
98. Security trust model tích hợp 445.
99. Self-hosting không yêu cầu GC/borrow checker/LLVM.
100. **Axiom chỉ được coi là thực sự self-hosting khi compiler của Axiom có thể được build lại từ source bằng chính Axiom toolchain, tạo native compiler artifacts trực tiếp, và quá trình bootstrap có provenance + verification đủ để phân biệt rõ trust root, evidence và phần chưa được chứng minh.**

**BOOTSTRAP-488 hoàn tất / LOCKED.**

---

# TIẾN ĐỘ CHUỖI

```text
479  Contracts / Design-by-Contract              LOCKED
480  Runtime Validation / Sanitizers              LOCKED
481  Profiling / Tracing                          LOCKED
482  Self-hosting / Bootstrap Trust               LOCKED
483  Toolchain / Cross Compilation                LOCKED
484  Language Evolution / Editions               LOCKED
485  Documentation / Knowledge Graph              LOCKED
486  Semantic Refactoring / Change Impact         LOCKED
487  Build Graph 2.0 / Hermetic / Remote Cache    LOCKED
488  Self-hosting Compiler / Staged Bootstrap     LOCKED
```

**Task kế tiếp: `BOOTSTRAP-489 — DISTRIBUTION OF NATIVE APPLICATIONS, INSTALLER, DEPLOYMENT, UPDATE, SIGNING, CODE SIGNING & APPLICATION LIFECYCLE`.**