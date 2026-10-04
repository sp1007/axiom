#include <ctype.h>
#include <string.h>

#include "driver/driver.h"
#include "unit.h"

/* T004 QA boundary tests: invariants of the generated command/emitter tables and of the shipped
 * commands (version, inspect, --features). They hold for every later task that adds a cmd_/emit_
 * file, so they catch a bad registration at the first build. */

static int is_cli_name(const char *s) {
    return s != NULL && s[0] != '\0';
}

AX_TEST(driver_registry_commands_wellformed) {
    int count = 0;
    for (const AxCommand *const *c = ax_commands; *c != NULL; ++c, ++count) {
        AX_CHECK(is_cli_name((*c)->name));
        AX_CHECK((*c)->summary != NULL && (*c)->summary[0] != '\0');
        AX_CHECK((*c)->run != NULL);
        /* main.c owns these spellings */
        AX_CHECK(strcmp((*c)->name, "help") != 0);
        AX_CHECK(strcmp((*c)->name, "--help") != 0);
        AX_CHECK(strcmp((*c)->name, "-h") != 0);
        for (const AxCommand *const *d = c + 1; *d != NULL; ++d) {
            AX_CHECK(strcmp((*c)->name, (*d)->name) != 0);
        }
        AX_CHECK(ax_find_command((*c)->name) == *c);
    }
    AX_CHECK(count >= 3);
    AX_CHECK(ax_find_command("version") != NULL);
    AX_CHECK(ax_find_command("inspect") != NULL);
    AX_CHECK(ax_find_command("--features") != NULL);
    AX_CHECK(ax_find_command("") == NULL);
    AX_CHECK(ax_find_command("Version") == NULL);
}

AX_TEST(driver_registry_emitters_wellformed) {
    for (const AxEmitter *const *e = ax_emitters; *e != NULL; ++e) {
        AX_CHECK(is_cli_name((*e)->name));
        AX_CHECK((*e)->summary != NULL);
        AX_CHECK((*e)->run != NULL);
        for (const char *p = (*e)->name; *p != '\0'; ++p) {
            AX_CHECK(islower((unsigned char)*p) || isdigit((unsigned char)*p) || *p == '_');
        }
        for (const AxEmitter *const *f = e + 1; *f != NULL; ++f) {
            AX_CHECK(strcmp((*e)->name, (*f)->name) != 0);
        }
        AX_CHECK(ax_find_emitter((*e)->name) == *e);
    }
    AX_CHECK(ax_find_emitter("") == NULL);
    AX_CHECK(ax_find_emitter("no_such_emitter") == NULL);
}

/* Run a command with both streams captured in memory-like temp files; returns the exit code. */
static int run_captured(const AxCommand *cmd, int argc, char **argv, char *out, size_t out_cap,
                        char *err, size_t err_cap) {
    FILE *fo = tmpfile();
    FILE *fe = tmpfile();
    AX_CHECK(fo != NULL && fe != NULL);
    if (fo == NULL || fe == NULL) {
        return -1;
    }
    AxIo io = {fo, fe};
    int rc = cmd->run(&io, argc, argv);
    rewind(fo);
    rewind(fe);
    size_t n = fread(out, 1, out_cap - 1, fo);
    out[n] = '\0';
    n = fread(err, 1, err_cap - 1, fe);
    err[n] = '\0';
    fclose(fo);
    fclose(fe);
    return rc;
}

AX_TEST(driver_version_output_is_one_lf_line) {
    char out[256], err[256];
    char *argv[] = {"version", NULL};
    const AxCommand *c = ax_find_command("version");
    AX_CHECK(c != NULL);
    if (c == NULL) {
        return;
    }
    AX_CHECK_EQ_INT(run_captured(c, 1, argv, out, sizeof out, err, sizeof err), AX_EXIT_OK);
    AX_CHECK(strncmp(out, "axiom0 ", 7) == 0);
    size_t len = strlen(out);
    AX_CHECK(len > 8 && out[len - 1] == '\n');
    AX_CHECK(strchr(out, '\r') == NULL);
    AX_CHECK(strchr(out, '\n') == out + len - 1); /* exactly one line */
    AX_CHECK_EQ_INT(strlen(err), 0);
}

AX_TEST(driver_commands_reject_extra_arguments) {
    char out[256], err[256];
    char *v[] = {"version", "extra", NULL};
    char *f[] = {"--features", "extra", NULL};
    AX_CHECK_EQ_INT(run_captured(ax_find_command("version"), 2, v, out, sizeof out, err, sizeof err),
                    AX_EXIT_USAGE);
    AX_CHECK_EQ_INT(strlen(out), 0);
    AX_CHECK(strstr(err, "extra") != NULL);
    AX_CHECK(strchr(err, '\r') == NULL);
    AX_CHECK_EQ_INT(
        run_captured(ax_find_command("--features"), 2, f, out, sizeof out, err, sizeof err),
        AX_EXIT_USAGE);
}

AX_TEST(driver_inspect_usage_errors) {
    char out[256], err[512];
    const AxCommand *c = ax_find_command("inspect");
    AX_CHECK(c != NULL);
    if (c == NULL) {
        return;
    }
    char *none[] = {"inspect", NULL};
    char *empty[] = {"inspect", "--emit=", NULL};
    char *unknown[] = {"inspect", "--emit=no_such_emitter_qa", "file.ax", NULL};
    AX_CHECK_EQ_INT(run_captured(c, 1, none, out, sizeof out, err, sizeof err), AX_EXIT_USAGE);
    AX_CHECK(strstr(err, "usage") != NULL);
    AX_CHECK_EQ_INT(run_captured(c, 2, empty, out, sizeof out, err, sizeof err), AX_EXIT_USAGE);
    AX_CHECK_EQ_INT(run_captured(c, 3, unknown, out, sizeof out, err, sizeof err), AX_EXIT_USAGE);
    AX_CHECK(strstr(err, "no_such_emitter_qa") != NULL);
    AX_CHECK_EQ_INT(strlen(out), 0);
    AX_CHECK(strchr(err, '\r') == NULL);
}

AX_TEST(driver_features_prints_one_capability_per_line) {
    char out[1024], err[256];
    char *argv[] = {"--features", NULL};
    AX_CHECK_EQ_INT(
        run_captured(ax_find_command("--features"), 1, argv, out, sizeof out, err, sizeof err),
        AX_EXIT_OK);
    /* every line is a non-empty lowercase word, LF terminated, no CR; the empty list is valid */
    AX_CHECK(strchr(out, '\r') == NULL);
    size_t len = strlen(out);
    AX_CHECK(len == 0 || out[len - 1] == '\n');
    AX_CHECK(strstr(out, "\n\n") == NULL);
    AX_CHECK(out[0] != '\n');
    AX_CHECK_EQ_INT(strlen(err), 0);
}
