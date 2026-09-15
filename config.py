"""
Non-secret configuration for the paper trading bot.
Secrets (API keys) must be stored as GitHub Actions secrets.
"""

# ------------------------------------------------------------------ #
# Watchlist
# ------------------------------------------------------------------ #
# Six liquid ETFs covering equities, gold, and bonds.
# Ticker symbols must match Trading 212 instrument identifiers exactly.
# Verify them via broker.instruments() before running live.

SYMBOLS = [
    "SPY",   # US large-cap equities
    "QQQ",   # US tech-heavy equities
    "IWM",   # US small-cap equities
    "GLD",   # Gold
    "TLT",   # Long-term US Treasuries
    "EFA",   # Developed markets (ex-US)
]

# ------------------------------------------------------------------ #
# Capital and risk
# ------------------------------------------------------------------ #

STARTING_CAPITAL = 5_000.00          # Virtual account size in GBP
RISK_PER_TRADE = 0.0025              # 0.25% of equity per trade (£12.50)
MAX_PORTFOLIO_EXPOSURE = 0.80        # Never invest more than 80% of account
MAX_POSITION_EXPOSURE = 0.25         # Max 25% of account in one instrument
MAX_OPEN_POSITIONS = 4               # Maximum simultaneous long positions
MAX_DAILY_LOSS = 0.01                # Shut down if daily loss exceeds 1%
MAX_TOTAL_DRAWDOWN = 0.10            # Shut down if drawdown exceeds 10%

# ------------------------------------------------------------------ #
# Exit parameters
# ------------------------------------------------------------------ #

STOP_ATR_MULTIPLIER = 2.0            # Stop-loss = entry - 2 * ATR
TAKE_PROFIT_R_MULTIPLIER = 2.0       # Take-profit = entry + 2 * (stop distance)

# ------------------------------------------------------------------ #
# Indicator parameters
# ------------------------------------------------------------------ #

FAST_EMA = 20    # Fast exponential moving average (bars)
SLOW_EMA = 50    # Slow exponential moving average (bars)
TREND_EMA = 200  # Long-term trend filter (bars)
ATR_PERIOD = 14  # Average True Range period (bars)

# ------------------------------------------------------------------ #
# Safety
# ------------------------------------------------------------------ #

# Stage control: prevents accidental live trading.
# Stage 1 = read-only. Stage 2 = backtest. Stage 3 = dry run.
# Stage 4 = demo orders. Stage 5 = (never here yet).
STAGE = 1

# When True, print intended orders but do not submit them.
DRY_RUN = True

# Sanity check: raise immediately if someone tries to enable live trading.
LIVE_TRADING_ENABLED = False
if LIVE_TRADING_ENABLED:
    raise RuntimeError(
        "Live trading is disabled. This bot runs on the demo account only."
    )
