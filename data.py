from pathlib import Path
import pandas as pd


DATA_DIR = Path("market_data")


def fetch_csv_data(symbol: str) -> pd.DataFrame:
    """
    Load OHLCV data from a local CSV file in market_data/.

    Expected filename:
        market_data/SPY.csv
        market_data/QQQ.csv
        market_data/GLD.csv
        market_data/TLT.csv

    Expected columns:
        datetime, open, high, low, close, volume

    Column names are normalised to lowercase.
    """
    file_path = DATA_DIR / f"{symbol}.csv"

    if not file_path.exists():
        raise RuntimeError(
            f"CSV file not found for {symbol}: {file_path}"
        )

    df = pd.read_csv(file_path)

    df.columns = [str(c).strip().lower() for c in df.columns]

    required = ["datetime", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise RuntimeError(
            f"{symbol} CSV is missing columns {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    df = df[required].copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna()

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna()
    df = df.sort_values("datetime").reset_index(drop=True)
    df = df.set_index("datetime")

    return df
