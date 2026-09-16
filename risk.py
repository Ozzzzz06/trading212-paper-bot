def calculate_quantity(
    equity: float,
    entry_price: float,
    stop_distance: float,
    risk_fraction: float = 0.0025,
    max_position_fraction: float = 0.25,
) -> float:
    if equity <= 0 or entry_price <= 0 or stop_distance <= 0:
        return 0.0

    risk_budget = equity * risk_fraction
    qty_by_risk = risk_budget / stop_distance

    max_position_value = equity * max_position_fraction
    qty_by_cap = max_position_value / entry_price

    qty = min(qty_by_risk, qty_by_cap)
    return max(qty, 0.0)


def calculate_initial_stop(
    entry_price: float,
    atr: float,
    atr_multiple: float = 2.0,
) -> float:
    return entry_price - (atr_multiple * atr)


def calculate_trailing_stop(
    highest_close: float,
    atr: float,
    atr_multiple: float = 3.0,
) -> float:
    return highest_close - (atr_multiple * atr)