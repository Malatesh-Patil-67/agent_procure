from __future__ import annotations

from pathlib import Path

import duckdb


def stage_operating_data(raw_directory: Path, database_path: Path) -> None:
    """Build a portable DuckDB staging layer before operational data moves to Postgres."""
    connection = duckdb.connect(str(database_path))
    try:
        connection.execute("CREATE OR REPLACE TABLE delivery_history AS SELECT * FROM read_csv_auto(?)", [str(raw_directory / "delivery_history.csv")])
        connection.execute("CREATE OR REPLACE TABLE defect_history AS SELECT * FROM read_csv_auto(?)", [str(raw_directory / "defect_history.csv")])
        connection.execute("CREATE OR REPLACE TABLE demand_forecast AS SELECT * FROM read_csv_auto(?)", [str(raw_directory / "demand_forecast.csv")])
    finally:
        connection.close()
