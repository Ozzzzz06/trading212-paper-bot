"""
Stage 1 — read-only account check.

This script connects to the Trading 212 demo account and reports:
  - Account summary (total value, cash, invested)
  - Open positions
  - Pending orders

It places NO orders.  Its only purpose is to verify that:
  1. GitHub Actions can execute Python while your computer is off.
  2. The GitHub secrets are configured correctly.
  3. The demo API credentials are valid.
  4. The demo account shows approximately £5,000 in virtual capital.

Once this works, we proceed to Stage 2 (backtest) and Stage 3 (dry run).
"""

import json
from datetime import datetime, timezone

from broker import Trading212Client
from config import STAGE


def pretty(data: dict | list) -> str:
    """Return indented JSON string for readable log output."""
    return json.dumps(data, indent=2, default=str)


def main() -> None:
    print("=" * 60)
    print("Trading 212 paper-bot — Stage", STAGE, "account check")
    print("UTC time:", datetime.now(timezone.utc).isoformat())
    print("=" * 60)

    client = Trading212Client()

    print("\n--- ACCOUNT SUMMARY ---")
    summary = client.account_summary()
    print(pretty(summary))

    print("\n--- FREE CASH ---")
    cash = client.account_cash()
    print(pretty(cash))

    print("\n--- OPEN POSITIONS ---")
    positions = client.positions()
    if not positions:
        print("No open positions.")
    else:
        print(pretty(positions))

    print("\n--- PENDING ORDERS ---")
    orders = client.pending_orders()
    if not orders:
        print("No pending orders.")
    else:
        print(pretty(orders))

    print("\n" + "=" * 60)
    print("Check complete. No orders were placed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
