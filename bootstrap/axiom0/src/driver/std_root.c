#include "driver/std_root.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <sys/stat.h>
#endif

static void normalize_slashes(char *path) {
    for (char *p = path; *p; p++) {
        if (*p == '\\') *p = '/';
    }
}

static bool is_directory(const char *path) {
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

static bool get_exe_dir(char *out, size_t out_cap) {
#ifdef _WIN32
    DWORD len = GetModuleFileNameA(NULL, out, (DWORD)out_cap);
    if (len == 0 || len >= out_cap) return false;
    normalize_slashes(out);
    char *last = strrchr(out, '/');
    if (last) *last = '\0';
    return true;
#else
    ssize_t len = readlink("/proc/self/exe", out, out_cap - 1);
    if (len <= 0) return false;
    out[len] = '\0';
    char *last = strrchr(out, '/');
    if (last) *last = '\0';
    return true;
#endif
}

static char s_std_root_buf[2048];

const char *ax_find_std_root(const char *explicit_flag) {
    /* 1. Explicit flag (--std-root <dir>) */
    if (explicit_flag && explicit_flag[0] != '\0') {
        if (is_directory(explicit_flag)) {
            snprintf(s_std_root_buf, sizeof(s_std_root_buf), "%s", explicit_flag);
            normalize_slashes(s_std_root_buf);
            return s_std_root_buf;
        }
        return NULL;
    }

    /* 2. Environment variable AXIOM_STD */
    const char *env_std = getenv("AXIOM_STD");
    if (env_std && env_std[0] != '\0') {
        if (is_directory(env_std)) {
            snprintf(s_std_root_buf, sizeof(s_std_root_buf), "%s", env_std);
            normalize_slashes(s_std_root_buf);
            return s_std_root_buf;
        }
    }

    /* 3. <exe dir>/../std & 4. <exe dir>/std */
    char exe_dir[1024];
    if (get_exe_dir(exe_dir, sizeof(exe_dir))) {
        char candidate[2048];
        snprintf(candidate, sizeof(candidate), "%s/../std", exe_dir);
        if (is_directory(candidate)) {
            snprintf(s_std_root_buf, sizeof(s_std_root_buf), "%s", candidate);
            normalize_slashes(s_std_root_buf);
            return s_std_root_buf;
        }

        snprintf(candidate, sizeof(candidate), "%s/std", exe_dir);
        if (is_directory(candidate)) {
            snprintf(s_std_root_buf, sizeof(s_std_root_buf), "%s", candidate);
            normalize_slashes(s_std_root_buf);
            return s_std_root_buf;
        }
    }

    return NULL;
}
