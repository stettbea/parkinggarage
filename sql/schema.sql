CREATE TABLE IF NOT EXISTS parking_garage (
    parking_id TEXT PRIMARY KEY,
    parking_name TEXT NOT NULL,
    address TEXT,
    capacity INTEGER CHECK (capacity > 0),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS occupancy_snapshot (
    fetched_at_utc TIMESTAMPTZ NOT NULL,
    source_updated_at_utc TIMESTAMPTZ,
    parking_id TEXT NOT NULL,
    status TEXT,
    free_spaces INTEGER CHECK (free_spaces >= 0),

    PRIMARY KEY (parking_id, fetched_at_utc),
    FOREIGN KEY (parking_id) REFERENCES parking_garage(parking_id)
);

CREATE TABLE IF NOT EXISTS weather_hourly (
    weather_time_utc TIMESTAMPTZ PRIMARY KEY,
    temperature_c DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION CHECK (precipitation_mm >= 0),
    weather_code INTEGER,
    snowfall_cm DOUBLE PRECISION CHECK (snowfall_cm >= 0),
    wind_speed_kmh DOUBLE PRECISION CHECK (wind_speed_kmh >= 0),
    cloud_cover_pct INTEGER CHECK (cloud_cover_pct BETWEEN 0 AND 100)
);