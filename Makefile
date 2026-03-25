.PHONY: repro test-fix

# build ducklake from source with the fix applied, then point DUCKDB_BIN at it
DUCKDB_BIN ?= /tmp/ducklake-fix/build/release/duckdb

repro:
	uv run repro.py

test-fix:
	uv run test_fix.py $(DUCKDB_BIN)
