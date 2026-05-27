/**
 * pages/DashboardPage.jsx
 * ───────────────────────
 * Main dashboard with stat cards, emissions chart, and recent
 * activity feed. Uses staggered fade-in animations.
 *
 * Data is fetched from /api/dashboard/stats/ with a fallback
 * to realistic mock data when the backend is unavailable.
 */

import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
} from 'lucide-react';
import { dashboardAPI } from '../api/client';
import StatCard from '../components/StatCard';
import EmissionsChart from '../components/EmissionsChart';
import RecentActivity from '../components/RecentActivity';
import './DashboardPage.css';

/* ── Mock fallback data ───────────────────────────────────── */
const MOCK_STATS = {
  total_records: 1247,
  approved: 892,
  failed: 43,
  suspicious: 78,
  pending_review: 234,
  emissions_by_scope: [
    { scope: 'Scope 1', emissions: 42500 },
    { scope: 'Scope 2', emissions: 28300 },
    { scope: 'Scope 3', emissions: 67800 },
  ],
};

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await dashboardAPI.getStats();
        setStats(res.data);
      } catch {
        // Fallback to mock data when backend is unavailable
        setStats(MOCK_STATS);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  /* ── Loading skeleton ───────────────────────────────────── */
  if (loading) {
    return (
      <div className="dashboard">
        <div className="page-header">
          <div className="skeleton skeleton-heading" />
          <div className="skeleton skeleton-text" style={{ width: '40%' }} />
        </div>
        <div className="dashboard__stats">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton skeleton-card" />
          ))}
        </div>
        <div className="dashboard__charts">
          <div className="skeleton skeleton-card" style={{ height: 340 }} />
          <div className="skeleton skeleton-card" style={{ height: 340 }} />
        </div>
      </div>
    );
  }

  /* ── Stat card configuration ────────────────────────────── */
  const cards = [
    {
      title: 'Total Records',
      value: stats.total_records.toLocaleString(),
      icon: BarChart3,
      color: '#3b82f6',
      trend: { direction: 'up', value: '12%' },
    },
    {
      title: 'Approved',
      value: stats.approved.toLocaleString(),
      icon: CheckCircle2,
      color: '#10b981',
      trend: { direction: 'up', value: '8%' },
    },
    {
      title: 'Failed',
      value: stats.failed.toLocaleString(),
      icon: XCircle,
      color: '#ef4444',
      trend: { direction: 'down', value: '3%' },
    },
    {
      title: 'Suspicious',
      value: stats.suspicious.toLocaleString(),
      icon: AlertTriangle,
      color: '#f59e0b',
      trend: null,
    },
    {
      title: 'Pending Review',
      value: stats.pending_review.toLocaleString(),
      icon: Clock,
      color: '#8b5cf6',
      trend: { direction: 'up', value: '5%' },
    },
  ];

  return (
    <div className="dashboard">
      <div className="page-header animate-fade-in-up">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Overview of your ESG data ingestion pipeline
        </p>
      </div>

      {/* ── Stat Cards ──────────────────────────────────── */}
      <div className="dashboard__stats">
        {cards.map((card, i) => (
          <div
            key={card.title}
            className="animate-fade-in-up"
            style={{ animationDelay: `${(i + 1) * 60}ms`, opacity: 0 }}
          >
            <StatCard {...card} />
          </div>
        ))}
      </div>

      {/* ── Charts Row ──────────────────────────────────── */}
      <div className="dashboard__charts">
        <div className="animate-fade-in-up delay-4" style={{ opacity: 0 }}>
          <EmissionsChart data={stats.emissions_by_scope} />
        </div>
        <div className="animate-fade-in-up delay-5" style={{ opacity: 0 }}>
          <RecentActivity />
        </div>
      </div>
    </div>
  );
}
