"""Append new monthly rows to data/sales_data.csv.

Usage:
  python scripts/append_new_data.py             # add every complete month up to last month
  python scripts/append_new_data.py --months 3  # add exactly 3 months after the last one (demo)

The rows are SIMULATED with the same growth and festive-season pattern as the
original UrbanKart dataset. Replace generate_rows() with a real API call to use live data.
"""
import argparse, pathlib
from datetime import date
import numpy as np, pandas as pd

CSV = pathlib.Path(__file__).resolve().parents[1] / "data" / "sales_data.csv"
START = pd.Timestamp("2021-11-01")
SEAS = {
 "Electronics":[0.86,0.84,0.92,0.94,0.96,0.90,0.92,0.98,1.03,1.26,1.32,1.07],
 "Apparel":[0.90,0.87,1.00,1.03,1.13,0.98,0.91,0.95,1.05,1.30,1.17,1.11],
 "Grocery":[0.97,0.95,0.98,1.00,1.01,0.98,1.00,1.02,1.03,1.09,1.05,1.04]}
BASE = {"Electronics":(380,24500),"Apparel":(900,1450),"Grocery":(2600,310)}
GROWTH = {"Electronics":0.0062,"Apparel":0.0050,"Grocery":0.0040}
REGION = {"West":1.00,"South":0.82}

def generate_rows(month):
    t = (month.year - START.year) * 12 + month.month - START.month
    rows = []
    for ci, (cat, (u0, p0)) in enumerate(BASE.items()):
        s = np.array(SEAS[cat]); s = s / s.mean()
        for ri, (reg, rf) in enumerate(REGION.items()):
            rng = np.random.default_rng([2026, t, ci, ri])   # repeatable per month
            units = int(round(u0*rf*(1+GROWTH[cat])**t*s[month.month-1]*rng.lognormal(0, 0.045)))
            price = int(round(p0*(1.0028**t)*rng.normal(1, 0.01)))
            rows.append({"Date": month.strftime("%Y-%m-%d"), "Year": month.year, "Month_No": month.month,
                         "Month": month.strftime("%B"), "Region": reg, "Category": cat,
                         "Units_Sold": units, "Avg_Price": price, "Revenue": units*price})
    return rows

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--months", type=int, default=0)
    n = ap.parse_args().months
    df = pd.read_csv(CSV, parse_dates=["Date"])
    last = df.Date.max()
    if n > 0:
        new_months = list(pd.date_range(last + pd.offsets.MonthBegin(1), periods=n, freq="MS"))
    else:
        last_complete = pd.Timestamp(date.today().replace(day=1)) - pd.offsets.MonthBegin(1)
        new_months = list(pd.date_range(last + pd.offsets.MonthBegin(1), last_complete, freq="MS"))
    if not new_months:
        print("Already up to date. Last month:", last.strftime("%b %Y")); return
    rows = [r for m in new_months for r in generate_rows(m)]
    out = pd.concat([df.assign(Date=df.Date.dt.strftime("%Y-%m-%d")), pd.DataFrame(rows)], ignore_index=True)
    out.to_csv(CSV, index=False)
    print("Added", len(new_months), "month(s):", new_months[0].strftime("%b %Y"), "to", new_months[-1].strftime("%b %Y"))

if __name__ == "__main__":
    main()
