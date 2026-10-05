#ifndef AX_LEX_LEX_H
#define AX_LEX_LEX_H

#include "diag/diag.h"
#include "source/source.h"
#include "kernel/interner.h"

typedef enum AxTokenKind {
    AX_TOK_IDENT, AX_TOK_INT, AX_TOK_FLOAT, AX_TOK_STR, AX_TOK_BYTE_STR, AX_TOK_CHAR, AX_TOK_LABEL,
    AX_TOK_UNDERSCORE, AX_TOK_ERROR, AX_TOK_EOF,
    
    AX_TOK_KW_AS, AX_TOK_KW_ASYNC, AX_TOK_KW_AWAIT, AX_TOK_KW_BREAK, AX_TOK_KW_COMPTIME,
    AX_TOK_KW_CONST, AX_TOK_KW_CONTINUE, AX_TOK_KW_DYN, AX_TOK_KW_ELSE, AX_TOK_KW_ENUM,
    AX_TOK_KW_EXTERN, AX_TOK_KW_FALSE, AX_TOK_KW_FN, AX_TOK_KW_FOR, AX_TOK_KW_IF,
    AX_TOK_KW_IMPL, AX_TOK_KW_IN, AX_TOK_KW_LET, AX_TOK_KW_LOOP, AX_TOK_KW_MATCH,
    AX_TOK_KW_MODULE, AX_TOK_KW_MUT, AX_TOK_KW_MUT_VIEW, AX_TOK_KW_PUB, AX_TOK_KW_RETURN,
    AX_TOK_KW_SELF_VALUE, AX_TOK_KW_SELF_TYPE, AX_TOK_KW_STATIC, AX_TOK_KW_STRUCT,
    AX_TOK_KW_TRAIT, AX_TOK_KW_TRUE, AX_TOK_KW_TYPE, AX_TOK_KW_UNSAFE, AX_TOK_KW_USE,
    AX_TOK_KW_VIEW, AX_TOK_KW_WHERE, AX_TOK_KW_WHILE,
    AX_TOK_KW_MOVE, AX_TOK_KW_UNION, AX_TOK_KW_YIELD,

    AX_TOK_LPAREN, AX_TOK_RPAREN, AX_TOK_LBRACKET, AX_TOK_RBRACKET, AX_TOK_LBRACE, AX_TOK_RBRACE,
    AX_TOK_COMMA, AX_TOK_SEMI, AX_TOK_COLON, AX_TOK_DOT, AX_TOK_DOT_DOT, AX_TOK_DOT_DOT_EQ,
    AX_TOK_AT, AX_TOK_QUESTION, AX_TOK_ARROW, AX_TOK_FAT_ARROW,
    AX_TOK_PLUS, AX_TOK_MINUS, AX_TOK_STAR, AX_TOK_SLASH, AX_TOK_PERCENT, AX_TOK_AMP,
    AX_TOK_PIPE, AX_TOK_CARET, AX_TOK_TILDE, AX_TOK_BANG, AX_TOK_SHL, AX_TOK_SHR,
    AX_TOK_AMP_AMP, AX_TOK_PIPE_PIPE, AX_TOK_EQ_EQ, AX_TOK_BANG_EQ, AX_TOK_LT, AX_TOK_LT_EQ,
    AX_TOK_GT, AX_TOK_GT_EQ,
    AX_TOK_EQ, AX_TOK_PLUS_EQ, AX_TOK_MINUS_EQ, AX_TOK_STAR_EQ, AX_TOK_SLASH_EQ,
    AX_TOK_PERCENT_EQ, AX_TOK_AMP_EQ, AX_TOK_PIPE_EQ, AX_TOK_CARET_EQ, AX_TOK_SHL_EQ,
    AX_TOK_SHR_EQ
} AxTokenKind;

enum {
    AX_TOK_FLAG_NL_BEFORE = 1 << 0,
    AX_TOK_FLAG_ERROR     = 1 << 1,
    AX_TOK_FLAG_RAW       = 1 << 2,
    AX_TOK_FLAG_BYTE_FORM = 1 << 3
};

typedef enum AxSuffix {
    AX_SUFFIX_NONE,
    AX_SUFFIX_I8, AX_SUFFIX_I16, AX_SUFFIX_I32, AX_SUFFIX_I64, AX_SUFFIX_ISIZE,
    AX_SUFFIX_U8, AX_SUFFIX_U16, AX_SUFFIX_U32, AX_SUFFIX_U64, AX_SUFFIX_USIZE,
    AX_SUFFIX_F32, AX_SUFFIX_F64
} AxSuffix;

typedef struct AxToken {
    AxTokenKind kind;
    Span span;
    uint16_t flags;
    union {
        struct {
            uint64_t value;
            AxSuffix suffix;
        } int_val;
        struct {
            AxSuffix suffix;
        } float_val;
        struct {
            uint8_t *bytes;
            size_t len;
        } str_val;
        uint32_t char_val;
        StrId ident_val;
    } val;
} AxToken;

typedef enum AxCommentKind {
    AX_COMMENT_LINE,
    AX_COMMENT_DOC,
    AX_COMMENT_BLOCK
} AxCommentKind;

typedef struct AxComment {
    AxCommentKind kind;
    Span span;
} AxComment;

typedef struct AxLexResult {
    AxArena arena;
    AxToken *tokens;
    size_t token_count;
    AxComment *comments;
    size_t comment_count;
} AxLexResult;

AxLexResult ax_lex(FileId file, StrView text, AxDiagSink *sink, StrInterner *interner);
void ax_lex_result_free(AxLexResult *res);

const char *ax_token_kind_name(AxTokenKind kind);
const char *ax_suffix_name(AxSuffix suffix);

#endif /* AX_LEX_LEX_H */
