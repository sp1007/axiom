# SPEC-22 — Incremental Compilation, Multi-Tier Fingerprinting & Persistent Cache

- **Status**: draft (T756, 2026-11-03)
- **Owner**: `axiom-architect`
- **Consolidates**: `0142` (`specs/0142`, Part XXIII §16–§28 & §53), `0152` (`specs/0152`, §78–§79), `0153` (`specs/0153`, §18, §30 & §37 `ACACHE-20..24`), `0564` (`tasks/0564`, BOOTSTRAP-305 §305.6–§305.13 & §305.24), `0778` (`tasks/0778`, BOOTSTRAP-556 §556.48–§556.54, §556.141–§556.151 & §556.190–§556.200), `0788` (`tasks/0788`, BOOTSTRAP-566 §566.1–§566.32, §566.81–§566.125 & §566.168–§566.200), `0789` (`tasks/0789`, BOOTSTRAP-567 hermetic action digests), `0792` (`tasks/0792`, BOOTSTRAP-570 incremental IDE/semantic reuse)
- **Covers**: `REQ-CORE-3089`, `REQ-CORE-3090`, `REQ-LNK-634..933`, `REQ-LNK-1434..1633`
- **Related**: `spec/SPEC-21-query-engine-semantic-db.md`, `spec/SPEC-60-comptime-2-0.md`, `spec/SPEC-73-inlining-specialization-devirt.md`, `spec/SPEC-75-lto-wpo-section-gc-pgo.md`, `spec/diagnostics.md`, `spec/invariants.md`

## Tóm tắt

SPEC-22 định nghĩa mô hình biên dịch tăng dần (incremental compilation), hệ thống phân cấp dấu vân tay ngữ nghĩa 4 tầng (four-tier fingerprinting), thuật toán lan truyền thay đổi đỏ-xanh (`try_mark_green`), và bộ nhớ đệm bền vững trên đĩa (persistent cache) cho `compiler/` (E18.2):
1. **Phân cấp dấu vân tay 128-bit tách biệt miền (`Fingerprint128`)**: Tách bạch `SourceFingerprint` (nội dung byte chuẩn hóa), `AstFingerprint` (cú pháp phi vị trí, bỏ qua khoảng trắng và chú thích thường), `InterfaceFingerprint` + `AbiFingerprint` (chữ ký `pub`, kiểu, ràng buộc trait, layout `@repr(C)`), `BodyFingerprint` (`Verified MIR` của thân hàm), và `CodegenFingerprint` (đơn vị sinh mã đã đơn hình hóa kèm cờ đích/tối ưu hóa).
2. **Tường lửa giao diện–thân hàm & thuật toán đỏ-xanh (`try_mark_green`)**: Sửa đổi thân một hàm `priv` hoặc hàm `pub` không nội tuyến (`!@inline`) không làm đổi `InterfaceFingerprint` của module; các module phụ thuộc phía sau được đánh dấu xanh (green) mà không cần kiểm tra kiểu (`typeck_body`) lại (`0` truy vấn `typeck` hạ lưu bị chạy lại).
3. **Bộ nhớ đệm bền vững có kiểm chứng & đường nhanh `< 100 ms`**: Đồ thị phụ thuộc truy vấn, dấu vân tay, chẩn đoán và tệp `.obj` theo từng module được lưu trữ nguyên tử với khóa tổ hợp (`CompilerDigest`, `TargetTriple`, `OptProfile`, `SafetyProfile`, `ManifestDigest`). Khi không có thay đổi nguồn (no-op rebuild), trình biên dịch xác thực bảng băm gốc và hoàn tất trong `< 100 ms`.
4. **Bất biến tương đương tuyệt đối**: Biên dịch tăng dần là tối ưu hóa thuần túy — kết quả ngữ nghĩa, danh sách chẩn đoán và tệp thực thi `.obj`/`.exe` phải giống hệt từng byte so với biên dịch sạch (`--no-incremental`).

---

## 1. Four-Tier Fingerprint Hierarchy & Canonical Hashing

### `AXS-INC-001` — 128-Bit Domain-Separated Fingerprint Primitives (`Fingerprint128`)

1. **Cryptographic canonical hash**: All incremental fingerprints in `compiler/incremental/fingerprint` are 128-bit values (`Fingerprint128 { lo: u64, hi: u64 }`) derived by truncating BLAKE3-256 (or the canonical kernel 128-bit SipHash/BLAKE3 stream) over a domain-prefixed canonical byte stream (`0788 §566.80`).
2. **Domain separation**: Every fingerprint computation begins with an explicit ASCII domain tag (`"AXIOM-FP-SRC-v1"`, `"AXIOM-FP-AST-v1"`, `"AXIOM-FP-API-v1"`, `"AXIOM-FP-ABI-v1"`, `"AXIOM-FP-BODY-v1"`, `"AXIOM-FP-CGU-v1"`, `"AXIOM-FP-ACT-v1"`). Fingerprints from distinct domains are never interchangeable.
3. **Address and scheduling independence**: Hash streams SHALL serialize `SemanticKey` paths, canonical De Bruijn / ordinal type indices, and sorted dependency lists (`SPEC-21 AXS-QRY-003`). Raw pointer addresses, arena offsets, session-local `u32` IDs without canonical mapping, and file modification timestamps (`mtime`) SHALL NEVER enter any semantic or codegen fingerprint (`0153 ACACHE-20`, `0788 §566.11`, `0778 §556.200`).

```axiom
struct Fingerprint128 {
    lo: u64,
    hi: u64
}

enum FingerprintTier {
    Source,
    Ast,
    Interface,
    Abi,
    Body,
    Codegen
}
```

### `AXS-INC-002` — Multi-Tier Fingerprint Hierarchy

For every compilation unit and item (`SemanticKey`), the compiler computes a strict hierarchy of fingerprints (`0142 §XXIII.19–24`, `0152 §78`, `0564 §305.7`, `0778 §556.141–142`, `0788 §566.15–23`):

| Tier | Fingerprint Name | Granularity | Canonical Inputs | Insensitive To |
|---|---|---|---|---|
| **Tier 0** | `SourceFingerprint` | `SourceFileId` | Normalized UTF-8 bytes (`LF` line endings) + logical module path (`0788 §566.12`) | OS file `mtime`, physical workspace root path |
| **Tier 1** | `AstFingerprint` | `ModuleId` / per-item CST/AST | Token kinds, identifier/literal payloads, item structure, attribute tokens (`0778 §556.48`) | Whitespace, line breaks, byte spans (`Span`), non-doc comments (`//`, `/* */`) |
| **Tier 2a** | `InterfaceFingerprint` | `DefId` / `ModuleId` | Visibility (`pub` vs `priv`), item signature (`item_signature`), generic type/const params, `where` bounds, trait impl headers, exported `const` values, effect/capability contracts (`0564 §305.7`, `0778 §556.48`, `0788 §566.17`) | Private item declarations, non-inlined function bodies, local variable names, expression spans |
| **Tier 2b** | `AbiFingerprint` | `DefId` (`struct`, `enum`, `fn`) | `layout_of(T)` (size, alignment, field offsets, niche layout), `@repr(...)`, `@align(N)`, calling convention (`extern "C"`, Win64 ABI class), exported symbol name (`REQ-CORE-3090`, `0564 §305.8`, `0788 §566.18–19`) | Private helper functions, non-layout method bodies |
| **Tier 3** | `BodyFingerprint` | `DefId` (function/const/static body) | Canonical `Verified MIR` basic blocks, statements, terminators, local types, drop elaboration graph, referenced callee `SemanticKey`s (`0788 §566.16`) | Source whitespace, comments, byte spans, unreferenced sibling items in the same module |
| **Tier 4** | `CodegenFingerprint` | Monomorphized `CodegenUnit` | `BodyFingerprint` + transitive inlined `BodyFingerprint`s + referenced `AbiFingerprint`s + `ConstValue` digests + `TargetConfig` (`TargetTriple`, CPU features, `-O` level, `--panic`, `--safety-profile`) (`0142 §XXIII.24`, `0564 §305.9`) | Unreferenced modules, non-inlined cross-module private bodies |

### `AXS-INC-003` — `InterfaceFingerprint` vs `BodyFingerprint` Firewall & ABI Separation

1. **Semantic dependency on interfaces (`REQ-CORE-3089`)**: Incremental invalidation is governed by the semantic dependency graph in `CompilerDB` (`SPEC-21`), never by raw file modification timestamps.
2. **Three-way change classification (`REQ-CORE-3090`, `0564 §305.8`)**:
   - **Implementation-only change**: `BodyFingerprint(f)` changes while `InterfaceFingerprint(f)` and `AbiFingerprint(f)` remain identical. Downstream callers that do not inline `f` or evaluate `f` at compile time DO NOT re-run `resolve_module`, `item_signature`, `typeck_body`, or `mir_body`.
   - **Interface change**: `InterfaceFingerprint(item)` changes (e.g. parameter/return type, generic bound, visibility, or trait contract). All queries with a `DependencyKind.Interface` edge to `item` are invalidated and re-evaluated.
   - **ABI / layout change**: `AbiFingerprint(ty_or_fn)` changes (e.g. field added/reordered in a public or `@repr(C)` struct, `@align(N)` modified, or calling convention changed). All queries and `CodegenUnit`s with a `DependencyKind.Abi` or `DependencyKind.Layout` edge to `ty_or_fn` are invalidated (`0778 §556.51`, `0788 §566.29`).

### `AXS-INC-004` — Cross-Module `const`, Generic Monomorphization & Inlined Body Dependencies

While non-inlined runtime function calls depend only on `InterfaceFingerprint(callee)` and `AbiFingerprint(callee)` (`0142 §XXIII.18`, `0152 §79`):
1. **Compile-time evaluation (`const` / `comptime fn`)**: Evaluating a `const` item or `comptime fn` records a `DependencyKind.ConstBody` edge on `BodyFingerprint(callee)` and on the resulting `ConstValue` fingerprint (`SPEC-60 AXS-CTM-022`).
2. **Generic instantiation**: Monomorphizing a generic function `g<T>` in consumer module `M` records a `DependencyKind.GenericBody` edge from `M`'s `CodegenUnit` to `BodyFingerprint(g)` and `AbiFingerprint(T)`. Editing the body of `g<T>` leaves `M`'s `typeck_body` green (`InterfaceFingerprint(g)` unchanged) while invalidating only `M`'s monomorphized `CodegenFingerprint`.
3. **Cross-module inlining**: When the optimizer inlines callee `h` (`@inline` or profitability-driven inlining under `-O1`/`-O2`, `SPEC-73`) into caller `f`, `CodegenFingerprint(f)` records a `DependencyKind.InlinedBody` edge to `BodyFingerprint(h)`. Editing `h`'s body invalidates `CodegenFingerprint(f)` without invalidating `typeck_body(f)`.

---

## 2. Red-Green Change Propagation (`try_mark_green`) & Fine-Grained Invalidation

### `AXS-INC-010` — Red-Green Node Coloring & Typed Dependency Edges

Every memoized node `Q` in `CompilerDB` (`SPEC-21 AXS-QRY-010`) tracks its verification state at the current revision `R_curr` (`0778 §556.151`, `0788 §566.24–25`):
1. **Node colors**:
   - `Green(R_curr)`: Verified at `R_curr` — either newly computed with unchanged fingerprint (backdated) or proven unaffected because all input dependencies remained `Green`.
   - `Red(R_curr)`: Re-evaluated at `R_curr` and produced a `Fingerprint128` (or diagnostic set) different from its previous revision (`changed_at = R_curr`).
   - `Unknown(R_prev)`: Stale (`verified_at < R_curr`); requires `try_mark_green` before reuse.
2. **Typed dependency edges (`DependencyKind`)**: Each recorded edge `caller -> callee` carries a `DependencyKind` (`Ast`, `NameLookup`, `Interface`, `Abi`, `Layout`, `TraitImpl`, `ConstBody`, `GenericBody`, `InlinedBody`, `Codegen`) and the `Fingerprint128` observed when `caller` was last computed (`0788 §566.24–25`).

```axiom
enum NodeColor {
    Unknown(RevisionId),
    Green(RevisionId),
    Red(RevisionId)
}

enum DependencyKind {
    Ast,
    NameLookup,
    Interface,
    Abi,
    Layout,
    TraitImpl,
    ConstBody,
    GenericBody,
    InlinedBody,
    Codegen
}
```

### `AXS-INC-011` — Deterministic `try_mark_green` Verification & Backdating Algorithm

When `db.query(Q)` is requested at revision `R_curr` and `Q` is in state `Unknown(R_prev)` (`SPEC-21 AXS-QRY-033`, `0778 §556.199`, `0788 §566.89–98`, `T757`):
1. **Dependency walk**: The engine iterates `Q`'s recorded dependencies `[D_0, D_1, ..., D_{k-1}]` in deterministic recorded order.
2. **Recursive check**: For each `D_i`:
   - If `D_i` is an input table entry whose `SourceFingerprint` / config digest at `R_curr` equals the digest at `R_prev`, `D_i` is `Green(R_curr)`.
   - If `D_i` is a derived query in state `Unknown`, the engine recursively runs `try_mark_green(db, D_i)`.
   - If `D_i`'s fingerprint for the edge's `DependencyKind` at `R_curr` differs from the fingerprint observed by `Q` at `R_prev`, the loop aborts early: `Q` cannot be marked green without re-execution.
3. **Green reuse without re-execution**: If every `D_i` verifies with an unchanged fingerprint for its `DependencyKind`, `Q` is marked `Green(R_curr)` (`verified_at = R_curr`), its cached value and snapshot-bound diagnostics are replayed (`SPEC-21 AXS-QRY-030`), and `Q`'s provider is NOT executed.
4. **Re-execution and backdating**: If any `D_i` changed, `Q`'s provider executes at `R_curr`, producing `(new_val, new_diags)` with `new_fp = fingerprint128(new_val)`:
   - If `new_fp == old_fp` and `new_diags == old_diags`, `Q` is **backdated**: `verified_at = R_curr`, `changed_at` stays `R_prev`, and `Q` is colored `Green(R_curr)` so callers of `Q` are shielded from re-execution.
   - Otherwise, `changed_at = R_curr`, `Q` is colored `Red(R_curr)`, and callers depending on `Q`'s changed tier must re-evaluate.

### `AXS-INC-012` — Private-Body Firewall Guarantee (`Edit-One-Private-Fn` Invariant)

1. **Module interface aggregation**: A module `M`'s `InterfaceFingerprint(M)` aggregates only exported (`pub`) item signatures, exported type/trait definitions, exported `AbiFingerprint`s, and `pub use` re-exports (`0778 §556.48–49`, `0788 §566.17`).
2. **Zero downstream typeck on private/body-only edits**: When a developer edits whitespace/comments (`AstFingerprint` unchanged) or edits the body of a `priv fn` or a non-`@inline`, non-`comptime`, non-generic `pub fn` in module `A`:
   - `parse_module(A)`, `typeck_body(A.edited_fn)`, `mir_body(A.edited_fn)`, and `CodegenUnit(A)` re-run as needed.
   - `InterfaceFingerprint(A)` and `AbiFingerprint(A)` backdate to `Green(R_curr)`.
   - Every downstream module `B` that imports `A` verifies `InterfaceFingerprint(A)` as `Green(R_curr)` and executes **zero** `resolve_module(B)` or `typeck_body(B.*)` queries (`0152 §79`, `T757`, `T759`).

### `AXS-INC-013` — Fine-Grained Invalidation Matrix & Telemetry (`--emit=fingerprints`, `--emit=incremental-stats`)

1. **Invalidation matrix (`0778 §556.145–146`, `0788 §566.168–178`)**:
   - *Comment / whitespace edit*: `SourceFingerprint` `Red` -> `AstFingerprint` backdates `Green` -> `0` semantic, MIR, or codegen queries re-run (`zero-codegen rebuild`, `0788 §566.98`).
   - *Private or non-inlined `pub` function body edit*: `BodyFingerprint(f)` `Red`, `InterfaceFingerprint(f)` `Green` -> only `typeck_body(f)`, `mir_body(f)`, and `f`'s module `.obj` rebuild; `0` downstream `typeck` queries re-run.
   - *Inlined (`@inline`) or generic function body edit*: `InterfaceFingerprint(f)` `Green`, `BodyFingerprint(f)` `Red` -> `0` downstream `typeck` queries re-run; only callers whose `CodegenFingerprint` recorded `InlinedBody` / `GenericBody` on `f` regenerate machine code.
   - *Exported `const` / `comptime fn` body edit*: If the evaluated `ConstValue` backdates to the same value, downstream consumers stay `Green`; if `ConstValue` changes, only consumers with a `ConstBody` edge re-evaluate.
   - *Public signature or `@repr(C)` layout edit*: `InterfaceFingerprint` / `AbiFingerprint` `Red` -> only downstream items with an `Interface`, `Abi`, or `Layout` edge to the modified symbol re-evaluate (`0788 §566.27`).
2. **Inspector telemetry (`T757`)**:
   - `axiom inspect <target> --emit=fingerprints` outputs deterministic lines sorted by `SemanticKey` reporting `(SemanticKey, AstFingerprint, InterfaceFingerprint, AbiFingerprint, BodyFingerprint, CodegenFingerprint)`.
   - `axiom inspect <target> --emit=incremental-stats` (and `build --emit=incremental-stats`) outputs deterministic JSON/key-value counters: `queries_total`, `queries_green_reused`, `queries_recomputed`, `queries_backdated`, `modules_typechecked`, `cgu_reused`, `cgu_rebuilt`, and per-node `miss_reason` (`SOURCE_CHANGED`, `API_CHANGED`, `ABI_CHANGED`, `BODY_CHANGED`, `CONFIG_CHANGED`, `COLD_CACHE`) (`0788 §566.104–107`).

---

## 3. Persistent On-Disk Incremental Cache, Action Digest & `< 100 ms` No-Op Fast Path

### `AXS-INC-020` — Layered Cache Architecture (`L0`–`L2`)

The self-hosted compiler implements a three-tier local cache hierarchy (`0564 §305.12`, `0788 §566.3–7`):
1. **`L0` Process-local `CompilerDB` memo tables**: In-memory arena and query slots within a single compiler invocation (`SPEC-21`).
2. **`L1` Session / daemon in-memory snapshot store**: Retains `CompilerDB` across incremental edits in long-running `LSP` / daemon sessions (`0792 §570.1`).
3. **`L2` Persistent on-disk workspace cache (`<build-dir>/.axiom-cache/`)**: Stores the serialized dependency graph (`dep-graph.axcache`), fingerprint index, cached diagnostic table, and content-addressed per-module COFF `.obj` / metadata artifacts (`objects/<fp128_hex>.obj`) (`T758`).

### `AXS-INC-021` — Hermetic Action Digest & Cache Key Binding (`ACACHE-20..21`)

Every persistent cache lookup and on-disk index header is keyed by a hermetic 128-bit `EnvironmentDigest` (`0142 §XXIII.27`, `0153 ACACHE-20..21`, `0564 §305.11`, `0788 §566.10`, `0789 §567.1`, `T758`):
```text
EnvironmentDigest = BLAKE3_128(
    "AXIOM-ENV-v1" ||
    compiler_binary_digest ||
    cache_schema_version ||
    target_triple ||
    cpu_feature_mask ||
    opt_profile ||
    safety_profile ||
    panic_strategy ||
    artifact_kind ||
    manifest_digest
)
```
Undeclared host environment variables, current working directory strings, and wall-clock timestamps are excluded from `EnvironmentDigest` (`0153 ADET-23`, `0788 §566.200 #8–10`). Any change to `EnvironmentDigest` invalidates target-dependent cached `.obj` artifacts while preserving crash safety.

### `AXS-INC-022` — Versioned, Checksummed On-Disk Schema, Atomic Publication & Corruption Fallback (`ACACHE-23..24`)

1. **Header & integrity check**: Every `.axcache` file begins with a fixed 32-byte header: 8-byte magic `"AXCACHE1"`, `u32 schema_version`, `u32 flags`, `Fingerprint128 env_digest`, and a trailing 128-bit BLAKE3 payload checksum covering all serialized bytes (`0778 §556.193`, `0788 §566.200 #45–48`).
2. **Atomic publication**: Cache files and cached `.obj` blobs are written to a process-unique temporary file (`<path>.tmp.<pid>`) and flushed before an atomic rename (`MoveFileExW(..., MOVEFILE_REPLACE_EXISTING)` on Windows / `rename` on POSIX) into the cache directory (`0788 §566.200 #53–56`). Partial writes from crashes or power loss are never visible as valid entries.
3. **Graceful fallback (`0153 ACACHE-23..24`, `0778 §556.194–195`)**: If `.axiom-cache` is missing, has an unknown magic or `schema_version`, fails the payload checksum, or references a missing `.obj` blob, the compiler silently discards the stale/corrupt cache entry, logs `miss_reason = CORRUPT | SCHEMA_CHANGED` in `--emit=incremental-stats`, and falls back to clean recomputation without emitting a user error or failing the build.

### `AXS-INC-023` — Root Workspace Digest & `< 100 ms` No-Op Rebuild Fast Path

To satisfy the P18 exit criterion (`no-op rebuild < 100 ms on the compiler itself`, `T758`, `T759`):
1. The root cache index stores a compact **Workspace Input Manifest** listing every input `SourceFileId`, its logical path, file byte length, and `SourceFingerprint`, plus `EnvironmentDigest` and the final output artifact path and `ArtifactFingerprint`.
2. On `axiom build` (when `--no-incremental` is not passed), before constructing AST/HIR/MIR arenas, the driver loads `dep-graph.axcache`, verifies `EnvironmentDigest`, hashes the workspace source files (using fast `(size, mtime_ns)` pre-check backed by BLAKE3 `SourceFingerprint` verification when metadata differs or in strict mode), and checks that the output `.exe`/`.lib`/`.dll` exists and matches `ArtifactFingerprint` (`0788 §566.97–99`).
3. If all input `SourceFingerprint`s, `EnvironmentDigest`, and output `ArtifactFingerprint` match, the driver replays any cached warnings in canonical `AXD-060` order and exits `0` immediately (`0` semantic queries, `0` codegen units, `0` linker invocations) in `< 100 ms`.

### `AXS-INC-024` — Clean-vs-Incremental Semantic, Diagnostic & Binary Equivalence (`ACACHE-22`)

1. **Zero semantic authority (`0153 ACACHE-22`, `0788 §566.199`)**: The incremental cache is strictly a performance optimization. For any workspace state `S` and any sequence of prior edits `S_0 -> S_1 -> ... -> S`, an incremental build of `S` MUST produce:
   - The exact same exit code and sorted diagnostic stream (`--json` and human stderr, `AXD-060`) as a clean build (`--no-incremental`).
   - Byte-for-byte identical COFF `.obj`, `.lib`, `.dll`, and PE32+ `.exe` artifacts (`INV-DET-001`, `INV-DET-002`).
2. **Error & recovery non-pollution (`0778 §556.199 #31–32`, `0788 §566.85`)**: Compilation units that emit error diagnostics MAY cache their input-bound diagnostics for warm replay, but SHALL NEVER publish a `Ready` `.obj` codegen artifact into the persistent artifact cache.

---

## 4. Diagnostics, Canonical Examples & Verification Matrix

### `AXS-INC-050` — Incremental Cache & CLI Diagnostic Policy

1. **Transparent cache fallback**: Cache misses, version upgrades, and corrupt/truncated `.axcache` files NEVER emit user-facing `error` or `warning` diagnostics; they recover transparently via clean recomputation (`AXS-INC-022`).
2. **CLI flags**:
   - `--incremental` (default for workspace `build`/`check`) and `--no-incremental` (forces clean full evaluation and bypasses reading `.axiom-cache`).
   - `--cache-dir <path>` overrides `<build-dir>/.axiom-cache`.
   - `inspect --emit=fingerprints` and `inspect --emit=incremental-stats` (or `build --emit=incremental-stats`) emit deterministic machine-readable fingerprint and reuse telemetry (`AXS-INC-013`).
3. **Diagnostic equivalence**: Any semantic, type, ownership, capability, or linker error (`AX_*`) present in a cached module is replayed in exact `AXD-060` order on warm incremental runs (`SPEC-21 AXS-QRY-030`, `AXS-INC-024`).

### `AXS-INC-051` — Positive Canonical Examples

```axiom
// === File: math_lib.ax ===
module math_lib

// Private helper: not part of `InterfaceFingerprint(math_lib)`.
// Editing `internal_scale` body (e.g. changing `x * 2` to `x + x`)
// changes `BodyFingerprint(math_lib.internal_scale)` and `CodegenFingerprint(math_lib)`,
// but `InterfaceFingerprint(math_lib)` backdates to GREEN (AXS-INC-012).
fn internal_scale(x: i32) -> i32 {
    x * 2
}

// Public non-inlined function: signature `(i32) -> i32` is in `InterfaceFingerprint(math_lib)`.
pub fn compute_metric(v: i32) -> i32 {
    internal_scale(v) + 1
}

// Public constant: value `100` is part of `ConstBody` / `InterfaceFingerprint`.
pub const BASE_OFFSET: i32 = 100
```

```axiom
// === File: app.ax ===
module app

use math_lib

// When `math_lib.internal_scale` (or whitespace/comments in `math_lib.ax`) is edited:
// 1. `try_mark_green` checks `InterfaceFingerprint(math_lib)` -> GREEN.
// 2. `typeck_body(app.main)` and `mir_body(app.main)` are marked GREEN without re-running!
// 3. `--emit=incremental-stats` reports `modules_typechecked: 1` (`math_lib` only),
//    `cgu_reused: 1` (`app.obj`), `cgu_rebuilt: 1` (`math_lib.obj`).
pub fn main() -> i32 {
    let base = math_lib.BASE_OFFSET
    let res = math_lib.compute_metric(21)
    if base + res == 143 {
        0
    } else {
        1
    }
}
```

### `AXS-INC-052` — Negative / Invalidation Canonical Examples (Signature & ABI Propagation)

```axiom
// === Scenario A: Public signature change invalidates downstream typeck (AXS-INC-003) ===
// In `math_lib.ax`, changing `pub fn compute_metric(v: i32) -> i32`
// to `pub fn compute_metric(v: i64) -> i64` changes `InterfaceFingerprint(math_lib.compute_metric)`.
// `try_mark_green` marks `typeck_body(app.main)` RED, re-runs `typeck_body(app.main)`,
// and deterministically emits:
// ERROR [AX_TYPE_MISMATCH]: expected `i64`, found `i32` at `math_lib.compute_metric(21i32)`

// === Scenario B: `@repr(C)` layout / ABI change invalidates layout consumers (REQ-CORE-3090) ===
module abi_types

@repr(C)
pub struct PacketHeader {
    pub magic: u32,
    pub flags: u16,
    pub reserved: u16 // Adding `pub seq: u64` changes `AbiFingerprint(abi_types.PacketHeader)`.
}

// Any consumer module querying `layout_of(abi_types.PacketHeader)` or passing `PacketHeader`
// across calls has a `DependencyKind.Abi` / `DependencyKind.Layout` edge, so its
// `mir_body` and `CodegenFingerprint` are invalidated and rebuilt automatically.
```

### `AXS-INC-053` — E18.2 Implementation & Verification Matrix

| Task | Scope | Required Verification Target | Invariant ID |
|---|---|---|---|
| `T757` | 128-bit `Source`/`Ast`/`Interface`/`Abi`/`Body`/`Codegen` fingerprints, red-green `try_mark_green` propagation, `inspect --emit=fingerprints` & `--emit=incremental-stats` | `tests/run/incremental_fingerprint` | `INV-INC-001` |
| `T758` | Persistent `.axiom-cache` on-disk dependency graph & `.obj` cache, hermetic `EnvironmentDigest`, corruption recovery, `< 100 ms` no-op rebuild fast path | `tests/run/incremental_cache` | `INV-INC-002` |
| `T759` | End-to-end E18.2 conformance: `< 100 ms` no-op self-rebuild, edit-one-private-fn (`0` downstream `typeck`), signature/const/generic invalidation, clean-vs-incremental byte identity | `tests/conformance/p18/e18_2_incremental` | `INV-INC-003` |

---

## Sources

- `docs/base/specs/0142 - Part XXIII — Build System · Package Resolution · Incremental Compilation · Reproducible Build.md` (§XXIII.16–§XXIII.28, §XXIII.53)
- `docs/base/specs/0152 - AXIOM IMPLEMENTATION BLUEPRINT — TỪ SPEC ĐẾN COMPILER TỰ CHẠY.md` (§78 Incremental compilation, §79 Private implementation changes)
- `docs/base/specs/0153 - AXIOM COMPILER KERNEL SPEC.md` (§18 Incremental invalidation, §30 Compiler Cache Boundary, §37 `ACACHE-20..24`)
- `docs/base/tasks/0564 - BOOTSTRAP-305 — AXIOM TOOLCHAIN DRIVER & BUILD GRAPH ENGINE.md` (§305.6–§305.13, §305.24)
- `docs/base/tasks/0778 - BOOTSTRAP-556 — COMPILER FRONTEND PERFORMANCE 2.0, INCREMENTAL LEXING/PARSING, PARALLEL NAME RESOLUTION & FAST SEMANTIC ANALYSIS.md` (§556.48–§556.54, §556.141–§556.151, §556.190–§556.200)
- `docs/base/tasks/0788 - BOOTSTRAP-566 — COMPILER CACHE 3.0 — SEMANTIC INVALIDATION, CROSS-PHASE REUSE, REMOTE CACHE, CACHE TRUST, CACHE GC & ZERO-REBUILD INCREMENTAL COMPILATION.md` (§566.1–§566.32, §566.81–§566.125, §566.168–§566.200)
- `docs/base/tasks/0789 - BOOTSTRAP-567 — COMPILER DISTRIBUTED BUILD 2.0 — REMOTE EXECUTION, CONTENT-ADDRESSED WORKERS, HERMETIC ACTIONS, REMOTE ARTIFACT TRANSFER, SCHEDULING & VERIFICATION.md`
- `docs/base/tasks/0792 - BOOTSTRAP-570 — COMPILER IDE/LSP ENGINE 4.0.md`
