from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(
    title="FinTrace Decision Robustness API",
    description="REST backend supporting claim extraction, evidence provenance verification, and calibration lab scoring.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str

class ClaimAnalyzeRequest(BaseModel):
    statement: str
    sourceUrl: Optional[str] = None
    ticker: Optional[str] = None
    horizon: Optional[str] = "2 months"

class CalibrationRequest(BaseModel):
    initialStance: str
    initialConfidence: int
    revisedStance: str
    revisedConfidence: int
    refutedAssumptions: dict

# Canonical Seed Store
SYNTHETIC_CLAIMS = [
    {
        "id": "claim_mgs_01",
        "ticker": "MGS",
        "company": "Meridian Grid Systems",
        "statement": "MGS will rise 30% in two months on strong grid backlog.",
        "date": "18 Nov 2026",
        "validationStatus": "Needs Verification",
        "direction": "Bullish",
        "evidenceCoverage": 64,
        "sourceUrl": "https://twitter.com/energy_analyst_pro/status/17258390",
        "horizon": "2 months",
        "targetPrice": "$192.50",
        "currentPrice": "$148.20",
        "breakdown": {
            "statedTarget": "30% price appreciation",
            "impliedHorizon": "60 days (January 2027)",
            "primaryCatalyst": "Contracted substation delivery pipeline",
            "missingConditions": [
                "High-voltage transformer delivery lead times",
                "Raw copper cost index fluctuations",
                "Interconnection queue FERC approval timelines"
            ]
        },
        "completeness": {
            "score": 58,
            "provenanceStatus": "USER-PROVIDED + PARTIALLY VERIFIED",
            "identifiedAssumptions": 4,
            "testedAssumptions": 1
        },
        "interpretations": [
            {
                "fork": "A: Optimistic Grid Expansion",
                "stance": "Bullish",
                "rationale": "Backlog conversion matches historical FY25 run-rate with gross margin expansion.",
                "source": "AI-GENERATED FORK"
            },
            {
                "fork": "B: Supply Chain Chokepoint",
                "stance": "Neutral / Cautious",
                "rationale": "Transformer vendor lead times now exceed 72 weeks; revenue recognition deferred.",
                "source": "AI-GENERATED FORK"
            },
            {
                "fork": "C: Regulatory Cap Risk",
                "stance": "Bearish Risk",
                "rationale": "State utility commission rate-case filings pending public hearing resistance.",
                "source": "AI-GENERATED FORK"
            }
        ],
        "supportingEvidence": [
            {
                "id": "ev_01",
                "title": "MGS Q3 Form 10-Q Contracted Backlog Schedule",
                "source": "SEC EDGAR",
                "date": "02 Nov 2026",
                "provenance": "REAL",
                "excerpt": "Reported firm backlog reached $2.4B, with 68% slated for delivery across fiscal 2027.",
                "url": "https://www.sec.gov/edgar/mgs/q3-2026"
            },
            {
                "id": "ev_02",
                "title": "Transformer Input Cost & Lead-Time Briefing",
                "source": "DOE Grid Deployment Office",
                "date": "15 Oct 2026",
                "provenance": "REAL",
                "excerpt": "Large power transformer procurement lead times currently average 84-110 weeks across North America.",
                "url": "https://energy.gov/gdo/reports/2026-lpt"
            }
        ]
    },
    {
        "id": "claim_apxr_02",
        "ticker": "APXR",
        "company": "Apex Renewables",
        "statement": "Apex Renewables capacity will double post-tax credit announcement.",
        "date": "18 Nov 2026",
        "validationStatus": "Needs Verification",
        "direction": "Bullish",
        "evidenceCoverage": 71,
        "sourceUrl": "https://linkedin.com/posts/cleanpower-brief",
        "horizon": "6 months",
        "targetPrice": "$42.00",
        "currentPrice": "$28.40",
        "breakdown": {
            "statedTarget": "100% capacity expansion",
            "impliedHorizon": "180 days",
            "primaryCatalyst": "Section 45X advanced manufacturing production credit",
            "missingConditions": ["Local permitting approval rate", "Grid tie-in transmission capacity"]
        },
        "completeness": {"score": 62, "provenanceStatus": "SYNTHETIC", "identifiedAssumptions": 3, "testedAssumptions": 1},
        "interpretations": [
            {"fork": "Tax Credit Flow-through", "stance": "Bullish", "rationale": "Direct monetization accelerates Phase 2 fab.", "source": "AI-GENERATED FORK"}
        ],
        "supportingEvidence": []
    }
]

SYNTHETIC_EVIDENCE = [
    {
        "id": "ev-sec-mgs-10q",
        "title": "MGS Q3 Form 10-Q Contracted Backlog Schedule",
        "source": "SEC EDGAR · Meridian Grid Systems",
        "ticker": "MGS",
        "date": "02 Nov 2026",
        "category": "SEC Filings",
        "provenance": "REAL",
        "confidenceScore": 96,
        "summary": "Firm contracted backlog stands at $2.42B, of which $1.64B is slated for recognition across FY 2027.",
        "fullText": "Meridian Grid Systems Inc. filed Form 10-Q for the quarterly period ended September 30, 2026. Note 4: Performance Obligations..."
    },
    {
        "id": "ev-doe-trans-cost",
        "title": "Transformer Input Cost & Lead-Time Briefing",
        "source": "DOE Grid Deployment Office",
        "ticker": "SECTOR-WIDE",
        "date": "15 Oct 2026",
        "category": "Industry Reports",
        "provenance": "REAL",
        "confidenceScore": 92,
        "summary": "High-voltage transformer lead times remain extended at 84–110 weeks, creating potential project deployment lags.",
        "fullText": "The Department of Energy Grid Deployment Office published its Q3 2026 Heavy Electrical Equipment Assessment..."
    }
]

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "FinTrace Robustness Engine"}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    return {
        "success": True,
        "token": "tok_demo_active_session",
        "user": {
            "name": "Nakul Verma",
            "email": req.email,
            "role": "Retail Investor & Decision Analyst"
        }
    }

@app.get("/api/claims")
def get_claims():
    return SYNTHETIC_CLAIMS

@app.get("/api/claims/{claim_id}")
def get_claim(claim_id: str):
    for c in SYNTHETIC_CLAIMS:
        if c["id"] == claim_id:
            return c
    return SYNTHETIC_CLAIMS[0]

@app.post("/api/claims/analyze")
def analyze_claim(req: ClaimAnalyzeRequest):
    new_claim = {
        "id": f"claim_{len(SYNTHETIC_CLAIMS) + 1}",
        "ticker": (req.ticker or "SYN").upper(),
        "company": f"Analyzed Entity ({req.ticker or 'SYN'})",
        "statement": req.statement,
        "date": "Today",
        "validationStatus": "Needs Verification",
        "direction": "Bullish",
        "evidenceCoverage": 65,
        "sourceUrl": req.sourceUrl or "",
        "horizon": req.horizon or "2 months",
        "breakdown": {
            "statedTarget": "Extracted milestone",
            "impliedHorizon": req.horizon or "60 days",
            "primaryCatalyst": "Extracted catalyst",
            "missingConditions": ["Supply chain delivery timelines", "Regulatory approvals"]
        },
        "completeness": {"score": 60, "provenanceStatus": "AI-GENERATED", "identifiedAssumptions": 3, "testedAssumptions": 1},
        "interpretations": [
            {"fork": "A: Optimistic Expansion", "stance": "Bullish", "rationale": "Direct growth assumption.", "source": "AI-GENERATED FORK"},
            {"fork": "B: Input Bottleneck", "stance": "Cautious", "rationale": "Supplier constraints.", "source": "AI-GENERATED FORK"}
        ],
        "supportingEvidence": SYNTHETIC_EVIDENCE[:1]
    }
    SYNTHETIC_CLAIMS.append(new_claim)
    return new_claim

@app.get("/api/evidence")
def get_evidence(q: Optional[str] = None):
    if not q:
        return SYNTHETIC_EVIDENCE
    return [e for e in SYNTHETIC_EVIDENCE if q.lower() in e["title"].lower() or q.lower() in e["ticker"].lower()]

@app.post("/api/decision-lab/calibrate")
def calibrate(req: CalibrationRequest):
    return {
        "success": True,
        "calibrationScore": 82,
        "delta": 26,
        "insights": "Demonstrated reduced overconfidence by flagging 84-week supply bottlenecks."
    }
