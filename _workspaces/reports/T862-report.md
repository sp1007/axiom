# T862 Report — E20.4 Canonical Build Sandbox, Hermetic/Reproducible Compilation, Ed25519 Signing & Supply-Chain Trust Specification (`SPEC-113`)

STATUS: COMPLETE

## Tóm tắt

Hoàn thành đặc tả chính tắc `spec/SPEC-113-hermetic-builds-supply-chain-trust.md` cho Epic **E20.4** (`T862`), quy định toàn diện mô hình tin cậy chuỗi cung ứng (`Safe ≠ Trusted`, `Signed ≠ Correct`, `REQ-PKG-024`), việc khai báo và kiểm toán 6 quyền đặc quyền của gói (`unsafe`, `ffi`, `net`, `fs`, `process`, `asm`), từ chối leo thang đặc quyền bắc cầu dựa trên `[trust.policy]`, hộp cát biên dịch kín (`BuildSandbox`, `REQ-PKG-022`: cây mã nguồn chỉ đọc `/source` và `/dependencies`, đầu ra giới hạn tại `/build` và `/output`, cấm truy cập mạng `NetworkPolicy = Denied`, danh sách trắng biến môi trường `env_allowlist`, đồng hồ ảo đóng băng `SOURCE_DATE_EPOCH = 0` và bộ sinh số ngẫu nhiên tất định, ánh xạ lại tiền tố đường dẫn chuẩn `--remap-path-prefix` sang `@pkg/`, `@ws/`, `@std/`, `@gen/`, `@out/`, kiểm tra rò rỉ đường dẫn máy chủ sau liên kết, và bộ kiểm tra biên dịch kép `--verify-repro` để đảm bảo kết quả khớp từng bit), ký số gói và chuỗi công cụ bằng `Ed25519` (RFC 8032), chứng thực nguồn gốc biên dịch JSON (`.axprov.json`), chuỗi băm minh bạch (`ArtifactLog`), và giao thức biên dịch kép đa dạng (`DDC`) chống lại tấn công *Reflections on Trusting Trust*. Đồng thời cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, và `spec/invariants.md` (`INV-HERM-001`..`INV-HERM-003` với `since: T863`..`T865`).

## Summary of Decisions & Deliverables

1. **Supply-Chain Trust Model & Transitive Capability Auditing (`SPEC-113 §1`, `AXS-HERM-001`..`AXS-HERM-004`, `REQ-PKG-024`)**:
   - Formalized the separation of the 4 security planes (**Compile-Time Safety**, **Runtime Authority**, **Build Isolation**, **Supply-Chain Trust**) and the core axioms `Safe ≠ Trusted` and `Signed ≠ Correct`.
   - Defined the 6 package-level capability declarations in `axiom.toml` `[capabilities]` (`unsafe`, `ffi`, `net`, `fs`, `process`, `asm`) and static source-vs-manifest verification (`AX_DRIVER_BAD_MANIFEST` `data.kind = "undeclared_package_capability"`).
   - Specified transitive dependency capability closure over `axiom.lock` and workspace `[trust.policy]` (`default_max_capabilities`, `package_grants`) with mandatory fail-closed capability-escalation rejection (`AX_DRIVER_BAD_MANIFEST` `data.kind = "capability_escalation_denied"`, `REQ-PKG-024`).
   - Specified `[[build_tool]]` and `comptime` capability isolation and `GeneratedSourceProvenance` confinement (`data.kind = "undeclared_build_output"`).

2. **Hermetic Build Sandbox (`SPEC-113 §2`, `AXS-HERM-010`..`AXS-HERM-015`, `REQ-PKG-022`)**:
   - Defined the 5 virtual filesystem namespaces (`/source` read-only, `/dependencies` read-only, `/build` read-write scratch, `/output` write-once, `/cache` content-addressed) and the mandatory 4-step path resolution pipeline (`canonicalize -> resolve -> authorize -> access`) blocking `..` traversal and symlink/junction escapes (`data.kind = "sandbox_fs_violation"`).
   - Enforced `NetworkPolicy = Denied` during compilation, `comptime`, and `[[build_tool]]` execution (`data.kind = "sandbox_net_violation"`), sanitized environment allowlisting (`[build].env_allowlist`, `data.kind = "sandbox_env_violation"`), frozen `SOURCE_DATE_EPOCH = 0` virtual clock and deterministic `ChaCha20`/splitmix64 PRNG (`data.kind = "sandbox_clock_or_rng_violation"`), and `ProcessPolicy = Denied` (`data.kind = "sandbox_process_violation"`).

3. **Bit-for-Bit Reproducible Compilation & `--verify-repro` (`SPEC-113 §3`, `AXS-HERM-020`..`AXS-HERM-023`, `REQ-PKG-022`)**:
   - Specified canonical `--remap-path-prefix` rules mapping host checkout paths to `@pkg/<ns>/<name>@<ver>/`, `@ws/`, `@std/`, `@gen/<ns>/<name>@<ver>/`, and `@out/`, plus post-link host-path byte scanning (`data.kind = "repro_host_path_leak"`).
   - Specified deterministic symbol, section, relocation, archive, and unwind ordering across `--jobs 1` and `--jobs N`, the 12-component `HermeticBuildFingerprint`, and the 2-run differential `--verify-repro` / `axiomc verify-repro` verifier (`ReproStatus.Reproduced | NotReproduced | Inconclusive`, `data.kind = "repro_mismatch"`).

4. **Ed25519 Signing, `.axprov.json` Provenance, Transparency Log & DDC Bootstrap Trust (`SPEC-113 §4–§5`, `AXS-HERM-030`..`AXS-HERM-053`)**:
   - Specified RFC 8032 Ed25519 package and toolchain signing over domain-separated `"AXIOM-SIG-v1\0"` transcripts, strict separation of compiler passes from private signing keys, dual-signed `KeyRotationCert`s, key revocation checks, and `ArtifactLog` hash chains.
   - Specified the external `.axprov.json` JSON build provenance manifest (orthogonal to `.axmi`/`.axmeta`), zero-trust remote build cache verification, secret redaction, Diverse Double-Compilation (`DDC`) Stage-2A/Stage-2B/Stage-3 fixed-point bootstrap verification (`data.kind = "ddc_mismatch"`), and the `axiomc verify-repro|trust|audit|provenance` CLI surface.
   - Updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` (`INV-HERM-001`..`INV-HERM-003` with `since: T863`..`T865`).

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `requirements: 32308 ... gaps: 0 / COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T862` → verified all 4 modified/created files match the task's `paths:` and `locks:` declarations.

## Files changed

- spec/SPEC-113-hermetic-builds-supply-chain-trust.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md
