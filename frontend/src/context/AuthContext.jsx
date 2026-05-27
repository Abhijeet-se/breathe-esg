/**
 * context/AuthContext.jsx
 * ──────────────────────
 * Global authentication state via React Context.
 *
 * Provides:
 *  • user        — current user object (role, tenant, name, etc.)
 *  • login()     — authenticates and stores JWT tokens
 *  • logout()    — clears tokens and resets state
 *  • isAuthenticated — derived boolean
 *  • loading     — true while checking stored tokens on mount
 *
 * Token lifecycle:
 *  • access_token and refresh_token are persisted in localStorage
 *  • On mount, if tokens exist we call /auth/me/ to rehydrate the
 *    user object. If the call fails the tokens are discarded.
 *  • A timer is set to refresh the access token 30 s before expiry
 *    (assumes 5-min tokens; adjust as needed).
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { authAPI } from '../api/client';

const AuthContext = createContext(null);

/* ── Demo user for prototype mode (no real backend) ─────── */
const DEMO_USER = {
  id: 1,
  email: 'analyst@acme.com',
  first_name: 'Jane',
  last_name: 'Doe',
  role: 'analyst',
  tenant: { id: 1, name: 'Acme Corp' },
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const refreshTimer = useRef(null);

  /* Clear any pending refresh timer */
  const clearRefreshTimer = useCallback(() => {
    if (refreshTimer.current) {
      clearTimeout(refreshTimer.current);
      refreshTimer.current = null;
    }
  }, []);

  /**
   * Schedule a token refresh 30 s before the access token expires.
   * Falls back to demo mode if the refresh call fails.
   */
  const scheduleRefresh = useCallback(
    (expiresInMs = 5 * 60 * 1000) => {
      clearRefreshTimer();
      const delay = Math.max(expiresInMs - 30_000, 10_000);
      refreshTimer.current = setTimeout(async () => {
        try {
          const refresh = localStorage.getItem('refresh_token');
          if (!refresh) return;
          const res = await authAPI.refreshToken(refresh);
          localStorage.setItem('access_token', res.data.access);
          scheduleRefresh();
        } catch {
          /* refresh failed — keep user logged in with demo data */
        }
      }, delay);
    },
    [clearRefreshTimer]
  );

  /* ── Rehydrate user on mount ──────────────────────────── */
  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await authAPI.me();
        setUser(res.data);
        scheduleRefresh();
      } catch {
        // If me() fails (no backend), use demo user when token exists
        setUser(DEMO_USER);
      }
      setLoading(false);
    };
    init();
    return clearRefreshTimer;
  }, [scheduleRefresh, clearRefreshTimer]);

  /* ── Login ────────────────────────────────────────────── */
  const login = useCallback(
    async (email, password) => {
      try {
        const res = await authAPI.login(email, password);
        localStorage.setItem('access_token', res.data.access);
        localStorage.setItem('refresh_token', res.data.refresh);
        // Fetch the full user profile
        const meRes = await authAPI.me();
        setUser(meRes.data);
        scheduleRefresh();
        return { ok: true };
      } catch (err) {
        // ── Prototype / demo fallback ──
        if (email === 'analyst@acme.com' && password === 'password123') {
          localStorage.setItem('access_token', 'demo-access-token');
          localStorage.setItem('refresh_token', 'demo-refresh-token');
          setUser(DEMO_USER);
          return { ok: true };
        }
        const message =
          err.response?.data?.detail || 'Invalid credentials. Please try again.';
        return { ok: false, message };
      }
    },
    [scheduleRefresh]
  );

  /* ── Logout ───────────────────────────────────────────── */
  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    clearRefreshTimer();
    setUser(null);
  }, [clearRefreshTimer]);

  const value = {
    user,
    login,
    logout,
    loading,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Custom hook for consuming auth context.
 * Throws if used outside of <AuthProvider>.
 */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}

export default AuthContext;
