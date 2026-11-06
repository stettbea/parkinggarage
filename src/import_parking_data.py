import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# Hauptordner des Projekts bestimmen
project_dir = Path(__file__).resolve().parent.parent

# Verbindung zur Neon-Datenbank vorbereiten
load_dotenv(project_dir / ".env")
database_url = os.getenv("DATABASE_URL")

# Alle gesammelten Monatsdateien finden
csv_files = sorted((project_dir / "data" / "raw").glob("parking_*.csv"))

# Parkhäuser aus den CSV-Dateien auslesen
garages = {}

for csv_file in csv_files:
    with open(csv_file, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            garages[row["parking_id"]] = (
                row["parking_name"],
                row["address"]
            )

# Parkhäuser in PostgreSQL speichern
with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        for parking_id, (name, address) in garages.items():
            cur.execute(
                """
                INSERT INTO parking_garage
                    (parking_id, parking_name, address)
                VALUES (%s, %s, %s)
                ON CONFLICT (parking_id) DO NOTHING
                """,
                (parking_id, name, address)
            )

print(f"{len(garages)} unterschiedliche Parkhäuser verarbeitet.")

# SQL-Befehl zum Speichern der Parkhausmessungen
insert_sql = """
    INSERT INTO occupancy_snapshot
        (fetched_at_utc, source_updated_at_utc, parking_id, status, free_spaces)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (parking_id, fetched_at_utc) DO NOTHING
"""

# Messungen aus allen CSV-Dateien importieren
batch = []
processed = 0

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:

        for csv_file in csv_files:
            with open(csv_file, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    batch.append((
                        row["fetched_at_utc"],
                        row["source_updated_at_utc"] or None,
                        row["parking_id"],
                        row["status"] or None,
                        int(row["free_spaces"]) if row["free_spaces"] else None
                    ))

                    # Jeweils 1000 Messungen gemeinsam importieren
                    if len(batch) >= 1000:
                        cur.executemany(insert_sql, batch)
                        processed += len(batch)
                        batch.clear()

        # Verbleibende Messungen importieren
        if batch:
            cur.executemany(insert_sql, batch)
            processed += len(batch)

print(f"{processed} Parkhausmessungen verarbeitet.")