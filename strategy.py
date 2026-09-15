"""
Signal generation layer.

Converts a DataFrame with indicator columns into a Signal dataclass.
Only uses completed (closed) bars — never the still-forming bar at iloc[-1]
if the data was fetched mid-candle.  The caller is responsible for ensuring
the most recent bar is complete before calling generate_signal().
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    symbol: str
    action: str          # "BUY", "SELL", or "HOLD"
    stop_distance: float # distance from entry to stop-loss (price units)


def generate_signal(symbol: str, df: pd.DataFrame) -> Signal:
    """
    Generate a trading signal for a single instrument.

    Entry rule:
        - 20 EMA crosses above 50 EMA (fast crosses slow upwards).
        - Price is above the 200 EMA (broader uptrend confirmed).
        - Stop distance = 2 × ATR at entry.

    Exit rule:
        - 20 EMA crosses below 50 EMA.

    Hold:
        - All other conditions.
    """
    if len(df) < 3:
        return Signal(symbol=symbol, action="HOLD", stop_distance=0.0)

    latest   = df.iloc[-1]  # most recent completed bar
    previous = df.iloc[-2]  # bar before that

    # EMA crossover: fast crosses above slow
    crossed_up = (
        previous["ema_fast"] <= previous["ema_slow"]
        and latest["ema_fast"] > latest["ema_slow"]
    )

    # EMA crossover: fast crosses below slow
    crossed_down = (
        previous["ema_fast"] >= previous["ema_slow"]
        and latest["ema_fast"] < latest["ema_slow"]
    )

    # Only buy when the broader trend is up
    above_trend = latest["close"] > latest["ema_trend"]

    if crossed_up and above_trend:
        return Signal(
            symbol=symbol,
            action="BUY",
            stop_distance=2.0 * latest["atr"],
        )

    if crossed_down:
        return Signal(
            symbol=symbol,
            action="SELL",
            stop_distance=0.0,
        )

    return Signal(symbol=symbol, action="HOLD", stop_distance=0.0)
