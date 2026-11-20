import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { api, SYNTHETIC_CLAIMS } from '../services/api';

function generateReportText(claim) {
  const exportDate = new Date().toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short'
  });

  const missingConditions = claim.breakdown?.missingConditions || [
    'High-voltage transformer delivery lead times exceed 84 weeks',
    'Raw copper and grain-oriented electrical steel price surges',
    'FERC interconnection queue backlog deferrals'
  ];

  const interpretations = (claim.interpretations || []).map((fork, idx) => {
    const forkLetter = String.fromCharCode(65 + idx);
    return `[Fork ${forkLetter}] ${fork.fork}\n  Stance: ${fork.stance}\n  Rationale: ${fork.rationale}\n  Source: ${fork.source || 'AI-GENERATED FORK'}`;
  }).join('\n\n');

  const supportingEvidence = (claim.supportingEvidence || []).map((ev, idx) => {
    return `[Evidence ${idx + 1}] ${ev.title}\n  - ID: ${ev.id}\n  - Source: ${ev.source || 'Direct Record'} (${ev.date || 'Undated'})\n  - Provenance: ${ev.provenance || 'SYNTHETIC'}${ev.url ? `\n  - Reference URL: ${ev.url}` : ''}\n  - Excerpt:\n    "${ev.excerpt}"`;
  }).join('\n\n');

  const contradictoryEvidence = (claim.contradictoryEvidence || []).map((ev, idx) => {
    return `[Contradictory / Risk Item ${idx + 1}] ${ev.title}\n  - ID: ${ev.id}\n  - Provenance: ${ev.provenance || 'SYNTHETIC'}\n  - Excerpt:\n    "${ev.excerpt}"`;
  }).join('\n\n');

  return `================================================================================
FINTRACE CLAIM ANALYSIS REPORT
Decision Intelligence & Evidence Verification
================================================================================

COMPANY / CLAIM NAME: ${claim.company} (${claim.ticker})
DATE OF CLAIM: ${claim.date}
VERIFICATION STATUS: ${claim.validationStatus}
PROVENANCE STATUS: ${claim.completeness?.provenanceStatus || 'USER-PROVIDED'}

--------------------------------------------------------------------------------
OVERVIEW & CLAIM SUMMARY
--------------------------------------------------------------------------------
Original Claim:
  "${claim.statement}"

Direction: ${claim.direction || 'Unspecified'}
Evidence Coverage: ${claim.evidenceCoverage}%
Implied Horizon: ${claim.horizon || 'Unspecified'}
${claim.currentPrice ? `Current Price: ${claim.currentPrice}\n` : ''}${claim.targetPrice ? `Target Price: ${claim.targetPrice}\n` : ''}${claim.sourceUrl ? `Source Reference: ${claim.sourceUrl}\n` : ''}Completeness Score: ${claim.completeness?.score || claim.evidenceCoverage || 'N/A'} / 100
Identified Assumptions: ${claim.completeness?.identifiedAssumptions || 4} Total
Tested Assumptions: ${claim.completeness?.testedAssumptions || 1} Tested

--------------------------------------------------------------------------------
SECTION A — CLAIM BREAKDOWN
--------------------------------------------------------------------------------
Stated Target:
  ${claim.breakdown?.statedTarget || 'Target not specified'}

Implied Timeframe / Horizon:
  ${claim.breakdown?.impliedHorizon || claim.horizon || 'Timeframe not specified'}

Primary Catalyst:
  ${claim.breakdown?.primaryCatalyst || 'Catalyst not specified'}

--------------------------------------------------------------------------------
SECTION B — INVALIDATION CONDITIONS (CRITICAL CHECKS)
--------------------------------------------------------------------------------
The claim relies on hidden assumptions that would negate the thesis if violated:
${missingConditions.map((cond, i) => `  [${i + 1}] ${cond}`).join('\n')}

--------------------------------------------------------------------------------
SECTION C — INTERPRETATION FORK ENGINE (MULTI-ANGLE PERSPECTIVES)
--------------------------------------------------------------------------------
${interpretations || '  No interpretation forks recorded.'}

--------------------------------------------------------------------------------
SECTION D — SUPPORTING EVIDENCE & CITATIONS
--------------------------------------------------------------------------------
${supportingEvidence || '  No supporting evidence recorded.'}
${contradictoryEvidence ? `\n--------------------------------------------------------------------------------\nCONTRADICTORY / RISK EVIDENCE\n--------------------------------------------------------------------------------\n${contradictoryEvidence}\n` : ''}
--------------------------------------------------------------------------------
EVIDENCE DETAILS & CONCLUSIONS
--------------------------------------------------------------------------------
Evidence Coverage Score: ${claim.evidenceCoverage}%
Validation State: ${claim.validationStatus}
Conclusion:
  ${claim.validationStatus === 'Completed'
    ? 'All core claims and assumptions have been verified against filed regulatory records and empirical performance metrics.'
    : 'The claim contains substantial untested assumptions and delivery timeline risks that warrant independent stress testing in the Virtual Decision Lab.'}

================================================================================
REPORT EXPORT METADATA
================================================================================
Exported by: FINTRACE Investor Workspace
Export Timestamp: ${exportDate}
File Format: Plain Text (.txt) Claim Analysis Report
System Note: Synthetic educational demonstration data.
================================================================================
`;
}

export default function ClaimAnalysisReport() {
  const [searchParams] = useSearchParams();
  const claimId = searchParams.get('id') || 'claim_mgs_01';
  const [claim, setClaim] = useState(null);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [downloadError, setDownloadError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.getClaim(claimId).then(setClaim);
  }, [claimId]);

  if (!claim) {
    return (
      <div className="flex-1 p-gutter-xl flex items-center justify-center">
        <div className="flex items-center gap-2 text-body-md font-mono">
          <span className="material-symbols-outlined animate-spin text-[20px]">progress_activity</span>
          <span>Loading claim report...</span>
        </div>
      </div>
    );
  }

  const handleExport = () => {
    try {
      if (!claim) {
        throw new Error('No claim data available to export.');
      }

      // Generate complete text content
      const reportContent = generateReportText(claim);

      // Create Blob with MIME type text/plain;charset=utf-8
      const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });

      // Dynamically generate sanitized filename
      const sanitizedName = (claim.company || claim.ticker || 'Claim')
        .trim()
        .replace(/[^a-zA-Z0-9\s_-]/g, '')
        .replace(/\s+/g, '_');
      const filename = `FINTRACE_${sanitizedName}_Claim_Report.txt`;

      // Create temporary download URL and anchor element
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Revoke temporary URL
      setTimeout(() => {
        URL.revokeObjectURL(downloadUrl);
      }, 1000);

      setDownloadSuccess(true);
      setDownloadError(null);
      setTimeout(() => setDownloadSuccess(false), 3000);
    } catch (err) {
      console.error('Download failed:', err);
      setDownloadError('Failed to download report. Please try again.');
      setTimeout(() => setDownloadError(null), 4000);
    }
  };

  return (
    <main className="flex-1 p-gutter-md lg:p-gutter-lg max-w-6xl w-full mx-auto flex flex-col gap-gutter-lg">
      {/* Download Notifications */}
      {downloadSuccess && (
        <div
          role="status"
          aria-live="polite"
          className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-800 dark:text-emerald-200 flex items-center justify-between gap-2 text-body-sm font-semibold animate-fadeIn shadow-sm"
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-emerald-600 dark:text-emerald-400 text-[20px]">
              check_circle
            </span>
            <span>Report downloaded successfully.</span>
          </div>
          <span className="font-mono text-xs opacity-75">
            FINTRACE_{((claim.company || claim.ticker || 'Claim').trim().replace(/[^a-zA-Z0-9\s_-]/g, '').replace(/\s+/g, '_'))}_Claim_Report.txt
          </span>
        </div>
      )}

      {downloadError && (
        <div
          role="alert"
          className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-800 dark:text-rose-200 flex items-center gap-2 text-body-sm font-semibold animate-fadeIn shadow-sm"
        >
          <span className="material-symbols-outlined text-rose-600 dark:text-rose-400 text-[20px]">
            error
          </span>
          <span>{downloadError}</span>
        </div>
      )}

      {/* Report Header Card */}
      <section className="p-gutter-lg rounded-lg bg-light-surface-container-low dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-gutter-md">
          <div className="flex flex-col gap-gutter-xs">
            <div className="flex flex-wrap items-center gap-gutter-sm">
              <span className="font-mono text-mono-sm px-2.5 py-0.5 rounded-sm bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container font-semibold">
                {claim.ticker}
              </span>
              <span className="font-mono text-mono-sm px-2 py-0.5 rounded-sm bg-light-surface dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-light-on-surface-variant dark:text-dark-on-surface-variant">
                SYNTHETIC CLAIM REPORT
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full font-label text-label-sm font-semibold ${
                claim.validationStatus === 'Completed'
                  ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                  : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
              }`}>
                {claim.validationStatus}
              </span>
            </div>
            <h1 className="font-display text-headline-lg lg:text-display-lg font-bold">
              {claim.company} — Claim Analysis Report
            </h1>
            <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant italic border-l-2 border-light-primary dark:border-dark-primary pl-3 py-1">
              "{claim.statement}"
            </p>
          </div>

          <div className="flex items-center gap-gutter-sm shrink-0">
            <button
              type="button"
              id="export-report-btn"
              data-testid="export-report-btn"
              onClick={handleExport}
              className="inline-flex items-center gap-1.5 px-gutter-md py-2.5 rounded-DEFAULT border border-light-outline-variant dark:border-dark-outline-variant bg-light-surface dark:bg-dark-surface-container text-light-on-surface dark:text-dark-on-surface hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container-high font-label text-label-lg font-medium transition-colors shadow-sm cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">
                {downloadSuccess ? 'check_circle' : 'download'}
              </span>
              <span>{downloadSuccess ? 'Exported' : 'Export'}</span>
            </button>

            <Link
              to="/virtual-decision-lab"
              className="inline-flex items-center gap-1.5 px-gutter-md py-2.5 rounded-DEFAULT bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary hover:opacity-90 font-label text-label-lg font-semibold transition-opacity shadow-sm"
            >
              <span className="material-symbols-outlined text-[18px]">science</span>
              <span>Test in Decision Lab</span>
            </Link>
          </div>
        </div>

        {/* Overview Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-gutter-sm pt-gutter-md border-t border-light-outline-variant dark:border-dark-outline-variant font-mono text-mono-sm">
          <div>
            <span className="text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px] uppercase block">
              Evidence Coverage
            </span>
            <span className="font-bold text-headline-md font-sans text-light-primary dark:text-dark-primary">
              {claim.evidenceCoverage}%
            </span>
          </div>
          <div>
            <span className="text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px] uppercase block">
              Implied Horizon
            </span>
            <span className="font-semibold text-body-md font-sans text-light-on-surface dark:text-dark-on-surface">
              {claim.horizon}
            </span>
          </div>
          <div>
            <span className="text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px] uppercase block">
              Identified Assumptions
            </span>
            <span className="font-semibold text-body-md font-sans text-light-on-surface dark:text-dark-on-surface">
              {claim.completeness?.identifiedAssumptions || 4} Total · {claim.completeness?.testedAssumptions || 1} Tested
            </span>
          </div>
          <div>
            <span className="text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px] uppercase block">
              Provenance Status
            </span>
            <span className="font-semibold text-[11px] text-amber-600 dark:text-amber-400">
              {claim.completeness?.provenanceStatus || 'USER-PROVIDED'}
            </span>
          </div>
        </div>
      </section>

      {/* Section A — Claim Breakdown */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="font-headline text-headline-md font-bold">Section A — Claim Breakdown</h2>
          <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            SYNTHETIC
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md">
          <div className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1">
            <span className="font-label text-label-sm text-light-on-primary-container dark:text-dark-on-primary-container font-semibold uppercase text-[11px]">
              Stated Target
            </span>
            <p className="font-title text-title-md font-semibold text-light-on-surface dark:text-dark-on-surface">
              {claim.breakdown?.statedTarget || '30% price appreciation'}
            </p>
          </div>

          <div className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1">
            <span className="font-label text-label-sm text-light-on-primary-container dark:text-dark-on-primary-container font-semibold uppercase text-[11px]">
              Implied Timeframe
            </span>
            <p className="font-title text-title-md font-semibold text-light-on-surface dark:text-dark-on-surface">
              {claim.breakdown?.impliedHorizon || '60 days'}
            </p>
          </div>

          <div className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-1">
            <span className="font-label text-label-sm text-light-on-primary-container dark:text-dark-on-primary-container font-semibold uppercase text-[11px]">
              Primary Catalyst
            </span>
            <p className="font-title text-title-md font-semibold text-light-on-surface dark:text-dark-on-surface">
              {claim.breakdown?.primaryCatalyst || 'Substation delivery pipeline'}
            </p>
          </div>
        </div>
      </section>

      {/* Section B — Missing Invalidation Conditions */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-warning text-[22px]">warning</span>
            <h2 className="font-headline text-headline-md font-bold">Section B — Invalidation Conditions</h2>
          </div>
          <span className="text-label-sm text-amber-600 dark:text-amber-400 font-semibold font-mono">
            CRITICAL CHECKS
          </span>
        </div>

        <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant">
          The claim relies on hidden assumptions that would negate the thesis if violated:
        </p>

        <ul className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md">
          {(claim.breakdown?.missingConditions || [
            'High-voltage transformer delivery lead times exceed 84 weeks',
            'Raw copper and grain-oriented electrical steel price surges',
            'FERC interconnection queue backlog deferrals'
          ]).map((cond, idx) => (
            <li key={idx} className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex items-start gap-2.5">
              <span className="material-symbols-outlined text-warning text-[18px] shrink-0 mt-0.5">
                cancel
              </span>
              <span className="text-body-md text-light-on-surface dark:text-dark-on-surface font-medium text-[13px]">
                {cond}
              </span>
            </li>
          ))}
        </ul>
      </section>

      {/* Section C — Interpretation Fork Engine */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-headline text-headline-md font-bold">Section C — Interpretation Fork Engine</h2>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
              Multi-angle perspective compiler: examining bull, bear, and consensus perspectives.
            </p>
          </div>
          <span className="font-mono text-mono-sm px-2 py-0.5 rounded-sm bg-light-secondary/30 text-light-on-secondary dark:bg-dark-secondary/25 dark:text-dark-on-surface text-[11px]">
            AI-GENERATED FORKS
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md items-stretch">
          {(claim.interpretations || []).map((fork, idx) => (
            <article key={idx} className="p-gutter-md rounded-lg bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col justify-between gap-gutter-sm">
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold font-mono ${
                    fork.stance.toLowerCase().includes('bull')
                      ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                      : fork.stance.toLowerCase().includes('bear')
                      ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400'
                      : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                  }`}>
                    {fork.stance}
                  </span>
                  <span className="text-[10px] font-mono text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    FORK {String.fromCharCode(65 + idx)}
                  </span>
                </div>
                <h3 className="font-title text-title-md font-semibold">{fork.fork}</h3>
                <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                  {fork.rationale}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Section D — Supporting Evidence & Citations */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="font-headline text-headline-md font-bold">Section D — Supporting Evidence</h2>
          <Link
            to="/evidence-centre"
            className="font-label text-label-sm text-light-on-primary-container dark:text-dark-secondary hover:underline inline-flex items-center gap-1 font-semibold"
          >
            <span>Open in Evidence Centre</span>
            <span className="material-symbols-outlined text-[16px]">open_in_new</span>
          </Link>
        </div>

        <div className="flex flex-col gap-gutter-md">
          {(claim.supportingEvidence || []).map((ev) => (
            <div key={ev.id} className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-body-md text-light-on-surface dark:text-dark-on-surface">
                    {ev.title}
                  </span>
                  <span className="font-mono text-mono-sm px-2 py-0.5 rounded-sm bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold">
                    {ev.provenance}
                  </span>
                </div>
                <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
                  {ev.source} · {ev.date}
                </span>
              </div>
              <blockquote className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant border-l-2 border-light-primary dark:border-dark-primary pl-3 text-[13px]">
                "{ev.excerpt}"
              </blockquote>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
