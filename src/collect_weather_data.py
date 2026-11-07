import csv
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import psycopg
from dotenv import load_dotenv


# --------------------------------------------------
# 1. Hauptverzeichnis des Projekts bestimmen
# --------------------------------------------------

project_dir = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# 2. Open-Meteo API konfigurieren
# --------------------------------------------------

params = {
    "latitude": 47.3769,
    "longitude": 8.5417,
    "start_date": "2026-10-20",
    "end_date": (
        datetime.now(timezone.utc).date() - timedelta(days=1)
    ).isoformat(),
    "hourly": (
        "temperature_2m,"
        "precipitation,"
        "weather_code,"
        "snowfall,"
        "wind_speed_10m,"
        "cloud_cover"
    ),
    "timezone": "GMT"
}


# --------------------------------------------------
# 3. API-Adresse erstellen
# --------------------------------------------------

url = (
    "https://historical-forecast-api.open-meteo.com/v1/forecast?"
    + urlencode(params)
)


# --------------------------------------------------
# 4. Wetterdaten abrufen
# --------------------------------------------------

with urlopen(url, timeout=30) as response:
    weather_data = json.load(response)

hourly = weather_data["hourly"]


# --------------------------------------------------
# 5. Speicherordner festlegen
# --------------------------------------------------

output_dir = project_dir / "data" / "raw"
output_dir.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 6. Spalten unserer CSV-Dateien definieren
# --------------------------------------------------

fieldnames = [
    "weather_time_utc",
    "temperature_c",
    "precipitation_mm",
    "weather_code",
    "snowfall_cm",
    "wind_speed_kmh",
    "cloud_cover_pct"
]


# --------------------------------------------------
# 7. Wetterdaten nach Monaten aufteilen
# --------------------------------------------------

monthly_data = {}

for i in range(len(hourly["time"])):

    weather_time = datetime.fromisoformat(
        hourly["time"][i]
    ).replace(tzinfo=timezone.utc)

    # Passenden Dateinamen bestimmen
    filename = f"weather_{weather_time:%Y-%m}.csv"

    if filename not in monthly_data:
        monthly_data[filename] = []

    monthly_data[filename].append({
        "weather_time_utc": weather_time.isoformat(),
        "temperature_c": hourly["temperature_2m"][i],
        "precipitation_mm": hourly["precipitation"][i],
        "weather_code": hourly["weather_code"][i],
        "snowfall_cm": hourly["snowfall"][i],
        "wind_speed_kmh": hourly["wind_speed_10m"][i],
        "cloud_cover_pct": hourly["cloud_cover"][i]
    })


# --------------------------------------------------
# 8. Wetterdaten in monatlichen CSV-Dateien speichern
# --------------------------------------------------

for filename, rows in sorted(monthly_data.items()):

    output_file = output_dir / filename

    # Bereits vorhandene Zeitpunkte prüfen
    existing_times = set()

    if output_file.exists():
        with open(output_file, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                existing_times.add(row["weather_time_utc"])

    # Nur neue Wetterdaten auswählen
    new_rows = [
        row for row in rows
        if row["weather_time_utc"] not in existing_times
    ]

    # Prüfen, ob CSV-Header benötigt wird
    write_header = (
        not output_file.exists()
        or output_file.stat().st_size == 0
    )

    # Neue Wetterdaten speichern
    with open(output_file, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        writer.writerows(new_rows)

    print(f"{filename}: {len(new_rows)} neue Wetterbeobachtungen")

print("Historische Wetterdaten erfolgreich verarbeitet!")


# --------------------------------------------------
# 9. PostgreSQL-Datenbankverbindung vorbereiten
# --------------------------------------------------

load_dotenv(project_dir / ".env")
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL fehlt.")


# --------------------------------------------------
# 10. SQL-Befehl für den Wetterdatenimport definieren
# --------------------------------------------------

insert_sql = """
    INSERT INTO weather_hourly (
        weather_time_utc,
        temperature_c,
        precipitation_mm,
        weather_code,
        snowfall_cm,
        wind_speed_kmh,
        cloud_cover_pct
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (weather_time_utc) DO NOTHING
"""


# --------------------------------------------------
# 11. Alle Wetter-CSV-Dateien finden
# --------------------------------------------------

csv_files = sorted(output_dir.glob("weather_*.csv"))

processed = 0
inserted = 0


# --------------------------------------------------
# 12. Wetterdaten in Neon PostgreSQL synchronisieren
# --------------------------------------------------

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:

        for csv_file in csv_files:

            with open(csv_file, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:

                    # Werte in passende Datentypen umwandeln
                    values = (
                        row["weather_time_utc"],
                        float(row["temperature_c"]),
                        float(row["precipitation_mm"]),
                        int(row["weather_code"]),
                        float(row["snowfall_cm"]),
                        float(row["wind_speed_kmh"]),
                        int(row["cloud_cover_pct"])
                    )

                    # Wetterbeobachtung in PostgreSQL speichern
                    cur.execute(insert_sql, values)

                    processed += 1
                    inserted += cur.rowcount


# --------------------------------------------------
# 13. Ergebnis ausgeben
# --------------------------------------------------

print(f"{processed} Wetterbeobachtungen verarbeitet.")
print(f"{inserted} neue Wetterbeobachtungen in Neon gespeichert.")