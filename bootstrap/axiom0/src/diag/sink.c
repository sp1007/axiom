#include "diag/diag.h"
#include <string.h>
#include <stdlib.h>

void ax_diag_sink_init(AxDiagSink *sink) {
    ax_arena_init(&sink->arena, 8192);
    sink->diags = NULL;
    sink->len = 0;
    sink->cap = 0;
    sink->errors = 0;
    sink->warnings = 0;
}

void ax_diag_sink_free(AxDiagSink *sink) {
    ax_xfree(sink->diags);
    ax_arena_reset(&sink->arena);
    sink->len = 0;
    sink->cap = 0;
}

static const char *dup_str(AxArena *arena, const char *str) {
    if (!str) return NULL;
    size_t len = strlen(str);
    char *res = ax_arena_alloc(arena, len + 1, 1);
    memcpy(res, str, len + 1);
    return res;
}

void ax_diag_sink_report(AxDiagSink *sink, const AxDiagnostic *diag) {
    if (sink->len == sink->cap) {
        sink->diags = ax_grow_array(sink->diags, &sink->cap, sizeof(AxDiagnostic *), sink->len + 1);
    }
    AxDiagnostic *d = ax_arena_alloc(&sink->arena, sizeof(AxDiagnostic), 8);
    
    d->code = diag->code;
    d->severity = diag->severity;
    d->message = dup_str(&sink->arena, diag->message);
    d->primary = diag->primary;
    
    d->label_count = diag->label_count;
    if (d->label_count > 0) {
        d->labels = ax_arena_alloc(&sink->arena, sizeof(AxDiagLabel) * d->label_count, 8);
        for (size_t i = 0; i < d->label_count; i++) {
            d->labels[i].span = diag->labels[i].span;
            d->labels[i].message = dup_str(&sink->arena, diag->labels[i].message);
        }
    } else {
        d->labels = NULL;
    }
    
    d->note_count = diag->note_count;
    if (d->note_count > 0) {
        d->notes = ax_arena_alloc(&sink->arena, sizeof(const char *) * d->note_count, 8);
        for (size_t i = 0; i < d->note_count; i++) {
            d->notes[i] = dup_str(&sink->arena, diag->notes[i]);
        }
    } else {
        d->notes = NULL;
    }
    
    d->help_count = diag->help_count;
    if (d->help_count > 0) {
        d->helps = ax_arena_alloc(&sink->arena, sizeof(const char *) * d->help_count, 8);
        for (size_t i = 0; i < d->help_count; i++) {
            d->helps[i] = dup_str(&sink->arena, diag->helps[i]);
        }
    } else {
        d->helps = NULL;
    }
    
    d->fix_count = diag->fix_count;
    if (d->fix_count > 0) {
        d->fixes = ax_arena_alloc(&sink->arena, sizeof(AxDiagFix) * d->fix_count, 8);
        for (size_t i = 0; i < d->fix_count; i++) {
            d->fixes[i].message = dup_str(&sink->arena, diag->fixes[i].message);
            d->fixes[i].applicability = diag->fixes[i].applicability;
            d->fixes[i].edit_count = diag->fixes[i].edit_count;
            if (d->fixes[i].edit_count > 0) {
                d->fixes[i].edits = ax_arena_alloc(&sink->arena, sizeof(AxDiagEdit) * d->fixes[i].edit_count, 8);
                for (size_t j = 0; j < d->fixes[i].edit_count; j++) {
                    d->fixes[i].edits[j].span = diag->fixes[i].edits[j].span;
                    d->fixes[i].edits[j].replacement = dup_str(&sink->arena, diag->fixes[i].edits[j].replacement);
                }
            } else {
                d->fixes[i].edits = NULL;
            }
        }
    } else {
        d->fixes = NULL;
    }
    
    d->data_count = diag->data_count;
    if (d->data_count > 0) {
        d->data = ax_arena_alloc(&sink->arena, sizeof(AxDiagDataEntry) * d->data_count, 8);
        for (size_t i = 0; i < d->data_count; i++) {
            d->data[i].key = dup_str(&sink->arena, diag->data[i].key);
            d->data[i].value.kind = diag->data[i].value.kind;
            switch (diag->data[i].value.kind) {
                case AX_DIAG_DATA_STRING:
                    d->data[i].value.v.string = dup_str(&sink->arena, diag->data[i].value.v.string);
                    break;
                case AX_DIAG_DATA_INTEGER:
                    d->data[i].value.v.integer = diag->data[i].value.v.integer;
                    break;
                case AX_DIAG_DATA_BOOLEAN:
                    d->data[i].value.v.boolean = diag->data[i].value.v.boolean;
                    break;
                case AX_DIAG_DATA_STRING_LIST:
                    d->data[i].value.v.string_list.count = diag->data[i].value.v.string_list.count;
                    if (d->data[i].value.v.string_list.count > 0) {
                        d->data[i].value.v.string_list.items = ax_arena_alloc(&sink->arena, sizeof(const char *) * d->data[i].value.v.string_list.count, 8);
                        for (size_t j = 0; j < d->data[i].value.v.string_list.count; j++) {
                            d->data[i].value.v.string_list.items[j] = dup_str(&sink->arena, diag->data[i].value.v.string_list.items[j]);
                        }
                    } else {
                        d->data[i].value.v.string_list.items = NULL;
                    }
                    break;
            }
        }
    } else {
        d->data = NULL;
    }
    
    sink->diags[sink->len++] = d;
    if (d->severity == AX_DIAG_ERROR) {
        sink->errors++;
    } else if (d->severity == AX_DIAG_WARNING) {
        sink->warnings++;
    }
}

struct SortEntry {
    size_t idx;
    AxDiagnostic *d;
};

static int compare_entries(const void *a, const void *b) {
    const struct SortEntry *ea = a;
    const struct SortEntry *eb = b;
    const AxDiagnostic *da = ea->d;
    const AxDiagnostic *db = eb->d;
    
    bool da_none = ax_span_is_none(da->primary);
    bool db_none = ax_span_is_none(db->primary);
    if (da_none != db_none) {
        return da_none ? -1 : 1;
    }
    if (!da_none) {
        if (da->primary.file.v != db->primary.file.v) {
            return (da->primary.file.v < db->primary.file.v) ? -1 : 1;
        }
        if (da->primary.start != db->primary.start) {
            return (da->primary.start < db->primary.start) ? -1 : 1;
        }
    }
    if (da->code != db->code) {
        return (da->code < db->code) ? -1 : 1;
    }
    if (ea->idx != eb->idx) {
        return (ea->idx < eb->idx) ? -1 : 1;
    }
    return 0;
}

void ax_diag_sink_sort(AxDiagSink *sink) {
    if (sink->len > 1) {
        struct SortEntry *entries = ax_xmalloc(sizeof(struct SortEntry) * sink->len);
        for (size_t i = 0; i < sink->len; i++) {
            entries[i].idx = i;
            entries[i].d = sink->diags[i];
        }
        
        qsort(entries, sink->len, sizeof(struct SortEntry), compare_entries);
        
        for (size_t i = 0; i < sink->len; i++) {
            sink->diags[i] = entries[i].d;
        }
        
        ax_xfree(entries);
    }
}
