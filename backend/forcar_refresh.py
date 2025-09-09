#!/usr/bin/env python3
"""
Script para forçar refresh dos dados no frontend
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/home/junior/niochat/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
django.setup()

from conversations.models import Conversation
from core.models import Provedor

def forcar_refresh_frontend():
    """Força refresh dos dados no frontend"""
    
    print("🔄 FORÇANDO REFRESH DOS DADOS NO FRONTEND")
    print("=" * 50)
    
    # Buscar conversa 94
    conversa = Conversation.objects.filter(id=94).first()
    
    if not conversa:
        print("❌ Conversa 94 não encontrada")
        return
    
    print(f"✅ Conversa encontrada: ID {conversa.id}")
    print(f"📱 Contact: {conversa.contact.name}")
    print(f"🔄 Status: {conversa.status}")
    print(f"📋 Additional attributes: {conversa.additional_attributes}")
    
    # Verificar se assigned_team está presente
    if conversa.additional_attributes and 'assigned_team' in conversa.additional_attributes:
        equipe = conversa.additional_attributes['assigned_team']['name']
        print(f"✅ Equipe: {equipe}")
        
        # Forçar save para garantir que os dados estão atualizados
        conversa.save()
        print("✅ Dados salvos novamente")
        
        # Verificar se o serializer retorna corretamente
        from conversations.serializers import ConversationListSerializer
        serializer = ConversationListSerializer(conversa)
        additional_data = serializer.data.get('additional_attributes', {})
        
        print(f"📡 Dados do serializer:")
        print(f"   Additional attributes: {additional_data}")
        print(f"   Assigned team: {additional_data.get('assigned_team')}")
        
        if additional_data.get('assigned_team', {}).get('name') == equipe:
            print("✅ Serializer retornando dados corretos")
        else:
            print("❌ Problema no serializer")
    else:
        print("❌ Assigned team não encontrado nos additional_attributes")
    
    print("\n💡 INSTRUÇÕES PARA O USUÁRIO:")
    print("1. Abra o DevTools do navegador (F12)")
    print("2. Vá na aba Console")
    print("3. Recarregue a página (Ctrl+F5 ou Cmd+Shift+R)")
    print("4. Procure por logs que começam com '🔍 DEBUG getEquipe:'")
    print("5. Verifique se os dados estão chegando corretamente")

if __name__ == "__main__":
    forcar_refresh_frontend()




