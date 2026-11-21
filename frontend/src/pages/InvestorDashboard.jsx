import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function InvestorDashboard() {
  const [currentUser, setCurrentUser] = useState(() => api.getCurrentUser());
  const [overview, setOverview] = useState({
    total_claims_submitted: 0,
    total_claims_analyzed: 0,
    total_evidence_records: 0,
    total_decisions_recorded: 0,
    recent_claims: [],
    recent_decisions: []
  });
  const [progress, setProgress] = useState(null);
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    async function loadDashboardData() {
      try {
        const [userData, ovData, progData, claimsData] = await Promise.all([
          api.getMe(),
          api.getDashboardOverview(),
          api.getDashboardProgress(),
          api.getClaims()
        ]);
        if (isMounted) {
          if (userData) setCurrentUser(userData);
          if (ovData) setOverview(ovData);
          if (progData) setProgress(progData);
          if (claimsData) setClaims(claimsData);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) setLoading(false);
      }
    }
    loadDashboardData();
    return () => {
      isMounted = false;
    };
  }, []);

  const userName = currentUser?.name ? currentUser.name.split(' ')[0] : 'Investor';

  const scoreDisplay = () => {
    if (progress?.has_transfer && progress.transfer_score !== null) {
      return `${Math.round(progress.transfer_score)} / 100`;
    }
    if (progress?.has_baseline && progress.baseline_score !== null) {
      return `${Math.round(progress.baseline_score)} / 100`;
    }
    return 'Unrated';
  };

  const deltaDisplay = () => {
    if (progress?.has_transfer && progress?.delta !== null) {
      const sign = progress.delta >= 0 ? '+' : '';
      return `${sign}${progress.delta} vs baseline`;
    }
    if (progress?.has_baseline) {
      return 'Baseline established';
    }
    return 'Complete assessment to calibrate';
  };

  return (
    <main className="relative flex-1 p-gutter-md lg:p-gutter-lg max-w-7xl w-full mx-auto flex flex-col gap-gutter-lg z-10 pb-16">
      {/* Dashboard Ambient Glow Highlights */}
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden z-0">
        <div className="absolute -top-24 left-1/4 w-[28rem] h-[28rem] rounded-full bg-light-primary/20 dark:bg-dark-primary/15 blur-3xl" />
        <div className="absolute top-1/3 right-12 w-96 h-96 rounded-full bg-light-secondary/25 dark:bg-dark-secondary/15 blur-3xl" />
      </div>

      {/* Liquid Glass Welcome Panel */}
      <section className="relative z-10 liquid-glass-surface rounded-3xl p-6 lg:p-8 flex flex-col md:flex-row md:items-center justify-between gap-gutter-md">
        <div className="flex flex-col gap-gutter-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full font-mono text-mono-sm bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container font-semibold shadow-xs">
              LIVE EVIDENCE ENGINE
            </span>
            <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
              No trade execution · Epistemic decision intelligence
            </span>
          </div>
          <h1 className="font-display text-display-lg-mobile lg:text-display-lg text-light-on-surface dark:text-dark-on-surface font-extrabold tracking-tight mt-1">
            Good evening, {userName}
          </h1>
          <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-xl">
            Your investor decision intelligence overview. Examine empirical evidence and calibrate conviction without noise.
          </p>
        </div>
        <Link
          to="/analyse-claim"
          className="inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-full bg-gradient-to-r from-light-primary to-sky-400 dark:from-dark-primary dark:to-purple-500 text-light-on-primary dark:text-dark-on-primary font-label text-label-lg font-bold shadow-lg shadow-light-primary/25 dark:shadow-dark-primary/30 hover:scale-[1.02] active:scale-[0.98] transition-all duration-state-change shrink-0"
        >
          <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
            query_stats
          </span>
          <span>Analyse New Claim</span>
        </Link>
      </section>

      {/* 4 Liquid Glass Metric Cards */}
      <section aria-label="Key Metrics" className="relative z-10 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-gutter-md items-stretch">
        <article className="liquid-glass-surface rounded-2xl p-6 flex flex-col justify-between gap-4 group hover:-translate-y-1 hover:shadow-xl transition-all duration-300">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant font-medium">
              Total Claims Analysed
            </span>
            <div className="w-10 h-10 rounded-xl glass-nested flex items-center justify-center text-light-primary dark:text-dark-primary shadow-xs">
              <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                fact_check
              </span>
            </div>
          </div>
          <p className="font-display text-4xl tabular-nums font-extrabold text-light-on-surface dark:text-dark-on-surface tracking-tight">
            {overview.total_claims_submitted}
          </p>
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full font-mono text-[11px] bg-light-primary-container/70 dark:bg-dark-primary-container/50 text-light-on-primary-container dark:text-dark-on-primary-container font-semibold">
              {overview.total_claims_submitted > 0 ? `${overview.total_claims_submitted} recorded` : 'No claims yet'}
            </span>
          </div>
        </article>

        <article className="liquid-glass-surface rounded-2xl p-6 flex flex-col justify-between gap-4 group hover:-translate-y-1 hover:shadow-xl transition-all duration-300">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant font-medium">
              Reports Generated
            </span>
            <div className="w-10 h-10 rounded-xl glass-nested flex items-center justify-center text-light-secondary dark:text-dark-on-primary-container shadow-xs">
              <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                description
              </span>
            </div>
          </div>
          <p className="font-display text-4xl tabular-nums font-extrabold text-light-on-surface dark:text-dark-on-surface tracking-tight">
            {overview.total_claims_analyzed}
          </p>
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full font-mono text-[11px] bg-amber-500/15 text-amber-600 dark:text-amber-400 font-semibold">
              {overview.total_claims_analyzed > 0 ? `${overview.total_claims_analyzed} verified analyses` : '0 analyses'}
            </span>
          </div>
        </article>

        <article className="liquid-glass-surface rounded-2xl p-6 flex flex-col justify-between gap-4 group hover:-translate-y-1 hover:shadow-xl transition-all duration-300">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant font-medium">
              Calibration Score
            </span>
            <div className="w-10 h-10 rounded-xl glass-nested flex items-center justify-center text-light-primary dark:text-dark-primary shadow-xs">
              <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                psychology
              </span>
            </div>
          </div>
          <p className="font-display text-4xl tabular-nums font-extrabold text-light-primary dark:text-dark-primary tracking-tight">
            {scoreDisplay()}
          </p>
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full font-mono text-[11px] bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-bold">
              {deltaDisplay()}
            </span>
          </div>
        </article>

        <article className="liquid-glass-surface rounded-2xl p-6 flex flex-col justify-between gap-4 group hover:-translate-y-1 hover:shadow-xl transition-all duration-300">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant font-medium">
              Decisions Recorded
            </span>
            <div className="w-10 h-10 rounded-xl glass-nested flex items-center justify-center text-light-secondary dark:text-dark-on-primary-container shadow-xs">
              <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                science
              </span>
            </div>
          </div>
          <p className="font-display text-4xl tabular-nums font-extrabold text-light-on-surface dark:text-dark-on-surface tracking-tight">
            {overview.total_decisions_recorded}
          </p>
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full font-mono text-[11px] bg-purple-500/15 text-purple-600 dark:text-purple-400 font-semibold">
              Virtual Decision Lab sessions
            </span>
          </div>
        </article>
      </section>

      {/* Chart + Learning Insights Row */}
      <section className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-gutter-lg items-stretch">
        {/* Decision Evaluation Progress Chart */}
        <article className="lg:col-span-8 liquid-glass-surface rounded-3xl p-6 lg:p-8 flex flex-col justify-between gap-gutter-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-gutter-sm">
            <div>
              <h2 className="font-headline text-headline-md font-bold text-light-on-surface dark:text-dark-on-surface">
                Decision Evaluation Progress
              </h2>
              <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] mt-0.5">
                Progression across baseline, AI-assisted practice, and independent assessment (0–100 scale).
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-label-sm">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full glass-nested">
                <span className="w-2.5 h-2.5 rounded-full bg-light-outline dark:bg-dark-outline" />
                <span className="text-[12px] font-medium">Baseline</span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full glass-nested">
                <span className="w-2.5 h-2.5 rounded-full bg-light-secondary dark:bg-dark-secondary" />
                <span className="text-[12px] font-medium">Assisted</span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full glass-nested">
                <span className="w-2.5 h-2.5 rounded-full bg-light-primary dark:bg-dark-primary shadow-xs" />
                <span className="text-[12px] font-bold text-light-primary dark:text-dark-primary">Independent</span>
              </span>
            </div>
          </div>

          {progress && (progress.has_baseline || progress.has_transfer) ? (
            <div className="w-full overflow-x-auto py-2">
              <svg viewBox="0 0 680 230" className="w-full h-60 text-light-on-surface-variant dark:text-dark-on-surface-variant" role="img" aria-label="Decision evaluation progress chart">
                <defs>
                  <linearGradient id="curveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="currentColor" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="currentColor" stopOpacity="0.0" />
                  </linearGradient>
                  <filter id="nodeGlow" x="-50%" y="-50%" width="200%" height="200%">
                    <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="currentColor" floodOpacity="0.4" />
                  </filter>
                </defs>

                <g stroke="currentColor" strokeOpacity="0.12" strokeDasharray="4 4">
                  <line x1="48" y1="30" x2="650" y2="30" />
                  <line x1="48" y1="75" x2="650" y2="75" />
                  <line x1="48" y1="120" x2="650" y2="120" />
                  <line x1="48" y1="165" x2="650" y2="165" />
                </g>

                <g fill="currentColor" fontSize="11" fontFamily="JetBrains Mono, monospace" opacity="0.75">
                  <text x="12" y="34">100</text>
                  <text x="18" y="79">75</text>
                  <text x="18" y="124">50</text>
                  <text x="18" y="169">25</text>
                  <text x="85" y="206">Baseline</text>
                  <text x="450" y="206">Independent Transfer</text>
                </g>

                {progress.has_baseline && progress.has_transfer && (
                  <>
                    <polygon
                      fill="url(#curveGradient)"
                      className="text-light-primary dark:text-dark-primary"
                      points={`120,${200 - (progress.baseline_score * 1.7)} 520,${200 - (progress.transfer_score * 1.7)} 520,200 120,200`}
                    />
                    <polyline
                      fill="none"
                      className="stroke-light-primary dark:stroke-dark-primary"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      points={`120,${200 - (progress.baseline_score * 1.7)} 520,${200 - (progress.transfer_score * 1.7)}`}
                    />
                    <circle cx="120" cy={200 - (progress.baseline_score * 1.7)} r="6" className="fill-light-outline dark:fill-dark-outline" />
                    <circle cx="520" cy={200 - (progress.transfer_score * 1.7)} r="7" className="fill-light-primary dark:fill-dark-primary" filter="url(#nodeGlow)" />
                  </>
                )}
              </svg>
            </div>
          ) : (
            <div className="w-full py-12 rounded-2xl glass-nested flex flex-col items-center justify-center text-center p-6 gap-3">
              <span className="material-symbols-outlined text-[36px] text-light-outline dark:text-dark-outline">
                insights
              </span>
              <p className="font-headline text-headline-sm font-bold text-light-on-surface dark:text-dark-on-surface">
                No evaluation sessions recorded
              </p>
              <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-md text-[13px]">
                Complete your baseline assessment or practice in the Virtual Decision Lab to generate authentic calibration trajectories.
              </p>
              <Link
                to="/virtual-decision-lab"
                className="mt-2 px-5 py-2 rounded-full bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-md font-semibold hover:opacity-90"
              >
                Launch Decision Lab
              </Link>
            </div>
          )}
        </article>

        {/* Learning Insights Panel */}
        <article className="lg:col-span-4 liquid-glass-surface rounded-3xl p-6 lg:p-8 flex flex-col justify-between gap-gutter-md">
          <div className="flex flex-col gap-gutter-sm">
            <div className="flex items-center justify-between">
              <h2 className="font-headline text-headline-md font-bold text-light-on-surface dark:text-dark-on-surface">
                Learning Insights
              </h2>
              <span className="font-mono text-mono-sm px-2.5 py-0.5 rounded-full bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container font-semibold text-[11px]">
                CALIBRATION
              </span>
            </div>
            
            {progress?.summary ? (
              <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] leading-relaxed">
                {progress.summary}
              </p>
            ) : (
              <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] leading-relaxed">
                Identify unstated assumptions and test alternative interpretation forks to build robust epistemic vigilance.
              </p>
            )}

            <div className="p-4 rounded-2xl glass-nested flex flex-col gap-1">
              <span className="font-label text-label-sm text-light-primary dark:text-dark-primary font-bold uppercase tracking-wider text-[11px]">
                EVALUATION STATUS
              </span>
              <span className="font-title text-title-md font-extrabold text-light-on-surface dark:text-dark-on-surface">
                {progress?.status ? progress.status.replace(/_/g, ' ') : 'PENDING ASSESSMENT'}
              </span>
            </div>

            <div className="p-4 rounded-2xl glass-nested flex flex-col gap-1">
              <span className="inline-block w-fit px-2.5 py-0.5 rounded-full font-label text-label-sm bg-warning/20 text-warning font-bold text-[11px]">
                DECISION RECORDS
              </span>
              <span className="font-title text-title-md font-extrabold text-light-on-surface dark:text-dark-on-surface">
                {overview.total_decisions_recorded} Persistent Decisions
              </span>
            </div>
          </div>

          <Link
            to="/decision-intelligence"
            className="w-full py-2.5 rounded-full glass-nested text-light-primary dark:text-dark-primary font-label text-label-lg font-bold text-center hover:bg-light-primary hover:text-white dark:hover:bg-dark-primary dark:hover:text-dark-on-primary transition-all duration-state-change flex items-center justify-center gap-2"
          >
            <span>Inspect full assessment</span>
            <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
              arrow_forward
            </span>
          </Link>
        </article>
      </section>

      {/* Quick Actions */}
      <section aria-label="Quick Actions" className="relative z-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-gutter-md items-stretch">
        <Link
          to="/analyse-claim"
          className="liquid-glass-surface rounded-2xl p-5 hover:-translate-y-1 hover:shadow-xl transition-all duration-300 flex items-center gap-4 group"
        >
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-light-primary-container to-white dark:from-dark-primary-container dark:to-purple-900/40 flex items-center justify-center text-light-on-primary-container dark:text-dark-on-primary-container shrink-0 group-hover:scale-105 transition-transform shadow-xs">
            <span className="material-symbols-outlined text-[22px]" aria-hidden="true">query_stats</span>
          </div>
          <div>
            <p className="font-title text-title-md font-bold text-light-on-surface dark:text-dark-on-surface">Analyse a Claim</p>
            <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">New claim check</p>
          </div>
        </Link>

        <Link
          to="/evidence-centre"
          className="liquid-glass-surface rounded-2xl p-5 hover:-translate-y-1 hover:shadow-xl transition-all duration-300 flex items-center gap-4 group"
        >
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-light-primary-container to-white dark:from-dark-primary-container dark:to-purple-900/40 flex items-center justify-center text-light-on-primary-container dark:text-dark-on-primary-container shrink-0 group-hover:scale-105 transition-transform shadow-xs">
            <span className="material-symbols-outlined text-[22px]" aria-hidden="true">fact_check</span>
          </div>
          <div>
            <p className="font-title text-title-md font-bold text-light-on-surface dark:text-dark-on-surface">Browse Evidence</p>
            <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">Trace filings</p>
          </div>
        </Link>

        <Link
          to="/virtual-decision-lab"
          className="liquid-glass-surface rounded-2xl p-5 hover:-translate-y-1 hover:shadow-xl transition-all duration-300 flex items-center gap-4 group"
        >
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-light-primary-container to-white dark:from-dark-primary-container dark:to-purple-900/40 flex items-center justify-center text-light-on-primary-container dark:text-dark-on-primary-container shrink-0 group-hover:scale-105 transition-transform shadow-xs">
            <span className="material-symbols-outlined text-[22px]" aria-hidden="true">science</span>
          </div>
          <div>
            <p className="font-title text-title-md font-bold text-light-on-surface dark:text-dark-on-surface">Continue Learning</p>
            <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">Log rationale</p>
          </div>
        </Link>

        <Link
          to="/decision-intelligence"
          className="liquid-glass-surface rounded-2xl p-5 hover:-translate-y-1 hover:shadow-xl transition-all duration-300 flex items-center gap-4 group"
        >
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-light-primary-container to-white dark:from-dark-primary-container dark:to-purple-900/40 flex items-center justify-center text-light-on-primary-container dark:text-dark-on-primary-container shrink-0 group-hover:scale-105 transition-transform shadow-xs">
            <span className="material-symbols-outlined text-[22px]" aria-hidden="true">psychology</span>
          </div>
          <div>
            <p className="font-title text-title-md font-bold text-light-on-surface dark:text-dark-on-surface">Skill Analytics</p>
            <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">5 dimensions</p>
          </div>
        </Link>
      </section>

      {/* Recent Activity Table */}
      <section className="relative z-10 liquid-glass-surface rounded-3xl p-6 lg:p-8 flex flex-col gap-gutter-md">
        <div className="flex items-center justify-between">
          <h2 className="font-headline text-headline-md font-bold text-light-on-surface dark:text-dark-on-surface">
            Recent Activity
          </h2>
          <span className="font-mono text-mono-sm px-3 py-1 rounded-full bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container font-semibold text-[11px]">
            PERSISTED CLAIMS
          </span>
        </div>

        {claims.length > 0 ? (
          <div className="w-full overflow-x-auto rounded-2xl glass-nested">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-light-outline-variant/60 dark:border-dark-outline-variant/60 text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-4">Claim / Ticker</th>
                  <th className="py-3 px-4">Validation</th>
                  <th className="py-3 px-4">Coverage</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-light-outline-variant/40 dark:divide-dark-outline-variant/40 text-body-md">
                {claims.map((claim) => (
                  <tr key={claim.id} className="hover:bg-light-primary-container/20 dark:hover:bg-dark-surface-container/60 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="flex flex-col">
                        <span className="font-bold text-light-on-surface dark:text-dark-on-surface">
                          {claim.company} ({claim.ticker})
                        </span>
                        <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant truncate max-w-xs text-[12px]">
                          {claim.statement}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-3 py-0.5 rounded-full text-label-sm font-semibold text-[12px] ${
                        claim.validationStatus === 'Completed'
                          ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                          : claim.validationStatus === 'Needs Verification'
                          ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                          : 'bg-rose-500/15 text-rose-600 dark:text-rose-400'
                      }`}>
                        {claim.validationStatus}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-mono-sm tabular-nums font-semibold">
                      {claim.evidenceCoverage}%
                    </td>
                    <td className="py-3.5 px-4 font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
                      {claim.date}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/claim-analysis-report?id=${claim.id}`}
                        className="inline-flex items-center px-3 py-1 rounded-full font-label text-label-sm text-light-primary dark:text-dark-primary font-bold hover:bg-light-primary/10 dark:hover:bg-dark-primary/10 transition-colors"
                      >
                        View Report
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="w-full py-12 rounded-2xl glass-nested flex flex-col items-center justify-center text-center p-6 gap-3">
            <span className="material-symbols-outlined text-[36px] text-light-outline dark:text-dark-outline">
              history_edu
            </span>
            <p className="font-headline text-headline-sm font-bold text-light-on-surface dark:text-dark-on-surface">
              No claims submitted yet
            </p>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-md text-[13px]">
              Submit your first financial claim to parse catalysts, verify official regulatory disclosures, and uncover unstated assumptions.
            </p>
            <Link
              to="/analyse-claim"
              className="mt-2 px-5 py-2 rounded-full bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-md font-semibold hover:opacity-90"
            >
              Analyse a Claim
            </Link>
          </div>
        )}
      </section>
    </main>
  );
}
