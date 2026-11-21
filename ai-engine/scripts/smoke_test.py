"""Standalone live smoke-test script for FinTrace AI Engine live providers.

Usage:
    python scripts/smoke_test.py

Requirements:
    - ai-engine/.env populated with GROQ_API_KEY and/or GEMINI_API_KEY.
    - Zero secrets logged to console.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

# Add ai-engine root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine_interface import ClaimExtractionInput
from facade import FinTraceAIEngine
from providers.gemini_provider import GeminiProvider
from providers.groq_provider import GroqProvider
from providers.schemas import LLMMessage, MessageRole, ProviderRequest


def _mask_key(key: str | None) -> str:
    """Mask sensitive API key to prevent secret leakage in terminal logs (Audit Item M-1)."""
    if not key or not key.strip():
        return "[NOT SET]"
    return "[CONFIGURED]"


async def test_live_groq(api_key: str | None) -> bool:
    print("\n--- 1. Testing Live Groq Provider ---")
    if not api_key:
        print("[SKIP] GROQ_API_KEY not configured in .env.")
        return False

    print(f"Key detected: {_mask_key(api_key)}")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    provider = GroqProvider(api_key=api_key, default_model=model)

    req = ProviderRequest(
        model_id=model,
        messages=[
            LLMMessage(role=MessageRole.SYSTEM, content="You are a financial NLP smoke test."),
            LLMMessage(role=MessageRole.USER, content="Reply with: 'GROQ_OPERATIONAL'"),
        ],
        temperature=0.0,
        max_tokens=20,
    )

    try:
        start = time.perf_counter()
        resp = await provider.generate_text(req)
        latency = (time.perf_counter() - start) * 1000.0
        print(f"[SUCCESS] Groq Model: {resp.model_identifier}")
        print(f"          Latency: {latency:.1f}ms (roundtrip)")
        print(f"          Tokens: {resp.token_usage.prompt_tokens} in / {resp.token_usage.completion_tokens} out")
        print(f"          Output: {resp.raw_content.strip()}")
        return True
    except Exception as e:
        print(f"[FAIL] Groq call failed: {type(e).__name__}: {str(e)}")
        return False


async def test_live_gemini(api_key: str | None) -> bool:
    print("\n--- 2. Testing Live Gemini Provider ---")
    if not api_key:
        print("[SKIP] GEMINI_API_KEY not configured in .env.")
        return False

    print(f"Key detected: {_mask_key(api_key)}")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    provider = GeminiProvider(api_key=api_key, default_model=model)

    req = ProviderRequest(
        model_id=model,
        messages=[
            LLMMessage(role=MessageRole.SYSTEM, content="You are a financial NLP smoke test."),
            LLMMessage(role=MessageRole.USER, content="Reply with: 'GEMINI_OPERATIONAL'"),
        ],
        temperature=0.0,
        max_tokens=20,
    )

    try:
        start = time.perf_counter()
        resp = await provider.generate_text(req)
        latency = (time.perf_counter() - start) * 1000.0
        print(f"[SUCCESS] Gemini Model: {resp.model_identifier}")
        print(f"          Latency: {latency:.1f}ms (roundtrip)")
        print(f"          Tokens: {resp.token_usage.prompt_tokens} in / {resp.token_usage.completion_tokens} out")
        print(f"          Output: {resp.raw_content.strip()}")
        return True
    except Exception as e:
        print(f"[FAIL] Gemini call failed: {type(e).__name__}: {str(e)}")
        return False


async def test_live_end_to_end_pipeline() -> None:
    print("\n--- 3. Testing Live Resilient End-to-End Pipeline ---")
    engine = FinTraceAIEngine.from_env()

    health = engine.get_health_status()
    print(f"Engine Primary Provider:  {health.get('primary_provider')}")
    print(f"Engine Reviewer Provider: {health.get('reviewer_provider')}")

    sample_thesis = (
        "Nvidia will reach $200 per share by end of fiscal 2026 driven by Blackwell "
        "datacenter GPU rack deployments, but gross margins will compress if CoWoS packaging yields stall."
    )
    print(f"\nProcessing Sample Thesis:\n\"{sample_thesis}\"")

    inp = ClaimExtractionInput(
        raw_text=sample_thesis,
        source_url="https://fintrace.ai/smoke-test",
        author="Analyst Smoke Test",
    )

    try:
        start = time.perf_counter()
        result = await engine.analyze_end_to_end(inp)
        duration = (time.perf_counter() - start) * 1000.0

        print(f"\n[PIPELINE SUCCESS] Completed in {duration:.1f}ms")
        print(f"  Company / Ticker:    {result.claim.company_name} ({result.claim.ticker})")
        print(f"  Thesis Summary:      {result.claim.claim_summary}")
        print(f"  Direction:           {result.claim.direction.value}")
        print(f"  Target Metric:       {result.claim.target_metric}")
        print(f"  Time Horizon:        {result.claim.time_horizon}")
        print(f"  Falsifiable:         {result.claim.is_falsifiable} (Score: {result.claim.falsifiability_score})")
        print(f"  Invalidation Ctr:    {len(result.claim.invalidation_criteria)} criteria defined")
        print(f"  Deterministic Check: {result.validation.validation_status} (Valid: {result.validation.is_valid})")
        print(f"  Interpretation Forks: {len(result.fork_analysis.forks)} forks generated")
        for i, fork in enumerate(result.fork_analysis.forks, 1):
            print(f"    Fork {i}: [{fork.implied_direction.value}] {fork.fork_title} (w={fork.plausibility_weight:.2f})")

        if result.dual_model_review:
            print(f"  Dual-Model Concord:  {result.dual_model_review.is_concordant}")
            print(f"  Reviewer Notes:      {result.dual_model_review.reviewer_critique_notes[:100]}...")
            print(f"  Consensus Warning:   {result.dual_model_review.consensus_warning}")
        else:
            print("  Dual-Model Review:   Skipped (Single-provider mode)")

    except Exception as e:
        print(f"[FAIL] End-to-end pipeline failed: {type(e).__name__}: {str(e)}")


async def main():
    print("=================================================================")
    print("       FinTrace AI Engine — Phase 2 Live Smoke Test              ")
    print("=================================================================")

    # Load environment variables from .env
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded credentials from {env_path.name}")
    else:
        load_dotenv()
        print("Loaded environment variables from standard path")

    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    groq_ok = await test_live_groq(groq_key)
    gemini_ok = await test_live_gemini(gemini_key)
    await test_live_end_to_end_pipeline()

    print("\n=================================================================")
    print(f" Smoke Test Summary: Groq={'OK' if groq_ok else 'N/A'}, Gemini={'OK' if gemini_ok else 'N/A'}")
    print("=================================================================")


if __name__ == "__main__":
    asyncio.run(main())
