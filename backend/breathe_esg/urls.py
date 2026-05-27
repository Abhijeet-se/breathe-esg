"""
Breathe ESG - Root URL Configuration
=====================================

In production (DEBUG=False), Django serves the React SPA for all non-API routes.
The SPA handles its own client-side routing via React Router.

URL priority:
  1. /admin/   -> Django admin
  2. /api/     -> REST API endpoints
  3. /media/   -> Uploaded files (dev only)
  4. /*        -> React SPA (production only, via index.html catch-all)
"""

import os
from pathlib import Path

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, HttpResponse


def serve_react_app(request):
    """
    Catch-all view that serves the React SPA's index.html.

    In production, the built React app is placed in FRONTEND_DIR.
    All non-API routes are forwarded to the SPA, which handles
    client-side routing (e.g., /login, /review, /audit).
    """
    frontend_dir = getattr(settings, 'FRONTEND_DIR', None)
    if frontend_dir:
        index_path = os.path.join(frontend_dir, 'index.html')
        if os.path.exists(index_path):
            return FileResponse(open(index_path, 'rb'), content_type='text/html')

    return HttpResponse(
        '<h1>Frontend not built</h1>'
        '<p>Run <code>npm run build</code> in the frontend directory, '
        'then copy dist/ to backend/frontend_dist/</p>',
        status=503
    )


urlpatterns = [
    # Django admin - useful for direct DB inspection during development
    path('admin/', admin.site.urls),
    # All API routes are namespaced under /api/
    path('api/', include('api.urls')),
]

# Serve media files in development (uploaded CSV/Excel files)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# In production, serve the React SPA for all other routes
# This MUST be the last pattern - it catches everything not matched above
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^(?!api/|admin/|static/|media/).*$', serve_react_app),
    ]
