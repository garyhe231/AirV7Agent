"""
Rate entry QA validation service.
Mirrors the V7 conditional formatting rules:
- Weight break rates must decrease as weight increases (higher weight = lower rate)
- FTL rate / 5000 should be <= +5000kg LTL rate
- Sell rates must be >= buy rates (no negative margin)
"""
from typing import Dict, Any, List

WEIGHT_BREAKS_BUY = ["buy_rate_min", "buy_rate_45", "buy_rate_100",
                      "buy_rate_300", "buy_rate_500", "buy_rate_per_kg", "buy_rate_2000"]
WEIGHT_BREAKS_SELL = ["sell_rate_min", "sell_rate_45", "sell_rate_100",
                       "sell_rate_300", "sell_rate_500", "sell_rate_per_kg", "sell_rate_2000"]
WEIGHT_BREAK_LABELS = ["Min", "+45kg", "+100kg", "+300kg", "+500kg", "+1000kg", "+2000kg"]

PICKUP_BREAKS = ["pickup_min", "pickup_kg_100", "pickup_kg_500", "pickup_kg_1000", "pickup_kg_2000"]
DELIVERY_BREAKS = ["delivery_min", "delivery_kg_100", "delivery_kg_500", "delivery_kg_1000", "delivery_kg_2000"]


def validate_lane_rates(lane: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all rate entries for a lane.
    Returns list of violations with field names, severity, and message.
    """
    violations = []

    def check_descending(fields: List[str], labels: List[str], prefix: str):
        """Higher weight breaks must have lower or equal rates."""
        rates = []
        for f in fields:
            v = lane.get(f)
            rates.append(float(v) if v is not None else None)

        for i in range(len(rates) - 1):
            a, b = rates[i], rates[i + 1]
            if a is not None and b is not None and b > a:
                violations.append({
                    "field": fields[i + 1],
                    "severity": "error",
                    "rule": "weight_break_ascending",
                    "message": f"{prefix} {labels[i+1]} rate (${b}) is higher than {labels[i]} rate (${a}). "
                               f"Higher weight breaks should have equal or lower rates.",
                })

    # Check buy rate weight breaks
    check_descending(WEIGHT_BREAKS_BUY, WEIGHT_BREAK_LABELS, "Buy")

    # Check sell rate weight breaks
    check_descending(WEIGHT_BREAKS_SELL, WEIGHT_BREAK_LABELS, "Sell")

    # Check pickup weight breaks (per-kg rates should decrease with weight)
    pickup_rates = [lane.get(f) for f in PICKUP_BREAKS[1:]]  # skip min (flat fee)
    pickup_labels = ["+100kg", "+500kg", "+1000kg", "+2000kg"]
    for i in range(len(pickup_rates) - 1):
        a, b = pickup_rates[i], pickup_rates[i + 1]
        if a is not None and b is not None and float(b) > float(a):
            violations.append({
                "field": PICKUP_BREAKS[i + 2],
                "severity": "warning",
                "rule": "pickup_break_ascending",
                "message": f"Pickup {pickup_labels[i+1]} rate (${b}) > {pickup_labels[i]} (${a}).",
            })

    # Check delivery weight breaks
    delivery_rates = [lane.get(f) for f in DELIVERY_BREAKS[1:]]
    delivery_labels = ["+100kg", "+500kg", "+1000kg", "+2000kg"]
    for i in range(len(delivery_rates) - 1):
        a, b = delivery_rates[i], delivery_rates[i + 1]
        if a is not None and b is not None and float(b) > float(a):
            violations.append({
                "field": DELIVERY_BREAKS[i + 2],
                "severity": "warning",
                "rule": "delivery_break_ascending",
                "message": f"Delivery {delivery_labels[i+1]} rate (${b}) > {delivery_labels[i]} (${a}).",
            })

    # Check sell >= buy for each weight break pair
    buy_sell_pairs = list(zip(WEIGHT_BREAKS_BUY, WEIGHT_BREAKS_SELL, WEIGHT_BREAK_LABELS))
    for buy_f, sell_f, label in buy_sell_pairs:
        buy_v = lane.get(buy_f)
        sell_v = lane.get(sell_f)
        if buy_v is not None and sell_v is not None:
            if float(sell_v) < float(buy_v):
                violations.append({
                    "field": sell_f,
                    "severity": "error",
                    "rule": "negative_margin",
                    "message": f"{label} sell rate (${sell_v}) is below buy rate (${buy_v}). Negative margin.",
                })

    # FTL vs +5000kg check (pickup)
    pickup_ftl = lane.get("pickup_ftl")
    pickup_5000 = lane.get("pickup_kg_5000")
    ftl_cap = lane.get("pickup_ftl_capacity") or 5000
    if pickup_ftl and pickup_5000:
        ftl_per_kg = float(pickup_ftl) / float(ftl_cap)
        if ftl_per_kg < float(pickup_5000):
            violations.append({
                "field": "pickup_kg_5000",
                "severity": "warning",
                "rule": "ftl_better_than_ltl",
                "message": f"FTL rate / capacity = ${ftl_per_kg:.3f}/kg which is cheaper than +5000kg LTL "
                           f"rate (${pickup_5000}/kg). Consider using FTL rate.",
            })

    # Same for delivery FTL
    delivery_ftl = lane.get("delivery_ftl")
    delivery_5000 = lane.get("delivery_kg_5000")
    del_cap = lane.get("delivery_ftl_capacity") or 5000
    if delivery_ftl and delivery_5000:
        ftl_per_kg = float(delivery_ftl) / float(del_cap)
        if ftl_per_kg < float(delivery_5000):
            violations.append({
                "field": "delivery_kg_5000",
                "severity": "warning",
                "rule": "ftl_better_than_ltl",
                "message": f"Delivery FTL / capacity = ${ftl_per_kg:.3f}/kg cheaper than +5000kg "
                           f"(${delivery_5000}/kg). Consider using FTL rate.",
            })

    # Missing mandatory fields check
    mandatory = ["origin_airport", "destination_airport", "service_tier",
                 "effective_date", "expiration_date"]
    for f in mandatory:
        if not lane.get(f):
            violations.append({
                "field": f,
                "severity": "warning",
                "rule": "missing_mandatory",
                "message": f"Mandatory field '{f}' is empty.",
            })

    errors = [v for v in violations if v["severity"] == "error"]
    warnings = [v for v in violations if v["severity"] == "warning"]

    return {
        "valid": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "violations": violations,
        "errors": errors,
        "warnings": warnings,
    }


def validate_all_lanes(lanes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate all lanes and return a summary."""
    results = []
    total_errors = 0
    total_warnings = 0

    for lane in lanes:
        result = validate_lane_rates(lane)
        result["lane_id"] = lane.get("lane_id")
        result["port_pair"] = f"{lane.get('origin_airport','?')} - {lane.get('destination_airport','?')}"
        results.append(result)
        total_errors += result["error_count"]
        total_warnings += result["warning_count"]

    return {
        "lanes": results,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "all_valid": total_errors == 0,
    }
