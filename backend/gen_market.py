import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

np.random.seed(42)

# Because this script is run from backend/,
# this creates backend/data/market/
out_dir = Path("data/market")
out_dir.mkdir(parents=True, exist_ok=True)

configs = {
    "RELIANCE": {
        "start": 2450,
        "drift": 0.0006,
        "vol": 0.016
    },
    "TCS": {
        "start": 3800,
        "drift": 0.0003,
        "vol": 0.013
    },
    "HDFCBANK": {
        "start": 1550,
        "drift": 0.0004,
        "vol": 0.014
    },
    "INFY": {
        "start": 1450,
        "drift": -0.0002,
        "vol": 0.018
    },
    "ICICIBANK": {
        "start": 1050,
        "drift": 0.0005,
        "vol": 0.015
    },
}

n_days = 260
end_date = datetime(2026, 8, 28)

dates = []
d = end_date

while len(dates) < n_days:
    if d.weekday() < 5:
        dates.append(d)
    d -= timedelta(days=1)

dates = sorted(dates)

for symbol, cfg in configs.items():

    price = cfg["start"]
    rows = []

    for dt in dates:

        ret = np.random.normal(
            cfg["drift"],
            cfg["vol"]
        )

        open_p = price

        close_p = max(
            1.0,
            price * (1 + ret)
        )

        high_p = max(
            open_p,
            close_p
        ) * (
            1 + abs(np.random.normal(0, 0.004))
        )

        low_p = min(
            open_p,
            close_p
        ) * (
            1 - abs(np.random.normal(0, 0.004))
        )

        volume = int(
            np.random.normal(
                6_000_000,
                1_500_000
            )
        )

        volume = max(
            500_000,
            volume
        )

        # Occasional volume spike
        if np.random.rand() < 0.03:
            volume = int(
                volume * np.random.uniform(2.5, 4)
            )

        rows.append({
            "date": dt.strftime("%Y-%m-%d"),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": volume,
        })

        price = close_p

    df = pd.DataFrame(rows)

    output_file = out_dir / f"{symbol}.csv"

    df.to_csv(
        output_file,
        index=False
    )

    print(
        symbol,
        "->",
        len(df),
        "rows, last close",
        df.iloc[-1]["close"]
    )

print("\nMarket data generation complete.")