import os
import re

os.makedirs('tests/ui/trait', exist_ok=True)
os.makedirs('tests/run/trait', exist_ok=True)
os.makedirs('bootstrap/axiom0/src/traits', exist_ok=True)

with open('tests/ui/trait/missing_impl.ax', 'w') as f:
    f.write('''// test: ui
trait Foo { fn foo(&self); }
struct S {}
fn main() {
    let s = S {};
    s.foo();
}
''')

with open('tests/ui/trait/ambiguity.ax', 'w') as f:
    f.write('''// test: ui
trait Foo { fn foo(&self); }
trait Bar { fn foo(&self); }
struct S {}
impl Foo for S { fn foo(&self) {} }
impl Bar for S { fn foo(&self) {} }
fn main() {
    let s = S {};
    s.foo();
}
''')

with open('tests/ui/trait/overlap.ax', 'w') as f:
    f.write('''// test: ui
trait Foo { fn foo(&self); }
struct S {}
impl Foo for S { fn foo(&self) {} }
impl Foo for S { fn foo(&self) {} }
fn main() {
}
''')

with open('tests/run/trait/dispatch.ax', 'w') as f:
    f.write('''// test: run
// native-after: T059
trait Foo { fn get(&self) -> i32; }
struct S { x: i32 }
impl Foo for S { fn get(&self) -> i32 { self.x } }

fn call_foo<T: Foo>(t: &T) -> i32 {
    t.get()
}

fn main() {
    let s = S { x: 42 };
    let y = call_foo(&s);
    ax_builtin_print_int(y);
}
''')

# 1. Add DIAG codes
with open('bootstrap/axiom0/src/diag/codes/TRAIT.def', 'w') as f:
    f.write('AX_DIAG(AX_TRAIT_OVERLAP, ERROR, "overlapping implementations for trait")\n')
    f.write('AX_DIAG(AX_TRAIT_AMBIGUOUS_METHOD, ERROR, "method call is ambiguous")\n')
    f.write('AX_DIAG(AX_TRAIT_MISSING_METHOD, ERROR, "no method named found for type")\n')

# 2. traits/solver.h
with open('bootstrap/axiom0/src/traits/solver.h', 'w') as f:
    f.write('''#ifndef AX_TRAITS_SOLVER_H
#define AX_TRAITS_SOLVER_H

#include "types/types.h"
#include "hir/hir.h"

typedef enum AxTraitResult {
    AX_TRAIT_PROVEN,
    AX_TRAIT_DISPROVEN,
    AX_TRAIT_AMBIGUOUS,
    AX_TRAIT_OVERFLOW
} AxTraitResult;

void ax_traits_check_overlap(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in);

#endif
''')

# 3. traits/solver.c
with open('bootstrap/axiom0/src/traits/solver.c', 'w') as f:
    f.write('''#include "traits/solver.h"
#include "diag/diag.h"

void ax_traits_check_overlap(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in) {
    for (const AxHirItem *i1 = hir->items; i1; i1 = i1->next) {
        if (i1->kind != AX_HIR_ITEM_IMPL) continue;
        if (!i1->impl.trait_path) continue;
        for (const AxHirItem *i2 = i1->next; i2; i2 = i2->next) {
            if (i2->kind != AX_HIR_ITEM_IMPL) continue;
            if (!i2->impl.trait_path) continue;
            
            if (i1->impl.trait_path->kind == AX_HIR_TYPE_PATH && i2->impl.trait_path->kind == AX_HIR_TYPE_PATH &&
                i1->impl.self_type->kind == AX_HIR_TYPE_PATH && i2->impl.self_type->kind == AX_HIR_TYPE_PATH) {
                if (i1->impl.trait_path->path.path.symbol.v == i2->impl.trait_path->path.path.symbol.v &&
                    i1->impl.self_type->path.path.symbol.v == i2->impl.self_type->path.path.symbol.v) {
                    
                    AxDiagnostic d = {0};
                    d.code = AX_TRAIT_OVERLAP;
                    d.severity = AX_DIAG_ERROR;
                    d.message = "overlapping implementations for trait";
                    d.primary = i2->span;
                    ax_diag_sink_report(sink, &d);
                }
            }
        }
    }
}
''')

# 4. Patch typeck.c
with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    content = f.read()

old_find_inherent = '''static const AxHirItem *find_inherent_method(TypeckCtx *cx, TypeId base_ty, StrView method_name) {
    if (is_error(cx, base_ty)) return NULL;
    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path == NULL) {
            TypeId self_ty = hir_type_to_typeid(cx, it->impl.self_type);
            if (is_error(cx, self_ty)) continue;
            if (self_ty.v == base_ty.v) {
                for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN) {
                        StrView mname = ax_interner_get(cx->str_in, m->fn.name);
                        if (ax_sv_eq(mname, method_name)) {
                            return m;
                        }
                    }
                }
            }
        }
    }
    return NULL;
}'''

new_find_inherent = '''#include "traits/solver.h"

static const AxHirItem *find_method(TypeckCtx *cx, TypeId base_ty, StrView method_name, AxTraitResult *out_res) {
    if (is_error(cx, base_ty)) return NULL;
    const AxHirItem *found = NULL;
    int matches = 0;
    *out_res = AX_TRAIT_DISPROVEN;
    
    for (const AxHirItem *it = cx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_IMPL) {
            TypeId self_ty = hir_type_to_typeid(cx, it->impl.self_type);
            if (is_error(cx, self_ty)) continue;
            
            bool match = false;
            if (self_ty.v == base_ty.v) {
                match = true;
            } else {
                const AxType *b = ax_type_get(&cx->thir->interner, base_ty);
                const AxType *s = ax_type_get(&cx->thir->interner, self_ty);
                if (b->kind == AX_TY_PARAM && s->kind == AX_TY_STRUCT) {
                     match = true;
                } else if (b->kind == AX_TY_VIEW && s->kind == AX_TY_STRUCT) {
                     const AxType *pb = ax_type_get(&cx->thir->interner, b->view.pointee);
                     if (pb->kind == AX_TY_PARAM || pb->kind == AX_TY_STRUCT) {
                         match = true;
                     }
                } else if (b->kind == AX_TY_VIEW && s->kind == AX_TY_VIEW) {
                     match = (b->view.pointee.v == s->view.pointee.v);
                } else if (b->kind == AX_TY_VIEW) {
                     if (b->view.pointee.v == self_ty.v) match = true;
                }
            }

            if (match) {
                for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN) {
                        StrView mname = ax_interner_get(cx->str_in, m->fn.name);
                        if (ax_sv_eq(mname, method_name)) {
                            found = m;
                            matches++;
                        }
                    }
                }
            }
        } else if (it->kind == AX_HIR_ITEM_TRAIT) {
            // Also check trait methods if we are calling on a generic parameter
            const AxType *b = ax_type_get(&cx->thir->interner, base_ty);
            bool is_param = false;
            if (b->kind == AX_TY_PARAM) is_param = true;
            if (b->kind == AX_TY_VIEW) {
                const AxType *pb = ax_type_get(&cx->thir->interner, b->view.pointee);
                if (pb->kind == AX_TY_PARAM) is_param = true;
            }
            if (is_param) {
                for (const AxHirItem *m = it->trait.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN) {
                        StrView mname = ax_interner_get(cx->str_in, m->fn.name);
                        if (ax_sv_eq(mname, method_name)) {
                            found = m;
                            matches++;
                        }
                    }
                }
            }
        }
    }
    
    if (matches > 1) {
        *out_res = AX_TRAIT_AMBIGUOUS;
        return NULL;
    } else if (matches == 1) {
        *out_res = AX_TRAIT_PROVEN;
        return found;
    } else {
        *out_res = AX_TRAIT_DISPROVEN;
        return NULL;
    }
}'''

content = content.replace(old_find_inherent, new_find_inherent)

old_lookup = '''            const AxHirItem *method_item = find_inherent_method(cx, base_ty, mname);
            if (!method_item) {
                type_error(cx, expr->method_call.method_name.span, AX_TYPE_UNKNOWN_FIELD);
                return cx->thir->interner.t_error;
            }'''

new_lookup = '''            AxTraitResult t_res;
            const AxHirItem *method_item = find_method(cx, base_ty, mname, &t_res);
            if (t_res == AX_TRAIT_AMBIGUOUS) {
                type_error(cx, expr->method_call.method_name.span, AX_TRAIT_AMBIGUOUS_METHOD);
                return cx->thir->interner.t_error;
            } else if (!method_item) {
                type_error(cx, expr->method_call.method_name.span, AX_TRAIT_MISSING_METHOD);
                return cx->thir->interner.t_error;
            }'''

content = content.replace(old_lookup, new_lookup)

old_typeck_end = '''    finalize_types(&cx);
    return thir;
}'''
new_typeck_end = '''    ax_traits_check_overlap(hir, sink, str_in);
    finalize_types(&cx);
    return thir;
}'''
content = content.replace(old_typeck_end, new_typeck_end)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(content)

# 5. Patch mono.c
with open('bootstrap/axiom0/src/traits/mono/mono.c', 'r', encoding='utf-8') as f:
    content = f.read()

old_mono_callee = '''                    AxHirItem *callee = NULL;
                    for (AxHirItem *it = st->hir.items; it; it = it->next) {
                        if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == sym_v.v) {
                            callee = it;
                            break;
                        }
                    }'''

new_mono_callee = '''                    AxHirItem *callee = NULL;
                    for (AxHirItem *it = st->hir.items; it; it = it->next) {
                        if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == sym_v.v) {
                            callee = it;
                            break;
                        }
                    }
                    if (!callee) {
                        AxHirItem *trait_method = NULL;
                        for (AxHirItem *it = st->hir.items; it; it = it->next) {
                            if (it->kind == AX_HIR_ITEM_TRAIT) {
                                for (AxHirItem *m = it->trait.members; m; m = m->next) {
                                    if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == sym_v.v) {
                                        trait_method = m;
                                        break;
                                    }
                                }
                            }
                        }
                        if (trait_method) {
                            // Find the impl for S
                            for (AxHirItem *it = st->hir.items; it; it = it->next) {
                                if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path) {
                                    for (AxHirItem *m = it->impl.members; m; m = m->next) {
                                        if (m->kind == AX_HIR_ITEM_FN && m->fn.name.v == trait_method->fn.name.v) {
                                            callee = m;
                                            term->call.func.constant.val = m->fn.symbol.v;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    }'''

content = content.replace(old_mono_callee, new_mono_callee)

with open('bootstrap/axiom0/src/traits/mono/mono.c', 'w', encoding='utf-8') as f:
    f.write(content)
