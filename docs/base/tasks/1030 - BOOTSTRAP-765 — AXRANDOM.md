# BOOTSTRAP-765 — AXRANDOM

**Title:** Native Randomness, Pseudorandom Generators, Entropy Sources, Secure Randomness, Seeds & Deterministic Random Runtime 5.0  
**Namespace:** `AXRANDOM`  
**Phase:** Axiom Civilization Runtime / Native Randomness Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXRANDOM` cung cấp một abstraction thống nhất cho mọi nhu cầu randomness của Axiom:

```text
Randomness
├── hardware/system entropy
├── cryptographically secure random
├── general-purpose PRNG
├── deterministic PRNG
├── reproducible simulation
├── random distributions
└── random sampling
```

Điểm quan trọng:

```text
PRNG ≠ CSPRNG ≠ entropy source
```

Không được để API đơn giản khiến programmer vô tình sử dụng nguồn randomness không phù hợp cho security.

---

# 2. Boundary

`AXRANDOM` sở hữu:

- random source abstraction;
- entropy acquisition;
- PRNG;
- CSPRNG interface;
- deterministic RNG;
- seed/state;
- random distributions;
- bounded integer generation;
- floating random generation;
- sampling;
- shuffle;
- reproducibility;
- random stream splitting;
- random-state serialization;
- randomness diagnostics.

`AXCRYPTO` sở hữu:

- cryptographic algorithms;
- key derivation;
- cryptographic protocols;
- signatures;
- encryption.

`AXSECURITY` sở hữu:

- authorization;
- capability;
- security policy;
- enforcement.

`AXRANDOM` không trở thành một cryptography library.

---

# 3. Kiến trúc tổng thể

```text
                     AXRANDOM
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Entropy          PRNG          CSPRNG
       Sources           │              │
          │              │              │
          ▼              ▼              ▼
     Seed Material   General RNG    Secure RNG
          │              │              │
          └──────┬───────┴───────┬──────┘
                 ▼               ▼
             Distributions   Sampling
                 │               │
                 └───────┬───────┘
                         ▼
                 Application / Runtime
```

---

# 4. Random source types

Baseline:

```text
ENTROPY
SYSTEM_RANDOM
SECURE_RANDOM
PSEUDORANDOM
DETERMINISTIC
HARDWARE_RANDOM
VIRTUAL_RANDOM
```

Mỗi source có capability metadata.

---

# 5. Entropy

Entropy source cung cấp unpredictable material.

Ví dụ:

```text
OS random facility
hardware RNG
trusted platform source
```

Entropy không phải một PRNG.

---

# 6. Entropy quality

Source metadata:

```text
entropy_source {
    source_id
    kind
    estimated_quality
    blocking
    health
    platform
}
```

Không được tuyên bố "true randomness" chỉ vì dữ liệu đến từ hardware.

---

# 7. OS entropy

Default secure random source nên ưu tiên operating-system CSPRNG facilities.

Platform backend:

```text
Windows → system RNG
Linux   → kernel RNG
Apple   → system security RNG
WASM    → host-provided secure source
```

---

# 8. Hardware RNG

Hardware RNG có thể được dùng:

```text
hardware
    ↓
health/availability
    ↓
entropy pool
```

Không mặc định expose hardware RNG trực tiếp cho application.

---

# 9. Entropy pool

Runtime có thể maintain internal seed material:

```text
entropy sources
       ↓
  conditioning
       ↓
 internal seed state
       ↓
     CSPRNG
```

Pool implementation phải tránh làm entropy source thành global bottleneck.

---

# 10. CSPRNG

CSPRNG là generator có security-oriented semantics.

Properties:

- unpredictable without state;
- forward/backtracking resistance theo implementation;
- reseeding;
- bounded output;
- explicit failure.

Axiom không tự định nghĩa cryptographic algorithm mới.

---

# 11. CSPRNG implementation boundary

Implementation có thể dựa trên primitive đã được chuẩn hóa trong `AXCRYPTO`.

Ví dụ abstraction:

```text
secure_random_bytes()
```

không expose algorithm-specific details tới ordinary application code.

---

# 12. Secure random API

```text
secure_random_bytes(buffer)
secure_random_u64()
secure_random_u128()
secure_random_range()
```

---

# 13. Secure failure

Nếu secure source không available:

```text
RANDOM_SECURE_UNAVAILABLE
```

Không fallback silently sang ordinary PRNG.

Đây là invariant quan trọng.

---

# 14. General PRNG

General-purpose PRNG dành cho:

- game;
- procedural generation;
- randomized algorithms;
- simulation;
- fuzzing;
- sampling.

Không được dùng cho cryptographic secrets.

---

# 15. Default PRNG

Axiom nên có một default high-quality PRNG.

Yêu cầu:

- fast;
- small state;
- statistically strong;
- reproducible;
- portable.

Implementation có thể thay đổi giữa ABI generations nếu explicitly versioned.

---

# 16. Algorithm identity

RNG state phải xác định algorithm:

```text
rng_state {
    algorithm_id
    algorithm_version
    state
}
```

Không deserialize state vào generator khác mà không phát hiện mismatch.

---

# 17. Deterministic RNG

```text
rng = deterministic(seed)
```

cùng:

```text
algorithm
seed
initial_state
```

phải tạo cùng sequence trên supported deterministic ABI.

---

# 18. Reproducibility

Simulation có thể ghi:

```text
seed
algorithm
algorithm_version
stream_id
```

thay vì lưu toàn bộ random output.

---

# 19. Random state

API:

```text
rng_state_save()
rng_state_restore()
```

cho deterministic generator.

Secure RNG state không được expose tùy tiện.

---

# 20. Secure state protection

CSPRNG internal state:

- không serializable qua ordinary API;
- không log;
- không expose qua diagnostics;
- memory protection tùy platform.

---

# 21. Seed

Seed là initialization material.

```text
seed
 ↓
generator initialization
```

Seed không nhất thiết có cùng semantics với entropy.

---

# 22. Automatic seeding

General RNG có thể:

```text
rng_default()
```

và runtime tự seed từ system entropy.

Nhưng API phải cho phép deterministic construction.

---

# 23. Explicit seed

```text
rng_seed(123456789)
```

cho deterministic testing/simulation.

Không dùng explicit predictable seed cho security-sensitive random values.

---

# 24. Seed domain separation

Các generator độc lập không nên vô tình sử dụng cùng state sequence.

API hỗ trợ:

```text
rng_split()
```

---

# 25. RNG splitting

```text
master
 ├── worker-0
 ├── worker-1
 ├── worker-2
 └── worker-3
```

Mỗi stream có domain/stream identifier.

---

# 26. Parallel randomness

Không dùng một global RNG lock cho toàn application.

Preferred:

```text
thread-local / task-local
        +
stream splitting
        +
independent state
```

---

# 27. Thread safety

Một `Rng` mutable state mặc định không cần thread-safe.

Có abstraction:

```text
SharedRng
```

nếu application thực sự cần shared access.

---

# 28. Task safety

Task-local RNG có thể inherit hoặc split từ parent.

Inheritance policy phải explicit.

---

# 29. Fork/process safety

Sau process duplication:

```text
parent RNG state
       ↓
 child
```

không được tiếp tục cùng sequence nếu generator có security implications.

CSPRNG phải reseed/rekey sau process boundary khi platform semantics yêu cầu.

---

# 30. Random bytes

Primitive:

```text
random_bytes(n)
```

là foundational API.

---

# 31. Integer generation

```text
random_u8()
random_u16()
random_u32()
random_u64()
random_u128()
```

và signed variants.

---

# 32. Unbiased range

Không implement:

```text
random_u64() % n
```

một cách naïve cho arbitrary `n`.

API range phải tránh modulo bias.

---

# 33. Range API

```text
random_range(min, max)
random_below(n)
```

Semantics:

```text
[min, max)
```

được khuyến nghị làm canonical form.

---

# 34. Empty range

```text
random_range(10, 10)
```

phải trả:

```text
RANDOM_EMPTY_RANGE
```

không undefined behavior.

---

# 35. Integer overflow

Range calculation phải xử lý:

```text
MIN_INT
MAX_INT
```

mà không overflow intermediate arithmetic.

---

# 36. Floating random

API:

```text
random_f32()
random_f64()
```

Canonical interval:

```text
[0, 1)
```

---

# 37. Floating precision

Không tuyên bố entropy cao hơn số bit significand của floating-point type.

---

# 38. Distribution abstraction

```text
Distribution<T>
```

Baseline:

```text
Uniform
Bernoulli
Normal
Exponential
Poisson
```

---

# 39. Uniform distribution

```text
uniform(min, max)
```

phải preserve distribution semantics.

---

# 40. Bernoulli

```text
bernoulli(p)
```

với:

```text
0 ≤ p ≤ 1
```

invalid probability phải fail.

---

# 41. Normal distribution

```text
normal(mean, standard_deviation)
```

Không dùng cho security.

---

# 42. Exponential

```text
exponential(lambda)
```

`lambda > 0`.

---

# 43. Poisson

```text
poisson(lambda)
```

với parameter hợp lệ.

---

# 44. Distribution state

Distribution algorithms có thể giữ state/cache.

State phải tách khỏi RNG state.

---

# 45. Sampling

API:

```text
sample(range, count)
sample_without_replacement(collection, count)
```

---

# 46. Shuffle

```text
shuffle(array, rng)
```

phải dùng unbiased permutation algorithm.

Không dùng sort-by-random-key.

---

# 47. Weighted sampling

```text
weighted_sample(items, weights)
```

weights phải validate:

- finite;
- non-negative;
- valid sum.

---

# 48. Reservoir sampling

Cho stream lớn:

```text
reservoir_sample(stream, k)
```

không yêu cầu load toàn bộ dữ liệu vào memory.

---

# 49. Random choice

```text
choice(collection)
```

empty collection:

```text
RANDOM_EMPTY_COLLECTION
```

---

# 50. Secure token boundary

Application cần random token có thể gọi:

```text
secure_random_bytes()
```

Không expose helper có tên gây nhầm:

```text
random_token()
```

mà implementation dùng ordinary PRNG.

Security-sensitive helper phải có `secure_` semantics rõ ràng.

---

# 51. Nonce generation

Cryptographic nonce requirements thuộc AXCRYPTO.

AXRANDOM chỉ cung cấp entropy/random bytes khi AXCRYPTO yêu cầu.

---

# 52. Identifier generation

Random IDs:

```text
random_id()
secure_id()
```

phải phân biệt security requirement.

Identity/capability IDs có thể được cấp bởi AXIDENTITY/AXCAPABILITY thay vì application tự tạo.

---

# 53. Randomness and AXSECURITY

AXSECURITY không phụ thuộc vào ordinary PRNG.

Security-critical random operations phải request:

```text
SECURE_RANDOM
```

capability/source.

---

# 54. Randomness and AXCRYPTO

```text
AXRANDOM
   │
   └── secure random bytes
             ↓
         AXCRYPTO
```

AXRANDOM không tự thực hiện:

- AES;
- ChaCha;
- hashing;
- signatures;
- key exchange.

---

# 55. Randomness and AXIDENTITY

Identity generation có thể consume secure randomness.

Nhưng identity format/namespace thuộc AXIDENTITY.

---

# 56. Randomness and AXNETWORK

Network protocols có thể request:

```text
secure random
```

cho protocol-specific nonce/challenge material.

Protocol semantics thuộc AXNETWORK/AXCRYPTO.

---

# 57. Virtual random

Simulation:

```text
virtual_rng(seed)
```

phải deterministic.

Không được tự đọc system entropy.

---

# 58. Replay

Replay mode:

```text
recorded RNG state
```

hoặc:

```text
seed + deterministic algorithm
```

để reproducing execution.

---

# 59. Random event trace

Diagnostics có thể record:

```text
algorithm_id
stream_id
seed_hash
state_position
```

nhưng không log secure random output.

---

# 60. Secret leakage prevention

Không được đưa:

```text
secure random bytes
CSPRNG state
private seed material
```

vào:

- AXLOGGING;
- AXOBSERVABILITY;
- AXDIAGNOSTICS;
- AXAUDIT.

---

# 61. Seed logging

Deterministic test seed có thể log:

```text
seed = 12345
```

Secure seed material thì không.

---

# 62. Entropy source diagnostics

Có thể expose:

```text
entropy_source_info()
```

bao gồm:

```text
available
health
blocking
source_id
```

Không expose internal secret state.

---

# 63. Entropy failure

General RNG auto-seeding:

```text
system entropy unavailable
```

phải có defined fallback policy.

Security RNG thì **không** fallback sang predictable source.

---

# 64. Entropy blocking

Source có thể:

```text
BLOCKING
NON_BLOCKING
```

API expose behavior.

Application có thể chọn:

```text
secure_random_bytes()
try_secure_random_bytes()
```

---

# 65. Secure readiness

Runtime startup có thể query:

```text
secure_random_ready()
```

để security-sensitive service fail early nếu source chưa available.

---

# 66. Hardware source health

Hardware entropy source phải được coi là untrusted input cho conditioning layer.

Không trực tiếp tin tưởng mọi hardware random bit.

---

# 67. Conditioning

Nếu runtime aggregate multiple entropy sources:

```text
source A ─┐
source B ─┼→ conditioner → secure generator
source C ─┘
```

conditioning algorithm thuộc cryptographic primitive layer.

---

# 68. Randomness quality

Statistical test pass không chứng minh cryptographic security.

AXRANDOM phải phân biệt:

```text
STATISTICAL_QUALITY
```

và:

```text
CRYPTOGRAPHIC_SECURITY
```

---

# 69. Statistical testing

Development/test builds có thể cung cấp:

```text
rng_test_distribution()
rng_test_uniformity()
```

Không chạy expensive statistical testing trên production hot path.

---

# 70. Benchmark

AXRANDOM benchmark API có thể đo:

```text
bytes/sec
calls/sec
latency
allocation
contention
```

Không dùng benchmark result để tuyên bố cryptographic strength.

---

# 71. Compiler literals

Axiom có thể hỗ trợ:

```text
seed(1234)
```

nhưng không có magic syntax tạo security secret.

---

# 72. Type system

Nên phân biệt:

```text
Random
SecureRandom
DeterministicRandom
```

ở type/API level.

Mục tiêu là làm misuse khó xảy ra.

---

# 73. API conversion

Không cho implicit:

```text
SecureRandom → Random
```

nếu conversion làm mất security semantics.

Một secure RNG có thể được sử dụng ở API cần ordinary randomness, nhưng ngược lại không.

---

# 74. Secure random wrapper

```text
SecureRng
    ↓
random_u64()
random_bytes()
random_range()
```

Mọi output vẫn giữ security provenance ở API level.

---

# 75. Capability metadata

RNG descriptor:

```text
rng_info {
    kind
    algorithm
    secure
    deterministic
    thread_safe
    reproducible
}
```

---

# 76. State ownership

RNG state phải có clear ownership.

```text
Rng
 └── owned mutable state
```

Không có implicit global mutable RNG state bắt buộc.

---

# 77. Global convenience API

Có thể cung cấp:

```text
random()
secure_random()
```

nhưng implementation phải map tới explicit runtime instances.

Global convenience không được biến state thành hidden shared mutable bottleneck.

---

# 78. Per-core RNG

General PRNG có thể sử dụng:

```text
per-core state
```

để giảm contention.

---

# 79. NUMA

NUMA systems:

```text
node-local RNG state
```

có thể được sử dụng.

Không yêu cầu cross-NUMA synchronization cho ordinary PRNG.

---

# 80. Zero allocation

Hot APIs:

```text
random_u64()
random_range()
random_f64()
random_bytes(existing_buffer)
```

phải zero-allocation.

---

# 81. Bulk generation

API:

```text
random_fill(buffer)
```

để vectorize/batch generation.

Compiler/runtime có thể sử dụng SIMD.

---

# 82. SIMD

PRNG implementation có thể vectorize:

```text
scalar
SIMD
batch
```

mà vẫn giữ deterministic stream semantics khi algorithm contract yêu cầu.

---

# 83. Determinism across CPU

Nếu deterministic ABI yêu cầu reproducibility:

```text
same seed
same algorithm version
same sequence
```

không phụ thuộc CPU SIMD width.

Implementation optimized có thể internally vectorize nhưng output phải giữ contract.

---

# 84. Cross-platform determinism

Axiom test/runtime có thể yêu cầu:

```text
AXRANDOM_DETERMINISTIC_ABI_1
```

để guarantee sequence compatibility giữa supported platforms.

---

# 85. Versioning

Algorithm upgrade không được âm thầm thay đổi deterministic sequence.

Ví dụ:

```text
PRNG_X@1
PRNG_X@2
```

là các deterministic algorithms khác nhau về compatibility.

---

# 86. Serialization

Deterministic state:

```text
serialize_rng_state()
```

phải chứa:

```text
algorithm_id
version
state
stream metadata
```

---

# 87. Corrupted state

Invalid state:

```text
RANDOM_INVALID_STATE
```

Không được tiếp tục bằng state partially parsed.

---

# 88. Randomness replay

Replay subsystem có thể:

```text
seed
 ↓
algorithm version
 ↓
stream tree
 ↓
deterministic execution
```

để debug.

---

# 89. Fuzzing

AXRANDOM cung cấp deterministic random stream cho fuzzers.

Ví dụ:

```text
seed
case_index
mutation_stream
```

cho reproducible failures.

---

# 90. AI integration

AI tooling có thể:

- phát hiện modulo bias;
- phát hiện ordinary RNG dùng cho security;
- generate deterministic test seeds;
- analyze random distribution;
- detect shared RNG contention;
- suggest secure API.

AI không được tự nâng ordinary RNG thành secure RNG.

---

# 91. Diagnostics integration

AXDIAGNOSTICS có thể report:

```text
RNG algorithm
stream count
reseed count
entropy source health
contention
generation throughput
```

Không expose secret state.

---

# 92. Observability integration

AXOBSERVABILITY có thể expose:

```text
random_bytes_generated
secure_random_requests
entropy_failures
reseed_count
rng_contention
```

Không expose random output.

---

# 93. Logging integration

AXLOGGING có thể ghi:

```text
RNG initialization failure
entropy source unavailable
algorithm mismatch
```

Không ghi seed secrets.

---

# 94. Audit integration

AXAUDIT có thể record:

```text
administrative RNG configuration change
security RNG source policy change
```

Không audit từng random byte.

---

# 95. Configuration

AXCONFIG có thể điều chỉnh:

```text
default_prng
secure_rng_policy
reseed_interval
entropy_source_policy
deterministic_mode
```

Security policy vẫn thuộc AXSECURITY.

---

# 96. Native API — entropy

```text
entropy_sources()
entropy_source_info()
entropy_available()
entropy_read()
entropy_health()
```

---

# 97. Native API — general RNG

```text
rng_create()
rng_seed()
rng_next_u64()
rng_next_u128()
rng_next_f64()
rng_bytes()
rng_range()
rng_split()
rng_state_save()
rng_state_restore()
rng_destroy()
```

---

# 98. Native API — secure RNG

```text
secure_rng_create()
secure_random_bytes()
secure_random_u64()
secure_random_range()
secure_rng_reseed()
secure_rng_status()
```

---

# 99. Native API — distributions

```text
uniform()
bernoulli()
normal()
exponential()
poisson()
weighted_sample()
shuffle()
choice()
reservoir_sample()
```

---

# 100. Native API — deterministic

```text
deterministic_rng()
rng_algorithm_id()
rng_algorithm_version()
rng_stream_id()
```

---

# 101. Native ABI

```text
AXRANDOM_ABI_1
```

Canonical types:

```text
Rng
SecureRng
DeterministicRng
Seed
RngState
Distribution<T>
RandomRange
EntropySource
RngInfo
```

---

# 102. Error model

```text
RANDOM_INVALID
RANDOM_EMPTY_RANGE
RANDOM_EMPTY_COLLECTION
RANDOM_INVALID_PROBABILITY
RANDOM_INVALID_DISTRIBUTION
RANDOM_OVERFLOW
RANDOM_STATE_INVALID
RANDOM_ALGORITHM_UNKNOWN
RANDOM_ALGORITHM_VERSION
RANDOM_ENTROPY_UNAVAILABLE
RANDOM_ENTROPY_FAILED
RANDOM_SECURE_UNAVAILABLE
RANDOM_SECURE_RESEED_FAILED
RANDOM_SOURCE_UNAVAILABLE
RANDOM_SOURCE_UNHEALTHY
RANDOM_BUFFER_INVALID
RANDOM_DETERMINISM_VIOLATION
RANDOM_PERMISSION_DENIED
```

---

# 103. Security rule — fallback

Critical invariant:

```text
secure_random()
      ↓
failure
      ↓
ERROR
```

Never:

```text
secure_random()
      ↓
failure
      ↓
ordinary_prng()
```

silently.

---

# 104. Security rule — API naming

Axiom ưu tiên naming rõ:

```text
random_*
secure_random_*
deterministic_random_*
```

thay vì một API `random()` làm mọi thứ.

---

# 105. Security rule — secrets

Secure random output phải được coi là potentially sensitive.

Default diagnostics:

```text
REDACT
```

---

# 106. Security rule — seed

Deterministic seed có thể public.

Secure RNG seed material không.

---

# 107. Performance architecture

```text
Application
    │
    ▼
thread-local RNG
    │
    ├── scalar
    └── SIMD/bulk
```

Không:

```text
Application
    ↓
global mutex
    ↓
random generator
```

trên ordinary hot path.

---

# 108. Secure performance

Secure RNG có thể batch output:

```text
OS entropy
    ↓
internal secure generator
    ↓
buffer
    ↓
many requests
```

giảm syscall overhead.

---

# 109. Reseeding

CSPRNG có thể reseed:

- theo byte budget;
- thời gian;
- fork/process boundary;
- explicit administrative event;
- source health event.

Exact threshold là implementation/security profile parameter.

---

# 110. Reseeding không phá API semantics

Application không cần biết internal reseed state để sử dụng secure RNG.

Deterministic RNG không tự reseed từ external entropy.

---

# 111. Random stream lifetime

Short-lived RNG:

```text
create
use
destroy
```

Long-lived service:

```text
persistent generator
```

có thể tối ưu.

---

# 112. Resource limits

AXRANDOM phải hỗ trợ limits:

```text
max_rng_instances
max_state_memory
max_entropy_request
max_secure_batch
```

để tránh resource exhaustion.

---

# 113. Multi-tenant isolation

RNG instances thuộc process/security domain không được vô tình chia sẻ state cross-domain.

AXSECURITY enforce isolation.

---

# 114. Sandboxed applications

Sandboxed app chỉ được access random facilities mà platform/security profile cho phép.

AXRANDOM không bypass sandbox.

---

# 115. Virtual environment

VM/container randomness có thể phụ thuộc host.

AXRANDOM expose source metadata nhưng không tự coi virtualization là insecure.

---

# 116. Hardware acceleration

Compiler/runtime có thể dùng:

- hardware RNG;
- SIMD;
- platform random APIs;

khi available.

Fallback phải preserve semantic category.

---

# 117. Portable backend

```text
AXRANDOM API
      │
 ┌────┼──────────────┐
 ▼    ▼              ▼
WIN  UNIX          WASM
backend backend    backend
```

Không để application phụ thuộc OS-specific RNG API trong portable code.

---

# 118. Canonical flow — simulation

```text
seed
 ↓
deterministic_rng
 ↓
simulation
 ├── worker 0 → split
 ├── worker 1 → split
 └── worker 2 → split
 ↓
reproducible result
```

---

# 119. Canonical flow — secure secret

```text
application
    ↓
secure_random_bytes()
    ↓
AXRANDOM
    ↓
OS/platform secure source
    ↓
bytes
    ↓
AXCRYPTO
```

---

# 120. Canonical flow — random algorithm

```text
rng
 ↓
random_range(0, n)
 ↓
unbiased bounded integer
 ↓
algorithm
```

---

# 121. Canonical flow — parallel

```text
master_rng
    ↓
split(stream_id)
    ├── task A
    ├── task B
    └── task C
```

---

# 122. Canonical flow — replay

```text
record:
 algorithm
 version
 seed
 stream tree
      ↓
replay:
 deterministic RNG
      ↓
same random sequence
```

---

# 123. Canonical flow — secure failure

```text
secure RNG
   ↓
source unavailable
   ↓
explicit error
   ↓
application decides recovery
```

AXRANDOM không tự hạ security level.

---

# 124. Canonical flow — diagnostics

```text
AXDIAGNOSTICS
      ↓
RNG metadata
      ↓
algorithm/version/source
      ↓
NO secret state
```

---

# 125. Compiler diagnostics

Compiler/static analyzer có thể cảnh báo:

```text
ordinary RNG used in security-sensitive API
```

khi type information cho phép xác định.

---

# 126. Modulo-bias diagnostic

Code pattern:

```text
rng.next_u64() % n
```

có thể được cảnh báo khi `n` không phải power-of-two và context yêu cầu uniformity.

---

# 127. Hidden global state prohibition

Core runtime không được yêu cầu một mutable global PRNG duy nhất.

---

# 128. Deterministic mode

Test runner có thể activate:

```text
AXRANDOM_DETERMINISTIC
```

nhưng secure APIs không được tự chuyển sang deterministic mode.

---

# 129. Production safeguard

Nếu application build profile:

```text
production
```

vẫn sử dụng deterministic RNG ở security-sensitive context, compiler/runtime có thể reject tùy security profile.

---

# 130. Distribution correctness

Distribution implementations phải document:

```text
domain
parameter constraints
precision
tail behavior
determinism
```

---

# 131. Statistical guarantees

AXRANDOM chỉ guarantee distribution contract trong phạm vi precision của implementation.

Không claim mathematical perfection cho floating distributions.

---

# 132. Rejection sampling

Bounded random integer nên dùng rejection sampling hoặc equivalent unbiased method.

---

# 133. Bulk API correctness

```text
random_fill(buffer)
```

phải có cùng semantic source quality như repeated primitive calls.

---

# 134. Zero-copy

Random bytes ghi trực tiếp vào caller-owned buffer.

Không yêu cầu intermediate heap buffer.

---

# 135. Memory safety

Buffer API phải kiểm tra:

```text
pointer
length
alignment
writability
```

theo Axiom memory/unsafe semantics.

---

# 136. Unsafe low-level access

Hardware-specific RNG access có thể tồn tại trong `unsafe`/platform layer.

Ordinary application không cần sử dụng.

---

# 137. AI-generated code safety

Compiler metadata có thể đánh dấu API:

```text
@security_random
@deterministic_random
@nonsecure_random
```

AI coding tools có thể dùng metadata để tránh API misuse.

---

# 138. ABI metadata

Compiler emits:

```text
rng algorithm descriptor
distribution descriptor
security classification
deterministic contract
```

khi required.

---

# 139. Version compatibility

`AXRANDOM_ABI_1` phải giữ:

- type layout;
- function calling convention;
- error semantics;
- random category semantics.

Algorithm sequence compatibility chỉ được guarantee cho explicitly versioned deterministic algorithms.

---

# 140. Formal invariants

```text
RANDOM-INV-01
PRNG không được được coi là entropy source.

RANDOM-INV-02
CSPRNG phải có security-specific API semantics.

RANDOM-INV-03
secure_random failure không được silently fallback sang ordinary PRNG.

RANDOM-INV-04
Deterministic RNG phải reproducible theo algorithm/version contract.

RANDOM-INV-05
Secure RNG state không được expose qua ordinary state API.

RANDOM-INV-06
Secure RNG output không được mặc định xuất hiện trong logs.

RANDOM-INV-07
Secure RNG output không được mặc định xuất hiện trong diagnostics.

RANDOM-INV-08
Secure RNG output không được mặc định xuất hiện trong observability telemetry.

RANDOM-INV-09
Entropy source health không đồng nghĩa cryptographic proof.

RANDOM-INV-10
Hardware RNG không mặc định được coi là trusted entropy tuyệt đối.

RANDOM-INV-11
Random integer range phải tránh modulo bias khi yêu cầu uniformity.

RANDOM-INV-12
Empty range phải trả lỗi xác định.

RANDOM-INV-13
Invalid distribution parameters phải được reject.

RANDOM-INV-14
Floating random canonical range phải được xác định rõ.

RANDOM-INV-15
RNG state phải xác định algorithm/version khi serialize.

RANDOM-INV-16
State thuộc algorithm khác không được silently restore.

RANDOM-INV-17
Thread-safe sharing không được là default requirement của mutable RNG.

RANDOM-INV-18
Parallel RNG phải hỗ trợ independent stream semantics.

RANDOM-INV-19
RNG splitting phải preserve stream identity.

RANDOM-INV-20
Deterministic RNG không được tự reseed từ external entropy.

RANDOM-INV-21
CSPRNG có thể reseed mà không phá API-level randomness contract.

RANDOM-INV-22
Process duplication không được vô tình tạo identical secure RNG stream.

RANDOM-INV-23
Security-sensitive consumers phải sử dụng secure randomness.

RANDOM-INV-24
AXRANDOM không tự định nghĩa cryptographic algorithms.

RANDOM-INV-25
AXRANDOM không được bypass AXSECURITY.

RANDOM-INV-26
AXRANDOM không sở hữu identity semantics.

RANDOM-INV-27
AXRANDOM không sở hữu key-management semantics.

RANDOM-INV-28
Random APIs hot-path phải hỗ trợ zero-allocation operation.

RANDOM-INV-29
Bulk random generation phải ghi trực tiếp vào caller buffer khi API cho phép.

RANDOM-INV-30
RNG global mutable state không được là runtime requirement.

RANDOM-INV-31
Deterministic replay phải ghi algorithm/version/seed hoặc equivalent state identity.

RANDOM-INV-32
Secure seed material không được log.

RANDOM-INV-33
Deterministic test seed có thể được log khi không phải secret.

RANDOM-INV-34
RNG resource usage phải có bounded configuration.

RANDOM-INV-35
Cross-security-domain RNG state không được chia sẻ mặc định.

RANDOM-INV-36
Virtual RNG không được đọc hardware entropy trong deterministic mode.

RANDOM-INV-37
Compiler có thể phân biệt secure và non-secure random API semantics.

RANDOM-INV-38
AI tooling không được tự chuyển ordinary RNG thành security RNG.

RANDOM-INV-39
Algorithm upgrade không được âm thầm phá deterministic compatibility contract.

RANDOM-INV-40
Mọi random API phải công khai rõ category: secure, pseudo, deterministic hoặc entropy.
```

---

# 141. Definition of Done

`AXRANDOM 5.0` được freeze khi có:

- entropy abstraction;
- system entropy;
- hardware entropy abstraction;
- entropy health;
- entropy metadata;
- CSPRNG;
- secure random API;
- explicit secure failure;
- general PRNG;
- deterministic PRNG;
- explicit seeds;
- automatic seeding;
- stream splitting;
- task/thread-safe usage model;
- process boundary handling;
- random bytes;
- integer generation;
- unbiased bounded integers;
- floating random;
- uniform distribution;
- Bernoulli;
- normal;
- exponential;
- Poisson;
- weighted sampling;
- reservoir sampling;
- shuffle;
- choice;
- deterministic state save/restore;
- deterministic replay;
- virtual randomness;
- parallel streams;
- SIMD/bulk generation;
- zero-allocation hot paths;
- resource limits;
- security separation;
- AXCRYPTO integration;
- AXSECURITY integration;
- AXIDENTITY integration;
- AXNETWORK integration;
- AXDIAGNOSTICS integration;
- AXOBSERVABILITY integration;
- AXLOGGING integration;
- AXAUDIT integration;
- AXCONFIG integration;
- compiler misuse diagnostics;
- AI metadata;
- native ABI;
- 40 invariants.

**AXRANDOM 5.0 → FROZEN.**

---

# BOOTSTRAP-766 — AXREGISTRY

**Native Naming, Service Discovery, Resource Registry, Endpoint Registry, Type/Schema Registry & Versioned Resolution Runtime 5.0**

Module tiếp theo sẽ giải quyết một foundation còn thiếu sau khi Axiom đã có:

```text
AXIDENTITY
AXNETWORK
AXPROCESS
AXIPC
AXSTORAGE
AXDATABASE
AXCONFIG
AXTIME
AXRANDOM
```

Các subsystem này cần một cơ chế chuẩn để:

```text
name
   ↓
namespace
   ↓
registry
   ↓
version
   ↓
resource/service
   ↓
resolve
```

`AXREGISTRY` sẽ đặc biệt tách **name resolution** khỏi **authorization**: registry chỉ xác định “tên này hiện resolve tới resource nào”, còn AXSECURITY/AXAUTH/AXCAPABILITY quyết định caller có được phép sử dụng resource đó hay không.