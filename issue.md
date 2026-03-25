### What happens?

Writing a VARIANT column to a DuckLake with a PostgreSQL metadata catalog
fails when a shredded string field's min/max stat contains a single quote.
The `ducklake_table_column_stats` `extra_stats` JSON embeds the raw values
without escaping, so PostgreSQL gets a syntax error.

The per-file stats in `ducklake_file_variant_stats` do escape correctly
(`'it''s broken'`) in the same transaction, so this is just a missed spot.

Related: #790 (same kind of escaping bug, fixed for data inlining).

### To Reproduce

Repo with testcontainers script: https://github.com/wideltann/ducklake-variant-bug

```sql
ATTACH 'ducklake:postgres:dbname=...' AS dl (DATA_PATH '/tmp/files/');
USE dl;
CREATE TABLE t (v VARIANT);
INSERT INTO t VALUES ('[{"text": "hello"}]'::JSON::VARIANT);
-- works

INSERT INTO t VALUES ('[{"text": "it''s broken"}]'::JSON::VARIANT);
-- fails: syntax error at or near "s"
-- ...,"min":"hello","max":"it's broken",...
--                          ^ unescaped quote
```

### Where the bug is

`TrySerialize()` in `src/storage/statistics/ducklake_variant_stats.cpp`:

```cpp
result = "'" + out + "'";
```

Should use `DuckLakeUtil::SQLLiteralToString(out)` (which does
`Replace("'", "''")`) like everywhere else.

### Environment

- DuckDB: v1.5.1
- DuckLake: latest (via `INSTALL ducklake`)
- PostgreSQL: 16
- OS: macOS arm64
