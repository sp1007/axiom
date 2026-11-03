# T217 — Plan phase P17: Debugging & runtime introspection

## Tóm tắt
Hoàn tất lập kế hoạch giai đoạn **P17 (`P17-debugging-runtime-introspectio`)** theo `spec/ROADMAP.md` §3–§4. Đã mở rộng đầy đủ 7 epic của P17 (`E17.1`–`E17.7`) thành **28 task cụ thể** (`T068` được tinh chỉnh tại chỗ + 27 task mới `T700`–`T726`, mỗi epic 4 task: 1 spec task của `axiom-architect` cho `SPEC-92`..`SPEC-98`, 2 task cài đặt của `axiom-backend`/`axiom-semantics`/`axiom-stdlib`, và 1 task kiểm thử hợp chuẩn của `axiom-qa` với `reviewer: axiom-architect`), nối toàn bộ phụ thuộc với cổng P16 (`T316`) và cổng P17 (`T317`), đồng thời ánh xạ đầy đủ hai chiều toàn bộ yêu cầu P17 (`REQ-DBG-116`..`REQ-DBG-121` và `REQ-ERR-001`..`REQ-ERR-003`) trong `spec/requirements/CATALOG.md`.

## Summary

Expanded Phase **P17 (`P17-debugging-runtime-introspectio`)** from the 7 epics in `spec/ROADMAP.md` §3 (`E17.1`–`E17.7`) into **28 concrete tasks** (`T068` refined in place + 27 new tasks `T700`–`T726`, 4 tasks per epic, all depending on P16 gate `T316`):

1. **E17.1 — Debug IR + CodeView/PDB (Windows) (`T700`–`T703`)**:
   - `T700` (`axiom-architect`): `spec/SPEC-92-debug-ir-codeview-pdb.md` — target-independent `DebugIR` (`DebugModule`, strong IDs, `SourceOrigin` bidirectional provenance, lexical scopes distinct from ownership lifetimes, post-RA `MachineLocation` range lists, explicit `OptimizedOut` representation), CodeView C13 `.debug$S`/`.debug$T` COFF subsections, and deterministic MSF v7 / PDB 7.00 container format.
   - `T701` (`axiom-backend`): Target-independent `DebugIR` builder, location-range tracker & CodeView `.debug$S`/`.debug$T` COFF emitter (`compiler/debug/ir`, `compiler/obj/codeview`).
   - `T702` (`axiom-backend`): Deterministic MSF v7 page allocator, PDB 7.00 stream writer (PDB Info, TPI, DBI, IPI, GSI/PSI) & PE `IMAGE_DIRECTORY_ENTRY_DEBUG` `RSDS` linker (`compiler/link/pdb`, `compiler/link/pe_debug`).
   - `T703` (`axiom-qa`): Debug IR, CodeView C13 & deterministic PDB 7.00 conformance suite (`tests/conformance/p17/e17_1_codeview_pdb`).

2. **E17.2 — DWARF (ELF/Mach-O) (`T704`–`T707`)**:
   - `T704` (`axiom-architect`): `spec/SPEC-93-dwarf-elf-macho.md` — lowering `DebugIR` to DWARF v5 (`.debug_info`, `.debug_abbrev`, `.debug_str`, `.debug_line_str`, `.debug_line`, `.debug_loclists`, `.debug_rnglists`, `.debug_aranges`, `.debug_names`) across ELF, Mach-O (`.dSYM`), and WASM (`wasm32`).
   - `T705` (`axiom-backend`): DWARF v5 DIE tree, `.debug_info`/`.debug_abbrev`/`.debug_str` & `.debug_line` state-machine emitter (`compiler/obj/dwarf`).
   - `T706` (`axiom-backend`): DWARF v5 `.debug_loclists`/`.debug_rnglists`/`.debug_names`, ELF `.note.gnu.build-id`, Mach-O `__DWARF`/`.dSYM` bundle & WASM debug linker (`compiler/link/dwarf`).
   - `T707` (`axiom-qa`): DWARF v5 ELF, Mach-O `.dSYM` & WASM debug information conformance suite (`tests/conformance/p17/e17_2_dwarf`).

3. **E17.3 — Unwinding & backtraces on all targets (`T708`, `T068`, `T709`, `T710`)**:
   - `T708` (`axiom-architect`): `spec/SPEC-94-unwinding-backtraces.md` — target-independent `UnwindPlan` derived from machine `FramePlan` (`Prologue`/`Body`/`Epilogue`), Windows x64/ARM64 `.pdata`/`.xdata`, ELF `.eh_frame`/`.eh_frame_hdr` DWARF CFI, Mach-O `__TEXT,__unwind_info`, `std.backtrace`, and `AXCRASH` minidump reporting.
   - `T068` (`axiom-backend`): Windows unwind info (`.pdata`/`.xdata`) and panic backtrace basics (`compiler/target/x64/unwind`, `compiler/obj/pe_unwind`, `compiler/link/pe_pdata`).
   - `T709` (`axiom-backend`): ELF `.eh_frame`/`.eh_frame_hdr` DWARF CFI, Mach-O `__unwind_info`, `std.backtrace` & `AXCRASH` minidump runtime (`compiler/obj/eh_frame`, `compiler/link/eh_frame_hdr`, `std/backtrace`, `std/crash`).
   - `T710` (`axiom-qa`): Cross-target unwinding, `std.backtrace` & `AXCRASH` minidump conformance suite (`tests/conformance/p17/e17_3_unwinding_backtrace`).

4. **E17.4 — Debugger contract & symbolication (`T711`–`T714`)**:
   - `T711` (`axiom-architect`): `spec/SPEC-95-debugger-contract-symbolication.md` — native debugger contract (`WinDbg`/`cdb`, `gdb`, `lldb`), cross-format symbolication engine, inline/async logical frame reconstruction, and Natvis/GDB/LLDB semantic type visualizers.
   - `T712` (`axiom-backend`): Cross-format symbolication engine (PDB/DWARF/source-map), canonical Axiom demangler & inline/async frame resolver (`compiler/debug/symbolicate`, `std/debug/symbolicate`).
   - `T713` (`axiom-stdlib`): Natvis/GDB/LLDB semantic visualizers (`String`/`Vec`/`Option`/`Result`/`Future` and `@secret` `<redacted>` masking) & `axiomc symbolicate` CLI (`compiler/debug/visualizers`, `compiler/driver/symbolicate_cmd`, `std/debug/contract`).
   - `T714` (`axiom-qa`): Debugger contract, Natvis/GDB/LLDB visualizers & symbolication conformance suite (`tests/conformance/p17/e17_4_debugger_symbolication`).

5. **E17.5 — Profiler & performance introspection (`T715`–`T718`)**:
   - `T715` (`axiom-architect`): `spec/SPEC-96-profiler-performance-introspection.md` — `AXPROFILER` sampling profiler, `--profile=instrument` & `@profile`/`@no_profile` hooks, heap/arena allocation & async contention counters, and `.axprof` / flamegraph / Chrome Trace exports.
   - `T716` (`axiom-backend`): Compiler `--profile=instrument` pass, `@profile`/`@no_profile` hooks & `.axprof_desc` source-mapped counter tables (`compiler/instrument/profile`).
   - `T717` (`axiom-stdlib`): `std.profiler` sampling engine, allocation/async contention telemetry & flamegraph/`.axprof` exporters (`std/profiler`, `compiler/driver/profile_cmd`).
   - `T718` (`axiom-qa`): `AXPROFILER` sampling, instrumentation, allocation/async telemetry & flamegraph conformance suite (`tests/conformance/p17/e17_5_profiler`).

6. **E17.6 — Sanitizers & runtime verification (`T719`–`T722`)**:
   - `T719` (`axiom-architect`): `spec/SPEC-97-sanitizers-runtime-verification.md` — `--sanitize=address|memory|ub|thread|bounds|all` dynamic sanitizers and runtime verification contract.
   - `T720` (`axiom-semantics`): Compiler sanitizer instrumentation pass inserting address/bounds/provenance, uninitialized-memory, UB, and thread shadow hooks (`compiler/instrument/sanitize`).
   - `T721` (`axiom-stdlib`): Sanitizer runtime library (`std.rt.sanitize`): redzone quarantine, shadow state, `TSan` vector clocks/lock-order detector & symbolicated violation reports (`std/rt/sanitize`).
   - `T722` (`axiom-qa`): Address, memory, UB, bounds & thread sanitizer conformance suite (`tests/conformance/p17/e17_6_sanitizers`).

7. **E17.7 — Trace & replay (`T723`–`T726`)**:
   - `T723` (`axiom-architect`): `spec/SPEC-98-trace-replay.md` — `AXREPLAY` deterministic execution recording, `.axtrace` event logs, state checkpoints, and time-travel debugging (`reverse-step`, `reverse-continue`, `last-writer`).
   - `T724` (`axiom-backend`): Compiler `--trace` instrumentation pass & MIR interpreter time-travel record/replay oracle (`compiler/instrument/trace`, `compiler/interp/replay`).
   - `T725` (`axiom-stdlib`): `std.replay` (`.axtrace` recorder/replayer, state checkpoints & time-travel query engine) & `axiomc replay` CLI (`std/replay`, `compiler/driver/replay_cmd`).
   - `T726` (`axiom-qa`): `AXREPLAY` deterministic execution recording, replay & time-travel debugging conformance suite (`tests/conformance/p17/e17_7_trace_replay`).

## Files changed

- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md
- ./_workspaces/tasks/todo/T068-windows-unwind-info-pdata-xdata-and-panic-backtrac.md
- ./_workspaces/tasks/todo/T317-phase-p17-gate-debugging-runtime-introspection.md
- ./_workspaces/tasks/todo/T506-e13-2-raw-memory-volatile-mmio-layout-spec.md
- ./_workspaces/tasks/todo/T700-e17-1-debug-ir-codeview-pdb-msf-spec.md
- ./_workspaces/tasks/todo/T701-e17-1-debug-ir-builder-location-tracker-codeview-obj.md
- ./_workspaces/tasks/todo/T702-e17-1-msf-page-allocator-pdb-writer-pe-rsds-linker.md
- ./_workspaces/tasks/todo/T703-e17-1-debug-ir-codeview-pdb-conformance.md
- ./_workspaces/tasks/todo/T704-e17-2-dwarf-v5-elf-macho-dsym-wasm-spec.md
- ./_workspaces/tasks/todo/T705-e17-2-dwarf-v5-die-tree-debug-info-abbrev-line.md
- ./_workspaces/tasks/todo/T706-e17-2-dwarf-v5-loclists-rnglists-names-dsym-linker.md
- ./_workspaces/tasks/todo/T707-e17-2-dwarf-v5-elf-macho-wasm-conformance.md
- ./_workspaces/tasks/todo/T708-e17-3-cross-target-unwinding-backtrace-axcrash-spec.md
- ./_workspaces/tasks/todo/T709-e17-3-elf-eh-frame-macho-unwind-std-backtrace-crash.md
- ./_workspaces/tasks/todo/T710-e17-3-cross-target-unwinding-backtrace-conformance.md
- ./_workspaces/tasks/todo/T711-e17-4-debugger-contract-symbolication-visualizers-spec.md
- ./_workspaces/tasks/todo/T712-e17-4-symbolication-engine-demangler-inline-async-frames.md
- ./_workspaces/tasks/todo/T713-e17-4-natvis-gdb-lldb-visualizers-symbolicate-cli.md
- ./_workspaces/tasks/todo/T714-e17-4-debugger-contract-symbolication-conformance.md
- ./_workspaces/tasks/todo/T715-e17-5-profiler-sampling-instrumentation-telemetry-spec.md
- ./_workspaces/tasks/todo/T716-e17-5-profile-instrument-pass-attributes-counter-tables.md
- ./_workspaces/tasks/todo/T717-e17-5-std-profiler-sampling-alloc-async-flamegraph-cli.md
- ./_workspaces/tasks/todo/T718-e17-5-profiler-performance-introspection-conformance.md
- ./_workspaces/tasks/todo/T719-e17-6-sanitizers-address-memory-ub-thread-spec.md
- ./_workspaces/tasks/todo/T720-e17-6-sanitizer-instrumentation-pass-shadow-checks.md
- ./_workspaces/tasks/todo/T721-e17-6-std-rt-sanitize-quarantine-shadow-tsan-reports.md
- ./_workspaces/tasks/todo/T722-e17-6-sanitizers-runtime-verification-conformance.md
- ./_workspaces/tasks/todo/T723-e17-7-axreplay-deterministic-trace-replay-spec.md
- ./_workspaces/tasks/todo/T724-e17-7-trace-instrumentation-pass-interp-replay-oracle.md
- ./_workspaces/tasks/todo/T725-e17-7-std-replay-axtrace-checkpoints-time-travel-cli.md
- ./_workspaces/tasks/todo/T726-e17-7-trace-replay-time-travel-conformance.md

## Tests

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P17-debugging-runtime-introspectio --strict` → `9 rows` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `gaps: 0`, `COVERAGE OK` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T068`, `T317`, `T700`–`T726` → `OK` (`29 files`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → `OK (487 tasks)`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T217` → `0 REFUSED`

## Spec deviations

None.

## Follow-ups

None.

STATUS: COMPLETE round=0
