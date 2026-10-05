#include "driver/driver.h"
#include <stdlib.h>
#include <string.h>

static int run_emit_tokens(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc != 2) {
        fputs("axiom0: usage: axiom0 inspect --emit=tokens <file>\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    const char *path = pos_argv[1];
    
    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = path;
    
    int rc = ax_pipeline_run(&st, AX_STAGE_LEX);

    // format: tests/lex/README.md
    for (size_t i = 0; i < st.lex_res.token_count; ++i) {
            const AxToken *tok = &st.lex_res.tokens[i];
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
                    StrView name = ax_interner_get(&st.interner, tok->val.ident_val);
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
        for (size_t i = 0; i < st.lex_res.comment_count; ++i) {
            const AxComment *c = &st.lex_res.comments[i];
            const char *ck = "LineComment";
            if (c->kind == AX_COMMENT_DOC) ck = "DocComment";
            else if (c->kind == AX_COMMENT_BLOCK) ck = "BlockComment";
            fprintf(io->out, "%s [%u..%u]\n", ck, c->span.start, c->span.end);
        }

    ax_pipeline_free(&st);
    free(pos_argv);
    return rc;
}

const AxEmitter axemit_tokens = {
    "tokens",
    "dump the lexer token stream",
    run_emit_tokens
};
