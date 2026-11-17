#ifndef BUILD_LOG_STATS_HELPER_H
#define BUILD_LOG_STATS_HELPER_H

#include <stddef.h>
#include <stdio.h>

typedef struct {
    size_t lines;
    size_t warnings;
    size_t errors;
} LogStats;

enum {
    LOG_STATS_OK = 0,
    LOG_STATS_READ_ERROR = 1,
    LOG_STATS_MEMORY_ERROR = 2,
    LOG_STATS_BINARY_INPUT = 3
};

int log_stats_collect(FILE *input, LogStats *stats);

#endif
