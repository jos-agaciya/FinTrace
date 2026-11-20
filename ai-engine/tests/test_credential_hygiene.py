"""Regression tests verifying zero credential leakage in logging and diagnostics (Audit Item M-1)."""

import pytest

from scripts.smoke_test import _mask_key


def test_mask_key_hygiene_zero_partial_leakage():
    """Verify that _mask_key never logs any partial substring of a sensitive credential."""
    test_keys = [
        "gsk_1234567890abcdefghijklmnopqrstuvwxyz",
        "AQ.A1234567890_ZYXWVUTSRQPONMLKJIHGFEDCBA-urA",
        "sk-proj-9876543210fedcba",
        "short",
        "123",
    ]

    for key in test_keys:
        output = _mask_key(key)
        assert output == "[CONFIGURED]"
        # Proves that NO substring of the key with length >= 3 appears in output
        for i in range(len(key) - 2):
            sub = key[i : i + 3]
            assert sub not in output, f"Key substring '{sub}' leaked in output: {output}"


def test_mask_key_empty_or_none():
    """Verify empty or None credentials return [NOT SET]."""
    assert _mask_key(None) == "[NOT SET]"
    assert _mask_key("") == "[NOT SET]"
    assert _mask_key("   ") == "[NOT SET]"
