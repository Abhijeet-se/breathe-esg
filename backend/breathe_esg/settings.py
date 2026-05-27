"""
Breathe ESG - Django Settings
=============================

Configuration for the ESG Data Ingestion Platform.

Design Decisions:
- Uses dj-database-url for flexible database configuration (SQLite dev, PostgreSQL prod)
- JWT authentication via djangorestframework-simplejwt for stateless API auth
- CORS configured for React frontend at localhost:5173
- WhiteNoise for static file serving in production
- Media root configured for file uploads (CSV/Excel ingestion files)
- python-dotenv loads .env file for local development secrets
"""

import os
from pathlib import Path
from datetime import timedelta

# Load environment variables from .env file if it exists
# This enables local development without setting system env vars
from dotenv import load_dotenv
load_dotenv()

import dj_database_url

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-breathe-esg-dev-key-change-in-production-!@#$%'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

# Parse ALLOWED_HOSTS from comma-separated env var, with sensible defaults
# Reads DJANGO_ALLOWED_HOSTS (set in render.yaml) or ALLOWED_HOSTS as fallback
_hosts_env = os.environ.get('DJANGO_ALLOWED_HOSTS') or os.environ.get(
    'ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0'
)
ALLOWED_HOSTS = [h.strip() for h in _hosts_env.split(',') if h.strip()]

# In production (DEBUG=False), if no hosts are explicitly set, allow all
# This prevents DisallowedHost errors on auto-generated Render domains
if not DEBUG and ALLOWED_HOSTS == ['localhost', '127.0.0.1', '0.0.0.0']:
    ALLOWED_HOSTS = ['*']


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================
# Apps are ordered: Django built-ins -> third-party -> project apps
# This ordering matters for template resolution and signal registration
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',               # Django REST Framework for API
    'rest_framework_simplejwt',     # JWT authentication
    'corsheaders',                  # CORS support for frontend
    'django_filters',              # Filtering support for DRF
    # Project apps
    'tenants',                      # Multi-tenant user management
    'ingestion',                    # Data ingestion & processing pipeline
    'api',                          # API endpoints
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static file serving
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS must be before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tenants.middleware.TenantMiddleware',  # Custom: attaches tenant to request
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'breathe_esg.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'breathe_esg.wsgi.application'

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
# Uses dj-database-url for flexible configuration:
# - If DATABASE_URL env var is set (e.g., PostgreSQL), use that
# - Otherwise, fall back to SQLite for local development
# This allows seamless transition between dev and production
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,  # Connection pooling: keep connections alive for 10 min
    )
}

# =============================================================================
# AUTHENTICATION
# =============================================================================
# Custom user model: tenants.User extends AbstractUser with tenant FK and role
AUTH_USER_MODEL = 'tenants.User'

# Password validation - standard Django validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================
REST_FRAMEWORK = {
    # JWT as default authentication - stateless, scalable
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Require authentication by default - explicit is better than implicit
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # django-filter for queryset filtering
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    # Pagination: 50 items per page, configurable via query param
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# =============================================================================
# JWT CONFIGURATION
# =============================================================================
# Short-lived access tokens (1 hour) with longer refresh tokens (1 day)
# This balances security with user experience
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,      # Issue new refresh token on each refresh
    'BLACKLIST_AFTER_ROTATION': False,   # Don't use blacklist (no extra DB table)
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# =============================================================================
# CORS CONFIGURATION
# =============================================================================
# Allow the React frontend (Vite default port) to make API requests
_cors_origins = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173'
)
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(',') if o.strip()]

# In production, the frontend is served from the same origin as the API,
# so we allow all origins to handle auto-generated Render subdomains
if not DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True  # Allow cookies/auth headers

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise for efficient static file serving in production
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Frontend build output directory (populated by Vite build or Dockerfile)
# In production, the built React SPA is served from here.
# We always set these paths — collectstatic handles missing dirs gracefully,
# and WhiteNoise checks existence at runtime.
FRONTEND_DIR = BASE_DIR / 'frontend_dist'
STATICFILES_DIRS = [str(FRONTEND_DIR)]
WHITENOISE_ROOT = str(FRONTEND_DIR)

# Media files: uploaded CSV/Excel files for ingestion
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================
# We use UUIDs explicitly in models, but set BigAuto as Django's default
# for any models that don't override (e.g., third-party)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# LOGGING
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

