# ducklake variant stats single-quote bug

When using a PostgreSQL metadata catalog, VARIANT columns blow up on commit
if a shredded string field's min/max stat contains a single quote.
The `extra_stats` JSON in `ducklake_table_column_stats` embeds the raw
min/max without escaping, so PostgreSQL gets broken SQL.

The per-file stats (`ducklake_file_variant_stats`) *do* escape correctly
in the same transaction, so this is just a missed spot.

## running it

Needs podman or docker.

```bash
make repro
# or: uv run repro.py
```

## expected

Both inserts succeed.

## actual

```
ok: insert without apostrophe
FAIL: insert with apostrophe
```

The second insert makes `it's broken` the new max for the shredded
`text` field. The unescaped apostrophe in the stats JSON breaks the
SQL literal.

## fix

`fix.patch` has the two-line fix — use `DuckLakeUtil::SQLLiteralToString()`
instead of raw single-quote wrapping. Apply it to the ducklake source:

```bash
cd /path/to/ducklake
git apply /path/to/fix.patch
```

## where the bug is

`TrySerialize()` in `src/storage/statistics/ducklake_variant_stats.cpp`:

```cpp
result = "'" + out + "'";
```

`out` has raw values like `"max":"it's broken"`. Wrapping that in single
quotes without escaping is the problem. `DuckLakeUtil::SQLLiteralToString()`
(in `src/common/ducklake_util.cpp`) already does `Replace("'", "''")`
and is used everywhere else.
