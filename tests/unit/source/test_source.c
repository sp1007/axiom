#include "source/source.h"
#include "unit.h"

AX_TEST(source_virtual_file) {
    SourceDatabase db;
    ax_source_db_init(&db);
    
    FileId id1 = ax_source_db_add_virtual(&db, ax_sv_cstr("v1.ax"), ax_sv_cstr("foo\nbar"));
    AX_CHECK(id1.v != 0);
    AX_CHECK(ax_sv_eq_cstr(ax_source_db_path(&db, id1), "v1.ax"));
    AX_CHECK(ax_sv_eq_cstr(ax_source_db_text(&db, id1), "foo\nbar"));
    
    FileId id2 = ax_source_db_add_virtual(&db, ax_sv_cstr("v1.ax"), ax_sv_cstr("different"));
    AX_CHECK_EQ_INT(id1.v, id2.v);
    
    ax_source_db_free(&db);
}

AX_TEST(source_crlf_and_no_newline) {
    SourceDatabase db;
    ax_source_db_init(&db);
    
    FileId id = ax_source_db_add_virtual(&db, ax_sv_cstr("v1.ax"), ax_sv_cstr("line1\r\nline2\r\nline3"));
    Span s1 = ax_source_db_line_range(&db, id, 1);
    AX_CHECK(ax_sv_eq_cstr(ax_source_db_span_text(&db, s1), "line1"));
    Span s2 = ax_source_db_line_range(&db, id, 2);
    AX_CHECK(ax_sv_eq_cstr(ax_source_db_span_text(&db, s2), "line2"));
    Span s3 = ax_source_db_line_range(&db, id, 3);
    AX_CHECK(ax_sv_eq_cstr(ax_source_db_span_text(&db, s3), "line3"));
    
    /* offset 6 is 'l' in line2 ("line1\r\n" is 7 bytes: 0..6)
       Wait: 'l' 'i' 'n' 'e' '1' '\r' '\n' -> 5 + 2 = 7 bytes.
       So offset 7 is 'l' of line2. */
    LineCol lc1 = ax_source_db_line_col(&db, ax_span(id, 7, 7));
    AX_CHECK_EQ_INT(lc1.line, 2);
    AX_CHECK_EQ_INT(lc1.col_bytes, 1);
    
    LineCol lc2 = ax_source_db_line_col(&db, ax_span(id, 8, 8)); /* 'i' */
    AX_CHECK_EQ_INT(lc2.line, 2);
    AX_CHECK_EQ_INT(lc2.col_bytes, 2);
    
    ax_source_db_free(&db);
}

AX_TEST(source_bom_and_multibyte) {
    SourceDatabase db;
    ax_source_db_init(&db);
    
    /* BOM + "chào" (ch\xc3\xa0o) */
    FileId id = ax_source_db_add_virtual(&db, ax_sv_cstr("v1.ax"), ax_sv_cstr("\xef\xbb\xbf""ch\xc3\xa0o"));
    AX_CHECK(ax_sv_eq_cstr(ax_source_db_text(&db, id), "ch\xc3\xa0o"));
    
    /* offset 5 is after 'o' (c=1, h=1, à=2, o=1 -> 5 bytes) */
    LineCol lc = ax_source_db_line_col(&db, ax_span(id, 5, 5));
    AX_CHECK_EQ_INT(lc.line, 1);
    AX_CHECK_EQ_INT(lc.col_bytes, 6); /* 1-based */
    AX_CHECK_EQ_INT(lc.col_chars, 5); /* c, h, à, o, plus one for the position after it */
    
    ax_source_db_free(&db);
}

AX_TEST(source_empty_file) {
    SourceDatabase db;
    ax_source_db_init(&db);
    
    FileId id = ax_source_db_add_virtual(&db, ax_sv_cstr("empty"), ax_sv_cstr(""));
    AX_CHECK(ax_sv_eq_cstr(ax_source_db_text(&db, id), ""));
    Span s = ax_source_db_line_range(&db, id, 1);
    AX_CHECK(s.start == 0 && s.end == 0);
    
    LineCol lc = ax_source_db_line_col(&db, ax_span(id, 0, 0));
    AX_CHECK_EQ_INT(lc.line, 1);
    AX_CHECK_EQ_INT(lc.col_bytes, 1);
    AX_CHECK_EQ_INT(lc.col_chars, 1);
    
    ax_source_db_free(&db);
}

AX_TEST(source_out_of_bounds) {
    SourceDatabase db;
    ax_source_db_init(&db);
    
    FileId id = ax_source_db_add_virtual(&db, ax_sv_cstr("v1.ax"), ax_sv_cstr("hello"));
    
    /* Out of bounds offset should clamp to text.len (5) */
    LineCol lc = ax_source_db_line_col(&db, ax_span(id, 100, 100));
    AX_CHECK_EQ_INT(lc.line, 1);
    AX_CHECK_EQ_INT(lc.col_bytes, 6);
    AX_CHECK_EQ_INT(lc.col_chars, 6);
    
    /* Out of bounds line should return none span */
    Span s = ax_source_db_line_range(&db, id, 10);
    AX_CHECK(ax_span_is_none(s));
    
    ax_source_db_free(&db);
}
