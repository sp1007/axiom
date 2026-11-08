# SPEC-112 — Canonical Package Registry Protocol, Deterministic `.axpkg` Content-Addressed Archive, Precompiled `.axmeta` Binary/Interface Distribution, Offline Mirrors & Transactional Rollback Specification

- **Status**: Normative
- **Phase**: P20 (E20.3 — Package Registry Protocol, `.axpkg` Archive, Offline Mirror & Distribution Runtime)
- **Rules**: `AXS-REG-001` .. `AXS-REG-053`
- **Requirements**: `REQ-ECO-8736`, `REQ-PKG-024` (and related artifact/package contracts `REQ-PKG-010`..`REQ-PKG-017`, `REQ-PKG-022`, `REQ-PKG-025`, `REQ-LNK-479`..`REQ-LNK-481`, `REQ-LNK-526`..`REQ-LNK-529`, `REQ-LNK-617`..`REQ-LNK-622`)

## Tóm tắt

Đặc tả này quy định kiến trúc chính tắc cho giao thức kho lưu trữ gói ứng dụng bản địa (Native Application Package Registry), định dạng tệp lưu trữ phân phối tất định có địa chỉ nội dung `.axpkg` (`std/pkg/archive`), giao thức chỉ mục thưa tĩnh (`std/pkg/registry`), định tuyến đa kho lưu trữ có ghim không gian tên chống tấn công nhầm lẫn phụ thuộc (`compiler/pkg/distribution`), tiêu thụ gói nhị phân/giao diện biên dịch sẵn qua `.axmeta`/`.axmi`, kho gương ngoại tuyến (`mirror`), và cơ chế kênh cập nhật / hoàn nguyên giao dịch (transactional rollback) cùng giao diện dòng lệnh `axiomc pkg publish|fetch|verify|search|mirror|rollback` (`compiler/driver/registry_cmd`):

1. **Ranh giới kiến trúc giữa trình biên dịch cốt lõi và kho lưu trữ gói (`AXS-REG-001`..`AXS-REG-004`)**: Trình biên dịch cốt lõi (`CompilerDB`, `BuildGraph`) không bao giờ thực hiện lời gọi mạng ngầm định trong quá trình biên dịch (`REQ-ECO-8736`, `REQ-PKG-024`). Việc tìm nạp gói là một bước tiền dựng tường minh, được xác thực mã băm nội dung trước khi biên dịch. Kho lưu trữ gói hoàn toàn là tầng phân phối tùy chọn: các ứng dụng Axiom biên dịch ra mã máy chạy độc lập mà không cần kết nối mạng, tài khoản đám mây, trình nền chợ ứng dụng hay trình quản lý gói thời gian chạy (`tasks/0858 §1–§10, §308`).
2. **Định dạng lưu trữ `.axpkg` tất định và cây băm Merkle SHA-256 (`AXS-REG-010`..`AXS-REG-013`)**: Mỗi gói `.axpkg` bắt đầu bằng `ArtifactHeader` 64-byte chuẩn (`magic = "AXPKG001"`, `SPEC-24`), chứa bản kê `axiom.toml` chuẩn hóa, tóm tắt giao diện `.axmeta`/`.axmi`, bảng mục tệp sắp xếp theo thứ tự từ điển đường dẫn tương đối POSIX (`/`), dấu thời gian sửa đổi bằng `0` (`mtime = 0`), quyền tệp chuẩn hóa (`0644`/`0755`), và mã băm gốc `merkle_root` SHA-256 tính trên cây Merkle nhị phân của toàn bộ tệp (`tasks/0412 §9–§10`, `tasks/0858 §15–§17`). Mọi phiên bản gói đã xuất bản là bất biến vĩnh viễn.
3. **Tiêu thụ gói mã nguồn, gói nhị phân biên dịch sẵn (`.axmeta`/`.axmi` + `.axlib`) và gói lai (`AXS-REG-020`..`AXS-REG-023`)**: Hỗ trợ ba chế độ phân phối (`Source`, `Binary`, `Hybrid`) (`tasks/0665 §8`, `tasks/0739 §493.1–§493.51`). Khi tiêu thụ gói nhị phân, `CompilerDB` nạp trực tiếp tệp giao diện `.axmi`/`.axmeta` (chứa các kiểu `pub`, bố cục `@repr`, bảng `Trait`/`impl`, hợp đồng quyền sở hữu/capability/effect, hằng số và mẫu `Verified MIR` cho hàm tổng quát) mà không cần phân tích lại mã nguồn, đồng thời kiểm tra nghiêm ngặt bộ ba dấu vân tay (`ApiFingerprint`, `SemanticInterfaceFingerprint`, `AbiFingerprint`) và `TargetFingerprint` trước khi liên kết.
4. **Giao thức chỉ mục thưa (`AXPACKAGE_PROTOCOL_1`), định tuyến đa kho lưu trữ và kho gương ngoại tuyến (`AXS-REG-030`..`AXS-REG-032`)**: Chỉ mục kho lưu trữ sử dụng các tệp dòng JSON tĩnh (`index/<namespace>/<prefix2>/<name>.jsonl`) và kho đối tượng theo địa chỉ nội dung (`blobs/sha256/<b0>/<b1>/<sha256>.axpkg`). Cấu hình đa kho lưu trữ tách biệt rõ `priority` (độ ưu tiên tìm kiếm) với `TrustPolicy` và danh sách ghim không gian tên (`pinned_namespaces`), ngăn chặn tuyệt đối kho lưu trữ độ ưu tiên thấp hoặc công cộng giả mạo các gói nội bộ (`tasks/0858 §11–§14`).
5. **Kênh cập nhật, thế hệ cài đặt nguyên tử và hoàn nguyên giao dịch an toàn dữ liệu (`AXS-REG-033`..`AXS-REG-053`)**: Quản lý các kênh phát hành (`stable`, `beta`, `preview`, `nightly`, `internal`), nhật ký giao dịch `.axupdate-journal`, chuyển đổi con trỏ thế hệ nguyên tử (`active -> gen_<N>`), và hoàn nguyên (`rollback`) về thế hệ đã xác thực trước đó mà không bao giờ xóa hoặc làm hỏng dữ liệu người dùng (`tasks/0858 §25–§40, §63–§90`).

---

## 1. Architectural Boundary, Registry Optionality & Compile-Time-Only Pre-Build Fetching

- **AXS-REG-001 (Core Compiler vs Package Registry Boundary — `REQ-ECO-8736`, `REQ-PKG-024`)**:
  1. **Zero implicit network access during compilation (`tasks/0412 §8, §57–§58`, `tasks/0665 §1–§2`, `tasks/0858 §1–§4, §308`, `tasks/1065 §170, §191–§192`, `PKG-INV-10`, `PKG-INV-38`)**: The Axiom compiler core (`CompilerDB` in `SPEC-21`, `BuildGraph` execution in `SPEC-110`) operates exclusively on resolved, local, content-verified inputs. Neither lexing, parsing, name resolution, type checking, `comptime` evaluation (`SPEC-60`), optimization, code generation, nor linking may ever open a network socket, query a remote package registry, or download missing dependencies on the fly (`NetCap = Denied`).
  2. **Explicit pre-build fetch & verification boundary (`tasks/0412 §58`, `tasks/1065 §50–§60`)**: Package registry communication occurs exclusively during explicit package-management phases (`axiomc pkg fetch|add|update|publish|mirror|search` or the pre-build dependency staging step when online resolution is permitted). Before `BuildGraph` construction (`SPEC-110 AXS-BLD-020`) begins, every external package in `axiom.lock` MUST already reside in the local content-addressed store (`.axiom/cache/pkg/sha256/...`) or offline `vendor/` directory and MUST have passed `SHA-256` Merkle digest verification (`SPEC-111 AXS-PKG-032`).
  3. **Optional distribution layer & zero runtime dependency (`tasks/0858 §2–§3, §304 #1–4, #40, §308`, `REQ-PKG-013`, `REQ-PKG-016`, `REQ-PKG-024`, `PKG-INV-19`)**: The package registry and distribution runtime are strictly optional ecosystem services. Compiling and executing an Axiom program or workspace requires no public marketplace, no online account, no background package daemon, no telemetry, and no license activation server. Native binaries produced by `axiomc` have zero runtime dependency on `std/pkg/*` unless the application itself explicitly imports `std.pkg` to act as a package/extension host (`tasks/0858 §308–§309`).

- **AXS-REG-002 (Taxonomy of Package, Repository, Registry & Distribution Profiles)**:
  Refining `SPEC-110 AXS-BLD-001` and `SPEC-111 AXS-PKG-002`, the distribution architecture maintains a strict separation of responsibilities (`tasks/0665 §2`, `tasks/0858 §5–§8, §307`, `tasks/1065 §1–§6`):
  1. **`Package` (Immutable Distributable Unit)**: A versioned, content-addressed bundle (`.axpkg`) identified by the 7-tuple `PackageIdentity = (RegistryId, NamespaceId, PackageName, SemVer, PackageSourceId, ContentHash, SemanticInterfaceFingerprint)` (`SPEC-111 AXS-PKG-002`).
  2. **`Repository` (Storage & Transport Endpoint)**: A concrete storage source implementing the transport-neutral `Repository` contract (`query_index`, `fetch_metadata`, `download_blob`, `verify_snapshot`; `tasks/0858 §7–§8`, `tasks/1065 §184`). Supported repository kinds are:
     - `RepositoryKind.LocalDirectory`: A directory on the local filesystem containing a sparse index and `.axpkg` blobs.
     - `RepositoryKind.FileArchive`: A single-file offline repository bundle (`.axrepo`).
     - `RepositoryKind.HttpSparse`: A static or dynamic HTTP/HTTPS server serving the `AXPACKAGE_PROTOCOL_1` sparse index layout (`AXS-REG-030`).
     - `RepositoryKind.Mirror`: A read-only content-verified mirror of one or more upstream registries (`AXS-REG-032`).
     - `RepositoryKind.VendorStore`: A workspace-local `vendor/` tree (`SPEC-111 AXS-PKG-033`).
  3. **`Registry` (Logical Index & Namespace Authority)**: A named logical authority (`RegistryId`, e.g., `"default"`, `"corp_internal"`) whose metadata index maps `(NamespaceId, PackageName, SemVer)` coordinates to immutable `ContentHash` (`merkle_root`) and `SemanticInterfaceFingerprint` digests. A single `RegistryId` may be backed by multiple physical `Repository` mirrors without changing `PackageIdentity` (`PKG-INV-03`, `PKG-INV-34`).
  4. **`DistributionProfile` (`tasks/0858 §307`)**: Toolchains and host environments operate under one of five explicit distribution profiles:
     - `AXIOM_PACKAGE_NONE` (`Minimal`): Single-file/local module compilation with no package manager or registry state.
     - `AXIOM_PACKAGE_LOCAL` (`Local`): Offline installation and builds from local `.axpkg` archives, `vendor/`, and `.axiom/cache/pkg/` only.
     - `AXIOM_PACKAGE_DEV` (`Developer`): Local workspace development with local and configured registry resolution.
     - `AXIOM_PACKAGE_ENTERPRISE` (`Enterprise`): Private registries, namespace pinning, mandatory publisher/integrity policy enforcement, and offline mirrors.
     - `AXIOM_PACKAGE_FULL` (`Full`): Complete multi-repository synchronization, release channels, transactional generations, and rollback management.

- **AXS-REG-003 (Immutable Published Versions &Yank/Quarantine Lifecycle — `tasks/0858 §16–§18, §98–§100`, `tasks/1065 §100–§102, §128–§129`)**:
  1. **Permanent version immutability (`tasks/0858 §16, §304 #6`, `tasks/1065 §102`, `PKG-INV-35`)**: Once a package coordinate `(RegistryId, NamespaceId, PackageName, SemVer)` is published to a registry index with `(sha256, merkle_root, sif)`, the published `.axpkg` bytes and digests for that exact version are permanently immutable. Any attempt to republish or overwrite an existing `(NamespaceId, PackageName, SemVer)` with different bytes or metadata MUST be rejected by both `axiomc pkg publish` and the registry index verifier with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "immutable_version_exists"`, `data.package`, `data.version`, `data.existing_sha256`). Any change to source, interface, or binary payload requires incrementing the SemVer version.
  2. **Deterministic publication pipeline (`tasks/1065 §100–§101, §175`)**: `axiomc pkg publish` executes a fixed deterministic pipeline:
     $$\text{validate\_manifest} \rightarrow \text{reject\_local\_only\_deps} \rightarrow \text{verify\_compile\_and\_interface} \rightarrow \text{pack\_canonical\_axpkg} \rightarrow \text{compute\_merkle\_root} \rightarrow \text{append\_index\_entry}$$
     Publishing the same canonical package tree twice produces the exact same `.axpkg` byte stream and `merkle_root` (`tasks/1065 §175`). A package containing path-only dependencies (lacking a registry `version` requirement) or unpinned mutable VCS references MUST be rejected before publication with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "unpublishable_dependency"`).
  3. **Yank vs Quarantine state (`tasks/0858 §99–§100`, `tasks/1065 §128–§129, §168`)**:
     - `yanked = true`: Marks a version as deprecated/withdrawn for new unlocked resolutions (`SPEC-111 AXS-PKG-011`), while keeping its `.axpkg` blob available so existing workspaces pinned via `axiom.lock` remain 100% reproducible.
     - `quarantined = true`: Marks a version as emergency-blocked due to a critical vulnerability or supply-chain compromise (`tasks/0858 §99–§100`). A quarantined version MUST NOT be newly selected or activated, and builds referencing a quarantined version fail with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "quarantined_package"`, `data.package`, `data.version`) unless an explicit offline forensic audit flag is used.

- **AXS-REG-004 (Untrusted Transport & Pre-Use Content/Metadata Verification — `tasks/0412 §8–§10, §41, §58`, `tasks/0665 §12, §26`, `tasks/1065 §112–§113`)**:
  1. **Never trust filenames, URLs, or unverified index strings (`tasks/0412 §10`, `tasks/0665 §12`, `APKG-35..36`, `PKG-INV-12..13`)**: An archive named `crypto-1.4.2.axpkg` or downloaded from `https://.../crypto/1.4.2.axpkg` is treated as untrusted bytes until verified.
  2. **Four-stage pre-use verification gate (`tasks/0412 §8, §41, §58`, `tasks/1065 §112`)**: Before any downloaded or local `.axpkg` archive is admitted into `.axiom/cache/pkg/` or `CompilerDB`:
     - **Stage 1 (Archive & Merkle digest check)**: Verify the 64-byte `ArtifactHeader` (`magic == "AXPKG001"`), recompute the full `SHA-256` archive digest and binary Merkle tree over all payload entries (`AXS-REG-012`), and confirm exact equality with the expected `sha256` / `merkle_root` from `axiom.lock` (or the verified registry index entry).
     - **Stage 2 (Embedded manifest coordinate check)**: Parse the embedded `ManifestSection` (`axiom.toml`) inside the `.axpkg` and verify that its `(namespace, name, version, dependencies, features)` match the registry index record and the resolved `PackageIdentity` (`tasks/0412 §10, §41`). Any coordinate discrepancy between the outer filename/index and the inner `axiom.toml` is rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "manifest_coordinate_mismatch"`).
     - **Stage 3 (Interface & target/ABI contract check)**: Validate the embedded `.axmeta` / `.axmi` `InterfaceSummarySection` (`magic == "AXMETA01"` or `"AXMI0001"`) and confirm that its `SemanticInterfaceFingerprint` (`sif`) matches `axiom.lock`.
     - **Stage 4 (Sandboxed extraction check)**: Extract files under strict path-traversal and decompression quota enforcement (`AXS-REG-013`) without executing any bundled code (`tasks/0858 §26, §66`, `PKG-INV-16`).

---

## 2. Deterministic `.axpkg` Content-Addressed Archive Format & SHA-256 Merkle Tree Verification

- **AXS-REG-010 (`.axpkg` Binary Container Schema & `ArtifactHeader` Layout — `SPEC-24 AXS-ART-002, AXS-ART-024`, `tasks/0858 §15–§17`, `tasks/1065 §175–§177`)**:
  `std/pkg/archive` packs and unpacks `.axpkg` archives as deterministic binary containers conforming to `SPEC-24 AXS-ART-002..004`:
  1. **64-byte `ArtifactHeader` (`SPEC-24 AXS-ART-002`)**:
     - `magic`: `[8]u8 = "AXPKG001"` (`0x41, 0x58, 0x50, 0x4B, 0x47, 0x30, 0x30, 0x31`).
     - `format_family`: `u16 = 6` (`AXPKG`).
     - `schema_version`: `u16 = 1`.
     - `artifact_kind`: `u16`: `1 = SourcePackage`, `2 = BinaryPackage`, `3 = HybridPackage`.
     - `flags`: `u16`: Bit 0 `little_endian = 1`, Bit 1 `deterministic = 1`, Bit 2 `has_binary_variants`, Bit 3 `payload_compressed`.
     - `target_fingerprint`: `Fingerprint128` (`0` for target-neutral source packages or multi-target packages; exact `TargetFingerprint` for single-target binary packages).
     - `interface_fingerprint`: `Fingerprint128` (low 128 bits of the package's `SemanticInterfaceFingerprint`).
     - `section_count`: `u32` (number of 48-byte `SectionDescriptor` records immediately following the header).
     - `producer_version`: `u32`, `payload_offset`: `u64`, `payload_size`: `u64`, `content_hash`: `Fingerprint128` (BLAKE3-128 container header/section check per `SPEC-24 AXS-ART-002`).
  2. **Mandatory `.axpkg` section table (sorted by ascending `(section_type, id)`)**:
     - `SECTION_MANIFEST` (`section_type = 1`): Canonical normalized `axiom.toml` UTF-8 bytes.
     - `SECTION_INTERFACE_SUMMARY` (`section_type = 2`): Embedded `.axmeta` / `.axmi` summary header containing `SemanticInterfaceFingerprint` (256-bit BLAKE3), `ApiFingerprint` (256-bit BLAKE3), per-target `AbiFingerprint` table, and exported module list.
     - `SECTION_MERKLE_INDEX` (`section_type = 3`): The `AxpkgMerkleHeader` (containing `entry_count: u32`, `tree_node_count: u32`, and `merkle_root: [32]u8` SHA-256), followed by `entry_count` fixed/variable `AxpkgEntryRecord` descriptors and the serialized 32-byte SHA-256 Merkle tree nodes.
     - `SECTION_PROVENANCE` (`section_type = 12`): Canonical provenance record (`compiler_semantic_version`, `source_tree_sha256`, `lock_graph_hash`, `distribution_mode`, and optional signature envelope slot for `SPEC-113`).
     - `SECTION_PAYLOAD_BLOBS` (`section_type = 15`): Concatenated file contents aligned to 8-byte boundaries in the exact order of `AxpkgEntryRecord[]`.

- **AXS-REG-011 (Canonical Entry Normalization: Sorted POSIX Paths, Zeroed Timestamps & Normalized Permissions — `tasks/0412 §9–§10, §56`, `tasks/1065 §134–§135, §176–§177`)**:
  To guarantee that packing the same package on Windows, Linux, or macOS produces a bit-for-bit identical `.axpkg` archive and identical `merkle_root` (`INV-DET-001`, `INV-DET-002`, `PKG-INV-02`, `PKG-INV-35`):
  1. **Relative POSIX path normalization**: Every file path inside a package is converted to UTF-8 (NFC) relative to the package root directory using forward slashes (`/`), with no leading `/`, no trailing `/`, and no `.` or `..` segments (e.g., `"axiom.toml"`, `"src/lib.ax"`, `"targets/x86_64-windows/libcrypto.axlib"`).
  2. **Strict lexicographical sorting (`tasks/1065 §177`)**: All `AxpkgEntryRecord` entries MUST be sorted in strict ascending unsigned byte order (`memcmp`) of their normalized UTF-8 `path` strings. Duplicate paths (or paths colliding under ASCII case-folding `to_ascii_lowercase()`, such as `"src/ Vec.ax"` and `"src/vec.ax"`) are rejected during packing and unpacking with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "duplicate_archive_entry"`).
  3. **Zeroed timestamps & ownership (`tasks/1065 §134–§135`, `INV-DET-002`)**: Every entry record stores `mtime_sec = 0`, `mtime_nsec = 0`, `uid = 0`, `gid = 0`. Host filesystem creation/modification times, inode numbers, and OS user accounts NEVER enter `.axpkg` bytes.
  4. **Two-state normalized permissions**: File permissions are normalized to a 1-bit `entry_mode`:
     - `0` (`0644`, regular read-only/read-write data or source file: `axiom.toml`, `*.ax`, `*.axmi`, `*.axmeta`, `*.axlib`, `*.lib`, `*.a`, `*.md`, `*.json`).
     - `1` (`0755`, executable binary/tool artifact under `bin/` or `targets/<triple>/bin/`).
  5. **Text line-ending normalization & ignored paths**: All UTF-8 text sources (`*.ax`, `*.toml`, `*.md`, `*.json`, `*.def`) have `CRLF` (`\r\n`) normalized to `LF` (`\n`) prior to hashing and packing. Ephemeral workspace directories (`.axiom/`, `target/`, `vendor/`, `.git/`, `build-snap-*/`) are unconditionally excluded from `.axpkg` packing.

- **AXS-REG-012 (SHA-256 Merkle Tree Digest & Chunk Integrity Verification — `tasks/0412 §9–§10`, `tasks/0858 §17, §116–§117`)**:
  Every `.axpkg` archive is content-addressed by a domain-separated 256-bit `SHA-256` Merkle tree root (`merkle_root`):
  1. **Chunked payload digest (`tasks/0858 §116–§117`)**: For a file entry $i$ with normalized payload bytes $B_i$ of length $L_i$, $B_i$ is partitioned into $K_i = \max(1, \lceil L_i / 65536 \rceil)$ chunks $C_{i,0}, \dots, C_{i,K_i-1}$ of at most $64\text{ KiB}$ ($65,536$ bytes) each. Each chunk has digest:
     $$h_{i,k} = \text{SHA256}(\texttt{"AXPKG-CHUNK-v1\textbackslash0"} \,\|\, \text{u64\_le}(k) \,\|\, C_{i,k})$$
     and the file's `payload_sha256` is the binary Merkle root of $(h_{i,0}, \dots, h_{i,K_i-1})$ (equal to $h_{i,0}$ when $L_i \le 65,536$). This enables bounded-memory streaming verification and resumable HTTP range downloads (`tasks/0858 §116–§117, §221–§222`).
  2. **Per-entry leaf hash**: For the $i$-th sorted entry $(0 \le i < N)$ with normalized path $P_i$, mode $M_i \in \{0, 1\}$, byte size $L_i$, and `payload_sha256` $D_i$:
     $$\text{Leaf}_i = \text{SHA256}(\texttt{"AXPKG-LEAF-v1\textbackslash0"} \,\|\, \text{u32\_le}(|P_i|) \,\|\, P_i \,\|\, \text{u8}(M_i) \,\|\, \text{u64\_le}(L_i) \,\|\, D_i)$$
  3. **Binary tree reduction & package `merkle_root`**: At each tree level, adjacent pairs $(\text{Node}_{2j}, \text{Node}_{2j+1})$ reduce via:
     $$\text{Parent}_j = \text{SHA256}(\texttt{"AXPKG-NODE-v1\textbackslash0"} \,\|\, \text{Node}_{2j} \,\|\, \text{Node}_{2j+1})$$
     If a level has an odd number of nodes, the final node is promoted unchanged to the next level. Finally, the tree root $T_{\text{files}}$ is bound to the canonical `SECTION_MANIFEST` digest $D_{\text{manifest}} = \text{SHA256}(\text{manifest\_bytes})$ and `SECTION_INTERFACE_SUMMARY` digest $D_{\text{iface}} = \text{SHA256}(\text{iface\_bytes})$:
     $$\text{merkle\_root} = \text{SHA256}(\texttt{"AXPKG-ROOT-v1\textbackslash0"} \,\|\, D_{\text{manifest}} \,\|\, D_{\text{iface}} \,\|\, \text{u32\_le}(N) \,\|\, T_{\text{files}})$$
  4. **Verification failure**: If recomputing any chunk digest, `Leaf_i`, internal node, or `merkle_root` during `std/pkg/archive` unpacking or `axiomc pkg verify` differs by even 1 bit from the recorded digest in `SECTION_MERKLE_INDEX` or `axiom.lock`, verification fails immediately with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "merkle_mismatch" | "hash_mismatch"`, `data.package`, `data.entry`, `data.expected_sha256`, `data.found_sha256`).

- **AXS-REG-013 (Sandboxed Unpacking, Path-Traversal Defense & Decompression Quotas — `tasks/0412 §40`, `tasks/0858 §65–§66, §234`, `tasks/1065 §114–§115`)**:
  `std/pkg/archive` enforces strict isolation during `.axpkg` unpacking (`PKG-INV-14..16`):
  1. **Reject path traversal & special files (`PKG-INV-15`)**: Any `AxpkgEntryRecord` whose path is empty, starts with `/` or `\`, contains `\` or `:`, contains `.` or `..` path components, contains control characters (`< 0x20` or `0x7F`), or has an `entry_mode` outside `{0, 1}` (such as symlinks, hardlinks, FIFOs, sockets, or device nodes) is rejected before writing any file to disk with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "path_traversal"`, `data.entry`).
  2. **Bounded resource quotas (`tasks/0858 §118, §234`, `tasks/1065 §115`)**: Unpacking enforces configurable ceilings (defaults: `max_archive_size = 64 MiB`, `max_uncompressed_total = 256 MiB`, `max_single_file_size = 64 MiB`, `max_compression_ratio = 100`, `max_entries = 16,384`). Any archive exceeding a quota or whose declared `uncompressed_size` disagrees with the actual decompressed byte count is aborted and rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "archive_quota_exceeded"`).
  3. **Staging transaction & atomic commit (`tasks/0858 §64–§67`)**: Unpacking writes exclusively to an isolated staging directory `.axiom/cache/pkg/staging/<merkle_root_hex>.tmp.<pid>/`, verifies every entry's `Leaf_i` digest and the aggregate `merkle_root`, sets `mtime = 0`, and only then atomically renames the directory to `.axiom/cache/pkg/sha256/<b0>/<b1>/<merkle_root_hex>/`. On any error, the staging directory is unlinked completely.

---

## 3. Source, Precompiled `.axmeta` / `.axmi` Interface & Binary Package Consumption

- **AXS-REG-020 (Package Distribution Modes: `Source`, `Binary` & `Hybrid` — `tasks/0412 §20–§24`, `tasks/0665 §8, §19–§21`, `tasks/0739 §493.1–§493.6, §493.47–§493.51`)**:
  `compiler/pkg/distribution` supports three explicit `.axpkg` distribution modes (`ArtifactHeader.artifact_kind`):
  1. **`DistributionMode.Source` (`artifact_kind = 1`)**: Contains `axiom.toml`, canonical `.ax` source files under `src/`, and the embedded `SECTION_INTERFACE_SUMMARY` (`.axmeta` summary). Consuming workspaces compile the package from source through `CompilerDB` and cache the resulting target artifacts locally (`SPEC-110 AXS-BLD-030`).
  2. **`DistributionMode.Binary` (`artifact_kind = 2`, `tasks/0665 §8, §20`, `tasks/0739 §493.1, §493.47`)**: Contains `axiom.toml`, full `.axmi` module interface artifacts (`interfaces/<module>.axmi` with embedded `.axmeta`), and precompiled target-specific library/object payloads (`targets/<target-triple>/<variant>/<lib>.axlib` or `.lib`/`.a`/`.dll`/`.so`/`.dylib`/`.wasm`), with private implementation `.ax` sources omitted.
  3. **`DistributionMode.Hybrid` (`artifact_kind = 3`, `tasks/0412 §24`, `tasks/0739 §493.49–§493.50`)**: Bundles both `.axmi` interfaces + precompiled target-variant binary slices (`targets/<target-triple>/...`) AND the complete canonical `.ax` source tree (`src/`). When the active compilation target, ABI, CPU feature mask, and profile match a bundled binary slice, `compiler/pkg/distribution` consumes the binary slice directly without re-parsing source; when no binary slice matches (and `--require-binary` is not set), it falls back deterministically to compiling the bundled `.ax` source tree while recording the structured `BinaryRejectionReason`.

- **AXS-REG-021 (Source-Free `CompilerDB` Ingestion of `.axmeta` / `.axmi` Binary Packages — `tasks/0412 §21`, `tasks/0665 §8`, `tasks/0739 §493.2–§493.20, §493.55–§493.60, §493.78–§493.80`, `SPEC-24 AXS-ART-010..014`, `REQ-PKG-010`)**:
  When `compiler/pkg/distribution` resolves a `Binary` package (or a matched binary slice of a `Hybrid` package), `CompilerDB` (`SPEC-21`) ingests the package's `.axmi` / `.axmeta` interface directly without lexing or parsing any `.ax` source file (`tasks/0739 §493.55`):
  1. **Complete semantic surface population**: Loading `<pkg>.axmi` populates `CompilerDB` with all `pub` declarations (`pub fn`, `pub struct`, `pub enum`, `pub union`, `pub trait`, `pub type`, `pub const`, `pub static`, `pub extern`, `pub use`), canonical `TypeId` DAGs (`SPEC-24 AXS-ART-011`), `@repr` physical layouts (`size`, `align`, `field_offsets`, niche encodings; `tasks/0739 §493.18–§493.20`), `Trait` and `impl` coherence tables (`tasks/0739 §493.12–§493.17`), `FnContractSummary` interprocedural ownership/capability/effect/panic contracts (`SPEC-24 AXS-ART-012`, `tasks/0739 §493.64–§493.67`), and serialized `ConstValue` payloads (`tasks/0739 §493.78`).
  2. **Precompiled generic & inlineable MIR templates (`REQ-PKG-010`, `tasks/0739 §493.11, §493.37–§493.45`, `SPEC-24 AXS-ART-013`)**: Generic functions (`pub fn f<T>(...)`), `@inline` functions, and `comptime fn` items are serialized in `.axmi` as canonical `Verified MIR` templates (`GenericMir`). Upon deserialization, `CompilerDB` re-runs the MIR structural/type/ownership verifier (`INV-PIPE-002`) before monomorphizing or inlining into downstream callers.
  3. **Precompiled generic instance reuse (`tasks/0739 §493.38–§493.42`)**: A binary package MAY include pre-instantiated native object specializations (`GenericInstance`) keyed by:
     $$\text{GenericInstanceKey} = \text{BLAKE3}(\text{GenericDefId},\; \text{TypeArgs},\; \text{ConstArgs},\; \text{TargetFingerprint},\; \text{CpuFeatureMask},\; \text{OptProfile},\; \text{AbiFingerprint},\; \text{DepSifHashes})$$
     The consumer reuses a precompiled generic instance if and only if its `GenericInstanceKey` matches identically; otherwise the consumer instantiates and compiles the specialization locally from the `.axmi` `GenericMir` template.
  4. **Comptime host-execution barrier (`tasks/0739 §493.79–§493.80`)**: Evaluating a `comptime fn` exported by a binary package executes exclusively through the verified `GenericMir` template inside the sandboxed `CompilerDB` CTFE interpreter (`SPEC-60`). The compiler MUST NEVER load or execute native machine code (`.dll`/`.so`/`.obj`) from a package inside `comptime`.

- **AXS-REG-022 (Three-Tier Interface Fingerprints & Pre-Link Binary Compatibility Gate — `tasks/0412 §22–§23`, `tasks/0665 §9, §16, §20`, `tasks/0739 §493.21–§493.31, §493.51, §493.61–§493.63`, `SPEC-24 AXS-ART-022..023`)**:
  1. **Three distinct fingerprints (`tasks/0739 §493.21–§493.23`, `PKG-INV-37`)**: Every `.axpkg` `SECTION_INTERFACE_SUMMARY` and `.axmi` header records three separate 256-bit BLAKE3 digests that MUST NOT be conflated:
     - `ApiFingerprint`: Hash of public item names, signatures, generic bounds, and trait declarations (source-level API compatibility).
     - `SemanticInterfaceFingerprint` (`SIF`): `ApiFingerprint` combined with evaluated `const` values, `FnContractSummary` ownership/capability/effect/panic summaries, and exported `GenericMir` template bodies.
     - `AbiFingerprint`: Hash of `TargetFingerprint`, calling conventions (`CallConv`), `@repr` type sizes/alignments/field offsets, `dyn Trait` vtable layouts, pointer width, endianness, panic strategy (`abort` vs `unwind`), safety profile, and `compiler_abi_revision`.
  2. **Pre-link validation checklist (`tasks/0739 §493.24–§493.29, §493.61–§493.63`)**: Before `compiler/pkg/distribution` admits a binary artifact (`targets/<triple>/...`) into `BuildGraph` / `LinkerCore`, it verifies:
     - `ArtifactHeader.schema_version` and `compiler_semantic_version` compatibility (`AX_LINK_ARTIFACT_SCHEMA_MISMATCH` on mismatch);
     - `TargetFingerprint` exact match on `(arch, os, abi, object_format, pointer_width, endianness, panic_strategy)` and subset inclusion of required CPU features (`pkg.cpu_feature_mask & ~active_target.cpu_feature_mask == 0`; `AX_LINK_ARTIFACT_TARGET_MISMATCH` on mismatch);
     - `AbiFingerprint` exact match across all shared public types and extern symbols (`AX_LINK_ABI_MISMATCH` on mismatch);
     - Transitive dependency `SemanticInterfaceFingerprint` coherence across the resolved diamond graph (`AX_LINK_AXLIB_PACKAGE_CONFLICT` if two binary packages were compiled against incompatible interface fingerprints of a shared dependency).
  3. **No silent incompatible linking (`tasks/0739 §493.51`, `APKG-37`, `APKG-55`, `PKG-INV-21..22`)**: When a `Binary`-only package fails any check in (2), compilation halts before symbol resolution/relocation and emits the corresponding `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, `AX_LINK_ABI_MISMATCH`, or `AX_LINK_AXLIB_PACKAGE_CONFLICT` diagnostic with structured `data.expected_*` and `data.found_*` fields.

- **AXS-REG-023 (Multi-Target `.axpkg` Slice Layout & Deterministic Variant Selection — `tasks/0665 §21`, `tasks/0858 §19–§22, §128–§132`)**:
  A single `.axpkg` archive (`Binary` or `Hybrid`) may ship precompiled artifacts for multiple target triples and CPU feature baselines under canonical relative paths:
  ```text
  axiom.toml
  interfaces/<module>.axmi
  targets/<target-triple>/<cpu-variant>/artifact.toml
  targets/<target-triple>/<cpu-variant>/lib<name>.axlib
  ```
  `compiler/pkg/distribution` selects a target slice deterministically by:
  1. Filtering `targets/<target-triple>/*` to slices matching the active `TargetId` (`x86_64-windows`, `aarch64-windows`, `x86_64-linux`, `aarch64-linux`, `riscv64-linux`, `aarch64-macos`, `x86_64-macos`, `aarch64-android`, `wasm32-wasi`, `wasm32-freestanding`), `AbiFingerprint`, `Profile`, and `LinkKind`.
  2. Among compatible `<cpu-variant>` slices whose required `cpu_feature_mask` is a subset of the active target's enabled CPU features (`SPEC-44`), selecting the slice with the highest specificity (largest popcount of matched `cpu_feature_mask`, tie-broken by lexicographical variant name, with `"baseline"` as the universal fallback).

---

## 4. Sparse Registry Index Protocol, Multi-Repository Routing, Offline Mirrors & Transactional Rollback

- **AXS-REG-030 (Sparse Static Registry Index Protocol `AXPACKAGE_PROTOCOL_1` — `tasks/0412 §38, §57`, `tasks/0858 §6–§8, §37–§38`, `tasks/1065 §116, §164–§169`)**:
  `std/pkg/registry` implements the canonical sparse registry protocol (`protocol_version = 1`), designed to work identically over static HTTP/HTTPS file hosting, local filesystem directories, and air-gapped mirrors without requiring a custom database daemon:
  1. **Repository root `config.json`**:
     ```json
     {
       "protocol_version": 1,
       "registry_id": "default",
       "dl_template": "{root}/blobs/sha256/{b0}/{b1}/{sha256}.axpkg",
       "index_snapshot_hash": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
     }
     ```
  2. **Sparse per-package index records (`index/<namespace>/<prefix2>/<name>.jsonl`)**:
     Where `<prefix2>` is the first two ASCII characters of `<name>` (or `"_1"` for 1-character names). Each file is UTF-8 newline-delimited JSON (`LF` line endings) with one JSON object per published version sorted in ascending SemVer 2.0 order (`AXS-PKG-004`):
     ```json
     {"v":"1.4.2","ns":"axiom","name":"crypto","sha256":"2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae","merkle_root":"2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae","sif":"blake3:8899aabbccddeeff00112233445566778899aabbccddeeff0011223344556677","api":"blake3:11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff","mode":"hybrid","targets":["x86_64-windows","x86_64-linux"],"deps":[{"ns":"default","name":"core_math","req":"^0.2.0","scope":"normal","features":["default"],"optional":false}],"features":{"default":["constant_time"],"constant_time":[],"aead":[]},"channel":"stable","yanked":false,"quarantined":false,"security_fix":false,"min_compiler":"0.1.0"}
     ```
  3. **Content-addressed archive blobs (`blobs/sha256/<b0>/<b1>/<sha256_hex>.axpkg`)**:
     Where `<b0>` and `<b1>` are the first two lowercase hex byte pairs of `<sha256_hex>` (matching `.axiom/cache/pkg/sha256/<b0>/<b1>/<sha256_hex>/` in `SPEC-111 AXS-PKG-032`).
  4. **Selective O(reachable) fetching & snapshot reproducibility (`tasks/0412 §38`, `tasks/0858 §37–§39, §190–§191`)**: During dependency resolution, `std/pkg/registry` reads only the `.jsonl` index files of packages transitively referenced by the workspace. The repository's `index_snapshot_hash` (the SHA-256 over all sorted `index/<ns>/<p2>/<name>.jsonl` paths and digests) uniquely identifies the registry state at resolution time.

- **AXS-REG-031 (Multi-Repository Priority vs Trust Routing & Namespace Pinning — `tasks/0858 §11–§14, §33–§35`, `tasks/1065 §5, §106–§108, §172–§174`, `T860`)**:
  Workspaces and host configurations (`axiom.toml` `[[registry]]` or `.axiom/config.toml`) may configure multiple repositories simultaneously:
  ```toml
  [[registry]]
  id = "corp_internal"
  url = "file://D:/mirrors/corp_registry"
  priority = 100
  trust_policy = "enterprise_verified"
  pinned_namespaces = ["corp", "sec_internal"]
  allow_unsigned = false

  [[registry]]
  id = "public_default"
  url = "https://registry.axiom-lang.org"
  priority = 10
  trust_policy = "public_standard"
  pinned_namespaces = ["axiom"]
  allow_unsigned = true
  ```
  `compiler/pkg/distribution` enforces three strict routing invariants to prevent dependency-confusion and repository-shadowing attacks (`tasks/0858 §12–§14`):
  1. **Mandatory namespace pinning (Dependency-Confusion Defense)**: When a namespace `ns` is listed in `pinned_namespaces` of registry `R_pin` (or when a dependency in `axiom.toml` explicitly specifies `registry = "<id>"`), any lookup for `ns/<name>` is bound exclusively to `R_pin`. If another configured repository `R_other` (even one with higher numeric `priority` or offering a higher SemVer version `99.0.0`) advertises `ns/<name>` or attempts to serve it, `compiler/pkg/distribution` rejects the shadowing candidate and emits `AX_DRIVER_BAD_MANIFEST` (`data.kind = "namespace_shadow_blocked"`, `data.package = "<ns>/<name>"`, `data.expected_registry = "<R_pin>"`, `data.shadowing_registry = "<R_other>"`). Duplicate `pinned_namespaces` claims across two distinct non-mirror registries in the same configuration are rejected upfront with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "conflicting_namespace_pin"`).
  2. **Trust policy dominates priority (`tasks/0858 §13–§14, §34–§35`)**: Numeric `priority` (evaluated in descending order, tie-broken by ASCII `id`) determines candidate search order ONLY for unpinned namespaces across repositories that satisfy the workspace's `[package.policy]`. A higher-priority repository MUST NEVER override a package blocked by `blocked_packages`, `quarantined = true`, `min_allowed_version`, or `allow_unsigned = false`.
  3. **Credential isolation & URL redaction (`tasks/0858 §121–§122, §226, §304 #30`, `tasks/1065 §173–§174`, `PKG-INV-33`)**: Repository credentials exist only in external host environment/credential stores, are never sent to a different repository or untrusted mirror on redirect, and are stripped from `axiom.lock` (which records `registry = "<id>"`, never raw credential-bearing URLs).

- **AXS-REG-032 (Offline-First Local Repository Mirrors & Air-Gapped Resolution — `tasks/0858 §9–§10, §112–§115, §190–§195`, `tasks/1065 §50–§65, §130–§131, §170–§171`, `PKG-INV-10, PKG-INV-34`)**:
  1. **Local mirror synchronization (`axiomc pkg mirror`)**: `axiomc pkg mirror <dest_dir> [--from-lock [<axiom.lock>] | --packages <spec>...] [--verify]` populates a self-contained `AXPACKAGE_PROTOCOL_1` directory at `<dest_dir>` containing `config.json`, the exact `index/<ns>/<p2>/<name>.jsonl` metadata slices, all corresponding `blobs/sha256/<b0>/<b1>/<sha256>.axpkg` archives, and `mirror-snapshot.toml` recording `index_snapshot_hash` and total verified blob count.
  2. **Content-identity preservation across mirrors (`tasks/0858 §113–§115`, `PKG-INV-34`)**: Every blob copied into or fetched from a mirror is verified against its `SHA-256` `merkle_root`. Because `PackageIdentity` keys on `(RegistryId, NamespaceId, PackageName, SemVer, SourceId, ContentHash, SIF)` and never on the physical mirror URL (`SPEC-111 AXS-PKG-002`), redirecting `RegistryId = "default"` to `--registry-mirror <dest_dir>` (or `AXIOM_REGISTRY_MIRROR=<dest_dir>`) under `--offline` produces a byte-for-byte identical `axiom.lock` and byte-for-byte identical compiled binaries (`INV-DET-001`).
  3. **Offline-first cache hierarchy (`tasks/0412 §39, §58`, `tasks/0858 §9, §109–§112`, `tasks/1065 §170`)**: Whenever `.axiom/cache/pkg/sha256/` or `vendor/` already contains the verified `sha256` blob required by `axiom.lock`, `axiomc build|check|test|run` and `axiomc pkg fetch --locked` satisfy the dependency locally with zero network requests even when `--offline` is not explicitly passed (`tasks/1065 §170`).

- **AXS-REG-033 (Release Channels, Minimum Secure Version Floor & Downgrade Protection — `tasks/0858 §91–§100`)**:
  1. **Explicit release channels (`tasks/0858 §91–§94`)**: Every published registry index entry carries a `channel` tag in `{"stable", "beta", "preview", "nightly", "internal"}` (default `"stable"`). Workspaces and installed applications subscribe to `"stable"` by default; candidates from non-default channels (`"beta"`, `"preview"`, `"nightly"`, `"internal"`) are considered only when explicitly requested via `channel = "<ch>"` in `axiom.toml` or `--channel <ch>` on the CLI. Switching channels is always an explicit configuration change, never automatic (`tasks/0858 §94`).
  2. **Minimum secure version & downgrade guard (`tasks/0858 §95–§98`)**: Workspace `[package.policy]` may declare `allow_downgrade = false` and per-package security floors `min_allowed_version = { "axiom/crypto" = "2.0.1" }`. Any attempt by resolution, `axiomc pkg update`, or `axiomc pkg rollback` to select a version $v < \text{min\_allowed\_version}$ (or to downgrade below the currently active generation when `allow_downgrade = false`) is rejected with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "policy_blocked_version"`, `data.package`, `data.version`, `data.min_allowed_version`).

- **AXS-REG-034 (Transactional Package Installation, Atomic Generations, `.axupdate-journal` & Safe Rollback — `tasks/0858 §25–§40, §63–§90, §101–§108, §157–§169, §304 #10–14, #21`)**:
  `std/pkg/registry` manages package/application installations inside a generation root (`<root>/.axiom/pkg/`) using an atomic, crash-recoverable state machine:
  1. **Installation state machine & 5-phase transaction (`tasks/0858 §63–§67`)**:
     Every managed package transitions through `Available -> Downloaded -> Verified -> Staged -> Installed -> Activated` (or `Disabled | Quarantined | Removed`). Installation executes five sequential phases:
     $$\text{download} \rightarrow \text{verify\_merkle\_and\_policy} \rightarrow \text{stage\_isolated} \rightarrow \text{validate\_graph\_and\_abi} \rightarrow \text{atomic\_commit}$$
     No binary or script inside a package is ever executed during `download`, `verify`, `stage`, or `validate` (`tasks/0858 §66, §304 #10`).
  2. **Write-ahead `.axupdate-journal` & crash recovery (`tasks/0858 §84–§89, §242`)**:
     Before mutating the active generation pointer, the transaction manager writes a checksummed journal record to `<root>/.axiom/pkg/.axupdate-journal`:
     ```toml
     journal_version = 1
     tx_id = "tx_00000018"
     state = "staged" # "staged" | "committed" | "rolled_back"
     prev_generation = 17
     next_generation = 18
     journal_sha256 = "sha256:..."
     ```
     If an installation or update fails midway or is interrupted by process crash / power loss (`tasks/0858 §84–§87`), opening the package store validates `.axupdate-journal`: any transaction still in `state = "staged"` is rolled back cleanly, leaving `prev_generation` active and intact.
  3. **Numbered immutable generations & atomic activation pointer (`tasks/0858 §67–§70, §90, §247`)**:
     Each committed transaction materializes an immutable generation manifest `<root>/.axiom/pkg/generations/gen_<N>/generation.toml` (listing all active packages, their `merkle_root` digests, channels, and capabilities) and atomically switches `<root>/.axiom/pkg/active_generation` from `gen_<N-1>` to `gen_<N>` via temp-write-then-rename.
  4. **Safe rollback & strict user-data preservation (`tasks/0858 §70–§75, §101–§103, §163–§169, §304 #13–14, #21`)**:
     - `axiomc pkg rollback [--to-generation <M>]` selects the previous verified generation $M$ (default $N - 1$), re-verifies every package's `merkle_root` in `.axiom/cache/pkg/` and checks `min_allowed_version` / `allow_downgrade` policy (`AXS-REG-033`), and atomically flips `active_generation` to `gen_<M>`.
     - Previous generations remain pinned in `.axiom/cache/pkg/` until they fall outside `rollback_retention_count` (default `2`), after which `axiomc pkg gc` may reclaim unreferenced CAS blobs (`tasks/0858 §69, §106–§108, §248–§250`).
     - **User data boundary (`tasks/0858 §71, §73, §75, §102, §304 #14, #21`)**: Package rollback and `axiomc pkg remove` operate strictly on immutable package/binary generations and NEVER delete, overwrite, or falsify application/user state under `<root>/data/` or user workspace files.

---

## 5. Registry & Distribution CLI Subcommands, Diagnostics, Examples & Conformance Matrix

- **AXS-REG-040 (`axiomc pkg` Registry, Archive, Mirror & Rollback CLI Subcommands — `T859`, `T860`)**:
  Extending `SPEC-111 AXS-PKG-040`, `compiler/driver/registry_cmd` provides the following deterministic CLI subcommands:
  1. **`axiomc pkg pack [--mode source|binary|hybrid] [--target <triple>...] [-o <path.axpkg>]`**:
     Validates `axiom.toml`, compiles and emits `.axmi` / `.axmeta` (and native target artifacts when `--mode binary|hybrid`), normalizes and sorts all package entries (`mtime = 0`, `LF` line endings, `0644`/`0755` modes), computes the `SHA-256` Merkle tree (`AXS-REG-012`), writes the deterministic `.axpkg` archive, and prints its `merkle_root` digest.
  2. **`axiomc pkg publish [--registry <id>] [--channel stable|beta|preview|nightly|internal] [--mode source|binary|hybrid] [--dry-run]`**:
     Executes the publication pipeline (`AXS-REG-003`), packs the canonical `.axpkg`, verifies that `(namespace, name, version)` does not already exist in the target registry (`data.kind = "immutable_version_exists"`), uploads/writes the blob to `blobs/sha256/<b0>/<b1>/<merkle_root>.axpkg`, and atomically appends the version record to `index/<ns>/<p2>/<name>.jsonl` (updating `config.json` `index_snapshot_hash`). With `--dry-run`, performs all validations and `.axpkg` packing without mutating the registry.
  3. **`axiomc pkg fetch [--locked] [--offline] [--registry-mirror <dir>]`**:
     Resolves the workspace dependency graph (or reads `axiom.lock` under `--locked`), routes each package lookup according to multi-repository `pinned_namespaces` and `TrustPolicy` (`AXS-REG-031`), downloads any missing `.axpkg` blobs into `.axiom/cache/pkg/sha256/`, and runs the 4-stage pre-use verification gate (`AXS-REG-004`).
  4. **`axiomc pkg verify [<path.axpkg> | <pkg_spec>] [--offline]`**:
     Verifies the 64-byte `ArtifactHeader`, `SECTION_MANIFEST`, `SECTION_INTERFACE_SUMMARY`, every file entry's `Leaf_i` digest, and the root `merkle_root` against `axiom.lock` and active `[package.policy]`.
  5. **`axiomc pkg search <query> [--registry <id>] [--channel <ch>] [--limit <N>] [--format text|json]`**:
     Queries configured registry indices for packages matching `<query>` (ordered deterministically by exact name match, then ascending `(namespace, name, highest_version)`). Search is purely informational and never mutates `axiom.toml` or `axiom.lock` (`tasks/1065 §167`).
  6. **`axiomc pkg mirror <dest_dir> [--from-lock [<axiom.lock>] | --packages <spec>...] [--verify]`**:
     Synchronizes and verifies a self-contained offline sparse registry mirror at `<dest_dir>` (`AXS-REG-032`).
  7. **`axiomc pkg install <pkg_or_axpkg> [--root <dir>] [--channel <ch>] [--offline]`** and **`axiomc pkg rollback [--root <dir>] [--to-generation <N>]`**:
     Executes transactional 5-phase package installation or atomic generation rollback via `.axupdate-journal` (`AXS-REG-034`).

- **AXS-REG-050 (Diagnostic Mapping)**:
  `std/pkg/archive`, `std/pkg/registry`, `compiler/pkg/distribution`, and `compiler/driver/registry_cmd` map all E20.3 error conditions to canonical diagnostic codes registered in `compiler/diag/code.ax` (`spec/diagnostics.md` §3 `AXD-021`, §10–§11):

  | Corpus / Task Shorthand | Canonical `AX_<AREA>_<NAME>` | Area | Sev | Exit | Trigger Condition & Structured `data` Fields |
  |---|---|---|---|---|---|
  | `AXPKG_MERKLE_MISMATCH`, `AXPKG_HASH_MISMATCH` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | `.axpkg` `merkle_root`, chunk digest, or entry `Leaf_i` SHA-256 digest does not match `SECTION_MERKLE_INDEX`, registry index, or `axiom.lock` (`AXS-REG-004`, `AXS-REG-012`; `data.kind = "merkle_mismatch" \| "hash_mismatch"`, `data.package`, `data.entry`, `data.expected_sha256`, `data.found_sha256`). |
  | `AXPKG_IMMUTABLE_VERSION` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Attempting to publish or overwrite an already-published `(namespace, name, version)` in a registry with different content or metadata (`AXS-REG-003`; `data.kind = "immutable_version_exists"`, `data.package`, `data.version`). |
  | `AXPKG_UNPUBLISHABLE_DEP` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Attempting to publish a package that retains path-only or unpinned mutable VCS dependencies (`AXS-REG-003`; `data.kind = "unpublishable_dependency"`, `data.dependency`). |
  | `AXPKG_COORD_MISMATCH` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Embedded `axiom.toml` inside `.axpkg` disagrees with the registry index entry or expected `(namespace, name, version)` (`AXS-REG-004`; `data.kind = "manifest_coordinate_mismatch"`). |
  | `AXPKG_NAMESPACE_SHADOW`, `E_DEP_CONFUSION` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Unpinned or lower-trust repository attempts to serve or shadow a package belonging to a namespace pinned via `pinned_namespaces` (`AXS-REG-031`; `data.kind = "namespace_shadow_blocked" \| "conflicting_namespace_pin"`, `data.package`, `data.expected_registry`, `data.shadowing_registry`). |
  | `AXPKG_QUARANTINED`, `AXPKG_POLICY_BLOCKED` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Package version is marked `quarantined = true`, listed in `blocked_packages`, or violates `min_allowed_version` / `allow_downgrade = false` during resolution, install, or rollback (`AXS-REG-003`, `AXS-REG-033..034`; `data.kind = "quarantined_package" \| "policy_blocked_version"`, `data.package`, `data.version`). |
  | `AXPKG_ROLLBACK_FAILED` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | Requested rollback target generation does not exist, has a corrupt `.axupdate-journal`, or is blocked by `min_allowed_version` (`AXS-REG-034`; `data.kind = "rollback_unavailable"`, `data.generation`). |
  | `AXPKG_PATH_TRAVERSAL`, `AXPKG_QUOTA` | `AX_DRIVER_BAD_MANIFEST` | `DRIVER` | `error` | `1` | `.axpkg` entry contains `..`, leading `/`, `\`, drive prefix, symlink/device node, duplicate case-folded path, or exceeds decompression quotas (`AXS-REG-011`, `AXS-REG-013`; `data.kind = "path_traversal" \| "duplicate_archive_entry" \| "archive_quota_exceeded"`). |
  | `AXPKG_BAD_CONTAINER` | `AX_LINK_BAD_ARTIFACT` | `LINK` | `error` | `1` | `.axpkg`, `.axmi`, or `.axmeta` has invalid magic (`!= "AXPKG001"` / `"AXMI0001"` / `"AXMETA01"`), truncated header/section table, out-of-bounds section offset, or failed BLAKE3 header/section checksum (`AXS-REG-010`, `SPEC-24 AXS-ART-050`). |
  | `AXPKG_SCHEMA_INCOMPATIBLE` | `AX_LINK_ARTIFACT_SCHEMA_MISMATCH` | `LINK` | `error` | `1` | Unsupported `.axpkg` / `.axmi` / `.axmeta` `schema_version` or incompatible `compiler_semantic_version` (`AXS-REG-022`, `SPEC-24 AXS-ART-005`). |
  | `AXPKG_TARGET_INCOMPATIBLE` | `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `error` | `1` | Precompiled binary `.axpkg` slice mismatches active `TargetFingerprint`, OS/arch/pointer width, required CPU feature baseline, or panic/safety profile (`AXS-REG-022..023`, `SPEC-24 AXS-ART-023`). |
  | `AXPKG_ABI_INCOMPATIBLE` | `AX_LINK_ABI_MISMATCH` | `LINK` | `error` | `1` | Precompiled binary `.axpkg` `.axmeta` `AbiFingerprint`, `@repr` layout, or calling convention conflicts with downstream consumer (`AXS-REG-022`, `SPEC-27 AXS-LNK-005`). |
  | `AXPKG_DIAMOND_CONFLICT` | `AX_LINK_AXLIB_PACKAGE_CONFLICT` | `LINK` | `error` | `1` | Two precompiled binary packages in the link graph were built against conflicting `SemanticInterfaceFingerprint`s or `AbiFingerprint`s of a shared dependency (`AXS-REG-022`, `SPEC-89 AXS-ARTM-014`). |

- **AXS-REG-051 (Positive Canonical Examples)**:
  1. **Deterministic `.axpkg` packaging, sparse registry publication, and source-free precompiled `.axmeta`/`.axmi` consumption (`AXS-REG-010..023`)**:
     ```axiom
     // === Upstream package `axiom/fast_hash` v1.2.0 (src/lib.ax) ===
     // Packed and published via:
     //   axiomc pkg publish --registry default --mode binary --channel stable
     // Produces `fast_hash-1.2.0.axpkg` containing `axiom.toml`, `interfaces/fast_hash.axmi`
     // (with exported `Digest64`, `mix64<T>`, and verified GenericMir), and
     // `targets/x86_64-windows/baseline/libfast_hash.axlib`.
     module fast_hash

     @repr(C)
     pub struct Digest64 {
         pub value: u64,
     }

     pub trait Hashable {
         fn to_u64(self: view<Self>) -> u64
     }

     pub const FNV_PRIME: u64 = 1099511628211

     pub fn hash_one<T: Hashable>(item: view<T>, seed: u64) -> Digest64 {
         let raw = item.to_u64()
         let mixed = (seed ^ raw) *% FNV_PRIME
         return Digest64 { value: mixed }
     }
     ```
     ```axiom
     // === Downstream workspace `app` consuming `axiom/fast_hash@1.2.0` from Binary .axpkg ===
     // Pre-build step:
     //   axiomc pkg mirror ./local_mirror --from-lock axiom.lock --verify
     //   axiomc build --offline --locked --registry-mirror ./local_mirror
     // `CompilerDB` ingests `interfaces/fast_hash.axmi` directly (zero `.ax` source parsing),
     // verifies `TargetFingerprint` and `AbiFingerprint`, monomorphizes `hash_one<Packet>` from
     // the verified `GenericMir` template, and links `libfast_hash.axlib`.
     module app

     use fast_hash.Digest64
     use fast_hash.Hashable
     use fast_hash.hash_one

     pub struct Packet {
         pub id: u64,
         pub payload: u64,
     }

     impl Hashable for Packet {
         fn to_u64(self: view<Packet>) -> u64 {
             return self.id ^ self.payload
         }
     }

     pub fn main() -> i32 {
         let pkt = Packet { id: 42, payload: 100 }
         let d: Digest64 = hash_one(pkt.as_view(), 14695981039346656037)
         if d.value != 0 {
             return 0
         }
         return 1
     }
     ```
  2. **Transactional package installation, generation activation, and safe rollback (`AXS-REG-034`)**:
     ```axiom
     // Using `std.pkg.registry` and `std.pkg.archive` in a deployment tool test:
     module pkg_deploy_test

     use std.pkg.archive.pack_axpkg
     use std.pkg.archive.verify_axpkg
     use std.pkg.registry.RegistryStore

     pub fn verify_transactional_rollback(store: mut_view<RegistryStore>) -> i32 {
         // Generation 1 installs `corp/agent@1.0.0`, Generation 2 upgrades to `corp/agent@1.1.0`.
         let gen_after_upgrade = store.active_generation()
         if gen_after_upgrade != 2 {
             return 1
         }
         // Rolling back atomically restores Generation 1 (`corp/agent@1.0.0`)
         // while preserving `<root>/data/user_config.toml` untouched.
         let ok = store.rollback_to(1)
         if !ok || store.active_generation() != 1 {
             return 2
         }
         return 0
     }
     ```

- **AXS-REG-052 (Negative Canonical Examples)**:
  1. **Rejected multi-repository dependency-confusion / namespace shadowing (`AXS-REG-031`)**:
     - Workspace configures `corp_internal` (`priority = 50`, `pinned_namespaces = ["corp"]`) and `public_mirror` (`priority = 100`, unpinned).
     - `public_mirror` advertises `corp/auth_token@9.9.9` while `corp_internal` has `corp/auth_token@1.2.0`.
     - If `public_mirror` is queried or attempts to supply `corp/auth_token`, `compiler/pkg/distribution` rejects the unpinned source with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "namespace_shadow_blocked"`, `data.package = "corp/auth_token"`, `data.expected_registry = "corp_internal"`, `data.shadowing_registry = "public_mirror"`) and resolves `corp/auth_token` exclusively from `corp_internal`.
  2. **Rejected immutable version overwrite & Merkle leaf tampering (`AXS-REG-003`, `AXS-REG-012`)**:
     - Publishing `axiom/fast_hash@1.2.0` a second time with a modified `src/lib.ax` fails immediately with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "immutable_version_exists"`, `data.package = "axiom/fast_hash"`, `data.version = "1.2.0"`).
     - Modifying 1 byte of a file payload inside `fast_hash-1.2.0.axpkg` without updating `merkle_root` fails `axiomc pkg verify` and `axiomc pkg fetch` with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "merkle_mismatch"`).
  3. **Rejected precompiled binary `.axpkg` target/ABI mismatch (`AXS-REG-022`)**:
     - Attempting to link a `Binary`-only `fast_hash-1.2.0.axpkg` containing only `targets/x86_64-linux/baseline/libfast_hash.axlib` into an `--target x86_64-windows` build fails before linking with `AX_LINK_ARTIFACT_TARGET_MISMATCH` (`data.expected_target = "x86_64-windows"`, `data.found_target = "x86_64-linux"`).

- **AXS-REG-053 (E20.3 Implementation & Verification Matrix)**:

  | Task | Role | Deliverable Scope & Allowed Paths | Primary Invariant & Verification Suite |
  |---|---|---|---|
  | `T859` | `axiom-stdlib` | `std/pkg/archive`, `std/pkg/registry`, `tests/run/pkg_registry`: Deterministic `.axpkg` packer/unpacker with lexicographically sorted POSIX paths, zeroed timestamps (`mtime = 0`), normalized permissions, embedded `axiom.toml` + `.axmeta` headers, path-traversal/quota defenses, and binary SHA-256 Merkle tree verifier (`AXS-REG-010..013`); sparse JSONL registry index client (`AXPACKAGE_PROTOCOL_1`), immutable version publication enforcement, local filesystem/mirror repositories, and `.axupdate-journal` transactional generation installation & rollback (`AXS-REG-001..004`, `AXS-REG-030`, `AXS-REG-032..034`). | `INV-REG-001` (`tests/run/pkg_registry`) |
  | `T860` | `axiom-backend` | `compiler/pkg/distribution`, `compiler/driver/registry_cmd`, `tests/run/pkg_distribution`: Source, precompiled `.axmeta`/`.axmi` + binary (`.axlib`), and hybrid `.axpkg` consumption in `CompilerDB` without re-parsing source, 3-tier fingerprint (`Api`/`SIF`/`Abi`) & `TargetFingerprint` pre-link validation (`AXS-REG-020..023`), multi-repository priority vs trust routing with `pinned_namespaces` dependency-confusion defense (`AXS-REG-031`), and `axiomc pkg pack\|publish\|fetch\|verify\|search\|mirror\|install\|rollback` CLI (`AXS-REG-040`). | `INV-REG-002` (`tests/run/pkg_distribution`) |
  | `T861` | `axiom-qa` | `tests/conformance/p20/e20_3_registry_distribution`: End-to-end E20.3 conformance suite certifying `REQ-ECO-8736` and `REQ-PKG-024` across `axiomc pkg publish` -> sparse index update -> `axiomc pkg fetch` -> workspace build, immutable version enforcement, SHA-256 Merkle tampering detection, `axiomc pkg mirror` air-gapped workspace resolution, precompiled `.axmeta` + binary package consumption, multi-repository namespace-pinning dependency-confusion defense, transactional generation rollback, and `--interp` vs native equivalence (`0 WEAK-NATIVE`). | `INV-REG-003` (`tests/conformance/p20/e20_3_registry_distribution`) |

## Sources
tasks/0412 (BOOTSTRAP-153: `§8`–`§10`, `§20`–`§26`, `§38`–`§41`, `§54`–`§61` `APKG-20..60`); tasks/0665 (BOOTSTRAP-406: `§1`–`§12`, `§16`–`§21`, `§39`–`§43` `APKG-01..30`); tasks/0739 (BOOTSTRAP-493: `§493.1`–`§493.100`); tasks/0858 (BOOTSTRAP-625: `§1`–`§40`, `§63`–`§132`, `§157`–`§198`, `§209`–`§250`, `§299`–`§310`); tasks/1065 (BOOTSTRAP-800 `AXPACKAGE`: `§50`–`§65`, `§100`–`§139`, `§164`–`§200`, `PKG-INV-01..40`); `spec/requirements/CATALOG.md` (`REQ-ECO-8736`, `REQ-PKG-010`..`REQ-PKG-017`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `REQ-LNK-479`..`REQ-LNK-481`, `REQ-LNK-526`..`REQ-LNK-529`, `REQ-LNK-617`..`REQ-LNK-622`); `SPEC-21`; `SPEC-22`; `SPEC-24`; `SPEC-27`; `SPEC-88`; `SPEC-89`; `SPEC-110`; `SPEC-111`; `spec/diagnostics.md`; `spec/invariants.md`.
