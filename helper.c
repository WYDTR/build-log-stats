#include "helper.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static int token_character(unsigned char ch) {
    return (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
           (ch >= '0' && ch <= '9') || ch == '_';
}

/* Remove complete ANSI CSI sequences, including compiler colour escapes. */
static void strip_ansi(char *line) {
    size_t read_pos = 0, write_pos = 0;
    while (line[read_pos] != '\0') {
        if ((unsigned char)line[read_pos] == 27 && line[read_pos + 1] == '[') {
            size_t end = read_pos + 2;
            while (line[end] != '\0' && (unsigned char)line[end] >= 0x20 &&
                   (unsigned char)line[end] <= 0x3f) {
                ++end;
            }
            if ((unsigned char)line[end] >= 0x40 && (unsigned char)line[end] <= 0x7e) {
                read_pos = end + 1;
                continue;
            }
        }
        line[write_pos++] = line[read_pos++];
    }
    line[write_pos] = '\0';
}

static int has_diagnostic(const char *line, const char *pattern) {
    const char *match = line;
    while ((match = strstr(match, pattern)) != NULL) {
        if (match == line || !token_character((unsigned char)match[-1])) {
            return 1;
        }
        ++match;
    }
    return 0;
}

static void record_line(char *line, LogStats *stats) {
    ++stats->lines;
    strip_ansi(line);
    /* Count one diagnostic per line, preferring errors over warnings. */
    if (has_diagnostic(line, "error:")) {
        ++stats->errors;
    } else if (has_diagnostic(line, "warning:")) {
        ++stats->warnings;
    }
}

int log_stats_collect(FILE *input, LogStats *stats) {
    size_t length = 0, capacity = 256;
    char *line = malloc(capacity);
    int ch;
    memset(stats, 0, sizeof(*stats));
    if (line == NULL) {
        return LOG_STATS_MEMORY_ERROR;
    }
    while ((ch = fgetc(input)) != EOF) {
        if (ch == 0) {
            free(line);
            return LOG_STATS_BINARY_INPUT;
        }
        if (ch == '\n') {
            line[length] = '\0';
            record_line(line, stats);
            length = 0;
            continue;
        }
        if (length + 1 >= capacity) {
            char *grown;
            if (capacity > SIZE_MAX / 2) {
                free(line);
                return LOG_STATS_MEMORY_ERROR;
            }
            capacity *= 2;
            grown = realloc(line, capacity);
            if (grown == NULL) {
                free(line);
                return LOG_STATS_MEMORY_ERROR;
            }
            line = grown;
        }
        line[length++] = (char)ch;
    }
    if (ferror(input)) {
        free(line);
        return LOG_STATS_READ_ERROR;
    }
    if (length > 0) {
        line[length] = '\0';
        record_line(line, stats);
    }
    free(line);
    return LOG_STATS_OK;
}
