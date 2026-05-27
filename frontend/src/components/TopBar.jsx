/**
 * components/TopBar.jsx
 * ─────────────────────
 * Persistent top bar showing:
 *  • Hamburger toggle for sidebar (on mobile / as alt control)
 *  • Page breadcrumb area
 *  • Tenant name
 *  • User avatar + name
 *  • Logout button
 */

import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, Menu, Bell } from 'lucide-react';
import './TopBar.css';

export default function TopBar({ onToggleSidebar }) {
  const { user, logout } = useAuth();

  const initials = user
    ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
    : '??';

  return (
    <header className="topbar">
      <div className="topbar__left">
        <button
          className="btn-icon topbar__menu-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
        >
          <Menu size={20} />
        </button>
      </div>

      <div className="topbar__right">
        {/* Tenant badge */}
        <div className="topbar__tenant">
          {user?.tenant?.name || 'Acme Corp'}
        </div>

        {/* Notifications bell (placeholder) */}
        <button className="btn-icon" aria-label="Notifications">
          <Bell size={18} />
        </button>

        {/* User info */}
        <div className="topbar__user">
          <div className="topbar__avatar">{initials}</div>
          <span className="topbar__user-name">
            {user ? `${user.first_name} ${user.last_name}` : 'User'}
          </span>
        </div>

        {/* Logout */}
        <button className="btn-icon" onClick={logout} aria-label="Logout" title="Sign out">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
