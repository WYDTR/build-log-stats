#include "config.h"
#include "helper.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

static void usage(FILE *stream) {
    fputs("Usage: app [--json] [--fail-on-error] [--] [FILE|-]\n"
          "Count diagnostic lines in a compiler/build log.\n"
          "With no FILE, or with '-', read standard input.\n"
          "Options: --help, --version, --json, --fail-on-error\n", stream);
}

int main(int argc, char **argv) {
    const char *path = NULL;
    int json = 0, fail_on_error = 0, positional = 0;
    FILE *input = stdin;
    LogStats stats;
    int result;

    for (int i = 1; i < argc; ++i) {
        if (!positional && strcmp(argv[i], "--") == 0) {
            positional = 1;
        } else if (!positional && strcmp(argv[i], "--help") == 0) {
            usage(stdout);
            return 0;
        } else if (!positional && strcmp(argv[i], "--version") == 0) {
            puts("build-log-stats " BUILD_LOG_STATS_VERSION);
            return 0;
        } else if (!positional && strcmp(argv[i], "--json") == 0) {
            json = 1;
        } else if (!positional && strcmp(argv[i], "--fail-on-error") == 0) {
            fail_on_error = 1;
        } else if (!positional && argv[i][0] == '-' && strcmp(argv[i], "-") != 0) {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            usage(stderr);
            return 2;
        } else if (path != NULL) {
            fputs("Only one input file is supported.\n", stderr);
            return 2;
        } else {
            path = argv[i];
        }
    }
    if (path != NULL && strcmp(path, "-") != 0) {
        input = fopen(path, "rb");
        if (input == NULL) {
            fprintf(stderr, "Cannot open %s: %s\n", path, strerror(errno));
            return 3;
        }
    }
    result = log_stats_collect(input, &stats);
    if (input != stdin && fclose(input) != 0 && result == LOG_STATS_OK) {
        result = LOG_STATS_READ_ERROR;
    }
    if (result != LOG_STATS_OK) {
        const char *message = result == LOG_STATS_MEMORY_ERROR ? "Out of memory" :
                              result == LOG_STATS_BINARY_INPUT ? "Input contains a NUL byte" :
                              "Cannot read input";
        fprintf(stderr, "%s\n", message);
        return 3;
    }
    if (json) {
        printf("{\"lines\":%zu,\"warnings\":%zu,\"errors\":%zu}\n",
               stats.lines, stats.warnings, stats.errors);
    } else {
        printf("lines=%zu warnings=%zu errors=%zu\n",
               stats.lines, stats.warnings, stats.errors);
    }
    if (fflush(stdout) != 0) {
        fputs("Cannot write output\n", stderr);
        return 3;
    }
    return fail_on_error && stats.errors > 0 ? 1 : 0;
}
