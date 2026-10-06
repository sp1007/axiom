#include "driver/driver.h"
#include "hir/lower.h"
#include <string.h>
#include <stdlib.h>
#include <time.h>

// Globals
bool ax_opt_color_never = false;
bool ax_opt_time_passes = false;
bool ax_opt_json = false;
bool ax_opt_O0 = false;
bool ax_opt_O1 = false;
const char *ax_opt_target = NULL;
const char *ax_opt_build_o = NULL;
bool ax_opt_interp = false;

const AxOption ax_opts_pipeline[] = {
    {"--color=never", AX_OPT_BOOL, &ax_opt_color_never, "disable colored diagnostics"},
    {"--time-passes", AX_OPT_BOOL, &ax_opt_time_passes, "print pass timing"},
    {"--json", AX_OPT_BOOL, &ax_opt_json, "emit diagnostics in JSON format"},
    {"-O0", AX_OPT_BOOL, &ax_opt_O0, "disable optimizations"},
    {"-O1", AX_OPT_BOOL, &ax_opt_O1, "enable optimizations"},
    {"--target", AX_OPT_STRING, &ax_opt_target, "target triple"},
    {NULL, 0, NULL, NULL}
};

const AxOption ax_opts_build[] = {
    {"-o", AX_OPT_STRING, &ax_opt_build_o, "output file"},
    {NULL, 0, NULL, NULL}
};

const AxOption ax_opts_run[] = {
    {"--interp", AX_OPT_BOOL, &ax_opt_interp, "force interpreter"},
    {NULL, 0, NULL, NULL}
};

const AxOption *const ax_all_options[] = {
    ax_opts_pipeline,
    ax_opts_build,
    ax_opts_run,
    NULL
};

int ax_options_parse(const AxIo *io, int argc, char **argv, const AxOption *const *tables, int *out_argc, char ***out_argv, bool *out_dash_dash) {
    char **pos = malloc(((size_t)argc + 1) * sizeof(char *));
    if (!pos) {
        fputs("axiom0: out of memory\n", io->err);
        return AX_EXIT_ICE;
    }
    int pos_c = 0;
    bool dash_dash = false;
    
    for (int i = 0; i < argc; ++i) {
        if (!dash_dash && strcmp(argv[i], "--") == 0) {
            dash_dash = true;
            continue;
        }
        if (!dash_dash && argv[i][0] == '-') {
            bool found = false;
            for (const AxOption *const *t = tables; *t != NULL; ++t) {
                for (const AxOption *o = *t; o->name != NULL; ++o) {
                    if (strcmp(argv[i], o->name) == 0) {
                        found = true;
                        if (o->type == AX_OPT_BOOL) {
                            *(bool *)o->dest = true;
                        } else if (o->type == AX_OPT_STRING) {
                            if (i + 1 >= argc) {
                                fprintf(io->err, "axiom0: option '%s' requires an argument\n", o->name);
                                free(pos);
                                return AX_EXIT_USAGE;
                            }
                            *(const char **)o->dest = argv[++i];
                        }
                        break;
                    }
                }
                if (found) break;
            }
            if (!found) {
                fprintf(io->err, "axiom0: unknown option '%s'\n", argv[i]);
                free(pos);
                return AX_EXIT_USAGE;
            }
        } else {
            pos[pos_c++] = argv[i];
        }
    }
    
    pos[pos_c] = NULL;
    
    if (out_argc) *out_argc = pos_c;
    if (out_argv) *out_argv = pos;
    else free(pos);
    
    if (out_dash_dash) *out_dash_dash = dash_dash;
    
    return AX_EXIT_OK;
}

static void report_error(AxDiagSink *sink, AxDiagCode code) {
    AxDiagnostic d = {0};
    d.code = code;
    d.severity = AX_DIAG_ERROR;
    d.message = ax_diag_code_default_message(code);
    ax_diag_sink_report(sink, &d);
}

static void stage_source(AxDriverState *st) {
    st->file = ax_source_db_load(&st->db, ax_sv_cstr(st->main_file));
    if (st->file.v == 0) {
        report_error(&st->sink, AX_IO_FILE_NOT_FOUND);
        st->failed = true;
        return;
    }
    st->text = ax_source_db_text(&st->db, st->file);
}

#include "mir/mir.h"
#include "verify/verify.h"

static void stage_lex(AxDriverState *st) {
    size_t len = strlen(st->main_file);
    if (len > 4 && strcmp(st->main_file + len - 4, ".mir") == 0) {
        // Stop pipeline here for .mir files
        AxArena temp_arena;
        ax_arena_init(&temp_arena, 0);
        
        AxHirItem fake_func = {0};
        fake_func.kind = AX_HIR_ITEM_FN;
        
        const char *magic = strstr(st->text.ptr, "// expected_return_type: ");
        TypeId expected_ret = {0};
        bool has_fake_func = false;
        if (magic) {
            expected_ret.v = (uint32_t)atoi(magic + strlen("// expected_return_type: "));
            has_fake_func = true;
        }

        AxMirBody *body = ax_mir_parse(st->text.ptr, &st->thir.interner, &temp_arena);
        if (body) {
            if (has_fake_func) {
                AxType t = {0};
                t.kind = AX_TY_FN;
                t.fn.ret_type = expected_ret;
                TypeId t_id = ax_intern_type(&st->thir.interner, &t);
                AxItemTypeMap_insert(&st->thir.item_types, &fake_func, t_id);
                ax_verify_mir(body, &st->thir, &st->sink, &fake_func);
            } else {
                ax_verify_mir(body, &st->thir, &st->sink, NULL);
            }
        } else {
            report_error(&st->sink, AX_VERIFY_MIR_SYNTAX);
        }
        ax_arena_destroy(&temp_arena);
        
        // Prevent further stages from running
        st->failed = true;
        return;
    }
    st->lex_res = ax_lex(st->file, st->text, &st->sink, &st->interner);
}

static void stage_parse(AxDriverState *st) {
    st->parse_res = ax_parse(&st->parse_arena, st->lex_res.tokens, st->lex_res.token_count, &st->sink, &st->interner);
}

static void stage_resolve(AxDriverState *st) {
    st->resolve_map = ax_resolve(&st->parse_res.ast, &st->resolve_arena, &st->sink, &st->interner);
}

static void stage_hir(AxDriverState *st) {
    st->hir = ax_lower_ast(&st->hir_arena, &st->parse_res.ast, &st->resolve_map, &st->sink);
}

#include "mir/build/build.h"
#include "verify/verify.h"

static void stage_typeck(AxDriverState *st) {
    if (st->sink.errors > 0) return;
    st->thir = ax_typeck(&st->hir, &st->sink, &st->interner, &st->db);
    if (st->sink.errors > 0) return;
    
    // Build and verify MIR
    AxArena temp_arena;
    ax_arena_init(&temp_arena, 0);
    
    for (AxHirItem *it = st->hir.items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN) {
            AxMirBody *body = ax_mir_build(it, &st->thir, &temp_arena);
            if (body) {
                ax_verify_mir(body, &st->thir, &st->sink, it);
            }
        }
    }
    
    ax_arena_destroy(&temp_arena);
}

const AxStage ax_pipeline_stages[] = {
    {AX_STAGE_SOURCE, "source", NULL, stage_source},
    {AX_STAGE_LEX, "lex", "lex", stage_lex},
    {AX_STAGE_PARSE, "parse", "parse", stage_parse},
    {AX_STAGE_RESOLVE, "resolve", "resolve", stage_resolve},
    {AX_STAGE_HIR, "hir", "hir", stage_hir},
    {AX_STAGE_TYPECK, "typeck", "typeck", stage_typeck},
    {AX_STAGE_LIMIT, NULL, NULL, NULL}
};

void ax_pipeline_init(AxDriverState *st, const AxIo *io) {
    memset(st, 0, sizeof(*st));
    st->io = io;
    ax_source_db_init(&st->db);
    ax_diag_sink_init(&st->sink);
    ax_interner_init(&st->interner);
    ax_arena_init(&st->parse_arena, 0);
    ax_arena_init(&st->resolve_arena, 0);
    ax_arena_init(&st->hir_arena, 0);
    ax_resolve_map_init(&st->resolve_map);
    ax_thir_init(&st->thir);
}

void ax_pipeline_free(AxDriverState *st) {
    ax_thir_free(&st->thir);
    ax_arena_destroy(&st->hir_arena);
    ax_resolve_map_free(&st->resolve_map);
    ax_arena_destroy(&st->resolve_arena);
    ax_arena_destroy(&st->parse_arena);
    ax_lex_result_free(&st->lex_res);
    ax_interner_free(&st->interner);
    ax_diag_sink_free(&st->sink);
    ax_source_db_free(&st->db);
}

int ax_pipeline_run(AxDriverState *st, AxStageId stop_after) {
    int max_stage_idx = 0;
    while (ax_pipeline_stages[max_stage_idx].name != NULL) {
        max_stage_idx++;
    }

    // Find requested stage
    int target_idx = -1;
    for (int i = 0; i < max_stage_idx; ++i) {
        if (ax_pipeline_stages[i].id == stop_after) {
            target_idx = i;
            break;
        }
    }

    if (target_idx == -1) {
        // "stubs return 'not yet supported' diagnostics"
        report_error(&st->sink, AX_DRIVER_STAGE_NOT_AVAILABLE);
        target_idx = max_stage_idx - 1; // Just run what we have and then fail
    }

    for (int i = 0; i <= target_idx; ++i) {
        if (st->failed) break;
        
        clock_t start = 0;
        if (ax_opt_time_passes) start = clock();
        
        ax_pipeline_stages[i].run(st);
        
        if (ax_opt_time_passes) {
            clock_t end = clock();
            double seconds = (double)(end - start) / CLOCKS_PER_SEC;
            fprintf(st->io->out, "time: %-10s %.4fs\n", ax_pipeline_stages[i].name, seconds);
        }
    }
    
    if (target_idx == -1) {
        st->failed = true; // ensure we fail if the requested stage isn't there
    }

    int rc = AX_EXIT_OK;
    if (st->sink.errors > 0 || st->sink.warnings > 0) {
        if (ax_opt_json) {
            ax_diag_render_json(&st->sink, &st->db, st->io->err);
        } else {
            ax_diag_render_human(&st->sink, &st->db, st->io->err);
        }
        rc = st->sink.errors > 0 ? AX_EXIT_DIAG : AX_EXIT_OK;
    }
    return rc;
}
