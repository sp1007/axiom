# SPEC-113 — Canonical Build Sandbox, Hermetic/Reproducible Compilation, Ed25519 Signing & Supply-Chain Trust Specification

- **Status**: draft (T862, 2026-11-08)
- **Owner**: axiom-architect
- **Phase**: P20 (E20.4 — Hermetic Build Sandbox, Reproducible Compilation, Ed25519 Signing & Supply-Chain Trust)
- **Rules**: `AXS-HERM-001` .. `AXS-HERM-053`
- **Covers**: `REQ-PKG-022`, `REQ-PKG-024`
- **Consolidates**: `tasks/0590 (§1–§52, ABUILD-01..30)`; `tasks/0449 (§1–§33, ASEC-20..44)`; `tasks/0772 (§550.1–§550.79, #1–200)`; `tasks/0661 (§5, §14, §18–§24)`; `tasks/1065 (§50–§60, §112–§140, §199 PKG-INV-01..40)`; `spec/SPEC-53-safety-profiles-capability-security.md`; `spec/SPEC-88-cross-compilation-platform-layer.md`; `spec/SPEC-110-build-graph-driver.md`; `spec/SPEC-111-package-manager-resolution-lockfiles.md`; `spec/SPEC-112-package-registry-distribution.md`; `spec/BOOTSTRAP.md`.
- **Consumers**: `compiler/build/sandbox`, `compiler/build/repro`, `std/pkg/trust`, `compiler/driver/trust_cmd`, `tests/run/build_hermetic`, `tests/run/pkg_supply_chain`, `tests/conformance/p20/e20_4_hermetic_supply_chain`, `T863`–`T865`.

## Tóm tắt

Đặc tả `SPEC-113` quy định kiến trúc chính tắc cho mô hình tin cậy chuỗi cung ứng (`Safe ≠ Trusted`, `Signed ≠ Correct`), chính sách kiểm soát leo thang đặc quyền của gói phụ thuộc (`[trust.policy]`), hộp cát dựng kín (hermetic build sandbox), hợp đồng biên dịch tái lập đồng nhất từng bit giữa các thư mục và máy chủ khác nhau (`REQ-PKG-022`, `REQ-PKG-024`), chữ ký số Ed25519 cho gói và chuỗi công cụ, bản kê chứng thực nguồn gốc dựng (`.axprov.json`), kiểm định biên dịch kép đa dạng (Diverse Double-Compilation — DDC), và giao diện dòng lệnh `axiomc trust|audit|verify-repro|provenance` cho phân hệ `E20.4` (Phase `P20`):

1. **Mô hình tin cậy chuỗi cung ứng bốn chiều và chống leo thang capability qua phụ thuộc (`AXS-HERM-001`..`AXS-HERM-004`, `REQ-PKG-024`)**: Phân tách độc lập giữa An toàn ngôn ngữ (`Safe` vs `Unsafe`), Quyền năng tài nguyên (`Capability`), Độ tin cậy nguồn/nhà phát hành (`Source/Publisher Trust`), và Tính toàn vẹn tạo phẩm (`Artifact Integrity`) (`tasks/0449 §1–§4, ASEC-20..44`, `tasks/0590 §2–§3, ABUILD-12`). Mỗi gói khai báo tập capability cần thiết (`unsafe`, `ffi`, `net`, `fs`, `process`, `asm`) trong `axiom.toml`. Trình kiểm toán phụ thuộc (`std/pkg/trust`, `axiomc audit`) tính bao đóng capability bắc cầu trên toàn bộ `DependencyGraph` và từ chối ngay lập tức (`AX_DRIVER_BAD_MANIFEST` với `data.kind = "capability_escalation_denied"`) khi bất kỳ gói phụ thuộc trực tiếp hoặc gián tiếp nào yêu cầu hoặc sử dụng capability không được cấp phép tường minh bởi `[trust.policy]` của không gian làm việc gốc (`ASEC-34`, `ABUILD-07`, `ABUILD-23`).
2. **Hộp cát dựng kín (`BuildSandbox`) cô lập hệ thống tệp, mạng, môi trường, đồng hồ và tiến trình (`AXS-HERM-010`..`AXS-HERM-015`, `REQ-PKG-022`, `REQ-PKG-024`)**: Mọi bước biên dịch, đánh giá `comptime`, và thực thi `[[build_tool]]` chạy trong `BuildSandbox` (`compiler/build/sandbox`) với cây mã nguồn `/source` và `/dependencies` chỉ đọc (`read-only`), đầu ra bị khóa chặt vào thư mục tạo phẩm `/output` được chỉ định của gói, chuẩn hóa đường dẫn và giải liên kết tượng trưng trước khi kiểm tra quyền (`canonicalize -> resolve -> authorize -> access`, chống thoát đường dẫn `..`/symlink/junction `ABUILD-22`), cấm tuyệt đối truy cập mạng (`NetworkPolicy = Denied`, `ABUILD-02`), lọc sạch biến môi trường và `PATH` của máy chủ theo danh sách trắng tường minh (`ABUILD-04`), cố định đồng hồ ảo (`ClockPolicy.Frozen`, `SOURCE_DATE_EPOCH = 0`) và hạt giống ngẫu nhiên tất định (`ABUILD-05`), đồng thời khóa việc tạo tiến trình con trái phép (`ABUILD-08..09`).
3. **Ánh xạ lại tiền tố đường dẫn chuẩn tắc (`--remap-path-prefix`) và tái lập đồng nhất từng bit (`AXS-HERM-020`..`AXS-HERM-023`, `REQ-PKG-022`)**: Bộ chuẩn hóa tái lập (`compiler/build/repro`) ánh xạ mọi đường dẫn tệp nguồn, bảng dòng gỡ lỗi (`.debug_line`/DWARF/CodeView), vị trí `panic`, và siêu dữ liệu `.axmi`/`.axmeta` sang tiền tố ảo chuẩn (`@ws/...`, `@pkg/<ns>/<name>@<ver>/...`, `@std/...`, `@gen/...`) hoặc theo cờ `--remap-path-prefix <from>=<to>`, đồng thời áp đặt thứ tự tất định cho ký hiệu, đoạn (section), bảng định vị lại, và mục lưu trữ tĩnh (`mtime = 0`, `TimeDateStamp = 0`). Cùng một đầu vào mã nguồn và `axiom.lock` luôn tạo ra tệp thực thi, thư viện, `.axmeta`, và `.axpkg` giống hệt nhau từng bit trên các thư mục checkout, biến môi trường, ngôn ngữ vùng miền (locale), và số luồng `--jobs` khác nhau, được kiểm chứng tự động qua `axiomc build --verify-repro` / `axiomc verify-repro`.
4. **Chữ ký số Ed25519, bản kê chứng thực nguồn gốc `.axprov.json` và biên dịch kép đa dạng DDC (`AXS-HERM-030`..`AXS-HERM-035`)**: Chuẩn hóa chữ ký Ed25519 (RFC 8032) trên bảng kê định danh tạo phẩm chuẩn tắc (`PackageIdentity`, `merkle_root`, `SIF`, `AbiFingerprint`, `TargetFingerprint`, `lock_graph_hash`), tách biệt hoàn toàn trình biên dịch khỏi khóa bí mật ký số (`tasks/0772 §550.8`), hỗ trợ xoay vòng/thu hồi khóa và chuỗi băm nhật ký minh bạch (`ArtifactLog`), xuất bản kê chứng thực nguồn gốc dựng JSON (`.axprov.json`) gắn kết `CompilerFingerprint`, `SdkFingerprint`, `axiom.lock` và mã băm SHA-256 của từng tạo phẩm đầu ra, cũng như quy trình kiểm định biên dịch kép đa dạng (DDC) chống cửa hậu trình biên dịch hạt giống (`tasks/0772 §550.13–§550.18`).
5. **Giao diện dòng lệnh `axiomc trust|audit|verify-repro|provenance` và ma trận kiểm chứng E20.4 (`AXS-HERM-040`..`AXS-HERM-053`)**: Quy định chi tiết các lệnh con CLI, bảng ánh xạ mã chẩn đoán, ví dụ Axiom chuẩn tắc (`=` và `.`), và các bất biến `INV-HERM-001`..`INV-HERM-003` cho `T863`–`T865`.

---

## 1. Supply-Chain Trust Model, Package Capability Declarations & Capability-Escalation Policy (`AXS-HERM-001`..`004`)

### AXS-HERM-001 — Four-Dimensional Supply-Chain Trust Model & Non-Equivalence Invariants (`tasks/0449 §1–§4, §8, §18–§24, ASEC-20..44`, `tasks/0590 §2–§3, §30, §51 ABUILD-12..13`, `tasks/0772 §550.1–§550.4, §550.10, §550.68–§550.69, §550.79`)

1. **Four Orthogonal Supply-Chain Planes (`tasks/0590 §2`, `tasks/0449 §1, §32`)**:
   Extending the three language/OS security dimensions of `SPEC-53 AXS-SEC-001`, the Axiom build and package supply chain separates four distinct trust planes that MUST NEVER be conflated into a single boolean `trusted = true` or a numeric "security score" (`tasks/0590 §2–§3, §30–§31`, `tasks/0772 §550.2, §550.68–§550.69, §550.79 #85–91, #199`):
   - **`SourceTrust`**: Provenance and review status of the source tree (`LocalWorkspace`, `PinnedVcsCommit`, `VerifiedRegistrySource`, `AuditedSource`, `UnknownSource`).
   - **`BuildTrust`**: Hermeticity, sandbox isolation, and reproducibility of the build process that transformed source inputs into artifacts (`UnverifiedBuild`, `SandboxedHermetic`, `ReproducibleVerified`, `AttestedBuild`).
   - **`ArtifactTrust`**: Cryptographic integrity and publisher authenticity of a distributed `.axpkg`, `.axmi`/`.axmeta`, `.axlib`, executable, or toolchain bundle (`ChecksumVerified`, `SignedBy(SignerId, KeyId)`, `TransparencyLogged`, `Revoked`, `Quarantined`).
   - **`RuntimeTrust` (`Authority & Safety`)**: The static language safety profile (`safe`, `sandbox`, `system` per `SPEC-53`) and the explicit capability set (`unsafe`, `ffi`, `net`, `fs`, `process`, `asm`) that the code is permitted to exercise at build time or runtime.
2. **Fundamental Non-Equivalence Laws (`ASEC-20..22, ASEC-30..32`, `ABUILD-12..13`, `tasks/0772 §550.10, §550.79 #15–18, #87–90`)**:
   - **`Safe ≠ Trusted` (`ASEC-20, ASEC-21`)**: A third-party package written entirely in safe Axiom (`@forbid_unsafe`) is guaranteed free of memory UB and data races, but is still **untrusted** with respect to filesystem, network, process, or logic abuse unless granted authority by workspace policy. Conversely, a kernel or cryptographic driver package may be **trusted** by workspace policy to use `unsafe` or `asm` while still undergoing full semantic verification outside its `unsafe` blocks.
   - **`Hash/Identity ≠ Trust` (`ASEC-30`)**: Matching a `SHA-256` content hash or `PackageIdentity` proves only that the bytes have not changed since lockfile recording, not that the package is benign or authorized to escalate capabilities.
   - **`Signed ≠ Safe` and `Signed ≠ Correct` (`ASEC-31`, `tasks/0590 §2–§3`, `tasks/0772 §550.10, #16, #87`)**: A valid Ed25519 signature proves only that the holder of `KeyId` signed the canonical artifact digest and metadata transcript; a signed package containing `unsafe` or `ffi` remains subject to `[trust.policy]` capability checks and compiler verification.
   - **`Reproducible ≠ Secure` (`tasks/0772 §550.79 #17, #88`)**: Bit-for-bit reproducibility proves that the binary was produced deterministically from the declared inputs and toolchain without hidden build injection, not that the source code itself is free of logic vulnerabilities.
   - **`ABI-Compatible ≠ Trusted` (`ASEC-32`, `tasks/0449 §18`)**: Passing `.axmeta` `AbiFingerprint` and `TargetFingerprint` checks proves binary layout compatibility, not supply-chain trust or capability authorization.
3. **Zero Mandatory Runtime Overhead (`ASEC-40, ASEC-44`, `tasks/0772 §550.77–§550.78, #174–179, #200`, `REQ-PKG-024`)**:
   - All supply-chain trust checks, capability-escalation audits, Ed25519 signature verifications, and provenance attestations execute strictly at package resolution, build, or verification time (`std/pkg/trust`, `compiler/build/sandbox`, `compiler/driver/trust_cmd`). They NEVER inject a garbage collector, virtual machine, background security daemon, hidden thread, network call, or telemetry into compiled user binaries.

### AXS-HERM-002 — Package Capability Declarations (`unsafe`, `ffi`, `net`, `fs`, `process`, `asm`) & Reachability Auditing (`tasks/0449 §5–§11, §25–§26, ASEC-34..35`, `tasks/0590 §4, §14–§16, §31–§33, ABUILD-23..24`, `REQ-PKG-024`, `T864`)

1. **Six Canonical Package-Level Capability Identifiers**:
   Every package `axiom.toml` MAY declare a `[package.capabilities]` table (and optional `[build.capabilities]` for `[[build_tool]]` / `comptime` build-time requirements) over the closed canonical set of six supply-chain capability identifiers:
   ```toml
   [package.capabilities]
   unsafe = false   # unsafe { ... }, unsafe fn/trait/impl, raw pointer deref/arith, static mut, @at/@addr
   ffi = false      # extern "<abi>" blocks, @link, @export, std.ffi / dynamic library loading
   asm = false      # @naked functions, inline/module machine assembly, privileged ISA intrinsics
   fs = false       # std.fs / host.file_* / FsCap filesystem authority
   net = false      # std.net / host.net_* / NetCap network socket authority
   process = false  # std.process / host.process_* / ProcessCap child process execution
   ```
   When `[package.capabilities]` (or an individual key) is omitted in a third-party dependency's `axiom.toml`, all omitted capabilities default to `false` (pure safe, computation-only Axiom).
2. **Compiler-Verified Capability Usage vs Manifest Declaration (`tasks/0449 §25–§26`, `tasks/0590 §31–§32`, `T864`)**:
   For every package $P$ in the workspace or dependency graph, `CompilerDB` and `std/pkg/trust` compute two capability bitmasks (`u32` bitset where `CAP_UNSAFE = 1 << 0`, `CAP_FFI = 1 << 1`, `CAP_NET = 1 << 2`, `CAP_FS = 1 << 3`, `CAP_PROCESS = 1 << 4`, `CAP_ASM = 1 << 5`):
   - **`DeclaredCaps(P)`**: The bitmask parsed from `P`'s `axiom.toml` `[package.capabilities]` (and recorded in `P`'s `.axmi`/`.axmeta` `InterfaceSummarySection` and `.axpkg` index record).
   - **`ActualCaps(P)` (`InherentCaps(P)` & `ReachableCaps(P)`)**: Derived directly from `CompilerDB` semantic/MIR analysis of `P`'s source modules (or from `P`'s verified `.axmi` `FnContractSummary` & import table for precompiled binary packages):
     1. `unsafe`: Set iff any module in $P$ contains an `unsafe` block, `unsafe fn`, `unsafe trait`, `unsafe impl`, raw pointer dereference/offset, `static mut`, or `@at`/`@addr` declaration.
     2. `ffi`: Set iff any module in $P$ declares an `extern "<abi>"` block, `@link(...)`, `@export`, `@jni_export`, `@wasm_import`, or imports `std.ffi` / `std.sys.*_dl`.
     3. `asm`: Set iff any module in $P$ declares a `@naked` function, inline/module assembly construct, or privileged hardware CSR/MMIO instruction.
     4. `fs`: Set iff any module in $P$ imports or calls `std.fs`, `std.os` filesystem primitives, `host.file_*`, or accepts/uses `std.security.FsCap`.
     5. `net`: Set iff any module in $P$ imports or calls `std.net`, `host.net_*`, or accepts/uses `std.security.NetCap`.
     6. `process`: Set iff any module in $P$ imports or calls `std.process`, `host.process_*`, or accepts/uses `std.security.ProcessCap`.
3. **No Hidden Undeclared Capabilities in Dependencies (`ASEC-34`, `ABUILD-24`)**:
   - If a package $P$ exercises a capability $c \in \text{ActualCaps}(P)$ that is NOT declared in $\text{DeclaredCaps}(P)$ (`(ActualCaps(P) & ~DeclaredCaps(P)) != 0`), `axiomc pkg pack|publish`, `axiomc audit`, and workspace builds under `[trust.policy]` reject $P$ with `AX_DRIVER_BAD_MANIFEST`:
     - `data.kind = "undeclared_package_capability"`
     - `data.package = "<namespace>/<name>@<version>"`
     - `data.capability = "<unsafe|ffi|net|fs|process|asm>"`
     - `data.item = "<module.item_name>"`
   - Conversely, if a package declares a capability in `DeclaredCaps(P)` that is never reached from the workspace's entry points (`(DeclaredCaps(P) & ~ReachableCaps(P)) != 0`), `axiomc audit` reports it as an `unused_capability` finding (`ASEC-35`, `tasks/0449 §26`, `ASEC-43`: least-authority analysis informs the developer and fails only when `--deny-unused-capabilities` is passed, never silently altering program semantics).

### AXS-HERM-003 — Transitive Dependency Trust Policy (`[trust.policy]`) & Capability-Escalation Rejection (`REQ-PKG-024`, `tasks/0449 §8–§11, ASEC-34`, `tasks/0590 §16, §32–§35, ABUILD-07, ABUILD-20, ABUILD-23..24`, `T864`)

1. **Workspace Root `[trust.policy]` Schema in `axiom.toml`**:
   The root workspace (or standalone root package) `axiom.toml` defines the authoritative supply-chain trust and capability budget for the entire dependency graph via `[trust.policy]` and optional per-package `[trust.packages."<ns>/<name>"]` overrides:
   ```toml
   [trust.policy]
   enforce = true
   default_allowed_capabilities = [] # Third-party dependencies get zero privileged capabilities by default
   allow_unsafe = ["axiom/core_math", "corp/crypto_sys"]
   allow_ffi = ["corp/crypto_sys"]
   allow_asm = []
   allow_fs = ["corp/config_loader"]
   allow_net = []
   allow_process = []
   allow_build_tools = ["corp/schema_gen"]
   require_signed = false
   require_reproducible = false
   trusted_signers = ["ed25519:a1b2c3d4e5f60718"]

   [trust.packages."corp/crypto_sys"]
   version = "^1.4.0"
   capabilities = ["unsafe", "ffi"]
   signer = "ed25519:a1b2c3d4e5f60718"
   ```
   Only the **root workspace `axiom.toml`** may define `[trust.policy]`. Any `[trust.policy]` table embedded inside a non-root dependency package is ignored for capability granting (and flagged if it attempts self-granting) so a dependency can never grant permissions to itself (`tasks/0449 §10`, `tasks/0590 §15–§16`).
2. **Transitive Capability Closure & Explicit Capability-Escalation Rejection (`REQ-PKG-024`, `ASEC-34`, `ABUILD-07`, `ABUILD-20`, `ABUILD-23`)**:
   - Let $G = (V, E)$ be the resolved `DependencyGraph` (`SPEC-110`, `SPEC-111`). For every package node $P \in V$, its effective required capability set is:
     $$\text{RequiredCaps}(P) = \text{DeclaredCaps}(P) \cup \text{ActualCaps}(P)$$
     and its transitive capability closure across dependency edges is:
     $$\text{CapClosure}(P) = \text{RequiredCaps}(P) \cup \bigcup_{(P \to Q) \in E} \text{CapClosure}(Q)$$
   - For each non-root dependency package $Q \in V$, let $\text{GrantedCaps}(Q)$ be the union of `default_allowed_capabilities`, the per-capability allowlists `allow_<cap>` in `[trust.policy]` that match $Q$'s canonical `<namespace>/<name>` (or `<name>` when `namespace == "default"`), and any explicit `[trust.packages."<ns>/<name>"].capabilities` entry matching $Q$'s resolved version.
   - **Pre-build enforcement gate (`ABUILD-20`, `REQ-PKG-024`)**: Before `BuildGraph` compilation or linking executes (and during `axiomc audit`), `std/pkg/trust` verifies that for every dependency $Q \in V$:
     $$\text{RequiredCaps}(Q) \subseteq \text{GrantedCaps}(Q)$$
     and that for every transitive chain $R \to \dots \to P \to Q$, if $P$ is restricted by a scoped ceiling $\text{MaxSubtreeCaps}(P)$, $\text{CapClosure}(P) \subseteq \text{MaxSubtreeCaps}(P)$.
   - If any direct or transitive dependency $Q$ requests or uses a capability $c \notin \text{GrantedCaps}(Q)$ (for example, workspace root `app` depends on safe library `json_util`, which transitively depends on `evil_dep` that uses `unsafe`, `ffi`, or `net` without a grant in `app`'s `[trust.policy]`), the build/audit fails closed immediately with `AX_DRIVER_BAD_MANIFEST`:
     - `data.kind = "capability_escalation_denied"`
     - `data.package = "<namespace>/<name>@<version>"`
     - `data.capability = "<unsafe|ffi|net|fs|process|asm>"`
     - `data.dependency_path = "app@0.1.0 -> json_util@1.2.0 -> evil_dep@0.3.1"`

### AXS-HERM-004 — Build-Tool (`[[build_tool]]`) & `comptime` Authority Confinement & Input Provenance (`tasks/0449 §11–§14, ASEC-24..26`, `tasks/0590 §13–§16, §50, ABUILD-07..09`, `tasks/0772 §550.22–§550.25`)

1. **Build Tools as Explicit Untrusted Execution Boundaries (`ASEC-26`, `tasks/0590 §14–§16`, `tasks/0772 §550.22–§550.24`)**:
   - Compiling a package's `.ax` source files and executing a package's `[[build_tool]]` binary are distinct trust boundaries (`tasks/0449 §11`). A dependency package may only execute a `[[build_tool]]` if its package coordinate is explicitly listed in `[trust.policy].allow_build_tools` (workspace member packages are permitted by default within their sandboxed `inputs`/`outputs`).
   - A `[[build_tool]]` target cannot escalate its granted capabilities (`ReadSource` / `WriteArtifact` can never self-upgrade to `Network`, `ExecuteTool`, or host `ReadFilesystem`; `ABUILD-07`).
2. **External Tool Fingerprinting (`ExecuteTool`, `tasks/0590 §13, ABUILD-08..09`, `tasks/0772 §550.37–§550.38`)**:
   - Arbitrary shell/interpreter spawning (`cmd.exe`, `powershell.exe`, `sh`, `bash`, `python`, `perl`) is unconditionally forbidden in hermetic builds.
   - If a build action requires an external code-generator binary (`ExecuteTool`), it MUST be declared in `axiom.toml` with a pinned `ToolIdentity`:
     ```
     ToolIdentity = {
         tool_id:          String,     // e.g. "flatc"
         version:          SemVer,
         executable_sha256: Digest256, // verified before spawn
         args_template:    Vec<String>,
         declared_inputs:  Vec<String>,
         declared_outputs: Vec<String>,
     }
     ```
     The tool's `executable_sha256`, `args_template`, and input/output digests are folded directly into `HermeticBuildFingerprint` (`AXS-HERM-022`).
3. **Mandatory Provenance for Generated Files (`tasks/0590 §50`, `tasks/0772 §550.25, #70–72`)**:
   - The compiler MUST NEVER treat a file that merely appears inside a build directory as a valid compilation input unless it is registered in `BuildInputDB` with a verified `GeneratedSourceProvenance` record (`generator_id`, `generator_version`, `generator_exe_sha256`, `input_merkle_root`, `config_hash`, `output_sha256`) matching a declared `outputs` entry of an authorized `[[build_tool]]` or `comptime` generator (`SPEC-110 AXS-BLD-022`). Any undeclared or extra file written by a build tool causes the action to fail with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "undeclared_build_output"`, `data.path`).

---

## 2. Hermetic Build Sandbox & Host Isolation (`AXS-HERM-010`..`015`)

### AXS-HERM-010 — Formal Hermetic Build Contract & Self-Contained `BuildSandbox` (`REQ-PKG-022`, `REQ-PKG-024`, `tasks/0590 §4–§5, §17, §43, ABUILD-01..06, ABUILD-28..30`, `tasks/0772 §550.6`, `T863`)

1. **Pure Functional Hermeticity Law (`tasks/0590 §17`, `ABUILD-01, ABUILD-06`)**:
   In hermetic build mode (active by default for all workspace builds with `deterministic = true` and enforced strictly under `--hermetic` or `--sandbox=strict`), every build output artifact is a pure deterministic function of explicitly declared and content-fingerprinted inputs:
   $$\text{Artifact} = \mathcal{F}\!\left(\text{SourceTree},\; \text{LockedDeps},\; \text{ToolchainIdentity},\; \text{TargetDesc},\; \text{SdkFingerprint},\; \text{FeatureSet},\; \text{ProfileConfig},\; \text{ComptimeInputs},\; \text{BuildToolInputs},\; \text{DeclaredEnv}\right)$$
   Undeclared host state — including files outside declared package roots, ambient environment variables, host `PATH`, wall-clock time, OS CSPRNG entropy, network responses, user/machine names, and checkout directory paths — MUST have **zero** influence on emitted bytes (`ABUILD-02..06`).
2. **Container-Free Native Enforcement (`tasks/0590 §5, §43, ABUILD-28..30`)**:
   `compiler/build/sandbox` enforces the `BuildSandbox` policy (`filesystem_policy`, `network_policy`, `process_policy`, `environment_policy`, `clock_policy`, `random_policy`, `resource_limits`) directly inside the `axiomc` build driver, `CompilerDB` source loader, `comptime` evaluator (`SPEC-60`), and `[[build_tool]]` host harness without requiring Docker, Nix, Bazel, or root/administrator OS privileges. Any policy violation fails closed with an explicit diagnostic (`ABUILD-30`).

### AXS-HERM-011 — Virtual Filesystem Namespaces, Read-Only Source Tree, Output Confinement & Canonicalize-Before-Authorize Path Defense (`REQ-PKG-022`, `tasks/0590 §6–§7, ABUILD-03, ABUILD-22`, `T863`)

1. **Five Isolated Sandbox Filesystem Mounts (`tasks/0590 §6`)**:
   For each `BuildAction` executing on compilation unit $U$ of package $P$, `compiler/build/sandbox` exposes only five logical filesystem namespaces and hides the rest of the host filesystem (`C:\Users\...`, `/home/...`, `/etc/...`, `/var/...`):
   - **`/source`** (mapped to $P$'s package root directory): **Read-only (`FsPerm.Read`)**. Contains only files tracked in $P$'s package source tree.
   - **`/dependencies`** (mapped to the read-only `.axiom/cache/pkg/sha256/...` or `vendor/` roots of $P$'s direct dependencies in `axiom.lock`): **Read-only (`FsPerm.Read`)**. $P$ cannot read files belonging to unrelated packages not in its declared dependency closure.
   - **`/build`** (mapped to `.axiom/target/<env>/<profile>/work/<unit_id>/`): **Read-write scratch directory (`FsPerm.ReadWrite`)**, wiped clean before action start and deleted upon action completion.
   - **`/output`** (mapped to `.axiom/target/<env>/<profile>/deps/<unit_id>/` for compilation/archive actions, or `.axiom/target/<env>/<profile>/gen/<unit_id>/` for `[[build_tool]]` actions): **Confined artifact destination (`FsPerm.ReadWriteCreate`)**. Every emitted `.axmi`, `.obj`/`.o`, `.axlib`/`.lib`/`.a`, binary, or generated `.ax` file MUST be written inside `/output` via atomic temp-write-then-rename (`SPEC-110 AXS-BLD-033`).
   - **`/cache`** (mapped to `.axiom/cache/`): Accessible only by the compiler's internal cache manager (`compiler/build/cache`), never directly writable by user `comptime` code or `[[build_tool]]` binaries.
2. **Read-Only Source & Dependency Tree Enforcement**:
   Any attempt by compilation, `comptime` evaluation, or a `[[build_tool]]` to open a file for writing, appending, truncation, creation, rename, or deletion under `/source`, `/dependencies`, or the workspace root (`axiom.toml`, `axiom.lock`, `src/**`) is blocked before touching disk and emits `AX_DRIVER_BAD_MANIFEST` (`data.kind = "sandbox_fs_violation"`, `data.operation = "write_readonly_source"`, `data.path`).
3. **Canonicalize-Before-Authorize Path-Escape Defense (`tasks/0590 §7`, `ABUILD-22`)**:
   To prevent Time-of-Check-to-Time-of-Use (TOCTOU) and traversal escapes (`../secret`, absolute host paths `C:\...` or `/etc/...`, POSIX symlinks, Windows NTFS junctions/reparse points, or `\\?\` device paths), `compiler/build/sandbox` MUST execute path validation in strict four-step order:
   $$\text{1. Canonicalize \& Resolve All Symlinks/Junctions} \;\longrightarrow\; \text{2. Map to Sandbox Namespace Identity} \;\longrightarrow\; \text{3. Authorize Against Mount Permission} \;\longrightarrow\; \text{4. Perform File Access}$$
   - Authorizing a raw lexical path string *before* resolving `..` segments and symlink/junction targets is strictly forbidden (`tasks/0590 §7`).
   - If the canonicalized physical path resolves outside the physical root of `/source`, `/dependencies`, `/build`, or `/output` (including a symlink inside `/source` whose target points outside the package directory), the access is denied immediately with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "sandbox_fs_violation"`, `data.operation = "path_escape"`, `data.path`, `data.resolved_path`).

### AXS-HERM-012 — Zero Network Access During Compilation & Comptime (`REQ-PKG-022`, `REQ-PKG-024`, `tasks/0590 §8–§9, ABUILD-02, ABUILD-21`, `tasks/0449 §14, ASEC-27`, `SPEC-112 AXS-REG-001`, `T863`)

1. **Unconditional Compile-Time Network Ban (`NetworkPolicy = Denied`, `ABUILD-02`)**:
   During workspace `BuildGraph` execution (`RunBuildTool`, `EmitInterface`, `CompileCodegenUnit`, `AssembleArchive`, `LinkArtifact`), `NetworkPolicy` is unconditionally `Denied`. Neither the compiler frontend/backend, the `comptime` CTFE interpreter (`SPEC-60`), nor any `[[build_tool]]` process may open a TCP/UDP/raw socket, perform DNS lookup, or make HTTP/HTTPS requests.
2. **Separation of Runtime `net` Capability from Build-Time Network Access (`ASEC-25`)**:
   Declaring `net = true` under `[package.capabilities]` in `axiom.toml` (and granting `allow_net` in `[trust.policy]`) authorizes the **compiled target program** to use `std.net` at runtime; it NEVER grants network access to the package during compilation, `comptime`, or `[[build_tool]]` execution.
3. **Diagnostic on Violation**:
   Any attempt to invoke network operations during build or `comptime` fails closed with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "sandbox_net_violation"`, `data.package`, `data.endpoint`) (or `AX_CTM_CAPABILITY_DENIED` when triggered directly inside a `comptime` expression per `SPEC-60 AXS-CTM-003`).

### AXS-HERM-013 — Sanitized Environment Variable Allowlist & Host `PATH` Scrubbing (`REQ-PKG-022`, `tasks/0590 §10, ABUILD-04`, `tasks/0772 §550.6, §550.36–§550.37, #64–65`, `T863`)

1. **Default Host Environment Scrubbing (`ABUILD-04`)**:
   `compiler/build/sandbox` scrubs the entire inherited host OS environment table (`environ` / `GetEnvironmentStringsW`). Ambient variables such as `HOME`, `USERPROFILE`, `USERNAME`, `USER`, `PATH`, `TEMP`, `TMP`, `TMPDIR`, `APPDATA`, `LOCALAPPDATA`, `HOSTNAME`, `COMPUTERNAME`, `CPU_COUNT`, `NUMBER_OF_PROCESSORS`, `LANG`, `LC_ALL`, `LC_CTYPE`, `TZ`, `RANDOM`, `PWD`, `CD`, `SSH_AUTH_SOCK`, `AWS_*`, `GITHUB_*`, and `CFLAGS`/`LDFLAGS` are hidden from compilation queries, `@build_env(...)`, `comptime`, and `[[build_tool]]` processes (`tasks/0590 §10`).
2. **Synthetic Canonical Environment Table**:
   Inside `BuildSandbox`, the environment table contains ONLY:
   - **Compiler-controlled canonical variables**:
     - `AXIOM_PKG_NAMESPACE = "<namespace>"`
     - `AXIOM_PKG_NAME = "<name>"`
     - `AXIOM_PKG_VERSION = "<major>.<minor>.<patch>"`
     - `AXIOM_TARGET_TRIPLE = "<target_triple>"`
     - `AXIOM_HOST_TRIPLE = "<host_triple>"`
     - `AXIOM_PROFILE = "<profile_name>"`
     - `AXIOM_EDITION = "2026"`
     - `AXIOM_SOURCE_DIR = "/source"`
     - `AXIOM_OUT_DIR = "/output"`
     - `SOURCE_DATE_EPOCH = "0"`
     - `TZ = "UTC"`
     - `LC_ALL = "C"`
   - **Explicitly allowlisted build variables**: Variables listed in `[build].env_allowlist = ["KEY1", ...]` in the root `axiom.toml` and passed via `--build-env KEY1=VALUE1` (or read from the host only when explicitly listed in `env_allowlist`). Every allowlisted `(key, value)` pair (or `"<unset>"` sentinel if absent) is sorted by ASCII `key` and hashed into `DeclaredEnvDigest` inside `HermeticBuildFingerprint` (`AXS-HERM-022`).
3. **Diagnostic on Undeclared Environment Lookup**:
   Querying any environment variable key not in the canonical compiler-controlled set or `[build].env_allowlist` during `comptime` or `[[build_tool]]` execution is rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "sandbox_env_violation"`, `data.var_name`).
4. **Host `PATH` Poisoning Defense (`tasks/0772 §550.37, #65`, `INV-BOOT-003`)**:
   `PATH` inside the sandbox is empty (`""`). The compiler never searches host `PATH` for `gcc`, `clang`, `cl.exe`, `link.exe`, `ld`, `lld`, `as`, `ar`, `lipo`, `python`, or `sh`.

### AXS-HERM-014 — Deterministic Virtual Clock (`ClockPolicy.Frozen`) & Seeded Entropy (`RandomPolicy.Deterministic`) (`REQ-PKG-022`, `tasks/0590 §11–§12, ABUILD-05`, `tasks/0772 §550.6, #66–67`, `T863`)

1. **`ClockPolicy` (`tasks/0590 §11`)**:
   `BuildSandbox` supports four clock modes: `Frozen` (default), `Deterministic`, `Denied`, and `HostTime` (forbidden in hermetic/reproducible builds).
   - Under the default `ClockPolicy.Frozen`, the virtual wall clock is pinned to `SOURCE_DATE_EPOCH = 0` (`1970-01-01T00:00:00Z`, or the explicit integer seconds value configured via `--source-date-epoch <sec>` and hashed into `HermeticBuildFingerprint`).
   - Under `ClockPolicy.Deterministic`, logical build ticks advance by `+1 ns` per deterministic AST/MIR step count, never from hardware `RDTSC` or OS monotonic/wall clocks.
   - Any direct attempt by a `comptime` function or `[[build_tool]]` to query unvirtualized host wall-clock time is rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "sandbox_clock_or_rng_violation"`, `data.source = "host_clock"`).
2. **`RandomPolicy` (`tasks/0590 §12`)**:
   - In hermetic builds, `RandomPolicy` is `Deterministic(seed)` where the 256-bit ChaCha20 PRNG seed is derived deterministically from:
     $$\text{seed} = \text{BLAKE3\_256}(\texttt{"AXIOM-BUILD-RNG-v1\textbackslash0"} \,\|\, \text{PackageIdentityHash} \,\|\, \text{CompilationUnitId} \,\|\, \text{u64\_le}(\text{explicit\_seed}))$$
   - Calling non-deterministic OS entropy (`SecureRandom` / `BCryptGenRandom` / `/dev/urandom` / `RDRAND`) during compilation, `comptime`, or `[[build_tool]]` execution is rejected in hermetic mode with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "sandbox_clock_or_rng_violation"`, `data.source = "nondeterministic_rng"`).

### AXS-HERM-015 — Subprocess & External Tool Execution Lockdown (`ProcessPolicy.Denied`) (`tasks/0590 §13–§16, ABUILD-08..09`, `T863`)

1. By default, `ProcessPolicy = Denied` across all compilation and `[[build_tool]]` units.
2. Any attempt by a `[[build_tool]]` or plugin to spawn a child OS process (`CreateProcessW`, `posix_spawn`, `fork`/`exec`, `system`) when `ExecuteTool` has not been explicitly granted in `[trust.policy]` and pinned by `ToolIdentity.executable_sha256` (`AXS-HERM-004`) is intercepted and rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "sandbox_process_violation"`, `data.program`).

---

## 3. Cross-Directory & Cross-Machine Bit-for-Bit Reproducibility Contract (`AXS-HERM-020`..`023`)

### AXS-HERM-020 — Canonical Path Prefix Remapping (`--remap-path-prefix` & Virtual Mount Prefixes, `REQ-PKG-022`, `tasks/0590 §28`, `tasks/0661 §5.1, §23`, `T863`)

1. **Mandatory Path Prefix Remapping (`compiler/build/repro`)**:
   To ensure that checking out and building a workspace in `D:\work\proj_a` on Machine 1 and `/home/ci/builds/job_99/proj_b` on Machine 2 produces bit-for-bit identical binaries, debug tables, `.axmi`/`.axmeta` interfaces, and `.axpkg` archives (`REQ-PKG-022`), `compiler/build/repro` normalizes every file path before it is interned into `CompilerDB` display spans, panic `Location` strings (`file!()`), `.debug_line` / DWARF `DW_AT_comp_dir` & `DW_AT_name` strings, COFF/PE CodeView symbols, or `.axmeta` provenance records:
   - All path separators `\` are converted to forward slashes `/`.
   - Default virtual prefix table (applied in longest-prefix-first order):
     1. `<pkg_abs_root>/` (for any workspace member or dependency package `<ns>/<name>@<ver>`) $\longrightarrow$ `@pkg/<ns>/<name>@<ver>/` (or `@pkg/<name>@<ver>/` when `ns == "default"`);
     2. `<workspace_abs_root>/` (for workspace-level files outside a member package) $\longrightarrow$ `@ws/`;
     3. `<std_abs_root>/` (standard library root) $\longrightarrow$ `@std/`;
     4. `.axiom/target/<env>/<profile>/gen/<pkg_id>/` (generated sources) $\longrightarrow$ `@gen/<ns>/<name>@<ver>/`;
     5. `.axiom/target/` (build artifact directory) $\longrightarrow$ `@out/`.
   - User-specified `--remap-path-prefix <old_prefix>=<new_prefix>` CLI flags (and `[build].remap_path_prefixes` in `axiom.toml`) are evaluated in longest-`<old_prefix>`-first order prior to the built-in table.
2. **Post-Link Host-Path Leakage Audit (`INV-DET-002`, `REQ-PKG-022`)**:
   In `--hermetic` and `--verify-repro` modes, `compiler/build/repro` scans all emitted artifact bytes (`.obj`, `.o`, `.lib`, `.a`, `.axlib`, `.axmi`, `.axmeta`, `.axpkg`, `.exe`, ELF, Mach-O, `.wasm`) for the literal UTF-8 and UTF-16LE byte sequences of `<workspace_abs_root>`, `<std_abs_root>`, and host `USERPROFILE`/`HOME`. If any unremapped host path byte sequence is found in an emitted artifact, the build fails with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "repro_host_path_leak"`, `data.artifact`, `data.leaked_path`).

### AXS-HERM-021 — Deterministic Symbol, Section, Relocation, Debug & Archive Ordering (`REQ-PKG-022`, `tasks/0590 §25–§28, ABUILD-16, ABUILD-25`, `SPEC-23`, `SPEC-26`, `SPEC-27`, `SPEC-89`, `T863`)

1. **Two Reproducibility Levels (`tasks/0590 §25, ABUILD-25`)**:
   - **Level 1 (Semantic Reproducibility)**: Identical `.axmi` `SemanticInterfaceFingerprint`, `AbiFingerprint`, exported symbol set, and observable program semantics.
   - **Level 2 (Bit-for-Bit Binary Reproducibility — Default for Axiom)**: Byte-for-byte identical output files (`SHA-256(Artifact_A) == SHA-256(Artifact_B)`).
2. **Elimination of All Compiler & Linker Nondeterminism (`tasks/0590 §26–§28`)**:
   `compiler/` and `std/pkg/` enforce canonical ordering across every stage:
   - **Hash tables & sets**: Iteration over `HashMap` / `HashSet` in `kernel/` and `std.collections` follows deterministic insertion order (`INV-KERN-007`), and all cross-module or cross-worker collections are explicitly sorted by canonical `(PackageIdentity, ModulePath, ItemName)` before emission.
   - **Parallel compilation invariance (`tasks/0590 §27, ABUILD-16`, `SPEC-23`)**: `BuildGraph` actions and per-CGU codegen tasks may execute concurrently on `--jobs <N>` threads, but CGU partitioning, symbol table indices, string-literal labels (`.Lstr.<fn>.<k>`), panic labels (`.Lpanic.<n>`), monomorphization instance ordering, and linker input order are determined purely by the canonical sorted DAG topology (`--jobs 1` produces the exact same bytes as `--jobs N`).
   - **Section, relocation & unwind ordering**: Object writers (`COFF`, `ELF64`, `Mach-O 64`, `.wasm`) emit sections in fixed canonical order, sort symbol tables and COMDAT groups by mangled symbol name (`memcmp`), and emit `.pdata`/`.xdata`/`.eh_frame` unwind records in ascending function RVA order (`SPEC-27`, `SPEC-80..91`).
   - **Zeroed timestamps & deterministic build IDs**: All COFF/PE `TimeDateStamp` fields, archive member `mtime`/`uid`/`gid` headers (`CoffAr`, `GnuAr`, `BsdAr`, `.axlib`, `.axpkg`), and DWARF/CodeView timestamps are set to `0` (`INV-DET-002`). Build UUIDs (`LC_UUID`, ELF `.note.gnu.build-id`, PE debug GUID) are derived as `BLAKE3_128("AXIOM-BUILD-ID-v1\0" || NormalizedImageBytes)` rather than random UUIDv4 values.

### AXS-HERM-022 — Canonical 12-Component `HermeticBuildFingerprint` (`tasks/0590 §18, §38`, `tasks/0772 §550.3, §550.11`, `T863`)

Every hermetic build unit computes a domain-separated 256-bit SHA-256 `HermeticBuildFingerprint`:
$$\text{HermeticBuildFingerprint} = \text{SHA256}\!\left(\texttt{"AXHERM-FP-v1\textbackslash0"} \,\|\, C_1 \,\|\, C_2 \,\|\, \dots \,\|\, C_{12}\right)$$
where the 12 canonical components are:
1. $C_1$ (`CompilerSemanticVersion`): UTF-8 version string + schema revision;
2. $C_2$ (`CompilerBinarySha256`): 32-byte SHA-256 digest of the active `axiomc` executable;
3. $C_3$ (`LanguageEdition`): UTF-8 edition string (`"2026"`);
4. $C_4$ (`TargetFingerprint`): 16-byte `TargetFingerprint` (`SPEC-81`) + enabled `CpuFeatureMask`;
5. $C_5$ (`SdkFingerprint`): 32-byte `SysrootFingerprint` / `SDKManifest` digest (`SPEC-88`);
6. $C_6$ (`SourceMerkleRoot`): 32-byte SHA-256 Merkle root of the package's normalized `/source` files (`SPEC-112 AXS-REG-012`);
7. $C_7$ (`DependencyLockGraphHash`): 32-byte `graph_hash` from `axiom.lock` + direct dependency `SemanticInterfaceFingerprint`s;
8. $C_8$ (`FeatureSetHash`): 32-byte BLAKE3/SHA-256 digest of sorted active feature names;
9. $C_9$ (`ComptimeInputsDigest`): 32-byte digest of all `@include_bytes`/`@include_str` and `comptime` input constants;
10. $C_{10}$ (`BuildToolInputsDigest`): 32-byte digest of `[[build_tool]]` binary hashes, `ToolIdentity` records, and generated output provenance;
11. $C_{11}$ (`ProfileConfigDigest`): 32-byte digest of `opt_level`, `lto`, `panic`, `safety_profile`, `debug_info`, `overflow_checks`, and `--remap-path-prefix` rules;
12. $C_{12}$ (`DeclaredEnvDigest`): 32-byte digest of sorted `[build].env_allowlist` `(key, value)` pairs and `SOURCE_DATE_EPOCH`.

### AXS-HERM-023 — Double-Build Reproducibility Verifier (`axiomc build --verify-repro` & `axiomc verify-repro`, `REQ-PKG-022`, `tasks/0590 §25, §48–§49`, `tasks/0772 §550.11–§550.12`, `T863`)

1. **Differential Perturbation Protocol (`compiler/build/repro`)**:
   When `axiomc build --verify-repro` or `axiomc verify-repro` is invoked:
   - **Run 1 (`Build_A`)**: Compiles the workspace in staging directory `<target_dir>/repro_verify/run_a/ws_alpha` with `--jobs 1`, synthetic ambient env `HOST_NOISE="alpha"`, `TZ="UTC"`, `LC_ALL="C"`, and normal file discovery order.
   - **Run 2 (`Build_B`)**: Compiles the same workspace sources + `axiom.lock` in a differently named, deeper directory `<target_dir>/repro_verify/run_b/nested/ws_beta` with `--jobs 4` (or alternate worker count), perturbed ambient env `HOST_NOISE="beta_9999"`, `USERNAME="repro_perturbed_user"`, `TZ="Asia/Ho_Chi_Minh"`, and reversed directory entry buffer order before canonical sorting.
2. **Structured `ReproducibilityResult` & Fail-Closed Verdict (`tasks/0772 §550.12`)**:
   `compiler/build/repro` compares every emitted artifact (`exe`, `lib`, `dll`, `axlib`, `.axmi`, `.axmeta`, `.axpkg`) between `Build_A` and `Build_B`:
   - `ReproStatus.Reproduced`: Both runs succeeded, `HermeticBuildFingerprint_A == HermeticBuildFingerprint_B`, and every output artifact is 100% byte-for-byte identical (`expected_sha256 == observed_sha256`, `size_a == size_b`).
   - `ReproStatus.NotReproduced`: At least one artifact differs in byte length or SHA-256 digest. The verifier locates the exact first differing byte offset, identifies the enclosing container section (`.text`, `.rdata`, `.debug_line`, `SECTION_MERKLE_INDEX`, etc.) and nearest symbol, populates `differences[]`, and emits `AX_DRIVER_BAD_MANIFEST` (`data.kind = "repro_mismatch"`, `data.artifact`, `data.expected_sha256`, `data.found_sha256`, `data.first_diff_offset`, `data.section`).
   - `ReproStatus.Inconclusive`: Either build failed or required inputs were missing. `Inconclusive` is NEVER treated as `Reproduced` (`tasks/0772 §550.12`) and exits with code `1`.


---

## 4. Ed25519 Signing, JSON Provenance Attestation, Transparency Log & Bootstrap Trust (`AXS-HERM-030`..`AXS-HERM-035`)

### AXS-HERM-030 — Ed25519 Package & Toolchain Signing Architecture (`tasks/0590 §33–§36`, `tasks/0772 §550.4, §550.24, §550.32–§550.34`, `SPEC-112 §3`, `T864`)

1. **Strict Separation of Compiler & Signing Keys (`tasks/0772 §550.4, §550.24`)**:
   - The compiler frontend, middle-end, codegen, and linker (`axiomc build`) NEVER hold or access private signing keys during compilation.
   - Cryptographic signing is an explicit, isolated post-build operation executed by `std/pkg/trust` (`axiomc trust sign`, `axiomc pkg publish --sign-key <path>`) using an explicit signing key file or hardware token handle.
2. **Cryptographic Primitive (`Ed25519`, RFC 8032)**:
   - Public keys are 32-byte compressed Edwards25519 points (`pk_bytes: [u8; 32]`); signatures are 64-byte `(R, S)` pairs (`sig_bytes: [u8; 64]`).
   - Verification enforces strict canonical small-order point rejection and $S < L$ malleability rejection (`std.crypto` / `std/pkg/trust`).
   - Every public key is identified by `key_id = HexLower(SHA256("AXKEY-ED25519-v1\0" || pk_bytes)[0..16])` (32 hex characters).
3. **Domain-Separated Package Signature Transcript (`PackageSignature`)**:
   When signing a `.axpkg` archive (`SPEC-112 §3`) or provenance bundle, `std/pkg/trust` signs the canonical domain-separated transcript:
   $$\text{Transcript} = \texttt{"AXIOM-SIG-v1\textbackslash0"} \,\|\, \text{CanonicalEncode}\!\left(\begin{aligned}
   &\text{pkg\_id},\; \text{merkle\_root},\; \text{sif},\; \text{abi\_fp},\\
   &\text{target\_fp},\; \text{lock\_graph\_hash},\; \text{provenance\_sha256},\\
   &\text{signer\_id},\; \text{key\_id},\; \text{signed\_epoch\_sec}
   \end{aligned}\right)$$
   - In a `.axpkg` v1 container, the signature envelope is stored in the optional `SECTION_PROVENANCE` (`section_type = 12`, `SPEC-112 AXS-REG-011`) and recorded in `axiom.lock` (`signature_key_id`, `provenance_digest`) and the registry index entry (`SPEC-112 AXS-REG-020`).
   - Any bit flip in the package's `merkle_root`, `.axmi` `SemanticInterfaceFingerprint`, `AbiFingerprint`, `provenance_sha256`, `signer_id`, or `key_id` invalidates the Ed25519 signature and triggers `AX_DRIVER_BAD_MANIFEST` (`data.kind = "signature_invalid"`, `data.package`, `data.key_id`).

### AXS-HERM-031 — Trust Roots, Key Rotation, Revocation & Transparency Log (`tasks/0590 §34–§36, §50–§51`, `tasks/0772 §550.25–§550.27, §550.33, §550.37`, `T864`)

1. **Workspace Trust Store & Policy Enforcement**:
   - Trusted public keys are configured in `.axiom/trust/roots.toml` or inline in `axiom.toml` `[trust.policy]`:
     - `trusted_signers`: list of `{ signer_id, key_id, public_key_hex, scope = "@ns/*" | "@ns/pkg", valid_from_epoch, expires_epoch }`.
     - `revoked_keys`: list of `{ key_id, revoked_at_epoch, reason }`.
   - When `require_signatures = true`:
     - Unsigned packages fail closed with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "unsigned_package_rejected"`, `data.package`).
     - Packages signed by a `key_id` not matching an active, in-scope `trusted_signers` entry fail with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "untrusted_signer"`, `data.package`, `data.signer_id`, `data.key_id`).
     - Packages signed by a key listed in `revoked_keys` (or expired prior to `signed_epoch_sec`) fail with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "revoked_signing_key"`, `data.package`, `data.key_id`).
2. **Cryptographic Key Rotation (`KeyRotationCert`, `tasks/0772 §550.37`)**:
   - Key rotation requires a dual-signed `KeyRotationCert` containing `(signer_id, old_key_id, new_key_id, new_public_key_hex, effective_epoch)` signed by BOTH `old_key_id` (proving authorization from the previous trust anchor) and `new_key_id` (proving possession of the new private key) over domain tag `"AXIOM-KEY-ROTATE-v1\0"`.
3. **Append-Only Transparency Hash Chain (`ArtifactLog`, `tasks/0590 §36`)**:
   - Registry mirrors and local `.axiom/trust/transparency.log` maintain an append-only hash chain of published package/provenance records:
     $$H_0 = 0^{32}, \qquad H_n = \text{SHA256}\!\left(\texttt{"AXLOG-v1\textbackslash0"} \,\|\, H_{n-1} \,\|\, \text{CanonicalBytes}(\text{LogEntry}_n)\right)$$
   - `axiomc trust verify` and `axiomc audit` verify that every entry's `prev_entry_hash` equals $H_{n-1}$ and that no historical `(pkg_id, merkle_root, key_id)` entry has been mutated or equivocated.

### AXS-HERM-032 — Toolchain & Target SDK Identity Verification (`tasks/0590 §31`, `tasks/0772 §550.29–§550.31`, `SPEC-88`, `T864`)

1. **`ToolchainIdentity` & `CompilerFingerprint`**:
   - Every `axiomc` installation carries a `ToolchainIdentity` manifest (`toolchain.axtrust.toml`) recording `compiler_version`, `host_target`, `compiler_binary_sha256`, `std_source_merkle_root`, `runtime_archive_sha256`, and an optional official release Ed25519 signature (`AXIOM-TOOLCHAIN-SIG-v1\0`).
2. **`SdkFingerprint` & Sysroot Integrity (`SPEC-88`)**:
   - Target sysroots (`SDKManifest` in `SPEC-88`) record exact SHA-256 digests for all startup objects (`crt1.o`, `crti.o`), import libraries (`.lib`, `.tbd`, `.so` stubs), and linker scripts.
   - Before linking in `--hermetic` mode or when `[trust.policy].expected_sdk_fingerprint` is set, `axiomc` verifies that the active SDK digest matches the pinned `SdkFingerprint`; any mismatch emits `AX_DRIVER_BAD_MANIFEST` (`data.kind = "sdk_integrity_mismatch"`, `data.expected`, `data.found`).

### AXS-HERM-033 — JSON Build Provenance Attestation Manifest (`.axprov.json`, `tasks/0590 §37–§40`, `tasks/0772 §550.35–§550.36`, `SPEC-112 §3`, `T864`)

1. **Provenance Orthogonality Rule (`tasks/0772 §550.4, §550.35`)**:
   - Build provenance is an external attestation artifact (`.axprov.json` alongside build outputs, or embedded inside `.axpkg` `SECTION_PROVENANCE` `section_type = 12`).
   - Provenance metadata MUST NEVER be injected into `.axmi` (`SemanticInterfaceFingerprint`), `.axmeta`, or compiled machine code sections (`.text`, `.rdata`), preserving 100% invariance of compilation outputs with respect to builder identity or signing time.
2. **Canonical `.axprov.json` Schema (`schema = "axiom.provenance.v1"`)**:
   `std/pkg/trust` emits and parses deterministic JSON (UTF-8, keys sorted lexicographically, no insignificant whitespace in canonical digest form) with the following mandatory fields:
   ```json
   {
     "schema": "axiom.provenance.v1",
     "package": {
       "namespace": "acme",
       "name": "crypto_hash",
       "version": "1.2.0",
       "source_merkle_root": "sha256:<64-hex>"
     },
     "builder": {
       "builder_id": "ci.acme.internal/runner-linux-x64",
       "invocation_mode": "hermetic",
       "sandbox_profile": "hermetic.v1"
     },
     "toolchain": {
       "compiler_version": "0.1.0",
       "compiler_fingerprint": "sha256:<64-hex>",
       "sdk_fingerprint": "sha256:<64-hex>",
       "target_triple": "x86_64-unknown-linux-gnu",
       "target_fingerprint": "<32-hex>"
     },
     "inputs": {
       "lockfile_sha256": "sha256:<64-hex>",
       "lock_graph_hash": "sha256:<64-hex>",
       "hermetic_build_fingerprint": "sha256:<64-hex>",
       "features": ["simd", "std"],
       "remap_rules": ["@pkg/acme/crypto_hash@1.2.0/", "@std/", "@out/"]
     },
     "capabilities": {
       "declared": ["unsafe"],
       "reachable_Closure": ["unsafe"]
     },
     "outputs": [
       {
         "name": "libcrypto_hash.axlib",
         "kind": "axlib",
         "size": 18432,
         "sha256": "sha256:<64-hex>",
         "sif": "<32-hex>",
         "abi_fingerprint": "<32-hex>"
       }
     ],
     "signature": {
       "algorithm": "ed25519",
       "signer_id": "release@acme.example",
       "key_id": "<32-hex>",
       "signed_epoch_sec": 1700000000,
       "sig_hex": "<128-hex>"
     }
   }
   ```
3. **Provenance Verification (`axiomc trust verify` / `axiomc provenance verify`)**:
   - Recomputes `sha256` and `size` of every file listed in `outputs[]`, verifies `source_merkle_root`, `lockfile_sha256`, `lock_graph_hash`, and `hermetic_build_fingerprint` against the workspace or `.axpkg`, and verifies `signature.sig_hex` using the Ed25519 public key for `signature.key_id`.
   - Any digest mismatch between `.axprov.json` and the actual artifact bytes or lockfile fails closed with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "provenance_mismatch"`, `data.artifact`, `data.expected`, `data.found`).

### AXS-HERM-034 — Remote Build Cache & Distributed Worker Zero-Trust Verification (`tasks/0590 §29–§30`, `tasks/0772 §550.47–§550.56`, `SPEC-110 §6`, `T863`, `T864`)

1. **Never Trust Unverified Remote Cache Hits (`tasks/0772 §550.53–§550.54`)**:
   - Action cache entries in `.axiom/cache/` or a remote cache are indexed by `HermeticBuildFingerprint` (`AXS-HERM-022`).
   - Before materializing a cached artifact into `/output`, the build engine verifies:
     1. Exact match of all 12 `HermeticBuildFingerprint` components;
     2. Recomputed `SHA-256` of every artifact blob matches the manifest digest;
     3. When `[trust.policy].require_signed_cache = true`, a valid Ed25519 signature from a trusted builder key over the cache entry's `.axprov.json`.
   - Corrupt or untrusted remote cache entries are quarantined and either rejected (`--offline` / `--require-signed-cache`) or locally rebuilt and cross-checked against the local `HermeticBuildFingerprint`.
2. **Secret Redaction in Provenance, Logs & Crash Bundles (`tasks/0772 §550.46`)**:
   - `.axprov.json`, build logs, and `AX_ICE_*` crash reproduction bundles NEVER include raw ambient host environment variables, registry bearer tokens (`AXIOM_REGISTRY_TOKEN`), private key paths/bytes, or unremapped host user paths.

### AXS-HERM-035 — Diverse Double-Compilation (DDC) Bootstrap Trust Verification (`tasks/0449 §190.5`, `tasks/0590 §32`, `tasks/0772 §550.13–§550.18, §550.74`, `BOOTSTRAP.md §4`, `T864`)

1. **Defense Against Reflections on Trusting Trust (`tasks/0772 §550.13–§550.16`)**:
   To defeat self-propagating compiler backdoors in the `axiom0` $\longrightarrow$ Stage 1 $\longrightarrow$ Stage 2 $\longrightarrow$ Stage 3 self-hosting bootstrap chain (`BOOTSTRAP.md`), `std/pkg/trust` specifies the **Diverse Double-Compilation (DDC)** verification protocol:
   - Given identical Axiom compiler sources $S_{\text{compiler}}$, pinned `axiom.lock`, and hermetic `BuildSandbox` configuration:
     - Path A compiles $S_{\text{compiler}}$ using seed compiler $C_A$ (e.g., independent bootstrap implementation or host Toolchain A) to produce Stage-1 binary $C_{1A}$, which then compiles $S_{\text{compiler}}$ to produce Stage-2 binary $C_{2A}$.
     - Path B compiles $S_{\text{compiler}}$ using an independent seed compiler $C_B$ (or distinct bootstrap chain) to produce Stage-1 binary $C_{1B}$, which then compiles $S_{\text{compiler}}$ to produce Stage-2 binary $C_{2B}$.
     - Stage-2 binary $C_{2A}$ compiles $S_{\text{compiler}}$ to produce Stage-3 binary $C_3$.
   - **DDC Fixed-Point Invariant**:
     $$\text{SHA256}(C_{2A}) == \text{SHA256}(C_{2B}) == \text{SHA256}(C_3)$$
   - If $\text{SHA256}(C_{2A}) \neq \text{SHA256}(C_{2B})$ or $\text{SHA256}(C_{2A}) \neq \text{SHA256}(C_3)$, `axiomc trust verify --ddc` fails closed with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "ddc_mismatch"`, `data.stage2_a_sha256`, `data.stage2_b_sha256`, `data.stage3_sha256`).
2. **Standalone Minimal Trust Verifier (`tasks/0772 §550.74`)**:
   - The core Ed25519 signature, SHA-256 Merkle root, `.axprov.json` digest, and DDC hash comparison logic in `std/pkg/trust` is self-contained with zero dependency on compiler middle-end/codegen internals so that auditing a release bundle requires only a minimal, easily inspectable verification kernel.

---

## 5. CLI Surface, Diagnostics, Canonical Examples & Verification Matrix (`AXS-HERM-040`..`AXS-HERM-053`)

### AXS-HERM-040 — CLI Subcommands (`axiomc build`, `axiomc verify-repro`, `axiomc trust`, `axiomc audit`, `axiomc provenance`, `tasks/0590 §48–§53`, `T863`, `T864`)

`compiler/driver` and `compiler/driver/trust_cmd` expose the following deterministic CLI commands and flags (supporting `--error-format=human|json|short`):

1. **Hermetic & Reproducible Build Flags (`T863`)**:
   - `axiomc build --hermetic` — enforces strict `BuildSandbox` isolation (`AXS-HERM-010`..`AXS-HERM-015`), canonical `--remap-path-prefix` (`AXS-HERM-020`), and post-link host-path leak scanning.
   - `axiomc build --remap-path-prefix <old>=<new>` — adds an explicit canonical path prefix mapping.
   - `axiomc build --verify-repro` / `axiomc verify-repro [--jobs-a 1 --jobs-b 4]` — executes the 2-run differential perturbation reproducibility check (`AXS-HERM-023`) and emits a structured `ReproducibilityResult` report.
   - `axiomc build --provenance <out.axprov.json>` — emits the canonical `.axprov.json` build provenance manifest (`AXS-HERM-033`).
2. **Supply-Chain Trust & Signing Commands (`T864`)**:
   - `axiomc trust keygen --signer <id> --out-dir <dir>` — deterministically or cryptographically generates an Ed25519 keypair (`<key_id>.secret`, `<key_id>.pub`) and prints the `[trust.policy].trusted_signers` TOML stanza.
   - `axiomc trust sign <artifact_or_axpkg> --key <secret_key_path> [--provenance <path>]` — signs a `.axpkg` package or `.axprov.json` provenance manifest using Ed25519 (`AXS-HERM-030`).
   - `axiomc trust verify <artifact_or_axpkg> [--provenance <path>] [--ddc <stage2a> <stage2b> <stage3>]` — verifies Ed25519 signatures, trust-root membership, key revocation status, `.axprov.json` artifact SHA-256 digests, and optional DDC bootstrap fixed-point equality (`AXS-HERM-030`..`AXS-HERM-035`).
   - `axiomc trust rotate --old-key <path> --new-key <path> --out <cert.toml>` — emits a dual-signed `KeyRotationCert` (`AXS-HERM-031`).
   - `axiomc audit [--capabilities] [--signatures] [--provenance]` — audits the entire resolved dependency graph in `axiom.lock` against `[trust.policy]`, reporting transitive capability closure (`REQ-PKG-024`), signature coverage, transparency log continuity, and any capability escalation or trust violations (`AXS-HERM-002`..`AXS-HERM-004`, `AXS-HERM-031`).
   - `axiomc provenance emit|verify|inspect <target>` — generates, validates, or inspects `.axprov.json` attestation manifests (`AXS-HERM-033`).

### AXS-HERM-050 — Diagnostic Mapping Table (`spec/diagnostics.md`, `T863`, `T864`)

Per `spec/diagnostics.md` `AXD-010` and `AXD-021`, E20.4 introduces no new diagnostic area; all hermetic sandbox, reproducibility, capability-escalation, signing, and provenance failures map to existing canonical diagnostic codes with structured `data.kind` discriminants:

| Failure Condition | Canonical Diagnostic Code | Structured `data.kind` / Fields | Spec Rule |
|---|---|---|---|
| Package source uses `unsafe` / `ffi` / `asm` / `net` / `fs` / `process` without declaring it in `[capabilities]` | `AX_DRIVER_BAD_MANIFEST` (plus `AX_SEC_UNSAFE_FORBIDDEN` / `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN` at item span) | `kind = "undeclared_package_capability"`, `package`, `capability`, `span` | `AXS-HERM-002` |
| Dependency requests capability not granted by root `[trust.policy]` (`REQ-PKG-024`) | `AX_DRIVER_BAD_MANIFEST` | `kind = "capability_escalation_denied"`, `package`, `capability`, `policy_source`, `dependency_chain` | `AXS-HERM-003` |
| `[[build_tool]]` writes outside `/build` or emits undeclared file | `AX_DRIVER_BAD_MANIFEST` | `kind = "undeclared_build_output"`, `package`, `tool`, `path` | `AXS-HERM-004` |
| Read/write outside allowed sandbox roots, write to `/source` or `/dependencies`, or symlink/junction escape (`REQ-PKG-022`) | `AX_DRIVER_BAD_MANIFEST` | `kind = "sandbox_fs_violation"`, `operation`, `requested_path`, `resolved_path`, `reason` | `AXS-HERM-011` |
| Socket/DNS/HTTP access attempted during compilation, `comptime`, or `[[build_tool]]` (`REQ-PKG-022`) | `AX_DRIVER_BAD_MANIFEST` (or `AX_CTM_CAPABILITY_DENIED` inside `comptime`) | `kind = "sandbox_net_violation"`, `phase`, `operation`, `endpoint` | `AXS-HERM-012` |
| Undeclared host environment variable read inside hermetic build | `AX_DRIVER_BAD_MANIFEST` | `kind = "sandbox_env_violation"`, `var_name`, `package` | `AXS-HERM-013` |
| Wall-clock time or OS CSPRNG queried inside hermetic build | `AX_DRIVER_BAD_MANIFEST` | `kind = "sandbox_clock_or_rng_violation"`, `primitive`, `package` | `AXS-HERM-014` |
| Unregistered or forbidden child process spawn inside hermetic build | `AX_DRIVER_BAD_MANIFEST` | `kind = "sandbox_process_violation"`, `executable`, `package` | `AXS-HERM-015` |
| Unremapped host absolute path found in emitted binary/metadata (`REQ-PKG-022`) | `AX_DRIVER_BAD_MANIFEST` | `kind = "repro_host_path_leak"`, `artifact`, `leaked_path` | `AXS-HERM-020` |
| Double-build `--verify-repro` produces differing artifact bytes (`REQ-PKG-022`) | `AX_DRIVER_BAD_MANIFEST` | `kind = "repro_mismatch"`, `artifact`, `expected_sha256`, `found_sha256`, `first_diff_offset`, `section` | `AXS-HERM-023` |
| Invalid Ed25519 signature over `.axpkg` or `.axprov.json` | `AX_DRIVER_BAD_MANIFEST` | `kind = "signature_invalid"`, `package`, `key_id` | `AXS-HERM-030` |
| Package is unsigned when `require_signatures = true` | `AX_DRIVER_BAD_MANIFEST` | `kind = "unsigned_package_rejected"`, `package` | `AXS-HERM-031` |
| Signer `key_id` is not in `[trust.policy].trusted_signers` or out of scope | `AX_DRIVER_BAD_MANIFEST` | `kind = "untrusted_signer"`, `package`, `signer_id`, `key_id` | `AXS-HERM-031` |
| Signer `key_id` is listed in `revoked_keys` or expired | `AX_DRIVER_BAD_MANIFEST` | `kind = "revoked_signing_key"`, `package`, `key_id` | `AXS-HERM-031` |
| Target sysroot/SDK digest does not match pinned `SdkFingerprint` | `AX_DRIVER_BAD_MANIFEST` | `kind = "sdk_integrity_mismatch"`, `expected`, `found` | `AXS-HERM-032` |
| `.axprov.json` digest or lockfile binding does not match artifact bytes | `AX_DRIVER_BAD_MANIFEST` | `kind = "provenance_mismatch"`, `artifact`, `expected`, `found` | `AXS-HERM-033` |
| DDC Stage-2A / Stage-2B / Stage-3 compiler binary hashes diverge | `AX_DRIVER_BAD_MANIFEST` | `kind = "ddc_mismatch"`, `stage2_a_sha256`, `stage2_b_sha256`, `stage3_sha256` | `AXS-HERM-035` |

### AXS-HERM-051 — Positive Canonical Examples

1. **Workspace `axiom.toml` with Explicit Capability Grants, Trust Roots & Hermetic Sandbox Policy**:
   ```toml
   [package]
   name = "acme/payment_gateway"
   version = "1.0.0"
   edition = "2026"

   [capabilities]
   unsafe = false
   ffi = false
   net = true
   fs = false
   process = false
   asm = false

   [build]
   hermetic = true
   source_date_epoch = 0
   env_allowlist = ["PAYMENT_SCHEMA_VERSION"]
   remap_path_prefixes = [
     { from = "/opt/ci/runners/slot_42", to = "@ci" }
   ]

   [trust.policy]
   default_max_capabilities = []
   require_signatures = true
   require_provenance = true
   reject_undeclared_capabilities = true

   [trust.policy.package_grants]
   "acme/payment_gateway@1.0.0" = ["net"]
   "std/crypto_sys@1.4.2" = ["unsafe", "asm"]

   [[trust.policy.trusted_signers]]
   signer_id = "release@axiom-lang.org"
   key_id = "8f4b2e19c0a3d5716e2049b8a1c3f7e2"
   public_key_hex = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
   scope = "@std/*"
   ```
2. **Hermetic Sandbox Execution, Path Remapping, Reproducibility Verification & Provenance Attestation in Canonical Axiom (`=` and `.` syntax)**:
   ```axiom
   module app.verify_hermetic

   import std.pkg.trust.{
       CapabilitySet, PackageCapability, TrustPolicy, Ed25519KeyPair,
       ProvenanceManifest, sign_provenance, verify_provenance, audit_capability_closure
   }
   import compiler.build.sandbox.{BuildSandbox, SandboxConfig, SandboxPathKind}
   import compiler.build.repro.{PathRemapper, verify_reproducible_build, ReproStatus}

   pub fn run_hermetic_pipeline(
       ws_alpha: Str,
       ws_beta: Str,
       policy: TrustPolicy,
       keypair: Ed25519KeyPair
   ) -> Result[ProvenanceManifest, Str] {
       // 1. Audit transitive dependency capability closure (REQ-PKG-024)
       audit_res = audit_capability_closure(policy)
       if !audit_res.is_allowed() {
           return Result.Err(audit_res.violation_reason)
       }

       // 2. Verify canonical path prefix remapping (REQ-PKG-022)
       remapper = PathRemapper.for_workspace(ws_alpha, "acme/payment_gateway", "1.0.0")
       mapped_src = remapper.remap_path(ws_alpha.concat("/src/main.ax"))
       // mapped_src == "@pkg/acme/payment_gateway@1.0.0/src/main.ax"

       // 3. Run double-build reproducibility check across distinct directories
       repro = verify_reproducible_build(ws_alpha, ws_beta)
       match repro.status {
           ReproStatus.Reproduced => {},
           _ => return Result.Err("bit-for-bit reproducibility check failed")
       }

       // 4. Sign and verify JSON provenance attestation manifest
       prov = ProvenanceManifest.from_build(repro.fingerprint, keypair.signer_id)
       signed_prov = sign_provenance(prov, keypair)
       verified = verify_provenance(signed_prov, policy)
       if !verified {
           return Result.Err("provenance signature verification failed")
       }
       return Result.Ok(signed_prov)
   }
   ```

### AXS-HERM-052 — Negative Canonical Examples

1. **Rejected Transitive Capability Escalation (`REQ-PKG-024`, `AXS-HERM-003`)**:
   - Package `acme/json_fmt@0.3.1` is a transitive formatting utility whose manifest declares `capabilities = { ffi = true, net = true }`, while the root workspace `[trust.policy]` sets `default_max_capabilities = []` and grants no override for `acme/json_fmt@0.3.1`.
   - Running `axiomc build` or `axiomc audit` rejects the build before compilation begins:
     ```text
     error[AX_DRIVER_BAD_MANIFEST]: capability escalation denied for dependency `acme/json_fmt@0.3.1`
       --> axiom.toml:22:1
        |
        = note: kind = "capability_escalation_denied"
        = note: dependency chain: `acme/payment_gateway@1.0.0 -> acme/log_sink@1.1.0 -> acme/json_fmt@0.3.1`
        = note: requested capabilities `["ffi", "net"]` exceed root `[trust.policy]` grant `[]`
        = help: remove the untrusted dependency or explicitly grant `"acme/json_fmt@0.3.1" = ["ffi", "net"]` in `[trust.policy.package_grants]`
     ```
2. **Rejected Sandbox Filesystem Escape & Network Access During Compilation (`REQ-PKG-022`, `AXS-HERM-011`, `AXS-HERM-012`)**:
   ```axiom
   module malicious.build_hook

   // ERROR: attempting to read outside `/source` via parent traversal in comptime
   const STOLEN_KEYS: [u8] = @include_bytes("../../../../etc/passwd")
   // -> emits AX_DRIVER_BAD_MANIFEST (data.kind = "sandbox_fs_violation", reason = "path_escape_outside_source")
   ```
   Similarly, any `[[build_tool]]` or `comptime` evaluation attempting to open a TCP socket or write to `/source/generated.ax` is immediately terminated and rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "sandbox_net_violation"` or `"sandbox_fs_violation"`).
3. **Rejected Tampered Provenance or Untrusted Signer (`AXS-HERM-030`, `AXS-HERM-031`, `AXS-HERM-033`)**:
   - If a `.axpkg` archive's payload bytes are modified after signing or its `.axprov.json` `outputs[0].sha256` does not match the compiled `.axlib`, `axiomc trust verify` fails closed with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "signature_invalid"` or `"provenance_mismatch"`).

### AXS-HERM-053 — E20.4 Implementation & Verification Matrix (`T863`..`T865`)

| Task ID | Owner | Deliverables | Spec Rules | Invariant | Verification Path |
|---|---|---|---|---|---|
| `T863` | `axiom-backend` | `compiler/build/sandbox`, `compiler/build/repro`, `tests/run/build_hermetic` | `AXS-HERM-010`..`AXS-HERM-023`, `AXS-HERM-040` | `INV-HERM-001` | `tests/run/build_hermetic` |
| `T864` | `axiom-stdlib` | `std/pkg/trust`, `compiler/driver/trust_cmd`, `tests/run/pkg_supply_chain` | `AXS-HERM-001`..`AXS-HERM-004`, `AXS-HERM-030`..`AXS-HERM-040` | `INV-HERM-002` | `tests/run/pkg_supply_chain` |
| `T865` | `axiom-qa` | `tests/conformance/p20/e20_4_hermetic_supply_chain` | `AXS-HERM-001`..`AXS-HERM-053` | `INV-HERM-003` | `tests/conformance/p20/e20_4_hermetic_supply_chain` |

## Sources

- `REQ-PKG-022` (Hermetic and reproducible build sandbox: read-only source, confined build outputs, zero network access, sanitized env, canonical path remapping, bit-for-bit identical binaries across directories/machines)
- `REQ-PKG-024` (Supply-chain trust model and capability auditing: `Safe ≠ Trusted`, package capability declarations, transitive dependency trust policy, capability escalation rejection)
- `docs/base/tasks/0590 - BOOTSTRAP-331 - AXIOM BUILD SANDBOX, HERMETIC BUILD & SUPPLY-CHAIN TRUST ENGINE.md` (§1–§64, rules `ABUILD-01`..`ABUILD-26`)
- `docs/base/tasks/0449 - BOOTSTRAP-190 - Security, Sandboxing, Supply Chain & Trust Model.md` (§190.1–§190.6)
- `docs/base/tasks/0772 - BOOTSTRAP-550 - SECURE COMPILER, SUPPLY-CHAIN HARDENING, COMPILER SELF-PROTECTION, TRUSTED BUILD, SIGNED TOOLCHAIN & MALICIOUS COMPILER DEFENSE.md` (§550.1–§550.90)
- `docs/base/tasks/0661 - BOOTSTRAP-402 - AXIOM DETERMINISTIC COMPILATION, REPRODUCIBLE BUILDS & ARTIFACT FINGERPRINTING.md` (§1–§15)
- `docs/base/tasks/1065 - PHASE39 - CANONICAL LANGUAGE Freeze, GOVERNANCE, RELEASE ENGINEERING, CONFORMANCE GATES & LONG-TERM EVOLUTION CONSTITUTION.md` (§39.1–§39.5)
- `spec/SPEC-23-incremental-query-engine-caching.md`, `spec/SPEC-26-module-metadata-binary-interface.md`, `spec/SPEC-27-object-emission-linker-interface.md`, `spec/SPEC-53-safety-profiles-capability-security.md`, `spec/SPEC-88-target-sdks-sysroots-cross-compilation.md`, `spec/SPEC-110-build-graph-driver.md`, `spec/SPEC-111-package-manager-resolution-lockfiles.md`, `spec/SPEC-112-package-registry-distribution.md`, `spec/BOOTSTRAP.md`, `spec/diagnostics.md`, `spec/invariants.md`
