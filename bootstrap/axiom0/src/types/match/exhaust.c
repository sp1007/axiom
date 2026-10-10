#include "types/types.h"
#include "hir/hir.h"
#include <string.h>

void ax_match_check_exhaustiveness(AxThir *thir, StrInterner *str_in, const SourceDatabase *db, AxDiagSink *sink, const AxHirExpr *expr, TypeId val_ty) {
    if (expr->kind != AX_HIR_EXPR_MATCH) return;

    bool has_wildcard = false;
    for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
        if (arm->pat->kind == AX_HIR_PAT_WILDCARD || arm->pat->kind == AX_HIR_PAT_BINDING) {
            has_wildcard = true;
            break;
        }
    }
    
    if (has_wildcard) return;

    const AxType *t = ax_type_get(&thir->interner, val_ty);
    if (!t) return;
    
    if (t->kind == AX_TY_BOOL) {
        bool has_true = false;
        bool has_false = false;
        for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
            if (arm->pat->kind == AX_HIR_PAT_LITERAL) {
                if (arm->pat->literal.tok.kind == AX_TOK_KW_TRUE) has_true = true;
                if (arm->pat->literal.tok.kind == AX_TOK_KW_FALSE) has_false = true;
            }
        }
        if (has_true && has_false) return;
        AxDiagnostic d = {0};
        d.severity = AX_DIAG_ERROR;
        d.code = AX_PAT_NON_EXHAUSTIVE;
        d.message = ax_diag_code_default_message(AX_PAT_NON_EXHAUSTIVE);
        d.primary = expr->span;
        ax_diag_sink_report(sink, &d);
        return;
    }

    if (t->kind == AX_TY_ENUM) {
        size_t count = t->enm.variant_count;
        bool *seen = ax_arena_alloc(&thir->interner.arena, sizeof(bool) * count, _Alignof(bool));
        for (size_t i = 0; i < count; i++) seen[i] = false;

        for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
            StrView vname = {0};
            if (arm->pat->kind == AX_HIR_PAT_PATH) {
                StrView name = ax_source_db_span_text(db, arm->pat->path.path.span);
                vname = name;
                const char *dot = memchr(name.ptr, '.', name.len);
                if (dot) {
                    vname.ptr = dot + 1;
                    vname.len = name.len - (dot - name.ptr) - 1;
                }
            } else if (arm->pat->kind == AX_HIR_PAT_STRUCT) {
                StrView name = ax_source_db_span_text(db, arm->pat->struct_pat.path.span);
                vname = name;
                const char *dot = memchr(name.ptr, '.', name.len);
                if (dot) {
                    vname.ptr = dot + 1;
                    vname.len = name.len - (dot - name.ptr) - 1;
                }
            }

            if (vname.ptr) {
                size_t vidx = 0;
                for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                    StrView var_name = ax_interner_get(str_in, v->name);
                    if (ax_sv_eq(var_name, vname)) {
                        seen[vidx] = true;
                        break;
                    }
                    vidx++;
                }
            }
        }

        bool all = true;
        for (size_t i = 0; i < count; i++) {
            if (!seen[i]) all = false;
        }
        if (all) return;

        AxDiagnostic d = {0};
        d.severity = AX_DIAG_ERROR;
        d.code = AX_PAT_NON_EXHAUSTIVE;
        d.message = ax_diag_code_default_message(AX_PAT_NON_EXHAUSTIVE);
        d.primary = expr->span;
        ax_diag_sink_report(sink, &d);
        return;
    }

    AxDiagnostic d = {0};
    d.severity = AX_DIAG_ERROR;
    d.code = AX_PAT_NON_EXHAUSTIVE;
    d.message = ax_diag_code_default_message(AX_PAT_NON_EXHAUSTIVE);
    d.primary = expr->span;
    ax_diag_sink_report(sink, &d);
}
