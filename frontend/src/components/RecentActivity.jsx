/**
 * components/RecentActivity.jsx
 * ─────────────────────────────
 * Shows the 10 most recent batch uploads in a compact list.
 * Wrapped in a glass card.
 *
 * Props:
 *  • items — array of { id, filename, status, records, created_at }
 *            Falls back to mock data.
 */

import React from 'react';
import { FileSpreadsheet } from 'lucide-react';
import StatusBadge from './StatusBadge';
import './RecentActivity.css';

const MOCK_ITEMS = [
  { id: 1, filename: 'fuel_log_q1_2024.csv', status: 'approved', records: 142, created_at: '2024-03-15T10:30:00Z' },
  { id: 2, filename: 'electricity_mar.xlsx', status: 'parsed', records: 87, created_at: '2024-03-14T14:20:00Z' },
  { id: 3, filename: 'travel_expenses.csv', status: 'suspicious', records: 56, created_at: '2024-03-13T09:10:00Z' },
  { id: 4, filename: 'fleet_diesel_feb.csv', status: 'approved', records: 210, created_at: '2024-03-12T16:45:00Z' },
  { id: 5, filename: 'office_energy.xlsx', status: 'failed', records: 0, created_at: '2024-03-11T11:00:00Z' },
  { id: 6, filename: 'flights_q1.csv', status: 'uploaded', records: 34, created_at: '2024-03-10T08:30:00Z' },
  { id: 7, filename: 'natural_gas_jan.csv', status: 'approved', records: 95, created_at: '2024-03-09T13:15:00Z' },
  { id: 8, filename: 'company_cars.xlsx', status: 'parsed', records: 178, created_at: '2024-03-08T10:00:00Z' },
  { id: 9, filename: 'rail_travel.csv', status: 'approved', records: 22, created_at: '2024-03-07T15:40:00Z' },
  { id: 10, filename: 'heating_oil.csv', status: 'suspicious', records: 63, created_at: '2024-03-06T09:20:00Z' },
];

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function RecentActivity({ items }) {
  const list = items || MOCK_ITEMS;

  return (
    <div className="recent-activity glass-card">
      <h3 className="recent-activity__title">Recent Uploads</h3>
      <ul className="recent-activity__list">
        {list.map((item) => (
          <li key={item.id} className="recent-activity__item">
            <div className="recent-activity__icon">
              <FileSpreadsheet size={18} />
            </div>
            <div className="recent-activity__info">
              <span className="recent-activity__filename">{item.filename}</span>
              <span className="recent-activity__meta">
                {item.records} records · {timeAgo(item.created_at)}
              </span>
            </div>
            <StatusBadge status={item.status} />
          </li>
        ))}
      </ul>
    </div>
  );
}
