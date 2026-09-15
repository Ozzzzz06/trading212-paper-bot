import os
import requests


class Trading212Client:
    """
    Read-only client for the Trading 212 demo API.
    Only connects to the practice (demo) environment.
    Order placement is disabled until Stage 4.
    """

    BASE_URL = "https://demo.trading212.com/api/v0"

    def __init__(self):
        api_key = os.environ.get("T212_API_KEY")
        api_secret = os.environ.get("T212_API_SECRET")

        if not api_key or not api_secret:
            raise RuntimeError(
                "T212_API_KEY and T212_API_SECRET environment variables "
                "are not set. Add them as GitHub Actions secrets."
            )

        self.session = requests.Session()
        self.session.auth = (api_key, api_secret)
        self.session.headers.update(
            {"User-Agent": "oz-trading212-paper-bot/0.1"}
        )

    def _get(self, path: str) -> dict | list:
        """Make a GET request to the demo API and return parsed JSON."""
        url = f"{self.BASE_URL}{path}"
        response = self.session.get(url, timeout=20)

        if not response.ok:
            raise RuntimeError(
                f"Trading 212 API error {response.status_code} "
                f"on {path}: {response.text}"
            )

        return response.json()

    # ------------------------------------------------------------------ #
    # Account
    # ------------------------------------------------------------------ #

    def account_summary(self) -> dict:
        """Return cash, invested, and total portfolio value."""
        return self._get("/equity/account/summary")

    def account_cash(self) -> dict:
        """Return free cash available for trading."""
        return self._get("/equity/account/cash")

    # ------------------------------------------------------------------ #
    # Positions
    # ------------------------------------------------------------------ #

    def positions(self) -> list:
        """Return all open positions."""
        return self._get("/equity/positions")

    # ------------------------------------------------------------------ #
    # Orders
    # ------------------------------------------------------------------ #

    def pending_orders(self) -> list:
        """Return all pending (unfilled) orders."""
        return self._get("/equity/orders")

    # ------------------------------------------------------------------ #
    # Instruments
    # ------------------------------------------------------------------ #

    def instruments(self) -> list:
        """Return all tradeable instruments on the platform."""
        return self._get("/equity/metadata/instruments")
