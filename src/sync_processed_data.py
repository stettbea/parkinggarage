import csv
import os
from datetime import date, datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# --------------------------------------------------
# 1. Projektverzeichnis bestimmen
# --------------------------------------------------

project_dir = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# 2. Datenbankverbindung vorbereiten
# --------------------------------------------------

load_dotenv(project_dir / ".env")
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL fehlt.")


# --------------------------------------------------
# 3. Bereinigte Dateien von Person B finden
# --------------------------------------------------

garages_file = project_dir / "data" / "processed" / "garages.csv"
clean_file = project_dir / "data" / "processed" / "occupancy_clean.csv"

for file_path in [garages_file, clean_file]:
    if not file_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")


# --------------------------------------------------
# 4. CSV-Dateien einlesen
# --------------------------------------------------

with open(garages_file, newline="", encoding="utf-8") as file:
    garages = list(csv.DictReader(file))

with open(clean_file, newline="", encoding="utf-8") as file:
    clean_data = list(csv.DictReader(file))

if not garages or not clean_data:
    raise ValueError("Eine der CSV-Dateien ist leer.")

print(f"{len(garages)} Parkhäuser gefunden.")
print(f"{len(clean_data)} bereinigte Messungen gefunden.")


# --------------------------------------------------
# 5. Zahlen aus den CSV-Dateien umwandeln
# --------------------------------------------------

def to_integer(value):
    if value is None or value.strip() == "":
        return None

    number = float(value)

    if not number.is_integer():
        raise ValueError(f"Keine ganze Zahl: {value}")

    return int(number)


def to_float(value):
    if value is None or value.strip() == "":
        return None

    return float(value)


# --------------------------------------------------
# 6. Bereinigte Messungen vorbereiten
# --------------------------------------------------

clean_rows = []
seen_keys = set()

for row in clean_data:

    slot = datetime.fromisoformat(row["slot_utc"])
    parking_id = row["parking_id"]

    if slot.tzinfo is None:
        raise ValueError("Zeitstempel ohne Zeitzone gefunden.")

    # Prüfen, ob eine Messung doppelt vorkommt
    key = (parking_id, slot)

    if key in seen_keys:
        raise ValueError(f"Doppelte Messung gefunden: {key}")

    seen_keys.add(key)

    # Boolean-Wert aus CSV umwandeln
    weekend_text = row["is_weekend"].strip().lower()

    if weekend_text not in ("true", "false"):
        raise ValueError("Ungültiger Wert bei is_weekend.")

    is_weekend = weekend_text == "true"

    clean_rows.append((
        slot,
        parking_id,
        row["status"],
        to_integer(row["free_spaces"]),
        to_integer(row["capacity_used"]),
        to_float(row["occupancy_rate"]),
        date.fromisoformat(row["date"]),
        to_integer(row["hour"]),
        row["weekday"],
        is_weekend
    ))


# --------------------------------------------------
# 7. SQL-Befehl für Parkhaus-Stammdaten
# --------------------------------------------------

update_garages_sql = """
    UPDATE parking_garage
    SET
        capacity = %s,
        latitude = %s,
        longitude = %s,
        capacity_used = %s,
        city_name = %s,
        city_address = %s,
        match_method = %s,
        max_free = %s
    WHERE parking_id = %s
"""


# --------------------------------------------------
# 8. Verbindung zu Neon herstellen
# --------------------------------------------------

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:

        # ------------------------------------------
        # 8.1 Parkhaus-Stammdaten aktualisieren
        # ------------------------------------------

        updated = 0

        for row in garages:

            values = (
                to_integer(row["capacity"]),
                to_float(row["latitude"]),
                to_float(row["longitude"]),
                to_integer(row["capacity_used"]),
                row["city_name"] or None,
                row["city_address"] or None,
                row["match_method"] or None,
                to_integer(row["max_free"]),
                row["parking_id"]
            )

            cur.execute(update_garages_sql, values)

            if cur.rowcount != 1:
                raise ValueError(
                    f"Parkhaus nicht gefunden: {row['parking_id']}"
                )

            updated += 1

        # ------------------------------------------
        # 8.2 Bisherige bereinigte Messungen ersetzen
        # ------------------------------------------

        cur.execute("DELETE FROM occupancy_clean")

        # ------------------------------------------
        # 8.3 Aktuelle bereinigte Daten importieren
        # ------------------------------------------

        copy_sql = """
            COPY occupancy_clean (
                slot_utc,
                parking_id,
                status,
                free_spaces,
                capacity_used,
                occupancy_rate,
                date,
                hour,
                weekday,
                is_weekend
            )
            FROM STDIN
        """

        with cur.copy(copy_sql) as copy:
            for row in clean_rows:
                copy.write_row(row)

        # ------------------------------------------
        # 8.4 Ergebnis kontrollieren
        # ------------------------------------------

        cur.execute("SELECT COUNT(*) FROM occupancy_clean")
        total_clean = cur.fetchone()[0]

        if total_clean != len(clean_rows):
            raise ValueError("Anzahl importierter Messungen stimmt nicht.")

# Erst hier werden die Änderungen gespeichert.
# Bei einem Fehler wird die Transaktion zurückgerollt.


# --------------------------------------------------
# 9. Ergebnis ausgeben
# --------------------------------------------------

print(f"{updated} Parkhäuser aktualisiert.")
print(f"{total_clean} bereinigte Messungen in Neon gespeichert.")
print("Synchronisierung erfolgreich abgeschlossen.")