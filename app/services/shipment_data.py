"""
Shipment Level Data Model service.
Processes raw client shipment data (columns A-T from V7 sheet) and
auto-generates all 4 analytics: consolidation, density, seasonality, weighted average.
"""
import csv
import io
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Column A-T from the V7 shipment level data model tab
SHIPMENT_COLUMNS = [
    "shipment_date",        # A - date (YYYY-MM or YYYY-MM-DD)
    "origin_country",       # B
    "origin_city",          # C
    "origin_airport",       # D
    "destination_country",  # E
    "destination_city",     # F
    "destination_airport",  # G
    "service_tier",         # H - STD/EXP/DEF
    "actual_weight_kg",     # I
    "volume_cbm",           # J
    "chargeable_weight_kg", # K - calculated (provided or computed)
    "dim_ratio",            # L - default 6
    "dg_status",            # M - general cargo / lithium batteries / class 1-9
    "stackable",            # N - yes/no
    "packaging",            # O - loose/palletized
    "incoterms",            # P
    "sell_rate_per_kg",     # Q - optional
    "buy_rate_per_kg",      # R - optional
    "currency",             # S
    "notes",                # T
]

# Weight buckets for density analysis (dim ratio categories)
DENSITY_BUCKETS = [
    ("1:3 and below", 0, 3),
    ("1:4", 3, 4),
    ("1:5", 4, 5),
    ("1:6", 5, 6),
    ("1:7", 6, 7),
    ("1:8", 7, 8),
    ("1:9+", 8, 999),
]

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def parse_csv_shipments(csv_text: str) -> List[Dict[str, Any]]:
    """Parse uploaded CSV into list of shipment dicts."""
    reader = csv.DictReader(io.StringIO(csv_text))
    shipments = []
    for row in reader:
        s = {}
        for col in SHIPMENT_COLUMNS:
            val = row.get(col, "").strip()
            if col in ("actual_weight_kg", "volume_cbm", "chargeable_weight_kg",
                       "dim_ratio", "sell_rate_per_kg", "buy_rate_per_kg"):
                try:
                    s[col] = float(val) if val else None
                except ValueError:
                    s[col] = None
            else:
                s[col] = val or None
        # Compute chargeable weight if not provided
        if not s.get("chargeable_weight_kg"):
            actual = s.get("actual_weight_kg") or 0
            cbm = s.get("volume_cbm") or 0
            ratio = s.get("dim_ratio") or 6
            vol_weight = cbm * (1000 / ratio)
            s["chargeable_weight_kg"] = max(actual, vol_weight) if (actual or cbm) else None
        # Compute density ratio if possible
        if s.get("actual_weight_kg") and s.get("volume_cbm") and s["volume_cbm"] > 0:
            s["_density_ratio"] = s["actual_weight_kg"] / (s["volume_cbm"] * 1000 / 6)
        else:
            s["_density_ratio"] = None
        # Parse month/year from date
        date_str = s.get("shipment_date") or ""
        if len(date_str) >= 7:
            try:
                s["_year"] = int(date_str[:4])
                s["_month"] = int(date_str[5:7])
            except ValueError:
                s["_year"] = None
                s["_month"] = None
        else:
            s["_year"] = None
            s["_month"] = None
        # Port pair
        orig = s.get("origin_airport") or s.get("origin_city") or "?"
        dest = s.get("destination_airport") or s.get("destination_city") or "?"
        s["_port_pair"] = f"{orig} - {dest}"
        shipments.append(s)
    return shipments


def generate_consolidation(shipments: List[Dict[str, Any]],
                            award_pct: float = 0.5,
                            weeks: int = 52,
                            ftl_threshold: float = 4000) -> Dict[str, Any]:
    """Generate consolidation assessment from shipment data."""
    # Main freight: by port pair
    pair_cw: Dict[str, float] = defaultdict(float)
    for s in shipments:
        cw = s.get("chargeable_weight_kg") or 0
        pair_cw[s["_port_pair"]] += cw

    main_freight = []
    for pair, total_cw in sorted(pair_cw.items(), key=lambda x: -x[1]):
        weekly = total_cw / weeks
        awarded = weekly * award_pct
        main_freight.append({
            "port_pair": pair,
            "total_cw_kg": round(total_cw, 0),
            "weekly_cw_kg": round(weekly, 1),
            "awarded_weekly_kg": round(awarded, 1),
            "consolidation": "Yes" if awarded >= ftl_threshold else "No",
            "ftl_utilization_pct": round(awarded / ftl_threshold * 100, 1),
        })

    # Origin: by origin airport
    origin_cw: Dict[str, float] = defaultdict(float)
    for s in shipments:
        orig = s.get("origin_airport") or s.get("origin_city") or "?"
        origin_cw[orig] += s.get("chargeable_weight_kg") or 0

    origins = []
    for airport, total_cw in sorted(origin_cw.items(), key=lambda x: -x[1]):
        weekly = total_cw / weeks
        awarded = weekly * award_pct
        origins.append({
            "airport": airport,
            "total_cw_kg": round(total_cw, 0),
            "weekly_cw_kg": round(weekly, 1),
            "awarded_weekly_kg": round(awarded, 1),
            "consolidation": "Yes" if awarded >= ftl_threshold else "No",
        })

    # Destination: by destination airport
    dest_cw: Dict[str, float] = defaultdict(float)
    for s in shipments:
        dest = s.get("destination_airport") or s.get("destination_city") or "?"
        dest_cw[dest] += s.get("chargeable_weight_kg") or 0

    destinations = []
    for airport, total_cw in sorted(dest_cw.items(), key=lambda x: -x[1]):
        weekly = total_cw / weeks
        awarded = weekly * award_pct
        destinations.append({
            "airport": airport,
            "total_cw_kg": round(total_cw, 0),
            "weekly_cw_kg": round(weekly, 1),
            "awarded_weekly_kg": round(awarded, 1),
            "consolidation": "Yes" if awarded >= ftl_threshold else "No",
        })

    return {
        "main_freight": main_freight,
        "origins": origins,
        "destinations": destinations,
        "settings": {"award_pct": award_pct, "weeks": weeks, "ftl_threshold_kg": ftl_threshold},
        "total_shipments": len(shipments),
        "total_cw_kg": round(sum(s.get("chargeable_weight_kg") or 0 for s in shipments), 0),
    }


def generate_density(shipments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate density profile per port pair showing % per density bucket."""
    # Group by port pair
    pair_shipments: Dict[str, List[float]] = defaultdict(list)
    for s in shipments:
        ratio = s.get("_density_ratio")
        if ratio is not None:
            pair_shipments[s["_port_pair"]].append(ratio)

    results = []
    for pair, ratios in sorted(pair_shipments.items()):
        total = len(ratios)
        if total == 0:
            continue
        buckets = {}
        for label, low, high in DENSITY_BUCKETS:
            count = sum(1 for r in ratios if low < r <= high)
            buckets[label] = round(count / total * 100, 1)
        # Find dominant bucket
        dominant = max(buckets.items(), key=lambda x: x[1])
        results.append({
            "port_pair": pair,
            "total_shipments": total,
            "density_profile": buckets,
            "dominant_bucket": dominant[0],
            "dominant_pct": dominant[1],
        })

    # Overall density profile
    all_ratios = [s.get("_density_ratio") for s in shipments if s.get("_density_ratio") is not None]
    overall = {}
    if all_ratios:
        total = len(all_ratios)
        for label, low, high in DENSITY_BUCKETS:
            count = sum(1 for r in all_ratios if low < r <= high)
            overall[label] = round(count / total * 100, 1)

    return {
        "by_lane": results,
        "overall": overall,
        "total_shipments_with_dims": len(all_ratios),
        "note": "Density ratio = actual weight / (CBM × 1000/6). 1:6 = neutral, >1:6 = heavy, <1:6 = light/bulky",
    }


def generate_seasonality(shipments: List[Dict[str, Any]],
                          filter_pair: Optional[str] = None) -> Dict[str, Any]:
    """Generate monthly seasonality from shipment dates."""
    # Filter by port pair if requested
    filtered = [s for s in shipments if s.get("_month") is not None]
    if filter_pair:
        filtered = [s for s in filtered if s["_port_pair"] == filter_pair]

    # Monthly CW
    monthly_cw: Dict[int, float] = defaultdict(float)
    yearly_monthly: Dict[int, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for s in filtered:
        m = s["_month"]
        y = s["_year"]
        cw = s.get("chargeable_weight_kg") or 0
        monthly_cw[m] += cw
        if y:
            yearly_monthly[y][m] += cw

    total = sum(monthly_cw.values())
    monthly_result = []
    for i, month in enumerate(MONTHS, 1):
        cw = monthly_cw.get(i, 0)
        pct = round(cw / total * 100, 1) if total else 0
        monthly_result.append({
            "month": month,
            "month_num": i,
            "cw_kg": round(cw, 0),
            "pct": pct,
            "is_peak": pct > (100 / 12 * 1.1),
        })

    peak_months = [m["month"] for m in monthly_result if m["is_peak"]]

    # Per year breakdown
    yearly = {}
    for year, months in sorted(yearly_monthly.items()):
        yearly[str(year)] = {MONTHS[m-1]: round(v, 0) for m, v in months.items()}

    return {
        "monthly": monthly_result,
        "peak_months": peak_months,
        "pss_months": ["Sep", "Oct", "Nov", "Dec"],
        "pss_volume_pct": round(sum(m["pct"] for m in monthly_result if m["month"] in ["Sep","Oct","Nov","Dec"]), 1),
        "total_cw_kg": round(total, 0),
        "by_year": yearly,
        "filter_applied": filter_pair or "all lanes",
    }


def generate_weighted_average(shipments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate weighted average by port pair showing concentration per weight break.
    Weight breaks: <45, 45-99, 100-299, 300-499, 500-999, 1000-1999, 2000+
    """
    BREAKS = [
        ("Min (<45kg)", 0, 45),
        ("+45kg", 45, 100),
        ("+100kg", 100, 300),
        ("+300kg", 300, 500),
        ("+500kg", 500, 1000),
        ("+1000kg", 1000, 2000),
        ("+2000kg", 2000, 999999),
    ]

    pair_shipments: Dict[str, List[float]] = defaultdict(list)
    for s in shipments:
        cw = s.get("chargeable_weight_kg")
        if cw is not None and cw > 0:
            pair_shipments[s["_port_pair"]].append(cw)

    results = []
    for pair, cws in sorted(pair_shipments.items()):
        total = len(cws)
        total_cw = sum(cws)
        avg_cw = total_cw / total if total else 0

        break_dist = {}
        for label, low, high in BREAKS:
            count = sum(1 for c in cws if low <= c < high)
            pct = round(count / total * 100, 1) if total else 0
            break_dist[label] = {"count": count, "pct": pct}

        # Find the dominant break (by shipment count)
        dominant = max(break_dist.items(), key=lambda x: x[1]["pct"])

        # Weighted average CW
        weighted_avg = round(sum(c * c for c in cws) / total_cw if total_cw else 0, 1)

        results.append({
            "port_pair": pair,
            "total_shipments": total,
            "total_cw_kg": round(total_cw, 0),
            "avg_shipment_kg": round(avg_cw, 1),
            "weighted_avg_kg": weighted_avg,
            "dominant_break": dominant[0],
            "dominant_break_pct": dominant[1]["pct"],
            "break_distribution": break_dist,
        })

    return {"by_lane": results, "total_shipments": len(shipments)}


def process_shipment_data(csv_text: str,
                           award_pct: float = 0.5,
                           weeks: int = 52,
                           ftl_threshold: float = 4000) -> Dict[str, Any]:
    """Full pipeline: parse CSV → generate all 4 analytics."""
    shipments = parse_csv_shipments(csv_text)
    if not shipments:
        return {"error": "No valid shipment rows found in uploaded data"}

    return {
        "total_shipments": len(shipments),
        "consolidation": generate_consolidation(shipments, award_pct, weeks, ftl_threshold),
        "density": generate_density(shipments),
        "seasonality": generate_seasonality(shipments),
        "weighted_average": generate_weighted_average(shipments),
    }


def get_sample_csv_template() -> str:
    """Return a sample CSV template with headers and 3 example rows."""
    headers = ",".join(SHIPMENT_COLUMNS)
    rows = [
        "2026-01,CN,Shanghai,PVG,US,Los Angeles,LAX,STD,520,3.2,,6,General Cargo,Yes,Palletized,EXW,,,USD,",
        "2026-01,CN,Shanghai,PVG,US,New York,JFK,EXP,310,2.8,,6,General Cargo,Yes,Palletized,EXW,,,USD,",
        "2026-02,CN,Guangzhou,CAN,US,Los Angeles,LAX,STD,680,4.5,,6,General Cargo,No,Loose,EXW,,,USD,",
    ]
    return headers + "\n" + "\n".join(rows)
