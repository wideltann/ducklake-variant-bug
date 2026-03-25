# /// script
# requires-python = ">=3.12"
# dependencies = ["testcontainers[postgres]"]
# ///
"""
Tests the ducklake fix using the locally built duckdb CLI.
Pass the duckdb binary path as the first argument.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from testcontainers.postgres import PostgresContainer


def run_sql(duckdb_bin, sql):
    result = subprocess.run(
        [duckdb_bin, "-c", sql],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, result.stdout.strip()


def main():
    duckdb_bin = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ducklake-fix/build/release/duckdb"

    with PostgresContainer("postgres:16") as pg:
        connstr = (
            f"dbname={pg.dbname} host={pg.get_container_host_ip()} "
            f"port={pg.get_exposed_port(5432)} "
            f"user={pg.username} password={pg.password}"
        )
        data_path = Path(tempfile.mkdtemp(prefix="ducklake_repro_"))

        sql = f"""
INSTALL postgres;
ATTACH 'ducklake:postgres:{connstr}' AS dl (DATA_PATH '{data_path}/');
USE dl;
CREATE TABLE t (v VARIANT);
INSERT INTO t VALUES ('[{{"text": "hello"}}]'::JSON::VARIANT);
INSERT INTO t VALUES ('[{{"text": "it''s broken"}}]'::JSON::VARIANT);
SELECT * FROM t;
"""
        ok, output = run_sql(duckdb_bin, sql)
        if ok:
            print("ok: both inserts succeeded, fix works")
            print(output)
        else:
            print("FAIL: second insert blew up")
            print(output)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
