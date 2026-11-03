---
id: T671
title: E16.5 — Capability-safe JNI binding layer (std.ffi.jni: JniEnv, JLocal, JGlobal, JavaVM & @jni_export)
phase: P16-targets-platforms
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T313, T670]
priority: 114
status: todo
attempts: 0
paths: [std/ffi/jni, compiler/hir/jni_attr, tests/run/jni, tests/selfhost/hir]
spec: [spec/SPEC-85-android-aarch64-jni.md, 0198, 0200]
covers: [REQ-TGT-074, REQ-TGT-075, REQ-TGT-110, REQ-TGT-230]
---
# T671 — E16.5 — Capability-safe JNI binding layer (std.ffi.jni: JniEnv, JLocal, JGlobal, JavaVM & @jni_export)

## Goal
Implement the 3-layer capability-safe JNI binding library in `std/ffi/jni` and the `@jni_export` attribute lowering in `compiler/hir/jni_attr`.

## Scope
- Implement `std/ffi/jni`:
  - `std.ffi.jni.raw`: C ABI structs and function-pointer tables for `JNIEnv`, `JavaVM`, `JNINativeInterface_`, `JNIInvokeInterface_`, `JNINativeMethod`, `jobject`, `jclass`, `jstring`, `jthrowable`, `jmethodID`, `jfieldID`, `jvalue`.
  - `std.ffi.jni`: Capability-scoped `JniEnv` (`!Send`, `!Share`, usable only through `view<JniEnv>` / `mut_view<JniEnv>`), `JLocal<T>` (deterministic `DeleteLocalRef` in `Drop`, non-`Send`, non-storable in globals), `JGlobal<T>` and `JWeak<T>` (`Send + Share`, deterministic `DeleteGlobalRef`/`DeleteWeakGlobalRef` in `Drop`), `with_local_frame`, `JavaVM.with_attached_env` (RAII `AttachCurrentThread`/`DetachCurrentThread`), `JClass`/`JMethodId`/`JFieldId` lookup, `JString` UTF-8 conversion, byte/primitive array critical/element views, and automatic `ExceptionCheck`/`ExceptionClear` converting pending JVM exceptions into `Result<T, JException>`.
- Implement `@jni_export(package = "...", class = "...")` in `compiler/hir/jni_attr`: lower annotated Axiom functions into `extern "C"` JNI symbols (`Java_<pkg>_<cls>_<name>`) that wrap the raw `JNIEnv*` in a scoped `mut_view<JniEnv>`, forbid returning a `JLocal` directly without promotion/release, and catch Axiom errors/panics at the JNI boundary (`ThrowNew` + safe zero/null return).
- Add tests (using a deterministic in-process mock `JNIEnv`/`JavaVM` vtable so JNI logic runs under both `--interp` and native on all hosts) in `tests/run/jni` and `tests/selfhost/hir`.

## Acceptance
- [ ] `std.ffi.jni` and `@jni_export` pass positive and negative tests in `tests/run/jni` and `tests/selfhost/hir` (including compile-time rejection of escaping `view<JniEnv>` or sending `JLocal` across threads).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T671-report.md` with exact `## Files changed`.

## Out of scope
- Full Android + JNI conformance suite (`T672`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:40:00 created by T216 (P16 phase planning)
