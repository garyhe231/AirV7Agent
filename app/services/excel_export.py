import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from typing import Dict, Any, List
from datetime import datetime
import shutil
import os

TEMPLATE_PATH = "/Users/jhe/Downloads/[Client]_ Air Template_v7.xlsx"


def export_to_v7(bid_data: Dict[str, Any], output_path: str) -> str:
    """Copy the V7 template and populate it with bid data."""
    shutil.copy2(TEMPLATE_PATH, output_path)
    wb = openpyxl.load_workbook(output_path)

    _fill_internal_pricing(wb, bid_data)
    _fill_kickoff(wb, bid_data)

    wb.save(output_path)
    return output_path


def _fill_internal_pricing(wb, bid_data: Dict[str, Any]):
    ws = wb["Internal Pricing"]
    lanes = bid_data.get("lanes", [])

    # Data starts at row 7 (rows 1-6 are headers/legend)
    for i, lane in enumerate(lanes):
        row = 7 + i
        col_map = {
            1: i + 1,                                          # Lane ID
            2: lane.get("pricing_request_id", ""),            # Pricing Request ID
            9: lane.get("client_name", bid_data.get("client_name", "")),  # Client
            10: lane.get("effective_date", ""),               # Effective Date
            11: lane.get("expiration_date", ""),              # Expiration Date
            12: lane.get("incoterms", ""),                    # Incoterms
            18: lane.get("origin_country", ""),               # Origin Country
            20: lane.get("origin_city", ""),                  # Origin City
            23: lane.get("origin_airport", ""),               # Origin Airport
            25: lane.get("destination_country", ""),          # Dest Country
            27: lane.get("destination_city", ""),             # Dest City
            30: lane.get("destination_airport", ""),          # Dest Airport
            32: lane.get("total_shipments", ""),              # Total Shipments
            36: lane.get("chargeable_weight_kg", ""),         # Chargeable Weight
            38: lane.get("avg_shipment_kg", ""),              # Avg Shipment
            49: lane.get("service_tier", ""),                 # Service Tier
            51: lane.get("origin_currency", "USD"),           # Origin Currency
            52: lane.get("pickup_min", ""),                   # Pickup Min
            55: lane.get("pickup_kg_1000", ""),               # Pickup 1000kg
            60: lane.get("origin_thc", ""),                   # Origin THC
            61: lane.get("screening", ""),                    # Screening
            62: lane.get("doc_fee", ""),                      # Doc Fee
            63: lane.get("export_customs", ""),               # Export Customs
            65: lane.get("main_currency", "USD"),             # Main Currency
            73: lane.get("buy_rate_per_kg", ""),              # Buy 1000kg
            75: lane.get("fuel_surcharge", ""),               # FSC
            76: lane.get("security_charge", ""),              # SSC
            77: lane.get("ams_ens", ""),                      # AMS/ENS
            79: lane.get("pss", ""),                          # PSS
            82: lane.get("airline", ""),                      # Airline
            83: lane.get("routing", ""),                      # Routing
            86: lane.get("transit_min", ""),                  # Transit Min
            87: lane.get("transit_max", ""),                  # Transit Max
            88: lane.get("dest_currency", "USD"),             # Dest Currency
            89: lane.get("delivery_min", ""),                 # Delivery Min
            92: lane.get("delivery_kg_1000", ""),             # Delivery 1000kg
            97: lane.get("dest_thc", ""),                     # Dest THC
            98: lane.get("import_service", ""),               # Import Service
            99: lane.get("import_customs", ""),               # Import Customs
            100: lane.get("doc_turnover", ""),                # Doc Turnover
            118: lane.get("sell_rate_per_kg", ""),            # Sell 1000kg
        }
        for col, value in col_map.items():
            if value != "":
                ws.cell(row=row, column=col).value = value


def _fill_kickoff(wb, bid_data: Dict[str, Any]):
    if "kickoff" not in bid_data or not bid_data["kickoff"]:
        return
    ws = wb["Kick Off Questions"]
    kickoff = bid_data["kickoff"]

    # Answer column is B (col 2); questions start at row 3
    answer_map = {
        3: kickoff.get("client_due_date"),
        4: kickoff.get("internal_due_date"),
        5: kickoff.get("commercial_context"),
        6: kickoff.get("opportunity_strategy"),
        7: kickoff.get("expected_rounds"),
        8: kickoff.get("num_providers"),
        9: kickoff.get("client_transit_times"),
        11: kickoff.get("financial_penalties"),
        12: kickoff.get("fuel_policy"),
        13: kickoff.get("cargo_density"),
        14: kickoff.get("accepts_pss"),
        15: kickoff.get("routing_requirements"),
        16: kickoff.get("special_delivery"),
        17: kickoff.get("pricing_instructions"),
        19: kickoff.get("award_methodology"),
        20: kickoff.get("pricing_assessment_logic"),
        21: kickoff.get("what_makes_us_win"),
        22: kickoff.get("other_notes"),
    }
    for row, value in answer_map.items():
        if value:
            ws.cell(row=row, column=2).value = value


def generate_customer_quote_html(bid_data: Dict[str, Any]) -> str:
    """Generate a simple HTML customer-facing quote."""
    client_name = bid_data.get("client_name", "Client")
    lanes = bid_data.get("lanes", [])
    rows = ""
    for lane in lanes:
        origin = f"{lane.get('origin_city', '')} ({lane.get('origin_airport', '')})"
        dest = f"{lane.get('destination_city', '')} ({lane.get('destination_airport', '')})"
        sell = lane.get("sell_rate_per_kg", "-")
        fsc = lane.get("fuel_surcharge", "-")
        ssc = lane.get("security_charge", "-")
        ams = lane.get("ams_ens", "-")
        transit = f"{lane.get('transit_min', '?')}-{lane.get('transit_max', '?')} days"
        effective = lane.get("effective_date", "-")
        expiration = lane.get("expiration_date", "-")
        tier = lane.get("service_tier", "-")
        rows += f"""
        <tr>
            <td>{lane.get('lane_id')}</td>
            <td>{origin}</td>
            <td>{dest}</td>
            <td>{tier}</td>
            <td>{sell}</td>
            <td>{fsc}</td>
            <td>{ssc}</td>
            <td>{ams}</td>
            <td>{transit}</td>
            <td>{effective}</td>
            <td>{expiration}</td>
        </tr>"""

    return f"""
    <div class="quote-export">
        <h2>Airfreight Quote — {client_name}</h2>
        <p class="quote-meta">Generated: {datetime.now().strftime('%Y-%m-%d')} | Currency: USD</p>
        <table class="quote-table">
            <thead>
                <tr>
                    <th>#</th><th>Origin</th><th>Destination</th><th>Service</th>
                    <th>Rate/kg</th><th>FSC</th><th>SSC</th><th>AMS/ENS</th>
                    <th>Transit</th><th>Valid From</th><th>Valid To</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <div class="terms">
            <p>* All rates are based on USD. Flexport reserves the right to apply a Currency Adjustment Factor (CAF).</p>
            <p>* Offer is valid for acceptance maximum 7 days after submission date.</p>
            <p>* Chargeable weight based on actual vs volumetric (1:6 ratio), whichever is greater.</p>
        </div>
    </div>
    """
