"""
WSGI config for breathe_esg project.
Exposes the WSGI callable as a module-level variable named ``application``.
Used by gunicorn in production: gunicorn breathe_esg.wsgi:application
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'breathe_esg.settings')
application = get_wsgi_application()
