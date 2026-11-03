---
id: T766
title: E18.4 — Axiom object/LTO/semantic package container sections & schema-versioned reader/writer
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T765]
priority: 716
status: todo
attempts: 0
paths: [compiler/artifact/container, tests/run/artifact_container]
spec: [spec/SPEC-24-artifact-format-module-interfaces.md, 0164, tasks/0591, tasks/0739, tasks/0787, tasks/0803]
covers: [REQ-LNK-574, REQ-LNK-575, REQ-LNK-576, REQ-LNK-577, REQ-LNK-578, REQ-LNK-579, REQ-LNK-580, REQ-LNK-581, REQ-LNK-582, REQ-LNK-583, REQ-LNK-584, REQ-LNK-585, REQ-LNK-586, REQ-LNK-587, REQ-LNK-588, REQ-LNK-589, REQ-LNK-590, REQ-LNK-591, REQ-LNK-592, REQ-LNK-593, REQ-LNK-594, REQ-LNK-595, REQ-LNK-596, REQ-LNK-597, REQ-LNK-598, REQ-LNK-599, REQ-LNK-600, REQ-LNK-601, REQ-LNK-602, REQ-LNK-603, REQ-LNK-604, REQ-LNK-605, REQ-LNK-606, REQ-LNK-607, REQ-LNK-608, REQ-LNK-609, REQ-LNK-610, REQ-LNK-611, REQ-LNK-612, REQ-LNK-613, REQ-LNK-3634, REQ-LNK-3635, REQ-LNK-3636, REQ-LNK-3637, REQ-LNK-3638, REQ-LNK-3639, REQ-LNK-3640, REQ-LNK-3641, REQ-LNK-3642, REQ-LNK-3643, REQ-LNK-3644, REQ-LNK-3645, REQ-LNK-3646, REQ-LNK-3647, REQ-LNK-3648, REQ-LNK-3649, REQ-LNK-3650, REQ-LNK-3651, REQ-LNK-3652, REQ-LNK-3653, REQ-LNK-3654, REQ-LNK-3655, REQ-LNK-3656, REQ-LNK-3657, REQ-LNK-3658, REQ-LNK-3659, REQ-LNK-3660, REQ-LNK-3661, REQ-LNK-3662, REQ-LNK-3663, REQ-LNK-3664, REQ-LNK-3665, REQ-LNK-3666, REQ-LNK-3667, REQ-LNK-3668, REQ-LNK-3669, REQ-LNK-3670, REQ-LNK-3671, REQ-LNK-3672, REQ-LNK-3673, REQ-LNK-3674, REQ-LNK-3675, REQ-LNK-3676, REQ-LNK-3677, REQ-LNK-3678, REQ-LNK-3679, REQ-LNK-3680, REQ-LNK-3681, REQ-LNK-3682, REQ-LNK-3683, REQ-LNK-3684, REQ-LNK-3685, REQ-LNK-3686, REQ-LNK-3687, REQ-LNK-3688, REQ-LNK-3689, REQ-LNK-3690, REQ-LNK-3691, REQ-LNK-3692, REQ-LNK-3693, REQ-LNK-3694, REQ-LNK-3695, REQ-LNK-3696, REQ-LNK-3697, REQ-LNK-3698, REQ-LNK-3699, REQ-LNK-3700, REQ-LNK-3701, REQ-LNK-3702, REQ-LNK-3703, REQ-LNK-3704, REQ-LNK-3705, REQ-LNK-3706, REQ-LNK-3707, REQ-LNK-3708, REQ-LNK-3709, REQ-LNK-3710, REQ-LNK-3711, REQ-LNK-3712, REQ-LNK-3713, REQ-LNK-3714, REQ-LNK-3715, REQ-LNK-3716, REQ-LNK-3717, REQ-LNK-3718, REQ-LNK-3719, REQ-LNK-3720, REQ-LNK-3721, REQ-LNK-3722, REQ-LNK-3723, REQ-LNK-3724, REQ-LNK-3725, REQ-LNK-3726, REQ-LNK-3727, REQ-LNK-3728, REQ-LNK-3729, REQ-LNK-3730, REQ-LNK-3731, REQ-LNK-3732, REQ-LNK-3733, REQ-LNK-3734, REQ-LNK-3735, REQ-LNK-3736, REQ-LNK-3737, REQ-LNK-3738, REQ-LNK-3739, REQ-LNK-3740, REQ-LNK-3741, REQ-LNK-3742, REQ-LNK-3743]
---
# T766 — E18.4 — Axiom object/LTO/semantic package container sections & schema-versioned reader/writer

## Goal
Implement embedded `.axmeta` / `.axlto` COFF object sections and schema-versioned semantic package container reader/writer in `compiler/artifact/container` per `spec/SPEC-24-artifact-format-module-interfaces.md`.

## Scope
- Emit non-alloc (`IMAGE_SCN_LNK_INFO` / `IMAGE_SCN_MEM_DISCARDABLE`) `.axmeta` and `.axlto` sections into COFF `.obj` and `.lib` artifacts carrying the `.axmi` interface summary, LTO Verified MIR bitcode, and `InterfaceFingerprint` (`tasks/0787`, `tasks/0803`).
- Implement the schema-versioned section reader in `compiler/artifact/container` with magic-number, schema-version, target-triple, and checksum validation, emitting deterministic diagnostics on incompatible or corrupted artifacts.
- Ensure final `.exe`/`.dll` linking strips non-runtime `.axmeta`/`.axlto` sections while using them during link-time verification and LTO.

## Acceptance
- [ ] Tests in `tests/run/artifact_container` verify `.axmeta`/`.axlto` embedding in `.obj`, round-trip extraction, rejection of corrupted or mismatched-schema sections with clear diagnostics, and stripping from final `.exe`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T766-report.md` with exact `## Files changed`.

## Out of scope
- Multi-object archive linking and section GC (`E18.6` `T067`, `T774`–`T776`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T766/build` and `python tools/axtest.py --compiler build-snap-T766/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:58:55 created by T218 (P18 phase planning)
