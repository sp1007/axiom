#include "driver/driver.h"
#include "lex/lex.h"
#include "source/source.h"
#include "diag/diag.h"

#include <stdlib.h>
#include <string.h>

static int run_emit_tokens(const AxIo *io, int argc, char **argv) {
    if (argc != 2) {
        fputs("axiom0: usage: axiom0 inspect --emit=tokens <file>\n", io->err);
        return AX_EXIT_USAGE;
    }

    const char *path = argv[1];
    SourceDatabase db;
    ax_source_db_init(&db);

    FileId file = ax_source_db_load(&db, ax_sv_cstr(path));
    if (file.v == 0) {
        fprintf(io->err, "axiom0: failed to open file '%s'\n", path);
        ax_source_db_free(&db);
        return AX_EXIT_DIAG;
    }

    StrView text = ax_source_db_text(&db, file);

    AxDiagSink sink;
    ax_diag_sink_init(&sink);
    StrInterner interner;
    ax_interner_init(&interner);

    AxLexResult res = ax_lex(file, text, &sink, &interner);

    // format: tests/lex/README.md
    for (size_t i = 0; i < res.token_count; ++i) {
        const AxToken *tok = &res.tokens[i];
        fprintf(io->out, "%s [%u..%u]", ax_token_kind_name(tok->kind), tok->span.start, tok->span.end);
        if (tok->flags & AX_TOK_FLAG_NL_BEFORE) {
            fprintf(io->out, " NL");
        }
        if (tok->flags & AX_TOK_FLAG_ERROR) {
            fprintf(io->out, " ERROR");
        }
        if (tok->flags & AX_TOK_FLAG_RAW) {
            fprintf(io->out, " RAW");
        }
        if (tok->flags & AX_TOK_FLAG_BYTE_FORM) {
            fprintf(io->out, " BYTE_FORM");
        }

        switch (tok->kind) {
            case AX_TOK_INT:
                fprintf(io->out, " %llu", (unsigned long long)tok->val.int_val.value);
                if (tok->val.int_val.suffix != AX_SUFFIX_NONE) {
                    fprintf(io->out, " %s", ax_suffix_name(tok->val.int_val.suffix));
                }
                break;
            case AX_TOK_FLOAT:
                fprintf(io->out, " %s", ax_suffix_name(tok->val.float_val.suffix));
                break;
            case AX_TOK_IDENT:
            case AX_TOK_LABEL: {
                StrView name = ax_interner_get(&interner, tok->val.ident_val);
                fprintf(io->out, " ");
                fwrite(name.ptr, 1, name.len, io->out);
                break;
            }
            case AX_TOK_CHAR:
                fprintf(io->out, " %u", tok->val.char_val);
                break;
            case AX_TOK_STR:
            case AX_TOK_BYTE_STR: {
                fprintf(io->out, " ");
                for (size_t k = 0; k < tok->val.str_val.len; ++k) {
                    fprintf(io->out, "%02x", tok->val.str_val.bytes[k]);
                }
                break;
            }
            default:
                break;
        }
        fprintf(io->out, "\n");
    }
    
    // Dump trivia
    for (size_t i = 0; i < res.comment_count; ++i) {
        const AxComment *c = &res.comments[i];
        const char *ck = "LineComment";
        if (c->kind == AX_COMMENT_DOC) ck = "DocComment";
        else if (c->kind == AX_COMMENT_BLOCK) ck = "BlockComment";
        fprintf(io->out, "%s [%u..%u]\n", ck, c->span.start, c->span.end);
    }

    int rc = AX_EXIT_OK;
    if (sink.errors > 0 || sink.warnings > 0) {
        ax_diag_render_human(&sink, &db, io->err);
        rc = sink.errors > 0 ? AX_EXIT_DIAG : AX_EXIT_OK;
    }

    ax_lex_result_free(&res);
    ax_interner_free(&interner);
    ax_diag_sink_free(&sink);
    ax_source_db_free(&db);

    return rc;
}

const AxEmitter axemit_tokens = {
    "tokens",
    "dump the lexer token stream",
    run_emit_tokens
};
