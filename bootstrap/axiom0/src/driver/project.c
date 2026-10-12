#include "driver/project.h"
#include "driver/std_root.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <dirent.h>
#include <sys/stat.h>
#endif

static void normalize_slashes(char *path) {
    for (char *p = path; *p; p++) {
        if (*p == '\\') *p = '/';
    }
}

static bool is_dir(const char *path) {
#ifdef _WIN32
    DWORD attr = GetFileAttributesA(path);
    if (attr == INVALID_FILE_ATTRIBUTES) return false;
    return (attr & FILE_ATTRIBUTE_DIRECTORY) != 0;
#else
    struct stat st;
    if (stat(path, &st) != 0) return false;
    return S_ISDIR(st.st_mode);
#endif
}

static bool file_exists(const char *path) {
#ifdef _WIN32
    DWORD attr = GetFileAttributesA(path);
    if (attr == INVALID_FILE_ATTRIBUTES) return false;
    return (attr & FILE_ATTRIBUTE_DIRECTORY) == 0;
#else
    struct stat st;
    if (stat(path, &st) != 0) return false;
    return S_ISREG(st.st_mode);
#endif
}

static int cmp_str(const void *a, const void *b) {
    const char *sa = *(const char **)a;
    const char *sb = *(const char **)b;
    return strcmp(sa, sb);
}

typedef struct StringList {
    char **items;
    size_t count;
    size_t cap;
} StringList;

static void strlist_add(StringList *list, const char *s) {
    if (list->count >= list->cap) {
        list->cap = list->cap == 0 ? 16 : list->cap * 2;
        list->items = realloc(list->items, list->cap * sizeof(char *));
    }
    list->items[list->count++] = strdup(s);
}

static void scan_dir_recursive(const char *base_dir, const char *sub_dir, StringList *out) {
    char search_dir[1024];
    if (sub_dir && sub_dir[0]) {
        snprintf(search_dir, sizeof(search_dir), "%s/%s", base_dir, sub_dir);
    } else {
        snprintf(search_dir, sizeof(search_dir), "%s", base_dir);
    }

#ifdef _WIN32
    char pattern[2048];
    snprintf(pattern, sizeof(pattern), "%s/*", search_dir);
    WIN32_FIND_DATAA fd;
    HANDLE h = FindFirstFileA(pattern, &fd);
    if (h == INVALID_HANDLE_VALUE) return;

    do {
        if (strcmp(fd.cFileName, ".") == 0 || strcmp(fd.cFileName, "..") == 0) continue;
        char rel_path[2048];
        if (sub_dir && sub_dir[0]) {
            snprintf(rel_path, sizeof(rel_path), "%s/%s", sub_dir, fd.cFileName);
        } else {
            snprintf(rel_path, sizeof(rel_path), "%s", fd.cFileName);
        }
        normalize_slashes(rel_path);

        if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            scan_dir_recursive(base_dir, rel_path, out);
        } else {
            size_t len = strlen(fd.cFileName);
            if (len > 3 && strcmp(fd.cFileName + len - 3, ".ax") == 0) {
                strlist_add(out, rel_path);
            }
        }
    } while (FindNextFileA(h, &fd));

    FindClose(h);
#else
    DIR *d = opendir(search_dir);
    if (!d) return;
    struct dirent *ent;
    while ((ent = readdir(d))) {
        if (strcmp(ent->d_name, ".") == 0 || strcmp(ent->d_name, "..") == 0) continue;
        char rel_path[1024];
        if (sub_dir && sub_dir[0]) {
            snprintf(rel_path, sizeof(rel_path), "%s/%s", sub_dir, ent->d_name);
        } else {
            snprintf(rel_path, sizeof(rel_path), "%s", ent->d_name);
        }
        char full[1024];
        snprintf(full, sizeof(full), "%s/%s", base_dir, rel_path);
        if (is_dir(full)) {
            scan_dir_recursive(base_dir, rel_path, out);
        } else {
            size_t len = strlen(ent->d_name);
            if (len > 3 && strcmp(ent->d_name + len - 3, ".ax") == 0) {
                strlist_add(out, rel_path);
            }
        }
    }
    closedir(d);
#endif
}

static void add_project_file(AxProject *proj, const char *disk_path, const char *display_path, const char *module_path, bool is_main, bool is_std) {
    if (proj->file_count >= proj->file_cap) {
        proj->file_cap = proj->file_cap == 0 ? 8 : proj->file_cap * 2;
        proj->files = realloc(proj->files, proj->file_cap * sizeof(AxProjectFile));
    }
    AxProjectFile *f = &proj->files[proj->file_count++];
    snprintf(f->disk_path, sizeof(f->disk_path), "%s", disk_path);
    normalize_slashes(f->disk_path);
    snprintf(f->display_path, sizeof(f->display_path), "%s", display_path);
    normalize_slashes(f->display_path);
    snprintf(f->module_path, sizeof(f->module_path), "%s", module_path);
    f->is_main = is_main;
    f->is_std = is_std;
}

static void derive_module_path(char *out, size_t out_cap, const char *rel_path) {
    const char *p = rel_path;
    if (strncmp(p, "src/", 4) == 0) p += 4;
    size_t len = strlen(p);
    if (len > 3 && strcmp(p + len - 3, ".ax") == 0) {
        len -= 3;
    }
    size_t i = 0;
    for (; i < len && i + 1 < out_cap; i++) {
        if (p[i] == '/' || p[i] == '\\') out[i] = '.';
        else out[i] = p[i];
    }
    out[i] = '\0';
}

static void emit_driver_diag(AxDiagSink *sink, AxDiagCode code) {
    if (!sink) return;
    AxDiagnostic d = {0};
    d.code = code;
    d.severity = AX_DIAG_ERROR;
    d.message = ax_diag_code_default_message(code);
    ax_diag_sink_report(sink, &d);
}

bool ax_project_discover(const char *input_path, const char *explicit_std_root, AxProject *proj, AxDiagSink *sink) {
    memset(proj, 0, sizeof(*proj));

    char norm_input[1024];
    snprintf(norm_input, sizeof(norm_input), "%s", input_path);
    normalize_slashes(norm_input);

    /* Discover std root according to ADR-0006 §8 */
    const char *std_root = ax_find_std_root(explicit_std_root);
    if (std_root) {
        proj->std_root = std_root;
    } else {
        /* If explicit_std_root was provided or if std is required and missing: emit AX_DRIVER_NO_STD */
        emit_driver_diag(sink, AX_DRIVER_NO_STD);
        return false;
    }

    if (is_dir(norm_input)) {
        proj->is_package = true;
        snprintf(proj->root_dir, sizeof(proj->root_dir), "%s", norm_input);

        char toml_path[2048];
        snprintf(toml_path, sizeof(toml_path), "%s/axiom.toml", norm_input);
        if (file_exists(toml_path)) {
            if (!ax_manifest_read(toml_path, &proj->manifest)) {
                emit_driver_diag(sink, AX_DRIVER_BAD_MANIFEST);
                return false;
            }
        } else {
            /* Package directory without axiom.toml */
            snprintf(proj->manifest.kind, sizeof(proj->manifest.kind), "exe");
            char *last = strrchr(norm_input, '/');
            snprintf(proj->manifest.name, sizeof(proj->manifest.name), "%.127s", last ? last + 1 : norm_input);
        }

        /* Scan src/ directory */
        char src_dir[2048];
        snprintf(src_dir, sizeof(src_dir), "%s/src", norm_input);
        if (!is_dir(src_dir)) {
            /* Maybe root itself has .ax files */
            snprintf(src_dir, sizeof(src_dir), "%s", norm_input);
        }

        StringList sl = {0};
        scan_dir_recursive(norm_input, "src", &sl);
        if (sl.count == 0) {
            scan_dir_recursive(norm_input, "", &sl);
        }

        /* Sort files lexicographically for determinism (AXD-060) */
        if (sl.count > 1) {
            qsort(sl.items, sl.count, sizeof(char *), cmp_str);
        }

        for (size_t i = 0; i < sl.count; i++) {
            char disk_path[2048];
            snprintf(disk_path, sizeof(disk_path), "%s/%s", norm_input, sl.items[i]);
            normalize_slashes(disk_path);

            char mod_path[256];
            derive_module_path(mod_path, sizeof(mod_path), sl.items[i]);

            bool is_main = (strcmp(sl.items[i], "src/main.ax") == 0 || strcmp(sl.items[i], "main.ax") == 0);
            add_project_file(proj, disk_path, sl.items[i], mod_path, is_main, false);
            free(sl.items[i]);
        }
        free(sl.items);
    } else {
        /* Single file input */
        proj->is_package = false;

        /* Check if inside a package src/ */
        char *src_pos = strstr(norm_input, "/src/");
        if (src_pos) {
            char root[1024];
            size_t root_len = (size_t)(src_pos - norm_input);
            memcpy(root, norm_input, root_len);
            root[root_len] = '\0';
            char toml_path[2048];
            snprintf(toml_path, sizeof(toml_path), "%s/axiom.toml", root);
            if (file_exists(toml_path)) {
                /* It's part of a package! Discover the package */
                return ax_project_discover(root, explicit_std_root, proj, sink);
            }
        }

        /* Standalone file */
        char mod_path[256];
        char *last = strrchr(norm_input, '/');
        const char *filename = last ? last + 1 : norm_input;
        derive_module_path(mod_path, sizeof(mod_path), filename);

        add_project_file(proj, norm_input, norm_input, mod_path, true, false);
    }

    /* Add core std files after user files if they exist */
    if (proj->std_root) {
        struct StdFile { const char *path; const char *vpath; const char *mod; };
        struct StdFile std_files[] = {
            {"core/option.ax", "<std>/core/option.ax", "std.core.option"},
            {"core/result.ax", "<std>/core/result.ax", "std.core.result"},
            {"core/prelude.ax", "<std>/core/prelude.ax", "std.core.prelude"}
        };
        for (size_t f = 0; f < 3; f++) {
            char disk[2048];
            snprintf(disk, sizeof(disk), "%s/%s", proj->std_root, std_files[f].path);
            normalize_slashes(disk);
            if (file_exists(disk)) {
                bool already = false;
                for (size_t i = 0; i < proj->file_count; i++) {
                    if (strcmp(proj->files[i].disk_path, disk) == 0) {
                        already = true;
                        break;
                    }
                }
                if (!already) {
                    add_project_file(proj, disk, std_files[f].vpath, std_files[f].mod, false, true);
                }
            }
        }
    }

    return true;
}

void ax_project_free(AxProject *proj) {
    if (proj->files) {
        free(proj->files);
        proj->files = NULL;
    }
    proj->file_count = 0;
    proj->file_cap = 0;
}
