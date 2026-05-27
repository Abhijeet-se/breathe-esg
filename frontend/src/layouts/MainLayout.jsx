/**
 * layouts/MainLayout.jsx
 * ──────────────────────
 * Shell layout for all authenticated pages.
 *
 * Structure:
 *   ┌──────────┬─────────────────────────────┐
 *   │ Sidebar  │  TopBar                      │
 *   │          ├─────────────────────────────┤
 *   │          │  <Outlet />  (page content)  │
 *   │          │                              │
 *   └──────────┴─────────────────────────────┘
 *
 * The sidebar is collapsible (240px ↔ 64px) and the toggle is
 * persisted for the session via React state.
 */

import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import './MainLayout.css';

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`layout ${collapsed ? 'layout--collapsed' : ''}`}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
      <div className="layout__main">
        <TopBar onToggleSidebar={() => setCollapsed((c) => !c)} />
        <main className="layout__content animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
