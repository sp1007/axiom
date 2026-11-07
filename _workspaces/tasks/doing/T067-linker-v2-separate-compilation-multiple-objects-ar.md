---
id: T067
title: E18.6 — Linker v2: separate compilation, multiple objects, archives
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T774, T750, T766]
priority: 723
status: doing
attempts: 1
paths: [compiler/link, compiler/driver, tests/link2]
spec: [spec/SPEC-27-separate-compilation-linker-v2.md, 0164, 0217, 0099, 0239, 0256, tasks/0369, tasks/0786, tasks/0803, tasks/0804]
covers: [REQ-LNK-228, REQ-LNK-229, REQ-LNK-230, REQ-LNK-231, REQ-LNK-234, REQ-LNK-235, REQ-LNK-236, REQ-LNK-237, REQ-LNK-238, REQ-LNK-239, REQ-LNK-240, REQ-LNK-241, REQ-LNK-242, REQ-LNK-243, REQ-LNK-244, REQ-LNK-245, REQ-LNK-246, REQ-LNK-247, REQ-LNK-248, REQ-LNK-249, REQ-LNK-250, REQ-LNK-251, REQ-LNK-252, REQ-LNK-253, REQ-LNK-254, REQ-LNK-255, REQ-LNK-256, REQ-LNK-257, REQ-LNK-258, REQ-LNK-259, REQ-LNK-260, REQ-LNK-261, REQ-LNK-262, REQ-LNK-263, REQ-LNK-264, REQ-LNK-265, REQ-LNK-266, REQ-LNK-267, REQ-LNK-268, REQ-LNK-269, REQ-LNK-270, REQ-LNK-271, REQ-LNK-272, REQ-LNK-273, REQ-LNK-274, REQ-LNK-275, REQ-LNK-276, REQ-LNK-277, REQ-LNK-278, REQ-LNK-279, REQ-LNK-280, REQ-LNK-281, REQ-LNK-282, REQ-LNK-283, REQ-LNK-284, REQ-LNK-285, REQ-LNK-286, REQ-LNK-287, REQ-LNK-288, REQ-LNK-289, REQ-LNK-290, REQ-LNK-291, REQ-LNK-292, REQ-LNK-293, REQ-LNK-294, REQ-LNK-295, REQ-LNK-296, REQ-LNK-297, REQ-LNK-298, REQ-LNK-299, REQ-LNK-300, REQ-LNK-301, REQ-LNK-302, REQ-LNK-303, REQ-LNK-304, REQ-LNK-305, REQ-LNK-306, REQ-LNK-307, REQ-LNK-308, REQ-LNK-309, REQ-LNK-310, REQ-LNK-311, REQ-LNK-312, REQ-LNK-313, REQ-LNK-314, REQ-LNK-315, REQ-LNK-316, REQ-LNK-317, REQ-LNK-318, REQ-LNK-319, REQ-LNK-320, REQ-LNK-321, REQ-LNK-322, REQ-LNK-323, REQ-LNK-324, REQ-LNK-325, REQ-LNK-326, REQ-LNK-327, REQ-LNK-328, REQ-LNK-329, REQ-LNK-330, REQ-LNK-331, REQ-LNK-332, REQ-LNK-333, REQ-LNK-334, REQ-LNK-335, REQ-LNK-336, REQ-LNK-337, REQ-LNK-338, REQ-LNK-339, REQ-LNK-340, REQ-LNK-341, REQ-LNK-342, REQ-LNK-343, REQ-LNK-344, REQ-LNK-345, REQ-LNK-346, REQ-LNK-347, REQ-LNK-348, REQ-LNK-349, REQ-LNK-350, REQ-LNK-351, REQ-LNK-352, REQ-LNK-353, REQ-LNK-354, REQ-LNK-355, REQ-LNK-356, REQ-LNK-357, REQ-LNK-358, REQ-LNK-359, REQ-LNK-360, REQ-LNK-361, REQ-LNK-362, REQ-LNK-363, REQ-LNK-364, REQ-LNK-365, REQ-LNK-366, REQ-LNK-367, REQ-LNK-368, REQ-LNK-369, REQ-LNK-370, REQ-LNK-371, REQ-LNK-372, REQ-LNK-373, REQ-LNK-374, REQ-LNK-375, REQ-LNK-376, REQ-LNK-377, REQ-LNK-378, REQ-LNK-379, REQ-LNK-380, REQ-LNK-381, REQ-LNK-382, REQ-LNK-383, REQ-LNK-384, REQ-LNK-385, REQ-LNK-386, REQ-LNK-387, REQ-LNK-388, REQ-LNK-389, REQ-LNK-390, REQ-LNK-391, REQ-LNK-392, REQ-LNK-393, REQ-LNK-394, REQ-LNK-395, REQ-LNK-396, REQ-LNK-397, REQ-LNK-398, REQ-LNK-399, REQ-LNK-400, REQ-LNK-401, REQ-LNK-402, REQ-LNK-403, REQ-LNK-404, REQ-LNK-405, REQ-LNK-406, REQ-LNK-407, REQ-LNK-408, REQ-LNK-409, REQ-LNK-410, REQ-LNK-411, REQ-LNK-412, REQ-LNK-413, REQ-LNK-414, REQ-LNK-415, REQ-LNK-416, REQ-LNK-417, REQ-LNK-418, REQ-LNK-419, REQ-LNK-420, REQ-LNK-421, REQ-LNK-422, REQ-LNK-423, REQ-LNK-424, REQ-LNK-425, REQ-LNK-426, REQ-LNK-427, REQ-LNK-428, REQ-LNK-429, REQ-LNK-430, REQ-LNK-431, REQ-LNK-432, REQ-LNK-433, REQ-LNK-3785, REQ-LNK-3786, REQ-LNK-3787, REQ-LNK-3788, REQ-LNK-3789, REQ-LNK-3790, REQ-LNK-3791, REQ-LNK-3792, REQ-LNK-3793, REQ-LNK-3794, REQ-LNK-3795, REQ-LNK-3796, REQ-LNK-3797, REQ-LNK-3798, REQ-LNK-3799, REQ-LNK-3800, REQ-LNK-3801, REQ-LNK-3802, REQ-LNK-3803, REQ-LNK-3804, REQ-LNK-3805, REQ-LNK-3806, REQ-LNK-3807, REQ-LNK-3808, REQ-LNK-3809, REQ-LNK-3810, REQ-LNK-3811, REQ-LNK-3812, REQ-LNK-3813, REQ-LNK-3814, REQ-LNK-3815, REQ-LNK-3816, REQ-LNK-3817, REQ-LNK-3818, REQ-LNK-3819, REQ-LNK-3820, REQ-LNK-3821, REQ-LNK-3822, REQ-LNK-3823, REQ-LNK-3824, REQ-LNK-3825, REQ-LNK-3826, REQ-LNK-3827, REQ-LNK-3828, REQ-LNK-3829, REQ-LNK-3830, REQ-LNK-3831, REQ-LNK-3832, REQ-LNK-3833, REQ-LNK-3834, REQ-LNK-3835, REQ-LNK-3836, REQ-LNK-3837, REQ-LNK-3838, REQ-LNK-3839, REQ-LNK-3840, REQ-LNK-3841, REQ-LNK-3842, REQ-LNK-3843, REQ-LNK-3844, REQ-LNK-3845, REQ-LNK-3846, REQ-LNK-3847, REQ-LNK-3848, REQ-LNK-3849, REQ-LNK-3850, REQ-LNK-3851, REQ-LNK-3852, REQ-LNK-3853, REQ-LNK-3854, REQ-LNK-3855, REQ-LNK-3856, REQ-LNK-3857, REQ-LNK-3858, REQ-LNK-3859, REQ-LNK-3860, REQ-LNK-3861, REQ-LNK-3862, REQ-LNK-3863, REQ-LNK-3864, REQ-LNK-3865, REQ-LNK-3866, REQ-LNK-3867, REQ-LNK-3868, REQ-LNK-3869, REQ-LNK-3870, REQ-LNK-3871, REQ-LNK-3872, REQ-LNK-3873, REQ-LNK-3874, REQ-LNK-3875, REQ-LNK-3876, REQ-LNK-3877, REQ-LNK-3878, REQ-LNK-3879, REQ-LNK-3880, REQ-LNK-3881, REQ-LNK-3882, REQ-LNK-3883, REQ-LNK-3884, REQ-LNK-3984, REQ-LNK-3985, REQ-LNK-3986, REQ-LNK-3987, REQ-LNK-3988, REQ-LNK-3989, REQ-LNK-3990, REQ-LNK-3991, REQ-LNK-3992, REQ-LNK-3993]
started: 2026-11-08 04:54:29
agent: T067-impl
---
# T067 — E18.6 — Linker v2: separate compilation, multiple objects, archives

## Goal
Implement per-module separate compilation (`.obj` + `.axmi` per module), `LinkIR` multi-object and `.lib` archive linking, cross-object relocation patching, and structured symbol resolution diagnostics in `compiler/link` and `compiler/driver` per `spec/SPEC-27-separate-compilation-linker-v2.md`.

## Scope
- Emit one COFF `.obj` per module in multi-module projects and feed the ordered object + `.lib` archive list into the `LinkIR` linker (`0164`, `0217`, `0256`, `tasks/0786`, `tasks/0804`).
- Implement global symbol table merging across multiple objects and archives, cross-module relocation resolution (`ADDR64`, `REL32`, section-relative `.pdata`/`.xdata`), and deterministic section layout.
- Emit structured diagnostics for duplicate strong symbols, undefined references (with demangled Axiom item names and referencing module/span), and ABI/calling-convention mismatches across objects.

## Acceptance
- [ ] Multi-module projects build via separate per-module `.obj` files and `.lib` archives in `tests/link2`; rebuilds are byte-identical.
- [ ] Duplicate and undefined cross-object symbol tests in `tests/link2` verify deterministic diagnostic codes and demangled symbol names.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T067-report.md` with exact `## Files changed`.

## Out of scope
- Reachability section GC and `COMDAT` folding (`T775`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Paths re-pathed to canonical `compiler/<module>` layout by T076 (ADR-0005 §8, SPEC-20 §8).
- Roadmap epic E18.6 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T067/build` and `python tools/axtest.py --compiler build-snap-T067/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 03:01:00 refined by T218 (linked to SPEC-27, T750, T766, and T775)
- 2026-11-08 04:54:29 started (attempt 1) T067-impl
