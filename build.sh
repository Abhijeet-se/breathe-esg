#!/usr/bin/env bash
# ============================================
# Render Build Script — Breathe ESG
# ============================================
# This script is called by Render during deployment.
# It builds the frontend, installs backend deps,
# and prepares the app for production.
# ============================================

set -o errexit  # Exit on error

echo "==> Installing backend dependencies..."
cd backend
pip install -r requirements.txt

echo "==> Installing frontend dependencies..."
cd ../frontend
npm install

echo "==> Building frontend..."
npm run build

echo "==> Copying frontend build to backend..."
cd ..
rm -rf backend/frontend_dist
cp -r frontend/dist backend/frontend_dist

echo "==> Running Django migrations..."
cd backend
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Creating sample data (if first deploy)..."
python manage.py create_sample_data || echo "Sample data already exists, skipping."

echo "==> Build complete!"
