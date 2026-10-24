#include "driver/driver.h"
#include "driver/mono.h"
#include "hir/lower.h"
#include "mir/drop/drop.h"
#include <string.h>
#include <stdlib.h>
#include <time.h>

// Globals
bool ax_opt_color_never = false;
bool ax_opt_time_passes = false;
bool ax_opt_json = false;
bool ax_opt_O0 = false;
bool ax_opt_O1 = false;
bool ax_opt_verify_each = false;
const char *ax_opt_target = NULL;
const char *ax_opt_build_o = NULL;
bool ax_opt_interp = false;
const char *ax_opt_std_root = NULL;

void ax_verify_mir_own(const AxMirBody *body, const AxThir *thir, AxDiagSink *sink, const AxHirItem *func);

const AxOption ax_opts_pipeline[] = {
    {"--color=never", AX_OPT_BOOL, &ax_opt_color_never, "disable colored diagnostics"},
    {"--time-passes", AX_OPT_BOOL, &ax_opt_time_passes, "print pass timing"},
    {"--json", AX_OPT_BOOL, &ax_opt_json, "emit diagnostics in JSON format"},
    {"-O0", AX_OPT_BOOL, &ax_opt_O0, "disable optimizations"},
    {"-O1", AX_OPT_BOOL, &ax_opt_O1, "enable optimizations"},
    {"--verify-each", AX_OPT_BOOL, &ax_opt_verify_each, "verify MIR after each pass"},
    {"--target", AX_OPT_STRING, &ax_opt_target, "target triple"},
    {"--std-root", AX_OPT_STRING, &ax_opt_std_root, "path to std library root"},
    {NULL, 0, NULL, NULL}
};

const char *ax_opt_emit = NULL;
const char *ax_opt_stack_reserve = "1048576";

const AxOption ax_opts_build[] = {
    {"-o", AX_OPT_STRING, &ax_opt_build_o, "output file"},
    {"--emit", AX_OPT_STRING, &ax_opt_emit, "emit type (obj)"},
    {"--stack-reserve", AX_OPT_STRING, &ax_opt_stack_reserve, "stack reserve size"},
    {NULL, 0, NULL, NULL}
};

const char *ax_opt_step_limit = "50000000";
const char *ax_opt_max_call_depth = "100000";

const AxOption ax_opts_run[] = {
    {"--interp", AX_OPT_BOOL, &ax_opt_interp, "force interpreter"},
    {"--step-limit", AX_OPT_STRING, &ax_opt_step_limit, "MIR step limit"},
    {"--max-call-depth", AX_OPT_STRING, &ax_opt_max_call_depth, "Call depth limit"},
    {NULL, 0, NULL, NULL}
};

const AxOption *const ax_all_options[] = {
    ax_opts_pipeline,
    ax_opts_build,
    ax_opts_run,
    NULL
};

static int s_run_argc = 0;
static const char *s_run_argv[256];

int ax_options_parse(const AxIo *io, int argc, char **argv, const AxOption *const *tables, int *out_argc, char ***out_argv, bool *out_dash_dash) {
    char **pos = malloc(((size_t)argc + 1) * sizeof(char *));
    if (!pos) {
        fputs("axiom0: out of memory\n", io->err);
        return AX_EXIT_ICE;
    }
    int pos_c = 0;
    bool dash_dash = false;
    s_run_argc = 0;
    
    for (int i = 0; i < argc; ++i) {
        if (!dash_dash && strcmp(argv[i], "--") == 0) {
            dash_dash = true;
            s_run_argc = 0;
            for (int j = i + 1; j < argc && s_run_argc < 256; j++) {
                s_run_argv[s_run_argc++] = argv[j];
            }
            continue;
        }
        if (!dash_dash && argv[i][0] == '-') {
            bool found = false;
            const char *arg = argv[i];
            const char *eq = strchr(arg, '=');
            size_t name_len = eq ? (size_t)(eq - arg) : strlen(arg);

            for (const AxOption *const *t = tables; *t != NULL; ++t) {
                for (const AxOption *o = *t; o->name != NULL; ++o) {
                    if (strncmp(arg, o->name, name_len) == 0 && strlen(o->name) == name_len) {
                        found = true;
                        if (o->type == AX_OPT_BOOL) {
                            if (eq) {
                                fprintf(io->err, "axiom0: option '%s' does not take an argument\n", o->name);
                                free(pos);
                                return AX_EXIT_USAGE;
                            }
                            *(bool *)o->dest = true;
                        } else if (o->type == AX_OPT_STRING) {
                            if (eq) {
                                *(const char **)o->dest = eq + 1;
                            } else {
                                if (i + 1 >= argc) {
                                    fprintf(io->err, "axiom0: option '%s' requires an argument\n", o->name);
                                    free(pos);
                                    return AX_EXIT_USAGE;
                                }
                                *(const char **)o->dest = argv[++i];
                            }
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
    size_t len = strlen(st->main_file);
    if (len > 4 && strcmp(st->main_file + len - 4, ".mir") == 0) {
        st->file = ax_source_db_load(&st->db, ax_sv_cstr(st->main_file));
        if (st->file.v == 0) {
            report_error(&st->sink, AX_IO_FILE_NOT_FOUND);
            st->failed = true;
            return;
        }
        st->text = ax_source_db_text(&st->db, st->file);
        return;
    }

    if (!ax_project_discover(st->main_file, ax_opt_std_root, &st->project, &st->sink)) {
        st->failed = true;
        return;
    }

    if (st->project.std_root) {
        bool uses_host = false;
        for (size_t i = 0; i < st->project.file_count; i++) {
            if (!st->project.files[i].is_std) {
                FILE *f = fopen(st->project.files[i].disk_path, "rb");
                if (f) {
                    fseek(f, 0, SEEK_END);
                    long sz = ftell(f);
                    fseek(f, 0, SEEK_SET);
                    if (sz > 0) {
                        char *buf = malloc(sz + 1);
                        if (buf) {
                            size_t rd = fread(buf, 1, sz, f);
                            buf[rd] = '\0';
                            if (strstr(buf, "host")) {
                                uses_host = true;
                            }
                            free(buf);
                        }
                    }
                    fclose(f);
                }
            }
            if (uses_host) break;
        }

        if (uses_host) {
            char disk[sizeof(((AxProjectFile*)0)->disk_path)];
            snprintf(disk, sizeof(disk), "%s/core/host.ax", st->project.std_root);
            for (char *p = disk; *p; p++) {
                if (*p == '\\') *p = '/';
            }
            FILE *hf = fopen(disk, "rb");
            if (hf) {
                fclose(hf);
                bool already = false;
                for (size_t i = 0; i < st->project.file_count; i++) {
                    if (strcmp(st->project.files[i].disk_path, disk) == 0) {
                        already = true;
                        break;
                    }
                }
                if (!already) {
                    if (st->project.file_count >= st->project.file_cap) {
                        st->project.file_cap = st->project.file_cap == 0 ? 8 : st->project.file_cap * 2;
                        st->project.files = realloc(st->project.files, st->project.file_cap * sizeof(AxProjectFile));
                    }
                    AxProjectFile *pf = &st->project.files[st->project.file_count++];
                    memcpy(pf->disk_path, disk, sizeof(pf->disk_path));
                    snprintf(pf->display_path, sizeof(pf->display_path), "<std>/core/host.ax");
                    snprintf(pf->module_path, sizeof(pf->module_path), "std.core.host");
                    pf->is_main = false;
                    pf->is_std = true;
                }
            }
        }
    }

    if (st->project.file_count == 0) {
        report_error(&st->sink, AX_IO_FILE_NOT_FOUND);
        st->failed = true;
        return;
    }

    for (size_t i = 0; i < st->project.file_count; i++) {
        AxProjectFile *f = &st->project.files[i];
        f->fid = ax_source_db_load_as(&st->db, ax_sv_cstr(f->disk_path), ax_sv_cstr(f->display_path));
        if (f->fid.v == 0) {
            report_error(&st->sink, AX_IO_FILE_NOT_FOUND);
            st->failed = true;
            return;
        }
        if (f->is_main) {
            st->file = f->fid;
            st->text = ax_source_db_text(&st->db, f->fid);
        }
    }

    if (st->file.v == 0) {
        for (size_t i = 0; i < st->project.file_count; i++) {
            if (!st->project.files[i].is_std) {
                st->file = st->project.files[i].fid;
                st->text = ax_source_db_text(&st->db, st->file);
                break;
            }
        }
        if (st->file.v == 0 && st->project.file_count > 0) {
            st->file = st->project.files[0].fid;
            st->text = ax_source_db_text(&st->db, st->file);
        }
    }
}

#include "mir/mir.h"
#include "verify/verify.h"
#include "own/own.h"

static void stage_lex(AxDriverState *st) {
    if (st->file.v != 0) {
        st->lex_res = ax_lex(st->file, st->text, &st->sink, &st->interner);
    }
}

static void stage_parse(AxDriverState *st) {
    if (st->project.file_count == 0) {
        st->parse_res = ax_parse(&st->parse_arena, st->lex_res.tokens, st->lex_res.token_count, &st->sink, &st->interner);
        return;
    }

    AxAstItem *first_item = NULL;
    AxAstItem *last_item = NULL;

    for (size_t i = 0; i < st->project.file_count; i++) {
        AxProjectFile *f = &st->project.files[i];
        FileId fid = f->fid;
        StrView txt = ax_source_db_text(&st->db, fid);
        if (txt.ptr == NULL) continue;

        AxLexResult l;
        bool need_free_lex = false;
        if (fid.v == st->file.v && st->lex_res.tokens != NULL) {
            l = st->lex_res;
        } else {
            l = ax_lex(fid, txt, &st->sink, &st->interner);
            need_free_lex = true;
        }

        AxParseResult p = ax_parse(&st->parse_arena, l.tokens, l.token_count, &st->sink, &st->interner);
        if (need_free_lex) {
            ax_lex_result_free(&l);
        }

        /* If this is a package file without an explicit leading module declaration,
         * synthesize an AX_ITEM_MODULE node. */
        if (st->project.is_package && f->module_path[0] != '\0') {
            if (p.ast.items == NULL || p.ast.items->kind != AX_ITEM_MODULE) {
                size_t seg_count = 1;
                for (const char *c = f->module_path; *c; c++) {
                    if (*c == '.') seg_count++;
                }

                StrId *segs = ax_arena_alloc(&st->parse_arena, seg_count * sizeof(StrId), _Alignof(StrId));
                char seg_buf[256];
                const char *cur = f->module_path;
                for (size_t s = 0; s < seg_count; s++) {
                    const char *dot = strchr(cur, '.');
                    size_t slen = dot ? (size_t)(dot - cur) : strlen(cur);
                    if (slen >= sizeof(seg_buf)) slen = sizeof(seg_buf) - 1;
                    memcpy(seg_buf, cur, slen);
                    seg_buf[slen] = '\0';
                    segs[s] = ax_intern_cstr(&st->interner, seg_buf);
                    cur = dot ? dot + 1 : "";
                }

                AxAstItem *synth_mod = ax_arena_alloc(&st->parse_arena, sizeof(AxAstItem), _Alignof(AxAstItem));
                memset(synth_mod, 0, sizeof(AxAstItem));
                synth_mod->kind = AX_ITEM_MODULE;
                synth_mod->vis.kind = AX_VIS_PUB;
                synth_mod->module.path.segments = segs;
                synth_mod->module.path.count = seg_count;
                synth_mod->next = p.ast.items;
                p.ast.items = synth_mod;
            }
        }

        /* Append p.ast.items to overall item chain */
        if (p.ast.items != NULL) {
            if (!first_item) {
                first_item = p.ast.items;
                last_item = p.ast.items;
            } else {
                last_item->next = p.ast.items;
            }
            while (last_item && last_item->next) {
                last_item = last_item->next;
            }
        }
    }

    st->parse_res.ast.items = first_item;
}

static void stage_resolve(AxDriverState *st) {
    st->resolve_map = ax_resolve(&st->parse_res.ast, &st->resolve_arena, &st->sink, &st->interner);
}

static void stage_hir(AxDriverState *st) {
    st->hir = ax_lower_ast(&st->hir_arena, &st->parse_res.ast, &st->resolve_map, &st->sink);

    // BOOTSTRAP-SHORTCUT T087: Link impl members to the main AST item list to ensure they are typechecked.
    // This avoids memory leaks and bypasses the need for complex module resolution of methods for now.
    AxHirItem *tail = st->hir.items;
    if (tail) {
        while (tail->next) tail = tail->next;
        AxHirItem *orig_tail = tail;
        for (AxHirItem *it = st->hir.items; it && it != orig_tail->next; it = it->next) {
            if (it->kind == AX_HIR_ITEM_IMPL && it->impl.members) {
                // BOOTSTRAP-SHORTCUT T131: Mangle destructor names
                if (it->impl.trait_path && it->impl.self_type && it->impl.self_type->kind == AX_HIR_TYPE_PATH) {
                    /* T158 / AXS-DROP-008: the same predicate as typeck, drop elaboration and the port's
                     * hir_postprocess_items - the trait path resolves to the prelude lang item Drop. */
                    if (ax_hir_impl_is_lang_drop(it, &st->hir, &st->interner, &st->db)) {
                        StrView self_name = ax_source_db_span_text(&st->db, it->impl.self_type->path.path.span);
                        size_t less_idx = 0;
                        while (less_idx < self_name.len && self_name.ptr[less_idx] != '<') {
                            less_idx++;
                        }
                        self_name.len = less_idx;
                        char mangled[256];
                        snprintf(mangled, sizeof(mangled), "%.*s_drop", (int)self_name.len, self_name.ptr);
                        StrId mangled_id = ax_intern_cstr(&st->interner, mangled);
                        AxSymbolId mangled_sym = { mangled_id.v };
                        
                        for (AxHirItem *m = it->impl.members; m; m = m->next) {
                            if (m->kind == AX_HIR_ITEM_FN) {
                                StrView fname = ax_interner_get(&st->interner, m->fn.name);
                                if (fname.len == 4 && memcmp(fname.ptr, "drop", 4) == 0) {
                                    m->fn.name = mangled_id;
                                    m->fn.symbol = mangled_sym;
                                }
                            }
                        }
                    }
                }
                
                for (AxHirItem *m = it->impl.members; m; m = m->next) {
                    AxHirItem *copy = ax_arena_alloc(&st->hir_arena, sizeof(AxHirItem), _Alignof(AxHirItem));
                    *copy = *m;
                    copy->next = NULL;
                    tail->next = copy;
                    tail = copy;
                }
            } else if (it->kind == AX_HIR_ITEM_EXTERN_BLOCK && it->extern_block.members) {
                for (AxHirItem *m = it->extern_block.members; m; m = m->next) {
                    AxHirItem *copy = ax_arena_alloc(&st->hir_arena, sizeof(AxHirItem), _Alignof(AxHirItem));
                    *copy = *m;
                    copy->next = NULL;
                    tail->next = copy;
                    tail = copy;
                }
            }
        }
    }
}

#include "mir/build/build.h"
#include "mir/build/intrinsics.h"
#include "verify/verify.h"
#include "own/unsafe/unsafe.h"
#include "kernel/hashmap.h"
#include "../interp/interp.h"

typedef AxMirBody *AxMirBodyPtr;
AX_DEFINE_HASHMAP(AxMirMap, AxHirItemPtr, AxMirBodyPtr, ax_key_hash_ptr, ax_key_eq_ptr);

static AxMirMap g_mir_map = {0};
static AxArena g_mir_arena = {0};
static bool g_mir_initialized = false;

struct AxMirBody *ax_pipeline_get_mir(const struct AxHirItem *it) {
    AxMirBody **ptr = AxMirMap_get(&g_mir_map, (AxHirItemPtr)it);
    if (ptr) return *ptr;
    return NULL;
}

#include "opt/opt.h"

static void build_mir_for_item(AxDriverState *st, AxHirItem *it) {
    if (it->kind == AX_HIR_ITEM_FN && it->fn.body) {
        for (AxHirAttr *attr = it->attrs; attr; attr = attr->next) {
            StrView an = ax_interner_get(&st->interner, attr->name);
            if (ax_sv_eq_cstr(an, "intrinsic")) {
                /* T134: @intrinsic functions have placeholder bodies in source; calls are lowered by
                 * typeck (AX_INTR_BUILTIN), the MIR builder (AX_INTR_MIR_OP / AX_INTR_MIR_TERM), or LIR
                 * host-call renaming (AX_INTR_HOST), so no placeholder body is ever compiled. */
                StrView fn_name = ax_interner_get(&st->interner, it->fn.name);
                AxIntrinsicRef iref;
                if (ax_intrinsic_lookup(fn_name, &iref)) return;
            }
        }
        AxMirBody *body = ax_mir_build(it, &st->thir, &g_mir_arena);
        if (body) {
            ax_verify_mir(body, &st->thir, &st->sink, it);
            AxMirMap_insert(&g_mir_map, it, body);
        }
    }
}
/* ---- T134: the intrinsic table at the driver ------------------------------------------------------------------
 * typeck sits below the MIR layer and cannot read the table, so the driver (1) writes the encoded table reference
 * of every recognized `@intrinsic fn` into the attribute as one positional integer argument before typeck (low 32
 * bits = ax_intrinsic_encode, high 32 bits = builtin_ty for AX_INTR_BUILTIN), and (2) after typeck rejects every
 * `@intrinsic fn` that is not a table row with a matching signature (AX_TYPE_UNKNOWN_INTRINSIC), so a placeholder
 * body is never compiled or run in its place. */

static AxHirAttr *intrinsic_attr(AxDriverState *st, const AxHirItem *it) {
    for (AxHirAttr *at = it->attrs; at; at = at->next) {
        StrView an = ax_interner_get(&st->interner, at->name);
        if (ax_sv_eq_cstr(an, "intrinsic")) return at;
    }
    return NULL;
}

static void annotate_intrinsic_item(AxDriverState *st, AxHirItem *it) {
    if (it->kind != AX_HIR_ITEM_FN) return;
    AxHirAttr *at = intrinsic_attr(st, it);
    if (!at || at->args) return;
    AxIntrinsicRef ref;
    if (!ax_intrinsic_lookup(ax_interner_get(&st->interner, it->fn.name), &ref)) return;
    AxHirAttrArg *arg = ax_arena_alloc(&st->hir_arena, sizeof(AxHirAttrArg), _Alignof(AxHirAttrArg));
    AxHirExpr *lit = ax_arena_alloc(&st->hir_arena, sizeof(AxHirExpr), _Alignof(AxHirExpr));
    memset(arg, 0, sizeof(*arg));
    memset(lit, 0, sizeof(*lit));
    lit->kind = AX_HIR_EXPR_LITERAL;
    lit->span = at->span;
    lit->literal.kind = AX_TOK_INT;
    lit->literal.val.int_val.value = ((uint64_t)ref.desc->builtin_ty << 32) | (uint64_t)ax_intrinsic_encode(&ref);
    arg->span = at->span;
    arg->expr = lit;
    at->args = arg;
}

static void check_intrinsic_item(AxDriverState *st, const AxHirItem *it) {
    if (it->kind != AX_HIR_ITEM_FN || !intrinsic_attr(st, it)) return;
    size_t generic_count = 0;
    if (it->fn.generic_params) {
        for (const AxHirGenericParam *p = it->fn.generic_params->params; p; p = p->next) generic_count++;
    }
    AxIntrinsicRef ref;
    const TypeId *fty = AxItemTypeMap_get(&st->thir.item_types, it);
    bool ok = fty && ax_intrinsic_lookup(ax_interner_get(&st->interner, it->fn.name), &ref) &&
              ax_intrinsic_signature_ok(&ref, ax_type_get(&st->thir.interner, *fty), generic_count, &st->thir.interner);
    if (!ok) {
        AxDiagnostic d = {0};
        d.code = AX_TYPE_UNKNOWN_INTRINSIC;
        d.severity = AX_DIAG_ERROR;
        d.message = ax_diag_code_default_message(AX_TYPE_UNKNOWN_INTRINSIC);
        d.primary = it->span;
        ax_diag_sink_report(&st->sink, &d);
    }
}

static void for_each_fn_item(AxDriverState *st, void (*fn)(AxDriverState *, AxHirItem *)) {
    for (AxHirItem *it = st->hir.items; it; it = it->next) {
        fn(st, it);
        if (it->kind == AX_HIR_ITEM_IMPL) {
            for (AxHirItem *m = it->impl.members; m; m = m->next) fn(st, m);
        } else if (it->kind == AX_HIR_ITEM_TRAIT) {
            for (AxHirItem *m = it->trait.members; m; m = m->next) fn(st, m);
        }
    }
}

static void check_intrinsic_item_cb(AxDriverState *st, AxHirItem *it) { check_intrinsic_item(st, it); }

static void stage_typeck(AxDriverState *st) {
    if (st->sink.errors > 0) return;
    extern void ax_traits_check_overlap(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in);
    ax_traits_check_overlap(&st->hir, &st->sink, &st->interner);
    for_each_fn_item(st, annotate_intrinsic_item);
    AxConstEvaluator evaluator = ax_interp_create_const_evaluator(&st->hir, &st->interner, &st->resolve_map, &st->parse_res.ast, &st->sink);
    st->thir = ax_typeck_with_evaluator(&st->hir, &st->sink, &st->interner, &st->db, &evaluator);
    free(evaluator.ctx);
    if (st->sink.errors > 0) return;
    for_each_fn_item(st, check_intrinsic_item_cb);
    if (st->sink.errors > 0) return;

    ax_unsafe_check(&st->hir, &st->thir, &st->sink, &st->interner);
    if (st->sink.errors > 0) return;
    
    // Build and verify MIR
    if (!g_mir_initialized) {
        ax_arena_init(&g_mir_arena, 0);
        AxMirMap_init(&g_mir_map);
        g_mir_initialized = true;
    }
    
    for (AxHirItem *it = st->hir.items; it; it = it->next) {
        build_mir_for_item(st, it);
        if (it->kind == AX_HIR_ITEM_IMPL) {
            for (AxHirItem *m = it->impl.members; m; m = m->next) {
                build_mir_for_item(st, m);
            }
        } else if (it->kind == AX_HIR_ITEM_TRAIT) {
            for (AxHirItem *m = it->trait.members; m; m = m->next) {
                build_mir_for_item(st, m);
            }
        }
    }
}

#include "own/own.h"

static void stage_own(AxDriverState *st) {
    if (st->sink.errors > 0 || !g_mir_initialized) return;

    uint32_t cur = 0;
    AxMirMapEntry *e;
    while (AxMirMap_next(&g_mir_map, &cur, &e)) {
        const AxHirItem *it = e->key;
        AxMirBody *body = e->value;
        for (uint32_t i = 0; i < body->local_count; i++) {
            // Exercise the copy classification for coverage
            ax_type_is_copy(body->locals[i].ty, &st->thir, &st->interner);
        }
        ax_own_check(it, body, &st->thir, &st->sink, &st->interner);
        if (st->sink.errors == 0) {
            ax_verify_mir_own(body, &st->thir, &st->sink, it);
        }
        ax_mir_drop_elaborate(body, &st->thir, &st->hir, &st->db, &st->sink, &st->interner);
        /* T141: -O1 runs on drop-elaborated MIR (as in the port, compiler/driver/pipeline.ax), so an
         * optimisation can never remove or reorder a drop (SPEC-03 AXS-SEM-003) and both compilers
         * optimise the same MIR (ADR-0034 §2 parity). */
        if (st->sink.errors == 0 && ax_opt_O1) {
            ax_opt_run(body, &st->thir, &st->sink, it, ax_opt_verify_each);
        }
    }
}

static void stage_run(AxDriverState *st) {
    if (st->sink.errors > 0) return;
    
    AxHirItem *main_fn = NULL;
    for (AxHirItem *it = st->hir.items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN) {
            StrView name = ax_interner_get(&st->interner, it->fn.name);
            if (name.len == 4 && memcmp(name.ptr, "main", 4) == 0) {
                main_fn = it;
                break;
            }
        }
    }
    
    if (!main_fn) {
        report_error(&st->sink, AX_TYPE_MAIN_MISSING);
        return;
    }
    
    TypeId *ret_ty_ptr = AxItemTypeMap_get(&st->thir.item_types, main_fn);
    TypeId main_ty_id = ret_ty_ptr ? *ret_ty_ptr : st->thir.interner.t_error;
    
    if (main_ty_id.v == 0) {
        AX_ICE("driver: main has unresolved type (0) after typeck");
    }
    
    const AxType *main_ty = ax_type_get(&st->thir.interner, main_ty_id);
    
    /* AXS-SEM-080: the signature is a type rule checked by typeck (reported by `check` as well);
     * reaching here with a non-fn type would be an internal error. */
    if (!main_ty || main_ty->kind != AX_TY_FN) {
        AX_ICE("driver: main has no fn type after a successful typeck");
    }
    
    int step_limit = atoi(ax_opt_step_limit);
    int call_depth_limit = atoi(ax_opt_max_call_depth);
    
    const char *full_argv[257];
    int full_argc = 0;
    full_argv[full_argc++] = st->main_file ? st->main_file : "axiom0";
    for (int i = 0; i < s_run_argc && full_argc < 256; i++) {
        full_argv[full_argc++] = s_run_argv[i];
    }

    extern const char *ax_run_panic_msg;
    int rc = ax_interp_run(main_fn, &st->thir, &st->hir, &st->interner, &st->resolve_map, &st->parse_res.ast, &st->sink, step_limit, call_depth_limit, g_mir_initialized ? &g_mir_map : NULL, &ax_run_panic_msg, st->io->out, full_argc, full_argv);
    st->exit_code = rc;
}

extern void ax_stage_build_native(AxDriverState *st);
extern void ax_stage_mono(AxDriverState *st);

/* BOOTSTRAP-SHORTCUT (T134, follow-up: fix driver/mono.c, which is outside this task): mono.c reads the low 32 bits
 * of EVERY const callee as a function symbol, but the builtin callees that take a type argument (ptr_add, ptr_sub,
 * size_of, ...) carry a TypeId there. A TypeId equal to the symbol of some non-generic fn turned such a call into a
 * call of that fn: before T134 silently into the placeholder body of an intrinsic (`interner_get` computed
 * `strings + n` as `wrapping_add_u64(...)` = 0), now into an unresolved symbol. Move the TypeId into the high 32
 * bits and put a sentinel in the low 32 bits that neither resolve.c (1..) nor hir/lower.c (0x80000000..) uses. */
#define AX_MONO_TYPE_ARG_SENTINEL 0x7FFFFFFFull

static bool callee_carries_type_arg(const AxMirTerminator *term, const TypeInterner *in) {
    if (term->kind != AX_MIR_TERM_CALL || term->call.func.kind != AX_MIR_OP_CONST) return false;
    TypeId ty = term->call.func.constant.ty;
    if (ty.v == 0) return false;
    switch ((int)ax_type_get(in, ty)->kind) {
        case AX_TY_BUILTIN_PTR_ADD: case AX_TY_BUILTIN_PTR_SUB: case AX_TY_BUILTIN_SIZE_OF: case AX_TY_BUILTIN_ALIGN_OF:
        case AX_TY_BUILTIN_NEEDS_DROP: case AX_TY_BUILTIN_DROP_IN_PLACE: case AX_TY_BUILTIN_PTR_COPY:
        case AX_TY_BUILTIN_PTR_COPY_NONOVERLAPPING: case AX_TY_BUILTIN_PTR_WRITE_BYTES:
            return true;
        default:
            return false;
    }
}

static void tag_type_arg_callees(AxMirBody *body, const TypeInterner *in, bool tag) {
    for (size_t i = 0; i < body->bb_count; i++) {
        AxMirTerminator *term = &body->bbs[i].terminator;
        if (!callee_carries_type_arg(term, in)) continue;
        if (tag) {
            if ((term->call.func.constant.val & 0xFFFFFFFFull) != AX_MONO_TYPE_ARG_SENTINEL) {
                term->call.func.constant.val = (term->call.func.constant.val << 32) | AX_MONO_TYPE_ARG_SENTINEL;
            }
        } else {
            if ((term->call.func.constant.val & 0xFFFFFFFFull) == AX_MONO_TYPE_ARG_SENTINEL) {
                term->call.func.constant.val >>= 32;
            }
        }
    }
}

static void stage_mono_shielded(AxDriverState *st) {
    if (g_mir_initialized) {
        uint32_t cur = 0;
        AxMirMapEntry *e;
        while (AxMirMap_next(&g_mir_map, &cur, &e)) tag_type_arg_callees(e->value, &st->thir.interner, true);
    }
    ax_stage_mono(st);
    if (g_mir_initialized) {
        uint32_t cur = 0;
        AxMirMapEntry *e;
        while (AxMirMap_next(&g_mir_map, &cur, &e)) tag_type_arg_callees(e->value, &st->thir.interner, false);
    }
    for (const AxMonoInstance *inst = st->mono_instances; inst; inst = inst->next) {
        if (inst->body) tag_type_arg_callees(inst->body, &st->thir.interner, false);
    }
}

const AxStage ax_pipeline_stages[] = {
    {AX_STAGE_SOURCE, "source", NULL, stage_source},
    {AX_STAGE_LEX, "lex", "lex", stage_lex},
    {AX_STAGE_PARSE, "parse", "parse", stage_parse},
    {AX_STAGE_RESOLVE, "resolve", "resolve", stage_resolve},
    {AX_STAGE_HIR, "hir", "hir", stage_hir},
    {AX_STAGE_TYPECK, "typeck", "typeck", stage_typeck},
    {AX_STAGE_OWN, "own", "own", stage_own},
    {AX_STAGE_INTERP, "run", "interp", stage_run},
    {AX_STAGE_MONO, "mono", "mono", stage_mono_shielded},
    {AX_STAGE_LIMIT, "build", "native", ax_stage_build_native},
    {AX_STAGE_LIMIT + 1, "opt", "opt", stage_source},
    {AX_STAGE_LIMIT + 2, NULL, NULL, NULL}
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
    if (g_mir_initialized) {
        AxMirMap_free(&g_mir_map);
        ax_arena_destroy(&g_mir_arena);
        g_mir_initialized = false;
    }
    ax_thir_free(&st->thir);
    ax_arena_destroy(&st->hir_arena);
    ax_resolve_map_free(&st->resolve_map);
    ax_arena_destroy(&st->resolve_arena);
    ax_arena_destroy(&st->parse_arena);
    ax_lex_result_free(&st->lex_res);
    ax_interner_free(&st->interner);
    ax_diag_sink_free(&st->sink);
    ax_source_db_free(&st->db);
    ax_project_free(&st->project);
}

int ax_pipeline_run(AxDriverState *st, AxStageId stop_after) {
    size_t len = strlen(st->main_file);
    if (len > 4 && strcmp(st->main_file + len - 4, ".mir") == 0) {
        if (st->file.v == 0) {
            stage_source(st);
            if (st->failed) return AX_EXIT_DIAG;
        }

        AxArena temp_arena;
        ax_arena_init(&temp_arena, 0);
        
        ax_thir_init(&st->thir);
        
        AxMirBody *body = ax_mir_parse(st->text.ptr, &st->thir.interner, &temp_arena);
        if (body) {
            ax_verify_mir(body, &st->thir, &st->sink, NULL);
            if (st->sink.errors == 0) {
                ax_verify_mir_own(body, &st->thir, &st->sink, NULL);
            }
            if (st->sink.errors == 0 && ax_opt_O1) {
                ax_opt_run(body, &st->thir, &st->sink, NULL, ax_opt_verify_each);
            }
        } else {
            report_error(&st->sink, AX_VERIFY_MIR_SYNTAX);
        }
        ax_arena_destroy(&temp_arena);
        
        if (st->sink.errors > 0) {
            if (ax_opt_json) {
                ax_diag_render_json(&st->sink, &st->db, st->io->err);
            } else {
                ax_diag_render_human(&st->sink, &st->db, st->io->err);
            }
            return AX_EXIT_DIAG;
        }
        return AX_EXIT_OK;
    }

    int max_stage_idx = 0;
    while (ax_pipeline_stages[max_stage_idx].name != NULL) {
        max_stage_idx++;
    }

    if (stop_after == AX_STAGE_LIMIT) {
        if (ax_opt_interp) {
            stop_after = AX_STAGE_INTERP;
        }
    }

    // Find requested stage
    int target_idx = -1;
    if (stop_after == AX_STAGE_TYPECK) {
        stop_after = AX_STAGE_OWN;
    }
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
        
        if (ax_pipeline_stages[i].id == AX_STAGE_INTERP && stop_after != AX_STAGE_INTERP) {
            continue;
        }

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
    }
    
    if (st->exit_code != 0) {
        rc = st->exit_code;
    } else if (st->sink.errors > 0) {
        rc = AX_EXIT_DIAG;
    }
    
    return rc;
}
