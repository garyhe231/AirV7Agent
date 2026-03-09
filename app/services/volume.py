from typing import List, Dict, Any, Optional

FTL_THRESHOLD_KG = 4000  # default consolidation threshold
AWARD_DEFAULT = 0.50     # default award assumption 50%
WEEKS_PER_YEAR = 52


def analyze_volume(lanes: List[Dict[str, Any]], award_pct: float = AWARD_DEFAULT,
                   ftl_threshold: float = FTL_THRESHOLD_KG) -> Dict[str, Any]:
    """Compute weekly volume, awarded volume, consolidation potential per lane."""
    results = []
    total_annual_cw = 0
    total_awarded_cw = 0

    for lane in lanes:
        annual_cw = lane.get("chargeable_weight_kg") or 0
        weekly_cw = annual_cw / WEEKS_PER_YEAR
        awarded_weekly = weekly_cw * award_pct
        can_consolidate = awarded_weekly >= ftl_threshold

        results.append({
            "lane_id": lane.get("lane_id"),
            "port_pair": f"{lane.get('origin_airport','?')} - {lane.get('destination_airport','?')}",
            "annual_cw_kg": round(annual_cw, 0),
            "weekly_cw_kg": round(weekly_cw, 1),
            "awarded_weekly_kg": round(awarded_weekly, 1),
            "award_pct": award_pct,
            "consolidation": "Yes" if can_consolidate else "No",
            "ftl_threshold_kg": ftl_threshold,
            "utilization_pct": round((awarded_weekly / ftl_threshold * 100), 1) if ftl_threshold else 0,
        })
        total_annual_cw += annual_cw
        total_awarded_cw += annual_cw * award_pct

    return {
        "lanes": results,
        "summary": {
            "total_annual_cw_kg": round(total_annual_cw, 0),
            "total_awarded_cw_kg": round(total_awarded_cw, 0),
            "award_pct": award_pct,
            "weeks": WEEKS_PER_YEAR,
            "ftl_threshold_kg": ftl_threshold,
            "lanes_that_can_consolidate": sum(1 for r in results if r["consolidation"] == "Yes"),
            "total_lanes": len(results),
        }
    }


def analyze_seasonality(lanes: List[Dict[str, Any]],
                        monthly_dist: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Distribute annual volume across months using a seasonality profile.
    monthly_dist: list of 12 weights (will be normalized). Default = flat.
    """
    if not monthly_dist or len(monthly_dist) != 12:
        # Default: slight peak in Q4 (Sep-Dec), typical air freight pattern
        monthly_dist = [0.075, 0.070, 0.080, 0.080, 0.085, 0.080,
                        0.080, 0.085, 0.090, 0.095, 0.095, 0.085]

    total_weight = sum(monthly_dist)
    normalized = [w / total_weight for w in monthly_dist]

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    total_annual = sum(l.get("chargeable_weight_kg") or 0 for l in lanes)

    monthly_volumes = []
    for i, (month, pct) in enumerate(zip(months, normalized)):
        vol = total_annual * pct
        monthly_volumes.append({
            "month": month,
            "pct": round(pct * 100, 1),
            "volume_kg": round(vol, 0),
            "is_peak": pct > (1 / 12 * 1.1),  # >10% above flat baseline
        })

    peak_months = [m["month"] for m in monthly_volumes if m["is_peak"]]

    return {
        "monthly_volumes": monthly_volumes,
        "total_annual_kg": round(total_annual, 0),
        "peak_months": peak_months,
        "pss_applicable_months": ["Sep", "Oct", "Nov", "Dec"],
    }


def compute_weighted_average_rate(lanes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute shipment-mix-weighted average sell rate across weight breaks.
    Uses the +1000kg sell rate as the primary rate for now.
    """
    results = []
    total_cw = sum(l.get("chargeable_weight_kg") or 0 for l in lanes)

    for lane in lanes:
        cw = lane.get("chargeable_weight_kg") or 0
        sell = lane.get("sell_rate_per_kg") or 0
        weight = cw / total_cw if total_cw else 0
        results.append({
            "port_pair": f"{lane.get('origin_airport','?')} - {lane.get('destination_airport','?')}",
            "cw_kg": cw,
            "sell_per_kg": sell,
            "weight_pct": round(weight * 100, 1),
            "weighted_contribution": round(sell * weight, 4),
        })

    weighted_avg = sum(r["weighted_contribution"] for r in results)

    return {
        "lanes": results,
        "weighted_avg_sell_per_kg": round(weighted_avg, 4),
        "total_cw_kg": round(total_cw, 0),
    }


def milk_run_assessment(lanes: List[Dict[str, Any]],
                        focus_zip_codes: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Assess which destination lanes may benefit from milk run (multi-stop) trucking.
    Milk run is relevant for US destinations (LAX, ORD) with multiple nearby delivery points.
    """
    milk_run_candidates = []
    standard_delivery = []

    us_hubs = {"LAX", "ORD", "JFK", "SFO", "EWR", "ATL", "DFW", "SEA", "BOS", "MIA"}

    for lane in lanes:
        dest_airport = (lane.get("destination_airport") or "").upper()
        dest_country = (lane.get("destination_country") or "").upper()
        weekly_cw = (lane.get("chargeable_weight_kg") or 0) / WEEKS_PER_YEAR

        is_us = dest_country == "US" or dest_airport in us_hubs
        is_milk_run_hub = dest_airport in {"LAX", "ORD"}  # primary milk run hubs per V7

        entry = {
            "lane_id": lane.get("lane_id"),
            "port_pair": f"{lane.get('origin_airport','?')} - {dest_airport}",
            "dest_airport": dest_airport,
            "weekly_cw_kg": round(weekly_cw, 1),
            "delivery_cost_per_kg": lane.get("delivery_min") or lane.get("delivery_kg_1000") or 0,
        }

        if is_milk_run_hub and weekly_cw > 500:
            entry["recommendation"] = "Evaluate milk run — check MRTC for zip code coverage"
            entry["milk_run_eligible"] = True
            milk_run_candidates.append(entry)
        else:
            entry["recommendation"] = "Standard point-to-point delivery"
            entry["milk_run_eligible"] = False
            standard_delivery.append(entry)

    return {
        "milk_run_candidates": milk_run_candidates,
        "standard_delivery": standard_delivery,
        "note": "Milk run model applies to LAX/ORD destinations. Check MRTC tool for actual zip code coverage and achieved cost per kg.",
    }
