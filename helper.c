#include "helper.h"
#include "rules.h"

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
    for (size_t start = 0; line[start] != '\0'; ++start) {
        size_t pos = 0;
        if (start > 0 && token_character((unsigned char)line[start - 1])) {
            continue;
        }
        while (pattern[pos] != '\0' && line[start + pos] != '\0') {
            unsigned char ch = (unsigned char)line[start + pos];
#if LOG_STATS_IGNORE_CASE
            if (ch >= 'A' && ch <= 'Z') {
                ch = (unsigned char)(ch - 'A' + 'a');
            }
#endif
            if (ch != (unsigned char)pattern[pos]) {
                break;
            }
            ++pos;
        }
        if (pattern[pos] == '\0') {
            return 1;
        }
    }
    return 0;
}

static void record_line(char *line, LogStats *stats) {
    ++stats->lines;
    strip_ansi(line);
    /* Count one diagnostic per line: error > warning > note. */
    if (has_diagnostic(line, "error:")) {
        ++stats->errors;
    } else if (has_diagnostic(line, "warning:")) {
        ++stats->warnings;
#if LOG_STATS_COUNT_NOTES
    } else if (has_diagnostic(line, "note:")) {
        ++stats->notes;
#endif
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
