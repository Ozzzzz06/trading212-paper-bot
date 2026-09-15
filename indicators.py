"""
Technical indicator calculations.
All functions take a pandas DataFrame with at least columns:
    open, high, low, close, volume
and return a copy with additional indicator columns appended.
"""

import pandas as pd


def add_ema(df: pd.DataFrame, span: int, column: str = "close") -> pd.Series:
    """
    Calculate an exponential moving average.

    Uses adjust=False so each bar is a genuine rolling weighted average
    (not a corrected initialisation). This matches most charting platforms.
    """
    return df[column].ewm(span=span, adjust=False).mean()


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range.

    True Range is the greatest of:
      - high - low
      - |high - previous close|
      - |low  - previous close|

    We use shift(1) so the previous-close comes from a completed bar,
    avoiding any look-ahead contamination.
    """
    prev_close = df["close"].shift(1)

    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return true_range.rolling(period).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all strategy indicators to a price DataFrame.

    Returns a copy so the original data is never mutated.
    """
    from config import FAST_EMA, SLOW_EMA, TREND_EMA, ATR_PERIOD

    result = df.copy()

    result["ema_fast"]  = add_ema(result, FAST_EMA)
    result["ema_slow"]  = add_ema(result, SLOW_EMA)
    result["ema_trend"] = add_ema(result, TREND_EMA)
    result["atr"]       = add_atr(result, ATR_PERIOD)

    return result
