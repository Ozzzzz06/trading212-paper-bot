import math
from dataclasses import dataclass

import pandas as pd

from config import (
    RISK_PER_TRADE,
    MAX_POSITION_EXPOSURE,
    STARTING_CAPITAL,
    SYMBOLS,
)
from data import fetch_hourly_data
from indicators import add_indicators
from risk import calculate_quantity, calculate_exit_prices


SLIPPAGE_FRACTION = 0.0005
MAX_HOLDING_BARS = 5 * 7  # roughly 5 trading days of hourly bars


@dataclass
class Trade:
    symbol: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    reason: str


def run_single_symbol_backtest(symbol: str) -> tuple[list[Trade], float]:
    equity = STARTING_CAPITAL
    trades: list[Trade] = []

    df = fetch_hourly_data(symbol)
    df = add_indicators(df).dropna().copy()

    in_position = False
    entry_price = 0.0
    entry_time = None
    quantity = 0.0
    stop_price = 0.0
    take_profit_price = 0.0
    bars_held = 0

    for i in range(2, len(df)):
        current = df.iloc[i]
        previous = df.iloc[i - 1]

        prev_ema_fast = float(previous["ema_fast"])
        prev_ema_slow = float(previous["ema_slow"])
        curr_ema_fast = float(current["ema_fast"])
        curr_ema_slow = float(current["ema_slow"])
        curr_close = float(current["close"])
        curr_ema_trend = float(current["ema_trend"])
        curr_atr = float(current["atr"])
        curr_low = float(current["low"])
        curr_high = float(current["high"])
        
        crossed_up = (
            prev_ema_fast <= prev_ema_slow
            and curr_ema_fast > curr_ema_slow
        )
        
        crossed_down = (
            prev_ema_fast >= prev_ema_slow
            and curr_ema_fast < curr_ema_slow
        )

        if not in_position:
            if crossed_up and curr_close > curr_ema_trend:
                stop_distance = 2.0 * curr_atr

                qty = calculate_quantity(
                    equity=equity,
                    entry_price=curr_close,
                    stop_distance=float(stop_distance),
                    risk_fraction=RISK_PER_TRADE,
                    max_position_fraction=MAX_POSITION_EXPOSURE,
                )

                if qty > 0:
                    entry_price = float(current["close"]) * (1 + SLIPPAGE_FRACTION)
                    quantity = qty
                    stop_price, take_profit_price = calculate_exit_prices(
                        entry_price=entry_price,
                        atr=curr_atr,
                        stop_multiplier=2.0,
                        reward_multiple=2.0,
                    )
                    entry_time = str(df.index[i])
                    bars_held = 0
                    in_position = True
        else:
            bars_held += 1

            exit_reason = None
            exit_price = None

            if curr_low <= stop_price:
                exit_price = stop_price * (1 - SLIPPAGE_FRACTION)
                exit_reason = "stop_loss"
            elif curr_high >= take_profit_price:
                exit_price = take_profit_price * (1 - SLIPPAGE_FRACTION)
                exit_reason = "take_profit"
            elif crossed_down:
                exit_price = float(current["close"]) * (1 - SLIPPAGE_FRACTION)
                exit_reason = "ema_cross_down"
            elif bars_held >= MAX_HOLDING_BARS:
                exit_price = float(current["close"]) * (1 - SLIPPAGE_FRACTION)
                exit_reason = "max_holding_period"

            if exit_reason is not None:
                pnl = (exit_price - entry_price) * quantity
                equity += pnl

                trades.append(
                    Trade(
                        symbol=symbol,
                        entry_time=entry_time,
                        exit_time=str(df.index[i]),
                        entry_price=entry_price,
                        exit_price=exit_price,
                        quantity=quantity,
                        pnl=pnl,
                        reason=exit_reason,
                    )
                )

                in_position = False
                entry_price = 0.0
                quantity = 0.0
                stop_price = 0.0
                take_profit_price = 0.0
                bars_held = 0

    return trades, equity


def summarise_trades(trades: list[Trade], final_equity: float) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame(
            [
                {
                    "trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "final_equity": final_equity,
                    "avg_win": 0.0,
                    "avg_loss": 0.0,
                }
            ]
        )

    pnl_series = pd.Series([t.pnl for t in trades])
    wins = pnl_series[pnl_series > 0]
    losses = pnl_series[pnl_series <= 0]

    return pd.DataFrame(
        [
            {
                "trades": int(len(trades)),
                "win_rate": float((pnl_series > 0).mean()),
                "total_pnl": float(pnl_series.sum()),
                "final_equity": float(final_equity),
                "avg_win": float(wins.mean()) if not wins.empty else 0.0,
                "avg_loss": float(losses.mean()) if not losses.empty else 0.0,
            }
        ]
    )


def main():
    all_trades = []
    symbol_rows = []

    for symbol in ["SPY", "QQQ", "GLD", "TLT"]:
        trades, final_equity = run_single_symbol_backtest(symbol)
        all_trades.extend(trades)

        summary = summarise_trades(trades, final_equity)
        summary.insert(0, "symbol", symbol)
        symbol_rows.append(summary)

        print(f"\n=== {symbol} ===")
        print(summary.to_string(index=False))

    full_summary = pd.concat(symbol_rows, ignore_index=True)

    print("\n=== COMBINED SUMMARY ===")
    print(full_summary.to_string(index=False))

    if all_trades:
        trades_df = pd.DataFrame([t.__dict__ for t in all_trades])
        print("\n=== SAMPLE TRADES ===")
        print(trades_df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
