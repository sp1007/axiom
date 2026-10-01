---
name: axiom-testing
description: Test architecture for the Axiom compiler — test file formats and directives (.ax run/ui/golden tests), the tools/axtest.py runner, compile-fail diagnostics tests, golden snapshots (tokens/AST/HIR/MIR), differential testing (MIR interpreter vs native -O0/-O1), encoder/object validation against GNU as/objdump, fuzzing, conformance and adversarial semantic suites, and QA boundary cross-checks. Use whenever writing or running compiler tests, adding a regression test for a bug, verifying a task's acceptance criteria, or doing QA on a finished task.
---

# Axiom compiler testing

Principle (docs 0152 §64, 0263 §47, 0145): every feature is proven at three levels —
**semantic** (MIR interpreter = oracle), **native** (compiled executable), **agreement** (both give
the same observable result). Tests are the spec made executable; a feature without tests does not
exist.

## Test kinds and layout

| Dir | Kind | What is checked |
|---|---|---|
| `tests/lex/` | golden | `x.ax` → `x.tokens` (from `inspect --emit=tokens`) |
| `tests/parse/` | golden | `x.ax` → `x.ast` |
| `tests/hir/`, `tests/mir/` | golden | lowered IR dumps (structure, not incidental numbering) |
| `tests/ui/` | compile-fail | expected diagnostic codes at expected lines, nothing else |
| `tests/run/` | run | exit code / stdout, **both** interpreter and native unless restricted |
| `tests/diff/` | differential | interp vs native -O0 vs native -O1 must agree |
| `tests/encode/` | exec + C driver | our instruction bytes == GNU `as` bytes for the same instruction |
| `tests/obj/`, `tests/link/` | exec + C driver | `objdump -x/-d` accepts our COFF/PE/ELF; layout/relocs correct |
| `tests/mc/` | golden + C driver | machine IR (`.mi`), encoded listing (`.mc`), frame/probe checks |
| `tests/modules/` | project | a directory with `axiom.toml` is one multi-file test |
| `tests/std/`, `tests/programs/` | run | library and real-program tests, both modes |
| `tests/perf/` | data | benchmark sources and committed baselines (`*.csv`) |
| `tests/conformance/` | spec suites | cases ported from 0017, 0022, 0026, 0114 (one dir per spec area) |
| `tests/fuzz/` | corpus | seeds for tools/fuzz.py; any crash/ICE/hang is a failure |
| `tests/unit/` | C unit tests | kernel data structures etc. (compiled into `axiom0-unit`, run by an `exec` manifest) |

Adding tests never requires editing shared files (ADR-0005 §2): the runner discovers `tests/**`, a
golden kind is derived from the sibling file extension (`x.tokens`, `x.ast`, `x.resolved`, `x.hir`,
`x.thir`, `x.mir`, `x.lir`, `x.mi`, `x.mc` ↔ `inspect --emit=<ext>`), C unit tests are globbed from
`tests/unit/**/*.c`, and C test drivers from `tests/**/cdriver_*.c` (run through `*.test` manifests of
kind `exec`). Only T005 edits `tools/axtest.py`; only T004 edits CMakeLists.txt. Binary fixtures live
under `tests/**/fixtures/` (everything else binary is git-ignored).

## Directives (first comment lines of an `.ax` file)

```axiom
// test: run                 # run | ui | golden | diff
// exit: 42                  # expected exit code (run/diff)
// stdout: Xin chào thế giới\n   # optional exact stdout, compared as UTF-8 bytes
// modes: interp native      # default for run: both; restrict only with a reason comment
// target: x86_64-windows    # optional; default host target
// flags: -O1                # extra compiler flags
fn main() -> i32 {
    return 42
}
```

More directives (all implemented by T005): `args: xin chào` (program arguments), `env: NAME=value`,
`stdin: text`, `stderr: text`, `timeout: 30` (seconds; default 10), `skip-unless: tool gcc`,
`requires: axiom0-internal` (test of the C implementation, excluded when the compiler under test is
axiomc), and the two below.

**`// native-after: T033`** — the test was written before the native backend supports its feature:
its native mode is SKIP until the named catch-up task removes the directive (ADR-0005 §1). Use it
for every run test added by an oracle-first task (the task text says which catch-up task to name);
the catch-up task must leave `grep -rn "native-after: <its id>" tests` empty. Never use
`modes: interp` for this purpose.

**`// xfail: T123 <reason>`** — an expected failure for a **spec gap that has an ADR** and an open
task (never for an implementation bug). It is reported XFAIL; if it passes it is XPASS, which counts
as a failure until the directive is removed.

**Native-only tests.** The MIR interpreter runs heap and OS code through the host intrinsics
(ADR-0002), so std and compiler-port tests run in both modes. The only accepted reasons for
`// modes: native` are "direct FFI is native-only (ADR-0002)" and a heavy test (≥ 100k elements) that
has a small interp twin. The only accepted reason for `// modes: interp` is "oracle-only check"
(out-of-bounds, dangling or misaligned raw-pointer access that only the oracle detects). QA fails
any other restriction.

Result states: PASS, FAIL, SKIP (always with a reason), XFAIL, XPASS, CRASH (compiler exit code 3 or
an unexpected access violation), TIMEOUT. XPASS, CRASH and TIMEOUT count as FAIL.

Compile-fail tests annotate the offending line inline:

```axiom
// test: ui
fn main() -> i32 {
    return true          //~ ERROR AX_TYPE_MISMATCH
}
```

`//~ ERROR CODE` = on this line; `//~^ ERROR CODE` = previous line; `//~ WARN CODE`. The runner
fails on missing **and** unexpected diagnostics. Match on codes, not message text, so wording can
improve without churn.

Golden files are updated only with `python tools/axtest.py --bless <filter>`, and a blessed diff
must be reviewed (read the diff, explain it in the report). Blind blessing hides regressions.

## Runner

```bash
python tools/axtest.py                    # everything
python tools/axtest.py --filter run/struct --verbose
python tools/axtest.py --json > _workspaces/artifacts/test-results.json   # for agents
python tools/axtest.py --bless parse/
```

The runner builds nothing: build first. The build that counts for a task is the one in its snapshot
(`taskctl.py snapshot <ID>` → `build-snap-<ID>/`, build directory `build-snap-<ID>/build`), so the
runner takes `--compiler <path>` (default `build/axiom0.exe`, env `AXIOM0`) and is run from inside
the snapshot for a verdict.
It runs the compiler and test programs as binary subprocesses and compares stdout/stderr as raw
bytes — never through text-mode decoding, which would hide CRLF/UTF-8 bugs.
It must print a final line
`TOTAL n PASS p FAIL f SKIP s XFAIL x` and exit non-zero on any failure. `--std-root std` is passed
to the compiler (ADR-0006 §8); `--exclude-requires axiom0-internal` is used once axiomc is the
compiler under test (T086 onwards).

## Gates (ADR-0005 §3, ROADMAP R9)

A gate task is PASS or BLOCKED, never "passes except for …". All tests pass; the only tolerated
non-passing tests are `xfail` entries for spec gaps with an ADR and a task. An implementation bug
found by a gate blocks it until the fix task (filed by the architect) is done. Every core gate also
runs `python tools/gatecheck.py` (from T022), `reqcov.py --strict` and `harness_check.py`. Fuzz
campaigns are defined by `--seed` and `--iterations`, never by wall time. Performance baselines are
committed under `tests/perf/*.csv` (`_workspaces/artifacts` is git-ignored).

## Writing good compiler tests

- **Canonical greeting is `Xin chào thế giới`, never "hello world"** (owner decision): every
  hello-style sample, smoke test, doc example and fixture prints it, so UTF-8 (2- and 3-byte
  sequences, combining-free precomposed Vietnamese) is exercised by default. stdout is compared as
  raw UTF-8 bytes (`Xin ch\xc3\xa0o th\xe1\xba\xbf gi\xe1\xbb\x9bi`).

- Files are LF-only (`.gitattributes`); when generating tests or golden files from Python on Windows
  use `open(path, "w", encoding="utf-8", newline="\n")` — the default writes CRLF and breaks
  byte-exact comparisons.

- Write test and golden files with the Write/Edit tools, never shell heredocs/`printf`/`echo -e`:
  the Windows shells here rewrite `\n`/`\r` escapes and backticks, producing tests that check the
  wrong bytes.

- One behaviour per test, named after it (`move_then_use.ax`, `shadow_space_5_args.ax`).
- Always pair a positive with a negative test for each rule (accepts valid, rejects invalid with the
  exact code).
- Exit codes are the cheapest oracle before stdout exists — compute a checksum into the exit code
  (keep it < 256) to observe many values.
- Boundary values: 0, 1, -1, INT_MIN/MAX per width, overflow edges, empty struct, 0-length array,
  >4 args (Windows register/stack boundary), 16-byte alignment at call sites, deep nesting.
- Regressions: every fixed bug gets a test named `bug_<short>.ax` reproducing it first.

## Encoder / object validation (doc 0184, 0185)

For an instruction form, assemble the reference with GNU as (Intel syntax) and compare bytes:

```bash
printf '.intel_syntax noprefix\nmov r9d, 42\n' > t.s && as --64 t.s -o t.o && objdump -d -M intel t.o
```

Generate tables of forms (all registers incl. r8–r15, all ModRM/SIB/disp8/disp32 cases, REX edge
cases like `spl/bpl/sil/dil`, `rbp`/`r13` base with no disp, `rsp`/`r12` base needing SIB) and
store them as `tests/encode/*.txt` expectations so the test suite does not need `as` at run time.
`objdump -x -d out.exe` must parse every object/image we write; check section flags, entry point,
import table, relocations.

**Cross-link oracle** (T026, T028): our `.obj` files are also linked by the system toolchain
(`gcc`/`ld`, MSYS2 ucrt64) and must behave exactly like our own PE output. This isolates COFF-writer
bugs from PE-linker bugs. It is a test oracle only; the production path never calls an external
linker. Tests SKIP when gcc is not on PATH.

## Differential testing

`tests/diff/` programs are compiled at every optimisation level and run under the interpreter;
all observable results (exit code, stdout) must match. When the optimizer lands, every `run` test
also runs at -O1 automatically. A mismatch is a bug in the optimizer, backend or interpreter —
never "fix" it by changing the expectation without finding which one is wrong.

## Fuzzing

`tools/fuzz.py` mutates `tests/fuzz/` seeds (byte flips, token splices, grammar-aware generation)
and runs `axiom0 check`; failure = crash, ICE, timeout (>5 s), or non-deterministic diagnostics
across two runs. Minimise and add any finding to `tests/ui/` or `tests/parse/` as a regression.
A campaign is a command with a fixed seed and iteration count (for example
`python tools/fuzz.py --seed 1 --iterations 200000`) that must end with 0 findings.

## QA boundary cross-checks (what QA looks for beyond "tests pass")

Most compiler bugs live at the seams between phases, where each side is "correct" alone:
- parser AST shape ↔ resolver/HIR lowering expectations (every AST node kind handled?)
- typeck results ↔ MIR builder (every typed expression lowered? types agree?)
- MIR ↔ verifier (verifier checks every instruction kind the builder can emit?)
- MIR ↔ interpreter ↔ LIR lowering (same semantics for overflow, division, shifts, casts)
- ABI lowering ↔ isel ↔ frame lowering (shadow space, alignment, callee-saved actually saved)
- encoder relocations ↔ object writer ↔ linker (offsets, addends, REL32 relative to next instr)
- diagnostics codes in code ↔ `diag/codes/<AREA>.def` ↔ tests referencing them
- oracle host intrinsics ↔ native `__ax_host_*` functions in `std/sys/windows` (same results in both
  modes for heap, files, args, env)
- std `HashMap` order and hash ↔ axiom0 `kernel/` (the port must produce byte-identical dumps)

QA reads both sides of a seam and writes a test that crosses it. Grep for `switch` over enum kinds
and check the default branches: an `AX_ICE` default hides unhandled kinds until a user hits them.
