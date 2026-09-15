import time
import pandas as pd
import yfinance as yf


def fetch_hourly_data(symbol: str, period: str = "60d", retries: int = 4) -> pd.DataFrame:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            df = yf.download(
                tickers=symbol,
                period=period,
                interval="1h",
                auto_adjust=False,
                progress=False,
                threads=False,
                group_by="column",
            )

            if df.empty:
                raise RuntimeError(f"No data returned for {symbol}")

            if isinstance(df.columns, pd.MultiIndex):
                if symbol in df.columns.get_level_values(-1):
                    df = df.xs(symbol, axis=1, level=-1)
                else:
                    df.columns = df.columns.get_level_values(0)

            df.columns = [str(c).lower() for c in df.columns]

            required = ["open", "high", "low", "close", "volume"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                raise RuntimeError(
                    f"{symbol} missing columns {missing}. Returned columns: {list(df.columns)}"
                )

            df = df[required].copy()
            df = df.apply(pd.to_numeric, errors="coerce").dropna()

            if df.empty:
                raise RuntimeError(f"{symbol} returned only missing values")

            return df

        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(5 * attempt)
            else:
                raise RuntimeError(
                    f"Failed to fetch data for {symbol} after {retries} attempts: {exc}"
                ) from exc
