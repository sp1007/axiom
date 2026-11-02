---
id: T774
title: E18.6 — Canonical separate compilation, multi-object linking & section GC specification (SPEC-27)
phase: P18-compiler-architecture-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T764, T772]
priority: 722
status: todo
attempts: 0
paths: [spec/SPEC-27-separate-compilation-linker-v2.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-24-artifact-format-module-interfaces.md, spec/SPEC-26-windows-artifact-kinds.md, 0099, 0164, 0185, 0217, 0239, 0256, tasks/0369, tasks/0526, tasks/0786, tasks/0802, tasks/0803, tasks/0804]
covers: [REQ-LNK-001, REQ-LNK-002, REQ-LNK-003, REQ-LNK-004, REQ-LNK-005, REQ-LNK-006, REQ-LNK-007, REQ-LNK-008, REQ-LNK-009, REQ-LNK-010, REQ-LNK-011, REQ-LNK-012, REQ-LNK-013, REQ-LNK-014, REQ-LNK-015, REQ-LNK-016, REQ-LNK-017, REQ-LNK-018, REQ-LNK-019, REQ-LNK-020, REQ-LNK-021, REQ-LNK-022, REQ-LNK-023, REQ-LNK-024, REQ-LNK-025, REQ-LNK-026, REQ-LNK-027, REQ-LNK-028, REQ-LNK-029, REQ-LNK-030, REQ-LNK-031, REQ-LNK-032, REQ-LNK-033, REQ-LNK-034, REQ-LNK-035, REQ-LNK-036, REQ-LNK-037, REQ-LNK-038, REQ-LNK-039, REQ-LNK-040, REQ-LNK-041, REQ-LNK-042, REQ-LNK-043, REQ-LNK-044, REQ-LNK-045, REQ-LNK-046, REQ-LNK-047, REQ-LNK-048, REQ-LNK-049, REQ-LNK-050, REQ-LNK-051, REQ-LNK-052, REQ-LNK-053, REQ-LNK-054, REQ-LNK-055, REQ-LNK-056, REQ-LNK-122, REQ-LNK-123, REQ-LNK-124, REQ-LNK-125, REQ-LNK-126, REQ-LNK-127, REQ-LNK-128, REQ-LNK-129, REQ-LNK-130, REQ-LNK-131, REQ-LNK-132, REQ-LNK-133, REQ-LNK-134, REQ-LNK-135, REQ-LNK-136, REQ-LNK-137, REQ-LNK-138, REQ-LNK-139, REQ-LNK-140, REQ-LNK-141, REQ-LNK-142, REQ-LNK-143, REQ-LNK-144, REQ-LNK-145, REQ-LNK-146, REQ-LNK-147, REQ-LNK-148, REQ-LNK-149, REQ-LNK-150, REQ-LNK-151, REQ-LNK-152, REQ-LNK-153, REQ-LNK-154, REQ-LNK-155, REQ-LNK-156, REQ-LNK-157, REQ-LNK-158, REQ-LNK-159, REQ-LNK-160, REQ-LNK-3434, REQ-LNK-3435, REQ-LNK-3436, REQ-LNK-3437, REQ-LNK-3438, REQ-LNK-3439, REQ-LNK-3440, REQ-LNK-3441, REQ-LNK-3442, REQ-LNK-3443, REQ-LNK-3444, REQ-LNK-3445, REQ-LNK-3446, REQ-LNK-3447, REQ-LNK-3448, REQ-LNK-3449, REQ-LNK-3450, REQ-LNK-3451, REQ-LNK-3452, REQ-LNK-3453, REQ-LNK-3454, REQ-LNK-3455, REQ-LNK-3456, REQ-LNK-3457, REQ-LNK-3458, REQ-LNK-3459, REQ-LNK-3460, REQ-LNK-3461, REQ-LNK-3462, REQ-LNK-3463, REQ-LNK-3464, REQ-LNK-3465, REQ-LNK-3466, REQ-LNK-3467, REQ-LNK-3468, REQ-LNK-3469, REQ-LNK-3470, REQ-LNK-3471, REQ-LNK-3472, REQ-LNK-3473, REQ-LNK-3474, REQ-LNK-3475, REQ-LNK-3476, REQ-LNK-3477, REQ-LNK-3478, REQ-LNK-3479, REQ-LNK-3480, REQ-LNK-3481, REQ-LNK-3482, REQ-LNK-3483, REQ-LNK-3484, REQ-LNK-3485, REQ-LNK-3486, REQ-LNK-3487, REQ-LNK-3488, REQ-LNK-3489, REQ-LNK-3490, REQ-LNK-3491, REQ-LNK-3492, REQ-LNK-3493, REQ-LNK-3494, REQ-LNK-3495, REQ-LNK-3496, REQ-LNK-3497, REQ-LNK-3498, REQ-LNK-3499, REQ-LNK-3500, REQ-LNK-3501, REQ-LNK-3502, REQ-LNK-3503, REQ-LNK-3504, REQ-LNK-3505, REQ-LNK-3506, REQ-LNK-3507, REQ-LNK-3508, REQ-LNK-3509, REQ-LNK-3510, REQ-LNK-3511, REQ-LNK-3512, REQ-LNK-3513, REQ-LNK-3514, REQ-LNK-3515, REQ-LNK-3516, REQ-LNK-3517, REQ-LNK-3518, REQ-LNK-3519, REQ-LNK-3520, REQ-LNK-3521, REQ-LNK-3522, REQ-LNK-3523, REQ-LNK-3524, REQ-LNK-3525, REQ-LNK-3526, REQ-LNK-3527, REQ-LNK-3528, REQ-LNK-3529, REQ-LNK-3530, REQ-LNK-3531, REQ-LNK-3532, REQ-LNK-3533, REQ-LNK-3534, REQ-LNK-3535, REQ-LNK-3536, REQ-LNK-3537, REQ-LNK-3538, REQ-LNK-3539, REQ-LNK-3540, REQ-LNK-3541, REQ-LNK-3542, REQ-LNK-3543, REQ-LNK-3544, REQ-LNK-3545, REQ-LNK-3546, REQ-LNK-3547, REQ-LNK-3548, REQ-LNK-3549, REQ-LNK-3550, REQ-LNK-3551, REQ-LNK-3552, REQ-LNK-3553, REQ-LNK-3554, REQ-LNK-3555, REQ-LNK-3556, REQ-LNK-3557, REQ-LNK-3558, REQ-LNK-3559, REQ-LNK-3560, REQ-LNK-3561, REQ-LNK-3562, REQ-LNK-3563, REQ-LNK-3564, REQ-LNK-3565, REQ-LNK-3566, REQ-LNK-3567, REQ-LNK-3568, REQ-LNK-3569, REQ-LNK-3570, REQ-LNK-3571, REQ-LNK-3572, REQ-LNK-3573, REQ-LNK-3574, REQ-LNK-3575, REQ-LNK-3576, REQ-LNK-3577, REQ-LNK-3578, REQ-LNK-3579, REQ-LNK-3580, REQ-LNK-3581, REQ-LNK-3582, REQ-LNK-3583, REQ-LNK-3584, REQ-LNK-3585, REQ-LNK-3586, REQ-LNK-3587, REQ-LNK-3588, REQ-LNK-3589, REQ-LNK-3590, REQ-LNK-3591, REQ-LNK-3592, REQ-LNK-3593, REQ-LNK-3594, REQ-LNK-3595, REQ-LNK-3596, REQ-LNK-3597, REQ-LNK-3598, REQ-LNK-3599, REQ-LNK-3600, REQ-LNK-3601, REQ-LNK-3602, REQ-LNK-3603, REQ-LNK-3604, REQ-LNK-3605, REQ-LNK-3606, REQ-LNK-3607, REQ-LNK-3608, REQ-LNK-3609, REQ-LNK-3610, REQ-LNK-3611, REQ-LNK-3612, REQ-LNK-3613, REQ-LNK-3614, REQ-LNK-3615, REQ-LNK-3616, REQ-LNK-3617, REQ-LNK-3618, REQ-LNK-3619, REQ-LNK-3620, REQ-LNK-3621, REQ-LNK-3622, REQ-LNK-3623, REQ-LNK-3624, REQ-LNK-3625, REQ-LNK-3626, REQ-LNK-3627, REQ-LNK-3628, REQ-LNK-3629, REQ-LNK-3630, REQ-LNK-3631, REQ-LNK-3632, REQ-LNK-3633]
---
# T774 — E18.6 — Canonical separate compilation, multi-object linking & section GC specification (SPEC-27)

## Goal
Consolidate the canonical specification for Axiom's separate compilation model, `LinkIR` multi-object and archive linking, cross-object symbol resolution, `COMDAT` generic deduplication, and reachability-based section garbage collection (`section GC`) into `spec/SPEC-27-separate-compilation-linker-v2.md` (`AXS-LNK-*` rule IDs).

## Scope
- Write `spec/SPEC-27-separate-compilation-linker-v2.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-LNK-NNN` rules.
- Specify the separate-compilation contract (`0099`, `0164`, `0217`, `tasks/0369`, `tasks/0786`, `tasks/0804`): compiling each module to its own `.obj` + `.axmi` and linking multiple `.obj` files and `.lib` archives in deterministic canonical order.
- Specify `LinkIR` (`0256`, `tasks/0526`), strong vs weak/`COMDAT` symbol resolution (`IMAGE_SCN_LNK_COMDAT` for monomorphized generic instantiations and vtables), and structured duplicate/undefined symbol diagnostics carrying demangled Axiom paths and source spans.
- Specify per-function/per-datum section emission (`-ffunction-sections` / `-fdata-sections` equivalent) and root-set reachability section GC (`@entry`, `@export`, `@used`, `@at` fixed-address roots, `.pdata`/`.xdata` unwind associations, and runtime reflection roots).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-27-separate-compilation-linker-v2.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-LNK-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T774-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of multi-object linking and section GC (`T067`, `T775`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 03:01:00 created by T218 (P18 phase planning)
