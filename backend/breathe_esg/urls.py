"""
Breathe ESG - Root URL Configuration
=====================================

Django serves the React SPA for all non-API routes.
The SPA handles its own client-side routing via React Router.

URL priority:
  1. /admin/   -> Django admin
  2. /api/     -> REST API endpoints
  3. /*        -> React SPA (catch-all, serves index.html)
"""

import os

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.http import FileResponse, HttpResponse


def serve_react_app(request):
    """
    Catch-all view that serves the React SPA's index.html.

    The built React app is placed in FRONTEND_DIR by the build script.
    All non-API routes are forwarded here, and the SPA handles
    client-side routing (e.g., /login, /review, /audit).
    """
    frontend_dir = getattr(settings, 'FRONTEND_DIR', None)
    if frontend_dir:
        index_path = os.path.join(str(frontend_dir), 'index.html')
        if os.path.exists(index_path):
            return FileResponse(open(index_path, 'rb'), content_type='text/html')

    return HttpResponse(
        '<h1>Breathe ESG</h1>'
        '<p>The React frontend has not been built yet.</p>'
        '<ul>'
        '<li><a href="/api/health/">API Health Check</a></li>'
        '<li><a href="/admin/">Django Admin</a></li>'
        '</ul>',
        content_type='text/html',
    )


urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # All API routes under /api/
    path('api/', include('api.urls')),

    # Catch-all: serve React SPA for everything else.
    # This MUST be last — it matches all remaining paths.
    re_path(r'^.*$', serve_react_app, name='spa_catchall'),
]
