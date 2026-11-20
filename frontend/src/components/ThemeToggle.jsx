import React from 'react';
import { useTheme } from '../hooks/useTheme';

export default function ThemeToggle({ showLabels = true }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div
      role="group"
      aria-label="Theme switcher"
      className="inline-flex items-center p-1 rounded-full bg-light-surface-container-low/90 dark:bg-dark-surface-container/90 border border-light-outline-variant/80 dark:border-dark-outline-variant/60 shadow-xs"
    >
      <button
        type="button"
        onClick={() => toggleTheme('light')}
        id="btn-theme-light"
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-label text-label-sm font-semibold transition-all duration-theme-switch ${
          theme === 'light'
            ? 'bg-light-surface text-light-on-surface shadow-sm'
            : 'bg-transparent text-light-on-surface-variant dark:text-dark-on-surface-variant hover:text-light-on-surface dark:hover:text-dark-on-surface'
        }`}
      >
        <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
          light_mode
        </span>
        {showLabels && <span className="hidden sm:inline">Light</span>}
      </button>
      <button
        type="button"
        onClick={() => toggleTheme('dark')}
        id="btn-theme-dark"
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-label text-label-sm font-semibold transition-all duration-theme-switch ${
          theme === 'dark'
            ? 'bg-dark-surface-container-high text-dark-on-surface shadow-sm'
            : 'bg-transparent text-light-on-surface-variant dark:text-dark-on-surface-variant hover:text-light-on-surface dark:hover:text-dark-on-surface'
        }`}
      >
        <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
          dark_mode
        </span>
        {showLabels && <span className="hidden sm:inline">Dark</span>}
      </button>
    </div>
  );
}
