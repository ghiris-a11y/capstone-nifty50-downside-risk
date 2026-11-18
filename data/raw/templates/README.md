# Macro data templates (fill from official sources only; do not estimate)

The pipeline reads `data/raw/repo_rate.csv`, `data/raw/cpi.csv` and `data/raw/iip.csv` (columns `date,value`)
only when they exist. Fill a template completely, check it, then copy it to that name. A partly filled or
empty file would remove rows from the model, so leave the file absent until it is complete (2014-12 to the
latest release).

| File | What to enter | `date` convention | Official source |
|---|---|---|---|
| repo_rate.csv | RBI policy repo rate (%), one row per change, plus a first row in Dec 2014 | Date the change took effect (MPC announcement date) | RBI: Database on Indian Economy (data.rbi.org.in), table of policy rates; or the MPC press releases on rbi.org.in |
| cpi.csv | CPI (Combined, All India, General Index), monthly | Last day of the reference month (pipeline adds a 15-day release lag) | MoSPI CPI releases (mospi.gov.in / esankhyiki.mospi.gov.in) |
| iip.csv | IIP General Index, monthly | Last day of the reference month (pipeline adds a 45-day release lag) | MoSPI IIP releases (mospi.gov.in / esankhyiki.mospi.gov.in) |

Use the final revised figure for each month and note in the report the access date of each source.
CPI and IIP base years have changed over time; use one consistent base-year series (with the official
linking factor if needed) and record which one.
