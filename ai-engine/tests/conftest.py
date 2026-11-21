"""Shared pytest fixtures for AI Engine test suite."""

import sys
from pathlib import Path
import pytest

# Ensure ai-engine root is in sys.path for direct package discovery
AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent
if str(AI_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ENGINE_ROOT))


@pytest.fixture
def sample_raw_claim_text() -> str:
    return (
        "Tesla will reach $400 by end of 2026 driven by Robotaxi autonomy scaling. "
        "Thesis invalidated if Robotaxi commercial launch does not occur by Q4 2026."
    )


@pytest.fixture
def sample_vague_claim_text() -> str:
    return "Tech stocks look set for a massive rally very soon!"
