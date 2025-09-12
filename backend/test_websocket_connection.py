#!/usr/bin/env python3
"""
Script para testar conectividade WebSocket e Redis
"""

import asyncio
import redis
import sys
import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
django.setup()

from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from conversations.consumers import DashboardConsumer, UserStatusConsumer
from conversations.consumers_private_chat import PrivateChatConsumer
from conversations.consumers_internal_chat import InternalChatConsumer, InternalChatNotificationConsumer

async def test_redis_connection():
    """Testar conexão com Redis"""
    print("🔍 Testando conexão com Redis...")
    
    try:
        # Testar conexão direta com Redis
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # Testar ping
        result = r.ping()
        print(f"✅ Redis ping: {result}")
        
        # Testar set/get
        r.set('test_key', 'test_value', ex=10)
        value = r.get('test_key')
        print(f"✅ Redis set/get: {value.decode() if value else 'None'}")
        
        # Limpar chave de teste
        r.delete('test_key')
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão Redis: {e}")
        return False

async def test_channel_layer():
    """Testar Channel Layer"""
    print("\n🔍 Testando Channel Layer...")
    
    try:
        channel_layer = get_channel_layer()
        
        # Testar envio de mensagem
        await channel_layer.group_send(
            'test_group',
            {
                'type': 'test_message',
                'text': 'Teste de conectividade'
            }
        )
        
        print("✅ Channel Layer funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Erro no Channel Layer: {e}")
        return False

async def test_websocket_consumers():
    """Testar conectividade dos consumers WebSocket"""
    print("\n🔍 Testando Consumers WebSocket...")
    
    consumers_to_test = [
        ('DashboardConsumer', DashboardConsumer),
        ('UserStatusConsumer', UserStatusConsumer),
        ('PrivateChatConsumer', PrivateChatConsumer),
        ('InternalChatConsumer', InternalChatConsumer),
        ('InternalChatNotificationConsumer', InternalChatNotificationConsumer),
    ]
    
    results = {}
    
    for name, consumer_class in consumers_to_test:
        try:
            # Criar comunicador de teste
            communicator = WebsocketCommunicator(consumer_class.as_asgi(), f"/ws/test/{name.lower()}/")
            
            # Tentar conectar
            connected, subprotocol = await communicator.connect()
            
            if connected:
                print(f"✅ {name}: Conectado com sucesso")
                results[name] = True
                
                # Desconectar
                await communicator.disconnect()
            else:
                print(f"❌ {name}: Falha na conexão")
                results[name] = False
                
        except Exception as e:
            print(f"❌ {name}: Erro - {e}")
            results[name] = False
    
    return results

async def test_websocket_routes():
    """Testar rotas WebSocket"""
    print("\n🔍 Testando rotas WebSocket...")
    
    routes_to_test = [
        '/ws/conversas_dashboard/',
        '/ws/user_status/',
        '/ws/private-chat/',
        '/ws/internal-chat-notifications/',
        '/ws/painel/1/',
    ]
    
    results = {}
    
    for route in routes_to_test:
        try:
            # Simular conexão (sem autenticação real)
            communicator = WebsocketCommunicator(
                DashboardConsumer.as_asgi(), 
                route
            )
            
            connected, subprotocol = await communicator.connect()
            
            if connected:
                print(f"✅ Rota {route}: Acessível")
                results[route] = True
                await communicator.disconnect()
            else:
                print(f"❌ Rota {route}: Inacessível")
                results[route] = False
                
        except Exception as e:
            print(f"❌ Rota {route}: Erro - {e}")
            results[route] = False
    
    return results

async def main():
    """Função principal"""
    print("🚀 Iniciando testes de conectividade WebSocket...\n")
    
    # Testar Redis
    redis_ok = await test_redis_connection()
    
    # Testar Channel Layer
    channel_ok = await test_channel_layer()
    
    # Testar Consumers
    consumer_results = await test_websocket_consumers()
    
    # Testar Rotas
    route_results = await test_websocket_routes()
    
    # Resumo
    print("\n📊 RESUMO DOS TESTES:")
    print("=" * 50)
    print(f"Redis: {'✅ OK' if redis_ok else '❌ FALHA'}")
    print(f"Channel Layer: {'✅ OK' if channel_ok else '❌ FALHA'}")
    
    print("\nConsumers:")
    for name, result in consumer_results.items():
        print(f"  {name}: {'✅ OK' if result else '❌ FALHA'}")
    
    print("\nRotas:")
    for route, result in route_results.items():
        print(f"  {route}: {'✅ OK' if result else '❌ FALHA'}")
    
    # Verificar se há problemas críticos
    critical_failures = []
    if not redis_ok:
        critical_failures.append("Redis não está acessível")
    if not channel_ok:
        critical_failures.append("Channel Layer não está funcionando")
    
    if critical_failures:
        print(f"\n🚨 PROBLEMAS CRÍTICOS ENCONTRADOS:")
        for failure in critical_failures:
            print(f"  - {failure}")
        print("\n💡 SUGESTÕES:")
        print("  1. Verificar se o Redis está rodando")
        print("  2. Verificar credenciais do Redis")
        print("  3. Verificar conectividade de rede")
        print("  4. Verificar configurações do Django Channels")
    else:
        print("\n✅ Todos os testes críticos passaram!")
        print("💡 Se ainda há problemas de WebSocket, verifique:")
        print("  1. Configuração do nginx/proxy")
        print("  2. Certificados SSL")
        print("  3. Firewall/portas")
        print("  4. Logs do servidor")

if __name__ == "__main__":
    asyncio.run(main())
