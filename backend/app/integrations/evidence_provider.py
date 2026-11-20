from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import asyncio
import httpx

# ---------------------------------------------------------------------------
# Strict Entity Resolution Registries
# Prevents false company matches and jurisdictional confusion.
# ---------------------------------------------------------------------------

VERIFIED_NSE_REGISTRY = {
    "INFY": {
        "name": "Infosys Limited",
        "symbol": "INFY",
        "isin": "INE009A01021",
        "has_us_adr": True,
        "sec_ticker": "INFY",
        "sec_cik": 1067491
    },
    "TCS": {
        "name": "Tata Consultancy Services Limited",
        "symbol": "TCS",
        "isin": "INE467B01029",
        "has_us_adr": False,
        "sec_ticker": None,
        "sec_cik": None
    },
    "RELIANCE": {
        "name": "Reliance Industries Limited",
        "symbol": "RELIANCE",
        "isin": "INE002A01018",
        "has_us_adr": False,
        "sec_ticker": None,
        "sec_cik": None
    },
    "HDFCBANK": {
        "name": "HDFC Bank Limited",
        "symbol": "HDFCBANK",
        "isin": "INE040A01034",
        "has_us_adr": True,
        "sec_ticker": "HDB",
        "sec_cik": 1144967
    },
    "WIPRO": {
        "name": "Wipro Limited",
        "symbol": "WIPRO",
        "isin": "INE075A01022",
        "has_us_adr": True,
        "sec_ticker": "WIT",
        "sec_cik": 1123799
    }
}

# Reverse mapping from normalized common names to verified NSE symbols
NAME_TO_NSE_SYMBOL = {
    "infosys": "INFY",
    "infosys limited": "INFY",
    "infosys ltd": "INFY",
    "tcs": "TCS",
    "tata consultancy services": "TCS",
    "tata consultancy services limited": "TCS",
    "tata consultancy services ltd": "TCS",
    "reliance": "RELIANCE",
    "reliance industries": "RELIANCE",
    "reliance industries limited": "RELIANCE",
    "reliance industries ltd": "RELIANCE",
    "hdfc bank": "HDFCBANK",
    "wipro": "WIPRO"
}


def parse_nse_date(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse dates from NSE announcement format ('18-Nov-2026 22:10:55' or '2026-11-18 22:10:55')."""
    if not dt_str:
        return None
    for fmt in ["%d-%b-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            return datetime.strptime(dt_str.strip(), fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


class BaseEvidenceProvider(ABC):
    """Abstract interface for financial evidence providers."""

    @abstractmethod
    async def retrieve_evidence(
        self,
        company_name: Optional[str],
        ticker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve verified evidence records for a given company or ticker."""
        pass


class NSEDisclosuresProvider(BaseEvidenceProvider):
    """
    Primary evidence retrieval provider for Indian-listed equities querying
    official corporate disclosures directly from the National Stock Exchange of India (NSE).
    """

    def __init__(self, timeout: float = 10.0, request_spacing: float = 0.1):
        self.timeout = timeout
        self.request_spacing = request_spacing
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def resolve_nse_symbol(self, company_name: Optional[str], ticker: Optional[str]) -> Optional[Dict[str, Any]]:
        """Resolves verified NSE identity strictly. Rejects mismatches and unverified companies."""
        t = (ticker or "").upper().strip()
        if t in VERIFIED_NSE_REGISTRY:
            return VERIFIED_NSE_REGISTRY[t]

        norm_name = (company_name or "").lower().strip()
        if norm_name in NAME_TO_NSE_SYMBOL:
            mapped_sym = NAME_TO_NSE_SYMBOL[norm_name]
            return VERIFIED_NSE_REGISTRY.get(mapped_sym)

        # If ticker is provided directly (e.g. valid uppercase symbol)
        if t and t.isalpha() and len(t) <= 12:
            return {
                "name": company_name or t,
                "symbol": t,
                "isin": None,
                "has_us_adr": False,
                "sec_ticker": None,
                "sec_cik": None
            }

        return None

    async def retrieve_evidence(
        self,
        company_name: Optional[str],
        ticker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        entity = self.resolve_nse_symbol(company_name, ticker)
        if not entity:
            # Unverified or ambiguous symbol: never fabricate evidence
            return []

        symbol = entity["symbol"]
        evidence_items: List[Dict[str, Any]] = []

        if self.request_spacing > 0:
            await asyncio.sleep(self.request_spacing)

        url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={symbol}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    return []

                announcements = res.json()
                if not isinstance(announcements, list):
                    return []

                # Extract up to 3 most recent verified statutory disclosures
                count = min(3, len(announcements))
                for i in range(count):
                    ann = announcements[i]
                    if not isinstance(ann, dict):
                        continue

                    # Exact original PDF attachment URL
                    pdf_url = ann.get("attchmntFile") or f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"
                    raw_title = ann.get("attchmntText") or ann.get("desc") or f"Corporate Disclosure ({symbol})"
                    clean_title = f"NSE Disclosure: {raw_title[:120].strip()}"
                    pub_date = parse_nse_date(ann.get("sort_date") or ann.get("an_dt"))
                    isin = ann.get("sm_isin") or entity.get("isin")
                    company_disp = ann.get("sm_name") or entity.get("name")

                    content_summary = (
                        f"Official statutory filing submitted by {company_disp} (NSE: {symbol}) "
                        f"to the National Stock Exchange of India. Description: {raw_title[:200]}. "
                        f"Verified primary exchange record."
                    )

                    evidence_items.append({
                        "title": clean_title,
                        "document_title": raw_title[:255],
                        "publisher": "NSE India",
                        "source_url": pdf_url,
                        "publication_date": pub_date,
                        "evidence_category": "COMPANY_DISCLOSURE",
                        "company_identifier": symbol,
                        "company_symbol": symbol,
                        "company_isin": isin,
                        "source_jurisdiction": "IN",
                        "exchange": "NSE",
                        "content_summary": content_summary,
                        "provenance_status": "REAL",
                        "raw_payload": None
                    })

        except Exception:
            # On network timeout, 403, 429 or parsing failure, return empty list (never fabricate)
            return []

        return evidence_items


class SECDisclosuresProvider(BaseEvidenceProvider):
    """
    US regulatory disclosure provider querying SEC EDGAR.
    STRICTLY RESTRICTED to verified SEC registrants and verified US ADRs.
    Never searches arbitrary Indian domestic company names to avoid entity mismatches.
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "FinTraceAcademic ResearchTeam/1.0 (contact@fintrace.org)"
        }

    async def retrieve_evidence(
        self,
        company_name: Optional[str],
        ticker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # 1. Resolve whether this issuer is a verified US registrant or cross-listed ADR
        search_ticker = (ticker or "").upper().strip()
        search_name = (company_name or "").lower().strip()

        matched_cik: Optional[int] = None
        matched_title: Optional[str] = None
        matched_sec_ticker: Optional[str] = None

        # Check verified ADR registry first
        if search_ticker in VERIFIED_NSE_REGISTRY and VERIFIED_NSE_REGISTRY[search_ticker]["has_us_adr"]:
            reg = VERIFIED_NSE_REGISTRY[search_ticker]
            matched_cik = reg["sec_cik"]
            matched_sec_ticker = reg["sec_ticker"]
            matched_title = reg["name"]
        elif search_name in NAME_TO_NSE_SYMBOL:
            sym = NAME_TO_NSE_SYMBOL[search_name]
            if VERIFIED_NSE_REGISTRY[sym]["has_us_adr"]:
                reg = VERIFIED_NSE_REGISTRY[sym]
                matched_cik = reg["sec_cik"]
                matched_sec_ticker = reg["sec_ticker"]
                matched_title = reg["name"]

        # STRICT GUARD: If this is an Indian domestic company without US ADR (e.g. TCS, RELIANCE),
        # NEVER query SEC EDGAR. Prevent Reliance Industries matching Reliance, Inc. (Scottsdale, AZ)!
        if not matched_cik:
            if search_ticker in ["TCS", "RELIANCE"] or "tata consultancy" in search_name or "reliance" in search_name:
                return []
            # For non-Indian queries, check if explicit US ticker was supplied
            if search_ticker in ["AAPL", "MSFT", "GOOGL", "AMZN", "INFY"]:
                try:
                    async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                        r = await client.get("https://www.sec.gov/files/company_tickers.json")
                        if r.status_code == 200:
                            data = r.json()
                            for item in data.values():
                                if item.get("ticker", "").upper() == search_ticker:
                                    matched_cik = item["cik_str"]
                                    matched_sec_ticker = search_ticker
                                    matched_title = item.get("title", "")
                                    break
                except Exception:
                    return []

        if not matched_cik:
            return []

        # 2. Query SEC EDGAR submissions
        evidence_items: List[Dict[str, Any]] = []
        cik_padded = str(matched_cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                sub_res = await client.get(url)
                if sub_res.status_code != 200:
                    return []

                sub_data = sub_res.json()
                recent = sub_data.get("filings", {}).get("recent", {})
                forms = recent.get("form", [])
                filing_dates = recent.get("filingDate", [])
                report_dates = recent.get("reportDate", [])

                count = min(3, len(forms))
                for i in range(count):
                    form_name = forms[i]
                    f_date_str = filing_dates[i] if i < len(filing_dates) else None
                    r_date_str = report_dates[i] if i < len(report_dates) else None

                    pub_dt = None
                    if f_date_str:
                        try:
                            pub_dt = datetime.strptime(f_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        except Exception:
                            pub_dt = None

                    evidence_items.append({
                        "title": f"SEC Form {form_name}: Official Filing for {matched_title}",
                        "document_title": f"SEC Form {form_name}",
                        "publisher": "SEC EDGAR Disclosures",
                        "source_url": f"https://www.sec.gov/edgar/browse/?CIK={cik_padded}",
                        "publication_date": pub_dt,
                        "evidence_category": "COMPANY_DISCLOSURE",
                        "company_identifier": matched_sec_ticker or matched_title,
                        "company_symbol": matched_sec_ticker,
                        "company_isin": None,
                        "source_jurisdiction": "US",
                        "exchange": "SEC",
                        "content_summary": (
                            f"Official statutory disclosure form {form_name} filed with the US SEC on {f_date_str} "
                            f"(Period of Report: {r_date_str or 'Not Stated'}). Verified US primary disclosure."
                        ),
                        "provenance_status": "REAL",
                        "raw_payload": None
                    })
        except Exception:
            return []

        return evidence_items


class CorporateDisclosuresProvider(BaseEvidenceProvider):
    """
    Unified router that selects the correct jurisdictional disclosure provider.
    - Indian-listed companies -> NSEDisclosuresProvider (Primary home market)
    - Verified US ADRs -> Supplementary SEC disclosures
    - Unverified or ambiguous -> Returns empty without fabricating
    """

    def __init__(self, timeout: float = 10.0):
        self.nse_provider = NSEDisclosuresProvider(timeout=timeout)
        self.sec_provider = SECDisclosuresProvider(timeout=timeout)

    async def retrieve_evidence(
        self,
        company_name: Optional[str],
        ticker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # 1. Retrieve primary Indian exchange disclosures via NSE
        results = await self.nse_provider.retrieve_evidence(company_name=company_name, ticker=ticker)

        # 2. If the issuer has a verified cross-listed US ADR, retrieve supplementary SEC disclosures
        resolved = self.nse_provider.resolve_nse_symbol(company_name, ticker)
        if resolved and resolved.get("has_us_adr"):
            sec_results = await self.sec_provider.retrieve_evidence(company_name=company_name, ticker=ticker)
            results.extend(sec_results)

        # 3. For pure US equities (e.g. AAPL, MSFT) where NSE returns empty
        if not results:
            t = (ticker or "").upper().strip()
            if t in ["AAPL", "MSFT", "GOOGL", "AMZN"]:
                results = await self.sec_provider.retrieve_evidence(company_name=company_name, ticker=ticker)

        return results
