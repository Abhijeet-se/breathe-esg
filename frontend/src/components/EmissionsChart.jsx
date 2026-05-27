/**
 * components/EmissionsChart.jsx
 * ─────────────────────────────
 * Recharts BarChart showing total emissions by scope (1, 2, 3).
 * Wrapped in a glass card.
 *
 * Props:
 *  • data — array of { scope: string, emissions: number }
 *           If omitted, uses realistic mock data.
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import './EmissionsChart.css';

const MOCK_DATA = [
  { scope: 'Scope 1', emissions: 42500 },
  { scope: 'Scope 2', emissions: 28300 },
  { scope: 'Scope 3', emissions: 67800 },
];

const BAR_COLORS = ['#f97316', '#3b82f6', '#8b5cf6'];

/* Custom tooltip matching our design system */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip glass-card-strong">
      <p className="chart-tooltip__label">{label}</p>
      <p className="chart-tooltip__value">
        {Number(payload[0].value).toLocaleString()} kg CO₂e
      </p>
    </div>
  );
}

export default function EmissionsChart({ data }) {
  const chartData = data || MOCK_DATA;

  return (
    <div className="emissions-chart glass-card">
      <h3 className="emissions-chart__title">Emissions by Scope</h3>
      <div className="emissions-chart__body">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} barSize={48} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" vertical={false} />
            <XAxis
              dataKey="scope"
              tick={{ fill: '#94a3b8', fontSize: 13 }}
              axisLine={{ stroke: 'rgba(148,163,184,0.1)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(148,163,184,0.06)' }} />
            <Bar dataKey="emissions" radius={[6, 6, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
