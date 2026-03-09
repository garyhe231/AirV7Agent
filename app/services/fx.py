from typing import Dict, Optional

# FX rates from V7 template (as of 2026-02-17): 1 unit of FROM currency = X USD
TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "CAD": 0.73322,
    "GBP": 1.3563,
    "EUR": 1.185125,
    "SEK": 0.1114936,
    "DKK": 0.1586322,
    "CNY": 0.1447461,
    "HKD": 0.1279533,
    "JPY": 0.006528395,
    "AUD": 0.708285,
    "IDR": 0.0000593435,
    "LKR": 0.003237559,
    "MYR": 0.1244552,
    "SGD": 0.0172981,
}

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "CNY": "¥", "HKD": "HK$",
    "AUD": "A$", "CAD": "C$", "JPY": "¥", "SGD": "S$", "MYR": "RM",
}


def convert_to_usd(amount: float, from_currency: str) -> float:
    rate = TO_USD.get(from_currency.upper(), 1.0)
    return round(amount * rate, 4)


def convert(amount: float, from_currency: str, to_currency: str) -> float:
    usd = convert_to_usd(amount, from_currency)
    to_rate = TO_USD.get(to_currency.upper(), 1.0)
    return round(usd / to_rate, 4)


def get_all_rates() -> Dict[str, float]:
    return TO_USD.copy()


def get_supported_currencies():
    return list(TO_USD.keys())
