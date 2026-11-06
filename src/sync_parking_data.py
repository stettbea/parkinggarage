import csv
import os
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# Projektverzeichnis bestimmen
project_dir = Path(__file__).resolve().parent.parent

# Datenbankverbindung vorbereiten
load_dotenv(project_dir / ".env")
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL fehlt.")

# Alle CSV-Dateien finden
csv_files = sorted((project_dir / "data" / "raw").glob("parking_*.csv"))

if not csv_files:
    raise FileNotFoundError("Keine Parkhaus-CSV gefunden.")

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:

        # Letzten gespeicherten Messzeitpunkt ermitteln
        cur.execute(
            "SELECT MAX(fetched_at_utc) FROM occupancy_snapshot"
        )
        last_saved = cur.fetchone()[0]

        # Neue Messungen sammeln
        new_rows = []
        garages = {}

        for csv_file in csv_files:
            with open(csv_file, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    fetched_at = datetime.fromisoformat(
                        row["fetched_at_utc"].replace("Z", "+00:00")
                    )

                    # Bereits importierte Zeitpunkte überspringen
                    if last_saved is not None and fetched_at <= last_saved:
                        continue

                    garages[row["parking_id"]] = (
                        row["parking_name"],
                        row["address"]
                    )

                    new_rows.append((
                        fetched_at,
                        row["source_updated_at_utc"] or None,
                        row["parking_id"],
                        row["status"] or None,
                        int(row["free_spaces"]) if row["free_spaces"] else None
                    ))

        # Neue Parkhäuser bei Bedarf hinzufügen
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

        # Neue Messungen importieren
        insert_sql = """
            INSERT INTO occupancy_snapshot
                (fetched_at_utc, source_updated_at_utc,
                 parking_id, status, free_spaces)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (parking_id, fetched_at_utc) DO NOTHING
        """

        for i in range(0, len(new_rows), 1000):
            cur.executemany(insert_sql, new_rows[i:i + 1000])

print(f"{len(new_rows)} neue Parkhausmessungen verarbeitet.")