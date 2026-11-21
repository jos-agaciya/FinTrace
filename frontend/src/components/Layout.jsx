import React, { useState, useEffect, useRef } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';
import { api } from '../services/api';

export default function Layout({ children }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentUser, setCurrentUser] = useState(() => api.getCurrentUser() || null);
  
  const notifRef = useRef(null);
  const profileRef = useRef(null);
  
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    api.getMe().then((user) => {
      if (isMounted && user) {
        setCurrentUser(user);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSignOut = async (e) => {
    if (e) e.preventDefault();
    await api.logout();
    navigate('/login');
  };

  // Close dropdowns on outside click or Escape key
  useEffect(() => {
    function handleClickOutside(event) {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setNotifOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setNotifOpen(false);
        setProfileOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const handleSearch = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      navigate(`/analysis-reports?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
    }
  };

  const navItems = [
    {
      group: 'Overview',
      items: [
        { path: '/investor-dashboard', label: 'Investor Dashboard', icon: 'space_dashboard' }
      ]
    },
    {
      group: 'Analysis',
      items: [
        { path: '/analyse-claim', label: 'Analyse a Claim', icon: 'query_stats' },
        { path: '/analysis-reports', label: 'Analysis Reports', icon: 'description' },
        { path: '/evidence-centre', label: 'Evidence Centre', icon: 'fact_check' }
      ]
    },
    {
      group: 'Learning',
      items: [
        { path: '/virtual-decision-lab', label: 'Virtual Decision Lab', icon: 'science' },
        { path: '/decision-intelligence', label: 'Decision Intelligence', icon: 'psychology' }
      ]
    }
  ];

  // Derive breadcrumb from current route
  const getBreadcrumb = () => {
    const p = location.pathname;
    if (p.includes('investor-dashboard')) return { section: 'Overview', page: 'Investor Dashboard' };
    if (p.includes('analyse-claim')) return { section: 'Analysis', page: 'Analyse a Claim' };
    if (p.includes('claim-analysis-report')) return { section: 'Analysis', page: 'Claim Analysis Report' };
    if (p.includes('analysis-reports')) return { section: 'Analysis', page: 'Analysis Reports' };
    if (p.includes('evidence-centre')) return { section: 'Analysis', page: 'Evidence Centre' };
    if (p.includes('virtual-decision-lab')) return { section: 'Learning', page: 'Virtual Decision Lab' };
    if (p.includes('decision-intelligence')) return { section: 'Learning', page: 'Decision Intelligence' };
    if (p.includes('settings')) return { section: 'Preferences', page: 'Settings & Profile' };
    return { section: 'Overview', page: 'Investor Dashboard' };
  };

  const breadcrumb = getBreadcrumb();

  return (
    <div className="relative h-screen w-screen overflow-hidden flex bg-light-surface text-light-on-surface dark:bg-dark-surface dark:text-dark-on-surface transition-colors duration-theme-switch">
      {/* Mobile Drawer Backdrop */}
      {mobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-light-on-surface/30 dark:bg-dark-surface/60 z-40 lg:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Completely Fixed 100vh Left Sidebar */}
      <aside
        id="app-sidebar"
        className={`fixed lg:static inset-y-0 left-0 z-40 h-screen ${
          sidebarCollapsed ? 'w-20' : 'w-64'
        } bg-light-surface/90 dark:bg-dark-surface-container-low/95 backdrop-blur-xl border-r border-light-outline-variant/80 dark:border-dark-outline-variant/60 flex flex-col justify-between transition-all duration-theme-switch overflow-hidden shrink-0 ${
          mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Top: Logo & Main Navigation */}
        <div className="p-gutter-md flex flex-col gap-gutter-lg overflow-y-auto overflow-x-hidden">
          {/* Brand Header */}
          <div className="flex items-center justify-between gap-gutter-sm px-2 py-1 shrink-0">
            <NavLink
              to="/investor-dashboard"
              className="flex items-center gap-gutter-sm group"
              onClick={() => setMobileSidebarOpen(false)}
            >
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-light-primary to-sky-400 dark:from-dark-primary dark:to-purple-400 flex items-center justify-center text-light-on-primary dark:text-dark-on-primary shrink-0 shadow-md shadow-light-primary/20 dark:shadow-dark-primary/20 group-hover:scale-105 transition-transform">
                <span className="material-symbols-outlined text-[22px]" aria-hidden="true">
                  analytics
                </span>
              </div>
              {!sidebarCollapsed && (
                <div className="sidebar-label flex flex-col overflow-hidden">
                  <span className="font-display text-title-md tracking-tight text-light-on-surface dark:text-dark-on-surface font-bold">
                    FINTRACE
                  </span>
                  <span className="font-mono text-mono-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px]">
                    Decision Compiler
                  </span>
                </div>
              )}
            </NavLink>
            <button
              type="button"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              aria-label="Collapse sidebar"
              className="hidden lg:inline-flex items-center justify-center w-8 h-8 rounded-full text-light-on-surface-variant dark:text-dark-on-surface-variant hover:bg-light-primary-container/60 dark:hover:bg-dark-surface-container transition-colors duration-state-change"
            >
              <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
                {sidebarCollapsed ? 'dock_to_right' : 'dock_to_left'}
              </span>
            </button>
          </div>

          {/* Navigation Groups */}
          <nav aria-label="Primary Navigation" className="flex flex-col gap-gutter-md">
            {navItems.map((group) => (
              <div key={group.group} className="flex flex-col gap-1">
                {!sidebarCollapsed && (
                  <span className="sidebar-label px-3 font-label text-label-sm uppercase tracking-wider text-light-on-surface-variant dark:text-dark-on-surface-variant text-[11px] font-semibold">
                    {group.group}
                  </span>
                )}
                {group.items.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileSidebarOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-label text-label-lg transition-all duration-state-change ${
                        isActive
                          ? 'bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-semibold shadow-sm'
                          : 'text-light-on-surface-variant dark:text-dark-on-surface-variant hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container hover:text-light-on-surface dark:hover:text-dark-on-surface'
                      }`
                    }
                    title={sidebarCollapsed ? item.label : undefined}
                  >
                    <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                      {item.icon}
                    </span>
                    {!sidebarCollapsed && <span>{item.label}</span>}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
        </div>

        {/* Bottom: Settings & Sign Out Permanently Visible at Bottom */}
        <div className="p-gutter-md border-t border-light-outline-variant/80 dark:border-dark-outline-variant/60 flex flex-col gap-1.5 shrink-0 bg-light-surface/40 dark:bg-dark-surface-container-low/40">
          <NavLink
            to="/settings"
            onClick={() => setMobileSidebarOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-label text-label-lg transition-all duration-state-change ${
                isActive
                  ? 'bg-light-primary text-light-on-primary dark:bg-dark-primary dark:text-dark-on-primary font-semibold shadow-sm'
                  : 'text-light-on-surface-variant dark:text-dark-on-surface-variant hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container hover:text-light-on-surface dark:hover:text-dark-on-surface'
              }`
            }
            title={sidebarCollapsed ? 'Settings' : undefined}
          >
            <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
              settings
            </span>
            {!sidebarCollapsed && <span>Settings</span>}
          </NavLink>

          <button
            type="button"
            onClick={handleSignOut}
            className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 dark:hover:bg-rose-500/15 font-label text-label-lg font-medium transition-all duration-state-change w-full text-left"
            title={sidebarCollapsed ? 'Sign out' : undefined}
          >
            <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
              logout
            </span>
            {!sidebarCollapsed && <span>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Right Content Area: Independent Vertical Scroll */}
      <div className="flex-1 h-screen flex flex-col overflow-y-auto overflow-x-hidden min-w-0">
        {/* Sticky Top Navigation (Stays pinned at top of right scrollable area) */}
        <header className="sticky top-0 z-30 h-16 shrink-0 px-gutter-md lg:px-gutter-lg border-b border-light-outline-variant/80 dark:border-dark-outline-variant/60 bg-light-surface/90 dark:bg-dark-surface/90 backdrop-blur-xl flex items-center justify-between gap-gutter-md">
          <div className="flex items-center gap-gutter-md min-w-0">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              aria-label="Open navigation"
              className="lg:hidden inline-flex items-center justify-center w-10 h-10 rounded-full border border-light-outline-variant/80 dark:border-dark-outline-variant/60 text-light-on-surface dark:text-dark-on-surface hover:bg-light-surface-container-low dark:hover:bg-dark-surface-container transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                menu
              </span>
            </button>
            <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant">
              <span>{breadcrumb.section}</span>
              <span aria-hidden="true">/</span>
              <span className="text-light-on-surface dark:text-dark-on-surface font-semibold">
                {breadcrumb.page}
              </span>
            </nav>
          </div>

          <div className="flex items-center gap-gutter-sm sm:gap-gutter-md">
            {/* Global Search Bar (Organic Pill) */}
            <div className="hidden md:flex relative items-center w-64 lg:w-72">
              <span
                className="material-symbols-outlined absolute left-3.5 text-[18px] text-light-on-surface-variant dark:text-dark-on-surface-variant pointer-events-none"
                aria-hidden="true"
              >
                search
              </span>
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearch}
                placeholder="Search claims, tickers, reports..."
                className="w-full pl-10 pr-4 py-2 rounded-full bg-light-surface-container-low/90 dark:bg-dark-surface-container/90 border border-light-outline-variant/80 dark:border-dark-outline-variant/60 text-body-md text-light-on-surface dark:text-dark-on-surface placeholder:text-light-outline dark:placeholder:text-dark-outline focus:border-light-primary dark:focus:border-dark-primary outline-none focus:ring-2 focus:ring-light-primary/30 dark:focus:ring-dark-primary/30 transition-all shadow-xs"
              />
            </div>

            {/* Theme Switcher */}
            <ThemeToggle showLabels={true} />

            {/* Notifications Dropdown (Anchor + Proper Layered Glassmorphism) */}
            <div className="relative" ref={notifRef}>
              <button
                type="button"
                onClick={() => {
                  setNotifOpen(!notifOpen);
                  setProfileOpen(false);
                }}
                aria-expanded={notifOpen}
                aria-label="Notifications"
                className={`relative inline-flex items-center justify-center w-10 h-10 rounded-full border transition-all duration-state-change ${
                  notifOpen
                    ? 'border-light-primary dark:border-dark-primary bg-light-primary-container/40 dark:bg-dark-primary-container/40 text-light-primary dark:text-dark-primary'
                    : 'border-light-outline-variant/80 dark:border-dark-outline-variant/60 bg-light-surface dark:bg-dark-surface-container/80 text-light-on-surface dark:text-dark-on-surface hover:border-light-primary dark:hover:border-dark-primary'
                }`}
              >
                <span className="material-symbols-outlined text-[20px]" aria-hidden="true">
                  notifications
                </span>
                <span className="absolute top-2 right-2 w-2.5 h-2.5 rounded-full bg-light-primary dark:bg-dark-primary ring-2 ring-light-surface dark:ring-dark-surface" />
              </button>

              {/* Layered Floating Notification Panel */}
              {notifOpen && (
                <div
                  className="glass-dropdown absolute right-0 top-full mt-2.5 w-80 sm:w-96 p-gutter-md rounded-2xl z-50 flex flex-col gap-gutter-sm animate-in fade-in zoom-in-95 duration-150"
                  role="dialog"
                  aria-label="Notifications Panel"
                >
                  <div className="flex items-center justify-between pb-2 border-b border-light-outline-variant/60 dark:border-dark-outline-variant/60">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-[18px] text-light-primary dark:text-dark-primary">
                        notifications_active
                      </span>
                      <span className="font-title text-title-md font-bold text-light-on-surface dark:text-dark-on-surface">
                        Notifications
                      </span>
                    </div>
                    <span className="font-mono text-mono-sm px-2 py-0.5 rounded-full bg-light-primary-container text-light-on-primary-container dark:bg-dark-primary-container dark:text-dark-on-primary-container text-[11px] font-semibold">
                      2 unread
                    </span>
                  </div>

                  <div className="flex flex-col gap-2 max-h-80 overflow-y-auto">
                    <div className="glass-nested p-3 rounded-xl flex items-start gap-3 hover:bg-light-primary-container/30 dark:hover:bg-dark-surface-container-high transition-colors cursor-pointer">
                      <div className="w-8 h-8 rounded-full bg-amber-500/15 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                        <span className="material-symbols-outlined text-[18px]">warning</span>
                      </div>
                      <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                        <p className="text-body-md font-semibold text-light-on-surface dark:text-dark-on-surface">
                          MGS claim validation completed
                        </p>
                        <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
                          3 missing risk disclosures flagged · 14m ago
                        </p>
                      </div>
                    </div>

                    <div className="glass-nested p-3 rounded-xl flex items-start gap-3 hover:bg-light-primary-container/30 dark:hover:bg-dark-surface-container-high transition-colors cursor-pointer">
                      <div className="w-8 h-8 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                        <span className="material-symbols-outlined text-[18px]">trending_up</span>
                      </div>
                      <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                        <p className="text-body-md font-semibold text-light-on-surface dark:text-dark-on-surface">
                          New independent assessment ready
                        </p>
                        <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px]">
                          Score improved +26 pts from baseline · Yesterday
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-light-outline-variant/60 dark:border-dark-outline-variant/60 flex items-center justify-between text-label-sm">
                    <button
                      type="button"
                      onClick={() => setNotifOpen(false)}
                      className="text-light-primary dark:text-dark-primary font-semibold hover:underline"
                    >
                      Mark all as read
                    </button>
                    <button
                      type="button"
                      onClick={() => setNotifOpen(false)}
                      className="text-light-on-surface-variant dark:text-dark-on-surface-variant hover:text-light-on-surface dark:hover:text-dark-on-surface font-medium"
                    >
                      Close
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* User Profile Dropdown (Properly Anchored Floating Panel) */}
            <div className="relative" ref={profileRef}>
              <button
                type="button"
                onClick={() => {
                  setProfileOpen(!profileOpen);
                  setNotifOpen(false);
                }}
                aria-expanded={profileOpen}
                aria-label="User profile menu"
                className={`flex items-center gap-2 pl-1.5 pr-3 py-1.5 rounded-full border transition-all duration-state-change ${
                  profileOpen
                    ? 'border-light-primary dark:border-dark-primary bg-light-primary-container/40 dark:bg-dark-primary-container/40'
                    : 'border-light-outline-variant/80 dark:border-dark-outline-variant/60 bg-light-surface dark:bg-dark-surface-container/80 hover:border-light-primary dark:hover:border-dark-primary'
                }`}
              >
                <span className="w-7 h-7 rounded-full bg-gradient-to-tr from-light-secondary to-purple-300 dark:from-dark-secondary dark:to-indigo-300 text-light-on-secondary dark:text-dark-on-secondary flex items-center justify-center font-label text-label-sm font-bold shadow-xs">
                  {currentUser?.initials || 'FT'}
                </span>
                <span className="hidden sm:inline font-label text-label-lg font-semibold text-light-on-surface dark:text-dark-on-surface">
                  {(currentUser?.name || 'Investor').split(' ')[0]}
                </span>
                <span className={`material-symbols-outlined text-[18px] transition-transform duration-200 ${profileOpen ? 'rotate-180' : ''}`} aria-hidden="true">
                  expand_more
                </span>
              </button>

              {/* Layered Floating Profile Menu */}
              {profileOpen && (
                <div
                  className="glass-dropdown absolute right-0 top-full mt-2.5 w-64 p-2 rounded-2xl z-50 flex flex-col gap-1 animate-in fade-in zoom-in-95 duration-150"
                  role="menu"
                  aria-label="User profile dropdown"
                >
                  <div className="p-3 border-b border-light-outline-variant/60 dark:border-dark-outline-variant/60 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-light-secondary to-purple-300 dark:from-dark-secondary dark:to-indigo-300 text-light-on-secondary dark:text-dark-on-secondary flex items-center justify-center font-label text-label-lg font-bold shrink-0 shadow-sm">
                      {currentUser?.initials || 'FT'}
                    </div>
                    <div className="flex flex-col min-w-0">
                      <p className="font-label text-label-lg font-bold text-light-on-surface dark:text-dark-on-surface truncate">
                        {currentUser?.name || 'Investor'}
                      </p>
                      <p className="text-label-sm text-light-on-surface-variant dark:text-dark-on-surface-variant text-[12px] truncate">
                        {currentUser?.email || ''}
                      </p>
                    </div>
                  </div>

                  <div className="py-1 flex flex-col gap-1">
                    <NavLink
                      to="/settings"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-body-md font-medium text-light-on-surface dark:text-dark-on-surface hover:bg-light-primary-container/40 dark:hover:bg-dark-surface-container-high transition-colors"
                      role="menuitem"
                    >
                      <span className="material-symbols-outlined text-[18px] text-light-primary dark:text-dark-primary">
                        person
                      </span>
                      <span>User Profile</span>
                    </NavLink>

                    <NavLink
                      to="/settings"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-body-md font-medium text-light-on-surface dark:text-dark-on-surface hover:bg-light-primary-container/40 dark:hover:bg-dark-surface-container-high transition-colors"
                      role="menuitem"
                    >
                      <span className="material-symbols-outlined text-[18px] text-light-primary dark:text-dark-primary">
                        settings
                      </span>
                      <span>Settings &amp; Preferences</span>
                    </NavLink>
                  </div>

                  <div className="pt-1 border-t border-light-outline-variant/60 dark:border-dark-outline-variant/60">
                    <button
                      type="button"
                      onClick={(e) => {
                        setProfileOpen(false);
                        handleSignOut(e);
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-body-md font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 transition-colors text-left"
                      role="menuitem"
                    >
                      <span className="material-symbols-outlined text-[18px]">
                        logout
                      </span>
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Independently Scrollable Dashboard / Page Content */}
        <div className="flex-1 min-w-0">
          {children}
        </div>
      </div>
    </div>
  );
}
