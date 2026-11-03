---
id: T669
title: E16.5 — Canonical Android AArch64 Bionic ELF target & capability-safe JNI binding specification (SPEC-85)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T511, T657, T661]
priority: 112
status: todo
attempts: 0
paths: [spec/SPEC-85-android-aarch64-jni.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-82-linux-elf-dynamic.md, spec/SPEC-83-aarch64-linux.md, 0198, 0200, 0220, tasks/0453]
covers: [REQ-TGT-069, REQ-TGT-070, REQ-TGT-071, REQ-TGT-072]
---
# T669 — E16.5 — Canonical Android AArch64 Bionic ELF target & capability-safe JNI binding specification (SPEC-85)

## Goal
Consolidate the canonical specification for Axiom's `aarch64-android` target, Bionic dynamic linking (`ET_DYN` PIE and `.so` artifacts without requiring an installed Android NDK), and the 3-layer capability-safe JNI binding architecture into `spec/SPEC-85-android-aarch64-jni.md` (`AXS-ANDR-*` and `AXS-JNI-*` rule IDs).

## Scope
- Write `spec/SPEC-85-android-aarch64-jni.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-ANDR-NNN` and `AXS-JNI-NNN` rules (`0198`, `0200`, `0220 §9`).
- Specify the `aarch64-android` target descriptor (`0198 §1–13`): API level as part of target identity (`default api_level = 29`), AAPCS64 calling convention (`X18` reserved for ShadowCallStack on Android), mandatory PIE (`ET_DYN`) for executables (`/system/bin/linker64` `PT_INTERP`) and shared libraries (`lib<name>.so` with `DT_SONAME`), 16 KiB (`0x4000`) `PT_LOAD` maximum page alignment (Android 15+ requirement), `.note.android.ident` ELF note, Android linker namespace rules (`libc.so`, `libm.so`, `libdl.so`, `liblog.so`), and NDK-free compilation via built-in Bionic stub symbol catalogs (`0198 §4`).
- Specify the 3-layer JNI binding architecture (`0200 §1–19`):
  - **Layer 1 (`std.ffi.jni.raw`)**: Raw C ABI `JNIEnv*`, `JavaVM*`, `jobject`, `jclass`, `jmethodID`, `jfieldID`, `JNINativeInterface_` vtable pointers (`unsafe`).
  - **Layer 2 (`std.ffi.jni`)**: Capability-scoped safe wrappers — `view<JniEnv>` cannot be stored or sent across threads (`!Send`, `!Share`), `JLocal<T>` tied to the active `JniEnv` frame and calling `DeleteLocalRef` on `Drop`, `JGlobal<T>` and `JWeak<T>` (`Send + Share`) calling `DeleteGlobalRef`/`DeleteWeakGlobalRef` on `Drop`, `with_local_frame(env, cap, |frame_env| ...)` (`PushLocalFrame`/`PopLocalFrame`), `JavaVM.with_attached_env(|env| ...)` (`AttachCurrentThread`/`DetachCurrentThread`), `JString` UTF-8/modified-UTF-8 conversion and primitive array views (`GetPrimitiveArrayCritical` / `GetByteArrayElements`), and mandatory `ExceptionCheck` + conversion of pending Java exceptions to `Result<T, JException>` before returning to Axiom.
  - **Layer 3 (`@jni_export`)**: Compiler-generated `extern "C"` JNI entry wrappers (`Java_<pkg>_<cls>_<method>` and `JNI_OnLoad` `RegisterNatives` tables) that construct a scoped `view<JniEnv>`, catch Axiom panics or `Err(JException)` at the boundary (throwing a Java exception via `ThrowNew` instead of unwinding into the JVM), and prevent `JLocal` escape.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-85-android-aarch64-jni.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-ANDR-NNN` and `AXS-JNI-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T669-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and stdlib implementation (`T670`, `T671`).
- APK/AAB packaging (explicitly separated from `.so` generation per `0198 §6`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 08:40:00 created by T216 (P16 phase planning)
