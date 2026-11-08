# SPEC-111 — Canonical `AXPACKAGE` Package Manager, Deterministic SemVer 2.0 Resolver, Monotonic Feature Unification & Reproducible `axiom.lock` Specification

- **Status**: Normative
- **Phase**: P20 (E20.2 — Package Manager, SemVer Resolution & Lockfiles)
- **Rules**: `AXS-PKG-001` .. `AXS-PKG-053`
- **Requirements**: `REQ-ECO-8736`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025` (consolidates foundational package/dependency/lockfile rules `REQ-PKG-001`..`REQ-PKG-023`)

## Tóm tắt

Đặc tả này quy định kiến trúc chính tắc cho trình quản lý gói `AXPACKAGE`, định danh gói có địa chỉ nội dung (`PackageIdentity`), bộ giải ràng buộc phiên bản ngữ nghĩa SemVer 2.0 tất định (`compiler/pkg/semver`, `compiler/pkg/resolver`), cơ chế hợp nhất tính năng đơn điệu, cô lập đa phiên bản chính song song (side-by-side major-version isolation), hợp đồng khóa tái lập `axiom.lock` v1 (`std/pkg/lockfile`), kho lưu trữ gói định danh bằng mã băm SHA-256 và đóng gói ngoại tuyến `vendor/` (`std/pkg/store`), cùng giao diện dòng lệnh `axiomc pkg` (`compiler/driver/pkg_cmd`):

1. **Mô hình `AXPACKAGE`, định danh 7 thành phần và chuẩn SemVer 2.0 (`AXS-PKG-001`..`AXS-PKG-005`)**: `AXPACKAGE` hoạt động hoàn toàn tại thời điểm dựng/biên dịch và không bao giờ trở thành phụ thuộc thời gian chạy của tệp thực thi (`REQ-PKG-013`, `REQ-PKG-024`, `REQ-ECO-8736`). Mỗi phiên bản gói được định danh duy nhất bởi bộ 7 thành phần `PackageIdentity = (Registry, Namespace, Name, Version, SourceId, ContentHash, SemanticInterfaceFingerprint)` độc lập với đường dẫn tệp cục bộ hay URL tải xuống. Chuẩn SemVer 2.0 (`MAJOR.MINOR.PATCH[-prerelease][+build]`) quy định thứ tự toàn phần tất định và các toán tử ràng buộc (`=`, `^`, `~`, `<`, `<=`, `>`, `>=`, `!=`, `*`, hợp/giao), trong đó các phiên bản tiền phát hành (`prerelease`) không bao giờ tự động được chọn bởi các ràng buộc ổn định.
2. **Bộ giải phụ thuộc tất định độc lập thứ tự và cây suy diễn xung đột (`AXS-PKG-010`..`AXS-PKG-013`)**: Bộ giải phụ thuộc theo phong cách PubGrub/CDCL tạo ra cùng một đồ thị `ResolvedPackageGraph` và tệp `axiom.lock` giống hệt nhau từng byte bất kể thứ tự khai báo trong `axiom.toml`, thứ tự tệp trên đĩa hay thứ tự trang của kho lưu trữ (`REQ-PKG-020`, `REQ-PKG-022`). Khi xảy ra mâu thuẫn phiên bản hoặc tính năng, bộ giải sinh cây suy diễn nguyên nhân xung đột (conflict derivation tree) đầy đủ từ gói gốc tới điểm xung đột.
3. **Cô lập đa phiên bản chính song song và hợp nhất tính năng đơn điệu (`AXS-PKG-020`..`AXS-PKG-024`)**: Khi hai nhánh phụ thuộc yêu cầu hai phiên bản chính không tương thích (`pkg@1.x` và `pkg@2.x`), trình giải quyết cho phép cả hai cùng tồn tại với `PackageId` và tiền tố ký hiệu đã mã hóa (mangled symbol prefix) tách biệt, đồng thời gắn nhãn kiểu danh định (`TypeId`) khác biệt (`pkg@1.Vec2 != pkg@2.Vec2`) trừ khi được tái xuất công khai tường minh (`pub use`). Quá trình hợp nhất tính năng là đơn điệu (phép hợp tập hợp trong cùng `BuildEnvClass`), tách biệt nghiêm ngặt giữa `Host` (`build`/`comptime`) và `Target` (`normal`/`dev`), không bao giờ âm thầm tắt tính năng bắt buộc và không bao giờ làm thay đổi ngữ nghĩa cốt lõi của ngôn ngữ (`REQ-PKG-025`).
4. **Định dạng `axiom.lock` v1 chính tắc, kho nội dung SHA-256 và chế độ ngoại tuyến `vendor/` (`AXS-PKG-030`..`AXS-PKG-033`)**: Quy định lược đồ `axiom.lock` v1 được sắp xếp từ điển tất định, gắn kết `sdk_fingerprint` (`SPEC-88`) và `graph_hash` (`SHA-256`). Kho lưu trữ gói cục bộ (`.axiom/cache/pkg/`) và thư mục `vendor/` luôn xác thực mã băm nội dung `SHA-256` trước khi sử dụng (không bao giờ tin tưởng tên tệp đơn thuần), giải nén an toàn trong vùng cát (chống path traversal và zip bomb), và hỗ trợ dựng hoàn toàn cách ly mạng (`--locked`, `--offline`, `--vendor`).
5. **Giao diện dòng lệnh `axiomc pkg` và ma trận kiểm chứng E20.2 (`AXS-PKG-040`..`AXS-PKG-053`)**: Quy định ngữ nghĩa chính tắc cho `axiomc pkg init|add|remove|update|lock|tree|verify-lock|vendor`, bảng ánh xạ mã chẩn đoán (`AX_DRIVER_BAD_MANIFEST`, `AX_TYPE_MISMATCH`, …), các ví dụ chuẩn và ma trận kiểm chứng cho `T855`–`T857`.

---

## 1. `AXPACKAGE` Model, Canonical `PackageIdentity`, and SemVer 2.0 Specification

- **AXS-PKG-001 (`AXPACKAGE` Boundary & Compile-Time-Only Resolution — `REQ-PKG-024`, `REQ-ECO-8736`)**:
  1. **Compile-time and build-time authority**: `AXPACKAGE` (`1065 §1–§2`, `0098 §1`, `tasks/0412 §1`, `tasks/0446 §187.1`) governs package manifest dependency declarations, SemVer 2.0 version constraint resolution, feature unification, lockfile persistence (`axiom.lock`), content-addressed source/artifact caching, and offline vendoring (`vendor/`). All `AXPACKAGE` resolution completes deterministically before or during `BuildGraph` construction (`SPEC-110 AXS-BLD-010`).
  2. **Zero runtime package manager dependency (`REQ-PKG-013`, `REQ-PKG-024`, `PKG-INV-19`)**: Compiled Axiom executables and libraries are standalone native or WebAssembly artifacts (`SPEC-89`). They MUST NOT embed a dynamic package resolver, query a package registry at runtime, or require `axiomc`, `axiom.toml`, `axiom.lock`, or `.axiom/cache` to be present on the deployment target machine (`0098 §1`, `tasks/0446 §187.160 ADIST-20`, `1065 §1`).
  3. **Strict separation of concerns (`1065 §2`, `PKG-INV-38`, `PKG-INV-40`)**: `AXPACKAGE` does NOT own core language semantics (`CompilerDB`, `SPEC-03`), version-control history (`AXVCS` / `AXHISTORY`, `SPEC-102`), build action scheduling (`AXBUILD`, `SPEC-110`), or cryptographic primitives (`AXCRYPTO` / `AXTRUST`, `SPEC-112`).

- **AXS-PKG-002 (Canonical 7-Tuple `PackageIdentity` & Path/URL Independence)**:
  Refining `SPEC-110 AXS-BLD-002`, every resolved package instance in `AXPACKAGE` is uniquely identified by a canonical 7-tuple (`0098 §4–§8`, `tasks/0412 §4–§7`, `tasks/0446 §187.2–§187.4`, `tasks/0661 §6`, `tasks/1065 §3–§6, §52–§53`, `REQ-PKG-001`..`REQ-PKG-002`, `REQ-PKG-011`):
  ```
  PackageIdentity = {
      registry:                        RegistryId,     // "default" | "workspace" | "local" | "vendor" | <registry-id>
      namespace:                       NamespaceId,    // canonical ASCII lowercase ([a-z][a-z0-9_-]{0,63}), default "default"
      name:                            PackageName,    // canonical ASCII lowercase ([a-z][a-z0-9_-]{0,63})
      version:                         SemVer,         // MAJOR.MINOR.PATCH[-prerelease][+build]
      source_id:                       PackageSourceId,// Registry | VcsCommit | Path | Workspace | Archive | Vendor
      content_hash:                    Digest256,      // SHA-256 of canonical normalized package tree / archive
      semantic_interface_fingerprint:  Digest256       // BLAKE3-256 SIF of exported public interface & ABI contract
  }
  ```
  1. **Namespace and name normalization (`1065 §4–§6`, `PKG-INV-01`, `PKG-INV-15`)**: Both `namespace` and `name` MUST match `^[a-z][a-z0-9_-]{0,63}$`. When a package in `axiom.toml` omits an explicit `namespace` prefix (writing `name = "core_math"` rather than `name = "axiom/core_math"`), `namespace` defaults canonically to `"default"`. Package names and namespaces MUST NOT contain `/`, `\`, `..`, NUL bytes, or path-traversal sequences. A namespace prevents naming collisions across organizations/registries but NEVER implies cryptographic trust (`1065 §5`).
  2. **Host-path, URL, and credential independence (`1065 §3`, `REQ-PKG-001`, `PKG-INV-03`, `PKG-INV-33`)**: Absolute host filesystem paths, ephemeral mirror/download URLs, mutable Git branch/tag names, and authentication tokens/credentials MUST NOT participate in `PackageIdentity`, `content_hash`, `semantic_interface_fingerprint`, or mangled symbol hashes. Two packages with the same `(namespace, name, version)` originating from different registries or Git repositories have distinct `source_id` and `content_hash` fields and MUST NOT be conflated (`tasks/0412 §4`, `tasks/0446 §187.3`, `APKG-21`).
  3. **ContentHash computation (`0098 §6`, `tasks/0446 §187.4`, `1065 §52–§53`, `PKG-INV-02`)**: `content_hash` is the 256-bit `SHA-256` digest over the canonical package manifest (`axiom.toml`) and all package source/resource files sorted lexicographically by normalized `/` relative path, with UTF-8 `.ax`/`.toml` line endings normalized to `LF` (`\n`) and without filesystem timestamps, UID/GID, or untracked build outputs (`.axiom/`, `target/`, `vendor/`).
  4. **Semantic Interface Fingerprint (`SIF`, `0098 §7–§8`, `SPEC-110 AXS-BLD-030`, `APKG-10`)**: `semantic_interface_fingerprint` is the 256-bit BLAKE3 digest of the package's public module exports, public types/traits/capabilities/effects, generic MIR body templates (`REQ-PKG-010`), `@repr` layout contracts, active feature set (`feature_set_hash`), and target environment (`BuildEnvClass`). Modifying private function bodies leaves `semantic_interface_fingerprint` unchanged, enabling downstream early cutoff (`SPEC-110 AXS-BLD-031`).

- **AXS-PKG-003 (Dependency Source Coordinates & Immutable Revision Pinning)**:
  Every dependency declaration in `axiom.toml` resolves to one of six canonical `PackageSourceId` variants (`0098 §4`, `tasks/0412 §5, §148–§151`, `tasks/0446 §187.3`, `tasks/1065 §18–§27`):
  1. **`RegistrySource(registry_id, namespace, name, version)`**: Resolved from a configured package registry (`registry = "default"` when omitted).
  2. **`VcsCommitSource(repo_url_canonical, commit_oid, subdir_rel)`**: Declared in `axiom.toml` with `git = "<url>"` and an optional `rev = "<oid>"`, `tag = "<tag>"`, or `branch = "<branch>"`. During resolution, the VCS reference MUST be resolved to an exact immutable commit hash (`commit_oid`, 40-hex SHA-1 or 64-hex SHA-256 / `AXVCS` `RevisionId`) recorded in `axiom.lock` (`1065 §21, §53`, `PKG-INV-29`). Mutable branch or tag names MUST NOT appear as the locked revision identity (`PKG-INV-30`); in `--locked` or `--reproducible` mode, any VCS dependency lacking an immutable commit pin and `sha256` content hash in `axiom.lock` is rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "unpinned_vcs"`).
  3. **`PathSource(workspace_rel_path)`**: Declared via `path = "../core_math"`. The path MUST use `/` separators and normalize within the enclosing workspace or allowed local root without escaping via `..` (`1065 §22`). Packages published to a registry (`SPEC-112`) MUST NOT retain path-only dependencies lacking a `version` constraint.
  4. **`WorkspaceSource(member_rel_path)`**: Declared via `workspace = true`, inheriting the version constraint, source coordinate, and base features from `[workspace.dependencies]` in the workspace root `axiom.toml` (`1065 §23`).
  5. **`ArchiveSource(canonical_url, sha256_digest)`**: Declared via `archive = { url = "...", sha256 = "<hex>" }`. The `sha256` field is mandatory (`1065 §24`).
  6. **`VendorSource(vendor_rel_path, sha256_digest)`**: Materialized under `vendor/<namespace>/<name>-<version>/` and verified against the locked `sha256` content digest (`0098 §44`, `APKG-44`).
  By default, `AXPACKAGE` prefers `Source` (or `SourceWithCache`) resolution (`1065 §26–§27`). Prebuilt binary `.axlib` artifacts may be selected only when their `TargetFingerprint`, `AbiFingerprint`, compiler schema version, and `SHA-256` digest match the active compilation target (`PKG-INV-21..23`, `APKG-55`).

- **AXS-PKG-004 (SemVer 2.0 Data Model, Grammar & Total Ordering — `REQ-PKG-022`)**:
  `compiler/pkg/semver` parses and compares package versions strictly according to Semantic Versioning 2.0.0 (`tasks/1065 §7–§11`, `tasks/0446 §187.7`, `PKG-INV-04`):
  ```
  SemVer       ::= Major "." Minor "." Patch ("-" PreRelease)? ("+" BuildMeta)?
  Major        ::= "0" | [1-9][0-9]*
  Minor        ::= "0" | [1-9][0-9]*
  Patch        ::= "0" | [1-9][0-9]*
  PreRelease   ::= PreIdent ("." PreIdent)*
  BuildMeta    ::= MetaIdent ("." MetaIdent)*
  PreIdent     ::= "0" | [1-9][0-9]* | [0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*
  MetaIdent    ::= [0-9A-Za-z-]+
  ```
  1. **Reject malformed versions**: Leading zeroes on numeric `Major`, `Minor`, `Patch`, or purely numeric `PreIdent` tokens (e.g. `01.2.3` or `1.0.0-01`), empty identifiers (`1.0.0-` or `1.0.0+`), or negative/overflowing $> 64$-bit integers MUST be rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "semver"`, `data.version`).
  2. **Canonical precedence order (`1065 §9–§11`, `PKG-INV-04`)**:
     - Compare `(major, minor, patch)` numerically: $(M_1, m_1, p_1) < (M_2, m_2, p_2)$ lexicographically.
     - A normal version has strictly higher precedence than a pre-release version with the same `(major, minor, patch)`: `1.0.0-alpha < 1.0.0`.
     - Two pre-release versions with equal `(major, minor, patch)` are compared left-to-right token by token:
       - Two numeric tokens are compared as unsigned integers (`2 < 10`).
       - Two non-numeric tokens are compared lexicographically by ASCII byte value (`"alpha" < "beta"`).
       - A numeric token always has lower precedence than a non-numeric token (`1 < "alpha"`).
       - If all compared tokens are equal, the version with fewer pre-release tokens has lower precedence (`1.0.0-alpha < 1.0.0-alpha.1`).
     - **Build metadata invariance (`1065 §10`)**: `+build` metadata does NOT affect version precedence (`1.2.0+build1` and `1.2.0+build2` have equal SemVer precedence). When the resolver must break ties between two registry candidates that share identical `(major, minor, patch, prerelease)` but carry distinct `+build` strings, it orders them deterministically by ASCII byte comparison of the canonical `+build` string.

- **AXS-PKG-005 (SemVer 2.0 Version Constraint Grammar & Evaluation)**:
  `compiler/pkg/semver` supports the following closed set of version constraint forms (`tasks/1065 §12–§17`, `PKG-INV-05`):
  1. **Caret compatibility constraint (`^M.m.p`, or bare `"M.m.p"` / `"M.m"` / `"M"` in `axiom.toml`)**:
     - `^M.m.p` with $M > 0$ matches $v$ iff $M.m.p \le v < (M+1).0.0\text{-0}$.
     - `^0.m.p` with $m > 0$ matches $v$ iff $0.m.p \le v < 0.(m+1).0\text{-0}$.
     - `^0.0.p` matches $v$ iff $v == 0.0.p$.
     - Partial caret forms expand missing components to zero before applying the rule (`^1.2` $\equiv$ `^1.2.0`; `^0.2` $\equiv$ `^0.2.0`; `^1` $\equiv$ `^1.0.0`; `^0` $\equiv$ `>=0.0.0, <1.0.0-0`).
  2. **Tilde patch-level constraint (`~M.m.p`, `~M.m`, `~M`)**:
     - `~M.m.p` matches $v$ iff $M.m.p \le v < M.(m+1).0\text{-0}$.
     - `~M.m` matches $v$ iff $M.m.0 \le v < M.(m+1).0\text{-0}$.
     - `~M` matches $v$ iff $M.0.0 \le v < (M+1).0.0\text{-0}$.
  3. **Exact and inequality comparators (`=`, `!=`, `<`, `<=`, `>`, `>=`)**:
     - `=M.m.p` (or `=M.m.p-pre`) matches only versions with equal `(major, minor, patch, prerelease)`.
     - `!=M.m.p` excludes that exact version.
     - `<`, `<=`, `>`, `>=` compare via the total SemVer precedence order (`AXS-PKG-004`).
  4. **Wildcards (`*`, `M.*`, `M.x`, `M.m.*`, `M.m.x`)**:
     - `*` matches any stable version $\ge 0.0.0$.
     - `M.*` / `M.x` matches $M.0.0 \le v < (M+1).0.0\text{-0}$.
     - `M.m.*` / `M.m.x` matches $M.m.0 \le v < M.(m+1).0\text{-0}$.
  5. **Compound conjunctions and disjunction sets (`1065 §12, §17`)**:
     - Comma-separated or whitespace-separated comparators (`">=1.2.0, <2.0.0, !=1.5.3"`) evaluate as logical conjunction ($\land$).
     - Pipe-separated clauses (`"^1.4.0 || ^2.0.0"`) evaluate as logical disjunction ($\lor$) of conjunction clauses.
  6. **Pre-release isolation rule (`1065 §9`)**: A candidate version with a non-empty `prerelease` tag (`X.Y.Z-pre`) satisfies a comparator clause if and only if at least one comparator in that conjunction clause explicitly specifies a pre-release tag on the exact same `(X, Y, Z)` tuple (for example, `>=1.2.0-alpha.1, <1.3.0` matches `1.2.0-alpha.2` and `1.2.0`, but does NOT match `1.3.0-alpha.1`; `^1.2.0` matches `1.2.0` and `1.3.0`, but NEVER matches `1.2.0-alpha.1` or `1.2.1-rc.1`).

---

## 2. Deterministic Dependency Resolver, Conflict Derivation Trees & Order Invariance

- **AXS-PKG-010 (Declaration-Order & Filesystem-Order Invariant Resolution — `REQ-PKG-020`, `REQ-PKG-022`, `REQ-PKG-024`)**:
  `compiler/pkg/resolver` is a pure, deterministic function of `(WorkspaceManifests, OptionalLockfile, RegistryIndexSnapshot, TargetSpec, RequestedFeatures, ResolutionPolicy)` (`0098 §9`, `tasks/0412 §3`, `tasks/0446 §187.8`, `tasks/1065 §47–§49`, `ADEP-20`, `PKG-INV-06`):
  1. Before constraint solving begins, all workspace root members, dependency tables (`[dependencies]`, `[dev-dependencies]`, `[build-dependencies]`, `[comptime-dependencies]`, `[target.'cfg(...)'.dependencies]`), `[workspace.dependencies]`, `[patch.*]` tables, and registry candidate lists are canonicalized into sorted arrays ordered by `(RegistryId, NamespaceId, PackageName, BuildEnvClass, DependencyScope)`.
  2. Permuting the order of lines/keys in `axiom.toml`, reordering directory entries on disk (`readdir`), or shuffling candidate order in a registry index response MUST produce the exact same `ResolvedPackageGraph` and byte-for-byte identical `axiom.lock`.
  3. Package resolution is strictly declarative and side-effect-free: the resolver MUST NOT execute any package source code, `[[build_tool]]`, or `comptime` function during dependency resolution (`1065 §199 PKG-INV-18`).

- **AXS-PKG-011 (Version Unification, Lockfile Preservation & Candidate Ordering)**:
  1. **Compatible track deduplication (`0098 §9`, `tasks/0661 §8`)**: Each package dependency is grouped into a SemVer compatibility track `CompatTrack(SemVer)`:
     - For $M \ge 1$: `CompatTrack(M.m.p) = MajorTrack(M)`.
     - For $M = 0, m \ge 1$: `CompatTrack(0.m.p) = ZeroMinorTrack(m)`.
     - For $M = 0, m = 0$: `CompatTrack(0.0.p) = ZeroPatchTrack(p)`.
     All constraints targeting the same `(RegistryId, NamespaceId, PackageName, CompatTrack, BuildEnvClass)` MUST resolve to a single unified version $v$ satisfying the intersection $\bigcap_i C_i$ of all active constraints on that track. If the intersection within the track is empty (e.g. package `A` requires `math >=1.2.0, <1.5.0` and package `B` requires `math ^1.6.0`), resolution fails with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "version_conflict"`).
  2. **Lockfile-preferring resolution (`tasks/0446 §187.6`, `1065 §51–§55`, `ADEP-21`, `PKG-INV-09`)**: When an existing `axiom.lock` is present and the user has NOT invoked `axiomc pkg update`, the solver MUST first test the locked version $v_{\text{lock}}$ for each `(RegistryId, NamespaceId, PackageName)` before considering any newer registry candidate. As long as $v_{\text{lock}}$ satisfies all current manifest constraints, `axiomc build|check|test|run|pkg lock` MUST preserve $v_{\text{lock}}$ unchanged.
  3. **Deterministic candidate tie-breaking (`1065 §123, §168–§169`)**: When no locked version applies (or during `axiomc pkg update`), candidate versions within a compatibility track are evaluated in strict descending SemVer precedence order (`highest compatible version first`), or strict ascending SemVer precedence order when `--minimal-versions` is passed. Yanked registry versions (`yanked = true`) are skipped unless already pinned in `axiom.lock`.

- **AXS-PKG-012 (PubGrub Conflict-Driven Clause Learning & Derivation Trees)**:
  `compiler/pkg/resolver` implements deterministic unit propagation and conflict-driven clause learning (PubGrub incompatibility resolution) (`tasks/0412 §149 APKG-49`, `tasks/1065 §47–§49`):
  1. Every requirement or unavailability is represented as a normalized `Incompatibility` over package terms (e.g., `{app_cli@0.2.0 requires http ^2.0.0}`, `{http >=2.0.0, <3.0.0 requires tls >=1.5.0, <2.0.0}`).
  2. When unit propagation encounters a conflict on package `P`, prior-cause resolution derives a root-cause incompatibility and backjumps deterministically to the highest decision level where propagation can resume.
  3. If the root incompatibility contains only the workspace root package(s), the dependency graph is unsatisfiable. The solver constructs a canonical, human-readable derivation tree explaining every step of the failure chain (`root -> intermediate_pkg@ver -> conflicting_pkg constraint`) and emits `AX_DRIVER_BAD_MANIFEST` with:
     - `data.kind = "version_conflict"`
     - `data.package = "<namespace>/<name>"`
     - `data.derivation_chain = ["<step_1>", "<step_2>", ...]`
     The derivation chain order is deterministic and independent of hash-map or filesystem order.

- **AXS-PKG-013 (Inter-Package Acyclicity & Declarative `[patch]` Overrides)**:
  1. **No package cycles (`0098 §50–§52`, `tasks/0446 §187.10–§187.11`, `1065 §199 PKG-INV-26`, `REQ-PKG-008`, `REQ-PKG-009`, `REQ-PKG-011`)**: Within any single `BuildEnvClass`, the resolved package dependency graph MUST be a strict DAG. Any cycle `P_0 -> P_1 -> ... -> P_0` along active `normal` (or active ` normal + dev` in test builds) edges MUST be rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "package_cycle"`, `data.cycle = "P_0 -> P_1 -> ... -> P_0"`).
  2. **Workspace `[patch]` overrides (`1065 §144–§147`)**: The workspace root `axiom.toml` MAY declare `[patch.<registry>]` tables overriding a dependency coordinate with a local `path` or commit-pinned `git` source for workspace-wide testing/auditing. Every active patch override MUST match a compatible SemVer version and MUST be recorded explicitly in `axiom.lock` under `[[patch_override]]` so dependency provenance remains 100% auditable (`APKG-48`, `PKG-INV-36`).

---

## 3. Side-by-Side Major-Version Isolation, Nominal Type Identity & Monotonic Feature Unification

- **AXS-PKG-020 (Side-by-Side Incompatible Major-Version Coexistence — `REQ-PKG-011`, `REQ-PKG-024`)**:
  When different packages in a workspace require incompatible `CompatTrack` tracks of the same package (for example, `graphics` depends on `math = "^1.2.0"` while `audio` depends on `math = "^2.0.0"`, or `0.2.x` vs `0.3.x`), `compiler/pkg/resolver` MUST NOT arbitrarily force a single version or reject the build when side-by-side isolation is permitted (`0098 §10`, `tasks/0661 §10`, `tasks/1065 §199 PKG-INV-25`):
  1. **Dual node instantiation**: The resolver instantiates one resolved `PackageNode` per active `(RegistryId, NamespaceId, PackageName, CompatTrack, BuildEnvClass)` tuple (e.g., `math@1.4.2` and `math@2.1.0`), binding `graphics`'s dependency edge to `math@1.4.2` and `audio`'s dependency edge to `math@2.1.0`.
  2. **Disjoint `CompilerDB` `PackageId` and mangled symbol namespaces (`SPEC-110 AXS-BLD-002`, `REQ-PKG-010`, `REQ-PKG-011`)**: Every resolved `PackageNode` receives a distinct `PackageId` in `CompilerDB` and a collision-free symbol mangling prefix `_AXP_<pkg_name>_v<major>_<minor>_<patch>_<id_hash8>_...`. Functions, statics, vtables, and generic instantiations in `math@1.4.2` and `math@2.1.0` link into the same final binary without symbol collisions (`AX_LINK_DUPLICATE_SYMBOL`).
  3. **Singleton native `links` exclusion**: If a package manifest declares `links = "<native_c_symbol_domain>"` (claiming exclusive linkage ownership of a native C/system static library), at most ONE version of any package declaring that `links` key may appear in a single `Target` or `Host` link graph. Resolving two distinct versions with the same `links` key MUST emit `AX_DRIVER_BAD_MANIFEST` (`data.kind = "duplicate_native_links"`, `data.links`, `data.packages`).

- **AXS-PKG-021 (Distinct Nominal Type Identity Across Package Versions — `0098 §11`, `APKG-22`, `REQ-PKG-011`)**:
  Nominal types (`struct`, `enum`, `union`, `trait`, opaque `type`) in `CompilerDB` are canonically keyed by `(PackageId, ModuleId, ItemDefId)` (`0098 §11`, `tasks/0446 §187.2, §187.160 APKG-22`, `tasks/0661 §10`):
  1. Even if `math@1.4.2` and `math@2.1.0` declare a `pub struct Vec2 { pub x: f64, pub y: f64 }` with identical source tokens and `@repr(C)` physical layouts, `TypeId(math@1.4.2, Vec2) != TypeId(math@2.1.0, Vec2)`.
  2. Passing a value of `math@1.4.2.Vec2` to a function parameter expecting `math@2.1.0.Vec2` (or attempting to satisfy a trait bound `math@2.1.0.Metric` using an implementation of `math@1.4.2.Metric`) MUST be rejected at type-checking time with `AX_TYPE_MISMATCH`:
     - `data.expected = "math@2.1.0.Vec2"`
     - `data.found = "math@1.4.2.Vec2"`
     - `data.reason = "distinct_package_versions"`
     The diagnostic attaches a secondary note identifying the two resolved package versions and the dependency edges that introduced them (`SPEC-103`).

- **AXS-PKG-022 (Explicit Public Dependency Re-Export Bridging — `0098 §12`, `APKG-24`)**:
  A package `graphics` may intentionally expose types, traits, or functions from a dependency `math` as part of its own public API by marking the dependency `public = true` in `axiom.toml` (`math = { version = "^1.4.0", public = true }`) and writing `pub use math.Vec2` in its source module (`0098 §12`, `tasks/0446 §187.160 APKG-24`, `tasks/0661 §4`):
  1. **Identity preservation across `pub use` (`APKG-24`)**: `pub use math.Vec2` aliases the original `TypeId(math@1.4.2, Vec2)` in `graphics`'s export table without minting a new nominal `TypeId`. Therefore, if `app` depends on `graphics` (which re-exports `math@1.4.2.Vec2`) and also depends directly on `math = "^1.0.0"` (which unifies to the same `math@1.4.2` node per `AXS-PKG-011`), `graphics.Vec2` and `math.Vec2` have the exact same `TypeId` and interoperate seamlessly without wrapper conversions.
  2. **Public dependency compatibility check**: When a dependency is marked `public = true`, its `SemanticInterfaceFingerprint` is folded into the declaring package's own `SemanticInterfaceFingerprint` (`AXS-PKG-002`), and any version split where two packages linked together exchange a re-exported type backed by different major versions (`math@1` vs `math@2`) is caught deterministically by `AXS-PKG-021`.

- **AXS-PKG-023 (Monotonic Additive Feature Unification & Host/Target Scope Isolation — `REQ-PKG-025`)**:
  `compiler/pkg/resolver` resolves package features after version unification and before `BuildGraph` construction (`0098 §13–§14`, `tasks/0661 §12–§13`, `tasks/1065 §40–§43`, `SPEC-110 AXS-BLD-014`, `ADEP-23`, `ADEP-24`):
  1. **Monotonic least fixed point per `(PackageId, BuildEnvClass)`**: For each resolved package instance `(P, env)` where `env` is either `Target(TargetTriple)` or `Host(HostTriple)`, the active feature set $F(P, \text{env})$ is the least fixed point of:
     $$F_0(P, \text{env}) = \bigcup_{(U, \text{env}) \xrightarrow{e} (P, \text{env})} \text{RequestedFeatures}(e)$$
     expanded transitively across `P`'s `[features]` implication rules (`feat_a = ["feat_b", "dep:opt_dep", "opt_dep/sub_feat"]`). If any incoming edge $e$ has `default_features = true` (the default when omitted), `"default"` is included in $\text{RequestedFeatures}(e)$; only when ALL incoming edges to `(P, env)` specify `default_features = false` (or `--no-default-features` on the root package) is `"default"` omitted unless explicitly named.
  2. **Strict `Host` vs `Target` and `dev` scope isolation (`REQ-PKG-004`..`REQ-PKG-007`, `PKG-INV-20`)**:
     - Features requested on `[build-dependencies]` or `[comptime-dependencies]` apply exclusively to `Host(HostTriple)` nodes and MUST NOT activate features on `Target(TargetTriple)` nodes of the same package.
     - Features requested on `[dev-dependencies]` edges are included ONLY when resolving test, benchmark, or example build graphs (`axiomc test|bench`), and MUST NOT pollute production `axiomc build|run` feature sets.
  3. **Explicit optional dependency activation (`1065 §43`, `PKG-INV-27..28`)**: A dependency declared with `optional = true` is included in the active `ResolvedPackageGraph` if and only if an active feature in $F(P, \text{env})$ enables `dep:<opt_name>` (or the implicit feature `<opt_name>`). Unactivated optional dependencies are never fetched, resolved, or compiled in minimal/targeted mode, though workspace-wide `axiom.lock` generation records their locked candidate coordinates when solvable so enabling the feature later under `--locked` remains deterministic.

- **AXS-PKG-024 (Feature Integrity & Core Language Semantic Non-Interference — `REQ-PKG-025`)**:
  Per `REQ-PKG-025`, `0098 §13, §18, §53`, `tasks/0412 §150 APKG-56..57`, `tasks/1065 §1, §30, §199 PKG-INV-38`, and `SPEC-110 AXS-BLD-015`:
  1. **Never silently disable required features (`REQ-PKG-025`)**: If any active dependency edge or CLI invocation requires feature `f` on package `P`, the resolver MUST NOT silently drop, ignore, or disable `f` when `f` is undeclared, when a target `@cfg` predicate disables an optional dependency required by `f`, or when `f` conflicts with another active feature (`conflicts_with = [...]` in `[features]`). Instead, resolution MUST fail immediately with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "unknown_feature" | "missing_required_feature" | "feature_conflict"`, `data.package`, `data.feature`).
  2. **Package metadata and features never alter core language semantics (`REQ-PKG-025`, `APKG-14`, `APKG-35`, `APKG-56`)**: Package manifests (`axiom.toml`), lockfiles (`axiom.lock`), registry metadata, and feature flags MUST NOT alter Axiom's lexical or grammatical rules (`SPEC-01`, `SPEC-02`), type promotion lattice (`SPEC-40`, `SPEC-41`), ownership/move/view capability checking (`SPEC-10`..`SPEC-12`), concurrency race verification (`SPEC-30`), or safety profile rules (`SPEC-53`). Features control compilation exclusively through explicit `@cfg(feature = "<name>")` conditional compilation attributes in `.ax` source files (`SPEC-88`).

---

## 4. Canonical `axiom.lock` v1 Specification, Content-Addressed Store & Air-Gapped Vendoring

- **AXS-PKG-030 (Canonical `axiom.lock` v1 Schema & Deterministic Serialization — `REQ-PKG-022`)**:
  `std/pkg/lockfile` reads and writes the workspace lockfile `axiom.lock` at the workspace root (`0098 §5–§6`, `tasks/0412 §6`, `tasks/0446 §187.5–§187.6, §187.150`, `tasks/1065 §51–§54`, `PKG-INV-07..08`). A valid `axiom.lock` file is UTF-8 encoded without BOM, uses `LF` (`\n`) line endings, and conforms to the following canonical v1 schema:
  ```toml
  # This file is automatically @generated by axiomc pkg. Do not edit manually.
  lock_version = 1
  resolver = "1"
  sdk_fingerprint = "blake3:4a90e1c27b8f03d16e52a49c8107f3d29b1c4e8a7f06d52319a8c4e7b2d10f63"
  graph_hash = "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"

  [[package]]
  registry = "default"
  namespace = "default"
  name = "app_cli"
  version = "0.2.0"
  source = "workspace:crates/app_cli"
  sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  sif = "blake3:1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef01"
  env = "target"
  target_condition = "*"
  features = ["default", "simd"]
  dependencies = [
      "default/core_math@0.2.0 (workspace:crates/core_math) [normal]",
      "axiom/crypto@1.4.2 (registry:default) [normal]",
      "axiom/crypto@2.0.1 (registry:default) [normal]",
  ]

  [[package]]
  registry = "default"
  namespace = "axiom"
  name = "crypto"
  version = "1.4.2"
  source = "registry:default"
  sha256 = "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
  sif = "blake3:8899aabbccddeeff00112233445566778899aabbccddeeff0011223344556677"
  env = "target"
  target_condition = "*"
  features = ["constant_time", "default"]
  dependencies = []

  [[package]]
  registry = "default"
  namespace = "axiom"
  name = "crypto"
  version = "2.0.1"
  source = "registry:default"
  sha256 = "4fc82b26aecb47d2868c4efbe3581732a3e7cbcc6c2efb32062c08170a05eeb8"
  sif = "blake3:fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
  env = "target"
  target_condition = "*"
  features = ["aead", "default"]
  dependencies = []
  ```
  Canonical serialization rules:
  1. **Lexicographical entry sorting (`PKG-INV-07..08`)**: All `[[package]]` blocks MUST be sorted by `(namespace, name, version, source, env)` where `version` is ordered by SemVer 2.0 total order (`AXS-PKG-004`) and all other fields by ASCII byte order.
  2. **Sorted arrays**: Inside each `[[package]]` block, `features` and `dependencies` MUST be deduplicated and sorted in ascending ASCII byte order. Each string in `dependencies` has the canonical format `"<namespace>/<name>@<version> (<source>) [<scope>]"`.
  3. **`sdk_fingerprint` and `graph_hash`**:
     - `sdk_fingerprint` records the active toolchain/sysroot compatibility fingerprint (`SysrootFingerprint` per `SPEC-88 AXS-XCMP-023`).
     - `graph_hash` is the lowercase hex `sha256:<64-hex>` digest computed over the canonical normalized serialization of `lock_version`, `resolver`, `sdk_fingerprint`, all `[[package]]` records, and any `[[patch_override]]` records (`1065 §54, §140`).

- **AXS-PKG-031 (`--locked` / `--frozen` Drift Detection & Tamper Verification)**:
  1. When `--locked` or `--frozen` is passed to `axiomc build|check|run|test|bench|graph` or `axiomc pkg lock --check` / `axiomc pkg verify-lock` (`tasks/0446 §187.6`, `1065 §54–§55`, `PKG-INV-09`):
     - `axiom.lock` MUST exist at the workspace root and parse cleanly under `lock_version = 1`.
     - The recomputed `graph_hash` over `axiom.lock`'s entries MUST equal the stored `graph_hash` field; any mismatch is rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "lockfile_corrupt"`).
     - Re-running constraint and feature verification against `axiom.toml` MUST confirm that every root/member dependency constraint, active feature set, and `[patch]` override is satisfied by the exact entries in `axiom.lock` with zero added, removed, or re-versioned packages. Any discrepancy is rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "lockfile_drift"`, `data.detail`), and `axiom.lock` is never modified on disk.
  2. AI tools and automated refactoring commands (`SPEC-102`, `SPEC-103`) MUST NOT silently modify `axiom.lock` or bypass lockfile verification (`1065 §199 PKG-INV-39`).

- **AXS-PKG-032 (SHA-256 Content-Addressed Package Store & Archive Safety)**:
  `std/pkg/store` manages the local content-addressed package store under `.axiom/cache/pkg/sha256/<byte0_hex>/<byte1_hex>/<full_sha256_hex>/` (`0098 §6, §24`, `tasks/0412 §9–§10, §113–§115, §134–§139`, `tasks/1065 §57–§60, §114–§115`, `PKG-INV-12..16`):
  1. **Content-addressed lookup only (`0098 §24`, `tasks/0412 §9–§10`)**: Package cache entries are keyed strictly by their 256-bit `SHA-256` content digest (`sha256`), never by package name or archive filename alone. Identical package contents across mirrors deduplicate to the same `sha256` object (`1065 §59`, `PKG-INV-34`).
  2. **Mandatory pre-use SHA-256 verification (`APKG-45`, `PKG-INV-12`)**: Before loading any package from `.axiom/cache/pkg/`, a downloaded archive, or a `vendor/` directory, `std/pkg/store` computes its canonical `SHA-256` digest and compares it against the expected `sha256` recorded in `axiom.lock`. If the computed digest differs, the store refuses to use the package and emits `AX_DRIVER_BAD_MANIFEST` (`data.kind = "hash_mismatch"`, `data.package`, `data.expected_sha256`, `data.found_sha256`).
  3. **Sandboxed extraction & path-traversal rejection (`1065 §114–§115`, `APKG-47`, `PKG-INV-14..16`)**:
     - Archive extraction is performed entirely in memory / capability-scoped `FsCap` bounded to a temporary staging directory `<store_entry>.tmp.<pid>` before atomic rename (`SPEC-110 AXS-BLD-033`).
     - Any archive entry containing an absolute path (`/`, `C:\`), parent traversal segment (`..`), device node, or symlink/hardlink escaping the package root is rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "path_traversal"`, `data.entry`).
     - Decompression enforces deterministic resource limits (default max archive size `64 MiB`, max uncompressed total `256 MiB`, max compression ratio `100:1`, max file count `16,384`; `1065 §115`) to prevent archive bombs.
     - Extracted file modification timestamps are normalized to `mtime = 0` (`1065 §134–§135`), and no file from an extracted package is ever executed during resolution or extraction (`PKG-INV-16`).

- **AXS-PKG-033 (Air-Gapped `--offline` & `vendor/` Directory Materialization — `REQ-PKG-013`)**:
  To support air-gapped and hermetic enterprise/OS builds (`0098 §43–§44`, `tasks/0446 §187.158–§187.160 ADIST-21, ADIST-28`, `tasks/1065 §56, §170–§171`, `APKG-20..21`, `APKG-43..44`, `PKG-INV-10..11`):
  1. **`axiomc pkg vendor [<dir>]` (default `vendor/`)**: Exports every non-workspace dependency in `axiom.lock` from `.axiom/cache/pkg/` into `<dir>/<namespace>/<name>-<version>/` in canonical lexicographical order, and writes `<dir>/axiom-vendor.toml` mapping each `(namespace, name, version, source)` to its relative vendor directory and `sha256` digest. Vendoring preserves the original `PackageIdentity` (`APKG-44`) so builds using `vendor/` produce byte-for-byte identical binaries to builds using `.axiom/cache/pkg/`.
  2. **`--offline` and `--vendor` execution (`PKG-INV-10..11`)**:
     - Under `--offline`, `AXPACKAGE` forbids all network I/O (`NetCap = Denied`). Resolution reads only workspace manifests, `axiom.lock`, `vendor/` (when present), and `.axiom/cache/pkg/`.
     - Under `--vendor` (or when `[workspace].vendor = "vendor"` is configured), `std/pkg/store` resolves all external packages directly from `vendor/`, verifying each package's `SHA-256` digest against both `axiom.lock` and `vendor/axiom-vendor.toml`.
     - If any locked package is missing from `vendor/` and `.axiom/cache/pkg/` while `--offline` or `--vendor` is active, the command fails immediately with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "offline_missing_package"`, `data.package`, `data.sha256`; corpus shorthand `PACKAGE_NOT_CACHED` in `1065 §56`).

---

## 5. `axiomc pkg` CLI Subcommands, Diagnostics, Examples & Verification Matrix

- **AXS-PKG-040 (`axiomc pkg` Management CLI Subcommands)**:
  `compiler/driver/pkg_cmd` implements the `axiomc pkg <subcommand>` CLI suite (`tasks/0446 §187.151`, `tasks/1065 §121–§123, §182–§190`, `T856`):
  1. **`axiomc pkg init [--name <name>] [--lib | --bin] [--workspace]`**: Creates a canonical `axiom.toml` (and `src/main.ax` or `src/lib.ax` in canonical `=` / `.` syntax) in the current or specified directory. Fails with `AX_DRIVER_BAD_MANIFEST` if `axiom.toml` already exists.
  2. **`axiomc pkg add <spec> [--dev | --build | --comptime] [--features <f1,f2>] [--no-default-features] [--optional] [--public] [--path <dir> | --git <url> --rev <oid>]`**: Parses `<spec>` (`<name>@<constraint>` or `<namespace>/<name>@<constraint>`), inserts or updates the dependency entry in the appropriate scope table of `axiom.toml` in canonical key order, runs the SemVer 2.0 resolver (`compiler/pkg/resolver`), and atomically updates `axiom.lock`.
  3. **`axiomc pkg remove <name> [--dev | --build | --comptime]`**: Removes the dependency entry from `axiom.toml`, re-resolves the workspace graph to prune orphaned transitive dependencies, and atomically updates `axiom.lock`.
  4. **`axiomc pkg update [<pkg_spec>...] [--minimal-versions] [--dry-run]`**: Re-solves `axiom.toml` constraints against available candidates (`1065 §121–§123`). When `<pkg_spec>` is specified (e.g. `axiomc pkg update axiom/crypto@1.4.2`), performs a selective minimal update that upgrades only the named package (and any transitive dependencies forced by that upgrade) while keeping all other `axiom.lock` entries pinned.
  5. **`axiomc pkg lock [--check] [--offline]`**: Computes the resolved dependency graph and writes `axiom.lock` atomically without invoking compilation. With `--check`, behaves identically to `verify-lock`.
  6. **`axiomc pkg verify-lock [--offline] [--verify-store]`**: Validates `axiom.lock` schema v1, `graph_hash`, zero drift against `axiom.toml`, and (with `--verify-store` or `--offline`) verifies the `SHA-256` content digest of every locked package in `.axiom/cache/pkg/` or `vendor/`.
  7. **`axiomc pkg tree [--duplicates] [--invert <pkg>] [--edges normal|dev|build|comptime|all] [--format text|json]`**: Displays the resolved dependency graph in deterministic sorted tree order (`AXS-PKG-010`), annotating each node with its resolved version, source coordinate, active features, and `(host)` / `(target)` environment tag. `--duplicates` lists only packages with multiple side-by-side resolved versions (`AXS-PKG-020`); `--invert <pkg>` prints all causal dependency paths from workspace roots to `<pkg>`.
  8. **`axiomc pkg vendor [<dir>] [--verify]`**: Materializes or verifies the offline `vendor/` tree (`AXS-PKG-033`).

- **AXS-PKG-050 (Diagnostic Mapping)**:
  `compiler/pkg/semver`, `compiler/pkg/resolver`, `std/pkg/lockfile`, `std/pkg/store`, and `compiler/driver/pkg_cmd` map all `AXPACKAGE` error conditions to the canonical `DRIVER`, `TYPE`, `NAME`, `LINK`, `IO`, and `ICE` diagnostic codes registered in `compiler/diag/code.ax` (`spec/diagnostics.md` §3 `AXD-021`, §10–§11):

  | Corpus / Task Shorthand | Canonical `AX_<AREA>_<NAME>` | Area | Sev | Exit | Trigger Condition & Structured `data` Fields |
  |---|---|---|---|---|---|
  | `AXPKG_SEMVER`, `E_INVALID_SEMVER` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Malformed SemVer 2.0 version literal (leading zeroes, invalid pre-release/build token) or invalid version constraint expression (`AXS-PKG-004..005`; `data.kind = "semver"`, `data.version` / `data.constraint`). |
  | `AXPKG_CONFLICT`, `E_VERSION_CONFLICT` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Unsatisfiable SemVer version constraints within a compatibility track or missing candidate version, accompanied by a deterministic PubGrub conflict derivation tree (`AXS-PKG-011..012`; `data.kind = "version_conflict"`, `data.package`, `data.derivation_chain`). |
  | `AXPKG_FEATURE`, `E_FEATURE_CONFLICT` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Undeclared feature, mutually exclusive `conflicts_with` feature activation, or required feature that cannot be satisfied (`AXS-PKG-023..024`, `REQ-PKG-025`; `data.kind = "unknown_feature" \| "feature_conflict" \| "missing_required_feature"`, `data.package`, `data.feature`). |
  | `AXPKG_CYCLE`, `E_PKG_CYCLE` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Inter-package dependency cycle `P0 -> P1 -> ... -> P0` (`AXS-PKG-013`, `REQ-PKG-008`, `REQ-PKG-011`; `data.kind = "package_cycle"`, `data.cycle`). |
  | `AXPKG_NATIVE_LINKS` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Two side-by-side resolved packages in the same link graph declare the same singleton `links = "<native_lib>"` key (`AXS-PKG-020`; `data.kind = "duplicate_native_links"`, `data.links`). |
  | `AXPKG_TYPE_VERSION_MISMATCH` | `AX_TYPE_MISMATCH` | `TYPE` | `error` | `1` | Value or trait from `pkg@v1` used where nominal type/trait from side-by-side `pkg@v2` is expected without an unified re-export bridge (`AXS-PKG-021..022`; `data.expected`, `data.found`, `data.reason = "distinct_package_versions"`). |
  | `AXPKG_LOCK_DRIFT`, `AXPKG_LOCK_CORRUPT` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Missing `axiom.lock`, invalid `lock_version`, `graph_hash` tamper mismatch, or manifest-vs-lockfile drift under `--locked` / `verify-lock` (`AXS-PKG-030..031`; `data.kind = "lockfile_drift" \| "lockfile_corrupt"`). |
  | `AXPKG_HASH_MISMATCH` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Computed `SHA-256` content digest of a cached, fetched, or vendored package does not match the `sha256` recorded in `axiom.lock` (`AXS-PKG-032`; `data.kind = "hash_mismatch"`, `data.package`, `data.expected_sha256`, `data.found_sha256`). |
  | `AXPKG_UNPINNED_VCS` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | VCS/Git dependency uses a mutable branch/tag without an immutable commit `rev` pin and `sha256` digest in reproducible/`--locked` mode (`AXS-PKG-003`; `data.kind = "unpinned_vcs"`, `data.package`). |
  | `PACKAGE_NOT_CACHED`, `AXPKG_OFFLINE_MISSING` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Required package content is absent from `vendor/` and `.axiom/cache/pkg/` under `--offline` or `--vendor` (`AXS-PKG-033`, `1065 §56`; `data.kind = "offline_missing_package"`, `data.package`). |
  | `AXPKG_PATH_TRAVERSAL` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Package name, manifest path, or archive entry contains `..`, absolute paths, escaping symlinks, or exceeds decompression quotas (`AXS-PKG-002`, `AXS-PKG-032`; `data.kind = "path_traversal" \| "archive_quota_exceeded"`). |
  | `AXPKG_CLI_USAGE` | `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` | `DRIVER` | `error` | `2` | Invalid `axiomc pkg` subcommand or flag combination (`AXS-PKG-040`). |

- **AXS-PKG-051 (Positive Canonical Examples)**:
  1. **Side-by-side incompatible major versions (`math@1.4.2` and `math@2.0.1`) with explicit re-export façade (`AXS-PKG-020..022`)**:
     ```axiom
     // Package `math` v1.4.2: src/lib.ax
     module math

     pub struct Vec2 {
         pub x: f64,
         pub y: f64,
     }

     pub fn length_sq_v1(v: view<Vec2>) -> f64 {
         return (v.x * v.x) + (v.y * v.y)
     }
     ```
     ```axiom
     // Package `math` v2.0.1: src/lib.ax
     module math

     pub struct Vec2 {
         pub x: f64,
         pub y: f64,
     }

     pub fn dot_v2(a: view<Vec2>, b: view<Vec2>) -> f64 {
         return (a.x * b.x) + (a.y * b.y)
     }
     ```
     ```axiom
     // Package `legacy_physics` (depends on math = "^1.4.0"): src/lib.ax
     module legacy_physics

     use math.Vec2
     use math.length_sq_v1

     pub fn kinetic_factor(dx: f64, dy: f64) -> f64 {
         let v = Vec2 { x: dx, y: dy }
         return length_sq_v1(v.as_view())
     }
     ```
     ```axiom
     // Package `app` (depends on legacy_physics = "^0.1.0" and math = "^2.0.0"): src/main.ax
     module app

     use legacy_physics.kinetic_factor
     use math.Vec2
     use math.dot_v2

     pub fn main() -> i32 {
         let e1: f64 = kinetic_factor(3.0, 4.0)
         let p = Vec2 { x: 2.0, y: 5.0 }
         let e2: f64 = dot_v2(p.as_view(), p.as_view())
         if e1 == 25.0 && e2 == 29.0 {
             return 0
         }
         return 1
     }
     ```
     `compiler/pkg/resolver` resolves both `math@1.4.2` (bound to `legacy_physics`) and `math@2.0.1` (bound to `app`) in `axiom.lock`, mangles their symbols under distinct `PackageId` hashes, and links the resulting binary cleanly with zero runtime package manager dependency (`REQ-PKG-024`).

- **AXS-PKG-052 (Negative Canonical Examples)**:
  1. **Unsatisfiable SemVer diamond within the same compatibility track (`AXS-PKG-011..012`)**:
     - `app` depends on `net_http = "^1.0.0"` and `tls_core = ">=1.6.0, <2.0.0"`.
     - `net_http@1.2.0` (the only available `1.x` version) depends on `tls_core = ">=1.2.0, <1.5.0"`.
     - Because both `tls_core` constraints target `MajorTrack(1)` and `([1.6.0, 2.0.0) ∩ [1.2.0, 1.5.0)) == ∅`, `compiler/pkg/resolver` rejects the graph with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "version_conflict"`, `data.package = "default/tls_core"`, `data.derivation_chain = ["app@0.1.0 requires net_http ^1.0.0 -> net_http@1.2.0 requires tls_core >=1.2.0, <1.5.0", "app@0.1.0 requires tls_core >=1.6.0, <2.0.0"]`).
  2. **Rejected cross-major nominal type confusion (`AXS-PKG-021`)**:
     ```axiom
     // If `legacy_physics` exposes `pub fn make_v1() -> math_v1.Vec2`
     // and `app` passes that return value into `math_v2.dot_v2`:
     module app

     use legacy_physics.make_v1
     use math.dot_v2

     pub fn bad() -> f64 {
         let v1 = make_v1()
         return dot_v2(v1.as_view(), v1.as_view()) //~ ERROR AX_TYPE_MISMATCH (data.reason = "distinct_package_versions")
     }
     ```
  3. **Rejected silent disabling of required feature or `--locked` drift (`AXS-PKG-024`, `AXS-PKG-031`, `REQ-PKG-025`)**:
     - `app/axiom.toml` declares `crypto = { version = "^2.0.0", features = ["fips_hw"] }`, where `crypto@2.0.1` declares `[features] fips_hw = []` with `conflicts_with = ["software_only"]`, and another active dependency requests `crypto = { version = "^2.0.0", features = ["software_only"] }`.
     - Resolution halts with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "feature_conflict"`, `data.package = "axiom/crypto"`, `data.feature = "fips_hw"`).

- **AXS-PKG-053 (E20.2 Implementation & Verification Matrix)**:

  | Task | Role | Deliverable Scope & Allowed Paths | Primary Invariant & Verification Suite |
  |---|---|---|---|
  | `T855` | `axiom-semantics` | `compiler/pkg/semver`, `compiler/pkg/resolver`, `tests/run/pkg_resolver`: SemVer 2.0 parser/comparator & constraint evaluator (`AXS-PKG-004..005`), declaration-order-independent PubGrub constraint solver with conflict derivation trees (`AXS-PKG-010..013`), side-by-side incompatible major-version coexistence & nominal `TypeId` isolation (`AXS-PKG-020..022`), and monotonic `Host`/`Target`-isolated feature unification (`AXS-PKG-023..024`, `REQ-PKG-025`). | `INV-PKG-001` (`tests/run/pkg_resolver`) |
  | `T856` | `axiom-stdlib` | `std/pkg/lockfile`, `std/pkg/store`, `compiler/driver/pkg_cmd`, `tests/run/pkg_lockfile`: Canonical `axiom.lock` v1 parser/serializer & `--locked` drift/tamper verifier (`AXS-PKG-030..031`), `SHA-256` content-addressed package store with pre-use digest verification & sandboxed extraction (`AXS-PKG-032`), air-gapped `--offline` & `vendor/` materialization (`AXS-PKG-033`), and `axiomc pkg init\|add\|remove\|update\|lock\|tree\|verify-lock\|vendor` CLI (`AXS-PKG-040`). | `INV-PKG-002` (`tests/run/pkg_lockfile`) |
  | `T857` | `axiom-qa` | `tests/conformance/p20/e20_2_package_manager_lockfile`: End-to-end E20.2 conformance suite certifying `REQ-ECO-8736`, `REQ-PKG-022`, `REQ-PKG-024`, and `REQ-PKG-025` across SemVer 2.0 diamond resolution, conflict derivation trees, order invariance, monotonic feature unification, side-by-side major-version isolation, `axiom.lock` reproducibility, air-gapped `vendor/` builds, and `--interp` vs native equivalence (`0 WEAK-NATIVE`). | `INV-PKG-003` (`tests/conformance/p20/e20_2_package_manager_lockfile`) |

## Sources
0098 (`§1`–`§15`, `§20`–`§24`, `§41`–`§45`, `§50`–`§53`, `§60` `APKG-01..35`); tasks/0412 (BOOTSTRAP-153: `§1`–`§15`, `§139`–`§150` `APKG-20..60`); tasks/0446 (BOOTSTRAP-187: `§187.1`–`§187.15`, `§187.150`–`§187.160` `APKG-20..24`, `ADEP-20..27`, `ADIST-20..28`); tasks/0661 (BOOTSTRAP-402: `§4`–`§17`); tasks/1065 (BOOTSTRAP-800 `AXPACKAGE`: `§1`–`§63`, `§114`–`§153`, `§168`–`§200`, `PKG-INV-01..40`); `spec/requirements/CATALOG.md` (`REQ-ECO-8736`, `REQ-PKG-001`..`REQ-PKG-025`); `ADR-0006`; `ADR-0007`; `SPEC-03`; `SPEC-21`; `SPEC-22`; `SPEC-24`; `SPEC-88`; `SPEC-89`; `SPEC-102`; `SPEC-103`; `SPEC-110`; `spec/diagnostics.md`; `spec/invariants.md`.
