import React from 'react';

export default function DecisionIntelligence() {
  const dimensions = [
    { name: 'Evidence Scrutiny', score: 84, description: 'Depth of inquiry into primary regulatory and financial filings' },
    { name: 'Assumption Invalidation', score: 79, description: 'Ability to identify counterfactuals that would break the thesis' },
    { name: 'Horizon Realism', score: 82, description: 'Detecting mismatched timelines between catalysts and stock predictions' },
    { name: 'Source Provenance', score: 76, description: 'Differentiating verified corporate disclosures from social commentary' },
    { name: 'Cognitive Calibration', score: 69, description: 'Aligning subjective confidence with objective evidence probability' }
  ];

  const sessions = [
    {
      date: '18 Nov 2026',
      claim: 'Meridian Grid Systems (MGS)',
      type: 'Independent',
      initialConfidence: 85,
      calibratedConfidence: 58,
      score: 82,
      delta: '+26 pts',
      highlight: 'Exposed 84-week transformer delivery chokepoint'
    },
    {
      date: '17 Nov 2026',
      claim: 'Vortex Semiconductors (VRTX)',
      type: 'Assisted Practice',
      initialConfidence: 75,
      calibratedConfidence: 70,
      score: 79,
      delta: '+14 pts',
      highlight: 'Validated die-to-wafer patent claim moat'
    },
    {
      date: '14 Nov 2026',
      claim: 'Quantum Logistics (QNTM)',
      type: 'Assisted Practice',
      initialConfidence: 90,
      calibratedConfidence: 45,
      score: 74,
      delta: '+28 pts',
      highlight: 'Flagged sub-zero temperature battery degradation'
    },
    {
      date: '02 Nov 2026',
      claim: 'Apex Renewables (APXR)',
      type: 'Baseline Assessment',
      initialConfidence: 80,
      calibratedConfidence: 72,
      score: 52,
      delta: 'Baseline',
      highlight: 'Initial onboarding calibration profile established'
    }
  ];

  return (
    <main className="flex-1 p-gutter-md lg:p-gutter-lg max-w-7xl w-full mx-auto flex flex-col gap-gutter-lg">
      <div className="flex flex-col gap-gutter-xs">
        <h1 className="font-display text-display-lg-mobile lg:text-display-lg font-bold" data-design-text-token="display-lg">
          Decision Intelligence
        </h1>
        <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant" data-design-text-token="body-lg">
          Measure how effectively you evaluate financial information and calibrate judgment.
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
            78 / 100
          </p>
          <span className="font-mono text-mono-sm text-emerald-600 dark:text-emerald-400 font-semibold">
            +26 pts from baseline (52)
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
          <p className="font-display text-headline-lg tabular-nums font-bold">84%</p>
          <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            4 of 5 blindspots caught
          </span>
        </article>

        <article className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col justify-between gap-gutter-sm shadow-sm">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Calibration Ratio
            </span>
            <span className="material-symbols-outlined text-light-primary dark:text-dark-primary text-[20px]">
              model_training
            </span>
          </div>
          <p className="font-display text-headline-lg tabular-nums font-bold">9 : 5</p>
          <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            9 Assisted · 5 Independent
          </span>
        </article>

        <article className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col justify-between gap-gutter-sm shadow-sm">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Proficiency Tier
            </span>
            <span className="material-symbols-outlined text-light-secondary dark:text-dark-secondary text-[20px]">
              military_tech
            </span>
          </div>
          <p className="font-display text-headline-lg font-bold">Tier III</p>
          <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            Analytical Practitioner
          </span>
        </article>
      </section>

      {/* Progression Architecture */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <h2 className="font-headline text-headline-md font-bold">
          Baseline → Assisted Practice → Independent Assessment
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md">
          <div className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-mono-sm text-light-outline dark:text-dark-outline uppercase text-[11px]">
                Stage 1
              </span>
              <span className="font-mono text-mono-sm font-semibold">52 / 100</span>
            </div>
            <h3 className="font-title text-title-md font-semibold">Baseline Onboarding</h3>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
              Initial heuristic audit measuring cognitive biases and acceptance of unchecked claims.
            </p>
          </div>

          <div className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-mono-sm text-light-secondary dark:text-dark-secondary uppercase text-[11px]">
                Stage 2
              </span>
              <span className="font-mono text-mono-sm font-semibold">71 / 100</span>
            </div>
            <h3 className="font-title text-title-md font-semibold">Assisted Scrutiny</h3>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
              Interactive AI scenario forking highlighting supply bottlenecks and regulatory dates.
            </p>
          </div>

          <div className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border-2 border-light-primary dark:border-dark-primary flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-mono-sm text-light-primary dark:text-dark-primary uppercase font-bold text-[11px]">
                Stage 3 (Active)
              </span>
              <span className="font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary">
                78 / 100
              </span>
            </div>
            <h3 className="font-title text-title-md font-semibold">Independent Assessment</h3>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
              User autonomously challenges premises and tests invalidation conditions before assistance.
            </p>
          </div>
        </div>
      </section>

      {/* Five Assessment Dimensions */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="font-headline text-headline-md font-bold">Five Assessment Dimensions</h2>
          <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
            SYNTHETIC CALIBRATION
          </span>
        </div>

        <div className="flex flex-col gap-gutter-md">
          {dimensions.map((dim) => (
            <div key={dim.name} className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-body-md">
                <span className="font-semibold text-light-on-surface dark:text-dark-on-surface">
                  {dim.name}
                </span>
                <span className="font-mono text-mono-sm font-bold tabular-nums">
                  {dim.score} / 100
                </span>
              </div>
              <div className="w-full bg-light-surface-container dark:bg-dark-surface-container h-2 rounded-full overflow-hidden">
                <div
                  className="bg-light-primary dark:bg-dark-primary h-full rounded-full transition-all duration-500"
                  style={{ width: `${dim.score}%` }}
                />
              </div>
              <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
                {dim.description}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Session History Table */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex flex-col gap-gutter-md shadow-sm">
        <h2 className="font-headline text-headline-md font-bold">Session History</h2>
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-light-outline-variant dark:border-dark-outline-variant text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider">
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Target Claim</th>
                <th className="py-2.5 px-3">Session Mode</th>
                <th className="py-2.5 px-3">Confidence Shift</th>
                <th className="py-2.5 px-3">Score</th>
                <th className="py-2.5 px-3">Key Observation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-light-outline-variant/60 dark:divide-dark-outline-variant/60 text-body-md">
              {sessions.map((s, idx) => (
                <tr key={idx} className="hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container transition-colors">
                  <td className="py-3 px-3 font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    {s.date}
                  </td>
                  <td className="py-3 px-3 font-semibold text-light-on-surface dark:text-dark-on-surface">
                    {s.claim}
                  </td>
                  <td className="py-3 px-3 font-mono text-mono-sm text-[12px]">
                    {s.type}
                  </td>
                  <td className="py-3 px-3 font-mono text-mono-sm">
                    {s.initialConfidence}% → {s.calibratedConfidence}%
                  </td>
                  <td className="py-3 px-3 font-mono text-mono-sm font-bold text-light-primary dark:text-dark-primary">
                    {s.score} ({s.delta})
                  </td>
                  <td className="py-3 px-3 text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    {s.highlight}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
