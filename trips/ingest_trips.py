#!/usr/bin/env python
# coding: utf-8

import click
import pyarrow.parquet as pq
import pandas as pd
from sqlalchemy import create_engine
import fsspec


DEFAULT_PREFIX = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
DEFAULT_FILE = DEFAULT_PREFIX + "green_tripdata_2025-11.parquet"


def _apply_type_conversions(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype({
        "VendorID": "Int64",
        "RatecodeID": "Int64",
        "PULocationID": "Int64",
        "DOLocationID": "Int64",
        "passenger_count": "Int64",
        "payment_type": "Int64",
        "trip_type": "Int64",
        "store_and_fwd_flag": "object",
    })


@click.command()
@click.option("--file-path", default=DEFAULT_FILE, show_default=True,
              help="HTTP(S) URL or local path to the parquet file")
@click.option("--pg-user", default="root", show_default=True,
              help="Postgres user")
@click.option("--pg-pass", default="root", show_default=True,
              help="Postgres password")
@click.option("--pg-host", default="localhost", show_default=True,
              help="Postgres host")
@click.option("--pg-port", default=5432, type=int, show_default=True,
              help="Postgres port")
@click.option("--pg-db", default="ny_taxi", show_default=True,
              help="Postgres database")
@click.option("--table-name", default="green_taxi_data", show_default=True,
              help="Destination table name in the database")
@click.option("--limit-row-groups", type=int, default=None,
              help="Optional: limit how many row groups to process")
def main(file_path: str, pg_user: str, pg_pass: str, pg_host: str, pg_port: int, pg_db: str, table_name: str, limit_row_groups: int):
    """Ingest parquet row groups into a SQL database with configurable options."""

    db_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    engine = create_engine(db_url)

    # Open parquet file with fsspec
    fs = fsspec.filesystem('http')
    parquet_file = pq.ParquetFile(fs.open(file_path))

    # Read FIRST row group to get schema and create table
    click.echo("Creating table schema...")
    first_chunk = parquet_file.read_row_group(0).to_pandas()
    first_chunk = _apply_type_conversions(first_chunk)

    # Create table with proper schema (no rows)
    first_chunk.head(n=0).to_sql(
        name=table_name,
        con=engine,
        if_exists='replace',
        index=False,
    )

    total = parquet_file.num_row_groups
    click.echo(f"Table created. Processing {total} row groups...")

    # Process row groups (optionally limited)
    for i in range(total):
        if limit_row_groups is not None and i >= limit_row_groups:
            break

        click.echo(f"Processing row group {i+1}/{total}...")
        df_chunk = parquet_file.read_row_group(i).to_pandas()
        df_chunk = _apply_type_conversions(df_chunk)

        # Insert into database
        df_chunk.to_sql(
            name=table_name,
            con=engine,
            if_exists="append",
            index=False,
        )
        click.echo(f"Inserted row group {i+1}/{total}")

    click.echo("Data ingestion complete!")


if __name__ == "__main__":
    main()
