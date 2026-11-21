import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import MarketAnimation from '../components/MarketAnimation';
import { api } from '../services/api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.login(email, password);
      if (res && res.token) {
        navigate('/investor-dashboard');
      } else {
        setError('Invalid credentials. Please try again.');
      }
    } catch (err) {
      setError(err.message || 'Invalid email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-light-surface text-light-on-surface dark:bg-dark-surface dark:text-dark-on-surface font-body transition-colors duration-theme-switch ease-theme-switch antialiased">
      {/* Left Brand & Animated Synthetic Market Panel */}
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
            SYNTHETIC MARKET DEMO
          </span>
        </div>

        {/* Headline + Animated Synthetic Market Visual */}
        <div className="relative z-10 flex-1 flex flex-col justify-center gap-gutter-md my-auto py-6">
          <div className="max-w-lg flex flex-col gap-gutter-xs">
            <h1 className="font-display text-headline-lg lg:text-display-lg leading-tight font-bold" data-design-text-token="display-lg">
              Understand the claim. Examine the evidence.
            </h1>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Separate verifiable market context from social hype before forming a decision.
            </p>
          </div>

          {/* Continuous FINTRACE Market Visual Animation */}
          <MarketAnimation />
        </div>

        {/* Footer Guardrail */}
        <p className="relative z-10 text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
          Educational intelligence platform · No buy/sell recommendations or trade execution.
        </p>
      </section>

      {/* Right Auth Form Panel */}
      <main className="lg:col-span-6 p-gutter-lg lg:p-gutter-xl flex flex-col justify-between">
        <div className="flex justify-end">
          <ThemeToggle showLabels={true} />
        </div>

        <div className="w-full max-w-md mx-auto flex flex-col gap-gutter-lg py-gutter-xl">
          <div className="flex flex-col gap-gutter-xs">
            <h2 className="font-headline text-headline-lg font-bold" data-design-text-token="headline-lg">
              Welcome back
            </h2>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant">
              Sign in to your FinTrace workspace.
            </p>
          </div>

          {error && (
            <div className="p-3 rounded-DEFAULT bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-body-md">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-gutter-md">
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
                placeholder="Enter your password"
                className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface dark:placeholder:text-dark-outline outline-none focus:border-light-primary dark:focus:border-dark-primary focus-visible:ring-2 focus-visible:ring-light-primary dark:focus-visible:ring-dark-primary transition-colors"
              />
            </label>

            <div className="flex items-center justify-between text-body-md">
              <label className="inline-flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded-sm border-light-outline-variant dark:border-dark-outline-variant text-light-primary dark:text-dark-primary focus:ring-light-primary"
                />
                <span className="text-body-md">Remember me</span>
              </label>
              <a
                href="#forgot"
                onClick={(e) => {
                  e.preventDefault();
                  alert('Demonstration password reset link sent to ' + email);
                }}
                className="font-label text-label-lg text-light-on-primary-container dark:text-dark-on-primary-container hover:underline"
              >
                Forgot password?
              </a>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-DEFAULT bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-lg font-semibold hover:opacity-90 active:scale-[0.99] transition-all duration-state-change flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                  <span>Signing in...</span>
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <p className="text-center text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant">
            New to FinTrace?{' '}
            <Link
              to="/register"
              className="font-label text-label-lg text-light-on-primary-container dark:text-dark-on-primary-container hover:underline font-semibold"
            >
              Create an account
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
