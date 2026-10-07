# tests/conformance/vs0 — VS0 / MS-P3 conformance on the oracle (T022)

Subset conformance for the milestone MS-P3 (VS0, V1, BOOT-04..06 of `spec/SPEC-00-bootstrap.md`):
the bootstrap subset is type-checked, lowered to verified MIR and run by the MIR interpreter with
the exact SPEC-03 semantics. Every program is in canonical syntax (axiom-syntax: `=` only, `.`
paths, no `;` needed). Only features introduced by MS-P3 are used (F-INT, F-ARITH, F-DIVREM,
F-BITS, F-CMP, F-LET, F-CF, F-CALL, F-MAIN, F-PANIC); no `let mut`, casts, aggregates or strings
(MS-P5).

Every run test carries `// native-after: <task>` naming the native catch-up task of the latest
feature it uses (SPEC-00 §4 "Native task"): `T028` (constants, `+ - *`, unary `-` on i32/i64,
locals, `return`, `main`), `T033` (branches, calls), `T037` (division, shifts, bitwise, other
widths). Panic tests also fix the exact stderr line `panic: <message>\n` (AXS-SEM-071; both
executors must write it, AXS-SEM-003).

## Sources

| Group | Files | Source |
|---|---|---|
| First-test set | `fp01_*`, `fp02_*`, `fp03_*`, `fp10_*` | SPEC-00 §5 FP-01, FP-02, FP-03 (executed; the MIR golden of FP-03 is `tests/mir/build/first_mir.ax`, T019), FP-10; 0263 §32-34 |
| SPEC-03 §10 cases owned by MS-P3 | `sem_t04_*` … `sem_t16_*` | SEM-T01 (= FP-01), T02 (= FP-10), T04-T09, T14 (without the cast), T15, T16. T03, T10-T13, T17, T18 need `as` or the bit intrinsics (F-CAST/F-WRAP, MS-P5 T034) and belong to `tests/conformance/p5` |
| Literals | `lit_*`, `float_unsupported` | AXS-SEM-010, 012, 020-022; SPEC-01 AXS-LEX-054 |
| Checked arithmetic | `arith_*` | AXS-SEM-030 at the MIN/MAX edges of i8..u64; 0017 §10 (`+` never changes behaviour with the build) |
| Division / remainder | `div_*`, `rem_*` | AXS-SEM-032 |
| Bitwise / shifts | `bits_*`, `shift_*`, `bool_bitwise_*` | AXS-SEM-033, 034 |
| Comparisons / short circuit | `cmp_*`, `short_circuit_*` | AXS-SEM-035, 036; AXS-GRM-051 |
| Evaluation order | `order_*` | AXS-SEM-040, 041 (observed through the panic message of the first failing operand) |
| let / control flow / calls | `let_*`, `cf_*`, `call_*` | F-LET, F-CF, F-CALL; AXS-SEM-014, 046 |
| main | `main_*`, `return_missing_value` | AXS-SEM-080, 081; AXS-GRM-040 |
| Phase seams | `seam_*` | parser precedence/associativity and header expressions ↔ MIR value; unary MIR ops ↔ oracle; typeck ↔ diagnostics (one diagnostic per error) |

## 0114 (E2E consistency test) applicability

None of the 23 programs of 0114 is inside the MS-P3 subset; each is ported by the milestone that
introduces its features: A hello world (F-STR, MS-P5), B struct + method (F-STRUCT/F-METHOD,
MS-P5/P7), C generic + trait (MS-P7), D-F views (MS-P6), G-H partial move / drop (MS-P6), I Result
+ `?` (MS-P5), J-16 async, spawn, channel, atomic (post-v1 epics, ROADMAP R7), 17 unsafe (MS-P7),
18 and 22 FFI / `@repr(C)` (MS-P8), 19-20 recursive types, handles (MS-P7/P9), 21 public API
(MS-P7), 23 GPU (post-v1). The only 0114/0017 statement that applies to MS-P3 is the arithmetic
rule of 0017 §10 (deterministic checked `+`), covered by `arith_*`.
