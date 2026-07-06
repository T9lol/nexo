"""Currency presentation helpers.

RM (MYR) is the primary display currency across NeXo. USD figures are an
*approximate* convenience, derived from a placeholder rate — there is no live FX
feed integrated — so every USD amount is flagged ``usd_is_approximate``.

These helpers are pure presentation: they never touch trading state or engine
math. The numeric portfolio/equity values produced by the engine are treated as
MYR-primary, consistent with the frontend.
"""

from __future__ import annotations

from typing import Any

# Kept in sync with the frontend PLACEHOLDER_USD_MYR_RATE. Overridable via
# NEXO_USD_MYR_RATE (see api.config.Settings.usd_myr_rate).
PLACEHOLDER_USD_MYR_RATE = 4.7


def to_usd(amount_myr: float, rate: float) -> float | None:
    """Approximate a MYR amount in USD (``1 USD ~= rate MYR``)."""

    if not rate:
        return None
    return round(amount_myr / rate, 2)


def money(amount_myr: float, rate: float) -> dict[str, Any]:
    """Return a MYR-primary money object with an approximate USD figure."""

    return {
        "myr": round(amount_myr, 2),
        "usd": to_usd(amount_myr, rate),
        "usd_is_approximate": True,
    }


def currency_meta(rate: float) -> dict[str, Any]:
    """Response ``meta`` block documenting the currency basis."""

    return {
        "api_version": "v1",
        "currency": {
            "primary": "MYR",
            "usd_myr_rate": rate,
            "usd_is_approximate": True,
        },
    }
