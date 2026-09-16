from pathlib import Path

import pandas as pd


DATA_DIR = Path("market_data")


def fetch_csv_data(symbol: str) -> pd.DataFrame:
    """
    Load OHLCV data from a local CSV file in market_data/.

    Accepted first-column names:
        date or datetime

    Expected price columns:
        open, high, low, close, volume
    """
    file_path = DATA_DIR / f"{symbol}.csv"

    if not file_path.exists():
        raise RuntimeError(f"CSV file not found for {symbol}: {file_path}")

    df = pd.read_csv(file_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    if "datetime" not in df.columns and "date" in df.columns:
        df = df.rename(columns={"date": "datetime"})

    required = ["datetime", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise RuntimeError(
            f"{symbol} CSV is missing columns {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    df = df[required].copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna()
    df = df.sort_values("datetime").reset_index(drop=True)
    df = df.set_index("datetime")

    return df