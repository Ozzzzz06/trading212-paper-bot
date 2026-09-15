# trading212-paper-bot

A Python-based paper-trading bot that connects to the [Trading 212](https://www.trading212.com/) demo API.

Built to trial a long-only EMA crossover strategy on liquid ETFs using £5,000 virtual capital, with the aim of learning systematic trading without risking real money.

---

## Strategy overview

- **Universe**: SPY, QQQ, IWM, GLD, TLT, EFA
- **Signal**: 20 EMA crosses above 50 EMA, confirmed by price above 200 EMA
- **Position sizing**: 0.25% account risk per trade, sized by ATR-based stop distance
- **Exit**: EMA crossover reversal, ATR stop-loss, or take-profit (2×R)
- **Execution**: GitHub Actions runs the bot every hour; Trading 212 broker-side stop and limit orders protect positions between runs

---

## Project stages

| Stage | Status | Description |
|-------|--------|-------------|
| 1 | 🟢 Current | Read-only account check |
| 2 | ⬜ Pending | Historical backtest |
| 3 | ⬜ Pending | Dry-run signal report (no orders placed) |
| 4 | ⬜ Pending | Demo order execution |
| 5 | ⬜ Pending | Reliability trial |

---

## File structure

```
trading212-paper-bot/
├── broker.py          # Trading 212 API client (read-only for now)
├── config.py          # Strategy and risk parameters
├── indicators.py      # EMA and ATR calculations
├── strategy.py        # Signal generation logic
├── risk.py            # Position sizing and exit-price calculation
├── paper_runner.py    # Main entry point (Stage 1: account check)
├── requirements.txt   # Python dependencies
├── .env.example       # Template for local environment variables
├── .gitignore
└── .github/
    └── workflows/
        └── paper-trader.yml  # GitHub Actions hourly schedule
```

---

## Setup

### 1. Get a Trading 212 demo API key

1. Log in to Trading 212.
2. Go to **Settings → API (Beta) → Generate API key**.
3. Copy the key and secret — the secret is shown only once.

### 2. Add secrets to GitHub

1. Open your repository on GitHub.
2. Click **Settings → Secrets and variables → Actions → New repository secret**.
3. Add two secrets:
   - `T212_API_KEY` — your demo API key
   - `T212_API_SECRET` — your demo API secret

### 3. Run manually

1. Click the **Actions** tab in your repository.
2. Select **Trading 212 paper trader**.
3. Click **Run workflow**.
4. Open the run and expand **Run paper trader** to see the output.

---

## Safety rules

- This bot **only** connects to `demo.trading212.com`. Live trading is blocked.
- `DRY_RUN = True` in `config.py` — no orders are placed at Stage 1.
- API keys should have the minimum necessary permissions.
- Never commit `.env` or paste API keys into Python files.

---

## Capital and risk parameters

| Parameter | Value |
|-----------|-------|
| Starting capital | £5,000 (virtual) |
| Risk per trade | 0.25% (£12.50) |
| Max portfolio exposure | 80% |
| Max position size | 25% of account |
| Max open positions | 4 |
| Daily loss limit | 1% |
| Drawdown shutdown | 10% |
