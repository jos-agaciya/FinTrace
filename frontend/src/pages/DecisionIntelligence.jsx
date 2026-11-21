import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import AssessmentModal from '../components/AssessmentModal';

export default function DecisionIntelligence() {
  const [progress, setProgress] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [claims, setClaims] = useState({});
  const [loading, setLoading] = useState(true);

  // Assessment modal state
  const [modalStage, setModalStage] = useState(null); // 'BASELINE' | 'INDEPENDENT_TRANSFER' | null
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Tab state for history table
  const [activeHistoryTab, setActiveHistoryTab] = useState('assessments'); // 'assessments' | 'decisions'

  const loadData = useCallback(async () => {
    try {
      const [progData, decData, claimsList, assessData] = await Promise.all([
        api.getDashboardProgress(),
        api.getDecisions(),
        api.getClaims(),
        api.getAssessmentHistory('me')
      ]);

      setProgress(progData);
      setDecisions(decData || []);
      setAssessments(assessData || []);

      const cMap = {};
      (claimsList || []).forEach((c) => {
        cMap[c.id] = c;
      });
      setClaims(cMap);

      if (progData?.has_baseline && (progData?.has_independent_transfer || progData?.has_transfer)) {
        try {
          const comp = await api.compareAssessmentStages('me');
          setComparison(comp);
        } catch (e) {
          // Non-blocking
        }
      }
      setLoading(false);
    } catch (e) {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleOpenAssessment = (stage) => {
    setModalStage(stage);
    setIsModalOpen(true);
  };

  const handleAssessmentCompleted = async () => {
    await loadData();
  };

  const hasBaseline = Boolean(progress?.has_baseline);
  const hasTransfer = Boolean(progress?.has_independent_transfer || progress?.has_transfer);

  const baselineScore = progress?.baseline_score ?? progress?.baseline_total_score;
  const transferScore = progress?.transfer_score ?? progress?.latest_transfer_score;
  const delta = progress?.delta ?? progress?.percentage_point_delta;

  const overallScore = transferScore != null
    ? Math.round(transferScore)
    : (baselineScore != null ? Math.round(baselineScore) : null);

  const deltaText = delta != null
    ? `${delta >= 0 ? '+' : ''}${delta} pts from baseline (${Math.round(baselineScore)})`
    : (hasBaseline ? 'Baseline established' : 'Pending assessment');

  const dim = progress?.dimension_breakdown;

  // Normalized dimension scores
  // Note: Backend stores dimensions as 0-20 points (composite 100), or 0-100%
  const getNormScore = (val) => {
    if (val == null) return null;
    return val <= 20 ? Math.round(val * 5) : Math.round(val);
  };

  const dimensions = [
    {
      name: 'Evidence Scrutiny',
      rawScore: dim?.evidence_evaluation,
      score: getNormScore(dim?.evidence_evaluation),
      description: 'Depth of inquiry into primary regulatory filings, audited disclosures, and official reports.'
    },
    {
      name: 'Assumption Invalidation',
      rawScore: dim?.assumption_awareness ?? dim?.invalidation_sensitivity,
      score: getNormScore(dim?.assumption_awareness ?? dim?.invalidation_sensitivity),
      description: 'Capability to identify missing boundary conditions and counterfactual factors that negate a thesis.'
    },
    {
      name: 'Horizon Realism',
      rawScore: dim?.claim_specificity ?? dim?.horizon_calibration,
      score: getNormScore(dim?.claim_specificity ?? dim?.horizon_calibration),
      description: 'Detecting mismatched timelines between physical catalysts and forecasted target dates.'
    },
    {
      name: 'Source Provenance',
      rawScore: dim?.provenance_rigor ?? dim?.evidence_evaluation,
      score: getNormScore(dim?.provenance_rigor ?? dim?.evidence_evaluation),
      description: 'Differentiating statutory filings from social commentary, rumours, and promotional claims.'
    },
    {
      name: 'Cognitive Calibration',
      rawScore: dim?.confidence_calibration ?? dim?.epistemic_calibration,
      score: getNormScore(dim?.confidence_calibration ?? dim?.epistemic_calibration),
      description: 'Aligning subjective investment conviction with empirical evidence probability.'
    }
  ];

  return (
    <main className="flex-1 p-gutter-md lg:p-gutter-lg max-w-7xl w-full mx-auto flex flex-col gap-gutter-lg">
      {/* Page Title & Mission */}
      <div className="flex flex-col gap-gutter-xs">
        <h1 className="font-display text-display-lg-mobile lg:text-display-lg font-bold" data-design-text-token="display-lg">
          Decision Intelligence
        </h1>
        <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant" data-design-text-token="body-lg">
          Measure how effectively you evaluate financial information, audit claims against primary filings, and calibrate judgment.
        </p>
      </div>

      {/* 4 Summary Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-gutter-md items-stretch">
        <article className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col justify-between gap-gutter-sm shadow-sm">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Overall Calibration
            </span>
            <span className="material-symbols-outlined text-light-primary dark:text-dark-primary text-[20px]">
              psychology
            </span>
          </div>
          <p className="font-display text-headline-lg tabular-nums font-bold text-light-primary dark:text-dark-primary">
            {overallScore != null ? `${overallScore} / 100` : 'Unrated'}
          </p>
          <span className="font-mono text-mono-sm text-emerald-600 dark:text-emerald-400 font-semibold">
            {deltaText}
          </span>
        </article>

        <article className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col justify-between gap-gutter-sm shadow-sm">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Scrutiny Accuracy
            </span>
            <span className="material-symbols-outlined text-light-secondary dark:text-dark-secondary text-[20px]">
              verified
            </span>
          </div>
          <p className="font-display text-headline-lg tabular-nums font-bold">
            {dim?.evidence_evaluation != null ? `${getNormScore(dim.evidence_evaluation)}%` : '—'}
          </p>
          <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            {dim?.evidence_evaluation != null ? 'Empirical evidence metric' : 'Awaiting assessment'}
          </span>
        </article>

        <article className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col justify-between gap-gutter-sm shadow-sm">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Decisions Recorded
            </span>
            <span className="material-symbols-outlined text-light-primary dark:text-dark-primary text-[20px]">
              model_training
            </span>
          </div>
          <p className="font-display text-headline-lg tabular-nums font-bold">
            {decisions.length}
          </p>
          <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            {decisions.length > 0 ? `${decisions.length} sessions logged in database` : '0 sessions logged'}
          </span>
        </article>

        <article className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col justify-between gap-gutter-sm shadow-sm">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Assessment Status
            </span>
            <span className="material-symbols-outlined text-light-secondary dark:text-dark-secondary text-[20px]">
              military_tech
            </span>
          </div>
          <p className="font-display text-headline-lg font-bold">
            {hasTransfer ? 'Calibrated' : (hasBaseline ? 'Baseline' : 'Pending')}
          </p>
          <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            {progress?.status ? progress.status.replace(/_/g, ' ') : 'Not Started'}
          </span>
        </article>
      </section>

      {/* Comparative Learning Delta Banner (when both Stage 1 and 3 are completed) */}
      {comparison && (
        <section className="p-gutter-lg rounded-xl bg-gradient-to-r from-emerald-500/10 via-primary-500/10 to-transparent border border-emerald-500/30 dark:border-emerald-500/20 flex flex-col md:flex-row items-center justify-between gap-gutter-md">
          <div className="flex items-start gap-4">
            <span className="material-symbols-outlined text-[36px] text-emerald-600 dark:text-emerald-400 mt-1">
              verified_user
            </span>
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-headline text-headline-sm font-bold text-light-on-surface dark:text-dark-on-surface">
                  Cognitive Shift & Learning Progression Established
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                  {comparison.percentage_point_delta >= 0 ? '+' : ''}
                  {comparison.percentage_point_delta} pts Delta
                </span>
              </div>
              <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-2xl text-[14px]">
                {comparison.comparison_summary}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-light-outline-variant dark:border-dark-outline-variant pt-3 md:pt-0 md:pl-6">
            <div className="flex flex-col text-center">
              <span className="text-[11px] font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase">
                Stage 1 Baseline
              </span>
              <span className="font-display text-headline-md font-bold text-light-on-surface dark:text-dark-on-surface">
                {Math.round(comparison.baseline_score)}
              </span>
            </div>
            <span className="text-body-lg text-light-outline font-bold">→</span>
            <div className="flex flex-col text-center">
              <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold uppercase">
                Stage 3 Transfer
              </span>
              <span className="font-display text-headline-md font-bold text-emerald-600 dark:text-emerald-400">
                {Math.round(comparison.latest_transfer_score)}
              </span>
            </div>
          </div>
        </section>
      )}

      {/* Progression Architecture (3 Stages with visible action buttons) */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="font-headline text-headline-md font-bold">
              Baseline → Assisted Practice → Independent Assessment
            </h2>
            <p className="text-body-sm text-light-on-surface-variant dark:text-dark-on-surface-variant mt-0.5">
              Three-stage pedagogical progression measuring investor bias mitigation and independent cognitive rigor.
            </p>
          </div>
          <span className="font-mono text-mono-sm px-2.5 py-1 rounded bg-light-surface-container dark:bg-dark-surface text-light-on-surface-variant dark:text-dark-on-surface-variant">
            {hasTransfer ? 'All Stages Complete' : (hasBaseline ? 'Stage 1 Complete · Stage 2/3 Active' : 'Stage 1 Pending')}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md">
          {/* Stage 1: Baseline Onboarding */}
          <div
            className={`p-gutter-md rounded-xl border flex flex-col justify-between gap-4 transition-all ${
              hasBaseline
                ? 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant'
                : 'bg-light-surface-container dark:bg-dark-surface-container-high border-2 border-amber-500/60 dark:border-amber-400/60 shadow-sm'
            }`}
          >
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-mono-sm text-amber-600 dark:text-amber-400 uppercase font-bold text-[11px] flex items-center gap-1">
                  <span>Stage 1</span>
                  {hasBaseline && <span className="material-symbols-outlined text-[14px]">check_circle</span>}
                </span>
                <span className="font-mono text-mono-sm font-bold">
                  {baselineScore != null ? `${Math.round(baselineScore)} / 100` : 'Pending'}
                </span>
              </div>
              <h3 className="font-title text-title-md font-semibold text-light-on-surface dark:text-dark-on-surface">
                Baseline Onboarding
              </h3>
              <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                Initial heuristic audit measuring cognitive biases and acceptance of unchecked claims before receiving AI guidance.
              </p>
            </div>

            <div className="pt-2 border-t border-light-outline-variant/60 dark:border-dark-outline-variant/60">
              {hasBaseline ? (
                <button
                  type="button"
                  onClick={() => handleOpenAssessment('BASELINE')}
                  className="w-full py-2 px-3 rounded-lg bg-light-surface-container dark:bg-dark-surface-container border border-light-outline-variant hover:border-light-primary text-light-primary dark:text-dark-primary font-label text-label-sm font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <span className="material-symbols-outlined text-[16px]">visibility</span>
                  <span>Review / Retake Baseline</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleOpenAssessment('BASELINE')}
                  className="w-full py-2 px-3 rounded-lg bg-amber-600 text-white dark:bg-amber-500 dark:text-black font-label text-label-md font-semibold hover:opacity-90 flex items-center justify-center gap-1.5 shadow-sm transition-transform active:scale-95"
                >
                  <span className="material-symbols-outlined text-[18px]">play_arrow</span>
                  <span>Start Baseline Assessment</span>
                </button>
              )}
            </div>
          </div>

          {/* Stage 2: Assisted Scrutiny (7 decisions) */}
          <div className="p-gutter-md rounded-xl bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col justify-between gap-4">
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-mono-sm text-light-secondary dark:text-dark-secondary uppercase font-bold text-[11px] flex items-center gap-1">
                  <span>Stage 2</span>
                  {decisions.length > 0 && <span className="material-symbols-outlined text-[14px]">check_circle</span>}
                </span>
                <span className="font-mono text-mono-sm font-bold text-light-secondary dark:text-dark-secondary">
                  {decisions.length > 0 ? `${decisions.length} Decisions` : 'Pending'}
                </span>
              </div>
              <h3 className="font-title text-title-md font-semibold text-light-on-surface dark:text-dark-on-surface">
                Assisted Scrutiny
              </h3>
              <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                Interactive scenario forking highlighting supply bottlenecks and regulatory dates in Virtual Decision Lab.
              </p>
            </div>

            <div className="pt-2 border-t border-light-outline-variant/60 dark:border-dark-outline-variant/60">
              <Link
                to="/virtual-decision-lab"
                className="w-full py-2 px-3 rounded-lg bg-light-surface-container dark:bg-dark-surface-container border border-light-outline-variant hover:border-light-secondary text-light-secondary dark:text-dark-secondary font-label text-label-sm font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <span>Practice in Decision Lab</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </Link>
            </div>
          </div>

          {/* Stage 3: Independent Assessment */}
          <div
            className={`p-gutter-md rounded-xl border flex flex-col justify-between gap-4 transition-all ${
              hasTransfer
                ? 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant'
                : hasBaseline
                ? 'bg-light-surface-container dark:bg-dark-surface-container-high border-2 border-light-primary dark:border-dark-primary shadow-sm'
                : 'bg-light-surface-container-low dark:bg-dark-surface-container opacity-60 border-light-outline-variant dark:border-dark-outline-variant'
            }`}
          >
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-mono-sm text-light-primary dark:text-dark-primary uppercase font-bold text-[11px] flex items-center gap-1">
                  <span>Stage 3</span>
                  {hasTransfer ? (
                    <span className="material-symbols-outlined text-[14px]">check_circle</span>
                  ) : hasBaseline ? (
                    <span className="material-symbols-outlined text-[14px]">lock_open</span>
                  ) : (
                    <span className="material-symbols-outlined text-[14px]">lock</span>
                  )}
                </span>
                <span className="font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary">
                  {transferScore != null ? `${Math.round(transferScore)} / 100` : (hasBaseline ? 'Ready' : 'Locked')}
                </span>
              </div>
              <h3 className="font-title text-title-md font-semibold text-light-on-surface dark:text-dark-on-surface">
                Independent Assessment
              </h3>
              <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                User autonomously challenges premises and tests invalidation conditions on a counterfactual claim without AI assistance.
              </p>
            </div>

            <div className="pt-2 border-t border-light-outline-variant/60 dark:border-dark-outline-variant/60">
              {hasTransfer ? (
                <button
                  type="button"
                  onClick={() => handleOpenAssessment('INDEPENDENT_TRANSFER')}
                  className="w-full py-2 px-3 rounded-lg bg-light-surface-container dark:bg-dark-surface-container border border-light-outline-variant hover:border-light-primary text-light-primary dark:text-dark-primary font-label text-label-sm font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <span className="material-symbols-outlined text-[16px]">visibility</span>
                  <span>Review / Retake Assessment</span>
                </button>
              ) : hasBaseline ? (
                <button
                  type="button"
                  onClick={() => handleOpenAssessment('INDEPENDENT_TRANSFER')}
                  className="w-full py-2 px-3 rounded-lg bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-md font-semibold hover:opacity-90 flex items-center justify-center gap-1.5 shadow-sm transition-transform active:scale-95"
                >
                  <span className="material-symbols-outlined text-[18px]">rocket_launch</span>
                  <span>Start Independent Assessment</span>
                </button>
              ) : (
                <button
                  disabled
                  type="button"
                  className="w-full py-2 px-3 rounded-lg bg-light-surface-container dark:bg-dark-surface-container text-light-outline dark:text-dark-outline cursor-not-allowed font-label text-label-sm font-medium flex items-center justify-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">lock</span>
                  <span>Locked (Complete Stage 1)</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Five Assessment Dimensions */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="font-headline text-headline-md font-bold">Five Assessment Dimensions</h2>
          <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
            {dim ? 'GROUNDED RUBRIC SCORES' : 'AWAITING EVALUATION SESSION'}
          </span>
        </div>

        <div className="flex flex-col gap-gutter-md">
          {dimensions.map((d) => (
            <div key={d.name} className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-body-md">
                <span className="font-semibold text-light-on-surface dark:text-dark-on-surface">
                  {d.name}
                </span>
                <span className="font-mono text-mono-sm font-bold tabular-nums">
                  {d.score != null ? `${d.score} / 100` : '—'}
                </span>
              </div>
              <div className="w-full bg-light-surface-container dark:bg-dark-surface-container h-2 rounded-full overflow-hidden">
                <div
                  className="bg-light-primary dark:bg-dark-primary h-full rounded-full transition-all duration-500"
                  style={{ width: `${d.score != null ? d.score : 0}%` }}
                />
              </div>
              <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
                {d.description}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Evaluation Records & Decision History Tabs */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-light-outline-variant dark:border-dark-outline-variant pb-3">
          <div className="flex items-center gap-2">
            <h2 className="font-headline text-headline-md font-bold">Historical Records</h2>
            <div className="flex items-center bg-light-surface-container dark:bg-dark-surface rounded-lg p-1">
              <button
                type="button"
                onClick={() => setActiveHistoryTab('assessments')}
                className={`px-3 py-1 rounded text-label-sm font-semibold transition-colors ${
                  activeHistoryTab === 'assessments'
                    ? 'bg-light-surface dark:bg-dark-surface-container text-light-primary dark:text-dark-primary shadow-sm'
                    : 'text-light-on-surface-variant hover:text-light-on-surface'
                }`}
              >
                Assessments ({assessments.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveHistoryTab('decisions')}
                className={`px-3 py-1 rounded text-label-sm font-semibold transition-colors ${
                  activeHistoryTab === 'decisions'
                    ? 'bg-light-surface dark:bg-dark-surface-container text-light-primary dark:text-dark-primary shadow-sm'
                    : 'text-light-on-surface-variant hover:text-light-on-surface'
                }`}
              >
                Assisted Decisions ({decisions.length})
              </button>
            </div>
          </div>

          <Link
            to="/virtual-decision-lab"
            className="text-label-sm font-semibold text-light-primary dark:text-dark-primary hover:underline flex items-center gap-1"
          >
            <span>Practice in Decision Lab</span>
            <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
          </Link>
        </div>

        {activeHistoryTab === 'assessments' ? (
          assessments.length > 0 ? (
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-light-outline-variant dark:border-dark-outline-variant text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider">
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Stage</th>
                    <th className="py-2.5 px-3">Target Claim</th>
                    <th className="py-2.5 px-3">Total Score</th>
                    <th className="py-2.5 px-3">Evidence Scrutiny</th>
                    <th className="py-2.5 px-3">Confidence Justification</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-light-outline-variant/60 dark:divide-dark-outline-variant/60 text-body-md">
                  {assessments.map((a) => {
                    const claimInfo = claims[a.claim_id];
                    const claimName = claimInfo ? `${claimInfo.company || claimInfo.ticker} (${claimInfo.ticker})` : `Claim ${a.claim_id.slice(0, 8)}`;
                    const dateStr = a.created_at ? new Date(a.created_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Recent';
                    const isBase = a.assessment_stage === 'BASELINE';

                    return (
                      <tr key={a.id} className="hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container transition-colors">
                        <td className="py-3 px-3 font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                          {dateStr}
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full font-mono text-[11px] font-semibold ${
                              isBase
                                ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
                                : 'bg-primary-100 text-light-primary dark:bg-primary-900/40 dark:text-dark-primary'
                            }`}
                          >
                            {a.assessment_stage}
                          </span>
                        </td>
                        <td className="py-3 px-3 font-semibold text-light-on-surface dark:text-dark-on-surface">
                          {claimName}
                        </td>
                        <td className="py-3 px-3 font-mono text-mono-md font-bold text-light-primary dark:text-dark-primary">
                          {Math.round(a.total_score)} / 100
                        </td>
                        <td className="py-3 px-3 font-mono text-mono-sm">
                          {a.score_evidence_eval} / 20
                        </td>
                        <td className="py-3 px-3 font-mono text-mono-sm">
                          {a.score_confidence_calibration} / 20
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="w-full py-10 flex flex-col items-center justify-center text-center p-6 gap-3">
              <span className="material-symbols-outlined text-[36px] text-light-outline dark:text-dark-outline">
                assignment_turned_in
              </span>
              <p className="font-headline text-headline-sm font-bold text-light-on-surface dark:text-dark-on-surface">
                No assessment evaluations recorded yet
              </p>
              <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-md text-[13px]">
                Establish your cognitive baseline by starting Stage 1 Baseline Onboarding.
              </p>
              <button
                type="button"
                onClick={() => handleOpenAssessment('BASELINE')}
                className="mt-2 px-5 py-2 rounded-full bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-md font-semibold hover:opacity-90 shadow-sm"
              >
                Start Baseline Assessment
              </button>
            </div>
          )
        ) : decisions.length > 0 ? (
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-light-outline-variant dark:border-dark-outline-variant text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Target Claim</th>
                  <th className="py-2.5 px-3">Initial Thesis</th>
                  <th className="py-2.5 px-3">Conviction Shift</th>
                  <th className="py-2.5 px-3">Reasoning Shift</th>
                  <th className="py-2.5 px-3">Sensitivity Impact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-light-outline-variant/60 dark:divide-dark-outline-variant/60 text-body-md">
                {decisions.map((s) => {
                  const claimInfo = claims[s.claim_id];
                  const claimName = claimInfo ? `${claimInfo.company || claimInfo.ticker} (${claimInfo.ticker})` : `Claim ${s.claim_id.slice(0, 8)}`;
                  const dateStr = s.created_at ? new Date(s.created_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Recent';
                  const shiftType = s.sensitivity_summary?.reasoning_shift_type || 'RECORDED';

                  return (
                    <tr key={s.id} className="hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container transition-colors">
                      <td className="py-3 px-3 font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                        {dateStr}
                      </td>
                      <td className="py-3 px-3 font-semibold text-light-on-surface dark:text-dark-on-surface">
                        {claimName}
                      </td>
                      <td className="py-3 px-3 text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-xs truncate">
                        {s.initial_thesis}
                      </td>
                      <td className="py-3 px-3 font-mono text-mono-sm">
                        {s.initial_confidence}% {s.revised_confidence != null ? `→ ${s.revised_confidence}%` : '(Initial)'}
                      </td>
                      <td className="py-3 px-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full font-mono text-[11px] bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container font-semibold">
                          {shiftType.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-sm">
                        {s.sensitivity_summary?.shift_explanation || s.reason_for_change || 'Initial baseline recorded'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="w-full py-10 flex flex-col items-center justify-center text-center p-6 gap-3">
            <span className="material-symbols-outlined text-[36px] text-light-outline dark:text-dark-outline">
              history_toggle_off
            </span>
            <p className="font-headline text-headline-sm font-bold text-light-on-surface dark:text-dark-on-surface">
              No decision sessions logged yet
            </p>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-md text-[13px]">
              Step into the Virtual Decision Lab to record your initial hypotheses, evaluate filed disclosures, and test your conviction.
            </p>
            <Link
              to="/virtual-decision-lab"
              className="mt-2 px-5 py-2 rounded-full bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-md font-semibold hover:opacity-90"
            >
              Start Practice Session
            </Link>
          </div>
        )}
      </section>

      {/* Assessment Modal for Stage 1 Baseline & Stage 3 Independent Transfer */}
      <AssessmentModal
        stage={modalStage || 'BASELINE'}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCompleted={handleAssessmentCompleted}
      />
    </main>
  );
}
