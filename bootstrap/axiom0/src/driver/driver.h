#ifndef AX_DRIVER_DRIVER_H
#define AX_DRIVER_DRIVER_H

/* Public header of the driver module (layer: top of the stack, may use every other module).
 *
 * The driver is a pair of registries (ADR-0005 section 2):
 *   - src/driver/cmd_<name>.c   defines   const AxCommand axcmd_<name>
 *   - src/driver/emit_<name>.c  defines   const AxEmitter axemit_<name>
 * CMake globs those files at configure time and generates the NULL-terminated tables
 * `ax_commands` / `ax_emitters` (cmake/AxiomRegistry.cmake). A later task adds a file; it never
 * edits main.c, this header's tables or CMakeLists.txt. <name> is [a-z0-9_]+; the user-visible
 * name is the `name` field (so `cmd_features.c` can expose the command "--features").
 */

#include <stddef.h>
#include <stdio.h>

/* Process exit codes of `axiom0` (axiom-testing: exit code 3 is a CRASH for the runner). */
enum {
    AX_EXIT_OK = 0,    /* success */
    AX_EXIT_DIAG = 1,  /* the input produced error diagnostics (or a requested check failed) */
    AX_EXIT_USAGE = 2, /* bad command line: unknown command/option, missing argument */
    AX_EXIT_ICE = 3    /* internal compiler error */
};

/* Output streams are passed explicitly so commands stay testable and free of globals. */
typedef struct AxIo {
    FILE *out;
    FILE *err;
} AxIo;

/* argv[0] is the command (or emitter) name, like main(); argv[argc] == NULL. Returns an AX_EXIT_*. */
typedef int (*AxRunFn)(const AxIo *io, int argc, char **argv);

typedef struct AxCommand {
    const char *name;
    const char *summary; /* one line for the usage text */
    AxRunFn run;
} AxCommand;

typedef struct AxEmitter {
    const char *name;
    const char *summary;
    AxRunFn run; /* argv: "inspect" followed by the arguments except --emit=<name> */
} AxEmitter;

/* Generated tables, NULL-terminated, sorted by file name (deterministic). */
extern const AxCommand *const ax_commands[];
extern const AxEmitter *const ax_emitters[];

const AxCommand *ax_find_command(const char *name);
const AxEmitter *ax_find_emitter(const char *name);

/* Switch stdout/stderr to binary mode on Windows so that "\n" stays "\n" (axiom-c-stage0
 * "Byte-exact I/O"); a no-op elsewhere. Call once at program start. */
void ax_io_set_binary(void);

#endif /* AX_DRIVER_DRIVER_H */
