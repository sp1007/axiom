# T516 Report — E13.4 Canonical Safety Profiles, Ambient-Authority Ban, Secure Memory & Constant-Time Specification (`SPEC-53`)

## Summary
- Authored `spec/SPEC-53-safety-profiles-capability-security.md` (`AXS-SEC-001`..`AXS-SEC-053`) with a Vietnamese `## Tóm tắt`, canonical rules, positive/negative Axiom examples (`=` and `.` syntax), diagnostic taxonomy, and requirement/task traceability matrix for Epic `E13.4` (`T516`–`T520`):
  - **Section 1 (`AXS-SEC-001`..`005`)**: Orthogonal separation of language safety (`SAFE` vs `UNSAFE`), capability-based OS resource authority, and source/boundary trust; compilation safety profiles (`--safety-profile safe|sandbox|system`, `AX_DRIVER_INVALID_SAFETY_PROFILE`); module and package `@forbid_unsafe` / `@allow_unsafe` policy attributes with monotonic non-escalation (`AX_SEC_UNSAFE_FORBIDDEN`, `AX_SEC_CONFLICTING_SAFETY_POLICY`); non-owning capability provenance (`REQ-CAP-010`) vs raw pointers (`*const T`, `*mut T`), integer addresses (`usize`), and WASM linear-memory offsets (`REQ-CAP-123`, `REQ-FFI-124`, `AX_SEC_CAPABILITY_FORGERY`); and untrusted FFI boundaries (`REQ-FFI-117`) plus target-specific calling conventions (`REQ-ABI-046`).
  - **Section 2 (`AXS-SEC-010`..`014`)**: Resource authority capability tokens (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`) vs memory capabilities (`view<T>`, `mut_view<T>`); prohibition of ambient OS authority in `--safety-profile sandbox` and `comptime` evaluation with strict `comptime` $\leftrightarrow$ `runtime` authority isolation (`REQ-CAP-131`, `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`); monotonic capability attenuation (`attenuate_subpath`, `attenuate_endpoint`, `attenuate_prefix`); zero-copy scatter/gather I/O segment non-overlap (`REQ-CAP-135`, `REQ-CAP-139`, `AX_CAP_IO_BUFFER_OVERLAP`), `MappedRegion` lifetime/exclusivity (`REQ-CAP-136`), database buffer-pool `PagePin<T>` eviction protection (`REQ-CAP-137`), and timer callback capture lifetime safety (`REQ-CAP-138`); and compiler-proven zero-copy deserialization (`REQ-CAP-141`, `AX_CAP_ZERO_COPY_DESERIALIZE_UNPROVEN`).
  - **Section 3 (`AXS-SEC-020`..`024`)**: `Secret<T>` and `@secret` contract forbidding implicit `Copy` (`AX_SEC_SECRET_IMPLICIT_COPY`), redacting `Debug`/`Display` and compiler diagnostics (`"<secret>"`, `AX_SEC_SECRET_EXPOSURE`), and scrubbing memory deterministically on `Drop` via `Zeroize` and optimization-proof `zeroize_memory` / `black_box` barriers (`REQ-OPT-353`); secret taint lattice (`Public`, `Secret`, `Unknown`) and explicit `declassify`; `@constant_time` verification rejecting secret-dependent branches, secret-indexed memory accesses, and variable-latency instructions (`DIV`/`IDIV`/`REM`) (`AX_SEC_TIMING_LEAK`); and branchless `ct_eq`, `ct_select` (`CMOVcc`), `ct_swap_if`, and `ct_copy_if` primitives.
  - **Section 4 (`AXS-SEC-050`..`053`)**: Diagnostic table, positive/negative canonical Axiom examples, and requirement traceability (`REQ-CAP-010`, `REQ-CAP-123`, `REQ-FFI-117`, `REQ-CAP-131`, `REQ-ABI-046`, `REQ-FFI-124`, `REQ-CAP-135`..`139`, `REQ-CAP-141`, `REQ-OPT-353`).
- Updated `spec/INDEX.md` (§2 Canonical documents, §4 `AXS-SEC-NNN` namespace, §5 Topic → canonical source).
- Updated `spec/diagnostics.md` (`AXD-021` `SEC` area registration for `axiomc`, §11 `SPEC-53` diagnostic codes, and `## Sources`).
- Updated `spec/invariants.md` (§18 `INV-SEC-001`..`INV-SEC-004` and `## Sources`).

## Files changed
- `spec/SPEC-53-safety-profiles-capability-security.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python tools/gatecheck.py --no-run`: `MS-P1`..`MS-P10b PASS`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T516`: `0 REFUSED` lines.

STATUS: COMPLETE round=0
