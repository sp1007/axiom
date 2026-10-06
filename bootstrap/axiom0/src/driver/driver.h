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
#include <stdbool.h>

#include "source/source.h"
#include "diag/diag.h"
#include "lex/lex.h"
#include "syntax/parse.h"
#include "resolve/resolve.h"
#include "hir/hir.h"
#include "kernel/arena.h"
#include "kernel/str.h"
#include "kernel/interner.h"
#include "types/types.h"

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

// Options support
typedef enum AxOptionType {
    AX_OPT_BOOL,
    AX_OPT_STRING
} AxOptionType;

typedef struct AxOption {
    const char *name;
    AxOptionType type;
    void *dest;
    const char *help;
} AxOption;

// Helper: parse options from argv (stops at first positional arg or "--")
// Returns AX_EXIT_OK or AX_EXIT_USAGE.
// `out_argc`, `out_argv` will contain positional args (allocated with malloc, must be freed by caller).
// If `out_dash_dash` is not NULL, it is set to true if `--` was present.
int ax_options_parse(const AxIo *io, int argc, char **argv, const AxOption *const *tables, int *out_argc, char ***out_argv, bool *out_dash_dash);

extern const AxOption *const ax_all_options[];

// Options state globals
extern bool ax_opt_color_never;
extern bool ax_opt_time_passes;
extern bool ax_opt_json;
extern bool ax_opt_O0;
extern bool ax_opt_O1;
extern const char *ax_opt_target;
extern const char *ax_opt_build_o;
extern bool ax_opt_interp;

extern const AxOption ax_opts_pipeline[];
extern const AxOption ax_opts_build[];
extern const AxOption ax_opts_run[];

// Pipeline state
typedef enum AxStageId {
    AX_STAGE_SOURCE,
    AX_STAGE_LEX,
    AX_STAGE_PARSE,
    AX_STAGE_RESOLVE,
    AX_STAGE_HIR,
    AX_STAGE_TYPECK,
    AX_STAGE_INTERP,
    AX_STAGE_LIMIT
} AxStageId;

typedef struct AxDriverState {
    const AxIo *io;
    const char *main_file;
    bool failed;
    int exit_code;
    
    SourceDatabase db;
    AxDiagSink sink;
    StrInterner interner;
    AxArena parse_arena;
    AxArena resolve_arena;
    AxArena hir_arena;
    
    FileId file;
    StrView text;
    AxLexResult lex_res;
    AxParseResult parse_res;
    AxResolveMap resolve_map;
    AxHir hir;
    AxThir thir;
} AxDriverState;

typedef void (*AxStageRunFn)(AxDriverState *st);

typedef struct AxStage {
    AxStageId id;
    const char *name;
    const char *feature_name;
    AxStageRunFn run;
} AxStage;

extern const AxStage ax_pipeline_stages[];

// Initialize pipeline context (allocates inner arenas)
void ax_pipeline_init(AxDriverState *st, const AxIo *io);

// Run the pipeline up to (and including) stop_after stage.
// Handles --time-passes, stops early on errors.
// Renders diagnostics at the end (respecting --json, --color=never).
// Returns AX_EXIT_OK or AX_EXIT_DIAG (or AX_EXIT_ICE).
int ax_pipeline_run(AxDriverState *st, AxStageId stop_after);

// Free pipeline context
void ax_pipeline_free(AxDriverState *st);

#endif /* AX_DRIVER_DRIVER_H */
