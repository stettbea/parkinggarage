# Data Pipeline – Zurich Parking Garage Analytics

## 1. Overview

This project collects, processes, and stores parking garage occupancy and weather data to support data analysis and machine learning.

The data pipeline follows this structure:

```text
Zurich Parking Guidance System (PLS)
                |
                v
       Python Data Collector
                |
                v
     Raw CSV Files + Neon PostgreSQL
                |
                v
      Data Cleaning (Person B)
                |
                v
        Processed CSV Files
                |
                v
  Database Synchronization (Person A)
                |
                v
  SQL Joins with Garage and Weather Data
                |
                v
   EDA and Machine Learning (Person C)
```

Weather data is collected separately and stored in the same PostgreSQL database before being joined with the cleaned parking data.

## 2. Data Sources

### 2.1 Parking Garage Data

- **Source:** Zurich Parking Guidance System (PLS)
- **Original format:** XML/RSS
- **Collection frequency:** Every 15 minutes via GitHub Actions
- **Python script:** `src/collect_parking_data.py`
- **CSV storage:** `data/raw/parking_YYYY-MM.csv`
- **Database storage:** Neon PostgreSQL

The dataset contains information about parking garages, including available parking spaces, operational status, and timestamps.

### 2.2 Weather Data

- **Source:** Open-Meteo Historical Forecast API
- **Original format:** JSON
- **Collection frequency:** Daily via GitHub Actions
- **Python script:** `src/collect_weather_data.py`
- **CSV storage:** `data/raw/weather_YYYY-MM.csv`
- **Database storage:** Neon PostgreSQL

The weather dataset contains hourly measurements of:

- Temperature
- Precipitation
- Snowfall
- Wind speed
- Cloud cover
- Weather conditions (weather code)

**Important:** Precipitation and snowfall values represent the preceding hour. This must be considered when interpreting relationships between weather and parking garage occupancy.

## 3. Database Structure

The project uses a PostgreSQL database hosted on Neon.

The database contains four main tables:

| Table | Description |
|---|---|
| `parking_garage` | Master data containing parking garage information |
| `occupancy_snapshot` | Raw parking garage measurements |
| `weather_hourly` | Hourly weather data |
| `occupancy_clean` | Cleaned parking garage occupancy measurements |

The database schema is defined in:

`sql/schema.sql`

The database is accessed using the `DATABASE_URL` environment variable.

Database credentials must never be committed to the GitHub repository.

## 4. Data Collection and Synchronization

### 4.1 Automated Data Collection

Parking garage and weather data are collected automatically using GitHub Actions.

The automated workflows are defined in:

- `.github/workflows/collect.yml`
- `.github/workflows/weather.yml`

The collected raw data is stored in CSV files and synchronized with Neon PostgreSQL.

### 4.2 Data Cleaning

Person B is responsible for cleaning and preparing the parking garage data.

The processed datasets are stored in:

- `data/processed/garages.csv`
- `data/processed/occupancy_clean.csv`

The cleaning process prepares the data for consistent occupancy analysis.

### 4.3 Synchronization of Cleaned Data

Person A is responsible for importing the cleaned datasets into Neon PostgreSQL.

The synchronization is performed using:

```bash
python src/sync_processed_data.py
```

This script updates the parking garage master data and replaces the contents of `occupancy_clean` with the latest processed dataset.

**Important:** Changes made by Person B are not automatically synchronized with Neon. After the processed CSV files are updated, Person A must run the synchronization script again.

## 5. Data Integration Using SQL

### 5.1 Parking Garage Information

The cleaned occupancy measurements are linked to the parking garage master data using the shared `parking_id` column.

The SQL query is stored in:

`sql/queries/parking_clean_with_details.sql`

This join adds information such as:

- Parking garage name
- Address
- Latitude
- Longitude

### 5.2 Weather Data Integration

Parking garage occupancy data is collected approximately every 15 minutes, while weather data is available hourly.

To combine these datasets, each occupancy measurement is matched with the weather record corresponding to its UTC hour.

The SQL join condition is:

```sql
ON w.weather_time_utc = DATE_TRUNC('hour', c.slot_utc)
```

For example, an occupancy measurement recorded at 10:15 UTC is matched with the weather record at 10:00 UTC.

A `LEFT JOIN` is used to retain occupancy measurements even when matching weather data is unavailable.

Time-based analyses should account for the `Europe/Zurich` time zone when interpreting local hours and weekdays.

## 6. Data Availability for Analysis

The cleaned and integrated data is provided to Person C for exploratory data analysis (EDA) and machine learning.

The existing SQL query for the analysis dataset is stored in:

`sql/queries/c_analysis_dataset.sql`

The corresponding Python functionality is implemented in:

`src/analysis_prep.py`

Person C is responsible for running and validating the analysis code.

All analytical work should use the cleaned occupancy measurements rather than the unprocessed raw data.

## 7. Team Responsibilities

| Team Member | Responsibilities |
|---|---|
| **Person A** | Data collection, database setup, data synchronization, SQL integration, and technical documentation |
| **Person B** | Data cleaning, data quality checks, and preparation of processed datasets |
| **Person C** | Exploratory data analysis, visualization, and machine learning |

## 8. Data Quality and Maintenance

Several measures support data quality and reproducibility:

- Raw datasets are preserved in CSV format.
- Processed datasets are stored separately from raw data.
- Database constraints help prevent invalid or duplicate records.
- SQL joins are used to integrate data without modifying the original tables.
- Automated workflows support continuous data collection.
- SQL queries and Python scripts are version-controlled using GitHub.

Before the final analysis, the processed datasets should be updated and synchronized with Neon to ensure that the available data is consistent across the project.