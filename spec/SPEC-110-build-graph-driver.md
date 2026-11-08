# SPEC-110 — Canonical Build Graph, Declarative `axiom.toml` Workspace & Driver Orchestration

- **Status**: Normative
- **Phase**: P20 (E20.1 — Build Graph, Workspace & Driver Orchestration)
- **Rules**: `AXS-BLD-001` .. `AXS-BLD-053`
- **Requirements**: `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025` (consolidates foundational package/build rules `REQ-PKG-001`..`REQ-PKG-021`)

## Tóm tắt

Đặc tả này quy định kiến trúc chính tắc cho hệ thống dựng (build system), biểu đồ gói và không gian làm việc (`axiom.toml`), bộ lập lịch biểu đồ dựng thực thi dựa trên cơ sở dữ liệu truy vấn biên dịch (`CompilerDB`), phân tách môi trường biên dịch chéo (`Build`/`Host`/`Target`), bộ nhớ đệm dựng định danh theo nội dung đa tầng, và giao diện dòng lệnh điều phối không gian làm việc (`axiomc build|check|run|test|bench|clean|graph`) của Axiom:

1. **Năm tầng cấu trúc độc lập (`AXS-BLD-001`..`AXS-BLD-006`)**: Phân tách rạch ròi giữa `Module` (đơn vị không gian tên và kiểm tra kiểu trong gói), `Package` (đơn vị phân phối có phiên bản ngữ nghĩa, ranh giới hiệu ứng và tính năng), `Workspace` (tập hợp gói địa phương chia sẻ khóa phiên bản, cấu hình dựng và bộ đệm `.axiom/cache`), `DependencyGraph` (đồ thị có hướng không chu trình cấp gói với các phạm vi pha `normal`, `dev`, `build`, `comptime`, `system`), và `BuildGraph` (đồ thị tác vụ biên dịch/liên kết có định danh nội dung). Định danh gói (`PackageIdentity`) độc lập với đường dẫn tệp vật lý; chu trình phụ thuộc giữa các gói bị cấm tuyệt đối, trong khi các mô-đun cùng gói được phép tham chiếu lẫn nhau trong một thành phần liên thông mạnh (SCC).
2. **Tệp kê khai `axiom.toml` thuần khai báo và bất biến ngữ nghĩa (`AXS-BLD-010`..`AXS-BLD-016`)**: `axiom.toml` là định dạng tệp kê khai gói và không gian làm việc chính tắc duy nhất (`ADR-0006`). Tệp kê khai hoàn toàn mang tính khai báo — nghiêm cấm mọi khóa kịch bản mệnh lệnh tùy ý (`script`, `command`, `shell`, `eval`). Tập tính năng (`[features]`) và vị từ `@cfg(...)` phải được giải quyết tất định trước khi đóng băng biểu đồ dựng; hệ thống không bao giờ âm thầm vô hiệu hóa các tính năng bắt buộc và siêu dữ liệu gói không bao giờ làm thay đổi ngầm ngữ nghĩa cốt lõi của ngôn ngữ (`REQ-PKG-025`).
3. **Phân tách `Build`/`Host`/`Target` và hạ tầng `BuildGraph` trên `CompilerDB` (`AXS-BLD-020`..`AXS-BLD-025`)**: Mọi nút trong `BuildGraph` được gắn nhãn rõ ràng với bộ ba đích thực thi (`Host` cho các công cụ `build`/`comptime` hoặc `Target` cho các đơn vị `normal`/`dev`), ngăn chặn tuyệt đối việc trộn lẫn mã máy hoặc siêu dữ liệu ABI giữa máy chủ và máy đích (`SPEC-88`). Sinh mã nguồn tại thời điểm dựng chỉ được thực hiện thông qua các mục tiêu `build-tool` hoặc hàm `comptime` bị giới hạn quyền năng (capability-gated sandbox) với hồ sơ truy vết nguồn gốc (`GeneratedSourceProvenance`).
4. **Bộ nhớ đệm dựng định danh nội dung đa tầng và công bố nguyên tử (`AXS-BLD-030`..`AXS-BLD-035`)**: Tích hợp chặt chẽ với `CompilerDB` (`SPEC-21`) và hệ thống biên dịch khả tăng (`SPEC-22`) qua bốn tầng khóa băm BLAKE3-256 (`SemanticFingerprint`/`InterfaceFingerprint`, `AbiFingerprint`, `CodegenFingerprint`, `BuildFingerprint`). Mọi tạo phẩm đầu ra phải được kiểm tra tính toàn vẹn trước khi tái sử dụng và được ghi thông qua tệp tạm rồi đổi tên nguyên tử (atomic temp-write-then-rename), bảo đảm an toàn khi hủy bỏ (`CancellationToken`) và tính tất định tuyệt đối bất kể số luồng thực thi.
5. **Điều phối trình điều khiển `axiomc` và ánh xạ chẩn đoán (`AXS-BLD-040`..`AXS-BLD-053`)**: Quy định rõ ngữ nghĩa các lệnh con không gian làm việc (`build`, `check`, `run`, `test`, `bench`, `clean`, `graph`), luồng sự kiện JSONL có cấu trúc (`BuildEvent`), đầu ra giải thích lý do dựng lại (`--explain`) và xuất đồ thị (`--format=json|dot`), cùng bảng ánh xạ chẩn đoán chính tắc và ma trận kiểm chứng cho E20.1 (`T851`–`T853`).

---

## 1. Five Structural Layers, Package Identity, and Dependency Scopes

- **AXS-BLD-001 (Five Structural Layers of the Build Architecture)**:
  The Axiom build and package architecture MUST maintain five distinct structural representations (`0168 §2–§5`, `tasks/0356 §3`, `tasks/0372 §3–§4`, `tasks/0661 §3`, `REQ-PKG-001`..`REQ-PKG-004`, `REQ-PKG-022`, `REQ-PKG-024`):
  1. **`Module`**: A compile-time namespace, visibility, and semantic checking unit within a single package (`SPEC-03`). Modules are NOT independent distribution or versioning units (`REQ-PKG-002`).
  2. **`Package`**: The canonical unit of semantic versioning, dependency declaration, feature gating, capability/effect policy boundary, and distributable source/interface/binary packaging (`REQ-PKG-001`, `REQ-PKG-003`, `REQ-PKG-024`).
  3. **`Workspace`**: A local multi-package coordination root governed by a workspace `axiom.toml` that shares a single resolved dependency lock state (`axiom.lock`, `SPEC-111`), build profiles, target directory (`.axiom/target`), and content-addressed artifact cache (`.axiom/cache`) (`REQ-PKG-004`, `REQ-PKG-011`, `REQ-PKG-022`).
  4. **`DependencyGraph`**: The resolved directed acyclic graph (DAG) of package nodes and phase-qualified dependency edges (`normal`, `dev`, `build`, `comptime`, `system`) parameterized by active package features and target configuration predicates (`REQ-PKG-008`, `REQ-PKG-024`, `REQ-PKG-025`).
  5. **`BuildGraph`**: The lower-level executable DAG of fine-grained compilation, interface extraction (`.axmi`/`.axmeta`), code generation (`.obj`/`.o`), archiving (`.lib`/`.a`/`.axlib`), linking, and capability-sandboxed source-generation actions scheduled over `CompilerDB` (`SPEC-21`, `SPEC-22`).

- **AXS-BLD-002 (Canonical Package Identity & Path Independence)**:
  Every resolved package instance MUST be identified by a canonical `PackageIdentity` record (`0168 §12.1`, `tasks/0356 §7`, `tasks/0661 §5.1`, `REQ-PKG-005`..`REQ-PKG-007`, `REQ-PKG-015`..`REQ-PKG-018`):
  ```
  PackageIdentity = {
      name:             PackageName,      // canonical ASCII lowercase identifier ([a-z][a-z0-9_-]*)
      version:          SemVer,           // MAJOR.MINOR.PATCH[-pre][+build] (REQ-PKG-022)
      source_id:        PackageSourceId,  // WorkspaceLocal | PathRelative | GitCommit | RegistryDigest | VendorTree
      feature_set_hash: Digest256,        // BLAKE3-256 of sorted active feature names
      target_env_class: BuildEnvClass,    // Host | Target(TargetTriple)
      abi_salt:         Digest256         // toolchain + ABI/profile salt (SPEC-22, SPEC-88)
  }
  ```
  1. **Path independence (`REQ-PKG-005`, `REQ-PKG-018`)**: Absolute host filesystem paths MUST NOT participate in `PackageIdentity`, symbol mangling, `.axmi`/`.axmeta` metadata hashes, or content-addressed cache keys. Relocation of a workspace on disk MUST preserve all `PackageIdentity` digests.
  2. **Deterministic collision-free disambiguation (`REQ-PKG-006`, `REQ-PKG-007`, `REQ-PKG-015`..`REQ-PKG-017`)**: Every exported symbol, type fingerprint, vtable/descriptor, and module metadata table is namespace-qualified by `PackageIdentity`. When two distinct resolved versions or feature instantiations of a package coexist in the internal dependency graph (where permitted by private linkage rules in `SPEC-111`), their mangled symbol prefixes and `CompilerDB` `PackageId` keys MUST remain deterministically distinct (`tasks/0661 §5.1`).

- **AXS-BLD-003 (Package-Level DAG vs Intra-Package Module SCC Separation)**:
  1. **Inter-package acyclicity (`REQ-PKG-008`)**: The resolved `DependencyGraph` across packages (for any single phase edge class or causal build chain) MUST be a strict directed acyclic graph (DAG). Any package-level dependency cycle (`PkgA -> PkgB -> ... -> PkgA`) MUST be rejected during workspace/dependency graph construction with diagnostic `AX_DRIVER_BAD_MANIFEST` (`data.kind = "package_cycle"`, `data.cycle = "PkgA -> PkgB -> PkgA"`) (`0168 §12.3`, `tasks/0372 §11`, `tasks/0661 §15.5`).
  2. **Intra-package module dependency handling (`REQ-PKG-009`)**: Within a single package, module dependencies are governed by the module import graph (`SPEC-03`). Where intra-package module recursion is rejected by `SPEC-03` (`AX_NAME_IMPORT_CYCLE`), the frontend diagnoses it at module resolution time; where declarations within a compilation unit form mutually recursive type/function SCCs, `CompilerDB` queries evaluate them deterministically at the declaration SCC level (`SPEC-21`) while keeping the enclosing `Package` as a single acyclic node in `DependencyGraph` (`tasks/0356 §12`, `tasks/0661 §6`).

- **AXS-BLD-004 (Package Targets & Compilation Units)**:
  A single package manifest MAY declare multiple compilation targets (`0168 §6.4`, `tasks/0356 §9`, `tasks/0372 §6`):
  - At most one library target (`[lib]`, defaulting to `src/lib.ax` when present), producing `.axmi` interface metadata and static/shared/packaged library artifacts (`lib`, `staticlib`, `cdylib`, `rlib`/`axlib`).
  - Zero or more executable binary targets (`[[bin]]`, defaulting to `src/main.ax` when present), producing native or WebAssembly executables (`bin`).
  - Zero or more test targets (`tests/*.ax` or inline `@test` harnesses compiled in test mode), benchmark targets (`benches/*.ax`), example targets (`examples/*.ax`), and capability-restricted build-tool targets (`[[build_tool]]`).
  Each `(PackageIdentity, TargetUnitKind, TargetName, BuildEnvClass, BuildProfile)` tuple defines a canonical `CompilationUnitId` in `BuildGraph`.

- **AXS-BLD-005 (Five Dependency Scopes & Phase Isolation)**:
  Dependencies declared in `axiom.toml` are partitioned into five explicit scopes (`0168 §6.5`, `tasks/0356 §11`, `tasks/0372 §9`, `tasks/0661 §14`):
  1. **`normal` (`[dependencies]`)**: Linked into the package's `[lib]` and `[[bin]]` targets compiled for the `Target` environment.
  2. **`dev` (`[dev-dependencies]`)**: Available ONLY when compiling test, benchmark, or example targets of the declaring package. `dev-dependencies` MUST NOT leak into downstream consumers of the package's `[lib]` target (`tasks/0356 §11.2`, `tasks/0661 §14.1`) and MUST NOT participate in the `SemanticFingerprint` of non-test targets.
  3. **`build` (`[build-dependencies]`)**: Compiled for the `Host` environment and linked ONLY into declarative `[[build_tool]]` targets of the declaring package (`tasks/0356 §18`, `tasks/0661 §14.1`).
  4. **`comptime` (`[comptime-dependencies]`)**: Compiled for the deterministic `ComptimeVM` / `Host` evaluation context (`SPEC-08`) and isolated from target runtime binary linkage unless also declared in `[dependencies]`.
  5. **`system` (`[system-dependencies]`)**: Declarative native C/system library linkage specifications (resolved against the explicit target sysroot/SDK descriptor in `SPEC-88`), never via ambient host path probing.

- **AXS-BLD-006 (Deterministic Topological Ordering & Tie-Breaking)**:
  All collections in `Workspace`, `DependencyGraph`, and `BuildGraph`—including workspace member lists, dependency adjacency lists, feature sets, and ready queues in the build scheduler—MUST have a canonical total order sorted lexicographically by `(PackageIdentity.name, PackageIdentity.version, TargetUnitKind, TargetName, BuildEnvClass)` (`tasks/0356 §22`, `tasks/0372 §11.2`, `tasks/0661 §24`). Host directory iteration order (`readdir`), hash-table bucket order, or thread scheduling timing MUST NOT affect graph topology, action IDs, linker input argument order, or emitted diagnostics (`REQ-PKG-010`, `REQ-PKG-021`, `REQ-PKG-022`).

---

## 2. Declarative `axiom.toml` Package & Workspace Manifest Specification

- **AXS-BLD-010 (Canonical `axiom.toml` Manifest & `AXPACKAGE` Declarative Model)**:
  Per `ADR-0006` and `REQ-PKG-024`, `axiom.toml` is the sole canonical manifest file name for Axiom packages and workspaces (`0168 §6`, `tasks/0356 §8`, `tasks/0372 §5`, `tasks/0661 §11`). In the normative specification corpus (`1065 §1`), `AXPACKAGE` denotes this canonical declarative package manifest and dependency-isolated package graph model embodied by `axiom.toml` (together with `axiom.lock` in `SPEC-111` and `.axpkg` archives in `SPEC-112`). The build system MUST resolve package manifests, features, and workspace graphs deterministically at build-plan construction time without requiring any runtime package resolution, dynamic module loader, or ambient environment inspection (`REQ-PKG-024`).

- **AXS-BLD-011 (`axiom.toml` Top-Level Schema & Validation)**:
  A valid `axiom.toml` file MUST be UTF-8 encoded without BOM and parse as a strict declarative TOML document containing `[package]`, `[workspace]`, or both (a root package that also heads a workspace) (`0168 §6.2–§6.8`, `tasks/0661 §11.2`):
  ```toml
  [workspace]
  members = ["crates/core_math", "crates/app_cli"]
  exclude = ["crates/experimental"]
  default_members = ["crates/app_cli"]
  resolver = "1"

  [package]
  name = "app_cli"
  version = "0.2.0"
  edition = "2026"
  axiom = ">=0.1.0"
  license = "Apache-2.0"
  description = "Deterministic CLI application"
  authors = ["Axiom Team"]

  [lib]
  name = "app_cli"
  path = "src/lib.ax"
  crate_type = ["axlib"]

  [[bin]]
  name = "app"
  path = "src/main.ax"

  [features]
  default = ["simd"]
  simd = []
  telemetry = ["dep:metrics_core"]

  [dependencies]
  core_math = { path = "../core_math", version = "^0.2.0", features = ["fast_fma"] }
  metrics_core = { version = "^1.4.0", optional = true }

  [dev-dependencies]
  test_kit = { version = "^0.1.0" }

  [build-dependencies]
  schema_gen = { path = "../schema_gen", version = "^0.1.0" }

  [target.'cfg(target_os = "linux")'.dependencies]
  uring_sys = { version = "^0.3.0" }

  [profile.release]
  opt_level = 3
  lto = "thin"
  panic = "abort"
  debug_info = "line-tables-only"
  deterministic = true
  ```
  Validation rules:
  1. `[package].name` MUST be a non-empty ASCII lowercase identifier matching `^[a-z][a-z0-9_-]{0,63}$` and MUST NOT be a reserved keyword or `std`/`core`/`alloc`/`compiler` unless `bootstrap_internal = true` is active in toolchain sysroot builds.
  2. `[package].version` MUST be a valid Semantic Version (`MAJOR.MINOR.PATCH` with optional `-prerelease` and `+build` metadata, `REQ-PKG-022`).
  3. `[package].edition` MUST be a supported Axiom edition string (canonical default `"2026"`).
  4. Unknown top-level tables, duplicate keys, malformed SemVer strings, or type mismatches MUST fail manifest loading deterministically with `AX_DRIVER_BAD_MANIFEST` (`0168 §38`, `tasks/0661 §11.4`).

- **AXS-BLD-012 (Prohibition of Arbitrary Imperative Build Scripts)**:
  `axiom.toml` is strictly declarative (`0168 §2.2`, `tasks/0356 §18`, `tasks/0372 §14`, `tasks/0661 §18`). Manifests MUST NOT contain arbitrary shell commands, inline script hooks, or unconstrained host execution directives. Specifically:
  1. Any manifest key named `script`, `command`, `shell`, `eval`, `pre_build`, `post_build`, or `build_script_cmd` in `[package]`, `[workspace]`, `[[bin]]`, `[lib]`, or dependency tables MUST be rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "forbidden_script"`).
  2. Build-time code generation MUST use either pure `comptime` evaluation (`SPEC-08`) or an explicit declarative `[[build_tool]]` target governed by capability sandboxing (`AXS-BLD-022`).

- **AXS-BLD-013 (Workspace Root Discovery, Member Containment, and Shared State)**:
  1. **Workspace discovery**: When `axiomc` is invoked in a directory containing `axiom.toml`, it inspects whether that manifest defines `[workspace]` or `[package].workspace` pointing to an ancestor workspace root, or searches parent directories up to the filesystem or VCS root for an `axiom.toml` whose `[workspace].members` includes the current package directory (`0168 §7`, `tasks/0372 §7`, `tasks/0661 §12`).
  2. **Member path containment (`REQ-PKG-004`, `REQ-PKG-005`)**: Every path in `[workspace].members` and `[workspace].default_members` MUST be a normalized relative path using `/` separators that resolves strictly inside the workspace root directory without escaping via `..` or symlinks outside the workspace root. Missing member directories, members lacking a `[package]` `axiom.toml`, or escaping paths MUST be rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "workspace_member"`).
  3. **Shared workspace invariants (`REQ-PKG-011`, `REQ-PKG-022`)**: All members of a workspace share a single workspace-root `axiom.lock` (`SPEC-111`), unified `[profile.*]` definitions from the workspace root `axiom.toml` (member-level `[profile.*]` tables in non-root workspace members are ignored with a warning or rejected in strict mode), and a single workspace `.axiom/target` and `.axiom/cache` root.

- **AXS-BLD-014 (Declarative Feature Graph, Unification, and `@cfg` Predicates)**:
  1. **Closed feature namespace**: Every feature referenced by a package (via `--features`, `default = [...]`, or `dep_name/feat_name`) MUST be declared in that package's `[features]` table or generated as an implicit feature for an `optional = true` dependency (`0168 §10`, `tasks/0356 §13`, `tasks/0661 §16`). Referencing an undeclared feature MUST emit `AX_DRIVER_BAD_MANIFEST` (`data.kind = "unknown_feature"`, `data.feature = "<name>"`).
  2. **Monotonic feature unification within an environment class**: Within a single `BuildEnvClass` (`Target` vs `Host`), features requested on the same resolved `(PackageName, SemVer)` across all active dependency edges are combined by set union (`tasks/0356 §13.2`, `tasks/0661 §16.2`). Host `build-dependencies` features MUST NOT be unified into `Target` `normal` dependencies unless requested on the `Target` edge (`AXS-BLD-021`).
  3. **Cycle-free feature implications**: Feature implication chains (`feat_a = ["feat_b"]`) within a package or across `dep/feat` edges MUST be resolved to a least fixed point before `BuildGraph` construction; mutually exclusive feature constraints (`conflicts_with = [...]` when declared in `[features]`) that are simultaneously activated MUST fail graph resolution with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "feature_conflict"`).
  4. **Target-conditional dependencies (`[target.'cfg(...)'.dependencies]`)**: Conditional dependency predicates MUST use only the closed canonical `@cfg` predicate vocabulary defined in `SPEC-88 §4` (`target_os`, `target_arch`, `target_env`, `target_vendor`, `target_abi`, `target_pointer_width`, `target_endian`, `feature`, `profile`, `test`, ` sanitize`, logical `all(...)`, `any(...)`, `not(...)`). Unknown or syntactically invalid `@cfg` predicates in `axiom.toml` MUST be rejected with `AX_NAME_INVALID_CFG_PREDICATE` (`SPEC-88`).

- **AXS-BLD-015 (Feature Integrity & Semantic Non-Interference — `REQ-PKG-025`)**:
  To satisfy `REQ-PKG-025` (`1065 §1`, `tasks/0661 §16.4`):
  1. **No silent disabling of required features**: If package `A` requires feature `f` on dependency `B` (or a workspace CLI invocation explicitly requests `--features f`), the resolver and build planner MUST NOT silently drop, ignore, or disable `f` to work around a target incompatibility, missing optional dependency, or conflict. Either `f` and all of its transitive implications are active and verified in `B`'s `PackageIdentity.feature_set_hash`, or resolution halts with a deterministic hard error (`AX_DRIVER_BAD_MANIFEST` with `data.kind = "feature_conflict"` or `"missing_required_feature"`).
  2. **Package metadata never alters core language semantics**: Package manifest metadata (`[package]`, `[workspace]`, `[dependencies]`, `[features]`, `[profile.*]`, descriptions, authors, tags, or registry annotations) MUST NOT implicitly alter Axiom lexical grammar, operator precedence, type inference rules, borrow/ownership rules (`SPEC-09`), effect checking rules (`SPEC-11`), or memory safety guarantees (`SPEC-19`). Conditional compilation occurs ONLY at explicit `@cfg(...)` attributes in source code (`SPEC-88`), and profile flags (`opt_level`, `lto`, `debug_info`, `codegen_units`) control optimization and artifact emission without altering well-typed program semantics (`REQ-PKG-025`, `SPEC-20`).

- **AXS-BLD-016 (Canonical Build Profiles)**:
  Every workspace provides four built-in canonical profiles (`dev`, `release`, `test`, `bench`) plus optional user-defined `[profile.<name>]` tables that inherit from `dev` or `release` via `inherits = "dev" | "release"` (`0168 §11`, `tasks/0356 §25`, `tasks/0372 §15`, `tasks/0411 §8`):
  - `dev`: `opt_level = 0`, `debug_info = "full"`, `overflow_checks = true`, `lto = "off"`, `incremental = true`, `deterministic = true`.
  - `release`: `opt_level = 3`, `debug_info = "none"`, `overflow_checks = true`, `lto = "thin"`, `incremental = false`, `deterministic = true`.
  - `test`: inherits from `dev` with `@cfg(test)` active and test harness entry synthesis enabled (`SPEC-104`).
  - `bench`: inherits from `release` with `@cfg(bench)` active and benchmark harness entry synthesis enabled (`SPEC-104`).
  Invalid profile names or out-of-range profile settings MUST emit `AX_DRIVER_INVALID_PROFILE`, `AX_DRIVER_INVALID_SAFETY_PROFILE`, or `AX_DRIVER_INVALID_PANIC_STRATEGY` (`compiler/diag/code.ax`).

---

## 3. Host/Target Cross-Build Split, Sandboxed Build Generation, and `CompilerDB` `BuildGraph`

- **AXS-BLD-020 (Strict `Build`/`Host`/`Target` Environment Separation)**:
  Every workspace build plan operates over three explicit machine roles (`SPEC-88 §1`, `tasks/0356 §18.3`, `tasks/0661 §14.2`):
  1. **`Build`**: The machine executing the `axiomc` driver process.
  2. **`Host`**: The machine environment on which `build-dependencies`, `[[build_tool]]` binaries, and `comptime` extensions execute during the build (equals `Build` in standard native and single-stage cross builds).
  3. **`Target`**: The machine environment for which `normal` and `dev` compilation units (`[lib]`, `[[bin]]`, tests, benchmarks) are compiled and linked (`--target <triple>`, defaulting to `Host` when omitted).
  Every node in `DependencyGraph` and `BuildGraph` MUST carry an explicit `BuildEnvClass` (`Host(HostTriple)` vs `Target(TargetTriple)`).

- **AXS-BLD-021 (Dual-Environment Graph Partitioning & Zero Host/Target Bleed)**:
  When a package appears both as a `build-dependency` (or transitive dependency of a `[[build_tool]]`) and as a `normal`/`dev` dependency for a cross-compilation `Target` (`HostTriple != TargetTriple`):
  1. The build planner MUST instantiate two distinct `PackageIdentity` nodes—one tagged `Host(HostTriple)` and one tagged `Target(TargetTriple)`—with disjoint `CompilerDB` query keys, disjoint `.axmi` interface artifacts, disjoint object/archive outputs (`.axiom/target/host/<profile>/...` vs `.axiom/target/<target-triple>/<profile>/...`), and independent feature sets (`tasks/0356 §18.3`, `tasks/0661 §14.2`).
  2. Attempting to link a `Host`-compiled `.obj`/`.lib`/`.axmi` into a `Target` artifact (or vice versa when `HostTriple != TargetTriple`) MUST be rejected by the build graph verifier and linker with `AX_LINK_ARTIFACT_TARGET_MISMATCH` (`SPEC-24`, `SPEC-88`).
  3. Target-dependent queries (`size_of`, `align_of`, `usize` bit-width, endianness, `@cfg(target_*)`, `TargetDesc` layout) inside `BuildGraph` actions MUST evaluate against the node's own `BuildEnvClass` `TargetDesc` (`SPEC-88 §1`).

- **AXS-BLD-022 (Capability-Sandboxed `[[build_tool]]` & `comptime` Source Generation)**:
  Build-time source or table generation is strictly bounded and hermetic (`0168 §2.2`, `tasks/0356 §18`, `tasks/0372 §14`, `tasks/0661 §18`):
  1. **Declared inputs and outputs**: A declarative `[[build_tool]]` target in `axiom.toml` MUST declare its explicit input file globs/paths (`inputs = ["schema/api.axschema"]`, relative to package root) and output file names (`outputs = ["generated/api_types.ax"]`, materialized strictly inside `.axiom/target/<env>/<profile>/gen/<pkg-id>/`).
  2. **Capability-sandboxed execution (`SPEC-53`)**: When executed by the build scheduler, a `[[build_tool]]` binary (or `comptime` generator) receives ONLY a read-only `FsCap` scoped to its declared `inputs` directory and a write-only `FsCap` scoped to its dedicated `.axiom/target/.../gen/<pkg-id>/` output directory, with `NetCap = Denied`, `ProcessCap = Denied`, wall-clock `ClockCap = Denied`, and a sanitized environment table containing only canonical `AXIOM_PKG_NAME`, `AXIOM_PKG_VERSION`, `AXIOM_TARGET_TRIPLE`, `AXIOM_PROFILE`, and `AXIOM_OUT_DIR` variables.
  3. **Generated source provenance (`GeneratedSourceProvenance`)**: Every generated `.ax` file registered in `CompilerDB` carries a `GeneratedSourceProvenance` record (`generator_unit_id`, `input_digest`, `output_digest`, `logical_mount_path`) so diagnostics originating in generated code report both the generated file span and the originating `[[build_tool]]` / `comptime` declaration (`SPEC-61`, `SPEC-103`).

- **AXS-BLD-023 (`CompilerDB`-Backed `BuildGraph` Action DAG)**:
  The `BuildGraph` lowers the resolved `DependencyGraph` into a fine-grained, content-addressed DAG of typed build actions scheduled over `CompilerDB` (`SPEC-21`, `SPEC-22`, `SPEC-23`, `0168 §14`, `tasks/0356 §20`, `tasks/0372 §12`, `tasks/0661 §19`):
  ```
  enum BuildActionKind {
      RunBuildTool,      // Execute host [[build_tool]] -> generated source tree
      EmitInterface,     // Parse + HIR + Type/Cap/Effect check -> .axmi / .axmeta
      CompileCodegenUnit,// MIR + OptIR + LIR + Machine encode -> .obj / .o / .wasm
      AssembleArchive,   // Package CGU objects + .axmi -> .lib / .a / .axlib
      LinkArtifact,      // Link objects + archives + sysroot stubs -> .exe / ELF / Mach-O / .dll / .so / .dylib / .wasm
      RunTestUnit,       // Execute compiled test/bench binary under harness (axiomc test / bench)
  }
  ```
  1. **Interface-pipelined parallelism (`EmitInterface` vs `CompileCodegenUnit`)**: Downstream compilation units that depend on package `P` require `P`'s `EmitInterface` action (`.axmi` export table and `InterfaceFingerprint`) to begin frontend/type/capability checking, and do NOT need to wait for `P`'s `CompileCodegenUnit` or `AssembleArchive` actions until final `LinkArtifact` (`SPEC-24`, `SPEC-27`, `tasks/0356 §21`).
  2. **Unified `CompilerDB` authority**: In-process compilation actions (`EmitInterface`, `CompileCodegenUnit`, `AssembleArchive`, `LinkArtifact`) execute directly as memoized `CompilerDB` query pipelines (`SPEC-21`, `SPEC-23`) without spawning redundant child `axiomc` OS processes when running inside the workspace driver.

- **AXS-BLD-024 (Artifact Layout & Deterministic Output Paths)**:
  All build outputs for a workspace MUST be materialized under the canonical workspace build root (`.axiom/target/` by default, or `--target-dir <path>`) (`0168 §16`, `tasks/0372 §16`, `tasks/0661 §23`):
  - `.axiom/target/host/<profile>/`: Host `build-dependencies` and `[[build_tool]]` artifacts.
  - `.axiom/target/<target-triple>/<profile>/deps/`: Per-package `.axmi`, `.obj`/`.o`, and `.axlib`/`.lib`/`.a` artifacts named `<pkg_name>-<short_pkg_id_hash>.<ext>`.
  - `.axiom/target/<target-triple>/<profile>/gen/<pkg_name>-<short_pkg_id_hash>/`: Sandboxed `[[build_tool]]` outputs.
  - `.axiom/target/<target-triple>/<profile>/<bin_or_lib_name><ext>`: Final linked root artifacts (`exe`, `dll`, `so`, `dylib`, `a`, `lib`, `axlib`, `wasm`).
  - `.axiom/cache/`: Multi-tier content-addressed build cache (`AXS-BLD-030`).

- **AXS-BLD-025 (Deterministic Parallel Scheduling & Worker Invariance)**:
  The `BuildGraph` scheduler (`compiler/build/graph`) executes ready `BuildAction` nodes across `--jobs <N>` worker threads (`SPEC-23`):
  1. Ready actions whose dependencies are all `Completed` are dequeued in canonical `BuildActionId` order (`AXS-BLD-006`).
  2. Resulting artifacts, `.axmi` metadata, cache entries, `BuildEvent` logical sequence numbers, and sorted diagnostics (`AXD-060`) MUST be byte-for-byte identical between `--jobs 1` and `--jobs N` for any $N \ge 1$ (`SPEC-22`, `SPEC-23`, `REQ-PKG-010`, `REQ-PKG-022`).

---

## 4. Multi-Tier Content-Addressed Build Cache, Cutoff & Atomic Publication

- **AXS-BLD-030 (Four-Tier Content-Addressed Build Cache Keys)**:
  Building upon `SPEC-22` (`AXS-INC-010..015`), the workspace build cache (`compiler/build/cache`) computes four domain-separated 256-bit BLAKE3 fingerprints (stored alongside 128-bit `CompilerDB` query fingerprints) for every compilation unit and build action (`0168 §15`, `tasks/0356 §24`, `tasks/0372 §13`, `tasks/0661 §20–§21`):
  1. **`SemanticFingerprint` (`InterfaceFingerprint`)**: Covers the package's `PackageIdentity` (`name`, `version`, `feature_set_hash`, `target_env_class`), `edition`, active `@cfg` predicate valuation, normalized source-file content hashes of public/interface-affecting declarations, and the `SemanticFingerprint`s of direct dependencies. Whitespace, comments, and private function bodies that do not alter public types, traits, capabilities, effects, inline/generic/comptime bodies, or exported constants DO NOT change `SemanticFingerprint` (`SPEC-22`, `SPEC-24`).
  2. **`AbiFingerprint`**: Covers exported symbol names, calling conventions (`CallConvDesc`), `@repr` physical type layouts (`size`, `align`, field offsets), vtable layouts, panic strategy (`abort` vs `unwind`), and target ABI descriptor (`TargetFingerprint`, `SPEC-81`).
  3. **`CodegenFingerprint`**: Covers `SemanticFingerprint`, `AbiFingerprint`, private function/module implementation bodies, `[profile.<name>]` optimization settings (`opt_level`, `lto`, `debug_info`, `overflow_checks`, `safety_profile`, `codegen_units`), and target CPU features (`--target-feature`).
  4. **`BuildFingerprint` (`ActionCacheKey`)**: Covers `CodegenFingerprint` (or action-specific inputs), exact compiler binary/toolchain digest (`CompilerVersionDigest`), sysroot/SDK stub digest (`SysrootFingerprint`, `SPEC-88`), and dependency archive/object digests for `AssembleArchive` / `LinkArtifact` actions.

- **AXS-BLD-031 (Early-Cutoff Cascade Suppression)**:
  When a source edit inside package `A` modifies only private function bodies without changing `A`'s emitted `.axmi` interface (`SemanticFingerprint_new == SemanticFingerprint_old` and `AbiFingerprint_new == AbiFingerprint_old`):
  1. `A`'s affected `CompileCodegenUnit` and `AssembleArchive` actions re-execute.
  2. Downstream package `B` (which depends on `A`) observes an unchanged `SemanticFingerprint` and `AbiFingerprint` for `A`; therefore, `B`'s `EmitInterface` and `CompileCodegenUnit` actions achieve an immediate early-cutoff cache hit and MUST NOT recompile (`SPEC-22`, `tasks/0356 §21.2`, `tasks/0661 §20.3`).
  3. Only the final `LinkArtifact` action that consumes `A`'s updated archive `.lib`/`.a`/`.axlib` re-executes.

- **AXS-BLD-032 (Cache-Poisoning Defense & Pre-Reuse Artifact Verification)**:
  The content-addressed build cache (`.axiom/cache/`) MUST treat on-disk cache entries as untrusted until verified (`tasks/0356 §24.4`, `tasks/0661 §21.4`):
  1. Every cached entry consists of an artifact payload and a manifest header recording the `ActionCacheKey`, expected payload byte length, and BLAKE3-256 content digest.
  2. Before reusing a cached `.axmi`, `.obj`, `.axlib`, or executable artifact on a cache hit, `compiler/build/cache` MUST verify the header magic/schema version, file size, and BLAKE3-256 content digest (plus `ArtifactHeader` target triple match per `SPEC-24`).
  3. If a cache entry is truncated, corrupted, schema-mismatched, or fails digest verification, the cache manager MUST evict the corrupt entry, record a cache-miss reason (`CacheMissReason.CorruptEntryEvicted`), and transparently recompute the action without emitting a user error (`SPEC-22 AXS-INC-022`).

- **AXS-BLD-033 (Atomic Write-Then-Rename Publication & Cancellation Safety)**:
  1. **No partial artifact visibility**: Every build action that writes an artifact or cache entry MUST first write to a process/worker-unique temporary file in the same filesystem directory (`<target_path>.tmp.<pid>.<worker_id>`), flush its contents, and atomically publish it to `<target_path>` via atomic rename (`MoveFileExW` with `MOVEFILE_REPLACE_EXISTING` on Windows; `rename(2)` on POSIX) (`tasks/0356 §24.5`, `tasks/0411 §22`, `tasks/0661 §21.5`).
  2. **Structured cancellation (`CancellationToken`)**: When a build is interrupted (SIGINT / Ctrl+C, or first-error fail-fast under `--fail-fast`), the scheduler signals its `CancellationToken` (`SPEC-34`), awaits in-flight worker steps to reach a safe cancellation point, deletes any uncommitted `.tmp.*` files, and leaves `.axiom/cache` and `.axiom/target` free of half-written artifacts or stale lockfiles.

- **AXS-BLD-034 (Reproducible Build Canonicalization — `REQ-PKG-022`)**:
  All artifacts emitted by `BuildGraph` actions MUST be byte-for-byte reproducible across rebuilds, directory locations, and host platforms (`REQ-PKG-010`, `REQ-PKG-018`..`REQ-PKG-022`, `SPEC-88`, `SPEC-89`):
  1. Archive headers (`CoffAr`, `GnuAr`, `BsdAr`, `.axlib`) and object headers (`COFF`, `ELF`, `Mach-O`, `.wasm`) zero all timestamps (`mtime = 0`), UID/GID fields (`0`), and file modes (`0644`/`0755`), or derive header hashes deterministically from content digests (`SPEC-26`, `SPEC-80`, `SPEC-89`).
  2. Debug info and source map paths embedded in `.debug_line`, `.pdata`, or `.axmeta` are remapped relative to the logical package root (`pkg://<pkg_name>@<version>/src/...`) using `/` separators (`REQ-PKG-018`, `SPEC-88`, `SPEC-104`).

---

## 5. Workspace Driver Orchestration CLI, Diagnostics, Examples & Verification Matrix

- **AXS-BLD-040 (Workspace Driver Subcommands)**:
  The `axiomc` compiler driver (`compiler/driver/workspace_cmd`) provides seven canonical workspace-aware subcommands (`0168 §18`, `tasks/0372 §17`, `tasks/0411 §4`, `tasks/0661 §25`):
  1. **`axiomc build`**: Resolves the workspace `DependencyGraph`, lowers the `BuildGraph`, and executes all required `RunBuildTool`, `EmitInterface`, `CompileCodegenUnit`, `AssembleArchive`, and `LinkArtifact` actions for the selected packages/targets.
  2. **`axiomc check`**: Executes `RunBuildTool` and `EmitInterface` (full lexing, parsing, `@cfg` pruning, name resolution, type/trait checking, ownership/capability/effect checking, and MIR verification) across the selected workspace packages without running `CompileCodegenUnit`, `AssembleArchive`, or `LinkArtifact` (`tasks/0411 §4.2`).
  3. **`axiomc run`**: Executes `axiomc build` for a single executable binary target (`--bin <name>` or the sole default `[[bin]]` of the selected package) and invokes the resulting executable on the host (or configured target runner) forwarding trailing arguments after `--`. Passing `--universal-targets` or a library-only target to `axiomc run` emits `AX_DRIVER_USAGE` (exit code `2`).
  4. **`axiomc test`**: Compiles and executes `[lib]` inline `@test` units, `tests/*.ax` integration test targets, and `dev-dependencies` under the `test` profile (`SPEC-104`).
  5. **`axiomc bench`**: Compiles and executes `benches/*.ax` and `@bench` targets under the `bench` profile (`SPEC-76`, `SPEC-104`).
  6. **`axiomc clean`**: Deterministically removes build outputs in `.axiom/target/` (or scoped to `--package <name>` / `--profile <name>` / `--target <triple>`), while preserving `.axiom/cache/` unless `--all` or `--cache` is specified.
  7. **`axiomc graph`**: Exports the resolved `DependencyGraph` and/or `BuildGraph` without executing compilation actions (`AXS-BLD-042`).

- **AXS-BLD-041 (Workspace Selection, Feature, Target, and Mode Flags)**:
  Workspace subcommands accept the following canonical flags (`0168 §18.2`, `tasks/0411 §5`, `tasks/0661 §25.2`):
  - `--manifest-path <path>`: Explicit path to `axiom.toml` (defaults to workspace/package discovery from the working directory).
  - `--workspace`: Operate on all workspace members (`[workspace].members`).
  - `--package <name>` / `-p <name>` (repeatable): Operate on the named workspace member package(s). When neither `--workspace` nor `-p` is passed at a workspace root, `axiomc` operates on `[workspace].default_members` (or all `members` if `default_members` is omitted).
  - `--lib`, `--bin <name>`, `--bins`, `--test <name>`, `--tests`, `--bench <name>`, `--benches`: Target unit filters within the selected package(s).
  - `--profile <name>` (or `--release` shorthand for `--profile release`): Active build profile (`dev` by default for `build`/`check`/`run`, `test` for `test`, `bench` for `bench`).
  - `--target <triple>`: Target environment triple (`SPEC-88`).
  - `--features <f1,f2>`, `--no-default-features`, `--all-features`: Explicit feature selection on the selected root package(s) (`AXS-BLD-014`).
  - `--jobs <N>` / `-j <N>`: Worker thread count for the `BuildGraph` scheduler (`SPEC-23`, `AXS-BLD-025`).
  - `--offline`: Forbid network access during manifest/workspace resolution; fail immediately if any required package is not already present in the workspace, vendor tree, or local cache (`SPEC-111`, `SPEC-112`).
  - `--locked` / `--frozen`: Require an up-to-date `axiom.lock` without modifying it (`SPEC-111`).
  - `--explain`: Emit structured human-readable or JSON explanations of why each `BuildAction` was executed or reused from cache (`CacheHit` vs `CacheMissReason`: `SourceModified`, `InterfaceChanged`, `ProfileChanged`, `FeaturesChanged`, `TargetChanged`, `CompilerChanged`, `CorruptEntryEvicted`, `MissingOutput`) (`tasks/0411 §24`).

- **AXS-BLD-042 (Graph Introspection (`axiomc graph --format=json|dot`) & `BuildEvent` Stream)**:
  1. **`axiomc graph --format=json|dot`**: Serializes the resolved `DependencyGraph` and lowered `BuildGraph` in canonical topological order (`AXS-BLD-006`). JSON output includes `"schema_version": 1`, `"workspace_root"`, `"packages"` (with `PackageIdentity`, active `features`, `BuildEnvClass`, and `SemanticFingerprint`), `"dependency_edges"` (with `scope`: `"normal" | "dev" | "build" | "comptime" | "system"`), and `"build_actions"` (with `id`, `kind`, `env`, `inputs`, `outputs`, and `action_cache_key`). Graphviz `dot` output emits deterministic `digraph axiom_build_graph { ... }` nodes and edges in exact sorted order (`tasks/0372 §18`, `tasks/0661 §25.4`).
  2. **Structured `BuildEvent` JSONL stream (`--message-format=json`)**: During `build`/`check`/`test`/`bench`, the driver emits newline-delimited JSON (`NDJSON`) events (`WorkspaceResolved`, `ActionStarted`, `ActionCached`, `ActionCompleted`, `CompilerDiagnostic`, `ArtifactEmitted`, `BuildFinished`) ordered deterministically by logical action sequence number (`tasks/0411 §23`).

- **AXS-BLD-050 (Diagnostic Mapping)**:
  Workspace manifest parsing, feature unification, dependency graph construction, build cache verification, and workspace driver CLI commands reuse the canonical `DRIVER`, `NAME`, `LINK`, `IO`, and `ICE` diagnostic codes registered in `compiler/diag/code.ax` (`spec/diagnostics.md` §3 `AXD-021`, §10–§11):

  | Corpus / Task Shorthand | Canonical `AX_<AREA>_<NAME>` | Area | Sev | Exit | Trigger Condition & Structured `data` Fields |
  |---|---|---|---|---|---|
  | `AXPKG_0001`, `EBUILD_MANIFEST` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Malformed `axiom.toml` TOML syntax, unknown table/key, missing required `[package].name` / `version` / `edition`, invalid SemVer literal (`REQ-PKG-022`), or invalid `[workspace]` table (`data.kind = "syntax" \| "schema" \| "semver"`). |
  | `AXPKG_0002`, `EBUILD_FORBIDDEN_SCRIPT` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Imperative build script directive (`script`, `command`, `shell`, `eval`, `pre_build`, `post_build`) present in `axiom.toml` (`AXS-BLD-012`; `data.kind = "forbidden_script"`, `data.key`). |
  | `AXPKG_0003`, `EBUILD_WORKSPACE_MEMBER` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | `[workspace].members` path escapes workspace root (`..`), does not exist, or lacks a valid `[package]` `axiom.toml`, or duplicate package name in workspace (`AXS-BLD-013`; `data.kind = "workspace_member"`, `data.member`). |
  | `AXPKG_0004`, `EBUILD_PKG_CYCLE` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Inter-package dependency cycle `PkgA -> PkgB -> ... -> PkgA` in `DependencyGraph` (`AXS-BLD-003`, `REQ-PKG-008`; `data.kind = "package_cycle"`, `data.cycle`). |
  | `AXPKG_0005`, `EBUILD_FEATURE` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Reference to an undeclared package feature, cyclic feature implication, mutually exclusive feature conflict, or unfulfillable required feature (`AXS-BLD-014..015`, `REQ-PKG-025`; `data.kind = "unknown_feature" \| "feature_conflict" \| "missing_required_feature"`, `data.package`, `data.feature`). |
  | `AXBUILD_0001`, `EBUILD_CFG` | `AX_NAME_INVALID_CFG_PREDICATE` | `NAME` | `error` | `1` | Invalid or unknown `@cfg(...)` predicate in `[target.'cfg(...)'.dependencies]` (`AXS-BLD-014`, `SPEC-88`; `data.key`, `data.value`). |
  | `AXBUILD_0002`, `EBUILD_PROFILE` | `AX_DRIVER_INVALID_PROFILE` | `DRIVER` | `error` | `2` | Unknown `--profile <name>` or invalid `[profile.<name>]` inheritance/configuration (`AXS-BLD-016`). |
  | `AXBUILD_0003`, `EBUILD_TARGET_MIX` | `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `error` | `1` | Attempt to link or reuse a `Host`-environment artifact in a cross-compiled `Target` unit or vice versa (`AXS-BLD-021`). |
  | `AXBUILD_0004`, `EBUILD_CLI_USAGE` | `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` | `DRIVER` | `error` | `2` | Invalid workspace subcommand arguments, unknown package passed to `-p`, ambiguous `axiomc run` target without `--bin`, or invalid `--format` on `axiomc graph` (`AXS-BLD-040..042`). |

- **AXS-BLD-051 (Positive Canonical Examples)**:
  1. **Multi-package workspace with host `build-dependencies`, target `[dependencies]`, and early cutoff**:
     ```axiom
     // crates/core_math/src/lib.ax
     module core_math

     pub fn dot_product(a: view<[f64]>, b: view<[f64]>) -> f64 {
         let mut acc: f64 = 0.0
         let n: usize = if a.len() < b.len() { a.len() } else { b.len() }
         let mut i: usize = 0
         while i < n {
             acc = acc + (a[i] * b[i])
             i = i + 1
         }
         return acc
     }
     ```
     ```axiom
     // crates/app_cli/src/main.ax
     module app_cli

     use core_math.dot_product

     pub fn main() -> i32 {
         let xs: [3]f64 = [1.0, 2.0, 3.0]
         let ys: [3]f64 = [4.0, 5.0, 6.0]
         let total: f64 = dot_product(xs.as_view(), ys.as_view())
         if total == 32.0 {
             return 0
         }
         return 1
     }
     ```
     When a private helper inside `crates/core_math/src/lib.ax` is edited without changing the signature or inline contract of `core_math.dot_product`, `core_math`'s `SemanticFingerprint` and `AbiFingerprint` remain identical (`AXS-BLD-030..031`); `app_cli`'s `EmitInterface` and `CompileCodegenUnit` actions hit the `.axiom/cache` without recompiling, and only `core_math` codegen plus final `app_cli` linking execute.

- **AXS-BLD-052 (Negative Canonical Examples)**:
  1. **Rejected imperative build script in `axiom.toml` (`AXS-BLD-012`)**:
     ```toml
     [package]
     name = "bad_pkg"
     version = "0.1.0"
     edition = "2026"
     script = "sh ./gen.sh" # ERROR: AX_DRIVER_BAD_MANIFEST (data.kind = "forbidden_script")
     ```
  2. **Rejected inter-package dependency cycle (`AXS-BLD-003`, `REQ-PKG-008`)**:
     - `crates/alpha/axiom.toml` declares `beta = { path = "../beta", version = "^0.1.0" }` under `[dependencies]`.
     - `crates/beta/axiom.toml` declares `alpha = { path = "../alpha", version = "^0.1.0" }` under `[dependencies]`.
     - Running `axiomc check --workspace` rejects the workspace graph with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "package_cycle"`, `data.cycle = "alpha -> beta -> alpha"`).
  3. **Rejected unknown or conflicting required feature (`AXS-BLD-014..015`, `REQ-PKG-025`)**:
     - `crates/app_cli/axiom.toml` requests `core_math = { path = "../core_math", features = ["nonexistent_simd"] }`.
     - Resolution halts immediately with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "unknown_feature"`, `data.package = "core_math"`, `data.feature = "nonexistent_simd"`) rather than silently dropping `"nonexistent_simd"`.

- **AXS-BLD-053 (E20.1 Implementation & Verification Matrix)**:

  | Task | Role | Deliverable Scope & Allowed Paths | Primary Invariant & Verification Suite |
  |---|---|---|---|
  | `T851` | `axiom-frontend` | `compiler/build/manifest`, `compiler/build/workspace`, `tests/run/build_manifest`: Declarative `axiom.toml` parser/validator (`[package]`, `[workspace]`, `[[bin]]`, `[lib]`, 5 dependency scopes, `[features]`, `[profile.*]`, `[target.'cfg(...)'.dependencies]`), imperative script rejection (`AXS-BLD-012`), workspace member discovery, feature unification, and `REQ-PKG-025` enforcement. | `INV-BLD-001` (`tests/run/build_manifest`) |
  | `T852` | `axiom-backend` | `compiler/build/graph`, `compiler/build/cache`, `compiler/driver/workspace_cmd`, `tests/run/build_graph`: `CompilerDB`-backed `BuildGraph` lowering (`AXS-BLD-023`), strict `Host`/`Target` cross-build split (`AXS-BLD-020..021`), capability-sandboxed `[[build_tool]]` provenance (`AXS-BLD-022`), 4-tier BLAKE3 build cache with early cutoff & atomic rename (`AXS-BLD-030..034`), and `axiomc build\|check\|run\|test\|bench\|clean\|graph` CLI (`AXS-BLD-040..042`). | `INV-BLD-002` (`tests/run/build_graph`) |
  | `T853` | `axiom-qa` | `tests/conformance/p20/e20_1_build_graph_driver`: End-to-end E20.1 conformance suite covering `REQ-PKG-022`, `REQ-PKG-024`, and `REQ-PKG-025` across multi-package workspaces, feature unification, early-cutoff caching, cache corruption recovery, cross-target `Host`/`Target` isolation, and deterministic `graph`/`--explain` outputs. | `INV-BLD-003` (`tests/conformance/p20/e20_1_build_graph_driver`) |

## Sources
0168 Part XXXI (`§1`–`§41`, `BUILD-20..35`, `AXPKG_0001..0005`, `AXBUILD_0001..0004`); tasks/0356 (BOOTSTRAP-097: `§1`–`§105`, `ABUILD2-20..72`); tasks/0372 (BOOTSTRAP-113: `§1`–`§62`, `ABUILD-20..57`); tasks/0411 (BOOTSTRAP-152: `§1`–`§49`, `ADRIVER-20..55`); tasks/0661 (BOOTSTRAP-402: `§1`–`§52`, `ABUILD-01..30`); tasks/1065 (`§1`); `spec/requirements/CATALOG.md` (`REQ-PKG-001`..`REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`); `ADR-0006` (`§6`–`§8`); `ADR-0007`; `SPEC-03`; `SPEC-08`; `SPEC-21`; `SPEC-22`; `SPEC-23`; `SPEC-24`; `SPEC-26`; `SPEC-27`; `SPEC-34`; `SPEC-53`; `SPEC-61`; `SPEC-76`; `SPEC-81`; `SPEC-88`; `SPEC-89`; `SPEC-103`; `SPEC-104`; `spec/diagnostics.md`; `spec/invariants.md`.
