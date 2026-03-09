import json
import boto3
from typing import List, Dict, Any, Optional

BEDROCK_MODEL = "arn:aws:bedrock:us-east-1:013986332596:application-inference-profile/gdsg22td462g"
REGION = "us-east-1"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def _invoke(system: str, messages: List[Dict[str, str]], max_tokens: int = 2048) -> str:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]

SYSTEM_PROMPT = """You are the Air V7 Agent — an expert air freight RFP pricing assistant for Flexport.

Your job is to guide commercial teams through the complete Air V7 RFP process:
1. **Kickoff Questions** — capture commercial context, strategy, client requirements
2. **Bid Scoring** — assess opportunity quality and win probability
3. **Lane Pricing** — help structure origin charges, main freight, destination charges, surcharges
4. **Financial Analysis** — compute net revenue, take rate, cost vs sell per kg
5. **Customer Quote** — summarize the final customer-facing rate summary

You understand the full Air V7 sheet structure:
- Lane data: origin/destination airports, service tier (STD/EXP), chargeable weight, avg shipment size
- Origin charges: pickup, THC, screening, doc fee, export customs
- Main freight: buy rate per kg (by weight break), fuel surcharge (FSC), security (SSC), AMS/ENS, PSS
- Destination charges: delivery, THC, import service, import customs, doc turnover
- Markups: airport-to-airport markup, pickup markup, delivery markup
- Totals: cost per kg, sell per kg, net revenue per shipment, take rate

Key pricing concepts you know well:
- Chargeable weight = MAX(actual weight, volumetric weight). Volumetric = CBM × 166.67 (1:6 ratio)
- Weight breaks: Min, 45kg, 100kg, 300kg, 500kg, 1000kg, 2000kg
- FSC (fuel surcharge) and SSC (security surcharge) are typically pass-through
- PSS (Peak Season Surcharge) applies seasonally, usually Sep-Dec
- Take rate = (Sell - Cost) / Sell × 100%
- ENR (Expected Net Revenue) = NR per shipment × expected shipments

When analyzing bids, always consider:
- Lane density (heavier = better rates from airlines)
- Consolidation potential (weekly volume vs FTL threshold ~4000kg)
- Transit time competitiveness
- Currency exposure (origin/dest currency vs USD)
- Award assumption (typically 50% in first analysis)

Be concise, practical, and numbers-focused. When the user provides lane or volume data, extract it and compute financials. Always surface the most important commercial insight first.

IMPORTANT: Always complete your full response. Never cut off mid-sentence, mid-table, or mid-section. If a response would be very long, summarize sections rather than leaving them incomplete.

Current bid data will be provided in context when available.
"""


def build_context_block(bid_data: Optional[Dict[str, Any]]) -> str:
    if not bid_data:
        return ""
    lines = ["## Current Bid Context\n"]
    if bid_data.get("client_name"):
        lines.append(f"**Client:** {bid_data['client_name']}")
    if bid_data.get("pricing_request_id"):
        lines.append(f"**Pricing Request ID:** {bid_data['pricing_request_id']}")
    if bid_data.get("bid_score"):
        lines.append(f"**Bid Score:** {bid_data['bid_score'].get('score')} — {bid_data['bid_score'].get('recommendation')}")
    if bid_data.get("lanes"):
        lines.append(f"**Lanes entered:** {len(bid_data['lanes'])}")
        for lane in bid_data["lanes"]:
            origin = lane.get("origin_airport") or lane.get("origin_city") or "?"
            dest = lane.get("destination_airport") or lane.get("destination_city") or "?"
            cw = lane.get("chargeable_weight_kg")
            sell = lane.get("sell_rate_per_kg")
            lines.append(f"  - Lane {lane.get('lane_id')}: {origin} → {dest} | CW: {cw}kg | Sell: {sell} USD/kg")
    if bid_data.get("financials"):
        fin = bid_data["financials"]
        lines.append(f"**Total Net Revenue:** ${fin.get('total_net_revenue'):,.0f}" if fin.get("total_net_revenue") else "")
        lines.append(f"**Avg Take Rate:** {fin.get('avg_take_rate')}%" if fin.get("avg_take_rate") else "")
    return "\n".join(lines)


def chat(messages: List[Dict[str, str]], bid_data: Optional[Dict[str, Any]] = None) -> str:
    context = build_context_block(bid_data)
    system = SYSTEM_PROMPT
    if context:
        system += f"\n\n{context}"

    return _invoke(system, messages, max_tokens=8096)


def analyze_bid(bid_data: Dict[str, Any]) -> str:
    """Generate a full bid analysis summary."""
    prompt = f"""Please provide a comprehensive bid analysis summary for this opportunity:

{json.dumps(bid_data, indent=2, default=str)}

Structure your response as:
1. **Opportunity Overview** — client, scope, key commercial context
2. **Bid Score Assessment** — win probability and key factors
3. **Lane Analysis** — coverage, density, consolidation potential
4. **Financial Summary** — total net revenue, take rates, any red flags
5. **Recommended Pricing Strategy** — how aggressive to be, key levers
6. **Open Questions / Risks** — what's missing or concerning
"""
    return _invoke(SYSTEM_PROMPT, [{"role": "user", "content": prompt}], max_tokens=8096)


def suggest_rates(lane_data: Dict[str, Any], market_context: str = "") -> str:
    """Ask AI to suggest competitive rates for a lane."""
    prompt = f"""Based on this lane data, suggest competitive buy and sell rates:

Lane: {json.dumps(lane_data, indent=2, default=str)}

Market context: {market_context or 'Standard market conditions'}

Provide:
1. Suggested buy rate per kg (airport-to-airport, +1000kg)
2. Suggested sell rate per kg
3. Recommended markup %
4. Any surcharge considerations
5. Transit time expectation

Be specific with numbers and explain your reasoning briefly.
"""
    return _invoke(SYSTEM_PROMPT, [{"role": "user", "content": prompt}], max_tokens=4096)
