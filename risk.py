"""
Position-sizing and exit-price calculations.

All sizing is based on the distance to the stop-loss,
not on a fixed pound amount per instrument.

Example with £5,000 account:
    risk_budget  = £5,000 × 0.0025 = £12.50
    stop_distance = 2 × ATR = £4.00
    quantity      = £12.50 / £4.00 = 3.125 shares
    position cap  = £5,000 × 0.25 / £100 = 12.5 shares  (not binding here)
    result        = 3.125 shares
"""


def calculate_quantity(
    equity: float,
    entry_price: float,
    stop_distance: float,
    risk_fraction: float = 0.0025,
    max_position_fraction: float = 0.25,
) -> float:
    """
    Calculate the number of shares to buy.

    Returns 0.0 if the inputs are invalid (prevents divide-by-zero).
    The result is NOT rounded to integers — Trading 212 supports
    fractional shares.  Round externally if required.
    """
    if entry_price <= 0 or stop_distance <= 0 or equity <= 0:
        return 0.0

    risk_budget = equity * risk_fraction
    quantity_from_risk = risk_budget / stop_distance

    max_value = equity * max_position_fraction
    quantity_from_cap = max_value / entry_price

    return min(quantity_from_risk, quantity_from_cap)


def calculate_exit_prices(
    entry_price: float,
    atr: float,
    stop_multiplier: float = 2.0,
    reward_multiple: float = 2.0,
) -> tuple[float, float]:
    """
    Return (stop_price, take_profit_price) for a long position.

    stop_price        = entry - stop_multiplier × ATR
    take_profit_price = entry + reward_multiple × stop_distance

    With 2:1 reward-to-risk, if ATR = £1.50:
        stop_distance    = 2 × £1.50 = £3.00
        stop_price       = entry - £3.00
        take_profit      = entry + £6.00
    """
    stop_distance = atr * stop_multiplier
    stop_price = entry_price - stop_distance
    take_profit_price = entry_price + stop_distance * reward_multiple

    return stop_price, take_profit_price
