"""ASGI entry point for Homeward."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "homeward.settings")
application = get_asgi_application()
