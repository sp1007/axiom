# SPEC-44 — Canonical CPU Feature Detection, `@target_feature` Legality & Function Multiversioning Specification

Status: draft (T475, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0095 §7–8, §42 (ASIMD-14)`; `specs/0163 §1–7`; `tasks/0341 §100 (ANUM-29..30)`; `tasks/0344 §100 (ASIMD-71..78, 97)`; `tasks/0347 §100 (ASIMD-71..78, 97)`; `tasks/0403 §82`; `tasks/0407 §35`; `tasks/0453 §194.14–15`; `spec/SPEC-04-core-extensibility.md (AXS-EXT-022/032/054/060/091)`; `spec/SPEC-42-simd.md`; `spec/SPEC-43-simd-backend.md`; `spec/SPEC-73-inlining-specialization-devirt.md`; `spec/SPEC-75-lto-wpo-section-gc-pgo.md`.
Covers: `REQ-SIMD-011`, `REQ-SIMD-012`, `REQ-SIMD-013`, `REQ-SIMD-051`, `REQ-SIMD-079`, `REQ-SIMD-094`, `REQ-SIMD-095`, `REQ-SIMD-217`, `REQ-SIMD-218`, `REQ-SIMD-219`, `REQ-SIMD-220`, `REQ-SIMD-221`, `REQ-SIMD-222`, `REQ-SIMD-223`, `REQ-SIMD-224`, `REQ-SIMD-243`, `REQ-SIMD-256`, `REQ-SIMD-257`.
Consumers: `compiler/driver/opts.ax`, `compiler/hir/lower.ax`, `compiler/types/typeck.ax`, `compiler/verify/verifier.ax`, `compiler/mir/builder.ax`, `compiler/lir/builder.ax`, `compiler/target/x64/isel.ax`, `compiler/target/x64/encode.ax`, `compiler/interp/`, `std/arch/x86_64.ax`, `std/arch/detect.ax`, `T476`–`T479`, `E15.4` (`SPEC-73`), `E15.5`, `E15.6` (`SPEC-75`).

## Tóm tắt

Tài liệu `SPEC-44` quy định chuẩn tắc đồ thị tập lệnh phần cứng (`TargetDesc` feature DAG), hợp đồng kiểm định thuộc tính `@target_feature("...")`, cơ chế dò tìm tính năng CPU lúc chạy (`std.arch.is_x86_feature_detected` qua `CPUID`/`XGETBV`), và cơ chế đa phiên bản hàm (`@multiversion`) cho phân hệ `E12.5` (Phase `P12`). Các quyết định kiến trúc cốt lõi gồm:
- **Phân cấp tính năng x86-64 trong `TargetDesc` (`SPEC-04 AXS-EXT-060`, `ASIMD-97`, `REQ-SIMD-243`)**: Mục tiêu `x86_64-windows` luôn bật sẵn tập lệnh cơ sở `sse` và `sse2`; các tập lệnh mở rộng (`sse3`, `ssse3`, `sse4.1`, `sse4.2`, `popcnt`, `lzcnt`, `bmi1`, `bmi2`, `avx`, `avx2`, `fma`, `avx512f`) tạo thành đồ thị kéo theo bất biến (`avx512f -> avx2 -> avx -> sse4.2 -> sse4.1 -> ssse3 -> sse3 -> sse2 -> sse`, `fma -> avx`, `sse4.2 -> popcnt`) và được điều khiển tường minh qua cờ dòng lệnh `--target-feature=+feat,-feat`.
- **Tách biệt tuyệt đối giữa hợp thức sinh mã và ngữ nghĩa ngôn ngữ Core (`0453 §194.15`, `ANUM-29..30`, `ASIMD-71..74`, `REQ-SIMD-011..013`)**: Tập tính năng CPU chỉ quyết định tính hợp lệ khi phát lệnh máy và độ rộng thanh ghi vật lý (`XMM` vs `YMM`), tuyệt đối **không** làm thay đổi ngữ nghĩa ngôn ngữ Core của Axiom. Compiler không bao giờ tự động chèn lệnh dò `CPUID` ngầm vào hàm thường (`ANUM-30`, `REQ-SIMD-095`).
- **An toàn lời gọi `@target_feature` và ranh giới inliner (`SPEC-04 AXS-EXT-022/032/054/091`, `ASIMD-71..72`)**: Gọi một hàm mang `@target_feature("...")` hoặc intrinsic `std.arch.x86_64` đòi hỏi tập tính năng rộng hơn hàm gọi sẽ bị từ chối ở thời điểm biên dịch với `AX_TARGET_FEATURE_MISMATCH` trừ khi nằm trong khối `unsafe { ... }`, nằm trong nhánh được bảo vệ bởi `is_x86_feature_detected("...")` thống trị (dominating guard), hoặc trong bộ điều phối `@multiversion`. Bộ nội tuyến (`inliner`) bị cấm nhúng thân hàm con có tập tính năng rộng hơn vào hàm gọi hẹp hơn để ngăn rò rỉ lệnh `VEX`/`YMM` ra ngoài nhánh bảo vệ (`REQ-SIMD-011`, `REQ-SIMD-051`).
- **Dò tìm tính năng lúc chạy (`CPUID`/`XGETBV`) và đa phiên bản hàm `@multiversion` (`0095 §8`, `ASIMD-73..78`, `REQ-SIMD-219..224`)**: `std.arch.detect` kiểm tra đồng thời bit phần cứng `CPUID` (leaf `1`, `7`, `0x80000001`) và bit trạng thái thanh ghi hệ điều hành `XGETBV(0)` (`XCR0` cho `XMM`/`YMM`/`ZMM`), lưu kết quả nguyên tử (`Atomic<u64>`), và được mô phỏng tất định trong `--interp` qua `--interp-cpu-features=<list>`. Thuộc tính `@multiversion("avx2,fma", "sse4.1")` sinh các bản sao chuyên biệt kèm bản sao cơ sở bắt buộc (`$mv$default`), bảo toàn nguyên vẹn ABI công khai (`Win64 ABI`), điều phối tất định theo thứ tự ưu tiên giảm dần lúc chạy, và tự động rút gọn thành lời gọi tĩnh trực tiếp khi `--target-feature` lúc biên dịch đã thỏa mãn bản sao cao nhất.

---

## 1. x86-64 Target Feature Hierarchy in `TargetDesc` & CLI Contract (`AXS-CPU-001`..`005`)

### AXS-CPU-001 — `TargetDesc` Feature Bitmask & Canonical x86-64 Feature Set (`SPEC-04 AXS-EXT-060`, `ASIMD-97`, `REQ-SIMD-243`, `T476`)

1. **`TargetFeatureSet` Representation**: In `compiler/target/` and `compiler/driver/opts.ax`, a target feature set is represented as a 64-bit bitmask (`u64`) stored in `TargetDesc.default_features`, `Session.target_features`, `FnSig.target_features` (`SPEC-04 AXS-EXT-022`), and `LirFunction.target_features` (`SPEC-04 AXS-EXT-054`).
2. **Canonical x86-64 Feature Table**: On `x86_64-windows` (and `x86_64-linux`), the following canonical feature names and bit positions are defined:

| Feature Name | Bit Index | Mask Constant (`u64`) | Category & Hardware Meaning | Baseline on `x86_64-windows` |
|---|---|---|---|---|
| `"sse"` | `0` | `1u64 << 0` (`0x0001`) | Streaming SIMD Extensions (`XMM0`–`XMM15`, scalar/packed `f32x4`) | **Yes (mandatory)** |
| `"sse2"` | `1` | `1u64 << 1` (`0x0002`) | SSE2 128-bit packed integers & `f64x2` (`X64_FEATURE_BASELINE = 0x3`) | **Yes (mandatory)** |
| `"sse3"` | `2` | `1u64 << 2` (`0x0004`) | SSE3 horizontal float ops (`HADDPS`/`HADDPD`, `MOVDDUP`, `LDDQU`) | Optional |
| `"ssse3"` | `3` | `1u64 << 3` (`0x0008`) | Supplemental SSE3 (`PSHUFB`, `PABSB/W/D`, `PMADDUBSW`, `PALIGNR`) | Optional |
| `"sse4.1"` | `4` | `1u64 << 4` (`0x0010`) | SSE4.1 (`PMULLD`, `PCMPEQQ`, `PBLENDVB`, `BLENDVPS/PD`, `ROUNDPS/PD`, `PINSR*`/`PEXTR*`, `PMOVSX*`/`ZX*`, `PTEST`) | Optional |
| `"sse4.2"` | `5` | `1u64 << 5` (`0x0020`) | SSE4.2 (`PCMPGTQ`, `CRC32`) | Optional |
| `"popcnt"` | `6` | `1u64 << 6` (`0x0040`) | Hardware `POPCNT` instruction (`F3 0F B8`) | Optional |
| `"lzcnt"` | `7` | `1u64 << 7` (`0x0080`) | Hardware `LZCNT` instruction (`F3 0F BD`) | Optional |
| `"bmi1"` | `8` | `1u64 << 8` (`0x0100`) | Bit Manipulation Set 1 (`TZCNT`, `ANDN`, `BEXTR`, `BLSI`, `BLSMSK`, `BLSR`) | Optional |
| `"bmi2"` | `9` | `1u64 << 9` (`0x0200`) | Bit Manipulation Set 2 (`BZHI`, `MULX`, `PDEP`, `PEXT`, `RORX`, `SARX`, `SHLX`, `SHRX`) | Optional |
| `"avx"` | `10` | `1u64 << 10` (`0x0400`) | 256-bit `YMM0`–`YMM15` registers, 3-operand VEX encoding, 256-bit float ops, `VZEROUPPER` | Optional |
| `"avx2"` | `11` | `1u64 << 11` (`0x0800`) | 256-bit packed integer SIMD in `YMM`, `VPERMD`/`VPERMQ`, `VPSLLV*`/`VPSRLV*`, `VGATHER*` | Optional |
| `"fma"` | `12` | `1u64 << 12` (`0x1000`) | FMA3 3-operand fused multiply-add (`VFMADD213PS/PD/SS/SD`, etc.) | Optional |
| `"avx512f"` | `13` | `1u64 << 13` (`0x2000`) | AVX-512 Foundation (`ZMM0`–`ZMM31`, `k0`–`k7` mask registers, EVEX) | Optional (modeled in DAG/detect) |

### AXS-CPU-002 — Feature Implication DAG & Forward/Backward Closure (`ASIMD-97`, `REQ-SIMD-243`, `T476`)

1. **Direct Implication Edges**: The x86-64 target database models instruction-set compatibility as a directed acyclic graph (DAG):
   - Vector ISA chain: `avx512f -> avx2 -> avx -> sse4.2 -> sse4.1 -> ssse3 -> sse3 -> sse2 -> sse`
   - FMA implication: `fma -> avx` (and transitively `sse4.2 .. sse`)
   - SSE4.2 / POPCNT implication: `sse4.2 -> popcnt`
   - Bit-manipulation chain: `bmi2 -> bmi1`
2. **Forward Closure (`expand_implied_features(mask: u64) -> u64`)**: Enabling any feature `+F` automatically sets every ancestor reachable from `F` in the DAG. For example, enabling `"avx2"` expands to `{sse, sse2, sse3, ssse3, sse4.1, sse4.2, popcnt, avx, avx2}` (`0x0C7F`); enabling `"fma"` expands to `{sse, sse2, sse3, ssse3, sse4.1, sse4.2, popcnt, avx, fma}` (`0x147F`).
3. **Reverse Closure on Removal (`disable_dependent_features(mask: u64, feat: u64) -> u64`)**: Disabling `-F` on the command line clears bit `F` together with every feature `G` whose forward closure includes `F` (e.g., `-avx` clears `avx`, `avx2`, `fma`, and `avx512f`). Baseline `sse` and `sse2` are permanently set on `x86_64-windows` (`mask | X64_FEATURE_BASELINE`).

### AXS-CPU-003 — CLI Option `--target-feature=+feat,-feat` (`SPEC-04 AXS-EXT-081`, `T476`)

1. `compiler/driver/opts.ax` accepts `--target-feature=<list>` (and `--target-features=<list>`) where `<list>` is a comma-separated sequence of `+feat`, `-feat`, or `feat` (treated as `+feat`) tokens evaluated left-to-right starting from `X64_FEATURE_BASELINE` (`sse,sse2`).
2. Each `+feat` applies `mask = expand_implied_features(mask | bit(feat))`, and each `-feat` (for non-baseline features) applies `mask = disable_dependent_features(mask, bit(feat))`.
3. Passing an unknown feature token (or attempting to disable mandatory baseline `-sse` / `-sse2` on `x86_64-windows`) emits `AX_TARGET_UNKNOWN_FEATURE` (`data.feature = "<token>"`).

### AXS-CPU-004 — Core Language Semantics vs Target Feature Legality Invariant (`0453 §194.15`, `ANUM-29..30`, `ASIMD-71..74`, `REQ-SIMD-011`..`013`, `REQ-SIMD-051`, `REQ-SIMD-079`, `REQ-SIMD-094`, `REQ-SIMD-217`, `REQ-SIMD-256`)

1. **Semantics Invariance (`REQ-SIMD-013`, `0453 §194.15`)**: Target features govern **instruction selection, physical vector register width (`XMM` vs `YMM`), and codegen legality** (`REQ-SIMD-012`), **never** Core Axiom language semantics. Portable code using scalar types or `std.simd.Vector<T, N>` / `Mask<N>` has one canonical meaning independent of `--target-feature` or `@target_feature`.
2. **Strict Emission Legality (`REQ-SIMD-011`, `REQ-SIMD-051`, `REQ-SIMD-079`)**: Neither instruction selection (`compiler/target/x64/isel.ax`), the vector legalizer (`compiler/lir/builder.ax`), nor any optimization pass may emit a machine instruction whose required feature bit is `0` in the active function's `effective_features(fn)` mask.

### AXS-CPU-005 — No Implicit Runtime CPU Probing in Ordinary Functions (`ANUM-30`, `ASIMD-14`, `ASIMD-73`, `REQ-SIMD-095`, `REQ-SIMD-219`, `REQ-SIMD-257`)

The compiler NEVER injects hidden runtime `CPUID` probes, startup constructors, or implicit dynamic dispatch tables into ordinary functions (`ANUM-30`, `REQ-SIMD-095`, `REQ-SIMD-257`). Runtime CPU feature detection and dispatch occur exclusively when requested through `std.arch.is_x86_feature_detected` / `std.arch.detect.*` (`§3`) or `@multiversion` (`§4`) (`ASIMD-14`, `ASIMD-73`, `REQ-SIMD-219`).

---

## 2. `@target_feature("...")` Attribute, Call-Site Safety & Inliner Contract (`AXS-CPU-010`..`014`)

### AXS-CPU-010 — `@target_feature("...")` Syntax, Lowering & Effective Feature Mask (`SPEC-04 AXS-EXT-022/032/054/091`, `REQ-SIMD-012`, `REQ-SIMD-094`, `REQ-SIMD-217`, `REQ-SIMD-256`, `T476`)

1. **Syntax & Allowed Positions**: `@target_feature("feat1,feat2,...")` (accepting comma-separated feature names with optional leading `+`) may be attached to any `fn` item (`fn`, `pub fn`, `unsafe fn`, or inherent/trait method). Attaching `@target_feature` to a non-function item (`struct`, `enum`, `union`, `const`, `static`, `type`, `trait`, or `extern` block) is rejected with `AX_TARGET_INVALID_ATTRIBUTE`.
2. **Attribute Side Table & Signature Lowering**: `compiler/hir/lower.ax` and `compiler/types/typeck.ax` parse each feature name in `@target_feature("...")` (emitting `AX_TARGET_UNKNOWN_FEATURE` on any unrecognized name or `-feat` negation inside `@target_feature`), compute the forward implication closure `attr_mask = expand_implied_features(raw_mask)`, and store `attr_mask` in the `TargetFeature` attribute side table (`SPEC-04 AXS-EXT-032`), `FnSig.target_features` (`SPEC-04 AXS-EXT-022`), `MirBody.target_features`, and `LirFunction.target_features` (`SPEC-04 AXS-EXT-054`).
3. **Effective Feature Mask of a Function**: For any function `f` compiled in a session with global CLI features `session.target_features`, the active feature set inside `f`'s body is:
   $$\text{effective\_features}(f) = \text{expand\_implied\_features}(\text{session.target\_features} \;\cup\; f.\text{target\_features})$$

### AXS-CPU-011 — Call-Site Feature Legality & Dominating Detection Guard (`ASIMD-71..72`, `REQ-SIMD-011`..`012`, `REQ-SIMD-217`..`218`, `T476`)

Let `req = callee.target_features` (for a `@target_feature` function or a target-gated `std.arch.x86_64` intrinsic such as `vpaddd_256` or `vfmadd213_ps256`) and `avail = effective_features(caller)`. A direct call from `caller` to `callee` at call site `C` is legal if and only if at least one of the following four conditions holds:
1. **Static Superset**: `(req & ~avail) == 0` — every feature required by `callee` is already statically enabled in `caller` (via `--target-feature` or `caller`'s own `@target_feature`).
2. **Dominating Runtime Detection Guard**: For every feature bit $b \in \text{req} \setminus \text{avail}$, call site `C` is control-dependent on the `then` branch of a dominating `if` condition formed by `std.arch.is_x86_feature_detected("<b_name>")` or `std.arch.detect.has_<b_name>()` (combined with `&&` when multiple bits are missing).
3. **Explicit `unsafe` Scope**: Call site `C` lies inside an `unsafe { ... }` block or `unsafe fn` body, where the caller explicitly assumes the target-feature precondition.
4. **Compiler-Generated `@multiversion` Dispatcher**: Call site `C` is emitted inside the synthesized dispatcher body of a `@multiversion` function (`AXS-CPU-033`) guarded by `detected_feature_mask()`.

If none of (1)–(4) holds, `compiler/types/typeck.ax` and `compiler/verify/verifier.ax` reject the call with `AX_TARGET_FEATURE_MISMATCH` (`data.required`, `data.available`; also aliased as `AX_SIMD_TARGET_FEATURE_MISMATCH` / `AX_SIMD_TARGET_FEATURE_REQUIRED`).

### AXS-CPU-012 — Function-Pointer Coercion Rule for `@target_feature` Functions (`ASIMD-72`, `REQ-SIMD-218`, `T476`)

Coercing or assigning a function item `f` with `(f.target_features & ~session.target_features) != 0` to a first-class function-pointer type `fn(...) -> R` outside an `unsafe { ... }` block is rejected with `AX_TARGET_FEATURE_MISMATCH`, because an indirect caller through `fn(...) -> R` cannot statically verify `f`'s extra feature requirements (`ASIMD-72`, `REQ-SIMD-218`).

### AXS-CPU-013 — Inliner & Interprocedural Optimization Feature Boundary (`SPEC-73 AXS-INL-021`, `REQ-SIMD-011`, `REQ-SIMD-051`, `T476`, `T478`)

In `compiler/opt/` (`SPEC-73`), the inliner MUST NOT inline a callee `g` into a caller `f` whenever `(effective_features(g) & ~effective_features(f)) != 0` — even if the call site inside `f` is guarded by `if is_x86_feature_detected(...)` or an `unsafe` block (`INLINE_ILLEGAL: TargetFeatureSubsetViolation`). Inlining across a narrower caller feature boundary is forbidden because instruction selection, register allocation (`RegClass.Vec256` / `YMM` spill slots), and `VZEROUPPER` placement operate at whole-function granularity in LIR/Machine IR and could otherwise hoist or spill `VEX`/`YMM` instructions into `f`'s unguarded entry prologue (`REQ-SIMD-011`, `REQ-SIMD-051`, `REQ-SIMD-218`).

### AXS-CPU-014 — Per-Function Legalizer, Auto-Vectorizer & Instruction Selector Confinement (`REQ-SIMD-051`, `REQ-SIMD-079`, `T470`, `T472`, `T473`, `T476`)

During MIR-to-LIR lowering (`compiler/lir/builder.ax`), auto-vectorization (`E15.5`), and x86-64 instruction selection (`compiler/target/x64/isel.ax`), every transformation queries `effective_features(current_fn)`:
- When `avx2` is set in `effective_features(current_fn)`, 256-bit `Vector<T, N>` values lower to `LirType.V256` (`RegClass.Vec256`, `YMM0`–`YMM15`) and emit VEX-256 instructions plus `VZEROUPPER` (`SPEC-43 AXS-SBE-010, 022, 042`).
- When `avx2` is clear in `effective_features(current_fn)`, 256-bit vectors split deterministically into two 128-bit `LirType.V128` (`XMM`) chunks (`SPEC-43 AXS-SBE-011`), using `sse4.1` instructions if `sse4.1` is set or baseline `sse2` instructions otherwise (`SPEC-43 AXS-SBE-040..041`).

---

## 3. Runtime CPU Feature Detection (`std.arch.detect`) & Oracle Simulation (`AXS-CPU-020`..`023`)

### AXS-CPU-020 — Hardware `cpuid_count` & `xgetbv` Intrinsics (`std.arch.x86_64`, `REQ-SIMD-095`, `REQ-SIMD-219`, `REQ-SIMD-257`, `T477`)

1. **Declarations in `std/arch/x86_64.ax`**:
   ```axiom
   pub struct CpuidResult {
       pub eax: u32,
       pub ebx: u32,
       pub ecx: u32,
       pub edx: u32,
   }

   @intrinsic pub fn cpuid_count(leaf: u32, subleaf: u32) -> CpuidResult
   @intrinsic pub fn xgetbv(xcr: u32) -> u64
   ```
2. **Native x86-64 Lowering (`compiler/target/x64/isel.ax`, `encode.ax`)**:
   - `cpuid_count(leaf, subleaf)` moves `leaf` into `EAX` and `subleaf` into `ECX`, preserves `RBX` across the instruction (via `MOV r_save, rbx` / `XCHG` so callee-saved `RBX` is never corrupted), emits `CPUID` (`0F A2`), and writes `(EAX, EBX, ECX, EDX)` into the returned `CpuidResult`.
   - `xgetbv(xcr)` moves `xcr` into `ECX`, emits `XGETBV` (`0F 01 D0`), and returns `((EDX as u64) << 32u64) | (EAX as u64)`.

### AXS-CPU-021 — `CPUID` Leaf `1` / `7` / `0x80000001` & OS `XCR0` Verification Protocol (`std/arch/detect.ax`, `T477`)

`std/arch/detect.ax` computes the runtime feature bitmask by verifying **both** CPU hardware support (`CPUID`) and operating-system context-switch state enablement (`OSXSAVE` + `XGETBV(0)`):
1. Query `max_basic = cpuid_count(0u32, 0u32).eax`, `leaf1 = cpuid_count(1u32, 0u32)` (if `max_basic >= 1u32`), `leaf7 = cpuid_count(7u32, 0u32)` (if `max_basic >= 7u32`), `max_ext = cpuid_count(0x8000_0000u32, 0u32).eax`, and `ext1 = cpuid_count(0x8000_0001u32, 0u32)` (if `max_ext >= 0x8000_0001u32`).
2. Read `osxsave = ((leaf1.ecx >> 27u32) & 1u32) != 0u32`. Only when `osxsave` is `true`, execute `xcr0 = xgetbv(0u32)`; otherwise `xcr0 = 0u64`.
3. Compute OS register-state gates:
   - `os_avx = osxsave && ((xcr0 & 0x6u64) == 0x6u64)` (`XCR0.XMM[1] == 1` and `XCR0.YMM[2] == 1`). If `os_avx` is `false`, `avx`, `avx2`, `fma`, and `avx512f` MUST report `false` even if `CPUID` hardware bits are set!
   - `os_avx512 = os_avx && ((xcr0 & 0xE0u64) == 0xE0u64)` (`XCR0.opmask[5]`, `XCR0.ZMM_Hi256[6]`, `XCR0.Hi16_ZMM[7]` all `1`).
4. Extract individual feature bits and apply `expand_implied_features` consistency:
   - `sse`: `(leaf1.edx >> 25u32) & 1u32 != 0u32`; `sse2`: `(leaf1.edx >> 26u32) & 1u32 != 0u32`
   - `sse3`: `(leaf1.ecx >> 0u32) & 1u32 != 0u32`; `ssse3`: `(leaf1.ecx >> 9u32) & 1u32 != 0u32`
   - `sse4.1`: `(leaf1.ecx >> 19u32) & 1u32 != 0u32`; `sse4.2`: `(leaf1.ecx >> 20u32) & 1u32 != 0u32`
   - `popcnt`: `(leaf1.ecx >> 23u32) & 1u32 != 0u32`; `lzcnt`: `(ext1.ecx >> 5u32) & 1u32 != 0u32`
   - `bmi1`: `(leaf7.ebx >> 3u32) & 1u32 != 0u32`; `bmi2`: `bmi1 && ((leaf7.ebx >> 8u32) & 1u32 != 0u32)`
   - `avx`: `os_avx && ((leaf1.ecx >> 28u32) & 1u32 != 0u32)`
   - `fma`: `avx && ((leaf1.ecx >> 12u32) & 1u32 != 0u32)`
   - `avx2`: `avx && ((leaf7.ebx >> 5u32) & 1u32 != 0u32)`
   - `avx512f`: `os_avx512 && avx2 && ((leaf7.ebx >> 16u32) & 1u32 != 0u32)`

### AXS-CPU-022 — Atomic One-Time Feature Caching & `std.arch.is_x86_feature_detected` Surface (`T477`)

1. **Lock-Free Atomic Cache**: `std/arch/detect.ax` caches the computed feature bitmask in an internal `Atomic<u64>` word (`FEATURES_CACHE`, where bit `63` `0x8000_0000_0000_0000u64` is the initialized sentinel). On first query, when `FEATURES_CACHE.load(Ordering.Acquire)` has bit `63 == 0`, the caller runs the `AXS-CPU-021` `CPUID`/`XGETBV` probe and stores `mask | (1u64 << 63u64)` with `Ordering.Release`. All subsequent queries read the cached mask in `O(1)` without re-executing `CPUID`.
2. **Public API (`std.arch` and `std.arch.detect`)**:
   - `pub fn detected_feature_mask() -> u64`
   - `pub fn is_x86_feature_detected(feature: Str) -> bool`
   - Fast inline queries: `has_sse2() -> bool`, `has_sse3() -> bool`, `has_ssse3() -> bool`, `has_sse41() -> bool`, `has_sse42() -> bool`, `has_popcnt() -> bool`, `has_lzcnt() -> bool`, `has_bmi1() -> bool`, `has_bmi2() -> bool`, `has_avx() -> bool`, `has_avx2() -> bool`, `has_fma() -> bool`, `has_avx512f() -> bool`.

### AXS-CPU-023 — Deterministic MIR Interpreter Feature Simulation (`--interp-cpu-features`, `INV-DET-003`, `INV-ORACLE-002`, `REQ-SIMD-218`, `T477`)

1. **Hermetic Oracle Simulation**: To guarantee cross-host determinism (`INV-DET-003`), the MIR interpreter (`compiler/interp/`) NEVER executes host `CPUID` when evaluating `cpuid_count` or `xgetbv`. Instead, it synthesizes exact `CpuidResult` leaves (`0`, `1`, `7`, `0x8000_0000`, `0x8000_0001`) and `XCR0` (`0x07u64` when `avx` is simulated, `0xE7u64` when `avx512f` is simulated, `0x03u64` otherwise) from the session's simulated feature mask configured by `--interp-cpu-features=<list>`.
2. **Default Oracle Profile**: When `--interp-cpu-features` is not specified on the command line, `--interp` defaults to the standard `x86_64-v3` feature set: `sse,sse2,sse3,ssse3,sse4.1,sse4.2,popcnt,lzcnt,bmi1,bmi2,avx,avx2,fma`.
3. **Oracle Trap on Unsupported Feature Execution (`REQ-SIMD-218`)**: If `--interp` enters a `@target_feature` function or executes a target-gated `std.arch.x86_64` intrinsic whose required features are not all enabled in the active `--interp-cpu-features` mask (for example, calling an `avx2` function inside an unguarded `unsafe` block under `--interp-cpu-features=sse2`), the interpreter traps deterministically with `AX_UNSAFE_INTERP_UB` (exit code `125`).

---

## 4. Function Multiversioning (`@multiversion`) & Dispatcher Contract (`AXS-CPU-030`..`034`)

### AXS-CPU-030 — `@multiversion` Syntax, Clone Set & Mandatory Baseline Fallback (`0095 §8`, `0453 §194.14`, `ASIMD-73..75`, `REQ-SIMD-219`..`221`, `T478`)

1. **Syntax**: `@multiversion("feat_set_1", "feat_set_2", ...)` may be attached to any concrete function definition `fn name(params...) -> R { body }`. Each string literal argument specifies a non-empty comma-separated target-feature set $C_k$ (`k = 0 .. M - 1`, $M \ge 1$). An explicit `"default"` entry may optionally appear last; whether written or omitted, the compiler ALWAYS synthesizes a mandatory baseline fallback clone (`default`).
2. **Validation**:
   - Attaching `@multiversion` to a non-function item, an `extern` declaration, an `@intrinsic` declaration, a body-less trait method, or a function that also carries `@target_feature` is rejected with `AX_TARGET_INVALID_ATTRIBUTE`.
   - Empty `@multiversion()` or duplicate normalized feature masks (`expand_implied_features(C_i) == expand_implied_features(C_j)`) are rejected with `AX_TARGET_INVALID_ATTRIBUTE`.
   - Any unrecognized feature name inside a `@multiversion` string argument is rejected with `AX_TARGET_UNKNOWN_FEATURE`.

### AXS-CPU-031 — Clone Synthesis, Deterministic Symbol Mangling & Per-Clone Lowering (`SPEC-04 AXS-EXT-022/054`, `ASIMD-74..75`, `REQ-SIMD-220`..`221`, `T478`)

For a `@multiversion` function with canonical symbol `<sym>`, `compiler/hir/lower.ax`, `compiler/types/typeck.ax`, and `compiler/mir/builder.ax` synthesize:
1. **Specialized Internal Clones (`<sym>$mv$<slug>`)**: For each specialized target-feature string $C_k$, a private clone body named `<sym>$mv$<slug>` where `<slug>` joins the explicitly listed feature tokens in ascending bit-index order with `_` and replaces `.` with `_` (for example, `"avx2,fma"` $\to$ `<sym>$mv$avx2_fma`; `"sse4.1"` $\to$ `<sym>$mv$sse4_1`). The clone's signature and MIR/LIR body carry `target_features = expand_implied_features(session.target_features | mask(C_k))`.
2. **Mandatory Baseline Clone (`<sym>$mv$default`)**: A private fallback clone named `<sym>$mv$default` carrying `target_features = session.target_features` (baseline `sse,sse2` on `x86_64-windows`).
3. **Per-Clone Legalization & Instruction Selection**: Every clone body is lowered independently through `compiler/lir/builder.ax` and `compiler/target/x64/isel.ax` under its own `effective_features(clone)` (`AXS-CPU-014`). Thus `<sym>$mv$avx2_fma` lowers 256-bit `f32x8` operations to native `YMM` `VFMADD213PS` + `VZEROUPPER`, `<sym>$mv$sse4_1` lowers to 128-bit SSE4.1 `XMM` pairs, and `<sym>$mv$default` lowers to pure baseline SSE2 `XMM` pairs.

### AXS-CPU-032 — Semantic Equivalence & External ABI Preservation Across Clones (`ASIMD-74, 78`, `REQ-SIMD-220`, `REQ-SIMD-224`, `T478`, `T479`)

1. **Common Semantic Contract (`ASIMD-74`, `REQ-SIMD-220`)**: Every clone of a `@multiversion` function represents the exact same Axiom semantic function and MUST produce identical observable results, return values, and trap behavior across `--interp-cpu-features=sse2`, `sse4.1`, `avx2,fma`, and native execution (`INV-ORACLE-002`).
2. **External ABI Invariance (`ASIMD-78`, `REQ-SIMD-224`)**: The public dispatcher symbol `<sym>` and all internal clones `<sym>$mv$*` share an identical external signature and calling convention (`CallConv.Win64`, `SPEC-43 AXS-SBE-020..022`). Vector parameters and returns use the target-independent Win64 ABI classification (indirect pointer / `sret`), and any AVX/AVX2 clone touching `YMM` registers executes `VZEROUPPER` before returning so callers remain completely insulated from the selected clone's internal register width.

### AXS-CPU-033 — Deterministic Feature-Priority Ordering & Runtime Dispatcher Generation (`ASIMD-75`, `REQ-SIMD-221`, `T478`)

1. **Priority Total Order**: Specialized clones $C_k$ are ordered by descending priority key:
   $$\text{priority}(C_k) = \bigl(\text{max\_vec\_bits}(C_k),\; \text{popcount}(\text{expand\_implied\_features}(C_k)),\; \text{highest\_bit}(C_k)\bigr)$$
   where $\text{max\_vec\_bits}(C_k) \in \{512, 256, 128\}$. Thus `"avx2,fma"` ($256\text{-bit}$, `popcount = 10`) always precedes `"avx2"` ($256\text{-bit}$, `popcount = 9`), which precedes `"sse4.1"` ($128\text{-bit}$, `popcount = 5`), which precedes `"default"` ($128\text{-bit}$ baseline).
2. **Generated Dispatcher Body**: When runtime dispatch is active (`AXS-CPU-034`), the public function `<sym>` loads `let mask = std.arch.detect.detected_feature_mask()` once and tests each specialized clone $C_k$ in descending priority order:
   ```axiom
   if (mask & REQ_MASK_K) == REQ_MASK_K {
       return <sym>$mv$<slug_k>(args...)
   }
   ```
   falling through unconditionally to `return <sym>$mv$default(args...)`.

### AXS-CPU-034 — Compile-Time Static Dispatch Resolution, LTO Pruning & PGO Profitability (`ASIMD-75..77`, `REQ-SIMD-221`..`223`, `T478`)

1. **Compile-Time Static Dispatch Elimination (`ASIMD-75`, `REQ-SIMD-221`)**: If the compilation unit's static target feature mask (`session.target_features` from `--target-feature`) already satisfies the highest-priority clone $C_{\text{top}}$ (`(mask(C_top) & ~session.target_features) == 0`), the compiler omits the runtime `detected_feature_mask()` check in `<sym>` and lowers `<sym>` to a direct unconditional call (eligible for inlining) to `<sym>$mv$<slug_top>`.
2. **LTO Unreachable Clone Elimination (`ASIMD-76`, `REQ-SIMD-222`, `SPEC-75`)**: When static dispatch resolution or whole-program LTO (`--lto`) proves that lower-priority `$mv$` clones have no remaining call sites, dead-function elimination and section GC (`COMDAT`) strip the unused clones from the final binary.
3. **PGO Profitability-Only Rule (`ASIMD-77`, `REQ-SIMD-223`, `SPEC-75 AXS-PGO-002`)**: Profile-Guided Optimization (`--pgo-use`) may guide clone inlining budgets and loop vectorization cost models inside clones, but NEVER alters clone semantics or bypasses target-feature legality checks.

---

## 5. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-CPU-040`..`042`)

### AXS-CPU-040 — Diagnostic Codes (`spec/diagnostics.md`, `compiler/diag/code.ax`, `T476`–`T478`)

| Code | Sev | Task | Condition & Payload |
|---|---|---|---|
| `AX_TARGET_UNKNOWN_FEATURE` | E | `T476` | Unknown feature name (or disallowed `-sse`/`-sse2` baseline removal) in `--target-feature`, `@target_feature("...")`, or `@multiversion("...")` (`data.feature`). |
| `AX_TARGET_INVALID_ATTRIBUTE` | E | `T476`, `T478` | `@target_feature` or `@multiversion` attached to a non-function item (`struct`, `enum`, `const`, `static`, `extern`), empty `@multiversion()`, duplicate clone feature sets, or `@multiversion` combined with `@target_feature`. |
| `AX_TARGET_FEATURE_MISMATCH` | E | `T476` | Calling a `@target_feature` function or target-gated `std.arch.x86_64` intrinsic (or coercing a `@target_feature` function to `fn(...)`) from a caller lacking the required features without an enclosing `unsafe` block or dominating `is_x86_feature_detected` guard (`data.required`, `data.available`; synonym `AX_SIMD_TARGET_FEATURE_MISMATCH` / `AX_SIMD_TARGET_FEATURE_REQUIRED`). |

### AXS-CPU-041 — Canonical Positive & Negative Examples

```axiom
use std.simd.f32x8
use std.arch.is_x86_feature_detected

@target_feature("avx2,fma")
fn kernel_avx2_fma(a: f32x8, b: f32x8, c: f32x8) -> f32x8 {
    a.fma(b, c)
}

// 1. Safe runtime-guarded call to a `@target_feature` function (AXS-CPU-011 rule 2)
pub fn compute_guarded(a: f32x8, b: f32x8, c: f32x8) -> f32x8 {
    if is_x86_feature_detected("avx2") && is_x86_feature_detected("fma") {
        return kernel_avx2_fma(a, b, c)
    }
    a.fma(b, c)
}

// 2. Declarative function multiversioning with automatic clone & dispatcher synthesis (AXS-CPU-030..034)
@multiversion("avx2,fma", "sse4.1")
pub fn dot8(a: f32x8, b: f32x8) -> f32 {
    let prod = a * b
    prod.reduce_add()
}

fn rejected_unguarded_call(a: f32x8, b: f32x8, c: f32x8) -> f32x8 {
    // ERROR [AX_TARGET_FEATURE_MISMATCH]: callee requires `avx2,fma` not enabled in caller
    kernel_avx2_fma(a, b, c)
}
```

### AXS-CPU-042 — Requirement & Task Traceability Matrix

| Requirement ID | Corpus Source & Summary | Normative Rules in `SPEC-44` | Delivering / Verifying Tasks |
|---|---|---|---|
| `REQ-SIMD-011`, `REQ-SIMD-012`, `REQ-SIMD-013` | `tasks/0403 §82`: Unsupported target features cannot be emitted; `@target_feature` governs codegen legality; runtime CPU dispatch remains outside Core language semantics. | `AXS-CPU-004`, `AXS-CPU-010`..`014` | `T475` (spec), `T476`, `T479` |
| `REQ-SIMD-094`, `REQ-SIMD-217`, `REQ-SIMD-256` | `tasks/0341 §100 ANUM-29`, `tasks/0344 §100 ASIMD-71`: Target feature requirements are explicit compiler contracts. | `AXS-CPU-004`, `AXS-CPU-010`..`012`, `AXS-CPU-040` | `T475` (spec), `T476` |
| `REQ-SIMD-095`, `REQ-SIMD-219`, `REQ-SIMD-257` | `tasks/0341 §100 ANUM-30`, `tasks/0344 §100 ASIMD-73`: CPU feature probing is never implicitly added to ordinary functions; runtime CPU dispatch is an explicit library/compiler mechanism. | `AXS-CPU-005`, `AXS-CPU-020`..`023`, `AXS-CPU-030` | `T475` (spec), `T477`, `T478` |
| `REQ-SIMD-051`, `REQ-SIMD-079`, `REQ-SIMD-243` | `tasks/0403 §82`, `tasks/0407 §35`, `tasks/0344 §100 ASIMD-97`: `TargetDesc` models instruction-set compatibility DAG; target feature availability is verified before emission and respected by vector optimizations and inlining. | `AXS-CPU-001`..`003`, `AXS-CPU-013`..`014` | `T476` |
| `REQ-SIMD-218`, `REQ-SIMD-220`, `REQ-SIMD-224` | `tasks/0344 §100 ASIMD-72, 74, 78`: Code requiring unavailable target features cannot execute through an unguarded path; multiversioning preserves a common semantic contract and external ABI at public boundaries. | `AXS-CPU-011`..`013`, `AXS-CPU-023`, `AXS-CPU-032` | `T479` (`T476`–`T478`) |
| `REQ-SIMD-221`, `REQ-SIMD-222`, `REQ-SIMD-223` | `tasks/0344 §100 ASIMD-75..77`: Target-specialized clones may be selected at compile time or runtime; static target facts / LTO eliminate unnecessary dispatch; PGO influences profitability only, never semantics. | `AXS-CPU-030`..`034` | `T478` |

## Sources

- `docs/base/specs/0095 - Axiom — SIMD, Vectorization & Data-Oriented Computing v0.1.md` (`§7–8, §42, ASIMD-14`)
- `docs/base/specs/0163 - AXIOM Target Description Architecture v0.1.md` (`§1–7`)
- `docs/base/tasks/0341 - BOOTSTRAP-082 — Axiom SIMD, Vector, Tensor & Numeric Computing Model.md` (`§100, ANUM-29..30`)
- `docs/base/tasks/0344 - BOOTSTRAP-085 — Axiom SIMD, Vector, Matrix, Numeric Computing & Hardware Acceleration Model.md` (`§100, ASIMD-71..78, 97`)
- `docs/base/tasks/0347 - BOOTSTRAP-088 — Axiom SIMD, Vector Types, Auto-Vectorization & Portable Vector Semantics.md` (`§100, ASIMD-71..78, 97`)
- `docs/base/tasks/0403 - BOOTSTRAP-144 — SIMD, Vector Types & Auto-Vectorization Engine.md` (`§82`)
- `docs/base/tasks/0407 - BOOTSTRAP-148 — Vectorization, SIMD & Auto-Vectorization Engine.md` (`§35`)
- `docs/base/tasks/0453 - BOOTSTRAP-194 — Cross-Compilation, Multi-Target & Universal Native Toolchain.md` (`§194.14–15`)
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-022`, `AXS-EXT-032`, `AXS-EXT-054`, `AXS-EXT-060`, `AXS-EXT-091`)
- `spec/SPEC-42-simd.md` (`AXS-SIMD-001`..`063`)
- `spec/SPEC-43-simd-backend.md` (`AXS-SBE-001`..`052`)
- `spec/SPEC-73-inlining-specialization-devirt.md` (`AXS-INL-021`)
- `spec/SPEC-75-lto-wpo-section-gc-pgo.md` (`AXS-LTO-001`, `AXS-PGO-002`)
- `spec/requirements/CATALOG.md` (`REQ-SIMD-011`..`013`, `051`, `079`, `094`..`095`, `217`..`224`, `243`, `256`..`257`)
