import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function AssessmentModal({ stage = 'BASELINE', isOpen, onClose, onCompleted }) {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState(null);
  const [loadingPrompt, setLoadingPrompt] = useState(false);
  const [promptError, setPromptError] = useState(null);

  // Form state
  const [identifiedEvidenceTypes, setIdentifiedEvidenceTypes] = useState([]);
  const [distinguishedPrimarySources, setDistinguishedPrimarySources] = useState(true);
  const [identifiedMissingSpecificity, setIdentifiedMissingSpecificity] = useState([]);
  const [recognizedAlternativeInterpretations, setRecognizedAlternativeInterpretations] = useState(true);
  const [statedConfidence, setStatedConfidence] = useState(50);
  const [evidenceBackingLevel, setEvidenceBackingLevel] = useState('NONE');
  const [identifiedRiskFactors, setIdentifiedRiskFactors] = useState([]);
  const [confidenceJustification, setConfidenceJustification] = useState('');

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [result, setResult] = useState(null);
  const [comparison, setComparison] = useState(null);

  useEffect(() => {
    if (!isOpen) {
      setResult(null);
      setComparison(null);
      setSubmitError(null);
      return;
    }

    let isMounted = true;
    async function fetchPrompt() {
      setLoadingPrompt(true);
      setPromptError(null);
      try {
        const data = await api.getAssessmentPrompt(stage);
        if (isMounted) {
          setPrompt(data);
          // Set sensible starting defaults based on stage
          if (stage === 'BASELINE') {
            setIdentifiedEvidenceTypes(['UNVERIFIED_COMMENTARY']);
            setDistinguishedPrimarySources(true);
            setIdentifiedMissingSpecificity(['time_horizon', 'baseline_definition']);
            setRecognizedAlternativeInterpretations(true);
            setStatedConfidence(60);
            setEvidenceBackingLevel('LOW');
            setIdentifiedRiskFactors(['Execution Delay Risk']);
            setConfidenceJustification('The claim is sourced from promotional commentary without formal 10-K or 10-Q disclosures.');
          } else {
            setIdentifiedEvidenceTypes(['COMPANY_DISCLOSURE', 'REGULATORY_FILING']);
            setDistinguishedPrimarySources(true);
            setIdentifiedMissingSpecificity(['time_horizon', 'invalidation_condition', 'entry_condition']);
            setRecognizedAlternativeInterpretations(true);
            setStatedConfidence(40);
            setEvidenceBackingLevel('LOW');
            setIdentifiedRiskFactors(['Execution Delay Risk', 'Margin Compression Risk', 'Regulatory Risk']);
            setConfidenceJustification('Maintained disciplined 40% confidence because unconfirmed tariff renegotiations and absent invalidation criteria create severe downside risk.');
          }
          setLoadingPrompt(false);
        }
      } catch (err) {
        if (isMounted) {
          setPromptError(err.message || 'Failed to load assessment prompt');
          setLoadingPrompt(false);
        }
      }
    }
    fetchPrompt();

    return () => {
      isMounted = false;
    };
  }, [isOpen, stage]);

  if (!isOpen) return null;

  const toggleEvidenceType = (id) => {
    setIdentifiedEvidenceTypes((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleMissingSpecificity = (id) => {
    setIdentifiedMissingSpecificity((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleRiskFactor = (label) => {
    setIdentifiedRiskFactors((prev) =>
      prev.includes(label) ? prev.filter((item) => item !== label) : [...prev, label]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt) return;

    setSubmitting(true);
    setSubmitError(null);

    const payload = {
      session_id: 'me',
      claim_id: prompt.claim_id,
      assessment_stage: stage,
      identified_evidence_types: identifiedEvidenceTypes,
      distinguished_primary_sources: Boolean(distinguishedPrimarySources),
      identified_missing_specificity: identifiedMissingSpecificity,
      identified_risk_factors: identifiedRiskFactors,
      recognized_alternative_interpretations: Boolean(recognizedAlternativeInterpretations),
      stated_confidence: Number(statedConfidence),
      evidence_backing_level: evidenceBackingLevel,
      confidence_justification: confidenceJustification.trim(),
      raw_answers: {
        stage,
        submitted_at: new Date().toISOString()
      }
    };

    try {
      const res = await api.submitAssessment(payload);
      setResult(res);

      if (stage === 'INDEPENDENT_TRANSFER') {
        try {
          const comp = await api.compareAssessmentStages('me');
          setComparison(comp);
        } catch (e) {
          // Non-blocking if baseline was missing
        }
      }

      if (onCompleted) {
        onCompleted(res);
      }
    } catch (err) {
      setSubmitError(err.message || 'Assessment submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const isStage1 = stage === 'BASELINE';
  const stageTitle = isStage1 ? 'Stage 1: Baseline Onboarding' : 'Stage 3: Independent Assessment';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-light-surface dark:bg-dark-surface-container rounded-xl max-w-4xl w-full border border-light-outline-variant dark:border-dark-outline-variant shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 border-b border-light-outline-variant dark:border-dark-outline-variant flex items-center justify-between bg-light-surface-container-low dark:bg-dark-surface-container-low">
          <div className="flex items-center gap-3">
            <span
              className={`px-3 py-1 rounded-full text-label-sm font-mono font-bold uppercase tracking-wider ${
                isStage1
                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
                  : 'bg-primary-100 text-light-primary dark:bg-primary-900/40 dark:text-dark-primary'
              }`}
            >
              {stageTitle}
            </span>
            <h2 className="font-headline text-headline-sm font-bold text-light-on-surface dark:text-dark-on-surface">
              {result ? 'Evaluation Results & Rubric Feedback' : 'Investor Decision Evaluation'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-light-on-surface-variant hover:bg-light-surface-container dark:hover:bg-dark-surface text-[20px] transition-colors"
            title="Close"
          >
            ✕
          </button>
        </div>

        {/* Content body */}
        <div className="p-6 overflow-y-auto flex-1 flex flex-col gap-6">
          {loadingPrompt ? (
            <div className="py-16 flex flex-col items-center justify-center gap-3">
              <span className="material-symbols-outlined animate-spin text-[36px] text-light-primary dark:text-dark-primary">
                progress_activity
              </span>
              <p className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Initializing evaluation environment & unassisted claim...
              </p>
            </div>
          ) : promptError ? (
            <div className="p-4 rounded-lg bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-300 text-body-md border border-red-200 dark:border-red-800">
              <p className="font-semibold">Unable to load assessment prompt:</p>
              <p className="font-mono text-mono-sm mt-1">{promptError}</p>
            </div>
          ) : result ? (
            /* Results Screen */
            <div className="flex flex-col gap-6">
              {/* Score banner */}
              <div className="p-5 rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex flex-col gap-1 text-center sm:text-left">
                  <span className="text-label-sm font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase">
                    Deterministic Composite Score
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="font-display text-display-md font-bold text-light-primary dark:text-dark-primary">
                      {Math.round(result.total_score)}
                    </span>
                    <span className="font-mono text-mono-md text-light-on-surface-variant dark:text-dark-on-surface-variant">
                      / 100
                    </span>
                  </div>
                  <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-md">
                    Scored across five transparent cognitive anchors without opaque generative guessing.
                  </p>
                </div>

                {comparison && (
                  <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex flex-col gap-1 text-center sm:text-right">
                    <span className="text-label-sm font-mono text-emerald-800 dark:text-emerald-300 font-semibold uppercase">
                      Stage Delta vs Baseline
                    </span>
                    <span className="font-display text-headline-lg font-bold text-emerald-600 dark:text-emerald-400">
                      {comparison.percentage_point_delta >= 0 ? '+' : ''}
                      {comparison.percentage_point_delta} pts
                    </span>
                    <span className="text-[11px] font-mono text-emerald-700 dark:text-emerald-300">
                      Baseline: {Math.round(comparison.baseline_score)} → Transfer: {Math.round(comparison.latest_transfer_score)}
                    </span>
                  </div>
                )}
              </div>

              {comparison?.comparison_summary && (
                <div className="p-4 rounded-lg bg-light-primary-container/30 border border-light-primary/30 flex items-start gap-3">
                  <span className="material-symbols-outlined text-light-primary dark:text-dark-primary text-[22px]">
                    insights
                  </span>
                  <p className="text-body-md text-light-on-surface dark:text-dark-on-surface text-[14px]">
                    {comparison.comparison_summary}
                  </p>
                </div>
              )}

              {/* 5 Dimensions Breakdown */}
              <div className="flex flex-col gap-4">
                <h3 className="font-headline text-headline-sm font-bold">
                  Five Assessment Dimensions Rubric Feedback
                </h3>

                <div className="grid grid-cols-1 gap-3">
                  {/* D1 */}
                  <div className="p-4 rounded-lg bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-body-md">1. Evidence Scrutiny & Primary Provenance</span>
                      <span className="font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary">
                        {result.score_evidence_eval} / 20
                      </span>
                    </div>
                    <div className="w-full bg-light-surface-container dark:bg-dark-surface-container h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-light-primary dark:bg-dark-primary h-full rounded-full"
                        style={{ width: `${(result.score_evidence_eval / 20) * 100}%` }}
                      />
                    </div>
                    <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] mt-1">
                      {result.rubric_feedback?.evidence_evaluation}
                    </p>
                  </div>

                  {/* D2 */}
                  <div className="p-4 rounded-lg bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-body-md">2. Horizon Realism & Claim Specificity</span>
                      <span className="font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary">
                        {result.score_claim_specificity} / 20
                      </span>
                    </div>
                    <div className="w-full bg-light-surface-container dark:bg-dark-surface-container h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-light-primary dark:bg-dark-primary h-full rounded-full"
                        style={{ width: `${(result.score_claim_specificity / 20) * 100}%` }}
                      />
                    </div>
                    <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] mt-1">
                      {result.rubric_feedback?.claim_specificity}
                    </p>
                  </div>

                  {/* D3 */}
                  <div className="p-4 rounded-lg bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-body-md">3. Downside Risk Awareness</span>
                      <span className="font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary">
                        {result.score_risk_awareness} / 20
                      </span>
                    </div>
                    <div className="w-full bg-light-surface-container dark:bg-dark-surface-container h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-light-primary dark:bg-dark-primary h-full rounded-full"
                        style={{ width: `${(result.score_risk_awareness / 20) * 100}%` }}
                      />
                    </div>
                    <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] mt-1">
                      {result.rubric_feedback?.risk_awareness}
                    </p>
                  </div>

                  {/* D4 */}
                  <div className="p-4 rounded-lg bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-body-md">4. Assumption Invalidation</span>
                      <span className="font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary">
                        {result.score_assumption_awareness} / 20
                      </span>
                    </div>
                    <div className="w-full bg-light-surface-container dark:bg-dark-surface-container h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-light-primary dark:bg-dark-primary h-full rounded-full"
                        style={{ width: `${(result.score_assumption_awareness / 20) * 100}%` }}
                      />
                    </div>
                    <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] mt-1">
                      {result.rubric_feedback?.assumption_awareness}
                    </p>
                  </div>

                  {/* D5 */}
                  <div className="p-4 rounded-lg bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-body-md">5. Cognitive Calibration & Justification</span>
                      <span className="font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary">
                        {result.score_confidence_calibration} / 20
                      </span>
                    </div>
                    <div className="w-full bg-light-surface-container dark:bg-dark-surface-container h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-light-primary dark:bg-dark-primary h-full rounded-full"
                        style={{ width: `${(result.score_confidence_calibration / 20) * 100}%` }}
                      />
                    </div>
                    <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] mt-1">
                      {result.rubric_feedback?.confidence_calibration}
                    </p>
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex flex-wrap items-center justify-end gap-3 pt-4 border-t border-light-outline-variant dark:border-dark-outline-variant">
                {isStage1 ? (
                  <button
                    onClick={() => {
                      onClose();
                      navigate('/virtual-decision-lab');
                    }}
                    className="px-5 py-2.5 rounded-lg bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-md font-semibold hover:opacity-90 flex items-center gap-2"
                  >
                    <span>Proceed to Stage 2: Virtual Decision Lab</span>
                    <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                  </button>
                ) : null}
                <button
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-lg bg-light-surface-container dark:bg-dark-surface-container text-light-on-surface dark:text-dark-on-surface font-label text-label-md font-semibold hover:bg-light-surface-container-high"
                >
                  Return to Decision Intelligence
                </button>
              </div>
            </div>
          ) : (
            /* Questionnaire Form */
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
              {/* Target Claim Presentation Box */}
              <div className="p-5 rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-mono-md font-bold text-light-primary dark:text-dark-primary">
                      {prompt.ticker}
                    </span>
                    <span className="text-body-sm font-semibold text-light-on-surface dark:text-dark-on-surface">
                      · {prompt.company_name}
                    </span>
                  </div>
                  <span className="text-[12px] font-mono px-2 py-0.5 rounded bg-light-surface-container dark:bg-dark-surface text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    Horizon: {prompt.time_horizon}
                  </span>
                </div>

                <blockquote className="p-3.5 rounded-lg bg-light-surface dark:bg-dark-surface border-l-4 border-light-primary dark:border-dark-primary text-body-md font-medium text-light-on-surface dark:text-dark-on-surface">
                  "{prompt.statement}"
                </blockquote>

                <div className="flex items-center gap-2 text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                  <span className="material-symbols-outlined text-[16px]">info</span>
                  <span>{prompt.source_context}</span>
                </div>

                <div className="text-[13px] bg-primary-50 dark:bg-primary-950/40 p-2.5 rounded border border-primary-200 dark:border-primary-800 text-light-primary dark:text-dark-primary">
                  {prompt.guidance}
                </div>
              </div>

              {/* Dimension 1: Evidence Scrutiny */}
              <div className="p-5 rounded-xl bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-title text-title-md font-bold flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-light-primary-container text-light-primary dark:bg-dark-primary-container dark:text-dark-primary flex items-center justify-center text-[12px] font-mono font-bold">
                      1
                    </span>
                    Evidence Scrutiny
                  </h3>
                  <span className="text-label-sm font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    0 – 20 pts
                  </span>
                </div>
                <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                  Which statutory disclosures and audited filings are strictly required to verify the claim's financial metrics? (Select all that apply)
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
                  {[
                    { id: 'REGULATORY_FILING', label: 'Audited Annual Report (10-K / Form 20-F)', desc: 'Audited balance sheet, cash flows & note disclosures' },
                    { id: 'COMPANY_DISCLOSURE', label: 'Quarterly Segment Reports (10-Q)', desc: 'Unaudited interim operating margins by division' },
                    { id: 'BOARD_RESOLUTION', label: 'Material Contract Filing (8-K / Clause 30)', desc: 'Regulatory disclosure confirming enterprise contracts' },
                    { id: 'EARNINGS_TRANSCRIPT', label: 'Earnings Call Transcript & Guidance Q&A', desc: 'Management remarks and analyst Q&A' },
                    { id: 'PRESS_RELEASE', label: 'Unverified Promotional Press Release', desc: 'Marketing brief without statutory audit verification' },
                    { id: 'UNVERIFIED_COMMENTARY', label: 'Social Media / Forum Speculation', desc: 'Anonymous message board or newsletter hype' }
                  ].map((opt) => {
                    const checked = identifiedEvidenceTypes.includes(opt.id);
                    return (
                      <button
                        type="button"
                        key={opt.id}
                        onClick={() => toggleEvidenceType(opt.id)}
                        className={`p-3 rounded-lg border text-left flex flex-col gap-1 transition-all ${
                          checked
                            ? 'border-light-primary dark:border-dark-primary bg-light-primary-container/20 dark:bg-dark-primary-container/20'
                            : 'border-light-outline-variant dark:border-dark-outline-variant bg-light-surface-container-low dark:bg-dark-surface-container hover:border-light-outline'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-body-sm font-semibold text-light-on-surface dark:text-dark-on-surface">
                            {opt.label}
                          </span>
                          <span
                            className={`w-4 h-4 rounded flex items-center justify-center text-[12px] font-bold ${
                              checked
                                ? 'bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary'
                                : 'border border-light-outline-variant'
                            }`}
                          >
                            {checked ? '✓' : ''}
                          </span>
                        </div>
                        <span className="text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                          {opt.desc}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Dimension 2: Source Provenance */}
              <div className="p-5 rounded-xl bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-title text-title-md font-bold flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-light-primary-container text-light-primary dark:bg-dark-primary-container dark:text-dark-primary flex items-center justify-center text-[12px] font-mono font-bold">
                      2
                    </span>
                    Source Provenance
                  </h3>
                  <span className="text-label-sm font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    0 – 20 pts
                  </span>
                </div>
                <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                  Does this statement originate from an authoritative primary statutory disclosure, or secondary unverified commentary?
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1">
                  <button
                    type="button"
                    onClick={() => setDistinguishedPrimarySources(true)}
                    className={`p-3.5 rounded-lg border text-left flex flex-col gap-1 transition-all ${
                      distinguishedPrimarySources === true
                        ? 'border-light-primary dark:border-dark-primary bg-light-primary-container/20 dark:bg-dark-primary-container/20'
                        : 'border-light-outline-variant dark:border-dark-outline-variant bg-light-surface-container-low dark:bg-dark-surface-container'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-body-sm font-semibold">
                        Secondary Unverified Commentary
                      </span>
                      <span className="text-[14px]">
                        {distinguishedPrimarySources === true ? '●' : '○'}
                      </span>
                    </div>
                    <span className="text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                      Lacks direct regulatory grounding; requires independent statutory audit before allocation.
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setDistinguishedPrimarySources(false)}
                    className={`p-3.5 rounded-lg border text-left flex flex-col gap-1 transition-all ${
                      distinguishedPrimarySources === false
                        ? 'border-light-primary dark:border-dark-primary bg-light-primary-container/20 dark:bg-dark-primary-container/20'
                        : 'border-light-outline-variant dark:border-dark-outline-variant bg-light-surface-container-low dark:bg-dark-surface-container'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-body-sm font-semibold">
                        Primary Audited Regulatory Source
                      </span>
                      <span className="text-[14px]">
                        {distinguishedPrimarySources === false ? '●' : '○'}
                      </span>
                    </div>
                    <span className="text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                      Asserts the statement is an official, audited statutory disclosure directly actionable.
                    </span>
                  </button>
                </div>
              </div>

              {/* Dimension 3: Horizon Realism & Claim Specificity */}
              <div className="p-5 rounded-xl bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-title text-title-md font-bold flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-light-primary-container text-light-primary dark:bg-dark-primary-container dark:text-dark-primary flex items-center justify-center text-[12px] font-mono font-bold">
                      3
                    </span>
                    Horizon Realism & Claim Specificity
                  </h3>
                  <span className="text-label-sm font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    0 – 20 pts
                  </span>
                </div>
                <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                  Which critical boundary conditions, baseline metrics, or time horizons are missing from this claim? (Select all that apply)
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
                  {[
                    { id: 'time_horizon', label: 'Definite Contract Milestone Dates', desc: 'No verifiable calendar dates for revenue recognition' },
                    { id: 'baseline_definition', label: 'Clear Margin Baseline Definition', desc: 'Unstated whether 25% is GAAP operating or non-GAAP adjusted' },
                    { id: 'invalidation_condition', label: 'Explicit Invalidation / Falsification Metric', desc: 'Absence of negative threshold that disproves thesis' },
                    { id: 'entry_condition', label: 'Prerequisite Capex & Approvals', desc: 'Unstated capital expenditure and regulatory clearance' },
                    { id: 'exit_condition', label: 'Downside Stop-Loss Boundaries', desc: 'Lack of risk constraints if customer contract churn occurs' }
                  ].map((opt) => {
                    const checked = identifiedMissingSpecificity.includes(opt.id);
                    return (
                      <button
                        type="button"
                        key={opt.id}
                        onClick={() => toggleMissingSpecificity(opt.id)}
                        className={`p-3 rounded-lg border text-left flex flex-col gap-1 transition-all ${
                          checked
                            ? 'border-light-primary dark:border-dark-primary bg-light-primary-container/20 dark:bg-dark-primary-container/20'
                            : 'border-light-outline-variant dark:border-dark-outline-variant bg-light-surface-container-low dark:bg-dark-surface-container hover:border-light-outline'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-body-sm font-semibold text-light-on-surface dark:text-dark-on-surface">
                            {opt.label}
                          </span>
                          <span
                            className={`w-4 h-4 rounded flex items-center justify-center text-[12px] font-bold ${
                              checked
                                ? 'bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary'
                                : 'border border-light-outline-variant'
                            }`}
                          >
                            {checked ? '✓' : ''}
                          </span>
                        </div>
                        <span className="text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                          {opt.desc}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Dimension 4: Assumption Invalidation */}
              <div className="p-5 rounded-xl bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-title text-title-md font-bold flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-light-primary-container text-light-primary dark:bg-dark-primary-container dark:text-dark-primary flex items-center justify-center text-[12px] font-mono font-bold">
                      4
                    </span>
                    Assumption Invalidation
                  </h3>
                  <span className="text-label-sm font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    0 – 20 pts
                  </span>
                </div>
                <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                  Can this projection yield divergent financial interpretations under different operational or macroeconomic assumptions?
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1">
                  <button
                    type="button"
                    onClick={() => setRecognizedAlternativeInterpretations(true)}
                    className={`p-3.5 rounded-lg border text-left flex flex-col gap-1 transition-all ${
                      recognizedAlternativeInterpretations === true
                        ? 'border-light-primary dark:border-dark-primary bg-light-primary-container/20 dark:bg-dark-primary-container/20'
                        : 'border-light-outline-variant dark:border-dark-outline-variant bg-light-surface-container-low dark:bg-dark-surface-container'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-body-sm font-semibold">
                        Yes — Divergent Scenarios Exist
                      </span>
                      <span className="text-[14px]">
                        {recognizedAlternativeInterpretations === true ? '●' : '○'}
                      </span>
                    </div>
                    <span className="text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                      Margin compression occurs if hardware integration costs balloon or deal closures lag.
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRecognizedAlternativeInterpretations(false)}
                    className={`p-3.5 rounded-lg border text-left flex flex-col gap-1 transition-all ${
                      recognizedAlternativeInterpretations === false
                        ? 'border-light-primary dark:border-dark-primary bg-light-primary-container/20 dark:bg-dark-primary-container/20'
                        : 'border-light-outline-variant dark:border-dark-outline-variant bg-light-surface-container-low dark:bg-dark-surface-container'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-body-sm font-semibold">
                        No — Single Outcome Guaranteed
                      </span>
                      <span className="text-[14px]">
                        {recognizedAlternativeInterpretations === false ? '●' : '○'}
                      </span>
                    </div>
                    <span className="text-[12px] text-light-on-surface-variant dark:text-dark-on-surface-variant">
                      Assumes revenue and margin growth are deterministic and unencumbered.
                    </span>
                  </button>
                </div>
              </div>

              {/* Dimension 5: Cognitive Calibration & Justification */}
              <div className="p-5 rounded-xl bg-light-surface dark:bg-dark-surface border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-title text-title-md font-bold flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-light-primary-container text-light-primary dark:bg-dark-primary-container dark:text-dark-primary flex items-center justify-center text-[12px] font-mono font-bold">
                      5
                    </span>
                    Cognitive Calibration & Confidence Justification
                  </h3>
                  <span className="text-label-sm font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    0 – 20 pts
                  </span>
                </div>
                <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                  Calibrate your stated conviction level and justify how available evidence, identified missing conditions, and downside risks inform your confidence.
                </p>

                {/* Stated confidence slider */}
                <div className="flex flex-col gap-2 p-3.5 rounded-lg bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant">
                  <div className="flex items-center justify-between">
                    <label className="text-body-sm font-semibold">Stated Conviction / Confidence</label>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[12px] font-mono font-bold px-2 py-0.5 rounded ${
                          statedConfidence > 75
                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
                            : statedConfidence < 40
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                            : 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300'
                        }`}
                      >
                        {statedConfidence > 75
                          ? 'High Conviction Stance'
                          : statedConfidence < 40
                          ? 'Restrained / Conservative Stance'
                          : 'Moderate Conviction'}
                      </span>
                      <span className="font-mono text-mono-md font-bold text-light-primary dark:text-dark-primary tabular-nums">
                        {statedConfidence}%
                      </span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={statedConfidence}
                    onChange={(e) => setStatedConfidence(Number(e.target.value))}
                    className="w-full accent-light-primary dark:accent-dark-primary cursor-pointer"
                  />
                  <div className="flex justify-between text-[11px] font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    <span>0% (Skeptical / No Conviction)</span>
                    <span>50% (Equivocal)</span>
                    <span>100% (Absolute Certainty)</span>
                  </div>
                </div>

                {/* Evidence backing level & Risk factors */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-body-sm font-semibold">Evidence Backing Level</label>
                    <select
                      value={evidenceBackingLevel}
                      onChange={(e) => setEvidenceBackingLevel(e.target.value)}
                      className="p-2.5 rounded-lg border border-light-outline-variant dark:border-dark-outline-variant bg-light-surface-container-low dark:bg-dark-surface-container text-body-md"
                    >
                      <option value="NONE">NONE — Strictly unverified commentary</option>
                      <option value="LOW">LOW — Partial or circumstantial references</option>
                      <option value="MODERATE">MODERATE — Unaudited disclosures / filings</option>
                      <option value="HIGH">HIGH — Fully audited statutory documentation</option>
                    </select>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-body-sm font-semibold">
                      Identified Downside Risk Factors
                    </label>
                    <div className="flex flex-wrap gap-1.5">
                      {[
                        'Execution Delay Risk',
                        'Margin Compression Risk',
                        'Regulatory Risk',
                        'Customer Concentration',
                        'Macro Headwind'
                      ].map((risk) => {
                        const active = identifiedRiskFactors.includes(risk);
                        return (
                          <button
                            type="button"
                            key={risk}
                            onClick={() => toggleRiskFactor(risk)}
                            className={`px-2.5 py-1 rounded text-[12px] font-mono border transition-all ${
                              active
                                ? 'bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary border-transparent'
                                : 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant text-light-on-surface-variant'
                            }`}
                          >
                            {risk} {active ? '✕' : '+'}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Written justification */}
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-body-sm font-semibold">
                      Structured Confidence Justification
                    </label>
                    <span className="text-[11px] font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                      {confidenceJustification.length} chars
                    </span>
                  </div>
                  <textarea
                    rows={3}
                    value={confidenceJustification}
                    onChange={(e) => setConfidenceJustification(e.target.value)}
                    placeholder="Articulate how available evidence, unstated boundary conditions, and identified downside risks connect to your stated confidence level..."
                    className="p-3 rounded-lg border border-light-outline-variant dark:border-dark-outline-variant bg-light-surface-container-low dark:bg-dark-surface-container text-body-md focus:border-light-primary dark:focus:border-dark-primary outline-none"
                  />
                  <p className="text-[11px] font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    💡 Transparent Rubric Anchor: Explicitly connecting evidence scarcity, missing parameters, and identified downside risks to restrained confidence scores higher.
                  </p>
                </div>
              </div>

              {submitError && (
                <div className="p-3.5 rounded-lg bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-300 text-body-sm border border-red-200 dark:border-red-800">
                  {submitError}
                </div>
              )}

              {/* Submit CTA */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-lg bg-light-surface-container dark:bg-dark-surface-container text-light-on-surface dark:text-dark-on-surface font-label text-label-md font-semibold hover:bg-light-surface-container-high"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-6 py-2.5 rounded-lg bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-md font-semibold hover:opacity-90 disabled:opacity-50 flex items-center gap-2 shadow-sm"
                >
                  {submitting ? (
                    <>
                      <span className="material-symbols-outlined animate-spin text-[18px]">
                        progress_activity
                      </span>
                      <span>Evaluating Rubric...</span>
                    </>
                  ) : (
                    <>
                      <span>Submit Evaluation for Rubric Scoring</span>
                      <span className="material-symbols-outlined text-[18px]">gavel</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
