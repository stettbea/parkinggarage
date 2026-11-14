# Zurich Parking Garage Analytics

## Project Overview

This project analyzes parking garage utilization patterns in Zurich, Switzerland, using parking occupancy and weather data.

The objective is to understand how parking garage utilization varies across locations, times of day, weekdays, weekends, and weather conditions. The project also investigates how reliably periods of high utilization can be identified.

## Research Question

**How do parking garage utilization patterns in Zurich differ by location, time of day, weekday/weekend and weather conditions, and how reliably can periods of high utilization be identified?**

## Data Sources

The project combines two main data sources:

| Data Source | Description |
|---|---|
| Zurich Parking Guidance System (PLS) | Parking garage availability and status data, collected approximately every 15 minutes |
| Open-Meteo Historical Forecast API | Hourly weather data, including temperature, precipitation, snowfall, wind speed, and cloud cover |

## Technologies

- **Python:** Data collection, processing, and analysis
- **PostgreSQL (Neon):** Database storage
- **GitHub Actions:** Automated data collection
- **SQL:** Data integration and querying
- **Jupyter Notebooks:** Data cleaning, exploratory analysis, and machine learning

## Repository Structure

```text
parkinggarage/
├── .github/workflows/     # Automated data collection
├── data/
│   ├── raw/               # Collected raw data
│   ├── processed/         # Cleaned datasets
│   └── external/          # Additional data sources
├── docs/                  # Technical documentation
├── figures/               # Visualizations and analysis results
├── notebooks/             # Data cleaning, EDA, and modeling
├── sql/
│   ├── queries/           # SQL analysis queries
│   └── schema.sql         # Database schema
├── src/                   # Python scripts
└── README.md
```

## Data Pipeline

1. Parking garage data is collected automatically from the Zurich PLS feed.
2. Weather data is retrieved daily from Open-Meteo.
3. Raw datasets are stored as CSV files and in Neon PostgreSQL.
4. Parking garage data is cleaned and prepared for analysis.
5. Cleaned datasets are synchronized with PostgreSQL.
6. SQL queries combine occupancy measurements with garage information and weather data.
7. The resulting datasets are used for exploratory data analysis and machine learning.

## Database

The PostgreSQL database contains four main tables:

| Table | Description |
|---|---|
| `parking_garage` | Parking garage master data |
| `occupancy_snapshot` | Raw parking occupancy measurements |
| `occupancy_clean` | Cleaned parking occupancy measurements |
| `weather_hourly` | Hourly weather data |

Database access requires the `DATABASE_URL` environment variable. Database credentials are not stored in this repository.

## Analysis

The project focuses on:

- Parking garage utilization across different locations
- Daily and weekly occupancy patterns
- Differences between weekdays and weekends
- Relationships between weather conditions and parking utilization
- Identification and prediction of high-utilization periods

## Documentation

For further information about data collection, database integration, synchronization, and data availability, see:

[`docs/data_pipeline.md`](docs/data_pipeline.md)

## Team Responsibilities

| Team Member | Main Responsibility |
|---|---|
| Person A | Data collection, database management, SQL integration, and technical documentation |
| Person B | Data cleaning, data integration, and data quality |
| Person C | Exploratory data analysis and machine learning |