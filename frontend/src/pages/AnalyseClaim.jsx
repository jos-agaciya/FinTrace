import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function AnalyseClaim() {
  const [statement, setStatement] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [ticker, setTicker] = useState('');
  const [horizon, setHorizon] = useState('2 months');
  const [analyzing, setAnalyzing] = useState(false);
  const [modelFork, setModelFork] = useState(true);
  const navigate = useNavigate();

  const exampleClaims = [
    {
      label: 'MGS · Grid Backlog (+30%)',
      statement: 'MGS will rise 30% in two months on strong grid backlog.',
      ticker: 'MGS',
      sourceUrl: 'https://twitter.com/energy_analyst_pro/status/17258390',
      horizon: '2 months'
    },
    {
      label: 'APXR · Capacity Doubling (+100%)',
      statement: 'Apex Renewables capacity will double post-tax credit announcement in 6 months.',
      ticker: 'APXR',
      sourceUrl: 'https://linkedin.com/posts/cleanpower-brief',
      horizon: '6 months'
    },
    {
      label: 'VRTX · Semiconductor Yields (+22%)',
      statement: 'Next-gen packaging yields will crush competitor margins across next 12 months.',
      ticker: 'VRTX',
      sourceUrl: 'https://semi-analysis.substack.com/p/vortex-yields',
      horizon: '1 year'
    }
  ];

  const handleSelectExample = (ex) => {
    setStatement(ex.statement);
    setTicker(ex.ticker);
    setSourceUrl(ex.sourceUrl);
    setHorizon(ex.horizon);
  };

  const handleClear = () => {
    setStatement('');
    setSourceUrl('');
    setTicker('');
    setHorizon('2 months');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!statement.trim()) return;

    setAnalyzing(true);
    try {
      const res = await api.analyzeClaim({
        statement,
        sourceUrl,
        ticker,
        horizon
      });
      // Small timeout to show compilation step
      setTimeout(() => {
        setAnalyzing(false);
        navigate(`/claim-analysis-report?id=${res.id || 'claim_mgs_01'}`);
      }, 1000);
    } catch (err) {
      setAnalyzing(false);
      navigate('/claim-analysis-report?id=claim_mgs_01');
    }
  };

  return (
    <main className="flex-1 p-gutter-md lg:p-gutter-xl max-w-4xl w-full mx-auto flex flex-col gap-gutter-lg">
      <div className="flex flex-col gap-gutter-xs">
        <h1 className="font-display text-display-lg-mobile lg:text-display-lg font-bold" data-design-text-token="display-lg">
          Analyse a Claim
        </h1>
        <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant" data-design-text-token="body-lg">
          Understand the claim. Examine the evidence. Challenge the assumptions.
        </p>
      </div>

      {/* 3-Step Process Flow */}
      <section aria-label="Compiler Workflow" className="grid grid-cols-1 md:grid-cols-3 gap-gutter-md">
        <div className="p-gutter-md rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex items-start gap-3">
          <span className="w-8 h-8 rounded-full bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container flex items-center justify-center font-mono text-mono-sm font-bold shrink-0">
            1
          </span>
          <div>
            <h3 className="font-title text-title-md font-semibold">Parse Claim</h3>
            <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Deconstruct catalysts, stated milestones, and implied time horizon.
            </p>
          </div>
        </div>

        <div className="p-gutter-md rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex items-start gap-3">
          <span className="w-8 h-8 rounded-full bg-light-secondary/30 text-light-on-secondary dark:bg-dark-secondary/30 dark:text-dark-on-surface flex items-center justify-center font-mono text-mono-sm font-bold shrink-0">
            2
          </span>
          <div>
            <h3 className="font-title text-title-md font-semibold">Map Evidence</h3>
            <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Cross-check SEC EDGAR disclosures, supply chokepoints, and filings.
            </p>
          </div>
        </div>

        <div className="p-gutter-md rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant flex items-start gap-3">
          <span className="w-8 h-8 rounded-full bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container flex items-center justify-center font-mono text-mono-sm font-bold shrink-0">
            3
          </span>
          <div>
            <h3 className="font-title text-title-md font-semibold">Compile Forks</h3>
            <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Examine contradictory assumptions and counterfactual scenarios.
            </p>
          </div>
        </div>
      </section>

      {/* Synthetic Example Claims */}
      <section className="flex flex-col gap-gutter-xs">
        <span className="font-label text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider font-semibold text-[11px]">
          Synthetic Example Claims (Click to Populate)
        </span>
        <div className="flex flex-wrap gap-2">
          {exampleClaims.map((ex, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSelectExample(ex)}
              className="px-3 py-1.5 rounded-DEFAULT bg-light-surface dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant hover:border-light-primary dark:hover:border-dark-primary text-body-md text-light-on-surface dark:text-dark-on-surface font-medium transition-colors text-left flex items-center gap-2 text-[13px]"
            >
              <span className="material-symbols-outlined text-[16px] text-light-primary dark:text-dark-primary">
                touch_app
              </span>
              <span>{ex.label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Main Analysis Form */}
      <form onSubmit={handleSubmit} className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant shadow-sm flex flex-col gap-gutter-lg">
        <label className="flex flex-col gap-gutter-xs">
          <div className="flex items-center justify-between">
            <span className="font-label text-label-lg font-semibold">Financial Claim Statement</span>
            <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px]">
              Required
            </span>
          </div>
          <textarea
            required
            rows={4}
            value={statement}
            onChange={(e) => setStatement(e.target.value)}
            placeholder="Paste or write the financial assertion (e.g., 'Company X will double capacity and gross margin by Q3 due to new supplier agreements...')"
            className="w-full px-gutter-md py-3 rounded-DEFAULT bg-light-surface dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface placeholder:text-light-outline dark:placeholder:text-dark-outline focus:border-light-primary dark:focus:border-dark-primary focus:ring-1 focus:ring-light-primary dark:focus:ring-dark-primary outline-none transition-colors"
          />
        </label>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter-md">
          <label className="flex flex-col gap-gutter-xs">
            <span className="font-label text-label-lg font-semibold">Source URL (Optional)</span>
            <input
              type="url"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://social.network/post/claim-id"
              className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface placeholder:text-light-outline dark:placeholder:text-dark-outline focus:border-light-primary dark:focus:border-dark-primary focus:ring-1 focus:ring-light-primary outline-none transition-colors"
            />
            <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px]">
              Attach social post, video, or research note for provenance tracking.
            </span>
          </label>

          <div className="grid grid-cols-2 gap-gutter-sm">
            <label className="flex flex-col gap-gutter-xs">
              <span className="font-label text-label-lg font-semibold">Ticker / Symbol</span>
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                placeholder="e.g. MGS"
                className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface placeholder:text-light-outline dark:placeholder:text-dark-outline focus:border-light-primary dark:focus:border-dark-primary focus:ring-1 focus:ring-light-primary outline-none transition-colors uppercase font-mono"
              />
            </label>

            <label className="flex flex-col gap-gutter-xs">
              <span className="font-label text-label-lg font-semibold">Implied Horizon</span>
              <select
                value={horizon}
                onChange={(e) => setHorizon(e.target.value)}
                className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface outline-none focus:border-light-primary dark:focus:border-dark-primary transition-colors cursor-pointer"
              >
                <option value="1 month">1 month</option>
                <option value="2 months">2 months</option>
                <option value="6 months">6 months</option>
                <option value="1 year">1 year</option>
                <option value="2+ years">2+ years</option>
              </select>
            </label>
          </div>
        </div>

        {/* Multi-Model Compiler Options */}
        <div className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-light-primary dark:text-dark-primary text-[22px]">
              hub
            </span>
            <div>
              <p className="font-label text-label-lg font-semibold">Multi-Model Scenario Forking</p>
              <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
                Enables contrasting bull / bear thesis trees and chokepoint scrutiny.
              </p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={modelFork}
              onChange={(e) => setModelFork(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-light-outline-variant peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-light-primary dark:peer-checked:bg-dark-primary"></div>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-gutter-md pt-2 border-t border-light-outline-variant dark:border-dark-outline-variant">
          <button
            type="button"
            onClick={handleClear}
            className="px-gutter-md py-2.5 rounded-DEFAULT text-light-on-surface-variant dark:text-dark-on-surface-variant hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container font-label text-label-lg font-semibold transition-colors"
          >
            Clear Draft
          </button>

          <button
            type="submit"
            disabled={analyzing || !statement.trim()}
            className="inline-flex items-center justify-center gap-gutter-sm px-gutter-lg py-2.5 rounded-DEFAULT bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed font-label text-label-lg font-semibold transition-all duration-state-change shadow-sm"
          >
            {analyzing ? (
              <>
                <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                <span>Compiling Robustness Report...</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]">query_stats</span>
                <span>Analyse Claim</span>
              </>
            )}
          </button>
        </div>
      </form>
    </main>
  );
}
