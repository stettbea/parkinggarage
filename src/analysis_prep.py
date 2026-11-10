"""
Data loading for Person C's notebooks (03_eda, 05_model).

load_data() returns B's cleaned occupancy data, joined with the garage master data
and the hourly weather, plus the time features used in the EDA and the model.

Source:
  1. PostgreSQL (Neon), if DATABASE_URL is set in .env  -> sql/queries/c_analysis_dataset.sql
  2. otherwise the CSV files in data/processed and data/raw (same join in pandas)

Both sources give the same result, so the notebooks run with or without database access.
Cleaning itself is B's part (notebooks/02_integration_cleaning.ipynb); nothing is
re-cleaned here.
"""

import os
from pathlib import Path

# pyright: reportMissingImports=false
import pandas as pd  # type: ignore[import-not-found]

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
SQL_FILE = ROOT / "sql" / "queries" / "c_analysis_dataset.sql"
LOCAL_TZ = "Europe/Zurich"
RAIN_MM = 0.1  # an hour counts as "rain" from 0.1 mm precipitation


def _database_url():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    return os.getenv("DATABASE_URL")


def _load_sql(url):
    import psycopg
    query = SQL_FILE.read_text(encoding="utf-8")
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(query)
        cols = [d.name for d in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=cols)
    df["slot_utc"] = pd.to_datetime(df["slot_utc"], utc=True)
    for c in ["free_spaces", "capacity_used", "occupancy_rate", "latitude", "longitude", "temperature_c", "precipitation_mm"]:
        df[c] = pd.to_numeric(df[c])
    return df


def _load_csv():
    clean = pd.read_csv(PROCESSED / "occupancy_clean.csv")
    garages = pd.read_csv(PROCESSED / "garages.csv")
    weather = pd.concat([pd.read_csv(f) for f in sorted(RAW.glob("weather_*.csv"))], ignore_index=True)

    clean["slot_utc"] = pd.to_datetime(clean["slot_utc"], utc=True)
    clean["is_weekend"] = clean["is_weekend"].astype(str).str.lower().eq("true")
    weather["weather_time_utc"] = pd.to_datetime(weather["weather_time_utc"], utc=True)
    weather = weather.drop_duplicates("weather_time_utc")

    df = clean.merge(garages[["parking_id", "parking_name", "latitude", "longitude"]], on="parking_id", how="inner")
    df["weather_time_utc"] = df["slot_utc"].dt.floor("h")
    df = df.merge(weather[["weather_time_utc", "temperature_c", "precipitation_mm"]], on="weather_time_utc", how="left")
    cols = ["slot_utc", "parking_id", "parking_name", "free_spaces", "capacity_used", "occupancy_rate",
            "is_weekend", "latitude", "longitude", "temperature_c", "precipitation_mm"]
    return df[cols].sort_values(["parking_id", "slot_utc"]).reset_index(drop=True)


def load_data(source="auto", verbose=True):
    """Analysis dataset. source = "auto" | "sql" | "csv"."""
    url = _database_url() if source in ("auto", "sql") else None
    df = None
    if url:
        try:
            df, used = _load_sql(url), "PostgreSQL (sql/queries/c_analysis_dataset.sql)"
        except Exception as exc:          # no psycopg, no network, database asleep, ...
            if source == "sql":
                raise
            print(f"PostgreSQL not reachable ({type(exc).__name__}: {exc}) – falling back to the CSV files.")
    elif source == "sql":
        raise ValueError("DATABASE_URL is missing in .env")
    if df is None:
        df, used = _load_csv(), "CSV files (data/processed, data/raw)"

    # Time features in Zurich local time (people follow local time, incl. the switch on 25 Oct)
    local = df["slot_utc"].dt.tz_convert(LOCAL_TZ)
    df["slot_local"] = local
    df["date"] = local.dt.date
    df["hour"] = local.dt.hour
    df["minute_of_day"] = local.dt.hour * 60 + local.dt.minute
    df["weekday"] = local.dt.dayofweek          # 0 = Monday
    df["weekday_name"] = local.dt.day_name().str[:3]
    df["is_weekend"] = df["is_weekend"].astype(int)
    df["is_rain"] = (df["precipitation_mm"] >= RAIN_MM).astype("Int64").where(df["precipitation_mm"].notna())
    df["parking_name"] = df["parking_name"].str.replace(r"^(Parkhaus|Parkplatz)\s+", "", regex=True)

    if verbose:
        print(f"Data source: {used}")
        print(f"{len(df):,} rows · {df.parking_id.nunique()} garages · "
              f"{local.min():%d.%m.%Y} – {local.max():%d.%m.%Y} · weather missing for {df.temperature_c.isna().mean():.1%} of rows")
    return df


def caption(df):
    """Source line for every figure (source, period, sample size)."""
    return (f"Source: own 15-min collection of the PLS feed (City of Zurich), cleaned (notebook 02); weather: Open-Meteo · "
            f"{df.slot_local.min():%d.%m.}–{df.slot_local.max():%d.%m.%Y} · {df.parking_id.nunique()} garages · n = {len(df):,}")
