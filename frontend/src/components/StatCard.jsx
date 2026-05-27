/**
 * components/StatCard.jsx
 * ───────────────────────
 * Dashboard metric card with glassmorphism styling.
 *
 * Props:
 *  • title   — label text (e.g. "Total Records")
 *  • value   — number or string
 *  • icon    — lucide-react icon component
 *  • color   — CSS color string for accent border / icon
 *  • trend   — optional { direction: 'up' | 'down', value: string }
 */

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import './StatCard.css';

export default function StatCard({ title, value, icon: Icon, color, trend }) {
  return (
    <div className="stat-card glass-card" style={{ '--accent': color }}>
      <div className="stat-card__header">
        <div className="stat-card__icon" style={{ color }}>
          {Icon && <Icon size={22} />}
        </div>
        {trend && (
          <span
            className={`stat-card__trend ${
              trend.direction === 'up' ? 'stat-card__trend--up' : 'stat-card__trend--down'
            }`}
          >
            {trend.direction === 'up' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {trend.value}
          </span>
        )}
      </div>
      <div className="stat-card__value">{value}</div>
      <div className="stat-card__title">{title}</div>
    </div>
  );
}
