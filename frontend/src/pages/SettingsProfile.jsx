import React, { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { api } from '../services/api';

export default function SettingsProfile() {
  const { theme, toggleTheme } = useTheme();
  const cachedUser = api.getCurrentUser();
  const [name, setName] = useState(cachedUser?.name || '');
  const [email, setEmail] = useState(cachedUser?.email || '');
  const [role, setRole] = useState(cachedUser?.role || 'Retail Investor & Decision Analyst');
  const [initials, setInitials] = useState(cachedUser?.initials || 'FT');
  const [joinedDate, setJoinedDate] = useState('November 2026');
  const [landingPage, setLandingPage] = useState('/investor-dashboard');
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    api.getMe().then((user) => {
      if (isMounted && user) {
        setName(user.name);
        setEmail(user.email);
        setRole(user.role || 'Retail Investor & Decision Analyst');
        setInitials(user.initials || 'FT');
        if (user.created_at) {
          setJoinedDate(new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }));
        }
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const [notifs, setNotifs] = useState({
    validationAlerts: true,
    contradictoryAlerts: true,
    weeklyDigest: false
  });

  const handleSave = async (e) => {
    if (e) e.preventDefault();
    setSaveError(null);
    try {
      const updated = await api.updateMe({ name, role });
      if (updated) {
        setName(updated.name);
        setRole(updated.role || role);
        setInitials(updated.initials || 'FT');
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setSaveError(err.message || 'Failed to persist settings changes.');
      setTimeout(() => setSaveError(null), 4000);
    }
  };

  return (
    <main className="flex-1 p-gutter-md lg:p-gutter-xl max-w-4xl w-full mx-auto flex flex-col gap-gutter-lg">
      <div className="flex flex-col gap-gutter-xs">
        <h1 className="font-display text-display-lg-mobile lg:text-display-lg font-bold" data-design-text-token="display-lg">
          Settings &amp; Profile
        </h1>
        <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
          Manage your personal details, theme preference, notifications, and persistent account profile.
        </p>
      </div>

      {saved && (
        <div className="p-3 rounded-DEFAULT bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-label text-label-lg font-semibold flex items-center gap-2">
          <span className="material-symbols-outlined text-[20px]">check_circle</span>
          <span>Settings and preferences successfully saved to database.</span>
        </div>
      )}

      {saveError && (
        <div className="p-3 rounded-DEFAULT bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 font-label text-label-lg font-semibold flex items-center gap-2">
          <span className="material-symbols-outlined text-[20px]">error</span>
          <span>{saveError}</span>
        </div>
      )}

      {/* Personal Information */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant shadow-sm flex flex-col gap-gutter-md">
        <h2 className="font-headline text-headline-md font-bold">Personal Information</h2>

        <div className="flex items-center gap-gutter-md pb-gutter-sm border-b border-light-outline-variant dark:border-dark-outline-variant">
          <div className="w-16 h-16 rounded-full bg-light-secondary dark:bg-dark-secondary text-light-on-secondary dark:text-dark-on-secondary flex items-center justify-center font-display text-headline-md font-bold shadow-sm">
            {initials}
          </div>
          <div>
            <h3 className="font-title text-title-md font-bold">{name || 'Investor User'}</h3>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
              {role} · Member since {joinedDate}
            </p>
          </div>
        </div>

        <form onSubmit={handleSave} className="grid grid-cols-1 md:grid-cols-2 gap-gutter-md">
          <label className="flex flex-col gap-gutter-xs">
            <span className="font-label text-label-lg font-semibold">Display Name</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface outline-none focus:border-light-primary dark:focus:border-dark-primary"
            />
          </label>

          <label className="flex flex-col gap-gutter-xs">
            <span className="font-label text-label-lg font-semibold">Email Address</span>
            <input
              type="email"
              value={email}
              disabled
              className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface-container-low/50 dark:bg-dark-surface-container/50 border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-outline dark:text-dark-outline outline-none cursor-not-allowed"
            />
          </label>

          <label className="flex flex-col gap-gutter-xs md:col-span-2">
            <span className="font-label text-label-lg font-semibold">Analytical Persona / Role</span>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface outline-none focus:border-light-primary dark:focus:border-dark-primary"
            />
          </label>
        </form>
      </section>

      {/* Account & Application Preferences */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant shadow-sm flex flex-col gap-gutter-md">
        <h2 className="font-headline text-headline-md font-bold">Account &amp; Application Preferences</h2>

        <div className="flex flex-col gap-gutter-md">
          {/* Theme Choice */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-gutter-sm pb-gutter-md border-b border-light-outline-variant dark:border-dark-outline-variant">
            <div>
              <p className="font-label text-label-lg font-semibold">Theme Mode</p>
              <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                Toggle between Light (Sky-Blue & Lavender) and Dark (Charcoal & Magenta).
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => toggleTheme('light')}
                className={`px-3 py-1.5 rounded-DEFAULT font-label text-label-sm font-semibold flex items-center gap-1.5 border transition-all ${
                  theme === 'light'
                    ? 'bg-light-primary text-light-on-primary border-transparent shadow-sm'
                    : 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant text-light-on-surface dark:text-dark-on-surface'
                }`}
              >
                <span className="material-symbols-outlined text-[16px]">light_mode</span>
                <span>Light</span>
              </button>
              <button
                type="button"
                onClick={() => toggleTheme('dark')}
                className={`px-3 py-1.5 rounded-DEFAULT font-label text-label-sm font-semibold flex items-center gap-1.5 border transition-all ${
                  theme === 'dark'
                    ? 'bg-dark-primary text-dark-on-primary border-transparent shadow-sm'
                    : 'bg-light-surface-container-low dark:bg-dark-surface-container border-light-outline-variant dark:border-dark-outline-variant text-light-on-surface dark:text-dark-on-surface'
                }`}
              >
                <span className="material-symbols-outlined text-[16px]">dark_mode</span>
                <span>Dark</span>
              </button>
            </div>
          </div>

          {/* Notifications */}
          <div className="flex flex-col gap-gutter-sm">
            <h3 className="font-title text-title-md font-semibold">Notifications</h3>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-body-md">Alert on claim validation completion</span>
              <input
                type="checkbox"
                checked={notifs.validationAlerts}
                onChange={(e) => setNotifs({ ...notifs, validationAlerts: e.target.checked })}
                className="rounded-sm border-light-outline-variant dark:border-dark-outline-variant text-light-primary dark:text-dark-primary"
              />
            </label>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-body-md">Alert when contradictory filings or supply chokepoints are flagged</span>
              <input
                type="checkbox"
                checked={notifs.contradictoryAlerts}
                onChange={(e) => setNotifs({ ...notifs, contradictoryAlerts: e.target.checked })}
                className="rounded-sm border-light-outline-variant dark:border-dark-outline-variant text-light-primary dark:text-dark-primary"
              />
            </label>
          </div>
        </div>

        <div className="pt-2 border-t border-light-outline-variant dark:border-dark-outline-variant flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            className="px-gutter-lg py-2.5 rounded-DEFAULT bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-lg font-semibold hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
          >
            Save Changes
          </button>
        </div>
      </section>
    </main>
  );
}
