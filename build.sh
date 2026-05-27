#!/usr/bin/env bash
# ============================================
# Render Build Script — Breathe ESG
# ============================================
# Called by Render during deployment.
# Builds frontend, installs backend deps,
# copies SPA into Django's static pipeline,
# then runs migrations and collectstatic.
# ============================================

set -o errexit  # Exit on error

echo "==> Installing backend dependencies..."
pip install -r backend/requirements.txt

echo "==> Installing frontend dependencies..."
cd frontend
npm install

echo "==> Building frontend..."
npm run build
cd ..

echo "==> Copying frontend build to backend/frontend_dist..."
rm -rf backend/frontend_dist
cp -r frontend/dist backend/frontend_dist

echo "==> Contents of frontend_dist:"
ls -la backend/frontend_dist/
ls -la backend/frontend_dist/assets/ 2>/dev/null || true

echo "==> Running Django migrations..."
cd backend
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Creating sample data (if first deploy)..."
python manage.py create_sample_data 2>/dev/null || echo "Sample data already exists or skipped."

echo "==> Build complete!"
