---
id: T775
title: E18.6 — Linker v2 reachability graph, COMDAT deduplication & unreferenced section GC
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T067]
priority: 724
status: todo
attempts: 0
paths: [compiler/link/gc, tests/run/link_section_gc, tests/selfhost]
spec: [spec/SPEC-27-separate-compilation-linker-v2.md, 0099, 0164, 0217, tasks/0369, tasks/0409, tasks/0410, tasks/0526, tasks/0786, tasks/0802, tasks/0804]
covers: [REQ-CORE-535, REQ-CORE-536, REQ-CORE-537, REQ-CORE-538, REQ-CORE-539, REQ-CORE-540, REQ-CORE-541, REQ-CORE-542, REQ-CORE-543, REQ-CORE-544, REQ-CORE-545, REQ-CORE-546, REQ-CORE-547, REQ-CORE-548, REQ-CORE-549, REQ-CORE-550, REQ-CORE-551, REQ-CORE-552, REQ-CORE-553, REQ-CORE-554, REQ-CORE-555, REQ-CORE-556, REQ-CORE-557, REQ-CORE-558, REQ-CORE-559, REQ-CORE-560, REQ-CORE-561, REQ-CORE-562, REQ-CORE-563, REQ-CORE-564, REQ-CORE-565, REQ-CORE-566, REQ-CORE-567, REQ-CORE-568, REQ-CORE-569, REQ-CORE-570, REQ-CORE-571, REQ-CORE-572, REQ-CORE-573, REQ-CORE-574, REQ-CORE-575, REQ-CORE-576, REQ-CORE-577, REQ-CORE-578, REQ-CORE-579, REQ-CORE-580, REQ-CORE-581, REQ-CORE-582, REQ-CORE-583, REQ-CORE-584, REQ-CORE-585, REQ-CORE-586, REQ-CORE-587, REQ-CORE-588, REQ-CORE-589, REQ-CORE-590, REQ-CORE-591, REQ-CORE-592, REQ-CORE-593, REQ-CORE-594, REQ-CORE-595, REQ-CORE-596, REQ-CORE-597, REQ-CORE-598, REQ-CORE-599, REQ-CORE-600, REQ-CORE-601, REQ-LNK-227, REQ-CORE-2541, REQ-CORE-2542, REQ-CORE-2543, REQ-CORE-2544, REQ-CORE-2545, REQ-CORE-2546, REQ-CORE-2547, REQ-CORE-2548, REQ-CORE-2549, REQ-CORE-2550, REQ-CORE-2551, REQ-CORE-2552, REQ-CORE-2553, REQ-CORE-2554, REQ-CORE-2555, REQ-CORE-2556, REQ-CORE-2557, REQ-CORE-2558, REQ-CORE-2559, REQ-CORE-2560, REQ-CORE-2561, REQ-CORE-2562, REQ-CORE-2563, REQ-CORE-2564, REQ-CORE-2565, REQ-CORE-2566, REQ-CORE-2567, REQ-CORE-2568, REQ-CORE-2569, REQ-CORE-2570, REQ-CORE-2571, REQ-CORE-2572, REQ-CORE-2573, REQ-CORE-2574, REQ-CORE-2575, REQ-CORE-2576, REQ-CORE-2577, REQ-CORE-2578, REQ-CORE-2579, REQ-CORE-2580, REQ-CORE-2581, REQ-CORE-2582, REQ-CORE-2583, REQ-CORE-2584, REQ-CORE-2585, REQ-CORE-2586, REQ-CORE-2587, REQ-CORE-2588, REQ-CORE-2589, REQ-CORE-2590, REQ-CORE-2591, REQ-CORE-2592, REQ-CORE-2593, REQ-CORE-2594, REQ-CORE-2595, REQ-CORE-2596, REQ-CORE-2597, REQ-CORE-2598, REQ-CORE-2599, REQ-CORE-2600, REQ-CORE-2601, REQ-CORE-2602, REQ-CORE-2603, REQ-CORE-2604, REQ-CORE-2605, REQ-CORE-2606, REQ-CORE-2607, REQ-CORE-2608, REQ-CORE-2609, REQ-CORE-2610, REQ-CORE-2611, REQ-CORE-2612, REQ-CORE-2613, REQ-CORE-2614, REQ-CORE-2615, REQ-CORE-2616, REQ-CORE-2617, REQ-CORE-2618, REQ-CORE-2619, REQ-CORE-2620, REQ-CORE-2621, REQ-CORE-2622, REQ-CORE-2623, REQ-CORE-2624, REQ-CORE-2625, REQ-CORE-2626, REQ-CORE-2627, REQ-CORE-2628, REQ-CORE-2629, REQ-CORE-2630, REQ-CORE-2631, REQ-CORE-2632, REQ-CORE-2633, REQ-CORE-2634, REQ-CORE-2635, REQ-CORE-2636, REQ-CORE-2637, REQ-CORE-2638, REQ-CORE-2639, REQ-CORE-2640, REQ-CORE-2641, REQ-CORE-2642, REQ-CORE-2643, REQ-LNK-3885, REQ-LNK-3886, REQ-LNK-3887, REQ-LNK-3888, REQ-LNK-3889, REQ-LNK-3890, REQ-LNK-3891, REQ-LNK-3892, REQ-LNK-3893, REQ-LNK-3894, REQ-LNK-3895, REQ-LNK-3896, REQ-LNK-3897, REQ-LNK-3898, REQ-LNK-3899, REQ-LNK-3900, REQ-LNK-3901, REQ-LNK-3902, REQ-LNK-3903, REQ-LNK-3904, REQ-LNK-3905, REQ-LNK-3906, REQ-LNK-3907, REQ-LNK-3908, REQ-LNK-3909, REQ-LNK-3910, REQ-LNK-3911, REQ-LNK-3912, REQ-LNK-3913, REQ-LNK-3914, REQ-LNK-3915, REQ-LNK-3916, REQ-LNK-3917, REQ-LNK-3918, REQ-LNK-3919, REQ-LNK-3920, REQ-LNK-3921, REQ-LNK-3922, REQ-LNK-3923, REQ-LNK-3924, REQ-LNK-3925, REQ-LNK-3926, REQ-LNK-3927, REQ-LNK-3928, REQ-LNK-3929, REQ-LNK-3930, REQ-LNK-3931, REQ-LNK-3932, REQ-LNK-3933, REQ-LNK-3934, REQ-LNK-3935, REQ-LNK-3936, REQ-LNK-3937, REQ-LNK-3938, REQ-LNK-3939, REQ-LNK-3940, REQ-LNK-3941, REQ-LNK-3942, REQ-LNK-3943, REQ-LNK-3944]
---
# T775 — E18.6 — Linker v2 reachability graph, COMDAT deduplication & unreferenced section GC

## Goal
Implement per-item section subdivision, `COMDAT` monomorphized generic deduplication, and root-set reachability section garbage collection (`--gc-sections`, enabled by default for release/standard links) in `compiler/link/gc` per `spec/SPEC-27-separate-compilation-linker-v2.md`.

## Scope
- Emit each function and static datum into its own section / `COMDAT` group (`IMAGE_SCN_LNK_COMDAT`) so duplicate generic instantiations across separate `.obj` files are deterministically folded (`0164`, `tasks/0526`, `tasks/0786`).
- Construct the section relocation graph in `compiler/link/gc` rooted at `@entry` / `main` / `DllMain`, `@export` items, `@used` / `@at` pinned declarations, and module initialisers.
- Sweep unreferenced code/read-only/data sections along with their associated `.pdata`/`.xdata` unwind entries while preserving all reachable and pinned sections (`tasks/0409`, `tasks/0410`, `tasks/0804`).
- Add `inspect --emit=link-map` and `--emit=gc-sections` to report retained vs discarded sections and folded `COMDAT` groups deterministically.

## Acceptance
- [ ] Tests in `tests/run/link_section_gc` verify that importing a single function from `std` or a multi-module library strips unreferenced functions/statics from the final `.exe`/`.dll`, folds duplicate generic instantiations across separate `.obj` files, and preserves `@export`/`@used` roots.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T775-report.md` with exact `## Files changed`.

## Out of scope
- Cross-target ELF/Mach-O linkers (`P16`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T775/build` and `python tools/axtest.py --compiler build-snap-T775/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 03:01:00 created by T218 (P18 phase planning)
