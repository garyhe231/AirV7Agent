from typing import Dict, List, Optional

# ─── 2026 Focus Lanes (full list from V7) ────────────────────────────────────
FOCUS_LANES: List[Dict[str, str]] = [
    {"pair": "AMS-ORD", "tradelane": "TAWB"}, {"pair": "AMS-JFK", "tradelane": "TAWB"},
    {"pair": "AMS-SFO", "tradelane": "TAWB"}, {"pair": "AMS-ATL", "tradelane": "TAWB"},
    {"pair": "AMS-DFW", "tradelane": "TAWB"}, {"pair": "AMS-PVG", "tradelane": "FEEB"},
    {"pair": "AMS-LAX", "tradelane": "TAWB"}, {"pair": "AMS-SGN", "tradelane": "FEEB"},
    {"pair": "AMS-HKG", "tradelane": "FEEB"}, {"pair": "AMS-BOM", "tradelane": "FEEB"},
    {"pair": "AMS-SIN", "tradelane": "FEEB"}, {"pair": "AMS-TPE", "tradelane": "FEEB"},
    {"pair": "ATL-AMS", "tradelane": "TAEB"}, {"pair": "ATL-PVG", "tradelane": "TPWB"},
    {"pair": "ATL-LHR", "tradelane": "TAEB"}, {"pair": "ATL-BKK", "tradelane": "TPWB"},
    {"pair": "ATL-SGN", "tradelane": "TPWB"}, {"pair": "ATL-FRA", "tradelane": "TAEB"},
    {"pair": "ATL-MXP", "tradelane": "TAEB"}, {"pair": "BKK-LAX", "tradelane": "TPWB"},
    {"pair": "BKK-ORD", "tradelane": "TPWB"}, {"pair": "BKK-JFK", "tradelane": "TPWB"},
    {"pair": "BKK-LHR", "tradelane": "FEEB"}, {"pair": "BOM-JFK", "tradelane": "FEEB"},
    {"pair": "BOM-ORD", "tradelane": "FEEB"}, {"pair": "BOM-LAX", "tradelane": "FEEB"},
    {"pair": "CAN-LAX", "tradelane": "TPWB"}, {"pair": "CAN-JFK", "tradelane": "TPWB"},
    {"pair": "CAN-ORD", "tradelane": "TPWB"}, {"pair": "CAN-LHR", "tradelane": "FEEB"},
    {"pair": "CGK-LAX", "tradelane": "TPWB"}, {"pair": "CGK-JFK", "tradelane": "TPWB"},
    {"pair": "DEL-JFK", "tradelane": "FEEB"}, {"pair": "DEL-ORD", "tradelane": "FEEB"},
    {"pair": "DEL-LHR", "tradelane": "FEEB"}, {"pair": "DXB-JFK", "tradelane": "FEEB"},
    {"pair": "FRA-JFK", "tradelane": "TAEB"}, {"pair": "FRA-LAX", "tradelane": "TAEB"},
    {"pair": "FRA-ORD", "tradelane": "TAEB"}, {"pair": "FRA-PVG", "tradelane": "FEEB"},
    {"pair": "HKG-LAX", "tradelane": "TPWB"}, {"pair": "HKG-JFK", "tradelane": "TPWB"},
    {"pair": "HKG-ORD", "tradelane": "TPWB"}, {"pair": "HKG-LHR", "tradelane": "FEEB"},
    {"pair": "ICN-LAX", "tradelane": "TPWB"}, {"pair": "ICN-JFK", "tradelane": "TPWB"},
    {"pair": "ICN-ORD", "tradelane": "TPWB"}, {"pair": "ICN-LHR", "tradelane": "FEEB"},
    {"pair": "JFK-AMS", "tradelane": "TAEB"}, {"pair": "JFK-FRA", "tradelane": "TAEB"},
    {"pair": "JFK-LHR", "tradelane": "TAEB"}, {"pair": "JFK-PVG", "tradelane": "TPEB"},
    {"pair": "KUL-LAX", "tradelane": "TPWB"}, {"pair": "KUL-JFK", "tradelane": "TPWB"},
    {"pair": "LAX-AMS", "tradelane": "TAEB"}, {"pair": "LAX-FRA", "tradelane": "TAEB"},
    {"pair": "LAX-LHR", "tradelane": "TAEB"}, {"pair": "LAX-PVG", "tradelane": "TPEB"},
    {"pair": "LAX-ICN", "tradelane": "TPEB"}, {"pair": "LAX-HKG", "tradelane": "TPEB"},
    {"pair": "LHR-JFK", "tradelane": "TAEB"}, {"pair": "LHR-LAX", "tradelane": "TAEB"},
    {"pair": "LHR-ORD", "tradelane": "TAEB"}, {"pair": "LHR-PVG", "tradelane": "FEEB"},
    {"pair": "MXP-JFK", "tradelane": "TAEB"}, {"pair": "MXP-LAX", "tradelane": "TAEB"},
    {"pair": "NRT-LAX", "tradelane": "TPWB"}, {"pair": "NRT-JFK", "tradelane": "TPWB"},
    {"pair": "NRT-ORD", "tradelane": "TPWB"}, {"pair": "NRT-LHR", "tradelane": "FEEB"},
    {"pair": "ORD-AMS", "tradelane": "TAEB"}, {"pair": "ORD-FRA", "tradelane": "TAEB"},
    {"pair": "ORD-LHR", "tradelane": "TAEB"}, {"pair": "ORD-PVG", "tradelane": "TPEB"},
    {"pair": "PVG-LAX", "tradelane": "TPWB"}, {"pair": "PVG-JFK", "tradelane": "TPWB"},
    {"pair": "PVG-ORD", "tradelane": "TPWB"}, {"pair": "PVG-LHR", "tradelane": "FEEB"},
    {"pair": "PVG-AMS", "tradelane": "FEEB"}, {"pair": "PVG-FRA", "tradelane": "FEEB"},
    {"pair": "SIN-LAX", "tradelane": "TPWB"}, {"pair": "SIN-JFK", "tradelane": "TPWB"},
    {"pair": "SIN-ORD", "tradelane": "TPWB"}, {"pair": "SIN-LHR", "tradelane": "FEEB"},
    {"pair": "SGN-LAX", "tradelane": "TPWB"}, {"pair": "SGN-JFK", "tradelane": "TPWB"},
    {"pair": "SGN-ORD", "tradelane": "TPWB"}, {"pair": "TPE-LAX", "tradelane": "TPWB"},
    {"pair": "TPE-JFK", "tradelane": "TPWB"}, {"pair": "TPE-ORD", "tradelane": "TPWB"},
]

FOCUS_LANE_SET = {lane["pair"] for lane in FOCUS_LANES}


def is_focus_lane(origin: str, dest: str) -> Optional[Dict[str, str]]:
    key = f"{origin.upper()}-{dest.upper()}"
    for lane in FOCUS_LANES:
        if lane["pair"] == key:
            return lane
    return None


def get_focus_lanes_by_tradelane(tradelane: str) -> List[Dict[str, str]]:
    return [l for l in FOCUS_LANES if l["tradelane"] == tradelane]


# ─── Ownership Matrix ────────────────────────────────────────────────────────
OWNERSHIP: Dict[str, Dict[str, str]] = {
    "AU": {"country": "Australia", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "BD": {"country": "Bangladesh", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "KH": {"country": "Cambodia", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "CN": {"country": "China", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "HK": {"country": "Hong Kong", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "IN": {"country": "India", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "ID": {"country": "Indonesia", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "JP": {"country": "Japan", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "MY": {"country": "Malaysia", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "PH": {"country": "Philippines", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "PK": {"country": "Pakistan", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "SG": {"country": "Singapore", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "KR": {"country": "South Korea", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "LK": {"country": "Sri Lanka", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "TW": {"country": "Taiwan", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "TH": {"country": "Thailand", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "VN": {"country": "Vietnam", "air_freight": "Asia TLM", "origin_trucking": "Asia Trucking", "dest_trucking": "Asia Trucking"},
    "US": {"country": "United States", "air_freight": "Americas TLM", "origin_trucking": "Americas TLM", "dest_trucking": "Americas TLM"},
    "CA": {"country": "Canada", "air_freight": "Americas TLM", "origin_trucking": "Americas TLM", "dest_trucking": "Americas TLM"},
    "MX": {"country": "Mexico", "air_freight": "Americas TLM", "origin_trucking": "Americas TLM", "dest_trucking": "Americas TLM"},
    "BR": {"country": "Brazil", "air_freight": "Americas TLM", "origin_trucking": "Americas TLM", "dest_trucking": "Americas TLM"},
    "NL": {"country": "Netherlands", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "DE": {"country": "Germany", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "GB": {"country": "United Kingdom", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "FR": {"country": "France", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "IT": {"country": "Italy", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "ES": {"country": "Spain", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "BE": {"country": "Belgium", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "SE": {"country": "Sweden", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "PL": {"country": "Poland", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "AE": {"country": "UAE", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
    "ZA": {"country": "South Africa", "air_freight": "EMEA TLM", "origin_trucking": "EMEA Trucking", "dest_trucking": "EMEA Trucking"},
}


def get_ownership(country_code: str) -> Optional[Dict[str, str]]:
    return OWNERSHIP.get(country_code.upper())


def get_lane_owners(origin_country: str, dest_country: str) -> Dict[str, str]:
    origin_owner = OWNERSHIP.get(origin_country.upper(), {})
    dest_owner = OWNERSHIP.get(dest_country.upper(), {})
    return {
        "origin_air_freight_owner": origin_owner.get("air_freight", "Unknown"),
        "origin_trucking_owner": origin_owner.get("origin_trucking", "Unknown"),
        "dest_trucking_owner": dest_owner.get("dest_trucking", "Unknown"),
    }
