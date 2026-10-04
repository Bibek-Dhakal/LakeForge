# Data

No datasets are committed. Everything is fetched at run time.

| Source | Format | Origin |
|---|---|---|
| NYC TLC yellow-taxi trips | monthly parquet | NYC Taxi & Limousine Commission trip record data |
| Taxi zone lookup | CSV, loaded into SQLite by `lakeforge seed-db` | NYC TLC |
| Daily weather | JSON API | Open-Meteo historical archive |

Check each provider's terms before redistributing data. Sizes: about 50 MB per monthly trips
file; three months fit comfortably on a laptop.
