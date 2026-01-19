#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from sqlalchemy import create_engine
import click

@click.command()
@click.option('--pg-user', envvar="PG_USER", default="root")
@click.option('--pg-pass', envvar="PG_PASS", default="root")
@click.option('--pg-host', envvar="PG_HOST", default="pgdatabase")
@click.option('--pg-db', envvar="PG_DB", default="ny_taxi")
@click.option('--pg-port', envvar="PG_PORT", default=5432)
@click.option('--target-table', envvar="TARGET_TABLE", default="zones")
def run(pg_user, pg_pass, pg_host, pg_db, pg_port, target_table):
    url = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/misc/taxi_zone_lookup.csv"
    df_zones = pd.read_csv(url)
    engine = create_engine(f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}")

    # create table
    df_zones.head(0).to_sql(
        name=target_table,
        con=engine,
        if_exists="replace"
    )
    print(f"table {target_table} created")

    # insert data
    df_zones.to_sql(
        name=target_table,
        con=engine,
        if_exists="append"
    )
    print(f"{len(df_zones)} rows inserted into {target_table}")

if __name__ == '__main__':
    run()