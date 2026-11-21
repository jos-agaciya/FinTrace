import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function EvidenceCentre() {
  const [evidenceList, setEvidenceList] = useState([]);
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [activeFiling, setActiveFiling] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    api.getEvidence(query).then((items) => {
      if (isMounted) {
        setEvidenceList(items || []);
        setLoading(false);
      }
    });
    return () => {
      isMounted = false;
    };
  }, [query]);

  const categories = ['All', 'SEC Filings', 'Regulatory', 'Industry Reports'];

  const filteredEvidence = evidenceList.filter((ev) => {
    const matchesCategory =
      selectedCategory === 'All' || ev.category === selectedCategory;
    const matchesQuery =
      ev.title.toLowerCase().includes(query.toLowerCase()) ||
      ev.ticker.toLowerCase().includes(query.toLowerCase()) ||
      ev.source.toLowerCase().includes(query.toLowerCase()) ||
      ev.summary.toLowerCase().includes(query.toLowerCase());
    return matchesCategory && matchesQuery;
  });

  return (
    <main className="flex-1 p-gutter-md lg:p-gutter-lg max-w-7xl w-full mx-auto flex flex-col gap-gutter-lg">
      <div className="flex flex-col gap-gutter-xs">
        <h1 className="font-display text-display-lg-mobile lg:text-display-lg font-bold" data-design-text-token="display-lg">
          Evidence Centre
        </h1>
        <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant" data-design-text-token="body-lg">
          Explore the official information behind financial claims with full statutory provenance.
        </p>
      </div>

      {/* Search & Filter Bar */}
      <section className="p-gutter-md rounded-lg bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col md:flex-row items-center justify-between gap-gutter-md">
        <div className="flex flex-wrap items-center gap-1 w-full md:w-auto">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-DEFAULT font-label text-label-sm font-semibold transition-colors ${
                selectedCategory === cat
                  ? 'bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary shadow-sm'
                  : 'text-light-on-surface-variant dark:text-dark-on-surface-variant hover:bg-light-surface dark:hover:bg-dark-surface-container-high'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-80">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-light-on-surface-variant dark:text-dark-on-surface-variant pointer-events-none">
            search
          </span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search company, ticker, or filing..."
            className="w-full pl-9 pr-3 py-2 rounded-DEFAULT bg-light-surface dark:bg-dark-surface-container-high border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface placeholder:text-light-outline dark:placeholder:text-dark-outline outline-none focus:border-light-primary dark:focus:border-dark-primary transition-colors"
          />
        </div>
      </section>

      {/* Evidence Cards Grid */}
      {filteredEvidence.length === 0 ? (
        <section className="p-12 rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant text-center flex flex-col items-center justify-center gap-3">
          <span className="material-symbols-outlined text-[42px] text-light-outline dark:text-dark-outline">
            folder_open
          </span>
          <h3 className="font-headline text-headline-sm font-bold text-light-on-surface dark:text-dark-on-surface">
            {evidenceList.length === 0 ? 'No Statutory Disclosures Yet' : 'No Matching Disclosures'}
          </h3>
          <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant max-w-md text-[13px]">
            {evidenceList.length === 0
              ? 'When claims are submitted and analyzed, primary regulatory filings from NSE India and SEC EDGAR are retrieved, extracted, and cataloged here.'
              : 'No verified filings match your current search criteria. Try a different keyword or reset filters.'}
          </p>
        </section>
      ) : (
        <section className="grid grid-cols-1 md:grid-cols-2 gap-gutter-lg items-stretch">
          {filteredEvidence.map((ev) => (
            <article
              key={ev.id}
              className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant shadow-sm flex flex-col justify-between gap-gutter-md hover:border-light-primary dark:hover:border-dark-primary transition-colors duration-state-change"
            >
              <div className="flex flex-col gap-gutter-sm">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-mono-sm px-2 py-0.5 rounded-sm bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container font-semibold">
                    {ev.ticker}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded-sm font-mono text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                      {ev.provenance}
                    </span>
                    <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px]">
                      {ev.date}
                    </span>
                  </div>
                </div>

                <h2 className="font-title text-title-md font-bold text-light-on-surface dark:text-dark-on-surface">
                  {ev.title}
                </h2>

                <p className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
                  {ev.source}
                </p>

                <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant leading-relaxed text-[13px]">
                  {ev.summary}
                </p>
              </div>

              <div className="pt-gutter-sm border-t border-light-outline-variant dark:border-dark-outline-variant flex items-center justify-between">
                <span className="font-mono text-mono-sm text-emerald-600 dark:text-emerald-400 font-semibold text-[12px]">
                  {ev.confidenceScore}% Verification Confidence
                </span>
                <button
                  type="button"
                  onClick={() => setActiveFiling(ev)}
                  className="font-label text-label-lg text-light-on-primary-container dark:text-dark-secondary hover:underline inline-flex items-center gap-1 font-semibold cursor-pointer"
                >
                  <span>Inspect Excerpt</span>
                  <span className="material-symbols-outlined text-[16px]">visibility</span>
                </button>
              </div>
            </article>
          ))}
        </section>
      )}

      {/* Excerpt Modal */}
      {activeFiling && (
        <div
          className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-gutter-md"
          onClick={() => setActiveFiling(null)}
        >
          <div
            className="w-full max-w-2xl bg-light-surface dark:bg-dark-surface-container rounded-lg border border-light-outline-variant dark:border-dark-outline-variant p-gutter-lg flex flex-col gap-gutter-md shadow-2xl max-h-[85vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-mono-sm px-2 py-0.5 rounded-sm bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container font-semibold">
                    {activeFiling.ticker}
                  </span>
                  <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    {activeFiling.category}
                  </span>
                </div>
                <h3 className="font-title text-title-md font-bold text-light-on-surface dark:text-dark-on-surface">
                  {activeFiling.title}
                </h3>
                <p className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
                  {activeFiling.source} · Filing Date: {activeFiling.date}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setActiveFiling(null)}
                className="w-8 h-8 rounded-DEFAULT flex items-center justify-center text-light-on-surface-variant dark:text-dark-on-surface-variant hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container-high transition-colors cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="p-gutter-md rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant font-mono text-body-md text-light-on-surface dark:text-dark-on-surface leading-relaxed whitespace-pre-line text-[13px]">
              {activeFiling.fullText || activeFiling.summary}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-light-outline-variant dark:border-dark-outline-variant text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant font-mono">
              <div className="flex items-center gap-2">
                <span>Provenance: {activeFiling.provenance} RECORD</span>
                {activeFiling.url && (
                  <a
                    href={activeFiling.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-light-primary dark:text-dark-primary underline text-xs"
                  >
                    View Original Source ↗
                  </a>
                )}
              </div>
              <button
                type="button"
                onClick={() => setActiveFiling(null)}
                className="px-4 py-2 rounded-DEFAULT bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-lg font-semibold hover:opacity-90 cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
