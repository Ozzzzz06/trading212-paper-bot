from dataclasses import dataclass

import pandas as pd

from config import STARTING_CAPITAL
from data import fetch_csv_data
from indicators import add_indicators
from risk import calculate_quantity, calculate_initial_stop, calculate_trailing_stop


SLIPPAGE_FRACTION = 0.0005

SYMBOLS = ["SPY", "QQQ", "GLD"]

MAX_TOTAL_EXPOSURE_FRACTION = 0.80
MAX_POSITION_EXPOSURE_FRACTION = 0.25
MAX_OPEN_POSITIONS = 3
RISK_PER_TRADE = 0.0025

INITIAL_STOP_ATR_MULTIPLE = 2.0
TRAILING_STOP_ATR_MULTIPLE = 4.0


@dataclass
class Position:
    symbol: str
    entry_time: str
    entry_price: float
    quantity: float
    stop_price: float
    bars_held: int
    signal_atr: float
    highest_close: float


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


def prepare_symbol_data(symbol: str) -> pd.DataFrame:
    df = fetch_csv_data(symbol)
    df = add_indicators(df).dropna().copy()
    df.index = pd.to_datetime(df.index, utc=True).normalize()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df["symbol"] = symbol
    return df


def build_master_dates(data_map: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    all_dates = set()
    for df in data_map.values():
        all_dates.update(df.index.tolist())
    return sorted(all_dates)


def get_common_start_date(data_map: dict[str, pd.DataFrame]) -> pd.Timestamp:
    return max(df.index.min() for df in data_map.values())


def portfolio_equity(
    cash: float,
    open_positions: dict[str, Position],
    price_map: dict[str, float],
) -> float:
    equity = cash
    for symbol, position in open_positions.items():
        if symbol in price_map:
            equity += position.quantity * price_map[symbol]
    return equity


def total_exposure(
    open_positions: dict[str, Position],
    price_map: dict[str, float],
) -> float:
    exposure = 0.0
    for symbol, position in open_positions.items():
        if symbol in price_map:
            exposure += position.quantity * price_map[symbol]
    return exposure


def run_portfolio_backtest():
    data_map = {symbol: prepare_symbol_data(symbol) for symbol in SYMBOLS}
    master_dates = build_master_dates(data_map)
    common_start = get_common_start_date(data_map)

    open_positions: dict[str, Position] = {}
    pending_entries: dict[str, float] = {}
    trades: list[Trade] = []
    equity_curve_rows: list[dict] = []

    cash = STARTING_CAPITAL
    ambiguous_exit_bars = 0

    for dt in master_dates:
        if dt < common_start:
            continue

        todays_rows = {}
        todays_closes = {}
        todays_opens = {}

        for symbol in SYMBOLS:
            df = data_map[symbol]
            if dt in df.index:
                row = df.loc[dt]
                todays_rows[symbol] = row
                todays_closes[symbol] = float(row["close"])
                todays_opens[symbol] = float(row["open"])

        if not todays_rows:
            continue

        # 1) Execute entries scheduled from prior signals at today's open
        for symbol in list(pending_entries.keys()):
            if symbol not in todays_rows:
                continue

            if symbol in open_positions:
                del pending_entries[symbol]
                continue

            if len(open_positions) >= MAX_OPEN_POSITIONS:
                del pending_entries[symbol]
                continue

            signal_atr = pending_entries[symbol]
            equity_at_open = portfolio_equity(cash, open_positions, todays_opens)
            exposure_at_open = total_exposure(open_positions, todays_opens)

            curr_open = todays_opens[symbol]
            entry_price = curr_open * (1 + SLIPPAGE_FRACTION)

            qty = calculate_quantity(
                equity=equity_at_open,
                entry_price=entry_price,
                stop_distance=INITIAL_STOP_ATR_MULTIPLE * signal_atr,
                risk_fraction=RISK_PER_TRADE,
                max_position_fraction=MAX_POSITION_EXPOSURE_FRACTION,
            )

            position_value = qty * entry_price
            max_total_exposure_value = equity_at_open * MAX_TOTAL_EXPOSURE_FRACTION

            if (
                qty > 0
                and position_value <= cash
                and (exposure_at_open + position_value) <= max_total_exposure_value
            ):
                stop_price = calculate_initial_stop(
                    entry_price=entry_price,
                    atr=signal_atr,
                    atr_multiple=INITIAL_STOP_ATR_MULTIPLE,
                )

                cash -= position_value

                open_positions[symbol] = Position(
                    symbol=symbol,
                    entry_time=str(dt),
                    entry_price=entry_price,
                    quantity=qty,
                    stop_price=stop_price,
                    bars_held=0,
                    signal_atr=signal_atr,
                    highest_close=float(todays_closes[symbol]),
                )

            del pending_entries[symbol]

        # 2) Process exits and trailing-stop updates
        for symbol in list(open_positions.keys()):
            if symbol not in todays_rows:
                continue

            current = todays_rows[symbol]
            position = open_positions[symbol]
            position.bars_held += 1

            curr_close = float(current["close"])
            curr_low = float(current["low"])
            curr_atr = float(current["atr"])

            position.highest_close = max(position.highest_close, curr_close)

            trailing_candidate = calculate_trailing_stop(
                highest_close=position.highest_close,
                atr=curr_atr,
                atr_multiple=TRAILING_STOP_ATR_MULTIPLE,
            )

            position.stop_price = max(position.stop_price, trailing_candidate)

            exit_reason = None
            exit_price = None

            if curr_low <= position.stop_price:
                exit_price = position.stop_price * (1 - SLIPPAGE_FRACTION)
                exit_reason = "trailing_stop"

            if exit_reason is not None:
                proceeds = exit_price * position.quantity
                pnl = (exit_price - position.entry_price) * position.quantity
                cash += proceeds

                trades.append(
                    Trade(
                        symbol=symbol,
                        entry_time=position.entry_time,
                        exit_time=str(dt),
                        entry_price=position.entry_price,
                        exit_price=exit_price,
                        quantity=position.quantity,
                        pnl=pnl,
                        reason=exit_reason,
                    )
                )

                del open_positions[symbol]

        # 3) Generate next-open signals using trend regime, not only fresh crossovers
        for symbol in SYMBOLS:
            if symbol not in todays_rows:
                continue

            if symbol in open_positions:
                continue

            current = todays_rows[symbol]

            curr_ema_fast = float(current["ema_fast"])
            curr_ema_slow = float(current["ema_slow"])
            curr_ema_trend = float(current["ema_trend"])
            curr_close = float(current["close"])
            curr_atr = float(current["atr"])

            trend_regime_long = (
                curr_ema_fast > curr_ema_slow
                and curr_close > curr_ema_trend
            )

            if trend_regime_long:
                pending_entries[symbol] = curr_atr

        equity_curve_rows.append(
            {
                "date": dt,
                "cash": cash,
                "open_positions": len(open_positions),
                "portfolio_equity": portfolio_equity(
                    cash, open_positions, todays_closes
                ),
            }
        )

    final_close_prices = {}
    for symbol, df in data_map.items():
        eligible = df[df.index >= common_start]
        if not eligible.empty:
            final_close_prices[symbol] = float(eligible.iloc[-1]["close"])

    final_equity = portfolio_equity(cash, open_positions, final_close_prices)
    equity_curve = pd.DataFrame(equity_curve_rows)
    trades_df = pd.DataFrame([t.__dict__ for t in trades]) if trades else pd.DataFrame()

    print("\n=== FINAL OPEN POSITIONS ===")

    if open_positions:
        final_position_rows = []

        for symbol, position in open_positions.items():
            current_price = final_close_prices[symbol]
            market_value = position.quantity * current_price
            unrealised_pnl = (
                (current_price - position.entry_price) * position.quantity
            )

            final_position_rows.append(
                {
                    "symbol": symbol,
                    "entry_time": position.entry_time,
                    "entry_price": position.entry_price,
                    "current_price": current_price,
                    "quantity": position.quantity,
                    "stop_price": position.stop_price,
                    "market_value": market_value,
                    "unrealised_pnl": unrealised_pnl,
                    "bars_held": position.bars_held,
                }
            )

        print(pd.DataFrame(final_position_rows).to_string(index=False))
    else:
        print("No open positions.")

    return trades, trades_df, final_equity, cash, ambiguous_exit_bars, equity_curve, common_start


def summarise_portfolio_trades(
    trades: list[Trade],
    trades_df: pd.DataFrame,
    final_equity: float,
    cash: float,
    ambiguous_exit_bars: int,
    equity_curve: pd.DataFrame,
    common_start: pd.Timestamp,
) -> pd.DataFrame:
    if equity_curve.empty:
        max_drawdown = 0.0
    else:
        running_peak = equity_curve["portfolio_equity"].cummax()
        drawdown = (equity_curve["portfolio_equity"] / running_peak) - 1.0
        max_drawdown = float(drawdown.min())

    total_return = (final_equity / STARTING_CAPITAL) - 1.0

    if equity_curve.empty:
        annualised_return = 0.0
    else:
        end_date = pd.Timestamp(equity_curve["date"].iloc[-1])
        years = max((end_date - common_start).days / 365.25, 1e-9)
        annualised_return = float((final_equity / STARTING_CAPITAL) ** (1 / years) - 1)

    if trades_df.empty:
        return pd.DataFrame(
            [
                {
                    "trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "total_return": total_return,
                    "annualised_return": annualised_return,
                    "max_drawdown": max_drawdown,
                    "final_equity": final_equity,
                    "cash": cash,
                    "avg_win": 0.0,
                    "avg_loss": 0.0,
                    "avg_holding_days": 0.0,
                    "trailing_stop_exits": 0,
                    "ambiguous_exit_bars": ambiguous_exit_bars,
                }
            ]
        )

    pnl_series = trades_df["pnl"]
    wins = pnl_series[pnl_series > 0]
    losses = pnl_series[pnl_series <= 0]
    reasons = trades_df["reason"]

    trades_df = trades_df.copy()
    trades_df["entry_time"] = pd.to_datetime(trades_df["entry_time"], utc=True)
    trades_df["exit_time"] = pd.to_datetime(trades_df["exit_time"], utc=True)
    trades_df["holding_days"] = (
        trades_df["exit_time"] - trades_df["entry_time"]
    ).dt.days

    return pd.DataFrame(
        [
            {
                "trades": int(len(trades_df)),
                "win_rate": float((pnl_series > 0).mean()),
                "total_pnl": float(pnl_series.sum()),
                "total_return": float(total_return),
                "annualised_return": float(annualised_return),
                "max_drawdown": float(max_drawdown),
                "final_equity": float(final_equity),
                "cash": float(cash),
                "avg_win": float(wins.mean()) if not wins.empty else 0.0,
                "avg_loss": float(losses.mean()) if not losses.empty else 0.0,
                "avg_holding_days": float(trades_df["holding_days"].mean()),
                "trailing_stop_exits": int((reasons == "trailing_stop").sum()),
                "ambiguous_exit_bars": int(ambiguous_exit_bars),
            }
        ]
    )


def summarise_by_symbol(trades_df: pd.DataFrame) -> pd.DataFrame:
    if trades_df.empty:
        return pd.DataFrame()

    temp = trades_df.copy()
    temp["entry_time"] = pd.to_datetime(temp["entry_time"], utc=True)
    temp["exit_time"] = pd.to_datetime(temp["exit_time"], utc=True)
    temp["holding_days"] = (temp["exit_time"] - temp["entry_time"]).dt.days

    rows = []
    for symbol, group in temp.groupby("symbol"):
        pnl_series = group["pnl"]
        wins = pnl_series[pnl_series > 0]
        losses = pnl_series[pnl_series <= 0]

        rows.append(
            {
                "symbol": symbol,
                "trades": int(len(group)),
                "win_rate": float((pnl_series > 0).mean()),
                "total_pnl": float(pnl_series.sum()),
                "avg_win": float(wins.mean()) if not wins.empty else 0.0,
                "avg_loss": float(losses.mean()) if not losses.empty else 0.0,
                "avg_holding_days": float(group["holding_days"].mean()),
                "trailing_stop_exits": int((group["reason"] == "trailing_stop").sum()),
            }
        )

    return pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def main():
    (
        trades,
        trades_df,
        final_equity,
        cash,
        ambiguous_exit_bars,
        equity_curve,
        common_start,
    ) = run_portfolio_backtest()

    portfolio_summary = summarise_portfolio_trades(
        trades,
        trades_df,
        final_equity,
        cash,
        ambiguous_exit_bars,
        equity_curve,
        common_start,
    )

    by_symbol = summarise_by_symbol(trades_df)

    print("\n=== PORTFOLIO SUMMARY ===")
    print(portfolio_summary.to_string(index=False))

    print(f"\nCommon start date: {common_start}")

    if not by_symbol.empty:
        print("\n=== BY SYMBOL ===")
        print(by_symbol.to_string(index=False))

    if not trades_df.empty:
        print("\n=== SAMPLE TRADES ===")
        print(trades_df.head(30).to_string(index=False))

    portfolio_summary.to_csv("portfolio_summary_dynamic_stop_v2.csv", index=False)
    by_symbol.to_csv("portfolio_by_symbol_dynamic_stop_v2.csv", index=False)
    equity_curve.to_csv("equity_curve_dynamic_stop_v2.csv", index=False)

    if not trades_df.empty:
        trades_df.to_csv("trades_dynamic_stop_v2.csv", index=False)


if __name__ == "__main__":
    main()