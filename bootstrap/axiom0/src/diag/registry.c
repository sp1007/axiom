#include "diag/diag.h"
#include <string.h>

#define AX_DIAG(code, severity, msg) #code,
static const char *const s_code_names[] = {
#include "diag/codes.def"
};
#undef AX_DIAG

#define AX_DIAG(code, severity, msg) msg,
static const char *const s_code_messages[] = {
#include "diag/codes.def"
};
#undef AX_DIAG

#define AX_DIAG(code, severity, msg) AX_DIAG_##severity,
static const AxDiagSeverity s_code_severities[] = {
#include "diag/codes.def"
};
#undef AX_DIAG

const char *ax_diag_code_name(AxDiagCode code) {
    if ((size_t)code >= AX_DIAG_CODE_COUNT) return "<unknown>";
    return s_code_names[code];
}

const char *ax_diag_code_default_message(AxDiagCode code) {
    if ((size_t)code >= AX_DIAG_CODE_COUNT) return "";
    return s_code_messages[code];
}

AxDiagSeverity ax_diag_code_severity(AxDiagCode code) {
    if ((size_t)code >= AX_DIAG_CODE_COUNT) return AX_DIAG_ERROR;
    return s_code_severities[code];
}
