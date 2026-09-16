import pandas as pd

from data import fetch_csv_data
from indicators import add_indicators


STARTING_CAPITAL = 5000.0
SYMBOLS = ["SPY", "QQQ", "GLD"]


def load_data(symbol: str) -> pd.DataFrame:
    df = fetch_csv_data(symbol)
    df = add_indicators(df).dropna().copy()

    df.index = pd.to_datetime(df.index, utc=True).normalize()
    df = df[~df.index.duplicated(keep="last")].sort_index()

    return df


def max_drawdown(equity: pd.Series) -> float:
    running_peak = equity.cummax()
    drawdown = (equity / running_peak) - 1.0
    return float(drawdown.min())


def annualised_return(start_value: float, end_value: float, start_date, end_date) -> float:
    years = max((end_date - start_date).days / 365.25, 1e-9)
    return float((end_value / start_value) ** (1 / years) - 1.0)


def main():
    data = {symbol: load_data(symbol) for symbol in SYMBOLS}

    common_start = max(df.index.min() for df in data.values())
    common_end = min(df.index.max() for df in data.values())

    closes = pd.DataFrame(
        {
            symbol: df.loc[
                (df.index >= common_start) & (df.index <= common_end),
                "close",
            ]
            for symbol, df in data.items()
        }
    ).ffill().dropna()

    normalised = closes / closes.iloc[0]

    individual_rows = []
    for symbol in SYMBOLS:
        equity = STARTING_CAPITAL * normalised[symbol]
        individual_rows.append(
            {
                "portfolio": f"{symbol} buy-and-hold",
                "final_equity": float(equity.iloc[-1]),
                "total_return": float((equity.iloc[-1] / STARTING_CAPITAL) - 1.0),
                "annualised_return": annualised_return(
                    STARTING_CAPITAL,
                    float(equity.iloc[-1]),
                    closes.index[0],
                    closes.index[-1],
                ),
                "max_drawdown": max_drawdown(equity),
            }
        )

    equal_weight_equity = STARTING_CAPITAL * normalised.mean(axis=1)

    individual_rows.append(
        {
            "portfolio": "Equal-weight SPY / QQQ / GLD",
            "final_equity": float(equal_weight_equity.iloc[-1]),
            "total_return": float(
                (equal_weight_equity.iloc[-1] / STARTING_CAPITAL) - 1.0
            ),
            "annualised_return": annualised_return(
                STARTING_CAPITAL,
                float(equal_weight_equity.iloc[-1]),
                closes.index[0],
                closes.index[-1],
            ),
            "max_drawdown": max_drawdown(equal_weight_equity),
        }
    )

    summary = pd.DataFrame(individual_rows)

    print("\n=== BENCHMARK PERIOD ===")
    print(f"Start: {closes.index[0]}")
    print(f"End:   {closes.index[-1]}")

    print("\n=== BUY-AND-HOLD BENCHMARKS ===")
    print(summary.to_string(index=False))

    output = pd.DataFrame(
        {
            "SPY_buy_and_hold": STARTING_CAPITAL * normalised["SPY"],
            "QQQ_buy_and_hold": STARTING_CAPITAL * normalised["QQQ"],
            "GLD_buy_and_hold": STARTING_CAPITAL * normalised["GLD"],
            "equal_weight_buy_and_hold": equal_weight_equity,
        }
    )
    output.to_csv("benchmark_equity_curve.csv", index_label="date")


if __name__ == "__main__":
    main()