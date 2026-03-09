from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from typing import Dict, Any, Optional, List
import json
import os
import tempfile
from datetime import datetime

from app.models import ChatRequest, BidData, BidScoreInput, Lane
from app.services.ai_agent import chat, analyze_bid, suggest_rates
from app.services.scoring import calculate_bid_score, compute_lane_financials, SCORE_OPTIONS
from app.services.excel_export import export_to_v7, generate_customer_quote_html
from app.services.fx import convert_to_usd, convert, get_all_rates, get_supported_currencies
from app.services.volume import analyze_volume, analyze_seasonality, compute_weighted_average_rate, milk_run_assessment
from app.services.reference import is_focus_lane, get_lane_owners, FOCUS_LANES, OWNERSHIP
from app.services.ips_export import generate_ips_csv
from app.services.shipment_data import process_shipment_data, get_sample_csv_template
from app.services.rate_qa import validate_lane_rates, validate_all_lanes
from app.services.currency_map import get_lane_currencies, get_currency_for_country

router = APIRouter(prefix="/api")


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    reply = chat(messages, req.bid_data)
    return {"reply": reply}


@router.post("/score")
async def score_bid(inputs: Dict[str, str]):
    score, recommendation = calculate_bid_score(inputs)
    return {"score": score, "recommendation": recommendation}


@router.get("/score/options")
async def get_score_options():
    return SCORE_OPTIONS


@router.post("/lanes/financials")
async def lane_financials(lane: Dict[str, Any]):
    result = compute_lane_financials(lane)
    return result


@router.post("/lanes/suggest-rates")
async def suggest_lane_rates(payload: Dict[str, Any]):
    lane_data = payload.get("lane", {})
    market_context = payload.get("market_context", "")
    suggestion = suggest_rates(lane_data, market_context)
    return {"suggestion": suggestion}


@router.post("/analyze")
async def analyze(bid_data: Dict[str, Any]):
    analysis = analyze_bid(bid_data)
    return {"analysis": analysis}


@router.post("/export/excel")
async def export_excel(bid_data: Dict[str, Any]):
    client_name = bid_data.get("client_name", "Client").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Air_V7_{client_name}_{timestamp}.xlsx"
    output_path = os.path.join(tempfile.gettempdir(), filename)

    try:
        export_to_v7(bid_data, output_path)
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/quote-html")
async def export_quote_html(bid_data: Dict[str, Any]):
    html = generate_customer_quote_html(bid_data)
    return {"html": html}


@router.post("/density/chargeable-weight")
async def calc_chargeable_weight(payload: Dict[str, Any]):
    actual_kg = payload.get("actual_weight_kg", 0)
    volume_cbm = payload.get("volume_cbm", 0)
    ratio = payload.get("dim_ratio", 6)
    volumetric_kg = volume_cbm * (1000 / ratio)
    chargeable = max(actual_kg, volumetric_kg)
    return {
        "actual_weight_kg": actual_kg,
        "volumetric_weight_kg": round(volumetric_kg, 2),
        "chargeable_weight_kg": round(chargeable, 2),
        "dim_ratio": f"1:{ratio}",
        "basis": "actual" if actual_kg >= volumetric_kg else "volumetric",
    }


# ─── FX ──────────────────────────────────────────────────────────────────────
@router.get("/fx/rates")
async def fx_rates():
    return {"rates": get_all_rates(), "base": "USD", "currencies": get_supported_currencies()}


@router.post("/fx/convert")
async def fx_convert(payload: Dict[str, Any]):
    amount = payload.get("amount", 0)
    from_ccy = payload.get("from_currency", "USD")
    to_ccy = payload.get("to_currency", "USD")
    result = convert(amount, from_ccy, to_ccy)
    return {"amount": amount, "from": from_ccy, "to": to_ccy, "result": result}


# ─── Volume Analysis ──────────────────────────────────────────────────────────
@router.post("/volume/analyze")
async def volume_analyze(payload: Dict[str, Any]):
    lanes = payload.get("lanes", [])
    award_pct = payload.get("award_pct", 0.5)
    ftl_threshold = payload.get("ftl_threshold", 4000)
    return analyze_volume(lanes, award_pct, ftl_threshold)


@router.post("/volume/seasonality")
async def volume_seasonality(payload: Dict[str, Any]):
    lanes = payload.get("lanes", [])
    monthly_dist = payload.get("monthly_dist", None)
    return analyze_seasonality(lanes, monthly_dist)


@router.post("/volume/weighted-average")
async def weighted_average(payload: Dict[str, Any]):
    lanes = payload.get("lanes", [])
    return compute_weighted_average_rate(lanes)


@router.post("/volume/milk-run")
async def milk_run(payload: Dict[str, Any]):
    lanes = payload.get("lanes", [])
    return milk_run_assessment(lanes)


# ─── Reference Data ───────────────────────────────────────────────────────────
@router.get("/reference/focus-lanes")
async def focus_lanes_list():
    return {"focus_lanes": FOCUS_LANES, "total": len(FOCUS_LANES)}


@router.get("/reference/focus-lane/{origin}/{dest}")
async def check_focus_lane(origin: str, dest: str):
    result = is_focus_lane(origin, dest)
    return {"is_focus_lane": result is not None, "lane": result}


@router.get("/reference/ownership/{country_code}")
async def lane_ownership(country_code: str):
    from app.services.reference import get_ownership
    result = get_ownership(country_code)
    if not result:
        raise HTTPException(status_code=404, detail=f"Country code {country_code} not found")
    return result


@router.post("/reference/lane-owners")
async def lane_owners(payload: Dict[str, Any]):
    origin = payload.get("origin_country", "")
    dest = payload.get("destination_country", "")
    return get_lane_owners(origin, dest)


# ─── Shipment Data Upload ─────────────────────────────────────────────────────
@router.post("/shipment/upload")
async def shipment_upload(payload: Dict[str, Any]):
    """Process uploaded CSV shipment data and generate all 4 analytics."""
    csv_text = payload.get("csv_text", "")
    award_pct = payload.get("award_pct", 0.5)
    weeks = payload.get("weeks", 52)
    ftl_threshold = payload.get("ftl_threshold", 4000)
    if not csv_text:
        raise HTTPException(status_code=400, detail="csv_text is required")
    result = process_shipment_data(csv_text, award_pct, weeks, ftl_threshold)
    return result


@router.get("/shipment/template")
async def shipment_template():
    """Return a sample CSV template with headers and example rows."""
    template = get_sample_csv_template()
    return Response(
        content=template,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=shipment_data_template.csv"},
    )


# ─── Rate QA ──────────────────────────────────────────────────────────────────
@router.post("/lanes/qa")
async def lane_qa(lane: Dict[str, Any]):
    """Validate a single lane's rates and return violations."""
    return validate_lane_rates(lane)


@router.post("/lanes/qa/all")
async def lanes_qa_all(payload: Dict[str, Any]):
    """Validate all lanes and return summary with per-lane violations."""
    lanes = payload.get("lanes", [])
    return validate_all_lanes(lanes)


# ─── Currency Auto-populate ───────────────────────────────────────────────────
@router.post("/currency/suggest")
async def currency_suggest(payload: Dict[str, Any]):
    """Suggest origin, main, and destination currencies for a lane."""
    origin = payload.get("origin_country", "")
    dest = payload.get("destination_country", "")
    return get_lane_currencies(origin, dest)


@router.get("/currency/for-country/{country_code}")
async def currency_for_country(country_code: str):
    """Get the primary currency for a country code."""
    ccy = get_currency_for_country(country_code)
    if not ccy:
        raise HTTPException(status_code=404, detail=f"No currency mapping for {country_code}")
    return {"country_code": country_code.upper(), "currency": ccy}


# ─── IPS Export ───────────────────────────────────────────────────────────────
@router.post("/export/ips-csv")
async def export_ips(bid_data: Dict[str, Any]):
    csv_content = generate_ips_csv(bid_data)
    client_name = bid_data.get("client_name", "Client").replace(" ", "_")
    filename = f"IPS_Upload_{client_name}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
