"""
ASGI config for app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from lobby.middleware import TokenMiddlewareStack


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

from arena.routing import websocket_urlpatterns as arena_routes
from lobby.routing import websocket_urlpatterns as lobby_routes

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        TokenMiddlewareStack(URLRouter(arena_routes + lobby_routes))
    )
})
