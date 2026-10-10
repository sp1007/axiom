#include "driver/manifest.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

static char *trim(char *s) {
    while (isspace((unsigned char)*s)) s++;
    if (*s == 0) return s;
    char *end = s + strlen(s) - 1;
    while (end > s && isspace((unsigned char)*end)) end--;
    end[1] = '\0';
    return s;
}

static void unquote(char *dst, size_t dst_cap, const char *src) {
    src = trim((char*)src);
    if (*src == '"' || *src == '\'') {
        char q = *src++;
        size_t i = 0;
        while (*src && *src != q && i + 1 < dst_cap) {
            dst[i++] = *src++;
        }
        dst[i] = '\0';
    } else {
        snprintf(dst, dst_cap, "%s", src);
    }
}

bool ax_manifest_read(const char *manifest_path, AxPackageManifest *out) {
    memset(out, 0, sizeof(*out));
    snprintf(out->kind, sizeof(out->kind), "exe");

    FILE *f = fopen(manifest_path, "rb");
    if (!f) return false;

    char line[512];
    char current_section[64] = "";
    bool found_package = false;

    while (fgets(line, sizeof(line), f)) {
        char *p = strchr(line, '#');
        if (p) *p = '\0';
        char *t = trim(line);
        if (*t == '\0') continue;

        if (*t == '[') {
            char *end = strchr(t, ']');
            if (end) {
                *end = '\0';
                snprintf(current_section, sizeof(current_section), "%s", trim(t + 1));
                if (strcmp(current_section, "package") == 0) {
                    found_package = true;
                }
            }
            continue;
        }

        if (strcmp(current_section, "package") == 0) {
            char *eq = strchr(t, '=');
            if (eq) {
                *eq = '\0';
                char *key = trim(t);
                char *val = trim(eq + 1);

                if (strcmp(key, "name") == 0) {
                    unquote(out->name, sizeof(out->name), val);
                } else if (strcmp(key, "version") == 0) {
                    unquote(out->version, sizeof(out->version), val);
                } else if (strcmp(key, "kind") == 0) {
                    unquote(out->kind, sizeof(out->kind), val);
                }
            }
        }
    }

    fclose(f);
    if (found_package && out->name[0] != '\0') {
        out->is_present = true;
        return true;
    }
    return false;
}
