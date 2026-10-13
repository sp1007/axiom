
#include "types/types.h"
#include "hir/hir.h"
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct Interval {
    int64_t start;
    int64_t end;
} Interval;



static bool get_pat_interval(const AxHirPat *pat, Interval *out) {
    if (pat->kind == AX_HIR_PAT_LITERAL) {
        if (pat->literal.tok.kind == AX_TOK_INT || pat->literal.tok.kind == AX_TOK_CHAR) {
            int64_t val = pat->literal.tok.val.int_val.value;
            if (pat->literal.is_negated) val = -val;
            out->start = val; out->end = val;
            return true;
        }
    } else if (pat->kind == AX_HIR_PAT_RANGE) {
        Interval start_iv, end_iv;
        if (get_pat_interval(pat->range.start, &start_iv) && get_pat_interval(pat->range.end, &end_iv)) {
            out->start = start_iv.start;
            out->end = end_iv.start;
            if (!pat->range.is_inclusive) out->end -= 1;
            return true;
        }
    }
    return false;
}

void ax_match_check_exhaustiveness(AxThir *thir, StrInterner *str_in, const SourceDatabase *db, AxDiagSink *sink, const AxHirExpr *expr, TypeId val_ty) {
    if (expr->kind != AX_HIR_EXPR_MATCH) return;

    bool has_unconditional_wildcard = false;
    for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
        if (!arm->guard && (arm->pat->kind == AX_HIR_PAT_WILDCARD || arm->pat->kind == AX_HIR_PAT_BINDING)) {
            has_unconditional_wildcard = true;
            // any arms after this are unreachable
            for (const AxHirMatchArm *unreach = arm->next; unreach; unreach = unreach->next) {
                AxDiagnostic d = {0};
                d.severity = AX_DIAG_WARNING;
                d.code = AX_PAT_UNREACHABLE;
                d.message = ax_diag_code_default_message(AX_PAT_UNREACHABLE);
                d.primary = unreach->pat->span;
                ax_diag_sink_report(sink, &d);
            }
            break;
        }
    }

    const AxType *t = ax_type_get(&thir->interner, val_ty);
    if (!t) return;
    
    // Interval check for ints and chars
    if (t->kind == AX_TY_I8 || t->kind == AX_TY_I16 || t->kind == AX_TY_I32 || t->kind == AX_TY_I64 || t->kind == AX_TY_U8 || t->kind == AX_TY_U16 || t->kind == AX_TY_U32 || t->kind == AX_TY_U64 || t->kind == AX_TY_CHAR) {
        Interval covered[256];
        size_t cov_count = 0;
        
        for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
            Interval iv;
            if (get_pat_interval(arm->pat, &iv)) {
                // Check if iv is fully covered by 'covered'
                bool is_covered = false;
                for (size_t i = 0; i < cov_count; i++) {
                    if (iv.start >= covered[i].start && iv.end <= covered[i].end) {
                        is_covered = true;
                        break;
                    }
                }
                
                if (is_covered) {
                    AxDiagnostic d = {0};
                    d.severity = AX_DIAG_WARNING;
                    d.code = AX_PAT_UNREACHABLE;
                    d.message = ax_diag_code_default_message(AX_PAT_UNREACHABLE);
                    d.primary = arm->pat->span;
                    ax_diag_sink_report(sink, &d);
                } else if (!arm->guard && cov_count < 256) {
                    covered[cov_count++] = iv;
                }
            } else if (arm->pat->kind == AX_HIR_PAT_OR) {
                // simplified for OR
                for (const AxHirPat *p = arm->pat->or_pat.pats; p; p = p->next) {
                    if (get_pat_interval(p, &iv)) {
                        bool is_covered = false;
                        for (size_t i = 0; i < cov_count; i++) {
                            if (iv.start >= covered[i].start && iv.end <= covered[i].end) {
                                is_covered = true;
                                break;
                            }
                        }
                        if (is_covered) {
                            AxDiagnostic d = {0};
                            d.severity = AX_DIAG_WARNING;
                            d.code = AX_PAT_UNREACHABLE;
                            d.message = ax_diag_code_default_message(AX_PAT_UNREACHABLE);
                            d.primary = p->span;
                            ax_diag_sink_report(sink, &d);
                        } else if (!arm->guard && cov_count < 256) {
                            covered[cov_count++] = iv;
                        }
                    }
                }
            }
        }
        
        if (has_unconditional_wildcard) return;
        
        bool full_coverage = false;
        if (t->kind == AX_TY_U8) {
            bool vals[256] = {0};
            for (size_t i = 0; i < cov_count; i++) {
                int64_t start = covered[i].start < 0 ? 0 : covered[i].start;
                int64_t end = covered[i].end > 255 ? 255 : covered[i].end;
                for (int64_t v = start; v <= end; v++) {
                    vals[v] = true;
                }
            }
            full_coverage = true;
            for (int v = 0; v < 256; v++) {
                if (!vals[v]) {
                    full_coverage = false;
                    break;
                }
            }
        }
        if (full_coverage) return;
        
        AxDiagnostic d = {0};
        d.severity = AX_DIAG_ERROR;
        d.code = AX_PAT_NON_EXHAUSTIVE;
        d.message = ax_diag_code_default_message(AX_PAT_NON_EXHAUSTIVE);
        d.primary = expr->span;
        ax_diag_sink_report(sink, &d);
        return;
    }
    
    if (t->kind == AX_TY_BOOL) {
        bool has_true = false;
        bool has_false = false;
        for (const AxHirMatchArm *arm = expr->match.arms; arm; arm = arm->next) {
            if (arm->pat->kind == AX_HIR_PAT_LITERAL) {
                if (arm->pat->literal.tok.kind == AX_TOK_KW_TRUE) {
                    if (has_true) {
                        AxDiagnostic d = {0}; d.severity = AX_DIAG_WARNING; d.code = AX_PAT_UNREACHABLE; d.message = ax_diag_code_default_message(AX_PAT_UNREACHABLE); d.primary = arm->pat->span; ax_diag_sink_report(sink, &d);
                    } else if (!arm->guard) has_true = true;
                }
                if (arm->pat->literal.tok.kind == AX_TOK_KW_FALSE) {
                    if (has_false) {
                        AxDiagnostic d = {0}; d.severity = AX_DIAG_WARNING; d.code = AX_PAT_UNREACHABLE; d.message = ax_diag_code_default_message(AX_PAT_UNREACHABLE); d.primary = arm->pat->span; ax_diag_sink_report(sink, &d);
                    } else if (!arm->guard) has_false = true;
                }
            }
        }
        if (has_unconditional_wildcard || (has_true && has_false)) return;
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
                StrView name = (arm->pat->path.path.span.file.v != 0) ? ax_source_db_span_text(db, arm->pat->path.path.span) : (StrView){0};
                vname = name;
                if (name.len > 0) {
                    const char *dot = memchr(name.ptr, '.', name.len);
                    if (dot) {
                        vname.ptr = dot + 1;
                        vname.len = name.len - (dot - name.ptr) - 1;
                    }
                }
                if (vname.len == 0 && arm->pat->path.path.name.v != 0) {
                    vname = ax_interner_get(str_in, arm->pat->path.path.name);
                }
            } else if (arm->pat->kind == AX_HIR_PAT_STRUCT) {
                StrView name = (arm->pat->struct_pat.path.span.file.v != 0) ? ax_source_db_span_text(db, arm->pat->struct_pat.path.span) : (StrView){0};
                vname = name;
                if (name.len > 0) {
                    const char *dot = memchr(name.ptr, '.', name.len);
                    if (dot) {
                        vname.ptr = dot + 1;
                        vname.len = name.len - (dot - name.ptr) - 1;
                    }
                }
                if (vname.len == 0 && arm->pat->struct_pat.path.name.v != 0) {
                    vname = ax_interner_get(str_in, arm->pat->struct_pat.path.name);
                }
            }

            if (vname.ptr) {
                size_t vidx = 0;
                StrView name = (arm->pat->kind == AX_HIR_PAT_PATH) ?
                    ((arm->pat->path.path.span.file.v != 0) ? ax_source_db_span_text(db, arm->pat->path.path.span) : (StrView){0}) :
                    ((arm->pat->struct_pat.path.span.file.v != 0) ? ax_source_db_span_text(db, arm->pat->struct_pat.path.span) : (StrView){0});
                bool enum_matches = true;
                if (name.len > 0) {
                    const char *dot = memchr(name.ptr, '.', name.len);
                    if (dot) {
                        StrView ename;
                        ename.ptr = name.ptr;
                        ename.len = dot - name.ptr;
                        StrView expected_ename = ax_interner_get(str_in, t->enm.def->enum_decl.name);
                        if (!ax_sv_eq(ename, expected_ename)) {
                            enum_matches = false;
                        }
                    }
                }
                
                for (const AxHirVariantDecl *v = t->enm.def->enum_decl.variants; v; v = v->next) {
                    StrView var_name = ax_interner_get(str_in, v->name);
                    if (enum_matches && ax_sv_eq(var_name, vname)) {
                        if (seen[vidx]) {
                            AxDiagnostic d = {0}; d.severity = AX_DIAG_WARNING; d.code = AX_PAT_UNREACHABLE; d.message = ax_diag_code_default_message(AX_PAT_UNREACHABLE); d.primary = arm->pat->span; ax_diag_sink_report(sink, &d);
                        } else if (!arm->guard) {
                            seen[vidx] = true;
                        }
                        break;
                    }
                    vidx++;
                }
            }
        }

        if (has_unconditional_wildcard) return;

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
    
    if (has_unconditional_wildcard) return;

    AxDiagnostic d = {0};
    d.severity = AX_DIAG_ERROR;
    d.code = AX_PAT_NON_EXHAUSTIVE;
    d.message = ax_diag_code_default_message(AX_PAT_NON_EXHAUSTIVE);
    d.primary = expr->span;
    ax_diag_sink_report(sink, &d);
}
