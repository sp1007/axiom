# T517 — E13.4: Safety profile enforcement (`@forbid_unsafe`, capability-only IO/net/fs, sandbox verification)

## Tóm tắt
- Triển khai cờ dòng lệnh `--safety-profile safe|sandbox|system` và các khoá cấu hình `safety_profile`, `forbid_unsafe` trong `axiom.toml` (`[package]`, `[security]`, `[target]`) tại `compiler/driver/opts.ax` và `compiler/driver/pipeline.ax`; trả về mã thoát `2` kèm `AX_DRIVER_INVALID_SAFETY_PROFILE` khi giá trị không hợp lệ.
- Bổ sung đầy đủ các mã chẩn đoán bảo mật theo `SPEC-53` trong `compiler/diag/code.ax`: `AX_SEC_UNSAFE_FORBIDDEN`, `AX_SEC_CONFLICTING_SAFETY_POLICY`, `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`, `AX_SEC_CAPABILITY_FORGERY`, `AX_DRIVER_INVALID_SAFETY_PROFILE`.
- Thực thi `@forbid_unsafe` (kế thừa phân cấp module cha -> module con, kế thừa item/impl/trait -> member, tính đơn điệu không leo thang đối với `@allow_unsafe`) và `--safety-profile safe|sandbox` trên toàn bộ 7 nhóm cấu trúc không an toàn (`unsafe {}`, `unsafe fn`, `unsafe trait`, `unsafe impl`, thao tác con trỏ thô `*p`/`p.f`/`p + n`/`address_of`, `extern` / `@export` / `@no_mangle`, `static mut`, `@at`/`@addr`, `@naked`) trong `compiler/types/typeck.ax`, đồng thời khử trùng lặp `AX_UNSAFE_REQUIRED` / `AX_CONC_UNSYNC_STATIC` bên trong phạm vi `@forbid_unsafe`.
- Thực thi cấm thẩm quyền ngầm (`REQ-CAP-131`, `AXS-SEC-011`) trong `--safety-profile sandbox` và `comptime` thông qua đồ thị lời gọi bắc cầu `SecOsGraph` (kèm ghi chú `call chain: ...` và kiểm tra cách ly hai chiều `comptime` <-> `runtime` đối với token `*Cap`).
- Chặn giả mạo capability/view an toàn (`view<T>`, `mut_view<T>`, `Str`, `FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`, `SandboxCaps`, `RootCaps`) từ địa chỉ nguyên, con trỏ thô hoặc `PhysAddr`/`VirtAddr`/`WasmAddr` (`REQ-CAP-010`, `REQ-CAP-123`) cả bên ngoài lẫn bên trong `unsafe`.
- Bổ sung bộ kiểm thử UI, CLI/manifest/`--json` oracle và kiểm thử thực thi đa chế độ (`interp`, `native`, `native-O1`, `WEAK-NATIVE: 0`) trong `tests/ui/security_profiles/`.

## Implementation Details
1. **Diagnostics (`compiler/diag/code.ax`)**:
   - Registered `AX_SEC_UNSAFE_FORBIDDEN` (`184`), `AX_SEC_CONFLICTING_SAFETY_POLICY` (`185`), `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN` (`186`), `AX_SEC_CAPABILITY_FORGERY` (`187`), and `AX_DRIVER_INVALID_SAFETY_PROFILE` (`218`).
2. **Driver CLI & Manifest (`compiler/driver/opts.ax`, `compiler/driver/mod.ax`, `compiler/driver/pipeline.ax`)**:
   - Added `--safety-profile <mode>` / `--safety-profile=<mode>` (`system` default, `safe`, `sandbox`) to `DriverOptions` and `driver_parse_options`.
   - Extended `PackageManifest` and `manifest_parse_text` to parse `safety_profile = "..."` and `forbid_unsafe = true|false` under `[package]`, `[security]` (`[security]` overrides `[package]`), and `[target]`/`[target.*]`; CLI `--safety-profile` overrides manifest settings.
   - Updated `ax_text_module_header` and `pipe_collect_module_headers` to skip leading `@attr` tokens before `module <path>` so multi-file packages with `@forbid_unsafe module a.b` discover module headers cleanly.
   - Wired `typeck_check_safety_profile` and `typeck_dedup_unsafe_diags_under_forbid` in `pipeline_stage_typeck`, passing explicit non-`std` `user_fids` so user sources cannot spoof `module std.*` to bypass `safe`/`sandbox`.
3. **Type & Security Verification (`compiler/types/typeck.ax`, `compiler/types/mod.ax`)**:
   - Implemented `tc_try_report_capability_forgery` in explicit casts (`HIR_EXPR_CAST`), implicit coercions (`coerce`), and block tail returns (`check_block`) with structured JSON `data.source` and `data.target`.
   - Enabled typechecking of `HIR_EXPR_COMPTIME` blocks (`check_expr_match_or_view`) and traversal in capture/spawn scanners.
   - Implemented `typeck_check_safety_profile` and `SecOsGraph` transitive authority analysis (`AXS-SEC-001`..`004`, `AXS-SEC-010`..`011`, `AXS-SEC-050`..`053`), emitting structured JSON `data` payloads (`construct`, `policy`, `operation`, `required_cap`, `profile`, `reason`) and transitive `call chain:` notes.

## Verification
All builds and test runs were executed exclusively inside isolated snapshot `build-snap-T517/` (`HEAD 3aabc4d98163`):
- **Stage-2/3 Selfhost Fixed-Point & Stage-0 Smoke Parity**:
  - Command: `python tools/build_axiomc.py --out build --root . --stage 3`
  - Result: `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == e555fd40393b72871a631198c9db538afa41784b0fe6dc882c1cbf3077a4ee64` (`8590848` bytes) `[seeded B==C]`; `STAGE0-GUARD OK` (byte-identical `.exe` on all 6 smoke programs).
- **Security Profile Test Suite (`--no-cache -j 2 --verbose`)**:
  - Command: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 --verbose --filter ui/security_profiles`
  - Result: `TOTAL 14 PASS 14 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
  - Mutation spot-proof on `safety_profile_safe_run.stdout` inside `build-snap-T517/`: mutating `386` -> `999` caused `3/3 FAIL` (`interp`, `native`, `native-O1`); restoring byte-identical passed `3/3 PASS` (`WEAK-NATIVE 0`).
- **Taskgate (`-j 2`)**:
  - Command: `python tools/taskgate.py --task T517 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T517.json`
  - Result: `TASKGATE T517 exit=0` (`TOTAL 444 PASS 442 FAIL 0 SKIP 2 XFAIL 0`, `WEAK-NATIVE: 0 in the task's own/changed tests`, `BASELINE OK`, `archcheck: clean (232 files scanned, 0 violations)`).

## Files changed
- compiler/diag/code.ax
- compiler/driver/mod.ax
- compiler/driver/opts.ax
- compiler/driver/pipeline.ax
- compiler/types/mod.ax
- compiler/types/typeck.ax
- tests/ui/security_profiles/capability_forgery_neg.ax
- tests/ui/security_profiles/comptime_ambient_isolation_neg.ax
- tests/ui/security_profiles/conflicting_safety_policy_neg.ax
- tests/ui/security_profiles/forbid_unsafe_constructs_neg.ax
- tests/ui/security_profiles/mixed_forbid_and_system_neg.ax
- tests/ui/security_profiles/safety_profile_cli_and_manifest.test
- tests/ui/security_profiles/safety_profile_cli_and_manifest_oracle.py
- tests/ui/security_profiles/safety_profile_safe_neg.ax
- tests/ui/security_profiles/safety_profile_safe_run.ax
- tests/ui/security_profiles/safety_profile_safe_run.stdout
- tests/ui/security_profiles/sandbox_ambient_authority_neg.ax
- tests/ui/security_profiles/sandbox_capability_ok.ax
- tests/ui/security_profiles/sandbox_unsafe_no_authority_neg.ax
- tests/ui/security_profiles/spec53_canonical_neg.ax

## Status
STATUS: COMPLETE round=0
