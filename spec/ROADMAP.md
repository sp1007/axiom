# Axiom implementation roadmap (P0 → v1.0 → ecosystem)

## Tóm tắt
Lộ trình ràng buộc của toàn dự án. P0–P10: viết compiler `axiom0` bằng C11 chỉ đủ để biên dịch
được bản viết lại bằng Axiom (`axiomc`) và đạt điểm cố định (T087); sau đó axiom0 đóng băng, mọi
tính năng P11–P23 viết một lần bằng Axiom; P24 (hệ sinh thái) hoãn tới khi chủ dự án quyết định.
Chín nguyên tắc R1–R9: spec rộng – cài đặt theo lát cắt dọc; lõi trước, tự biên dịch, rồi mới mở
rộng; lập kế hoạch cuốn chiếu trong khung cố định (task lập kế hoạch T2NN, gate T3NN); mọi yêu cầu
đều được truy vết; Windows x64 trước; C tối thiểu; thư viện chuẩn viết bằng Axiom ngay từ đầu; gate
chỉ có ĐẠT hoặc BỊ CHẶN. Đợt thẩm định 2026-09-30 đã chỉnh: test viết trước bản native mang dấu
`native-after`; oracle chạy được heap/hệ điều hành qua intrinsic "host"; tách các task quá lớn;
file dùng chung tách theo vùng. Thay đổi phạm vi phải có ADR và một dòng trong nhật ký cuối file.

Status: **baseline, binding**. Owner: axiom-architect. Changing a phase, an epic's scope or the phase
dependency graph requires an ADR (`spec/decisions/`) and an entry in the change log at the bottom.
Task-level detail lives on the board (`_workspaces/tasks/`); this file fixes the *shape* of the whole
project so tasks created at different times stay consistent.

Normative sources: `docs/base/specs`, `docs/base/tasks`, `docs/base/others` (concluded, lightly
reviewed). `docs/base/discussions` is brainstorming only. Numbers below are docs/base file numbers.

## 1. Roadmap decisions

- **R1 — Spec goes wide, implementation goes vertical** (0263 §52, 0152 §81). Every feature crosses
  the whole pipeline with tests before the next starts.
- **R2 — Core first, then self-host, then breadth.** P0–P10 build the Stage-0 compiler `axiom0` (C11)
  far enough to compile its own Axiom rewrite `axiomc`, reaching a fixed point (T087). This follows
  the later ladder (0263 §51, tasks/0260, tasks/0262) rather than the earlier order in 0152 §80, which
  put async/concurrency/GPU before self-hosting: doing that would implement every such feature twice
  (in C, then again in Axiom).
- **R3 — axiom0 freezes at the self-host gate.** After T087, `bootstrap/axiom0` receives only bug
  fixes needed to rebuild `axiomc` from scratch (bootstrap trust chain). All phases P11+ are
  implemented in `compiler/` (Axiom source) and `std/`, built by `axiomc`. Engineers keep their
  areas (frontend/semantics/backend/stdlib); only the implementation language changes.
- **R4 — Rolling-wave planning with a fixed frame.** Phases P0–P10 are fully tasked now. Each phase
  P11+ has a fixed **planning task** (T2NN) and **gate task** (T3NN) already on the board. The planning
  task expands only the epics listed here into tasks, following §4. New scope discovered later becomes a
  new epic through an ADR — never ad-hoc tasks.
- **R5 — Every requirement is traced.** `spec/requirements/CATALOG.md` maps each requirement to a task
  or to an epic here (`EPIC(E15.3)`); the phase planning task converts its epics' requirements to task
  ids. `reqcov.py --strict` must pass at every gate.
- **R6 — Targets:** Windows x64 PE first, Linux x64 ELF second (0181) — Linux arrives after
  self-hosting (E16.9, by R7); other targets in P16 through the shared target-independent LIR /
  target description (0152 §68, 0163).
- **R7 — Minimal C, general core.** The C core exists only to reach self-hosting fast; C code that
  will be rewritten anyway is waste. axiom0 implements exactly the self-host subset defined in
  `spec/SPEC-00-bootstrap.md` (T003a) — nothing more — while its data models (types, HIR, MIR, LIR,
  target description, object model) reserve extension points for every later epic
  (`spec/SPEC-04-core-extensibility.md`), so P11+ features plug in without redesign. Features not
  needed to compile axiomc (dyn/vtables, comptime fn, linear-scan regalloc, optimizer ladder 2,
  Linux ELF, separate compilation, unwind info…) are post-T087 epics. QA fails any axiom0 change
  that implements out-of-subset features.
  *Conditional exception (ADR-0005 §7):* if the stage-1 gate T086 measures a self-compile outside the
  SPEC-20 budget, the architect pulls a minimal linear-scan slice of E15.8 into axiom0 as a new P10
  task before T087. Nothing else may be pulled forward without an ADR.
- **R8 — Std in Axiom as soon as possible.** The standard library (including the self-host std subset)
  is written in Axiom from the start and compiled by axiom0 — never implemented in C; C provides only
  compiler intrinsics (including the host-interface intrinsics of ADR-0002, which the oracle implements
  so std also runs under the MIR interpreter) and FFI to the OS. Each std task depends on exactly the
  language features it uses — in the oracle **and** natively — so library work (and dogfooding of the
  compiler) starts as early as possible but never before a feature it needs. std is not ported at
  self-hosting: axiomc compiles the same sources.
- **R9 — Gates are PASS or BLOCKED** (0264 §20, ADR-0005 §3). A gate never closes with a known
  implementation bug; the only tolerated non-passing tests are `xfail` entries for a spec gap that has
  an ADR and a task. Tests written before their native support carry `native-after: <task>`, removed
  by that native catch-up task (ADR-0005 §1).

## 2. Phase map

```
P0 foundation+traceability → P1 kernel → P2 frontend → P3 semantic core (oracle)
  → P4 first native exe → P5 language core → P6 ownership/capability/drop
  → P7 abstraction (methods, generics, traits, closures, const items, raw pointers, host interface;
       modules T060 open right after the P5 gate, in parallel with P6)
  → P8 FFI (the rest of backend maturity moved after self-hosting by R7)
  → P9 core+std libraries → P10 self-hosting fixed point (axiom0 frozen)
        ├─ P11 concurrency & async ───────────────┐
        ├─ P15 optimizer 2.0 + regalloc (opens at once; vectorization waits for P12)
        ├─ P12 numeric, float, SIMD
        ├─ P13 low-level, unsafe, freestanding, security ── P16 targets ── P17 debugging
        ├─ P14 comptime 2.0, reflection, generators
        └─ P18 compiler architecture 2.0 ── P19 developer tooling
                                           └─ P20 build & packages (also needs P16)
  P21 std completion (needs P11, P13)   P22 GPU & heterogeneous (needs P11, P12, P16)
  P23 v1.0 conformance, freeze, release (needs P11–P22)
  P24 ecosystem runtimes (post-v1, deferred until the owner decides)
```

| Phase | Tasks now | Planning task | Gate task | Depends on gates |
|---|---|---|---|---|
| P0 foundation / traceability | T001–T006, T003a, T092–T111 | — | T111 | — |
| P1 kernel | T007–T009 | — | (T022) | P0 foundation tasks they name (run alongside traceability) |
| P2 frontend | T010–T016, T015b | — | (T022) | P1 |
| P3 semantic core | T017–T022 | — | T022 | P2, P0 gate T111, ownership spec T045 (for T018) |
| P4 native | T023–T029, T025b | — | T029 | P3 |
| P5 language core | T030–T044, T038b | — | T044 | P4 |
| P6 ownership | T045–T052, T048b (spec T045 runs early) | — | T052 | P5 |
| P7 abstraction | T053–T057, T054b, T059–T062, T061a–T061d (T060 opens after the P5 gate) | — | T062 | P6 |
| P8 FFI (backend maturity trimmed by R7) | T065 | — | (T075) | T060, T061b |
| P9 libraries (self-host std subset) | T069–T075, T071b, T071c, T073a, T074b | — | T075 | P7, P8 |
| P10 self-hosting | T076–T087 | — | T087 | P9 |
| P11 concurrency & async | T088–T090 | T211 | T311 | P10 |
| P12 numeric & SIMD | — | T212 | T312 | P10 |
| P13 low-level & security | — | T213 | T313 | P10 |
| P14 language completion: comptime 2.0, reflection, generators, dyn | T058 | T214 | T314 | P10 |
| P15 optimizer 2.0 + regalloc | T063, T064 | T215 | T315 | P10 (E15.5 needs P12) |
| P16 targets & platforms | T066 | T216 | T316 | P13 |
| P17 debugging & introspection | T068 | T217 | T317 | P16 |
| P18 compiler architecture 2.0 + Windows artifact kinds | T067, T750, T751 | T218 | T318 | P10 |
| P19 developer tooling | — | T219 | T319 | P18 |
| P20 build & packages | — | T220 | T320 | P16, P18 |
| P21 std completion | — | T221 | T321 | P11, P13 |
| P22 GPU & heterogeneous | — | T222 | T322 | P11, P12, P16 |
| P23 v1.0 release | T091 | T223 | T323 | P11–P22 |
| P24 ecosystem (post-v1) | — | T224 (deferred) | T324 (deferred) | P23 + owner decision |

Core vertical-slice names (ADR-0005; SPEC-00 holds the full BOOT-00..38 map): VS0 = T022 (oracle),
VS1 = T029 (first native, 0263 §51 VS#1), P5 gate = T044, VS2 = T086–T087 (self-hosting, 0263 §51
VS#2). Only board-editing tasks (T110, T111, T2NN) are "critical, run alone"; the P0 spec tasks and
the repository skeleton run in parallel (ADR-0005 §11).

## 3. Epics per phase (P11+)

Each epic: scope, key sources, exit criterion. Sources are starting points — the planning task also
pulls every catalogue requirement marked `EPIC(<id>)`.

### P11 — Concurrency & async (compiler/ + std/)
- **E11.1 Concurrency semantics** — Send/Share auto-traits, spawn capture rules, data-race = compile
  error, memory model. Src 0079 0091 0105 0033 0040 tasks/0298 tasks/0488 tasks/0685. Exit: race
  conformance suite green. *(T089)*
- **E11.2 Atomics & memory ordering** — Atomic<T>, orderings, fences, lowering to x64/other targets,
  oracle scheduler exploration. Src 0092 0208 tasks/0328 tasks/0515. Exit: litmus tests pass under
  oracle and native stress.
- **E11.3 Threads & synchronisation library** — thread spawn/join, Mutex, RwLock, Condvar, Once,
  channels, thread-local storage. Src 0203 0206 0207 0209 tasks/0329 tasks/0623. Exit: native stress
  suite. *(T090)*
- **E11.4 Async/await** — Future lang item, state-machine lowering, cancellation & drop, Waker.
  Src 0093 0201 0202 0248 tasks/0275 tasks/0297. Exit: async conformance. *(T088)*
- **E11.5 Executors, fibers & structured concurrency** — single/multi-thread executor, task groups,
  fiber/stackful model, scheduler. Src 0204 0205 tasks/0277 tasks/0278 tasks/0620. Exit: executor
  benchmarks + structured-cancellation tests.
- **E11.6 Async IO integration** — IOCP (Windows), epoll/io_uring (Linux) reactor, unified IO model.
  Src 0221 tasks/0335. Exit: async file/socket tests.

### P12 — Numeric, floating point & SIMD
- **E12.1 Integer model completion** — all widths incl. i128/u128 if specified, wrapping/checked/
  saturating families, bit ops, conversions. Src tasks/0327 tasks/0334 tasks/0431.
- **E12.2 Floating-point semantics** — f32/f64 types enter the language here (axiom0 has none; T034),
  SSE2 scalar codegen and XMM argument passing in the Windows x64 ABI, IEEE-754 rules, NaN/signed zero, rounding, float formatting/
  parsing, math library accuracy contract. Src tasks/0338 tasks/0345 tasks/0331.
- **E12.3 SIMD & vector types** — portable vector types, masks, lane ops, target feature detection.
  Src 0095 tasks/0337 tasks/0341 tasks/0344 tasks/0347.
- **E12.5 CPU feature detection & function multiversioning** — explicit `@target_feature` /
  multiversioned functions with a generated dispatcher; features never change language semantics.
  Src tasks/0453 §194.14-15, 0095 §8, tasks/0341 (ASIMD-14).
- **E12.4 SIMD backend** — SSE2/AVX2 (and NEON in P16) instruction selection/encoding for vector ops.
  Src tasks/0403 tasks/0407.
Exit (phase): numeric conformance + differential interp/native for float and vector programs.

### P13 — Low-level systems, unsafe, freestanding, security
- **E13.1 Unsafe & UB model** — builds on the minimal core version (T061a: raw pointers, unsafe blocks,
  memory intrinsics); here: full unsafe blocks/fns rules, raw pointer rules, provenance, trusted-unsafe
  boundaries. Src 0071 0044 tasks/0339 tasks/0282.
- **E13.2 Raw memory, volatile, MMIO, layout control** — volatile, packed/aligned repr, unions (0072),
  address spaces. Src tasks/0328 tasks/0515 0067 0072.
- **E13.3 Runtime composition & freestanding profile** — hosted vs freestanding, `@entry`, optional
  runtime, startup/static init/global state, runtime capability graph. Src 0143 0097 tasks/0358
  tasks/0359 tasks/0370 tasks/0455.
- **E13.4 Safety profiles & capability security** — profiles, sandboxing hooks, secure memory,
  constant-time annotations. Src tasks/0342 tasks/0449 tasks/0467 tasks/0703.
- **E13.6 Fixed-address declarations (`@at`)** — owner requirement REQ-OWNER-003, ADR-0001:
  overlay/placement of statics, arrays, structs, functions at absolute addresses, used with ordinary
  syntax; `Volatile`/`Mmio` field types; overlap/alignment checks; absolute symbols and pinned
  sections in object writers and linker; raw-binary/ELF freestanding images; oracle simulated
  address space. Src ADR-0001, 0071 §31-32, 0044, 0097, tasks/0328.
  Exit: a freestanding test image with an `@at` vector table and UART register block runs under the
  oracle with a device model, and native images place every `@at` object at its address.
- **E13.7 Module-relative bindings** — owner requirement REQ-OWNER-005,
  ADR-0001 §5-6: `@at(image("mod") + off)` / `image_self()` overlays resolved at module init in the
  hosted profile, hooked into the DLL/EXE initialisers of E18.7 (PE DLL output).
  Src ADR-0001, 0187, 0104, tasks/0336. Exit: a test DLL loaded into a test host EXE calls host
  functions and reads host data through module-relative bindings; missing module → DllMain FALSE.
- **E13.5 Panic & unwinding strategy** — panic=abort vs unwind decision per profile, cleanup
  guarantees across unwinding. Src 0229 tasks/0351 tasks/0700.
Exit: freestanding program boots without std; UB/safety conformance suite.

### P14 — Language completion: comptime 2.0, reflection, generators, dyn
- **E14.1 Comptime completion** — full comptime execution model, partial evaluation, specialization.
  Src 0102 0140 tasks/0340 tasks/0346 tasks/0509.
- **E14.2 Reflection & derive** — compile-time reflection API, derive framework, code generation
  boundary (no textual macros unless specified). Src tasks/0343 tasks/0296 tasks/0433.
- **E14.3 Generators & `yield`** — iterator state machines, lazy control flow. Src tasks/0512.
- **E14.4 dyn Trait & vtables** — dyn compatibility, coercion, vtable layout, native emission.
  Src tasks/0476 217.49-50, 0212. *(T058)*
Exit: derive(Debug/Eq/Hash/Serialize-style) implemented via reflection in std; generator tests.

### P15 — Optimizer 2.0
- **E15.1 OptIR: SSA / MemorySSA** — Src tasks/0398 0315 tasks/0366.
- **E15.2 Alias & escape analysis, allocation promotion** — Src tasks/0395 tasks/0397.
- **E15.3 Loops & bounds-check elimination** — SCEV, LICM, unrolling, BCE. Src tasks/0402.
- **E15.4 Inlining, specialization, devirtualization** (+ copy propagation, SROA) — Src tasks/0401
  tasks/0551. *(T064)*
- **E15.5 Auto-vectorization** — Src tasks/0403 tasks/0407 0095.
- **E15.6 LTO / whole-program / section GC / PGO** — Src tasks/0355 tasks/0408 tasks/0409 tasks/0410.
- **E15.8 Register allocation (linear scan) & better instruction selection** — first P15 task so
  axiomc itself becomes fast. Src 0182 0235 0252 tasks/0557. *(T063)*
- **E15.7 Performance contract** — benchmark suite, code-size & compile-time budgets, regression CI.
  Src tasks/0706 0074.
Exit: differential green at -O2; benchmark targets met and tracked in CI.

### P16 — Targets & platforms
- **E16.9 Linux x86-64 static** — SysV ABI, ELF64 writer, static linker, WSL test runs. Src 0192
  0053. *(T066; first P16 task)*
- **E16.1 Target description as data** — TargetDesc/ISA tables, backend conformance. Src 0163
  tasks/0524 tasks/0784.
- **E16.2 Linux ELF dynamic** — PIE, GOT/PLT, shared objects, libc interop. Src 0197.
- **E16.3 AArch64 Linux** — Src 0193 tasks/0521.
- **E16.4 macOS AArch64 + Mach-O** — Src 0196.
- **E16.5 Android AArch64 (+JNI layer)** — Src 0198 0200.
- **E16.6 WASM32** — Src tasks/0784.
- **E16.7 RISC-V64** — Src 0152 §59 tasks/0784.
- **E16.8 Cross-compilation & target matrix, OS platform layer** — any host builds for any target
  from one frontend; target SDK/sysroot selection. Src tasks/0453 tasks/0587 0220 tasks/0336.
- **E16.10 Artifact kinds & library matrix** — for every tier-1 target: executables, **static
  libraries** (produce Axiom `.lib`/`.a`; consume C/system archives), **dynamic libraries** (produce
  PE DLL + import `.lib` / ELF `.so` / Mach-O `.dylib`; consume system and third-party dynamic libs,
  lazy/eager binding, versioned symbols where the format supports them), import-library generation
  from `.def`-like declarations. Generalises E18.7 (Windows libraries) and E16.2 (ELF dynamic). Src 0563 0197
  0164 0217 tasks/0369 tasks/0453.
- **E16.11 Universal / multi-architecture artifacts** — explicit multi-target artifact composition
  (Mach-O universal x64+arm64 first; bundle formats elsewhere), never implicit. Src tasks/0453 §194.29.
- **E16.12 Windows on ARM64** — PE/COFF ARM64, Windows ARM64 ABI, reuse of the AArch64 backend.
  Src 0181 0193 tasks/0453.
Exit: full run suite on each tier-1 target (Windows x64, Windows ARM64, Linux x64, Linux AArch64,
macOS AArch64); WASM/RISC-V tier-2; the artifact matrix below is green.

Artifact matrix (E16.10–E16.12; ✔ = must be produced *and* consumed with tests):

| Target | executable | static lib | dynamic lib | notes |
|---|---|---|---|---|
| x86_64-windows | `.obj` (T026), `.exe` (T028) — core | `.lib` (E18.7) | `.dll` + import `.lib` (E18.7) | first target |
| aarch64-windows | PE32+ ARM64 | `.lib` | `.dll` | E16.12 |
| x86_64-linux | ELF (E16.9) | `.a` | `.so` (E16.2) | static first |
| aarch64-linux | ELF | `.a` | `.so` | E16.3 |
| aarch64-macos | Mach-O | `.a` | `.dylib` | E16.4; universal with x86_64 (E16.11) |
| aarch64-android | ELF PIE | `.a` | `.so` (JNI) | E16.5 |
| wasm32 | `.wasm` module | object archive | — (component model later) | E16.6, tier-2 |
| riscv64-linux | ELF | `.a` | `.so` | E16.7, tier-2 |

### P17 — Debugging & runtime introspection
- **E17.1 Debug IR + CodeView/PDB (Windows)** — Src 0190 0191.
- **E17.2 DWARF (ELF/Mach-O)** — Src tasks/0596.
- **E17.3 Unwinding & backtraces on all targets** — Src 0188 tasks/0700. *(T068 = Windows slice)*
- **E17.4 Debugger contract & symbolication** — Src 0100 0147 tasks/0811.
- **E17.5 Profiler & performance introspection** — Src tasks/0572 tasks/0730.
- **E17.6 Sanitizers & runtime verification** — Src tasks/0599 tasks/0733.
- **E17.7 Trace & replay** — Src tasks/1058 (AXREPLAY) 0147.
Exit: step-through debugging in a standard debugger on Windows and Linux; sanitizer suite.

### P18 — Compiler architecture 2.0
- **E18.1 Query engine / semantic database** — demand-driven queries, cycle handling, invalidation.
  Src tasks/0530 tasks/0533 tasks/0781 tasks/0384.
- **E18.2 Incremental compilation** — API/semantic/codegen fingerprints (0152 §78). Src 0142
  tasks/0778.
- **E18.3 Parallel compilation** — Src tasks/0530 tasks/0790.
- **E18.4 Artifact format & module interface files** — Axiom object/LTO/semantic package sections.
  Src tasks/0787 tasks/0739.
- **E18.5 Pass contracts & proof-carrying transformations** — Src tasks/0578 tasks/0545.
- **E18.7 Windows x64 artifact kinds: static `.lib`, `.dll` + import `.lib`** — owner requirement
  REQ-OWNER-006; first P18 tasks (P18 opens right after P10). COFF archive writer/reader, `--kind
  exe|obj|lib|dll`, PE DLL with exports/DllMain initialiser/.reloc, import-library generation;
  consume third-party .lib/.dll. The C core emits only .obj/.exe but reserves these kinds (SPEC-04).
  Src 0164 0217 0563 0186 0187 tasks/0369. *(T750, T751)*
- **E18.6 Separate compilation, multiple objects, archives, section GC** — Src 0164 0217 0099
  tasks/0369. *(T067)*
Exit: no-op rebuild < 100 ms on the compiler itself; edit-one-private-fn rebuild re-typechecks only
that module.

### P19 — Developer tooling
- **E19.1 LSP server** — diagnostics, go-to-definition, hover, completion, rename. Src 0101 tasks/0374.
- **E19.2 Formatter (canonical form)** — Src tasks/0476 (canonical language form).
- **E19.3 Refactoring engine** — Src 0101.
- **E19.4 Diagnostics UX 2.0 & AI-agent interface** — machine-readable fixes, explain codes. Src 0146
  tasks/0360 tasks/0421.
- **E19.5 Documentation generator & test framework UX** — Src tasks/0418 tasks/0361.
Exit: VS Code extension using the LSP; formatter idempotence over the whole corpus.

### P20 — Build system & package ecosystem
- **E20.1 Build graph & driver** — Src 0168 tasks/0356 tasks/0372 tasks/0411.
- **E20.2 Package manager, resolution, lockfiles** — Src 0098 tasks/0412 tasks/0446.
- **E20.3 Registry & distribution** — Src tasks/0665.
- **E20.4 Hermetic/reproducible builds & supply-chain trust** — Src tasks/0590 tasks/0449 tasks/0772.
- **E20.5 ABI stability, versioning, binary compatibility** — Src 0104 tasks/0452.
- **E20.7 Axiom dynamic components: plugins, hot-reload, versioned Axiom ABI** — Axiom-to-Axiom
  dynamic libraries with a stable, versioned interface (not just C ABI), component discovery/loading,
  hot-reload with state hand-off, ownership/capability rules preserved across the boundary.
  Src tasks/0584 tasks/0583 0104 tasks/0739 tasks/0856.
- **E20.6 SDK / sysroot / toolchain distribution** — Src tasks/0605 tasks/1034.
Exit: multi-package workspace builds reproducibly from lockfile on two machines.

### P21 — Standard library completion
- **E21.1 Collections breadth & data-oriented storage** — deque, B-tree map, SoA helpers, handles/
  generational storage. Src 0210 tasks/0348 tasks/0349 tasks/0608.
- **E21.2 Text & Unicode complete** — normalization, segmentation, case mapping. Src tasks/0332 0089.
- **E21.3 OS: fs, process, env, signals, IPC** — Src tasks/0335 tasks/0443.
- **E21.4 Networking** — sockets, DNS, async integration. Src tasks/0461 tasks/0335.
- **E21.5 Time & clocks** — Src tasks/0440 tasks/0464.
- **E21.6 Virtual memory & memory mapping** — Src tasks/0437.
- **E21.7 Serialization & binary data model** — Src tasks/0650 tasks/0742 tasks/0841.
- **E21.8 Crypto primitives & secure memory** — hashes, RNG, constant-time utilities. Src tasks/0467.
- **E21.9 Allocators: pool, custom and concurrent allocators** (basic arenas + typed ID tables are
  core, T073a) — Src 0106 0036 tasks/0280.
Exit: std API reference complete; std conformance suite on all tier-1 targets.

### P22 — GPU & heterogeneous computing
- **E22.1 Execution domains & kernel model** — Src 0096 0139 0120 tasks/0299.
- **E22.2 Device memory & ownership across devices** — Src 0120 tasks/0626.
- **E22.3 GPU codegen backend (SPIR-V first unless ADR decides otherwise)** — Src tasks/0626.
- **E22.4 Host runtime (Vulkan/D3D12 compute)** — Src tasks/0626.
Exit: kernel conformance examples run on a GPU with oracle-checked results.

### P23 — v1.0 conformance, freeze, release
- **E23.1 Full conformance suite & compiler qualification** — Src 0017 0145 0150 tasks/0602.
- **E23.2 Global contradiction audit & spec freeze** — Src 0151 0121. *(T091)*
- **E23.3 Release engineering** — binaries, installer, docs site, versioning policy.
Exit: Axiom v1.0 tagged; `reqcov.py --strict` shows every v1-core and v1-full requirement implemented.

### P24 — Ecosystem runtimes (post-v1, deferred)
Application-domain libraries from the corpus, catalogued as `post-v1` requirements (chunk C18 of the
extraction; `EPIC(E24.n)` in the catalogue). Planning task T224 and gate T324 are created
**deferred** and only start when the project owner explicitly schedules them.
- **E24.1 AI serving & agents** — model serving runtimes, agent frameworks.
- **E24.2 GUI & windowing** — windowing, widgets, input, text rendering.
- **E24.3 Audio & media** — audio graphs, codecs, media pipelines.
- **E24.4 Graphics** — rendering engines and scene runtimes on top of P22.
- **E24.5 Scientific computing & ML** — tensors, linear algebra, training runtimes.
- **E24.6 Databases & storage engines** — embedded stores, query engines.
- **E24.7 Distributed systems** — RPC, consensus, cluster runtimes.
- **E24.8 Domain runtimes** — finance, transport and the other application domains of the corpus.
- **E24.0 General post-v1 backlog** — deferred features not part of any specific epic.
- **E24.9 Ecosystem (post-v1)** — unspecified ecosystem projects. — finance, transport and the other application domains of the corpus.
Exit (phase): defined by T224 per epic when the owner schedules P24.

## 4. How a planning task expands a phase (standard, so all phases look alike)

1. Read this file's section for the phase, the catalogue rows with `EPIC(E<phase>.*)`, the phase's
   sources, and the gate reports of the phases it depends on.
2. For each epic create **3–10 tasks**, each finishable by one agent in one sitting (≤ ~1–2k changed
   lines), owner = area owner (frontend/semantics/backend/stdlib/qa/architect), `paths` narrow,
   `spec:` refs, `covers:` requirement ids, acceptance expressed as tests (positive + negative), plus
   the standard DoD lines, and `model:`/`gate_model:` by the axiom-tasks model rule. Start each epic with a spec task (architect) when the canonical `spec/`
   lacks that area — never implement from raw docs alone. **Cross-phase prerequisites:** when this
   file says an epic needs another phase (E15.5 needs P12; P16 needs P13; P20 needs P16 and P18; …),
   every task of that epic gets `depends` on that phase's gate task (E15.5 tasks → T312). Shared
   files go in `locks:`, single-owner files in `paths:` (ADR-0005 §14).
3. IDs: next free numbers from `T400` upward in phase blocks of 50 (`T400–T449` P11, `T450–T499`
   P12, … `T1050–T1099` P24), taken with `taskctl.py new-id --phase <P>`. Titles: `<Epic id> <short
   title>` (e.g. `E11.2 Atomic<T> lowering x64`).
4. Make the phase gate task T3NN depend on every task of the phase; add a QA conformance task per
   epic that has an exit criterion. Phase gates use `gate_model: opus` and the gate rule R9.
5. Update catalogue statuses `EPIC(...)` → task ids; run `taskctl.py validate`,
   `reqcov.py --strict` and `harness_check.py`; record the expansion in the change log below.
6. Scope not covered by any epic → ADR proposing a new epic (added here), not a stray task.
7. **Follow-up tasks outside a planning task** (unblock splits, gap tasks found by T076 or a gate,
   fix tasks): a letter suffix of the task they derive from (`T048c`), or the next free id of the
   phase from `taskctl.py new-id --phase <P>` — `T112–T199` for P0–P10, the phase block for P11+
   (ADR-0005 §9). Never an id from the `T2NN`/`T3NN` ranges, never a retired id. A task replaced by
   a split is closed with `taskctl.py supersede`.

## 5. Change log

| Date | Change | ADR |
|---|---|---|
| 2026-10-10 | T122 created as a prerequisite for T121 to add AxLocation tracking to MIR data structures, allowing diagnostics to report accurate source locations. | ADR-0021 |
| 2026-10-10 | T121 rescoped to include bootstrap/axiom0/src/driver/pipeline.c in paths to allow pipeline integration | ADR-0020 |
| 2026-10-10 | T046 split into T120 (place model, copy classification, pipeline registration) and T121 (move dataflow analysis, use-after-move/partial-move diagnostics) due to complexity of dataflow logic | ADR-0019 |
| 2026-10-06 | T022 (VS0 gate) unblock: fix tasks T114 parser, T115 typeck/driver, T116 MIR builder, T117 interpreter (after T116); T022 depends on all four and owns `tools/ci.ps1`; T069 depends on T061 (selfhost-subset rule d) | ADR-0016 |
| 2026-10-01 | Audit 2026-09-30 (4 lenses) applied. Oracle host interface: T061c; std runs under the interpreter (R8 wording) | ADR-0002 |
| 2026-10-01 | Backend robustness: ABI lowering as a LIR pass, machine-IR verifier, stack probes, `--stack-reserve` (T025 narrowed, new T025b; T027, T028, T037, T086) | ADR-0003 |
| 2026-10-01 | Self-host subset additions: wrapping/bit intrinsics (T034/T037), constant tables in `.rdata` (T061, new T061d), stored views (T045/T048), HashMap insertion order + shared hash (T007/T069/T073), generic drop glue (new T054b), derive Hash/Ord (T056), control/pattern forms (T031, T038, new T038b) | ADR-0004 |
| 2026-10-01 | Plan structure: `native-after` tests and VS1 reduced to 0263 VS#1 (T021, T028, T029, T033…); shared files split per area/command with `locks:`; gates PASS-or-BLOCKED with XFAIL (new R9); vertical frontend slice (T014 → T011, new T015b); T018 waits for T045; T017 waits for T111; T060 opens after the P5 gate; T034 ∥ T033 and T043 ∥ T042; only board-editing tasks are critical; self-compile budget with a conditional R7 exception; splits T025b, T038b, T048b, T054b, T061b, T061c, T061d, T071b, T071c, T074b; T076 must split the port tasks; follow-up id rule (§4.7); P24 epics E24.1–E24.8 and deferred gate T324; phase gates on Opus; R6 listed before R7 | ADR-0005 |
| 2026-10-01 | Bootstrap forms (Drop, `char` cast, `len`, derive(Copy), Option/Result, sub-range views), manifest `axiom.toml`, std root discovery, console output | ADR-0006 |
| 2026-09-29 | Baseline roadmap P0–P24, epics E11–E24, rolling-wave frame (T2NN plan / T3NN gate) | — |
| 2026-09-30 | Core constructs completed: T061a minimal raw pointers/unsafe/intrinsics (needed by Box/Vec/FFI; E13.1 extends it), slices in T048/T051, if-let/while-let/destructuring in T038 | self-host needs |
| 2026-09-30 | Text & scalars before self-host: `char` in T034/T010, char + UTF-16 primitives in T071, chars() in T073, W APIs only in T074; floats entirely in E12.2 (not in axiom0), float formatting removed from T071 | owner decision |
| 2026-09-30 | R8 std in Axiom as early as possible: T065 → T051+T060, T069 → T056+T060, T073 +T059, T075 +T062 | owner remark |
| 2026-09-30 | Self-host std subset completed: T073a arenas + typed ID tables (from E21.9), sort (T070), StringBuilder/format/parse/ByteBuf (T071), binary files/path/dir listing/clock (T074); subset defined early in T003a | self-host needs |
| 2026-09-29 | E18.7 Windows x64 .lib/.dll + import lib right after self-hosting (T750, T751); E13.7 reduced to module-relative bindings; C core emits .obj/.exe only | REQ-OWNER-006 |
| 2026-09-29 | Output/library coverage: E16.10 artifact kinds & library matrix, E16.11 universal binaries, E16.12 Windows ARM64, E12.5 CPU multiversioning, E20.7 Axiom dynamic components; artifact matrix table | owner review of specs |
| 2026-09-29 | New epic E13.7 module-relative bindings + PE DLL output (REQ-OWNER-005) | ADR-0001 §5-6 |
| 2026-09-29 | New epic E13.6 fixed-address declarations (owner requirement REQ-OWNER-003) | ADR-0001 |
| 2026-09-29 | R7 minimal C: T058→E14.4, T061 trimmed to const items (rest E14.1), T063→E15.8, T064→E15.4, T066→E16.9, T067→E18.6, T068→E17.3; P15 opens right after P10; new T003a core extensibility contract + exact self-host subset | owner decision |
| 2026-10-10 | T047 rescoped to add locks for own.c, typeck.c, verify.c, and target verify.c so it can integrate analysis | ADR-0023 |
| 2026-10-10 | T048b rescoped to remove sub-ranges and disjoint splits into new task T126 to manage size. | ADR-0026 |
| 2026-10-11 | T128 rescoped to only handle explicit drop(x) builtin. Implicit block cleanup and destructors split into new task T131. | ADR-0029 |
