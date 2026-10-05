#include "diag/diag.h"
#include <stdio.h>
#include <string.h>

static int get_gutter_width(uint32_t line) {
    if (line == 0) return 1;
    int w = 0;
    while (line > 0) {
        w++;
        line /= 10;
    }
    return w;
}

static void print_gutter_space(FILE *out, int width) {
    for (int i = 0; i < width; i++) fputc(' ', out);
    fputs(" | ", out);
}

static void print_severity_prefix(FILE *out, AxDiagSeverity sev, const char *code_name) {
    switch (sev) {
        case AX_DIAG_ERROR: fputs("error[", out); break;
        case AX_DIAG_WARNING: fputs("warning[", out); break;
        case AX_DIAG_INFO: fputs("info[", out); break;
        case AX_DIAG_HINT: fputs("hint[", out); break;
    }
    fprintf(out, "%s]: ", code_name);
}

static void render_line(FILE *out, StrView line_text) {
    for (size_t i = 0; i < line_text.len; i++) {
        char c = line_text.ptr[i];
        if (c == '\t') fputs("    ", out);
        else if (c != '\r' && c != '\n') fputc(c, out);
    }
    fputc('\n', out);
}

static void render_carets(FILE *out, StrView line_text, uint32_t start_col, uint32_t end_col, char caret_char, const char *msg) {
    // col is 1-based char index. For simplicity in MVP, we assume bytes == chars or just do byte index for the gutter.
    // Spec says: col is Unicode scalar values. Tab is one char, displayed as 4 spaces.
    // Let's accurately count display width.
    size_t display_start = 0;
    size_t display_end = 0;
    size_t char_idx = 1;
    size_t i = 0;
    
    // Find display start
    while (i < line_text.len && char_idx < start_col) {
        // Very basic utf8 char skipping:
        unsigned char c = line_text.ptr[i];
        int w = 1; // display width of this char
        size_t bytes = 1;
        if (c == '\t') { w = 4; }
        else if ((c & 0xE0) == 0xC0) bytes = 2;
        else if ((c & 0xF0) == 0xE0) bytes = 3;
        else if ((c & 0xF8) == 0xF0) bytes = 4;
        
        display_start += w;
        char_idx++;
        i += bytes;
    }
    
    display_end = display_start;
    if (start_col == end_col) {
        display_end += 1; // Zero-width gets 1 caret
    } else {
        while (i < line_text.len && char_idx < end_col) {
            unsigned char c = line_text.ptr[i];
            int w = 1;
            size_t bytes = 1;
            if (c == '\t') { w = 4; }
            else if ((c & 0xE0) == 0xC0) bytes = 2;
            else if ((c & 0xF0) == 0xE0) bytes = 3;
            else if ((c & 0xF8) == 0xF0) bytes = 4;
            
            display_end += w;
            char_idx++;
            i += bytes;
        }
    }
    
    for (size_t j = 0; j < display_start; j++) fputc(' ', out);
    for (size_t j = display_start; j < display_end; j++) fputc(caret_char, out);
    if (msg && msg[0]) {
        fprintf(out, " %s", msg);
    }
    fputc('\n', out);
}

static void print_span_snippet(FILE *out, const SourceDatabase *db, Span span, char caret_char, const char *msg, int gutter_width) {
    LineCol lc_start = ax_source_db_line_col(db, ax_span(span.file, span.start, span.start));
    LineCol lc_end = ax_source_db_line_col(db, ax_span(span.file, span.end, span.end));
    
    if (lc_start.line == lc_end.line) {
        Span line_span = ax_source_db_line_range(db, span.file, lc_start.line);
        StrView line_text = ax_source_db_span_text(db, line_span);
        
        fprintf(out, "%*u | ", gutter_width, lc_start.line);
        render_line(out, line_text);
        
        print_gutter_space(out, gutter_width);
        render_carets(out, line_text, lc_start.col_chars, lc_end.col_chars, caret_char, msg);
    } else {
        // Multi-line
        Span start_line_span = ax_source_db_line_range(db, span.file, lc_start.line);
        StrView start_line_text = ax_source_db_span_text(db, start_line_span);
        fprintf(out, "%*u | ", gutter_width, lc_start.line);
        render_line(out, start_line_text);
        
        print_gutter_space(out, gutter_width);
        render_carets(out, start_line_text, lc_start.col_chars, 999999, caret_char, NULL); // until end of line
        
        if (lc_end.line > lc_start.line + 1) {
            fprintf(out, "%*s...\n", gutter_width + 2, "");
        }
        
        Span end_line_span = ax_source_db_line_range(db, span.file, lc_end.line);
        StrView end_line_text = ax_source_db_span_text(db, end_line_span);
        fprintf(out, "%*u | ", gutter_width, lc_end.line);
        render_line(out, end_line_text);
        
        // Find first non-blank on last line
        uint32_t first_non_blank = 1;
        for (size_t i = 0; i < end_line_text.len; i++) {
            if (end_line_text.ptr[i] != ' ' && end_line_text.ptr[i] != '\t' && end_line_text.ptr[i] != '\r') {
                break;
            }
            first_non_blank++;
        }
        print_gutter_space(out, gutter_width);
        render_carets(out, end_line_text, first_non_blank, lc_end.col_chars, caret_char, msg);
    }
}

void ax_diag_render_human(const AxDiagSink *sink, const SourceDatabase *db, FILE *out) {
    for (size_t i = 0; i < sink->len; i++) {
        if (i > 0) fputs("\n", out);
        const AxDiagnostic *d = sink->diags[i];
        
        print_severity_prefix(out, d->severity, ax_diag_code_name(d->code));
        fprintf(out, "%s\n", d->message);
        
        if (!ax_span_is_none(d->primary)) {
            LineCol lc = ax_source_db_line_col(db, ax_span(d->primary.file, d->primary.start, d->primary.start));
            StrView path = ax_source_db_path(db, d->primary.file);
            
            char path_buf[1024];
            size_t len = path.len < sizeof(path_buf) - 1 ? path.len : sizeof(path_buf) - 1;
            memcpy(path_buf, path.ptr, len);
            path_buf[len] = '\0';
            for (size_t j = 0; j < len; j++) {
                if (path_buf[j] == '\\') path_buf[j] = '/';
            }
            
            fprintf(out, " --> %s:%u:%u\n", path_buf, lc.line, lc.col_chars);
            
            // Calculate gutter width
            int gutter_width = get_gutter_width(lc.line);
            for (size_t l = 0; l < d->label_count; l++) {
                if (!ax_span_is_none(d->labels[l].span) && d->labels[l].span.file.v == d->primary.file.v) {
                    LineCol llc = ax_source_db_line_col(db, ax_span(d->labels[l].span.file, d->labels[l].span.start, d->labels[l].span.start));
                    int lw = get_gutter_width(llc.line);
                    if (lw > gutter_width) gutter_width = lw;
                }
            }
            
            print_gutter_space(out, gutter_width); fputc('\n', out);
            print_span_snippet(out, db, d->primary, '^', NULL, gutter_width);
            
            // In a full implementation, labels should be interleaved in line order. 
            // For MVP, we print them sequentially.
            for (size_t l = 0; l < d->label_count; l++) {
                if (!ax_span_is_none(d->labels[l].span) && d->labels[l].span.file.v == d->primary.file.v) {
                    print_span_snippet(out, db, d->labels[l].span, '-', d->labels[l].message, gutter_width);
                }
            }
            print_gutter_space(out, gutter_width); fputc('\n', out);
        }
        
        for (size_t n = 0; n < d->note_count; n++) {
            fprintf(out, "  = note: %s\n", d->notes[n]);
        }
        for (size_t h = 0; h < d->help_count; h++) {
            fprintf(out, "  = help: %s\n", d->helps[h]);
        }
        for (size_t f = 0; f < d->fix_count; f++) {
            fprintf(out, "  = fix: %s\n", d->fixes[f].message);
        }
    }
    
    if (sink->len > 0) {
        fputc('\n', out);
        fprintf(out, "%u error%s, %u warning%s\n", 
                (unsigned)sink->errors, sink->errors == 1 ? "" : "s",
                (unsigned)sink->warnings, sink->warnings == 1 ? "" : "s");
    }
}
