import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';

export default function AnalysisReports() {
  const [searchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const [query, setQuery] = useState(initialQuery);
  const [statusFilter, setStatusFilter] = useState('All');
  const [claims, setClaims] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    api.getClaims().then((data) => {
      if (isMounted) {
        setClaims(data || []);
        setLoading(false);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredClaims = claims.filter((c) => {
    const matchesSearch =
      c.company.toLowerCase().includes(query.toLowerCase()) ||
      c.ticker.toLowerCase().includes(query.toLowerCase()) ||
      c.statement.toLowerCase().includes(query.toLowerCase());
    const matchesStatus =
      statusFilter === 'All' || c.validationStatus === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const toggleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(filteredClaims.map((c) => c.id));
    } else {
      setSelectedIds([]);
    }
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteClaim(id);
      setClaims((prev) => prev.filter((c) => c.id !== id));
      setSelectedIds((prev) => prev.filter((i) => i !== id));
    } catch (err) {
      console.error('Failed to delete claim from backend:', err);
    }
  };

  const handleBulkDelete = async () => {
    try {
      await Promise.all(selectedIds.map((id) => api.deleteClaim(id)));
      setClaims((prev) => prev.filter((c) => !selectedIds.includes(c.id)));
      setSelectedIds([]);
    } catch (err) {
      console.error('Failed to bulk delete claims:', err);
    }
  };

  return (
    <main className="flex-1 p-gutter-md lg:p-gutter-lg max-w-7xl w-full mx-auto flex flex-col gap-gutter-lg">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-gutter-md">
        <div>
          <h1 className="font-display text-display-lg-mobile lg:text-display-lg font-bold" data-design-text-token="display-lg">
            Analysis Reports
          </h1>
          <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
            Browse, filter, and manage verified claim evaluations.
          </p>
        </div>
        <Link
          to="/analyse-claim"
          className="inline-flex items-center gap-gutter-sm px-gutter-md py-2.5 rounded-DEFAULT bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary hover:opacity-90 font-label text-label-lg font-semibold transition-opacity shrink-0 shadow-sm"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          <span>Analyse New Claim</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <section className="p-gutter-md rounded-lg bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant flex flex-col md:flex-row items-center justify-between gap-gutter-md">
        <div className="flex flex-wrap items-center gap-1 w-full md:w-auto">
          {['All', 'Needs Verification', 'Completed', 'Provider Unavailable'].map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-DEFAULT font-label text-label-sm font-semibold transition-colors ${
                statusFilter === status
                  ? 'bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary shadow-sm'
                  : 'text-light-on-surface-variant dark:text-dark-on-surface-variant hover:bg-light-surface dark:hover:bg-dark-surface-container-high'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-gutter-sm w-full md:w-auto justify-end">
          <div className="relative flex-1 md:w-64">
            <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-light-on-surface-variant dark:text-dark-on-surface-variant pointer-events-none">
              search
            </span>
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search reports..."
              className="w-full pl-9 pr-3 py-2 rounded-DEFAULT bg-light-surface dark:bg-dark-surface-container-high border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface placeholder:text-light-outline dark:placeholder:text-dark-outline outline-none focus:border-light-primary dark:focus:border-dark-primary"
            />
          </div>

          {selectedIds.length > 0 && (
            <button
              type="button"
              onClick={handleBulkDelete}
              className="px-3 py-2 rounded-DEFAULT bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 font-label text-label-sm font-semibold flex items-center gap-1 transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">delete</span>
              <span>Delete ({selectedIds.length})</span>
            </button>
          )}
        </div>
      </section>

      {/* Reports Table */}
      <section className="w-full overflow-x-auto rounded-lg border border-light-outline-variant dark:border-dark-outline-variant bg-light-surface dark:bg-dark-surface-container-low shadow-sm">
        <table className="w-full text-left border-collapse">
          <thead className="bg-light-surface-container-low dark:bg-dark-surface-container border-b border-light-outline-variant dark:border-dark-outline-variant">
            <tr>
              <th scope="col" className="p-3 w-10">
                <input
                  type="checkbox"
                  checked={
                    filteredClaims.length > 0 &&
                    selectedIds.length === filteredClaims.length
                  }
                  onChange={toggleSelectAll}
                  className="rounded-sm border-light-outline-variant dark:border-dark-outline-variant text-light-primary dark:text-dark-primary"
                />
              </th>
              <th scope="col" className="px-gutter-md py-3 font-label text-label-sm uppercase tracking-wider text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Company / Ticker
              </th>
              <th scope="col" className="px-gutter-md py-3 font-label text-label-sm uppercase tracking-wider text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Direction
              </th>
              <th scope="col" className="px-gutter-md py-3 font-label text-label-sm uppercase tracking-wider text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Date Analysed
              </th>
              <th scope="col" className="px-gutter-md py-3 font-label text-label-sm uppercase tracking-wider text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Coverage
              </th>
              <th scope="col" className="px-gutter-md py-3 font-label text-label-sm uppercase tracking-wider text-light-on-surface-variant dark:text-dark-on-surface-variant">
                Validation
              </th>
              <th scope="col" className="px-gutter-md py-3 font-label text-label-sm uppercase tracking-wider text-light-on-surface-variant dark:text-dark-on-surface-variant text-right">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-light-outline-variant dark:divide-dark-outline-variant text-body-md">
            {filteredClaims.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-light-on-surface-variant dark:text-dark-on-surface-variant font-mono text-mono-sm">
                  {claims.length === 0
                    ? 'No analysis reports currently saved in the database. Submit a claim to generate your first report.'
                    : 'No analysis reports match your filter criteria.'}
                </td>
              </tr>
            ) : (
              filteredClaims.map((claim) => (
                <tr
                  key={claim.id}
                  className={`hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container transition-colors ${
                    selectedIds.includes(claim.id)
                      ? 'bg-light-primary-container/20 dark:bg-dark-primary-container/20'
                      : ''
                  }`}
                >
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(claim.id)}
                      onChange={() => toggleSelect(claim.id)}
                      className="rounded-sm border-light-outline-variant dark:border-dark-outline-variant text-light-primary dark:text-dark-primary"
                    />
                  </td>
                  <td className="px-gutter-md py-3.5">
                    <div className="flex flex-col">
                      <span className="font-semibold text-light-on-surface dark:text-dark-on-surface">
                        {claim.company} ({claim.ticker})
                      </span>
                      <span className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant truncate max-w-sm">
                        {claim.statement}
                      </span>
                    </div>
                  </td>
                  <td className="px-gutter-md py-3.5">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-label-sm font-semibold ${
                      claim.direction === 'Bullish'
                        ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                        : claim.direction === 'Bearish'
                        ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400'
                        : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                    }`}>
                      {claim.direction}
                    </span>
                  </td>
                  <td className="px-gutter-md py-3.5 font-mono text-mono-sm tabular-nums text-light-on-surface-variant dark:text-dark-on-surface-variant">
                    {claim.date}
                  </td>
                  <td className="px-gutter-md py-3.5">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-light-outline-variant dark:bg-dark-outline-variant h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-light-primary dark:bg-dark-primary h-full rounded-full"
                          style={{ width: `${claim.evidenceCoverage}%` }}
                        />
                      </div>
                      <span className="font-mono text-mono-sm tabular-nums">
                        {claim.evidenceCoverage}%
                      </span>
                    </div>
                  </td>
                  <td className="px-gutter-md py-3.5">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-label-sm font-semibold ${
                      claim.validationStatus === 'Completed'
                        ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                        : claim.validationStatus === 'Needs Verification'
                        ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                        : 'bg-rose-500/15 text-rose-600 dark:text-rose-400'
                    }`}>
                      {claim.validationStatus}
                    </span>
                  </td>
                  <td className="px-gutter-md py-3.5 text-right">
                    <div className="inline-flex items-center gap-2">
                      <Link
                        to={`/claim-analysis-report?id=${claim.id}`}
                        className="font-label text-label-sm text-light-on-primary-container dark:text-dark-secondary hover:underline font-semibold"
                      >
                        View Report
                      </Link>
                      <button
                        type="button"
                        onClick={() => handleDelete(claim.id)}
                        className="text-light-on-surface-variant dark:text-dark-on-surface-variant hover:text-rose-500 transition-colors cursor-pointer"
                        title="Delete report"
                      >
                        <span className="material-symbols-outlined text-[16px]">delete</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      {/* Footer Metadata */}
      <div className="flex items-center justify-between text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant font-mono">
        <span>Showing {filteredClaims.length} compiled reports</span>
        <span>PERSISTENT SQLITE AUDIT TRAIL</span>
      </div>
    </main>
  );
}
