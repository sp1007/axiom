---
id: T758
title: E18.2 — Persistent on-disk query/codegen cache, action digest validation & no-op fast path
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T757]
priority: 708
status: doing
attempts: 1
paths: [compiler/incremental/cache, tests/run/incremental_cache]
spec: [spec/SPEC-22-incremental-compilation.md, 0142, tasks/0778, tasks/0788, tasks/0789, tasks/0792]
covers: [REQ-LNK-714, REQ-LNK-715, REQ-LNK-716, REQ-LNK-717, REQ-LNK-718, REQ-LNK-719, REQ-LNK-720, REQ-LNK-721, REQ-LNK-722, REQ-LNK-723, REQ-LNK-724, REQ-LNK-725, REQ-LNK-726, REQ-LNK-727, REQ-LNK-728, REQ-LNK-729, REQ-LNK-730, REQ-LNK-731, REQ-LNK-732, REQ-LNK-733, REQ-LNK-734, REQ-LNK-735, REQ-LNK-736, REQ-LNK-737, REQ-LNK-738, REQ-LNK-739, REQ-LNK-740, REQ-LNK-741, REQ-LNK-742, REQ-LNK-743, REQ-LNK-744, REQ-LNK-745, REQ-LNK-746, REQ-LNK-747, REQ-LNK-748, REQ-LNK-749, REQ-LNK-750, REQ-LNK-751, REQ-LNK-752, REQ-LNK-753, REQ-LNK-754, REQ-LNK-755, REQ-LNK-756, REQ-LNK-757, REQ-LNK-758, REQ-LNK-759, REQ-LNK-760, REQ-LNK-761, REQ-LNK-762, REQ-LNK-763, REQ-LNK-764, REQ-LNK-765, REQ-LNK-766, REQ-LNK-767, REQ-LNK-768, REQ-LNK-769, REQ-LNK-770, REQ-LNK-771, REQ-LNK-772, REQ-LNK-773, REQ-LNK-774, REQ-LNK-775, REQ-LNK-776, REQ-LNK-777, REQ-LNK-778, REQ-LNK-779, REQ-LNK-780, REQ-LNK-781, REQ-LNK-782, REQ-LNK-783, REQ-LNK-784, REQ-LNK-785, REQ-LNK-786, REQ-LNK-787, REQ-LNK-788, REQ-LNK-789, REQ-LNK-790, REQ-LNK-791, REQ-LNK-792, REQ-LNK-793, REQ-LNK-794, REQ-LNK-795, REQ-LNK-796, REQ-LNK-797, REQ-LNK-798, REQ-LNK-799, REQ-LNK-800, REQ-LNK-801, REQ-LNK-802, REQ-LNK-803, REQ-LNK-834, REQ-LNK-835, REQ-LNK-836, REQ-LNK-837, REQ-LNK-838, REQ-LNK-839, REQ-LNK-840, REQ-LNK-841, REQ-LNK-842, REQ-LNK-843, REQ-LNK-844, REQ-LNK-845, REQ-LNK-846, REQ-LNK-847, REQ-LNK-848, REQ-LNK-849, REQ-LNK-850, REQ-LNK-851, REQ-LNK-852, REQ-LNK-853, REQ-LNK-854, REQ-LNK-855, REQ-LNK-856, REQ-LNK-857, REQ-LNK-858, REQ-LNK-859, REQ-LNK-860, REQ-LNK-861, REQ-LNK-862, REQ-LNK-863, REQ-LNK-864, REQ-LNK-865, REQ-LNK-866, REQ-LNK-867, REQ-LNK-868, REQ-LNK-869, REQ-LNK-870, REQ-LNK-871, REQ-LNK-872, REQ-LNK-873, REQ-LNK-874, REQ-LNK-875, REQ-LNK-876, REQ-LNK-877, REQ-LNK-878, REQ-LNK-879, REQ-LNK-880, REQ-LNK-881, REQ-LNK-882, REQ-LNK-883, REQ-LNK-884, REQ-LNK-885, REQ-LNK-886, REQ-LNK-887, REQ-LNK-888, REQ-LNK-889, REQ-LNK-890, REQ-LNK-891, REQ-LNK-892, REQ-LNK-893, REQ-LNK-894, REQ-LNK-895, REQ-LNK-896, REQ-LNK-897, REQ-LNK-898, REQ-LNK-899, REQ-LNK-900, REQ-LNK-901, REQ-LNK-902, REQ-LNK-903, REQ-LNK-904, REQ-LNK-905, REQ-LNK-906, REQ-LNK-907, REQ-LNK-908, REQ-LNK-909, REQ-LNK-910, REQ-LNK-911, REQ-LNK-912, REQ-LNK-913, REQ-LNK-914, REQ-LNK-915, REQ-LNK-916, REQ-LNK-917, REQ-LNK-918, REQ-LNK-919, REQ-LNK-920, REQ-LNK-921, REQ-LNK-922, REQ-LNK-923, REQ-LNK-924, REQ-LNK-925, REQ-LNK-926, REQ-LNK-927, REQ-LNK-928, REQ-LNK-929, REQ-LNK-930, REQ-LNK-931, REQ-LNK-932, REQ-LNK-933]
started: 2026-11-07 21:29:56
agent: T758-impl
---
# T758 — E18.2 — Persistent on-disk query/codegen cache, action digest validation & no-op fast path

## Goal
Implement the persistent on-disk incremental dependency graph and object/codegen cache, hermetic action digest validation, and the `< 100 ms` no-op rebuild fast path in `compiler/incremental/cache` per `spec/SPEC-22-incremental-compilation.md`.

## Scope
- Implement versioned, checksummed on-disk persistence in `compiler/incremental/cache` for the query dependency graph, item fingerprints, cached diagnostics, and per-module `.obj` artifacts (`tasks/0788`, `tasks/0789`).
- Key the cache by compiler binary digest, target triple, optimization level, safety profile, and manifest digest; gracefully evict and rebuild on schema mismatch or truncated cache files.
- Implement the root manifest/source-stat + content-digest fast check so a no-op rebuild of a multi-module workspace or the compiler itself completes in `< 100 ms`.
- Ensure cached rebuilds emit byte-identical `.obj`/`.exe` outputs and identical diagnostic streams to clean `--no-incremental` builds.

## Acceptance
- [ ] Tests in `tests/run/incremental_cache` verify cold-to-warm cache population, byte-identical output between clean and incremental builds, corruption recovery, and `< 100 ms` no-op rebuild on the compiler workspace.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T758-report.md` with exact `## Files changed`.

## Out of scope
- Parallel work-stealing execution (`E18.3` `T760`–`T763`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T758/build` and `python tools/axtest.py --compiler build-snap-T758/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:57:30 created by T218 (P18 phase planning)
- 2026-11-07 21:29:56 started (attempt 1) T758-impl
