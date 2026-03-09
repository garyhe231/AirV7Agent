"""
Currency auto-population from country code.
Maps ISO country codes to their primary currency for air freight invoicing.
"""
from typing import Optional

# Country ISO code → primary billing currency
COUNTRY_CURRENCY: dict = {
    # Asia Pacific
    "CN": "CNY", "HK": "HKD", "TW": "TWD", "KR": "KRW",
    "JP": "JPY", "SG": "SGD", "MY": "MYR", "TH": "THB",
    "VN": "VND", "ID": "IDR", "PH": "PHP", "IN": "INR",
    "PK": "PKR", "BD": "BDT", "LK": "LKR",
    "AU": "AUD", "NZ": "NZD",
    # Americas
    "US": "USD", "CA": "CAD", "MX": "MXN",
    "BR": "BRL", "CL": "CLP", "CO": "COP", "PE": "PEN",
    "AR": "ARS",
    # Europe
    "DE": "EUR", "FR": "EUR", "IT": "EUR", "ES": "EUR",
    "NL": "EUR", "BE": "EUR", "AT": "EUR", "PT": "EUR",
    "FI": "EUR", "IE": "EUR", "GR": "EUR", "LU": "EUR",
    "GB": "GBP", "CH": "CHF", "SE": "SEK", "NO": "NOK",
    "DK": "DKK", "PL": "PLN", "CZ": "CZK", "HU": "HUF",
    "RO": "RON", "TR": "TRY",
    # Middle East & Africa
    "AE": "AED", "SA": "SAR", "QA": "QAR", "KW": "KWD",
    "BH": "BHD", "OM": "OMR", "IL": "ILS",
    "EG": "EGP", "MA": "MAD", "ZA": "ZAR", "KE": "KES",
    "NG": "NGN", "GH": "GHS", "TZ": "TZS",
    # Central Asia / Other
    "RU": "RUB", "UA": "UAH", "KZ": "KZT",
}

# When billing in USD is preferred regardless of origin (typical for air freight)
USD_PREFERRED_ORIGINS = {"US", "CA", "AU", "NZ", "SG", "HK", "AE", "SA"}


def get_currency_for_country(country_code: str) -> Optional[str]:
    """Return the primary currency for a given ISO 2-letter country code."""
    if not country_code:
        return None
    return COUNTRY_CURRENCY.get(country_code.upper())


def get_lane_currencies(origin_country: str, dest_country: str) -> dict:
    """
    Suggest origin, main freight, and destination currencies for a lane.
    Main freight is almost always USD for international air.
    Origin/dest billing follows local currency convention.
    """
    origin_ccy = get_currency_for_country(origin_country) or "USD"
    dest_ccy = get_currency_for_country(dest_country) or "USD"

    return {
        "origin_currency": origin_ccy,
        "main_currency": "USD",
        "dest_currency": dest_ccy,
        "note": f"Origin billing: {origin_ccy} | Main freight: USD | Destination billing: {dest_ccy}",
    }
