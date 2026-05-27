/**
 * App.jsx
 * ───────
 * Root component — sets up React Router and auth-gated routing.
 *
 * Route structure:
 *   /login          → LoginPage   (public)
 *   /               → Dashboard   (protected, inside MainLayout)
 *   /upload         → UploadPage
 *   /review         → ReviewQueuePage
 *   /review/:id     → RecordDetailPage
 *   /audit          → AuditTrailPage
 *   *               → redirect to /
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import ReviewQueuePage from './pages/ReviewQueuePage';
import RecordDetailPage from './pages/RecordDetailPage';
import AuditTrailPage from './pages/AuditTrailPage';
import MainLayout from './layouts/MainLayout';

/* ── Protect routes that require auth ─────────────────────── */
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-base)',
      }}>
        <div className="spinner" style={{ width: 32, height: 32 }} />
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Public */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
      />

      {/* Protected — wrapped in MainLayout */}
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="review" element={<ReviewQueuePage />} />
        <Route path="review/:id" element={<RecordDetailPage />} />
        <Route path="audit" element={<AuditTrailPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
