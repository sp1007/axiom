#include "source/source.h"
#include "kernel/base.h"
#include "kernel/utf8.h"
#include <stdio.h>
#include <stdlib.h>

static void linemap_init(LineMap *lm) {
    lm->line_offsets = NULL;
    lm->len = 0;
    lm->cap = 0;
}

static void linemap_free(LineMap *lm) {
    ax_xfree(lm->line_offsets);
    linemap_init(lm);
}

static void linemap_push(LineMap *lm, uint32_t offset) {
    if (lm->len == lm->cap) {
        lm->line_offsets = (uint32_t *)ax_grow_array(
            lm->line_offsets, &lm->cap, sizeof(uint32_t), lm->len + 1);
    }
    lm->line_offsets[lm->len++] = offset;
}

static void build_line_map(SourceFile *sf) {
    linemap_init(&sf->line_map);
    linemap_push(&sf->line_map, 0); /* Line 1 starts at 0 */
    
    const char *p = sf->text.ptr;
    size_t len = sf->text.len;
    for (size_t i = 0; i < len; ) {
        if (p[i] == '\r' && i + 1 < len && p[i+1] == '\n') {
            linemap_push(&sf->line_map, (uint32_t)(i + 2));
            i += 2;
        } else if (p[i] == '\n') {
            linemap_push(&sf->line_map, (uint32_t)(i + 1));
            i += 1;
        } else {
            i++;
        }
    }
}

void ax_source_db_init(SourceDatabase *db) {
    ax_arena_init(&db->arena, 0);
    FileIdTable_init(&db->files);
    AxPathMap_init(&db->path_map);
}

void ax_source_db_free(SourceDatabase *db) {
    for (FileId id = FileIdTable_first(&db->files); FileId_is_some(id); id = FileIdTable_after(&db->files, id)) {
        SourceFile *sf = FileIdTable_get(&db->files, id);
        linemap_free(&sf->line_map);
        if (sf->alloc_ptr) {
            ax_xfree((void *)sf->alloc_ptr);
        }
    }
    FileIdTable_free(&db->files);
    AxPathMap_free(&db->path_map);
    ax_arena_destroy(&db->arena);
}

static SourceFile *create_file(SourceDatabase *db, StrView canonical_path, StrView text, const char *alloc_ptr) {
    SourceFile sf;
    sf.id = FileId_none(); /* set by push */
    sf.canonical_path = canonical_path;
    
    /* Handle BOM */
    if (text.len >= 3 && (unsigned char)text.ptr[0] == 0xEF && 
        (unsigned char)text.ptr[1] == 0xBB && (unsigned char)text.ptr[2] == 0xBF) {
        text.ptr += 3;
        text.len -= 3;
    }
    
    sf.text = text;
    sf.content_hash = ax_hash64(text.ptr, text.len);
    
    size_t err_offset;
    sf.has_invalid_utf8 = !ax_utf8_validate((const unsigned char *)text.ptr, text.len, &err_offset);
    
    sf.alloc_ptr = alloc_ptr;
    build_line_map(&sf);
    
    FileId id = FileIdTable_push(&db->files, sf);
    SourceFile *psf = FileIdTable_get(&db->files, id);
    psf->id = id;
    
    AxPathMap_insert(&db->path_map, psf->canonical_path, id);
    return psf;
}

FileId ax_source_db_load_as(SourceDatabase *db, StrView disk_path, StrView display_path) {
    FileId *existing = AxPathMap_get(&db->path_map, display_path);
    if (existing) {
        return *existing;
    }
    
    /* Need to NUL-terminate path for fopen */
    StrBuf path_buf;
    ax_sb_init(&path_buf);
    ax_sb_push(&path_buf, disk_path);
    
    FILE *f = fopen(path_buf.ptr, "rb");
    ax_sb_free(&path_buf);
    
    if (!f) return FileId_none();
    
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    if (size < 0) {
        fclose(f);
        return FileId_none();
    }
    
    char *buf = ax_xmalloc((size_t)size + 1);
    size_t read = fread(buf, 1, (size_t)size, f);
    fclose(f);
    
    if (read != (size_t)size) {
        ax_xfree(buf);
        return FileId_none();
    }
    buf[size] = '\0';
    
    StrView interned_path = ax_sv_dup(&db->arena, display_path);
    SourceFile *sf = create_file(db, interned_path, ax_sv(buf, (size_t)size), buf);
    return sf->id;
}

FileId ax_source_db_load(SourceDatabase *db, StrView canonical_path) {
    return ax_source_db_load_as(db, canonical_path, canonical_path);
}

FileId ax_source_db_add_virtual(SourceDatabase *db, StrView identity, StrView text) {
    FileId *existing = AxPathMap_get(&db->path_map, identity);
    if (existing) {
        return *existing;
    }
    StrView interned_id = ax_sv_dup(&db->arena, identity);
    StrView interned_text = ax_sv_dup(&db->arena, text);
    SourceFile *sf = create_file(db, interned_id, interned_text, NULL);
    return sf->id;
}

StrView ax_source_db_text(const SourceDatabase *db, FileId file) {
    if (!FileIdTable_contains(&db->files, file)) return ax_sv(NULL, 0);
    return FileIdTable_get(&db->files, file)->text;
}

StrView ax_source_db_path(const SourceDatabase *db, FileId file) {
    if (!FileIdTable_contains(&db->files, file)) return ax_sv(NULL, 0);
    return FileIdTable_get(&db->files, file)->canonical_path;
}

uint64_t ax_source_db_hash(const SourceDatabase *db, FileId file) {
    if (!FileIdTable_contains(&db->files, file)) return 0;
    return FileIdTable_get(&db->files, file)->content_hash;
}

StrView ax_source_db_span_text(const SourceDatabase *db, Span span) {
    if (ax_span_is_none(span)) return ax_sv(NULL, 0);
    SourceFile *sf = FileIdTable_get(&db->files, span.file);
    if (span.start > span.end || span.end > sf->text.len) {
        return ax_sv(NULL, 0);
    }
    return ax_sv_slice(sf->text, span.start, span.end - span.start);
}

LineCol ax_source_db_line_col(const SourceDatabase *db, Span span) {
    LineCol lc = {0, 0, 0};
    if (ax_span_is_none(span)) return lc;
    SourceFile *sf = FileIdTable_get(&db->files, span.file);
    
    uint32_t offset = span.start;
    if (offset > sf->text.len) offset = (uint32_t)sf->text.len;
    
    LineMap *lm = &sf->line_map;
    uint32_t line_idx = 0;
    
    /* Binary search for the line */
    uint32_t low = 0, high = lm->len;
    while (low < high) {
        uint32_t mid = low + (high - low) / 2;
        if (lm->line_offsets[mid] <= offset) {
            line_idx = mid;
            low = mid + 1;
        } else {
            high = mid;
        }
    }
    
    lc.line = line_idx + 1;
    uint32_t line_start = lm->line_offsets[line_idx];
    lc.col_bytes = offset - line_start + 1;
    
    /* Calculate characters (scalars) for column */
    size_t byte_diff = offset - line_start;
    const unsigned char *p = (const unsigned char *)sf->text.ptr + line_start;
    lc.col_chars = (uint32_t)ax_utf8_count(p, byte_diff) + 1;
    
    return lc;
}

Span ax_source_db_line_range(const SourceDatabase *db, FileId file, uint32_t line) {
    if (!FileIdTable_contains(&db->files, file)) return ax_span_none();
    SourceFile *sf = FileIdTable_get(&db->files, file);
    if (line == 0 || line > sf->line_map.len) return ax_span_none();
    
    uint32_t start = sf->line_map.line_offsets[line - 1];
    uint32_t end;
    if (line < sf->line_map.len) {
        end = sf->line_map.line_offsets[line];
        /* Exclude trailing \n or \r\n */
        if (end > start && sf->text.ptr[end - 1] == '\n') {
            end--;
            if (end > start && sf->text.ptr[end - 1] == '\r') {
                end--;
            }
        }
    } else {
        end = (uint32_t)sf->text.len;
    }
    return ax_span(file, start, end);
}
