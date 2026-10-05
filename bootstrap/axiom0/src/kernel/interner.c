#include "kernel/interner.h"

void ax_interner_init(StrInterner *in) {
    ax_arena_init(&in->bytes, 0);
    in->strings = NULL;
    in->len = 0;
    in->cap = 0;
    AxStrIdMap_init(&in->map);
}

void ax_interner_free(StrInterner *in) {
    AxStrIdMap_free(&in->map);
    ax_xfree(in->strings);
    in->strings = NULL;
    in->len = 0;
    in->cap = 0;
    ax_arena_destroy(&in->bytes);
}

StrId ax_intern(StrInterner *in, StrView s) {
    StrId *found = AxStrIdMap_get(&in->map, s);
    if (found != NULL) {
        return *found;
    }
    StrView owned = ax_sv_dup(&in->bytes, s);
    if (in->len == in->cap) {
        in->strings = ax_grow_array(in->strings, &in->cap, sizeof(StrView), in->len + 1);
    }
    in->strings[in->len] = owned;
    StrId id = StrId_from_index(in->len++);
    AxStrIdMap_insert(&in->map, owned, id);
    return id;
}

StrId ax_intern_cstr(StrInterner *in, const char *s) {
    return ax_intern(in, ax_sv_cstr(s));
}

StrId ax_interner_lookup(const StrInterner *in, StrView s) {
    StrId *found = AxStrIdMap_get(&in->map, s);
    return found == NULL ? StrId_none() : *found;
}

StrView ax_interner_get(const StrInterner *in, StrId id) {
    if (id.v == 0 || (size_t)id.v > in->len) {
        AX_ICE("ax_interner_get: invalid StrId %u (%llu strings)", (unsigned)id.v, (unsigned long long)in->len);
    }
    return in->strings[id.v - 1];
}

size_t ax_interner_len(const StrInterner *in) {
    return in->len;
}
