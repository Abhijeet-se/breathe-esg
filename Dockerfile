# Breathe ESG — Multi-stage Dockerfile
# Stage 1: Build React frontend
# Stage 2: Serve Django + static frontend via Gunicorn + WhiteNoise

# ============================================
# Stage 1: Build the React frontend
# ============================================
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Copy package files first for layer caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install --frozen-lockfile 2>/dev/null || npm install

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# ============================================
# Stage 2: Django backend + serve frontend
# ============================================
FROM python:3.11-slim AS production

# Security: run as non-root user
RUN groupadd -r breathe && useradd -r -g breathe breathe

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=breathe_esg.settings

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Copy built frontend into Django's static directory
# WhiteNoise will serve these in production
COPY --from=frontend-build /app/frontend/dist /app/frontend_dist

# Collect static files (including frontend build)
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Create media directory for uploads
RUN mkdir -p /app/media && chown -R breathe:breathe /app

# Switch to non-root user
USER breathe

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/')" || exit 1

# Start Gunicorn
CMD ["gunicorn", "breathe_esg.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
