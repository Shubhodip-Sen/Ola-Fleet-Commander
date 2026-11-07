# OLA Ride Bookings Analysis (July 2024)

103,024 bookings · 7 vehicle types · 50 Bengaluru zones · 31 July 2024 days.

## Folder
| Path | What it is |
|---|---|
| `sql/ola_analysis.sql` | 31 SQLite queries (data checks, KPIs, vehicles, time, zones, cancellations, payments, customers) |
| `app.py` | Gamified Streamlit dashboard "OLA Fleet Commander" |
| `deck/OLA_Ride_Analytics.pptx` | 12-slide presentation with speaker notes (`deck/build_deck.js` rebuilds it) |
| `prep_data.py` | Cleans `OLA_DataSet.xlsx` and builds `data/ola_cleaned.csv` + `data/ola.db` |
| `run_sql.py` | Runs every query in the .sql file and prints results (QA helper) |
| `data/` | `ola_cleaned.csv`, `ola.db` (put `OLA_DataSet.xlsx` here to rebuild) |
| `docs/` | Dashboard screenshots |

## Run it
```bash
pip install -r requirements.txt
python prep_data.py            # only if data/ola.db is missing and you have the xlsx
streamlit run app.py
sqlite3 data/ola.db < sql/ola_analysis.sql      # or use the SQL Lab tab in the app
```
The app rebuilds `ola.db` from `data/ola_cleaned.csv` automatically if the database file is missing.

## Notes
- Revenue = `Booking_Value` on `Success` bookings only. Booking value on failed bookings is shown as "fares at risk".
- Ratings, turnaround times and payment method are blank for failed bookings by design; they are labelled `Not Applicable`.
- July 2024 has five Mon/Tue/Wed and four of every other weekday: compare per-day averages, not raw totals.
- Fare and distance are almost uncorrelated (0.002), so the data looks simulated: trust direction over exact values.
- Gamification: XP, 5 levels, 8 badges. Progress lives in the browser session and resets on refresh.
