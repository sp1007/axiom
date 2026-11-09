---
id: T573
title: E14.1 — Sandboxed compile-time asset embedding (@embed_bytes, @embed_str) & package root containment
phase: P14-comptime-2-0-reflection-genera
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T551, T554]
priority: 195
status: todo
attempts: 0
paths: [compiler/mir, compiler/interp, compiler/lir, compiler/obj, tests/ui/embed, tests/run/embed]
spec: [spec/SPEC-60-comptime-2-0.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-EXP-087, REQ-EXP-088]
---
# T573 — E14.1 — Sandboxed compile-time asset embedding (@embed_bytes, @embed_str) & package root containment

## Goal
Implement hermetic compile-time asset embedding intrinsics `@embed_bytes("path")` -> `view<u8>` and `@embed_str("path")` -> `view<str>` with strict package-root containment, UTF-8 verification, 64 MiB limit, BLAKE3 invalidation tracking, and `.rdata` section materialization.

## Scope
- Implement parser and semantic lowering for `@embed_bytes("relative/path")` and `@embed_str("relative/path")` in `compiler/parser`, `compiler/hir`, and `compiler/types`.
- Enforce compile-time sandboxing: paths are strictly relative to the package manifest root; reject path traversal (`..` components) or symlink escapes outside the package root with diagnostic `AX_CONST_EMBED_PATH_TRAVERSAL`.
- Enforce size and encoding constraints: reject assets larger than 64 MiB with `AX_CONST_EMBED_TOO_LARGE`; for `@embed_str`, validate valid UTF-8 byte sequences at compile-time with `AX_CONST_EMBED_INVALID_UTF8`.
- In `compiler/interp` and `compiler/lir`/`compiler/obj`, materialize embedded slices as immutable `.rdata` anonymous byte buffers with null-terminator padding for string slices, recording asset file hashes (BLAKE3) for incremental compilation dependency tracking.

## Acceptance
- [ ] Negative UI tests in `tests/ui/embed` verify rejection of directory traversal (`../secret.txt`), invalid UTF-8 in `@embed_str`, and assets exceeding 64 MiB.
- [ ] Run tests in `tests/run/embed` verify reading embedded byte and string views in both `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T573-report.md` with exact `## Files changed`.

## Out of scope
- Runtime filesystem access (`std.fs`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T573/build` and `python tools/axtest.py --compiler build-snap-T573/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:05:00 created by axiom-architect (ADR-0039 P14 asset embedding expansion)
