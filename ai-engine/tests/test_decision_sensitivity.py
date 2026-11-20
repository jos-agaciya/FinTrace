"""Tests for Decision Sensitivity Explanation Engine."""

import pytest
from interpretation.schemas import InterpretationFork
from interpretation.sensitivity import (
    DecisionRecord,
    DecisionSensitivityEngine,
    DecisionSensitivityInput,
)
from claim_extraction.schemas import DirectionEnum


@pytest.fixture
def engine():
    return DecisionSensitivityEngine()


def test_detects_confidence_and_allocation_changes(engine):
    """Verify numeric deltas and neutral descriptions are correctly calculated."""
    inp = DecisionSensitivityInput(
        initial_decision=DecisionRecord(
            confidence_level=4.0,
            hypothetical_allocation_pct=60.0,
            written_rationale="High growth potential in autonomous technology.",
        ),
        revised_decision=DecisionRecord(
            confidence_level=2.0,
            hypothetical_allocation_pct=20.0,
            written_rationale="After reading the filing, operating margins exclude regulatory credits.",
        ),
    )

    result = engine.explain_sensitivity(inp)
    assert result.confidence_delta == -2.0
    assert result.allocation_delta_pct == -40.0
    assert "decreased by 2.0 points" in result.confidence_shift_description
    assert "decreased by 40.0 percentage points" in result.allocation_shift_description
    assert not result.unexplained_variance_flag


def test_identifies_correlated_interpretation_fork(engine):
    """Verify that words in revised rationale matching an interpretation fork are identified."""
    fork_a = InterpretationFork(
        fork_title="Automotive Gross Margin Ex-Regulatory Credits",
        scenario_description="Core vehicle delivery margin without regulatory subsidy income.",
        plausibility_weight=0.6,
        implied_direction=DirectionEnum.NEUTRAL,
        distinguishing_evidence_needed="Quarterly 10-Q GAAP gross margin bridge.",
    )

    inp = DecisionSensitivityInput(
        initial_decision=DecisionRecord(
            confidence_level=4.0,
            hypothetical_allocation_pct=50.0,
            written_rationale="Deliveries will rise 30%.",
        ),
        revised_decision=DecisionRecord(
            confidence_level=2.5,
            hypothetical_allocation_pct=25.0,
            written_rationale="Concerned about regulatory credits driving margin rather than automotive execution.",
        ),
        selected_interpretation_forks=[fork_a],
    )

    result = engine.explain_sensitivity(inp)
    assert len(result.associated_assumptions_or_forks) >= 1
    assert "Automotive Gross Margin Ex-Regulatory Credits" in result.associated_assumptions_or_forks[0]


def test_never_classifies_allocation_reduction_as_success(engine):
    """CRITICAL INVARIANT: Decreasing allocation must never be labeled 'better', 'smarter', or 'success'."""
    inp = DecisionSensitivityInput(
        initial_decision=DecisionRecord(
            confidence_level=5.0,
            hypothetical_allocation_pct=100.0,
            written_rationale="All in on breakout.",
        ),
        revised_decision=DecisionRecord(
            confidence_level=1.0,
            hypothetical_allocation_pct=0.0,
            written_rationale="Exited position completely after seeing missing timeframe.",
        ),
    )

    result = engine.explain_sensitivity(inp)
    full_output = f"{result.summary_of_change} {result.behavioral_disclaimer}".lower()

    # Must NOT praise or pass normative judgment
    assert "success" not in full_output
    assert "smarter" not in full_output
    assert "superior" not in full_output
    assert "better decision" not in full_output
    assert "not an investment quality score" in result.behavioral_disclaimer


def test_unexplained_variance_when_rationale_missing(engine):
    """Verify shift without revised rationale flags unexplained variance."""
    inp = DecisionSensitivityInput(
        initial_decision=DecisionRecord(
            confidence_level=3.0,
            hypothetical_allocation_pct=30.0,
            written_rationale="Initial view.",
        ),
        revised_decision=DecisionRecord(
            confidence_level=1.0,
            hypothetical_allocation_pct=5.0,
            written_rationale="",  # Empty revised rationale
        ),
    )

    result = engine.explain_sensitivity(inp)
    assert result.unexplained_variance_flag is True
    assert "not established" in result.summary_of_change.lower()


def test_unchanged_decision_handling(engine):
    """Verify zero shift in allocation and confidence produces unchanged description."""
    inp = DecisionSensitivityInput(
        initial_decision=DecisionRecord(
            confidence_level=3.0,
            hypothetical_allocation_pct=25.0,
            written_rationale="Holding allocation.",
        ),
        revised_decision=DecisionRecord(
            confidence_level=3.0,
            hypothetical_allocation_pct=25.0,
            written_rationale="Still holding allocation after reviewing report.",
        ),
    )

    result = engine.explain_sensitivity(inp)
    assert result.confidence_delta == 0.0
    assert result.allocation_delta_pct == 0.0
    assert "unchanged" in result.summary_of_change.lower()
    assert not result.unexplained_variance_flag


def test_preserves_initial_and_revised_rationales(engine):
    """Verify input rationales are faithfully preserved on the output object."""
    init_text = "I believe the market is mispricing this asset."
    rev_text = "Revised view: macroeconomic headwinds may delay the timeline."

    inp = DecisionSensitivityInput(
        initial_decision=DecisionRecord(
            confidence_level=4.0,
            hypothetical_allocation_pct=50.0,
            written_rationale=init_text,
        ),
        revised_decision=DecisionRecord(
            confidence_level=3.0,
            hypothetical_allocation_pct=30.0,
            written_rationale=rev_text,
        ),
    )

    result = engine.explain_sensitivity(inp)
    assert result.initial_rationale_preserved == init_text
    assert result.revised_rationale_preserved == rev_text
