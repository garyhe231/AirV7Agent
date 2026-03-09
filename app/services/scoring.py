from typing import Dict, Tuple

# Scoring options and weights matching the Bid Score Tool sheet
SCORE_OPTIONS = {
    "customer_segment": {
        "weight": 0.05,
        "options": {
            "Enterprise": 100,
            "Mid-Market": 80,
            "SMB": 60,
            "Unknown": 40,
        }
    },
    "company_size": {
        "weight": 0.05,
        "options": {
            ">$100M annual revenue": 100,
            "$10M - $100M annual revenue": 90,
            "$5M - $10M annual revenue": 80,
            "$1M - $5M annual revenue": 60,
            "<$1M annual revenue": 40,
        }
    },
    "industry": {
        "weight": 0.05,
        "options": {
            "Technology / Electronics": 100,
            "Retail / E-commerce": 100,
            "Automotive": 90,
            "Health & Personal Care": 80,
            "Industrial / Manufacturing": 70,
            "Other": 50,
        }
    },
    "commodity": {
        "weight": 0.05,
        "options": {
            "General cargo, fully serviceable": 100,
            "Some restrictions but mostly serviceable": 60,
            "70% of the business is not serviceable: cold chain, pharma, parcel, NFO etc.": 20,
        }
    },
    "value_proposition": {
        "weight": 0.05,
        "options": {
            "Strong existing relationship, client pulled us in": 100,
            "Client has shown clear interest in Flexport value prop": 70,
            "We submitted rates and got generic rate feedback": 20,
            "No prior engagement": 0,
        }
    },
    "willingness_trials": {
        "weight": 0.05,
        "options": {
            "Client committed to running trials before RFP": 100,
            "The customer will give us a few trail shipments on a common lane of interest prior to going into a formal RFP": 70,
            "Client open to trials after award": 40,
            "Not willing to run trials": 0,
        }
    },
    "stakeholder_relationship": {
        "weight": 0.05,
        "options": {
            "C-level relationship established": 100,
            "Mid-level relationship established": 60,
            "Working-level only": 30,
            "No prior collaboration": 0,
        }
    },
    "customer_persona": {
        "weight": 0.05,
        "options": {
            "Customer prioritizes service quality and is willing to pay a premium": 100,
            "Customer is somewhat price sensitive but willing to balance cost with service differentiation and value-added solutions": 50,
            "Customer is highly price sensitive, price is the primary driver": 20,
        }
    },
    "customer_status": {
        "weight": 0.05,
        "options": {
            "Existing customer, strong relationship": 100,
            "Existing customer, standard relationship": 80,
            "Net new": 60,
            "Lost previously": 30,
        }
    },
    "air_volume": {
        "weight": 0.10,
        "options": {
            ">2M kg yearly": 100,
            "10K - 2M kg yearly": 100,
            "1K - 10K kg yearly": 60,
            "<1K kg yearly": 20,
        }
    },
    "lane_serviceability": {
        "weight": 0.10,
        "options": {
            "More than 80% on Core lanes or focus/growth lanes": 100,
            "More than 30% on Core lanes or focus/growth lanes": 50,
            "Less than 30% on core lanes": 20,
        }
    },
    "volume_details": {
        "weight": 0.10,
        "options": {
            "Customer Provides shipment level historical data and volume forecasts": 100,
            "Customer provides lane level data only": 60,
            "No volume data provided": 20,
        }
    },
    "msa_penalty": {
        "weight": 0.05,
        "options": {
            "Willing to work without MSA": 100,
            "Standard MSA required": 70,
            "Strict penalties / non-standard MSA": 20,
        }
    },
    "accept_pss": {
        "weight": 0.10,
        "options": {
            "Yes": 100,
            "Yes, with conditions": 70,
            "No": 0,
        }
    },
    "rate_type": {
        "weight": 0.05,
        "options": {
            "All in rate": 50,
            "Net-net rate": 80,
            "Weight break rates": 100,
        }
    },
    "special_requirements": {
        "weight": 0.05,
        "options": {
            "No": 100,
            "Minor requirements": 70,
            "Major special requirements (cold chain, pharma, FBA, etc.)": 20,
        }
    },
}


def calculate_bid_score(inputs: Dict[str, str]) -> Tuple[float, str]:
    total_weight = 0.0
    weighted_score = 0.0

    for field, config in SCORE_OPTIONS.items():
        value = inputs.get(field)
        if value and value in config["options"]:
            score = config["options"][value]
            weighted_score += score * config["weight"]
            total_weight += config["weight"]

    if total_weight == 0:
        return 0.0, "Insufficient data to score"

    # Normalize to answered questions
    final_score = weighted_score / total_weight

    if final_score >= 80:
        recommendation = "Ideal customer — high probability of win. Invest fully."
    elif final_score >= 60:
        recommendation = "Good probability to win. Form a solid winning strategy."
    elif final_score >= 45:
        recommendation = "Low probability to win. Deprioritize vs other opportunities."
    else:
        recommendation = "Very low probability to win. Not recommended to bid."

    return round(final_score, 1), recommendation


def get_rate_for_weight(lane: dict, weight_kg: float, rate_type: str = "buy") -> float:
    """Pick the applicable weight break rate for a given shipment weight."""
    prefix = "buy_rate" if rate_type == "buy" else "sell_rate"
    breaks = [
        (2000, lane.get(f"{prefix}_2000")),
        (1000, lane.get(f"{prefix}_per_kg") or lane.get(f"{prefix}_1000")),
        (500,  lane.get(f"{prefix}_500")),
        (300,  lane.get(f"{prefix}_300")),
        (100,  lane.get(f"{prefix}_100")),
        (45,   lane.get(f"{prefix}_45")),
        (0,    lane.get(f"{prefix}_min")),
    ]
    for threshold, rate in breaks:
        if rate is not None and weight_kg >= threshold:
            return float(rate)
    # fallback to +1000kg rate
    return float(lane.get(f"{prefix}_per_kg") or 0)


def compute_lane_financials(lane: dict) -> dict:
    """Compute cost, sell, net revenue for a lane using weight break rates."""
    chargeable_kg = lane.get("chargeable_weight_kg") or 0
    total_shipments = lane.get("total_shipments") or 1
    avg_shipment = chargeable_kg / total_shipments if total_shipments else 0

    # Use weight-break rate for the average shipment size
    buy_rate = get_rate_for_weight(lane, avg_shipment, "buy")
    sell_rate = get_rate_for_weight(lane, avg_shipment, "sell")

    fuel = lane.get("fuel_surcharge") or 0
    security = lane.get("security_charge") or 0
    ams = lane.get("ams_ens") or 0
    acas = lane.get("acas") or 0
    pss = lane.get("pss") or 0

    cost_per_kg = buy_rate + fuel + security + ams + acas
    sell_per_kg = sell_rate + fuel + security + ams + acas + pss

    # Markup layer
    air_markup = lane.get("air_base_markup") or 0
    sell_per_kg += air_markup

    # Origin charges per shipment (HAWB fees)
    origin_thc = (lane.get("origin_thc") or 0) * avg_shipment
    screening = (lane.get("screening") or 0) * avg_shipment
    doc_fee = lane.get("doc_fee") or 0
    export_customs = lane.get("export_customs") or 0
    origin_per_hawb = origin_thc + screening + doc_fee + export_customs

    # Dest charges per shipment
    dest_thc = (lane.get("dest_thc") or 0) * avg_shipment
    import_svc = lane.get("import_service") or 0
    import_customs = lane.get("import_customs") or 0
    doc_turnover = lane.get("doc_turnover") or 0
    dest_per_hawb = dest_thc + import_svc + import_customs + doc_turnover

    # Pickup / delivery (use weight-break rate or min)
    pickup_kg = lane.get("pickup_kg_1000") or 0
    delivery_kg = lane.get("delivery_kg_1000") or 0
    pickup_min = lane.get("pickup_min") or 0
    delivery_min = lane.get("delivery_min") or 0
    pickup_cost = max(pickup_min, pickup_kg * avg_shipment)
    delivery_cost = max(delivery_min, delivery_kg * avg_shipment)

    cost_per_shipment = (cost_per_kg * avg_shipment) + origin_per_hawb + dest_per_hawb + pickup_cost + delivery_cost
    sell_per_shipment = (sell_per_kg * avg_shipment) + origin_per_hawb + dest_per_hawb + pickup_cost + delivery_cost

    nr_per_shipment = sell_per_shipment - cost_per_shipment
    total_nr = nr_per_shipment * total_shipments
    take_rate = (nr_per_shipment / sell_per_shipment * 100) if sell_per_shipment else 0

    return {
        "cost_per_kg": round(cost_per_kg, 4),
        "sell_per_kg": round(sell_per_kg, 4),
        "nr_per_shipment": round(nr_per_shipment, 2),
        "total_net_revenue": round(total_nr, 2),
        "take_rate_pct": round(take_rate, 1),
        "avg_shipment_kg": round(avg_shipment, 1),
        "weight_break_used": f"+{1000 if avg_shipment >= 1000 else 500 if avg_shipment >= 500 else 300 if avg_shipment >= 300 else 100 if avg_shipment >= 100 else 45}kg",
    }
