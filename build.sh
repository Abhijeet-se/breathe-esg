#!/usr/bin/env bash
# ============================================
# Render Build Script — Breathe ESG
# ============================================
# The pre-built React frontend is already in
# backend/frontend_dist/ (committed to Git).
# This script only needs to set up the backend.
# ============================================

set -o errexit

echo "==> Installing backend dependencies..."
pip install -r backend/requirements.txt

echo "==> Running Django migrations..."
cd backend
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Verifying frontend_dist exists..."
ls -la frontend_dist/ || echo "WARNING: frontend_dist not found!"
ls -la frontend_dist/index.html || echo "WARNING: index.html not found!"

echo "==> Creating sample data (if first deploy)..."
python manage.py create_sample_data 2>/dev/null || echo "Sample data exists, skipping."

echo "==> Build complete!"
