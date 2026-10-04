Command-line driver (`axiom0 <command>`) and the pipeline stage list. Layer: top of the stack (may use every other module).

Registries (ADR-0005 section 2): add `cmd_<name>.c` (defines `const AxCommand axcmd_<name>`) for a command
or `emit_<name>.c` (defines `const AxEmitter axemit_<name>`) for an `inspect --emit=<name>` emitter. CMake
generates the tables at configure time; `main.c`, `driver.h` and `CMakeLists.txt` are never edited for this.
Exit codes: 0 ok, 1 diagnostics, 2 usage error, 3 internal compiler error (`AX_EXIT_*` in `driver.h`).
