import React, { useState } from 'react';
import { useTheme } from '../hooks/useTheme';
import { SYNTHETIC_USER } from '../services/api';

export default function SettingsProfile() {
  const { theme, toggleTheme } = useTheme();
  const [name, setName] = useState(SYNTHETIC_USER.name);
  const [email, setEmail] = useState(SYNTHETIC_USER.email);
  const [role, setRole] = useState(SYNTHETIC_USER.role);
  const [landingPage, setLandingPage] = useState('/investor-dashboard');
  const [saved, setSaved] = useState(false);

  const [notifs, setNotifs] = useState({
    validationAlerts: true,
    contradictoryAlerts: true,
    weeklyDigest: false
  });

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <main className="flex-1 p-gutter-md lg:p-gutter-xl max-w-4xl w-full mx-auto flex flex-col gap-gutter-lg">
      <div className="flex flex-col gap-gutter-xs">
        <h1 className="font-display text-display-lg-mobile lg:text-display-lg font-bold" data-design-text-token="display-lg">
          Settings &amp; Profile
        </h1>
        <p className="text-body-lg text-light-on-surface-variant dark:text-dark-on-surface-variant">
          Manage your personal details, theme preference, notifications, and account security.
        </p>
      </div>

      {saved && (
        <div className="p-3 rounded-DEFAULT bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-label text-label-lg font-semibold flex items-center gap-2">
          <span className="material-symbols-outlined text-[20px]">check_circle</span>
          <span>Settings and preferences successfully saved.</span>
        </div>
      )}

      {/* Personal Information */}
      <section className="p-gutter-lg rounded-lg bg-light-surface dark:bg-dark-surface-container-low border border-light-outline-variant dark:border-dark-outline-variant shadow-sm flex flex-col gap-gutter-md">
        <h2 className="font-headline text-headline-md font-bold">Personal Information</h2>

        <div className="flex items-center gap-gutter-md pb-gutter-sm border-b border-light-outline-variant dark:border-dark-outline-variant">
          <div className="w-16 h-16 rounded-full bg-light-secondary dark:bg-dark-secondary text-light-on-secondary dark:text-dark-on-secondary flex items-center justify-center font-display text-headline-md font-bold shadow-sm">
            {SYNTHETIC_USER.initials}
          </div>
          <div>
            <h3 className="font-title text-title-md font-bold">{name}</h3>
            <p className="text-body-md text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
              {role} · Member since {SYNTHETIC_USER.joinedDate}
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
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-gutter-md py-2.5 rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface outline-none focus:border-light-primary dark:focus:border-dark-primary"
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

          {/* Default Landing */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-gutter-sm pb-gutter-md border-b border-light-outline-variant dark:border-dark-outline-variant">
            <div>
              <p className="font-label text-label-lg font-semibold">Default Workspace Landing</p>
              <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[13px]">
                Which screen to open immediately upon sign in.
              </p>
            </div>
            <select
              value={landingPage}
              onChange={(e) => setLandingPage(e.target.value)}
              className="px-3 py-2 rounded-DEFAULT bg-light-surface-container-low dark:bg-dark-surface-container border border-light-outline-variant dark:border-dark-outline-variant text-body-md text-light-on-surface dark:text-dark-on-surface outline-none cursor-pointer"
            >
              <option value="/investor-dashboard">Investor Dashboard (Default)</option>
              <option value="/analyse-claim">Analyse a Claim</option>
              <option value="/evidence-centre">Evidence Centre</option>
              <option value="/virtual-decision-lab">Virtual Decision Lab</option>
            </select>
          </div>

          {/* Notification toggles */}
          <div className="flex flex-col gap-3">
            <p className="font-label text-label-lg font-semibold">Notification Preferences</p>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-body-md">Notify when claim validation completes</span>
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
            className="px-gutter-lg py-2.5 rounded-DEFAULT bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-label text-label-lg font-semibold hover:opacity-90 transition-opacity shadow-sm"
          >
            Save Changes
          </button>
        </div>
      </section>
    </main>
  );
}
