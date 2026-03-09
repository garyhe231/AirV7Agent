# Air V7 Agent

An AI-powered air freight RFP pricing agent that automates the complete Flexport Air V7 workflow — from kickoff questions through to customer-facing quotes and IPS upload.

Built with FastAPI + Claude (via AWS Bedrock) + vanilla JS.

![Python](https://img.shields.io/badge/python-3.9+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green) ![Claude](https://img.shields.io/badge/Claude-Opus%204.6-purple)

---

## Features

| Tab | What it does |
|---|---|
| **Chat** | AI assistant with full Air V7 context — ask about pricing, strategy, rates, surcharges |
| **Kickoff** | All standard kickoff questions + AI strategy advice |
| **Bid Score** | 16-criteria weighted bid scoring tool with win probability |
| **Lanes & Pricing** | Full lane entry with 7 weight breaks (buy + sell), all origin/main/dest charges |
| **Volume** | Weekly volume, consolidation, seasonality chart, weighted average rate, milk run assessment |
| **Analysis** | One-click full AI bid analysis — strategy, financials, risks, open questions |
| **Export** | Customer-facing HTML quote, Air V7 Excel (populated template), IPS CSV upload |
| **Tools** | Chargeable weight calculator, FX converter (14 currencies), focus lane lookup, ownership matrix |

---

## Setup

### Prerequisites
- Python 3.9+
- AWS credentials with Bedrock access (`aws sts get-caller-identity` should work)

### Install & run

```bash
git clone https://github.com/garyhe231/AirV7Agent.git
cd AirV7Agent

pip3 install -r requirements.txt

python3 run.py
```

Open **http://localhost:8003**

### AWS Bedrock (default)

The agent uses Claude Opus 4.6 via AWS Bedrock. Make sure your AWS credentials are configured:

```bash
aws configure   # or use SSO / IAM role
```

### Anthropic API key (alternative)

If you prefer to use the Anthropic API directly, create a `.env` file:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

Then update `app/services/ai_agent.py` to use `anthropic.Anthropic()` instead of boto3.

---

## Project Structure

```
AirV7Agent/
├── run.py                        # Entry point
├── requirements.txt
├── app/
│   ├── main.py                   # FastAPI app
│   ├── models.py                 # Pydantic models (Lane, BidData, etc.)
│   ├── routers/
│   │   └── api.py                # All API endpoints
│   ├── services/
│   │   ├── ai_agent.py           # Claude integration (chat, analyze, suggest rates)
│   │   ├── scoring.py            # Bid score + lane financials with weight breaks
│   │   ├── volume.py             # Volume analysis, seasonality, consolidation, milk run
│   │   ├── fx.py                 # FX conversion (14 currencies, finance-approved rates)
│   │   ├── reference.py          # Focus lanes (90), ownership matrix (86 countries)
│   │   ├── ips_export.py         # IPS CSV upload format (104 columns)
│   │   └── excel_export.py       # Air V7 Excel template population
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/
│       └── index.html
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | AI chat with bid context |
| POST | `/api/score` | Calculate bid score |
| GET | `/api/score/options` | Get all scoring criteria and options |
| POST | `/api/lanes/financials` | Compute lane P&L with weight breaks |
| POST | `/api/lanes/suggest-rates` | AI rate suggestion for a lane |
| POST | `/api/analyze` | Full AI bid analysis |
| POST | `/api/volume/analyze` | Weekly volume + consolidation assessment |
| POST | `/api/volume/seasonality` | Monthly volume distribution |
| POST | `/api/volume/weighted-average` | Volume-weighted blended sell rate |
| POST | `/api/volume/milk-run` | Milk run trucking assessment |
| GET | `/api/fx/rates` | Get all FX rates |
| POST | `/api/fx/convert` | Convert between currencies |
| GET | `/api/reference/focus-lanes` | List all 2026 focus lanes |
| GET | `/api/reference/focus-lane/{origin}/{dest}` | Check if a lane is a focus lane |
| POST | `/api/reference/lane-owners` | Get TLM/trucking owners by country |
| POST | `/api/density/chargeable-weight` | Calculate chargeable weight (1:6 ratio) |
| POST | `/api/export/quote-html` | Generate customer-facing HTML quote |
| POST | `/api/export/ips-csv` | Generate IPS upload CSV (104 columns) |
| POST | `/api/export/excel` | Populate and download Air V7 Excel template |

---

## Key Concepts

- **Chargeable weight** = MAX(actual weight, volumetric weight). Volumetric = CBM × 166.67 (1:6 ratio)
- **Weight breaks**: Min, +45kg, +100kg, +300kg, +500kg, +1000kg, +2000kg — agent auto-selects the right break for each shipment
- **Take rate** = (Sell − Cost) / Sell × 100%
- **Consolidation**: weekly awarded CW vs FTL threshold (~4,000 kg)
- **PSS**: Peak Season Surcharge, typically Sep–Dec
- **AMS**: US-inbound only | **ENS**: EU-inbound only

---

## Test Results

```
33/33 tests passing
```

Run the test suite:

```bash
python3 /tmp/test_airv7.py   # requires the server to be running
```
