#ifndef AX_SYNTAX_PARSE_H
#define AX_SYNTAX_PARSE_H

#include "kernel/arena.h"
#include "lex/lex.h"
#include "syntax/ast.h"
#include "diag/diag.h"

typedef struct AxParseResult {
    AxAst ast;
    /* Information about fatal errors is in the diag sink. */
} AxParseResult;

/* Parse the token stream into an AST. 
 * The AST nodes are allocated in `arena`. 
 * Syntax errors are reported to `sink`. */
AxParseResult ax_parse(AxArena *arena, const AxToken *tokens, size_t token_count, AxDiagSink *sink, StrInterner *interner);

#endif /* AX_SYNTAX_PARSE_H */
