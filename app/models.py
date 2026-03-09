from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class KickoffAnswers(BaseModel):
    client_due_date: Optional[str] = None
    internal_due_date: Optional[str] = None
    commercial_context: Optional[str] = None
    opportunity_strategy: Optional[str] = None
    expected_rounds: Optional[str] = None
    num_providers: Optional[str] = None
    client_transit_times: Optional[str] = None
    financial_penalties: Optional[str] = None
    fuel_policy: Optional[str] = None
    cargo_density: Optional[str] = None
    accepts_pss: Optional[str] = None
    routing_requirements: Optional[str] = None
    special_delivery: Optional[str] = None
    pricing_instructions: Optional[str] = None
    award_methodology: Optional[str] = None
    pricing_assessment_logic: Optional[str] = None
    what_makes_us_win: Optional[str] = None
    other_notes: Optional[str] = None


class BidScoreInput(BaseModel):
    customer_segment: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    commodity: Optional[str] = None
    value_proposition: Optional[str] = None
    willingness_trials: Optional[str] = None
    stakeholder_relationship: Optional[str] = None
    customer_persona: Optional[str] = None
    customer_status: Optional[str] = None
    air_volume: Optional[str] = None
    lane_serviceability: Optional[str] = None
    volume_details: Optional[str] = None
    msa_penalty: Optional[str] = None
    accept_pss: Optional[str] = None
    rate_type: Optional[str] = None
    special_requirements: Optional[str] = None


class Lane(BaseModel):
    lane_id: int
    pricing_request_id: Optional[str] = None
    client_name: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    incoterms: Optional[str] = None
    service_tier: Optional[str] = None
    # Origin
    origin_country: Optional[str] = None
    origin_city: Optional[str] = None
    origin_airport: Optional[str] = None
    # Destination
    destination_country: Optional[str] = None
    destination_city: Optional[str] = None
    destination_airport: Optional[str] = None
    # Shipment info
    total_shipments: Optional[float] = None
    chargeable_weight_kg: Optional[float] = None
    avg_shipment_kg: Optional[float] = None
    # Pricing
    origin_currency: Optional[str] = "USD"
    pickup_min: Optional[float] = None
    pickup_kg_100: Optional[float] = None
    pickup_kg_500: Optional[float] = None
    pickup_kg_1000: Optional[float] = None
    pickup_kg_2000: Optional[float] = None
    origin_thc: Optional[float] = None
    screening: Optional[float] = None
    doc_fee: Optional[float] = None
    export_customs: Optional[float] = None
    main_currency: Optional[str] = "USD"
    buy_rate_basis: Optional[str] = "per kg"
    # Weight breaks (buy)
    buy_rate_min: Optional[float] = None
    buy_rate_45: Optional[float] = None
    buy_rate_100: Optional[float] = None
    buy_rate_300: Optional[float] = None
    buy_rate_500: Optional[float] = None
    buy_rate_per_kg: Optional[float] = None   # +1000kg
    buy_rate_2000: Optional[float] = None
    # Weight breaks (sell)
    sell_rate_min: Optional[float] = None
    sell_rate_45: Optional[float] = None
    sell_rate_100: Optional[float] = None
    sell_rate_300: Optional[float] = None
    sell_rate_500: Optional[float] = None
    sell_rate_per_kg: Optional[float] = None  # +1000kg
    sell_rate_2000: Optional[float] = None
    # Surcharges
    fuel_surcharge: Optional[float] = None
    security_charge: Optional[float] = None
    ams_ens: Optional[float] = None
    acas: Optional[float] = None
    pss: Optional[float] = None
    pss_effective: Optional[str] = None
    pss_expiration: Optional[str] = None
    # Markups
    air_base_markup: Optional[float] = None
    pickup_markup_kg: Optional[float] = None
    pickup_markup_flat: Optional[float] = None
    delivery_markup_kg: Optional[float] = None
    delivery_markup_flat: Optional[float] = None
    dest_currency: Optional[str] = "USD"
    delivery_min: Optional[float] = None
    delivery_kg_100: Optional[float] = None
    delivery_kg_500: Optional[float] = None
    delivery_kg_1000: Optional[float] = None
    delivery_kg_2000: Optional[float] = None
    dest_thc: Optional[float] = None
    import_service: Optional[float] = None
    import_customs: Optional[float] = None
    doc_turnover: Optional[float] = None
    # Transit times
    transit_min: Optional[int] = None
    transit_max: Optional[int] = None
    # Flight
    airline: Optional[str] = None
    routing: Optional[str] = None
    flights_per_week: Optional[int] = None
    days_of_uplift: Optional[str] = None
    # Extra
    packaging: Optional[str] = None
    stackable: Optional[str] = None
    dangerous_goods: Optional[str] = None
    customer_notes: Optional[str] = None
    tonnage_cap: Optional[float] = None
    cap_frequency: Optional[str] = None
    total_actual_weight_kg: Optional[float] = None
    total_volume_cbm: Optional[float] = None
    density_profile: Optional[str] = None
    round: Optional[str] = "1"


class BidData(BaseModel):
    client_name: str
    pricing_request_id: str
    kickoff: Optional[KickoffAnswers] = None
    bid_score: Optional[BidScoreInput] = None
    lanes: List[Lane] = []


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    bid_data: Optional[Dict[str, Any]] = None
