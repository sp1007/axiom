---
id: T672
title: E16.5 — Android AArch64 Bionic ELF (.so/PIE) & JNI ownership/exception bridge conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T313, T671]
priority: 115
status: todo
attempts: 0
paths: [tests/conformance/p16/e16_5_android_aarch64_jni]
spec: [spec/SPEC-85-android-aarch64-jni.md, 0198, 0200]
covers: [REQ-TGT-270, REQ-TGT-272, REQ-TGT-273, REQ-TGT-282]
---
# T672 — E16.5 — Android AArch64 Bionic ELF (.so/PIE) & JNI ownership/exception bridge conformance suite

## Goal
Certify the E16.5 exit criterion (`ROADMAP.md` §3): `aarch64-android` Bionic ELF64 `.so` and PIE generation (without requiring an external Android NDK) and capability-safe JNI reference/exception/thread management (`0198`, `0200`).

## Scope
- Create `tests/conformance/p16/e16_5_android_aarch64_jni` covering:
  - `aarch64-android` `.so` and PIE ELF64 binary inspection: `.note.android.ident` API level metadata, 16 KiB `PT_LOAD` alignment, `X18` preservation for Android ShadowCallStack, `/system/bin/linker64` interpreter, `DT_SONAME`, and exported `Java_*` / `JNI_OnLoad` symbols.
  - JNI reference lifetime & drop tests using the mock-JVM harness: verify exact `NewLocalRef`/`DeleteLocalRef`, `NewGlobalRef`/`DeleteGlobalRef`, `PushLocalFrame`/`PopLocalFrame`, and `AttachCurrentThread`/`DetachCurrentThread` call counts across normal returns, early `?` returns, and panics.
  - JNI exception bridge tests: Java exception pending after `CallObjectMethod` converted to `Result.Err(JException)`; Axiom error/panic inside `@jni_export` caught and converted to `ThrowNew` without unwinding across the C/JVM boundary.
  - Negative UI tests: attempting to store `view<JniEnv>` in a struct/static, send `JLocal<T>` to another thread, or use a `JLocal` after its `with_local_frame` scope ends is rejected at compile time.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p16/e16_5_android_aarch64_jni` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T672-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation changes (belong in `T670`–`T671`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:40:00 created by T216 (P16 phase planning)
