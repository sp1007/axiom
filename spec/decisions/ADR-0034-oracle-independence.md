# ADR-0034 — Oracle independence before Stage-1

Status: accepted (2026-10-20, architect; owner-delegated decision)

## Tóm tắt
- Đợt kiểm toán 2026-10-19 cho thấy chỉ ~16% phép kiểm có kỳ vọng độc lập với compiler; ~72% là so
  bản port Axiom với chính đầu ra của axiom0, nên lỗi thiết kế của axiom0 được port thừa hưởng mà
  không test nào thấy. Đã tái hiện 4 lỗi thật: chia/lấy dư u64 sai ở native, nhân u64 tràn không
  bẫy, dịch usize ≥ 32 bit panic, `impl Drop` không chạy với struct chỉ có trường scalar/con trỏ.
  Kiến trúc sư còn phát hiện thêm: parser bỏ âm thầm phần còn lại của dòng khi thiếu dấu kết thúc
  câu lệnh, và 37 manifest gọi cứng `{build}/axiom0` thay vì `{compiler}`.
- Quyết định: (1) cổng T086/T087 phải có "tập con độc lập" (kỳ vọng từ spec, Python, GNU as/objdump)
  chạy native bằng axiomc; đối chứng axiom0-vs-port chỉ là bằng chứng phụ. (2) Trước khi đóng băng
  (T087), mỗi task AX0-FIX sửa lỗi ngữ nghĩa phải sửa cả C lẫn bản port trong cùng task.
  (3)–(4) Định nghĩa tập con và thay oracle cross-link của T028 bằng kiểm objdump; link gcc/ld cho
  chương trình thật dời sang E18.7. (5) Sửa Drop trước T086 (không đợi T087). (6) Ký hiệu destructor
  dùng dạng dành riêng `<Type>$drop` nếu có va chạm tên. (7) Thiếu công cụ ngoài = FAIL, không SKIP.
  (8) Hai phát hiện MINOR (ABI qua DLL gcc, console UTF-8) được ghi rõ vào task lập kế hoạch P13/P21.
- Task mới: T140 (AX0-FIX-02), T141 (AX0-FIX-03), T142, T143, T144, T145, T146 (AX0-FIX-04); T134,
  T139, T086, T087 được sửa; T086 phụ thuộc thêm cả 7 task.

## Context
`_workspaces/audit/2026-10-19/oracle-independence.md` classified all 946 tests by the source of their
expected result. Findings OI-01..OI-14 (4 BLOCKER, 7 MAJOR, 3 MINOR). Category B (axiom0 vs. port,
determinism, `--emit=obj` equality, stage2 == stage3) cannot see a defect present in axiom0's design,
because the port copies that design (OI-04: `compiler/target/x64/frame.ax` uses `idiv` like
`isel.c`). At T086 the runner excludes `requires: axiom0-internal`, which removes most of the external
checks that exist (GNU-as table, PE loader driver, C units). Architect probes on 2026-10-20 added: the
parser never emits `AX_PARSE_EXPECTED_TERMINATOR` and silently drops the rest of a statement line
(`if c { return 5; } return 6;` → `return 6` gone), and 37 exec manifests run `{build}/axiom0`
regardless of `--compiler`.

The semantics involved are already specified, so no language rule changes:
unsigned `/ %` follow AXS-SEM-032 (mathematical truncation over the operand type), `*` overflow
AXS-SEM-030, shift range AXS-SEM-034 with N = bit width of the type (64 for isize/usize on x64,
REQ-TYP-035), Drop at every scope exit SPEC-12 AXS-DROP-001..003, terminators SPEC-02 AXS-GRM-011.

## Options
1. Rely on T134 + T139 (interp/native agreement) and stage2 == stage3. Rejected: shift width, Drop and
   the terminator bug are agreed by both executors and both compilers; agreement checks cannot see
   them by construction.
2. Fix the four bugs only. Rejected: the next design defect would again be invisible; the oracle gap
   is the root cause.
3. Fix the bugs and make a small set of independent oracles a hard part of the Stage-1/2 gates
   (chosen). Cost ≈ 5–7 task-sittings before T086; no new infrastructure beyond one runner directive.

For the port of each fix: (a) a separate port task after each axiom0 fix; (b) lockstep in the same
task (chosen, §2). For Drop: (a) before T087 as the audit proposed; (b) before T086 (chosen, §5).
For T028's cross-link oracle: (a) change the object model now so gcc/ld link real programs (2–3 days,
touches the obj model and the port); (b) objdump structural validation now, real cross-linking with
the import-library work of E18.7 (chosen, §4).

## Decision
1. **Oracle categories.** Evidence is ranked: A-ext (GNU as/objdump/gcc/ld, Python reference, Windows
   loader) and A (expected value derived by hand from a cited spec rule) prove correctness; B
   (compiler vs. compiler, compiler vs. port, determinism, fixed point) and C (self-snapshot golden)
   only detect change. A gate that certifies a compiler (T086, T087, later phase gates) needs A/A-ext
   evidence for every semantic area it relies on, run against that compiler natively.
2. **Lockstep fix rule (until the T087 freeze).** An `AX0-FIX-<nn>` task that fixes a semantic defect
   in axiom0 fixes the same defect in the ported module under `compiler/` in the same task, and
   regenerates the selfhost bundles/goldens that change. Reason: the bundles compare the port with
   axiom0's output, so a one-sided fix leaves the suite red between two tasks, and a port that
   inherits the defect makes axiomc wrong. After the freeze, defects are fixed in `compiler/` (and in
   axiom0 only when it blocks building axiomc, as an `AX0-FIX` task).
3. **Independent subset for T086/T087.** With the compiler under test natively built:
   `tests/conformance/**`; `tests/run/numeric/**` incl. the Python integer table (T140);
   `tests/run/drop/**`, `tests/run/mangle/**` (T141); hash vectors from
   `tests/unit/kernel/hash_vectors.txt` against the real `compiler/kernel/hash.ax` and
   `std/core/hash.ax` (T134); `tests/link/objdump_validate.test` (T142); the Axiom twin of the GNU-as
   vectors (T143); `tests/ui/parse/terminator_*` (T146); every selfhost `bundles_current.test`
   (T144); `WEAK-NATIVE` 0 in `tests/run/{numeric,drop,ptr,native_*}` and `tests/std` (T139, T145).
   No subset test may be `requires: axiom0-internal` or interp-only (except "oracle-only check").
4. **COFF/PE oracle.** T026's objdump criterion and T028's "cross-link every native run test" are
   replaced, for the pre-self-host compiler, by T142's objdump structural validation of real
   executables and objects plus the existing gcc link of `--emit=obj`. Linking real programs with
   gcc/ld needs standard `__imp_` import references and a linkable runtime object; that belongs to
   E18.7 (T751, import libraries) and is recorded there.
5. **Order.** T134 → T140 → T141 → T146 run alone (priority 0, shared paths); T142, T143 can run now in
   parallel with T085; T139 after T140; T144 and T145 after T146. T086 depends on all of them. Drop
   (T141) is fixed before T086 rather than before T087: Stage-1 must measure axiomc's real memory
   behaviour (ADR-0005 §7) on a std without the `_glue: DropGlue` workaround, and any later fix would
   force T086 to be re-run.
6. **Destructor symbols.** If T141's collision tests show that ADR-0032's `<Type>_drop` symbol can
   collide with a user item, destructor and drop-glue symbols use `<Type>$drop` (`$` is not an Axiom
   identifier character and is valid in COFF/GNU symbol names). This amends ADR-0032 only in that case.
7. **External tools are mandatory oracles.** A manifest whose expected result comes from an external
   tool (as, objdump, gcc, ld) FAILs when the tool is missing; no SKIP, no `skip-unless`. Exec
   manifests call `{compiler}`; `{build}/axiom0` only with `requires: axiom0-internal`.
8. **MINOR findings.** OI-14 (mangling collisions) is folded into T141. OI-12 (Windows ABI against a
   gcc-built DLL, `offsetof` table) is deferred to P13 planning (note in T213) because axiomc calls
   kernel32 with scalars/pointers only; the existing 7-argument and struct-by-value probes agree with
   Python. OI-13 (console output via WriteConsoleW) is deferred to P21 planning (note in T221); pipe
   bytes are already pinned by 8 tests in both modes.
9. **Stale binary.** `build/axiom0.exe` in the main tree is never evidence; skills `axiom-c-stage0` and
   `axiom-testing` say so, and every new or amended task says "build fresh in the snapshot".

## Consequences
- New tasks: T140 AX0-FIX-02 (integer semantics, axiom0 + port, Python table), T141 AX0-FIX-03 (Drop
  + std workaround removal + destructor-symbol collisions), T142 (objdump validation; `{compiler}` in
  37 manifests), T143 (GNU-as table widened + Axiom twin), T144 (selfhost bundle freshness), T145
  (native-evidence sweep), T146 AX0-FIX-04 (statement terminator, axiom0 + port + sweep).
- Amended: T134 (hash acceptance against Python vectors and the real module, native leg of
  `qa_hash_vectors.ax`), T139 (`stdout-file:` golden comparison for `tests/lir`/`tests/hir`; depends on
  T140), T086 (independent subset, WEAK-NATIVE 0, new dependencies), T087 (subset with axiomc2),
  T213/T221/T751 (carry-over notes).
- T086 starts later by roughly seven task-sittings; in exchange its PASS means axiomc1 is checked
  against oracles that do not share axiom0's design.
- Affected specs/tests: none of SPEC-02/03/12 changes; tests under `tests/run/numeric`,
  `tests/run/drop`, `tests/run/mangle`, `tests/link`, `tests/obj`, `tests/driver`, `tests/verify`,
  `tests/encode`, `tests/selfhost`, `tests/lir`, `tests/hir`, `tests/ui/parse`, `tests/std`.

## Sources
`_workspaces/audit/2026-10-19/oracle-independence.md` (OI-01..OI-14); SPEC-02 AXS-GRM-010/011;
SPEC-03 AXS-SEM-030..035; SPEC-12 AXS-DROP-001..003; ADR-0004 §1; ADR-0005 §1, §3, §7; ADR-0032;
tasks/0361 (testing invariants: REQ-TST-079 external compilers are not semantic oracles — here the
external tools check encodings, file formats and integer arithmetic only, not Axiom semantics);
tasks/0327, tasks/0334 (integer semantics); 0185 (COFF section flags).

## Revisit
Yes, partly: §5 (Drop before T086 rather than T087) and §6 (destructor symbol form) are judgement
calls the owner may want to review; the rest follows from the audit's confirmed reproductions.
