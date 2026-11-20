import re
from typing import Dict, Any, List, Optional, Tuple


# Known conglomerates where unadorned name is ambiguous
AMBIGUOUS_ENTITIES = {
    "tata": ["Tata Motors (TATAMOTORS)", "Tata Steel (TATASTEEL)", "Tata Power (TATAPOWER)", "TCS (TCS)"],
    "reliance": ["Reliance Industries (RELIANCE)", "Reliance Power (RPOWER)", "Reliance Infrastructure (RELINFRA)"],
    "adani": ["Adani Enterprises (ADANIENT)", "Adani Ports (ADANIPORTS)", "Adani Green (ADANIGREEN)", "Adani Power (ADANIPOWER)"],
    "birla": ["UltraTech Cement (ULTRACEMCO)", "Grasim Industries (GRASIM)", "Hindalco (HINDALCO)"],
    "bajaj": ["Bajaj Finance (BAJFINANCE)", "Bajaj Finserv (BAJAJFINSV)", "Bajaj Auto (BAJAJ-AUTO)"]
}


class ClaimValidator:
    """
    Deterministic rule-based extractor and validator.
    Strictly preserves unstated information as None. Never invents details.
    """

    @staticmethod
    def inspect_ambiguity(text: str, user_company: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Detects whether entity reference is inherently ambiguous."""
        subject = (user_company or text).lower()
        words = set(re.findall(r'\b[a-z]+\b', subject))

        for brand, candidates in AMBIGUOUS_ENTITIES.items():
            if brand in words:
                # Check if specific subsidiary is qualified
                qualified = False
                for c in candidates:
                    parts = [p.lower() for p in re.findall(r'\b[a-zA-Z]+\b', c)]
                    if any(part in words and part != brand for part in parts):
                        qualified = True
                        break
                if not qualified:
                    candidates_str = ", ".join(candidates)
                    return True, f"Entity reference '{brand.capitalize()}' is ambiguous. Please confirm: {candidates_str}."

        return False, None

    @staticmethod
    def extract_structured_fields(claim_text: str, existing_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extracts testable fields deterministically from claim text.
        If a field is not present in the text, it MUST remain None.
        """
        fields = existing_fields.copy() if existing_fields else {}

        # 1. Direction extraction if not provided
        if not fields.get("claim_direction"):
            lower = claim_text.lower()
            if any(w in lower for w in ["rise", "surge", "rally", "buy", "target", "soar", "gain", "up", "bullish", "multibagger"]):
                fields["claim_direction"] = "BULLISH"
            elif any(w in lower for w in ["fall", "crash", "plunge", "drop", "sell", "down", "bearish", "short", "dump"]):
                fields["claim_direction"] = "BEARISH"
            else:
                fields["claim_direction"] = "UNKNOWN"

        # 2. Target Value and Unit extraction
        if fields.get("target_value") is None:
            # Check percentage target like '30%' or 'rise 25%'
            pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', claim_text)
            if pct_match:
                fields["target_value"] = float(pct_match.group(1))
                fields["target_unit"] = "%"
            else:
                # Check absolute currency target like '₹1500' or 'Rs. 250' or '$50'
                curr_match = re.search(r'(?:₹|rs\.?|\$)\s*(\d+(?:\.\d+)?)', claim_text, re.IGNORECASE)
                if curr_match:
                    fields["target_value"] = float(curr_match.group(1))
                    fields["target_unit"] = "INR" if ("₹" in curr_match.group(0) or "rs" in curr_match.group(0).lower()) else "USD"

        # 3. Time Horizon extraction
        if not fields.get("time_horizon"):
            time_match = re.search(
                r'(?:in|within|next|over)\s+(?:the\s+)?(\d+\s+(?:days?|weeks?|months?|years?)|(?:next\s+)?(?:quarter|two\s+months|year|week))',
                claim_text,
                re.IGNORECASE
            )
            if time_match:
                fields["time_horizon"] = time_match.group(0).strip()

        # 4. Company extraction if user did not provide
        if not fields.get("company_name"):
            # Look for common patterns like 'XYZ Ltd' or 'ABC Inc'
            comp_match = re.search(r'\b([A-Z][A-Za-z0-9&]+(?:\s+(?:Ltd|Limited|Corp|Corporation|Industries|Enterprises|Pvt|Inc))?)\b', claim_text)
            if comp_match and comp_match.group(1).lower() not in ["strong", "buy", "sell", "the", "next", "two", "months"]:
                fields["company_name"] = comp_match.group(1)

        # 5. Check ambiguity
        is_ambiguous, notes = ClaimValidator.inspect_ambiguity(claim_text, fields.get("company_name"))
        fields["is_ambiguous_entity"] = is_ambiguous
        fields["entity_ambiguity_notes"] = notes

        # Missing fields remain explicitly None (entry, exit, invalidation, ticker if not found)
        for key in ["ticker", "exchange", "entry_condition", "exit_condition", "invalidation_condition", "evidence_or_rationale"]:
            if key not in fields:
                fields[key] = None

        return fields

    @staticmethod
    def identify_missing_dimensions(claim: Any) -> List[str]:
        """Identifies which of the 6 key testability dimensions are missing."""
        missing = []
        if not getattr(claim, "company_name", None) and not getattr(claim, "ticker", None):
            missing.append("company_or_ticker")
        if not getattr(claim, "target_value", None):
            missing.append("target_value")
        if not getattr(claim, "time_horizon", None):
            missing.append("time_horizon")
        if not getattr(claim, "entry_condition", None):
            missing.append("entry_condition")
        if not getattr(claim, "exit_condition", None):
            missing.append("exit_condition")
        if not getattr(claim, "invalidation_condition", None):
            missing.append("invalidation_condition")
        return missing
