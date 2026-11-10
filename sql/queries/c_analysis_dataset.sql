-- Weather is hourly, snapshots are every 15 minutes: each snapshot gets the weather of its hour.

SELECT
    c.slot_utc,
    c.parking_id,
    g.parking_name,
    c.free_spaces,
    c.capacity_used,
    c.occupancy_rate,
    c.is_weekend,
    g.latitude,
    g.longitude,
    w.temperature_c,
    w.precipitation_mm
FROM occupancy_clean AS c
JOIN parking_garage AS g
    ON c.parking_id = g.parking_id
LEFT JOIN weather_hourly AS w
    ON w.weather_time_utc = date_trunc('hour', c.slot_utc)
ORDER BY c.parking_id, c.slot_utc;
