# Breathe ESG Data Ingestion Platform

🌿 A full-stack ESG (Environmental, Social, Governance) emissions data ingestion
and review platform for enterprise sustainability teams.

## Overview

Breathe ESG enables corporate clients to:
- **Upload** emissions data from SAP fuel systems, utility bills, and corporate travel
- **Normalize** raw data into standardized units and calculate CO2e emissions
- **Validate** records with automated checks (missing fields, duplicates, anomalies)
- **Review** records via an analyst workflow with approve/reject/lock states
- **Audit** every change with an immutable audit trail

## Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | Django 4.2 + Django REST Framework  |
| Frontend  | React 18 + Vite                     |
| Database  | PostgreSQL (prod) / SQLite (dev)    |
| Auth      | JWT (djangorestframework-simplejwt) |
| Styling   | Vanilla CSS with Custom Properties  |
| Charts    | Recharts                            |
| Deploy    | Docker + Render                     |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, SQLite works for development)

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py create_sample_data
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Demo Credentials
After running `create_sample_data`:
- **Analyst:** analyst@acme.com / password123
- **Admin:** admin@acme.com / password123

## Architecture

```
breathe-esg/
├── backend/                 # Django API server
│   ├── breathe_esg/         # Project settings
│   ├── tenants/             # Multi-tenancy & auth
│   ├── ingestion/           # Data parsing, validation, normalization
│   └── api/                 # REST API endpoints
├── frontend/                # React SPA
│   └── src/
│       ├── pages/           # Route pages
│       ├── components/      # Reusable UI components
│       ├── context/         # Auth context provider
│       └── api/             # API client
├── MODEL.md                 # Database schema documentation
├── DECISIONS.md             # Architectural decision records
├── TRADEOFFS.md             # Design tradeoff analysis
├── SOURCES.md               # Emission factor citations
├── Dockerfile               # Production container
└── render.yaml              # Render deployment blueprint
```

## Features

### Data Sources
1. **SAP Fuel & Procurement** — Scope 1 emissions from fuel combustion
2. **Utility Electricity** — Scope 2 emissions from purchased electricity
3. **Corporate Travel** — Scope 3 emissions from business travel

### Review Workflow
Records follow a strict lifecycle:
```
Uploaded → Parsed → Approved → Locked
                  → Failed
                  → Suspicious → Approved → Locked
```

### Validation Rules
- Missing required fields
- Invalid date formats
- Unsupported units
- Duplicate row detection
- Negative value checks
- Statistical anomaly flagging

## Deployment

### Render (Recommended)
1. Push to GitHub
2. Connect repo on render.com
3. Create Blueprint from `render.yaml`
4. Deploy automatically

### Docker
```bash
docker build -t breathe-esg .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgres://... \
  -e DJANGO_SECRET_KEY=... \
  breathe-esg
```

## Documentation

- [MODEL.md](MODEL.md) — Database schema and entity relationships
- [DECISIONS.md](DECISIONS.md) — Architectural decision records
- [TRADEOFFS.md](TRADEOFFS.md) — Design tradeoff analysis
- [SOURCES.md](SOURCES.md) — Emission factor sources and assumptions

## License

Internal prototype — not for public distribution.
