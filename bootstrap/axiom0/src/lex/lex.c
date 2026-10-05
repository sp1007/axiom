#include "lex/lex.h"
#include "kernel/utf8.h"
#include "kernel/vec.h"
#include <string.h>

const char *ax_token_kind_name(AxTokenKind kind) {
    switch (kind) {
        case AX_TOK_IDENT: return "Ident";
        case AX_TOK_INT: return "Int";
        case AX_TOK_FLOAT: return "Float";
        case AX_TOK_STR: return "Str";
        case AX_TOK_BYTE_STR: return "ByteStr";
        case AX_TOK_CHAR: return "Char";
        case AX_TOK_LABEL: return "Label";
        case AX_TOK_UNDERSCORE: return "Underscore";
        case AX_TOK_ERROR: return "Error";
        case AX_TOK_EOF: return "Eof";

        case AX_TOK_KW_AS: return "KwAs";
        case AX_TOK_KW_ASYNC: return "KwAsync";
        case AX_TOK_KW_AWAIT: return "KwAwait";
        case AX_TOK_KW_BREAK: return "KwBreak";
        case AX_TOK_KW_COMPTIME: return "KwComptime";
        case AX_TOK_KW_CONST: return "KwConst";
        case AX_TOK_KW_CONTINUE: return "KwContinue";
        case AX_TOK_KW_DYN: return "KwDyn";
        case AX_TOK_KW_ELSE: return "KwElse";
        case AX_TOK_KW_ENUM: return "KwEnum";
        case AX_TOK_KW_EXTERN: return "KwExtern";
        case AX_TOK_KW_FALSE: return "KwFalse";
        case AX_TOK_KW_FN: return "KwFn";
        case AX_TOK_KW_FOR: return "KwFor";
        case AX_TOK_KW_IF: return "KwIf";
        case AX_TOK_KW_IMPL: return "KwImpl";
        case AX_TOK_KW_IN: return "KwIn";
        case AX_TOK_KW_LET: return "KwLet";
        case AX_TOK_KW_LOOP: return "KwLoop";
        case AX_TOK_KW_MATCH: return "KwMatch";
        case AX_TOK_KW_MODULE: return "KwModule";
        case AX_TOK_KW_MUT: return "KwMut";
        case AX_TOK_KW_MUT_VIEW: return "KwMutView";
        case AX_TOK_KW_PUB: return "KwPub";
        case AX_TOK_KW_RETURN: return "KwReturn";
        case AX_TOK_KW_SELF_VALUE: return "KwSelfValue";
        case AX_TOK_KW_SELF_TYPE: return "KwSelfType";
        case AX_TOK_KW_STATIC: return "KwStatic";
        case AX_TOK_KW_STRUCT: return "KwStruct";
        case AX_TOK_KW_TRAIT: return "KwTrait";
        case AX_TOK_KW_TRUE: return "KwTrue";
        case AX_TOK_KW_TYPE: return "KwType";
        case AX_TOK_KW_UNSAFE: return "KwUnsafe";
        case AX_TOK_KW_USE: return "KwUse";
        case AX_TOK_KW_VIEW: return "KwView";
        case AX_TOK_KW_WHERE: return "KwWhere";
        case AX_TOK_KW_WHILE: return "KwWhile";
        case AX_TOK_KW_MOVE: return "KwMove";
        case AX_TOK_KW_UNION: return "KwUnion";
        case AX_TOK_KW_YIELD: return "KwYield";

        case AX_TOK_LPAREN: return "LParen";
        case AX_TOK_RPAREN: return "RParen";
        case AX_TOK_LBRACKET: return "LBracket";
        case AX_TOK_RBRACKET: return "RBracket";
        case AX_TOK_LBRACE: return "LBrace";
        case AX_TOK_RBRACE: return "RBrace";
        case AX_TOK_COMMA: return "Comma";
        case AX_TOK_SEMI: return "Semi";
        case AX_TOK_COLON: return "Colon";
        case AX_TOK_DOT: return "Dot";
        case AX_TOK_DOT_DOT: return "DotDot";
        case AX_TOK_DOT_DOT_EQ: return "DotDotEq";
        case AX_TOK_AT: return "At";
        case AX_TOK_QUESTION: return "Question";
        case AX_TOK_ARROW: return "Arrow";
        case AX_TOK_FAT_ARROW: return "FatArrow";
        case AX_TOK_PLUS: return "Plus";
        case AX_TOK_MINUS: return "Minus";
        case AX_TOK_STAR: return "Star";
        case AX_TOK_SLASH: return "Slash";
        case AX_TOK_PERCENT: return "Percent";
        case AX_TOK_AMP: return "Amp";
        case AX_TOK_PIPE: return "Pipe";
        case AX_TOK_CARET: return "Caret";
        case AX_TOK_TILDE: return "Tilde";
        case AX_TOK_BANG: return "Bang";
        case AX_TOK_SHL: return "Shl";
        case AX_TOK_SHR: return "Shr";
        case AX_TOK_AMP_AMP: return "AmpAmp";
        case AX_TOK_PIPE_PIPE: return "PipePipe";
        case AX_TOK_EQ_EQ: return "EqEq";
        case AX_TOK_BANG_EQ: return "BangEq";
        case AX_TOK_LT: return "Lt";
        case AX_TOK_LT_EQ: return "LtEq";
        case AX_TOK_GT: return "Gt";
        case AX_TOK_GT_EQ: return "GtEq";
        case AX_TOK_EQ: return "Eq";
        case AX_TOK_PLUS_EQ: return "PlusEq";
        case AX_TOK_MINUS_EQ: return "MinusEq";
        case AX_TOK_STAR_EQ: return "StarEq";
        case AX_TOK_SLASH_EQ: return "SlashEq";
        case AX_TOK_PERCENT_EQ: return "PercentEq";
        case AX_TOK_AMP_EQ: return "AmpEq";
        case AX_TOK_PIPE_EQ: return "PipeEq";
        case AX_TOK_CARET_EQ: return "CaretEq";
        case AX_TOK_SHL_EQ: return "ShlEq";
        case AX_TOK_SHR_EQ: return "ShrEq";
    }
    return "?";
}

const char *ax_suffix_name(AxSuffix suffix) {
    switch (suffix) {
        case AX_SUFFIX_NONE: return "None";
        case AX_SUFFIX_I8: return "i8";
        case AX_SUFFIX_I16: return "i16";
        case AX_SUFFIX_I32: return "i32";
        case AX_SUFFIX_I64: return "i64";
        case AX_SUFFIX_ISIZE: return "isize";
        case AX_SUFFIX_U8: return "u8";
        case AX_SUFFIX_U16: return "u16";
        case AX_SUFFIX_U32: return "u32";
        case AX_SUFFIX_U64: return "u64";
        case AX_SUFFIX_USIZE: return "usize";
        case AX_SUFFIX_F32: return "f32";
        case AX_SUFFIX_F64: return "f64";
    }
    return "?";
}

typedef struct Lexer {
    FileId file;
    const unsigned char *src;
    size_t len;
    size_t pos;
    AxDiagSink *sink;
    StrInterner *interner;
    AxArena *arena;

    AxToken *tokens;
    size_t token_cap;
    size_t token_len;

    AxComment *comments;
    size_t comment_cap;
    size_t comment_len;

    bool pending_nl;
    AxTokenKind last_token_kind;
} Lexer;

static void push_token(Lexer *l, AxToken t) {
    if (l->token_len == l->token_cap) {
        l->token_cap = l->token_cap == 0 ? 64 : l->token_cap * 2;
        AxToken *new_arr = ax_arena_alloc(l->arena, l->token_cap * sizeof(AxToken), _Alignof(AxToken));
        if (l->token_len > 0) memcpy(new_arr, l->tokens, l->token_len * sizeof(AxToken));
        l->tokens = new_arr;
    }
    t.flags |= l->pending_nl ? AX_TOK_FLAG_NL_BEFORE : 0;
    l->pending_nl = false;
    l->tokens[l->token_len++] = t;
    l->last_token_kind = t.kind;
}

static void push_comment(Lexer *l, AxComment c) {
    if (l->comment_len == l->comment_cap) {
        l->comment_cap = l->comment_cap == 0 ? 16 : l->comment_cap * 2;
        AxComment *new_arr = ax_arena_alloc(l->arena, l->comment_cap * sizeof(AxComment), _Alignof(AxComment));
        if (l->comment_len > 0) memcpy(new_arr, l->comments, l->comment_len * sizeof(AxComment));
        l->comments = new_arr;
    }
    l->comments[l->comment_len++] = c;
}

static void report(Lexer *l, AxDiagCode code, uint32_t start, uint32_t end) {
    AxDiagnostic diag = {
        .code = code,
        .severity = AX_DIAG_ERROR,
        .message = ax_diag_code_default_message(code),
        .primary = ax_span(l->file, start, end)
    };
    ax_diag_sink_report(l->sink, &diag);
}

static void report_with_fix(Lexer *l, AxDiagCode code, uint32_t start, uint32_t end, const char *repl) {
    AxDiagnostic diag = {
        .code = code,
        .severity = AX_DIAG_ERROR,
        .message = ax_diag_code_default_message(code),
        .primary = ax_span(l->file, start, end)
    };
    if (repl) {
        AxDiagFix *fix = ax_arena_alloc(&l->sink->arena, sizeof(AxDiagFix), _Alignof(AxDiagFix));
        AxDiagEdit *edit = ax_arena_alloc(&l->sink->arena, sizeof(AxDiagEdit), _Alignof(AxDiagEdit));
        edit->span = diag.primary;
        edit->replacement = repl;
        fix->message = repl;
        fix->applicability = AX_FIX_MACHINE_APPLICABLE;
        fix->edits = edit;
        fix->edit_count = 1;
        diag.fixes = fix;
        diag.fix_count = 1;
    }
    ax_diag_sink_report(l->sink, &diag);
}

static bool is_whitespace(unsigned char c) {
    return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

static bool is_ident_start(unsigned char c) {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_';
}

static bool is_ident_continue(unsigned char c) {
    return is_ident_start(c) || (c >= '0' && c <= '9');
}

static bool is_dec_digit(unsigned char c) {
    return c >= '0' && c <= '9';
}

static bool is_hex_digit(unsigned char c) {
    return is_dec_digit(c) || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
}

static bool is_oct_digit(unsigned char c) {
    return c >= '0' && c <= '7';
}

static bool is_bin_digit(unsigned char c) {
    return c == '0' || c == '1';
}

static unsigned hex_val(unsigned char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return 0;
}

static void scan_whitespace_and_comments(Lexer *l) {
    while (l->pos < l->len) {
        if (l->src[l->pos] == '\n') {
            l->pending_nl = true;
            l->pos++;
        } else if (is_whitespace(l->src[l->pos])) {
            l->pos++;
        } else if (l->pos + 1 < l->len && l->src[l->pos] == '/' && l->src[l->pos+1] == '/') {
            uint32_t start = l->pos;
            l->pos += 2;
            bool is_doc = false;
            if (l->pos < l->len && l->src[l->pos] == '/' && (l->pos + 1 == l->len || l->src[l->pos+1] != '/')) {
                is_doc = true;
            }
            while (l->pos < l->len && l->src[l->pos] != '\n') {
                l->pos++;
            }
            AxComment c = {
                .kind = is_doc ? AX_COMMENT_DOC : AX_COMMENT_LINE,
                .span = ax_span(l->file, start, l->pos)
            };
            push_comment(l, c);
            // We do not consume the '\n' here, it will be consumed in the next iteration and set pending_nl
        } else if (l->pos + 1 < l->len && l->src[l->pos] == '/' && l->src[l->pos+1] == '*') {
            uint32_t start = l->pos;
            l->pos += 2;
            int depth = 1;
            while (l->pos < l->len && depth > 0) {
                if (l->src[l->pos] == '\n') {
                    l->pending_nl = true;
                }
                if (l->pos + 1 < l->len && l->src[l->pos] == '/' && l->src[l->pos+1] == '*') {
                    depth++;
                    l->pos += 2;
                } else if (l->pos + 1 < l->len && l->src[l->pos] == '*' && l->src[l->pos+1] == '/') {
                    depth--;
                    l->pos += 2;
                } else {
                    l->pos++;
                }
            }
            if (depth > 0) {
                report(l, AX_LEX_UNTERMINATED_COMMENT, start, l->len);
            }
            AxComment c = {
                .kind = AX_COMMENT_BLOCK,
                .span = ax_span(l->file, start, l->pos)
            };
            push_comment(l, c);
        } else {
            break;
        }
    }
}

static AxTokenKind check_keyword(StrView sv) {
    if (sv.len < 2 || sv.len > 8) return AX_TOK_IDENT;
    
    // perfect hashing or simple if chain
    const char *s = sv.ptr;
    size_t n = sv.len;
    
    if (n==2 && s[0]=='a' && s[1]=='s') return AX_TOK_KW_AS;
    if (n==5 && memcmp(s,"async",5)==0) return AX_TOK_KW_ASYNC;
    if (n==5 && memcmp(s,"await",5)==0) return AX_TOK_KW_AWAIT;
    if (n==5 && memcmp(s,"break",5)==0) return AX_TOK_KW_BREAK;
    if (n==8 && memcmp(s,"comptime",8)==0) return AX_TOK_KW_COMPTIME;
    if (n==5 && memcmp(s,"const",5)==0) return AX_TOK_KW_CONST;
    if (n==8 && memcmp(s,"continue",8)==0) return AX_TOK_KW_CONTINUE;
    if (n==3 && memcmp(s,"dyn",3)==0) return AX_TOK_KW_DYN;
    if (n==4 && memcmp(s,"else",4)==0) return AX_TOK_KW_ELSE;
    if (n==4 && memcmp(s,"enum",4)==0) return AX_TOK_KW_ENUM;
    if (n==6 && memcmp(s,"extern",6)==0) return AX_TOK_KW_EXTERN;
    if (n==5 && memcmp(s,"false",5)==0) return AX_TOK_KW_FALSE;
    if (n==2 && s[0]=='f' && s[1]=='n') return AX_TOK_KW_FN;
    if (n==3 && memcmp(s,"for",3)==0) return AX_TOK_KW_FOR;
    if (n==2 && s[0]=='i' && s[1]=='f') return AX_TOK_KW_IF;
    if (n==4 && memcmp(s,"impl",4)==0) return AX_TOK_KW_IMPL;
    if (n==2 && s[0]=='i' && s[1]=='n') return AX_TOK_KW_IN;
    if (n==3 && memcmp(s,"let",3)==0) return AX_TOK_KW_LET;
    if (n==4 && memcmp(s,"loop",4)==0) return AX_TOK_KW_LOOP;
    if (n==5 && memcmp(s,"match",5)==0) return AX_TOK_KW_MATCH;
    if (n==6 && memcmp(s,"module",6)==0) return AX_TOK_KW_MODULE;
    if (n==3 && memcmp(s,"mut",3)==0) return AX_TOK_KW_MUT;
    if (n==8 && memcmp(s,"mut_view",8)==0) return AX_TOK_KW_MUT_VIEW;
    if (n==3 && memcmp(s,"pub",3)==0) return AX_TOK_KW_PUB;
    if (n==6 && memcmp(s,"return",6)==0) return AX_TOK_KW_RETURN;
    if (n==4 && memcmp(s,"self",4)==0) return AX_TOK_KW_SELF_VALUE;
    if (n==4 && memcmp(s,"Self",4)==0) return AX_TOK_KW_SELF_TYPE;
    if (n==6 && memcmp(s,"static",6)==0) return AX_TOK_KW_STATIC;
    if (n==6 && memcmp(s,"struct",6)==0) return AX_TOK_KW_STRUCT;
    if (n==5 && memcmp(s,"trait",5)==0) return AX_TOK_KW_TRAIT;
    if (n==4 && memcmp(s,"true",4)==0) return AX_TOK_KW_TRUE;
    if (n==4 && memcmp(s,"type",4)==0) return AX_TOK_KW_TYPE;
    if (n==6 && memcmp(s,"unsafe",6)==0) return AX_TOK_KW_UNSAFE;
    if (n==3 && memcmp(s,"use",3)==0) return AX_TOK_KW_USE;
    if (n==4 && memcmp(s,"view",4)==0) return AX_TOK_KW_VIEW;
    if (n==5 && memcmp(s,"where",5)==0) return AX_TOK_KW_WHERE;
    if (n==5 && memcmp(s,"while",5)==0) return AX_TOK_KW_WHILE;
    if (n==4 && memcmp(s,"move",4)==0) return AX_TOK_KW_MOVE;
    if (n==5 && memcmp(s,"union",5)==0) return AX_TOK_KW_UNION;
    if (n==5 && memcmp(s,"yield",5)==0) return AX_TOK_KW_YIELD;
    
    return AX_TOK_IDENT;
}

static AxSuffix scan_suffix(Lexer *l, bool *had_err) {
    if (l->pos >= l->len) return AX_SUFFIX_NONE;
    if (!is_ident_start(l->src[l->pos])) return AX_SUFFIX_NONE;
    
    uint32_t start = l->pos;
    while (l->pos < l->len && is_ident_continue(l->src[l->pos])) l->pos++;
    StrView sv = ax_sv((const char*)&l->src[start], l->pos - start);
    const char *s = sv.ptr;
    size_t n = sv.len;
    AxSuffix suf = AX_SUFFIX_NONE;
    if (n==2 && s[0]=='i' && s[1]=='8') suf = AX_SUFFIX_I8;
    else if (n==3 && memcmp(s,"i16",3)==0) suf = AX_SUFFIX_I16;
    else if (n==3 && memcmp(s,"i32",3)==0) suf = AX_SUFFIX_I32;
    else if (n==3 && memcmp(s,"i64",3)==0) suf = AX_SUFFIX_I64;
    else if (n==5 && memcmp(s,"isize",5)==0) suf = AX_SUFFIX_ISIZE;
    else if (n==2 && s[0]=='u' && s[1]=='8') suf = AX_SUFFIX_U8;
    else if (n==3 && memcmp(s,"u16",3)==0) suf = AX_SUFFIX_U16;
    else if (n==3 && memcmp(s,"u32",3)==0) suf = AX_SUFFIX_U32;
    else if (n==3 && memcmp(s,"u64",3)==0) suf = AX_SUFFIX_U64;
    else if (n==5 && memcmp(s,"usize",5)==0) suf = AX_SUFFIX_USIZE;
    else if (n==3 && memcmp(s,"f32",3)==0) suf = AX_SUFFIX_F32;
    else if (n==3 && memcmp(s,"f64",3)==0) suf = AX_SUFFIX_F64;
    
    if (suf == AX_SUFFIX_NONE) {
        report(l, AX_LEX_INVALID_SUFFIX, start, l->pos);
        *had_err = true;
    }
    return suf;
}


static void scan_string_like(Lexer *l, AxToken *tok, bool is_byte_str, bool is_raw) {
    StrBuf buf;
    ax_sb_init(&buf);
    bool terminated = false;
    
    while (l->pos < l->len) {
        if (l->src[l->pos] == '"') {
            terminated = true;
            l->pos++;
            break;
        }
        if (l->src[l->pos] == '\n' || l->src[l->pos] == '\r') {
            break;
        }
        if (!is_raw && l->src[l->pos] == '\\') {
            uint32_t esc_start = l->pos;
            l->pos++;
            if (l->pos >= l->len || l->src[l->pos] == '\n' || l->src[l->pos] == '\r') {
                // Not an escape, just a backslash at end of line. AXS-LEX-061
                // It is an unterminated string. The span includes the backslash.
                break; // Break and report unterminated
            }
            unsigned char c = l->src[l->pos++];
            if (c == 'n') ax_sb_push_byte(&buf, '\n');
            else if (c == 'r') ax_sb_push_byte(&buf, '\r');
            else if (c == 't') ax_sb_push_byte(&buf, '\t');
            else if (c == '\\') ax_sb_push_byte(&buf, '\\');
            else if (c == '0') ax_sb_push_byte(&buf, '\0');
            else if (c == '"') ax_sb_push_byte(&buf, '"');
            else if (c == '\'') ax_sb_push_byte(&buf, '\'');
            else if (c == 'x') {
                if (l->pos + 1 < l->len && is_hex_digit(l->src[l->pos]) && is_hex_digit(l->src[l->pos+1])) {
                    unsigned val = (hex_val(l->src[l->pos]) << 4) | hex_val(l->src[l->pos+1]);
                    l->pos += 2;
                    if (!is_byte_str && val > 0x7F) {
                        report(l, AX_LEX_INVALID_ESCAPE, esc_start, l->pos);
                        tok->flags |= AX_TOK_FLAG_ERROR;
                    } else {
                        ax_sb_push_byte(&buf, val);
                    }
                } else {
                    while (l->pos < l->len && l->pos - esc_start < 4 && is_hex_digit(l->src[l->pos])) {
                        l->pos++;
                    }
                    report(l, AX_LEX_INVALID_ESCAPE, esc_start, l->pos);
                    tok->flags |= AX_TOK_FLAG_ERROR;
                }
            } else if (c == 'u') {
                if (is_byte_str) {
                    // Invalid in byte string
                    uint32_t u_end = l->pos;
                    if (l->pos < l->len && l->src[l->pos] == '{') {
                        u_end++;
                        while (u_end < l->len && l->src[u_end] != '}' && l->src[u_end] != '"' && l->src[u_end] != '\n' && l->src[u_end] != '\r') {
                            u_end++;
                        }
                        if (u_end < l->len && l->src[u_end] == '}') u_end++;
                    }
                    l->pos = u_end;
                    report(l, AX_LEX_INVALID_UNICODE_ESCAPE, esc_start, l->pos);
                    tok->flags |= AX_TOK_FLAG_ERROR;
                } else {
                    bool valid = true;
                    if (l->pos < l->len && l->src[l->pos] == '{') {
                        l->pos++;
                        uint32_t hex_start = l->pos;
                        while (l->pos < l->len && is_hex_digit(l->src[l->pos])) l->pos++;
                        uint32_t hex_len = l->pos - hex_start;
                        if (l->pos < l->len && l->src[l->pos] == '}') {
                            l->pos++;
                            if (hex_len > 0 && hex_len <= 6) {
                                uint32_t val = 0;
                                for (uint32_t i = hex_start; i < hex_start + hex_len; ++i) {
                                    val = (val << 4) | hex_val(l->src[i]);
                                }
                                if (val > 0x10FFFF || (val >= 0xD800 && val <= 0xDFFF)) {
                                    valid = false;
                                } else {
                                    unsigned char out[4];
                                    unsigned n = ax_utf8_encode(val, out);
                                    for (unsigned i = 0; i < n; ++i) ax_sb_push_byte(&buf, out[i]);
                                }
                            } else {
                                valid = false;
                            }
                        } else {
                            // Find the '}' or end of line/quote
                            while (l->pos < l->len && l->src[l->pos] != '}' && l->src[l->pos] != '"' && l->src[l->pos] != '\n' && l->src[l->pos] != '\r') {
                                l->pos++;
                            }
                            if (l->pos < l->len && l->src[l->pos] == '}') l->pos++;
                            valid = false;
                        }
                    } else {
                        valid = false;
                    }
                    if (!valid) {
                        report(l, AX_LEX_INVALID_UNICODE_ESCAPE, esc_start, l->pos);
                        tok->flags |= AX_TOK_FLAG_ERROR;
                    }
                }
            } else {
                report(l, AX_LEX_INVALID_ESCAPE, esc_start, l->pos);
                tok->flags |= AX_TOK_FLAG_ERROR;
            }
        } else {
            // Normal character
            unsigned char c = l->src[l->pos];
            if (is_byte_str && c >= 0x80) {
                // Find maximal run of non-ASCII? The spec AXS-LEX-063 says "on that character"
                AxUtf8Decoded dec = ax_utf8_decode(&l->src[l->pos], l->len - l->pos);
                report(l, AX_LEX_NON_ASCII_IN_BYTE_LITERAL, l->pos, l->pos + dec.len);
                tok->flags |= AX_TOK_FLAG_ERROR;
                l->pos += dec.len;
            } else {
                ax_sb_push_byte(&buf, c);
                l->pos++;
            }
        }
    }
    
    if (!terminated) {
        report(l, AX_LEX_UNTERMINATED_STRING, tok->span.start, l->pos);
        tok->flags |= AX_TOK_FLAG_ERROR;
    }
    
    tok->span.end = l->pos;
    tok->val.str_val.len = buf.len;
    tok->val.str_val.bytes = ax_arena_alloc(l->arena, buf.len, 1);
    if (buf.len > 0) {
        memcpy(tok->val.str_val.bytes, buf.ptr, buf.len);
    }
    ax_sb_free(&buf);
}

static void scan_char_like(Lexer *l, AxToken *tok, bool is_byte) {
    uint32_t val = 0;
    bool has_val = false;
    bool multiple = false;
    bool terminated = false;
    
    while (l->pos < l->len) {
        if (l->src[l->pos] == '\'') {
            terminated = true;
            l->pos++;
            break;
        }
        if (l->src[l->pos] == '\n' || l->src[l->pos] == '\r') {
            break;
        }
        
        uint32_t cur_val = 0;
        if (l->src[l->pos] == '\\') {
            uint32_t esc_start = l->pos;
            l->pos++;
            if (l->pos >= l->len || l->src[l->pos] == '\n' || l->src[l->pos] == '\r') {
                break;
            }
            unsigned char c = l->src[l->pos++];
            if (c == 'n') cur_val = '\n';
            else if (c == 'r') cur_val = '\r';
            else if (c == 't') cur_val = '\t';
            else if (c == '\\') cur_val = '\\';
            else if (c == '0') cur_val = '\0';
            else if (c == '"') cur_val = '"';
            else if (c == '\'') cur_val = '\'';
            else if (c == 'x') {
                if (l->pos + 1 < l->len && is_hex_digit(l->src[l->pos]) && is_hex_digit(l->src[l->pos+1])) {
                    cur_val = (hex_val(l->src[l->pos]) << 4) | hex_val(l->src[l->pos+1]);
                    l->pos += 2;
                    if (!is_byte && cur_val > 0x7F) {
                        report(l, AX_LEX_INVALID_ESCAPE, esc_start, l->pos);
                        tok->flags |= AX_TOK_FLAG_ERROR;
                    }
                } else {
                    while (l->pos < l->len && l->pos - esc_start < 4 && is_hex_digit(l->src[l->pos])) {
                        l->pos++;
                    }
                    report(l, AX_LEX_INVALID_ESCAPE, esc_start, l->pos);
                    tok->flags |= AX_TOK_FLAG_ERROR;
                }
            } else if (c == 'u') {
                if (is_byte) {
                    uint32_t u_end = l->pos;
                    if (l->pos < l->len && l->src[l->pos] == '{') {
                        u_end++;
                        while (u_end < l->len && l->src[u_end] != '}' && l->src[u_end] != '\'' && l->src[u_end] != '\n' && l->src[u_end] != '\r') {
                            u_end++;
                        }
                        if (u_end < l->len && l->src[u_end] == '}') u_end++;
                    }
                    l->pos = u_end;
                    report(l, AX_LEX_INVALID_UNICODE_ESCAPE, esc_start, l->pos);
                    tok->flags |= AX_TOK_FLAG_ERROR;
                } else {
                    bool valid = true;
                    if (l->pos < l->len && l->src[l->pos] == '{') {
                        l->pos++;
                        uint32_t hex_start = l->pos;
                        while (l->pos < l->len && is_hex_digit(l->src[l->pos])) l->pos++;
                        uint32_t hex_len = l->pos - hex_start;
                        if (l->pos < l->len && l->src[l->pos] == '}') {
                            l->pos++;
                            if (hex_len > 0 && hex_len <= 6) {
                                uint32_t v = 0;
                                for (uint32_t i = hex_start; i < hex_start + hex_len; ++i) {
                                    v = (v << 4) | hex_val(l->src[i]);
                                }
                                if (v > 0x10FFFF || (v >= 0xD800 && v <= 0xDFFF)) {
                                    valid = false;
                                } else {
                                    cur_val = v;
                                }
                            } else {
                                valid = false;
                            }
                        } else {
                            while (l->pos < l->len && l->src[l->pos] != '}' && l->src[l->pos] != '\'' && l->src[l->pos] != '\n' && l->src[l->pos] != '\r') {
                                l->pos++;
                            }
                            if (l->pos < l->len && l->src[l->pos] == '}') l->pos++;
                            valid = false;
                        }
                    } else {
                        valid = false;
                    }
                    if (!valid) {
                        report(l, AX_LEX_INVALID_UNICODE_ESCAPE, esc_start, l->pos);
                        tok->flags |= AX_TOK_FLAG_ERROR;
                    }
                }
            } else {
                report(l, AX_LEX_INVALID_ESCAPE, esc_start, l->pos);
                tok->flags |= AX_TOK_FLAG_ERROR;
            }
        } else {
            if (is_byte && l->src[l->pos] >= 0x80) {
                AxUtf8Decoded dec = ax_utf8_decode(&l->src[l->pos], l->len - l->pos);
                report(l, AX_LEX_NON_ASCII_IN_BYTE_LITERAL, l->pos, l->pos + dec.len);
                tok->flags |= AX_TOK_FLAG_ERROR;
                l->pos += dec.len;
            } else {
                if (is_byte) {
                    cur_val = l->src[l->pos++];
                } else {
                    AxUtf8Decoded dec = ax_utf8_decode(&l->src[l->pos], l->len - l->pos);
                    cur_val = dec.cp;
                    l->pos += dec.len;
                }
            }
        }
        
        if (has_val) {
            multiple = true;
        } else {
            val = cur_val;
            has_val = true;
        }
    }
    
    tok->span.end = l->pos;
    
    if (!terminated) {
        report(l, AX_LEX_UNTERMINATED_CHAR, tok->span.start, l->pos);
        tok->kind = AX_TOK_ERROR;
    } else if (!has_val || multiple) {
        report(l, AX_LEX_BAD_CHAR_LITERAL, tok->span.start, l->pos);
        tok->flags |= AX_TOK_FLAG_ERROR;
    }
    
    if (is_byte) {
        tok->kind = AX_TOK_INT;
        tok->val.int_val.value = val;
        tok->val.int_val.suffix = AX_SUFFIX_U8;
        tok->flags |= AX_TOK_FLAG_BYTE_FORM;
    } else {
        tok->kind = AX_TOK_CHAR;
        tok->val.char_val = val;
    }
}

static void scan_number(Lexer *l, AxToken *tok) {
    uint32_t start = tok->span.start;
    
    int base = 10;
    bool has_prefix = false;
    uint32_t digits_start = start;
    
    if (l->pos < l->len && l->src[l->pos] == '0' && l->pos + 1 < l->len) {
        unsigned char c = l->src[l->pos+1];
        if (c == 'x' || c == 'X' || c == 'o' || c == 'O' || c == 'b' || c == 'B') {
            has_prefix = true;
            if (c == 'X' || c == 'O' || c == 'B') {
                report_with_fix(l, AX_LEX_BAD_BASE_PREFIX, l->pos, l->pos+2, c == 'X' ? "0x" : c == 'O' ? "0o" : "0b");
                tok->flags |= AX_TOK_FLAG_ERROR;
            }
            if (c == 'x' || c == 'X') base = 16;
            else if (c == 'o' || c == 'O') base = 8;
            else if (c == 'b' || c == 'B') base = 2;
            l->pos += 2;
            digits_start = l->pos;
        }
    }
    
    uint64_t val = 0;
    bool overflow = false;
    bool missing_digits = true;
    bool invalid_digit = false;
    bool bad_sep = false;
    
    bool is_float = false;
    
    while (l->pos < l->len) {
        unsigned char c = l->src[l->pos];
        if (c == '_') {
            uint32_t sep_start = l->pos;
            while (l->pos < l->len && l->src[l->pos] == '_') l->pos++;
            if (!bad_sep && (sep_start == digits_start || l->pos == l->len || !is_hex_digit(l->src[l->pos]) || l->pos - sep_start > 1)) {
                report(l, AX_LEX_BAD_DIGIT_SEPARATOR, sep_start, l->pos);
                tok->flags |= AX_TOK_FLAG_ERROR;
                bad_sep = true; // only report once
            }
            continue;
        }
        
        // break if not hex digit or dot/exp
        if (!is_hex_digit(c) && c != '.' && c != 'e' && c != 'E') {
            break;
        }
        
        if (c == '.' || c == 'e' || c == 'E') {
            if (base != 10) {
                // Not float parts for non-decimal
                if (!is_hex_digit(c)) break; // 'e' is hex digit, '.' is not
            } else {
                // Need to check if '.' is float or dotdot
                if (c == '.') {
                    if (l->last_token_kind == AX_TOK_DOT) {
                        // Tuple index mode AXS-LEX-057
                        break;
                    }
                    if (l->pos + 1 < l->len && !is_dec_digit(l->src[l->pos+1])) {
                        break; // e.g. 1.max() or 1..2
                    }
                    is_float = true;
                } else if (c == 'e' || c == 'E') {
                    if (l->last_token_kind == AX_TOK_DOT) break; // Tuple index
                    
                    uint32_t look = l->pos + 1;
                    if (look < l->len && (l->src[look] == '+' || l->src[look] == '-')) look++;
                    if (look < l->len && is_dec_digit(l->src[look])) {
                        is_float = true;
                    } else {
                        break;
                    }
                }
            }
        }
        
        if (is_float) {
            // just consume the rest of the float
            l->pos++;
            while (l->pos < l->len) {
                unsigned char fc = l->src[l->pos];
                if (fc == '_') {
                    uint32_t sep_start = l->pos;
                    while (l->pos < l->len && l->src[l->pos] == '_') l->pos++;
                    if (!bad_sep && (l->pos == l->len || !is_dec_digit(l->src[l->pos]) || l->pos - sep_start > 1)) {
                        report(l, AX_LEX_BAD_DIGIT_SEPARATOR, sep_start, l->pos);
                        tok->flags |= AX_TOK_FLAG_ERROR;
                        bad_sep = true;
                    }
                    continue;
                }
                if (fc == 'e' || fc == 'E') {
                    l->pos++;
                    if (l->pos < l->len && (l->src[l->pos] == '+' || l->src[l->pos] == '-')) l->pos++;
                    continue;
                }
                if (!is_dec_digit(fc)) break;
                l->pos++;
            }
            break; // done float
        }
        
        // Integer part
        bool valid = false;
        if (base == 10 && is_dec_digit(c)) valid = true;
        else if (base == 16 && is_hex_digit(c)) valid = true;
        else if (base == 8 && is_oct_digit(c)) valid = true;
        else if (base == 2 && is_bin_digit(c)) valid = true;
        
        if (!valid) {
            // In a binary or octal literal the digit run is the maximal run of decimal digits and separators
            if ((base == 2 || base == 8) && is_dec_digit(c)) {
                if (!invalid_digit) {
                    report(l, AX_LEX_INVALID_DIGIT, l->pos, l->pos+1);
                    tok->flags |= AX_TOK_FLAG_ERROR;
                    invalid_digit = true;
                }
                l->pos++;
                continue;
            } else if (base == 16 && is_hex_digit(c)) {
                // valid
            } else {
                break; // not a digit
            }
        } else {
            missing_digits = false;
            uint64_t d = hex_val(c);
            if (val > (UINT64_MAX - d) / base) {
                overflow = true;
            } else {
                val = val * base + d;
            }
        }
        l->pos++;
    }
    
    // Check if ends with trailing '_'
    if (!bad_sep && l->pos > digits_start && l->src[l->pos-1] == '_') {
        // e.g. 10_
        uint32_t sep_start = l->pos - 1;
        while (sep_start > digits_start && l->src[sep_start-1] == '_') sep_start--;
        if (sep_start > digits_start) {
            report(l, AX_LEX_BAD_DIGIT_SEPARATOR, sep_start, l->pos);
            tok->flags |= AX_TOK_FLAG_ERROR;
        }
    }
    
    if (has_prefix && missing_digits) {
        report(l, AX_LEX_MISSING_DIGITS, start, l->pos);
        tok->flags |= AX_TOK_FLAG_ERROR;
        val = 0;
    }
    
    bool had_suffix_err = false;
    AxSuffix suf = AX_SUFFIX_NONE;
    if (l->last_token_kind != AX_TOK_DOT) {
        suf = scan_suffix(l, &had_suffix_err);
    }
    
    if (had_suffix_err) tok->flags |= AX_TOK_FLAG_ERROR;
    tok->span.end = l->pos;
    
    if (is_float) {
        tok->kind = AX_TOK_FLOAT;
        tok->val.float_val.suffix = suf;
    } else {
        tok->kind = AX_TOK_INT;
        if (!tok->flags && overflow) {
            report(l, AX_LEX_INT_OVERFLOW, start, l->pos);
            tok->flags |= AX_TOK_FLAG_ERROR;
            val = 0;
        } else if (overflow) {
            val = 0;
        }
        tok->val.int_val.value = val;
        tok->val.int_val.suffix = suf;
    }
}

AxLexResult ax_lex(FileId file, StrView text, AxDiagSink *sink, StrInterner *interner) {
    Lexer l;
    memset(&l, 0, sizeof(l));
    l.file = file;
    l.src = (const unsigned char *)text.ptr;
    l.len = text.len;
    l.sink = sink;
    l.interner = interner;
    AxArena arena;
    ax_arena_init(&arena, 0);
    l.arena = &arena;
    l.pending_nl = true; // start of file is true
    l.last_token_kind = AX_TOK_EOF;
    
    // Check BOM
    if (l.len >= 3 && l.src[0] == 0xEF && l.src[1] == 0xBB && l.src[2] == 0xBF) {
        l.pos += 3;
    }
    
    while (l.pos < l.len) {
        scan_whitespace_and_comments(&l);
        if (l.pos >= l.len) break;
        
        uint32_t start = l.pos;
        AxToken tok;
        memset(&tok, 0, sizeof(tok));
        tok.span.start = start;
        
        unsigned char c = l.src[l.pos];
        
        // UTF-8 decode to check invalid UTF-8
        AxUtf8Decoded dec = ax_utf8_decode(&l.src[l.pos], l.len - l.pos);
        if (!dec.ok) {
            report(&l, AX_LEX_INVALID_UTF8, start, start + dec.len);
            tok.kind = AX_TOK_ERROR;
            tok.span.end = start + dec.len;
            tok.flags |= AX_TOK_FLAG_ERROR;
            push_token(&l, tok);
            l.pos += dec.len;
            continue;
        }
        
        if (is_ident_start(c)) {
            if (c == 'b' && l.pos + 1 < l.len && (l.src[l.pos+1] == '"' || l.src[l.pos+1] == '\'')) {
                l.pos++;
                if (l.src[l.pos] == '"') {
                    l.pos++;
                    scan_string_like(&l, &tok, true, false);
                    tok.kind = AX_TOK_BYTE_STR;
                } else {
                    l.pos++;
                    scan_char_like(&l, &tok, true);
                }
                push_token(&l, tok);
                continue;
            }
            if (c == 'r' && l.pos + 1 < l.len && l.src[l.pos+1] == '"') {
                l.pos += 2;
                scan_string_like(&l, &tok, false, true);
                tok.kind = AX_TOK_STR;
                tok.flags |= AX_TOK_FLAG_RAW;
                push_token(&l, tok);
                continue;
            }
            
            while (l.pos < l.len && is_ident_continue(l.src[l.pos])) l.pos++;
            
            StrView word = ax_sv((const char *)&l.src[start], l.pos - start);
            if (word.len == 1 && word.ptr[0] == '_') {
                tok.kind = AX_TOK_UNDERSCORE;
            } else {
                tok.kind = check_keyword(word);
                if (tok.kind == AX_TOK_IDENT) {
                    tok.val.ident_val = ax_intern(l.interner, word);
                }
            }
            tok.span.end = l.pos;
            push_token(&l, tok);
            continue;
        }
        
        if (is_dec_digit(c)) {
            scan_number(&l, &tok);
            push_token(&l, tok);
            continue;
        }
        
        if (c == '"') {
            l.pos++;
            scan_string_like(&l, &tok, false, false);
            tok.kind = AX_TOK_STR;
            push_token(&l, tok);
            continue;
        }
        
        if (c == '\'') {
            l.pos++;
            if (l.pos < l.len && is_ident_start(l.src[l.pos])) {
                uint32_t word_start = l.pos;
                while (l.pos < l.len && is_ident_continue(l.src[l.pos])) l.pos++;
                if (l.pos < l.len && l.src[l.pos] == '\'') {
                    // char literal with multiple characters or valid char
                    l.pos = start + 1; // rewind to scan_char_like
                    scan_char_like(&l, &tok, false);
                } else {
                    // label
                    tok.kind = AX_TOK_LABEL;
                    tok.span.end = l.pos;
                    tok.val.ident_val = ax_intern(l.interner, ax_sv((const char *)&l.src[word_start], l.pos - word_start));
                }
            } else {
                scan_char_like(&l, &tok, false);
            }
            push_token(&l, tok);
            continue;
        }
        
        if (c == ':' && l.pos + 1 < l.len && l.src[l.pos+1] == ':') {
            report_with_fix(&l, AX_LEX_COLON_COLON, start, start+2, ".");
            tok.kind = AX_TOK_DOT;
            tok.span.end = start+2;
            tok.flags |= AX_TOK_FLAG_ERROR;
            l.pos += 2;
            push_token(&l, tok);
            continue;
        }
        if (c == ':' && l.pos + 1 < l.len && l.src[l.pos+1] == '=') {
            report_with_fix(&l, AX_LEX_COLON_EQ, start, start+2, "=");
            tok.kind = AX_TOK_EQ;
            tok.span.end = start+2;
            tok.flags |= AX_TOK_FLAG_ERROR;
            l.pos += 2;
            push_token(&l, tok);
            continue;
        }
        
        // Punctuation
        unsigned char c2 = l.pos + 1 < l.len ? l.src[l.pos+1] : 0;
        unsigned char c3 = l.pos + 2 < l.len ? l.src[l.pos+2] : 0;
        
        if (c == '.' && c2 == '.' && c3 == '.') {
            uint32_t dot_end = start + 3;
            while (dot_end < l.len && l.src[dot_end] == '.') dot_end++;
            report(&l, AX_LEX_INVALID_OPERATOR, start, dot_end);
            tok.kind = AX_TOK_ERROR;
            tok.span.end = dot_end;
            tok.flags |= AX_TOK_FLAG_ERROR;
            l.pos = dot_end;
            push_token(&l, tok);
            continue;
        }
        
        // Max munch
        if (c == '.' && c2 == '.' && c3 == '=') { tok.kind = AX_TOK_DOT_DOT_EQ; l.pos += 3; }
        else if (c == '<' && c2 == '<' && c3 == '=') { tok.kind = AX_TOK_SHL_EQ; l.pos += 3; }
        else if (c == '>' && c2 == '>' && c3 == '=') { tok.kind = AX_TOK_SHR_EQ; l.pos += 3; }
        else if (c == '.' && c2 == '.') { tok.kind = AX_TOK_DOT_DOT; l.pos += 2; }
        else if (c == '-' && c2 == '>') { tok.kind = AX_TOK_ARROW; l.pos += 2; }
        else if (c == '=' && c2 == '>') { tok.kind = AX_TOK_FAT_ARROW; l.pos += 2; }
        else if (c == '<' && c2 == '<') { tok.kind = AX_TOK_SHL; l.pos += 2; }
        else if (c == '>' && c2 == '>') { tok.kind = AX_TOK_SHR; l.pos += 2; }
        else if (c == '&' && c2 == '&') { tok.kind = AX_TOK_AMP_AMP; l.pos += 2; }
        else if (c == '|' && c2 == '|') { tok.kind = AX_TOK_PIPE_PIPE; l.pos += 2; }
        else if (c == '=' && c2 == '=') { tok.kind = AX_TOK_EQ_EQ; l.pos += 2; }
        else if (c == '!' && c2 == '=') { tok.kind = AX_TOK_BANG_EQ; l.pos += 2; }
        else if (c == '<' && c2 == '=') { tok.kind = AX_TOK_LT_EQ; l.pos += 2; }
        else if (c == '>' && c2 == '=') { tok.kind = AX_TOK_GT_EQ; l.pos += 2; }
        else if (c == '+' && c2 == '=') { tok.kind = AX_TOK_PLUS_EQ; l.pos += 2; }
        else if (c == '-' && c2 == '=') { tok.kind = AX_TOK_MINUS_EQ; l.pos += 2; }
        else if (c == '*' && c2 == '=') { tok.kind = AX_TOK_STAR_EQ; l.pos += 2; }
        else if (c == '/' && c2 == '=') { tok.kind = AX_TOK_SLASH_EQ; l.pos += 2; }
        else if (c == '%' && c2 == '=') { tok.kind = AX_TOK_PERCENT_EQ; l.pos += 2; }
        else if (c == '&' && c2 == '=') { tok.kind = AX_TOK_AMP_EQ; l.pos += 2; }
        else if (c == '|' && c2 == '=') { tok.kind = AX_TOK_PIPE_EQ; l.pos += 2; }
        else if (c == '^' && c2 == '=') { tok.kind = AX_TOK_CARET_EQ; l.pos += 2; }
        else if (c == '(') { tok.kind = AX_TOK_LPAREN; l.pos++; }
        else if (c == ')') { tok.kind = AX_TOK_RPAREN; l.pos++; }
        else if (c == '[') { tok.kind = AX_TOK_LBRACKET; l.pos++; }
        else if (c == ']') { tok.kind = AX_TOK_RBRACKET; l.pos++; }
        else if (c == '{') { tok.kind = AX_TOK_LBRACE; l.pos++; }
        else if (c == '}') { tok.kind = AX_TOK_RBRACE; l.pos++; }
        else if (c == ',') { tok.kind = AX_TOK_COMMA; l.pos++; }
        else if (c == ';') { tok.kind = AX_TOK_SEMI; l.pos++; }
        else if (c == ':') { tok.kind = AX_TOK_COLON; l.pos++; }
        else if (c == '.') { tok.kind = AX_TOK_DOT; l.pos++; }
        else if (c == '@') { tok.kind = AX_TOK_AT; l.pos++; }
        else if (c == '?') { tok.kind = AX_TOK_QUESTION; l.pos++; }
        else if (c == '+') { tok.kind = AX_TOK_PLUS; l.pos++; }
        else if (c == '-') { tok.kind = AX_TOK_MINUS; l.pos++; }
        else if (c == '*') { tok.kind = AX_TOK_STAR; l.pos++; }
        else if (c == '/') { tok.kind = AX_TOK_SLASH; l.pos++; }
        else if (c == '%') { tok.kind = AX_TOK_PERCENT; l.pos++; }
        else if (c == '&') { tok.kind = AX_TOK_AMP; l.pos++; }
        else if (c == '|') { tok.kind = AX_TOK_PIPE; l.pos++; }
        else if (c == '^') { tok.kind = AX_TOK_CARET; l.pos++; }
        else if (c == '~') { tok.kind = AX_TOK_TILDE; l.pos++; }
        else if (c == '!') { tok.kind = AX_TOK_BANG; l.pos++; }
        else if (c == '<') { tok.kind = AX_TOK_LT; l.pos++; }
        else if (c == '>') { tok.kind = AX_TOK_GT; l.pos++; }
        else if (c == '=') { tok.kind = AX_TOK_EQ; l.pos++; }
        
        if (l.pos > start) {
            tok.span.end = l.pos;
            push_token(&l, tok);
            continue;
        }
        
        // Not a punctuation either
        if (c >= 0x80) {
            // Non ASCII character outside literals
            uint32_t run_end = start + dec.len;
            while (run_end < l.len) {
                AxUtf8Decoded next_dec = ax_utf8_decode(&l.src[run_end], l.len - run_end);
                if (!next_dec.ok) break;
                if (next_dec.cp == 0xFEFF || next_dec.cp == 0x2000 || next_dec.cp == 0x2001 || next_dec.cp == 0x2002 || next_dec.cp == 0x2003 || next_dec.cp == 0x3000) {
                    break;
                }
                if (next_dec.cp >= 0x80 || is_ident_continue(l.src[run_end])) {
                    run_end += next_dec.len;
                } else {
                    break;
                }
            }
            if (dec.cp == 0xFEFF || dec.cp == 0xA0 || dec.cp == 0x2000 || dec.cp == 0x2001 || dec.cp == 0x2002 || dec.cp == 0x2003 || dec.cp == 0x3000) { 
                report(&l, AX_LEX_INVALID_CHAR, start, start + dec.len);
                l.pos += dec.len;
            } else {
                report(&l, AX_LEX_NON_ASCII_IDENT, start, run_end);
                l.pos = run_end;
            }
            tok.kind = AX_TOK_ERROR;
            tok.span.end = l.pos;
            tok.flags |= AX_TOK_FLAG_ERROR;
            push_token(&l, tok);
            continue;
        }
        
        // Anything else -> INVALID_CHAR
        report(&l, AX_LEX_INVALID_CHAR, start, start+1);
        tok.kind = AX_TOK_ERROR;
        tok.span.end = start+1;
        tok.flags |= AX_TOK_FLAG_ERROR;
        l.pos++;
        push_token(&l, tok);
    }
    
    AxToken eof_tok;
    memset(&eof_tok, 0, sizeof(eof_tok));
    eof_tok.kind = AX_TOK_EOF;
    eof_tok.span = ax_span(l.file, l.len, l.len);
    push_token(&l, eof_tok);
    
    AxLexResult res;
    res.arena = arena;
    res.tokens = l.tokens;
    res.token_count = l.token_len;
    res.comments = l.comments;
    res.comment_count = l.comment_len;
    
    return res;
}

void ax_lex_result_free(AxLexResult *res) {
    ax_arena_destroy(&res->arena);
}
