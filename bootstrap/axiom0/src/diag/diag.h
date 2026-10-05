#ifndef AX_DIAG_DIAG_H
#define AX_DIAG_DIAG_H

#include "kernel/base.h"
#include "source/source.h"
#include <stdio.h>

/* Severities */
typedef enum AxDiagSeverity {
    AX_DIAG_ERROR,
    AX_DIAG_WARNING,
    AX_DIAG_INFO,
    AX_DIAG_HINT
} AxDiagSeverity;

/* Codes */
#define AX_DIAG(code, severity, msg) code,
typedef enum AxDiagCode {
#include "diag/codes.def"
    AX_DIAG_CODE_COUNT
} AxDiagCode;
#undef AX_DIAG

const char *ax_diag_code_name(AxDiagCode code);
const char *ax_diag_code_default_message(AxDiagCode code);
AxDiagSeverity ax_diag_code_severity(AxDiagCode code);

typedef struct AxDiagLabel {
    Span span;
    const char *message;
} AxDiagLabel;

typedef enum AxDiagFixApplicability {
    AX_FIX_MACHINE_APPLICABLE,
    AX_FIX_MAYBE_APPLICABLE,
    AX_FIX_MANUAL_REVIEW
} AxDiagFixApplicability;

typedef struct AxDiagEdit {
    Span span;
    const char *replacement;
} AxDiagEdit;

typedef struct AxDiagFix {
    const char *message;
    AxDiagFixApplicability applicability;
    AxDiagEdit *edits;
    size_t edit_count;
} AxDiagFix;

typedef enum AxDiagDataKind {
    AX_DIAG_DATA_STRING,
    AX_DIAG_DATA_INTEGER,
    AX_DIAG_DATA_BOOLEAN,
    AX_DIAG_DATA_STRING_LIST
} AxDiagDataKind;

typedef struct AxDiagDataValue {
    AxDiagDataKind kind;
    union {
        const char *string;
        int64_t integer;
        bool boolean;
        struct {
            const char **items;
            size_t count;
        } string_list;
    } v;
} AxDiagDataValue;

typedef struct AxDiagDataEntry {
    const char *key;
    AxDiagDataValue value;
} AxDiagDataEntry;

typedef struct AxDiagnostic {
    AxDiagCode code;
    AxDiagSeverity severity;
    const char *message;
    Span primary;

    AxDiagLabel *labels;
    size_t label_count;

    const char **notes;
    size_t note_count;

    const char **helps;
    size_t help_count;

    AxDiagFix *fixes;
    size_t fix_count;

    AxDiagDataEntry *data;
    size_t data_count;
} AxDiagnostic;

typedef struct AxDiagSink {
    AxArena arena;
    AxDiagnostic **diags;
    size_t len;
    size_t cap;
    size_t errors;
    size_t warnings;
} AxDiagSink;

void ax_diag_sink_init(AxDiagSink *sink);
void ax_diag_sink_free(AxDiagSink *sink);

/* The diag passed in is deeply copied into the sink's arena. */
void ax_diag_sink_report(AxDiagSink *sink, const AxDiagnostic *diag);

void ax_diag_sink_sort(AxDiagSink *sink);

void ax_diag_render_human(const AxDiagSink *sink, const SourceDatabase *db, FILE *out);
void ax_diag_render_json(const AxDiagSink *sink, const SourceDatabase *db, FILE *out);

#endif /* AX_DIAG_DIAG_H */
