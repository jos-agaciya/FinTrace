import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';

const DECISION_OPTIONS = [
  {
    value: 'GOOD',
    label: 'GOOD',
    desc: 'Expect the situation or stock price to improve.',
    backendValue: 'Bullish'
  },
  {
    value: 'NEUTRAL',
    label: 'NEUTRAL',
    desc: 'Expect little or no significant change; uncertain.',
    backendValue: 'Neutral'
  },
  {
    value: 'BAD',
    label: 'BAD',
    desc: 'Expect the situation or stock price to worsen.',
    backendValue: 'Bearish'
  }
];

const mapStanceToBackend = (stance) => {
  if (!stance) return 'Neutral';
  const upper = String(stance).toUpperCase();
  if (upper.includes('GOOD') || upper.includes('BULLISH') || upper.includes('RISE')) return 'Bullish';
  if (upper.includes('BAD') || upper.includes('BEARISH') || upper.includes('FALL')) return 'Bearish';
  return 'Neutral';
};

export default function VirtualDecisionLab() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('');
  const [loadingScenarios, setLoadingScenarios] = useState(true);

  // Phase 1: First Decision
  const [initialStance, setInitialStance] = useState('');
  const [initialConfidence, setInitialConfidence] = useState(85);
  const [initialRationale, setInitialRationale] = useState('');

  // Phase 2: Evidence Review
  const [reviewedEvidence, setReviewedEvidence] = useState({});

  // Phase 3: Updated Decision
  const [updatedStance, setUpdatedStance] = useState('');
  const [updatedConfidence, setUpdatedConfidence] = useState(58);
  const [updatedRationale, setUpdatedRationale] = useState('');

  // UI, Validation & Submission state
  const [submitting, setSubmitting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [savedResult, setSavedResult] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const [fieldErrors, setFieldErrors] = useState({});

  // Decision History from SQLite
  const [history, setHistory] = useState([]);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  // References for scrolling
  const errorRef = useRef(null);
  const resultsRef = useRef(null);
  const phase1Ref = useRef(null);
  const phase2Ref = useRef(null);
  const phase3Ref = useRef(null);

  const loadDecisionsHistory = async () => {
    try {
      const records = await api.getDecisions();
      const mapped = (records || []).map((r) => {
        const delta = r.revised_confidence != null ? r.revised_confidence - r.initial_confidence : 0;
        return {
          id: r.id,
          scenarioId: r.claim_id,
          scenarioTitle: r.initial_thesis,
          ticker: r.claim_id ? r.claim_id.slice(0, 8).toUpperCase() : 'DEC',
          company: 'Persistent Portfolio Decision',
          displayDate: r.created_at
            ? new Date(r.created_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })
            : 'Recent',
          initialStance: r.initial_confidence > 55 ? 'GOOD' : (r.initial_confidence < 45 ? 'BAD' : 'NEUTRAL'),
          initialConfidence: r.initial_confidence,
          initialRationale: r.initial_thesis,
          reviewedEvidenceCount: 1,
          totalEvidenceCount: 1,
          reviewedEvidenceTitles: ['Primary verified corporate disclosures and filed filings'],
          updatedStance: r.revised_confidence != null
            ? (r.revised_confidence > 55 ? 'GOOD' : (r.revised_confidence < 45 ? 'BAD' : 'NEUTRAL'))
            : 'NEUTRAL',
          updatedConfidence: r.revised_confidence ?? r.initial_confidence,
          updatedRationale: r.revised_thesis || r.reason_for_change || '',
          confidenceDelta: delta,
          stanceChanged: false,
          decisionStrength: Math.abs(delta) > 10 ? 'Strong' : 'Calibrated',
          feedbackHeadline: r.sensitivity_summary?.shift_explanation || r.reason_for_change || 'Decision persisted in SQLite database.',
          learningSummary: r.sensitivity_summary?.shift_explanation || 'Saved and persisted in SQLite.'
        };
      });
      setHistory(mapped);
    } catch (e) {
      // Ignore
    }
  };

  // Initialize data on mount
  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const [scs] = await Promise.all([
          api.getDecisionLabScenarios(),
          loadDecisionsHistory()
        ]);
        if (isMounted) {
          if (Array.isArray(scs) && scs.length > 0) {
            setScenarios(scs);
            setSelectedScenarioId(scs[0].id);
            resetFormForScenario(scs[0], false);
          }
          setLoadingScenarios(false);
        }
      } catch (err) {
        if (isMounted) setLoadingScenarios(false);
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  const currentScenario = scenarios.find((s) => s.id === selectedScenarioId) || scenarios[0] || null;

  const resetFormForScenario = (scenario, clearRationale = true) => {
    if (!scenario) return;
    setInitialStance('');
    setInitialConfidence(85);
    setInitialRationale(clearRationale ? '' : scenario.defaultInitialRationale || '');
    setReviewedEvidence({});
    setUpdatedStance('');
    setUpdatedConfidence(58);
    setUpdatedRationale('');
    setSavedResult(null);
    setSaveSuccess(false);
    setValidationErrors([]);
    setFieldErrors({});
  };

  const handleScenarioChange = (newId) => {
    if (newId === selectedScenarioId) return;

    const hasUnsavedProgress =
      initialStance.length > 0 ||
      initialRationale.length > 0 ||
      Object.values(reviewedEvidence).some(Boolean) ||
      updatedStance.length > 0 ||
      updatedRationale.length > 0;

    if (hasUnsavedProgress && !savedResult) {
      const confirmChange = window.confirm(
        'You have an ongoing practice session. Discard changes and switch to this scenario?'
      );
      if (!confirmChange) return;
    }

    const nextScenario = scenarios.find((s) => s.id === newId) || scenarios[0];
    setSelectedScenarioId(newId);
    resetFormForScenario(nextScenario, false);
  };

  const toggleEvidence = (evidenceId) => {
    setReviewedEvidence((prev) => {
      const updated = { ...prev, [evidenceId]: !prev[evidenceId] };
      return updated;
    });
    setFieldErrors((prev) => ({ ...prev, evidence: false }));
    setValidationErrors((prev) => prev.filter((err) => !err.includes('evidence')));
  };

  const reviewedCount = Object.values(reviewedEvidence).filter(Boolean).length;
  const totalEvidenceCount = currentScenario ? (currentScenario.evidenceItems?.length || 0) : 0;

  const handleStartNewSession = () => {
    if (!currentScenario) return;
    const hasUnsaved =
      !savedResult &&
      (initialStance.length > 0 ||
        initialRationale.length > 0 ||
        reviewedCount > 0 ||
        updatedStance.length > 0 ||
        updatedRationale.length > 0);

    if (hasUnsaved) {
      const confirmDiscard = window.confirm(
        'Start a new session? Your current unsaved inputs will be cleared.'
      );
      if (!confirmDiscard) return;
    }

    resetFormForScenario(currentScenario, true);
  };

  const validateInputs = () => {
    const errors = [];
    const fields = {};

    if (!initialStance) {
      errors.push('Phase 1: Please select your first decision (GOOD, NEUTRAL, or BAD).');
      fields.initialStance = true;
    }

    if (!initialRationale || initialRationale.trim().length === 0) {
      errors.push('Phase 1: Please enter your reasoning explanation.');
      fields.initialRationale = true;
    }

    if (totalEvidenceCount > 0 && reviewedCount === 0) {
      errors.push('Phase 2: Please review and check at least one piece of evidence.');
      fields.evidence = true;
    }

    if (!updatedStance) {
      errors.push('Phase 3: Please select your updated decision after reviewing the facts (GOOD, NEUTRAL, or BAD).');
      fields.updatedStance = true;
    }

    if (!updatedRationale || updatedRationale.trim().length === 0) {
      errors.push('Phase 3: Please explain why you kept or changed your decision.');
      fields.updatedRationale = true;
    }

    return { errors, fields };
  };

  const handleCalibrateAndSave = async (e) => {
    if (e) e.preventDefault();
    if (submitting || !currentScenario) return;

    const { errors, fields } = validateInputs();
    if (errors.length > 0) {
      setValidationErrors(errors);
      setFieldErrors(fields);

      if (fields.initialStance || fields.initialRationale) {
        phase1Ref.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else if (fields.evidence) {
        phase2Ref.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else if (fields.updatedStance || fields.updatedRationale) {
        phase3Ref.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        errorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    setValidationErrors([]);
    setFieldErrors({});
    setSubmitting(true);

    try {
      const delta = updatedConfidence - initialConfidence;
      const stanceChanged = initialStance !== updatedStance;

      let feedbackHeadline = '';
      if (stanceChanged) {
        feedbackHeadline = 'You adjusted your stance after reviewing filed disclosures and constraints.';
      } else if (delta < 0) {
        feedbackHeadline = 'You kept your original thesis, but calibrated confidence downward based on identified risks.';
      } else if (delta > 0) {
        feedbackHeadline = 'You reviewed the verified evidence and reaffirmed conviction with higher confidence.';
      } else {
        feedbackHeadline = 'You kept your original decision and your confidence remained steady.';
      }

      const reviewedTitles = (currentScenario.evidenceItems || [])
        .filter((item) => reviewedEvidence[item.id])
        .map((item) => item.title);

      // 1. Persist Initial Decision to SQLite
      const initialRecord = await api.recordDecision({
        claim_id: currentScenario.id,
        initial_thesis: initialRationale,
        initial_confidence: initialConfidence,
        initial_allocation: 50.0,
        assumptions_evaluated: Object.keys(reviewedEvidence).filter((k) => reviewedEvidence[k])
      });

      // 2. Persist Revision to SQLite
      let sensitivitySummary = null;
      if (initialRecord && initialRecord.id) {
        const revisedRecord = await api.reviseDecision(initialRecord.id, {
          revised_thesis: updatedRationale,
          revised_confidence: updatedConfidence,
          revised_allocation: 50.0,
          reason_for_change: feedbackHeadline || updatedRationale,
          assumptions_evaluated: Object.keys(reviewedEvidence).filter((k) => reviewedEvidence[k])
        });
        sensitivitySummary = revisedRecord.sensitivity_summary;
      }

      // 3. Submit calibration sync
      try {
        await api.submitDecisionCalibration({
          initialStance: mapStanceToBackend(initialStance),
          initialConfidence,
          revisedStance: mapStanceToBackend(updatedStance),
          revisedConfidence: updatedConfidence,
          refutedAssumptions: reviewedEvidence
        });
      } catch (calibErr) {
        // calibration is auxiliary
      }

      const sessionRecord = {
        id: initialRecord?.id || `session_${Date.now()}`,
        scenarioId: currentScenario.id,
        scenarioTitle: currentScenario.title,
        ticker: currentScenario.ticker,
        company: currentScenario.company,
        completedAt: new Date().toISOString(),
        displayDate: new Date().toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        }),
        initialStance,
        initialConfidence,
        initialRationale,
        reviewedEvidenceCount: reviewedCount,
        totalEvidenceCount,
        reviewedEvidenceTitles: reviewedTitles,
        updatedStance,
        updatedConfidence,
        updatedRationale,
        confidenceDelta: delta,
        stanceChanged,
        decisionStrength: Math.abs(delta) > 10 ? 'Strong' : 'Moderate',
        feedbackHeadline: sensitivitySummary?.shift_explanation || feedbackHeadline,
        learningSummary: sensitivitySummary?.shift_explanation || currentScenario.learningOutcomes?.changedMind || 'Session persisted to SQLite.'
      };

      setSavedResult(sessionRecord);
      setSaveSuccess(true);
      await loadDecisionsHistory();
      setSubmitting(false);

      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err) {
      setValidationErrors([`Failed to persist decision: ${err.message || 'Unknown error'}`]);
      setSubmitting(false);
    }
  };

  if (loadingScenarios) {
    return (
      <div className="flex-1 p-gutter-xl flex items-center justify-center">
        <div className="flex items-center gap-2 text-body-md font-mono">
          <span className="material-symbols-outlined animate-spin text-[20px]">progress_activity</span>
          <span>Loading Decision Lab scenarios...</span>
        </div>
      </div>
    );
  }

  if (!currentScenario) {
    return (
      <main className="flex-1 p-gutter-md lg:p-gutter-lg max-w-6xl w-full mx-auto flex flex-col gap-gutter-lg pb-24">
        <div className="flex flex-col gap-gutter-xs">
          <h1 className="font-display text-display-lg-mobile lg:text-display-lg font-bold">
            Virtual Decision Lab
          </h1>
          <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
            Write down what you think before and after checking the evidence.
          </p>
        </div>

        <div className="p-12 rounded-2xl bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col items-center justify-center text-center gap-4">
          <span className="material-symbols-outlined text-[48px] text-light-primary dark:text-dark-primary">
            science
          </span>
          <h2 className="font-headline text-headline-md font-bold">
            No Active Practice Scenarios Available
          </h2>
          <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-md">
            The Decision Lab generates interactive scenarios directly from verified claims and filed disclosures in the database.
            Analyse your first claim to unlock practice scenarios.
          </p>
          <Link
            to="/analyse-claim"
            className="px-6 py-3 rounded-full bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-lg font-bold shadow-md hover:opacity-90"
          >
            Analyse a Claim Now
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 p-gutter-md lg:p-gutter-lg max-w-6xl w-full mx-auto flex flex-col gap-gutter-lg pb-24">
      {/* Title & Description */}
      <div className="flex flex-col gap-gutter-xs">
        <h1
          className="font-display text-display-lg-mobile lg:text-display-lg font-bold"
          data-design-text-token="display-lg"
        >
          Virtual Decision Lab
        </h1>
        <p
          className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant"
          data-design-text-token="body-lg"
        >
          Write down what you think before and after checking the evidence.
        </p>
      </div>

      {/* Educational Guardrail Banner */}
      <div className="p-gutter-md rounded-2xl bg-light-primary-container/60 dark:bg-dark-primary-container/40 border border-light-outline-variant dark:border-dark-outline-variant flex flex-col sm:flex-row items-start sm:items-center justify-between gap-gutter-md">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-light-primary dark:text-dark-primary text-[24px]">
            balance
          </span>
          <div>
            <p className="font-title text-title-md font-semibold">
              Practice Your Investment Decisions
            </p>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
              This area helps you check whether your investment decisions improve after reviewing
              the facts. This is for learning, not for deciding when to buy or sell.
            </p>
          </div>
        </div>
        <span className="font-mono text-mono-sm px-2.5 py-1 rounded-full bg-light-surface dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant font-semibold text-xs whitespace-nowrap">
          SQLITE PERSISTENCE ACTIVE
        </span>
      </div>

      {/* Scenario Selector & Overview Card */}
      <section className="p-gutter-lg rounded-2xl bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant shadow-sm flex flex-col gap-gutter-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-light-outline-variant dark:border-dark-outline-variant pb-3">
          <div>
            <span className="text-label-sm text-light-outline dark:text-dark-outline uppercase font-mono tracking-wider text-[11px]">
              Active Educational Scenario
            </span>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="font-mono font-bold text-light-primary dark:text-dark-primary text-sm px-2 py-0.5 rounded bg-light-primary/10 dark:bg-dark-primary/15 border border-light-primary/20">
                {currentScenario.ticker}
              </span>
              <h2 className="font-headline text-headline-md font-bold">
                {currentScenario.company}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant font-medium whitespace-nowrap">
              Switch Scenario:
            </label>
            <select
              value={selectedScenarioId}
              onChange={(e) => handleScenarioChange(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-sm font-semibold outline-none focus:border-light-primary dark:focus:border-dark-primary"
            >
              {scenarios.map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.ticker} — {sc.company}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant/60 dark:border-dark-outline-variant/60 flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-light-primary dark:text-dark-primary">
              feed
            </span>
            <span className="font-semibold text-body-md text-light-on-surface dark:text-dark-on-surface">
              {currentScenario.title}
            </span>
          </div>
          <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] leading-relaxed">
            {currentScenario.summary}
          </p>
          <div className="mt-1 pt-1 border-t border-light-outline-variant/40 dark:border-dark-outline-variant/40 flex items-center justify-between text-[12px] font-medium text-light-primary dark:text-dark-primary">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">help</span>
              <span>{currentScenario.firstImpressionQuestion}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Top Validation Banner */}
      {validationErrors.length > 0 && (
        <div
          ref={errorRef}
          className="p-gutter-md rounded-2xl bg-rose-500/10 border-2 border-rose-500/40 text-rose-700 dark:text-rose-300 flex flex-col gap-1.5 shadow-sm"
        >
          <div className="flex items-center gap-2 font-bold text-body-md">
            <span className="material-symbols-outlined text-[20px] text-rose-600">error</span>
            <span>Please complete the required items before saving:</span>
          </div>
          <ul className="list-disc pl-6 text-body-sm space-y-1">
            {validationErrors.map((err, idx) => (
              <li key={idx} className="font-medium">
                {err}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Step 1 & Step 3 Dual Decision Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter-lg">
        {/* Panel 1: Your First Decision */}
        <section
          ref={phase1Ref}
          className={`p-gutter-lg rounded-2xl bg-light-surface dark:bg-dark-surface-container-low border transition-all flex flex-col justify-between gap-gutter-md shadow-sm ${
            fieldErrors.initialStance || fieldErrors.initialRationale
              ? 'border-rose-500/60 ring-2 ring-rose-500/20'
              : 'border-light-outline-variant dark:border-dark-outline-variant'
          }`}
        >
          <div className="flex flex-col gap-gutter-md">
            <div className="flex items-center justify-between border-b border-light-outline-variant dark:border-dark-outline-variant pb-3">
              <div>
                <span className="text-label-sm text-light-outline dark:text-dark-outline uppercase font-mono tracking-wider text-[11px]">
                  Step 1
                </span>
                <h2 className="font-headline text-headline-md font-bold">Your First Decision</h2>
              </div>
              <span className="material-symbols-outlined text-light-on-surface-variant dark:text-dark-on-surface-variant">
                history
              </span>
            </div>

            {/* Stance Choice */}
            <div className="flex flex-col gap-gutter-xs">
              <label className="font-label text-label-lg font-semibold flex items-center justify-between">
                <span>What Do You Think?</span>
                <span
                  className={`text-xs font-semibold ${
                    fieldErrors.initialStance ? 'text-rose-500' : 'text-light-on-surface-variant dark:text-dark-on-surface-variant'
                  }`}
                >
                  * Required
                </span>
              </label>
              <div className="grid grid-cols-3 gap-2">
                {DECISION_OPTIONS.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => {
                      setInitialStance(s.value);
                      setFieldErrors((prev) => ({ ...prev, initialStance: false }));
                      setValidationErrors((prev) => prev.filter((err) => !err.includes('first decision')));
                    }}
                    className={`py-2 px-1.5 rounded-xl font-label text-center border transition-all ${
                      initialStance === s.value
                        ? 'bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary border-transparent shadow-sm'
                        : fieldErrors.initialStance
                        ? 'bg-rose-500/5 border-rose-400 text-light-on-surface dark:text-dark-on-surface'
                        : 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant text-light-on-surface dark:text-dark-on-surface hover:border-light-primary/50'
                    }`}
                  >
                    <div className="text-label-sm font-bold tracking-wide">{s.label}</div>
                    <div className="text-[11px] opacity-85 mt-0.5 leading-tight">{s.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Confidence Slider */}
            <div className="flex flex-col gap-gutter-xs">
              <div className="flex items-center justify-between">
                <label className="font-label text-label-lg font-semibold">How Confident Are You?</label>
                <span className="font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary text-base">
                  {initialConfidence}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={initialConfidence}
                onChange={(e) => setInitialConfidence(+e.target.value)}
                className="w-full accent-light-primary dark:accent-dark-primary cursor-pointer h-2 bg-light-surface-container-high dark:bg-dark-surface-container-high rounded-lg"
              />
              <div className="flex justify-between text-[11px] text-light-outline dark:text-dark-outline font-mono">
                <span>0% (No confidence)</span>
                <span>50% (Moderate)</span>
                <span>100% (Certain)</span>
              </div>
            </div>

            {/* Rationale */}
            <div className="flex flex-col gap-gutter-xs">
              <label className="font-label text-label-lg font-semibold flex items-center justify-between">
                <span>Why Do You Think So?</span>
                <span
                  className={`text-xs font-semibold ${
                    fieldErrors.initialRationale ? 'text-rose-500' : 'text-light-on-surface-variant dark:text-dark-on-surface-variant'
                  }`}
                >
                  * Required
                </span>
              </label>
              <textarea
                rows={3}
                value={initialRationale}
                placeholder="Explain what factors led to your first decision..."
                onChange={(e) => {
                  setInitialRationale(e.target.value);
                  setFieldErrors((prev) => ({ ...prev, initialRationale: false }));
                  setValidationErrors((prev) => prev.filter((err) => !err.includes('first decision')));
                }}
                className={`w-full px-gutter-md py-2.5 rounded-xl text-body-md text-light-on-surface dark:text-dark-on-surface outline-none text-sm leading-relaxed border transition-all ${
                  fieldErrors.initialRationale
                    ? 'border-rose-500 bg-rose-500/5'
                    : 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant focus:border-light-primary dark:focus:border-dark-primary'
                }`}
              />
            </div>
          </div>
        </section>

        {/* Panel 3: Your Updated Decision */}
        <section
          ref={phase3Ref}
          className={`p-gutter-lg rounded-2xl bg-light-surface dark:bg-dark-surface-container-low border transition-all flex flex-col justify-between gap-gutter-md shadow-sm ${
            fieldErrors.updatedStance || fieldErrors.updatedRationale
              ? 'border-rose-500/60 ring-2 ring-rose-500/20'
              : 'border-light-outline-variant dark:border-dark-outline-variant'
          }`}
        >
          <div className="flex flex-col gap-gutter-md">
            <div className="flex items-center justify-between border-b border-light-outline-variant dark:border-dark-outline-variant pb-3">
              <div>
                <span className="text-label-sm text-emerald-600 dark:text-emerald-400 uppercase font-mono tracking-wider text-[11px]">
                  Step 3
                </span>
                <h2 className="font-headline text-headline-md font-bold">
                  Your Decision After Reviewing the Facts
                </h2>
              </div>
              <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400">
                published_with_changes
              </span>
            </div>

            {/* Stance Choice */}
            <div className="flex flex-col gap-gutter-xs">
              <label className="font-label text-label-lg font-semibold flex items-center justify-between">
                <span>Your Updated View</span>
                <span
                  className={`text-xs font-semibold ${
                    fieldErrors.updatedStance ? 'text-rose-500' : 'text-light-on-surface-variant dark:text-dark-on-surface-variant'
                  }`}
                >
                  * Required
                </span>
              </label>
              <div className="grid grid-cols-3 gap-2">
                {DECISION_OPTIONS.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => {
                      setUpdatedStance(s.value);
                      setFieldErrors((prev) => ({ ...prev, updatedStance: false }));
                      setValidationErrors((prev) => prev.filter((err) => !err.includes('updated decision')));
                    }}
                    className={`py-2 px-1.5 rounded-xl font-label text-center border transition-all ${
                      updatedStance === s.value
                        ? 'bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary border-transparent shadow-sm'
                        : fieldErrors.updatedStance
                        ? 'bg-rose-500/5 border-rose-400 text-light-on-surface dark:text-dark-on-surface'
                        : 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant text-light-on-surface dark:text-dark-on-surface hover:border-light-primary/50'
                    }`}
                  >
                    <div className="text-label-sm font-bold tracking-wide">{s.label}</div>
                    <div className="text-[11px] opacity-85 mt-0.5 leading-tight">{s.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Confidence Slider */}
            <div className="flex flex-col gap-gutter-xs">
              <div className="flex items-center justify-between">
                <label className="font-label text-label-lg font-semibold">Your Updated Confidence</label>
                <span className="font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary text-base">
                  {updatedConfidence}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={updatedConfidence}
                onChange={(e) => setUpdatedConfidence(+e.target.value)}
                className="w-full accent-light-primary dark:accent-dark-primary cursor-pointer h-2 bg-light-surface-container-high dark:bg-dark-surface-container-high rounded-lg"
              />
              <div className="flex justify-between text-[11px] text-light-outline dark:text-dark-outline font-mono">
                <span>0% (No confidence)</span>
                <span>50% (Moderate)</span>
                <span>100% (Certain)</span>
              </div>
            </div>

            {/* Updated Rationale */}
            <div className="flex flex-col gap-gutter-xs">
              <label className="font-label text-label-lg font-semibold flex items-center justify-between">
                <span>Why did you keep or change your decision?</span>
                <span
                  className={`text-xs font-semibold ${
                    fieldErrors.updatedRationale ? 'text-rose-500' : 'text-light-on-surface-variant dark:text-dark-on-surface-variant'
                  }`}
                >
                  * Required
                </span>
              </label>
              <textarea
                rows={3}
                value={updatedRationale}
                placeholder="Explain how the evidence influenced your decision..."
                onChange={(e) => {
                  setUpdatedRationale(e.target.value);
                  setFieldErrors((prev) => ({ ...prev, updatedRationale: false }));
                  setValidationErrors((prev) => prev.filter((err) => !err.includes('explain why you kept')));
                }}
                className={`w-full px-gutter-md py-2.5 rounded-xl text-body-md text-light-on-surface dark:text-dark-on-surface outline-none text-sm leading-relaxed border transition-all ${
                  fieldErrors.updatedRationale
                    ? 'border-rose-500 bg-rose-500/5'
                    : 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant focus:border-light-primary dark:focus:border-dark-primary'
                }`}
              />
            </div>
          </div>
        </section>
      </div>

      {/* Step 2: Evidence Review Checklist */}
      {currentScenario.evidenceItems && currentScenario.evidenceItems.length > 0 && (
        <section
          ref={phase2Ref}
          className={`p-gutter-lg rounded-2xl bg-light-surface dark:bg-dark-surface-container-low border transition-all shadow-sm flex flex-col gap-gutter-md ${
            fieldErrors.evidence
              ? 'border-rose-500/60 ring-2 ring-rose-500/20'
              : 'border-light-outline-variant dark:border-dark-outline-variant'
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-light-outline-variant dark:border-dark-outline-variant pb-3">
            <div>
              <span className="text-label-sm text-purple-600 dark:text-purple-400 uppercase font-mono tracking-wider text-[11px]">
                Step 2
              </span>
              <h2 className="font-headline text-headline-md font-bold">
                Review the Evidence
              </h2>
              <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Check off the filed disclosures and risk points below before finalizing your decision.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span
                className={`font-mono text-mono-sm font-semibold px-3 py-1 rounded-full border text-xs ${
                  reviewedCount > 0
                    ? 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/30'
                    : fieldErrors.evidence
                    ? 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/30'
                    : 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30'
                }`}
              >
                Reviewed {reviewedCount} of {totalEvidenceCount} items
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter-md">
            {currentScenario.evidenceItems.map((item) => {
              const isChecked = !!reviewedEvidence[item.id];
              const isPositive = item.type === 'positive';

              return (
                <div
                  key={item.id}
                  onClick={() => toggleEvidence(item.id)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-3 select-none ${
                    isChecked
                      ? 'bg-light-primary/5 dark:bg-dark-primary/10 border-light-primary dark:border-dark-primary shadow-sm'
                      : 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant hover:border-light-outline'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => {}}
                    className="mt-1 h-4 w-4 rounded text-light-primary dark:text-dark-primary accent-light-primary dark:accent-dark-primary cursor-pointer"
                  />
                  <div className="flex-1 flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                          isPositive
                            ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                            : 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
                        }`}
                      >
                        {item.category}
                      </span>
                      <span className="text-[11px] text-light-outline dark:text-dark-outline font-mono">
                        {item.source}
                      </span>
                    </div>
                    <h4 className="font-semibold text-body-md text-light-on-surface dark:text-dark-on-surface">
                      {item.title}
                    </h4>
                    <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12.5px] leading-relaxed">
                      {item.detail}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Action Bar: Calibrate & Save Decision + Reset */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <button
          type="button"
          onClick={handleStartNewSession}
          className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-light-outline-variant dark:border-dark-outline-variant bg-light-surface-container-low dark:bg-dark-surface-container hover:bg-light-surface-container dark:hover:bg-dark-surface-container-high text-body-md font-semibold text-light-on-surface dark:text-dark-on-surface flex items-center justify-center gap-2 transition-all shadow-sm cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">restart_alt</span>
          <span>Reset / Start New Session</span>
        </button>

        <button
          type="button"
          id="calibrate-and-save-button"
          data-testid="calibrate-save-button"
          onClick={handleCalibrateAndSave}
          disabled={submitting}
          className="w-full sm:w-auto min-w-[280px] py-3.5 px-7 rounded-xl bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-lg font-bold hover:opacity-95 active:scale-[0.99] transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-60 cursor-pointer"
        >
          {submitting ? (
            <>
              <span className="material-symbols-outlined animate-spin text-[20px]">
                progress_activity
              </span>
              <span>Persisting to Database...</span>
            </>
          ) : (
            <>
              <span className="material-symbols-outlined text-[20px]">save</span>
              <span>Calibrate & Save Decision</span>
            </>
          )}
        </button>
      </div>

      {/* Results & Comparison Card */}
      {savedResult && (
        <section
          ref={resultsRef}
          className="p-gutter-lg rounded-2xl bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-md animate-fadeIn"
        >
          {saveSuccess && (
            <div className="p-4 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-800 dark:text-emerald-200 flex items-center gap-2.5 font-semibold text-body-md">
              <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400 text-[22px]">
                verified
              </span>
              <span>
                Decision Calibrated & Persisted to SQLite! Your record has been added to the database.
              </span>
            </div>
          )}

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-light-outline-variant dark:border-dark-outline-variant pb-3">
            <div>
              <span className="text-label-sm text-emerald-600 dark:text-emerald-400 uppercase font-mono tracking-wider text-[11px]">
                Decision Results
              </span>
              <h2 className="font-headline text-headline-md font-bold">
                Comparing Your First Decision vs. Your Updated Decision
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`font-mono text-mono-sm px-3 py-1 rounded-full font-bold text-xs ${
                  savedResult.confidenceDelta < 0
                    ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
                    : savedResult.confidenceDelta > 0
                    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                    : 'bg-light-surface-container dark:bg-dark-surface-container'
                }`}
              >
                {savedResult.confidenceDelta > 0
                  ? `+${savedResult.confidenceDelta} PTS CONFIDENCE`
                  : `${savedResult.confidenceDelta} PTS CONFIDENCE`}
              </span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/25 text-purple-900 dark:text-purple-200 flex items-center gap-3">
            <span className="material-symbols-outlined text-[24px] text-purple-600 dark:text-purple-400">
              lightbulb
            </span>
            <div className="flex flex-col">
              <span className="font-bold text-body-md">{savedResult.feedbackHeadline}</span>
              <span className="text-body-sm text-[12.5px] opacity-90">
                {savedResult.stanceChanged
                  ? `Decision stance shifted from "${savedResult.initialStance}" to "${savedResult.updatedStance}".`
                  : `Decision stance maintained as "${savedResult.updatedStance}".`}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md">
            <div className="p-gutter-md rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1">
              <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase font-mono text-[11px]">
                First Confidence Level
              </span>
              <p className="font-display text-headline-lg font-bold text-rose-500">
                {savedResult.initialConfidence}%
              </p>
              <span className="text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Stance: <span className="font-semibold">{savedResult.initialStance}</span>
              </span>
            </div>

            <div className="p-gutter-md rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1">
              <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase font-mono text-[11px]">
                Updated Confidence Level
              </span>
              <p className="font-display text-headline-lg font-bold text-emerald-500">
                {savedResult.updatedConfidence}%
              </p>
              <span className="text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Stance: <span className="font-semibold">{savedResult.updatedStance}</span>
              </span>
            </div>

            <div className="p-gutter-md rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1">
              <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase font-mono text-[11px]">
                Confidence Change
              </span>
              <p className="font-display text-headline-lg font-bold text-light-primary dark:text-dark-primary">
                {savedResult.confidenceDelta} percentage points
              </p>
              <span className="text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Reviewed {savedResult.reviewedEvidenceCount} of {savedResult.totalEvidenceCount} facts
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter-md">
            <div className="p-3.5 rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1">
              <span className="text-xs font-semibold uppercase text-light-outline dark:text-dark-outline">
                Your Initial Reasoning:
              </span>
              <p className="text-body-sm text-light-on-surface dark:text-dark-on-surface italic">
                "{savedResult.initialRationale}"
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1">
              <span className="text-xs font-semibold uppercase text-emerald-600 dark:text-emerald-400">
                Your Updated Reasoning:
              </span>
              <p className="text-body-sm text-light-on-surface dark:text-dark-on-surface italic">
                "{savedResult.updatedRationale}"
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Decision History Section (Loaded from SQLite) */}
      <section className="p-gutter-lg rounded-2xl bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant shadow-sm flex flex-col gap-gutter-md">
        <div className="flex items-center justify-between border-b border-light-outline-variant dark:border-dark-outline-variant pb-3">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-light-primary dark:text-dark-primary">
              manage_history
            </span>
            <h2 className="font-headline text-headline-md font-bold">
              Persistent Decision Records ({history.length})
            </h2>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="p-8 text-center flex flex-col items-center justify-center gap-2 text-light-on-surface-variant dark:text-dark-on-surface-variant">
            <span className="material-symbols-outlined text-[36px] text-light-outline dark:text-dark-outline">
              history_edu
            </span>
            <p className="font-semibold text-body-md">No saved practice sessions yet.</p>
            <p className="text-body-sm text-[13px]">
              Complete your first exercise above to review and track your decision calibration over time in the database.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {history.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-light-primary/50 transition-all"
              >
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-light-primary/10 dark:bg-dark-primary/15 text-light-primary dark:text-dark-primary">
                      {item.ticker}
                    </span>
                    <span className="font-semibold text-body-md text-light-on-surface dark:text-dark-on-surface">
                      {item.company}
                    </span>
                    <span className="text-xs text-light-outline dark:text-dark-outline font-mono">
                      • {item.displayDate || 'Recent'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                    <span>Initial: <strong className="text-light-on-surface dark:text-dark-on-surface">{item.initialStance} ({item.initialConfidence}%)</strong></span>
                    <span>→</span>
                    <span>Updated: <strong className="text-light-on-surface dark:text-dark-on-surface">{item.updatedStance} ({item.updatedConfidence}%)</strong></span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`font-mono text-xs font-bold px-2.5 py-1 rounded-full ${
                      item.confidenceDelta < 0
                        ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
                        : item.confidenceDelta > 0
                        ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                        : 'bg-light-surface dark:bg-dark-surface-container-high'
                    }`}
                  >
                    {item.confidenceDelta > 0 ? `+${item.confidenceDelta} pts` : `${item.confidenceDelta} pts`}
                  </span>

                  <button
                    type="button"
                    onClick={() => setSelectedHistoryItem(item)}
                    className="px-3 py-1.5 rounded-lg border border-light-outline-variant dark:border-dark-outline-variant bg-light-surface dark:bg-dark-surface text-body-sm font-semibold hover:border-light-primary transition-all flex items-center gap-1 cursor-pointer"
                  >
                    <span>View Details</span>
                    <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* History Details Modal */}
      {selectedHistoryItem && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="max-w-2xl w-full bg-light-surface dark:bg-dark-surface-container rounded-2xl border border-light-outline-variant dark:border-dark-outline-variant shadow-2xl p-6 flex flex-col gap-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-light-outline-variant dark:border-dark-outline-variant pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-sm px-2 py-0.5 rounded bg-light-primary/10 text-light-primary">
                  {selectedHistoryItem.ticker}
                </span>
                <h3 className="font-headline text-headline-md font-bold">
                  {selectedHistoryItem.company}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedHistoryItem(null)}
                className="p-1 rounded-lg hover:bg-light-surface-container-high dark:hover:bg-dark-surface-container-high transition-all cursor-pointer"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="flex flex-col gap-3 text-body-sm">
              <div className="p-3 rounded-xl bg-purple-500/10 text-purple-900 dark:text-purple-200 font-medium">
                {selectedHistoryItem.feedbackHeadline}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-light-surface-container-low dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant">
                  <span className="text-xs uppercase font-mono text-light-outline dark:text-dark-outline">
                    First Decision
                  </span>
                  <p className="font-semibold text-body-md">{selectedHistoryItem.initialStance}</p>
                  <p className="text-xs font-mono text-rose-500 font-bold">
                    Confidence: {selectedHistoryItem.initialConfidence}%
                  </p>
                  <p className="text-xs mt-2 italic text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    "{selectedHistoryItem.initialRationale}"
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-light-surface-container-low dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant">
                  <span className="text-xs uppercase font-mono text-emerald-600 dark:text-emerald-400">
                    Updated Decision
                  </span>
                  <p className="font-semibold text-body-md">{selectedHistoryItem.updatedStance}</p>
                  <p className="text-xs font-mono text-emerald-500 font-bold">
                    Confidence: {selectedHistoryItem.updatedConfidence}%
                  </p>
                  <p className="text-xs mt-2 italic text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    "{selectedHistoryItem.updatedRationale}"
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-light-surface-container-low dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant">
                <span className="text-xs uppercase font-mono text-light-outline dark:text-dark-outline">
                  Reviewed Evidence ({selectedHistoryItem.reviewedEvidenceCount || 0} items)
                </span>
                <ul className="list-disc pl-5 mt-1 text-xs space-y-1 text-light-on-surface-variant dark:text-dark-on-surface-variant">
                  {selectedHistoryItem.reviewedEvidenceTitles &&
                  selectedHistoryItem.reviewedEvidenceTitles.length > 0 ? (
                    selectedHistoryItem.reviewedEvidenceTitles.map((t, i) => (
                      <li key={i}>{t}</li>
                    ))
                  ) : (
                    <li>Reviewed facts from scenario docket</li>
                  )}
                </ul>
              </div>

              <div className="p-3 rounded-xl bg-light-surface-container-low dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant">
                <span className="text-xs uppercase font-mono text-light-outline dark:text-dark-outline">
                  Learning Summary
                </span>
                <p className="text-xs mt-1 leading-relaxed text-light-on-surface-variant dark:text-dark-on-surface-variant">
                  {selectedHistoryItem.learningSummary}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setSelectedHistoryItem(null)}
              className="mt-2 py-2 px-4 rounded-xl bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-semibold text-body-sm self-end cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
