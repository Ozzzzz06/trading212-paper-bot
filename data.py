import pandas as pd
import yfinance as yf


def fetch_hourly_data(symbol: str, period: str = "730d") -> pd.DataFrame:
    """
    Download hourly OHLCV data from Yahoo Finance.

    Yahoo intraday history is more limited than daily history, so this is
    intended for prototype research rather than long institutional backtests.
    """
    df = yf.download(
        tickers=symbol,
        period=period,
        interval="1h",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if df.empty:
        raise RuntimeError(f"No data returned for {symbol}")

    df = df.rename(columns=str.lower).copy()
    df = df[["open", "high", "low", "close", "volume"]]
    df.dropna(inplace=True)
    return df
