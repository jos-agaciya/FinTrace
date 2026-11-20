import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import { api } from '../services/api';

export default function Registration() {
  const [name, setName] = useState('Nakul Verma');
  const [email, setEmail] = useState('nakul@fintrace.app');
  const [password, setPassword] = useState('password123');
  const [confirmPassword, setConfirmPassword] = useState('password123');
  const [agree, setAgree] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (!agree) {
      setError('Please agree to the educational workspace terms');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await api.register({ name, email, password });
      if (res && res.success) {
        navigate('/investor-dashboard');
      } else {
        setError('Registration failed. Please try again.');
      }
    } catch (err) {
      setError('Connection error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-light-surface text-light-on-surface dark:bg-dark-surface dark:text-dark-on-surface font-body transition-colors duration-theme-switch ease-theme-switch antialiased">
      {/* Left Brand Panel */}
      <section className="relative overflow-hidden lg:col-span-6 p-gutter-lg lg:p-gutter-xl bg-gradient-to-br from-light-surface via-light-surface-container-low to-light-surface-container dark:from-dark-surface dark:via-dark-surface-container-low dark:to-dark-surface-container border-b lg:border-b-0 lg:border-r border-light-outline-variant dark:border-dark-outline-variant flex flex-col justify-between gap-gutter-lg transition-colors duration-theme-switch">
        {/* Top Brand Lockup */}
        <div className="relative z-10 flex items-center justify-between gap-gutter-sm">
          <div className="flex items-center gap-gutter-sm">
            <div className="w-10 h-10 rounded-DEFAULT bg-light-primary dark:bg-dark-primary flex items-center justify-center text-light-on-primary dark:text-dark-on-primary shadow-sm">
              <span className="material-symbols-outlined text-[22px]" aria-hidden="true">
                analytics
              </span>
            </div>
            <div className="flex flex-col">
              <span className="font-display text-headline-md tracking-tight font-bold">FINTRACE</span>
              <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px]">
                Decision Robustness Compiler
              </span>
            </div>
          </div>
          <span className="font-mono text-mono-sm px-2.5 py-1 rounded-sm bg-light-surface/90 dark:bg-dark-surface-container/90 border border-light-outline-variant dark:border-dark-outline-variant text-light-on-surface-variant dark:text-dark-on-surface-variant">
            CALIBRATION ENVIRONMENT
          </span>
        </div>

        {/* Value Prop Presentation */}
        <div className="relative z-10 flex-1 flex flex-col justify-center gap-gutter-lg max-w-lg my-auto py-8">
          <div className="flex flex-col gap-gutter-xs">
            <h1 className="font-display text-headline-lg lg:text-display-lg leading-tight font-bold" data-design-text-token="display-lg">
              Create your FinTrace learning workspace.
            </h1>
            <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Systematic decision intelligence for retail investors. No hype, no trade execution—only traceable evidence.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-gutter-md">
            <div className="p-gutter-md rounded-lg bg-light-surface/80 dark:bg-dark-surface-container/80 border border-light-outline-variant dark:border-dark-outline-variant flex items-start gap-3">
              <span className="material-symbols-outlined text-light-primary dark:text-dark-primary text-[22px] shrink-0 mt-0.5">
                fact_check
              </span>
              <div>
                <h3 className="font-title text-title-md font-semibold">Systematic Claim Decomposition</h3>
                <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                  Extract hidden catalysts, implied time horizons, and missing invalidation tests.
                </p>
              </div>
            </div>

            <div className="p-gutter-md rounded-lg bg-light-surface/80 dark:bg-dark-surface-container/80 border border-light-outline-variant dark:border-dark-outline-variant flex items-start gap-3">
              <span className="material-symbols-outlined text-light-secondary dark:text-dark-secondary text-[22px] shrink-0 mt-0.5">
                account_tree
              </span>
              <div>
                <h3 className="font-title text-title-md font-semibold">Multi-Angle Interpretation Forks</h3>
                <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                  Contrast bull and bear scenario trees before locking into an analytical position.
                </p>
              </div>
            </div>

            <div className="p-gutter-md rounded-lg bg-light-surface/80 dark:bg-dark-surface-container/80 border border-light-outline-variant dark:border-dark-outline-variant flex items-start gap-3">
              <span className="material-symbols-outlined text-light-primary dark:text-dark-primary text-[22px] shrink-0 mt-0.5">
                science
              </span>
              <div>
                <h3 className="font-title text-title-md font-semibold">Before-and-After Calibration Lab</h3>
                <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                  Log your thesis prior to evidence review and measure calibration drift.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Guardrail */}
        <p className="relative z-10 text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
          Educational intelligence platform · Strict non-trading and non-advisory principles.
        </p>
      </section>

      {/* Right Auth Form Panel */}
      <main className="lg:col-span-6 p-gutter-lg lg:p-gutter-xl flex flex-col justify-between">
        <div className="flex justify-end">
          <ThemeToggle showLabels={true} />
        </div>

        <div className="w-full max-w-md mx-auto flex flex-col gap-gutter-lg py-gutter-md">
          <div className="flex flex-col gap-gutter-xs">
            <h2 className="font-headline text-headline-lg font-bold" data-design-text-token="headline-lg">
              Create account
            </h2>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Set up your analytical investor profile.
            </p>
          </div>

          {error && (
            <div className="p-3 rounded-DEFAULT bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-body-md">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-gutter-md">
            <label className="flex flex-col gap-gutter-xs">
              <span className="font-label text-label-lg font-medium">Full Name</span>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Nakul Verma"
                className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface dark:placeholder:text-dark-outline outline-none focus:border-light-primary dark:focus:border-dark-primary focus-visible:ring-2 focus-visible:ring-light-primary dark:focus-visible:ring-dark-primary transition-colors"
              />
            </label>

            <label className="flex flex-col gap-gutter-xs">
              <span className="font-label text-label-lg font-medium">Email address</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nakul@fintrace.app"
                className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface dark:placeholder:text-dark-outline outline-none focus:border-light-primary dark:focus:border-dark-primary focus-visible:ring-2 focus-visible:ring-light-primary dark:focus-visible:ring-dark-primary transition-colors"
              />
            </label>

            <label className="flex flex-col gap-gutter-xs">
              <span className="font-label text-label-lg font-medium">Password</span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a strong password"
                className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface dark:placeholder:text-dark-outline outline-none focus:border-light-primary dark:focus:border-dark-primary focus-visible:ring-2 focus-visible:ring-light-primary dark:focus-visible:ring-dark-primary transition-colors"
              />
            </label>

            <label className="flex flex-col gap-gutter-xs">
              <span className="font-label text-label-lg font-medium">Confirm Password</span>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm password"
                className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface dark:placeholder:text-dark-outline outline-none focus:border-light-primary dark:focus:border-dark-primary focus-visible:ring-2 focus-visible:ring-light-primary dark:focus-visible:ring-dark-primary transition-colors"
              />
            </label>

            <div className="flex items-start gap-2 text-body-md pt-1">
              <input
                type="checkbox"
                id="terms-check"
                checked={agree}
                onChange={(e) => setAgree(e.target.checked)}
                className="mt-1 rounded-sm border-light-outline-variant dark:border-dark-outline-variant text-light-primary dark:text-dark-primary focus:ring-light-primary"
              />
              <label htmlFor="terms-check" className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px] leading-relaxed cursor-pointer">
                I understand FinTrace provides educational decision analysis and traceable evidence only, and never provides trade execution or investment advice.
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-DEFAULT bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-lg font-semibold hover:opacity-90 active:scale-[0.99] transition-all duration-state-change flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <>
                  <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                  <span>Creating account...</span>
                </>
              ) : (
                'Create account'
              )}
            </button>
          </form>

          <p className="text-center text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-label text-label-lg text-light-on-primary-container dark:text-dark-on-primary-container hover:underline font-semibold"
            >
              Sign in
            </Link>
          </p>
        </div>

        <div className="text-center text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
          FINTRACE · Analytical Decision Workspace
        </div>
      </main>
    </div>
  );
}
