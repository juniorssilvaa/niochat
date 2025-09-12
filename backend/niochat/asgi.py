"""
ASGI config for nio chat project.

This exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from conversations.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')

# Importar Django settings primeiro
django_asgi_app = get_asgi_application()

class TokenAuthMiddleware:
    """
    Middleware customizado para autenticação via token nos WebSockets
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Importar aqui para evitar problemas de importação
        from channels.db import database_sync_to_async
        from django.contrib.auth.models import AnonymousUser
        from rest_framework.authtoken.models import Token
        
        # Para WebSockets, vamos permitir conexões sem token por enquanto
        # e autenticar depois na conexão
        scope['user'] = AnonymousUser()
        
        return await self.app(scope, receive, send)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TokenAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})

