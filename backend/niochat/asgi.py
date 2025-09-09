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
        
        # Extrair token da query string
        query_string = scope.get('query_string', b'').decode()
        token = None
        
        if query_string:
            try:
                params = dict(item.split('=') for item in query_string.split('&') if '=' in item)
                token = params.get('token')
            except ValueError:
                # Se houver erro na parsing, tentar extrair token diretamente
                if 'token=' in query_string:
                    token = query_string.split('token=')[1].split('&')[0]
        
        if token:
            # Buscar usuário pelo token
            user = await self.get_user_from_token(token, database_sync_to_async, Token)
            if user:
                scope['user'] = user
            else:
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()
        
        return await self.app(scope, receive, send)
    
    async def get_user_from_token(self, token, database_sync_to_async, Token):
        @database_sync_to_async
        def _get_user():
            try:
                token_obj = Token.objects.get(key=token)
                return token_obj.user
            except Token.DoesNotExist:
                return None
        
        return await _get_user()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TokenAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})

