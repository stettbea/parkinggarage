CREATE TABLE IF NOT EXISTS parking_garage (
    parking_id TEXT PRIMARY KEY,
    parking_name TEXT NOT NULL,
    address TEXT,
    capacity INTEGER CHECK (capacity > 0),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

-- Zusätzliche Stammdaten aus Person Bs Datenintegration
ALTER TABLE parking_garage
    ADD COLUMN IF NOT EXISTS capacity_used INTEGER
        CHECK (capacity_used > 0),
    ADD COLUMN IF NOT EXISTS city_name TEXT,
    ADD COLUMN IF NOT EXISTS city_address TEXT,
    ADD COLUMN IF NOT EXISTS match_method TEXT,
    ADD COLUMN IF NOT EXISTS max_free INTEGER
        CHECK (max_free >= 0);

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

-- Bereinigte Parkhausmessungen von Person B
CREATE TABLE IF NOT EXISTS occupancy_clean (
    slot_utc TIMESTAMPTZ NOT NULL,
    parking_id TEXT NOT NULL,
    status TEXT,
    free_spaces INTEGER CHECK (free_spaces >= 0),
    capacity_used INTEGER CHECK (capacity_used > 0),
    occupancy_rate DOUBLE PRECISION CHECK (
        occupancy_rate BETWEEN 0 AND 1
    ),
    date DATE,
    hour SMALLINT CHECK (hour BETWEEN 0 AND 23),
    weekday TEXT,
    is_weekend BOOLEAN,

    PRIMARY KEY (parking_id, slot_utc),
    FOREIGN KEY (parking_id) REFERENCES parking_garage(parking_id)
);