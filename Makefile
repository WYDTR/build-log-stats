CC = gcc
CFLAGS = -O0
WARNINGS = -std=c11 -Wall -Wextra -Wpedantic

ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif

.PHONY: all clean test check-deps
all: app

app: main.o helper.o
	$(CC) $(CFLAGS) $(WARNINGS) main.o helper.o -o app

main.o: main.c helper.h config.h
	$(CC) $(CFLAGS) $(WARNINGS) -c main.c -o main.o

helper.o: helper.c helper.h rules.h
	$(CC) $(CFLAGS) $(WARNINGS) -c helper.c -o helper.o

test: app
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

check-deps:
	$(PYTHON) scripts/check_dependencies.py

clean:
	$(PYTHON) scripts/clean.py
