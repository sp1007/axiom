# Audit A3 — Task executability

## Summary
Read T001–T087, T003a, T061a, T073a in dependency order, skimmed T088–T111, T2xx, T3xx, T750/T751, plus `taskctl.py` (`ready`, `overlaps`, `commit`), `axiom-testing`, `axiom-c-stage0`, `.gitignore`.
The main clusters are:
- the test runner (T005) is too narrow for what later tasks need;
- hot shared files are not covered by `paths`: driver, `codes.def`, CMake, `axtest.py`;
- several tasks use features that are scheduled later: Option, impl/Drop, generics, `check`;
- the native catch-up split (T028/T033/T037 and the T030–T041 tests) has no defined way to flip native on;
- the port tasks T077–T085 are far too big for one sitting.
Counts: BLOCKER 0, MAJOR 15, MINOR 12 (27 findings; CONFIRMED 21, PLAUSIBLE 6).

## Findings

### A3-01 [MAJOR] [CONFIRMED] T005 runner has no kinds/directives for unit, encode, obj, link, project tests, args/env/stdin, xfail
- Where: T005 §Scope ("Kinds: run, ui, golden (tokens/ast/hir/thir/mir/lir), diff"; directives test/exit/stdout/modes/target/flags); needed by T007 (unit, "add a `unit` kind if needed"), T024 (`tests/encode`), T026/T027 (`tests/obj`, `tests/link`, cross-link SKIP), T014 (`--emit=resolved` golden), T025 (`--emit=mc` golden), T060 (`tests/modules` multi-file projects), T074 (program run "with argument `xin chào`", env var, temp files), T052/T013/T062 (failures parked as follow-ups).
- Problem: `axiom-testing` lists encode/obj/link/unit as test kinds, but T005 builds only run/ui/golden/diff. The golden kinds stop at lir, so `resolved` and `mc` are missing. There is no `args:`, `env:`, `stdin:` or `cwd:` directive, no directory/manifest-style test for multi-file projects, and no `xfail: Txxx` or SKIP-with-reason mechanism.
- Consequence if not fixed: each later task edits `tools/axtest.py` (not in its `paths`) or restricts its own acceptance. T007, T024, T026 and T027 will edit the runner in parallel with other tasks. T074's Unicode argument/env criteria cannot be expressed. T052's "suite passes or every failure has a follow-up" cannot hold together with every later task's "full suite passes".
- Proposed fix: extend T005 §Scope to:
  - (a) a generic `exec` kind (`// cmd:` or a `test.toml` manifest: command, expected exit/stdout, SKIP condition);
  - (b) golden kinds derived from the sibling extension for any `inspect --emit=<ext>`;
  - (c) directives `args`, `env`, `stdin`, `cwd`, `xfail: <task-id>` (counted as XFAIL, not FAIL) and `skip-unless: tool gcc`;
  - (d) project tests: a directory with `main.ax` plus `test.toml`.
  T007, T024, T026 and T027 then use kind (a) and never touch the runner. Add `tools/axtest.py` only to T005's `paths`. Capability-probe failure (`--features` unknown before T016) must mean "interp/native unavailable", not an error.

### A3-02 [MAJOR] [CONFIRMED] Hot shared files are edited by many tasks but listed in no `paths`: driver, `codes.def`, CMakeLists, `tests/README.md`, `tools/ci.sh`
- Where:
  - driver: T010 (`inspect --emit=tokens`), T011 (`--emit=ast`), T014 (`resolved`), T015 (`hir`), T017 (`thir`), T018 (`mir`), T020 ("driver runs the verifier"), T021 (`run --interp`), T023 (`lir`), T025 (`mc`), T026 (`--emit=obj`), T043 (`-O1` pass), T050 ("driver refuses unverified MIR"); only T004/T016/T028/T060 list `src/driver`;
  - `diag/codes.def`: T009 owns it, but T010–T072 all register codes and only T009's paths name `src/diag`;
  - CMake: T007 "unit test binary (CMake target)", T024 (`tests/encode`), T026/T027 (C test drivers in `tests/obj`, `tests/link`) — T004 owns `CMakeLists.txt`, which globs only `src/**/*.c`;
  - `tests/README.md` (T005): edited by T013 and others; `tools/ci.sh` (T004): edited by T006, not listed.
- Problem: `paths` is the only concurrency lock. Real parallel pairs exist: T037‖T038 (both add codes), T040‖T041, T042‖T043, T060‖T053–T059, T016‖T017 (see A3-06), and T005‖T006 (both touch `tools/tests`). `taskctl commit` stages the whole shared file, so the first committer also commits the other task's half-finished hunks.
- Consequence if not fixed: clobbered edits, broken builds, commits that mix tasks.
- Proposed fix:
  - T004 creates the driver as a command table with one file per command, `src/driver/cmd_<name>.c` (globbed), and each stage task lists its own `cmd_*.c`.
  - T009/T002 split the code registry into `src/diag/codes/<AREA>.def` (LEX, PARSE, NAME, TYPE, TRAIT, MOVE, INIT, CAP, DROP, VERIFY, CONST, LINK, IO, ICE), pre-created and included by `codes.def`; each task lists its area file.
  - T004's CMake globs `tests/unit/**/*.c` and `tests/**/cdriver_*.c` into test executables, so nobody edits CMake.
  - T006 gets `tools/ci.sh` and `tools/tests/archcheck` in its `paths`, or T004 pre-wires an "archcheck if present" hook.
  - Each task lists `tests/README.md` only if it edits it.

### A3-03 [MAJOR] [CONFIRMED] Parallel tasks share one working tree and one globbed build, so any task's half-written C breaks the others' builds and "full suite" gates
- Where: T004 §Scope (CMake globs `src/**/*.c`, warnings-as-errors), `axiom-tasks` ("safe to run in parallel without git worktrees"), every task's boilerplate "Full test suite passes (not only new tests); build warning-free".
- Problem: a private `build-<ID>` directory does not isolate sources. While task A builds, task B's in-progress file in `src/<other>` may not compile under `-Werror`. B's half-finished tests (golden files written before the code exists) fail A's "full suite" run. Stdlib tasks (T069–T075, Axiom code) compile with an axiom0 that semantics/backend tasks are rewriting at the same moment (T072‖T070/T071, T069‖T059/T061).
- Consequence if not fixed: spurious QA FAILs, wasted fix rounds, and the 2-round escalation to Opus spent on other tasks' breakage.
- Proposed fix: run each parallel task in its own git worktree (the Agent tool supports `isolation: "worktree"`), merged or cherry-picked by `taskctl commit`. With worktrees the `paths` lock only needs to predict merge conflicts. Otherwise restrict parallelism to (one C-compiler task + spec/QA/requirements-extraction tasks) and require QA to run only the task's own test dirs plus a full suite at the gates. NEEDS ARCHITECT/OWNER DECISION on the process.

### A3-04 [MAJOR] [CONFIRMED] T028 acceptance requires native branches/loops/recursion/overflow/div-zero before T033/T037 build them
- Where: T021 §Acceptance ("exit 42, arithmetic, branches, loops, recursion (fib), overflow trap, division by zero" in `tests/run/basic`) vs T025 §Scope (baseline isel, `return 42`, no cmp/jcc/div/overflow) vs T028 §Acceptance ("All tests/run/basic pass in native mode", plus the gcc cross-link oracle on every program) vs T033 §Scope (branch/loop lowering, >4 args, recursion) and T037 §Scope (overflow `jo`, div-by-zero checks).
- Problem: the native path (T025/T028) contains nothing that lowers a branch or an overflow check; T033/T037 add it later. T029 (VS1) then requires "every run test in both modes".
- Consequence if not fixed: T028 fails QA, or its agent silently pulls T033/T037 work into it, or restricts `modes` without a recorded reason.
- Proposed fix: either (a) T021 marks the branches/loops/fib/overflow/div tests `// modes: interp  // native-after: T033` (see A3-05) and T028 accepts only tests without them, or (b) move "cmp/jcc, loops, calls, recursion" into T025/T028 scope and keep only overflow/div checks in T037. Choose (a). Reword the T028 cross-link criterion to "every test that has native mode enabled".

### A3-05 [MAJOR] [CONFIRMED] Interp-only tests (T030–T032, T034–T036, T038–T041) have no defined way to become native later; the default `modes` is both
- Where: T030–T032 ("run + ui tests in interp mode (native catch-up in T033)"), T034/T036/T038 ("in interp"), T033/T037/T040/T042 (paths only `tests/run/native_*`), `axiom-testing` (default for run = both; restrict "only with a reason comment").
- Problem: after T028 native is available, so a T030 test without a `modes:` restriction runs natively in the full suite and fails. With a restriction, the catch-up task must delete it from test dirs it does not own (`tests/run/vars`, `cfg`, `fn`, …). T033 lists only `tests/run/native_abi`.
- Consequence if not fixed: each of T030–T032 and T034–T041 fails the full-suite criterion, or the native tasks edit files outside their `paths` (clobbering risk, see A3-02).
- Proposed fix: define in T005 the directive `// modes: interp  // native-after: T033`. The runner treats it as SKIP while T033 is not done (read the board, or a `tools/native_gate.txt` the catch-up task edits). Each catch-up task (T033, T037, T040, T042, T051, T059) states "remove/flip `native-after: <self>` in tests/run/<dirs>" and lists those dirs in `paths`.

### A3-06 [MAJOR] [CONFIRMED] T017 (ui tests, `inspect --emit=thir`) and T013 (fuzz via `axiom0 check --json`) do not depend on T016, which creates `check`
- Where: T013 deps [T012, T005], §Scope "runs `axiom0 check --json`"; T017 deps [T015, T003, T003a], §Acceptance `return true` ui test; T018–T021 wire into the driver.
- Problem: T016 (priority 26) is not an ancestor of T013/T017, so T017 (30) can start in parallel with T016. The `ui` kind runs `axiom0 check`, which only T016 defines. T013 fuzzes the `check` command, which does not exist at T013 time (only `inspect --emit=tokens/ast`, T010/T011).
- Consequence if not fixed: T013's acceptance ("20-minute campaign") cannot even start; T017/T018 race T016 on `src/driver`.
- Proposed fix: T013 deps += T016, or rewrite it to use `inspect --emit=ast --json`. T017 deps += T016 (T016 is then an ancestor of the whole semantic chain).

### A3-07 [MAJOR] [CONFIRMED] Features used by acceptance criteria before the task that delivers them
- Where and fix:
  - **T034** acceptance uses `char.from_u32(n) -> Option<char>`. Option lands in T039 and methods/assoc-fns on primitives in T053. Fix: move the `from_u32` criterion to T039, or make T034 provide a bootstrap intrinsic (`char_from_u32(n, &mut c) -> bool`) and let T069 add the Option wrapper.
  - **T038** acceptance: `if let`/`while let` "over Option". Option is T039. Fix: use a user-defined `enum Maybe` in T038, or add the Option lang item to T038 and leave only the `?` operator to T039.
  - **T049** needs `impl Drop for S { fn drop(self: mut_view<S>) }` and generic `drop(x)`. Impl blocks and traits are T053/T055, generics T054. Fix: T045 (SPEC-12) must define the bootstrap form of drop (e.g. `@lang(drop) fn`, registered per type) and T049 implements exactly that; T053/T055 then re-express it as the Drop trait.
  - **T048** scope "method receivers". Methods are T053. Fix: drop from T048 and add to T053 §Scope.
  - **T046** "copy classification (builtin + `@derive(Copy)`)". `@derive` lands in T056. Fix: T046 owns recognition of `@derive(Copy)`/`@copy` and T056 only extends it.
  - **T061a** intrinsics `size_of<T>()`, `ptr_copy<T>` are generic, but generics land in T054. Fix: state in T061a that they are compiler builtins with explicit type arguments, or make T061a depend on T054 (recommended — T065/T070 come after anyway, and this also removes its clash with T059/T053 on `lir`/`types`).
  - **T041** acceptance needs `Str` length (`len(s)`) before methods (T053); state that `len` is an intrinsic.
- Consequence if not fixed: agents invent ad-hoc forms (a silent spec pick, QA finds a deviation) or fail acceptance.

### A3-08 [MAJOR] [CONFIRMED] Interpreter cannot call extern functions, but T065/T069–T075 require std tests in interp + native
- Where: T065 paths [abi, link, types/ffi] (no `src/interp`), §Acceptance ("run tests calling GetTickCount/WriteFile"); T061a interp memory model = (alloc id, offset), no real addresses; T069 "tests/std/core run tests (interp + native)", T070 "Windows heap backend via FFI … leak check via allocator counters", T071/T074 tests.
- Problem: no task gives the oracle an FFI bridge (LoadLibrary/GetProcAddress + a call thunk, marshalling (alloc id, offset) ↔ real pointers) or replaces heap/IO with interp intrinsics. Every std test that allocates, prints or opens a file would be native-only, which breaks the three-level oracle principle for all of std (P9).
- Consequence if not fixed: T070 fails in interp mode or its tests get `modes: native` and the differential guard is lost exactly where the compiler-port code will live.
- Proposed fix: NEEDS ARCHITECT DECISION (record in an ADR and in T061a/T065). Preferred: T065 adds `src/interp/ffi` (host-call bridge for ≤ 8 integer/pointer args; pointer marshalling only for buffers that live in interp allocations) and adds `src/interp` and `src/mir` to its paths. Alternative: `alloc`/`free`/`write`/file ops are `@intrinsic`s implemented in both interp and native, and `@link` FFI is native-only. Either way T070 must state which.

### A3-09 [MAJOR] [CONFIRMED] `paths` of T060, T061a, T065 omit directories the scope obviously edits
- Where: T060 paths [resolve, source, driver, tests/modules, tests/ui/modules]. Modules affect HIR (T015), typeck item lookup and visibility (`src/types`), and symbol mangling (T054 `traits/mono`). T061a paths [types/ptr, own/unsafe, interp/mem, …] but needs MIR place projections (`src/mir`), LIR/isel ("pointer ops map onto existing LIR"), and `src/types` root (TypeKind Ptr). T065 needs isel/IAT for indirect extern calls (`src/lir`, `src/target/x64`).
- Problem: T060 runs in parallel with T053–T059 (disjoint listed paths) and edits `src/hir`/`src/types` unlisted; T061a/T065 edit `lir`/`target` while T059 (paths lir/target/obj) may be running.
- Consequence if not fixed: clobbering or broken builds in P7/P8.
- Proposed fix: T060 += `src/hir`, `src/types` (visibility), mangling hook; or add T060 → T054 ordering. T061a += `src/mir`, `src/lir`, `src/target/x64`. T065 += `src/lir`, `src/target/x64`, `src/interp`. Or make T060/T061a/T065 depend on T059 so they stop overlapping it.

### A3-10 [MAJOR] [CONFIRMED] T073a uses `Interner` hashing from T073 but depends only on T070
- Where: T073a §Scope ("`Interner<T>` … deterministic hashing from T073"), deps [T070], paths [std/core/arena, std/collections/idtable, tests/std/arena]; T073 paths include `std/collections`.
- Problem: T073a can start before T073 (both ready after T070/T071/T072; `std/collections/idtable` overlaps `std/collections`, so the lock serialises them, but in either order). If T073a goes first, `Hash`/`HashMap` do not exist.
- Consequence if not fixed: T073a agent re-implements hashing privately or blocks.
- Proposed fix: T073a deps [T070, T073]. Priority 104 → 105 (before T074 at 105 is fine).

### A3-11 [MAJOR] [CONFIRMED] T077–T085 port tasks are template clones, each far larger than one sitting, with unspecified differential outputs and Sonnet for the deepest modules
- Where: T077–T085 (identical Scope/Acceptance text; e.g. T081 typeck + trait solver; T082 ownership + MIR builder + drop + verifier; T084 LIR + x64 backend + encoder; T085 COFF + PE + driver), owner `axiom-stdlib`, model sonnet; `axiom-tasks` rule "≤ 1–2k lines".
- Problem: each task ports multiple C modules that took several tasks to write (T017, T046–T050, T053–T057 are separate Opus tasks). "Differential equality over the corpus (documented counts)" does not say what is compared for T077 (kernel/source/diag have no `inspect` output) or how the Axiom module is driven (harness entry point). T076 is the only place that can fix this, but its acceptance only says "gap tasks filed".
- Consequence if not fixed: T081–T085 cannot finish in one sitting or two fix rounds; the agent leaves "half-done work unrecorded" or blocks. This is the critical path to T087.
- Proposed fix: T076 §Acceptance must say: (a) every port task ≤ ~1.5k lines of Axiom, split per C module (lexer, parser+AST, resolver, HIR, types, traits, own/init/cap, drop, mir build, verify, interp, opt, lir, abi, isel/frame, encoder, coff, pe, driver); (b) each split task names the exact differential artefact (`inspect --emit=…` dump, `--json` diagnostics, object bytes) and the harness entry; (c) models: Opus for typeck/traits/ownership/verifier/MIR-builder ports (T081, T082, T083 optimizer+interp), Sonnet elsewhere; (d) T076 re-paths T058/T063–T068/T750/T751 to the chosen `compiler/<module>` names (they currently use `compiler/mir`, `compiler/opt`, `compiler/link`, `compiler/target/x64/…`, which do not match T077–T085's `compiler/lexer`, `compiler/own_mir_verify`, `compiler/obj_link_driver`, …).

### A3-12 [MAJOR] [CONFIRMED] T111 consolidation runs after code tasks have started and may rewrite the plan under running/done tasks
- Where: T110 (priority 8) deps T092–T109; T111 (9) deps T110; T004–T087 do not depend on T111. T111 §Scope "Extend scope of existing todo tasks … never rewrite tasks already in doing/ or done/"; §Acceptance "`reqcov.py --strict` exits 0" and "every task declares `covers:`".
- Problem: the 18 extraction tasks (priorities 16–33) interleave with T010–T017, so T110/T111 become ready around P2–P3. By then T001–T016 are done and cannot be edited, yet `covers:` must be added to every task and v1-core gaps must become new P0–P10 tasks. New tasks for already-finished phases cannot be ordered correctly.
- Consequence if not fixed: `--strict` either cannot reach zero GAPs (done tasks cannot gain `covers:`) or T111 edits done tasks, or SPEC-00 ladder changes after code exists.
- Proposed fix: add T111 to deps of T017 (first semantic task); T007–T016 are fully specified by T001–T003a. Or add T111 to T007's deps if you want zero rework. `reqcov` should treat done tasks' missing `covers:` as a warning only. NEEDS OWNER DECISION on the delay.

### A3-13 [MAJOR] [PLAUSIBLE] `static` items and read-only tables have no task (typecheck, MIR, native emission)
- Where: T011 parses `static`; no task in T017–T061 types or lowers `static`/`static mut`; T061 "const items … (array sizes, tables)" evaluated in the interpreter only, deps T059, paths exclude `lir`/`target`/`obj`; T059 (native catch-up) precedes T061.
- Problem: a self-hosted compiler wants const tables (keyword table, opcode/encoding tables, diagnostic code names). Nothing emits constant aggregates or statics natively, and no native catch-up follows T061.
- Consequence if not fixed: the port hits this at T077/T078 (first table), creating an emergency gap task; or const tables exist in interp only.
- Proposed fix: T003a must state whether `static` (immutable) and const aggregate tables are in the self-host subset (recommended: yes, immutable only). Add `src/lir`, `src/target/x64`, `src/obj` + "native `.rdata` emission of const aggregates" to T061, or add a T061b native catch-up. `static mut` stays post-T087.

### A3-14 [MAJOR] [PLAUSIBLE] Several compiler tasks are too big for one sitting
- T038 (enums + match + Maranget exhaustiveness + if-let/while-let/let-else + destructuring + enum layout) → split: T038 enums+match lowering/layout, T038b exhaustiveness + unreachable arms, T038c refutable/irrefutable pattern forms.
- T048 (view/mut_view, regions, conflicts, escapes, receivers, plus slices: unsized `[T]`, array→slice coercion, range sub-views, `split_at_mut`) → split T048 (capabilities/regions/conflicts/escapes) and T048b (slices; needs a typed `Range`, or restrict to `s[a..b]` as builtin syntax before T072).
- T054 (generic typeck/inference + instance collection + mangling + retiring the T039 shortcut) → T054 generics typeck/inference, T054b monomorphization + mangling + Option/Result generic.
- T025 (Win64 ABI lowering + machine IR + isel + frame lowering + `--emit=mc`) → T025a ABI + machine IR, T025b isel + frame.
- T061a (pointer types + unsafe checker + intrinsics + interp allocation/liveness/alignment model + native lowering) → T061a types/unsafe/native, T061b oracle memory model and intrinsics.
- T071 (Str/String/UTF-8, StringBuilder, integer format/parse, ByteBuf, char primitives, UTF-16) → T071 text core, T071b ByteBuf + int format/parse, T071c UTF-16.
- T074 (io/env/args/exit, binary files, path, directory listing, clock, all W APIs) → T074 io/env/process, T074b fs/path/dir/clock.
- Consequence if not fixed: half-done tasks or shrunk scope discovered at QA; the architect splits late (board rule), breaking dependency order at P6–P9.

### A3-15 [MAJOR] [CONFIRMED] Gate/test campaign acceptance that cannot be satisfied or is unverifiable by command
- T052 "Suite passes or every failure has a filed follow-up task" and T013/T062 "campaign clean or findings filed" contradict "full suite passes" unless a failing case can be marked expected-fail (see A3-01 `xfail`). Fix: accepted failures must carry `xfail: <task-id>`; the gate is PASS iff the only failures are XFAIL with an existing task.
- T013 "20-minute campaign", T062 "30-minute progfuzz": state the command and pass criterion (`python tools/fuzz.py --seed 1 --iterations N` with N fixed and 0 findings), not wall time.
- T044 "perf baseline recorded" / T075 "perf recorded": add a file and a format (`_workspaces/artifacts/perf.csv` is git-ignored, so nothing is committed — put the baseline under `tests/perf/baseline.csv`) and "benchmark set" = named files.
- Also T015 "Golden tests covering every AST node kind", T023 "Golden LIR tests for the subset programs", T031/T032/T053–T057 "run + ui tests" should name at least a minimum test list or a generated node-kind coverage check.

### A3-16 [MINOR] [CONFIRMED] T042/T074 console glyph criteria are not checkable in a non-interactive session
- Where: T042 "correct glyphs when stdout is a real Windows console … no mojibake"; T074 "std.io print/println correct on console, pipe and file".
- Problem: the agent/QA has no console; only pipe/file bytes can be asserted.
- Proposed fix: make it checkable, e.g. a test that calls `GetConsoleMode` on the stdout handle and asserts which path (WriteConsoleW vs WriteFile with CP_UTF8) is taken, run under ConPTY via Python (`winpty`/`pywinpty` not available) — or mark it a documented manual check outside acceptance and keep the byte-exact pipe/file tests as the gate.

### A3-17 [MINOR] [CONFIRMED] T043 lacks deps on T041/T042 although acceptance runs "all run tests" at -O1
- Where: T043 deps [T040]; T041 (string constants, MIR operand kinds) and T042 (native strings) run in parallel.
- Problem: the optimizer may start without the string-constant operand kind, hit an ICE default branch, or see str tests that do not yet pass natively.
- Fix: T043 deps [T042] (T044 already depends on both).

### A3-18 [MINOR] [CONFIRMED] T023 does not depend on the VS0 gate T022
- Where: T022 deps [T021, T016]; T023 deps [T021, T003a]; ROADMAP: P4 depends on the P3 gate.
- Problem: T022 (priority 35) and T023 (40) run in parallel; gate findings ("gaps filed as follow-ups") arrive after backend work began.
- Fix: T023 deps += T022 (T024/T026 may stay independent).

### A3-19 [MINOR] [CONFIRMED] Compiler must find `std/`, but no task defines the lookup
- Where: T039 (`std/core/prelude`), T060 ("prelude as a real std module", package root per spec 0168), T069–T074 (`std/…`), runner uses `--compiler build-<ID>/axiom0.exe` (std cannot be located relative to the executable).
- Fix: T060 defines the std search path order (`--std <dir>`, `AXIOM_STD`, repo-relative default); `axtest.py` passes it; T069 tests cite it. T039's "prelude source or built-in lang items" should pick one (recommended: built-in now, module in T060).

### A3-20 [MINOR] [CONFIRMED] Post-self-host task paths do not match the T077–T085 layout; cross-task `paths` for phases P11+ are speculative
- Where: T058 `compiler/traits/dyn, compiler/mir, compiler/interp`; T063 `compiler/target/x64/regalloc`; T064 `compiler/opt`; T066 `compiler/abi/sysv, compiler/obj/elf, compiler/link/elf`; T067 `compiler/link, compiler/driver`; T068 `compiler/link/pe`; T750/T751 `compiler/link/archive, compiler/link/pe_dll, compiler/obj/archive, compiler/driver/kind`.
- Problem: T077–T085 use merged directories (`kernel_source_diag`, `resolve_hir`, `typeck_traits`, `own_mir_verify`, `interp_opt`, `backend`, `obj_link_driver`). The locks do not overlap with the ported code, so they prevent nothing.
- Fix: part of A3-11(d).

### A3-21 [MINOR] [CONFIRMED] Owner/model/gate mismatches
- T081–T083 (Axiom ports of typeck, trait solver, ownership, verifier, interpreter) are owned by `axiom-stdlib`/Sonnet; the original C versions were Opus (`axiom-semantics`). Use `model: opus` (or owner `axiom-semantics`) for them.
- Phase gates T022, T029, T044, T052, T062, T075, T086, T087 and T311–T323 have `model: opus` but `gate_model: sonnet` with reviewer `axiom-architect`, while CLAUDE.md says phase-final gates are Opus. Set `gate_model: opus` for them.
- T060 (module system, visibility, manifest: "decide name/format with architect if unclear") is a Sonnet task with an open design question — set `model: opus` or settle the manifest in T003a/ADR before T060 starts.
- T073a (arena lifetime/ownership design) is Sonnet; acceptable only if T045 covers arena-escape rules.

### A3-22 [MINOR] [CONFIRMED] T004 (priority 5) and T002/T003/T003a are "critical, runs alone"; nothing can overlap with the architect's spec tasks
- Where: `taskctl.ready` (critical < 10 returns alone; nothing new starts while one is ready); T004–T008 have no spec dependency (T009 needs T002, T010 needs T001).
- Consequence: T004–T008 (repository skeleton, runner, kernel, source DB) wait for ~4 sequential Opus spec tasks although they could run in parallel.
- Fix: set T002/T003/T003a/T004 to priority ≥ 10 (deps already enforce order: T009→T002, T010→T001, T017→T003/T003a, T024/T026→T003a) and keep only T001 critical, or drop the critical flag entirely for P0.

### A3-23 [MINOR] [CONFIRMED] T086's "full suite with `--compiler axiomc`" includes C-internal test kinds that cannot run against axiomc
- Where: T086 §Scope/§Acceptance; `tests/unit` (axiom0-unit), `tests/encode`, `tests/obj`, `tests/link` (C drivers, cross-link) from T007/T024/T026/T027.
- Fix: T005 tags each test kind `needs: axiom0-internal`; T086 acceptance = "all tests without that tag pass with axiomc", and lists T086's own expected skip counts. T086/T087 (QA-owned) also need a stated fix path: failures become filed fix tasks for the owning port task, not QA edits to the compiler.

### A3-24 [MINOR] [CONFIRMED] Shared-file and scope slips in P0/P1 tasks
- T001 "update the skill too" (`.claude/skills/axiom-syntax/SKILL.md`) and ADRs in `spec/decisions`: paths list only spec files (T003/T003a/T045 also write ADRs — `spec/decisions` only in T001/T110).
- T005 and T006 are both ready after T004 and both write under `tools/tests`; T006 also edits `tools/ci.sh` — lists neither.
- T026/T027 fixture `.obj`/`.exe` files are git-ignored except under `tests/**/fixtures/**`; say so, else `taskctl commit` silently drops them ("skip (git-ignored)").
- T010/T011/T012 "ui tests" location unspecified (`tests/ui/lex`, `tests/ui/parse` not in any `paths`).

### A3-25 [MINOR] [CONFIRMED] T046–T049 acceptance overlap: "Every AXS-OWN rule" in T046 vs "matrix rows for init" (T047)
- Where: T046 §Acceptance, T047 §Acceptance, T045 §Scope (AXS-OWN/CAP/DROP rule IDs and matrix).
- Fix: T045 tags each matrix row with the task that must pass it (T046/T047/T048/T049); T046/T047 acceptance refer only to those rows.

### A3-26 [MINOR] [PLAUSIBLE] T018 MIR text parser is test-only C code and will be ported too
- Where: T018 §Scope; R7 (minimal C, QA fails out-of-subset C); T082 ports "verifier", whose tests are written in MIR text.
- Consequence: extra C (and later Axiom) for something the self-host subset does not need.
- Fix: decide in T003a: either the MIR parser is an explicit test-infrastructure exception, or verifier tests use a C test driver that builds MIR in memory.

### A3-27 [MINOR] [PLAUSIBLE] Interpreter performance vs acceptance sizes
- Where: T070 (100k-element stable sort), T073a (1M arena allocations, in both modes), T075 benchmarks; T021 step limit "for tests" but no default per-test timeout in T005.
- Consequence: interp-mode timeouts or step-limit aborts on std tests.
- Fix: T005 fixes a default timeout and `timeout:` directive; T021 states the interpreter throughput target and step-limit default; heavy tests use `modes: native` with a small interp twin.

## Checked and OK
- T001: deps/paths consistent; grammar must admit `@at` (covered); owner opus, gate opus.
- T002: dep T001; diagnostics taxonomy feeds T009; OK (A3-02 for the registry split).
- T003: dep T001; SPEC-03 decisions cite sources; OK.
- T003a: dep T003; scope covers extension points and the self-host list; acceptance checkable by review; OK.
- T004: skeleton/CMake/ci acceptance is command-checkable (cmake, `od -c`); only the A3-02/A3-22 notes apply.
- T005: self-test acceptance is concrete (22+1 byte greeting, CRLF, wrong UTF-8); only the A3-01 scope gaps.
- T006: acceptance is a fixture per rule; A3-24 for unlisted edits.
- T007: unit tests enumerated; needs the CMake/runner decision (A3-01/A3-02).
- T008: edge cases enumerated (CRLF, BOM, empty, multibyte); OK.
- T009: X-macro compile-time check is verifiable; A3-02 for code files.
- T010: strong golden acceptance (Vietnamese literal, char escapes, error codes); driver edit unlisted (A3-02).
- T011, T012: golden + ui tests; T012 ambiguity test for `a < b` vs `f<T>(x)`; OK.
- T014: acceptance lists cases; `resolved` golden kind (A3-01).
- T015: node-kind coverage vague (A3-15), otherwise OK.
- T016: per-command/option tests; OK.
- T018–T021: acceptance concrete; driver edits unlisted (A3-02); T017 dep (A3-06).
- T022: gate; deps OK.
- T024: GNU-as table generation; needs `encode` kind (A3-01).
- T026, T027: cross-link oracle with SKIP is well specified; fixture location (A3-24).
- T029: differential + determinism; deps OK.
- T030–T032, T035, T036, T039–T042: chain and paths consistent except A3-05/A3-07.
- T033, T037: native catch-up scope matches the interp features of their predecessors except `char` (T034) — add "char zero-extend/compare, shifts" explicitly to T037.
- T044: deps T042, T043; perf part vague (A3-15).
- T045: dep T003; spec-only; OK.
- T047, T050, T051, T052: OK apart from A3-15/A3-25.
- T053, T055–T057, T059: scope coherent; T053 should absorb receivers and inherent impls on primitives (A3-07).
- T062: OK apart from A3-15.
- T063–T068 (post-self-host): deps to T2xx consistent; path layout (A3-20).
- T069–T075: deps mostly right; additional dep T061a for T069 (mem intrinsics) is advisable.
- T076: paths include the whole board — it effectively runs alone; OK.
- T086, T087: A3-23.
- T088–T091, T211–T224, T311–T323, T750, T751: planning/gate frame consistent; T224 deferred correctly; paths speculative (A3-20).
- T092–T109: disjoint paths (`spec/requirements/raw/Cxx.md`), parallel-safe; each chunk ~2 MB of documents, so "skim" must be by headings/grep (as the procedure says).
- T110: critical; OK.
- Dependency/critical flags: T001, T002, T003, T003a, T004 (pri < 10) and T110, T111, T2xx critical are intentional; no task has a dependency cycle (`taskctl validate` OK, 143 tasks).
- Native catch-up coverage: every interp feature T030–T057 has a named catch-up (T033, T037, T040, T042, T051, T059, T061a native); exceptions are const tables/static (A3-13), FFI in the oracle (A3-08), FFI natively (T065).

## Cross-lens notes
- (Self-host lens) `static`/const tables and interp FFI (A3-08, A3-13) may also be self-host blockers; the self-host std list in T003a should state them.
- (Process lens) A3-03 (shared tree vs worktrees), A3-12 (T111 placement), A3-22 (critical flags) are scheduler/harness decisions.
- (Ladder lens) T043 (-O1 optimizer) and the T018 MIR text parser are candidates for R7 "minimal C" review.
