import os
from pathlib import Path
import psycopg
from dotenv import load_dotenv

# Projektverzeichnis bestimmen
project_dir = Path(__file__).resolve().parent.parent

# Zugangsdaten aus .env laden
load_dotenv(project_dir / ".env")
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL fehlt in der .env-Datei.")

# SQL-Datei einlesen
schema_sql = (project_dir / "sql" / "schema.sql").read_text(
    encoding="utf-8"
)

# Verbindung zur PostgreSQL-Datenbank herstellen
with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        cur.execute(schema_sql)

print("Die Datenbanktabellen wurden erfolgreich erstellt.")