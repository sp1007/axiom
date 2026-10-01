# Audit A2 — Ladder conformance (0263 §51 + tasks/0260/0262, 0264, 0172, 0181)

## Summary
Checked: 0263 in full (BOOT-00..38, §24/§28/§30 forbidden shortcuts, §40 Stage-0 completion, §41 order, §44-45 manifests/gates, §47-48 differential/fuzz), tasks/0260 (subset §3-4, S0-S3 §41, ABOOT-41..80), tasks/0262 (ladder, gates §50, V0-V4 §55), 0264 BOOTSTRAP-006 harness (§18-27, §39 gate), 0172 (kernel rules, §32 "not the whole frontend first"), 0181 (Windows-first, encoder/verifier, VS#1-#5), against T001-T087, T003a, T061a, T073a, ROADMAP R1-R8.
Result: most ladder steps are covered, and in the right order. Forbidden shortcuts (AST→asm, asm text, external assembler/linker in the production path, LLVM) are respected.
Counts: BLOCKER 1, MAJOR 4, MINOR 8.

## Findings

### A2-01 [BLOCKER] [CONFIRMED] VS1 (T028/T029) must run branches, loops, recursion, traps and calls natively, but native CFG/calls/checks arrive later in T033/T037
- Where: T021 `paths: [.., tests/run/basic]`, acceptance "exit 42, arithmetic, branches, loops, recursion (fib), overflow trap, division by zero". T028 acceptance "All tests/run/basic pass in native mode as well as interp". T029 scope "every run test executed in both modes and compared … first ABI test (add(20,22))". But T025 has only a "baseline isel", T033 scope is "Branch/loop lowering, calls with >4 args…" and T037 is "overflow checks (jo), div-by-zero checks". Ladder: 0263 §51 VS#1 comes after BOOT-11 and contains only `return 42`. CFG is BOOT-13 and Functions+ABI is BOOT-14, both after VS#1. The same order is in tasks/0262 §13-§19 and 0181 §38-41 (VS#1 exit 42, VS#2 call, VS#4 branch).
- Problem: T028 and T029 require backend features that are scheduled two to three tasks later. As written, T028 cannot pass. It passes only if the T025/T028 agent quietly takes over the scope of T033 and T037 (branch lowering, checked-arithmetic traps, calls).
- Consequence if not fixed: T028 or T029 fails QA or loops in fix rounds. If the agent does absorb the scope, T033 and T037 become partial duplicates and the ladder's "small first slice" is lost.
- Proposed fix: T028/T029 native acceptance covers only the VS1 set (constants, arithmetic without traps, locals, return). T021 run tests that use CFG/calls/traps carry `// modes: interp` with the reason "native in T033/T037" (the axiom-testing directive allows this). Move the native add(20,22) test from T029 to T033. T033 and T037 acceptance: "remove every interp-only restriction added before this task for CFG/calls (T033) or traps (T037)". T029 differential then runs over every test not marked interp-only.

### A2-02 [MAJOR] [CONFIRMED] The whole frontend is built before the first MIR, against the ladder's vertical-slice rule
- Where: T011 "AST data model for the whole v0.1 grammar". T014 `depends: [T012]`, where T012 is generics, traits/impls, closures, `dyn Trait`, raw pointers and unsafe. T015 "HIR nodes for all items/exprs/stmts/patterns/types". So T022 (VS0) comes after T016, T015, T014, T012 and T011. Ladder: 0263 §20 "AST cực kỳ nhỏ … Không thêm abstraction chỉ vì sau này có thể cần"; tasks/0262 §1 (every milestone reaches native or at least MIR) and §6 "Không vội generic/trait"; 0172 §32 "Không nên hoàn thành toàn bộ frontend rồi mới chạm backend"; ROADMAP R1.
- Problem: the first MIR, interpreter or native result can only happen after the full grammar (including out-of-subset `dyn`) is parsed and lowered to HIR. This is the "frontend 6 months, then backend" order that 0172 §32 warns against. Design flaws in HIR→THIR→MIR show up late, after a lot of HIR code exists.
- Consequence if not fixed: P2 becomes the largest horizontal chunk of C in the project. Any seam problem found at T019/T022 means reworking T015 across all node kinds.
- Proposed fix: move basic type syntax (simple paths, `[N]T` is optional) into T011. Change T014 to `depends: [T011]`. T015 lowers what T011 parses, and later tasks add HIR lowering for their own constructs. T012 stays as it is but becomes a dependency of T036/T038 (patterns, array types), T053-T057 and T061a instead of the VS0 path. The AST/HIR data model can still *reserve* variants per T003a (0263 §42 "implement later ≠ design later").

### A2-03 [MAJOR] [CONFIRMED] The MIR data model is designed before the ownership/capability/drop spec exists
- Where: T018 `depends: [T017, T003a]` claims "Define the full MIR (designed for ownership from day one)". T045 (canonical ownership/capability/drop spec) `depends: [T003]`, priority 65, and only T046 depends on it. Ladder: 0263 §42 "Implement later ≠ design later. Trước khi viết MIR phải biết MOVE, COPY, DROP, BORROW_READ, BORROW_WRITE"; 0263 §23; ABOOT-43/44/45 (tasks/0260 §45).
- Problem: T018 fixes places, operands, `view/view_mut` rvalues, drop terminators and storage markers before the rules they must support (partial moves, drop flags, region relations, stored vs ephemeral views) are written. T003a gives generic extension points but not these semantics.
- Consequence if not fixed: T046-T050 find that the MIR cannot express what SPEC-10/11/12 require (for example drop-flag places or region annotations), which means MIR rework after P5 has built on it. That rework spreads to interp, LIR and the verifier.
- Proposed fix: add T045 to T018's `depends` and raise T045's priority to just after T003a. This costs no real schedule time because T045 needs only T003 and runs in parallel with P1/P2. Alternatively, T003a must list the MIR ownership operations explicitly, but the T045 dependency is simpler.

### A2-04 [MAJOR] [CONFIRMED] Phase gates can pass with failing tests; the ladder allows only PASS or BLOCKED
- Where: T052 acceptance "Suite passes or every failure has a filed follow-up task". T062 "30-minute progfuzz campaign clean or findings filed". T013 has the same wording. Ladder: 0264 §20 ("Không có trạng thái 'gần xong'. Chỉ PASS hoặc BLOCKED"), 0263 §45 (else "BOOT-05 BLOCKED"), tasks/0262 §50 (gate requires tests, negative tests, verifier, native, no regression all green).
- Problem: the P6 gate is the adversarial ownership suite, the main evidence for ABOOT-44/45. Under this wording P7 can start with known soundness holes. XFAIL is not defined in the runner (see A2-06), so "filed" failures stay red, or get deleted.
- Consequence if not fixed: known ownership or capability unsoundness is carried into generics/closures and then into the axiomc port (T082). That is where 0262 §35 says the ownership checker must be written in the semantics it checks.
- Proposed fix: T052 and T062 acceptance: "all tests pass. A failure that is a spec gap gets an architect ADR and an XFAIL entry naming the follow-up task. An XFAIL is allowed only for a spec gap, never for an implementation bug." Fuzz findings are fixed or minimised into regression tests before the gate closes.

### A2-05 [MAJOR] [CONFIRMED] T038 acceptance uses Option, which only exists after T039
- Where: T038 acceptance "`if let`/`while let` (or spec equivalents) over Option". T039 (Option/Result lang items) `depends: [T038]`. Ladder order: 0263 §51 BOOT-17 Enum+Match comes before BOOT-18 Result+Option.
- Problem: the acceptance cannot be tested inside T038's own dependency closure.
- Consequence if not fixed: T038 QA fails, or the agent writes Option early (scope creep into T039).
- Proposed fix: T038 tests use a user-defined enum (for example `enum Opt { Some(i32), None }`). Move "if let / while let over Option" to T039's acceptance.

### A2-06 [MINOR] [CONFIRMED] BOOTSTRAP-006 harness gate items are only partly covered and not enforced
- Where: 0264 §18 (states PASS/FAIL/XPASS/XFAIL/SKIP/BLOCKED/CRASH/TIMEOUT; XFAIL must not hide regressions), §19-20 (machine-readable milestone manifest + gate), §23-24 (invariant registry → verifier rule → test, "invariant không được chỉ là comment"), §39 gate list. Board: T005 summary is "TOTAL n PASS p FAIL f SKIP s" only. T003 manifests are prose in SPEC-00. T002 `spec/invariants.md` names a verification method but nothing checks it. No gate depends on T006 (archcheck) or T013 (fuzz). A grep for `depends:.*T006` or `T013` finds no task.
- Problem: milestone gates depend on QA reading prose. The "architecture check / invariant check" legs of the 0264 §20 gate have no tool behind them.
- Consequence if not fixed: drift between SPEC-00 manifests, invariants and tests goes unnoticed, and XFAIL can't be expressed (this is also a precondition for the A2-04 fix).
- Proposed fix: T005 adds XFAIL/XPASS (XPASS counts as a failure), CRASH (compiler exit 3 = ICE) and TIMEOUT. T006 (or a small `tools/gatecheck.py` in T022) checks that every invariant in `spec/invariants.md` names an existing test dir, and that every SPEC-00 milestone's must-pass list exists and passes. Add T006 and T013 to T022's `depends`.

### A2-07 [MINOR] [CONFIRMED] Vertical-slice names clash with the ladder
- Where: board VS0 = T022 (oracle), VS1 = T029 (native), VS2 = T044 (P5 language core). 0263 §51: VERTICAL SLICE #1 = native exit 42 (after BOOT-11), VERTICAL SLICE #2 = compiler in Axiom through stage-2/reproducible (BOOT-31..38). tasks/0262 §55: V0 lexer/parser, V1 source→MIR, V2 native, V3 compiler in Axiom, V4 reproducible self-host.
- Problem: "VS2" means the language-core gate on the board but self-hosting in the owner-chosen ladder. Agents reading 0263 will misread gate scope.
- Proposed fix: rename T044 to "P5 gate: language core". SPEC-00 (T003) maps the names: V0 = T011/T013, V1/VS0 = T022, V2/VS1 = T029, V3/VS2 start = T086, V4/VS2 end = T087. Label T087 "VS2 (0263 §51 BOOT-36..38)".

### A2-08 [MINOR] [CONFIRMED] The fixed-point gate skips the ladder's functional-equivalence step and the no-external-tool check
- Where: T087 acceptance "axiomc2 and axiomc3 byte-identical … verified in CI". tasks/0262 §42 (first same tests / same diagnostics / same executable semantics, then bit-for-bit), §43; tasks/0260 §41 (stage2 ≡ stage3 functionally), ABOOT-74/75/78 (no external assembler/linker; Stage-N and N+1 preserve behaviour).
- Problem: there is no stated requirement that axiomc2 passes the full suite, and no check that the bootstrap chain invokes no gcc/ld/as. The T026/T028 cross-link oracle legitimately uses gcc, so the check needs to be explicit.
- Consequence if not fixed: if determinism breaks, T087 has no intermediate milestone to report, and nothing proves ABOOT-74/75 at the gate.
- Proposed fix: add to T087: "axiomc2 passes the full suite with identical diagnostics JSON and run results to axiomc1; tools/bootstrap.py runs with gcc/ld/as removed from PATH". Keep byte identity as the final criterion.

### A2-09 [MINOR] [PLAUSIBLE] Linear scan (0263 BOOT-28) moved after self-host without a measured budget
- Where: 0263 §27 ("Sau khi có executable: Linear Scan được đưa vào"), §51 BOOT-28 before VS#2; 0181 §39/§42 (VS#2 exercises register allocation, VS#5 spills). R7 / T063 → E15.8 after T087. 0263 §49 does allow "advanced register allocation" to wait.
- Problem: this deferral fits R7 and 0263 §49, and bootstrap does not *semantically* need it. But axiomc compiled by axiom0 keeps every local in a stack slot with fixed registers, and T087 needs two full self-compiles with that code. Nobody measures whether this is acceptable.
- Consequence if not fixed: T086/T087 could be impractically slow, which would only be discovered at the very end.
- Proposed fix: T044 already records a perf baseline. Add to T086: "record wall time and peak memory of axiom0→axiomc1 and axiomc1→axiomc2 against a budget set in SPEC-20". If over budget: NEEDS OWNER DECISION on pulling T063 before T087, or accepting the time.

### A2-10 [MINOR] [CONFIRMED] Ladder steps deferred by R6/R7 are recorded only in ROADMAP, not step by step in SPEC-00
- Where: deferred ladder items are BOOT-26 Comptime (T061 reduced to const items; tasks/0260 §3 lists "comptime (limited)"), BOOT-28 regalloc (T063), BOOT-29 Full linker (T067; the Windows analogue), BOOT-30 AArch64 (P16), and 0263 §4 Linux-first (inverted by 0181 and R6). ROADMAP R6/R7 and the change log record these. T003 scope says only "milestone ladder mapped to board phases". T003a says "Justify each inclusion" and says nothing about exclusions.
- Problem: an agent who reads 0263 or tasks/0260 (both cited on many tasks) sees these as required before self-hosting. Nothing on the board maps each BOOT-nn to a task or to "deferred to Exx.y because Rn".
- Proposed fix: T003 acceptance: SPEC-00 contains the BOOT-00..38 → task / deferral table (you can use the table below). T003a acceptance: every item in tasks/0260 §3 is marked in or out, with a reason (`var` is excluded by the syntax rule; limited comptime is covered by const items).

### A2-11 [MINOR] [PLAUSIBLE] ABI lowering happens after LIR, while the ladder places it between MIR and LIR
- Where: axiom-c-stage0 SKILL.md:61 layer order `… lir < abi < target/x64`. T023 "calls with abstract ABI placeholders". T025 "ABI lowering of params/returns". tasks/0262 §19 "MIR → ABI Lowering → LIR → Machine". 0264 §22 policy (`abi: [mir]`, `lir: [abi]`). 0172 §16 (abi(main) ← verified_mir).
- Problem: this is not a forbidden shortcut, since the ABI stays out of MIR as 0262 §19 requires. But it is a structural deviation from the ladder's pipeline, and axiomc (T084) will copy it, as will SysV (E16.9) later.
- Proposed fix: the architect writes a short ADR, either confirming "ABI lowering on LIR" with the reason or reordering the layers. No owner decision is needed.

### A2-12 [MINOR] [PLAUSIBLE] The machine-IR/encoding verifier required by 0181 is not on the board
- Where: 0181 §31 ("Trước khi encode: MachineVerifier; Sau khi encode: EncodingVerifier") and §32 (round-trip decoder suggested). T024 is validated against GNU `as` tables at test time only. T025 has no verifier.
- Consequence if not fixed: illegal operand forms from isel or frame lowering surface as crashes in the produced exe, not as ICEs at the right seam.
- Proposed fix: add to T025 a debug and test-mode machine-IR verifier (operand-form legality, register classes, 16-byte frame alignment, shadow space) with negative unit tests. The decoder can wait.

### A2-13 [MINOR] [CONFIRMED] Optimised MIR is re-verified only "in debug"
- Where: T043 "verify after each in debug". 0263 §45 (verifier passes), ABOOT-70 (generated code is re-verified), T020 "Driver runs the verifier after MIR build in every mode".
- Problem: if CI and test builds are Release, -O1 output reaches LIR unverified, so optimizer bugs show up only as differential mismatches.
- Proposed fix: T043: verify-after-each-pass is on in every build used by tools/axtest.py and CI (a flag that defaults to on in tests). The verifier stays mandatory before LIR at every -O level.

## Checked and OK

- Stage-0 in C11, no LLVM (0263 §1-3, AXIOM-BOOT-001): R-rules, T004 and T024/T026 (GNU as/gcc used as test oracles only).
- No AST→machine code (0263 §24/§28/§50): T028 wires MIR→LIR→x64→COFF→PE; T019 is the only AST/HIR-side producer of MIR.
- No assembly text / no external assembler (0263 §30, ABOOT-74): T024 encodes bytes directly.
- Own linker, no CRT, startup separate from `main` (0263 §8-12, 0181 §15-16): T027 `axiom_start` is linker-generated.
- MIR has Place abstraction from day one (0263 §23): T018.
- MIR verifier mandatory (ABOOT-47): T020 runs it in every mode; T050 refuses unverified MIR.
- Interpreter as oracle, independent of backend and host C (0263 §25, 0262 §10, ABOOT-48/76): T021 comes before T023; T006 rule "interp never includes target".
- Differential interp vs native, -O0/-O1 (0263 §47, 0262 §47-48, ABOOT-77): T029, T043, T044, T062.
- Determinism and reproducible build check (0264 §27, ABOOT-73/79): T026, T027, T029, T087.
- Early fuzzing (0263 §48, 0262 §49): T013 (lexer/parser), T062 (generated programs, interp==native at -O0/-O1).
- Architecture drift checker (0263 §46, 0172 §24): T006.
- Diagnostics as data from Stage-0, JSON output, recovery (0263 §18-19, 0172 §10-12): T009, T011, T016. The code format AX_AREA_NAME (vs AX1301 in 0263 §33) is decided by T002.
- Kernel (0172 KERNEL-001..005): T007 and T008. KERNEL-006/007 (query engine, persistent cache) are deferred to E18.1, consistent with 0263 §49 and R7.
- Order syntax → semantics → MIR → native → ownership → capability → drop (0263 §41): P2 → P3 → P4 → P5 → P6 (T046 move, T047 init, T048 capability, T049 drop).
- Windows-first instead of 0263 §4 Linux-first: 0181 (the later revision, AX86TARGET-36) plus ROADMAP R6.
- Self-host subset (tasks/0260 §3): struct/enum/tuple/array/fn/generic/trait/impl/module/match/if/loop/while/for/let/closure/Result/Option/ownership/view/mut_view are all on the board (T030-T072). `var` is excluded by the syntax rule. Async/GPU/dyn/reflection are deferred, as §4 allows.
- Compiler data model without GC (ABOOT-49..57): T007 (C) and T073a (Axiom arenas and typed ID tables).
- Stage-1/2/3 ladder (tasks/0260 §41, 0262 §41-43): T086 → T087 (see A2-08 for the missing intermediate check).
- First-test set of 0263 §32-39: exit 42 in T028; negative test in T017; MIR test in T019; optimisation test in T043; ABI test in T029, which should move to T033 (A2-01); struct test in T035/T037; ownership test in T046; capability test in T048.

Step → task map (0263 §51):

| Ladder step | Board task(s) | Status |
|---|---|---|
| BOOT-00 Repository + Build | T004, T005, T006 (+T001-T003a specs) | OK |
| BOOT-01 Lexer | T010 | OK |
| BOOT-02 Parser | T011 (+T012) | OK, but too wide before VS0 (A2-02) |
| BOOT-03 Basic HIR | T014, T015 | OK (A2-02) |
| BOOT-04 Type Checking | T017 | OK |
| BOOT-05 Minimal MIR | T018, T019, T020 | OK (A2-03) |
| BOOT-06 MIR Interpreter | T021, gate T022 | OK |
| BOOT-07 x86-64 Machine IR | T023 (LIR), T025 | OK (A2-11, A2-12) |
| BOOT-08 Machine Encoder | T024 | OK |
| BOOT-09 Object Writer (COFF instead of ELF, R6) | T026 | OK |
| BOOT-10 Tiny Linker (PE) | T027 | OK |
| BOOT-11 Native Execution / VS#1 | T028, gate T029 | A2-01 |
| BOOT-12 Variables | T030 (partly in T017/T019) | OK |
| BOOT-13 CFG | T031, native T033 | OK |
| BOOT-14 Functions + ABI | T032, native T033 | OK |
| BOOT-15 Struct + Layout | T035, native T037 | OK |
| BOOT-16 Arrays | T036, native T037 | OK |
| BOOT-17 Enum + Match | T038, native T040 | A2-05 |
| BOOT-18 Result + Option | T039, native T040 | OK |
| (strings/print, not in ladder) | T041, T042 | extra, needed for tests |
| BOOT-19 Ownership | T045, T046, T047 | OK |
| BOOT-20 Capability/View | T048 | OK |
| BOOT-21 Drop | T049, T050, native T051, gate T052 | A2-04 |
| BOOT-22 Cleanup | T049 (cleanup on every edge incl. `?`) | OK |
| BOOT-23 Generic | T054, native T059 | OK |
| BOOT-24 Traits | T053, T055, T056 | OK |
| BOOT-25 Closures | T057, native T059 | OK |
| BOOT-26 Comptime | T061 (const items only), rest E14.1 | Deferred by R7 (A2-10) |
| BOOT-27 Optimization | T043 (-O1), rest T064/E15.4 | Earlier than the ladder, OK |
| BOOT-28 Register Allocation | T063 / E15.8 (post-T087) | Deferred by R7 (A2-09) |
| BOOT-29 Full Linker | T067 / E18.6, T066 (ELF) / E16.9 | Deferred by R6/R7; the minimal linker is enough for bootstrap |
| BOOT-30 AArch64 | P16 (T216) | Deferred by R6; tasks/0260 §44 agrees |
| (modules, FFI, unsafe, std — needed by the subset) | T060, T065, T061a, T069-T075, T073a | Needed for self-host, OK |
| BOOT-31 Frontend in Axiom | T076, T077, T078, T079, T080, T081 | OK |
| BOOT-32 MIR in Axiom | T082, T083 | OK |
| BOOT-33 Backend in Axiom | T084 | OK |
| BOOT-34 Object Writer in Axiom | T085 | OK |
| BOOT-35 Linker in Axiom | T085 | OK |
| BOOT-36 Stage-1 Self Compile | T086 | OK (A2-09 budget) |
| BOOT-37 Stage-2 Bootstrap | T087 | A2-08 |
| BOOT-38 Reproducible Bootstrap | T087 | A2-08 |

## Cross-lens notes
- T003a Notes say "runs alone, before the repository skeleton", but T004 `depends: []`. Either the note is wrong or the dependency is missing (process lens).
- There is a stray empty directory tree `_workspaces/tasks/todo/_workspaces/tasks/{todo,doing,done}` (mtime 2026-09-30 23:00). Probably taskctl was run from the wrong cwd. It should be removed and taskctl should resolve paths from the repo root (process lens).
- T021 recursion(fib) and T032 "recursion/mutual recursion" overlap, as do T017/T019 (let, if/while, calls) and T030-T032. The scope boundaries need sharpening (executability lens).
- T041 introduces `Str` as a (ptr,len) "view" type before the P6 capability model. This is harmless for static literals, but T048 must fold `Str` into view semantics (0263 §39: a view is not just pointer+length).
