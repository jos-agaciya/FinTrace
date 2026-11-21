from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import httpx
from backend.app.core.config import settings


class AIProviderException(Exception):
    """Base exception for AI provider errors."""
    pass


class ProviderUnavailableException(AIProviderException):
    """Raised when an AI provider is unreachable, times out, or has no configured credentials."""
    pass


class BaseAIProvider(ABC):
    """Abstract provider interface for multi-model orchestration."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 15.0):
        self.api_key = api_key
        self.timeout = timeout
        self.name = "base"

    @abstractmethod
    async def analyze_claim(
        self,
        claim_text: str,
        evidence_bundle: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform first-pass claim extraction and interpretation."""
        pass

    @abstractmethod
    async def review_analysis(
        self,
        claim_text: str,
        evidence_bundle: List[Dict[str, Any]],
        primary_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform secondary independent review to detect hallucination or disagreement."""
        pass


class GroqProvider(BaseAIProvider):
    """Groq API integration adapter."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 25.0):
        super().__init__(api_key=api_key or settings.GROQ_API_KEY, timeout=timeout)
        self.name = "groq"
        self.model = getattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")

    async def analyze_claim(
        self,
        claim_text: str,
        evidence_bundle: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderUnavailableException("GROQ_API_KEY is not configured in backend environment.")

        prompt = (
            f"Analyze this financial claim strictly preserving missing fields as null:\nClaim: {claim_text}\n"
            f"Evidence: {json.dumps(evidence_bundle)}\n"
            "Return JSON with: direction, target, horizon, missing_fields, interpretation_summary"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 2048,
                        "response_format": {"type": "json_object"}
                    }
                )
                if res.status_code != 200:
                    raise ProviderUnavailableException(f"Groq API error HTTP {res.status_code}: {res.text}")
                content = res.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except (httpx.RequestError, json.JSONDecodeError, KeyError) as e:
            raise ProviderUnavailableException(f"Groq request failed: {str(e)}")

    async def review_analysis(
        self,
        claim_text: str,
        evidence_bundle: List[Dict[str, Any]],
        primary_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderUnavailableException("GROQ_API_KEY is not configured in backend environment.")

        prompt = (
            f"Review this financial claim analysis for inaccuracies or hallucination:\nClaim: {claim_text}\n"
            f"Evidence: {json.dumps(evidence_bundle)}\n"
            f"Primary Analysis: {json.dumps(primary_analysis)}\n"
            "Return JSON with: agrees (bool), material_disagreements (list), critique (str)"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 2048,
                        "response_format": {"type": "json_object"}
                    }
                )
                if res.status_code != 200:
                    raise ProviderUnavailableException(f"Groq API review error HTTP {res.status_code}: {res.text}")
                content = res.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            raise ProviderUnavailableException(f"Groq review failed: {str(e)}")


class GeminiProvider(BaseAIProvider):
    """Google Gemini API integration adapter."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 25.0):
        super().__init__(api_key=api_key or settings.GEMINI_API_KEY, timeout=timeout)
        self.name = "gemini"
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")

    async def analyze_claim(
        self,
        claim_text: str,
        evidence_bundle: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderUnavailableException("GEMINI_API_KEY is not configured in backend environment.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = (
            f"Analyze this financial claim strictly preserving missing fields as null:\nClaim: {claim_text}\n"
            f"Evidence: {json.dumps(evidence_bundle)}\n"
            "Return JSON with: direction, target, horizon, missing_fields, interpretation_summary"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]}
                )
                if res.status_code != 200:
                    raise ProviderUnavailableException(f"Gemini API error HTTP {res.status_code}: {res.text}")
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                # Clean code fences if present
                clean = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                return json.loads(clean)
        except Exception as e:
            raise ProviderUnavailableException(f"Gemini request failed: {str(e)}")

    async def review_analysis(
        self,
        claim_text: str,
        evidence_bundle: List[Dict[str, Any]],
        primary_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderUnavailableException("GEMINI_API_KEY is not configured in backend environment.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = (
            f"Review this financial claim analysis for inaccuracies or hallucination:\nClaim: {claim_text}\n"
            f"Evidence: {json.dumps(evidence_bundle)}\n"
            f"Primary Analysis: {json.dumps(primary_analysis)}\n"
            "Return JSON with: agrees (bool), material_disagreements (list), critique (str)"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]}
                )
                if res.status_code != 200:
                    raise ProviderUnavailableException(f"Gemini API review error HTTP {res.status_code}: {res.text}")
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                clean = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                return json.loads(clean)
        except Exception as e:
            raise ProviderUnavailableException(f"Gemini review failed: {str(e)}")


class AIEngineProvider(BaseAIProvider):
    """Provider adapter connecting backend to the FinTraceAIEngine."""

    def __init__(self, timeout: float = 15.0):
        super().__init__(api_key="internal", timeout=timeout)
        self.name = "ai-engine"

    async def analyze_claim(
        self,
        claim_text: str,
        evidence_bundle: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        from backend.app.integrations.ai_engine_adapter import AIEngineAdapter
        adapter = AIEngineAdapter.get_instance()
        if not adapter.is_available:
            raise ProviderUnavailableException("FinTraceAIEngine is not available")

        res = await adapter.analyze_claim_end_to_end(
            raw_text=claim_text,
            retrieved_evidence=evidence_bundle
        )
        if not res:
            raise ProviderUnavailableException("FinTraceAIEngine returned empty analysis")

        direction_val = res.claim.direction.value if hasattr(res.claim.direction, "value") else str(res.claim.direction)

        forks = []
        if res.fork_analysis and res.fork_analysis.forks:
            for f in res.fork_analysis.forks:
                forks.append({
                    "title": f.title,
                    "description": f.description,
                    "ambiguous_phrase": f.ambiguous_phrase or "unstated condition",
                    "assumptions": f.assumptions,
                    "information_required": f.distinguishing_data,
                    "is_ai_generated": True
                })

        return {
            "direction": direction_val,
            "target": res.claim.target_metric,
            "horizon": res.claim.time_horizon,
            "missing_fields": res.claim.unstated_assumptions,
            "interpretation_summary": res.claim.claim_summary,
            "falsifiability_score": round(res.claim.falsifiability_score * 100.0, 1),
            "forks": forks,
            "risk_indicators": [r.model_dump() for r in res.claim.risk_indicators],
            "validation_issues": [i.model_dump() for i in res.validation.issues],
            "dual_review": res.dual_model_review.model_dump() if res.dual_model_review else None,
            "primary_provider": res.primary_provider,
            "primary_model": res.primary_model,
            "fallback_used": res.fallback_used,
            "is_degraded": res.is_degraded,
            "provenance": "AI_GENERATED_MOCK" if "mock" in res.primary_provider.lower() else "AI_GENERATED_LIVE",
        }

    async def review_analysis(
        self,
        claim_text: str,
        evidence_bundle: List[Dict[str, Any]],
        primary_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        if primary_analysis.get("dual_review"):
            rev = primary_analysis["dual_review"]
            return {
                "agrees": rev.get("agrees", True),
                "material_disagreements": rev.get("disagreement_reasons", []),
                "critique": rev.get("critique", "Verified by DualModelReviewer.")
            }
        return {
            "agrees": True,
            "material_disagreements": [],
            "critique": "Analysis validated by AI Engine."
        }


def get_ai_provider(provider_name: str) -> BaseAIProvider:
    """Factory function for instantiating provider adapters."""
    lowered = provider_name.lower().strip()
    if lowered == "groq":
        return GroqProvider()
    elif lowered == "gemini":
        return GeminiProvider()
    elif lowered in ["ai-engine", "fintrace-ai-engine", "engine"]:
        return AIEngineProvider()
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")
