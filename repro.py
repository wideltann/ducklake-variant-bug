# /// script
# requires-python = ">=3.12"
# dependencies = ["duckdb>=1.5.1", "testcontainers[postgres]"]
# ///
"""
Repro for unescaped single quotes in VARIANT column stats breaking
PostgreSQL catalog commits. Needs podman or docker running.
"""

import tempfile
from pathlib import Path

import duckdb
from testcontainers.postgres import PostgresContainer


def main():
    with PostgresContainer("postgres:16") as pg:
        connstr = (
            f"dbname={pg.dbname} host={pg.get_container_host_ip()} "
            f"port={pg.get_exposed_port(5432)} "
            f"user={pg.username} password={pg.password}"
        )
        data_path = Path(tempfile.mkdtemp(prefix="ducklake_repro_"))

        conn = duckdb.connect()
        conn.execute("INSTALL ducklake; LOAD ducklake; INSTALL postgres;")
        conn.execute(
            f"ATTACH 'ducklake:postgres:{connstr}' AS dl "
            f"(DATA_PATH '{data_path}/')"
        )
        conn.execute("USE dl")
        conn.execute("CREATE TABLE t (v VARIANT)")

        # need an initial insert so the second one has existing stats to merge with
        conn.execute("""INSERT INTO t VALUES ('[{"text": "hello"}]'::JSON::VARIANT)""")
        print("ok: insert without apostrophe")

        # this one has an apostrophe that becomes the new max, which blows up
        # because TrySerialize() doesn't escape the quote in the JSON blob
        try:
            conn.execute(
                """INSERT INTO t VALUES ('[{"text": "it''s broken"}]'::JSON::VARIANT)"""
            )
            print("ok: insert with apostrophe (fixed!)")
        except duckdb.TransactionException as e:
            print("FAIL: insert with apostrophe")
            print(f"  {e}")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
