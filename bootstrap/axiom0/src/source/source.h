#ifndef AX_SOURCE_SOURCE_H
#define AX_SOURCE_SOURCE_H

#include "kernel/arena.h"
#include "kernel/hash.h"
#include "kernel/id.h"
#include "kernel/str.h"
#include "kernel/hashmap.h"

AX_DEFINE_ID(FileId);

typedef struct Span {
    FileId file;
    uint32_t start;
    uint32_t end;
} Span;

static inline Span ax_span(FileId file, uint32_t start, uint32_t end) {
    Span s = {file, start, end};
    return s;
}

static inline bool ax_span_is_none(Span s) {
    return s.file.v == 0;
}

static inline Span ax_span_none(void) {
    return ax_span(FileId_none(), 0, 0);
}

typedef struct LineCol {
    uint32_t line;       /* 1-based */
    uint32_t col_bytes;  /* 1-based, bytes */
    uint32_t col_chars;  /* 1-based, Unicode scalars */
} LineCol;

typedef struct LineMap {
    uint32_t *line_offsets;
    size_t len;
    size_t cap;
} LineMap;

typedef struct SourceFile {
    FileId id;
    StrView canonical_path;
    StrView text;
    uint64_t content_hash;
    LineMap line_map;
    const char *alloc_ptr; /* NULL if virtual/arena-allocated */
    bool has_invalid_utf8;
} SourceFile;

static inline uint64_t ax_path_hash(const StrView *k) { return ax_sv_hash(*k); }
static inline bool ax_path_eq(const StrView *a, const StrView *b) { return ax_sv_eq(*a, *b); }

AX_DEFINE_ID_TABLE(FileIdTable, FileId, SourceFile);
AX_DEFINE_HASHMAP(AxPathMap, StrView, FileId, ax_path_hash, ax_path_eq);

typedef struct SourceDatabase {
    AxArena arena; /* owns virtual texts and path strings */
    FileIdTable files;
    AxPathMap path_map;
} SourceDatabase;

void ax_source_db_init(SourceDatabase *db);
void ax_source_db_free(SourceDatabase *db);

/* path should be canonical. If already loaded, returns existing FileId.
 * On I/O error, returns FileId_none(). */
FileId ax_source_db_load(SourceDatabase *db, StrView canonical_path);
FileId ax_source_db_load_as(SourceDatabase *db, StrView disk_path, StrView display_path);

/* Identity is used as the path. */
FileId ax_source_db_add_virtual(SourceDatabase *db, StrView identity, StrView text);

StrView ax_source_db_text(const SourceDatabase *db, FileId file);
StrView ax_source_db_path(const SourceDatabase *db, FileId file);
uint64_t ax_source_db_hash(const SourceDatabase *db, FileId file);

/* Span access */
StrView ax_source_db_span_text(const SourceDatabase *db, Span span);
LineCol ax_source_db_line_col(const SourceDatabase *db, Span span);
Span ax_source_db_line_range(const SourceDatabase *db, FileId file, uint32_t line);

#endif /* AX_SOURCE_SOURCE_H */
