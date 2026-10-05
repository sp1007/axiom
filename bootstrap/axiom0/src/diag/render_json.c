#include "diag/diag.h"
#include <stdio.h>
#include <string.h>

static void write_json_string(FILE *out, const char *str) {
    fputc('"', out);
    if (str) {
        for (const unsigned char *p = (const unsigned char *)str; *p; p++) {
            if (*p == '"') {
                fputs("\\\"", out);
            } else if (*p == '\\') {
                fputs("\\\\", out);
            } else if (*p == '\b') {
                fputs("\\b", out);
            } else if (*p == '\f') {
                fputs("\\f", out);
            } else if (*p == '\n') {
                fputs("\\n", out);
            } else if (*p == '\r') {
                fputs("\\r", out);
            } else if (*p == '\t') {
                fputs("\\t", out);
            } else if (*p < 0x20) {
                fprintf(out, "\\u%04x", *p);
            } else {
                fputc(*p, out);
            }
        }
    }
    fputc('"', out);
}

static void write_severity(FILE *out, AxDiagSeverity sev) {
    switch (sev) {
        case AX_DIAG_ERROR: fputs("\"error\"", out); break;
        case AX_DIAG_WARNING: fputs("\"warning\"", out); break;
        case AX_DIAG_INFO: fputs("\"info\"", out); break;
        case AX_DIAG_HINT: fputs("\"hint\"", out); break;
        default: fputs("\"error\"", out); break;
    }
}

static void write_span(FILE *out, const SourceDatabase *db, Span span) {
    if (ax_span_is_none(span)) {
        fputs("null", out);
        return;
    }
    
    StrView path = ax_source_db_path(db, span.file);
    LineCol lc_start = ax_source_db_line_col(db, ax_span(span.file, span.start, span.start));
    LineCol lc_end = ax_source_db_line_col(db, ax_span(span.file, span.end, span.end));
    
    fputs("{\"file\":", out);
    // Path should have backslashes replaced with forward slashes for output.
    // Wait, the spec says "path as the file was named... with \ replaced by /".
    char path_buf[1024];
    size_t len = path.len < sizeof(path_buf) - 1 ? path.len : sizeof(path_buf) - 1;
    memcpy(path_buf, path.ptr, len);
    path_buf[len] = '\0';
    for (size_t i = 0; i < len; i++) {
        if (path_buf[i] == '\\') path_buf[i] = '/';
    }
    write_json_string(out, path_buf);
    
    fprintf(out, ",\"start\":%u,\"end\":%u,\"line\":%u,\"col\":%u,\"end_line\":%u,\"end_col\":%u}",
            (unsigned)span.start, (unsigned)span.end,
            (unsigned)lc_start.line, (unsigned)lc_start.col_chars,
            (unsigned)lc_end.line, (unsigned)lc_end.col_chars);
}

static void write_labels(FILE *out, const SourceDatabase *db, const AxDiagnostic *diag) {
    fputs("[", out);
    for (size_t i = 0; i < diag->label_count; i++) {
        if (i > 0) fputs(",", out);
        fputs("{\"span\":", out);
        write_span(out, db, diag->labels[i].span);
        fputs(",\"message\":", out);
        write_json_string(out, diag->labels[i].message ? diag->labels[i].message : "");
        fputs("}", out);
    }
    fputs("]", out);
}

static void write_string_array(FILE *out, const char **arr, size_t count) {
    fputs("[", out);
    for (size_t i = 0; i < count; i++) {
        if (i > 0) fputs(",", out);
        write_json_string(out, arr[i]);
    }
    fputs("]", out);
}

static void write_fixes(FILE *out, const SourceDatabase *db, const AxDiagnostic *diag) {
    fputs("[", out);
    for (size_t i = 0; i < diag->fix_count; i++) {
        if (i > 0) fputs(",", out);
        fputs("{\"message\":", out);
        write_json_string(out, diag->fixes[i].message);
        
        fputs(",\"applicability\":", out);
        switch (diag->fixes[i].applicability) {
            case AX_FIX_MACHINE_APPLICABLE: fputs("\"machine-applicable\"", out); break;
            case AX_FIX_MAYBE_APPLICABLE: fputs("\"maybe-applicable\"", out); break;
            case AX_FIX_MANUAL_REVIEW: fputs("\"manual-review\"", out); break;
        }
        
        fputs(",\"edits\":[", out);
        for (size_t j = 0; j < diag->fixes[i].edit_count; j++) {
            if (j > 0) fputs(",", out);
            fputs("{\"span\":", out);
            write_span(out, db, diag->fixes[i].edits[j].span);
            fputs(",\"replacement\":", out);
            write_json_string(out, diag->fixes[i].edits[j].replacement);
            fputs("}", out);
        }
        fputs("]}", out);
    }
    fputs("]", out);
}

static void write_data(FILE *out, const AxDiagnostic *diag) {
    fputs("{", out);
    for (size_t i = 0; i < diag->data_count; i++) {
        if (i > 0) fputs(",", out);
        write_json_string(out, diag->data[i].key);
        fputs(":", out);
        switch (diag->data[i].value.kind) {
            case AX_DIAG_DATA_STRING:
                write_json_string(out, diag->data[i].value.v.string);
                break;
            case AX_DIAG_DATA_INTEGER:
                fprintf(out, "%lld", (long long)diag->data[i].value.v.integer);
                break;
            case AX_DIAG_DATA_BOOLEAN:
                fputs(diag->data[i].value.v.boolean ? "true" : "false", out);
                break;
            case AX_DIAG_DATA_STRING_LIST:
                write_string_array(out, diag->data[i].value.v.string_list.items, diag->data[i].value.v.string_list.count);
                break;
        }
    }
    fputs("}", out);
}

void ax_diag_render_json(const AxDiagSink *sink, const SourceDatabase *db, FILE *out) {
    fputs("{\"schema\":1,\"tool\":\"axiom0\",\"diagnostics\":[", out);
    for (size_t i = 0; i < sink->len; i++) {
        if (i > 0) fputs(",", out);
        const AxDiagnostic *d = sink->diags[i];
        
        fprintf(out, "{\"id\":%u,\"code\":", (unsigned)i);
        write_json_string(out, ax_diag_code_name(d->code));
        fputs(",\"severity\":", out);
        write_severity(out, d->severity);
        fputs(",\"message\":", out);
        write_json_string(out, d->message);
        
        fputs(",\"primary\":", out);
        write_span(out, db, d->primary);
        
        fputs(",\"labels\":", out);
        write_labels(out, db, d);
        
        fputs(",\"notes\":", out);
        write_string_array(out, d->notes, d->note_count);
        
        fputs(",\"helps\":", out);
        write_string_array(out, d->helps, d->help_count);
        
        fputs(",\"fixes\":", out);
        write_fixes(out, db, d);
        
        fputs(",\"data\":", out);
        write_data(out, d);
        
        fputs("}", out);
    }
    fprintf(out, "],\"errors\":%u,\"warnings\":%u}\n", (unsigned)sink->errors, (unsigned)sink->warnings);
}
