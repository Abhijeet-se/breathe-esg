/**
 * pages/LoginPage.jsx
 * ───────────────────
 * Full-screen login page with animated gradient background,
 * glass-card form, and demo credentials hint.
 *
 * On success, redirects to "/" via React Router.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Leaf, Eye, EyeOff } from 'lucide-react';
import './LoginPage.css';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(email, password);

    if (result.ok) {
      navigate('/', { replace: true });
    } else {
      setError(result.message);
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      {/* Animated background grid */}
      <div className="login-page__bg">
        <div className="login-page__grid" />
        <div className="login-page__glow login-page__glow--1" />
        <div className="login-page__glow login-page__glow--2" />
      </div>

      {/* Login card */}
      <div className="login-card glass-card-strong animate-scale-in">
        {/* Logo */}
        <div className="login-card__logo">
          <span className="login-card__logo-icon">🌿</span>
          <h1 className="login-card__brand">Breathe</h1>
          <p className="login-card__tagline">ESG Data Ingestion Platform</p>
        </div>

        {/* Form */}
        <form className="login-card__form" onSubmit={handleSubmit}>
          {error && (
            <div className="login-card__error animate-fade-in">
              {error}
            </div>
          )}

          <div className="input-group">
            <label className="input-label" htmlFor="email">
              Email Address
            </label>
            <input
              id="email"
              className="input-field"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              autoFocus
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="password">
              Password
            </label>
            <div className="login-card__password-wrap">
              <input
                id="password"
                className="input-field"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                className="login-card__password-toggle"
                onClick={() => setShowPassword((s) => !s)}
                tabIndex={-1}
                aria-label="Toggle password visibility"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg login-card__submit"
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : 'Sign In'}
          </button>
        </form>

        {/* Demo hint */}
        <div className="login-card__demo">
          <span className="login-card__demo-label">Demo credentials</span>
          <code>analyst@acme.com / password123</code>
        </div>
      </div>
    </div>
  );
}
