# Axiom

**Axiom** is a self-hosted systems programming language and ahead-of-time native compiler engineered from first principles with zero external runtime, assembler, or linker dependencies.

Originally bootstrapped from a minimal C11 seed (`bootstrap/axiom0/`, frozen after reaching the Phase 10 self-hosting fixed point), the compiler (`compiler/`, ~280k LOC of Axiom) and standard library (`std/`, ~29k LOC of Axiom) are written in Axiom itself and compile directly to native Windows x64 PE32+ executables (`.exe`), dynamic libraries (`.dll`), import/static libraries (`.lib`), relocatable COFF objects (`.obj`), and `.axlib`/`.axmod` module artifacts without invoking an external C compiler, assembler, or system linker.

---

## Key Highlights

- **Self-Hosted Fixed Point (`axiom0` → `axiomc1` → `axiomc2`)**: `bootstrap/axiom0` (C11) is permanently frozen at the Phase 10 bootstrap boundary (`SPEC-20`). All post-bootstrap language, optimizer, linker, stdlib, and tooling features live exclusively in `compiler/` and `std/`. During bootstrap verification, host C compilers and linkers are stripped from `PATH` to guarantee hermetic code generation.
- **Capability-Based Ownership & Safety**: Deterministic drop elaboration, move tracking, and explicit read/write view capabilities (`view<T>`, `mut_view<T>`) verified on Mid-level IR (`MIR`) prior to interpretation or native codegen (`SPEC-11`), paired with scoped `unsafe`, raw pointers, `@at(...)` fixed-address bindings, and `extern "C"` / `extern "system"` FFI.
- **Clean, Unambiguous Syntax**:
  - Variable binding and assignment use `=` exclusively (no `:=`, no `var`).
  - Module, type, enum, and member paths use `.` exclusively (no `::`).
- **Dual Execution Engines (Differential Parity)**: Every runnable program can execute in the deterministic `MIR` interpreter (`run --interp`) and as a standalone CRT-free native binary (`build` / `run` at `-O0` and `-O1`), continuously cross-checked byte-for-byte on exit codes, `stdout`, and `stderr`.
- **Direct Native Backend & Linker**: Target-independent Low-level IR (`LIR`), ABI lowering, Optimizer 2.0 (`OptIR`/SSA, `MemorySSA`, alias/escape analysis, SROA, inlining, devirtualization, loop optimizations/BCE, vectorization), linear-scan register allocation, machine-IR verification, a direct x86-64 machine-code encoder (cross-checked against GNU `as` across 10,000+ instruction vectors), COFF writer, and built-in PE32+ `.exe`/`.dll`/`.lib` linker.
- **Deterministic Byte-Exact Output**: `stdout` and `stderr` use binary mode on Windows (`\n` only, never `\r\n`), object/PE timestamps and checksums are zeroed (`SOURCE_DATE_EPOCH=0`), and Stage-1 vs Stage-2 outputs are byte-for-byte identical.

```axiom
module main

pub fn main() -> i32 {
    print("Xin chào thế giới\n");
    0
}
```

---

## Project Status & Roadmap

Canonical specifications (`SPEC-*`), Architecture Decision Records (`spec/decisions/ADR-*`), requirement traceability (`spec/requirements/`), and the binding phase graph live in [`spec/ROADMAP.md`](spec/ROADMAP.md).

| Phase | Milestone | Status |
|-------|-----------|--------|
| **P0–P9** | Kernel, lexer/parser, resolver/HIR, typechecker/traits/generics, ownership/capabilities/drop, MIR interpreter, x86-64 native backend, FFI, self-host `std` subset | **Completed** |
| **P10** | Self-hosting compiler port (`compiler/`) & Stage-1/Stage-2 fixed point (`T087`; `axiom0` frozen) | **Completed** |
| **P15** | Optimizer 2.0 (`OptIR`, `MemorySSA`, SROA, inlining/devirt, loop opts/BCE, vectorization, LTO/PGO) & linear-scan register allocation (`T315`) | **Completed** |
| **P18** | Compiler Architecture 2.0: query engine, incremental & parallel compilation, `.axlib`/`.axmod` containers, separate compilation, PE32+ `.dll` & `.lib` (`T318`) | **Completed** |
| **P19** | Developer Tooling: formatter (`fmt`), doc generator (`docgen`), LSP/VFS (`lsp`), refactoring engine (`refactor`), semantic query (`ai_query`), test runner (`T319`) | **Completed** |
| **P11–P14** | Concurrency & `async`/`await` (`P11`), 128-bit/IEEE-754 float/SIMD (`P12`), low-level/freestanding/security (`P13`), `comptime` 2.0/reflection/generators/`dyn` (`P14`) | **In Progress** |
| **P16–P17, P20** | Multi-target backends — Linux ELF, macOS Mach-O, Wasm, ARM64, RISC-V (`P16`), DWARF/PDB debugging (`P17`), build graph & package manager (`P20`) | **In Progress** |
| **P21–P23** | Standard library completion (`P21`), GPU & heterogeneous compute (`P22`), v1.0 conformance & release freeze (`P23`) | **Planned** |

---

## Repository Layout

| Directory | Contents |
|-----------|----------|
| `compiler/` | Self-hosted `axiomc` compiler written in Axiom (175 modules across `kernel/`, `source/`, `diag/`, `lex/`, `syntax/`, `resolve/`, `hir/`, `types/`, `traits/`, `own/`, `mir/`, `verify/`, `interp/`, `opt/`, `lir/`, `abi/`, `target/`, `backend/`, `obj/`, `link/`, `artifact/`, `query/`, `incremental/`, `parallel/`, `build/`, `pkg/`, `fmt/`, `docgen/`, `lsp/`, `refactor/`, `ai_query/`, `test_runner/`, `driver/`) |
| `std/` | Axiom standard library written entirely in Axiom (`core/`, `alloc/`, `collections/`, `text/`, `bytes/`, `io/`, `fs/`, `path/`, `env/`, `process/`, `time/`, `thread/`, `sync/`, `future/`, `async/`, `sys/`, `pkg/`, `vcs/`, `sdk/`, ...) |
| `bootstrap/axiom0/` | Frozen Stage-0 bootstrap compiler in C11 (`CMakeLists.txt`, `cmake/`, `src/<module>/`; ~37k LOC) |
| `spec/` | Normative language & compiler specifications (`SPEC-*.md`), ADRs (`spec/decisions/`), `ROADMAP.md`, and requirement catalogs (`spec/requirements/`) |
| `tests/` | 2,160+ test suites: `lex/`, `parse/`, `resolve/`, `hir/`, `typeck/`, `ui/`, `mir/`, `verify/`, `opt/`, `opt2/`, `lir/`, `mc/`, `encode/`, `obj/`, `link/`, `link2/`, `run/`, `diff/`, `std/`, `modules/`, `driver/`, `inspect/`, `conformance/`, `fuzz/`, `perf/`, `unit/`, and `selfhost/` |
| `tools/` | Build, bootstrap, test runner, dependency cache, architecture checker, requirement tracer, and gate scripts (Python 3 standard library only — zero external packages) |
| `docs/` | Original design & research corpus (read-only archive) |

---

## Compiler Pipeline

```text
.ax / axiom.toml
  └─► Lexer & Recursive-Descent Parser (compiler/lex, compiler/syntax)
  └─► Name Resolver & HIR Lowering (compiler/resolve, compiler/hir)
  └─► Type Checker, Trait Solver & Monomorphizer (compiler/types, compiler/traits)
  └─► MIR Builder, Async/Drop Elaboration, Capability/Move Checker & Verifier (compiler/mir, compiler/own, compiler/verify)
        ├─► Deterministic MIR Interpreter (`run --interp` / comptime; compiler/interp)
        └─► Optimizer 2.0 (`-O1` / `OptIR` / `MemorySSA`; compiler/opt)
              └─► LIR & Target ABI Lowering (compiler/lir, compiler/abi)
              └─► Machine IR, Linear-Scan Regalloc & Machine Verifier (compiler/backend)
              └─► Direct Machine-Code Encoder & Object Writer (compiler/obj)
              └─► Built-in PE32+ `.exe` / `.dll` / `.lib` & `.axlib` Linker (compiler/link, compiler/artifact)
```

---

## Building from Source

### Prerequisites
- **Python 3.10+** (standard library only; no `pip install` needed)
- **CMake 3.20+** and **Ninja**
- **Clang or GCC** (e.g. MSYS2 `ucrt64` on Windows) — required **only** to compile the C11 Stage-0 seed `axiom0` (and optional GNU `as`/`ld`/`objdump` differential oracle tests). Once `axiom0` is built, `axiomc` compiles itself and user programs with zero external toolchain dependencies.

### 1. Build the Self-Hosted Compiler (`axiomc`) — Recommended

`tools/build_axiomc.py` builds `axiom0` (if absent), strips external C compilers/linkers from `PATH`, compiles Stage-1 (`axiomc1.exe`) using `axiom0`, and compiles Stage-2 (`axiomc2.exe` / `axiomc.exe`) using `axiomc1`:

```powershell
python tools/build_axiomc.py --out build
build/axiomc2.exe version
```

Useful flags for `tools/build_axiomc.py`:
- `--stage 1` — build up to `axiomc1.exe` only (fast local iteration on `compiler/` changes)
- `--stage 2` — build through Stage-2 `axiomc2.exe` (default)
- `--force` — force a clean rebuild even when `build/axiomc2.exe` is newer than `compiler/**` and `std/**`

### 2. Build Stage-0 (`axiom0`) Only

```powershell
cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure
```

CMake options for `bootstrap/axiom0`: `-DCMAKE_BUILD_TYPE=Debug|Release`, `-DAX_WERROR=ON|OFF` (strict C11 `-Wall -Wextra -Wpedantic` by default), `-DAX_SANITIZE=ON` (ASan + UBSan where supported). Build directories (`build/`, `build-*/`) are git-ignored.

---

## CLI Usage

```powershell
# Type-check a single file or an `axiom.toml` package
build/axiomc2.exe check path/to/main.ax
build/axiomc2.exe check --json path/to/main.ax

# Compile a standalone native PE32+ executable (no external linker or CRT)
build/axiomc2.exe build -o app.exe path/to/main.ax
build/axiomc2.exe build -O1 -o app.exe path/to/main.ax

# Emit a relocatable COFF object (.obj) or PE32+ DLL + import library (.dll + .lib)
build/axiomc2.exe build --emit=obj -o mod.obj path/to/mod.ax
build/axiomc2.exe build --kind dll -o plugin.dll path/to/plugin.ax

# Compile and run (native by default, or via the MIR interpreter)
build/axiomc2.exe run path/to/main.ax
build/axiomc2.exe run --interp path/to/main.ax

# Inspect intermediate representations
# (<name>: tokens | ast | resolved | hir | thir | mir | mir-opt | optir | memssa | async-layout | lir | mi | mc | obj)
build/axiomc2.exe inspect --emit=mir path/to/main.ax
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Source/compile error diagnostics reported |
| `2` | CLI usage error (unknown command/flag or missing argument) |
| `3` | Internal compiler error (ICE) |
| `101` | Runtime panic in an executed Axiom program (`assert` / `panic`) |

---

## Testing & Verification

All test and verification tools live in `tools/` and use Python 3's standard library exclusively:

```powershell
# List all discovered tests (~2,160 test IDs across interp, native, and native-O1 modes)
python tools/axtest.py --list

# Run specific test groups against the Stage-2 self-hosted compiler (use -j 2 on 4-core/16 GB hosts)
python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 run/str ui/typeck diff/opt

# Enforce compiler module layer boundaries (acyclic dependency graph)
python tools/archcheck.py

# Verify all self-host single-file test bundles match live compiler/ sources
python tools/axtest.py --compiler build/axiomc2.exe --build-dir build -j 2 selfhost/bundles_current.test

# Verify stage-0 / stage-1 / stage-2 bootstrap & binary determinism parity
python tools/axtest.py --compiler build/axiomc2.exe --build-dir build -j 2 selfhost/stage1/stage1_bootstrap.test

# Check requirement traceability coverage against spec/requirements/CATALOG.md
python tools/reqcov.py
```

Key testing invariants:
- **Observable Native Evidence (`WEAK-NATIVE 0`)**: Native `run` tests must verify an observable outcome (exact `// stdout:`, `// stderr:`, `stdout-contains:`, non-zero `// exit:`, or `test: diff` agreement against `--interp`), never a bare exit-code `0` alone.
- **Content-Addressed Test Cache (`tools/axtest_cache.py`)**: Caches deterministic test outcomes keyed by `sha256(compiler)` and exact transitive source/fixture dependencies (`--no-cache` forces a cold run; `--gate` re-verifies a deterministic random sample fresh).
- **Binary Fixtures Policy**: Compiled artifacts (`*.exe`, `*.obj`, `*.dll`, `*.lib`, `*.pdb`) are git-ignored everywhere except under `tests/**/fixtures/` (marked `binary` in `.gitattributes`). All source, spec, and test files enforce LF (`\n`) line endings.
- **Full CI Script**: `powershell -File tools/ci.ps1` (Windows) or `bash tools/ci.sh` (POSIX).

---

## License

Licensed under the [Apache License, Version 2.0](LICENSE) (see also [`NOTICE`](NOTICE)).
