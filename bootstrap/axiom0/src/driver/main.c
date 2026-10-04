#include <string.h>

#include "driver/driver.h"

/* axiom0 entry point. Contains no command logic: it only dispatches argv[1] through the
 * generated command registry (see driver.h). Never edited by later tasks.
 *
 * Exit codes: 0 ok, 1 diagnostics, 2 usage error, 3 internal compiler error (AX_EXIT_*). */

static void print_usage(FILE *to) {
    fputs("usage: axiom0 <command> [arguments]\n\ncommands:\n", to);
    for (const AxCommand *const *c = ax_commands; *c != NULL; ++c) {
        fprintf(to, "  %-12s %s\n", (*c)->name, (*c)->summary);
    }
    fputs("  help         print this text\n"
          "\n"
          "exit codes: 0 ok, 1 diagnostics reported, 2 usage error, 3 internal compiler error\n",
          to);
}

int main(int argc, char **argv) {
    ax_io_set_binary();
    AxIo io = {stdout, stderr};

    if (argc < 2) {
        print_usage(io.err);
        return AX_EXIT_USAGE;
    }
    const char *name = argv[1];
    if (strcmp(name, "help") == 0 || strcmp(name, "--help") == 0 || strcmp(name, "-h") == 0) {
        print_usage(io.out);
        return AX_EXIT_OK;
    }
    const AxCommand *cmd = ax_find_command(name);
    if (cmd == NULL) {
        fprintf(io.err, "axiom0: unknown command '%s'\n", name);
        print_usage(io.err);
        return AX_EXIT_USAGE;
    }
    int rc = cmd->run(&io, argc - 1, argv + 1);
    if (fflush(io.out) != 0 || fflush(io.err) != 0) {
        return rc == AX_EXIT_OK ? AX_EXIT_ICE : rc;
    }
    return rc;
}
