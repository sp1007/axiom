#include "interp/host.h"
#include "diag/diag.h"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define MAX_FILE_HANDLES 256
#define MAX_DIR_HANDLES 128

typedef struct {
    HANDLE h;
    bool open;
} InterpFileEntry;

typedef struct {
    HANDLE hFind;
    WIN32_FIND_DATAW ffd;
    bool has_entry;
    bool open;
} InterpDirEntry;

struct InterpHostState {
    char *args[256];
    size_t argc;
    InterpFileEntry file_table[MAX_FILE_HANDLES];
    InterpDirEntry dir_table[MAX_DIR_HANDLES];
    uint64_t last_monotonic_ns;
};

void ax_interp_host_init(InterpCtx *ctx, int argc, const char **argv) {
    if (!ctx) return;
    if (!ctx->host) {
        ctx->host = (InterpHostState*)calloc(1, sizeof(InterpHostState));
    }
    InterpHostState *st = ctx->host;
    if (!st) return;

#ifdef _WIN32
    int wargc = 0;
    LPWSTR *wargv = CommandLineToArgvW(GetCommandLineW(), &wargc);
    if (wargv) {
        int dash_dash = -1;
        for (int i = 0; i < wargc; i++) {
            if (wcscmp(wargv[i], L"--") == 0) {
                dash_dash = i;
                break;
            }
        }
        if (argc > 0 && argv && argv[0]) {
            st->args[st->argc++] = strdup(argv[0]);
        }
        if (dash_dash >= 0) {
            for (int i = dash_dash + 1; i < wargc && st->argc < 256; i++) {
                int u8len = WideCharToMultiByte(CP_UTF8, 0, wargv[i], -1, NULL, 0, NULL, NULL);
                if (u8len > 0) {
                    char *u8str = (char*)malloc((size_t)u8len);
                    if (u8str) {
                        WideCharToMultiByte(CP_UTF8, 0, wargv[i], -1, u8str, u8len, NULL, NULL);
                        st->args[st->argc++] = u8str;
                    }
                }
            }
        } else if (argc > 1 && argv) {
            for (int i = 1; i < argc && st->argc < 256; i++) {
                st->args[st->argc++] = strdup(argv[i]);
            }
        }
        LocalFree(wargv);
        return;
    }
#endif

    if (argc > 0 && argv) {
        for (int i = 0; i < argc && i < 256; i++) {
            st->args[i] = strdup(argv[i]);
            st->argc++;
        }
    }
}

static size_t ax_interp_args_count(InterpCtx *ctx) {
    return (ctx && ctx->host) ? ctx->host->argc : 0;
}

static int64_t ax_interp_arg(InterpCtx *ctx, size_t i, uint64_t buf_addr, size_t cap) {
    if (!ctx || !ctx->host) return -4;
    InterpHostState *st = ctx->host;
    if (i >= st->argc || !st->args[i]) return -4;
    size_t len = strlen(st->args[i]);
    if (cap > 0 && len > 0) {
        size_t to_write = len < cap ? len : cap;
        uint8_t *host_buf = ax_interp_validate_raw_ptr(ctx, buf_addr, to_write, 1);
        if (!ctx->failed) memcpy(host_buf, st->args[i], to_write);
    }
    return (int64_t)len;
}

static int allocate_file_handle(InterpCtx *ctx, HANDLE h) {
    if (!ctx || !ctx->host) return -1;
    InterpHostState *st = ctx->host;
    for (int i = 3; i < MAX_FILE_HANDLES; i++) {
        if (!st->file_table[i].open) {
            st->file_table[i].h = h;
            st->file_table[i].open = true;
            return i;
        }
    }
    return -1;
}

static int allocate_dir_handle(InterpCtx *ctx, HANDLE hFind, WIN32_FIND_DATAW *ffd) {
    if (!ctx || !ctx->host) return -1;
    InterpHostState *st = ctx->host;
    for (int i = 1; i < MAX_DIR_HANDLES; i++) {
        if (!st->dir_table[i].open) {
            st->dir_table[i].hFind = hFind;
            st->dir_table[i].ffd = *ffd;
            st->dir_table[i].has_entry = true;
            st->dir_table[i].open = true;
            return i + 1000;
        }
    }
    return -1;
}

static wchar_t *utf8_to_wchar(const char *u8, size_t len) {
    if (len == 0) {
        wchar_t *empty = (wchar_t*)malloc(sizeof(wchar_t));
        if (empty) empty[0] = L'\0';
        return empty;
    }
    int wlen = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, u8, (int)len, NULL, 0);
    if (wlen <= 0) return NULL;
    wchar_t *res = (wchar_t*)malloc(((size_t)wlen + 1) * sizeof(wchar_t));
    if (!res) return NULL;
    MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, u8, (int)len, res, wlen);
    res[wlen] = L'\0';
    return res;
}

static char *wchar_to_utf8(const wchar_t *wstr, size_t *out_len) {
    if (!wstr) return NULL;
    int u8len = WideCharToMultiByte(CP_UTF8, 0, wstr, -1, NULL, 0, NULL, NULL);
    if (u8len <= 0) return NULL;
    char *res = (char*)malloc((size_t)u8len);
    if (!res) return NULL;
    WideCharToMultiByte(CP_UTF8, 0, wstr, -1, res, u8len, NULL, NULL);
    if (out_len) *out_len = (size_t)(u8len > 0 ? u8len - 1 : 0);
    return res;
}

static uint64_t ax_interp_monotonic_ns(InterpCtx *ctx) {
    LARGE_INTEGER count, freq;
    QueryPerformanceCounter(&count);
    QueryPerformanceFrequency(&freq);
    uint64_t ns = 0;
    if (freq.QuadPart > 0) {
        ns = (uint64_t)(((double)count.QuadPart / (double)freq.QuadPart) * 1000000000.0);
    }
    if (ctx && ctx->host) {
        if (ns < ctx->host->last_monotonic_ns) {
            ns = ctx->host->last_monotonic_ns;
        } else {
            ctx->host->last_monotonic_ns = ns;
        }
    }
    return ns;
}

void ax_interp_host_cleanup(InterpCtx *ctx) {
    if (!ctx || !ctx->host) return;
    InterpHostState *st = ctx->host;
    for (int i = 3; i < MAX_FILE_HANDLES; i++) {
        if (st->file_table[i].open) {
            CloseHandle(st->file_table[i].h);
            st->file_table[i].open = false;
        }
    }
    for (int i = 1; i < MAX_DIR_HANDLES; i++) {
        if (st->dir_table[i].open) {
            FindClose(st->dir_table[i].hFind);
            st->dir_table[i].open = false;
            st->dir_table[i].has_entry = false;
        }
    }
    for (size_t i = 0; i < st->argc; i++) {
        if (st->args[i]) {
            free(st->args[i]);
            st->args[i] = NULL;
        }
    }
    st->argc = 0;
    free(st);
    ctx->host = NULL;
}

bool ax_interp_eval_host_intrinsic(InterpCtx *ctx, StrView name, const uint64_t *args, size_t arg_count, AxInterpValue *out_ret) {
    (void)arg_count;

    if (ax_sv_eq_cstr(name, "heap_alloc")) {
        uint64_t size = args[0];
        uint64_t align = args[1];
        if (size == 0) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }
        if (align == 0 || (align & (align - 1)) != 0 || align > 4096) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }
        size_t alloc_bytes = size < 16 ? 16 : (size_t)size;
        uint8_t *mem = (uint8_t*)calloc(1, alloc_bytes);
        if (!mem) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }
        InterpAlloc *a = ax_interp_register_alloc(ctx, mem, size, (uint32_t)align, -1);
        if (out_ret) out_ret->vals[0] = a->base_addr;
        return true;
    }

    if (ax_sv_eq_cstr(name, "heap_realloc")) {
        uint64_t p = args[0];
        uint64_t old_size = args[1];
        uint64_t new_size = args[2];
        uint64_t align = args[3];

        if (p == 0) {
            // Behave like heap_alloc
            uint8_t *mem = (uint8_t*)calloc(1, new_size < 16 ? 16 : (size_t)new_size);
            if (!mem) {
                if (out_ret) out_ret->vals[0] = 0;
                return true;
            }
            InterpAlloc *a = ax_interp_register_alloc(ctx, mem, new_size, (uint32_t)align, -1);
            if (out_ret) out_ret->vals[0] = a->base_addr;
            return true;
        }
        if (new_size == 0) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }

        InterpAlloc *found = NULL;
        for (size_t i = 0; i < ctx->alloc_count; i++) {
            if (ctx->allocs[i].base_addr == p) {
                found = &ctx->allocs[i];
                break;
            }
        }
        if (!found || !found->is_live || found->call_depth != -1) {
            ax_interp_report_ub(ctx, "use of dangling pointer (use-after-free)");
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }

        size_t alloc_bytes = new_size < 16 ? 16 : (size_t)new_size;
        uint8_t *new_mem = (uint8_t*)calloc(1, alloc_bytes);
        if (!new_mem) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }

        size_t copy_sz = old_size < new_size ? (size_t)old_size : (size_t)new_size;
        if (found->size < copy_sz) copy_sz = (size_t)found->size;
        if (copy_sz > 0 && found->host_ptr) {
            memcpy(new_mem, found->host_ptr, copy_sz);
        }
        if (found->host_ptr) {
            free(found->host_ptr);
        }
        found->is_live = false;
        found->host_ptr = NULL;

        InterpAlloc *na = ax_interp_register_alloc(ctx, new_mem, new_size, (uint32_t)align, -1);
        if (out_ret) out_ret->vals[0] = na->base_addr;
        return true;
    }

    if (ax_sv_eq_cstr(name, "heap_free")) {
        uint64_t p = args[0];
        (void)args[1]; // size
        (void)args[2]; // align
        if (p == 0) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }
        InterpAlloc *found = NULL;
        for (size_t i = 0; i < ctx->alloc_count; i++) {
            if (ctx->allocs[i].base_addr == p) {
                found = &ctx->allocs[i];
                break;
            }
        }
        if (!found) {
            ax_interp_report_ub(ctx, "pointer access to unmapped memory");
            return true;
        }
        if (!found->is_live) {
            ax_interp_report_ub(ctx, "use of dangling pointer (use-after-free)");
            return true;
        }
        if (found->call_depth != -1) {
            ax_interp_report_ub(ctx, "heap_free called on non-heap allocation");
            return true;
        }
        if (found->host_ptr) {
            free(found->host_ptr);
        }
        found->is_live = false;
        found->host_ptr = NULL;
        if (out_ret) out_ret->vals[0] = 0;
        return true;
    }

    if (ax_sv_eq_cstr(name, "stdio")) {
        uint64_t which = args[0];
        if (which <= 2) {
            if (out_ret) out_ret->vals[0] = which;
        } else {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
        }
        return true;
    }

    if (ax_sv_eq_cstr(name, "open")) {
        uint64_t path_addr = args[0];
        uint64_t path_len = args[1];
        uint32_t mode = (uint32_t)args[2];

        uint8_t *path_host = ax_interp_validate_raw_ptr(ctx, path_addr, path_len, 1);
        if (ctx->failed) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        wchar_t *wpath = utf8_to_wchar((const char*)path_host, (size_t)path_len);
        if (!wpath) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        DWORD desired_access = 0;
        DWORD creation_disposition = 0;
        if (mode == 0) {
            desired_access = GENERIC_READ;
            creation_disposition = OPEN_EXISTING;
        } else if (mode == 1) {
            desired_access = GENERIC_WRITE | GENERIC_READ;
            creation_disposition = CREATE_ALWAYS;
        } else if (mode == 2) {
            desired_access = FILE_APPEND_DATA | GENERIC_READ;
            creation_disposition = OPEN_ALWAYS;
        } else {
            free(wpath);
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        HANDLE h = CreateFileW(wpath, desired_access, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL, creation_disposition, FILE_ATTRIBUTE_NORMAL, NULL);
        free(wpath);

        if (h == INVALID_HANDLE_VALUE) {
            DWORD err = GetLastError();
            int64_t code = -9;
            if (err == ERROR_FILE_NOT_FOUND || err == ERROR_PATH_NOT_FOUND) code = -1;
            else if (err == ERROR_ACCESS_DENIED) code = -2;
            else if (err == ERROR_FILE_EXISTS || err == ERROR_ALREADY_EXISTS) code = -3;
            if (out_ret) out_ret->vals[0] = (uint64_t)code;
            return true;
        }

        int hid = allocate_file_handle(ctx, h);
        if (hid < 0) {
            CloseHandle(h);
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }
        if (mode == 2) {
            SetFilePointer(h, 0, NULL, FILE_END);
        }
        if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)hid;
        return true;
    }

    if (ax_sv_eq_cstr(name, "read")) {
        int64_t h = (int64_t)args[0];
        uint64_t buf_addr = args[1];
        uint64_t cap = args[2];

        if (cap == 0) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }

        uint8_t *buf_host = ax_interp_validate_raw_ptr(ctx, buf_addr, cap, 1);
        if (ctx->failed) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        HANDLE win_h = INVALID_HANDLE_VALUE;
        if (h == 0) {
            win_h = GetStdHandle(STD_INPUT_HANDLE);
        } else if (h >= 3 && h < MAX_FILE_HANDLES && ctx->host && ctx->host->file_table[h].open) {
            win_h = ctx->host->file_table[h].h;
        } else {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        DWORD read_bytes = 0;
        if (!ReadFile(win_h, buf_host, (DWORD)cap, &read_bytes, NULL)) {
            DWORD err = GetLastError();
            if (err == ERROR_HANDLE_EOF || err == ERROR_BROKEN_PIPE) {
                if (out_ret) out_ret->vals[0] = 0;
                return true;
            }
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }
        if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)read_bytes;
        return true;
    }

    if (ax_sv_eq_cstr(name, "write")) {
        int64_t h = (int64_t)args[0];
        uint64_t p_addr = args[1];
        uint64_t len = args[2];

        if (len == 0) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }

        uint8_t *p_host = ax_interp_validate_raw_ptr(ctx, p_addr, len, 1);
        if (ctx->failed) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        HANDLE win_h = INVALID_HANDLE_VALUE;
        bool is_stdio = false;
        if (h == 1) {
            win_h = GetStdHandle(STD_OUTPUT_HANDLE);
            is_stdio = true;
        } else if (h == 2) {
            win_h = GetStdHandle(STD_ERROR_HANDLE);
            is_stdio = true;
        } else if (h >= 3 && h < MAX_FILE_HANDLES && ctx->host && ctx->host->file_table[h].open) {
            win_h = ctx->host->file_table[h].h;
        } else {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        if (is_stdio) {
            DWORD mode = 0;
            if (GetConsoleMode(win_h, &mode)) {
                int wlen = MultiByteToWideChar(CP_UTF8, 0, (const char*)p_host, (int)len, NULL, 0);
                if (wlen > 0) {
                    wchar_t *wbuf = (wchar_t*)malloc(((size_t)wlen + 1) * sizeof(wchar_t));
                    if (wbuf) {
                        MultiByteToWideChar(CP_UTF8, 0, (const char*)p_host, (int)len, wbuf, wlen);
                        DWORD wwritten = 0;
                        WriteConsoleW(win_h, wbuf, (DWORD)wlen, &wwritten, NULL);
                        free(wbuf);
                    }
                }
                if (out_ret) out_ret->vals[0] = len;
                return true;
            }
        }

        DWORD written = 0;
        if (!WriteFile(win_h, p_host, (DWORD)len, &written, NULL)) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }
        if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)written;
        return true;
    }

    if (ax_sv_eq_cstr(name, "close")) {
        int64_t h = (int64_t)args[0];
        if (h >= 3 && h < MAX_FILE_HANDLES && ctx->host && ctx->host->file_table[h].open) {
            CloseHandle(ctx->host->file_table[h].h);
            ctx->host->file_table[h].open = false;
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }
        if (h >= 0 && h <= 2) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }
        if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
        return true;
    }

    if (ax_sv_eq_cstr(name, "file_size")) {
        int64_t h = (int64_t)args[0];
        if (h < 3 || h >= MAX_FILE_HANDLES || !ctx->host || !ctx->host->file_table[h].open) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }
        LARGE_INTEGER li;
        if (GetFileSizeEx(ctx->host->file_table[h].h, &li)) {
            if (out_ret) out_ret->vals[0] = (uint64_t)li.QuadPart;
        } else {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
        }
        return true;
    }

    if (ax_sv_eq_cstr(name, "args_count")) {
        if (out_ret) out_ret->vals[0] = (uint64_t)ax_interp_args_count(ctx);
        return true;
    }

    if (ax_sv_eq_cstr(name, "arg")) {
        size_t i = (size_t)args[0];
        uint64_t buf_addr = args[1];
        size_t cap = (size_t)args[2];
        int64_t res = ax_interp_arg(ctx, i, buf_addr, cap);
        if (out_ret) out_ret->vals[0] = (uint64_t)res;
        return true;
    }

    if (ax_sv_eq_cstr(name, "env_get")) {
        uint64_t name_addr = args[0];
        uint64_t name_len = args[1];
        uint64_t buf_addr = args[2];
        uint64_t cap = args[3];

        uint8_t *name_host = ax_interp_validate_raw_ptr(ctx, name_addr, name_len, 1);
        if (ctx->failed) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }
        wchar_t *wname = utf8_to_wchar((const char*)name_host, (size_t)name_len);
        if (!wname) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }
        DWORD needed = GetEnvironmentVariableW(wname, NULL, 0);
        if (needed == 0) {
            DWORD err = GetLastError();
            free(wname);
            int64_t c = (err == ERROR_ENVVAR_NOT_FOUND) ? -1 : -9;
            if (out_ret) out_ret->vals[0] = (uint64_t)c;
            return true;
        }
        wchar_t *wval = (wchar_t*)malloc(((size_t)needed + 1) * sizeof(wchar_t));
        if (!wval) {
            free(wname);
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }
        GetEnvironmentVariableW(wname, wval, needed);
        free(wname);
        size_t u8len = 0;
        char *u8val = wchar_to_utf8(wval, &u8len);
        free(wval);
        if (!u8val) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }
        if (cap > 0 && u8len > 0) {
            size_t to_write = u8len < cap ? u8len : (size_t)cap;
            uint8_t *host_buf = ax_interp_validate_raw_ptr(ctx, buf_addr, to_write, 1);
            if (!ctx->failed) memcpy(host_buf, u8val, to_write);
        }
        free(u8val);
        if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)u8len;
        return true;
    }

    if (ax_sv_eq_cstr(name, "exe_path")) {
        uint64_t buf_addr = args[0];
        uint64_t cap = args[1];

        wchar_t wbuf[2048];
        DWORD len = GetModuleFileNameW(NULL, wbuf, 2048);
        if (len == 0) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }
        size_t u8len = 0;
        char *u8 = wchar_to_utf8(wbuf, &u8len);
        if (!u8) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }
        for (size_t i = 0; i < u8len; i++) {
            if (u8[i] == '\\') u8[i] = '/';
        }
        if (cap > 0 && u8len > 0) {
            size_t to_write = u8len < cap ? u8len : (size_t)cap;
            uint8_t *host_buf = ax_interp_validate_raw_ptr(ctx, buf_addr, to_write, 1);
            if (!ctx->failed) memcpy(host_buf, u8, to_write);
        }
        free(u8);
        if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)u8len;
        return true;
    }

    if (ax_sv_eq_cstr(name, "exit")) {
        int code = (int)(int32_t)args[0];
        ctx->failed = true;
        ctx->exit_code = code;
        if (out_ret) out_ret->vals[0] = (uint64_t)code;
        return true;
    }

    if (ax_sv_eq_cstr(name, "remove")) {
        uint64_t path_addr = args[0];
        uint64_t path_len = args[1];
        uint8_t *path_host = ax_interp_validate_raw_ptr(ctx, path_addr, path_len, 1);
        if (ctx->failed) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }
        wchar_t *wpath = utf8_to_wchar((const char*)path_host, (size_t)path_len);
        if (!wpath) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }
        if (DeleteFileW(wpath)) {
            free(wpath);
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }
        DWORD err = GetLastError();
        if (err == ERROR_ACCESS_DENIED) {
            if (RemoveDirectoryW(wpath)) {
                free(wpath);
                if (out_ret) out_ret->vals[0] = 0;
                return true;
            }
            err = GetLastError();
        }
        free(wpath);
        int64_t c = -9;
        if (err == ERROR_FILE_NOT_FOUND || err == ERROR_PATH_NOT_FOUND) c = -1;
        else if (err == ERROR_ACCESS_DENIED) c = -2;
        if (out_ret) out_ret->vals[0] = (uint64_t)c;
        return true;
    }

    if (ax_sv_eq_cstr(name, "mkdir")) {
        uint64_t path_addr = args[0];
        uint64_t path_len = args[1];
        uint8_t *path_host = ax_interp_validate_raw_ptr(ctx, path_addr, path_len, 1);
        if (ctx->failed) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }
        wchar_t *wpath = utf8_to_wchar((const char*)path_host, (size_t)path_len);
        if (!wpath) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }
        if (CreateDirectoryW(wpath, NULL)) {
            free(wpath);
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }
        DWORD err = GetLastError();
        free(wpath);
        int64_t c = -9;
        if (err == ERROR_ALREADY_EXISTS) c = -3;
        else if (err == ERROR_PATH_NOT_FOUND) c = -1;
        else if (err == ERROR_ACCESS_DENIED) c = -2;
        if (out_ret) out_ret->vals[0] = (uint64_t)c;
        return true;
    }

    if (ax_sv_eq_cstr(name, "metadata")) {
        uint64_t path_addr = args[0];
        uint64_t path_len = args[1];
        uint64_t out_addr = args[2];

        uint8_t *path_host = ax_interp_validate_raw_ptr(ctx, path_addr, path_len, 1);
        uint8_t *out_host = ax_interp_validate_raw_ptr(ctx, out_addr, 16, 8);
        if (ctx->failed) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        wchar_t *wpath = utf8_to_wchar((const char*)path_host, (size_t)path_len);
        if (!wpath) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        WIN32_FILE_ATTRIBUTE_DATA data;
        if (!GetFileAttributesExW(wpath, GetFileExInfoStandard, &data)) {
            DWORD err = GetLastError();
            free(wpath);
            int64_t c = -9;
            if (err == ERROR_FILE_NOT_FOUND || err == ERROR_PATH_NOT_FOUND) c = -1;
            else if (err == ERROR_ACCESS_DENIED) c = -2;
            if (out_ret) out_ret->vals[0] = (uint64_t)c;
            return true;
        }
        free(wpath);

        uint64_t kind = 1;
        if (data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
            kind = 2;
        } else if (data.dwFileAttributes & (FILE_ATTRIBUTE_DEVICE | FILE_ATTRIBUTE_REPARSE_POINT)) {
            kind = 3;
        }
        uint64_t size = ((uint64_t)data.nFileSizeHigh << 32) | (uint64_t)data.nFileSizeLow;

        uint64_t *out_words = (uint64_t*)out_host;
        out_words[0] = kind;
        out_words[1] = size;
        if (out_ret) out_ret->vals[0] = 0;
        return true;
    }

    if (ax_sv_eq_cstr(name, "dir_open")) {
        uint64_t path_addr = args[0];
        uint64_t path_len = args[1];

        uint8_t *path_host = ax_interp_validate_raw_ptr(ctx, path_addr, path_len, 1);
        if (ctx->failed) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        wchar_t *wpath = utf8_to_wchar((const char*)path_host, (size_t)path_len);
        if (!wpath) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }

        size_t wlen = wcslen(wpath);
        wchar_t *search_pattern = (wchar_t*)malloc((wlen + 4) * sizeof(wchar_t));
        if (!search_pattern) {
            free(wpath);
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }
        wcscpy(search_pattern, wpath);
        if (wlen > 0 && (search_pattern[wlen - 1] == L'/' || search_pattern[wlen - 1] == L'\\')) {
            wcscat(search_pattern, L"*");
        } else {
            wcscat(search_pattern, L"\\*");
        }
        free(wpath);

        WIN32_FIND_DATAW ffd;
        HANDLE hFind = FindFirstFileW(search_pattern, &ffd);
        free(search_pattern);

        if (hFind == INVALID_HANDLE_VALUE) {
            DWORD err = GetLastError();
            int64_t c = -9;
            if (err == ERROR_FILE_NOT_FOUND || err == ERROR_PATH_NOT_FOUND) c = -1;
            else if (err == ERROR_ACCESS_DENIED) c = -2;
            if (out_ret) out_ret->vals[0] = (uint64_t)c;
            return true;
        }

        int dhid = allocate_dir_handle(ctx, hFind, &ffd);
        if (dhid < 0) {
            FindClose(hFind);
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }
        if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)dhid;
        return true;
    }

    if (ax_sv_eq_cstr(name, "dir_next")) {
        int64_t dhid = (int64_t)args[0];
        uint64_t buf_addr = args[1];
        uint64_t cap = args[2];

        int slot_idx = (int)(dhid - 1000);
        if (!ctx->host || slot_idx < 1 || slot_idx >= MAX_DIR_HANDLES || !ctx->host->dir_table[slot_idx].open) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
            return true;
        }
        InterpDirEntry *entry = &ctx->host->dir_table[slot_idx];

        while (entry->has_entry && (wcscmp(entry->ffd.cFileName, L".") == 0 || wcscmp(entry->ffd.cFileName, L"..") == 0)) {
            if (!FindNextFileW(entry->hFind, &entry->ffd)) {
                entry->has_entry = false;
                break;
            }
        }

        if (!entry->has_entry) {
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }

        size_t n = 0;
        char *name_u8 = wchar_to_utf8(entry->ffd.cFileName, &n);
        if (!name_u8) {
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-9;
            return true;
        }

        if (n > cap) {
            // When n > cap, the entry is not consumed
            free(name_u8);
            if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)n;
            return true;
        }

        uint8_t *host_buf = ax_interp_validate_raw_ptr(ctx, buf_addr, n, 1);
        if (!ctx->failed && host_buf) {
            memcpy(host_buf, name_u8, n);
        }
        free(name_u8);

        // Advance to next entry
        if (!FindNextFileW(entry->hFind, &entry->ffd)) {
            entry->has_entry = false;
        }

        if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)n;
        return true;
    }

    if (ax_sv_eq_cstr(name, "dir_close")) {
        int64_t dhid = (int64_t)args[0];
        int slot_idx = (int)(dhid - 1000);
        if (ctx->host && slot_idx >= 1 && slot_idx < MAX_DIR_HANDLES && ctx->host->dir_table[slot_idx].open) {
            FindClose(ctx->host->dir_table[slot_idx].hFind);
            ctx->host->dir_table[slot_idx].open = false;
            ctx->host->dir_table[slot_idx].has_entry = false;
            if (out_ret) out_ret->vals[0] = 0;
            return true;
        }
        if (out_ret) out_ret->vals[0] = (uint64_t)(int64_t)-4;
        return true;
    }

    if (ax_sv_eq_cstr(name, "monotonic_ns")) {
        if (out_ret) out_ret->vals[0] = ax_interp_monotonic_ns(ctx);
        return true;
    }

    return false;
}
