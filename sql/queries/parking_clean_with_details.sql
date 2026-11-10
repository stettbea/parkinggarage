-- Schritt 35: Bereinigte Parkhausmessungen
-- mit den Parkhaus-Stammdaten verbinden.
-- Analysegrundlage für Person C.

SELECT
    c.*,
    g.parking_name,
    g.address,
    g.latitude,
    g.longitude
FROM occupancy_clean AS c
JOIN parking_garage AS g
    ON c.parking_id = g.parking_id;