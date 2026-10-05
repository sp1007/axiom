#include "diag/diag.h"
#include "unit.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void read_file_to_str(FILE *f, char *buf, size_t cap) {
    fseek(f, 0, SEEK_SET);
    size_t len = fread(buf, 1, cap - 1, f);
    buf[len] = '\0';
}

AX_TEST(diag_registry_basics) {
    AX_CHECK_EQ_STR(ax_diag_code_name(AX_LEX_INVALID_UTF8), "AX_LEX_INVALID_UTF8");
    AX_CHECK_EQ_INT(ax_diag_code_severity(AX_LEX_INVALID_UTF8), AX_DIAG_ERROR);
    AX_CHECK_EQ_STR(ax_diag_code_default_message(AX_LEX_INVALID_UTF8), "invalid UTF-8 byte sequence");
    
    // Check one code from another area to prove it was included
    AX_CHECK_EQ_STR(ax_diag_code_name(AX_ICE_INTERNAL), "AX_ICE_INTERNAL");
    AX_CHECK_EQ_INT(ax_diag_code_severity(AX_NAME_SHADOW_MODULE), AX_DIAG_WARNING);
}

AX_TEST(diag_human_renderer) {
    SourceDatabase db;
    ax_source_db_init(&db);
    FileId fid = ax_source_db_add_virtual(&db, ax_sv_cstr("src/main.ax"), 
        ax_sv_cstr("fn main() {\n\treturn true\n}\n"));
    
    AxDiagSink sink;
    ax_diag_sink_init(&sink);
    
    AxDiagnostic diag = {0};
    diag.code = AX_TYPE_MISMATCH;
    diag.severity = AX_DIAG_ERROR;
    diag.message = "mismatched types: expected `i32`, found `bool`";
    diag.primary = ax_span(fid, 13, 17); // "true"
    
    const char *notes[] = {"the function returns `i32`"};
    diag.notes = notes;
    diag.note_count = 1;
    
    const char *helps[] = {"remove the value or change the return type"};
    diag.helps = helps;
    diag.help_count = 1;
    
    ax_diag_sink_report(&sink, &diag);
    
    FILE *f = fopen("test_diag_human.out", "wb+");
    ax_diag_render_human(&sink, &db, f);
    
    char buf[1024];
    read_file_to_str(f, buf, sizeof(buf));
    fclose(f);
    
    // We do not strict-match the carets in this test to allow flexible renderer,
    // but we can check substrings.
    AX_CHECK(strstr(buf, "error[AX_TYPE_MISMATCH]: mismatched types: expected `i32`, found `bool`") != NULL);
    AX_CHECK(strstr(buf, "--> src/main.ax:2:2") != NULL);
    AX_CHECK(strstr(buf, "2 |     return true") != NULL);
    AX_CHECK(strstr(buf, "note: the function returns `i32`") != NULL);
    AX_CHECK(strstr(buf, "help: remove the value or change the return type") != NULL);
    AX_CHECK(strstr(buf, "1 error, 0 warnings") != NULL);
    
    ax_diag_sink_free(&sink);
    ax_source_db_free(&db);
}

AX_TEST(diag_json_renderer) {
    SourceDatabase db;
    ax_source_db_init(&db);
    FileId fid = ax_source_db_add_virtual(&db, ax_sv_cstr("C:\\path\\src.ax"), 
        ax_sv_cstr("a::b\n"));
        
    AxDiagSink sink;
    ax_diag_sink_init(&sink);
    
    AxDiagEdit edit = {ax_span(fid, 1, 3), "."};
    AxDiagFix fix = {"replace `::` with `.`", AX_FIX_MACHINE_APPLICABLE, &edit, 1};
    
    AxDiagnostic diag = {0};
    diag.code = AX_LEX_COLON_COLON;
    diag.severity = AX_DIAG_ERROR;
    diag.message = "`::` is not an Axiom token; paths use `.`";
    diag.primary = ax_span(fid, 1, 3);
    diag.fixes = &fix;
    diag.fix_count = 1;
    
    ax_diag_sink_report(&sink, &diag);
    
    FILE *f = fopen("test_diag_json.out", "wb+");
    ax_diag_render_json(&sink, &db, f);
    char buf[1024];
    read_file_to_str(f, buf, sizeof(buf));
    fclose(f);
    
    AX_CHECK(strstr(buf, "\"schema\":1") != NULL);
    AX_CHECK(strstr(buf, "\"tool\":\"axiom0\"") != NULL);
    AX_CHECK(strstr(buf, "\"code\":\"AX_LEX_COLON_COLON\"") != NULL);
    AX_CHECK(strstr(buf, "\"file\":\"C:/path/src.ax\"") != NULL);
    AX_CHECK(strstr(buf, "\"start\":1,\"end\":3") != NULL);
    AX_CHECK(strstr(buf, "\"replacement\":\".\"") != NULL);
    AX_CHECK(strstr(buf, "\"errors\":1,\"warnings\":0") != NULL);
    
    ax_diag_sink_free(&sink);
    ax_source_db_free(&db);
}

AX_TEST(diag_sort) {
    AxDiagSink sink;
    ax_diag_sink_init(&sink);
    
    // Emission 1
    AxDiagnostic d1 = {0};
    d1.code = AX_TYPE_MISMATCH;
    d1.primary = ax_span_none();
    ax_diag_sink_report(&sink, &d1);
    
    // Emission 2
    AxDiagnostic d2 = {0};
    d2.code = AX_TYPE_MISMATCH;
    d2.primary = ax_span((FileId){1}, 10, 10);
    ax_diag_sink_report(&sink, &d2);
    
    // Emission 3
    AxDiagnostic d3 = {0};
    d3.code = AX_TYPE_MISMATCH;
    d3.primary = ax_span((FileId){1}, 5, 5);
    ax_diag_sink_report(&sink, &d3);
    
    ax_diag_sink_sort(&sink);
    
    AX_CHECK(ax_span_is_none(sink.diags[0]->primary));
    AX_CHECK_EQ_INT(sink.diags[1]->primary.start, 5);
    AX_CHECK_EQ_INT(sink.diags[2]->primary.start, 10);
    
    ax_diag_sink_free(&sink);
}

AX_TEST(diag_qa_edge_cases) {
    SourceDatabase db;
    ax_source_db_init(&db);
    FileId fid = ax_source_db_add_virtual(&db, ax_sv_cstr("src/main.ax"), 
        ax_sv_cstr("fn \xc3\xa9() {\r\n\treturn\r\n\ttrue\r\n}\r\n"));
    
    AxDiagSink sink;
    ax_diag_sink_init(&sink);
    
    AxDiagnostic diag = {0};
    diag.code = AX_TYPE_MISMATCH;
    diag.severity = AX_DIAG_ERROR;
    diag.message = "mismatched types: multi-line unicode";
    diag.primary = ax_span(fid, 12, 24);
    
    ax_diag_sink_report(&sink, &diag);
    
    FILE *f_human = fopen("test_diag_qa_human.out", "wb+");
    ax_diag_render_human(&sink, &db, f_human);
    
    FILE *f_json = fopen("test_diag_qa_json.out", "wb+");
    ax_diag_render_json(&sink, &db, f_json);
    
    char buf_human[1024];
    read_file_to_str(f_human, buf_human, sizeof(buf_human));
    fclose(f_human);
    
    char buf_json[1024];
    read_file_to_str(f_json, buf_json, sizeof(buf_json));
    fclose(f_json);
    
    AX_CHECK(strstr(buf_human, "error[AX_TYPE_MISMATCH]: mismatched types: multi-line unicode") != NULL);
    AX_CHECK(strstr(buf_human, "--> src/main.ax:2:2") != NULL);
    AX_CHECK(strstr(buf_human, "2 |     return") != NULL);
    AX_CHECK(strstr(buf_human, "  |     ^^^^^^") != NULL);
    AX_CHECK(strstr(buf_human, "3 |     true") != NULL);
    AX_CHECK(strstr(buf_human, "  |     ^^^") != NULL);
    
    AX_CHECK(strstr(buf_json, "\"start\":12,\"end\":24") != NULL);
    AX_CHECK(strstr(buf_json, "\"line\":2,\"col\":2") != NULL);
    AX_CHECK(strstr(buf_json, "\"end_line\":3,\"end_col\":5") != NULL);
    
    ax_diag_sink_free(&sink);
    ax_source_db_free(&db);
}

AX_TEST(diag_qa_no_span) {
    SourceDatabase db;
    ax_source_db_init(&db);
    ax_source_db_add_virtual(&db, ax_sv_cstr("src/main.ax"), 
        ax_sv_cstr("fn main() {}\n"));
    
    AxDiagSink sink;
    ax_diag_sink_init(&sink);
    
    AxDiagnostic diag = {0};
    diag.code = AX_TYPE_MISMATCH;
    diag.severity = AX_DIAG_ERROR;
    diag.message = "mismatched types: no span";
    diag.primary = ax_span_none();
    
    ax_diag_sink_report(&sink, &diag);
    
    FILE *f_human = fopen("test_diag_qa_no_span_human.out", "wb+");
    ax_diag_render_human(&sink, &db, f_human);
    
    FILE *f_json = fopen("test_diag_qa_no_span_json.out", "wb+");
    ax_diag_render_json(&sink, &db, f_json);
    
    char buf_human[1024] = {0};
    read_file_to_str(f_human, buf_human, sizeof(buf_human));
    fclose(f_human);
    
    char buf_json[1024] = {0};
    read_file_to_str(f_json, buf_json, sizeof(buf_json));
    fclose(f_json);
    
    AX_CHECK(strstr(buf_human, "error[AX_TYPE_MISMATCH]: mismatched types: no span") != NULL);
    // Should not contain source view
    AX_CHECK(strstr(buf_human, "-->") == NULL);
    
    AX_CHECK(strstr(buf_json, "\"start\"") == NULL);
    
    ax_diag_sink_free(&sink);
    ax_source_db_free(&db);
}
