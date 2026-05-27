/**
 * components/Sidebar.jsx
 * ──────────────────────
 * Collapsible sidebar navigation with lucide-react icons.
 *
 * Props:
 *  • collapsed  — boolean, whether the sidebar is in narrow mode
 *  • onToggle   — callback to toggle collapsed state
 *
 * Navigation items are defined in NAV_ITEMS. The active route is
 * determined via useLocation() and highlighted with a gradient
 * background and emerald accent.
 */

import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  ClipboardCheck,
  History,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import './Sidebar.css';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/upload', label: 'Upload Data', icon: Upload },
  { to: '/review', label: 'Review Queue', icon: ClipboardCheck },
  { to: '/audit', label: 'Audit Trail', icon: History },
];

const ADMIN_ITEMS = [
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();

  /** Check if a path matches the current route */
  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      {/* ── Brand ─────────────────────────────────────────── */}
      <div className="sidebar__brand">
        <span className="sidebar__logo">🌿</span>
        {!collapsed && <span className="sidebar__brand-text">Breathe</span>}
      </div>

      {/* ── Navigation ────────────────────────────────────── */}
      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={`sidebar__link ${isActive(item.to) ? 'sidebar__link--active' : ''}`}
            title={collapsed ? item.label : undefined}
          >
            <item.icon size={20} />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}

        <div className="sidebar__separator" />

        {ADMIN_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={`sidebar__link ${isActive(item.to) ? 'sidebar__link--active' : ''}`}
            title={collapsed ? item.label : undefined}
          >
            <item.icon size={20} />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* ── Collapse toggle ───────────────────────────────── */}
      <button className="sidebar__toggle" onClick={onToggle} aria-label="Toggle sidebar">
        {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </aside>
  );
}
