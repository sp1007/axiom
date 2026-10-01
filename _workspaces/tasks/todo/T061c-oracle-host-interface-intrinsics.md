---
id: T061c
title: Host-interface intrinsics: oracle implementation + native call lowering
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T061b, T060]
priority: 82
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/interp, bootstrap/axiom0/src/types, bootstrap/axiom0/src/lir, std/core/host.ax, tests/run/host]
locks: [bootstrap/axiom0/src/diag/codes/IO.def, bootstrap/axiom0/src/diag/codes/TYPE.def, bootstrap/axiom0/src/driver/pipeline.c]
spec: [0025, 0031, 0169, 0170, 0219, spec/decisions/ADR-0002-oracle-host-interface.md, spec/SPEC-04-core-extensibility.md]
covers: []
---
# T061c — Host-interface intrinsics: oracle implementation + native call lowering

## Goal
Let the MIR interpreter run programs that use the heap and the OS, so std (P9) and the compiler port (P10) keep the three-level oracle (ADR-0002). Without this task every std test would be native-only.

## Scope
- Declarations `std/core/host.ax`: the intrinsic set of ADR-0002 §1 with the final names and signatures from SPEC-04 (heap alloc/realloc/free, write/read/open/close/file_size, remove/mkdir/metadata, directory iteration, args, env, exit, monotonic clock, stdio handles).
- Interpreter (`src/interp/host`): each intrinsic implemented in C over the T061a memory model — heap intrinsics create/free interpreter allocations; buffer arguments must lie inside a live allocation (bounds-checked); Windows W APIs internally, UTF-8 at the boundary; `args` come from `axiom0 run --interp file.ax -- <args>` (T016).
- Native: a call of `host.X` lowers to a direct call of the Axiom function `__ax_host_X`; the std host module is added to every program that uses a host intrinsic (std root of T060). The implementations arrive in `std/sys/windows` with T070 (heap), T074 (stdio, files, args, env, exit) and T074b (remove, mkdir, metadata, directory listing, clock); until then a native build that needs a missing one reports an undefined-symbol link error.
- Tests in `tests/run/host/{heap,io,fs}` carry `// native-after: T070`, `T074` or `T074b` respectively.

## Acceptance
- [ ] Interp run tests: allocate/grow/free with the leak counter back at zero; use-after-free of a heap block is caught by the oracle; write to stdout (`Xin chào thế giới`, byte-exact) and stderr; write a file, read it back, compare; `args` with `xin chào`; `env_get`; `exit(7)`; directory listing sorted by the test; `monotonic_ns` non-decreasing.
- [ ] Each test carries the `native-after` directive of its group; a native build of a heap test fails with the documented undefined-symbol diagnostic (ui/exec test), not a crash.
- [ ] A direct `extern` call reached by the interpreter is not handled here (T065 reports it).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T061c-report.md` with exact `## Files changed`.

## Out of scope
- The native implementations (`std/sys/windows`, T070/T074/T074b); an FFI bridge inside the interpreter (rejected by ADR-0002).
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Adding an intrinsic later needs an edit of SPEC-04, not an ADR (ADR-0002 §1).
- axiomc's interpreter port implements the same intrinsics by calling std directly (ADR-0002 §6).
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
